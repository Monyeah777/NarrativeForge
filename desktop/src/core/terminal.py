#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""NF 终端（`nf shell`）——端壳退役后的人机交互入口（纯 stdlib · 确定性 · 可注入）。

定位（对齐 `docs/L3_FROZEN.md`「能力入口一律落 CLI」）：
桌面 GUI 端壳与打包线已于 2026-09-09 永久退役，公开面收敛为「协议 + core 库 + CLI」，
人机交互面随之真空。本模块补的**不是**第二套命令面，而是把**既有** CLI 命令面按能力菜单
组织成可交互会话：读一行 → 解析 → 闸门 → 分派 → 打印。命令真源仍是 `scripts/nf.py`
的 argparse 面——`ZONES` 的每条示例命令都由 verify check39 解析断言，菜单指向死命令即红。

三条硬约束（与仓库红线同源）：
1. **零第三方依赖**：只用 stdlib。刻意不用 curses（Windows 无该模块）与 PySide6 等
   GUI 工具包（PySide6 只服务 CCV3 卡面写入，与终端无关）。
2. **确定性**：同一输入两次运行逐字节一致——`nf shell --exec` 是回归面，也是 check39 的判据。
3. **安全闸门**：写入类命令默认拒跑，须显式确认（交互输入 yes，或调用方显式 `--yes`）。
   终端不替使用者拍板；`serve`（长驻服务）与 `shell`（递归会话）在会话内给指引而非执行。

分层：本模块只做「解析 / 菜单 / 渲染 / 闸门 / 会话状态机」，**不 import scripts/nf.py**——
执行由调用方以 `runner(argv) -> int` 注入，故 core 层保持零 CLI 反向依赖，单测可完全离线。
"""
from __future__ import annotations

import io
import json
import shlex
import sys
from collections import namedtuple
from contextlib import redirect_stderr, redirect_stdout

SHELL_VERSION = "1.0.0"

#: 会话提示符（单行、无颜色——重定向到文件时逐字节可读）
PROMPT = "nf> "
#: 退出词（大小写不敏感）
QUIT_WORDS = ("quit", "exit", "q", "退出", "再见")
#: 确认词（写入类命令的显式放行）
YES_WORDS = ("y", "yes", "ok", "是", "确认", "可以")

#: 需要显式确认的写入面标记（命令里出现任一即视为写盘/不可逆动作）
CONFIRM_FLAGS = ("--write", "--apply", "--register", "--tag", "--force",
                 "--push", "--delete", "--rm")
#: 需要显式确认的 (命令, 子命令) 组合（无标记位也写盘的动词）
CONFIRM_VERBS = (("asset", "add"), ("asset", "rm"), ("asset", "deprecate"),
                 ("module", "deprecate"), ("module", "restore"),
                 ("module", "signature"), ("register", ""), ("import", ""),
                 ("rename", ""), ("release", ""))
#: 会话内不直接执行：长驻/递归/需独占终端的动词 → 给指引
BLOCKED_IN_SHELL = {
    "shell": "终端内不再开终端（避免递归会话）：请另开一个终端窗口运行 nf shell。",
    "serve": "serve 是长驻 MCP 服务（会占住当前终端）：请另开终端运行 "
             "nf serve <快照.json>，本终端可继续用只读命令面。",
}

#: 能力菜单（单一真源）：键 / 稳定 id / 标题 / 一句话 / 示例命令（可执行原文）
#: 覆盖端壳退役前 GUI 七区的能力面（导入 / 校验 / 管线 / 生成 / 资产 / 预设 / 社区），
#: 但**只指向既有命令**——新增能力仍须先落 CLI，再登记进本表。
ZONES = (
    {"key": "0", "id": "doctor", "title": "环境自检",
     "summary": "只读体检：仓库件在场 / 解释器可用 / 基线自描述一致性",
     "examples": ("nf doctor",)},
    {"key": "1", "id": "demo", "title": "一键演示世界",
     "summary": "P04 轻混全链跑一遍（retrieve→compose→gate→export）并产出 CCV3 卡",
     "examples": ("nf demo",)},
    {"key": "2", "id": "assemble", "title": "需求 → 装配计划",
     "summary": "一句话需求 → 命中预设包或转用户自定义流；--check 验收成品",
     "examples": ("nf assemble \"帮我组装一个西幻生存世界的完整版\"",
                  "nf assemble 西幻生存 --check sample.md")},
    {"key": "3", "id": "run", "title": "全链生产",
     "summary": "选管线与模块 → 装配 → 质量门 → 导出（--seed 装载官方核心 + 社区包）",
     "examples": ("nf run --pipeline community/校园西幻轻混组合包/pipelines/"
                  "P04_轻混装配流管线.md --modules 通用类:M00,轻混类:M91,"
                  "轻混类:M92,通用类:M80 --seed",)},
    {"key": "4", "id": "validate", "title": "校验与体检",
     "summary": "正文 lint / 状态前置 / 一致性分级 / 模块引用门禁（端壳时代「校验区」）",
     "examples": ("nf lint sample.md", "nf conformance", "nf module verify")},
    {"key": "5", "id": "market", "title": "货架与资产",
     "summary": "市场浏览（--list）/ 单包详情 / 资产货架 / 供应链台账盘点",
     "examples": ("nf market --list", "nf asset ls", "nf asset inventory")},
    {"key": "6", "id": "pipeline", "title": "管线与模块",
     "summary": "管线派生（new）/ 抽象执行（dryrun）/ 模块状态位与边界签名",
     "examples": ("nf pipeline new --id P07 --name 演示领域管线", "nf module ls")},
    {"key": "7", "id": "help", "title": "帮助与命令面",
     "summary": "全命令总览与任意子命令帮助（终端内输入 /help 同效）",
     "examples": ("nf --help", "nf help assemble")},
)

#: 一行输入的解析结果：kind ∈ empty/quit/help/menu/zone/run/unknown
Intent = namedtuple("Intent", "kind payload raw")

#: 斜杠命令词表（`/` 后首个词）：既是 `/x` 形态的判据，也是 MSYS 还原的判据
SLASH_WORDS = ("quit", "exit", "q", "help", "?", "menu", "菜单",
               "zone", "z", "区", "doctor", "自检", "version", "ver", "版本")


def _slash_intent(body: str, raw: str):
    """解析斜杠命令体 → Intent；非斜杠命令词返回 None（调用方决定怎么归类）。"""
    head, _, tail = body.partition(" ")
    head = head.lower()
    if head in ("quit", "exit", "q"):
        return Intent("quit", "", raw)
    if head in ("help", "?"):
        return Intent("help", tail.strip(), raw)
    if head in ("menu", "菜单"):
        return Intent("menu", "", raw)
    if head in ("zone", "z", "区"):
        return Intent("zone", tail.strip(), raw)
    if head in ("doctor", "自检"):
        return Intent("run", ["doctor"], raw)
    if head in ("version", "ver", "版本"):
        return Intent("run", ["--version"], raw)
    return None


def zone_table() -> tuple:
    """返回能力菜单真源（终端渲染、check39 与文档共用同一份数据，不留第二份）。"""
    return ZONES


def zone_by_key(key: str):
    """按菜单键取条目；未命中返回 None（调用方给修复指引，不抛栈）。"""
    for item in ZONES:
        if item["key"] == str(key).strip():
            return item
    return None


def split_args(text: str) -> list:
    """把一行命令拆成 argv；兼容带引号的需求文本。拆分失败退回朴素空白切分。"""
    try:
        return shlex.split(text, posix=True)
    except ValueError:
        return text.split()


def _strip_nf(argv: list) -> list:
    """剥掉可选的 `nf` / `nf.py` 前缀——终端里两种写法都吃。"""
    if argv and argv[0] in ("nf", "nf.py"):
        return argv[1:]
    return argv


def parse(line: str) -> Intent:
    """解析一行输入 → Intent。

    支持四类：`/` 命令（/help /menu /quit /zone <k>）、裸菜单键（0-7）、
    `nf <args...>` 直通、纯 quit 词。其余为 unknown（由调用方给指引）。
    """
    raw = line.strip()
    if not raw:
        return Intent("empty", "", raw)
    if raw.lower() in QUIT_WORDS:
        return Intent("quit", "", raw)
    if raw.startswith("/"):
        hit = _slash_intent(raw[1:].strip(), raw)
        return hit if hit is not None else Intent("unknown", raw, raw)
    if raw.isdigit() and zone_by_key(raw) is not None:
        return Intent("zone", raw, raw)
    argv = _strip_nf(split_args(raw))
    if not argv:
        return Intent("empty", "", raw)
    if argv[0] in ("quit", "exit"):
        return Intent("quit", "", raw)
    # MSYS/Git-Bash 兼容：`"/zone 4"` 这类以 `/` 开头的参数会被通行层当成 POSIX 路径
    # 转换成 `C:/…/zone 4`（单 token 的 `/menu` 不受影响）。若首 token 的**末段**是斜杠
    # 命令词，就还原成该命令——否则 Git Bash 用户会看到一条莫名其妙的 argparse 报错。
    head_path = argv[0].replace("\\", "/")
    if "/" in head_path:
        seg = head_path.rsplit("/", 1)[-1].lower()
        if seg in SLASH_WORDS:
            hit = _slash_intent(" ".join([seg] + [str(a) for a in argv[1:]]), raw)
            if hit is not None:
                return hit
    return Intent("run", argv, raw)


def needs_confirm(argv: list) -> bool:
    """判定一条命令是否属于写入/不可逆面（须显式确认才放行）。"""
    if any(tok in CONFIRM_FLAGS for tok in argv):
        return True
    if not argv:
        return False
    head = argv[0]
    sub = argv[1] if len(argv) > 1 and not argv[1].startswith("-") else ""
    return (head, sub) in CONFIRM_VERBS or (head, "") in CONFIRM_VERBS


def example_resolves(example: str, commands, root_flags) -> bool:
    """菜单示例是否指向**真实**命令面（commands/root_flags 由调用方从 argparse 面传）。

    单一判据：verify check39 与单测都调本函数——菜单不许指向死命令，判据只有一处实现。
    """
    intent = parse(example)
    if intent.kind != "run" or not intent.payload:
        return False
    head = intent.payload[0]
    return head in set(commands) or head in set(root_flags)


def banner(baseline: str = "") -> str:
    """终端开场横幅：版本 + 基线 + 最快上手路径（无时间戳 → 可逐字节复现）。"""
    lines = ["NarrativeForge 终端 v%s（端壳退役后的人机入口；命令真源 = nf CLI）"
             % SHELL_VERSION]
    if baseline:
        lines.append("  基线：%s" % baseline)
    lines += [
        "  输入数字 0-7 看能力菜单 · /menu 重看菜单 · /help 看用法 · quit 退出",
        "  任意 nf 命令可直接直通（例：nf doctor / nf market --list）",
        "  写入类命令（--write/--apply/--register…）须二次确认，终端不替你拍板",
    ]
    return "\n".join(lines)


def menu() -> str:
    """渲染能力菜单（人读表 + 可执行示例入口）。"""
    lines = ["== NF 能力菜单（端壳七区 → CLI 命令面）==", ""]
    for item in ZONES:
        lines.append("[%s] %s —— %s" % (item["key"], item["title"], item["summary"]))
    lines += ["",
              "看某区示例：输入编号（如 4）或 /zone 4；执行：把示例里的命令打进终端。"]
    return "\n".join(lines)


def zone_detail(key: str) -> str:
    """渲染单个能力区的示例命令（未命中键 → 给可用键清单，不抛栈）。"""
    item = zone_by_key(key)
    if item is None:
        return ("未识别的菜单键「%s」（可用键：%s；示例：输入 0 看环境自检）"
                % (key, "、".join(z["key"] for z in ZONES)))
    lines = ["== [%s] %s ==" % (item["key"], item["title"]),
             "  %s" % item["summary"],
             "  示例命令（复制即用）："]
    lines += ["    %s" % ex for ex in item["examples"]]
    return "\n".join(lines)


class Session:
    """终端会话状态机：解析 → 闸门 → 分派，I/O 全部由调用方注入（可离线单测）。

    `runner(argv) -> int` 为命令执行回调（CLI 侧传 `main`）；本类只负责
    「该不该跑 / 跑完怎么记」——保证 core 层不依赖 scripts/nf.py。
    """

    def __init__(self, runner, assume_yes: bool = False):
        if not callable(runner):
            raise ValueError("Session 需要可调用的 runner(argv) -> int；"
                             "请传入 scripts/nf.py 的 main（终端不自己执行命令）")
        self._runner = runner
        self.assume_yes = bool(assume_yes)
        self.history = []      # 逐条记录 dict（line/kind/exit/argv/out/err/note）
        self.last_zone = ""
        self.quit = False

    def invoke(self, argv: list) -> tuple:
        """执行一条命令 → (exit_code, stdout, stderr)；捕获输出以便落档与比对。

        三类非返回式退出都在此归一，保证会话不被打断：
        `SystemExit`（argparse 用法错误 / --version / help 动作）、`KeyboardInterrupt`（130）、
        未预期异常（与 CLI 顶层同口径：一句错误 + 退出 1，NF_DEBUG=1 时透出堆栈）。
        """
        out, err = io.StringIO(), io.StringIO()
        code = 0
        with redirect_stdout(out), redirect_stderr(err):
            try:
                result = self._runner(list(argv))
                if isinstance(result, int):
                    code = result
            except SystemExit as exc:
                code = exc.code if isinstance(exc.code, int) else 1
            except KeyboardInterrupt:
                code = 130
            except Exception as exc:  # 与 CLI 顶层同口径：一句错误 + 退出 1
                print("  ✗ 内部错误：%s（重跑 NF_DEBUG=1 看堆栈）" % exc, file=sys.stderr)
                code = 1
        return code, out.getvalue(), err.getvalue()

    def dispatch(self, line: str, confirmed: bool = False) -> dict:
        """处理一行 → 记录 dict（line/kind/exit/argv/out/err/note）。

        `confirmed=True` 表示调用方已就该行取得使用者放行（交互追问拿到 yes）——写入类
        命令据此放行；`assume_yes`（CLI 的 --yes）是整场会话的显式放行开关。
        """
        intent = parse(line)
        rec = {"line": intent.raw, "kind": intent.kind, "exit": 0,
               "argv": [], "out": "", "err": "", "note": ""}
        if intent.kind == "empty":
            pass
        elif intent.kind == "quit":
            self.quit = True
        elif intent.kind == "help":
            code, out, err = self.invoke(["help"] + ([intent.payload]
                                                     if intent.payload else []))
            rec.update(exit=code, out=out, err=err)
        elif intent.kind == "menu":
            rec["note"] = menu()
        elif intent.kind == "zone":
            self.last_zone = intent.payload
            rec["note"] = zone_detail(intent.payload)
        elif intent.kind == "unknown":
            rec.update(exit=2, note=("未识别：%s（可用：数字 0-7 看菜单 · /menu · "
                                     "/help · quit · 或直接输入 nf 命令）" % intent.raw))
        else:  # run
            argv = list(intent.payload)
            rec["argv"] = argv
            blocked = BLOCKED_IN_SHELL.get(argv[0]) if argv else None
            if blocked:
                rec.update(exit=2, note=blocked)
            elif needs_confirm(argv) and not (self.assume_yes or confirmed):
                rec.update(exit=2, note=(
                    "%s 属于写入/不可逆面——须显式确认：交互会话里输入 yes 放行，"
                    "非交互跑时加 --yes（终端不替使用者拍板）。" % " ".join(argv)))
            else:
                code, out, err = self.invoke(argv)
                rec.update(exit=code, out=out, err=err)
        self.history.append(rec)
        return rec

    def handle(self, line: str) -> tuple:
        """薄封装：处理一行 → (kind, exit_code, 要打印的文本)。"""
        rec = self.dispatch(line)
        return (rec["kind"], rec["exit"],
                (rec["out"] + rec["err"] + rec["note"]).rstrip("\n"))


def run_session(runner, stdin, stdout, assume_yes: bool = False,
                show_banner: bool = True, baseline: str = "") -> int:
    """交互会话主循环：读一行 → 分派 → 打印 → 直到 quit / EOF。

    写入类命令在交互态**就地追问**（读到 yes 才放行本次）；非交互态仍须 `--yes`。
    返回 0（正常结束）或非 0（会话中有命令失败）——供 CI/脚本判红。
    """
    session = Session(runner, assume_yes=assume_yes)
    if show_banner:
        stdout.write(banner(baseline) + "\n")
        stdout.flush()
    worst = 0
    while not session.quit:
        stdout.write(PROMPT)
        stdout.flush()
        line = stdin.readline()
        if line == "":                      # EOF（管道/重定向结束）
            stdout.write("\n")
            break
        intent = parse(line)
        confirmed = False
        if intent.kind == "run" and needs_confirm(intent.payload) \
                and not session.assume_yes:
            stdout.write("  该命令会写盘：%s\n  确认执行？(yes/no) " % intent.raw)
            stdout.flush()
            confirmed = stdin.readline().strip().lower() in YES_WORDS
            if not confirmed:
                stdout.write("  已取消（未执行）。\n")
                stdout.flush()
                session.history.append({"line": intent.raw, "kind": "blocked",
                                        "exit": 2, "argv": list(intent.payload),
                                        "out": "", "err": "", "note": ""})
                worst = max(worst, 2)
                continue
        rec = session.dispatch(line, confirmed=confirmed)
        text = (rec["out"] + rec["err"] + rec["note"]).rstrip("\n")
        if text:
            stdout.write(text + "\n")
        stdout.flush()
        worst = max(worst, rec["exit"])
    return worst


def run_script(script: str, runner, assume_yes: bool = False,
               as_json: bool = False) -> tuple:
    """非交互模式：`--exec "命令1; 命令2"` 逐条执行 → (exit_code, 文本, 记录)。

    记录逐条含 line/kind/exit/argv/out/err —— 既是 CI 判据也是机器面（`--json`）。
    命令之间用 `;` 分隔（NF 命令面本身不用分号，故不产生歧义）。
    """
    session = Session(runner, assume_yes=assume_yes)
    records = []
    worst = 0
    for piece in script.split(";"):
        raw = piece.strip()
        if not raw:
            continue
        rec = session.dispatch(raw)
        records.append(rec)
        worst = max(worst, rec["exit"])
        if rec["kind"] == "quit":
            break
    if as_json:
        return (worst,
                json.dumps({"kind": "nf-shell", "shell_version": SHELL_VERSION,
                            "records": records}, ensure_ascii=False, indent=2),
                records)
    lines = []
    for rec in records:
        lines.append("[nf shell] > %s" % rec["line"])
        body = (rec["out"] + rec["err"] + rec["note"]).rstrip("\n")
        if body:
            lines += ["  " + ln for ln in body.splitlines()]
        lines.append("  结果：%s（exit=%d）" % (rec["kind"], rec["exit"]))
    return worst, "\n".join(lines), records
