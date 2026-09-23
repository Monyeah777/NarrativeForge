<!-- nf-asset: key="CONCEPT_GRAPH" version="1.0" status="active" -->
# 概念图 · 红队、越狱与安全测试（概念前置偏序）

> 用途：本域包的**前置闭包求值输入面**——把「红队、越狱与安全测试」这一域的 12 个细分概念声明成一张偏序图（DAG），供域内口径模块（红队越狱与安全测试:M01）与收口模块（红队越狱与安全测试:M02）消费。
> 资产键：`CONCEPT_GRAPH`｜形态：人读表（§2）/ 别名表（§3）/ 机器可读块（§4）三形态同源——**§4 围栏块是唯一机读真相**，§2/§3 由它导出。
> 覆盖：12 个包内概念 + 6 个**可扩展标准节点**（标准目录绑定）+ 1 个包外前置族（C09-00 领域通用前置）。
> 来源：本件正文自撰；每条细分的权威锚见资产 `DOMAIN_SPEC` 与 `STANDARDS_ANCHORS`（逐条可达性实证）。

## 1. 读法

- **概念**：一个可独立装载的知识单元（本域第 N 条细分）。
- **前置**：装载该概念之前必须先具备的概念（边方向「前置 → 后继」）。
- **层**：该概念在 NF 九层位中的合理驻留层（P00–P80），用于装配定位，不是执行顺序。
- **证据**：节点来源锚（见 §5 图例）；本图所有节点均挂外部可复核锚。

## 2. 条目键表（一概念一键，asset_get 寻址）

| 条目键 | 概念 | 层 | 直接前置 | 证据 |
|---|---|---|---|---|
| `C09-01` | 提示注入 | P40 | — | c09-anchor |
| `C09-02` | 越狱模板 | P60 | `C09-01` | c09-anchor |
| `C09-03` | 系统提示泄露 | P40 | `C09-02` | c09-anchor |
| `C09-04` | 工具滥用 | P60 | `C09-03`、`C09-01` | c09-anchor |
| `C09-05` | 多轮渐进攻击 | P40 | `C09-04`、`C09-02` | c09-anchor |
| `C09-06` | 数据外泄测试 | P60 | `C09-05`、`C09-03` | c09-anchor |
| `C09-07` | 跨语言绕过 | P40 | `C09-06`、`C09-04` | c09-anchor |
| `C09-08` | 多模态攻击面 | P60 | `C09-07`、`C09-05` | c09-anchor |
| `C09-09` | 自动化红队 | P40 | `C09-08`、`C09-06` | c09-anchor |
| `C09-10` | 攻击成功率度量 | P60 | `C09-09`、`C09-07` | c09-anchor |
| `C09-11` | 缓解与加固 | P40 | `C09-10`、`C09-08` | c09-anchor |
| `C09-12` | 漏洞披露流程 | P60 | `C09-11`、`C09-09` | c09-anchor |
| `STD-cncf-otel-semconv` | 标准 · 语义约定（可扩展注册表）（OpenTelemetry） | P80 | `C09-04`、`C09-07` | std-catalog |
| `STD-commonmark` | 标准 · CommonMark 0.31.2（CommonMark） | P80 | `C09-01`、`C09-03` | std-catalog |
| `STD-cwe` | 标准 · CWE 缺陷枚举（MITRE） | P80 | `C09-12` | std-catalog |
| `STD-frictionless-table` | 标准 · Table Schema（Frictionless） | P80 | `C09-06` | std-catalog |
| `STD-mlcommons-bench` | 标准 · MLPerf 基准（可扩展场景）（MLCommons） | P80 | `C09-11` | std-catalog |
| `STD-owasp-llm` | 标准 · LLM 应用十大风险（OWASP） | P80 | `C09-02`、`C09-05`、`C09-08`、`C09-09`、`C09-10` | std-catalog |

## 3. 别名表（求值时 id 与别名等价）

| 别名 | 概念 id |
|---|---|
| `C09-提示注入` | `C09-01` |
| `C09-越狱模板` | `C09-02` |
| `C09-系统提示泄露` | `C09-03` |
| `C09-工具滥用` | `C09-04` |
| `C09-多轮渐进攻击` | `C09-05` |
| `C09-数据外泄测试` | `C09-06` |
| `C09-跨语言绕过` | `C09-07` |
| `C09-多模态攻击面` | `C09-08` |
| `C09-自动化红队` | `C09-09` |
| `C09-攻击成功率度量` | `C09-10` |
| `C09-缓解与加固` | `C09-11` |
| `C09-漏洞披露流程` | `C09-12` |
| `std-cncf-otel-semconv` | `STD-cncf-otel-semconv` |
| `std-commonmark` | `STD-commonmark` |
| `std-cwe` | `STD-cwe` |
| `std-frictionless-table` | `STD-frictionless-table` |
| `std-mlcommons-bench` | `STD-mlcommons-bench` |
| `std-owasp-llm` | `STD-owasp-llm` |

## 4. 机器可读块（唯一机读真相）

```yaml
concept_graph:
  version: "1.0"
  domain: "红队、越狱与安全测试"
  code: "C09"
  provenance_strength: "external"
  provenance_legend:
    c09-anchor: "域内权威锚（规范 / 论文 / 参考实现），逐条 URL 与可达性实证见资产 STANDARDS_ANCHORS（本波实测）"
    std-catalog: "可扩展标准目录条目（protocol/standards_catalog.json，本机可达性实测）"
  external_prereqs:
    - id: "C09-00"
      name: "领域通用前置族（数学/工程基础，包外）"
  branches:
    - id: "domain"
      name: "红队、越狱与安全测试 全域"
      nodes:
        - "C09-01"
        - "C09-02"
        - "C09-03"
        - "C09-04"
        - "C09-05"
        - "C09-06"
        - "C09-07"
        - "C09-08"
        - "C09-09"
        - "C09-10"
        - "C09-11"
        - "C09-12"
    - id: "standards"
      name: "可扩展标准（绑定）"
      nodes:
        - "STD-cncf-otel-semconv"
        - "STD-commonmark"
        - "STD-cwe"
        - "STD-frictionless-table"
        - "STD-mlcommons-bench"
        - "STD-owasp-llm"
  nodes:
    - id: "C09-01"
      name: "提示注入"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "c09-anchor"
    - id: "C09-02"
      name: "越狱模板"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "C09-01"
      provenance:
        - "c09-anchor"
    - id: "C09-03"
      name: "系统提示泄露"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "C09-02"
      provenance:
        - "c09-anchor"
    - id: "C09-04"
      name: "工具滥用"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "C09-03"
        - "C09-01"
      provenance:
        - "c09-anchor"
    - id: "C09-05"
      name: "多轮渐进攻击"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "C09-04"
        - "C09-02"
      provenance:
        - "c09-anchor"
    - id: "C09-06"
      name: "数据外泄测试"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "C09-05"
        - "C09-03"
      provenance:
        - "c09-anchor"
    - id: "C09-07"
      name: "跨语言绕过"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "C09-06"
        - "C09-04"
      provenance:
        - "c09-anchor"
    - id: "C09-08"
      name: "多模态攻击面"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "C09-07"
        - "C09-05"
      provenance:
        - "c09-anchor"
    - id: "C09-09"
      name: "自动化红队"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "C09-08"
        - "C09-06"
      provenance:
        - "c09-anchor"
    - id: "C09-10"
      name: "攻击成功率度量"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "C09-09"
        - "C09-07"
      provenance:
        - "c09-anchor"
    - id: "C09-11"
      name: "缓解与加固"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "C09-10"
        - "C09-08"
      provenance:
        - "c09-anchor"
    - id: "C09-12"
      name: "漏洞披露流程"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "C09-11"
        - "C09-09"
      provenance:
        - "c09-anchor"
    - id: "STD-cncf-otel-semconv"
      name: "标准 · 语义约定（可扩展注册表）"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "C09-04"
        - "C09-07"
      provenance:
        - "std-catalog"
    - id: "STD-commonmark"
      name: "标准 · CommonMark 0.31.2"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "C09-01"
        - "C09-03"
      provenance:
        - "std-catalog"
    - id: "STD-cwe"
      name: "标准 · CWE 缺陷枚举"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "C09-12"
      provenance:
        - "std-catalog"
    - id: "STD-frictionless-table"
      name: "标准 · Table Schema"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "C09-06"
      provenance:
        - "std-catalog"
    - id: "STD-mlcommons-bench"
      name: "标准 · MLPerf 基准（可扩展场景）"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "C09-11"
      provenance:
        - "std-catalog"
    - id: "STD-owasp-llm"
      name: "标准 · LLM 应用十大风险"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "C09-02"
        - "C09-05"
        - "C09-08"
        - "C09-09"
        - "C09-10"
      provenance:
        - "std-catalog"
```

## 5. 证据与边界

- 每个节点的来源锚（外部规范 / 论文 / 参考实现）逐条登记于 `STANDARDS_ANCHORS`，本图 `provenance_strength = external`（全覆盖，可复核）。
- 图只声明**结构前置**（装载顺序），不声明掌握程度；边为「先具备 → 后展开」的域内常识序。
- 包外前置族（C09-00）不随包交付，装载方须自备领域基础。
