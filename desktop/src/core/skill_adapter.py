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
    s = re.sub(r"[^\w\u4e00-\u9fff-]+", "-", name).strip("-") or "skill"
    return s.lower()


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
    frontmatter = (
        "---\n"
        f"name: {_slug(ir.title)}\n"
        f"description: {desc}\n"
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
    skill_dir = dest_dir / _slug(ir.title)
    skill_dir.mkdir(parents=True, exist_ok=True)
    skill_path = skill_dir / "SKILL.md"
    skill_path.write_text(_build_skill_md(ir), encoding="utf-8")
    res.files.append(str(skill_path))
