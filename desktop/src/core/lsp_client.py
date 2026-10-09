"""LSP 客户端装配面：把「哪个编辑器、填什么配置」这一件收敛成可生成的唯一真相。

为什么独立成模块（2026-10-08 拆分）：`core/lsp.py` 越过 800 行（新文件上限）后按纪律「能拆就拆」——
客户端配置与协议服务器是**两个变化原因**：前者跟着编辑器生态走（新增/修改编辑器支持），后者跟着
LSP 规范与 NF 语言面走。拆开后各自的判据面也清楚：配置生成有逐字投影判据
（`test_lsp.TestDocConfigStaysInSync`），协议行为有 `lsp.check` 与端到端帧级金标。

只覆盖**内置 LSP 客户端**的编辑器：Neovim（vim.lsp.start）/ Emacs（eglot）/ Helix（languages.toml）。
VS Code 类需要扩展宿主，本仓无编辑器可装载验证，**不生成**伪造配置——按 docs/lsp.md 的诚实标注
留给使用者。纯标准库；无副作用。
"""
from __future__ import annotations

#: 支持的编辑器（唯一真相 = 这里；CLI 的 --print-config choices 与文档示例都由它派生）
CLIENT_EDITORS = ("neovim", "emacs", "helix")

_CFG_HEAD = {
    "neovim": "Neovim（init.lua）",
    "emacs": "Emacs / eglot（init.el）",
    "helix": "Helix（languages.toml）",
}


def render_client_config(editor: str, root: str) -> str:
    """生成编辑器现成配置（唯一真相 = 本函数；docs/lsp.md 的示例由它产出）。"""
    e = (editor or "").strip().lower()
    if e not in CLIENT_EDITORS:
        raise ValueError("未知编辑器 %r（可选：%s）" % (editor, " / ".join(CLIENT_EDITORS)))
    cmd = "%s/scripts/nf.py" % root.replace("\\", "/").rstrip("/")
    if e == "neovim":
        body = ('vim.lsp.start({\n'
                '  name = "nf-lsp",\n'
                '  cmd = { "python", "%s", "lsp" },\n'
                '  root_dir = "%s",\n'
                '})\n') % (cmd, root.replace("\\", "/").rstrip("/"))
    elif e == "emacs":
        body = ("(with-eval-after-load 'eglot\n"
                "  (add-to-list 'eglot-server-programs\n"
                "               '(markdown-mode . (\"python\" \"%s\" \"lsp\"))))\n") % cmd
    else:
        body = ('[[language]]\n'
                'name = "markdown"\n'
                'language-servers = ["nf-lsp"]\n'
                '\n'
                '[language-server.nf-lsp]\n'
                'command = "python"\n'
                'args = ["%s", "lsp"]\n') % cmd
    return "# NF LSP · %s\n%s" % (_CFG_HEAD[e], body)
