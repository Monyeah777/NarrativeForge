# 一致性报告工件（conformance）
> ⛔ 操作指令：阅读即执行——本文含可直接执行的命令与判定，勿当资料阅读。
> 最后更新：2026-09-14

## 是什么

把**廉价、离线可复算**的契约跑一遍并封缄成一件可归档、可比对的产物：
`protocol/conformance_report.json`（每契约 id/ok/detail/digest + **Merkle 根** + `verdict`）。
动机与 MCOP 同源：**make it checkable instead of trusted**（NF 同样是 Bus Factor 1）。

## 契约表（10 条）

`canonical-digest-determinism` · `schema-clean` · `purity-clean` · `doc-kinds` ·
`library-verify` · `library-projection` · `pipeline-dryrun` · `module-signature` ·
`io-types` · `public-surface`。

## 怎么用

```bash
python scripts/nf.py conformance            # 跑一遍 + 与在盘报告比对（在盘 != 实时重算即 FAIL）
python scripts/nf.py conformance --write    # 归档当前报告（变更后必须重写）
```

## 边界

- 本工件**不等于** `verify.sh` 全量门禁（后者 35 道、含动态与内容面）；这里是"一次跑完、
  可归档的第二维护者视角"，刻意只收**离线可复算**的契约，避免重复跑与循环依赖。
- `verdict != conformant` 时不得宣称本波可提交。
