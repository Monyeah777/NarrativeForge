# 第三方 MCP 目录提交包（NinFenz Content Gate）

> 官方注册表走 `mcp-publisher`（流程见 `SUBMIT.md`）；本文件负责**第三方目录**：要准备的材料、渠道清单、逐站逐步流程。
> 一次性把材料备齐后，剩下的动作在多数站只需「粘贴 + 点提交」。
> 最后更新：2026-10-08

---

## 0 渠道总表（先看谁做什么）

| 渠道 | 提交形式 | 谁执行 | 前置 | 当前状态 |
|---|---|---|---|---|
| 官方 MCP Registry | `mcp-publisher` CLI | **我** | 已满足（npm 1.0.1 带 `mcpName`） | ✅ **已上架 v1.0.1**（2026-10-08） |
| **awesome-mcp-servers**（最大聚合列表） | GitHub **PR** 改 README | 你（浏览器 2 分钟） | 无 | 待做（下面给现成整行） |
| **Cline MCP Marketplace** | GitHub **Issue**（模板） | 你 | 400×400 PNG ✅ · `llms-install.md` ✅ · Cline 实测一次 | 待做 |
| **mcp.so** | 站内表单 | 你 | 无 | 待做 |
| **Glama** | 站内认领/提交（GitHub 登录） | 你 | 无 | 待做 |
| **PulseMCP** | 站内表单 | 你 | 无 | 待做（我这边 IP 被其 Cloudflare 拦） |
| 魔搭 ModelScope MCP 广场 | 站内表单 | 你 | 魔搭账号 | 可选 |
| mcpservers.org · mcpmarket.com · mcpdirectory.ai | 轻量表单 | 你 | 无 | 可选 |
| GitHub MCP 目录（github.com/mcp） | 通常随官方注册表收录 | — | 官方注册表先上架 | 观察 |

**推荐顺序**：官方注册表（我）→ awesome PR（你，收益最大）→ Cline（你，需实测）→ mcp.so / Glama / PulseMCP（你，纯粘贴）。

---

## 0.5 直达链接（逐条实测过状态码；标 302/403 的是"脚本被拦、浏览器正常"）

### A 你需要点开的（提交 / 认领）

| # | 渠道 | 直达链接 | 实测 | 你要做的动作 |
|---|---|---|---|---|
| 1 | awesome-mcp-servers | https://github.com/punkpeye/awesome-mcp-servers/edit/main/README.md | 302（→ 登录页，浏览器正常） | 粘 §2.1 那一行 → Propose changes → PR 标题末尾加 `🤖🤖🤖` |
| 1b | ↑ 投稿规则 | https://github.com/punkpeye/awesome-mcp-servers/blob/main/CONTRIBUTING.md | 200 | 读一眼格式与 agent 快速通道说明 |
| 2 | Cline Marketplace | https://github.com/cline/mcp-marketplace/issues/new?template=mcp-server-submission.yml | 302（→ 登录页） | 填仓库 URL + 上传 `icon-400.png` + 粘贴描述 + 勾实测确认 |
| 3 | mcp.so | https://mcp.so/submit | 403（机器人拦截，浏览器正常） | 粘 §1 材料包 |
| 4 | Glama | https://glama.ai/mcp/servers?query=ninfenz | 200 | 有条目 → Claim；没有 → 提交仓库地址 |
| 5 | PulseMCP | https://www.pulsemcp.com/submit | 403（机器人拦截） | 粘 §1 材料包 |
| 6 | 魔搭 ModelScope | https://modelscope.cn/mcp | 200 | 需魔搭账号，粘中文块 |
| 7 | mcpservers.org | https://mcpservers.org/submit | 200 | 表单 |
| 8 | mcpmarket.com | https://mcpmarket.com/ | 200 | 页脚提交入口 |
| — | mcpdirectory.ai | https://mcpdirectory.ai/ | **000（本次不可达）** | 建议跳过 |

### B 我这边用、你也可以自查的

| 用途 | 直达链接 | 实测 |
|---|---|---|
| 官方注册表（人看） | https://registry.modelcontextprotocol.io/ | 200 |
| 官方注册表（机器查） | https://registry.modelcontextprotocol.io/v0/servers?search=ninfenz | 脚本 000（本机代理路径不稳），发布器可正常读写 |
| MCP 发布器下载 | https://github.com/modelcontextprotocol/registry/releases/latest | 302→release |
| npm 包页 | https://www.npmjs.com/package/ninfenz | 403（机器人拦截，浏览器正常） |
| 发布工作流（可看运行历史） | https://github.com/Monyeah777/NinFenz/actions/workflows/npm-publish.yml | 200 |
| 站点机器入口 | https://ninfenz.dev/llms.txt | 200 |
| 完整单文件 | https://ninfenz.dev/llms-full.txt | 200 |
| 机读事实 | https://ninfenz.dev/facts.json | 200 |
| 仓库根安装说明（待推送后生效） | https://github.com/Monyeah777/NinFenz/blob/main/llms-install.md | 待推送 |
| 图标下载（待推送后生效） | https://raw.githubusercontent.com/Monyeah777/NinFenz/main/packaging/mcp/assets/icon-400.png | 待推送 |

---

## 0.6 每个渠道要粘/要传的直达文件（一键复制）

| 渠道 | 要粘贴 / 要上传的文件 | 内容形态 |
|---|---|---|
| awesome-mcp-servers | [submissions/01-awesome-mcp-servers.md](submissions/01-awesome-mcp-servers.md) | 一整行 markdown + PR 标题 |
| Cline Marketplace | [submissions/02-cline-marketplace.md](submissions/02-cline-marketplace.md) + **上传** [assets/icon-400.png](assets/icon-400.png) | Issue 正文整段 + 400×400 PNG |
| mcp.so | [submissions/03-mcp-so.md](submissions/03-mcp-so.md) | 表单逐字段 |
| Glama | [submissions/04-glama.md](submissions/04-glama.md) | 仓库地址 + 描述块 |
| PulseMCP | [submissions/05-pulsemcp.md](submissions/05-pulsemcp.md) | 表单逐字段 |
| 魔搭 ModelScope | [submissions/06-modelscope.md](submissions/06-modelscope.md) | 中文表单逐字段 |
| mcpservers.org | [submissions/07-mcpservers-org.md](submissions/07-mcpservers-org.md) | 表单逐字段 |
| mcpmarket.com | [submissions/08-mcpmarket.md](submissions/08-mcpmarket.md) | 表单逐字段 |
| 其它（英文站） | [submissions/09-generic-en.md](submissions/09-generic-en.md) | 通用块 |
| 其它（中文站） | [submissions/10-generic-zh.md](submissions/10-generic-zh.md) | 通用块 |

> 每个文件都是"打开 → 全选 → 复制 → 粘贴"的单一用途件；GitHub 文件页右上角自带复制按钮。
> 状态：这些文件与 `19a48de5` 一起在本地产出，**推送落地后**上面的 GitHub 链接才可点（本地路径现在就能用）。

## 1 通用材料包（备一次，处处粘贴）

| 字段 | 取值 |
|---|---|
| 名称（registry name） | `io.github.Monyeah777/ninfenz` |
| 展示名 | **NinFenz Content Gate** |
| 一句话（EN） | Read-only MCP server for a content contract layer: protocol, modules, pipelines, assets, library. |
| 一句话（ZH） | 给任何 AI agent 一个可校验的内容规范与资产底座——先查契约，再落笔。 |
| 类目 | `content-creation`（备选：`developer-tools` / `knowledge-management`） |
| 标签 | `mcp` `content-contract` `spec-driven` `verification` `knowledge-base` `python` `llm` |
| 传输 | `stdio`（modern `2026-07-28` + legacy `2025-11-25` 双协议） |
| 安装（零安装） | `npx -y ninfenz serve` |
| 安装（检出） | `python scripts/nf.py serve` |
| 工具面 | 10 只读工具 + 1 prompt（`assemble_guide`）；**无写路径** |
| 许可 | MIT |
| 仓库 | https://github.com/Monyeah777/NinFenz |
| 站点 | https://ninfenz.dev/ |
| 图标 | `packaging/mcp/assets/icon-400.png`（Cline 要 400×400）· `icon-512.png`（其它站） |
| 安装说明书 | 仓库根 `llms-install.md`（agent 只读这一份即可装） |

**可粘贴描述块（中文）**

```text
NinFenz Content Gate —— 只读 MCP 服务器：把长内容的验收标准（协议 / 模块 / 管线 / 资产 / 馆藏）变成 agent 可调用的检索与取件工具面。
10 个只读工具 + 1 个装载引导 prompt；支持 modern 2026-07-28 与 legacy 2025-11-25 双协议；零第三方依赖（Python 标准库）；无写路径。
安装：npx -y ninfenz serve    仓库：https://github.com/Monyeah777/NinFenz    站点：https://ninfenz.dev/
```

**可粘贴描述块（English）**

```text
NinFenz Content Gate — a read-only MCP server that exposes a content contract layer to agents: protocol specs, modules, pipelines, assets and the knowledge library.
10 read-only tools + 1 prompt (assemble_guide); dual protocol era (2026-07-28 modern / 2025-11-25 legacy); zero third-party deps (Python stdlib); no write paths.
Install: npx -y ninfenz serve    Repo: https://github.com/Monyeah777/NinFenz    Site: https://ninfenz.dev/
```

---

## 2 逐渠道详细流程

### 2.1 awesome-mcp-servers（先做这个：一次 PR 覆盖最大受众）

入口：https://github.com/punkpeye/awesome-mcp-servers

1. 打开 README，点右上角铅笔（Edit）→ GitHub 会自动帮你 fork 一份；
2. 在 Servers 列表里按字母序找到插入位置（`M` 段附近），**粘这一行**：

```markdown
- [Monyeah777/NinFenz](https://github.com/Monyeah777/NinFenz) 🐍 🏠 - Content contract layer as a read-only MCP server: protocol specs, modules, pipelines, assets and the knowledge library for long-form content (Python stdlib only, no write paths).
```

3. 提交：Commit changes → Propose changes → 创建 PR；
4. **在 PR 标题末尾加 `🤖🤖🤖`**：官方 CONTRIBUTING 写明这是**agent PR 快速通道**（"Just add 🤖🤖🤖 to the end of the PR title to opt-in. Merging your PR will be fast-tracked."）；
5. 注意格式：条目前是 `- [owner/repo](url)`，后接 **legend emoji** —— `🐍`（Python 代码库）、`🏠`（本地服务）；描述一句话，句末不加句号也可（照抄上面的行最省事）。

> 该列表只收「有公开仓库、可自行安装」的 server（远程托管型另去 awesome-remote-mcp-servers）—— 我们满足。

### 2.2 Cline MCP Marketplace

入口（提交 issue，模板已就绪）：https://github.com/cline/mcp-marketplace/issues/new?template=mcp-server-submission.yml

1. **GitHub Repo URL**：`https://github.com/Monyeah777/NinFenz`（嵌套路径也行）；
2. **Logo**：上传 `packaging/mcp/assets/icon-400.png`（要求 400×400 PNG）；
3. **Reason for Addition**：把 §1 的中文或英文描述块粘进去，并补一句「零第三方依赖、无写路径、双协议版本」；
4. **实测确认**：审核要求「把 README 和/或 `llms-install.md` 交给 Cline，观察它能成功装好」—— 请在 Cline 里真跑一次：把仓库根的 `llms-install.md` 贴给 Cline，看它是否完成安装并列出工具（仓库根本次新增了这份文件，就是为这一步）；
5. 提交后等人工审核。审核四个维度：社区活跃度 / 维护者可信度 / 项目成熟度 / 安全（敏感域从严）。

### 2.3 mcp.so

入口：https://mcp.so/submit

1. 打开表单，字段以页面为准（通常：名称 / 一句话 / 仓库 URL / 安装命令 / 类目 / 图标）。页面是前端渲染，我这边取不到字段文本，**你照着 §1 粘贴即可**；
2. 名称填 `NinFenz Content Gate`，仓库填 GitHub 地址，安装命令填 `npx -y ninfenz serve`；
3. 提交后一般几天内出现；可在站内搜索 `ninfenz` 复核。

### 2.4 Glama

入口：https://glama.ai/mcp/servers

1. 用 GitHub 登录；Glama 会自己扫 GitHub 上的 MCP 仓库，先在站内搜 `NinFenz` 或 `ninfenz`；
2. 若已有条目 → 点 **Claim** 认领（证明你是仓库属主）；若没有 → 用站内 "Add server / Submit" 提交仓库地址 + §1 描述；
3. Glama 会给条目算安全/质量分，并把徽章回链到仓库（可后续把它加进 README 徽章位，增加互相引用）。

### 2.5 PulseMCP

入口：https://www.pulsemcp.com/submit

> 提示：该站有 Cloudflare 人机校验，我这边的出口 IP 被拦（返回 "Attention Required"），所以只能你用自己的浏览器提交。

1. 打开表单，粘 §1 的名称 / 描述 / 仓库 / 安装命令；
2. 他们在审核通过后会发一封确认邮件（若表单要邮箱，用你能收信的邮箱）。

### 2.6 魔搭 ModelScope MCP 广场（可选，中国区）

入口：https://modelscope.cn/mcp　· 需要魔搭账号；字段同上（名称/描述/仓库/安装命令），中文材料直接用 §1 中文块。

### 2.7 轻量目录（可选，几分钟）

| 站点 | 入口 | 说明 |
|---|---|---|
| mcpservers.org | https://mcpservers.org/submit | 表单 |
| mcpmarket.com | https://mcpmarket.com/ | 提交入口在页脚 |
| mcpdirectory.ai | https://mcpdirectory.ai/ | 表单 |

### 2.8 官方 MCP Registry（回顾：已自动化）

发布链路：`packaging/mcp/server.json`（schema `2025-12-11`）→ `mcp-publisher validate` → `mcp-publisher login github --token <PAT>` → `mcp-publisher publish`。
前置硬条件：**npm 包内必须带 `mcpName`**（注册表校验 npm 归属），且 `server.json` 的 `version` / `packages[0].version` 必须与已发布版本同值 —— 2026-10-08 实证：版本不同值时注册表会去查旧版本并报 "missing 'mcpName' field"，改齐后一次通过。

**已上架（2026-10-08）**：`io.github.Monyeah777/ninfenz@1.0.1`；查询（注意 search 区分大小写，用 `NinFenz` 或 `Monyeah777` 才命中）：

```bash
curl -s "https://registry.modelcontextprotocol.io/v0/servers?search=NinFenz"
```

---

## 3 上架后自检（每站上完跑一遍）

```bash
# 官方注册表
curl -s "https://registry.modelcontextprotocol.io/v0/servers?search=ninfenz"
# 客户端视角（等价 agent 的装载动作）
npx -y --registry https://registry.npmjs.org ninfenz serve   # 应进入 stdio，等待 JSON-RPC
```

---

## 4 缺件与责任人

| 事项 | 谁 | 状态 |
|---|---|---|
| 400×400 PNG 图标 | 我 | ✅ `packaging/mcp/assets/icon-400.png`（同目录 512 版） |
| `llms-install.md`（Cline 一键安装要读） | 我 | ✅ 仓库根已新增 |
| 官方注册表发布 | 我 | ⏳ 等 1.0.1 |
| awesome PR / Cline issue / mcp.so / Glama / PulseMCP | 你 | 待做（材料已备） |
| Cline 里真跑一次安装（审核会问） | 你 | 待做 |
| 魔搭账号（可选） | 你 | — |

## 5 时效与预期

| 渠道 | 通常时长 |
|---|---|
| 官方 MCP Registry | 分钟级（发布即生效） |
| awesome-mcp-servers PR | 几小时–几天（标题带 `🤖🤖🤖` 走快速通道） |
| Cline Marketplace | 数天–数周（人工审核，看社区指标） |
| mcp.so / Glama / PulseMCP | 数天 |

> 一个共同点：这些目录都**只读公开仓库/包**，没有需要 CI 凭证的写入面 —— 所以除登录动作外，材料一次备好就不用再回来改。