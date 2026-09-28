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

from core import conformance_scan as csc   # 共享语料：一次只读调用内同文只读一遍

_ROOT = Path(__file__).resolve().parents[3]
_LEDGER = "protocol/community_asset_ledger.json"


def _file_keys(path: Path, text: str = None) -> List[str]:
    """键发现（`text` 可由调用方传入——避免同一份件被读两遍）。"""
    keys = set(re.findall(r"[A-Z][A-Z0-9_]*", path.stem))
    if text is not None:
        head = text[:8000]
    else:
        try:
            head = csc.read_text_cached(path)[:8000]
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
            text = csc.read_text_cached(p)
            lines = text.splitlines()
            for k in _file_keys(p, text):
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


#: `verify()` 的全部输入：两条资产面（`build()` 枚举的）+ 台账件本身。
VERIFY_INPUTS = ("community/*/assets/*.md", "05_资产库/用户自定义/*.md", _LEDGER)


def verify(root: str = ".") -> Tuple[List[str], Dict[str, Any]]:
    """台账 ↔ 盘上实况一致（原体见 `_verify_impl`）；派生结果按**输入内容指纹**缓存。

    输入面窄（两条资产面 + 台账件），但冷进程里读它们也要 ~100 ms，与算一遍同量级，故
    `require_resident=True`：只在常驻语料层在位时才走缓存（那时见证成本几乎为零）。
    """
    return csc.memo_pair("asset-ledger-verify", VERIFY_INPUTS, _verify_impl, root,
                         require_resident=True)


def _verify_impl(root: str = ".") -> Tuple[List[str], Dict[str, Any]]:
    """真算（未命中缓存时走这里）。"""
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
