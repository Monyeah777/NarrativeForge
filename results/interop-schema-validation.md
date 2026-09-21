# 互操作导出面 · 外部权威校验报告

> 由 `scripts/check_interop_schemas.py --fetch` 生成（非门禁；联网取证）。

| 面 | 官方 schema | HTTP | 结果 | 说明 |
|---|---|---|---|---|
| openapi | https://spec.openapis.org/oas/3.1/schema/2022-10-07 | 200 | ok | 官方 meta-schema 校验通过 |
| asyncapi | https://raw.githubusercontent.com/asyncapi/spec-json-schemas/master/schemas/3.0.0.json | 200 | ok | 官方 meta-schema 校验通过 |
| slsa | https://raw.githubusercontent.com/slsa-framework/slsa/main/docs/specs/provenance/v1.0/schema.json | - | no-schema | SLSA v1 官方以 CUE / Protobuf 定义机器可读协议（slsa-framework/slsa: spec/schema/provenance.cue + provenance.proto），无官方 JSON Schema —— 本机无 CUE 工具链，故不做 schema 校验 |
| intoto | https://raw.githubusercontent.com/in-toto/attestation/main/spec/v1/statement.schema.json | - | no-schema | in-toto Statement v1 官方以 Markdown 规范发布（in-toto/attestation: spec/v1/statement.md），该目录无 JSON Schema |
| sbom | https://raw.githubusercontent.com/spdx/spdx-spec/develop/schemas/spdx-schema-2-3.json | 200 | ok | 官方 meta-schema 校验通过 |
| prov | https://www.w3.org/ns/prov.jsonld | 300 | unavailable | schema 取不到（网络/地址问题，非派生面问题） |
| cyclonedx | https://raw.githubusercontent.com/CycloneDX/specification/master/schema/bom-1.5.schema.json | 200 | ok | 官方 meta-schema 校验通过 |
| a2a | A2A 官方仓以 .proto + 文档为主（a2aproject/A2A: specification/a2a.proto；specification/json 下仅 README），无官方 JSON Schema 可供本机校验 | - | no-schema | A2A 官方仓以 .proto + 文档为主（a2aproject/A2A: specification/a2a.proto；specification/json 下仅 README），无官方 JSON Schema 可供本机校验 |
| vc | W3C VC Data Model 2.0 以规范文本 + JSON-LD 上下文发布（w3c/vc-data-model: 规范正文；无官方 JSON Schema 收口凭证形状） | - | no-schema | W3C VC Data Model 2.0 以规范文本 + JSON-LD 上下文发布（w3c/vc-data-model: 规范正文；无官方 JSON Schema 收口凭证形状） |
| c2pa | C2PA 规范以 CBOR/JUMBF 容器 + JSON 清单表示定义（contentauth/c2pa-rs 等实现仓；官方无独立 JSON Schema 文件），且本仓**不做容器封装**，故只做自校验 | - | no-schema | C2PA 规范以 CBOR/JUMBF 容器 + JSON 清单表示定义（contentauth/c2pa-rs 等实现仓；官方无独立 JSON Schema 文件），且本仓**不做容器封装**，故只做自校验 |
| cid | CID 由 multiformats 规范定义（multiformats/cid + multicodec 表），无 JSON Schema；本仓以**已知向量**校验（sha256("") 的 CIDv1 raw） | - | no-schema | CID 由 multiformats 规范定义（multiformats/cid + multicodec 表），无 JSON Schema；本仓以**已知向量**校验（sha256("") 的 CIDv1 raw） |
| ccv3(E1) | SillyTavern 源码字面量 | 200 | ok | 与上游字面量一致（spec=chara_card_v3 / spec_version=3.0 / data 结构在位） |
| mcp(E3) | https://raw.githubusercontent.com/modelcontextprotocol/modelcontextprotocol/main/schema/2026-07-28/schema.json | 200 | ok | 4 个方法应答通过官方 schema（server/discover / resources/list / tools/list / prompts/list） |

> 口径：`unavailable` = schema 取不到（网络/地址问题，不判派生面不合格）；
> `skipped` = 本机缺 validator；`fail` = 官方 schema 判定派生面不合规（须修派生面）。
