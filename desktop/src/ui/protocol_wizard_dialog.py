"""E2 协议定义向导对话框（v2.0.x：填表生成 protocol.yaml，不懂 Schema 可用）。

表单字段（结构化 → ProtocolForm → build_protocol_yaml）：
- id / name / pipeline 文本行
- module_id_range：逗号分隔（M66, M67）
- categories：逗号分隔
- modules：多行，每行 `id desc`（如 `M66 灵异事件触发`）
- mount_layers：多行，每行 `层名: id1, id2`（如 `P30 事件: M66`）
- core_only：默认勾选
生成 → yaml 预览 + self_check 自检 + 保存 protocol.yaml。
非目标：无 LLM 自然语言；登记沿用 v1 三要件（生成物自检可过 check14 粗校验）。
"""
from __future__ import annotations

from pathlib import Path

from PySide6 import QtCore, QtWidgets

from ..core.protocol_wizard import (
    ProtocolForm, build_protocol_yaml, self_check)
from . import common


def _parse_csv(text: str) -> list:
    return [x.strip() for x in text.replace("，", ",").split(",") if x.strip()]


def _parse_module_lines(text: str) -> list:
    """每行 `id desc` → [(id, desc)]。"""
    out = []
    for ln in text.splitlines():
        ln = ln.strip()
        if not ln:
            continue
        parts = ln.split(None, 1)
        out.append((parts[0], parts[1] if len(parts) > 1 else ""))
    return out


def _parse_mount_lines(text: str) -> dict:
    """每行 `层名: id1, id2` → {层名: {default:[...], available:[]}}。"""
    out: dict = {}
    for ln in text.splitlines():
        ln = ln.strip()
        if not ln or ":" not in ln:
            continue
        layer, rest = ln.split(":", 1)
        default = _parse_csv(rest)
        out[layer.strip()] = {"default": default, "available": []}
    return out


class ProtocolWizardDialog(QtWidgets.QDialog):
    """自定义协议定义向导。"""

    def __init__(self, app, parent=None):
        super().__init__(parent)
        self.app = app
        self.setWindowTitle("创建自定义协议 · 协议定义向导")
        self.resize(640, 620)
        self._build_ui()

    def _build_ui(self):
        root = QtWidgets.QVBoxLayout(self)
        tip = QtWidgets.QLabel(
            "定义第三方协议：填下表，向导自动生成合规 protocol.yaml（schema v2，"
            "结构字段自动填）。保存后按 02 §8.3 三要件登记即可被调度。")
        tip.setWordWrap(True)
        root.addWidget(tip)

        f = QtWidgets.QFormLayout()
        self.ed_id = QtWidgets.QLineEdit()
        self.ed_id.setPlaceholderText("如 灵异校园包（机读唯一标识）")
        self.ed_name = QtWidgets.QLineEdit()
        self.ed_name.setPlaceholderText("显示名，与 README 标题一致")
        self.ed_pipe = QtWidgets.QLineEdit("P02")
        self.ed_range = QtWidgets.QLineEdit()
        self.ed_range.setPlaceholderText("模块编号，逗号分隔（M91-M99 社区段）：M66, M67")
        self.ed_cat = QtWidgets.QLineEdit()
        self.ed_cat.setPlaceholderText("独占类别：灵异")
        f.addRow("包 id:", self.ed_id)
        f.addRow("包名:", self.ed_name)
        f.addRow("管线:", self.ed_pipe)
        f.addRow("编号清单:", self.ed_range)
        f.addRow("类别:", self.ed_cat)
        root.addLayout(f)

        self.ck_core = QtWidgets.QCheckBox("只依赖官方核心层（core_only，推荐）")
        self.ck_core.setChecked(True)
        root.addWidget(self.ck_core)

        root.addWidget(QtWidgets.QLabel("模块清单（每行 `id 描述`）："))
        self.ed_mods = QtWidgets.QPlainTextEdit()
        self.ed_mods.setPlaceholderText("M66 灵异事件触发\nM67 鬼怪出没规则")
        self.ed_mods.setMaximumHeight(90)
        root.addWidget(self.ed_mods)

        root.addWidget(QtWidgets.QLabel("挂载层（每行 `层名: 默认模块id`，逗号分隔）："))
        self.ed_mount = QtWidgets.QPlainTextEdit()
        self.ed_mount.setPlaceholderText(
            "P30 事件: M66\nP40 行为决策: M67\n"
            "（层名用 02 §5 挂载点键名，如 P00 数据基座 / P40 行为决策）")
        self.ed_mount.setMaximumHeight(80)
        root.addWidget(self.ed_mount)

        btns = QtWidgets.QHBoxLayout()
        b_gen = QtWidgets.QPushButton("生成 preview")
        b_gen.clicked.connect(self._generate)
        b_save = QtWidgets.QPushButton("保存 protocol.yaml…")
        b_save.clicked.connect(self._save)
        btns.addWidget(b_gen)
        btns.addWidget(b_save)
        btns.addStretch(1)
        root.addLayout(btns)

        self.preview = QtWidgets.QPlainTextEdit()
        self.preview.setReadOnly(True)
        self.preview.setPlaceholderText("生成的 protocol.yaml 预览 + 自检结果。")
        root.addWidget(self.preview, 1)

    # ---------- 动作 ----------
    def _collect_form(self) -> ProtocolForm:
        return ProtocolForm(
            id=self.ed_id.text().strip() or "未命名包",
            name=self.ed_name.text().strip() or "未命名包",
            pipeline=self.ed_pipe.text().strip() or "P01",
            module_id_range=_parse_csv(self.ed_range.text()),
            categories=_parse_csv(self.ed_cat.text()),
            core_only=self.ck_core.isChecked(),
            modules=_parse_module_lines(self.ed_mods.toPlainText()),
            mount_layers=_parse_mount_lines(self.ed_mount.toPlainText()),
        )

    def _generate(self):
        form = self._collect_form()
        text = build_protocol_yaml(form)
        self._last_text = text
        warns = self_check(text)
        head = ("—— 生成成功（protocol.yaml v2）——\n" if not warns
                else "—— 生成完成，自检警告 ——\n")
        self.preview.setPlainText(head + ("\n".join(f"⚠ {w}" for w in warns)
                                          + "\n\n" if warns else "") + text)
        self.app.status("协议已生成" + ("，自检通过" if not warns else ""), 4000)

    def _save(self):
        if not hasattr(self, "_last_text"):
            common.info(self, "先生成 preview。")
            return
        default = f"{self.ed_name.text().strip() or 'protocol'}.yaml"
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "保存 protocol.yaml", str(Path.home() / default),
            "YAML (*.yaml *.yml)")
        if not path:
            return
        Path(path).write_text(self._last_text, encoding="utf-8")
        common.info(self, f"✓ 已保存 {path}\n"
                          "下一步：把文件放入你的领域包目录（含 modules/assets），"
                          "按 02 §8.3 三要件登记注册。")
