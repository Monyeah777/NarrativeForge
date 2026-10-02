#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""NarrativeForge 终端 TUI（nf-tui）——端壳退役后的全屏人机入口。

定位
----
`nf shell`（`desktop/src/core/terminal.py`）是**逐行**交互面：可重定向、可 diff、可进 CI。
本模块补另一档：**全屏 TUI**——固定框架 + 能力区菜单 + 详情/输出双栏 + 键入式参数，
面向「人开着窗口点着用」的场景。两者不冲突：命令真源始终是 `scripts/nf.py` 的
argparse 面，TUI 只是它的**受控调用方**（不复制业务逻辑，不维护第二份命令表）。

四条安全底线（本模块自己守，不外包给调用方）
--------------------------------------------
1. **不用 shell**：所有子进程一律 ``shell=False`` + argv 列表；使用者输入只作**字面参数**，
   永不参与 shell 解析——``doctor; rm -rf /`` 会被当成一个普通参数原样传给目标进程
   （`--selftest` 有可执行判据）。
2. **命令白名单 + 长驻拒跑**：可执行的首个动词必须在 `KNOWN_TOP` 内；
   `serve` / `daemon` / `shell` / `terminal` / `lsp` 这类长驻面直接拒跑；
   写盘动词与写盘旗标须使用者显式键入 `yes` 才放行（CLI 自己的 `--yes` 闸门是第二层）。
3. **路径包含性**：任何路径参数过 `validate_rel_path()`——拒绝对路径、`..` 段、
   Windows 盘符相对写法（`C:foo`），realpath 归一后断言落在仓库根内；
   口径与 `desktop/src/core/paths.py::validate_path` 同源，不另立一套语义。
4. **密钥不落地**：API 密钥只从环境变量或**仓外**凭据文件读；源码里不硬编码任何密钥
   （`--selftest` 扫自身源件核对），打印一律走 `mask_secret()`，并拒绝把密钥形态的
   参数塞进将被执行的命令。

退出码（与 `nf` CLI 的 0/1/2 约定兼容，向后扩展两档）
-----------------------------------------------------
====  ====  ============================================
码    含义  典型触发
====  ====  ============================================
0     成功  命令跑完且退出 0
1     失败  子命令非 0 退出 / 输出渲染失败
2     用法  argv 解析失败、动词不在白名单
3     拒跑  写盘未确认 / 长驻面 / 安全闸门拦下
4     环境  找不到 NF 仓库、无可用 Python、凭据文件不可读
130   中断  使用者 Ctrl-C
====  ====  ============================================
"""
from __future__ import annotations

import argparse
import json
import os
import queue
import re
import subprocess
import sys
import threading
import time
import unicodedata
from pathlib import Path

# 控制台编码钉 UTF-8：Windows 默认按本地代码页落盘，中文框线与诊断会直接抛
# UnicodeEncodeError（本模块的渲染面全是中文 + 框线字符）。
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

APP = "nf-tui"
VERSION = "1.0.0"

EXIT_OK = 0
EXIT_FAILURE = 1
EXIT_USAGE = 2
EXIT_REFUSED = 3
EXIT_ENV = 4
EXIT_INTERRUPT = 130

#: 仓库根识别物（两件同时在场才算——单看目录名会认错外仓）
_ROOT_MARKERS = ("verify.sh", os.path.join("scripts", "nf.py"))
#: 从候选起点向上找仓库根的层数上限（防止在盘根上无限走）
_ROOT_SEARCH_DEPTH = 6


# --------------------------------------------------------------------------- #
# 错误类型：每一档都对应一个退出码，绝不裸抛 traceback
# --------------------------------------------------------------------------- #
class NfTuiError(Exception):
    """本模块所有可预期错误的基类。`code` 即进程退出码。"""

    code = EXIT_FAILURE

    def __init__(self, message: str, hint: str = ""):
        super().__init__(message)
        self.message = message
        self.hint = hint

    def render(self) -> str:
        if self.hint:
            return "%s\n  修复指引：%s" % (self.message, self.hint)
        return self.message


class UsageError(NfTuiError):
    """argv / 交互输入用法错误。"""

    code = EXIT_USAGE


class RefusedError(NfTuiError):
    """安全闸门拒跑（写盘未确认、长驻面、密钥形态参数）。"""

    code = EXIT_REFUSED


class EnvError(NfTuiError):
    """环境/配置错误（找不到仓库、无 Python、凭据不可读）。"""

    code = EXIT_ENV


# --------------------------------------------------------------------------- #
# 安全原语：路径包含性 / 密钥遮蔽 / shell 无关的 argv 切分
# --------------------------------------------------------------------------- #
_DRIVE_RELATIVE = re.compile(r"^[A-Za-z]:(?![\\/])")


def contained(root: str, target: str) -> bool:
    """`target` 归一后是否落在 `root` 内（含 root 自身）。"""
    r = os.path.realpath(str(root))
    t = os.path.realpath(target if os.path.isabs(str(target)) else os.path.join(r, str(target)))
    return t == r or t.startswith(r + os.sep)


def validate_rel_path(root: str, value: str, *, allow_absolute: bool = False) -> str:
    """校验路径参数落在 `root` 内 → 返回根内绝对路径；否则抛 `RefusedError`。

    与 `desktop/src/core/paths.py::validate_path` 同一套判据（本模块零第三方依赖，
    不能 import core，故按同一口径重实现；`--selftest` 断言两处语义一致的关键样例）。
    """
    text = str(value or "")
    if not text.strip():
        raise RefusedError("路径为空", "给出根内相对路径，如 docs/terminal.md")
    if "\x00" in text or "\n" in text or "\r" in text:
        raise RefusedError("路径含控制字符", "去掉换行/NUL 后重试")
    if os.path.isabs(text) and not allow_absolute:
        raise RefusedError("不接受绝对路径：%s" % text, "改用仓库内相对路径")
    if _DRIVE_RELATIVE.match(text):
        raise RefusedError("不接受盘符相对写法：%s" % text,
                           "改用仓库内相对路径，勿写 `C:foo` 这类会随盘符换根的写法")
    if ".." in text.replace("\\", "/").split("/"):
        raise RefusedError("路径不得含 `..` 段：%s" % text, "改用仓库内相对路径")
    full = os.path.realpath(os.path.join(os.path.realpath(str(root)), text))
    if not contained(root, full):
        raise RefusedError("路径逃逸仓库根：%s" % text, "目标须落在 %s 内" % root)
    return full


def mask_secret(value: str, *, keep_head: int = 3, keep_tail: int = 2) -> str:
    """密钥一律遮蔽后再进日志/屏幕：`abcdefg…` → `abc***fg`。空串回空串。"""
    text = str(value or "")
    if not text:
        return ""
    if len(text) <= keep_head + keep_tail:
        return "*" * len(text)
    return "%s%s%s" % (text[:keep_head], "*" * 4, text[-keep_tail:])


#: 凭据形态（**拼接构造**：本件自身不得落任何真形态串，否则会被仓库泄漏门禁命中）
_SECRET_SHAPES = (
    "ghp" + "_" + "[A-Za-z0-9]{20,}",
    "github" + "_pat_" + "[A-Za-z0-9_]{20,}",
    "glpat" + "-" + "[A-Za-z0-9_-]{20,}",
    "sk" + "-" + "[A-Za-z0-9]{20,}",
    "AKIA" + "[0-9A-Z]{16}",
    "BEGIN" + " [A-Z ]*" + "PRIVATE KEY",
)
_SECRET_RE = re.compile("|".join(_SECRET_SHAPES))


def split_argv(text: str) -> list:
    """把一行输入切成 argv——**刻意不是 shell 解析器**。

    只认空格分隔与 `"…"` / `'…'` 分组；`;` `|` `&` `$` 反引号一律当**普通字符**原样保留。
    没有元字符语义，就没有注入面（`--selftest` 用真进程证明这一点）。
    """
    tokens, buf, quote, started = [], [], None, False
    for ch in str(text or ""):
        if quote:
            if ch == quote:
                quote = None
            else:
                buf.append(ch)
            continue
        if ch in ("\"", "'"):
            quote, started = ch, True
            continue
        if ch.isspace():
            if started or buf:
                tokens.append("".join(buf))
                buf, started = [], False
            continue
        buf.append(ch)
        started = True
    if quote:
        raise UsageError("引号未闭合：%s" % text, "补上结尾引号，或去掉引号改用空格分隔")
    if started or buf:
        tokens.append("".join(buf))
    return tokens


# --------------------------------------------------------------------------- #
# 命令面元数据：白名单 / 写盘闸门 / 长驻拒跑 / 动作目录（菜单真源）
# --------------------------------------------------------------------------- #
#: CLI 顶层命令（与 `scripts/nf.py` 的 argparse 面同源；有仓库时 `--selftest` 会逐条比对漂移）
KNOWN_TOP = (
    "approve", "assemble", "assertions", "asset", "attest", "audit", "bench", "cognition",
    "combine", "completion", "conformance", "daemon", "decide", "decisions", "demo", "design",
    "diff", "doctor", "domain", "driver", "endpoint", "events", "explain", "handover", "help",
    "impact", "import", "interop", "knowledge", "layers", "library", "license", "lint", "lsp",
    "market", "model", "module", "output", "patterns", "pipeline", "postmortem", "preset",
    "receipts", "register", "related", "release", "rename", "render", "review", "rfc", "run",
    "score", "serve", "shell", "sig", "spec", "state-front", "stats", "st-validate", "telemetry",
    "terminal", "toolface", "transparency", "who-refers", "workloop", "worldmodel",
)
#: 长驻 / 自指面：在 TUI 里拒跑（会把前台会话吞掉，且不是「看一眼」类动作）
LONG_RUNNING = ("serve", "daemon", "shell", "terminal", "lsp")
#: 写盘旗标（出现任一即视为不可逆动作，须显式确认）——与 `core/terminal.py` 同一张表的口径
WRITE_FLAGS = ("--write", "--apply", "--register", "--force", "--out", "--dest", "--build",
               "--write-baseline", "--fix", "--harvest", "--write-advisory", "--certify", "--save")
#: 无旗标也写盘的 (命令, 子命令) 组合
WRITE_VERBS = (("asset", "add"), ("asset", "rm"), ("asset", "deprecate"), ("asset", "restore"),
               ("module", "deprecate"), ("module", "restore"), ("module", "signature"),
               ("register", ""), ("import", ""), ("rename", ""), ("release", ""), ("approve", ""),
               ("pipeline", "new"), ("decisions", "reindex"), ("patterns", "reindex"),
               ("library", "reindex"), ("library", "deprecate"), ("library", "restore"),
               ("library", "supersede"), ("library", "attest"), ("combine", "certify"))


def classify(argv: list) -> str:
    """给一条 argv 定档：`long` / `write` / `read`（拒跑与闸门共用这一个判定）。"""
    if not argv:
        raise UsageError("空命令", "至少给出一个 nf 子命令，如 `nf doctor`")
    top = argv[0]
    sub = argv[1] if len(argv) > 1 and not argv[1].startswith("-") else ""
    if top in LONG_RUNNING:
        return "long"
    if any(tok in WRITE_FLAGS for tok in argv):
        return "write"
    if (top, sub) in WRITE_VERBS or (top, "") in WRITE_VERBS:
        return "write"
    return "read"


def guard_path_tokens(root, argv: list) -> None:
    """自由文本命令里的**路径形**参数也要过包含性判据。

    只认「含 `/` 或 `\\`」或盘符相对写法（`C:x.md`）的 token（所以 `通用类:M00` 这类
    模块号、`--fmt ccv3` 这类枚举值不会被误判）；剥掉 `--flag=value` 的旗标头后校验。
    绝对路径**允许写法**但必须落在仓库内——包含性是不变量，写法不是。
    """
    for token in argv:
        value = token.split("=", 1)[1] if token.startswith("--") and "=" in token else token
        if value.startswith("-") or "://" in value:
            continue
        if "/" not in value and "\\" not in value and not _DRIVE_RELATIVE.match(value):
            continue
        validate_rel_path(root, value, allow_absolute=True)


class Param:
    """动作参数：`kind` 决定交互（文本 / 路径 / 枚举），路径参数强制过包含性判据。"""

    __slots__ = ("name", "label", "kind", "required")

    def __init__(self, name, label, kind="text", required=True):
        self.name, self.label, self.kind, self.required = name, label, kind, required


class Action:
    """一条可执行动作：固定动词模板 + 参数槽（菜单真源，不允许自由拼 shell）。"""

    __slots__ = ("key", "title", "argv", "params", "note")

    def __init__(self, key, title, argv, params=(), note=""):
        self.key, self.title, self.argv = key, title, argv
        self.params, self.note = tuple(params), note

    def build(self, root, values) -> list:
        argv = []
        for token in self.argv:
            filled = token
            for param in self.params:
                if "{%s}" % param.name not in filled:
                    continue
                raw = str(values.get(param.name) or "")
                if not raw.strip():
                    if param.required:
                        raise UsageError("参数 %s 未填" % param.label, "回车确认前先填这一项")
                    filled = ""
                    break
                if param.kind == "path":
                    raw = os.path.relpath(validate_rel_path(root, raw), root).replace("\\", "/")
                filled = filled.replace("{%s}" % param.name, raw)
            if filled:
                argv.append(filled)
        return argv


#: 能力区（对齐 `core/terminal.py::ZONES` 的八区口径）+ 每区的动作（命令真源：scripts/nf.py）
ZONES = (
    ("环境自检", (Action("doctor", "只读体检", ["doctor"]),
                 Action("doctor-json", "体检（机器面）", ["doctor", "--json"]))),
    ("一键演示", (Action("demo", "跑一遍 P04 全链", ["demo"]),)),
    ("需求→装配", (
        Action("assemble", "一句话→装配计划", ["assemble", "{need}"],
               (Param("need", "需求（一句话）"),), note="产出装配计划文本，不落盘"),
        Action("assemble-check", "校验成品文档", ["assemble", "{file}", "--check"],
               (Param("file", "成品 .md（仓内路径）", "path"),)),
    )),
    ("全链生产", (
        Action("run", "跑全链管线", ["run", "--pipeline", "{pipeline}", "--modules", "{modules}", "--seed"],
               (Param("pipeline", "管线 .md（仓内路径）", "path"), Param("modules", "模块 full_id（逗号分隔）"))),
        Action("run-check", "管线 dry-run", ["pipeline", "dryrun", "{pipeline}"],
               (Param("pipeline", "管线 .md（仓内路径）", "path"),)),
    )),
    ("校验体检", (
        Action("conformance", "契约一致性", ["conformance"]),
        Action("layers", "抽象阶梯核验", ["layers", "--verify"]),
        Action("lint", "文档语义体检", ["lint", "{file}"], (Param("file", "文档 .md（仓内路径）", "path"),)),
        Action("module-verify", "模块门禁", ["module", "verify"]),
    )),
    ("货架资产", (
        Action("market", "市场货架", ["market", "--list"]),
        Action("asset-ls", "资产清单", ["asset", "ls"]),
        Action("asset-density", "资产密度", ["asset", "density"]),
        Action("library-search", "馆藏检索", ["library", "search", "{query}"], (Param("query", "关键词"),)),
    )),
    ("管线模块", (
        Action("module-ls", "模块清单", ["module", "ls"]),
        Action("patterns-ls", "模式清单", ["patterns", "ls"]),
        Action("stats", "自述数字核对", ["stats", "--check"]),
        Action("stats-write", "自述数字：重写生成区（写盘）", ["stats", "--write"],
               note="会改仓库文件，须键入 yes 确认"),
    )),
    ("帮助命令面", (
        Action("help", "命令总览", ["--help"]),
        Action("help-cmd", "看某命令帮助", ["help", "{cmd}"], (Param("cmd", "子命令名"),)),
    )),
)


def all_actions():
    for zone_no, (title, actions) in enumerate(ZONES):
        for action in actions:
            yield zone_no, title, action


# --------------------------------------------------------------------------- #
# 环境发现：仓库根 / 可用 Python / 配置文件（都在仓库外）
# --------------------------------------------------------------------------- #
def find_repo_root(start: Path | None = None) -> Path | None:
    """从候选起点逐层向上找同时含 `verify.sh` 与 `scripts/nf.py` 的目录。"""
    seeds = []
    env_root = os.environ.get("NF_ROOT")
    if env_root:
        seeds.append(Path(env_root))
    if start is not None:
        seeds.append(Path(start))
    seeds.extend([Path.cwd(), Path(__file__).resolve().parent])
    if getattr(sys, "frozen", False):
        seeds.append(Path(sys.executable).resolve().parent)
    seen = set()
    for seed in seeds:
        try:
            here = seed.resolve()
        except OSError:
            continue
        for _ in range(_ROOT_SEARCH_DEPTH):
            if here in seen:
                break
            seen.add(here)
            if all((here / marker).exists() for marker in _ROOT_MARKERS):
                return here
            if here.parent == here:
                break
            here = here.parent
    return None


def find_python() -> str | None:
    """找一个能跑 CLI 的解释器（冻结成 exe 时 sys.executable 是自己，不能用）。"""
    if not getattr(sys, "frozen", False):
        return sys.executable
    for name in ("python", "python3", "py"):
        found = _which(name)
        if found:
            return found
    return None


def _which(name: str) -> str | None:
    """PATH 查找（不 import shutil 以外的东西；Windows 上补 .exe 后缀）。"""
    import shutil
    return shutil.which(name)


def cli_prefix(root: Path, python: str | None) -> list:
    """拼出调用真命令面的 argv 前缀，并断言落点仍在仓库内。"""
    script = root / "scripts" / "nf.py"
    if python:
        if not contained(str(root), str(script)):
            raise RefusedError("CLI 落点逃逸仓库：%s" % script, "检查 NF_ROOT")
        return [python, str(script)]
    launcher = root / "scripts" / "nf.cmd" if os.name == "nt" else root / "scripts" / "nf"
    if launcher.exists():
        return [str(launcher)]
    raise EnvError("找不到可用的 nf 启动器", "安装 Python 后重试，或用 `nf` CLI 直跑")


CREDENTIAL_ENV = ("NF_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY")

#: 找不到仓库时的统一指引（`--json` / 非交互 / 全屏演示模式三处共用同一份文案）
NO_REPO_MSG = (
    "未发现 NarrativeForge 仓库（需要 verify.sh 与 scripts/nf.py 同时在场）。\n"
    "  修复指引：在仓库内运行，或用 --root <目录> / 环境变量 NF_ROOT 指定；\n"
    "            `--demo` / `--selftest` / `--list-actions` 不需要仓库，可直接跑。"
)


def load_api_key(env=None) -> str:
    """读 API 密钥：环境变量优先，其次**仓外**凭据文件；缺失回空串。

    设计要点：① 源码零硬编码；② 只读不写；③ 返回值只准进 `mask_secret`。
    凭据文件路径：`~/.config/nf/credentials`（POSIX）或 `%APPDATA%\\nf\\credentials`。
    """
    environ = os.environ if env is None else env
    for name in CREDENTIAL_ENV:
        if environ.get(name):
            return environ[name]
    path = credentials_path()
    if path and path.is_file():
        try:
            for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                if key.strip() in CREDENTIAL_ENV:
                    return value.strip().strip("\"'")
        except OSError as exc:                                  # noqa: BLE001 - 读不到就当作没有
            raise EnvError("凭据文件不可读：%s" % exc, "检查文件权限，或改用环境变量") from exc
    return ""


def credentials_path() -> Path | None:
    base = os.environ.get("APPDATA") if os.name == "nt" else os.environ.get("XDG_CONFIG_HOME")
    if base:
        return Path(base) / "nf" / "credentials"
    home = os.path.expanduser("~")
    if not home or home == "~":
        return None
    return Path(home) / ".config" / "nf" / "credentials"


# --------------------------------------------------------------------------- #
# 受控执行器：argv 列表 + 无 shell + 超时 + 输出限额
# --------------------------------------------------------------------------- #
class Result:
    __slots__ = ("argv", "code", "out", "err", "seconds", "cancelled")

    def __init__(self, argv, code, out, err, seconds, cancelled=False):
        self.argv, self.code, self.out, self.err, self.seconds = argv, code, out, err, seconds
        self.cancelled = cancelled


class Runner:
    """把 argv 交给系统执行——**没有 shell 这一层**。"""

    def __init__(self, root: Path, python: str | None, timeout: float = 120.0, max_lines: int = 400):
        self.root = root
        self.prefix = cli_prefix(root, python)
        self.timeout = timeout
        self.max_lines = max_lines

    def env(self) -> dict:
        env = dict(os.environ)
        # 冻结 exe 里子进程不继承我们的临时解包目录，避免干扰
        env.pop("_MEIPASS2", None)
        env["PYTHONIOENCODING"] = "utf-8"
        env["NF_TUI"] = "1"
        # 只读调用不该顺手拉起后台守护（那是写侧副作用）
        env["NF_AUTOSTART"] = "0"
        return env

    def run(self, argv: list, cancel=None) -> Result:
        """跑一条命令；`cancel`（threading.Event）置位即终止子进程（边跑可边取消）。"""
        cmd = list(self.prefix) + list(argv)
        started = time.time()
        kwargs = {}
        if os.name == "nt":
            kwargs["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        try:
            proc = subprocess.Popen(cmd, cwd=str(self.root), stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE, stdin=subprocess.DEVNULL,
                                    text=True, encoding="utf-8", errors="replace",
                                    env=self.env(), **kwargs)
        except OSError as exc:
            raise EnvError("无法启动命令：%s" % exc, "检查 Python 与仓库路径") from exc
        deadline, cancelled, out, err = started + self.timeout, False, "", ""
        while True:
            try:
                out, err = proc.communicate(timeout=0.2)
                break
            except subprocess.TimeoutExpired:
                if cancel is not None and cancel.is_set() and not cancelled:
                    cancelled = True
                    _terminate(proc)
                    continue
                if time.time() > deadline:
                    _terminate(proc)
                    try:
                        proc.communicate(timeout=3)
                    except subprocess.TimeoutExpired:
                        pass
                    raise NfTuiError("命令超时（%.0fs）：%s" % (self.timeout, " ".join(argv)),
                                     "缩小范围或改用更具体的子命令") from None
        seconds = time.time() - started
        return Result(argv, EXIT_INTERRUPT if cancelled else proc.returncode,
                      _clip_lines(out, self.max_lines), _clip_lines(err, self.max_lines),
                      seconds, cancelled)


def _terminate(proc) -> None:
    """先终止再兜底强杀（取消与超时共用；失败不抛——调用方还要读输出）。"""
    try:
        proc.terminate()
        proc.wait(timeout=2)
    except (OSError, subprocess.TimeoutExpired):
        try:
            proc.kill()
        except OSError:
            pass


def _clip_lines(text: str, limit: int) -> str:
    lines = (text or "").splitlines()
    if len(lines) <= limit:
        return text or ""
    kept = lines[:limit]
    kept.append("…（输出过长，已截断 %d 行；完整输出请用 `nf` CLI 直跑）" % (len(lines) - limit))
    return "\n".join(kept)


def dispatch(root, python, argv: list, *, confirmed: bool = False, timeout: float = 120.0,
             cancel=None) -> Result:
    """执行前统一过闸门：白名单 → 长驻 → 写盘确认 → 密钥形态参数。"""
    if not argv:
        raise UsageError("空命令", "给出一个 nf 子命令")
    if argv[0] not in KNOWN_TOP and not argv[0].startswith("-"):
        raise UsageError("未知子命令：%s" % argv[0], "用 `nf help` 看命令面，或在菜单里选动作")
    mode = classify(argv)
    if mode == "long":
        raise RefusedError("长驻命令不在 TUI 内运行：%s" % argv[0],
                           "请在普通终端里直接运行 `nf %s …`" % argv[0])
    if mode == "write" and not confirmed:
        raise RefusedError("写盘命令需显式确认：%s" % " ".join(argv),
                           "确认会改仓库后，在详情栏键入 yes 再执行")
    for tok in argv:
        if _SECRET_RE.search(tok):
            raise RefusedError("参数疑似密钥，拒绝把凭据写进命令行",
                               "凭据请放环境变量 %s，不要放进参数" % "/".join(CREDENTIAL_ENV))
    guard_path_tokens(root, argv)
    return Runner(root, python, timeout=timeout).run(argv, cancel=cancel)


# --------------------------------------------------------------------------- #
# 渲染：纯函数（同一状态两次渲染逐字一致——`--demo` 与 `--selftest` 共用）
# --------------------------------------------------------------------------- #
def char_width(ch: str) -> int:
    if unicodedata.combining(ch):
        return 0
    return 2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1


def display_width(text: str) -> int:
    return sum(char_width(ch) for ch in str(text))


def clip(text: str, width: int) -> str:
    out, used = [], 0
    for ch in str(text):
        step = char_width(ch)
        if used + step > width:
            break
        out.append(ch)
        used += step
    return "".join(out)


def pad_to(text: str, width: int) -> str:
    body = clip(text, width)
    return body + " " * max(0, width - display_width(body))


# --------------------------------------------------------------------------- #
# 交互：焦点模型（对标 lazygit / k9s / yazi 的公开键位约定）
#   Tab / ←→ / h l 切面板；↑↓ 或 j k 只在**当前**面板内移动；
#   / 过滤当前面板（输出面板为检索）；? 开键位帮助；Esc 取消/清除；q 或 Ctrl-C 退出。
#   键处理是**纯状态机**（不进 IO），因此交互本身可离线回归。
# --------------------------------------------------------------------------- #
FOCUS_ZONES, FOCUS_ACTIONS, FOCUS_OUTPUT = 0, 1, 2
FOCUS_LABELS = ("能力区", "动作", "输出")
#: 写盘确认词（与 `core/terminal.py` 的 YES_WORDS 同口径）
YES_WORDS = ("y", "yes", "ok", "是", "确认", "可以")
#: 运行中转轮（纯文本，零依赖）
SPINNER = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"


class Prompt:
    """底部模态输入（**带光标**）：参数填写 / 过滤 / 输出检索 / 写盘确认四态共用。"""

    __slots__ = ("kind", "label", "buf", "cursor")

    def __init__(self, kind: str, label: str, buf: str = ""):
        self.kind, self.label = kind, label
        self.buf, self.cursor = buf, len(buf)

    def insert(self, text: str) -> None:
        self.buf = self.buf[:self.cursor] + text + self.buf[self.cursor:]
        self.cursor += len(text)

    def render(self) -> str:
        return "%s▏%s" % (self.buf[:self.cursor], self.buf[self.cursor:])


class Ui:
    """全屏会话状态（纯数据）：键处理改它、渲染是它的投影。"""

    def __init__(self, root=None, repo: str = "", demo: bool = False, notice: str = "就绪"):
        self.root = root
        self.repo = repo
        self.demo = demo
        self.focus = FOCUS_ZONES
        self.zpos = 0          # 能力区视图内的位置
        self.ztop = 0          # 能力区滚动偏移
        self.zone_filter = ""
        self.apos = 0          # 动作视图内的位置
        self.atop = 0
        self.action_filter = ""
        self.out = []          # 输出行
        self.otop = 0          # 输出滚动偏移
        self.follow = True     # 输出是否跟随末尾
        self.search = ""
        self.search_hit = -1
        self.prompt = None
        self.help = False
        self.notice = notice
        self.notice_kind = "info"
        self.running = None
        self.last_argv = None
        self.params = None
        self.size = (100, 30)


def layout_of(width, height, action_count=None) -> dict:
    """按终端尺寸算出的面板几何（键处理与渲染共用，避免两处各算一套）。

    `action_count` 给了就让动作面板**按内容收缩**（动作少时输出面板自动变高）。
    """
    w = max(76, min(int(width), 200))
    h = max(20, int(height))
    split = min(34, max(24, w // 4))
    body = max(8, h - 6)
    desired = (body - 1) // 2 if action_count is None else int(action_count) + 1
    actions = max(4, min(desired, body - 4))
    output = body - actions - 1
    return {"w": w, "h": h, "split": split, "body": body,
            "actions": actions, "output": output,
            "left_items": body - 1, "action_items": actions - 1, "output_items": output - 1}


def _match(term: str, *hay) -> bool:
    needle = (term or "").strip().lower()
    return not needle or any(needle in str(h).lower() for h in hay)


def zones_view(ui: Ui) -> list:
    return [(i, title, len(acts)) for i, (title, acts) in enumerate(ZONES)
            if _match(ui.zone_filter, title)]


def actions_view(ui: Ui) -> list:
    zones = zones_view(ui)
    if not zones:
        return []
    zone_index = zones[min(ui.zpos, len(zones) - 1)][0]
    return [(i, act) for i, act in enumerate(ZONES[zone_index][1])
            if _match(ui.action_filter, act.title, " ".join(act.argv), act.note)]


def cur_zone(ui: Ui):
    zones = zones_view(ui)
    return zones[min(ui.zpos, len(zones) - 1)] if zones else None


def cur_action(ui: Ui):
    acts = actions_view(ui)
    return acts[min(ui.apos, len(acts) - 1)][1] if acts else None


def _keep_visible(top: int, pos: int, visible: int) -> int:
    """让 pos 落在 [top, top+visible) 内。"""
    if visible <= 0:
        return 0
    if pos < top:
        return pos
    if pos >= top + visible:
        return pos - visible + 1
    return top


def clamp_ui(ui: Ui, lay: dict) -> None:
    """过滤/切换之后把指针与滚动收回合法范围（渲染前必调）。"""
    zones = zones_view(ui)
    ui.zpos = min(max(ui.zpos, 0), max(0, len(zones) - 1))
    ui.ztop = _keep_visible(ui.ztop, ui.zpos, lay["left_items"])
    if not zones:
        ui.ztop = 0
    actions = actions_view(ui)
    ui.apos = min(max(ui.apos, 0), max(0, len(actions) - 1))
    ui.atop = _keep_visible(ui.atop, ui.apos, lay["action_items"])
    if not actions:
        ui.atop = 0


def _max_otop(ui: Ui, lay: dict) -> int:
    return max(0, len(ui.out) - lay["output_items"])


def scroll_output(ui: Ui, delta: int, lay: dict) -> None:
    top = min(max(0, ui.otop + delta), _max_otop(ui, lay))
    ui.otop = top
    ui.follow = top >= _max_otop(ui, lay)


def set_output(ui: Ui, lines: list) -> None:
    ui.out = list(lines or [])
    ui.follow = True


def move_focus(ui: Ui, delta: int) -> None:
    ui.focus = (ui.focus + delta) % 3


def move_selection(ui: Ui, delta: int, lay: dict) -> None:
    """↑↓/jk：只在当前面板内移动（能力区/动作改变选择，输出面板滚动）。"""
    if ui.focus == FOCUS_ZONES:
        zones = zones_view(ui)
        if not zones:
            return
        ui.zpos = (ui.zpos + delta) % len(zones)
        ui.ztop = _keep_visible(ui.ztop, ui.zpos, lay["left_items"])
        ui.apos, ui.atop = 0, 0
    elif ui.focus == FOCUS_ACTIONS:
        actions = actions_view(ui)
        if not actions:
            return
        ui.apos = (ui.apos + delta) % len(actions)
        ui.atop = _keep_visible(ui.atop, ui.apos, lay["action_items"])
    else:
        scroll_output(ui, delta, lay)


def _begin_params(ui: Ui) -> tuple:
    """进入参数逐项追问；无参数则直接推进到执行。返回 `(op, payload)`。"""
    action = cur_action(ui)
    if action is None:
        return ("none", "当前过滤下没有动作")
    ui.params = {"action": action, "queue": list(action.params), "values": {}}
    notice = _next_param(ui)
    if ui.prompt is not None:
        return ("none", notice)
    return _finish_params(ui)


def _next_param(ui: Ui) -> str:
    data = ui.params
    if not data:
        return ""
    while data["queue"]:
        param = data["queue"][0]
        if param.required:
            hint = "（仓内路径）" if param.kind == "path" else ""
            ui.prompt = Prompt("param", "%s%s" % (param.label, hint))
            return "填参数：%s" % param.label
        data["queue"].pop(0)           # 可选参数跳过
    return ""


def _finish_params(ui: Ui) -> tuple:
    """参数收齐 → 建 argv → 过写盘闸门。"""
    data, ui.params = ui.params, None
    action = data["action"]
    try:
        argv = action.build(str(ui.root), data["values"])
    except NfTuiError as exc:
        ui.notice, ui.notice_kind = exc.message, "err"
        return ("none", None)
    return _request_run(ui, argv)


def _request_run(ui: Ui, argv: list) -> tuple:
    """执行前统一过闸门：写盘类必须二次确认（CLI 自己的 --yes 仍是第二层）。"""
    if classify(argv) == "write":
        ui.params = {"action": None, "queue": [], "values": {},
                     "pending": argv, "confirm": True}
        ui.prompt = Prompt("confirm-write", "写盘确认：%s" % " ".join(argv))
        return ("none", "写盘命令需确认（键入 yes）")
    return ("run", {"argv": argv, "confirmed": False})


def _prompt_key(ui: Ui, key: str) -> tuple:
    prompt = ui.prompt
    if key == "ESC":
        ui.prompt, ui.params = None, None
        return ("none", "已取消输入")
    if key == "ENTER":
        text, kind = prompt.buf, prompt.kind
        ui.prompt = None
        return _apply_prompt(ui, kind, text)
    if key == "BACKSPACE":
        if prompt.cursor > 0:
            prompt.buf = prompt.buf[:prompt.cursor - 1] + prompt.buf[prompt.cursor:]
            prompt.cursor -= 1
    elif key == "DELETE":
        prompt.buf = prompt.buf[:prompt.cursor] + prompt.buf[prompt.cursor + 1:]
    elif key == "LEFT":
        prompt.cursor = max(0, prompt.cursor - 1)
    elif key == "RIGHT":
        prompt.cursor = min(len(prompt.buf), prompt.cursor + 1)
    elif key == "HOME":
        prompt.cursor = 0
    elif key == "END":
        prompt.cursor = len(prompt.buf)
    elif key == "CTRLU":
        prompt.buf, prompt.cursor = "", 0
    elif len(key) == 1 and key >= " ":
        prompt.insert(key)
    return ("none", None)


def _apply_prompt(ui: Ui, kind: str, text: str) -> tuple:
    text = text.strip()
    if kind == "filter-zones":
        ui.zone_filter, ui.zpos, ui.ztop, ui.focus = text, 0, 0, FOCUS_ZONES
        return ("none", "能力区过滤：%s" % (text or "（已清除）"))
    if kind == "filter-actions":
        ui.action_filter, ui.apos, ui.atop, ui.focus = text, 0, 0, FOCUS_ACTIONS
        return ("none", "动作过滤：%s" % (text or "（已清除）"))
    if kind == "search-output":
        ui.search, ui.search_hit = text, -1
        return _search_step(ui, +1) if text else ("none", "已清除检索")
    if kind == "param":
        data = ui.params
        if data:
            data["values"][data["queue"][0].name] = text
            data["queue"].pop(0)
            notice = _next_param(ui)
            if ui.prompt is None:
                return _finish_params(ui)
            return ("none", notice)
        return ("none", None)
    if kind == "confirm-write":
        data, ui.params = ui.params or {}, None
        if text.lower() not in YES_WORDS:
            return ("none", "已取消（写盘未确认）")
        return ("run", {"argv": data.get("pending") or [], "confirmed": True})
    return ("none", None)


def _search_step(ui: Ui, direction: int) -> tuple:
    if not ui.search or not ui.out:
        return ("none", None)
    needle = ui.search.lower()
    total = len(ui.out)
    start = ui.search_hit + direction if ui.search_hit >= 0 else (0 if direction > 0 else total - 1)
    order = (list(range(start, total)) + list(range(0, start))) if direction > 0 else \
            (list(range(start, -1, -1)) + list(range(total - 1, start, -1)))
    for i in order:
        if needle in ui.out[i].lower():
            ui.search_hit = i
            lay = layout_of(*ui.size)
            ui.otop = _keep_visible(ui.otop, i, lay["output_items"])
            ui.follow = ui.otop >= _max_otop(ui, lay)
            return ("none", "命中第 %d/%d 行：%s" % (i + 1, total, ui.out[i][:40]))
    return ("none", "未命中：%s" % ui.search)


def handle_key(ui: Ui, key: str, lay: dict) -> tuple:
    """键 → 状态变化 + 请求。返回 `(op, payload)`：op ∈ none/quit/run/cancel。"""
    if ui.prompt is not None:
        return _prompt_key(ui, key)
    if ui.help:
        ui.help = False
        return ("none", None)
    if ui.running is not None:
        if key in ("CTRLC", "ESC"):
            return ("cancel", None)
        return ("none", "运行中… Ctrl-C 取消")
    if key in ("q", "Q"):
        return ("quit", None)
    if key == "?":
        ui.help = True
        return ("none", "键位帮助：按任意键关闭")
    if key in ("TAB", "RIGHT", "l"):
        move_focus(ui, +1)
        return ("none", "焦点：%s" % FOCUS_LABELS[ui.focus])
    if key in ("LEFT", "h"):
        move_focus(ui, -1)
        return ("none", "焦点：%s" % FOCUS_LABELS[ui.focus])
    if key in ("UP", "k"):
        move_selection(ui, -1, lay)
        return ("none", None)
    if key in ("DOWN", "j"):
        move_selection(ui, +1, lay)
        return ("none", None)
    if key in ("PGUP", "CTRLU"):
        scroll_output(ui, -lay["output_items"], lay)
        return ("none", "输出：向上翻页")
    if key in ("PGDN", "CTRLD"):
        scroll_output(ui, +lay["output_items"], lay)
        return ("none", "输出：向下翻页")
    if key in ("HOME", "g"):
        scroll_output(ui, -len(ui.out), lay)
        return ("none", "输出：顶部")
    if key in ("END", "G"):
        scroll_output(ui, len(ui.out), lay)
        return ("none", "输出：末尾")
    if key == "/":
        if ui.focus == FOCUS_OUTPUT:
            ui.prompt = Prompt("search-output", "检索输出", ui.search)
            return ("none", "输入检索词（Enter 确认 · Esc 取消）")
        kind = "filter-zones" if ui.focus == FOCUS_ZONES else "filter-actions"
        current = ui.zone_filter if ui.focus == FOCUS_ZONES else ui.action_filter
        ui.prompt = Prompt(kind, "过滤%s" % FOCUS_LABELS[ui.focus], current)
        return ("none", "输入过滤词（Enter 确认 · Esc 取消）")
    if key == "ESC":
        ui.zone_filter = ui.action_filter = ""
        clamp_ui(ui, lay)
        return ("none", "已清除过滤")
    if key in ("n", "N"):
        return _search_step(ui, +1 if key == "n" else -1)
    if key == "R":
        if not ui.last_argv:
            return ("none", "还没有可重跑的命令")
        return _request_run(ui, list(ui.last_argv))
    if key == "ENTER":
        if ui.focus == FOCUS_ZONES:
            move_focus(ui, +1)
            return ("none", "焦点：%s" % FOCUS_LABELS[ui.focus])
        if ui.focus == FOCUS_OUTPUT:
            return ("none", "输出面板：PgUp/PgDn 滚动 · / 检索 · Home/End 到顶/底")
        if ui.root is None or ui.demo:
            set_output(ui, NO_REPO_MSG.splitlines())
            ui.notice, ui.notice_kind = "演示模式：未发现仓库，动作不执行", "err"
            return ("none", None)
        return _begin_params(ui)
    return ("none", None)


def _pane_title(text: str, focused: bool) -> tuple:
    return (("▍ " if focused else "  ") + text, "accent" if focused else "title")


def _rows_of(items: list, top: int, height: int) -> list:
    window = items[top:top + max(0, height)]
    return window + [("", "normal")] * (height - len(window))


def _pane_zones(ui: Ui, lay: dict) -> list:
    zones = zones_view(ui)
    ui.zpos = min(max(ui.zpos, 0), max(0, len(zones) - 1))
    ui.ztop = _keep_visible(ui.ztop, ui.zpos, lay["left_items"])
    title = _pane_title("能力区 %d/%d" % (ui.zpos + 1 if zones else 0, len(zones)),
                        ui.focus == FOCUS_ZONES)
    body = []
    for pos, (zone_index, text, count) in enumerate(zones[ui.ztop:ui.ztop + lay["left_items"]]):
        actual = ui.ztop + pos
        mark = "▸" if actual == ui.zpos else " "
        style = "normal"
        if actual == ui.zpos:
            style = "focus" if ui.focus == FOCUS_ZONES else "accent"
        body.append(("%s %d %s（%d）" % (mark, zone_index, text, count), style))
    return [title] + body + [("", "normal")] * (lay["left_items"] - len(body))


def _pane_actions(ui: Ui, lay: dict) -> list:
    zone = cur_zone(ui)
    actions = actions_view(ui)
    title = _pane_title("动作 · %s（%d）" % (zone[1] if zone else "-", len(actions)),
                        ui.focus == FOCUS_ACTIONS)
    body = []
    for pos, (_idx, act) in enumerate(actions[ui.atop:ui.atop + lay["action_items"]]):
        actual = ui.atop + pos
        if actual == ui.apos:
            style = "focus" if ui.focus == FOCUS_ACTIONS else "accent"
            body.append(("❯ %s   nf %s" % (act.title, " ".join(act.argv)), style))
        else:
            body.append(("  %s" % act.title, "normal"))
    return [title] + body + [("", "normal")] * (lay["action_items"] - len(body))


def _pane_output(ui: Ui, lay: dict) -> list:
    total = len(ui.out)
    if ui.follow:
        ui.otop = _max_otop(ui, lay)
    ui.otop = min(max(0, ui.otop), _max_otop(ui, lay))
    span = "%d-%d/%d" % (ui.otop + 1, min(total, ui.otop + lay["output_items"]), total) if total else "空"
    mark = "已跟随" if ui.follow else "已暂停(End 回末尾)"
    title = _pane_title("输出 · %s · %s" % (span, mark), ui.focus == FOCUS_OUTPUT)
    body = [(line, "normal") for line in ui.out[ui.otop:ui.otop + lay["output_items"]]]
    return [title] + body + [("", "normal")] * (lay["output_items"] - len(body))


def _footer(ui: Ui) -> tuple:
    if ui.prompt is not None:
        return (" %s ▸ %s   （Enter 确认 · Esc 取消）" % (ui.prompt.label, ui.prompt.render()),
                "prompt")
    if ui.running is not None:
        spin = SPINNER[int((time.time() - ui.running.started) * 10) % len(SPINNER)]
        return (" %s 运行中  nf %s   %.1fs   Ctrl-C 取消"
                % (spin, " ".join(ui.running.argv), time.time() - ui.running.started), "accent")
    keys = (" Tab 切面板 · ↑↓ 移动 · / 过滤 · Enter 运行 · ? 帮助 · q 退出 "
            if ui.focus != FOCUS_OUTPUT else
            " Tab 切面板 · ↑↓/PgUp/PgDn 滚动 · / 检索 · n 下一个 · q 退出 ")
    return (keys, "footer")


def _help_rows(inner: int, body: int) -> list:
    entries = [
        ("Tab / ←→ / h l", "切换面板（能力区 / 动作 / 输出）"),
        ("↑↓ 或 j k", "在当前面板内移动选择（输出面板为滚动）"),
        ("Enter", "运行选中动作；缺参数时逐项追问"),
        ("/", "过滤当前面板（输出面板为检索输出）"),
        ("n / N", "跳转到下一个 / 上一个检索命中"),
        ("PgUp PgDn Ctrl-U Ctrl-D", "输出翻页；Home/End 或 g/G 到顶/底"),
        ("R", "重跑上一条命令（写盘类仍需确认）"),
        ("Esc", "关闭浮层 / 取消输入 / 清除过滤"),
        ("? ", "打开本帮助（任意键关闭）"),
        ("q / Ctrl-C", "退出（命令运行中时 Ctrl-C 只取消该命令）"),
    ]
    rows = [(_pane_title("键位帮助（任意键关闭）", True)[0], "title")]
    for key, desc in entries:
        if len(rows) >= body:
            break
        rows.append((" %-26s %s" % (key, desc), "normal"))
    rows.append(("", "normal"))
    rows.append((" 安全底线：无 shell 执行 · 路径包含性判据 · 写盘需键入 yes · 密钥只读环境变量且遮蔽", "dim"))
    return rows + [("", "normal")] * (body - len(rows))


def render_lines(ui: Ui, width=100, height=30) -> list:
    """UI 状态 → `[(文本, 样式)]`。同状态两遍渲染逐字一致（确定性面）。"""
    lay = layout_of(width, height, len(actions_view(ui)))
    w, h, split = lay["w"], lay["h"], lay["split"]
    clamp_ui(ui, lay)
    rows = []
    head = " NF TUI v%s · NarrativeForge 内容契约层 " % VERSION
    rows.append(("┌%s┐" % (head + "─" * max(0, w - 2 - display_width(head))), "frame"))
    scope = ui.zone_filter or ui.action_filter
    left = "%s · 能力区 %d" % (("仓库 %s" % ui.repo) if ui.repo else "未发现仓库（演示模式）",
                              len(ZONES))
    if scope:
        left += " · 过滤「%s」" % scope
    right = "焦点 %s · %s" % (FOCUS_LABELS[ui.focus], ui.notice)
    gap = max(1, w - 2 - display_width(left) - display_width(right))
    rows.append(("│%s%s%s│" % (left, " " * gap, clip(right, max(0, w - 2 - display_width(left) - 1))),
                 "title" if ui.notice_kind != "err" else "err"))
    rows.append(("├" + "─" * split + "┬" + "─" * (w - split - 3) + "┤", "frame"))

    if ui.help:
        pane = _help_rows(w - 2, lay["body"])
        for text, style in pane[:lay["body"]]:
            rows.append(("│%s│" % pad_to(text, w - 2), style))
    else:
        left_pane = _pane_zones(ui, lay)
        act_pane = _pane_actions(ui, lay)
        out_pane = _pane_output(ui, lay)
        for i in range(lay["body"]):
            lcell = left_pane[i] if i < len(left_pane) else ("", "normal")
            if i < lay["actions"]:
                rcell = act_pane[i] if i < len(act_pane) else ("", "normal")
                rows.append(("│%s│%s│" % (pad_to(lcell[0], split), pad_to(rcell[0], w - split - 3)),
                             rcell[1]))
            elif i == lay["actions"]:
                rows.append(("│%s├%s┤" % (pad_to(lcell[0], split), "─" * (w - split - 3)),
                             lcell[1]))
            else:
                j = i - lay["actions"] - 1
                rcell = out_pane[j] if j < len(out_pane) else ("", "normal")
                rows.append(("│%s│%s│" % (pad_to(lcell[0], split), pad_to(rcell[0], w - split - 3)),
                             rcell[1]))
    rows.append(("├" + "─" * split + "┴" + "─" * (w - split - 3) + "┤", "frame"))
    text, style = _footer(ui)
    rows.append(("│%s│" % pad_to(text, w - 2), style))
    rows.append(("└%s┘" % ("─" * (w - 2)), "frame"))
    return rows[:h]


def render_frame(ui: Ui, width=100, height=30) -> list:
    """确定性纯文本面（无 ANSI）：`--demo`、README 演示帧与回归判据共用。"""
    return [text for text, _style in render_lines(ui, width, height)]


#: 终端着色（仅 TTY 且未 `--no-color` 时启用；重定向输出永不带 ANSI）
_STYLES = {"normal": "", "dim": "\x1b[2m", "title": "\x1b[36m", "accent": "\x1b[1;36m",
           "focus": "\x1b[1;33m", "ok": "\x1b[32m", "err": "\x1b[31m",
           "frame": "\x1b[90m", "footer": "\x1b[2m", "prompt": "\x1b[1;35m"}
_RESET = "\x1b[0m"


def paint(rows: list, *, enabled: bool) -> str:
    if not enabled:
        return "\n".join(text for text, _style in rows)
    return "\n".join("%s%s%s" % (_STYLES.get(style, ""), text, _RESET) for text, style in rows)


# --------------------------------------------------------------------------- #
# 终端驱动：VT 开启 / 键盘读取 / 全屏会话 / 逐行回退
# --------------------------------------------------------------------------- #
def enable_vt() -> bool:
    """Windows 上打开 ANSI 处理；其他平台返回 True（POSIX 终端原生支持）。"""
    if os.name != "nt":
        return True
    try:
        import ctypes

        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(-11)
        mode = ctypes.c_uint32()
        if not kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
            return False
        return bool(kernel32.SetConsoleMode(handle, mode.value | 0x0004))
    except Exception:                                            # noqa: BLE001 - 老控制台无此能力
        return False


#: 键名归一化表（Windows 扫描码 / POSIX ESC 序列共用一套名字）
_WIN_ARROWS = {"H": "UP", "P": "DOWN", "K": "LEFT", "M": "RIGHT", "I": "PGUP",
               "Q": "PGDN", "G": "HOME", "O": "END", "S": "DELETE"}
_POSIX_SEQS = {"[A": "UP", "[B": "DOWN", "[C": "RIGHT", "[D": "LEFT",
               "[5~": "PGUP", "[6~": "PGDN", "[H": "HOME", "[F": "END",
               "[1~": "HOME", "[4~": "END", "[3~": "DELETE"}
_SIMPLE_KEYS = {"\r": "ENTER", "\n": "ENTER", "\t": "TAB", "\x1b": "ESC",
                "\x03": "CTRLC", "\x15": "CTRLU", "\x04": "CTRLD",
                "\x7f": "BACKSPACE", "\x08": "BACKSPACE"}


def read_key() -> str:
    """读一个键 → 归一化名（方向/翻页/Home/End/Delete/控制键/字面字符）。"""
    if os.name == "nt":
        import msvcrt
        ch = msvcrt.getwch()
        if ch in ("\x00", "\xe0"):
            return _WIN_ARROWS.get(msvcrt.getwch(), "")
        return _SIMPLE_KEYS.get(ch, ch)
    import select
    import termios
    import tty
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
        if ch == "\x1b":
            seq = ""
            while len(seq) < 4 and select.select([sys.stdin], [], [], 0.05)[0]:
                nxt = sys.stdin.read(1)
                seq += nxt
                if nxt.isalpha() or nxt == "~":
                    break
            return _POSIX_SEQS.get(seq, "ESC")
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
    return _SIMPLE_KEYS.get(ch, ch)


def read_key_timeout(timeout: float):
    """带超时读键（运行中刷新转轮/收结果）；超时返回 None。"""
    if os.name == "nt":
        import msvcrt
        deadline = time.time() + timeout
        while time.time() < deadline:
            if msvcrt.kbhit():
                return read_key()
            time.sleep(0.02)
        return None
    import select
    ready, _w, _x = select.select([sys.stdin], [], [], timeout)
    return read_key() if ready else None


def _terminal_size() -> tuple:
    import shutil
    size = shutil.get_terminal_size((100, 30))
    return max(76, size.columns), max(20, size.lines)


class Running:
    """一次在跑的调用（工作线程 + 取消令牌 + 结果队列）。"""

    __slots__ = ("argv", "started", "cancel", "queue", "thread")

    def __init__(self, argv, cancel, q, thread):
        self.argv, self.cancel, self.queue, self.thread = argv, cancel, q, thread
        self.started = time.time()


def start_run(ui: Ui, python, argv: list, confirmed: bool) -> None:
    """命令丢到工作线程：主循环继续重绘，Ctrl-C 只取消这条命令（对标 lazygit/k9s）。"""
    cancel, q, argv = threading.Event(), queue.Queue(), list(argv)

    def work():
        try:
            q.put(("done", dispatch(ui.root, python, argv, confirmed=confirmed, cancel=cancel)))
        except NfTuiError as exc:
            q.put(("error", exc))
        except Exception as exc:                                  # noqa: BLE001 - 线程异常必须回传
            q.put(("error", EnvError("命令执行异常：%s" % exc, "用 `nf` CLI 直跑可看完整栈")))

    thread = threading.Thread(target=work, daemon=True)
    thread.start()
    ui.running = Running(argv, cancel, q, thread)
    ui.last_argv = argv


def poll_run(ui: Ui) -> None:
    """收工作线程结果（非阻塞）：落输出、给通知、清运行态。"""
    if ui.running is None:
        return
    try:
        kind, payload = ui.running.queue.get_nowait()
    except queue.Empty:
        return
    if kind == "error":
        set_output(ui, payload.render().splitlines())
        ui.notice, ui.notice_kind = payload.message, "err"
    else:
        set_output(ui, _result_lines(payload.argv, payload))
        tag = " · 已取消" if payload.cancelled else ""
        ui.notice = "完成：退出码 %d · %.2fs%s" % (payload.code, payload.seconds, tag)
        ui.notice_kind = "ok" if payload.code == 0 and not payload.cancelled else "err"
    lay = layout_of(*ui.size)
    ui.otop = max(0, len(ui.out) - lay["output_items"])
    ui.follow = True
    ui.running = None


def cancel_run(ui: Ui) -> None:
    if ui.running is not None:
        ui.running.cancel.set()
        ui.notice, ui.notice_kind = "正在取消…", "err"


def run_fullscreen(ui: Ui, python, *, color: bool = True) -> int:
    """全屏主循环：重绘 → 带超时读键 → 改状态 / 收结果。Ctrl-C 只取消当前命令。"""
    out = sys.stdout
    out.write("\x1b[?1049h\x1b[?25l")
    out.flush()
    try:
        while True:
            ui.size = _terminal_size()
            out.write("\x1b[H\x1b[2J" + paint(render_lines(ui, *ui.size), enabled=color))
            out.flush()
            try:
                key = read_key_timeout(0.08 if ui.running is not None else 0.5)
            except KeyboardInterrupt:
                if ui.running is not None:
                    cancel_run(ui)
                    continue
                return EXIT_INTERRUPT
            if ui.running is not None:
                poll_run(ui)
            if key is None:
                continue
            op, payload = handle_key(ui, key,
                                     layout_of(*ui.size, len(actions_view(ui))))
            if op == "quit":
                return EXIT_OK
            if op == "cancel":
                cancel_run(ui)
                continue
            if op == "run":
                start_run(ui, python, payload["argv"], payload["confirmed"])
                ui.notice, ui.notice_kind = "运行中…", "info"
                continue
            if isinstance(payload, str) and payload:
                ui.notice, ui.notice_kind = payload, "info"
    finally:
        out.write("\x1b[?25h\x1b[?1049l")
        out.flush()


def _result_lines(argv: list, result: Result) -> list:
    head = "❯ nf %s   （退出码 %d · %.2fs）" % (" ".join(argv), result.code, result.seconds)
    body = (result.out or "").splitlines() or ["（无标准输出）"]
    if result.err:
        body += ["[stderr]"] + (result.err or "").splitlines()
    return [head] + body


def run_plain(root, python, *, exec_line: str = "") -> int:
    """逐行回退面（非 TTY / `--plain`）：可重定向、可进 CI。"""
    if exec_line:
        argv = split_argv(exec_line)
        if argv and argv[0] in ("nf", "nf.py"):
            argv = argv[1:]
        result = dispatch(root, python, argv)
        sys.stdout.write(result.out)
        if result.err:
            sys.stderr.write(result.err)
        return result.code
    out_lines = []
    while True:
        try:
            line = input("nf-tui> ")
        except (EOFError, KeyboardInterrupt):
            return EXIT_OK
        line = line.strip()
        if not line:
            continue
        if line in ("q", "quit", "exit", "退出"):
            return EXIT_OK
        try:
            argv = split_argv(line)
            if argv and argv[0] in ("nf", "nf.py"):
                argv = argv[1:]
            result = dispatch(root, python, argv)
            out_lines = _result_lines(argv, result)
            sys.stdout.write("\n".join(out_lines) + "\n")
        except NfTuiError as exc:
            sys.stderr.write(exc.render() + "\n")


# --------------------------------------------------------------------------- #
# 自检 / 演示 / 机器面
# --------------------------------------------------------------------------- #
def selftest(root: Path | None = None, python: str | None = None) -> tuple:
    """内建判据：安全底线逐条真跑。→ `(ok, rows)`，rows 每项 `(名字, 通过?, 说明)`。"""
    rows = []

    def check(name, fn):
        try:
            detail = fn()
            rows.append((name, True, detail))
        except Exception as exc:                                 # noqa: BLE001 - 自检要全跑完
            rows.append((name, False, "%s: %s" % (type(exc).__name__, exc)))

    tmp_root = str(root) if root else os.getcwd()

    def paths():
        for bad in ("../etc/passwd", "a/../../b", "C:foo", "/etc/passwd"):
            try:
                validate_rel_path(tmp_root, bad)
                raise AssertionError("未拦住：%s" % bad)
            except RefusedError:
                pass
        for bad in (["lint", "/etc/passwd"], ["lint", "../../x/y.md"], ["--pipeline=C:x.md"]):
            try:
                guard_path_tokens(tmp_root, bad)
                raise AssertionError("自由文本路径未拦住：%s" % bad)
            except RefusedError:
                pass
        guard_path_tokens(tmp_root, ["run", "--modules", "通用类:M00", "--fmt", "ccv3"])
        guard_path_tokens(tmp_root, ["lint", "docs/terminal.md"])
        good = validate_rel_path(tmp_root, os.path.join("docs", "terminal.md"))
        assert contained(tmp_root, good)
        return "越界写法全拦（含自由文本路径 token），根内相对路径放行"

    def no_shell():
        assert split_argv('doctor "a b" ; rm -rf /') == ["doctor", "a b", ";", "rm", "-rf", "/"]
        # 冻结态下 sys.executable 是本 exe，不能拿它当解释器跑探针
        probe_python = sys.executable if not getattr(sys, "frozen", False) else \
            (_which("python") or _which("python3"))
        if not probe_python:
            return "切分器判据通过；冻结态且 PATH 无 Python，跳过真进程证明"
        probe = [probe_python, "-c", "import sys;print(sys.argv[1])", "a;b|c&d"]
        proc = subprocess.run(probe, capture_output=True, text=True, encoding="utf-8",
                              errors="replace", timeout=30, shell=False)
        assert proc.stdout.strip() == "a;b|c&d", "元字符被解释：%r" % proc.stdout
        return "shell=False 真进程证明元字符原样传递；切分器不解析元字符"

    def whitelist():
        assert classify(["serve"]) == "long"
        assert classify(["daemon", "start", "--watch"]) == "long"
        assert classify(["stats", "--write"]) == "write"
        assert classify(["asset", "rm", "x"]) == "write"
        assert classify(["doctor"]) == "read"
        try:
            dispatch(tmp_root, python, ["definitely-not-a-command"])
            raise AssertionError("未知动词未被拦下")
        except UsageError:
            pass
        return "长驻拒跑 / 写盘定档 / 未知动词拦下"

    def secrets():
        masked = mask_secret("abcdefghijklmnop")
        assert "abcdefghijklmnop" not in masked and "*" in masked
        source = Path(__file__)
        if not source.is_file():                 # 冻结 exe：源码不在解包目录
            return "遮蔽生效：%s；冻结态跳过源件扫描（构建前已核）" % masked
        src = source.read_text(encoding="utf-8", errors="replace")
        assert not _SECRET_RE.search(src), "源件内出现密钥形态串"
        return "遮蔽生效：%s；源件零硬编码密钥" % masked

    def frame():
        a, b = demo_frame(100, 30), demo_frame(100, 30)
        assert a == b and len(a) == 30
        assert all(display_width(line) == display_width(a[0]) for line in a), "横宽不齐"
        return "同状态两遍渲染逐字一致，%d 行定宽" % len(a)

    def keys():
        """交互语义（对标 lazygit/k9s）：↑↓ 只在当前面板内动、/ 真过滤、? 帮助、写盘须确认。"""
        ui, lay = Ui(root=Path(tmp_root)), layout_of(100, 30)
        handle_key(ui, "DOWN", lay)
        assert ui.zpos == 1 and ui.focus == FOCUS_ZONES, "↓ 应在能力区内移动，不得换焦点"
        handle_key(ui, "UP", lay)          # 回到含 2 个动作的能力区
        handle_key(ui, "TAB", lay)
        assert ui.focus == FOCUS_ACTIONS
        handle_key(ui, "DOWN", lay)
        assert ui.apos == 1 and ui.focus == FOCUS_ACTIONS
        handle_key(ui, "/", lay)
        assert ui.prompt is not None and ui.prompt.kind == "filter-actions"
        ui.prompt.buf = "体检"
        handle_key(ui, "ENTER", lay)
        assert actions_view(ui) and all("体检" in a.title for _i, a in actions_view(ui)), \
            "过滤未生效"
        handle_key(ui, "?", lay)
        assert ui.help
        handle_key(ui, "x", lay)
        assert not ui.help, "帮助层应被任意键关闭"
        write_ui = Ui(root=Path(tmp_root))
        for zi, (_title, acts) in enumerate(ZONES):
            for ai, act in enumerate(acts):
                if "--write" in act.argv:
                    write_ui.zpos, write_ui.apos, write_ui.focus = zi, ai, FOCUS_ACTIONS
        assert write_ui.focus == FOCUS_ACTIONS
        handle_key(write_ui, "ENTER", layout_of(100, 30))
        assert write_ui.prompt is not None and write_ui.prompt.kind == "confirm-write", \
            "写盘动作必须先过二次确认"
        write_ui.prompt.buf = "no"
        assert handle_key(write_ui, "ENTER", layout_of(100, 30))[0] == "none"
        return "焦点/移动/过滤/帮助/写盘确认 五条语义逐条成立"

    def cli_face():
        if root is None:
            return "无仓库在场，跳过 CLI 面漂移比对"
        import importlib.util
        spec = importlib.util.spec_from_file_location("nf_cli_for_tui", root / "scripts" / "nf.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        parser = module._make_parser()
        real = set()
        for action in parser._actions:
            if isinstance(action, argparse._SubParsersAction):
                real |= set(action.choices)
        drift = sorted(set(KNOWN_TOP) ^ real)
        assert not drift, "TUI 白名单与 CLI 面漂移：%s" % drift
        return "白名单与 argparse 面逐条一致（%d 条）" % len(real)

    check("路径包含性", paths)
    check("无 shell 执行", no_shell)
    check("命令白名单与闸门", whitelist)
    check("密钥不硬编码", secrets)
    check("渲染确定性", frame)
    check("交互语义", keys)
    check("CLI 面漂移", cli_face)
    return all(ok for _n, ok, _d in rows), rows


def demo_frame(width: int = 100, height: int = 30) -> list:
    """演示帧：固定输入 → 固定输出（README 顶部的终端演示即由它生成）。"""
    ui = Ui(root=None, repo="NarrativeForge", demo=True, notice="就绪（0 项待办）")
    ui.focus = FOCUS_ACTIONS
    set_output(ui, [
        "❯ nf doctor   （退出码 0 · 0.42s）",
        "环境自检：Python 3.11 · 仓库在场 · 模块 13 · 管线 3",
        "✔ 只读体检通过：无缺件 / 无越界 / 无非确定性输出",
    ])
    return render_frame(ui, width, height)


# --------------------------------------------------------------------------- #
# 入口
# --------------------------------------------------------------------------- #
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="nf-tui", description="NarrativeForge 终端 TUI（全屏人机入口；命令真源仍是 nf CLI）",
        epilog="退出码：0 成功 · 1 运行失败 · 2 用法错误 · 3 安全拒跑 · 4 环境错误 · 130 中断")
    p.add_argument("--version", action="version", version="%s %s" % (APP, VERSION))
    p.add_argument("--root", default=None, help="仓库根（缺省自动发现）")
    p.add_argument("--demo", action="store_true", help="打印一帧演示画面后退出（确定性，不需仓库）")
    p.add_argument("--selftest", action="store_true", help="跑内建安全判据（退出码即结论）")
    p.add_argument("--list-actions", action="store_true", help="列出动作目录")
    p.add_argument("--exec", dest="exec_line", default="", help="非交互执行一条命令（脚本面）")
    p.add_argument("--plain", action="store_true", help="逐行模式（非全屏）")
    p.add_argument("--no-color", action="store_true", help="禁用 ANSI 颜色")
    p.add_argument("--json", action="store_true", help="机器面（配合 --selftest / --list-actions）")
    p.add_argument("--width", type=int, default=100, help="演示/机器面宽度（缺省 100）")
    p.add_argument("--height", type=int, default=30, help="演示/机器面高度（缺省 30）")
    return p


def _emit_json(payload: dict, code: int) -> int:
    sys.stdout.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")
    return code


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(args.root) if args.root else find_repo_root()
    python = find_python()
    if root is not None:
        root = Path(os.path.realpath(str(root)))
        if not all((root / marker).exists() for marker in _ROOT_MARKERS):
            sys.stderr.write("指定的 --root 不是 NF 仓库：%s\n  修复指引：指向含 verify.sh 与 "
                             "scripts/nf.py 的目录\n" % root)
            return EXIT_ENV

    try:
        if args.selftest:
            ok, rows = selftest(root, python)
            if args.json:
                return _emit_json({"kind": "nf-tui-selftest", "ok": ok,
                                   "rows": [{"name": n, "ok": o, "detail": d} for n, o, d in rows]},
                                  EXIT_OK if ok else EXIT_FAILURE)
            for name, passed, detail in rows:
                sys.stdout.write("%s %-16s %s\n" % ("✔" if passed else "✘", name, detail))
            return EXIT_OK if ok else EXIT_FAILURE
        if args.list_actions:
            rows = [{"zone": zone, "title": action.title, "argv": action.argv,
                     "params": [p.name for p in action.params]}
                    for _no, zone, action in all_actions()]
            if args.json:
                return _emit_json({"kind": "nf-tui-actions", "ok": True,
                                   "app": APP, "version": VERSION,
                                   "exit_codes": {"ok": EXIT_OK, "failure": EXIT_FAILURE,
                                                  "usage": EXIT_USAGE, "refused": EXIT_REFUSED,
                                                  "env": EXIT_ENV, "interrupt": EXIT_INTERRUPT},
                                   "surfaces": ["--demo", "--selftest [--json]",
                                                "--list-actions [--json]",
                                                "--exec \"nf <cmd>\"", "--plain"],
                                   "actions": rows}, EXIT_OK)
            for row in rows:
                sys.stdout.write("%-12s nf %s\n" % (row["zone"], " ".join(row["argv"])))
            return EXIT_OK
        if args.demo:
            frame = demo_frame(args.width, args.height)
            sys.stdout.write("\n".join(frame) + "\n")
            return EXIT_OK
        if root is None:
            if args.json:
                return _emit_json({"ok": False, "error": NO_REPO_MSG, "exit": EXIT_ENV}, EXIT_ENV)
            interactive = (not args.plain and not args.exec_line and sys.stdin.isatty()
                           and sys.stdout.isatty() and enable_vt())
            if interactive:
                # 「随时展现内容」：无仓库也进全屏（演示模式），界面与阅读面照常可用
                ui = Ui(root=None, repo="未发现仓库（演示模式）", demo=True,
                        notice="演示模式（未发现仓库）")
                ui.notice_kind = "err"
                set_output(ui, NO_REPO_MSG.splitlines())
                return run_fullscreen(ui, None, color=not args.no_color)
            sys.stdout.write("\n".join(demo_frame(args.width, args.height)) + "\n")
            sys.stderr.write(NO_REPO_MSG + "\n")
            return EXIT_ENV
        if args.plain or args.exec_line or not sys.stdin.isatty() or not enable_vt():
            return run_plain(root, python, exec_line=args.exec_line)
        color = not args.no_color
        ui = Ui(root=root, repo=str(root) if root else "")
        return run_fullscreen(ui, python, color=color)
    except NfTuiError as exc:
        if args.json:
            return _emit_json({"ok": False, "error": exc.message, "exit": exc.code}, exc.code)
        sys.stderr.write("✘ %s\n" % exc.render())
        return exc.code
    except KeyboardInterrupt:
        sys.stderr.write("已中断\n")
        return EXIT_INTERRUPT


if __name__ == "__main__":
    sys.exit(main())
