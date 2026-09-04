# NarrativeForge 路线图（ROADMAP）

> **定位**：v0.5.0 → v1.0.0 五版本路线的**唯一规划真相源**（I5）。本文件只回答「往哪走、边界在哪、交付锚点是什么」；每版本的**任务级分解与验收**见对应方案文档（08_/09_…）。
> **治理指针**：发布、版本行、方案文档追加、门禁四项约定见 §8——任何版本演进不得绕过。

## 1. 版本总览

| 版本 | 代号 | 状态 | 一句话目标 | 方案真相源 |
| --- | --- | --- | --- | --- |
| v0.5.0 | 优化版 | ✅ 已发布（2026-09-04） | 吸收外部项目精华、夯实底层能力（T1–T6） | 08_v0.5.0_优化版方案.md |
| v0.6.0 | 协议中转站 | ✅ 已发布（2026-09-04） | 协议体系从人读规范文档升级为机读可驱动的通用协议层 | 09_v0.6.0_协议中转站方案.md |
| v0.7.0 | 自定义协议 | ✅ 已发布（2026-09-04） | 对外开放协议注册，第三方可注册自定义协议 | 10_v0.7.0_自定义协议方案.md |
| v0.8.0 | 自定义模块组合 | 🔵 当前主线 | 对外开放模块组合，第三方题材模块可组合装配 | 11_v0.8.0_自定义模块组合方案.md |
| v0.9.0 | Android 同步门禁 | 🔮 规划 | APK 闪退修复 + Android↔真源同步差异入 CI | — |
| v1.0.0 | 全平台正式版 | 🔮 规划 | desktop / android / 协议层 / 社区生态收口，正式发布 | — |

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

## 5. v0.8.0 自定义模块组合（🔵 当前主线）
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

## 6. v0.9.0 Android 同步门禁 + APK 闪退修复（🔮 规划）

一句话：修复 Android 端 APK 闪退问题；把 sync --check 差异校验接入 CI（缺口⑦闭环：Android↔真源一致性不再靠人工）。前置：v0.6.0 已交付 sync_android.sh --check 模式本体。

## 7. v1.0.0 全平台正式版（🔮 规划）

一句话：desktop / android 双端 + 协议层 + 社区生态收口，全平台正式发布。

## 8. 治理指针（四项约定）

1. **README 版本行指针**：README 版本行（L33 锚点「vX.Y.Z（当前主线）」）随发布更新。
2. **协议链随方案文档追加**：README L32 协议链每新增方案文档（08→09→…）追加一行。
3. **CHANGELOG 发布归档**：每次发布把 [Unreleased] 归档为 [版本号] + 日期段，并同步打 annotated tag。
4. **门禁全绿铁律**：verify.sh（含 check12 代码层 unittest）0 WARN 0 FAIL 方可提交；任一 FAIL = 协议事故，回滚再改。
