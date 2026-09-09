# AI_ROUTING · 按连接能力选线（AI 入口路由层）

> ⛔ 操作指令：按能力边界选线并执行；拿不准模块/资产一律不编造。
> 最后更新：2026-09-09

## 路由表（A/B1/B2）

| 身份 | 能力边界 | 执行通道 |
|---|---|---|
| Agent（有 API / 能执行代码） | clone、verify、接 MCP | A 线：`nf serve` MCP（详见 `docs/mcp.md`） |
| 免费客户端 AI（非 API，能读 raw/下载） | 读 raw、下载文件 | B1 线：`agent_组装指令包_v0.2.md` 完整装配 |
| 纯粘贴客户端 | 只能读粘贴文本 | B2 已免除，自取 `docs/paste_card.md` |

## B1 完整装配

1. 读 `agent_组装指令包_v0.2.md`（取货顺序/选件铁律/骨架/自检）。
2. 按指令包取件：01 → 02 → 06 → 07 → 所需 community 包。
3. 选件 → 组装 → 过 `##7. 自检清单` → 输出完整版 md，缺口如实声明。

## 产出验收

八段骨架齐全 / 模块编号合法 / 模块要素齐 / 事件闭合 / 自检逐条自答；任一否先修再交付。

## 用户侧模型参考（2026-09-06 四模型实测）

| 场景 | 推荐 | 依据 |
|---|---|---|
| 快速迭代 | DeepSeek | 效率高、协议理解深 |
| 正式交付 .md | 千问 | 直接产出 md 文件 |
| 终稿查漏 | Kimi | 最长最细、自检严 |
| 纯粘贴 | — | B2 已免除 |

## 云端图书馆导购（AI 接待员）

开场报菜单：组装新世界 / 报编号取件 / 描述需求推荐 / 随机盲盒 / 投稿入库。规则：镜像换前缀、raw 喂 AI；编号大小写先读 `library/ALIAS.md`；馆内没有严禁编造，引导现场创作+投稿。详见 `ROUTES.md`。

## 取件基底

- GitHub raw：`https://raw.githubusercontent.com/Monyeah777/NarrativeForge/main/`
- Gitee raw（国内）：`https://gitee.com/monyeah777/narrative-forge/raw/main/`
