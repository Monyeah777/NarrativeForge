# MCP 目录注册（NinFenz Content Gate）· 操作手册

> 面向 agent 的正面战场：把只读 MCP 服务登记进各目录，让 agent 与 MCP 客户端能搜到、一键装载。
> 真源：`protocol/mcp_package.json`（机读）· 人读投影：`docs/mcp.md` 的「上架材料」节 · 本目录 `server.json`（官方注册表格式，按 2025-09-29 schema 校验）
> 最后更新：2026-10-08

---

## 0 我们提交什么

| 字段 | 取值 |
|---|---|
| 名称（registry name） | `io.github.monyeah777/ninfenz` |
| 展示名 | NinFenz Content Gate |
| 一句话 | 给任何 AI agent 一个可校验的内容规范与资产底座——先查契约，再落笔 |
| 类目 | `content-creation` |
| 传输 | `stdio`（dual-era：modern `2026-07-28` + legacy `2025-11-25`） |
| 入口（零安装） | `npx -y ninfenz serve` |
| 入口（有检出） | `python scripts/nf.py serve` |
| 许可 | MIT |
| 站点 | https://ninfenz.dev/ · 仓库 https://github.com/Monyeah777/NinFenz |

能力面（只读）：10 tools（pipeline_ls · spec_ls · registry_query · library_search · library_read · pattern_read · knowledge_order · module_read · pipeline_read · asset_get）+ 1 prompt（assemble_guide）。**无写路径**。

---

## 1 官方 MCP Registry（registry.modelcontextprotocol.io）

发布用官方 `mcp-publisher`，命名空间所有权由 **GitHub 设备码登录**证明（我拿不到你的 OAuth，这一步只能你跑）。

```bash
# 1) 装发布器（Windows 用 Git Bash 跑更省事）
curl -L "https://github.com/modelcontextprotocol/registry/releases/latest/download/mcp-publisher_windows_amd64.tar.gz" | tar xz mcp-publisher

# 2) 在 packaging/mcp 目录（server.json 所在处）登录
cd packaging/mcp
./mcp-publisher login github      # 会给一个设备码，浏览器里输入并授权

# 3) 发布（会按 server.schema.json 校验 server.json）
./mcp-publisher publish
```

发布成功后可查：
```bash
curl -s "https://registry.modelcontextprotocol.io/v0/servers?search=ninfenz"
```

> 命名空间规则：`io.github.<你的 GitHub 用户名>/<服务名>`。我们填的是 `io.github.monyeah777/ninfenz`，与仓库属主一致，登录授权即可通过归属校验。
> package 归属：注册表还会核对 npm 包 `ninfenz` 确实存在且版本匹配（当前 1.0.0）。若将来发 1.0.1，`server.json` 的 `version` 与 `packages[0].version` 要同步改。

---

## 2 第三方目录（表单/仓库订阅，均可直接粘贴）

| 目录 | 入口 | 提交方式 | 备注 |
|---|---|---|---|
| **mcp.so** | https://mcp.so/submit | 表单：名称 / 描述 / 仓库 / 安装命令 | 流量最大的社区目录之一 |
| **Smithery** | https://smithery.ai/new | GitHub 登录后选仓库，或 CLI `npx @smithery/cli` | 支持自动读取仓库里的 server 配置 |
| **Glama** | https://glama.ai/mcp/servers | 表单或 PR 到其仓库 | 与 GitHub 同步较好 |
| **PulseMCP** | https://www.pulsemcp.com/submit | 表单 | 编辑器精选风格 |
| **Cline / VS Code MCP 市场** | 各自仓库 issue/PR | 按模板提 issue | 面向 IDE 用户 |
| **魔搭 ModelScope** | https://modelscope.cn/mcp | 表单 | 中国区 MCP 目录 |
| ~~百度 MCP 表单~~ | — | — | 与百度收录一并搁置（见 DEPLOY-search-submit.md §6） |

**复制粘贴用的描述块**（各表单通用）：

```
NinFenz Content Gate — 一个只读 MCP 服务器：把长内容的验收标准（协议 / 模块 / 管线 / 资产 / 馆藏）变成 agent 可调用的检索与取件工具面。
10 个只读工具 + 1 个装载引导 prompt，支持 modern 2026-07-28 与 legacy 2025-11-25 双协议版本，零第三方依赖，无写路径。
安装：npx -y ninfenz serve     仓库：https://github.com/Monyeah777/NinFenz     站点：https://ninfenz.dev/
```

---

## 3 发布前自证（本仓已有门禁，不要绕过）

```bash
# 工具面与运行时逐名一致（多一个少一个即 FAIL）
python scripts/nf.py mcp --json 2>/dev/null || python -m unittest tests.test_mcp_packaging
# 只读红线：不含任何写工具
python -m unittest tests.test_mcp_runtime tests.test_mcp_trust_meta
# 端到端真跑（协议级）
python scripts/nf.py serve   # 手工：喂 initialize → tools/list → tools/call
```

---

## 4 上架后自检

```bash
# 官方注册表能否搜到
curl -s "https://registry.modelcontextprotocol.io/v0/servers?search=ninfenz"
# 客户端真装（等价 agent 的行为）
npx -y --registry https://registry.npmjs.org ninfenz serve   # 应进入 stdio 服务，等待 JSON-RPC
```
