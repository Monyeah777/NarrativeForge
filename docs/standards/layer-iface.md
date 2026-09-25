# 标准目录 · 层 iface（84 条）

> 本页由 `python scripts/geo_export.py --write` 生成，禁止手改。真源：`protocol/standards_catalog.json` + `protocol/standards_binding.json`。

- 覆盖：标准 **370** 条 · 本机可达 **332** · 不可达 **38** · 机构 **194** · 依赖边 **206**
- 分层：data 148 · eng 38 · form 29 · gov 71 · iface 84
- 可达性是**本机实测**（探针日期见每条），不可达条目照实标注、不假装可达。
- 本页为 `docs/standards/index.md` 的按层切片，锚点与主索引一致。

### `a2a`
- A2A 协议 · Linux Foundation · 层 iface · 可达 是（200 · 2026-09-24） · 扩展点 agent-card-extension · 绑定 主锚 10 / 辅锚 0 · https://a2a-protocol.org/latest/specification/

### `acme`
- ACME 证书签发自动化 · IETF · 层 iface · 可达 是（200 · 2026-09-24） · 扩展点 challenge-type, identifier-type · 绑定 主锚 0 / 辅锚 0 · https://www.rfc-editor.org/rfc/rfc8555

### `activitypub`
- ActivityPub · W3C · 层 iface · 可达 是（200 · 2026-09-24） · 扩展点 activity-type-extension, extension-context · 绑定 主锚 0 / 辅锚 0 · https://www.w3.org/TR/activitypub/

### `adsb`
- ADS-B 广播式自动相关监视 · ICAO · 层 iface · 可达 否（404 · 2026-09-24） · 扩展点 message-type, version-field · 绑定 主锚 0 / 辅锚 0 · https://www.icao.int/airnavigation/Pages/ADS-B.aspx

### `ais-itdma`
- AIS 船舶自动识别 · ITU · 层 iface · 可达 是（200 · 2026-09-24） · 扩展点 message-type, application-identifier · 绑定 主锚 0 / 辅锚 0 · https://www.itu.int/rec/R-REC-M.1371/en

### `amqp10`
- AMQP 1.0 消息协议 · OASIS · 层 iface · 可达 是（200 · 2026-09-24） · 扩展点 performative-extension, type-encoding · 绑定 主锚 0 / 辅锚 0 · https://docs.oasis-open.org/amqp/core/v1.0/os/amqp-core-overview-v1.0-os.html

### `autosar-ap`
- Adaptive Platform · AUTOSAR · 层 iface · 可达 否（0 · 2026-09-24） · 扩展点 manifest-extension · 绑定 主锚 0 / 辅锚 0 · https://www.autosar.org/

### `autosar-someip`
- SOME/IP 车载服务通信 · AUTOSAR · 层 iface · 可达 否（0 · 2026-09-24） · 扩展点 service-interface, eventgroup · 绑定 主锚 0 / 辅锚 0 · https://www.autosar.org/fileadmin/standards/R22-11/FO/AUTOSAR_SWS_SOMEIPServiceDiscoveryProtocol.pdf

### `bacnet`
- BACnet 楼宇自动化 · ASHRAE · 层 iface · 可达 是（200 · 2026-09-24） · 扩展点 proprietary-property, object-type-extension · 绑定 主锚 0 / 辅锚 0 · https://www.bacnet.org/

### `can-fd`
- CAN FD 车载总线 · ISO/CiA · 层 iface · 可达 是（200 · 2026-09-24） · 扩展点 can-id, signal-matrix · 绑定 主锚 0 / 辅锚 0 · https://www.can-cia.org/can-knowledge/

### `cim-iec61970`
- IEC 61970 CIM 电网模型 · IEC/UCA · 层 iface · 可达 是（200 · 2026-09-24） · 扩展点 profile, cim-extension · 绑定 主锚 0 / 辅锚 0 · https://www.ucaiug.org/

### `cncf-cloudevents`
- CloudEvents 1.0 · CNCF · 层 iface · 可达 是（200 · 2026-09-24） · 扩展点 extension-attribute · 绑定 主锚 5 / 辅锚 14 · https://github.com/cloudevents/spec/blob/main/cloudevents/spec.md

### `cncf-otel-otlp`
- OTLP 协议 · OpenTelemetry · 层 iface · 可达 是（200 · 2026-09-24） · 扩展点 proto-extension, http-json · 绑定 主锚 3 / 辅锚 0 · https://opentelemetry.io/docs/specs/otlp/

### `cni`
- CNI 容器网络接口 · CNCF · 层 iface · 可达 是（200 · 2026-09-24） · 扩展点 plugin-capability, option-field · 绑定 主锚 0 / 辅锚 0 · https://github.com/containernetworking/cni/blob/main/SPEC.md

### `covesa-vss`
- Vehicle Signal Specification · COVESA · 层 iface · 可达 是（200 · 2026-09-24） · 扩展点 overlay-extension · 绑定 主锚 4 / 辅锚 0 · https://covesa.global/

### `didcomm`
- DIDComm 消息协议 · DIF · 层 iface · 可达 是（200 · 2026-09-24） · 扩展点 message-type-registry, decorator · 绑定 主锚 0 / 辅锚 0 · https://identity.foundation/didcomm-messaging/spec/

### `fhir-shorthand`
- FHIR Shorthand（扩展定义语言） · HL7 · 层 iface · 可达 是（200 · 2026-09-24） · 扩展点 extension-definition · 绑定 主锚 0 / 辅锚 0 · https://hl7.org/fhir/uv/shorthand/

### `fido-ctap`
- CTAP 认证器协议 · FIDO Alliance · 层 iface · 可达 是（200 · 2026-09-24） · 扩展点 vendor-command, extension-map · 绑定 主锚 0 / 辅锚 0 · https://fidoalliance.org/specs/fido-v2.1-ps-20210615/fido-client-to-authenticator-protocol-v2.1-ps-20210615.html

### `gateway-api`
- Gateway API · Kubernetes SIG · 层 iface · 可达 是（200 · 2026-09-24） · 扩展点 extension-ref, policy-attachment · 绑定 主锚 0 / 辅锚 0 · https://gateway-api.sigs.k8s.io/

### `gnap`
- GNAP 授权协商 · IETF · 层 iface · 可达 是（200 · 2026-09-24） · 扩展点 grant-request-extension, interaction-mode · 绑定 主锚 0 / 辅锚 0 · https://www.rfc-editor.org/rfc/rfc9635

### `graphql`
- GraphQL SDL · GraphQL Foundation · 层 iface · 可达 是（200 · 2026-09-24） · 扩展点 directive-extension · 绑定 主锚 0 / 辅锚 0 · https://spec.graphql.org/October2021/

### `grpc`
- gRPC over HTTP/2 · CNCF/gRPC · 层 iface · 可达 是（200 · 2026-09-24） · 扩展点 custom-metadata, service-config · 绑定 主锚 0 / 辅锚 0 · https://github.com/grpc/grpc/blob/master/doc/PROTOCOL-HTTP2.md

### `hl7-fhir`
- FHIR（资源扩展机制） · HL7 · 层 iface · 可达 是（200 · 2026-09-24） · 扩展点 extension, profile-ig · 绑定 主锚 9 / 辅锚 0 · https://hl7.org/fhir/

### `http-caching`
- HTTP 缓存（RFC 9111） · IETF · 层 iface · 可达 是（200 · 2026-09-24） · 扩展点 cache-directive, field-extension · 绑定 主锚 0 / 辅锚 0 · https://www.rfc-editor.org/rfc/rfc9111

### `http-semantics`
- HTTP 语义（RFC 9110） · IETF · 层 iface · 可达 是（200 · 2026-09-24） · 扩展点 method-registry, field-name-registry, status-code-registry · 绑定 主锚 0 / 辅锚 0 · https://www.rfc-editor.org/rfc/rfc9110

### `ieee1815`
- IEEE 1815 DNP3 · IEEE · 层 iface · 可达 是（200 · 2026-09-24） · 扩展点 object-variation, function-code · 绑定 主锚 0 / 辅锚 0 · https://standards.ieee.org/ieee/1815/5324/

### `ietf-http`
- HTTP 语义 (RFC 9110) · IETF · 层 iface · 可达 是（200 · 2026-09-24） · 扩展点 extension-headers, content-negotiation · 绑定 主锚 0 / 辅锚 0 · https://www.rfc-editor.org/rfc/rfc9110.txt

### `ietf-problem`
- Problem Details (RFC 9457) · IETF · 层 iface · 可达 是（200 · 2026-09-24） · 扩展点 extension-members · 绑定 主锚 0 / 辅锚 0 · https://www.rfc-editor.org/rfc/rfc9457.txt

### `ietf-webpush`
- Web Push (RFC 8291) · IETF · 层 iface · 可达 是（200 · 2026-09-24） · 扩展点 header-registry · 绑定 主锚 0 / 辅锚 0 · https://www.rfc-editor.org/rfc/rfc8291.txt

### `ipmi`
- IPMI 服务器管理 · Intel · 层 iface · 可达 否（403 · 2026-09-24） · 扩展点 manufacturer-specific-command, sensor-type · 绑定 主锚 0 / 辅锚 0 · https://www.intel.com/content/www/us/en/products/docs/servers/ipmi/ipmi-home.html

### `iso15118`
- ISO 15118 车充通信 · ISO/IEC · 层 iface · 可达 否（403 · 2026-09-24） · 扩展点 application-protocol, certificate-profile · 绑定 主锚 0 / 辅锚 0 · https://www.iso.org/standard/77845.html

### `iso20022`
- ISO 20022 报文（可扩展元素） · ISO · 层 iface · 可达 否（403 · 2026-09-24） · 扩展点 message-definition-extension · 绑定 主锚 0 / 辅锚 0 · https://www.iso20022.org/iso-20022-message-definitions

### `jsonapi`
- JSON:API 1.1 · JSON:API · 层 iface · 可达 是（200 · 2026-09-24） · 扩展点 extension-member · 绑定 主锚 0 / 辅锚 0 · https://jsonapi.org/format/

### `jsonrpc`
- JSON-RPC 2.0 · JSON-RPC · 层 iface · 可达 是（200 · 2026-09-24） · 扩展点 extension-method · 绑定 主锚 0 / 辅锚 0 · https://www.jsonrpc.org/specification

### `k8s-crd`
- Kubernetes CRD/API 扩展 · CNCF · 层 iface · 可达 是（200 · 2026-09-24） · 扩展点 crd-versioning, admission · 绑定 主锚 2 / 辅锚 0 · https://kubernetes.io/docs/concepts/extend-kubernetes/api-extension/custom-resources/

### `kafka-protocol`
- Kafka 线协议 · Apache · 层 iface · 可达 是（200 · 2026-09-24） · 扩展点 api-key-version, flexible-version · 绑定 主锚 0 / 辅锚 0 · https://kafka.apache.org/protocol.html

### `lsp`
- Language Server Protocol · Microsoft · 层 iface · 可达 是（200 · 2026-09-24） · 扩展点 custom-method, capability · 绑定 主锚 2 / 辅锚 0 · https://microsoft.github.io/language-server-protocol/

### `matrix`
- Matrix 联邦协议 · Matrix.org Foundation · 层 iface · 可达 是（200 · 2026-09-24） · 扩展点 m-scoped-extension, room-version · 绑定 主锚 0 / 辅锚 0 · https://spec.matrix.org/latest/

### `matter`
- Matter 智能家居 · Connectivity Standards Alliance · 层 iface · 可达 是（200 · 2026-09-24） · 扩展点 cluster-extension, device-type · 绑定 主锚 0 / 辅锚 0 · https://csa-iot.org/all-solutions/matter/

### `mavlink`
- MAVLink 无人系统协议 · MAVLink 社区 · 层 iface · 可达 是（200 · 2026-09-24） · 扩展点 custom-message, message-id-range · 绑定 主锚 0 / 辅锚 0 · https://mavlink.io/en/

### `mcp`
- Model Context Protocol · Anthropic/MCP · 层 iface · 可达 是（200 · 2026-09-24） · 扩展点 server-capability, extension-method · 绑定 主锚 14 / 辅锚 0 · https://modelcontextprotocol.io/specification/2025-06-18

### `modbus`
- Modbus 通信 · Modbus Organization · 层 iface · 可达 是（200 · 2026-09-24） · 扩展点 function-code-extension, exception-code · 绑定 主锚 0 / 辅锚 0 · https://modbus.org/

### `mqtt5`
- MQTT 5.0 · OASIS · 层 iface · 可达 是（200 · 2026-09-24） · 扩展点 user-property, reason-code · 绑定 主锚 0 / 辅锚 0 · https://docs.oasis-open.org/mqtt/mqtt/v5.0/mqtt-v5.0.html

### `nmea0183`
- NMEA 0183 航海语句 · NMEA · 层 iface · 可达 是（200 · 2026-09-24） · 扩展点 sentence-extension, proprietary-sentence · 绑定 主锚 0 / 辅锚 0 · https://www.nmea.org/standards/

### `oasis-asyncapi`
- AsyncAPI 3.0 · AsyncAPI · 层 iface · 可达 是（200 · 2026-09-24） · 扩展点 extension, bindings · 绑定 主锚 0 / 辅锚 0 · https://www.asyncapi.com/docs/reference/specification/v3.0.0

### `oasis-odata`
- OData v4.01 · OASIS · 层 iface · 可达 是（200 · 2026-09-24） · 扩展点 vocabulary-extensions, annotations · 绑定 主锚 0 / 辅锚 0 · https://docs.oasis-open.org/odata/odata/v4.01/odata-v4.01-part1-protocol.html

### `oasis-openapi`
- OpenAPI 3.1 · OpenAPI Initiative · 层 iface · 可达 是（200 · 2026-09-24） · 扩展点 x-extension, specification-extension · 绑定 主锚 15 / 辅锚 3 · https://spec.openapis.org/oas/v3.1.0

### `oasis-sarif`
- SARIF 2.1.0 · OASIS · 层 iface · 可达 是（200 · 2026-09-24） · 扩展点 property-bag, taxonomies · 绑定 主锚 7 / 辅锚 0 · https://docs.oasis-open.org/sarif/sarif/v2.1.0/sarif-v2.1.0.html

### `oauth2`
- OAuth 2.0 授权框架 · IETF · 层 iface · 可达 是（200 · 2026-09-24） · 扩展点 grant-type-registry, token-type-registry · 绑定 主锚 0 / 辅锚 0 · https://www.rfc-editor.org/rfc/rfc6749

### `oci-distribution`
- OCI 镜像分发 · Open Container Initiative · 层 iface · 可达 是（200 · 2026-09-24） · 扩展点 media-type, api-extension · 绑定 主锚 0 / 辅锚 0 · https://github.com/opencontainers/distribution-spec

### `oci-image`
- 镜像清单 · OCI · 层 iface · 可达 是（200 · 2026-09-24） · 扩展点 annotation, media-type · 绑定 主锚 19 / 辅锚 0 · https://github.com/opencontainers/image-spec/blob/main/manifest.md

### `ocpp`
- OCPP 充电桩协议 · Open Charge Alliance · 层 iface · 可达 是（200 · 2026-09-24） · 扩展点 vendor-extension, profile · 绑定 主锚 0 / 辅锚 0 · https://openchargealliance.org/protocols/open-charge-point-protocol/

### `oidc`
- OpenID Connect Core · OpenID Foundation · 层 iface · 可达 是（200 · 2026-09-24） · 扩展点 claim-extension, auth-method · 绑定 主锚 0 / 辅锚 0 · https://openid.net/specs/openid-connect-core-1_0.html

### `onnx`
- ONNX（opset 扩展） · Linux Foundation · 层 iface · 可达 是（200 · 2026-09-24） · 扩展点 opset-version, function-op · 绑定 主锚 46 / 辅锚 0 · https://github.com/onnx/onnx/blob/main/docs/IR.md

### `opcua`
- OPC UA 工业互联 · OPC Foundation · 层 iface · 可达 是（200 · 2026-09-24） · 扩展点 companion-specification, information-model-extension · 绑定 主锚 2 / 辅锚 0 · https://reference.opcfoundation.org/

### `opcua-security`
- OPC UA 安全策略 · OPC Foundation · 层 iface · 可达 是（200 · 2026-09-24） · 扩展点 security-policy, certificate-profile · 绑定 主锚 0 / 辅锚 0 · https://reference.opcfoundation.org/Core/Part2/v105/docs/

### `openadr`
- OpenADR 需求响应 · OpenADR Alliance · 层 iface · 可达 是（200 · 2026-09-24） · 扩展点 profile, event-extension · 绑定 主锚 0 / 辅锚 0 · https://openadr.org/

### `opengis-wms`
- WMS 实现规范（可扩展） · OGC · 层 iface · 可达 是（200 · 2026-09-24） · 扩展点 vendor-parameters · 绑定 主锚 0 / 辅锚 0 · https://www.ogc.org/standard/wms/

### `openid-federation`
- OpenID Federation · OpenID Foundation · 层 iface · 可达 是（200 · 2026-09-24） · 扩展点 entity-statement, metadata-policy · 绑定 主锚 0 / 辅锚 0 · https://openid.net/specs/openid-federation-1_0.html

### `openid4vci`
- OpenID for Verifiable Credential Issuance · OpenID Foundation · 层 iface · 可达 是（200 · 2026-09-24） · 扩展点 credential-format, extension-parameter · 绑定 主锚 0 / 辅锚 0 · https://openid.net/specs/openid-4-verifiable-credential-issuance-1_0.html

### `pkce`
- PKCE 授权码保护 · IETF · 层 iface · 可达 是（200 · 2026-09-24） · 扩展点 challenge-method · 绑定 主锚 0 / 辅锚 0 · https://www.rfc-editor.org/rfc/rfc7636

### `protobuf`
- Protocol Buffers proto3 · Google · 层 iface · 可达 是（200 · 2026-09-24） · 扩展点 reserved-fields, custom-options · 绑定 主锚 0 / 辅锚 0 · https://protobuf.dev/programming-guides/proto3/

### `quic`
- QUIC 传输 · IETF · 层 iface · 可达 是（200 · 2026-09-24） · 扩展点 transport-parameter, frame-type · 绑定 主锚 0 / 辅锚 0 · https://www.rfc-editor.org/rfc/rfc9000

### `redfish`
- Redfish 系统管理 · DMTF · 层 iface · 可达 是（200 · 2026-09-24） · 扩展点 oem-extension, schema-registry · 绑定 主锚 0 / 辅锚 0 · https://www.dmtf.org/standards/redfish

### `ros2-interface`
- ROS 2 接口定义 · Open Robotics · 层 iface · 可达 是（200 · 2026-09-24） · 扩展点 idl-message, qos-profile · 绑定 主锚 0 / 辅锚 0 · https://docs.ros.org/en/rolling/Concepts/Basic/About-Interfaces.html

### `saml2`
- SAML 2.0 断言 · OASIS · 层 iface · 可达 是（200 · 2026-09-24） · 扩展点 attribute-profile, extension-schema · 绑定 主锚 0 / 辅锚 0 · https://docs.oasis-open.org/security/saml/v2.0/

### `scim2`
- SCIM 2.0 跨域身份管理 · IETF · 层 iface · 可达 是（200 · 2026-09-24） · 扩展点 schema-extension, resource-type · 绑定 主锚 0 / 辅锚 0 · https://www.rfc-editor.org/rfc/rfc7644

### `sd-jwt`
- SD-JWT 选择性披露 · IETF · 层 iface · 可达 是（200 · 2026-09-24） · 扩展点 disclosure-frame, kb-jwt · 绑定 主锚 0 / 辅锚 0 · https://datatracker.ietf.org/doc/draft-ietf-oauth-selective-disclosure-jwt/

### `sepa-iso20022`
- ISO 20022 报文定义库 · ISO · 层 iface · 可达 否（403 · 2026-09-24） · 扩展点 message-extension · 绑定 主锚 0 / 辅锚 0 · https://www.iso20022.org/iso-20022-message-definitions

### `sparql11`
- SPARQL 1.1 Protocol · W3C · 层 iface · 可达 是（200 · 2026-09-24） · 扩展点 extension-function · 绑定 主锚 0 / 辅锚 0 · https://www.w3.org/TR/sparql11-protocol/

### `spiffe`
- SPIFFE 工作负载身份 · CNCF · 层 iface · 可达 是（200 · 2026-09-24） · 扩展点 svid-extension, trust-domain · 绑定 主锚 0 / 辅锚 0 · https://spiffe.io/docs/latest/spiffe-about/spiffe-concepts/

### `sse-html`
- Server-Sent Events · WHATWG · 层 iface · 可达 是（200 · 2026-09-24） · 扩展点 event-field, retry-semantics · 绑定 主锚 0 / 辅锚 0 · https://html.spec.whatwg.org/multipage/server-sent-events.html

### `sunspec`
- SunSpec 逆变器模型 · SunSpec Alliance · 层 iface · 可达 否（403 · 2026-09-24） · 扩展点 model-point-extension, profile · 绑定 主锚 0 / 辅锚 0 · https://sunspec.org/specifications/

### `tls13`
- TLS 1.3 · IETF · 层 iface · 可达 是（200 · 2026-09-24） · 扩展点 extension-type, cipher-suite-registry · 绑定 主锚 0 / 辅锚 0 · https://www.rfc-editor.org/rfc/rfc8446

### `uma2`
- UMA 2.0 用户管理访问 · Kantara Initiative · 层 iface · 可达 是（200 · 2026-09-24） · 扩展点 grant-extension, scope-format · 绑定 主锚 0 / 辅锚 0 · https://docs.kantarainitiative.org/uma/wg/rec-oauth-uma-grant-2.0.html

### `urdf`
- URDF 机器人描述 · ROS 社区 · 层 iface · 可达 是（200 · 2026-09-24） · 扩展点 extension-tag, gazebo-tag · 绑定 主锚 0 / 辅锚 0 · https://docs.ros.org/en/rolling/Tutorials/Intermediate/URDF/URDF-Main.html

### `vc-data-integrity`
- 可验证凭证数据完整性 · W3C · 层 iface · 可达 是（200 · 2026-09-24） · 扩展点 cryptosuite, proof-purpose · 绑定 主锚 0 / 辅锚 0 · https://www.w3.org/TR/vc-data-integrity/

### `w3c-wot`
- Web of Things Thing Description · W3C · 层 iface · 可达 是（200 · 2026-09-24） · 扩展点 extension-vocabulary, thing-model · 绑定 主锚 1 / 辅锚 0 · https://www.w3.org/TR/wot-thing-description11/

### `webauthn`
- WebAuthn · W3C · 层 iface · 可达 是（200 · 2026-09-24） · 扩展点 extension-identifier, authenticator-attachment · 绑定 主锚 0 / 辅锚 0 · https://www.w3.org/TR/webauthn-3/

### `webidl`
- Web IDL · WHATWG · 层 iface · 可达 是（200 · 2026-09-24） · 扩展点 extended-attribute · 绑定 主锚 0 / 辅锚 0 · https://webidl.spec.whatwg.org/

### `webmention`
- Webmention · W3C · 层 iface · 可达 是（200 · 2026-09-24） · 扩展点 endpoint-discovery, vouch-extension · 绑定 主锚 0 / 辅锚 0 · https://www.w3.org/TR/webmention/

### `websocket`
- WebSocket 协议 · IETF · 层 iface · 可达 是（200 · 2026-09-24） · 扩展点 extension-negotiation, subprotocol · 绑定 主锚 0 / 辅锚 0 · https://www.rfc-editor.org/rfc/rfc6455

### `wsdl20`
- WSDL 2.0 · W3C · 层 iface · 可达 是（200 · 2026-09-24） · 扩展点 feature-extension · 绑定 主锚 0 / 辅锚 0 · https://www.w3.org/TR/wsdl20/

### `xmpp`
- XMPP 核心 · IETF · 层 iface · 可达 是（200 · 2026-09-24） · 扩展点 xep-extension, stanza-extension · 绑定 主锚 0 / 辅锚 0 · https://www.rfc-editor.org/rfc/rfc6120
