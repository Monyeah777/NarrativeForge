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
                     choices=["ccv3", "skill", "agents", "claude", "mcp"],
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
    a_thk = asub.add_parser("thickness",
                            help="资产语义厚度体检（45：字符/键/小节/表格 + 低信息档候选）", description="资产语义厚度体检（45：字符/键/小节/表格 + 低信息档候选）")
    a_thk.add_argument("--root", default=ROOT, help="扫描根（缺省=仓库根）")
    a_thk.add_argument("--json", action="store_true",
                       help="输出结构化 JSON（厚度统计）")
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
    rel = sub.add_parser("release",
                         help="发布前体检（45：verify + 基线自描述一致 + doctor；--fast 跳过 verify）", description="发布前体检（45：verify + 基线自描述一致 + doctor；--fast 跳过 verify）")
    rel.add_argument("--fast", action="store_true",
                     help="跳过 verify.sh 全量（快速自检：基线自描述 + doctor）")
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
    import json
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
        print(f"== nf design steelman init ==")
        print(f"  ✓ 工作单已生成: {out}")
        print(f"    用三套引导模板之一填充六段，然后跑 --check 自检")
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
        print(f"    按引导问卷完成各节回填，然后 --check 自检")
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
            return 1 if issues else 0
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
    "8": "缺什么：社区资产行数溯源不符。补什么：核对资产切片行号区间（07 §7 项3）。",
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
    "27": "缺什么：架构纯度违约（端壳残留/私货可变物/重复标题/raise 消息缺修复指引）。补什么：purity_scan 四规则逐条修；示例：R1 端壳关键词残留清理。",
    "28": "缺什么：协议层 IDL 违约（schema 定义缺失或协议件字段漂移）。补什么：protocol/schema 五定义在场 + 在场 machine_contract/管线/协议包/台账过 schema；示例：nf doctor 看 schema 在场。",
    "29": "缺什么：Conformance 虚标或声明缺失（声明级别 > 可证级别）。补什么：按 01 §1.2 与 conformance_scan 提示降级或补证据。",
    "30": "缺什么：扩展判据缺失或版本字段 bump 无迁移记录。补什么：protocol/EXTENSION.md 判据 + bump 变更带 01 §7/02 §9.3 四步迁移记录。",
    "31": "缺什么：生成物过期（protocol/generated 与当前 schema/协议件不一致）。补什么：重跑 protocol_golden.write_golden 并随变更一并提交。",
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
        chk("基线自描述一致（verify %s · check1-31 PASS=49）"
            % q_stats["verify_version"], not q_issues,
            "verify/README/CHANGELOG/VERSION-MATRIX")
    except Exception as exc:
        chk("基线自描述一致", False, str(exc))

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
            "  COMPREPLY=( $(compgen -W \"$fl\" -- \"$cur\") $(compgen -f -- \"$cur\") )",
            "}",
            "complete -F _nf_completions nf",
            "",
        ]
        print("\n".join(lines))
        return 0

    if args.shell == "zsh":
        lines = [
            "#compdef nf",
            "# nf zsh completion（自动生成）",
            "_nf_cmds=(%s)" % " ".join(cmds),
            "_nf() {",
            "  local -a cmds",
            "  cmds=(%s)" % " ".join(cmds),
            "  if (( CURRENT == 2 )); then",
            "    _describe -t commands 'nf command' cmds",
            "  else",
            "    _files",
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
    print("\n".join(lines))
    return 0


def _cmd_assemble(args):
    """nf assemble：需求 → 澄清漏斗 → 装配计划；--check 对成品完整版做机器验收。"""
    from core import assemble_plan as ap

    funnel = ap.clarify(args.requirement)
    plan_ = funnel.get("plan") or ap.plan(args.requirement)
    if args.save_path:
        text = ap.dossier(args.requirement, plan_,
                          funnel.get("questions") or [])
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
        issues, stats = ap.check(out_md, plan_)
        print("== nf assemble --check（需求 → 成品机器验收）==")
        print("  需求：%s → %s/%s（模块提及 %d · 允许集 %d）"
              % (args.requirement, plan_["package"] or "？",
                 plan_["pipeline"] or "？", stats["modules_mentioned"],
                 stats["allowed"]))
        for issue in issues:
            print("  [FAIL] %s" % issue, file=sys.stderr)
        if not issues:
            print("  ✓ 成品通过自组装机器验收（八段骨架 + 编号允许集 + 决策引用）")
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
        print("  自定义预留槽位：模块 M91-M99 · 资产 900+ 命名空间 · 新管线 Pxx（不占用既有）")
        print("  建件：按 community/模板制作指令包.md 做自定义模块/资产 → "
              "protocol.yaml 登记（nf register）→ 成品里即可引用 → 验收")
        print("  验收：nf assemble \"%s\" --check <out.md>"
              % args.requirement)
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
    if issues or rc != 0:
        print("  ✗ 发布体检未过（基线/verify）——禁止发布", file=sys.stderr)
        return 1
    print("  ✓ 发布体检通过：verify 全绿 + 基线自描述一致（可打 tag）")
    return 0


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
