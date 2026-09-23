<!-- nf-asset: key="STANDARDS_ANCHORS" version="1.0" status="active" -->
# 权威锚表 · AI+金融投研与风控

> 用途：本域 12 条细分各自的**外部权威锚**（规范 / 论文 / 参考实现）与**可达性实证**。外部锚只作口径与机制参照，**不作品质背书**（STRATEGY §3.2/§3.3）。
> 资产键：`STANDARDS_ANCHORS`｜实测日期：2026-09-22（本机 GET，HTTP 状态见下表；不可达如实记 `✗`，不假装可达）。

## 1. 锚表

| 条目键 | 锚类型 | URL | 可达性 | 可扩展标准（绑定） |
|---|---|---|---|---|
| `D04-01` | spec | https://www.cfainstitute.org/en/ethics-standards/codes/gips-standards | ✓ 200 | `gips` GIPS 绩效标准（CFA Institute；域码 D04 专属绑定（轮换 0）） |
| `D04-02` | spec | https://www.cfainstitute.org/en/ethics-standards/codes/gips-standards | ✓ 200 | `gips` GIPS 绩效标准（CFA Institute；域码 D04 专属绑定（轮换 0）） |
| `D04-03` | spec | https://www.cfainstitute.org/en/ethics-standards/codes/gips-standards | ✓ 200 | `gips` GIPS 绩效标准（CFA Institute；域码 D04 专属绑定（轮换 0）） |
| `D04-04` | spec | https://www.cfainstitute.org/en/ethics-standards/codes/gips-standards | ✓ 200 | `gips` GIPS 绩效标准（CFA Institute；域码 D04 专属绑定（轮换 0）） |
| `D04-05` | spec | https://www.cfainstitute.org/en/ethics-standards/codes/gips-standards | ✓ 200 | `cncf-cloudevents` CloudEvents 1.0（CNCF；关键词「事件|消息|通道」命中） |
| `D04-06` | spec | https://www.cfainstitute.org/en/ethics-standards/codes/gips-standards | ✓ 200 | `gips` GIPS 绩效标准（CFA Institute；关键词「金融|投研|风控|保险|绩效」命中） |
| `D04-07` | spec | https://www.cfainstitute.org/en/ethics-standards/codes/gips-standards | ✓ 200 | `gips` GIPS 绩效标准（CFA Institute；域码 D04 专属绑定（轮换 0）） |
| `D04-08` | spec | https://www.cfainstitute.org/en/ethics-standards/codes/gips-standards | ✓ 200 | `gdpr` GDPR（EU；关键词「隐私|个人信息|去标识|合规|监管」命中） |
| `D04-09` | spec | https://www.cfainstitute.org/en/ethics-standards/codes/gips-standards | ✓ 200 | `gdpr` GDPR（EU；关键词「隐私|个人信息|去标识|合规|监管」命中） |
| `D04-10` | spec | https://www.cfainstitute.org/en/ethics-standards/codes/gips-standards | ✓ 200 | `gips` GIPS 绩效标准（CFA Institute；关键词「金融|投研|风控|保险|绩效」命中） |
| `D04-11` | spec | https://www.cfainstitute.org/en/ethics-standards/codes/gips-standards | ✓ 200 | `gips` GIPS 绩效标准（CFA Institute；域码 D04 专属绑定（轮换 0）） |
| `D04-12` | spec | https://www.cfainstitute.org/en/ethics-standards/codes/gips-standards | ✓ 200 | `gips` GIPS 绩效标准（CFA Institute；域码 D04 专属绑定（轮换 0）） |

## 2. 使用边界

- 锚用于**口径复核**（该细分的通行定义/评测口径从何而来），不表示 NF 复制了外部文本；本包正文自撰。
- 锚不可达时按不可达记档，不影响本包口径面的机检（判据落在本包 schema 与度量族）。
- 锚版本漂移（规范改版）由维护者按需复核；本表不做自动追踪。
