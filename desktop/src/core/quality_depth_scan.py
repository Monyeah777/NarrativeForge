"""45 · check32 质量纵深汇总扫描（多个新门禁聚合为单一硬门）。

聚合口径（只把已具备、可无歧义机检的硬门纳入）：
- payload_registry：事件载荷注册表 30/30、防死注册、漏登；
- asset_ledger_projection：community 键表机读投影双源一致；
- instruction_step_audit：指令档步骤引用可寻址；
- asset_density + thickness + usage(strict)：空档/不可读 + 低信息档 + 零引用键。
- world_model：可选确定性抽象状态契约（变量/相位/不变式）语义成立。
- world_slots：M00 数据槽注册表自身结构与类型约束成立。
- concept_graph：概念前置偏序图（资产机读块）健康度——无环 / 无悬空 / 边有溯源 /
  层位合法 / 别名唯一 / 分支完备（判据面收口，见 results/audit/docs_audit-50 §二）。

若任一子扫描 FAIL，本扫描 FAIL；动态/外部证据类不入本门（保持不伪造）。
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple


#: `scan()` 的输入面：**所有子扫描器的面取并集**（语料 + 协议/文档 + 代码 + 判据脚本）。
#: 面很宽，所以缓存只在常驻语料层在位时启用（见 `conformance_scan.memo_pair` 的说明）。
QD_INPUTS = ("03_管线库/**/*", "04_模块库/**/*", "05_资产库/**/*", "community/**/*",
             "library/**/*", "patterns/**/*", "decisions/**/*",
             "protocol/**/*", "docs/**/*", "01_核心协议.md", "02_联动注册表.md",
             "06_Agent执行协议.md", "07_官方核心出厂与社区预设导航.md",
             "verify.sh", "README.md", "README.en.md", "ROUTES.md", "llms.txt",
             "STRATEGY.md", "AGENTS.md",
             "desktop/**/*.py", "scripts/**/*", ".github/scripts/*.py",
             # 2026-09-29 补齐（**陈旧洞**）：下面两条是 `domain_pack.SCAN_INPUTS` 里的面，而并集里一条都没有
             # ⇒ 改它们时聚合缓存会**命中旧值**（实测：未被覆盖 101 件）。并集面是**保守面**——宁可多列，
             # 不许漏列；覆盖性由 `test_quality_depth_scan.CompositeFaceCoverageTest` 逐条守着。
             ".rivet/private_archive/ai_packs/specs/*.json",
             "desktop/src/core/registry.json")


def scan(root: str = ".") -> Tuple[List[str], Dict[str, Any]]:
    """纵深汇总（外层）：一次只读调用内共享语料读（见 `conformance_scan.read_memo`）。

    十几个子扫描器反复读同一批包资产 / 模块文档（实测同一份件被读 9–10 遍）；作用域严格等于
    这一次调用，出口即清——不跨调用复用，故与「新起进程」看到同一份仓库事实。

    2026-09-29 再叠一层**内容键缓存**（输入面见 `QD_INPUTS`，是各子扫描器面的并集；宽面 ⇒
    `require_resident=True`）：改完文件的第一条重命令里，本函数曾是最大的一笔（profile 521 ms）。
    「读盘面 ⊆ 输入面」由 `test_conformance_scan.DerivedResultCacheTest` 的同一张表守着。
    """
    from core import conformance_scan as _csc
    if _csc.resident_active():
        return _csc.memo_pair("quality-depth", QD_INPUTS, _inner, root,
                              require_resident=True,
                              code_modules=("core.quality_depth_scan",))
    return _inner(root)


def _inner(root: str = ".") -> Tuple[List[str], Dict[str, Any]]:
    """真算（含共享语料作用域）。"""
    from core import conformance_scan as _csc
    with _csc.read_memo():
        return _scan_impl(root)


def _scan_impl(root: str = ".") -> Tuple[List[str], Dict[str, Any]]:
    from core import asset_density as ad
    from core import asset_ledger_projection as alp
    from core import concept_graph as cg
    from core import domain_pack as dpk
    from core import instruction_step_audit as isa
    from core import output_forms as of
    from core import pack_combo as pcb
    from core import payload_consumer as pc
    from core import payload_registry as pr
    from core import tool_face as tf
    from core import world_model as wm
    from core import world_slots as ws

    issues: List[str] = []
    stats: Dict[str, Any] = {}
    for name, fn in (("payload_registry", pr.scan),
                     ("asset_ledger", alp.verify),
                     ("instruction_audit", isa.scan),
                     ("concept_graph", cg.scan),
                     ("output_forms", of.scan),
                     ("domain_packs", dpk.scan),
                     ("combos", pcb.scan),
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
    tf_issues, tf_stats = tf.scan(root)
    for i in tf_issues:
        issues.append("tool_face: %s" % i)
    stats["tool_face"] = tf_stats
    wm_issues, wm_stats = wm.scan(root)
    for i in wm_issues:
        issues.append("world_model: %s" % i)
    stats["world_model"] = wm_stats
    ws_issues, ws_stats = ws.scan(root)
    for i in ws_issues:
        issues.append("world_slots: %s" % i)
    stats["world_slots"] = ws_stats
    _, consumer_stats = pc.scan(root)
    stats["payload_consumer"] = consumer_stats
    return issues, stats
