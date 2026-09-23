<!-- nf-asset: key="STANDARDS_ANCHORS" version="1.0" status="active" -->
# 权威锚表 · 提示工程与指令设计

> 用途：本域 12 条细分各自的**外部权威锚**（规范 / 论文 / 参考实现）与**可达性实证**。外部锚只作口径与机制参照，**不作品质背书**（STRATEGY §3.2/§3.3）。
> 资产键：`STANDARDS_ANCHORS`｜实测日期：2026-09-22（本机 GET，HTTP 状态见下表；不可达如实记 `✗`，不假装可达）。

## 1. 锚表

| 条目键 | 锚类型 | URL | 可达性 | 可扩展标准（绑定） |
|---|---|---|---|---|
| `E01-01` | spec | https://spec.commonmark.org/0.31.2/ | ✓ 200 | `commonmark` CommonMark 0.31.2（CommonMark；关键词「提示|指令|模板」命中） |
| `E01-02` | spec | https://spec.commonmark.org/0.31.2/ | ✓ 200 | `commonmark` CommonMark 0.31.2（CommonMark；关键词「提示|指令|模板」命中） |
| `E01-03` | spec | https://spec.commonmark.org/0.31.2/ | ✓ 200 | `commonmark` CommonMark 0.31.2（CommonMark；E 段默认绑定（轮换 0）） |
| `E01-04` | spec | https://spec.commonmark.org/0.31.2/ | ✓ 200 | `commonmark` CommonMark 0.31.2（CommonMark；E 段默认绑定（轮换 0）） |
| `E01-05` | spec | https://spec.commonmark.org/0.31.2/ | ✓ 200 | `ietf-json-schema` JSON Schema 2020-12（IETF/JSON Schema；关键词「约束|校验|schema|形状|契约」命中） |
| `E01-06` | spec | https://spec.commonmark.org/0.31.2/ | ✓ 200 | `a2a` A2A 协议（Linux Foundation；关键词「多智能体|协同|编排」命中） |
| `E01-07` | spec | https://spec.commonmark.org/0.31.2/ | ✓ 200 | `gfm` GFM 扩展（GitHub；关键词「缓存|分块|上下文」命中） |
| `E01-08` | spec | https://spec.commonmark.org/0.31.2/ | ✓ 200 | `commonmark` CommonMark 0.31.2（CommonMark；关键词「提示|指令|模板」命中） |
| `E01-09` | spec | https://spec.commonmark.org/0.31.2/ | ✓ 200 | `commonmark` CommonMark 0.31.2（CommonMark；关键词「提示|指令|模板」命中） |
| `E01-10` | spec | https://spec.commonmark.org/0.31.2/ | ✓ 200 | `onnx` ONNX（opset 扩展）（Linux Foundation；关键词「模型|推理|量化」命中） |
| `E01-11` | spec | https://spec.commonmark.org/0.31.2/ | ✓ 200 | `mlcommons-bench` MLPerf 基准（可扩展场景）（MLCommons；关键词「评测|基准|排行榜|跑分」命中） |
| `E01-12` | spec | https://spec.commonmark.org/0.31.2/ | ✓ 200 | `commonmark` CommonMark 0.31.2（CommonMark；E 段默认绑定（轮换 0）） |

## 2. 使用边界

- 锚用于**口径复核**（该细分的通行定义/评测口径从何而来），不表示 NF 复制了外部文本；本包正文自撰。
- 锚不可达时按不可达记档，不影响本包口径面的机检（判据落在本包 schema 与度量族）。
- 锚版本漂移（规范改版）由维护者按需复核；本表不做自动追踪。
