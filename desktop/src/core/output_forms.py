"""产出形态面（output forms）——把「产出一律是散文」的缺口机制化。

背景（内部差距）：两个非叙事域包（AI系统域包 / 量化金融域包）的产出**全是散文**——
连数据契约、指标表、策略规格都是 Markdown 表格：人能读，机器只能当文本，判不了形状、
判不了单位、判不了引用完整，更复算不了数。本模块把产出**形态**本身当成一等对象：

1. **形态清单**（`protocol/output_forms.json`）：主域全量形态类别（结构化数据 / 表格 /
   图表 / 图结构 / 契约 / 接口 / 时序 / 打包 / 文档 / 金融专业面 / AI 专业面）逐条登记，
   每条带外部规范入口与**可达性实证**（本机 GET 结果），并标注本仓的机验能力档位。
2. **机检档位**（tier）：T0 散文 → T1 良构 → T2 形状（schema/结构）→ T3 语义
   （引用 / 单位 / 口径 / 双源一致）→ T4 **可复算**（本仓引擎重算并与在盘产物逐字段比对）。
3. **自家校验器**：本仓零第三方硬依赖（purity R5），故自带 JSON Schema 2020-12
   **子集**校验器（不支持的官方关键字**显式列出**，绝不静默通过）+ 形态结构校验器
   （Vega-Lite / Mermaid / GraphML / CSV / XML…）。
4. **包级清单**（`community/<包>/outputs/INDEX.json`）：每个包声明自己的机验产出面
   （路径 / 形态 / 档位 / 角色 / schema / 双源 / 复算），check14/check32 据此判定。
5. **机验率与功能面计量**：`machine_verifiable_ratio` = 机验面 /（机验面 + 散文资产），
   `functional_faces` = T4 面数；基线落 `protocol/output_forms_baseline.json`（可重签），
   机验率**回退即 FAIL**（口径同 check8 资产行基线，不把数字写死进 verify.sh）。

纪律：不伪造——形态可达性实证失败如实记档；不支持的关键字显式上报；复算不一致即 FAIL。
"""

from __future__ import annotations

import csv
import io
import json
import os
import re
# 只解析本仓自持产出面；DTD/ENTITY 已在 _xml_guard 前置拒绝
import xml.etree.ElementTree as ET  # noqa: S405  # nosec B405 -- self-authored artifacts only
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

REGISTRY_REL = "protocol/output_forms.json"
BASELINE_REL = "protocol/output_forms_baseline.json"
INDEX_REL = "outputs/INDEX.json"

#: 机检档位（递增）；档位 = **本仓可做的判定强度**，不是「格式有多高级」
TIERS: Tuple[str, ...] = ("T0", "T1", "T2", "T3", "T4")
TIER_MEANING = {
    "T0": "散文（只能人读，机器无判据）",
    "T1": "良构（有语法，可判是否可解析）",
    "T2": "形状（有 schema / 结构断言：类型·必填·枚举）",
    "T3": "语义（引用完整·单位口径·双源一致）",
    "T4": "可复算（本仓引擎重算并与在盘产物逐字段一致）",
}

#: 形态状态（对外可判定口径）
#: supported=本仓既有产出/校验面；absorbed=本波从零构建；planned=登记未做（带触发条件）；
#: deferred=暂缓（有明确前置）；unfit=不适面；reference=实现参考（机制借鉴，非产出形态）；
#: unreachable=规范入口本机不可达（实证 false，不假装可达）。
STATUSES = ("supported", "absorbed", "planned", "deferred", "unfit",
            "reference", "unreachable")

_EXT_FORM = {
    ".json": "json", ".jsonl": "jsonl", ".ndjson": "jsonl", ".yaml": "yaml",
    ".yml": "yaml", ".toml": "toml", ".csv": "csv", ".tsv": "csv", ".xml": "xml",
    ".md": "markdown", ".mmd": "mermaid", ".dot": "graphviz-dot", ".gv": "graphviz-dot",
    ".graphml": "graphml", ".svg": "svg", ".txt": "text", ".proto": "protobuf-proto3",
    ".graphql": "graphql-sdl", ".ttl": "turtle", ".sql": "sql-ddl",
}
#: 形态自身可达的**上限**档位（本仓校验器决定；未实现的形态按扩展名给 T1 兜底）
_FORM_MAX_TIER = {
    "json": "T2", "jsonl": "T2", "yaml": "T2", "toml": "T2", "csv": "T2",
    "xml": "T1", "svg": "T1", "markdown": "T1", "text": "T0",
    "json-schema": "T2", "vega-lite": "T3", "mermaid": "T3", "graphviz-dot": "T3",
    "graphml": "T3", "json-graph-format": "T3", "quant-metrics": "T3",
    "performance-report": "T4", "concept-closure": "T4", "system-card": "T3",
    "domain-spec": "T3", "domain-report": "T4",
}


def _rel(root: str, rel: str) -> Path:
    return Path(root) / rel.replace("/", os.sep)


def _read_json(path: Path) -> Tuple[Any, str]:
    try:
        return json.loads(path.read_text(encoding="utf-8")), ""
    except OSError as exc:
        return None, "不可读：%s" % exc
    except ValueError as exc:
        return None, "JSON 解析失败：%s" % exc


# ---------------------------------------------------------------- 形态清单

def load_registry(root: str = ".") -> Dict[str, Any]:
    data, _ = _read_json(_rel(root, REGISTRY_REL))
    return data if isinstance(data, dict) else {}


def registry_verify(root: str = ".") -> Tuple[List[str], Dict[str, Any]]:
    """形态清单自检：结构合法 + 类别/档位在册 + id 唯一 + 可达性实证齐备。"""
    issues: List[str] = []
    reg = load_registry(root)
    if not reg:
        return ["%s 缺失或不可解析（形态清单是真源）" % REGISTRY_REL], {}
    if reg.get("schema") != "nf-output-forms/1":
        issues.append("schema 应为 nf-output-forms/1，实为 %r" % reg.get("schema"))
    cats = reg.get("categories") or []
    cat_ids = {c.get("id") for c in cats if isinstance(c, dict)}
    if not cat_ids:
        issues.append("categories 为空（形态必须有类别归属）")
    for c in cats:
        if not isinstance(c, dict) or not c.get("id") or not c.get("name"):
            issues.append("categories 条目缺 id/name：%r" % (c,))
    forms = reg.get("forms") or []
    seen: set = set()
    per_cat: Dict[str, int] = {}
    per_tier: Dict[str, int] = {}
    per_status: Dict[str, int] = {}
    unreachable = 0
    for f in forms:
        if not isinstance(f, dict):
            issues.append("forms 条目非对象：%r" % (f,))
            continue
        fid = f.get("id")
        if not fid:
            issues.append("forms 条目缺 id：%r" % (f,))
            continue
        if fid in seen:
            issues.append("形态 id 重复：%s" % fid)
        seen.add(fid)
        if f.get("category") not in cat_ids:
            issues.append("%s 类别未在册：%r" % (fid, f.get("category")))
        if f.get("tier") not in TIERS:
            issues.append("%s 档位非法：%r（预期 %s）" % (fid, f.get("tier"), "/".join(TIERS)))
        if f.get("status") not in STATUSES:
            issues.append("%s 状态非法：%r" % (fid, f.get("status")))
        spec = f.get("spec") or {}
        if f.get("status") != "unfit" and not spec.get("uri"):
            issues.append("%s 缺规范入口 spec.uri（不适面才可空）" % fid)
        ev = f.get("evidence") or {}
        if "reachable" not in ev:
            issues.append("%s 缺可达性实证 evidence.reachable（不伪造：查不到也要记 false）" % fid)
        elif ev.get("reachable") is False:
            unreachable += 1
        per_cat[f.get("category")] = per_cat.get(f.get("category"), 0) + 1
        per_tier[str(f.get("tier"))] = per_tier.get(str(f.get("tier")), 0) + 1
        per_status[str(f.get("status"))] = per_status.get(str(f.get("status")), 0) + 1
    stats = {"forms": len(forms), "categories": len(cat_ids),
             "by_category": per_cat, "by_tier": per_tier, "by_status": per_status,
             "unreachable": unreachable}
    return issues, stats


# ---------------------------------------------------------------- 形态识别

def detect(root: str, rel: str) -> Tuple[str, str]:
    """按扩展名 + 内容嗅探判形态，返回 (form_id, tier)。不猜：认不出即 text/T0。"""
    path = _rel(root, rel)
    ext = path.suffix.lower()
    form = _EXT_FORM.get(ext, "text")
    if ext == ".json":
        data, _ = _read_json(path)
        if isinstance(data, dict):
            sch = str(data.get("$schema") or "")
            if "json-schema.org" in sch:
                form = "json-schema"
            kind = str(data.get("kind") or "")
            if kind.startswith("nf-domain-spec"):
                form = "domain-spec"
            elif kind.startswith("nf-domain-report"):
                form = "domain-report"
            elif kind.startswith("nf-system-card"):
                form = "system-card"
            elif "vega-lite" in sch:
                form = "vega-lite"
            elif "vega" in sch:
                form = "vega"
            elif kind.startswith("nf-performance"):
                form = "performance-report"
            elif kind.startswith("nf-quant-metrics"):
                form = "quant-metrics"
            elif kind.startswith("nf-concept-closure"):
                form = "concept-closure"
    return form, _FORM_MAX_TIER.get(form, "T1")


# ---------------------------------------------------------------- JSON Schema 子集

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


# ---------------------------------------------------------------- 形态结构校验

def _check_json(root: str, rel: str) -> List[str]:
    path = _rel(root, rel)
    raw = path.read_text(encoding="utf-8")
    dups: List[str] = []

    def hook(pairs):
        seen = set()
        for k, _v in pairs:
            if k in seen:
                dups.append(k)
            seen.add(k)
        return dict(pairs)

    try:
        json.loads(raw, object_pairs_hook=hook)
    except ValueError as exc:
        return ["JSON 不可解析：%s" % exc]
    return ["JSON 重复键：%s" % d for d in sorted(set(dups))]


def _check_jsonl(root: str, rel: str) -> List[str]:
    issues: List[str] = []
    for i, line in enumerate(_rel(root, rel).read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            json.loads(line)
        except ValueError as exc:
            issues.append("第 %d 行非 JSON：%s" % (i, exc))
    return issues


def _check_csv(root: str, rel: str) -> List[str]:
    text = _rel(root, rel).read_text(encoding="utf-8")
    if "\x00" in text:
        return ["含 NUL 字节（非文本 CSV）"]
    rows = list(csv.reader(io.StringIO(text)))
    rows = [r for r in rows if r]
    if not rows:
        return ["空表"]
    width = len(rows[0])
    issues = [] if width else ["表头为空"]
    for i, r in enumerate(rows[1:], 2):
        if len(r) != width:
            issues.append("第 %d 行字段数 %d ≠ 表头 %d" % (i, len(r), width))
    if len(set(rows[0])) != width:
        issues.append("表头有重名列")
    return issues


def _check_xml(root: str, rel: str) -> List[str]:
    text = _rel(root, rel).read_text(encoding="utf-8")
    guard = _xml_guard(text)
    if guard:
        return [guard]
    try:
        ET.fromstring(text)  # nosec B314 -- DTD/ENTITY rejected in _xml_guard
    except ET.ParseError as exc:
        return ["XML 良构性失败：%s" % exc]
    return []


_DTD_RE = re.compile(r"<!\s*(?:DOCTYPE|ENTITY)", re.I)


def _xml_guard(text: str) -> str:
    """XML 解析前哨：拒绝 DTD/ENTITY 声明（堵实体展开 / 十亿笑声类攻击）。

    本仓 XML 面（GraphML / SVG）只由本仓生成器写出，不需要 DTD；一旦出现即视为异常输入，
    直接判不合格而不是「带风险解析」——不引第三方（defusedxml）也守住安全面。
    """
    if _DTD_RE.search(text):
        return "含 DTD/ENTITY 声明（本仓 XML 产出面禁 DTD：堵实体展开类攻击）"
    return ""


def _check_markdown(root: str, rel: str) -> List[str]:
    text = _rel(root, rel).read_text(encoding="utf-8")
    issues = []
    if not text.strip():
        issues.append("空档")
    if text.count("```") % 2:
        issues.append("代码围栏未闭合（``` 奇数个）")
    return issues


def _check_toml(root: str, rel: str) -> List[str]:
    try:
        import tomllib  # Python 3.11+ 标准库
    except ImportError:  # pragma: no cover - 3.10 及以下
        return []
    try:
        tomllib.loads(_rel(root, rel).read_text(encoding="utf-8"))
    except Exception as exc:
        return ["TOML 不可解析：%s" % exc]
    return []


def _check_yaml(root: str, rel: str) -> List[str]:
    """YAML 只做**收窄子集**良构判定（本项目自用面：映射/列表/标量），不引第三方。"""
    text = _rel(root, rel).read_text(encoding="utf-8")
    issues: List[str] = []
    for i, line in enumerate(text.splitlines(), 1):
        if "\t" in line[: len(line) - len(line.lstrip())]:
            issues.append("第 %d 行用 Tab 缩进（YAML 禁 Tab）" % i)
        stripped = line.strip()
        if stripped.startswith("- ") or not stripped or stripped.startswith("#"):
            continue
        if ":" not in line:
            issues.append("第 %d 行非映射项（收窄子集要求 key: value）：%s" % (i, stripped[:40]))
    return issues


def _check_vega_lite(root: str, rel: str) -> List[str]:
    data, err = _read_json(_rel(root, rel))
    if err:
        return [err]
    issues: List[str] = []
    if "vega-lite" not in str(data.get("$schema") or ""):
        issues.append("缺 $schema（应为 vega-lite v5）")
    if not any(k in data for k in ("mark", "layer", "hconcat", "vconcat",
                                   "concat", "facet", "spec", "repeat")):
        issues.append("缺 mark/layer 等绘图主体")
    if "data" not in data:
        issues.append("缺 data（图不能没有数据源）")
    enc = data.get("encoding")
    if isinstance(enc, dict):
        for ch, spec in enc.items():
            if not isinstance(spec, dict):
                issues.append("encoding.%s 非对象" % ch)
                continue
            if not any(k in spec for k in ("field", "aggregate", "value", "datum",
                                           "timeUnit", "bin")):
                issues.append("encoding.%s 无 field/aggregate/value（通道未绑定）" % ch)
    elif enc is not None and not isinstance(enc, dict):
        issues.append("encoding 非对象")
    return issues


_MERMAID_KINDS = ("graph", "flowchart", "sequencediagram", "classdiagram",
                  "erdiagram", "statediagram", "gantt", "pie", "journey", "mindmap")


def _check_mermaid(root: str, rel: str) -> List[str]:
    lines = [x.rstrip() for x in _rel(root, rel).read_text(encoding="utf-8").splitlines()]
    body = [x for x in lines if x.strip() and not x.strip().startswith("%%")]
    if not body:
        return ["空图"]
    issues = []
    head = body[0].strip().lower()
    if not any(head.startswith(k) for k in _MERMAID_KINDS):
        issues.append("首行非已知图种：%r" % body[0].strip()[:40])
    return issues


def _check_dot(root: str, rel: str) -> List[str]:
    text = _rel(root, rel).read_text(encoding="utf-8")
    issues = []
    if not re.search(r"^\s*(strict\s+)?(di)?graph\b", text, re.M):
        issues.append("缺 digraph/graph 头")
    if text.count("{") != text.count("}"):
        issues.append("花括号不配对（{ %d / } %d）" % (text.count("{"), text.count("}")))
    return issues


def _check_graphml(root: str, rel: str) -> List[str]:
    path = _rel(root, rel)
    guard = _xml_guard(path.read_text(encoding="utf-8"))
    if guard:
        return ["GraphML %s" % guard]
    try:
        tree = ET.parse(path)  # nosec B314 -- DTD/ENTITY rejected in _xml_guard
    except ET.ParseError as exc:
        return ["GraphML XML 解析失败：%s" % exc]
    r = tree.getroot()
    tag = r.tag.split("}")[-1]
    issues = []
    if tag != "graphml":
        issues.append("根元素应为 graphml，实为 %s" % tag)
    graphs = r.findall(".//{*}graph")
    if not graphs:
        issues.append("缺 <graph> 元素")
    nodes = {n.get("id") for g in graphs for n in g.findall("{*}node")}
    for g in graphs:
        for e in g.findall("{*}edge"):
            for end in ("source", "target"):
                if e.get(end) not in nodes:
                    issues.append("边端点悬空：%s=%s" % (end, e.get(end)))
    return issues


def _check_quant_metrics(root: str, rel: str) -> List[str]:
    """口径注册表语义检查：**宣称的引擎必须真实存在**（宣称≠实现），口径参数自洽。"""
    issues = _check_json(root, rel)
    data, err = _read_json(_rel(root, rel))
    if err or not isinstance(data, dict):
        return issues + ([err] if err else [])
    from core import quant_metrics as qm

    for m in list(data.get("metrics") or []) + list(data.get("declared_only") or []):
        if not isinstance(m, dict):
            issues.append("条目非对象：%r" % (m,))
            continue
        mid = m.get("id") or "?"
        eng = str(m.get("engine") or "")
        if eng:
            mod, _, fn = eng.partition(":")
            if mod != "quant_metrics" or not hasattr(qm, fn):
                issues.append("%s: 宣称 engine=%s，但 core/quant_metrics 无该实现（宣称≠实现）"
                              % (mid, eng))
        if m.get("verifiable") == "T4" and not eng:
            issues.append("%s: 标 T4（可复算）却无 engine" % mid)
        params = m.get("required_params") or []
        if m.get("annual_factor_required") and "annual_factor" not in params:
            issues.append("%s: 需年化因子却未列入 required_params（口径四要素不全）" % mid)
    names = {str(m.get("id")) for m in (data.get("metrics") or [])}
    expected = {k for k in data.get("annual_factors", {})}
    if expected != {"daily", "weekly", "monthly"}:
        issues.append("annual_factors 键集应为 daily/weekly/monthly，实为 %s" % sorted(expected))
    if len(names) != len(data.get("metrics") or []):
        issues.append("metrics 存在重复 id")
    return issues


def _check_domain_spec(root: str, rel: str) -> List[str]:
    """域口径表机读投影：条数口径 + id 序 + 判据/锚齐备（语义面，不只形状）。"""
    issues = _check_json(root, rel)
    data, err = _read_json(_rel(root, rel))
    if err or not isinstance(data, dict):
        return issues + ([err] if err else [])
    code = str(data.get("code") or "")
    subs = data.get("subdivisions") or []
    if len(subs) != 12:
        issues.append("细分条目应为 12 条，实为 %d" % len(subs))
    for i, s in enumerate(subs, 1):
        want = "%s-%02d" % (code, i)
        if s.get("id") != want:
            issues.append("第 %d 条 id 应为 %s，实为 %r" % (i, want, s.get("id")))
        if not str(s.get("anchor") or "").startswith(("http://", "https://")):
            issues.append("%s 锚非绝对 URL" % s.get("id"))
        if int(s.get("anchor_status") or 0) == 0:
            issues.append("%s 锚缺可达性实测值（不得假装可达：探不到记 0 并在锚表注明）"
                          % s.get("id"))
    return issues


def _check_domain_report(root: str, rel: str) -> List[str]:
    """域报告：形状 + 口径族在册 + 样例规模自洽（复算一致由 recompute 面判）。"""
    from core import domain_metrics as dm

    issues = _check_json(root, rel)
    data, err = _read_json(_rel(root, rel))
    if err or not isinstance(data, dict):
        return issues + ([err] if err else [])
    fam = str(data.get("family") or "")
    if fam not in dm.FAMILIES:
        issues.append("度量族未在本仓引擎登记：%r（不得宣称可复算）" % fam)
    metrics = data.get("metrics") or {}
    if str(metrics.get("family") or "") != fam:
        issues.append("metrics.family 与报告 family 不一致")
    if int(data.get("sample_rows") or 0) < 1:
        issues.append("样例规模为 0（无样例即无口径值）")
    return issues


_FORM_CHECK: Dict[str, Callable[[str, str], List[str]]] = {
    "json": _check_json, "json-schema": _check_json, "vega-lite": _check_vega_lite,
    "vega": _check_json, "jsonl": _check_jsonl, "csv": _check_csv, "xml": _check_xml,
    "markdown": _check_markdown, "toml": _check_toml, "yaml": _check_yaml,
    "mermaid": _check_mermaid, "graphviz-dot": _check_dot, "graphml": _check_graphml,
    "svg": _check_xml, "json-graph-format": _check_json,
    "quant-metrics": _check_quant_metrics, "performance-report": _check_json,
    "concept-closure": _check_json, "system-card": _check_json,
    "domain-spec": _check_domain_spec, "domain-report": _check_domain_report,
}


# ---------------------------------------------------------------- 包级产出清单

def _pack_dirs(root: str) -> List[str]:
    base = Path(root) / "community"
    if not base.is_dir():
        return []
    return sorted(d.name for d in base.iterdir()
                  if d.is_dir() and (_rel(root, "community/%s/%s" % (d.name, INDEX_REL))).is_file())


def _gen_performance_report(root: str, entry: dict):
    """由净值数据用本仓引擎装配绩效报告（GIPS 对齐披露面）。"""
    from core import quant_metrics as qm

    spec = entry.get("recompute") or entry.get("render") or {}
    inputs = spec.get("inputs") or []
    if not inputs:
        return None, ["声明可复算/可渲染但缺 inputs（无源即无功能）"]
    src = _pkg_rel(entry, inputs[0])
    series, err = qm.load_equity_curve(_rel(root, src))
    if err:
        return None, ["输入 %s %s" % (src, err)]
    params = dict(spec.get("params") or {})
    try:
        return qm.performance_report(series, **params), []
    except Exception as exc:  # 参数口径错误必须可见，不得静默兜底
        return None, ["复算异常 %s: %s" % (type(exc).__name__, exc)]


def _gen_concept_closure(root: str, entry: dict):
    """由概念图资产复算闭包/装载序（AI系统域包的 M25/M26 产物面）。"""
    from core import concept_graph as cg

    spec = entry.get("recompute") or entry.get("render") or {}
    graph_path = _pkg_rel(entry, spec.get("graph") or cg.DEFAULT_ASSET)
    target = spec.get("target") or ""
    if not target:
        return None, ["声明可复算但缺 target"]
    graph = cg.load_graph(_rel(root, graph_path))
    if not graph:
        return None, ["概念图 %s 不可解析（无源）" % graph_path]
    return {
        "kind": "nf-concept-closure/1",
        "graph": graph_path,
        "target": target,
        "closure": [cg.resolve(graph, x) for x in cg.closure(graph, target)],
        "load_order": cg.toposort(graph),
        "alias": [[k, v] for k, v in sorted(cg.alias_map(graph).items())],
    }, []


def _gen_vega(root: str, entry: dict):
    from core import quant_metrics as qm

    spec = entry.get("recompute") or entry.get("render") or {}
    inputs = spec.get("inputs") or []
    if not inputs:
        return None, ["图表面缺 inputs"]
    src = _pkg_rel(entry, inputs[0])
    series, err = qm.load_equity_curve(_rel(root, src))
    if err:
        return None, ["输入 %s %s" % (src, err)]
    params = dict(spec.get("params") or {})
    which = spec.get("id")
    if which == "vega-drawdown":
        return qm.vega_drawdown(series, **params), []
    return qm.vega_equity_curve(series, **params), []


def _gen_mermaid(root: str, entry: dict):
    from core import quant_metrics as qm

    spec = entry.get("recompute") or entry.get("render") or {}
    if spec.get("id") == "mermaid-declaration-flow":
        return qm.mermaid_declaration_flow(), []
    return None, ["未登记 Mermaid 生成器：%r" % spec.get("id")]


def _gen_domain_report(root: str, entry: dict):
    """域包 T4 面：由样例夹具按声明度量族重算域报告（core/domain_metrics）。"""
    from core import domain_metrics as dm

    spec = entry.get("recompute") or entry.get("render") or {}
    inputs = spec.get("inputs") or []
    params = dict(spec.get("params") or {})
    family = str(params.pop("family", ""))
    if not inputs or not family:
        return None, ["域报告缺 inputs 或 family（无源/无族即无功能）"]
    src = _pkg_rel(entry, inputs[0])
    rows, err = dm.load_rows(_rel(root, src))
    if err:
        return None, ["输入 %s %s" % (src, err)]
    try:
        metrics = dm.evaluate(family, rows, **params)
    except Exception as exc:  # 口径参数错误必须可见
        return None, ["复算异常 %s: %s" % (type(exc).__name__, exc)]
    return {
        "kind": "nf-domain-report/1",
        "code": str(params.get("code") or ""),
        "domain": str(params.get("domain") or ""),
        "family": family,
        "sample": inputs[0],
        "sample_rows": len(rows),
        "metrics": metrics,
    }, []


def _gen_vega_metrics(root: str, entry: dict):
    """指标条形图：由域报告里的标量指标确定性生成 Vega-Lite 规格。"""
    spec = entry.get("render") or entry.get("recompute") or {}
    inputs = spec.get("inputs") or []
    if not inputs:
        return None, ["图表面缺 inputs"]
    data, err = _read_json(_rel(root, _pkg_rel(entry, inputs[0])))
    if err:
        return None, ["输入 %s %s" % (inputs[0], err)]
    vals = []
    for k, v in sorted((data.get("metrics") or {}).items()):
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            vals.append({"metric": k, "value": float(v)})
    if not vals:
        return None, ["报告里没有可画的标量指标"]
    return {
        "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
        "description": str(spec.get("params", {}).get("title") or "域指标"),
        "data": {"values": vals},
        "mark": {"type": "bar"},
        "encoding": {
            "x": {"field": "value", "type": "quantitative", "title": "口径值"},
            "y": {"field": "metric", "type": "nominal", "title": "指标",
                  "sort": "-x"},
        },
    }, []


def _gen_mermaid_concept_dag(root: str, entry: dict):
    """概念图 → Mermaid（按层分组的流程图）；图即数据，节点/边由概念图导出。"""
    from core import concept_graph as cg

    spec = entry.get("recompute") or entry.get("render") or {}
    graph_path = _pkg_rel(entry, spec.get("graph") or cg.DEFAULT_ASSET)
    graph = cg.load_graph(_rel(root, graph_path))
    if not graph:
        return None, ["概念图 %s 不可解析（无源）" % graph_path]
    prereq = cg.prereqs_of(graph)
    layer = {n: (m.get("layer") or "P00") for n, m in cg.node_meta(graph).items()}
    lines = ["%% 概念前置图（由 " + graph_path + " 确定性派生；唯一机读真相在资产 §4 围栏块）",
             "flowchart TD"]
    seen_layers = []
    for node in cg.in_package_ids(graph):
        lay = layer.get(node, "P00")
        if lay not in seen_layers:
            seen_layers.append(lay)
    for lay in sorted(seen_layers):
        ids = [n for n in cg.in_package_ids(graph) if layer.get(n) == lay]
        if not ids:
            continue
        lines.append("  subgraph %s[%s]" % (lay, lay))
        for n in ids:
            lines.append("    %s" % n)
        lines.append("  end")
    for node in cg.in_package_ids(graph):
        for pre in prereq.get(node, []):
            if pre.startswith("C0") and pre == "C00":
                continue
            lines.append("  %s --> %s" % (pre, node))
    return "\n".join(lines) + "\n", []


def _gen_graphml_concept_dag(root: str, entry: dict):
    """概念图 → GraphML（图交换形态）：边端点引用完整性由形态校验器判定。"""
    from core import concept_graph as cg

    spec = entry.get("recompute") or entry.get("render") or {}
    graph_path = _pkg_rel(entry, spec.get("graph") or cg.DEFAULT_ASSET)
    graph = cg.load_graph(_rel(root, graph_path))
    if not graph:
        return None, ["概念图 %s 不可解析（无源）" % graph_path]
    prereq = cg.prereqs_of(graph)
    meta = cg.node_meta(graph)
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<graphml xmlns="http://graphml.graphdrawing.org/xmlns">',
           '  <key id="layer" for="node" attr.name="layer" attr.type="string"/>',
           '  <key id="branch" for="node" attr.name="branch" attr.type="string"/>',
           '  <key id="provenance" for="edge" attr.name="provenance" attr.type="string"/>',
           '  <graph id="concept-graph" edgedefault="directed">']
    nodes = list(cg.in_package_ids(graph))
    for node in list(nodes):                # 包外前置（如 C00）：声明存在，作为图节点保留
        for pre in prereq.get(node, []):
            if pre not in nodes:
                nodes.append(pre)
    for node in nodes:
        m = meta.get(node, {})
        out.append('    <node id="%s">' % node)
        out.append('      <data key="layer">%s</data>' % (m.get("layer") or ""))
        out.append('      <data key="branch">%s</data>' % (m.get("branch") or ""))
        out.append('    </node>')
    for node in nodes:
        for pre in prereq.get(node, []):
            out.append('    <edge source="%s" target="%s">' % (pre, node))
            out.append('      <data key="provenance">%s</data>' % (m_prov(meta, node, pre)))
            out.append('    </edge>')
    out += ['  </graph>', '</graphml>']
    return "\n".join(out) + "\n", []


def m_prov(meta: dict, node: str, pre: str) -> str:
    """边溯源：取目标节点 provenance（概念图边级溯源在资产内，缺则标 unknown）。"""
    return str((meta.get(node) or {}).get("provenance") or "unknown")


#: 生成器登记（**唯一入口**：渲染与复算共用同一函数——不复算的渲染 = 手写，禁）
GENERATORS: Dict[str, Callable[[str, dict], Tuple[Any, List[str]]]] = {
    "performance-report": _gen_performance_report,
    "concept-closure": _gen_concept_closure,
    "vega-equity-curve": _gen_vega,
    "vega-drawdown": _gen_vega,
    "mermaid-declaration-flow": _gen_mermaid,
    "mermaid-concept-dag": _gen_mermaid_concept_dag,
    "graphml-concept-dag": _gen_graphml_concept_dag,
    "domain-report": _gen_domain_report,
    "vega-metrics": _gen_vega_metrics,
}


def _gen_id(entry: dict) -> str:
    for key in ("recompute", "render"):
        spec = entry.get(key)
        if isinstance(spec, dict) and spec.get("id"):
            return str(spec["id"])
    return ""


def _pkg_rel(entry: dict, rel: str) -> str:
    """包内声明的相对路径 → 仓库相对路径（以本包目录为根）。"""
    pkg = entry.get("_pkg") or ""
    if rel.startswith("community/") or not pkg:
        return rel
    return "community/%s/%s" % (pkg, rel.lstrip("/"))


def _dump(value: Any) -> str:
    if isinstance(value, str):
        return value if value.endswith("\n") else value + "\n"
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _recompute_entry(root: str, entry: dict) -> Tuple[List[str], Dict[str, Any]]:
    """T4 复算：生成器重算 → 与在盘产物比对（JSON 逐字段 / 文本逐字节）。"""
    out_rel = entry["path"]
    gen = GENERATORS.get(_gen_id(entry))
    if gen is None:
        return ["%s 声明复算 %r 无对应引擎（不得假装可复算）" % (out_rel, _gen_id(entry))], {}
    fresh, errs = gen(root, entry)
    if fresh is None:
        return ["%s: %s" % (out_rel, e) for e in errs], {}
    on_disk = _rel(root, _pkg_rel(entry, out_rel)).read_bytes()
    if isinstance(fresh, str):
        diffs = [] if on_disk == _dump(fresh).encode("utf-8") else ["文本面与复算不一致（逐字节）"]
    else:
        try:
            declared = json.loads(on_disk.decode("utf-8"))
        except (ValueError, UnicodeDecodeError) as exc:
            return ["%s: 在盘产物不可解析 %s" % (out_rel, exc)], {}
        diffs = _deep_diff(fresh, {k: declared.get(k) for k in fresh})
        if b"\r\n" in on_disk:
            diffs.append("在盘产物含 CRLF（仓库 EOL 契约 = LF）")
    return ["%s: 复算与在盘不一致 %s" % (out_rel, d) for d in diffs], {"diff": len(diffs)}


def render_outputs(root: str = ".", package: str = "", write: bool = False
                   ) -> Tuple[List[str], List[Dict[str, Any]]]:
    """渲染包内声明的产出面（数据 / 图表）：--write 才落盘；缺生成器即报错不静默。"""
    issues: List[str] = []
    rows: List[Dict[str, Any]] = []
    for pkg in _pack_dirs(root):
        if package and pkg != package:
            continue
        idx, err = _read_json(_rel(root, "community/%s/%s" % (pkg, INDEX_REL)))
        if err:
            issues.append("%s: %s" % (pkg, err))
            continue
        for entry in (idx.get("outputs") or []):
            gid = _gen_id(entry)
            if not gid:
                continue
            gen = GENERATORS.get(gid)
            if gen is None:
                issues.append("%s/%s: 未登记生成器 %r" % (pkg, entry.get("path"), gid))
                continue
            value, errs = gen(root, {**entry, "_pkg": pkg})
            if value is None:
                issues += ["%s/%s: %s" % (pkg, entry.get("path"), e) for e in errs]
                continue
            dest = _rel(root, "community/%s/%s" % (pkg, entry["path"]))
            text = _dump(value)
            # 逐字节比对（含 EOL）：产物契约 = LF，故 CRLF 也算「需要重渲染」
            changed = (not dest.is_file()) or dest.read_bytes() != text.encode("utf-8")
            if write and changed:
                dest.parent.mkdir(parents=True, exist_ok=True)
                # EOL 纪律：仓库 = LF（.gitattributes `* text=auto eol=lf`）；Windows 文本模式
                # 默认会把 \n 写成 \r\n → 必须显式 newline="\n"（check33 编码卫生会判 FAIL）
                dest.write_text(text, encoding="utf-8", newline="\n")
            rows.append({"package": pkg, "path": entry["path"], "generator": gid,
                         "changed": changed, "written": bool(write and changed)})
    return issues, rows


def _deep_diff(a: Any, b: Any, path: str = "$", out: Optional[List[str]] = None) -> List[str]:
    if out is None:
        out = []
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            if k not in a:
                out.append("%s.%s 仅存于在盘" % (path, k))
            elif k not in b:
                out.append("%s.%s 仅存于复算" % (path, k))
            else:
                _deep_diff(a[k], b[k], "%s.%s" % (path, k), out)
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            out.append("%s 长度 %d≠%d" % (path, len(a), len(b)))
        for i, (x, y) in enumerate(zip(a, b)):
            _deep_diff(x, y, "%s[%d]" % (path, i), out)
    elif isinstance(a, (int, float)) and isinstance(b, (int, float)) \
            and not isinstance(a, bool) and not isinstance(b, bool):
        if abs(float(a) - float(b)) > 1e-9:
            out.append("%s 数值 %r≠%r" % (path, a, b))
    elif a != b:
        out.append("%s %r≠%r" % (path, a, b))
    return out


def index_verify(root: str = ".") -> Tuple[List[str], Dict[str, Any]]:
    """包级产出清单机检：声明存在 / 形态与档位属实 / schema 校验 / 双源一致 / T4 复算。"""
    issues: List[str] = []
    rows: List[Dict[str, Any]] = []
    for pkg in _pack_dirs(root):
        rel = "community/%s/%s" % (pkg, INDEX_REL)
        idx, err = _read_json(_rel(root, rel))
        if err:
            issues.append("%s: %s" % (rel, err))
            continue
        if idx.get("schema") != "nf-output-index/1":
            issues.append("%s: schema 应为 nf-output-index/1" % rel)
        if idx.get("package") != pkg:
            issues.append("%s: package 字段 %r ≠ 包目录名 %r" % (rel, idx.get("package"), pkg))
        for entry in idx.get("outputs") or []:
            path = entry.get("path") or ""
            form = entry.get("form") or ""
            tier = entry.get("tier") or ""
            if not path:
                issues.append("%s: outputs 条目缺 path" % rel)
                continue
            if tier not in TIERS:
                issues.append("%s: %s 档位非法 %r" % (rel, path, tier))
                continue
            if not _rel(root, "community/%s/%s" % (pkg, path)).is_file():
                issues.append("%s: 声明产出面不存在 %s" % (rel, path))
                continue
            got_form, got_tier = detect(root, "community/%s/%s" % (pkg, path))
            if form and form != got_form:
                issues.append("%s: %s 声明形态 %s，实测 %s" % (rel, path, form, got_form))
            if TIERS.index(tier) > TIERS.index(got_tier):
                issues.append("%s: %s 声明档位 %s 超出本仓可判上限 %s"
                              % (rel, path, tier, got_tier))
            checker = _FORM_CHECK.get(form or got_form)
            sub = checker(root, "community/%s/%s" % (pkg, path)) if checker else []
            issues += ["%s: %s %s" % (rel, path, s) for s in sub]
            sch_rel = entry.get("schema") or ""
            if sch_rel:
                full = "community/%s/%s" % (pkg, sch_rel)
                schema, serr = _read_json(_rel(root, full))
                if serr:
                    issues.append("%s: %s schema %s" % (rel, path, serr))
                else:
                    inst, ierr = _read_json(_rel(root, "community/%s/%s" % (pkg, path)))
                    if ierr:
                        issues.append("%s: %s %s" % (rel, path, ierr))
                    else:
                        unsup: List[str] = []
                        errs = json_schema_check(inst, schema, unsupported=unsup)
                        issues += ["%s: %s schema 不符 %s" % (rel, path, e) for e in errs[:8]]
            ds = entry.get("dual_source")
            if isinstance(ds, dict):
                issues += ["%s: %s %s" % (rel, path, m)
                           for m in _dual_source_check(root, pkg, path, ds)]
            rc = entry.get("recompute")
            if isinstance(rc, dict):
                sub_issues, _st = _recompute_entry(root, {**entry, "_pkg": pkg})
                issues += ["%s: %s" % (rel, s) for s in sub_issues]
            elif tier == "T4":
                issues.append("%s: %s 声明 T4（可复算）却无 recompute 声明" % (rel, path))
            rows.append({"package": pkg, "path": path, "form": form or got_form,
                         "tier": tier, "role": entry.get("role") or ""})
    stats = {"packages": len(_pack_dirs(root)), "outputs": len(rows),
             "by_role": _count(rows, "role"), "by_tier": _count(rows, "tier"),
             "by_form": _count(rows, "form")}
    return issues, stats


def _count(rows: Sequence[Dict[str, Any]], key: str) -> Dict[str, int]:
    out: Dict[str, int] = {}
    for r in rows:
        out[str(r.get(key))] = out.get(str(r.get(key)), 0) + 1
    return dict(sorted(out.items()))


def _dual_source_check(root: str, pkg: str, path: str, ds: dict) -> List[str]:
    """双源一致：数据面 vs 散文面（键集必须互为子集）。"""
    md_rel = ds.get("markdown") or ""
    key_re = re.compile(ds.get("key_pattern") or r"`([A-Z][A-Z0-9_]{2,})`")
    md_path = _rel(root, "community/%s/%s" % (pkg, md_rel))
    if not md_path.is_file():
        return ["双源对照件不存在：%s" % md_rel]
    md_keys = set(key_re.findall(md_path.read_text(encoding="utf-8")))
    for drop in (ds.get("exclude") or []):
        md_keys.discard(str(drop))
    data, err = _read_json(_rel(root, "community/%s/%s" % (pkg, path)))
    if err:
        return [err]
    field = ds.get("field") or "id"
    data_keys = set()
    for _key, value in data.items():          # 数据面任意列表（metrics / declared_only …）
        if not isinstance(value, list):
            continue
        for item in value:
            if isinstance(item, dict) and item.get(field):
                data_keys.add(str(item[field]))
    only_md = sorted(md_keys - data_keys)
    only_data = sorted(data_keys - md_keys)
    out = []
    if only_md:
        out.append("双源不一致：散文面独有键 %s" % only_md[:6])
    if only_data:
        out.append("双源不一致：数据面独有键 %s" % only_data[:6])
    return out


# ---------------------------------------------------------------- 机验率计量

def meter(root: str = ".") -> Tuple[List[str], Dict[str, Any]]:
    """机验率与功能面计量（不改盘；基线比对见 baseline_verify）。"""
    stats: Dict[str, Any] = {"packages": {}, "totals": {}}
    for pkg in _pack_dirs(root):
        idx, _err = _read_json(_rel(root, "community/%s/%s" % (pkg, INDEX_REL)))
        entries = (idx or {}).get("outputs") or []
        mv = [e for e in entries if e.get("tier") in ("T2", "T3", "T4")]
        fn_faces = [e for e in entries if e.get("tier") == "T4"]
        prose = [p.name for p in (_rel(root, "community/%s/assets" % pkg)).glob("*.md")
                 if p.name != "README.md"] if _rel(root, "community/%s/assets" % pkg).is_dir() else []
        denom = len(mv) + len(prose)
        stats["packages"][pkg] = {
            "machine_verifiable": len(mv),
            "functional": len(fn_faces),
            "prose_assets": len(prose),
            "machine_verifiable_ratio": round(len(mv) / denom, 4) if denom else 0.0,
            "roles": _count([{"r": e.get("role")} for e in entries], "r"),
            "tiers": _count([{"t": e.get("tier")} for e in entries], "t"),
        }
    pkgs = stats["packages"]
    if pkgs:
        stats["totals"] = {
            "machine_verifiable": sum(p["machine_verifiable"] for p in pkgs.values()),
            "functional": sum(p["functional"] for p in pkgs.values()),
            "prose_assets": sum(p["prose_assets"] for p in pkgs.values()),
            "machine_verifiable_ratio": round(
                sum(p["machine_verifiable"] for p in pkgs.values())
                / max(1, sum(p["machine_verifiable"] + p["prose_assets"] for p in pkgs.values())), 4),
        }
    return [], stats


def baseline_verify(root: str = ".") -> Tuple[List[str], Dict[str, Any]]:
    """机验率基线（可重签）：低于基线即 FAIL——防「新增产出又退回散文」。"""
    issues: List[str] = []
    base, err = _read_json(_rel(root, BASELINE_REL))
    _, stats = meter(root)
    if err:
        return ["%s 缺失或不可解析（%s；重签：nf output meter --write）" % (BASELINE_REL, err)], stats
    prev = (base.get("packages") or {})
    for pkg, cur in stats["packages"].items():
        old = prev.get(pkg)
        if old is None:
            continue
        if cur["machine_verifiable"] < int(old.get("machine_verifiable", 0)):
            issues.append("%s 机验产出面回退：%d → %d（基线 %s）"
                          % (pkg, int(old.get("machine_verifiable", 0)),
                             cur["machine_verifiable"], BASELINE_REL))
        if cur["functional"] < int(old.get("functional", 0)):
            issues.append("%s 功能面（T4 可复算）回退：%d → %d"
                          % (pkg, int(old.get("functional", 0)), cur["functional"]))
    return issues, {"baseline": bool(base), **stats}


def write_baseline(root: str = ".") -> Dict[str, Any]:
    _, stats = meter(root)
    doc = {
        "schema": "nf-output-forms-baseline/1",
        "note": "机验率/功能面基线（可重签工件）。低于基线即 check32 失败——"
                "产出形态不得从数据/契约退回散文。重签：nf output meter --write",
        "packages": {k: {"machine_verifiable": v["machine_verifiable"],
                         "functional": v["functional"],
                         "prose_assets": v["prose_assets"],
                         "machine_verifiable_ratio": v["machine_verifiable_ratio"]}
                     for k, v in stats["packages"].items()},
        "totals": stats["totals"],
    }
    dest = _rel(root, BASELINE_REL)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(doc, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8", newline="\n")
    return doc


def scan(root: str = ".") -> Tuple[List[str], Dict[str, Any]]:
    """check32 子扫描入口：形态清单 + 包级产出清单 + 机验率基线三合一。"""
    issues: List[str] = []
    reg_issues, reg_stats = registry_verify(root)
    issues += ["形态清单: %s" % i for i in reg_issues]
    idx_issues, idx_stats = index_verify(root)
    issues += ["包级产出面: %s" % i for i in idx_issues]
    base_issues, base_stats = baseline_verify(root)
    issues += ["机验率基线: %s" % i for i in base_issues]
    stats = {"registry": reg_stats, "index": idx_stats,
             "meter": base_stats.get("packages", {})}
    return issues, stats
