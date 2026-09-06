"""功能区 E · 资产管理：资产包浏览 / 新建 / 导入目录 / 删除 / 条目查看。

资产包 = { name, version, entries: {资产键: 内容}, source_dir }（asset.json）。
对接 core.storage.Store 的 list/get/save/remove_asset_pack 四方法。
"""
from __future__ import annotations
import json
from pathlib import Path
from PySide6 import QtCore, QtWidgets
from ..core.models import AssetPack
from . import common


def _value_preview(v, maxlen: int = 120) -> str:
    """把 entries 里的值（str/list/dict）格式化为单行预览。"""
    if isinstance(v, str):
        s = v if v else "(空字符串)"
    elif isinstance(v, (list, dict)):
        try:
            s = json.dumps(v, ensure_ascii=False)[:maxlen]
        except Exception:
            s = repr(v)
    else:
        s = str(v)
    return s if len(s) <= maxlen else s[:maxlen] + "…"


class ZoneEAssets(QtWidgets.QWidget):
    """⑤ 资产管理：左侧包列表，右侧详情与条目表。"""
    def __init__(self, app, parent=None):
        super().__init__(parent)
        self.app = app
        self._packs: list[AssetPack] = []
        self._build_ui()
        self.refresh()

    # ---------- UI ----------
    def _build_ui(self):
        root = QtWidgets.QHBoxLayout(self)

        left = QtWidgets.QVBoxLayout()
        left.addWidget(QtWidgets.QLabel("资产包："))
        self.pack_list = QtWidgets.QListWidget()
        self.pack_list.currentRowChanged.connect(self._on_select)
        left.addWidget(self.pack_list, 1)
        btns = QtWidgets.QGridLayout()
        b_new = QtWidgets.QPushButton("新建…")
        b_imp = QtWidgets.QPushButton("导入目录…")
        b_del = QtWidgets.QPushButton("删除")
        b_ref = QtWidgets.QPushButton("刷新")
        for w, r, c in ((b_new, 0, 0), (b_imp, 0, 1),
                        (b_del, 1, 0), (b_ref, 1, 1)):
            btns.addWidget(w, r, c)
        b_new.clicked.connect(self.do_new)
        b_imp.clicked.connect(self.do_import_dir)
        b_del.clicked.connect(self.do_delete)
        b_ref.clicked.connect(self.refresh)
        left.addLayout(btns)
        root.addLayout(left, 2)

        right = QtWidgets.QVBoxLayout()
        self.info_label = QtWidgets.QLabel("（未选择资产包）")
        self.info_label.setWordWrap(True)
        right.addWidget(self.info_label)
        right.addWidget(QtWidgets.QLabel("条目（资产键 → 内容预览）："))
        self.entry_table = QtWidgets.QTableWidget(0, 3)
        self.entry_table.setHorizontalHeaderLabels(["键", "类型", "内容预览"])
        self.entry_table.setEditTriggers(
            QtWidgets.QAbstractItemView.NoEditTriggers)
        self.entry_table.verticalHeader().setVisible(False)
        hh = self.entry_table.horizontalHeader()
        hh.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch)
        right.addWidget(self.entry_table, 1)
        root.addLayout(right, 3)

    # ---------- 数据 ----------
    def refresh(self):
        """重载包列表；尽力保持当前选择行。"""
        cur = self.pack_list.currentRow()
        self._packs = sorted(self.app.store.list_asset_packs(),
                             key=lambda a: a.name)
        self.pack_list.clear()
        for a in self._packs:
            tip = (f"版本 {a.version} · {len(a.entries)} 键"
                   + (f"\n来源: {a.source_dir}" if a.source_dir else ""))
            it = QtWidgets.QListWidgetItem(
                f"{a.name}　（{len(a.entries)}键）")
            it.setToolTip(tip)
            self.pack_list.addItem(it)
        if 0 <= cur < self.pack_list.count():
            self.pack_list.setCurrentRow(cur)
        elif self._packs:
            self.pack_list.setCurrentRow(0)
        self._on_select(self.pack_list.currentRow())

    def _current(self) -> AssetPack | None:
        r = self.pack_list.currentRow()
        if 0 <= r < len(self._packs):
            return self._packs[r]
        return None

    def _on_select(self, _row):
        a = self._current()
        self.entry_table.setRowCount(0)
        if a is None:
            self.info_label.setText("（未选择资产包）")
            return
        self.info_label.setText(
            f"名称：{a.name}　|　版本：{a.version}　|　"
            f"条目：{len(a.entries)} 键"
            + (f"　|　来源目录：{a.source_dir}" if a.source_dir else "")
            + (f"　|　安装于：{a.installed_at}" if a.installed_at else ""))
        keys = sorted(a.entries.keys())
        for r, k in enumerate(keys):
            v = a.entries[k]
            self.entry_table.insertRow(r)
            self.entry_table.setItem(
                r, 0, QtWidgets.QTableWidgetItem(k))
            self.entry_table.setItem(
                r, 1, QtWidgets.QTableWidgetItem(
                    type(v).__name__ if not isinstance(v, str)
                    else ("str" if v else "str(空)")))
            self.entry_table.setItem(
                r, 2, QtWidgets.QTableWidgetItem(_value_preview(v)))

    # ---------- 操作 ----------
    def do_new(self):
        name, ok = QtWidgets.QInputDialog.getText(
            self, "新建资产包", "资产包名称：",
            text=f"新资产包{len(self._packs) + 1}")
        if not ok or not name.strip():
            return
        a = AssetPack(name=name.strip(), version="1.0.0")
        try:
            self.app.store.save_asset_pack(a)
        except Exception as exc:      # noqa: BLE001
            common.error(self, f"创建失败：{exc}")
            return
        self.refresh()
        self._select_name(a.name)
        self._notify()
        common.info(self, f"已创建空资产包「{a.name}」。"
                          "可在 asset.json 中补充 entries 后重新导入。")

    def do_import_dir(self):
        """选择含 asset.json 的资产包目录（或模块资产目录），导入为资产包。"""
        path = QtWidgets.QFileDialog.getExistingDirectory(
            self, "选择资产包目录（内含 asset.json）", str(Path.home()))
        if not path:
            return
        d = Path(path)
        cand = d / "asset.json"
        if not cand.exists():
            hits = list(d.rglob("asset.json"))
            if hits:
                cand = hits[0]
            else:
                common.warn(self, "所选目录下未找到 asset.json，无法导入。")
                return
        try:
            data = json.loads(cand.read_text(encoding="utf-8"))
            a = AssetPack.from_json(data if isinstance(data, dict) else {})
        except Exception as exc:      # noqa: BLE001
            common.error(self, f"解析 asset.json 失败：{exc}")
            return
        if not a.name:
            a.name = d.name
        a.source_dir = str(cand.parent)
        try:
            self.app.store.save_asset_pack(a)
        except Exception as exc:      # noqa: BLE001
            common.error(self, f"导入失败：{exc}")
            return
        self.refresh()
        self._select_name(a.name)
        self._notify()
        common.info(self, f"已导入资产包「{a.name}」"
                          f"（{len(a.entries)} 键）。")

    def do_delete(self):
        a = self._current()
        if a is None:
            common.info(self, "请先在左侧选择要删除的资产包。")
            return
        if QtWidgets.QMessageBox.question(
                self, "确认删除",
                f"删除资产包「{a.name}」（{len(a.entries)} 键）？"
                "\n此操作仅移除库内登记，不影响源目录文件。") \
                != QtWidgets.QMessageBox.StandardButton.Yes:
            return
        self.app.store.remove_asset_pack(a.name)
        self.refresh()
        self._notify()
        common.info(self, f"已删除资产包「{a.name}」。")

    # ---------- 辅助 ----------
    def _select_name(self, name: str):
        for i in range(self.pack_list.count()):
            if self.pack_list.item(i).text().startswith(name):
                self.pack_list.setCurrentRow(i)
                break

    def _notify(self):
        """资产库变化 → 通知 ④生成 刷新资产下拉。"""
        if hasattr(self.app, "zone_d") and self.app.zone_d is not None:
            self.app.zone_d.refresh_assets()
        if hasattr(self.app, "status"):
            self.app.status(f"资产包库已刷新：{len(self._packs)} 个")
