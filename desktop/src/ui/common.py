"""GUI 公共小工具：字段摘要、校验结果文本化、模块信息弹窗等。"""
from __future__ import annotations

from PySide6 import QtWidgets

from ..core.models import Module, CATEGORIES
from ..core.validator import validate_module

CATEGORY_FILTER = ["全部"] + list(CATEGORIES)


def module_summary(m: Module, max_assets: int = 12) -> str:
    """把解析/校验后的模块格式化为多行可读文本。"""
    lines = [
        f"模块ID : {m.full_id or '(空)'}",
        f"名称   : {m.name or '(空)'}",
        f"分类   : {m.category}",
        f"挂载层 : {m.layer or '(空)'}  (九层: P00-P80)",
        f"可替换 : {'是' if m.replaceable else '否'}",
        f"依赖   : {', '.join(m.inputs) if m.inputs else '无'}",
        f"输出键 : {', '.join(m.outputs) if m.outputs else '(空)'}",
        f"发布事件: {', '.join(m.events_publish) if m.events_publish else '无'}",
        f"订阅事件: {', '.join(m.events_subscribe) if m.events_subscribe else '无'}",
        f"引用资产: {', '.join(m.assets[:max_assets]) if m.assets else '无'}"
        + (" …" if len(m.assets) > max_assets else ""),
        "核心逻辑:",
    ]
    logic = (m.logic or "(空)").strip()
    for ln in logic.splitlines()[:20]:
        lines.append(f"    {ln}")
    if len(logic.splitlines()) > 20:
        lines.append("    …（截断）")
    if m.source_md:
        lines.append(f"原始 MD : {len(m.source_md)} 字符")
    return "\n".join(lines)


def validation_text(m: Module, installed_ids: list[str],
                    pipeline=None) -> str:
    """校验模块并输出可读文本（错误前置 ✓/✗）。"""
    errors = validate_module(m, installed_ids=installed_ids, pipeline=pipeline)
    if not errors:
        return "✓ 校验通过：必填字段完整、层位合法、依赖齐全。"
    head = f"✗ 发现 {len(errors)} 个问题："
    return head + "\n" + "\n".join(f"  · {e}" for e in errors)


def module_detail_dialog(parent, m: Module) -> None:
    """模块详情弹窗（module.json 字段 + source.md 原文）。"""
    dlg = QtWidgets.QDialog(parent)
    dlg.setWindowTitle(f"模块详情 · {m.full_id}")
    dlg.resize(760, 620)
    lay = QtWidgets.QVBoxLayout(dlg)
    tabs = QtWidgets.QTabWidget()
    # 字段页
    fld = QtWidgets.QPlainTextEdit()
    fld.setReadOnly(True)
    fld.setPlainText(module_summary(m))
    tabs.addTab(fld, "字段摘要")
    # source.md 页
    src = QtWidgets.QPlainTextEdit()
    src.setReadOnly(True)
    src.setPlainText(m.source_md or "(无 source.md)")
    tabs.addTab(src, "source.md 原文")
    lay.addWidget(tabs)
    btn = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Close)
    btn.rejected.connect(dlg.reject)
    lay.addWidget(btn)
    dlg.exec()


def info(parent, text: str, title: str = "提示") -> None:
    QtWidgets.QMessageBox.information(parent, title, text)


def warn(parent, text: str, title: str = "警告") -> None:
    QtWidgets.QMessageBox.warning(parent, title, text)


def error(parent, text: str, title: str = "错误") -> None:
    QtWidgets.QMessageBox.critical(parent, title, text)
