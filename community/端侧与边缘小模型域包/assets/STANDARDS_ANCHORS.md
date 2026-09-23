<!-- nf-asset: key="STANDARDS_ANCHORS" version="1.0" status="active" -->
# 权威锚表 · 端侧与边缘小模型

> 用途：本域 12 条细分各自的**外部权威锚**（规范 / 论文 / 参考实现）与**可达性实证**。外部锚只作口径与机制参照，**不作品质背书**（STRATEGY §3.2/§3.3）。
> 资产键：`STANDARDS_ANCHORS`｜实测日期：2026-09-22（本机 GET，HTTP 状态见下表；不可达如实记 `✗`，不假装可达）。

## 1. 锚表

| 条目键 | 锚类型 | URL | 可达性 | 可扩展标准（绑定） |
|---|---|---|---|---|
| `A14-01` | paper | https://arxiv.org/abs/1910.01108 | ✓ 200 | `onnx` ONNX（opset 扩展）（Linux Foundation；关键词「模型|推理|量化」命中） |
| `A14-02` | paper | https://arxiv.org/abs/2208.07339 | ✓ 200 | `oasis-openapi` OpenAPI 3.1（OpenAPI Initiative；关键词「接口|API|端点|服务|部署」命中） |
| `A14-03` | doc | https://onnxruntime.ai/docs/ | ✓ 200 | `onnx` ONNX（opset 扩展）（Linux Foundation；关键词「模型|推理|量化」命中） |
| `A14-04` | spec | https://mlcommons.org/benchmarks/inference-mobile/ | ✓ 200 | `onnx` ONNX（opset 扩展）（Linux Foundation；域码 A14 专属绑定（轮换 0）） |
| `A14-05` | paper | https://arxiv.org/abs/1607.00133 | ✓ 200 | `gdpr` GDPR（EU；关键词「隐私|个人信息|去标识|合规|监管」命中） |
| `A14-06` | paper | https://arxiv.org/abs/2312.11514 | ✓ 200 | `a2a` A2A 协议（Linux Foundation；关键词「多智能体|协同|编排」命中） |
| `A14-07` | spec | https://mlcommons.org/benchmarks/inference-datacenter/ | ✓ 200 | `mlcommons-bench` MLPerf 基准（可扩展场景）（MLCommons；关键词「评测|基准|排行榜|跑分」命中） |
| `A14-08` | paper | https://arxiv.org/abs/2110.02178 | ✓ 200 | `onnx` ONNX（opset 扩展）（Linux Foundation；域码 A14 专属绑定（轮换 0）） |
| `A14-09` | spec | https://covesa.global/ | ✓ 200 | `covesa-vss` Vehicle Signal Specification（COVESA；关键词「交通|出行|车机|车辆|导航」命中） |
| `A14-10` | paper | https://arxiv.org/abs/2302.04761 | ✓ 200 | `mcp` Model Context Protocol（Anthropic/MCP；关键词「工具调用|智能体|工作流|Agent」命中） |
| `A14-11` | doc | https://uptane.org/ | ✓ 200 | `uptane` OTA 安全框架（Uptane；关键词「固件|OTA|升级」命中） |
| `A14-12` | spec | https://owasp.org/www-project-top-10-for-large-language-model-applications/ | ✓ 200 | `owasp-llm` LLM 应用十大风险（OWASP；关键词「安全|越狱|红队|攻击|对抗」命中） |

## 2. 使用边界

- 锚用于**口径复核**（该细分的通行定义/评测口径从何而来），不表示 NF 复制了外部文本；本包正文自撰。
- 锚不可达时按不可达记档，不影响本包口径面的机检（判据落在本包 schema 与度量族）。
- 锚版本漂移（规范改版）由维护者按需复核；本表不做自动追踪。
