#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AI 系统域 · 概念前置闭包求值（只读 · 确定性 · 零网络 · 不改仓库任何文件）。

定位：把「概念前置依赖」从**内容**变成**可复算产物**——读域包资产
`community/AI系统域包/assets/CONCEPT_GRAPH.md` 的机器可读块，输出：

1. 前置闭包 `closure(c)`
2. 缺失清单 `missing(c, L)`（L = 已装载概念集）
3. 合法装载序 `load_order`（toposort 的确定性线性化）
4. 下一步可装载集 `frontier(L)`（就绪清单）

并附三件可证检查：图健康度（无环 / 无悬空 / 有溯源 / 层位合法 / 别名唯一 / 分支完备）、
「给定序列对图的违反边数」（判定某份讲序 / 目录序是不是本图的前置序）、锚点自检
`--check`（含负例注入）。

检索词解析：条目键 → 别名 → 概念名（大小写与首尾空白无关）；`--list` 可枚举全表。

纪律：本工具是**只读求值器**，不是 nf 子命令、不是门禁、不改 Schema；确定性 = 同输入同输出
（并列按 id 升序，集合输出一律排序）。YAML 解析复用仓库既有 PyYAML 依赖。

用法（仓库根目录）：
  python scripts/ai_domain_closure.py --list
  python scripts/ai_domain_closure.py --target C22 --loaded C01,C07,C08,C10,C18
  python scripts/ai_domain_closure.py --target RAG --json
  python scripts/ai_domain_closure.py --ready-list --loaded C00,C01,C20 --branch app
  python scripts/ai_domain_closure.py --gaps --loaded C00,C01 --branch app --limit 10
  python scripts/ai_domain_closure.py --order design-guide-chapter-order
  python scripts/ai_domain_closure.py --check
退出码：0 成功 / 1 自检、图健康度或输入非法 / 2 用法错误。
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
    """求值拒绝原因（缺资产 / 缺机读块 / 图非法 / 检索词无解）。"""


# ---------------------------------------------------------------- 读取机读块
def fenced_block(text: str, marker: str = BLOCK_MARKER) -> str:
    """取含 marker 的 ```yaml 围栏正文（无则空串）。"""
    for m in _FENCE.finditer(text):
        body = m.group(1)
        if re.search(r"(?m)^%s\s*:" % re.escape(marker), body):
            return body
    return ""


def load_graph(asset_path: str | Path = DEFAULT_ASSET) -> Dict[str, Any]:
    """读资产 → `concept_graph` 字典（缺件 / 缺块 / 解析失败一律抛 ClosureError）。"""
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


def branch_map(graph: Dict[str, Any]) -> Dict[str, List[str]]:
    """{分支 id: [概念 id]}（保持资产声明序）。"""
    out: Dict[str, List[str]] = {}
    for br in graph.get("branches") or []:
        if isinstance(br, dict) and br.get("id"):
            out[str(br["id"])] = [str(x) for x in (br.get("nodes") or [])]
    return out


def node_branch(graph: Dict[str, Any]) -> Dict[str, str]:
    """{概念 id: 分支 id}（未归入任何分支者不进映射）。"""
    out: Dict[str, str] = {}
    for bid, nodes in branch_map(graph).items():
        for nid in nodes:
            out.setdefault(nid, bid)
    return out


def alias_map(graph: Dict[str, Any]) -> Dict[str, str]:
    """{别名（casefold）: 概念 id}；别名重复即抛 ClosureError（防歧义）。"""
    out: Dict[str, str] = {}
    for node in graph.get("nodes") or []:
        if not isinstance(node, dict) or not node.get("id"):
            continue
        nid = str(node["id"])
        for raw in node.get("aliases") or []:
            key = str(raw).strip().casefold()
            if not key:
                continue
            if key in out and out[key] != nid:
                raise ClosureError("别名重复：%r 同时指向 %s 与 %s"
                                   "（修复指引：别名在图内须唯一——与 01 §1.1 词法纪律同源）"
                                   % (raw, out[key], nid))
            out[key] = nid
    return out


def resolve(graph: Dict[str, Any], token: str) -> str:
    """检索词 → 概念 id（顺序：条目键 → 别名 → 概念名）。"""
    t = str(token).strip()
    meta = node_meta(graph)
    if t in meta:
        return t
    am = alias_map(graph)
    if t.casefold() in am:
        return am[t.casefold()]
    for nid, rec in meta.items():
        if str(rec.get("name") or "").strip().casefold() == t.casefold():
            return nid
    raise ClosureError("检索词不在图中：%s（修复指引：用条目键 Cxx、别名或概念名——"
                       "`--list` 可枚举全表）" % token)


def closure(graph: Dict[str, Any], target: str) -> List[str]:
    """传递闭包 closure(target) = {target} ∪ ⋃ closure(p)；返回排序列表。"""
    tid = resolve(graph, target)
    prereqs = prereqs_of(graph)
    seen: Set[str] = set()
    stack = [tid]
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


def frontier(graph: Dict[str, Any], loaded: Sequence[str], branch: str = "") -> List[str]:
    """就绪清单 frontier(L) = {c ∉ L : prereqs(c) ⊆ L}（可限定分支）。"""
    have = {str(x) for x in loaded}
    prereqs = prereqs_of(graph)
    bids = node_branch(graph) if branch else {}
    out = []
    for c in in_package_ids(graph):
        if c in have:
            continue
        if branch and bids.get(c) != branch:
            continue
        if all(p in have for p in prereqs.get(c, [])):
            out.append(c)
    return sorted(out)


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
        raise ClosureError("概念图存在环，无法给出装载序"
                           "（修复指引：按资产 §4 conflict_rules 归并并列节点）")
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
    """图健康度：无环 / 无悬空 / 边有溯源 / 层位合法 / id 唯一 / 别名唯一 / 分支完备。"""
    issues: List[str] = []
    prereqs = prereqs_of(graph)
    ext = {str(x.get("id")) for x in (graph.get("external_prereqs") or [])
           if isinstance(x, dict)}
    declared = set(prereqs) | ext
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
                issues.append("悬空前置：%s ← %s（前置不在节点表 / 外部前置族中）" % (nid, p))
            if p == nid:
                issues.append("自环：%s ← %s" % (nid, p))
    # 分支完备：每个包内概念须恰属一个分支；分支成员须是已知概念
    bids = node_branch(graph)
    for nid in sorted(set(prereqs) - set(bids)):
        issues.append("概念 %s 未归入任何分支（修复指引：在图 branches 段登记）" % nid)
    for nid in sorted(set(bids) - set(prereqs)):
        issues.append("分支声明了不存在的概念：%s（修复指引：核对 branches.nodes）" % nid)
    flat = [n for v in branch_map(graph).values() for n in v]
    if len(flat) != len(set(flat)):
        issues.append("概念被多个分支重复声明（修复指引：一概念只入一个分支）")
    try:
        alias_map(graph)
    except ClosureError as exc:
        issues.append(str(exc))
    try:
        toposort(graph)
    except ClosureError as exc:
        issues.append(str(exc))
    return issues


# ---------------------------------------------------------------- 输出
def report(graph: Dict[str, Any], target: str, loaded: Sequence[str],
           asset_label: str) -> Dict[str, Any]:
    """四件产物 + 判定，打包成结构化结果。"""
    tid = resolve(graph, target)
    meta = node_meta(graph)
    bids = node_branch(graph)
    clo = closure(graph, tid)
    miss = missing(graph, tid, loaded)
    order = toposort(graph)
    front = frontier(graph, loaded)
    return {
        "asset": asset_label,
        "graph_version": str(graph.get("version") or ""),
        "domain": str(graph.get("domain") or ""),
        "nodes": len(in_package_ids(graph)),
        "external_prereqs": len(graph.get("external_prereqs") or []),
        "branches": {k: len(v) for k, v in sorted(branch_map(graph).items())},
        "target": tid,
        "target_query": str(target),
        "target_name": str(meta.get(tid, {}).get("name") or ""),
        "target_branch": bids.get(tid, ""),
        "loaded": sorted({str(x) for x in loaded}),
        "closure": clo,
        "closure_size": len(clo),
        "missing": miss,
        "missing_size": len(miss),
        "missing_external": [c for c in miss if meta.get(c, {}).get("external")],
        "readiness": not miss,
        "load_order": order,
        "load_order_size": len(order),
        "frontier": front,
        "frontier_size": len(front),
    }


def render(res: Dict[str, Any]) -> str:
    lines = [
        "== AI 系统域 · 前置闭包求值（只读）==",
        "资产：%s（v%s · 域 %s · 节点 %d + 包外前置 %d · 分支 %s）"
        % (res["asset"], res["graph_version"], res["domain"], res["nodes"],
           res["external_prereqs"],
           " / ".join("%s=%d" % (k, v) for k, v in sorted(res["branches"].items()))),
        "目标：%s（%s）· 分支 %s" % (res["target"], res["target_name"],
                                 res["target_branch"] or "-"),
        "[1] 前置闭包 closure(%s)：%d 个概念" % (res["target"], res["closure_size"]),
        "    %s" % "、".join(res["closure"]),
        "[2] 缺失清单 missing(%s, L)：%d 个概念" % (res["target"], res["missing_size"]),
        "    %s" % ("、".join(res["missing"]) if res["missing"] else "（空 · 已就绪）"),
        "[3] 合法装载序 load_order（toposort 确定性线性化）：%d 个概念"
        % res["load_order_size"],
        "    %s" % "、".join(res["load_order"]),
        "[4] 下一步可装载集 frontier(L)：%d 个概念" % res["frontier_size"],
        "    %s" % ("、".join(res["frontier"]) if res["frontier"] else "（空）"),
        "已装载集 L：%d 个 · 就绪判定 readiness：%s"
        % (len(res["loaded"]), "就绪" if res["readiness"] else "未就绪"),
    ]
    if res["missing_external"]:
        lines.append("    其中包外前置（读者侧应已具备，不建模块）：%s"
                     % "、".join(res["missing_external"]))
    return "\n".join(lines)


def render_list(graph: Dict[str, Any]) -> str:
    """条目键全表 + 别名（人读；供 --list）。"""
    meta = node_meta(graph)
    bids = node_branch(graph)
    lines = ["== 条目键全表（%d 概念 + %d 包外前置）=="
             % (len(in_package_ids(graph)), len(graph.get("external_prereqs") or []))]
    for nid in in_package_ids(graph):
        rec = meta[nid]
        al = "、".join(str(x) for x in (rec.get("aliases") or []))
        lines.append("  %-4s [%-7s] %-6s %s%s"
                     % (nid, bids.get(nid, "-"), str(rec.get("layer") or "-"),
                        rec.get("name") or "", ("（别名：%s）" % al) if al else ""))
    return "\n".join(lines)


def render_gaps(graph: Dict[str, Any], loaded: Sequence[str], branch: str,
                limit: int) -> str:
    """前置缺失清单（只列非空，按缺失规模降序；供 --gaps）。"""
    meta = node_meta(graph)
    bids = node_branch(graph)
    rows = []
    for nid in in_package_ids(graph):
        if branch and bids.get(nid) != branch:
            continue
        miss = missing(graph, nid, loaded)
        if miss:
            rows.append((nid, miss))
    rows.sort(key=lambda r: (-len(r[1]), r[0]))
    lines = ["== 前置缺失清单（L=%d 概念%s · 非空项 %d）=="
             % (len({str(x) for x in loaded}),
                (" · 分支 " + branch) if branch else "", len(rows))]
    for nid, miss in rows[:limit]:
        ext = [c for c in miss if meta.get(c, {}).get("external")]
        lines.append("  %-4s %-30s 缺 %2d：%s%s"
                     % (nid, str(meta.get(nid, {}).get("name") or "")[:30], len(miss),
                        "、".join(miss[:8]) + ("…" if len(miss) > 8 else ""),
                        ("（含包外前置 %s）" % "、".join(ext)) if ext else ""))
    if len(rows) > limit:
        lines.append("  …（另有 %d 项，--limit 调整）" % (len(rows) - limit))
    return "\n".join(lines)


# ---------------------------------------------------------------- 自检
def self_check(asset: str | Path = DEFAULT_ASSET) -> Tuple[List[str], List[str]]:
    """自检 → (failures, passes)。含负例注入：环 / 悬空 / 别名重复 / 分支缺口。"""
    import copy

    fails: List[str] = []
    passes: List[str] = []

    def expect(cond: bool, label: str) -> None:
        (passes if cond else fails).append(label)

    graph = load_graph(asset)
    expect(not problems(graph),
           "图健康度：无环 / 无悬空 / 有溯源 / 层位合法 / 别名唯一 / 分支完备")

    clo = closure(graph, "C22")
    expect(len(clo) == 13 and "C22" in clo and "C00" in clo,
           "closure(C22) = 13 个概念（含自身与包外前置 C00）")

    loaded = ["C01", "C07", "C08", "C10", "C18"]
    miss = missing(graph, "C22", loaded)
    expect(len(miss) == 8 and "C22" in miss and "C09" in miss,
           "missing(C22, {C01,C07,C08,C10,C18}) = 8 个概念")
    expect(closure(graph, "C01") == ["C00", "C01"], "closure(C01) = {C00, C01}")

    order = toposort(graph)
    expect(len(order) == len(in_package_ids(graph)) and not violations(graph, order),
           "load_order 覆盖全部包内概念且对图零违反边")
    expect(toposort(graph) == order and closure(graph, "C22") == clo,
           "确定性：同输入两次求值逐字节一致")

    expect(resolve(graph, "RAG") == "C28" and resolve(graph, "PagedAttention") == "C22"
           and resolve(graph, "  autodiff  ") == "C08",
           "检索词解析：别名（含大小写 / 空白）与条目键同解")
    expect(closure(graph, "RAG") == closure(graph, "C28"), "别名闭包与条目键闭包一致")

    front = frontier(graph, ["C00", "C01"])
    expect("C02" in front and "C25" not in front,
           "frontier({C00,C01}) 含 C02 且不含前置未齐的 C25")
    expect(frontier(graph, ["C00", "C01"], branch="app") == [],
           "frontier 分支过滤生效（app 支此时为空）")

    cyc = copy.deepcopy(graph)
    for node in cyc["nodes"]:
        if node["id"] == "C09":
            node["prereqs"] = list(node["prereqs"]) + ["C12"]
    expect(any("环" in i for i in problems(cyc)), "负例：注入环被检出")

    dang = copy.deepcopy(graph)
    for node in dang["nodes"]:
        if node["id"] == "C22":
            node["prereqs"] = list(node["prereqs"]) + ["C99"]
    expect(any("悬空" in i for i in problems(dang)), "负例：悬空前置被检出")

    dup = copy.deepcopy(graph)
    for node in dup["nodes"]:
        if node["id"] == "C29":
            node["aliases"] = list(node.get("aliases") or []) + ["RAG"]
    expect(any("别名重复" in i for i in problems(dup)), "负例：重复别名被检出")

    nbr = copy.deepcopy(graph)
    for br in nbr["branches"]:
        br["nodes"] = [n for n in br["nodes"] if n != "C45"]
    expect(any("未归入任何分支" in i for i in problems(nbr)), "负例：分支缺口被检出")

    expect(len(violations(graph, list(reversed(order)))) > 0, "负例：逆序序列的违反边非零")

    return fails, passes


# ---------------------------------------------------------------- CLI
def _orderings(graph: Dict[str, Any]) -> Dict[str, List[str]]:
    out: Dict[str, List[str]] = {}
    for item in graph.get("orderings") or []:
        if isinstance(item, dict) and item.get("id"):
            out[str(item["id"])] = [str(x) for x in (item.get("seq") or [])]
    return out


def _loaded_arg(raw: str) -> List[str]:
    return [x.strip() for x in (raw or "").split(",") if x.strip()]


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="AI 系统域概念前置闭包求值（只读；不改仓库任何文件）")
    ap.add_argument("--asset", default=DEFAULT_ASSET,
                    help="概念图资产路径（缺省 %s）" % DEFAULT_ASSET)
    ap.add_argument("--target", default="C22",
                    help="目标概念：条目键 / 别名 / 概念名（如 C22、RAG、PagedAttention）")
    ap.add_argument("--loaded", default="", help="已装载概念集，逗号分隔（如 C00,C01,C20）")
    ap.add_argument("--branch", default="", help="分支过滤（compute / app；缺省全图）")
    ap.add_argument("--order", default="", help="校验资产内某个 orderings 序列的违反边")
    ap.add_argument("--list", action="store_true", help="列条目键全表（含别名）")
    ap.add_argument("--ready-list", action="store_true",
                    help="输出下一步可装载集 frontier(L)（可配 --branch）")
    ap.add_argument("--gaps", action="store_true",
                    help="输出前置缺失清单（只列非空项；可配 --branch / --limit）")
    ap.add_argument("--limit", type=int, default=20, help="--gaps 输出行数上限（缺省 20）")
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
        bids = branch_map(graph)
        if args.branch and args.branch not in bids:
            print("  ✗ 未知分支：%s（可用：%s）"
                  % (args.branch, "、".join(sorted(bids)) or "（无）"), file=sys.stderr)
            return 2

        if args.list:
            print(render_list(graph))
            return 0

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

        loaded = _loaded_arg(args.loaded)
        if args.gaps:
            print(render_gaps(graph, loaded, args.branch, max(1, args.limit)))
            return 0

        if args.ready_list:
            front = frontier(graph, loaded, args.branch)
            if args.json:
                print(json.dumps({"loaded": sorted({str(x) for x in loaded}),
                                  "branch": args.branch, "frontier": front,
                                  "frontier_size": len(front)},
                                 ensure_ascii=False, indent=2, sort_keys=True))
            else:
                print("== 下一步可装载集 frontier(L)（%s）=="
                      % ("分支 " + args.branch if args.branch else "全图"))
                print("  L = %s" % ("、".join(sorted({str(x) for x in loaded})) or "（空）"))
                print("  frontier = %s（%d 个）"
                      % ("、".join(front) if front else "（空）", len(front)))
            return 0

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
