"""接力协议门禁（SBAR：情境 → 背景 → 评估 → 建议 + 未决项）。

真源：`protocol/handover.json`（声明）+ `handovers/HO-*.md`（交接件）。

判据（全部可证，零第三方依赖）：
- 声明：schema；`sections` 必须恰好五段；`rules` 非空；`required_fields` / `status_vocabulary` 在册；
- 交接件：frontmatter 必填齐；`status` 在词表；`date` 为 YYYY-MM-DD；五段齐；
  **`## 未决项` 非空**（空未决 = 不合格交接）；**每条未决必须带判据**（出现「判据」字样）；
  `refs` 每条须解析到仓库真实件或 `checkN`（与 decisions 的 evidence 同语义，不重写第二套解析）。
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Tuple

from core import doc_family
from core.library import parse_frontmatter

DECL_REL = "protocol/handover.json"
GLOB = "handovers/HO-*.md"
SCHEMA = "nf-handover/1"
SECTIONS = ("## 情境", "## 背景", "## 评估", "## 建议", "## 未决项")


#: 列表块解析的**唯一出处**（与 postmortem 曾逐字重复的两份拷贝，2026-10-01 收口）
from core.md_blocks import bullet_blocks as _bullet_blocks


def decl(root: str = ".") -> Dict[str, Any]:
    return doc_family.load_decl(root, DECL_REL)


def entries(root: str = ".") -> List[Dict[str, Any]]:
    return doc_family.entries(root, GLOB)


def check_doc(root: str, rel: str) -> Tuple[List[str], Dict[str, Any]]:
    """单件机检 → (issues, stats)。"""
    p = Path(root) / rel
    if not p.is_file():
        return ["交接件不存在：%s" % rel], {}
    fm, body = parse_frontmatter(p.read_text(encoding="utf-8"))
    fm = fm or {}
    body = body or ""
    issues: List[str] = []
    d = decl(root)
    issues += doc_family.frontmatter_issues(
        fm, d, required=("id", "date", "from", "to", "status", "refs"),
        vocab_key="status_vocabulary", field="status",
        default_vocab=("open", "closed"))
    for sec in SECTIONS:
        if sec not in body:
            issues.append("正文缺段落：%s" % sec)
    pending = body.split("## 未决项", 1)[1] if "## 未决项" in body else ""
    items = _bullet_blocks(pending)
    if not items:
        issues.append("未决项为空——空未决 = 不合格交接（没有未决就是没交接）")
    for it in items:
        if "判据" not in it:
            issues.append("未决项缺判据（怎样算完成）：%s" % it[:40])
    issues += doc_family.refs_issues(root, fm.get("refs"), doc_family.check_numbers(root),
                                     label="refs", allow_adr=True, strip_brackets=True)
    return issues, {"pending": len(items), "sections": sum(1 for s in SECTIONS if s in body)}


def scan(root: str = ".") -> Tuple[List[str], List[str], Dict[str, Any]]:
    """声明 + 全部交接件 → (issues, warns, stats)。"""
    issues: List[str] = []
    warns: List[str] = []
    d = decl(root)
    if not d:
        return ["缺交接协议声明 %s" % DECL_REL], warns, {}
    if str(d.get("schema") or "") != SCHEMA:
        issues.append("交接协议 schema 不匹配（期望 %s）" % SCHEMA)
    if tuple(d.get("sections") or ()) != ("情境", "背景", "评估", "建议", "未决项"):
        issues.append("sections 必须是五段（情境/背景/评估/建议/未决项）")
    if not (d.get("rules") or []):
        issues.append("rules 不得为空（交接纪律必须成文）")
    rows = entries(root)
    pending_total = 0
    for e in rows:
        i, st = check_doc(root, e["path"])
        issues += ["%s：%s" % (e["fm"].get("id") or e["file"], x) for x in i]
        pending_total += st.get("pending", 0)
    if not rows:
        warns.append("暂无交接件（%s）——门禁空转" % GLOB)
    stats = {"handovers": len(rows), "pending": pending_total}
    return issues, warns, stats
