"""条件先行排布（state-first）：把「状态块」放到资料**之前**的确定性排布纪律。

灵感来源（如实标注）：`arXiv:2609.02702（2026-09-02，预印本）` 报道「条件先行（condition first）
优于条件后置」——把推理轨迹当**任务状态的文本代理**置于长上下文之前。
NF 侧**只取「排布」这一层**：不做模型内部、不假定该结论在 NF 成立、不产任何性能宣称。

三件确定性的事（纯标准库）：
1. `build_state_block(text)`：从产物**确定性提取**状态文本代理（编号清单 / 段落计数 / 要点摘录），
   明确标注「由产物提取，非模型生成」；
2. `reorder(text, mode)`：`front` 条件先行 / `back` 条件后置 / `none` 省略；
3. `check_order(text)`：判据——状态块存在且位于**所有其它二级小节之前**。
"""
from __future__ import annotations

import hashlib
import re
from typing import Dict, List, Tuple

STATE_HEAD = "## 状态块（条件先行摘要）"
_IDS = re.compile(r"\b(?:M\d{2,3}|P\d{2})\b")
_NF = re.compile(r"NF-[A-Za-z0-9-]+")
_SECTION = re.compile(r"^##\s+", re.M)
_BULLET = re.compile(r"^\s*[-*]\s+(.+)$", re.M)


def build_state_block(text: str, max_points: int = 8) -> str:
    """确定性提取状态块（不调模型、不编内容）。"""
    ids = sorted(set(_IDS.findall(text)))
    nfs = sorted(set(_NF.findall(text)))
    sections = len(_SECTION.findall(text))
    bullets = [b.strip() for b in _BULLET.findall(text)]
    lines = [STATE_HEAD, "",
             "> 本块由产物**确定性提取**（非模型生成）——它是该产物的「状态文本代理」，供重读时先对齐状态。",
             "", "| 项 | 值 |", "|---|---|",
             "| 模块/挂载编号 | %s |" % ("、".join(ids) if ids else "（无）"),
             "| NF 编号 | %s |" % ("、".join(nfs) if nfs else "（无）"),
             "| 二级标题数 | %d |" % sections,
             "| 要点行数 | %d |" % len(bullets),
             "| 原文 sha256 | `%s` |" % hashlib.sha256(text.encode("utf-8")).hexdigest()[:16],
             ""]
    if bullets:
        lines += ["**关键设置点（原文摘录，非改写）**：", ""]
        lines += ["- %s" % b[:120] for b in bullets[:max_points]]
        lines += [""]
    return "\n".join(lines)


def strip_state_block(text: str) -> str:
    """去掉已存在的状态块（幂等：重复 reorder 不叠加）。"""
    if STATE_HEAD not in text:
        return text
    head, _, tail = text.partition(STATE_HEAD)
    sep = tail.find("\n---\n")
    if sep >= 0:
        return (head + tail[sep + len("\n---\n"):]).lstrip("\n")
    m = _SECTION.search(tail)
    return (head + tail[m.start():]).lstrip("\n") if m else head


def reorder(text: str, mode: str = "front") -> str:
    """front=条件先行 / back=条件后置 / none=省略。"""
    if mode == "none":
        return text
    body = strip_state_block(text)
    block = build_state_block(body)
    if mode == "front":
        return block + "\n---\n\n" + body
    if mode == "back":
        return body.rstrip("\n") + "\n\n---\n\n" + block
    raise ValueError("mode 只能是 front / back / none：%s" % mode)


def check_order(text: str) -> List[str]:
    """判据：状态块存在且前置（位于所有其它二级小节之前）。"""
    if STATE_HEAD not in text:
        return ["缺状态块——无状态文本代理可前置"]
    pos = text.index(STATE_HEAD)
    before = sum(1 for m in _SECTION.finditer(text)
                 if m.start() < pos and not text.startswith("## 状态块", m.start()))
    return (["状态块未前置：它出现在 %d 个二级小节之后（条件先行要求置于资料之前）" % before]
            if before > 0 else [])


def ab_manifest(text: str) -> Dict[str, Dict[str, object]]:
    """T3 三刺激件清单（只备装置，不执行模型）。"""
    out: Dict[str, Dict[str, object]] = {}
    for mode in ("front", "back", "none"):
        v = reorder(text, mode)
        out[mode] = {"sha256": hashlib.sha256(v.encode("utf-8")).hexdigest(),
                     "chars": len(v), "state_front": not check_order(v)}
    return out


def verify(text: str) -> Tuple[List[str], Dict[str, object]]:
    """产物级自检 → (issues, stats)。"""
    issues = check_order(text)
    block = build_state_block(strip_state_block(text))
    return issues, {"block_chars": len(block), "ab": ab_manifest(text)}
