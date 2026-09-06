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
        b_import_ext = QtWidgets.QPushButton("读入外部产物…")
        b_install = QtWidgets.QPushButton("② 安装入库")
        b_install.setEnabled(False)
        b_clear = QtWidgets.QPushButton("清空")
        btns.addWidget(b_parse)
        btns.addWidget(b_open)
        btns.addWidget(b_import_ext)
        btns.addStretch(1)
        btns.addWidget(b_install)
        btns.addWidget(b_clear)
        root.addLayout(btns)

        b_parse.clicked.connect(self.do_parse)
        b_open.clicked.connect(self.open_file)
        b_import_ext.clicked.connect(self.import_external)
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
        self._external_ir = None
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

    def import_external(self):
        """读入外部产物（SKILL.md / chara_card_v3 / world.json）→ IR 预览。

        38 W1（34 遗留 F2 · ROADMAP A4）：接 core.import_adapter 宽容层解析，
        薄接线——调 core 库 + 复用 editor/result 既有形态；登记走 store 装载
        （与 nf import --register 同源：save_module 幂等）。
        """
        from ..core import import_adapter as imp
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "读入外部产物",
            "", "外部产物 (*.md *.json);;SKILL.md (*.md);;JSON (*.json)")
        if not path:
            return
        p = Path(path)
        try:
            if p.suffix.lower() == ".md":
                res = imp.parse_skill(p.read_text(encoding="utf-8"),
                                      skill_dir=p.parent)
                self._render_external_skill(res, p)
            else:  # .json → chara_card_v3 / world.json
                data = __import__("json").loads(
                    p.read_text(encoding="utf-8"))
                res = imp.parse_ccv3(data) if "chara" in data or \
                    "spec" in data else imp.parse_ccv3({}, data)
                self._render_external_ccv3(res, p)
        except Exception as exc:      # noqa: BLE001
            common.error(self, f"读入外部产物失败：{exc}")
            self.result_view.setPlainText(f"✗ 读入异常：{exc}")
            return

    def _render_external_skill(self, res, path: Path) -> None:
        """SKILL 解析结果 → 结果区（nf 模式 IR 预览 + 登记入口）。"""
        if res.mode == "nf" and res.ir is not None:
            ir = res.ir
            mods = [m for lay in ir.layers for m in lay.modules] \
                + list(ir.extra_modules)
            body = f"【外部 SKILL 读入 · nf 结构】{path.name}\n\n" \
                f"管线：{ir.pipeline_id or '-'} · 模块 {len(mods)} 个"
            if getattr(res, "bundled_resources", None):
                body += f"\n随行资源：{len(res.bundled_resources)} 项"
            for m in mods[:8]:
                body += f"\n  · {m.full_id} {m.name}"
            if len(mods) > 8:
                body += f"\n  … 共 {len(mods)} 个"
            self._external_ir = ir
        else:
            self._external_ir = None
            body = f"【外部 SKILL 读入 · 宽容层】{path.name}\n\n" \
                f"name: {res.frontmatter.get('name', '-')}\n" \
                f"description: {res.frontmatter.get('description', '-')}\n\n" \
                f"{res.body[:400]}"
            if res.warnings:
                body += "\n\n警告：\n" + "\n".join(
                    f"  ⚠ {w}" for w in res.warnings[:5])
        self.result_view.setPlainText(body)
        # 可登记（nf 结构）→ 启用安装按钮（do_install 需 last_parsed，
        # 这里登记 IR 用独立入口——复用安装按钮语义改为登记 IR）
        self.b_install.setEnabled(self._external_ir is not None)

    def _render_external_ccv3(self, res, path: Path) -> None:
        """CCV3 解析结果 → 结果区（IR 模块预览 + 登记入口）。"""
        mods = [m for lay in res.ir.layers for m in lay.modules] \
            + list(res.ir.extra_modules) if res.ir is not None else []
        if res.ir is not None:
            self._external_ir = res.ir
            body = f"【外部 CCV3 读入】{path.name}\n\n" \
                f"管线：{res.ir.pipeline_id or '-'} · 模块 {len(mods)} 个"
            for m in mods[:8]:
                body += f"\n  · {m.full_id} {m.name}"
            self.b_install.setEnabled(True)
        else:
            self._external_ir = None
            body = f"【外部 CCV3 读入 · 宽容层】{path.name}\n" \
                f"（未还原 IR，仅 raw 保留）"
            self.b_install.setEnabled(False)
        self.result_view.setPlainText(body)

    def do_install(self):
        # 外部产物登记路径（38 W1）：_external_ir 在场 → 装载 IR 模块
        ext_ir = getattr(self, "_external_ir", None)
        if ext_ir is not None:
            return self._install_external_ir(ext_ir)
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

    def _install_external_ir(self, ir) -> None:
        """登记外部产物 IR 模块入 store（与 nf import --register 同源语义）。

        IRModule → Module 显式转换（full_id 拆 cat:num，同 scripts/nf.py
        _cmd_import 既有接法）；幂等：save_module 覆盖同名（只增不删纪律）。
        """
        from ..core.models import Module
        mods = [m for lay in ir.layers for m in lay.modules] \
            + list(ir.extra_modules)
        n = 0
        for im in mods:
            try:
                fid = im.full_id
                cat, num = fid.rsplit(":", 1) if ":" in fid else ("通用类", fid)
                self.app.store.save_module(Module(
                    id=num, name=im.name, category=cat,
                    layer=im.layer, source_md=im.content))
                n += 1
            except Exception as exc:      # noqa: BLE001
                common.error(self, f"登记 {im.full_id} 失败：{exc}")
        self.result_view.appendPlainText(
            f"\n✓ 已登记外部产物模块 {n} 个（store 幂等装载）")
        self.module_installed.emit()
        self.app.on_modules_changed()
        self._external_ir = None
        self.b_install.setEnabled(False)

    def do_clear(self):
        self.editor.clear()
        self.result_view.clear()
        self.last_path = ""
        self.b_install.setEnabled(False)