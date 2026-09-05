#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E4 模块市场雏形 offscreen GUI 冒烟（zone_g 检索驱动一站式视图）。

用法：QT_QPA_PLATFORM=offscreen python3 scripts/smoke_zone_g_market.py
前置：仓库完整 checkout（04_模块库 官方核心 / community 在库）；无需真机显示器。
覆盖（E4 验证清单）：
  装载官方核心模块 → 实例化 MainWindow（真实 GUI 构造链）
  → zone_g.do_search：
      ① query="M00" → module 行命中（引用列 = 通用类:M00）
      ② 空 query 全部 kind → 四类合计行数 > 0（模块+资产+管线+协议任一在源）
      ③ 选中 module 行触发「加入装配」动作 → app.selected 含该 full_id
        + 信息列出现「已装配」标记 + zone_c 层树勾选同步（stat 计数 +1）
任一断言失败 → exit 1；全部通过 → exit 0。
"""
import os
import shutil
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# desktop/src 供 core.* 顶层导入；desktop 供 src.ui.* 包导入（ui 内用相对导入）
sys.path.insert(0, os.path.join(ROOT, "desktop", "src"))
sys.path.insert(0, os.path.join(ROOT, "desktop"))

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QPA_FONTDIR", "")

HOME = os.environ.get("NF_TEST_HOME") or "/tmp/nf_smoke_zone_g"
shutil.rmtree(HOME, ignore_errors=True)
os.makedirs(HOME, exist_ok=True)

from PySide6 import QtWidgets                 # noqa: E402
from core.storage import Store                # noqa: E402
from core.parser import parse_module          # noqa: E402
MODULE_LIB = os.path.join(ROOT, "04_模块库")

failures = []


def check(name: str, cond: bool, detail: str = ""):
    if cond:
        print(f"  ✓ {name}")
    else:
        print(f"  ✗ FAIL: {name}" + (f" —— {detail}" if detail else ""))
        failures.append(name)


# ---- 装载官方核心模块（M00 等锚点命中用）----
print("[1] 装载官方核心模块 + 实例化 MainWindow")
store = Store(home=HOME)
core_files = sorted(p for p in __import__("glob").glob(
    os.path.join(MODULE_LIB, "*", "*.md")))
for f in core_files:
    try:
        with open(f, encoding="utf-8") as fh:
            m = parse_module(fh.read())
        store.save_module(m)
    except Exception as e:                     # noqa: BLE001
        check(f"parse_module({os.path.basename(f)})", False, repr(e))
check("官方模块已装载（≥1 件）", len(store.list_modules()) >= 1,
      f"实际 {len(store.list_modules())}")

# 资产包 fixture：空资产包命名以令 search('asset_pack') 可命中
from core.models import AssetPack               # noqa: E402
_store_ap = AssetPack(name="冒烟测试资产", version="1.0.0",
                      entries={"k1": "测试键"}, installed_at="2026-09-05T00:00:00")
store.save_asset_pack(_store_ap)
check("资产包 fixture 已装载", len(store.list_asset_packs()) == 1,
      f"实际 {len(store.list_asset_packs())}")

qt_app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
from core.pipeline_loader import discover_pipelines        # noqa: E402
from src.ui.main_window import MainWindow                   # noqa: E402

# 管线缓存：从 03_管线库 发现装载（E4 pipeline 命中/装配树需要）
PIPE_DIR = os.path.join(ROOT, "03_管线库")
pipes = discover_pipelines(PIPE_DIR) if os.path.isdir(PIPE_DIR) else []
store.save_cache("pipelines", [p.to_json() for p in pipes])
win = MainWindow(store)
win.show()
win.zone_g.query_edit.setText("M00")
win.zone_g.do_search()
check("MainWindow 构造成功（store 空壳可跑）", win is not None)

# ---- ① query="M00" → module 行命中 ----
print("[2] 检索 query=M00")
tbl = win.zone_g.table
rows_m00 = []
for r in range(tbl.rowCount()):
    ref_item = tbl.item(r, 1)
    if ref_item and ref_item.text() == "通用类:M00":
        rows_m00.append(r)
check("M00 命中 module 行", len(rows_m00) == 1,
      f"实际行 {rows_m00}，总 {tbl.rowCount()}")
if rows_m00:
    r = rows_m00[0]
    kind_item = tbl.item(r, 0)
    check("命中行类型=模块",
          kind_item is not None and kind_item.text() == "模块",
          f"类型列 {kind_item.text() if kind_item else None}")
    # 双击行弹详情对话框会阻塞——用 info 文本确认非空即可
    info_item = tbl.item(r, 3)
    check("命中行信息列含层位",
          info_item is not None and "层" in info_item.text(),
          f"info={info_item.text() if info_item else None}")

# ---- ③ 加入装配动作 ----
print("[3] 从搜索结果加入装配（M00）")
if rows_m00:
    r = rows_m00[0]
    tbl.selectRow(r)
    win.zone_g.do_action()
    check("app.selected 含 通用类:M00", "通用类:M00" in win.selected,
          f"selected={sorted(win.selected)}")
    info_item = tbl.item(r, 3)
    check("信息列出现「已装配」标记",
          info_item is not None and "已装配" in info_item.text(),
          f"info={info_item.text() if info_item else None}")
    check("③ 层树勾选同步（stat 含 已选 1）",
          "已选 1" in win.zone_c.stat_label.text(),
          f"stat={win.zone_c.stat_label.text()}")
    check("重复加入幂等（selected 仍 1 项）",
          (win.zone_g.do_action() is None
           and len(win.selected) == 1),
          f"selected={sorted(win.selected)}")

# ---- ② 空 query 全部 kind → 四类合计 > 0 ----
print("[4] 空 query 全部 kind 浏览")
win.zone_g.kind_combo.setCurrentIndex(0)      # 全部
win.zone_g.query_edit.setText("")
win.zone_g.do_search()
total = win.zone_g.table.rowCount()
check("全部 kind 空 query 有结果（Discovery 列表）", total > 0,
      f"实际 {total}")
kinds = set()
for r in range(total):
    it = win.zone_g.table.item(r, 0)
    if it:
        kinds.add(it.text())
print(f"    出现类型：{sorted(kinds)}")
check("四类检索齐备（模块/资产包/管线/协议均可见）",
      {"模块", "资产包", "管线", "协议"} <= kinds,
      f"实际 {sorted(kinds)}")

# ---- ⑤ asset_pack 命中 → 选用资产包动作 ----
print("[5] asset_pack 检索 → 选用资产包")
win.zone_g.kind_combo.setCurrentIndex(2)      # 资产包
win.zone_g.query_edit.setText("冒烟")
win.zone_g.do_search()
tbl = win.zone_g.table
row_ap = None
for r in range(tbl.rowCount()):
    ref_item = tbl.item(r, 1)
    if ref_item and ref_item.text() == "冒烟测试资产":
        row_ap = r
        break
check("资产包检索命中 fixture", row_ap is not None,
      f"总 {tbl.rowCount()} 行")
if row_ap is not None:
    tbl.selectRow(row_ap)
    win.zone_g.do_action()
    cb = win.zone_d.asset_combo
    check("④ 资产包下拉已选用 fixture",
          cb.currentData() == "冒烟测试资产",
          f"currentData={cb.currentData()}")

# ---- ⑥ pipeline 命中 → 设为当前管线动作 ----
print("[6] pipeline 检索 → 设为当前管线")
win.zone_g.kind_combo.setCurrentIndex(3)      # 管线
win.zone_g.query_edit.setText("P00")
win.zone_g.do_search()
tbl = win.zone_g.table
row_pipe = None
for r in range(tbl.rowCount()):
    ref_item = tbl.item(r, 1)
    if ref_item and ref_item.text() == "P00":
        row_pipe = r
        break
check("管线检索命中 P00", row_pipe is not None,
      f"总 {tbl.rowCount()} 行")
if row_pipe is not None:
    tbl.selectRow(row_pipe)
    win.zone_g.do_action()
    check("当前管线已切换 P00", win.current_pipeline_id == "P00",
          f"current_pipeline_id={win.current_pipeline_id}")
    check("③ 管线下拉同步 P00",
          win.zone_c.pipe_combo.currentData() == "P00",
          f"combo={win.zone_c.pipe_combo.currentData()}")

print(f"\n[统计] 模块 {len(store.list_modules())} · 管线 {len(pipes)}")
if failures:
    print(f"\n✗ SMOKE ZONE_G FAILED（{len(failures)} 项）：{failures}")
    sys.exit(1)
print("\n★ SMOKE ZONE_G PASSED ✓（检索命中 → 加入装配 → 装配态标记 → 层树联动）")
sys.exit(0)
