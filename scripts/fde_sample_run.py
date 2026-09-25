#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""FDE 打样 · 可跑样例（check38 子扫描 4）。

定位：证明「NF 是 FDE 的 AI infra 中游标准」不是宣言——样例把一次 FDE 交付跑成证据：
    客户 brief → 域包（AI系统域包）装配面 → 四道门 → 交付物 + 证据包。

样例链（全部本地、确定性、无网络）：
  G1 产出面自洽：包内 outputs/INDEX.json 声明的每个产出面在场且可解析
  G2 契约合规：T2 面（schema）与 T3 面（data）逐对跑 JSON Schema 子集校验
  G3 概念图健康：assets/CONCEPT_GRAPH.md 机读块通过 concept_graph 健康判据
  G4 装配链在场：protocol.yaml + 自带管线 + 模块文档可指认
  G5 中游层成立：`nf stats --check` 与 `geo_export --check` 同时通过（出口自动化就位）

产物（docs/fde-sample/evidence/）：
  deliverable.md  交付物（技术文档形态：系统卡摘要 + 概念闭包 + 产出面 + 装配步骤 + 验收判据）
  gates.txt       四道门的原始输出
  result.jsonl    逐门结论（JSONL）
  manifest.json   产物 sha256 + 时间戳 + 输入指纹

用法：python scripts/fde_sample_run.py --run | --check
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from typing import Any, Dict, List, Tuple

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PACK = "community/AI系统域包"
EV = "docs/fde-sample/evidence"


def _sha(path: str) -> str:
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def _read_json(path: str) -> Any:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _gates(root: str) -> Tuple[List[Dict[str, Any]], List[str], Dict[str, Any]]:
    sys.path.insert(0, os.path.join(root, "desktop", "src"))
    from core import concept_graph as cg
    from core import output_forms as of

    rows: List[Dict[str, Any]] = []
    issues: List[str] = []
    facts: Dict[str, Any] = {}

    # G1 产出面自洽
    index_path = os.path.join(root, PACK, "outputs/INDEX.json")
    idx = _read_json(index_path)
    declared = idx.get("outputs") or []
    missing, unparsable = [], []
    for e in declared:
        p = os.path.join(root, PACK, str(e.get("path") or ""))
        if not os.path.isfile(p):
            missing.append(e.get("path"))
        elif str(e.get("path")).endswith((".json",)):
            try:
                _read_json(p)
            except Exception as ex:  # noqa: BLE001
                unparsable.append("%s (%s)" % (e.get("path"), ex))
    g1 = not missing and not unparsable
    rows.append({"gate": "G1_outputs_declared", "verdict": "PASS" if g1 else "FAIL",
                 "detail": "声明面 %d · 缺失 %d · 不可解析 %d" % (len(declared), len(missing), len(unparsable))})
    if not g1:
        issues.append("G1：产出面缺失=%s 不可解析=%s" % (missing, unparsable))
    facts["declared_outputs"] = len(declared)

    # G2 契约合规（T2 schema ↔ T3 data 逐对）
    pairs, schema_fail = 0, []
    for e in declared:
        schema_rel = e.get("schema")
        if not schema_rel:
            continue
        sp = os.path.join(root, PACK, str(schema_rel))
        dp = os.path.join(root, PACK, str(e.get("path") or ""))
        if not (os.path.isfile(sp) and os.path.isfile(dp)):
            schema_fail.append("%s：schema 或 data 缺失" % e.get("path"))
            continue
        pairs += 1
        errs = of.json_schema_check(_read_json(dp), _read_json(sp))
        if errs:
            schema_fail.append("%s：%s" % (e.get("path"), errs[:2]))
    g2 = not schema_fail and pairs > 0
    rows.append({"gate": "G2_contracts", "verdict": "PASS" if g2 else "FAIL",
                 "detail": "schema↔data 对 %d · 不合规 %d" % (pairs, len(schema_fail))})
    if not g2:
        issues.append("G2：%s" % schema_fail[:3])
    facts["schema_pairs"] = pairs

    # G3 概念图健康
    graph_path = os.path.join(root, PACK, "assets/CONCEPT_GRAPH.md")
    graph = cg.load_graph(graph_path)
    problems = cg.problems(graph)
    nodes = len(cg.node_meta(graph))
    order = cg.toposort(graph)
    strength = cg.provenance_strength(graph)
    g3 = not problems
    rows.append({"gate": "G3_concept_graph", "verdict": "PASS" if g3 else "FAIL",
                 "detail": "节点 %d · 拓扑序 %d · 问题 %d · 证据强度 %s"
                           % (nodes, len(order), len(problems), strength)})
    if not g3:
        issues.append("G3：%s" % problems[:3])
    facts.update({"concept_nodes": nodes, "topo_len": len(order), "provenance_strength": strength})

    # G4 装配链在场
    need = [os.path.join(root, PACK, "protocol.yaml"),
            os.path.join(root, PACK, "pipelines/P07_AI系统域装配流管线.md"),
            os.path.join(root, PACK, "modules/M25_前置闭包求值.md"),
            os.path.join(root, PACK, "modules/M26_装载序就绪门.md")]
    lack = [os.path.relpath(p, root) for p in need if not os.path.isfile(p)]
    g4 = not lack
    rows.append({"gate": "G4_assembly_chain", "verdict": "PASS" if g4 else "FAIL",
                 "detail": "装配链 4 件，缺 %d" % len(lack)})
    if not g4:
        issues.append("G4：缺 %s" % lack)

    # G5 中游层成立（出口自动化就位）
    from core import repo_stats as rs
    import importlib.util

    s_issues, s_stats = rs.check(root)
    spec = importlib.util.spec_from_file_location("geo_export", os.path.join(root, "scripts/geo_export.py"))
    geo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(geo)  # type: ignore[union-attr]
    g_issues, g_stats = geo.check(root)
    g5 = not s_issues and not g_issues
    rows.append({"gate": "G5_midstream_exports", "verdict": "PASS" if g5 else "FAIL",
                 "detail": "stats.check 问题 %d · geo.check 问题 %d" % (len(s_issues), len(g_issues))})
    if not g5:
        issues.append("G5：%s %s" % (s_issues[:2], g_issues[:2]))
    facts["standards"] = g_stats.get("standards", 0)
    return rows, issues, facts


def _deliverable(root: str, facts: Dict[str, Any]) -> str:
    card = _read_json(os.path.join(root, PACK, "outputs/SYSTEM_CARD.json"))
    closure = _read_json(os.path.join(root, PACK, "outputs/CONCEPT_CLOSURE.json"))
    idx = _read_json(os.path.join(root, PACK, "outputs/INDEX.json"))
    sysmod = card.get("system") or {}
    use = card.get("intended_use") or {}
    lines = [
        "# FDE 交付样例 · AI 系统域包 → 技术文档交付物",
        "",
        "> 本文件由 `python scripts/fde_sample_run.py --run` 生成（生成物，禁止手改）。",
        "> 交付形态：技术文档（techdoc）。中游位置：NF 契约层夹在「模型/传输协议」与「客户交付物」之间。",
        "",
        "## 1. 交付对象（系统卡摘要）",
        "",
        "- 系统：%s（%s · v%s · %s）" % (sysmod.get("name"), sysmod.get("id"),
                                        sysmod.get("version"), sysmod.get("kind_of_system")),
        "- 用途：%s" % str(use.get("purpose") or "")[:300],
        "- 模型无关：%s · 上游模型：%s" % (sysmod.get("model_agnostic"),
                                          ", ".join(sysmod.get("upstream_models") or []) or "—"),
        "- 限制：%s" % ("；".join(str(x)[:80] for x in (card.get("limitations") or []))[:300]),
        "- 风险框架：%s" % ((card.get("risk_management") or {}).get("framework") or "—"),
        "",
        "## 2. 概念闭包（装配前提）",
        "",
        "- 目标：`%s` · 闭包大小 %s · 装载序长度 %s"
        % (closure.get("target"), len(closure.get("closure") or []), len(closure.get("load_order") or [])),
        "- 概念节点 %s · 拓扑序 %s · 证据强度 `%s`"
        % (facts.get("concept_nodes"), facts.get("topo_len"), facts.get("provenance_strength")),
        "",
        "## 3. 交付面清单（包自持声明）",
        "",
        "| 面 | 形态 | 档位 | 角色 |",
        "|---|---|---|---|",
    ]
    for e in idx.get("outputs") or []:
        lines.append("| `%s` | %s | %s | %s |" % (e.get("path"), e.get("form"), e.get("tier"), e.get("role")))
    lines += [
        "",
        "## 4. 装配步骤（FDE 侧照做）",
        "",
        "1. 装载域包声明：`%s/protocol.yaml`" % PACK,
        "2. 求前置闭包：模块 `M25_前置闭包求值`（本样例结果见 §2）",
        "3. 过装载序就绪门：模块 `M26_装载序就绪门`",
        "4. 走本包管线：`%s/pipelines/P07_AI系统域装配流管线.md`" % PACK,
        "5. 交付出面：按 §3 清单产出（T2 schema / T3 data）",
        "",
        "## 5. 验收判据（本样例实跑的四道门 + 中游层核验）",
        "",
        "| 门 | 判据 | 证据 |",
        "|---|---|---|",
        "| G1 | 声明产出面全部在场且可解析 | `evidence/gates.txt` |",
        "| G2 | T2 schema ↔ T3 data 逐对合规 | `evidence/gates.txt` |",
        "| G3 | 概念图健康（无环/无悬空/别名唯一/分支完备） | `evidence/gates.txt` |",
        "| G4 | 装配链四件在场可指认 | `evidence/gates.txt` |",
        "| G5 | 中游出口成立（`nf stats --check` + `geo_export --check`） | `evidence/result.jsonl` |",
        "",
        "> 复算：`python scripts/fde_sample_run.py --check`（逐字节比对本目录证据与当前仓库状态）。",
        "",
    ]
    return "\n".join(lines)


def _build(root: str) -> Dict[str, str]:
    rows, issues, facts = _gates(root)
    outs: Dict[str, str] = {}
    outs["%s/deliverable.md" % EV] = _deliverable(root, facts)
    outs["%s/gates.txt" % EV] = "\n".join(
        ["$ python scripts/fde_sample_run.py --run", "exit=%d" % (1 if issues else 0)]
        + ["  [%s] %s · %s" % (r["verdict"], r["gate"], r["detail"]) for r in rows]) + "\n"
    outs["%s/result.jsonl" % EV] = "\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n"
    inputs = {}
    for rel in [os.path.join(PACK, "outputs/INDEX.json"), os.path.join(PACK, "outputs/SYSTEM_CARD.json"),
                os.path.join(PACK, "outputs/CONCEPT_CLOSURE.json"),
                os.path.join(PACK, "assets/CONCEPT_GRAPH.md"), os.path.join(PACK, "protocol.yaml")]:
        # 键一律用 POSIX 分隔符：仓库文本卫生判据禁止标识面出现反斜杠（Windows 下 os.path.join 会引入）
        inputs[rel.replace(os.sep, "/")] = _sha(os.path.join(root, rel))
    manifest = {"schema": "nf-fde-sample/1", "pack": PACK, "facts": facts,
                "inputs": inputs, "issues": issues,
                "artifacts": {k: hashlib.sha256(v.encode("utf-8")).hexdigest()
                              for k, v in outs.items() if not k.endswith("manifest.json")},
                "generated_at": ""}
    outs["%s/manifest.json" % EV] = json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    return outs


def run(root: str = ROOT) -> Tuple[List[str], int]:
    import datetime
    outs = _build(root)
    manifest_path = os.path.join(root, EV, "manifest.json")
    stamp = datetime.datetime.now().astimezone().strftime("%Y-%m-%d %H:%M %z")
    outs["%s/manifest.json" % EV] = outs["%s/manifest.json" % EV].replace('"generated_at": ""',
                                                                         '"generated_at": "%s"' % stamp)
    for rel, text in outs.items():
        path = os.path.join(root, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="") as fh:
            fh.write(text)
    doc = json.loads(outs["%s/manifest.json" % EV])
    return doc.get("issues") or [], len(outs)


def check(root: str = ROOT) -> Tuple[List[str], Dict[str, Any]]:
    outs = _build(root)
    issues: List[str] = []
    for rel, text in outs.items():
        path = os.path.join(root, rel)
        if not os.path.isfile(path):
            issues.append("缺样例证据 %s（跑 `fde_sample_run.py --run`）" % rel)
            continue
        if rel.endswith("manifest.json"):
            try:
                on_disk = json.loads(open(path, encoding="utf-8").read())
                fresh = json.loads(text)
                on_disk.pop("generated_at", None)
                fresh.pop("generated_at", None)
                if on_disk != fresh:
                    issues.append("%s 与当前仓库状态不一致（跑 `--run` 重跑）" % rel)
            except Exception as e:  # noqa: BLE001
                issues.append("%s 不可解析：%s" % (rel, e))
        elif open(path, encoding="utf-8").read() != text:
            issues.append("%s 与当前仓库状态不一致（跑 `--run` 重跑）" % rel)
    stats = {"gates": 5, "evidence_files": len(outs)}
    return issues, stats


def scan(root: str = ROOT) -> Tuple[List[str], Dict[str, Any]]:
    """check38 子扫描入口：FDE 样例可跑且证据与现状一致。"""
    return check(root)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="fde_sample_run", description="FDE 中游标准打样（可跑样例）")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--run", action="store_true")
    g.add_argument("--check", action="store_true")
    ap.add_argument("--root", default=ROOT)
    args = ap.parse_args(argv)
    if args.run:
        issues, n = run(args.root)
        print("== FDE 样例已跑 ==  证据 %d 件 → %s/" % (n, EV))
    else:
        issues, stats = check(args.root)
        print("== FDE 样例自检 ==  门 %(gates)d · 证据件 %(evidence_files)d" % stats)
    for i in issues:
        print("  [FAIL] %s" % i, file=sys.stderr)
    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
