"""功能区 C · 管线选择与排序：层结构树 + 按层勾选参与装配的模块。"""
from __future__ import annotations

from pathlib import Path

from PySide6 import QtCore, QtGui, QtWidgets

from ..core.models import Pipeline, fid_key
from ..core.pipeline_loader import discover_pipelines, load_pipeline_file
from . import common


class ZoneCPipeline(QtWidgets.QWidget):
    """③ 管线装配：左侧管线下拉，主区层树勾选模块。"""

    pipeline_changed = QtCore.Signal()
    selection_changed = QtCore.Signal()

    def __init__(self, app, parent=None):
        super().__init__(parent)
        self.app = app
        self._busy = False
        self._build_ui()

    # ---------- UI ----------
    def _build_ui(self):
        root = QtWidgets.QVBoxLayout(self)
        bar = QtWidgets.QHBoxLayout()
        bar.addWidget(QtWidgets.QLabel("管线:"))
        self.pipe_combo = QtWidgets.QComboBox()
        self.pipe_combo.currentIndexChanged.connect(self._on_pipe_switch)
        bar.addWidget(self.pipe_combo, 1)
        b_load = QtWidgets.QPushButton("加载管线库目录…")
        b_load.clicked.connect(self.load_pipeline_dir)
        bar.addWidget(b_load)
        b_reload = QtWidgets.QPushButton("重新载入")
        b_reload.clicked.connect(self.app.reload_pipelines)
        bar.addWidget(b_reload)
        root.addLayout(bar)

        self.desc_label = QtWidgets.QLabel()
        self.desc_label.setWordWrap(True)
        root.addWidget(self.desc_label)

        self.tree = QtWidgets.QTreeWidget()
        self.tree.setHeaderLabels(["层 / 模块（勾选 = 参与装配）", "说明"])
        self.tree.setColumnWidth(0, 420)
        self.tree.itemChanged.connect(self._on_tree_changed)
        root.addWidget(self.tree, 1)

        bottom = QtWidgets.QHBoxLayout()
        b_default = QtWidgets.QPushButton("按管线默认勾选")
        b_default.clicked.connect(self.apply_defaults)
        b_clear = QtWidgets.QPushButton("清空勾选")
        b_clear.clicked.connect(self.clear_selection)
        bottom.addWidget(b_default)
        bottom.addWidget(b_clear)
        bottom.addStretch(1)
        self.stat_label = QtWidgets.QLabel("已选 0 个模块")
        bottom.addWidget(self.stat_label)
        root.addLayout(bottom)

    # ---------- 填充 ----------
    def refresh_pipes(self, keep: str | None = None):
        """重填管线下拉（keep: 尝试保持当前管线 id）。"""
        self._busy = True
        self.pipe_combo.blockSignals(True)
        self.pipe_combo.clear()
        idx_keep = 0
        for i, p in enumerate(self.app.pipelines):
            self.pipe_combo.addItem(f"{p.id} · {p.name}", p.id)
            if keep and p.id == keep:
                idx_keep = i
        self.pipe_combo.setCurrentIndex(idx_keep)
        self.pipe_combo.blockSignals(False)
        self._busy = False
        self.refresh()

    def refresh(self):
        """依据当前管线重建层树（勾选状态与 app.selected 同步）。"""
        pipe = self.app.current_pipeline
        if pipe is None:
            self.desc_label.setText("（无管线：请加载管线库或重新载入）")
            self.tree.clear()
            self.stat_label.setText("已选 0 个模块")
            return
        self.desc_label.setText(
            f"{pipe.description or '（无描述）'}　｜　结构：{pipe.structure_type}"
            f"　｜　{len(pipe.layers)} 层")
        modules = self.app.store.list_modules()
        by_layer: dict[str, list] = {}
        for m in modules:
            by_layer.setdefault(m.layer, []).append(m)
        self._busy = True
        self.tree.clear()
        for layer in pipe.layers:
            top = QtWidgets.QTreeWidgetItem(
                [f"层 {layer.id} · {layer.name}", layer.description or ""])
            top.setFlags(QtCore.Qt.ItemIsEnabled)
            if layer.optional:
                top.setText(0, top.text(0) + "（可选层）")
            gray = QtGui.QBrush(QtCore.Qt.GlobalColor.gray)
            allowed = {fid_key(a) for a in (layer.allowed_modules or [])}
            for m in sorted(by_layer.get(layer.id, []),
                            key=lambda x: (x.category, x.id)):
                child = QtWidgets.QTreeWidgetItem(
                    [f"{m.full_id}  {m.name}", f"依赖:{len(m.inputs)} "
                     f"输出:{len(m.outputs)}"])
                child.setData(0, QtCore.Qt.UserRole, m.full_id)
                child.setFlags(QtCore.Qt.ItemIsUserCheckable
                               | QtCore.Qt.ItemIsEnabled)
                child.setCheckState(
                    0, QtCore.Qt.Checked if m.full_id in self.app.selected
                    else QtCore.Qt.Unchecked)
                if allowed and fid_key(m.full_id) not in allowed:
                    child.setForeground(0, gray)
                    child.setToolTip(
                        0, "⚠ 不在当前层允许集内（可强制勾选，生成时给出提示）")
                if not m.enabled:
                    child.setForeground(0, gray)
                    child.setToolTip(0, "该模块已停用（可在②模块库启用）")
                top.addChild(child)
            self.tree.addTopLevelItem(top)
            top.setExpanded(True)
        self._busy = False
        self._update_stat()

    def _update_stat(self):
        self.stat_label.setText(f"已选 {len(self.app.selected)} 个模块")

    # ---------- 事件 ----------
    def _on_pipe_switch(self, _idx):
        if self._busy:
            return
        self.app.current_pipeline_id = self.pipe_combo.currentData()
        self.app.store.set_config("pipeline", self.app.current_pipeline_id)
        self.pipeline_changed.emit()
        self.app.on_pipeline_changed()
        self.refresh()

    def _on_tree_changed(self, item, col):
        if self._busy or col != 0 or not item.parent():
            return
        # 顶层=层，子项=模块（full_id 存于 UserRole）
        full_id = item.data(0, QtCore.Qt.UserRole)
        if not full_id:
            return
        if item.checkState(0) == QtCore.Qt.Checked:
            self.app.selected.add(full_id)
        else:
            self.app.selected.discard(full_id)
        self._update_stat()
        self.selection_changed.emit()
        self.app.on_selection_changed()

    # ---------- 操作 ----------
    def load_pipeline_dir(self):
        path = QtWidgets.QFileDialog.getExistingDirectory(
            self, "选择管线库目录（03_管线库）", str(Path.home()))
        if not path:
            return
        pipes = discover_pipelines(path)
        if not pipes:
            common.warn(self, "该目录下未发现可用管线（.md/.yaml）。")
            return
        # 更新缓存并刷新
        self.app.pipelines = pipes
        self.app.store.save_cache(
            "pipelines", [p.to_json() for p in pipes])
        self.app.store.set_config("pipeline_dir", path)
        self.app.current_pipeline_id = pipes[0].id
        self.refresh_pipes(keep=pipes[0].id)
        self.app.on_pipeline_changed()
        common.info(self, f"已加载 {len(pipes)} 条管线并写入缓存。")

    def apply_defaults(self):
        pipe = self.app.current_pipeline
        if pipe is None:
            return
        modules = {fid_key(m.full_id): m.full_id
                   for m in self.app.store.list_modules()}
        picked: set[str] = set()
        for layer in pipe.layers:
            for d in layer.default_modules or []:
                k = fid_key(d)
                if k in modules:
                    picked.add(modules[k])
        if picked:
            self.app.selected = picked
            common.info(self, f"已按管线默认勾选 {len(picked)} 个模块。")
        else:
            common.info(self, "当前管线未声明默认模块（default_modules 为空），"
                              "请在左侧手动勾选。")
        self.refresh()
        self.app.on_selection_changed()

    def clear_selection(self):
        self.app.selected.clear()
        self.refresh()
        self.app.on_selection_changed()