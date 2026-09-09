"""45 · check32 质量纵深汇总扫描（多个新门禁聚合为单一硬门）。

聚合口径（只把已具备、可无歧义机检的硬门纳入）：
- payload_registry：事件载荷注册表 30/30、防死注册、漏登；
- asset_ledger_projection：community 键表机读投影双源一致；
- instruction_step_audit：指令档步骤引用可寻址；
- asset_density + thickness + usage(strict)：空档/不可读 + 低信息档 + 零引用键。

若任一子扫描 FAIL，本扫描 FAIL；动态/外部证据类不入本门（保持不伪造）。
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple


def scan(root: str = ".") -> Tuple[List[str], Dict[str, Any]]:
    from core import asset_density as ad
    from core import asset_ledger_projection as alp
    from core import instruction_step_audit as isa
    from core import payload_consumer as pc
    from core import payload_registry as pr

    issues: List[str] = []
    stats: Dict[str, Any] = {}
    for name, fn in (("payload_registry", pr.scan),
                     ("asset_ledger", alp.verify),
                     ("instruction_audit", isa.scan),
                     ("asset_density", ad.scan),
                     ("asset_thickness", ad.thickness_scan),
                     ("asset_usage_strict", lambda r: ad.usage_scan(r))):
        sub_issues, sub_stats = fn(root)
        if name == "asset_usage_strict":
            if sub_stats.get("zero_usage", 0) > 0:
                sub_issues = ["资产零引用键 %d 个（键消费证明未闭合）"
                              % sub_stats["zero_usage"]]
        for i in sub_issues:
            issues.append("%s: %s" % (name, i))
        stats[name] = sub_stats
    _, consumer_stats = pc.scan(root)
    stats["payload_consumer"] = consumer_stats
    return issues, stats
