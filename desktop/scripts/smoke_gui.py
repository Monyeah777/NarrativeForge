#!/usr/bin/env python3
"""GUI 冒烟测试：offscreen 实例化 MainWindow 并演练核心交互路径。

用法：
    NARRATIVE_FORGE_HOME=/tmp/nf-test-home \
    QT_QPA_PLATFORM=offscreen python3 scripts/smoke_gui.py
"""
from __future__ import annotations

import os
import sys

# 保证从项目根运行时可导入 src
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6 import QtCore, QtWidgets  # noqa: E402

from src.core.models import Pipeline  # noqa: E402
from src.ui.main_window import MainWindow  # noqa: E402

CHECKS: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    mark = "PASS" if cond else "FAIL"
    CHECKS.append(mark)
    print(f"[{mark}] {name}" + (f"  ({detail})" if detail else ""))


def main() -> int:
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
    win = MainWindow()
    win.show()
    app.processEvents()

    # ---------- 1. 初始装载 ----------
    check("7 个功能区已挂载", all(
        getattr(win, f"zone_{z}") is not None for z in "abcdefg"))
    check("tabs 共 7 页", win.tabs.count() == 7,
          f"count={win.tabs.count()}")
    check("管线已装载", len(win.pipelines) >= 3,
          f"{len(win.pipelines)} 条")
    check("当前管线已选定", win.current_pipeline is not None,
          win.current_pipeline_id or "None")
    n_mod = len(win.store.list_modules())
    check("模块库已装载", n_mod >= 30, f"{n_mod} 个模块")
    n_pack = len(win.store.list_asset_packs())
    check("资产包已装载", n_pack >= 2, f"{n_pack} 个资产包")
    check("② 表格已填充", win.zone_b.table.rowCount() == n_mod,
          f"rows={win.zone_b.table.rowCount()}")
    top_count = win.zone_c.tree.topLevelItemCount()
    check("③ 层树已填充", top_count == len(win.current_pipeline.layers),
          f"top={top_count}")
    # zone_d 下拉固定含「（无资产包）」占位项，故 count = 资产包数 + 1
    check("④ 资产下拉已填充",
          win.zone_d.asset_combo.count() == n_pack + 1,
          f"count={win.zone_d.asset_combo.count()}")
    check("⑤ 资产列表已填充",
          win.zone_e.pack_list.count() == n_pack,
          f"count={win.zone_e.pack_list.count()}")

    # ---------- 2. 勾选联动 ----------
    # 取当前管线第一个模块勾选 → 验证 selected 与 ④ 提示刷新
    tree = win.zone_c.tree
    first_module_item = None
    for i in range(tree.topLevelItemCount()):
        top = tree.topLevelItem(i)
        if top.childCount():
            first_module_item = top.child(0)
            break
    check("层树含模块子项", first_module_item is not None)
    if first_module_item is not None:
        first_module_item.setCheckState(0, QtCore.Qt.Checked)
        app.processEvents()
        check("勾选后 selected 更新", len(win.selected) == 1,
              f"selected={sorted(win.selected)}")

    # ② 区勾选列联动（另一模块）
    tbl = win.zone_b.table
    target_row = -1
    for r in range(tbl.rowCount()):
        fid = tbl.item(r, 1).data(QtCore.Qt.UserRole)
        if fid not in win.selected:
            target_row = r
            break
    if target_row >= 0:
        ck_item = tbl.item(target_row, 0)
        ck_item.setCheckState(QtCore.Qt.Checked)
        app.processEvents()
        check("② 勾选联动 selected", len(win.selected) >= 2,
              f"selected={len(win.selected)}")

    # ---------- 3. 生成预览 ----------
    win.zone_d.title_edit.setText("冒烟测试文档")
    win.zone_d.do_generate()
    app.processEvents()
    has_md = bool(getattr(win.zone_d, "last_md", ""))
    check("④ 生成预览成功", has_md and len(win.zone_d.last_md) > 200,
          f"len={len(win.zone_d.last_md)}")
    if has_md:
        check("预览含标题", "冒烟测试文档" in win.zone_d.last_md)

    # ---------- 4. 预设保存 + 应用 ----------
    # zone_f.do_save 弹模态 QInputDialog，不适合自动化；直接走 snapshot_preset 存库，
    # 再经 apply_preset_state 入口测「保存 → 清空 → 应用恢复」闭环。
    from src.core.preset_manager import snapshot_preset  # noqa: E402
    presets_before = len(win.store.list_presets())
    pipe0 = win.current_pipeline
    mods = [win.store.get_module(f) for f in sorted(win.selected)
            if win.store.get_module(f) is not None]
    p = snapshot_preset("冒烟预设", pipe0.id, mods, "")
    win.store.save_preset(p)
    app.processEvents()
    check("预设已保存", len(win.store.list_presets()) == presets_before + 1)
    win.zone_f.refresh()
    check("⑥ 预设下拉已刷新", win.zone_f.preset_combo.count()
          == presets_before + 1,
          f"count={win.zone_f.preset_combo.count()}")

    # 应用预设（先清空勾选，再验证恢复）
    win.zone_c.clear_selection()
    app.processEvents()
    check("清空勾选生效", len(win.selected) == 0)
    from src.core.preset_manager import apply_preset  # noqa: E402
    result = apply_preset(win.store, p)
    win.apply_preset_state(result)
    app.processEvents()
    check("应用预设恢复勾选", len(win.selected) == len(mods),
          f"selected={len(win.selected)}")

    # ---------- 5. 回调与重载 ----------
    win.on_modules_changed()
    win.on_pipeline_changed()
    win.on_selection_changed()
    win.reload_pipelines()
    app.processEvents()
    check("各联动回调无异常", True)

    # ---------- 6. 拖放入口 ----------
    # 用现有测试模块 source.md 模拟拖放（zone_a.load_file 走 parse_module，
    # 仅支持 md 文本；module_dir_of/get_module_dir 不存在，改用 module_dirs()）
    md_file = None
    for d in win.store.module_dirs():
        cand = d / "source.md"
        if cand.exists():
            md_file = str(cand)
            break
    if md_file:
        ok = win.zone_a.load_file(md_file)
        check("拖放/打开入口解析文件", ok,
              os.path.basename(md_file))
        check("解析后切到①区可安装", win.zone_a.b_install.isEnabled())

    # ---------- 7. 状态栏 ----------
    win.status("冒烟测试完成")
    check("状态栏可写", bool(win.statusBar().currentMessage()))

    # 清理冒烟预设，保持测试库干净
    win.store.remove_preset("冒烟预设")

    failed = CHECKS.count("FAIL")
    print(f"\n===== 冒烟测试完成：{len(CHECKS) - failed}/{len(CHECKS)} 通过"
          f"（失败 {failed}）=====")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())