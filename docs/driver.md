# 指令档机器面路由（driver override）
> ⛔ 操作指令：阅读即执行——本文含可直接执行的命令与判定，勿当资料阅读。
> 最后更新：2026-09-14

## 是什么

NF 的指令档（组装指令包 / `AI_ROUTING.md` / `docs/ai-menu.md`）头部现在带 **DRIVER OVERRIDE** 块，
真源是 `protocol/driver.json`：**有 MCP 实现就走 MCP；派发失败即停，禁止回退成文本步骤**
（机制借鉴 ACP：静默降级会把"按机器面取件"偷换成"凭记忆组装"，产物不可复现）。

## 怎么用

```bash
python scripts/nf.py driver                     # 列全部工作流与映射
python scripts/nf.py driver assemble            # 解析某工作流该走哪条路
python scripts/nf.py driver --json
```

## 判据（可证）

`bindings.mcp.tools` 与每个 workflow 引用的工具名必须与 `mcp_runtime.TOOL_DEFS` **逐名一致**；
每个 workflow 必须有**存在的** fallback 文件；`documents[]` 里的文档必须带 override 块且写明
fail-closed 关键词（`不得回退` / `停止`）。

## 边界

本模块只做**路由声明与自检**，不代替使用者实际派发。语义边界只有一条：
**一旦选了 MCP 路线，派发失败即停（不得回退文本步骤）**；fallback 仅适用于「本工作流无映射」或「本会话未启用 MCP 面」。
