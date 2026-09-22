<!-- nf-asset: key="STANDARDS_ANCHORS" version="1.0" status="active" -->
# 权威锚表 · 具身智能与机器人

> 用途：本域 12 条细分各自的**外部权威锚**（规范 / 论文 / 参考实现）与**可达性实证**。外部锚只作口径与机制参照，**不作品质背书**（STRATEGY §3.2/§3.3）。
> 资产键：`STANDARDS_ANCHORS`｜实测日期：2026-09-22（本机 GET，HTTP 状态见下表；不可达如实记 `✗`，不假装可达）。

## 1. 锚表

| 条目键 | 锚类型 | URL | 可达性 |
|---|---|---|---|
| `A13-01` | doc | https://moveit.picknik.ai/ | ✓ 200 |
| `A13-02` | paper | https://arxiv.org/abs/1710.01330 | ✓ 200 |
| `A13-03` | paper | https://arxiv.org/abs/2212.06817 | ✓ 200 |
| `A13-04` | paper | https://arxiv.org/abs/1709.10087 | ✓ 200 |
| `A13-05` | paper | https://arxiv.org/abs/1703.06907 | ✓ 200 |
| `A13-06` | repo | https://pypi.org/project/filterpy/ | ✓ 200 |
| `A13-07` | paper | https://arxiv.org/abs/2204.01691 | ✓ 200 |
| `A13-08` | spec | https://eur-lex.europa.eu/eli/reg/2023/1230/oj | ✗ 202 |
| `A13-09` | doc | https://docs.nav2.org/ | ✓ 200 |
| `A13-10` | doc | https://docs.opencv.org/4.x/d9/d0c/group__calib3d.html | ✓ 200 |
| `A13-11` | paper | https://arxiv.org/abs/2303.04137 | ✓ 200 |
| `A13-12` | paper | https://arxiv.org/abs/2303.03378 | ✓ 200 |

## 2. 使用边界

- 锚用于**口径复核**（该细分的通行定义/评测口径从何而来），不表示 NF 复制了外部文本；本包正文自撰。
- 锚不可达时按不可达记档，不影响本包口径面的机检（判据落在本包 schema 与度量族）。
- 锚版本漂移（规范改版）由维护者按需复核；本表不做自动追踪。
