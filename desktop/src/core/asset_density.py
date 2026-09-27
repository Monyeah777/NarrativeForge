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


#: 引用度普查的内容键缓存：键 = **语料与键集的 sha256**（见 `usage_scan`）。
#: 必要性（实测）：一次普查 = 1499 个键 × 3.5 MB 语料的逐键子串计数 ≈ **2.7 s**；而
#: 「跑全量评分」的路径（`nf score`、回归单测、发布体检 + 覆盖率通道）会在同一进程里
#: 反复走到这里。键取内容哈希（不是路径）→ 内容没变必然同结果，内容一改键就变，
#: 因此不存在「改了文件还读到旧值」的陈旧风险。
_CENSUS_CACHE: Dict[str, Dict[str, int]] = {}
_CENSUS_CACHE_MAX = 64


def _keys_of(path: Path, text: Optional[str] = None) -> List[str]:
    """文件名令牌 ∪ 正文键声明（`text` 可由调用方传入——避免同一份件被读两遍）。"""
    keys = set(re.findall(r"[A-Z][A-Z0-9_]*", path.stem))
    if text is None:
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            return sorted(keys)
    head = text[:6000]
    # 条目键面（2026-09-23 对齐）：除大写下划线键外，仓库里还大量使用**带连字符的条目键**
    # （如域包的 `C01-01` / `A08-07` —— 经 asset_get('<资产键>','<条目键>') 真实可寻址）。
    # 原字符集 `[A-Z0-9_]` 看不见它们 → 密度被系统性低估（AI 品类域包扩面后实测暴露）。
    keys.update(re.findall(r"`([A-Z][A-Z0-9_-]{2,})`", head))
    keys.update(re.findall(r"\"([A-Z][A-Z0-9_-]{2,})\"\s*:", head))
    keys.update(re.findall(r"##\s*([A-Z][A-Z0-9_-]{2,})", head))
    return sorted(keys)


def scan(root: str = ".") -> Tuple[List[str], Dict[str, Any]]:
    r = Path(root)
    issues: List[str] = []
    rows = []
    patterns = ["community/*/assets/*.md", "05_资产库/用户自定义/*.md"]
    for pat in patterns:
        for p in sorted(r.glob(pat)):
            if p.name == "README.md":
                continue
            try:
                text = p.read_text(encoding="utf-8")
            except OSError as exc:
                issues.append("%s 不可读：%s" % (p, exc))
                continue
            if not text.strip():
                issues.append("%s 为空档（0 字符）" % p)
                continue
            keys = _keys_of(p, text)
            rel = p.relative_to(r).as_posix()
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


def usage_scan(root: str = ".") -> Tuple[List[str], Dict[str, Any]]:
    """资产引用度体检：每个资产键在 04/community/docs 全语料中被引用次数。

    FAIL 面留空（纯统计）：zero_usage 为「注册了但全语料无引用」的键清单，
    供作者裁决（低信息键候选），不自动删。
    """
    r = Path(root)
    keys: Dict[str, str] = {}
    for pat in ("community/*/assets/*.md", "05_资产库/用户自定义/*.md"):
        for p in r.glob(pat):
            if p.name == "README.md":
                continue
            for k in _keys_of(p):
                keys.setdefault(k, p.relative_to(r).as_posix())
    corpus: List[str] = []
    for base in ("04_模块库", "community", "docs"):
        for p in (r / base).rglob("*.md"):
            try:
                corpus.append(p.read_text(encoding="utf-8"))
            except OSError:
                continue
    # 内容键：语料（逐件 + 分隔符，防止跨件拼接歧义）与键集一起哈希。
    h = hashlib.sha256()
    for text in corpus:
        h.update(text.encode("utf-8"))
        h.update(b"\x00")
    for k in sorted(keys):
        h.update(k.encode("utf-8"))
        h.update(b"\x01")
    ckey = h.hexdigest()
    counts = _CENSUS_CACHE.get(ckey)
    if counts is None:
        # 逐键 `str.count` 是**精确**语义（非重叠、含互相包含）——已实测：bytes 版更慢；
        # 单遍 alternation 在「两键于同一位置重叠」（如 AB/BC 于 ABC）时会漏计，故不走。
        blob = "\n".join(corpus)
        counts = {k: blob.count(k) for k in keys}
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
    """
    r = Path(root)
    import re as _re

    rows = []
    for pat in ("community/*/assets/*.md", "05_资产库/用户自定义/*.md"):
        for p in sorted(r.glob(pat)):
            if p.name == "README.md":
                continue
            try:
                text = p.read_text(encoding="utf-8")
            except OSError:
                continue
            if not text.strip():
                continue
            keys = _keys_of(p, text)
            lines = text.splitlines()
            sections = sum(1 for ln in lines if _re.match(r"^#{1,3}\s", ln))
            tables = sum(1 for ln in lines if ln.lstrip().startswith("|"))
            low = len(text) < 200 or (not keys and sections == 0)
            rel = p.relative_to(r).as_posix()
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
