"""45 W2 · 资产键语义密度体检（资产质量维机检）。

对 community 各包 assets 与 05 用户自定义资产文件做密度体检：
- 键发现 = 文件名令牌 ∪ 正文键声明（`KEY` / "KEY": / ## KEY，与 AI 通道资源面同口径）；
- 统计每文件 键数/字符数，标出「无键文件」（多为附机制/中文名件，合法——入 unkeyed 计数不 FAIL）；
- FAIL 面只留：文件空或不可读（真异常）。
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from core import conformance_scan as csc
from core import disk_cache


#: 引用度普查的内容键缓存：键 = **语料与键集的 sha256**（见 `usage_scan`）。
#: 必要性（实测）：一次普查 = 1499 个键 × 3.5 MB 语料的逐键子串计数 ≈ **2.7 s**；而
#: 「跑全量评分」的路径（`nf score`、回归单测、发布体检 + 覆盖率通道）会在同一进程里
#: 反复走到这里。键取内容哈希（不是路径）→ 内容没变必然同结果，内容一改键就变，
#: 因此不存在「改了文件还读到旧值」的陈旧风险。
_CENSUS_CACHE: Dict[str, Dict[str, int]] = {}
_CENSUS_CACHE_MAX = 64

#: **逐件**计数的内容键缓存（键 = (该件正文 sha256, 键集 sha256)）：`count_keys_additive` 用它把
#: 「改一件就要重扫 3.5 MB」变成「只重算被改的那一件」。存**稀疏**字典（单件里绝大多数键不出现），
#: 于是 2500 件 × ~30 个非零键 ≈ 75k 条，量级完全可控。
_FILE_COUNT_CACHE: Dict[Any, Dict[str, int]] = {}
_FILE_COUNT_CACHE_MAX = 4096

#: `_keys_of` 的**逐件内容键缓存**（键 = (文件名 stem, 正文 sha256)）。依据（实测 2026-09-29）：
#: `usage_scan` 要为 360 份资产件各跑四个正则取键（实测 6.6 ms），而键集只是**该件正文 + 文件名**
#: 的纯函数——改 `04_模块库`、文档、代码这类与资产无关的件时结果必然不变。
_KEYS_OF_CACHE: Dict[Any, List[str]] = {}
_KEYS_OF_CACHE_MAX = 4096

#: `usage_scan` 的**语料面**（就是它数的那些件）。指纹走常驻层**逐件摘要**，不再把 3.5 MB 正文
#: 逐件 `encode()` 后重哈希一遍（实测那条 2815 件的哈希环占 `usage_scan` 的三分之一）。
CORPUS_PATTERNS = ("04_模块库/**/*.md", "community/**/*.md", "docs/**/*.md")



def _keys_of(path: Path, text: Optional[str] = None) -> List[str]:
    """文件名令牌 ∪ 正文键声明（`text` 可由调用方传入——避免同一份件被读两遍）。"""
    if text is None:
        try:
            text = csc.read_text_cached(path)
        except OSError:
            return sorted(set(re.findall(r"[A-Z][A-Z0-9_]*", path.stem)))
    ck = (path.stem, hashlib.sha256(text.encode("utf-8")).hexdigest())
    hit = _KEYS_OF_CACHE.get(ck)
    if hit is not None:                       # 键集只是**该件正文 + 文件名**的纯函数（键即内容）
        return hit
    keys = set(re.findall(r"[A-Z][A-Z0-9_]*", path.stem))
    head = text[:6000]
    # 条目键面（2026-09-23 对齐）：除大写下划线键外，仓库里还大量使用**带连字符的条目键**
    # （如域包的 `C01-01` / `A08-07` —— 经 asset_get('<资产键>','<条目键>') 真实可寻址）。
    # 原字符集 `[A-Z0-9_]` 看不见它们 → 密度被系统性低估（AI 品类域包扩面后实测暴露）。
    keys.update(re.findall(r"`([A-Z][A-Z0-9_-]{2,})`", head))
    keys.update(re.findall(r"\"([A-Z][A-Z0-9_-]{2,})\"\s*:", head))
    keys.update(re.findall(r"##\s*([A-Z][A-Z0-9_-]{2,})", head))
    got = sorted(keys)
    if len(_KEYS_OF_CACHE) >= _KEYS_OF_CACHE_MAX:
        _KEYS_OF_CACHE.clear()
    _KEYS_OF_CACHE[ck] = got
    return got


#: `scan()` / `thickness_scan()` 的全部输入：就是它们枚举的那两条**资产面**
#: （community 各包的 assets/*.md + 官方用户自定义资产）。两条面都很窄，
#: 所以「改文档/代码」不会作废它们的缓存，只有动资产才重算。
ASSET_INPUTS = ("community/*/assets/*.md", "05_资产库/用户自定义/*.md")


def scan(root: str = ".") -> Tuple[List[str], Dict[str, Any]]:
    """资产台账面体检（原体见 `_scan_impl`）。派生结果按**输入内容指纹**缓存（键即内容）。"""
    return csc.memo_pair("asset-density", ASSET_INPUTS, _scan_impl, root,
                          code_modules=("core.asset_density",))


def _scan_impl(root: str = ".") -> Tuple[List[str], Dict[str, Any]]:
    issues: List[str] = []
    rows = []
    patterns = ["community/*/assets/*.md", "05_资产库/用户自定义/*.md"]
    for pat in patterns:
        # 走共享枚举器（`os.scandir` 单遍 + 作用域内子树清单复用）：同一棵 community
        # 过去被 scan / thickness / usage 各自用 Path.glob/rglob 走了一遍。
        for rel in csc.iter_files(root, pat):
            if rel.rsplit("/", 1)[-1] == "README.md":
                continue
            try:
                text = csc.read_text_cached(Path(root) / rel)
            except OSError as exc:
                issues.append("%s 不可读：%s" % (rel, exc))
                continue
            if not text.strip():
                issues.append("%s 为空档（0 字符）" % rel)
                continue
            keys = _keys_of(Path(rel), text)
            pkg = rel.split("/")[1] if rel.startswith("community") else "官方"
            rows.append({"package": pkg, "file": rel,
                         "keys": len(keys), "key_list": keys,
                         "chars": len(text)})
    n_files = len(rows)
    n_keys = sum(x["keys"] for x in rows)
    n_unkeyed = sum(1 for x in rows if x["keys"] == 0)
    n_tiny = sum(1 for x in rows if x["chars"] < 200)
    stats = {"files": n_files, "keys": n_keys,
             "unkeyed": n_unkeyed, "tiny": n_tiny,
             "avg_keys_per_file": round(n_keys / max(1, n_files), 2)}
    return issues, stats


class _Matcher:
    """键集固定时的 **Aho–Corasick** 自动机：**建一次，多份文本复用**。

    2026-09-29 实测（一个真事故）：上一版把自动机**逐件各建一次**（921 件）——建机成本
    ≈2 ms × 921 ≈ **2.0 s**，比「拼成一整条一次扫完」（0.3 s）**慢 6 倍**。自动机只由**键集**
    决定，所以按键集缓存复用：逐件扫描就只剩 O(该件长度)，而逐件结果又能按内容缓存。
    """

    __slots__ = ("_goto", "_out", "_fail", "keys")

    def __init__(self, keys):
        from collections import deque
        self.keys = [str(k) for k in keys]
        goto: List[Dict[str, int]] = [{}]
        out: List[List[str]] = [[]]
        fail: List[int] = [0]
        for k in self.keys:
            node = 0
            for ch in k:
                nxt = goto[node].get(ch)
                if nxt is None:
                    nxt = len(goto)
                    goto.append({})
                    out.append([])
                    fail.append(0)
                    goto[node][ch] = nxt
                node = nxt
            out[node].append(k)
        queue = deque(goto[0].values())
        while queue:
            node = queue.popleft()
            for ch, nxt in goto[node].items():
                f = fail[node]
                while f and ch not in goto[f]:
                    f = fail[f]
                fail[nxt] = goto[f].get(ch, 0)
                out[nxt] = out[nxt] + out[fail[nxt]]   # 输出沿失败链传播（互相包含的键都算）
                queue.append(nxt)
        self._goto, self._out, self._fail = goto, out, fail

    def counts(self, blob: str) -> Dict[str, int]:
        """一遍扫过 `blob`：按键盘下每次出现的位置，再**按键做非重叠贪心计数**
        （`pos > 上次命中结束位置` 才计数）——`str.count` 的左优先非重叠语义就是这样。"""
        _goto, _out, _fail = self._goto, self._out, self._fail
        positions: Dict[str, List[int]] = {}
        node = 0
        for i, ch in enumerate(blob):
            while node and ch not in _goto[node]:
                node = _fail[node]
            node = _goto[node].get(ch, 0)
            for k in _out[node]:
                positions.setdefault(k, []).append(i - len(k) + 1)
        counts: Dict[str, int] = {}
        for k in self.keys:
            n, last_end = 0, -1
            for pos in positions.get(k, ()):            # 位置天然升序
                if pos > last_end:
                    n += 1
                    last_end = pos + len(k) - 1
            counts[k] = n
        return counts


#: 键集 → 自动机（上限几份：一次普查只用一份键集）。键集变了自然换机，无需手工失效。
_MATCHERS: Dict[str, "_Matcher"] = {}
_MATCHERS_MAX = 4


def _matcher(keys) -> Optional["_Matcher"]:
    """按**键集内容**取自动机；空键 / 单键不值得建机（参考实现更快也更好懂）→ None。"""
    str_keys = [str(k) for k in keys]
    if "" in str_keys or len(str_keys) < 2:
        return None
    key = hashlib.sha256("\x01".join(sorted(str_keys)).encode("utf-8")).hexdigest()
    got = _MATCHERS.get(key)
    if got is None:
        if len(_MATCHERS) >= _MATCHERS_MAX:
            _MATCHERS.clear()
        got = _Matcher(str_keys)
        _MATCHERS[key] = got
    return got


def count_keys(blob: str, keys) -> Dict[str, int]:
    """数每个键在 `blob` 里的出现次数——**与 `str.count` 逐字节同语义**（非重叠、互相包含都算）。

    为什么不用一行 `{k: blob.count(k) for k in keys}`：那是「1499 个键 × 3.5 MB 语料」= **5.2 GB**
    的字符扫描，实测 **3.11 s**（profile 里单笔最大，且每个新内容状态都要重付一遍）。走自动机后
    同一批数字只要 ~0.3 s。等价性由 `test_asset_density.KeyCountEquivalenceTest` 守着
    （随机串 400 例 + 重叠/嵌套/空键边界 + 真语料逐键比对）。
    """
    str_keys = [str(k) for k in keys]
    matcher = _matcher(str_keys)
    if matcher is None:
        return {k: blob.count(k) for k in str_keys}
    return matcher.counts(blob)


def count_keys_additive(texts, keys, digests=None) -> Dict[str, int]:
    """**逐件计数再相加**（等价于把语料用 `"\\n"` 连起来数一次），但**逐件**结果可缓存。

    为什么两者等价（可证）：连接语料用的是 `"\\n"` 分隔，而**任何键都不可能含换行**（资产 id 是
    字母数字 + 分隔符）。于是「跨件匹配」只可能出现在包含该分隔符的位置——而那样的匹配不存在
    ⇒ 逐件计数之和与「拼成一整条再数」**逐键相同**。这条等价性由
    `test_asset_density.KeyCountEquivalenceTest` 在**真语料**上断言（并在合成语料上加负例）。

    为什么不直接数整条：逐件结果可以按**文件内容**缓存（键即内容）——一次真编辑只会让**被改的那一件**
    重算（守护里尤其明显：常驻层已经按路径给出新正文，这里按正文命中），而整条 blob 的指纹一变
    就要把 3.5 MB 重扫一遍。

    fail-closed：键里只要出现换行（当前不可能），就退回整条拼接计数——正确性优先于省算。

    `digests`（可选，与 `texts` 一一对应）让调用方交出**已经算过的内容摘要**（常驻层逐件摘要），
    省掉这里再 `sha256(text.encode())` 一遍——一次新内容状态里那是 2815 次编码 + 哈希（实测 ~5 ms）。
    摘要口径与这里现算的完全一致（同一 payload 语义，见 `conformance_scan._payload_digest`）。
    """
    keys = [str(k) for k in keys]
    if any("\n" in k for k in keys):
        return count_keys("\n".join(texts), keys)
    keys_key = hashlib.sha256("\x01".join(sorted(keys)).encode("utf-8")).hexdigest()
    matcher = _matcher(keys)                        # 自动机按**键集**复用（别逐件重建，实测慢 6 倍）
    totals = {k: 0 for k in keys}
    for idx, text in enumerate(texts):
        dg = digests[idx] if digests is not None else \
            hashlib.sha256(text.encode("utf-8")).hexdigest()
        ck = (dg, keys_key)
        per = _FILE_COUNT_CACHE.get(ck)
        if per is None:
            per = matcher.counts(text) if matcher is not None \
                else {k: text.count(k) for k in keys}
            sparse = {k: n for k, n in per.items() if n}      # 稀疏：单件里绝大多数键一次都不出现
            if len(_FILE_COUNT_CACHE) >= _FILE_COUNT_CACHE_MAX:
                _FILE_COUNT_CACHE.clear()
            _FILE_COUNT_CACHE[ck] = sparse
            per = sparse
        for k, n in per.items():
            totals[k] += n
    return totals


def usage_scan(root: str = ".") -> Tuple[List[str], Dict[str, Any]]:
    """资产引用度体检：每个资产键在 04/community/docs 全语料中被引用次数。

    FAIL 面留空（纯统计）：zero_usage 为「注册了但全语料无引用」的键清单，
    供作者裁决（低信息键候选），不自动删。
    """
    keys: Dict[str, str] = {}
    for pat in ("community/*/assets/*.md", "05_资产库/用户自定义/*.md"):
        for rel in csc.iter_files(root, pat):
            if rel.rsplit("/", 1)[-1] == "README.md":
                continue
            for k in _keys_of(Path(rel)):
                keys.setdefault(k, rel)
    # 内容键：**语料面指纹**（常驻层逐件摘要，不读正文）＋ 键集。口径与旧实现一致（同一批件、
    # 同一 payload 语义），但不再把 3.5 MB 正文逐件 `encode()` + 重哈希——而且键能**先算**，
    # 于是命中时**根本不必把 2815 份语料读成列表**（旧实现是「先全读、再查表」）。
    h = hashlib.sha256()
    h.update(csc.content_fingerprint(root, CORPUS_PATTERNS).encode("utf-8"))
    h.update(b"\x00")
    for k in sorted(keys):
        h.update(k.encode("utf-8"))
        h.update(b"\x01")
    ckey = h.hexdigest()
    # 落盘键另叠**代码面 + 运行时**（见 core.disk_cache）：改了普查算法必然换键，
    # 不靠"记得手工 bump 版本标签"。
    dkey = disk_cache.key("census", ckey, root=root,
                               code_modules=("core.asset_density",))
    counts = _CENSUS_CACHE.get(ckey)
    if counts is None:
        counts = disk_cache.load("census", dkey,
                                 validate=lambda d: isinstance(d, dict)
                                 and set(d) == set(keys))
    if counts is None:
        # 语义 = 逐键 `str.count`（非重叠、含互相包含）——已实测：bytes 版更慢；单遍 alternation 在
        # 「两键于同一位置重叠」（如 AB/BC 于 ABC）时会漏计。现在走 `count_keys_additive`
        # （逐件 Aho–Corasick + 非重叠贪心，再相加；与「拼成一整条再数」逐键等价，见其 docstring），
        # 于是**逐件**结果能按文件内容缓存：真编辑只让被改的那一件重算。实测整条 3.11 s → ~0.2 s，
        # 且改一件之后再算只需那一件的钱。
        corpus: List[str] = []
        digests: List[str] = []
        for rel in (r for pat in CORPUS_PATTERNS for r in csc.iter_files(root, pat)):
            try:
                corpus.append(csc.read_text_cached(Path(root) / rel))
            except OSError:
                continue
            # 摘要已在常驻层（上面的语料面指纹刚把它们算齐）⇒ 这里只是取用，不再编码 + 重哈希
            digests.append(csc._payload_digest(root, rel).hex())
        counts = count_keys_additive(corpus, keys, digests=digests)
        disk_cache.store("census", dkey, counts)
    if ckey not in _CENSUS_CACHE:
        if len(_CENSUS_CACHE) >= _CENSUS_CACHE_MAX:
            _CENSUS_CACHE.clear()
        _CENSUS_CACHE[ckey] = counts
    zero = sorted(k for k, n in counts.items() if n == 0)
    stats = {"assets": len(keys), "zero_usage": len(zero),
             "used": len(keys) - len(zero),
             "total_refs": sum(counts.values()),
             "zero_keys": zero}
    return [], stats


def thickness_scan(root: str = ".") -> Tuple[List[str], Dict[str, Any]]:
    """资产语义厚度（计数升半语义）：每档 字符/键/小节/表格行 与 low 判定。

    low = 空/过短(<200字) 或 无键且无小节（低信息档候选）；只报告不删（issues 空）。
    派生结果按**输入内容指纹**缓存（输入面与 `scan()` 同：两条资产面）——纯函数，键即内容。
    """
    return csc.memo_pair("asset-thickness", ASSET_INPUTS, _thickness_impl, root,
                          code_modules=("core.asset_density",))


def _thickness_impl(root: str = ".") -> Tuple[List[str], Dict[str, Any]]:
    """真算（未命中缓存时走这里）。"""
    import re as _re

    rows = []
    for pat in ("community/*/assets/*.md", "05_资产库/用户自定义/*.md"):
        for rel in csc.iter_files(root, pat):
            if rel.rsplit("/", 1)[-1] == "README.md":
                continue
            try:
                text = csc.read_text_cached(Path(root) / rel)
            except OSError:
                continue
            if not text.strip():
                continue
            keys = _keys_of(Path(rel), text)
            lines = text.splitlines()
            sections = sum(1 for ln in lines if _re.match(r"^#{1,3}\s", ln))
            tables = sum(1 for ln in lines if ln.lstrip().startswith("|"))
            low = len(text) < 200 or (not keys and sections == 0)
            pkg = rel.split("/")[1] if rel.startswith("community") else "官方"
            rows.append({"package": pkg, "file": rel, "chars": len(text),
                         "keys": len(keys), "sections": sections,
                         "tables": tables, "low_info": low})
    low_files = sorted(x["file"] for x in rows if x["low_info"])
    stats = {"files": len(rows),
             "low_info": len(low_files), "low_files": low_files,
             "avg_chars": round(sum(x["chars"] for x in rows) / max(1, len(rows))),
             "avg_sections": round(sum(x["sections"] for x in rows) / max(1, len(rows)))}
    return [], stats
