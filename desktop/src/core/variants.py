"""变体/条件装配库（v2.3.0 B2：静态组合之上的装配层变体选择）。

composer.py 头部非目标「不改组合声明结构」（references 协议层冻结，V2 前不扩
schema）——变体/条件因此落在**装配层**：对 base selected 模块集做预定义变换
（增/删模块），产出独立装配集；重叠仲裁 = 变体间模块重叠的声明级报告（不阻断，
消费方自行决定用哪个变体）。

变体定义（调用方声明，如管线 YAML `variants:` 或 CLI 参数）：
    variants = {
        "轻混完整":  {"add": ["校园情感类:M55"], "remove": []},
        "轻混极简":  {"add": [],                "remove": ["轻混类:M92"]},
    }

API：
- apply_variant(base_selected, variant) -> list[str]：单变体变换（full_id 列表，
  增去重、删忽略不存在——幂等）。
- variant_assemblies(base_selected, variants) -> VariantPlan：全变体展开 + 重叠
  仲裁报告（{name, selected, overlap: [...]}）。返回报告不写盘。

边界：不做条件运行时判断（if/分支动态路由留协议 V2/后续）；变体是**静态模板
选择**。消费方 = pipe/nf CLI（`--variant` 选模板后再走 build_assembly）。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from .models import fid_key


@dataclass
class Variant:
    """单个变体展开结果。"""
    name: str
    selected: List[str] = field(default_factory=list)
    overlap: List[str] = field(default_factory=list)   # 与本变体冲突的重叠模块（跨变体仲裁用，单变体恒空）


@dataclass
class VariantPlan:
    """全变体展开 + 重叠仲裁报告。"""
    base: List[str] = field(default_factory=list)
    variants: List[Variant] = field(default_factory=list)

    @property
    def overlap_issues(self) -> List[str]:
        """变体间模块重叠的人类可读报告（声明级警告，不阻断）。"""
        issues: List[str] = []
        names = [v.name for v in self.variants]
        seen: Dict[str, List[str]] = {}   # fid -> [variant names]
        for v in self.variants:
            for fid in v.selected:
                seen.setdefault(fid, []).append(v.name)
        for fid, owners in seen.items():
            if len(owners) > 1:
                issues.append(f"模块 {fid} 被多个变体共同持有: "
                              + ", ".join(owners))
        return issues


def _norm_list(items) -> List[str]:
    return [str(x) for x in (items or [])]


def apply_variant(base_selected: List[str],
                  variant: Dict[str, list]) -> Variant:
    """单变体变换：base + add（去重）− remove（忽略不存在）。幂等。"""
    add = _norm_list(variant.get("add"))
    remove = _norm_list(variant.get("remove"))
    out: List[str] = []
    seen: set = set()
    remove_keys = {fid_key(x) for x in remove}
    for fid in list(base_selected) + add:
        k = fid_key(fid)
        if k in remove_keys or k in seen:
            continue
        out.append(fid)
        seen.add(k)
    return Variant(name=str(variant.get("name", "")), selected=out)


def variant_assemblies(base_selected: List[str],
                       variants: Dict[str, dict]) -> VariantPlan:
    """全变体展开：每变体 = base 变换结果；产出 VariantPlan（含跨变体重叠报告）。

    variants: {variant_name: {"add": [...], "remove": [...]}}——add/remove 为
    full_id 列表（与 pipe/CLI selected 同格式）。
    """
    plan = VariantPlan(base=list(base_selected))
    for name, spec in variants.items():
        spec = dict(spec)
        spec["name"] = name
        plan.variants.append(apply_variant(base_selected, spec))
    return plan
