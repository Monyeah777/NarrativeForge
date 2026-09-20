#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AI 系统域 · 概念前置闭包求值（只读 · 确定性 · 零网络 · 不改仓库任何文件）。

定位：把「概念前置依赖」从**内容**变成**可复算产物**——读域包资产
`community/AI系统域包/assets/CONCEPT_GRAPH.md` 的机器可读块，输出三件产物：

1. 前置闭包 `closure(c)`
2. 缺失清单 `missing(c, L)`（L = 已装载概念集）
3. 合法装载序 `load_order`（toposort 的确定性线性化）

并附两件可证检查：图自身健康度（无环 / 无悬空 / 边有溯源）与「给定序列对图的违反边数」
（用于判定某份讲序 / 目录序是不是本图的前置序）。

纪律：本工具是**只读求值器**，不是 nf 子命令、不是门禁、不改 Schema；确定性 = 同输入同输出
（同层并列按 id 升序，集合输出一律排序）。YAML 解析复用仓库既有 PyYAML 依赖。

用法（仓库根目录）：
  python scripts/ai_domain_closure.py --target C22 --loaded C01,C07,C08,C10,C18
  python scripts/ai_domain_closure.py --target C22 --json
  python scripts/ai_domain_closure.py --order cmu-mlsys
  python scripts/ai_domain_closure.py --check          # 自检（含负例注入）
退出码：0 成功 / 1 自检或图健康度失败 / 2 用法错误。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Sequence, Set, Tuple

#: 默认资产路径（含机器可读块的概念图）
DEFAULT_ASSET = "community/AI系统域包/assets/CONCEPT_GRAPH.md"
BLOCK_MARKER = "concept_graph"
LAYERS = ("P00", "P10", "P20", "P30", "P40", "P50", "P60", "P70", "P80")

_FENCE = re.compile(r"(?ms)^```yaml\s*\n(.*?)^```")


class ClosureError(ValueError):
    """求值拒绝原因（缺资产 / 缺机读块 / 图非法）。"""


# ---------------------------------------------------------------- 读取机读块
def fenced_block(text: str, marker: str = BLOCK_MARKER) -> str:
    """取含 marker 的 ```yaml 围栏正文（无则空串）。"""
    for m in _FENCE.finditer(text):
        body = m.group(1)
        if re.search(r"(?m)^%s\s*:" % re.escape(marker), body):
            return body
    return ""


def load_graph(asset_path: str | Path = DEFAULT_ASSET) -> Dict[str, Any]:
    """读资产 → `concept_graph` 字典（缺件/缺块/解析失败一律抛 ClosureError）。"""
    path = Path(asset_path)
    if not path.is_file():
        raise ClosureError("概念图资产不存在：%s（修复指引：给出域包内 assets/CONCEPT_GRAPH.md 路径）"
                           % path)
    body = fenced_block(path.read_text(encoding="utf-8"))
    if not body:
        raise ClosureError("资产缺 `%s:` 机器可读块：%s（修复指引：补 ```yaml 围栏块，"
                           "块内首键为 %s）" % (BLOCK_MARKER, path, BLOCK_MARKER))
    try:
        import yaml
    except ImportError as exc:                    # pragma: no cover - 仓库既有依赖
        raise ClosureError("缺 PyYAML（修复指引：pip install pyyaml）") from exc
    data = yaml.safe_load(body)
    graph = (data or {}).get(BLOCK_MARKER)
    if not isinstance(graph, dict):
        raise ClosureError("机读块结构非法：%s（修复指引：顶层键须为 %s）" % (path, BLOCK_MARKER))
    return graph


# ---------------------------------------------------------------- 图语义
def prereqs_of(graph: Dict[str, Any]) -> Dict[str, List[str]]:
    """{概念 id: 直接前置 id 列表}（保持资产声明序，去重）。"""
    out: Dict[str, List[str]] = {}
    for node in graph.get("nodes") or []:
        if not isinstance(node, dict) or not node.get("id"):
            continue
        seen: List[str] = []
        for p in node.get("prereqs") or []:
            p = str(p)
            if p not in seen:
                seen.append(p)
        out[str(node["id"])] = seen
    return out


def node_meta(graph: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """{概念 id: 节点元信息}（含包外前置，标 external=True）。"""
    out: Dict[str, Dict[str, Any]] = {}
    for node in graph.get("nodes") or []:
        if isinstance(node, dict) and node.get("id"):
            rec = dict(node)
            rec["external"] = False
            out[str(node["id"])] = rec
    for node in graph.get("external_prereqs") or []:
        if isinstance(node, dict) and node.get("id"):
            rec = dict(node)
            rec["external"] = True
            out.setdefault(str(node["id"]), rec)
    return out


def in_package_ids(graph: Dict[str, Any]) -> List[str]:
    """包内概念 id（外部前置族不计入装载序）。"""
    return sorted(prereqs_of(graph))


def closure(graph: Dict[str, Any], target: str) -> List[str]:
    """传递闭包 closure(target) = {target} ∪ ⋃ closure(p)；返回排序列表。"""
    prereqs = prereqs_of(graph)
    meta = node_meta(graph)
    if target not in prereqs and target not in meta:
        raise ClosureError("目标概念不在图中：%s（修复指引：--target 用资产内 Cxx 编号）" % target)
    seen: Set[str] = set()
    stack = [target]
    while stack:
        cur = stack.pop()
        if cur in seen:
            continue
        seen.add(cur)
        stack.extend(prereqs.get(cur, []))
    return sorted(seen)


def missing(graph: Dict[str, Any], target: str, loaded: Sequence[str]) -> List[str]:
    """缺失清单 missing(target, L) = closure(target) − L。"""
    have = {str(x) for x in loaded}
    return [c for c in closure(graph, target) if c not in have]


def toposort(graph: Dict[str, Any]) -> List[str]:
    """确定性拓扑序（Kahn；并列按 id 升序）。图有环 → 抛 ClosureError。"""
    prereqs = prereqs_of(graph)
    ids = sorted(prereqs)
    indeg = {i: 0 for i in ids}
    children: Dict[str, List[str]] = {i: [] for i in ids}
    for i in ids:
        for p in prereqs[i]:
            if p in indeg:                      # 包外前置不参与排序
                indeg[i] += 1
                children[p].append(i)
    ready = sorted(i for i in ids if indeg[i] == 0)
    out: List[str] = []
    while ready:
        cur = ready.pop(0)
        out.append(cur)
        for nxt in sorted(children[cur]):
            indeg[nxt] -= 1
            if indeg[nxt] == 0:
                ready.append(nxt)
        ready.sort()
    if len(out) != len(ids):
        raise ClosureError("概念图存在环，无法给出装载序（修复指引：按资产 §5 冲突规则归并并列节点）")
    return out


def violations(graph: Dict[str, Any], seq: Sequence[str]) -> List[Tuple[str, str]]:
    """给定序列对图的违反边：[(前置, 后继)]——前置排在后继之后即违反。"""
    pos = {str(x): i for i, x in enumerate(seq)}
    prereqs = prereqs_of(graph)
    bad: List[Tuple[str, str]] = []
    for user, ps in sorted(prereqs.items()):
        if user not in pos:
            continue
        for p in ps:
            if p in pos and pos[p] > pos[user]:
                bad.append((p, user))
    return bad


def problems(graph: Dict[str, Any]) -> List[str]:
    """图健康度：无环 / 无悬空 / 边有溯源 / 层位合法 / id 唯一。返回问题清单。"""
    issues: List[str] = []
    prereqs = prereqs_of(graph)
    declared = set(prereqs) | {str(x.get("id")) for x in (graph.get("external_prereqs") or [])
                              if isinstance(x, dict)}
    seen_nodes: Set[str] = set()
    for node in graph.get("nodes") or []:
        if not isinstance(node, dict) or not node.get("id"):
            issues.append("节点缺 id（修复指引：每个节点须有 Cxx 编号）")
            continue
        nid = str(node["id"])
        if nid in seen_nodes:
            issues.append("节点 id 重复：%s（编号须唯一）" % nid)
        seen_nodes.add(nid)
        if not node.get("provenance"):
            issues.append("节点 %s 缺 provenance（边无溯源即不可复核）" % nid)
        layer = str(node.get("layer") or "")
        if layer and layer not in LAYERS:
            issues.append("节点 %s 层位越界：%s（取值 %s）" % (nid, layer, "/".join(LAYERS)))
    for nid, ps in sorted(prereqs.items()):
        for p in ps:
            if p not in declared:
                issues.append("悬空前置：%s ← %s（前置不在节点表/外部前置族中）" % (nid, p))
            if p == nid:
                issues.append("自环：%s ← %s" % (nid, p))
    try:
        toposort(graph)
    except ClosureError as exc:
        issues.append(str(exc))
    return issues


# ---------------------------------------------------------------- 输出
def report(graph: Dict[str, Any], target: str, loaded: Sequence[str],
           asset_label: str) -> Dict[str, Any]:
    """三件产物 + 判定，打包成结构化结果。"""
    meta = node_meta(graph)
    clo = closure(graph, target)
    miss = missing(graph, target, loaded)
    order = toposort(graph)
    return {
        "asset": asset_label,
        "graph_version": str(graph.get("version") or ""),
        "domain": str(graph.get("domain") or ""),
        "nodes": len(in_package_ids(graph)),
        "external_prereqs": len(graph.get("external_prereqs") or []),
        "target": target,
        "loaded": sorted({str(x) for x in loaded}),
        "closure": clo,
        "closure_size": len(clo),
        "missing": miss,
        "missing_size": len(miss),
        "missing_external": [c for c in miss if meta.get(c, {}).get("external")],
        "readiness": not miss,
        "load_order": order,
        "load_order_size": len(order),
    }


def render(res: Dict[str, Any]) -> str:
    lines = [
        "== AI 系统域 · 前置闭包求值（只读）==",
        "资产：%s（v%s · 域 %s · 节点 %d + 包外前置 %d）"
        % (res["asset"], res["graph_version"], res["domain"],
           res["nodes"], res["external_prereqs"]),
        "[1] 前置闭包 closure(%s)：%d 个概念" % (res["target"], res["closure_size"]),
        "    %s" % "、".join(res["closure"]),
        "[2] 缺失清单 missing(%s, L)：%d 个概念"
        % (res["target"], res["missing_size"]),
        "    %s" % ("、".join(res["missing"]) if res["missing"] else "（空 · 已就绪）"),
        "[3] 合法装载序 load_order（toposort 确定性线性化）：%d 个概念"
        % res["load_order_size"],
        "    %s" % "、".join(res["load_order"]),
        "已装载集 L：%d 个 · 就绪判定 readiness：%s"
        % (len(res["loaded"]), "就绪" if res["readiness"] else "未就绪"),
    ]
    if res["missing_external"]:
        lines.append("    其中包外前置（读者侧应已具备，不建模块）：%s"
                     % "、".join(res["missing_external"]))
    return "\n".join(lines)


# ---------------------------------------------------------------- 自检
def self_check(asset: str | Path = DEFAULT_ASSET) -> Tuple[List[str], List[str]]:
    """自检 → (failures, passes)。含负例注入：环 / 悬空 / 逆序。"""
    import copy

    fails: List[str] = []
    passes: List[str] = []

    def expect(cond: bool, label: str) -> None:
        (passes if cond else fails).append(label)

    graph = load_graph(asset)
    expect(not problems(graph), "图健康度：无环 / 无悬空 / 节点均有溯源与合法层位")

    clo = closure(graph, "C22")
    expect(len(clo) == 13 and "C22" in clo and "C00" in clo,
           "closure(C22) = 13 个概念（含自身与包外前置 C00）")

    loaded = ["C01", "C07", "C08", "C10", "C18"]
    miss = missing(graph, "C22", loaded)
    expect(len(miss) == 8 and "C22" in miss and "C09" in miss,
           "missing(C22, {C01,C07,C08,C10,C18}) = 8 个概念")
    expect(closure(graph, "C01") == ["C00", "C01"], "closure(C01) = {C00, C01}")

    order = toposort(graph)
    expect(len(order) == len(in_package_ids(graph)) and not [1 for _ in violations(graph, order)],
           "load_order 覆盖全部包内概念且对图零违反边")
    expect(toposort(graph) == order and closure(graph, "C22") == clo,
           "确定性：同输入两次求值逐字节一致")

    # 负例 1：注入环（C09 反向依赖 C12）→ 必须被检出
    cyc = copy.deepcopy(graph)
    for node in cyc["nodes"]:
        if node["id"] == "C09":
            node["prereqs"] = list(node["prereqs"]) + ["C12"]
    expect(any("环" in i for i in problems(cyc)), "负例：注入环被检出")

    # 负例 2：注入悬空前置 → 必须被检出
    dang = copy.deepcopy(graph)
    for node in dang["nodes"]:
        if node["id"] == "C22":
            node["prereqs"] = list(node["prereqs"]) + ["C99"]
    expect(any("悬空" in i for i in problems(dang)), "负例：悬空前置被检出")

    # 负例 3：逆序序列 → 违反边必须非零
    bad_seq = list(reversed(order))
    expect(len(violations(graph, bad_seq)) > 0, "负例：逆序序列的违反边非零")

    return fails, passes


# ---------------------------------------------------------------- CLI
def _orderings(graph: Dict[str, Any]) -> Dict[str, List[str]]:
    out: Dict[str, List[str]] = {}
    for item in graph.get("orderings") or []:
        if isinstance(item, dict) and item.get("id"):
            out[str(item["id"])] = [str(x) for x in (item.get("seq") or [])]
    return out


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="AI 系统域概念前置闭包求值（只读；不改仓库任何文件）")
    ap.add_argument("--asset", default=DEFAULT_ASSET,
                    help="概念图资产路径（缺省 %s）" % DEFAULT_ASSET)
    ap.add_argument("--target", default="C22", help="目标概念 id（如 C22）")
    ap.add_argument("--loaded", default="", help="已装载概念集，逗号分隔（如 C01,C07,C08）")
    ap.add_argument("--order", default="", help="校验资产内某个 orderings 序列的违反边")
    ap.add_argument("--json", action="store_true", help="输出结构化 JSON")
    ap.add_argument("--check", action="store_true", help="自检（含负例注入）")
    args = ap.parse_args(argv)

    try:
        if args.check:
            fails, passes = self_check(args.asset)
            for p in passes:
                print("  [PASS] %s" % p)
            for f in fails:
                print("  [FAIL] %s" % f)
            print("自检：%d/%d 通过" % (len(passes), len(passes) + len(fails)))
            return 0 if not fails else 1

        graph = load_graph(args.asset)
        health = problems(graph)
        if health:
            for i in health:
                print("  [FAIL] %s" % i)
            return 1

        if args.order:
            seqs = _orderings(graph)
            if args.order not in seqs:
                print("  ✗ 资产内无该序：%s（可用：%s）"
                      % (args.order, "、".join(sorted(seqs)) or "（无）"), file=sys.stderr)
                return 2
            bad = violations(graph, seqs[args.order])
            print("== 序校验：%s（%d 个概念）==" % (args.order, len(seqs[args.order])))
            print("  违反边：%d" % len(bad))
            for p, u in bad:
                print("    %s → %s 被违反（前置排在后继之后）" % (p, u))
            return 0

        loaded = [x.strip() for x in (args.loaded or "").split(",") if x.strip()]
        res = report(graph, args.target, loaded, args.asset)
        if args.json:
            print(json.dumps(res, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(render(res))
        return 0
    except ClosureError as exc:
        print("  ✗ %s" % exc, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
