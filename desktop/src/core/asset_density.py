"""45 W2 · 资产键语义密度体检（资产质量维机检）。

对 community 各包 assets 与 05 用户自定义资产文件做密度体检：
- 键发现 = 文件名令牌 ∪ 正文键声明（`KEY` / "KEY": / ## KEY，与 AI 通道资源面同口径）；
- 统计每文件 键数/字符数，标出「无键文件」（多为附机制/中文名件，合法——入 unkeyed 计数不 FAIL）；
- FAIL 面只留：文件空或不可读（真异常）。
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Tuple


def _keys_of(path: Path) -> List[str]:
    keys = set(re.findall(r"[A-Z][A-Z0-9_]*", path.stem))
    try:
        head = path.read_text(encoding="utf-8")[:6000]
    except OSError:
        return sorted(keys)
    keys.update(re.findall(r"`([A-Z][A-Z0-9_]{2,})`", head))
    keys.update(re.findall(r"\"([A-Z][A-Z0-9_]{2,})\"\s*:", head))
    keys.update(re.findall(r"##\s*([A-Z][A-Z0-9_]{2,})", head))
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
            keys = _keys_of(p)
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
