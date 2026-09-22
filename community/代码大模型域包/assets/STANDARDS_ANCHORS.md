<!-- nf-asset: key="STANDARDS_ANCHORS" version="1.0" status="active" -->
# 权威锚表 · 代码大模型

> 用途：本域 12 条细分各自的**外部权威锚**（规范 / 论文 / 参考实现）与**可达性实证**。外部锚只作口径与机制参照，**不作品质背书**（STRATEGY §3.2/§3.3）。
> 资产键：`STANDARDS_ANCHORS`｜实测日期：2026-09-22（本机 GET，HTTP 状态见下表；不可达如实记 `✗`，不假装可达）。

## 1. 锚表

| 条目键 | 锚类型 | URL | 可达性 |
|---|---|---|---|
| `A09-01` | paper | https://arxiv.org/abs/2107.03374 | ✓ 200 |
| `A09-02` | paper | https://arxiv.org/abs/2303.12570 | ✓ 200 |
| `A09-03` | paper | https://arxiv.org/abs/2308.02312 | ✓ 200 |
| `A09-04` | paper | https://arxiv.org/abs/2109.00859 | ✓ 200 |
| `A09-05` | spec | https://cwe.mitre.org/ | ✓ 200 |
| `A09-06` | paper | https://arxiv.org/abs/2305.00418 | ✓ 200 |
| `A09-07` | paper | https://arxiv.org/abs/1809.08887 | ✓ 200 |
| `A09-08` | doc | https://www.shellcheck.net/ | ✓ 200 |
| `A09-09` | doc | https://refactoring.com/catalog/ | ✓ 200 |
| `A09-10` | paper | https://arxiv.org/abs/2102.04664 | ✓ 200 |
| `A09-11` | paper | https://arxiv.org/abs/2107.03374 | ✓ 200 |
| `A09-12` | spec | https://owasp.org/www-project-top-10-for-large-language-model-applications/ | ✓ 200 |

## 2. 使用边界

- 锚用于**口径复核**（该细分的通行定义/评测口径从何而来），不表示 NF 复制了外部文本；本包正文自撰。
- 锚不可达时按不可达记档，不影响本包口径面的机检（判据落在本包 schema 与度量族）。
- 锚版本漂移（规范改版）由维护者按需复核；本表不做自动追踪。
