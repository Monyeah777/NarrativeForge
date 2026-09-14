# 执行结果跑分台（bench）
> ⛔ 操作指令：阅读即执行——本文含可直接执行的命令与判定，勿当资料阅读。
> 最后更新：2026-09-14

## 是什么

把「任意 AI 按 NF 协议产出的成品」丢进用例，做**五维确定性评分**并留档，支持多跑/多模型比对
（机制借鉴 ACP 的 benchmark suite）。它不做质量宣称——分数是**相对可比量**。

维度：`structure`（八段骨架）· `traceability`（编号真值/无编造）· `closure`（事件闭合自陈）·
`prose`（正文 AI 味）· `selfcheck`（自检清单完整度）。前两维复用 `assemble_plan.check`（即
`nf assemble --check` 的同一引擎），第三维用样本自陈，第四维用 `prose_lint`。

## 怎么用

```bash
python scripts/nf.py bench run --case desktop/tests/fixtures/benchmark/suite/p03-western-cross \
    --artifact <产物.md> --model <模型名> --out runs/model-a.json
python scripts/nf.py bench compare runs/*.json
python scripts/nf.py bench report runs/*.json
```

## 边界

- 只跑**离线确定性**判据，不调模型；判据取用例 `expected`（`min_total` 总分下限 + `min_segments` 八段骨架下限，任一不达即判 `fail`——声明即判据）。
- 跑分是"外部实测的容器"（E1/E2/Y5 回填时把产物丢进来即可比对），**不替代** verify 门禁。
