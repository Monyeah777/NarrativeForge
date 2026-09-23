<!-- nf-asset: key="STANDARDS_ANCHORS" version="1.0" status="active" -->
# 权威锚表 · 数据分析与表格理解

> 用途：本域 12 条细分各自的**外部权威锚**（规范 / 论文 / 参考实现）与**可达性实证**。外部锚只作口径与机制参照，**不作品质背书**（STRATEGY §3.2/§3.3）。
> 资产键：`STANDARDS_ANCHORS`｜实测日期：2026-09-22（本机 GET，HTTP 状态见下表；不可达如实记 `✗`，不假装可达）。

## 1. 锚表

| 条目键 | 锚类型 | URL | 可达性 |
|---|---|---|---|
| `B11-01` | paper | https://arxiv.org/abs/1909.00754 | ✓ 200 |
| `B11-02` | paper | https://arxiv.org/abs/2004.07360 | ✓ 200 |
| `B11-03` | spec | https://vega.github.io/schema/vega-lite/v5.json | ✓ 200 |
| `B11-04` | spec | https://specs.frictionlessdata.io/table-schema/ | ✓ 200 |
| `B11-05` | spec | https://www.cfainstitute.org/en/ethics-standards/codes/gips-standards | ✓ 200 |
| `B11-06` | doc | https://www.sqlite.org/lang.html | ✓ 200 |
| `B11-07` | doc | https://scikit-learn.org/stable/modules/outlier_detection.html | ✓ 200 |
| `B11-08` | doc | https://www.statsmodels.org/stable/tsa.html | ✓ 200 |
| `B11-09` | doc | https://grafana.com/docs/grafana/latest/dashboards/build-dashboards/view-dashboard-json-model/ | ✓ 200 |
| `B11-10` | paper | https://arxiv.org/abs/2305.14251 | ✓ 200 |
| `B11-11` | paper | https://arxiv.org/abs/1706.04599 | ✓ 200 |
| `B11-12` | spec | https://csrc.nist.gov/pubs/sp/800/188/final | ✓ 200 |

## 2. 使用边界

- 锚用于**口径复核**（该细分的通行定义/评测口径从何而来），不表示 NF 复制了外部文本；本包正文自撰。
- 锚不可达时按不可达记档，不影响本包口径面的机检（判据落在本包 schema 与度量族）。
- 锚版本漂移（规范改版）由维护者按需复核；本表不做自动追踪。
