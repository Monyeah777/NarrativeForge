"""组合运行时调度引擎（v2.0.x-E3：references 跨包引用运行时消费）。

- resolve_combination(store, pipeline)：按 registry protocols references（I5）
  闭包解析可装配集——own（自带模块）+ reference（references 引用的 source 包
  模块，从 community/<pkg>/modules parse 装载正文——只读消费不复制入包，
  I5 单一真相源）+ core 提示。
- build_assembly(store, pipeline, selected, include_references=True)：
  render_ir 前合并——selected(own) + reference 模块 → 完整装配集，让跨包组合
  模块正文运行时真正进装配/导出（当前缺口：references 只到 asset_get 资产寻址）。
- check15 已保证 references 合法（可寻址/闭包）；引擎防御性解析失败入 warnings
  （不静默丢，合规组合不应触发）。
- 非目标：不做跨包内容复制入包（只读）；不改组合声明结构。
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from .models import Module, Pipeline, fid_key
from .storage import Store


@dataclass
class Combination:
    """组合解析结果。"""
    pipeline_id: str = ""
    own_modules: List[Module] = field(default_factory=list)
    reference_modules: List[Module] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


def _repo_root() -> Path:
    """仓库根（desktop/src/core → 3 级上）。"""
    return Path(__file__).resolve().parents[3]


def _protocol_refs(store: Store, pipeline_id: str) -> List[dict]:
    """registry protocols[] 按 id 找 references（I5）。异常返回 []。"""
    try:
        from .registry_loader import load_registry
        reg = load_registry()
        for p in (reg.protocols or []):
            if p.get("id") == pipeline_id or p.get("pipeline") == pipeline_id:
                return list(p.get("references") or [])
    except Exception:
        pass
    return []


def _load_source_module(pkg_name: str, module_ref: str) -> Optional[Module]:
    """从 community/<pkg>/modules/<id>_*.md parse 装载引用模块。"""
    from .parser import parse_module
    root = _repo_root()
    mod_dir = root / "community" / pkg_name / "modules"
    if not mod_dir.is_dir():
        return None
    num = str(module_ref).split(":")[-1]
    for f in sorted(mod_dir.glob("*.md")):
        if f.name.startswith(num + "_") or f.stem == num:
            try:
                return parse_module(f.read_text(encoding="utf-8"))
            except Exception:
                continue
    return None


def resolve_combination(store: Store, pipeline: Pipeline) -> Combination:
    """按管线（协议）references 闭包解析可装配集。

    - own：store 已装模块中管线层序内的（由调用方 selected 决定——此处返回
      结构，own_modules 由 build_assembly 从 selected 填；本函数填管线自带
      层默认相关的已装模块作参考）
    - reference：registry references 引用的 source 模块（parse 装载正文）
    """
    combo = Combination(pipeline_id=pipeline.id)
    for ref in _protocol_refs(store, pipeline.id):
        pkg = ref.get("source_package")
        mid = ref.get("module_id")
        if not pkg or not mid:
            continue
        m = _load_source_module(pkg, mid)
        if m is None:
            combo.warnings.append(
                f"引用模块 {mid}（{pkg}）解析失败——源文件缺失或格式不识别")
            continue
        # 去重：同 full_id 已装载则跳过
        if any(fid_key(m.full_id) == fid_key(x.full_id)
               for x in combo.reference_modules):
            continue
        combo.reference_modules.append(m)
    return combo


def build_assembly(store: Store, pipeline: Pipeline,
                   selected: List[Module],
                   include_references: bool = True) -> List[Module]:
    """render_ir 前合并：selected(own) + references 引用模块 → 完整装配集。

    include_references=False：仅 selected（现行行为，供不需要组合的调用）。
    """
    mods = list(selected)
    if not include_references:
        return mods
    combo = resolve_combination(store, pipeline)
    seen = {fid_key(m.full_id) for m in mods}
    for rm in combo.reference_modules:
        if fid_key(rm.full_id) not in seen:
            mods.append(rm)
            seen.add(fid_key(rm.full_id))
    return mods
