"""JSON Schema 子集校验器（**叶子件**：不 import 任何 core 模块）。

为什么单独成件（2026-09-29）：这段纯函数原在 `output_forms` 里，而 `pack_combo` 只为
调它而 import `output_forms` —— 与 `output_forms → pack_combo` 构成**模块级双向对**，
`coupling_metrics` 的零环硬判据因此不达标。迁到叶子后两边都只依赖叶子，各自单向。
"""
from __future__ import annotations

import json
import re
from typing import Any, List, Optional


_JSON_TYPES = {
    "object": dict, "array": list, "string": str, "boolean": bool,
    "number": (int, float), "integer": int, "null": type(None),
}

_SUPPORTED = {
    "$schema", "$id", "$ref", "$defs", "definitions", "title", "description",
    "type", "enum", "const", "properties", "patternProperties", "required",
    "additionalProperties", "items", "prefixItems", "minItems", "maxItems",
    "uniqueItems", "minLength", "maxLength", "pattern", "format", "minimum",
    "maximum", "exclusiveMinimum", "exclusiveMaximum", "multipleOf",
    "allOf", "anyOf", "oneOf", "not", "propertyNames", "dependentRequired",
}
_UNSUPPORTED_WORDS = {
    "if", "then", "else", "contains", "minContains", "maxContains",
    "unevaluatedProperties", "unevaluatedItems", "dependentSchemas",
    "$dynamicRef", "$dynamicAnchor", "contentEncoding", "contentMediaType",
}


def _resolve_ref(ref: str, root_schema: dict) -> Optional[dict]:
    """只支持本地引用（#/$defs/x、#/definitions/x）——远程引用不静默跳过，报 unsupported。"""
    if not ref.startswith("#/"):
        return None
    node: Any = root_schema
    for part in ref[2:].split("/"):
        part = part.replace("~1", "/").replace("~0", "~")
        if isinstance(node, dict) and part in node:
            node = node[part]
        else:
            return None
    return node if isinstance(node, dict) else None


def _type_ok(value: Any, want: str) -> bool:
    py = _JSON_TYPES.get(want)
    if py is None:
        return True
    if want in ("number", "integer") and isinstance(value, bool):
        return False
    return isinstance(value, py)


def json_schema_check(instance: Any, schema: dict, path: str = "$",
                      root_schema: Optional[dict] = None,
                      unsupported: Optional[List[str]] = None) -> List[str]:
    """JSON Schema 2020-12 **子集**校验：返回错误清单；不支持的官方关键字进 unsupported。

    子集边界（公开声明，不假装全实现）：见 `_SUPPORTED`；超出即上报，
    「不支持」绝不等价「通过」。
    """
    if root_schema is None:
        root_schema = schema
    if unsupported is None:
        unsupported = []
    errors: List[str] = []
    if not isinstance(schema, dict):
        return ["%s: schema 节点非对象" % path]
    for kw in sorted(set(schema) - _SUPPORTED):
        if kw in _UNSUPPORTED_WORDS or kw.startswith("$"):
            tag = "%s@%s" % (kw, path)
            if tag not in unsupported:
                unsupported.append(tag)
    if "$ref" in schema:
        target = _resolve_ref(str(schema["$ref"]), root_schema)
        if target is None:
            unsupported.append("远程/悬空 $ref %s@%s" % (schema["$ref"], path))
        else:
            errors += json_schema_check(instance, target, path, root_schema, unsupported)
    types = schema.get("type")
    if types is not None:
        cand = types if isinstance(types, list) else [types]
        if not any(_type_ok(instance, t) for t in cand):
            errors.append("%s: 类型应为 %s，实为 %s"
                          % (path, "/".join(map(str, cand)), type(instance).__name__))
    if "const" in schema and instance != schema["const"]:
        errors.append("%s: 应为常量 %r" % (path, schema["const"]))
    if "enum" in schema and instance not in schema["enum"]:
        errors.append("%s: 取值 %r 不在枚举内" % (path, instance))
    if isinstance(instance, str):
        if "minLength" in schema and len(instance) < schema["minLength"]:
            errors.append("%s: 长度 < %s" % (path, schema["minLength"]))
        if "maxLength" in schema and len(instance) > schema["maxLength"]:
            errors.append("%s: 长度 > %s" % (path, schema["maxLength"]))
        if "pattern" in schema and not re.search(str(schema["pattern"]), instance):
            errors.append("%s: 不匹配 pattern %s" % (path, schema["pattern"]))
        fmt = schema.get("format")
        if fmt:
            errors += _format_errors(instance, fmt, path)
    if isinstance(instance, (int, float)) and not isinstance(instance, bool):
        for kw, op, cmp_ in (("minimum", ">=", lambda a, b: a >= b),
                             ("maximum", "<=", lambda a, b: a <= b),
                             ("exclusiveMinimum", ">", lambda a, b: a > b),
                             ("exclusiveMaximum", "<", lambda a, b: a < b)):
            if kw in schema and not cmp_(instance, schema[kw]):
                errors.append("%s: %s %s %s 不成立" % (path, instance, op, schema[kw]))
        if "multipleOf" in schema and schema["multipleOf"]:
            q = instance / schema["multipleOf"]
            if abs(q - round(q)) > 1e-9:
                errors.append("%s: 非 %s 的整数倍" % (path, schema["multipleOf"]))
    if isinstance(instance, list):
        if "minItems" in schema and len(instance) < schema["minItems"]:
            errors.append("%s: 元素数 < %s" % (path, schema["minItems"]))
        if "maxItems" in schema and len(instance) > schema["maxItems"]:
            errors.append("%s: 元素数 > %s" % (path, schema["maxItems"]))
        if schema.get("uniqueItems"):
            seen = [json.dumps(x, sort_keys=True, ensure_ascii=False) for x in instance]
            if len(set(seen)) != len(seen):
                errors.append("%s: uniqueItems 被违反" % path)
        prefix = schema.get("prefixItems")
        if isinstance(prefix, list):
            for i, sub in enumerate(prefix):
                if i < len(instance):
                    errors += json_schema_check(instance[i], sub, "%s[%d]" % (path, i),
                                                root_schema, unsupported)
        items = schema.get("items")
        if isinstance(items, dict):
            start = len(prefix) if isinstance(prefix, list) else 0
            for i in range(start, len(instance)):
                errors += json_schema_check(instance[i], items, "%s[%d]" % (path, i),
                                            root_schema, unsupported)
    if isinstance(instance, dict):
        props = schema.get("properties") or {}
        pats = schema.get("patternProperties") or {}
        for key in schema.get("required") or []:
            if key not in instance:
                errors.append("%s: 缺必填字段 %s" % (path, key))
        for dep, need in (schema.get("dependentRequired") or {}).items():
            if dep in instance:
                for n in need:
                    if n not in instance:
                        errors.append("%s: 出现 %s 时必填 %s" % (path, dep, n))
        for key, value in instance.items():
            matched = False
            if key in props:
                matched = True
                errors += json_schema_check(value, props[key], "%s.%s" % (path, key),
                                            root_schema, unsupported)
            for pat, sub in pats.items():
                if re.search(pat, key):
                    matched = True
                    errors += json_schema_check(value, sub, "%s.%s" % (path, key),
                                                root_schema, unsupported)
            if not matched:
                ap = schema.get("additionalProperties", True)
                if ap is False:
                    errors.append("%s: 多余字段 %s（additionalProperties=false）" % (path, key))
                elif isinstance(ap, dict):
                    errors += json_schema_check(value, ap, "%s.%s" % (path, key),
                                                root_schema, unsupported)
        pn = schema.get("propertyNames")
        if isinstance(pn, dict):
            for key in instance:
                errors += json_schema_check(key, pn, "%s<键:%s>" % (path, key),
                                            root_schema, unsupported)
    for kw, mode in (("allOf", "all"), ("anyOf", "any"), ("oneOf", "one")):
        subs = schema.get(kw)
        if not isinstance(subs, list):
            continue
        results = [json_schema_check(instance, s, path, root_schema, unsupported)
                   for s in subs]
        ok = sum(1 for r in results if not r)
        if mode == "all" and ok != len(subs):
            errors.append("%s: allOf 有 %d/%d 子式不成立" % (path, len(subs) - ok, len(subs)))
        if mode == "any" and ok == 0:
            errors.append("%s: anyOf 全不成立" % path)
        if mode == "one" and ok != 1:
            errors.append("%s: oneOf 命中 %d 个（须恰 1）" % (path, ok))
    if isinstance(schema.get("not"), dict) and not json_schema_check(
            instance, schema["not"], path, root_schema, unsupported):
        errors.append("%s: not 子式被满足" % path)
    return errors


def _format_errors(value: str, fmt: str, path: str) -> List[str]:
    if fmt == "date":
        return [] if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value) else ["%s: 非 ISO 8601 日期" % path]
    if fmt == "date-time":
        return ([] if re.fullmatch(r"\d{4}-\d{2}-\d{2}[Tt ].+", value)
                else ["%s: 非 ISO 8601 日期时间" % path])
    if fmt == "uri":
        return ([] if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", value)
                else ["%s: 非绝对 URI" % path])
    return []
