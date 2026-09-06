"""功能区 F · 预设：把当前勾选/管线/资产包存为预设，一键复原 + JSON 导入导出。

预设 = { name, pipeline, modules: [full_id...], asset_pack }。
对接 core.preset_manager（snapshot/apply/export/import）与 Store 落盘。
"""
from __future__ import annotations
from PySide6 import QtCore, QtWidgets
from ..core.models import Preset
from ..core.preset_manager import (
    snapshot_preset, apply_preset,
    export_preset_json, import_preset_json,
    export_preset_file, import_preset_file,
)
from . import common


class ZoneFPresets(QtWidgets.QWidget):
    """⑥ 预设管理：保存 / 应用 / 删除 / 导入导出。"""
    def __init__(self, app, parent=None):
        super().__init__(parent)
        self.app = app
        self._presets: list[Preset] = []
        self._build_ui()
        self.refresh()

    # ---------- UI ----------
    def _build_ui(self):
        root = QtWidgets.QVBoxLayout(self)

        bar = QtWidgets.QHBoxLayout()
        bar.addWidget(QtWidgets.QLabel("预设:"))
        self.preset_combo = QtWidgets.QComboBox()
        self.preset_combo.currentIndexChanged.connect(self._on_select)
        bar.addWidget(self.preset_combo, 1)
        b_refresh = QtWidgets.QPushButton("刷新")
        b_refresh.clicked.connect(self.refresh)
        bar.addWidget(b_refresh)
        root.addLayout(bar)

        self.info_label = QtWidgets.QLabel("（无预设）")
        self.info_label.setWordWrap(True)
        root.addWidget(self.info_label)

        grp_save = QtWidgets.QGroupBox("保存 / 应用")
        g1 = QtWidgets.QGridLayout(grp_save)
        b_save = QtWidgets.QPushButton("保存当前勾选为预设…")
        b_apply = QtWidgets.QPushButton("应用此预设")
        b_del = QtWidgets.QPushButton("删除此预设")
        b_save.clicked.connect(self.do_save)
        b_apply.clicked.connect(self.do_apply)
        b_del.clicked.connect(self.do_delete)
        for w, r, c in ((b_save, 0, 0), (b_apply, 0, 1), (b_del, 0, 2)):
            g1.addWidget(w, r, c)
        root.addWidget(grp_save)

        grp_io = QtWidgets.QGroupBox("导入 / 导出（跨机器迁移 JSON）")
        g2 = QtWidgets.QHBoxLayout(grp_io)
        b_exp = QtWidgets.QPushButton("导出 JSON 文件…")
        b_imp = QtWidgets.QPushButton("导入 JSON 文件…")
        b_cp = QtWidgets.QPushButton("复制 JSON 到剪贴板")
        b_paste = QtWidgets.QPushButton("从剪贴板导入")
        b_exp.clicked.connect(self.do_export_file)
        b_imp.clicked.connect(self.do_import_file)
        b_cp.clicked.connect(self.do_copy_json)
        b_paste.clicked.connect(self.do_paste_json)
        for w in (b_exp, b_imp, b_cp, b_paste):
            g2.addWidget(w)
        g2.addStretch(1)
        root.addWidget(grp_io)

        self.hint = QtWidgets.QLabel(
            "提示：预设记录的是 管线 + 勾选集合 + 资产包。"
            "「应用」会把 ③ 的勾选与 ④ 的资产包一起复原。")
        self.hint.setWordWrap(True)
        root.addWidget(self.hint)
        root.addStretch(1)

    # ---------- 数据 ----------
    def refresh(self):
        cur = self.preset_combo.currentData()
        self._presets = sorted(self.app.store.list_presets(),
                               key=lambda p: (p.pipeline, p.name))
        self.preset_combo.blockSignals(True)
        self.preset_combo.clear()
        for p in self._presets:
            self.preset_combo.addItem(
                f"{p.pipeline} · {p.name}（{len(p.modules)}模块）", p.name)
        if cur:
            idx = self.preset_combo.findData(cur)
            if idx >= 0:
                self.preset_combo.setCurrentIndex(idx)
        self.preset_combo.blockSignals(False)
        self._on_select(self.preset_combo.currentIndex())

    def _current(self) -> Preset | None:
        r = self.preset_combo.currentIndex()
        if 0 <= r < len(self._presets):
            return self._presets[r]
        return None

    def _on_select(self, _idx):
        p = self._current()
        if p is None:
            self.info_label.setText("（无预设）")
            return
        self.info_label.setText(
            f"名称：{p.name}\n管线：{p.pipeline}\n"
            f"模块数：{len(p.modules)}（{', '.join(p.modules[:6])}"
            + (" …" if len(p.modules) > 6 else "") + "）\n"
            + (f"资产包：{p.asset_pack}" if p.asset_pack else "资产包：无")
            + (f"\n创建时间：{p.created_at}" if p.created_at else ""))

    # ---------- 保存 / 应用 ----------
    def do_save(self):
        pipe = self.app.current_pipeline
        if pipe is None:
            common.warn(self, "请先在 ③管线装配 加载并选择管线。")
            return
        if not self.app.selected:
            common.warn(self, "当前未勾选任何模块，预设将为空。"
                              "确认继续？", title="提示")
        name, ok = QtWidgets.QInputDialog.getText(
            self, "保存预设", "预设名称：",
            text=f"{pipe.id}预设{len(self._presets) + 1}")
        if not ok or not name.strip():
            return
        # 收集勾选模块（保持管线内顺序稳定：按 full_id 排序）
        modules = []
        for fid in sorted(self.app.selected):
            m = self.app.store.get_module(fid)
            if m is not None:
                modules.append(m)
        ap = ""
        zd = getattr(self.app, "zone_d", None)
        if zd is not None and getattr(zd, "asset_combo", None) is not None:
            ap = zd.asset_combo.currentData() or ""
        p = snapshot_preset(name.strip(), pipe.id, modules, ap)
        try:
            self.app.store.save_preset(p)
        except Exception as exc:      # noqa: BLE001
            common.error(self, f"保存预设失败：{exc}")
            return
        self.refresh()
        idx = self.preset_combo.findData(p.name)
        if idx >= 0:
            self.preset_combo.setCurrentIndex(idx)
        common.info(self, f"已保存预设「{p.name}」："
                          f"{pipe.id} · {len(p.modules)} 模块"
                          + (f" · 资产包「{ap}」" if ap else ""))

    def do_apply(self):
        p = self._current()
        if p is None:
            common.info(self, "请先在列表中选择要应用的预设。")
            return
        result = apply_preset(self.app.store, p)
        # 交给主窗口统一更新 ③/②/④ 各视图状态
        if hasattr(self.app, "apply_preset_state"):
            self.app.apply_preset_state(result)
        else:
            common.warn(self, "主窗口未提供 apply_preset_state，无法应用。")

    def do_delete(self):
        p = self._current()
        if p is None:
            common.info(self, "请先选择要删除的预设。")
            return
        if QtWidgets.QMessageBox.question(
                self, "确认删除", f"删除预设「{p.name}」？") \
                != QtWidgets.QMessageBox.StandardButton.Yes:
            return
        self.app.store.remove_preset(p.name)
        self.refresh()
        common.info(self, f"已删除预设「{p.name}」。")

    # ---------- 导入 / 导出 ----------
    def do_export_file(self):
        p = self._current()
        if p is None:
            common.info(self, "请先选择要导出的预设。")
            return
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "导出预设 JSON", f"{p.name}.preset.json",
            "JSON (*.json);;所有文件 (*)")
        if not path:
            return
        ok = export_preset_file(p, path)
        if ok:
            common.info(self, f"已导出：{path}")
        else:
            common.error(self, "导出失败，请检查路径权限。")

    def do_import_file(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "导入预设 JSON", "", "JSON (*.json);;所有文件 (*)")
        if not path:
            return
        p = import_preset_file(self.app.store, path)
        if p is None:
            common.error(self, "文件格式非法：缺少 name/pipeline 或 JSON 损坏。")
            return
        self.refresh()
        idx = self.preset_combo.findData(p.name)
        if idx >= 0:
            self.preset_combo.setCurrentIndex(idx)
        common.info(self, f"已导入预设「{p.name}」。")

    def do_copy_json(self):
        p = self._current()
        if p is None:
            common.info(self, "请先选择要复制的预设。")
            return
        QtWidgets.QApplication.clipboard().setText(export_preset_json(p))
        common.info(self, "预设 JSON 已复制到剪贴板。")

    def do_paste_json(self):
        text = QtWidgets.QApplication.clipboard().text()
        if not text.strip():
            common.info(self, "剪贴板为空。")
            return
        p = import_preset_json(text)
        if p is None:
            common.error(self, "剪贴板内容不是合法预设 JSON。")
            return
        try:
            self.app.store.save_preset(p)
        except Exception as exc:      # noqa: BLE001
            common.error(self, f"导入失败：{exc}")
            return
        self.refresh()
        idx = self.preset_combo.findData(p.name)
        if idx >= 0:
            self.preset_combo.setCurrentIndex(idx)
        common.info(self, f"已从剪贴板导入预设「{p.name}」。")