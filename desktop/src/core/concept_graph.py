"""概念图资产的门禁体检 + 图语义库（判据面收口，2026-09-20 作者裁决执行）。

背景（内部差距实证，见 `results/audit/docs_audit-50-ai-domain.md` §二）：概念前置偏序图
此前只落在**内容面**（域包资产的机器可读块），check 族全绿与图质量无关——图有环 / 前置
悬空 / 别名重复 / 节点未归支，门禁一条都不会红。本模块补上该判据面，并被两处消费：

- **门禁**：`quality_depth_scan.scan()` 的子扫描 → verify check32（**既有 check 内追加**，
  不新增 check 序号、不改 Schema）；
- **工具**：`scripts/ai_domain_closure.py`（只读求值器）复用本模块语义——图语义单一实现，
  避免「门禁算一套、求值器算另一套」的双源漂移。

判据（全部确定性、零第三方依赖；YAML 复用仓库既有依赖）：
- 结构：节点 id 唯一、层位 ∈ P00–P80、必备字段（name）、**边带 provenance**；
- 图论：无环（拓扑全序可达）、前置无悬空（须在节点表或外部前置族内）、无自环；
- 检索面：别名唯一（重复即歧义）；
- 分支面：分支 id 唯一、每个包内概念恰属一个分支、分支成员须真实存在。

纪律：没有 `concept_graph:` 机读块的资产一律跳过（不影响既有包与用户自定义资产）。
"""
from __future__ import annotations

import glob
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Sequence, Set, Tuple

BLOCK_MARKER = "concept_graph"
LAYERS = ("P00", "P10", "P20", "P30", "P40", "P50", "P60", "P70", "P80")
#: 默认资产路径（AI 系统域包自带概念图；工具侧缺省值）
DEFAULT_ASSET = "community/AI系统域包/assets/CONCEPT_GRAPH.md"
#: 资产货架（与 asset_ledger.SHELF_GLOBS 同口径，单层）
SHELF_GLOBS = (os.path.join("community", "*", "assets", "*.md"),
               os.path.join("05_资产库", "用户自定义", "*.md"))

_FENCE = re.compile(r"(?ms)^```yaml\s*\n(.*?)^```")


class ClosureError(ValueError):
    """求值 / 解析拒绝原因（缺资产、缺机读块、图非法、检索词无解）。"""


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


def graph_assets(root: str = ".") -> List[str]:
    """仓库内带概念图机读块的资产（相对路径，排序；无则空表）。"""
    out = []
    for pattern in SHELF_GLOBS:
        for f in sorted(glob.glob(os.path.join(root, pattern))):
            try:
                text = Path(f).read_text(encoding="utf-8")
            except OSError:
                continue
            if fenced_block(text):
                out.append(Path(f).relative_to(Path(root)).as_posix())
    return out


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
        if not str(node.get("name") or "").strip():
            issues.append("节点 %s 缺 name（修复指引：每个概念须有可读名）" % nid)
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


# ---------------------------------------------------------------- 门禁扫描
def scan(root: str = ".") -> Tuple[List[str], Dict[str, int]]:
    """全仓工程度扫描 → (issues, stats)（供 check32 子扫描；无图资产即中性通过）。"""
    issues: List[str] = []
    nodes = edges = 0
    assets = graph_assets(root)
    for rel in assets:
        try:
            graph = load_graph(Path(root) / rel)
        except ClosureError as exc:
            issues.append("%s: %s" % (rel, exc))
            continue
        prereqs = prereqs_of(graph)
        nodes += len(prereqs)
        edges += sum(len(v) for v in prereqs.values())
        for msg in problems(graph):
            issues.append("%s: %s" % (rel, msg))
    return issues, {"graphs": len(assets), "nodes": nodes, "edges": edges}
