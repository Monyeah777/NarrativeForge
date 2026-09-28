"""43 A2 —— Conformance 一致性分级扫描（声明 ≤ 可证级别，防虚标）。

分级定义见 01 §1.2：L0 结构可读 / L1 机读契约 / L2 装配可执行 / L3 外部互操作。

扫描对象：
- 模块文档 machine_contract.conformance（23 件机读块，check28 约束必带）
- community/*/protocol.yaml package.conformance（5 协议包，在册 = L2）
- protocol/export_conformance.json（导出契约面 manifest，L3 = 导出门禁锁定面）

用法：conformance_scan.scan('.') -> (issues, stats)
"""

from __future__ import annotations

import copy
import contextlib
import functools
import glob
import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import yaml  # PyYAML（仓库既有依赖）
except Exception:  # pragma: no cover
    yaml = None  # type: ignore[assignment]

FENCE = re.compile(r"(?ms)```yaml\s*(.*?)```")
_T = chr(96) * 3
#: 统一的安全 YAML 加载器：优先 **libyaml 的 C 实现**（`CSafeLoader`），缺则回退纯 Python。
#: 依据（本波实测）：本仓 473 次 YAML 解析里 PyYAML 扫描器是纯 Python，单份机器契约 ~2 ms——
#: 换 C 实现后同一批正文 **7.8× 快**（200 份正文 0.164 s → 0.021 s）。
#: 等价性**逐块实证**：本仓全部 1395 个 YAML 文本块（584 份文件）用两种加载器各解析一遍，
#: 值差异 0、异常行为差异 0（见 `test_conformance_scan` 的等价断言；缺 libyaml 时自动跳过）。
SAFE_LOADER = getattr(yaml, "CSafeLoader", None) or getattr(yaml, "SafeLoader", None)
#: 围栏 YAML 解析缓存：键 = (marker, **文本本身**)，值 = 解析结果或 None（见 `_fence_yaml`）。
#: **负结果（2026-09 受控 A/B，勿重复尝试）**：本缓存与下面的 `_BODY_CACHE` **不做磁盘持久化**。
#: 实测：575 块全量「纯解析」**139 ms** vs「从盘读回」**108 ms**——只差 **31 ms**（每块解析仅
#: ~0.24 ms，而落盘读回要开一个文件 + 解 JSON ~0.19 ms，文件系统一冷还会更贵）。为 31 ms 增加
#: 近千个缓存文件不划算；这两笔账留在进程内层即可（冷路径的大头已由 AST 事实/派生结果那几路
#: 落盘承担）。注意：cProfile 会把 PyYAML 这类「调用密集」代码放大成 ~0.65 s，别拿画像数字当收益。
_FENCE_CACHE: Dict[Tuple[str, str], Any] = {}
_FENCE_CACHE_MAX = 4096
#: 围栏**正文**缓存：键 = 正文本身。给「自己抽正文」的调用方用（pipeline_loader /
#: concept_graph 过去直接调 load_yaml，等于每轮都重解析——与 `_fence_yaml` 的缓存互补）。
_BODY_CACHE: Dict[str, Any] = {}
_BODY_CACHE_MAX = 4096

#: 「一次**只读**扫描内共享语料」的读缓存：作用域由 `read_memo()` 显式框定，出口即清。
#: 必要性（实测）：一次 `regression_score.evaluate` 打开 **7833** 次文件、其中只有 **2354**
#: 个不同文件——**70% 是冗余读**（同一份包资产被 concept_graph / asset_density / output_forms
#: 等各读一遍）。作用域严格等于「一次扫描调用」，且这些聚合入口都是纯读（写路径 `--write`
#: 在聚合**之后**才发生），所以冷却语义与「新起进程」一致：不跨调用、不跨请求复用。
#: 与读缓存**同生命周期**的「列目录」缓存：一次只读调用内，`_module_docs` 这类清单只走一遍
#: 文件系统（实测一次 evaluate 里它被调 5 次、合计 167 ms；各扫描器各自重走同一批目录）。
_READ_MEMO: Optional[Dict[str, Any]] = None
_DIR_MEMO: Optional[Dict[str, Any]] = None
#: 与读缓存同生命周期的**逐件内容摘要**缓存（键＝文件）：一次只读调用里同一件只为指纹算一次
#: 摘要——一次 `evaluate` 里多个输入面高度重叠，这一层把「每个面重算一遍哈希」摊成一次。
_DIGEST_MEMO: Optional[Dict[str, bytes]] = None
#: 与读缓存**同生命周期**的「按模式枚举」缓存：一次只读调用内，同一 (root, pattern) 只走一遍
#: 文件系统（实测：输入面在 2 个指纹 + 各扫描器之间重复枚举，44% 的遍历是白走）。
_PAT_MEMO: Optional[Dict[Tuple[str, str], Tuple[str, ...]]] = None
#: 与读缓存**同生命周期**的「子树文件清单」缓存：一次只读调用内，每棵子树只走一遍文件系统。
#: 依据（实测）：一次 `evaluate` 建了 **5403** 个 `os.scandir`（仅建扫描器就 **687 ms / 25%**），
#: 其中 `community` 一棵树被 layer_model 的 `_walk_files`、两个指纹、若干扫描器各自走了一遍。
#: 键即目录 ⇒ 目录没变清单就一样；作用域出口即清（与冷读语义一致）。
_TREE_MEMO: Optional[Dict[str, Tuple[str, ...]]] = None

#: **常驻层**（`_RESIDENT`）：跨调用、跨请求活着的一份「语料正文 + 目录条目」。
#:
#: 为什么需要它（2026-09-29 实测）：改一个文件之后，守护的第一条重命令要 **1.6–2.0 s**——
#: 因为上面那些作用域缓存**出口即清**，下一个请求要把整棵语料重新枚举（1484 个目录 / ~2000 次
#: `scandir`）并重读（~2500 次 open）。而其中**只有被改的那一件**真的变了。
#:
#: 为什么它不破坏「热进程 == 新起进程」这条头号不变式：它**只在守护带监听且监听健康时安装**，
#: 且**只按监听给出的确知路径失效**；监听说不清（溢出 / 路径解不出 / 只跳代际没给路径）时，调用方
#: 必须 `clear_resident()` 整批作废。也就是说它比响应缓存**不多信任任何东西**——响应缓存本来就
#: 靠同一条「代际没变 ⇒ 树没变」的判据（同一条 `watch.selfcheck` 机制自检 + 卷类型闸门守着）。
#: 只缓存**监听根之下**的件；根外的读一律走原路（根外没有变更通知，无从失效）。
_RESIDENT: Optional[Dict[str, Any]] = None
#: 常驻层的容量上界（目录条数与正文条数）：超出即停止收录（不影响正确性，只是退回按需读）。
_RESIDENT_DIR_MAX = 8192
_RESIDENT_TEXT_MAX = 16384


class _Entry:
    """常驻目录索引里的一条：只提供 `os.DirEntry` 被用到的那五个成员。"""

    __slots__ = ("name", "path", "_is_dir", "_is_file", "_is_link")

    def __init__(self, name: str, path: str, is_dir: bool, is_file: bool, is_link: bool):
        self.name = name
        self.path = path
        self._is_dir = is_dir
        self._is_file = is_file
        self._is_link = is_link

    def is_dir(self) -> bool:
        return self._is_dir

    def is_file(self) -> bool:
        return self._is_file

    def is_symlink(self) -> bool:
        return self._is_link


def install_resident(root) -> None:
    """安装常驻层（**只在守护带监听且监听健康时调用**）。"""
    global _RESIDENT
    root_abs = os.path.normcase(os.path.abspath(str(root)))
    _RESIDENT = {"root": root_abs, "dirs": {}, "text": {}, "bytes": {}, "digest": {}}


def resident_active() -> bool:
    return _RESIDENT is not None


def resident_stats() -> Dict[str, int]:
    """常驻层规模（观测 + 判据用）：目录条数 / 正文条数 / 二进制条数。"""
    if _RESIDENT is None:
        return {"dirs": 0, "text": 0, "bytes": 0, "digest": 0}
    return {"dirs": len(_RESIDENT["dirs"]), "text": len(_RESIDENT["text"]),
            "bytes": len(_RESIDENT["bytes"]), "digest": len(_RESIDENT["digest"])}


def clear_resident() -> None:
    """整批作废（监听说不清 / 不再健康时调用）。"""
    global _RESIDENT
    _RESIDENT = None


def _resident_key(path) -> str:
    """路径 → 归一化键（`normcase(abspath)`）——**带记忆**。

    依据（实测，2026-09-29 profile）：一次 `evaluate` 里本函数被调 **17628 次**、单独花掉 **71 ms**，
    而它只是 `abspath + normcase`（各约 2 µs）。热路径（`read_text_cached` / `_payload_digest` /
    常驻层的每次查表）都按**同一批路径**反复调它，所以按 `(cwd, 传入写法)` 记忆是安全的：
    `abspath` 只依赖 cwd，而 cwd 在**一次只读调用内**不变（守护逐请求 chdir，不在一段中途改）。
    """
    raw = str(path)
    memo_key = (os.getcwd(), raw)
    hit = _KEY_CACHE.get(memo_key)
    if hit is not None:
        return hit
    key = os.path.normcase(os.path.abspath(raw))
    if len(_KEY_CACHE) >= _KEY_CACHE_MAX:
        _KEY_CACHE.clear()
    _KEY_CACHE[memo_key] = key
    return key


#: `_resident_key` 的记忆表（见其说明）：到上限整批清，避免无界增长。
_KEY_CACHE: Dict[Tuple[str, str], str] = {}
_KEY_CACHE_MAX = 65536


def _resident_under(key: str) -> bool:
    """这个（已 normcase 的绝对）路径是否落在常驻层的监听根之下。"""
    res = _RESIDENT
    if res is None:
        return False
    root = res["root"]
    return key == root or key.startswith(root + os.sep)


def drop_resident(paths) -> None:
    """按**确知变更**的路径精确失效：正文按件删；目录条目按**父目录**删（增删都会改父目录清单）。

    `paths` 是监听给出的仓库相对路径（`/` 分隔、小写）；解析不过来的路径直接忽略。
    """
    res = _RESIDENT
    if res is None:
        return
    root = res["root"]
    for rel in paths or ():
        key = os.path.normcase(os.path.join(root, str(rel).replace("/", os.sep)))
        res["text"].pop(key, None)
        res["bytes"].pop(key, None)
        res["digest"].pop(key, None)
        res["dirs"].pop(os.path.dirname(key), None)
        res["dirs"].pop(key, None)          # 路径本身也可能是目录（整棵子树增删）


@contextlib.contextmanager
def read_memo():
    """框定「共享语料」的作用域（可嵌套；**嵌套＝细化，共享同一份缓存**）。

    冷却契约的边界是**最外层**那次只读调用（如 `regression_score.evaluate`）：出口统一清空，
    下个调用照常重新读盘。嵌套的 `read_memo()`（如 `quality_depth_scan.scan`）过去会另起一份
    空缓存，于是外层刚读过的语料在里面**又读一遍**——实测这样一次 evaluate 白开了上千次文件；
    现在嵌套只是同一只读调用内的细化，缓存共存但不越出最外层边界。

    安全性前提＝「作用域内只读」（本仓既有纪律：写路径在聚合**之后**才发生）。四个调用点
    （regression_score / quality_depth_scan / conformance_report / output_forms）都是纯读聚合入口。
    """
    global _READ_MEMO, _DIR_MEMO, _PAT_MEMO, _TREE_MEMO, _DIGEST_MEMO
    outermost = _READ_MEMO is None
    if outermost:
        _READ_MEMO, _DIR_MEMO, _PAT_MEMO, _TREE_MEMO, _DIGEST_MEMO = {}, {}, {}, {}, {}
    try:
        yield
    finally:
        if outermost:
            _READ_MEMO = _DIR_MEMO = _PAT_MEMO = _TREE_MEMO = _DIGEST_MEMO = None


def _fast_glob_supported(pattern: str) -> bool:
    """本模块自走的枚举支持的**模式子集**：段级 `**` + 段内 `*` / `?`。

    超出子集一律**回退** `Path.glob`——宁可慢，也不许悄悄改语义（回退面：字符类 `[…]`、
    以 `**` 结尾的模式）。子集与 `Path.glob` 的**逐模式等价**由单测钉住（含点文件）。
    """
    pat = str(pattern)
    if "[" in pat or "]" in pat:
        return False
    return pat.split("/")[-1] != "**"


@functools.lru_cache(maxsize=512)
def _segment_regex(part: str) -> "re.Pattern[str]":
    """把单个路径段编译成正则：`*` → 任意（不含 `/`），`?` → 单字符（不含 `/`）。"""
    out = []
    for ch in part:
        if ch == "*":
            out.append("[^/]*")
        elif ch == "?":
            out.append("[^/]")
        else:
            out.append(re.escape(ch))
    return re.compile("^" + "".join(out) + "$")


@functools.lru_cache(maxsize=512)
def _compiled_parts(pattern: str):
    """把模式**一次**编译成「段 → 正则（`**` 记为 None）」的元组。

    依据（实测）：走查版与清单版过去都**每次调用**重新编译段正则——一次 evaluate 里
    `_segment_regex` 被调 **31995** 次、`re.escape` **164752** 次（自耗时合计 ~0.29 s）。
    模式的编译结果是**模式的纯函数**（与文件系统无关），故可长期记忆，不存在陈旧问题。
    """
    return tuple(None if part == "**" else _segment_regex(part)
                 for part in (p for p in str(pattern).split("/") if p != ""))


def _scandir_list(path: str):
    """列目录（绝不抛）：目录不可读/已消失时返回空——枚举面按「不存在」处理。

    常驻层命中即**零 IO**（守护带监听时安装，见 `_RESIDENT` 的说明）；否则照旧 `os.scandir`。
    """
    key = _resident_key(path)
    if _RESIDENT is not None:
        hit = _RESIDENT["dirs"].get(key)
        if hit is not None:
            return hit
    try:
        with os.scandir(path) as it:
            entries = list(it)
    except OSError:
        return []
    if _RESIDENT is not None and _resident_under(key) \
            and len(_RESIDENT["dirs"]) < _RESIDENT_DIR_MAX:
        packed = []
        for entry in entries:
            try:
                packed.append(_Entry(entry.name, entry.path, entry.is_dir(),
                                     entry.is_file(), entry.is_symlink()))
            except OSError:                     # 枚举与取值之间消失的条目 → 当作不存在
                continue
        _RESIDENT["dirs"][key] = packed
        return packed
    return entries


def _enumerate_rel(root_abs: str, pattern: str) -> List[str]:
    """`os.scandir` **单遍**枚举（相对 root 的 posix 路径）。语义对齐 `Path.glob`：

    - `**` 消费**零或多层目录**，且不进入符号链接目录（与 pathlib 的 `_RecursiveWildcardSelector` 同）；
    - `*` / `?` 不跨 `/`；**含点文件**（pathlib 的 glob 不隐藏点文件，这里也不）；
    - 末段只收**文件**（pathlib 的 glob 末段用 `is_file()`，跟随符号链接——这里同样跟随）。

    为什么不用 `Path.glob`：它的 `**` 逐层重入，实测本仓 `community/*/outputs/**/*`（1156 件）
    要 236 ms，而 `os.scandir` 单遍约 90 ms——指纹每次只读调用都要按输入面枚举一遍。
    """
    parts = _compiled_parts(pattern)
    out: List[str] = []

    def match(dir_abs: str, rel: str, i: int) -> None:
        if i >= len(parts):
            return
        rx = parts[i]
        if rx is None:                                        # `**`
            match(dir_abs, rel, i + 1)                       # 零层：当前目录直接续匹配
            for entry in _scandir_list(dir_abs):
                try:
                    if entry.is_dir() and not entry.is_symlink():
                        match(entry.path, rel + entry.name + "/", i)
                except OSError:
                    continue
            return
        last = (i == len(parts) - 1)
        for entry in _scandir_list(dir_abs):
            if not rx.match(entry.name):
                continue
            try:
                if last:
                    if entry.is_file():
                        out.append(rel + entry.name)
                elif entry.is_dir():
                    match(entry.path, rel + entry.name + "/", i + 1)
            except OSError:
                continue

    match(root_abs, "", 0)
    return sorted(out)


def iter_files(root, pattern: str) -> List[str]:
    """按模式枚举**文件**（相对 root 的 posix 路径，已排序）。作用域内按 (root, 模式) 记忆。

    作用域与读缓存同生命周期（`read_memo` 出口即清），因此**不跨调用复用**——与「新起进程
    看同一份仓库事实」的冷却语义一致，不存在陈旧目录清单。
    """
    root_abs = os.path.abspath(str(root))
    key = (os.path.normcase(root_abs), str(pattern))
    if _PAT_MEMO is not None:
        hit = _PAT_MEMO.get(key)
        if hit is not None:
            return list(hit)
    prefix = _fixed_prefix(str(pattern))
    tree = _tree_hit(root_abs, prefix)          # 子树清单已在作用域里 ⇒ 内存里筛，零 IO
    if tree is not None:
        parts = _compiled_parts(str(pattern))
        got = tuple(rel for rel in tree
                    if _match_parts(rel.split("/"), parts))
    elif _fast_glob_supported(pattern):
        got = tuple(_enumerate_rel(root_abs, str(pattern)))
    else:
        base = Path(root)
        got = tuple(sorted(p.relative_to(base).as_posix()
                           for p in base.glob(str(pattern)) if p.is_file()))
    if _PAT_MEMO is not None:
        _PAT_MEMO[key] = got
    return list(got)


def _fixed_prefix(pattern: str) -> str:
    """模式里**通配符之前**的固定目录前缀（`a/b/*.md` → `a/b`；全固定件 → 其所在目录）。

    只用于「子树清单是否已在作用域里」的定位，不参与匹配语义。
    """
    parts = [p for p in str(pattern).split("/") if p != ""]
    keep: List[str] = []
    for part in parts[:-1]:
        if any(ch in part for ch in "*?["):
            break
        keep.append(part)
    return "/".join(keep)


def _match_parts(segments, parts) -> bool:
    """把**整条相对路径**的分段与模式分段做匹配（`**` 消费零或多段）——与走查版语义同源。

    与 `_enumerate_rel` 共用 `_segment_regex`，两版的等价性由 `FastGlobTest` 同时覆盖
    （走查版与「子树清单」版各测一遍，防止两条路径漂移）。
    """
    def step(si: int, pi: int) -> bool:
        """下标版递归：不做切片（切片在 4.6 万次调用里本身就值 ~0.1 s）。"""
        if pi >= len(parts):
            return si >= len(segments)
        rx = parts[pi]
        if rx is None:                                   # `**`：零段或多段
            if step(si, pi + 1):
                return True
            return si < len(segments) and step(si + 1, pi)
        if si >= len(segments):
            return False
        if not rx.match(segments[si]):
            return False
        return step(si + 1, pi + 1)

    return step(0, 0)


def tree_files(root, rel_dir: str = "") -> List[str]:
    """`rel_dir` 子树内**全部文件**（仓库相对 posix 路径，已排序）。作用域内按目录记忆。

    给「要按多个模式反复匹配同一棵树」的调用方用（`layer_model` 的真源面展开就是这种形状）。
    作用域与读缓存同生命周期：出口即清，不跨调用复用。
    """
    root_abs = os.path.abspath(str(root))
    key = os.path.normcase(os.path.join(root_abs, str(rel_dir or "")))
    if _TREE_MEMO is not None:
        hit = _TREE_MEMO.get(key)
        if hit is not None:
            return list(hit)
    out: List[str] = []

    def walk(dir_abs: str, rel: str) -> None:
        for entry in _scandir_list(dir_abs):
            try:
                if entry.is_dir():
                    if not entry.is_symlink():
                        walk(entry.path, rel + entry.name + "/")
                elif entry.is_file():
                    out.append(rel + entry.name)
            except OSError:
                continue

    start_rel = "" if not rel_dir else str(rel_dir).strip("/") + "/"
    walk(key, start_rel)
    got = tuple(sorted(out))
    if _TREE_MEMO is not None:
        _TREE_MEMO[key] = got
    return list(got)


def _tree_hit(root_abs: str, rel_dir: str):
    """作用域里**已有**的子树清单（没有就返回 None——不主动去建，免得比定向走查更贵）。"""
    if _TREE_MEMO is None:
        return None
    return _TREE_MEMO.get(os.path.normcase(os.path.join(root_abs, str(rel_dir or ""))))


def read_text_cached(path) -> str:
    """读文本：在 `read_memo()` 作用域内，同一**文件**只读一次（含解码）；域外就是普通读。

    键做**路径归一化**（`normcase(abspath)`）：各扫描器传进来的写法不同（`"."/相对路径`
    vs 绝对路径），不归一会指向不同键、共享失效——实测就是这样（同一份资产仍被读 4 次）。
    """
    key = _resident_key(path)
    if _READ_MEMO is not None:
        hit = _READ_MEMO.get(key)
        if hit is not None:
            return hit
    if _RESIDENT is not None:                   # 常驻层：跨请求复用（按监听路径失效）
        hit = _RESIDENT["text"].get(key)
        if hit is not None:
            if _READ_MEMO is not None:
                _READ_MEMO[key] = hit
            return hit
    text = Path(path).read_text(encoding="utf-8")
    if _READ_MEMO is not None:
        _READ_MEMO[key] = text
    if _RESIDENT is not None and _resident_under(key) \
            and len(_RESIDENT["text"]) < _RESIDENT_TEXT_MAX:
        _RESIDENT["text"][key] = text
    return text


def read_bytes_cached(path) -> bytes:
    """读字节：同上（`_recompute_entry` 的逐字节比对用）。"""
    key = _resident_key(path)
    if _READ_MEMO is not None:
        hit = _READ_MEMO.get("b:" + key)
        if hit is not None:
            return hit                          # type: ignore[return-value]
    if _RESIDENT is not None:                   # 同上（二进制面：图片等非 UTF-8 件）
        hit = _RESIDENT["bytes"].get(key)
        if hit is not None:
            if _READ_MEMO is not None:
                _READ_MEMO["b:" + key] = hit
            return hit
    raw = Path(path).read_bytes()
    if _READ_MEMO is not None:
        _READ_MEMO["b:" + key] = raw            # type: ignore[assignment]
    if _RESIDENT is not None and _resident_under(key) \
            and len(_RESIDENT["bytes"]) < _RESIDENT_TEXT_MAX:
        _RESIDENT["bytes"][key] = raw
    return raw


def content_fingerprint(root: str, patterns) -> str:
    """按**内容**给一组文件取指纹（键即内容 ⇒ 内容一变指纹就变，无陈旧风险）。

    用于「派生结果的跨调用缓存」：先在本模块里**穷举输入面**（写成 patterns），再拿指纹当键。
    走共享读（`read_text_cached`），这些文件本来就要被读，指纹近乎白拿。

    枚举走 `iter_files`（`os.scandir` 单遍 + 作用域内记忆）：实测本仓一次 `evaluate` 里
    指纹占 **926 ms / 31%**，而其中「枚举」一项就 463 ms（`community/*/outputs/**/*` 单条
    236 ms 是 pathlib `**` 的逐层重入）——换成单遍后同一条降到 ~90 ms。

    2026-09-29 再进一步：**逐件摘要**（`_payload_digest`）也进两级缓存——作用域内一份、常驻层一份
    （按监听变更**逐件**失效）。于是「面再宽」也只剩「枚举 + 合并」：实测 8 个面（含 3439 件的宽面）
    的见证成本从 **228 ms 降到 ~30 ms**，而**指纹口径逐位不变**（同一件同一 payload ⇒ 同一摘要）。
    """
    h = hashlib.sha256()
    for pat in patterns:
        for rel in iter_files(root, str(pat)):
            h.update(rel.encode("utf-8"))
            h.update(b"\x00")
            h.update(_payload_digest(root, rel))
            h.update(b"\x01")
    return h.hexdigest()


def _payload_digest(root: str, rel: str) -> bytes:
    """单件的**内容摘要**（`sha256` 的 raw digest）；键＝文件，随监听变更逐件失效。

    payload 口径与 `content_fingerprint` 历史口径**完全一致**：能按 UTF-8 读出的文本按
    `encode("utf-8")`（与重编码后的字节等价），读不出（图片等）按**原始字节**——所以摘要换来的
    加速不改变任何已有指纹值。
    """
    path = os.path.join(str(root), *rel.split("/"))
    key = _resident_key(path)
    if _DIGEST_MEMO is not None:
        hit = _DIGEST_MEMO.get(key)
        if hit is not None:
            return hit
    if _RESIDENT is not None:
        hit = _RESIDENT["digest"].get(key)
        if hit is not None:
            if _DIGEST_MEMO is not None:
                _DIGEST_MEMO[key] = hit
            return hit
    try:
        payload = read_text_cached(path).encode("utf-8")
    except UnicodeDecodeError:
        # 非 UTF-8（图片等二进制）按**字节**取指纹：输入面一旦变宽就会遇到它们，
        # 这里**不许崩**（崩了等于把「多放一个二进制附件」变成「命令直接失败」）。
        payload = read_bytes_cached(path)
    digest = hashlib.sha256(payload).digest()
    if _DIGEST_MEMO is not None:
        _DIGEST_MEMO[key] = digest
    if _RESIDENT is not None and _resident_under(key):
        _RESIDENT["digest"][key] = digest
    return digest


#: `scan()` 派生结果的跨调用缓存（键 = 输入内容指纹）。输入面见 `SCAN_INPUTS`——**穷举**，
#: 所以「输入一变必然换键」，不需要随请求清空。
_SCAN_CACHE: Dict[str, Tuple[List[str], Dict[str, int]]] = {}
#: `scan()` 的全部输入（逐一对照实现枚举：证据 id 的 registry + 模块文档 + 协议包声明 +
#: 导出契约 manifest + 门禁脚本里的证据名）。
SCAN_INPUTS = ("desktop/src/core/registry.json",
               "04_模块库/*/*.md",
               "community/*/modules/*.md",
               "community/*/protocol.yaml",
               "protocol/export_conformance.json",
               "verify.sh")


def load_yaml(text: str) -> Any:
    """模块间**共用**的安全 YAML 载入（libyaml 优先；无 PyYAML 即报，不静默降级）。

    新调用点一律走这里，别再各写一份 `yaml.safe_load`——否则「同一个仓库里两套解析器」
    既慢又会有语义分叉。

    注意：这里**直接实例化安全加载器**（`SAFE_LOADER(text)` + `get_single_data()`），与
    `yaml.safe_load()` 逐字同语义，但不写 `yaml.load(...)`——后者是纯度扫描 R6 登记的
    危险 sink（CWE-502 非安全载入），不该为了少写两行把禁用面叫回来。
    """
    if yaml is None:
        raise RuntimeError("PyYAML 不在（修复指引：pip install pyyaml）")
    loader = SAFE_LOADER(text)
    try:
        return loader.get_single_data()
    finally:
        loader.dispose()


def load_yaml_cached(body: str) -> Any:
    """按**正文文本**缓存的安全 YAML 载入（键即内容 ⇒ 文本一变键就变，无陈旧风险）。

    与 `_fence_yaml` 的缓存同一条纪律，只是键更贴近「自己抽正文」的调用方：管道加载器与
    概念图加载器各自用正则抽出正文后直接解析，过去因此**每轮全量重解析**（实测热跑 score
    里仍有 325 次 YAML 解析）。解析失败按原样抛出、不缓存（确定性）。
    """
    if body in _BODY_CACHE:
        return _BODY_CACHE[body]
    got = load_yaml(body)
    if len(_BODY_CACHE) >= _BODY_CACHE_MAX:
        _BODY_CACHE.clear()
    _BODY_CACHE[body] = got
    return got


def _read_json(path: str) -> Tuple[Any, str]:
    try:
        return json.loads(read_text_cached(path)), ""
    except Exception as exc:
        return None, str(exc)


def _parse_fence_yaml(text: str, marker: str) -> Any:
    """真的去扫围栏并交给 PyYAML（未命中缓存时走这里）；未命中 / 解析失败 → None。"""
    for m in FENCE.finditer(text):
        body = m.group(1)
        if marker not in body:
            continue
        try:
            parsed = load_yaml_cached(body) if yaml is not None else None
        except Exception:
            return None
        if isinstance(parsed, dict):
            return parsed
    return None


def _fence_yaml_cached(text: str, marker: str) -> Any:
    """`(marker, 文本)` → 解析结果（None = 没找到该围栏或解析失败）。见 `_fence_yaml`。"""
    key = (marker, text)
    if key not in _FENCE_CACHE:
        if len(_FENCE_CACHE) >= _FENCE_CACHE_MAX:
            _FENCE_CACHE.clear()
        _FENCE_CACHE[key] = _parse_fence_yaml(text, marker)
    return _FENCE_CACHE[key]


def _fence_yaml(text: str, marker: str) -> Dict[str, Any]:
    """取围栏 ```yaml 里含 marker 的第一个块（未命中 → `{}`）；结果按**文本本身**缓存。

    效率（实测）：`nf doctor` 里同一批 **248 份**模块文档被恰好解析**两遍**（496 次
    `yaml.safe_load`，累计 **1.47 s ≈ 体检总时的 74%**）——PyYAML 的扫描器是纯 Python，
    单份 ~3 ms，重复一遍就是纯亏。缓存键取文本本身（不是路径）：文本没变必然同结果，
    文本一变键就变，所以**不存在「改了文件还读到旧值」的陈旧风险**——这正是它敢跨命令
    常驻的原因。返回值一律给**深拷贝**，调用方就地改动不会串味。
    """
    got = _fence_yaml_cached(text, marker)
    return copy.deepcopy(got) if got is not None else {}


def _fence_yaml_opt(text: str, marker: str) -> Optional[Dict[str, Any]]:
    """同 `_fence_yaml`，但「没找到 / 解析失败」返回 None（schema_lint 的既有语义）。

    与 `_fence_yaml` **同一份缓存、同一次解析**——同一段文本被两个模块各解析一遍是纯重复。
    """
    got = _fence_yaml_cached(text, marker)
    return copy.deepcopy(got) if got is not None else None


def _module_docs(root: str) -> List[str]:
    """模块文档清单（**一次只读调用内只走一遍文件系统**——见 `read_memo`）。

    实测：一次 `evaluate` 里本函数被调 **5** 次（各扫描器各自重走 `04_模块库` + `community/*/modules`），
    合计 167 ms。作用域与读缓存同生命周期，出口即清——下一次调用照常重新列目录，故不会陈旧。
    """
    key = os.path.normcase(os.path.abspath(str(root)))
    if _DIR_MEMO is not None and key in _DIR_MEMO:
        return list(_DIR_MEMO[key])
    out: List[str] = []
    for sub in ["04_模块库"]:
        base = os.path.join(root, sub)
        if os.path.isdir(base):
            for dirpath, _, files in os.walk(base):
                out += [os.path.join(dirpath, f) for f in files if f.endswith(".md")]
    pkg_dir = os.path.join(root, "community")
    if os.path.isdir(pkg_dir):
        for pkg in sorted(os.listdir(pkg_dir)):
            mdir = os.path.join(pkg_dir, pkg, "modules")
            if os.path.isdir(mdir):
                out += [os.path.join(mdir, f) for f in sorted(os.listdir(mdir)) if f.endswith(".md")]
    out = sorted(out)
    if _DIR_MEMO is not None:
        _DIR_MEMO[key] = out
    return list(out)


def _evidence_ids(root: str, reg: Any = None) -> List[str]:
    """官方 registry modules[] + community registry protocols[].module_ids（装配在册证据）。

    `reg` 可由调用方传入（同一次扫描里 registry.json 只该读一次——见 `scan`）。
    """
    if reg is None:
        reg, _ = _read_json(os.path.join(root, "desktop", "src", "core", "registry.json"))
    ids: List[str] = []
    if isinstance(reg, dict):
        for m in reg.get("modules") or []:
            if isinstance(m, dict) and isinstance(m.get("id"), str):
                ids.append(m["id"])
        for p in reg.get("protocols") or []:
            for mid in (p.get("module_ids") or []):
                if isinstance(mid, str):
                    ids.append(mid)
    return ids


def scan(root: str = ".") -> Tuple[List[str], Dict[str, int]]:
    """检查（外层）：派生结果按**输入内容指纹**跨调用缓存（输入面见 `SCAN_INPUTS`，已穷举）。

    依据（实测）：本函数一次调用约 0.4 s，而它只依赖那 6 类输入——守护逐请求清空按 root 的
    缓存时，这些派生账会被白交一遍。键即内容 ⇒ 输入一变指纹就变，故不需要随请求清空。

    再叠一层**持久**缓存（`core.disk_cache`：键里还含**代码面 + 运行时**）：新进程也能免付
    这笔派生账。读回时按 `result_pair_ok` 校验形状，不可信即重算。

    「读到的文件必须全部落在输入面内」有判据守着（test_conformance_scan.DerivedResultCacheTest）：
    将来给本函数加新读取，判据会先红、逼着把新输入补进来——不会悄悄读到陈旧结果。
    """
    fp = content_fingerprint(root, SCAN_INPUTS)
    hit = _SCAN_CACHE.get(fp)
    if hit is None:
        from core import disk_cache
        dkey = disk_cache.key("scan", fp, root=root)
        cached = disk_cache.load("scan", dkey, validate=result_pair_ok)
        if cached is None:
            got = _scan_impl(root)
            disk_cache.store("scan", dkey,
                             {"issues": list(got[0]), "stats": got[1]})
        else:
            got = (list(cached["issues"]), dict(cached["stats"]))
        hit = _SCAN_CACHE[fp] = copy.deepcopy(got)
    return copy.deepcopy(hit[0]), copy.deepcopy(hit[1])


def result_pair_ok(value) -> bool:
    """持久缓存读回值的形状校验：`{"issues": [...], "stats": {...}}`（否则当未命中）。"""
    return (isinstance(value, dict) and set(value) == {"issues", "stats"}
            and isinstance(value["issues"], list) and isinstance(value["stats"], dict))


#: 通用「内容键派生结果」缓存的**进程内**层：tag → {输入面指纹: {"issues":…, "stats":…}}。
#: 与各派生自己的专用缓存同一条纪律（键即内容），只是把「指纹 → 缓存 → 落盘 → 校验 → 深拷贝」
#: 这套骨架收成一处，新派生接入只需三行（见 `memo_pair` 的调用示例）。
_DERIVED_MEMO: Dict[str, Dict[str, Any]] = {}


def memo_pair(tag: str, patterns, impl, root: str = ".",
              require_resident: bool = False, keep: int = 8):
    """`(issues, stats)` 形状的派生结果缓存（**进程内 + 持久**两层；键即内容）。

    纪律与 `scan()` 完全一致：输入面（`patterns`，须穷举）变 ⇒ 指纹变 ⇒ 必重算；持久层键里
    另含代码面 + 运行时（`disk_cache.key`）；读回必过 `result_pair_ok`；一切 IO 尽力而为。

    `require_resident=True` 给**宽输入面**用：只在常驻语料层在位时才走缓存——那时指纹的读盘
    成本几乎为零（正文已在内存，只剩枚举 + 哈希，实测 3.5 MB 语料 ~33 ms），而冷进程里宽面指纹
    要把整棵语料重读一遍（实测 ~1.0 s），比直接算更贵，所以**宁可不缓存**。
    """
    if require_resident and not resident_active():
        return impl(root)
    fp = content_fingerprint(root, patterns)
    mem = _DERIVED_MEMO.setdefault(tag, {})
    hit = mem.get(fp)
    if hit is None:
        from core import disk_cache
        dkey = disk_cache.key(tag, fp, root=root)
        packed = disk_cache.load(tag, dkey, validate=result_pair_ok)
        if packed is None:
            got = impl(root)
            packed = {"issues": list(got[0]), "stats": got[1]}
            disk_cache.store(tag, dkey, packed)
        if len(mem) >= keep:
            mem.clear()
        mem[fp] = packed
        hit = packed
    return copy.deepcopy(list(hit["issues"])), copy.deepcopy(dict(hit["stats"]))


def _scan_impl(root: str = ".") -> Tuple[List[str], Dict[str, int]]:
    issues: List[str] = []
    if yaml is None:
        issues.append("PyYAML 不在（conformance_scan 依赖仓库既有 yaml 依赖）")
        return issues, {"modules_mc": 0, "packages": 0, "export_items": 0}

    # registry.json 只读一次：过去它在**每个社区包的循环体里**被重读一遍（实测 112 次
    # ≈ 0.09 s，纯重复 IO + JSON 解析），现在提到扫描开头，两个用处共用同一份。
    reg, _ = _read_json(os.path.join(root, "desktop", "src", "core", "registry.json"))
    evidence = set(_evidence_ids(root, reg))
    reg_ids = {p.get("id") for p in (reg or {}).get("protocols") or []}

    modules_mc = 0
    #: 模块 id 全局唯一（01 §1.6.11：module id 是全局寻址面）——登记面由 check14 ⑤b 管
    #: `module_id_range` 声明；但**同一包内两个模块文件声明同一 mc.id** 此前无判据，
    #: 运行时索引为 first-wins 静默择一（mcp_runtime._resolve_module / pipelinerun._module_files），
    #: 会让「看起来唯一」的编号实际指向不确定的模块。此处补文件级唯一判据（极端渗透 D3）。
    seen_mc_id: dict = {}
    for doc in _module_docs(root):
        rel = os.path.relpath(doc, root).replace(os.sep, "/")
        try:
            text = read_text_cached(doc)      # 共享语料：同一份模块文档一次只读一遍
        except Exception as exc:
            issues.append(f"{rel}: 读取失败 {exc}")
            continue
        parsed = _fence_yaml(text, "machine_contract")
        if "machine_contract" not in parsed:
            continue
        mc = parsed["machine_contract"]
        mid = str((mc or {}).get("id") or "")
        if mid:
            if mid in seen_mc_id:
                issues.append("%s: 模块 id 与 %s 重复（mc.id=%s）——编号是全局寻址面，"
                              "运行时索引会静默择一，须改号"
                              "（修复指引：按 01 §1.6.11 换类内段号或 M91-M99 段号）"
                              % (rel, seen_mc_id[mid], mid))
            else:
                seen_mc_id[mid] = rel
        modules_mc += 1
        declared = mc.get("conformance")
        if declared not in ("L1", "L2", "L3"):
            issues.append(f"{rel}: machine_contract 缺/非法 conformance 声明 {declared!r}")
            continue
        mid = mc.get("id")
        provable = 2 if isinstance(mid, str) and mid in evidence else 1
        order = {"L1": 1, "L2": 2, "L3": 3}
        if order[declared] > provable:
            issues.append(
                f"{rel}: conformance 虚标 {declared} > 可证 L{provable}"
                f"（{mid!r} 不在装配在册证据）"
            )

    # community 协议包
    packages = 0
    for proto in sorted(glob.glob(os.path.join(root, "community", "*", "protocol.yaml"))):
        rel = os.path.relpath(proto, root).replace(os.sep, "/")
        try:
            # 共享语料 + 内容键解析（同一份 protocol.yaml 一轮只读一次、只解析一次）
            data = load_yaml_cached(read_text_cached(proto))
        except Exception as exc:
            issues.append(f"{rel}: protocol.yaml 解析失败 {exc}")
            continue
        packages += 1
        pkg = (data or {}).get("package") or {}
        declared = pkg.get("conformance")
        pid = pkg.get("id")
        if declared not in ("L1", "L2", "L3"):
            issues.append(f"{rel}: package 缺/非法 conformance 声明 {declared!r}")
            continue
        provable = 2 if isinstance(pid, str) and pid in reg_ids else 1
        order = {"L1": 1, "L2": 2, "L3": 3}
        if order[declared] > provable:
            issues.append(f"{rel}: conformance 虚标 {declared} > 可证 L{provable}（包不在 registry protocols[]）")

    # 导出契约面 manifest（L3 = 导出契约门禁锁定面）
    manifest_path = os.path.join(root, "protocol", "export_conformance.json")
    manifest, err = _read_json(manifest_path)
    export_items = 0
    if not isinstance(manifest, dict):
        issues.append(f"protocol/export_conformance.json 缺失/解析失败：{err}")
    else:
        verify_txt = ""
        verify_path = os.path.join(root, "verify.sh")
        if os.path.isfile(verify_path):
            with open(verify_path, encoding="utf-8") as fh:
                verify_txt = fh.read()
        for item in manifest.get("items") or []:
            export_items += 1
            if not isinstance(item, dict):
                issues.append("export manifest item 非对象")
                continue
            if item.get("conformance") != "L3":
                issues.append(f"导出面 {item.get('id')}: conformance 应为 L3（导出门禁锁定面）")
            for ev in item.get("evidence") or []:
                if not os.path.isfile(os.path.join(root, ev)):
                    issues.append(f"导出面 {item.get('id')}: 证据文件缺失 {ev}")
            for gate in item.get("gates") or []:
                if gate not in verify_txt:
                    issues.append(f"导出面 {item.get('id')}: 证据门禁 {gate} 不在 verify.sh")

    stats = {
        "modules_mc": modules_mc,
        "packages": packages,
        "export_items": export_items,
    }
    return issues, stats
