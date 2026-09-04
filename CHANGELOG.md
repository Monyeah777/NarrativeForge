# Changelog

> 格式约定：Keep a Changelog 中文化（Added/Changed/Fixed 语义）；版本段按时间倒序；[Unreleased] = 当前主线开发中；发布即归档为 [版本号] + 日期段并打 annotated tag（ROADMAP §8 治理指针 3）。
> 基线说明：本文件随 v0.6.0 方案 B 第①步落盘（2026-09-04）；早期版本（v0.1.0–v0.5.0）条目按 git 版本史（八 tag）回写简述。

## [Unreleased] - v0.6.0 协议中转站（开发中）

### Added
- 工程治理三件套落盘：ROADMAP.md（五版本路线唯一规划真相源 + 治理指针四项）/ CHANGELOG.md（本文件）/ CONTRIBUTING.md（Conventional Commits + 四步验证门槛 + 三改动域细则）。
- .github 模板：ISSUE_TEMPLATE（bug_report / feature_request）+ PULL_REQUEST_TEMPLATE（改动域勾选 + 门禁自检清单）。
- verify.sh 增 check12 代码层门禁（desktop/tests/test_core.py 40 用例 unittest + py_compile 语法抽查）。

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
