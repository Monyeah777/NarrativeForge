# NF 终端（`nf shell`）——端壳退役后的人机入口

> 最后更新：2026-10-03

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

三条启动路径的定位（**别混用**）：`scripts/nf`（POSIX）带**守护快路**，配合
`eval "$(nf daemon shell-init bash)"` 是毫秒级客户端；`scripts\nf.cmd` 同样带快路（比 POSIX 启动器慢）——
cmd.exe 没有内建套接字，故由 `scripts/nf_client.py`（**纯 stdlib**、`python -S` 起，不 import
仓库模块）代走一次套接字往返，拿不到守护就退回直跑（与 POSIX 启动器同一契约）；
`python scripts/nf.py` 是唯一真源入口，前两者都只是它的启动器。

进入后：输入 `0`–`8` 看能力区示例，`/menu` 重看菜单，`/help` 看用法，`quit` 退出。
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
| 8 | 写盘表单 | `/form <id>` 逐项追问（13 张表，见下文「写盘表单」）——本区**不留动作字面量**：动作由 `FORMS` 投影而来 |

菜单真源是 `desktop/src/core/terminal.py` 的 `ZONES`；**菜单只许指向真实命令**——
由 verify check39 与 `desktop/tests/test_terminal.py` 共用同一判据逐条断言
（`terminal.example_resolves`），新增能力须先落 CLI 再登记菜单。区的**动作**同样出自真源：
显式 `actions`，或（表单区）由 `terminal.zone_action_dicts()` 从 `FORMS` 投影。

## 交互语法

| 输入 | 行为 |
|---|---|
| `0`–`8` | 看该能力区的说明与可复制示例 |
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
python scripts/nf.py shell --map                 # 能力地图：按能力族分区，覆盖全部命令
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

### 顶尖 CLI 基线（逐条可核，不是形容词）

```bash
python scripts/nf.py shell --baseline          # 逐行跑证据命令并给判定（17 项）
python scripts/nf.py shell --baseline --json   # 机器面（纯 JSON：ok / stats / rows）
```

基线真源在 `desktop/src/core/terminal.py` 的 `TERMINAL_BASELINE`：每行 = 一项能力 + **一条证据命令**（+ 必须出现/必须不出现的片段 + 期望退出码，必要时 + stdin 输入 + **期待落盘的文件**）。当前 **20 行**覆盖（下表按主题归并——4 条写盘闸门行合成一项，逐行清单见 `terminal.py`）：命令面可达 / 关键词检索 / 能力地图 / 拼错建议 / **写盘闸门（该被拒）** / **递归长驻拦截（该被拒）** / 补全 / 限长提示 / 非 TTY 无色 / 脚本面 / **历史重放** / **历史落盘** / **会话持久化** / **菜单↔族互标** / 表单 dry-run / 纯 JSON 机器面 / 活体自检。

四条纪律：① 证据行**只读仓库**（带 `--write`/`--apply`/`--yes` 等旗标会被基线自身判违规）；② 允许声明「该被拒」（`expect_exit: 2` + 拒跑理由），安全面因此也在基线内；③ 交互态证据（历史/会话）用 `{TMP}` 占位展开到**系统临时目录**下的固定目录 `<临时目录>/nf_baseline`（仓库之外；固定名避免 `mkdtemp` 在本环境无法删除而堆积），并用「期待落盘文件」断言状态**真的写下去了**；④ verify check39 逐行断言同一份表——**「对标顶尖 CLI」的完成度可以逐条核**，不靠观感。

- **`--verify --deep`（活体档）**：在静态面（索引/策展/菜单）之上再核**本机环境与可执行性**——① 真跑一条只读命令（`nf layers --verify`）核对退出码；② **逐条**跑 `nf <cmd> --help`（当前 64 条，只读，约 11 秒）核对退出码——「最全功能」由此从「索引里查得到」升级为「命令真的跑得通」；③ 探测历史/会话落点**可写性**（沿祖先目录判断，**不落探针文件**）；④ 如实报告 TTY / readline / 分页器现状。所有结论与静态档同一套口径（`terminal.deep_check` 调 `self_check`），退出码即结论。
- **机器面（`--json`）**：`--commands --json`（逐条命令 + 摘要 + 旗标）、`--map --json`（族分区）、`--form --json`（表单真源）/ `--form <id> --json`（组装计划 argv）、`--verify [--deep] --json`（ok / issues / stats）。**输出必须是纯 JSON**——活体输出会被捕获进字段而不是混进 stdout，check39 直接断言这一点。

- **面判别键（全命令口径 · 2026-10-01 收口）**：任何声明了 `--json` 的面，成功输出一律是
  **对象**且顶层带面判别键 `kind`（协议件面用 `schema`）；失败一律
  `{"ok": false, "error": … , "exit": N}`。此前新旧两套信封并存（实跑 64 个可无参运行的
  `--json` 面：17 带键 / 47 不带，其中 7 个还是裸数组——成功回数组、失败回对象，
  消费方**无法区分**），本轮统一。**唯一豁免是 `nf interop`**：它导出的是第三方标准文档
  （OpenAPI / AsyncAPI / SPDX / CycloneDX / in-toto / VC / C2PA / CID），**不得**加 NF
  私键（加了会被官方 meta-schema 判越界，AUD-0010 实测），改由规范自身版本键自证。
  判据：`desktop/tests/test_cli_json_face.py`（静态字典面 + 动态真跑 + 豁免面逐一点名）。

- **成功面不得回吐本机绝对路径（2026-10-01 收口）**：同一条纪律此前只写在失败消息
  （`_no_machine_paths`）、入仓文件（`conformance_report._c_public_surface`）与
  `test_leak_surface` 上；实测 `nf doctor --json` / `nf toolface --json` /
  `nf daemon status --json` 三处**成功面**仍把 `C:\\Users\\<用户名>\\…` 原样写出。现改为
  **仓库相对**（doctor 明细、toolface 的 `source`）或**可移植写法**（daemon 的 `root` /
  `state_file` → `~/…`，见 `_portable_path`）。判据并入 `test_cli_json_face`（机器面 + 人读面
  各扫一遍本机路径形状）。

## 单真值源 · 多视图（投影面）

终端面只有**一份真值**：`desktop/src/core/terminal.py` 的策展表（`ZONES` 能力区 + 动作目录 /
`FAMILIES` 能力族 / `FORMS` 写盘表单 / 写盘闸门三表 / `BLOCKED_IN_SHELL`），加上
`scripts/nf.py` 的 argparse 面（命令的**存在性**）。其余一切都是它的**投影**：

| 视图 | 呈现什么 | 入口 |
|---|---|---|
| 行模式终端 | 菜单示例 / 能力族地图 / 写盘表单逐项追问 | `nf shell`（本文件上文各节） |
| 全屏 TUI | 动作目录（含**写盘表单区**：13 张表各是一个可回车动作） | `python tui/nf.py` |
| 机器面 | 整面快照（JSON） | `nf shell --surface --json` |
| 生成件 | 全屏视图的离线输入（零 core 依赖） | `tui/_surface.py` |

```bash
python scripts/nf.py shell --surface            # 人读面：逐区列动作与闸门计数
python scripts/nf.py shell --surface --json     # 机器面：kind=nf-terminal-surface
python scripts/nf.py shell --surface-write      # 重生成 tui/_surface.py（真源改动后必跑）
```

三条纪律：

1. **视图不许留第二份表**。全屏 TUI 冻结成单文件 exe、不能 import core，于是曾经手抄命令
   白名单 / 闸门表 / 动作目录——手抄的闸门表漏了「命令 + 旗标才写盘」的配对表
   （`terminal.CONFIRM_FLAG_PAIRS`），`nf interop --all` 这类写面在全屏视图里**不确认即可执行**。
   现在 TUI 只 `import _surface`（生成件），口径由真源唯一持有；视图可以**显式**额外收紧
   （例：TUI 把 `daemon` 整族列为拒跑，理由写在 `TUI_EXTRA_LONG_RUNNING`，属视图策略而非分叉）。
2. **投影必须可对账**。`tui/_surface.py` 是**生成件**（件内抬头写明真源与重生命令）。真源改了
   没重生成 ⇒ `nf shell --verify` 与 verify check39 都会红：重算投影后与在场件**逐字节**比对，
   报出首个不一致行并给重生成命令。
3. **视图口径只许更严，不许更松**。check39 逐条比对：全屏视图的写盘旗标 / 写盘动词 /
   命令 + 旗标配对必须**覆盖**真源三表；命令白名单必须与 argparse 面一致；动作 `argv[0]` 必须是
   真实命令；能力区数必须与真源一致。视图侧的写面同样受闸门约束：表单物化出的动作必须被判为
   `write`（单测逐条枚举），空的可选参数与其旗标一起丢弃（与 `terminal.build_argv` 同口径，
   免得留下悬空 `--reason`）。

判据落点：`verify.sh` check39（投影逐字节 + 视图不弱于真源）、
`desktop/tests/test_terminal.py`（`TerminalSurfaceTest`）、
`desktop/tests/test_nf_tui.py`（`SurfaceSingleSourceTest`）、
`python tui/nf.py --selftest`（「闸门口径（单源）」「投影同源」两行）。

## 写盘表单与会话状态（会改仓库的动作由人安全驱动）

`nf` 的写盘命令都要参数齐 + `--yes`，对人是负担。终端把它拆成**逐项追问**：`/form <id>` 开始，一次问一项（可选项**空行跳过**），填齐后打印**组装好的命令**再问 `yes/no`，确认后才执行——而且最终仍走同一条**写盘闸门**（终端不绕过它）。当前 **13 张表**覆盖常用写盘点：`deprecate-module` / `restore-module` / `types-write` / `stats-write` / `asset-add` / `register-apply` / `rename-apply` / `receipts-write` / `preset-save` / `library-deprecate` / `library-restore` / `pipeline-new` / `approve-subject`。**其余写面逐条登记在 `terminal.FORM_EXEMPT`**（写明为什么不为它建表），判据保证「闸门表里的每个写面要么有表、要么有理由」——新写面入闸却没人想起配表即红。

这 13 张表**同时是全屏视图的动作**：`ZONES` 的第 8 区（`id=forms`）标 `forms: True`，动作由
`terminal.zone_action_dicts()` 从 `FORMS` 投影而来——于是「表单真源只有一份」（改表即改两个视图，
不存在第二次登记）。表单步骤里带 `kind: "path"` 的参数在全屏视图里会成为**路径参数**：过仓库
包含性判据后才拼进 argv。

非交互也能用（dry-run 优先）：

```bash
python scripts/nf.py shell --form                                # 列全部表单
python scripts/nf.py shell --form stats-write                    # 只组装 + 打印（dry-run）
python scripts/nf.py shell --form deprecate-module --answer file=community/x/M1.md --answer reason=重复
python scripts/nf.py shell --form stats-write --yes              # 显式放行才真正执行
```

- **参数真源**：表单模板里的 `{key}` 由 step 填；模板只能指向**真实 CLI 动词**（check39 断言），空值连同其旗标一起丢弃（不留悬空 `--reason`）。**布尔旗标**用「单占位」表达：把 `{key}` 单独放一格，填 `--force` 就带上、留空即丢（见 `preset-save`）。
- **二次确认**：交互态 `yes/no`；非交互态必须显式 `--yes`（缺省只 dry-run）。
- **会话状态**：`--session <文件>` 持久化视图设置与上次分区（`/set` 后立即落盘）。守卫：路径须**绝对**且**不得落在仓库内**——仓库里留状态件会被 `git add -A` 吞掉（2026-09-26 实测过一次 tmp 文件事故）。

## 效率（把「快」也变成判据）

终端的两类效率各自有判据：

**① 进程内开销（机制成本）**

- **命令面只构建一次**：argparse 面构建实测 **96–118 ms/次**，而一次终端命令过去要建 3 次以上（索引 + 命令树 + 真正解析），`--verify --deep` 的全命令扫描更是 **64 次**。现在 `_build_parser()` / `_collect_cli_tree()` / `_shell_command_index()` 全部进程内缓存。
- **`--version` 短路**：最常被调用的探测命令不再构建命令面（输出与 argparse 的 version 动作逐字一致）。
- **宽度查询缓存**：`char_width()` 带 `lru_cache(4096)`——列表渲染是逐字符问宽度的热路径。
- **抽象阶梯真源面展开（v13）**：`nf layers --verify` 是唯一仍有 ~1 s 固定成本的只读命令，成本几乎全在 glob 展开——`_rule_issues` 的 L1/L2/L3 会把同一批 43 个 pattern 反复展开（约 10.5k 次 `stat`），L6 还会对 core 全量 `ast.parse`。现在：每次扫描内按 pattern 缓存、每棵子树只 `os.walk` 一次 + glob→正则匹配（字符类等专有语义回退参考实现）、L6 先文本预筛再解析 AST。快路径与参考实现**逐 pattern 等价**（真源 43 个 pattern + 字符类 / `?` / `**` / 固定件 / 空子树 5 类形态，0 处不一致），四阶面规模不变（契约 52 / 资产 2218 / 引擎 256 / 出口 26）。
- **核心扫描去重（v14）**：终端之外的只读命令也按同一纪律收——`nf conformance` 过去把十八项契约**跑两遍**（先比对再打印），现在只跑一遍；`nf doctor` 里 248 份模块文档的机器契约块被解析 **496 次**（占体检 74%），改为按**文本本身**缓存解析（文本变则键变，无陈旧风险）；管线 dry-run 的 `sweep()` 给 228 条管线各建一次全仓模块索引（≈5.6 万次读盘），改为一次只建一次；纯度扫描的同一棵树被 walk 四遍，改为**一次 parse + 一次 walk** 取齐四类事实；广度证明每次组合取缓存键都走了一次 `Path.resolve()`（Windows 系统调用），改用 `os.path.abspath`——**6888 次组合因此省下 3.8 s**。等价性用参考实现逐条比对守住（纯度 issues/stats 全等、广度组合数与合法性全等）。
- **同文重算改按内容键缓存（v15）**：资产引用度普查（1499 键 × 3.5 MB 逐键精确计数 ≈ 2.9 s）按**语料与键集的 sha256** 缓存——键取内容而非路径，内容一改键就变，故无陈旧风险；同一进程内第二次普查 2.94 s → 0.88 s。另修两处纯重复 IO：`conformance_scan` 曾在**每个社区包**循环里重读 registry.json（112 次），`asset_density._keys_of` 曾把调用方刚读过的正文再读一遍。**两条「加速」被实测否决**：`bytes.count` 更慢（UTF-8 稀释），单遍 alternation 在键于同一位置重叠时会漏计（会让「零引用键」出假零）——精确语义优先。
- **统一 YAML 加载器改用 libyaml（v16）**：归因发现剩下的 YAML 成本**不是重复解析而是解析器慢**（`schema_lint` 的 473 次解析零重复、`concept_graph` 的 102 份概念图是真实解析）。`CSafeLoader` 实测比 `SafeLoader` **7.8× 快**；新增共享入口 `conformance_scan.load_yaml()`（libyaml 优先、缺则回退纯 Python），四处热点解析点并入。等价性**逐块实证**：本仓 1395 个 YAML 文本块（584 份文件）两种加载器结果与异常行为**全等**（已固化为回归断言）。首版用 `yaml.load(...)` 被自家纯度判据 R6 判为 CWE-502 危险 sink——改为直接实例化安全加载器（与 `yaml.safe_load` 同语义），不把禁用面叫回来。

实测（本机，单跑）：

| 场景 | 前 | 后 |
|---|---|---|
| `nf shell --verify --deep`（64 次 `--help` + 一次 `layers --verify`） | ~11.3 s | **~1.9 s** |
| `nf shell --baseline`（17 行逐条） | 数秒级（受重建拖累） | **1.95 s**（16 行 ≤ 4.3 ms） |
| `nf shell --commands`（冷启动） | 363 ms | **281 ms** |
| `nf --version`（冷启动） | 223 ms | **242 ms**（其中解释器 ~60 ms、文件执行/AV ~100 ms、导入 ~20 ms） |
| `nf layers --verify`（抽象阶梯全仓扫描） | ~1.18 s | **~0.5 s**（`layer_model.scan` 801 ms → 281 ms） |
| `nf conformance`（十八项契约 + 在盘比对） | ~40 s | **~5.1 s** |
| `nf doctor`（环境体检） | ~1.0 s | **~0.94 s**（进程内 1.97 s → 0.69 s） |
| `nf score`（四路信号 + 纵深扫描） | 17.1 s | **13.3 s**（广度证明 4.86 s → 0.30 s） |
| `nf shell --baseline`（进程内，17 行） | 1.95 s | **0.38 s** |
| `nf score`（v15 后） | 13.3 s | **12.6 s**（普查同内容不重算） |
| 整套单测（1241 例，`verify` check12 的主要成本） | 253.3 s | **206.8 s** |
| 300 件馆藏的规模回归用例（`library.search` 的 O(n²)） | 25.4 s | **1.07 s** |
| `nf conformance`（v16 后，统一 YAML 加载器） | 5.1 s | **3.1 s** |
| `nf score`（v16 后） | 12.6 s | **9.3 s** |
| 整套单测（v16 后） | 206.8 s | **187.3 s** |

**② 延迟预算（基线行自带 `max_ms`）**

`nf shell --baseline` 现在会为**每一行证据计时**并与人读输出并列（`✔ … 1.7 ms nf shell --commands …`）：轻行默认预算 **300 ms**（实测 ~1–2 ms，留 100× 余量，仍能拦住「解析器缓存失效→涨到 ~300 ms 量级」这类回归），`--verify --deep` 行单独给 **6000 ms**（2026-09-29 **实测重标**：该行主成本是**全仓抽象阶梯扫描** `nf layers --verify`——空闲 ~0.5–1.7 s、本机满载 2.4–3.7 s；旧标定「进程内 ~320 ms、留 6× 余量」的前提已不成立，2000 ms 只剩 1.15× 余量，同一棵树实测一次绿一次红。6000 ms ≈ 3.5× 空闲余量，仍能拦住「全命令扫描涨回 ~11 s」这类数量级回归），且**超预算的行再测两次取最小样本**（min of N 是本仓一贯的性能口径——预算量的是机制开销，不是这台机器当时的心情）。超预算即判该行不过 → check39 红 → 推不上去。

**③ 少敲键（用户效率）**

- **唯一前缀补全**：输入 `scor` 会自动补成 `score`（只在**恰好一个候选**时生效并显式标注；歧义时仍走拼错建议、不猜着执行——例如 `stat` 同时命中 stats 与 state-front 两个候选）。
- 配合已有的补全（Tab/`/complete`）、历史重放（`!!`/`!n`/`!前缀`）、能力地图与检索，常用动作的按键数都在个位数。

**④ 读取形状（把「不重复读」变成判据）**

墙钟断言在 CI / 并发机上会抖，但「同一份件在一次扫描里被读几次」是**确定性**的——于是把本轮修掉的缺陷类钉成读次数判据：`library.search` 在 300 件馆藏下**单件 ≤ 2 次、总读次数随件数线性**（另有变异样本证明该界限能抓住旧实现的 O(n²) 形状）；一次纵深扫描**单件最大 ≤ 14 次**（实测均值 3.5、单件最大 9）。同类回归（对每条目/每条结果重跑一次全量读取）会立刻红，而不是「只是变慢」。

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

会话内**不执行**三类命令（避免卡死终端）：`serve`（长驻 MCP 服务）、`lsp`（常驻 stdio
服务，等编辑器发 Content-Length 帧——与 `serve` 同型，2026-10-01 补齐）与 `shell`
（递归会话，`nf terminal` 是它的别名、同拦）——终端只给指引，请另开终端或由 IDE 拉起。

## 写盘闸门

**真源 = `desktop/src/core/terminal.py` 的三张表**（`CONFIRM_FLAGS` / `CONFIRM_VERBS` /
`CONFIRM_FLAG_PAIRS`）；本页只写口径与**节选**清单，且判据会核对本页出现的每一项都真在表里
（防文档飘）。命中以下任一形态即视为写入/不可逆面，默认拒跑（退出码 2 + 修复指引）：

- 标记位：`--write` `--apply` `--register` `--force`
  `--out` `--dest` `--build`，以及**名字里没有 `--write` 但同样写盘**的：`--write-baseline`
  （`nf score` 重签回归基线；`nf asset baseline` 的重签用的是 `--write`）、`--fix`
  （`nf lint` 机械修复就地改源件）、`--harvest`（`nf module types` 写事件载荷注册表）、
  `--write-advisory`（`nf pipeline dryrun` 写管线 advisory 台账）、`--certify`
  （`nf combine plan` 写组合证书）、`--save`（`nf assemble` 写**你自己命名**的档案文件，
  可给仓库相对路径 ⇒ 与 `--out` 同类）、`--surface-write`（`nf shell` **自身**的生成器旗标：
  把终端面真源投影成 `tui/_surface.py`；只从 CLI 顶层可达——`shell` 在会话内被拒跑）
- 动词（**不带任何旗标也直接改仓库件**）：`register` / `import` / `rename` / `release` /
  `approve`（落 `protocol/approvals/*.json`）/ `asset add|rm|deprecate|restore` /
  `module deprecate|restore|signature` / `pipeline new` / `decisions reindex` /
  `patterns reindex` / `knowledge transform`（写 `protocol/transform_log.json`）/
  `library reindex|deprecate|restore|supersede|attest`
- 命令+旗标配对：`interop --all`（落盘 `results/interop/*`；同名的 `interop --check` 只读，
  不拦——`pipeline dryrun --all` 同理）；`--trace` / `--session` **只在 `nf assemble` 上算写**
  （写你命名的文件）——`nf knowledge frequency --trace` 是**读**、`nf shell --session` 另有
  「必须绝对路径且不得落仓库内」的硬闸，两条都不拦

放行方式只有两种：交互会话里就地回答 `yes`（只放行当次），或调用方显式 `--yes`。

**闸门守的是哪条面（口径）**：只守**文本驱动**的面——交互输入、`nf shell --exec`、
`nf shell --file`（这三条都可能承载**粘贴/注入**进来的文本，机器不替人判断「这行该不该跑」）。
**显式 argv** 的面不设这道闸：`nf <cmd> …` 直跑与 `nf daemon exec <argv>` 等价于操作者自己敲的
命令（后者文档即写明「输出/退出码与直跑一致」）。实测对照：`nf shell --exec "nf stats --write"`
→ exit 2（拒），加 `--yes` 即放行；`nf daemon exec stats --write` → 照跑。

## 非交互模式（CI / 脚本 / 回归）

## 执行层常驻（`nf daemon`）——毫秒级响应

`nf <命令>` 每次都要起一个解释器。本机实测（2026-09-29，min of N）**裸解释器 47 ms**、
`nf --version` **215 ms** —— 固定成本 ≈ 解释器启动 + 导入（~10 ms）+ **argparse 命令面构建
（实测 117 ms，65 条子命令）**。`nf daemon` 把执行搬进常驻进程，客户端只做一次套接字往返
（热进程内 `--version` **1.5 ms**；用 bash 内建 `$EPOCHREALTIME` 计量，零 fork、无 `date` 偏差）。

| 路径 | `--version` | `stats --check` | `doctor` |
|---|---|---|---|
| python 直跑（原路径，每条一次解释器） | 215 ms | 288 ms | 634 ms |
| `scripts/nf` 启动器（**无守护**：回退 python 直跑） | 296 ms | 365 ms | 713 ms |
| `scripts/nf` 启动器（经守护） | 48 ms | 48 ms | 48 ms |
| **bash 函数（零子进程，经守护）** | **1.5 ms** | **1.6 ms** | **1.6 ms** |

启动器本身现在只剩 **bash 启动地板（本机 ~39 ms）+ 一次套接字往返**。修前它比「同一条命令
python 直跑」还慢 **164 ms**——三笔固定成本都是按**每条命令**计的：外部 `dirname` + 子 shell
≈58 ms、一次命令替换（Store 桩路径判据）≈30 ms、「真起一次解释器」的终判 ≈60 ms（真撞上
Microsoft Store 别名桩要 ~300 ms）。三笔分别改成参数展开、按平台择一（Windows 先要 `python`）、
终判按「解释器名 + 平台」**缓存**后：启动器经守护 **175 ms → 48 ms**、无守护 **428 ms → 296 ms**。
判据是**解释器启动次数**（PATH 上挂 shim：先记一笔再转发真解释器，与机器快慢无关）——
快路命中 **0 次**、回退**稳态恰好 1 次**（修前每条 2 次）、`python3` 是桩时必须换成能跑的那个
（`test_launcher.InterpreterLaunchBudgetTest`）。

> **2026-10-02 同口径复测（min of 5，同一手法）**：bash 地板 **40.8 ms**、`scripts/nf --version`
> 经守护 **71.9 ms**（一次解释器都不起）、无守护 **260.9 ms**（恰好 1 次）、
> `python scripts/nf.py --version` **189.3 ms**。即上表「经守护 48 ms」的分项如今是
> **地板 41 ms + 套接字往返 ≈31 ms**（当初往返 ≈9 ms），组合式（地板 + 一次往返）没变；
> 「无守护 296 ms」与今日 261 ms 同量级。
> 口径提醒：本节数字是**带日期的实测记录**，不是承诺——**机制面**（快路起几次解释器、回退稳态
> 几次）由 `test_launcher.InterpreterLaunchBudgetTest` 确定性守着，**墙钟数字**随机器与负载漂，
> 复测请沿用「同轮同时量墙钟 + 启动次数」的手法（第一版只量墙钟、不与启动次数同轮比对，
> 曾把无守护路径读成与快路同速）。

常驻对**重命令**同样有效（内容键缓存跨请求保留；实测本机，min of N）：

| 命令 | 冷启动直跑 | 守护稳态 |
|---|---|---|
| `nf score` | 7.5–8.4 s | **~3.5 s**（派生结果按内容键缓存后） |
| `nf doctor` | 697 ms | **212–385 ms**（同机抖动范围内） |
| `nf conformance` | 3.07 s | **2.19 s** |

判据面（都落在 check12，机器无关）：AST 事实**内容键**语义（同文命中 / 改文重算）、改文后下一次扫描必须看到新结果、常驻复用（**数 `ast.parse`**：第二次只允许 L6 预筛的极少数且少一个数量级）、**启动器快路快过 python 直跑（POSIX 上 3×）**。

命令面延迟全景（24 条代表命令；冷启 = 新进程直跑，守护 = 常驻热跑；本机实测）：

| 命令 | 冷启 | 守护 |
|---|---|---|
| `nf score` | 7729 ms | **3624 ms** |
| `nf conformance` | 3202 ms | **2403 ms** |
| `nf layers --verify` / `nf doctor` / `nf pipeline dryrun --all` | 550 / 716 / 555 ms | **304 / 227 / 204 ms** |
| `nf interop --check` · `nf toolface` · `nf module ls` · `nf worldmodel` · `nf stats --check` | 384 / 407 / 305 / 400 / 315 ms | **135 / 132 / 131 / 100 / 89 ms** |
| 其余 14 条（audit / decisions / receipts / sig / patterns / library / cognition / state-front / knowledge / market / output / assertions / approve / domain） | 225–313 ms | **2–41 ms** |

即：**除两条「全仓工具」外，命令面全部进入毫秒/百毫秒级**；24 条的退出码与直跑逐一相同。这条全景也有判据守着——11 条轻命令的**打开文件数 ≤ 60**（实测 0–36，全仓约 2354 个文件），谁把全仓扫描塞进轻命令，check12 当场红。

**重命令的成本结构**（热跑 `regression_score.evaluate`）：**读+开文件 ≈25%**、**元数据（stat/scandir 等）≈35%**、**计算 ≈40%**。跨调用**内容键**缓存（围栏 YAML / 引用度普查 / 派生结果）与**一次只读调用内共享语料**（读缓存 + 目录遍历/子树清单缓存，均为出口即清）把这份账压到实测 **~2.0 s**（打开 2461 次、不同件 2456——语料在一次只读调用内基本只读一遍）。

### 不重算：目录监听 + 响应缓存（`nf daemon start --watch`，可选）

「用 mtime/size 推断变没变」那条路被显式否决（指纹没变 ≠ 文件没变；Windows 时间戳粒度 ~15.6 ms）。本波换一条**不问「像不像变了」、只问「有没有变」**的路子：守护装一个目录监听（Windows：`ReadDirectoryChangesW`，递归子树），维护**树代际**；只读命令的**整条响应**按 `(argv, cwd)` 缓存，**代际没变才复用**。

| 路径 | `nf score` |
|---|---|
| 冷启动直跑 | 7.7 s |
| 守护稳态（每次真重算） | ~2.2 s |
| **守护 + `--watch`（树没变 → 整条复用）** | **~0.18 s**（差额是 `bash scripts/nf` 的进程启动） |
| 同上，配零子进程客户端 | **5 ms/次**（3 轮 ×20 采样；协议往返，无子进程） |

实测（本机）：同一棵树连跑两次 `nf score` → **6816 ms / 176 ms**；在仓库里增删一个临时文件后 → **2087 ms（重算）**，再跑一次 → **177 ms**。

纪律（fail-closed，均有判据）：

- **只把「收到变更通知」当「变了」**：监听不可用 / 句柄失效 / 线程异常 → 缓存整体停用（不命中、旧条目一并作废），行为与常规守护完全一致；缓冲溢出如实报 `overflowed` 并让代际跳变（宁可全废，不可错答）。
- **守护自己执行过「非准入」命令 ⇒ 立刻作废整批缓存**，**不等监听线程异步察觉**：作废原本只靠监听的几毫秒窗口，而脚本里 `nf conformance --write; nf score` 这种连跑就可能落在窗口里吃到写之前的旧响应（有确定性判据守着，不靠计时）。**残留窗口如实记**：外部进程改了仓库、而请求恰好在监听察觉前几毫秒到达时，仍可能命中旧响应——这是通知制缓存的固有窗口；守护侧写入已由上面那条变成**确定性**作废。
- **两道 fail-closed 闸门（打开句柄成功 ≠ 通知会到）**：① **卷类型**——只在本机固定盘启用（网络盘 SMB/UNC 的通知语义不可靠、会静默漏事件 → 代际永不推进＝永久回放旧结果）；② **机制自检**——启动时在一个**临时目录**里真跑一遍「创建 / 改 / 删除」，三类通知都到才算可用。任一条不过就判「监听不可用」、缓存整体停用。代价实测只有 ~70–90 ms（`nf daemon start --watch` 565 → ~650 ms，一次性）。
- **`.git/` 下的变更不作废响应缓存**：日常 `git status/add/commit` 都会写 `.git/`，若照旧作废，每跑一次 git 命令，下一个 `nf score` 就要退回 ~2.2 s 重算（实测：修前 `.git` 探针后平均 **151 ms**，修后 **10 ms**）。安全前提是**有判据的事实**——追踪一次 `evaluate` 的全部打开与尝试打开，含 `.git/` 的路径必须为 **0 件**（实测仓内 2560 件、`.git` 下 0 件），且被缓存的只读命令都不调用 git。混批、解析不出路径、缓冲溢出**一律照旧转脏**（只忽略「这一批全部落在忽略面内」的情形）。
- **准入表按 argv 前缀**（不是顶层命令名）：只有**纯读、且对同一棵树逐字节可复现**的形态可缓存——`--version` / `score` / `conformance` / `layers` / `stats` / `doctor` / `interop` / `toolface` / `assertions` / `cognition`，以及 `patterns ls|show|for|verify` / `module ls|status|verify` / `decisions verify|show`。带 `--write` 一类写盘开关的一律绕过。
  「按前缀」是必须的：`module` / `decisions` / `patterns` 这些顶层命令**同时有读写子命令**（`module deprecate`、`decisions reindex`、`patterns reindex`），只按顶层名放行会把写形态一起放进来。两条准入判据都可执行：① 同树连跑两次，退出码 / stdout / stderr 逐字节相同；② 逐条跑完 `git status` 前后不变（候选 12 条实测全部既纯净又可复现）。
- **本波只实现 Windows 监听**：其他平台 `watch.available()` 为假，守护自动降级——不写没跑过的平台代码。
- **自动拉起（默认开 · 非阻塞；`NF_AUTOSTART=0` 可关）**：守护不在时，启动器把带 `--watch` 的守护**丢到后台**拉起，**本条命令照常走 python 直跑、不等它**（`daemon` / `shell` / `terminal` / `serve` / `lsp` 本就不走守护，不触发）。**为什么默认开**：起守护要 ~0.65 s，但后台起**不占本条命令的时间**（首条只多一次 fork ≈10 ms），而**从第二条起命令落到守护快路**。实测（本机，各 7 连发取中位；**数字随机器变，只作量级参照**）：`python scripts/nf.py stats --json` **≈223 ms**（每条冷起解释器）· `bash scripts/nf stats --json` **≈123 ms** · `scripts/nf.cmd stats --json` **≈194 ms**（2026-10-01 起经 `scripts/nf_client.py` 走快路；**此前 ≈391 ms**）。`.cmd` 这一档仍**比 POSIX 启动器慢**（多一层 cmd.exe 外壳，且比它自己的客户端 `python -S scripts/nf_client.py` ≈155 ms 又多 ≈40 ms）——毫秒级那一档是 POSIX 启动器 `scripts/nf` 配 `eval "$(nf daemon shell-init bash)"`。默认路径因此对「agent 密集重复调用」是毫秒级；若你只跑一次性命令、不想让守护常驻，`NF_AUTOSTART=0` 关掉即可（`nf daemon exec` 是同类语义：那条默认拉起，且可 `--no-start` 拒绝）。

### 不重读：常驻语料 + 目录索引（按监听变更**精确**失效）

响应缓存只管「树没变」那一档；**改了一个文件之后**呢？实测（本机，min of N）：改完立刻跑
`nf score`，守护里的**第一条**要 **1.6–2.0 s**——因为那些共享语料缓存的作用域边界是「一次调用」，
下一个请求得把整棵语料**重新枚举**（1484 个目录 / ~2000 次 `scandir`）并**重读**（~2500 次 open），
而其中真正变了的往往只有一件。

本波加一层**常驻层**（`conformance_scan._RESIDENT`：正文 + 目录条目），只在守护带**健康监听**时
安装，只收录**监听根之下**的件，并**只按监听给出的确知路径**失效：正文按件删、目录条目按父目录删
（增删都会改父目录清单）。**说不清就整批作废**（缓冲溢出 / 路径解不出 / 只跳代际没给路径）。

| 场景（守护热跑，改完立刻的第一条 `nf score`） | 常驻层关 | 常驻层开 |
|---|---|---|
| 改 `CHANGELOG.md` 这类**不在任何输入面**的件 | 1591 ms | **872 ms** |
| 往 `04_模块库/通用类/` 放一件（**落在输入面里**） | 1625 ms | **951 ms** |

（同机各 3 轮中位；开关是 `NF_NO_RESIDENT=1`，可随时退回旧行为对照。）

为什么它**不比响应缓存多信任任何东西**：响应缓存本来就靠同一条「代际没变 ⇒ 树没变」的判据，
而那条判据又由卷类型闸门 + 机制自检 + 溢出上报守着。常驻层只是把同一条信任用在更多数据上，
且**没有新的失效路径**——监听说不清时它整批作废，比响应缓存（还留着旧响应但代际会跳）更保守。
判据（确定性，不看墙钟）：变更面报得出路径且拒绝装懂（`DirWatcherTest`）、层只收录根下的件、
给了确知路径就必须立刻失效、说不清必须整批归零、守护确实装上并在 `_bump()` 后归零
（`ResidentLayerTest` + `WatchDaemonIntegrationTest`）。

再往下一层是**派生结果**：扫描器的结果都是「输入内容的纯函数」，于是按**输入面内容指纹**缓存
（进程内 + 落盘两层；键里另含代码面与运行时）。两条纪律决定形状：

- **窄面在任何进程都缓存**（资产密度两函数、台账投影）——见证只要几十毫秒，值得。
- **宽面只在常驻层在位时缓存**（`schema_lint` / 阶梯 / 纯度：声明面覆盖整棵语料）——冷进程里
  宽面指纹要把语料重读一遍（实测 ~1.0 s），比直接算更贵，故**宁可不算**（`require_resident`）。

而「见证」本身也被压到近乎为零：**逐件摘要随正文一起常驻**，按监听变更**逐件**失效。实测 8 个
输入面（含 3439 件的宽面）的见证成本 **228 → ~30 ms**，且**指纹值逐位不变**（同一件同一 payload
⇒ 同一摘要）。端到端（本机，3 轮独立取中位、每轮新起守护）：

| 改完立刻的第一条 `nf score` | 修前 | 修后 |
|---|---|---|
| 无关变更（改不在任何输入面里的件） | 1591 ms | **545 ms** |
| 相关变更（改输入面里的件，**唯一新内容状态**，端到端） | 1625 ms（Aho 之前 4.6–6.3 s） | **≈1.25 s**（同一状态再来一次 ~52 ms） |
| 树没变（整条复用） | — | **51 ms** |

**「新内容状态」这四个字很重要**：同一个内容状态跑第二遍会命中盘上条目（~50 ms），而**每次真编辑
都是一个新状态**。把这个区分量清楚才看出真正的元凶——引用度普查用逐键 `str.count` 数 1499 个键 ×
3.5 MB 语料 = **5.2 GB 字符扫描 = 3.11 s**，每个新状态都要重付。现在换成 **Aho–Corasick**
（一遍扫语料 + 按键盘非重叠贪心计数，与 `str.count` **逐字节同语义**）：真语料上 **2895 → 323 ms**
（合计引用 31323 逐键一致），`usage_scan` 整体 ~3.1 s → **296 ms**，等价性由 400 例随机串 +
重叠/嵌套/空键边界 + 真语料子集三条判据守着。

再进一步（2026-09-29）：普查改成**逐件计数再相加**、并按**文件内容**缓存逐件结果——等价性可证
（asset id 不含换行 ⇒ 跨件匹配不存在），于是**一次真编辑只让被改的那一件重算**：`usage_scan`
逐件缓存热时 **296 → 28 ms**，端到端「真编辑后的第一条重命令」**1.95 s → 0.35 s**
（同一状态再来一次仍 ~50 ms，冷进程 ~1.87 s 不变）。

**口径纪律（踩过三次，写死在这里）**：凡称「新内容状态」，探针必须写**一次性唯一正文**
（时间戳 + 计数器），否则从第二遍起命中的是盘上**同一内容状态**的派生，量到的是「同内容重放」
而不是新状态。按这条纪律重测：**唯一新状态 · 守护第一条 ≈ 1.25 s**、同状态再来 ~52 ms、
树没变 ~50 ms、冷进程 ~1.9 s。

**共享读现在是「一次物理读服务两种口径」**：底层只读**原始字节**并收进常驻层，文本由
`TextIOWrapper(BytesIO(raw), encoding="utf-8", newline=None)` 解出（与 `Path.read_text` 的
通用换行语义**逐字节一致**，判据 `ResidentRawEquivalenceTest` 对真语料逐件比对）。于是「同一份件
既当文本读、又当字节读」（`ET.parse`、`_recompute_entry` 的字节比对等）不再读第二遍——一次
「新内容状态」重算的真读盘从 **1047 次降到 38 次**（不同件 1039 → 33）。

纵深汇总（`quality_depth_scan`，check32 门面）自己**把十几个子扫描器挨个跑一遍**，所以它也接了
内容键缓存（输入面 = 各子扫描器面的并集）——它是剩下那笔账的最大一处，接上之后**进程内
`evaluate` 476 → 43 ms**。与此同时把「查表」本身也压便宜：路径键（`normcase(abspath())`）带记忆
（实测一次 `evaluate` 里它被调 17628 次、单独吃掉 71 ms）。

**代码面（谁真的依赖谁的代码）也是内容键的一部分**，而整块代码面（119 件）意味着「改任何一件
core 文件 ⇒ 所有派生换键」。现在按**导入闭包**细化：每个派生只把「自己静态 import 到的那些
`core.*` 模块」（传递闭包）进键。三条 fail-closed：解析不出 / 闭包里出现动态导入构造
（`__import__` / `importlib`）/ 闭包为空 ⇒ 一律**退回整块代码面**；另有一条**运行期完整性判据**
——在全新解释器里真跑一遍该派生，期间 import 的 `core.*` 必须都在闭包内（静态分析漏判会当场红）。
确定性证据：改 `desktop/src/core/terminal.py` 之后，换键的站点数从 **9/9** 降到 **0/9**。

守护侧还有一处「自废武功」也修了：判「代码换版」时会把 `core.*` 整块摘掉重载（保证不跑旧代码）,
于是新模块的常驻语料层是空的——现在换版前取走、换版后装回（层里是仓库事实，与代码无关）。
端到端：**改一行代码后的第一条重命令 2609 → 870 ms**（再改一次 440 ms）。

**两条要记住的边界**：① 冷进程（无守护）**不**走宽面缓存——`nf score` ~1.9 s、
`nf conformance` ~2.3 s，与接入前一致（不拿读数换速度）；② 把代码当**数据**审计的那几个派生
（纯度 / 阶梯 / 纵深汇总）在代码变化后**必须**重算——那是真依赖，不是浪费。

**边界（必须知道）**：改任何一个 `desktop/src`/`scripts` 下的文件 ⇒ 代码面进键 ⇒ 所有落盘派生
条目一次性换键，**下一条重命令要付一次全量重算**（实测 ~4.9 s）。这是「代码面进键」这条既有
纪律的代价：宁可重算，也不拿旧算法算出来的账当新账。判据见
`test_conformance_scan.DerivedResultCacheTest`（8 个站点、表驱动；「读到的件必须落在声明输入面内」
这一条会在给扫描器加新读取时先红——本轮它当场抓出两处漏声明）。

```sh
nf daemon start                      # 拉起守护（后台；只绑 127.0.0.1 + 一次性令牌）
nf daemon start --watch              # 另开：目录监听 + 只读命令响应缓存（树没变即整条复用）
eval "$(nf daemon shell-init bash)"  # 装进当前 shell：零子进程客户端（真毫秒级）
nf daemon bench                      # 复跑上表（--json 机读）
nf daemon stop                       # 停用：立刻回到 python 直跑，不改变任何可用性
```

纪律（与全仓一致，均有判据）：

- **只加速不改语义**：守护的 `(exit, stdout, stderr)` 与**真子进程直跑逐字节相同**（`test_daemon` 逐命令比对）。
- **热进程不得陈旧**：每次请求前清空**按路径键**的缓存（`pack_combo` 画像 / `registry_loader` 注册表），
  保留**内容键**缓存（围栏 YAML、引用度普查——键即内容，天然不陈旧）；另按 `core/scripts` **源码指纹**
  判断是否整块重载，绝不拿旧代码回话。
- **安全边界**：只绑 `127.0.0.1`（**没有**放行外网的开关）+ 一次性令牌（回环不是信任边界）+ 请求
  1 MiB 上限；长驻/自指命令（`serve` / `shell` / `terminal` / `lsp` / `daemon`）在守护内**拒跑**，且拒绝后守护仍存活。**别名与常驻面一视同仁**（2026-10-01 修）：`terminal` 是 `shell` 的别名、`lsp` 是常驻 stdio 服务，此前不在拒跑表里 ⇒ 经守护快路会**静默零输出地以 0 退出**，直跑却真起服务。
- **可回退**：任何一步不成立（无状态文件 / 无 bash / 连不上 / 协议头不对）启动器都**静默回退** python 直跑。

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
