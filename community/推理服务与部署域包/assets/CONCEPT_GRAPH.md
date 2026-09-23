<!-- nf-asset: key="CONCEPT_GRAPH" version="1.0" status="active" -->
# 概念图 · 推理服务与部署（概念前置偏序）

> 用途：本域包的**前置闭包求值输入面**——把「推理服务与部署」这一域的 12 个细分概念声明成一张偏序图（DAG），供域内口径模块（推理服务与部署:M01）与收口模块（推理服务与部署:M02）消费。
> 资产键：`CONCEPT_GRAPH`｜形态：人读表（§2）/ 别名表（§3）/ 机器可读块（§4）三形态同源——**§4 围栏块是唯一机读真相**，§2/§3 由它导出。
> 覆盖：12 个包内概念 + 1 个包外前置族（C11-00 领域通用前置）。
> 来源：本件正文自撰；每条细分的权威锚见资产 `DOMAIN_SPEC` 与 `STANDARDS_ANCHORS`（逐条可达性实证）。

## 1. 读法

- **概念**：一个可独立装载的知识单元（本域第 N 条细分）。
- **前置**：装载该概念之前必须先具备的概念（边方向「前置 → 后继」）。
- **层**：该概念在 NF 九层位中的合理驻留层（P00–P80），用于装配定位，不是执行顺序。
- **证据**：节点来源锚（见 §5 图例）；本图所有节点均挂外部可复核锚。

## 2. 条目键表（一概念一键，asset_get 寻址）

| 条目键 | 概念 | 层 | 直接前置 | 证据 |
|---|---|---|---|---|
| `C11-01` | 推理服务框架 | P40 | — | c11-anchor |
| `C11-02` | 网关与路由 | P60 | `C11-01` | c11-anchor |
| `C11-03` | 多模型编排 | P40 | `C11-02` | c11-anchor |
| `C11-04` | 自动扩缩容 | P60 | `C11-03`、`C11-01` | c11-anchor |
| `C11-05` | 限流与队列 | P40 | `C11-04`、`C11-02` | c11-anchor |
| `C11-06` | 缓存策略 | P60 | `C11-05`、`C11-03` | c11-anchor |
| `C11-07` | 灰度与回滚 | P40 | `C11-06`、`C11-04` | c11-anchor |
| `C11-08` | A/B 模型切换 | P60 | `C11-07`、`C11-05` | c11-anchor |
| `C11-09` | 监控与告警 | P40 | `C11-08`、`C11-06` | c11-anchor |
| `C11-10` | 成本核算 | P60 | `C11-09`、`C11-07` | c11-anchor |
| `C11-11` | 私有化部署 | P40 | `C11-10`、`C11-08` | c11-anchor |
| `C11-12` | SLA 与容量规划 | P60 | `C11-11`、`C11-09` | c11-anchor |

## 3. 别名表（求值时 id 与别名等价）

| 别名 | 概念 id |
|---|---|
| `C11-推理服务框架` | `C11-01` |
| `C11-网关与路由` | `C11-02` |
| `C11-多模型编排` | `C11-03` |
| `C11-自动扩缩容` | `C11-04` |
| `C11-限流与队列` | `C11-05` |
| `C11-缓存策略` | `C11-06` |
| `C11-灰度与回滚` | `C11-07` |
| `C11-A/B-模型切换` | `C11-08` |
| `C11-监控与告警` | `C11-09` |
| `C11-成本核算` | `C11-10` |
| `C11-私有化部署` | `C11-11` |
| `C11-SLA-与容量规划` | `C11-12` |

## 4. 机器可读块（唯一机读真相）

```yaml
concept_graph:
  version: "1.0"
  domain: "推理服务与部署"
  code: "C11"
  provenance_strength: "external"
  provenance_legend:
    c11-anchor: "域内权威锚（规范 / 论文 / 参考实现），逐条 URL 与可达性实证见资产 STANDARDS_ANCHORS（本波实测）"
  external_prereqs:
    - id: "C11-00"
      name: "领域通用前置族（数学/工程基础，包外）"
  branches:
    - id: "domain"
      name: "推理服务与部署 全域"
      nodes:
        - "C11-01"
        - "C11-02"
        - "C11-03"
        - "C11-04"
        - "C11-05"
        - "C11-06"
        - "C11-07"
        - "C11-08"
        - "C11-09"
        - "C11-10"
        - "C11-11"
        - "C11-12"
  nodes:
    - id: "C11-01"
      name: "推理服务框架"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "c11-anchor"
    - id: "C11-02"
      name: "网关与路由"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "C11-01"
      provenance:
        - "c11-anchor"
    - id: "C11-03"
      name: "多模型编排"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "C11-02"
      provenance:
        - "c11-anchor"
    - id: "C11-04"
      name: "自动扩缩容"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "C11-03"
        - "C11-01"
      provenance:
        - "c11-anchor"
    - id: "C11-05"
      name: "限流与队列"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "C11-04"
        - "C11-02"
      provenance:
        - "c11-anchor"
    - id: "C11-06"
      name: "缓存策略"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "C11-05"
        - "C11-03"
      provenance:
        - "c11-anchor"
    - id: "C11-07"
      name: "灰度与回滚"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "C11-06"
        - "C11-04"
      provenance:
        - "c11-anchor"
    - id: "C11-08"
      name: "A/B 模型切换"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "C11-07"
        - "C11-05"
      provenance:
        - "c11-anchor"
    - id: "C11-09"
      name: "监控与告警"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "C11-08"
        - "C11-06"
      provenance:
        - "c11-anchor"
    - id: "C11-10"
      name: "成本核算"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "C11-09"
        - "C11-07"
      provenance:
        - "c11-anchor"
    - id: "C11-11"
      name: "私有化部署"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "C11-10"
        - "C11-08"
      provenance:
        - "c11-anchor"
    - id: "C11-12"
      name: "SLA 与容量规划"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "C11-11"
        - "C11-09"
      provenance:
        - "c11-anchor"
```

## 5. 证据与边界

- 每个节点的来源锚（外部规范 / 论文 / 参考实现）逐条登记于 `STANDARDS_ANCHORS`，本图 `provenance_strength = external`（全覆盖，可复核）。
- 图只声明**结构前置**（装载顺序），不声明掌握程度；边为「先具备 → 后展开」的域内常识序。
- 包外前置族（C11-00）不随包交付，装载方须自备领域基础。
