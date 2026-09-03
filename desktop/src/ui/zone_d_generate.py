"""功能区 D · 装配生成：勾选集合 + 管线 → 校验 → 生成完整 MD 预览/保存。"""
from __future__ import annotations

from pathlib import Path

from PySide6 import QtCore, QtWidgets

from ..core.generator import generate_document, default_filename
from ..core.models import AssetPack
from ..core.validator import check_assembly
from . import common


class ZoneDGenerate(QtWidgets.QWidget):
    """④ 生成输出：标题/资产包选择 → 装配校验 → 文档预览 → 保存 MD。"""

    def __init__(self, app, parent=None):
        super().__init__(parent)
        self.app = app
        self.last_md = ""
        self._build_ui()

    # ---------- UI ----------
    def _build_ui(self):
        root = QtWidgets.QVBoxLayout(self)
        bar = QtWidgets.QHBoxLayout()
        bar.addWidget(QtWidgets.QLabel("文档标题:"))
        self.title_edit = QtWidgets.QLineEdit()
        self.title_edit.setPlaceholderText("留空则按管线生成默认标题")
        bar.addWidget(self.title_edit, 1)
        bar.addWidget(QtWidgets.QLabel("资产包:"))
        self.asset_combo = QtWidgets.QComboBox()
        bar.addWidget(self.asset_combo)
        b_gen = QtWidgets.QPushButton("生成预览")
        b_gen.clicked.connect(self.do_generate)
        bar.addWidget(b_gen)
        b_save = QtWidgets.QPushButton("保存为文件…")
        b_save.clicked.connect(self.do_save)
        bar.addWidget(b_save)
        root.addLayout(bar)

        split = QtWidgets.QSplitter(QtCore.Qt.Vertical)
        self.preview = QtWidgets.QPlainTextEdit()
        self.preview.setReadOnly(True)
        self.preview.setPlaceholderText(
            "点击「生成预览」输出装配完成的文档（含目录、逐层内容、资产附录）。")
        split.addWidget(self.preview)
        self.warn_view = QtWidgets.QPlainTextEdit()
        self.warn_view.setReadOnly(True)
        self.warn_view.setMaximumHeight(130)
        split.addWidget(self.warn_view)
        root.addWidget(split, 1)

        self.hint = QtWidgets.QLabel("提示：先到 ③管线装配 勾选参与模块。")
        self.hint.setWordWrap(True)
        root.addWidget(self.hint)

    # ---------- 数据 ----------
    def refresh_assets(self):
        self.asset_combo.blockSignals(True)
        cur = self.asset_combo.currentText()
        self.asset_combo.clear()
        self.asset_combo.addItem("（无资产包）", "")
        for a in self.app.store.list_asset_packs():
            self.asset_combo.addItem(f"{a.name}（{len(a.entries)}键）", a.name)
        idx = self.asset_combo.findText(cur)
        if idx >= 0:
            self.asset_combo.setCurrentIndex(idx)
        self.asset_combo.blockSignals(False)

    def refresh(self):
        self.refresh_assets()
        if self.app.current_pipeline:
            self.hint.setText(
                f"管线：{self.app.current_pipeline.name}　|　"
                f"已选 {len(self.app.selected)} 个模块。")

    # ---------- 动作 ----------
    def _collect_modules(self):
        """selected full_id → Module 列表（跳过已删除/停用可选）。"""
        out, missing = [], []
        for fid in sorted(self.app.selected):
            m = self.app.store.get_module(fid)
            if m is None:
                missing.append(fid)
            else:
                out.append(m)
        return out, missing

    def do_generate(self):
        pipe = self.app.current_pipeline
        if pipe is None:
            common.warn(self, "暂无管线，请先在 ③管线装配 加载管线库。")
            return
        modules, missing = self._collect_modules()
        if not modules:
            common.warn(self, "未选择任何有效模块，请先在 ②/③ 勾选。")
            return
        lines = []
        if missing:
            lines.append(f"⚠ 以下勾选模块已不存在，已跳过：{', '.join(missing)}")
        # 装配前整体检查
        issues = check_assembly(modules, pipe)
        lines.extend(issues)
        ap_name = self.asset_combo.currentData() or ""
        asset_pack = self.app.store.get_asset_pack(ap_name) if ap_name else None
        title = self.title_edit.text().strip()
        try:
            md, gen_warns = generate_document(
                pipe, modules, asset_pack=asset_pack, title=title)
        except Exception as exc:      # noqa: BLE001
            common.error(self, f"生成失败：{exc}")
            return
        self.last_md = md
        self.preview.setPlainText(md)
        warns = (["—— 装配检查 ——"] + issues +
                 ["", "—— 生成器提示 ——"] + (gen_warns or ["（无）"]))
        self.warn_view.setPlainText("\n".join(warns))
        self.hint.setText(
            f"✓ 生成完成：{len(modules)} 个模块 → {len(md)} 字符"
            + (f"，资产附录来自「{asset_pack.name}」" if asset_pack else "")
            + "。可点击「保存为文件…」。")

    def do_save(self):
        if not self.last_md:
            common.info(self, "请先生成预览。")
            return
        pipe = self.app.current_pipeline
        default_name = default_filename(pipe) if pipe else "output.md"
        start_dir = str(Path.home() / "Documents")
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "保存生成的 Markdown", str(Path(start_dir) / default_name),
            "Markdown (*.md);;所有文件 (*)")
        if not path:
            return
        if not path.lower().endswith(".md"):
            path += ".md"
        try:
            Path(path).write_text(self.last_md, encoding="utf-8")
        except Exception as exc:      # noqa: BLE001
            common.error(self, f"保存失败：{exc}")
            return
        self.app.status(f"已保存：{path}")