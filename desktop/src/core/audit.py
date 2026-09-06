"""M_AUDIT 协议设计审计模块（v2.6：nf design audit——决策过程质量）。

NF 内部**可选装载**元模块：审计「协议设计过程本身的质量」——不处理叙事/
技术文档/ERP 内容，只审计"这份设计是怎么被想出来的、有没有盲区"。与
verify/check（内容合规）正交：verify 查"产物对不对"，audit 查"决策过程稳
不稳"。产物 = audit.md（过程档案），与产物文档（存"定了什么"）互补——二者
共存使方案可回溯审计。

三种审计模式（mode）：
- steelman  钢人论证（复用 core.steelman 四步法：重写问题→双向强化→核心
  变量→判断）——升格合并裁决：import core.steelman 而非复制，避免双源漂移；
- blindspot 盲区扫描（Q1 最没把握的事 / Q2 最大的遗漏，各 3-7 项）；
- full      完整审计（钢人 + 双盲区 + 评估结论 + 行动建议）。

核心机制（两条盲区问题，blindspot/full 内置）：
- Q1「你最没有把握的事情是什么？」——反幻觉：迫使交出不自信部分（低置信度
  清单 3-7 项），不假装什么都懂。
- Q2「我最大的遗漏是什么？」——反思维惯性：从 auditor 视角反查没问出口的
  假设、没考虑到的场景（遗漏清单 3-7 项）。
- 缺陷闭环：audit.md 第 7 节缺陷条目 = 下一轮迭代输入（审计→缺陷→修订→再
  审计）。

契约（audit.md schema）：
  frontmatter: mode / target / verdict / date / auditor / related
  verdict 三态: 通过 / 需补充以下信息 / 需重做
  清单边界: 3-7 项（少于 3 = 敷衍，多于 7 = 未收敛）

范围纪律（随升格合并裁决修订）：不 import 仓库外任何依赖 + 不 import core
外模块（允许 import core.steelman——同 composer→variants 互引惯例）；
不进 verify 链（audit 产物不参与门禁计分）；声明制字段统一 audit_ref。

用法：
    init_audit("是否立项？", target="38 方案", mode="full")   # → audit.md 文本
    check_audit(path)                                        # → warn 列表（缺文件返回提示不抛错）
    scan_audit(root)                                         # → 审计记录索引
"""
from __future__ import annotations

import datetime as _dt
import re
from pathlib import Path
from typing import Dict, List, Optional

from .steelman import (  # 升格合并裁决：钢人节判据单一来源——占位文本与条目
    ARG_PLACEHOLDERS,    # 计数（内部走 steelman 的 _LIST_ITEM_RE）全部 import
    SECTION_PLACEHOLDERS,        # core.steelman 复用，不自持正则/占位副本，
    count_list_entries,          # 杜绝双源漂移
)

#: 三种审计模式
AUDIT_MODES: List[str] = ["steelman", "blindspot", "full"]

#: verdict 三态
VERDICTS: List[str] = ["通过", "需补充以下信息", "需重做"]

#: blindspot 清单边界（少于 3 = 敷衍，多于 7 = 未收敛）
LIST_MIN = 3
LIST_MAX = 7

#: audit.md 节标题（full 模式全量；steelman/blindspot 裁剪见 _MODE_SECTIONS）。
#: 说明：audit.md 是独立 schema（计划 §七 七节），steelman mode 的「复用」=
#: 逻辑复用 core.steelman 的问题重述/论据骨架与 check 语义（升格合并裁决），
#: 节号按 audit 七节编排——steelman mode 输出 1 问题重述/2 支持/3 反对/
#: 4 核心变量(钢人 Step3)/5 评估结论/6 行动建议（钢人四步并入，不重复占
#: blindspot 的低置信度/遗漏位）。
AUDIT_SECTIONS: List[str] = [
    "1. 问题重述",
    "2. 支持侧最强论据",
    "3. 反对侧最强论据",
    "4. 核心变量",
    "5. 低置信度清单",
    "6. 遗漏清单",
    "7. 评估结论",
    "8. 行动建议与缺陷条目",
]

#: mode → 输出的节号子集
_MODE_SECTIONS = {
    "steelman": [1, 2, 3, 4, 7, 8],
    "blindspot": [1, 5, 6, 7, 8],
    "full": [1, 2, 3, 4, 5, 6, 7, 8],
}

#: 各节 init 预置的占位条目文本（不含 "- " 前缀）——init 骨架生成与 check
#: 精确剔除**同源**（单一来源：占位判定只认这里列的精确文本，不用 startswith
#: '（' 形状代理——整行括号包裹的真实内容不会被误剔，编号/项目符号形态的
#: 真实条目照常计数）。节 2/3/4（钢人节）**逐字别名** core.steelman 常量
#: （ARG_PLACEHOLDERS / SECTION_PLACEHOLDERS，同文单源而非同义副本）——
#: 跨模块 init 骨架互换/交 core.steelman.check 复核时，同一份占位文本两侧
#: 判定一致，杜绝「audit 计为真实论据 / steelman 计为真实论据」的假绿；节
#: 5/6（盲区清单）为 audit 专属占位。形态正则 _LIST_ITEM_RE 与条目计数
#: count_list_entries 同样来自 core.steelman（见文件头 import）。
_SECTION_PLACEHOLDERS: Dict[int, List[str]] = {
    2: list(ARG_PLACEHOLDERS[2]),
    3: list(ARG_PLACEHOLDERS[3]),
    4: [SECTION_PLACEHOLDERS[4]],
    5: ["（低置信度一：附影响面）", "（低置信度二）", "（低置信度三）"],
    6: ["（遗漏一：没问出口的假设/没考虑到的场景）",
        "（遗漏二）", "（遗漏三）"],
}


def _heading(num: int) -> str:
    return f"## {AUDIT_SECTIONS[num - 1]}"


def _frontmatter(mode: str, target: str, context: str) -> str:
    related = f"related: [{context}]" if context else "related: []"
    return (
        "---\n"
        f"mode: {mode}\n"
        f"target: {target}\n"
        "verdict: <三态之一：通过 / 需补充以下信息 / 需重做>\n"
        f"date: {_dt.date.today().isoformat()}\n"
        "auditor: <人/AI>\n"
        f"{related}\n"
        "---\n"
    )


def _section_body(num: int) -> str:
    """各节 init 骨架（full/裁剪通用）。

    占位条目由 _SECTION_PLACEHOLDERS 生成（与 check 精确剔除同源——单一来源，
    避免 init 预置文本与 check 占位判定双源漂移）。
    """
    if num == 1:
        return ("用最完整方式重述真正要解决的问题（1-3段，不含判断）。\n"
                "> Step1 重写问题：若重述后问题变了，说明初始问题质量低（先修"
                "问题再审方案）。")
    if num == 2:
        items = "\n".join(f"- {t}" for t in _SECTION_PLACEHOLDERS[2])
        return (items + "\n"
                "> 禁'如果…也许…'弱表述、禁'虽然但是'软化表述。")
    if num == 3:
        items = "\n".join(f"- {t}" for t in _SECTION_PLACEHOLDERS[3])
        return (items + "\n"
                "> 反对侧论据不得软化为'只是有点担心'。")
    if num == 4:
        return (_SECTION_PLACEHOLDERS[4][0] + "\n"
                "> Step3：变了结论就该翻转的变量，非影响因素清单；列不出 = "
                "判断未收敛")
    if num == 5:
        items = "\n".join(f"- {t}" for t in _SECTION_PLACEHOLDERS[5])
        return ("**Q1「你最没有把握的事情是什么？」——反幻觉**\n"
                "低置信度清单（3-7 项，少于 3 = 敷衍，多于 7 = 未收敛）：\n"
                + items)
    if num == 6:
        items = "\n".join(f"- {t}" for t in _SECTION_PLACEHOLDERS[6])
        return ("**Q2「我最大的遗漏是什么？我没有意识到什么？」——反思维惯性**\n"
                "遗漏清单（3-7 项，每项标注若不处理会怎样）：\n"
                + items)
    if num == 7:
        return ("**评估结论（三态）**：<通过 / 需补充以下信息 / 需重做>\n\n"
                "**一句话理由**：<结论依据>")
    return ("**下一步行动**：<具体动作>\n\n"
            "**回退路径**：<判断错了怎么回退>\n\n"
            "**本轮缺陷条目（= 下轮迭代输入）**：\n"
            "- （缺陷一）\n- （缺陷二）")


def init_audit(question: str, target: str, mode: str = "full",
               context: str = "", auditor: str = "",
               path: Optional[Path] = None) -> str:
    """生成 audit.md 骨架（含引导问题 + 七节，依 mode 裁剪）。

    steelman mode 复用 core.steelman 的问题重述/正反论据骨架（升格合并）。
    """
    if mode not in AUDIT_MODES:
        raise ValueError(f"未知 audit mode：{mode}（可选 {AUDIT_MODES}）")
    head = (
        "# M_AUDIT 协议设计审计\n\n"
        f"> **被审计对象（target）**：{target}\n"
        f"> **审计问题**：{question}\n\n"
        "> 引导（人-AI 对话脚手架，Q1/Q2 内置）见文末；完成后回填各节。\n"
    )
    sections = []
    for num in _MODE_SECTIONS[mode]:
        sections.append(f"{_heading(num)}\n\n{_section_body(num)}\n")
    txt = _frontmatter(mode, target, context) + "\n" + head + "\n".join(sections)
    txt += _prompt_tail(mode)
    if path is not None:
        path.write_text(txt, encoding="utf-8")
    return txt


def _prompt_tail(mode: str) -> str:
    prompts = [
        "--- Prompt A（路线决策）---\n两三条路线各列最强论据，再比较核心变量。",
        "--- Prompt B（需求收敛）---\n重述真实问题（剥离方案），支持=为什么现在"
        "做，反对=为什么可缓。",
        "--- Prompt C（设计评审）---\n支持=该设计不可替代处，反对=耦合/维护/"
        "边界风险。",
    ]
    qs = ("--- 盲区双问（blindspot/full 内置）---\n"
          "Q1 你最没有把握的事情是什么？（低置信度，3-7 项）\n"
          "Q2 我最大的遗漏是什么？（未意识到的假设/场景，3-7 项）")
    return "\n\n## 引导模板（填充后删除本段）\n\n" + "\n".join(prompts) + \
        ("\n" + qs if mode in ("blindspot", "full") else "")


def _sec_text(text: str, sec_title: str) -> str:
    """取节标题后到下一节/EOF 的正文（不含引导注释/模板段）。"""
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


def _has_content(sec_text: str, placeholder: str) -> bool:
    """节内是否有真实内容行（非空、非引用注释、且不等于该节占位精确文本）。"""
    for ln in sec_text.splitlines():
        s = ln.strip()
        if not s or s.startswith(">") or s.startswith("#"):
            continue
        if s == placeholder:
            continue
        return True
    return False


def validate_list_count(n: int) -> bool:
    """清单条目数合法性（3-7 边界）。"""
    return LIST_MIN <= n <= LIST_MAX


def check_audit(path) -> List[str]:
    """结构自检 audit.md：返回 warn 列表。

    缺文件 → 返回「未审计」提示（非红、不抛错——模块是引导工具非门禁）。
    verdict 合法性、mode 合法性、清单边界、关键节在场均校验。
    """
    p = Path(path)
    if not p.exists():
        return [f"未审计：{p}（nf design audit init 生成 audit.md 后重跑）"]
    try:
        text = p.read_text(encoding="utf-8")
    except OSError as exc:
        return [f"读取失败：{p}（{exc}）"]
    warns: List[str] = []
    fm = text.split("---")[1] if text.startswith("---") else ""
    mode = None
    for key in ("mode:", "target:", "verdict:", "date:", "auditor:"):
        m = re.search(rf"^{key}\s*(.*)$", fm, re.M) if fm else None
        if not m:
            warns.append(f"frontmatter 缺 {key.strip(':')}")
        elif key == "mode:":
            raw = m.group(1).strip()
            mode = raw.strip("<>")
            if mode not in AUDIT_MODES:
                warns.append(f"未知 mode：{raw}（可选 {AUDIT_MODES}）")
        elif key == "verdict:":
            raw = m.group(1).strip()
            v = raw.strip("<>")
            # 占位形态（<三态之一…> 引导提示）视为待填，非非法
            if v.startswith("三态之一") or v in VERDICTS:
                pass
            else:
                warns.append(
                    f"verdict 非法：{raw}（三态：{'/'.join(VERDICTS)}）")
    # 节在场（按 mode 裁剪：仅校验该 mode 应有的节）+ blindspot 清单边界
    for sec in AUDIT_SECTIONS:
        num = int(sec.split(".", 1)[0])
        if mode in AUDIT_MODES and num not in _MODE_SECTIONS[mode]:
            continue  # 该 mode 不输出的节，不要求在场
        if not any(ln.strip().startswith(f"## {sec}")
                   for ln in text.splitlines()):
            warns.append(f"缺节：{sec}")
            continue
        body = _sec_text(text, sec)
        if num in (2, 3) and mode in ("steelman", "full"):
            # 钢人论据判据（复用 core.steelman check 语义：剔除 init 精确占位
            # 后 ≥3 条真实论据；编号/项目符号形态均计入——不做内容形态代理）
            n = count_list_entries(body, _SECTION_PLACEHOLDERS.get(num, ()))
            if n < 3:
                label = "支持侧" if num == 2 else "反对侧"
                warns.append(f"{label}论据不足：{sec} 至少 3 条真实论据"
                             f"（当前 {n} 条）")
        elif num == 4 and mode in ("steelman", "full"):
            # 核心变量判据：非空（剔除 init 精确占位文本，不用尖括号形状代理）
            if not _has_content(body, _SECTION_PLACEHOLDERS[4][0]):
                warns.append("核心变量未填（4 节：改变结论的那个变量）")
        elif num in (5, 6) and mode in ("blindspot", "full", None):
            n = count_list_entries(body, _SECTION_PLACEHOLDERS.get(num, ()))
            if not validate_list_count(n):
                warns.append(f"{'低置信度' if num == 5 else '遗漏'}清单条目"
                             f" {n} 条越界（需 {LIST_MIN}-{LIST_MAX}）")
    return warns


def scan_audit(root) -> List[str]:
    """列出目录下已有 audit.md（含 mode/verdict frontmatter）。"""
    base = Path(root)
    hits = []
    for p in sorted(base.glob("*.md")):
        try:
            head = p.read_text(encoding="utf-8")[:400]
        except OSError:
            continue
        if head.startswith("---") and "mode:" in head and "target:" in head:
            m = re.search(r"^target:\s*(.+)$", head, re.M)
            tgt = m.group(1).strip() if m else "-"
            m2 = re.search(r"^mode:\s*(.+)$", head, re.M)
            mode = m2.group(1).strip() if m2 else "-"
            m3 = re.search(r"^verdict:\s*(.+)$", head, re.M)
            verdict = m3.group(1).strip() if m3 else "-"
            hits.append(f"{p.name}  [mode={mode}]  [verdict={verdict}]"
                        f"\n    └ target: {tgt}")
    return hits
