"""功能区 G · 本地资源发现与装配中心（E4 模块市场雏形 + E5 社区仓库盘点）。

阶段①（E4 + E5，2.0 收口）：检索驱动一站式视图——消费 retriever.search
module/asset_pack/pipeline/protocol（本地已装/在册）+ community_module /
community_pipeline（community 仓库盘点：可发现 → 一键装载入库）；module
可追加进装配集、pipeline 可设为当前管线、社区项可装载入库后转装配/选用。
阶段②（规划）：接入 NarrativeForge 社区索引（GitHub）实现在线拉取/更新，
            届时替换「从 GitHub 拉取（占位）」按钮为真实下载逻辑。
"""
from __future__ import annotations

import json
from pathlib import Path
from PySide6 import QtCore, QtWidgets
from ..core.models import Module
from ..core.parser import parse_module
from ..core.retriever import search
from . import common

KIND_LABELS = [("全部", None), ("模块", "module"), ("资产包", "asset_pack"),
               ("管线", "pipeline"), ("协议", "protocol"),
               ("社区模块", "community_module"), ("社区管线", "community_pipeline")]


class ZoneGCommunity(QtWidgets.QWidget):
    """⑦ 本地资源发现与装配：检索四类资源 → 从结果加入装配/切换管线/选用资产。"""
    def __init__(self, app, parent=None):
        super().__init__(parent)
        self.app = app
        self._hits = []          # 最近一次检索结果（Hit 列表，行 UserRole 同源）
        self._busy = False
        self._build_ui()

    # ---------- UI ----------
    def _build_ui(self):
        root = QtWidgets.QVBoxLayout(self)

        desc = QtWidgets.QLabel(
            "资源发现与装配中心：检索已安装模块 / 资产包 / 管线 / 在册协议，"
            "以及 community 社区仓库可装载模块 / 管线。\n"
            "本地资源可直接加入装配、切管线、选资产；社区项未装可一键装载入库，"
            "已装则转装配。在线社区拉取为阶段②规划，未接入。")
        desc.setWordWrap(True)
        root.addWidget(desc)

        # 检索行
        bar = QtWidgets.QHBoxLayout()
        bar.addWidget(QtWidgets.QLabel("类型:"))
        self.kind_combo = QtWidgets.QComboBox()
        for label, val in KIND_LABELS:
            self.kind_combo.addItem(label, val)
        bar.addWidget(self.kind_combo)
        self.query_edit = QtWidgets.QLineEdit()
        self.query_edit.setPlaceholderText("检索关键词（留空 = 列出该类型全部）")
        self.query_edit.setClearButtonEnabled(True)
        self.query_edit.returnPressed.connect(self.do_search)
        bar.addWidget(self.query_edit, 1)
        b_search = QtWidgets.QPushButton("搜索")
        b_search.clicked.connect(self.do_search)
        bar.addWidget(b_search)
        root.addLayout(bar)

        # 结果表：类型 | 引用(ref) | 名称 | 信息
        self.table = QtWidgets.QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["类型", "引用", "名称", "信息"])
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch)
        self.table.itemSelectionChanged.connect(self._on_selection)
        self.table.itemDoubleClicked.connect(self._on_double)
        self.table.setMinimumHeight(140)
        root.addWidget(self.table, 1)

        # 动作行（按钮文案/启停随选中行 kind 变化）
        acts = QtWidgets.QHBoxLayout()
        self.act_hint = QtWidgets.QLabel("检索后选中一行执行动作（模块可双击看详情）")
        self.act_hint.setWordWrap(True)
        acts.addWidget(self.act_hint, 1)
        self.b_action = QtWidgets.QPushButton("执行动作")
        self.b_action.setEnabled(False)
        self.b_action.clicked.connect(self.do_action)
        acts.addWidget(self.b_action)
        root.addLayout(acts)

        self.result = QtWidgets.QLabel("")
        self.result.setWordWrap(True)
        self.result.setStyleSheet("color: #1a6e2a;")
        root.addWidget(self.result)

        # 底部工具区（保留导入/E2 向导能力）
        grp_tools = QtWidgets.QGroupBox("工具区：批量导入 / 单文件导入 / 创建自定义协议（E2）")
        gt = QtWidgets.QVBoxLayout(grp_tools)
        row1 = QtWidgets.QHBoxLayout()
        b_dir = QtWidgets.QPushButton("① 批量导入模块目录…")
        b_dir.clicked.connect(self.do_import_dir)
        row1.addWidget(b_dir)
        self.dir_label = QtWidgets.QLabel("（尚未导入）")
        self.dir_label.setWordWrap(True)
        row1.addWidget(self.dir_label, 1)
        gt.addLayout(row1)
        row2 = QtWidgets.QHBoxLayout()
        b_file = QtWidgets.QPushButton("② 单文件导入模块…")
        b_file.clicked.connect(self.do_import_file)
        row2.addWidget(b_file)
        b_wizard = QtWidgets.QPushButton("③ 创建自定义协议（协议定义向导）…")
        b_wizard.clicked.connect(self.do_open_wizard)
        b_wizard.setToolTip("v2.0.x-E2：填表生成合规 protocol.yaml（不懂 Schema 也能定义第三方协议）")
        row2.addWidget(b_wizard)
        row2.addStretch(1)
        gt.addLayout(row2)
        root.addWidget(grp_tools)

    # ---------- 检索 ----------
    def do_search(self):
        """按 kind+关键词检索四类本地资源，填入结果表。"""
        kind = self.kind_combo.currentData()
        query = self.query_edit.text().strip()
        self._busy = True
        self.table.setRowCount(0)
        hits = search(self.app.store, kind, query, limit=100)
        self._hits = list(hits)
        selected = self.app.selected
        for i, hit in enumerate(self._hits):
            self.table.insertRow(i)
            kind_label = dict((v, k) for k, v in KIND_LABELS).get(
                hit.kind, hit.kind)
            cell_kind = QtWidgets.QTableWidgetItem(kind_label)
            cell_kind.setData(QtCore.Qt.UserRole, hit)
            cell_ref = QtWidgets.QTableWidgetItem(hit.ref)
            cell_name = QtWidgets.QTableWidgetItem(hit.name)
            info = self._hit_info(hit, in_selected=hit.ref in selected)
            cell_info = QtWidgets.QTableWidgetItem(info)
            self.table.setItem(i, 0, cell_kind)
            self.table.setItem(i, 1, cell_ref)
            self.table.setItem(i, 2, cell_name)
            self.table.setItem(i, 3, cell_info)
        self._busy = False
        self._update_selection()
        if not hits:
            self.result.setText("（无命中：换关键词或换类型；留空关键词列出该类型全部）")
            self.result.setStyleSheet("color: #8a6d1a;")
        else:
            self.result.setText(f"✓ 命中 {len(hits)} 项（范围：本地资源）")
            self.result.setStyleSheet("color: #1a6e2a;")

    def _hit_info(self, hit, in_selected: bool) -> str:
        """结果信息列：module 层位/分类 + 装配态；community 项来源包+装载态。"""
        if hit.kind == "module":
            tag = hit.tags[0] if hit.tags else ""
            mark = " · ✓ 已装配" if in_selected else ""
            return f"层 {hit.layer} · {tag}{mark}"
        if hit.kind in ("community_module", "community_pipeline"):
            # tags = [来源包, "✓已装"/"可装载"]（retriever._community_hits）
            pkg = hit.tags[0] if hit.tags else ""
            state = hit.tags[1] if len(hit.tags) > 1 else ""
            if hit.kind == "community_module":
                in_asm = " · ✓ 已装配" if in_selected else ""
                return f"{pkg} · 层 {hit.layer} · {state}{in_asm}"
            return f"{pkg} · {state}"
        return " · ".join(hit.tags or [])

    def refresh_flags(self):
        """装配集变化后重标 module / community_module 行的标记（②③ 联动触发）。"""
        if self._busy or self.table.rowCount() == 0:
            return
        selected = self.app.selected
        for r in range(self.table.rowCount()):
            item = self.table.item(r, 0)
            if item is None:
                continue
            hit = item.data(QtCore.Qt.UserRole)
            if hit is None or hit.kind not in ("module", "community_module"):
                continue
            info = self._hit_info(hit, in_selected=hit.ref in selected)
            it = self.table.item(r, 3)
            if it is not None:
                it.setText(info)

    # ---------- 动作 ----------
    def _update_selection(self):
        """选中行变化 → 更新动作按钮文案/启停。"""
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            self.b_action.setEnabled(False)
            self.b_action.setText("执行动作")
            self.act_hint.setText("检索后选中一行执行动作（模块可双击看详情）")
            return
        row = rows[0].row()
        item = self.table.item(row, 0)
        hit = item.data(QtCore.Qt.UserRole) if item else None
        if hit is None:
            self.b_action.setEnabled(False)
            self.b_action.setText("执行动作")
            self.act_hint.setText("")
            return
        kind = hit.kind
        if kind == "module":
            self.b_action.setText("加入装配")
            self.act_hint.setText(
                f"把模块 {hit.ref} 追加进装配集（保留现有勾选，参与 ③装配/④生成）")
        elif kind == "pipeline":
            self.b_action.setText("设为当前管线")
            self.act_hint.setText(f"切换到管线 {hit.ref}（③ 层树随管线重建）")
        elif kind == "asset_pack":
            self.b_action.setText("选用资产包")
            self.act_hint.setText(f"在 ④生成 中选用资产包 {hit.ref}")
        elif kind == "protocol":
            self.b_action.setText("查看协议详情")
            self.act_hint.setText(f"查看协议 {hit.ref} 的声明（管线/模块/层挂载/引用）")
        elif kind == "community_module":
            installed = len(hit.tags) > 1 and hit.tags[1] == "✓已装"
            if installed:
                self.b_action.setText("加入装配")
                self.act_hint.setText(
                    f"模块 {hit.ref} 已装载（来源 {hit.tags[0]}）——加入装配参与 ③/④")
            else:
                self.b_action.setText("一键装载入库")
                self.act_hint.setText(
                    f"把社区模块 {hit.ref}（来源 {hit.tags[0]}）安装进本地模块库，"
                    "装载后即可勾选装配")
        elif kind == "community_pipeline":
            installed = len(hit.tags) > 1 and hit.tags[1] == "✓已装"
            if installed:
                self.b_action.setText("设为当前管线")
                self.act_hint.setText(
                    f"管线 {hit.ref}（来源 {hit.tags[0]}）已装载——设为当前管线")
            else:
                self.b_action.setText("装载管线到本地")
                self.act_hint.setText(
                    f"把社区管线 {hit.ref}（来源 {hit.tags[0]}）并入本地管线库，"
                    "装载后 ③ 下拉可选用")
        else:
            self.b_action.setEnabled(False)
            self.b_action.setText("执行动作")
            self.act_hint.setText("")
            return
        self.b_action.setEnabled(True)

    def _on_selection(self):
        if not self._busy:
            self._update_selection()

    def _selected_hit(self):
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            return None
        item = self.table.item(rows[0].row(), 0)
        return item.data(QtCore.Qt.UserRole) if item else None

    def do_action(self):
        """按选中行 kind 分流执行动作。"""
        hit = self._selected_hit()
        if hit is None:
            return
        kind = hit.kind
        if kind == "module":
            if self.app.add_module_to_assembly(hit.ref):
                self.refresh_flags()
        elif kind == "pipeline":
            if not self.app.set_current_pipeline(hit.ref):
                common.warn(self, f"管线 {hit.ref} 不在当前管线库中，"
                                  "可先在 ③管线装配 加载管线库目录。")
        elif kind == "asset_pack":
            cb = self.app.zone_d.asset_combo
            idx = cb.findData(hit.ref)
            if idx >= 0:
                cb.setCurrentIndex(idx)
                self.app.zone_d.refresh()
                self.app.status(f"已选用资产包：{hit.ref}（④生成 生效）", 4000)
            else:
                common.warn(self, f"资产包 {hit.ref} 未安装（检索源已装资产包，"
                                  "正常不应触发）。")
        elif kind == "protocol":
            self._show_protocol_detail(hit.ref)
        elif kind in ("community_module", "community_pipeline"):
            self._do_community_action(hit)

    def _do_community_action(self, hit):
        """E5：社区盘点项动作——未装装载入库，已装转装配/切管线。

        hit.tags = [来源包, "✓已装"/"可装载"]（retriever._community_hits）。
        """
        from ..core.community_inventory import (CommunityItem,
                                                install_module,
                                                install_pipeline)
        pkg = hit.tags[0] if hit.tags else ""
        installed = len(hit.tags) > 1 and hit.tags[1] == "✓已装"
        item = CommunityItem(kind=hit.kind, pkg=pkg, ref=hit.ref,
                             name=hit.name, layer=hit.layer,
                             installed=installed)
        if hit.kind == "community_module":
            if not installed:
                if not install_module(self.app.store, item):
                    common.error(self,
                                 f"装载失败：{hit.ref}（来源 {pkg}）"
                                 "——源文件缺失或解析失败。")
                    return
                # 装载成功：刷新 ②③④ 模块库 + 重标结果（可装载 → ✓已装）
                self.app.on_modules_changed()
                self._reload_community_flags()
                self.app.status(
                    f"✓ 已装载社区模块 {hit.ref}（{pkg}）——"
                    "可在 ②③ 勾选参与装配", 5000)
            else:
                if self.app.add_module_to_assembly(hit.ref):
                    self.refresh_flags()
        elif hit.kind == "community_pipeline":
            if not installed:
                if not install_pipeline(self.app.store, item):
                    common.error(self, f"装载失败：管线 {hit.ref}"
                                       f"（来源 {pkg}）——源文件缺失或解析失败。")
                    return
                self.app.reload_pipelines()
                self._reload_community_flags()
                self.app.status(f"✓ 已装载社区管线 {hit.ref}（{pkg}）——"
                                "③ 下拉可选用", 5000)
            else:
                if not self.app.set_current_pipeline(hit.ref):
                    common.warn(self, f"管线 {hit.ref} 不在当前管线库中。")

    def _reload_community_flags(self):
        """装载动作后重跑当前检索，刷新结果行装载态标记。"""
        if self._busy or self.table.rowCount() == 0:
            return
        q = self.query_edit.text().strip()
        kind = self.kind_combo.currentData()
        if kind not in ("community_module", "community_pipeline"):
            return
        selected = self.app.selected
        for r in range(self.table.rowCount()):
            item = self.table.item(r, 0)
            if item is None:
                continue
            hit = item.data(QtCore.Qt.UserRole)
            if hit is None or hit.kind not in ("community_module",
                                               "community_pipeline"):
                continue
            # 重查该 ref 的 installed 状态（重新 search 单条）
            from ..core.community_inventory import catalog
            cur = None
            for it in catalog(self.app.store):
                if it.kind == hit.kind and it.ref == hit.ref:
                    cur = it
                    break
            if cur is None:
                continue
            state = "✓已装" if cur.installed else "可装载"
            hit.tags = [cur.pkg, state] if len(hit.tags) >= 1 \
                else [state]
            info = self._hit_info(
                hit, in_selected=hit.ref in selected)
            info_item = self.table.item(r, 3)
            if info_item is not None:
                info_item.setText(info)

    def _on_double(self, item):
        if item is None:
            return
        hit = item.data(QtCore.Qt.UserRole)
        if hit is None:
            return
        if hit.kind == "module":
            m = self.app.store.get_module(hit.ref)
            if m:
                common.module_detail_dialog(self, m)
        elif hit.kind == "community_module":
            m = self.app.store.get_module(hit.ref)
            if m:
                common.module_detail_dialog(self, m)
            else:
                common.info(self, f"社区模块 {hit.ref}（来源 {hit.tags[0] if hit.tags else ''}）"
                                  "尚未装载——点「一键装载入库」安装后即可查看详情并参与装配。")
        elif hit.kind == "protocol":
            self._show_protocol_detail(hit.ref)

    # ---------- 协议详情 ----------
    def _protocol_entry(self, pid: str):
        try:
            from ..core.registry_loader import load_registry
            reg = load_registry()
            for p in (reg.protocols or []):
                if p.get("id") == pid:
                    return p
        except Exception:
            pass
        return None

    def _show_protocol_detail(self, pid: str):
        entry = self._protocol_entry(pid)
        if entry is None:
            common.warn(self, f"未找到协议 {pid} 的在册声明。")
            return
        lines = [f"协议 : {entry.get('id', '')}",
                 f"名称 : {entry.get('name', '')}",
                 f"管线 : {entry.get('pipeline', '')}",
                 f"分类 : {', '.join(entry.get('categories') or []) or '(空)'}",
                 f"模块 : {', '.join(entry.get('module_ids') or []) or '(空)'}",
                 "层挂载:"]
        ml = entry.get("mount_layers") or {}
        for lid, info in sorted(ml.items()):
            dft = ", ".join(info.get("default") or []) or "(无)"
            lines.append(f"  {lid} {info.get('name', '')}: 默认 {dft}")
        refs = entry.get("references") or []
        if refs:
            lines.append("跨包引用:")
            for ref in refs:
                lines.append(f"  · {ref.get('module_id')}"
                             f" ← {ref.get('source_package')}"
                             + ("（资产只读）" if ref.get("asset_readonly") else ""))
        else:
            lines.append("跨包引用: （无）")
        dlg = QtWidgets.QDialog(self)
        dlg.setWindowTitle(f"协议详情 · {pid}")
        dlg.resize(680, 480)
        lay = QtWidgets.QVBoxLayout(dlg)
        view = QtWidgets.QPlainTextEdit()
        view.setReadOnly(True)
        view.setPlainText("\n".join(lines))
        lay.addWidget(view)
        btn = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Close)
        btn.rejected.connect(dlg.reject)
        lay.addWidget(btn)
        dlg.exec()

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
