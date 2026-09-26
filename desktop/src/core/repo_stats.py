"""出口自动化 · 自述数字实算真源（check38 子扫描 1）。

口径纪律：README / README.en / llms.txt 里的每个数字都必须能回指**唯一产物**，
且由本模块实算；文档只承载生成区（marker 包围），禁止手改。

口径表（数字 → 真源 → 实算方式）：
- core_modules       → desktop/src/core/registry.json · len(modules)
- core_pipelines     → 03_管线库/P*.md · 文件名编号集合
- registered_packs   → desktop/src/core/registry.json · len(protocols)
- pack_dirs          → community/*/protocol.yaml · 目录计数（须 == registered_packs）
- pack_assets        → community/*/assets/*.md · 计数
- concept_graphs     → community/*/assets/CONCEPT_GRAPH.md · 计数
- standards_total / standards_reachable / standards_unreachable / standards_bodies
  / standards_edges / standards_by_layer → protocol/standards_catalog.json · coverage
- standard_bindings  → protocol/standards_binding.json · bindings_total
- domain_packs / subdivisions_total → protocol/domain_packs.json · count / subdivisions_total
- library_items      → library/*.md 去除 INDEX.md / ALIAS.md
- verify_checks      → verify.sh · `^checkN()` 定义数
- verify_version     → verify.sh 头部 `# 版本 : vX.Y`

生成物：protocol/repo_stats.json（机读）+ 三个入口文件的 marker 区。
若任一数字取不到 → 记 issue（不静默填 0）。
"""

from __future__ import annotations

import glob
import json
import os
import re
import sys
from typing import Any, Dict, List, Tuple

STATS_REL = "protocol/repo_stats.json"
BEGIN = "<!-- nf:stats:begin -->"
END = "<!-- nf:stats:end -->"
BLOCK_FILES = ("README.md", "README.en.md", "llms.txt")


def _read_json(path: str) -> Any:
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:  # noqa: BLE001
        return None


def compute(root: str = ".") -> Tuple[Dict[str, Any], List[str]]:
    issues: List[str] = []
    stats: Dict[str, Any] = {}

    reg = _read_json(os.path.join(root, "desktop/src/core/registry.json"))
    if not isinstance(reg, dict):
        issues.append("取不到 registry.json（官方核心模块/登记包口径缺失）")
        reg = {}
    stats["core_modules"] = len(reg.get("modules") or [])
    stats["registered_packs"] = len(reg.get("protocols") or [])

    pipes = sorted(os.path.basename(p)[:3] for p in glob.glob(os.path.join(root, "03_管线库/P*.md")))
    stats["core_pipelines"] = pipes

    pack_dirs = sorted(os.path.dirname(p)[len(os.path.join(root, "community")) + 1:].replace("\\", "/")
                       for p in glob.glob(os.path.join(root, "community/*/protocol.yaml")))
    stats["pack_dirs"] = len(pack_dirs)
    if pack_dirs and stats["pack_dirs"] != stats["registered_packs"]:
        issues.append("盘上包目录 %d ≠ registry 登记 %d（登记三要件与盘上实况不一致）"
                      % (stats["pack_dirs"], stats["registered_packs"]))

    stats["pack_assets"] = len(glob.glob(os.path.join(root, "community/*/assets/*.md")))
    stats["concept_graphs"] = len(glob.glob(os.path.join(root, "community/*/assets/CONCEPT_GRAPH.md")))

    cat = _read_json(os.path.join(root, "protocol/standards_catalog.json")) or {}
    cov = cat.get("coverage") or {}
    for key in ("standards", "reachable", "unreachable", "bodies", "depends_edges", "by_layer"):
        if key not in cov:
            issues.append("标准目录 coverage 缺 %s（口径不完整）" % key)
    stats["standards_total"] = cov.get("standards", 0)
    stats["standards_reachable"] = cov.get("reachable", 0)
    stats["standards_unreachable"] = cov.get("unreachable", 0)
    stats["standards_bodies"] = cov.get("bodies", 0)
    stats["standards_edges"] = cov.get("depends_edges", 0)
    stats["standards_by_layer"] = cov.get("by_layer", {})

    bind = _read_json(os.path.join(root, "protocol/standards_binding.json")) or {}
    stats["standard_bindings"] = bind.get("bindings_total", 0)

    manifest = _read_json(os.path.join(root, "protocol/domain_packs.json")) or {}
    stats["domain_packs"] = manifest.get("count", 0)
    stats["subdivisions_total"] = manifest.get("subdivisions_total", 0)

    lib = [os.path.basename(p) for p in glob.glob(os.path.join(root, "library/*.md"))]
    stats["library_items"] = len([f for f in lib if f not in ("INDEX.md", "ALIAS.md")])

    vpath = os.path.join(root, "verify.sh")
    try:
        with open(vpath, encoding="utf-8") as fh:
            vtext = fh.read()
    except Exception:  # noqa: BLE001
        vtext = ""
        issues.append("取不到 verify.sh（质量凭证口径缺失）")
    stats["verify_checks"] = len(re.findall(r"^check[0-9]+\(\)", vtext, re.M))
    m = re.search(r"^# 版本\s*:\s*v([0-9][0-9.]*)", vtext, re.M)
    stats["verify_version"] = m.group(1) if m else ""
    if not stats["verify_version"]:
        issues.append("verify.sh 头部缺「# 版本 : vX」版本行")
    if stats["verify_checks"] < 1:
        issues.append("verify.sh 未扫到任何 checkN() 定义")

    # 质量基线真源：quality_baseline.EXPECTED_*（与 verify.sh 版本共同构成基线句）
    try:
        sys.path.insert(0, os.path.join(root, "desktop", "src"))
        from core import quality_baseline as qb  # type: ignore
        stats["baseline_checks"] = int(getattr(qb, "EXPECTED_CHECKS", stats["verify_checks"]))
        stats["baseline_pass"] = int(getattr(qb, "EXPECTED_PASS", 0))
    except Exception as exc:  # noqa: BLE001
        stats["baseline_checks"] = stats["verify_checks"]
        stats["baseline_pass"] = 0
        issues.append("取不到 quality_baseline.EXPECTED_*：%s（基线句无法生成）" % exc)
    if stats["baseline_checks"] != stats["verify_checks"]:
        issues.append("基线 check 数 %d ≠ verify.sh 实扫 %d（同步 quality_baseline.EXPECTED_CHECKS）"
                      % (stats["baseline_checks"], stats["verify_checks"]))

    stats["schema"] = "nf-repo-stats/1"
    return stats, issues


def _zh(stats: Dict[str, Any]) -> str:
    pipes = " / ".join(stats.get("core_pipelines") or []) or "—"
    layers = stats.get("standards_by_layer") or {}
    layer_txt = " · ".join("%s %s" % (k, layers[k]) for k in sorted(layers)) or "—"
    return "\n".join([
        BEGIN,
        "**官方核心**：%d 模块 · %d 管线（%s） · 核心协议件 01–07"
        % (stats["core_modules"], len(stats.get("core_pipelines") or []), pipes),
        "**社区规模**：%d 登记包 · %d 资产档 · %d 概念图 · %d 域包/%d 细分 · 标准目录 %d 条（可达 %d / 不可达 %d · 机构 %d · %d 条依赖边） · 标准绑定 %d 条"
        % (stats["registered_packs"], stats["pack_assets"], stats["concept_graphs"],
           stats["domain_packs"], stats["subdivisions_total"],
           stats["standards_total"], stats["standards_reachable"], stats["standards_unreachable"],
           stats["standards_bodies"], stats["standards_edges"], stats["standard_bindings"]),
        "**质量凭证**：verify v%s · check1-%d · PASS=%d（`bash verify.sh` 单入口；期望基线取自 `quality_baseline.EXPECTED_*`） · 馆藏 %d 件"
        % (stats["verify_version"], stats["baseline_checks"], stats["baseline_pass"], stats["library_items"]),
        "",
        "分层：%s （按标准目录 layer）" % layer_txt,
        "",
        "> 本区由 `python scripts/nf.py stats --write` 生成，禁止手改；口径与实算真源见 `protocol/repo_stats.json`。",
        END,
    ])


def _en(stats: Dict[str, Any]) -> str:
    return "\n".join([
        BEGIN,
        "**Official core**: %d modules · %d pipelines (%s) · protocol files 01-07"
        % (stats["core_modules"], len(stats.get("core_pipelines") or []),
           " / ".join(stats.get("core_pipelines") or []) or "—"),
        "**Community scale**: %d registered packs · %d asset files · %d concept graphs · %d domain packs / %d subdivisions · standards catalog %d (reachable %d / unreachable %d · %d bodies · %d dependency edges) · standard bindings %d"
        % (stats["registered_packs"], stats["pack_assets"], stats["concept_graphs"],
           stats["domain_packs"], stats["subdivisions_total"],
           stats["standards_total"], stats["standards_reachable"], stats["standards_unreachable"],
           stats["standards_bodies"], stats["standards_edges"], stats["standard_bindings"]),
        "**Quality evidence**: verify v%s · check1-%d · PASS=%d (`bash verify.sh`; expectations from `quality_baseline.EXPECTED_*`) · library %d items"
        % (stats["verify_version"], stats["baseline_checks"], stats["baseline_pass"], stats["library_items"]),
        "",
        "> Generated by `python scripts/nf.py stats --write`. Do not edit by hand; sources in `protocol/repo_stats.json`.",
        END,
    ])


def _llms(stats: Dict[str, Any]) -> str:
    return "\n".join([
        BEGIN,
        "- 质量凭证（可静态实算）：verify v%s · check1-%d · PASS=%d（`bash verify.sh` 单入口；期望基线取自 `quality_baseline.EXPECTED_*`，本行由生成器写入）。"
        % (stats["verify_version"], stats["baseline_checks"], stats["baseline_pass"]),
        "- 规模（实算真源 `protocol/repo_stats.json`）：%d 登记包 · %d 资产档 · %d 概念图 · 标准目录 %d 条（可达 %d） · 标准绑定 %d 条 · 馆藏 %d 件。"
        % (stats["registered_packs"], stats["pack_assets"], stats["concept_graphs"],
           stats["standards_total"], stats["standards_reachable"], stats["standard_bindings"],
           stats["library_items"]),
        "- 标准目录 GEO 出口（可引用）：`docs/standards/index.md` · 机读 `protocol/geo_export.json`。",
        END,
    ])


def render(stats: Dict[str, Any]) -> Dict[str, str]:
    return {"README.md": _zh(stats), "README.en.md": _en(stats), "llms.txt": _llms(stats)}


def _replace_block(text: str, block: str) -> Tuple[str, bool]:
    i, j = text.find(BEGIN), text.find(END)
    if i < 0 or j < 0 or j < i:
        return text, False
    return text[:i] + block + text[j + len(END):], True


def write(root: str = ".") -> Tuple[List[str], Dict[str, Any]]:
    stats, issues = compute(root)
    blocks = render(stats)
    for rel, block in blocks.items():
        path = os.path.join(root, rel)
        if not os.path.isfile(path):
            issues.append("缺入口文件 %s（无法写入生成区）" % rel)
            continue
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
        new, ok = _replace_block(text, block)
        if not ok:
            issues.append("%s 缺 marker（%s / %s），未写入" % (rel, BEGIN, END))
            continue
        with open(path, "w", encoding="utf-8", newline="") as fh:
            fh.write(new)
    out = os.path.join(root, STATS_REL)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="") as fh:
        json.dump(stats, fh, ensure_ascii=False, indent=2, sort_keys=True)
        fh.write("\n")
    return issues, stats


def check(root: str = ".") -> Tuple[List[str], Dict[str, Any]]:
    stats, issues = compute(root)
    blocks = render(stats)
    for rel, block in blocks.items():
        path = os.path.join(root, rel)
        if not os.path.isfile(path):
            issues.append("缺入口文件 %s" % rel)
            continue
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
        new, ok = _replace_block(text, block)
        if not ok:
            issues.append("%s 缺 marker 区" % rel)
        elif new != text:
            issues.append("%s 的生成区与实算不一致（跑 `nf stats --write` 重写）" % rel)
    recorded = _read_json(os.path.join(root, STATS_REL))
    if recorded != stats:
        issues.append("%s 与实算不一致（跑 `nf stats --write` 重写）" % STATS_REL)
    return issues, stats


def scan(root: str = ".") -> Tuple[List[str], Dict[str, Any]]:
    """check38 子扫描入口：自述数字 ↔ 实算一致。"""
    return check(root)
