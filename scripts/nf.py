#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""NarrativeForge 全链管道 CLI（v2.1.0 B2：retrieve→compose→gate→export 单命令）。

用法：
  python scripts/nf.py run --pipeline <P04管线.md> \
      --modules 通用类:M00,轻混类:M91,轻混类:M92,通用类:M80 \
      [--store <dir>] [--seed] [--fmt ccv3|skill] [--dest <out>] \
      [--no-include-refs] [--force-export]

- 全链 = pipe()：模块选择 → compose（E3 references 并入）→ render_ir
  → quality_gate（三态）→ export（exporter._REGISTRY）。
- --seed：把 04_模块库 + community 组合包模块装载进临时 store（演示/自测用，
  等同 e2e 前置）；缺省要求 --store 指向已含所选模块的工作区。
- 打印 GateResult 摘要（PASS/WARN/FAIL）+ 产物路径；FAIL 且非 --force-export
  → exit 1（CLI 层门禁镜像 verify 铁律）。
- 产物×适配矩阵：skill 拒 narrative（适配器内拒出，warnings 带说明）——
  CLI 原样透传 warnings。
"""
import argparse
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "desktop", "src"))


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="nf", description="NarrativeForge 全链管道（B2：retrieve→compose→gate→export）")
    sub = p.add_subparsers(dest="cmd", required=True)

    run = sub.add_parser("run", help="跑全链管道：模块选择→装配→质检→导出")
    run.add_argument("--pipeline", required=True,
                     help="管线 md 文件路径（如 community/校园西幻轻混组合包/pipelines/P04_轻混装配流管线.md）")
    run.add_argument("--modules", required=True,
                     help="参与装配的模块 full_id，逗号分隔（如 通用类:M00,轻混类:M91）")
    run.add_argument("--store", default=None,
                     help="Store 工作区目录（缺省=临时，配合 --seed）")
    run.add_argument("--seed", action="store_true",
                     help="把 04_模块库官方核心 + community 组合包装载进 store（演示/自测）")
    run.add_argument("--fmt", default="ccv3",
                     choices=["ccv3", "skill", "agents", "claude", "mcp"],
                     help="导出格式（exporter 注册表：ccv3/skill/agents/claude/mcp）")
    run.add_argument("--dest", default=None, help="导出目录（缺省=store 根）")
    run.add_argument("--no-include-refs", action="store_true",
                     help="不并入 E3 references 跨包模块（默认并入）")
    run.add_argument("--force-export", action="store_true",
                     help="质量门 FAIL 也导出（诊断用；ok 仍 False）")
    return p


def _seed_store(store):
    """装载官方核心 + 轻混组合包（等同 e2e 前置）。返回统计 dict。"""
    import glob
    from pathlib import Path
    from core.parser import parse_module
    stats = {"core": 0, "combo": 0}
    for f in sorted(glob.glob(os.path.join(ROOT, "04_模块库", "*", "*.md"))):
        try:
            store.save_module(parse_module(Path(f).read_text(encoding="utf-8")))
            stats["core"] += 1
        except Exception:
            continue
    for f in sorted(glob.glob(os.path.join(ROOT, "community",
                                           "校园西幻轻混组合包", "modules", "*.md"))):
        try:
            store.save_module(parse_module(Path(f).read_text(encoding="utf-8")))
            stats["combo"] += 1
        except Exception:
            continue
    return stats


def main(argv=None) -> int:
    args = _build_parser().parse_args(argv)
    if args.cmd != "run":
        _build_parser().print_help()
        return 2

    from core.pipeline import pipe
    from core.pipeline_loader import load_pipeline_file
    from core.storage import Store

    pipeline = load_pipeline_file(args.pipeline)
    if pipeline is None:
        print(f"✗ 管线解析失败：{args.pipeline}", file=sys.stderr)
        return 2

    store = Store(home=args.store) if args.store else Store()
    if args.seed:
        stats = _seed_store(store)
        print(f"  seed 装载：官方核心 {stats['core']} 件"
              f" + 轻混组合包 {stats['combo']} 件 → {store.home}")
    else:
        print(f"  store：{store.home}")

    selected = [m.strip() for m in args.modules.split(",") if m.strip()]
    dest = args.dest
    r = pipe(store, pipeline, selected,
             include_references=not args.no_include_refs,
             fmt=args.fmt, dest_dir=dest,
             fail_on_gate=not args.force_export)

    print(f"\n== 质量门 ==\n  PASS {r.gate.n_pass} · WARN {r.gate.n_warn}"
          f" · FAIL {r.gate.n_fail}" + ("（可产出）" if r.ok else "（存在 FAIL）"))
    # B1 可解释化：逐条含修复建议（quality_gate 报告样式，warn/fail 都 actionable）
    for issue in r.gate.issues:
        if issue.level in ("fail", "warn"):
            print(f"  [{issue.level.upper()}] {issue.message}")
            if issue.suggestion:
                print(f"      建议：{issue.suggestion}")
    for w in r.warnings:
        print(f"  [INFO] {w}")
    if r.export is not None:
        print("\n== 导出 ==")
        if r.export.files:
            for f in r.export.files:
                print(f"  ✓ {f}")
        if r.export.warnings:
            for w in r.export.warnings:
                print(f"  [导出] {w}")
    if not r.ok:
        print("\n✗ 质量门 FAIL（可信任度不变量）"
              + ("；已按 --force-export 导出诊断产物" if args.force_export
                 else "——修复装配后重跑或加 --force-export 看坏产物"), file=sys.stderr)
        return 1
    print("\n★ 全链管道 PASSED ✓")
    return 0


if __name__ == "__main__":
    sys.exit(main())
