"""一致性**声明**（借 ACP `CONFORMANCE.md`）：把「符合什么、管到哪、什么不管」写成清单。

NF 此前只有 `nf conformance` 的**报告**（跑一遍契约），没有**声明**——「哪些件在范围内、
哪些历史件被排除」是隐式的、散在 check 代码里。本模块把声明变成可机检件：

`protocol/CONFORMANCE.md` 三段（机器按标题解析，人也可读）：
- `## 声明`：规范 × 版本 × 真源（版本值必须与真源**逐条一致**）；
- `## 范围`：scope 白名单（每个路径必须**存在**）；
- `## 排除`：显式排除清单（路径 + 理由；路径须存在或匹配到文件）；
- 另有硬约束：**scope ∩ 排除 = ∅**（不许既在范围又排除）。

纪律：版本事实一律**从真源读**（01/02/registry.json/schema/基线常量），声明里改数字改不动门禁。
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

DECL_REL = "protocol/CONFORMANCE.md"
_ROW = re.compile(r"^\|\s*`?([^`|]+?)`?\s*\|\s*`?([^`|]+?)`?\s*\|\s*([^|]+?)\s*\|\s*$")
_ROW2 = re.compile(r"^\|\s*`?([^`|]+?)`?\s*\|\s*([^|]+?)\s*\|\s*$")
_BULLET = re.compile(r"^\s*[-*]\s+`([^`]+)`")


def _section(text: str, title: str) -> List[str]:
    """取 `## <title>` 到下一个同级标题之间的行。"""
    lines = text.splitlines()
    start = None
    for i, ln in enumerate(lines):
        if ln.strip() == "## " + title:
            start = i + 1
            continue
        if start is not None and ln.startswith("## "):
            return lines[start:i]
    return lines[start:] if start is not None else []


def parse(root: str = ".") -> Dict[str, Any]:
    """解析声明文件 → {versions, scope, excluded}。"""
    p = Path(root) / DECL_REL
    text = p.read_text(encoding="utf-8") if p.is_file() else ""
    versions = {}
    for ln in _section(text, "声明"):
        m = _ROW.match(ln.strip())
        if not m:
            continue
        name = m.group(1).strip()
        if name in ("规范",) or re.fullmatch(r"[-: ]+", name):
            continue                      # 表头 / 分隔行
        versions[name] = {"version": m.group(2).strip(),
                          "source": m.group(3).strip()}
    scope = [m.group(1).strip() for ln in _section(text, "范围")
             for m in [_BULLET.match(ln)] if m]
    excluded = []
    for ln in _section(text, "排除"):
        m = _ROW2.match(ln.strip())
        cell = m.group(1).strip() if m else ""
        if m and cell not in ("路径",) and not re.fullmatch(r"[-: ]+", cell):
            excluded.append({"path": m.group(1).strip(), "reason": m.group(2).strip()})
    return {"versions": versions, "scope": scope, "excluded": excluded}


def live_versions(root: str = ".") -> Dict[str, str]:
    """版本真源（声明必须与这里一致）。"""
    from core import quality_baseline as qb

    out: Dict[str, str] = {}
    reg = Path(root) / "desktop" / "src" / "core" / "registry.json"
    if reg.is_file():
        data = json.loads(reg.read_text(encoding="utf-8"))
        out["registry schema"] = str(data.get("registry_schema_version") or "")
    contract = Path(root) / "protocol" / "schema" / "contract.schema.json"
    if contract.is_file():
        data = json.loads(contract.read_text(encoding="utf-8"))
        enum = ((data.get("properties") or {}).get("schema") or {}).get("enum") or []
        out["machine_contract schema"] = ",".join(str(x) for x in enum)
    prot = sorted((Path(root) / "community").glob("*/protocol.yaml"))
    if prot:
        m = re.search(r'schema_version\s*:\s*"?([\w.]+)"?',
                      prot[0].read_text(encoding="utf-8"))
        out["protocol.yaml schema"] = m.group(1) if m else ""
    schemas = sorted((Path(root) / "protocol" / "schema").glob("*.json"))
    out["IDL schema 集"] = "%d 件" % len(schemas)
    verify_path = Path(root) / "verify.sh"
    verify = verify_path.read_text(encoding="utf-8") if verify_path.is_file() else ""
    vm = re.search(r"# 版本 : (v[\d.]+)", verify)
    # 缺 verify.sh 的临时夹具：基线真源退化为常量（如实标注版本未知），不崩
    out["基线"] = "%s · check1-%d · PASS=%d" % (
        vm.group(1) if vm else "?", qb.EXPECTED_CHECKS, qb.EXPECTED_PASS)
    return out


def scan(root: str = ".") -> Tuple[List[str], Dict[str, Any]]:
    """声明机检 → (issues, stats)。"""
    issues: List[str] = []
    decl = parse(root)
    live = live_versions(root)
    if not decl["versions"]:
        issues.append("声明文件缺 `## 声明` 版本表（修复指引：见 %s）" % DECL_REL)
    for name, want in live.items():
        got = (decl["versions"].get(name) or {}).get("version", "")
        if got != want:
            issues.append("声明与真源不一致：%s 声明=%s 真源=%s（修复指引：改声明对齐真源）"
                          % (name, got or "(缺)", want))
    # 反向：声明了真源里根本没有的规范项 = 无法核验的声明（不许用声明充数）
    for name in decl["versions"]:
        if name not in live:
            issues.append("声明了无法核验的规范项：%s（真源缺失；修复指引：补真源或删该行）" % name)
    if not decl["scope"]:
        issues.append("声明文件缺 `## 范围` 白名单")
    for rel in decl["scope"]:
        if not (Path(root) / rel).exists():
            issues.append("范围里的路径不存在：%s（修复指引：删掉或改正）" % rel)
    if not decl["excluded"]:
        issues.append("声明文件缺 `## 排除` 清单（显式排除是声明的核心价值）")
    for item in decl["excluded"]:
        rel = item["path"]
        if not rel:
            continue
        if any(ch in rel for ch in "*?["):
            if not list(Path(root).glob(rel)):
                issues.append("排除项 glob 无匹配：%s" % rel)
        elif not (Path(root) / rel).exists():
            issues.append("排除项路径不存在：%s（修复指引：删除该条或修正路径）" % rel)
    scope_set = {s.rstrip("/") for s in decl["scope"]}
    for item in decl["excluded"]:
        rel = item["path"].rstrip("/")
        for s in scope_set:
            if rel == s or rel.startswith(s + "/") or s.startswith(rel + "/"):
                issues.append("scope 与排除重叠：%s ↔ %s（同一条不能既在范围又排除）" % (s, rel))
    stats = {"versions": len(decl["versions"]), "scope": len(decl["scope"]),
             "excluded": len(decl["excluded"]),
             "live": live}
    return issues, stats
