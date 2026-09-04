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

## 5. Issue / PR 规范

- **缺陷上报**：使用 .github/ISSUE_TEMPLATE/bug_report.md——APK 闪退必填：设备型号 / 系统版本 / App 版本 / 复现步骤 / 日志。
- **功能请求**：使用 .github/ISSUE_TEMPLATE/feature_request.md。
- **PR**：使用 .github/PULL_REQUEST_TEMPLATE.md，勾选改动域（协议层 / 代码层 / 社区包）+ 门禁自检清单（verify.sh 全绿 / unittest 40 用例 / 是否改 core 已 sync / py_compile 通过）。
