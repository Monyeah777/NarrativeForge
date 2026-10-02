"""模块级耦合度量与**只许收敛**的债务闸门（架构纯度/可维护性面 · ISO 25010 可维护性）。

外部标准对接（Robert C. Martin《Clean Architecture》包度量 + 稳定依赖原则 SDP）：
- **Ca**（afferent coupling）= 有多少同包模块依赖我；**Ce**（efferent）= 我依赖多少同包模块；
  **I = Ce/(Ca+Ce)**（0 = 最稳，1 = 最不稳）。
- **SDP（稳定依赖原则）**：依赖关系应指向**更稳定**（I 更小）的一侧。
- **环（cycle）**：模块级依赖成环 = 无法单独理解/替换其中任一模块。

为什么是「登记债 + 棘轮」而不是「一律判死」（实测口径）：
首日实测 core 122 个模块 → **3 个模块级环 + 5 处 SDP 违例**（`conformance_scan↔disk_cache`、
`domain_pack→output_forms→pack_combo→domain_pack`、`library↔receipts` 等）。这些是存量设计债，
一次性判死会立刻红门禁且要求重构正被并发会话改写的文件——**代价与风险都不该由一次判据上线承担**。
故：**登记在册的债放行（可审计）**，判据只拦**新增**环/新增 SDP 违例（只减不增）；
债务被消掉时记 WARN 提示从登记表移除（债务表不得虚挂）。

纪律：纯标准库；只读扫描（唯 `write()` 落盘）；错误消息带修复指引。
"""
from __future__ import annotations

import ast

from core import atomic_write
import json
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

BASELINE_REL = "protocol/coupling_baseline.json"
SCHEMA = "nf-coupling/1"
SCAN_DIR = "desktop/src/core"
#: 依赖图里忽略的模块（无耦合语义的包入口）
SKIP = {"__init__"}


def _module_deps(path: Path, known: Set[str]) -> Set[str]:
    """该模块依赖的同包模块名集合（`core.X` / `from core import X` / `from . import X`）。"""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
    except SyntaxError:
        return set()
    out: Set[str] = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.ImportFrom):
            if n.module == "core":
                out.update(a.name.split(".")[0] for a in n.names)
            elif n.module and n.module.startswith("core."):
                out.add(n.module.split(".")[1])
            elif n.level and n.module:
                out.add(n.module.split(".")[0])
            elif n.level and not n.module:
                out.update(a.name.split(".")[0] for a in n.names)
        elif isinstance(n, ast.Import):
            for a in n.names:
                if a.name.startswith("core."):
                    out.add(a.name.split(".")[1])
    return {d for d in out if d in known and d != path.stem}


def graph(root: str = ".") -> Tuple[Dict[str, Set[str]], Dict[str, Dict[str, Any]]]:
    """→ (deps, metrics)：deps[模块] = 依赖集合；metrics[模块] = {ca, ce, i}。"""
    d = Path(root) / SCAN_DIR
    known = {p.stem for p in d.glob("*.py")} - SKIP
    deps = {m: _module_deps(d / (m + ".py"), known) for m in sorted(known)}
    ca = {m: sum(1 for o, ds in deps.items() if m in ds) for m in known}
    ce = {m: len(ds) for m, ds in deps.items()}
    metrics = {m: {"ca": ca[m], "ce": ce[m],
                   "i": round(ce[m] / (ca[m] + ce[m]), 4) if (ca[m] + ce[m]) else 0.0}
               for m in sorted(known)}
    return deps, metrics


def cycles(deps: Dict[str, Set[str]]) -> List[Tuple[str, ...]]:
    """模块级环（去重、成员排序后返回）。"""
    color: Dict[str, int] = {}
    found: Set[Tuple[str, ...]] = set()
    stack: List[str] = []

    def dfs(u: str) -> None:
        color[u] = 1
        stack.append(u)
        for v in sorted(deps.get(u, ())):
            if color.get(v, 0) == 1:
                cyc = stack[stack.index(v):]
                found.add(tuple(sorted(set(cyc))))
            elif color.get(v, 0) == 0:
                dfs(v)
        stack.pop()
        color[u] = 2

    for m in sorted(deps):
        if color.get(m, 0) == 0:
            dfs(m)
    return sorted(found)


def sdp_violations(deps: Dict[str, Set[str]], metrics: Dict[str, Dict[str, Any]]
                   ) -> List[Tuple[str, str]]:
    """稳定依赖原则违例：A 依赖 B 而 B 比 A 更不稳（I 更大）→ (A, B)。"""
    out = []
    for m, ds in deps.items():
        for d in sorted(ds):
            if metrics[d]["i"] > metrics[m]["i"] + 1e-9:
                out.append((m, d))
    return sorted(out)


def load_baseline(root: str = ".") -> Dict[str, Any]:
    p = Path(root) / BASELINE_REL
    if not p.is_file():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except ValueError:  # 基线缺失/坏件 ⇒ 空基线：全部环/违例按「新增」判（fail-closed，宁可全报）
        return {}


def scan(root: str = ".") -> Tuple[List[str], List[str], Dict[str, Any]]:
    """→ (issues, warns, stats)：**新增**环 / **新增** SDP 违例 = FAIL；已消债务仍挂 = WARN。"""
    deps, metrics = graph(root)
    cyc = cycles(deps)
    sdp = sdp_violations(deps, metrics)
    base = load_baseline(root)
    known_cyc = {tuple(sorted(c)) for c in (base.get("cycles") or [])}
    # SDP 有**方向**（A 依赖 B，不是 B 依赖 A）——故不排序，按 (依赖方, 被依赖方) 精确比对
    known_sdp = {tuple(p) for p in (base.get("sdp") or [])}
    issues: List[str] = []
    warns: List[str] = []
    if not base:
        warns.append("无耦合基线 %s（本次按「零容忍」判：修复指引 "
                     "python scripts/coupling_metrics.py --write 登记存量债）" % BASELINE_REL)
        known_cyc, known_sdp = set(), set()
    for c in cyc:
        if c not in known_cyc:
            issues.append("新增模块级环：%s（修复指引：断开其中一条依赖——常是惰性 import 循环；"
                          "确属设计债须评审后 python scripts/coupling_metrics.py --write 登记）"
                          % " → ".join(list(c) + [c[0]]))
    for a, b in sdp:
        if (a, b) not in known_sdp:
            issues.append("新增 SDP 违例：%s(I=%.2f) 依赖了更不稳的 %s(I=%.2f)（修复指引：把依赖"
                          "反向——让稳定侧定义接口、由不稳侧实现；确属存量债须评审后 --write 登记）"
                          % (a, metrics[a]["i"], b, metrics[b]["i"]))
    for c in sorted(known_cyc - set(cyc)):
        warns.append("登记环已消除：%s（修复指引：从 %s 的 cycles 移除）"
                     % (" → ".join(list(c) + [c[0]]), BASELINE_REL))
    for a, b in sorted(known_sdp - set(sdp)):
        warns.append("登记 SDP 违例已消除：%s → %s（修复指引：从 %s 的 sdp 移除）"
                     % (a, b, BASELINE_REL))
    stats = {"modules": len(deps), "cycles": len(cyc), "sdp": len(sdp),
             "registered_cycles": len(known_cyc), "registered_sdp": len(known_sdp)}
    return issues, warns, stats


def write(root: str = ".") -> Tuple[List[str], Dict[str, Any]]:
    """把当前环/SDP 违例登记为存量债（显式动作）→ (issues, doc)。"""
    deps, metrics = graph(root)
    doc = {"schema": SCHEMA,
           "note": "存量耦合债登记（棘轮：只许减少；新增环/SDP 违例判 FAIL，除非评审后重登）",
           "cycles": [list(c) for c in cycles(deps)],
           "sdp": [list(p) for p in sdp_violations(deps, metrics)],
           "metrics": metrics}
    p = Path(root) / BASELINE_REL
    atomic_write.write_text(p, json.dumps(doc, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    return [], doc
