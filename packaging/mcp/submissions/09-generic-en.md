# 09 · 通用块（英文）—— 任何未列出的目录站都能用

```text
Name: NinFenz Content Gate
Tagline: Read-only MCP server for a content contract layer: protocol, modules, pipelines, assets, library.
Description: A read-only MCP server that turns long-form acceptance criteria (protocol specs, modules, pipelines, assets, knowledge library) into agent-callable retrieval tools. 10 read-only tools + 1 prompt (assemble_guide); dual protocol era (2026-07-28 modern / 2025-11-25 legacy); zero third-party deps (Python stdlib); no write paths.
Install: npx -y ninfenz serve
Repo: https://github.com/Monyeah777/NinFenz
Site: https://ninfenz.dev/
Category: content-creation
Tags: mcp, content-contract, spec-driven, verification, knowledge-base, python, llm
License: MIT
```

## 传输配置（stdio）—— 只填 Stdio，另两种留空

我们**只提供 stdio**（本地进程）；Streamable HTTP 与 SSE 未提供 → 表单里留空即可（未配置的方式不会展示在详情页）。

**完整配置（`mcpServers` 形式，直接整段粘）**

```json
{
  "mcpServers": {
    "ninfenz": {
      "command": "npx",
      "args": ["-y", "ninfenz", "serve"]
    }
  }
}
```

**字段式（表单把 command / args 拆开问时）**

| 字段 | 值 |
|---|---|
| 名称 / name | `ninfenz` |
| command | `npx` |
| args | `-y ninfenz serve`（或数组 `["-y","ninfenz","serve"]`） |
| env | 留空（无需任何密钥/变量） |

**备用命令**

- 本地 npm 镜像滞后时：`npx -y --registry https://registry.npmjs.org ninfenz serve`
- 本地检出时：command `python` · args `["scripts/nf.py","serve"]` · cwd 填克隆路径
- Windows 客户端若找不到 `npx`：command 改 `cmd` · args `["/c","npx","-y","ninfenz","serve"]`

**同页常问的其它字段**

| 字段 | 值 |
|---|---|
| 传输 / transport | `stdio` |
| 协议版本 | modern `2026-07-28` + legacy `2025-11-25`（双版本并存） |
| 工具数 / prompts | 10 个只读工具 + 1 个 prompt（`assemble_guide`）；`additionalProperties: false`，参数不合即 `-32602` |
| 是否只读 | 是（无写路径） |
