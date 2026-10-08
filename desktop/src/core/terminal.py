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

import tempfile
import hashlib
import io
import json
import os
import pprint
import shlex
import sys
import time
from collections import namedtuple
from contextlib import redirect_stderr, redirect_stdout
from functools import lru_cache
from pathlib import Path
from typing import Any

SHELL_VERSION = "1.0.0"

#: 会话提示符（单行、无颜色——重定向到文件时逐字节可读）
PROMPT = "nf> "
#: 退出词（大小写不敏感）
QUIT_WORDS = ("quit", "exit", "q", "退出", "再见")
#: 确认词（写入类命令的显式放行）
YES_WORDS = ("y", "yes", "ok", "是", "确认", "可以")

#: 需要显式确认的写入面标记（命令里出现任一即视为写盘/不可逆动作）
CONFIRM_FLAGS = ("--write", "--apply", "--register", "--force",
                 "--out", "--dest", "--build",
                 # 2026-10-01 补：**写盘但不叫 `--write`** 的三个旗标——按 help 清点「收文件/
                 # 写产物的旗标」时逐个核对 `needs_confirm` 抓到（此前 shell 里可无确认改仓库）：
                 #   `--write-baseline`（nf score 重签回归基线）、`--fix`（nf lint 机械修复
                 #   **就地改源件**）。
                 "--write-baseline", "--fix",
                 # 2026-10-01 三补（**机械枚举全部旗标**后逐条核对写 sink 抓到）：上一轮是
                 # 按「已知写旗标名」清的（`--write*` / `--re-sign` / `--fix`），漏掉了三个
                 # **不带任何 `--write` 语义**却直接改仓库的旗标：
                 #   `nf module types --harvest`  → 写 `protocol/event_registry.json`
                 #   `nf pipeline dryrun --write-advisory` → 写 `protocol/pipeline_advisory.json`
                 #   `nf combine plan --certify`  → 写 `protocol/combo_certificates.json`
                 # 外加一个「写你自己命名的文件」的旗标（与已入闸的 `--out` 同类）：
                 #   `nf assemble … --save <文件>`（可给仓库相对路径 ⇒ 在 shell 粘贴面里能落仓）。
                 "--harvest", "--write-advisory", "--certify", "--save",
                 # 2026-10-03 补（终端面单真值源波）：`nf shell --surface-write` 把终端面真源
                 # 投影成生成件 `tui/_surface.py`——**它写仓库**，故按同一口径登记为写面标记。
                 # 本旗标只属于 `shell` 自身，而 `shell` 在会话内被拒跑（`BLOCKED_IN_SHELL`），
                 # 所以它在闸门里的作用面正是 `needs_confirm` 写明的那条：**文本驱动面**
                 # （`--exec` / `--file` / 交互输入）里出现该旗标即须显式确认；显式 argv 直跑
                 # 与其余写面同待遇（不额外设闸）。表单侧不建追问表，理由见 `FORM_EXEMPT`。
                 "--surface-write")
#: 2026-10-01 清掉 5 个**死条目**（表里有、`nf` 的 argparse 面里没有）：`--tag` / `--push` /
#: `--delete` / `--rm` / `--re-sign`——都是更早版本的残影（`nf release` 如今是 `--fast` / `--plan` / `--freeze [--apply]`；
#: `nf asset baseline` 的重签旗标是 **`--write`**，已被上面那条覆盖，行为面并没有因此漏拦）。
#: 死条目的害处不是漏拦（它们匹配不到任何东西），而是**误导读者的口径**：文档写着「命中
#: `--re-sign` 才需要确认」，读者照着敲只会拿到用法错误。判据见 `test_write_flag_gate`：闸门
#: 三表的每一条都必须真在 argparse 面里（本类问题由它兜住）。
#: 需要显式确认的 (命令, 子命令) 组合（无标记位也写盘的动词）
CONFIRM_VERBS = (("asset", "add"), ("asset", "rm"), ("asset", "deprecate"),
                 ("module", "deprecate"), ("module", "restore"),
                 ("module", "signature"), ("register", ""), ("import", ""),
                 ("rename", ""), ("release", ""),
                 # 2026-09-30 补：这些动词**不带 `--write` 也直接改仓库件**（投影重建 / 生命周期
                 # 流转 / frontmatter 落锚 / 派生新件），此前只在 `CONFIRM_FLAGS` 里找标记位，
                 # 于是 `nf shell --exec "nf library deprecate <id>"` 这类**无标记写盘**漏过闸门。
                 ("pipeline", "new"), ("decisions", "reindex"), ("patterns", "reindex"),
                 ("library", "reindex"), ("library", "deprecate"), ("library", "restore"),
                 ("library", "supersede"), ("library", "attest"),
                 # 2026-10-01 补：`nf approve <对象> --by <人>` 会写**批准记录**
                 # （`protocol/approvals/*.json`）——那是治理/问责产物，且**不带任何写旗标**，
                 # 此前在 shell 里可无确认落一条批准。
                 ("approve", ""),
                 # 2026-10-01 再补（**机械枚举**变异类子命令后逐条核对 `needs_confirm` 抓到）：
                 #   `nf asset restore` 与 `nf asset deprecate` 同型（改台账 + 资产文件头），
                 #   但动词表里只登记了 deprecate ⇒ 恢复方向漏过闸门；
                 #   `nf knowledge transform add|promote` 会写 `protocol/transform_log.json`
                 #   （消化记录），同样不带旗标。
                 ("asset", "restore"), ("knowledge", "transform"),
                 # 2026-10-01 新增 `nf preset` 面时的同步登记：`save` / `rm` / `import` 会改
                 # **本机预设库**（`<NF_HOME>/presets/*.json`）——与 `library deprecate` 同型
                 # （无旗标、直接改状态），`ls` / `show` / `apply` 是只读解析面，不入闸。
                 ("preset", "save"), ("preset", "rm"), ("preset", "import"))
#: 「某命令 + 某旗标」才写盘的组合：同一旗标在别的命令上是只读（`pipeline --all` 只扫不改），
#: 故不能把 `--all` 放进 `CONFIRM_FLAGS`。
#: 「某命令 + 某旗标」才写盘的组合：同一旗标在别的命令上是只读，故不能放进 `CONFIRM_FLAGS`。
#: - `interop --all`：只扫不改（`--all` 在别处是只读全集），只有 interop 的面才是落盘全集；
#: - `assemble --trace` / `--session`：这两个旗标在 `nf knowledge frequency --trace` 与
#:   `nf shell --session` 上是**读/仓外受控**（shell 那条另有「必须绝对路径且不得落仓库内」的
#:   硬闸），只有 `nf assemble` 的这两条会**写你自己命名的文件**（可仓库相对 ⇒ 粘贴面能落仓）。
CONFIRM_FLAG_PAIRS = (("interop", "--all"),
                       ("assemble", "--trace"), ("assemble", "--session"))
#: 会话内不直接执行：长驻/递归/需独占终端的动词 → 给指引
BLOCKED_IN_SHELL = {
    "shell": "终端内不再开终端（避免递归会话）：请另开一个终端窗口运行 nf shell。",
    "serve": "serve 是长驻 MCP 服务（会占住当前终端）：请另开终端运行 "
             "nf serve <快照.json>，本终端可继续用只读命令面。",
    # 2026-10-01 补：`lsp` 与 `serve` **同型**——常驻 stdio 服务，`LspServer.serve()` 是
    # `while True: stdin.readline(...)`，交互会话里跑它会**静默占住终端**（实测：给空 stdin
    # 才立刻退；活终端会一直等帧）。此前只拦了 serve，本条按同一口径补齐。
    "lsp": "lsp 是常驻 stdio 服务（等编辑器发 Content-Length 帧，会占住当前终端）："
           "请由编辑器/IDE 直接拉起（nf lsp），本终端可继续用只读命令面。",
}
#: 别名单源：`nf terminal` 是 `nf shell` 的 argparse 别名（`add_parser("shell",
#: aliases=["terminal"])`）。此前只有 `_cmd_shell` 内部自己认这两个拼写，会话层的
#: `BLOCKED_IN_SHELL` 查不到 `terminal` ⇒ 会**先执行再被 handler 拒**（结果一样，但拦截点晚
#: 一拍）。这里补上别名键、消息仍只有一份（引用同一条），两种拼写都在**执行前**拦下。
BLOCKED_IN_SHELL["terminal"] = BLOCKED_IN_SHELL["shell"]

#: 能力菜单（**单一真源**）：键 / 稳定 id / 标题 / 一句话 / 示例命令（可执行原文）/
#: 动作目录（argv 模板 + 参数槽，供全屏 TUI 物化成可回车执行的动作）。
#: 覆盖端壳退役前 GUI 七区的能力面（导入 / 校验 / 管线 / 生成 / 资产 / 预设 / 社区），
#: 但**只指向既有命令**——新增能力仍须先落 CLI，再登记进本表。
#: 多视图纪律（2026-10-03）：行模式 `nf shell` 渲染 examples / 能力族 / 表单，全屏
#: `tui/nf.py` 渲染 actions，`nf shell --surface --json` 出机器面——三者都是本表的**投影**，
#: 表本身只有这一份（TUI 不再手抄）。投影件 `tui/_surface.py` 由 `nf shell --surface-write`
#: 生成，check39 断言「重算结果与在场件逐字节一致」。
#: 动作字典形态：{"key", "title", "argv", "params", "note"}；参数形态：
#: {"name", "label", "kind": "text"|"path", "required"}——`kind=path` 的参数在 TUI 侧强制过
#: 路径包含性判据（与 core/paths.py 同口径）。
ZONES: tuple[dict[str, Any], ...] = (
    {"key": "0", "id": "doctor", "title": "环境自检",
     "family": "start",
     "summary": "只读体检：仓库件在场 / 解释器可用 / 基线自描述一致性",
     "examples": ("nf doctor",),
     "actions": (
         {"key": "doctor", "title": "只读体检", "argv": ("doctor",), "params": (), "note": ""},
         {"key": "doctor-json", "title": "体检（机器面）", "argv": ("doctor", "--json"),
          "params": (), "note": ""},
     )},
    {"key": "1", "id": "demo", "title": "一键演示世界",
     "family": "start",
     "summary": "P04 轻混全链跑一遍（retrieve→compose→gate→export）并产出 CCV3 卡",
     "examples": ("nf demo",),
     "actions": (
         {"key": "demo", "title": "跑一遍 P04 全链", "argv": ("demo",), "params": (), "note": ""},
     )},
    {"key": "2", "id": "assemble", "title": "需求 → 装配计划",
     "family": "forge",
     "summary": "一句话需求 → 命中预设包或转用户自定义流；--check 验收成品",
     "examples": ("nf assemble \"帮我组装一个西幻生存世界的完整版\"",
                  "nf assemble 西幻生存 --check sample.md"),
     "actions": (
         {"key": "assemble", "title": "一句话→装配计划", "argv": ("assemble", "{need}"),
          "params": ({"name": "need", "label": "需求（一句话）", "kind": "text",
                      "required": True},),
          "note": "产出装配计划文本，不落盘"},
         {"key": "assemble-check", "title": "校验成品文档",
          "argv": ("assemble", "{file}", "--check"),
          "params": ({"name": "file", "label": "成品 .md（仓内路径）", "kind": "path",
                      "required": True},),
          "note": ""},
     )},
    {"key": "3", "id": "run", "title": "全链生产",
     "family": "forge",
     "summary": "选管线与模块 → 装配 → 质量门 → 导出（--seed 装载官方核心 + 社区包）",
     "examples": ("nf run --pipeline community/校园西幻轻混组合包/pipelines/"
                  "P04_轻混装配流管线.md --modules 通用类:M00,轻混类:M91,"
                  "轻混类:M92,通用类:M80 --seed",),
     "actions": (
         {"key": "run", "title": "跑全链管线",
          "argv": ("run", "--pipeline", "{pipeline}", "--modules", "{modules}", "--seed"),
          "params": ({"name": "pipeline", "label": "管线 .md（仓内路径）", "kind": "path",
                      "required": True},
                     {"name": "modules", "label": "模块 full_id（逗号分隔）", "kind": "text",
                      "required": True}),
          "note": ""},
         {"key": "run-check", "title": "管线 dry-run", "argv": ("pipeline", "dryrun", "{pipeline}"),
          "params": ({"name": "pipeline", "label": "管线 .md（仓内路径）", "kind": "path",
                      "required": True},),
          "note": ""},
     )},
    {"key": "4", "id": "validate", "title": "校验与体检",
     "family": "verify",
     "summary": "正文 lint / 状态前置 / 一致性分级 / 模块引用门禁（端壳时代「校验区」）",
     "examples": ("nf lint sample.md", "nf conformance", "nf module verify"),
     "actions": (
         {"key": "conformance", "title": "契约一致性", "argv": ("conformance",), "params": (),
          "note": ""},
         {"key": "layers", "title": "抽象阶梯核验", "argv": ("layers", "--verify"), "params": (),
          "note": ""},
         {"key": "lint", "title": "文档语义体检", "argv": ("lint", "{file}"),
          "params": ({"name": "file", "label": "文档 .md（仓内路径）", "kind": "path",
                      "required": True},),
          "note": ""},
         {"key": "module-verify", "title": "模块门禁", "argv": ("module", "verify"),
          "params": (), "note": ""},
     )},
    {"key": "5", "id": "market", "title": "货架与资产",
     "family": "shelf",
     "summary": "市场浏览（--list）/ 单包详情 / 资产货架 / 供应链台账盘点",
     "examples": ("nf market --list", "nf asset ls", "nf asset inventory"),
     "actions": (
         {"key": "market", "title": "市场货架", "argv": ("market", "--list"), "params": (),
          "note": ""},
         {"key": "asset-ls", "title": "资产清单", "argv": ("asset", "ls"), "params": (), "note": ""},
         {"key": "asset-density", "title": "资产密度", "argv": ("asset", "density"), "params": (),
          "note": ""},
         {"key": "library-search", "title": "馆藏检索", "argv": ("library", "search", "{query}"),
          "params": ({"name": "query", "label": "关键词", "kind": "text", "required": True},),
          "note": ""},
     )},
    {"key": "6", "id": "pipeline", "title": "管线与模块",
     "family": "shelf",
     "summary": "管线派生（new）/ 抽象执行（dryrun）/ 模块状态位与边界签名",
     "examples": ("nf pipeline new --id P07 --name 演示领域管线", "nf module ls"),
     "actions": (
         {"key": "module-ls", "title": "模块清单", "argv": ("module", "ls"), "params": (),
          "note": ""},
         {"key": "patterns-ls", "title": "模式清单", "argv": ("patterns", "ls"), "params": (),
          "note": ""},
         {"key": "stats", "title": "自述数字核对", "argv": ("stats", "--check"), "params": (),
          "note": ""},
         {"key": "stats-write", "title": "自述数字：重写生成区（写盘）",
          "argv": ("stats", "--write"), "params": (),
          "note": "会改仓库文件，须键入 yes 确认"},
     )},
    {"key": "7", "id": "help", "title": "帮助与命令面",
     "family": "meta",
     "summary": "全命令总览与任意子命令帮助（终端内输入 /help 同效）",
     "examples": ("nf --help", "nf help assemble"),
     "actions": (
         {"key": "help", "title": "命令总览", "argv": ("--help",), "params": (), "note": ""},
         {"key": "help-cmd", "title": "看某命令帮助", "argv": ("help", "{cmd}"),
          "params": ({"name": "cmd", "label": "子命令名", "kind": "text", "required": True},),
          "note": ""},
     )},
    # 表单区：**不留动作字面量**——`forms: True` 表示本区的动作由 `FORMS` 投影而来
    # （`zone_action_dicts`），于是「写盘表单」这张真源只有一个（改表即改视图）。
    # 行模式用 `/form <id>` 逐项追问，全屏视图把它物化成可回车动作。
    {"key": "8", "id": "forms", "title": "写盘表单",
     "family": "meta",
     "summary": "会改仓库的动作逐项追问：表单真源 FORMS 的每一张都是一个可执行动作",
     "examples": (),
     "actions": (),
     "forms": True},
)


def form_action_dict(form) -> dict:
    """一张写盘表单 → 动作字典（argv 模板与参数槽逐字取自表单真源，不加第二套语义）。

    参数槽的 `kind` 由步骤自带的 `kind` 决定（`path` = 仓库内路径，视图侧须过包含性判据）；
    步骤没写 `kind` 就是自由文本。`required=False` 的步骤在视图侧对应「留空则连同其旗标一起丢」。
    """
    params = [{"name": str(st["key"]), "label": str(st.get("prompt") or st["key"]),
               "kind": str(st.get("kind") or "text"),
               "required": bool(st.get("required"))}
              for st in form.get("steps") or ()]
    return {"key": str(form["id"]), "title": str(form["title"]),
            "argv": [str(t) for t in form.get("argv") or ()],
            "params": params, "note": str(form.get("summary") or "")}


def zone_action_dicts(zone) -> list:
    """某区的**有效动作表**：显式 `actions`，或（`forms: True` 的区）由 `FORMS` 投影而来。

    单一出处：真源侧自检、投影件与全屏视图都走这里——「表单 → 动作」的映射不许抄第二遍，
    否则表单改了而视图没跟上，正是本波要根除的那类漂移。
    """
    if zone.get("forms"):
        return [form_action_dict(f) for f in FORMS]
    return [dict(a) for a in zone.get("actions") or ()]

#: 一行输入的解析结果：kind ∈ empty/quit/help/menu/zone/run/unknown
Intent = namedtuple("Intent", "kind payload raw")

#: 能力地图（**策展真源**）：把 CLI 的每个顶层命令恰好归入一个能力族。
#: 菜单（0-8）是新手路径；本表是「全功能可见」的完整分面——两者分工不重叠。
#: check39 与 `nf shell --verify` 共用同一判据：族分区必须恰好覆盖命令集（不缺不重不虚）。
FAMILIES: tuple[dict[str, Any], ...] = (
    {"id": "start", "name": "上手与自检",
     "summary": "第一次进 NF：体检、一键演示、自述数字、抽象阶梯",
     "commands": ("doctor", "demo", "stats", "layers")},
    {"id": "forge", "name": "装配与生产",
     "summary": "从需求到产物：装配计划、预设（管线+模块+资产包一次组装）、全链管道、渲染、协议件读写、入库登记",
     "commands": ("assemble", "preset", "run", "render", "spec", "register", "import")},
    {"id": "shelf", "name": "资产与货架",
     "summary": "市场、资产台账、模块生命周期、管线派生、组合引擎、域包工厂、产出形态",
     "commands": ("market", "asset", "module", "pipeline", "combine", "domain",
                  "output", "rename")},
    {"id": "verify", "name": "质检与验证",
     "summary": "正文 lint、一致性报告、断言表、知识签名、评分、差异、解释、状态前置、发布体检与变更日志生成、许可证、遥测",
     "commands": ("lint", "conformance", "assertions", "sig", "score", "diff",
                  "explain", "st-validate", "release", "changelog", "license", "telemetry")},
    {"id": "library", "name": "图书馆与知识",
     "summary": "馆藏存取、双源知识、行话术语、实践包、协议件版本史、引用关系与影响面",
     "commands": ("library", "knowledge", "cognition", "patterns", "rfc",
                  "related", "who-refers", "impact")},
    {"id": "govern", "name": "治理与决策",
     "summary": "决策记录（ADR）、审计、背书、回执、交接、复盘、决策层、评审、构建回路、批准、透明日志、设计审计、语言面（本地化与责任方）",
     "commands": ("decisions", "audit", "attest", "receipts", "handover",
                  "postmortem", "decide", "model", "review", "workloop",
                  "approve", "transparency", "design", "locales")},
    {"id": "integrate", "name": "服务与集成",
     "summary": "MCP 服务面、编辑器面、跑分台、端点契约、互操作导出、指令档路由、事件背书、状态前置、世界模型、模块工具面",
     "commands": ("serve", "lsp", "bench", "endpoint", "interop", "driver",
                  "events", "state-front", "worldmodel", "toolface")},
    {"id": "meta", "name": "命令面与终端",
     "summary": "帮助、补全脚本、终端自身（本命令即在此族）",
     "commands": ("help", "completion", "shell", "terminal", "daemon")},
)

#: 斜杠命令词表（`/` 后首个词）：既是 `/x` 形态的判据，也是 MSYS 还原的判据
SLASH_WORDS: tuple[str, ...] = ("quit", "exit", "q", "help", "?", "menu", "菜单",
               "zone", "z", "区", "doctor", "自检", "version", "ver", "版本",
               "find", "search", "找", "查", "commands", "cmd", "cmds", "命令",
               "map", "families", "族", "地图",
               "history", "hist", "历史", "complete", "补全",
               "set", "settings", "设置",
               "form", "forms", "表单", "cancel", "取消")
SLASH_WORDS = SLASH_WORDS + ("replay", "重放")


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
    if head in ("replay", "重放"):
        # `/replay`（无参数）= 列清单；`/replay n` / `/replay 前缀` = 重放
        return Intent("replay-list" if not tail.strip() else "replay", tail.strip(), raw)
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


@lru_cache(maxsize=4096)
def char_width(ch: str) -> int:
    """单字符显示宽度（CJK/全角/emoji = 2，其余 = 1，控制字符 = 0）。

    带缓存：列表渲染每个字符都要问一次宽度，`--commands`（135 行）这类场景下是热路径；
    字符集有限，4096 项缓存足够覆盖任意一次渲染。
    """
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
    """颜色模式 → 布尔：always / never / auto（auto = 真 TTY 且未设 NO_COLOR）。

    额外尊重 `CLICOLOR_FORCE`（非 "0" 即强制开启 auto 档）——与 `NO_COLOR` 同为业界惯例；
    两者冲突时 `NO_COLOR` 优先（关比开安全）。
    """
    m = str(mode or "auto").strip().lower()
    if m == "always":
        return True
    if m == "never":
        return False
    if os.environ.get("NO_COLOR"):
        return False
    if str(os.environ.get("CLICOLOR_FORCE") or "").strip() not in ("", "0"):
        return True
    try:
        return bool(stream is not None and stream.isatty())
    except Exception:      # 尽力而为：判定不了就按无色（安全侧）
        return False


def highlight(text, needle, on: bool = False) -> str:
    """把命中词包成高亮（**仅着色时**；大小写不敏感，只标第一处，避免满屏噪声）。

    必须在**截断/补位之后**调用：ANSI 转义也算字符宽度，先着色会让列对齐失真。
    """
    body = str(text or "")
    key = str(needle or "")
    if not on or not key:
        return body
    idx = body.lower().find(key.lower())
    if idx < 0:
        return body
    return (body[:idx] + style(body[idx:idx + len(key)], "warn", True)
            + body[idx + len(key):])


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


def _row(left: str, right: str, width: int, color: bool = False,
         hl: str = "") -> str:
    """两列行：左列固定宽度（按显示宽度补），右列按剩余宽度截断（可带命中高亮）。"""
    left_col = 28
    left_txt = pad_to("  " + left, left_col)
    remain = max(20, int(width) - left_col)
    return (style(left_txt, "cmd", color)
            + highlight(clip(right, remain), hl, color))


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

FORMS: tuple[dict[str, Any], ...] = (
    {"id": "deprecate-module", "title": "弃用模块",
     "summary": "把某个模块文件标记为 deprecated（写文件头状态位）",
     "steps": ({"key": "file", "prompt": "模块 md 路径", "required": True, "kind": "path",
                "hint": "如 community/<包>/modules/M97_术语管理.md"},
               {"key": "reason", "prompt": "弃用原因（可空）", "required": False}),
     "argv": ("module", "deprecate", "{file}", "--reason", "{reason}")},
    {"id": "restore-module", "title": "恢复模块",
     "summary": "把 deprecated / retired 的模块恢复为 active",
     "steps": ({"key": "file", "prompt": "模块 md 路径", "required": True, "kind": "path"},),
     "argv": ("module", "restore", "{file}")},
    {"id": "types-write", "title": "补 I/O 类型面",
     "summary": "给有机读契约的模块补 io_types（确定性推导，未命中写 untyped）",
     "steps": (), "argv": ("module", "types", "--write")},
    {"id": "stats-write", "title": "重写自述数字生成区",
     "summary": "按实算重写 README / README.en / llms.txt 统计块与 protocol/repo_stats.json",
     "steps": (), "argv": ("stats", "--write")},
    {"id": "asset-add", "title": "资产入库",
     "summary": "资产文件头写 nf-asset 头 + 台账 append（溯源键表自动生成）",
     "steps": ({"key": "file", "prompt": "资产文件路径（相对 --root）", "required": True,
                "kind": "path"},
               {"key": "key", "prompt": "溯源键（台账内唯一）", "required": True},
               {"key": "source", "prompt": "溯源说明（源文件/区间/登记日期）", "required": True},
               {"key": "root", "prompt": "资产根目录", "required": True, "kind": "path",
                "hint": "如 05_资产库"},
               {"key": "module", "prompt": "消费模块 id（可空）", "required": False},
               {"key": "version", "prompt": "版本位（可空 = 1.0）", "required": False},
               {"key": "tier", "prompt": "货架分级 official/community/experimental（可空）",
                "required": False}),
     "argv": ("asset", "add", "{file}", "--key", "{key}", "--source", "{source}",
              "--root", "{root}", "--module", "{module}", "--version", "{version}",
              "--tier", "{tier}")},
    {"id": "register-apply", "title": "本地登记写回",
     "summary": "protocol.yaml → registry protocols[]（校验全过后只增不删合并写）",
     "steps": ({"key": "pkg_dir", "prompt": "包目录", "required": True, "kind": "path",
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
    # ---- 第二批（2026-10-01）：把「已入闸但没表」的常用写面补成组装式命令 ----
    # 依据：闸门表（CONFIRM_VERBS / CONFIRM_FLAGS / CONFIRM_FLAG_PAIRS）是写面的**穷举真源**，
    # 而表单此前只覆盖其中 8 张 ⇒ 其余写面在终端里只能手敲全参数。本批先补 agent 高频的四类，
    # 其余逐条登记在 `FORM_EXEMPT`（写明「为什么不为它建表」），由判据保证「写面必有去处」。
    {"id": "preset-save", "title": "保存预设", "summary": "把一条装配清单存成本机预设（落在 NF_HOME，非仓库）",
     "steps": ({"key": "name", "prompt": "预设名", "required": True, "hint": "如 西幻生存-最小"},
               {"key": "pipeline", "prompt": "管线 id（可空）", "required": False, "hint": "如 P04"},
               {"key": "modules", "prompt": "模块 full_id，逗号分隔（可空）", "required": False,
                "hint": "如 通用类:M00,轻混类:M91"},
               {"key": "assets", "prompt": "资产包名（可空）", "required": False},
               {"key": "force", "prompt": "要覆盖同名预设就填 --force，否则留空", "required": False}),
     "argv": ("preset", "save", "{name}", "--pipeline", "{pipeline}", "--modules", "{modules}",
              "--assets", "{assets}", "{force}")},
    {"id": "library-deprecate", "title": "馆藏条目弃用",
     "summary": "生命周期流转 → deprecated（不再推荐、仍可读）",
     "steps": ({"key": "entry", "prompt": "馆藏编号", "required": True, "hint": "如 NF-1"},),
     "argv": ("library", "deprecate", "{entry}")},
    {"id": "library-restore", "title": "馆藏条目回退",
     "summary": "生命周期回退 → active", "steps": ({"key": "entry", "prompt": "馆藏编号", "required": True},),
     "argv": ("library", "restore", "{entry}")},
    {"id": "pipeline-new", "title": "派生新管线",
     "summary": "自 P00 骨架派生新管线（改 id/name/领域标签；登记 02 与填层名挂载按 README 三步）",
     "steps": ({"key": "id", "prompt": "新管线 id", "required": True, "hint": "如 P07"},
               {"key": "name", "prompt": "显示名", "required": True, "hint": "如 演示领域管线"},
               {"key": "from", "prompt": "模板管线 md（可空 = 03_管线库/P00…）", "required": False,
                "kind": "path"},
               {"key": "domain", "prompt": "领域标签（可空）", "required": False},
               {"key": "dest", "prompt": "输出路径（可空 = 官方管线位）", "required": False,
                "kind": "path"}),
     "argv": ("pipeline", "new", "--id", "{id}", "--name", "{name}", "--from", "{from}",
              "--domain", "{domain}", "--dest", "{dest}")},
    {"id": "approve-subject", "title": "批准内容绑定",
     "summary": "给被批准对象落一条批准记录（protocol/approvals/*.json）",
     "steps": ({"key": "subject", "prompt": "被批准对象路径（仓库相对）", "required": True,
                "kind": "path"},
               {"key": "by", "prompt": "批准人标识（可空）", "required": False},
               {"key": "note", "prompt": "批准说明（可空）", "required": False}),
     "argv": ("approve", "{subject}", "--by", "{by}", "--note", "{note}")},
)


#: 已入闸但**刻意不建表**的写面 → 理由（逐条点名）。判据：闸门表里的每一项要么有表、要么在这里
#: 有理由，否则红——这样新写面不会「悄悄没有组装式入口」（2026-10-01：表单只覆盖 8/30 个写面，
#: 而没有任何判据盯着这个比例）。
FORM_EXEMPT = {
    "--build": "输出类：`assemble --build` 的产物形态随需求变，一表装不下（闸门仍拦）",
    "--certify": "输出类：`combine plan --certify` 与组合证书绑定，参数由组合面推导",
    "--dest": "输出类：落点随命令而异，手敲路径比填表更快",
    "--fix": "机械修复：`lint --fix` 就地改源件，先跑 `lint` 看清单再决定",
    "--harvest": "登记类：`module types --harvest` 与 I/O 类型面绑定，属批量维护",
    "--out": "输出类：`interop --out` / `attest --out` 等落点由用例决定",
    "--register": "登记类：`import --register` 载荷来自外部件，先落盘再登记",
    "--save": "输出类：`assemble --save` 写用户命名的档案文件",
    "--write-advisory": "输出类：`pipeline dryrun --write-advisory` 写 advisory 台账",
    "--write-baseline": "基线类：`score --write-baseline` 重签回归基线，签发是评审动作",
    "asset deprecate": "货架维护：条目少、动作一次性，`nf asset ls` 后手敲更直接",
    "asset restore": "货架维护：同上（恢复路径带原层级，表单装不下）",
    "asset rm": "货架维护：删除类动作刻意不给一键表（留一步手敲）",
    "decisions reindex": "维护类：全量重建索引，一次一条命令即可",
    "import": "入库类：载荷是外部 SKILL.md / chara.json，路径与来源逐次不同",
    "knowledge transform": "维护类：`knowledge transform` 写 protocol/transform_log.json",
    "library attest": "签名类：要 `--key-file` / `--ssh-key`，密钥路径不该进表单回放",
    "library reindex": "维护类：全量重建索引（改 frontmatter 后跑一次）",
    "library supersede": "生命周期：取代链要指向新条目，取舍由作者判断",
    "module signature": "签名类：`module signature` 要密钥/身份件，同上",
    "patterns reindex": "维护类：实践包索引全量重建",
    "preset import": "本机态：导入要外部文件路径，`,` 与 `--store` 由使用场景决定",
    "preset rm": "本机态：与 `preset ls` 成对，手敲一眼确认删的是哪条",
    "release": "发布类：动词 `release` 改模块发布位，属评审动作",
    "interop --all": "导出类：`interop --all` 一条命令落全量 12 面，无需参数组装",
    "assemble --trace": "遥测类：trace 文件由上一次 `--trace` 产出，路径逐次不同",
    "assemble --session": "会话类：`--session` 要绝对路径且不得落仓库内（硬闸），表单帮不上",
    "--surface-write": "生成器类：`nf shell --surface-write` 把终端面真源投影成生成件，"
                        "落点只有一项且内容由真源确定性重算（`nf shell --surface` 可先看结果），"
                        "逐项追问给不出额外安全边际",
}


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
        from . import atomic_write
        atomic_write.write_text(
            path, json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
        return True
    except OSError:  # 会话落盘失败 ⇒ False（调用方据返回值告警）
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
    if raw.startswith("!"):
        # `!!` = 上一条（剥掉全部前导 `!`）；`!n` = 第 n 条；`!前缀` = 最近一条前缀命中
        return Intent("replay", raw.lstrip("!").strip(), raw)
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
    """判定一条命令是否属于写入/不可逆面（须显式确认才放行）。

    **闸门守的是「文本驱动」的面（2026-10-01 实测后写明）**：交互输入、`nf shell --exec`、
    `nf shell --file` —— 这三条都可能承载**粘贴/注入**进来的文本，机器不替人判断「这行该不该
    跑」。而**显式 argv** 的面不设这道闸：`nf <cmd> …` 直跑与 `nf daemon exec <argv>` 等价于
    操作者自己敲的命令（后者文档即写明「输出/退出码与直跑一致」）。实测对照：
    `nf shell --exec "nf stats --write"` → **exit 2（拒）**、`nf shell --file <含写命令的脚本>`
    → 同（两者加 `--yes` 即显式放行）；`nf daemon exec stats --write` → 照跑。

    **改口径要两边一起改**：谁要动这条边界（例如也给 `daemon exec` 加确认），必须同时更新本
    段说明与 CHANGELOG——不要只改一边，那会让「闸门到底守哪条面」重新变成无人可查的问题。
    """
    if any(tok in CONFIRM_FLAGS for tok in argv):
        return True
    if not argv:
        return False
    head = argv[0]
    sub = argv[1] if len(argv) > 1 and not argv[1].startswith("-") else ""
    if (head, sub) in CONFIRM_VERBS or (head, "") in CONFIRM_VERBS:
        return True
    return any((head, tok) in CONFIRM_FLAG_PAIRS for tok in argv)


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
    lines = ["NinFenz 终端 v%s（端壳退役后的人机入口；命令真源 = nf CLI）"
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
    lines = [style("== NF 能力菜单（%d 区 → CLI 命令面）==" % len(ZONES), "head", color), ""]
    for item in ZONES:
        # 键固定 1 显示宽度（0-9），故不补宽——保持 `[0] 标题 —— 摘要` 的既有格式契约
        left = style("[%s]" % item["key"], "cmd", color)
        lines.append("%s %s —— %s"
                     % (left, item["title"], clip(item["summary"], max(20, w - 30))))
    lines += ["",
              "看某区示例：输入编号（如 4）或 /zone 4；执行：把示例里的命令打进终端。"]
    rest = families_without_zone()
    if rest:
        lines.append("  本菜单是**任务路径**（%d 区）；完整面见 /map（%d 族）。"
                     "未在此列的族：%s（在那几族里用 /find <词> 或 /commands 定位）"
                     % (len(ZONES), len(FAMILIES), "、".join(rest)))
    return "\n".join(lines)


def zone_detail(key: str, color: bool = False) -> str:
    """渲染单个能力区的示例命令（未命中键 → 给可用键清单，不抛栈）。"""
    item = zone_by_key(key)
    if item is None:
        return ("未识别的菜单键「%s」（可用键：%s；示例：输入 0 看环境自检）"
                % (key, "、".join(z["key"] for z in ZONES)))
    lines = [style("== [%s] %s ==" % (item["key"], item["title"]), "head", color),
             "  %s" % item["summary"]]
    if item.get("examples"):
        lines.append("  示例命令（复制即用）：")
        lines += ["    " + style(ex, "cmd", color) for ex in item["examples"]]
    else:
        # 无示例的区（表单区）：列它投影出的动作——行模式用 `/form <id>` 逐项追问
        lines.append("  本区动作（`/form <id>` 逐项追问，或在全屏视图里回车运行）：")
        lines += ["    " + style("/form %s" % act["key"], "cmd", color) + "  —— %s"
                  % act["title"] for act in zone_action_dicts(item)]
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
        lines.append(_row("nf " + str(e.get("path")), str(e.get("summary") or ""), w,
                          color, hl=query))
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


def families_for(filt: str = "") -> list:
    """按过滤词取能力族（渲染与 `--map --json` 共用同一判据，免得两处漂移）。"""
    f = str(filt or "").strip().lower()
    out = []
    for fam in FAMILIES:
        if not f or f in str(fam["id"]).lower() or f in str(fam["name"]).lower() \
                or any(f in c for c in fam["commands"]):
            out.append(fam)
    return out


def zones_of_family(fid: str) -> list:
    """哪些菜单区指向该族（菜单 = 任务路径，族 = 完整面；互标让两者可对照）。"""
    return [str(z["key"]) for z in ZONES if str(z.get("family")) == str(fid)]


def families_without_zone() -> list:
    """没被任何菜单区指向的族（不是缺陷：菜单只是快捷路径，但它们该被**显式**告知）。"""
    used = {str(z.get("family")) for z in ZONES}
    return [str(f["id"]) for f in FAMILIES if str(f["id"]) not in used]


def render_map(filt: str = "", width=None, color: bool = False) -> str:
    """渲染能力地图（全功能分面）：每族给一句话定位 + 该族命令清单。"""
    w = term_width(width)
    lines = [style("== NF 能力地图（%d 族 · 覆盖 CLI 全部顶层命令）==" % len(FAMILIES),
                   "head", color)]
    for fam in families_for(filt):
        cmds = list(fam["commands"])
        lines.append("")
        _zones = zones_of_family(fam["id"])
        lines.append("%s %s —— %s%s"
                     % (style("[%s]" % fam["id"], "cmd", color), fam["name"],
                        clip(fam["summary"], max(20, w - 34)),
                        ("　（菜单快捷区：%s）" % "、".join(_zones)) if _zones
                        else "　（菜单无快捷区——用 /find <词> 或 /commands 定位）"))
        lines.append("    " + style(" · ".join("nf %s" % c for c in cmds), "dim", color))
    lines.append("")
    lines.append("  单族用法：/map <族名或命令片段>；命令详情：/find <词>；逐条列出：/commands")
    return "\n".join(lines)


# ---------------------------------------------------------------- 顶尖 CLI 基线
# 「对标最顶尖 CLI」若只停在观感上，就没法判完成。这一节把它摊成**可复跑的证据表**：
# 每行 = 一项能力 + 一条证据命令（+ 必须出现/必须不出现的片段）；`nf shell --baseline` 逐行跑、
# verify check39 逐行断言——「顶尖」于是是逐条可核的事实。行只许用**仓库内真实存在**的入口
# （argv[0] 必须是 shell），且必须**只读**（不许带写盘旗标）。

#: 基线里的受控临时路径占位：展开为系统临时目录下的固定目录（**仓库之外**，不污染工作区）。
BASELINE_TMP = "{TMP}"

#: 每行证据的**默认延迟预算**（毫秒）：超时即判「效率退化」——把「极致效率」变成门禁。
#: 标定方法：单跑实测（机器空闲）后留 100× 以上余量——轻行实测 ~1-2 ms，预算 300 ms，
#: 既能容忍负载抖动，又能拦住**数量级回归**（例：解析器缓存失效会让轻行从 ~2 ms 涨到 ~300 ms
#: 量级；全命令扫描从 ~0.3 s 涨回 ~11 s，那一行另有 BASELINE_DEEP_MAX_MS 预算兜底）。
BASELINE_DEFAULT_MAX_MS = 300
#: 活体深检行的预算。**2026-09-29 实测重标 2000 → 6000**：该行主成本是**全仓抽象阶梯扫描**
#: （`nf layers --verify` 空闲 ~0.5–1.7 s / 本机满载 2.4–3.7 s），旧注「~320 ms × 6」的前提
#: 已不成立（2000 ms 实余 1.15×、同一棵树一次绿一次红）；6000 ≈ 3.5× 空闲余量，仍拦 ~11 s 级回归。
BASELINE_DEEP_MAX_MS = 6000


def baseline_tmp_dir() -> str:
    """基线探针目录：`<系统临时目录>/nf_baseline`（固定名；**仓库之外**）。

    不用 `mkdtemp`：本环境删目录受限，固定名 + 覆盖写既干净又确定性，不给工作区留件。
    """
    path = os.path.join(tempfile.gettempdir(), "nf_baseline")
    os.makedirs(path, exist_ok=True)
    return path


TERMINAL_BASELINE: tuple[dict[str, Any], ...] = (
    {"id": "discover-commands", "name": "命令面可达（列出全部命令）",
     "argv": ("shell", "--commands", "--no-banner"), "expect": "nf 命令面"},
    {"id": "discover-search", "name": "关键词检索（按用途找命令）",
     "argv": ("shell", "--search", "装配", "--no-banner"), "expect": "命令检索"},
    {"id": "discover-map", "name": "能力地图（全命令按族策展）",
     "argv": ("shell", "--map", "--no-banner"), "expect": "能力地图"},
    {"id": "typo-suggest", "name": "拼错建议（不甩 usage）",
     "argv": ("shell", "--exec", "nf statss", "--no-banner"), "expect": "你是不是想找",
     "expect_exit": 2},
    {"id": "write-gate", "name": "写盘闸门（非交互默认拒跑）",
     "argv": ("shell", "--exec", "nf stats --write", "--no-banner"),
     "expect": "确认", "expect_exit": 2},
    # 2026-09-30 补：**无标记写盘动词**与**命令+旗标**配对的闸门（此前只拦 `--write` 一族）
    {"id": "write-gate-verb", "name": "写盘闸门（无标记动词：library 生命周期）",
     "argv": ("shell", "--exec", "nf library deprecate NF-ZZZ", "--no-banner"),
     "expect": "确认", "expect_exit": 2},
    {"id": "write-gate-reindex", "name": "写盘闸门（投影重建）",
     "argv": ("shell", "--exec", "nf decisions reindex", "--no-banner"),
     "expect": "确认", "expect_exit": 2},
    {"id": "write-gate-pair", "name": "写盘闸门（interop --all 落盘）",
     "argv": ("shell", "--exec", "nf interop --all", "--no-banner"),
     "expect": "确认", "expect_exit": 2},
    {"id": "nested-shell-guard", "name": "递归/长驻拦截（serve/shell）",
     "argv": ("shell", "--exec", "nf shell", "--no-banner"),
     "expect": "另开", "expect_exit": 2},
    {"id": "complete", "name": "补全（命令 / 子命令 / 旗标）",
     "argv": ("shell", "--complete", "nf lay", "--no-banner"), "expect": "nf layers"},
    {"id": "limit-hint", "name": "限长提示（长列表不静默截断）",
     "argv": ("shell", "--commands", "asset", "--limit", "3", "--no-banner"),
     "expect": "还有"},
    {"id": "no-ansi-by-default", "name": "非 TTY 无色（逐字节确定）",
     "argv": ("shell", "--commands", "asset", "--limit", "3", "--no-banner"),
     "forbid": "\x1b"},
    {"id": "script-face", "name": "脚本面（--exec 逐条执行）",
     "argv": ("shell", "--exec", "/zone 0", "--no-banner"), "expect": "环境自检"},
    {"id": "history-replay", "name": "历史重放（!! / !n / !前缀）",
     # 本行主题是「重放机制」，用最轻的真实命令（--version）——避免把 `layers --verify`
     # 那类全仓扫描（~1.5 s/次）的成本记在效率证据上（时间预算是判**机制开销**的）。
     "argv": ("shell", "--exec", "nf --version; !!", "--no-banner"), "expect": "重放"},
    {"id": "history-persist", "name": "历史落盘（交互态写文件）",
     "argv": ("shell", "--history", BASELINE_TMP + "/shell_history", "--no-banner"),
     "stdin": "nf --version\nquit\n",
     "expect": "nf 1.0.1", "expect_file": BASELINE_TMP + "/shell_history"},
    {"id": "session-persist", "name": "会话状态持久化（--session）",
     "argv": ("shell", "--session", BASELINE_TMP + "/shell_session.json",
              "--no-history", "--no-banner"),
     "stdin": "/set width=120\nquit\n",
     "expect": "width = 120", "expect_file": BASELINE_TMP + "/shell_session.json"},
    {"id": "menu-family-crosslink", "name": "菜单↔能力族互标",
     "argv": ("shell", "--exec", "/menu", "--no-banner"), "expect": "未在此列的族"},
    {"id": "form-dry-run", "name": "写盘表单（dry-run 只组装不执行）",
     "argv": ("shell", "--form", "stats-write", "--json", "--no-banner"),
     "expect": '"executed": false'},
    {"id": "machine-face", "name": "机器面（--verify --json 纯 JSON）",
     "argv": ("shell", "--verify", "--json", "--no-banner"),
     "expect": '"kind": "shell-verify"'},
    {"id": "live-selfcheck", "name": "活体自检（真跑一条只读命令）",
     # 同一行承载两条断言：活体档在场 + 全 64 命令逐条 --help 均可调用（只跑一次）
     "argv": ("shell", "--verify", "--deep", "--no-banner"),
     "expect": ("活体", "全命令可调用："), "max_ms": BASELINE_DEEP_MAX_MS},
)

#: 基线的写盘禁令：证据行只许只读（出现这些旗标即视为基线自身违规）
BASELINE_FORBIDDEN_FLAGS = ("--write", "--apply", "--register", "--yes", "--force",
                            "--tag", "--rm", "--delete")


def baseline_table() -> tuple:
    """顶尖 CLI 基线真源（`nf shell --baseline`、check39、测试共用同一份）。"""
    return TERMINAL_BASELINE


def baseline_argv_issues() -> list:
    """基线自身的自洽判据：id 唯一、只走 shell、且证据行只读。"""
    issues = []
    seen = set()
    for row in TERMINAL_BASELINE:
        rid = str(row.get("id"))
        if not rid or rid in seen:
            issues.append("基线行 id 缺失或重复：%s" % rid)
        seen.add(rid)
        argv = [str(a) for a in row.get("argv") or []]
        if not argv or argv[0] != "shell":
            issues.append("基线行 %s 的入口不是 shell：%s" % (rid, argv[:1]))
        if not row.get("expect") and not row.get("forbid"):
            issues.append("基线行 %s 既没 expect 也没 forbid（判不出对错）" % rid)
        for tok in argv:
            if tok in BASELINE_FORBIDDEN_FLAGS:
                issues.append("基线行 %s 带写盘旗标 %s（证据必须只读）" % (rid, tok))
        for tok in argv:
            if BASELINE_TMP in tok and not os.path.isabs(
                    tok.replace(BASELINE_TMP, baseline_tmp_dir())):
                issues.append("基线行 %s 的临时占位展开后不是绝对路径：%s" % (rid, tok))
        if int(row.get("expect_exit", 0)) not in (0, 2):
            issues.append("基线行 %s 的 expect_exit 只许 0 或 2（0 = 该成功，2 = 该被拒）" % rid)
        if int(row.get("expect_exit", 0)) != 0 and not row.get("expect"):
            issues.append("基线行 %s 声明了非零 expect_exit，须给 expect 说明拒跑理由" % rid)
    return issues


def _expect_hits(text: str, expect) -> bool:
    """`expect` 支持单条或多条：多条要求**全部出现**（同一行证据可承载多条断言）。"""
    if not expect:
        return True
    items = expect if isinstance(expect, (list, tuple)) else [expect]
    return all(str(x) in text for x in items)


def run_baseline(runner, rows=None) -> tuple:
    """逐行跑证据命令 → (results, stats)。

    `runner(argv, stdin_text=None) -> (exit_code, 合并输出)`：`stdin` 供交互态证据喂输入，
    `expect_file` 断言某文件**真的落盘**；超预算的行**再测两次取最小**（见 BASELINE_DEEP_MAX_MS）。
    """
    results = []
    for row in (rows or TERMINAL_BASELINE):
        # 注意：**只**对含 `{TMP}` 的项做 normpath——否则 Windows 上会把 `/zone 0` 规整成
        # `\zone 0`，直接打坏斜杠命令（实测踩到：脚本面与菜单行双双判红）。
        argv = []
        for a in row.get("argv") or []:
            item = str(a)
            argv.append(os.path.normpath(item.replace(BASELINE_TMP, baseline_tmp_dir()))
                        if BASELINE_TMP in item else item)
        budget = float(row.get("max_ms", BASELINE_DEFAULT_MAX_MS))
        ms, content_ok = float("inf"), False
        for _ in range(3):                 # bounded retry：只超预算才继续，取最小样本
            t0 = time.perf_counter()
            code, out = runner(argv, row.get("stdin"))
            ms = min(ms, (time.perf_counter() - t0) * 1000.0)
            text = str(out or "")
            _exp_raw = str(row.get("expect_file") or "")
            exp_file = (os.path.normpath(_exp_raw.replace(BASELINE_TMP, baseline_tmp_dir()))
                        if _exp_raw else "")
            content_ok = (code == int(row.get("expect_exit", 0))
                          and _expect_hits(text, row.get("expect"))
                          and (not row.get("forbid") or row["forbid"] not in text)
                          and (not exp_file or os.path.isfile(exp_file)))
            if not content_ok or ms <= budget:
                break
        ok = content_ok and ms <= budget
        results.append({"id": row["id"], "name": row["name"],
                        "argv": argv,
                        "exit": code, "expect_exit": int(row.get("expect_exit", 0)),
                        "ms": round(ms, 1),
                        "max_ms": budget, "content_ok": content_ok,
                        "ok": bool(ok),
                        "expect": row.get("expect") or "",
                        "forbid": row.get("forbid") or "",
                        "expect_file": exp_file})
    stats = {"rows": len(results),
             "passed": sum(1 for r in results if r["ok"]),
             "slowest_ms": max([r["ms"] for r in results] or [0.0]),
             "total_ms": round(sum(r["ms"] for r in results), 1)}
    return results, stats


def portable_rows(results) -> list:
    """把基线结果里的**本机临时路径**还原成 `{TMP}` 占位符（仅供展示/机器面）。

    为什么（2026-10-01 取证）：`run_baseline` 为了让证据命令真跑，把 `{TMP}` 展开成了本机
    临时目录；那份**原始结果**要留着（单测断言展开值、排障要看真实路径），但直接进人读面/
    `--json` 就是**机器绝对路径回吐**（实测 `nf shell --baseline` 与 `--baseline --json` 都在
    打印 `C:\\Users\\<user>\\…`）。故拆开：执行/诊断用原值，**展示用本函数**。
    """
    tmp_now = baseline_tmp_dir()
    out = []
    for r in results or []:
        row = dict(r)
        row["argv"] = [str(a).replace(tmp_now, BASELINE_TMP) for a in r.get("argv") or []]
        f = str(r.get("expect_file") or "")
        row["expect_file"] = f.replace(tmp_now, BASELINE_TMP) if f else ""
        out.append(row)
    return out


def render_baseline(results, stats, width=None, color: bool = False) -> str:  # noqa: ARG001 - 调用契约：nf.py/test 按 width= 传入
    """渲染基线逐行结果（人读）：一行一项能力 + 判定 + 证据命令。"""
    lines = [style("== 顶尖 CLI 基线（%d 项 · 逐条可复跑）==" % stats["rows"], "head", color),
             "  通过 %d/%d · 总耗时 %s ms · 最慢 %s ms（每行有延迟预算，超时即判效率退化）"
             % (stats["passed"], stats["rows"], stats.get("total_ms", "-"),
                stats.get("slowest_ms", "-"))]
    for r in results:
        flag = style("✔" if r["ok"] else "✘", "ok" if r["ok"] else "fail", color)
        lines.append("%s %s %8s ms  nf %s"
                     % (flag, pad_to(r["name"], 30), r.get("ms", "-"),
                        " ".join(r["argv"])))
    lines.append("  单行复跑：直接执行该行的 `nf …`（全部只读，不改仓库）")
    return "\n".join(lines)


def writable_dir_probe(path: str) -> tuple:
    """→ (ok, 说明)：**不落件**地判断某文件落点是否可写（沿祖先上溯到存在的目录再看权限）。

    不用「写一个探针再删」：本环境删目录受限，且探针本身就会留件——「不留件」比「测得准一点点」重要。
    """
    if not path:
        return True, "未启用"
    cur = os.path.dirname(os.path.abspath(path)) or "."
    while cur and not os.path.isdir(cur):
        parent = os.path.dirname(cur)
        if parent == cur:
            break
        cur = parent
    if os.path.isdir(cur) and os.access(cur, os.W_OK):
        return True, "可写（%s）" % cur
    return False, "不可写（%s）" % cur


def deep_check(index, commands, root_flags=(), live_runner=None,
               history_path=None, session_path=None, stream=None,
               pager_ok=None) -> tuple:
    """活体自检 → (issues, stats)：静态面之上再核**本机环境**与**真跑一条只读命令**。

    `nf shell --verify`（静态）与 `--verify --deep`（活体）共用本函数；调用方注入
    `live_runner(argv) -> int`（真实执行一条只读命令）与 `pager_ok`（分页器是否在场）。
    判据只读、不落件：可写性用祖先目录探测，不写探针文件。
    """
    issues, stats = self_check(index, commands, root_flags)
    # 说明：`live_runner` 可能内部走 argparse 的 --help（SystemExit(0)）——统一在此归一，
    # 否则一次 help 就把整个深检打断（实测踩过）。
    def _live(argv):
        if live_runner is None:
            return -1
        try:
            code = live_runner(list(argv))
            return code if isinstance(code, int) else 0
        except SystemExit as exc:
            return exc.code if isinstance(exc.code, int) else 0
        except Exception:
            return 1

    # 活体 ①：真跑一条只读命令（覆盖「命令面真的能跑通」而不是「索引里查得到」）
    if live_runner is not None:
        code = _live(["layers", "--verify"])
        stats["live_command"] = "nf layers --verify"
        stats["live_code"] = code
        if code != 0:
            issues.append("活体自检失败：nf layers --verify 退出码 %s"
                          "（修复指引：直接跑该命令看细分；阶梯件或索引可能已漂移）" % code)
        # 活体 ①b：「最全功能」的可执行层证据——**逐条**跑 `nf <cmd> --help`（只读）
        failed = []
        for cmd in sorted({str(c) for c in (commands or [])}):
            if _live([cmd, "--help"]) != 0:
                failed.append(cmd)
        stats["help_sweep_total"] = len(set(commands or []))
        stats["help_sweep_failed"] = failed
        if failed:
            issues.append("全命令可调用性失败：%s（修复指引：逐条跑 nf <cmd> --help 定位；"
                          "命令面与实况脱钩即「最全」失守）" % "、".join(failed[:6]))
    # 活体 ②：历史 / 会话落点可写（只探测，不落件）
    for label, path in (("历史", history_path), ("会话", session_path)):
        ok, why = writable_dir_probe(path)
        stats["%s落点" % label] = why
        if not ok:
            issues.append("%s落点不可写：%s（修复指引：--history / --session 指向可写目录）"
                          % (label, why))
    # 活体 ③：环境事实（TTY / readline / 分页器）——如实报告，不当判据
    try:
        stats["tty"] = bool(stream is not None and stream.isatty())
    except Exception:      # 尽力而为：判不了就记 False（事实陈述，不影响结论）
        stats["tty"] = False
    stats["readline"] = readline_available()
    stats["pager"] = "在场" if pager_ok else ("不在场" if pager_ok is False else "未探测")
    return issues, stats


def self_check(index, commands, root_flags=(), _examples=None) -> tuple:
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
    seen: dict[str, Any] = {}
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

    # ③ 菜单：每条示例与每个动作必须指向真实命令；键须从 0 连续
    flags = {str(x) for x in root_flags or []}
    ex_total = 0
    act_total = 0
    for item in ZONES:
        for ex in item.get("examples") or ():
            ex_total += 1
            if not example_resolves(ex, commands, flags):
                issues.append("菜单指向死命令：%s（区 %s）" % (ex, item["id"]))
        for act in zone_action_dicts(item):
            act_total += 1
            first = str((act.get("argv") or [""])[0])
            if first.startswith("-"):
                continue                    # 根级旗标（如 `nf --help`）按设计放行
            if commands and first not in commands:
                issues.append("菜单动作指向死命令：nf %s（动作 %s / 区 %s）"
                              "（修复指引：动作 argv 只许用真实 CLI 动词）"
                              % (first, act.get("key"), item.get("id")))
            if not str(act.get("key") or "").strip():
                issues.append("菜单动作缺稳定 key（区 %s）" % item.get("id"))
        if not zone_action_dicts(item):
            issues.append("菜单区缺可执行动作：%s（修复指引：全屏视图的动作面板由 "
                          "zone_action_dicts 物化——显式登记 actions，或标 `forms: True` "
                          "让本区投影写盘表单）" % item.get("id"))
    keys = [z["key"] for z in ZONES]
    if keys != [str(i) for i in range(len(keys))]:
        issues.append("菜单键不连续：%s（修复指引：从 0 起连续编号）" % keys)
    fam_ids = {str(f["id"]) for f in FAMILIES}
    for z in ZONES:
        if str(z.get("family") or "") not in fam_ids:
            issues.append("菜单区 %s 的 family 不在能力族名单：%s"
                          "（修复指引：填 start/forge/shelf/verify/library/govern/integrate/meta）"
                          % (z["id"], z.get("family")))

    stats = {"commands": len(commands), "families": len(FAMILIES),
             "index_entries": len(index_paths), "examples": ex_total,
             "actions": act_total,
             "families_without_zone": families_without_zone()}
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
                    or (Path.home() / ".NinFenz"))
    return str(home / "shell_history")


def load_history(path: str, limit: int = 200) -> list:
    """读历史（尾部 limit 条，跳过空行）；文件不存在返回空表（不报错）。"""
    try:
        with open(path, encoding="utf-8") as fh:
            rows = [ln.rstrip("\n") for ln in fh if ln.strip()]
    except OSError:  # 历史文件缺失/坏件 ⇒ 空历史（等价于首次运行）
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
    except OSError:  # 历史追加失败 ⇒ False（调用方据此告警；历史是便利面）
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
        self.history: list[dict[str, Any]] = []   # 逐条记录 dict（line/kind/exit/argv/out/err/note）
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
        self.active_form: dict[str, Any] | None = None   # {"form": …, "answers": {…}} —— 写盘表单进行中
        # 会话内命令记录（供 `!!` / `!n` / `!前缀` 重放；不含 replay 自身，避免自指）
        self.commands: list[Any] = []   # [(原始行, …)] 只记「能重放」的类别

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

    #: 只读视图类意图（不执行外部命令，只渲染）
    _VIEW_KINDS = ("menu", "zone", "search", "commands", "map", "complete", "replay-list")

    def dispatch(self, line: str, confirmed: bool = False) -> dict:
        """处理一行 → 记录 dict（line/kind/exit/argv/out/err/note）。

        `confirmed=True` 表示调用方已就该行取得使用者放行（交互追问拿到 yes）——写入类
        命令据此放行；`assume_yes`（CLI 的 --yes）是整场会话的显式放行开关。
        """
        early = self._form_preempt(line)
        if early is not None:
            return early
        intent = parse(line)
        rec = {"line": intent.raw, "kind": intent.kind, "exit": 0,
               "argv": [], "out": "", "err": "", "note": ""}
        self._handlers().get(intent.kind, self._run)(intent, rec, confirmed)
        self._record(intent, rec)
        return rec

    def _form_preempt(self, line: str):
        """表单进行中：除 `/cancel` 与 quit 外，输入一律当作**回答**（`k=v` 或按顺序填）。"""
        if self.active_form is None:
            return None
        early = self._handle_form_line(_strip_comment(str(line)).strip())
        if early is not None:
            self.history.append(early)
        return early

    def _record(self, intent, rec: dict) -> None:
        """落历史；能重放的类别记入 `commands`（供 `!!`/`!n`/`!前缀`）。"""
        self.history.append(rec)
        if rec["kind"] in self.REPLAYABLE_KINDS and str(intent.raw).strip():
            self.commands.append(str(intent.raw).strip())

    def _handlers(self) -> dict:
        """意图 → 处理器（**查表**替代 if/elif 链：新增意图只加一行，不改控制流）。"""
        view = self._view
        return {
            "empty": self._h_empty, "quit": self._h_quit, "help": self._h_help,
            "set": self._set_cmd,
            "menu": view, "zone": view, "search": view, "commands": view,
            "map": view, "complete": view, "replay-list": view,
            "form": self._form_cmd, "cancel": self._form_cmd,
            "replay": self._replay, "history": self._history_cmd,
            "unknown": self._unknown,
        }

    def _h_empty(self, intent, rec: dict, confirmed: bool) -> None:
        pass

    def _h_quit(self, intent, rec: dict, confirmed: bool) -> None:
        self.quit = True

    def _h_help(self, intent, rec: dict, confirmed: bool) -> None:
        code, out, err = self.invoke(["help"] + ([intent.payload] if intent.payload else []))
        rec.update(exit=code, out=out, err=err)

    def _view(self, intent, rec: dict, confirmed: bool = False) -> None:
        """只读视图：菜单/分区/检索/命令表/地图/补全/重放清单（不触外部执行）。"""
        kind = intent.kind
        if kind == "menu":
            rec["note"] = menu(self.width, self.color)
        elif kind == "zone":
            self.last_zone = intent.payload
            rec["note"] = zone_detail(intent.payload, self.color)
        elif kind == "search":
            text, hits = render_search(self.index, intent.payload,
                                       width=self.width, color=self.color)
            rec["note"] = text
            rec["exit"] = 0 if hits else 2
        elif kind == "commands":
            rec["note"] = render_commands(self.index, intent.payload, limit=self.limit,
                                          width=self.width, color=self.color)
        elif kind == "map":
            rec["note"] = render_map(intent.payload, self.width, self.color)
        elif kind == "complete":
            cands = complete(intent.payload, self.index)
            rec["note"] = render_completions(intent.payload, cands,
                                             width=self.width, color=self.color)
            rec["exit"] = 0 if cands else 2
        else:  # replay-list
            rec["note"] = self.render_replay_list()

    def _form_cmd(self, intent, rec: dict, confirmed: bool = False) -> None:
        if intent.kind == "cancel":
            self._cancel_form(rec)
        elif not intent.payload:
            rec["note"] = render_forms("", self.width, self.color)
        else:
            self._open_form(intent.payload, rec)

    def _open_form(self, fid: str, rec: dict) -> None:
        form = form_by_id(fid)
        if form is None:
            rec.update(exit=2, note="未识别的表单：%s（可用：%s；/form 列全部）"
                       % (fid, "、".join(str(f["id"]) for f in FORMS)))
            return
        self.active_form = {"form": form, "answers": {}}
        rec["note"] = render_form(form, {}, self.color)

    def _cancel_form(self, rec: dict) -> None:
        if self.active_form:
            fid = self.active_form["form"]["id"]
            self.active_form = None
            rec["note"] = "已中止表单 %s（未执行任何写盘动作）" % fid
        else:
            rec.update(exit=2, note="当前没有进行中的表单（/form 列全部表单）")

    def _replay(self, intent, rec: dict, confirmed: bool) -> None:
        ok, payload = self.resolve_replay(intent.payload)
        if not ok:
            rec.update(exit=2, note=str(payload))
            return
        inner = self.dispatch(payload, confirmed=confirmed)
        rec.update(kind="replay", argv=inner["argv"], exit=inner["exit"],
                   out=inner["out"], err=inner["err"])
        rec["note"] = "重放：%s%s" % (payload, ("\n" + inner["note"])
                                     if inner["note"] else "")

    def _history_cmd(self, intent, rec: dict, confirmed: bool = False) -> None:
        rows = load_history(self.history_path, limit=200) if self.history_path else []
        n = int(str(intent.payload).strip()) if str(intent.payload).strip().isdigit() else 0
        shown = rows[-n:] if n else rows
        head = ("== 历史（%d 条%s）==" % (len(rows), "（最近 %d 条）" % n if n else ""))
        if not self.history_path:
            rec["note"] = ("未启用历史记录（交互态加 --history <文件> 或去掉 --no-history；"
                           "`--exec`/`--file` 不写历史以保持确定性）")
            rec["exit"] = 2
        elif not shown:
            rec["note"] = head + "\n  （暂无记录）"
        else:
            rec["note"] = "\n".join([head] + ["  %3d  %s" % (i + 1, ln)
                                              for i, ln in enumerate(shown)])

    def _unknown(self, intent, rec: dict, confirmed: bool = False) -> None:
        rec.update(exit=2, note=("未识别：%s（可用：数字 0-7 看菜单 · /menu · "
                                 "/map · /find <词> · /commands · /help · quit · "
                                 "或直接输入 nf 命令）" % intent.raw))

    def _set_cmd(self, intent, rec: dict, confirmed: bool = False) -> None:
        text, ok = self._apply_settings(intent.payload)
        rec["note"] = text
        rec["exit"] = 0 if ok else 2

    def _auto_complete(self, argv: list) -> list:
        """效率：**唯一前缀**自动补全（`nf stat` → `nf stats`）——只在恰好一个候选时生效，
        有歧义一律不猜（照旧走未知命令分支给候选）。"""
        if not (argv and self._tops and argv[0] not in self._tops
                and not str(argv[0]).startswith("-")):
            return argv
        cands = sorted(c for c in self._tops if c.startswith(argv[0]))
        return [cands[0]] + argv[1:] if len(cands) == 1 else argv

    def _run_block(self, argv: list, confirmed: bool) -> str:
        """run 分支的拦截面 → 空串表示放行；否则为拒跑说明。"""
        if not argv:
            return ""
        blocked = BLOCKED_IN_SHELL.get(argv[0])
        unknown = (self._tops and argv[0] not in self._tops
                   and argv[0] not in ("help", "--version", "--help", "-h"))
        if unknown:
            near = did_you_mean(argv[0], sorted(self._tops))
            return ("未知命令：%s%s（修复指引：/find <词> 检索命令面，或 /commands 列全部；"
                    "直接跑 `nf --help` 看总览）"
                    % (argv[0], "；你是不是想找：%s" % "、".join(near) if near else ""))
        if blocked:
            return blocked
        if needs_confirm(argv) and not (self.assume_yes or confirmed):
            return ("%s 属于写入/不可逆面——须显式确认：交互会话里输入 yes 放行，"
                    "非交互跑时加 --yes（终端不替使用者拍板）。" % " ".join(argv))
        return ""

    def _run(self, intent, rec: dict, confirmed: bool) -> None:
        argv = list(intent.payload)
        rec["argv"] = argv
        completed = self._auto_complete(argv)
        if completed != argv:
            rec["note"] = "唯一前缀补全：%s → %s" % (argv[0], completed[0])
            argv = completed
            rec["argv"] = argv
        note = self._run_block(argv, confirmed)
        if note:
            rec.update(exit=2, note=note)
            return
        code, out, err = self.invoke(argv)
        rec.update(exit=code, out=out, err=err)

    def _apply_settings(self, payload: str):
        """`/set [k=v …]` → (文本, ok)：改视图设置；成功且开了会话文件时顺手落盘。"""
        text, ok = self._set_impl(payload)
        if ok and self.session_path:
            save_session_state(self.session_path, self)
        return text, ok

    #: 可重放的输入类别（表单追问的中间回答不算——重放它没有意义）
    REPLAYABLE_KINDS = ("run", "set", "commands", "search", "map", "complete", "history")

    def resolve_replay(self, spec: str):
        """解析重放说明 → `(ok, 命令行 | 给用户的说明)`。

        形态：`!!`（上一条）、`!n`（第 n 条，1 起）、`!前缀`（最近一条以该前缀开头）。
        """
        spec = str(spec or "").strip()
        if not self.commands:
            return False, "本次会话还没有可重放的命令（先跑一条；/replay 看清单）"
        if not spec:
            return True, self.commands[-1]
        if spec.isdigit():
            n = int(spec)
            if 1 <= n <= len(self.commands):
                return True, self.commands[n - 1]
            return False, ("重放序号越界：!%s（本次会话共 %d 条；/replay 看清单）"
                           % (spec, len(self.commands)))
        for line in reversed(self.commands):
            if line.startswith(spec):
                return True, line
        return False, ("没有以「%s」开头的历史命令（/replay 看清单；或直接输入该命令）" % spec)

    def render_replay_list(self) -> str:
        """列出可重放命令（编号与 `!n` 一致）。"""
        if not self.commands:
            return "（本次会话还没有可重放的命令）"
        lines = ["== 本次会话命令（%d 条 · 重放：!! / !n / !前缀）==" % len(self.commands)]
        lines += ["  %3d  %s" % (i + 1, ln) for i, ln in enumerate(self.commands)]
        return "\n".join(lines)

    def _handle_form_line(self, text: str):
        """表单进行中的一行输入 → 记录 dict（除 `/cancel`/quit 外都算回答）。"""
        active = self.active_form
        form = active["form"] if active else {}
        answers = active["answers"] if active else {}
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
        active = self.active_form
        form = active["form"] if active else {}
        answers = active["answers"] if active else {}
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
        # 重放行要先解析出目标，写盘闸门才对**真正要跑的那条**生效（fail-closed 不变）
        _need = needs_confirm(intent.payload) if intent.kind == "run" else False
        if intent.kind == "replay" and intent.payload:
            _ok, _resolved = session.resolve_replay(intent.payload)
            if _ok:
                _target = parse(_resolved)
                if _target.kind == "run":
                    _need = needs_confirm(_target.payload)
        if _need and not session.assume_yes:
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
        import readline  # (stdlib；Windows 无该模块)
    except ImportError:
        return False
    try:
        if history_path:
            try:
                readline.read_history_file(history_path)
            except OSError:  # 历史文件读不到（首次运行/权限）⇒ 从空历史开始
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


# ---------------------------------------------------------------- 终端面投影（单真值源 → 多视图）
# 单真值源 = 本模块的策展表（ZONES / FAMILIES / FORMS / 写盘闸门三表 / BLOCKED_IN_SHELL）
#            + `scripts/nf.py` 的 argparse 面（命令的**存在性**）。
# 多视图   = ① 行模式 `nf shell`：菜单示例 / 能力族 / 写盘表单
#            ② 全屏 `tui/nf.py`：动作目录（把 ZONES[].actions 物化成可回车执行的动作）
#            ③ 机器面 `nf shell --surface --json`：给 agent 与门禁的整面快照
#            ④ 生成件 `tui/_surface.py`：全屏视图在源码态与冻结态的**唯一输入**（零 core 依赖）
# 为什么要有这一节：全屏 TUI 冻结成单文件 exe，**不能 import core**，于是曾把命令白名单、
# 写盘闸门与动作目录**各手抄一份**。手抄件的代价当场可见——它漏了 `CONFIRM_FLAG_PAIRS`，
# 即 `nf interop --all` / `nf assemble --trace` 这类「命令 + 旗标才写盘」的面在全屏视图里
# **不确认就执行**；而两份表只在 TUI 自检时比对，平时可以静默漂移。
# 口径：视图只许**投影**真值，不许各自留表；漂移由 check39（生成件逐字节）+ 单测当场判红。

SURFACE_SCHEMA = "nf-terminal-surface/1"
#: 投影件规范落点（`nf shell --surface-write` 的缺省目标，check39 也按这里对账）
SURFACE_MODULE_PATH = "tui/_surface.py"
#: 投影源件（人读元信息；机器判据只认本模块的表 + argparse 面）
SURFACE_SOURCE = {
    "module": "desktop/src/core/terminal.py",
    "tables": ["ZONES", "FAMILIES", "FORMS", "CONFIRM_FLAGS", "CONFIRM_VERBS",
               "CONFIRM_FLAG_PAIRS", "BLOCKED_IN_SHELL"],
    "commands": "scripts/nf.py 的 argparse 面",
}


def _surface_params(items) -> list:
    """参数槽归一：只有这五个字段进投影（视图侧不许私加语义）。"""
    return [{"name": str(p["name"]), "label": str(p.get("label") or p["name"]),
             "kind": str(p.get("kind") or "text"),
             "required": bool(p.get("required", True))}
            for p in items or ()]


def surface_payload(commands=(), root_flags=()) -> dict:
    """终端面机器快照——**唯一**投影源，四个视图都由它派生（JSON 原生类型，可序列化）。

    各节含义：`zones` 能力菜单（含 `actions` 动作目录）/ `families` 能力族策展 /
    `forms` 写盘表单 / `gates` 写盘闸门三表（flags / verbs / pairs）/ `blocked` 会话内
    不直接执行的动词与指引 / `commands`·`root_flags` 来自 argparse 面（存在性真源）。
    `digest` 是除自身外全量的规范摘要——视图侧可用它做一次廉价对账。
    """
    zones = [{"key": str(z["key"]), "id": str(z["id"]), "title": str(z["title"]),
              "family": str(z.get("family") or ""), "summary": str(z.get("summary") or ""),
              "examples": [str(e) for e in z.get("examples") or ()],
              # `forms: True` = 本区动作由 FORMS 投影（视图据此识别表单区，不必猜 id）
              "forms": bool(z.get("forms")),
              "actions": [{"key": str(a["key"]), "title": str(a["title"]),
                           "argv": [str(t) for t in a.get("argv") or ()],
                           "params": _surface_params(a.get("params")),
                           "note": str(a.get("note") or "")}
                          for a in zone_action_dicts(z)]}
             for z in ZONES]
    families = [{"id": str(f["id"]), "name": str(f["name"]),
                 "summary": str(f.get("summary") or ""),
                 "commands": [str(c) for c in f.get("commands") or ()]}
                for f in FAMILIES]
    forms = [{"id": str(f["id"]), "title": str(f["title"]), "summary": str(f.get("summary") or ""),
              "steps": [{"key": str(s["key"]), "prompt": str(s.get("prompt") or ""),
                         "required": bool(s.get("required")),
                         "hint": str(s.get("hint") or "")}
                        for s in f.get("steps") or ()],
              "argv": [str(t) for t in f.get("argv") or ()]}
             for f in FORMS]
    payload = {
        "kind": "nf-terminal-surface",
        "schema": SURFACE_SCHEMA,
        # 拷贝一份：投影是可被调用方改写的数据，不许把模块级常量交出去当可写对象
        "source": {k: (list(v) if isinstance(v, list) else v)
                   for k, v in SURFACE_SOURCE.items()},
        "commands": sorted(str(c) for c in commands or ()),
        "root_flags": sorted(str(f) for f in root_flags or ()),
        "zones": zones,
        "families": families,
        "forms": forms,
        "gates": {"flags": [str(x) for x in CONFIRM_FLAGS],
                  "verbs": [[str(a), str(b)] for a, b in CONFIRM_VERBS],
                  "pairs": [[str(a), str(b)] for a, b in CONFIRM_FLAG_PAIRS]},
        "blocked": {str(k): str(v) for k, v in sorted(BLOCKED_IN_SHELL.items())},
    }
    payload["digest"] = surface_digest(payload)
    return payload


def surface_digest(payload) -> str:
    """投影内容摘要（除 `digest` 自身外全量；键序归一，故与构造顺序无关）。"""
    body = {k: v for k, v in (payload or {}).items() if k != "digest"}
    text = json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


#: 生成件抬头（人读纪律写在件内，免得后人把它当手写表改）
SURFACE_MODULE_HEAD = '''# -*- coding: utf-8 -*-
"""NF 终端面投影（**生成件 · 请勿手改**）。

真源：desktop/src/core/terminal.py 的策展表（ZONES / FAMILIES / FORMS / 写盘闸门三表 /
      BLOCKED_IN_SHELL）+ scripts/nf.py 的 argparse 面（命令存在性）。
生成：python scripts/nf.py shell --surface-write tui/_surface.py
判据：verify check39「投影与真源同步」+ desktop/tests/test_nf_tui.py
——本件被手改、或真源改了没重生成，都会在判据里当场判红（重算后逐字节比对）。
"""'''


def render_surface_module(payload) -> str:
    """把机器快照渲染成可 import 的生成件（确定性：同输入逐字节一致）。"""
    def lit(value):
        return pprint.pformat(value, width=96, sort_dicts=False)

    parts = [SURFACE_MODULE_HEAD, ""]
    for name, key in (("KIND", "kind"), ("SCHEMA", "schema"), ("DIGEST", "digest"),
                      ("SOURCE", "source"), ("COMMANDS", "commands"),
                      ("ROOT_FLAGS", "root_flags")):
        parts.append("%s = %s" % (name, lit(payload[key])))
    for name, key in (("ZONES", "zones"), ("FAMILIES", "families"), ("FORMS", "forms"),
                      ("GATES", "gates"), ("BLOCKED", "blocked")):
        parts.append("")
        parts.append("%s = %s" % (name, lit(payload[key])))
    text = "\n".join(parts).rstrip("\n") + "\n"
    return text.replace("\r\n", "\n")


def surface_module_text(commands=(), root_flags=()) -> str:
    """生成件应有内容（check39 与单测都用它重算，不另存第二份）。"""
    return render_surface_module(surface_payload(commands, root_flags))


def surface_sync_issues(module_text: str, commands=(), root_flags=()) -> list:
    """投影件对账：重算 → 与在场文本逐字节比对；返回问题清单（空 = 同步）。"""
    expected = surface_module_text(commands, root_flags)
    if str(module_text) == expected:
        return []
    got = str(module_text).splitlines()
    want = expected.splitlines()
    where = "（在场 %d 行 / 应为 %d 行）" % (len(got), len(want))
    for i, line in enumerate(want):
        if i >= len(got) or got[i] != line:
            where = "首个不一致在第 %d 行：在场 %r / 应为 %r" % (
                i + 1, (got[i] if i < len(got) else "<缺行>"), line)
            break
    return ["%s 与真源不同步%s（修复指引：python scripts/nf.py shell --surface-write %s）"
            % (SURFACE_MODULE_PATH, where, SURFACE_MODULE_PATH)]


def render_surface(payload, width=None, color: bool = False) -> str:
    """人读面：逐区列出动作与示例条数（机器面用 `--surface --json`）。"""
    w = term_width(width)
    lines = [style("== NF 终端面投影（%s · 命令 %d · 能力族 %d · 表单 %d）=="
                   % (payload.get("schema"), len(payload.get("commands") or []),
                      len(payload.get("families") or []), len(payload.get("forms") or [])),
                   "head", color)]
    for z in payload.get("zones") or []:
        acts = z.get("actions") or []
        lines.append(_row("[%s] %s" % (z["key"], z["title"]),
                          "%s · 动作 %d：%s" % (z.get("family") or "", len(acts),
                                                "、".join(str(a["title"]) for a in acts)),
                          w, color))
    g = payload.get("gates") or {}
    lines.append("  写盘闸门：旗标 %d · 动词 %d · 命令+旗标 %d · 会话内不直跑 %d"
                 % (len(g.get("flags") or []), len(g.get("verbs") or []),
                    len(g.get("pairs") or []), len(payload.get("blocked") or {})))
    lines.append("  四项视图同源：nf shell（示例/族/表单）· tui/nf.py（动作目录）· "
                 "--surface --json（机器面）· %s（生成件）" % SURFACE_MODULE_PATH)
    lines.append("  对账：nf shell --verify（终端自检）· verify check39（投影与真源同步）")
    return "\n".join(lines)
