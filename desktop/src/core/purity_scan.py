"""42 M3：架构纯度体检（verify check27 · 文档级 grep 断言族）。

每波收口前跑纯度体检，首批四规则（文档级，纯 stdlib）：

R1 层级越界/端壳残留：协议真相源（01/02）不得再出现 android/APK/src/ui/Kivy
    （APK 线裁决 #16 移除后的残留扫描）。
R2 私货/可变物：协议层文档（01/02/06/07）不得出现机器不可复现内容
    （绝对盘符路径 / 临时目录 / TODO-FIXME-XXX-TBD 占位）。
R3 冗余标题：同文档内重复章节标题（同一标题文本出现 >1 次）。
R4 错误信息即微型文档：desktop/src/core 全部 raise 消息须含修复/指引语
    （应为/先/请/须/必填/参考/示例/§ 等动作或出处词——标准批 A #12）。

check27 自身用变异注入验证捕获力（mutation testing：test_purity_scan 对
每规则注入典型违规样本，断言可被捕获——「check 的 check」）。
"""
from __future__ import annotations

import ast
import os
import re

#: 协议真相源 + 导航文档（R1/R2/R3 作用域）
PROTO_DOCS = ("01_核心协议.md", "02_联动注册表.md",
              "06_Agent执行协议.md", "07_官方核心出厂与社区预设导航.md")

_END_SHELL = re.compile(r"(?i)(android|APK|src/ui|Kivy)")
_PRIVATE = re.compile(r"[A-Za-z]:\\|/tmp/|/Users/|/home/|TODO|FIXME|XXX|TBD")
_HEAD = re.compile(r"^#{1,6}\s+(.*?)\s*$")
_ACTION = re.compile(
    r"(应|须|先|必填|必需|必须|请|建议|参考|查看|运行|执行|使用|改用|替换|修复|"
    r"补齐|重新|重跑|更正|核对|检查|可选|选项|列表|注册|示例|格式|参见|见|按|需|"
    r"选择|可用|如|缺少|缺|期望|修正|§|文档|帮助|重试|再)")


def _iter_raise_messages(tree: ast.AST):
    for node in ast.walk(tree):
        if isinstance(node, ast.Raise) and isinstance(node.exc, ast.Call) \
                and node.exc.args:
            arg = node.exc.args[0]
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                yield node.lineno, arg.value
            elif isinstance(arg, ast.JoinedStr):
                parts = [v.value for v in arg.values
                         if isinstance(v, ast.Constant) and isinstance(v.value, str)]
                yield node.lineno, "".join(parts)


def scan(root: str = ".") -> tuple:
    issues = []
    stats = {"docs": 0, "raises": 0}
    # R1/R2/R3：协议层文档
    for name in PROTO_DOCS:
        path = os.path.join(root, name)
        if not os.path.exists(path):
            continue
        text = open(path, encoding="utf-8").read()
        stats["docs"] += 1
        if name in ("01_核心协议.md", "02_联动注册表.md"):
            for i, ln in enumerate(text.splitlines(), 1):
                if _END_SHELL.search(ln):
                    issues.append("%s:%d 端壳/APK 残留：%s"
                                  % (name, i, ln.strip()[:80]))
        for i, ln in enumerate(text.splitlines(), 1):
            if _PRIVATE.search(ln):
                issues.append("%s:%d 私货/可变物：%s"
                              % (name, i, ln.strip()[:80]))
        seen = {}
        for i, ln in enumerate(text.splitlines(), 1):
            m = _HEAD.match(ln)
            if not m:
                continue
            title = m.group(1).strip()
            seen.setdefault(title, []).append(i)
        for title, lines in seen.items():
            if len(lines) > 1:
                issues.append("%s 重复标题「%s」：行 %s"
                              % (name, title, ",".join(map(str, lines))))
    # R4：错误信息审计（desktop/src/core/*.py）
    core_dir = os.path.join(root, "desktop", "src", "core")
    if os.path.isdir(core_dir):
        for fname in sorted(os.listdir(core_dir)):
            if not fname.endswith(".py"):
                continue
            fpath = os.path.join(core_dir, fname)
            try:
                tree = ast.parse(open(fpath, encoding="utf-8").read())
            except (OSError, SyntaxError):
                continue
            for lineno, msg in _iter_raise_messages(tree):
                stats["raises"] += 1
                if msg and not _ACTION.search(msg):
                    issues.append("%s:%d raise 消息缺修复指引：%s"
                                  % (fname, lineno, msg[:60]))
    return issues, stats
