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
| `/help` 或 `/help <cmd>` | 转 CLI 帮助面（等价 `nf help …`） |
| `nf <args…>` 或 `<args…>` | 直通 CLI（`nf` 前缀可省） |
| `quit` `exit` `q` `退出` | 退出会话 |

健壮性（对标顶尖 CLI 终端的几件标配）：**Ctrl-C 只取消当前行、不杀会话**；行尾 `\` **续行**（多行命令）；行内 `#` 起注释（引号内的 `#` 保留）；命令写错时给**拼错建议**（编辑距离 ≤3），而不是把 60 条命令的 usage 甩一脸。

## 命令面检索（「最全功能」的可发现性）

终端的瓶颈从来不是命令少，而是**找不到**——CLI 有 64 个顶层命令、135 条含二级的入口。三条入口解决它：

```bash
python scripts/nf.py shell --commands            # 列出全部可达命令（顶层 + 二级）
python scripts/nf.py shell --commands asset      # 按子串过滤
python scripts/nf.py shell --search 装配         # 按关键词检索（未命中退出 2，可进脚本）
```

会话内等价形态是 `/commands [过滤]` 与 `/find <词>`。**索引由 CLI 的 argparse 面派生**（终端不维护第二份命令表），并由 verify check39 断言两件事：① 索引覆盖**全部**顶层命令；② 每个命令都能被检索到自身——「最全功能」因此是可机检事实，不是宣称。

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
