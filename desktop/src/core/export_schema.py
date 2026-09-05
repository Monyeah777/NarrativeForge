"""导出产物 schema 校验（v2.2.0 A1：5 种导出格式逐键 shape 自检）。

外部吸收清单 A1（SpecForge Artifact Gating）：导出产物合规才绿——export()
产出外部格式后校验其 shape（非完整 JSON Schema 引擎，逐键断言结构/必填），
防「产物可生成但格式漂移」。

覆盖 exporter._REGISTRY 5 格式：
- ccv3    chara.json（chara_card_v3：spec/spec_version/name/description/
          character_book.entries[]）+ world.json（entries[]）
- skill   SKILL.md（YAML frontmatter name/description + 正文 ## 层结构）
- agents  AGENTS.md（# Agent Operating Rules + ## 层）
- claude  CLAUDE.md（同 agents 形态）
- mcp     mcp.json（mcp{name, capabilities.resources, resources[]}）

每个校验器返回 list[str] issues（空 = 通过）。文件级校验对产物路径断言存在。
"""
from __future__ import annotations

import glob
import json
import os
import re
from typing import List

#: ccv3 chara_card_v3 稳定核心字段（对齐 ccv3_adapter 文档注释 + 真实产物）
CCV3_CHARA_KEYS = {"name", "description", "spec", "spec_version"}
CCV3_CHARA_OPT = {"personality", "scenario", "first_mes", "mes_example",
                  "system_prompt", "post_history_instructions",
                  "alternate_greetings", "tags", "creator",
                  "character_version", "character_book"}
#: world 条目必填（对齐 ccv3_adapter world_entries 产出）
WORLD_ENTRY_KEYS = {"name", "keys", "content", "enabled",
                    "insertion_order", "id"}
MCP_RESOURCE_KEYS = {"uri", "name", "mimeType", "text"}


def check_ccv3_chara(path: str) -> List[str]:
    issues: List[str] = []
    if not os.path.isfile(path):
        return [f"ccv3 chara.json 缺失: {path}"]
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        return [f"ccv3 chara.json 解析失败: {e}"]
    if not isinstance(data, dict):
        return ["ccv3 chara.json 应为对象"]
    for k in CCV3_CHARA_KEYS:
        if k not in data:
            issues.append(f"ccv3 chara 缺必填键: {k}")
    book = data.get("character_book") if isinstance(data, dict) else None
    if book is not None:
        entries = book.get("entries") if isinstance(book, dict) else None
        if not isinstance(entries, list):
            issues.append("ccv3 character_book.entries[] 缺失或非列表")
        else:
            for i, e in enumerate(entries):
                if not isinstance(e, dict) or not e.get("name") or not e.get("content"):
                    issues.append(f"ccv3 world 条目 {i} 缺 name/content")
    return issues


def check_ccv3_world(path: str) -> List[str]:
    issues: List[str] = []
    if not os.path.isfile(path):
        return [f"ccv3 world.json 缺失: {path}"]
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        return [f"ccv3 world.json 解析失败: {e}"]
    entries = data.get("entries") if isinstance(data, dict) else None
    if not isinstance(entries, list):
        return ["ccv3 world.entries[] 缺失或非列表"]
    for i, e in enumerate(entries):
        if not isinstance(e, dict):
            issues.append(f"world 条目 {i} 非对象")
            continue
        for k in WORLD_ENTRY_KEYS:
            if k not in e:
                issues.append(f"world 条目 {i} 缺键: {k}")
    return issues


def _check_md_frontmatter(path: str, required: tuple) -> List[str]:
    issues: List[str] = []
    if not os.path.isfile(path):
        return [f"md 产物缺失: {path}"]
    with open(path, encoding="utf-8") as f:
        txt = f.read()
    if not txt.startswith("---"):
        issues.append(f"{path} 缺 YAML frontmatter（--- 起始）")
        return issues
    end = txt.find("\n---", 4)
    fm = txt[4:end] if end > 0 else ""
    for k in required:
        if not re.search(rf"^{re.escape(k)}:", fm, re.M):
            issues.append(f"{path} frontmatter 缺 {k}")
    # 正文须含 `## ` 层结构（无 frontmatter 块的正文）
    body = txt[end + 4:] if end > 0 else txt
    if not re.search(r"^#{1,2} ", body, re.M):
        issues.append(f"{path} 正文缺 #/## 标题结构")
    return issues


def check_skill_md(path: str) -> List[str]:
    return _check_md_frontmatter(path, ("name", "description"))


def check_agents_md(path: str) -> List[str]:
    return _check_md_frontmatter(path, ("",)) if False else _check_agents_like(path)


def _check_agents_like(path: str) -> List[str]:
    issues: List[str] = []
    if not os.path.isfile(path):
        return [f"agents/claude 产物缺失: {path}"]
    with open(path, encoding="utf-8") as f:
        txt = f.read()
    if not re.search(r"^# .+", txt, re.M):
        issues.append(f"{path} 缺 # 一级标题")
    if not re.search(r"^## ", txt, re.M):
        issues.append(f"{path} 缺 ## 章节结构")
    return issues


def check_claude_md(path: str) -> List[str]:
    return check_agents_md(path)


def check_mcp_json(path: str) -> List[str]:
    issues: List[str] = []
    if not os.path.isfile(path):
        return [f"mcp.json 缺失: {path}"]
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        return [f"mcp.json 解析失败: {e}"]
    mcp = data.get("mcp") if isinstance(data, dict) else None
    if not isinstance(mcp, dict):
        return ["mcp.json 缺 mcp 对象"]
    if not mcp.get("name"):
        issues.append("mcp.name 缺失")
    caps = mcp.get("capabilities") if isinstance(mcp, dict) else None
    if not isinstance(caps, dict) or "resources" not in caps:
        issues.append("mcp.capabilities.resources 缺失")
    res = mcp.get("resources")
    if not isinstance(res, list):
        issues.append("mcp.resources[] 缺失或非列表")
    else:
        for i, r in enumerate(res):
            if not isinstance(r, dict) or not all(k in r for k in MCP_RESOURCE_KEYS):
                issues.append(f"mcp resource {i} 缺字段（uri/name/mimeType/text）")
    return issues


#: 格式 → 产物文件名校验器（export 后调用；path 为 dest 下文件名）
_FORMAT_FILES = {
    "ccv3": [("chara.json", check_ccv3_chara), ("world.json", check_ccv3_world)],
    "skill": [("SKILL.md", check_skill_md)],
    "agents": [("AGENTS.md", check_agents_md)],
    "claude": [("CLAUDE.md", check_claude_md)],
    "mcp": [("mcp.json", check_mcp_json)],
}


def validate_export(fmt: str, dest_dir: str) -> List[str]:
    """校验 dest_dir 下 fmt 格式的导出产物 shape；返回 issues（空 = 通过）。

    skill 产物在 dest/<slug>/SKILL.md（skill 适配器建 skill_dir 子目录），
    其余格式在 dest 顶层。
    """
    if fmt not in _FORMAT_FILES:
        return [f"未登记校验的格式: {fmt}"]
    issues: List[str] = []
    for fname, checker in _FORMAT_FILES[fmt]:
        if fmt == "skill":
            hits = sorted(glob.glob(os.path.join(dest_dir, "*", fname)))
            if not hits:
                issues.append(f"skill 产物缺失: {os.path.join(dest_dir, '*', fname)}")
            for h in hits:
                issues.extend(checker(h))
        else:
            issues.extend(checker(os.path.join(dest_dir, fname)))
    return issues
