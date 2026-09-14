# 编辑器接入（LSP）
> ⛔ 操作指令：阅读即执行——本文含可直接执行的配置与判定，勿当资料阅读。
> 最后更新：2026-09-14

## 是什么

`nf lsp` 是**最小 LSP 服务器**（stdio，`Content-Length` 分帧）：full-sync、发布诊断、
quickfix code action；诊断源与 `nf lint` / `nf lint --prose` 同源，**不自行写盘**。

## 怎么接

VS Code（`settings.json`，需 `vscode-languageclient` 类通用客户端或自建扩展）：

```json
{"nf-lsp": {"command": "python", "args": ["<仓库绝对路径>/scripts/nf.py", "lsp"]}}
```

Neovim（`init.lua`）：

```lua
vim.lsp.start({ name = "nf-lsp", cmd = { "python", "<仓库绝对路径>/scripts/nf.py", "lsp" },
  root_dir = "<仓库绝对路径>" })
```

## 自测（无需编辑器）

```bash
python -m unittest desktop.tests.test_lsp -v     # 分帧 / 诊断 / quickfix 全链
```

## 边界（诚实标注）

- **未在真实编辑器里装载验证过**（本仓工作机无 VS Code/Neovim）——协议层与回归测试已过，
  编辑器侧装载留给使用者；装载结果请回填本文件。
- 只做 full-sync + 诊断 + quickfix；不做增量同步、不做工作区编辑、不发写盘动作。
