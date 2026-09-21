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

## 幂等声明（RFC 9110 §9.2.2）

契约**默认 idempotent**——同请求重放须得同结果且无副作用；例外只在顶层
`idempotency_exceptions` 登记（每条给 `mode` / `key` / `why`）：非幂等端点（如
`bench.evaluate` 会落评测记录）`key=required` 时客户端 MUST 带幂等键、服务端 MUST 据此去重。
判据：例外 id 须在契约内、`mode` 与 `key` 在词表内、`why` 非空、要求幂等键时
`conventions.idempotency` 必须在场。派生面同步标注：`nf interop --kind openapi` 的每个
operation 带 `x-nf-idempotency`。

## 边界

契约存在 ≠ 服务存在。真正实现服务时把 `status` 改成 `implemented` 并补实测记录；此前不得对外宣称有服务。
