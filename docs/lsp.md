# 编辑器接入（LSP）
> ⛔ 操作指令：阅读即执行——本文含可直接执行的配置与判定，勿当资料阅读。
> 最后更新：2026-10-07

## 是什么

`nf lsp` 是 NF 的 LSP 服务器（stdio，`Content-Length` 分帧）：**诊断 + 领域智能 + quickfix**。
诊断源与 `nf lint` / `nf lint --prose` 同源；领域符号表来自 `core/nf_language`（模块 id /
资产键 / 事件名 / 层位 id / 管线 id，全部从 registry.json、`machine_contract`、事件登记表
与文件面派生，不造第二份事实）。**不自行写盘**——编辑只经 `codeAction` 交客户端。

**入站资源闸门**：单条消息（含表头行）上限 **8 MiB**——`Content-Length` 超限或为负、
表头行不发换行地超长，一律判坏帧回 `-32700` 并**继续服务**（与 MCP 面同一档上限、同一类取证）。

### 能力表

| 能力 | LSP 方法 | 说明 |
|---|---|---|
| 同步 | `initialize` → `textDocumentSync` | full-sync（openClose + save）；**不做增量同步** |
| 诊断 | `textDocument/publishDiagnostics` | 两类源（`nf` 机械规则 / `nf-prose` 正文 lint），逐条带真实行/列 |
| 修复 | `textDocument/codeAction` | `quickfix`：最小行级编辑（回放校验不过则退整文档替换） |
| 补全 | `textDocument/completion` | 模块 id / 资产键 / 事件名 / 层位 id / 管线 id（前缀补全） |
| 悬停 | `textDocument/hover` | 符号元数据（模块名与挂载、事件发布/订阅方、资产所属包……） |
| 跳定义 | `textDocument/definition` | 引用 → 定义件；**歧义失败关闭**（不猜，见下「边界」） |
| 大纲 | `textDocument/documentSymbol` | Markdown 标题树（跳过围栏代码块）；按客户端能力给层级/扁平两形态 |
| 工作区符号 | `workspace/symbol` | 全仓符号检索（模块/资产/事件/层位/管线） |
| 折叠 | `textDocument/foldingRange` | 标题小节（到下一个同级/更高级标题前）+ 代码围栏；单行区间不给（客户端会忽略，给了只是噪声） |
| 引用 | `textDocument/references` | **只认登记关系**（事件 ↔ 发布/订阅模块、模块 ↔ 挂载层、管线 ← 域包采用）；每条位置都可解释（why），未登记一律空表——**不做全文搜索**（会喷假引用） |
| 位置编码 | `positionEncoding` | 固定 `utf-16`（LSP 默认口径，客户端必须支持） |

## 三步接入

第 1 步：生成配置（**不必手抄**）——唯一真相是同一个渲染器，下面三块配置即它的输出：

```bash
python scripts/nf.py lsp --print-config neovim     # 也可 emacs / helix
```

第 2 步：把输出粘进编辑器配置（LSP 客户端走 stdio，路径指向**仓库绝对路径**）。
第 3 步：重启编辑器，打开仓库内任意 `.md`。

Neovim（`init.lua`）：

```lua
vim.lsp.start({
  name = "nf-lsp",
  cmd = { "python", "<仓库绝对路径>/scripts/nf.py", "lsp" },
  root_dir = "<仓库绝对路径>",
})
```

Emacs / eglot（`init.el`）：

```elisp
(with-eval-after-load 'eglot
  (add-to-list 'eglot-server-programs
               '(markdown-mode . ("python" "<仓库绝对路径>/scripts/nf.py" "lsp"))))
```

Helix（`languages.toml`）：

```toml
[[language]]
name = "markdown"
language-servers = ["nf-lsp"]

[language-server.nf-lsp]
command = "python"
args = ["<仓库绝对路径>/scripts/nf.py", "lsp"]
```

## 自测（无需编辑器）

```bash
python -m unittest desktop.tests.test_lsp desktop.tests.test_lsp_hardening desktop.tests.test_nf_language -v
```

## 边界（诚实标注）

- **未在真实编辑器里装载验证过**（本仓工作机无 VS Code / Neovim / Emacs / Helix）——协议行为由
  回归测试与 `check33` 的编辑器面判据覆盖（能力声明 / 诊断定位 / didClose / 退出码 / 领域解析 /
  补全·悬停·跳定义·大纲 / 配置生成），编辑器侧装载留给使用者——**本仓不假称已验证**。
  interop 他证通道的 `lsp` 面**尚未补卡**（补它要同步 .NET 线 golden，前置见
  `results/audit/docs_audit-93-three-axis-adapters.md`）；补卡前本文件不指向任何回填行。
- **VS Code 类不生成配置**：其 LSP 客户端需要扩展宿主，本仓无编辑器可装载验证，故不提供
  未经实测的扩展或配置（不假称已适配）。内置 LSP 客户端的编辑器（Neovim / Emacs / Helix）可直接接入。
- 只做 full-sync + 诊断 + 领域智能 + quickfix + **结构化引用** + **折叠**；不做增量同步、不做格式化、不做语义高亮。
- **歧义标识符不跳定义**：裸号 `M10` 同属 `通用:M10` / `生存:M10`，`P00` 同属层位与官方管线——
  这类 token 只在悬停里列出全部同名候选，跳定义按失败关闭处理（不猜一个）。
- **引用不是文本搜索**：只有 `registry.json` 里登记的关系才给位置；`P00` 这类同名 token 会把「层位」
  与「管线」两种关系的命中一并列出（每条带 why 说明来源），而不是猜一种。
