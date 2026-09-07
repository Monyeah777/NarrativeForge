# NarrativeForge 外部验证实证报告（v2.7 · 40 总纲波 A S1 建档）

> **状态（2026-09-07）**：本文件是波 A S1「外部验证」的官方记录位。四项出口（E1 CCV3→SillyTavern / E2 SKILL+AGENTS→Claude Code / E3 nf serve→标准 MCP 客户端 / Y5 样本交免费 AI 复测）的**实测均需真实外部工具/客户端环境**；本工作台只完成前置条件清点 + 各出口 runbook + 准备材料落位 + 状态占位。**未实测项一律不宣称转正**——README / docs 对外宣告以本文件与 `docs/mcp.md` 状态为准（S13 转正门未开）。
> **验收对照（总纲波 A）**：验收 = 实证报告 ≥1 出口成功 或 明确差距修复。当前四项均「待外部实测」，验收未达成；本文件即差距声明 + 回填作业面。

## 0. 记录约定

- **每出口四要素**：环境 / 步骤 / 结果 / 差距与修复；状态取 `待外部实测 · 部分成功 · 有差距 · 转正` 四态之一。
- **回填铁律**：只记真实装载/调用结果；禁止以「AI 自产→AI 自验」冒充外部实测（S1 立项根因）。任何一步造假 = 协议事故。
- **机检可覆盖面已先行**：导出 schema 合规由 verify check19/check22 常驻门禁机检；供应链闭合由 check23（波 A W1）机检——本次 CCV3 实导质量门 0 WARN / 0 FAIL（见 E1 准备材料）。
- **verify 基线**：`bash verify.sh` PASS=33 / WARN=0 / FAIL=0（波 A W1–W4 提交时点）。

## 1. E1 · CCV3 导出 → SillyTavern 装载实测

**目标**：证明 NF 的 CCV3 导出物能被真实前端 SillyTavern 作为角色卡导入并运行（全项目第一个外部验证锚点，成败均为资产）。
**环境**：需一台装有 SillyTavern 的机器（本工作台无此前端，不可代跑）。
**准备材料（已落位）**：
- CCV3 导出样例（本次会话实导，质量门 PASS 0/0/0）：`docs/external-validation-assets/E1_ccv3_sample_lightmix_P04_chara.json` + `E1_ccv3_sample_lightmix_P04_world.json`——来源 = `community/校园西幻轻混组合包`（P04 管线：通用类:M00 / 轻混类:M91 / 轻混类:M92 / 通用类:M80，`--seed` 装载）。
- schema 自举对照卡（import adapter 单测 fixture，check19/22 覆盖）：`desktop/tests/fixtures/external/chara.json`（+ `world.json`）。
- 重生成命令（换校园 P02 / 西幻 P03 同构）：`python scripts/nf.py run --pipeline <P02/P03 管线 .md> --modules <包 README §2 装载清单模块 full_id，类别前缀格式同 docs/mcp.md 示例> --seed --fmt ccv3 --dest <目录>`。
**实测步骤（runbook）**：① 在 SillyTavern 导入上述 `chara.json`（Create new character → Advanced/Import）；② 世界信息侧栏挂 `world.json`（如支持）；③ 逐项核对：加载成功？字段映射偏差？（name/description/personality/mes_example/character_book 等）④ 开一轮对话确认协议注入与角色卡生效；⑤ 按四要素回填下表。
**结果**：待外部实测。
**差距与修复**：无真实前端加载记录即不转正；若导入出现字段偏差，本段记录差异清单并交 export 层修复（fixture 随 X1 沉淀入测试库）。

| 日期 | 前端/版本 | 结果 | 字段映射偏差 | 差距与修复 |
|---|---|---|---|---|
| 待实测 | SillyTavern（版本待填） | 待回填 | 待回填 | 待回填 |
## 2. E2 · SKILL / AGENTS 导出 → Claude Code 装载实测

**目标**：SKILL 导出产物能被 Claude Code 以 skill 形式装载；AGENTS（project_rules）产物能在 Claude Code 项目级生效（doc_semantics 两出口端到端实证）。
**环境**：需装有 Claude Code（含/不含 MCP 均可）的机器（本工作台不可代跑）。
**准备材料**：
- SKILL 出口现成样例（技术文档装配战例 P06 产物，历史自举三件套之一）：`desktop/tests/fixtures/external/技术文档装配战例/SKILL.md`。
- AGENTS 出口生成命令（doc_semantics=project_rules → AGENTS/CLAUDE 出口，v2.3.0 A3 打通）：`python scripts/nf.py run --pipeline community/技术文档域包/pipelines/P06_技术文档题材装配流管线.md --modules <该包模块 full_id> --seed --doc-semantics project_rules --fmt agents --dest <目录>`（技术文档域包装载清单见 `community/技术文档域包/README.md`）。
- 渲染出口备查：`nf render <pkg_dir> --fmt agents|claude|skill`（协议定义 → 多出口规则，v2.5.0）。
**实测步骤（runbook）**：① 建临时 Claude Code 项目，将 SKILL.md 放入 skills 目录（或按 Claude 规范注册）→ 验证可被 `/` 调用；② AGENTS 产物放入项目根 → 验证项目级规则随会话装载生效（问答抽查 + 日志核对）；③ 按四要素回填下表。
**结果**：待外部实测。
**差距与修复**：无真实装载记录即不转正；Claude Code 侧 skill/AGENTS 规则格式差异如有，本段记录并交 rules_render/export 修复。

| 日期 | 客户端/版本 | 出口 | 结果 | 差距与修复 |
|---|---|---|---|---|
| 待实测 | Claude Code（版本待填） | SKILL | 待回填 | 待回填 |
| 待实测 | Claude Code（版本待填） | AGENTS(project_rules) | 待回填 | 待回填 |

## 3. E3 · `nf serve`（MCP stdio）→ 标准 MCP 客户端实测

**目标**：MCP Server 正式化收口——`nf serve` 能被真实标准 MCP 客户端连接，resources/list + read 可用（只读面与 uri 白名单生效）。
**环境**：需任一支持 MCP stdio 的客户端（Claude Desktop 类；本工作台无 MCP 客户端宿主，不可代跑真实连接）。
**准备材料**：接入文档（快照导出 → 服务启动 → 客户端配置样例 → 能力表 → 错误码）已在 `docs/mcp.md`；实现 = `desktop/src/core/mcp_runtime.py` + CLI `nf serve`；协议版本对齐 `2025-11-25`（A5 核查 G1/G2/G4 已勾销，基线见 `33_v2.2.0_A5-MCP规范差距核查报告.md`）。
**实测步骤（runbook）**：① 按 docs/mcp.md 三步产快照（`nf run --fmt mcp`）并起服务；② 在客户端 mcpServers 注册 nf.py serve；③ 连接后调 `resources/list` 枚举、`resources/read` 取正文、写面方法应回 `-32601`、未知 uri 应回 `-32602`；④ 按四要素回填下表（docs/mcp.md 文末占位同步）。
**结果**：待外部实测。
**差距与修复**：无真实客户端会话记录即不转正（docs/mcp.md 已声明）；若有协议实现偏差，本段记录并交 mcp_runtime 修复。

| 日期 | 客户端/版本 | resources/list | resources/read | 写面拒绝 | 差距与修复 |
|---|---|---|---|---|---|
| 待实测 | 待实测 | 待回填 | 待回填 | 待回填 | 待回填 |
## 4. Y5 · 完整版样本交真实免费 AI 复测

**目标**：把波 A 组装的完整版样本交给「真实免费 AI（agent 用户）」装载开跑或继续扩展——第一个 agent 用户外部验证锚点（并入 S1 口径）。
**环境**：任意能读文件的免费 AI 客户端（DeepSeek / 千问 / Kimi 等，非本工作台）。
**准备材料（已落位）**：
- 预设 A 校园样本（馆藏）：`library/NF-1.md`（引用式历史样本）。
- 预设 B 西幻样本（波 A W3 实证新件）：`docs/完整版样本_西幻生存流P03.md`。
- 取用方式：给 AI raw 直链或文件本体，说「按 ## 6 装载指引开跑」。
**实测步骤（runbook）**：① 任选一样本发给免费 AI；② 让 AI 按 ## 3 注册表投影 → ## 2 管线逐层推进 → 至少跑 3 个回合并输出正文；③ 核对：能否复述模块清单？正文是否过 M80 质检门风格？是否出现编造编号/资产？（三重对账：编号 / 资产键 / 双 AI 复述互验）④ 按四要素回填下表。
**结果**：待外部实测（本工作台不代跑外部 AI）。
**差距与修复**：若样本装载不顺（如引用式缺口导致离线不可跑），记录并升级为自包含档重出样本。

| 日期 | 客户端/模型 | 样本 | 结果（装载/回合/编造检查） | 差距与修复 |
|---|---|---|---|---|
| 待实测 | 待实测 | NF-1 / P03 西幻样本 | 待回填 | 待回填 |

## 5. 汇总与转正门

| 出口 | 当前状态 | 转正条件 | 转正判定 |
|---|---|---|---|
| E1 CCV3 → SillyTavern | 待外部实测（材料已备） | 真实导入成功或明确差距修复 | ☐ 未转正 |
| E2 SKILL/AGENTS → Claude Code | 待外部实测（材料已备） | 真实装载生效或明确差距修复 | ☐ 未转正 |
| E3 nf serve → MCP 客户端 | 待外部实测（材料已备） | 真实连接 + list/read/拒写符合预期 | ☐ 未转正 |
| Y5 样本 → 免费 AI 复测 | 待外部实测（样本已备） | ≥1 样本被真实免费 AI 装载开跑 | ☐ 未转正 |

**结论**：本报告为建档稿（非转正稿）。README 对外宣称维持现状；`docs/mcp.md` E3 占位与本报告共用回填位。任一出入口完成实测即按本报告四要素回填，达验收后再执行 S13（README 宣称逐项转正）+ X1（fixture 沉淀入测试库）。
**回填提示**：回填时勿删本文件任何表头与状态列；只填结果列，并在「差距与修复」写明修复提交号。