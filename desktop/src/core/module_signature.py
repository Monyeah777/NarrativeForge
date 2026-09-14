"""模块**边界签名**基线（机制借鉴 Pipelex 的 `signature_for`：边界写一次、实现可替）。

NF 的 `machine_contract` 是「人读契约的机读投影」，会随实现一起改；缺的是**边界冻结**：
一个模块对外的承诺（id / inputs / outputs / events / interfaces）改了，必须显式重签，
不能被顺手改掉。

- 基线 = `protocol/module_signatures.json`（模块 id → 边界字段 + 摘要）；
- 新增模块 → 提示补签；消失模块 → 提示撤签；**边界漂移 = FAIL**，直到显式
  `nf module signature --write` 重新冻结（重签即留下 diff 供评审）。

纪律：只取边界字段（不含 description/note 等易变文本）；纯标准库。
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

SCHEMA = "nf-module-signatures/1"
BASELINE_REL = "protocol/module_signatures.json"
_BOUNDARY_KEYS = ("inputs", "outputs", "events", "interfaces", "layer", "category",
                  "io_types")


def signatures(root: str = ".") -> Dict[str, Dict[str, Any]]:
    """全仓模块边界签名（id → {digest, boundary, path}）。"""
    from core import conformance_scan as csc

    out: Dict[str, Dict[str, Any]] = {}
    for doc in csc._module_docs(root):
        text = Path(doc).read_text(encoding="utf-8")
        parsed = csc._fence_yaml(text, "machine_contract")
        mc = parsed.get("machine_contract") if isinstance(parsed, dict) else None
        if not isinstance(mc, dict):
            continue
        mid = str(mc.get("id") or "")
        if not mid:
            continue
        boundary = {k: mc.get(k) for k in _BOUNDARY_KEYS}
        blob = json.dumps(boundary, sort_keys=True, ensure_ascii=False,
                          separators=(",", ":")).encode("utf-8")
        out[mid] = {"digest": hashlib.sha256(blob).hexdigest(),
                    "boundary": boundary,
                    "path": Path(doc).relative_to(root).as_posix()}
    return out


def baseline(root: str = ".", rel: str = BASELINE_REL) -> Dict[str, Any]:
    p = Path(root) / rel
    if not p.is_file():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def write(root: str = ".", rel: str = BASELINE_REL) -> str:
    sigs = signatures(root)
    doc = {"schema": SCHEMA, "count": len(sigs),
           "modules": {k: {"digest": v["digest"], "path": v["path"]}
                       for k, v in sorted(sigs.items())}}
    p = Path(root) / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(doc, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                 encoding="utf-8", newline="\n")
    return rel


def verify(root: str = ".", rel: str = BASELINE_REL) -> Tuple[List[str], List[str], Dict[str, Any]]:
    """→ (issues, warns, stats)：边界漂移 = FAIL；未签/撤签 = WARN。"""
    issues: List[str] = []
    warns: List[str] = []
    base = baseline(root, rel)
    if not base:
        return ["缺模块边界基线 %s（修复指引：nf module signature --write）" % rel], [], {}
    sigs = signatures(root)
    base_mods = base.get("modules") or {}
    for mid, rec in sorted(sigs.items()):
        if mid not in base_mods:
            warns.append("新模块未签边界：%s（修复指引：nf module signature --write）" % mid)
        elif base_mods[mid].get("digest") != rec["digest"]:
            issues.append("边界漂移：%s（inputs/outputs/events/interfaces 变了）"
                          "（修复指引：评审后 nf module signature --write 重新冻结）" % mid)
    for mid in sorted(set(base_mods) - set(sigs)):
        warns.append("基线中的模块已不在仓库：%s（修复指引：重签以撤下）" % mid)
    stats = {"modules": len(sigs), "signed": len(base_mods),
             "drifted": [i.split("：")[1].split("（")[0] for i in issues]}
    return issues, warns, stats
