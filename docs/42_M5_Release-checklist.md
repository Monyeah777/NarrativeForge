# 42 M5.6 · Release Checklist（tag 前逐项核验 · 随下个 tag 首用）

> 模板：tag vX.Y.Z 前逐项打勾；任何一项未过 = 不发布。

- [ ] **变更全齐**：CHANGELOG 归档（[Unreleased] 内容迁至版本段并清空）+ VERSION-MATRIX 同步（版本×方案×能力行）。
- [ ] **audit 建档在**：docs_audit-<N>-vX.Y.md verdict 通过（含五维自评段）。
- [ ] **verify 全绿**：`bash verify.sh`（check1-32 PASS=51，v2.22）0 WARN 0 FAIL。
- [ ] **覆盖率数字公示**：`bash scripts/coverage_summary.sh`（core ≥80%）。
- [ ] **判级器词表核验**：06 §11 无新增未定义强度词（必须/禁止/应/可之外）。
- [ ] **错误信息审计零缺失**：check27 R4 绿。
- [ ] **文档卫生**：doc_hygiene 标识/last-updated 常驻绿（指令类 100% + 零过期）。
- [ ] **golden master 冻结**：`bash scripts/release_freeze.sh vX.Y.Z` 产出产物快照 + nf-sig 指纹（见下）。
- [ ] **双端同步**：README 版本块 ✅ 已发布 + ROADMAP 状态行归位。
- [ ] **端壳线确认**：无端壳待办残留（L3 端壳线已永久退役，2026-09-09 作者裁决；见 docs/L3_FROZEN.md）。

## Golden Master 冻结（M5.6 + 批 C #5）

tag 点把关键产物做成可复现存档：

```bash
bash scripts/release_freeze.sh vX.Y.Z
# 产物 = .release-frozen/<tag>/sha256.manifest（01/02/06/07 + desktop/src/core/*.py +
# verify.sh + nf sig --verify 全量指纹），供日后回归对照（tag 点产物不漂移）。
```
