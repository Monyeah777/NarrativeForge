#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""`desktop/src/core/*.py` 的**导入图**（谁 import 了 core 里的谁）——**持久化**。

依据（实测 2026-09-29）：一次冷进程 `evaluate` 里，16 个派生站点各自要解析导入闭包，而
`_module_info` 逐模块 `ast.parse` 同一批源码——6 个站点样本 BFS 合计 **133 ms**（其中
`core.quality_depth_scan` 一个闭包就 101 ms）。依赖解析只是「**该件正文**的纯函数」⇒ 与
`purity_scan._facts_for` 的 AST 事实同一套做法：**落盘**，键＝根 + 模块名 + `mtime_ns` + `size`
+ 版本；新进程免付（本仓 ~50 份模块 ≈ 100 ms）。

纪律与既有缓存一致：`NF_NO_DISK_CACHE=1` 时读写皆废（退回现算）；读回必过形状校验，不可信就重算；
含动态导入构造（`__import__` / `importlib`）时结果里带 `dyn=True`，调用方据此**退回整块代码面**。
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

#: core 包在仓库里的目录（与 `disk_cache._CORE_DIR` 同源；此处独立声明以免循环导入）。
_CORE_DIR = ("desktop", "src", "core")
#: 键里的版本位：**抽取逻辑一改就换键**（旧图不许当新图用）。
_VERSION = "v1"


def _ok(value) -> bool:
    """读回值的形状：`[rel|None, [依赖名…], dyn]`。"""
    return (isinstance(value, list) and len(value) == 3
            and (value[0] is None or isinstance(value[0], str))
            and isinstance(value[1], list) and all(isinstance(x, str) for x in value[1])
            and isinstance(value[2], bool))


def listing(root: str) -> dict:
    """一次 `scandir` 拿到 `core/*.py` 的 `(mtime_ns, size)`（Windows 上 `DirEntry.stat()` 免费）。

    依据（实测 2026-09-29）：闭包 BFS 逐模块 `Path.stat()` 本机 ~110 µs ⇒ 16 个站点各解析一遍累计
    几十毫秒；一次目录读（~1.5 ms）就够整个闭包用。**失败 → 返回 `{}`**，调用方退回逐件 stat
    （fail-closed：宁可多花一次 stat，也不许把「列不到的模块」当成不存在）。
    """
    out: dict = {}
    try:
        with os.scandir(Path(root).joinpath(*_CORE_DIR)) as it:
            for ent in it:
                if ent.name.endswith(".py"):
                    st = ent.stat()
                    out[ent.name] = (st.st_mtime_ns, st.st_size)
    except OSError:  # 列目录失败 ⇒ 空表：调用方退回逐件 stat（不把「列不到」当不存在）
        return {}
    return out


def parse(text: str) -> Optional[Tuple[frozenset, bool]]:
    """正文 → `(依赖名集合, 是否含动态导入)`；解析不出 → None（调用方退回整块代码面）。"""
    import ast
    try:
        tree = ast.parse(text)
    except Exception:                                        # noqa: BLE001 - 解析不出即「说不清」
        return None
    deps: set = set()
    dyn = False
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "core" or alias.name.startswith("core."):
                    if "." in alias.name:
                        deps.add(alias.name.split(".")[1])
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            if mod == "core":
                deps.update(a.name for a in node.names)
            elif mod.startswith("core."):
                deps.add(mod.split(".")[1])
        elif isinstance(node, ast.Call):
            fn = node.func
            if isinstance(fn, ast.Name) and fn.id == "__import__":
                dyn = True
            elif isinstance(fn, ast.Attribute) \
                    and getattr(getattr(fn, "value", None), "id", "") == "importlib":
                dyn = True
    return frozenset(d for d in deps if d), dyn


def load_or_parse(root: str, name: str, stamp) -> Optional[Tuple[str, frozenset, bool]]:
    """`(相对路径或 None, 静态依赖, 含动态导入)`；持久层命中即免解析，失败一律现算。"""
    from core import disk_cache as dc
    rel = "/".join(_CORE_DIR + (str(name) + ".py",))
    ckey = dc_digest(root, name, stamp)
    packed = dc.load("import-graph", ckey, validate=_ok)
    if packed is not None:
        return (packed[0], frozenset(packed[1]), bool(packed[2]))
    path = Path(root).joinpath(*_CORE_DIR, str(name) + ".py")
    try:
        got = parse(path.read_text(encoding="utf-8"))
    except OSError:
        got = None
    if got is None:
        return None
    deps, dyn = got
    dc.store("import-graph", ckey, [rel, sorted(deps), dyn])
    return (rel, deps, dyn)


def dc_digest(root: str, name: str, stamp) -> str:
    """持久键（不走 `dc.key`：那会反过来算代码面，形成递归）。"""
    import hashlib
    blob = "%s|%s|%s|%s|%s" % (os.path.normcase(os.path.abspath(str(root))), name,
                               stamp[0], stamp[1], _VERSION)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


_IMPORT_MEMO: Dict[Any, Optional[Tuple[str, frozenset, bool]]] = {}

def _module_info(root: str, name: str, listing: Optional[dict] = None):
    """解析 `desktop/src/core/<name>.py` → (相对路径或 None, 静态依赖, 是否含动态导入构造)。

    - 文件不存在 ⇒ `(None, {}, False)`：这不是模块文件（`from core import <名字>` 里的名字可能来自
      `core/__init__.py`），调用方据此把它折算成对 `__init__.py` 的依赖，而不是判「说不清」。
    - 文件在但解析不出 ⇒ `None`：真的说不清，调用方**退回整块代码面**。
    - 记忆键含 `(mtime_ns, size)`：进程活着的时候代码被改了，图必须跟着变（本轮判据当场抓过：
      只按 (根, 模块) 记忆会让合成树里的第二版内容读成第一版）。解析本体见 `core.import_graph`
      （**落盘**：一次冷跑 16 个站点各解析一遍同一批源码 ≈ 100 ms，键含 mtime+size 故不陈旧）。
    """
    path = Path(root).joinpath(*_CORE_DIR, str(name) + ".py")
    stamp = (listing or {}).get(str(name) + ".py")
    if stamp is None:                    # 列表里没有（或没给列表）⇒ 逐件 stat 兜底（fail-closed）
        try:
            st = path.stat()
            stamp = (st.st_mtime_ns, st.st_size)
        except OSError:
            return (None, frozenset(), False)
    rkey = (os.path.normcase(os.path.abspath(str(root))), str(name), stamp)
    if rkey in _IMPORT_MEMO:
        return _IMPORT_MEMO[rkey]
    info = load_or_parse(root, name, stamp)
    _IMPORT_MEMO[rkey] = info
    return info




def code_scope_files(root: str, modules) -> Optional[Tuple[str, ...]]:
    """`modules` 的**静态导入闭包**（仓库内文件，posix 相对路径）；任何不确定 → `None`。

    fail-closed 三条：① 闭包里任一模块解析不出（缺件/语法错）→ None；② 闭包里出现**动态导入构造**
    （`__import__` / `importlib`）→ None（静态闭包不再可信，退回整块代码面）；③ 闭包为空 → None。
    """
    seen: set = set()
    stack = [str(m).split(".")[-1] for m in modules]
    files: set = set()
    stamps = listing(root)                 # 一次目录读，闭包里每个模块的 (mtime, size) 都从它取
    while stack:
        name = stack.pop()
        if name in seen:
            continue
        info = _module_info(root, name, stamps)
        if info is None or info[2]:
            return None
        seen.add(name)
        if info[0] is None:                        # 不是模块文件 → 折算成 core/__init__.py 的依赖
            files.add("/".join(_CORE_DIR + ("__init__.py",)))
            continue
        files.add(info[0])
        stack.extend(info[1])
    return tuple(sorted(files)) if files else None




_SCOPE_FP: Dict[Any, Optional[str]] = {}

def code_scope_fingerprint(root: str, modules) -> Optional[str]:
    """闭包的**内容指纹**（按 (根, 模块元组) 记忆）；闭包算不出 → None。

    逐件直取摘要（2026-09-29 实测）：闭包是**已知的相对路径表**，而 `face_fingerprint(root, files)`
    会把每个路径**当成一个模式**去走目录——本仓 4 件的闭包实测要 **42.5 ms**（每个模式一次目录枚举），
    16 个站点合计 ~90 ms。这里按与面指纹**同一帧**（`rel \\x00 digest \\x01`，顺序＝已排序）直接算，
    实测 0.1–2 ms/站点，**值逐位不变**（判据：`test_disk_cache.CodeScopeFrameTest`）。
    """
    rkey = (os.path.normcase(os.path.abspath(str(root))), tuple(sorted(map(str, modules))))
    if rkey in _SCOPE_FP:
        return _SCOPE_FP[rkey]
    files = code_scope_files(root, modules)
    out = None
    if files is not None:
        from core import content_face as _cf      # 同帧同口径（叶子件），缺件不计入
        have = _cf.list_core_files(str(root))
        digests = {rel: _cf.payload_digest(str(root), rel) for rel in files
                   if rel.rsplit("/", 1)[-1] in have}
        out = _cf.hash_face(sorted(digests), digests)
    _SCOPE_FP[rkey] = out
    return out




def reset_code_scope(root: Optional[str] = None) -> None:
    """清掉导入图与闭包指纹的记忆（守护判定代码已换版后调用）。"""
    rkey = None if root is None else os.path.normcase(os.path.abspath(str(root)))
    for memo in (_IMPORT_MEMO, _SCOPE_FP):
        for k in [k for k in memo if rkey is None or k[0] == rkey]:
            memo.pop(k, None)
