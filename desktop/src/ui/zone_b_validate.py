"""功能区 B · 模块库与校验：分类筛选 / 勾选参与装配 / 校验展示 / 删除启停。"""
from __future__ import annotations

from PySide6 import QtCore, QtWidgets

from . import common

COL_CHECK, COL_FID, COL_NAME, COL_LAYER, COL_ENABLED, COL_ASSETS = range(6)


class ZoneBValidate(QtWidgets.QWidget):
    """② 校验展示：本地已装模块一览 + 选中模块字段级校验。"""

    selection_changed = QtCore.Signal()     # 勾选集合变化

    def __init__(self, app, parent=None):
        super().__init__(parent)
        self.app = app
        self._busy = False
        self._build_ui()

    # ---------- UI ----------
    def _build_ui(self):
        root = QtWidgets.QVBoxLayout(self)
        # 工具行
        bar = QtWidgets.QHBoxLayout()
        bar.addWidget(QtWidgets.QLabel("分类:"))
        self.cat_combo = QtWidgets.QComboBox()
        self.cat_combo.addItems(common.CATEGORY_FILTER)
        self.cat_combo.currentTextChanged.connect(self.refresh)
        bar.addWidget(self.cat_combo)
        self.search_edit = QtWidgets.QLineEdit()
        self.search_edit.setPlaceholderText("搜索 ID / 名称…")
        self.search_edit.setClearButtonEnabled(True)
        self.search_edit.textChanged.connect(self.refresh)
        bar.addWidget(self.search_edit, 1)
        b_refresh = QtWidgets.QPushButton("刷新")
        b_refresh.clicked.connect(self.refresh)
        bar.addWidget(b_refresh)
        root.addLayout(bar)

        # 表格
        self.table = QtWidgets.QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(
            ["参与", "模块ID", "名称", "层位", "启用", "引用资产"])
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        hh.setSectionResizeMode(COL_CHECK, QtWidgets.QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(COL_FID, QtWidgets.QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(COL_LAYER, QtWidgets.QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(COL_ENABLED, QtWidgets.QHeaderView.ResizeToContents)
        self.table.itemChanged.connect(self._on_item_changed)
        self.table.itemSelectionChanged.connect(self._on_selection)
        self.table.itemDoubleClicked.connect(self._on_double)
        root.addWidget(self.table, 1)

        # 校验输出
        self.check_view = QtWidgets.QPlainTextEdit()
        self.check_view.setReadOnly(True)
        self.check_view.setMaximumHeight(120)
        root.addWidget(QtWidgets.QLabel("选中模块校验："))
        root.addWidget(self.check_view)

        # 操作行
        ops = QtWidgets.QHBoxLayout()
        b_import = QtWidgets.QPushButton("从文件安装…")
        b_toggle = QtWidgets.QPushButton("启用/停用选中")
        b_delete = QtWidgets.QPushButton("删除选中")
        b_all = QtWidgets.QPushButton("全选参与")
        b_none = QtWidgets.QPushButton("全部不参与")
        ops.addWidget(b_import)
        ops.addWidget(b_toggle)
        ops.addWidget(b_delete)
        ops.addStretch(1)
        ops.addWidget(b_all)
        ops.addWidget(b_none)
        root.addLayout(ops)

        b_import.clicked.connect(self.import_file)
        b_toggle.clicked.connect(self.toggle_selected)
        b_delete.clicked.connect(self.delete_selected)
        b_all.clicked.connect(lambda: self._set_all(True))
        b_none.clicked.connect(lambda: self._set_all(False))

    # ---------- 数据填充 ----------
    def refresh(self):
        """按筛选重填表格；勾选状态与 app.selected 保持一致。"""
        cat = self.cat_combo.currentText()
        kw = self.search_edit.text().strip().lower()
        self._busy = True
        self.table.setRowCount(0)
        modules = sorted(self.app.store.list_modules(),
                         key=lambda m: (m.category, m.id))
        row = 0
        for m in modules:
            if cat != "全部" and m.category != cat:
                continue
            if kw and kw not in m.full_id.lower() and kw not in m.name.lower():
                continue
            self.table.insertRow(row)
            # 勾选列
            ck = QtWidgets.QTableWidgetItem()
            ck.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
            ck.setCheckState(QtCore.Qt.Checked if m.full_id in self.app.selected
                             else QtCore.Qt.Unchecked)
            self.table.setItem(row, COL_CHECK, ck)
            fid = QtWidgets.QTableWidgetItem(m.full_id)
            fid.setData(QtCore.Qt.UserRole, m.full_id)
            self.table.setItem(row, COL_FID, fid)
            self.table.setItem(row, COL_NAME,
                               QtWidgets.QTableWidgetItem(m.name))
            self.table.setItem(row, COL_LAYER,
                               QtWidgets.QTableWidgetItem(m.layer))
            en = QtWidgets.QTableWidgetItem(
                "✓" if m.enabled else "✗")
            en.setForeground(QtCore.Qt.GlobalColor.green if m.enabled
                             else QtCore.Qt.GlobalColor.gray)
            self.table.setItem(row, COL_ENABLED, en)
            self.table.setItem(row, COL_ASSETS,
                               QtWidgets.QTableWidgetItem(
                                   ",".join(m.assets[:3])))
            row += 1
        self._busy = False
        self._on_selection()

    # ---------- 事件 ----------
    def _on_item_changed(self, item):
        if self._busy or item.column() != COL_CHECK:
            return
        fid = self.table.item(item.row(), COL_FID)
        if fid is None:
            return
        full_id = fid.data(QtCore.Qt.UserRole)
        if item.checkState() == QtCore.Qt.Checked:
            self.app.selected.add(full_id)
        else:
            self.app.selected.discard(full_id)
        self.selection_changed.emit()
        self.app.on_selection_changed()

    def _on_selection(self):
        if self._busy:
            return
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            self.check_view.setPlainText("（未选中模块：点选一行查看校验结果）")
            return
        row = rows[0].row()
        fid_item = self.table.item(row, COL_FID)
        if fid_item is None:
            return
        full_id = fid_item.data(QtCore.Qt.UserRole)
        m = self.app.store.get_module(full_id)
        if m is None:
            return
        installed = [x.full_id for x in self.app.store.list_modules()]
        text = (f"【{m.full_id} · {m.name}】\n"
                + common.validation_text(m, installed, self.app.current_pipeline))
        self.check_view.setPlainText(text)

    def _on_double(self, item):
        fid_item = self.table.item(item.row(), COL_FID)
        if fid_item is None:
            return
        full_id = fid_item.data(QtCore.Qt.UserRole)
        m = self.app.store.get_module(full_id)
        if m:
            common.module_detail_dialog(self, m)

    # ---------- 操作 ----------
    def _selected_rows(self):
        return [r.row() for r in self.table.selectionModel().selectedRows()]

    def import_file(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "导入模块文件", "", "模块文件 (*.md *.txt);;所有文件 (*)")
        if not path:
            return
        ok = self.app.zone_a.load_file(path)
        if ok:
            self.app.tabs.setCurrentIndex(0)

    def toggle_selected(self):
        rows = self._selected_rows()
        if not rows:
            common.info(self, "请先选中要操作的行。")
            return
        for r in rows:
            fid_item = self.table.item(r, COL_FID)
            if fid_item:
                self.app.store.toggle_module(
                    fid_item.data(QtCore.Qt.UserRole))
        self.app.on_modules_changed()

    def delete_selected(self):
        rows = self._selected_rows()
        if not rows:
            common.info(self, "请先选中要删除的行。")
            return
        names = [self.table.item(r, COL_FID).text() for r in rows
                 if self.table.item(r, COL_FID)]
        if QtWidgets.QMessageBox.question(
                self, "确认删除",
                f"删除以下模块？\n" + "\n".join(names)) \
                != QtWidgets.QMessageBox.StandardButton.Yes:
            return
        for r in rows:
            fid_item = self.table.item(r, COL_FID)
            if fid_item:
                fid = fid_item.data(QtCore.Qt.UserRole)
                self.app.store.remove_module(fid)
                self.app.selected.discard(fid)
        self.app.on_modules_changed()

    def _set_all(self, checked: bool):
        """全选/全不选：作用于当前筛选结果行。"""
        self._busy = True
        for r in range(self.table.rowCount()):
            it = self.table.item(r, COL_CHECK)
            fid_item = self.table.item(r, COL_FID)
            if it is None or fid_item is None:
                continue
            fid = fid_item.data(QtCore.Qt.UserRole)
            it.setCheckState(QtCore.Qt.Checked if checked
                             else QtCore.Qt.Unchecked)
            if checked:
                self.app.selected.add(fid)
            else:
                self.app.selected.discard(fid)
        self._busy = False
        self.selection_changed.emit()
        self.app.on_selection_changed()