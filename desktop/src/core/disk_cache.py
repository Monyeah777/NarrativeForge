"""内容寻址的**持久**缓存：把「内容的纯函数」结果移出进程生命周期。

用途：执行层里最贵的几笔账（引用度普查、产出面逐件校验、一致性分级扫描…）都是**输入内容的
纯函数**，但每开一个新进程就要重付一遍。把它们按内容寻址落到盘上，新进程直接取回。

键 = `sha256(标签 | 代码面内容 | 运行时标签 | 调用方给的各段键)`

- **代码面内容**（`desktop/src/**/*.py` + `scripts/**/*`，实测 157 件 / 41 ms）：把「算这段的
  函数本身」也放进键里，于是 **改了算法必然换键**——不需要靠"记得手工 bump 版本标签"这种脆弱
  纪律（漏 bump 就等于悄悄拿旧算法的结果当新结果）。
- **运行时标签**：Python 版本 / 平台 / PyYAML 是否在场——软依赖的有无会改变结果。
- **调用方给的各段键**：各自的输入面内容指纹（例如产出面的 `INDEX_INPUTS`）。

落点：`<NF_HOME>/cache/<tag>/<key>.json`（**不在仓库内**，故仓库纯净与门禁不受影响）。

纪律（fail-closed）：
1. 读回必须**校验**（调用方给 `validate`）：结构不对 / 键集不符 / 半截 JSON → 一律当没命中；
2. 一切 IO **尽力而为**：写不进、读不到都静默回落重算，绝不影响命令结果；
3. `NF_NO_DISK_CACHE=1` 整体关闭（读写皆废）；
4. 每个标签只留最近 `KEEP` 份（按 mtime 裁剪），缓存不得无界增长。
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Callable, Optional

ENV_OFF = "NF_NO_DISK_CACHE"
KEEP = 16
#: 大集合标签（每份文件一条的那种，如 AST 事实）裁剪频次：每 N 次写入裁一次。
#: 为什么不一写一裁：一写一裁＝每次都要把目录整个 scandir+stat 一遍，**每份文件一条**的标签
#: 会变成 O(n²)（250 条 × 250 次 = 6 万次 stat，实测吃掉几百毫秒，把收益全抵消）。
PRUNE_EVERY_BIG = 128
#: 参与「代码面」的路径（改了算法即换键；不含 tests——测试不影响结果）。
CODE_FACE = ("desktop/src/**/*.py", "scripts/**/*")

_CODE_FP: dict = {}                      # root → 代码面指纹（**按根记忆**：换根不得串味）
_RUNTIME: Optional[str] = None
_KEEP: dict = {}                         # tag → 上限（给大集合标签用）
_PRUNE_COUNT: dict = {}


def enabled() -> bool:
    return not os.environ.get(ENV_OFF)


def root_dir() -> Path:
    from core import storage
    return storage.default_home() / "cache"


def dir_for(tag: str) -> Path:
    return root_dir() / str(tag)


def runtime_tag() -> str:
    """运行时标签：软依赖与解释器在场与否**会改变结果**，故必须进键。"""
    global _RUNTIME
    if _RUNTIME is None:
        import sys
        try:
            import yaml
            yaml_bit = "yaml=%s" % getattr(yaml, "__version__", "?")
        except Exception:                              # noqa: BLE001 - 缺 PyYAML 是合法状态
            yaml_bit = "yaml=none"
        _RUNTIME = "%d.%d.%d|%s|%s" % (sys.version_info[0], sys.version_info[1],
                                       sys.version_info[2], os.name, yaml_bit)
    return _RUNTIME


def code_fingerprint(root: str = ".") -> str:
    """代码面内容指纹（**按根**进程内记忆；实测 41 ms）。

    按根记忆是必须的：早先写成单变量时，换一棵树会拿回上一棵树的指纹——判据当场抓住
    （`test_code_fingerprint_tracks_code_content`）。守护在**判定代码已换版**时要调
    `reset_code_fingerprint()`，否则会拿旧算法的键去命中盘上旧算法的账。
    """
    rkey = os.path.normcase(os.path.abspath(str(root)))
    hit = _CODE_FP.get(rkey)
    if hit is None:
        from core import conformance_scan as csc
        hit = csc.content_fingerprint(str(root), CODE_FACE)
        _CODE_FP[rkey] = hit
    return hit


def reset_code_fingerprint(root: Optional[str] = None) -> None:
    """清掉代码面指纹记忆（守护判定「代码已换版」后调用；不给 root 则全清）。"""
    if root is None:
        _CODE_FP.clear()
        return
    _CODE_FP.pop(os.path.normcase(os.path.abspath(str(root))), None)


#: 仓库内模块的**导入图**（懒建、按 (根, 模块) 记忆）：模块名 → (文件相对路径, 依赖, 是否含动态导入)。
#: 只用来**划定代码面的范围**（谁真的依赖谁的代码），不参与任何判定；解析不出/含动态导入 → 退回整块。
_IMPORT_MEMO: Dict[Any, Optional[Tuple[str, frozenset, bool]]] = {}
_CORE_DIR = ("desktop", "src", "core")


def _module_info(root: str, name: str):
    """解析 `desktop/src/core/<name>.py` → (相对路径或 None, 静态依赖, 是否含动态导入构造)。

    - 文件不存在 ⇒ `(None, {}, False)`：这不是模块文件（`from core import <名字>` 里的名字可能来自
      `core/__init__.py`），调用方据此把它折算成对 `__init__.py` 的依赖，而不是判「说不清」。
    - 文件在但解析不出 ⇒ `None`：真的说不清，调用方**退回整块代码面**。
    - 记忆键含 `(mtime_ns, size)`：进程活着的时候代码被改了，图必须跟着变（本轮判据当场抓过：
      只按 (根, 模块) 记忆会让合成树里的第二版内容读成第一版）。
    """
    path = Path(root).joinpath(*_CORE_DIR, str(name) + ".py")
    try:
        st = path.stat()
        stamp = (st.st_mtime_ns, st.st_size)
    except OSError:
        return (None, frozenset(), False)
    rkey = (os.path.normcase(os.path.abspath(str(root))), str(name), stamp)
    if rkey in _IMPORT_MEMO:
        return _IMPORT_MEMO[rkey]
    info = None
    try:
        import ast
        tree = ast.parse(path.read_text(encoding="utf-8"))
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
        info = ("/".join(_CORE_DIR + (str(name) + ".py",)),
                frozenset(d for d in deps if d), dyn)
    except Exception:                                  # noqa: BLE001 - 解析不出即「说不清」
        info = None
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
    while stack:
        name = stack.pop()
        if name in seen:
            continue
        info = _module_info(root, name)
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
    """闭包的**内容指纹**（按 (根, 模块元组) 记忆）；闭包算不出 → None。"""
    rkey = (os.path.normcase(os.path.abspath(str(root))), tuple(sorted(map(str, modules))))
    if rkey in _SCOPE_FP:
        return _SCOPE_FP[rkey]
    files = code_scope_files(root, modules)
    out = None
    if files is not None:
        from core import conformance_scan as csc
        out = csc.content_fingerprint(str(root), files)
    _SCOPE_FP[rkey] = out
    return out


def reset_code_scope(root: Optional[str] = None) -> None:
    """清掉导入图与闭包指纹的记忆（守护判定代码已换版后调用）。"""
    rkey = None if root is None else os.path.normcase(os.path.abspath(str(root)))
    for memo in (_IMPORT_MEMO, _SCOPE_FP):
        for k in [k for k in memo if rkey is None or k[0] == rkey]:
            memo.pop(k, None)


def key(tag: str, *parts: str, root: str = ".", code_modules=None) -> str:
    """算缓存键：标签 + 代码面 + 运行时 + 调用方给的各段。

    `code_modules` 给出「这段派生**自己的**代码闭包」（如 `("core.schema_lint",)`）时，代码面只取闭包
    ——于是改别的模块不再换键（实测：整块代码面 119 件，多数派生只依赖 3–21 件；改 `terminal.py`
    这种与派生无关的件不该让全部派生重算）。闭包算不出/含动态导入 → **退回整块代码面**
    （宁可多算，不可拿旧算法的账当新账）。不给 `code_modules` 时行为与从前完全一致。
    """
    if code_modules:
        scope = code_scope_fingerprint(root, code_modules)
        code_bit = scope if scope is not None else code_fingerprint(root)
    else:
        code_bit = code_fingerprint(root)
    h = hashlib.sha256()
    for piece in ("v1", str(tag), code_bit, runtime_tag()) + tuple(
            str(p) for p in parts):
        h.update(piece.encode("utf-8"))
        h.update(b"\x00")
    return h.hexdigest()


def _path(tag: str, ckey: str) -> Path:
    return dir_for(tag) / ("%s.json" % ckey)


def load(tag: str, ckey: str,
         validate: Optional[Callable[[Any], bool]] = None) -> Any:
    """读回缓存值；**任何不可信**一律返回 None（宁可重算，不可错答）。"""
    if not enabled():
        return None
    try:
        got = json.loads(_path(tag, ckey).read_text(encoding="utf-8"))
    except Exception:                                  # noqa: BLE001 - 缺件/半截/不可读
        return None
    if validate is not None:
        try:
            if not validate(got):
                return None
        except Exception:                              # noqa: BLE001 - 校验器自己炸也算不可信
            return None
    return got


def store(tag: str, ckey: str, value: Any, keep: Optional[int] = None) -> None:
    """写盘（尽力而为）：原子替换 + 有界裁剪；失败静默。

    `keep` 给「每份文件一条」的大集合标签用（如 AST 事实 250 条）；小集合标签沿用 `KEEP`。
    小集合（≤64）每次写都裁（目录本身就小，成本可忽略）；大集合每 `PRUNE_EVERY_BIG` 次裁一次。
    """
    if not enabled():
        return
    try:
        d = dir_for(tag)
        d.mkdir(parents=True, exist_ok=True)
        p = _path(tag, ckey)
        tmp = p.with_name(p.name + ".tmp")
        with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(value, ensure_ascii=False, sort_keys=True))
        os.replace(tmp, p)                             # 原子替换：读者看不到半截 JSON
        limit = int(keep if keep is not None else _KEEP.get(tag, KEEP))
        n = _PRUNE_COUNT.get(tag, 0) + 1
        if limit <= 64 or n >= PRUNE_EVERY_BIG:
            _PRUNE_COUNT[tag] = 0
            prune(tag, limit)
        else:
            _PRUNE_COUNT[tag] = n
    except Exception:                                  # noqa: BLE001 - 写不进就算了
        return


def prune(tag: str, keep: int = KEEP) -> None:
    """只留最近 `keep` 份（按 mtime）。"""
    try:
        d = dir_for(tag)
        entries = sorted(d.glob("*.json"), key=lambda q: q.stat().st_mtime, reverse=True)
        for old in entries[keep:]:
            old.unlink()
    except Exception:                                  # noqa: BLE001 - 裁剪失败不影响结果
        return
