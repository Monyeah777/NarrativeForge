# 服务端点契约（endpoint）
> ⛔ 操作指令：阅读即执行——本文含可直接执行的命令与判定，勿当资料阅读。
> 最后更新：2026-09-14

## 是什么

`protocol/endpoint_contract.json` 把 NF **已实现**的能力声明成 HTTP 面（机制借鉴
microsoft/ai-chat-protocol 的 API 规格）：`status: proposed`——**服务本体未实现**，本契约只固定形状。

## 怎么用

```bash
python scripts/nf.py endpoint
python scripts/nf.py endpoint --json
```

## 判据（可证，防"纸面能力"）

每个端点的 `maps_to` 必须解析为**当下真实存在**的 CLI 子命令（在 `scripts/nf.py` 的
subparser 注册表内）或 MCP 工具（在 `mcp_runtime.TOOL_DEFS` 内）；`method`/`status` 在词表内；
`streaming: true` 的端点必须声明 SSE 约定；`id` 与 `method+path` 唯一。

## 边界

契约存在 ≠ 服务存在。真正实现服务时把 `status` 改成 `implemented` 并补实测记录；此前不得对外宣称有服务。
