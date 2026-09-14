# 内容绑定批准记录（approve）
> ⛔ 操作指令：阅读即执行——本文含可直接执行的命令与判定，勿当资料阅读。
> 最后更新：2026-09-14

## 是什么

把「有人批准了」从散文变成**内容绑定、可重放**的记录：`protocol/approvals/*.json`
（`subject` + `subject_digest` + `approved_by` + `approved_at` + `note`）。
**被批准对象一改，记录立刻失效**——批准不是永久通行证。

## 怎么用

```bash
python scripts/nf.py approve <路径> --by <批准人> --note "…"   # 写记录
python scripts/nf.py approve --verify                          # 校验（对象改动即 FAIL）
python scripts/nf.py approve --list                            # 列记录（含失效标记）
```

## 边界

- 只判「声明是否在场、是否仍与对象内容绑定」，**不判内容质量**。
- NF 为单人治理：不存在 MCOP 意义上的"拒绝自批准"——批准人字段是**可追溯标识**，不是权限系统。
