"""AGENTS vs SKILL 语义裁决（v2.1.0 A1：两判据机制化，A 线第三格）。

裁决规则（用户草案机制化）：
  - 复用性判据：内容脱离本仓库后还有意义吗？有 → SKILL；绑死本仓库
    （构建/测试/提交纪律/目录规则等项目约定）→ project_rules。
  - 装载判据：读者需要「常驻知道」还是「按需调用」？前者 → AGENTS
    （project_rules）；后者 → SKILL。

信号优先级（本模块 = 唯一真源，agent_rules_adapter / pipeline /
protocol_wizard.self_check 共用）：
  1) IR.meta['doc_semantics'] 显式声明（"project_rules" / "skill"）；
  2) title / 模块名 项目约定词启发（含 项目/仓库/约定/规则/提交/构建/命令纪律）；
  3) 缺省回退 SKILL（兼容现状：无信号 techdoc 装配走既有 skill 出口）。

出口语义对应（产物×适配矩阵）：
  project_rules → AGENTS.md / CLAUDE.md（agent_rules_adapter，常驻项目约定）
  skill         → SKILL.md（已交付 18 方案）
"""
from __future__ import annotations

import re
from typing import Optional

from .ir import IRDocument

PROJECT_RULES = "project_rules"
SKILL = "skill"

#: project_rules 触发词（title/模块名启发）：绑仓库的项目约定语义
_PROJECT_CONVENTION_RE = re.compile(
    r"项目|仓库|约定|提交|构建命令|测试命令|命令纪律|目录规则|规范纪律|"
    r"构建与提交|开发规则")

#: 能力语义触发词（可复用任务流程，独立于仓库也成立）——用于反向确认 skill
_SKILL_WORDS = re.compile(r"指南|教程|迁移|流程|操作手册|howto|tutorial|guide")


def classify_doc_semantics(ir: IRDocument) -> str:
    """两判据裁决 → PROJECT_RULES 或 SKILL。本模块是唯一真源。

    1) meta 显式声明优先（装配端可精确标注产出语义）；
    2) 无声明 → title/模块名项目约定词启发（复用性判据的正向探测）；
    3) 仍无信号 → SKILL（复用性=脱离仓库仍有意义的能力包，缺省兼容现状）。
    """
    # ① 显式声明
    explicit = ir.meta.get("doc_semantics") if ir.meta else None
    if explicit in (PROJECT_RULES, SKILL):
        return explicit

    # ② 项目约定词启发（正向：title 或模块名含"绑仓库约定"信号）
    haystack = [ir.title, ir.pipeline_name]
    for layer in ir.layers:
        for m in layer.modules:
            haystack.append(m.name)
    haystack.append(" ".join(m.name for l in ir.layers for m in l.modules))
    text = " ".join(h for h in haystack if h)

    if _PROJECT_CONVENTION_RE.search(text):
        # 复用性判据：命中项目约定词 → 内容绑仓库 → project_rules
        return PROJECT_RULES
    # ③ 缺省：无 project 信号 → SKILL（能力语义/无信号）
    return SKILL
