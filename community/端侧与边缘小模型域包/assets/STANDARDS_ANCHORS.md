<!-- nf-asset: key="STANDARDS_ANCHORS" version="1.0" status="active" -->
# 权威锚表 · 端侧与边缘小模型

> 用途：本域 12 条细分各自的**外部权威锚**（规范 / 论文 / 参考实现）与**可达性实证**。外部锚只作口径与机制参照，**不作品质背书**（STRATEGY §3.2/§3.3）。
> 资产键：`STANDARDS_ANCHORS`｜细分锚实测日期：2026-09-22（本机 GET，HTTP 状态见下表；不可达如实记 `✗`，不假装可达）｜标准锚实测日期见下表「标准锚」列（取自 `protocol/standards_catalog.json` 的本机探针记录）。

## 1. 锚表

| 条目键 | 锚类型 | URL | 可达性 | 主锚（域口径标准） | 辅锚（产出承载标准） |
|---|---|---|---|---|---|
| `A14-01` | paper | https://arxiv.org/abs/1910.01108 | ✓ 200 | `onnx` ONNX（opset 扩展）（Linux Foundation｜iface｜✓ 2026-09-24；关键词「模型|推理|量化」命中） | `ietf-json-schema` JSON Schema 2020-12（IETF/JSON Schema｜data｜✓ 2026-09-24；A 段载体锚（轮换 0；与主锚异层）） |
| `A14-02` | paper | https://arxiv.org/abs/2208.07339 | ✓ 200 | `oasis-openapi` OpenAPI 3.1（OpenAPI Initiative｜iface｜✓ 2026-09-24；关键词「接口|API|端点|服务|部署」命中） | `w3c-tabular-data` Tabular Data Model (CSVW)（W3C｜data｜✓ 2026-09-24；A 段载体锚（轮换 1；与主锚异层）） |
| `A14-03` | doc | https://onnxruntime.ai/docs/ | ✓ 200 | `onnx` ONNX（opset 扩展）（Linux Foundation｜iface｜✓ 2026-09-24；关键词「模型|推理|量化」命中） | `vega-lite` Vega-Lite v5（Vega｜form｜✓ 2026-09-24；A 段载体锚（轮换 2；与主锚异层）） |
| `A14-04` | spec | https://mlcommons.org/benchmarks/inference-mobile/ | ✓ 200 | `ieee-754` 浮点运算标准（IEEE｜data｜✓ 2026-09-24；域码 A14 专属绑定（轮换 1）） | `mermaid` Mermaid 图语言（Mermaid｜form｜✓ 2026-09-24；A 段载体锚（轮换 3；与主锚异层）） |
| `A14-05` | paper | https://arxiv.org/abs/1607.00133 | ✓ 200 | `gdpr` GDPR（EU｜gov｜✓ 2026-09-24；关键词「隐私|个人信息|去标识|合规|监管」命中） | `ietf-json-schema` JSON Schema 2020-12（IETF/JSON Schema｜data｜✓ 2026-09-24；A 段载体锚（轮换 0；与主锚异层）） |
| `A14-06` | paper | https://arxiv.org/abs/2312.11514 | ✓ 200 | `a2a` A2A 协议（Linux Foundation｜iface｜✓ 2026-09-24；关键词「多智能体|协同|编排」命中） | `ietf-json-schema` JSON Schema 2020-12（IETF/JSON Schema｜data｜✓ 2026-09-24；A 段载体锚（轮换 0；与主锚异层）） |
| `A14-07` | spec | https://mlcommons.org/benchmarks/inference-datacenter/ | ✓ 200 | `mlcommons-bench` MLPerf 基准（可扩展场景）（MLCommons｜eng｜✓ 2026-09-24；关键词「评测|基准|排行榜|跑分」命中） | `w3c-tabular-data` Tabular Data Model (CSVW)（W3C｜data｜✓ 2026-09-24；A 段载体锚（轮换 1；与主锚异层）） |
| `A14-08` | paper | https://arxiv.org/abs/2110.02178 | ✓ 200 | `ieee-754` 浮点运算标准（IEEE｜data｜✓ 2026-09-24；域码 A14 专属绑定（轮换 1）） | `vega-lite` Vega-Lite v5（Vega｜form｜✓ 2026-09-24；A 段载体锚（轮换 2；与主锚异层）） |
| `A14-09` | spec | https://covesa.global/ | ✓ 200 | `covesa-vss` Vehicle Signal Specification（COVESA｜iface｜✓ 2026-09-24；关键词「交通|出行|车机|车辆|导航」命中） | `mermaid` Mermaid 图语言（Mermaid｜form｜✓ 2026-09-24；A 段载体锚（轮换 3；与主锚异层）） |
| `A14-10` | paper | https://arxiv.org/abs/2302.04761 | ✓ 200 | `mcp` Model Context Protocol（Anthropic/MCP｜iface｜✓ 2026-09-24；关键词「工具调用|智能体|工作流|Agent」命中） | `w3c-prov-o` PROV-O 溯源本体（W3C｜gov｜✓ 2026-09-24；A 段载体锚（轮换 4；与主锚异层）） |
| `A14-11` | doc | https://uptane.org/ | ✓ 200 | `uptane` OTA 安全框架（Uptane｜gov｜✓ 2026-09-24；关键词「固件|OTA|升级」命中） | `ietf-json-schema` JSON Schema 2020-12（IETF/JSON Schema｜data｜✓ 2026-09-24；A 段载体锚（轮换 0；与主锚异层）） |
| `A14-12` | spec | https://owasp.org/www-project-top-10-for-large-language-model-applications/ | ✓ 200 | `owasp-llm` LLM 应用十大风险（OWASP｜gov｜✓ 2026-09-24；关键词「安全|越狱|红队|攻击|对抗」命中） | `w3c-tabular-data` Tabular Data Model (CSVW)（W3C｜data｜✓ 2026-09-24；A 段载体锚（轮换 1；与主锚异层）） |

## 2. 使用边界

- 锚用于**口径复核**（该细分的通行定义/评测口径从何而来），不表示 NF 复制了外部文本；本包正文自撰。
- **双锚分工**：主锚 = 该细分依据的域口径标准（可能与细分锚不同源，形成第二证据链）；辅锚 = 该细分产出（数据 / 契约 / 图表 / 图示 / 溯源）所承载的开放标准。
- 标准锚取自 `protocol/standards_catalog.json` 的**本机实测记录**（含取样标题与 sha256），可达性 false 如实标注，不假装可达。
- 锚不可达时按不可达记档，不影响本包口径面的机检（判据落在本包 schema 与度量族）。
- 锚版本漂移（规范改版）由维护者按需复核；本表不做自动追踪。
