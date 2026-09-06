"""主窗口 MainWindow：整合 ①~⑦ 七功能区，承担跨区状态协调与拖放入口。

各功能区（zone_a~g）均以 ``(app, parent=None)`` 构造并持有 self.app，
通过本类暴露的属性/方法完成跨区协作。本类是 zone 之间的唯一协调者：

- 状态属性：store / pipelines / current_pipeline_id / current_pipeline / selected
- 功能区实例：zone_a ~ zone_g、tabs
- 协调方法：status / reload_pipelines / on_modules_changed /
            on_pipeline_changed / on_selection_changed / apply_preset_state
- 拖放入口：把拖入的 .md/.txt/.json 交给 zone_a 解析
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

from PySide6 import QtCore, QtGui, QtWidgets

from ..core.models import Pipeline
from ..core.pipeline_loader import discover_pipelines
from ..core.storage import Store
from .zone_a_import import ZoneAImport
from .zone_b_validate import ZoneBValidate
from .zone_c_pipeline import ZoneCPipeline
from .zone_d_generate import ZoneDGenerate
from .zone_e_assets import ZoneEAssets
from .zone_f_presets import ZoneFPresets
from .zone_g_community import ZoneGCommunity

APP_TITLE = "叙事工坊 · 桌面工具"


class MainWindow(QtWidgets.QMainWindow):
    """叙事工坊桌面工具主窗口（A~G 七功能区整合）。"""

    def __init__(self, store: Optional[Store] = None):
        super().__init__()
        # ---------- 核心状态（zone 依赖的 app 接口） ----------
        self.store: Store = store or Store()
        self.pipelines: list[Pipeline] = []
        self.current_pipeline_id: Optional[str] = None
        self.selected: set[str] = set()      # full_id 集合（跨 ②③④ 共享）

        # ---------- 七功能区（构造顺序：a 先行，b 运行期引用 a） ----------
        self.zone_a = ZoneAImport(self)
        self.zone_b = ZoneBValidate(self)
        self.zone_c = ZoneCPipeline(self)
        self.zone_d = ZoneDGenerate(self)
        self.zone_e = ZoneEAssets(self)
        self.zone_f = ZoneFPresets(self)
        self.zone_g = ZoneGCommunity(self)

        self._build_ui()
        self._load_initial_state()

    # ---------- UI ----------
    def _build_ui(self) -> None:
        self.setWindowTitle(APP_TITLE)
        self.resize(1160, 780)

        tabs = QtWidgets.QTabWidget()
        tabs.addTab(self.zone_a, "① 导入解析")
        tabs.addTab(self.zone_b, "② 模块库 · 校验")
        tabs.addTab(self.zone_c, "③ 管线装配")
        tabs.addTab(self.zone_d, "④ 生成输出")
        tabs.addTab(self.zone_e, "⑤ 资产库")
        tabs.addTab(self.zone_f, "⑥ 预设")
        tabs.addTab(self.zone_g, "⑦ 社区拉取")
        self.tabs = tabs
        self.setCentralWidget(tabs)

        self.statusBar().showMessage("就绪")
        # 拖放入口：文件拖入窗口 → 交给 ① 解析
        self.setAcceptDrops(True)

    # ---------- 属性 ----------
    @property
    def current_pipeline(self) -> Optional[Pipeline]:
        """当前管线（按 current_pipeline_id 匹配；无匹配时回退第一条）。"""
        for p in self.pipelines:
            if p.id == self.current_pipeline_id:
                return p
        return self.pipelines[0] if self.pipelines else None

    # ---------- 初始装载 ----------
    def _load_initial_state(self) -> None:
        """启动时装载管线缓存/配置与模块库，刷新各视图。"""
        self._reload_pipelines_impl(notify=False)
        cfg = self.store.get_config("pipeline")
        ids = [p.id for p in self.pipelines]
        self.current_pipeline_id = cfg if cfg in ids else (
            ids[0] if ids else None)
        # ③ 管线下拉 + 层树（内部会按当前管线重建）
        self.zone_c.refresh_pipes(keep=self.current_pipeline_id)
        # ② 模块表格 / ④ 统计提示 / ⑤ 资产包 / ⑥ 预设
        self.zone_b.refresh()
        self.zone_d.refresh_assets()
        self.zone_d.refresh()
        self.zone_e.refresh()
        self.zone_f.refresh()
        self.status(
            f"就绪：管线 {len(self.pipelines)} 条 · 模块 "
            f"{len(self.store.list_modules())} 个 · 资产包 "
            f"{len(self.store.list_asset_packs())} 个 · 预设 "
            f"{len(self.store.list_presets())} 个", 8000)

    # ---------- 状态栏 ----------
    def status(self, msg: str, timeout: int = 5000) -> None:
        """状态栏提示（zone 通用出口）。"""
        self.statusBar().showMessage(str(msg), timeout)

    # ---------- 管线 ----------
    def reload_pipelines(self) -> None:
        """③ 区“重新载入”：从缓存/配置目录重建管线列表并刷新。"""
        self._reload_pipelines_impl(notify=True)

    def _reload_pipelines_impl(self, notify: bool) -> None:
        raw = self.store.load_cache("pipelines")
        if isinstance(raw, list) and raw:
            self.pipelines = [Pipeline.from_json(d) for d in raw]
        else:
            # 缓存缺失 → 回退到配置里记录的管线库目录重新发现
            pdir = self.store.get_config("pipeline_dir")
            pipes = discover_pipelines(pdir) if pdir else []
            self.pipelines = pipes
            if pipes:
                self.store.save_cache(
                    "pipelines", [p.to_json() for p in pipes])
        ids = [p.id for p in self.pipelines]
        if self.current_pipeline_id not in ids:
            self.current_pipeline_id = ids[0] if ids else None
        self.zone_c.refresh_pipes(keep=self.current_pipeline_id)
        if notify:
            if self.pipelines:
                self.status(f"已重新载入 {len(self.pipelines)} 条管线。")
            else:
                self.status("未发现管线：请在 ③管线装配 加载管线库目录。")

    # ---------- 跨区联动回调 ----------
    def on_modules_changed(self) -> None:
        """模块库增删/启停后：重刷 ②③④（勾选可能因删除而变化）。"""
        self.zone_b.refresh()
        self.zone_c.refresh()
        self.zone_d.refresh()
        self.status(
            f"模块库已刷新：共 {len(self.store.list_modules())} 个模块",
            4000)

    def on_pipeline_changed(self) -> None:
        """管线切换后：②校验视图（依赖当前管线）与 ④提示 联动刷新。

        ③ 区层树已由 zone_c 内部在切换时自行重建，这里不再重复重建。
        """
        self.zone_b.refresh()
        self.zone_d.refresh()
        pipe = self.current_pipeline
        self.status(f"当前管线：{pipe.id} · {pipe.name}" if pipe
                    else "当前管线：无")

    def on_selection_changed(self) -> None:
        """勾选集合变化后：④ 统计/提示 + ⑦ 装配态标记刷新（②③ 勾选即状态源）。"""
        self.zone_d.refresh()
        self.zone_g.refresh_flags()

    # ---------- 预设应用（⑥ 区委托的统一入口） ----------
    def apply_preset_state(self, result: dict) -> None:
        """应用预设结果：切管线 → 重填勾选 → 联动刷新 ②③④⑤。

        result = apply_preset(store, preset) 的返回：
            {"pipeline": str|None, "modules": list[Module],
             "asset_pack": str, "warnings": list[str]}
        """
        pipe_id = result.get("pipeline")
        modules = result.get("modules") or []
        asset_pack = result.get("asset_pack") or ""
        warnings = result.get("warnings") or []

        ids = [p.id for p in self.pipelines]
        if pipe_id and pipe_id not in ids:
            self.status(f"预设管线 {pipe_id} 不在当前管线库中，已跳过切换；"
                        "可先在 ③管线装配 加载该管线。", 6000)
            pipe_id = None
        if pipe_id:
            self.current_pipeline_id = pipe_id
            self.store.set_config("pipeline", pipe_id)

        # 勾选集合（full_id）
        self.selected = {m.full_id for m in modules}

        # ③ 按目标管线重建层树（含勾选）；② 表格同步
        self.zone_c.refresh_pipes(keep=self.current_pipeline_id)
        self.zone_b.refresh()

        # ④ 资产包联动
        self.zone_d.refresh_assets()
        if asset_pack:
            idx = self.zone_d.asset_combo.findData(asset_pack)
            if idx >= 0:
                self.zone_d.asset_combo.setCurrentIndex(idx)
        self.zone_d.refresh()
        if warnings:
            self.zone_d.warn_view.setPlainText(
                "应用预设提示：\n" + "\n".join(f"· {w}" for w in warnings))

        self.status(f"已应用预设：{len(self.selected)} 个模块参与装配。",
                    6000)

    # ---------- E4 资源装配协调（⑦ 区检索视图委托的统一入口） ----------
    def add_module_to_assembly(self, full_id: str) -> bool:
        """把单个模块追加进装配集（E4：从搜索结果加入装配）。

        与 apply_preset_state 的「重填」语义区分——保留现有勾选，追加并
        联动刷新 ②③④。已在装配集内则幂等返回 True；模块不存在返回 False。
        """
        m = self.store.get_module(full_id)
        if m is None:
            return False
        if full_id not in self.selected:
            self.selected.add(full_id)
            # ③ 层树勾选同步 + ② 表格勾选同步 + ④ 生成统计联动
            self.zone_c.refresh()
            self.zone_b.refresh()
            self.zone_d.refresh()
        self.status(
            f"已加入装配：{m.full_id} · {m.name}"
            f"（当前共 {len(self.selected)} 个模块）", 4000)
        return True

    def set_current_pipeline(self, pipeline_id: str) -> bool:
        """切换当前管线（E4：从搜索结果选用管线；③ 下拉切换同路径）。

        与 apply_preset_state 的管线切换子序列一致：写配置 → ③ 重建层树
        → ②/④ 联动刷新。目标管线不在库中返回 False。
        """
        ids = [p.id for p in self.pipelines]
        if pipeline_id not in ids:
            return False
        self.current_pipeline_id = pipeline_id
        self.store.set_config("pipeline", pipeline_id)
        self.zone_c.refresh_pipes(keep=pipeline_id)
        self.zone_b.refresh()
        self.zone_d.refresh()
        pipe = self.current_pipeline
        self.status(
            f"当前管线：{pipe.id} · {pipe.name}" if pipe
            else f"当前管线：{pipeline_id}", 4000)
        return True

    # ---------- 拖放 ----------
    def dragEnterEvent(self, event: QtGui.QDragEnterEvent) -> None:  # noqa: N802
        if event.mimeData().hasUrls() and any(
                u.isLocalFile() for u in event.mimeData().urls()):
            event.acceptProposedAction()

    def dropEvent(self, event: QtGui.QDropEvent) -> None:  # noqa: N802
        for url in event.mimeData().urls():
            if not url.isLocalFile():
                continue
            p = Path(url.toLocalFile())
            if p.is_file():
                if self.zone_a.load_file(p):
                    self.tabs.setCurrentIndex(0)
                    self.status(f"已拖入载入：{p.name}")
                break      # 只处理第一个文件
        event.acceptProposedAction()


def run(argv=None) -> int:
    """创建 QApplication 并进入事件循环（入口脚本共用）。"""
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication(argv if argv is not None else sys.argv)
    app.setApplicationName("叙事工坊")
    app.setApplicationDisplayName(APP_TITLE)
    win = MainWindow()
    win.show()
    return app.exec()
