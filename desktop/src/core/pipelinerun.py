"""管线抽象执行（dry-run）→ 执行图（机制借鉴 Pipelex `dry_run_pipeline` → GraphSpec）。

NF 此前只能回答「管线**声明**自洽吗」（静态 check），回答不了「这条管线**跑得通**吗」。
本模块补这一层：**不调模型、不动状态、不写盘**，只用声明跑一遍。

判决分层（关键：把「真错」与「NF 执行模型决定的待裁决项」分开，避免噪声门禁）：

- **hard**（真缺陷）：模块在仓库找不到；依赖落在**严格更后的层**。
- **advisory**（不判死，据实标注）：同层内依赖序（NF 的 I5 明确「最终执行顺序以注册表
  合并为准，禁止硬编码」）；事件订阅方在本执行集内无发布方（可能由 references 跨包
  闭包或外部域包提供）。

执行集 = 官方核心基座（registry.json `modules[]`，随每次装配恒执行）∪ 管线各层模块。
纪律：纯标准库；只读；不执行任何生成。
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from core.models import fid_key
from core.pipeline_loader import load_pipeline_file

_MODULE_GLOBS = ("04_模块库/*/*.md", "community/*/modules/*.md")


def _module_files(root: str = ".") -> Dict[str, Dict[str, Any]]:
    """仓库模块索引：文件名即 id（全限定由类别限定补），机读契约在场则挂上。"""
    from core import conformance_scan as csc

    out: Dict[str, Dict[str, Any]] = {}
    r = Path(root)
    seen = set()
    for pat in _MODULE_GLOBS:
        for p in sorted(r.glob(pat)):
            rel = p.relative_to(r).as_posix()
            if rel in seen or p.name == "README.md":
                continue
            seen.add(rel)
            stem = p.stem.split("_", 1)[0]
            cat = p.parent.name.replace("类", "")
            rec: Dict[str, Any] = {"id": stem, "cat_id": "%s:%s" % (cat, stem),
                                   "path": rel, "has_contract": False,
                                   "inputs": [], "outputs": [],
                                   "publish": [], "subscribe": []}
            try:
                text = p.read_text(encoding="utf-8")
                parsed = csc._fence_yaml(text, "machine_contract")
                mc = parsed.get("machine_contract") if isinstance(parsed, dict) else None
                if isinstance(mc, dict):
                    rec["has_contract"] = True
                    rec["inputs"] = [str(x) for x in (mc.get("inputs") or [])]
                    rec["outputs"] = [str(x) for x in (mc.get("outputs") or [])]
                    ev = mc.get("events") or {}
                    rec["publish"] = [str(x) for x in (ev.get("publish") or [])]
                    rec["subscribe"] = [str(x) for x in (ev.get("subscribe") or [])]
                    if mc.get("id"):
                        rec["cat_id"] = str(mc["id"])
                    from core import io_types as _iot
                    rec["io_types"] = _iot.parse_io_types(text) or {}
            except OSError:
                pass
            for key in (stem, rec["cat_id"], fid_key(rec["cat_id"])):
                out.setdefault(key, rec)
    return out


def _core_ids(root: str = ".") -> List[str]:
    """官方核心基座 id（registry.json modules[]）。"""
    path = Path(root) / "desktop" / "src" / "core" / "registry.json"
    try:
        reg = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    return [str(m.get("id")) for m in (reg.get("modules") or []) if m.get("id")]


def _resolve(ref: str, index: Dict[str, Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    return index.get(ref) or index.get(fid_key(ref)) or index.get(ref.split(":")[-1])


def graph(pipeline_path: str, root: str = ".",
          overrides: Optional[Dict[str, List[str]]] = None) -> Dict[str, Any]:
    """跑一遍管线声明 → 执行图 JSON（hard/issues 与 advisory/notes 分列）。"""
    abs_path = (pipeline_path if os.path.isabs(pipeline_path)
                else os.path.join(root, pipeline_path))
    pl = load_pipeline_file(abs_path)
    if pl is None:
        raise ValueError("管线解析失败：%s（修复指引：检查 frontmatter 与代码围栏闭合）"
                         % pipeline_path)
    index = _module_files(root)
    core = _core_ids(root)
    issues: List[str] = []
    notes: List[str] = []
    steps: List[Dict[str, Any]] = []
    edges: List[Dict[str, str]] = []
    tokens: List[str] = []
    done = set(core) | {fid_key(x) for x in core} | {x.split(":")[-1] for x in core}
    published: Dict[str, str] = {}
    subscribed: Dict[str, List[str]] = {}
    layer_of: Dict[str, int] = {}
    executed: List[str] = []

    # 基座先跑：官方核心的产出/事件进入池
    for ref in core:
        rec = _resolve(ref, index)
        if rec:
            for tok in rec["outputs"]:
                if tok not in tokens:
                    tokens.append(tok)
            for ev in rec["publish"]:
                published.setdefault(ev, rec["cat_id"])
            for ev in rec["subscribe"]:
                subscribed.setdefault(ev, []).append(rec["cat_id"])

    for idx, layer in enumerate(pl.layers, 1):
        refs = list((overrides or {}).get(layer.id) or layer.default_modules or [])
        # 本层成员集合（先算出来：同层依赖是「顺序由注册表裁决」，不判死）
        same_layer = {str(r) for r in refs}
        step = {"index": idx, "layer": layer.id, "layer_name": layer.name,
                "optional": bool(layer.optional), "modules": [], "missing": []}
        for ref in refs:
            rec = _resolve(str(ref), index)
            if rec is None:
                step["missing"].append(str(ref))
                issues.append("模块未在仓库找到：%s（层 %s）"
                              "（修复指引：核对 04_模块库/community/*/modules 的文件名与类别限定）"
                              % (ref, layer.id))
                continue
            mid = rec["cat_id"]
            executed.append(mid)
            step["modules"].append({"id": mid, "path": rec["path"],
                                    "has_contract": rec["has_contract"]})
            layer_of[mid] = idx
            for dep in rec["inputs"]:
                rec_dep = _resolve(dep, index)
                dep_id = rec_dep["cat_id"] if rec_dep else dep
                bare = dep_id.split(":")[-1]
                dep_layer = layer_of.get(dep_id, layer_of.get(bare))
                if dep_id in done or dep in done or bare in done:
                    edges.append({"from": dep_id, "to": mid, "kind": "input"})
                elif (dep in same_layer or dep_id in same_layer or bare in same_layer):
                    notes.append({"category": "同层依赖序",
                                  "detail": "%s ← %s（以注册表合并顺序为准）" % (mid, dep_id)})
                    edges.append({"from": dep_id, "to": mid, "kind": "input"})
                elif dep_layer is not None and dep_layer > idx:
                    issues.append("依赖序违约：%s 依赖 %s，但 %s 未在其之前执行"
                                  "（修复指引：前移提供方层位，或把该模块移出本层 default）"
                                  % (mid, dep_id, dep_id))
                else:
                    # 既不在本执行集、也不在更后层：可能由 references 跨包闭包或外部域包提供
                    notes.append({"category": "跨包/外部依赖",
                                  "detail": "%s ← %s（可能由 references 闭包或外部域包提供）"
                                            % (mid, dep_id)})
            done.add(mid)
            done.add(fid_key(mid))
            done.add(mid.split(":")[-1])
            done.add(rec["id"])
            for tok in rec["outputs"]:
                if tok not in tokens:
                    tokens.append(tok)
            for ev in rec["publish"]:
                published.setdefault(ev, mid)
            for ev in rec["subscribe"]:
                subscribed.setdefault(ev, []).append(mid)
        steps.append(step)

    for ev, subs in sorted(subscribed.items()):
        if ev not in published:
            notes.append({"category": "跨包/外部事件",
                          "detail": "%s ← %s（可能由 references 跨包闭包或外部域包提供）"
                                    % ("、".join(sorted(set(subs))), ev)})

    # 类型面（io_types）：仅在本执行集内判**可证**事项（未收窄不判死）
    kind_of_token: Dict[str, str] = {}
    type_issues_before = len(issues)
    for mid in executed:
        rec = _resolve(mid, index)
        if not rec:
            continue
        for tok, kind in ((rec.get("io_types") or {}).get("outputs") or {}).items():
            if kind == "untyped":
                continue
            prev = kind_of_token.get(tok)
            if prev and prev != kind:
                issues.append("类型冲突：token %s 同时被声明为 %s 与 %s"
                              "（修复指引：对齐各模块 io_types.outputs）"
                              % (tok, prev, kind))
            kind_of_token.setdefault(tok, kind)
    for mid in executed:
        rec = _resolve(mid, index)
        if not rec:
            continue
        for dep, want in ((rec.get("io_types") or {}).get("inputs") or {}).items():
            if want in ("untyped", "state"):
                continue
            dep_rec = _resolve(dep, index)
            if not dep_rec:
                continue
            got = sorted({v for v in ((dep_rec.get("io_types") or {})
                                      .get("outputs") or {}).values() if v != "untyped"})
            if got and want not in got:
                issues.append("类型不匹配：%s 期望 %s 提供 %s，而 %s 声明输出类型 %s"
                              "（修复指引：对齐 io_types 或调整依赖）"
                              % (mid, dep, want, dep, got))

    stats = {"layers": len(pl.layers), "modules": sum(len(s["modules"]) for s in steps),
             "missing": sum(len(s["missing"]) for s in steps), "core_base": len(core),
             "tokens": len(tokens), "events_published": len(published),
             "typed_tokens": len(kind_of_token),
             "issues": len(issues), "type_issues": len(issues) - type_issues_before,
             "notes": len(notes)}
    return {"schema": "nf-graphspec/1",
            "pipeline": {"id": pl.id, "name": pl.name,
                         "structure_type": pl.structure_type,
                         "path": str(pipeline_path).replace("\\", "/")},
            "steps": steps, "edges": edges, "tokens": tokens,
            "events": {"published": sorted(published)},
            "issues": issues, "notes": notes, "stats": stats}


def discover(root: str = ".") -> List[str]:
    """仓库内全部管线文件（03_管线库 + community/*/pipelines）。"""
    hits: List[str] = []
    for pat in ("03_管线库/*.md", "community/*/pipelines/*.md"):
        hits += [Path(p).as_posix() for p in sorted(Path(root).glob(pat))]
    return hits


def sweep(root: str = ".") -> Tuple[List[str], Dict[str, Any]]:
    """全仓管线扫一遍 → (hard issues, stats)（供门禁聚合）。"""
    issues: List[str] = []
    total = {"pipelines": 0, "notes": 0, "modules": 0, "core_base": 0}
    buckets: Dict[str, int] = {}
    items: List[Dict[str, str]] = []
    for p in discover(root):
        g = graph(p, root)
        total["pipelines"] += 1
        total["notes"] += g["stats"]["notes"]
        total["modules"] += g["stats"]["modules"]
        total["core_base"] = max(total["core_base"], g["stats"]["core_base"])
        issues += ["%s：%s" % (g["pipeline"]["id"], i) for i in g["issues"]]
        for n in g["notes"]:
            cat = n.get("category", "未分类") if isinstance(n, dict) else "未分类"
            buckets[cat] = buckets.get(cat, 0) + 1
            items.append({"pipeline": g["pipeline"]["id"], "category": cat,
                          "detail": n.get("detail", "") if isinstance(n, dict) else str(n)})
    total["advisory_buckets"] = buckets
    total["advisory_items"] = items
    return issues, total


def advisory_report(root: str = ".", write: bool = False) -> Dict[str, Any]:
    """advisory 分类台账：把「不判死的提示」按类别计数落盘（可归档、可追踪收敛）。"""
    issues, total = sweep(root)
    doc = {"schema": "nf-pipeline-advisory/1",
           "note": ("管线抽象执行的 advisory（同层顺序 / 跨包依赖 / 跨包事件）——"
                    "不判死，但需分类可见；类别计数下降即缺口收敛。"),
           "pipelines": total["pipelines"], "counts": total["advisory_buckets"],
           "total": total["notes"], "items": total["advisory_items"]}
    if write:
        p = Path(root) / "protocol" / "pipeline_advisory.json"
        p.write_text(json.dumps(doc, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                     encoding="utf-8", newline="\n")
    return doc


def verify_advisory(root: str = ".") -> Tuple[List[str], Dict[str, Any]]:
    """台账与实时重算一致（类别计数不得悄悄变）。"""
    live = advisory_report(root)
    issues: List[str] = []
    p = Path(root) / "protocol" / "pipeline_advisory.json"
    if not p.is_file():
        issues.append("缺 advisory 台账 protocol/pipeline_advisory.json"
                      "（修复指引：nf pipeline dryrun --all --write-advisory）")
        return issues, {"total": live["total"]}
    try:
        committed = json.loads(p.read_text(encoding="utf-8"))
        if committed.get("counts") != live["counts"]:
            issues.append("advisory 台账过期：记录 %s ≠ 实测 %s"
                          "（修复指引：重建台账）"
                          % (committed.get("counts"), live["counts"]))
    except ValueError:
        issues.append("advisory 台账 JSON 不可解析")
    return issues, {"total": live["total"], "counts": live["counts"]}
