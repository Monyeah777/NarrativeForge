"""叙事工坊 · Android 入口（KivyMD 五屏：A导入/B模块库/C管线/D资产/E生成）。

启动流程：创建 Controller → ensure_seeded 首装自举（幂等）→ 组装底部导航。
UI 壳只做薄封装：所有数据/状态操作均委托 android/app/controller.py（纯逻辑）。
"""
from __future__ import annotations

import sys
from pathlib import Path

# 确保 android/ 下 app 包可导入（buildozer source.dir=. 时工作目录即本目录）
sys.path.insert(0, str(Path(__file__).resolve().parent))

from kivymd.app import MDApp
from kivymd.uix.bottomnavigation import MDBottomNavigation, MDBottomNavigationItem
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.toolbar import MDTopAppBar

from app import config
from app.controller import Controller
from app.ui.screens import (
    AssetTab, GenerateTab, ImportTab, ModulesTab, PipelineTab,
)


class MainApp(MDApp):
    """叙事工坊主应用：持有 Controller 单例 + 底部五导航。"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.ctrl: Controller = None
        self.tab_import: ImportTab = None
        self.tab_modules: ModulesTab = None
        self.tab_pipeline: PipelineTab = None
        self.tab_asset: AssetTab = None
        self.tab_generate: GenerateTab = None

    def build(self):
        self.theme_cls.primary_palette = "Teal"
        self.theme_cls.theme_style = "Light"
        self.title = config.APP_NAME

        # ---- 数据层：首装自举（幂等，版本一致自动跳过） ----
        self.ctrl = Controller()
        seed_stats = self.ctrl.ensure_seeded()

        root = MDBoxLayout(orientation="vertical")
        # 注意：KivyMD 1.2.0 的 MDTopAppBar 没有 subtitle 属性（全类属性集仅
        # title/left_action_items/right_action_items/mode/type/headline_text 等，
        # 传入未知 kwarg 会在 EventDispatcher.__init__ 抛 TypeError 导致启动闪退）。
        # elevation 继承自基类 NotchedBox（toolbar.py:787 NumericProperty），合法。
        # 版本信息改由右下角"关于"区域/各页空态展示，此处仅保留主标题。
        bar = MDTopAppBar(title=config.APP_NAME,
                          elevation=2)
        root.add_widget(bar)

        nav = MDBottomNavigation()

        # A 导入
        self.tab_import = ImportTab(self.ctrl, on_imported=self.refresh_after_import)
        nav.add_widget(self._item("tab_import", "导入", "file-import",
                                  self.tab_import))

        # B 模块库
        self.tab_modules = ModulesTab(self.ctrl, on_changed=self.refresh_generate)
        nav.add_widget(self._item("tab_modules", "模块库", "view-list",
                                  self.tab_modules))

        # C 管线
        self.tab_pipeline = PipelineTab(self.ctrl, on_changed=self.refresh_generate)
        nav.add_widget(self._item("tab_pipeline", "管线", "timeline-text",
                                  self.tab_pipeline))

        # D 资产
        self.tab_asset = AssetTab(self.ctrl, on_changed=self.refresh_generate)
        nav.add_widget(self._item("tab_asset", "资产", "database-outline",
                                  self.tab_asset))

        # E 生成
        self.tab_generate = GenerateTab(self.ctrl)
        nav.add_widget(self._item("tab_generate", "生成", "text-box-multiple",
                                  self.tab_generate))

        root.add_widget(nav)

        # 首装自举结果提示
        self._seed_message = seed_stats
        return root

    @staticmethod
    def _item(name: str, text: str, icon: str, content) -> MDBottomNavigationItem:
        it = MDBottomNavigationItem(name=name, text=text, icon=icon)
        it.add_widget(content)
        return it

    def on_start(self):
        st = getattr(self, "_seed_message", None) or {}
        if st.get("errors"):
            from kivymd.uix.snackbar import Snackbar
            Snackbar(text="种子导入出错：" + "；".join(st["errors"][:3]),
                     duration=5).open()
        elif not st.get("skipped"):
            from kivymd.uix.snackbar import Snackbar
            Snackbar(
                text=f"已装载 {st.get('pipelines', 0)} 管线 · "
                     f"{st.get('modules', 0)} 模块 · "
                     f"{st.get('asset_packs', 0)} 资产包",
                duration=3).open()
        # 初始数据视图
        self.tab_modules.refresh()
        self.tab_pipeline.refresh()
        self.tab_asset.refresh()
        self.tab_generate.refresh_status()

    # ---------------- 跨屏联动 ----------------
    def refresh_after_import(self):
        self.tab_modules.refresh()
        self.tab_generate.refresh_status()

    def refresh_generate(self, *_args):
        self.tab_generate.refresh_status()


if __name__ == "__main__":
    MainApp().run()
