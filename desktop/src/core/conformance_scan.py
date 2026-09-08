"""43 A2 —— Conformance 一致性分级扫描（声明 ≤ 可证级别，防虚标）。

分级定义见 01 §1.2：L0 结构可读 / L1 机读契约 / L2 装配可执行 / L3 外部互操作。

扫描对象：
- 模块文档 machine_contract.conformance（23 件机读块，check28 约束必带）
- community/*/protocol.yaml package.conformance（5 协议包，在册 = L2）
- protocol/export_conformance.json（导出契约面 manifest，L3 = 导出门禁锁定面）

用法：conformance_scan.scan('.') -> (issues, stats)
"""

from __future__ import annotations

import glob
import json
import os
import re
from typing import Any, Dict, List, Tuple

try:
    import yaml  # PyYAML（仓库既有依赖）
except Exception:  # pragma: no cover
    yaml = None  # type: ignore[assignment]

FENCE = re.compile(r"(?ms)```yaml\s*(.*?)```")
_T = chr(96) * 3


def _read_json(path: str) -> Tuple[Any, str]:
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh), ""
    except Exception as exc:
        return None, str(exc)


def _fence_yaml(text: str, marker: str) -> Dict[str, Any]:
    for m in FENCE.finditer(text):
        body = m.group(1)
        if marker not in body:
            continue
        try:
            parsed = yaml.safe_load(body) if yaml is not None else None
        except Exception:
            return {}
        if isinstance(parsed, dict):
            return parsed
    return {}


def _module_docs(root: str) -> List[str]:
    out: List[str] = []
    for sub in ["04_模块库"]:
        base = os.path.join(root, sub)
        if os.path.isdir(base):
            for dirpath, _, files in os.walk(base):
                out += [os.path.join(dirpath, f) for f in files if f.endswith(".md")]
    pkg_dir = os.path.join(root, "community")
    if os.path.isdir(pkg_dir):
        for pkg in sorted(os.listdir(pkg_dir)):
            mdir = os.path.join(pkg_dir, pkg, "modules")
            if os.path.isdir(mdir):
                out += [os.path.join(mdir, f) for f in sorted(os.listdir(mdir)) if f.endswith(".md")]
    return sorted(out)


def _evidence_ids(root: str) -> List[str]:
    """官方 registry modules[] + community registry protocols[].module_ids（装配在册证据）。"""
    reg, _ = _read_json(os.path.join(root, "desktop", "src", "core", "registry.json"))
    ids: List[str] = []
    if isinstance(reg, dict):
        for m in reg.get("modules") or []:
            if isinstance(m, dict) and isinstance(m.get("id"), str):
                ids.append(m["id"])
        for p in reg.get("protocols") or []:
            for mid in (p.get("module_ids") or []):
                if isinstance(mid, str):
                    ids.append(mid)
    return ids


def scan(root: str = ".") -> Tuple[List[str], Dict[str, int]]:
    issues: List[str] = []
    if yaml is None:
        issues.append("PyYAML 不在（conformance_scan 依赖仓库既有 yaml 依赖）")
        return issues, {"modules_mc": 0, "packages": 0, "export_items": 0}

    evidence = set(_evidence_ids(root))

    modules_mc = 0
    for doc in _module_docs(root):
        rel = os.path.relpath(doc, root).replace(os.sep, "/")
        try:
            text = open(doc, encoding="utf-8").read()
        except Exception as exc:
            issues.append(f"{rel}: 读取失败 {exc}")
            continue
        parsed = _fence_yaml(text, "machine_contract")
        if "machine_contract" not in parsed:
            continue
        mc = parsed["machine_contract"]
        modules_mc += 1
        declared = mc.get("conformance")
        if declared not in ("L1", "L2", "L3"):
            issues.append(f"{rel}: machine_contract 缺/非法 conformance 声明 {declared!r}")
            continue
        mid = mc.get("id")
        provable = 2 if isinstance(mid, str) and mid in evidence else 1
        order = {"L1": 1, "L2": 2, "L3": 3}
        if order[declared] > provable:
            issues.append(
                f"{rel}: conformance 虚标 {declared} > 可证 L{provable}"
                f"（{mid!r} 不在装配在册证据）"
            )

    # community 协议包
    packages = 0
    for proto in sorted(glob.glob(os.path.join(root, "community", "*", "protocol.yaml"))):
        rel = os.path.relpath(proto, root).replace(os.sep, "/")
        try:
            data = yaml.safe_load(open(proto, encoding="utf-8").read())
        except Exception as exc:
            issues.append(f"{rel}: protocol.yaml 解析失败 {exc}")
            continue
        packages += 1
        pkg = (data or {}).get("package") or {}
        declared = pkg.get("conformance")
        pid = pkg.get("id")
        if declared not in ("L1", "L2", "L3"):
            issues.append(f"{rel}: package 缺/非法 conformance 声明 {declared!r}")
            continue
        reg, _ = _read_json(os.path.join(root, "desktop", "src", "core", "registry.json"))
        reg_ids = {p.get("id") for p in (reg or {}).get("protocols") or []}
        provable = 2 if isinstance(pid, str) and pid in reg_ids else 1
        order = {"L1": 1, "L2": 2, "L3": 3}
        if order[declared] > provable:
            issues.append(f"{rel}: conformance 虚标 {declared} > 可证 L{provable}（包不在 registry protocols[]）")

    # 导出契约面 manifest（L3 = 导出契约门禁锁定面）
    manifest_path = os.path.join(root, "protocol", "export_conformance.json")
    manifest, err = _read_json(manifest_path)
    export_items = 0
    if not isinstance(manifest, dict):
        issues.append(f"protocol/export_conformance.json 缺失/解析失败：{err}")
    else:
        verify_txt = ""
        verify_path = os.path.join(root, "verify.sh")
        if os.path.isfile(verify_path):
            verify_txt = open(verify_path, encoding="utf-8").read()
        for item in manifest.get("items") or []:
            export_items += 1
            if not isinstance(item, dict):
                issues.append("export manifest item 非对象")
                continue
            if item.get("conformance") != "L3":
                issues.append(f"导出面 {item.get('id')}: conformance 应为 L3（导出门禁锁定面）")
            for ev in item.get("evidence") or []:
                if not os.path.isfile(os.path.join(root, ev)):
                    issues.append(f"导出面 {item.get('id')}: 证据文件缺失 {ev}")
            for gate in item.get("gates") or []:
                if gate not in verify_txt:
                    issues.append(f"导出面 {item.get('id')}: 证据门禁 {gate} 不在 verify.sh")

    stats = {
        "modules_mc": modules_mc,
        "packages": packages,
        "export_items": export_items,
    }
    return issues, stats
