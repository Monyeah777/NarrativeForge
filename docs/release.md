# 发布编排（release）
> ⛔ 操作指令：本文是发布策略的**声明件**——`core/release_gate.py` 逐锚点机检（`nf release --plan` / check38 子扫描）；读到即执行，勿当资料。
> 最后更新：2026-10-05

## 这份文件解决什么

发布动作散在 `nf release`（体检）、`scripts/release_freeze.sh`（快照）、`scripts/bump_verify.sh`（换标）
与人工清单里，**顺序**与**前置**此前只存在于记忆。本文件把顺序写成可机检的锚点面，把执行交给一条命令：

```bash
python scripts/nf.py release --plan          # 人读计划（有序步骤：命令 / 产出 / 判据）
python scripts/nf.py release --plan --json   # 机读计划
python scripts/nf.py release                 # 发布前体检（= 既有 verify + 覆盖率 + e2e + 报告新鲜度）
python scripts/nf.py release --freeze --apply --by <批准人> --note "<本波说明>"
                                             # 按序执行冻结链（缺省只打印，不执行）
```

## 冻结链

**顺序不可颠倒**（依据 `decisions/ADR-0005-新增NET引擎线.md` 与 `postmortems/PO-0001-冻结顺序事故.md` 的教训）：内容定稿 →
一致性报告重算 → 内容绑定批准 → 协议层回执重签。

1. `python scripts/nf.py conformance --write`（产出 `protocol/conformance_report.json`，须 `conformant`）
2. `nf approve protocol/conformance_report.json --by <批准人> --note <说明>`（内容绑定；对象一改即失效）
3. `python scripts/nf.py receipts --scope protocol --write`（协议层回执单根 + 派生面联动刷新）

回执必须在**内容改动之后**最后跑——否则单根覆盖的是旧字节。改馆藏内容后另须
`nf library receipts --write`（收口链多一步）。

## 版本面

版本登记三处必须**不悬空**（重算口径见 `core/quality_baseline.py` 与 VERSION-MATRIX 自带的双向核验）：

| 处 | 真源 | 发布时动作 |
|---|---|---|
| `CHANGELOG.md` | 最新节 `## [X.Y.Z]` | 未发布 → 归档为已发布并留 PASS 基线 |
| `VERSION-MATRIX.md` | 版本 × 方案 × 能力行 | 补一行（版本 / 日期状态 / 方案 / 能力） |
| `README.md` 版本块 | 「当前」行 | 当前行切到新版本 |

`bash verify.sh` 是全量门禁的单入口；`PASS` 期望值是声明（`quality_baseline.EXPECTED_*`），
不手写在本文里（手写必漂）。

## Golden Master

tag 点把关键产物做成可复现存档：

```bash
bash scripts/release_freeze.sh vX.Y.Z
```

产出 = `.release-frozen/<tag>/sha256.manifest`（`01_核心协议.md` / `02_联动注册表.md` /
`06_Agent执行协议.md` / `07_官方核心出厂与社区预设导航.md` / `verify.sh` + `desktop/src/core/*.py`）
+ `sig-fingerprint.txt`（`nf sig --verify` 全量知识指纹）。快照是**历史时点事实**，不随现状更新；
结构不完整（缺件类 / 空摘要）即由 check38 的 `release_gate` 子扫描判红。

> 语言面：本指南另有 `docs/en/release.md`（English）· `docs/ja/release.md`（日本語）两版；本地化规则与覆盖面声明见 `docs/locales.md`（译件 `docs/en/locales.md` · `docs/ja/locales.md`）。注册表 = `protocol/locales.json`，判据 = check34 的语言面扫描。

## 变更条目

改动落地时在 `changes/unreleased/` 写一条条目（`type:` + `note:`，词表同 `CONTRIBUTING §1`）；
发布收口时由 `nf changelog` **生成**版本节（渲染确定、逐条可溯源：只做分组与格式，不改写原文），
审阅后 `--write` 落盘并归档条目到 `changes/<version>/`：

```bash
python scripts/nf.py changelog --version X.Y.Z --date YYYY-MM-DD          # 预览（发布 PR 的原生等价物）
python scripts/nf.py changelog --version X.Y.Z --date YYYY-MM-DD --write  # 落盘 + 归档
```

规则与理由见 `changes/README.md`；判据在 check38 的 `release_gate` 子扫描（字段缺失 / 条目不可溯源即红）。

## 边界（不宣称）

- 本机制**不代替** `verify.sh`：门禁绿是发布前提，不是质量顶尖的宣称。
- 计划是**编排**，不是证明：`--apply` 只按序调既有命令，不新增任何写语义。
- `git tag` 由人执行（本机制只给命令与判据）——打标是不可逆动作，不入自动执行面。
