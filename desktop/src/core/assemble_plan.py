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

#: 未命中官方预设但足以判定“用户有具体自定义题材”的内容线索
CUSTOM_CUES = [
    "自定义", "权谋", "宫廷", "科幻", "都市", "悬疑", "恐怖",
    "修仙", "机甲", "冒险", "武侠", "末日", "星际", "盗墓", "权斗",
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


def clarify(requirement: str) -> Dict[str, Any]:
    """需求收敛漏斗：信息不足 → 澄清问句；足够 → 直接进 plan。"""
    req = requirement.strip()
    if not req:
        return {"status": "clarify", "requirement": req,
                "questions": ["请描述你要的世界：题材方向（如 西幻生存/校园情感/自定义）？"]}
    p = plan(req)
    if p["matched"] or any(cue in req for cue in CUSTOM_CUES):
        return {"status": "ready", "requirement": req, "plan": p,
                "questions": []}
    return {
        "status": "clarify",
        "requirement": req,
        "questions": [
            "① 题材方向：官方预设（西幻生存/校园情感/技术文档/轻混/通用核心）还是你的自定义题材？",
            "② 玩法主轴：生存/关系/成长/任务/探索……哪个是推进核心？",
            "③ 世界尺度：单个完整版世界，还是要跨预设组合？",
        ],
    }


def dossier(requirement: str, plan_: Dict[str, Any],
            questions: List[str] = (), answers: List[str] = ()) -> str:
    """漏斗产出 → 需求档案（对齐 docs/需求收敛模板.md 八字段回填稿）。"""
    req = requirement.strip()
    status = "澄清中（nf assemble 已抛问句，待回填）" if questions else (
        "custom 用户自定义流" if not plan_.get("matched") else "preset 预设匹配")
    lines = [
        "需求澄清稿",
        "1. 一句话需求：%s" % req,
        "2. 背景与痛点：（待回填——为什么现在做 / 现有哪一环断了）",
        "3. 谁消费（决策人 / 外部方）：（待确认——作者 / agent 用户）",
        "4. 范围边界（做 / 不做）：%s" % status,
        "   领域判定：%s" % (
            "%s/%s" % (plan_.get("package"), plan_.get("pipeline"))
            if plan_.get("matched") else
            "未命中官方预设 → 用户自定义（可借用包：%s）"
            % ("、".join(plan_.get("known_packages") or []) or "—")),
        "   取件模块：%s" % "、".join(plan_.get("fetch_modules") or []),
        "5. 验收标准（可测断言）：nf assemble \"%s\" --check <out.md> 期望 PASS"
        "（八段骨架 / 编号在装配允许集 / 决策句带引用）" % req,
        "6. 风险与未知：关键词识别有界（未命中 ≠ 不适配，需回填确认）；"
        "用户自定义件须先落库登记（M91-M99 / 资产 900+ / 新 Pxx）验收才认；"
        "外部实证按 STRATEGY 封闭期冻结（NF-FIELD-001 素材缺位）",
        "7. 涉及协议 / 文件：agent_组装指令包_v0.2.md；%s 管线件；"
        "装配计划允许集 %d 模块；community/模板制作指令包.md（如需建自定义件）"
        % ("、".join(plan_.get("pipeline_files") or []) or "（待定）",
           len(plan_.get("allowed_module_ids") or [])),
        "8. 素材引用：仓库内完整版样本 / 资产键表；外部素材无则如实声明",
    ]
    if questions:
        lines.append("待澄清（nf assemble 问句）：")
        lines += ["  · %s" % q for q in questions]
    if answers:
        lines.append("澄清回填（--answer，已并入需求与档案）：")
        lines += ["  · %s" % a for a in answers]
    return "\n".join(lines) + "\n"


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
    all_registered = _official_core_ids()
    for mids in packages.values():
        all_registered += mids
    allowed = sorted(set(all_registered))
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
    _EXPL = ("残留", "不命中", "源编号", "未装配", "说明")
    narrative = {0, 1, 2}
    cur_seg = None
    in_code = False
    for line in output_md.splitlines():
        s = line.strip()
        if s.startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        m = _SEG.match(line)
        if m:
            cur_seg = int(m.group(1))
            continue
        for tok in _MODULE.findall(line):
            mentioned.add(tok)
            if tok in allowed or tok.split(":", 1)[-1] in {
                    a.split(":", 1)[-1] for a in allowed}:
                continue
            if any(k in line for k in _EXPL):
                continue
            issues.append("编造/越界编号：%s（全库允许集外，且非残留/不命中说明）" % tok)
        if cur_seg not in narrative or s.startswith(("-", "*", "|")):
            continue
        for clause in re.split(r"[。！？；\n]+", line):
            clause = clause.strip()
            if not clause:
                continue
            if _DECISION.search(clause) and not _CITATION.search(clause) \
                    and not _MODULE.search(clause):
                issues.append("无引用决策句：%s" % clause[:60])
    stats = {
        "segments": len(segs),
        "modules_mentioned": len(mentioned),
        "allowed": len(allowed),
    }
    return issues, stats
