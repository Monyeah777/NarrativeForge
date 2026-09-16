"""复盘门禁（SRE postmortem：无指责 + 根因指向机制 + 行动项可指派可验）。

真源：`protocol/postmortem.json`（声明）+ `postmortems/PO-*.md`（复盘件）。

判据（全部可证，零第三方依赖）：
- 声明：schema；四段；blame_tokens / root_cause_tokens 非空；status 词表；
- 复盘件：frontmatter 必填齐、status 在词表、date 格式、四段齐；
  `trigger` 与 `refs` 必须解析到真实件或 `checkN`；
  **禁指责**：blame_tokens 命中即 FAIL；**根因指向机制**：根因段须含 root_cause_tokens；
  **行动项可指派可验**：每条行动项必须同时含「负责人」与「判据」；
  **未复盘不得关闭**：`status: closed` 必须已被协议回执锚定。
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

from core.library import parse_frontmatter

DECL_REL = "protocol/postmortem.json"
RECEIPTS_REL = "protocol/RECEIPTS.json"
GLOB = "postmortems/PO-*.md"
SCHEMA = "nf-postmortem/1"
SECTIONS = ("## 现象", "## 影响", "## 根因", "## 行动项")
_CHECK = re.compile(r"^check(\d+)$")
_DATED = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_BULLET = re.compile(r"^\s*[-*]\s+(.+)$", re.M)


def _bullet_blocks(text: str) -> List[str]:
    """把列表按「bullet 块」切分：一条 bullet 含其后续缩进续行（换行续写算同一条）。"""
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


def _refs_ok(root: str, refs: Any, checks: set) -> List[str]:
    issues: List[str] = []
    if isinstance(refs, str):
        refs = [refs]
    for ref in (refs or []):
        s = str(ref).strip()
        c = _CHECK.match(s)
        if c:
            if c.group(1) not in checks:
                issues.append("引用指向不存在的 check：%s" % s)
            continue
        if not (Path(root) / s.replace("\\", "/")).exists():
            issues.append("引用无法解析：%s" % s)
    return issues


def check_doc(root: str, rel: str) -> Tuple[List[str], Dict[str, Any]]:
    """单件机检 → (issues, stats)。"""
    p = Path(root) / rel
    if not p.is_file():
        return ["复盘件不存在：%s" % rel], {}
    d = decl(root)
    fm, body = parse_frontmatter(p.read_text(encoding="utf-8"))
    fm, body = fm or {}, body or ""
    issues: List[str] = []
    for k in (d.get("required_fields") or ["id", "date", "trigger", "status", "refs"]):
        if not fm.get(k):
            issues.append("缺必填字段：%s" % k)
    if str(fm.get("status")) not in (d.get("status_vocabulary") or ["open", "closed"]):
        issues.append("status 越词表：%s" % fm.get("status"))
    if not _DATED.match(str(fm.get("date") or "")):
        issues.append("date 非 YYYY-MM-DD：%s" % fm.get("date"))
    for sec in SECTIONS:
        if sec not in body:
            issues.append("正文缺段落：%s" % sec)
    for tok in (d.get("blame_tokens") or []):
        if tok and tok in body:
            issues.append("命中指责性归因词「%s」——复盘对事不对人" % tok)
    root_sec = body.split("## 根因", 1)[1].split("## 行动项", 1)[0] if "## 根因" in body else ""
    toks = d.get("root_cause_tokens") or []
    if root_sec and toks and not any(t in root_sec for t in toks):
        issues.append("根因段未指向机制（须出现 %s 之一）" % "/".join(toks[:4]))
    acts = _bullet_blocks(body.split("## 行动项", 1)[1]) if "## 行动项" in body else []
    if not acts:
        issues.append("行动项为空——没有行动项的复盘不闭环")
    for a in acts:
        if "负责人" not in a:
            issues.append("行动项缺负责人：%s" % a[:40])
        if "判据" not in a:
            issues.append("行动项缺判据：%s" % a[:40])
    r = Path(root)
    verify = (r / "verify.sh").read_text(encoding="utf-8") if (r / "verify.sh").is_file() else ""
    checks = set(re.findall(r"^check(\d+)\(\)\{", verify, re.M))
    for key in ("trigger",):
        v = fm.get(key)
        issues += _refs_ok(root, v, checks)
    issues += _refs_ok(root, fm.get("refs"), checks)
    if str(fm.get("status")) == "closed" and (r / RECEIPTS_REL).is_file():
        doc = json.loads((r / RECEIPTS_REL).read_text(encoding="utf-8"))
        ids = {e.get("id") for e in (doc.get("entries") or [])}
        if rel not in ids:
            issues.append("status=closed 但未被协议回执锚定（防事后美化；修复指引：nf receipts --write）")
    stats = {"actions": len(acts), "sections": sum(1 for s in SECTIONS if s in body)}
    return issues, stats


def scan(root: str = ".") -> Tuple[List[str], List[str], Dict[str, Any]]:
    """声明 + 全部复盘件 → (issues, warns, stats)。"""
    issues: List[str] = []
    warns: List[str] = []
    d = decl(root)
    if not d:
        return ["缺复盘协议声明 %s" % DECL_REL], warns, {}
    if str(d.get("schema") or "") != SCHEMA:
        issues.append("复盘协议 schema 不匹配（期望 %s）" % SCHEMA)
    if tuple(d.get("sections") or ()) != ("现象", "影响", "根因", "行动项"):
        issues.append("sections 必须是四段（现象/影响/根因/行动项）")
    for k in ("blame_tokens", "root_cause_tokens"):
        if not (d.get(k) or []):
            issues.append("%s 不得为空（无指责与根因判据必须成文）" % k)
    rows = entries(root)
    acts = 0
    for e in rows:
        i, st = check_doc(root, e["path"])
        issues += ["%s：%s" % (e["fm"].get("id") or e["file"], x) for x in i]
        acts += st.get("actions", 0)
    if not rows:
        warns.append("暂无复盘件（%s）——门禁空转" % GLOB)
    return issues, warns, {"postmortems": len(rows), "actions": acts}
