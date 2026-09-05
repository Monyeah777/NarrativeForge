# Narrative Forge · 文档生成工坊（规范驱动）

**Narrative Forge 是一台规范驱动的结构化文档生成器（元工具/文档工厂）**。它按协议校验结构，与文体无关：小说、技术文档、设定集都适用。叙事世界（P01/P02/P03）目前应用最成熟。

**生成路径**：自然语言意图 → 按协议模板填充（模块/管线/资产三正交装配）→ `bash verify.sh` 结构校验（十三项门禁，check1-13）→ 输出结构化文档/可运行世界。

**三个正交维度（均可增删改）**：
- 模块（04_模块库）：领域能力原语，按 01 §2 声明接口后登记即被调度。
- 管线（03_管线库）：数据流转骨架，含领域无关的 P00 通用骨架（装载→语境推进→实体状态→内容生产→决策→装配→一致性→素材→输出）；P01/P02/P03 是 P00 在叙事领域的实例装配。新领域复制 P00 派生新管线即可，引擎不改一行。
- 资产（随领域包分发）：数据模板/素材，按键挂载供模块裁剪注入。领域资产位于 community/<领域包>/assets/（随包附带溯源索引）；05_资产库仅留用户自定义扩增槽与总索引（见 05_资产库/README.md）。

## 下载桌面工具

桌面工具（社区版，Windows exe / macOS / Linux）在 **Releases** 发布成品，由 GitHub Actions 自动构建（`.github/workflows/build-desktop.yml`）。社区用户无需安装 Python、无需运行任何构建脚本：

1. 打开仓库 Releases 页，下载对应平台产物（`NarrativeForge.exe` / Mach-O / ELF）。
2. 双击运行。首次启动自动创建数据目录 `~/.NarrativeForge/`。
3. 源码运行兜底：`cd desktop && pip install PySide6 && python main.py`。

## 社区版模板闭环（自制模板 → 组装 → 输出 MD）

社区版的核心用法：从本仓库 GitHub 界面下载规范，用**任意非 API 免费客户端 AI**（豆包、DeepSeek、Kimi、文心一言、ChatGPT 免费版、本地模型等）制作自己的模板，再导入桌面工具勾选组装，输出 MD 交给叙事前端：

1. **下载规范**：阅读/复制 `community/模板制作指令包.md`（模块/管线/资产包三格式 + M91–M99 社区预留号段）。
2. **AI 做模板**：把指令粘贴给任意客户端 AI，描述你的需求（例：「做一个校园悬疑系统」），AI 输出模板正文。
3. **导入组装**：将 AI 输出的正文另存为 .md，拖入桌面工具 → 自动解析校验 → 勾选模块 → 选管线与资产包 → 生成 MD。
4. **开始叙事**：把生成的 MD 交给叙事前端（SillyTavern 等）使用，或继续导入更多模块扩展世界。

图文流程与 FAQ 见 `community/README.md`。

## 协议链
01_核心协议 → 02_联动注册表 → 03_管线库 → 04_模块库 → 05_资产库 → 06_Agent执行协议 → 07_官方核心出厂与社区预设导航 → 08_v0.5.0_优化版方案 → 09_v0.6.0_协议中转站方案 → 10_v0.7.0_自定义协议方案 → 11_v0.8.0_自定义模块组合方案 → 12_v0.9.0_Android同步门禁与APK闪退修复方案 → 13_v1.0.0_全平台正式版方案 → 14_v1.2.0_协议中转站v2方案 → 15_v1.3.0_Agentic检索方案 → 16_v1.4.0_质量治理闭环方案 → 17_v2.0.0_导出层CCV3方案 → 18_v2.0x_SKILL出口插件方案。
> **2.0 导出层序列（v1.2.0–v2.0.x，🔵 当前主线·开发中，已并入 v1 main=dd2003f）**：从「叙事工具」到「所有 AI 协议标准的上游生成器」——v1.2 协议中转站 v2（IR 内容归一化）/ v1.3 Agentic 检索（四类统一 search）/ v1.4 质量治理闭环（quality_gate + check17）/ v2.0.0 CCV3 导出（映射层+exporter+PNG+check18+GUI 导出）/ v2.0.x SKILL 出口插件（产物×适配矩阵：techdoc→SKILL、narrative→CCV3）。verify v2.8 PASS=24。方案真相源见 14–18。
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

## 桌面工具（desktop/）

这套协议的 GUI 实现：拖入 .md 模块 → 校验 → 勾选装配 → 输出文档。

- 自动化构建：`.github/workflows/build-desktop.yml`（三平台并行；推送 `v*` tag 自动发布 Release）
- 打包说明：`desktop/packaging/README.md`
- 源码运行与单测：`desktop/README.md`