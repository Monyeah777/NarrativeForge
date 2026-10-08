# 02 · Cline MCP Marketplace —— Issue 正文（复制整段）

> 用途：打开 https://github.com/cline/mcp-marketplace/issues/new?template=mcp-server-submission.yml 并粘进对应字段。
> **上传附件**：仓库里的 `packaging/mcp/assets/icon-400.png`（要求 400×400 PNG）。

```text
### GitHub Repo URL
https://github.com/Monyeah777/NinFenz

### Logo
（附件已上传：icon-400.png，400×400 PNG）

### Reason for Addition
NinFenz Content Gate 是一个只读 MCP 服务器：把长内容的验收标准（协议 / 模块 / 管线 / 资产 / 馆藏）变成 agent 可调用的检索与取件工具面。
给 Cline 用户的价值：
- 10 个只读工具 + 1 个 prompt（assemble_guide）；无写路径，不会改用户仓库；
- 零第三方依赖（Python 标准库），一条 `npx -y ninfenz serve` 即可装载；
- 双协议版本（modern 2026-07-28 + legacy 2025-11-25），参数按 inputSchema 逐条校验（不合即 -32602）；
- 仓库自带确定性门禁（check1-40 · PASS=72 · 约 2225 单测），安装说明见仓库根 `llms-install.md`。

### 实测确认（先在 Cline 里跑一次，再留下这句）
把仓库根 `llms-install.md` 交给 Cline，安装成功并能列出 10 个工具。
```
