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
import os

INSTRUCTION_MARK = "⛔ 操作指令"
LAST_UPDATED_PREFIX = "> 最后更新："

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
        head = _head_lines(open(path, encoding="utf-8").read())
        if not any(ln.startswith(LAST_UPDATED_PREFIX) for ln in head):
            issues.append("%s 缺「最后更新」位（头部 %d 行内）" % (rel, len(head)))
    for rel in INSTRUCTION_DOCS:
        path = os.path.join(root, rel)
        if not os.path.exists(path):
            continue
        head = _head_lines(open(path, encoding="utf-8").read())
        if not any(INSTRUCTION_MARK in ln for ln in head):
            issues.append("%s 缺「⛔ 操作指令」标识头（指令类文档须全覆盖）" % rel)
    return issues


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
