# -*- coding: utf-8 -*-
"""叙事工坊 android/app 控制器本地自测（纯逻辑，无 Kivy）。

CI 冒烟用法：python3 scripts/selftest_android.py
前置：已执行 bash scripts/sync_android.sh（生成 android/app/{core,seed}）。
覆盖链路：种子自举 → 幂等跳过 → 管线选择 → 按层自动勾选 → 装配检查
         → 生成文档 → 保存 → 模块导入/勾选/删除。
"""
import glob
import os
import re
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

# ---- 10. UI 启动安全静态断言（v0.9.0 T1：APK 闪退修复点回归闸门） ----
# 纯 python3 文件读取，不 import KivyMD（CI 裸环境无 Kivy 依赖）。三断言
# 对应三处历史闪退修复（git merge-base 实证均已含于 v0.8.0 tag）：
#   ① screens.py 不得含 MDRadioButton import —— KivyMD 1.2.0 已移除该类
#      （selectioncontrol 仅导出 MDCheckbox/MDSwitch/Thumb）；旧 import 抛
#      ImportError → main.py 顶层 import screens 即启动闪退（根因一）。
#   ② main.py MDTopAppBar 调用不得含 subtitle= kwarg —— 1.2.0 无该属性，
#      未知 kwarg → EventDispatcher.__init__ 抛 TypeError → 启动闪退（根因二）。
#   ③ _register_cjk_fonts 定义在场且 build() 首行调用 —— 思源黑体 SC 覆盖
#      Roboto* 名称，修复中文方块字（根因三）。
# FAIL 任一 = 冒烟 exit 1（闪退修复点回归有 CI 闸门）。
_screens_src = open(os.path.join(ROOT, "android/app/ui/screens.py"),
                    encoding="utf-8").read()
# 只匹配「行首 from ... import」形式的真实 import 语句（re.M 行锚定）；
# screens.py 的 _radio_row docstring 记录了根因说明（引用旧代码原文），
# 裸子串匹配会误伤文档字符串——故必须行锚定排除 docstring/注释描述。
assert not re.search(
    r"^\s*from\s+kivymd\.uix\.selectioncontrol\s+import\s+MDRadioButton\b",
    _screens_src, re.M), \
    "[10.a] screens.py 含 MDRadioButton import（KivyMD 1.2.0 已移除 → ImportError 闪退）"
print("[10.a] screens.py 无 MDRadioButton import ✓")

_main_src = open(os.path.join(ROOT, "android/main.py"), encoding="utf-8").read()
assert not re.search(r"MDTopAppBar\([^)]*subtitle=", _main_src), \
    "[10.b] main.py MDTopAppBar 调用含 subtitle=（1.2.0 无该属性 → TypeError 闪退）"
print("[10.b] main.py MDTopAppBar 无 subtitle= kwarg ✓")

assert "def _register_cjk_fonts" in _main_src, \
    "[10.c] main.py 缺 _register_cjk_fonts 定义（CJK 覆盖缺失 → 中文方块字）"
_build_first = None
for _i, _ln in enumerate(_main_src.splitlines()):
    if _ln.strip().startswith("def build("):
        for _body in _main_src.splitlines()[_i + 1:]:
            _s = _body.strip()
            if not _s or _s.startswith("#"):
                continue
            _build_first = _s
            break
        break
assert _build_first and "_register_cjk_fonts()" in _build_first, \
    "[10.c] main.py build() 首行未调用 _register_cjk_fonts()（实际首行: %r）" % _build_first
print("[10.c] _register_cjk_fonts 定义在场 + build() 首行调用 ✓")

print("\n★ ALL CONTROLLER SELFTEST PASSED ✓")