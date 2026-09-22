"""42 M4：文档可执行性卫生检查（分类标识 + last-updated + 过期告警）。

规则：
- 指令类文档（菜单/作业书/迁移指南/规范/演练集）须在头部带
  「⛔ 操作指令」标识行——阅读即执行，勿当资料阅读（100% 覆盖校验）。
- 关键文档（协议层/导航/MCP/菜单/指引 + 全部指令类）须带「最后更新：YYYY-MM-DD」位；
  stale()：超 N 月未更新且在被引用清单 → WARN 告警。
- 校验目标清单 = REQUIRED_DOCS（本库维护；新增指令/关键文档须入清单，
  否则 check 漏检——见 test_doc_hygiene 变异注入）。
"""
from __future__ import annotations

import datetime as _dt
import glob
import os
import re

INSTRUCTION_MARK = "⛔ 操作指令"
LAST_UPDATED_PREFIX = "> 最后更新："

#: 文档四型（机制借鉴 Diátaxis：tutorial 学习导向 / how-to 任务导向 /
#: reference 信息导向 / explanation 理解导向）。NF 原有「指令类 / 资料类」二分
#: 是**执行语义**（要不要读到即执行），四型是**用途语义**——两者并存，不互相替代。
KINDS = ("tutorial", "how-to", "reference", "explanation")

#: 四型**写法**判据（信息类型化的 NF 落位：类型不只是标签，还是写法约束）。
#: 只判可判定形状、不判文风；违规按 WARN 挂账（先可数、再逐波收），不判死。
KIND_RULES = {
    "how-to": {"must_any": (r"```", r"python scripts/nf\.py", r">\s*⛔"),
               "label": "可执行命令块"},
    "reference": {"must_any": (r"^\|.+\|", r"词表", r"字段"), "label": "词表或字段表"},
    "tutorial": {"must_any": (r"^\s*\d+[.、]\s", r"步骤", r"演练"), "label": "步骤序列"},
    "explanation": {"must_any": (r"为什么", r"权衡", r"机制", r"原理"),
                    "label": "为什么或权衡"},
}

#: 文档 → 四型归属（关键文档与指令档全覆盖；新增关键文档须同步入表）
DOC_KINDS = {
    "01_核心协议.md": "reference",
    "02_联动注册表.md": "reference",
    "06_Agent执行协议.md": "how-to",
    "07_官方核心出厂与社区预设导航.md": "reference",
    "DEEP_DIVE.md": "explanation",
    "AI_ROUTING.md": "how-to",
    "agent_组装指令包_v0.2.md": "how-to",
    "docs/mcp.md": "how-to",
    "docs/ai-menu.md": "how-to",
    "docs/ai-menu-fieldtest-v1.md": "how-to",
    "docs/迁移指南-基于nf-sig-diff.md": "how-to",
    "docs/attest.md": "how-to",
    "docs/verification-cards.md": "reference",
    "docs/需求收敛模板.md": "reference",
    "docs/42_M1_协议可执行性自测规范.md": "reference",
    "docs/42_M1_P03_演练集.md": "tutorial",
    "docs/42_M2_回合状态头_v1.md": "reference",
    "docs/42_M3_纯度体检.md": "reference",
    "docs/44_M1_执行演练扩展.md": "tutorial",
    "docs/44_M2_AI通道内容规范.md": "reference",
    "docs/45_执行遥测规范.md": "reference",
    "docs/45_M2_回合级drill.md": "tutorial",
    "docs/45_M3_techdoc载荷提案.md": "explanation",
    "docs/library.md": "how-to",
    "docs/receipts.md": "how-to",
    "docs/conformance.md": "how-to",
    "docs/io_types.md": "reference",
    "docs/pipelinerun.md": "how-to",
    "docs/machine_contract.md": "how-to",
    "docs/approval.md": "how-to",
    "docs/module_signature.md": "how-to",
    "docs/lsp.md": "how-to",
    "docs/driver.md": "how-to",
    "docs/patterns.md": "how-to",
    "docs/bench.md": "how-to",
    "docs/endpoint.md": "how-to",
    "docs/rfc.md": "reference",
    "docs/knowledge.md": "how-to",
    "docs/assertions.md": "how-to",
    "docs/modeling.md": "how-to",
    "docs/interop.md": "how-to",
    "docs/text-hygiene.md": "reference",
    "docs/decision-layer.md": "how-to",
}

#: 需带 last-updated 位的关键文档（协议/导航/接入 + 指令类）
REQUIRED_DOCS = [
    "01_核心协议.md", "02_联动注册表.md", "06_Agent执行协议.md",
    "07_官方核心出厂与社区预设导航.md", "docs/mcp.md", "docs/ai-menu.md",
    "docs/ai-menu-fieldtest-v1.md", "docs/迁移指南-基于nf-sig-diff.md",
    "docs/需求收敛模板.md",
    "docs/42_M1_协议可执行性自测规范.md", "docs/42_M1_P03_演练集.md",
    "docs/42_M2_回合状态头_v1.md", "docs/42_M3_纯度体检.md",
    "agent_组装指令包_v0.2.md",
    "docs/44_M1_执行演练扩展.md",
    "docs/44_M2_AI通道内容规范.md",
    "docs/45_执行遥测规范.md",
    "docs/45_M2_回合级drill.md",
    "docs/45_M3_techdoc载荷提案.md",
    "DEEP_DIVE.md",
    "docs/library.md",
    "docs/receipts.md",
    "docs/conformance.md",
    "docs/io_types.md",
    "docs/pipelinerun.md",
    "docs/machine_contract.md",
    "docs/approval.md",
    "docs/module_signature.md",
    "docs/lsp.md",
    "docs/driver.md",
    "docs/patterns.md",
    "docs/bench.md",
    "docs/endpoint.md",
    "docs/rfc.md",
    "docs/knowledge.md",
    "docs/assertions.md",
    "docs/modeling.md",
    "docs/interop.md",
    "docs/text-hygiene.md",
    "docs/decision-layer.md",
]

#: 指令类文档（须带 ⛔ 操作指令 标识）
INSTRUCTION_DOCS = [
    "docs/ai-menu.md", "docs/ai-menu-fieldtest-v1.md",
    "docs/迁移指南-基于nf-sig-diff.md",
    "docs/42_M1_协议可执行性自测规范.md", "docs/42_M1_P03_演练集.md",
    "docs/42_M2_回合状态头_v1.md", "docs/42_M3_纯度体检.md",
    "agent_组装指令包_v0.2.md",
    "docs/44_M1_执行演练扩展.md",
    "docs/44_M2_AI通道内容规范.md",
    "docs/45_执行遥测规范.md",
    "docs/45_M2_回合级drill.md",
    "docs/45_M3_techdoc载荷提案.md",
    "AI_ROUTING.md",
    "docs/library.md",
    "docs/receipts.md",
    "docs/conformance.md",
    "docs/pipelinerun.md",
    "docs/machine_contract.md",
    "docs/approval.md",
    "docs/module_signature.md",
    "docs/lsp.md",
    "docs/driver.md",
    "docs/patterns.md",
    "docs/bench.md",
    "docs/endpoint.md",
    "docs/rfc.md",
    "docs/knowledge.md",
    "docs/assertions.md",
    "docs/modeling.md",
    "docs/interop.md",
    "docs/decision-layer.md",
]


def _head_lines(text: str, n: int = 8) -> list:
    return text.splitlines()[:n]


def check_markers(root: str = ".") -> list:
    """指令标识 + last-updated 位覆盖校验（目标清单内 100%）。"""
    issues = []
    for rel in REQUIRED_DOCS:
        path = os.path.join(root, rel)
        if not os.path.exists(path):
            issues.append("%s 缺失（须入 REQUIRED_DOCS 清单）" % rel)
            continue
        with open(path, encoding="utf-8") as fh:
            head = _head_lines(fh.read())
        if not any(ln.startswith(LAST_UPDATED_PREFIX) for ln in head):
            issues.append("%s 缺「最后更新」位（头部 %d 行内）" % (rel, len(head)))
    for rel in INSTRUCTION_DOCS:
        path = os.path.join(root, rel)
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8") as fh:
            head = _head_lines(fh.read())
        if not any(INSTRUCTION_MARK in ln for ln in head):
            issues.append("%s 缺「⛔ 操作指令」标识头（指令类文档须全覆盖）" % rel)
    return issues


def kind_coverage(root: str = ".") -> list:
    """四型覆盖校验：关键文档与指令档每件都须有四型归属（新增件漏表即报）。"""
    issues = []
    for rel in sorted(set(REQUIRED_DOCS) | set(INSTRUCTION_DOCS)):
        kind = DOC_KINDS.get(rel)
        if not kind:
            issues.append("%s 缺四型归属（DOC_KINDS；取值 %s）" % (rel, "/".join(KINDS)))
        elif kind not in KINDS:
            issues.append("%s 四型取值非法：%s（取值 %s）" % (rel, kind, "/".join(KINDS)))
    return issues


def kind_rules(root: str = ".") -> list:
    """四型**写法**判据 → WARN 清单（走形不改归属；存量按可数收敛，不判死）。"""
    warns = []
    for rel, kind in sorted(DOC_KINDS.items()):
        rule = KIND_RULES.get(kind)
        if not rule:
            continue
        path = os.path.join(root, rel)
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
        if not any(re.search(p, text, re.M) for p in rule["must_any"]):
            warns.append("%s 属 %s 型但缺「%s」（写法未定型）" % (rel, kind, rule["label"]))
    return warns


def kind_distribution(root: str = ".") -> dict:
    """四型分布（只统计在盘文件；供门禁/报告聚合）。"""
    dist = {k: 0 for k in KINDS}
    for rel, kind in DOC_KINDS.items():
        if os.path.exists(os.path.join(root, rel)) and kind in dist:
            dist[kind] += 1
    dist["total"] = sum(dist[k] for k in KINDS)
    return dist


def stale(root: str = ".", month_limit: int = 3,
          today: str = "") -> list:
    """过期告警：关键文档「最后更新」距今超过 month_limit 个月 → WARN 清单。"""
    today = today or _dt.date.today().isoformat()
    now = _dt.date.fromisoformat(today)
    warns = []
    for rel in REQUIRED_DOCS:
        path = os.path.join(root, rel)
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8") as fh:
            content = fh.read()
        for ln in content.splitlines():
            if ln.startswith(LAST_UPDATED_PREFIX):
                date_str = ln[len(LAST_UPDATED_PREFIX):].strip()
                try:
                    updated = _dt.date.fromisoformat(date_str)
                except ValueError:
                    warns.append("%s 最后更新位格式非法：%s" % (rel, date_str))
                    break
                months = (now.year - updated.year) * 12 + now.month - updated.month
                if months > month_limit:
                    warns.append("%s 超过 %d 个月未更新（最后更新 %s）"
                                 % (rel, month_limit, date_str))
                break
    return warns


#: 正文正规性扫描目标（NF 自产内容面；第三方夹具、`scripts/__pycache__` 等不入面）
TEXT_SANITY_GLOBS = (
    "*.md", "docs/*.md", "docs/**/*.md",
    "04_模块库/*/*.md", "community/*/*.md", "community/*/modules/*.md", "community/*/assets/*.md",
    "library/*.md", "protocol/*.md", "skills/*/*.md", "patterns/*/*.md",
    "postmortems/*.md", "decisions/*.md", "results/*.md",
)

#: mojibake 特征字：UTF-8 中文被按 GBK 解码后再存回 UTF-8 时的高频字符。
#: 取样自真实缺陷（`library/NF-TECHDOC-*.md` 与 `docs/examples/state-front/*` 同源生成产物）。
MOJIBAKE_MARKERS = "锛銆鈥鏄鏂鐨涓鍦閫鎶璁缂鐩鍐鍜欏鏈鐢姝涔浣"
MOJIBAKE_MIN_HITS = 3


def text_sanity(root: str = ".", globs=None) -> list:
    """正文正规性（**WARN 级，存量挂账不判死**）：围栏配平 + mojibake 特征。

    判据两条，只判可判定形状、不判文风：
    ① 围栏配平——每件正文的围栏标记（行首 ``` 或 ~~~）计数须为**偶数**；
       奇 = 有未配平围栏，渲染与「按围栏切段」的解析（如 machine_contract 提取）都会走偏。
    ② 编码可读——单行命中 ≥ `MOJIBAKE_MIN_HITS` 个 mojibake 特征字 = 该行正文不可读
       （疑似 UTF-8/GBK 双重转换）。

    返回 `"WARN: …"` 字符串列表，由调用方决定是否计入 WARN 计数。
    """
    out: list = []
    files = sorted({p for g in (globs or TEXT_SANITY_GLOBS)
                    for p in glob.glob(os.path.join(root, g), recursive=True)})
    for rel in files:
        rel = os.path.relpath(rel)
        try:
            with open(rel, encoding="utf-8") as fh:
                text = fh.read()
        except (OSError, UnicodeDecodeError) as exc:
            out.append("WARN: 正文不可读 %s（%s）" % (rel, exc))
            continue
        lines = text.splitlines()
        fences = sum(1 for ln in lines if re.match(r"^\s*(```|~~~)", ln))
        if fences % 2:
            out.append("WARN: 围栏未配平 %s（标记 %d 个，须为偶数——未配平的正文渲染与"
                       "按围栏切段的解析都会走偏）" % (rel, fences))
        bad = sum(1 for ln in lines
                  if sum(1 for ch in ln if ch in MOJIBAKE_MARKERS) >= MOJIBAKE_MIN_HITS)
        if bad:
            out.append("WARN: 正文疑似 mojibake %s（%d 行命中编码特征——疑似 UTF-8/GBK 双重转换）"
                       % (rel, bad))
    return out
