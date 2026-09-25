#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""标准目录 · GEO 出口生成器（check38 子扫描 3）。

定位：把 `protocol/standards_catalog.json`（370 条）+ `protocol/standards_binding.json`（1200 绑定）
导出成**生成式引擎可引用**的稳定面。全部是生成物，禁止手写；`--check` 逐字节比对，防漂移。

产物：
- docs/standards/index.md          全量可引用索引（每条 `### <id>` 稳定锚）
- docs/standards/layer-<L>.md      按层切分（data / eng / form / gov / iface）
- docs/standards/answer-cards.md   按问题形态聚合的可引用卡（扩展点 / 分层 / 绑定 / 不可达）
- protocol/geo_export.json         机读紧凑面（避免引擎解析 370 条大 JSON）

用法：python scripts/geo_export.py --write | --check
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Dict, List, Tuple

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CATALOG_REL = "protocol/standards_catalog.json"
BINDING_REL = "protocol/standards_binding.json"
INDEX_REL = "docs/standards/index.md"
CARDS_REL = "docs/standards/answer-cards.md"
MACHINE_REL = "protocol/geo_export.json"
LAYERS = ["data", "eng", "form", "gov", "iface"]
HEAD = ("> 本页由 `python scripts/geo_export.py --write` 生成，禁止手改。"
        "真源：`protocol/standards_catalog.json` + `protocol/standards_binding.json`。")


def _load(root: str) -> Tuple[List[Dict[str, Any]], Dict[str, Any], Dict[str, Dict[str, int]]]:
    cat = json.load(open(os.path.join(root, CATALOG_REL), encoding="utf-8"))
    bind = json.load(open(os.path.join(root, BINDING_REL), encoding="utf-8"))
    counts: Dict[str, Dict[str, int]] = {}
    for pack in bind.get("packs") or []:
        for b in pack.get("bindings") or []:
            main = str(b.get("standard") or "")
            sup = str(b.get("support_standard") or "")
            if main:
                counts.setdefault(main, {"main": 0, "support": 0})["main"] += 1
            if sup:
                counts.setdefault(sup, {"main": 0, "support": 0})["support"] += 1
    return cat.get("standards") or [], cat.get("coverage") or {}, counts


def _line(s: Dict[str, Any], counts: Dict[str, Dict[str, int]]) -> str:
    ev = s.get("evidence") or {}
    reach = "是" if ev.get("reachable") else "否"
    http = ev.get("http_status", "-")
    date = ev.get("probe_date", "-")
    ext = ", ".join(s.get("ext_points") or []) or "—"
    c = counts.get(s["id"]) or {}
    return ("- %s · %s · 层 %s · 可达 %s（%s · %s） · 扩展点 %s · 绑定 主锚 %d / 辅锚 %d · %s"
            % (s.get("title") or s["id"], s.get("body") or "—", s.get("layer") or "—",
               reach, http, date, ext, c.get("main", 0), c.get("support", 0), s.get("url") or "—"))


def _head(title: str, coverage: Dict[str, Any], extra: str = "") -> List[str]:
    lines = ["# %s" % title, "", HEAD, ""]
    lines.append("- 覆盖：标准 **%d** 条 · 本机可达 **%d** · 不可达 **%d** · 机构 **%d** · 依赖边 **%d**"
                 % (coverage.get("standards", 0), coverage.get("reachable", 0),
                    coverage.get("unreachable", 0), coverage.get("bodies", 0),
                    coverage.get("depends_edges", 0)))
    by_layer = coverage.get("by_layer") or {}
    lines.append("- 分层：%s" % " · ".join("%s %s" % (k, by_layer.get(k, 0)) for k in sorted(by_layer)))
    lines.append("- 可达性是**本机实测**（探针日期见每条），不可达条目照实标注、不假装可达。")
    if extra:
        lines.append("- %s" % extra)
    lines.append("")
    return lines


def build(root: str) -> Dict[str, str]:
    standards, coverage, counts = _load(root)
    ordered = sorted(standards, key=lambda s: (str(s.get("layer") or ""), str(s.get("id") or "")))
    outs: Dict[str, str] = {}

    idx = _head("标准目录 · 可引用索引（GEO 出口）", coverage,
                "每条标准一个稳定锚：`#<id>`（如 `%s#onnx`）。" % INDEX_REL)
    for s in ordered:
        idx += ["### `%s`" % s["id"], _line(s, counts), ""]
    outs[INDEX_REL] = "\n".join(idx).rstrip() + "\n"

    for layer in LAYERS:
        rows = [s for s in ordered if str(s.get("layer") or "") == layer]
        body = _head("标准目录 · 层 %s（%d 条）" % (layer, len(rows)), coverage,
                     "本页为 `%s` 的按层切片，锚点与主索引一致。" % INDEX_REL)
        for s in rows:
            body += ["### `%s`" % s["id"], _line(s, counts), ""]
        outs["docs/standards/layer-%s.md" % layer] = "\n".join(body).rstrip() + "\n"

    # 可引用卡（按问题形态聚合）
    cards = _head("标准目录 · 可引用卡（按问题形态）", coverage,
                  "每张卡回答一类问题，可直接被生成式引擎引用；数据源同主索引。")
    top_ext = sorted(standards, key=lambda s: (-len(s.get("ext_points") or []), str(s.get("id"))))[:20]
    cards += ["## 卡 1 · 哪些标准提供扩展点？", "",
              "全 **%d** 条标准均声明扩展点（`ext_points`），扩展点最多的 20 条：" % len(standards), ""]
    cards += ["- `%s` · %s · 扩展点 %d：%s"
              % (s["id"], s.get("title") or "—", len(s.get("ext_points") or []),
                 ", ".join(s.get("ext_points") or [])[:120]) for s in top_ext]
    cards += ["", "## 卡 2 · 各层有哪些标准？", ""]
    by_layer = coverage.get("by_layer") or {}
    for layer in LAYERS:
        cards.append("- **%s** %d 条 → `docs/standards/layer-%s.md`"
                     % (layer, by_layer.get(layer, 0), layer))
    bound_rows = sorted(({"id": k, **v} for k, v in counts.items()),
                        key=lambda r: (-(r["main"] + r["support"]), r["id"]))
    cards += ["", "## 卡 3 · 哪些标准被域包绑定、绑了多少次？", "",
              "绑定总量 **1200**（%d 条不同标准被引用；主锚=口径锚，辅锚=产出承载锚）。绑定最多的 20 条：" % len(counts), ""]
    cards += ["- `%s` · 主锚 %d / 辅锚 %d" % (r["id"], r["main"], r["support"]) for r in bound_rows[:20]]
    unreach = [s for s in standards if not (s.get("evidence") or {}).get("reachable")]
    cards += ["", "## 卡 4 · 哪些标准本机不可达？（诚实披露）", "",
              "共 **%d** 条本机探测未达（不假装可达），逐条如下：" % len(unreach), ""]
    cards += ["- `%s` · %s · HTTP %s · %s"
              % (s["id"], s.get("title") or "—", (s.get("evidence") or {}).get("http_status", "-"),
                 str((s.get("evidence") or {}).get("error") or "")[:80]) for s in unreach]
    outs[CARDS_REL] = "\n".join(cards).rstrip() + "\n"

    machine = {
        "schema": "nf-geo-export/1",
        "note": "生成物；真源 protocol/standards_catalog.json + protocol/standards_binding.json。",
        "coverage": coverage,
        "standards": [
            {"id": s["id"], "title": s.get("title"), "body": s.get("body"),
             "url": s.get("url"), "layer": s.get("layer"), "ext_points": s.get("ext_points") or [],
             "reachable": bool((s.get("evidence") or {}).get("reachable")),
             "http_status": (s.get("evidence") or {}).get("http_status"),
             "probe_date": (s.get("evidence") or {}).get("probe_date"),
             "sha256_sample": (s.get("evidence") or {}).get("sha256_sample"),
             "bound_main": (counts.get(s["id"]) or {}).get("main", 0),
             "bound_support": (counts.get(s["id"]) or {}).get("support", 0)}
            for s in ordered
        ],
    }
    outs[MACHINE_REL] = json.dumps(machine, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    return outs


def write(root: str = ROOT) -> Tuple[List[str], int]:
    outs = build(root)
    for rel, text in outs.items():
        path = os.path.join(root, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="") as fh:
            fh.write(text)
    return [], len(outs)


def check(root: str = ROOT) -> Tuple[List[str], Dict[str, Any]]:
    outs = build(root)
    issues = []
    for rel, text in outs.items():
        path = os.path.join(root, rel)
        if not os.path.isfile(path):
            issues.append("缺生成物 %s（跑 `geo_export.py --write`）" % rel)
            continue
        if open(path, encoding="utf-8").read() != text:
            issues.append("%s 与标准目录不一致（跑 `geo_export.py --write` 重写）" % rel)
    standards, coverage, counts = _load(root)
    ids = {s["id"] for s in standards}
    idx_path = os.path.join(root, INDEX_REL)
    anchored = set()
    if os.path.isfile(idx_path):
        import re
        anchored = set(re.findall(r"^### `([^`]+)`", open(idx_path, encoding="utf-8").read(), re.M))
    if anchored != ids:
        issues.append("索引锚点集合 ≠ 目录 id 集合（缺 %d / 多 %d）"
                      % (len(ids - anchored), len(anchored - ids)))
    stats = {"standards": len(standards), "bound_standards": len(counts),
             "files": len(outs), "coverage": coverage}
    return issues, stats


def scan(root: str = ROOT) -> Tuple[List[str], Dict[str, Any]]:
    """check38 子扫描入口：GEO 出口 ↔ 标准目录一致。"""
    return check(root)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="geo_export", description="标准目录 GEO 出口（生成物，防手改）")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    ap.add_argument("--root", default=ROOT)
    args = ap.parse_args(argv)
    if args.write:
        issues, n = write(args.root)
        print("== GEO 出口已生成 == %d 个文件（%s · docs/standards/* · %s）"
              % (n, INDEX_REL, MACHINE_REL))
    else:
        issues, stats = check(args.root)
        print("== GEO 出口自检 ==  标准 %(standards)d 条 · 被绑定 %(bound_standards)d 条 · 生成物 %(files)d 件"
              % stats)
    for i in issues:
        print("  [FAIL] %s" % i, file=sys.stderr)
    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
