# 照做步骤（FDE 样例 · 命令原文）

> 读者：FDE 或客户侧复核人。把下面的命令原样粘贴执行即可复现本样例；每步给**期望输出**与**退出码**。
> 口径：本样例只用仓库内产物，不联网。

## 步骤 0 · 取件与定位

```bash
git clone <repo> && cd <repo>
python -c "import sys;print(sys.version)"
```

期望：Python ≥ 3.11。退出码 0。

## 步骤 1 · 跑样例并落证据

```bash
python scripts/fde_sample_run.py --run
```

期望输出（形状）：

```
== FDE 样例已跑 ==  证据 4 件 → docs/fde-sample/evidence/
```

退出码 0（任一 G1–G4 失败则非 0，并打印 `[FAIL]` 行）。

## 步骤 2 · 核对五道门

```bash
cat docs/fde-sample/evidence/gates.txt
```

期望：五行 `[PASS]`（G1 产出面 / G2 契约 / G3 概念图 / G4 装配链 / G5 中游出口）。

## 步骤 3 · 复算（防样例腐烂）

```bash
python scripts/fde_sample_run.py --check
```

期望：`== FDE 样例自检 ==  门 5 · 证据件 4`；退出码 0。
若报 FAIL → 说明仓库状态已变，重跑步骤 1。

## 步骤 4 · 交付物

```bash
sed -n '1,40p' docs/fde-sample/evidence/deliverable.md
```

期望：技术文档形态的交付物——系统卡摘要（用途/限制/风险框架）、概念闭包（目标/规模/证据强度）、交付面清单、装配步骤、验收判据表。

## 步骤 5 · 两层出口核对（中游标准成立性）

```bash
python scripts/nf.py stats --check        # 自述数字 = 实算
python scripts/geo_export.py --check      # 标准锚面 = 生成物
bash verify.sh                            # 单入口门禁（需 bash）
```

期望：前两条退出码 0；`verify.sh` 输出末行 `>>> 全部通过（WARN 仅提示非致命），变更可提交 <<<`。

## 步骤 6 · 第三方可跑的下一步（不在本样例内）

客户/第三方若要证「互操作兼容」，按 `docs/interop-thirdparty.md` 的卡片自选对端工具跑一遍，并把结果回填 `results/interop-thirdparty-status.md`（六字段齐备才算一条他证）。

## 变更记录（本文件随样例演进）

| 日期 | 变更 |
|---|---|
| 2026-09-24 | 首版：五门（G1–G5）+ 六步照做 |
