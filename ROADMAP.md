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

## 8. 治理指针（四项约定）

1. **README 版本行指针**：README 版本行（L33 锚点「vX.Y.Z（当前主线）」）随发布更新。
2. **协议链随方案文档追加**：README L32 协议链每新增方案文档（08→09→…）追加一行。
3. **CHANGELOG 发布归档**：每次发布把 [Unreleased] 归档为 [版本号] + 日期段，并同步打 annotated tag。
4. **门禁全绿铁律**：verify.sh（含 check12 代码层 unittest）0 WARN 0 FAIL 方可提交；任一 FAIL = 协议事故，回滚再改。
