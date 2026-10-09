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

from core import doc_family

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
    out = doc_family.entries(root, GLOB)
    out.sort(key=lambda e: str(e["fm"].get("id") or e["file"]))
    return out


def _receipt_ids(root: str) -> set:
    p = Path(root) / RECEIPTS_REL
    if not p.is_file():
        return set()
    import json
    doc = json.loads(p.read_text(encoding="utf-8"))
    return {str(e.get("id")) for e in (doc.get("entries") or [])}


def _check_entry_id(fm: Dict[str, Any], name: str, did: str,
                    ids: Dict[str, str], issues: List[str]) -> None:
    """单条目编号面：id 形态、id ↔ 文件名一致、编号重复。"""
    if not _ID.match(did):
        issues.append("%s 的 id 不合法（须 ADR-四位数字）：%s" % (name, did))
    m = _FILE_ID.match(name)
    if not m or ("ADR-%s" % m.group(1)) != did:
        issues.append("%s 的 id 与文件名不一致：%s" % (name, did))
    if did in ids:
        issues.append("ADR 编号重复：%s（%s 与 %s）" % (did, ids[did], name))


def _check_required_fields(fm: Dict[str, Any], tag: str, issues: List[str]) -> None:
    for k in ("title", "status", "date", "evidence"):
        if not fm.get(k):
            issues.append("%s 缺必填字段：%s" % (tag, k))


def _check_sections(body: str, tag: str, issues: List[str]) -> None:
    for sec in SECTIONS:
        if sec not in body:
            issues.append("%s 正文缺段落：%s" % (tag, sec))


def _check_entry_fields(fm: Dict[str, Any], tag: str, body: str,
                        issues: List[str]) -> str:
    """单条目字段面（必填字段 / status 词表 / date 形态 / 正文段落）→ 返回 status。"""
    _check_required_fields(fm, tag, issues)
    st = str(fm.get("status") or "")
    if st and st not in STATUSES:
        issues.append("%s 的 status 越词表：%s（%s）" % (tag, st, "/".join(STATUSES)))
    date = str(fm.get("date") or "")
    if date and not _DATED.match(date):
        issues.append("%s 的 date 非 YYYY-MM-DD：%s" % (tag, date))
    _check_sections(body, tag, issues)
    return st


def _check_entry_evidence(fm: Dict[str, Any], tag: str, r: Path,
                          checks: set, issues: List[str]) -> None:
    """单条目证据面：空项 / 指向的 checkN 存在 / 跨 ADR 引用放行 / 路径可达。"""
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


def _check_entry_lifecycle(fm: Dict[str, Any], tag: str, path: str, st: str, did: str,
                           has_receipts: bool, receipts: set,
                           supby: Dict[str, str], issues: List[str]) -> None:
    """单条目生命周期面：accepted 是否被回执锚定、superseded 是否给了 superseded_by。"""
    if st == "accepted" and has_receipts and path not in receipts:
        issues.append("%s 已 accepted 但未被协议回执锚定（修复指引：nf receipts --write）"
                      "——未锚定的 accepted 等于可被偷改" % tag)
    sb = str(fm.get("superseded_by") or "").strip()
    if st == "superseded" and sb in _DASH:
        issues.append("%s 标 superseded 但缺 superseded_by" % tag)
    if sb not in _DASH:
        supby[did] = sb


def _check_supersede_chains(supby: Dict[str, str], ids: Dict[str, str],
                            issues: List[str]) -> None:
    """取代链：目标须在册、且**不成环**（最多走 len(supby)+1 跳）。"""
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


def _check_supersedes(ids: Dict[str, str], rows: List[Dict[str, Any]],
                      issues: List[str]) -> None:
    """反向引用：「supersedes」指向的编号须在册。"""
    for did in ids:
        for other in rows:
            if str(other["fm"].get("id")) != did:
                continue
            sup = str(other["fm"].get("supersedes") or "").strip()
            if sup not in _DASH and sup not in ids:
                issues.append("%s 的 supersedes 指向不在册编号：%s" % (did, sup))


def scan(root: str = ".") -> Tuple[List[str], List[str], Dict[str, Any]]:
    """机检 → (issues, warns, stats)。"""
    issues: List[str] = []
    warns: List[str] = []
    rows = entries(root)
    if not rows:
        return ["未发现任何 ADR（%s）" % GLOB], warns, {"decisions": 0}
    r = Path(root)
    checks = doc_family.check_numbers(root)
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
        _check_entry_id(fm, name, did, ids, issues)
        ids[did] = name
        st = _check_entry_fields(fm, tag, e["body"], issues)
        _check_entry_evidence(fm, tag, r, checks, issues)
        _check_entry_lifecycle(fm, tag, path, st, did, has_receipts, receipts, supby, issues)
    _check_supersede_chains(supby, ids, issues)
    _check_supersedes(ids, rows, issues)
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
    return doc_family.write_index(
        root, index_rel=INDEX_REL, header="# NF 决策记录索引（INDEX）\n\n",
        begin=BEGIN, end=END, block=render_index(root))


def check_projection(root: str = ".") -> List[str]:
    return doc_family.check_index(
        root, index_rel=INDEX_REL, begin=BEGIN, end=END, block=render_index(root),
        missing_hint="nf decisions reindex",
        mismatch="决策登记表与实时重算不一致（跑 nf decisions reindex）")
