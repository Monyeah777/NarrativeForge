"""功能区 G · 社区拉取：模块库导入（MVP 以本地导入代替 GitHub 拉取）。

阶段①（MVP）：目录批量导入 module.json 模块 / 单个模板文件导入。
阶段②（规划）：接入 NarrativeForge 社区索引（GitHub）实现拉取/更新，
            届时替换下方「从 GitHub 拉取（占位）」按钮为真实下载逻辑。
"""
from __future__ import annotations
import json
from pathlib import Path
from PySide6 import QtCore, QtWidgets
from ..core.models import Module
from ..core.parser import parse_module
from . import common


class ZoneGCommunity(QtWidgets.QWidget):
    """⑦ 社区拉取：批量导入本地模块仓库 / 单文件模板入库。"""
    def __init__(self, app, parent=None):
        super().__init__(parent)
        self.app = app
        self._build_ui()

    # ---------- UI ----------
    def _build_ui(self):
        root = QtWidgets.QVBoxLayout(self)

        desc = QtWidgets.QLabel(
            "社区拉取：把他人发布的模块（module.json 目录结构）或"
            "单份规范模板批量导入本地模块库。\n"
            "阶段②将接入 NarrativeForge 社区索引（GitHub）实现在线拉取与更新。")
        desc.setWordWrap(True)
        root.addWidget(desc)

        grp_dir = QtWidgets.QGroupBox("① 批量导入：模块仓库目录（内含 module.json）")
        gd = QtWidgets.QVBoxLayout(grp_dir)
        row = QtWidgets.QHBoxLayout()
        b_dir = QtWidgets.QPushButton("选择目录并导入…")
        b_dir.clicked.connect(self.do_import_dir)
        row.addWidget(b_dir)
        row.addStretch(1)
        self.dir_label = QtWidgets.QLabel("（尚未导入）")
        self.dir_label.setWordWrap(True)
        row.addWidget(self.dir_label, 1)
        gd.addLayout(row)
        root.addWidget(grp_dir)

        grp_file = QtWidgets.QGroupBox("② 单文件导入：规范模板 .md / module.json")
        gf = QtWidgets.QHBoxLayout(grp_file)
        b_file = QtWidgets.QPushButton("选择文件并导入…")
        b_file.clicked.connect(self.do_import_file)
        gf.addWidget(b_file)
        gf.addStretch(1)
        root.addWidget(grp_file)

        grp_gh = QtWidgets.QGroupBox("③ 创建自定义协议（E2 协议定义向导）")
        gg = QtWidgets.QHBoxLayout(grp_gh)
        b_wizard = QtWidgets.QPushButton("创建自定义协议…")
        b_wizard.clicked.connect(self.do_open_wizard)
        b_wizard.setToolTip("v2.0.x-E2：填表生成合规 protocol.yaml（不懂 Schema 也能定义第三方协议）")
        gg.addWidget(b_wizard)
        gg.addStretch(1)
        root.addWidget(grp_gh)

        self.result = QtWidgets.QLabel("")
        self.result.setWordWrap(True)
        self.result.setStyleSheet("color: #1a6e2a;")
        root.addWidget(self.result)
        root.addStretch(1)

    # ---------- E2 协议定义向导 ----------
    def do_open_wizard(self):
        """打开自定义协议向导对话框（E2）。"""
        from .protocol_wizard_dialog import ProtocolWizardDialog
        dlg = ProtocolWizardDialog(self.app, self)
        dlg.exec()

    # ---------- 导入逻辑 ----------
    def _load_module_json(self, jfile: Path) -> Module | None:
        """读取 module.json（同目录 source.md 优先回填原文）。"""
        try:
            data = json.loads(jfile.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                return None
            m = Module.from_json(data)
            src = jfile.parent / "source.md"
            if src.exists():
                m.source_md = src.read_text(encoding="utf-8")
            return m if m.id else None
        except Exception:
            return None

    def do_import_dir(self):
        """递归扫描所选目录下的 module.json，逐个安装。"""
        path = QtWidgets.QFileDialog.getExistingDirectory(
            self, "选择模块仓库目录", str(Path.home()))
        if not path:
            return
        hits = sorted(Path(path).rglob("module.json"))
        if not hits:
            common.warn(self, "该目录下未发现任何 module.json，"
                              "请确认选择的是模块仓库/导出目录。")
            return
        ok_n, skip_n, skipped = 0, 0, []
        for jf in hits:
            m = self._load_module_json(jf)
            if m is None:
                skip_n += 1
                skipped.append(str(jf.parent.name))
                continue
            try:
                self.app.store.save_module(m)
                ok_n += 1
            except Exception:          # noqa: BLE001
                skip_n += 1
                skipped.append(str(jf.parent.name))
        # 清除被覆盖/删除模块可能残留的勾选
        self.app.selected = {
            f for f in self.app.selected
            if self.app.store.get_module(f) is not None}
        self.app.on_modules_changed()
        self.dir_label.setText(f"目录：{path}")
        msg = (f"✓ 批量导入完成：成功 {ok_n} 个"
               + (f"，跳过 {skip_n} 个（{', '.join(skipped[:5])}"
                  + (" …" if skip_n > 5 else "") + "）" if skip_n else ""))
        self.result.setText(msg)
        common.info(self, msg)

    def do_import_file(self):
        """单文件导入：.md 规范模板走解析器，.json 走 module.json 读取。"""
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "选择模块文件", "",
            "模块文件 (*.md *.txt *.json);;所有文件 (*)")
        if not path:
            return
        f = Path(path)
        m = None
        if f.suffix.lower() == ".json":
            m = self._load_module_json(f)
        else:
            try:
                text = f.read_text(encoding="utf-8")
                m = parse_module(text)
            except Exception as exc:   # noqa: BLE001
                common.error(self, f"解析失败：{exc}")
                return
        if m is None or not m.id:
            common.error(self, "未能从文件中识别出模块（缺少 id 等核心字段）。")
            return
        if not m.source_md and f.suffix.lower() != ".json":
            m.source_md = f.read_text(encoding="utf-8")
        try:
            self.app.store.save_module(m)
        except Exception as exc:       # noqa: BLE001
            common.error(self, f"安装失败：{exc}")
            return
        self.app.selected = {
            f_ for f_ in self.app.selected
            if self.app.store.get_module(f_) is not None}
        self.app.on_modules_changed()
        self.result.setText(f"✓ 已导入：{m.full_id} {m.name}")
        common.info(self, f"已导入并安装模块「{m.full_id} · {m.name}」。")