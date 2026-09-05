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

    reg = sub.add_parser("register",
                         help="协议登记本地助手（B3-B：protocol.yaml → registry protocols[]）")
    reg.add_argument("pkg_dir", help="包目录（如 community/校园西幻轻混组合包）")
    reg.add_argument("--check", dest="mode", action="store_const", const="check",
                     help="只校验三要件 + 打印投影 diff（缺省，不写盘）")
    reg.add_argument("--apply", dest="mode", action="store_const", const="apply",
                     help="校验全过后合并写 registry.json protocols[]（只增不删）")
    reg.add_argument("--registry", default=None,
                     help="registry.json 路径（缺省 = desktop/src/core/registry.json）")
    reg.set_defaults(mode="check")

    mkt = sub.add_parser("market",
                         help="市场协议查询（B4：依赖闭包 + 挂载冲突预检）")
    mkt.add_argument("pkg_dir", help="包目录（如 community/校园西幻轻混组合包）")
    mkt.add_argument("--registry", default=None,
                     help="registry.json 路径（缺省 = desktop/src/core/registry.json）")
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


def _cmd_register(args) -> int:
    """nf register：本地登记助手（B3-B）。--check 只读 / --apply 合并写。"""
    from core.protocol_projection import project_entry
    from core.registry_sync import check_registerable, merge_protocols

    reg_path = args.registry or os.path.join(ROOT, "desktop", "src", "core", "registry.json")
    doc_path = os.path.join(ROOT, "02_联动注册表.md")

    # 三要件校验（② 02 在册；① protocol.yaml 由 check_registerable 内置）
    with open(doc_path, encoding="utf-8") as f:
        doc = f.read()
    issues = check_registerable(args.pkg_dir, doc)
    if issues:
        for msg in issues:
            print(f"  [拒绝] {msg}", file=sys.stderr)
        print("✗ 校验未通过——须先满足登记三要件（02 §8.3）；详见 02 §9.2 同步纪律", file=sys.stderr)
        return 2

    entry = project_entry(args.pkg_dir)

    import json
    with open(reg_path, encoding="utf-8") as f:
        reg = json.load(f)
    cur = reg.get("protocols")
    if not isinstance(cur, list):
        print("✗ registry protocols[] 缺失或非列表", file=sys.stderr)
        return 2

    # 键序无关比较：merge 结果与现状在规范化（sorted keys）意义上相等 → 无实质变化
    def _canon(prots):
        return sorted(json.dumps(p, sort_keys=True, ensure_ascii=False) for p in prots)

    existing = next((p for p in cur if p["id"] == entry["id"]), None)
    merged = merge_protocols(cur, [entry])
    changed = _canon(merged) != _canon(cur)
    print(f"== nf register {entry['id']} [{args.mode}] ==")
    if not changed:
        print("  投影与 registry 现状一致，无更新（幂等，不写盘）")
        if args.mode == "apply":
            return 0
        return 0
    print("  将更新 protocols[]：%s" % ("新增" if existing is None else "覆盖"))
    diff_keys = sorted(k for k in entry if not existing or existing.get(k) != entry.get(k))
    if diff_keys:
        print("  差异字段：%s" % ", ".join(diff_keys))

    if args.mode != "apply":
        print("  [--check] 未写盘（--apply 才合并写入）")
        return 0

    reg["protocols"] = merged
    with open(reg_path, "w", encoding="utf-8") as f:
        json.dump(reg, f, ensure_ascii=False, indent=2)
    print(f"  ✓ 已写入 {reg_path}（protocols[] {len(cur)} → {len(merged)} 条，只增不删）")
    print("  下一步：跑 `bash verify.sh` 由 check14 ⑦ 元素级断言自证")
    return 0


def _cmd_market(args) -> int:
    """nf market：依赖闭包 + 挂载冲突预检（B4 CLI 先行；信息查询，冲突不阻断）。"""
    import json
    from core.market_analyzer import conflicts, dependencies
    from core.registry_sync import check_registerable

    reg_path = args.registry or os.path.join(ROOT, "desktop", "src", "core", "registry.json")
    doc_path = os.path.join(ROOT, "02_联动注册表.md")

    pkg_id = os.path.basename(args.pkg_dir.rstrip("/\\"))

    with open(reg_path, encoding="utf-8") as f:
        reg = json.load(f)
    prots = {p["id"]: p for p in reg.get("protocols", [])}
    with open(doc_path, encoding="utf-8") as f:
        doc = f.read()

    # 登记状态（复用 registry_sync 三要件校验；issue 即未就绪提示，不阻断查询）
    reg_issues = check_registerable(args.pkg_dir, doc)
    print(f"== nf market {pkg_id} ==")
    print("  登记状态: %s" % ("在册（02 §8 + registry protocols[]）"
                              if not reg_issues else "; ".join(reg_issues)))
    if pkg_id not in prots:
        print("  registry protocols[] 无条目——无 references 可查")
        return 2 if reg_issues else 0

    # 加载各包 protocol.yaml 内容（data 供 dependencies/conflicts 用）
    import glob
    import yaml
    data = {}
    for pf in sorted(glob.glob(os.path.join(ROOT, "community", "*", "protocol.yaml"))):
        try:
            with open(pf, encoding="utf-8") as f:
                raw = yaml.safe_load(f)
            data[raw["package"]["id"]] = raw
        except Exception:
            continue

    seen, dep_issues = dependencies(pkg_id, prots, data)
    cfl = conflicts(pkg_id, prots, data)
    print("  依赖闭包: %s" % (", ".join(sorted(seen)) if seen else "无跨包引用"))
    for i in dep_issues:
        print(f"  [依赖] {i}")
    if cfl:
        for i in cfl:
            print(f"  [冲突] {i}")
    else:
        print("  挂载冲突: 无")
    return 0


def main(argv=None) -> int:
    args = _build_parser().parse_args(argv)
    if args.cmd == "register":
        return _cmd_register(args)
    if args.cmd == "market":
        return _cmd_market(args)
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
