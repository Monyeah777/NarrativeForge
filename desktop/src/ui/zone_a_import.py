"""功能区 A · 拖入解析：接受 md/文本 → 解析为 Module → 展示/校验/安装。"""
from __future__ import annotations

from pathlib import Path

from PySide6 import QtCore, QtWidgets

from ..core.parser import parse_module
from . import common


class ZoneAImport(QtWidgets.QWidget):
    """① 导入解析：文本粘贴 / 文件拖入 / 打开文件 三种入口。"""

    module_installed = QtCore.Signal()

    def __init__(self, app, parent=None):
        super().__init__(parent)
        self.app = app          # MainWindow（提供 store / refresh 联动）
        self.last_parsed = None
        self.last_path = ""
        self._build_ui()

    # ---------- UI ----------
    def _build_ui(self):
        root = QtWidgets.QVBoxLayout(self)
        tip = QtWidgets.QLabel(
            "将 AI 填充完成的模块 .md/.txt 拖入本窗口任意位置，"
            "或粘贴/打开文本后点击「解析」。解析结果可即时校验并安装入库。")
        tip.setWordWrap(True)
        root.addWidget(tip)

        split = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        # 左：输入
        left = QtWidgets.QGroupBox("模块原文（指令集式 / 仓库式均支持）")
        ll = QtWidgets.QVBoxLayout(left)
        self.editor = QtWidgets.QPlainTextEdit()
        self.editor.setPlaceholderText(
            "# 模块 情感:M22\n\n## 基本信息\n- 名称：...\n- 挂载层：P40\n"
            "- 可替换：是\n- 输入依赖：...\n- 输出键：...\n\n## 核心逻辑\n...\n\n"
            "## 引用的资产\n- ...\n")
        self.editor.textChanged.connect(self._clear_parsed)
        ll.addWidget(self.editor)
        # 右：结果
        right = QtWidgets.QGroupBox("解析与校验结果")
        rl = QtWidgets.QVBoxLayout(right)
        self.result_view = QtWidgets.QPlainTextEdit()
        self.result_view.setReadOnly(True)
        rl.addWidget(self.result_view)
        split.addWidget(left)
        split.addWidget(right)
        split.setSizes([460, 460])
        root.addWidget(split, 1)

        btns = QtWidgets.QHBoxLayout()
        b_parse = QtWidgets.QPushButton("① 解析文本")
        b_open = QtWidgets.QPushButton("打开文件…")
        b_install = QtWidgets.QPushButton("② 安装入库")
        b_install.setEnabled(False)
        b_clear = QtWidgets.QPushButton("清空")
        btns.addWidget(b_parse)
        btns.addWidget(b_open)
        btns.addStretch(1)
        btns.addWidget(b_install)
        btns.addWidget(b_clear)
        root.addLayout(btns)

        b_parse.clicked.connect(self.do_parse)
        b_open.clicked.connect(self.open_file)
        b_install.clicked.connect(self.do_install)
        b_clear.clicked.connect(self.do_clear)
        self.b_install = b_install

    # ---------- 外部入口 ----------
    def load_file(self, path: str | Path) -> bool:
        """拖入/打开统一入口。返回是否解析成功。"""
        p = Path(path)
        try:
            text = p.read_text(encoding="utf-8")
        except Exception as exc:      # noqa: BLE001
            common.error(self, f"读取文件失败：{exc}")
            return False
        self.last_path = str(p)
        self.editor.setPlainText(text)
        return self.do_parse()

    def load_text(self, text: str, source: str = "") -> bool:
        self.last_path = source
        self.editor.setPlainText(text)
        return self.do_parse()

    # ---------- 动作 ----------
    def _clear_parsed(self):
        self.last_parsed = None
        if hasattr(self, "b_install"):
            self.b_install.setEnabled(False)

    def do_parse(self) -> bool:
        text = self.editor.toPlainText().strip()
        if not text:
            common.warn(self, "请先粘贴或打开模块文本。")
            return False
        try:
            m = parse_module(text)
        except Exception as exc:      # noqa: BLE001
            common.error(self, f"解析失败：{exc}")
            self.result_view.setPlainText(f"✗ 解析异常：{exc}")
            return False
        self.last_parsed = m
        installed = [x.full_id for x in self.app.store.list_modules()]
        pipe = self.app.current_pipeline
        body = "【解析成功】\n\n" + common.module_summary(m)
        body += "\n\n【即时校验】\n" + common.validation_text(m, installed, pipe)
        if not m.source_md and self.last_path:
            body += f"\n\n（未读到 source.md 原文，来自：{self.last_path}）"
        self.result_view.setPlainText(body)
        self.b_install.setEnabled(bool(m.id and m.name))
        return True

    def open_file(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "打开模块文件", "", "模块文件 (*.md *.txt);;所有文件 (*)")
        if path:
            self.load_file(path)

    def do_install(self):
        if self.last_parsed is None:
            return
        try:
            self.app.store.save_module(self.last_parsed)
        except Exception as exc:      # noqa: BLE001
            common.error(self, f"安装失败：{exc}")
            return
        m = self.last_parsed
        self.result_view.appendPlainText(
            f"\n✓ 已安装：{m.full_id} · {m.name}"
            f"（目录 modules/{m.category}/{m.id}_{m.name}/）")
        self.module_installed.emit()
        self.app.on_modules_changed()

    def do_clear(self):
        self.editor.clear()
        self.result_view.clear()
        self.last_path = ""
        self.b_install.setEnabled(False)