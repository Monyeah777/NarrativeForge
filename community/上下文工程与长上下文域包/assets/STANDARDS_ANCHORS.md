<!-- nf-asset: key="STANDARDS_ANCHORS" version="1.0" status="active" -->
# 权威锚表 · 上下文工程与长上下文

> 用途：本域 12 条细分各自的**外部权威锚**（规范 / 论文 / 参考实现）与**可达性实证**。外部锚只作口径与机制参照，**不作品质背书**（STRATEGY §3.2/§3.3）。
> 资产键：`STANDARDS_ANCHORS`｜实测日期：2026-09-22（本机 GET，HTTP 状态见下表；不可达如实记 `✗`，不假装可达）。

## 1. 锚表

| 条目键 | 锚类型 | URL | 可达性 | 可扩展标准（绑定） |
|---|---|---|---|---|
| `C12-01` | paper | https://arxiv.org/abs/2307.03172 | ✓ 200 | `gfm` GFM 扩展（GitHub；关键词「缓存|分块|上下文」命中） |
| `C12-02` | paper | https://arxiv.org/abs/2307.03172 | ✓ 200 | `cncf-otel-semconv` 语义约定（可扩展注册表）（OpenTelemetry；C 段默认绑定（轮换 0）） |
| `C12-03` | paper | https://arxiv.org/abs/2307.03172 | ✓ 200 | `frictionless-package` Data Package（Frictionless；关键词「检索|向量|嵌入|召回」命中） |
| `C12-04` | paper | https://arxiv.org/abs/2307.03172 | ✓ 200 | `gfm` GFM 扩展（GitHub；关键词「缓存|分块|上下文」命中） |
| `C12-05` | paper | https://arxiv.org/abs/2307.03172 | ✓ 200 | `commonmark` CommonMark 0.31.2（CommonMark；关键词「提示|指令|模板」命中） |
| `C12-06` | paper | https://arxiv.org/abs/2307.03172 | ✓ 200 | `gfm` GFM 扩展（GitHub；关键词「缓存|分块|上下文」命中） |
| `C12-07` | paper | https://arxiv.org/abs/2307.03172 | ✓ 200 | `cncf-otel-semconv` 语义约定（可扩展注册表）（OpenTelemetry；C 段默认绑定（轮换 0）） |
| `C12-08` | paper | https://arxiv.org/abs/2307.03172 | ✓ 200 | `cncf-otel-semconv` 语义约定（可扩展注册表）（OpenTelemetry；C 段默认绑定（轮换 0）） |
| `C12-09` | paper | https://arxiv.org/abs/2307.03172 | ✓ 200 | `w3c-epub33` EPUB 3.3（W3C；关键词「文档|出版|排版|校对」命中） |
| `C12-10` | paper | https://arxiv.org/abs/2307.03172 | ✓ 200 | `w3c-epub33` EPUB 3.3（W3C；关键词「文档|出版|排版|校对」命中） |
| `C12-11` | paper | https://arxiv.org/abs/2307.03172 | ✓ 200 | `cncf-otel-semconv` 语义约定（可扩展注册表）（OpenTelemetry；C 段默认绑定（轮换 0）） |
| `C12-12` | paper | https://arxiv.org/abs/2307.03172 | ✓ 200 | `cncf-otel-semconv` 语义约定（可扩展注册表）（OpenTelemetry；关键词「可观测|遥测|监控|日志|成本|可靠性」命中） |

## 2. 使用边界

- 锚用于**口径复核**（该细分的通行定义/评测口径从何而来），不表示 NF 复制了外部文本；本包正文自撰。
- 锚不可达时按不可达记档，不影响本包口径面的机检（判据落在本包 schema 与度量族）。
- 锚版本漂移（规范改版）由维护者按需复核；本表不做自动追踪。
