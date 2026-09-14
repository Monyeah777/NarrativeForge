---
id: single-source-truth
name: 真源 + 投影，禁止双写
status: active
scope:
  - 协议层
  - 资产层
applies_to:
  - library/INDEX.md
  - library/ALIAS.md
  - patterns/INDEX.md
  - protocol/conformance_report.json
  - protocol/RECEIPTS.json
rules:
  - 每份数据只有一个真源（frontmatter / registry.json / 契约声明），其余形态一律由脚本重生成
  - 生成区必须用显式标记包裹（BEGIN/END GENERATED），人工区不受影响
  - 门禁断言「在盘投影 == 实时重算」——不一致即 FAIL，不允许手工修表
evidence:
  - check34
  - check35
  - desktop/src/core/library.py
---

## 为什么

双写必然漂移：人改了一处、忘了另一处，两份"真相"开始各说各话。NF 的 I5（真相唯一）在各层
落地的方式就是——**真源 + 投影 + 重算断言**。

## 怎么用

```bash
python scripts/nf.py library reindex      # 真源(frontmatter) → INDEX/ALIAS 投影
python scripts/nf.py patterns reindex     # 真源(PATTERN.md) → patterns/INDEX 投影
python scripts/nf.py conformance --write  # 真源(契约) → 报告工件
```

## 反例

直接手改 `library/INDEX.md` 的生成区、或手改 `patterns/INDEX.md` 的表格——下一次重算即被覆盖，
且门禁会先报"投影不一致"。
