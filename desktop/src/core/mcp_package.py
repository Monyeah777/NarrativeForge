"""B 线包装声明门禁（内容质检 MCP 包）：工具面 / 类目 / 红线可机检。

真源 `protocol/mcp_package.json`。核心判据是**红线「只读面不变」**：
声明的 tools/prompts 必须与 `mcp_runtime.TOOL_DEFS` / `PROMPT_DEFS` **逐名一致**
（多一个少一个即 FAIL）——这样"上架材料里写的工具列表"永远不会与真实运行时漂移。
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

DECL_REL = "protocol/mcp_package.json"
SCHEMA = "nf-mcp-package/1"
CATEGORIES = ("content-creation", "developer-tools", "knowledge-management")


def decl(root: str = ".") -> Dict[str, Any]:
    p = Path(root) / DECL_REL
    return json.loads(p.read_text(encoding="utf-8")) if p.is_file() else {}


def scan(root: str = ".") -> Tuple[List[str], List[str], Dict[str, Any]]:
    """→ (issues, warns, stats)。"""
    issues: List[str] = []
    warns: List[str] = []
    d = decl(root)
    if not d:
        return ["缺 B 线包装声明 %s" % DECL_REL], warns, {}
    if str(d.get("schema") or "") != SCHEMA:
        issues.append("包装声明 schema 不匹配（期望 %s）" % SCHEMA)
    if tuple(d.get("category_vocabulary") or ()) != CATEGORIES:
        issues.append("类目词表与判据不一致（期望 %s）" % "/".join(CATEGORIES))
    if not (d.get("red_lines") or []):
        issues.append("红线不得为空（上架包的纪律必须成文）")
    if str(d.get("status")) == "draft" and not (d.get("pending") or []):
        issues.append("status=draft 但 pending 为空——草案必须写明还差什么")
    pkg = d.get("package") if isinstance(d.get("package"), dict) else {}
    if not (pkg.get("name_candidates") or []):
        issues.append("缺命名候选（B-S1 须给候选）")
    if not (pkg.get("one_liner_candidates") or []):
        issues.append("缺一句话候选（B-S1 须给候选）")
    if str(pkg.get("category")) not in CATEGORIES:
        issues.append("类目越词表：%s" % pkg.get("category"))
    # 红线「只读面不变」：与运行时逐名一致
    try:
        from core.mcp_runtime import PROMPT_DEFS, TOOL_DEFS
        live_tools = [t["name"] for t in TOOL_DEFS]
        live_prompts = [p["name"] for p in PROMPT_DEFS]
    except Exception as exc:                      # 运行时可导入性本身也是判据
        issues.append("mcp_runtime 不可导入，无法核对工具面：%s" % exc)
        live_tools, live_prompts = [], []
    got_tools = [str(x) for x in (pkg.get("tools") or [])]
    got_prompts = [str(x) for x in (pkg.get("prompts") or [])]
    if sorted(got_tools) != sorted(live_tools):
        issues.append("工具面与运行时不一致（上架材料会漂移）：声明 %d 个 / 运行时 %d 个"
                      "（多：%s；少：%s）"
                      % (len(got_tools), len(live_tools),
                         sorted(set(got_tools) - set(live_tools)) or "无",
                         sorted(set(live_tools) - set(got_tools)) or "无"))
    if sorted(got_prompts) != sorted(live_prompts):
        issues.append("提示面与运行时不一致：声明 %s / 运行时 %s"
                      % (got_prompts, live_prompts))
    if (d.get("pending") or []):
        warns.append("包装声明为草案：%d 项待补（%s）"
                     % (len(d["pending"]), "；".join(d["pending"][:2])))
    stats = {"tools": len(got_tools), "prompts": len(got_prompts),
             "targets": len(pkg.get("targets") or []),
             "category": str(pkg.get("category"))}
    return issues, warns, stats
