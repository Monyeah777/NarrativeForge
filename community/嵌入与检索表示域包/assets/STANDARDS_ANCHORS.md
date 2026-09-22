<!-- nf-asset: key="STANDARDS_ANCHORS" version="1.0" status="active" -->
# 权威锚表 · 嵌入与检索表示

> 用途：本域 12 条细分各自的**外部权威锚**（规范 / 论文 / 参考实现）与**可达性实证**。外部锚只作口径与机制参照，**不作品质背书**（STRATEGY §3.2/§3.3）。
> 资产键：`STANDARDS_ANCHORS`｜实测日期：2026-09-22（本机 GET，HTTP 状态见下表；不可达如实记 `✗`，不假装可达）。

## 1. 锚表

| 条目键 | 锚类型 | URL | 可达性 |
|---|---|---|---|
| `A11-01` | paper | https://arxiv.org/abs/2212.03533 | ✓ 200 |
| `A11-02` | paper | https://arxiv.org/abs/2210.11934 | ✓ 200 |
| `A11-03` | paper | https://arxiv.org/abs/1908.10084 | ✓ 200 |
| `A11-04` | paper | https://arxiv.org/abs/1702.08734 | ✓ 200 |
| `A11-05` | doc | https://scikit-learn.org/stable/modules/metrics.html | ✓ 200 |
| `A11-06` | paper | https://arxiv.org/abs/2004.09813 | ✓ 200 |
| `A11-07` | paper | https://arxiv.org/abs/2112.07899 | ✓ 200 |
| `A11-08` | paper | https://arxiv.org/abs/2112.01488 | ✓ 200 |
| `A11-09` | paper | https://arxiv.org/abs/1603.09320 | ✓ 200 |
| `A11-10` | paper | https://arxiv.org/abs/2104.08663 | ✓ 200 |
| `A11-11` | paper | https://arxiv.org/abs/2107.06499 | ✓ 200 |
| `A11-12` | paper | https://arxiv.org/abs/2210.07316 | ✓ 200 |

## 2. 使用边界

- 锚用于**口径复核**（该细分的通行定义/评测口径从何而来），不表示 NF 复制了外部文本；本包正文自撰。
- 锚不可达时按不可达记档，不影响本包口径面的机检（判据落在本包 schema 与度量族）。
- 锚版本漂移（规范改版）由维护者按需复核；本表不做自动追踪。
