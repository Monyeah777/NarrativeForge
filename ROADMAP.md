# NarrativeForge 路线图（ROADMAP）

> **定位**：v0.5.0 → v1.0.0 五版本路线的**唯一规划真相源**（I5）。本文件只回答「往哪走、边界在哪、交付锚点是什么」；每版本的**任务级分解与验收**见对应方案文档（08_/09_…）。
> **治理指针**：发布、版本行、方案文档追加、门禁四项约定见 §8——任何版本演进不得绕过。

## 1. 版本总览

| 版本 | 代号 | 状态 | 一句话目标 | 方案真相源 |
| --- | --- | --- | --- | --- |
| v0.5.0 | 优化版 | ✅ 已发布（2026-09-04） | 吸收外部项目精华、夯实底层能力（T1–T6） | 08_v0.5.0_优化版方案.md |
| v0.6.0 | 协议中转站 | ✅ 已发布（2026-09-04） | 协议体系从人读规范文档升级为机读可驱动的通用协议层 | 09_v0.6.0_协议中转站方案.md |
| v0.7.0 | 自定义协议 | ✅ 已发布（2026-09-04） | 对外开放协议注册，第三方可注册自定义协议 | 10_v0.7.0_自定义协议方案.md |
| v0.8.0 | 自定义模块组合 | ✅ 已发布（2026-09-04） | 对外开放模块组合，第三方题材模块可组合装配 | 11_v0.8.0_自定义模块组合方案.md |
| v0.9.0 | Android 同步门禁 | ✅ 已发布（2026-09-04） | APK 闪退修复 + Android↔真源同步差异入 CI | 12_v0.9.0_Android同步门禁与APK闪退修复方案.md |
| v1.0.0 | 全平台正式版 | ✅ 已发布（2026-09-04） | desktop / android / 协议层 / 社区生态收口，正式发布 | 13_v1.0.0_全平台正式版方案.md |
| v1.1.0 | 通用核心基础包 | ✅ 已发布（2026-09-04） | T4-1：community 第 4 包（P05 核心基础流）战例落盘 + check14/15 扩容 3→4 | —（承接 13 方案延续，无独立方案文档） |
| v1.2.0 | 协议中转站 v2 | ✅ 已实现（2.0 E0-①） | IR 内容归一化层（2.0 E0-①） | 14_v1.2.0_协议中转站v2方案.md |
| v1.3.0 | Agentic 检索 | ✅ 已实现（2.0 E0-②） | 四类对象统一检索（2.0 E0-②） | 15_v1.3.0_Agentic检索方案.md |
| v1.4.0 | 质量治理闭环 | ✅ 已实现（2.0 E0-③） | 质检门+check17（2.0 E0-③） | 16_v1.4.0_质量治理闭环方案.md |
| v2.0.0 | 导出层 CCV3 | ✅ 已发布（2026-09-05，tag v2.0.0） | CCV3 首发+插件架构（2.0 E1） | 17_v2.0.0_导出层CCV3方案.md |
| v2.0.x | 2.0 E1-E5 收口 | ✅ 已实现（2026-09-05） | CCV3/SKILL 出口 + 协议向导 + 组合运行时 + 模块市场雏形 + 仓库盘点 | 17-22 方案文档 |
| v2.1.0 | 基础层深化 A/B/C 首波 | ✅ 已发布（2026-09-05，tag v2.1.0） | A1/A2 适配器 + B1-B4（管道化/质量门/协议自举/登记助手/market）+ C-b techdoc 域包战例 + 23 分层治理 | 23-32 方案文档 |
| v2.2.0 | 外部吸收首波 | ✅ 已发布（2026-09-05，tag v2.2.0） | verify 验证纵深 A1-A5（export_schema/引用反查/文档完整性/registry 闭合/MCP 规范核查）+ B1/B2 方案模板纪律 | 33 方案文档 + 33_v2.2.0_A5-MCP规范差距核查报告.md |
| v2.3.0 | 基础层深化首波 | ✅ 已发布（2026-09-05，tag v2.3.0） | A3 规则出口打通（doc_semantics 透传）+ B2 变体装配（variants）+ B3 文档 retro-fit（M93/M96） | 34 方案文档（§7.5 展开） |
| v2.4.0 | 外部吸收大包 | ✅ 已发布（2026-09-06，tag v2.4.0） | 规范核查三连（SKILL/CCV3/AGENTS）+ 实现四件（A4 check22 体检 / A5 nf rename / A6 质量分级 / A7 上架元数据） | 35 方案文档（§7.5 展开） |
| v2.5.0 | 基础层深化续 | ✅ 已发布（2026-09-06，tag v2.5.0） | 读入入册（skill 资源随行装载 + import --register）+ 协议层 V2（版本槽位 + 条件组合）+ 市场本体化收口（market list --tier + spec ls）+ 协议多出口渲染（rules_render）+ MCP 运行时化（mcp_runtime stdio，G1/G2/G4 勾销 + C2 安全层） | 36 方案文档（CCV3 修复）+ 37 方案提交线（§7.5 展开） |
| v2.6.0 | 端壳接线波第 1 波 | ✅ 已发布（2026-09-06，tag v2.6.0） | L3 冻结快照恢复（51f7130）+ W1-W9 接线（读入/doc_semantics/一键全链/变体/rules 多出口/五格式导出/质量门面板/市场目录/MCP serve）+ Release 产线修复（G1 ci-verify + G2 build-desktop/build-android 干跑 + emulator 启动冒烟） | 38 方案合并稿（§7.5 勾销 + L3_FROZEN.md） |
| v2.3+ | 基础层深化续 | 🔮 规划（方向见 §7.5，条件池 §7.6） | C/D 条件池（端壳生态 / AI 内容生成，触发条件冻结） | —（§7.5/§7.6 展开） |

> **「协议开放三部曲」内在脉络**：**v0.6 统一入口 → v0.7 开放自定义协议 → v0.8 开放模块组合**。v0.6 若未建立统一入口，v0.7/v0.8 的开放将无从谈起——统一入口是协议开放的地基。

## 2. v0.5.0 优化版（✅ 已发布）

- 一句话：吸收外部项目精华（NovelClaw 等七点机制调研）、夯实底层能力，任务 T1–T6 全量交付：T1 编号治理收口 / T2 社区包装配 / T3 记忆分层 / T4 M80 门禁流水线 / T5 资产工作台化 / T6 社区发布规范收口。
- 交付物：verify.sh v2.1 两段式门禁（check1–11）、P02 校园情感流 / P03 西幻生存流两套社区预设、Android 首次 APK Release、协议文档体系 01–07 + 08 方案。
- 明细见 08_v0.5.0_优化版方案.md。

## 3. v0.6.0 协议中转站（✅ 已发布 2026-09-04）

### 一句话目标
协议体系从「人读规范文档」升级为「机读可驱动的通用协议层」——建立**协议统一入口（协议中转站）**，让 desktop/android 双端代码不再各自以文件系统约定消费 03/04/05，而是经注册表机读 Schema 统一驱动。

### 范围边界

✅ **四做**：
1. **协议统一入口**：注册表机读 Schema + Runtime 装载器（缺口⑧——v0.6.0 核心命题）。
2. **迁移机制落地**：01 §7 版本兼容 V1–V3 规则落地为迁移模板 / 示例文档 / 校验（缺口⑥，V2 bump 首次实战）。
3. **sync --check 模式**：sync_android.sh 增加 `--check` 差异校验模式（缺口⑦；仅做模式本体，接入 CI 归 v0.9.0）。
4. **v0.5.0 治理缺口补漏**：ROADMAP / CHANGELOG / CONTRIBUTING / .github 模板 / verify.sh 增 check12（本文件所在批次）。

❌ **四不做**：
1. 对外开放协议注册（= v0.7.0）。
2. 第三方模块组合装配（= v0.8.0）。
3. Android 功能扩展（= v0.9.0，桌面单屏远弱 7 区不在本版）。
4. 端到端测试入 CI（范围外，桌面端到端断言缺口⑩留待另行立项）。

### 交付锚点
- 09_v0.6.0_协议中转站方案.md（A→B→T 三层落盘，08 格式）。
- verify.sh check12（代码层门禁：unittest 40 用例 + py_compile 语法抽查）。
- 协议统一入口代码（desktop core 侧 Runtime 装载器 + 注册表机读 Schema）。
- 迁移机制文档 / 模板 / 校验（01 §7 V1–V3 落地）。
- sync_android.sh `--check`。

### 版本内提交约定
按 08 惯例：每批次独立 commit；verify.sh（含 check12）全绿方可推送。

## 4. v0.7.0 自定义协议（✅ 已发布 2026-09-04）

### 一句话目标
在 v0.6 统一入口之上**对外开放协议注册**——第三方可按协议声明（protocol.yaml）注册自定义协议，进入注册表登记与门禁调度。

### 范围边界

✅ **三做**（任务分解见 10_v0.7.0_自定义协议方案.md，A→B→T 三层）：
1. **协议声明 Schema 机读化（B1/T1）**：01 §6 新增第三方协议声明 protocol.yaml Schema 规范（必填字段 + R1/R2/R3 映射 + M91-M99 编号规则 + 模板），社区包根目录必带 protocol.yaml。
2. **注册流程机读化 + 投影扩展（B2/T2）**：02 §8.3 升级「登记 = protocol.yaml 在场 + 本表在册 + registry.json protocols[] 投影」三要件；校园/西幻两包 retro-fit 落 protocol.yaml 作首例战例；registry.json 增 protocols[]（schema_version 保持 "2"，V1 只增不删）。
3. **注册门禁 check14（B3/T3，v2.4）**：verify.sh 新增 check14 第三方协议注册机读门禁（入段 C）——Schema 合法 / R1-R3 合规 / 编号段唯一 / protocol.yaml ↔ README ↔ 02 §8 ↔ registry.json protocols[] 四方一致。

❌ **三不做**：
1. 第三方模块组合装配（= v0.8.0，registry_loader 不消费 protocols[] 做装配驱动）。
2. Android 功能扩展与 APK 闪退修复（= v0.9.0）。
3. 端到端测试入 CI（范围外）。

### 交付锚点
- 10_v0.7.0_自定义协议方案.md（A→B→T 三层落盘，09 格式）。
- verify.sh v2.4（check1–14 全绿）+ 两包 protocol.yaml + registry.json protocols[] 投影。

### 版本内提交约定
按 09 惯例：每批次独立 commit（C0–C4）；verify.sh（含 check14）全绿方可推送。

## 5. v0.8.0 自定义模块组合（✅ 已发布 2026-09-04）
### 一句话目标
在 v0.7 开放协议注册之上**对外开放模块组合**——第三方题材模块可在 P00 骨架上自由组合装配为新的社区管线（方案甲：references 受控跨包引用）。
### 范围边界
✅ **三做**（任务分解见 11_v0.8.0_自定义模块组合方案.md，A→B→T 三层）：
1. **组合引用 Schema 机读化（B1/T1）**：01 §6.1 protocol.yaml Schema v1→v2——新增 `package.references` 跨包模块白名单引用（source_package/module_id/source_schema_version/asset_readonly）；R1 演进为「禁互引 + references 受控引用（依赖闭包闭合官方核心）」，cross_package 保留恒空 deprecated；01 §7 迁移记录 v1→v2 四步入档。
2. **组合登记机制 + 投影扩展（B2/T2）**：02 §8.4 组合管线登记（四规则：引用在册可寻址/依赖闭包闭合官方核心/同层 default 槽位唯一/契约 WARN 提示）+ 文档级组合声明示例；校园/西幻两包 protocol.yaml retro-fit schema_version→"2"（references: [] 向后兼容演示）；registry.json protocols[] 补 references（registry_schema_version 保持 "2"，V1 只增不删）。
3. **组合门禁 check15（B3/T3，v2.5）**：verify.sh 新增 check15 组合门禁（入段 C）——引用在册可寻址 / 依赖闭包闭合官方核心 / 挂载层 default 冲突 / schema_version v2 兼容 / protocol.yaml ↔ registry protocols[] references 一致。
❌ **三不做**：
1. Runtime 组合调度引擎改造（registry_loader 保持只读官方核心投影，引擎级消费归后续版本）。
2. 跨包资产内容复制与完整题材级可玩组合包战例（资产只读通道运行时实现 + 战例深度留 v0.8.1，见 11 方案 §6 开放问题 1/3）。
3. Android 功能扩展与 APK 闪退修复（= v0.9.0）；端到端测试入 CI（范围外）。
### 交付锚点
- 11_v0.8.0_自定义模块组合方案.md（A→B→T 三层落盘，10 格式）。
- verify.sh v2.5（check1–15 全绿）+ 两包 protocol.yaml schema_version "2" + registry.json protocols[] references 投影。
### 版本内提交约定
按 09/10 惯例：每批次独立 commit（C0–C4）；verify.sh（含 check15）全绿方可推送。

## 6. v0.9.0 Android 同步门禁 + APK 闪退修复（✅ 已发布 2026-09-04）
### 一句话目标
把 sync --check 差异校验接入 CI（缺口⑦闭环：Android↔真源一致性不再靠人工）；对 APK 闪退修复（代码已含 v0.8.0 历史，git merge-base 实证）做验证归档 + 纳入 CI 回归门禁保障。
### 范围边界
✅ **三做**（任务分解见 12_v0.9.0_Android同步门禁与APK闪退修复方案.md，A→B→T 三层）：
1. **闪退修复验证归档 + 回归断言入冒烟（B1/T1）**：git merge-base 实证三处修复代码（`6b9445e` MDRadioButton→MDCheckbox + MDTopAppBar 去 subtitle / `e92f119` CJK 字体注册）均已含于 v0.8.0 tag——本版定位为「验证修复已含历史版本 + 归档根因链」，非新写修复代码；selftest_android.py 增 UI 启动安全静态断言三断言（screens.py 无 MDRadioButton import / main.py MDTopAppBar 无 subtitle kwarg / `_register_cjk_fonts` 定义在场且 build() 首行调用），纯 python3 文件读取无 Kivy 依赖，FAIL 任一 = 冒烟 exit 1。
2. **CI 同步门禁 --check 自证（B2/T2）**：build-android.yml 同步步骤（`bash scripts/sync_android.sh`，core/seed 为 .gitignore 生成物不入库故 CI 中 sync 是其唯一生成途径）后**追加**一步 `bash scripts/sync_android.sh --check` 自证闸门——先保留生成步骤再自证（直接替换会命中 fresh checkout 生成物缺失边界必然失败）；有差异 exit 1 fail CI、无差异继续冒烟。缺口⑦（Android↔真源一致性不再靠人工）闭环。
3. **三件套版本收口（B3/T3）**：CHANGELOG [Unreleased] v0.8.0 段归档 [0.8.0]（治理指针 3 发布归档收口）+ 新建 [Unreleased] v0.9.0 段；ROADMAP §1 L14/§5 状态归位；README 协议链追加 12 + v0.8.0 块引用切 ✅ + 新增 v0.9.0 🔵 块引用——v0.9.0 版本语义（「修复闪退」）与代码事实（修复已含 v0.8.0）厘清落档。
❌ **三不做**：
1. Android 功能扩展（UI/功能迭代明确不在本版，同历版三不做）。
2. 端到端测试入 CI（真机/模拟器启动 UI 自动化留范围外，延续 v0.5.0–v0.8.0 四版范围外声明；APK 装机启动验证仍靠真机手动验收）。
3. 协议层与 verify.sh 门禁改动（本版无协议层 Schema/门禁改动，check1–15 PASS=20 不变；sync_android.sh --check 本体与 buildozer/p4a 构建链三补丁均不动）。
### 交付锚点
- 12_v0.9.0_Android同步门禁与APK闪退修复方案.md（A→B→T 三层落盘，11 格式）。
- selftest_android.py UI 启动安全静态断言三断言（纯 python3 无 Kivy 依赖，闪退修复点回归有 CI 闸门）。
- build-android.yml sync --check 自证闸门步骤（缺口⑦闭环）。
- 三件套收口（CHANGELOG [0.8.0] 归档 + [Unreleased] v0.9.0 段 / README 协议链 12 + 块引用双切 / ROADMAP §1 L14 🔵 + §6 展开）+ tag v0.9.0。
### 版本内提交约定
按 10/11 惯例：每批次独立 commit（C0–C3）；verify.sh（含 check12，全量 PASS=20）全绿方可推送。

## 7. v1.0.0 全平台正式版（✅ 已发布 2026-09-04）
### 一句话目标
v1.0.0「全平台正式版·打好地基」——一次兑现历版方案 §6 开放问题与 ROADMAP 范围外声明累计 6+ 条「明示留待 v1.0.0」收口项：**协议层收口 + 社区生态收口 + 双端发布质量收口**，全平台正式发布（tag v1.0.0）；功能扩展一律外推 v1.1+。
### 范围边界
✅ **三做**（任务分解见 13_v1.0.0_全平台正式版方案.md，A→B→T 三层）：
1. **协议层收口（B1/T1）**：02 §8.4 规则④契约仲裁 WARN→FAIL 强校验升级 + 模块头契约机读化 + desktop Runtime asset_get 跨包只读寻址（asset_readonly 运行时实现，I5 单一真相源闭环）——**本项打破 verify.sh PASS=20 基线**：check16 契约校验门禁随 T1-3 入段 C，verify.sh v2.6，PASS 20→22；C0–C2 中间态 PASS=20 保持，C4 起 PASS=22 终态全绿方收口。
2. **社区生态收口（B2/T2）**：CONTRIBUTING「提交→PR 评审→登记→发布」协作流程五步 + community/「校园 × 西幻轻混」完整可玩组合包战例——社区生态从「可注册可组合」收口到「有协作流程、有真实战例」。
3. **双端发布质量收口（B3/T3）**：端到端测试入 CI（缺口⑩闭环：桌面 headless 断言 + Android 模拟器启动冒烟最小集）+ 正式发布仪式三件套终态 + tag v1.0.0（真机手动验收保留为发布前最终门禁）。
❌ **三不做**：
1. Android 功能扩展 / 桌面 UI 迭代（外推 v1.1+）。
2. 引擎级组合调度引擎改造（registry_loader 只做只读寻址，不消费 references 做装配驱动）。
3. 跨包资产内容复制/移动（I5 单一真相源；资产跨包只读寻址已由 T1-3 提供运行时通道）。
### 交付锚点
- 13_v1.0.0_全平台正式版方案.md（A→B→T 三层落盘，12 格式）。
- verify.sh v2.6（check1–16 全绿 PASS=22）+ 02 §8.4 契约 WARN→FAIL 强校验 + 模块头契约机读化 + desktop Runtime asset_get 跨包只读寻址。
- CONTRIBUTING 协作流程五步 + community/「校园 × 西幻轻混」完整可玩组合包战例。
- 端到端测试入 CI（桌面 headless 断言 + Android 模拟器启动冒烟最小集）。
- 三件套终态 + tag v1.0.0（正式发布仪式收口，随后 v1.1.0 立项）。
### 版本内提交约定
按 11/12 惯例：每批次独立 commit（C0–C8）；verify.sh 门禁全绿方可提交（C0 仅动文档 PASS=20 保持；C1–C3 中间态 PASS=20 保持；C4 起 PASS=22 终态）；C8 push 前依 13 方案 §6 开放问题 6 向用户索取一次性新 PAT（不写入 config）。

## 7.5 基础层深化方向（v2.1.0 已发布 ✅；v2.2+ 展开见 §7.6）

### 一句话目标
基础层 = 让「协议标准族 × 生成器能力 × 内容库」三条线在 **L0–L2 内自洽闭环、全链路管道化**（retrieve → compose → gate → export 一条命令走通）；中下游端（CLI / 可嵌入库 / GUI / APK）冻结为薄壳，等基础层收敛后 CLI/库先行、GUI/APK 按需一次性包络。**端壳不再逐功能跟进**（L3_FROZEN.md 冻结契约）；下游生态（SillyTavern / agent 框架）随适配面自然扩张——「上游生成器」的价值在下游消费端兑现。

### 范围边界（四线，随收敛逐项立项——每项落独立方案文档再实现）

✅ **A 适配矩阵补全**（产物×适配矩阵：现两格填实 techdoc→SKILL / 装配→CCV3）：
1. **techdoc → AGENTS.md / CLAUDE.md**（A1，既定下一步——ROADMAP v2.0.x 行旧文已预告）。
2. **techdoc/协议定义 → MCP server 定义**（A2，JSON 协议导出）。
3. **协议向导产物 → 各 agent 框架 rules 多目标渲染**（A3——E2 产物本应多出口，现单出口）。✅ **A3 规则出口打通已落地（方案 34）**：doc_semantics 三层透传（render_ir/pipe/nf run `--doc-semantics {project_rules,skill}`）——techdoc 规则装配可显式声明 project_rules → AGENTS.md/CLAUDE.md 出口（此前 render_ir 不写 IR.meta['doc_semantics'] → classify 回退 skill 拒出，断链已修复）。P90 战例端到端产 AGENTS.md。✅ **GUI 向导声明 UI 已接线（38 方案 W2，v2.6.0）**：protocol_wizard 加 doc_semantics 三选一（commit 8b9a4a1）。✅ **A3 协议多出口渲染已落地（方案 37 Wave4，v2.5.0）**：新增 `desktop/src/core/rules_render.py`（protocol.yaml → agents/claude/skill 三格，`_RULES_RENDERERS` 注册表仿 exporter._REGISTRY + 范围纪律）+ `nf render <pkg_dir> --fmt`——协议定义本身（E2 产物/社区包声明）现可直接多出口渲染，适配矩阵补格完成。
4. **双向适配补全**（A4：「外部→NF」读入 SKILL/CCV3 反哺内部表示——「上游生成器」完整语义的另一半）。✅ **已实现（方案 34，v2.3.0）**：新增 `desktop/src/core/import_adapter.py`——parse_skill 双层（结构层 NF 导出逐字节还原 + 宽容层外部 SKILL.md 降级解析）+ parse_ccv3 结构还原（chara_card_v3/world.json → IR，同源去重）；exporter 补 `_REGISTRY_IN` 反向符号（格式→解析函数，只挂已交付 skill/ccv3 两格——范围纪律：agents/claude/mcp 未交付读入适配器不登记）。原三重阻碍（读入零基础 / 无样例不可测试 / 外部 spec 真实性未验证）随解锁样例双保险在场（自举三件套 + Anthropic 官方次样例 2 份）与单测 21 用例全绿解除；verify PASS 维持 29（不开新 check，check12 discover 自动收编）。遗留（非 A4 范围，见 34 方案）：CCV3 persona 语义还原 / GUI 接线（F2）。✅ **关 2（方案 37 Wave1，v2.5.0）**：skill 资源随行装载（parse_skill 宽容层 `bundled_resources` 扫描 → IR meta）+ 读入→内容库自动登记（`nf import --register` 幂等装载，同源去重）——34 遗留 4 项关 2 留 2。✅ **GUI 读入接线已落地（38 方案 W1，v2.6.0）**：zone_a 外部产物读入入口（SKILL.md/chara.json → IR 预览 → 登记，commit a95ba7e/368e7ba）——34 遗留 GUI 接线（F2）关 1 留 1（CCV3 persona 语义还原，纯 L2 域独立挂账）。

✅ **B 生成器能力纵向深化**：
1. **质检可解释化**（B1）：quality_gate 三态门 → 可解释报告 + 自动修复建议（warn 现无 actionable 输出）。
2. **组合运行时升级 + 全链管道化**（B2）：composer 静态闭包合并 → 变体/条件组合 + 冲突仲裁报告；**retrieve→compose→gate→export 串成单命令**（E4/E5 已备检索/装载，只差串链——CLI/库先行形态的地基）。✅ **B2 变体装配已落地（方案 34）**：新增 `desktop/src/core/variants.py`（apply_variant base+add−remove 幂等 + variant_assemblies 全变体展开 + 跨变体重叠仲裁报告，声明级不阻断）+ nf run `--variant-add/--variant-remove`（P04 冒烟 `--variant-remove` 导出 PASSED）。裁决：不扩展 references schema（composer freeze），变体 = 装配层模板选择。✅ **条件组合已落地（方案 37 Wave2，v2.5.0）**：`composer.build_assembly` 增 `conditions` 参数——module 声明 variant/condition → 组合时按条件动态裁剪（RED→GREEN 反证）。B2 变体 + 条件组合 + 冲突仲裁三段齐。
3. **协议向导自举闭环**（B3）：向导生成 → check14 门禁 → 注册一站式（生成物直接可登记）。✅ **C+A 已落地（方案 29）**：C=check14 ⑦ 元素级全序（module_ids/mount_layers 逐条比对，同长度漂移可抓）+ 包目录 glob 化（新增组合/通用包零改 verify.sh）+ Windows 分隔符兼容；A=`desktop/src/core/protocol_projection.py`（protocol.yaml → registry protocols[] 条目，字段与 ⑦ 断言同构）。✅ **B 已落地（方案 30）**：`nf register` 本地登记助手（registry_sync 校验三要件 + merge 只增不删幂等 → nf.py register --check/--apply；02 §9.2 豁免子句划界——受控路径非 PR 机器人/自动流水线）。B3 三段闭环全通：向导生成 → check14 门禁 → 登记机读落地。
4. **市场协议本体化**（B4）：E5 社区盘点之上补版本 / 依赖解析 / 冲突仲裁 / 上架规则——目录视图 → 真协议。✅ **CLI/库先行已落地（方案 31）**：`desktop/src/core/market_analyzer.py`（check15 ②③ 判据提为可 import 库——`dependencies` 依赖闭包 + `conflicts` 挂载冲突）+ nf.py `market <包目录>` 查询（登记状态/依赖/冲突，门禁前移）。✅ **瑶光发现已修（31 补遗）**：verify.sh check15 ② 源包嵌套 references 死检查（原误取 dependencies 层恒空，references 实居 package 层）——verify.sh 判据已改 `pkg2.get('references')`（package 层），RED 反证：注入嵌套后检出「嵌套 references」；真 4 包 PASS=24 保持。✅ **版本槽位已落地（方案 37 Wave2，v2.5.0）**：protocol.yaml `package.version` 机读字段 + registry protocols[] version 投影 + check14 ⑦ 联动（版本声明合法性/引用钉扎复核）。✅ **上架规则 + Spec Registry 已落地（方案 37 Wave3，v2.5.0）**：市场上架规则化（消费 35-A7 分级字段）+ `nf market list --tier=official|community|experimental` 目录视图 CLI + `nf spec ls`（Spec Registry = C3 并入 B4）。✅ **GUI 目录视图已接线（38 方案 W8，v2.6.0）**：zone_g tier 分级列表（list_market 同库，commit 786d96c）——B4 遗留 GUI（zone_g）目录视图关。

✅ **C 内容库资产化**：题材/行业域包广度扩展（techdoc 域 = 新领域三步自然延伸）+ 模块质量分级（官方核心/社区/实验）+ 版本化；**内容由 A/B 工具链自动生成/校验**（内容=产物，非手工艺品），不逐包手写。🔵 **techdoc 域包战例已落地（方案 32）**：community 第 5 包「技术文档域包」——第一个非叙事题材域包（自带 M97 术语管理/M98 修订记录落 M91-99 社区段 + core_modules 引官方含 M90 + P06 派生管线），02 §8 登记 + registry protocols[] 第 5 条（nf register 工具链实战走通），verify ③ R2 扩域 ALL_PKGS 全两两。遗留：模块质量分级（C-a 无消费方待用途）+ 版本化（B4 协议层 V2 遗留）。✅ **C-a 消费方已落地（方案 37 Wave3，v2.5.0）**：`nf market list --tier=official|community|experimental` 消费 35-A6 分级字段——模块质量分级从「无消费方」到目录视图 CLI 消费方闭环。✅ **GUI 视图已接线（38 方案 W8，v2.6.0）**：zone_g 分级视图同库消费（commit 786d96c）——C-a GUI 视图留 L3 关。

✅ **D 验证/治理基础设施**：verify 分层门禁（L0-L2 默认全绿，**23 方案 v2.9 立基 → 现行 v2.11 check1-22 全绿**）+ CI 收敛基础层闸门（ci-verify + e2e-desktop，**已完成 23 方案**）；本段即 ROADMAP 空位补正文。

❌ **三不做**（本阶段边界）：
1. 端壳逐功能跟进（GUI 不加按钮、Android 不加能力——L3_FROZEN.md 冻结契约；仅基础层里程碑收敛点一次性全量接线）。
2. APK/EXE 作为阶段里程碑产出（release 层维持用户决策搁置；一次性产出时 CLI → 库 → GUI/APK 顺序，薄壳包络）。
3. 内容层手工逐包编写（一律走 A/B 工具链，防内容=手工艺品的不可校验态）。

### 交付锚点
- 每条立项 → 独立方案文档（沿用 NN_vX.Y_方案.md A→B→T 格式 + 审批）+ verify 全绿 + 战例闭环。
- **B2 全链管道化 = 首个里程碑**（CLI/库先行形态的地基，retrieve→compose→gate→export 一条命令）——建议 v2.1.0 首立项。
- A1（AGENTS/CLAUDE 适配器）与 B2 并列优先：A 线最实一格 + B 线地基。

### 版本内提交约定
沿用历版：每批次独立 commit；verify.sh（v2.11 分层门禁，check1-22 全绿 PASS=31）全绿方可提交；GUI 大 feature 先落方案审批再实现。

## 7.6 v2.2.0 短期 roadmap（外部吸收首波，✅ 已发布 2026-09-05，tag v2.2.0）

> **来源**：外部两批 28 项筛选（SpecForge/OpenSpec/MCP 等方法论外部输入）——真正「现在该做」收敛为「verify 从协议一致性加深到产物与语义完整性」+「方案模板纪律」。方案 33 已批准（A 族 5 项 + B 族 2 项，四波）。

### 执行中（方案 33，四波全完成 ✅）
- ✅ **Wave1 A1 导出产物 schema 合规**（cc3106e）：export_schema 5 格式 shape 校验 + check19。
- ✅ **Wave2 A3 文档完整性门禁 + A2 引用反查**（14e47dc + c13fb95）：check20（模块必填清单缺即 fail）+ retriever.referenced_by「谁引用 Mxx」+ nf who-refers CLI。
- ✅ **Wave3 A4 变更影响面 + A5 MCP 规范核查**（d0dc61b + 181de51）：impact_check.py + check21（registry 引用图闭合）+ 一次性 MCP 规范差距报告落盘。
- ✅ **Wave4 B 族 + C/D 族 + 收口**（e68718b）：CONTRIBUTING §4.5 方案模板五问 + 消费方声明（防无消费方能力重演）；33 真相源/README/CHANGELOG 已同步。verify PASS=29 全绿。
- ✅ **v2.2.0 发布收口**：三件套归档 + tag v2.2.0（治理指针 3）。

### C/D 族条件池（本版只记录不实现）
- **C 族（端壳/生态，绑三问①终点形态 + F2 形态决策）**：~~C1 MCP Server / C2 MCP 运行时安全层 / C3 Spec Registry~~——✅ **C1+C2 已落地（方案 37 Wave5，v2.5.0，2851b74）**：`desktop/src/core/mcp_runtime.py` 快照烧成 stdio JSON-RPC 服务（33-A5 报告 G1/G2/G4 差距勾销——initialize 握手 serverInfo / resources/list 去 text / resources/read 返正文）+ C2 最小安全层随行（只读无 tools/prompts + uri 白名单）+ `nf serve` CLI。✅ **C3 Spec Registry 已落地（方案 37 Wave3，v2.5.0）**：`nf spec ls` 版本化 spec 查询（= B4 遗留并入）。冻结池余项：C4 审批变更工作流 / C5 OpenSDD 双模式 / C6 M3E Canvas / C7 Agent 检索触发模式——三问①选工具链/AI 消费路线或社区路线时立项；C4 随社区路线、C5-C7 随 F2 产品设计。
- **D 族（F3 内容资产 AI 化，条件触发冻结）**：D1 BNF/Outlines 约束生成（触发：F3 AI 写模块格式不稳） / D2 STORM 调研生成（F3 扩充题材包） / D3 多 Agent 分工（F3 批量产内容） / D4 Docling 素材解析（dogfooding 暴露素材进不来） / D5 LiteFlow 条件路由（流程级动态分支出现）。D1 优先「模板+parser 强校验」，约束解码为备选。

### 后续候选（33 后，v2.3+）
- 方案 33 全部落地（verify v2.10 PASS=29，tag v2.2.0）；下一波基础层深化方向见 §7.5（C/D 条件池触发条件见上）。
- 备忘排除（不吸收）：OpenSDD 文档先于代码 / codex-spec 意图→spec（协议栈已走更深）/ 渐进式加载（已实现）/ FSM 约束生成（映射错误）/ machine_rules YAML（负资产）。


## 8. 治理指针（六项约定）

1. **README 版本块指针**：README 协议链后随发布插入「> **vX.Y.Z …（✅ 已发布 …）**」版本块（L33 起，每版一条；最新版置顶于序列块上方），随发布更新。
2. **协议链随方案文档追加**：README L32 协议链每新增方案文档（08→09→…）追加一行。
3. **CHANGELOG 发布归档**：每次发布把 [Unreleased] 归档为 [版本号] + 日期段，并同步打 annotated tag。**接线账计数随归档标注**：归档条目须含「端壳待接线项：N 项」（N = 冻结期未接线的 L2 新增能力数，积压量单一事实源，L3_FROZEN 脉冲触发条件机读基础）。
4. **门禁全绿铁律**：verify.sh（v2.11 分层门禁，段 C check12-22 含 check12 代码层 unittest）0 WARN 0 FAIL 方可提交；任一 FAIL = 协议事故，回滚再改。基础层提交以 `bash verify.sh` 全绿为唯一标尺（clone 即绿，零前置）。
5. **分层治理（23 方案 + 38 方案脉冲升级）**：L3 端壳（android/ + desktop/src/ui 等）冻结移出主仓库演进主线，见 `L3_FROZEN.md`——端壳改动不随基础层演进；verify/CI 只锁 L0-L2。
6. **端壳接线波触发条件（38 方案 F2 裁决，陈述性规则）**：端壳默认冻结，解冻触发 = ① 未接线新能力 ≥6 项（以 CHANGELOG 归档标注的「端壳待接线项」计数为单一事实源）或 ② 用户/消费方驱动的必须项出现。触发后执行一次「批量接线 + Release 产出」（v2.6 = 第 1 波承诺交付），波后回冻结；质量分层永久保留（L3 不参与 verify，端侧靠 workflow 构建 + 冒烟断言）。接线波须有接线账清单（能力 → GUI 呈现映射）方可立项。**✅ 第 1 波已执行（v2.6.0，2026-09-06）**：W1-W9 接线 + 冒烟全绿（smoke_gui 22/22 + emulator 启动冒烟）+ Release 产线恢复，波后回冻结（见 L3_FROZEN.md 第 1 波记录）。

## 9. 未来计划（40 总纲 · 2026-09-06 用户批准）

> **真相源**：`40_未来计划总纲_三层评估短板解决方案与分波实施.md`——三层专业评估全部非 A 级短板 → 解决方案 → 分波实施路线，为 v2.7+ 基础层演进主线 + 壳集中波总索引（38 方案管壳线，40 管基础层，同一分离哲学两半）。波 0（治理修订）已完成：S6 壳分离触发 / S8 权限最小化 + sha256 / S9 执行对账模板 / S11 文档收口。

| 波 | 版本 | 内容 | 状态 |
|---|---|---|---|
| 波 0 | 治理修订（不产 tag） | S6 壳分离 / S8 安全 / S9 对账 / S11 收口 | ✅ 已完成（2026-09-06） |
| 波 A | v2.7.0（首个无壳） | S1 外部验证 / S2 nf asset 族 / S3 首批商品 / X1-3 / Y1-5 Agent 自主组装线（B2 粘贴档已免除，2026-09-07 裁决） | ✅ 已发布（2026-09-07，tag v2.7.0——与波 B 整合发布） |
| 波 B | 并入 v2.7.0（原 v2.8.0 顺延） | S4 pipeline new / S5 模块流转 / S7 近端 / S3 续 | ✅ 已发布（2026-09-07，并入 v2.7.0；S3 续挂账） |
| 波 Σ | 壳集中波（shells-v*） | 38 方案五 Stage（W1-W9 + APK 降级 + MCP POC） | ⏸️ P3 触发 |
| 波 C | v2.8.0（首个内容波） | 41 波C 质量编译深化（C1–C9 + D 组，2026-09-08 立项） | 🚧 实施中（W1-W5：C1-C7 + D2-D6 落地，check1-26 PASS=39；E3 客户端实测/D1/D7 待回填） |
| 波 D–N | 常态（P∞） | 审计 + 对账 + 回冻结 + 外部评审窗 | 脉冲式 |

> **波 A 实施进度（2026-09-07）**：W1（S2 nf asset 族 + S3 首批资产入库 + S8 密钥扫描入 CI + check23）/ W2（Y1/Y2 入口 + X2 docs/mcp.md + X3 第三方入口）/ W3（Y4 完整版样本 P03 西幻实证）/ W4（S1 docs_external-validation-v2.7.md 实证档建档 + E1 CCV3 实导材料）已提交。外部实测（E1–E3 / Y5）待真实工具环境回填——本工作台不可代跑外部客户端；回填后按实证报告执行 S13（README 宣称逐项转正）追补转正（**2026-09-07 用户拍板：先行整合发布 v2.7.0，转正待实测回填后补记**）。

> **波 B 实施进度（2026-09-07）**：S4 `nf pipeline new`（P00 派生脚手架，pipeline_scaffold.py + 单测）/ S5 模块生命周期（module_lifecycle.py + `nf module ls/status/deprecate/restore/verify`，check24 入 verify.sh v2.13 + 单测）/ S7 近端（`nf demo` 一键演示世界 + `nf --help` 作者/开发者分层引导 + README「五分钟快速开始」）已提交；verify v2.13 PASS=35 全绿。收口（2026-09-07 用户拍板）：波 A + 波 B 整合为单一 v2.7.0 发布（README 版本块 + CHANGELOG [2.7.0] 归档 + `docs_audit-40-v2.7.md` 建档 + annotated tag v2.7.0）；v2.8.0 版本号顺延给后续常态内容波；S3 续（第二个官方题材包/第三方首例）继续挂账；E1–E3/Y5 外部实测回填后追补 S13 转正。
