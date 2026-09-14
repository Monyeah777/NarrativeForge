"""全仓事件背书核对（补 check16/26 之外的空白：**社区域包的订阅是否真有人发布**）。

此前 check16 只做「相邻装配 publish ⊆ neighbour subscribe」的**结构**仲裁，check26 只扫
techdoc 链；**没有任何一道门问过**：某个模块订阅的事件，全仓（官方核心 ∪ 社区包）里到底
有没有发布方。L0 → L1 retro-fit 让社区域包的发布/订阅第一次可见，这条空白才暴露出来。

判定分两档（诚实分层，避免把"跨包"当"断链"）：

- **hard（FAIL）**：订阅的事件在全仓**无任何发布方**，且未登记进
  `protocol/external_events.json`（由外部/未实现通道提供的显式挂账）。
- **warn**：发布方在**别的包**（跨包依赖）——不是错，但需要显式可见（references 应能解释）。
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

ALLOWLIST_REL = "protocol/external_events.json"


def _modules(root: str = "."):
    from core import conformance_scan as csc

    for doc in csc._module_docs(root):
        rel = Path(doc).relative_to(root).as_posix()
        text = Path(doc).read_text(encoding="utf-8")
        parsed = csc._fence_yaml(text, "machine_contract")
        mc = parsed.get("machine_contract") if isinstance(parsed, dict) else None
        if isinstance(mc, dict) and mc.get("id"):
            yield rel, mc


def _allowlist(root: str = ".") -> Set[str]:
    p = Path(root) / ALLOWLIST_REL
    if not p.is_file():
        return set()
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except ValueError:
        return set()
    return {str(k) for k in (data.get("events") or {})}


def build(root: str = ".") -> Dict[str, Any]:
    """事件 → 发布方（含所属包）。"""
    publishers: Dict[str, List[Dict[str, str]]] = {}
    subscribers: Dict[str, List[Dict[str, str]]] = {}
    for rel, mc in _modules(root):
        pkg = rel.split("/")[1] if rel.startswith("community/") else "官方核心"
        mid = str(mc.get("id"))
        ev = mc.get("events") or {}
        for e in (ev.get("publish") or []):
            publishers.setdefault(str(e), []).append({"module": mid, "pkg": pkg})
        for e in (ev.get("subscribe") or []):
            subscribers.setdefault(str(e), []).append({"module": mid, "pkg": pkg})
    return {"publishers": publishers, "subscribers": subscribers}


def scan(root: str = ".") -> Tuple[List[str], List[str], Dict[str, Any]]:
    """→ (issues, warns, stats)。"""
    data = build(root)
    allow = _allowlist(root)
    issues: List[str] = []
    warns: List[str] = []
    uncovered: List[str] = []
    cross_pkg: List[str] = []
    for ev, subs in sorted(data["subscribers"].items()):
        pubs = data["publishers"].get(ev) or []
        if not pubs:
            if ev in allow:
                warns.append("事件 %s 无仓内发布方（已挂账为外部通道：%s）" % (ev, ALLOWLIST_REL))
            else:
                uncovered.append(ev)
                issues.append("事件背书缺口：%s 被 %s 订阅，但全仓无发布方"
                              "（修复指引：补发布模块，或登记进 %s 作为外部通道）"
                              % (ev, "、".join(sorted({s["module"] for s in subs})[:3]),
                                 ALLOWLIST_REL))
            continue
        sub_pkgs = {s["pkg"] for s in subs}
        pub_pkgs = {p["pkg"] for p in pubs}
        if sub_pkgs and pub_pkgs and not (sub_pkgs & pub_pkgs):
            cross_pkg.append(ev)
            warns.append("跨包事件：%s 由 %s 发布、被 %s 订阅（references 应能解释）"
                         % (ev, "、".join(sorted(pub_pkgs)), "、".join(sorted(sub_pkgs))))
    stats = {"events": len(set(data["publishers"]) | set(data["subscribers"])),
             "uncovered": uncovered, "cross_pkg": cross_pkg}
    return issues, warns, stats
