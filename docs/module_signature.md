# 模块边界冻结（module signature）
> ⛔ 操作指令：阅读即执行——本文含可直接执行的命令与判定，勿当资料阅读。
> 最后更新：2026-09-14

## 是什么

模块对外的**承诺**（`inputs` / `outputs` / `events` / `interfaces` / `layer` / `category` /
`io_types`）冻结成基线 `protocol/module_signatures.json`（摘要 + 路径）。
边界改了而没重签 → **FAIL**；这样"顺手改边界"不能悄悄发生（机制借自 Pipelex `signature_for`）。

## 怎么用

```bash
python scripts/nf.py module signature            # 校验（漂移即 FAIL）
python scripts/nf.py module signature --write    # 评审后显式重签
```

## 边界

- 只取**边界字段**，`description`/`note` 等易变文本不参与（避免假漂移）。
- 未签（新增模块）与撤下（基线有、仓库无）记 WARN；**漂移**才是 FAIL。
