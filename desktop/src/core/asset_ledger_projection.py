"""45 · 资产键表机读 ledger 投影（#2：键 → 文件 → 行映射，键条目级寻址）。

community 各包 assets/README.md 键表原为人读；本模块把「键发现」投影成机读 ledger：
- 键源 = 资产文件名令牌 ∪ 正文键声明（`KEY` / "KEY": / ## KEY，与 AI 通道同口径）；
- 每键记 {package, file, first_line}（first_line = 键在正文首次出现行，找不到 = 文件名行 1）；
- protocol/community_asset_ledger.json 为常驻投影（verify 双源一致，refresh 刷新）。
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

_ROOT = Path(__file__).resolve().parents[3]
_LEDGER = "protocol/community_asset_ledger.json"


def _file_keys(path: Path) -> List[str]:
    keys = set(re.findall(r"[A-Z][A-Z0-9_]*", path.stem))
    try:
        head = path.read_text(encoding="utf-8")[:8000]
    except OSError:
        return sorted(keys)
    keys.update(re.findall(r"`([A-Z][A-Z0-9_]{2,})`", head))
    keys.update(re.findall(r"\"([A-Z][A-Z0-9_]{2,})\"\s*:", head))
    keys.update(re.findall(r"^##\s*([A-Z][A-Z0-9_]{2,})", head, re.M))
    return sorted(keys)


def build(root: str = ".") -> List[Dict[str, Any]]:
    r = Path(root)
    rows: List[Dict[str, Any]] = []
    for pat in ("community/*/assets/*.md", "05_资产库/用户自定义/*.md"):
        for p in sorted(r.glob(pat)):
            if p.name == "README.md":
                continue
            rel = p.relative_to(r).as_posix()
            pkg = rel.split("/")[1] if rel.startswith("community") else "官方"
            text = p.read_text(encoding="utf-8")
            lines = text.splitlines()
            for k in _file_keys(p):
                line = 1
                for idx, ln in enumerate(lines, 1):
                    if re.search(r"\b" + re.escape(k) + r"\b", ln):
                        line = idx
                        break
                rows.append({"key": k, "package": pkg, "file": rel, "line": line})
    rows.sort(key=lambda x: (x["package"], x["key"], x["file"]))
    return rows


def refresh(root: str = ".") -> Tuple[List[str], Dict[str, Any]]:
    r = Path(root)
    rows = build(str(r))
    data = {"schema": "community-asset-ledger/1", "entries": rows}
    (r / _LEDGER).write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8", newline="\n")
    return [], {"entries": len(rows)}


def verify(root: str = ".") -> Tuple[List[str], Dict[str, Any]]:
    r = Path(root)
    issues: List[str] = []
    path = r / _LEDGER
    if not path.exists():
        return ["%s 缺失（refresh 生成）" % _LEDGER], {}
    data = json.loads(path.read_text(encoding="utf-8"))
    current = build(str(r))
    if data.get("entries") != current:
        issues.append("%s 过期：与资产扫描不一致（refresh）" % _LEDGER)
    return issues, {"entries": len(current)}
