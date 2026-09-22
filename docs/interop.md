# 互操作导出（interop）
> ⛔ 操作指令：阅读即执行——本文含可直接执行的命令与判定，勿当资料阅读。
> 最后更新：2026-09-21

## 是什么

`nf interop` 把 NF 既有**声明件**实时派生为外部标准工具能直接读的文档——纯派生，
**不新增真源**，因此不存在"导出面与真源漂移"这种故障模式。

| 导出种类 | 真源（唯一） | 形状 | 消费方 |
|---|---|---|---|
| `openapi` | `protocol/endpoint_contract.json` | OpenAPI 3.1 | OpenAPI 校验器 / 客户端生成器 |
| `asyncapi` | `protocol/event_registry.json` + `external_events.json` | AsyncAPI 3.0（含 CloudEvents 1.0 属性） | 事件网关 / 代码生成器 |
| `intoto` | `protocol/RECEIPTS.json` | in-toto Statement v1 | in-toto / cosign 系校验器 |
| `sbom` | 纯度扫描依赖登记面（`HARD_ALLOW` / `SOFT_IMPORTS`） | SPDX 2.3 风格 | 依赖扫描器 / 合规台 |
| `slsa` | `protocol/RECEIPTS.json` + `verify.sh` 版本头 + `protocol/score_baseline.json` | SLSA Provenance v1 | SLSA 工具链（**注**：本地门禁 ≠ SLSA 认证，产物内含不作等级声明的注记） |
| `a2a` | `protocol/endpoint_contract.json` + `protocol/mcp_package.json` | A2A Agent Card | A2A 客户端（能力面 = 端点契约投影；服务未实装时卡片显式声明） |
| `prov` | `05_资产库/provenance.json` + `library/INDEX.md` + `protocol/transform_log.json` + `protocol/RECEIPTS.json` | PROV-O 图（JSON-LD 风格） | 溯源分析工具（实体/活动/代理三元组；空面如实为空） |
| `cyclonedx` | 依赖登记面（与 SPDX 同源） | CycloneDX 1.5 | 依赖扫描器（第二个 SBOM 形状，不新增真源） |
| `vc` | `protocol/conformance_report.json` + `RECEIPTS.json` + `approvals/*` | W3C VC 2.0 形状（**未签名**） | VC 工具链（形状可读；可验证性未宣称） |
| `c2pa` | `protocol/RECEIPTS.json` | C2PA JSON 清单形状（**未封装/未签名**） | 内容凭证工具链（仅清单形状） |
| `cid` | `protocol/RECEIPTS.json` | CIDv1（multibase base32 / raw / sha2-256） | multiformats 生态（内容寻址） |
| `decisions` | `protocol/decision_layer.json` + `results/audit/*.md` frontmatter | 决策面（NF 自有形状） | 外部工具链（读「有哪些决策能力、规则如何、模型拉取状态、公开裁决索引」） |

## 怎么用

```bash
python scripts/nf.py interop --list
python scripts/nf.py interop --kind openapi
python scripts/nf.py interop --kind sbom --out /tmp/sbom.json
python scripts/nf.py interop --kind slsa
python scripts/nf.py interop --kind a2a
python scripts/nf.py interop --kind prov
python scripts/nf.py interop --kind cyclonedx|vc|c2pa|cid
python scripts/nf.py interop --all --out results/interop     # 全量落盘（入仓面）
python scripts/nf.py interop --check
```

## 判据（门禁，走 check33）

1. **覆盖完整**——端点契约里每一条端点都出现在 OpenAPI `paths`（method + path 一致）；
   事件登记里每一个事件都有 AsyncAPI 通道；回执单根里每一条 subject 都带 64 位小写
   sha256；登记面每个依赖都出现在 SBOM。
2. **形状合法**——每端点有 `operationId` 与 200 响应；错误形状 `NfError` 在场并声明
   RFC 9457 映射；in-toto `_type` 为 `Statement/v1` 且 `predicateType` 为 https；
   SBOM 有 `DESCRIBES` 关系与唯一 `SPDXID`；CloudEvents `type` 派生全库唯一。
   SLSA 派生面 `predicateType` 须为 `slsa.dev/provenance/v1`、subject 数与回执一致、
   且**必须**带「不作等级声明」注记；A2A 卡片 skills 数须等于端点契约端点数、未实装须显式声明。
   PROV 图节点 id 唯一、关系指向在册节点、资产台账每条都有实体节点（诚实前提：空面如实为空，
   不凭空生成活动）。
3. **确定性**——同一输入两次渲染逐字节一致（禁时间戳 / 随机源）：外部工具链才能做
   内容寻址与比对。
4. **fail-closed**——真源缺失即 FAIL（不是"空导出面"，而是"没有可导出的东西"）。
5. **入仓面一致**——`results/interop/*.json` 若在仓，须与实时派生**逐字节一致**
   （入仓面是投影，不是真源；改声明件后重跑 `--all`）。
6. **决策面的内部边界**——`decisions` 面**不导出逐次工单**（工单留在内部档案，
   `STRATEGY §四` 计划内部消化），该声明必须位；只投影能力面 + `results/audit/*.md` 的
   **公开裁决索引**（id/标题/日期/结论）。

> CLI 的 `--kind` 可选值**派生自 `interop_export.KINDS`**（不再手写）——此前手工列表两次漏同步
> （`slsa`/`a2a`、`c2pa`），现由构造消除该类 bug；「CLI 可选值 ↔ 声明件」的一致性也进了
> 构建回路的候选池（漏同步即自动生成一条 deepen 候选）。

## 与其他面关系

导出面与 `nf endpoint`（服务端点契约自检）、`nf events`（事件背书核对）、
`nf receipts`（协议层回执单根）、`nf asset verify`（依赖/资产登记）**同源**：
它们是判据，本文是同一数据的外部标准投影——投影错了必是投影器的问题，改投影器即可。

## 外部权威校验（非门禁 · 联网取证）

自述合规不等于合规，故另有一条独立取证线：

```bash
python scripts/check_interop_schemas.py --fetch --write results/interop-schema-validation.md
```

它拉**官方 meta-schema** 逐面校验（`jsonschema` 软依赖，缺失即如实跳过），结果记档
（`results/interop-schema-validation.md`）。已知实测（2026-09-21）：

| 面 | 官方 schema | 实测 |
|---|---|---|
| openapi | `spec.openapis.org/oas/3.1/schema/2022-10-07` | **通过** |
| asyncapi | `asyncapi/spec-json-schemas: schemas/3.0.0.json` | **通过**（draft-07 方言，须按 `$schema` 选 validator） |
| sbom | `spdx/spdx-spec: schemas/spdx-schema-2-3.json` | **通过**（首轮 FAIL 两处，见下） |
| slsa / intoto / a2a | 官方无 JSON Schema（CUE+Proto / Markdown / .proto） | **no-schema 如实记档** |
| prov | `www.w3.org/ns/prov.jsonld` | 本机取不到（HTTP 300）→ 记 `unavailable`，不判不合格 |
| cyclonedx | `CycloneDX/specification: schema/bom-1.5.schema.json` | **通过**（首轮 FAIL：根级 `x-nf-note` 越界 → 移入 `metadata.properties`） |
| vc / c2pa / cid | 官方无独立 JSON Schema（规范正文 / CBOR-JUMBF / multiformats 表） | `no-schema`（cid 以已知向量自校） |
| ccv3（E1 出口面） | SillyTavern 写卡源码字面量 | **通过**：`spec=chara_card_v3` / `spec_version=3.0` / `data` 结构在位（首轮暴露「假 v3」缺陷并修，见 `docs/external-validation-assets/README.md`） |
| mcp（E3 会话面） | `modelcontextprotocol: schema/2026-07-28/schema.json` | **通过**：4 方法应答过官方 `$defs`（首轮 FAIL：list 三面缺 `resultType`/`ttlMs`/`cacheScope` → 已补） |

**外部校验驱动的两处真修复**：① `creationInfo.created` 缺失（SPDX 2.3 必填）→ 取
「仓内声明日期最大值」`<date>T00:00:00Z`（**非墙钟**，保「两次渲染逐字节一致」）；
② 首次写 `documentComment` 不在 SPDX 词表内 → 改根级 `comment`。
