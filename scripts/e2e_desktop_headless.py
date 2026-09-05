#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""叙事工坊桌面端到端 headless 冒烟断言（C7 · T3-1 端到端测试入 CI，缺口⑩闭环）。

CI 用法：python3 scripts/e2e_desktop_headless.py
前置：仓库完整 checkout（04_模块库 / 03_管线库 / community 在库）；无需 GUI、
      无需 android/app 生成物——本脚本直驱 desktop core 层真实链路
      （Store / parser / validator / generator / pipeline_loader，与 GUI 共用同一 core）。

覆盖真实链路：
  装载官方核心 13 件（04_模块库 分类子目录逐文件 parse_module → Store.save_module）
  + T2-2 组合包模块 M91/M92（community/校园西幻轻混组合包，C6 战例）
  → 装载 P04 轻混装配流管线（load_pipeline_file，YAML frontmatter）
  → 按层装配（M00@P00 / M91@P40 / M92@P50 / M80@P80，层位精确匹配）
  → check_assembly 装配检查（核心锚点齐全）
  → generate_document 生成文档（层头/模块块/source.md 全文标题提升/资产附录）
  → 产物断言（文件在场 + 层头 + 模块块 full_id 锚点 + 事件语义 + 层序）
任一断言失败 → exit 1（CI 门禁）；全部通过 → exit 0。
"""
import glob
import os
import shutil
import sys

# Windows GBK 控制台兼容：stdout 强制 UTF-8（print ✓ 在 cp936 下抛 UnicodeEncodeError）
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # 仓库根
sys.path.insert(0, os.path.join(ROOT, "desktop", "src"))

# 临时 NF_HOME（Store 构造即建 modules/assets/presets/cache 目录）
HOME = os.environ.get("NF_TEST_HOME") or "/tmp/nf_e2e_home"
shutil.rmtree(HOME, ignore_errors=True)
os.makedirs(HOME, exist_ok=True)

from core.storage import Store                 # noqa: E402
from core.parser import parse_module           # noqa: E402
from core.validator import check_assembly      # noqa: E402
from core.generator import generate_document   # noqa: E402
from core.pipeline_loader import load_pipeline_file  # noqa: E402

MODULE_LIB = os.path.join(ROOT, "04_模块库")
PKG_MODULES = os.path.join(ROOT, "community", "校园西幻轻混组合包", "modules")
P04_PATH = os.path.join(ROOT, "community", "校园西幻轻混组合包",
                        "pipelines", "P04_轻混装配流管线.md")
OUT_MD = os.path.join(HOME, "ci_e2e_out.md")

failures: list = []


def check(name: str, cond: bool, detail: str = ""):
    if cond:
        print(f"  ✓ {name}")
    else:
        print(f"  ✗ FAIL: {name}" + (f" —— {detail}" if detail else ""))
        failures.append(name)


store = Store(home=HOME)

# ---- [1] 装载官方核心模块（04_模块库 分类子目录 13 件）----
print("[1] 装载官方核心模块（04_模块库）")
core_files = sorted(glob.glob(os.path.join(MODULE_LIB, "*", "*.md")))
check("官方模块库文件数 = 13", len(core_files) == 13, f"实际 {len(core_files)}")
core_full_ids = []
for f in core_files:
    try:
        with open(f, encoding="utf-8") as fh:
            m = parse_module(fh.read())
    except Exception as e:  # noqa: BLE001 —— 任一文件解析失败即记 FAIL
        check(f"parse_module({os.path.basename(f)})", False, repr(e))
        continue
    store.save_module(m)
    core_full_ids.append(m.full_id)
    print(f"    · {os.path.relpath(f, MODULE_LIB)} → {m.full_id} @{m.layer}")
check("官方核心注入 13 件", len(core_full_ids) == 13,
      f"实际 {len(core_full_ids)}")
for anchor in ("通用类:M00", "通用类:M80"):
    check(f"核心锚点 {anchor} 已注入", anchor in core_full_ids)

# ---- [2] 装载 T2-2 组合包模块（M91/M92）----
print("[2] 装载组合包模块（M91/M92）")
pkg_files = sorted(glob.glob(os.path.join(PKG_MODULES, "*.md")))
pkg_mods = {}
for f in pkg_files:
    with open(f, encoding="utf-8") as fh:
        m = parse_module(fh.read())
    store.save_module(m)
    pkg_mods[m.id] = m
    print(f"    · {os.path.basename(f)} → {m.full_id} @{m.layer}")
check("组合包模块注入 2 件", len(pkg_mods) == 2, f"实际 {len(pkg_mods)}")
m91 = pkg_mods.get("M91")
m92 = pkg_mods.get("M92")
check("M91 full_id=轻混类:M91 @P40",
      m91 is not None and m91.full_id == "轻混类:M91" and m91.layer == "P40",
      f"实际 {getattr(m91, 'full_id', None)} @{getattr(m91, 'layer', None)}")
check("M92 full_id=轻混类:M92 @P50",
      m92 is not None and m92.full_id == "轻混类:M92" and m92.layer == "P50",
      f"实际 {getattr(m92, 'full_id', None)} @{getattr(m92, 'layer', None)}")

# ---- [3] 装载 P04 轻混装配流管线 ----
print("[3] 装载 P04 轻混装配流管线")
p04 = load_pipeline_file(P04_PATH)
check("P04 管线解析成功", p04 is not None)
if p04:
    check("P04 id/name",
          p04.id == "P04" and p04.name == "轻混装配流管线",
          f"实际 {p04.id} · {p04.name}")
    check("P04 九层骨架", len(p04.layer_ids) == 9, f"实际 {p04.layer_ids}")
    l40 = p04.layer("P40")
    l50 = p04.layer("P50")
    check("P04 P40 default=[M91]",
          l40 is not None and l40.default_modules == ["M91"])
    check("P04 P50 default=[M92]",
          l50 is not None and l50.default_modules == ["M92"])

# ---- [4] 按层装配（M00@P00 / M91@P40 / M92@P50 / M80@P80）----
print("[4] 按层装配")
need = ["通用类:M00", "轻混类:M91", "轻混类:M92", "通用类:M80"]
installed = {m.full_id: m for m in store.list_modules()}
selected = []
for fid in need:
    m = installed.get(fid)
    check(f"装配项 {fid} 已安装", m is not None)
    if m:
        selected.append(m)
print("    装配清单：", [(m.full_id, m.layer) for m in selected])

# ---- [5] check_assembly 装配检查（核心锚点 M00/M80）----
print("[5] check_assembly 装配检查")
issues = check_assembly(selected, p04) if p04 else ["管线未就绪"]
check("check_assembly 无问题", issues == [], f"实际 {issues}")

# ---- [6] generate_document 生成文档 ----
print("[6] generate_document 生成文档")
title = "CI 端到端冒烟：轻混装配流"
md, warns = generate_document(p04, selected, asset_pack=None, title=title)
check("warns 为空（层位精确匹配）", warns == [], f"实际 {warns}")
with open(OUT_MD, "w", encoding="utf-8") as fh:
    fh.write(md)
check("产物文件在场且非空",
      os.path.isfile(OUT_MD) and len(md) > 2000, f"md {len(md)} 字节")

# ---- [7] 产物断言（层头 / 模块块 full_id 锚点 / 事件语义 / 标题提升 / 层序）----
print("[7] 产物断言")
has = lambda s: s in md  # noqa: E731
check("文档标题", has(f"# {title}"))
check("管线元信息行",
      has("> 管线：轻混装配流管线（P04）｜ 模块 4 个"))
# 层头（P04 九层骨架名 + description 随层头输出）
for hdr in ("## 层 P00 · 数据基座", "## 层 P40 · 行为决策",
            "## 层 P50 · 交互执行", "## 层 P80 · 输出呈现"):
    check(f"层头「{hdr}」", has(hdr))
check("P40 层描述（轻混决策位）随层头输出", has("轻混决策位"))
check("P80 层描述（匿名馈赠呈现面）随层头输出", has("匿名馈赠"))
# 模块块头（full_id · name（layer）锚点）
for blk in ("### 轻混类:M91 · 异界身份桥（P40）",
            "### 轻混类:M92 · 轻混装配执行（P50）",
            "### 通用类:M00 · 数据结构（P00）",
            "### 通用类:M80 · 输出生成器（P80）"):
    check(f"模块块「{blk}」", has(blk))
# 事件语义（M91 发布/订阅契约 + M92 收口契约 + 源文引用链）
for ev in ("campus_gift_intent", "campus_anonymous_gift",
           "confession_event", "relationship_change",
           "npc_action", "production_output"):
    check(f"事件语义「{ev}」在产物中", has(ev))
# source.md 全文标题提升（一级 # → ### 在模块块内）
check("M91 source 标题提升（### 模块 M91 · 异界身份桥）",
      has("### 模块 M91 · 异界身份桥"))
check("M92 source 标题提升（### 模块 M92 · 轻混装配执行）",
      has("### 模块 M92 · 轻混装配执行"))
# 层序（数据基座 → 行为决策 → 交互执行 → 输出呈现）
i00 = md.index("## 层 P00 · 数据基座")
i40 = md.index("## 层 P40 · 行为决策")
i50 = md.index("## 层 P50 · 交互执行")
i80 = md.index("## 层 P80 · 输出呈现")
check("层序 P00 < P40 < P50 < P80", i00 < i40 < i50 < i80,
      f"实际 {i00}/{i40}/{i50}/{i80}")

# ---- [8] v2.0.0 导出战例：IR → 质检门 → CCV3 导出（战略验收自动化段）----
print("[8] v2.0.0 导出战例（IR→quality_gate→export ccv3）")
from core.generator import render_ir
from core.quality_gate import run_gate
from core.exporter import export
from core.composer import build_assembly
from pathlib import Path
OUT_DIR = HOME  # 与 MD 同目录（NF_TEST_HOME 临时目录）
assemble_combo = build_assembly(store, p04, selected, include_references=True)
ir = render_ir(p04, assemble_combo, asset_pack=None, title=title)
gate = run_gate(ir)
check("质量门 ok（导出可放行）", gate.ok(),
      f"PASS {gate.n_pass}/WARN {gate.n_warn}/FAIL {gate.n_fail}")
check("质量门 ok（导出可放行）", gate.ok(),
      f"PASS {gate.n_pass}/WARN {gate.n_warn}/FAIL {gate.n_fail}")
eres = export(ir, "ccv3", dest_dir=OUT_DIR)
exported = {os.path.basename(f) for f in eres.files}
check("chara.json 已导出", "chara.json" in exported,
      f"files={sorted(exported)}")
import json as _json
chara = _json.loads(
    Path(OUT_DIR, "chara.json").read_text(encoding="utf-8"))
check("chara spec = chara_card_v3", chara.get("spec") == "chara_card_v3",
      f"spec={chara.get('spec')}")
world = _json.loads(Path(OUT_DIR, "world.json").read_text(encoding="utf-8"))
world_keys = "".join("".join(e.get("keys") or []) for e in world["entries"])
check("world 覆盖叙事模块 M91/M92",
      "M91" in world_keys and "M92" in world_keys, "")
check("world 含跨包引用 M55(校园)/M17(西幻)（E3 运行时生效）",
      "M55" in world_keys and "M17" in world_keys, "")
check("导出无未映射警告（不静默丢弃）", not eres.warnings,
      f"warnings={eres.warnings}")
check("world 条目已落盘", len(world["entries"]) > 0,
      f"{len(world['entries'])} 条")

# ---- 汇总 ----
stats = store.stats()
check("Store 模块总数 = 15（官方13 + 组合包2）",
      stats["modules"] == 15, f"实际 {stats}")
print(f"\n[统计] Store: {stats}")
print(f"[产物] {OUT_MD}（{len(md)} 字节）")
if failures:
    print(f"\n✗ E2E DESKTOP HEADLESS FAILED"
          f"（{len(failures)} 项断言失败）：{failures}")
    sys.exit(1)
print("\n★ E2E DESKTOP HEADLESS PASSED ✓"
      "（官方13件 + M91/M92 + P04 → 装配 → 生成 → 断言全绿）")
sys.exit(0)
