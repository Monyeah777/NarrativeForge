# 标准目录 · 可引用卡（按问题形态）

> 本页由 `python scripts/geo_export.py --write` 生成，禁止手改。真源：`protocol/standards_catalog.json` + `protocol/standards_binding.json`。

- 覆盖：标准 **370** 条 · 本机可达 **332** · 不可达 **38** · 机构 **194** · 依赖边 **206**
- 分层：data 148 · eng 38 · form 29 · gov 71 · iface 84
- 可达性是**本机实测**（探针日期见每条），不可达条目照实标注、不假装可达。
- 每张卡回答一类问题，可直接被生成式引擎引用；数据源同主索引。

## 卡 1 · 哪些标准提供扩展点？

全 **370** 条标准均声明扩展点（`ext_points`），扩展点最多的 20 条：

- `http-semantics` · HTTP 语义（RFC 9110） · 扩展点 3：method-registry, field-name-registry, status-code-registry
- `acme` · ACME 证书签发自动化 · 扩展点 2：challenge-type, identifier-type
- `activitypub` · ActivityPub · 扩展点 2：activity-type-extension, extension-context
- `adbc` · ADBC 数据库访问接口 · 扩展点 2：driver-manager, statement-option
- `adsb` · ADS-B 广播式自动相关监视 · 扩展点 2：message-type, version-field
- `aicpa-soc2` · SOC 2 信任服务准则 · 扩展点 2：trust-services-category, criterion
- `ais-itdma` · AIS 船舶自动识别 · 扩展点 2：message-type, application-identifier
- `amqp10` · AMQP 1.0 消息协议 · 扩展点 2：performative-extension, type-encoding
- `archimate` · ArchiMate 3.2 企业架构建模 · 扩展点 2：specialization, exchange-format
- `arib-ttml` · ARIB 字幕/编成元数据 · 扩展点 2：profile, data-component
- `arrow` · Arrow 列式格式 · 扩展点 2：extension-type, metadata
- `arrow-flight-sql` · Arrow Flight SQL 协议 · 扩展点 2：command-type, extension-metadata
- `asciidoc` · AsciiDoc 标记语言 · 扩展点 2：macro-extension, block-extension
- `atag20` · ATAG 2.0 创作工具无障碍 · 扩展点 2：conformance-level, success-criterion-scope
- `autosar-someip` · SOME/IP 车载服务通信 · 扩展点 2：service-interface, eventgroup
- `avif` · AVIF 图像格式 · 扩展点 2：av1-item, extended-profile
- `avro` · Avro 规范 · 扩展点 2：schema-resolution, logical-type
- `bacnet` · BACnet 楼宇自动化 · 扩展点 2：proprietary-property, object-type-extension
- `bibframe` · BIBFRAME 书目框架 · 扩展点 2：profile, vocabulary-extension
- `bis-basel-iii` · 巴塞尔 III 资本框架 · 扩展点 2：approach-selection, national-discretion

## 卡 2 · 各层有哪些标准？

- **data** 148 条 → `docs/standards/layer-data.md`
- **eng** 38 条 → `docs/standards/layer-eng.md`
- **form** 29 条 → `docs/standards/layer-form.md`
- **gov** 71 条 → `docs/standards/layer-gov.md`
- **iface** 84 条 → `docs/standards/layer-iface.md`

## 卡 3 · 哪些标准被域包绑定、绑了多少次？

绑定总量 **1200**（70 条不同标准被引用；主锚=口径锚，辅锚=产出承载锚）。绑定最多的 20 条：

- `vega-lite` · 主锚 5 / 辅锚 364
- `w3c-tabular-data` · 主锚 95 / 辅锚 198
- `ietf-json-schema` · 主锚 63 / 辅锚 228
- `commonmark` · 主锚 70 / 辅锚 111
- `w3c-prov-o` · 主锚 69 / 辅锚 88
- `mermaid` · 主锚 4 / 辅锚 136
- `mlcommons-bench` · 主锚 110 / 辅锚 0
- `frictionless-table` · 主锚 85 / 辅锚 0
- `nist-ai-rmf` · 主锚 74 / 辅锚 0
- `cncf-otel-semconv` · 主锚 46 / 辅锚 27
- `w3c-epub33` · 主锚 60 / 辅锚 0
- `onnx` · 主锚 46 / 辅锚 0
- `common-criteria` · 主锚 41 / 辅锚 0
- `spdx-licenses` · 主锚 23 / 辅锚 15
- `gdpr` · 主锚 36 / 辅锚 0
- `frictionless-package` · 主锚 24 / 辅锚 0
- `owasp-llm` · 主锚 23 / 辅锚 0
- `cncf-cloudevents` · 主锚 5 / 辅锚 14
- `creativecommons` · 主锚 19 / 辅锚 0
- `oci-image` · 主锚 19 / 辅锚 0

## 卡 4 · 哪些标准本机不可达？（诚实披露）

共 **38** 条本机探测未达（不假装可达），逐条如下：

- `arib-ttml` · ARIB 字幕/编成元数据 · HTTP 403 · HTTPError: Forbidden
- `autosar-ap` · Adaptive Platform · HTTP 0 · URLError: <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify fai
- `autosar-someip` · SOME/IP 车载服务通信 · HTTP 0 · URLError: <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify fai
- `exif` · Exif 图像元数据 · HTTP 0 · URLError: <urlopen error [SSL: SSLV3_ALERT_HANDSHAKE_FAILURE] sslv3 alert handsh
- `council-europe-ai` · AI 框架公约 · HTTP 403 · HTTPError: Forbidden
- `bwf` · 广播 WAV（BWF） · HTTP 403 · HTTPError: Forbidden
- `ebucore` · EBUCore 媒体元数据 · HTTP 403 · HTTPError: Forbidden
- `onix` · ONIX 出版元数据 · HTTP 202 · 
- `eu-accessibility-act` · 欧洲无障碍法案 · HTTP 0 · URLError: <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify fai
- `fatf-recommendations` · FATF 反洗钱建议 · HTTP 403 · HTTPError: Forbidden
- `hipaa-security` · HIPAA 安全规则 · HTTP 403 · HTTPError: Forbidden
- `hl7-cda` · HL7 CDA 临床文档 · HTTP 202 · 
- `hl7-v2` · HL7 v2 消息 · HTTP 202 · 
- `adsb` · ADS-B 广播式自动相关监视 · HTTP 404 · HTTPError: Not Found
- `ipmi` · IPMI 服务器管理 · HTTP 403 · HTTPError: Forbidden
- `iso-8601` · 日期时间（含 8601-2 扩展） · HTTP 403 · HTTPError: Forbidden
- `iso20022` · ISO 20022 报文（可扩展元素） · HTTP 403 · HTTPError: Forbidden
- `pdf20` · PDF 2.0（ISO 32000-2） · HTTP 403 · HTTPError: Forbidden
- `sepa-iso20022` · ISO 20022 报文定义库 · HTTP 403 · HTTPError: Forbidden
- `iec-42001` · AI 管理体系 · HTTP 403 · HTTPError: Forbidden
- `iso-iec-25010` · SQuaRE 质量模型 · HTTP 403 · HTTPError: Forbidden
- `iso-iec-26511` · 术语工作（Terminology） · HTTP 403 · HTTPError: Forbidden
- `iso-iec-42010` · 架构描述 · HTTP 403 · HTTPError: Forbidden
- `iso15118` · ISO 15118 车充通信 · HTTP 403 · HTTPError: Forbidden
- `pdfa` · PDF/A 长期保存 · HTTP 403 · HTTPError: Forbidden
- `pdfua` · PDF/UA 无障碍 · HTTP 403 · HTTPError: Forbidden
- `bibframe` · BIBFRAME 书目框架 · HTTP 403 · HTTPError: Forbidden
- `marc21` · MARC 21 书目格式 · HTTP 403 · HTTPError: Forbidden
- `mets` · METS 封装元数据 · HTTP 403 · HTTPError: Forbidden
- `mods` · MODS 书目元数据 · HTTP 403 · HTTPError: Forbidden
- `premis` · PREMIS 保存元数据 · HTTP 403 · HTTPError: Forbidden
- `riff` · RIFF 容器 · HTTP 0 · URLError: <urlopen error [WinError 10054] 远程主机强迫关闭了一个现有的连接。>
- `opentype` · OpenType 字体 · HTTP 0 · URLError: <urlopen error [WinError 10054] 远程主机强迫关闭了一个现有的连接。>
- `iso4217-six` · ISO 4217 货币代码（维护机构版） · HTTP 0 · URLError: <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify fai
- `sunspec` · SunSpec 逆变器模型 · HTTP 403 · HTTPError: Forbidden
- `archimate` · ArchiMate 3.2 企业架构建模 · HTTP 401 · HTTPError: Unauthorized
- `togaf` · TOGAF 企业架构框架 · HTTP 401 · HTTPError: Unauthorized
- `unlocode` · UN/LOCODE 地点代码 · HTTP 403 · HTTPError: Forbidden
