"""接力协议门禁（SBAR：情境 → 背景 → 评估 → 建议 + 未决项）。

真源：`protocol/handover.json`（声明）+ `handovers/HO-*.md`（交接件）。

判据（全部可证，零第三方依赖）：
- 声明：schema；`sections` 必须恰好五段；`rules` 非空；`required_fields` / `status_vocabulary` 在册；
- 交接件：frontmatter 必填齐；`status` 在词表；`date` 为 YYYY-MM-DD；五段齐；
  **`## 未决项` 非空**（空未决 = 不合格交接）；**每条未决必须带判据**（出现「判据」字样）；
  `refs` 每条须解析到仓库真实件或 `checkN`（与 decisions 的 evidence 同语义，不重写第二套解析）。
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

from core.library import parse_frontmatter

DECL_REL = "protocol/handover.json"
GLOB = "handovers/HO-*.md"
SCHEMA = "nf-handover/1"
SECTIONS = ("## 情境", "## 背景", "## 评估", "## 建议", "## 未决项")
_CHECK = re.compile(r"^check(\d+)$")
_ADR = re.compile(r"^ADR-\d{4}$")
_DATED = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_BULLET = re.compile(r"^\s*[-*]\s+(.+)$", re.M)


def _bullet_blocks(text: str) -> List[str]:
    """列表按「bullet 块」切分（含缩进续行）——换行续写也算同一条未决项。"""
    blocks: List[str] = []
    cur: List[str] = []
    for line in text.splitlines():
        if re.match(r"^\s*[-*]\s+", line):
            if cur:
                blocks.append("\n".join(cur).strip())
            cur = [line]
        elif cur and line.strip():
            cur.append(line)
        elif cur:
            blocks.append("\n".join(cur).strip())
            cur = []
    if cur:
        blocks.append("\n".join(cur).strip())
    return blocks


def decl(root: str = ".") -> Dict[str, Any]:
    import json
    p = Path(root) / DECL_REL
    return json.loads(p.read_text(encoding="utf-8")) if p.is_file() else {}


def entries(root: str = ".") -> List[Dict[str, Any]]:
    r = Path(root)
    out = []
    for p in sorted(r.glob(GLOB)):
        fm, body = parse_frontmatter(p.read_text(encoding="utf-8"))
        out.append({"path": p.relative_to(r).as_posix(), "file": p.name,
                    "fm": fm or {}, "body": body or ""})
    return out


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
    for k in (d.get("required_fields") or ["id", "date", "from", "to", "status", "refs"]):
        if not fm.get(k):
            issues.append("缺必填字段：%s" % k)
    if str(fm.get("status")) not in (d.get("status_vocabulary") or ["open", "closed"]):
        issues.append("status 越词表：%s" % fm.get("status"))
    if not _DATED.match(str(fm.get("date") or "")):
        issues.append("date 非 YYYY-MM-DD：%s" % fm.get("date"))
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
    r = Path(root)
    verify = (r / "verify.sh").read_text(encoding="utf-8") if (r / "verify.sh").is_file() else ""
    checks = set(re.findall(r"^check(\d+)\(\)\{", verify, re.M))
    refs = fm.get("refs") or []
    if isinstance(refs, str):
        refs = [refs]
    for ref in refs:
        s = str(ref).strip()
        if s.startswith("[") and s.endswith("]"):
            s = s.strip("[]").strip()
        c = _CHECK.match(s)
        if c:
            if c.group(1) not in checks:
                issues.append("refs 指向不存在的 check：%s" % s)
            continue
        if _ADR.match(s):
            continue
        if not (r / s.replace("\\", "/")).exists():
            issues.append("refs 无法解析：%s" % s)
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
