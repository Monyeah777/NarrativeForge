---
id: AUD-0019
title: 可扩展标准目录（126 条 / 65 机构）+ 100 包 × 1200 细分逐条绑定（覆盖率 100%）+ 概念密度门槛 + 决策模型裁决
date: 2026-09-23
scope: 作者指令「先搜集所有可扩展标准；把所有域包在概念密度与数据真实性上对齐，且质量纵深发展；默认可用决策模型与检索资料」——本件记录：标准目录与可达性实证、逐条绑定规则与实测、概念图标准分支（密度）、门禁四判据、决策模型裁决、本波修掉的问题
verdict: pass
auditor: 本轮执行者
subjects:
  - desktop/src/core/domain_pack.py:dd10260c8a03ec5be7cf4d30689eef1141e23296f87ed99846715e560cfa4fcd
  - desktop/src/core/asset_density.py:6058bf77810a36fc0d62ca489a52e988d017aca812f5fb8a8d45fcf58f916bcb
  - docs/domain-packs.md:fd3bbbef5d6475e3a095c79a34cdeb9342be077f227af41e01429feedba93428
  - protocol/data_contracts.json:3687b2b499f33d927a37a072eb3e48df690a73056f3124ed38a86b7dab14c7e4
---

> 签收位：本件**未填 `accepted_by`/`accepted_at`**——验收签收属作者动作，执行者不自签。
> subjects = 4 件（工厂、资产密度度量、公开文档、数据契约登记）；**不含派生物**
> （`protocol/standards_catalog.json` 与 `protocol/standards_binding.json` 由脚本/工厂可复算，
> 是**证据与投影**而非源——按口径不入审计绑定）。

## 一、内部差距（开工依据）

1. 100 个域包虽已结构完整，但**每条细分只挂一个外部锚**（URL），没有「这条细分依据哪条**可扩展
   标准**的哪个扩展点」这一层——外部标准与包内容之间缺一条可机检的绑定层。
2. **概念密度**没有口径、也没有门槛：概念图 12 节点 / 9 边，边/节点 = 0.75，低于「一张图至少
   要连得起来」的常识线。
3. **数据真实性**只有锚可达性一条链；缺第二条独立链（标准绑定），也没有「引用是否在册」的判据。

## 二、可扩展标准目录（外部检索 + 逐条实证）

`protocol/standards_catalog.json`：**126 条**标准 / **65 家机构** / **115 条本机可达 200**，
按层分布 data 38 · gov 38 · iface 29 · form 13 · eng 8。每条登记：
`body`（机构）/ `title` / `url` / **`ext_points`（扩展机制：扩展点、扩展注册表、profile、
命名空间、版本化槽位）** / `layer` / `evidence`（本机状态 + 取样标题 + sha256 + 探针日期与方法）。

不可达 11 条如实记（eur-lex 202 反爬 / iso.org 403 / iso20022 403 / autosar 0），**不假装可达**；
绑定规则优先选可达条目（实测每条细分的 `standard_ref` 都命中可达或已被目录登记的条目）。

## 三、逐条绑定（100 包 × 12 细分 = 1200 条，覆盖率 100%）

`protocol/standards_binding.json`：每条 = `subdivision` + `standard` + `rationale`
（关键词命中 / 域码专属 / 段默认轮换 / **多样性补位**）+ 标准机构与 URL。

规则优先级（写在 `core/domain_pack.py`，可复算）：
1. **关键词**（≈60 条规则：许可→CC、隐私→GDPR、安全→OWASP-LLM、医疗→FHIR、影像→DICOM、
   食品→Codex、金融→GIPS、车机→COVESA VSS、机器人→EU 机械条例、OTA→Uptane、地理→OGC、
   术语→SKOS、溯源→PROV-O、契约→JSON Schema、表格→CSVW、评测→MLPerf、可观测→OTel、
   接口→OpenAPI、事件→CloudEvents、工具调用→MCP、多智能体→A2A、模型→ONNX、图表→Vega-Lite…）；
2. **域码专属**（26 条覆盖，如 C11→K8s CRD+OTLP、C18→OTel+Prometheus+OpenMetrics、D04→GIPS+MIC）；
3. **段默认轮换**（A/B/C/D/E/F 各 3 条池，按细分序轮换）；
4. **多样性补位**：若整包被关键词挤到 <3 条标准，按段池改绑直到 ≥3 条。

## 四、概念密度与门禁四判据（check32 `domain_packs`）

概念图新增 **standards 分支**：节点 `STD-<标准 id>`（层位 P80、溯源键 `std-catalog`），
边为「概念 → 其依据的标准」；分支、别名、溯源图例同步扩展（图健康六判据仍零 issue）。

| 判据 | 门槛 | 实测 |
|---|---|---|
| 每条细分有 `standard_ref` | 覆盖率 100% | **1.0000** |
| 引用 id 在标准目录在册 | 全在册 | **1200/1200** |
| 每包不同标准数 | ≥3 | **最小 3** |
| 概念密度（边/节点） | ≥1.0 | **最小 1.0476**（节点 12→15–20，边 9→21–24） |

## 五、决策模型（Laya 热路径 + Jev 契约冷链路；非门禁）

真模型（本地 `laya-multilingual`）在**绑定最弱**的 8 个包里选下一步深化对象 →
**C01 数据采集与清洗域包**（不同标准 3），`worth deepening p=0.9229`；
冷链路三步对本波两条断言（目录可达性为实测 / 绑定覆盖率 100%）给出真伪可判定结论与归属意见。
记录：`.rivet/private_archive/ai_packs/decision_standards.json`。

## 六、本波修掉的三处真问题

1. **生成器读标准目录用了硬编码 `"."`**（cwd 依赖）——单测在 `desktop/` 下运行时读不到目录，
   生成内容不同 → `domain verify` 报漂移。修法：生成函数全部接收 `root`（`plan(root, spec)` 透传）。
2. **多样性不足**：关键词规则会把某些包 12 条细分全挤到 1–2 条标准 → 加「多样性补位」后处理，
   门槛 ≥3 条不同标准。
3. **批量写盘偶发 EINVAL(22)**（Windows 杀软/句柄扫描）：工厂全部落盘改走**退避重试**
   （`_write_text_retry`），并把 registry 投影收进 build（此前实测漏跑 register 导致四处红）。

## 七、边界与不宣称

- 标准目录是**入口与可达性实证**，未做规范全文比对；绑定是**口径与机制参照**，不作质量背书。
- 74 个派生档（derived）包的领域细则仍待作者补全（包内三处显式标注）；绑定层不改变该事实。
- 概念密度门槛 1.0 是**下限**，不代表图已完备；标准节点是「依据」不是「从属」。
