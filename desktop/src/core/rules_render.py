"""协议多出口 rules 渲染器（v2.5.0 Wave4：A3 适配矩阵补格）。

protocol.yaml（协议向导产物 / 社区包协议声明）→ 多目标 agent rules 渲染：
- agents   AGENTS.md（仓库级 agent 工作规则）
- claude   CLAUDE.md（同内容变体）
- skill    SKILL.md（能力包——协议声明作为可复用能力）

范围纪律（同 exporter._REGISTRY / _REGISTRY_IN）：只挂已交付的 agents/claude/skill
三格；mcp/ccv3 无 rules 渲染器不登记。

与 exporter._REGISTRY 的区别：exporter 从 IR（装配产物）导出；本渲染器从
protocol.yaml（协议声明）直接渲染——E2 协议向导产物本应多出口，此前单出口
（只产 protocol.yaml），本模块补多出口。
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import yaml


def _load_protocol(pkg_dir: str) -> Dict[str, Any]:
    with open(os.path.join(pkg_dir, "protocol.yaml"), encoding="utf-8") as f:
        return yaml.safe_load(f)


def _pkg_name(data: Dict[str, Any]) -> str:
    return str(data.get("package", {}).get("name") or "协议包")


def _module_lines(data: Dict[str, Any]) -> List[str]:
    pkg = data.get("package", {})
    out = []
    for m in pkg.get("modules") or []:
        mid = m.get("id") if isinstance(m, dict) else str(m)
        desc = m.get("desc", "") if isinstance(m, dict) else ""
        out.append(f"### {mid}" + (f" · {desc}" if desc else ""))
    return out


def _render_agents(data: Dict[str, Any]) -> str:
    """protocol.yaml → AGENTS.md（项目约定：协议声明作 agent 工作规则）。"""
    name = _pkg_name(data)
    lines = [f"# Agent Operating Rules", "", f"## {name} · 协议声明", ""]
    pkg = data.get("package", {})
    lines.append(f"- 管线：{pkg.get('pipeline', '')}")
    lines.append(f"- 类别：{', '.join(str(c) for c in pkg.get('categories') or [])}")
    lines.append(f"- 版本：{pkg.get('version', '1.0.0')}")
    mods = _module_lines(data)
    if mods:
        lines.append("")
        lines.extend(mods)
    return "\n".join(lines)


def _render_claude(data: Dict[str, Any]) -> str:
    """CLAUDE.md 变体（同 agents 内容）。"""
    return _render_agents(data)


def _render_skill(data: Dict[str, Any]) -> str:
    """protocol.yaml → SKILL.md（协议声明作可复用能力包）。"""
    name = _pkg_name(data)
    pkg = data.get("package", {})
    frontmatter = (
        "---\n"
        f"name: {pkg.get('id', 'protocol').lower()}\n"
        f"description: {name}（{pkg.get('pipeline', '')}）协议声明\n"
        "license: Proprietary. LICENSE.txt has complete terms\n"
        "---\n")
    body = [f"# {name}", "", f"## 协议声明", ""]
    body.append(f"- 管线：{pkg.get('pipeline', '')}")
    body.append(f"- 类别：{', '.join(str(c) for c in pkg.get('categories') or [])}")
    return frontmatter + "\n".join(body)


#: 协议多出口渲染器注册表（v2.5.0 Wave4 A3：格式 → 渲染函数）。
#: 范围纪律：只挂已交付 agents/claude/skill 三格。
_RULES_RENDERERS: Dict[str, Callable[[Dict[str, Any]], str]] = {
    "agents": _render_agents,
    "claude": _render_claude,
    "skill": _render_skill,
}


def render_protocol(pkg_dir: str, fmt: str) -> str:
    """protocol.yaml → 目标格式 rules 文本。fmt 未注册 → KeyError。"""
    if fmt not in _RULES_RENDERERS:
        raise KeyError(f"未登记的协议渲染格式：{fmt}（已注册：{sorted(_RULES_RENDERERS)}）")
    return _RULES_RENDERERS[fmt](_load_protocol(pkg_dir))
