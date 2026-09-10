"""world_slots 注册表扫描器（protocol/world_slots.json 自身机检）。

校验对象：M00 数据槽可绑定投影的结构与类型约束，确保 world_model.slot
引用的不是一份会漂移的自由 JSON。只验可无歧义项：

- schema_version 必须为 "1"；
- slots 非空 object；
- 每个 slot 的 kind 合法；owner 非空；
- item_kind 仅 kind=array 可用，且值域合法。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

SLOT_KINDS = {"string", "integer", "number", "boolean", "array", "object"}
ITEM_KINDS = {"string", "integer", "number", "boolean"}


def validate_registry(data: Any, label: str = "world_slots") -> List[str]:
    issues: List[str] = []
    if not isinstance(data, dict):
        return [f"{label}: 顶层非对象"]
    if data.get("schema_version") != "1":
        issues.append(f"{label}.schema_version: 应为 \"1\"")
    slots = data.get("slots")
    if not isinstance(slots, dict) or not slots:
        issues.append(f"{label}.slots: 非空对象")
        return issues
    for path, spec in slots.items():
        at = f"{label}.slots.{path!r}"
        if not isinstance(path, str) or not path.strip():
            issues.append(f"{at}: 槽位路径非空字符串")
        if not isinstance(spec, dict):
            issues.append(f"{at}: 槽位定义非对象")
            continue
        kind = spec.get("kind")
        owner = spec.get("owner")
        item_kind = spec.get("item_kind")
        if kind not in SLOT_KINDS:
            issues.append(f"{at}.kind: 非法类型 {kind!r}")
        if not isinstance(owner, str) or not owner.strip():
            issues.append(f"{at}.owner: 非空字符串")
        if kind == "array":
            if item_kind is not None and item_kind not in ITEM_KINDS:
                issues.append(f"{at}.item_kind: 非法元素类型 {item_kind!r}")
        elif item_kind is not None:
            issues.append(f"{at}.item_kind: 仅 kind=array 可用")
    return issues


def scan(root: str = ".") -> Tuple[List[str], Dict[str, Any]]:
    r = Path(root)
    path = r / "protocol" / "world_slots.json"
    if not path.is_file():
        return ["protocol/world_slots.json 缺失"], {"slots": 0}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return ["protocol/world_slots.json 解析失败：%s" % exc], {"slots": 0}
    issues = validate_registry(data)
    m00_path = r / "04_模块库" / "通用类" / "M00_数据结构.md"
    if m00_path.is_file():
        m00_text = m00_path.read_text(encoding="utf-8")
        slots = data.get("slots") if isinstance(data, dict) else {}
        for slot in slots:
            for part in str(slot).split("."):
                if part and part not in m00_text:
                    issues.append(
                        "world_slots slot 路径段未在 M00 文档锚定：%r（%s）"
                        % (part, slot)
                    )
    else:
        issues.append("04_模块库/通用类/M00_数据结构.md 缺失")
    slots = data.get("slots") if isinstance(data, dict) else {}
    arrays = sum(1 for v in slots.values()
                 if isinstance(v, dict) and v.get("kind") == "array")
    return issues, {
        "slots": len(slots) if isinstance(slots, dict) else 0,
        "arrays": arrays,
    }
