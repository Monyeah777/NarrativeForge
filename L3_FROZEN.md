# L3 端壳层冻结声明（23 方案分层治理真相源）

> **Status**：冻结中（2026-09-05，23 方案方案 A 落地）——端壳不随基础层演进，最后一次性产出。

## 分层定义（23 方案）

| 层 | 仓库载体 | 本质 | 演进节奏 |
|---|---|---|---|
| L0 协议层 | 01/02 + 方案文档链（14–23） | 单一事实源声明 | 随变更演进 |
| L1 内容层 | 03/04/05（管线/模块/资产库） | 数据 | 随变更演进 |
| L2 核心逻辑层 | desktop/src/core（纯 Python 零第三方依赖） | 真身 | **高频迭代（主战场）** |
| L3 端壳层 | desktop GUI / android app | 包络 | **冻结 → 最后一次性产出** |

**战略依据**：端壳是包络层，基础层才是真身。每次基础层演进都重打两端、同步维护多端产物是纯工程损耗；分层后基础层可高频迭代，端壳只在最后一公里一次性包络。NF 已天然长出此骨架（desktop/src/core 刻意零第三方依赖 + android 靠 sync 单向镜像），本文件将其显式化、治理化。

## 本文件 = 移出清单索引 + 接回路径

**2026-09-05 移出主仓库演进主线（git rm，历史保留可回溯）**，commit `5ae202b`：

- `android/`（入库部分 13 文件：app bootstrap/config/controller/ui/screens + main.py + buildozer.spec + fonts/NotoSansSC + p4a_* 三补丁 + .gitignore；`android/app/{core,seed}` 本为 gitignored sync 生成物未入库）
- `desktop/src/ui/`（11 py：common/main_window/protocol_wizard_dialog/zone_a-g）
- `desktop/main.py` + `desktop/src/__main__.py`（GUI 入口，import src.ui）
- `desktop/packaging/`（narrative_forge.spec + build_linux/macos.sh + README）
- `desktop/scripts/smoke_gui.py` + `desktop/scripts/bench.py`（GUI 冒烟/基准，import src.ui）
- `scripts/smoke_zone_g_market.py`（E5 UI 冒烟，import src.ui.main_window——L3 专用）
- `scripts/selftest_android.py` + `scripts/sync_android.sh`（android 自测/同步工具）

**保留（L2/L0/L1，不受影响）**：`desktop/src/core/` 全量、`desktop/tests/` 全量、`desktop/scripts/seed_from_repo.py`、根 `scripts/e2e_desktop_headless.py`、`scripts/reconcile_assets.sh`。

## 治理同步（23 方案）

- verify.sh v2.9 分层门禁：check13① 去 android 比对（两处）、check12② compileall 去 android——**默认锁 L0-L2，clone 即绿零前置**（commit c681b72）。
- CI：新增 ci-verify.yml（checkout → verify.sh，push main 触发）；build-desktop/build-android 退役 main 自动触发——**仅 v* tag / 手动 dispatch**（commit 474a9dc）。

## 未来一次性产出接回路径

1. **恢复源码**：`git checkout 5ae202b^ -- android/ desktop/src/ui desktop/main.py desktop/src/__main__.py desktop/packaging desktop/scripts/smoke_gui.py desktop/scripts/bench.py scripts/smoke_zone_g_market.py scripts/selftest_android.py scripts/sync_android.sh`（从 git 历史恢复冻结快照）。
2. **重接 sync**：跑 `scripts/sync_android.sh` 从 desktop/src/core 重建 android/app/{core,seed}（若做 android 端）。
3. **启用构建**：build-desktop/build-android workflow 已保留 v* tag 触发，push v* tag 即出 EXE/APK Release。
4. **verify 豁免说明**：接回后 L3 文件不参与 verify L0-L2 门禁（check12/13 已去 android）；端侧质量靠各自 workflow 的构建/冒烟保障。

## 纪律

- 冻结期不随基础层提交改动 android/ 或 desktop/src/ui（演进回主线需先解冻并同步 verify/CI）。
- L2 core 新增能力不要求同步 android 镜像（sync 职责已退役，接回时一次性重建）。
