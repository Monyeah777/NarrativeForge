<!-- nf-asset: key="STANDARDS_ANCHORS" version="1.0" status="active" -->
# 权威锚表 · 音频与音乐生成

> 用途：本域 12 条细分各自的**外部权威锚**（规范 / 论文 / 参考实现）与**可达性实证**。外部锚只作口径与机制参照，**不作品质背书**（STRATEGY §3.2/§3.3）。
> 资产键：`STANDARDS_ANCHORS`｜实测日期：2026-09-22（本机 GET，HTTP 状态见下表；不可达如实记 `✗`，不假装可达）。

## 1. 锚表

| 条目键 | 锚类型 | URL | 可达性 | 可扩展标准（绑定） |
|---|---|---|---|---|
| `A05-01` | paper | https://arxiv.org/abs/2306.05284 | ✓ 200 | `w3c-webaudio` Web Audio API（W3C；关键词「音频|语音|声学|音乐|歌声」命中） |
| `A05-02` | repo | https://pypi.org/project/spleeter/ | ✓ 200 | `ietf-json-schema` JSON Schema 2020-12（IETF/JSON Schema；A 段默认绑定（轮换 0）） |
| `A05-03` | spec | https://www.w3.org/2021/06/musicxml40/ | ✓ 200 | `ietf-json-schema` JSON Schema 2020-12（IETF/JSON Schema；A 段默认绑定（轮换 0）） |
| `A05-04` | repo | https://pypi.org/project/essentia/ | ✓ 200 | `ietf-json-schema` JSON Schema 2020-12（IETF/JSON Schema；A 段默认绑定（轮换 0）） |
| `A05-05` | repo | https://pypi.org/project/demucs/ | ✓ 200 | `w3c-webaudio` Web Audio API（W3C；关键词「音频|语音|声学|音乐|歌声」命中） |
| `A05-06` | spec | https://dcase.community/ | ✓ 200 | `cncf-cloudevents` CloudEvents 1.0（CNCF；关键词「事件|消息|通道」命中） |
| `A05-07` | spec | https://www.w3.org/TR/webaudio/ | ✓ 200 | `opengeospatial` OGC 标准（含 GeoJSON/3D Tiles）（OGC；关键词「地理|遥感|地图|空间|三维|点云」命中） |
| `A05-08` | paper | https://arxiv.org/abs/2209.15352 | ✓ 200 | `ietf-json-schema` JSON Schema 2020-12（IETF/JSON Schema；A 段默认绑定（轮换 0）） |
| `A05-09` | spec | https://creativecommons.org/licenses/ | ✓ 200 | `creativecommons` 许可与权利表达（Creative Commons；关键词「许可|版权|知识产权|授权」命中） |
| `A05-10` | repo | https://pypi.org/project/recbole/ | ✓ 200 | `w3c-webaudio` Web Audio API（W3C；关键词「音频|语音|声学|音乐|歌声」命中） |
| `A05-11` | paper | https://arxiv.org/abs/2105.02446 | ✓ 200 | `w3c-webaudio` Web Audio API（W3C；关键词「音频|语音|声学|音乐|歌声」命中） |
| `A05-12` | spec | https://www.itu.int/rec/T-REC-P.862 | ✓ 200 | `mlcommons-bench` MLPerf 基准（可扩展场景）（MLCommons；关键词「评测|基准|排行榜|跑分」命中） |

## 2. 使用边界

- 锚用于**口径复核**（该细分的通行定义/评测口径从何而来），不表示 NF 复制了外部文本；本包正文自撰。
- 锚不可达时按不可达记档，不影响本包口径面的机检（判据落在本包 schema 与度量族）。
- 锚版本漂移（规范改版）由维护者按需复核；本表不做自动追踪。
