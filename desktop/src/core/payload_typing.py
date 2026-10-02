"""45 #1 · 事件载荷类型收窄工具（证据型提案，不改注册表）。

注册表字段目前全 untyped（无正文显式类型）。为避免编造，本模块只给出
「字段名 → 建议类型」的机械规则（数值语义词 → number；其余保持 untyped），
并产出 narrowing 报告；作者确认后按 protocol/event_registry.json 字段型收窄。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

_ROOT = Path(__file__).resolve().parents[3]
_NUMERIC = ("tick", "day", "minute", "count", "qty", "lv", "from_lv", "to_lv",
            "duration", "delta", "price_delta", "affinity_delta", "round",
            "weight", "strength", "tier", "old_tier", "new_tier", "intensity",
            "quality", "cost", "version")
_LISTISH = ("sections", "changes", "participants", "damage_log", "targets",
            "encounters", "affected_towns", "definitions", "delta", "status")


def propose(root: str = ".") -> Dict[str, Any]:
    r = Path(root)
    data = json.loads((r / "protocol/event_registry.json").read_text(encoding="utf-8"))
    out: Dict[str, Any] = {"status": "proposal", "events": {}}
    for ev, spec in data["events"].items():
        fields = spec.get("fields") or {}
        narrowing = {}
        for name in fields:
            base = name.rstrip("[]")
            if base in _NUMERIC:
                narrowing[name] = "number"
            elif name.endswith("[]") or name in _LISTISH:
                narrowing[name] = "array"
        out["events"][ev] = narrowing
    return out


def scan(root: str = ".") -> Tuple[List[str], Dict[str, Any]]:
    # 缺根/缺协议件时**如实报 issue**，不抛裸 FileNotFoundError（与 `payload_registry.scan`
    # 同一条纪律——极端渗透 F-5 只修了那一个入口，2026-10-01 空根普查发现本入口漏修）。
    if not (Path(root) / "protocol/event_registry.json").is_file():
        return (["缺 protocol/event_registry.json（修复指引：在 NF 仓库根运行本扫描，"
                 "或先补齐该协议件——类型收窄提案要以它为准）"], {})
    return [], {"proposal_events": len(propose(str(Path(root)))["events"]),
                "status": "proposal-only（确认后按 registry 落 typed）"}
