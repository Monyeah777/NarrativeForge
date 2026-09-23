<!-- nf-asset: key="STANDARDS_ANCHORS" version="1.0" status="active" -->
# 权威锚表 · 视觉模型

> 用途：本域 12 条细分各自的**外部权威锚**（规范 / 论文 / 参考实现）与**可达性实证**。外部锚只作口径与机制参照，**不作品质背书**（STRATEGY §3.2/§3.3）。
> 资产键：`STANDARDS_ANCHORS`｜实测日期：2026-09-22（本机 GET，HTTP 状态见下表；不可达如实记 `✗`，不假装可达）。

## 1. 锚表

| 条目键 | 锚类型 | URL | 可达性 | 可扩展标准（绑定） |
|---|---|---|---|---|
| `A03-01` | paper | https://arxiv.org/abs/1512.03385 | ✓ 200 | `w3c-svg2` SVG 2（W3C；关键词「图像|视觉|扩散|超分|抠图」命中） |
| `A03-02` | paper | https://arxiv.org/abs/1506.02640 | ✓ 200 | `ietf-json-schema` JSON Schema 2020-12（IETF/JSON Schema；A 段默认绑定（轮换 0）） |
| `A03-03` | paper | https://arxiv.org/abs/1703.06870 | ✓ 200 | `ietf-json-schema` JSON Schema 2020-12（IETF/JSON Schema；A 段默认绑定（轮换 0）） |
| `A03-04` | paper | https://arxiv.org/abs/1611.08050 | ✓ 200 | `ietf-json-schema` JSON Schema 2020-12（IETF/JSON Schema；A 段默认绑定（轮换 0）） |
| `A03-05` | paper | https://arxiv.org/abs/1907.03670 | ✓ 200 | `opengeospatial` OGC 标准（含 GeoJSON/3D Tiles）（OGC；关键词「地理|遥感|地图|空间|三维|点云」命中） |
| `A03-06` | paper | https://arxiv.org/abs/1503.03832 | ✓ 200 | `ietf-json-schema` JSON Schema 2020-12（IETF/JSON Schema；A 段默认绑定（轮换 0）） |
| `A03-07` | paper | https://arxiv.org/abs/2001.04193 | ✓ 200 | `w3c-svg2` SVG 2（W3C；关键词「图像|视觉|扩散|超分|抠图」命中） |
| `A03-08` | paper | https://arxiv.org/abs/1406.2199 | ✓ 200 | `oci-image` 镜像清单（OCI；关键词「视频|剪辑|字幕」命中） |
| `A03-09` | paper | https://arxiv.org/abs/1711.05225 | ✓ 200 | `dicom` DICOM 标准（DICOM；关键词「影像|放射」命中） |
| `A03-10` | paper | https://arxiv.org/abs/2106.08265 | ✓ 200 | `cwe` CWE 缺陷枚举（MITRE；关键词「漏洞|缺陷|弱点」命中） |
| `A03-11` | paper | https://arxiv.org/abs/1711.10398 | ✓ 200 | `opengeospatial` OGC 标准（含 GeoJSON/3D Tiles）（OGC；关键词「地理|遥感|地图|空间|三维|点云」命中） |
| `A03-12` | paper | https://arxiv.org/abs/1805.09501 | ✓ 200 | `mlcommons-bench` MLPerf 基准（可扩展场景）（MLCommons；关键词「训练|微调|对齐|蒸馏|偏好」命中） |

## 2. 使用边界

- 锚用于**口径复核**（该细分的通行定义/评测口径从何而来），不表示 NF 复制了外部文本；本包正文自撰。
- 锚不可达时按不可达记档，不影响本包口径面的机检（判据落在本包 schema 与度量族）。
- 锚版本漂移（规范改版）由维护者按需复核；本表不做自动追踪。
