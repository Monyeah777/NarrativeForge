"""NF → MVU 变量模板导出（契约 → 变量模板的确定性投影；NF 不做 MVU 运行时）。

目标格式版本锚点：MVU-Maker 公开 README（`raw.githubusercontent.com/Lunacaty/MVU-Maker`），
**现场核对日期 2026-09-16**；适配器版本 `mvu_adapter/0.1`。

核对结论（逐字命中，非转述）：
- 可核对 ✓：变量树根 `stat_data`；初始化条目名 `[InitVar]请勿打开`（禁用态、MVU 引擎读取、
  按 Schema 生成默认空值）；`[mvu_update]变量更新规则` / `[mvu_update]变量输出格式`（后者要求
  AI 以 **JSON Patch** 输出）；七类型 `string / number / boolean / enum / object / record / union`；
  酒馆助手脚本接口 `registerMvuSchema`；Zod 4 能力 `prefault / clamp / describe`。
- 不可核对 ✗（未写入产物语义，只在 README 与 warning 里标注）：树路径规则细节、条目位置参数
  （`atDepth` / `depth` / `order`）适用规则、`character_book.entries` 与 `tavern_helper.scripts`
  的数组硬要求、正则五件套组成、变量列表（蓝灯 @D0）条目形态、base64/chara 分发细节。

边界：**不产 JS、不产 Zod 脚本、不做运行时**；本模块只做「契约 → 变量模板 JSON + digest」。
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Dict, List

from .ir import IRDocument

ADAPTER_VERSION = "mvu_adapter/0.1"
DOC_CHECK_DATE = "2026-09-16"
DOC_SOURCE = "https://raw.githubusercontent.com/Lunacaty/MVU-Maker/HEAD/README.md"

#: 类型映射建议（NF io_types / world_model kind → MVU 七类型）。
#: 只有前四条是低风险直映；array / object / union 待核对后再定稿（故标 draft）。
TYPE_MAP = {"string": "string", "integer": "number", "number": "number",
            "boolean": "boolean", "enum": "enum", "array": "array",
            "object": "object", "untyped": "union"}
UNVERIFIED = ["stat_data 树路径规则", "条目位置参数 atDepth/depth/order",
              "entries / tavern_helper.scripts 数组硬要求", "正则五件套组成",
              "变量列表条目形态（蓝灯 @D0）", "base64/chara 分发细节"]


def _modules(ir: IRDocument) -> List[Any]:
    """遍历 IR 的层内模块 + extra_modules（对形状宽容，不猜字段）。"""
    out: List[Any] = []
    for layer in (getattr(ir, "layers", None) or []):
        out.extend(getattr(layer, "modules", None) or [])
    out.extend(getattr(ir, "extra_modules", None) or [])
    return out


def _canonical_digest(obj: Any) -> str:
    """契约摘要：canonical JSON（排序键 + 紧凑分隔符）+ SHA-256（纯标准库）。"""
    blob = json.dumps(obj, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def _ir_module_ids(ir: IRDocument) -> List[str]:
    """从 IR 里尽力收集模块 id（形状宽容）：层内模块 / 层 module_ids / extra_modules /
    `ir.modules`；全部取不到时退化为对 `to_markdown()` / `str(ir)` 扫 `M\\d+`。

    真跑实测：装配路径下 `layers[].modules` 可能为空，故必须有这条兜底——
    否则取件只看 IR 会永远空转（见 postmortems/PO-0001 的教训：根因要指向机制）。
    """
    ids: List[str] = []

    def _add(x: Any) -> None:
        s = x if isinstance(x, str) else str(
            getattr(x, "full_id", None) or getattr(x, "id", "") or "")
        s = s.strip()
        if s and s not in ids:
            ids.append(s)

    for layer in (getattr(ir, "layers", None) or []):
        for m in (getattr(layer, "modules", None) or []):
            _add(m)
        for mid in (getattr(layer, "module_ids", None) or []):
            _add(mid)
    for m in (getattr(ir, "extra_modules", None) or []):
        _add(m)
    for m in (getattr(ir, "modules", None) or []):
        _add(m)
    if not ids:
        text = ""
        for attr in ("to_markdown", "to_md"):
            fn = getattr(ir, attr, None)
            if callable(fn):
                try:
                    text = fn() or ""
                    break
                except Exception:
                    pass
        text = text or str(ir)
        ids = list(dict.fromkeys(re.findall(r"M\d{2,3}", text)))
    return ids


def _collect_world_models(ir: IRDocument) -> List[Dict[str, Any]]:
    """取每条模块的 `machine_contract.world_model` → [{module, contract, digest}]。

    取件三级 fallback（同一种提取法，只是换文本源）：
    ① `IRModule.content`（装配后归一正文）→ ② `IRModule.source_md`（原始 markdown）
    → ③ 模块源文件（按 id 在 `conformance_scan._module_docs` 里匹配）。
    真跑实测：装配路径下 `content` 已不含 fence，故必须有 ②③ 兜底。
    """
    from . import conformance_scan as csc

    rows: List[Dict[str, Any]] = []
    by_id: Dict[str, str] = {}

    def _index() -> Dict[str, str]:
        if by_id:
            return by_id
        root = Path(__file__).resolve().parents[3]
        for doc in csc._module_docs(str(root)):
            txt = Path(doc).read_text(encoding="utf-8")
            parsed = csc._fence_yaml(txt, "machine_contract") or {}
            mc = parsed.get("machine_contract") if isinstance(parsed, dict) else None
            if isinstance(mc, dict) and mc.get("id"):
                by_id[str(mc["id"])] = txt
        return by_id

    idx = _index()
    objs = {str(getattr(m, "full_id", None) or getattr(m, "id", "") or ""): m
            for m in _modules(ir)}
    for mid in _ir_module_ids(ir):
        bare = mid.split(":")[-1]
        obj = objs.get(mid) or objs.get(bare)
        texts = [getattr(obj, "content", "") or "" if obj is not None else "",
                 getattr(obj, "source_md", "") or "" if obj is not None else "",
                 idx.get(bare, ""), idx.get(mid, "")]
        wm = None
        for t in texts:
            if not t:
                continue
            parsed = csc._fence_yaml(t, "machine_contract") or {}
            mc = parsed.get("machine_contract") if isinstance(parsed, dict) else None
            cand = (mc or {}).get("world_model") if isinstance(mc, dict) else None
            if isinstance(cand, dict):
                wm = cand
                break
        if not isinstance(wm, dict):
            continue
        rows.append({"module": mid, "contract": wm, "digest": _canonical_digest(wm)})
    return rows


def _iter_variables(c: Dict[str, Any]) -> List[Dict[str, Any]]:
    """变量声明既是 dict 也是 list（真件在 `abstract_state.variables`，是 list）。

    真跑实测（M50）：`world_model = {abstract_state, transition, invariants, checks}`；
    变量在 `abstract_state.variables`（list of {name, kind, slot, note, source}）。
    故此处两种形状都收，且优先 `world_model.variables` 再退 `abstract_state.variables`。
    """
    decl = c.get("variables")
    if decl is None and isinstance(c.get("abstract_state"), dict):
        decl = c["abstract_state"].get("variables")
    out: List[Dict[str, Any]] = []
    if isinstance(decl, dict):
        for name, d in decl.items():
            row = dict(d) if isinstance(d, dict) else {}
            row.setdefault("name", name)
            out.append(row)
    elif isinstance(decl, list):
        for d in decl:
            if isinstance(d, dict) and d.get("name"):
                out.append(dict(d))
    return out


def _iter_checks(c: Dict[str, Any]) -> List[Any]:
    """checks 既是 dict（按变量名）也是 list（按 check 对象）——两种都收。"""
    decl = c.get("checks")
    out: List[Any] = []
    if isinstance(decl, dict):
        for k, v in decl.items():
            out.append((k, v))
    elif isinstance(decl, list):
        for d in decl:
            if isinstance(d, dict):
                key = str(d.get("id") or d.get("name") or d.get("target") or "check")
                out.append((key, d))
    return out


def build_mvu_payload(ir: IRDocument) -> Dict[str, Any]:
    """纯函数：契约 → NF 侧 MVU 中间模型（可单测，不写盘）。"""
    rows = _collect_world_models(ir)
    variables: List[Dict[str, Any]] = []
    initial: Dict[str, Any] = {}
    checks: Dict[str, Any] = {}
    phases: List[Any] = []
    invariants: List[Any] = []
    warnings: List[str] = []
    seen: Dict[str, str] = {}
    for r in rows:
        c = r["contract"]
        for decl in _iter_variables(c):
            name = str(decl.get("name") or "")
            if not name:
                continue
            if name in seen and seen[name] != r["module"]:
                warnings.append("变量名冲突：%s 同时来自 %s 与 %s——按先到者保留，"
                                "冲突已记录（不静默）" % (name, seen[name], r["module"]))
                continue
            seen[name] = r["module"]
            kind = str(decl.get("kind") or "untyped")
            variables.append({"name": name, "kind": kind,
                              "mvu_type": TYPE_MAP.get(kind, "union"),
                              "slot": decl.get("slot") or "",
                              "note": decl.get("note") or "",
                              "source": r["module"]})
        st = c.get("abstract_state") if isinstance(c.get("abstract_state"), dict) else {}
        if st.get("initial"):
            initial.update(st["initial"])
        for k, v in _iter_checks(c):
            vals = v.get("values") if isinstance(v, dict) else None
            if vals is None and isinstance(v, dict):
                vals = v.get("allowed") or v.get("enum")
            checks[k] = {"values": vals} if vals else {"rule": v}
        tr = c.get("transition") if isinstance(c.get("transition"), dict) else {}
        phases.extend(tr.get("phases") or [])
        invariants.extend(c.get("invariants") or [])
    return {
        "schema": "nf-mvu-payload/1",
        "generator": ADAPTER_VERSION,
        "target": {"format": "MVU 变量模板（stat_data 树）", "doc_check_date": DOC_CHECK_DATE,
                   "doc_source": DOC_SOURCE,
                   "verified": ["stat_data", "[InitVar]请勿打开",
                                "[mvu_update]变量更新规则", "[mvu_update]变量输出格式（JSON Patch）",
                                "七类型 string/number/boolean/enum/object/record/union",
                                "registerMvuSchema", "prefault/clamp/describe"],
                   "unverified": UNVERIFIED},
        "variables": variables,
        "initial": initial,
        "checks": checks,
        "phases": phases,
        "invariants": invariants,
        "provenance": {"modules": sorted({r["module"] for r in rows}),
                       "digests": {r["module"]: r["digest"] for r in rows}},
        "nf_draft": True,
        "warnings": warnings,
    }


def _worldbook_draft(payload: Dict[str, Any]) -> Dict[str, Any]:
    """世界书条目草案：只放已核对确切的条目名；位置参数一律标 draft（未核对）。"""
    return {"nf_draft": True,
            "nf_note": "条目位置参数（atDepth/depth/order）与数组硬要求未核对，故不写死；"
                       "请按目标前端的实际约定补齐后再导入。",
            "character_book": {"entries": [
                {"name": "[InitVar]请勿打开",
                 "nf_role": "变量初始化（禁用态，前端引擎读取；按 Schema 生成默认空值）",
                 "content": json.dumps(payload["initial"], ensure_ascii=False,
                                       sort_keys=True)},
                {"name": "[mvu_update]变量更新规则", "nf_role": "每变量更新触发条件",
                 "content": "(待填：NF 不产更新规则文本，只给变量与初值)"},
                {"name": "[mvu_update]变量输出格式", "nf_role": "要求以 JSON Patch 输出更新",
                 "content": "(待填：JSON Patch 输出约束)"}]}}


def export_mvu(ir: IRDocument, dest_dir: Path, res) -> None:
    """写出 MVU 变量模板产物；无 world_model 时不产空文件集，只记 warning。"""
    payload = build_mvu_payload(ir)
    if not payload["variables"]:
        res.warnings.append("IR 内无任何 world_model：未产出 MVU 变量模板（不产空文件集）")
        return
    dest = Path(dest_dir)
    dest.mkdir(parents=True, exist_ok=True)
    p1 = dest / "mvu_variables.json"
    p2 = dest / "mvu_worldbook.json"
    p3 = dest / "mvu_README.md"
    p1.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                  encoding="utf-8", newline="\n")
    p2.write_text(json.dumps(_worldbook_draft(payload), ensure_ascii=False, indent=2,
                             sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    p3.write_text(
        "# MVU 变量模板（由 NarrativeForge 导出）\n\n"
        "- 生成器：%s ｜ 目标格式锚点核对日期：%s\n- 契约来源：%s\n\n"
        "## 产物\n\n"
        "| 文件 | 内容 | 状态 |\n|---|---|---|\n"
        "| mvu_variables.json | 变量表 + 初值 + checks + 相位 + 不变式 + 溯源 digest | 可核 |\n"
        "| mvu_worldbook.json | 世界书条目草案（`[InitVar]` / `[mvu_update]` ×2） | **draft** |\n\n"
        "## 如实声明\n\n"
        "- **未在真实 SillyTavern 实测**，不声称兼容；条目位置参数与数组硬要求**未核对**，"
        "故 worldbook 保持 draft。\n"
        "- 正则五件套**未产出**（组成未核对）。\n"
        "- 未核对清单：%s\n"
        % (ADAPTER_VERSION, DOC_CHECK_DATE, DOC_SOURCE, "、".join(UNVERIFIED)),
        encoding="utf-8", newline="\n")
    res.files.extend([str(p1), str(p2), str(p3)])
    for w in payload.get("warnings") or []:
        res.warnings.append(w)
    res.warnings.append("MVU 侧装配件为 draft（条目位置参数与数组要求未核对）；未在真实 ST 实测")
