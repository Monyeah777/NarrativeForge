# L3 端壳层退役记录（23 方案分层治理真相源 · 2026-09-09 永久退役）

> **Status**：~~冻结-接线脉冲契约~~ → **2026-09-09 永久退役（作者裁决）**：桌面 GUI 端壳与打包/发布线彻底移出公开面，**不再有接线波**——与 android 线（裁决 #16）同轨。git 历史完整可回溯。
> **契约史**：23 方案分层治理（L0 协议 / L1 内容 / L2 core / L3 端壳）→ 38 方案 F2 三问裁决（2026-09-06：冻结-接线-冻结脉冲节奏，决策档案 docs_f2-decision-steelman.md）→ 第 1 波接线 v2.6 收口（2026-09-06，commit 序列 51f7130→5a3c0e4，smoke_gui 22/22 + build-desktop/build-android 干跑）→ 波后回冻结 → **2026-09-09 作者裁决永久退役**（W33 移出 + 本地清理波收尾）。
> **APK 线移除记录（裁决 #16，2026-09-07）**：Android APK 线**彻底移除**——`git rm` android/（含 app bootstrap/config/controller/ui/screens/main/buildozer/p4a 补丁）+ build-android.yml + selftest_android.py + sync_android.sh；check_ui_core_links 同步去 android 化。理由 = 包络负资产：首次构建 10h+、v0.8/v0.9/v2.6 三轮闪退修复、CI 绿 ≠ 真机不闪退、作者学生预算月投入数百；APK 三大功能（浏览/预览/轻导出）已被 AI 线（A/B1）全覆盖。**不再恢复（git 历史可回溯）**。
> **桌面端壳退役记录（2026-09-09，作者裁决「清掉，保持干净」）**：W33（f8123b6 移出 desktop/src/ui 全量 + 壳打包脚本 + build-desktop.yml + UI 测试/检查脚本）+ 清理波（9b6a443/b5b7e90 后续 commit）`git rm` desktop/main.py + desktop/src/__main__.py + desktop/packaging/（spec/README）+ desktop/scripts/smoke_gui.py/bench.py + scripts/smoke_zone_g_market.py。理由 = 端壳包络能力已被 **CLI（scripts/nf.py：run/import/assemble/serve…）+ AI 装配线（AGENT_START/组装指令包）全覆盖**；PySide6 三平台打包与 UI 测试同步维护负担与 APK 线同型；公开面一致性（README/community 已无桌面工具叙事）。**不再恢复**。

## 分层定义（23 方案，退役后现状）

| 层 | 仓库载体 | 本质 | 演进节奏 |
|---|---|---|---|
| L0 协议层 | 01/02 + 文档链 | 单一事实源声明 | 随变更演进 |
| L1 内容层 | 03/04/05（管线/模块/资产库）+ community/ | 数据 | 随变更演进 |
| L2 核心逻辑层 | desktop/src/core（纯 Python 零第三方依赖）+ scripts/nf.py | 真身 | **高频迭代（主战场）** |
| L3 端壳层 | ~~desktop GUI + 打包线~~（Android #16；桌面 2026-09-09） | 包络 | **已退役——不再接线** |

**战略依据（历史）**：端壳是包络层，基础层才是真身。分层后基础层可高频迭代，端壳只在触发条件达成时执行「批量接线 + Release 产出」。2026-09-09 后该层整体退役——基础层（协议 + core + CLI + AI 装配）已自足，仓库不再产桌面壳。

## 本文件 = 退役清单索引 + 保留边界

**2026-09-05 首次移出主仓库演进主线**（commit `5ae202b`）→ **2026-09-07 android 彻底移除（#16）** → **2026-09-09 桌面端壳彻底移除（作者裁决）**：

- ~~`android/`（入库部分 13 文件）~~——**【已彻底移除·裁决 #16·2026-09-07·不再恢复】**
- ~~`desktop/src/ui/`（11 py：common/main_window/protocol_wizard_dialog/zone_a-g）~~——**【已彻底移除·2026-09-09·不再恢复】**
- ~~`desktop/main.py` + `desktop/src/__main__.py`（GUI 入口，import src.ui）~~——**【同上】**
- ~~`desktop/packaging/`（narrative_forge.spec + build_linux/macos.sh + README）~~——**【同上】**
- ~~`desktop/scripts/smoke_gui.py` + `desktop/scripts/bench.py`（GUI 冒烟/基准，import src.ui/PySide6）~~——**【同上】**
- ~~`scripts/smoke_zone_g_market.py`（E5 UI 冒烟，import src.ui.main_window）~~——**【同上】**
- ~~`scripts/selftest_android.py` + `scripts/sync_android.sh`~~——**【已彻底移除·裁决 #16·2026-09-07·不再恢复】**
- ~~`.github/workflows/build-desktop.yml` + `build-android.yml`~~——**【已彻底移除·不再恢复】**

**保留（L2/L1/L0，不受影响）**：`desktop/src/core/` 全量、`desktop/tests/` 全量、`desktop/scripts/seed_from_repo.py`（种子导入器，保留）、根 `scripts/e2e_desktop_headless.py`（headless core 直驱 E2E，CI e2e-desktop.yml 在跑）、`scripts/reconcile_assets.sh`。

## 治理同步（现状）

- verify.sh v2.22：默认锁 L0-L2，clone 即绿零前置；check12 = desktop core/tests unittest 全量 + 全量 py_compile（端壳文件已不在树，compile 面随退役收窄）。
- CI：ci-verify.yml（push main 触发 verify.sh）；e2e-desktop.yml（headless core 直驱，无需 GUI）；release-gate.yml（v* tag 即跑 verify+基线+覆盖率）。

## 纪律（退役后）

- **端壳线不预设恢复**：新 GUI/新壳形态须作者新裁决后另行立项（不复用本文件路径，不沿用冻结脉冲机制）。
- **L2 core 是唯一真身**：新增能力无端壳同步义务；能力入口一律落 CLI（nf.py）与文档/AI 装配线。
- **公开面一致性**：任何文档不得再出现桌面工具下载/运行/打包指引（README/community 已清零，回归由 doc_hygiene 与人工检查共同兜底）。
