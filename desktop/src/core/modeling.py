"""内容建模三件门禁：词表登记册 / 规范与说明件之分 / 数据契约登记。

机制借鉴（一句式）：SKOS 的概念方案（概念用标识符 + 标签 + 映射管理）、标准治理里的
normative / informative 二分、ODCS 与 Data Contract Specification 的数据契约要素。

判据（全部可证、零第三方依赖）：
- **词表**：每个 scheme 用 probe 指回真源（`python_attr` / `json_path` / `literal`），
  声明值必须与真源**逐项一致**；id 唯一；status 在册；值不得重复且不得与 aliases 撞车。
- **规范/说明**：两份名单交集为空；规范件必须被回执锚定**或**显式 `covered_by`（checkN 须真实存在）；
  说明件**不得**出现在回执覆盖面内（否则等于把解释当规范）。
- **数据契约**：artifact 必须存在；`quality_rule` 必须解析到**真实**的 `checkN` 或 `assertion:<id>`；
  owner / freshness 非空；status 在册。
"""
from __future__ import annotations

import importlib
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

VOCAB_REL = "protocol/vocabularies.json"
NORM_REL = "protocol/normative.json"
DC_REL = "protocol/data_contracts.json"
RECEIPTS_REL = "protocol/RECEIPTS.json"
VOCAB_SCHEMA = "nf-vocabularies/1"
NORM_SCHEMA = "nf-normative/1"
DC_SCHEMA = "nf-data-contracts/1"
_CHECK_RE = re.compile(r"^check(\d+)$")


def _read(root: str, rel: str) -> Dict[str, Any]:
    p = Path(root) / rel
    return json.loads(p.read_text(encoding="utf-8")) if p.is_file() else {}


def _as_values(obj: Any) -> List[str]:
    if isinstance(obj, dict):
        return [str(k) for k in obj]
    if isinstance(obj, (list, tuple)):
        return [str(x) for x in obj]
    return []


def _probe(root: str, probe: Dict[str, Any]) -> Tuple[List[str], str]:
    kind = str(probe.get("kind") or "")
    if kind == "literal":
        return [], "literal（以本册为准）"
    if kind == "python_attr":
        mod = importlib.import_module(str(probe.get("module") or ""))
        return _as_values(getattr(mod, str(probe.get("attr") or ""))), "python_attr"
    if kind == "json_path":
        doc: Any = _read(root, str(probe.get("file") or ""))
        for part in str(probe.get("path") or "").split("."):
            if not isinstance(doc, dict) or part not in doc:
                return [], "json_path 断链：%s" % probe.get("path")
            doc = doc[part]
        return _as_values(doc), "json_path"
    return [], "未知 probe.kind：%s" % kind


def verify_vocabularies(root: str = ".") -> Tuple[List[str], List[str], Dict[str, Any]]:
    issues: List[str] = []
    warns: List[str] = []
    doc = _read(root, VOCAB_REL)
    if not doc:
        return ["缺词表登记册 %s" % VOCAB_REL], warns, {}
    if str(doc.get("schema") or "") != VOCAB_SCHEMA:
        issues.append("词表登记册 schema 不匹配（期望 %s）" % VOCAB_SCHEMA)
    statuses = tuple(doc.get("status_vocabulary") or ())
    if sorted(statuses) != ["active", "deprecated"]:
        issues.append("status 词表与判据不一致（期望 active/deprecated）")
    kinds = tuple(doc.get("probe_kinds") or ())
    seen = set()
    for s in doc.get("schemes") or []:
        sid = str(s.get("id") or "")
        if sid in seen:
            issues.append("词表 id 重复：%s" % sid)
        seen.add(sid)
        if str(s.get("status")) not in statuses:
            issues.append("词表 %s status 越词表：%s" % (sid, s.get("status")))
        vals = [str(v) for v in (s.get("values") or [])]
        if len(vals) < 2:
            issues.append("词表 %s 少于两个值（不成词表）" % sid)
        if len(set(vals)) != len(vals):
            issues.append("词表 %s 值重复" % sid)
        for a in (s.get("aliases") or []):
            if str(a) in vals:
                issues.append("词表 %s 的 alias 与值撞车：%s" % (sid, a))
        probe = s.get("probe") if isinstance(s.get("probe"), dict) else {}
        if str(probe.get("kind")) not in kinds:
            issues.append("词表 %s 的 probe.kind 不在册：%s" % (sid, probe.get("kind")))
            continue
        live, note = _probe(root, probe)
        if str(probe.get("kind")) == "literal":
            continue
        if not live:
            issues.append("词表 %s 的真源取不到（%s）" % (sid, note))
            continue
        if sorted(live) != sorted(vals):
            issues.append("词表 %s 与真源漂移：册=%s 真源=%s"
                          % (sid, "/".join(sorted(vals)), "/".join(sorted(live))))
    stats = {"schemes": len(seen),
             "literal": sum(1 for s in (doc.get("schemes") or [])
                            if str((s.get("probe") or {}).get("kind")) == "literal")}
    return issues, warns, stats


def _receipt_ids(root: str) -> set:
    doc = _read(root, RECEIPTS_REL)
    return {str(e.get("id")) for e in (doc.get("entries") or [])}


def verify_normative(root: str = ".") -> Tuple[List[str], List[str], Dict[str, Any]]:
    issues: List[str] = []
    warns: List[str] = []
    doc = _read(root, NORM_REL)
    if not doc:
        return ["缺规范/说明件名单 %s" % NORM_REL], warns, {}
    if str(doc.get("schema") or "") != NORM_SCHEMA:
        issues.append("规范件名单 schema 不匹配（期望 %s）" % NORM_SCHEMA)
    r = Path(root)
    verify_sh = (r / "verify.sh").read_text(encoding="utf-8") if (r / "verify.sh").is_file() else ""
    checks = set(re.findall(r"^check(\d+)\(\)\{", verify_sh, re.M))
    receipts = _receipt_ids(root)
    norm_paths = []
    for item in doc.get("normative") or []:
        entry = item if isinstance(item, dict) else {"path": str(item)}
        rel = str(entry.get("path") or "")
        norm_paths.append(rel)
        if not rel:
            issues.append("规范件条目缺 path")
            continue
        if not (r / rel).is_file():
            issues.append("规范件不存在：%s" % rel)
            continue
        if rel in receipts:
            continue
        covered = [str(c) for c in (entry.get("covered_by") or [])]
        if not covered:
            issues.append("规范件既未被回执锚定也无 covered_by：%s"
                          "（修复指引：跑 nf receipts --write，或显式声明 covered_by）" % rel)
            continue
        for c in covered:
            m = _CHECK_RE.match(c)
            if m and m.group(1) not in checks:
                issues.append("规范件 %s 的 covered_by 指向不存在的 check：%s" % (rel, c))
    info_globs = [str(g) for g in (doc.get("informative") or [])]
    info_hits: set = set()
    for g in info_globs:
        pat = g + "/*" if g.endswith("/**") else g
        hits = [p for p in r.glob(pat) if p.is_file()] if any(
            ch in pat for ch in "*?[") else ([r / pat] if (r / pat).is_file() else [])
        if not hits:
            warns.append("说明件名单的条目无匹配（可能写错）：%s" % g)
        for p in hits:
            info_hits.add(p.relative_to(r).as_posix())
    for rel in sorted(info_hits):
        if rel in receipts:
            issues.append("说明件被回执锚定（等于把解释当规范）：%s" % rel)
    overlap = sorted(set(norm_paths) & info_hits)
    for rel in overlap:
        issues.append("同一件既列规范又列说明：%s" % rel)
    stats = {"normative": len(norm_paths), "informative_files": len(info_hits),
             "receipts": len(receipts)}
    return issues, warns, stats


def verify_contracts(root: str = ".") -> Tuple[List[str], List[str], Dict[str, Any]]:
    issues: List[str] = []
    warns: List[str] = []
    doc = _read(root, DC_REL)
    if not doc:
        return ["缺数据契约登记 %s" % DC_REL], warns, {}
    if str(doc.get("schema") or "") != DC_SCHEMA:
        issues.append("数据契约登记 schema 不匹配（期望 %s）" % DC_SCHEMA)
    statuses = tuple(doc.get("status_vocabulary") or ())
    prefixes = tuple(doc.get("rule_prefixes") or ())
    if prefixes != ("check", "assertion:"):
        issues.append("rule_prefixes 与判据不一致（期望 check / assertion:）")
    r = Path(root)
    verify_sh = (r / "verify.sh").read_text(encoding="utf-8") if (r / "verify.sh").is_file() else ""
    checks = set(re.findall(r"^check(\d+)\(\)\{", verify_sh, re.M))
    assertion_ids = {str(a.get("id")) for a in
                     (_read(root, "protocol/assertions.json").get("assertions") or [])}
    seen = set()
    for c in doc.get("contracts") or []:
        cid = str(c.get("id") or "")
        if cid in seen:
            issues.append("契约 id 重复：%s" % cid)
        seen.add(cid)
        art = str(c.get("artifact") or "")
        if not art or not (r / art).is_file():
            issues.append("契约 %s 的 artifact 不存在：%s" % (cid, art or "(缺)"))
        if str(c.get("status")) not in statuses:
            issues.append("契约 %s status 越词表：%s" % (cid, c.get("status")))
        if not str(c.get("owner") or "").strip():
            issues.append("契约 %s 缺 owner（无人认领的契约不许登记）" % cid)
        if not str(c.get("freshness") or "").strip():
            issues.append("契约 %s 缺 freshness（重建动作必须写明）" % cid)
        rule = str(c.get("quality_rule") or "")
        if rule.startswith("check"):
            n = rule[5:]
            if n not in checks:
                issues.append("契约 %s 的 quality_rule 指向不存在的 check：%s" % (cid, rule))
        elif rule.startswith("assertion:"):
            aid = rule.split(":", 1)[1]
            if aid not in assertion_ids:
                issues.append("契约 %s 的 quality_rule 指向不存在的断言：%s" % (cid, rule))
        else:
            issues.append("契约 %s 的 quality_rule 无法解析（须 checkN 或 assertion:<id>）：%s"
                          % (cid, rule or "(缺)"))
    stats = {"contracts": len(seen), "checks_seen": len(checks),
             "assertions_seen": len(assertion_ids)}
    return issues, warns, stats


def scan(root: str = ".") -> Tuple[List[str], List[str], Dict[str, Any]]:
    """三件聚合 → (issues, warns, stats)。"""
    issues: List[str] = []
    warns: List[str] = []
    stats: Dict[str, Any] = {}
    for name, fn in (("vocabularies", verify_vocabularies),
                     ("normative", verify_normative),
                     ("data_contracts", verify_contracts)):
        i, w, s = fn(root)
        issues += i
        warns += w
        stats[name] = s
    return issues, warns, stats
