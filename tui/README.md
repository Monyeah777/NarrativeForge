# NF 终端 TUI（nf-tui）

> 最后更新：2026-10-02

> 全屏人机入口，配套（不是替代）`nf shell` 的逐行交互面。命令真源仍是 `scripts/nf.py`
> 的 argparse 面——TUI 只做「菜单 / 参数 / 闸门 / 渲染」，不复制任何业务逻辑。

## 是什么

`nf shell`（`desktop/src/core/terminal.py`）面向可重定向、可 diff、可进 CI 的**逐行**用法；
本目录补另一档：**全屏 TUI**——固定框架 + 八能力区菜单 + 详情/输出双栏 + 键入式参数，
面向人开着窗口点着用的场景。两者共用同一套语义（写盘闸门、命令白名单、非 TTY 回退）。

```sh
python tui/nf.py                 # 全屏 TUI（TTY 下）
python tui/nf.py --selftest      # 内建安全判据（退出码即结论）
python tui/nf.py --demo          # 打印一帧演示画面（确定性，不需仓库）
python tui/nf.py --list-actions  # 列出全部动作与其 argv
python tui/nf.py --exec "nf doctor"   # 非交互执行一条命令（脚本面）
```

## 键位（对标 lazygit / k9s / yazi 的公开约定）

焦点模型是这类终端的第一条纪律：**`↑↓` 只在当前面板内移动，换面板另有其键**。

| 键 | 作用 |
|---|---|
| `Tab` · `←/→` · `h`/`l` | 切换面板（能力区 → 动作 → 输出，循环） |
| `↑`/`↓` 或 `k`/`j` | 在**当前**面板内移动选择；输出面板上为逐行滚动 |
| `Enter` | 运行选中动作；缺参数时逐项追问（路径参数过包含性判据） |
| `/` | 过滤当前面板；焦点在输出面板时改为**检索输出**（`n`/`N` 跳命中） |
| `PgUp`/`PgDn` · `Ctrl-U`/`Ctrl-D` · `Home`/`End` | 输出翻页 / 到顶到底（越界即回到跟随末尾） |
| `R` | 重跑上一条命令（写盘类仍须重新键入 `yes`） |
| `Esc` | 关闭浮层 / 取消输入 / 清除过滤 |
| `?` | 键位帮助（任意键关闭） |
| `q` · `Ctrl-C` | 退出；**命令运行中 `Ctrl-C` 只取消该命令**，不杀会话 |

命令在**工作线程**里跑：主循环继续重绘，状态栏显示转轮与已用时间，所以长命令不再让界面假死。
非 TTY、`--plain` 或 `--exec` 时自动回退逐行模式（可重定向、可进 CI）。

## 给 agent 的四个面（无 TTY 也能用）

| 面 | 用途 | 输出契约 |
|---|---|---|
| `python tui/nf.py --list-actions --json` | 发现全部动作、argv 模板与参数名 | 对象，顶层 `kind=nf-tui-actions` + `actions` / `exit_codes` / `surfaces` |
| `python tui/nf.py --exec "nf doctor"` | 跑一条命令并透传其退出码 | stdout/stderr 即子命令原样；退出码 = 子命令退出码 |
| `python tui/nf.py --selftest --json` | 安全底线自检 | 对象，顶层 `kind=nf-tui-selftest` + `ok` + 逐条 `rows` |
| `python tui/nf.py --demo` | 取一帧确定性演示画面 | 纯文本帧，无 ANSI，任何环境可渲染 |

失败面统一为 `{"ok": false, "error": …, "exit": N}`（与仓库其它 `--json` 面同形）。
找不到仓库时也不会「什么都不显示」：TTY 下直接进全屏演示模式，非 TTY 下先打印演示帧再以退出码 4 报告。

## 四条安全底线（都有可执行判据）

1. **不用 shell**：子进程一律 `shell=False` + argv 列表，使用者输入只作字面参数。
   `split_argv()` 刻意**不是** shell 解析器——`;` `|` `&` `$` 反引号没有元字符语义。
   判据：`--selftest` 用真进程断言 `a;b|c&d` 原样送达。
2. **命令白名单 + 长驻拒跑**：首个动词须在 `KNOWN_TOP` 内（与 CLI 的 argparse 面逐条比对漂移）；
   `serve`/`daemon`/`shell`/`terminal`/`lsp` 直接拒跑（退出码 3）；写盘动词与写盘旗标须显式键入
   `yes` 才放行，CLI 自己的 `--yes` 闸门仍是第二层。
3. **路径包含性**：任何路径参数过 `validate_rel_path()`——拒绝对路径、`..` 段、盘符相对写法
   （`C:foo`），realpath 归一后断言落在仓库根内；自由文本命令里的路径形 token 同样过闸。
   口径与 `desktop/src/core/paths.py` 的 `validate_path` 同源。
4. **密钥不落地**：源码零硬编码；API 密钥只从环境变量（`NF_API_KEY` / `OPENAI_API_KEY` /
   `ANTHROPIC_API_KEY`）或**仓外**凭据文件读；打印一律 `mask_secret()`；疑似密钥的参数直接拒跑。

密钥没有出现在源码里，也没有出现在命令参数里——TUI 只把它从环境读进内存并遮蔽显示。

## 退出码

| 码 | 含义 | 典型触发 |
|---|---|---|
| 0 | 成功 | 命令跑完且退出 0 |
| 1 | 失败 | 子命令非 0 退出 / 自检不通过 |
| 2 | 用法错误 | argv 解析失败、动词不在白名单 |
| 3 | 安全拒跑 | 写盘未确认 / 长驻面 / 路径逃逸 / 密钥形态参数 |
| 4 | 环境错误 | 找不到仓库、无可用 Python、凭据文件不可读 |
| 130 | 中断 | 使用者 `Ctrl-C` |

## 打包单文件 exe

TUI 只用标准库，且不 import `core`，因此可以独立冻结成单文件可执行程序：

```sh
powershell -ExecutionPolicy Bypass -File tui/build_exe.ps1     # Windows
bash tui/build_exe.sh                                          # POSIX
```

产物是单文件可执行程序（Windows 上为 `nf.exe`）。冻结态下的行为差异只有一处：
CLI 调用改用 PATH 上的 `python`；找不到仓库时 `--demo` / `--selftest` / `--list-actions`
仍可离线运行，其余动作会以退出码 4 报「未发现 NarrativeForge 仓库」并给修复指引。

## 边界

- **不是第二套命令面**：菜单/动作只是 `scripts/nf.py` 真命令的受控调用方；
  `--selftest` 会拿真 argparse 面比对白名单，漂移即红。
- **不是 `nf shell` 的替代**：要可重定向、可 diff、可进 CI 的形态，用 `nf shell`（见 `docs/terminal.md`）。
- **只在仓库内读写**：需要写仓外路径的动作请在普通终端用 `nf` 直跑。
