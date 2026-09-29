"""43 A1 —— 协议层 IDL 校验器（自实现 JSON-schema 子集 + 全量件扫描）。

零第三方 JSON-schema 实现红线：本模块自实现子集校验（type/required/
properties/propertyNames/enum/pattern/minLength/minItems/maxItems/minimum
+ additionalProperties），不引 jsonschema。YAML 解析复用仓库既有 PyYAML
依赖（verify check16 已用）。

扫描对象（见 protocol/README.md）：
- contract  模块头 machine_contract（04_模块库 + community/*/modules）
- module    registry.json modules[]（02 §2 投影）
- pipeline  管线声明 Pipeline（03_管线库 + community/*/pipelines）
- protocol  community/*/protocol.yaml（01 §6.1）
- asset     05_资产库/provenance.json assets[]（S2 台账）

用法：schema_lint.scan('.') -> (issues: list[str], stats: dict)
"""

from __future__ import annotations

import glob
import hashlib
import json
import os
import re
from typing import Any, Dict, List, Optional, Tuple

from core import conformance_scan as _csc   # 统一 YAML 加载器 / 围栏解析缓存真源

#: 逐件校验（围栏解析 + 子集校验）的**内容键缓存**用的占位路径前缀：结果按「与路径无关」的形状存，
#: 取用时再把前缀换成真实相对路径。依据（实测 2026-09-29）：`schema_lint.scan` 稳态 51 ms 里，
#: 逐件子集校验与围栏解析是绝大部分（`subset_validate` 28291 次调用、`_fence_yaml` 363 次），
#: 而它们只是「**该件正文** + schema 定义」的纯函数——改与协议件无关的件时必然不变。
_PATH_PLACEHOLDER = "\x00NFDOC\x00"
_DOC_LINT_CACHE: Dict[Any, Any] = {}
_DOC_LINT_CACHE_MAX = 4096

SCHEMA_DIR = os.path.join("protocol", "schema")

#: 本校验器**实现的 JSON-Schema 方言**（自实现子集的语义归属）。
#: 五份 schema 的 `$schema` 声明必须等于它——声明与实现不一致 = 方言虚标
#: （子集是按 draft 2020-12 的形状做的：propertyNames 等属 2019-09+ 关键字）。
DIALECT = "https://json-schema.org/draft/2020-12/schema"

# 校验器已实现的关键字白名单（子集边界显式化）：
# schema 定义若使用白名单之外的关键字（oneOf/$ref/patternProperties/format…），
# check28 将 FAIL——防止「校验器声称子集却静默忽略语义」的假绿。
SUBSET_ALLOWED_KEYS = {
    "$schema", "$id", "title", "description", "type",
    "required", "properties", "propertyNames", "additionalProperties", "items",
    "enum", "pattern", "minLength", "minimum", "minItems", "maxItems",
}


def subset_key_violations(schema: Any, path: str = "schema") -> List[str]:
    """递归扫描 schema 定义里校验器未实现的关键字（越界即 FAIL）。"""
    if not isinstance(schema, dict):
        return []
    out = [
        f"{path}: 使用了校验器未实现的关键字 {key}（JSON-schema 子集越界——"
        "check28 无法兑现该语义；须扩展校验器或删除该关键字）"
        for key in schema
        if key not in SUBSET_ALLOWED_KEYS
    ]
    props = schema.get("properties")
    if isinstance(props, dict):
        for pname, sub in props.items():
            out += subset_key_violations(sub, f"{path}/properties/{pname}")
    items = schema.get("items")
    if isinstance(items, dict):
        out += subset_key_violations(items, f"{path}/items")
    extra = schema.get("additionalProperties")
    if isinstance(extra, dict):
        out += subset_key_violations(extra, f"{path}/additionalProperties")
    pnames = schema.get("propertyNames")
    if isinstance(pnames, dict):
        out += subset_key_violations(pnames, f"{path}/propertyNames")
    return out


# ---------------------------------------------------------------- 子集校验器
def subset_validate(
    instance: Any, schema: Any, path: str = "instance"
) -> List[str]:
    """JSON-schema 子集校验；返回违例消息列表（空 = 通过）。"""
    if schema is None:
        return []
    if not isinstance(schema, dict):
        return [f"{path}: schema 段非对象"]
    out: List[str] = []

    stype = schema.get("type")
    if stype == "object":
        if not isinstance(instance, dict):
            return [f"{path}: 应为 object，实为 {type(instance).__name__}"]
        props = schema.get("properties", {})
        for req in schema.get("required", []) or []:
            if req not in instance:
                out.append(f"{path}: 缺必填字段 {req}")
        # propertyNames：键名逐个过子 schema（01 §1.1 扩展键命名纪律）
        pnames = schema.get("propertyNames")
        if isinstance(pnames, dict):
            for key in instance:
                out += subset_validate(key, pnames, f"{path}/{key}（键名）")
        for key in props:
            if key in instance:
                out += subset_validate(instance[key], props[key], f"{path}/{key}")
        extra = schema.get("additionalProperties")
        for key in instance:
            if key in props:
                continue
            if extra is False:
                out.append(f"{path}: 未知字段 {key}（不在该 schema 词表内）")
            elif isinstance(extra, dict):
                out += subset_validate(instance[key], extra, f"{path}/{key}")
        return out

    if stype == "array":
        if not isinstance(instance, list):
            return [f"{path}: 应为 array，实为 {type(instance).__name__}"]
        if "minItems" in schema and len(instance) < schema["minItems"]:
            out.append(f"{path}: 数组长度 {len(instance)} < minItems {schema['minItems']}")
        if "maxItems" in schema and len(instance) > schema["maxItems"]:
            out.append(f"{path}: 数组长度 {len(instance)} > maxItems {schema['maxItems']}")
        items = schema.get("items")
        for i, item in enumerate(instance):
            out += subset_validate(item, items, f"{path}[{i}]")
        return out

    if stype == "string":
        if not isinstance(instance, str):
            return [f"{path}: 应为 string，实为 {type(instance).__name__}"]
        if "minLength" in schema and len(instance) < schema["minLength"]:
            out.append(f"{path}: 字符串过短 {len(instance)} < minLength {schema['minLength']}")
        if "enum" in schema and instance not in schema["enum"]:
            out.append(f"{path}: 值 {instance!r} 不在枚举 {schema['enum']}")
        if "pattern" in schema:
            if not re.search(schema["pattern"], instance):
                out.append(f"{path}: 值 {instance!r} 不匹配 pattern {schema['pattern']}")
        return out

    if stype == "integer":
        if isinstance(instance, bool) or not isinstance(instance, int):
            return [f"{path}: 应为 integer，实为 {type(instance).__name__}"]
        if "minimum" in schema and instance < schema["minimum"]:
            out.append(f"{path}: 值 {instance} < minimum {schema['minimum']}")
        return out

    if stype == "number":
        if isinstance(instance, bool) or not isinstance(instance, (int, float)):
            return [f"{path}: 应为 number，实为 {type(instance).__name__}"]
        if "minimum" in schema and instance < schema["minimum"]:
            out.append(f"{path}: 值 {instance} < minimum {schema['minimum']}")
        return out

    if stype == "boolean":
        if not isinstance(instance, bool):
            return [f"{path}: 应为 boolean，实为 {type(instance).__name__}"]
        return out

    if stype is None:
        return []
    return [f"{path}: 校验器不支持的 type {stype!r}"]


# ---------------------------------------------------------------- schema 元检
def check_schema_files(root: str) -> Tuple[List[str], List[Dict[str, Any]]]:
    """校验 protocol/schema/*.json 在场且元结构合法；返回 (issues, schemas)。"""
    issues: List[str] = []
    schemas: List[Dict[str, Any]] = []
    sdir = os.path.join(root, SCHEMA_DIR)
    if not os.path.isdir(sdir):
        return [f"{SCHEMA_DIR}/ 缺失（协议层 IDL 未落盘）"], []
    files = sorted(glob.glob(os.path.join(sdir, "*.json")))
    for f in files:
        name = os.path.basename(f)
        try:
            with open(f, encoding="utf-8") as fh:
                data = json.load(fh)
        except Exception as exc:
            issues.append(f"{name}: JSON 解析失败 {exc}")
            continue
        if not isinstance(data, dict):
            issues.append(f"{name}: schema 顶层非对象")
            continue
        for key in ("$id", "title", "type"):
            if key not in data:
                issues.append(f"{name}: schema 缺 {key}")
        if data.get("$schema") != DIALECT:
            issues.append("%s: $schema=%r 与校验器实现的方言不一致（预期 %s；"
                          "修复指引：改声明或先扩展校验器再改声明）"
                          % (name, data.get("$schema"), DIALECT))
        if data.get("type") != "object":
            issues.append(f"{name}: schema.type 应为 object")
        if not isinstance(data.get("properties"), dict):
            issues.append(f"{name}: schema.properties 缺失/非对象")
        if "required" in data and not isinstance(data.get("required"), list):
            issues.append(f"{name}: schema.required 非数组")
        issues += subset_key_violations(data, name)
        schemas.append(data)
    return issues, schemas


def load_schema(root: str, name: str) -> Optional[Dict[str, Any]]:
    """按 $id 取单份 schema 定义（供测试/生成物复用）。"""
    _, schemas = check_schema_files(root)
    for s in schemas:
        if s.get("$id") == name:
            return s
    return None


# ---------------------------------------------------------------- 数据抽取
def _face_paths(root: str, *patterns: str) -> List[str]:
    """按模式枚举，并还原成 `os.path.join(root, ...)` 形态（与旧 `os.walk`/`os.listdir` 同契约）。

    为什么换掉 `os.walk` / `os.listdir` / `glob`（2026-09-29 实测）：这三种写法各自真走一遍文件系统，
    而 `csc.iter_files` 走**共享枚举**——目录清单已在常驻层（`dirs` 桶）里，于是 `discover()`
    **54 ms → 0.8 ms（65×）**。面**逐件一致**（真仓库：module 248 / pipeline 114 / protocol 111 件，
    一条不差）由 `test_schema_lint.DirectEnumerationTest` 逐件比对守着。
    """
    out: List[str] = []
    for pat in patterns:
        for rel in _csc.iter_files(root, pat):
            out.append(os.path.join(root, *rel.split("/")))
    return out


def discover(root: str) -> Dict[str, List[str]]:
    """枚举三张面（模块文档 / 管线文档 / 协议声明）；路径形态与旧实现一致（root 前缀）。"""
    return {
        "module_docs": _face_paths(root, "04_模块库/**/*.md", "community/*/modules/*.md"),
        "pipeline_docs": _face_paths(root, "03_管线库/**/*.md", "community/*/pipelines/*.md"),
        "protocol_files": _face_paths(root, "community/*/protocol.yaml"),
    }


def _fence_yaml(text: str, marker: str) -> Optional[Dict[str, Any]]:
    """取围栏 ```yaml 里含 marker 的第一个块（未命中 → None）。

    效率（实测，`nf conformance`）：本函数与 `conformance_scan._fence_yaml` 过去各自解析
    同一批模块文档（248 份机器契约块），等于同文两遍 PyYAML——现在**同源同一份缓存**，
    语义仍是本模块的「未命中 → None」（见 `conformance_scan._fence_yaml_opt`）。
    """
    return _csc._fence_yaml_opt(text, marker)


def _read_json(path: str) -> Tuple[Optional[Dict[str, Any]], str]:
    try:
        return json.loads(_csc.read_text_cached(path)), ""
    except Exception as exc:
        return None, str(exc)


# ---------------------------------------------------------------- 扫描主入口
#: `scan()` 的全部输入：逐一对照 `discover()` 的两处枚举（04 模块库 + community 的 modules /
#: pipelines / protocol.yaml）、schema 定义面、以及各校验器读到的管线库与资产侧件。
LINT_INPUTS = ("03_管线库/**/*.md", "04_模块库/**/*.md",
               "community/*/protocol.yaml", "community/*/modules/*.md",
               "community/*/pipelines/*.md", "community/*/assets/*.md",
               "protocol/schema/*.json", "05_资产库/**/*",
               "desktop/src/core/registry.json")


def scan(root: str = ".") -> Tuple[List[str], Dict[str, int]]:
    """全量扫描协议件；返回 (issues, stats)。issues 空 = check28 通过。

    派生结果按**输入内容指纹**缓存（输入面见 `LINT_INPUTS`，已穷举）——与
    `conformance_scan.scan` 同一条纪律：键即内容 ⇒ 输入一变必换键，不存在陈旧；「读到的件必须
    落在输入面内」由 `test_conformance_scan.DerivedResultCacheTest` 的同一张表守着（将来给本函数
    加新读取，那条判据会先红、逼着把新输入补进来）。
    """
    return _csc.memo_pair("schema-lint", LINT_INPUTS, _scan_impl, root,
                          code_modules=("core.schema_lint",))


def _schema_fp(schema: Any) -> str:
    """schema 定义的**内容指纹**（进逐件缓存键）：schema 一变，所有逐件结果必须重算。"""
    if schema is None:
        return "-"
    return hashlib.sha256(json.dumps(schema, ensure_ascii=False, sort_keys=True,
                                     default=str).encode("utf-8")).hexdigest()


def _lint_doc_cached(text: str, marker: str, schema: Any, schema_fp: str, prefix: str,
                     obj_key: str = ""):
    """一份件的「围栏解析 + 子集校验」结果（**键即内容**）；返回 `None` 表示没有该围栏。

    结果按**与路径无关**的形状缓存（消息里的路径前缀用 `_PATH_PLACEHOLDER` 占位，取用时再替换），
    所以同一份正文出现在不同路径上也能复用。判据：`test_schema_lint.DocLintCacheTest` 用**未缓存的
    参考实现**在真仓库全部模块/管线/协议件上逐条比对，并断言「面内改动必换键、面外改动不换键」。
    """
    key = (marker, obj_key, hashlib.sha256(text.encode("utf-8")).hexdigest(), schema_fp)
    hit = _DOC_LINT_CACHE.get(key)
    if hit is None:
        parsed = _fence_yaml(text, marker)
        if parsed is None:
            hit = None
        else:
            want = obj_key or marker
            obj = parsed.get(want, parsed) if want in parsed else parsed
            errs = subset_validate(obj, schema, _PATH_PLACEHOLDER) if schema is not None else []
            hit = tuple(errs)
        if len(_DOC_LINT_CACHE) >= _DOC_LINT_CACHE_MAX:
            _DOC_LINT_CACHE.clear()
        _DOC_LINT_CACHE[key] = hit
    if hit is None:
        return None
    return [m.replace(_PATH_PLACEHOLDER, prefix) for m in hit]


def _lint_obj_cached(obj: Any, schema: Any, schema_fp: str, prefix: str) -> List[str]:
    """按**对象内容**缓存子集校验结果（`registry.modules` / `provenance.assets[i]` 这类逐条面）。

    与 `_lint_doc_cached` 同一套纪律：键 =（对象规范 JSON 的 sha256、schema 指纹），消息里的路径
    前缀用 `_PATH_PLACEHOLDER` 占位、取用时替换——于是**同一份条目内容出现在不同下标上也能复用**。
    判据：`test_schema_lint.DocLintCacheTest` 用未缓存参考实现在真仓库 registry / provenance 上逐条比对。
    """
    if schema is None:
        return []
    key = (hashlib.sha256(json.dumps(obj, ensure_ascii=False, sort_keys=True,
                                     default=str).encode("utf-8")).hexdigest(), schema_fp)
    hit = _DOC_LINT_CACHE.get(key)
    if hit is None:
        hit = tuple(subset_validate(obj, schema, _PATH_PLACEHOLDER))
        if len(_DOC_LINT_CACHE) >= _DOC_LINT_CACHE_MAX:
            _DOC_LINT_CACHE.clear()
        _DOC_LINT_CACHE[key] = hit
    return [m.replace(_PATH_PLACEHOLDER, prefix) for m in hit]


def _scan_impl(root: str = ".") -> Tuple[List[str], Dict[str, int]]:
    """真算（未命中缓存时走这里）。"""
    issues: List[str] = []
    if _csc.yaml is None:                     # PyYAML 惰性（见 `core.lazy_yaml`）：只在这里问一次
        issues.append("PyYAML 不在（schema_lint 依赖仓库既有 yaml 依赖）")
        stats = {"schema_files": 0, "module_docs": 0, "contract_covered": 0,
                 "pipelines": 0, "protocols": 0, "asset_entries": 0}
        return issues, stats

    schema_issues, schemas = check_schema_files(root)
    issues += schema_issues
    by_name = {os.path.basename(s["$id"]): s for s in schemas if "$id" in s}

    paths = discover(root)
    module_docs = paths["module_docs"]
    pipeline_docs = paths["pipeline_docs"]
    protocol_files = paths["protocol_files"]

    contract_schema = by_name.get("contract.schema.json")
    module_schema = by_name.get("module.schema.json")
    pipeline_schema = by_name.get("pipeline.schema.json")
    protocol_schema = by_name.get("protocol.schema.json")
    asset_schema = by_name.get("asset.schema.json")

    contract_covered = 0
    contract_fp = _schema_fp(contract_schema)
    for doc in module_docs:
        rel = os.path.relpath(doc, root).replace(os.sep, "/")
        try:
            text = _csc.read_text_cached(doc)     # 共享语料（memo 生效时同文只读一遍）
        except Exception as exc:
            issues.append(f"{rel}: 读取失败 {exc}")
            continue
        msgs = _lint_doc_cached(text, "machine_contract", contract_schema, contract_fp,
                                f"{rel} machine_contract")
        if msgs is None:
            continue  # 存量旧格式模块（check16 过渡策略：缺块不阻断）
        contract_covered += 1
        issues += msgs

    # registry 投影（module.schema.json）
    reg_path = os.path.join(root, "desktop", "src", "core", "registry.json")
    reg, err = _read_json(reg_path)
    if reg is None:
        issues.append(f"registry.json 读取/解析失败：{err}")
        reg_modules: List[Dict[str, Any]] = []
    else:
        reg_modules = reg.get("modules") or []
    if module_schema is not None:
        module_fp = _schema_fp(module_schema)
        for entry in reg_modules:
            issues += _lint_obj_cached(entry, module_schema, module_fp, "registry.modules")

    # 管线声明（pipeline.schema.json）
    pipeline_fp = _schema_fp(pipeline_schema)
    for doc in pipeline_docs:
        rel = os.path.relpath(doc, root).replace(os.sep, "/")
        try:
            text = _csc.read_text_cached(doc)     # 共享语料（memo 生效时同文只读一遍）
        except Exception as exc:
            issues.append(f"{rel}: 读取失败 {exc}")
            continue
        msgs = _lint_doc_cached(text, "Pipeline:", pipeline_schema, pipeline_fp,
                                f"{rel} Pipeline", obj_key="Pipeline")
        if msgs is None:
            issues.append(f"{rel}: Pipeline yaml 缺失/解析失败")
            continue
        issues += msgs

    # community 协议声明（protocol.schema.json）
    protocol_fp = _schema_fp(protocol_schema)
    for proto in protocol_files:
        rel = os.path.relpath(proto, root).replace(os.sep, "/")
        try:
            # 共享语料 + 内容键解析：同一份 protocol.yaml 在一轮里只读一次、只解析一次
            data = _csc.load_yaml_cached(_csc.read_text_cached(proto))
        except Exception as exc:
            issues.append(f"{rel}: protocol.yaml 解析失败 {exc}")
            continue
        issues += _lint_obj_cached(data, protocol_schema, protocol_fp, rel)

    # 资产台账（asset.schema.json）
    prov_path = os.path.join(root, "05_资产库", "provenance.json")
    prov, err = _read_json(prov_path)
    prov_entries: List[Dict[str, Any]] = []
    if prov is None:
        issues.append(f"provenance.json 读取/解析失败：{err}")
    else:
        prov_entries = prov.get("assets") or []
    if asset_schema is not None:
        asset_fp = _schema_fp(asset_schema)
        for i, entry in enumerate(prov_entries):
            issues += _lint_obj_cached(entry, asset_schema, asset_fp, f"provenance.assets[{i}]")

    stats = {
        "schema_files": len(schemas),
        "module_docs": len(module_docs),
        "contract_covered": contract_covered,
        "pipelines": len(pipeline_docs),
        "protocols": len(protocol_files),
        "asset_entries": len(prov_entries),
    }
    return issues, stats
