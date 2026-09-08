## [2.7.0] - 2026-09-07（40 总纲波 A + 波 B 整合发布 · 首个无壳基础层版本）
### Added
- **发布整合（用户 2026-09-07 拍板「整合到 v2.7」）**：40 总纲波 A（原计划 v2.7.0）与波 B（原计划 v2.8.0）**整合为单一 v2.7.0 发布**；版本号 v2.8.0 顺延给后续常态内容波。首个无壳基础层 tag（分离节奏发布线首验，普通基础层 tag 不产壳）。
- **发布摘要**：波 A = S1 外部验证实证档（`docs_external-validation-v2.7.md`）+ S2 资产供应链台账（`nf asset` + check23）+ S3 首批官方资产集入库 + S8 密钥扫描入 CI + X/Y 线（Y1-Y5 Agent 自助组装 / X2 `docs/mcp.md` / Y9′-Y12′ 云端公共线）+ APK 线彻底移除（裁决 #16）；波 B = S4 管线脚手架（`nf pipeline new`）+ S5 模块生命周期（`nf module` + check24）+ S7 近端（`nf demo` / `nf --help` 分层 / README 五分钟快速开始）。
- **verify 复核**：verify.sh v2.12→v2.13（check23→check24），PASS=35 / WARN=0 / FAIL=0 全绿；ci-verify 绿线 PASS=35。
### 对账表（40 总纲收口：计划项 vs 实际提交）
| 计划项 | 实际提交 | 状态 |
|---|---|---|
| 波 0 治理修订（S6/S8/S9/S11，不产 tag） | 随 main 直接推送（含 docs_audit-38-stage1.md / ROADMAP §9 / CONTRIBUTING §6 / README L3 段） | ✅ 已完成 |
| APK 线彻底移除（裁决 #16） | commit `6663557` + 文档 6 文件同步 | ✅ 已完成 |
| 云端公共线 Y9′–Y12′（不产独立 tag，随 main） | 线上 commit `90ab277` / `43b5d45` / `e4b1fdd` / `088554f` / `984871d` 等 | ✅ 已完成 |
| 波 A W1–W4（S1/S2/S3/X1-3/Y1-5） | commit `947918f` | ✅ 已完成 |
| 波 B S4/S5/S7 近端 | commit `7d9d6b5` | ✅ 已完成 |
| 整合发布 v2.7.0（README 版本块 + CHANGELOG 归档 + audit 建档 + tag） | 本归档条目 + `docs_audit-40-v2.7.md` + annotated tag `v2.7.0` | ✅ 已完成 |
### Notes
- **端壳待接线项：4**（冻结期未接线的 L2 新增能力：资产供应链台账 CLI / 管线脚手架 / 模块生命周期 / 一键演示世界——计数 < 6，壳线冻结持续不触发接线波；脉冲触发条件重计见 L3_FROZEN）。
- **外部实证 E1–E3 / Y5 仍未回填**（需真实 SillyTavern / Claude Code / MCP 客户端 / 免费 AI 机器，本工作台不可代跑）——v2.7.0 版本发布**不等同** S13 宣称转正；回填后按 `docs_external-validation-v2.7.md` 更新 README 相关宣称并追补转正记录。
- 原 [Unreleased] 各波/线实施明细随本版归档为下辖小节（标题保留波 W/线标记，正文原样归档；个别时序性挂账注记以〔修订〕标注收口实况）。
## [2.7.0 · 波B] - 2026-09-07（40 总纲实施波B：S4 管线脚手架 + S5 模块生命周期 + S7 近端引导）
### Added
- **S4 `nf pipeline new`（`desktop/src/core/pipeline_scaffold.py`）**：自 P00 通用骨架派生新管线文档（标题 / 顶层 id / name / tags 领域标签替换；层位 id 守住不动；坏 id / 缺键 / 目标已存在均拒绝写盘不产坏档）+ `scripts/nf.py pipeline new --id --name --from --domain --dest`；单测 5 例全绿。
- **S5 模块生命周期（`desktop/src/core/module_lifecycle.py` + `nf module ls/status/deprecate/restore/verify`）**：04_模块库 + community 模块 status 位解析/写回（缺省 active，元信息行 `状态：…`）；deprecated/retired 被引用（模块依赖/订阅或 community protocol.yaml 命中）→ 引用门禁 FAIL；verify.sh v2.13 新增 check24；全库 44 模块扫描全 active 无违约；单测 7 例全绿。
- **S7 近端引导**：`nf demo` 一键演示世界（P04 轻混全链 → CCV3 chara.json/world.json，质量门 PASS 0/WARN 0/FAIL 0，实测 0.1 s）；`nf --help` 作者/开发者分层引导文案；README 新增「五分钟快速开始」。
- **verify 复核**：PASS=35 / WARN=0 / FAIL=0 全绿（verify.sh v2.12→v2.13，check23→check24，ci-verify 绿线 PASS=34→35）。
### Notes
- 波 B 冒烟记录（本工作台实测、产物不入库）：`nf pipeline new --id P07 --name 演示领域管线 --domain 悬疑` → 派生档结构正确（标题/P07/悬疑领域 tag，层位 P00 未动）；派生 P07 以轻混模块装配 run 可跑 PASSED；module deprecate→status→restore 在 /tmp 副本流转全通过、`nf module verify` 全绿。
- 波 B 收口项仍挂账：S3 续（第二个官方题材包或第三方首例上架，按货架 tier 标准补种）待排。**〔修订·2026-09-07〕**：作者拍板波 A + 波 B 整合为单一 v2.7.0 发布（tag v2.7.0），不再单独产 tag v2.8.0；外部实证 E1–E3/Y5 回填后追补 S13 转正——见本段上方 [2.7.0] 发布归档。
## [2.7.0 · 波A W4] - 2026-09-07（40 总纲实施 W4：S1 外部验证实证档建档 + E1 准备材料实导 + ROADMAP 状态同步）
### Added
- **`docs_external-validation-v2.7.md`（S1 实证报告 · 建档稿非转正稿）**：四项出口（E1 CCV3→SillyTavern / E2 SKILL+AGENTS→Claude Code / E3 nf serve→标准 MCP 客户端 / Y5 完整版样本→免费 AI 复测）各带四要素表（环境/步骤/结果/差距修复）+ 汇总转正门——未实测不宣称转正（S13 门未开，验收未达成如实标注）。
- **E1 准备材料实导落位 `docs/external-validation-assets/`**：`nf run --fmt ccv3` 实导轻混 P04 导出件（chara.json + world.json，质量门 PASS 0 WARN 0 FAIL 0，check19/22 覆盖）——供真实 SillyTavern 装载实测直接取用。
- **ROADMAP §9 波 A 状态同步**：行内状态 🔮 规划 → 🚧 实施中（W1–W4 已提交 2026-09-07），表尾补实施进度注记（外部实测回填 → S13 转正 → tag v2.7.0）。
### Notes
- 本波 W1–W4 的对外转正仍缺最后一环：E1–E3 / Y5 真实外部实测（需有 SillyTavern / Claude Code / MCP 客户端 / 免费 AI 的机器，本工作台不可代跑）。

## [2.7.0 · 波A W3] - 2026-09-07（40 总纲实施 W3：Y4 完整版样本实证（P03 西幻）+ Y5 复测待外部档位）
### Added
- **Y4 实证（对话内组装）落盘 `docs/完整版样本_西幻生存流P03.md`**：装配师 Codex 扮演「仅知仓库地址的外部 agent」，按 `agent_组装指令包_v0.1.md` 取货顺序（07 → 02 → 01/06 → 西幻包）组装**预设 B · 西幻生存流完整版**——P03 管线，26 模块在册（default 24 = 核心 11 + 题材 13，M03/M23 为 P20 allowed 备选）；八段骨架（## 0–## 7）齐，自检 7 项全过；与馆藏 NF-1（预设 A · 校园）配对，装配链在**两个官方预设**均实证走通。
- **样本诚实纪律随行**：引用式档位（规格自包含、正文引用式）；来源清单逐文件可追溯；已知缺口如实声明（23 内容资产未内嵌正文 / 订阅侧逐事件合并表未穷举 / 回合顺序为 06 §3 指导骨架，最终以注册表合并为准 I5）。
- **verify 复核**：PASS=33 / WARN=0 / FAIL=0 全绿（纯新增文档层，未动协议/门禁/代码）。
### Notes
- **Y5 用户复测（待外部执行）**：本样本须交**真实免费 AI** 装载开跑或继续扩展（第一个「agent 用户」外部验证锚点）；本工作台无法代跑外部 AI——复测结果记录位 = `docs_external-validation-v2.7.md`（S1 实证报告，收口 W 建档后回填）。
- **S1 E1–E3（同待外部环境）**：SillyTavern 装载 / Claude Code 装载 / MCP 客户端连接三项实测需真实外部工具，本机无现成环境——下一步为出准备材料与占位报告，不宣称转正。

## [2.7.0 · 波A W2] - 2026-09-07（40 总纲实施 W2：Y 线入口补齐 + X2 MCP 接入文档 + X3 第三方贡献者入口）
### Added
- **Y2 AGENT_START.md（根目录）**：装配师三句话开场（角色 → 取货规范 → 出口自检）+ 能读/不能读仓库分流（B1 自主 / 纯粘贴如实标注）+ 免编造铁律；与 AGENTS.md（开发者纪律）分置不混。
- **Y1 07 §8「Agent 自助组装入口」（完整版规格消费侧引用）**：入口顺序 / 完整版定义 / B1 取货顺序 / 选件铁律 / 自检清单真相源全部指向 `agent_组装指令包_v0.1.md` 与 06，防双源漂移。
- **X2 `docs/mcp.md`（nf serve 接入文档）**：快照导出 → 服务启动 → 标准客户端配置样例 → 能力表（只读 resources/list+read、无 tools/prompts 写路径、uri 白名单）→ 错误码 → **E3 实测记录预留占位**（未实测不宣称转正）。
- **X3 community/README「第三方贡献者入口」**：第一个第三方做什么 / 怎么提交（CONTRIBUTING §4.4 五步 + `nf register`）/ 验收什么（verify PASS≥33：check14/15/23）。
### Changed
- README：A 线单元格指向 `docs/mcp.md`；⚡ 段补 AGENT_START 三句话开场指引；B1 取件清单修正文件名笔误（`07_导航.md` → `07_官方核心出厂与社区预设导航.md`）。

## [2.7.0 · 波A W1] - 2026-09-07（40 总纲实施 W1：S2 资产供应链族 + S3 首批官方资产集入库战例 + S8 密钥扫描入 CI）
### Added
- **S2 nf asset 供应链台账族（40 总纲波A 机制主产出）**：`desktop/src/core/asset_ledger.py`（纯标准库零依赖）+ `scripts/nf.py asset` 子命令族（add / verify / inventory / ls / rm / deprecate / restore）——溯源键表 `provenance.json` 随 add 自动生成；资产文件头 `nf-asset`（key/version/status）与台账双源一致；生命周期 active→deprecated→retired；同键/同文件去重、路径逃逸拒绝。
- **verify check23 资产供应链闭合门禁（verify.sh v2.11→v2.12）**：每资产可溯源（source 必填）/ 可发现（文件在册）/ 键无孤儿（文件头键 ∈ 台账）；存量未托管计 STAT 不阻断；`desktop/tests/test_asset_ledger.py` 15 用例全绿；PASS 31→33。
- **S3 首批官方资产集入库战例**：官方核心资产集（TECH_RULES / TECH_TEMPLATES，module=M90，tier=official）经 `nf asset add` 入库 `05_资产库/provenance.json`——工具链首次实测（verify/inventory/ls 全通，check23 实测）。
- **S8 密钥明文扫描入 ci-verify**：checkout 后全量正则扫常见 token 前缀（ghp_/github_pat_/gho_/sk-/AIza/AKIA/xox*），命中即红；仓库实测零误报（CHANGELOG 弃用记录仅含 `ghp_` 前缀字样、无完整 token，不触发）。
### Changed
- verify.sh 版本 v2.11→v2.12（check23 新增）；ci-verify PASS 绿线 31→33。

## [2.7.0 · APK 线移除] - 2026-09-07（作者裁决 #16：Android APK 线彻底移除）
### Removed
- **android/ 全目录**（app bootstrap/config/controller/ui/screens + main.py + buildozer.spec + p4a 补丁等）——彻底 `git rm`，不再恢复（裁决 #16：包络负资产——首次构建 10h+、v0.8/v0.9/v2.6 三轮闪退修复、CI 绿 ≠ 真机不闪退、学生预算月投入数百；浏览/预览/轻导出三大功能已被 AI 线 A/B1 全覆盖）。
- **build-android.yml / selftest_android.py / sync_android.sh**——APK 构建与自测链随线移除。
- **check_ui_core_links 去 android 化**：脚本 + 单测改桌面 UI-only 引用面（15 用例全绿，verify PASS=31 不变）。
- **文档同步**：README（端壳段/Release 描述/端壳注记）、L3_FROZEN（APK 线移除记录 + 冻结区清单更新）、.github 模板（bug/feature/PR 去 android）、registry_loader 与 e2e-desktop.yml 注释清理。
### Changed
- **移动端产品叙事**：手机用户入口 = 任意 AI 客户端（B1 线：读 raw / 下载文件），不再提供专用 App；桌面 GUI（exe/macOS/Linux）保留冻结-脉冲契约。

## [2.7.0 · 波 0 治理修订] - 2026-09-06（40 总纲；不产独立 tag，随 v2.7.0 发布）
### Security
- **旧 token 弃用记录（40 总纲 S8）**：2026-09-06 会话中使用的 GitHub PAT（`ghp_` 前缀，用于 dispatch 验证）已明文出现在会话记录——**已弃用，不再使用**。轮换 SOP：任何出现在对话/日志/文档中的 token 立即到 GitHub → Settings → Developer settings → Personal access tokens 撤销重建；新 token 仅经环境变量注入，不写入文件/提交/对话。后续 CI/workflow 一律用 `GITHUB_TOKEN`（最小权限，见权限最小化条目），不再使用个人 PAT 触发。
### Changed
- **40 总纲波 0 治理修订**：S6 壳分离触发（build-desktop/build-android `push.tags` v* → `shells-v*`，普通基础层 tag 不产壳，v2.7 = 首个无壳发布）；S8 workflow permissions 最小化（ci-verify/e2e-desktop/build×2 顶层 `contents: read`，需写 job 单独提权）+ Release 资产 sha256 校验和随行；S9 执行对账模板落 `.rivet/reconcile-template.md`（三段式：fetch 核对→规划对照→差异说明，波次完成时填）；S11 40 总纲落盘根目录 + ROADMAP §9「未来计划」节 + CONTRIBUTING §6 安全章程小节 + README L3 段触发口径同步。**端壳待接线项：0**（壳线冻结持续，脉冲触发条件重计，见 L3_FROZEN）。

## [2.7.0 · 云端公共线] - Y9′–Y12′ 云端公共线（40 总纲增补 v1.4，2026-09-07；随 main 直接推送，不产独立 tag，已随 v2.7.0 发布）
### Added
- **Y11′ 云端公共产物馆 · 编号制式 v0.4 上线（90ab277）**：四级编号 `NF-档位段-自定义段-36进制序号`——档位段 = 建构件/成品类型（自由复合拼写、不依赖词表）；序号 = 36 进制（每位 0-9 → A-Z、1 起、无前导零、不定长、同前缀各自计数）；段长 ≤16、前缀小写键全馆唯一；默认形 `NF-1`；入馆唯一硬标准 = 自包含可召回（引用式公开档不再收，历史样本在馆注明）。
- **ALIAS.md 大小写转译站（90ab277）**：机器人每次入库全量重建；AI 大小写拿不准 → 编号全小写化 → 表内匹配真实编号 → 拼 raw（AI 识别协议三路径：快 / 转译 / 慢）。
- **Y12′ 云端代收站 V2（90ab277）**：入库脚本支持四段编号分配（同前缀 36 进制递推）+ 段位校验（配对 / 字符 / 长度）+ 前缀小写键查重拒稿；投稿模板新增档位词/自定义段字段 + 自包含声明；白名单维持仅作者本人（S3 第三方实战前不开放）。
- **40 总纲增补 v1.4（本提交）**：Y9′–Y12′ 云端公共线入总纲（= 双 agent 共享真相源，替代 .rivet/plans 不可见档案）+ 裁决记录 12/13；Y9′ 连通协议设计文档落 `.rivet/plans`（登记面随基础层排期窗口）。
### Changed
- **NF-0001 → NF-1（90ab277）**：默认形迁移（INDEX 登记表 / 文件注记头 / README 示例同步）；README 📚 段与 INDEX 全量泛化去叙事化（建构件 + 成品同馆同档、形态/领域自述）；verify PASS=31 不变（公共层零协议层改动，实测全绿）。
- **入库机器人滥用防御 V2.1（e4b1fdd）**：模板残留净化（字段值以「（」开头或命中说明短语 → 视为未填回退标题/形态/一句话/档位词）+ 空壳拒收（正文残留模板占位行 → 回评提示并关闭）；实测 Issue #1 模板原样提交曾污染入库 NF-2（空壳件已下架）；投稿模板新增懒人模式指引。
- **Gitee 开放投稿前端（43b5d45）**：写入口搬到 Gitee Issues（国内直连，面向所有人开放——零治理：取消白名单、不设审核，滥用出事拉黑/下架）；GitHub Actions 每 10 分钟轮询（gitee_ingest.py + gitee-poll.yml），同一入库核心 → 双端推送 → Gitee 回评双端链接 → 关题（state=closed 幂等 + 注记头「来源：Gitee Issue #N」防重）；依赖 `GITEE_TOKEN` secret（Gitee 专用子令牌：issues 读写 + 推送最小权限，作者主令牌不共享）。
- **40 总纲 v1.5 + INDEX 投稿通道公开化（本提交）**：Y12′ 双前端 + 滥用防御 + 裁决 #14 入总纲（共享真相源同步）；INDEX 投稿须知更新公开投稿指引（Gitee 主入口 + 模板可全不删 + GitHub 仅作者自投）；Gitee 侧投稿模板落 `.gitee/ISSUE_TEMPLATE/NF投稿.md`。
## [2.6.0] - 2026-09-06（v2.6.0 端壳接线波第 1 波：L3 冻结快照恢复 + W1-W9 接线 + Release 产线修复——脉冲式治理首波兑现）
### Added
- **v2.6.0-L3 冻结快照恢复（38 方案 Stage 2.1，51f7130）**：35 个 L3 端壳文件自 5ae202b^ 单 commit 回接——android/（bootstrap/config/controller/ui/screens/main/buildozer/p4a 三补丁）+ desktop/src/ui/（11 py：common/main_window/protocol_wizard_dialog/zone_a-g）+ main.py/src/__main__.py/packaging/smoke_gui/bench/smoke_zone_g_market/selftest_android/sync_android（可整体 revert 回冻）。
- **v2.6.0-W0 漂移扫描（38 方案，476658d）**：`scripts/check_ui_core_links.py`（UI↔core 符号存在性自动盘点，脉冲式接线波基础设施——每波触发先跑它，不入 verify）+ 6 单测；实测 ui+controller 对 v2.5 core 无硬断。
- **v2.6.0-W1 zone_a 读入入口（38 方案，a95ba7e + 368e7ba）**：外部产物读入 GUI 化（34 遗留 F2 · ROADMAP A4）——SKILL.md/chara.json 宽容层解析 → IR 预览 → 登记（调 import_adapter + 类别短名→长名契约归一，防 fid_key 双目录击穿幂等）。9 回归用例。
- **v2.6.0-W2 protocol_wizard doc_semantics 声明（38 方案，8b9a4a1）**：向导加三选一（不声明/project_rules/skill）——34 A3 遗留 GUI 声明 UI 补齐。
- **v2.6.0-W3 zone_c 一键全链执行（38 方案，a79ec1f）**：selected → pipe()（retrieve→compose→gate→export 与 nf run 同路径）→ 结果到质量门/预览区——CLI 优先原则杜绝行为分叉。
- **v2.6.0-W4 zone_c 变体/条件选项（38 方案，6376872）**：装配变体变换入一键执行（apply_variant 前置，与 nf run --variant-add/remove 等价）。
- **v2.6.0-W5 协议包 rules 渲染出口（38 方案，78c18d6）**：协议详情加「渲染 rules…」（agents/claude/skill 三格式，render_protocol 同库 CLI nf render）。
- **v2.6.0-W6 zone_d 导出格式对齐（38 方案，2c64e93）**：五格式下拉（ccv3/skill/agents/claude/mcp）+ do_export_fmt 通用导出（exporter._REGISTRY 全可达，与 CLI nf run --fmt 同库）。
- **v2.6.0-W7 zone_d 质量门可解释面板（38 方案，a42592d）**：warn/fail 逐条展示 actionable 建议（26 方案 B1 suggestion 字段 GUI 化，纯展示层不动门禁语义）。
- **v2.6.0-W8 zone_g 市场目录视图（38 方案，786d96c）**：tier 分级列表（official/community/experimental，list_market 同库 CLI nf market list --tier，B4/C-a GUI 化）。
- **v2.6.0-W9 main_window MCP serve 入口（38 方案，5a3c0e4）**：QProcess 拉起 nf serve（选 mcp.json 快照 → stdio JSON-RPC 子进程，不可线程内嵌；Stage 4 POC 底座）。
- **v2.6.0-G1 ci-verify 修复（38 方案，e01d9a7/ae1c62d/fb2a95a）**：verify.sh check12/18/19 失败回显诊断增强 + CI 干净环境缺 yaml/PySide6 依赖修复 + PySide6 无头 Linux EGL 系统库（libegl1/libgl1）。
- **v2.6.0-G2 Release 产线修复（38 方案）**：build-desktop 干跑三平台全绿（dispatch 34021426960）+ build-android 干跑恢复（APK 构建 34022367652 起稳定 success）——v2.1-v2.5 全 failure 的产线恢复可产出资产。
- **v2.6.0-APK 启动崩溃修复（38 方案，cf33929）**：KivyMD 1.2.0 BaseSnackbar→MDSnackbar 改名 + 文本改 MDLabel children 构造（旧 Snackbar(text=) 启动即崩——emulator logcat 实证 TypeError）——v0.9.0 闪退痛点同类在 x86_64 模拟器的漏网，修复后 emulator 启动冒烟（install→am start→pidof 存活）全绿。
- **v2.6.0-smoke 断言自校准（9cb05a7）**：smoke_gui 内容量断言（≥30/≥2 固定下限）改自校准（模块>0 + 表格一致性、资产包 store↔GUI 一致）——与 v2.6 官方内容面（13 模块/0 官方资产包）漂移假红消除；空 home 反例仍 FAIL 保检出力。本地 offscreen 22/22 全绿。
- **v2.6.0-audit/steelman 判据单一来源（693d52e）**：SECTION_PLACEHOLDERS 占位精确文本 + count_list_entries 导出复用（audit/steelman 跨模块同文单源，骨架假绿锁死回归 55 用例全绿）。
### Fixed
- **v2.6.0-emulator-smoke 环境链（38 方案，d25dade/ae16c92/8533376/23d2b09/ddae6db）**：ubuntu-latest runner 无 /dev/kvm 权限（kvm4all udev 规则）→ APK 相对路径定位失败（$GITHUB_WORKSPACE 绝对路径）→ emulator-runner 逐行 sh -c 变量跨行丢失（单行串联）→ logcat 抓取定位 app 崩溃。
### Changed
- **v2.6.0 发布收口**：L3_FROZEN.md 状态升级「第 1 波完成 → 回冻结」+ 第 1 波记录；ROADMAP §1 v2.6.0 行 + §7.5 A3/A4/B4/C-a GUI 挂账勾销 + §8 指针 6 执行标记；README v2.6.0 块；tag v2.6.0。**端壳待接线项：0**（v2.6 = 第 1 波接线全部兑现，积压清零回冻结；脉冲触发条件重计）。

## [2.5.0] - 2026-09-06（v2.5.0 基础层深化续：A 矩阵补全 + B 挂账 + MCP 运行时化——主线收口）
### Added
- **v2.5.0-Wave1 读入入册（方案 37，ea1a5d1）**：`import_adapter` parse_skill 宽容层资源随行装载（`bundled_resources` 扫描 scripts/references/assets 相对路径 → IR meta 资源清单，供导出随行复制/消费方装载）+ `nf import <file> --register` 内容库登记（parse → 结构校验 → 幂等装载 registry 同源去重，同 30 方案 merge 只增不删纪律）。34 方案遗留「skill 资源随行装载 + 读入→内容库自动登记」关 2。单测 +6（test_import_adapter）。
- **v2.5.0-Wave2 协议层 V2（方案 37，0b0db5f + fed97bd）**：①包版本槽位——protocol.yaml `package.version` 机读字段 + registry protocols[] 条目 version 投影 + 02 §8 登记字段 + check14 ⑦ 元素级比对含版本声明合法性、引用钉扎复核（B4 版本槽位遗留兑现）；②条件组合运行时——`composer.build_assembly` 增 `conditions` 参数（module 声明 variant/condition → 组合时按条件动态裁剪，B2 上半段）。check14/check15 扩展用例 + 变体组合 RED→GREEN 反证。
- **v2.5.0-Wave3 市场本体化收口（方案 37，003d60b）**：`market_analyzer` 上架规则化（消费 35-A7 分级字段——必填/版本/依赖/分级声明规则）+ `list_market/package_grade` + `nf market list --tier=official|community|experimental` 目录视图 CLI 先行 + `nf spec ls`（Spec Registry = C3 并入 B4，版本化 spec 查询）。C-a 模块质量分级消费方闭环。GUI 目录视图仍冻结（L3）。
- **v2.5.0-Wave4 协议多出口渲染（方案 37，6cc3b84）**：新增 `desktop/src/core/rules_render.py`——protocol.yaml（E2 协议向导产物/社区包协议声明）→ agents/claude/skill 三格 rules 渲染（`_RULES_RENDERERS` 注册表，仿 exporter._REGISTRY 模式 + 范围纪律只挂已交付三格）+ `nf render <pkg_dir> --fmt {agents,claude,skill}`。A3 适配矩阵补格：协议定义 → agent rules / SKILL。单测 5 用例全绿（含 round-trip + 范围纪律 + 未登记格式拒出）。
- **v2.5.0-Wave5 MCP 运行时化（方案 37，2851b74）**：新增 `desktop/src/core/mcp_runtime.py`——快照烧成服务：mcp.json（mcp_adapter 静态快照）→ stdio JSON-RPC 运行时。33-A5 报告三差距勾销：G1 形态级（静态文件 → JSON-RPC 会话协议，换行分隔 UTF-8 transport）+ G2 字段级（resources/list 返去 text 纯元数据、正文经 resources/read contents[].text 两段式）+ G4 归属层（name/version 入 initialize 握手 serverInfo）。C2 最小安全层随行：只读（tools/prompts 未实现 → -32601）+ uri 白名单（未知 uri → -32602）。`nf serve <mcp.json>` CLI。单测 9 用例 + stdio 子进程 e2e 冒烟（握手/list/read/白名单/只读五连全过）。
### Fixed
- **v2.5.0-B3 CCV3 资产条目 id 修复（方案 36 Wave1，c1d310f）**：`ccv3_adapter._asset_entries` 资产条目缺 `id` 字段 → 含 asset_refs 的装配导出后 `check_ccv3_world` 报「缺键: id」（测试盲区静默 bug）。修复 = `_asset_entries` 加 `start` 参数续号（id/insertion_order 连续编号，去固定 1000 魔法数）+ `world_entries` 衔接；补 `_narrative_ir_with_assets` 回归用例（RED→GREEN）。单测 267→268。
### Changed
- 34 方案「非目标」persona 表述修订：从「标记占位非真实角色定义」改为「仅透传 chara_meta 不判占位」（对齐 parse_ccv3 源码实际行为）；README 协议链补 36 + v2.5.0 块 + 方案真相源 36_v2.5.0_基础层深化续方案.md 落盘。
- **v2.5.0 发布收口**：verify.sh PASS=31 全绿（Wave1-5 单测收编 check12 discover：268→291）+ README v2.5.0 块切「✅ 已发布」+ ROADMAP §1 v2.5.0 行归位 + §7.5 挂账勾销（A3 多出口渲染 / B2 条件组合 / B4 版本槽位 + Spec Registry / C-a 分级消费方 / C1 MCP 运行时化 + C2 安全层 全 ✅；34 遗留关 2 留 2——skill 资源随行装载 + 读入自动登记已关，CCV3 persona 语义还原 + GUI 接线（F2）留）+ tag v2.5.0（治理指针 3）。**端壳待接线项：9**（38 方案接线账——5 格式导出+体检 / 双向读入+资源随行+登记 / 质量门建议 / 引用反查+rename+impact / 市场深化 / 变体+条件组合 / rules 多出口 / 全链 run / MCP serve；脉冲触发条件 ≥6 已达成，v2.6 = 第 1 波接线）。

## [2.4.0] - 2026-09-06（v2.4.0 外部吸收大包：规范核查三连 + 实现四件）
### Added
- **v2.4.0-A1/A2/A3 规范同步核查三连（方案 35 Wave1，672029e）**：一次性核查报告 `35_v2.4.0_外部规范同步核查报告.md`——SKILL（agentskills.io 实抓）/ CCV3 v3（SillyTavern 官方 validator SSH 实读）/ AGENTS.md（openai/agents.md 官方仓库）三对照 + 差距裁决；发现 A2 spec_version "v3" 为 bug 级差距（ST 导入 fail）。
- **v2.4.0-A4 导出物规范体检 check22（方案 35 Wave2，fbcae71）**：ccv3 spec_version "v3"→"3.0"（修复 ST validator Number("v3")=NaN fail）+ skill name 改 pipeline_id ASCII slug（对齐 name 仅 a-z0-9- 约束）+ license 字段 + export_schema 硬约束（spec_version 数值/skill name 规范/description ≤1024）+ verify check22（PASS 29→31）。
- **v2.4.0-A5 变更助手引用重链（方案 35 Wave2，e1b4c9e）**：`impact_check.rename_module_plan` + `nf rename <old> <new> [--check|--apply]`——references 批量重链闭环（--check 只列不写盘，--apply 合并写 registry protocols[]）。
- **v2.4.0-A6 质量分级徽章（方案 35 Wave2，55bbfaa）**：`market_analyzer.grade_of_module/grades_of_package`（official/community/experimental，官方判定匹配完整 id 防 M22 重号段误判）+ nf market 徽章输出。
- **v2.4.0-A7 上架元数据模板（方案 35 Wave2，84aaa75）**：02 §8.3 登记三要件补上架元数据四元组（版本/作者/兼容/说明，V1 只增不删）+ 模板制作指令包交付自检第 4 条。
### Changed
- verify.sh v2.10→v2.11（check22 入段 C）；单测 258→267（A5 +4、A6 +5、A4 语义）；ROADMAP §7.5 A3-A7 收口 + README 协议链补 35 + 方案真相源 35_v2.4.0_外部吸收大包方案.md 落盘。
- **v2.4.0 发布收口**：CHANGELOG [Unreleased] → [2.4.0] 归档 + README v2.4.0 块切「✅ 已发布」+ tag v2.4.0（治理指针 3）。

## [2.3.0] - 2026-09-05（v2.3.0 基础层深化首波：A3 规则出口打通 + B2 变体装配 + B3 文档 retro-fit + A4 双向读入）
### Added
- **v2.3.0-A3 规则出口打通（方案 34 Wave1，3b132bb）**：doc_semantics 三层透传（render_ir/pipe/nf run `--doc-semantics {project_rules,skill}`）——techdoc 规则装配可显式声明 project_rules → AGENTS.md/CLAUDE.md 出口（修复断链：render_ir 原不写 IR.meta['doc_semantics'] → classify 回退 skill 拒出）。P90 战例 `nf run --fmt agents --doc-semantics project_rules` 产 AGENTS.md。测试 +4。
- **v2.3.0-B2 变体装配（方案 34 Wave2，ff73f2e）**：新增 `desktop/src/core/variants.py`——apply_variant（base+add−remove 幂等）+ variant_assemblies（全变体展开 + 跨变体重叠仲裁报告，声明级不阻断）+ nf run `--variant-add/--variant-remove`（P04 冒烟 PASSED）。裁决：不扩展 references schema（composer freeze），变体 = 装配层模板选择。测试 11。
- **v2.3.0-B3 文档 retro-fit（方案 34 Wave3，0a1f00c）**：M93/M96（通用核心包）补「## 6 不变式遵守（01 §5）」边界段（I1-I5 对齐 M97/M98 形态，内容不造假）；实测修正 M97/M98 已有该段故不动。verify PASS=29 保持。
- **v2.3.0-A4 双向读入反向解析适配器（方案 34，b8409d0）**：新增 `desktop/src/core/import_adapter.py`——parse_skill 双层设计（结构层 NF 导出 frontmatter/层级逐字节还原 mode='nf'；宽容层外部 SKILL.md 降级 tolerant 解析 external + ir=None）+ parse_ccv3 结构还原（chara_card_v3/world.json → IR，同源去重）；IR meta 记 adapter_in 供消费方识别读入来源。单测 19 用例全绿（含自举 SKILL.md 428B 逐字节 round-trip 闭环）。
- **v2.3.0-A4 解锁样例双保险（方案 34，b8409d0）**：自举主样例三件套（技术文档装配战例 SKILL.md + chara.json + world.json）+ Anthropic 官方次样例两份（skill-creator/docx.SKILL.md，宽容层外部兼容锚点 + 外部 spec 真实性锚点）。
### Changed
- exporter.py 补读入反向符号（34 方案 A4）：`_REGISTRY_IN` 反向注册表（格式→解析函数，与 export-only 五出口对称）只挂已交付 skill/ccv3 两格——范围纪律（未启用不出厂）：agents/claude/mcp 暂无读入适配器不登记。
- ROADMAP §1 v2.3.0 行 + §7.5 A3/B2/A4 子项标注落地（A3/B2 本批、A4 双向读入 ✅ 已实现）；README 协议链补 34 + v2.3.0 块；方案真相源 34_v2.3.0_基础层深化首波方案.md + 34_v2.3.0_A4双向读入方案.md 落盘。
- **v2.3.0 发布收口**：CHANGELOG [Unreleased] → [2.3.0] 归档 + README v2.3.0 块切「✅ 已发布」+ tag v2.3.0（治理指针 3）；一并推送 v2.2.0 后 3 补遗（7f73da8/0b7c4e4/931f81e，registry 变更前置机读化 + check22 裁决）。

## [2.2.0] - 2026-09-05（v2.2.0 外部吸收首波：verify 验证纵深 A1-A5 + 方案模板纪律 B1-B2）
### Added
- **v2.2.0-A1 导出产物 schema 合规（方案 33 Wave1，cc3106e）**：verify 新 check19——新增 `desktop/src/core/export_schema.py`（5 导出格式 ccv3/skill/agents/claude/mcp 各建逐键 shape 自检）+ `desktop/tests/test_export_schema.py`（合法产物 PASS、篡改 FAIL）。verify PASS 24→26。
- **v2.2.0-A2 引用反查（方案 33 Wave2，c13fb95）**：`retriever.referenced_by(module_id, path)` 反向引用查询（遍历 registry protocols[].references，裸号 M55 ↔ 限定 id 情感:M55 双向命中）+ `nf who-refers <module_id>` CLI（--registry 可指路径；单测 +6）。
- **v2.2.0-A3 文档完整性门禁（方案 33 Wave2，14e47dc）**：verify 新 check20——模块文档必填项分层校验（官方 13 件强校验 machine_contract/元数据/职责章节；社区机读完备者强校验、未完备存量 WARN 统计，对齐 check16 过渡策略）。verify PASS 26→27。
- **v2.2.0-A4 registry 引用图闭合门禁（方案 33 Wave3，d0dc61b）**：verify 新 check21——新增 `desktop/src/core/impact_check.py`（registry 自洽纯 JSON 门禁：references.source_package 在册 / module_id 裸号归一在源包在列 / 同包无裸号重复 + removal_impact 变更前置影响面查询；15 单测含真源自洽 smoke）。verify PASS 27→29。
- **v2.2.0-A5 MCP 规范差距核查（方案 33 Wave3，181de51）**：一次性核查报告落盘 `33_v2.2.0_A5-MCP规范差距核查报告.md`——mcp.json（27 方案产物）对照 MCP 规范 2025-11-25 schema.ts 实证：G1 形态级（静态快照 vs JSON-RPC 会话，非缺陷）/ G2 Resource.text 属 read 响应非 list 元数据 / G3-G8 合法无返工；check19 边界声明 + C1 MCP Server 立项差距基线。
- **v2.2.0-B1/B2 方案模板纪律（方案 33 Wave4，e68718b）**：CONTRIBUTING 新增 §4.5——NN_ 方案模板必填两段：B1 五问自检（谁消费/何时验证被消费/与非目标边界/与现存协议关系/失败定义）+ B2 消费方声明（功能→谁消费→怎么验证被消费，空消费方不得入方案），防 C-a 无消费方能力重演。
### Changed
- verify.sh v2.9→v2.10（check19/20/21 入段 C，头部/统计配套说明同步；单测 199 OK、PASS=29 全绿）。
- README 协议链追加 33 + v2.2.0 版本块（治理指针 2）；ROADMAP §7.6 条件池（C/D 族，af3d191）+ 执行状态更新；CONTRIBUTING §4.5（B1/B2）；方案真相源 33_v2.2.0_外部吸收首波方案.md 落盘。
- **v2.2.0 发布收口**：CHANGELOG [Unreleased] → [2.2.0] 归档 + README v2.2.0 块切「✅ 已发布」+ ROADMAP §1 v2.2.0 行 + tag v2.2.0（治理指针 3）。
- **v2.2.0 补遗（registry 变更前置机读化闭环，7f73da8）**：`nf impact <target>` CLI——拟删除 module/protocol 前置影响面预检（`removal_impact_protocol` 整包删除 + `impact_of_change` 自动判别 + `--check` 门禁退出码）；check22 不新增（与 check21 重复，前置检查 = 操作时 CLI 消费方而非静态门禁）。33 方案遗留第 1 条闭环。单测 199→222。
- **v2.2.0 补遗（check22 候选裁决，33 遗留第 2 条）**：「示例/边界段落硬性必填」不开立——01 协议对模块文档段落无「示例段/边界段」条文；全仓官方+社区 44 件无一含独立「示例」段（示例散在代码块，无机读锚点）；「违例与边界」为社区格式约定（官方 13 件经违例/边界/不变式遵守任一表述全覆盖，M90 用不变式遵守；社区 4 件元模块 M97/M98/M93/M96 缺属 retro-fit 存量，走 check20 过渡 WARN）。裁决理由落 33 方案「遗留」节。

## [2.0.x] - 2026-09-05（2.0 E2-E5 收口：协议向导 + 组合运行时 + 模块市场雏形 + 仓库盘点）
### Added
- **v2.0.x-E2 协议定义向导（方案 19，031f543 docs + 9bf5055 feat）**：自定义协议 GUI 化落地——`desktop/src/core/protocol_wizard.py`（ProtocolForm + build_protocol_yaml 生成合规 protocol.yaml v2 + self_check）+ `desktop/src/ui/protocol_wizard_dialog.py`（向导 QDialog）+ zone_g「创建自定义协议…」入口（协议定义从手写 Schema 门槛降为填表生成）。
- **v2.0.x-E3 组合运行时调度引擎（方案 20，07b8bf0 docs + caa45f4 feat）**：references 跨包引用运行时消费——`desktop/src/core/composer.py`（resolve_combination 按 registry protocols references 闭包解析 + build_assembly 装配前合并 own+reference 模块正文，轻混 P04 导出 world 现含校园 M55/西幻 M17）；e2e [8] + zone_d 生成默认含引用。
- **v2.0.x-E4 模块市场雏形（方案 21，6699566 docs + 7d3678f feat）**：zone_g 升级检索驱动一站式视图——消费 retriever.search 四类（module/asset_pack/pipeline/protocol 本地资源）结果表 + 按 kind 分流动作（module 加入装配追加进 selected / pipeline 设为当前管线 / asset_pack 选用资产包 / protocol 查看详情）；main_window 增 add_module_to_assembly（追加语义，区别于预设重填）+ set_current_pipeline；装配态标记随 ②③ 勾选联动；`scripts/smoke_zone_g_market.py` offscreen 冒烟（检索命中→加入装配→层树同步→四类齐备）。
- **v2.0.x-E5 模块市场雏形深化（方案 22，69dd4b2 W1 core + 47c0dfd W2 UI）**：community 仓库盘点——新增 `desktop/src/core/community_inventory.py`（catalog 盘点 4 包 29 模块 + 4 管线 + 已装判定；install_module save_module 幂等 / install_pipeline pipelines cache 按 id merge 不覆盖既有）；retriever.search 扩 kind=community_module/community_pipeline（显式指定才并入，E4 四类语义隔离，Hit tags=[来源包,✓已装/可装载]）；zone_g kind 下拉加「社区模块/社区管线」档——未装一键装载入库（module → on_modules_changed / pipeline → reload_pipelines）、已装转加入装配/设为当前管线；`scripts/smoke_zone_g_market.py` [7][8] 装载冒烟（M55 装载入库→标记翻转、P04 cache merge→③ 下拉含）。I5 边界裁决：references 跨包只读（E3）与用户工作区装载（E5，等同 seed_from_repo 既有模式）正交不冲突。
### Changed
- README 协议链追加 19/20/21/22（治理指针 2，收口 E2-E5 落地）。
- **23 方案分层治理**：L3 端壳冻结移出主仓库演进主线——verify.sh v2.9 分层门禁（check13① 去 android 两处比对、check12② compileall 去 android、版本号收口，clone 即绿零前置）+ CI 新增 ci-verify（L0-L2 闸门）+ build-desktop/build-android 退役 main 自动触发（仅 v* tag/手动）+ `L3_FROZEN.md` 真相源落盘（含移出清单索引与接回路径）。L2 core 语义零回归（135 单测/verify PASS=24/e2e 全绿）。

## [2.1.0] - 2026-09-05（v2.1.0 基础层深化：A 适配面 + B 生成器 + C 内容资产化——CLI/库先行 + 自举工具链）
### Added
- **v2.1.0-B2 全链管道化（方案 24，f25ea79 W1 + c59b11f W2）**：retrieve→compose→gate→export 单命令——新增 `desktop/src/core/pipeline.py`（pipe() 单一入口：selected full_id → build_assembly(E3 references 并入) → render_ir → quality_gate 三态 → gate.ok 且非禁阻断才 export；本地缺失项跳过入 warnings；fail_on_gate=False 强制导出诊断产物但 ok 仍 False——可信任度不变量不破）+ `scripts/nf.py` CLI（run 子命令，GateResult 摘要 + FAIL exit 1 镜像 verify 铁律；skill 拒 narrative 的产物×适配矩阵纪律 warnings 透传）。CLI/库先行薄壳形态（L3_FROZEN.md）的地基，L2 首个里程碑。
- **v2.1.0-A1 AGENTS/CLAUDE 适配器 + SKILL 边界裁决机制化（方案 25，74db425 W1 + 98ed908 W2）**：产物×适配矩阵第三格——新增 `desktop/src/core/semantics.py`（两判据裁决唯一真源：`classify_doc_semantics(ir)` meta 显式声明 > title/模块名项目约定词启发 > 缺省回退 skill）+ `agent_rules_adapter.py`（techdoc+project_rules → AGENTS.md/CLAUDE.md 项目约定出口，narrative/能力语义拒出同 skill 纪律）+ exporter 注册 agents/claude；protocol_wizard.self_check 内置 doc_semantics 值域校验 + nf.py --fmt 扩 agents/claude。CLI/库先行 + 裁决规则供向导/生成器复用。
- **v2.1.0-B1 质量门可解释化（方案 26，9d396df）**：quality_gate 三态门 → 可解释报告 + 自动修复建议——`Issue` 加 `suggestion` 字段（缺省空串，向后兼容）+ 四条默认规则各补 actionable 修复指引（R1 空装配→勾选含核心 M00/M80 / R2 缺锚点→勾选 P00/P80 / W1 资产悬空→装包或删引用 / W2 层外→移层位或改层序）+ `GateResult.report_text()` 可解释报告（fail 优先、warn 可行动）；nf.py 质量门打印带建议。warn 从"只提示"变"告诉你怎么改"。
- **v2.1.0-A2 MCP server 定义导出（方案 27，112aad1）**：A 线第四格——新增 `desktop/src/core/mcp_adapter.py`（techdoc IR → mcp.json：`mcp{name, capabilities.resources, resources[]}` 每模块 → Resource uri 层级编码 + text 正文，extra 入不静默丢；narrative 拒出同 skill/agents 纪律）+ exporter 注册 mcp + nf.py --fmt 扩。诚实映射裁决：无结构化工具参数源故做 Resources 型（MCP 官方定义 = client 管理的上下文数据），Tool/Prompt 留待结构化源。
- **v2.1.0-A1 补遗（方案 28，b4994f4）**：ProtocolForm 加 `doc_semantics` 声明入口 + build_protocol_yaml 非空写键（值域拦截，非法抛 ValueError）、空缺省不写（真实实例/登记门禁兼容）——A1 语义裁决闭环完整：向导声明产出语义 → yaml 携带 → self_check 校验（由死代码变生效）→ 下游按裁决路由 AGENTS/CLAUDE 或 SKILL。
- **v2.1.0-B3 协议自举 C+A（方案 29，本批）**：登记缺口治理两段收口——**C 底座**：verify.sh check14 ⑦ module_ids/mount_layers 从长度比对升**元素级全序**（键归一：protocol 长键 `P40 行为决策` → registry 短键 `P40`；同长度漂移现可抓，RED 实证 M65→M66）+ check14 ①/遍历/降级与 check15 遍历/降级**包目录 glob 化**（community/* 扫含 protocol.yaml 目录，新增组合/通用包登记零改 verify.sh）+ ③ 领域包类别互斥泛化两两 + ⑤ segmap 按包名段落定位 + **Windows 分隔符兼容**（glob 反斜杠归一，修跨平台键不一致）；**A 主体**：新增 `desktop/src/core/protocol_projection.py`（protocol.yaml → registry protocols[] 条目，字段与 ⑦ 断言同构，project_all == 现有 4 条目回归锚点；集成自证：产物替换 registry protocols[] 后 verify.sh PASS=24 保持）。B（nf register 自动登记 CLI）留最后一公里——registry 投影由手写变半自动可核。verify PASS=24 + 单测 169 绿。
- **v2.1.0-B3-B 协议登记助手（方案 30，本批）**：B3 自举闭环最后一段接通——`nf register` 本地登记助手把 projection 产物**校验后合并**入 registry protocols[]（替代人工手抄）。02 §9.2 加**豁免子句**（受控路径：包已 §8 在册 + protocol.yaml 合规 → 同步派生投影 = 02 发起登记的机读落地，与 PR 机器人/自动流水线划界）；新增 `desktop/src/core/registry_sync.py`（`check_registerable` 三要件 + `merge_protocols` 只增不删/保键序/幂等——幂等 = 无实质变化不写盘）+ nf.py `register` 子命令（--check 只读 / --apply 写盘后提示 verify 自证；02 未在册 exit 2）。集成自证：registry 漂移 → --check 检出不写盘 → --apply 修复 → verify check14 ⑦ PASS=24。verify PASS=24 + 单测 177 绿。
- **v2.1.0-B4 市场协议 CLI 先行（方案 31，本批）**：check15 ②③ 判据提为可 import 库——新增 `desktop/src/core/market_analyzer.py`（`dependencies` 依赖闭包无环/叶⊆官方13/源包嵌套 references + `conflicts` 挂载层键归一 default 交集）+ nf.py `market <包目录>` 子命令（登记状态 + 依赖闭包 + 冲突预检，CLI 先行门禁前移）。**瑶光发现已修（31 补遗）**：verify.sh check15 ② 源包嵌套检查原误取 dependencies.references 恒空（references 与 dependencies 平级居 package 层）——verify.sh 判据改 `pkg2.get('references')`（package 层），RED 反证注入嵌套可抓、真 4 包 PASS=24 保持。verify PASS=24 + 单测 184 绿。
- **v2.1.0-C-b techdoc 域包战例（方案 32，本批）**：C 线内容库资产化首个落地——community 第 5 包「技术文档域包」（第一个非叙事题材域包，README 扩展新领域三步完整战例）。自带 M97 术语管理 / M98 修订记录（落 M91-99 社区段，已实证空闲）+ core_modules 引官方 13 件含 M90 + P06 技术文档题材装配流管线 + 02 §8 登记；**verify.sh check14 ③ R2 类别互斥从 DOMAIN 扩为 ALL_PKGS 全两两**（新题材域包自带模块落社区段不进 DOMAIN，类别仍须与社区包无交集；现有 4 包类别空交集不误报）；**nf register --apply 工具链实战**写 registry protocols[] 第 5 条（30 方案首次对新领域包走通三要件拦截→放行）+ nf market info 输出在册/无冲突；测试锚点改动态 N 条（registry 4→5）。verify PASS=24 全绿（⑦ 内部 5 包元素级全过）+ 单测 184 绿。

## [2.0.0] - 2026-09-05（v2.0.0 导出层：上游生成器——E0 三件套 + CCV3/SKILL 出口）
### Added
- **v1.2.0 协议中转站 v2（IR 内容归一化，2.0 E0-①）**：ir.py IRDocument/IRLayer/IRModule + normalize_module_body + ir_to_md（IR 默认 MD 适配器）；generator.render_ir 装配→IR（层序/层外/资产 refs+missing 归一），generate_document 改两段（render_ir+ir_to_md），对外 MD 输出零回归（一致性 diff 逐字节）。方案 14。
- **v1.3.0 Agentic 检索（2.0 E0-②）**：retriever.search() 四类统一入口（module/asset_pack/pipeline/protocol），结构化 grep 不上向量 + Hit 元数据卡片（对齐 Agent Skills Discovery）。方案 15。
- **v1.4.0 质量治理闭环（2.0 E0-③）**：quality_gate.run_gate 三态质检门（空装配+核心锚点 fail / 资产悬空+层外 warn，ok()=fail==0 不变量）；zone_d 生成后三态展示；verify check17 入段 C（PASS→23）。方案 16。
- **v2.0.0 导出层 CCV3 首发（2.0 E1 收口）**：立项核心发现=CCV3 语义错配（NF 装配=世界规则集→character_book 主承载，persona 主角占位）；ccv3_adapter（IR→chara_card_v3+world，引擎锚点排除/资产独立/无静默丢弃）；exporter 格式注册表 + PNG 卡（QImage tEXt，零新依赖）；e2e 导出战例（真实组合包→IR→质量门→export 全绿）；zone_d「导出 CCV3」按钮（质量门 FAIL 阻断）；verify check18 入段 C（PASS→24）。方案 17。
- **v2.0.x SKILL 出口插件**：skill_adapter（techdoc IR→SKILL.md agentskills 格式；narrative IR 拒出——产物×适配矩阵第二行机制化）。方案 18。
### Changed
- verify.sh v2.6→v2.8（check17 质量门 / check18 导出契约，PASS 22→24）。
### Fixed（Windows 跨平台，本分支修复）
- registry_loader.asset_get 路径包含硬编码 '/' → is_relative_to（Windows resolve 反斜杠致资产寻址全拒）。
- verify.sh check16 漏用裸 python3 stub（对齐 PY3 回退）。
- e2e_desktop_headless stdout GBK reconfigure（Windows cp936 ✓ 崩溃）。

# Changelog

> 格式约定：Keep a Changelog 中文化（Added/Changed/Fixed 语义）；版本段按时间倒序；[Unreleased] = 当前主线开发中；发布即归档为 [版本号] + 日期段并打 annotated tag（ROADMAP §8 治理指针 3）。
> 基线说明：本文件随 v0.6.0 方案 B 第①步落盘（2026-09-04）；早期版本（v0.1.0–v0.5.0）条目按 git 版本史（八 tag）回写简述。

## [1.1.0] - 2026-09-04（v1.1.0 社区通用核心基础包）
### Added
- T4-1 通用核心基础包（P05 核心基础流）战例落盘（C1=395e59a）：community 新增第 4 个社区包——protocol.yaml（schema v2，core_only 12 件官方配合、references 零跨包、0 资产）+ README 装载手册 + pipelines/P05（核心基础流）+ M93–M96 四模块（各带 machine_contract）；登记三要件②③实况落位（02 §8.3 通用类整包登记 + registry protocols[] 第 4 条投影程序化生成自 protocol.yaml、双源一致）；community/README 目录导览新增本包行（4 包全覆盖）；verify.sh check14/check15 扩容（CORE 第三类变量独立入 ALL_PKGS、①段/降级段 for 3→4 目录、check15 PKGS 3→4），复验 PASS=22 WARN=0 FAIL=0 全绿。

## [1.0.0] - 2026-09-04（v1.0.0 全平台正式版）
### Added
- 13_v1.0.0_全平台正式版方案.md 落盘（方案真相源，I5）：v1.0.0 定位为「全平台正式版·打好地基——协议层收口 + 社区生态收口 + 双端质量收口，功能扩展一律外推」。连续八版（v0.1–v0.9）协议/平台/生态快速演进后，历版方案 §6 开放问题与 ROADMAP 范围外声明累计 6+ 条「明示留待 v1.0.0」收口项一次兑现。问题全景 A1–A3（A1 协议层三处半收口：契约仲裁仅 WARN / 模块头契约无机读 / asset_readonly 无运行时 / A2 社区生态无协作流程与真实战例 / A3 双端发布质量无端到端闸门）；改进收口 B1–B3（B1 协议层收口：模块头契约机读化 + 自动契约仲裁 WARN→FAIL + desktop Runtime asset_get 跨包只读寻址 / B2 社区生态收口：CONTRIBUTING 协作流程五步 + community/「校园 × 西幻轻混」完整可玩组合包战例 / B3 双端发布质量收口：端到端测试入 CI 缺口⑩闭环（桌面 headless 断言 + Android 模拟器启动冒烟最小集）+ 正式发布仪式三件套终态收口）；任务分解 T1 协议层收口（T1-1 机读化 → T1-2 仲裁升级 → T1-3 只读寻址，check16 随 T1-3 一次性入段 C）→ T2 社区生态收口（T2-1 流程文档化 → T2-2 完整战例，依赖 T1）→ T3 双端发布质量收口（T3-1 端到端入 CI，依赖 T2-2 → T3-2 发布仪式终态 + tag v1.0.0）；提交规划 C0–C8（C0 仅动文档 PASS=20 保持；C1–C3 中间态 PASS=20 保持；C4 起 PASS=22 终态）。ROADMAP §1 L15 v1.0.0 状态切「🔵 当前主线」+ §7 一句话展开完整范围（✅三做/❌三不做）落盘；README 协议链追加 13、新增 v1.0.0 🔵 块引用、v0.9.0 块引用切「✅ 已发布 2026-09-04」；本段下方 [0.9.0] 段归档为治理指针 3 发布归档收口（v0.9.0 发布时遗留，原 [Unreleased] v0.9.0 段内容原样迁入不增删改）。
- T1-1 模块头 machine_contract 机读块落地（A1/B1，C1-1=49e8f93）：01_核心协议.md §1 模块契约声明补 machine_contract 机读块规范 + §7 迁移记录（+33 行）；04_模块库官方 13 件模块头各补 machine_contract 机读块（各 +15 行）——模块契约（inputs/outputs/events）从人读声明升级为机读可解析字段，为 check16 自动契约仲裁提供机读判据（11 §6 开放问题 4 收紧路径的机读前提；字段级新增不 bump，C1–C3 中间态 PASS=20 保持）。
- T1-2 自动契约仲裁升级（A1/B1，C1-2=e0300cd）：02 §8.4 登记判定规则④由「契约 WARN 提示、不阻断装配」升级为「契约断裂 FAIL 阻断 + 自动仲裁」（删除「留 v1.0.0 生态收口」标记，条款原文更新）+ 仲裁判据条款（模块头机读契约 inputs/outputs/events + 01 §1 events publish⊆subscribe 语义）+ §9.1/§9.2 同步。
- T1-3 desktop Runtime asset_get 跨包只读寻址（A1/B1，C3=17eac3a）：desktop/src/core/registry_loader 实现 references.asset_readonly 声明资产的跨包只读寻址运行时通道（白名单授权校验 + 只读不复制，I5 单一真相源闭环）——组合包声明 asset_readonly: true 后即有运行时通道可消费源包资产，「组合可玩」最后一块拼图补齐（引擎级组合调度不做，❌②纪律）。
- T1-3 check16 契约仲裁门禁入段 C（A1/B1，C4=69b078e）：verify.sh v2.6 四处同步 + check16 双断言入段 C（check16-A 契约仲裁 FAIL 断言：相邻装配 publish ⊄ subscribe 即 FAIL；check16-B 运行时寻址授权一致断言），PASS 20→22 全绿——自动契约仲裁从人读复核升级为 CI 自动闸门。
- T2-1 第三方协作流程文档化（A2/B2，C5=8380d3f）：CONTRIBUTING.md 升级「社区包协作流程」章节（§4.4 提交→PR 评审→登记→发布五步含检查单）+ 02 §9.2 补协作流程纪律条——10 §6 开放问题 4「流程治理留待 v1.0.0 生态收口」兑现。
- T2-2 完整可玩组合包战例落盘（A2/B2，C6=5e5f957）：community/「校园 × 西幻轻混」完整可玩组合包（P04 轻混装配流管线 + M91 异界身份桥/M92 轻混装配执行 + references 组合引用 M55/M17 + asset_readonly 资产只读授权 + README 装载手册；02 §8.4 YAML 骨架示例升级为真实可装载包）；registry protocols[] 投影第 3 条；verify.sh check14/15/16 适配组合包自动发现，verify PASS=22 全绿 + headless 端到端冒烟可跑通——11 §6 开放问题 3 + 02 §8.4 战例延期 1 版兑现。
- T3-1 端到端测试入 CI（A3/B3，C7=5b35c44）：scripts/e2e_desktop_headless.py 桌面端到端断言（真实生成链路：装载组合包 → 选管线 → 按层装配 → 生成文档 → 产物断言，33 项断言实跑全绿 exit 0）入 CI（.github/workflows/e2e-desktop.yml 独立 workflow）；build-android.yml 追加 android-emulator-smoke job（模拟器 boot → 安装 release APK → 真实启动不闪退冒烟最小集）——缺口⑩（双端「真实启动 + 真实生成链路」自动化端到端验证）闭环；12 §6 开放问题 1 运行时答案；真机手动验收保留为发布前最终门禁。
## [0.9.0] - 2026-09-04（v0.9.0 Android 同步门禁 + APK 闪退修复）
### Added
- 12_v0.9.0_Android同步门禁与APK闪退修复方案.md 落盘（方案真相源，I5）：v0.9.0 定位为「Android 同步门禁 + APK 闪退修复——把 sync --check 差异校验接入 CI（缺口⑦闭环：Android↔真源一致性不再靠人工）；对 APK 闪退修复做验证归档 + 纳入 CI 回归门禁保障」。关键前提（git merge-base 实证）：三处闪退修复代码（6b9445e MDRadioButton→MDCheckbox + MDTopAppBar 去 subtitle / 7fd6c0f bump / e92f119 CJK 字体注册）均已含于 v0.8.0 历史——本版对闪退定位 =「验证修复已含历史版本 + 归档根因链 + CI 门禁保障」，非新写修复代码。问题全景 A1–A3（A1 闪退修复已含 v0.8.0 但无 CI 回归保障 / A2 CI 同步不带 --check 缺口⑦ / A3 三件套版本状态滞后于 git 事实）；改进收口 B1–B3（B1 验证归档 + selftest_android.py UI 启动安全静态断言三断言：无 MDRadioButton import / MDTopAppBar 无 subtitle kwarg / _register_cjk_fonts 定义 + build() 首行调用 / B2 build-android.yml 同步步骤后追加 sync --check 自证闸门（保留生成步骤再自证，规避 fresh checkout 生成物缺失边界）/ B3 三件套收口 + v0.9.0 语义厘清）；任务分解 T1 静态断言（无前置）→ T2 CI --check 闸门（无前置，与 T1 可并行）→ T3 版本收口核验（依赖 T1/T2）；提交规划 C0–C3（本版无协议层改动，verify.sh PASS=20 不变）。ROADMAP §1 L14 v0.9.0 状态切「🔵 当前主线」+ §6 范围细化落盘；README 协议链追加 12、新增 v0.9.0 🔵 块引用、v0.8.0 块引用切「✅ 已发布 2026-09-04」；本段下方 [0.8.0] 段归档为治理指针 3 发布归档收口（v0.8.0 发布时遗留，原 [Unreleased] v0.8.0 段内容原样迁入不增删改）。

- T1 UI 启动安全静态断言入冒烟（A1/B1，C1=6bea61f）：scripts/selftest_android.py 在控制器纯逻辑链路后追加第 [10] 段「UI 启动安全静态断言」三则（纯 python3 文件读取零 Kivy 依赖，任一 FAIL = 冒烟 exit 1）——①screens.py 行锚定正则（`^\s*from\s+kivymd\.uix\.selectioncontrol\s+import\s+MDRadioButton\b`，re.M）断言无 MDRadioButton 真实 import（KivyMD 1.2.0 已移除该类 → ImportError 闪退根因一；行锚定排除 _radio_row docstring 中旧代码根因描述文本误伤——首版裸子串匹配被正向运行实证误伤后修正）②main.py `MDTopAppBar\([^)]*subtitle=` 正则断言无 subtitle= kwarg（TypeError 闪退根因二）③main.py `_register_cjk_fonts` 定义在场 + build() 函数体首个非空非注释行断言含调用（CJK 方块字根因三）。三修复点（6b9445e MDRadioButton→MDCheckbox + MDTopAppBar 去 subtitle / e92f119 CJK 字体注册）均已含于 v0.8.0 历史（git merge-base 实证），本断言将修复点纳入 CI 回归保障——KivyMD 再 bump 或修复代码回退即被拦截；反向验证实证：sed 注入 MDRadioButton import → selftest exit 1 且 [10.a] 精确 FAIL，mv 恢复后 exit 0 全绿。
- T2 CI 同步步骤追加 --check 自证闸门（A2/B2，C2=66579c3）：build-android.yml「同步共享源码与种子数据」步骤后追加一步「双端一致性自证闸门（sync --check，缺口⑦）」（`run: bash scripts/sync_android.sh --check`）+ 注释说明——缺口⑦闭环：android/app/{core,seed} 为 .gitignore 生成物（不入库），v0.8.0 收口曾现人工漏同步双端漂移（core/registry.json 源 6110B vs 生成物 4186B 停旧快照）实证，一致性不再靠人工；保留生成步骤后再自证（fresh checkout 下生成物缺失，直接替换 --check 会命中缺失边界必然失败，已实证删生成物→sync 重建→--check exit 0）；有差异 exit 1 fail CI、无差异放行后续冒烟/构建。

## [0.8.0] - 2026-09-04（v0.8.0 自定义模块组合）
### Added
- 11_v0.8.0_自定义模块组合方案.md 落盘（方案真相源，I5）：v0.8.0 定位为「自定义模块组合——在 v0.7 开放协议注册之上对外开放模块组合，第三方题材模块可在 P00 骨架上自由组合装配为新的社区管线（方案甲：references 受控跨包引用）」。问题全景 A1–A3（A1 模块组合无机读通道 / A2 组合装配合法性无门禁 / A3 管线派生纯人读无组合清单）；改进收口 B1–B3（B1 组合引用 Schema 化 / B2 组合登记机制 + registry protocols[] references 投影 / B3 check15 组合门禁）；任务分解 T1 组合引用 Schema 规范 → T2 组合登记 + 两包 retro-fit + registry protocols[] → T3 verify.sh check15 + v2.5；提交规划 C0–C4。ROADMAP §1 行 13 v0.8.0 状态切「🔵 当前主线」+ §5 范围细化落盘；README 协议链追加 11、版本行切 v0.8.0（当前主线·开发中）。
## [0.7.0] - 2026-09-04（v0.7.0 自定义协议）

### Added
- T1 协议声明 Schema 机读化（B1）：01 §6 新增 6.1 第三方协议声明 protocol.yaml Schema 规范（必填 12 字段表 + R1→dependencies / R2→categories+module_id_range / R3→pipeline+mount_layers 映射 + M91-M99 编号规则 + 模板），社区包根目录必带 protocol.yaml。
- T2 注册流程机读化 + 投影扩展（B2）：02 §8.3 升级「登记 = protocol.yaml 在场 + 本表在册 + registry.json protocols[] 投影」三要件 + §9.1 字段映射表 §8↔protocols[] 行 + §9.2 社区登记同步纪律第 4 条；校园/西幻两包 retro-fit 落 protocol.yaml（校园 51 行 / 西幻 69 行）作首例战例，两包 README 补双源一致声明；registry.json 增 protocols[] 两包投影（schema_version 保持 "2"，V1 只增不删）。
- T3 注册门禁 check14（B3）：verify.sh 升 v2.4 新增 check14 社区协议登记门禁（入段 C 无条件执行）——protocol.yaml 在场 / Schema 必填 12 字段 yaml 解析 / R2 类别不冲突 / R1 依赖边界 / M91-M99 不占用 + 编号在册一致 / protocol.yaml↔README 双源一致 / registry protocols[] 投影一致，七项全绿 PASS=19。

### Changed
- 10_v0.7.0_自定义协议方案.md 落盘（方案真相源，I5）：v0.7.0 定位为「自定义协议——在 v0.6 统一入口之上对外开放协议注册，第三方可按协议声明注册自定义协议，进入注册表登记与门禁调度」。问题全景 A1–A3（A1 第三方协议注册无机读入口 / A2 协议声明无机读 Schema / A3 注册无门禁校验）；改进收口 B1–B3（B1 protocol.yaml Schema 机读化 / B2 注册流程机读化 + registry.json protocols[] 投影 / B3 check14 注册门禁）；任务分解 T1 协议声明 Schema 规范 → T2 两包 retro-fit + 02 §8.3/§9 升级 + registry.json protocols[] → T3 verify.sh check14 + v2.4；提交规划 C0–C4。ROADMAP §1 行 12 v0.7.0 状态切「🔵 当前主线」+ §4 范围细化落盘；README 协议链追加 10、版本行切 v0.7.0（当前主线·开发中）。

## [0.6.0] - 2026-09-04（v0.6.0 协议中转站）

### Added
- 工程治理三件套落盘：ROADMAP.md（五版本路线唯一规划真相源 + 治理指针四项）/ CHANGELOG.md（本文件）/ CONTRIBUTING.md（Conventional Commits + 四步验证门槛 + 三改动域细则）。
- .github 模板：ISSUE_TEMPLATE（bug_report / feature_request）+ PULL_REQUEST_TEMPLATE（改动域勾选 + 门禁自检清单）。
- verify.sh 增 check12 代码层门禁（desktop/tests/test_core.py 40 用例 unittest + py_compile 语法抽查）。
- T1.1 机读投影落地（协议中转站 B1 第一步）：desktop/src/core/registry.json 落盘（registry_schema_version "2"，13 件模块表 / P00–P80 挂载点含 P40/P60 optional / 四组固定订阅）；02 §9 机读投影声明 + 字段映射 + 同步纪律；registry_schema_version 1→2 V2 bump 首例（迁移记录四步见 02 §9.3）。
- T2 迁移机制落地（B2 第二步）：verify.sh 增 check13 迁移完整性门禁（02 §2 模块表 13 件 ↔ registry.json modules 逐条机读比对，python3 heredoc 断言）；verify.sh 升 v2.3 三段式门禁（段 A check1–6 / 段 B check7–11 / 段 C check12–13 无条件执行）。
- T3 sync --check 落地（B3 第三步）：scripts/sync_android.sh 增 `--check` 只读差异校验（core 段 diff -rq 排除 __pycache__ / seed 段逐目录 diff / `_ck_err` 汇总 exit 0/1），基态/异态双态自测通过，同步逻辑本体零改动。

### Changed
- 09_v0.6.0_协议中转站方案.md 落盘（方案真相源，I5）：v0.6.0 定位为「协议中转站——协议体系从人读规范文档升级为机读可驱动的通用协议层」。三项改进收口：B1 协议统一入口（02 §9 机读投影 registry.json + desktop Runtime 装载器 registry_loader，I5 扩展为「文档层 + 机读投影双校验唯一」）；B2 迁移机制落地（01 §7 实操模板 + registry_schema_version 1→2 V2 bump 首例 + verify.sh check13 断言）；B3 同步工具链 --check（sync_android.sh 只读差异校验，有差异 exit 1）。任务分解 T1 协议统一入口 → T2 迁移机制（依赖 T1.1 bump 素材）→ T3 sync --check（独立并行）；提交规划 C0–C5。

## [0.5.0] - 2026-09-04（v0.5.0 优化版）

### Added
- T1 编号治理收口：重号类别前缀全限定（M22/M10 等带 通用:/事件:/生存:/情感: 前缀），verify.sh check2 限定扫描。
- T2 社区包装配：P02 校园情感流 / P03 西幻生存流两套预设；R1 包间禁互引 / R2 类别独占 / R3 装配契约；07 §7 终验清单 Mxx 引用全限定收口。
- T3 记忆分层：认知边界（M23）与记忆分层模块落地。
- T4 M80 门禁流水线：M80 §3 gate 三档升级为声明式 gate_action 流水线（pass: [direct] / warn: [self_correct, log_revision] / fail: [rewrite, retry_limit:3, fallback: white_sketch]）+ gate_decision_record 决策记录格式（系统日志独立通道，不进叙事文本）；P90 引用闭合（以 M80 §3 为唯一真相源）；verify.sh check5 补 gate_action / gate_decision_record 断言。
- T5 资产工作台化：三方对账脚本 scripts/reconcile_assets.sh + verify.sh check11 门禁 + 两份 assets/README 标注列与官方核心对照修正。
- T6 社区发布规范收口。

### Changed
- verify.sh v2.1：两段式门禁（段 A 官方核心 check1–6 / 段 B 社区领域包 check7–11，缺包 WARN 跳过）。

## [0.4.0] - 2026-09-04（两级结构收口）

- 平台 v1.1 起两级结构：官方核心 13 件（通用 6 / 事件 5 / 世界 1 / 技术文档 M90）+ 社区领域包登记（02 §8）。
- 07 §7 项 8 裸 M22/M40 补情感: 类别前缀；selftest_android.py 对齐官方收敛结构（管线 P02→P01，android seed 仅 P00/P01/P90）。

## [0.3.0 / 0.3.1 / 0.3.2 / 0.3.3] - 2026-09-03 / 09-04（Android 首次 APK 发布与构建链修复系列）

- v0.3.0：Android 首次 APK Release（buildozer 裸机 master 方案 + KivyMD 五屏 UI 闭环）。
- 0.3.1–0.3.3：构建链修复——minapi 23→24（CPython3.14 remote_debugging 用 preadv/pwritev，bionic 自 API24 才声明）；pin NDK r25b（解锁 kivy 2.3.0 cgl_gl clang compile）；p4a pin #3180；python -m build --skip-dependency-check（绕过 dist-info 残留误报）；CI 失败诊断注解回传（::error::、TAIL30、clang error 行精确抓取）。

## [0.2.0] - 2026-09-03（Android 端落地）

- Android 端 KivyMD 五屏 UI + controller 闭环 + buildozer CI 工作流（弃三方 docker action，改裸机 master 方案）。

## [0.1.0] - 2026-09-03（桌面首发）

- 模块化叙事引擎项目文件全量交付（01 协议 / 02 注册表 / 03 管线 / 04 模块 / 05 资产 / 06 执行协议 / 07 社区预设 + 十项验收 verify.sh）。
- 桌面三平台 Release（CI 构建，Release 资产加平台后缀）+ 社区版模板工作流 + MIT License。
