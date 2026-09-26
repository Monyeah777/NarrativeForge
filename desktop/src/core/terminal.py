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
import os
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

#: 能力地图（**策展真源**）：把 CLI 的每个顶层命令恰好归入一个能力族。
#: 菜单（0-7）是新手路径；本表是「全功能可见」的完整分面——两者分工不重叠。
#: check39 与 `nf shell --verify` 共用同一判据：族分区必须恰好覆盖命令集（不缺不重不虚）。
FAMILIES = (
    {"id": "start", "name": "上手与自检",
     "summary": "第一次进 NF：体检、一键演示、自述数字、抽象阶梯",
     "commands": ("doctor", "demo", "stats", "layers")},
    {"id": "forge", "name": "装配与生产",
     "summary": "从需求到产物：装配计划、全链管道、渲染、协议件读写、入库登记",
     "commands": ("assemble", "run", "render", "spec", "register", "import")},
    {"id": "shelf", "name": "资产与货架",
     "summary": "市场、资产台账、模块生命周期、管线派生、组合引擎、域包工厂、产出形态",
     "commands": ("market", "asset", "module", "pipeline", "combine", "domain",
                  "output", "rename")},
    {"id": "verify", "name": "质检与验证",
     "summary": "正文 lint、一致性报告、断言表、知识签名、评分、差异、解释、状态前置、发布体检、许可证、遥测",
     "commands": ("lint", "conformance", "assertions", "sig", "score", "diff",
                  "explain", "st-validate", "release", "license", "telemetry")},
    {"id": "library", "name": "图书馆与知识",
     "summary": "馆藏存取、双源知识、行话术语、实践包、协议件版本史、引用关系与影响面",
     "commands": ("library", "knowledge", "cognition", "patterns", "rfc",
                  "related", "who-refers", "impact")},
    {"id": "govern", "name": "治理与决策",
     "summary": "决策记录（ADR）、审计、背书、回执、交接、复盘、决策层、评审、构建回路、批准、透明日志、设计审计",
     "commands": ("decisions", "audit", "attest", "receipts", "handover",
                  "postmortem", "decide", "model", "review", "workloop",
                  "approve", "transparency", "design")},
    {"id": "integrate", "name": "服务与集成",
     "summary": "MCP 服务面、编辑器面、跑分台、端点契约、互操作导出、指令档路由、事件背书、状态前置、世界模型、模块工具面",
     "commands": ("serve", "lsp", "bench", "endpoint", "interop", "driver",
                  "events", "state-front", "worldmodel", "toolface")},
    {"id": "meta", "name": "命令面与终端",
     "summary": "帮助、补全脚本、终端自身（本命令即在此族）",
     "commands": ("help", "completion", "shell", "terminal")},
)

#: 斜杠命令词表（`/` 后首个词）：既是 `/x` 形态的判据，也是 MSYS 还原的判据
SLASH_WORDS = ("quit", "exit", "q", "help", "?", "menu", "菜单",
               "zone", "z", "区", "doctor", "自检", "version", "ver", "版本",
               "find", "search", "找", "查", "commands", "cmd", "cmds", "命令",
               "map", "families", "族", "地图",
               "history", "hist", "历史", "complete", "补全",
               "set", "settings", "设置",
               "form", "forms", "表单", "cancel", "取消")


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
    if head in ("find", "search", "找", "查"):
        return Intent("search", tail.strip(), raw)
    if head in ("commands", "cmd", "cmds", "命令"):
        return Intent("commands", tail.strip(), raw)
    if head in ("map", "families", "族", "地图"):
        return Intent("map", tail.strip(), raw)
    if head in ("history", "hist", "历史"):
        return Intent("history", tail.strip(), raw)
    if head in ("complete", "补全"):
        return Intent("complete", tail.strip(), raw)
    if head in ("set", "settings", "设置"):
        return Intent("set", tail.strip(), raw)
    if head in ("form", "forms", "表单"):
        return Intent("form", tail.strip(), raw)
    if head in ("cancel", "取消"):
        return Intent("cancel", tail.strip(), raw)
    return None


def zone_table() -> tuple:
    """返回能力菜单真源（终端渲染、check39 与文档共用同一份数据，不留第二份）。"""
    return ZONES


# ---------------------------------------------------------------- 输出体验
# 顶尖 CLI 的观感三件：**列宽对齐**（CJK 按两个显示宽度算）、**长列表可收**（限长 + 提示）、
# **颜色克制**（默认只在真 TTY 上色，`NO_COLOR` 一票否决；非 TTY 逐字节确定——这是硬契约）。

#: East Asian Wide / Fullwidth 码位区间（UAX #11 的实用子集；emoji 走宽）
_WIDE_RANGES = (
    (0x1100, 0x115F), (0x2E80, 0x303E), (0x3041, 0x33FF), (0x3400, 0x4DBF),
    (0x4E00, 0x9FFF), (0xA000, 0xA4CF), (0xAC00, 0xD7A3), (0xF900, 0xFAFF),
    (0xFE10, 0xFE19), (0xFE30, 0xFE6F), (0xFF00, 0xFF60), (0xFFE0, 0xFFE6),
    (0x1F300, 0x1F64F), (0x1F900, 0x1F9FF), (0x20000, 0x2FFFD), (0x30000, 0x3FFFD),
)
#: 结构着色（ANSI）：只在 color=True 时生效；语义固定、可复算
_STYLES = {"head": "\033[1m", "cmd": "\033[36m", "ok": "\033[32m",
           "warn": "\033[33m", "fail": "\033[31m", "dim": "\033[2m"}
_RESET = "\033[0m"


def char_width(ch: str) -> int:
    """单字符显示宽度（CJK/全角/emoji = 2，其余 = 1，控制字符 = 0）。"""
    cp = ord(ch)
    if cp < 32 or cp == 0x7F:
        return 0
    for lo, hi in _WIDE_RANGES:
        if lo <= cp <= hi:
            return 2
    return 1


def display_width(text: str) -> int:
    """字符串显示宽度（列对齐用；纯函数、确定性）。"""
    return sum(char_width(ch) for ch in str(text or ""))


def pad_to(text: str, width: int) -> str:
    """右补空格到指定**显示宽度**（CJK 不歪列）。"""
    text = str(text or "")
    gap = int(width) - display_width(text)
    return text + (" " * gap if gap > 0 else "")


def clip(text: str, width: int) -> str:
    """单行截断到指定显示宽度（超宽加省略号）。"""
    text = str(text or "")
    if display_width(text) <= width:
        return text
    out, used = [], 0
    for ch in text:
        cw = char_width(ch)
        if used + cw > max(0, int(width) - 1):
            break
        out.append(ch)
        used += cw
    return "".join(out) + "…"


def style(text, kind: str, on: bool = False) -> str:
    """按语义着色（on=False 原样返回——非 TTY 默认，保逐字节确定）。"""
    body = str(text)
    if not on or kind not in _STYLES:
        return body
    return "%s%s%s" % (_STYLES[kind], body, _RESET)


def resolve_color(mode: str = "auto", stream=None) -> bool:
    """颜色模式 → 布尔：always / never / auto（auto = 真 TTY 且未设 NO_COLOR）。"""
    m = str(mode or "auto").strip().lower()
    if m == "always":
        return True
    if m == "never":
        return False
    if os.environ.get("NO_COLOR"):
        return False
    try:
        return bool(stream is not None and stream.isatty())
    except Exception:      # 尽力而为：判定不了就按无色（安全侧）
        return False


def term_width(width=None, env=None, default: int = 100) -> int:
    """渲染宽度：显式 width > 环境 COLUMNS（≥40 才认）> default。"""
    if width:
        try:
            return max(40, int(width))
        except (TypeError, ValueError):
            return default
    e = env if env is not None else os.environ
    try:
        cols = int(e.get("COLUMNS") or 0)
    except (TypeError, ValueError, AttributeError):
        cols = 0
    return cols if cols >= 40 else default


def _row(left: str, right: str, width: int, color: bool = False) -> str:
    """两列行：左列固定宽度（按显示宽度补），右列按剩余宽度截断。"""
    left_col = 28
    left_txt = pad_to("  " + left, left_col)
    remain = max(20, int(width) - left_col)
    return style(left_txt, "cmd", color) + clip(right, remain)


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


# ---------------------------------------------------------------- 写盘表单
# 「会改仓库」的动作不该要求用户一口气敲全参数、再补一个 `--yes`。表单族把它拆成**逐项追问**：
# 参数真源 = 表单模板（argv 模板里的 `{key}` 由 step 填），执行仍走同一条写盘闸门。
#
# 纪律：每张表的模板只能指向**真实存在的 CLI 动词**（check39 断言 argv[0] 在命令面内）；
# 表单本身不改任何东西——它只把参数问齐，然后交给 CLI 与闸门。

FORMS = (
    {"id": "deprecate-module", "title": "弃用模块",
     "summary": "把某个模块文件标记为 deprecated（写文件头状态位）",
     "steps": ({"key": "file", "prompt": "模块 md 路径", "required": True,
                "hint": "如 community/<包>/modules/M97_术语管理.md"},
               {"key": "reason", "prompt": "弃用原因（可空）", "required": False}),
     "argv": ("module", "deprecate", "{file}", "--reason", "{reason}")},
    {"id": "restore-module", "title": "恢复模块",
     "summary": "把 deprecated / retired 的模块恢复为 active",
     "steps": ({"key": "file", "prompt": "模块 md 路径", "required": True},),
     "argv": ("module", "restore", "{file}")},
    {"id": "types-write", "title": "补 I/O 类型面",
     "summary": "给有机读契约的模块补 io_types（确定性推导，未命中写 untyped）",
     "steps": (), "argv": ("module", "types", "--write")},
    {"id": "stats-write", "title": "重写自述数字生成区",
     "summary": "按实算重写 README / README.en / llms.txt 统计块与 protocol/repo_stats.json",
     "steps": (), "argv": ("stats", "--write")},
    {"id": "asset-add", "title": "资产入库",
     "summary": "资产文件头写 nf-asset 头 + 台账 append（溯源键表自动生成）",
     "steps": ({"key": "file", "prompt": "资产文件路径（相对 --root）", "required": True},
               {"key": "key", "prompt": "溯源键（台账内唯一）", "required": True},
               {"key": "source", "prompt": "溯源说明（源文件/区间/登记日期）", "required": True},
               {"key": "root", "prompt": "资产根目录", "required": True, "hint": "如 05_资产库"},
               {"key": "module", "prompt": "消费模块 id（可空）", "required": False},
               {"key": "version", "prompt": "版本位（可空 = 1.0）", "required": False},
               {"key": "tier", "prompt": "货架分级 official/community/experimental（可空）",
                "required": False}),
     "argv": ("asset", "add", "{file}", "--key", "{key}", "--source", "{source}",
              "--root", "{root}", "--module", "{module}", "--version", "{version}",
              "--tier", "{tier}")},
    {"id": "register-apply", "title": "本地登记写回",
     "summary": "protocol.yaml → registry protocols[]（校验全过后只增不删合并写）",
     "steps": ({"key": "pkg_dir", "prompt": "包目录", "required": True,
                "hint": "如 community/校园西幻轻混组合包"},),
     "argv": ("register", "{pkg_dir}", "--apply")},
    {"id": "rename-apply", "title": "模块改名重链",
     "summary": "批量更新 references 中对该模块的引用后写回",
     "steps": ({"key": "old_id", "prompt": "旧模块 id", "required": True},
               {"key": "new_id", "prompt": "新模块 id", "required": True}),
     "argv": ("rename", "{old_id}", "{new_id}", "--apply")},
    {"id": "receipts-write", "title": "重签协议层回执",
     "summary": "内容改动后重新冻结 protocol/RECEIPTS.json（随后通常重跑 conformance / 批准）",
     "steps": (), "argv": ("receipts", "--scope", "protocol", "--write")},
)


def form_table() -> tuple:
    """表单真源（终端渲染、`--form`、check39 共用同一份）。"""
    return FORMS


def form_by_id(fid: str):
    """按 id 取表单；未命中返回 None（调用方给可用清单，不抛栈）。"""
    for f in FORMS:
        if str(f["id"]) == str(fid).strip():
            return f
    return None


def form_missing(form, answers) -> list:
    """还差哪些**必填** step（未填或空白都算缺）。"""
    out = []
    for st in form.get("steps") or []:
        if st.get("required") and not str((answers or {}).get(st["key"], "")).strip():
            out.append(st["key"])
    return out


def form_pending(form, answers) -> list:
    """还没**settle**的 step（未出现在 answers 里；空串 = 已明确跳过）——表单逐项追问用它。"""
    return [st["key"] for st in form.get("steps") or []
            if st["key"] not in (answers or {})]


def build_argv(form, answers) -> list:
    """表单 + 回答 → CLI argv（空值连同其旗标一起丢弃；必填缺失即报并给指引）。"""
    answers = answers or {}
    missing = form_missing(form, answers)
    if missing:
        raise ValueError("表单 %s 还缺必填项：%s（修复指引：用 /form %s 补齐或 --answer %s=…）"
                         % (form.get("id"), "、".join(missing), form.get("id"),
                            missing[0]))
    toks = list(form.get("argv") or [])
    out = []
    i = 0
    while i < len(toks):
        tok = toks[i]
        nxt = toks[i + 1] if i + 1 < len(toks) else None
        if tok.startswith("{") and tok.endswith("}"):
            val = str(answers.get(tok[1:-1], "")).strip()
            if val:
                out.extend(split_args(val))
            i += 1
            continue
        if nxt and nxt.startswith("{") and nxt.endswith("}"):
            val = str(answers.get(nxt[1:-1], "")).strip()
            if val:
                out.append(tok)
                out.extend(split_args(val))
            i += 2                    # 空值：旗标与值一起丢，不留悬空旗标
            continue
        out.append(tok)
        i += 1
    return out


def render_forms(filt: str = "", width=None, color: bool = False) -> str:
    """列出全部写盘表单（可按 id/标题过滤）。"""
    f = str(filt or "").strip().lower()
    w = term_width(width)
    lines = [style("== 写盘表单（%d 张 · 逐项追问 → 组装命令 → 二次确认）==" % len(FORMS),
                   "head", color)]
    for form in FORMS:
        if f and f not in str(form["id"]).lower() and f not in str(form["title"]).lower():
            continue
        lines.append(_row("/form " + str(form["id"]),
                          "%s —— %s" % (form["title"], form["summary"]), w, color))
    lines.append("  用法：/form <id> 开始追问；/cancel 中止；参数真源见 protocol/LAYERS.json 同级的 CLI 面")
    return "\n".join(lines)


def render_form(form, answers=None, color: bool = False) -> str:
    """渲染一张表单：已填/待填进度 + 下一个问题。"""
    answers = answers or {}
    lines = [style("== 表单：%s（%s）==" % (form["title"], form["id"]), "head", color),
             "  %s" % form["summary"], ""]
    for st in form.get("steps") or []:
        key = st["key"]
        val = str(answers.get(key, "")).strip()
        mark = "✔" if val else ("✱" if st.get("required") else "·")
        shown = ("　%s=%s" % (key, val)) if val else ""
        lines.append("  [%s] %s（%s）%s%s"
                     % (mark, key, st["prompt"], shown,
                        ("  提示：%s" % st["hint"]) if st.get("hint") and not val else ""))
    missing = form_missing(form, answers)
    pending = form_pending(form, answers)
    if pending:
        nxt = [st for st in form["steps"] if st["key"] == pending[0]][0]
        tail = "空行 = 跳过（可选项）" if not nxt.get("required") else "必填"
        lines += ["", "  请回答 %s（%s）：直接输入值（%s）；`/cancel` 中止"
                  % (nxt["key"], nxt["prompt"], tail)]
    elif missing:
        lines += ["", "  [FAIL] 必填项为空：%s" % "、".join(missing)]
    else:
        try:
            argv = build_argv(form, answers)
            lines += ["", "  组装命令：nf %s" % " ".join(argv),
                      "  确认执行？(yes/no)"]
        except ValueError as exc:
            lines += ["", "  [FAIL] %s" % exc]
    return "\n".join(lines)


#: 会话状态文件 schema（`--session <file>`；仅显式给出时读写）
SESSION_SCHEMA = "nf-shell-session/1"


def load_session_state(path: str):
    """读会话文件 → (state, warn)：缺件返回空态；坏件给理由但不抛（终端不该被状态文件拖死）。"""
    if not path:
        return {}, ""
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except FileNotFoundError:
        return {}, ""
    except OSError as exc:
        return {}, "会话文件不可读（%s）：%s" % (path, exc)
    except json.JSONDecodeError as exc:
        return {}, "会话文件不是合法 JSON（%s）：%s（修复指引：删除该文件或改成合法 JSON）" \
            % (path, exc)
    if str(data.get("schema")) != SESSION_SCHEMA:
        return {}, "会话文件 schema 不匹配（期望 %s；修复指引：删除后重开）" % SESSION_SCHEMA
    return data, ""


def save_session_state(path: str, session) -> bool:
    """把会话状态落盘（视图设置 + 上次分区）：父目录不存在则建；失败返回 False（不抛）。"""
    data = {"schema": SESSION_SCHEMA,
            "settings": {"color": str(session.color_mode),
                         "width": int(session.width or 0),
                         "limit": int(session.limit or 0)},
            "last_zone": str(session.last_zone or "")}
    try:
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=2, sort_keys=True)
            fh.write("\n")
        return True
    except OSError:
        return False


def _strip_comment(line: str) -> str:
    """剥掉行内注释：`#` 位于**词首**（行首或前一字符为空白）且不在引号内时起始注释。

    与 shell 同语义（`echo a # x` 的 `#` 起注释，`echo "a # x"` 的不算）——脚本文件面
    因此可以自注释，而带 `#` 的引号参数（如装配需求文本）不会被吃掉。
    """
    out, quote, prev = [], None, " "
    for ch in str(line):
        if quote:
            out.append(ch)
            if ch == quote:
                quote = None
            continue
        if ch in ("'", '"'):
            quote = ch
            out.append(ch)
            prev = ch
            continue
        if ch == "#" and prev.isspace():
            break
        out.append(ch)
        prev = ch
    return "".join(out)


def parse(line: str) -> Intent:
    """解析一行输入 → Intent。

    支持四类：`/` 命令（/help /menu /quit /zone <k>）、裸菜单键（0-7）、
    `nf <args...>` 直通、纯 quit 词。其余为 unknown（由调用方给指引）。
    行内注释（词首 `#`）与行尾续行由调用方先行处理；此处只做语句解析。
    """
    raw = _strip_comment(line).strip()
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


def banner(baseline: str = "", color: bool = False) -> str:
    """终端开场横幅：版本 + 基线 + 最快上手路径（无时间戳 → 可逐字节复现）。"""
    lines = ["NarrativeForge 终端 v%s（端壳退役后的人机入口；命令真源 = nf CLI）"
             % SHELL_VERSION]
    if baseline:
        lines.append("  基线：%s" % baseline)
    lines += [
        "  数字 0-7 看能力菜单 · /map 能力地图 · /find <词> 检索 · /commands 列全部 · quit 退出",
        "  任意 nf 命令可直接直通（例：nf doctor / nf market --list）；行尾 \\ 可续行",
        "  写入类命令（--write/--apply/--register…）须二次确认，终端不替你拍板",
    ]
    lines[0] = style(lines[0], "head", color)
    return "\n".join(lines)


def menu(width=None, color: bool = False) -> str:
    """渲染能力菜单（人读表 + 可执行示例入口）。"""
    w = term_width(width)
    lines = [style("== NF 能力菜单（端壳七区 → CLI 命令面）==", "head", color), ""]
    for item in ZONES:
        # 键固定 3 显示宽度（0-7），故不补宽——保持 `[0] 标题 —— 摘要` 的既有格式契约
        left = style("[%s]" % item["key"], "cmd", color)
        lines.append("%s %s —— %s"
                     % (left, item["title"], clip(item["summary"], max(20, w - 30))))
    lines += ["",
              "看某区示例：输入编号（如 4）或 /zone 4；执行：把示例里的命令打进终端。"]
    return "\n".join(lines)


def zone_detail(key: str, color: bool = False) -> str:
    """渲染单个能力区的示例命令（未命中键 → 给可用键清单，不抛栈）。"""
    item = zone_by_key(key)
    if item is None:
        return ("未识别的菜单键「%s」（可用键：%s；示例：输入 0 看环境自检）"
                % (key, "、".join(z["key"] for z in ZONES)))
    lines = [style("== [%s] %s ==" % (item["key"], item["title"]), "head", color),
             "  %s" % item["summary"],
             "  示例命令（复制即用）："]
    lines += ["    " + style(ex, "cmd", color) for ex in item["examples"]]
    return "\n".join(lines)


# ---------------------------------------------------------------- 命令面检索
# 「最全功能」的瓶颈不是命令少，而是**找不到**：CLI 有 60+ 顶层命令、70+ 二级子命令，
# 菜单只能覆盖入口。这一节提供确定性检索/列出/纠错，索引由 CLI 侧从 argparse 面派生
# （terminal 不 import scripts/nf.py，保持 core 不反向依赖）。

def _lev(a: str, b: str) -> int:
    """编辑距离（确定性；用于拼错建议）。"""
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def did_you_mean(word: str, names, limit: int = 3) -> list:
    """最近的候选名（距离 ≤3），按（距离, 名称）排序——拼错时给建议而不是甩 usage。"""
    word = str(word or "").strip().lower()
    if not word:
        return []
    scored = [( _lev(word, str(n).lower()), str(n)) for n in names]
    hits = [(d, n) for d, n in scored if d <= 3 and d > 0]
    hits.sort()
    return [n for _d, n in hits[:limit]]


def search(index, query: str, limit: int = 8) -> list:
    """在命令面上检索 → [(score, entry)]（确定性：分数降序、路径升序）。

    打分档（不引入模糊权重谜团，全部可复算）：精确名 100 > 名前缀 80 > 名含 60 >
    摘要含 40 > 名称近似（编辑距离 ≤2）35-5·d。空查询 → 按路径列出前 limit 条。
    """
    q = str(query or "").strip().lower()
    entries = list(index or [])
    if not q:
        return [(0, e) for e in sorted(entries, key=lambda x: str(x.get("path")))[:limit]]
    out = []
    for e in entries:
        path = str(e.get("path") or "")
        low = path.lower()
        head = low.split(" ")[0]
        summary = str(e.get("summary") or "").lower()
        score = 0
        if low == q or head == q:
            score = 100
        elif low.startswith(q) or head.startswith(q):
            score = 80
        elif q in low:
            score = 60
        elif q in summary:
            score = 40
        else:
            d = min(_lev(q, head), _lev(q, low))
            if d <= 2:
                score = 35 - 5 * d
        if score:
            out.append((score, e))
    out.sort(key=lambda x: (-x[0], str(x[1].get("path"))))
    return out[:limit]


def render_search(index, query: str, limit: int = 8, width=None,
                  color: bool = False) -> tuple:
    """渲染检索结果 → (文本, 命中数)。未命中给确定性的下一步指引，不空手而归。"""
    hits = search(index, query, limit=limit)
    if not hits:
        near = did_you_mean(query, [str(e.get("path")).split(" ")[0] for e in index or []])
        tip = ("；你是不是想找：%s" % "、".join(near)) if near else ""
        return ("未命中命令：「%s」%s\n  （用 /commands 列全部命令面；或用 nf --help 看总览）"
                % (query, tip), 0)
    w = term_width(width)
    lines = [style("== 命令检索：「%s」（%d 命中）==" % (query, len(hits)), "head", color)]
    for _score, e in hits:
        lines.append(_row("nf " + str(e.get("path")), str(e.get("summary") or ""), w, color))
    lines.append("  用法：直接输入 `nf <命令> …`；二级见 `nf <命令> --help`")
    return "\n".join(lines), len(hits)


def render_commands(index, filt: str = "", limit: int = 0, width=None,
                    color: bool = False) -> str:
    """列出全部可达命令（可按子串过滤）——把「最全功能」摊开成一张可检视的表。"""
    f = str(filt or "").strip().lower()
    rows = sorted((e for e in index or []
                   if not f or f in str(e.get("path")).lower()
                   or f in str(e.get("summary") or "").lower()),
                  key=lambda e: str(e.get("path")))
    tops = {str(e.get("path")).split(" ")[0] for e in index or []}
    w = term_width(width)
    lines = [style("== nf 命令面（顶层 %d · 含二级 %d 条%s）=="
                   % (len(tops), len(rows), ("，过滤：%s" % filt) if f else ""),
                   "head", color)]
    shown = rows if not limit or int(limit) <= 0 else rows[:int(limit)]
    for e in shown:
        lines.append(_row("nf " + str(e.get("path")), str(e.get("summary") or ""), w, color))
    if len(shown) < len(rows):
        lines.append(style("  … 还有 %d 条（--limit 0 看全部，或加过滤词收敛）"
                           % (len(rows) - len(shown)), "dim", color))
    lines.append("  检索：/find <词>（或 nf shell --search <词>）；菜单：/menu")
    return "\n".join(lines)


def family_table() -> tuple:
    """能力地图真源（终端渲染、`--map`、自检与 check39 共用同一份）。"""
    return FAMILIES


def family_of(cmd: str):
    """某命令所属族；未登记返回 None（自检会把它判成策展缺口）。"""
    name = str(cmd).strip()
    for fam in FAMILIES:
        if name in fam["commands"]:
            return fam
    return None


def render_map(filt: str = "", width=None, color: bool = False) -> str:
    """渲染能力地图（全功能分面）：每族给一句话定位 + 该族命令清单。"""
    f = str(filt or "").strip().lower()
    w = term_width(width)
    lines = [style("== NF 能力地图（%d 族 · 覆盖 CLI 全部顶层命令）==" % len(FAMILIES),
                   "head", color)]
    for fam in FAMILIES:
        cmds = list(fam["commands"])
        hit = (not f) or f in str(fam["id"]).lower() or f in str(fam["name"]).lower() \
            or any(f in c for c in cmds)
        if not hit:
            continue
        lines.append("")
        lines.append("%s %s —— %s"
                     % (style("[%s]" % fam["id"], "cmd", color), fam["name"],
                        clip(fam["summary"], max(20, w - 34))))
        lines.append("    " + style(" · ".join("nf %s" % c for c in cmds), "dim", color))
    lines.append("")
    lines.append("  单族用法：/map <族名或命令片段>；命令详情：/find <词>；逐条列出：/commands")
    return "\n".join(lines)


def self_check(index, commands, root_flags=(), examples=None) -> tuple:
    """终端自检 → (issues, stats)：策展完备性 + 索引覆盖 + 菜单示例可达。

    这是**单源判据**：`nf shell --verify`（给人跑）与 verify check39（给门禁跑）调用同一函数，
    于是「终端自己说没问题」与「门禁说没问题」永远同一套语义。
    """
    issues = []
    commands = {str(c) for c in commands or []}
    index = list(index or [])
    index_paths = {str(e.get("path")) for e in index}
    index_tops = {p.split(" ")[0] for p in index_paths}

    # ① 索引：覆盖全部顶层命令 + 含二级 + 指向真命令
    missing = sorted(commands - index_tops)
    if missing:
        issues.append("索引漏命令：%s（修复指引：索引须由 argparse 面派生）"
                      % "、".join(missing[:5]))
    stray = sorted(index_tops - commands)
    if stray:
        issues.append("索引含不存在的命令：%s（修复指引：核对 _shell_command_index）"
                      % "、".join(stray[:5]))
    if len(index_paths) < 2 * max(len(commands), 1):
        issues.append("索引疑未含二级子命令：%d 条 / 顶层 %d（修复指引：索引须含 `cmd sub`）"
                      % (len(index_paths), len(commands)))
    for path in sorted(index_paths):
        if not str(path).strip():
            issues.append("索引存在空路径条目（修复指引：核对索引派生）")

    # ② 策展：能力族必须恰好分区命令集（不缺 / 不重 / 不虚）
    seen = {}
    for fam in FAMILIES:
        if not fam.get("name") or not fam.get("summary") or not fam.get("commands"):
            issues.append("能力族 %s 缺 name/summary/commands（修复指引：补齐策展字段）"
                          % fam.get("id"))
        for cmd in fam.get("commands") or []:
            if cmd in seen:
                issues.append("命令 %s 同时归入 %s 与 %s（修复指引：一命令只归一族）"
                              % (cmd, seen[cmd], fam.get("id")))
            seen[cmd] = fam.get("id")
            if commands and cmd not in commands:
                issues.append("能力族 %s 含不存在的命令：%s（修复指引：改成真实命令）"
                              % (fam.get("id"), cmd))
    uncurated = sorted(commands - set(seen))
    if uncurated:
        issues.append("未被能力地图策展的命令：%s（修复指引：登记进 FAMILIES——"
                      "「最全功能」= 每个命令都有归属）" % "、".join(uncurated[:8]))

    # ③ 菜单：每条示例必须指向真实命令；键须从 0 连续
    flags = {str(x) for x in root_flags or []}
    ex_total = 0
    for item in ZONES:
        for ex in item["examples"]:
            ex_total += 1
            if not example_resolves(ex, commands, flags):
                issues.append("菜单指向死命令：%s（区 %s）" % (ex, item["id"]))
    keys = [z["key"] for z in ZONES]
    if keys != [str(i) for i in range(len(keys))]:
        issues.append("菜单键不连续：%s（修复指引：从 0 起连续编号）" % keys)

    stats = {"commands": len(commands), "families": len(FAMILIES),
            "index_entries": len(index_paths), "examples": ex_total}
    return issues, stats


# ---------------------------------------------------------------- 补全与历史
# 顶尖 CLI 终端的体感差距主要在这两件：**打一半能补**、**翻得回上一轮**。
# 约束：core 零第三方依赖——`readline` 是 stdlib 但 Windows 无该模块，故补全判据本身
# 做成**纯函数**（任何平台都能用：`/complete <前缀>` 与行尾 Tab 都吃），readline 只在
# 可用时接管（POSIX），不可用则退化为候选列表。

#: 斜杠命令的展示词表（补全用）：只列拉丁规范词，中文别名仍可直接输入
SLASH_HELP = (
    ("menu", "能力菜单"), ("map", "能力地图（8 族）"), ("find", "检索命令面"),
    ("commands", "列出全部命令"), ("zone", "看某能力区示例"), ("help", "CLI 帮助面"),
    ("history", "看历史（可给条数）"), ("complete", "补全（可给前缀）"),
    ("doctor", "环境自检"), ("version", "版本"), ("quit", "退出"),
)


def default_history_path() -> str:
    """历史文件默认落点：`<NF_HOME>/shell_history`（与 Store 同一 home 约定，不落仓库）。"""
    try:
        from core import storage            # 单源：NF_HOME 约定只在 storage 里定义一次
        home = storage.default_home()
    except Exception:                       # 尽力而为：storage 不可用时退回同样口径的字面约定
        home = Path(os.environ.get("NARRATIVE_FORGE_HOME")
                    or (Path.home() / ".NarrativeForge"))
    return str(home / "shell_history")


def load_history(path: str, limit: int = 200) -> list:
    """读历史（尾部 limit 条，跳过空行）；文件不存在返回空表（不报错）。"""
    try:
        with open(path, encoding="utf-8") as fh:
            rows = [ln.rstrip("\n") for ln in fh if ln.strip()]
    except OSError:
        return []
    return rows[-int(limit):] if limit else rows


def append_history(path: str, line: str) -> bool:
    """追加一条历史（跳过空行与「与上一条重复」）；返回是否写入。父目录不存在则创建。"""
    text = str(line).strip()
    if not text:
        return False
    try:
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        prev = load_history(path, limit=1)
        if prev and prev[-1] == text:
            return False
        with open(path, "a", encoding="utf-8", newline="\n") as fh:
            fh.write(text + "\n")
        return True
    except OSError:
        return False


def _restore_msys_partial(text: str) -> str:
    """MSYS/Git-Bash 兼容（**补全面**）：以 `/` 开头的参数会被通行层改写成 `C:/…/ma`。

    与 `parse()` 的还原同判据，但**允许前缀**——补全本来就是打一半：末段若是任一斜杠词的
    前缀就还原成 `/<段>`。只影响补全候选，不改变任何执行语义。
    """
    if "/" not in text and "\\" not in text:
        return text
    head, _, tail = text.partition(" ")
    seg = head.replace("\\", "/").rsplit("/", 1)[-1].lower()
    if seg and any(str(w).startswith(seg) for w in SLASH_WORDS):
        return "/" + seg + ((" " + tail) if tail else "")
    return text


def complete(partial: str, index, limit: int = 20) -> list:
    """补全候选（纯函数，确定性）→ [{"text": …, "note": …}]。

    支持四类前缀：`/`（斜杠命令）、`/map <族>`、`/zone <键>`、`nf <命令>[ <子命令>][ -]`。
    命令/子命令/旗标都从 CLI 的 argparse 索引派生——补全面与命令面永远同源。
    """
    text = str(partial or "")
    stripped = _restore_msys_partial(text.strip())
    entries = list(index or [])
    out = []

    # ① 斜杠命令族
    if stripped.startswith("/"):
        body = stripped[1:]
        head, _, tail = body.partition(" ")
        if head in ("map", "族", "地图") and " " in body:
            for fam in FAMILIES:
                key = str(fam["id"])
                if tail and not (key.startswith(tail) or tail in str(fam["name"])):
                    continue
                out.append({"text": "/map %s" % key, "note": str(fam["name"])})
            return out[:limit]
        if head in ("zone", "z", "区") and " " in body:
            for z in ZONES:
                if tail and not str(z["key"]).startswith(tail):
                    continue
                out.append({"text": "/zone %s" % z["key"], "note": str(z["title"])})
            return out[:limit]
        for word, note in SLASH_HELP:
            if word.startswith(head):
                out.append({"text": "/" + word, "note": note})
        return out[:limit]

    # ② nf 命令面
    has_nf = stripped == "nf" or stripped.startswith("nf ")
    body = stripped[3:].strip() if stripped.startswith("nf ") else stripped
    tokens = body.split()
    base = " ".join(tokens[:-1]) if len(tokens) > 1 else ""
    prefix = tokens[-1] if tokens else ""
    if prefix.startswith("-"):
        resolved = base
        for e in entries:
            if str(e.get("path")) == resolved:
                for flag in e.get("flags") or []:
                    if str(flag).startswith(prefix):
                        out.append({"text": ("nf " if has_nf else "") + resolved + " " + flag,
                                    "note": "旗标"})
                break
        return out[:limit]
    for e in entries:
        path = str(e.get("path"))
        if base:
            if not path.startswith(base + " "):
                continue
            rest = path[len(base) + 1:]
            if " " in rest:
                continue
        else:
            if " " in path:
                continue
        if prefix and not path.startswith(prefix):
            continue
        out.append({"text": ("nf " + path) if has_nf else path,
                    "note": str(e.get("summary") or "")})
    return out[:limit]


def render_completions(partial: str, cands, width=None, color: bool = False) -> str:
    """渲染补全候选（人读）：一行一条，带用途；未命中给下一步指引。"""
    if not cands:
        return ("无补全候选：「%s」（用 /commands 列全部命令、/map 看能力族，"
                "或 /find <词> 检索）" % partial)
    w = term_width(width)
    lines = [style("== 补全：「%s」（%d 条）==" % (partial, len(cands)), "head", color)]
    for c in cands:
        lines.append(_row(str(c.get("text")), str(c.get("note") or ""), w, color))
    return "\n".join(lines)


class Session:
    """终端会话状态机：解析 → 闸门 → 分派，I/O 全部由调用方注入（可离线单测）。

    `runner(argv) -> int` 为命令执行回调（CLI 侧传 `main`）；本类只负责
    「该不该跑 / 跑完怎么记」——保证 core 层不依赖 scripts/nf.py。
    """

    def __init__(self, runner, assume_yes: bool = False, index=None,
                 history_path=None, color=False, width=None, limit=0,
                 color_mode="never", stream=None, session_path=None):
        if not callable(runner):
            raise ValueError("Session 需要可调用的 runner(argv) -> int；"
                             "请传入 scripts/nf.py 的 main（终端不自己执行命令）")
        self._runner = runner
        self.assume_yes = bool(assume_yes)
        self.history = []      # 逐条记录 dict（line/kind/exit/argv/out/err/note）
        self.last_zone = ""
        self.quit = False
        # 命令面索引（由 CLI 侧从 argparse 面派生）：用于检索 / 列命令 / 拼错建议。
        # 缺省 None = 不启用预检（core 单测可完全离线，不依赖 CLI 面）。
        self.index = list(index or [])
        self._tops = {str(e.get("path")).split(" ")[0] for e in self.index}
        # 历史文件（交互态用；None = 不记录）。`--exec` / `--file` 一律不写，保持确定性。
        self.history_path = str(history_path) if history_path else None
        # 视图设置（`/set` 可改）：颜色 / 宽度 / 列表限长。默认无色——非 TTY 逐字节确定。
        self.color = bool(color)
        self.color_mode = str(color_mode or "never")
        self.width = width
        self.limit = int(limit or 0)
        self.stream = stream
        # 会话状态（`--session <file>`）：视图设置 + 上次分区；None = 不持久化
        self.session_path = str(session_path) if session_path else None
        self.active_form = None      # {"form": …, "answers": {…}} —— 写盘表单进行中

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
        # 表单进行中：除 `/cancel` 与 quit 外，输入一律当作**回答**（`k=v` 或按顺序填）
        if self.active_form is not None:
            early = self._handle_form_line(_strip_comment(str(line)).strip())
            if early is not None:
                self.history.append(early)
                return early
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
            rec["note"] = menu(self.width, self.color)
        elif intent.kind == "zone":
            self.last_zone = intent.payload
            rec["note"] = zone_detail(intent.payload, self.color)
        elif intent.kind == "search":
            text, hits = render_search(self.index, intent.payload,
                                       width=self.width, color=self.color)
            rec["note"] = text
            rec["exit"] = 0 if hits else 2
        elif intent.kind == "commands":
            rec["note"] = render_commands(self.index, intent.payload, limit=self.limit,
                                          width=self.width, color=self.color)
        elif intent.kind == "map":
            rec["note"] = render_map(intent.payload, self.width, self.color)
        elif intent.kind == "complete":
            cands = complete(intent.payload, self.index)
            rec["note"] = render_completions(intent.payload, cands,
                                             width=self.width, color=self.color)
            rec["exit"] = 0 if cands else 2
        elif intent.kind == "set":
            text, ok = self._apply_settings(intent.payload)
            rec["note"] = text
            rec["exit"] = 0 if ok else 2
        elif intent.kind == "form":
            if not intent.payload:
                rec["note"] = render_forms("", self.width, self.color)
            else:
                form = form_by_id(intent.payload)
                if form is None:
                    rec.update(exit=2, note="未识别的表单：%s（可用：%s；/form 列全部）"
                               % (intent.payload,
                                  "、".join(str(f["id"]) for f in FORMS)))
                else:
                    self.active_form = {"form": form, "answers": {}}
                    rec["note"] = render_form(form, {}, self.color)
        elif intent.kind == "cancel":
            if self.active_form:
                fid = self.active_form["form"]["id"]
                self.active_form = None
                rec["note"] = "已中止表单 %s（未执行任何写盘动作）" % fid
            else:
                rec.update(exit=2, note="当前没有进行中的表单（/form 列全部表单）")
        elif intent.kind == "history":
            rows = load_history(self.history_path, limit=200) if self.history_path else []
            n = 0
            if str(intent.payload).strip().isdigit():
                n = int(str(intent.payload).strip())
            shown = rows[-n:] if n else rows
            head = ("== 历史（%d 条%s）=="
                    % (len(rows), "（最近 %d 条）" % n if n else ""))
            if not self.history_path:
                rec["note"] = ("未启用历史记录（交互态加 --history <文件> 或去掉 --no-history；"
                               "`--exec`/`--file` 不写历史以保持确定性）")
                rec["exit"] = 2
            elif not shown:
                rec["note"] = head + "\n  （暂无记录）"
            else:
                rec["note"] = "\n".join([head] + ["  %3d  %s" % (i + 1, ln)
                                                  for i, ln in enumerate(shown)])
        elif intent.kind == "unknown":
            rec.update(exit=2, note=("未识别：%s（可用：数字 0-7 看菜单 · /menu · "
                                     "/map · /find <词> · /commands · /help · quit · "
                                     "或直接输入 nf 命令）" % intent.raw))
        else:  # run
            argv = list(intent.payload)
            rec["argv"] = argv
            blocked = BLOCKED_IN_SHELL.get(argv[0]) if argv else None
            unknown = (argv and self._tops and argv[0] not in self._tops
                       and argv[0] not in ("help", "--version", "--help", "-h"))
            if unknown:
                near = did_you_mean(argv[0], sorted(self._tops))
                rec.update(exit=2, note=(
                    "未知命令：%s%s（修复指引：/find <词> 检索命令面，或 /commands 列全部；"
                    "直接跑 `nf --help` 看总览）"
                    % (argv[0], "；你是不是想找：%s" % "、".join(near) if near else "")))
            elif blocked:
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

    def _apply_settings(self, payload: str):
        """`/set [k=v …]` → (文本, ok)：无参数打印当前值，有参数改 color / width / limit。"""
        text, ok = self._set_impl(payload)
        if ok and self.session_path:
            save_session_state(self.session_path, self)
        return text, ok

    def _handle_form_line(self, text: str):
        """表单进行中的一行输入 → 记录 dict（除 `/cancel`/quit 外都算回答）。"""
        form = self.active_form["form"]
        answers = self.active_form["answers"]
        low = text.lower()
        rec = {"line": text, "kind": "form", "exit": 0, "argv": [], "out": "",
               "err": "", "note": ""}
        if text.startswith("/cancel") or low in ("cancel", "取消"):
            self.active_form = None
            rec["note"] = "已中止表单 %s（未执行任何写盘动作）" % form["id"]
            return rec
        if text.startswith("/") and not text.startswith("/form"):
            return None                    # 其它斜杠命令照常走 parse（表单保持挂起）
        if not form_pending(form, answers) and not form_missing(form, answers):
            if low in YES_WORDS:
                try:
                    argv = build_argv(form, answers)
                except ValueError as exc:
                    rec.update(exit=2, note=str(exc))
                    return rec
                self.active_form = None
                code, out, err = self.invoke(argv)
                rec.update(kind="run", argv=argv, exit=code, out=out, err=err)
                return rec
            self.active_form = None
            rec["note"] = ("已取消（未执行）：表单 %s 未提交（重新 /form %s 可再填）"
                           % (form["id"], form["id"]))
            return rec
        return self._answer_form(text)

    def _answer_form(self, text: str):
        """把一行记进表单：`k=v` 指定键，否则按 steps 顺序填下一个未 settle 项。

        空行 = **明确跳过**当前项（记空串），于是可选项也会被逐项问到、而不是被静默略过。
        """
        form = self.active_form["form"]
        answers = self.active_form["answers"]
        steps = list(form.get("steps") or [])
        key, _, val = text.partition("=")
        key = key.strip()
        if val and any(st["key"] == key for st in steps):
            answers[key] = val.strip()
        else:
            pend = [st for st in steps if st["key"] not in answers]
            if not pend:
                return {"line": text, "kind": "form", "exit": 0, "argv": [],
                        "out": "", "err": "",
                        "note": "表单已填完：回答 yes 执行 / no 取消"}
            answers[pend[0]["key"]] = str(text or "").strip()
        return {"line": text, "kind": "form", "exit": 0, "argv": [], "out": "",
                "err": "", "note": render_form(form, answers, self.color)}

    def _set_impl(self, payload: str):
        """`/set` 的实现（无副作用；落盘由 `_apply_settings` 负责）。"""
        bad = []
        for pair in str(payload or "").split():
            key, _, value = pair.partition("=")
            key, value = key.strip().lower(), value.strip()
            if key == "color":
                if value not in ("auto", "always", "never"):
                    bad.append(pair)
                    continue
                self.color_mode = value
                self.color = resolve_color(value, self.stream)
            elif key == "width":
                try:
                    self.width = max(40, int(value)) if value else None
                except ValueError:
                    bad.append(pair)
            elif key == "limit":
                try:
                    self.limit = max(0, int(value))
                except ValueError:
                    bad.append(pair)
            elif value == "":
                pass
            else:
                bad.append(pair)
        lines = ["== 终端设置 ==",
                 "  color = %s（实际着色：%s；`NO_COLOR` 一票否决 auto）"
                 % (self.color_mode, "开" if self.color else "关"),
                 "  width = %s（默认取 COLUMNS，否则 100）" % (self.width or "auto"),
                 "  limit = %s（列表限长；0 = 全部）" % self.limit,
                 "  历史 = %s" % (self.history_path or "关闭"),
                 "  会话 = %s" % (self.session_path or "未持久化（--session <文件> 开启）"),
                 "  用法：/set color=never width=120 limit=40（可只给其中几项）"]
        if bad:
            lines.append("  [FAIL] 无法识别：%s（可用键：color / width / limit）" % "、".join(bad))
        return "\n".join(lines), not bad

    def handle(self, line: str) -> tuple:
        """薄封装：处理一行 → (kind, exit_code, 要打印的文本)。"""
        rec = self.dispatch(line)
        return (rec["kind"], rec["exit"],
                (rec["out"] + rec["err"] + rec["note"]).rstrip("\n"))


def run_session(runner, stdin, stdout, assume_yes: bool = False,
                show_banner: bool = True, baseline: str = "", index=None,
                history_path=None, color=False, width=None, limit=0,
                color_mode="never", session_path=None) -> int:
    r"""交互会话主循环：读一行 → 分派 → 打印 → 直到 quit / EOF。

    写入类命令在交互态**就地追问**（读到 yes 才放行本次）；非交互态仍须 `--yes`。
    返回 0（正常结束）或非 0（会话中有命令失败）——供 CI/脚本判红。

    健壮性（对标顶尖 CLI 终端）：Ctrl-C 只取消当前行、不杀会话；行尾 `\` 续行（多行命令）；
    行尾 Tab = 补全候选；`history_path` 启用跨会话历史（`--exec`/`--file` 不写，保确定性）。
    """
    state, warn = load_session_state(session_path)
    session = Session(runner, assume_yes=assume_yes, index=index,
                      history_path=history_path, color=color, width=width,
                      limit=limit, color_mode=color_mode, stream=stdout,
                      session_path=session_path)
    session.last_zone = str(state.get("last_zone") or "")
    if show_banner:
        stdout.write(banner(baseline, color) + "\n")
        if warn:
            stdout.write("  [WARN] %s\n" % warn)
        stdout.flush()
    worst = 0
    while not session.quit:
        stdout.write(PROMPT)
        stdout.flush()
        try:
            line = stdin.readline()
        except KeyboardInterrupt:      # Ctrl-C 取消当前输入，会话继续（不是退出码 130）
            stdout.write("\n  （已取消当前输入——会话继续；quit 退出）\n")
            stdout.flush()
            continue
        if line == "":                      # EOF（管道/重定向结束）
            stdout.write("\n")
            break
        # 行尾 Tab = 补全（零依赖的「Tab 体感」：任何平台都能用；readline 可用时另有接管）
        if line.rstrip("\n").endswith("\t"):
            partial = _strip_comment(line).rstrip("\n").rstrip("\t")
            stdout.write(render_completions(partial, complete(partial, session.index))
                         + "\n")
            stdout.flush()
            continue
        # 行尾 `\` 续行：长命令/多行输入（续行提示符为 `… `）
        while line.rstrip("\n").endswith("\\"):
            line = line.rstrip("\n")[:-1] + " "
            stdout.write("... ")
            stdout.flush()
            try:
                nxt = stdin.readline()
            except KeyboardInterrupt:
                nxt = ""
            if nxt == "":
                break
            line += nxt
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
        # 只记「真执行过的东西」：空行不入，quit/exit 也不入（否则每条会话都多一行噪音）
        if session.history_path and rec["kind"] not in ("empty", "quit"):
            append_history(session.history_path, rec["line"])
    if session.session_path:
        save_session_state(session.session_path, session)
    return worst


def install_readline(completer_text, history_path=None):
    """可用时接上 readline（POSIX）：Tab 补全 + 历史文件；不可用返回 False（Windows 常态）。

    这是**可选增强**而非依赖：补全判据本身在 `complete()` 里，任何平台都能用。
    """
    try:
        import readline  # noqa: F401  (stdlib；Windows 无该模块)
    except ImportError:
        return False
    try:
        if history_path:
            try:
                readline.read_history_file(history_path)
            except OSError:
                pass
            readline.set_history_length(200)

        def _completer(text, state):
            options = completer_text(text) or []
            if state < len(options):
                return options[state]
            return None

        readline.set_completer(_completer)
        readline.parse_and_bind("tab: complete")
        return True
    except Exception:      # 尽力而为：readline 行为异常时不拖垮终端（缺口由补全命令另报）
        return False


def readline_available() -> bool:
    """只探测 readline 是否可用（不产生副作用——`--verify` 用它报事实，不改当前进程行为）。"""
    try:
        import readline  # noqa: F401
        return True
    except ImportError:
        return False


def _statements(lines) -> list:
    """把脚本/`--exec` 文本切成语句：`;` 与换行都是分隔；`#` 开头为注释。"""
    out = []
    for raw in lines:
        for piece in str(raw).split(";"):
            stmt = piece.strip()
            if stmt and not stmt.startswith("#"):
                out.append(stmt)
    return out


def run_lines(lines, runner, assume_yes: bool = False, as_json: bool = False,
              index=None) -> tuple:
    """逐条执行语句序列 → (exit_code, 文本, 记录)（`--exec` 与脚本文件共用同一条链）。

    记录逐条含 line/kind/exit/argv/out/err —— 既是 CI 判据也是机器面（`--json`）。
    """
    session = Session(runner, assume_yes=assume_yes, index=index)
    records = []
    worst = 0
    for raw in _statements(lines):
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
    out_lines = []
    for rec in records:
        out_lines.append("[nf shell] > %s" % rec["line"])
        body = (rec["out"] + rec["err"] + rec["note"]).rstrip("\n")
        if body:
            out_lines += ["  " + ln for ln in body.splitlines()]
        out_lines.append("  结果：%s（exit=%d）" % (rec["kind"], rec["exit"]))
    return worst, "\n".join(out_lines), records


def run_script(script: str, runner, assume_yes: bool = False,
               as_json: bool = False, index=None) -> tuple:
    """非交互模式：`--exec "命令1; 命令2"` 逐条执行 → (exit_code, 文本, 记录)。

    `;` 与换行都是分隔符；`#` 开头为注释（NF 命令面本身不用分号/井号，故不产生歧义）。
    """
    return run_lines(str(script).splitlines() or [str(script)], runner,
                     assume_yes=assume_yes, as_json=as_json, index=index)


def run_file(path: str, runner, assume_yes: bool = False, as_json: bool = False,
             index=None) -> tuple:
    """脚本文件模式（`nf shell --file tour.nf`）：逐行执行，`#` 注释与空行跳过。

    与 `--exec` 共用同一条执行链（同一 Session / 索引 / 闸门），差别只在语句来源——
    于是「终端里能敲的」与「脚本里能跑的」永远是同一套语义。
    """
    with open(path, encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    return run_lines(lines, runner, assume_yes=assume_yes, as_json=as_json, index=index)
