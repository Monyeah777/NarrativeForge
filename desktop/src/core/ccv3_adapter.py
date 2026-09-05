"""CCV3 映射层（v2.0.0 T1：IR → chara_card_v3 + world entries）。

映射规则（17_v2.0.0 方案 §B1，立项 A 段成果）：
- NF 装配产物 = **世界规则集**（真实社区包语义实证）→ 主承载 = character_book
  （SillyTavern lorebook 条目），不是伪单角色 persona。
- **引擎锚点排除**：P00（数据结构）/P80（输出生成器）是协议核心层（01 §5 I2），
  非叙事内容 → 不导 world（显式排除，非静默丢弃）。
- 叙事层模块（P10-P70 等）→ 每条 world 条目：keys=[full_id]，content=归一正文。
- 资产（IR.asset_refs）→ 独立条目（I4 数据隔离：素材与规则分条目，可被引用）。
- persona = 主角占位引导（不伪称角色定义）；scenario = 叙事入口/引导语。
- spec 锚点：chara_card_v3 / v3（SillyTavern 兼容稳定核心字段；权威 spec 在线
  抓取受网络限制未复核——字段集保守，真实 SillyTavern 导入时校准）。

CCV3 字段集（SillyTavern 稳定核心，spec v3）：name / description / personality /
scenario / first_mes / mes_example / system_prompt / post_history_instructions /
alternate_greetings / character_book.entries[] / tags / creator /
character_version / spec / spec_version。
"""
from __future__ import annotations

from typing import List

from .ir import IRDocument

# 引擎锚点层（01 §5 I2 核心固定：数据结构/输出呈现，非叙事内容不导出）
_ENGINE_LAYERS = {"P00", "P80"}


def _module_entries(ir: IRDocument) -> List[dict]:
    """叙事层模块 → world 条目（排除 P00/P80 引擎锚点）。"""
    entries: List[dict] = []
    order = 0
    for layer in ir.layers:
        if layer.id in _ENGINE_LAYERS:
            continue
        for m in layer.modules:
            entries.append({
                "name": m.name,
                "keys": [m.full_id, m.name],
                "content": m.content,
                "enabled": True,
                "insertion_order": order,
                "case_sensitive": False,
                "priority": 10,
                "id": order,
                "comment": f"NF 层 {layer.id} · {layer.name}",
            })
            order += 1
    for m in ir.extra_modules:
        if m.layer in _ENGINE_LAYERS:
            continue
        entries.append({
            "name": m.name, "keys": [m.full_id], "content": m.content,
            "enabled": True, "insertion_order": order,
            "case_sensitive": False, "priority": 5, "id": order,
            "comment": "NF 层外模块", })
        order += 1
    return entries


def _asset_entries(ir: IRDocument) -> List[dict]:
    """资产 refs → 独立条目（素材；缺失键不导，已在 IR.asset_missing 明示）。"""
    entries: List[dict] = []
    for key, val in (ir.asset_refs or {}).items():
        if val is None:
            continue
        content = val if isinstance(val, str) else str(val)
        entries.append({
            "name": key, "keys": [key], "content": content,
            "enabled": True, "insertion_order": 1000,
            "case_sensitive": False, "priority": 10,
            "comment": "NF 资产素材", })
    return entries


def world_entries(ir: IRDocument) -> List[dict]:
    """装配 → lorebook 条目列表（规则模块 + 资产）。"""
    return _module_entries(ir) + _asset_entries(ir)


def _scenario_text(ir: IRDocument) -> str:
    """scenario：叙事入口层模块内容或引导语。"""
    for layer in ir.layers:
        if layer.id in _ENGINE_LAYERS:
            continue
        if layer.modules:
            first = layer.modules[0]
            head = first.content[:400].strip()
            if head:
                return (f"{first.name}：{head}\n\n"
                        f"（叙事世界「{ir.title}」已就绪，故事由此展开）")
    return f"叙事世界「{ir.title}」已就绪。你将以主角身份进入，故事由此展开。"


def map_ir_to_ccv3(ir: IRDocument) -> dict:
    """IR → chara_card_v3 dict（CCV3 单卡 + character_book 世界书）。"""
    n_rule = sum(len(l.modules) for l in ir.layers
                 if l.id not in _ENGINE_LAYERS)
    n_asset = len([v for v in (ir.asset_refs or {}).values() if v is not None])
    description = (
        f"{ir.pipeline_name}（{ir.pipeline_id}）装配产物 · {n_rule} 个规则模块"
        f" + {n_asset} 项资产素材。由叙事工坊 2.0 导出层生成。")
    entries = world_entries(ir)
    return {
        "spec": "chara_card_v3",
        "spec_version": "v3",
        "name": ir.title,
        "description": description,
        "personality": "（主角占位）此装配是世界观设定，非单一角色定义——"
                       "主角由你在叙事前端创建/选择，此卡提供世界规则上下文。",
        "scenario": _scenario_text(ir),
        "first_mes": f"你来到了「{ir.title}」。世界规则已加载，故事开始了……",
        "mes_example": "",
        "creator_notes": f"由 NarrativeForge 2.0 导出层生成（{ir.pipeline_id}）",
        "system_prompt": "",
        "post_history_instructions": "",
        "alternate_greetings": [],
        "character_book": {
            "name": f"{ir.title} · 世界书",
            "entries": entries,
        },
        "tags": [ir.pipeline_id],
        "creator": "NarrativeForge",
        "character_version": "2.0.0",
        "extensions": {},
    }
