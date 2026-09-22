<!-- nf-asset: key="STANDARDS_ANCHORS" version="1.0" status="active" -->
# 权威锚表 · 分类与情感分析

> 用途：本域 12 条细分各自的**外部权威锚**（规范 / 论文 / 参考实现）与**可达性实证**。外部锚只作口径与机制参照，**不作品质背书**（STRATEGY §3.2/§3.3）。
> 资产键：`STANDARDS_ANCHORS`｜实测日期：2026-09-22（本机 GET，HTTP 状态见下表；不可达如实记 `✗`，不假装可达）。

## 1. 锚表

| 条目键 | 锚类型 | URL | 可达性 |
|---|---|---|---|
| `B04-01` | repo | https://pypi.org/project/Rasa/ | ✓ 200 |
| `B04-02` | paper | https://arxiv.org/abs/1509.01626 | ✓ 200 |
| `B04-03` | repo | https://pypi.org/project/textblob/ | ✓ 200 |
| `B04-04` | paper | https://arxiv.org/abs/2005.00547 | ✓ 200 |
| `B04-05` | paper | https://aclanthology.org/S16-1003/ | ✓ 200 |
| `B04-06` | doc | https://www.perspectiveapi.com/ | ✓ 200 |
| `B04-07` | repo | https://pypi.org/project/vaderSentiment/ | ✓ 200 |
| `B04-08` | paper | https://arxiv.org/abs/2209.11055 | ✓ 200 |
| `B04-09` | repo | https://pypi.org/project/scikit-multilearn/ | ✓ 200 |
| `B04-10` | paper | https://arxiv.org/abs/1706.04599 | ✓ 200 |
| `B04-11` | doc | https://scikit-learn.org/stable/modules/generated/sklearn.metrics.cohen_kappa_score.html | ✓ 200 |
| `B04-12` | doc | https://scikit-learn.org/stable/modules/model_evaluation.html | ✓ 200 |

## 2. 使用边界

- 锚用于**口径复核**（该细分的通行定义/评测口径从何而来），不表示 NF 复制了外部文本；本包正文自撰。
- 锚不可达时按不可达记档，不影响本包口径面的机检（判据落在本包 schema 与度量族）。
- 锚版本漂移（规范改版）由维护者按需复核；本表不做自动追踪。
