"""SKILL.md 出口适配器（v2.0.x 插件：产物×适配矩阵第二行）。

- 矩阵约束（18 方案 / 2.0 基线 §2）：SKILL 只接**指令/协议类装配产物**
  （IR.type == 'techdoc'，如 P90 技术文档/协议规格）——SKILL 是教 agent 干活的
  能力包，不是叙事内容容器。
- narrative IR 请求 skill → 拒绝（0 文件 + warnings 说明：叙事类请用 CCV3/原生 MD），
  语义错配防混机制化。
- 格式锚点（agentskills.io 实锤）：Skill = 目录 + SKILL.md；YAML frontmatter
  name/description 必填；渐进披露 Discovery 载元数据。正文 = 按层序组织的操作
  说明（消费 IR 层模块内容，同 CCV3 共用 IR 真源）。

用法：export(ir, 'skill', dest_dir)（exporter._REGISTRY 已注册）。
"""
from __future__ import annotations

import re
from pathlib import Path

from .ir import IRDocument


def _slug(name: str) -> str:
    """任意串 → 合规 skill name（v2.4.0 A1 核查：对齐 agentskills.io name 约束）。

    规范要求 name 仅小写字母/数字/连字符（a-z 0-9 -）、≤64 字符、不得首尾连字符、
    禁连续 --。中文 title 无法 ASCII 化——故 name 主源用 pipeline_id（ASCII 稳定），
    description 保留中文 title 全文（description 无字符集限制）。name 与目录名
    （export_skill 用同一 _slug 建 skill_dir）必一致，满足「name 匹配父目录」。
    """
    s = re.sub(r"[^a-z0-9-]+", "-", str(name).lower()).strip("-")
    s = re.sub(r"-{2,}", "-", s)          # 禁连续连字符
    s = s[:64].strip("-")                  # ≤64 且不得尾连字符
    return s or "skill"


def _build_skill_md(ir: IRDocument) -> str:
    """techdoc IR → SKILL.md 文本（frontmatter + 层序操作说明）。"""
    body_parts = [f"# {ir.title}", ""]
    n_blocks = 0
    for layer in ir.layers:
        body_parts.append(f"## 层 {layer.id} · {layer.name}")
        for m in layer.modules:
            body_parts.append(f"### {m.full_id} · {m.name}")
            body_parts.append(m.content or "（无正文）")
            n_blocks += 1
    if ir.extra_modules:
        # techdoc 装配的层外模块（如 P90 管线装配 M90——M90 层位=P90 管线 id
        # 非九层，落入 extra）也是技能正文，不得丢弃（不静默丢内容不变式）
        body_parts.append("## 附加规则")
        for m in ir.extra_modules:
            body_parts.append(f"### {m.full_id} · {m.name}")
            body_parts.append(m.content or "（无正文）")
            n_blocks += 1
    desc = (f"{ir.pipeline_name}（{ir.pipeline_id}）生成："
            f"协议/文档操作规格，共 {n_blocks} 个规则块。")
    # name 主源 = pipeline_id（ASCII 稳定，合规）；title 中文保留进 description/body
    skill_name = _slug(ir.pipeline_id or ir.title)
    frontmatter = (
        "---\n"
        f"name: {skill_name}\n"
        f"description: {desc}\n"
        "license: Proprietary. LICENSE.txt has complete terms\n"
        "---\n")
    return frontmatter + "\n\n".join(body_parts)


def export_skill(ir: IRDocument, dest_dir: Path, res) -> None:
    """SKILL 适配器主体（注册进 exporter._REGISTRY['skill']）。"""
    if ir.type != "techdoc":
        res.warnings.append(
            "SKILL 出口仅接受指令/协议类装配（techdoc）——当前是 narrative "
            "叙事类产物，请用 CCV3 / 原生 MD 导出（产物×出口适配矩阵）")
        return
    dest_dir = Path(dest_dir)
    skill_dir = dest_dir / _slug(ir.pipeline_id or ir.title)
    skill_dir.mkdir(parents=True, exist_ok=True)
    skill_path = skill_dir / "SKILL.md"
    skill_path.write_text(_build_skill_md(ir), encoding="utf-8")
    res.files.append(str(skill_path))
