"""内容绑定批准记录（机制借鉴 MCOP 的 approved-changeset gate）。

NF 现状：所有「作者裁决」只存在于散文（代码注释与文档里）。本模块把「有人批准了」
变成**内容绑定、可重放**的记录：

- 记录 = {schema, subject, subject_digest, approved_by, approved_at, note}；
- 被批准对象一改，`subject_digest` 立刻不符 → **失效**（approved 不是永久通行证）；
- 缺批准人 / 摘要不符 / 指向不存在的对象 → FAIL。

纪律：纯标准库；记录入库（protocol/approvals/*.json）可 diff 可审计。
"""
from __future__ import annotations

import hashlib
import json
import os
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Tuple

SCHEMA = "nf-approval/1"
DIR_REL = "protocol/approvals"


def subject_digest(root: str, subject: str) -> str:
    """被批准对象的整文件摘要（不含批准记录本身——记录是独立文件，无自指问题）。"""
    p = Path(root) / subject
    return hashlib.sha256(p.read_bytes()).hexdigest()


def approve(root: str, subject: str, approved_by: str, note: str = "",
            today: str = "") -> str:
    """写一条批准记录 → 相对路径。"""
    if not approved_by.strip():
        raise ValueError("批准人不能为空（修复指引：--by <批准人标识>）")
    p = Path(root) / subject
    if not p.is_file():
        raise ValueError("被批准对象不存在：%s（修复指引：给出仓库内真实文件路径）" % subject)
    rec = {"schema": SCHEMA, "subject": subject.replace("\\", "/"),
           "subject_digest": subject_digest(root, subject),
           "approved_by": approved_by.strip(),
           "approved_at": today or date.today().isoformat(),
           "note": note}
    safe = subject.replace("/", "__").replace("\\", "__")
    dest = Path(root) / DIR_REL / ("%s.json" % safe)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(rec, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8", newline="\n")
    return dest.relative_to(Path(root)).as_posix()


def records(root: str = ".") -> List[Dict[str, Any]]:
    d = Path(root) / DIR_REL
    if not d.is_dir():
        return []
    out = []
    for p in sorted(d.glob("*.json")):
        try:
            out.append(json.loads(p.read_text(encoding="utf-8")))
        except ValueError:
            out.append({"schema": "?", "subject": p.name, "broken": True})
    return out


def verify(root: str = ".") -> Tuple[List[str], Dict[str, Any]]:
    """校验全部批准记录 → (issues, stats)。改动即失效、缺批准人即 FAIL。"""
    issues: List[str] = []
    rows = records(root)
    stale = []
    for rec in rows:
        subj = str(rec.get("subject") or "")
        if rec.get("schema") != SCHEMA:
            issues.append("批准记录 schema 不匹配：%s" % subj)
            continue
        if not str(rec.get("approved_by") or "").strip():
            issues.append("批准记录缺批准人：%s" % subj)
        if not os.path.isfile(os.path.join(root, subj)):
            issues.append("批准对象不存在：%s" % subj)
            continue
        if subject_digest(root, subj) != str(rec.get("subject_digest") or ""):
            stale.append(subj)
            issues.append("批准已失效（对象内容已改）：%s（修复指引：重新批准）" % subj)
    stats = {"records": len(rows), "stale": stale,
             "subjects": sorted({str(r.get("subject")) for r in rows})}
    return issues, stats


def list_records(root: str = ".") -> List[Dict[str, Any]]:
    """列批准记录 + 失效标记（供 `nf approve --list`；只读）。"""
    out = []
    for rec in records(root):
        subj = str(rec.get("subject") or "")
        stale = True
        if rec.get("schema") == SCHEMA and os.path.isfile(os.path.join(root, subj)):
            stale = subject_digest(root, subj) != str(rec.get("subject_digest") or "")
        out.append({"subject": subj, "approved_by": rec.get("approved_by", ""),
                    "approved_at": rec.get("approved_at", ""),
                    "note": rec.get("note", ""), "stale": stale})
    return out
