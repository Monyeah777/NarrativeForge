<!-- nf-asset: key="STANDARDS_ANCHORS" version="1.0" status="active" -->
# 权威锚表 · 代码生成与补全

> 用途：本域 12 条细分各自的**外部权威锚**（规范 / 论文 / 参考实现）与**可达性实证**。外部锚只作口径与机制参照，**不作品质背书**（STRATEGY §3.2/§3.3）。
> 资产键：`STANDARDS_ANCHORS`｜实测日期：2026-09-22（本机 GET，HTTP 状态见下表；不可达如实记 `✗`，不假装可达）。

## 1. 锚表

| 条目键 | 锚类型 | URL | 可达性 |
|---|---|---|---|
| `B08-01` | paper | https://arxiv.org/abs/2108.07732 | ✓ 200 |
| `B08-02` | paper | https://arxiv.org/abs/2306.03091 | ✓ 200 |
| `B08-03` | spec | https://peps.python.org/pep-0257/ | ✓ 200 |
| `B08-04` | paper | https://arxiv.org/abs/2006.03511 | ✓ 200 |
| `B08-05` | doc | https://docs.python.org/3/library/re.html | ✓ 200 |
| `B08-06` | spec | https://spec.openapis.org/oas/v3.1.0 | ✓ 200 |
| `B08-07` | doc | https://developer.hashicorp.com/terraform/language | ✓ 200 |
| `B08-08` | spec | https://peps.python.org/pep-0008/ | ✓ 200 |
| `B08-09` | paper | https://arxiv.org/abs/2310.06770 | ✓ 200 |
| `B08-10` | spec | https://spdx.org/licenses/ | ✓ 200 |
| `B08-11` | spec | https://osv.dev/ | ✓ 200 |
| `B08-12` | doc | https://microsoft.github.io/language-server-protocol/ | ✓ 200 |

## 2. 使用边界

- 锚用于**口径复核**（该细分的通行定义/评测口径从何而来），不表示 NF 复制了外部文本；本包正文自撰。
- 锚不可达时按不可达记档，不影响本包口径面的机检（判据落在本包 schema 与度量族）。
- 锚版本漂移（规范改版）由维护者按需复核；本表不做自动追踪。
