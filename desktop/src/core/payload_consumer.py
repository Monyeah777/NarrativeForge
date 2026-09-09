"""45 · payload-consumer 消费核对雏形（只报告不设闸）。

把事件载荷注册表（declared/typed）与 machine_contract 订阅方对应：
consumer_map[event] = [订阅该事件的模块 id]；events 消费统计供未来
「消费时校验」的核对底座。缺订阅方不 FAIL（允许广播/出口事件），只在统计中暴露。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

_ROOT = Path(__file__).resolve().parents[3]


def scan(root: str = ".") -> Tuple[List[str], Dict[str, Any]]:
    r = Path(root)
    reg = json.loads((r / "protocol/event_registry.json").read_text(encoding="utf-8"))
    subs: Dict[str, List[str]] = {}
    from core import conformance_scan as csc
    for doc in csc._module_docs(str(r)):
        txt = Path(doc).read_text(encoding="utf-8")
        parsed = csc._fence_yaml(txt, "machine_contract")
        mc = parsed.get("machine_contract") if isinstance(parsed, dict) else None
        mid = str((mc or {}).get("id") or "")
        ev = (mc or {}).get("events") or {}
        for e in ev.get("subscribe") or []:
            subs.setdefault(str(e), []).append(mid)
    consumers = {}
    declared = 0
    for ev, spec in reg.get("events", {}).items():
        if spec.get("fields"):
            declared += 1
            consumers[ev] = sorted(set(subs.get(ev, [])))
    stats = {"events_declared": declared,
             "events_consumed": sum(1 for v in consumers.values() if v),
             "consumer_map": consumers}
    return [], stats
