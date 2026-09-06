"""钢人论证模块（v2.6-A：nf design steelman——可选决策辅助）。

NF 内部**可选装载**模块（默认缺席、零常驻成本）：为决策提供结构化正反论证
工作单（steelman.md）产物 + init/check/ls 工具。论证内容由人/任意 AI 填充
（NF 不接模型）——模块只提供骨架与记录，正是社区版工作流。

设计原则（四原则）：
① 默认缺席——不装不感知、零常驻成本；
② 产物化——论证输出 = 文件 steelman.md，可入库、可追溯、可被未来 AI 重读；
③ 渐进增强——先工具，用出价值再谈机制；
④ LLM 协作友好——骨架 + 记录，内容由人/任意 AI 填充。

schema（steelman.md）：
  frontmatter: decision/date/decider/context/related
  六段: 1 问题重述 / 2 支持侧最强论据 / 3 反对侧最强论据 /
        4 核心变量 / 5 判断与理由 / 6 回退路径
  init 产物含三套引导模板（Prompt A 路线决策 / B 需求收敛 / C 设计评审）。

单一来源纪律：六节标题 = STEELMAN_SECTIONS（init 生成与 check 校验同源，
改常量两端同步）；2/3 节占位条目 = ARG_PLACEHOLDERS（init 预置与 check
精确剔除同源，整行括号包裹的真实内容不会被误判为占位）；4/6 节整行占位 =
SECTION_PLACEHOLDERS（init 预置与 check 精确剔除同源——占位判定只认精确
文本，不用 startswith('<') 前缀代理，尖括号包裹术语的真实内容不会被误判为
未填）。判据导出复用：_LIST_ITEM_RE / count_list_entries / ARG_PLACEHOLDERS
/ SECTION_PLACEHOLDERS 供 core.audit 直接 import（钢人节同文单源），audit
不自持正则或占位副本，跨模块 init 骨架互换/check 复核判定一致。

范围纪律：纯零依赖（L2 惯例，同 variants.py/market_analyzer.py）；
不接 verify（不开新 check）；声明制（steelman_ref）v2.6 不做强制。

用法：
    init_worksheet("是否立项？", context="38 方案")      # → 工作单文本
    check_worksheet(text)                               # → 缺项 warn 列表
    scan_steelman(root)                                 # → 工作单索引
"""
from __future__ import annotations

import datetime as _dt
import re
from pathlib import Path
from typing import Dict, List, Optional

#: 六节标题（顺序即 schema 顺序）——init/check 的单一来源
STEELMAN_SECTIONS: List[str] = [
    "1. 问题重述",
    "2. 支持侧最强论据",
    "3. 反对侧最强论据",
    "4. 核心变量",
    "5. 判断与理由",
    "6. 回退路径",
]

#: 2/3 节 init 预置的占位 bullet（按节号）——check 只按这些精确文本判“未填”
ARG_PLACEHOLDERS: Dict[int, List[str]] = {
    2: ["（论据一：独立成立、不可轻易驳倒）", "（论据二）", "（论据三）"],
    3: ["（论据一：独立成立、不可软化）", "（论据二）", "（论据三）"],
}
_PLACEHOLDER_SET = frozenset(
    p for ph in ARG_PLACEHOLDERS.values() for p in ph)

#: 4/6 节 init 预置的整行占位（按节号）——init 生成与 check 精确剔除同源。
#: 占位判定只认这里列出的精确文本：第 4 节填 `<成本敏感度>` 这类尖括号包裹
#: 的真实内容（≠占位）即视为已填，不会被 startswith('<') 前缀代理误剔。
SECTION_PLACEHOLDERS: Dict[int, str] = {
    4: "<改变结论的那个变量>",
    6: "<判断错了怎么回退>（可选但对 NF 有用）",
}

#: 列表条目形态识别（2/3/5 节内容判据共用）：项目符号（-/*/•）、阿拉伯或
#: 中文数字 + 分隔符（. 、 ． ) ））、括号编号（(1)（一））。「形态」只用来
#: 判断某行是不是列表条目，不参与“是否有实质内容”的判据——空条目（只有
#: 编号/符号、无内容）不计，顿号/中文编号等真实形态照常计入。
#: 小数守卫（对抗验证 RED→GREEN）：阿拉伯数字 + 点号须后随非数字——正文段
#: 如 '1.5 倍成本风险…'（数字+点+数字）是小数，不是编号列表条目，不得误计。
_LIST_ITEM_RE = re.compile(
    r"^(?:"
    r"[-*•]\s+"
    # 中文数字：可接任意分隔符（小数点不会跟在中文数字后，无小数误判）
    r"|(?:[一二三四五六七八九十百]+)\s*[.、．)）]\s*"
    # 阿拉伯数字 + 非点分隔符（、．)）——无小数形态
    r"|(?:\d+)\s*[、．)）]\s*"
    # 阿拉伯数字 + 点号：须后随非数字（排除 '1.5' 类小数/序数点）
    r"|(?:\d+)\s*\.(?!\d)\s*"
    r"|[（(]\s*(?:\d+|[一二三四五六七八九十百]+)\s*[）)]\s*"
    r")(.*)$"
)

#: init 引导模板三套（Prompt A 路线决策 / B 需求收敛 / C 设计评审）
PROMPT_TEMPLATES = {
    "A": "路线决策：两三条路线各列最强论据，再比较核心变量。",
    "B": "需求收敛：重述真实问题（剥离方案），支持=为什么现在做，反对=为什么可缓。",
    "C": "设计评审：支持=该设计不可替代处，反对=耦合/维护/边界风险。",
}


def _heading(num: int) -> str:
    """由 STEELMAN_SECTIONS 生成 '## <序号>. <标题>' 标题行（num 从 1 起）。"""
    return f"## {STEELMAN_SECTIONS[num - 1]}"


def _frontmatter(question: str, context: str, decider: str) -> str:
    return (
        "---\n"
        f"decision: <一句话判断>\n"
        f"date: {_dt.date.today().isoformat()}\n"
        f"decider: {decider or '<人>'}\n"
        f"context: {context or '<方案号/域包名/触发场景>'}\n"
        "related: []\n"
        "---\n"
    )


def init_worksheet(question: str, context: str = "",
                   decider: str = "", path: Optional[Path] = None) -> str:
    """生成空白钢人工作单（含问题重述 + 六段骨架 + 引导模板注释）。

    path 给定时写盘并返回内容；否则仅返回文本（供测试/管道）。
    """
    head = (
        "# 钢人论证工作单\n\n"
        f"> **问题**：{question}\n\n"
        "> 使用引导（三选一，Prompt 原文见文末）：\n"
        "> - Prompt A 路线决策（多路线取舍）\n"
        "> - Prompt B 需求收敛（做不做/何时做）\n"
        "> - Prompt C 设计评审（方案评审）\n\n"
    )
    body = []
    # 1. 问题重述（预填问题，待展开）
    body.append(f"{_heading(1)}\n\n{question}\n\n"
                "> 用最完整方式重述真正要解决的问题（1-3段，不含判断）\n")
    # 2/3. 正反论据各 3 个占位（与 check 精确剔除同源：ARG_PLACEHOLDERS）
    for num in (2, 3):
        items = "\n".join(f"- {t}" for t in ARG_PLACEHOLDERS[num])
        body.append(f"{_heading(num)}\n\n{items}\n")
    # 4. 核心变量（占位 = SECTION_PLACEHOLDERS[4]，check 精确剔除同源）
    body.append(f"{_heading(4)}\n\n{SECTION_PLACEHOLDERS[4]}\n")
    # 5. 判断与理由
    body.append(f"{_heading(5)}\n\n"
                "**判断**：<一句话判断>\n\n"
                "**理由**：\n1. \n2. \n3. \n")
    # 6. 回退路径（占位 = SECTION_PLACEHOLDERS[6]，check 精确剔除同源）
    body.append(f"{_heading(6)}\n\n{SECTION_PLACEHOLDERS[6]}\n")
    templates = "\n".join(
        f"--- Prompt {k} ---\n{v}\n" for k, v in PROMPT_TEMPLATES.items())
    txt = _frontmatter(question, context, decider) + head + "\n".join(body)
    txt += "\n\n## 引导模板（填充后删除本段）\n\n" + templates
    if path is not None:
        path.write_text(txt, encoding="utf-8")
    return txt


def _section_text(text: str, sec_title: str) -> str:
    """取某节标题之后到下一节/EOF 的正文（不含引导注释行与模板段）。"""
    lines = text.splitlines()
    start = None
    for i, ln in enumerate(lines):
        if ln.strip().startswith(f"## {sec_title}"):
            start = i + 1
            break
    if start is None:
        return ""
    out = []
    for ln in lines[start:]:
        s = ln.strip()
        if s.startswith("## ") or s.startswith("--- Prompt"):
            break
        out.append(ln)
    return "\n".join(out)


def count_list_entries(sec_text: str, placeholders=()) -> int:
    """节内有效列表条目数（项目符号/编号均可，_LIST_ITEM_RE 统一识别）。

    单一来源导出（steelman 自身与 core.audit 共用同一实现，防判据双源
    漂移）：只把 placeholders 中的精确占位文本与空条目（只有编号/符号无
    内容）排除在外——列表形态不参与判据：顿号/中文编号/括号编号等真实
    形态照常计数；'1.5 倍' 类小数正文行（非编号条目）不计。
    """
    ph = frozenset(placeholders)
    n = 0
    for ln in sec_text.splitlines():
        m = _LIST_ITEM_RE.match(ln.strip())
        if not m:
            continue
        content = m.group(1).strip()
        if content and content not in ph:
            n += 1
    return n


def _count_list_items(sec_text: str) -> int:
    """2/3 节论据计数（占位剔除 = ARG_PLACEHOLDERS 全集，见 _PLACEHOLDER_SET）。"""
    return count_list_entries(sec_text, _PLACEHOLDER_SET)


def _real_lines(sec_text: str, placeholder: str) -> List[str]:
    """节内「真实内容行」：非空、非引用注释、且不等于该节 init 占位精确文本。

    占位判定只认精确文本（SECTION_PLACEHOLDERS 单一来源）——不用
    startswith('<') 前缀代理：尖括号包裹术语（如 <成本敏感度>）是真实内容，
    不得被误判为该节未填。
    """
    real = []
    for ln in sec_text.splitlines():
        s = ln.strip()
        if not s or s.startswith(">") or s.startswith("#"):
            continue
        if s == placeholder:
            continue
        real.append(s)
    return real


def check_worksheet(text: str) -> List[str]:
    """结构自检：返回缺项 warn 列表（空 = 通过）。

    判据（六节标题单一来源 STEELMAN_SECTIONS，占位单一来源
    ARG_PLACEHOLDERS / SECTION_PLACEHOLDERS）：frontmatter decision/date/
    decider/context 在场；六节标题齐全；问题重述非空；正反论据各 ≥3（剔除
    init 占位后计数）；核心变量非空（占位精确剔除）；判断含理由（≥1 实质
    列表条目理由）；回退路径非空（占位精确剔除）。
    """
    warns: List[str] = []
    fm = text.split("---")[1] if text.startswith("---") else ""
    for key in ("decision:", "date:", "decider:", "context:"):
        if f"{key} " not in fm and key not in fm:
            warns.append(f"frontmatter 缺 {key.strip(':')}")
    lines = text.splitlines()
    for sec in STEELMAN_SECTIONS:
        num = int(sec.split(".", 1)[0])
        if not any(ln.strip().startswith(f"## {sec}") for ln in lines):
            warns.append(f"缺节：{sec}")
            continue
        body = _section_text(text, sec)
        if num == 1:
            real = [ln for ln in body.splitlines()
                    if ln.strip() and not ln.strip().startswith(">")
                    and not ln.strip().startswith("## ")]
            if not real:
                warns.append("问题重述未填（1 节需完整重述问题）")
        elif num in (2, 3):
            if _count_list_items(body) < 3:
                label = "支持侧" if num == 2 else "反对侧"
                warns.append(f"{label}论据 <3 条（{sec} 至少 3 条独立论据）")
        elif num in (4, 6):
            if not _real_lines(body, SECTION_PLACEHOLDERS[num]):
                if num == 4:
                    warns.append("核心变量未填（4 节：改变结论的那个变量）")
                else:
                    warns.append("回退路径未填（6 节）")
        elif num == 5:
            if "**判断**" not in body:
                warns.append("判断缺失（5 节需一句话判断）")
            elif not _has_numbered_reason(body):
                warns.append("判断无理由（5 节需 ≥1 条编号理由）")
    return warns


def _has_numbered_reason(body: str) -> bool:
    """5 节是否有实质编号理由：逐行判「列表条目 + 实质内容」，行内空白不跨行。

    缺陷修正一（RED→GREEN，6df32bc）：原 `re.search(r"^\s*\d+\.\s*\S", body,
    re.M)` 的 `\s*` 可跨行——`1. \n2. `（空理由占位）被误判为有理由。改逐行。
    缺陷修正二（本批）：原判据只认「行首阿拉伯数字加点」一种形态——中文编号
    （一、二、三）、括号编号（（1））、项目符号等真实形态的理由被误报「判断无
    理由」。统一走 _LIST_ITEM_RE：形态只判“是不是条目”，占位守卫不回退——
    仅编号无实质内容（1. / 一、 空行）仍判无理由；内容为 init 占位文本不计。
    """
    for ln in body.splitlines():
        m = _LIST_ITEM_RE.match(ln.strip())
        if not m:
            continue
        content = m.group(1).strip()
        if content and content not in _PLACEHOLDER_SET:
            return True
    return False


def scan_steelman(root) -> List[str]:
    """列出目录下已有钢人工作单（含钢人 frontmatter 的 .md 文件）。返回描述行。"""
    base = Path(root)
    hits = []
    for p in sorted(base.glob("*.md")):
        try:
            head = p.read_text(encoding="utf-8")[:500]
        except OSError:
            continue
        if head.startswith("---") and "decision:" in head and "date:" in head:
            # 提取 context 简述
            m = re.search(r"^context:\s*(.+)$", head, re.M)
            ctx = m.group(1).strip() if m else "-"
            m2 = re.search(r"^decision:\s*(.+)$", head, re.M)
            dec = m2.group(1).strip() if m2 else "-"
            m3 = re.search(r"\*\*问题\*\*：(.+)$", head, re.M)
            q = m3.group(1).strip() if m3 else "-"
            hits.append(f"{p.name}  [context={ctx}]  [decision={dec}]"
                        f"\n    └ 问题: {q}")
    return hits
