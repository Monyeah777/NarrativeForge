"""45 · 事件载荷字段注册表（载荷形状化地基）。

- protocol/event_registry.json 用 protocol/event_payload.schema.json 自校验
  （沿用 schema_lint 子集校验器，零第三方）；
- 交叉断言：已登记事件名必须出现在任一 machine_contract 的 publish/subscribe 或
  registry.subscriptions（防死注册/名字漂移）；
- 社区包事件载荷逐批 retro-fit 前，未登记事件不 FAIL（扩展登记渐进）。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

_ROOT = Path(__file__).resolve().parents[3]


def scan(root: str = ".") -> Tuple[List[str], Dict[str, Any]]:
    r = Path(root)
    from core import schema_lint as sl

    issues: List[str] = []
    # 缺根/缺协议件时**如实报 issue**，不抛裸 FileNotFoundError（极端渗透 D4：
    # 其余扫描器在空根下都返回 issue 列表，只有本入口会崩——同一纪律须一致）。
    missing = [rel for rel in ("protocol/event_payload.schema.json",
                               "protocol/event_registry.json")
               if not (r / rel).is_file()]
    if missing:
        return (["缺 %s（修复指引：在 NF 仓库根运行本扫描，或先补齐该协议件）"
                 % "、".join(missing)], {})
    schema = json.loads((r / "protocol/event_payload.schema.json").read_text(encoding="utf-8"))
    registry = json.loads((r / "protocol/event_registry.json").read_text(encoding="utf-8"))
    issues += sl.subset_validate(registry, schema, "event_registry")

    used: set = set()
    from core import conformance_scan as csc
    for doc in csc._module_docs(str(r)):
        txt = Path(doc).read_text(encoding="utf-8")
        parsed = csc._fence_yaml(txt, "machine_contract")
        mc = parsed.get("machine_contract") if isinstance(parsed, dict) else None
        ev = (mc or {}).get("events") or {}
        used.update(ev.get("publish") or [])
        used.update(ev.get("subscribe") or [])
    reg_json = json.loads((r / "desktop/src/core/registry.json").read_text(encoding="utf-8"))
    used.update((reg_json.get("subscriptions") or {}).keys())
    registered = registry.get("events", {})
    dead = sorted(set(registered) - used)
    if dead:
        issues.append("已登记事件无 machine 引用（死注册）：%s" % ", ".join(dead))
    missing = sorted(used - set(registered))
    if missing:
        issues.append("机器事件未登记载荷（漏登）：%s" % ", ".join(missing))
    declared = sum(1 for v in registered.values() if v.get("fields"))
    return issues, {"registered": len(registered), "used": len(used),
                    "declared": declared,
                    "pending": len(registered) - declared}
