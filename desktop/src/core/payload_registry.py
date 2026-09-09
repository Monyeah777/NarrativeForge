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
    dead = sorted(set(registry.get("events", {})) - set(used))
    if dead:
        issues.append("已登记事件无 machine 引用（死注册）：%s" % ", ".join(dead))
    return issues, {"registered": len(registry.get("events", {})), "used": len(used)}
