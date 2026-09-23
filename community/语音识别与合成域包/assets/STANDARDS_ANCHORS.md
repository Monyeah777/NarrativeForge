<!-- nf-asset: key="STANDARDS_ANCHORS" version="1.0" status="active" -->
# 权威锚表 · 语音识别与合成

> 用途：本域 12 条细分各自的**外部权威锚**（规范 / 论文 / 参考实现）与**可达性实证**。外部锚只作口径与机制参照，**不作品质背书**（STRATEGY §3.2/§3.3）。
> 资产键：`STANDARDS_ANCHORS`｜实测日期：2026-09-22（本机 GET，HTTP 状态见下表；不可达如实记 `✗`，不假装可达）。

## 1. 锚表

| 条目键 | 锚类型 | URL | 可达性 | 可扩展标准（绑定） |
|---|---|---|---|---|
| `A04-01` | paper | https://arxiv.org/abs/1512.02595 | ✓ 200 | `w3c-webaudio` Web Audio API（W3C；关键词「音频|语音|声学|音乐|歌声」命中） |
| `A04-02` | repo | https://pypi.org/project/webrtcvad/ | ✓ 200 | `w3c-webaudio` Web Audio API（W3C；关键词「音频|语音|声学|音乐|歌声」命中） |
| `A04-03` | paper | https://arxiv.org/abs/2003.12687 | ✓ 200 | `ietf-json-schema` JSON Schema 2020-12（IETF/JSON Schema；A 段默认绑定（轮换 0）） |
| `A04-04` | dataset | https://commonvoice.mozilla.org/ | ✓ 200 | `ietf-json-schema` JSON Schema 2020-12（IETF/JSON Schema；A 段默认绑定（轮换 0）） |
| `A04-05` | repo | https://pypi.org/project/noisereduce/ | ✓ 200 | `ietf-json-schema` JSON Schema 2020-12（IETF/JSON Schema；A 段默认绑定（轮换 0）） |
| `A04-06` | paper | https://arxiv.org/abs/2010.10759 | ✓ 200 | `ietf-json-schema` JSON Schema 2020-12（IETF/JSON Schema；A 段默认绑定（轮换 0）） |
| `A04-07` | paper | https://arxiv.org/abs/1712.05884 | ✓ 200 | `onnx` ONNX（opset 扩展）（Linux Foundation；关键词「模型|推理|量化」命中） |
| `A04-08` | paper | https://arxiv.org/abs/1802.06006 | ✓ 200 | `ietf-json-schema` JSON Schema 2020-12（IETF/JSON Schema；A 段默认绑定（轮换 0）） |
| `A04-09` | paper | https://arxiv.org/abs/1904.06022 | ✓ 200 | `ietf-json-schema` JSON Schema 2020-12（IETF/JSON Schema；A 段默认绑定（轮换 0）） |
| `A04-10` | paper | https://arxiv.org/abs/2212.04356 | ✓ 200 | `ietf-json-schema` JSON Schema 2020-12（IETF/JSON Schema；A 段默认绑定（轮换 0）） |
| `A04-11` | paper | https://arxiv.org/abs/2104.01378 | ✓ 200 | `mlcommons-bench` MLPerf 基准（可扩展场景）（MLCommons；关键词「评测|基准|排行榜|跑分」命中） |
| `A04-12` | paper | https://arxiv.org/abs/2303.00747 | ✓ 200 | `oci-image` 镜像清单（OCI；关键词「视频|剪辑|字幕」命中） |

## 2. 使用边界

- 锚用于**口径复核**（该细分的通行定义/评测口径从何而来），不表示 NF 复制了外部文本；本包正文自撰。
- 锚不可达时按不可达记档，不影响本包口径面的机检（判据落在本包 schema 与度量族）。
- 锚版本漂移（规范改版）由维护者按需复核；本表不做自动追踪。
