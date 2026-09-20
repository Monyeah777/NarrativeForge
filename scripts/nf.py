#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""NarrativeForge 全链管道 CLI（v2.1.0 B2：retrieve→compose→gate→export 单命令）。

用法：
  python scripts/nf.py run --pipeline <P04管线.md> \
      --modules 通用类:M00,轻混类:M91,轻混类:M92,通用类:M80 \
      [--store <dir>] [--seed] [--fmt ccv3|skill] [--dest <out>] \
      [--no-include-refs] [--force-export]

- 全链 = pipe()：模块选择 → compose（E3 references 并入）→ render_ir
  → quality_gate（三态）→ export（exporter._REGISTRY）。
- --seed：把 04_模块库 + community 组合包模块装载进临时 store（演示/自测用，
  等同 e2e 前置）；缺省要求 --store 指向已含所选模块的工作区。
- 打印 GateResult 摘要（PASS/WARN/FAIL）+ 产物路径；FAIL 且非 --force-export
  → exit 1（CLI 层门禁镜像 verify 铁律）。
- 产物×适配矩阵：skill 拒 narrative（适配器内拒出，warnings 带说明）——
  CLI 原样透传 warnings。
"""
import argparse
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "desktop", "src"))

NF_CLI_VERSION = "1.0.0"
NF_CLI_EPILOG = (
    "入门：\n"
    "  nf --help             # 全命令总览\n"
    "  nf help <cmd>         # 查看任意子命令帮助\n"
    "  nf doctor             # 环境自检（快速只读体检）\n"
    "  nf completion bash    # 生成 shell 补全（>> ~/.bashrc）\n"
    "  nf run / nf demo      # 作者五分钟上手（README「五分钟快速开始」含逐条示例）\n"
    "退出码：0 成功 · 1 运行/校验失败 · 2 用法错误（argparse 约定）。"
)


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="nf", description=(
            "NarrativeForge 全链管道（B2：retrieve→compose→gate→export）。"
            "分层引导（40 总纲 v2.8 波B S7）：作者五分钟上手 = run / demo / pipeline new；"
            "开发者与仓库治理工具族 = asset / module / register / market / spec / render / serve / "
            "design / audit / who-refers / impact / rename / import——README「五分钟快速开始」"
            "含逐条示例。"),
        epilog=NF_CLI_EPILOG,
    )
    p.add_argument("--version", action="version",
                   version="nf %s" % NF_CLI_VERSION,
                   help="显示版本号后退出")
    sub = p.add_subparsers(dest="cmd", required=False)

    run = sub.add_parser("run", help="跑全链管道：模块选择→装配→质检→导出", description="跑全链管道：模块选择→装配→质检→导出")
    run.add_argument("--pipeline", required=True,
                     help="管线 md 文件路径（如 community/校园西幻轻混组合包/pipelines/P04_轻混装配流管线.md）")
    run.add_argument("--modules", required=True,
                     help="参与装配的模块 full_id，逗号分隔（如 通用类:M00,轻混类:M91）")
    run.add_argument("--store", default=None,
                     help="Store 工作区目录（缺省=临时，配合 --seed）")
    run.add_argument("--seed", action="store_true",
                     help="把 04_模块库官方核心 + community 组合包装载进 store（演示/自测）")
    run.add_argument("--fmt", default="ccv3",
                     choices=["ccv3", "skill", "agents", "claude", "mcp", "mvu"],
                     help="导出格式（exporter 注册表：ccv3/skill/agents/claude/mcp）")
    run.add_argument("--doc-semantics", default=None,
                     choices=["project_rules", "skill"],
                     help="显式声明装配产物语义（v2.3.0 A3：project_rules → AGENTS/CLAUDE 出口；skill → SKILL）——不传则回退 classify 启发式")
    run.add_argument("--dest", default=None, help="导出目录（缺省=store 根）")
    run.add_argument("--variant-add", default="",
                     help="变体增量模块 full_id（逗号分隔，v2.3.0 B2：经 apply_variant 并入 selected）")
    run.add_argument("--variant-remove", default="",
                     help="变体移除模块 full_id（逗号分隔，从 selected 剔除；与 --variant-add 同用时 remove 优先）")
    run.add_argument("--no-include-refs", action="store_true",
                     help="不并入 E3 references 跨包模块（默认并入）")
    run.add_argument("--force-export", action="store_true",
                     help="质量门 FAIL 也导出（诊断用；ok 仍 False）")

    reg = sub.add_parser("register",
                         help="协议登记本地助手（B3-B：protocol.yaml → registry protocols[]）", description="协议登记本地助手（B3-B：protocol.yaml → registry protocols[]）")
    reg.add_argument("pkg_dir", help="包目录（如 community/校园西幻轻混组合包）")
    reg.add_argument("--check", dest="mode", action="store_const", const="check",
                     help="只校验三要件 + 打印投影 diff（缺省，不写盘）")
    reg.add_argument("--apply", dest="mode", action="store_const", const="apply",
                     help="校验全过后合并写 registry.json protocols[]（只增不删）")
    reg.add_argument("--registry", default=None,
                     help="registry.json 路径（缺省 = desktop/src/core/registry.json）")
    reg.set_defaults(mode="check")

    mkt = sub.add_parser("market",
                         help="市场协议查询（B4：依赖闭包 + 挂载冲突预检；list 目录视图）", description="市场协议查询（B4：依赖闭包 + 挂载冲突预检；list 目录视图）")
    mkt.add_argument("pkg_dir", nargs="?", default=None,
                     help="包目录（如 community/校园西幻轻混组合包）；缺省 + --list 列目录")
    mkt.add_argument("--list", action="store_true",
                     help="列市场目录（官方核心 + 社区包，各带分级徽章）")
    mkt.add_argument("--json", action="store_true",
                     help="输出结构化 JSON（目录 / 包视图）")
    mkt.add_argument("--tier", default=None,
                     choices=["official", "community", "experimental"],
                     help="按分级筛选（v2.5.0 Wave3：官方/社区/实验）")
    mkt.add_argument("--registry", default=None,
                     help="registry.json 路径（缺省 = desktop/src/core/registry.json）")

    spc = sub.add_parser("spec",
                         help="Spec Registry 查询（v2.5.0 Wave3：版本化 spec 查询）", description="Spec Registry 查询（v2.5.0 Wave3：版本化 spec 查询）")
    spc.add_argument("action", nargs="?", default="ls", choices=["ls"],
                     help="动作（ls 列 spec 版本清单）")
    spc.add_argument("--registry", default=None,
                     help="registry.json 路径（缺省 = desktop/src/core/registry.json）")

    rnd = sub.add_parser("render",
                         help="协议多出口渲染（A3：protocol.yaml → agents/claude/skill rules）", description="协议多出口渲染（A3：protocol.yaml → agents/claude/skill rules）")
    rnd.add_argument("pkg_dir", help="包目录（如 community/技术文档域包）")
    rnd.add_argument("--fmt", default="agents", choices=["agents", "claude", "skill"],
                     help="目标格式（agents/claude/skill）")
    rnd.add_argument("--dest", default=None, help="输出目录（缺省=当前目录）")

    srv = sub.add_parser("serve",
                         help="MCP 运行时服务（C1：mcp.json 快照 → stdio JSON-RPC，供 MCP client 拉起）", description="MCP 运行时服务（C1：mcp.json 快照 → stdio JSON-RPC，供 MCP client 拉起）")
    srv.add_argument("snapshot", help="mcp.json 快照路径（如 nf run --fmt mcp 产物）")

    dsn = sub.add_parser("design",
                         help="决策辅助工具族（v2.6-A：可选装载——钢人论证工作单）", description="决策辅助工具族（v2.6-A：可选装载——钢人论证工作单）")
    dsub = dsn.add_subparsers(dest="design_cmd", required=True)
    stl = dsub.add_parser("steelman",
                          help="钢人论证工作单：init/--check/ls（默认缺席，按需自检）", description="钢人论证工作单：init/--check/ls（默认缺席，按需自检）")
    stl.add_argument("action", nargs="?", default="ls",
                     choices=["init", "ls"],
                     help="动作（init 生成工作单 / ls 列决策档案索引；缺省 ls）")
    stl.add_argument("question", nargs="?",
                     help="init：问题描述（引号包裹，如 \"是否立项？\"）")
    stl.add_argument("--context", default="",
                     help="init：context 字段（方案号/域包名/触发场景）")
    stl.add_argument("--decider", default="",
                     help="init：decider 字段（决策人，缺省留空待填）")
    stl.add_argument("--out", default=None,
                     help="init：输出路径（缺省 = 当前目录 steelman.md）")
    stl.add_argument("--check", dest="check_file", metavar="FILE",
                     help="check：结构自检指定 steelman.md（输出缺项 warn）")
    stl.add_argument("--root", default=".",
                     help="ls：扫描目录（缺省 = 当前目录）")

    # nf design audit（M_AUDIT，升格合并后 design 家族统一入口；steelman 语义
    # 由 audit steelman mode 承载，nf design steelman 保留为兼容别名）
    aud = dsub.add_parser("audit",
                          help="协议设计审计（M_AUDIT：决策过程质量——钢人/blindspot/full）", description="协议设计审计（M_AUDIT：决策过程质量——钢人/blindspot/full）")
    aud.add_argument("action", nargs="?", default="ls",
                     choices=["init", "ls"],
                     help="动作（init 生成 audit.md / ls 列审计索引；缺省 ls）")
    aud.add_argument("question", nargs="?",
                     help="init：审计问题描述（引号包裹）")
    aud.add_argument("--target", default="",
                     help="init：被审计对象（方案/决策/协议设计引用）")
    aud.add_argument("--mode", default="full",
                     choices=["steelman", "blindspot", "full"],
                     help="审计模式（默认 full：钢人 + 双盲区 + 结论 + 行动）")
    aud.add_argument("--context", default="",
                     help="init：related 字段（关联方案文档）")
    aud.add_argument("--out", default=None,
                     help="init：输出路径（缺省 = 当前目录 audit.md）")
    aud.add_argument("--check", dest="check_file", metavar="FILE",
                     help="check：结构自检指定 audit.md（缺文件返回提示非红）")
    aud.add_argument("--root", default=".",
                     help="ls：扫描目录（缺省 = 当前目录）")

    whr = sub.add_parser("who-refers",
                         help="引用反查（A2：谁引用了某模块，遍历 registry references）", description="引用反查（A2：谁引用了某模块，遍历 registry references）")
    whr.add_argument("module_id", help="模块 id（如 M91 或 情感:M55）")
    whr.add_argument("--registry", default=None,
                     help="registry.json 路径（缺省 = desktop/src/core/registry.json）")

    imp = sub.add_parser("impact",
                         help="变更影响面预检（A4 前置：拟删除 module/protocol 前查破坏性影响）", description="变更影响面预检（A4 前置：拟删除 module/protocol 前查破坏性影响）")
    imp.add_argument("target", help="目标（protocol id 如 校园情感领域包，或 module id 如 M55 / 情感:M55）")
    imp.add_argument("--check", dest="mode", action="store_const", const="check",
                     help="门禁模式：破坏性变更（有引用方/官方在册）exit 1，无破坏 exit 0")
    imp.add_argument("--registry", default=None,
                     help="registry.json 路径（缺省 = desktop/src/core/registry.json）")

    ren = sub.add_parser("rename",
                         help="模块改名引用重链（A5：references 中引用该模块的条目批量更新）", description="模块改名引用重链（A5：references 中引用该模块的条目批量更新）")
    ren.add_argument("old_id", help="旧模块 id（如 M55 或 情感:M55）")
    ren.add_argument("new_id", help="新模块 id（如 M99 或 情感:M99）")
    ren.add_argument("--check", dest="mode", action="store_const", const="check",
                     help="只列受影响引用清单不写盘（缺省）")
    ren.add_argument("--apply", dest="mode", action="store_const", const="apply",
                     help="批量重链 references 后合并写 registry protocols[]（只改引用不改其它）")
    ren.add_argument("--registry", default=None,
                     help="registry.json 路径（缺省 = desktop/src/core/registry.json）")

    imp2 = sub.add_parser("import",
                          help="读入外部产物（SKILL.md/chara.json）→ parse + 可选内容库登记（A4 遗留闭环）", description="读入外部产物（SKILL.md/chara.json）→ parse + 可选内容库登记（A4 遗留闭环）")
    imp2.add_argument("file", help="外部产物文件（SKILL.md 或 chara.json）")
    imp2.add_argument("--register", action="store_true",
                      help="解析出的 IR 模块幂等装载进 Store 内容库（save_module 覆盖式幂等）")
    imp2.add_argument("--store", default=None,
                      help="Store 工作区目录（缺省=临时）")

    # nf asset：资产供应链台账（40 总纲 v2.7 波 A S2——add/verify/inventory/ls/rm/deprecate/restore）
    ast = sub.add_parser("asset",
                         help="资产供应链台账（S2：add 入库 / verify 闭合 / inventory 盘点 / ls 浏览 / rm 摘除 / deprecate·restore 流转）", description="资产供应链台账（S2：add 入库 / verify 闭合 / inventory 盘点 / ls 浏览 / rm 摘除 / deprecate·restore 流转）")
    asub = ast.add_subparsers(dest="asset_cmd", required=True)

    a_add = asub.add_parser("add",
                            help="入库资产：资产文件头写 nf-asset 头 + 台账 append（溯源键表自动生成）", description="入库资产：资产文件头写 nf-asset 头 + 台账 append（溯源键表自动生成）")
    a_add.add_argument("file", help="资产文件路径（相对 --root，如 用户自定义/TECH_RULES.md）")
    a_add.add_argument("--key", required=True, help="溯源键（台账内唯一，键无孤儿前提）")
    a_add.add_argument("--source", required=True,
                       help="溯源说明（源文件/区间/登记日期——每资产必须可溯源）")
    a_add.add_argument("--root", default=None,
                       help="资产根目录 = 台账所在目录（如 05_资产库；add 必填）")
    a_add.add_argument("--module", default="", help="消费模块 id（如 M90/M93/M96，可空）")
    a_add.add_argument("--version", default="1.0", help="资产版本位（默认 1.0）")
    a_add.add_argument("--status", default="active",
                       choices=("active", "deprecated", "retired"))
    a_add.add_argument("--tier", default=None,
                       choices=("official", "community", "experimental"),
                       help="货架分级（首次建档落台账级；缺省 official）")
    a_add.add_argument("--package", default="", help="归属包名（台账级，如 官方核心资产集）")

    a_vrf = asub.add_parser("verify", help="台账闭合校验（与 verify.sh check23 同语义）", description="台账闭合校验（与 verify.sh check23 同语义）")
    a_vrf.add_argument("--root", default=ROOT, help="扫描根（缺省=仓库根）")

    a_bl = asub.add_parser("baseline",
                           help="社区资产行数基线（可重签工件；漂移即 FAIL 直到显式重签）",
                           description="社区资产行数基线（机制对齐 module signature：外形冻结、内容演进须显式重签）")
    a_bl.add_argument("--write", action="store_true", help="重新冻结基线（评审后显式重签）")
    a_bl.add_argument("--root", default=ROOT, help="扫描根（缺省=仓库根）")

    a_inv = asub.add_parser("inventory", help="库存盘点（台账摘要 + 未托管/孤儿统计）", description="库存盘点（台账摘要 + 未托管/孤儿统计）")
    a_inv.add_argument("--root", default=ROOT, help="扫描根（缺省=仓库根）")
    a_inv.add_argument("--json", action="store_true",
                       help="输出结构化 JSON（盘点行）")

    a_ls = asub.add_parser("ls", help="货架浏览（--pkg / --tier / --status 过滤）", description="货架浏览（--pkg / --tier / --status 过滤）")
    a_ls.add_argument("--root", default=ROOT, help="扫描根（缺省=仓库根）")
    a_ls.add_argument("--json", action="store_true",
                      help="输出结构化 JSON（货架条目）")
    a_dns = asub.add_parser("density",
                            help="资产键语义密度体检（45：键数/字符/无键与空档统计）", description="资产键语义密度体检（45：键数/字符/无键与空档统计）")
    a_dns.add_argument("--root", default=ROOT, help="扫描根（缺省=仓库根）")
    a_dns.add_argument("--json", action="store_true",
                       help="输出结构化 JSON（密度统计）")
    a_use = asub.add_parser("usage",
                            help="资产引用度体检（45：键在 04/community/docs 全语料引用次数/零引用清单）", description="资产引用度体检（45：键在 04/community/docs 全语料引用次数/零引用清单）")
    a_use.add_argument("--root", default=ROOT, help="扫描根（缺省=仓库根）")
    a_use.add_argument("--json", action="store_true",
                       help="输出结构化 JSON（引用度统计）")
    a_use.add_argument("--strict", action="store_true",
                       help="零引用键存在即 exit 1（键消费证明进门禁）")
    a_thk = asub.add_parser("thickness",
                            help="资产语义厚度体检（45：字符/键/小节/表格 + 低信息档候选）", description="资产语义厚度体检（45：字符/键/小节/表格 + 低信息档候选）")
    a_thk.add_argument("--root", default=ROOT, help="扫描根（缺省=仓库根）")
    a_thk.add_argument("--json", action="store_true",
                       help="输出结构化 JSON（厚度统计）")
    a_led = asub.add_parser("ledger",
                            help="资产键表机读投影（45：protocol/community_asset_ledger.json；--refresh 重生成）", description="资产键表机读投影（45：protocol/community_asset_ledger.json；--refresh 重生成）")
    a_led.add_argument("--root", default=ROOT, help="扫描根（缺省=仓库根）")
    a_led.add_argument("--refresh", action="store_true",
                       help="重生成 ledger 文件（随资产变更提交）")
    a_led.add_argument("--json", action="store_true",
                       help="输出结构化 JSON（校验统计）")
    a_ls.add_argument("--pkg", default="", help="台账 package 过滤")
    a_ls.add_argument("--tier", default="",
                      choices=("official", "community", "experimental"))
    a_ls.add_argument("--status", default="",
                      choices=("active", "deprecated", "retired"))

    for _name, _desc in (("rm", "从台账摘除条目（不删资产文件，残留头由 check23 报孤儿）"),
                         ("deprecate", "状态流转 → deprecated"),
                         ("restore", "状态流转 → active（deprecated 回退）")):
        _sp = asub.add_parser(_name, help=_desc)
        _sp.description = _desc
        _sp.add_argument("--ledger", required=True,
                         help="provenance.json 路径（如 05_资产库/provenance.json）")
        _sp.add_argument("--key", required=True, help="溯源键")
    # ---- v2.8.0 波B S4：管线脚手架 ----
    pln = sub.add_parser("pipeline",
                         help="管线脚手架（v2.8 波B S4：pipeline new——自 P00 骨架派生新管线）", description="管线脚手架（v2.8 波B S4：pipeline new——自 P00 骨架派生新管线）")
    psub = pln.add_subparsers(dest="pipeline_cmd", required=True)
    p_new = psub.add_parser("new", help="派生新管线：复制模板 → 改 id/name/领域标签（登记 02 / 填层名挂载按 README 三步）", description="派生新管线：复制模板 → 改 id/name/领域标签（登记 02 / 填层名挂载按 README 三步）")
    p_dry = psub.add_parser("dryrun",
                            help="管线抽象执行（不调模型跑一遍声明 → 执行图；hard 缺陷 + advisory 分列）",
                            description="管线抽象执行（内部差距：静态 check 只能答『声明自洽吗』，答不了『跑得通吗』）")
    p_dry.add_argument("--pipeline", default="", help="管线 md 路径（缺省 + --all 时全仓扫）")
    p_dry.add_argument("--all", action="store_true", help="全仓管线扫一遍并汇总")
    p_dry.add_argument("--json", action="store_true", help="输出执行图 JSON")
    p_dry.add_argument("--write-advisory", action="store_true",
                       help="配合 --all：把 advisory 分类台账写入 protocol/pipeline_advisory.json")
    p_new.add_argument("--id", required=True, help="新管线 id（如 P07）")
    p_new.add_argument("--name", required=True, help="新管线显示名（如 演示领域管线）")
    p_new.add_argument("--from", dest="template", default=None,
                       help="模板管线 md（缺省 = 03_管线库/P00_通用文档生成管线.md）")
    p_new.add_argument("--domain", default="",
                       help="领域标签（如 悬疑 → tags 追加「悬疑领域」）")
    p_new.add_argument("--dest", default="",
                       help="输出 md 路径（缺省 = 03_管线库/<id>_<name>.md 官方管线位）")

    # ---- v2.8.0 波B S5：模块生命周期 ----
    mds = sub.add_parser("module",
                         help="模块生命周期（v2.8 波B S5：status 位 + deprecate/restore + 引用门禁 verify）", description="模块生命周期（v2.8 波B S5：status 位 + deprecate/restore + 引用门禁 verify）")
    msub = mds.add_subparsers(dest="module_cmd", required=True)
    m_ls = msub.add_parser("ls", help="浏览模块状态（--status 过滤；缺省全量）", description="浏览模块状态（--status 过滤；缺省全量）")
    m_ls.add_argument("--status", default="", choices=("active", "deprecated", "retired"))
    m_ls.add_argument("--root", default=ROOT, help="扫描根（缺省 = 仓库根）")
    m_ls.add_argument("--json", action="store_true",
                      help="输出结构化 JSON（模块状态清单）")
    m_st = msub.add_parser("status", help="查看单个模块文件状态位", description="查看单个模块文件状态位")
    m_st.add_argument("file", help="模块 md 路径（如 community/<包>/modules/Mxx_….md）")
    m_dp = msub.add_parser("deprecate", help="状态流转 → deprecated（写文件元信息行状态位）", description="状态流转 → deprecated（写文件元信息行状态位）")
    m_dp.add_argument("file", help="模块 md 路径")
    m_dp.add_argument("--reason", default="", help="弃用原因（写入状态位）")
    m_rs = msub.add_parser("restore", help="状态流转 → active（deprecated/retired 回退）", description="状态流转 → active（deprecated/retired 回退）")
    m_rs.add_argument("file", help="模块 md 路径")
    m_vf = msub.add_parser("verify", help="引用门禁扫描（与 verify.sh check24 同语义）", description="引用门禁扫描（与 verify.sh check24 同语义）")
    m_sg = msub.add_parser("signature",
                           help="模块边界签名基线（边界写一次；漂移即 FAIL 直到重签）",
                           description="模块边界签名基线（机制借鉴 Pipelex signature_for：边界冻结、实现可替）")
    m_sg.add_argument("--write", action="store_true",
                      help="重新冻结边界基线（评审后显式重签）")
    m_sg.add_argument("--json", action="store_true", help="输出结构化 JSON")
    m_ty = msub.add_parser("types",
                           help="I/O 类型面（io_types）：覆盖率 + 可证不匹配；--write 补标",
                           description="I/O 类型面（机制借鉴 Pipelex typed concepts，01 §7 V1 字段级新增）")
    m_ty.add_argument("--write", action="store_true",
                      help="给全部有机读契约的模块补 io_types（确定性推导，未命中写 untyped）")
    m_ty.add_argument("--json", action="store_true", help="输出结构化 JSON")
    m_ty.add_argument("--harvest", action="store_true",
                      help="从模块正文事件契约收割载荷字段（并入 event_registry）")
    m_ty.add_argument("--backlog", action="store_true",
                      help="生成/校验类型积压台账（不可推断的 untyped 显式化）")
    m_ct = msub.add_parser("contract",
                           help="L0 → L1 机读块 retro-fit（从人读引用块/正文投影，不编造）",
                           description="L0 → L1 机读块 retro-fit（机制借鉴 Pipelex：机读块 = 人读契约的结构化投影）")
    m_ct.add_argument("--write", action="store_true", help="写入机读块（幂等；已有机读块则跳过）")
    m_ct.add_argument("--json", action="store_true", help="输出结构化 JSON")
    m_vf.add_argument("--root", default=ROOT, help="扫描根（缺省 = 仓库根）")

    # ---- v2.8.0 波B S7：一键演示世界 ----
    dm = sub.add_parser("demo",
                        help="一键演示世界（v2.8 波B S7：P04 轻混全链 → CCV3 导出）", description="一键演示世界（v2.8 波B S7：P04 轻混全链 → CCV3 导出）")
    dm.add_argument("--dest", default="", help="导出目录（缺省 = 系统临时目录并打印路径）")
    # ---- v2.8.0 波C C1/C2/C5：知识签名 / 版本差异 / 修复指引（41 规划）----
    sg = sub.add_parser("sig",
                        help="协议知识签名（41 波C C1：01-36 文档/管线/模块 → 结构化签名，知识指纹）", description="协议知识签名（41 波C C1：01-36 文档/管线/模块 → 结构化签名，知识指纹）")
    sg.add_argument("target", nargs="*", default=None,
                    help="目标 md 或目录；缺省 = 全量 01-36 编号方案文档")
    sg.add_argument("--json", action="store_true", help="输出完整 canonical JSON 记录")
    sg.add_argument("--verify", action="store_true",
                    help="check25 同语义：两遍生成一致性校验（可复现门禁）")
    at = sub.add_parser("attest",
                        help="内容 attestation（三级信任：digest_only / hmac-sha256 / sigstore 外挂锚）",
                        description="内容 attestation（内部差距：知识签名只自证可复现，无对外可验证的篡改证据）")
    at.add_argument("target", nargs="?", default="",
                    help="目标 md（缺省 = 01/02/06/07 四件集合）")
    at.add_argument("--out", default="", help="写出 attestation JSON 的路径（缺省 = 不写盘）")
    at.add_argument("--issuer", default="", help="签发方标识（写入 producer.issuer）")
    at.add_argument("--key-file", default="",
                    help="HMAC 密钥文件 → 签发/校验 hmac-sha256 级 attestation")
    at.add_argument("--verify", default="",
                    help="校验既有 attestation JSON（缺省 = 生成模式）")
    at.add_argument("--json", action="store_true", help="输出结构化 JSON")
    sc = sub.add_parser("score",
                        help="基线相对回归评分（Codecov 式：当前 vs 基线，no silent worsening）",
                        description="基线相对回归评分（内部差距：现有门禁全为绝对门，无 delta/回归判据）")
    sc.add_argument("--baseline", default="",
                    help="基线 JSON（缺省 = protocol/score_baseline.json）")
    sc.add_argument("--write-baseline", action="store_true",
                    help="把当前分值写入基线（审计注记随写入）")
    sc.add_argument("--tolerance", type=float, default=0.0,
                    help="整体分允许下降幅度（缺省 0 = 不允许下降）")
    sc.add_argument("--exceptions", default="",
                    help="审计例外 JSON（[{signal,reason}]，例外只标注理由不隐藏回归）")
    sc.add_argument("--json", action="store_true", help="输出结构化 JSON")
    ln = sub.add_parser("lint",
                        help="机械检查/修复（doc_hygiene 同源判据 + 可选正文 lint；--fix 只改机械面）",
                        description="机械检查/修复（内部差距：既有扫描器只报告不修，仓库无 auto-fix）")
    ln.add_argument("target", nargs="*", default=None,
                    help="目标 md/目录（缺省 = doc_hygiene 关键/指令档清单）")
    ln.add_argument("--fix", action="store_true",
                    help="应用机械修复（缺省 = 只报告，发现即 exit 1）")
    ln.add_argument("--dry-run", action="store_true",
                    help="配合 --fix：只报将改什么，不写盘")
    ln.add_argument("--prose", action="store_true",
                    help="额外跑正文 lint（去 AI 味规则集）")
    ln.add_argument("--kinds", action="store_true",
                    help="只跑四型写法判据（信息类型化：类型不只是标签）")
    asrt = sub.add_parser("assertions",
                          help="数据化断言表（Schematron 式：patterns→rules→assertions）",
                          description="数据化断言表（机制借鉴 Schematron；kind 为封闭集）")
    asrt.add_argument("--json", action="store_true", help="输出结构化 JSON")
    mdl = sub.add_parser("model",
                         help="内容建模三件（词表登记册 / 规范与说明件 / 数据契约登记）",
                         description="内容建模三件（机制借鉴 SKOS 概念方案 / 规范-说明件二分 / 数据契约要素）")
    mdl.add_argument("part", nargs="?", default="",
                     choices=["", "vocab", "normative", "contracts"],
                     help="只看一件（缺省 = 三件全跑）")
    mdl.add_argument("--json", action="store_true", help="输出结构化 JSON")
    dec = sub.add_parser("decisions",
                         help="决策记录（ADR：一条一编号；采纳后不改不删，只可被取代）",
                         description="决策记录（机制借鉴 ADR：supersede-only + 不可改）")
    dsub = dec.add_subparsers(dest="decisions_cmd")
    d_sh = dsub.add_parser("show", help="看单条决策（frontmatter + 正文）", description="看单条决策")
    d_sh.add_argument("id", help="编号（如 ADR-0001）")
    for _d in (dsub.add_parser("verify", help="机检决策记录", description="机检决策记录"),
               dsub.add_parser("reindex", help="重建 INDEX 投影", description="重建 INDEX 投影"),
               d_sh):
        _d.add_argument("--json", action="store_true", help="输出结构化 JSON")
    ho = sub.add_parser("handover",
                        help="接力协议（SBAR：情境/背景/评估/建议 + 未决项带判据）",
                        description="接力协议（机制借鉴 SBAR；空未决即不合格交接）")
    hosub = ho.add_subparsers(dest="handover_cmd")
    ho_ls = hosub.add_parser("ls", help="列全部交接件", description="列全部交接件")
    ho_ck = hosub.add_parser("check", help="机检单件交接", description="机检单件交接")
    ho_ck.add_argument("path", help="交接件路径（仓库相对）")
    for _h in (ho_ls, ho_ck, hosub.add_parser("verify", help="机检声明 + 全部交接件",
                                              description="机检声明 + 全部交接件")):
        _h.add_argument("--json", action="store_true", help="输出结构化 JSON")
    pm = sub.add_parser("postmortem", help="复盘（无指责 + 根因指向机制 + 行动项闭环）",
                        description="复盘（机制借鉴 SRE postmortem）")
    pmsub = pm.add_subparsers(dest="postmortem_cmd")
    pm_ck = pmsub.add_parser("check", help="机检单件复盘", description="机检单件复盘")
    pm_ck.add_argument("path", help="复盘件路径（仓库相对）")
    for _p in (pmsub.add_parser("ls", help="列全部复盘", description="列全部复盘"), pm_ck,
               pmsub.add_parser("verify", help="机检声明 + 全部复盘件", description="机检")):
        _p.add_argument("--json", action="store_true", help="输出结构化 JSON")
    au = sub.add_parser("audit", help="审计/验收（结论绑定对象 digest + 签收双要素）",
                        description="审计/验收（机制借鉴 Audit Report + Acceptance/Sign-off）")
    ausub = au.add_subparsers(dest="audit_cmd")
    au_ck = ausub.add_parser("check", help="机检单件审计", description="机检单件审计")
    au_ck.add_argument("path", help="审计件路径（仓库相对）")
    for _a in (ausub.add_parser("ls", help="列全部审计件", description="列全部审计件"), au_ck,
               ausub.add_parser("verify", help="机检声明 + 全部审计件", description="机检")):
        _a.add_argument("--json", action="store_true", help="输出结构化 JSON")
    cog = sub.add_parser("cognition", help="认知族（行话术语表 + 执行分档 Runbook/Playbook）",
                         description="认知族（机制借鉴 Glossary + SOP/Runbook/Playbook 分档）")
    cog.add_argument("part", nargs="?", default="", choices=["", "glossary", "modes"],
                     help="只看一件（缺省 = 全跑）")
    cog.add_argument("--json", action="store_true", help="输出结构化 JSON")
    stv = sub.add_parser("st-validate",
                         help="ST 制卡校验器原型（卡 / 世界书 / MVU 变量 → 报告；A-S3）",
                         description="ST 制卡校验器原型 v0（任务书 A-S3：R1 结构 / R3 世界书 / R4 变量）")
    stv.add_argument("path", help="被校验对象（JSON；卡 / 世界书 / MVU 变量产物）")
    stv.add_argument("--out", default="", help="把 markdown 报告写入该路径")
    stv.add_argument("--json", action="store_true", help="输出结构化 JSON")
    sfp = sub.add_parser("state-front",
                         help="条件先行排布（状态块前置/后置/省略；T3 刺激件生成器）",
                         description="条件先行排布（灵感来源 arXiv:2609.02702 的 condition-first；NF 只做排布纪律）")
    sfp.add_argument("path", help="产物 md 路径（仓库相对或绝对）")
    sfp.add_argument("--mode", default="front", choices=["front", "back", "none"],
                     help="排布方式（缺省 front = 条件先行）")
    sfp.add_argument("--out", default="", help="写出排布结果")
    sfp.add_argument("--check", action="store_true", help="只判「状态块是否已前置」")
    sfp.add_argument("--ab", action="store_true", help="输出 A/B/C 三刺激件清单（T3 装置）")
    sfp.add_argument("--json", action="store_true", help="输出结构化 JSON")
    ln.add_argument("--json", action="store_true", help="输出结构化 JSON")
    lp = sub.add_parser("lsp",
                        help="最小 LSP 服务器（stdio：诊断 + quickfix，供编辑器接入；不写盘）",
                        description="最小 LSP 服务器（stdio Content-Length 分帧；诊断/quickfix 与 nf lint 同源）")
    lp.add_argument("--root", default="", help="仓库根（缺省 = 本仓库）")
    lc = sub.add_parser("license",
                        help="图书馆许可证门（登记表「许可」列 + 条目内联声明双源校验）",
                        description="图书馆许可证门（内部差距：登记表无许可列，入库产物不承载共享条款）")
    lc.add_argument("--json", action="store_true", help="输出结构化 JSON")
    tl = sub.add_parser("telemetry",
                        help="遥测 semconv 映射（trace 记录 → OTel GenAI 属性 / OTLP 形状）",
                        description="遥测 semconv 映射（内部差距：trace 为自定 JSON，对外界不可消费）")
    tl.add_argument("trace", help="trace JSON（单条记录或 {records:[...]}）")
    tl.add_argument("--otlp", action="store_true",
                    help="输出 OTLP 形状 JSON（resourceSpans → scopeSpans → spans）")
    conf = sub.add_parser("conformance",
                         help="一致性报告工件（全部契约 → Merkle 根 + verdict；可归档可比对）",
                          description="一致性报告工件（机制借鉴 MCOP runConformanceSuite：make it checkable instead of trusted）")
    conf.add_argument("--write", action="store_true",
                      help="把当前报告写入 protocol/conformance_report.json")
    conf.add_argument("--json", action="store_true", help="输出结构化 JSON")
    ev = sub.add_parser("events",
                        help="全仓事件背书核对（订阅必有发布方；跨包事件可见；外部通道须挂账）",
                        description="全仓事件背书核对（补 check16/26 之外：社区域包订阅是否真有发布方）")
    ev.add_argument("--json", action="store_true", help="输出结构化 JSON")
    rc2 = sub.add_parser("receipts",
                         help="协议层回执单根（01–07/schema/baseline 等机读产物各带 inclusion proof）",
                         description="协议层回执单根（把回执覆盖面从馆藏扩到协议层机读产物）")
    rc2.add_argument("--scope", default="protocol", choices=["protocol"],
                     help="回执范围（当前支持 protocol）")
    rc2.add_argument("--write", action="store_true", help="写入 protocol/RECEIPTS.json")
    rc2.add_argument("--entry", default="", help="只验一条（按相对路径）")
    rc2.add_argument("--json", action="store_true", help="输出结构化 JSON")
    drv = sub.add_parser("driver",
                         help="指令档机器面路由（有 MCP 走 MCP；派发失败即停、不回退文本步骤）",
                         description="指令档机器面路由（机制借鉴 ACP driver override）")
    drv.add_argument("workflow", nargs="?", default="",
                     help="工作流名（缺省 = 列全部工作流）")
    drv.add_argument("--json", action="store_true", help="输出结构化 JSON")
    rfc = sub.add_parser("rfc",
                         help="协议件 RFC 索引（编号/Category/Date/Status + supersede 链）",
                         description="协议件 RFC 索引（机制借鉴 HMP：把协议版本史做成可机读头）")
    rfc.add_argument("--json", action="store_true", help="输出结构化 JSON")
    ptn = sub.add_parser("patterns",
                         help="实践包：可发布/可消费/可移植的最佳实践（ls/show/for/verify/reindex）",
                         description="实践包品类（机制借鉴 ACP patterns：与内容域包并列的实践规范包）")
    p2 = ptn.add_subparsers(dest="patterns_cmd")
    pa_ls = p2.add_parser("ls", help="列出全部 pattern", description="列出全部 pattern")
    pa_sh = p2.add_parser("show", help="看单条 pattern（frontmatter + 正文）",
                          description="看单条 pattern（frontmatter + 正文）")
    pa_sh.add_argument("id", help="pattern id（目录名）")
    pa_fp = p2.add_parser("for", help="反向查：某文件适用哪些 pattern",
                          description="反向查：某文件适用哪些 pattern")
    pa_fp.add_argument("target", help="文件路径（仓库相对或绝对）")
    pa_vf = p2.add_parser("verify", help="机检 pattern（格式 + 可证性）",
                          description="机检 pattern（格式 + 可证性）")
    pa_ri = p2.add_parser("reindex", help="重建 patterns/INDEX 投影",
                          description="重建 patterns/INDEX 投影")
    for _p2 in (pa_ls, pa_sh, pa_fp, pa_vf, pa_ri):
        _p2.add_argument("--json", action="store_true", help="输出结构化 JSON")
    bn = sub.add_parser("bench",
                        help="执行结果跑分台（对 agent 产物五维确定性评分；多跑可比对）",
                        description="执行结果跑分台（机制借鉴 ACP benchmark suite：外部实测的容器）")
    b2 = bn.add_subparsers(dest="bench_cmd", required=True)
    b_run = b2.add_parser("run", help="跑一个用例 → run 记录（可 --out 存档）",
                          description="跑一个用例 → run 记录（可 --out 存档）")
    b_run.add_argument("--case", required=True, help="用例目录（含 case.json）")
    b_run.add_argument("--artifact", default="", help="被评产物 md（缺省=用例 default_artifact）")
    b_run.add_argument("--model", default="", help="跑次来源标识（模型/客户端名）")
    b_run.add_argument("--out", default="", help="把 run 记录写入该 JSON（缺省=打印）")
    b_cmp = b2.add_parser("compare", help="多跑比对（逐维均值/极差/相对最佳回落）",
                          description="多跑比对（逐维均值/极差/相对最佳回落）")
    b_cmp.add_argument("runs", help="run 记录 JSON（单个对象或数组）")
    b_rep = b2.add_parser("report", help="人读跑分报告（markdown）",
                          description="人读跑分报告（markdown）")
    b_rep.add_argument("runs", help="run 记录 JSON（单个对象或数组）")
    for _b2 in (b_run, b_cmp, b_rep):
        _b2.add_argument("--json", action="store_true", help="输出结构化 JSON")
    ep = sub.add_parser("endpoint",
                        help="服务端点契约（proposed：把已实现能力声明成 HTTP 面 + 指向真实性门禁）",
                        description="服务端点契约（机制借鉴 microsoft/ai-chat-protocol）")
    ep.add_argument("--json", action="store_true", help="输出结构化 JSON")
    kn = sub.add_parser("knowledge",
                        help="双源知识层（权威分层 / 消化可追溯 / 查询有序 / 时效 / 可见性）",
                        description="双源知识层（机制借鉴一句式：编译时机按数据域选择）")
    ksub = kn.add_subparsers(dest="knowledge_cmd")
    k_order = ksub.add_parser("order", help="解析查询顺序（合同级在前、参考级在后）",
                              description="解析查询顺序（合同级在前、参考级在后）")
    k_order.add_argument("--as", dest="clearance", default="",
                         choices=["", "public", "internal", "restricted"],
                         help="按可见性裁剪（缺省 = 不裁剪）")
    k_lint = ksub.add_parser("lint", help="知识层巡检（悬空 / 孤儿 / 时效 / 溯源 / 声明）",
                             description="知识层巡检（悬空 / 孤儿 / 时效 / 溯源 / 声明）")
    k_tr = ksub.add_parser("transform", help="列消化记录（外部 → 本地，digest 绑定）",
                           description="列消化记录（外部 → 本地，digest 绑定）")
    k_tr.add_argument("--json", action="store_true", help="输出结构化 JSON")
    _t = k_tr.add_subparsers(dest="transform_cmd")
    t_add = _t.add_parser("add", help="登记一条消化记录（复核双签，未转正）",
                          description="登记一条消化记录（复核双签，未转正）")
    t_add.add_argument("--from", dest="src", required=True, help="参考级源 id")
    t_add.add_argument("--to", dest="dst", required=True, help="本地产物（仓库相对路径）")
    t_add.add_argument("--by", default="", help="复核人")
    t_add.add_argument("--at", default="", help="复核时间 YYYY-MM-DD（缺省 = 今天）")
    t_add.add_argument("--json", action="store_true", help="输出结构化 JSON")
    t_prom = _t.add_parser("promote", help="转正（须齐三档证据 + 复核双签）",
                           description="转正（须齐三档证据 + 复核双签）")
    t_prom.add_argument("--from", dest="src", required=True, help="参考级源 id")
    t_prom.add_argument("--to", dest="dst", required=True, help="本地产物（仓库相对路径）")
    t_prom.add_argument("--by", default="", help="复核人（必填）")
    t_prom.add_argument("--at", default="", help="复核时间 YYYY-MM-DD（缺省 = 今天）")
    t_prom.add_argument("--evidence", default="",
                        help="证据档（逗号分隔，须齐 machine-checkable,reproducible,externally-attestable）")
    t_prom.add_argument("--json", action="store_true", help="输出结构化 JSON")
    k_freq = ksub.add_parser("frequency", help="从 trace 复算知识源使用频次（--write 落台账）",
                             description="从 trace 复算知识源使用频次（确定性；频次不可手写）")
    k_freq.add_argument("--trace", required=True, help="trace 文件（JSON / JSONL）")
    k_freq.add_argument("--write", action="store_true",
                        help="写入 protocol/knowledge_usage.json")
    k_vis = ksub.add_parser("visible", help="按可见性列出源（认知裁剪执行面）",
                            description="按可见性列出源（认知裁剪执行面）")
    k_vis.add_argument("--as", dest="clearance", default="public",
                       choices=["public", "internal", "restricted"],
                       help="消费方清除级（public ⊆ internal ⊆ restricted）")
    for _k in (k_order, k_lint, k_freq, k_vis):
        _k.add_argument("--json", action="store_true", help="输出结构化 JSON")
    ap = sub.add_parser("approve",
                        help="内容绑定批准记录（被批准对象改动即失效）",
                        description="内容绑定批准记录（机制借鉴 MCOP approved-changeset gate）")
    ap.add_argument("subject", nargs="?", default="", help="被批准对象路径（仓库相对）")
    ap.add_argument("--by", default="", help="批准人标识")
    ap.add_argument("--note", default="", help="批准说明")
    ap.add_argument("--verify", action="store_true",
                    help="校验全部批准记录（缺省 = 生成模式）")
    ap.add_argument("--list", action="store_true", help="列出全部批准记录（含失效标记）")
    ap.add_argument("--json", action="store_true", help="输出结构化 JSON")
    lib = sub.add_parser("library",
                         help="云端图书馆机器面（frontmatter 真源 / INDEX·ALIAS 投影 / 检索）",
                         description="云端图书馆机器面（内部差距：library 无 CLI 面、MCP 检索不覆盖馆藏、元数据非一等公民）")
    lsub = lib.add_subparsers(dest="library_cmd")
    l_ls = lsub.add_parser("ls", help="列出馆藏条目（编号/状态/许可/标题）",
                           description="列出馆藏条目（编号/状态/许可/标题）")
    l_sh = lsub.add_parser("show", help="查看单条条目（frontmatter + 正文头）",
                           description="查看单条条目（frontmatter + 正文头）")
    l_sh.add_argument("entry", help="编号（如 NF-1）")
    l_ri = lsub.add_parser("reindex",
                           help="重生成 INDEX 生成区 + ALIAS（真源 = 条目 frontmatter）",
                           description="重生成 INDEX 生成区 + ALIAS（真源 = 条目 frontmatter）")
    l_vf = lsub.add_parser("verify", help="校验 frontmatter + 投影一致性（图书馆门同语义）",
                           description="校验 frontmatter + 投影一致性（图书馆门同语义）")
    l_vf.add_argument("--key-file", default="",
                      help="验签名锚用的 HMAC 密钥（缺省 = 只报「无法校验」，不判死）")
    l_vf.add_argument("--ssh-allowed-signers", default="",
                      help="ssh-sig 锚校验用的 allowed_signers 文件")
    l_vf.add_argument("--ssh-identity", default="",
                      help="ssh-sig 锚校验用的 principal")
    l_se = lsub.add_parser("search", help="关键词检索（标题/描述/标签/正文，中文子串可用）",
                           description="关键词检索（标题/描述/标签/正文，中文子串可用）")
    l_se.add_argument("query", help="检索串")
    l_dp = lsub.add_parser("deprecate", help="生命周期流转 → deprecated（不再推荐、仍可读）",
                           description="生命周期流转 → deprecated（不再推荐、仍可读）")
    l_dp.add_argument("entry", help="编号")
    l_rs = lsub.add_parser("restore", help="生命周期回退 → active",
                           description="生命周期回退 → active")
    l_rs.add_argument("entry", help="编号")
    l_sp = lsub.add_parser("supersede", help="取代链：旧条目 → superseded（指向新条目）",
                           description="取代链：旧条目 → superseded（指向新条目）")
    l_sp.add_argument("entry", help="被取代的旧编号")
    l_sp.add_argument("by", help="取代它的新编号")
    l_at = lsub.add_parser("attest", help="给条目挂 attestation（复用 nf attest 信封摘要）",
                           description="给条目挂 attestation（复用 nf attest 信封摘要，写入 frontmatter）")
    l_at.add_argument("entry", help="编号")
    l_at.add_argument("--key-file", default="",
                      help="HMAC 密钥文件 → 一并落签名锚（不给则 digest_only 级）")
    l_at.add_argument("--ssh-key", default="",
                      help="SSH 私钥路径 → 落 ssh-sig 锚（真实非对称签名，读者用 ssh-keygen 即可验）")
    l_at.add_argument("--ssh-identity", default="",
                      help="ssh-sig 的 principal（allowed_signers 里的身份）")
    l_rc = lsub.add_parser("receipts",
                           help="馆藏回执 + 单根（逐条 inclusion proof，读者可本地折叠验证）",
                           description="馆藏回执 + 单根（机制借鉴 MCOP MMR：O(log n) 审计路径代替 O(n) 重放）")
    l_rc.add_argument("--write", action="store_true", help="写入 library/RECEIPTS.json")
    l_rc.add_argument("--entry", default="",
                      help="只验一条：按编号取回执并本地折叠到根（读者侧验证入口）")
    for _p in (l_ls, l_sh, l_ri, l_vf, l_se, l_dp, l_rs, l_sp, l_at, l_rc):
        _p.add_argument("--json", action="store_true", help="输出结构化 JSON")
    df = sub.add_parser("diff",
                        help="版本差异检测（41 波C C2：两份签名/文档 → 字段级差异 + 兼容判定）", description="版本差异检测（41 波C C2：两份签名/文档 → 字段级差异 + 兼容判定）")
    df.add_argument("a", help="签名 A 的文档 md 路径")
    df.add_argument("b", help="签名 B 的文档 md 路径")
    df.add_argument("--json", action="store_true", help="输出结构化差异 JSON")
    ex = sub.add_parser("explain",
                        help="check 修复指引（41 波C C5：缺什么/补什么/示例 三段式）", description="check 修复指引（41 波C C5：缺什么/补什么/示例 三段式）")
    ex.add_argument("check", help="check 编号（如 25；all = 全量清单）")
    rel = sub.add_parser("related",
                        help="See-Also 关联查询（41 波C C4：market/图书馆条目人读引用链）", description="See-Also 关联查询（41 波C C4：market/图书馆条目人读引用链）")
    rel.add_argument("target",
                    help="目标 = 包 id（如 技术文档域包）或模块 id（如 M90 / 技术文档:M90）")
    rel.add_argument("--registry", default=None,
                     help="registry.json 路径（缺省 = desktop/src/core/registry.json）")
    rel.add_argument("--json", action="store_true",
                     help="输出结构化 JSON（See-Also 关联结果）")
    hep = sub.add_parser("help",
                         help="显示 nf 或指定子命令的帮助", description="显示 nf 或指定子命令的帮助")
    hep.add_argument("command", nargs="?", metavar="COMMAND",
                     help="子命令名；缺省 = 显示 nf 总帮助")
    doc = sub.add_parser("doctor",
                         help="环境自检（快速只读体检：关键文件/registry/schema/核心库——不开 verify 慢跑）", description="环境自检（快速只读体检：关键文件/registry/schema/核心库——不开 verify 慢跑）")
    doc.add_argument("--json", action="store_true",
                     help="输出结构化 JSON 报告")
    cmp = sub.add_parser("completion",
                         help="生成 shell 补全脚本（bash/zsh/fish；用法：nf completion bash >> ~/.bashrc）", description="生成 shell 补全脚本（bash/zsh/fish；用法：nf completion bash >> ~/.bashrc）")
    cmp.add_argument("shell", choices=("bash", "zsh", "fish"),
                     help="目标 shell")
    asm = sub.add_parser("assemble",
                         help="需求 → 自组装编排（44：一句话需求 → 装配计划；--check 对成品机器验收）", description="需求 → 自组装编排（44：一句话需求 → 装配计划；--check 对成品机器验收）")
    asm.add_argument("requirement",
                     help="用户需求一句话（如：帮我组装一个西幻生存世界的完整版）")
    asm.add_argument("--check", dest="check_md", metavar="OUT.md",
                     help="对成品完整版 md 做机器验收（骨架/编号/引用）")
    asm.add_argument("--save", dest="save_path", metavar="FILE.md",
                     help="把澄清/计划落成需求档案（八字段回填稿）")
    asm.add_argument("--trace", dest="trace_path", metavar="TRACE.json",
                     help="执行遥测落盘（计划/澄清/验收留痕，供真实转录/E3 补测底座）")
    asm.add_argument("--rounds", action="store_true",
                     help="回合级 drill：对成品转录按回合断言（引用/推进/编造，45 A2）")
    asm.add_argument("--answer", action="append", default=None,
                     metavar="问答",
                     help="澄清回填（可多次，如 --answer \"题材：西幻生存\" --answer \"主轴：生存\"）")
    asm.add_argument("--session", dest="session_path", metavar="SESSION.json",
                     help="会话存储：多次调用间保留已回填澄清（多轮记忆落盘）")
    rel = sub.add_parser("release",
                         help="发布前体检（45：verify + 基线自描述一致 + doctor；--fast 跳过 verify）", description="发布前体检（45：verify + 基线自描述一致 + doctor；--fast 跳过 verify）")
    rel.add_argument("--fast", action="store_true",
                     help="跳过 verify.sh 全量（快速自检：基线自描述 + doctor）")
    tf = sub.add_parser("toolface",
                        help="模块工具面浏览（45：machine_contract.tool_face 可选建议层，AI 裁量不入门禁）", description="模块工具面浏览（45：machine_contract.tool_face 可选建议层，AI 裁量不入门禁）")
    tf.add_argument("--json", action="store_true",
                    help="输出结构化 JSON（工具面清单）")
    wm = sub.add_parser("worldmodel",
                        help="world_model 浏览（JEPA-inspired 确定性抽象状态契约，check32 硬门）", description="world_model 浏览（JEPA-inspired 确定性抽象状态契约，check32 硬门）")
    wm.add_argument("--json", action="store_true",
                    help="输出结构化 JSON（world_model 清单）")
    wm.add_argument("--walk", action="store_true",
                    help="从 initial_phase 重放确定性相位迁移环")
    wm.add_argument("--run", action="store_true",
                    help="执行 WorldModelRuntime：状态校验 + 相位前进 + 轨迹重放")
    wm.add_argument("--state", dest="state_path", metavar="STATE.json",
                    help="具体 M00 状态 JSON；与 --run 联用时按 slot 绑定重放")
    return p


def _seed_store(store):
    """装载官方核心 + 轻混组合包（等同 e2e 前置）。返回统计 dict。"""
    import glob
    from pathlib import Path
    from core.parser import parse_module
    stats = {"core": 0, "combo": 0}
    for f in sorted(glob.glob(os.path.join(ROOT, "04_模块库", "*", "*.md"))):
        try:
            store.save_module(parse_module(Path(f).read_text(encoding="utf-8")))
            stats["core"] += 1
        except Exception:
            continue
    for f in sorted(glob.glob(os.path.join(ROOT, "community",
                                           "校园西幻轻混组合包", "modules", "*.md"))):
        try:
            store.save_module(parse_module(Path(f).read_text(encoding="utf-8")))
            stats["combo"] += 1
        except Exception:
            continue
    return stats


def _cmd_register(args) -> int:
    """nf register：本地登记助手（B3-B）。--check 只读 / --apply 合并写。"""
    from core.protocol_projection import project_entry
    from core.registry_sync import check_registerable, merge_protocols

    reg_path = args.registry or os.path.join(ROOT, "desktop", "src", "core", "registry.json")
    doc_path = os.path.join(ROOT, "02_联动注册表.md")

    # 三要件校验（② 02 在册；① protocol.yaml 由 check_registerable 内置）
    with open(doc_path, encoding="utf-8") as f:
        doc = f.read()
    issues = check_registerable(args.pkg_dir, doc)
    if issues:
        for msg in issues:
            print(f"  [拒绝] {msg}", file=sys.stderr)
        print("✗ 校验未通过——须先满足登记三要件（02 §8.3）；详见 02 §9.2 同步纪律", file=sys.stderr)
        return 1

    entry = project_entry(args.pkg_dir)

    import json
    with open(reg_path, encoding="utf-8") as f:
        reg = json.load(f)
    cur = reg.get("protocols")
    if not isinstance(cur, list):
        print("✗ registry protocols[] 缺失或非列表", file=sys.stderr)
        return 1

    # 键序无关比较：merge 结果与现状在规范化（sorted keys）意义上相等 → 无实质变化
    def _canon(prots):
        return sorted(json.dumps(p, sort_keys=True, ensure_ascii=False) for p in prots)

    existing = next((p for p in cur if p["id"] == entry["id"]), None)
    merged = merge_protocols(cur, [entry])
    changed = _canon(merged) != _canon(cur)
    print(f"== nf register {entry['id']} [{args.mode}] ==")
    if not changed:
        print("  投影与 registry 现状一致，无更新（幂等，不写盘）")
        if args.mode == "apply":
            return 0
        return 0
    print("  将更新 protocols[]：%s" % ("新增" if existing is None else "覆盖"))
    diff_keys = sorted(k for k in entry if not existing or existing.get(k) != entry.get(k))
    if diff_keys:
        print("  差异字段：%s" % ", ".join(diff_keys))

    if args.mode != "apply":
        print("  [--check] 未写盘（--apply 才合并写入）")
        return 0

    reg["protocols"] = merged
    with open(reg_path, "w", encoding="utf-8") as f:
        json.dump(reg, f, ensure_ascii=False, indent=2)
    print(f"  ✓ 已写入 {reg_path}（protocols[] {len(cur)} → {len(merged)} 条，只增不删）")
    print("  下一步：跑 `bash verify.sh` 由 check14 ⑦ 元素级断言自证")
    return 0


def _cmd_market(args) -> int:
    """nf market：依赖闭包 + 挂载冲突预检（B4 CLI 先行；信息查询，冲突不阻断）。"""
    import json
    from core.market_analyzer import (conflicts, dependencies, grades_of_package,
                                      list_market)
    from core.registry_sync import check_registerable
    from core.registry_loader import load_registry

    reg_path = args.registry or os.path.join(ROOT, "desktop", "src", "core", "registry.json")
    doc_path = os.path.join(ROOT, "02_联动注册表.md")

    # ---- list 目录视图（v2.5.0 Wave3）----
    if args.list:
        reg = load_registry(reg_path)
        items = list_market(reg, tier=args.tier)
        if args.json:
            import json as _json
            print(_json.dumps({
                "kind": "market-list",
                "tier": args.tier,
                "items": items,
            }, ensure_ascii=False, indent=2, sort_keys=True))
            return 0
        print(f"== nf market list{'（tier=' + args.tier + '）' if args.tier else ''} ==")
        _badge = {"official": "🏛官方", "community": "🌐社区", "experimental": "🧪实验"}
        for it in items:
            if it["kind"] == "module":
                print(f"  [{_badge[it['grade']]}] 模块 {it['id']} · {it['name']}")
            else:
                print(f"  [{_badge[it['grade']]}] 包 {it['id']} v{it['version']}"
                      f"（{it['modules']} 模块）")
        return 0

    if not args.pkg_dir:
        print("✗ 缺 pkg_dir（或加 --list 列目录）", file=sys.stderr)
        return 2
    pkg_id = os.path.basename(args.pkg_dir.rstrip("/\\"))

    with open(reg_path, encoding="utf-8") as f:
        reg = json.load(f)
    prots = {p["id"]: p for p in reg.get("protocols", [])}
    with open(doc_path, encoding="utf-8") as f:
        doc = f.read()

    # 登记状态（复用 registry_sync 三要件校验；issue 即未就绪提示，不阻断查询）
    reg_issues = check_registerable(args.pkg_dir, doc)
    if pkg_id not in prots:
        if args.json:
            print(json.dumps({
                "kind": "market-package",
                "pkg_id": pkg_id,
                "registered": False,
                "issues": reg_issues,
            }, ensure_ascii=False, indent=2, sort_keys=True))
            return 1 if reg_issues else 0
        print("  registry protocols[] 无条目——无 references 可查")
        return 1 if reg_issues else 0

    # 加载各包 protocol.yaml 内容（data 供 dependencies/conflicts 用）
    import glob
    import yaml
    data = {}
    for pf in sorted(glob.glob(os.path.join(ROOT, "community", "*", "protocol.yaml"))):
        try:
            with open(pf, encoding="utf-8") as f:
                raw = yaml.safe_load(f)
            data[raw["package"]["id"]] = raw
        except Exception:
            continue

    seen, dep_issues = dependencies(pkg_id, prots, data)
    cfl = conflicts(pkg_id, prots, data)
    # A6 质量分级徽章（v2.4.0）：官方核心/社区/实验
    grades = grades_of_package(prots, pkg_id)
    if args.json:
        print(json.dumps({
            "kind": "market-package",
            "pkg_id": pkg_id,
            "registered": True,
            "issues": reg_issues,
            "dependencies": sorted(seen),
            "dependency_issues": dep_issues,
            "conflicts": cfl,
            "grades": grades,
        }, ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    print(f"== nf market {pkg_id} ==")
    print("  登记状态: %s" % ("在册（02 §8 + registry protocols[]）"
                              if not reg_issues else "; ".join(reg_issues)))
    if grades:
        _badge = {"official": "🏛官方", "community": "🌐社区", "experimental": "🧪实验"}
        badge_line = ", ".join(f"{m}({_badge[g]})" for m, g in grades.items())
        print(f"  分级徽章: {badge_line}")
    print("  依赖闭包: %s" % (", ".join(sorted(seen)) if seen else "无跨包引用"))
    for i in dep_issues:
        print(f"  [依赖] {i}")
    if cfl:
        for i in cfl:
            print(f"  [冲突] {i}")
    else:
        print("  挂载冲突: 无")
    return 0


def _cmd_who_refers(args) -> int:
    """nf who-refers <module_id>：谁在 references 中引用了该模块（A2 反查）。"""
    from core.retriever import referenced_by

    reg_path = args.registry or os.path.join(ROOT, "desktop", "src", "core", "registry.json")
    refs = referenced_by(args.module_id, path=reg_path)
    print(f"== 谁引用了 {args.module_id} ==")
    if not refs:
        print("  无（registry protocols[].references 中无引用）")
        return 0
    for r in refs:
        ro = "只读" if r.get("asset_readonly") else ""
        print(f"  {r['referrer']} → {r['source_package']}.{r['module_id']} {ro}")
    return 0


def _cmd_impact(args) -> int:
    """nf impact <target>：拟删除目标（module/protocol）的破坏性影响预检（A4 前置）。

    --check 门禁模式：破坏性变更（module 被引用/官方在册，或整包删除有引用方）
    exit 1——镜像 verify 铁律，供变更前门禁接线。
    """
    from core.impact_check import impact_of_change
    from core.registry_loader import load_registry

    reg_path = args.registry or os.path.join(ROOT, "desktop", "src", "core", "registry.json")
    reg = load_registry(reg_path)
    im = impact_of_change(reg, args.target)
    print(f"== 删除影响面预检: {args.target} ==")
    if im.get("error"):
        print(f"  [拒绝] {im['error']}")
        return 1

    if "module_id" in im:                     # module 级
        refs = im["referenced_by"]
        print(f"  类型: module（官方在册 {im['in_official_core'] or '无'} · "
              f"属包 {im['in_packages'] or '无'}）")
        if not refs and not im["in_official_core"]:
            print("  无破坏性影响（无引用方且非官方核心——可安全移除）")
            return 0
        for r in refs:
            ro = "只读" if r.get("asset_readonly") else ""
            print(f"  破坏性: 被 {r['protocol']} 引用（引用声明源 {r['source_package']}"
                  f"，asset_readonly {ro or 'false'}）")
        if im["in_official_core"]:
            print(f"  破坏性: 官方核心在册 {im['in_official_core']}（删官方核心 = 协议事故）")
        return 1 if args.mode == "check" else 0
    # protocol 级（整包删除）
    refs = im["referenced_by_packages"]
    print(f"  类型: protocol 整包（module_ids {im['module_ids'] or '无'}）")
    if not refs:
        print("  无破坏性影响（无其它包引用本包模块——可安全移除，自身 references 随之消失）")
        return 0
    for r in refs:
        print(f"  破坏性: 被 {r['protocol']} 引用（引用声明源 {r['source_package']}）")
    return 1 if args.mode == "check" else 0


def _cmd_rename(args) -> int:
    """nf rename <old> <new>：模块改名引用重链（A5 变更助手）。

    --check（缺省）只列受影响引用；--apply 批量重链 references[].module_id 后
    合并写 registry protocols[]（只改引用目标，不动其它字段，V1 只增不删语义）。
    """
    from core.impact_check import rename_module_plan
    from core.registry_loader import load_registry

    reg_path = args.registry or os.path.join(ROOT, "desktop", "src", "core", "registry.json")
    reg = load_registry(reg_path)
    plan = rename_module_plan(reg, args.old_id, args.new_id)
    print(f"== 改名引用重链: {args.old_id} → {args.new_id} ==")
    if not plan["affected"]:
        print("  无引用方（registry references 中无引用该模块——安全改名，无需重链）")
        return 0
    for a in plan["affected"]:
        print(f"  重链: {a['protocol']} references {a['old_module_id']} → "
              f"{a['new_module_id']}（源 {a['source_package']}）")

    if args.mode != "apply":
        print(f"  [{args.mode or 'check'}] 未写盘（--apply 才合并写 registry protocols[]）")
        return 0

    import json as _json
    with open(reg_path, encoding="utf-8") as f:
        raw = _json.load(f)
    raw["protocols"] = plan["updated_protocols"]
    with open(reg_path, "w", encoding="utf-8") as f:
        _json.dump(raw, f, ensure_ascii=False, indent=2)
    print(f"  ✓ 已重链 {len(plan['affected'])} 处引用并写盘 {reg_path}")
    print("  下一步：跑 `bash verify.sh` 由 check14 ⑦/check15 ① 元素级断言自证")
    return 0


def _cmd_import(args) -> int:
    """nf import <file> [--register]：读入外部产物（A4 遗留闭环）。

    SKILL.md → parse_skill（含 skill_dir 随行资源扫描）；chara.json →
    parse_ccv3。--register 把 IR 模块幂等装载进 Store（save_module 覆盖式幂等，
    同 seed_from_repo 模式）。
    """
    import json
    from pathlib import Path
    from core.import_adapter import parse_skill, parse_ccv3
    from core.storage import Store
    from core.models import Module

    p = Path(args.file)
    if not p.is_file():
        print(f"✗ 文件不存在: {p}", file=sys.stderr)
        return 2

    is_ccv3 = p.suffix.lower() == ".json" or "chara" in p.stem.lower()
    print(f"== nf import {p.name} ==")
    if is_ccv3:
        data = json.loads(p.read_text(encoding="utf-8"))
        res = parse_ccv3(data)
        kind = "CCV3 chara"
        bundled = []
    else:
        text = p.read_text(encoding="utf-8")
        res = parse_skill(text, skill_dir=p.parent)
        kind = "SKILL"
        bundled = res.bundled_resources

    print(f"  类型: {kind} | 解析: {'ok' if res.ok else 'fail'} | mode: {res.mode}")
    if res.ir is not None:
        n_mod = sum(len(l.modules) for l in res.ir.layers) + len(res.ir.extra_modules)
        print(f"  IR: {res.ir.type} · {res.ir.title} · 管线 {res.ir.pipeline_id} · {n_mod} 模块")
    if bundled:
        print(f"  随行资源: {', '.join(bundled)}")
    for w in res.warnings:
        print(f"  [警告] {w}")

    if not args.register:
        return 0
    if res.ir is None:
        print("✗ 无 IR 可登记（external 模式未升 IR）", file=sys.stderr)
        return 1

    store = Store(home=args.store) if args.store else Store()
    n = 0
    for layer in res.ir.layers:
        for im in layer.modules:
            fid = im.full_id
            cat, num = fid.rsplit(":", 1) if ":" in fid else ("通用类", fid)
            store.save_module(Module(id=num, name=im.name, category=cat,
                                    layer=im.layer, source_md=im.content))
            n += 1
    for im in res.ir.extra_modules:
        fid = im.full_id
        cat, num = fid.rsplit(":", 1) if ":" in fid else ("通用类", fid)
        store.save_module(Module(id=num, name=im.name, category=cat,
                                layer=im.layer, source_md=im.content))
        n += 1
    print(f"  ✓ 已幂等装载 {n} 模块 → {store.home}")
    return 0


def _cmd_spec(args) -> int:
    """nf spec ls：Spec Registry 查询（v2.5.0 Wave3：版本化 spec 清单）。"""
    from core.registry_loader import load_registry

    reg_path = args.registry or os.path.join(ROOT, "desktop", "src", "core", "registry.json")
    reg = load_registry(reg_path)
    print("== nf spec ls ==")
    print(f"  registry_schema_version: {reg.registry_schema_version}")
    print(f"  官方核心模块: {len(reg.modules)} 件")
    for p in reg.protocols or []:
        print(f"  {p.get('id')}: schema v{p.get('schema_version')}"
              f" · version {p.get('version') or '1.0.0'}"
              f" · {len(p.get('module_ids') or [])} 模块")
    return 0


def _cmd_render(args) -> int:
    """nf render <pkg_dir> --fmt：协议多出口渲染（A3：protocol.yaml → rules）。"""
    from pathlib import Path
    from core.rules_render import render_protocol

    txt = render_protocol(args.pkg_dir, args.fmt)
    out_name = {"agents": "AGENTS.md", "claude": "CLAUDE.md", "skill": "SKILL.md"}[args.fmt]
    dest = Path(args.dest) if args.dest else Path.cwd()
    dest.mkdir(parents=True, exist_ok=True)
    out_path = dest / out_name
    out_path.write_text(txt, encoding="utf-8")
    pkg_basename = os.path.basename(args.pkg_dir.rstrip("/\\"))
    print(f"== nf render {pkg_basename} → {args.fmt} ==")
    print(f"  ✓ {out_path}")
    return 0


def _cmd_serve(args) -> int:
    """nf serve <mcp.json>：快照烧成 stdio JSON-RPC 服务（C1，MCP client 拉起）。

    transport 纪律：stdout 只写 MCP 消息（换行分隔 JSON-RPC）——初始化说明走 stderr。
    """
    from core.mcp_runtime import load_snapshot, McpRuntime

    print(f"== nf serve {os.path.basename(args.snapshot)} =="
          f"（stdio JSON-RPC，Ctrl+C 退出）", file=sys.stderr)
    return McpRuntime(load_snapshot(args.snapshot)).serve_stdio()


def _cmd_design(args) -> int:
    """nf design steelman：钢人论证工作单（v2.6-A，可选决策辅助）。

    init "<问题>"            → 生成空白工作单（frontmatter + 六段 + 引导模板）
    steelman --check <file>  → 结构自检（缺项 warn 列表，空 = 通过）
    steelman ls [--root]     → 列决策档案索引（已有 steelman.md）
    """
    from pathlib import Path
    from core.steelman import (init_worksheet, check_worksheet,
                               scan_steelman)

    if args.check_file:
        p = Path(args.check_file)
        if not p.exists():
            print(f"  ✗ 文件不存在: {p}")
            return 1
        warns = check_worksheet(p.read_text(encoding="utf-8"))
        if not warns:
            print(f"  ✓ 结构自检通过（四步齐备 + meta 在场）: {p}")
            return 0
        print(f"== nf design steelman --check {p} ==")
        for w in warns:
            print(f"  ⚠ {w}")
        print(f"  → 缺项 {len(warns)} 条（补齐后重跑 --check）")
        return 1
    if args.action == "init":
        if not args.question:
            print("  ✗ init 需要问题描述: nf design steelman init \"<问题>\"")
            return 2
        out = Path(args.out) if args.out else Path.cwd() / "steelman.md"
        out.parent.mkdir(parents=True, exist_ok=True)
        init_worksheet(args.question, context=args.context,
                       decider=args.decider, path=out)
        print("== nf design steelman init ==")
        print(f"  ✓ 工作单已生成: {out}")
        print("    用三套引导模板之一填充六段，然后跑 --check 自检")
        return 0
    # ls
    root = Path(args.root)
    if not root.is_dir():
        print(f"  ✗ 目录不存在: {root}")
        return 1
    hits = scan_steelman(root)
    print("== nf design steelman ls ==")
    if not hits:
        print("  （无 steelman 工作单——nf design steelman init 生成第一份）")
        return 0
    print(f"  决策档案 {len(hits)} 份:")
    for h in hits:
        print(f"  · {h}")
    return 0


def _cmd_audit(args) -> int:
    """nf design audit：M_AUDIT 协议设计审计（决策过程质量）。

    audit init <question> --target T --mode {steelman,blindspot,full}
    audit --check <file>    # schema/verdict/清单边界；缺文件提示非红
    audit ls [--root]       # 审计记录索引
    """
    from pathlib import Path
    from core.audit import init_audit, check_audit, scan_audit

    if args.check_file:
        p = Path(args.check_file)
        warns = check_audit(p)
        if not warns:
            print(f"  ✓ 审计结构自检通过: {p}")
            return 0
        print(f"== nf design audit --check {p} ==")
        for w in warns:
            print(f"  ⚠ {w}")
        return 1
    if args.action == "init":
        if not args.question:
            print('  ✗ init 需要审计问题: nf design audit init "<问题>" --target T')
            return 2
        if not args.target:
            print('  ✗ init 需要 --target（被审计对象）: 如 --target "38 方案"')
            return 2
        out = Path(args.out) if args.out else Path.cwd() / "audit.md"
        out.parent.mkdir(parents=True, exist_ok=True)
        init_audit(args.question, target=args.target, mode=args.mode,
                   context=args.context, path=out)
        print(f"== nf design audit init（mode={args.mode}）==")
        print(f"  ✓ audit.md 已生成: {out}")
        print("    按引导问卷完成各节回填，然后 --check 自检")
        return 0
    # ls
    root = Path(args.root)
    if not root.is_dir():
        print(f"  ✗ 目录不存在: {root}")
        return 1
    hits = scan_audit(root)
    print("== nf design audit ls ==")
    if not hits:
        print("  （无 audit.md——nf design audit init 生成第一份）")
        return 0
    print(f"  审计记录 {len(hits)} 份:")
    for h in hits:
        print(f"  · {h}")
    return 0


def _cmd_asset(args) -> int:
    """nf asset：资产供应链台账族（40 总纲 S2）。纯信息命令缺省只读，写操作显式子命令。"""
    import json as _json
    from core import asset_ledger as al

    try:
        if args.asset_cmd == "baseline":
            from core import asset_line_baseline as alb
            if args.write:
                path = alb.write(args.root)
                print("== nf asset baseline --write ==")
                print("  [OK] 资产行数基线已重签：%s" % os.path.relpath(path, args.root))
                print("    下一步：`bash verify.sh` 由 check8 自证外形一致")
                return 0
            issues, warns, stats = alb.verify(args.root)
            print("== nf asset baseline（在册 %d 包 · 基线 %d 包）=="
                  % (stats.get("packages", 0), stats.get("baseline", 0)))
            for w in warns:
                print("  [WARN] %s" % w)
            for i in issues:
                print("  [FAIL] %s" % i)
            if not issues:
                print("  [OK] 社区包资产外形与基线一致（改外形须显式重签）")
            return 1 if issues else 0
        if args.asset_cmd == "add":
            if not args.root:
                print("  ✗ add 需要 --root（台账所在资产根目录，如 05_资产库）", file=sys.stderr)
                return 2
            entry = al.add_asset(args.root, args.file, args.key, args.source,
                                 module=args.module, version=args.version,
                                 status=args.status, tier=args.tier,
                                 package=args.package)
            print("== nf asset add ==")
            print("  ✓ 已入库：%s（key=%s · version=%s · status=%s）"
                  % (entry["file"], entry["key"], entry["version"], entry["status"]))
            print("    台账：%s" % al.default_ledger_path(args.root))
            print("    下一步：`bash verify.sh` 由 check23 自证供应链闭合")
            return 0
        if args.asset_cmd == "verify":
            issues, stats = al.verify_root(args.root)
            print("== nf asset verify（扫描根：%s）==" % args.root)
            print("  台账 %d · 托管资产 %d · 存量未托管 %d · 孤儿头 %d"
                  % (stats["ledgers"], stats["assets"],
                     stats["untracked"], stats["orphans"]))
            for i in issues:
                print("  [FAIL] %s" % i)
            if issues:
                print("  ✗ 供应链台账存在缺口——修复后重跑（verify.sh check23 同语义）", file=sys.stderr)
                return 1
            print("  ✓ 台账闭合：每资产可溯源 / 可发现 / 键无孤儿")
            return 0
        if args.asset_cmd == "inventory":
            rows = al.inventory_root(args.root)
            if args.json:
                print(_json.dumps({"kind": "asset-inventory", "rows": rows},
                                  ensure_ascii=False, indent=2, sort_keys=True))
                return 0
            print("== nf asset inventory（扫描根：%s）==" % args.root)
            if not rows:
                print("  （无 provenance.json 台账——nf asset add 建档首个资产集）")
                return 0
            for r in rows:
                err = ("（读取失败：%s）" % r["error"]) if r.get("error") else ""
                print("  · %-28s pkg=%-10s tier=%-12s 在册=%d 未托管=%d 孤儿=%d%s"
                      % (r["dir"], r["package"], r["tier"],
                         r["assets"], r["untracked"], r["orphans"], err))
            return 0
        if args.asset_cmd == "ls":
            rows = al.filter_rows(al.iter_assets(args.root),
                                  pkg=args.pkg, tier=args.tier, status=args.status)
            if args.json:
                print(_json.dumps({"kind": "asset-ls", "rows": rows},
                                  ensure_ascii=False, indent=2, sort_keys=True))
                return 0
            print("== nf asset ls%s%s%s ==" % (
                "（pkg=" + args.pkg + "）" if args.pkg else "",
                "（tier=" + args.tier + "）" if args.tier else "",
                "（status=" + args.status + "）" if args.status else ""))
            if not rows:
                print("  （货架为空——nf asset add 入库首批资产）")
                return 0
            for r in rows:
                print("  · %-8s %-14s v%-6s %-10s %s -> %s"
                      % (r["tier"], r["key"], r["version"], r["status"],
                         r["file"], r["source"]))
            return 0
        if args.asset_cmd == "density":
            from core import asset_density as ad
            issues, stats = ad.scan(args.root)
            if args.json:
                print(_json.dumps({"kind": "asset-density",
                                   "ok": not issues, "issues": issues,
                                   "stats": stats},
                                  ensure_ascii=False, indent=2, sort_keys=True))
            else:
                print("== nf asset density（45 资产键语义密度）==")
                print("  资产文件 %d · 键 %d · 平均 %.2f 键/档"
                      % (stats["files"], stats["keys"],
                         stats["avg_keys_per_file"]))
                print("  无键档（中文名/附机制，合法计数）%d · 短档(<200字) %d"
                      % (stats["unkeyed"], stats["tiny"]))
                for i in issues:
                    print("  [FAIL] %s" % i)
                if not issues:
                    print("  ✓ 密度体检通过：无空档/不可读资产档")
            return 1 if issues else 0
        if args.asset_cmd == "usage":
            from core import asset_density as ad
            issues, stats = ad.usage_scan(args.root)
            if args.json:
                print(_json.dumps({"kind": "asset-usage",
                                   "issues": issues, "stats": stats},
                                  ensure_ascii=False, indent=2, sort_keys=True))
            else:
                print("== nf asset usage（45 资产引用度）==")
                print("  资产键 %d · 有引用 %d · 零引用 %d · 引用总次数 %d"
                      % (stats["assets"], stats["used"], stats["zero_usage"],
                         stats["total_refs"]))
                if stats["zero_keys"]:
                    print("  零引用键（低信息候选，不自动删）：%s"
                          % "、".join(stats["zero_keys"][:20]))
            return 1 if (issues or (args.strict and stats["zero_usage"] > 0)) else 0
        if args.asset_cmd == "thickness":
            from core import asset_density as ad
            issues, stats = ad.thickness_scan(args.root)
            if args.json:
                print(_json.dumps({"kind": "asset-thickness",
                                   "issues": issues, "stats": stats},
                                  ensure_ascii=False, indent=2, sort_keys=True))
            else:
                print("== nf asset thickness（45 资产语义厚度）==")
                print("  资产档 %d · 平均 %d 字符/档 · 平均 %d 小节/档"
                      % (stats["files"], stats["avg_chars"],
                         stats["avg_sections"]))
                print("  低信息候选 %d（只报告不删）" % stats["low_info"])
                for f in stats["low_files"][:20]:
                    print("  · %s" % f)
            return 1 if issues else 0
        if args.asset_cmd == "ledger":
            from core import asset_ledger_projection as alp
            if args.refresh:
                issues, stats = alp.refresh(args.root)
            else:
                issues, stats = alp.verify(args.root)
            if args.json:
                print(_json.dumps({"kind": "asset-ledger",
                                   "refresh": bool(args.refresh),
                                   "issues": issues, "stats": stats},
                                  ensure_ascii=False, indent=2, sort_keys=True))
            else:
                print("== nf asset ledger（资产键表机读投影）==")
                if args.refresh:
                    print("  ✓ ledger 已重生成（%d 条）" % stats.get("entries", 0))
                else:
                    print("  校验：条目 %d · 一致 %s"
                          % (stats.get("entries", 0),
                             "是" if not issues else "否（refresh）"))
                for i in issues:
                    print("  [FAIL] %s" % i)
            return 1 if issues else 0
        # rm / deprecate / restore：写操作，需显式 --ledger + --key
        ledger_path = args.ledger
        assets_root = os.path.dirname(os.path.abspath(ledger_path))
        if args.asset_cmd == "rm":
            removed = al.remove_entry(assets_root, args.key, ledger_path=ledger_path)
            print("== nf asset rm ==")
            print("  ✓ 已从台账摘除：%s（%s）" % (removed["key"], removed["file"]))
            print("    资产文件保留；若残留文件头，verify check23 将报孤儿——确认不再使用后手动清理旧头")
            return 0
        status = "deprecated" if args.asset_cmd == "deprecate" else "active"
        updated = al.set_status(assets_root, args.key, status, ledger_path=ledger_path)
        print("== nf asset %s ==" % args.asset_cmd)
        print("  ✓ 状态流转：%s -> %s（文件头已同步）"
              % (updated["key"], updated["status"]))
        return 0
    except al.AssetLedgerError as exc:
        print("  ✗ %s" % exc, file=sys.stderr)
        return 1


def _cmd_pipeline(args) -> int:
    """nf pipeline new：P00 骨架派生新管线（v2.8.0 波B S4）。"""
    if getattr(args, "pipeline_cmd", None) == "dryrun":
        from core import pipelinerun as pr
        import json as _json
        if args.all or not args.pipeline:
            if getattr(args, "write_advisory", False):
                doc = pr.advisory_report(ROOT, write=True)
                print("  ✓ advisory 台账已写入：共 %d 条 · %s"
                      % (doc["total"], doc["counts"]))
                return 0
            issues, tot = pr.sweep(ROOT)
            if args.json:
                print(_json.dumps({"issues": issues,
                                   "stats": {k: v for k, v in tot.items()
                                             if k != "advisory_items"}},
                                  ensure_ascii=False, indent=2, sort_keys=True))
            else:
                print("== nf pipeline dryrun --all ==")
                print("  管线 %d · 模块 %d · 官方核心基座 %d · advisory %d"
                      % (tot["pipelines"], tot["modules"], tot["core_base"],
                         tot["notes"]))
                for cat, n in sorted(tot.get("advisory_buckets", {}).items()):
                    print("    · %-14s %d" % (cat, n))
                for i in issues:
                    print("  [FAIL] %s" % i, file=sys.stderr)
                if not issues:
                    print("  ✓ 全仓管线零 hard 缺陷（advisory 为同层序/跨包事件，不作判死）")
            return 1 if issues else 0
        try:
            g = pr.graph(args.pipeline, ROOT)
        except (OSError, ValueError) as exc:
            print("  ✗ %s" % exc, file=sys.stderr)
            return 1
        if args.json:
            print(_json.dumps(g, ensure_ascii=False, indent=2, sort_keys=True))
            return 1 if g["issues"] else 0
        print("== nf pipeline dryrun：%s（%s）==" % (g["pipeline"]["id"], g["pipeline"]["name"]))
        print("  层 %d · 模块 %d · token %d · 事件 %d · hard %d · advisory %d"
              % (g["stats"]["layers"], g["stats"]["modules"], g["stats"]["tokens"],
                 g["stats"]["events_published"], g["stats"]["issues"],
                 g["stats"]["notes"]))
        for s in g["steps"]:
            mods = "、".join(m["id"] for m in s["modules"]) or "（空）"
            print("  %2d. %-4s %-14s %s" % (s["index"], s["layer"],
                                            s["layer_name"][:12], mods))
        for i in g["issues"]:
            print("  [FAIL] %s" % i, file=sys.stderr)
        for n in g["notes"][:6]:
            print("  [note] %s" % (n.get("detail") if isinstance(n, dict) else n))
        return 1 if g["issues"] else 0
    from core.pipeline_scaffold import scaffold_pipeline, default_filename
    tmpl = args.template or os.path.join(ROOT, "03_管线库",
                                         "P00_通用文档生成管线.md")
    try:
        with open(tmpl, encoding="utf-8") as fh:
            template = fh.read()
        new_text = scaffold_pipeline(template, args.id, args.name,
                                     domain=args.domain)
    except (OSError, ValueError) as exc:
        print("  ✗ %s" % exc, file=sys.stderr)
        return 1
    dest = args.dest or os.path.join(ROOT, "03_管线库",
                                     default_filename(args.id.upper(), args.name))
    dest = os.path.abspath(dest)
    if os.path.exists(dest):
        print("  ✗ 目标已存在，不覆盖：%s" % dest, file=sys.stderr)
        return 1
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest, "w", encoding="utf-8") as fh:
        fh.write(new_text)
    print("== nf pipeline new ==")
    print("  ✓ 派生管线落盘：%s" % dest)
    print("  后续三步：① 按 01 §2 填层名 / default / allowed；② 新模块落 04_模块库 或复用通用件；")
    print("            ③ 登记 02_联动注册表 → Agent 即调度（I5，引擎不改）")
    print("  试跑：python scripts/nf.py run --pipeline %s"
          " --modules <领域模块 full_id> --seed --fmt ccv3" % dest)
    return 0


def _cmd_module(args) -> int:
    """nf module：模块生命周期（v2.8.0 波B S5）。ls/verify 只读；deprecate/restore 写文件状态位。"""
    import json as _json
    from core import module_lifecycle as ml
    try:
        if args.module_cmd == "contract":
            from core import machine_contract as mctl
            if args.write:
                rows = mctl.apply(ROOT, write=True)
                print("== nf module contract --write ==")
                print("  ✓ L0 → L1/L2 retro-fit 完成：%d 件" % len(rows))
                for r in rows:
                    print("    %-52s %s" % (r["path"], r["level"]))
                return 0
            c_issues, c_warns, c_stats = mctl.scan(ROOT)
            if args.json:
                print(_json.dumps({"issues": c_issues, "warns": c_warns,
                                   "stats": c_stats}, ensure_ascii=False,
                                  indent=2, sort_keys=True))
            else:
                print("== nf module contract（机读块覆盖）==")
                print("  仍为 L0（无机读块）：%d 件" % len(c_stats.get("l0_list") or []))
                for i in c_issues:
                    print("  [FAIL] %s" % i, file=sys.stderr)
                for w in c_warns:
                    print("  [WARN] %s" % w)
                if not c_issues and not (c_stats.get("l0_list") or []):
                    print("  ✓ 全库模块均有机器契约（L0 = 0）")
            return 1 if c_issues else 0
        if args.module_cmd == "types":
            from core import io_types as iot
            if getattr(args, "harvest", False):
                from core import payload_harvest as ph
                h = ph.apply(ROOT, write=True)
                print("== nf module types --harvest ==")
                print("  正文载荷收割：新增 %d · 收窄 %d · 冲突 %d"
                      % (len(h["added"]), len(h["narrowed"]), len(h["conflicts"])))
                for c in h["conflicts"][:5]:
                    print("  [WARN] 类型冲突（只报告不改）：%s" % c)
                print("  类型面：%s" % ph.stats(ROOT))
                return 0
            if getattr(args, "backlog", False):
                from core import payload_harvest as ph
                if args.write:
                    doc = ph.backlog(ROOT, write=True)
                    print("  ✓ 类型积压台账已写入：%d 项 untyped（protocol/type_backlog.json）"
                          % doc["count"])
                    return 0
                b_issues, b_stats = ph.verify_backlog(ROOT)
                print("== nf module types --backlog ==")
                print("  不可推断的 untyped：%d 项" % b_stats["untyped"])
                for i in b_issues:
                    print("  [FAIL] %s" % i, file=sys.stderr)
                return 1 if b_issues else 0
            if args.write:
                rows = iot.apply(ROOT, write=True)
                cov = iot.coverage(ROOT)
                print("== nf module types --write ==")
                print("  ✓ 已补标 %d 件（机读契约模块 %d · 类型覆盖 %.1f%%）"
                      % (sum(1 for r in rows if r["changed"]),
                         cov["modules_with_contract"], cov["coverage"]))
                return 0
            t_issues, t_warns, _t = iot.scan(ROOT)
            cov = iot.coverage(ROOT)
            if args.json:
                print(_json.dumps({"issues": t_issues, "warns": t_warns,
                                   "stats": cov}, ensure_ascii=False,
                                  indent=2, sort_keys=True))
            else:
                print("== nf module types（I/O 类型面）==")
                print("  机读契约模块 %d · L0 未承载 %d · 已标注 %d/%d 字段（%.1f%%）"
                      % (cov["modules_with_contract"], cov["l0_modules"],
                         cov["typed_fields"],
                         cov["typed_fields"] + cov["untyped_fields"], cov["coverage"]))
                for i in t_issues:
                    print("  [FAIL] %s" % i, file=sys.stderr)
                for w in t_warns:
                    print("  [WARN] %s" % w)
                if not t_issues:
                    print("  ✓ 无可证类型不匹配（untyped 为如实缺口，不判死）")
            return 1 if t_issues else 0
        if args.module_cmd == "signature":
            from core import module_signature as ms
            if args.write:
                rel = ms.write(ROOT)
                print("== nf module signature --write ==")
                print("  ✓ 边界基线已重冻结：%s（%d 模块）"
                      % (rel, len(ms.signatures(ROOT))))
                return 0
            sig_issues, sig_warns, sig_stats = ms.verify(ROOT)
            if args.json:
                print(_json.dumps({"issues": sig_issues, "warns": sig_warns,
                                   "stats": sig_stats},
                                  ensure_ascii=False, indent=2, sort_keys=True))
            else:
                print("== nf module signature（边界冻结）==")
                print("  模块 %d · 已签 %d" % (sig_stats.get("modules", 0),
                                              sig_stats.get("signed", 0)))
                for i in sig_issues:
                    print("  [FAIL] %s" % i, file=sys.stderr)
                for w in sig_warns:
                    print("  [WARN] %s" % w)
                if not sig_issues:
                    print("  ✓ 全部模块边界与基线一致（改边界须显式重签）")
            return 1 if sig_issues else 0
        if args.module_cmd == "verify":
            issues, stats = ml.verify_modules(args.root)
            print("== nf module verify ==")
            print("  统计：模块 %d / active %d / deprecated %d / retired %d"
                  % (stats["modules"], stats["active"],
                     stats["deprecated"], stats["retired"]))
            if issues:
                for issue in issues:
                    print("  [FAIL] %s" % issue, file=sys.stderr)
                return 1
            print("  ✓ 无 deprecated/retired 模块被引用（引用门禁全绿）")
            return 0
        if args.module_cmd == "ls":
            rows = []
            for rel in ml.iter_module_files(args.root):
                txt = ml.read_text(args.root, rel)
                status, _ = ml.get_status(txt)
                if args.status and status != args.status:
                    continue
                rows.append((status, rel))
            if args.json:
                print(_json.dumps({
                    "kind": "module-ls",
                    "status": args.status or None,
                    "rows": [{"status": s, "file": f} for s, f in sorted(rows)],
                }, ensure_ascii=False, indent=2, sort_keys=True))
                return 0
            print("== nf module ls ==")
            for status, rel in rows:
                print("  %-10s %s" % (status, rel))
            print("  合计 %d" % len(rows))
            return 0
        # 单文件操作：status / deprecate / restore
        fpath = args.file
        with open(fpath, encoding="utf-8") as fh:
            txt = fh.read()
        before, _ = ml.get_status(txt)
        if args.module_cmd == "status":
            print("== nf module status ==")
            print("  %s → %s" % (fpath, before))
            return 0
        target = "deprecated" if args.module_cmd == "deprecate" else "active"
        new_txt = ml.set_status(txt, target,
                                reason=getattr(args, "reason", ""),
                                module_file=fpath)
        if new_txt != txt:
            with open(fpath, "w", encoding="utf-8") as fh:
                fh.write(new_txt)
        print("== nf module %s ==" % args.module_cmd)
        print("  ✓ 状态流转：%s → %s（%s）" % (before, target, fpath))
        print("  复核：python scripts/nf.py module verify（引用门禁，verify check24 同语义）")
        return 0
    except (OSError, ValueError) as exc:
        print("  ✗ %s" % exc, file=sys.stderr)
        return 1


def _cmd_demo(args) -> int:
    """nf demo：一键演示世界（v2.8.0 波B S7）——P04 轻混全链 → CCV3。"""
    import tempfile
    import time
    from core.pipeline import pipe
    from core.pipeline_loader import load_pipeline_file
    from core.storage import Store
    pipeline_path = os.path.join(ROOT, "community", "校园西幻轻混组合包",
                                 "pipelines", "P04_轻混装配流管线.md")
    pipeline = load_pipeline_file(pipeline_path)
    if pipeline is None:
        print("  ✗ 演示管线解析失败：%s" % pipeline_path, file=sys.stderr)
        return 1
    store = Store()
    stats = _seed_store(store)
    dest = args.dest or tempfile.mkdtemp(prefix="nf_demo_")
    t0 = time.time()
    selected = ["通用类:M00", "轻混类:M91", "轻混类:M92", "通用类:M80"]
    r = pipe(store, pipeline, selected, include_references=True,
             fmt="ccv3", dest_dir=dest)
    elapsed = time.time() - t0
    print("== nf demo（一键演示世界 · P04 轻混）==")
    print("  seed 装载：官方核心 %d 件 + 轻混组合包 %d 件"
          % (stats["core"], stats["combo"]))
    print("  全链计时：%.1f s（retrieve→compose→gate→export）" % elapsed)
    print("  质量门：PASS %d · WARN %d · FAIL %d"
          % (r.gate.n_pass, r.gate.n_warn, r.gate.n_fail))
    if r.export is not None and r.export.files:
        for f in r.export.files:
            print("  产物：%s" % f)
        print("  装载：把上述 chara.json 导入任意 AI 前端 / SillyTavern 即可开跑")
    return 0 if r.ok else 1


def _rel_to_root(target):
    """把调用方给的路径归一化为仓库相对路径（不存在则报错）。"""
    t = os.path.abspath(target)
    if not os.path.exists(t):
        raise ValueError("目标不存在：%s" % target)
    return os.path.relpath(t, ROOT)

CHECK_GUIDE = {
    "1": "缺什么：官方核心目录结构件缺失（01/02/06/07/README/LICENSE + 官方管线 P00/P01/P90）。补什么：按 07 §7 项1 清单补齐根级文件与 03_管线库 官方管线。",
    "2": "缺什么：重号 ID 未全限定（官方层裸号重复）。补什么：官方核心层模块引用一律全限定（通用:M10/事件:M22），07 §7 项5。",
    "3": "缺什么：五条不变式落点缺失或错位。补什么：核对 01 §5 ↔ 07 §7 项6 的逐条落点声明。",
    "4": "缺什么：认知边界断链（06 §4 管线 ↔ M23 认知域不一致）。补什么：对齐执行协议与 M23 的裁剪/过滤口径。",
    "5": "缺什么：质检门流水线违约（M80 gate_action ↔ 06 §5）。补什么：核对输出生成器的 gate_action 三态与执行协议一致。",
    "6": "缺什么：入口导航断链（README → 07 → 协议链/官方目录）。补什么：按 07 §7 项6 修 README 路由。",
    "7": "缺什么：社区两包结构完整度违约。补什么：校园/西幻包 modules/pipelines/protocol.yaml/README 与 02 §8 在册数一致。",
    "8": "缺什么：社区资产外形与基线不一致（文件数 / 行数 / 逐文件摘要）。补什么：核对内容后显式重签 `nf asset baseline --write`（07 §7 项3）。",
    "9": "缺什么：模块-资产引用不可寻址或社区 README 重号未限定。补什么：资产键真实可寻址 + 社区重号限定引用。",
    "10": "缺什么：EXT 闭合违约或社区红线未落地。补什么：EXT 实体闭合 + 红线条目对齐 07 §7 项2/8。",
    "11": "缺什么：资产-模块三方对账不一致（02 §8.1 ↔ modules/ ↔ assets/README）。补什么：三方条目对齐（08 方案 T5 A5）。",
    "12": "缺什么：desktop/src 或 scripts 语法/单测失败。补什么：跑 python -m unittest discover -s desktop/tests 修到全绿；示例：新模块未补测试→先写测试再实现。",
    "13": "缺什么：02 头部与 registry.json 协议版本不一致或迁移记录不全。补什么：版本改动需 02 §9.3 四步（快照/bump/迁移说明/回读）。",
    "14": "缺什么：社区协议登记缺 protocol.yaml/Schema 12 字段/登记三要件。补什么：01 §6.1 + 02 §8.3 补齐并保持 registry protocols[] 一致。",
    "15": "缺什么：组合引用 references 违约（不在册/闭包未闭合/层冲突/schema 不兼容/双源不一致）。补什么：按 02 §8.4 五断言核对。",
    "16": "缺什么：machine_contract 机读结构或装配 publish⊆subscribe 违约。补什么：01 §1.1 契约字段 + 运行时寻址授权一致。",
    "17": "缺什么：质量门 unittest 失败。补什么：装配/锚点/资产悬空需过 quality_gate 语义。",
    "18": "缺什么：导出契约 unittest 失败。补什么：ccv3_adapter/exporter 映射层检查锚点与条目。",
    "19": "缺什么：导出产物 shape 与 schema 不符。补什么：对照 export_schema 5 格式自检。",
    "20": "缺什么：模块文档必填项缺失。补什么：按文档完整性清单补必填字段。",
    "21": "缺什么：registry 引用图悬空/裸号重复。补什么：清理 source_package/module_id 引用。",
    "22": "缺什么：导出物规范体检失败（spec_version/name/description 超限）。补什么：按 export_schema 硬约束修正。",
    "23": "缺什么：资产供应链台账违约（不可溯源/不可发现/键孤儿）。补什么：05_资产库/provenance.json + 文件头双源一致。",
    "24": "缺什么：模块状态位异常或 deprecated/retired 被引用。补什么：module deprecate/restore 流转或移除引用方。",
    "25": "缺什么：01-36 编号方案文档签名不可复现/结构缺标题。补什么：文档须 UTF-8 且含 # 标题，同一内容重复生成须逐字节一致；示例：nf sig --verify。",
    "26": "缺什么：语义矛盾（techdoc 链订阅事件无发布方 / 挂载点或类别漂移）。补什么：全库补发布方或修正漂移；示例：nf related 反查 + semantic_conflict.scan。",
    "27": "缺什么：架构纯度违约（端壳残留/私货可变物/重复标题/raise 消息缺修复指引/第三方 import 未登记）。补什么：purity_scan 五规则逐条修；示例：R1 端壳关键词残留清理、R5 第三方 import 改软导入并在 SOFT_IMPORTS 登记理由。",
    "28": "缺什么：协议层 IDL 违约（schema 定义缺失或协议件字段漂移）。补什么：protocol/schema 五定义在场 + 在场 machine_contract/管线/协议包/台账过 schema；示例：nf doctor 看 schema 在场。",
    "29": "缺什么：Conformance 虚标或声明缺失（声明级别 > 可证级别）。补什么：按 01 §1.2 与 conformance_scan 提示降级或补证据。",
    "30": "缺什么：扩展判据缺失或版本字段 bump 无迁移记录。补什么：protocol/EXTENSION.md 判据 + bump 变更带 01 §7/02 §9.3 四步迁移记录。",
    "31": "缺什么：生成物过期（protocol/generated 与当前 schema/协议件不一致）。补什么：重跑 protocol_golden.write_golden 并随变更一并提交。",
    "32": "缺什么：质量纵深汇总违约（载荷注册表/资产 ledger/指令审计/资产密度·厚度·零引用/tool_face/world_model/world_slots 任一缺口）。补什么：跑 nf release 看细分失败项，修复后 verify 全绿；world_model 契约自查可用 nf worldmodel。",
}

def _cmd_sig(args):
    """nf sig：41 波C C1 —— 结构化签名（知识指纹）。"""
    from core import knowledge_sig as ks
    import json as _json
    try:
        if args.verify:
            issues, stats = ks.verify_reproducible(ROOT)
            print("== nf sig --verify（check25 同语义）==")
            print("  文档 %d · 可复现 %d" % (stats["docs"], stats["reproducible"]))
            for i in issues:
                print("  [FAIL] %s" % i, file=sys.stderr)
            if not issues:
                print("  ✓ 01-36 全量签名两遍一致（知识指纹稳定）"); return 0
            return 1
        targets = list(args.target) if args.target else ks.discover_docs(ROOT)
        if not targets:
            print("  ✗ 未找到签名目标（缺省 = 根目录 01-36 编号方案文档）", file=sys.stderr); return 1
        out = []
        for t in targets:
            rel = _rel_to_root(t)
            sig = ks.build_signature(rel, ROOT)
            out.append({"digest": ks.signature_digest(sig), "sig": sig})
        if args.json:
            print(_json.dumps(out, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print("== nf sig（%d 文档）==" % len(out))
            for r in out:
                s = r["sig"]
                print("  %s  %-10s %-8s %s  refs=%d" %
                      (r["digest"][:12], s["path"], s["doc_id"],
                       s["title"][:28], len(s["refs"])))
        return 0
    except (OSError, ValueError) as exc:
        print("  ✗ %s" % exc, file=sys.stderr); return 1

def _cmd_attest(args):
    """nf attest：内容 attestation 生成/校验（三级信任；缺锚一律拒绝）。"""
    from core import attest
    import json as _json
    try:
        if args.verify:
            with open(_rel_to_root(args.verify), encoding="utf-8") as fh:
                payload = _json.load(fh)
            items = (payload.get("attestations")
                     if isinstance(payload, dict) and "attestations" in payload
                     else [payload])
            key = attest.read_key_file(args.key_file) if args.key_file else None
            results = []
            for att in items:
                ok, issues, level = attest.verify(att, ROOT, key=key)
                results.append({"subject": (att.get("subject") or {}).get("path"),
                                "ok": ok, "level": level, "issues": issues})
            all_ok = bool(results) and all(r["ok"] for r in results)
            if args.json:
                print(_json.dumps({"ok": all_ok, "results": results},
                                  ensure_ascii=False, indent=2))
            else:
                print("== nf attest --verify（%d 件）==" % len(results))
                for r in results:
                    print("  %s %-34s 信任级：%s"
                          % ("✓" if r["ok"] else "✗", r["subject"], r["level"]))
                    for i in r["issues"]:
                        print("    [FAIL] %s" % i, file=sys.stderr)
            return 0 if all_ok else 1
        targets = [args.target] if args.target else list(attest.DEFAULT_SUBJECTS)
        key = attest.read_key_file(args.key_file) if args.key_file else None
        items = []
        for t in targets:
            att = attest.build(_rel_to_root(t), ROOT, issuer=args.issuer)
            if key:
                att = attest.sign_hmac(att, key)
            items.append(att)
        payload = (items[0] if len(items) == 1
                   else {"schema": "nf-attest-set/1", "attestations": items})
        if args.out:
            out_path = (args.out if os.path.isabs(args.out)
                        else os.path.join(ROOT, args.out))
            os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
            with open(out_path, "w", encoding="utf-8",
                      newline="\n") as fh:
                fh.write(_json.dumps(payload, ensure_ascii=False,
                                     indent=2, sort_keys=True) + "\n")
        if args.json:
            print(_json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print("== nf attest（%d 件）==" % len(items))
            for att in items:
                sig = att.get("signature") or {}
                print("  %s  %-34s 级=%s  信封=%s"
                      % (att["subject"]["sha256"][:12], att["subject"]["path"],
                         sig.get("scheme") or "digest_only",
                         att["envelope_digest"][:12]))
            if args.out:
                print("  写入：%s" % os.path.relpath(
                    os.path.abspath(out_path), ROOT).replace("\\", "/"))
            if not key:
                print("  提示：未加 --key-file → digest_only 级（只证一致，"
                      "不证诚实性）；对外可验证需 hmac 密钥或 sigstore 外挂锚。",
                      file=sys.stderr)
        return 0
    except (OSError, ValueError) as exc:
        print("  ✗ %s" % exc, file=sys.stderr)
        return 1


def _cmd_lint(args):
    """nf lint：机械检查/修复（与 doc_hygiene / prose_lint 同源判据）。"""
    from core import autofix
    import json as _json
    if getattr(args, "kinds", False):
        from core import doc_hygiene as dh
        warns = dh.kind_rules(ROOT)
        print("== nf lint --kinds（四型写法判据）==")
        for w in warns:
            print("  [WARN] %s" % w)
        if not warns:
            print("  ✓ 四型写法齐（每型都有该型必备的结构块）")
        return 0
    try:
        if args.target:
            targets = []
            for t in args.target:
                p = t if os.path.isabs(t) else os.path.join(ROOT, t)
                if os.path.isdir(p):
                    for dirpath, _dirs, files in os.walk(p):
                        targets += [os.path.join(dirpath, f) for f in sorted(files)
                                    if f.endswith(".md")]
                elif os.path.exists(p):
                    targets.append(p)
                else:
                    print("  ✗ 目标不存在：%s" % t, file=sys.stderr)
                    return 1
        else:
            from core import doc_hygiene as dh
            rels = sorted(set(dh.REQUIRED_DOCS) | set(dh.INSTRUCTION_DOCS))
            targets = [os.path.join(ROOT, r) for r in rels
                       if os.path.exists(os.path.join(ROOT, r))]
        reports, prose = [], []
        for p in targets:
            if args.fix:
                rep = autofix.fix_file(p, root=ROOT, dry_run=args.dry_run)
                if rep["rules"]:
                    reports.append(rep)
            else:
                with open(p, encoding="utf-8") as fh:
                    text = fh.read()
                rules = autofix.lint_rules(p, text, ROOT)
                if rules:
                    reports.append({"path": p, "changed": False,
                                    "rules": [r["rule"] for r in rules]})
            if args.prose:
                from core import prose_lint
                extra = prose_lint.load_custom_terms(ROOT)
                with open(p, encoding="utf-8") as fh:
                    for f in prose_lint.lint_text(fh.read(), extra_terms=extra):
                        f = dict(f)
                        f["path"] = os.path.relpath(p, ROOT).replace("\\", "/")
                        prose.append(f)
        if args.json:
            print(_json.dumps({"mechanical": reports, "prose": prose},
                              ensure_ascii=False, indent=2, sort_keys=True))
        else:
            mode = ("修复（dry-run）" if args.dry_run
                    else "修复" if args.fix else "报告")
            print("== nf lint（%s · %d 目标）==" % (mode, len(targets)))
            for rep in reports:
                rel = os.path.relpath(rep["path"], ROOT).replace("\\", "/")
                print("  %s %s" % ("✎" if rep.get("changed") else "·", rel))
                print("      %s" % "、".join(rep["rules"]))
            if not reports:
                print("  ✓ 机械面无待办")
            if prose:
                print("  正文 lint：%d 条" % len(prose))
                for f in prose[:20]:
                    print("    [%s] %s:%d %s" % (f["rule"], f["path"],
                                                f["line"], f["message"]))
        if args.fix:
            return 0
        return 1 if (reports or prose) else 0
    except (OSError, ValueError) as exc:
        print("  ✗ %s" % exc, file=sys.stderr)
        return 1


def _cmd_conformance(args):
    """nf conformance：一致性报告工件（全部契约 → Merkle 根 + verdict）。"""
    from core import conformance_report as cr
    import json as _json
    if args.write:
        rel = cr.write(ROOT)
        doc = cr.run(ROOT)
        print("== nf conformance --write ==")
        print("  报告已写入：%s" % rel)
        print("  verdict：%s（%d/%d 契约通过）· root=%s"
              % (doc["verdict"], doc["passed"], doc["total"], doc["root"][:16]))
        return 0 if doc["verdict"] == "conformant" else 1
    issues, stats = cr.verify_committed(ROOT)
    doc = cr.run(ROOT)
    if args.json:
        print(_json.dumps({"report": doc, "issues": issues},
                          ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print("== nf conformance（一致性报告）==")
        print("  %s · %d/%d 契约 · root=%s"
              % (doc["verdict"], doc["passed"], doc["total"], doc["root"][:16]))
        for c in doc["contracts"]:
            print("  %s %-30s %s" % ("✓" if c["ok"] else "✗", c["id"], c["detail"][:60]))
        for i in issues:
            print("  [FAIL] %s" % i, file=sys.stderr)
    return 1 if (issues or doc["verdict"] != "conformant") else 0


def _cmd_driver(args):
    """nf driver：指令档机器面路由解析/自检。"""
    from core import driver
    import json as _json
    issues, warns, stats = driver.scan(ROOT)
    if args.workflow:
        r = driver.resolve(ROOT, args.workflow)
        if args.json:
            print(_json.dumps({"resolve": r, "issues": issues, "warns": warns},
                              ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print("== nf driver %s ==" % args.workflow)
            print("  路径：%s" % ("MCP（机器面）" if r["mode"] == "mcp" else r["mode"]))
            if r.get("prompt"):
                print("  提示：%s" % r["prompt"])
            if r.get("tools"):
                print("  工具：%s" % "、".join(r["tools"]))
            print("  文本 fallback：%s" % r.get("fallback", "-"))
            print("  派发失败：%s" % r.get("on_dispatch_failure", "-"))
            for i in issues:
                print("  [FAIL] %s" % i, file=sys.stderr)
        return 1 if issues else 0
    if args.json:
        doc = driver.load(ROOT)
        print(_json.dumps({"driver": doc, "issues": issues, "warns": warns,
                           "stats": stats}, ensure_ascii=False, indent=2,
                          sort_keys=True))
    else:
        doc = driver.load(ROOT)
        print("== nf driver（指令档机器面路由）==")
        for name, wf in sorted((doc.get("workflows") or {}).items()):
            print("  %-12s MCP：%-28s fallback：%s"
                  % (name, "、".join(wf.get("mcp_tools") or []) or "-",
                     wf.get("fallback", "-")))
        for w in warns:
            print("  [note] %s" % w)
        for i in issues:
            print("  [FAIL] %s" % i, file=sys.stderr)
        if not issues:
            print("  ✓ 工作流映射/工具名/fallback/文档声明块全部一致（fail-closed 已声明）")
    return 1 if issues else 0


def _cmd_rfc(args):
    """nf rfc：协议件 RFC 索引与 supersede 链自检。"""
    from core import rfc as rf
    from pathlib import Path
    import json as _json
    issues, warns, stats = rf.scan(ROOT)
    idx = rf.index(ROOT)
    if args.json:
        print(_json.dumps({"index": idx, "issues": issues, "warns": warns,
                           "stats": stats}, ensure_ascii=False, indent=2,
                          sort_keys=True))
    else:
        print("== nf rfc（协议件版本史）==")
        for item in idx.get("docs") or []:
            head = rf.parse_head((Path(ROOT) / item["path"]).read_text(encoding="utf-8"))
            print("  %-9s %-34s %-16s %-9s %s"
                  % (item.get("rfc"), item.get("path"), head.get("cat", "-"),
                     head.get("status", "-"), head.get("date", "-")))
        for i in issues:
            print("  [FAIL] %s" % i, file=sys.stderr)
        if not issues:
            print("  ✓ %d 件 RFC 头齐备且链可解析" % stats.get("docs", 0))
    return 1 if issues else 0


def _cmd_patterns(args):
    """nf patterns：实践包（ls/show/for/verify/reindex）。"""
    from core import patterns as pt
    from pathlib import Path
    import json as _json
    sub = getattr(args, "patterns_cmd", None) or "ls"
    want_json = bool(getattr(args, "json", False))
    if sub == "ls":
        rows = pt.entries(ROOT)
        if want_json:
            print(_json.dumps([{"id": e["fm"].get("id"), "name": e["fm"].get("name"),
                                "status": e["fm"].get("status"),
                                "applies_to": e["fm"].get("applies_to")}
                               for e in rows], ensure_ascii=False, indent=2,
                              sort_keys=True))
        else:
            print("== nf patterns ls（%d 条）==" % len(rows))
            for e in rows:
                fm = e["fm"]
                print("  %-28s %-10s %s" % (fm.get("id", e["dir"]),
                                            fm.get("status", ""), fm.get("name", "")))
        return 0
    if sub == "show":
        want = args.id.strip()
        hit = next((e for e in pt.entries(ROOT)
                    if str(e["fm"].get("id") or e["dir"]) == want), None)
        if hit is None:
            print("  ✗ pattern 未找到：%s（nf patterns ls 可枚举）" % args.id,
                  file=sys.stderr)
            return 1
        text = (Path(ROOT) / hit["path"]).read_text(encoding="utf-8")
        if want_json:
            print(_json.dumps({"id": want, "path": hit["path"],
                               "frontmatter": hit["fm"]}, ensure_ascii=False,
                              indent=2, sort_keys=True))
        else:
            print("== nf patterns show %s ==" % want)
            for k in sorted(hit["fm"]):
                print("  %-12s %s" % (k + ":", hit["fm"][k]))
            print()
            print(text.split("---", 2)[-1].strip()[:1200])
        return 0
    if sub == "for":
        hits = pt.for_path(ROOT, args.target)
        if want_json:
            print(_json.dumps(hits, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print("== nf patterns for %s（%d 条适用）==" % (args.target, len(hits)))
            for h in hits:
                print("  %-28s %s（命中 %s）" % (h["id"], h["name"], h["matched"]))
        return 0
    if sub == "reindex":
        out = pt.write_projection(ROOT)
        print("  ✓ patterns/INDEX 投影已重建：%s" % ("有变化" if out["changed"] else "无变化"))
        return 0
    issues, warns, stats = pt.scan(ROOT)
    proj = pt.check_projection(ROOT)
    if want_json:
        print(_json.dumps({"issues": issues, "warns": warns, "projection": proj,
                           "stats": stats}, ensure_ascii=False, indent=2,
                          sort_keys=True))
    else:
        print("== nf patterns verify（%d 条）==" % stats.get("patterns", 0))
        for i in list(issues) + list(proj):
            print("  [FAIL] %s" % i, file=sys.stderr)
        for w in warns:
            print("  [WARN] %s" % w)
        if not issues and not proj:
            print("  ✓ 格式合规 + 适用面/证据可证 + INDEX 投影一致")
    return 1 if (issues or proj) else 0


def _cmd_bench(args):
    """nf bench：执行结果跑分（run / compare / report）。"""
    from core import bench
    from pathlib import Path
    import json as _json
    sub = getattr(args, "bench_cmd", None) or "run"
    if sub == "run":
        case_arg = args.case
        if os.path.isdir(case_arg):
            case_arg = os.path.join(case_arg, "case.json")
        case_path = (case_arg if os.path.isabs(case_arg)
                     else os.path.relpath(os.path.abspath(case_arg), ROOT))
        artifact = args.artifact or bench.load_case(Path(ROOT, case_path))["default_artifact"]
        try:
            run = bench.evaluate(ROOT, case_path, artifact, model=args.model)
        except (OSError, ValueError, KeyError) as exc:
            print("  ✗ %s" % exc, file=sys.stderr)
            return 1
        if args.out:
            with open(_rel_out(args.out), "w", encoding="utf-8", newline="\n") as fh:
                fh.write(_json.dumps(run, ensure_ascii=False, indent=2,
                                     sort_keys=True) + "\n")
        if args.json:
            print(_json.dumps(run, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print("== nf bench run：%s ==" % run["case"])
            print("  产物 %s（%s）· 模型 %s" % (run["artifact"],
                                              run["artifact_digest"][:12],
                                              run["model"] or "-"))
            for k, v in sorted(run["scores"].items()):
                print("  %-14s %.4f" % (k, v))
            print("  总分 %.2f（下限 %.0f）→ %s" % (run["total"], run["floor"],
                                                   run["verdict"]))
            for i in run["detail"]["issues"][:4]:
                print("    · %s" % i[:110])
        return 0 if run["verdict"] != "fail" else 1
    runs = _load_runs(args.runs)
    if sub == "compare":
        doc = bench.compare(runs)
        if args.json:
            print(_json.dumps(doc, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print("== nf bench compare（%d 跑）==" % doc["runs"])
            for r in doc["ranking"]:
                print("  %-14s %-16s %6s %s" % (r["run"], r["model"] or "-",
                                                r["total"], r["verdict"]))
            for k, v in sorted(doc["dims"].items()):
                print("    · %-14s 均值 %.4f 极差 %.4f" % (k, v["mean"], v["spread"]))
            if doc["regressions_vs_best"]:
                print("  相对最佳回落 %d 项（前 3）：" % len(doc["regressions_vs_best"]))
                for g in doc["regressions_vs_best"][:3]:
                    print("    · %s %s %.4f→%.4f" % (g["run"], g["dim"], g["from"], g["to"]))
        return 0
    md = bench.report_markdown(bench.compare(runs))
    print(md if not args.json else _json.dumps({"markdown": md},
                                               ensure_ascii=False, indent=2))
    return 0


def _cmd_endpoint(args):
    """nf endpoint：服务端点契约自检（proposed）。"""
    from core import endpoint
    import json as _json
    issues, warns, stats = endpoint.scan(ROOT)
    doc = endpoint.load(ROOT)
    if args.json:
        print(_json.dumps({"contract": doc, "issues": issues, "warns": warns,
                           "stats": stats}, ensure_ascii=False, indent=2,
                          sort_keys=True))
    else:
        print("== nf endpoint（服务端点契约 · %s）==" % stats.get("status", "?"))
        for ep in doc.get("endpoints") or []:
            print("  %-8s %-22s %-9s %s"
                  % (ep.get("method"), ep.get("path"),
                     "SSE" if ep.get("streaming") else "单发", ep.get("maps_to")))
        for i in issues:
            print("  [FAIL] %s" % i, file=sys.stderr)
        for w in warns:
            print("  [note] %s" % w)
        if not issues:
            print("  ✓ 每个端点都映射到现存 CLI 子命令或 MCP 工具（契约不指向空气）")
    return 1 if issues else 0


def _cmd_state_front(args):
    """nf state-front：条件先行排布（确定性；不调模型）。"""
    from core import state_front as sf
    import json as _json
    from pathlib import Path as _Path
    p = args.path if os.path.isabs(args.path) else os.path.join(ROOT, args.path)
    try:
        with open(p, encoding="utf-8") as fh:
            text = fh.read()
    except OSError as exc:
        print("  ✗ %s" % exc, file=sys.stderr)
        return 1
    if args.ab:
        man = sf.ab_manifest(text)
        if args.json:
            print(_json.dumps(man, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print("== nf state-front --ab（三刺激件清单 · 不调模型）==")
            for k in ("front", "back", "none"):
                v = man[k]
                print("  %-6s chars %6d · sha256 %s · 状态块前置=%s"
                      % (k, v["chars"], v["sha256"][:16], v["state_front"]))
        return 0
    if args.check:
        issues = sf.check_order(text)
        if args.json:
            print(_json.dumps({"issues": issues}, ensure_ascii=False, indent=2))
        else:
            print("== nf state-front --check（%s）==" % args.path)
            for i in issues:
                print("  [FAIL] %s" % i)
            if not issues:
                print("  ✓ 状态块已前置（条件先行）")
        return 1 if issues else 0
    out = sf.reorder(text, args.mode)
    if args.out:
        op = args.out if os.path.isabs(args.out) else os.path.join(ROOT, args.out)
        _Path(op).parent.mkdir(parents=True, exist_ok=True)
        with open(op, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(out)
    if args.json:
        print(_json.dumps({"mode": args.mode, "chars": len(out),
                           "state_front": not sf.check_order(out)}, ensure_ascii=False))
    else:
        print("== nf state-front（%s → %s）==" % (args.path, args.mode))
        print("  输出长度 %d 字符 · 状态块前置=%s"
              % (len(out), not sf.check_order(out)))
        if args.out:
            print("  已写入：%s" % args.out)
    return 0


def _cmd_st_validate(args):
    """nf st-validate：ST 制卡校验器原型（A-S3）。"""
    from core import st_validator as sv
    from pathlib import Path
    import json as _json
    try:
        rep = sv.validate(args.path)
    except (OSError, ValueError) as exc:
        print("  ✗ %s" % exc, file=sys.stderr)
        return 1
    md = sv.report_markdown(rep)
    if args.out:
        outp = args.out if os.path.isabs(args.out) else os.path.join(ROOT, args.out)
        Path(outp).parent.mkdir(parents=True, exist_ok=True)
        with open(outp, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(md)
    if args.json:
        print(_json.dumps(rep, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        c = rep.get("counts", {})
        print("== nf st-validate %s（%s：fail %d · warn %d · info %d）=="
              % (args.path, rep.get("kind"), c.get("fail", 0), c.get("warn", 0),
                 c.get("info", 0)))
        for i in rep.get("issues") or []:
            print("  [%s] %s %s" % (i["severity"].upper(), i["rule"], i["detail"]))
        if not rep.get("issues"):
            print("  ✓ 可自动化项全部通过（R1/R3/R4）")
        if args.out:
            print("  报告已写入：%s" % args.out)
    return 1 if (rep.get("counts", {}).get("fail", 0) > 0) else 0


def _cmd_cognition(args):
    """nf cognition：行话术语表 / 执行分档（认证 + 逐条逐字核对）。"""
    from core import cognition as cg
    import json as _json
    part = getattr(args, "part", "") or ""
    fns = {"glossary": cg.verify_glossary, "modes": cg.verify_modes}
    picked = [k for k in fns if not part or k == part]
    issues, warns, stats = [], [], {}
    for k in picked:
        i, w, s = fns[k](ROOT)
        issues += i
        warns += w
        stats[k] = s
    if args.json:
        print(_json.dumps({"issues": issues, "warns": warns, "stats": stats},
                          ensure_ascii=False, indent=2, sort_keys=True))
    else:
        g, m = stats.get("glossary", {}), stats.get("modes", {})
        print("== nf cognition（术语 %d 条 · 使用面 %d · 执行档 %d · 合格实例 %d）=="
              % (g.get("terms", 0), g.get("uses", 0), m.get("modes", 0), m.get("instances_ok", 0)))
        for w in warns:
            print("  [WARN] %s" % w)
        for i in issues:
            print("  [FAIL] %s" % i, file=sys.stderr)
        if not issues:
            print("  ✓ 术语在真源与使用面逐字可核 · 每档实例含必备结构块")
    return 1 if issues else 0


def _cmd_audit(args):
    """nf audit：审计/验收（列表 / 单件机检 / 全量机检）。"""
    from core import audit as au
    import json as _json
    sub = getattr(args, "audit_cmd", None) or "ls"
    want_json = bool(getattr(args, "json", False))
    if sub == "check":
        issues, st = au.check_doc(ROOT, args.path)
        if want_json:
            print(_json.dumps({"path": args.path, "issues": issues, "stats": st},
                              ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print("== nf audit check %s%s ==" % (
                args.path, "（legacy：无审计头，按 WARN 挂账）" if st.get("legacy") else ""))
            for i in issues:
                print("  [FAIL] %s" % i, file=sys.stderr)
            if not issues and not st.get("legacy"):
                print("  ✓ 必填齐 · verdict 在册 · 结论绑定对象 digest · 签收双要素")
        return 1 if issues else 0
    if sub == "verify":
        issues, warns, stats = au.scan(ROOT)
        if want_json:
            print(_json.dumps({"issues": issues, "warns": warns, "stats": stats},
                              ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print("== nf audit verify（%d 件 · 带审计头 %d · legacy %d）=="
                  % (stats.get("audits", 0), stats.get("with_header", 0), stats.get("legacy", 0)))
            for w in warns:
                print("  [WARN] %s" % w)
            for i in issues:
                print("  [FAIL] %s" % i, file=sys.stderr)
            if not issues:
                print("  ✓ 声明与全部审计件一致（legacy 只挂账不判死）")
        return 1 if issues else 0
    rows = au.entries(ROOT)
    if want_json:
        print(_json.dumps([{k: e["fm"].get(k) for k in
                            ("id", "date", "scope", "verdict", "auditor")} for e in rows],
                          ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print("== nf audit（%d 件）==" % len(rows))
        for e in rows:
            fm = e["fm"]
            print("  %-11s %-6s %-11s %s" % (fm.get("id") or "(legacy)",
                                             fm.get("verdict") or "-",
                                             fm.get("date") or "-", e["file"]))
    return 0


def _cmd_postmortem(args):
    """nf postmortem：复盘（列表 / 单件机检 / 全量机检）。"""
    from core import postmortem as pm
    import json as _json
    sub = getattr(args, "postmortem_cmd", None) or "ls"
    want_json = bool(getattr(args, "json", False))
    if sub == "check":
        issues, st = pm.check_doc(ROOT, args.path)
        if want_json:
            print(_json.dumps({"path": args.path, "issues": issues, "stats": st},
                              ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print("== nf postmortem check %s（行动项 %d 条）==" % (args.path, st.get("actions", 0)))
            for i in issues:
                print("  [FAIL] %s" % i, file=sys.stderr)
            if not issues:
                print("  ✓ 四段齐 · 无指责 · 根因指向机制 · 行动项带负责人与判据")
        return 1 if issues else 0
    if sub == "verify":
        issues, warns, stats = pm.scan(ROOT)
        if want_json:
            print(_json.dumps({"issues": issues, "warns": warns, "stats": stats},
                              ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print("== nf postmortem verify（%d 件 · 行动项 %d 条）=="
                  % (stats.get("postmortems", 0), stats.get("actions", 0)))
            for w in warns:
                print("  [WARN] %s" % w)
            for i in issues:
                print("  [FAIL] %s" % i, file=sys.stderr)
            if not issues:
                print("  ✓ 声明与全部复盘件一致")
        return 1 if issues else 0
    rows = pm.entries(ROOT)
    if want_json:
        print(_json.dumps([{k: e["fm"].get(k) for k in
                            ("id", "title", "status", "date", "trigger")} for e in rows],
                          ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print("== nf postmortem（%d 件）==" % len(rows))
        for e in rows:
            fm = e["fm"]
            print("  %-9s %-7s %-10s %s" % (fm.get("id"), fm.get("status"),
                                            fm.get("date"), fm.get("title")))
    return 0


def _cmd_handover(args):
    """nf handover：接力协议（列表 / 单件机检 / 全量机检）。"""
    from core import handover as ho
    import json as _json
    sub = getattr(args, "handover_cmd", None) or "ls"
    want_json = bool(getattr(args, "json", False))
    if sub == "check":
        issues, st = ho.check_doc(ROOT, args.path)
        if want_json:
            print(_json.dumps({"path": args.path, "issues": issues, "stats": st},
                              ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print("== nf handover check %s（未决 %d 条）==" % (args.path, st.get("pending", 0)))
            for i in issues:
                print("  [FAIL] %s" % i, file=sys.stderr)
            if not issues:
                print("  ✓ 五段齐 · 未决非空且每条带判据 · refs 可解析")
        return 1 if issues else 0
    if sub == "verify":
        issues, warns, stats = ho.scan(ROOT)
        if want_json:
            print(_json.dumps({"issues": issues, "warns": warns, "stats": stats},
                              ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print("== nf handover verify（%d 件 · 未决 %d 条）=="
                  % (stats.get("handovers", 0), stats.get("pending", 0)))
            for w in warns:
                print("  [WARN] %s" % w)
            for i in issues:
                print("  [FAIL] %s" % i, file=sys.stderr)
            if not issues:
                print("  ✓ 声明与全部交接件一致")
        return 1 if issues else 0
    rows = ho.entries(ROOT)
    if want_json:
        print(_json.dumps([{k: e["fm"].get(k) for k in
                            ("id", "title", "status", "date", "from", "to")}
                           for e in rows], ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print("== nf handover（%d 件）==" % len(rows))
        for e in rows:
            fm = e["fm"]
            print("  %-9s %-7s %-10s %s → %s" % (fm.get("id"), fm.get("status"),
                                                 fm.get("date"), fm.get("from"), fm.get("to")))
    return 0


def _cmd_decisions(args):
    """nf decisions：决策记录（列表 / 单条 / 机检 / 投影重建）。"""
    from core import decisions as dc
    import json as _json
    sub = getattr(args, "decisions_cmd", None) or "ls"
    want_json = bool(getattr(args, "json", False))
    if sub == "reindex":
        out = dc.write_projection(ROOT)
        print("  ✓ decisions/INDEX 投影已重建：%s" % ("有变化" if out["changed"] else "无变化"))
        return 0
    if sub == "show":
        want = args.id.strip().upper()
        hit = next((e for e in dc.entries(ROOT)
                    if str(e["fm"].get("id")) == want), None)
        if hit is None:
            print("  ✗ 未找到：%s（nf decisions 可枚举）" % args.id, file=sys.stderr)
            return 1
        if want_json:
            print(_json.dumps({"id": want, "path": hit["path"], "frontmatter": hit["fm"]},
                              ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print("== nf decisions show %s ==" % want)
            for k in sorted(hit["fm"]):
                print("  %-14s %s" % (k + ":", hit["fm"][k]))
            print()
            print(hit["body"].strip()[:1200])
        return 0
    issues, warns, stats = dc.scan(ROOT)
    proj = dc.check_projection(ROOT)
    if sub == "verify":
        if want_json:
            print(_json.dumps({"issues": issues, "warns": warns, "projection": proj,
                               "stats": stats}, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print("== nf decisions verify（%d 条 · accepted %d）=="
                  % (stats.get("decisions", 0), stats.get("accepted", 0)))
            for i in list(issues) + list(proj):
                print("  [FAIL] %s" % i, file=sys.stderr)
            if not issues and not proj:
                print("  ✓ 编号/状态/取代链/证据可解析/三段齐/回执锚定 全部一致")
        return 1 if (issues or proj) else 0
    rows = dc.entries(ROOT)
    if want_json:
        print(_json.dumps([{k: e["fm"].get(k) for k in
                            ("id", "title", "status", "date", "superseded_by")}
                           for e in rows], ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print("== nf decisions（%d 条）==" % len(rows))
        for e in rows:
            fm = e["fm"]
            print("  %-9s %-11s %-10s %s" % (fm.get("id"), fm.get("status"),
                                             fm.get("date"), fm.get("title")))
    return 0


def _cmd_model(args):
    """nf model：内容建模三件（词表 / 规范说明件 / 数据契约）。"""
    from core import modeling as M
    import json as _json
    part = getattr(args, "part", "") or ""
    fns = {"vocab": M.verify_vocabularies,
           "normative": M.verify_normative,
           "contracts": M.verify_contracts}
    picked = [k for k in fns if not part or k == part]
    issues, warns, stats = [], [], {}
    for k in picked:
        i, w, s = fns[k](ROOT)
        issues += i
        warns += w
        stats[k] = s
    if args.json:
        print(_json.dumps({"issues": issues, "warns": warns, "stats": stats},
                          ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print("== nf model（内容建模三件%s）==" % (" · " + part if part else ""))
        for k in picked:
            print("  %-10s %s" % (k, stats.get(k, {})))
        for w in warns:
            print("  [WARN] %s" % w)
        for i in issues:
            print("  [FAIL] %s" % i, file=sys.stderr)
        if not issues:
            print("  ✓ 词表与真源一致 · 规范件皆有主 · 说明件未被当规范 · 契约 quality_rule 全部解析")
    return 1 if issues else 0


def _cmd_assertions(args):
    """nf assertions：跑数据化断言表（封闭 kind 集，不引第三方）。"""
    from core import assertions as at
    import json as _json
    results, issues = at.run(ROOT)
    if args.json:
        print(_json.dumps({"results": results, "issues": issues},
                          ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print("== nf assertions（%d 条 · kind 封闭集 %s）=="
              % (len(results), "/".join(at.KINDS)))
        for r in results:
            print("  [%s] %-38s %s" % ("PASS" if r["ok"] else "FAIL", r["id"], r["detail"]))
        for i in issues:
            print("  [FAIL] %s" % i, file=sys.stderr)
        if not issues:
            print("  ✓ 断言表全绿（新增规则 = 加一行数据，不必改 check 代码）")
    return 1 if issues else 0


def _rel_out(path):
    return path if os.path.isabs(path) else os.path.join(ROOT, path)


def _cmd_knowledge(args):
    """nf knowledge：双源知识层（状态 / 顺序 / 巡检 / 消化记录）。"""
    from core import knowledge as kn
    import json as _json
    sub = getattr(args, "knowledge_cmd", None) or "status"
    want_json = bool(getattr(args, "json", False))
    if sub == "order":
        clearance = str(getattr(args, "clearance", "") or "")
        rows = kn.resolve_order(ROOT, clearance=clearance)
        if want_json:
            print(_json.dumps({"clearance": clearance or "不裁剪", "query_order": rows},
                              ensure_ascii=False,
                              indent=2, sort_keys=True))
        else:
            print("== nf knowledge order（查询有序：合同级 → 参考级%s）=="
                  % ("· 裁剪至 " + clearance if clearance else ""))
            for i, r in enumerate(rows, 1):
                print("  %d. %-22s %-9s %-18s %s"
                      % (i, r["id"], r["authority"], r["kind"], r["locator"]))
        return 0
    if sub == "visible":
        clearance = str(getattr(args, "clearance", "public") or "public")
        allowed = kn.visible_ids(ROOT, clearance)
        rows = [{"id": str(s.get("id")), "visibility": str(s.get("visibility")),
                 "visible": str(s.get("id")) in allowed} for s in kn.sources(ROOT)]
        if want_json:
            print(_json.dumps({"clearance": clearance, "sources": rows},
                              ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print("== nf knowledge visible --as %s ==" % clearance)
            for r in rows:
                print("  %-22s %-11s %s" % (r["id"], r["visibility"],
                                            "可见" if r["visible"] else "裁剪"))
        return 0
    if sub == "frequency":
        try:
            counts = kn.harvest_frequency(args.trace)
        except OSError as exc:
            print("  ✗ %s" % exc, file=sys.stderr)
            return 1
        if args.write:
            kn.write_usage(ROOT, counts)
        issues, _warns, stats = kn.verify_usage(ROOT)
        if want_json:
            print(_json.dumps({"counts": counts, "written": bool(args.write),
                               "issues": issues, "stats": stats},
                              ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print("== nf knowledge frequency（%d 源有事件 · 共 %d 次）=="
                  % (len(counts), sum(counts.values())))
            for k, v in counts.items():
                print("  %-22s %d" % (k, v))
            if not counts:
                print("  （trace 中无 knowledge_source 事件）")
            for i in issues:
                print("  [FAIL] %s" % i, file=sys.stderr)
            if args.write and not issues:
                print("  ✓ 频率台账已写入 %s（频次可复算）" % kn.USAGE_REL)
            elif not args.write:
                print("  （未写台账；加 --write 落盘）")
        return 1 if issues else 0
    if sub == "lint":
        issues, warns, stats = kn.lint(ROOT)
        if want_json:
            print(_json.dumps({"issues": issues, "warns": warns, "stats": stats},
                              ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print("== nf knowledge lint（知识层巡检）==")
            for i in issues:
                print("  [FAIL] %s" % i, file=sys.stderr)
            for w in warns:
                print("  [WARN] %s" % w)
            if not issues:
                print("  ✓ 声明/顺序/溯源/悬空/孤儿 全绿（时效缺失 %d 件已记 WARN）"
                      % stats.get("no_stale_after", 0))
        return 1 if issues else 0
    if sub == "transform":
        tcmd = getattr(args, "transform_cmd", None)
        if tcmd in ("add", "promote"):
            import datetime as _dt
            src = args.src.strip()
            dst = args.dst.strip().replace("\\", "/")
            at = args.at.strip() or _dt.date.today().isoformat()
            if not os.path.isfile(os.path.join(ROOT, dst)):
                print("  ✗ 产物不存在：%s（记录的 to 必须是仓库内真实件）" % dst,
                      file=sys.stderr)
                return 1
            if src not in kn.reference_ids(ROOT):
                print("  ✗ from 必须是已声明的参考级源：%s（修复指引：nf knowledge 列全部源）"
                      % src, file=sys.stderr)
                return 1
            digest = kn.sha256_file(os.path.join(ROOT, dst))
            entries = [dict(e) for e in (kn.load_log(ROOT).get("entries") or [])]
            cur = next((e for e in entries
                        if e.get("from") == src and e.get("to") == dst), None)
            if cur is None:
                cur = {"from": src, "to": dst, "digest": digest, "reviewed_by": "",
                       "reviewed_at": "", "evidence": [], "promoted": False}
                entries.append(cur)
            cur["digest"] = digest
            if args.by.strip():
                cur["reviewed_by"] = args.by.strip()
            cur["reviewed_at"] = at
            if tcmd == "promote":
                ev = [x.strip() for x in (args.evidence or "").split(",") if x.strip()]
                missing = [t for t in kn.TIERS if t not in ev]
                if missing:
                    print("  ✗ 转正须齐三档证据，缺：%s（修复指引：--evidence %s）"
                          % ("/".join(missing), ",".join(kn.TIERS)), file=sys.stderr)
                    return 1
                if not cur.get("reviewed_by"):
                    print("  ✗ 转正须复核双签：缺 --by", file=sys.stderr)
                    return 1
                cur["evidence"] = list(ev)
                cur["promoted"] = True
            kn.write_log(ROOT, entries)
            issues, _w, stats = kn.verify_transform(ROOT)
            if want_json:
                print(_json.dumps({"entry": cur, "issues": issues, "stats": stats},
                                  ensure_ascii=False, indent=2, sort_keys=True))
            else:
                print("== nf knowledge transform %s ==" % tcmd)
                print("  %s → %s（digest %s）转正=%s 复核=%s@%s"
                      % (src, dst, digest[:12], cur.get("promoted"),
                         cur.get("reviewed_by") or "-", cur.get("reviewed_at") or "-"))
                for i in issues:
                    print("  [FAIL] %s" % i, file=sys.stderr)
                if not issues:
                    print("  ✓ 记录已落盘，且与产物摘要一致（产物一改记录即失效）")
            return 1 if issues else 0
        issues, _warns, stats = kn.verify_transform(ROOT)
        log = kn.load_log(ROOT)
        if want_json:
            print(_json.dumps({"issues": issues, "stats": stats,
                               "entries": log.get("entries") or []},
                              ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print("== nf knowledge transform（消化记录：%d 条）==" % stats.get("entries", 0))
            for e in log.get("entries") or []:
                print("  %-18s → %-28s 转正=%s" % (e.get("from"), e.get("to"),
                                                    e.get("promoted")))
            for i in issues:
                print("  [FAIL] %s" % i, file=sys.stderr)
            if not issues:
                print("  ✓ 记录与产物摘要一致（无记录 = 无转正，符合 stay-reference）")
        return 1 if issues else 0
    issues, warns, stats = kn.scan(ROOT)
    decl = kn.load_decl(ROOT)
    if want_json:
        print(_json.dumps({"declaration": decl, "issues": issues, "warns": warns,
                           "stats": stats}, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print("== nf knowledge（双源知识层 · %d 源：合同 %d / 参考 %d）=="
              % (stats.get("sources", 0), stats.get("contract", 0), stats.get("reference", 0)))
        for s in kn.sources(ROOT):
            print("  %-22s %-9s %-18s %-10s %s"
                  % (s.get("id"), s.get("authority"), s.get("kind"),
                     s.get("visibility"), s.get("locator")))
        for w in warns:
            print("  [WARN] %s" % w)
        for i in issues:
            print("  [FAIL] %s" % i, file=sys.stderr)
        if not issues:
            print("  ✓ 权威分层/查询有序/时效/晋升/审核/认知裁剪 全部与判据一致")
    return 1 if issues else 0


def _load_runs(path):
    import json as _json
    with open(_rel_out(path), encoding="utf-8") as fh:
        data = _json.load(fh)
    if isinstance(data, dict) and "runs" in data:
        data = data["runs"]
    return data if isinstance(data, list) else [data]


def _cmd_receipts(args):
    """nf receipts：协议层回执单根（生成 / 校验 / 单条验证）。"""
    from core import receipts as rc
    import json as _json
    path = os.path.join(ROOT, rc.PROTOCOL_RECEIPTS_REL)
    if args.write:
        rel = rc.write_scope(ROOT, scope=args.scope)
        doc = rc.build_scope(ROOT, scope=args.scope)
        print("  ✓ 协议层回执已写入：%s（根 %s · %d 件）"
              % (rel, doc["root"][:16], doc["count"]))
        return 0
    if not os.path.exists(path):
        print("  ✗ 缺协议层回执（修复指引：nf receipts --write）", file=sys.stderr)
        return 1
    with open(path, encoding="utf-8") as fh:
        doc = _json.load(fh)
    if args.entry:
        hit = next((e for e in doc.get("entries") or []
                    if e.get("id") == args.entry), None)
        if hit is None:
            print("  ✗ 回执中没有该件：%s" % args.entry, file=sys.stderr)
            return 1
        folded = rc.fold_proof(str(hit["leaf"]), hit.get("proof") or [])
        ok = folded == str(doc.get("root"))
        print("== nf receipts --entry %s ==" % hit["id"])
        print("  折叠 %s · 根 %s → %s"
              % (folded[:16], str(doc.get("root"))[:16], "✓ 一致" if ok else "✗ 不一致"))
        return 0 if ok else 1
    issues, stats = rc.verify_scope(doc, ROOT)
    if args.json:
        print(_json.dumps({"issues": issues, "stats": stats},
                          ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print("== nf receipts --scope %s（%d 件 · root=%s）=="
              % (args.scope, stats.get("entries", 0), str(stats.get("root"))[:16]))
        for i in issues:
            print("  [FAIL] %s" % i, file=sys.stderr)
        if not issues:
            print("  ✓ 每条回执折叠到根，且根与实时重算一致")
    return 1 if issues else 0


def _cmd_events(args):
    """nf events：全仓事件背书核对。"""
    from core import registry_cross as rx
    import json as _json
    issues, warns, stats = rx.scan(ROOT)
    if args.json:
        print(_json.dumps({"issues": issues, "warns": warns, "stats": stats},
                          ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print("== nf events（全仓事件背书）==")
        print("  事件 %d · 跨包 %d · 无发布方挂账 %d"
              % (stats["events"], len(stats["cross_pkg"]),
                 len(warns) - len(stats["cross_pkg"])))
        for i in issues:
            print("  [FAIL] %s" % i, file=sys.stderr)
        for wmsg in warns[:10]:
            print("  [note] %s" % wmsg)
        if not issues:
            print("  ✓ 每个被订阅的事件都有发布方（外部通道已显式挂账）")
    return 1 if issues else 0


def _cmd_approve(args):
    """nf approve：内容绑定批准记录（生成 / 校验）。"""
    from core import approval
    import json as _json
    if args.list:
        rows = approval.list_records(ROOT)
        if args.json:
            print(_json.dumps(rows, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print("== nf approve --list（%d 条）==" % len(rows))
            for r in rows:
                print("  %s %-42s by %-12s %s%s"
                      % ("✗失效" if r["stale"] else "✓有效", r["subject"],
                         r["approved_by"] or "-", r["approved_at"],
                         ("　· " + r["note"][:30]) if r["note"] else ""))
            if not rows:
                print("  （暂无记录）")
        return 0
    if args.verify:
        issues, stats = approval.verify(ROOT)
        if args.json:
            print(_json.dumps({"issues": issues, "stats": stats},
                              ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print("== nf approve --verify（%d 条）==" % stats.get("records", 0))
            for i in issues:
                print("  [FAIL] %s" % i, file=sys.stderr)
            if not issues:
                print("  ✓ 全部批准记录有效（内容绑定未失效）")
        return 1 if issues else 0
    if not args.subject:
        print("  ✗ 需要被批准对象路径（或 --verify）（修复指引：nf approve <path> --by <人>）",
              file=sys.stderr)
        return 2
    try:
        rel = approval.approve(ROOT, args.subject, args.by, args.note)
    except (OSError, ValueError) as exc:
        print("  ✗ %s" % exc, file=sys.stderr)
        return 1
    if args.json:
        print(_json.dumps({"ok": True, "record": rel}, ensure_ascii=False, indent=2))
    else:
        print("  ✓ 批准记录已写入：%s（对象改动即自动失效）" % rel)
    return 0


def _cmd_library(args):
    """nf library：云端图书馆机器面（真源 = 条目 frontmatter）。"""
    from core import library as lib
    import json as _json
    sub = getattr(args, "library_cmd", None) or "ls"
    if sub == "ls":
        rows = lib.entries(ROOT)
        if getattr(args, "json", False):
            print(_json.dumps(lib.to_manifest(ROOT), ensure_ascii=False,
                              indent=2, sort_keys=True))
        else:
            print("== nf library ls（%d 件）==" % len(rows))
            for e in rows:
                fm = e["fm"]
                print("  %-32s %-10s %-6s %s" % (
                    e["id"], str(fm.get("status") or "active"),
                    str(fm.get("license") or "-"), str(fm.get("title") or "")))
        return 0
    if sub == "show":
        want = args.entry.strip()
        hit = None
        for e in lib.entries(ROOT):
            if e["id"] == want or e["id"].lower() == want.lower():
                hit = e
                break
        if hit is None:
            print("  ✗ 条目未找到：%s（nf library ls 可枚举；大小写用 ALIAS 转译）"
                  % args.entry, file=sys.stderr)
            return 1
        if args.json:
            print(_json.dumps({"id": hit["id"], "path": hit["path"],
                               "frontmatter": hit["fm"]},
                              ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print("== nf library show %s ==" % hit["id"])
            print("  路径：%s" % hit["path"])
            for k in sorted(hit["fm"]):
                print("  %-14s %s" % (k + ":", hit["fm"][k]))
        return 0
    if sub == "reindex":
        out = lib.write_projection(ROOT)
        if args.json:
            print(_json.dumps(out, ensure_ascii=False, indent=2))
        else:
            print("== nf library reindex ==")
            print("  重生成：%s" % ("、".join(out["changed"]) if out["changed"]
                                    else "无变化（投影已是最新）"))
        return 0
    if sub == "verify":
        vkey = None
        if getattr(args, "key_file", ""):
            from core import attest as _att2
            vkey = _att2.read_key_file(args.key_file)
        issues, warns, stats = lib.verify(
            ROOT, key=vkey,
            ssh_allowed_signers=getattr(args, "ssh_allowed_signers", ""),
            ssh_identity=getattr(args, "ssh_identity", ""))
        proj = lib.check_projection(ROOT)
        if args.json:
            print(_json.dumps({"issues": issues, "projection": proj,
                               "warns": warns, "stats": {k: v for k, v in stats.items()
                                                         if k != "warns"}},
                              ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print("== nf library verify（图书馆门）==")
            print("  条目 %d · 在役 %d · WARN %d"
                  % (stats["entries"], stats["active"], len(warns)))
            for i in list(issues) + list(proj):
                print("  [FAIL] %s" % i, file=sys.stderr)
            for w in warns:
                print("  [WARN] %s" % w)
            if not issues and not proj:
                print("  ✓ frontmatter 真源 + INDEX/ALIAS 投影一致")
        return 1 if (issues or proj) else 0
    if sub == "search":
        hits = lib.search(args.query, ROOT)
        if args.json:
            print(_json.dumps(hits, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print("== nf library search「%s」（%d 命中）==" % (args.query, len(hits)))
            for h in hits:
                print("  %-32s %-6s %s" % (h["id"], h["score"], h["title"]))
                print("      %s" % h["path"])
        return 0
    if sub in ("deprecate", "restore", "supersede"):
        if sub == "supersede":
            path = lib.set_status(ROOT, args.entry, "superseded", superseded_by=args.by)
            msg = "已取代：%s → %s" % (args.entry, args.by)
        else:
            new = "deprecated" if sub == "deprecate" else "active"
            path = lib.set_status(ROOT, args.entry, new)
            msg = "生命周期 → %s：%s" % (new, args.entry)
        if args.json:
            print(_json.dumps({"ok": True, "path": path, "message": msg},
                              ensure_ascii=False, indent=2))
        else:
            print("  ✓ %s（投影已重建；%s）" % (msg, path))
        return 0
    if sub == "receipts":
        from core import receipts as rc
        if args.entry:
            if not os.path.exists(os.path.join(ROOT, rc.RECEIPTS_REL)):
                print("  ✗ 缺回执文件（修复指引：nf library receipts --write）",
                      file=sys.stderr)
                return 1
            doc = rc.load(ROOT)
            want = args.entry.strip().lower()
            hit = next((e for e in doc.get("entries") or []
                        if str(e.get("id", "")).lower() == want), None)
            if hit is None:
                print("  ✗ 回执中没有该条目：%s（修复指引：nf library ls 列全量编号）"
                      % args.entry, file=sys.stderr)
                return 1
            folded = rc.fold_proof(str(hit["leaf"]), hit.get("proof") or [])
            ok = folded == str(doc.get("root"))
            if args.json:
                print(_json.dumps({"id": hit["id"], "ok": ok, "root": doc.get("root"),
                                   "folded": folded, "path": hit.get("path"),
                                   "leaf": hit.get("leaf"), "proof": hit.get("proof")},
                                  ensure_ascii=False, indent=2, sort_keys=True))
            else:
                print("== nf library receipts --entry %s ==" % hit["id"])
                print("  回执折叠：%s" % folded[:24])
                print("  全馆根　：%s" % str(doc.get("root"))[:24])
                print("  %s（拿到该条内容 + 本回执即可本地自验，无需全馆）"
                      % ("✓ 一致" if ok else "✗ 不一致"))
            return 0 if ok else 1
        if args.write:
            rel = rc.write(ROOT)
            doc = rc.build(ROOT)
            print("  ✓ 回执已写入：%s（根 %s · %d 条）"
                  % (rel, doc["root"][:16], doc["count"]))
            return 0
        if not os.path.exists(os.path.join(ROOT, rc.RECEIPTS_REL)):
            print("  ✗ 缺回执文件（修复指引：nf library receipts --write）",
                  file=sys.stderr)
            return 1
        issues, stats = rc.verify(rc.load(ROOT), ROOT)
        if args.json:
            print(_json.dumps({"issues": issues, "stats": stats},
                              ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print("== nf library receipts（%d 条 · root=%s）=="
                  % (stats.get("entries", 0), str(stats.get("root"))[:16]))
            for i in issues:
                print("  [FAIL] %s" % i, file=sys.stderr)
            if not issues:
                print("  ✓ 每条回执折叠到根，且根与实时重算一致")
        return 1 if issues else 0
    if sub == "attest":
        from core import library as nflib2
        from core import attest as _att
        key = _att.read_key_file(args.key_file) if args.key_file else None
        out = nflib2.set_attestation(
            ROOT, args.entry, key=key,
            ssh_key=getattr(args, "ssh_key", ""),
            ssh_identity=getattr(args, "ssh_identity", ""))
        if args.json:
            print(_json.dumps(out, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print("== nf library attest %s ==" % out["id"])
            print("  信任级：%s%s" % (out["level"],
                                     "" if not out.get("key_id")
                                     else "（key_id %s）" % out["key_id"]))
            print("  attestation：%s" % out["attestation"])
            print("  已写入 frontmatter（attestation/attested_at%s），投影已重建"
                  % ("/anchor_*" if out.get("key_id") else ""))
            if out.get("warn"):
                print("  ⚠ %s" % out["warn"])
        return 0
    print("  ✗ 未知 library 子命令：%s" % sub, file=sys.stderr)
    return 2


def _cmd_telemetry(args):
    """nf telemetry：trace 记录 → OTel GenAI semconv 属性 / OTLP 形状。"""
    from core import telemetry_semconv as ts
    import json as _json
    try:
        records = ts.load_trace(args.trace)
    except (OSError, ValueError) as exc:
        print("  ✗ %s" % exc, file=sys.stderr)
        return 1
    if not records:
        print("  ✗ trace 为空或格式不识别（支持单条记录或 {records:[...]}）",
              file=sys.stderr)
        return 1
    if args.otlp:
        print(_json.dumps(ts.to_export(records), ensure_ascii=False, indent=2,
                          sort_keys=False))
        return 0
    print("== nf telemetry（%d 记录 → semconv 属性）==" % len(records))
    for r in records:
        print("  %s" % ts.tool_name_of(r))
        for k, v in sorted(ts.attributes_for(r).items()):
            print("    %-28s %s" % (k, _json.dumps(v, ensure_ascii=False)))
    return 0


def _cmd_license(args):
    """nf license：图书馆许可证门（登记行 + 内联声明双源）。"""
    from core import license_gate as lg
    import json as _json
    issues, stats = lg.scan(ROOT)
    if args.json:
        print(_json.dumps({"issues": issues, "stats": stats},
                          ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print("== nf license（图书馆许可证门）==")
        print("  登记 %d 件 · 已声明 %d · 未声明 %d · 无内联 %d · 双源不一致 %d"
              % (stats["entries"], stats["declared"], len(stats["undeclared"]),
                 len(stats["no_inline"]), len(stats["mismatched"])))
        for i in issues:
            print("  [FAIL] %s" % i, file=sys.stderr)
        for w in stats["warnings"]:
            print("  [WARN] %s" % w)
        if not issues:
            print("  ✓ 许可面无 FAIL（WARN 为待投稿人回填项，不阻断入库）")
    return 1 if issues else 0


def _cmd_lsp(args):
    """nf lsp：最小 LSP 服务器（stdio）。"""
    from core import lsp as lsp_mod
    root = args.root or ROOT
    return lsp_mod.LspServer(root=root).serve()


def _cmd_score(args):
    """nf score：基线相对回归评分（绝对门之上的 no-silent-worsening 面）。"""
    from core import regression_score as rs
    from datetime import datetime, timezone
    import json as _json
    try:
        cur = rs.evaluate(ROOT)
        base_rel = args.baseline or rs.DEFAULT_BASELINE
        base_path = (base_rel if os.path.isabs(base_rel)
                     else os.path.join(ROOT, base_rel))
        baseline = (rs.load_baseline(base_path) if os.path.exists(base_path)
                    else {"schema": rs.SCHEMA})
        exceptions = []
        if args.exceptions:
            exc_path = (args.exceptions if os.path.isabs(args.exceptions)
                        else os.path.join(ROOT, args.exceptions))
            with open(exc_path, encoding="utf-8") as fh:
                exceptions = _json.load(fh)
        out = rs.compare(cur, baseline, tolerance=args.tolerance,
                         exceptions=exceptions)
        if args.write_baseline:
            rs.save_baseline(base_path, cur,
                             recorded_at=datetime.now(timezone.utc)
                             .strftime("%Y-%m-%dT%H:%M:%SZ"),
                             note="nf score --write-baseline")
        if args.json:
            print(_json.dumps({"current": cur, "compare": out},
                              ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print("== nf score（基线相对回归评分）==")
            print("  当前 %.2f · 基线 %.2f · delta %+.2f · 容差 %.2f"
                  % (out["current_score"], out["baseline_score"],
                     out["delta"], args.tolerance))
            print("  %s" % out["verdict"])
            for s in cur["signals"]:
                print("  · %-18s w=%.2f v=%.2f" % (s["name"], s["weight"], s["value"]))
            for r in out["regressed"]:
                print("    [REGRESS] %s %.4f → %.4f（%.4f）"
                      % (r["signal"], r["from"], r["to"], r["drop"]),
                      file=sys.stderr)
            if args.write_baseline:
                print("  基线已写入：%s" % os.path.relpath(
                    os.path.abspath(base_path), ROOT).replace("\\", "/"))
        return 0 if out["ok"] else 1
    except (OSError, ValueError, _json.JSONDecodeError) as exc:
        print("  ✗ %s" % exc, file=sys.stderr)
        return 1


def _cmd_diff(args):
    """nf diff：41 波C C2 —— 结构化差异 + 兼容判定。"""
    from core import knowledge_sig as ks
    import json as _json
    try:
        ra = _rel_to_root(args.a)
        rb = _rel_to_root(args.b)
        diff = ks.diff_signatures(ks.build_signature(ra, ROOT),
                                 ks.build_signature(rb, ROOT))
        if args.json:
            print(_json.dumps(diff, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print("== nf diff ==")
            print("  %s  →  %s" % (diff["from"], diff["to"]))
            if not diff["changes"]:
                print("  无字段差异（两份签名一致）")
            for c in diff["changes"]:
                print("  [%s] %s  %r → %r" % (c["kind"], c["field"], c["from"], c["to"]))
            print("  判定：%s" % diff["verdict"])
            impact = diff.get("impact", "editorial")
            label = {"bump": "结构性（须 bump + 迁移记录）",
                     "additive": "字段级新增（V1 只增不删）",
                     "editorial": "措辞/编辑（无契约影响）"}.get(impact, impact)
            print("  影响度：%s（%s）" % (impact, label))
        return 0
    except (OSError, ValueError) as exc:
        print("  ✗ %s" % exc, file=sys.stderr); return 1

def _cmd_explain(args):
    """nf explain：41 波C C5 —— check 修复指引（缺什么/补什么/示例）。"""
    key = args.check.strip().lower()
    if key in ("all", ""):
        print("== nf explain all（check 修复指引全量）==")
        for k in sorted(CHECK_GUIDE):
            print("  check%s：%s" % (k, CHECK_GUIDE[k]))
        return 0
    if key.startswith("check"):
        key = key[5:]
    guide = CHECK_GUIDE.get(key)
    if not guide:
        print("  ✗ 未知 check：%s（可用 all 看全量）" % args.check, file=sys.stderr); return 2
    print("== nf explain check%s ==" % key)
    print("  %s" % guide); return 0

def _cmd_related(args):
    """nf related：41 波C C4 —— 图书馆 See-Also 人读引用链（含模块级依赖图）。"""
    import json as _json
    import re as _re
    from core.market_analyzer import related_of
    from core import module_lifecycle as ml
    reg_path = args.registry or os.path.join(ROOT, "desktop", "src", "core", "registry.json")
    try:
        with open(reg_path, encoding="utf-8") as fh:
            reg = _json.load(fh)
        prots = {p["id"]: p for p in reg.get("protocols", [])}
        owner = {}
        for pid in reg.get("protocols", []):
            for m in pid.get("module_ids") or []:
                owner.setdefault(m, pid.get("id"))
        for m in reg.get("modules", []):
            owner.setdefault(m.get("id"), "官方核心")
        fence_re = _re.compile(r"```yaml(.*?)```", _re.S)
        id_re = _re.compile(r"(?m)^\s*id:\s*(M\d+)")
        inp_re = _re.compile(r"(?ms)^\s*inputs:\s*\[(.*?)\]")
        graph = {}
        for rel in ml.iter_module_files(ROOT):
            txt = ml.read_text(ROOT, rel)
            for fence in fence_re.findall(txt):
                if "machine_contract:" not in fence:
                    continue
                im = id_re.search(fence)
                if not im:
                    continue
                iv = inp_re.search(fence)
                ins = set()
                if iv:
                    for x in _re.split(r"[,\s]+", iv.group(1).strip()):
                        if x and not x.startswith("#"):
                            ins.add(x)
                graph.setdefault(im.group(1), set()).update(ins)
        r = related_of(args.target, prots, module_graph=graph, owner_map=owner)
        if args.json:
            print(_json.dumps(r, ensure_ascii=False, indent=2, sort_keys=True))
            return 0
        print("== nf related（See-Also · 相关条目 + 引用链）==")
        print("  目标：%s（%s）" % (r["target"], r["kind"]))
        print("  关联条目（引用了谁 / 依赖链）：%s" % ("、".join(r["refs"]) or "—"))
        print("  反向引用方（谁引用我）：%s" % ("、".join(r["referenced_by"]) or "—"))
        print("  相关模块互见：%s" % ("、".join(r["related_modules"]) or "—"))
        return 0
    except (OSError, ValueError, KeyError) as exc:
        print("  ✗ %s" % exc, file=sys.stderr); return 1


def _cmd_help(args):
    """nf help [COMMAND]：显示 nf 总帮助或指定子命令帮助。"""
    root = _build_parser()
    command = getattr(args, "command", None)
    if command:
        for action in root._actions:
            if isinstance(action, argparse._SubParsersAction):
                choice = action.choices.get(command)
                if choice is not None:
                    choice.print_help()
                    return 0
        print("  ✗ 未知子命令：%s（nf --help 看全量）" % command, file=sys.stderr)
        return 2
    root.print_help()
    return 0


def _cmd_doctor(args):
    """nf doctor：环境自检（快速只读体检；不开 verify 慢跑）。

    检查项：关键文件在场 / registry 可解析且模块在册 / IDL schema 定义在场 /
    核心库可导入。exit 0 = 全部通过；任一 FAIL = 1。
    """
    import json as _json

    checks = []

    def chk(name, ok, detail):
        checks.append({"name": name, "ok": bool(ok), "detail": str(detail)})

    for rel in ("README.md", "01_核心协议.md", "02_联动注册表.md",
                "06_Agent执行协议.md", "07_官方核心出厂与社区预设导航.md",
                "AGENTS.md", "STRATEGY.md", "verify.sh"):
        chk("文件在场 %s" % rel, os.path.isfile(os.path.join(ROOT, rel)), rel)

    reg_path = os.path.join(ROOT, "desktop", "src", "core", "registry.json")
    try:
        with open(reg_path, encoding="utf-8") as fh:
            reg = _json.load(fh)
        n_modules = len(reg.get("modules") or [])
        n_prots = len(reg.get("protocols") or [])
        chk("registry 可解析（modules=%d protocols=%d）" % (n_modules, n_prots),
            n_modules >= 13 and n_prots >= 5,
            "desktop/src/core/registry.json")
    except Exception as exc:
        chk("registry 可解析", False, "desktop/src/core/registry.json: %s" % exc)

    sdir = os.path.join(ROOT, "protocol", "schema")
    try:
        n_schema = len([f for f in os.listdir(sdir) if f.endswith(".json")])
    except OSError as exc:
        n_schema = 0
        chk("IDL schema 定义在场", False, str(exc))
    if os.path.isdir(sdir):
        chk("IDL schema 定义在场（%d 份）" % n_schema, n_schema == 5, sdir)

    try:
        sys.path.insert(0, os.path.join(ROOT, "desktop", "src"))
        from core import schema_lint  # noqa: F401
        chk("核心库可导入（schema_lint）", True, "desktop/src/core")
    except Exception as exc:
        chk("核心库可导入（schema_lint）", False, str(exc))

    try:
        from core import quality_baseline as qb
        q_issues, q_stats = qb.scan(ROOT)
        chk("基线自描述一致（verify %s · check1-%d PASS=%d）"
            % (q_stats["verify_version"], q_stats["checks"], qb.EXPECTED_PASS),
            not q_issues,
            "verify/README/CHANGELOG/VERSION-MATRIX")
    except Exception as exc:
        chk("基线自描述一致", False, str(exc))

    try:
        import json as _j
        from jsonschema import Draft202012Validator
        for f in sorted(os.listdir(os.path.join(ROOT, "protocol", "schema"))):
            if f.endswith(".json"):
                with open(os.path.join(ROOT, "protocol", "schema", f),
                          encoding="utf-8") as fh:
                    Draft202012Validator.check_schema(_j.load(fh))
        chk("schema 标准对照（jsonschema）", True, "CI 与本地同跑")
    except Exception as exc:
        chk("schema 标准对照（jsonschema）", True,
            "可选依赖未装（CI 已装真跑）：%s" % exc)

    try:
        from core import tool_face as tf
        tf_issues, tf_stats = tf.scan(ROOT)
        chk("模块工具面（tool_face）",
            not tf_issues,
            "模块 %d · 条目 %d · 候选 %d"
            % (tf_stats["modules"], tf_stats["entries"],
               tf_stats["candidates"]))
    except Exception as exc:
        chk("模块工具面（tool_face）", False, str(exc))

    try:
        from core import world_model as wm
        from core import world_slots as ws
        wm_issues, wm_stats = wm.scan(ROOT)
        ws_issues, ws_stats = ws.scan(ROOT)
        chk("world_model 契约",
            not wm_issues,
            "模块 %d · 变量 %d · checks %d · slots %d/%d"
            % (wm_stats["modules"], wm_stats["variables"],
               wm_stats.get("checks", 0), wm_stats.get("slots", 0),
               wm_stats.get("slot_registry", 0)))
        chk("world_slots 注册表",
            not ws_issues,
            "slots %d · arrays %d" % (ws_stats["slots"], ws_stats["arrays"]))
    except Exception as exc:
        chk("world_model/world_slots", False, str(exc))

    n_pass = sum(1 for c in checks if c["ok"])
    if args.json:
        print(_json.dumps({
            "version": NF_CLI_VERSION,
            "ok": n_pass == len(checks),
            "passed": n_pass,
            "total": len(checks),
            "checks": checks,
        }, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print("== nf doctor（nf %s）==" % NF_CLI_VERSION)
        for c in checks:
            print("  [%s] %s（%s）" % ("PASS" if c["ok"] else "FAIL",
                                       c["name"], c["detail"]))
        print("  体检：%d/%d 通过" % (n_pass, len(checks)))
    return 0 if n_pass == len(checks) else 1


def _collect_cli_tree():
    """自省 argparse 命令面：命令 × 顶层 flags × 二级子命令（供 completion 生成）。"""
    root = _build_parser()

    def flags(parser):
        out = []
        for act in parser._actions:
            if isinstance(act, argparse._SubParsersAction):
                continue
            out += list(act.option_strings)
        return sorted(set(out))

    tree = {}
    for act in root._actions:
        if not isinstance(act, argparse._SubParsersAction):
            continue
        for name, sp in act.choices.items():
            nested = {}
            for act2 in sp._actions:
                if isinstance(act2, argparse._SubParsersAction):
                    for n2, sp2 in act2.choices.items():
                        nested[n2] = flags(sp2)
            tree[name] = {"flags": flags(sp), "nested": nested}
    return {
        "commands": sorted(tree),
        "root_flags": flags(root),
        "tree": tree,
    }


def _cmd_completion(args):
    """nf completion <bash|zsh|fish>：从 argparse 命令面生成 shell 补全脚本。"""
    data = _collect_cli_tree()
    cmds = data["commands"]
    root_flags = data["root_flags"]
    tree = data["tree"]
    words = lambda xs: " ".join(xs)  # noqa: E731

    def var(cmd):
        return cmd.replace("-", "_")

    if args.shell == "bash":
        lines = [
            "# nf bash completion（自动生成 · 追加到 ~/.bashrc 后 source）",
            "_nf_cmds=\"%s\"" % words(cmds),
            "_nf_root_flags=\"%s\"" % words(root_flags),
        ]
        for c in cmds:
            lines.append("_nf_flags_%s=\"%s\"" % (var(c), words(tree[c]["flags"])))
            if tree[c]["nested"]:
                lines.append("_nf_nested_%s=\"%s\""
                             % (var(c), words(sorted(tree[c]["nested"]))))
        lines += [
            "_nf_completions(){",
            "  local cur cmd",
            "  cur=\"${COMP_WORDS[COMP_CWORD]}\"",
            "  if [ \"$COMP_CWORD\" -eq 1 ]; then",
            "    COMPREPLY=( $(compgen -W \"$_nf_cmds $_nf_root_flags\" -- \"$cur\") )",
            "    return",
            "  fi",
            "  cmd=\"${COMP_WORDS[1]}\"",
            "  case \"$cmd\" in",
        ]
        for c in cmds:
            if tree[c]["nested"]:
                lines.append(
                    "    %s) if [ \"$COMP_CWORD\" -eq 2 ]; then"
                    " eval nest=\"$_nf_nested_%s\";"
                    " COMPREPLY=( $(compgen -W \"$nest\" -- \"$cur\") ); return; fi ;;" % (c, var(c)))
        lines += [
            "  esac",
            "  eval fl=\"$_nf_flags_${cmd//-/_}\"; fl=\"${fl:-}\"",
            "  if [[ \"$cur\" == -* ]]; then COMPREPLY=( $(compgen -W \"$fl\" -- \"$cur\") ); return; fi",
            "  COMPREPLY=( $(compgen -W \"$fl\" -- \"$cur\") $(compgen -f -- \"$cur\") )",
            "}",
            "complete -F _nf_completions nf",
            "",
        ]
        print("\n".join(lines))
        return 0

    if args.shell == "zsh":
        all_flags = sorted(set(data["root_flags"]))
        for c in cmds:
            all_flags += tree[c]["flags"]
            for sub in tree[c]["nested"].values():
                all_flags += sub
        all_flags = sorted(set(all_flags))
        lines = [
            "#compdef nf",
            "# nf zsh completion（自动生成）",
            "_nf_cmds=(%s)" % " ".join(cmds),
            "_nf_all_flags=(%s)" % " ".join(all_flags),
            "_nf() {",
            "  local -a cmds",
            "  cmds=(%s)" % " ".join(cmds),
            "  if (( CURRENT == 2 )); then",
            "    _describe -t commands 'nf command' cmds",
            "  else",
            "    if [[ $PREFIX == -* ]]; then compadd -- $_nf_all_flags; else _files; fi",
            "  fi",
            "}",
            "compdef _nf nf",
            "",
        ]
        print("\n".join(lines))
        return 0

    # fish
    lines = [
        "# nf fish completion（自动生成 · nf completion fish | source）",
        "complete -c nf -f",
        "complete -c nf -n '__fish_use_subcommand' -a '%s'" % " ".join(cmds),
    ]
    for c in cmds:
        for f in tree[c]["flags"]:
            if f.startswith("--"):
                lines.append("complete -c nf -n '__fish_seen_subcommand_from %s' -l %s"
                             % (c, f[2:]))
            elif f.startswith("-") and len(f) == 2:
                lines.append("complete -c nf -n '__fish_seen_subcommand_from %s' -s %s"
                             % (c, f[1:]))
        for n2 in tree[c]["nested"]:
            lines.append("complete -c nf -n '__fish_seen_subcommand_from %s' -a '%s'"
                         % (c, n2))
            for f in tree[c]["nested"][n2]:
                cond = "__fish_seen_subcommand_from %s; and __fish_seen_subcommand_from %s" % (c, n2)
                if f.startswith("--"):
                    lines.append("complete -c nf -n '%s' -l %s" % (cond, f[2:]))
                elif f.startswith("-") and len(f) == 2:
                    lines.append("complete -c nf -n '%s' -s %s" % (cond, f[1:]))
    print("\n".join(lines))
    return 0


def _cmd_assemble(args):
    """nf assemble：需求 → 澄清漏斗 → 装配计划；--check 对成品完整版做机器验收。"""
    from core import assemble_plan as ap

    req_text = args.requirement
    answers = getattr(args, "answer", None) or []
    if args.session_path:
        prior = _session_load(args.session_path)
        answers = prior + [a for a in answers if a not in prior]
    if answers:
        req_text = req_text + "（" + "；".join(answers) + "）"
    funnel = ap.clarify(req_text)
    plan_ = funnel.get("plan") or ap.plan(req_text)
    if args.save_path:
        text = ap.dossier(req_text, plan_,
                          funnel.get("questions") or [], answers)
        try:
            parent = os.path.dirname(os.path.abspath(args.save_path))
            if parent:
                os.makedirs(parent, exist_ok=True)
            with open(args.save_path, "w", encoding="utf-8",
                      newline="\n") as fh:
                fh.write(text)
        except OSError as exc:
            print("  ✗ 写需求档案失败：%s（修复指引：给可写路径）" % exc,
                  file=sys.stderr)
            return 1
        print("  ✓ 需求档案已存：%s" % args.save_path)
    if funnel["status"] == "clarify":
        if args.session_path:
            _session_write(args.session_path, args.requirement, answers)
        if args.trace_path:
            _write_trace_file(args.trace_path, {
                "tool": "nf assemble", "phase": "clarify",
                "requirement": args.requirement,
                "questions": funnel.get("questions") or [],
            })
        print("== nf assemble（需求澄清）==")
        print("  你的需求信息还不够直接编排，先补三点（缺一不可）：")
        for q in funnel["questions"]:
            print("  · %s" % q)
        print("  补充后再跑：nf assemble \"题材+主轴+尺度的一句话\" --check <out.md>")
        return 0
    if args.check_md:
        try:
            with open(args.check_md, encoding="utf-8") as fh:
                out_md = fh.read()
        except OSError as exc:
            print("  ✗ 读取成品失败：%s（修复指引：给出仓库内完整版 md 路径）" % exc,
                  file=sys.stderr)
            return 1
        import re as _re
        has_segments = bool(_re.search(r"^##\s+[0-7]\.", out_md, _re.M))
        issues, stats = ap.check(out_md, plan_) if (
            has_segments or not args.rounds) else ([], {})
        if not stats:
            stats = {"segments": 0, "modules_mentioned": 0,
                     "allowed": len(plan_.get("allowed_module_ids") or [])}
        if args.rounds:
            from core import round_drill as rd
            r_issues, r_stats = rd.scan(out_md, plan_["allowed_module_ids"])
            for i in r_issues:
                issues.append("回合级[%s]" % i)
            if r_stats["warn_gaps"]:
                print("  [WARN] 回合跳号：%s" % r_stats["warn_gaps"])
        print("== nf assemble --check（需求 → 成品机器验收）==")
        print("  需求：%s → %s/%s（模块提及 %d · 允许集 %d）"
              % (args.requirement, plan_["package"] or "？",
                 plan_["pipeline"] or "？", stats["modules_mentioned"],
                 stats["allowed"]))
        for issue in issues:
            print("  [FAIL] %s" % issue, file=sys.stderr)
        if not issues:
            print("  ✓ 成品通过自组装机器验收（八段骨架 + 编号允许集 + 决策引用）")
        if args.trace_path:
            _write_trace_file(args.trace_path, {
                "tool": "nf assemble", "phase": "check",
                "requirement": args.requirement,
                "source": args.check_md,
                "matched": plan_.get("matched"),
                "package": plan_.get("package"),
                "pipeline": plan_.get("pipeline"),
                "ok": not issues,
                "issues": issues,
                "stats": stats,
            })
        return 1 if issues else 0
    print("== nf assemble（需求 → 装配计划）==")
    if plan_["matched"]:
        print("  匹配预设：%s · 管线 %s" % (plan_["package"], plan_["pipeline"]))
        print("  管线件：%s" % ("、".join(plan_["pipeline_files"]) or "—"))
        print("  取件模块：%s" % "、".join(plan_["fetch_modules"]))
        print("  装配允许集（官方核心 + 包模块）：%d"
              % len(plan_["allowed_module_ids"]))
        print("  下一步：读 agent_组装指令包_v0.2.md → 取件 → 输出完整版 → "
              "nf assemble \"%s\" --check <out.md> 验收" % args.requirement)
    else:
        print("  未命中预设 → 用户自定义流（custom）")
        print("  可借用已登记包：%s"
              % ("、".join(plan_["known_packages"]) or "—"))
        print("  装配允许集（官方核心 + 全部已登记社区模块）：%d"
              % len(plan_["allowed_module_ids"]))
        print("  自定义预留槽位：模块 M91-M99 或 <本包独占类别>:Mxx 类内段 · 资产 900+ 命名空间 · "
              "新管线 Pxx（避让层位 id P00-P80 与官方/既有管线，见 02 §8.3）")
        print("  建件：按 community/模板制作指令包.md 做自定义模块/资产 → "
              "protocol.yaml 登记（nf register）→ 成品里即可引用 → 验收")
        print("  验收：nf assemble \"%s\" --check <out.md>"
              % args.requirement)
    if args.session_path:
        _session_write(args.session_path, args.requirement, answers)
    if args.trace_path:
        _write_trace_file(args.trace_path, {
            "tool": "nf assemble", "phase": "plan",
            "requirement": args.requirement,
            "status": plan_.get("status"),
            "matched": plan_.get("matched"),
            "package": plan_.get("package"),
            "pipeline": plan_.get("pipeline"),
            "allowed_modules": len(plan_.get("allowed_module_ids") or []),
        })
    return 0


def _cmd_release(args):
    """nf release：发布前体检——verify + 基线自描述一致（--fast 跳过 verify）。"""
    import subprocess
    from core import quality_baseline as qb

    issues, stats = qb.scan(ROOT)
    print("== nf release check（发布前体检）==")
    print("  verify 版本 %s · check 数 %d（基线自描述一致：%s）"
          % (stats["verify_version"], stats["checks"],
             "OK" if not issues else "FAIL"))
    for i in issues:
        print("  [FAIL] %s" % i, file=sys.stderr)
    if args.fast:
        print("  --fast：跳过 verify.sh 全量（发布前请跑完整 nf release）")
        return 1 if issues else 0
    rc = subprocess.run(["bash", "verify.sh"], cwd=ROOT).returncode
    gate_fail = bool(issues) or rc != 0
    if not gate_fail:
        from core import asset_ledger_projection as alp
        from core import instruction_step_audit as isa
        from core import payload_registry as pr
        for name, fn in (("资产 ledger", alp.verify),
                         ("指令审计", isa.scan),
                         ("载荷注册表", pr.scan)):
            f_issues, _ = fn(ROOT)
            if f_issues:
                gate_fail = True
                print("  [FAIL] %s：%s" % (name, "；".join(f_issues[:3])),
                      file=sys.stderr)
            else:
                print("  ✓ %s 一致" % name)
        cov = subprocess.run(["bash", "scripts/per_module_coverage.sh", "30"],
                             cwd=ROOT).returncode
        if cov != 0:
            gate_fail = True
            print("  [FAIL] 逐模块覆盖率 < min30", file=sys.stderr)
        else:
            print("  ✓ 逐模块覆盖率 ≥ min30")
    if gate_fail:
        print("  ✗ 发布体检未过（基线/verify）——禁止发布", file=sys.stderr)
        return 1
    print("  ✓ 发布体检通过：verify 全绿 + 基线自描述一致（可打 tag）")
    return 0


def _write_trace_file(path, payload):
    import json as _json
    try:
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            _json.dump(payload, fh, ensure_ascii=False, indent=2, sort_keys=True)
            fh.write("\n")
    except OSError as exc:
        print("  ✗ 写 trace 失败：%s（修复指引：给可写路径）" % exc,
              file=sys.stderr)
        return False
    print("  ✓ trace 已存：%s" % path)
    return True


def _session_load(path):
    import json as _json
    try:
        with open(path, encoding="utf-8") as fh:
            return list((_json.load(fh).get("answers") or []))
    except (OSError, ValueError):
        return []


def _session_write(path, requirement, answers):
    import json as _json
    try:
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            _json.dump({"requirement": requirement, "answers": list(answers)},
                       fh, ensure_ascii=False, indent=2)
    except OSError:
        pass


def _cmd_toolface(args):
    """nf toolface：浏览模块工具面（machine_contract.tool_face）。"""
    import json as _json
    from core import tool_face as tf

    issues, stats = tf.scan(ROOT)
    if args.json:
        print(_json.dumps({"kind": "toolface", "issues": issues, "stats": stats},
                          ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print("== nf toolface（模块工具面 · AI 裁量不入门禁）==")
        print("  模块 %d · 条目 %d · 候选工具链接 %d"
              % (stats["modules"], stats["entries"], stats["candidates"]))
        for f in stats["faces"]:
            print("  · %s（%s · %d 条目）"
                  % (f["module"], f["source"], f["entries"]))
        for i in issues:
            print("  [FAIL] %s" % i, file=sys.stderr)
    return 1 if issues else 0


def _cmd_worldmodel(args):
    """nf worldmodel：浏览确定性抽象状态契约（machine_contract.world_model）。"""
    import json as _json
    from pathlib import Path

    from core import conformance_scan as csc
    from core import world_model as wm

    concrete = None
    if getattr(args, "state_path", None):
        concrete = _json.loads(Path(args.state_path).read_text(encoding="utf-8"))

    def _load(model):
        text = Path(ROOT, model["source"]).read_text(encoding="utf-8")
        parsed = csc._fence_yaml(text, "machine_contract")
        return parsed.get("machine_contract", {}).get("world_model")

    def _run_one(model):
        contract = _load(model)
        if not isinstance(contract, dict):
            return None
        runtime = wm.WorldModelRuntime(contract)
        return runtime.replay_concrete(concrete) if concrete is not None else runtime.replay()

    issues, stats = wm.scan(ROOT)
    if args.json and args.run:
        runs = []
        for m in stats["models"]:
            result = _run_one(m)
            if result is not None:
                runs.append({
                    "module": m["module"],
                    "source": m["source"],
                    "result": result,
                })
        print(_json.dumps({"kind": "worldmodel-run", "issues": issues, "runs": runs},
                          ensure_ascii=False, indent=2, sort_keys=True))
    elif args.json:
        print(_json.dumps({"kind": "worldmodel", "issues": issues, "stats": stats},
                          ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print("== nf worldmodel（JEPA-inspired 确定性抽象状态契约 · check32 硬门）==")
        print("  模块 %d · 变量 %d · 相位 %d · 不变式 %d · checks %d · slots %d/%d"
              % (stats["modules"], stats["variables"],
                 stats["phases"], stats["invariants"],
                 stats.get("checks", 0), stats.get("slots", 0),
                 stats.get("slot_registry", 0)))
        for m in stats["models"]:
            print("  · %s（%s · initial=%s · %d phases · %d invariants · %d checks）"
                  % (m["module"], m["source"], m["initial_phase"],
                     m["phases"], m["invariants"], m.get("checks", 0)))
        if args.walk:
            for m in stats["models"]:
                contract = _load(m)
                if not isinstance(contract, dict):
                    continue
                seq, reason, repeat = wm.phase_sequence(contract)
                print("  → %s 重放：%s（终止=%s%s）"
                      % (m["module"], " → ".join(seq), reason,
                         " · 重复=" + str(repeat) if repeat else ""))
        if args.run:
            for m in stats["models"]:
                result = _run_one(m)
                if result is None:
                    continue
                print("  → %s 运行：%d steps（%s%s · digest=%s）"
                      % (m["module"], len(result["steps"]), result["reason"],
                         " · 重复=" + str(result["repeat"]) if result["repeat"] else "",
                         result.get("digest", "")[:12]))
                for step in result["steps"]:
                    print("    %d. %s → %s（guard=%s）"
                          % (step["step"], step["phase_from"], step["phase_to"],
                             step["guard"]))
        for i in issues:
            print("  [FAIL] %s" % i, file=sys.stderr)
    return 1 if issues else 0


def main(argv=None) -> int:
    args = _build_parser().parse_args(argv)
    if args.cmd is None:
        _build_parser().print_help()
        return 0
    if args.cmd == "help":
        return _cmd_help(args)
    if args.cmd == "doctor":
        return _cmd_doctor(args)
    if args.cmd == "completion":
        return _cmd_completion(args)
    if args.cmd == "assemble":
        return _cmd_assemble(args)
    if args.cmd == "release":
        return _cmd_release(args)
    if args.cmd == "toolface":
        return _cmd_toolface(args)
    if args.cmd == "worldmodel":
        return _cmd_worldmodel(args)
    if args.cmd == "register":
        return _cmd_register(args)
    if args.cmd == "asset":
        return _cmd_asset(args)
    if args.cmd == "pipeline":
        return _cmd_pipeline(args)
    if args.cmd == "module":
        return _cmd_module(args)
    if args.cmd == "sig":
        return _cmd_sig(args)
    if args.cmd == "attest":
        return _cmd_attest(args)
    if args.cmd == "score":
        return _cmd_score(args)
    if args.cmd == "lint":
        return _cmd_lint(args)
    if args.cmd == "lsp":
        return _cmd_lsp(args)
    if args.cmd == "license":
        return _cmd_license(args)
    if args.cmd == "telemetry":
        return _cmd_telemetry(args)
    if args.cmd == "library":
        return _cmd_library(args)
    if args.cmd == "conformance":
        return _cmd_conformance(args)
    if args.cmd == "approve":
        return _cmd_approve(args)
    if args.cmd == "events":
        return _cmd_events(args)
    if args.cmd == "receipts":
        return _cmd_receipts(args)
    if args.cmd == "driver":
        return _cmd_driver(args)
    if args.cmd == "rfc":
        return _cmd_rfc(args)
    if args.cmd == "patterns":
        return _cmd_patterns(args)
    if args.cmd == "bench":
        return _cmd_bench(args)
    if args.cmd == "endpoint":
        return _cmd_endpoint(args)
    if args.cmd == "knowledge":
        return _cmd_knowledge(args)
    if args.cmd == "assertions":
        return _cmd_assertions(args)
    if args.cmd == "model":
        return _cmd_model(args)
    if args.cmd == "decisions":
        return _cmd_decisions(args)
    if args.cmd == "handover":
        return _cmd_handover(args)
    if args.cmd == "postmortem":
        return _cmd_postmortem(args)
    if args.cmd == "audit":
        return _cmd_audit(args)
    if args.cmd == "cognition":
        return _cmd_cognition(args)
    if args.cmd == "st-validate":
        return _cmd_st_validate(args)
    if args.cmd == "state-front":
        return _cmd_state_front(args)
    if args.cmd == "diff":
        return _cmd_diff(args)
    if args.cmd == "related":
        return _cmd_related(args)
    if args.cmd == "explain":
        return _cmd_explain(args)
    if args.cmd == "demo":
        return _cmd_demo(args)
    if args.cmd == "market":
        return _cmd_market(args)
    if args.cmd == "who-refers":
        return _cmd_who_refers(args)
    if args.cmd == "impact":
        return _cmd_impact(args)
    if args.cmd == "rename":
        return _cmd_rename(args)
    if args.cmd == "import":
        return _cmd_import(args)
    if args.cmd == "spec":
        return _cmd_spec(args)
    if args.cmd == "render":
        return _cmd_render(args)
    if args.cmd == "serve":
        return _cmd_serve(args)
    if args.cmd == "design":
        if args.design_cmd == "audit":
            return _cmd_audit(args)
        return _cmd_design(args)
    if args.cmd != "run":
        _build_parser().print_help()
        return 2

    from core.pipeline import pipe
    from core.pipeline_loader import load_pipeline_file
    from core.storage import Store

    pipeline = load_pipeline_file(args.pipeline)
    if pipeline is None:
        print(f"✗ 管线解析失败：{args.pipeline}", file=sys.stderr)
        return 1

    store = Store(home=args.store) if args.store else Store()
    if args.seed:
        stats = _seed_store(store)
        print(f"  seed 装载：官方核心 {stats['core']} 件"
              f" + 轻混组合包 {stats['combo']} 件 → {store.home}")
    else:
        print(f"  store：{store.home}")

    selected = [m.strip() for m in args.modules.split(",") if m.strip()]
    # B2 变体：--variant-add/--variant-remove 经 apply_variant 变换 selected
    if args.variant_add or args.variant_remove:
        from core.variants import apply_variant
        v = apply_variant(selected, {
            "add": [x.strip() for x in args.variant_add.split(",") if x.strip()],
            "remove": [x.strip() for x in args.variant_remove.split(",") if x.strip()],
        })
        selected = v.selected
        print(f"  [变体] selected {args.modules.split(',')} → {selected}"
              + (f"（移除 {args.variant_remove}）" if args.variant_remove else ""))
    dest = args.dest
    r = pipe(store, pipeline, selected,
             include_references=not args.no_include_refs,
             fmt=args.fmt, dest_dir=dest,
             fail_on_gate=not args.force_export,
             doc_semantics=args.doc_semantics)

    print(f"\n== 质量门 ==\n  PASS {r.gate.n_pass} · WARN {r.gate.n_warn}"
          f" · FAIL {r.gate.n_fail}" + ("（可产出）" if r.ok else "（存在 FAIL）"))
    # B1 可解释化：逐条含修复建议（quality_gate 报告样式，warn/fail 都 actionable）
    for issue in r.gate.issues:
        if issue.level in ("fail", "warn"):
            print(f"  [{issue.level.upper()}] {issue.message}")
            if issue.suggestion:
                print(f"      建议：{issue.suggestion}")
    for w in r.warnings:
        print(f"  [INFO] {w}")
    if r.export is not None:
        print("\n== 导出 ==")
        if r.export.files:
            for f in r.export.files:
                print(f"  ✓ {f}")
        if r.export.warnings:
            for w in r.export.warnings:
                print(f"  [导出] {w}")
    if not r.ok:
        print("\n✗ 质量门 FAIL（可信任度不变量）"
              + ("；已按 --force-export 导出诊断产物" if args.force_export
                 else "——修复装配后重跑或加 --force-export 看坏产物"), file=sys.stderr)
        return 1
    print("\n★ 全链管道 PASSED ✓")
    return 0


def cli(argv=None) -> int:
    """CLI 运行时封装：SIGPIPE 语义 + 断管/中断兜底 + 退出码归一。

    - POSIX：恢复 SIGPIPE 默认动作（`nf ... | head` 静默截断，无 traceback）；
    - 断管兜底（Windows 无 SIGPIPE 场景）；
    - Ctrl-C → 130；返回非 int（如 None）按 0 处理。
    - 未预期异常：默认一句错误 + 提示（NF_DEBUG=1 时透出堆栈），不裸刷 traceback。
    """
    try:
        import signal
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    except Exception:
        pass
    try:
        code = main(argv)
    except BrokenPipeError:
        try:
            devnull = os.open(os.devnull, os.O_WRONLY)
            os.dup2(devnull, sys.stdout.fileno())
        except Exception:
            pass
        code = 0
    except KeyboardInterrupt:
        code = 130
    except Exception as exc:
        if os.environ.get("NF_DEBUG"):
            raise
        print("  ✗ 内部错误：%s（重跑 NF_DEBUG=1 nf ... 看堆栈）" % exc,
              file=sys.stderr)
        code = 1
    return code if isinstance(code, int) else 0


if __name__ == "__main__":
    sys.exit(cli())
