"""45 · 模块工具面扫描器（machine_contract.tool_face 可选建议层）。

轻量机检只验可无歧义项：purpose/guidance 在场、candidates 有链接必有出处
（repo+license）；「装不装/装哪个/自造」不入门禁（AI 自由裁量）。
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

_ROOT = Path(__file__).resolve().parents[3]


def validate_entry(entry: Dict[str, Any]) -> List[str]:
    issues = []
    if not isinstance(entry.get("purpose"), str) or not entry["purpose"].strip():
        issues.append("tool_face 条目缺 purpose")
    guidance = entry.get("guidance")
    if not isinstance(guidance, dict) or not guidance:
        issues.append("tool_face 条目缺 guidance（指导段是验收硬核）")
    for c in (entry.get("candidates") or []):
        if not isinstance(c, dict):
            issues.append("candidate 非对象")
            continue
        repo = str(c.get("repo") or "")
        if not re.match(r"^https?://", repo):
            issues.append("candidate 缺合法 https 链接")
        if not str(c.get("license") or "").strip():
            issues.append("candidate 缺 license（有链接必须有出处）")
    return issues


def scan(root: str = ".") -> Tuple[List[str], Dict[str, Any]]:
    r = Path(root)
    from core import conformance_scan as csc

    issues: List[str] = []
    modules = 0
    entries = 0
    candidates = 0
    faces = []
    for doc in csc._module_docs(str(r)):
        text = Path(doc).read_text(encoding="utf-8")
        parsed = csc._fence_yaml(text, "machine_contract")
        mc = parsed.get("machine_contract") if isinstance(parsed, dict) else None
        if not isinstance(mc, dict) or "tool_face" not in mc:
            continue
        face = mc["tool_face"]
        if not isinstance(face, list) or not face:
            issues.append("%s: tool_face 非空列表" % doc)
            continue
        modules += 1
        faces.append({"module": (mc.get("id") or doc),
                      "source": doc,
                      "entries": len(face)})
        for e in face:
            entries += 1
            issues += validate_entry(e)
            candidates += len(e.get("candidates") or [])
    return issues, {"modules": modules, "entries": entries,
                    "candidates": candidates, "faces": faces}
