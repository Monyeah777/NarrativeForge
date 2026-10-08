# llms-install.md — 给 agent 的安装说明书（NinFenz / NF）

> 用途：任何 agent（Cline / Claude Code / Cursor / Codex / 自研）**只读这一份**就能把 NF 装好、自检、接上 MCP。
> 机器入口：https://ninfenz.dev/llms.txt　事实源：https://ninfenz.dev/facts.json　完整单文件：https://ninfenz.dev/llms-full.txt
> 许可 MIT —— 使用请保留 LICENSE 与署名；官方唯一入口 https://ninfenz.dev，**无付费版**，不需要下载任何第三方客户端。

## 0 一句话

NinFenz（宁封子，简称 NF）是**内容契约层**：用「协议 + 确定性门禁 + 可验证产物」让 AI 稳定产出长内容。
对 agent 而言它是一个只读知识/规范面 + 一套可复跑的确定性检查。

## 1 前置

| 需要 | 说明 |
|---|---|
| Python ≥ 3.11 | **仅标准库**，零第三方依赖 |
| Node ≥ 20 | 仅在使用 npm 包入口（`npx -y ninfenz`）时需要 |
| git | 仅克隆路线需要 |

## 2 安装（三条路，任选其一）

### A 零安装：用已发布的 npm 包（推荐给 agent，最快）

```bash
npx -y ninfenz --version       # 期望输出 nf 1.0.1
npx -y ninfenz doctor          # 体检：期望 16/16 通过
npx -y ninfenz serve           # 启动只读 MCP（stdio JSON-RPC，Ctrl+C 退出）
```

### B 克隆仓库（要改协议/资产、跑全量门禁时）

```bash
git clone https://github.com/Monyeah777/NinFenz.git
cd NinFenz
python scripts/nf.py doctor        # 16 项体检
python scripts/nf.py stats --check # 自述数字与真源一致
bash verify.sh                     # 全量门禁（L0–L2 · 40 检查 · 约 2225 单测；15 分钟量级）
```

### C 只要 MCP 面（浅克隆）

```bash
git clone --depth 1 https://github.com/Monyeah777/NinFenz.git
python scripts/nf.py serve
```

## 3 接进 MCP 客户端（stdio）

Claude Desktop / Cursor / Cline 通用配置（零安装，走 npm 包）：

```json
{
  "mcpServers": {
    "ninfenz": { "command": "npx", "args": ["-y", "ninfenz", "serve"] }
  }
}
```

本地检出（走仓库内脚本）：

```json
{
  "mcpServers": {
    "ninfenz": { "command": "python", "args": ["scripts/nf.py", "serve"], "cwd": "<克隆后的绝对路径>" }
  }
}
```

**能力面（只读，无写路径）**：10 个工具 —— `pipeline_ls` · `spec_ls` · `registry_query` · `library_search` · `library_read` · `pattern_read` · `knowledge_order` · `module_read` · `pipeline_read` · `asset_get`；1 个 prompt —— `assemble_guide`。
协议：modern `2026-07-28` 与 legacy `2025-11-25` 双版本并存；参数按 `inputSchema` 逐条校验（不合即 `-32602`）。

## 4 装完自检（agent 必做，全绿才算装好）

```bash
npx -y ninfenz doctor             # 体检 16/16
python scripts/nf.py stats --check  # 数字口径一致
python scripts/nf.py receipts       # 协议回执根一致
python scripts/nf.py audit verify   # 审计件与声明一致
python scripts/nf.py conformance    # 一致性分级（只读面不虚标）
```

协议级探针（验证 MCP 真的活着；把下列 4 帧喂给 stdin 即可）：

```text
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-11-25","capabilities":{},"clientInfo":{"name":"probe","version":"1"}}}
{"jsonrpc":"2.0","method":"notifications/initialized"}
{"jsonrpc":"2.0","id":2,"method":"tools/list"}
{"jsonrpc":"2.0","id":3,"method":"prompts/list"}
```

期望：第 1 帧回 `serverInfo.name = nf-repo-live` 与协议版本；第 2 帧回 10 个工具（各带 `inputSchema`）。

## 5 常见问题

| 现象 | 原因与处理 |
|---|---|
| `npx ninfenz` 报 404 | 本地 npm 指向镜像且镜像滞后：加 `--registry https://registry.npmjs.org` |
| `nf serve` 无输出 | 它是 stdio 服务，**等 stdin 的 JSON-RPC 帧**；直接回车不会打印菜单 |
| 门禁很慢 | 全量含 `2225` 个单测；只做日常检查用 `nf doctor` / `nf stats --check` |
| 想读全部协议 | https://ninfenz.dev/llms-full.txt（单文件）或 MCP 的 `library_search` / `spec_ls` |

## 6 出口面（agent 可直接抓）

| 入口 | 地址 |
|---|---|
| 站点（官方唯一） | https://ninfenz.dev/ |
| 清单 | https://ninfenz.dev/llms.txt |
| 完整单文件 | https://ninfenz.dev/llms-full.txt |
| 机读事实 | https://ninfenz.dev/facts.json |
| npm | https://www.npmjs.com/package/ninfenz |
| 仓库 | https://github.com/Monyeah777/NinFenz |