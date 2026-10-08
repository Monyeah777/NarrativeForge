# ninfenz · npm 一键包

**NinFenz（NF）是内容契约层（content contract layer）**：把「AI 稳定产出长内容」变成可装载、可质检、可复现的工程。协议域中立、模型无关；叙事只是官方第一个域包。
**不是**模型、**不是**提示词模板集、**不是**某厂商 SDK。MIT。

本包是 NF 的**一键入口**：零安装脚本、零网络请求、零遥测；首次运行把随包 payload 解到缓存目录（带 sha256 清单校验），然后原样把参数转发给 NF CLI。

## 快速开始

```bash
# 跑一条只读体检（不需要 clone）
npx -y ninfenz doctor

# 打开 NF 终端 TUI（纯标准库全屏界面）
npx -y ninfenz tui

# 看看命令面
npx -y ninfenz --help

# 把 payload 落成一份真实工作树（想自己跑 verify.sh 时）
npx -y ninfenz install --dest ./nf
cd nf && bash verify.sh        # Windows 用 Git Bash
```

全局安装（可选）：

```bash
npm i -g ninfenz
nf doctor
```

## 前置条件

| 项 | 要求 | 说明 |
|---|---|---|
| Node.js | **>= 18.17** | 只用于启动器（无第三方依赖） |
| Python | **>= 3.11** | NF CLI 本体；纯标准库，无 pip 依赖 |

Python 探测顺序：`NINFENZ_PYTHON` → `py -3`（Windows）→ `python3` → `python`。
找不到或版本过低时**直接拒绝启动并给修复指引**（fail-closed，不静默降级）。

> 可选：装了 PyYAML 时 YAML 字段全量解析；没装会打印一条 WARN 并退回**子集口径**（NF 本体零硬依赖，这是设计而非故障；静默可设 `NF_QUIET_YAML=1`）。

## 入口面

| 入口 | 命令 | 用途 |
|---|---|---|
| npx | `npx -y ninfenz <子命令>` | 一次性体验 / CI 里临时调用 |
| 全局 | `npm i -g ninfenz` → `nf <子命令>` | 常驻终端入口 |
| 已有检出 | `nf --repo <目录> <子命令>` | 跳过解包，直接跑你的工作树 |
| 物化 | `nf install --dest <目录>` | 把 payload 落成可用的运行时工作树（自证门禁走 git clone） |
| MCP | `npx -y ninfenz serve` | 只读 MCP 服务面（双协议版本） |

## 包里有什么（由 `tools/stage-payload.mjs` 从 git 受跟踪文件生成）

- 协议件 `01–07`、`STRATEGY.md`、`llms.txt`、`docs/agent/AGENT_START.md`、`docs/agent/AI_ROUTING.md`、`docs/meta/DEEP_DIVE.md`
- 核心库 `desktop/src/**`、CLI `scripts/**`、终端 `tui/nf.py`
- 资产 `03_管线库` / `04_模块库` / `05_资产库`、域包 `community/**`、标准目录与注册表 `protocol/**`
- 门禁 `verify.sh` 与其单测 `desktop/tests/**`

> **自证门禁的正确方式**：payload 是**运行时 / 协议树**（不含 `.github/`、`results/`、`.git`）。`install --dest` 得到的是可用工作树（CLI / TUI / MCP 正常），**要跑完整 check1-40 门禁请 git clone 后 `bash verify.sh`**——`verify.sh` 依赖上述仓库件，这是设计而非缺陷。
- 清单 `payload/payload-manifest.json`：逐文件 sha256 + 聚合 `tree_sha256`

当前体积：**2945 件 · 解包 19.75 MB**（tarball 远小于此；域名包与标准目录占主要体积）。

## 供应链纪律（为什么可以放心 npx）

- **没有 `preinstall/install/postinstall`**：安装期零执行（`npm run verify` 会强制这一点）。
- **payload 逐文件 sha256 校验**：解包后立刻核对，不一致即拒绝启动。
- **固定 mtime**：暂存时把 mtime 归一到固定时间戳，减少构建噪声。
- **发布带 provenance**：`publishConfig.provenance = true`，由 GitHub Actions OIDC 签发来源证明。
- **可 `--ignore-scripts` 安装**：不影响任何功能。

## 环境变量

| 变量 | 作用 |
|---|---|
| `NINFENZ_PYTHON` | 指定 Python 解释器 |
| `NINFENZ_CACHE` | 指定解包缓存目录 |
| `PYTHONUTF8` / `PYTHONIOENCODING` | 启动器自动设为 `1` / `utf-8`（中文输出必需） |

缓存目录：Windows `%LOCALAPPDATA%\ninfenz\cache`；其余 `$XDG_CACHE_HOME/ninfenz` 或 `~/.cache/ninfenz`。
清理：直接删该目录（不会影响已有检出）。

## 链接

- **站点（官方唯一入口）**：https://ninfenz.dev/　机器面：/llms.txt · /llms-full.txt · /facts.json
- 仓库（canonical）：https://github.com/Monyeah777/NinFenz
- 国内镜像：https://gitee.com/monyeah777/ninfenz
- 机器入口 `llms.txt`：https://raw.githubusercontent.com/Monyeah777/NinFenz/main/llms.txt
- MCP 接入：https://raw.githubusercontent.com/Monyeah777/NinFenz/main/docs/mcp.md
- 许可：MIT（见包内 `LICENSE`）

## 维护者：发布流程

```bash
cd packaging/npm
npm run stage     # 暂存 payload（含版本口径闸门：package.json 版本 == NF_CLI_VERSION）
npm run verify    # 发布前自检（安装脚本/payload 校验/元数据/预算）
npm test          # 冒烟测试（清单自洽 + 快路径 + 真跑 doctor）
npm pack --dry-run
npm publish --provenance --access public   # 或走 .github/workflows/npm-publish.yml
```
