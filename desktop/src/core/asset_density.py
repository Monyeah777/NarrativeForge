"""45 W2 · 资产键语义密度体检（资产质量维机检）。

对 community 各包 assets 与 05 用户自定义资产文件做密度体检：
- 键发现 = 文件名令牌 ∪ 正文键声明（`KEY` / "KEY": / ## KEY，与 AI 通道资源面同口径）；
- 统计每文件 键数/字符数，标出「无键文件」（多为附机制/中文名件，合法——入 unkeyed 计数不 FAIL）；
- FAIL 面只留：文件空或不可读（真异常）。
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from core import conformance_scan as csc


#: 引用度普查的内容键缓存：键 = **语料与键集的 sha256**（见 `usage_scan`）。
#: 必要性（实测）：一次普查 = 1499 个键 × 3.5 MB 语料的逐键子串计数 ≈ **2.7 s**；而
#: 「跑全量评分」的路径（`nf score`、回归单测、发布体检 + 覆盖率通道）会在同一进程里
#: 反复走到这里。键取内容哈希（不是路径）→ 内容没变必然同结果，内容一改键就变，
#: 因此不存在「改了文件还读到旧值」的陈旧风险。
_CENSUS_CACHE: Dict[str, Dict[str, int]] = {}
_CENSUS_CACHE_MAX = 64

#: 引用度普查的**磁盘**缓存：内容寻址（键 = 语料+键集的 sha256）+ **口径版本**标签。
#: 必要性（实测）：一次普查 = 1499 键 × 3.5 MB 语料的逐键子串计数 = **3.02 s**，占冷进程
#: `evaluate` 6.3 s 的近一半；而它是**内容的纯函数**——不起守护的默认路径每开一个新进程就要重付。
#: 落点在 `NF_HOME`（**不在仓库内**，故不影响仓库纯净与门禁）：`<NF_HOME>/cache/census/<tag>-<key>.json`。
#: 纪律：① 键即内容 ⇒ 内容一变键就变，不存在陈旧；② **口径一变必须 bump `_DISK_CACHE_TAG`**
#: （标签进文件名，旧条目自然不再命中，不会拿旧算法的账当新账）；③ 一切 IO **尽力而为**，
#: 失败一律静默回落重算；④ 环境变量 `NF_NO_DISK_CACHE=1` 可整体关闭；⑤ 只保留最近 N 份。
_DISK_CACHE_TAG = "census-v1"
_DISK_CACHE_KEEP = 16
_DISK_CACHE_ENV = "NF_NO_DISK_CACHE"


def _disk_cache_dir() -> Path:
    from core import storage
    return storage.default_home() / "cache" / "census"


def _disk_cache_enabled() -> bool:
    return not os.environ.get(_DISK_CACHE_ENV)


def _disk_load(ckey: str, keys) -> Optional[Dict[str, int]]:
    """读盘上的普查条目；**任何不可信**（缺件 / 解析失败 / 键集不符 / 关闭）一律返回 None。"""
    if not _disk_cache_enabled():
        return None
    try:
        p = _disk_cache_dir() / ("%s-%s.json" % (_DISK_CACHE_TAG, ckey))
        data = json.loads(p.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or set(data) != set(keys):
            return None                     # 半截文件 / 键集不符：宁可重算，不可错答
        return {str(k): int(v) for k, v in data.items()}
    except Exception:                       # noqa: BLE001 - 读不到就重算
        return None


def _disk_store(ckey: str, counts: Dict[str, int]) -> None:
    """写盘（尽力而为）：失败不影响命令；写后裁剪到最近 `_DISK_CACHE_KEEP` 份。"""
    if not _disk_cache_enabled():
        return
    try:
        d = _disk_cache_dir()
        d.mkdir(parents=True, exist_ok=True)
        p = d / ("%s-%s.json" % (_DISK_CACHE_TAG, ckey))
        tmp = p.with_name(p.name + ".tmp")
        with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(counts, sort_keys=True))
        os.replace(tmp, p)                  # 原子替换：读者看不到半截 JSON
        _disk_prune(d)
    except Exception:                       # noqa: BLE001 - 写不进就算了
        return


def _disk_prune(d: Path) -> None:
    """只留最近 N 份（按 mtime）：缓存不得无界增长。"""
    try:
        entries = sorted(d.glob("%s-*.json" % _DISK_CACHE_TAG),
                         key=lambda q: q.stat().st_mtime, reverse=True)
        for old in entries[_DISK_CACHE_KEEP:]:
            old.unlink()
    except Exception:                       # noqa: BLE001 - 裁剪失败不影响结果
        return


def _keys_of(path: Path, text: Optional[str] = None) -> List[str]:
    """文件名令牌 ∪ 正文键声明（`text` 可由调用方传入——避免同一份件被读两遍）。"""
    keys = set(re.findall(r"[A-Z][A-Z0-9_]*", path.stem))
    if text is None:
        try:
            text = csc.read_text_cached(path)
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
    corpus: List[str] = []
    # `(r/base).rglob("*.md")` ≡ `Path.glob(base + "/**/*.md")`：改走共享枚举器后，
    # 已在作用域里建过的子树清单直接复用（community 这棵树不再被第三次走）。
    for base in ("04_模块库", "community", "docs"):
        for rel in csc.iter_files(root, base + "/**/*.md"):
            try:
                corpus.append(csc.read_text_cached(Path(root) / rel))
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
        counts = _disk_load(ckey, keys)     # 内容寻址的持久缓存：新进程免付那 3 s（见模块头注释）
    if counts is None:
        # 逐键 `str.count` 是**精确**语义（非重叠、含互相包含）——已实测：bytes 版更慢；
        # 单遍 alternation 在「两键于同一位置重叠」（如 AB/BC 于 ABC）时会漏计，故不走。
        blob = "\n".join(corpus)
        counts = {k: blob.count(k) for k in keys}
        _disk_store(ckey, counts)
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
    """
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
