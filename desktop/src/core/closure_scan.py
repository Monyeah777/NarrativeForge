"""44 追加 · 契约事件闭包扫描（元工具·只报告不设闸）。

口径（与 43 元工具定位一致）：只统计 machine_contract 机读声明的订阅/发布闭包
（23 件机读块 + registry 官方订阅）。事件只有文本侧（内容模块正文声明）而无机读侧
的，列为 sub_only/pub_only 孤儿并标注所在模块——它们是内容覆盖面（check16 过渡策略），
**不是元工具缺口**，不 FAIL、不进入验收结论；仅供作者裁决与可复现跟踪。

golden 集成：protocol_golden.collect 收录 closure 统计 → check31 双源一致，
事件闭包结构漂移即生成物过期（红 = 提示重跑）。
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Tuple

def _module_contracts(root: str) -> List[Dict[str, Any]]:
    from core import conformance_scan as csc

    rows = []
    for doc in csc._module_docs(root):
        rel = os.path.relpath(doc, root).replace(os.sep, "/")
        try:
            with open(doc, encoding="utf-8") as fh:
                text = fh.read()
        except Exception:
            continue
        parsed = csc._fence_yaml(text, "machine_contract")
        mc = parsed.get("machine_contract") if isinstance(parsed, dict) else None
        if not isinstance(mc, dict):
            continue
        rows.append({"id": mc.get("id"), "name": mc.get("name"),
                     "source": rel, "contract": mc})
    rows.sort(key=lambda r: (str(r["id"]), str(r["source"])))
    return rows


def scan(root: str = ".") -> Tuple[List[str], Dict[str, Any]]:
    """扫描 machine 事件闭包；issues 恒空（只报告，不设闸）。"""
    rows = _module_contracts(root)
    publishers: Dict[str, List[str]] = {}
    subscribers: Dict[str, List[str]] = {}
    for r in rows:
        ev = (r["contract"].get("events") or {})
        mid = str(r["id"])
        for e in ev.get("publish") or []:
            publishers.setdefault(str(e), []).append(mid)
        for e in ev.get("subscribe") or []:
            subscribers.setdefault(str(e), []).append(mid)
    pub_events = sorted(publishers)
    sub_events = sorted(subscribers)
    linked = sorted(set(pub_events) & set(sub_events))
    sub_only = sorted(set(sub_events) - set(pub_events))
    pub_only = sorted(set(pub_events) - set(sub_events))

    def _side_map(events, table):
        return {e: sorted(set(table.get(e) or [])) for e in events}

    stats: Dict[str, Any] = {
        "modules": len(rows),
        "linked_events": linked,
        "sub_only_events": sub_only,
        "pub_only_events": pub_only,
        "sub_only_by_module": _side_map(sub_only, subscribers),
        "pub_only_by_module": _side_map(pub_only, publishers),
    }
    return [], stats


if __name__ == "__main__":  # pragma: no cover - 调试入口
    import sys

    root = sys.argv[1] if len(sys.argv) > 1 else "."
    issues, stats = scan(root)
    print(json.dumps(stats, ensure_ascii=False, indent=2, sort_keys=True))
