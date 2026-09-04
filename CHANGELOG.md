# Changelog

> 格式约定：Keep a Changelog 中文化（Added/Changed/Fixed 语义）；版本段按时间倒序；[Unreleased] = 当前主线开发中；发布即归档为 [版本号] + 日期段并打 annotated tag（ROADMAP §8 治理指针 3）。
> 基线说明：本文件随 v0.6.0 方案 B 第①步落盘（2026-09-04）；早期版本（v0.1.0–v0.5.0）条目按 git 版本史（八 tag）回写简述。

## [Unreleased] - v0.9.0 Android 同步门禁 + APK 闪退修复（开发中）
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
