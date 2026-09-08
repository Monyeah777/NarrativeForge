# 41 波C C8 · MCP transport 扩展评估（streamable HTTP / SSE）

> 范围：在 stdio（现状）之外评估 streamable HTTP / SSE 远程装载通道；产出 = 评估文档 + 试点结论（做/不做 + 依据）。协议基线 = 33_v2.2.0_A5-MCP规范差距核查报告（G1/G2/G4 已勾销，stdio 会话协议就位）。

## 一、现状与基线

- 现役通道：`desktop/src/core/mcp_runtime.py` stdio transport——换行分隔 UTF-8 JSON-RPC，逐行读写，`resources/list` + `resources/read` 只读面（C2 最小安全层：白名单 uri、无 tools/prompts 写路径）。
- 协议事实（2025-11-25 schema）：stdio 与 streamable HTTP 均为受支持 transport；streamable HTTP 用 JSON-RPC over HTTP（POST + SSE 响应流），需服务端监听端口。
- 消费方假设：作者本机 agent 会话经 stdio 拉起 `nf serve`；真实远程客户端（Claude Desktop 类）尚未回填 E3 实测。

## 二、扩展差距评估

streamable HTTP / SSE 相比 stdio 的新增面：

| 维度 | 差距 | 说明 |
|---|---|---|
| 服务形态 | 从子进程 stdio 到长驻 HTTP 服务 | 需端口监听、生命周期管理、多会话并发 |
| 安全面 | 网络暴露 | 只读 resources 也需鉴权/白名单/绑定策略；与 C2「只读最小面」叠加后攻击面变大 |
| 能力收益 | 远程装载 | 当前能力表 = resources 只读 + 未来 C7 tools/prompts 只读——远程消费方尚无真实需求回填 |
| 运维 | 部署 | 需托管进程/反代/TLS；基础层零第三方依赖红线内无现成 web 栈 |

## 三、试点结论：暂不做（回冻结）

**结论：不做 streamable HTTP / SSE 试点**，理由：

1. **无消费方**：E3 标准 MCP 客户端实测未回填前，远程 transport 的收益无人消费（按需装配哲学：不产没人消费的东西）。
2. **安全优先**：远程 transport 必须叠加鉴权/白名单/端口治理——在 E3 回填、确有远程装载需求前，网络面引入的风险大于收益。
3. **路径清晰**：stdio 已覆盖作者本机 agent 消费场景；后续如需远程，评估项已列于此文档，可随 E3 回填后重启。

回冻结条件：E3 标准 MCP 客户端实测回填 **且** 出现真实远程装载需求 → 重启本评估并试点 streamable HTTP（先 tools/prompts 只读面，不引入写路径）。
