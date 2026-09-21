"""正文级 lint（内部差距实证：NF 的风格门是 M80 的**档位 DNA 资产**——靠执行方自觉比对，
没有机器可跑的正文检查；仓库全域无正文 lint 件）。

本模块把「风格门」补上**执行侧机检**：对正文段落跑确定性规则，输出可寻址的发现项
（行号 + 规则 + 片段），供 `nf lint --prose` 与 LSP 诊断消费。

规则取向 = 「AI 味」的可判定面（不判文笔好坏，只标机械特征）：
`cliche_open` 陈词滥调开头 / `summary_tail` 总结腔收尾 / `lecture_tone` 说教腔 /
`binary_parallel` 对称句式 / `triple_adj` 四字词堆砌 / `repeat_connector` 段首连接词复用 /
`hedge_overuse` 模糊限定词过密 / `punct_mix` 中英标点混用。

纪律：只报告不阻断（正文质量不由机器判死刑）；规则集可由资产键 `PROSE_LINT` 扩展
（05_资产库/用户自定义），与 NF「风格档位化」同源——不在协议层内嵌固定风格条目。
"""
from __future__ import annotations

import os
import re
from typing import Dict, List, Optional

CLICHES = ("在这个", "随着时代", "众所周知", "不言而喻", "无论如何", "某种程度上",
           "在当今", "如今的社会", "无需多言")
SUMMARY_TAILS = ("总而言之", "综上所述", "总之", "总的来说", "综上")
LECTURE = ("我们应该", "让我们", "请记住", "要知道", "我们必须")
CONNECTORS = ("然而", "与此同时", "值得一提的是", "不仅如此", "更重要的是", "毫无疑问")
HEDGES = ("似乎", "仿佛", "或许", "也许", "可能", "大概", "某种程度上")

#: 触发阈值（可按档位覆盖）
HEDGE_PER_1000 = 12.0
TRIPLE_ADJ_MIN = 3

_BINARY = re.compile(r"不是[^。；\n]{1,20}而是|不仅[^。；\n]{1,20}而且|"
                     r"既要[^。；\n]{1,20}又要")
_QUAD = re.compile(r"(?:[\u4e00-\u9fa5]{4}、){2,}[\u4e00-\u9fa5]{4}")
_PUNCT = re.compile(r"[\u4e00-\u9fa5][,;:!?]")
_FENCE = re.compile(r"^\s*```")

#: 资产扩展槽（存在则并入自定义词表）
CUSTOM_ASSET = "05_资产库/用户自定义/PROSE_LINT.md"


def load_custom_terms(root: str = ".") -> List[str]:
    """读资产槽里的自定义禁用词（每行一个；缺文件 = 空）。"""
    path = os.path.join(root, CUSTOM_ASSET)
    if not os.path.exists(path):
        return []
    terms = []
    with open(path, encoding="utf-8") as fh:
        for ln in fh:
            ln = ln.strip()
            if ln and not ln.startswith(("#", ">", "-", "|")):
                terms.append(ln)
    return terms


def _prose_lines(text: str) -> List[tuple]:
    """正文行 = 非代码围栏内的非结构行（跳过标题/引用/表格/列表/分隔线）。"""
    out, in_fence = [], False
    for i, ln in enumerate(text.splitlines(), 1):
        if _FENCE.match(ln):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        s = ln.strip()
        if not s or s[0] in "#>|" or s.startswith("- ") or s.startswith("* "):
            continue
        if re.match(r"^\d+[.、]", s):
            continue
        out.append((i, s))
    return out


def lint_text(text: str, extra_terms: Optional[List[str]] = None,
              hedge_per_1000: float = HEDGE_PER_1000) -> List[Dict[str, object]]:
    """正文 → 发现项列表 [{rule, line, message, snippet}]（1 基行号）。"""
    out: List[Dict[str, object]] = []
    lines = _prose_lines(text)
    body = "".join(s for _i, s in lines)
    terms = list(CLICHES) + list(extra_terms or [])

    for no, s in lines:
        hit = next((w for w in terms if w in s), None)
        if hit:
            out.append({"rule": "cliche_open", "line": no,
                        "message": "陈词滥调/套话：「%s」" % hit, "snippet": s[:40]})
        tail = next((w for w in SUMMARY_TAILS if w in s), None)
        if tail:
            out.append({"rule": "summary_tail", "line": no,
                        "message": "总结腔：「%s」" % tail, "snippet": s[:40]})
        lec = next((w for w in LECTURE if w in s), None)
        if lec:
            out.append({"rule": "lecture_tone", "line": no,
                        "message": "说教腔：「%s」" % lec, "snippet": s[:40]})
        m = _BINARY.search(s)
        if m:
            out.append({"rule": "binary_parallel", "line": no,
                        "message": "对称句式（AI 腔高发）：%s" % m.group(0)[:20],
                        "snippet": s[:40]})
        q = _QUAD.search(s)
        if q and q.group(0).count("、") + 1 >= TRIPLE_ADJ_MIN:
            out.append({"rule": "triple_adj", "line": no,
                        "message": "四字词堆砌（≥%d 连）：%s"
                                   % (TRIPLE_ADJ_MIN, q.group(0)[:24]),
                        "snippet": s[:40]})
        p = _PUNCT.search(s)
        if p:
            out.append({"rule": "punct_mix", "line": no,
                        "message": "中英标点混用：%s" % p.group(0), "snippet": s[:40]})

    starts = [s[:4] for _no, s in lines]
    for c in CONNECTORS:
        hits = [i for i, st in enumerate(starts) if st.startswith(c)]
        if len(hits) >= 2:
            out.append({"rule": "repeat_connector", "line": lines[hits[1]][0],
                        "message": "段首连接词复用 %d 次：「%s」" % (len(hits), c),
                        "snippet": c})

    if body:
        n_hedge = sum(body.count(w) for w in HEDGES)
        per_1k = n_hedge * 1000.0 / max(1, len(body))
        if per_1k > hedge_per_1000:
            out.append({"rule": "hedge_overuse", "line": 0,
                        "message": "模糊限定词过密：%.1f 次/千字（阈值 %.1f）"
                                   % (per_1k, hedge_per_1000), "snippet": ""})
    out.sort(key=lambda f: (f["line"], f["rule"]))
    return out


def summarize(findings: List[Dict[str, object]]) -> Dict[str, int]:
    """按规则计数（便于门禁/报告聚合）。"""
    counts: Dict[str, int] = {}
    for f in findings:
        counts[f["rule"]] = counts.get(f["rule"], 0) + 1
    return counts


#: 命令面一致性扫描范围（入口文档 + 协议件 + 使用面 docs）
FACE_DOCS = ("README.md", "README.en.md", "ROUTES.md", "AGENT_START.md",
             "AI_ROUTING.md", "agent_组装指令包_v0.2.md", "llms.txt",
             "01_核心协议.md", "02_联动注册表.md", "06_Agent执行协议.md",
             "07_官方核心出厂与社区预设导航.md")
_CODE_SPAN = re.compile(r"`([^`\n]+)`")
_FENCE_BLOCK = re.compile(r"```[a-zA-Z0-9]*\n(.*?)```", re.S)
_NF_CALL = re.compile(r"\b(?:nf|nf\.py)\s+([a-z][a-z0-9-]*)")
_MCP_TOOL_MENTION = re.compile(r"([a-z][a-z0-9_]{2,})（MCP 工具）")


def _command_snippets(text: str) -> List[str]:
    """只取**当作命令呈现**的片段：行内代码 + 围栏代码块（避免把散文误判成命令）。"""
    out = [m.group(1) for m in _CODE_SPAN.finditer(text)]
    out += [m.group(1) for m in _FENCE_BLOCK.finditer(text)]
    return out


def command_face(root: str = ".") -> tuple:
    """文档命令面 ↔ CLI 注册表 / MCP 工具表一致性（外部标准净吸收：文档即接口面）。

    内部差距：`protocol/driver.json` 只锚定**指令档**（组装指令包 / AI_ROUTING / ai-menu）
    的机器面路由；README、ROUTES、07 导航、docs/** 里写的 `nf <子命令>` 与 MCP 工具名
    **无判据**——写错一个子命令（改名的残留）读者按文档执行即失败，门禁一条都不会红。
    判据只看「当作命令呈现的片段」（行内代码 / 围栏块），不判散文里的自然语言词。
    """
    import glob
    nf_path = os.path.join(root, "scripts", "nf.py")
    cmds = set()
    if os.path.exists(nf_path):
        with open(nf_path, encoding="utf-8") as fh:
            cmds = set(re.findall(r'sub\.add_parser\(\s*"([a-z0-9-]+)"', fh.read()))
    try:
        import sys
        sys.path.insert(0, os.path.join(root, "desktop", "src"))
        from core.mcp_runtime import TOOL_DEFS  # noqa: PLC0415
        tools = {t["name"] for t in TOOL_DEFS}
    except Exception:  # pragma: no cover - 工具表不可读即跳过工具面
        tools = set()
    docs = [d for d in FACE_DOCS if os.path.exists(os.path.join(root, d))]
    docs += sorted(os.path.relpath(p, root).replace(os.sep, "/")
                   for p in glob.glob(os.path.join(root, "docs", "*.md")))
    issues: List[str] = []
    checked = 0
    for rel in docs:
        with open(os.path.join(root, rel), encoding="utf-8") as fh:
            text = fh.read()
        for snip in _command_snippets(text):
            for m in _NF_CALL.finditer(snip):
                checked += 1
                name = m.group(1)
                if name not in cmds:
                    issues.append("%s 命令面：`%s` 不是 CLI 子命令"
                                  "（修复指引：核对 scripts/nf.py 注册表改文档，或先实现该命令）"
                                  % (rel, ("nf " + name).strip()))
            for m in _MCP_TOOL_MENTION.finditer(snip):
                checked += 1
                if tools and m.group(1) not in tools:
                    issues.append("%s 命令面：%s 不是已登记 MCP 工具"
                                  "（修复指引：核对 core/mcp_runtime.TOOL_DEFS，"
                                  "工具名与实现须逐名一致）" % (rel, m.group(1)))
    return issues, {"docs": len(docs), "commands_checked": checked,
                    "cli_commands": len(cmds), "mcp_tools": len(tools)}
