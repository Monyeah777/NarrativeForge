"""模块校验器（指令集 5.2 validate_module）。

必填字段：id, name, layer, inputs, outputs, logic
附加检查：依赖模块是否已安装、挂载层是否在管线允许集内。
返回 list[str] 错误；空列表 = 通过。
"""
from __future__ import annotations

from typing import List, Optional

from .models import Module, Pipeline, LAYER_IDS, fid_key


def validate_module(parsed: Module,
                    installed_ids: Optional[List[str]] = None,
                    pipeline: Optional[Pipeline] = None,
                    ) -> List[str]:
    """校验模块。installed_ids: 已安装模块 full_id 列表；pipeline: 目标管线。"""
    errors: List[str] = []

    # ---- 必填 ----
    if not parsed.id:
        errors.append("缺少必填字段: id")
    if not parsed.name:
        errors.append("缺少必填字段: name")
    if not parsed.layer:
        errors.append("缺少必填字段: layer")
    if not parsed.outputs:
        errors.append("缺少必填字段: outputs（可为空但建议声明输出键）")
    if not parsed.logic:
        errors.append("缺少核心逻辑 (logic)——模块将无法驱动行为")

    # ---- 层位合法性 ----
    if parsed.layer and parsed.layer not in LAYER_IDS:
        errors.append(f"挂载层 {parsed.layer} 不在九层骨架内（应为 P00-P80）")

    # ---- 依赖检查 ----
    installed = set(installed_ids or [])
    for dep in parsed.inputs or []:
        # 依赖可能不带类前缀（仓库内 M22 默认同文件上下文）；宽松匹配
        found = dep in installed
        if not found:
            for iid in installed:
                if iid.endswith(":" + dep) or iid == dep:
                    found = True
                    break
        if not found:
            errors.append(f"依赖模块 {dep} 未安装")

    # ---- 管线层允许集检查 ----
    if pipeline and parsed.layer:
        pl = pipeline.layer(parsed.layer)
        if pl is not None:
            # 允许集元素与模块标识均做类别去『类』归一（情感类:M22 ↔ 情感:M22）
            allowed = {fid_key(a) for a in (pl.allowed_modules or [])}
            if allowed:
                cands = {fid_key(parsed.id), fid_key(parsed.full_id),
                         fid_key(f"{parsed.category}:{parsed.id}")}
                if not (cands & allowed):
                    errors.append(
                        f"模块 {parsed.full_id} 不在管线 {pipeline.id} 的 "
                        f"{parsed.layer} 层允许集内（{sorted(allowed)}）")

    return errors


def check_assembly(selected: List[Module], pipeline: Pipeline) -> List[str]:
    """装配前整体检查：管线各层是否有默认模块缺失/选中模块是否跨层齐全。"""
    issues: List[str] = []
    if not selected:
        issues.append("未选择任何模块")
        return issues
    # 缺核心模块提示
    core_need = {"M00", "M80"}
    have = {m.id for m in selected} | {m.id.split(":")[-1] for m in selected}
    for c in core_need:
        if c not in have:
            issues.append(f"提示：缺少核心模块 {c}（数据基座/输出呈现）")
    # 重复同层模块允许，但提示跨层空缺
    return issues