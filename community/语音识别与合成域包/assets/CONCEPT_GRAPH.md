<!-- nf-asset: key="CONCEPT_GRAPH" version="1.0" status="active" -->
# 概念图 · 语音识别与合成（概念前置偏序）

> 用途：本域包的**前置闭包求值输入面**——把「语音识别与合成」这一域的 12 个细分概念声明成一张偏序图（DAG），供域内口径模块（语音识别与合成:M01）与收口模块（语音识别与合成:M02）消费。
> 资产键：`CONCEPT_GRAPH`｜形态：人读表（§2）/ 别名表（§3）/ 机器可读块（§4）三形态同源——**§4 围栏块是唯一机读真相**，§2/§3 由它导出。
> 覆盖：12 个包内概念 + 1 个包外前置族（A04-00 领域通用前置）。
> 来源：本件正文自撰；每条细分的权威锚见资产 `DOMAIN_SPEC` 与 `STANDARDS_ANCHORS`（逐条可达性实证）。

## 1. 读法

- **概念**：一个可独立装载的知识单元（本域第 N 条细分）。
- **前置**：装载该概念之前必须先具备的概念（边方向「前置 → 后继」）。
- **层**：该概念在 NF 九层位中的合理驻留层（P00–P80），用于装配定位，不是执行顺序。
- **证据**：节点来源锚（见 §5 图例）；本图所有节点均挂外部可复核锚。

## 2. 条目键表（一概念一键，asset_get 寻址）

| 条目键 | 概念 | 层 | 直接前置 | 证据 |
|---|---|---|---|---|
| `A04-01` | 端到端 ASR 声学建模 | P40 | `A04-02` | a04-anchor |
| `A04-02` | 语音活动检测与切分 | P60 | — | a04-anchor |
| `A04-03` | 说话人分离与识别 | P40 | — | a04-anchor |
| `A04-04` | 方言与口音适应 | P60 | `A04-01` | a04-anchor |
| `A04-05` | 噪声与远场鲁棒 | P40 | `A04-01` | a04-anchor |
| `A04-06` | 流式低延迟识别 | P60 | `A04-01` | a04-anchor |
| `A04-07` | TTS 声学模型与声码器 | P40 | — | a04-anchor |
| `A04-08` | 音色克隆与声音转换 | P60 | `A04-07` | a04-anchor |
| `A04-09` | 韵律与情感控制 | P40 | `A04-07` | a04-anchor |
| `A04-10` | 多语种混说 | P60 | `A04-03` | a04-anchor |
| `A04-11` | 语音评测与打分 | P40 | `A04-01`、`A04-09` | a04-anchor |
| `A04-12` | 字幕时间轴对齐 | P60 | `A04-06` | a04-anchor |

## 3. 别名表（求值时 id 与别名等价）

| 别名 | 概念 id |
|---|---|
| `A04-端到端-ASR-声学建模` | `A04-01` |
| `A04-语音活动检测与切分` | `A04-02` |
| `A04-说话人分离与识别` | `A04-03` |
| `A04-方言与口音适应` | `A04-04` |
| `A04-噪声与远场鲁棒` | `A04-05` |
| `A04-流式低延迟识别` | `A04-06` |
| `A04-TTS-声学模型与声码器` | `A04-07` |
| `A04-音色克隆与声音转换` | `A04-08` |
| `A04-韵律与情感控制` | `A04-09` |
| `A04-多语种混说` | `A04-10` |
| `A04-语音评测与打分` | `A04-11` |
| `A04-字幕时间轴对齐` | `A04-12` |

## 4. 机器可读块（唯一机读真相）

```yaml
concept_graph:
  version: "1.0"
  domain: "语音识别与合成"
  code: "A04"
  provenance_strength: "external"
  provenance_legend:
    a04-anchor: "域内权威锚（规范 / 论文 / 参考实现），逐条 URL 与可达性实证见资产 STANDARDS_ANCHORS（本波实测）"
  external_prereqs:
    - id: "A04-00"
      name: "领域通用前置族（数学/工程基础，包外）"
  branches:
    - id: "domain"
      name: "语音识别与合成 全域"
      nodes:
        - "A04-01"
        - "A04-02"
        - "A04-03"
        - "A04-04"
        - "A04-05"
        - "A04-06"
        - "A04-07"
        - "A04-08"
        - "A04-09"
        - "A04-10"
        - "A04-11"
        - "A04-12"
  nodes:
    - id: "A04-01"
      name: "端到端 ASR 声学建模"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "A04-02"
      provenance:
        - "a04-anchor"
    - id: "A04-02"
      name: "语音活动检测与切分"
      layer: "P60"
      branch: "domain"
      prereqs: []
      provenance:
        - "a04-anchor"
    - id: "A04-03"
      name: "说话人分离与识别"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "a04-anchor"
    - id: "A04-04"
      name: "方言与口音适应"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "A04-01"
      provenance:
        - "a04-anchor"
    - id: "A04-05"
      name: "噪声与远场鲁棒"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "A04-01"
      provenance:
        - "a04-anchor"
    - id: "A04-06"
      name: "流式低延迟识别"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "A04-01"
      provenance:
        - "a04-anchor"
    - id: "A04-07"
      name: "TTS 声学模型与声码器"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "a04-anchor"
    - id: "A04-08"
      name: "音色克隆与声音转换"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "A04-07"
      provenance:
        - "a04-anchor"
    - id: "A04-09"
      name: "韵律与情感控制"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "A04-07"
      provenance:
        - "a04-anchor"
    - id: "A04-10"
      name: "多语种混说"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "A04-03"
      provenance:
        - "a04-anchor"
    - id: "A04-11"
      name: "语音评测与打分"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "A04-01"
        - "A04-09"
      provenance:
        - "a04-anchor"
    - id: "A04-12"
      name: "字幕时间轴对齐"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "A04-06"
      provenance:
        - "a04-anchor"
```

## 5. 证据与边界

- 每个节点的来源锚（外部规范 / 论文 / 参考实现）逐条登记于 `STANDARDS_ANCHORS`，本图 `provenance_strength = external`（全覆盖，可复核）。
- 图只声明**结构前置**（装载顺序），不声明掌握程度；边为「先具备 → 后展开」的域内常识序。
- 包外前置族（A04-00）不随包交付，装载方须自备领域基础。
