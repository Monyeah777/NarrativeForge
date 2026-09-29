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
import contextlib
import copy
import hashlib
import io
import json
import os
import re
# 只解析本仓自持产出面；DTD/ENTITY 已在 _xml_guard 前置拒绝
import xml.etree.ElementTree as ET  # noqa: S405  # nosec B405 -- self-authored artifacts only
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

from core import conformance_scan as _csc   # 共享语料（读缓存 / 列目录缓存 / 内容指纹）

REGISTRY_REL = "protocol/output_forms.json"
BASELINE_REL = "protocol/output_forms_baseline.json"
INDEX_REL = "outputs/INDEX.json"
#: 逐包内容键里要一并计入的共享件（registry 的所有包都读它）。
REGISTRY_INPUT = "desktop/src/core/registry.json"

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
    "combo-cert": "T4",
}


def _rel(root: str, rel: str) -> Path:
    return Path(root) / rel.replace("/", os.sep)


#: 一次**只读**校验内共享「同文件读一次」。**真源是 conformance_scan 的共享语料缓存**——
#: 这样 `index_verify` 的读盘能与外层聚合（evaluate / qds.scan / conformance_report.run）
#: 的其它扫描器**共用同一份**（同一份包资产过去被四个模块各读一遍）。
#: 作用域仍严格等于一次 `index_verify` 调用（出口即清），所以不会读到陈旧内容；
#: 写路径（`render_outputs(write=True)`）从不进入该作用域。
def _memo_reads():
    from core import conformance_scan as _csc
    return _csc.read_memo()


#: `index_verify` 的**输入面**（穷举；内容键结果缓存的键就取自它）。
#: 有「读到的文件必须全部落在输入面内」的判据守着（test_conformance_scan.DerivedResultCacheTest），
#: 所以将来给本函数加新读取，判据会先红、逼着把新输入补进来——不会悄悄读到陈旧结果。
INDEX_INPUTS = ("community/*/outputs/**/*",
                "community/*/assets/*",
                "community/*/protocol.yaml",
                "community/*/modules/*.md",
                "04_模块库/*/*.md",
                "desktop/src/core/registry.json",
                # 2026-09-29 补齐（**陈旧洞**）：本模块真读这两件（形态清单 registry + 机验率基线），
                # 原先一条都没申报 ⇒ 重签基线/改形态清单时 `output-forms-scan` 会**命中旧结果**。
                # 抓它的是「**逻辑读**」审计（`read_text_cached` 级追踪）：只盯 `io.open` 的旧判据看不见
                # 常驻层命中的读，这两条洞因此躲过了很久——见 `test_conformance_scan.LogicalReadFaceAuditTest`。
                "protocol/output_forms.json",
                "protocol/output_forms_baseline.json")
#: 结果缓存（键 = 输入内容指纹；输入一变指纹就变，故不需要随请求清空）。
_INDEX_CACHE: Dict[str, Any] = {}


def _read_text_cached(path: Path) -> str:
    from core import conformance_scan as _csc
    return _csc.read_text_cached(path)


def _read_bytes_cached(path: Path) -> bytes:
    from core import conformance_scan as _csc
    return _csc.read_bytes_cached(path)


def _read_json(path: Path) -> Tuple[Any, str]:
    try:
        return json.loads(_read_text_cached(path)), ""
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
            elif str(data.get("schema") or "").startswith("nf-combo/1"):
                form = "combo-cert"
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

# JSON Schema 校验器已迁到**叶子件** `core/json_schema.py`（2026-09-29）：原先
# `output_forms ↔ pack_combo` 是模块级双向对（pack_combo 只用这一个纯函数），迁出后
# 两边都单向依赖叶子，零环由 `coupling_metrics` 机检。
from core.json_schema import json_schema_check as _js_check

json_schema_check = _js_check          # 兼容别名：本模块既有调用点（1115/1429 等）不变


# ---------------------------------------------------------------- 形态结构校验

def _check_json(root: str, rel: str) -> List[str]:
    path = _rel(root, rel)
    raw = _read_text_cached(path)
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
    for i, line in enumerate(_read_text_cached(_rel(root, rel)).splitlines(), 1):
        if not line.strip():
            continue
        try:
            json.loads(line)
        except ValueError as exc:
            issues.append("第 %d 行非 JSON：%s" % (i, exc))
    return issues


def _check_csv(root: str, rel: str) -> List[str]:
    text = _read_text_cached(_rel(root, rel))
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
    text = _read_text_cached(_rel(root, rel))
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
    text = _read_text_cached(_rel(root, rel))
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
        tomllib.loads(_read_text_cached(_rel(root, rel)))
    except Exception as exc:
        return ["TOML 不可解析：%s" % exc]
    return []


def _check_yaml(root: str, rel: str) -> List[str]:
    """YAML 只做**收窄子集**良构判定（本项目自用面：映射/列表/标量），不引第三方。"""
    text = _read_text_cached(_rel(root, rel))
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
    lines = [x.rstrip() for x in _read_text_cached(_rel(root, rel)).splitlines()]
    body = [x for x in lines if x.strip() and not x.strip().startswith("%%")]
    if not body:
        return ["空图"]
    issues = []
    head = body[0].strip().lower()
    if not any(head.startswith(k) for k in _MERMAID_KINDS):
        issues.append("首行非已知图种：%r" % body[0].strip()[:40])
    return issues


def _check_dot(root: str, rel: str) -> List[str]:
    text = _read_text_cached(_rel(root, rel))
    issues = []
    if not re.search(r"^\s*(strict\s+)?(di)?graph\b", text, re.M):
        issues.append("缺 digraph/graph 头")
    if text.count("{") != text.count("}"):
        issues.append("花括号不配对（{ %d / } %d）" % (text.count("{"), text.count("}")))
    return issues


def _check_graphml(root: str, rel: str) -> List[str]:
    path = _rel(root, rel)
    guard = _xml_guard(_read_text_cached(path))
    if guard:
        return ["GraphML %s" % guard]
    try:
        # 从**已缓存的字节**解析（`_read_bytes_cached` 与 `_read_text_cached` 共用同一次物理读）
        # ——`ET.parse(path)` 会自己再开一次文件，同一件在一次重算里被读两遍（实测 105 次）。
        r = ET.fromstring(_read_bytes_cached(path))  # nosec B314 -- DTD/ENTITY 已在 _xml_guard 拒掉
    except ET.ParseError as exc:
        return ["GraphML XML 解析失败：%s" % exc]
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
    # 惰性引用：_check_combo_cert 定义在本表之后（避免前向引用 NameError）
    "combo-cert": lambda r, x: _check_combo_cert(r, x),
}


# ---------------------------------------------------------------- 包级产出清单

def _pack_dirs(root: str) -> List[str]:
    """有 `community/<包>/outputs/INDEX.json` 的包目录名（有序）。

    效率（实测 2026-09-29）：原实现是 `Path.iterdir()` + 逐条 `d.is_dir()` +
    `INDEX.json.is_file()`——**每次 20 ms**（106 个包 ⇒ 200+ 次 stat），而 `index_verify` 与
    `meter` 每个内容状态各调一次 ⇒ 一次新状态白花 **40 ms**（占 `index_verify` 的一半）。
    改走共享枚举器（`community/*/outputs/INDEX.json`；目录清单已在常驻层）后 **~1 ms**。
    面**逐件一致**由 `test_output_forms.PackEnumerationTest` 用旧口径原样重算比对守着。
    """
    from core import conformance_scan as _csc
    return sorted({rel.split("/")[1]
                   for rel in _csc.iter_files(root, "community/*/" + INDEX_REL)})


#: **逐包**产出面校验的内容键缓存：键 = (该包目录内容指纹, registry 内容指纹)。
#: 为什么按包切：一次「改一页模块文档」只会让**那一个包**的键变，其余包直接命中——
#: 实测（稀疏常驻层的新进程里）`index_verify` 713 ms → 改一包之后只剩那一个包的钱。
#: 键即内容 ⇒ 无陈旧风险；`_DIGEST_MEMO` 让「外层输入面指纹已经算过的件」在这里近乎白拿。
_PACK_VERIFY_CACHE: Dict[Any, Any] = {}
_PACK_VERIFY_MAX = 4096


#: 逐包键里「属于该包」的那几条（**必须 ⊆ `INDEX_INPUTS`**，否则「读盘面 ⊆ 输入面」判据会红）。
_PACK_FACE_SLICE = ("outputs/**/*", "assets/*", "protocol.yaml", "modules/*.md")
#: 逐包键里「所有包共享」的那几条。**2026-09-29 用读追踪补齐**：`_verify_pack` 的 T4 复算会经
#: `pack_combo.combine/profiles` 读到**别的包的声明 / 资产台账 / 模块契约**（实测越面读 225 件）——
#: 这些不写进键，就会「子扫描器失效、外层键没变」⇒ 逐包缓存命中旧判决（**陈旧/假绿**）。
#: 只有**产物切片**（`_PACK_FACE_SLICE`）是「谁改谁重算」；声明面一变，所有包的判决都可能变。
#: **核心模块文档按「解析后的契约」进键**（见 `shared_face_key`）：正文改动不该重算 106 个包。
#: 判据：`test_output_forms.PackKeyReadCoverageTest`。
_PACK_FACE_SHARED = ("community/*/modules/*.md", "community/*/protocol.yaml",
                     "community/*/assets/provenance.json", REGISTRY_INPUT)
#: 逐包键里「按**解析后**契约进键」的那条（`04_模块库`）：正文改动不换键、`machine_contract` 变才换。
_PACK_FACE_PARSED = ("04_模块库/*/*.md",)


def shared_face_key(root: str = ".") -> str:
    """逐包键里**所有包共享**的那一半（跨包模块面 + registry）——**每个内容状态只算一遍**。

    为什么单拎出来（2026-09-29 仪器化实测）：`index_verify` 要为 111 个包各取一次内容键，
    而每个键都把 235 份 `community/*/modules/*.md` 重新枚举 + 摘要一遍 ⇒ **111 遍同一条共享面**，
    实测占 `index_verify` 185 ms 里的大头。切出来之后共享面一次算好、逐包只算自己那一份切片。
    正确性：键仍覆盖**同一批件**（共享面 ∪ 该包切片），任一侧内容一变键必变。
    **核心模块（`04_模块库`）按解析后的契约进键**（`pack_combo.core_contracts_fingerprint`）：
    `combine` 只消费核心模块的 `publish`（`core_pub`），所以正文改动不影响任何判决——按正文取键
    会让 106 个包在白改正文时全重算（实测 **+800 ms/条命令**）。判据：`PackKeyReadCoverageTest`
    （读覆盖）与 `PackVerifyCacheTest`（面内/面外换键）。
    """
    raw = _csc.face_fingerprint(root, _PACK_FACE_SHARED)
    from core import pack_combo as pc            # 惰性导入：避免模块级环
    core = pc.core_contracts_fingerprint(root)
    return hashlib.sha256(("%s\x00%s" % (raw, core)).encode("utf-8")).hexdigest()


_PACK_KEY_MEMO: Dict[str, Any] = {}
_PACK_KEY_MEMO_MAX = 4096


def _pack_key_reusable(root: str, pkg: str, shared: str) -> Any:
    """**确知变更面**驱动的键复用：本包切片确知没变 ⇒ 复用上一次的键（返回该键；否则 None）。

    依据（实测 2026-09-29）：`index_verify` 要为 106 个包各算一次切片指纹（合计 ~15 ms），而最常见的
    改动（改 `04_模块库` 正文、改文档、改协议声明外的件）**一件都不落在任何包的切片里**——算完 106 次
    才发现全都没变。读层早就在用「确知变更路径」精确失效（`drop_resident`），键层过去没用。

    fail-closed：`conformance_scan.changed_paths()` 说「不知道」（没装常驻层 / 监听说不清 / 刚装层）
    时**一律不复用**；只有「确知这一批变更里没有一件落在本包切片模式内」才复用。
    """
    prev = _PACK_KEY_MEMO.get(pkg)
    if not prev or prev[0] != shared:
        return None
    known, changed = _csc.changed_paths()
    if not known:
        return None
    if any(_matches_any(rel, _pack_slice_patterns(pkg)) for rel in changed):
        return None                              # 本包切片里有确知变更 → 老老实实重算
    return prev[1]


def _pack_slice_patterns(pkg: str):
    return tuple("community/%s/%s" % (pkg, rel) for rel in _PACK_FACE_SLICE)


def _matches_any(rel: str, patterns) -> bool:
    """仓库相对路径是否落在任一模式内（语义与 `iter_files` 同源：`**` 跨目录、`*` 不跨）。

    两侧都按 `lower()` 归一：① 监听给的是**小写**相对路径，而模式里有 `INDEX.json` 这种大写；
    ② 归一后若「本该不匹配却被判成匹配」，后果只是**多算一次**（安全方向）——反过来才会陈旧。
    """
    segs = [s.lower() for s in str(rel).replace("\\", "/").split("/")]
    for pat in patterns:
        if _csc._match_parts(segs, _csc._compiled_parts(str(pat).replace("\\", "/").lower())):
            return True
    return False


def pack_slice_index(root: str) -> Dict[str, List[str]]:
    """**一次枚举**四条包面，按包切成 `{包名: [该包的相对路径…]}`（每条面内有序）。

    依据（实测 2026-09-29）：`pack_content_key` 过去按包拼模式（106 包 × 4 条 = 424 个不同模式），
    一次 `nf score` 里 `iter_files` 因此被调 **619 次（35.5 ms）**，其中 ~424 次是「同一批面按包切」。
    一次枚举 + 内存切片后只剩 4 次枚举（实测 ~8 ms），**键值逐位不变**（同一条路径清单、同一顺序），
    由 `test_output_forms.PackSliceIndexTest` 在真仓库上逐包比对守着。
    """
    out: Dict[str, List[str]] = {}
    for rel_pat in _PACK_FACE_SLICE:
        for rel in _csc.iter_files(root, "community/*/" + rel_pat):
            out.setdefault(rel.split("/")[1], []).append(rel)
    return out


def pack_content_key(root: str, pkg: str, shared: str = "", rels=None) -> str:
    """一个包的**内容键** = `(共享面指纹, 该包切片指纹)` 两者的组合（见 `shared_face_key`）。

    为什么要按切片而不是整棵包树：判据（`DerivedResultCacheTest.test_reads_stay_inside_declared_input_face`）
    要求**读盘面 ⊆ 声明输入面**——用整棵包树会把 `pipelines/**` 也读进来，而它不在 `INDEX_INPUTS` 里，
    当场红（实测）。切片 = 声明面里属于该包的那几条 + `community/*/modules/*.md`（组合包会借阅别包模块，
    保守起见每包都计入）+ registry。

    **边界（如实记）**：因为把「全体包的 modules」都算进每个包的键，**改一页模块文档仍会换掉所有包的键**
    （这是保守代价）。改 `docs/**`、协议件、包外资产等**不在包切片里**的件时，只有外层整块键变、
    **逐包键全不变** ⇒ 逐包缓存全命中（实测 `index_verify` 533 → 11 ms）。要连模块文档也精确到包，
    得按 `protocol.yaml` 的 `references` 求「被借阅包」闭包——属下一步。
    """
    if not shared:                        # 单调用方（如单测）自己用时不强求外部先算
        shared = shared_face_key(root)
    reused = _pack_key_reusable(root, pkg, shared)
    if reused is not None:
        return reused
    if rels is None:                      # 单独调用（如单测）时仍按包枚举，结果与切片路线**逐位相同**
        rels = [r for rel_pat in _PACK_FACE_SLICE
                for r in _csc.iter_files(root, "community/%s/%s" % (pkg, rel_pat))]
    per_pack = _csc.fingerprint_of(root, rels)
    key = hashlib.sha256(("%s\x00%s" % (shared, per_pack)).encode("utf-8")).hexdigest()
    if len(_PACK_KEY_MEMO) >= _PACK_KEY_MEMO_MAX:
        _PACK_KEY_MEMO.clear()
    _PACK_KEY_MEMO[pkg] = (shared, key)
    return key


def _pack_verify_ok(value) -> bool:
    """逐包校验结果的形状校验：`{"issues": [...], "rows": [...]}`（否则当未命中）。"""
    return (isinstance(value, dict) and set(value) == {"issues", "rows"}
            and isinstance(value["issues"], list) and isinstance(value["rows"], list))


def _verify_pack_cached(root: str, pkg: str, shared: str = "", rels=None):
    """按包内容键取校验结果：进程内一层 + **落盘**一层（新进程也能免付未变包的账）。"""
    key = pack_content_key(root, pkg, shared, rels)
    hit = _PACK_VERIFY_CACHE.get(key)
    if hit is None:
        hit = _verify_pack_io(root, pkg, key)
        if len(_PACK_VERIFY_CACHE) >= _PACK_VERIFY_MAX:
            _PACK_VERIFY_CACHE.clear()
        _PACK_VERIFY_CACHE[key] = hit
    return hit


def _verify_pack_io(root: str, pkg: str, key: str):
    """`_verify_pack_cached` 的落盘层（可被 A/B 关掉：`NF_NO_PACK_DISK=1`）。"""
    if os.environ.get("NF_NO_PACK_DISK"):
        issues, rows = _verify_pack(root, pkg)
        return list(issues), list(rows)
    from core import disk_cache
    dkey = disk_cache.key("pack-verify", key, root=root,
                          code_modules=("core.output_forms",))
    packed = disk_cache.load("pack-verify", dkey, validate=_pack_verify_ok)
    if packed is None:
        issues, rows = _verify_pack(root, pkg)
        packed = {"issues": list(issues), "rows": list(rows)}
        disk_cache.store("pack-verify", dkey, packed, keep=512)
    return list(packed["issues"]), list(packed["rows"])


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


def _gen_combo_cert(root: str, entry: dict):
    """组合包 T4 面：按 INDEX 声明的 packs/extra_modules 重算组合证书。"""
    from core import pack_combo as pc

    spec = entry.get("recompute") or {}
    params = dict(spec.get("params") or {})
    packs = list(params.get("packs") or [])
    mods = list(params.get("extra_modules") or [])
    if not packs and not mods:
        return None, ["组合证书缺 packs/extra_modules（无输入即无复算）"]
    cert = pc.combine(root, packs=packs, extra_modules=mods)
    if params.get("label"):
        cert["label"] = params["label"]
    if params.get("note"):
        cert["note"] = params["note"]
    return cert, []


def _combo_doc(root: str, entry: dict) -> Tuple[Any, str]:
    """读证书输入（供图表/图示生成器复用）。"""
    spec = entry.get("render") or {}
    rel = (spec.get("inputs") or ["outputs/COMBO_CERT.json"])[0]
    data, err = _read_json(_rel(root, _pkg_rel(entry, rel)))
    return (data, "") if not err else (None, "输入 %s %s" % (rel, err))


def _gen_vega_layer_stack(root: str, entry: dict):
    data, err = _combo_doc(root, entry)
    if err:
        return None, [err]
    rows = [{"layer": k, "modules": len(v)}
            for k, v in _stack_pairs(data.get("layer_stacks"))]
    if not rows:
        return None, ["证书无 layer_stacks（无可画数据）"]
    return {
        "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
        "description": (entry.get("render") or {}).get("params", {}).get("title", "层位堆叠"),
        "data": {"values": rows},
        "mark": {"type": "bar"},
        "encoding": {"x": {"field": "layer", "type": "nominal", "title": "层位",
                           "sort": None},
                     "y": {"field": "modules", "type": "quantitative", "title": "模块数"}},
    }, []


def _gen_mermaid_layer_load(root: str, entry: dict):
    data, err = _combo_doc(root, entry)
    if err:
        return None, [err]
    lines = ["%% 组合包装载序（由 COMBO_CERT.json 确定性派生）", "flowchart LR"]
    for lay, mods in _stack_pairs(data.get("layer_stacks")):
        tag = lay.replace("-", "")
        lines.append('  %s["%s"]' % (tag, lay))
        for i, m in enumerate(mods):
            node = "%s_%d" % (tag, i)
            lines.append('  %s["%s"]' % (node, m))
            lines.append("  %s --> %s" % (tag, node))
    return "\n".join(lines) + "\n", []


def _gen_graphml_module_deps(root: str, entry: dict):
    data, err = _combo_doc(root, entry)
    if err:
        return None, [err]
    mods = list(data.get("modules") or [])
    explicit = set((data.get("dependency_closure") or {}).get("explicit") or [])
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<graphml xmlns="http://graphml.graphdrawing.org/xmlns">',
           '  <key id="layer" for="node" attr.name="layer" attr.type="string"/>',
           '  <graph id="combo" edgedefault="directed">']
    for m in mods:
        lay = ""
        for k, v in _stack_pairs(data.get("layer_stacks")):
            if m in v:
                lay = k
                break
        out.append('    <node id="%s"><data key="layer">%s</data></node>' % (m, lay))
    for m in mods:                      # 依赖边：模块 → 其显式依赖（在组合内的）
        rec = _combo_module_inputs(root, entry, m)
        for dep in rec:
            if dep in explicit and dep != m:
                out.append('    <edge source="%s" target="%s"/>' % (m, dep))
    out += ["  </graph>", "</graphml>"]
    return "\n".join(out) + "\n", []


def _combo_module_inputs(root: str, entry: dict, module_id: str) -> List[str]:
    from core import pack_combo as pc

    rec = pc.prof_get_module(root, module_id)
    return [str(x) for x in (rec.get("inputs") or [])]


def _stack_pairs(stacks: Any) -> List[Tuple[str, List[str]]]:
    """层栈两种历史形态兼容：列表（当前）[{layer, modules}] 与字典 {P40: [...]}。"""
    if isinstance(stacks, list):
        return [(str(r.get("layer") or ""), [str(x) for x in (r.get("modules") or [])])
                for r in stacks if isinstance(r, dict)]
    if isinstance(stacks, dict):
        return [(str(k), [str(x) for x in v]) for k, v in sorted(stacks.items())]
    return []


def _check_combo_cert(root: str, rel: str) -> List[str]:
    """组合证书：schema + 五不变量（复算一致由 recompute 面判）。"""
    from core import pack_combo as pc

    issues = _check_json(root, rel)
    data, err = _read_json(_rel(root, rel))
    if err or not isinstance(data, dict):
        return issues + ([err] if err else [])
    unsup: List[str] = []
    issues += ["证书不合 schema：%s" % e
               for e in pc.CERT_SCHEMA and json_schema_check(data, pc.CERT_SCHEMA,
                                                             unsupported=unsup)[:4]]
    if unsup:
        issues.append("证书校验器遇不支持关键字：%s" % sorted(set(unsup))[:2])
    fresh, perr = _gen_combo_cert(root, {"recompute": {"params": {
        "packs": data.get("packs"), "extra_modules": data.get("extra_modules")}}})
    if fresh is None:
        issues += ["复算失败：%s" % e for e in perr]
    else:
        if fresh.get("legal") is not True:
            issues.append("组合非法（五不变量未全成立）")
        if fresh.get("digest") != data.get("digest"):
            issues.append("证书摘要与实时复算不一致（组合输入已变）")
    return issues


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
    "combo-cert": _gen_combo_cert,
    "vega-layer-stack": _gen_vega_layer_stack,
    "mermaid-layer-load": _gen_mermaid_layer_load,
    "graphml-module-deps": _gen_graphml_module_deps,
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
    on_disk = _read_bytes_cached(_rel(root, _pkg_rel(entry, out_rel)))
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
    """包内产出清单机检（外层）：一次调用内共享「同文件读一次」（见 `_memo_reads`）。

    逐件校验会把同一份产物读 5–8 遍（detect / 查重 / schema / 双源 / 复算）——实测热跑里
    3027 次读盘、占该函数 1.54 s 的一大半。memo 的作用域严格等于**这一次调用**（出口即清），
    所以不会出现「读到陈旧内容」；下一次调用照常重新读盘。

    再叠一层**内容键结果缓存**：本函数是那批输入的纯函数，按输入内容指纹缓存后，同内容重复调用
    （`nf score` 与 `nf conformance` 都会走到它）省掉整轮校验（实测 ~0.72 s）。输入面见
    `INDEX_INPUTS`，并有「读到的文件必须全部落在输入面内」的判据守着
    （见 test_conformance_scan.DerivedResultCacheTest）。
    """
    fp = _csc.face_fingerprint(root, INDEX_INPUTS)
    hit = _INDEX_CACHE.get(fp)
    if hit is None:
        from core import disk_cache
        dkey = disk_cache.key("index-verify", fp, root=root,
                              code_modules=("core.output_forms",))
        cached = disk_cache.load("index-verify", dkey, validate=_csc.result_pair_ok)
        if cached is None:
            with _memo_reads():
                got = _index_verify_impl(root)
            disk_cache.store("index-verify", dkey,
                             {"issues": list(got[0]), "stats": got[1]})
        else:
            got = (list(cached["issues"]), dict(cached["stats"]))
        # 只**存**不拷：`got` 是本次刚算出来（或刚从盘里读出来）的新对象，不存在与别处的别名；
        # 真正需要的是返回时那一份拷贝（防调用方改到缓存）。过去这里还多深拷一次
        # （实测本仓 1500+ 行产出清单 = 每轮白拷 ~8 ms）。
        hit = _INDEX_CACHE[fp] = got
    return copy.deepcopy(hit[0]), copy.deepcopy(hit[1])


def _index_verify_impl(root: str = ".") -> Tuple[List[str], Dict[str, Any]]:
    """包级产出清单机检：声明存在 / 形态与档位属实 / schema 校验 / 双源一致 / T4 复算。"""
    issues: List[str] = []
    rows: List[Dict[str, Any]] = []
    shared = shared_face_key(root)                 # 共享面每个内容状态只算一遍（过去 111 遍）
    slices = pack_slice_index(root)                # 包切片一次枚举（过去 106 包各 4 条模式 = 424 次）
    for pkg in _pack_dirs(root):
        hit = _verify_pack_cached(root, pkg, shared, slices.get(pkg, []))
        issues += hit[0]
        rows += hit[1]
    stats = {"packages": len(_pack_dirs(root)), "outputs": len(rows),
             "by_role": _count(rows, "role"), "by_tier": _count(rows, "tier"),
             "by_form": _count(rows, "form")}
    return issues, stats


def _verify_pack(root: str, pkg: str) -> Tuple[List[str], List[Dict[str, Any]]]:
    """**单个包**的产出面校验（原体；被 `_index_verify_impl` 按包内容键缓存）。"""
    issues: List[str] = []
    rows: List[Dict[str, Any]] = []
    rel = "community/%s/%s" % (pkg, INDEX_REL)
    idx, err = _read_json(_rel(root, rel))
    if err:
        issues.append("%s: %s" % (rel, err))
        return issues, rows
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
    return issues, rows


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
    md_keys = set(key_re.findall(_read_text_cached(md_path)))
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
    # 资产档面一次枚举（共享枚举器：走查/子树清单复用），替代「每个包各一次 glob」——
    # 实测本仓 111 个包各 glob 一次 `assets/*.md`（106 次落盘遍历），而这一面本来就要被
    # asset_density / 指纹走一遍。
    prose_by_pkg: Dict[str, List[str]] = {}
    for rel in _csc.iter_files(root, "community/*/assets/*.md"):
        parts = rel.split("/")
        if len(parts) == 4 and parts[3] != "README.md":
            prose_by_pkg.setdefault(parts[1], []).append(parts[3])
    for pkg in _pack_dirs(root):
        idx, _err = _read_json(_rel(root, "community/%s/%s" % (pkg, INDEX_REL)))
        entries = (idx or {}).get("outputs") or []
        mv = [e for e in entries if e.get("tier") in ("T2", "T3", "T4")]
        fn_faces = [e for e in entries if e.get("tier") == "T4"]
        prose = prose_by_pkg.get(pkg, [])
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
    """check32 子扫描入口：形态清单 + 包级产出清单 + 机验率基线三合一。

    派生结果按**输入内容指纹**缓存（输入面复用同模块已穷举的 `INDEX_INPUTS`——它正是本入口
    三个子校验的读面）。**冷进程也走这层**（2026-09-29 实测：宽面指纹在同一只读作用域内近乎白拿，
    而重算这条派生账贵得多；见 `quality_depth_scan.scan` 的实测数字）。
    """
    return _csc.memo_pair("output-forms-scan", INDEX_INPUTS, _scan_impl, root,
                          code_modules=("core.output_forms",))


def _scan_impl(root: str = ".") -> Tuple[List[str], Dict[str, Any]]:
    """真算（未命中缓存时走这里）。"""
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
