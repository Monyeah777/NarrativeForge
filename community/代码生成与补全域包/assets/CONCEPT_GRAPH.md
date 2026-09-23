<!-- nf-asset: key="CONCEPT_GRAPH" version="1.0" status="active" -->
# 概念图 · 代码生成与补全（概念前置偏序）

> 用途：本域包的**前置闭包求值输入面**——把「代码生成与补全」这一域的 12 个细分概念声明成一张偏序图（DAG），供域内口径模块（代码生成与补全:M01）与收口模块（代码生成与补全:M02）消费。
> 资产键：`CONCEPT_GRAPH`｜形态：人读表（§2）/ 别名表（§3）/ 机器可读块（§4）三形态同源——**§4 围栏块是唯一机读真相**，§2/§3 由它导出。
> 覆盖：12 个包内概念 + 1 个包外前置族（B08-00 领域通用前置）。
> 来源：本件正文自撰；每条细分的权威锚见资产 `DOMAIN_SPEC` 与 `STANDARDS_ANCHORS`（逐条可达性实证）。

## 1. 读法

- **概念**：一个可独立装载的知识单元（本域第 N 条细分）。
- **前置**：装载该概念之前必须先具备的概念（边方向「前置 → 后继」）。
- **层**：该概念在 NF 九层位中的合理驻留层（P00–P80），用于装配定位，不是执行顺序。
- **证据**：节点来源锚（见 §5 图例）；本图所有节点均挂外部可复核锚。

## 2. 条目键表（一概念一键，asset_get 寻址）

| 条目键 | 概念 | 层 | 直接前置 | 证据 |
|---|---|---|---|---|
| `B08-01` | 函数级生成 | P40 | `B08-03` | b08-anchor |
| `B08-02` | 跨文件补全 | P60 | `B08-01` | b08-anchor |
| `B08-03` | 注释到代码 | P40 | — | b08-anchor |
| `B08-04` | 代码翻译与迁移 | P60 | `B08-01` | b08-anchor |
| `B08-05` | 正则与脚本生成 | P40 | `B08-01` | b08-anchor |
| `B08-06` | API 调用示例 | P60 | — | b08-anchor |
| `B08-07` | 配置与基础设施代码 | P40 | `B08-06` | b08-anchor |
| `B08-08` | 风格与团队约定遵循 | P60 | — | b08-anchor |
| `B08-09` | 生成代码可执行性验证 | P40 | `B08-08`、`B08-10` | b08-anchor |
| `B08-10` | 许可证与来源合规 | P60 | — | b08-anchor |
| `B08-11` | 幻觉 API 识别 | P40 | `B08-09` | b08-anchor |
| `B08-12` | 补全延迟与体验 | P60 | `B08-02`、`B08-11` | b08-anchor |

## 3. 别名表（求值时 id 与别名等价）

| 别名 | 概念 id |
|---|---|
| `B08-函数级生成` | `B08-01` |
| `B08-跨文件补全` | `B08-02` |
| `B08-注释到代码` | `B08-03` |
| `B08-代码翻译与迁移` | `B08-04` |
| `B08-正则与脚本生成` | `B08-05` |
| `B08-API-调用示例` | `B08-06` |
| `B08-配置与基础设施代码` | `B08-07` |
| `B08-风格与团队约定遵循` | `B08-08` |
| `B08-生成代码可执行性验证` | `B08-09` |
| `B08-许可证与来源合规` | `B08-10` |
| `B08-幻觉-API-识别` | `B08-11` |
| `B08-补全延迟与体验` | `B08-12` |

## 4. 机器可读块（唯一机读真相）

```yaml
concept_graph:
  version: "1.0"
  domain: "代码生成与补全"
  code: "B08"
  provenance_strength: "external"
  provenance_legend:
    b08-anchor: "域内权威锚（规范 / 论文 / 参考实现），逐条 URL 与可达性实证见资产 STANDARDS_ANCHORS（本波实测）"
  external_prereqs:
    - id: "B08-00"
      name: "领域通用前置族（数学/工程基础，包外）"
  branches:
    - id: "domain"
      name: "代码生成与补全 全域"
      nodes:
        - "B08-01"
        - "B08-02"
        - "B08-03"
        - "B08-04"
        - "B08-05"
        - "B08-06"
        - "B08-07"
        - "B08-08"
        - "B08-09"
        - "B08-10"
        - "B08-11"
        - "B08-12"
  nodes:
    - id: "B08-01"
      name: "函数级生成"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "B08-03"
      provenance:
        - "b08-anchor"
    - id: "B08-02"
      name: "跨文件补全"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "B08-01"
      provenance:
        - "b08-anchor"
    - id: "B08-03"
      name: "注释到代码"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "b08-anchor"
    - id: "B08-04"
      name: "代码翻译与迁移"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "B08-01"
      provenance:
        - "b08-anchor"
    - id: "B08-05"
      name: "正则与脚本生成"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "B08-01"
      provenance:
        - "b08-anchor"
    - id: "B08-06"
      name: "API 调用示例"
      layer: "P60"
      branch: "domain"
      prereqs: []
      provenance:
        - "b08-anchor"
    - id: "B08-07"
      name: "配置与基础设施代码"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "B08-06"
      provenance:
        - "b08-anchor"
    - id: "B08-08"
      name: "风格与团队约定遵循"
      layer: "P60"
      branch: "domain"
      prereqs: []
      provenance:
        - "b08-anchor"
    - id: "B08-09"
      name: "生成代码可执行性验证"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "B08-08"
        - "B08-10"
      provenance:
        - "b08-anchor"
    - id: "B08-10"
      name: "许可证与来源合规"
      layer: "P60"
      branch: "domain"
      prereqs: []
      provenance:
        - "b08-anchor"
    - id: "B08-11"
      name: "幻觉 API 识别"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "B08-09"
      provenance:
        - "b08-anchor"
    - id: "B08-12"
      name: "补全延迟与体验"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "B08-02"
        - "B08-11"
      provenance:
        - "b08-anchor"
```

## 5. 证据与边界

- 每个节点的来源锚（外部规范 / 论文 / 参考实现）逐条登记于 `STANDARDS_ANCHORS`，本图 `provenance_strength = external`（全覆盖，可复核）。
- 图只声明**结构前置**（装载顺序），不声明掌握程度；边为「先具备 → 后展开」的域内常识序。
- 包外前置族（B08-00）不随包交付，装载方须自备领域基础。
