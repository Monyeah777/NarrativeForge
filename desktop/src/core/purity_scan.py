"""42 M3：架构纯度体检（verify check27 · 文档级 grep 断言族）。

每波收口前跑纯度体检，首批四规则（文档级，纯 stdlib）：

R1 层级越界/端壳残留：协议真相源（01/02）不得再出现 android/APK/src/ui/Kivy
    （APK 线裁决 #16 移除后的残留扫描）。
R2 私货/可变物：协议层文档（01/02/06/07）不得出现机器不可复现内容
    （绝对盘符路径 / 临时目录 / TODO-FIXME-XXX-TBD 占位）。
R3 冗余标题：同文档内重复章节标题（同一标题文本出现 >1 次）。
R4 错误信息即微型文档：desktop/src/core 全部 raise 消息须含修复/指引语
    （应为/先/请/须/必填/参考/示例/§ 等动作或出处词——标准批 A #12）。
R5 import 面越界：desktop/src/core + scripts 的第三方 import 面必须**登记**——
    只许 stdlib / 本地模块 / HARD_ALLOW 登记的硬依赖；其余第三方必须**软导入**
    （try/except ImportError 守卫）且在 SOFT_IMPORTS 登记理由；已退役端壳的存量残留
    在 IMPORT_RESIDUE 登记（**WARN 挂账**，带裁决指针，不判死但不得隐身）。
    （内部差距：CONTRIBUTING §4.2「core 零第三方依赖」是成文红线，此前**零判据**。）
R6 危险 sink 面：desktop/src/core + scripts 不得出现**动态执行 / shell 命令 / 不安全
    反序列化**（eval / exec / __import__ / os.system / os.popen / subprocess(shell=True) /
    pickle.load(s) / marshal.loads / yaml.load）——确需使用须在 SINK_ALLOW 登记并写明理由
    （放行可审计；list 参数调用 subprocess 不受限）。
    （内部差距：安全兜底此前**零判据**——NF 只靠人读与本仓之外的 linter；实测 sink 面
    仅 1 处受控 `__import__`，故本条落地即零返工。）

check27 自身用变异注入验证捕获力（mutation testing：test_purity_scan 对
每规则注入典型违规样本，断言可被捕获——「check 的 check」）。
"""
from __future__ import annotations

import ast
import os
import re
import sys

#: 协议真相源 + 导航文档（R1/R2/R3 作用域）
PROTO_DOCS = ("01_核心协议.md", "02_联动注册表.md",
              "06_Agent执行协议.md", "07_官方核心出厂与社区预设导航.md")

_END_SHELL = re.compile(r"(?i)(android|APK|src/ui|Kivy)")
_PRIVATE = re.compile(r"[A-Za-z]:\\|/tmp/|/Users/|/home/|TODO|FIXME|XXX|TBD")

#: R5 硬依赖白名单（**登记**的第三方硬 import：允许直接 import）
HARD_ALLOW = {
    "yaml": "PyYAML（仓库既有依赖；check16/28 同源解析，见 CONTRIBUTING §4.2 例外）",
}
#: R5 软导入登记（第三方可选依赖：必须 try/except ImportError 守卫 + 写明理由）
SOFT_IMPORTS = {
    "jsonschema": "IDL 标准实现交叉验证（可选对照；缺依赖则跳过该面）",
    "PySide6": "CCV3 卡面占位图写入（缺依赖须给明确修复指引，不得裸 ImportError）",
    "laya": "决策层本地服务（scripts/serve_decision_model.py）的模型运行时；软导入 + 缺依赖给修复指引",
}
#: R5 存量残留（**WARN 挂账**：确有理由保留的存量违规，须带裁决/文档指针；不判死但不得隐身）
#: 空表即"零残留"。注意本扫描按**文件系统**取件（与 verify 其它 check 同口径）——
#: 未入库的本地副本同样会被扫到，故"仓库干净"不等于"工作目录干净"。
#: 2026-09-20：唯一一项残留（`scripts/` 下端壳自检旧脚本，属 `.git/info/exclude` 的本地旧副本）
#: 经作者裁决删除，登记随之清空。
IMPORT_RESIDUE: dict = {}
IMPORT_SCAN = ("desktop/src/core/*.py", "scripts/*.py")

#: R6 危险 sink（AST 级；键 = 规范化调用名）+ CWE 对齐（外部缺陷类型编码，便于跨工具对账）
DANGEROUS_CALLS = {
    "eval": "CWE-95 动态执行（输入可注入）",
    "exec": "CWE-95 动态执行（输入可注入）",
    "__import__": "CWE-470 动态导入（须证明模块名非用户输入）",
    "os.system": "CWE-78 shell 命令（改用 subprocess 列表参数）",
    "os.popen": "CWE-78 shell 管道（改用 subprocess 列表参数）",
    "pickle.load": "CWE-502 不安全反序列化（可执行任意代码）",
    "pickle.loads": "CWE-502 不安全反序列化（可执行任意代码）",
    "marshal.loads": "CWE-502 不安全反序列化",
    "yaml.load": "CWE-502 非安全 YAML 载入（改用 yaml.safe_load）",
}
#: R6 已登记放行（键 = "<文件基名>:<调用名>"；放行须可审计）
SINK_ALLOW = {
    "regression_score.py:__import__":
        "模块名取自内部常量表 SIGNAL_SPECS（非用户输入），用于按名调用既有扫描器",
}
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


def _guarded_import_lines(tree: ast.AST) -> set:
    """try/except {ImportError|ModuleNotFoundError|Exception|bare} 守卫体内的 import 行号。"""
    out = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Try):
            continue
        catches = False
        for h in node.handlers:
            if h.type is None:
                catches = True
            elif isinstance(h.type, ast.Name):
                catches = catches or h.type.id in ("ImportError", "ModuleNotFoundError", "Exception")
            elif isinstance(h.type, ast.Tuple):
                names = {e.id for e in h.type.elts if isinstance(e, ast.Name)}
                catches = catches or bool(names & {"ImportError", "ModuleNotFoundError", "Exception"})
        if not catches:
            continue
        for sub in node.body:
            for n2 in ast.walk(sub):
                if isinstance(n2, (ast.Import, ast.ImportFrom)):
                    out.add(n2.lineno)
    return out


def _top_modules(tree: ast.AST) -> list:
    """→ [(module_top_name, lineno)]（跳过相对导入）。"""
    out = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            out += [(a.name.split(".")[0], node.lineno) for a in node.names]
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            out.append((node.module.split(".")[0], node.lineno))
    return out


def _is_local(mod: str, root: str) -> bool:
    if mod == "core":
        return True
    for base in (os.path.join(root, "desktop", "src", "core"), os.path.join(root, "scripts")):
        if os.path.exists(os.path.join(base, mod + ".py")):
            return True
    return False


def scan(root: str = ".") -> tuple:
    issues = []
    stats = {"docs": 0, "raises": 0, "imports": 0, "import_residue": []}
    # R1/R2/R3：协议层文档
    for name in PROTO_DOCS:
        path = os.path.join(root, name)
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
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
                with open(fpath, encoding="utf-8") as fh:
                    tree = ast.parse(fh.read())
            except (OSError, SyntaxError):
                continue
            for lineno, msg in _iter_raise_messages(tree):
                stats["raises"] += 1
                if msg and not _ACTION.search(msg):
                    issues.append("%s:%d raise 消息缺修复指引：%s"
                                  % (fname, lineno, msg[:60]))
    # R5：import 面（core + scripts 的第三方依赖须登记；软导入才可免硬依赖）
    import glob as _glob
    for rel_pat in IMPORT_SCAN:
        for f in sorted(_glob.glob(os.path.join(root, rel_pat))):
            rel = os.path.relpath(f, root).replace("\\", "/")
            try:
                with open(f, encoding="utf-8") as fh:
                    tree = ast.parse(fh.read())
            except (OSError, SyntaxError):
                continue
            guarded = _guarded_import_lines(tree)
            residue = IMPORT_RESIDUE.get(rel)
            for mod, lineno in _top_modules(tree):
                if mod in sys.stdlib_module_names or _is_local(mod, root):
                    continue
                stats["imports"] += 1
                if mod in HARD_ALLOW:
                    continue
                if mod in SOFT_IMPORTS:
                    if lineno not in guarded:
                        msg = ("%s:%d 第三方 %s 未软导入（须 try/except ImportError 守卫；"
                               "登记理由：%s）" % (rel, lineno, mod, SOFT_IMPORTS[mod]))
                        (stats["import_residue"] if residue else issues).append(
                            "%s（%s）" % (msg, residue) if residue else msg)
                    continue
                msg = ("%s:%d 第三方 import 未登记：%s（修复指引：改为软导入并在 purity_scan.SOFT_IMPORTS "
                       "登记理由，或加入 HARD_ALLOW；端壳残留则登记 IMPORT_RESIDUE）" % (rel, lineno, mod))
                (stats["import_residue"] if residue else issues).append(
                    "%s（%s）" % (msg, residue) if residue else msg)
            # R6：危险 sink 面（同一次 AST 遍历复用 tree）
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                call = ast.unparse(node.func)
                flags = []
                if call in DANGEROUS_CALLS:
                    flags.append(call)
                for kw in node.keywords:
                    if kw.arg == "shell" and isinstance(kw.value, ast.Constant) \
                            and kw.value.value is True:
                        flags.append("subprocess(shell=True)")
                for name in flags:
                    stats["sinks"] = stats.get("sinks", 0) + 1
                    key = "%s:%s" % (os.path.basename(f), "subprocess" if "shell" in name else call)
                    if key in SINK_ALLOW:
                        continue
                    issues.append("%s:%d 危险 sink %s（%s）——确需使用须在 purity_scan.SINK_ALLOW "
                                  "登记理由（修复指引：改用安全等价物，或登记后写明为何不可注入）"
                                  % (rel, node.lineno, name,
                                     DANGEROUS_CALLS.get(call, "shell=True 命令注入面")))
    # R6 自洽面（登记表自身的判据）：每个 sink 类目须带 CWE 对齐（跨工具对账用缺陷类型编码），
    # 且 SINK_ALLOW 的每个放行键必须指向一个已登记 sink——放行不能凭空出现。
    for call, desc in sorted(DANGEROUS_CALLS.items()):
        if not re.match(r"^CWE-\d+ ", desc):
            issues.append("危险 sink 类目缺 CWE 对齐：%s（修复指引：在 purity_scan.DANGEROUS_CALLS "
                          "的说明前加 `CWE-<nnn> `，便于外部扫描器按缺陷类型对账）" % call)
    for key in sorted(SINK_ALLOW):
        sink = key.rsplit(":", 1)[-1]
        if sink not in DANGEROUS_CALLS and sink != "subprocess":
            issues.append("SINK_ALLOW 放行键指向未登记 sink：%s（修复指引：删除放行，"
                          "或先在 DANGEROUS_CALLS 登记该 sink 类目）" % key)
    return issues, stats
