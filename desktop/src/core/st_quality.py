"""ST 制卡质量规范门禁（验收层规范的**数据化**：M/S/R → fail/warn/info）。

真源 `protocol/st_quality.json`。本模块只做两件确定性的事：

1. **声明完整性**：id 唯一且前缀等于 scope；level ∈ {M,S,R}；scope ∈ {C,W,V,X}；
   每条须有 rule 与 basis；`check` ∈ {declaration, artifact}；
   `status: draft` 时 `pending` 必须非空（草案必须写明还差什么 —— 防"草案当成品"）。
2. **可落到产物的规则就判**：标 `check: artifact` 的规则在**真实产物**上核。
   当前只有 V2（初始值完备）：`mvu_variables.json` 的 `initial` 键集合必须 ⊆ 变量名集合
   —— 真跑实测通过（4 变量 / 4 初值键）。

边界：NF **不做 ST 运行时**，不解析 PNG/实卡（那属 A-S3 校验器）；本件只声明 + 能判的判。
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

DECL_REL = "protocol/st_quality.json"
SCHEMA = "nf-st-quality/1"
ARTIFACT_REL = "docs/examples/mvu-output/mvu_variables.json"


def decl(root: str = ".") -> Dict[str, Any]:
    p = Path(root) / DECL_REL
    return json.loads(p.read_text(encoding="utf-8")) if p.is_file() else {}


def _check_v2(root: str) -> List[str]:
    """V2 初始值完备：initial 键集合 ⊆ 变量名集合。"""
    p = Path(root) / ARTIFACT_REL
    if not p.is_file():
        return []
    doc = json.loads(p.read_text(encoding="utf-8"))
    names = {str(v.get("name")) for v in (doc.get("variables") or [])}
    init = doc.get("initial") or {}
    extra = sorted(set(init) - names)
    return (["V2：初始值含未声明变量 %s（initial 与变量表不一一对应）" % "、".join(extra)]
            if extra else [])


def _check_checklist(root: str, d: Dict[str, Any]) -> List[str]:
    """清单必须覆盖全部规则：`checklist` 指向的件里每个规则 id 都要出现（否则清单是装饰）。"""
    rel = str(d.get("checklist") or "")
    if not rel:
        return ["缺 checklist 字段——人工自查清单必须登记（否则 S 级规则无处落地）"]
    p = Path(root) / rel
    if not p.is_file():
        return ["自查清单不存在：%s" % rel]
    text = p.read_text(encoding="utf-8")
    miss = [str(r.get("id")) for r in (d.get("rules") or [])
            if str(r.get("id")) and ("| %s |" % r.get("id")) not in text]
    return (["自查清单未覆盖规则：%s" % "、".join(miss)] if miss else [])


def scan(root: str = ".") -> Tuple[List[str], List[str], Dict[str, Any]]:
    """→ (issues, warns, stats)。M→fail；S 的现状项进 warns；R 只计数。"""
    issues: List[str] = []
    warns: List[str] = []
    d = decl(root)
    if not d:
        return ["缺 ST 制卡质量规范 %s" % DECL_REL], warns, {}
    if str(d.get("schema") or "") != SCHEMA:
        issues.append("规范 schema 不匹配（期望 %s）" % SCHEMA)
    levels = tuple(d.get("level_vocabulary") or ())
    scopes = tuple(d.get("scope_vocabulary") or ())
    checks = tuple(d.get("check_vocabulary") or ())
    if levels != ("M", "S", "R"):
        issues.append("level 词表必须为 M/S/R")
    if scopes != ("C", "W", "V", "X"):
        issues.append("scope 词表必须为 C/W/V/X")
    if checks != ("declaration", "artifact"):
        issues.append("check 词表必须为 declaration/artifact")
    if str(d.get("status")) == "draft" and not (d.get("pending") or []):
        issues.append("status=draft 但 pending 为空——草案必须写明还差什么")
    seen = set()
    by_level: Dict[str, int] = {k: 0 for k in levels}
    arts: List[str] = []
    for r in d.get("rules") or []:
        rid = str(r.get("id") or "")
        tag = rid or "(无名)"
        if rid in seen:
            issues.append("规则 id 重复：%s" % rid)
        seen.add(rid)
        scope = str(r.get("scope") or "")
        if scope not in scopes:
            issues.append("%s scope 越词表：%s" % (tag, scope))
        elif rid and not rid.startswith(scope):
            issues.append("%s 的 id 前缀与 scope 不一致（应 %s 开头）" % (tag, scope))
        lv = str(r.get("level") or "")
        if lv not in levels:
            issues.append("%s level 越词表：%s" % (tag, lv))
        else:
            by_level[lv] = by_level.get(lv, 0) + 1
        for k in ("rule", "basis", "check"):
            if not str(r.get(k) or "").strip():
                issues.append("%s 缺必填字段：%s" % (tag, k))
        if str(r.get("check")) == "artifact":
            arts.append(rid)
    for rid in arts:
        if rid == "V2":
            issues += _check_v2(root)
    issues += _check_checklist(root, d)
    if (d.get("pending") or []):
        warns.append("规范为草案：%d 项待补（%s）" % (len(d["pending"]), "；".join(d["pending"][:2])))
    stats = {"rules": len(seen), "by_level": by_level,
             "artifact_checked": sum(1 for r in arts)}
    return issues, warns, stats
