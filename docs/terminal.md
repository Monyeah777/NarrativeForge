# NF 终端（`nf shell`）——端壳退役后的人机入口

> 最后更新：2026-09-25

> ⛔ 操作指令：本文含可直接执行的命令与判定，读到即执行；勿当资料阅读。

## 这个终端是什么

NF 桌面 GUI 端壳已于 2026-09-09 永久退役（记录见 `L3_FROZEN.md`），公开面收敛为
「协议 + core 库 + CLI」。人机交互面随之真空，`nf shell` 补的就是这一层：把**既有**
CLI 命令面按能力菜单组织成可交互会话——读一行 → 解析 → 闸门 → 分派 → 打印。

三条硬约束（与仓库红线同源）：

1. **零第三方依赖**：只用 Python stdlib，不用 curses（Windows 无该模块）与 GUI 工具包。
2. **确定性**：同一输入两次运行逐字节一致（`--exec` 即回归面）。
3. **安全闸门**：写入类命令默认拒跑，须显式确认（交互输入 yes，或显式 `--yes`）。

## 最快上手（两条命令）

```sh
./scripts/nf                       # POSIX：无参数即进交互终端
python scripts/nf.py shell         # 跨平台等价写法（Windows 亦可用 scripts\nf.cmd）
```

进入后：输入 `0`–`7` 看能力区示例，`/menu` 重看菜单，`/help` 看用法，`quit` 退出。
任意命令可直接直通，例：`nf doctor`、`nf market --list`、`nf assemble "西幻生存"`。

## 能力菜单（端壳七区 → CLI 命令面）

| 键 | 能力区 | 对应命令面（示例） |
|---|---|---|
| 0 | 环境自检 | `nf doctor` |
| 1 | 一键演示世界 | `nf demo` |
| 2 | 需求 → 装配计划 | `nf assemble "<需求>"` · `nf assemble … --check <成品.md>` |
| 3 | 全链生产 | `nf run --pipeline <管线.md> --modules … [--seed]` |
| 4 | 校验与体检 | `nf lint` · `nf conformance` · `nf module verify` |
| 5 | 货架与资产 | `nf market --list` · `nf asset ls` · `nf asset inventory` |
| 6 | 管线与模块 | `nf pipeline new …` · `nf module ls` |
| 7 | 帮助与命令面 | `nf --help` · `nf help <cmd>` |

菜单真源是 `desktop/src/core/terminal.py` 的 `ZONES`；**菜单只许指向真实命令**——
由 verify check39 与 `desktop/tests/test_terminal.py` 共用同一判据逐条断言
（`terminal.example_resolves`），新增能力须先落 CLI 再登记菜单。

## 交互语法

| 输入 | 行为 |
|---|---|
| `0`–`7` | 看该能力区的说明与可复制示例 |
| `/menu` `/zone 4` | 重看菜单 / 看某区示例 |
| `/find <词>`（`/search` 同义） | 在**全部命令面**上检索（命中给命令 + 一句话用途；未命中给候选） |
| `/commands [过滤]` | 列出全部可达命令（顶层 + 二级，可按子串过滤） |
| `/map [族或片段]` | **能力地图**：把全部顶层命令按能力族策展呈现（8 族），可过滤 |
| `/complete <前缀>` · 行尾 `Tab` | **补全**：命令 / 二级子命令 / 旗标 / 斜杠命令 / 能力族前缀 |
| `/history [n]` | 看历史（最近 n 条）；`quit` 与 Tab 行不入历史 |
| `/set [k=v …]` | 改视图设置（`color` / `width` / `limit`）；无参数打印当前值 |
| `/form [id]` | **写盘表单**：不带 id 列全部；带 id 开始逐项追问（参数填齐 → 组装命令 → 二次确认） |
| `/cancel` | 中止进行中的表单 / 动作（不执行任何写盘） |
| `/help` 或 `/help <cmd>` | 转 CLI 帮助面（等价 `nf help …`） |
| `nf <args…>` 或 `<args…>` | 直通 CLI（`nf` 前缀可省） |
| `quit` `exit` `q` `退出` | 退出会话 |

健壮性（对标顶尖 CLI 终端的几件标配）：**Ctrl-C 只取消当前行、不杀会话**；行尾 `\` **续行**（多行命令）；行内 `#` 起注释（引号内的 `#` 保留）；命令写错时给**拼错建议**（编辑距离 ≤3），而不是把 60 条命令的 usage 甩一脸。

## 命令面检索（「最全功能」的可发现性）

终端的瓶颈从来不是命令少，而是**找不到**——CLI 有 64 个顶层命令、135 条含二级的入口。三条入口解决它：

```bash
python scripts/nf.py shell --map                 # 能力地图：8 个能力族，覆盖全部 64 个命令
python scripts/nf.py shell --map 治理            # 只看某一族（也可按命令片段过滤）
python scripts/nf.py shell --commands            # 列出全部可达命令（顶层 + 二级）
python scripts/nf.py shell --commands asset      # 按子串过滤
python scripts/nf.py shell --search 装配         # 按关键词检索（未命中退出 2，可进脚本）
python scripts/nf.py shell --verify              # 终端自检（索引/策展/菜单三面，退出码即结论）
python scripts/nf.py shell --verify --deep       # 活体档：真跑一条只读命令 + 落点可写性 + 环境事实
python scripts/nf.py shell --verify --json       # 机器面（纯 JSON：ok / issues / stats）
python scripts/nf.py shell --complete "/ma"      # 斜杠命令补全 → /map、/menu…
python scripts/nf.py shell --complete "nf layers --"   # 旗标补全 → --json / --verify / --write
python scripts/nf.py shell --history <文件>      # 跨会话历史（缺省 <NF_HOME>/shell_history）
```

会话内等价形态是 `/map [族]`、`/commands [过滤]` 与 `/find <词>`。三层保证「最全」不是宣称：

① **索引由 CLI 的 argparse 面派生**（终端不维护第二份命令表）；② **能力地图把每个命令恰好归入一个族**（`start / forge / shelf / verify / library / govern / integrate / meta`），「未策展」即报；③ 判据**单源**——`nf shell --verify`（给人跑）与 verify check39（给门禁跑）调用同一个 `terminal.self_check`，所以「终端说没问题」与「门禁说没问题」永远同一套语义。

## 活体自检与机器面

- **`--verify --deep`（活体档）**：在静态面（索引/策展/菜单）之上再核**本机环境**——真跑一条只读命令（`nf layers --verify`）并核对退出码、探测历史/会话落点**可写性**（沿祖先目录判断，**不落探针文件**）、如实报告 TTY / readline / 分页器现状。所有结论与静态档同一套口径（`terminal.deep_check` 调 `self_check`），退出码即结论。
- **机器面（`--json`）**：`--commands --json`（逐条命令 + 摘要 + 旗标）、`--map --json`（族分区）、`--form --json`（表单真源）/ `--form <id> --json`（组装计划 argv）、`--verify [--deep] --json`（ok / issues / stats）。**输出必须是纯 JSON**——活体输出会被捕获进字段而不是混进 stdout，check39 直接断言这一点。

## 写盘表单与会话状态（会改仓库的动作由人安全驱动）

`nf` 的写盘命令都要参数齐 + `--yes`，对人是负担。终端把它拆成**逐项追问**：`/form <id>` 开始，一次问一项（可选项**空行跳过**），填齐后打印**组装好的命令**再问 `yes/no`，确认后才执行——而且最终仍走同一条**写盘闸门**（终端不绕过它）。当前 8 张表覆盖真实写盘点：`deprecate-module` / `restore-module` / `types-write` / `stats-write` / `asset-add` / `register-apply` / `rename-apply` / `receipts-write`。

非交互也能用（dry-run 优先）：

```bash
python scripts/nf.py shell --form                                # 列全部表单
python scripts/nf.py shell --form stats-write                    # 只组装 + 打印（dry-run）
python scripts/nf.py shell --form deprecate-module --answer file=community/x/M1.md --answer reason=重复
python scripts/nf.py shell --form stats-write --yes              # 显式放行才真正执行
```

- **参数真源**：表单模板里的 `{key}` 由 step 填；模板只能指向**真实 CLI 动词**（check39 断言），空值连同其旗标一起丢弃（不留悬空 `--reason`）。
- **二次确认**：交互态 `yes/no`；非交互态必须显式 `--yes`（缺省只 dry-run）。
- **会话状态**：`--session <文件>` 持久化视图设置与上次分区（`/set` 后立即落盘）。守卫：路径须**绝对**且**不得落在仓库内**——仓库里留状态件会被 `git add -A` 吞掉（2026-09-26 实测过一次 tmp 文件事故）。

## 输出体验（列宽 / 限长 / 着色 / 分页）

- **列宽对齐**：CJK 与 emoji 按**显示宽度 2** 计算（`display_width` / `pad_to` / `clip`），两列列表在中文终端里不歪列；宽度取 `--width`，否则环境 `COLUMNS`，否则 100。
- **限长与提示**：`--limit N`（0 = 全部）作用于长列表，截断时明确给「… 还有 M 条（`--limit 0` 看全部，或加过滤词收敛）」，不静默截断。
- **着色克制**：`--color=auto|always|never`（缺省 auto）。auto **只在真 TTY 且未设 `NO_COLOR`** 时上色；`NO_COLOR` 一票否决 auto，而 `always` 是显式要求、不受其影响。会话内 `/set color=never` 可随时关。
- **确定性契约（硬）**：非 TTY（管道 / CI / 测试 / `--exec` / `--file`）一律**无色、无分页、逐字节可复现**——verify check39 直接断言默认输出不含控制字符。
- **分页可选**：`--pager=auto` 才会在真 TTY 且 `less` / `more` 在场时接管长输出；缺省 `never`（保证可重定向、可 diff）。

## 补全与历史（零依赖口径）

顶尖 CLI 的体感主要在两件事：**打一半能补**、**翻得回上一轮**。NF 把两者都做成**判据**而非平台特性：

- **补全**：`complete()` 是纯函数（任何平台都能用：`/complete <前缀>`、行尾 `Tab`、`nf shell --complete`），候选覆盖命令 / 二级子命令 / 旗标 / 斜杠命令 / 能力族；POSIX 上若 `readline` 可用则自动接管 Tab（`install_readline`），Windows 无该模块时走候选列表回退——`nf shell --verify` 如实报告当前走的是哪条路。
- **历史**：仅**交互态**写 `<NF_HOME>/shell_history`（`--history <文件>` 换路径、`--no-history` 关闭）；`quit` 与 Tab 行不入历史；`--exec` / `--file` **一律不写**——脚本面确定性是硬契约（单测直接断言 `run_lines` 无历史钩子）。

会话内**不执行**两类命令（避免卡死终端）：`serve`（长驻 MCP 服务）与 `shell`（递归会话）——
终端只给指引，请另开一个终端窗口运行。

## 写盘闸门

命中以下任一形态即视为写入/不可逆面，默认拒跑（退出码 2 + 修复指引）：

- 标记位：`--write` `--apply` `--register` `--tag` `--force` `--push` `--delete` `--rm`
- 动词：`register` / `import` / `rename` / `release` / `asset add|rm|deprecate` /
  `module deprecate|restore|signature`

放行方式只有两种：交互会话里就地回答 `yes`（只放行当次），或调用方显式 `--yes`。

## 非交互模式（CI / 脚本 / 回归）

```sh
python scripts/nf.py shell --exec "nf doctor" --no-banner
python scripts/nf.py shell --exec "/zone 5" --json --no-banner
python scripts/nf.py shell --file tour.nf                    # 脚本文件（# 注释 / 空行跳过 / 行内 ; 再分隔）
python scripts/nf.py shell --file tour.nf --json             # 同一执行链的机器面
```

- `--exec` 用 `;` 分隔（换行同样算分隔），`--file` 逐行执行；两者**共用同一条执行链**（同一 Session / 索引 / 写盘闸门），于是「终端里能敲的」与「脚本里能跑的」永远同一套语义。
- 逐条执行并逐条给 `kind/exit`；退出码 = 各条最大值。
- `--json` 输出 `{"kind": "nf-shell", …}` 逐条记录（含 argv / exit / out / err）机器面。
- `--no-banner` 去掉开场横幅（日志场景）。

## 边界

- **不是全屏 TUI**：NF 的交互面刻意保持「逐行读写」——可重定向、可 diff、可进 CI；
  全屏 TUI 会引入终端能力耦合与第三方依赖，与 core「零第三方依赖」红线冲突。
- **不是第二套命令面**：终端不复制业务逻辑，命令真源始终是 `scripts/nf.py` 的 argparse 面。
- **新 GUI/新壳**：不在本文件的范围内；按 `STRATEGY.md` §四与裁决记录，须由作者新裁决后另行立项。
