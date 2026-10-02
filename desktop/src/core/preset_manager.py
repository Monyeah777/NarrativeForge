"""预设管理器（指令集功能F：预设配置 保存/加载/导出/导入/应用）。

预设 = { name, pipeline, modules: [full_id...], asset_pack }
Store 负责落盘；本模块提供 UI 层需要的组装/应用/导入导出语义。
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional

from .models import Preset, Module
from .storage import Store

PRESET_SCHEMA_VERSION = 1


def snapshot_preset(name: str,
                    pipeline_id: str,
                    selected_modules: List[Module],
                    asset_pack_name: str = "") -> Preset:
    """从 UI 勾选状态生成 Preset 对象（未落盘）。"""
    return Preset(
        name=name,
        pipeline=pipeline_id,
        modules=[m.full_id for m in selected_modules if m.enabled],
        asset_pack=asset_pack_name,
    )


def apply_preset(store: Store, preset: Preset) -> dict:
    """把预设应用到会话状态。

    返回 {"pipeline": id, "modules": [Module...], "asset_pack": name}；
    预设里声明但本地缺失的模块 → 记入 warnings。
    """
    modules: List[Module] = []
    warnings: List[str] = []
    for full_id in preset.modules:
        m = store.get_module(full_id)
        if m:
            modules.append(m)
        else:
            # 兼容裸 id（不带类前缀）
            found = None
            for mm in store.list_modules():
                if mm.id == full_id or mm.full_id == full_id:
                    found = mm
                    break
            if found:
                modules.append(found)
            else:
                warnings.append(f"预设引用模块 {full_id} 本地未安装，已跳过")
    return {
        "pipeline": preset.pipeline,
        "modules": modules,
        "asset_pack": preset.asset_pack,
        "warnings": warnings,
    }


# ------------------------- 导入 / 导出（跨机器迁移） -------------------------
def export_preset_json(preset: Preset) -> str:
    """序列化为带版本号的 JSON 文本。"""
    payload = {"schema": PRESET_SCHEMA_VERSION, "preset": preset.to_json()}
    return json.dumps(payload, ensure_ascii=False, indent=2)


def import_preset_json(text: str) -> Optional[Preset]:
    """从 JSON 文本还原 Preset。非法格式/缺核心字段返回 None。"""
    try:
        data = json.loads(text)
    except json.JSONDecodeError:  # JSON 坏件 ⇒ None（调用方据此报「预设不可用」）
        return None
    if isinstance(data, dict) and "preset" in data:
        data = data["preset"]
    if not isinstance(data, dict):
        return None
    # 核心字段校验：预设必须带非空 name 与 pipeline（否则视为非法 JSON 而非兜底默认值）
    if not data.get("name") or not data.get("pipeline"):
        return None
    return Preset.from_json(data)


def import_preset_file(store: Store, path: Path | str) -> Optional[Preset]:
    """读取外部预设文件并安装到本地预设库。"""
    f = Path(path)
    if not f.exists():
        return None
    try:
        text = f.read_text(encoding="utf-8")
    except Exception:  # 件不可读 ⇒ None（调用方据此报「预设不可用」）
        return None
    p = import_preset_json(text)
    if p:
        store.save_preset(p)
    return p


def export_preset_file(preset: Preset, path: Path | str) -> bool:
    """导出预设到外部文件。"""
    try:
        from core import atomic_write          # 交付件：原子写（半截迁移件不留，2026-10-01）
        atomic_write.write_text(path, export_preset_json(preset))
        return True
    except Exception:  # 落盘失败 ⇒ False（调用方据返回值报失败）
        return False
