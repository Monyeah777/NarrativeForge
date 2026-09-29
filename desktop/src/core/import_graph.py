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
from typing import Optional, Tuple

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
    except OSError:
        return {}
    return out


def parse(text: str) -> Optional[Tuple[str, frozenset, bool]]:
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
