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
    py: Any = _JSON_TYPES.get(want)
    if py is None:
        return True
    if want in ("number", "integer") and isinstance(value, bool):
        return False
    return isinstance(value, py)


#: 递归深度上限（2026-09-30 补）：schema 与实例**同时**深嵌套时会打爆 Python 栈（实测 2000 层
#: → `RecursionError`）——而这条链路吃的是**外来投稿**（社区域包声明的 artifact + 它的 schema）。
#: 崩掉等于把「一份恶意投稿」变成「门禁不可用」；超限一律**判 FAIL 并给修复指引**。
MAX_DEPTH = 64

#: 失控回溯（ReDoS）形态闸门：pattern **来自投稿者**（社区域包声明的 schema），嵌套量词一族
#: 会让匹配时间指数增长——实测 `(a+)+$` 对 26 字符已 3.9 s、30 字符再翻约 30 倍。命中即判 FAIL
#: （这是**形态**问题，不是「不支持的关键字」）。存量 442 条 pattern 实测零命中（不误伤）。
_NESTED_QUANT = re.compile(r"\([^()]*[+*][^()]*\)\s*[+*{]")
#: pattern 长度上限（防「写完就挂」的超长表达式；本仓最长实测 < 100 字符）。
MAX_PATTERN_CHARS = 512


def pattern_issue(pat: Any, path: str) -> str:
    """→ 该 pattern 的形态问题（空串 = 可用）。"""
    text = str(pat)
    if len(text) > MAX_PATTERN_CHARS:
        return ("%s: pattern 过长（%d > %d 字符）（修复指引：只写必要的约束）"
                % (path, len(text), MAX_PATTERN_CHARS))
    if _NESTED_QUANT.search(text):
        return ("%s: pattern 含嵌套量词 %r（可能指数回溯）（修复指引：改写表达式，"
                "避免 `(x+)+` / `(x*)*` 这类形态）" % (path, text))
    return ""


def _obj(v: Any) -> dict:
    """空值回退单点（schema 的「or {}」；radon 把每处 or 记为一个分支）。"""
    return v if isinstance(v, dict) else {}


def _arr(v: Any) -> list:
    """空值回退单点（schema 的「or []」）。"""
    return v if isinstance(v, list) else []


def _collect_unsupported(schema: dict, path: str, unsupported: List[str]) -> None:
    """未支持关键字登记（去重；$ 前缀与词表内的都算）。"""
    for kw in sorted(set(schema) - _SUPPORTED):
        if kw in _UNSUPPORTED_WORDS or kw.startswith("$"):
            tag = "%s@%s" % (kw, path)
            if tag not in unsupported:
                unsupported.append(tag)


def _check_ref(instance: Any, schema: dict, path: str, root_schema: dict,
               unsupported: List[str], depth: int, errors: List[str]) -> None:
    """$ref：可解析即递归；远程/悬空进 unsupported（不假装通过）。"""
    if "$ref" not in schema:
        return
    target = _resolve_ref(str(schema["$ref"]), root_schema)
    if target is None:
        unsupported.append("远程/悬空 $ref %s@%s" % (schema["$ref"], path))
        return
    errors += _check(instance, target, path, root_schema, unsupported, depth + 1)


def _check_type(instance: Any, schema: dict, path: str, errors: List[str]) -> None:
    """type：单值或列表，任一命中即过。"""
    types = schema.get("type")
    if types is None:
        return
    cand = types if isinstance(types, list) else [types]
    if not any(_type_ok(instance, t) for t in cand):
        errors.append("%s: 类型应为 %s，实为 %s"
                      % (path, "/".join(map(str, cand)), type(instance).__name__))


def _check_const_enum(instance: Any, schema: dict, path: str,
                      errors: List[str]) -> None:
    """const / enum 两关键字。"""
    if "const" in schema and instance != schema["const"]:
        errors.append("%s: 应为常量 %r" % (path, schema["const"]))
    if "enum" in schema and instance not in schema["enum"]:
        errors.append("%s: 取值 %r 不在枚举内" % (path, instance))


def _check_string(instance: Any, schema: dict, path: str,
                  errors: List[str]) -> None:
    """字符串关键字：长度 / pattern（含形态闸门）/ format。"""
    if not isinstance(instance, str):
        return
    if "minLength" in schema and len(instance) < schema["minLength"]:
        errors.append("%s: 长度 < %s" % (path, schema["minLength"]))
    if "maxLength" in schema and len(instance) > schema["maxLength"]:
        errors.append("%s: 长度 > %s" % (path, schema["maxLength"]))
    if "pattern" in schema:
        why = pattern_issue(schema["pattern"], path)
        if why:
            errors.append(why)
        elif not re.search(str(schema["pattern"]), instance):
            errors.append("%s: 不匹配 pattern %s" % (path, schema["pattern"]))
    fmt = schema.get("format")
    if fmt:
        errors += _format_errors(instance, fmt, path)


def _check_number(instance: Any, schema: dict, path: str,
                  errors: List[str]) -> None:
    """数值关键字：上下界（含排他）与 multipleOf。"""
    if not isinstance(instance, (int, float)) or isinstance(instance, bool):
        return
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


def _check_unique_items(instance: list, path: str, errors: List[str]) -> None:
    """uniqueItems：按规范化 JSON 串判重（顺序/键序不敏感）。"""
    seen = [json.dumps(x, sort_keys=True, ensure_ascii=False) for x in instance]
    if len(set(seen)) != len(seen):
        errors.append("%s: uniqueItems 被违反" % path)


def _check_prefix_items(instance: list, prefix: list, path: str, root_schema: dict,
                        unsupported: List[str], depth: int, errors: List[str]) -> None:
    """prefixItems：逐位子 schema（超出实例长度即止）。"""
    for i, sub in enumerate(prefix):
        if i < len(instance):
            errors += _check(instance[i], sub, "%s[%d]" % (path, i),
                             root_schema, unsupported, depth + 1)


def _check_items(instance: list, items: dict, prefix: Any, path: str,
                 root_schema: dict, unsupported: List[str], depth: int,
                 errors: List[str]) -> None:
    """items：prefixItems 之后的元素都按同一子 schema 校验。"""
    start = len(prefix) if isinstance(prefix, list) else 0
    for i in range(start, len(instance)):
        errors += _check(instance[i], items, "%s[%d]" % (path, i),
                         root_schema, unsupported, depth + 1)


def _check_array(instance: Any, schema: dict, path: str, root_schema: dict,
                 unsupported: List[str], depth: int, errors: List[str]) -> None:
    """数组关键字：元素数 / uniqueItems / prefixItems / items。"""
    if not isinstance(instance, list):
        return
    if "minItems" in schema and len(instance) < schema["minItems"]:
        errors.append("%s: 元素数 < %s" % (path, schema["minItems"]))
    if "maxItems" in schema and len(instance) > schema["maxItems"]:
        errors.append("%s: 元素数 > %s" % (path, schema["maxItems"]))
    if schema.get("uniqueItems"):
        _check_unique_items(instance, path, errors)
    prefix = schema.get("prefixItems")
    if isinstance(prefix, list):
        _check_prefix_items(instance, prefix, path, root_schema, unsupported, depth, errors)
    items = schema.get("items")
    if isinstance(items, dict):
        _check_items(instance, items, prefix, path, root_schema, unsupported, depth, errors)


def _check_required_fields(instance: dict, schema: dict, path: str,
                           errors: List[str]) -> None:
    """required 与 dependentRequired 两面。"""
    for key in _arr(schema.get("required")):
        if key not in instance:
            errors.append("%s: 缺必填字段 %s" % (path, key))
    for dep, need in _obj(schema.get("dependentRequired")).items():
        if dep in instance:
            for n in _arr(need):
                if n not in instance:
                    errors.append("%s: 出现 %s 时必填 %s" % (path, dep, n))


def _check_property(value: Any, key: str, props: dict, pats: dict, schema: dict,
                    path: str, root_schema: dict, unsupported: List[str],
                    depth: int, errors: List[str]) -> None:
    """单键：properties 命中 / patternProperties 命中 / additionalProperties 兜底。"""
    matched = False
    if key in props:
        matched = True
        errors += _check(value, props[key], "%s.%s" % (path, key),
                         root_schema, unsupported, depth + 1)
    for pat, sub in pats.items():
        why = pattern_issue(pat, path)
        if why:
            errors.append(why)          # 形态闸门：不拿投稿者的表达式去跑匹配
            continue
        if re.search(pat, key):
            matched = True
            errors += _check(value, sub, "%s.%s" % (path, key),
                             root_schema, unsupported, depth + 1)
    if matched:
        return
    ap = schema.get("additionalProperties", True)
    if ap is False:
        errors.append("%s: 多余字段 %s（additionalProperties=false）" % (path, key))
    elif isinstance(ap, dict):
        errors += _check(value, ap, "%s.%s" % (path, key),
                         root_schema, unsupported, depth + 1)


def _check_property_names(instance: dict, schema: dict, path: str, root_schema: dict,
                          unsupported: List[str], depth: int,
                          errors: List[str]) -> None:
    """propertyNames：键本身也按子 schema 校验。"""
    pn = schema.get("propertyNames")
    if not isinstance(pn, dict):
        return
    for key in instance:
        errors += _check(key, pn, "%s<键:%s>" % (path, key),
                         root_schema, unsupported, depth + 1)


def _check_object(instance: Any, schema: dict, path: str, root_schema: dict,
                  unsupported: List[str], depth: int, errors: List[str]) -> None:
    """对象关键字：必填 / 逐键 / propertyNames。"""
    if not isinstance(instance, dict):
        return
    props = _obj(schema.get("properties"))
    pats = _obj(schema.get("patternProperties"))
    _check_required_fields(instance, schema, path, errors)
    for key, value in instance.items():
        _check_property(value, key, props, pats, schema, path, root_schema,
                        unsupported, depth, errors)
    _check_property_names(instance, schema, path, root_schema, unsupported, depth, errors)


def _report_combinator(mode: str, ok: int, subs: list, path: str,
                       errors: List[str]) -> None:
    """组合子结论：all 须全过 / any 须至少一个 / one 须恰一个。"""
    if mode == "all" and ok != len(subs):
        errors.append("%s: allOf 有 %d/%d 子式不成立" % (path, len(subs) - ok, len(subs)))
    if mode == "any" and ok == 0:
        errors.append("%s: anyOf 全不成立" % path)
    if mode == "one" and ok != 1:
        errors.append("%s: oneOf 命中 %d 个（须恰 1）" % (path, ok))


def _check_combinators(instance: Any, schema: dict, path: str, root_schema: dict,
                       unsupported: List[str], depth: int,
                       errors: List[str]) -> None:
    """allOf / anyOf / oneOf 三组合子。"""
    for kw, mode in (("allOf", "all"), ("anyOf", "any"), ("oneOf", "one")):
        subs = schema.get(kw)
        if not isinstance(subs, list):
            continue
        results = [_check(instance, s, path, root_schema, unsupported, depth + 1)
                   for s in subs]
        ok = sum(1 for r in results if not r)
        _report_combinator(mode, ok, subs, path, errors)


def _check_not(instance: Any, schema: dict, path: str, root_schema: dict,
               unsupported: List[str], depth: int, errors: List[str]) -> None:
    """not：子式被满足即报错。"""
    if isinstance(schema.get("not"), dict) and not _check(
            instance, schema["not"], path, root_schema, unsupported, depth + 1):
        errors.append("%s: not 子式被满足" % path)


def _check(instance: Any, schema: dict, path: str = "$",
           root_schema: Optional[dict] = None,
           unsupported: Optional[List[str]] = None, _depth: int = 0) -> List[str]:
    """JSON Schema 2020-12 **子集**校验：返回错误清单；不支持的官方关键字进 unsupported。

    子集边界（公开声明，不假装全实现）：见 _SUPPORTED；超出即上报，
    「不支持」绝不等价「通过」。

    深度：超过 MAX_DEPTH 即停（深度是**输入属性**，不是「不支持的关键字」）——报错而不是崩。
    每类关键字一个校验器（_check_type/_check_string/_check_object …），本体只做分派。
    """
    if _depth > MAX_DEPTH:
        return ["%s: 嵌套超过上限 %d 层（修复指引：schema/实例别做这么深的结构；本仓判据面"
                "只处理扁平声明）" % (path, MAX_DEPTH)]
    if root_schema is None:
        root_schema = schema
    if unsupported is None:
        unsupported = []
    if not isinstance(schema, dict):
        return ["%s: schema 节点非对象" % path]
    errors: List[str] = []
    _collect_unsupported(schema, path, unsupported)
    _check_ref(instance, schema, path, root_schema, unsupported, _depth, errors)
    _check_type(instance, schema, path, errors)
    _check_const_enum(instance, schema, path, errors)
    _check_string(instance, schema, path, errors)
    _check_number(instance, schema, path, errors)
    _check_array(instance, schema, path, root_schema, unsupported, _depth, errors)
    _check_object(instance, schema, path, root_schema, unsupported, _depth, errors)
    _check_combinators(instance, schema, path, root_schema, unsupported, _depth, errors)
    _check_not(instance, schema, path, root_schema, unsupported, _depth, errors)
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

def json_schema_check(instance: Any, schema: dict, path: str = "$",
                      root_schema: Optional[dict] = None,
                      unsupported: Optional[List[str]] = None) -> List[str]:
    """公开入口（签名与历史一致）：内部走 `_check(..., _depth=0)`，带 `MAX_DEPTH` 深度闸门。

    为什么要包一层：递归实现需要把深度沿调用链传下去（否则闸门形同虚设），但**调用方不该关心
    这个参数**——本仓 4 个调用面（schema_lint / output_forms / check28 / 工具箱）签名一字不变。
    """
    return _check(instance, schema, path, root_schema, unsupported, 0)
