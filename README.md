# Narrative Forge · 文档生成工坊（规范驱动）

> **NarrativeForge（NF）** 原创开源 · MIT License · 衍生 / 引用请注明来源

**Narrative Forge 是一台规范驱动的结构化文档生成器（元工具/文档工厂）**。它按协议校验结构，与文体无关：小说、技术文档、设定集都适用。叙事世界（P01/P02/P03）目前应用最成熟。

**生成路径**：自然语言意图 → 按协议模板填充（模块/管线/资产三正交装配）→ `bash verify.sh` 结构校验（分层门禁 check1-31，v2.21）→ 输出结构化文档/可运行世界。

**三个正交维度（均可增删改）**：
- 模块（04_模块库）：领域能力原语，按 01 §2 声明接口后登记即被调度。
- 管线（03_管线库）：数据流转骨架，含领域无关的 P00 通用骨架（装载→语境推进→实体状态→内容生产→决策→装配→一致性→素材→输出）；P01/P02/P03 是 P00 在叙事领域的实例装配。新领域复制 P00 派生新管线即可，引擎不改一行。
- 资产（随领域包分发）：数据模板/素材，按键挂载供模块裁剪注入。领域资产位于 community/<领域包>/assets/（随包附带溯源索引）；05_资产库仅留用户自定义扩增槽与总索引（见 05_资产库/README.md）。

## ⚡ 如果你是 AI / Agent（先读这段）

本仓库同时是 **NF 协议的「AI 自适配入口」**：无论你能不能访问 GitHub、会不会用工具，只要**能读文本**，就能按协议组装 / 运行叙事世界。先按下方路由表自检能力边界，再走对应路径——路由表基于多模型实测（2026-09-06：豆包 / Kimi / 千问 / DeepSeek / 本地模型）。

> 🔗 **给 AI 的入口请用 raw 链接**（实测：部分 AI 能抓 raw.githubusercontent.com / gitee.com 的 raw 直链，但抓不了 Gitee 仓库主页 HTML）——把下方 raw 链接发给 AI 而非网页地址：
> - 规则总入口：`https://raw.githubusercontent.com/Monyeah777/NarrativeForge/main/README.md`（国内镜像：`https://gitee.com/monyeah777/narrative-forge/raw/main/README.md`）

> 🔗 代理式 agent 若被要求「作为装配师开工」，先读根目录 `AGENT_START.md`（三句话开场：角色 / 取货规范 / 出口自检）——本 ⚡ 段为完整路由，二者同源不冲突。

**先按用户意图开局**：
1. **组装「完整版」**（把用户需求变成可直接开跑的世界文档）→ 按下方能力表选线：A 线（agent）/ B1 线（免费客户端）
2. **运行一份现成完整版** → 请用户提供完整版 md，按其 `##6. 装载指引` 执行
3. **制作单件**（一个模块 / 资产包）→ 单件生产属另一指令族，请用户参照 `community/模板制作指令包.md`
4. **逛云端图书馆（公共）** → 让用户报编号（如 `NF-1` 或 `NF-WORLDCAMPUS-Monyeah777-1`，编号制式见下方 📚 段）直接取用，或让用户描述需求由你查 `library/INDEX.md` 推荐（见下方 📚 段）

### 第一步 · 对号入座（按连接能力选线）

| 你的身份 | 能力边界（实测） | 执行通道 |
|---|---|---|
| **Agent**（Operit、Claude 等 · 有 API / 能执行代码） | clone 仓库、跑 verify、可接 MCP | → **A 线**：`nf serve` MCP 深度集成（检索/装配/登记全能力；接入文档见 `docs/mcp.md`——随基础层 v2.7 S1-E3，E3 实测记录待回填） |
| **免费客户端 AI**（DeepSeek / 千问 / Kimi · 非 API） | 能读 raw 直链、能下载文件（产物另存 .md 仅几分钟） | → **B1 线**：非 API 主推大众盘（下方 B1 · 完整装配） |
| **纯粘贴客户端**（豆包 / 本地模型） | 只能读用户粘贴的文本 | → ~~B2~~ **已免除**（2026-09-07 作者裁决）：自取 `paste_card.md`，不推不维护 |

> ⚖️ **A 线与 B 线同等级**：agent 与非 API 用户都是服务对象、无高下之分——只是非 API 体量大得多、是主要盘；B 线内以 B1（能读 raw / 能下载）为主推，按连接能力选线即可，选到哪条都是完整通道。

### 第二步 · 执行

#### B1 · 完整装配模式（你能读 raw）

取件基底：`https://raw.githubusercontent.com/Monyeah777/NarrativeForge/main/`（后接文件名）。

1. 读装配指令包（内容通道取货顺序 + 选件铁律 + 骨架 + 自检）：`agent_组装指令包_v0.2.md`
2. 按指令包取件：`01_核心协议.md`（模块/管线/资产契约）→ `02_联动注册表.md` → `06_Agent执行协议.md` → `07_官方核心出厂与社区预设导航.md` → 用户所需 `community/<领域包>/`（含包内 README 装配清单）
3. 选件 → 按骨架组装 → 过 `##7. 自检清单` → 输出完整版 md（引用式档位：契约摘要 + 缺口如实声明，禁止编造未读内容）

### ~~B2 · 纯粘贴创作~~（已免除 · 2026-09-07 作者裁决）

纯粘贴通道**不再维护**——「用户非得用豆包那是用户的问题」：能下载文件的客户端（DeepSeek / 千问 / Kimi）产物另存 `.md` 仅几分钟，无需为极端受限场景养专门通道。

- 自取（仅纯文本场景，产物质量自担，不再迭代）：`paste_card.md`
- 留档价值判定依据：迷你协议卡相对一般 prompt 直贴属「吊打」级（八段硬骨架 + 编号域约束 M91–M99 + 资产键闭合 + 事件闭合 + 自检七项闭环 + 防静默截断分片规则），故留档不删；但**不随协议演进、不投入维护**。

### 产出验收（同一把尺）

交付前核对：八段骨架是否齐全？模块编号是否合法（M91–M99）？模块要素是否齐全？事件是否闭合？自检清单是否逐条自答？——任一为否，先修正再交付。完整版可直接复制给任意叙事 AI 按 `##6. 装载指引` 开跑。

### 🧭 用户侧：想组装完整版，用哪个模型？（基于 2026-09-06 四模型实测）

| 你的场景 | 推荐模型 | 实测依据 |
|---|---|---|
| 快速迭代 / 边改边看 | **DeepSeek** | 效率最高、协议理解最深（能引用官方模块原编号）；产物是聊天文本，需复制另存 .md |
| 正式交付 .md 成品 | **千问** | 直接产出 md 文件 + 一键分享给其他前端 |
| 最严谨的终稿 / 查漏补缺 | **Kimi** | 最长最细、自检最严（9 项），适合终审把关 |
| ~~豆包（纯粘贴）~~ | ~~B2 已免除~~ | 自取 `paste_card.md`，产物质量自担——不推不维护（2026-09-07 裁决） |

**通用流程**：把需求发给所选模型（B1：直读 raw 取件装配；纯粘贴：自取 `paste_card.md`）→ 收产物另存 `.md` → 交给任意叙事 AI 按 `##6. 装载指引` 开跑。四模型实测报告见社区实测记录（本地归档，不随仓库分发）。

## 五分钟快速开始（CLI · 作者向）

仓库零第三方依赖、clone 即跑（Windows 建议 Git Bash；无需桌面壳）。以下几步五分钟走通「验证 → 演示 → 跑管线 → 派生新领域」：

1. **跑全量验证（改任何库先过这关）**：`bash verify.sh` —— L0-L2 分层门禁 v2.21（check1-31）全绿 PASS=49 才可提交。
2. **一键演示世界**：`python scripts/nf.py demo` —— 自动装载社区「校园 × 西幻轻混」P04 管线全链跑通并导出 CCV3 成品（chara.json + world.json），产物路径与质量门（PASS/WARN/FAIL）直接打印。
3. **看帮助分层引导**：`python scripts/nf.py --help` —— 作者命令（run / demo / pipeline new）与开发者治理工具族分列说明；逐条用法看各子命令 `--help`。
4. **跑一条自己的管线**：`python scripts/nf.py run --pipeline community/校园西幻轻混组合包/pipelines/P04_轻混装配流管线.md --modules 通用类:M00,轻混类:M91,轻混类:M92,通用类:M80 --seed --fmt ccv3 --dest <输出目录>`
5. **新领域派生管线**：`python scripts/nf.py pipeline new --id P07 --name 演示领域管线 --domain 悬疑`（自 P00 骨架派生 → 按 01 §2 填层名/挂载 → 登记 02 联动注册表 → run 即调度，引擎不改一行）。
6. **模块状态与弃用流转**：`python scripts/nf.py module ls` / `module status <模块md>` / `module deprecate <模块md> --reason <原因>` / `module restore <模块md>` / `module verify`（引用门禁，与 verify check24 同语义）。

7. **CLI 健康与补全**：`python scripts/nf.py doctor`（环境自检）`/ help <子命令>`（单命令帮助）`/ completion bash`（shell 补全，zsh/fish 同）`/ --version`；数据命令（`sig`/`diff`/`market --list`/`asset ls`/`asset inventory`/`module ls`/`related`/`doctor`）加 `--json` 输出结构化结果。

> 详细装配规格见 `agent_组装指令包_v0.2.md`；模块 / 资产怎么写见 `community/模板制作指令包.md`。

## 分层与端壳（L3 冻结）

本项目分四层治理（23 方案 + 38 方案脉冲升级）：L0 协议层 / L1 内容层 / L2 核心逻辑层（`desktop/src/core`，纯 Python 零依赖，**高频迭代主战场**）/ L3 端壳层。端壳（桌面 GUI）是包络层——**默认冻结，触发条件达成时执行脉冲式接线波**（**Android APK 线已整体移除**，2026-09-07 裁决 #16，见 L3_FROZEN）（未接线新能力 ≥6 项或用户/消费方必须项），波后回冻结，不随基础层逐功能演进（详见 `L3_FROZEN.md`）。

端壳源码已移出主仓库演进主线（git 历史保留），产出时从冻结快照恢复并触发构建 workflow（壳线专用：仅 `shells-v*` 标签 / 手动触发——40 总纲 S6，基础层 v* 不再产壳）：Release 页可下载 `NarrativeForge.exe` / macOS / Linux 成品（`.github/workflows/build-desktop.yml`）。**Android APK 已不再产出（2026-09-07 裁决 #16）**——手机用户入口 = 任意 AI 客户端（B1 线：读 raw / 下载文件），无需专用 App。

基础层验证不依赖端壳：`bash verify.sh`（v2.21，L0-L2 分层门禁 check1-31，clone 即绿 PASS=49）+ `python scripts/e2e_desktop_headless.py` + `python -m unittest` 全绿即可。

## 社区版模板闭环（自制模板 → 组装 → 输出 MD）

社区版的核心用法：从本仓库 GitHub 界面下载规范，用**任意非 API 免费客户端 AI**（豆包、DeepSeek、Kimi、文心一言、ChatGPT 免费版、本地模型等）制作自己的模板，再导入桌面工具勾选组装，输出 MD 交给叙事前端：

1. **下载规范**：阅读/复制 `community/模板制作指令包.md`（模块/管线/资产包三格式 + M91–M99 社区预留号段）。
2. **AI 做模板**：把指令粘贴给任意客户端 AI，描述你的需求（例：「做一个校园悬疑系统」），AI 输出模板正文。
3. **导入组装**：将 AI 输出的正文另存为 .md，拖入桌面工具 → 自动解析校验 → 勾选模块 → 选管线与资产包 → 生成 MD。
4. **开始叙事**：把生成的 MD 交给叙事前端（SillyTavern 等）使用，或继续导入更多模块扩展世界。

图文流程与 FAQ 见 `community/README.md`。

## 协议链
01_核心协议 → 02_联动注册表 → 03_管线库 → 04_模块库 → 05_资产库 → 06_Agent执行协议 → 07_官方核心出厂与社区预设导航 → 08_v0.5.0_优化版方案 → 09_v0.6.0_协议中转站方案 → 10_v0.7.0_自定义协议方案 → 11_v0.8.0_自定义模块组合方案 → 12_v0.9.0_Android同步门禁与APK闪退修复方案 → 13_v1.0.0_全平台正式版方案 → 14_v1.2.0_协议中转站v2方案 → 15_v1.3.0_Agentic检索方案 → 16_v1.4.0_质量治理闭环方案 → 17_v2.0.0_导出层CCV3方案 → 18_v2.0x_SKILL出口插件方案 → 19_v2.0x_协议定义向导方案 → 20_v2.0x_组合运行时调度引擎方案 → 21_v2.0x_E4模块市场雏形方案 → 22_v2.0x_E5模块市场雏形深化方案 → 24_v2.1.0_全链管道化方案 → 25_v2.1.0_AGENTS适配器方案 → 26_v2.1.0_质量门可解释化方案 → 27_v2.1.0_MCP适配器方案 → 28_v2.1.0_A1补遗方案 → 29_v2.1.0_B3协议自举方案 → 30_v2.1.0_B3B协议登记助手方案 → 31_v2.1.0_B4市场协议CLI先行_nf-market方案 → 32_v2.1.0_C-b-techdoc域包战例方案 → 33_v2.2.0_外部吸收首波方案（A5 MCP 规范核查报告见 33_v2.2.0_A5-MCP规范差距核查报告.md） → 34_v2.3.0_基础层深化首波方案 → 35_v2.4.0_外部吸收大包方案（规范核查报告见 35_v2.4.0_外部规范同步核查报告.md） → 36_v2.5.0_基础层深化续方案。
> **v2.10.0 内容波收口 · 45 质量纵深/基础层 A 组随波发布**（✅ 已发布 2026-09-09，tag v2.10.0）：45 W1-W20（基线自锁/指令审计/载荷 30-30/回合 drill/资源分页/--answer/bump/逐模块覆盖率）+ 基础层 A1-A5 全部收口；verify v2.21 check1-31 PASS=49。
> **v2.9.0 内容波收口 · STRATEGY + 43/44 随波发布**（✅ 已发布 2026-09-08，tag v2.9.0）：STRATEGY 战略层（目标/质量唯一/内部法官/发布边界）+ 43 协议层元工具（check28-31、schema 子集自洽、事件闭包进 golden）+ 44 CLI 顶尖化（doctor/help/completion/json 自洽矩阵）+ 动态 drill（7 主线）+ AI 通道（内容通道/需求自组装/用户自定义/需求档案，nf assemble）。verify v2.21 check1-31 PASS=49。
> **v2.8.0 波 C 首个内容波 · 40 总纲 41/42 工程收口**（✅ 已发布 2026-09-08，tag v2.8.0）：41 波 C 质量编译深化（C1 `nf sig` / C2 `nf diff`+check25 / C3 语义矛盾 check26 / C4 `nf related` See-Also / C5 `nf explain` / C6 需求收敛模板 / C7 MCP 只读 tools/prompts / C8 transport 评估 / C9 回合指针 + D2-D6）+ 42 质量纵深 M1-M5 随波收口（执行失范 drill / 判级器 06 §11 / check27 纯度体检 / doc_hygiene 内容边界 / VERSION-MATRIX / coverage·lint CI）。verify.sh v2.21 PASS=49（check1-31），core 覆盖率 85%。外部实测线按 41 封存注记冻结，E3/B1/NF-FIELD-001 回填后补转正。方案真相源见 41_v2.8.0_波C质量编译深化规划.md 与 42_顶尖质量纵深工程规划.md。
> **v2.7.0 无壳基础层 · 40 总纲波A+波B 整合发布**（✅ 已发布 2026-09-07，tag v2.7.0）：首个无壳基础层版本——分离节奏发布线首验（普通基础层 tag 不再产壳，壳集中波另行 `shells-v*`）。波 A（S2 资产供应链台账 `nf asset` + check23 / S3 首批官方资产集入库 / S8 密钥扫描入 CI / Y1-Y5 Agent 自助组装线 / X2 `docs/mcp.md` / S1 外部验证实证档建档）+ 波 B（S4 `nf pipeline new` / S5 模块生命周期 `nf module` + check24 / S7 近端 `nf demo` + `nf --help` 分层 + README 五分钟快速开始）整合一版发布。verify.sh v2.13 PASS=35（check1-24）。外部实证 E1–E3 / Y5 回填后按 S13 转正补记。方案真相源见 40_未来计划总纲_三层评估短板解决方案与分波实施.md。
> **v2.6.0 端壳接线波第 1 波**（✅ 已发布 2026-09-06，tag v2.6.0）：L3 冻结快照恢复 + W1-W9 接线（zone_a 外部读入 / wizard doc_semantics 声明 / zone_c 一键全链 + 变体选项 / rules 多出口 / zone_d 五格式导出 + 质量门可解释面板 / zone_g 市场 tier 视图 / main_window MCP serve 入口）+ Release 产线修复（G1 ci-verify + G2 build-desktop/build-android 干跑 + APK 启动崩溃 MDSnackbar 修复 + emulator 启动冒烟全绿）。桌面冒烟 22/22 + verify v2.11 PASS=31。端壳待接线项 0（脉冲式治理首波兑现回冻结）。方案真相源见 38 方案合并稿。
> **v2.5.0 基础层深化续**（✅ 已发布 2026-09-06，tag v2.5.0）：主线收口——读入入册（parse_skill 资源随行装载 + nf import --register 登记）+ 协议层 V2（package.version 槽位 + 条件组合运行时）+ 市场本体化收口（nf market list --tier + nf spec ls）+ 协议多出口渲染（rules_render：protocol.yaml → agents/claude/skill）+ MCP 运行时化（mcp_runtime：快照 → stdio JSON-RPC，33-A5 报告 G1/G2/G4 差距勾销 + C2 只读白名单安全层 + nf serve）。verify v2.11 PASS=31。方案真相源见 36（CCV3 修复）+ 37 方案提交线。
> **v2.4.0 外部吸收大包**（✅ 已发布 2026-09-06，tag v2.4.0）：规范同步核查三连（SKILL/CCV3/AGENTS 报告）+ 实现四件（A4 导出物规范体检 check22 / A5 变更助手 nf rename / A6 质量分级徽章 / A7 上架元数据）。verify v2.11 PASS=31。方案真相源见 35。
> **v2.3.0 基础层深化首波**（✅ 已发布 2026-09-05，tag v2.3.0）：A3 规则出口打通（doc_semantics 三层透传 → AGENTS/CLAUDE）+ B2 变体装配（variants.py + nf --variant）+ B3 文档 retro-fit（M93/M96 补不变式遵守段）。verify v2.10 PASS=29。方案真相源见 34。
> **v2.2.0 外部吸收首波**（✅ 已发布 2026-09-05，tag v2.2.0）：verify 从协议一致性加深到产物与语义完整性——A1 导出 schema 合规（check19）/ A2 引用反查（referenced_by + nf who-refers）/ A3 文档完整性门禁（check20）/ A4 registry 引用图闭合门禁（check21）/ A5 MCP 规范差距核查（报告落盘）；B1/B2 方案模板纪律（CONTRIBUTING §4.5 五问 + 消费方声明）。verify v2.10 PASS=29。方案真相源见 33。
> **v2.1.0 基础层深化**（✅ 已发布 2026-09-05，tag v2.1.0）：A 适配面 + B 生成器 + C 内容资产化 CLI/库先行首波——A1 AGENTS/CLAUDE 适配器（semantics 裁决）+ A2 MCP server 导出 + A1 补遗（doc_semantics 接通）；B1 质量门可解释化 / B2 全链管道化（pipe() + nf CLI）/ B3 协议自举（check14 ⑦ 元素级 + glob 化 + 投影生成器）/ B3-B 登记助手（nf register）/ B4 market CLI 先行（依赖/冲突可查）；C-b techdoc 域包战例（第 5 包非叙事域包）；+ 23 分层治理（L3 端壳冻结）。verify v2.9 PASS=24。方案真相源见 23–32。
> **2.0 导出层序列（v1.2.0–v2.0.x，✅ 已归位 2026-09-05）**：从「叙事工具」到「多协议导出层」（CCV3/SKILL/MCP 等格式适配）——v1.2 协议中转站 v2（IR 内容归一化）/ v1.3 Agentic 检索（四类统一 search）/ v1.4 质量治理闭环（quality_gate + check17）/ v2.0.0 CCV3 导出（映射层+exporter+PNG+check18+GUI 导出）/ v2.0.x SKILL 出口插件（产物×适配矩阵：techdoc→SKILL、narrative→CCV3）/ v2.0.x-E2 协议定义向导（自定义协议 GUI 化）/ v2.0.x-E3 组合运行时调度引擎（references 跨包运行时消费）/ v2.0.x-E4 模块市场雏形（zone_g 检索驱动一站式视图）/ v2.0.x-E5 模块市场雏形深化（community 仓库盘点：可发现 → 可装载）。verify v2.8 PASS=24。方案真相源见 14–22。
> > **v1.1.0 社区通用核心基础包**（✅ 已发布 2026-09-04）：T4-1 通用核心基础包战例落盘（C=395e59a）——community 第 4 包「P05 核心基础流」：protocol.yaml schema v2（core_only 12 件、references 零跨包、0 资产）+ M93–M96 四模块（machine_contract）+ registry protocols[] 第 4 条投影；verify.sh check14/check15 扩容 3→4 目录、复验 PASS=22 全绿。版本演进与任务记录见 ROADMAP 与 CHANGELOG。
> **v1.0.0 全平台正式版**（✅ 已发布 2026-09-04）：全平台正式版·打好地基——一次兑现历版方案 §6 开放问题与范围外声明累计 6+ 条「明示留待 v1.0.0」收口项：①协议层收口（02 §8.4 规则④契约 WARN→FAIL 强校验 + 模块头契约机读化 + desktop Runtime asset_get 跨包只读寻址，check16 入段 C、verify.sh v2.6 PASS 20→22）；②社区生态收口（CONTRIBUTING「提交→PR 评审→登记→发布」协作流程五步 + community/「校园 × 西幻轻混」完整可玩组合包战例）；③双端发布质量收口（端到端测试入 CI 缺口⑩闭环：桌面 headless 断言 + Android 模拟器启动冒烟最小集 + 正式发布仪式三件套终态收口 + tag v1.0.0）；方案真相源见 13_v1.0.0_全平台正式版方案.md；版本演进与任务记录见 ROADMAP 与 CHANGELOG。
> **v0.9.0 Android 同步门禁 + APK 闪退修复**（✅ 已发布 2026-09-04）：闪退修复代码（MDRadioButton→MDCheckbox / MDTopAppBar 去 subtitle / CJK 字体注册）已含于 v0.8.0 历史（git merge-base 实证），本版对其做验证归档 + 回归断言入冒烟（selftest_android.py UI 启动安全静态断言三断言），并把 Android↔真源同步差异校验接入 CI（build-android.yml sync 步骤后追加 sync_android.sh --check 自证闸门，缺口⑦闭环）；方案真相源见 12_v0.9.0_Android同步门禁与APK闪退修复方案.md；版本演进与任务记录见 ROADMAP 与 CHANGELOG。
> **v0.8.0 自定义模块组合**（✅ 已发布 2026-09-04）：在 v0.7 开放协议注册之上对外开放模块组合——第三方题材模块可在 P00 骨架上自由组合装配为新的社区管线（references 受控跨包引用：01 §6.1 Schema v1→v2 → 02 §8.4 组合登记 + registry.json protocols[] references 投影 → verify.sh check15 组合门禁 v2.5）；方案真相源见 11_v0.8.0_自定义模块组合方案.md；版本演进与任务记录见 ROADMAP 与 CHANGELOG。
> **v0.7.0 自定义协议**（✅ 已发布 2026-09-04）：在 v0.6 统一入口之上对外开放协议注册——第三方按 protocol.yaml 协议声明注册自定义协议（01 §6.1 Schema 规范 → 02 §8.3 登记三要件 + registry.json protocols[] 投影 → verify.sh check14 注册门禁 v2.4，全量 PASS=19 全绿）；校园/西幻两包 retro-fit 为首例战例；版本演进与任务记录见 ROADMAP 与 CHANGELOG。

## 📚 云端图书馆（公共 · 编号寻址 · AI 可召回）
### 🧭 导购路由表（AI 接待员先读这个）
收到项目地址的 AI = 本馆接待员：用户说一句自然语言需求 → 你查 `ROUTES.md`（仓库根，双镜像均有）→ 拼 URL 直达。开场先回「🧭 菜单」：🎮 组装新世界 / 🎁 报编号取件 / 🔍 描述需求求推荐 / 🎲 随机盲盒 / 📮 投稿入库。核心规则：**镜像换前缀（GitHub ↔ Gitee）、后缀不动**；raw 形态喂 AI、网页形态给人；编号大小写拿不准先读 `library/ALIAS.md` 转译；**馆里没有的 → 严禁编造，如实说没有并引导「现场创作 + 投稿入库」**（决策流详见 ROUTES.md：命中 / 随机 / 未命中 / 转译 **A–H 八路径**——编号直达/模糊推荐/随机盲盒/未命中引导创作投稿/大小写转译/一堆需求批量汇总/连续会话保持状态/丢网址 AI 自抓（raw 优先，抓不到如实说 + 引导粘贴））。

NarrativeForge（NF）有一个**云端公共图书馆**（`library/`）：建构件与成品（世界 / CCV3 / 协议 / 管线 / 模板 / 域包…任何形态与领域）按 **NF 编号**归档，全馆开放——**任何 AI 仅凭编号即可通过链接调用，一次生成、永久召回**。

**编号制式（四级）**：`NF - 档位段 - 自定义段 - 36进制序号`——档位段 = 建构件/成品类型（WORLD / CCV3 / PKG / PROTO…可自由复合如 WORLDCAMPUS）；自定义段 = 用途或署名；序号 = 每位 0-9 → A-Z 递增（1,2,…9,A,…Z,10…），同前缀各自计数。不填档位/自定义 = 默认形（如 `NF-1`）。

- 目录（AI 导购/取阅入口）：`library/INDEX.md`（编号 | 标题 | 形态/领域 | 一句话）
- 大小写转译（AI 专用）：`library/ALIAS.md`（编号拿不准大小写 → 全小写化后在表内匹配真实编号）
- 取件基底（GitHub）：`https://raw.githubusercontent.com/Monyeah777/NarrativeForge/main/library/`（后接 `编号.md`）
- 取件基底（国内镜像 Gitee · 无需梯子）：`https://gitee.com/monyeah777/narrative-forge/raw/main/library/`（同规则）

**对用户**：想玩现成产物 → 对任意 AI 说「运行 NF 编号」或「帮我找 XX」；想把产物永久存档 → 投稿审核后获得编号，以后随时报号召回，无需重新生成。

**对 AI**：用户报编号 → 拼链接读取 → 按文档执行；大小写拿不准 → 先读 `library/ALIAS.md` 转译再拼链接；用户要推荐 → 先读 INDEX 筛选再报号。投稿须原创/已授权、且**自包含可召回**（文件自带「是什么 + 怎么用」，AI 单文件即正确使用；引用式不再收，见 INDEX 投稿须知）。

**📮 云端代收站（投稿自动化）**：AI 产物怎么进图书馆？在仓库 Issues 开题，标题写 `【NF投稿】作品名`，按 Issue 页「📚 NF 云端投稿」模板把产物全文粘贴到正文点提交——云端机器人自动按制式分配编号、入库、更新目录（INDEX + ALIAS），并在该 Issue 回复调用链接（约 1 分钟，全程无需懂代码）。AI 会读不会写？「人粘贴一次，剩下全自动」。全文控制在约 6 万字符内（平台限制），超长交给作者身边助手。

## 开箱即玩：社区领域预设
两套开箱预设以社区领域包随仓库分发（07 §3 索引）：
- **校园情感流（P02）**：装载手册 `community/校园情感领域包/README.md`（9 题材模块 + 29 资产，关系驱动）
- **西幻生存流（P03）**：装载手册 `community/西幻生存领域包/README.md`（14 题材模块 + 23 内容资产，生存驱动）
两包结构统一：README（速览/装载/资产/规则/验收）+ modules + assets + pipelines；制作规范见 `community/README.md` 与 `community/模板制作指令包.md`。

## 扩展新领域（三步）

① 在 community/ 下建领域包，包内 modules/ 按协议增题材模块 → ② 包内 assets/ 增资产模板并登记溯源索引（assets/README.md）→ ③ 复制 P00 派生新管线放包内 pipelines/，并在 02 §8 社区登记表登记，verify.sh 自动纳入 I5 调度。

## 核心逻辑层（desktop/src/core/）

基础层真身：纯 Python 零第三方依赖的装配/IR/质检/导出/检索逻辑，被端壳（桌面 GUI / android）复用。L0-L2 验证入口：

- 分层门禁：`bash verify.sh`（v2.21，check1-31 全绿 PASS=49，clone 即绿；Windows 用 Git Bash / WSL 跑 `bash`）
- 单元测试：`cd desktop && python -m unittest discover -s tests`
- 端到端：`python scripts/e2e_desktop_headless.py`（直驱 core，无需 GUI/端壳）

> 端壳层（桌面 GUI `desktop/src/ui`）已冻结移出演进主线，详见 `L3_FROZEN.md`——接回时从 git 历史恢复；**Android APK 线已整体移除（2026-09-07 裁决 #16，git 历史可回溯）**。
