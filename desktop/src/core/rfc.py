"""协议件 RFC 头 + supersede 链（机制借鉴 HMP 的 RFC 系列）。

NF 原有 01–07 编号与 §7 迁移记录，但**协议件自身没有版本史头**——「这份协议是哪一版、
什么状态、被谁取代」全靠翻文档。本模块把版本史做成**可机读头**：

```
> **RFC**: NF-0001 · **Category**: Standards Track · **Date**: 2026-09-08 ·
  **Status**: Active · **Supersedes**: — · **Superseded by**: —
```

判据（全部可证）：
- 每个在册协议件**必须**带 RFC 头，且六字段齐（RFC/Category/Date/Status/Supersedes/Superseded by）；
- `RFC` 编号在册唯一；`Category`/`Status` ∈ 词表；
- `Date` 必须等于该文档的「最后更新」（避免两份日期各说各话）；
- `Status: Superseded` 必须给 `Superseded by`；`Superseded by` 指向的编号必须在册（链可解析）；
- `Superseded by` 链不得成环。
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

INDEX_REL = "protocol/rfc_index.json"
CATEGORIES = ("Standards Track", "Informational", "Experimental", "Process")
_HEAD = re.compile(
    r"\*\*RFC\*\*:\s*(?P<rfc>NF-\d{4})\s*·\s*\*\*Category\*\*:\s*(?P<cat>[^·]+?)\s*·\s*"
    r"\*\*Date\*\*:\s*(?P<date>[\d-]+)\s*·\s*\*\*Status\*\*:\s*(?P<status>[^·]+?)\s*·\s*"
    r"\*\*Supersedes\*\*:\s*(?P<sup>[^·]+?)\s*·\s*\*\*Superseded by\*\*:\s*(?P<supby>[^·\n]+)")
_LAST_UPDATED = re.compile(r">\s*最后更新：\s*([\d-]+)")


def index(root: str = ".") -> Dict[str, Any]:
    p = Path(root) / INDEX_REL
    return json.loads(p.read_text(encoding="utf-8")) if p.is_file() else {}


def parse_head(text: str) -> Dict[str, str]:
    """取文档头 8 行内的 RFC 头（缺则返回空 dict）。"""
    head = "\n".join(text.splitlines()[:8])
    m = _HEAD.search(head)
    if not m:
        return {}
    out = {k: v.strip() for k, v in m.groupdict().items()}
    updated = _LAST_UPDATED.search(head)
    out["last_updated"] = updated.group(1) if updated else ""
    return out


def scan(root: str = ".") -> Tuple[List[str], List[str], Dict[str, Any]]:
    """→ (issues, warns, stats)。"""
    issues: List[str] = []
    warns: List[str] = []
    idx = index(root)
    if not idx:
        return ["缺 RFC 索引 %s（修复指引：见 protocol/rfc_index.json）" % INDEX_REL], [], {}
    vocab = tuple(idx.get("status_vocabulary") or ("Active",))
    seen: Dict[str, str] = {}
    supby: Dict[str, str] = {}
    for item in idx.get("docs") or []:
        rel, rfc = str(item.get("path") or ""), str(item.get("rfc") or "")
        p = Path(root) / rel
        if not p.is_file():
            issues.append("RFC 索引指向不存在的文档：%s" % rel)
            continue
        if rfc in seen:
            issues.append("RFC 编号重复：%s（%s 与 %s）" % (rfc, seen[rfc], rel))
        seen[rfc] = rel
        head = parse_head(p.read_text(encoding="utf-8"))
        if not head:
            issues.append("%s 缺 RFC 头（修复指引：见 docs 或 core/rfc.py 头格式）" % rel)
            continue
        if head["rfc"] != rfc:
            issues.append("%s 头部 RFC 与索引不一致：头=%s 索引=%s" % (rel, head["rfc"], rfc))
        if head["cat"] not in CATEGORIES:
            issues.append("%s Category 越词表：%s（%s）" % (rel, head["cat"], "/".join(CATEGORIES)))
        if head["status"] not in vocab:
            issues.append("%s Status 越词表：%s（%s）" % (rel, head["status"], "/".join(vocab)))
        if head["last_updated"] and head["date"] != head["last_updated"]:
            issues.append("%s Date 与「最后更新」不一致：RFC=%s 最后更新=%s"
                          % (rel, head["date"], head["last_updated"]))
        if str(item.get("category") or "") and str(item["category"]) != head["cat"]:
            issues.append("%s Category 索引与头部不一致：索引=%s 头=%s"
                          % (rel, item["category"], head["cat"]))
        if head["status"] == "Superseded" and head["supby"] in ("—", "-", ""):
            issues.append("%s 标记 Superseded 但缺 Superseded by" % rel)
        if head["supby"] not in ("—", "-", ""):
            supby[rfc] = head["supby"]
    for rfc, target in supby.items():
        if target not in seen:
            issues.append("%s 的 Superseded by 指向不在册的编号：%s" % (rfc, target))
            continue
        # 环检测
        cur, hops = target, 0
        while cur in supby and hops < len(supby) + 1:
            cur = supby[cur]
            hops += 1
            if cur == rfc:
                issues.append("supersede 链成环：%s → … → %s" % (rfc, rfc))
                break
    stats = {"docs": len(seen), "chains": len(supby),
             "statuses": sorted({parse_head((Path(root) / r).read_text(encoding="utf-8")).get("status", "")
                                 for r in seen.values()})}
    return issues, warns, stats
