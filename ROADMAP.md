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
| v2.1+ | 基础层深化 | 🔮 规划（方向见 §7.5） | A 适配面 / B 生成器纵向 / C 内容资产化 / D 治理（L0-L2 管道化 + 薄壳形态） | —（本表下方 §7.5 展开） |

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

## 7.5 v2.1+ 基础层深化（🔮 规划·方向展开）

### 一句话目标
基础层 = 让「协议标准族 × 生成器能力 × 内容库」三条线在 **L0–L2 内自洽闭环、全链路管道化**（retrieve → compose → gate → export 一条命令走通）；中下游端（CLI / 可嵌入库 / GUI / APK）冻结为薄壳，等基础层收敛后 CLI/库先行、GUI/APK 按需一次性包络。**端壳不再逐功能跟进**（L3_FROZEN.md 冻结契约）；下游生态（SillyTavern / agent 框架）随适配面自然扩张——「上游生成器」的价值在下游消费端兑现。

### 范围边界（四线，随收敛逐项立项——每项落独立方案文档再实现）

✅ **A 适配矩阵补全**（产物×适配矩阵：现两格填实 techdoc→SKILL / 装配→CCV3）：
1. **techdoc → AGENTS.md / CLAUDE.md**（A1，既定下一步——ROADMAP v2.0.x 行旧文已预告）。
2. **techdoc/协议定义 → MCP server 定义**（A2，JSON 协议导出）。
3. **协议向导产物 → 各 agent 框架 rules 多目标渲染**（A3——E2 产物本应多出口，现单出口）。
4. **双向适配补全**（A4：「外部→NF」读入 SKILL/CCV3 反哺内部表示——「上游生成器」完整语义的另一半）。🔒 **待外部样例/战例，暂缓**（方案 31 后核验，启明视角三重阻碍属实）：① 读入能力零基础（desktop/src 无 parse_ccv3/parse_skill/adapter_in 反向符号，五 adapter 全 export-only）；② 无外部产物样本（全仓库无 SKILL.md/chara_card_v3 样例，唯一 JSON 为自身 registry.json——解析方向无样例输入则连 RED 测试都写不出，**不可测试性**比 A3 的「格式可能不准」更堵）；③ 外部 spec 真实性未验证（agentskills.io/SillyTavern 锚点仅 docstring 声称）+ 读入后无消费方（反哺 IR 之后无导入动作消费）。**前置 = 一份真实外部产物样例**（下游实跑产出的 .card/world.json/SKILL.md 或手供样例目录）——样例到手前 A4 评估无意义，勿重复侦察。

✅ **B 生成器能力纵向深化**：
1. **质检可解释化**（B1）：quality_gate 三态门 → 可解释报告 + 自动修复建议（warn 现无 actionable 输出）。
2. **组合运行时升级 + 全链管道化**（B2）：composer 静态闭包合并 → 变体/条件组合 + 冲突仲裁报告；**retrieve→compose→gate→export 串成单命令**（E4/E5 已备检索/装载，只差串链——CLI/库先行形态的地基）。
3. **协议向导自举闭环**（B3）：向导生成 → check14 门禁 → 注册一站式（生成物直接可登记）。✅ **C+A 已落地（方案 29）**：C=check14 ⑦ 元素级全序（module_ids/mount_layers 逐条比对，同长度漂移可抓）+ 包目录 glob 化（新增组合/通用包零改 verify.sh）+ Windows 分隔符兼容；A=`desktop/src/core/protocol_projection.py`（protocol.yaml → registry protocols[] 条目，字段与 ⑦ 断言同构）。✅ **B 已落地（方案 30）**：`nf register` 本地登记助手（registry_sync 校验三要件 + merge 只增不删幂等 → nf.py register --check/--apply；02 §9.2 豁免子句划界——受控路径非 PR 机器人/自动流水线）。B3 三段闭环全通：向导生成 → check14 门禁 → 登记机读落地。
4. **市场协议本体化**（B4）：E5 社区盘点之上补版本 / 依赖解析 / 冲突仲裁 / 上架规则——目录视图 → 真协议。✅ **CLI/库先行已落地（方案 31）**：`desktop/src/core/market_analyzer.py`（check15 ②③ 判据提为可 import 库——`dependencies` 依赖闭包 + `conflicts` 挂载冲突）+ nf.py `market <包目录>` 查询（登记状态/依赖/冲突，门禁前移）。✅ **瑶光发现已修（31 补遗）**：verify.sh check15 ② 源包嵌套 references 死检查（原误取 dependencies 层恒空，references 实居 package 层）——verify.sh 判据已改 `pkg2.get('references')`（package 层），RED 反证：注入嵌套后检出「嵌套 references」；真 4 包 PASS=24 保持。遗留：包版本槽位（协议层 V2）+ 上架规则/市场目录视图——GUI（zone_g）解冻后以 market_analyzer 为库层接壳立项。

✅ **C 内容库资产化**：题材/行业域包广度扩展（techdoc 域 = 新领域三步自然延伸）+ 模块质量分级（官方核心/社区/实验）+ 版本化；**内容由 A/B 工具链自动生成/校验**（内容=产物，非手工艺品），不逐包手写。🔵 **techdoc 域包战例已落地（方案 32）**：community 第 5 包「技术文档域包」——第一个非叙事题材域包（自带 M97 术语管理/M98 修订记录落 M91-99 社区段 + core_modules 引官方含 M90 + P06 派生管线），02 §8 登记 + registry protocols[] 第 5 条（nf register 工具链实战走通），verify ③ R2 扩域 ALL_PKGS 全两两。遗留：模块质量分级（C-a 无消费方待用途）+ 版本化（B4 协议层 V2 遗留）。

✅ **D 验证/治理基础设施**：verify 分层门禁（L0-L2 默认全绿，**已完成 23 方案 v2.9**）+ CI 收敛基础层闸门（ci-verify + e2e-desktop，**已完成 23 方案**）；本段即 ROADMAP 空位补正文。

❌ **三不做**（本阶段边界）：
1. 端壳逐功能跟进（GUI 不加按钮、Android 不加能力——L3_FROZEN.md 冻结契约；仅基础层里程碑收敛点一次性全量接线）。
2. APK/EXE 作为阶段里程碑产出（release 层维持用户决策搁置；一次性产出时 CLI → 库 → GUI/APK 顺序，薄壳包络）。
3. 内容层手工逐包编写（一律走 A/B 工具链，防内容=手工艺品的不可校验态）。

### 交付锚点
- 每条立项 → 独立方案文档（沿用 NN_vX.Y_方案.md A→B→T 格式 + 审批）+ verify 全绿 + 战例闭环。
- **B2 全链管道化 = 首个里程碑**（CLI/库先行形态的地基，retrieve→compose→gate→export 一条命令）——建议 v2.1.0 首立项。
- A1（AGENTS/CLAUDE 适配器）与 B2 并列优先：A 线最实一格 + B 线地基。

### 版本内提交约定
沿用历版：每批次独立 commit；verify.sh（v2.9 分层门禁，PASS=24）全绿方可提交；GUI 大 feature 先落方案审批再实现。

## 8. 治理指针（五项约定）

1. **README 版本行指针**：README 版本行（L33 锚点「vX.Y.Z（当前主线）」）随发布更新。
2. **协议链随方案文档追加**：README L32 协议链每新增方案文档（08→09→…）追加一行。
3. **CHANGELOG 发布归档**：每次发布把 [Unreleased] 归档为 [版本号] + 日期段，并同步打 annotated tag。
4. **门禁全绿铁律**：verify.sh（v2.9 分层门禁，含 check12 代码层 unittest）0 WARN 0 FAIL 方可提交；任一 FAIL = 协议事故，回滚再改。基础层提交以 `bash verify.sh` 全绿为唯一标尺（clone 即绿，零前置）。
5. **分层治理（23 方案）**：L3 端壳（android/ + desktop/src/ui 等）冻结移出主仓库演进主线，见 `L3_FROZEN.md`——端壳改动不随基础层演进；verify/CI 只锁 L0-L2；未来一次性产出从 git 历史恢复 + 触发 v* tag workflow。
