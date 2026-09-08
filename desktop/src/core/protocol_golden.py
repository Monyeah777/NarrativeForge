"""43 A4 —— 协议生成物同仓 golden（schema 定义 → 可复现产物 + 双源回归）。

生成物 = protocol/generated/（提交入仓）：
- idl_report.json  校验摘要（schema 清单 + 全量件覆盖 + 契约/管线/协议/台账行）
- idl_summary.md   人读摘要（由同一 canonical 数据渲染，逐字节可复现）

一致性纪律：任何 schema/协议件变更后须重跑生成并同步入仓；
verify check31 断言仓库内生成物 == 当前实时重算（schema↔生成物双源一致），
不一致即 FAIL（红 = 生成物过期），提示用 write_golden 刷新。
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Tuple

from core import conformance_scan as _csc
from core import schema_lint as _sl

GENERATED_DIR = os.path.join("protocol", "generated")
REPORT_NAME = "idl_report.json"
SUMMARY_NAME = "idl_summary.md"


def _md_row(cells: List[str]) -> str:
    return "| " + " | ".join(str(c) for c in cells) + " |"


def collect(root: str) -> Dict[str, Any]:
    """收集生成物 canonical 数据（全部来自 schema/协议件实时扫描，确定性排序）。"""
    sl_issues, sl_stats = _sl.scan(root)
    _, schemas = _sl.check_schema_files(root)
    schema_ids = sorted(s.get("$id", "") for s in schemas if s.get("$id"))

    evidence = sorted(_csc._evidence_ids(root))
    contracts: List[Dict[str, Any]] = []
    for doc in _csc._module_docs(root):
        rel = os.path.relpath(doc, root).replace(os.sep, "/")
        try:
            with open(doc, encoding="utf-8") as fh:
                text = fh.read()
        except Exception:
            continue
        parsed = _csc._fence_yaml(text, "machine_contract")
        mc = parsed.get("machine_contract") if isinstance(parsed, dict) else None
        if not isinstance(mc, dict):
            continue
        contracts.append({
            "id": mc.get("id"),
            "name": mc.get("name"),
            "layer": mc.get("layer"),
            "conformance": mc.get("conformance"),
            "source": rel,
        })
    contracts.sort(key=lambda x: (str(x["id"]), str(x["source"])))

    pipelines = sorted(os.path.basename(p) for p in _sl.discover(root)["pipeline_docs"])
    packages = sorted(
        os.path.relpath(p, root).replace(os.sep, "/")
        for p in _sl.discover(root)["protocol_files"]
    )
    reg, _ = _sl._read_json(os.path.join(root, "desktop", "src", "core", "registry.json"))
    registry_modules: List[Dict[str, Any]] = []
    for m in (reg or {}).get("modules") or []:
        registry_modules.append({
            "id": m.get("id"),
            "category": m.get("category"),
            "source": m.get("source"),
            "layers": [mo.get("layer") for mo in (m.get("mounts") or [])],
        })
    registry_modules.sort(key=lambda x: str(x["id"]))
    prov, _ = _sl._read_json(os.path.join(root, "05_资产库", "provenance.json"))
    asset_keys = sorted(a.get("key") for a in (prov or {}).get("assets") or [])

    return {
        "generated_by": "43 A4 protocol_golden（schema 定义 → 校验摘要，确定性渲染）",
        "schema_ids": schema_ids,
        "coverage": {
            "module_docs": sl_stats["module_docs"],
            "contract_covered": sl_stats["contract_covered"],
            "pipelines": sl_stats["pipelines"],
            "protocols": sl_stats["protocols"],
            "asset_entries": sl_stats["asset_entries"],
            "schema_issues": len(sl_issues),
        },
        "evidence_ids": evidence,
        "registry_modules": registry_modules,
        "contracts": contracts,
        "pipeline_files": pipelines,
        "protocol_files": packages,
        "asset_keys": asset_keys,
    }


def render_json(data: Dict[str, Any]) -> bytes:
    return (json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def render_markdown(data: Dict[str, Any]) -> bytes:
    lines: List[str] = [
        "# protocol/generated · 协议层 IDL 校验摘要（43 A4 golden 产物）",
        "",
        "> 本文件由 `desktop/src/core/protocol_golden.py` 确定性渲染；",
        "> 校验摘要与 schema/协议件双源一致由 verify check31 断言（过期即红，重跑刷新）。",
        "",
        "## 覆盖",
        _md_row(["schema", "模块文档", "机读契约", "管线", "协议包", "台账条目"]),
        _md_row(["-", "-", "-", "-", "-", "-"]),
        _md_row([
            len(data["schema_ids"]),
            data["coverage"]["module_docs"],
            data["coverage"]["contract_covered"],
            data["coverage"]["pipelines"],
            data["coverage"]["protocols"],
            data["coverage"]["asset_entries"],
        ]),
        "",
        "## schema 定义",
    ]
    lines += ["- " + sid for sid in data["schema_ids"]]
    lines += ["", "## 装配在册证据（id 集）", "- " + ", ".join(data["evidence_ids"])]
    lines += ["", "## 机读契约模块", _md_row(["id", "conformance", "layer", "source"])]
    lines += [_md_row(["-", "-", "-", "-"])]
    for c in data["contracts"]:
        lines.append(_md_row([c["id"], c["conformance"], c["layer"], c["source"]]))
    lines += ["", "## 管线", "- " + ", ".join(data["pipeline_files"])]
    lines += ["", "## 协议包", "- " + ", ".join(data["protocol_files"])]
    lines += ["", "## 资产台账键", "- " + ", ".join(data["asset_keys"]), ""]
    return ("\n".join(lines) + "\n").encode("utf-8")


def write_golden(root: str) -> List[str]:
    """重算并写盘 protocol/generated/（返回写盘相对路径）。"""
    data = collect(root)
    out_dir = os.path.join(root, GENERATED_DIR)
    os.makedirs(out_dir, exist_ok=True)
    written: List[str] = []
    for name, blob in ((REPORT_NAME, render_json(data)), (SUMMARY_NAME, render_markdown(data))):
        path = os.path.join(out_dir, name)
        with open(path, "wb") as fh:
            fh.write(blob)
        written.append(os.path.relpath(path, root).replace(os.sep, "/"))
    return written


def verify_golden(root: str) -> Tuple[List[str], Dict[str, int]]:
    """check31：仓库内生成物 == 实时重算（schema↔生成物双源一致）。"""
    issues: List[str] = []
    data = collect(root)
    expected = render_json(data)
    report_path = os.path.join(root, GENERATED_DIR, REPORT_NAME)
    if not os.path.isfile(report_path):
        issues.append(f"{GENERATED_DIR}/{REPORT_NAME} 缺失（生成物未入仓）")
    else:
        with open(report_path, "rb") as fh:
            actual = fh.read()
        if actual != expected:
            issues.append(
                f"{GENERATED_DIR}/{REPORT_NAME} 过期：与当前 schema/协议件不一致——"
                "请用 protocol_golden.write_golden 刷新并随变更一并提交"
            )
    return issues, {"report_bytes": len(expected), "schema_ids": len(data["schema_ids"])}


if __name__ == "__main__":  # pragma: no cover - 手动重跑入口
    import sys

    root = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    )
    for rel in write_golden(root):
        print("written:", rel)
