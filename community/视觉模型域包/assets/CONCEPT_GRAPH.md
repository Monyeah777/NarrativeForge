<!-- nf-asset: key="CONCEPT_GRAPH" version="1.0" status="active" -->
# 概念图 · 视觉模型（概念前置偏序）

> 用途：本域包的**前置闭包求值输入面**——把「视觉模型」这一域的 12 个细分概念声明成一张偏序图（DAG），供域内口径模块（视觉模型:M01）与收口模块（视觉模型:M02）消费。
> 资产键：`CONCEPT_GRAPH`｜形态：人读表（§2）/ 别名表（§3）/ 机器可读块（§4）三形态同源——**§4 围栏块是唯一机读真相**，§2/§3 由它导出。
> 覆盖：12 个包内概念 + 8 个**可扩展标准节点**（标准目录绑定）+ 1 个包外前置族（A03-00 领域通用前置）。
> 来源：本件正文自撰；每条细分的权威锚见资产 `DOMAIN_SPEC` 与 `STANDARDS_ANCHORS`（逐条可达性实证）。

## 1. 读法

- **概念**：一个可独立装载的知识单元（本域第 N 条细分）。
- **前置**：装载该概念之前必须先具备的概念（边方向「前置 → 后继」）。
- **层**：该概念在 NF 九层位中的合理驻留层（P00–P80），用于装配定位，不是执行顺序。
- **证据**：节点来源锚（见 §5 图例）；本图所有节点均挂外部可复核锚。

## 2. 条目键表（一概念一键，asset_get 寻址）

| 条目键 | 概念 | 层 | 直接前置 | 证据 |
|---|---|---|---|---|
| `A03-01` | 图像分类与主干网络 | P40 | — | a03-anchor |
| `A03-02` | 目标检测 | P60 | `A03-01` | a03-anchor |
| `A03-03` | 语义与实例分割 | P40 | `A03-01`、`A03-02` | a03-anchor |
| `A03-04` | 关键点与姿态估计 | P60 | `A03-03` | a03-anchor |
| `A03-05` | 深度估计与点云 | P40 | `A03-04` | a03-anchor |
| `A03-06` | 人脸识别与活体检测 | P60 | — | a03-anchor |
| `A03-07` | 图像检索与重识别 | P40 | `A03-02`、`A03-06` | a03-anchor |
| `A03-08` | 视频理解与动作识别 | P60 | — | a03-anchor |
| `A03-09` | 医学影像分析 | P40 | — | a03-anchor |
| `A03-10` | 工业缺陷检测 | P60 | — | a03-anchor |
| `A03-11` | 遥感与航拍解译 | P40 | `A03-09`、`A03-10` | a03-anchor |
| `A03-12` | 数据增强与预训练策略 | P60 | `A03-05` | a03-anchor |
| `STD-cwe` | 标准 · CWE 缺陷枚举（MITRE） | P80 | `A03-10` | std-catalog |
| `STD-dicom` | 标准 · DICOM 标准（DICOM） | P80 | `A03-09` | std-catalog |
| `STD-ietf-json-schema` | 标准 · JSON Schema 2020-12（IETF/JSON Schema） | P80 | `A03-04` | std-catalog |
| `STD-mlcommons-bench` | 标准 · MLPerf 基准（可扩展场景）（MLCommons） | P80 | `A03-02`、`A03-12` | std-catalog |
| `STD-oci-image` | 标准 · 镜像清单（OCI） | P80 | `A03-08` | std-catalog |
| `STD-onnx` | 标准 · ONNX（opset 扩展）（Linux Foundation） | P80 | `A03-03`、`A03-06` | std-catalog |
| `STD-opengeospatial` | 标准 · OGC 标准（含 GeoJSON/3D Tiles）（OGC） | P80 | `A03-05`、`A03-11` | std-catalog |
| `STD-w3c-svg2` | 标准 · SVG 2（W3C） | P80 | `A03-01`、`A03-07` | std-catalog |

## 3. 别名表（求值时 id 与别名等价）

| 别名 | 概念 id |
|---|---|
| `A03-图像分类与主干网络` | `A03-01` |
| `A03-目标检测` | `A03-02` |
| `A03-语义与实例分割` | `A03-03` |
| `A03-关键点与姿态估计` | `A03-04` |
| `A03-深度估计与点云` | `A03-05` |
| `A03-人脸识别与活体检测` | `A03-06` |
| `A03-图像检索与重识别` | `A03-07` |
| `A03-视频理解与动作识别` | `A03-08` |
| `A03-医学影像分析` | `A03-09` |
| `A03-工业缺陷检测` | `A03-10` |
| `A03-遥感与航拍解译` | `A03-11` |
| `A03-数据增强与预训练策略` | `A03-12` |
| `std-cwe` | `STD-cwe` |
| `std-dicom` | `STD-dicom` |
| `std-ietf-json-schema` | `STD-ietf-json-schema` |
| `std-mlcommons-bench` | `STD-mlcommons-bench` |
| `std-oci-image` | `STD-oci-image` |
| `std-onnx` | `STD-onnx` |
| `std-opengeospatial` | `STD-opengeospatial` |
| `std-w3c-svg2` | `STD-w3c-svg2` |

## 4. 机器可读块（唯一机读真相）

```yaml
concept_graph:
  version: "1.0"
  domain: "视觉模型"
  code: "A03"
  provenance_strength: "external"
  provenance_legend:
    a03-anchor: "域内权威锚（规范 / 论文 / 参考实现），逐条 URL 与可达性实证见资产 STANDARDS_ANCHORS（本波实测）"
    std-catalog: "可扩展标准目录条目（protocol/standards_catalog.json，本机可达性实测）"
  external_prereqs:
    - id: "A03-00"
      name: "领域通用前置族（数学/工程基础，包外）"
  branches:
    - id: "domain"
      name: "视觉模型 全域"
      nodes:
        - "A03-01"
        - "A03-02"
        - "A03-03"
        - "A03-04"
        - "A03-05"
        - "A03-06"
        - "A03-07"
        - "A03-08"
        - "A03-09"
        - "A03-10"
        - "A03-11"
        - "A03-12"
    - id: "standards"
      name: "可扩展标准（绑定）"
      nodes:
        - "STD-cwe"
        - "STD-dicom"
        - "STD-ietf-json-schema"
        - "STD-mlcommons-bench"
        - "STD-oci-image"
        - "STD-onnx"
        - "STD-opengeospatial"
        - "STD-w3c-svg2"
  nodes:
    - id: "A03-01"
      name: "图像分类与主干网络"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "a03-anchor"
    - id: "A03-02"
      name: "目标检测"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "A03-01"
      provenance:
        - "a03-anchor"
    - id: "A03-03"
      name: "语义与实例分割"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "A03-01"
        - "A03-02"
      provenance:
        - "a03-anchor"
    - id: "A03-04"
      name: "关键点与姿态估计"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "A03-03"
      provenance:
        - "a03-anchor"
    - id: "A03-05"
      name: "深度估计与点云"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "A03-04"
      provenance:
        - "a03-anchor"
    - id: "A03-06"
      name: "人脸识别与活体检测"
      layer: "P60"
      branch: "domain"
      prereqs: []
      provenance:
        - "a03-anchor"
    - id: "A03-07"
      name: "图像检索与重识别"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "A03-02"
        - "A03-06"
      provenance:
        - "a03-anchor"
    - id: "A03-08"
      name: "视频理解与动作识别"
      layer: "P60"
      branch: "domain"
      prereqs: []
      provenance:
        - "a03-anchor"
    - id: "A03-09"
      name: "医学影像分析"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "a03-anchor"
    - id: "A03-10"
      name: "工业缺陷检测"
      layer: "P60"
      branch: "domain"
      prereqs: []
      provenance:
        - "a03-anchor"
    - id: "A03-11"
      name: "遥感与航拍解译"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "A03-09"
        - "A03-10"
      provenance:
        - "a03-anchor"
    - id: "A03-12"
      name: "数据增强与预训练策略"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "A03-05"
      provenance:
        - "a03-anchor"
    - id: "STD-cwe"
      name: "标准 · CWE 缺陷枚举"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "A03-10"
      provenance:
        - "std-catalog"
    - id: "STD-dicom"
      name: "标准 · DICOM 标准"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "A03-09"
      provenance:
        - "std-catalog"
    - id: "STD-ietf-json-schema"
      name: "标准 · JSON Schema 2020-12"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "A03-04"
      provenance:
        - "std-catalog"
    - id: "STD-mlcommons-bench"
      name: "标准 · MLPerf 基准（可扩展场景）"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "A03-02"
        - "A03-12"
      provenance:
        - "std-catalog"
    - id: "STD-oci-image"
      name: "标准 · 镜像清单"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "A03-08"
      provenance:
        - "std-catalog"
    - id: "STD-onnx"
      name: "标准 · ONNX（opset 扩展）"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "A03-03"
        - "A03-06"
      provenance:
        - "std-catalog"
    - id: "STD-opengeospatial"
      name: "标准 · OGC 标准（含 GeoJSON/3D Tiles）"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "A03-05"
        - "A03-11"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-svg2"
      name: "标准 · SVG 2"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "A03-01"
        - "A03-07"
      provenance:
        - "std-catalog"
```

## 5. 证据与边界

- 每个节点的来源锚（外部规范 / 论文 / 参考实现）逐条登记于 `STANDARDS_ANCHORS`，本图 `provenance_strength = external`（全覆盖，可复核）。
- 图只声明**结构前置**（装载顺序），不声明掌握程度；边为「先具备 → 后展开」的域内常识序。
- 包外前置族（A03-00）不随包交付，装载方须自备领域基础。
