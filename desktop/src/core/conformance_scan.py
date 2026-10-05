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
import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from core import lazy_yaml as _lyaml          # PyYAML **惰性**入口（`import yaml` ≈ 40 ms，见其 docstring）
from core import atomic_write

# 导入闭包指纹：由调用方算（持久层不再反向依赖解析层，见 2026-09-29 拆环）
from core import import_graph as _ig


def __getattr__(name):                        # PEP 562：旧名字照旧可用，只是**惰性**（见 core.lazy_yaml）
    if name in ("yaml", "SAFE_LOADER"):
        return _lyaml.module() if name == "yaml" else _lyaml.safe_loader()
    raise AttributeError(name)


FENCE = re.compile(r"(?ms)```yaml\s*(.*?)```")
_T = chr(96) * 3
#: 围栏 YAML 解析缓存：键 = (marker, **文本本身**)，值 = 解析结果或 None（见 `_fence_yaml`）。
#: **负结果（勿重复尝试）**：与 `_BODY_CACHE` 一样**不落盘**——575 块「纯解析」139 ms vs 读回 108 ms。
_FENCE_CACHE: Dict[Tuple[str, str], Any] = {}
_FENCE_CACHE_MAX = 4096
#: 围栏**正文**缓存（键 = 正文本身）：给「自己抽正文」的调用方用（与 `_fence_yaml` 互补）。
_BODY_CACHE: Dict[str, Any] = {}
_BODY_CACHE_MAX = 4096

#: 「一次**只读**扫描内共享语料」的**四层作用域缓存**（`read_memo()` 框定、出口即清；聚合入口都是
#: 纯读 ⇒ 冷却语义与「新起进程」一致）：读文本 / 列目录 / 按模式枚举 / 子树清单。实测一次
#: `evaluate` 打开 7833 次文件而只有 2354 个不同文件（70% 冗余读），并建过 5403 次 `scandir`。
_READ_MEMO: Optional[Dict[str, Any]] = None
_DIR_MEMO: Optional[Dict[Any, Any]] = None       # 键为 ("entries", path) 元组（与 _PAT_MEMO 串行会话隔离）
#: 与读缓存同生命周期的**逐件内容摘要**缓存（键＝文件）：输入面高度重叠，一次调用里每件只算一次。
_DIGEST_MEMO: Optional[Dict[str, bytes]] = None
#: 同生命周期的「按模式枚举」缓存：一次调用内同一 (root, pattern) 只走一遍文件系统（实测 44% 白走）。
_PAT_MEMO: Optional[Dict[Tuple[str, str], Tuple[str, ...]]] = None
#: 同生命周期的「子树文件清单」缓存：键即目录 ⇒ 目录没变清单就一样。
_TREE_MEMO: Optional[Dict[str, Tuple[str, ...]]] = None

#: **常驻层**（`_RESIDENT`）：跨调用、跨请求活着的一份「语料正文 + 目录条目」（依据：改一件后守护
#: 第一条重命令要 1.6–2.0 s，作用域缓存出口即清）。不比响应缓存多信任任何东西：只在守护带监听且
#: 监听健康时安装、只按**确知路径**失效、说不清即整批作废；只缓存监听根之下的件。
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
    _RESIDENT = {"root": root_abs, "dirs": {}, "text": {}, "bytes": {}, "digest": {}, "raw": {},
                 #: **确知变更面**（见 `changed_paths`）：装层时为空且**未确知**（fail-closed——
                 #: 新装的层不知道装之前发生过什么，任何「跳过重算」的推理都不许建立在这上面）。
                 "changed": set(), "changed_known": False}


#: 「确知变更面」的用途：读层一直用它精确失效（`drop_resident`）；**键层**过去没用——于是「改一件、
#: 106 个键都要重算」才发现全没变。有了它，「确知没变」的面直接复用上次的键；说不清就整批作废。
def note_changes(paths) -> None:
    """记下这一批**确知**变更的仓库相对路径（由守护的监听给出；`drop_resident` 会顺手调用）。"""
    if _RESIDENT is None:
        return
    _RESIDENT["changed_known"] = True
    _RESIDENT["changed"].update(str(p) for p in (paths or ()))


def changed_paths() -> Tuple[bool, set]:
    """`(known, paths)`：本进程**确知**自上次取用以来变过哪些仓库相对路径。

    `known=False`（没装层 / 监听说不清 / 刚装层）表示**不许做任何「没变」的推理**——调用方必须按
    「全都可能变了」处理（fail-closed）。
    """
    if _RESIDENT is None or not _RESIDENT.get("changed_known"):
        return False, set()
    return True, set(_RESIDENT["changed"])


def clear_changes() -> None:
    """**请求结束**时清空确知变更面（`daemon.execute` 的收尾调用）。

    为什么必须清（实测 2026-09-29 踩到）：`note_changes` 是**累加**的，而早先没有清空点 ⇒ 变更集会
    单调增长，几条命令之后**每个面都「沾到变更」**，键层复用直接退化成全量重算（探针里四种改动位置
    都报「重算 5 个面」就是这个 bug）。语义与读层一致：确知变更只在**当次请求**内有效。
    """
    if _RESIDENT is None:
        return
    _RESIDENT["changed"] = set()
    _RESIDENT["changed_known"] = False


def matches_any(rel: str, patterns) -> bool:
    """仓库相对路径是否落在任一模式内（语义与 `iter_files` 同源：`**` 跨目录、`*` 不跨）。

    两侧都按 `lower()` 归一：① 监听给的是**小写**相对路径，而模式里有 `INDEX.json` 这种大写；
    ② 归一后若「本该不匹配却被判成匹配」，后果只是**多算一次**（安全方向）——反过来才会陈旧。
    """
    segs = [s.lower() for s in str(rel).replace("\\", "/").split("/")]
    for pat in patterns:
        if _match_parts(segs, _compiled_parts(str(pat).replace("\\", "/").lower())):
            return True
    return False


#: **面指纹**缓存（键 = (绝对 root, 模式元组)）：确知这批变更没一件落在该面内就整个复用（不枚举、
#: 不摘要），说不清一律重算。条目 `{"rels", "index", "digests", "fp"}`；两级复用见 `face_digests`。
_FACE_CACHE: Dict[Any, Any] = {}
_FACE_FP_MAX = 1024
#: 观测位：**整面重算** / **增量更新** 各多少次（复用不算）。判据 `FaceReuseBudgetTest` 用它把
#: 「确知没变就复用」变成**确定性**数字——不能靠数 `content_fingerprint`（那是 0，实测踩过）。
_FACE_FP_STATS: Dict[str, int] = {"recomputes": 0, "incremental": 0}


def _hash_face(rels, digests) -> str:
    """面指纹 = 逐件「相对路径 + \\x00 + 摘要 + \\x01」流式哈希（委托叶子件 `content_face`，避免两份帧）。"""
    from core import content_face as _cf
    return _cf.hash_face(rels, digests)


def face_fingerprint(root: str, patterns) -> str:
    """`content_fingerprint` 的**带确知变更面复用**版本（值逐位相同，只在确知没变时省掉重算）。"""
    return face_digests(root, patterns)[0]


def face_digests(root: str, patterns):
    """`(面指纹, {相对路径: 逐件摘要})`——一次枚举 + 一次摘要**服务两种口径**。

    `face_fingerprint` 就是本函数的第一个返回值（两者值**逐位相同**）。
    依据（实测 2026-09-29）：`asset_density.usage_scan` 的内容键要按**同一张语料面**取指纹，而它随后
    又要给 2815 份语料各取一次逐件摘要当**逐件缓存键**——同一批摘要算了两遍（~5.6 ms）。这个入口把
    「枚举 + 摘要」一次做完，指纹与逐件摘要一起交出。
    """
    pats = tuple(str(p) for p in patterns)
    key = (os.path.normcase(os.path.abspath(str(root))), pats)
    ent = _FACE_CACHE.get(key)
    if ent is not None:
        known, changed = changed_paths()
        if known:
            relevant = [c for c in changed if matches_any(c, pats)]
            if not relevant:
                return ent["fp"], ent["digests"]          # ① 确知没变：连哈希都不算
            # ② 只改内容 ⇒ 增量（成员集合不变）。比对必须**大小写不敏感**：监听的相对路径是小写，
            # `iter_files` 是真实大小写（`M00_数据结构.md`）⇒ 否则一律误判成新增件、增量形同虚设。
            members = [ent["index"].get(str(c).lower()) for c in relevant]
            if all(rel and os.path.isfile(os.path.join(str(root), *rel.split("/")))
                   for rel in members):
                for rel in members:
                    ent["digests"][rel] = _payload_digest(root, rel)
                ent["fp"] = _hash_face(ent["rels"], ent["digests"])
                _FACE_FP_STATS["incremental"] += 1
                return ent["fp"], ent["digests"]
    rels: List[str] = []                                      # ③ 首次 / 成员集合变了：整面重建
    for pat in patterns:
        rels.extend(iter_files(root, str(pat)))
    digests = {rel: _payload_digest(root, rel) for rel in rels}
    fp = _hash_face(rels, digests)
    _FACE_FP_STATS["recomputes"] += 1
    if len(_FACE_CACHE) >= _FACE_FP_MAX:
        _FACE_CACHE.clear()
    _FACE_CACHE[key] = {"rels": rels, "digests": digests, "fp": fp,
                        "index": {rel.lower(): rel for rel in rels}}
    return fp, digests


def resident_active() -> bool:
    return _RESIDENT is not None


def resident_stats() -> Dict[str, int]:
    """常驻层规模（观测 + 判据用）：目录条数 / 正文条数 / 二进制条数。"""
    if _RESIDENT is None:
        return {"dirs": 0, "text": 0, "bytes": 0, "digest": 0, "raw": 0}
    return {"dirs": len(_RESIDENT["dirs"]), "text": len(_RESIDENT["text"]),
            "bytes": len(_RESIDENT["bytes"]), "digest": len(_RESIDENT["digest"]),
            "raw": len(_RESIDENT["raw"])}


def clear_resident() -> None:
    """整批作废（监听说不清 / 不再健康时调用）。"""
    global _RESIDENT
    _RESIDENT = None


def take_resident():
    """**取走**常驻层并返回（供「代码换版时把它搬到新模块」用）；本来没装 → None。

    背景：守护判定代码换版时会把 `core.*` 整块摘掉重载（保证不跑旧代码），于是新的
    `conformance_scan` 会是一个**空层**——不把它搬回来，改一行代码就要让下一条重命令把整棵语料
    重读一遍（实测 ~2 s）。常驻层装的是**仓库事实**（正文 / 目录条目 / 逐件摘要），与代码无关，
    所以跨代码换版保住它是安全的：它的失效仍然只由监听给出的变更路径驱动。
    """
    global _RESIDENT
    res, _RESIDENT = _RESIDENT, None
    return res


def adopt_resident(res) -> None:
    """接手一份常驻层（同一份仓库事实，换的只是装着它的模块对象）。"""
    global _RESIDENT
    _RESIDENT = res


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

    顺带把这一批**确知变更**记进 `changed`（见 `note_changes`）——键层据此判断「哪些面确知没变，
    可以复用上一次的键」。
    """
    res = _RESIDENT
    if res is None:
        return
    note_changes(paths)
    root = res["root"]
    for rel in paths or ():
        key = os.path.normcase(os.path.join(root, str(rel).replace("/", os.sep)))
        res["text"].pop(key, None)
        res["bytes"].pop(key, None)
        res["digest"].pop(key, None)
        res["raw"].pop(key, None)
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
    """把单个路径段编译成正则：`*` → 任意（不含 `/`），`?` → 单字符（不含 `/`）。

    **Windows 上必须大小写不敏感**：`Path.glob` 依托 `os.path.normcase`，在 Windows 上
    `*.md` 能匹配 `UPPER.MD`（既有 glob 用例「后缀不分大小写 + 点文件在面内」已钉死该语义）。
    快速枚举器若按大小写敏感匹配，会在 Windows 上**静默丢件**——实测（他证）：`glob-case`
    合成树上 `Path.glob` 6 件 / 快速枚举 5 件（丢 `.../UPPER.MD`），进而使 `asset usage /
    density / thickness`、`output meter` 与 `content_fingerprint`（**落盘缓存的键**）一起少算。
    """
    out = []
    for ch in part:
        if ch == "*":
            out.append("[^/]*")
        elif ch == "?":
            out.append("[^/]")
        else:
            out.append(re.escape(ch))
    return re.compile("^" + "".join(out) + "$",
                      re.IGNORECASE if os.name == "nt" else 0)


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

    常驻层命中即**零 IO**（守护带监听时安装，见 `_RESIDENT` 的说明）；**冷进程**也没必要重复走：
    本次只读调用内每个目录只列一遍（`_DIR_MEMO`，键带 `entries` 前缀，免得与 `_module_docs` 撞键）
    ——实测一次冷跑 2768 次 `scandir` 只覆盖 907 个目录（3.0 倍重复），而 2000 次 `scandir` 本机要
    ~306 ms：宽面各枚举一遍时，这笔重复是纯浪费。
    """
    key = _resident_key(path)
    if _RESIDENT is not None:
        hit = _RESIDENT["dirs"].get(key)
        if hit is not None:
            return hit
    dir_memo = _DIR_MEMO
    memo = ("entries", key) if dir_memo is not None else None
    if memo is not None and dir_memo is not None:
        hit = dir_memo.get(memo)
        if hit is not None:
            return hit
    try:
        with os.scandir(path) as it:
            entries = list(it)
    except OSError:  # 目录列不到 ⇒ 空清单（IO/权限问题；该类缺口由对应门禁另行报出，见 AUD-0016）
        return []
    if memo is not None and dir_memo is not None:
        dir_memo[memo] = entries
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
            except OSError:  # 尽力而为：跳过不可读/不可解析项；该类缺口由对应门禁另行报出（见 AUD-0016）
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
            except OSError:  # 尽力而为：跳过不可读/不可解析项；该类缺口由对应门禁另行报出（见 AUD-0016）
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
    # **一次物理读服务三种口径**：字节→文本按「通用换行」解出（与 `Path.read_text("utf-8")` 逐字节
    # 一致，判据 `ResidentRawEquivalenceTest`），摘要直接吃同一份字节（见 `_payload_digest`）。
    raw = _raw_bytes(path, key)
    text = _decode_text(raw)
    if _READ_MEMO is not None:
        _READ_MEMO[key] = text
    if _RESIDENT is not None and _resident_under(key) \
            and len(_RESIDENT["text"]) < _RESIDENT_TEXT_MAX:
        _RESIDENT["text"][key] = text
    return text


def _raw_bytes(path, key: str) -> bytes:
    """取**原始字节**（作用域 + 常驻层优先）：一次物理读之后，文本/字节/摘要三种口径都从这里出。

    读法（实测 2799 件 18.9 MB）：`buffering=0`（裸 FileIO）357 ms 最快，pathlib 408 / 缓冲 532 /
    `os.open` 510 ms。字节进 `_READ_MEMO["b:"+key]` ⇒ 摘要与文本**共用同一次物理读**。
    """
    if _READ_MEMO is not None:
        hit = _READ_MEMO.get("b:" + key)
        if hit is not None:
            return hit
    if _RESIDENT is not None:
        hit = _RESIDENT["raw"].get(key)
        if hit is not None:
            if _READ_MEMO is not None:
                _READ_MEMO["b:" + key] = hit
            return hit
    # 读侧短重试（2026-09-30）：并发原子写（`os.replace`）下 Windows 读者会瞬时拿到
    # PermissionError（WinError 5/32）——实测 119 万次读里 1055 次（≈0.09%）。这里是全仓
    # 语料的**唯一物理读**入口，故重试接在这里即可覆盖 purity / layer_model / 各 check。
    raw = atomic_write.read_bytes(path)
    if _READ_MEMO is not None:
        _READ_MEMO["b:" + key] = raw
    if _RESIDENT is not None and _resident_under(key) \
            and len(_RESIDENT["raw"]) < _RESIDENT_TEXT_MAX:
        _RESIDENT["raw"][key] = raw
    return raw


def _decode_text(raw: bytes) -> str:
    """原始字节 → 文本：与 `Path.read_text(encoding="utf-8")` 同语义（含**通用换行**翻译）。"""
    import io as _io
    with _io.TextIOWrapper(_io.BytesIO(raw), encoding="utf-8", newline=None) as wrapper:
        return wrapper.read()


def read_bytes_cached(path) -> bytes:
    """读字节：同上（`_recompute_entry` 的逐字节比对用）。作用域与 `raw` 层都归 `_raw_bytes`，
    本函数只多一层「二进制面」常驻条目（`_RESIDENT["bytes"]`）；2026-09-29 去重掉抄一遍的 20 行。"""
    key = _resident_key(path)
    if _RESIDENT is not None:
        hit = _RESIDENT["bytes"].get(key)
        if hit is not None:
            if _READ_MEMO is not None:
                _READ_MEMO["b:" + key] = hit
            return hit
    raw = _raw_bytes(path, key)
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
    rels: List[str] = []
    for pat in patterns:
        rels.extend(iter_files(root, str(pat)))
    return fingerprint_of(root, rels)


def fingerprint_of(root: str, rels) -> str:
    """按**给定的相对路径清单**取内容指纹（口径与 `content_fingerprint` 逐位相同）。

    为什么要这个入口（2026-09-29 实测）：`content_fingerprint` 每调一次就要**枚举一遍面**，而
    `output_forms` 的逐包内容键是按包拼模式调的——470 个包级模式 ⇒ 一次 `nf score` 里
    `iter_files` 被调 **619 次（35.5 ms）**，其中 ~424 次是「同一批面按包切」。能一次枚举、
    按包切片，就只剩四次枚举。
    """
    h = hashlib.sha256()
    for rel in rels:
        h.update(rel.encode("utf-8"))
        h.update(b"\x00")
        h.update(_payload_digest(root, rel))
        h.update(b"\x01")
    return h.hexdigest()


def _payload_digest(root: str, rel: str) -> bytes:
    """单件的**内容摘要**（`sha256` 的 raw digest）；键＝文件，随监听变更逐件失效。

    payload 口径与历史口径**完全一致**：能按 UTF-8 读出的文本按 encode("utf-8")（与重编码后的
    字节等价），读不出（图片等）按**原始字节**。**快路径**：正文无 `\\r` 时「解码再编码」是恒等
    变换（`\\r` 是通用换行翻译的唯一触发器）⇒ 直接摘要原始字节（本仓 2799 件 0 件含 CR，省 ~100 ms）。
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
    raw = _raw_bytes(path, key)                     # 一次物理读：文本口径也从这份字节解出
    if b"\r" in raw:
        try:
            raw = _decode_text(raw).encode("utf-8")  # 有 CR 才需要通用换行翻译后再编码
        except UnicodeDecodeError:
            pass       # 非 UTF-8（图片等）按**字节**取指纹：多放个二进制附件不该让命令失败
    digest = hashlib.sha256(raw).digest()
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

    注意：这里**直接实例化安全加载器**（`safe_loader()(text)` + `get_single_data()`），与
    `yaml.safe_load()` 逐字同语义，但不写 `yaml.load(...)`——后者是纯度扫描 R6 登记的
    危险 sink（CWE-502 非安全载入），不该为了少写两行把禁用面叫回来。
    """
    loader_cls = _lyaml.safe_loader()
    if loader_cls is None:
        raise RuntimeError("PyYAML 不在（修复指引：pip install pyyaml）")
    loader = loader_cls(text)
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
            parsed = load_yaml_cached(body) if _lyaml.module() is not None else None
        except Exception:  # 围栏 YAML 不可解析 ⇒ None（等价于「本件无该块」）
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

    2026-09-29 再改**枚举器**：原实现是 `os.walk("04_模块库")` + 逐包 `os.listdir(mdir)` +
    `os.path.isdir(mdir)`，在守护口径下每次新内容状态都要重付——实测 **107 次 `listdir` + 113 次
    `isdir` ≈ 21 ms**（占该状态 os/stat 面的四分之一）。改走共享枚举器（目录清单已在常驻层）
    后同一张面 **~0.5 ms**；面**逐件一致**由 `test_conformance_scan.ModuleDocsEquivalenceTest`
    用旧口径原样重算比对，**跨作用域新鲜**由 `ModuleDocsMemoTest` 用合成树盯着。
    """
    key = os.path.normcase(os.path.abspath(str(root)))
    if _DIR_MEMO is not None and key in _DIR_MEMO:
        return list(_DIR_MEMO[key])
    out: List[str] = []
    for pattern in ("04_模块库/**/*.md", "community/*/modules/*.md"):
        for rel in iter_files(root, pattern):
            out.append(os.path.join(root, *rel.split("/")))
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
    fp = face_fingerprint(root, SCAN_INPUTS)
    hit = _SCAN_CACHE.get(fp)
    if hit is None:
        from core import disk_cache
        dkey = disk_cache.key("scan", fp, root=root,
                              code_scope=_ig.code_scope_fingerprint(root, ("core.conformance_scan",)))
        cached = disk_cache.load("scan", dkey, validate=result_pair_ok)
        if cached is None:
            got = _scan_impl(root)
            cached = disk_cache.canonical({"issues": list(got[0]), "stats": got[1]})
            disk_cache.store("scan", dkey, cached)
        # 命中与未命中必须**逐字节一致**：落盘是 `sort_keys` 规范化过的，新算的那份也要过同一道
        # 规范化（否则首跑/次跑换序——见 `disk_cache.canonical` 的取证）。
        hit = _SCAN_CACHE[fp] = (list(cached["issues"]), dict(cached["stats"]))
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
              keep: int = 8, code_modules=None, fp: Optional[str] = None):
    """`(issues, stats)` 形状的派生结果缓存（**进程内 + 持久**两层；键即内容）。

    纪律与 `scan()` 一致：输入面（`patterns`，须穷举）变 ⇒ 指纹变 ⇒ 必重算；持久层键另含代码面 +
    运行时（`disk_cache.key`）；读回必过 `result_pair_ok`；一切 IO 尽力而为。

    `code_modules`（如 `("core.schema_lint",)`）把**代码面**缩到「这段派生自己的导入闭包」——改别的
    模块不再换键（闭包算不出/含动态导入时自动退回整块代码面，见 `disk_cache.key`）。

    `fp` 可传**已经算好的指纹**（口径须与 `content_fingerprint(root, patterns)` 一致）：调用方若有
    更省的取键方式（例如把两张面各自的指纹组合起来），就不必在这里把面再枚举一遍。

    **没有「只在常驻层在位时才缓存」这档开关了**（2026-09-29 删，实测）：那条规矩建立在「冷进程里
    宽面指纹比直接重算更贵」上——今天不成立，冷进程本来就要为别的站点读整棵语料（逐件摘要在同一
    只读作用域内共享），指纹近乎白拿，而重算派生账贵得多。删掉后冷进程首跑 **4481 → 2188 ms**、
    稳态 **1585 → 1183 ms**（结论逐位相同）。
    """
    if fp is None:
        # 走**面指纹**（带「确知没变就复用」）：各站点的面宽窄不一，这一改把「确知变更面」这条
        # 信息铺到**所有** `memo_pair` 站点，而不只是逐包键那一处。
        fp = face_fingerprint(root, patterns)
    mem = _DERIVED_MEMO.setdefault(tag, {})
    hit = mem.get(fp)
    if hit is None:
        from core import disk_cache
        from core import import_graph as _ig
        _scope = _ig.code_scope_fingerprint(root, code_modules) if code_modules else None
        dkey = disk_cache.key(tag, fp, root=root, code_scope=_scope)
        packed = disk_cache.load(tag, dkey, validate=result_pair_ok)
        if packed is None:
            got = impl(root)
            # 未命中也要与命中**逐字节一致**：落盘走 `sort_keys` 规范化 ⇒ 新算的这份同过一道
            # （否则首跑/次跑换序；见 `disk_cache.canonical` 的实证）。
            packed = disk_cache.canonical({"issues": list(got[0]), "stats": got[1]})
            disk_cache.store(tag, dkey, packed)
        if len(mem) >= keep:
            mem.clear()
        mem[fp] = packed
        hit = packed
    return copy.deepcopy(list(hit["issues"])), copy.deepcopy(dict(hit["stats"]))


def _scan_impl(root: str = ".") -> Tuple[List[str], Dict[str, int]]:
    issues: List[str] = []
    if _lyaml.module() is None:
        issues.append("PyYAML 不在（conformance_scan 依赖仓库既有 yaml 依赖）")
        return issues, {"modules_mc": 0, "packages": 0, "export_items": 0}

    # registry.json 只读一次：过去它在**每个社区包的循环体里**被重读一遍（实测 112 次
    # ≈ 0.09 s，纯重复 IO + JSON 解析），现在提到扫描开头，两个用处共用同一份。
    reg, _ = _read_json(os.path.join(root, "desktop", "src", "core", "registry.json"))
    evidence = set(_evidence_ids(root, reg))
    reg_ids = {p.get("id") for p in (reg or {}).get("protocols") or []}

    modules_mc = 0
    #: 模块 id 全局唯一（01 §1.6.11）——登记面由 check14 ⑤b 管；但**两个模块文件声明同一 mc.id**
    #: 此前无判据，运行时索引 first-wins 静默择一（`mcp_runtime` / `pipelinerun`）会让编号指向不确定
    #: 的模块。此处补文件级唯一判据（极端渗透 D3）。
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
    # 走共享枚举器（目录清单已在常驻层）：实测 2026-09-29，`glob.glob(community/*/protocol.yaml)`
    # 一次 **9–13 ms**（占该状态 stat 面的三分之一），同一张面走 `iter_files` 后 **~0.4 ms**。
    for rel in iter_files(root, "community/*/protocol.yaml"):
        proto = os.path.join(root, *rel.split("/"))
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
