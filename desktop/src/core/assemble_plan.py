"""44 · 需求 → 自组装编排（内部闭环）：需求文本 → 装配计划 → 成品机器验收。

战略口径（STRATEGY §一/§三）：用户提需求自组装是 AI 通道的最终价值；本模块把
「需求→选包→取件→成品自检」做成可复现的内部编排：
1. plan(requirement)  需求关键词 → 预设包/管线 + 取件清单（模块/管线/资产）
2. check(output_md, plan) 对成品做机器验收：八段骨架在场、编号在装配允许集、
   决策句带引用、无编造编号（对齐 execution_drill R1/R3/R4 口径）。

封闭期内不引外部 AI 实测；成品验收用仓库内真实战例（完整版样本）做回归样本。
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

_ROOT = Path(__file__).resolve().parents[3]

#: 需求关键词 → 官方预设（包 id / 管线 id）
DOMAIN_MAP = [
    (["西幻", "生存", "生存流"], ("西幻生存领域包", "P03")),
    (["校园", "情感", "恋爱", "毕业"], ("校园情感领域包", "P02")),
    (["轻混", "组合", "混搭"], ("校园西幻轻混组合包", "P04")),
    (["通用核心", "核心基础"], ("通用核心基础包", "P05")),
    (["技术文档", "techdoc", "文档工厂"], ("技术文档域包", "P06")),
]

_SEG = re.compile(r"^##\s*([0-7])\s*\.", re.M)
_MODULE = re.compile(r"(?:[\u4e00-\u9fff]+:)?M\d{2,3}")
_DECISION = re.compile(r"(应|应该|必须|禁止|不得|下一步|输出|结论)")
_CITATION = re.compile(r"(§\s*\d+(?:[.-]\d+)*|第\s*\d+\s*(?:节|步|章)|L\d+|"
                       r"[0-9A-Za-z_]+:[MTP]\d{2,3}|\b\d{1,3}\b\s*行)")


def _official_core_ids() -> List[str]:
    reg = json.loads((_ROOT / "desktop/src/core/registry.json").read_text(encoding="utf-8"))
    return [str(m["id"]) for m in reg.get("modules", [])]


def _package_module_sets() -> Dict[str, List[str]]:
    import yaml

    sets: Dict[str, List[str]] = {}
    for proto in sorted((_ROOT / "community").glob("*/protocol.yaml")):
        try:
            data = yaml.safe_load(proto.read_text(encoding="utf-8"))
            pkg = (data.get("package") or {}).get("id")
            mids = [(data.get("package") or {}).get("module_id_range") or []]
            if pkg:
                sets[str(pkg)] = [str(x) for x in mids[0]]
        except Exception:
            continue
    return sets


def plan(requirement: str) -> Dict[str, Any]:
    """需求 → 装配计划（预设包 + 取件清单）。"""
    req = requirement.strip()
    pkg, pipeline = None, None
    for keys, hit in DOMAIN_MAP:
        if any(k in req for k in keys):
            pkg, pipeline = hit
            break
    modules: List[str] = []
    matched = bool(pkg)
    if pkg:
        proto = _ROOT / "community" / pkg / "protocol.yaml"
        if proto.is_file():
            try:
                import yaml
                data = yaml.safe_load(proto.read_text(encoding="utf-8"))
                modules = [str(x) for x in (data.get("package") or {}).get("module_id_range") or []]
            except Exception:
                modules = []
    packages = _package_module_sets()
    if not matched:
        # 用户自定义/未命中：允许全域已登记模块（官方核心 + 各社区包），
        # 并给出自定义预留槽位；自定义件须先按模板落库登记，验收才认。
        for mids in packages.values():
            modules += mids
        modules = sorted(set(modules))
        known = sorted(packages)
    else:
        known = [pkg]
    allowed = sorted(set(_official_core_ids() + modules))
    if pipeline and pkg:
        pipeline_path = (_ROOT / "community" / pkg / "pipelines").glob("%s*.md" % pipeline)
        pipe_files = [p.relative_to(_ROOT).as_posix() for p in pipeline_path]
    else:
        pipe_files = []
    return {
        "requirement": req,
        "matched": matched,
        "package": pkg,
        "pipeline": pipeline,
        "pipeline_files": pipe_files,
        "fetch_modules": modules or [str(x) for x in _official_core_ids()],
        "allowed_module_ids": allowed,
        "known_packages": known,
        "status": "preset" if matched else "custom",
    }


def check(output_md: str, plan_: Dict[str, Any]) -> Tuple[List[str], Dict[str, int]]:
    """成品机器验收：八段骨架 / 编号在允许集 / 决策句带引用 / 无编造编号。"""
    issues: List[str] = []
    segs = {int(m.group(1)) for m in _SEG.finditer(output_md)}
    missing = [i for i in range(8) if i not in segs]
    if missing:
        issues.append("八段骨架缺段：##%s" % ", ".join(str(i) for i in missing))
    allowed = set(plan_.get("allowed_module_ids") or [])
    mentioned = set()
    for tok in _MODULE.findall(output_md):
        mentioned.add(tok)
        if tok not in allowed and tok.split(":", 1)[-1] not in {
            a.split(":", 1)[-1] for a in allowed}:
            issues.append("编造/越界编号：%s（装配允许集外）" % tok)
    for clause in re.split(r"[。！？；\n]+", output_md):
        if _DECISION.search(clause) and not _CITATION.search(clause) \
                and not _MODULE.search(clause):
            issues.append("无引用决策句：%s" % clause.strip()[:40])
    stats = {
        "segments": len(segs),
        "modules_mentioned": len(mentioned),
        "allowed": len(allowed),
    }
    return issues, stats
