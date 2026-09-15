"""决策记录门禁（ADR：一条决策一编号，采纳后不改不删，只可被取代）。

真源 = `decisions/ADR-*.md` 的 frontmatter + 正文；`decisions/INDEX.md` 是投影。

判据（全部可证，零第三方依赖）：
- 编号：`id` 必须等于文件名前缀 `ADR-\\d{4}`；全库唯一；
- 状态：`status ∈ {proposed, accepted, superseded, deprecated}`；`date` 为 YYYY-MM-DD；
- 三段齐：正文必须含 `## 背景` / `## 决策` / `## 后果`；
- 取代链：`supersedes` 与 `superseded_by` 互指、编号在册、链可解析且不成环；
- 证据可解析：`evidence` 每条须解析到仓库真实件、`checkN`（verify.sh 在册）或 `ADR-N`；
- **不可改**：`status: accepted` 的 ADR 必须已被协议回执锚定（`protocol/RECEIPTS.json`）——
  正文一改回执即失效，于是"改了"必然被 check35 抓住，决策只能靠新增 + 互指 supersede 演进。
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

from core.library import parse_frontmatter

GLOB = "decisions/ADR-*.md"
INDEX_REL = "decisions/INDEX.md"
RECEIPTS_REL = "protocol/RECEIPTS.json"
BEGIN = "<!-- BEGIN GENERATED: decisions-index -->"
END = "<!-- END GENERATED: decisions-index -->"
STATUSES = ("proposed", "accepted", "superseded", "deprecated")
SECTIONS = ("## 背景", "## 决策", "## 后果")
_ID = re.compile(r"^ADR-(\d{4})$")
_FILE_ID = re.compile(r"^ADR-(\d{4})-")
_CHECK = re.compile(r"^check(\d+)$")
_ADR = re.compile(r"^ADR-\d{4}$")
_DATED = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_DASH = ("—", "-", "")


def entries(root: str = ".") -> List[Dict[str, Any]]:
    r = Path(root)
    out = []
    for p in sorted(r.glob(GLOB)):
        fm, body = parse_frontmatter(p.read_text(encoding="utf-8"))
        out.append({"path": p.relative_to(r).as_posix(), "file": p.name,
                    "fm": fm or {}, "body": body or ""})
    out.sort(key=lambda e: str(e["fm"].get("id") or e["file"]))
    return out


def _receipt_ids(root: str) -> set:
    p = Path(root) / RECEIPTS_REL
    if not p.is_file():
        return set()
    import json
    doc = json.loads(p.read_text(encoding="utf-8"))
    return {str(e.get("id")) for e in (doc.get("entries") or [])}


def scan(root: str = ".") -> Tuple[List[str], List[str], Dict[str, Any]]:
    """机检 → (issues, warns, stats)。"""
    issues: List[str] = []
    warns: List[str] = []
    rows = entries(root)
    if not rows:
        return ["未发现任何 ADR（%s）" % GLOB], warns, {"decisions": 0}
    r = Path(root)
    verify = (r / "verify.sh").read_text(encoding="utf-8") if (r / "verify.sh").is_file() else ""
    checks = set(re.findall(r"^check(\d+)\(\)\{", verify, re.M))
    receipts = _receipt_ids(root)
    has_receipts = (r / RECEIPTS_REL).is_file()
    ids: Dict[str, str] = {}
    supby: Dict[str, str] = {}
    for e in rows:
        fm, name, path = e["fm"], e["file"], e["path"]
        did = str(fm.get("id") or "")
        tag = did or name
        if not did:
            issues.append("%s 缺 frontmatter id" % name)
            continue
        if not _ID.match(did):
            issues.append("%s 的 id 不合法（须 ADR-四位数字）：%s" % (name, did))
        m = _FILE_ID.match(name)
        if not m or ("ADR-%s" % m.group(1)) != did:
            issues.append("%s 的 id 与文件名不一致：%s" % (name, did))
        if did in ids:
            issues.append("ADR 编号重复：%s（%s 与 %s）" % (did, ids[did], name))
        ids[did] = name
        for k in ("title", "status", "date", "evidence"):
            if not fm.get(k):
                issues.append("%s 缺必填字段：%s" % (tag, k))
        st = str(fm.get("status") or "")
        if st and st not in STATUSES:
            issues.append("%s 的 status 越词表：%s（%s）" % (tag, st, "/".join(STATUSES)))
        date = str(fm.get("date") or "")
        if date and not _DATED.match(date):
            issues.append("%s 的 date 非 YYYY-MM-DD：%s" % (tag, date))
        for sec in SECTIONS:
            if sec not in e["body"]:
                issues.append("%s 正文缺段落：%s" % (tag, sec))
        for ev in (fm.get("evidence") or []):
            s = str(ev).strip()
            if not s:
                issues.append("%s 的 evidence 有空项" % tag)
                continue
            c = _CHECK.match(s)
            if c:
                if c.group(1) not in checks:
                    issues.append("%s 的 evidence 指向不存在的 check：%s" % (tag, s))
                continue
            if _ADR.match(s):
                continue                       # 跨 ADR 引用在链检查里统一判
            sp = s.replace("\\", "/")
            if not (r / sp).exists():
                issues.append("%s 的 evidence 无法解析：%s（修复指引：改为真实件路径，"
                              "或 checkN，或 ADR-N）" % (tag, s))
        if st == "accepted" and has_receipts and path not in receipts:
            issues.append("%s 已 accepted 但未被协议回执锚定（修复指引：nf receipts --write）"
                          "——未锚定的 accepted 等于可被偷改" % tag)
        sb = str(fm.get("superseded_by") or "").strip()
        if st == "superseded" and sb in _DASH:
            issues.append("%s 标 superseded 但缺 superseded_by" % tag)
        if sb not in _DASH:
            supby[did] = sb
    for did, target in supby.items():
        if target not in ids:
            issues.append("%s 的 superseded_by 指向不在册编号：%s" % (did, target))
            continue
        cur, hops = target, 0
        while cur in supby and hops < len(supby) + 1:
            cur = supby[cur]
            hops += 1
            if cur == did:
                issues.append("取代链成环：%s → … → %s" % (did, did))
                break
    for did, name in ids.items():
        for other in rows:
            if str(other["fm"].get("id")) != did:
                continue
            sup = str(other["fm"].get("supersedes") or "").strip()
            if sup not in _DASH and sup not in ids:
                issues.append("%s 的 supersedes 指向不在册编号：%s" % (did, sup))
    stats = {"decisions": len(ids),
             "accepted": sum(1 for e in rows if str(e["fm"].get("status")) == "accepted"),
             "chains": len(supby)}
    return issues, warns, stats


def render_index(root: str = ".") -> str:
    out = [BEGIN, "", "## 决策登记表（由各 ADR frontmatter 生成，勿手改）", "",
           "| 编号 | 标题 | 状态 | 日期 | 取代 |", "|---|---|---|---|---|"]
    for e in entries(root):
        fm = e["fm"]
        out.append("| %s | %s | %s | %s | %s |" % (
            fm.get("id", e["file"]), fm.get("title", ""), fm.get("status", ""),
            fm.get("date", ""), fm.get("superseded_by") or "—"))
    out += ["", "> 真源 = `decisions/ADR-*.md` 的 frontmatter；本表为投影（`nf decisions reindex` 重建）。",
            "", END]
    return "\n".join(out)


def write_projection(root: str = ".") -> Dict[str, Any]:
    p = Path(root) / INDEX_REL
    if not p.is_file():
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("# NF 决策记录索引（INDEX）\n\n" + BEGIN + "\n" + END + "\n",
                     encoding="utf-8", newline="\n")
    text = p.read_text(encoding="utf-8")
    block = render_index(root)
    if BEGIN in text and END in text:
        new = text[:text.index(BEGIN)] + block + text[text.index(END) + len(END):]
    else:
        new = text.rstrip("\n") + "\n\n" + block + "\n"
    changed = new != text
    if changed:
        p.write_text(new, encoding="utf-8", newline="\n")
    return {"changed": changed, "path": INDEX_REL}


def check_projection(root: str = ".") -> List[str]:
    p = Path(root) / INDEX_REL
    if not p.is_file():
        return ["缺 %s（修复指引：nf decisions reindex）" % INDEX_REL]
    text = p.read_text(encoding="utf-8")
    if BEGIN not in text or END not in text:
        return ["%s 缺生成区标记" % INDEX_REL]
    cur = text[text.index(BEGIN):text.index(END) + len(END)]
    return [] if cur == render_index(root) else ["决策登记表与实时重算不一致（跑 nf decisions reindex）"]
