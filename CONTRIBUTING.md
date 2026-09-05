# 贡献规范（CONTRIBUTING）

> **适用对象**：对 NarrativeForge **协议层（01–07 + 08/09 方案）**、**代码层（desktop/ android/ scripts/）**、**社区领域包（community/）** 的任何改动。
> **门禁铁律**：**任一 FAIL = 协议事故，回滚再改**；0 WARN / 0 FAIL 方可提交（verify.sh 语义）。

## 1. 提交信息格式（Conventional Commits）

格式：`<type>(<scope>): <subject>`——subject 用中文一句话，禁句号结尾。

| type | 用途 | 示例 |
| --- | --- | --- |
| feat | 新功能 / 新资产 / 新文档 | `feat(desktop): ROADMAP 落盘 + v0.6.0 治理缺口补漏` |
| fix | 缺陷修复 | `fix(android): minapi 23→24 修复 APK 构建` |
| docs | 文档 / 协议改动 | `docs(protocol): 02 §8 登记 P03 西幻包` |
| refactor | 重构不改行为 | `refactor(core): storage 导入路径收口` |
| test | 测试增补 | `test(core): verify.sh 增 check12 代码层门禁` |
| chore | 杂项 / CI | `chore(ci): build-desktop 增 unittest 步骤` |

scope 约定：`protocol`（01–07）/ `desktop` / `android` / `scripts` / `community` / `ci` / `core`（desktop/src/core 与 android/app/core 共用真相源）。

## 2. 分支策略：单主干 + 版本锚点

- 主干 main 为唯一长期分支，改动直接推 main（大改动可短命分支合并后删除）。
- **版本锚点**：发布即打 annotated tag（vX.Y.Z），tag 为版本真相源（I5），禁止在已发布 tag 上回写。
- 开工前工作树须干净（当前基线 HEAD=eac0fbd，tag v0.5.0）。

## 3. 验证门槛（提交前四步，全部通过）

```bash
# ① 协议门禁（check1–11 两段式：段 A 官方 / 段 B 社区）
bash verify.sh
# ② 代码层门禁（check12 同款：desktop core 40 用例）
cd desktop && python3 -m unittest discover -s tests -q && cd ..
# ③ Android 同步（改 desktop/src/core 后必跑；产物 android/app/{core,seed} 为 .gitignore 生成物不入库）
bash scripts/sync_android.sh
# ④ 语法抽查（全量 py 编译）
python3 -m compileall -q desktop/src android/app scripts
```

任一失败即回滚本次修改，修正后重跑；全绿方可提交推送。

## 4. 改动域细则

### 4.1 协议层（01–07 + 08/09 方案）
- 结构性改动走 **06 §10 修改规程四步闭环**：按协议声明 → 登记真相源 → verify.sh 自检 → 提交同步导航面。
- 动 01/02/06 契约触发 **01 §7 V2 bump**（结构性变更 + 迁移说明）；registry_schema_version / save_schema_version 双字段联动升级。
- 新增方案文档（08→09→…）须同步 README L32 协议链与 ROADMAP §1 总览表，不在多处重复维护任务清单。

### 4.2 代码层（desktop/ android/ scripts/）
- **core 零第三方依赖**（纯标准库）；确需引入第三方依赖先开 Issue 讨论。
- 改 desktop/src/core 任一文件**必跑 `bash scripts/sync_android.sh`**（android/app/core 为生成物被 .gitignore 忽略，单一事实源在 desktop/src/core 与 03/04/05）。
- 新增可测逻辑放 desktop/tests/，纳入 unittest 体系（check12）；暂不做端到端 / GUI 测试入 CI。
- Android 控制器侧纯逻辑自测：`python3 scripts/selftest_android.py`（前置已 sync）。

### 4.3 社区领域包（community/）
- 遵循 R1（包间禁互引）/ R2（类别独占）/ R3（装配契约）；新模块走 02 §8.1 登记，跑 verify.sh check7–11。
- 资产须登记溯源索引（assets/README.md）并满足 EXT 闭合（起始/终止行溯源注释 + 外部完整实体源标注），`bash scripts/reconcile_assets.sh --quiet` 应全清。

### 4.4 社区包协作流程（v1.0.0 起：第三方协议贡献全流程）

> **收口锚点**：兑现 10_v0.7.0_自定义协议方案 §6 开放问题 4——第三方包从提交到登记的协作流程（PR/评审/发布）原「不属 v0.7.0 协议层范畴……流程治理留待 v1.0.0 生态收口」，本版以文档化收口：**人读流程 = 本节五步**（提交 → PR 评审 → 登记 → 发布，含前置协议合规自检），**机读门禁 = verify.sh check 断言配套**（check14/check15/check16，见 02 §9.2）。流程治理本版 = 文档化，不做平台化/工具化（PR 机器人 / 自动登记流水线留后续，同防范围蔓延纪律）。适用对象：向 community/ 贡献新社区领域包（02 §8.1/8.2 同型）或组合管线包（02 §8.4 同型）的第三方。

**① 协议合规自检（提交前，贡献者必过）**
- **protocol.yaml 三要件齐备**（02 §8.3）：包根机读协议声明在场（01 §6.1 Schema 必填 12 字段，check14 ①-⑥ 断言）；登记要素（包目录/管线/模块/资产/类别）齐备；组合包另须 references 合规（02 §8.4 四规则：在册可寻址 / 依赖闭包闭合 / 同层 default 唯一 / 契约断裂 FAIL 阻断 + 自动仲裁）。
- **本地自检单**：`bash verify.sh` check1–16 全绿（0 WARN / 0 FAIL；check14 注册门禁 / check15 组合门禁为社区包专项）；代码/同步/语法按 §3 四步验证门槛全过；资产经 asset_get 寻址、登记溯源索引并满足 EXT 闭合，`bash scripts/reconcile_assets.sh --quiet` 全清（§4.3）。

**② 提交（分支 / commit / 引用规范）**
- 分支策略按 §2（单主干 main 直推或短命分支合并）；commit 信息遵循 §1 Conventional Commits——type 取 `feat`（新包落盘）/ `docs`（协议改动），scope 取 `community`。
- 方案文档引用：结构性协议改动须可溯方案文档（README L32 协议链）与登记真相源 02，不在多处重复维护任务清单（§4.1）。

**③ PR 评审（reviewer 判据）**
- 使用 .github/PULL_REQUEST_TEMPLATE.md，勾选「社区包」改动域 + 门禁自检清单（§5）。
- **协议层 reviewer 判据 = 02 §8.1–8.4 登记规则 + check 全绿**：整包登记对照 §8.3 登记三要件、组合登记对照 §8.4 登记判定四规则；verify.sh check1–16 PASS=22 全绿为合并前提。
- 评审范围含题材/资产合规：模块遵循 R1（包间禁互引）/ R2（类别独占）/ R3（装配契约）；资产 EXT 闭合 + 溯源索引在册（§4.3）。

**④ 登记（协作流程终点的机读落地）**
- 02 §8 登记表登记（新领域包走 §8.1/8.2 同型、组合管线包走 §8.4），编号落 M91–M99 段、不占官方核心 13 件与既有社区包编号（§8.3）；同步 registry.json `protocols[]` 投影（02 §9.1 字段映射；check14 ⑦ 断言）。
- 三要件缺一即不被平台门禁识别（02 §8.3）；**登记 = 协作流程终点的机读落地**（02 §9.2 协作流程纪律）。

**⑤ 发布（README 双源声明 + 版本行同步 + 发布纪律）**
- 包 README 装载手册声明登记指针——「登记三要件见 02 §8.3，组合登记见 02 §8.4」（对齐既有两包形态）；根 README 开箱即玩社区预设段与 07 §3 索引同步增补（双源声明一致，I5）。
- 版本行同步：schema_version / registry_schema_version 等字段级改动走 01 §7 V1（只增不删）/ V2（结构性变更 bump + 迁移记录）规则。
- 发布纪律：tag vX.Y.Z 为版本真相源（I5）、禁止在已发布 tag 上回写（§2）；发布条目同步 CHANGELOG 与 ROADMAP。

### 4.5 方案文档纪律（NN_ 方案模板必填两段，v2.2.0 B1/B2 起）
新增/修订方案文档（`NN_<版本>_<主题>方案.md`，含 .rivet/plans/ 草稿与 08-32 既有同型）**必含**以下两段，位置在「核心」段之后：

**B1 五问自检（Clarify 自检，每方案回答五问）**
1. **谁消费本功能**——具体消费方（模块/CLI/verify check/文档/外部产物格式），不接受「将来可能有用」。
2. **何时/如何验证被消费**——验证动作 + 时机（如「nf CLI 冒烟输出」「verify checkNN 绿」「单测断言」），可独立跑、有可观察结果。
3. **与非目标边界**——明确不做（对照 01 §5 I5 / L3_FROZEN 冻结面 / ROADMAP 条件池），一句话边界声明。
4. **与现存协议关系**——涉及 01-07 哪一层、是否需 02 登记 / registry 投影 / schema bump（V1/V2）。
5. **失败定义**——什么算验收不通过（RED 判据），与 §3 验证门槛对齐。

**B2 消费方声明（防 C-a 无消费方能力重演，并入 B1 五问 ①/②）**
- 以表格或清单声明：**功能** → **谁消费** → **怎么验证被消费**。消费方为空的条目不得进入方案（须先裁掉或绑定后续立项）。
- 追溯锚点：落地后 README L32 协议链 / CHANGELOG 条目须能指回该方案（治理指针 2），verify 新增 check 须在头部配套说明引方案号。

> 反例（C-a 教训）：模块质量分级曾因无消费方搁置——五问 ① 答不出「谁消费」即方案未成熟。正面示例见方案 33（A2 消费方 = nf who-refers CLI + retriever 库；A4 = verify check21）。

## 5. Issue / PR 规范
- **缺陷上报**：使用 .github/ISSUE_TEMPLATE/bug_report.md——APK 闪退必填：设备型号 / 系统版本 / App 版本 / 复现步骤 / 日志。
- **功能请求**：使用 .github/ISSUE_TEMPLATE/feature_request.md。
- **PR**：使用 .github/PULL_REQUEST_TEMPLATE.md，勾选改动域（协议层 / 代码层 / 社区包）+ 门禁自检清单（verify.sh 全绿 / unittest 40 用例 / 是否改 core 已 sync / py_compile 通过）。
