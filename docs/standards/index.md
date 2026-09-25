# 标准目录 · 可引用索引（GEO 出口）

> 本页由 `python scripts/geo_export.py --write` 生成，禁止手改。真源：`protocol/standards_catalog.json` + `protocol/standards_binding.json`。

- 覆盖：标准 **370** 条 · 本机可达 **332** · 不可达 **38** · 机构 **194** · 依赖边 **206**
- 分层：data 148 · eng 38 · form 29 · gov 71 · iface 84
- 可达性是**本机实测**（探针日期见每条），不可达条目照实标注、不假装可达。
- 每条标准一个稳定锚：`#<id>`（如 `docs/standards/index.md#onnx`）。

### `adbc`
- ADBC 数据库访问接口 · Apache · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 driver-manager, statement-option · 绑定 主锚 0 / 辅锚 0 · https://arrow.apache.org/adbc/

### `arib-ttml`
- ARIB 字幕/编成元数据 · ARIB · 层 data · 可达 否（403 · 2026-09-24） · 扩展点 profile, data-component · 绑定 主锚 0 / 辅锚 0 · https://www.arib.or.jp/english/std_tr/broadcasting/

### `arrow`
- Arrow 列式格式 · Apache · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 extension-type, metadata · 绑定 主锚 3 / 辅锚 0 · https://arrow.apache.org/docs/format/Columnar.html

### `arrow-flight-sql`
- Arrow Flight SQL 协议 · Apache · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 command-type, extension-metadata · 绑定 主锚 0 / 辅锚 0 · https://arrow.apache.org/docs/format/FlightSql.html

### `avif`
- AVIF 图像格式 · AOMedia · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 av1-item, extended-profile · 绑定 主锚 0 / 辅锚 0 · https://aomedia.org/specifications/avif/

### `avro`
- Avro 规范 · Apache · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 schema-resolution, logical-type · 绑定 主锚 0 / 辅锚 0 · https://avro.apache.org/docs/1.11.1/specification/

### `bibframe`
- BIBFRAME 书目框架 · Library of Congress · 层 data · 可达 否（403 · 2026-09-24） · 扩展点 profile, vocabulary-extension · 绑定 主锚 0 / 辅锚 0 · https://www.loc.gov/bibframe/

### `bson`
- BSON 二进制文档 · MongoDB · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 element-type, subtype · 绑定 主锚 0 / 辅锚 0 · https://bsonspec.org/spec.html

### `bwf`
- 广播 WAV（BWF） · EBU · 层 data · 可达 否（403 · 2026-09-24） · 扩展点 bext-chunk, axml-chunk · 绑定 主锚 0 / 辅锚 0 · https://tech.ebu.ch/publications/r98

### `cbor`
- CBOR (RFC 8949) · IETF · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 tag-registry · 绑定 主锚 0 / 辅锚 0 · https://www.rfc-editor.org/rfc/rfc8949.txt

### `cddl`
- CDDL 数据定义语言 · IETF · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 control-operator, socket-extension · 绑定 主锚 0 / 辅锚 0 · https://www.rfc-editor.org/rfc/rfc8610

### `citygml`
- CityGML 城市模型 · OGC · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 ade-extension, lod-level · 绑定 主锚 0 / 辅锚 0 · https://www.ogc.org/standards/citygml/

### `cityjson`
- CityJSON · CityJSON · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 extension, metadata-extension · 绑定 主锚 0 / 辅锚 0 · https://www.cityjson.org/specs/

### `cog`
- 云优化 GeoTIFF · COG 社区 · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 overview-structure, internal-tiling · 绑定 主锚 0 / 辅锚 0 · https://www.cogeo.org/

### `cose`
- COSE 签名与加密 · IETF · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 algorithm-registry, header-parameter · 绑定 主锚 0 / 辅锚 0 · https://www.rfc-editor.org/rfc/rfc9052

### `cpe`
- CPE 平台枚举 · NIST · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 well-formed-name, uri-binding · 绑定 主锚 0 / 辅锚 0 · https://nvd.nist.gov/products/cpe

### `crossref-schema`
- Crossref 元数据 schema · Crossref · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 schema-version, deposit-extension · 绑定 主锚 0 / 辅锚 0 · https://www.crossref.org/documentation/schema-library/

### `cve`
- CVE 漏洞编号 · CVE Program/MITRE · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 cve-id-block, cna-rules · 绑定 主锚 0 / 辅锚 0 · https://www.cve.org/

### `cvss`
- CVSS 严重度评分 · FIRST · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 metric-group, supplemental-metric · 绑定 主锚 0 / 辅锚 0 · https://www.first.org/cvss/v4-0/

### `datex-ii`
- DATEX II 交通数据 · EU/CEN · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 profile, extension-class · 绑定 主锚 0 / 辅锚 0 · https://datex2.eu/

### `dcat`
- DCAT 数据集目录词汇 · W3C · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 profile-class, property-extension · 绑定 主锚 0 / 辅锚 0 · https://www.w3.org/TR/vocab-dcat-3/

### `ddi`
- DDI 社会调查元数据 · DDI Alliance · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 lifecycle-module, controlled-vocabulary · 绑定 主锚 0 / 辅锚 0 · https://ddialliance.org/

### `delta-lake`
- Delta Lake 事务协议 · Linux Foundation · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 protocol-version, table-feature · 绑定 主锚 0 / 辅锚 0 · https://github.com/delta-io/delta/blob/master/PROTOCOL.md

### `dicom`
- DICOM 标准 · DICOM · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 private-attributes, supplement · 绑定 主锚 2 / 辅锚 0 · https://www.dicomstandard.org/

### `dicomweb`
- DICOMweb 服务 · DICOM/NEMA · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 resource-path, media-type · 绑定 主锚 0 / 辅锚 0 · https://www.dicomstandard.org/using/dicomweb

### `doi-handbook`
- DOI 标识手册 · DOI Foundation · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 prefix-suffix, metadata-kernel · 绑定 主锚 0 / 辅锚 0 · https://www.doi.org/the-identifier/resources/handbook/

### `dqv`
- DQV 数据质量词汇 · W3C · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 quality-dimension, metric-extension · 绑定 主锚 0 / 辅锚 0 · https://www.w3.org/TR/vocab-dqv/

### `dsse`
- DSSE 签名信封 · Secure Systems Lab · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 payload-type, signature-envelope · 绑定 主锚 0 / 辅锚 0 · https://github.com/secure-systems-lab/dsse/blob/master/protocol.md

### `dublin-core`
- 都柏林核心元数据 · DCMI · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 encoding-scheme, application-profile · 绑定 主锚 0 / 辅锚 0 · https://www.dublincore.org/specifications/dublin-core/dcmi-terms/

### `ebucore`
- EBUCore 媒体元数据 · EBU · 层 data · 可达 否（403 · 2026-09-24） · 扩展点 profile, extension-vocabulary · 绑定 主锚 0 / 辅锚 0 · https://tech.ebu.ch/publications/ebucore

### `exif`
- Exif 图像元数据 · CIPA · 层 data · 可达 否（0 · 2026-09-24） · 扩展点 tag-extension, makernote · 绑定 主锚 0 / 辅锚 0 · https://www.cipa.jp/std/documents/e/DC-X008-Translation-2019-E.pdf

### `ffv1`
- FFV1 无损视频编码 · IETF · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 version-slot, micro-version · 绑定 主锚 0 / 辅锚 0 · https://www.rfc-editor.org/rfc/rfc9043

### `fits`
- FITS 天文数据 · NASA/IAU · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 keyword-extension, convention · 绑定 主锚 0 / 辅锚 0 · https://fits.gsfc.nasa.gov/fits_standard.html

### `flac`
- FLAC 无损音频 · Xiph.Org · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 metadata-block-type, application-block · 绑定 主锚 0 / 辅锚 0 · https://xiph.org/flac/format.html

### `frictionless-package`
- Data Package · Frictionless · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 profile, resource-extension · 绑定 主锚 24 / 辅锚 0 · https://specs.frictionlessdata.io/data-package/

### `frictionless-table`
- Table Schema · Frictionless · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 custom-constraint, profile · 绑定 主锚 85 / 辅锚 0 · https://specs.frictionlessdata.io/table-schema/

### `gbfs`
- GBFS 共享出行 · MobilityData · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 versioned-endpoint, extension-field · 绑定 主锚 0 / 辅锚 0 · https://github.com/MobilityData/gbfs/blob/master/gbfs.md

### `geojson`
- GeoJSON · IETF · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 foreign-member, bbox · 绑定 主锚 0 / 辅锚 0 · https://www.rfc-editor.org/rfc/rfc7946

### `geotiff`
- GeoTIFF 地理标签 · OGC · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 geo-key, citation · 绑定 主锚 0 / 辅锚 0 · https://www.ogc.org/standards/geotiff/

### `gml`
- GML 地理标记语言 · OGC · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 application-schema, profile · 绑定 主锚 0 / 辅锚 0 · https://www.ogc.org/standards/gml/

### `gpx`
- GPX 轨迹交换 · TopoGrafix/OGC · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 extension-schema, wpt-type · 绑定 主锚 0 / 辅锚 0 · https://www.topografix.com/gpx.asp

### `gs1-epcis`
- EPCIS 供应链事件 · GS1 · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 event-type-extension, jsonld-context · 绑定 主锚 0 / 辅锚 0 · https://ref.gs1.org/standards/epcis/

### `gtfs`
- GTFS 公共交通静态数据 · MobilityData · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 proposal-process, agency-extension · 绑定 主锚 0 / 辅锚 0 · https://gtfs.org/documentation/schedule/reference/

### `gtfs-rt`
- GTFS-Realtime · MobilityData · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 experimental-field, extension-attribute · 绑定 主锚 0 / 辅锚 0 · https://gtfs.org/documentation/realtime/reference/

### `hdf5`
- HDF5 层级数据格式 · HDF Group · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 filter-pipeline, user-block · 绑定 主锚 0 / 辅锚 0 · https://support.hdfgroup.org/documentation/hdf5/latest/_f_m_t3.html

### `heif`
- HEIF 图像容器 · ISO/IEC · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 item-property, derived-item · 绑定 主锚 0 / 辅锚 0 · https://nokiatech.github.io/heif/

### `hl7-cda`
- HL7 CDA 临床文档 · HL7 · 层 data · 可达 否（202 · 2026-09-24） · 扩展点 template-id, section-extension · 绑定 主锚 0 / 辅锚 0 · http://www.hl7.org/implement/standards/product_brief.cfm?product_id=7

### `hl7-v2`
- HL7 v2 消息 · HL7 · 层 data · 可达 否（202 · 2026-09-24） · 扩展点 z-segment, table-extension · 绑定 主锚 0 / 辅锚 0 · https://www.hl7.org/implement/standards/product_brief.cfm?product_id=185

### `hudi`
- Hudi 表格式 · Apache · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 table-type, metadata-payload · 绑定 主锚 0 / 辅锚 0 · https://hudi.apache.org/docs/table_types/

### `iana-media-types`
- 媒体类型注册表 · IANA · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 registry-policy, suffix-tree · 绑定 主锚 0 / 辅锚 0 · https://www.iana.org/assignments/media-types/media-types.xhtml

### `iana-registries`
- IANA 协议注册表 · IANA · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 registry-policy, registration-template · 绑定 主锚 0 / 辅锚 0 · https://www.iana.org/assignments

### `icc`
- ICC 色彩特性文件 · ICC · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 tag-type, private-tag · 绑定 主锚 0 / 辅锚 0 · https://www.color.org/specification/ICC.1-2022-05.pdf

### `iceberg`
- Iceberg 表规范 · Apache · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 table-metadata-version, format-version · 绑定 主锚 0 / 辅锚 0 · https://iceberg.apache.org/spec/

### `ieee-754`
- 浮点运算标准 · IEEE · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 format-extension · 绑定 主锚 4 / 辅锚 0 · https://standards.ieee.org/ieee/754/6210/

### `ietf-ixdtf`
- IXDTF (RFC 9557) · IETF · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 annotation-suffix · 绑定 主锚 0 / 辅锚 6 · https://www.rfc-editor.org/rfc/rfc9557.txt

### `ietf-json`
- JSON (RFC 8259) · IETF · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 member-extension · 绑定 主锚 0 / 辅锚 0 · https://www.rfc-editor.org/rfc/rfc8259.txt

### `ietf-json-schema`
- JSON Schema 2020-12 · IETF/JSON Schema · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 vocabulary, format-annotation · 绑定 主锚 63 / 辅锚 228 · https://json-schema.org/draft/2020-12/json-schema-core

### `ietf-nip-19`
- NIP-19 编码（可扩展前缀） · IETF · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 prefix-registry · 绑定 主锚 0 / 辅锚 0 · https://www.rfc-editor.org/rfc/rfc9457.txt

### `ifc`
- IFC 建筑信息模型 · buildingSMART · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 property-set, ifc-extension-schema · 绑定 主锚 0 / 辅锚 0 · https://standards.buildingsmart.org/IFC/RELEASE/IFC4/ADD2_TC1/HTML/

### `iptc-photometadata`
- IPTC 图像元数据 · IPTC · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 property-extension, digitalsourcetype · 绑定 主锚 0 / 辅锚 0 · https://iptc.org/std/photometadata/specification/IPTC-PhotoMetadata

### `iso-8601`
- 日期时间（含 8601-2 扩展） · ISO · 层 data · 可达 否（403 · 2026-09-24） · 扩展点 interval-extension · 绑定 主锚 0 / 辅锚 0 · https://www.iso.org/standard/70907.html

### `iso-iec-26511`
- 术语工作（Terminology） · ISO/IEC · 层 data · 可达 否（403 · 2026-09-24） · 扩展点 concept-relation · 绑定 主锚 0 / 辅锚 0 · https://www.iso.org/standard/43122.html

### `iso10383`
- ISO 10383 MIC · ISO · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 code-list · 绑定 主锚 3 / 辅锚 0 · https://www.iso20022.org/market-identifier-codes

### `iso4217-six`
- ISO 4217 货币代码（维护机构版） · SIX Group · 层 data · 可达 否（0 · 2026-09-24） · 扩展点 currency-code, minor-unit · 绑定 主锚 0 / 辅锚 0 · https://www.six-group.com/en/products-services/financial-information/data-standards.html

### `isobmff`
- ISO 基媒体文件格式（ISOBMFF） · ISO/IEC · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 box-type-registry, brand-registry · 绑定 主锚 0 / 辅锚 0 · https://mp4ra.org/

### `jats`
- JATS 期刊文章标签集 · NLM/NISO · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 tag-set-variant, custom-element · 绑定 主锚 0 / 辅锚 0 · https://jats.nlm.nih.gov/

### `jose`
- JOSE 签名与加密（JWS/JWE） · IETF · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 algorithm-registry, header-parameter · 绑定 主锚 0 / 辅锚 0 · https://www.rfc-editor.org/rfc/rfc7515

### `jpeg-xl`
- JPEG XL · JPEG · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 signalling-flag, box-extension · 绑定 主锚 0 / 辅锚 0 · https://jpeg.org/jpegxl/

### `json-merge-patch`
- JSON Merge Patch · IETF · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 member-semantics · 绑定 主锚 0 / 辅锚 0 · https://www.rfc-editor.org/rfc/rfc7386

### `json-patch`
- JSON Patch 差分 · IETF · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 operation-set · 绑定 主锚 0 / 辅锚 0 · https://www.rfc-editor.org/rfc/rfc6902

### `json-pointer`
- JSON Pointer 定位 · IETF · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 escape-sequence · 绑定 主锚 0 / 辅锚 0 · https://www.rfc-editor.org/rfc/rfc6901

### `jsonlines`
- JSON Lines · jsonlines.org · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 record-extension · 绑定 主锚 0 / 辅锚 0 · https://jsonlines.org/

### `jsonpath`
- JSONPath 查询 · IETF · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 function-extension, segment-selector · 绑定 主锚 0 / 辅锚 0 · https://www.rfc-editor.org/rfc/rfc9535

### `jwk`
- JWK 密钥表示 · IETF · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 key-type, key-parameter · 绑定 主锚 0 / 辅锚 0 · https://www.rfc-editor.org/rfc/rfc7517

### `jwt`
- JWT 令牌 · IETF · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 claim-registry · 绑定 主锚 0 / 辅锚 0 · https://www.rfc-editor.org/rfc/rfc7519

### `khronos-gltf`
- glTF · Khronos · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 extension-mechanism, vendor-extensions · 绑定 主锚 5 / 辅锚 0 · https://www.khronos.org/gltf/

### `las`
- LAS 点云格式 · ASPRS/OGC · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 point-data-record-format, vlr · 绑定 主锚 0 / 辅锚 0 · https://www.ogc.org/standards/las/

### `loinc`
- LOINC 检验编码 · Regenstrief · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 answer-list, loinc-part · 绑定 主锚 0 / 辅锚 0 · https://loinc.org/kb/

### `marc21`
- MARC 21 书目格式 · Library of Congress · 层 data · 可达 否（403 · 2026-09-24） · 扩展点 field-9xx-local, subfield-extension · 绑定 主锚 0 / 辅锚 0 · https://www.loc.gov/marc/

### `matroska`
- Matroska 容器 · Matroska · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 element-extension, codec-mapping · 绑定 主锚 0 / 辅锚 0 · https://www.matroska.org/technical/elements.html

### `mets`
- METS 封装元数据 · Library of Congress · 层 data · 可达 否（403 · 2026-09-24） · 扩展点 profile, extension-schema · 绑定 主锚 0 / 辅锚 0 · https://www.loc.gov/standards/mets/

### `mitre-attack`
- ATT&CK 对抗战术库 · MITRE · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 technique-id, data-source · 绑定 主锚 0 / 辅锚 0 · https://attack.mitre.org/

### `mlcommons-croissant`
- Croissant 数据集元数据 · MLCommons · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 additional-property · 绑定 主锚 17 / 辅锚 0 · https://docs.mlcommons.org/croissant/docs/croissant-spec.html

### `mods`
- MODS 书目元数据 · Library of Congress · 层 data · 可达 否（403 · 2026-09-24） · 扩展点 extension-schema, role-term · 绑定 主锚 0 / 辅锚 0 · https://www.loc.gov/standards/mods/

### `msgpack`
- MessagePack 二进制序列化 · MessagePack · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 extension-type · 绑定 主锚 0 / 辅锚 0 · https://github.com/msgpack/msgpack/blob/master/spec.md

### `netcdf`
- NetCDF 科学数据 · Unidata · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 convention-attribute, group-hierarchy · 绑定 主锚 0 / 辅锚 0 · https://docs.unidata.ucar.edu/nug/current/

### `netex`
- NeTEx 公共交通网络 · CEN · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 profile, frame-extension · 绑定 主锚 0 / 辅锚 0 · https://netex-cen.eu/

### `oasis-xlf`
- XLIFF 2.1 · OASIS · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 module-extension · 绑定 主锚 0 / 辅锚 0 · https://docs.oasis-open.org/xliff/xliff-core/v2.1/os/xliff-core-v2.1-os.html

### `ogc-3dtiles`
- 3D Tiles · OGC · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 extension-mechanism · 绑定 主锚 0 / 辅锚 0 · https://docs.ogc.org/cs/22-025r4/22-025r4.html

### `omop-cdm`
- OMOP 通用数据模型 · OHDSI · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 vocabulary-mapping, era-extension · 绑定 主锚 0 / 辅锚 0 · https://ohdsi.github.io/CommonDataModel/

### `onix`
- ONIX 出版元数据 · EDItEUR · 层 data · 可达 否（202 · 2026-09-24） · 扩展点 codelist-extension, block-extension · 绑定 主锚 0 / 辅锚 0 · https://www.editeur.org/93/Release-3.0-Downloads/

### `onvif-ucum`
- 统一计量单位代码 · UCUM · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 unit-extension · 绑定 主锚 1 / 辅锚 0 · https://ucum.org/ucum

### `opendrive`
- OpenDRIVE 道路网络 · ASAM · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 user-defined-attribute, extension-registry · 绑定 主锚 0 / 辅锚 0 · https://www.asam.net/standards/

### `openehr`
- openEHR 临床信息模型 · openEHR · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 archetype, template-constraint · 绑定 主锚 0 / 辅锚 0 · https://specifications.openehr.org/

### `openexr`
- OpenEXR 图像 · Academy Software Foundation · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 attribute-type, part-extension · 绑定 主锚 0 / 辅锚 0 · https://openexr.com/en/latest/

### `opengeospatial`
- OGC 标准（含 GeoJSON/3D Tiles） · OGC · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 extension-package · 绑定 主锚 7 / 辅锚 0 · https://www.ogc.org/standards/

### `openlineage`
- OpenLineage 血缘事件 · OpenLineage/LF · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 facet-extension, custom-model · 绑定 主锚 0 / 辅锚 0 · https://openlineage.io/docs/spec/object-model/

### `opentype`
- OpenType 字体 · Microsoft/Adobe · 层 data · 可达 否（0 · 2026-09-24） · 扩展点 table-registry, variation-axis · 绑定 主锚 0 / 辅锚 0 · https://learn.microsoft.com/en-us/typography/opentype/spec/

### `opus`
- Opus 音频编码 · IETF · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 frame-packing, opus-channel-mapping · 绑定 主锚 0 / 辅锚 0 · https://www.rfc-editor.org/rfc/rfc6716

### `orc`
- ORC 列式存储格式 · Apache · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 writer-version, postscript-metadata · 绑定 主锚 0 / 辅锚 0 · https://orc.apache.org/specification/

### `orcid`
- ORCID 研究者标识 · ORCID · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 record-schema, api-version · 绑定 主锚 0 / 辅锚 0 · https://info.orcid.org/documentation/

### `parquet`
- Parquet 格式 · Apache · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 logical-type-extension · 绑定 主锚 4 / 辅锚 0 · https://github.com/apache/parquet-format

### `pdf20`
- PDF 2.0（ISO 32000-2） · ISO · 层 data · 可达 否（403 · 2026-09-24） · 扩展点 extension-dictionary, name-registry · 绑定 主锚 0 / 辅锚 0 · https://www.pdfa.org/resource/iso-32000-pdf/

### `pdfa`
- PDF/A 长期保存 · ISO/PDF Association · 层 data · 可达 否（403 · 2026-09-24） · 扩展点 conformance-level, profile-extension · 绑定 主锚 0 / 辅锚 0 · https://www.pdfa.org/resource/iso-19005-pdfa/

### `pdfua`
- PDF/UA 无障碍 · ISO/PDF Association · 层 data · 可达 否（403 · 2026-09-24） · 扩展点 conformance-level, structure-extension · 绑定 主锚 0 / 辅锚 0 · https://pdfa.org/resource/iso-14289-pdfua/

### `png3`
- PNG 第三版 · W3C · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 ancillary-chunk, private-chunk · 绑定 主锚 0 / 辅锚 0 · https://www.w3.org/TR/png-3/

### `premis`
- PREMIS 保存元数据 · Library of Congress · 层 data · 可达 否（403 · 2026-09-24） · 扩展点 agent-extension, event-type · 绑定 主锚 0 / 辅锚 0 · https://www.loc.gov/standards/premis/

### `rdf-star`
- RDF-star 三元组注解 · W3C · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 quoted-triple, annotation-syntax · 绑定 主锚 0 / 辅锚 0 · https://www.w3.org/TR/rdf12-concepts/

### `rdf11`
- RDF 1.1 · W3C · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 vocabulary-extension · 绑定 主锚 1 / 辅锚 0 · https://www.w3.org/TR/rdf11-concepts/

### `rfc3339`
- 时间戳 · IETF · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 profile · 绑定 主锚 2 / 辅锚 0 · https://www.rfc-editor.org/rfc/rfc3339.txt

### `rfc9562-uuid`
- UUID（含 v6/v7/v8） · IETF · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 version-field, variant-field · 绑定 主锚 0 / 辅锚 0 · https://www.rfc-editor.org/rfc/rfc9562

### `riff`
- RIFF 容器 · Microsoft · 层 data · 可达 否（0 · 2026-09-24） · 扩展点 chunk-extension, fourcc · 绑定 主锚 0 / 辅锚 0 · https://learn.microsoft.com/en-us/windows/win32/xaudio2/resource-interchange-file-format--riff-

### `ror`
- ROR 机构标识 · ROR · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 record-schema, relationship-type · 绑定 主锚 0 / 辅锚 0 · https://ror.readme.io/docs/ror-data-structure

### `s-100`
- S-100 海洋通用数据模型 · IHO · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 product-specification, feature-catalogue · 绑定 主锚 0 / 辅锚 0 · https://iho.int/en/s-100-universal-hydrographic-data-model

### `schema-org`
- 结构化数据词表 · Schema.org · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 extension, pending · 绑定 主锚 0 / 辅锚 0 · https://schema.org/Dataset

### `sdmx`
- SDMX 统计数据交换 · SDMX · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 data-structure-definition, codelist-extension · 绑定 主锚 0 / 辅锚 0 · https://sdmx.org/

### `shex`
- ShEx 形状表达式 · W3C · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 shape-map, semantic-action · 绑定 主锚 0 / 辅锚 0 · https://shex.io/shex-semantics/

### `snomed-ct`
- SNOMED CT 临床术语 · SNOMED International · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 extension-edition, reference-set · 绑定 主锚 0 / 辅锚 0 · https://www.snomed.org/

### `stix`
- STIX 威胁情报 · OASIS · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 custom-object, extension-definition · 绑定 主锚 0 / 辅锚 0 · https://docs.oasis-open.org/cti/stix/v2.1/stix-v2.1.html

### `taxii`
- TAXII 威胁情报交换 · OASIS · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 media-type, api-extension · 绑定 主锚 0 / 辅锚 0 · https://docs.oasis-open.org/cti/taxii/v2.1/taxii-v2.1.html

### `tbx-lisa`
- TBX 术语交换格式 · LISA/ISO · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 dialect-extension · 绑定 主锚 0 / 辅锚 0 · https://www.tbxinfo.net/

### `tei`
- TEI 文本编码倡议 · TEI Consortium · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 module-selection, customization-ODD · 绑定 主锚 0 / 辅锚 0 · https://tei-c.org/release/doc/tei-p5-doc/en/html/index.html

### `thrift`
- Thrift IDL 与协议 · Apache · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 idl-annotation, protocol-layer · 绑定 主锚 0 / 辅锚 0 · https://thrift.apache.org/docs/idl

### `tiff`
- TIFF 图像格式 · ITU-T · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 tag-extension, private-tag · 绑定 主锚 0 / 辅锚 0 · https://www.itu.int/rec/T-REC-T.871/en

### `toml`
- TOML 1.0 · TOML · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 table-extension · 绑定 主锚 0 / 辅锚 0 · https://toml.io/en/v1.0.0

### `ulid`
- ULID 有序标识 · ULID 社区 · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 timestamp-prefix, randomness · 绑定 主锚 0 / 辅锚 0 · https://github.com/ulid/spec

### `un-m49`
- UN M49 区域代码 · UN · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 region-code, subregion-code · 绑定 主锚 0 / 辅锚 0 · https://unstats.un.org/unsd/methodology/m49/

### `unicode-uca`
- UAX/UTS 系列（含 #15 归一化、#31 标识符） · Unicode · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 tailorable, property-alias · 绑定 主锚 0 / 辅锚 0 · https://www.unicode.org/reports/

### `unlocode`
- UN/LOCODE 地点代码 · UNECE · 层 data · 可达 否（403 · 2026-09-24） · 扩展点 location-code, function-classifier · 绑定 主锚 0 / 辅锚 0 · https://unece.org/trade/cefact/unlocode-code-list-country-and-territory

### `usd`
- USD 场景描述 · Pixar/ASWF · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 schema-extension, api-schema · 绑定 主锚 0 / 辅锚 0 · https://openusd.org/release/index.html

### `w3c-json-ld`
- JSON-LD 1.1 · W3C · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 context, vocab-extension · 绑定 主锚 0 / 辅锚 0 · https://www.w3.org/TR/json-ld11/

### `w3c-owl-time`
- OWL-Time 时间本体 · W3C · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 temporal-entity, extension · 绑定 主锚 3 / 辅锚 0 · https://www.w3.org/TR/owl-time/

### `w3c-owl2`
- OWL 2 本体语言 · W3C · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 profile, import · 绑定 主锚 0 / 辅锚 0 · https://www.w3.org/TR/owl2-overview/

### `w3c-shacl`
- SHACL 形状约束 · W3C · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 constraint-component, tag-based-rules · 绑定 主锚 0 / 辅锚 0 · https://www.w3.org/TR/shacl/

### `w3c-skos`
- SKOS 词表 · W3C · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 concept-scheme, semantic-relation · 绑定 主锚 8 / 辅锚 0 · https://www.w3.org/TR/skos-reference/

### `w3c-tabular-data`
- Tabular Data Model (CSVW) · W3C · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 annotation, dialect · 绑定 主锚 95 / 辅锚 198 · https://www.w3.org/TR/tabular-data-model/

### `w3c-turtle`
- Turtle 1.1 · W3C · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 prefix-extension · 绑定 主锚 0 / 辅锚 0 · https://www.w3.org/TR/turtle/

### `w3c-xml`
- XML 1.0 · W3C · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 namespace, xml-schema · 绑定 主锚 0 / 辅锚 0 · https://www.w3.org/TR/xml/

### `webp`
- WebP 容器与编码 · Google · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 chunk-extension, vp8l-feature · 绑定 主锚 0 / 辅锚 0 · https://developers.google.com/speed/webp/docs/riff_container

### `who-icd11`
- ICD-11 疾病分类 · WHO · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 extension-code, postcoordination · 绑定 主锚 0 / 辅锚 0 · https://icd.who.int/

### `woff2`
- WOFF2 字体封装 · W3C · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 flavor, metadata-block · 绑定 主锚 0 / 辅锚 0 · https://www.w3.org/TR/WOFF2/

### `xbrl`
- XBRL 财务报告标记 · XBRL International · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 taxonomy-extension, linkbase · 绑定 主锚 0 / 辅锚 0 · https://specifications.xbrl.org/

### `xliff21`
- XLIFF 2.1 本地化交换 · OASIS · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 extension-module, its-mapping · 绑定 主锚 0 / 辅锚 0 · https://docs.oasis-open.org/xliff/xliff-core/v2.1/xliff-core-v2.1.html

### `xmlschema11`
- XML Schema 1.1 · W3C · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 wildcard, extension-point · 绑定 主锚 0 / 辅锚 0 · https://www.w3.org/TR/xmlschema11-1/

### `xmp`
- XMP 可扩展元数据 · Adobe/ISO · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 namespace-schema, packet-wrapper · 绑定 主锚 0 / 辅锚 0 · https://developer.adobe.com/xmp/docs/

### `yaml12`
- YAML 1.2.2 · YAML · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 tag-extension · 绑定 主锚 0 / 辅锚 0 · https://yaml.org/spec/1.2.2/

### `yara`
- YARA 规则语言 · VirusTotal · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 module-system, external-variable · 绑定 主锚 0 / 辅锚 0 · https://yara.readthedocs.io/

### `zarr`
- Zarr 分块数组 · Zarr 社区 · 层 data · 可达 是（200 · 2026-09-24） · 扩展点 codec-pipeline, extension-dtype · 绑定 主锚 0 / 辅锚 0 · https://zarr-specs.readthedocs.io/en/latest/

### `archimate`
- ArchiMate 3.2 企业架构建模 · The Open Group · 层 eng · 可达 否（401 · 2026-09-24） · 扩展点 specialization, exchange-format · 绑定 主锚 0 / 辅锚 0 · https://pubs.opengroup.org/architecture/archimate3-doc/

### `bpmn2`
- BPMN 2.0 业务流程建模 · OMG · 层 eng · 可达 是（200 · 2026-09-24） · 扩展点 extension-element, custom-task · 绑定 主锚 0 / 辅锚 0 · https://www.omg.org/spec/BPMN/2.0/

### `cncf-otel-semconv`
- 语义约定（可扩展注册表） · OpenTelemetry · 层 eng · 可达 是（200 · 2026-09-24） · 扩展点 attribute-registry, stability-scope · 绑定 主锚 46 / 辅锚 27 · https://opentelemetry.io/docs/specs/semconv/

### `conventionalcommits`
- 规约式提交信息 · Conventional Commits · 层 eng · 可达 是（200 · 2026-09-24） · 扩展点 type-extension, footer-token · 绑定 主锚 0 / 辅锚 0 · https://www.conventionalcommits.org/en/v1.0.0/

### `csaf`
- CSAF 安全公告 · OASIS · 层 eng · 可达 是（200 · 2026-09-24） · 扩展点 profile, product-tree · 绑定 主锚 0 / 辅锚 0 · https://docs.oasis-open.org/csaf/csaf/v2.0/csaf-v2.0.html

### `cue`
- CUE 配置语言 · CUE · 层 eng · 可达 是（200 · 2026-09-24） · 扩展点 definition-constraint, attribute · 绑定 主锚 0 / 辅锚 0 · https://cuelang.org/docs/reference/spec/

### `cyclonedx-vex`
- CycloneDX VEX · CycloneDX · 层 eng · 可达 是（200 · 2026-09-24） · 扩展点 vulnerability-state, analysis-justification · 绑定 主锚 0 / 辅锚 0 · https://cyclonedx.org/capabilities/vex/

### `devcontainer-spec`
- Dev Container 规范 · Dev Container 社区 · 层 eng · 可达 是（200 · 2026-09-24） · 扩展点 feature-contribution, lifecycle-hook · 绑定 主锚 0 / 辅锚 0 · https://containers.dev/implementors/spec/

### `dmn`
- DMN 决策模型与记法 · OMG · 层 eng · 可达 是（200 · 2026-09-24） · 扩展点 decision-table-hit-policy, custom-function · 绑定 主锚 0 / 辅锚 0 · https://www.omg.org/spec/DMN/

### `editorconfig`
- EditorConfig 规范 · EditorConfig · 层 eng · 可达 是（200 · 2026-09-24） · 扩展点 property-name, plugin-extension · 绑定 主锚 0 / 辅锚 0 · https://editorconfig-specification.readthedocs.io/

### `finops-framework`
- FinOps 框架 · FinOps Foundation · 层 eng · 可达 是（200 · 2026-09-24） · 扩展点 capability-extension, maturity-level · 绑定 主锚 0 / 辅锚 0 · https://www.finops.org/framework/

### `in-toto`
- in-toto 供应链证明 · OpenSSF/CNCF · 层 eng · 可达 是（200 · 2026-09-24） · 扩展点 predicate-type, statement-subject · 绑定 主锚 0 / 辅锚 0 · https://github.com/in-toto/attestation/blob/main/spec/README.md

### `iso-iec-25010`
- SQuaRE 质量模型 · ISO/IEC · 层 eng · 可达 否（403 · 2026-09-24） · 扩展点 characteristic-extension · 绑定 主锚 0 / 辅锚 0 · https://www.iso.org/standard/78176.html

### `iso-iec-42010`
- 架构描述 · ISO/IEC · 层 eng · 可达 否（403 · 2026-09-24） · 扩展点 viewpoint-extension · 绑定 主锚 0 / 辅锚 0 · https://www.iso.org/standard/74393.html

### `junit-xml`
- JUnit XML 测试报告 · JUnit 社区 · 层 eng · 可达 是（200 · 2026-09-24） · 扩展点 custom-property, system-out · 绑定 主锚 0 / 辅锚 0 · https://github.com/testmoapp/junitxml

### `keepachangelog`
- 变更日志规范 · Keep a Changelog · 层 eng · 可达 是（200 · 2026-09-24） · 扩展点 change-type-section, version-anchor · 绑定 主锚 0 / 辅锚 0 · https://keepachangelog.com/en/1.1.0/

### `mlcommons-bench`
- MLPerf 基准（可扩展场景） · MLCommons · 层 eng · 可达 是（200 · 2026-09-24） · 扩展点 scenario-extension · 绑定 主锚 110 / 辅锚 0 · https://mlcommons.org/benchmarks/

### `nist-800-142`
- SP 800-142 组合测试实践 · NIST · 层 eng · 可达 是（200 · 2026-09-24） · 扩展点 methodology · 绑定 主锚 6 / 辅锚 0 · https://csrc.nist.gov/pubs/sp/800/142/final

### `opa-rego`
- Open Policy Agent / Rego · CNCF · 层 eng · 可达 是（200 · 2026-09-24） · 扩展点 custom-builtin, policy-bundle · 绑定 主锚 0 / 辅锚 0 · https://www.openpolicyagent.org/docs/latest/policy-language/

### `openchain`
- OpenChain 开源合规标准 · OpenChain Project · 层 eng · 可达 是（200 · 2026-09-24） · 扩展点 conformance-question, annex · 绑定 主锚 0 / 辅锚 0 · https://www.openchainproject.org/spec/

### `openmetrics`
- OpenMetrics 1.0 · OpenMetrics · 层 eng · 可达 是（200 · 2026-09-24） · 扩展点 metric-family-extension · 绑定 主锚 2 / 辅锚 0 · https://github.com/OpenObservability/OpenMetrics/blob/main/specification/OpenMetrics.md

### `openvex`
- OpenVEX 漏洞可利用性交换 · OpenSSF · 层 eng · 可达 是（200 · 2026-09-24） · 扩展点 statement-status, product-identifier · 绑定 主锚 0 / 辅锚 0 · https://github.com/openvex/spec

### `ossp-scorecard`
- Scorecard 开源项目健康度 · OpenSSF · 层 eng · 可达 是（200 · 2026-09-24） · 扩展点 check-name, score-detail · 绑定 主锚 0 / 辅锚 0 · https://github.com/ossf/scorecard

### `peps`
- PEP 体系（含 8/257/621） · Python · 层 eng · 可达 是（200 · 2026-09-24） · 扩展点 new-pep · 绑定 主锚 7 / 辅锚 0 · https://peps.python.org/

### `prometheus-exposition`
- 指标暴露格式 · Prometheus · 层 eng · 可达 是（200 · 2026-09-24） · 扩展点 metric-suffix · 绑定 主锚 2 / 辅锚 0 · https://prometheus.io/docs/instrumenting/exposition_formats/

### `reproducible-builds`
- 可重现构建 · Reproducible Builds · 层 eng · 可达 是（200 · 2026-09-24） · 扩展点 variation-source, attestation · 绑定 主锚 0 / 辅锚 0 · https://reproducible-builds.org/docs/

### `reuse-3`
- REUSE 许可声明规范 · REUSE/FSFE · 层 eng · 可达 是（200 · 2026-09-24） · 扩展点 spdx-header, reuse-toml · 绑定 主锚 0 / 辅锚 0 · https://reuse.software/spec-3.3/

### `rfc9162-ct`
- 证书透明 v2（CT） · IETF · 层 eng · 可达 是（200 · 2026-09-24） · 扩展点 log-entry-type, extension-data · 绑定 主锚 0 / 辅锚 0 · https://www.rfc-editor.org/rfc/rfc9162

### `sci-iso21031`
- 软件碳强度（SCI） · Green Software Foundation · 层 eng · 可达 是（200 · 2026-09-24） · 扩展点 functional-unit, boundary-definition · 绑定 主锚 0 / 辅锚 0 · https://sci.greensoftware.foundation/

### `scitt`
- SCITT 供应链透明 · IETF · 层 eng · 可达 是（200 · 2026-09-24） · 扩展点 signed-statement, transparency-service · 绑定 主锚 0 / 辅锚 0 · https://datatracker.ietf.org/doc/draft-ietf-scitt-architecture/

### `semver`
- 语义化版本 · SemVer 社区 · 层 eng · 可达 是（200 · 2026-09-24） · 扩展点 prerelease-identifier, build-metadata · 绑定 主锚 0 / 辅锚 0 · https://semver.org/spec/v2.0.0.html

### `sigstore`
- Sigstore 签名与透明日志 · OpenSSF · 层 eng · 可达 是（200 · 2026-09-24） · 扩展点 bundle-format, fulcio-extension · 绑定 主锚 0 / 辅锚 0 · https://docs.sigstore.dev/about/overview/

### `slsa`
- SLSA 供应链等级 · OpenSSF · 层 eng · 可达 是（200 · 2026-09-24） · 扩展点 build-level, threat-model-extension · 绑定 主锚 0 / 辅锚 0 · https://slsa.dev/spec/v1.0/

### `ssvc`
- SSVC 漏洞处置决策 · CISA/CERT-CC · 层 eng · 可达 是（200 · 2026-09-24） · 扩展点 decision-point, decision-table · 绑定 主锚 0 / 辅锚 0 · https://github.com/CERTCC/SSVC

### `sysml2`
- SysML v2 · OMG · 层 eng · 可达 是（200 · 2026-09-24） · 扩展点 metadata-definition, library-extension · 绑定 主锚 0 / 辅锚 0 · https://www.omg.org/spec/SysML/2.0/

### `tap14`
- TAP 测试协议 · TestAnything · 层 eng · 可达 是（200 · 2026-09-24） · 扩展点 directive, yaml-diagnostic · 绑定 主锚 0 / 辅锚 0 · https://testanything.org/tap-version-14-specification.html

### `togaf`
- TOGAF 企业架构框架 · The Open Group · 层 eng · 可达 否（401 · 2026-09-24） · 扩展点 architecture-method-extension, content-framework · 绑定 主锚 0 / 辅锚 0 · https://pubs.opengroup.org/togaf-standard/

### `uml25`
- UML 2.5.1 · OMG · 层 eng · 可达 是（200 · 2026-09-24） · 扩展点 stereotype, profile · 绑定 主锚 0 / 辅锚 0 · https://www.omg.org/spec/UML/2.5.1/

### `asciidoc`
- AsciiDoc 标记语言 · AsciiDoc 社区 · 层 form · 可达 是（200 · 2026-09-24） · 扩展点 macro-extension, block-extension · 绑定 主锚 0 / 辅锚 0 · https://docs.asciidoctor.org/asciidoc/latest/

### `atag20`
- ATAG 2.0 创作工具无障碍 · W3C · 层 form · 可达 是（200 · 2026-09-24） · 扩展点 conformance-level, success-criterion-scope · 绑定 主锚 0 / 辅锚 0 · https://www.w3.org/TR/ATAG20/

### `cff`
- CITATION.cff 引用文件 · Citation File Format 社区 · 层 form · 可达 是（200 · 2026-09-24） · 扩展点 schema-version, custom-field · 绑定 主锚 0 / 辅锚 0 · https://citation-file-format.github.io/

### `commonmark`
- CommonMark 0.31.2 · CommonMark · 层 form · 可达 是（200 · 2026-09-24） · 扩展点 extension-blocks · 绑定 主锚 70 / 辅锚 111 · https://spec.commonmark.org/0.31.2/

### `gfm`
- GFM 扩展 · GitHub · 层 form · 可达 是（200 · 2026-09-24） · 扩展点 extension · 绑定 主锚 12 / 辅锚 0 · https://github.github.com/gfm/

### `grafana-dashboard`
- Dashboard JSON model · Grafana · 层 form · 可达 是（200 · 2026-09-24） · 扩展点 panel-plugin, schema-version · 绑定 主锚 0 / 辅锚 0 · https://grafana.com/docs/grafana/latest/dashboards/build-dashboards/view-dashboard-json-model/

### `graphml`
- GraphML 1.0 · GraphML · 层 form · 可达 是（200 · 2026-09-24） · 扩展点 key-extension · 绑定 主锚 0 / 辅锚 0 · http://graphml.graphdrawing.org/specification.html

### `graphviz`
- DOT 语言 · Graphviz · 层 form · 可达 是（200 · 2026-09-24） · 扩展点 attribute-extension · 绑定 主锚 0 / 辅锚 0 · https://graphviz.org/doc/info/lang.html

### `its20`
- ITS 2.0 国际化标签集 · W3C · 层 form · 可达 是（200 · 2026-09-24） · 扩展点 data-category, local-markup · 绑定 主锚 0 / 辅锚 0 · https://www.w3.org/TR/its20/

### `manifest-json`
- Web App Manifest · W3C · 层 form · 可达 是（200 · 2026-09-24） · 扩展点 member-extension, display-mode · 绑定 主锚 0 / 辅锚 0 · https://www.w3.org/TR/appmanifest/

### `mathml4`
- MathML Core · W3C · 层 form · 可达 是（200 · 2026-09-24） · 扩展点 intent-attribute, operator-dictionary · 绑定 主锚 0 / 辅锚 0 · https://www.w3.org/TR/mathml-core/

### `mermaid`
- Mermaid 图语言 · Mermaid · 层 form · 可达 是（200 · 2026-09-24） · 扩展点 diagram-type-extension · 绑定 主锚 4 / 辅锚 136 · https://mermaid.js.org/intro/

### `odf`
- OpenDocument Format · OASIS · 层 form · 可达 是（200 · 2026-09-24） · 扩展点 extension-namespace, style-family · 绑定 主锚 0 / 辅锚 0 · https://www.oasis-open.org/committees/tc_home.php?wg_abbrev=office

### `omml`
- OMML 数学标记 · Microsoft/ECMA · 层 form · 可达 是（200 · 2026-09-24） · 扩展点 extension-element, math-run · 绑定 主锚 0 / 辅锚 0 · https://ecma-international.org/publications-and-standards/standards/ecma-376/

### `opc-ooxml`
- Open Packaging Conventions · ECMA · 层 form · 可达 是（200 · 2026-09-24） · 扩展点 part-naming, content-type · 绑定 主锚 0 / 辅锚 0 · https://ecma-international.org/publications-and-standards/standards/ecma-376/

### `rst-docutils`
- reStructuredText 指令/角色 · Docutils · 层 form · 可达 是（200 · 2026-09-24） · 扩展点 directive, role · 绑定 主锚 0 / 辅锚 0 · https://docutils.sourceforge.io/docs/ref/rst/restructuredtext.html

### `spdx-file`
- SPDX 文件头标注 · Linux Foundation · 层 form · 可达 是（200 · 2026-09-24） · 扩展点 file-tag, license-identifier · 绑定 主锚 0 / 辅锚 0 · https://spdx.dev/learn/handling-license-info/

### `ssml11`
- SSML 1.1 语音合成标记 · W3C · 层 form · 可达 是（200 · 2026-09-24） · 扩展点 extension-attribute, plugin-element · 绑定 主锚 0 / 辅锚 0 · https://www.w3.org/TR/speech-synthesis11/

### `ttml2`
- TTML2 时序文本 · W3C · 层 form · 可达 是（200 · 2026-09-24） · 扩展点 metadata-element, extension-designation · 绑定 主锚 0 / 辅锚 0 · https://www.w3.org/TR/ttml2/

### `vega`
- Vega 可视化语法 · Vega/LF · 层 form · 可达 是（200 · 2026-09-24） · 扩展点 extension-transform, config-scope · 绑定 主锚 0 / 辅锚 0 · https://vega.github.io/vega/docs/specification/

### `vega-datasets`
- Vega 数据集与规范 · Vega · 层 form · 可达 是（200 · 2026-09-24） · 扩展点 spec-extension · 绑定 主锚 0 / 辅锚 0 · https://vega.github.io/vega-lite/

### `vega-lite`
- Vega-Lite v5 · Vega · 层 form · 可达 是（200 · 2026-09-24） · 扩展点 config-extension · 绑定 主锚 5 / 辅锚 364 · https://vega.github.io/schema/vega-lite/v5.json

### `w3c-css`
- CSS 快照（分级扩展） · W3C · 层 form · 可达 是（200 · 2026-09-24） · 扩展点 module-level · 绑定 主锚 0 / 辅锚 0 · https://www.w3.org/TR/CSS/

### `w3c-epub33`
- EPUB 3.3 · W3C · 层 form · 可达 是（200 · 2026-09-24） · 扩展点 foreign-resources, manifest-properties · 绑定 主锚 60 / 辅锚 0 · https://www.w3.org/TR/epub-33/

### `w3c-mathml3`
- MathML 3 · W3C · 层 form · 可达 是（200 · 2026-09-24） · 扩展点 namespace-extension · 绑定 主锚 5 / 辅锚 0 · https://www.w3.org/TR/MathML3/

### `w3c-svg2`
- SVG 2 · W3C · 层 form · 可达 是（200 · 2026-09-24） · 扩展点 foreign-object, extension-elements · 绑定 主锚 11 / 辅锚 0 · https://www.w3.org/TR/SVG2/

### `w3c-webaudio`
- Web Audio API · W3C · 层 form · 可达 是（200 · 2026-09-24） · 扩展点 audioworklet · 绑定 主锚 17 / 辅锚 0 · https://www.w3.org/TR/webaudio/

### `wai-aria`
- WAI-ARIA 1.2 · W3C · 层 form · 可达 是（200 · 2026-09-24） · 扩展点 role-extension, aria-attribute · 绑定 主锚 0 / 辅锚 0 · https://www.w3.org/TR/wai-aria-1.2/

### `webvtt`
- WebVTT 字幕 · W3C · 层 form · 可达 是（200 · 2026-09-24） · 扩展点 cue-setting, region-extension · 绑定 主锚 0 / 辅锚 0 · https://www.w3.org/TR/webvtt1/

### `aicpa-soc2`
- SOC 2 信任服务准则 · AICPA · 层 gov · 可达 是（200 · 2026-09-24） · 扩展点 trust-services-category, criterion · 绑定 主锚 0 / 辅锚 0 · https://www.aicpa-cima.com/topic/audit-assurance/audit-and-assurance-greater-than-soc-2

### `bagit`
- BagIt (RFC 8493) · IETF · 层 gov · 可达 是（200 · 2026-09-24） · 扩展点 tag-file-extension · 绑定 主锚 0 / 辅锚 0 · https://www.rfc-editor.org/rfc/rfc8493.txt

### `bis-basel-iii`
- 巴塞尔 III 资本框架 · BIS/BCBS · 层 gov · 可达 是（200 · 2026-09-24） · 扩展点 approach-selection, national-discretion · 绑定 主锚 0 / 辅锚 0 · https://www.bis.org/bcbs/publ/d424.htm

### `c2pa-spec`
- 内容凭证规范 · C2PA · 层 gov · 可达 是（200 · 2026-09-24） · 扩展点 assertion-extension · 绑定 主锚 4 / 辅锚 0 · https://c2pa.org/specifications/specifications/1.3/index.html

### `cis-benchmarks`
- CIS 基线配置 · Center for Internet Security · 层 gov · 可达 是（200 · 2026-09-24） · 扩展点 profile-level, recommendation-number · 绑定 主锚 0 / 辅锚 0 · https://www.cisecurity.org/cis-benchmarks

### `cis-controls`
- CIS Critical Security Controls · Center for Internet Security · 层 gov · 可达 是（200 · 2026-09-24） · 扩展点 control-number, implementation-group · 绑定 主锚 0 / 辅锚 0 · https://www.cisecurity.org/controls

### `codex-alimentarius`
- 国际食品法典 · Codex · 层 gov · 可达 是（200 · 2026-09-24） · 扩展点 standard-extension · 绑定 主锚 0 / 辅锚 0 · https://www.fao.org/fao-who-codexalimentarius/en/

### `common-criteria`
- Common Criteria（ISO 15408） · CCRA · 层 gov · 可达 是（200 · 2026-09-24） · 扩展点 protection-profile, assurance-level · 绑定 主锚 41 / 辅锚 0 · https://www.commoncriteriaportal.org/

### `council-europe-ai`
- AI 框架公约 · Council of Europe · 层 gov · 可达 否（403 · 2026-09-24） · 扩展点 risk-based-approach, party-declaration · 绑定 主锚 0 / 辅锚 0 · https://www.coe.int/en/web/artificial-intelligence/the-framework-convention-on-artificial-intelligence

### `creativecommons`
- 许可与权利表达 · Creative Commons · 层 gov · 可达 是（200 · 2026-09-24） · 扩展点 license-versioning, rights-statements · 绑定 主锚 19 / 辅锚 0 · https://creativecommons.org/licenses/

### `cwe`
- CWE 缺陷枚举 · MITRE · 层 gov · 可达 是（200 · 2026-09-24） · 扩展点 view, category-extension · 绑定 主锚 11 / 辅锚 0 · https://cwe.mitre.org/

### `cyclonedx-mlbom`
- ML-BOM 能力 · CycloneDX · 层 gov · 可达 是（200 · 2026-09-24） · 扩展点 component-extension, property · 绑定 主锚 0 / 辅锚 0 · https://cyclonedx.org/capabilities/mlbom/

### `datacite`
- 元数据内核 · DataCite · 层 gov · 可达 是（200 · 2026-09-24） · 扩展点 profile · 绑定 主锚 4 / 辅锚 0 · https://schema.datacite.org/meta/kernel-4.6/

### `did-w3c-methods`
- DID 方法注册表 · W3C · 层 gov · 可达 是（200 · 2026-09-24） · 扩展点 method-registration, property-extension · 绑定 主锚 0 / 辅锚 0 · https://www.w3.org/TR/did-extensions/

### `edpb-guidelines`
- EDPB 数据保护指南 · EDPB · 层 gov · 可达 是（200 · 2026-09-24） · 扩展点 guideline-number, national-derogation · 绑定 主锚 0 / 辅锚 0 · https://www.edpb.europa.eu/our-work-tools/general-guidance/guidelines-recommendations-best-practices_en

### `eiopa-dora`
- DORA 数字运营韧性 · EIOPA · 层 gov · 可达 是（200 · 2026-09-24） · 扩展点 ict-risk-requirement, register-of-information · 绑定 主锚 0 / 辅锚 0 · https://www.eiopa.europa.eu/digital-operational-resilience-act-dora_en

### `enisa-nis2`
- NIS2 网络安全指令要求 · ENISA/EU · 层 gov · 可达 是（200 · 2026-09-24） · 扩展点 essential-entity-class, incident-reporting · 绑定 主锚 0 / 辅锚 0 · https://digital-strategy.ec.europa.eu/en/policies/nis2-directive

### `esma-mifid`
- MiFID II / MiFIR 监管要求 · ESMA · 层 gov · 可达 是（200 · 2026-09-24） · 扩展点 technical-standard, reporting-field · 绑定 主锚 0 / 辅锚 0 · https://www.esma.europa.eu/policy-rules/mifid-ii-and-mifir

### `etsi-en301549`
- EN 301 549 无障碍要求 · ETSI · 层 gov · 可达 是（200 · 2026-09-24） · 扩展点 clause-number, procurement-annex · 绑定 主锚 0 / 辅锚 0 · https://www.etsi.org/deliver/etsi_en/301500_301599/301549/

### `eu-accessibility-act`
- 欧洲无障碍法案 · European Commission · 层 gov · 可达 否（0 · 2026-09-24） · 扩展点 product-scope, harmonised-standard · 绑定 主锚 0 / 辅锚 0 · https://ec.europa.eu/social/main.jsp?catId=1202

### `eu-ai-act`
- AI 法案（技术文档/风险分级） · EU · 层 gov · 可达 是（200 · 2026-09-24） · 扩展点 annex-iv-doc, harmonised-standards · 绑定 主锚 0 / 辅锚 0 · https://digital-strategy.ec.europa.eu/en/policies/regulatory-framework-ai

### `eu-machinery`
- 机械条例 2023/1230 · EU · 层 gov · 可达 是（200 · 2026-09-24） · 扩展点 standard-harmonisation · 绑定 主锚 5 / 辅锚 0 · https://single-market-economy.ec.europa.eu/sectors/mechanical-engineering/machinery_en

### `fao-food`
- 食品安全与质量 · FAO · 层 gov · 可达 是（200 · 2026-09-24） · 扩展点 codex-alignment · 绑定 主锚 2 / 辅锚 0 · https://www.fao.org/food-safety/en/

### `fatf-recommendations`
- FATF 反洗钱建议 · FATF · 层 gov · 可达 否（403 · 2026-09-24） · 扩展点 recommendation-number, interpretive-note · 绑定 主锚 0 / 辅锚 0 · https://www.fatf-gafi.org/en/topics/fatf-recommendations.html

### `fedramp`
- FedRAMP 授权基线 · GSA · 层 gov · 可达 是（200 · 2026-09-24） · 扩展点 baseline-profile, control-tailoring · 绑定 主锚 0 / 辅锚 0 · https://www.fedramp.gov/

### `gdpr`
- GDPR · EU · 层 gov · 可达 是（200 · 2026-09-24） · 扩展点 codes-of-conduct, certification · 绑定 主锚 36 / 辅锚 0 · https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A32016R0679

### `ghg-protocol`
- 温室气体核算体系 · GHG Protocol · 层 gov · 可达 是（200 · 2026-09-24） · 扩展点 scope-definition, sector-guidance · 绑定 主锚 0 / 辅锚 0 · https://ghgprotocol.org/

### `gips`
- GIPS 绩效标准 · CFA Institute · 层 gov · 可达 是（200 · 2026-09-24） · 扩展点 composite-definition, disclosure · 绑定 主锚 11 / 辅锚 0 · https://www.cfainstitute.org/en/ethics-standards/codes/gips-standards

### `gleif-lei`
- ISO 17442 LEI · GLEIF · 层 gov · 可达 是（200 · 2026-09-24） · 扩展点 vLEI-ecosystem · 绑定 主锚 0 / 辅锚 0 · https://www.gleif.org/en/about-lei/iso-17442-the-lei-code-structure

### `hipaa-security`
- HIPAA 安全规则 · HHS · 层 gov · 可达 否（403 · 2026-09-24） · 扩展点 implementation-specification, addressable-vs-required · 绑定 主锚 0 / 辅锚 0 · https://www.hhs.gov/hipaa/for-professionals/security/index.html

### `iec-42001`
- AI 管理体系 · ISO/IEC · 层 gov · 可达 否（403 · 2026-09-24） · 扩展点 management-system-clauses · 绑定 主锚 0 / 辅锚 0 · https://www.iso.org/standard/42001

### `ieee-7000`
- IEEE 7000 系列（伦理对齐） · IEEE · 层 gov · 可达 是（200 · 2026-09-24） · 扩展点 process-extension · 绑定 主锚 0 / 辅锚 0 · https://standards.ieee.org/initiatives/autonomous-intelligence-systems/

### `ietf-bcp47`
- 语言标签 (RFC 5646) · IETF · 层 gov · 可达 是（200 · 2026-09-24） · 扩展点 extension-subtag, registry · 绑定 主锚 0 / 辅锚 0 · https://www.rfc-editor.org/rfc/rfc5646.txt

### `ietf-robots`
- robots.txt (RFC 9309) · IETF · 层 gov · 可达 是（200 · 2026-09-24） · 扩展点 extension-directive · 绑定 主锚 0 / 辅锚 0 · https://www.rfc-editor.org/rfc/rfc9309.txt

### `ifrs-standards`
- IFRS 会计准则 · IFRS Foundation · 层 gov · 可达 是（200 · 2026-09-24） · 扩展点 taxonomy-extension, transition-option · 绑定 主锚 0 / 辅锚 0 · https://www.ifrs.org/issued-standards/list-of-standards/

### `issb-sustainability`
- ISSB 可持续披露准则 · ISSB/IFRS · 层 gov · 可达 是（200 · 2026-09-24） · 扩展点 industry-based-guidance, transition-relief · 绑定 主锚 0 / 辅锚 0 · https://www.ifrs.org/issued-standards/ifrs-sustainability-standards-navigator/

### `nist-100-2`
- AI 100-2 对抗机器学习分类 · NIST · 层 gov · 可达 是（200 · 2026-09-24） · 扩展点 taxonomy · 绑定 主锚 0 / 辅锚 0 · https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.100-2e2023.pdf

### `nist-800-171`
- SP 800-171 受控非密信息保护 · NIST · 层 gov · 可达 是（200 · 2026-09-24） · 扩展点 requirement-family, assessment-procedure · 绑定 主锚 0 / 辅锚 0 · https://csrc.nist.gov/pubs/sp/800/171/r3/final

### `nist-800-188`
- SP 800-188 去标识化 · NIST · 层 gov · 可达 是（200 · 2026-09-24） · 扩展点 technique-catalog · 绑定 主锚 10 / 辅锚 0 · https://csrc.nist.gov/pubs/sp/800/188/final

### `nist-800-207`
- 零信任架构（SP 800-207） · NIST · 层 gov · 可达 是（200 · 2026-09-24） · 扩展点 deployment-model, policy-engine · 绑定 主锚 0 / 辅锚 0 · https://csrc.nist.gov/pubs/sp/800/207/final

### `nist-800-53`
- SP 800-53 安全与隐私控制 · NIST · 层 gov · 可达 是（200 · 2026-09-24） · 扩展点 control-identifier, control-overlay · 绑定 主锚 0 / 辅锚 0 · https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final

### `nist-800-63`
- SP 800-63 数字身份指南 · NIST · 层 gov · 可达 是（200 · 2026-09-24） · 扩展点 assurance-level, authenticator-type · 绑定 主锚 0 / 辅锚 0 · https://pages.nist.gov/800-63-4/

### `nist-ai-600-1`
- 生成式 AI 风险档案（AI 600-1） · NIST · 层 gov · 可达 是（200 · 2026-09-24） · 扩展点 risk-category, action-identifier · 绑定 主锚 0 / 辅锚 0 · https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.600-1.pdf

### `nist-ai-rmf`
- AI 风险管理框架 · NIST · 层 gov · 可达 是（200 · 2026-09-24） · 扩展点 profile, playbook · 绑定 主锚 74 / 辅锚 0 · https://www.nist.gov/itl/ai-risk-management-framework

### `nist-csf`
- 网络安全框架 2.0 · NIST · 层 gov · 可达 是（200 · 2026-09-24） · 扩展点 function-category, community-profile · 绑定 主锚 0 / 辅锚 0 · https://www.nist.gov/cyberframework

### `nist-privacy`
- 隐私框架 · NIST · 层 gov · 可达 是（200 · 2026-09-24） · 扩展点 profile · 绑定 主锚 0 / 辅锚 0 · https://www.nist.gov/privacy-framework

### `ntia-sbom`
- SBOM 最小要素 · NTIA · 层 gov · 可达 是（200 · 2026-09-24） · 扩展点 minimum-element, extension-field · 绑定 主锚 0 / 辅锚 0 · https://www.ntia.gov/report/2021/minimum-elements-software-bill-materials-sbom

### `oecd-ai`
- OECD AI 原则 · OECD · 层 gov · 可达 是（200 · 2026-09-24） · 扩展点 policy-observatory · 绑定 主锚 4 / 辅锚 0 · https://oecd.ai/en/ai-principles

### `oecd-privacy`
- OECD 隐私保护准则 · OECD · 层 gov · 可达 是（200 · 2026-09-24） · 扩展点 principle-set, implementation-guidance · 绑定 主锚 0 / 辅锚 0 · https://legalinstruments.oecd.org/en/instruments/OECD-LEGAL-0188

### `oscal`
- OSCAL 控制与评估交换 · NIST · 层 gov · 可达 是（200 · 2026-09-24） · 扩展点 model-extension, profile-resolution · 绑定 主锚 0 / 辅锚 0 · https://pages.nist.gov/OSCAL/

### `osi-osd`
- 开源定义 · OSI · 层 gov · 可达 是（200 · 2026-09-24） · 扩展点 license-review · 绑定 主锚 7 / 辅锚 0 · https://opensource.org/osd

### `osv`
- OSV 漏洞格式 · Google/OSV · 层 gov · 可达 是（200 · 2026-09-24） · 扩展点 ecosystem-extension · 绑定 主锚 7 / 辅锚 0 · https://osv.dev/

### `owasp-asvs`
- ASVS 应用安全验证标准 · OWASP · 层 gov · 可达 是（200 · 2026-09-24） · 扩展点 chapter-requirement, level-selection · 绑定 主锚 0 / 辅锚 0 · https://github.com/OWASP/ASVS

### `owasp-llm`
- LLM 应用十大风险 · OWASP · 层 gov · 可达 是（200 · 2026-09-24） · 扩展点 category-extension · 绑定 主锚 23 / 辅锚 0 · https://owasp.org/www-project-top-10-for-large-language-model-applications/

### `owasp-top10`
- Web 十大风险 · OWASP · 层 gov · 可达 是（200 · 2026-09-24） · 扩展点 category-extension · 绑定 主锚 0 / 辅锚 0 · https://owasp.org/www-project-top-ten/

### `pci-dss`
- PCI DSS 支付卡行业标准 · PCI SSC · 层 gov · 可达 是（200 · 2026-09-24） · 扩展点 requirement-number, customized-approach · 绑定 主锚 0 / 辅锚 0 · https://www.pcisecuritystandards.org/document_library/

### `rocrate`
- RO-Crate 1.1 · Research Object · 层 gov · 可达 是（200 · 2026-09-24） · 扩展点 profiles · 绑定 主锚 5 / 辅锚 0 · https://www.researchobject.org/ro-crate/specification.html

### `spdx-3`
- SPDX 3.0（含 AI profile） · SPDX · 层 gov · 可达 是（200 · 2026-09-24） · 扩展点 profile, extension-class · 绑定 主锚 4 / 辅锚 4 · https://spdx.github.io/spdx-spec/v3.0/

### `spdx-licenses`
- SPDX 许可证清单 · SPDX · 层 gov · 可达 是（200 · 2026-09-24） · 扩展点 license-expression, license-ref · 绑定 主锚 23 / 辅锚 15 · https://spdx.org/licenses/

### `unesco-ai`
- AI 伦理建议书 · UNESCO · 层 gov · 可达 是（200 · 2026-09-24） · 扩展点 readiness-assessment · 绑定 主锚 8 / 辅锚 0 · https://www.unesco.org/en/artificial-intelligence/recommendation-ethics

### `unicode-cldr`
- CLDR 本地化数据 · Unicode · 层 gov · 可达 是（200 · 2026-09-24） · 扩展点 locale-variants, annotation · 绑定 主锚 0 / 辅锚 0 · https://cldr.unicode.org/

### `uptane`
- OTA 安全框架 · Uptane · 层 gov · 可达 是（200 · 2026-09-24） · 扩展点 director-repository · 绑定 主锚 4 / 辅锚 0 · https://uptane.org/

### `us-section508`
- Section 508 无障碍 · US GSA · 层 gov · 可达 是（200 · 2026-09-24） · 扩展点 ict-standard, conformance-report · 绑定 主锚 0 / 辅锚 0 · https://www.section508.gov/

### `vc-controller-bindings`
- VC 控制器绑定方法 · W3C · 层 gov · 可达 是（200 · 2026-09-24） · 扩展点 binding-method, proof-format · 绑定 主锚 0 / 辅锚 0 · https://www.w3.org/TR/controller-document/

### `w3c-did`
- DID Core · W3C · 层 gov · 可达 是（200 · 2026-09-24） · 扩展点 method-registry · 绑定 主锚 0 / 辅锚 0 · https://www.w3.org/TR/did-core/

### `w3c-epub-a11y`
- EPUB 无障碍 1.1 · W3C · 层 gov · 可达 是（200 · 2026-09-24） · 扩展点 metadata-extension · 绑定 主锚 5 / 辅锚 0 · https://www.w3.org/TR/epub-a11y-11/

### `w3c-prov-o`
- PROV-O 溯源本体 · W3C · 层 gov · 可达 是（200 · 2026-09-24） · 扩展点 subclass, extension-module · 绑定 主锚 69 / 辅锚 88 · https://www.w3.org/TR/prov-o/

### `w3c-vc`
- Verifiable Credentials 2.0 · W3C · 层 gov · 可达 是（200 · 2026-09-24） · 扩展点 extension-property, status-list · 绑定 主锚 0 / 辅锚 6 · https://www.w3.org/TR/vc-data-model-2.0/

### `w3c-wcag22`
- WCAG 2.2 · W3C · 层 gov · 可达 是（200 · 2026-09-24） · 扩展点 techniques, conformance-claims · 绑定 主锚 1 / 辅锚 0 · https://www.w3.org/TR/WCAG22/

### `wcag-em`
- WCAG-EM 评估方法 · W3C · 层 gov · 可达 是（200 · 2026-09-24） · 扩展点 evaluation-scope, sample-selection · 绑定 主锚 0 / 辅锚 0 · https://www.w3.org/TR/WCAG-EM/

### `who-ai`
- 健康 AI 指南 · WHO · 层 gov · 可达 是（200 · 2026-09-24） · 扩展点 guidance-extension · 绑定 主锚 0 / 辅锚 0 · https://www.who.int/health-topics/artificial-intelligence

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
