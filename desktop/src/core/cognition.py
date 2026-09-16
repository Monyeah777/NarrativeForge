"""认知族门禁：行话术语表（glossary）+ 执行面分档（runbook / playbook）。

真源：`protocol/glossary.json`、`protocol/execution_modes.json`。

判据（全部可证，零第三方依赖）：
- 术语：term 唯一；definition 非空；**source 必须真实存在且逐字出现该术语**；
  **used_in 每条也必须真实存在且逐字出现该术语**（防"登记没人用的行话"）；
- 分档：mode id 唯一；required_blocks 非空；instances ≥1 且每件必须**逐字含全部必备结构块**
  （防自称 Runbook 却没有步骤/预期）。
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

GLOSSARY_REL = "protocol/glossary.json"
MODES_REL = "protocol/execution_modes.json"
G_SCHEMA = "nf-glossary/1"
M_SCHEMA = "nf-execution-modes/1"
_BLOCK = re.compile(r"^\s*(?:[-*]|\d+[.、]|#{2,4})\s*", re.M)


def _load(root: str, rel: str) -> Dict[str, Any]:
    p = Path(root) / rel
    return json.loads(p.read_text(encoding="utf-8")) if p.is_file() else {}


def _text(root: str, rel: str) -> str:
    p = Path(root) / rel
    return p.read_text(encoding="utf-8") if p.is_file() else ""


def verify_glossary(root: str = ".") -> Tuple[List[str], List[str], Dict[str, Any]]:
    issues: List[str] = []
    warns: List[str] = []
    doc = _load(root, GLOSSARY_REL)
    if not doc:
        return ["缺术语表 %s" % GLOSSARY_REL], warns, {}
    if str(doc.get("schema") or "") != G_SCHEMA:
        issues.append("术语表 schema 不匹配（期望 %s）" % G_SCHEMA)
    if not (doc.get("rules") or []):
        issues.append("术语表 rules 不得为空（登记纪律必须成文）")
    seen = set()
    uses = 0
    for t in doc.get("terms") or []:
        term = str(t.get("term") or "")
        if not term:
            issues.append("存在无 term 的条目")
            continue
        if term in seen:
            issues.append("术语重复：%s" % term)
        seen.add(term)
        if not str(t.get("definition") or "").strip():
            issues.append("术语 %s 缺 definition" % term)
        src = str(t.get("source") or "")
        if not (Path(root) / src).is_file():
            issues.append("术语 %s 的 source 不存在：%s" % (term, src))
        elif term not in _text(root, src):
            issues.append("术语 %s 未在其 source 中逐字出现：%s（定义必须落在真源里）"
                          % (term, src))
        ui = t.get("used_in") or []
        if isinstance(ui, str):
            ui = [ui]
        for rel in ui:
            rel = str(rel)
            if not (Path(root) / rel).is_file():
                issues.append("术语 %s 的 used_in 不存在：%s" % (term, rel))
            elif term not in _text(root, rel):
                issues.append("术语 %s 的 used_in 未逐字出现该术语：%s（防登记没人用的行话）"
                              % (term, rel))
            else:
                uses += 1
    return issues, warns, {"terms": len(seen), "uses": uses}


def verify_modes(root: str = ".") -> Tuple[List[str], List[str], Dict[str, Any]]:
    issues: List[str] = []
    warns: List[str] = []
    doc = _load(root, MODES_REL)
    if not doc:
        return ["缺执行分档声明 %s" % MODES_REL], warns, {}
    if str(doc.get("schema") or "") != M_SCHEMA:
        issues.append("执行分档 schema 不匹配（期望 %s）" % M_SCHEMA)
    seen = set()
    insts = 0
    for m in doc.get("modes") or []:
        mid = str(m.get("id") or "")
        if mid in seen:
            issues.append("mode id 重复：%s" % mid)
        seen.add(mid)
        blocks = [str(b) for b in (m.get("required_blocks") or [])]
        if not blocks:
            issues.append("mode %s 缺 required_blocks（该档必备结构必须成文）" % mid)
        rows = m.get("instances") or []
        if not rows:
            issues.append("mode %s 无实例（声明了档却没有件属于它）" % mid)
        for rel in rows:
            rel = str(rel)
            if not (Path(root) / rel).is_file():
                issues.append("mode %s 的实例不存在：%s" % (mid, rel))
                continue
            txt = _text(root, rel)
            miss = [b for b in blocks if b not in txt]
            if miss:
                issues.append("实例 %s 不属于 %s 档：缺结构块 %s" % (rel, mid, "/".join(miss)))
            else:
                insts += 1
    return issues, warns, {"modes": len(seen), "instances_ok": insts}


def scan(root: str = ".") -> Tuple[List[str], List[str], Dict[str, Any]]:
    issues: List[str] = []
    warns: List[str] = []
    stats: Dict[str, Any] = {}
    for name, fn in (("glossary", verify_glossary), ("modes", verify_modes)):
        i, w, s = fn(root)
        issues += i
        warns += w
        stats[name] = s
    return issues, warns, stats
