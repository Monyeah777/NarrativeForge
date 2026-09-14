"""指令档 → 机器面路由（driver override，机制借鉴 ACP）。

NF 的指令档（组装指令包 / AI_ROUTING / ai-menu）此前只说"怎么读"，**不声明"有机器面时走哪条路"**
——能否走 `nf serve` 的 MCP 工具面，全靠执行者自觉。本模块补这一层：

`protocol/driver.json`（机读真源）声明：
- `bindings`：MCP 服务入口、工具集、提示集（工具名必须与 `mcp_runtime.TOOL_DEFS` **逐名一致**）；
- `workflows`：每个工作流映射到 MCP 提示/工具 + **文本 fallback 文件**；
- `documents`：哪些指令档属于哪个工作流（该文档头部**必须**带 override 声明块）；
- `fail_closed`：派发失败即停、**禁止回退**（含必须出现在文档声明块里的关键词）。

判据（全部可证）：schema 合法；工具/提示名在运行时存在；fallback 文件存在；
文档存在且头部带 `DRIVER OVERRIDE` 块且块内写明本工作流名与 fail-closed 关键词。
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

DRIVER_REL = "protocol/driver.json"
OVERRIDE_MARK = "DRIVER OVERRIDE"


def load(root: str = ".") -> Dict[str, Any]:
    p = Path(root) / DRIVER_REL
    return json.loads(p.read_text(encoding="utf-8")) if p.is_file() else {}


def resolve(root: str = ".", workflow: str = "") -> Dict[str, Any]:
    """解析某工作流该走哪条路（只读；不实际派发）。"""
    doc = load(root)
    wf = (doc.get("workflows") or {}).get(workflow) or {}
    if not wf:
        return {"workflow": workflow, "mode": "unknown",
                "reason": "未在 %s 中映射" % DRIVER_REL}
    tools = list(wf.get("mcp_tools") or [])
    prompt = str(wf.get("mcp_prompt") or "")
    return {"workflow": workflow,
            "mode": "mcp" if (tools or prompt) else "markdown",
            "prompt": prompt, "tools": tools,
            "fallback": wf.get("fallback", ""),
            "on_dispatch_failure": "stop（禁止回退到文本步骤）"}


def scan(root: str = ".") -> Tuple[List[str], List[str], Dict[str, Any]]:
    """机检 driver 声明 → (issues, warns, stats)。"""
    issues: List[str] = []
    warns: List[str] = []
    doc = load(root)
    if not doc:
        return ["缺 driver 声明 %s（修复指引：见 protocol/driver.json）" % DRIVER_REL], [], {}
    if str(doc.get("schema") or "") != "nf-driver/1":
        issues.append("driver schema 不匹配（期望 nf-driver/1）")
    try:
        from core.mcp_runtime import PROMPT_DEFS, TOOL_DEFS
        live_tools = {t["name"] for t in TOOL_DEFS}
        live_prompts = {p["name"] for p in PROMPT_DEFS}
    except Exception:
        live_tools, live_prompts = set(), set()
    bind = doc.get("bindings") or {}
    for t in (bind.get("mcp.tools") or []):
        if t not in live_tools:
            issues.append("bindings.mcp.tools 引用了运行时不存在工具：%s" % t)
    for p in (bind.get("mcp.prompts") or []):
        if p not in live_prompts:
            issues.append("bindings.mcp.prompts 引用了运行时不存在提示：%s" % p)
    for name, wf in sorted((doc.get("workflows") or {}).items()):
        for t in (wf.get("mcp_tools") or []):
            if t not in live_tools:
                issues.append("workflow %s 引用不存在的 MCP 工具：%s（修复指引：改正或实现该工具）"
                              % (name, t))
        pr = str(wf.get("mcp_prompt") or "")
        if pr and pr not in live_prompts:
            issues.append("workflow %s 引用不存在的 MCP 提示：%s" % (name, pr))
        fb = str(wf.get("fallback") or "")
        if not fb:
            issues.append("workflow %s 缺 fallback 文件（无机器面时的文本路径必须显式）" % name)
        elif not (Path(root) / fb).is_file():
            issues.append("workflow %s 的 fallback 不存在：%s" % (name, fb))
    kws = (doc.get("fail_closed") or {}).get("marker_keywords") or []
    wfs = set(doc.get("workflows") or {})
    for d in (doc.get("documents") or []):
        rel, wf = str(d.get("path") or ""), str(d.get("workflow") or "")
        p = Path(root) / rel
        if not p.is_file():
            issues.append("driver.documents 指向不存在的文档：%s" % rel)
            continue
        if wf not in wfs:
            issues.append("%s 声明的工作流未在 workflows 中定义：%s" % (rel, wf))
        head = "\n".join(p.read_text(encoding="utf-8").splitlines()[:14])
        if OVERRIDE_MARK not in head:
            issues.append("%s 缺 `%s` 声明块（修复指引：见 protocol/driver.json 的 fail_closed）"
                          % (rel, OVERRIDE_MARK))
            continue
        if wf and wf not in head:
            warns.append("%s 的 override 块未写出工作流名 %s" % (rel, wf))
        for kw in kws:
            if kw not in head:
                issues.append("%s 的 override 块缺 fail-closed 关键词「%s」" % (rel, kw))
    stats = {"workflows": len(wfs), "documents": len(doc.get("documents") or []),
             "tools_bound": len(bind.get("mcp.tools") or []),
             "fallback_files": sum(1 for w in (doc.get("workflows") or {}).values()
                                   if w.get("fallback"))}
    return issues, warns, stats
