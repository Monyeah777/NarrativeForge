---
id: AUD-0022
title: 可扩展标准目录扩面 126 → 370 条 + 全 100 包「双锚（主锚/辅锚）× 数据真实性」对齐 + 概念图纵深（密度 1.0476 → 1.2647）
date: 2026-09-24
scope: 作者指令「先搜集所有可扩展标准；把所有域包在概念密度与数据真实性上对齐，且质量纵深发展；默认可用决策模型与检索资料」——本件记录：标准目录扩面与依赖边、双锚绑定规则与实测、概念图纵深、数据真实性复合口径、门禁七判据，以及本波修掉的两处门禁根因（含一处真缺陷）
verdict: pass
auditor: 本轮执行者
subjects:
  - desktop/src/core/domain_pack.py:789fb8f57c80721faf30d0b855c80fc451b0b3ac02b3a61489119fabb8a8719e
  - desktop/src/core/retriever.py:c8f2f384b1fdd34132b6a643ff4fefef6139bcb8e53c9a00e2487749f935b13b
  - desktop/tests/test_retriever.py:15b841c434d3cdecde9c12d326b04e642d176dfd59dd8dfe8287a3e496bb29e2
  - verify.sh:8fbc94910bb6dda962e5e5996e443844608b3dfc3c05b849eda28225939886e0
  - docs/domain-packs.md:5196a140e3bdb8af995cde13d7eba8c6ca39722e79b9711f767ad3f981ce2c79
---

> 签收位：本件**未填 `accepted_by`/`accepted_at`**——验收签收属作者动作，执行者不自签。
> subjects = 5 件（域包工厂、检索反向引用、其回归测试、门禁脚本、公开文档）；
> **不含派生物**——`protocol/standards_catalog.json`（探针脚本产出）与
> `protocol/standards_binding.json`（工厂产出）、100 包的 `DOMAIN_SPEC.json` 与
> `domain_packs.json` 名录均为可复算投影。

## 一、内部差距（开工依据）

1. 目录只有 **126 条**、65 家机构，覆盖偏窄：**工业/能源/交通协议**、**出版与文档形态族**、
   **治理细则（NIST 800 系列 / PCI / HIPAA / 巴塞尔 / FATF / ISSB）**、**工程出品面
   （SLSA / in-toto / Sigstore / CT / CSAF / SSVC / 建模标准族）**几乎空缺。
2. 每条细分**只绑一条标准**：一条标准要同时承担「这条细分依据什么口径」与「这条细分的产出靠什么承载」
   两种职责，二者混在一处，谁也证不清。
3. 「数据真实性」当时只有一句话断言（在册 + 可达），**没有复合口径、没有逐包复算数值、没有门槛**。
4. 概念图的标准分支是**星形**（概念 → 标准），标准之间的**真实依赖关系**（如 OpenAPI → JSON Schema、
   C2PA → CBOR）完全没进图。

## 二、标准目录扩面（126 → 370 条）+ 依赖边

| 指标 | 上一波 | 本波 |
|---|---|---|
| 标准条数 | 126 | **370**（新增 244） |
| 发布机构 | 65 | **194** |
| 本机可达 200 | 115 | **330** |
| 规范依赖边 `depends_on` | 0 | **206** |
| 层分布 | data 38 / gov 38 / iface 29 / form 13 / eng 8 | data 148 / iface 84 / gov 71 / eng 38 / form 29 |

新增面覆盖：数据格式族（ORC / Iceberg / Delta / HDF5 / NetCDF / Zarr / FITS / LAS / CityGML /
GeoJSON / JPEG XL / AVIF / HEIF / OpenEXR / USD / IFC / GTFS / NeTEx / STIX-TAXII…）；
接口族（OAuth2 / OIDC / SAML / SCIM / WebAuthn / GNAP / QUIC / TLS 1.3 / HTTP 语义与缓存 /
MQTT5 / AMQP / Kafka / Matrix / ActivityPub / OPC UA / Modbus / BACnet / OCPP / SunSpec /
Redfish / SPIFFE / Matter / ROS 2 / MAVLink…）；形态族（Vega / AsciiDoc / reST / OPC-OOXML /
OMML / ODF / WAI-ARIA / ATAG / ITS / WebVTT / TTML / SSML…）；治理族（NIST 800-53·CSF·800-63·800-207 /
OSCAL / FedRAMP / PCI DSS / HIPAA / 巴塞尔 III / FATF / IFRS / ISSB / GHG / CIS / ASVS / SOC 2 /
EN 301 549 / Section 508 / EAA…）；工程族（SemVer / Conventional Commits / TAP / JUnit XML /
可重现构建 / SLSA / in-toto / Sigstore / **证书透明 v2（RFC 9162）** / SCITT / OpenVEX / CSAF /
SSVC / OpenChain / REUSE / OPA·CUE / BPMN·DMN·UML·SysML / ArchiMate·TOGAF / FinOps / SCI…）。

**不可达如实记（40 条）**：bot 防护 403（iso.org / loc.gov / hhs.gov / fatt / coe / ebu /
sunspec / modbus…）、反爬 202（eur-lex / hl7.org / editeur）、本机出口不通（autosar / cipa SSL）、
付费墙与登录 401（pubs.opengroup）——**不假装可达**，且绑定时**可达优先**。

## 三、双锚绑定（1200 → 2400 条）

- **主锚**（`standard`）：该细分依据的域口径标准（关键词 → 域码专属 → 段默认轮换 → 多样性补位），
  新增**可达优先**：同一命中位有本机实测可达的候选即先取可达者。
- **辅锚**（`support_standard`）：该细分**产出的承载标准**（契约 / 数据表 / 图表 / 图示 / 溯源 /
  时间 / 单位 / 数值 / 遥测 / 凭证 / 清单 / 文本 / 许可 / 身份 / 接口 / 事件），按产出形态关键词选择，
  **优先与主锚异层**；辅锚覆盖率 **100%**。
- 绑定行逐条落 `layer / body / url / reachable / probe_date`——**实测证据跟着绑定走**，
  绑定表本身即可复核真实性。

**口径修正（本波顺手修的两处语义偏差）**：D 段默认锚 `iso-iec-25010`（ISO 软件质量模型，
iso.org 403 不可达）→ **Common Criteria（ISO 15408，可扩展保护轮廓，本机可达）**；
制造类关键词锚 `iso-iec-25010` → **OPC UA**（工业互联，本机可达）。两处同时提升**可达性**与**语义贴合度**
（软件质量模型本不是工业制造的首选口径锚）。

## 四、概念图纵深（密度门槛 1.0 → 1.25）

标准分支由「概念 → 主锚」单边扩为**三类边**：概念 → 主锚、概念 → 辅锚、**标准 → 标准（依赖）**；
依赖边端点（被依赖标准）一并入图，保证「有边必有端点」。实测 100 包：

| 指标 | 上一波 | 本波 |
|---|---|---|
| 节点/包 | 15–20 | **21–34** |
| 边/包 | 21–24 | **38–60** |
| 标准依赖边/包 | 0 | **3–12** |
| 最小密度 | 1.0476 | **1.2647**（均值 1.8566） |

## 五、数据真实性（逐包可复算的复合分）

```
data_authenticity = 在册率 × (0.5 + 0.5 × 本机实测可达率) × 证据齐备率
```

乘法口径，**任一环缺即降分**（不用加权和掩盖缺口）。三要素 + 细分锚已探率逐包复算并落
`DOMAIN_SPEC.json` 的 `data_authenticity` 块与名录；实测 100/100 包：
在册率 1.0 · 可达率 1.0 · 证据齐备 1.0 · 细分锚已探率 1.0 → **真实性分 1.0000**（门槛 0.95）。

check32 `domain_packs` 子扫描由四判据扩到**七判据**：覆盖率 100% / 引用在册 / 每包 ≥3 条不同标准 /
密度 ≥1.25 / **辅锚覆盖率 = 1.0** / **标准依赖边 ≥1** / **真实性 ≥0.95 且可达率 ≥0.9**。
绑定表逐行还须带**在册证明与实测记录**（缺任一即 FAIL）。

## 六、本波修掉的两处门禁根因

1. **`check16-B` 的过强假设**：原判据要求「每个被 `asset_readonly` 白名单引用的源包必须有
   `assets/*.md`」，对**声明 0 自有资产的借阅型包**（`校园西幻轻混组合包`，只有 modules/pipelines）
   直接判 FAIL——这是**判据错**（该包 `protocol.yaml` 明写 `assets.count: 0`）。改为：
   查到 `count: 0` 判「不虚标可寻址」（并断言 `asset_get` 返回 None），缺声明才判违约。
2. **`referenced_by` 的跨类别误命中（真缺陷）**：反向引用查询对**类别限定 id** 只按裸号尾部匹配，
   于是查 `AI保险:M01` 会返回 `数据采集与清洗:M01` / `法律与合规:M01` 的引用方——
   组合包产物化后类别限定 id 变多，这个缺陷才被硬编码期望的过期暴露出来。改为**类别感知匹配**
   （查询带类别 → 命中同类别或裸号声明，异类别同号不命中；查询裸号 → 保留裸号检索便利），
   并把测试期望改为「按声明侧类别感知复算」+ 加跨类别回归断言（不再写死 `== []`）。

## 七、边界（不宣称）

- **标准对齐 ≠ 遵从认证**：目录与绑定只声明「与该标准对齐、且该标准本机实测可达」，
  不声明合规、认证或采用；外部标准只作口径与机制参照（STRATEGY §3.2/§3.3）。
- 不可达标准**不当唯一锚**：可达优先 + 辅锚兜底，保证每条细分至少有一条本机实测可达的锚。
- 密度是**图结构指标**，不衡量内容质量；密度达标不等于口径正确。
- 12 条细分内容仍来自内部域规格档（作者侧输入），公开面只呈现结果与判据。
