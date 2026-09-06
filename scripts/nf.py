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
    run.add_argument("--doc-semantics", default=None,
                     choices=["project_rules", "skill"],
                     help="显式声明装配产物语义（v2.3.0 A3：project_rules → AGENTS/CLAUDE 出口；skill → SKILL）——不传则回退 classify 启发式")
    run.add_argument("--dest", default=None, help="导出目录（缺省=store 根）")
    run.add_argument("--variant-add", default="",
                     help="变体增量模块 full_id（逗号分隔，v2.3.0 B2：经 apply_variant 并入 selected）")
    run.add_argument("--variant-remove", default="",
                     help="变体移除模块 full_id（逗号分隔，从 selected 剔除；与 --variant-add 同用时 remove 优先）")
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

    whr = sub.add_parser("who-refers",
                         help="引用反查（A2：谁引用了某模块，遍历 registry references）")
    whr.add_argument("module_id", help="模块 id（如 M91 或 情感:M55）")
    whr.add_argument("--registry", default=None,
                     help="registry.json 路径（缺省 = desktop/src/core/registry.json）")

    imp = sub.add_parser("impact",
                         help="变更影响面预检（A4 前置：拟删除 module/protocol 前查破坏性影响）")
    imp.add_argument("target", help="目标（protocol id 如 校园情感领域包，或 module id 如 M55 / 情感:M55）")
    imp.add_argument("--check", dest="mode", action="store_const", const="check",
                     help="门禁模式：破坏性变更（有引用方/官方在册）exit 1，无破坏 exit 0")
    imp.add_argument("--registry", default=None,
                     help="registry.json 路径（缺省 = desktop/src/core/registry.json）")

    ren = sub.add_parser("rename",
                         help="模块改名引用重链（A5：references 中引用该模块的条目批量更新）")
    ren.add_argument("old_id", help="旧模块 id（如 M55 或 情感:M55）")
    ren.add_argument("new_id", help="新模块 id（如 M99 或 情感:M99）")
    ren.add_argument("--check", dest="mode", action="store_const", const="check",
                     help="只列受影响引用清单不写盘（缺省）")
    ren.add_argument("--apply", dest="mode", action="store_const", const="apply",
                     help="批量重链 references 后合并写 registry protocols[]（只改引用不改其它）")
    ren.add_argument("--registry", default=None,
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
    from core.market_analyzer import conflicts, dependencies, grades_of_package
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
    # A6 质量分级徽章（v2.4.0）：官方核心/社区/实验
    grades = grades_of_package(prots, pkg_id)
    if grades:
        _badge = {"official": "🏛官方", "community": "🌐社区", "experimental": "🧪实验"}
        badge_line = ", ".join(f"{m}({_badge[g]})" for m, g in grades.items())
        print(f"  分级徽章: {badge_line}")
    print("  依赖闭包: %s" % (", ".join(sorted(seen)) if seen else "无跨包引用"))
    for i in dep_issues:
        print(f"  [依赖] {i}")
    if cfl:
        for i in cfl:
            print(f"  [冲突] {i}")
    else:
        print("  挂载冲突: 无")
    return 0


def _cmd_who_refers(args) -> int:
    """nf who-refers <module_id>：谁在 references 中引用了该模块（A2 反查）。"""
    from core.retriever import referenced_by

    reg_path = args.registry or os.path.join(ROOT, "desktop", "src", "core", "registry.json")
    refs = referenced_by(args.module_id, path=reg_path)
    print(f"== 谁引用了 {args.module_id} ==")
    if not refs:
        print("  无（registry protocols[].references 中无引用）")
        return 0
    for r in refs:
        ro = "只读" if r.get("asset_readonly") else ""
        print(f"  {r['referrer']} → {r['source_package']}.{r['module_id']} {ro}")
    return 0


def _cmd_impact(args) -> int:
    """nf impact <target>：拟删除目标（module/protocol）的破坏性影响预检（A4 前置）。

    --check 门禁模式：破坏性变更（module 被引用/官方在册，或整包删除有引用方）
    exit 1——镜像 verify 铁律，供变更前门禁接线。
    """
    from core.impact_check import impact_of_change
    from core.registry_loader import load_registry

    reg_path = args.registry or os.path.join(ROOT, "desktop", "src", "core", "registry.json")
    reg = load_registry(reg_path)
    im = impact_of_change(reg, args.target)
    print(f"== 删除影响面预检: {args.target} ==")
    if im.get("error"):
        print(f"  [拒绝] {im['error']}")
        return 2

    if "module_id" in im:                     # module 级
        refs = im["referenced_by"]
        print(f"  类型: module（官方在册 {im['in_official_core'] or '无'} · "
              f"属包 {im['in_packages'] or '无'}）")
        if not refs and not im["in_official_core"]:
            print("  无破坏性影响（无引用方且非官方核心——可安全移除）")
            return 0
        for r in refs:
            ro = "只读" if r.get("asset_readonly") else ""
            print(f"  破坏性: 被 {r['protocol']} 引用（引用声明源 {r['source_package']}"
                  f"，asset_readonly {ro or 'false'}）")
        if im["in_official_core"]:
            print(f"  破坏性: 官方核心在册 {im['in_official_core']}（删官方核心 = 协议事故）")
        return 1 if args.mode == "check" else 0
    # protocol 级（整包删除）
    refs = im["referenced_by_packages"]
    print(f"  类型: protocol 整包（module_ids {im['module_ids'] or '无'}）")
    if not refs:
        print("  无破坏性影响（无其它包引用本包模块——可安全移除，自身 references 随之消失）")
        return 0
    for r in refs:
        print(f"  破坏性: 被 {r['protocol']} 引用（引用声明源 {r['source_package']}）")
    return 1 if args.mode == "check" else 0


def _cmd_rename(args) -> int:
    """nf rename <old> <new>：模块改名引用重链（A5 变更助手）。

    --check（缺省）只列受影响引用；--apply 批量重链 references[].module_id 后
    合并写 registry protocols[]（只改引用目标，不动其它字段，V1 只增不删语义）。
    """
    import json
    from core.impact_check import rename_module_plan
    from core.registry_loader import load_registry

    reg_path = args.registry or os.path.join(ROOT, "desktop", "src", "core", "registry.json")
    reg = load_registry(reg_path)
    plan = rename_module_plan(reg, args.old_id, args.new_id)
    print(f"== 改名引用重链: {args.old_id} → {args.new_id} ==")
    if not plan["affected"]:
        print("  无引用方（registry references 中无引用该模块——安全改名，无需重链）")
        return 0
    for a in plan["affected"]:
        print(f"  重链: {a['protocol']} references {a['old_module_id']} → "
              f"{a['new_module_id']}（源 {a['source_package']}）")

    if args.mode != "apply":
        print(f"  [{args.mode or 'check'}] 未写盘（--apply 才合并写 registry protocols[]）")
        return 0

    import json as _json
    with open(reg_path, encoding="utf-8") as f:
        raw = _json.load(f)
    raw["protocols"] = plan["updated_protocols"]
    with open(reg_path, "w", encoding="utf-8") as f:
        _json.dump(raw, f, ensure_ascii=False, indent=2)
    print(f"  ✓ 已重链 {len(plan['affected'])} 处引用并写盘 {reg_path}")
    print("  下一步：跑 `bash verify.sh` 由 check14 ⑦/check15 ① 元素级断言自证")
    return 0


def main(argv=None) -> int:
    args = _build_parser().parse_args(argv)
    if args.cmd == "register":
        return _cmd_register(args)
    if args.cmd == "market":
        return _cmd_market(args)
    if args.cmd == "who-refers":
        return _cmd_who_refers(args)
    if args.cmd == "impact":
        return _cmd_impact(args)
    if args.cmd == "rename":
        return _cmd_rename(args)
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
    # B2 变体：--variant-add/--variant-remove 经 apply_variant 变换 selected
    if args.variant_add or args.variant_remove:
        from core.variants import apply_variant
        v = apply_variant(selected, {
            "add": [x.strip() for x in args.variant_add.split(",") if x.strip()],
            "remove": [x.strip() for x in args.variant_remove.split(",") if x.strip()],
        })
        selected = v.selected
        print(f"  [变体] selected {args.modules.split(',')} → {selected}"
              + (f"（移除 {args.variant_remove}）" if args.variant_remove else ""))
    dest = args.dest
    r = pipe(store, pipeline, selected,
             include_references=not args.no_include_refs,
             fmt=args.fmt, dest_dir=dest,
             fail_on_gate=not args.force_export,
             doc_semantics=args.doc_semantics)

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
