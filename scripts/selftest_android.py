# -*- coding: utf-8 -*-
"""叙事工坊 android/app 控制器本地自测（纯逻辑，无 Kivy）。

CI 冒烟用法：python3 scripts/selftest_android.py
前置：已执行 bash scripts/sync_android.sh（生成 android/app/{core,seed}）。
覆盖链路：种子自举 → 幂等跳过 → 管线选择 → 按层自动勾选 → 装配检查
         → 生成文档 → 保存 → 模块导入/勾选/删除。
"""
import glob
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # 仓库根
sys.path.insert(0, os.path.join(ROOT, "android"))

HOME = os.environ.get("NF_TEST_HOME") or "/tmp/nf_selftest_home"
shutil.rmtree(HOME, ignore_errors=True)
os.makedirs(HOME, exist_ok=True)

from app.controller import Controller  # noqa: E402

c = Controller(home=HOME)

# ---- 1. 种子自举 ----
st = c.ensure_seeded()
print("[1] ensure_seeded →", st)
assert st["modules"] > 0 and st["pipelines"] > 0 \
    and not st["errors"], st

print("    pipelines:", [(p.id, p.name) for p in c.list_pipelines()])
print("    modules 总数:", len(c.list_modules()))
for k in sorted(c.modules_by_category()):
    print(f"    · {k}: {len(c.modules_by_category()[k])}")
print("    资产包:", c.asset_pack_names())

# ---- 2. 幂等 ----
st2 = c.ensure_seeded()
assert st2.get("skipped"), st2
print("[2] 幂等跳过 ✓", st2)

# ---- 3. 管线选择（持久化） ----
c.set_pipeline("P01")
assert c.current_pipeline_id == "P01"
print("[3] set_pipeline P01 →", c.current_pipeline().id,
      c.current_pipeline().name)

# ---- 4. 自动勾选（管线各层默认模块） ----
n = c.select_defaults()
print("[4] select_defaults 勾选数:", n)
assert n > 0
mods, missing = c.selected_modules()
print("    selected 有效:", len(mods), "| 失效:", missing)
assert missing == []
layers = sorted({m.layer for m in mods})
print("    覆盖层位:", layers)
assert len(layers) >= 5, layers  # 至少覆盖一半层位

# ---- 5. 装配检查 ----
issues = c.assembly_issues()
print("[5] assembly_issues:", issues)

# ---- 6. 生成文档 ----
md, warns = c.generate(title="《同桌的她》· CI 冒烟")
print("[6] generate → md长度:", len(md), "| 警告数:", len(warns))
assert md
print("    default_output_name:", c.default_output_name())

# ---- 7. 保存 ----
out = os.path.join(HOME, "out.md")
assert c.save_to(out)
print("[7] save_to ✓ →", os.path.getsize(out), "bytes")

# ---- 8. stats ----
print("[8] stats:", c.stats())

# ---- 9. 导入真实种子模块 + 勾选/删除 ----
src = sorted(glob.glob(os.path.join(
    ROOT, "android/app/seed/04_模块库/*/*.md")))[0]
text = open(src, encoding="utf-8").read()
print("[9] 导入样本:", os.path.basename(src))
m = c.import_module(text)
print("    imported →", m.full_id, "|", m.name, "@", m.layer)
assert c.get_module(m.full_id) is not None
assert c.toggle(m.full_id) is True and c.is_selected(m.full_id)
assert c.toggle(m.full_id) is False and not c.is_selected(m.full_id)
assert c.remove_module(m.full_id)
assert c.get_module(m.full_id) is None
print("    toggle 双向 + remove ✓")

print("\n★ ALL CONTROLLER SELFTEST PASSED ✓")