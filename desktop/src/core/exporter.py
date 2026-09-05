"""导出层 exporter（v2.0.0 T2：格式注册表 + CCV3 JSON/PNG 封装，2.0 E1）。

- export(ir, fmt='ccv3', dest_dir) -> ExportResult：经适配器注册表把 IR 导出
  为外部标准格式。CCV3 为第一适配器（默认首发出口）。
- CCV3 双产物：chara.json（chara_card_v3 dict，内嵌 character_book 世界书——
  SillyTavern 卡内嵌书）+ world.json（独立世界书，供 .world/世界书导入）。
- write_png_card：单卡 PNG（QImage tEXt 'chara' 键，base64 JSON）——CCV3 PNG
  分发形态；PySide6 QImage 零新依赖（探针实证写读回 match）。
- 未启用适配器不出厂（范围纪律）：_REGISTRY 只挂已交付适配器。

格式扩展（v2.0.x）：AGENTS/SKILL/MCP 适配器实现后注册进 _REGISTRY，各带
目标格式版本锚点——export() 不改，只加注册表项。
"""
from __future__ import annotations

import base64
import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from .ir import IRDocument
from .ccv3_adapter import map_ir_to_ccv3, world_entries
from .skill_adapter import export_skill
from .agent_rules_adapter import export_agents, export_claude


@dataclass
class ExportResult:
    fmt: str
    files: List[str] = field(default_factory=list)   # 产出文件绝对路径
    warnings: List[str] = field(default_factory=list)


# ------------------------------------------------------------------ 适配器
def _export_ccv3(ir: IRDocument, dest_dir: Path, res: ExportResult) -> None:
    chara = map_ir_to_ccv3(ir)
    world = {
        "name": f"{ir.title} · 世界书",
        "entries": world_entries(ir),
    }
    dest_dir.mkdir(parents=True, exist_ok=True)
    chara_path = dest_dir / "chara.json"
    world_path = dest_dir / "world.json"
    chara_path.write_text(json.dumps(chara, ensure_ascii=False, indent=2),
                          encoding="utf-8")
    world_path.write_text(json.dumps(world, ensure_ascii=False, indent=2),
                          encoding="utf-8")
    res.files.extend([str(chara_path), str(world_path)])
    # 未映射检查（映射不静默丢弃不变量）：IR 叙事层模块应全部进 world
    narrative = [m.full_id for l in ir.layers if l.id not in ("P00", "P80")
                 for m in l.modules]
    mapped = {k for e in world["entries"] for k in (e.get("keys") or [])}
    unmapped = [f for f in narrative if f not in mapped
                and f not in "".join(mapped)]
    if unmapped:
        res.warnings.append("以下叙事模块未入 world 条目（映射缺口）："
                            + "、".join(unmapped))


_REGISTRY = {
    "ccv3": _export_ccv3,
    "skill": export_skill,
    "agents": export_agents,
    "claude": export_claude,
}


# ------------------------------------------------------------------ 入口
def export(ir: IRDocument, fmt: str = "ccv3",
           dest_dir: Optional[str | Path] = None) -> ExportResult:
    """经适配器注册表导出 IR 为外部格式。fmt 未注册 → KeyError。"""
    if fmt not in _REGISTRY:
        raise KeyError(f"未注册的导出格式：{fmt}（已注册：{sorted(_REGISTRY)}）")
    dest = Path(dest_dir) if dest_dir else Path.cwd()
    res = ExportResult(fmt=fmt)
    _REGISTRY[fmt](ir, dest, res)
    return res


def write_png_card(ir: IRDocument, path: Optional[str | Path] = None) -> str:
    """产单卡 PNG（tEXt 'chara' = base64 chara JSON）。返回文件路径。"""
    chara = map_ir_to_ccv3(ir)
    payload = base64.b64encode(
        json.dumps(chara, ensure_ascii=False).encode("utf-8")).decode("ascii")
    from PySide6.QtGui import QImage
    img = QImage(512, 512, QImage.Format.Format_RGB32)
    img.fill(0xFF222233)      # 深色占位底（无卡面素材）
    img.setText("chara", payload)
    dest = Path(path) if path else Path.cwd() / "chara_card.png"
    if not dest.suffix:
        dest = dest.with_suffix(".png")
    if not img.save(str(dest)):
        raise OSError(f"PNG 写入失败：{dest}")
    return str(dest)
