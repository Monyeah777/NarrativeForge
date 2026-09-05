# Narrative Forge · 文档生成工坊（规范驱动）

**Narrative Forge 是一台规范驱动的结构化文档生成器（元工具/文档工厂）**。它按协议校验结构，与文体无关：小说、技术文档、设定集都适用。叙事世界（P01/P02/P03）目前应用最成熟。

**生成路径**：自然语言意图 → 按协议模板填充（模块/管线/资产三正交装配）→ `bash verify.sh` 结构校验（十三项门禁，check1-13）→ 输出结构化文档/可运行世界。

**三个正交维度（均可增删改）**：
- 模块（04_模块库）：领域能力原语，按 01 §2 声明接口后登记即被调度。
- 管线（03_管线库）：数据流转骨架，含领域无关的 P00 通用骨架（装载→语境推进→实体状态→内容生产→决策→装配→一致性→素材→输出）；P01/P02/P03 是 P00 在叙事领域的实例装配。新领域复制 P00 派生新管线即可，引擎不改一行。
- 资产（随领域包分发）：数据模板/素材，按键挂载供模块裁剪注入。领域资产位于 community/<领域包>/assets/（随包附带溯源索引）；05_资产库仅留用户自定义扩增槽与总索引（见 05_资产库/README.md）。

## 分层与端壳（L3 冻结）

本项目分四层治理（23 方案）：L0 协议层 / L1 内容层 / L2 核心逻辑层（`desktop/src/core`，纯 Python 零依赖，**高频迭代主战场**）/ L3 端壳层。端壳（桌面 GUI / Android APK）是包络层——**当前冻结，最后一次性产出交付形态**，不随基础层演进（详见 `L3_FROZEN.md`）。

端壳源码已移出主仓库演进主线（git 历史保留），产出时从冻结快照恢复并触发构建 workflow（仅 v* 标签 / 手动触发）：Release 页可下载 `NarrativeForge.exe` / macOS / Linux 成品（`.github/workflows/build-desktop.yml`），APK 由 `.github/workflows/build-android.yml` 产出。

基础层验证不依赖端壳：`bash verify.sh`（v2.9，L0-L2 分层门禁，clone 即绿）+ `python scripts/e2e_desktop_headless.py` + `python -m unittest` 全绿即可。

## 社区版模板闭环（自制模板 → 组装 → 输出 MD）

社区版的核心用法：从本仓库 GitHub 界面下载规范，用**任意非 API 免费客户端 AI**（豆包、DeepSeek、Kimi、文心一言、ChatGPT 免费版、本地模型等）制作自己的模板，再导入桌面工具勾选组装，输出 MD 交给叙事前端：

1. **下载规范**：阅读/复制 `community/模板制作指令包.md`（模块/管线/资产包三格式 + M91–M99 社区预留号段）。
2. **AI 做模板**：把指令粘贴给任意客户端 AI，描述你的需求（例：「做一个校园悬疑系统」），AI 输出模板正文。
3. **导入组装**：将 AI 输出的正文另存为 .md，拖入桌面工具 → 自动解析校验 → 勾选模块 → 选管线与资产包 → 生成 MD。
4. **开始叙事**：把生成的 MD 交给叙事前端（SillyTavern 等）使用，或继续导入更多模块扩展世界。

图文流程与 FAQ 见 `community/README.md`。

## 协议链
01_核心协议 → 02_联动注册表 → 03_管线库 → 04_模块库 → 05_资产库 → 06_Agent执行协议 → 07_官方核心出厂与社区预设导航 → 08_v0.5.0_优化版方案 → 09_v0.6.0_协议中转站方案 → 10_v0.7.0_自定义协议方案 → 11_v0.8.0_自定义模块组合方案 → 12_v0.9.0_Android同步门禁与APK闪退修复方案 → 13_v1.0.0_全平台正式版方案 → 14_v1.2.0_协议中转站v2方案 → 15_v1.3.0_Agentic检索方案 → 16_v1.4.0_质量治理闭环方案 → 17_v2.0.0_导出层CCV3方案 → 18_v2.0x_SKILL出口插件方案 → 19_v2.0x_协议定义向导方案 → 20_v2.0x_组合运行时调度引擎方案 → 21_v2.0x_E4模块市场雏形方案 → 22_v2.0x_E5模块市场雏形深化方案 → 24_v2.1.0_全链管道化方案 → 25_v2.1.0_AGENTS适配器方案 → 26_v2.1.0_质量门可解释化方案 → 27_v2.1.0_MCP适配器方案 → 28_v2.1.0_A1补遗方案 → 29_v2.1.0_B3协议自举方案 → 30_v2.1.0_B3B协议登记助手方案 → 31_v2.1.0_B4市场协议CLI先行_nf-market方案 → 32_v2.1.0_C-b-techdoc域包战例方案 → 33_v2.2.0_外部吸收首波方案（A5 MCP 规范核查报告见 33_v2.2.0_A5-MCP规范差距核查报告.md）。
> **v2.2.0 外部吸收首波**（🔵 主线执行中，方案 33）：verify 从协议一致性加深到产物与语义完整性——A1 导出 schema 合规（check19）/ A2 引用反查（referenced_by + nf who-refers）/ A3 文档完整性门禁（check20）/ A4 registry 引用图闭合门禁（check21）/ A5 MCP 规范差距核查（报告落盘）；B1/B2 方案模板纪律（CONTRIBUTING §4.5 五问 + 消费方声明）。verify v2.10 PASS=29。方案真相源见 33。
> **v2.1.0 基础层深化**（✅ 已发布 2026-09-05，tag v2.1.0）：A 适配面 + B 生成器 + C 内容资产化 CLI/库先行首波——A1 AGENTS/CLAUDE 适配器（semantics 裁决）+ A2 MCP server 导出 + A1 补遗（doc_semantics 接通）；B1 质量门可解释化 / B2 全链管道化（pipe() + nf CLI）/ B3 协议自举（check14 ⑦ 元素级 + glob 化 + 投影生成器）/ B3-B 登记助手（nf register）/ B4 market CLI 先行（依赖/冲突可查）；C-b techdoc 域包战例（第 5 包非叙事域包）；+ 23 分层治理（L3 端壳冻结）。verify v2.9 PASS=24。方案真相源见 23–32。
> **2.0 导出层序列（v1.2.0–v2.0.x，✅ 已归位 2026-09-05）**：从「叙事工具」到「所有 AI 协议标准的上游生成器」——v1.2 协议中转站 v2（IR 内容归一化）/ v1.3 Agentic 检索（四类统一 search）/ v1.4 质量治理闭环（quality_gate + check17）/ v2.0.0 CCV3 导出（映射层+exporter+PNG+check18+GUI 导出）/ v2.0.x SKILL 出口插件（产物×适配矩阵：techdoc→SKILL、narrative→CCV3）/ v2.0.x-E2 协议定义向导（自定义协议 GUI 化）/ v2.0.x-E3 组合运行时调度引擎（references 跨包运行时消费）/ v2.0.x-E4 模块市场雏形（zone_g 检索驱动一站式视图）/ v2.0.x-E5 模块市场雏形深化（community 仓库盘点：可发现 → 可装载）。verify v2.8 PASS=24。方案真相源见 14–22。
> > **v1.1.0 社区通用核心基础包**（✅ 已发布 2026-09-04）：T4-1 通用核心基础包战例落盘（C=395e59a）——community 第 4 包「P05 核心基础流」：protocol.yaml schema v2（core_only 12 件、references 零跨包、0 资产）+ M93–M96 四模块（machine_contract）+ registry protocols[] 第 4 条投影；verify.sh check14/check15 扩容 3→4 目录、复验 PASS=22 全绿。版本演进与任务记录见 ROADMAP 与 CHANGELOG。
> **v1.0.0 全平台正式版**（✅ 已发布 2026-09-04）：全平台正式版·打好地基——一次兑现历版方案 §6 开放问题与范围外声明累计 6+ 条「明示留待 v1.0.0」收口项：①协议层收口（02 §8.4 规则④契约 WARN→FAIL 强校验 + 模块头契约机读化 + desktop Runtime asset_get 跨包只读寻址，check16 入段 C、verify.sh v2.6 PASS 20→22）；②社区生态收口（CONTRIBUTING「提交→PR 评审→登记→发布」协作流程五步 + community/「校园 × 西幻轻混」完整可玩组合包战例）；③双端发布质量收口（端到端测试入 CI 缺口⑩闭环：桌面 headless 断言 + Android 模拟器启动冒烟最小集 + 正式发布仪式三件套终态收口 + tag v1.0.0）；方案真相源见 13_v1.0.0_全平台正式版方案.md；版本演进与任务记录见 ROADMAP 与 CHANGELOG。
> **v0.9.0 Android 同步门禁 + APK 闪退修复**（✅ 已发布 2026-09-04）：闪退修复代码（MDRadioButton→MDCheckbox / MDTopAppBar 去 subtitle / CJK 字体注册）已含于 v0.8.0 历史（git merge-base 实证），本版对其做验证归档 + 回归断言入冒烟（selftest_android.py UI 启动安全静态断言三断言），并把 Android↔真源同步差异校验接入 CI（build-android.yml sync 步骤后追加 sync_android.sh --check 自证闸门，缺口⑦闭环）；方案真相源见 12_v0.9.0_Android同步门禁与APK闪退修复方案.md；版本演进与任务记录见 ROADMAP 与 CHANGELOG。
> **v0.8.0 自定义模块组合**（✅ 已发布 2026-09-04）：在 v0.7 开放协议注册之上对外开放模块组合——第三方题材模块可在 P00 骨架上自由组合装配为新的社区管线（references 受控跨包引用：01 §6.1 Schema v1→v2 → 02 §8.4 组合登记 + registry.json protocols[] references 投影 → verify.sh check15 组合门禁 v2.5）；方案真相源见 11_v0.8.0_自定义模块组合方案.md；版本演进与任务记录见 ROADMAP 与 CHANGELOG。
> **v0.7.0 自定义协议**（✅ 已发布 2026-09-04）：在 v0.6 统一入口之上对外开放协议注册——第三方按 protocol.yaml 协议声明注册自定义协议（01 §6.1 Schema 规范 → 02 §8.3 登记三要件 + registry.json protocols[] 投影 → verify.sh check14 注册门禁 v2.4，全量 PASS=19 全绿）；校园/西幻两包 retro-fit 为首例战例；版本演进与任务记录见 ROADMAP 与 CHANGELOG。

## 开箱即玩：社区领域预设
两套开箱预设以社区领域包随仓库分发（07 §3 索引）：
- **校园情感流（P02）**：装载手册 `community/校园情感领域包/README.md`（9 题材模块 + 29 资产，关系驱动）
- **西幻生存流（P03）**：装载手册 `community/西幻生存领域包/README.md`（14 题材模块 + 23 内容资产，生存驱动）
两包结构统一：README（速览/装载/资产/规则/验收）+ modules + assets + pipelines；制作规范见 `community/README.md` 与 `community/模板制作指令包.md`。

## 扩展新领域（三步）

① 在 community/ 下建领域包，包内 modules/ 按协议增题材模块 → ② 包内 assets/ 增资产模板并登记溯源索引（assets/README.md）→ ③ 复制 P00 派生新管线放包内 pipelines/，并在 02 §8 社区登记表登记，verify.sh 自动纳入 I5 调度。

## 核心逻辑层（desktop/src/core/）

基础层真身：纯 Python 零第三方依赖的装配/IR/质检/导出/检索逻辑，被端壳（桌面 GUI / android）复用。L0-L2 验证入口：

- 分层门禁：`bash verify.sh`（v2.9，check1-18 全绿 PASS=24，clone 即绿）
- 单元测试：`cd desktop && python -m unittest discover -s tests`
- 端到端：`python scripts/e2e_desktop_headless.py`（直驱 core，无需 GUI/端壳）

> 端壳层（桌面 GUI `desktop/src/ui` + android app）已冻结移出演进主线，详见 `L3_FROZEN.md`——接回时从 git 历史恢复 + 重建 sync 镜像。