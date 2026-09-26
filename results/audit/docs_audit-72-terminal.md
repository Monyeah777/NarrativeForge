---
id: AUD-0024
title: NF 终端落地（nf shell）—— 端壳退役后的人机入口 + 端壳残留门禁（check39）
date: 2026-09-25
scope: 作者指令「删除 NF 中的 GUI，且为 NF 构建一个终端（CLI 开发）」。GUI 端壳源码/入口/打包线/CI 已于 2026-09-09 永久退役移出；本轮 = 退役状态复核并机制化（新增 check39 端壳零回潮）+ 终端入口落地（nf shell，纯 stdlib）。公开面只入结果态（代码 + 门禁 + 文档 + 本审计）。
verdict: pass
auditor: 本轮执行者
subjects:
  - desktop/src/core/terminal.py:d810f1312c0c2c21b0199ceb8afebc9a79a58139a0305405cb3f9cf0c1d0492b
  - scripts/nf.py:d4eba21b68225d3088e0f34463a2b711ea79feef31c9f273c4c8e7f67a6fa0fa
  - desktop/tests/test_terminal.py:cb42ec746dbb37d44c307156e20fd1bad2faa3c2d8f7bda14efda427c8ec68ea
  - scripts/nf:332e4512c1970d93858aadc9715d89fee5db61eae4d3dc49bac23de9bce65488
  - scripts/nf.cmd:a2563ccd0cdde64f1c394d3b426e22b3abd7d6438c5b3308f29d2086d9cac15c
  - verify.sh:c5b720488bc7dff44d243e6a94f10504bb3170a9aef3e3adb6a00eed4a700933
  - desktop/src/core/quality_baseline.py:2f56d683a21da1971ce69fc219bd3d6f5e336dc71ea37560920cfa744779d8e0
  - desktop/src/core/doc_hygiene.py:2b0acc2498874f2d37ca7d7e51b8f89d17c1bd5171e9532e75667c58d9d5f5fb
  - docs/terminal.md:3ed8ecc10f682c0c448f792308bae1975710965bbda004e6eaef39e6de91f85d
  - docs/L3_FROZEN.md:9dad824e749aac75ee4cf583adb48d0ede9c02a0a717ff43d314cbbfcb3cf3af
  - protocol/CONFORMANCE.md:566f676c1dc7e3fcf7211e8c04c7ff1c4050694a40b106d837a6559636e7a833
---

> 签收位：本件**未填 `accepted_by`/`accepted_at`**——验收签收属作者动作，执行者不自签。
> subjects 不含派生物：`protocol/repo_stats.json`、`results/interop/*.json`、`protocol/RECEIPTS.json`、
> `protocol/conformance_report.json`、`docs/verification-cards.md` 均为可复算投影或随基线刷新的
> 当前态文档，按既有口径不入审计绑定（它们由 check31/33/35/38 自证一致）。

## 一、内部差距（开工依据）

1. **端壳退役只到「历史事实」，没有常驻判据**：GUI 端壳已于 2026-09-09 由作者裁决永久退役
   （`5ae202b` 移出 `desktop/src/ui` + 打包线；`f8123b6` + 清理波移出 `desktop/main.py`、
   `desktop/src/__main__.py`、`desktop/packaging/`、`build-desktop.yml`、UI 测试/自检脚本）。
   但「已删除」这件事此前**没有任何门禁断言**——`purity_scan` R1 只扫 01/02 协议件里的端壳关键词，
   树内重新长出 GUI 模块不会被任何 check 拦住。
2. **人机交互面真空**：`docs/L3_FROZEN.md` 明文写「能力入口一律落 CLI」，而 CLI 只有非交互命令面，
   端壳退役后**没有**任何给人用的入口（`nf run` 需要参数、`nf --help` 是命令清单，不是可用界面）。
   这是 S7「产品上手门槛」在无壳前提下唯一可做的近端解。
3. **终端与命令面可能静默脱钩**：任何菜单/引导若手写命令示例，都会随 CLI 演进腐烂
   （仓库既有教训：`interop` 可选值两次漏同步、`_cov_tmp.json` 类漂移）。需要「菜单不许指向死命令」的机检。

## 二、交付

| 面 | 落点 |
|---|---|
| 终端核心 | `desktop/src/core/terminal.py`（纯 stdlib · 确定性 · 可注入 `runner` 的会话状态机；**不反向依赖** `scripts/nf.py`） |
| CLI 入口 | `scripts/nf.py` 新增 `shell`（别名 `terminal`）：`--exec` 非交互 / `--json` 机器面 / `--no-banner` / `--yes` |
| 启动器 | `scripts/nf`（POSIX）+ `scripts/nf.cmd`（Windows）：无参数即进终端 |
| 能力菜单 | 端壳时代 GUI 七区（导入/校验/管线/生成/资产/预设/社区）→ **既有**命令面映射；菜单真源 = `terminal.ZONES` |
| 安全闸门 | 写入类命令（`--write`/`--apply`/`--register`/`--tag`/`--rm`… + `register`/`import`/`rename`/`release`/`asset add…`）默认拒跑；交互输入 `yes` 或显式 `--yes` 才放行；`serve`/`shell` 在会话内只给指引 |
| 门禁 | verify **check39**：端壳残留零在场（7 个已知落点 + 全树源件扫描）+ 终端三件在场 + 菜单示例全部可解析到真实命令 + `--exec` 两遍逐字节一致 |
| 单测 | `desktop/tests/test_terminal.py` 31 例（解析/闸门/会话/CLI 集成/零依赖面；含「菜单指向死命令即红」与「SystemExit 不打断会话」） |
| 文档 | `docs/terminal.md`（入 doc_hygiene 四型与指令档清单）+ README/README.en 五分钟上手 + llms.txt 工具面 + ROADMAP/L3_FROZEN 状态 |
| 基线 | verify v2.28 → **v2.29**；`quality_baseline.EXPECTED_*` = **check1-39 · PASS=68** |

## 三、验收证据（本机实测）

- `bash verify.sh` → **PASS=68 · WARN=0 · FAIL=0（exit 0）**。
- `nf shell --exec "/menu"` 两次输出逐字节一致；`--json` 输出 `nf-shell` 逐条记录。
- `nf conformance` → **conformant 27/27**（含审计面）；`nf audit` 扫描零 issue；`nf approve --verify` 有效；
  `nf receipts` 根与实时重算一致；`nf interop --check` 入仓面逐字节一致；`nf stats --check` 自述数字一致。
- 端壳残留实测：树内无 `desktop/main.py`、`desktop/src/ui/*.py`、`desktop/packaging/`、
  `build-desktop.yml`、`build-android.yml`、GUI 测试与自检脚本（`rg` 全树为空）。

## 四、设计偏差与边界（如实记录）

1. **终端是逐行 REPL，不是全屏 TUI**：Windows 无 `curses`、core「零第三方依赖」是成文红线、
   且逐行读写可重定向/可 diff/可进 CI。全屏 TUI 会引入终端能力耦合，故不做（边界写入 `docs/terminal.md`）。
2. **门禁选新增 check39 而非并入 check33**：与 check38 的既有节奏一致（每面一条独立 check，可追溯）；
   代价是基线数与派生文档必须同步刷新（本轮已同步：CONFORMANCE 声明 / conformance 报告 / 内容绑定批准 /
   协议层回执 / interop 入仓面 / 验证卡册 / 审计 digest）。
3. **旧审计 digest 重绑**：基线变更触及 15 份审计件的被审对象（29 条），按仓库既有实践
   （见 commit `ba1cb08`「审计摘要重绑」）重绑 digest，使审计面回到自洽；**未**逐件重写旧审计结论——
   本波改动面由本件（AUD-0024）承担记录责任。此项属执行者自决的机械修复，作者可复核。
4. **未做（遗留）**：① 17 个孤儿字节码（GUI/APK 时代模块的 `.pyc`）待作者确认后清理；
   ② `scripts/e2e_desktop_headless.py` 与 `.github/workflows/e2e-desktop.yml` 的「desktop」命名属端壳时代遗留
   （功能是 headless core E2E，与 GUI 无关），改名牵连 purity_scan 放行键与单测，未擅动；
   ③ L2 真身仍挂在端壳时代目录名 `desktop/` 下，是否改名 `core/` 属独立一波，需作者立项。

## 五、五维自评（改了什么维 / 水位 / 差在哪）

| 维度 | 本波水位 | 说明 |
|---|---|---|
| 静态可核验 | ↑ | 新增 check39（端壳零回潮 + 终端可达 + 菜单无死命令 + 输出确定），基线 PASS 66 → 68，全绿 |
| 动态可执行 | ↑ | 终端把「协议被真实执行」的人机入口补回：命令直通 + 写入面闸门 + 确定性回归面 |
| 架构纯度 | →／↑ | 终端纯 stdlib、core 不反向依赖 CLI、菜单与命令面单一判据；端壳残留从「无判据」变「零容忍」 |
| 资产密度 | → | 本波不新增内容资产（终端为能力面，非内容面） |
| 文档可执行性 | ↑ | `docs/terminal.md` 读到即能跑；README 双语面同步并由 check34 断言一致 |
| 差在哪 | — | 全屏 TUI / 真·交互式表单（GUI 时代 zone 表单）未做：前者违背零依赖红线，后者需作者裁决新形态 |
