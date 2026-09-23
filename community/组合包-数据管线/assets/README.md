<!-- ai-index: borrow-only -->
# 借阅索引（本包无自有内容资产）

> 本组合包 `assets.count = 0`：不复制任何源包资产；下表是**借阅来源**清单，运行时经 `asset_get` 只读访问源包资产（`asset_readonly: true`）。

| 源包 | 借阅模块 | 源包资产键 |
|---|---|---|
| 合成数据生成域包 | 合成数据生成:M01、合成数据生成:M02 | 见源包 `assets/provenance.json` |
| 数据采集与清洗域包 | 数据采集与清洗:M01、数据采集与清洗:M02 | 见源包 `assets/provenance.json` |
| 评测基准与排行榜域包 | 评测基准与排行榜:M01、评测基准与排行榜:M02 | 见源包 `assets/provenance.json` |
| 预训练与继续预训练域包 | 预训练与继续预训练:M01、预训练与继续预训练:M02 | 见源包 `assets/provenance.json` |
