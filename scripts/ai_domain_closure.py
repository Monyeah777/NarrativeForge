#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""概念前置闭包求值（只读 · 确定性 · 零网络 · 不改仓库任何文件）。

定位：把「概念前置依赖」从**内容**变成**可复算产物**——读**任一**域包资产的
`concept_graph` 机器可读块（缺省 `community/AI系统域包/assets/CONCEPT_GRAPH.md`，
跨域用 `--asset community/量化金融域包/assets/QUANT_GRAPH.md` 等），输出：

1. 前置闭包 `closure(c)`
2. 缺失清单 `missing(c, L)`（L = 已装载概念集）
3. 合法装载序 `load_order`（toposort 的确定性线性化）
4. 下一步可装载集 `frontier(L)`（就绪清单）

并附三件可证检查：图健康度（无环 / 无悬空 / 有溯源 / 层位合法 / 别名唯一 / 分支完备）、
「给定序列对图的违反边数」（判定某份讲序 / 目录序是不是本图的前置序）、锚点自检
`--check`（含负例注入）。

**图语义单一实现**：本脚本不自带一套图算法，而是复用 `desktop/src/core/concept_graph.py`
（同一实现被 verify check32 的概念图子扫描消费）——避免「门禁算一套、求值器算另一套」的双源漂移。

检索词解析：条目键 → 别名 → 概念名（大小写与首尾空白无关）；`--list` 可枚举全表。

纪律：本工具是**只读求值器**，不是 nf 子命令、不改 Schema；确定性 = 同输入同输出
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
import copy
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT / "desktop" / "src") not in sys.path:      # 复用 core 的图语义（单一实现）
    sys.path.insert(0, str(_ROOT / "desktop" / "src"))

from core.concept_graph import (                        # noqa: E402  （路径注入后再导入）
    BLOCK_MARKER, DEFAULT_ASSET, LAYERS, ClosureError, alias_map, branch_map,
    closure, fenced_block, frontier, in_package_ids, load_graph, missing,
    node_branch, node_meta, prereqs_of, problems, resolve, toposort, violations,
)


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
        "== 概念前置闭包求值（只读）==",
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
        description="概念前置闭包求值（只读；跨域通用——用 --asset 指定任一含 concept_graph 块的资产）")
    ap.add_argument("--asset", default=str(_ROOT / DEFAULT_ASSET),
                    help="概念图资产路径（缺省仓库内 %s）" % DEFAULT_ASSET)
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

        res = report(graph, args.target, loaded, os.path.relpath(args.asset, _ROOT)
                     if str(args.asset).startswith(str(_ROOT)) else str(args.asset))
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
