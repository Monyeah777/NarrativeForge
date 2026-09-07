# L3 端壳层冻结声明（23 方案分层治理真相源 · 38 方案脉冲契约升级）

> **Status**：第 1 波接线完成（v2.6，2026-09-06）→ **已回冻结**。契约：端壳默认冻结，触发条件达成立即接线，波后回冻结（脉冲式，38 方案 F2 裁决）。
> **契约升级记录**：F2 三问裁决（38 Stage 0 G3，用户 2026-09-06）——「不恢复常态化，改为冻结-接线-冻结脉冲节奏」；决策档案 docs_f2-decision-steelman.md。
> **APK 线移除记录（裁决 #16，2026-09-07）**：Android APK 线**彻底移除**——`git rm` android/（含 app bootstrap/config/controller/ui/screens/main/buildozer/p4a 补丁）+ build-android.yml + selftest_android.py + sync_android.sh；check_ui_core_links 同步去 android 化（桌面 UI-only）。理由 = 包络负资产：首次构建 10h+、v0.8/v0.9/v2.6 三轮闪退修复、CI 绿 ≠ 真机不闪退、作者学生预算月投入数百；APK 三大功能（浏览/预览/轻导出）已被 AI 线（A/B1）全覆盖。**桌面 GUI 保留冻结-脉冲契约，android 项不再恢复（git 历史可回溯）**。
> **第 1 波记录（v2.6，38 方案 Stage 2-5）**：冻结快照恢复 commit `51f7130`（35 个 L3 文件自 5ae202b^ 单 commit 回接）→ W1-W9 接线（读入入口 / doc_semantics 声明 / 一键全链 / 变体选项 / rules 多出口 / 五格式导出 / 质量门面板 / 市场目录 / MCP serve，commit 序列 a95ba7e→5a3c0e4）→ 桌面冒烟 smoke_gui 22/22 全绿 → build-desktop/build-android workflow 干跑产线恢复（APK 构建 + emulator 启动冒烟）。波后回冻结，下次触发按积压 ≥6 项或用户驱动。

## 分层定义（23 方案）

| 层 | 仓库载体 | 本质 | 演进节奏 |
|---|---|---|---|
| L0 协议层 | 01/02 + 方案文档链（14–23） | 单一事实源声明 | 随变更演进 |
| L1 内容层 | 03/04/05（管线/模块/资产库） | 数据 | 随变更演进 |
| L2 核心逻辑层 | desktop/src/core（纯 Python 零第三方依赖） | 真身 | **高频迭代（主战场）** |
| L3 端壳层 | desktop GUI（Android APK 已移除 #16） | 包络 | **冻结 → 脉冲式接线波（触发条件 + 接线账）** |

**战略依据**：端壳是包络层，基础层才是真身。每次基础层演进都重打两端、同步维护多端产物是纯工程损耗；分层后基础层可高频迭代，端壳只在**触发条件达成时**执行一次「批量接线 + Release 产出」，完成后回到冻结。NF 已天然长出此骨架（desktop/src/core 刻意零第三方依赖），本文件将其显式化、治理化。

**脉冲节奏（38 方案 F2 裁决替代「最后一次性产出」）**：
- 端壳**默认态 = 冻结**（不逐功能跟进，沿用 23 方案全部纪律）；
- **解冻触发条件**（非时间拍脑袋）：基础层能力积压 ≥ 一批——**未接线新能力 ≥6 项**，或出现**用户/消费方驱动的必须项**；
- 触发后执行一次「批量接线 + Release 产出」（v2.6 = 第 1 波承诺交付），完成后回到冻结；
- **质量分层永久保留**：L3 不参与 verify（clone 即绿不破），端侧质量靠 workflow 构建 + 冒烟断言（smoke_gui）——治理红利永不回退；
- 下一次接线点**不预设死期**（示例 v2.8 或 3.0，按实际积压触发）；
- **接线账为触发条件的机读基础**：每次基础层发布在 CHANGELOG 标注「端壳待接线项」计数（积压量单一事实源，见 CHANGELOG 发布条目惯例）。

## 本文件 = 移出清单索引 + 接回路径

**2026-09-05 移出主仓库演进主线（git rm，历史保留可回溯）**，commit `5ae202b`：（注：清单中 android 相关项 2026-09-07 升级为**彻底移除**——裁决 #16，不再恢复；desktop/ui 等桌面端壳项仍按脉冲契约冻结可接回）

- ~~`android/`（入库部分 13 文件）~~——**【已彻底移除·裁决 #16·2026-09-07·不再恢复】**，历史见 git
- `desktop/src/ui/`（11 py：common/main_window/protocol_wizard_dialog/zone_a-g）
- `desktop/main.py` + `desktop/src/__main__.py`（GUI 入口，import src.ui）
- `desktop/packaging/`（narrative_forge.spec + build_linux/macos.sh + README）
- `desktop/scripts/smoke_gui.py` + `desktop/scripts/bench.py`（GUI 冒烟/基准，import src.ui）
- `scripts/smoke_zone_g_market.py`（E5 UI 冒烟，import src.ui.main_window——L3 专用）
- ~~`scripts/selftest_android.py` + `scripts/sync_android.sh`~~——**【已彻底移除·裁决 #16·2026-09-07·不再恢复】**

**保留（L2/L0/L1，不受影响）**：`desktop/src/core/` 全量、`desktop/tests/` 全量、`desktop/scripts/seed_from_repo.py`、根 `scripts/e2e_desktop_headless.py`、`scripts/reconcile_assets.sh`。

## 治理同步（23 方案）

- verify.sh v2.9 分层门禁：check13① 去 android 比对（两处）、check12② compileall 去 android——**默认锁 L0-L2，clone 即绿零前置**（commit c681b72）。
- CI：新增 ci-verify.yml（checkout → verify.sh，push main 触发）；build-desktop 退役 main 自动触发——**仅 v* tag / 手动 dispatch**（commit 474a9dc；build-android.yml 已随 APK 线移除）。

## 接线波接回路径（触发条件达成时执行）

1. **恢复源码（桌面端壳）**：`git checkout 5ae202b^ -- desktop/src/ui desktop/main.py desktop/src/__main__.py desktop/packaging desktop/scripts/smoke_gui.py desktop/scripts/bench.py scripts/smoke_zone_g_market.py`（从 git 历史恢复冻结快照；**android 相关项不再恢复**——裁决 #16）。
2. **启用构建**：build-desktop workflow 已保留 v* tag 触发，push v* tag 即出 EXE Release（Android APK 不再产）。
4. **verify 豁免说明**：接回后 L3 文件不参与 verify L0-L2 门禁（check12/13 已去 android）；端侧质量靠各自 workflow 的构建/冒烟保障。

## 纪律

- 冻结期不随基础层提交改动 desktop/src/ui（演进回主线需触发接线波并同步 verify/CI）。
- L2 core 新增能力无端壳同步义务（sync 已随 APK 线移除；桌面 UI 接线波时一次性接线）。
- **接线波纪律（38 方案）**：每次接线波须有明确接线账（能力 → GUI 呈现映射清单）+ 波后冒烟断言（smoke_gui）+ Release 产出；波完成即回冻结，不进入常态化逐功能跟进。
