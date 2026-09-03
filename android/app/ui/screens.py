"""叙事工坊 · Android UI 五个标签页（纯代码 KivyMD 布局，无 .kv 文件）。

A 导入  ：粘贴模块 Markdown → 解析预览 → 安装入库
B 模块库：全量列表勾选（或按当前管线各层默认模块一键勾选）
C 管线  ：单选生成管线（持久化到 config.json）
D 资产  ：单选资产包（"无" + 已装包）
E 生成  ：标题 → 生成预览 → 保存到应用输出目录 / 系统分享

所有数据/状态操作委托 app.controller.Controller（纯逻辑，UI 薄封装）。
"""
from __future__ import annotations

from typing import Callable, Optional

from kivy.metrics import dp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDFlatButton, MDRaisedButton
from kivymd.uix.label import MDLabel
from kivymd.uix.list import MDList
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.selectioncontrol import MDCheckbox, MDRadioButton
from kivymd.uix.snackbar import Snackbar
from kivymd.uix.textfield import MDTextField

from app.controller import Controller
from app.core.models import Module

TEXT_HINT = "# 模块 情感:M22 · 三冲动驱动\n\n分类：情感类\n挂载层：P40\n...（桌面工具指令集模块格式）"


def _snack(text: str, duration: float = 3.0) -> None:
    Snackbar(text=text, duration=duration).open()


def _scroll_with(list_widget: MDList) -> MDScrollView:
    sc = MDScrollView()
    sc.add_widget(list_widget)
    return sc


def _module_row(ctrl: Controller, m: Module,
                on_toggled: Optional[Callable] = None) -> MDBoxLayout:
    """模块库列表行：复选框 + 「full_id · 名称 @ 层位」。"""
    row = MDBoxLayout(orientation="horizontal",
                      size_hint_y=None, height=dp(52),
                      padding=[dp(4), 0, dp(12), 0])
    cb = MDCheckbox(size_hint=(None, 1), width=dp(48),
                    active=ctrl.is_selected(m.full_id))
    cb.bind(on_active=lambda _w, _v, fid=m.full_id: (
        ctrl.toggle(fid), on_toggled and on_toggled()))
    row.add_widget(cb)
    lab = MDLabel(text=f"{m.full_id} · {m.name}  @{m.layer}",
                  size_hint_x=1, theme_text_color="Secondary")
    row.add_widget(lab)
    return row


def _radio_row(text: str, group: str, active: bool,
               on_select: Callable[[bool], None]) -> MDBoxLayout:
    """单选行：MDRadioButton + 文本（radio 激活时触发 on_select(True)）。"""
    row = MDBoxLayout(orientation="horizontal",
                      size_hint_y=None, height=dp(52),
                      padding=[dp(4), 0, dp(12), 0])
    rb = MDRadioButton(size_hint=(None, 1), width=dp(48),
                       group=group, active=active)
    rb.bind(active=lambda _w, v, fn=on_select: v and fn())
    row.add_widget(rb)
    lab = MDLabel(text=text, size_hint_x=1, theme_text_color="Secondary")
    row.add_widget(lab)
    return row


# ============================================================
# A 导入
# ============================================================
class ImportTab(MDBoxLayout):
    def __init__(self, ctrl: Controller, on_imported: Callable,
                 **kwargs):
        super().__init__(orientation="vertical", padding=dp(12),
                         spacing=dp(8), **kwargs)
        self.ctrl = ctrl
        self.on_imported = on_imported

        self.input = MDTextField(hint_text="粘贴模块 Markdown…",
                                 helper_text=TEXT_HINT,
                                 helper_text_mode="on_focus",
                                 multiline=True,
                                 size_hint_y=None, height=dp(200))
        self.add_widget(self.input)

        btns = MDBoxLayout(orientation="horizontal",
                           size_hint_y=None, height=dp(52),
                           spacing=dp(8))
        preview_btn = MDRaisedButton(text="解析预览", size_hint=(0.5, 1),
                                     on_release=lambda _w: self._preview())
        import_btn = MDRaisedButton(text="导入安装", size_hint=(0.5, 1),
                                    on_release=lambda _w: self._import())
        btns.add_widget(preview_btn)
        btns.add_widget(import_btn)
        self.add_widget(btns)

        self.result = MDTextField(hint_text="解析结果 / 模块摘要",
                                  readonly=True, multiline=True,
                                  size_hint_y=1)
        self.add_widget(self.result)

    def _preview(self):
        text = (self.input.text or "").strip()
        if not text:
            _snack("请先粘贴模块 Markdown")
            return
        try:
            m = self.ctrl.parse_module_text(text)
            self.result.text = self.ctrl.module_summary(m)
            _snack(f"解析成功：{m.full_id} · {m.name}")
        except Exception as exc:  # noqa: BLE001
            self.result.text = f"解析失败：{exc}"
            _snack("解析失败，详见下方")

    def _import(self):
        text = (self.input.text or "").strip()
        if not text:
            _snack("请先粘贴模块 Markdown")
            return
        try:
            m = self.ctrl.import_module(text)
            self.result.text = f"✓ 已安装 {m.full_id} · {m.name} @{m.layer}"
            self.input.text = ""
            _snack(f"已安装 {m.full_id} · {m.name}")
            self.on_imported()
        except Exception as exc:  # noqa: BLE001
            self.result.text = f"导入失败：{exc}"
            _snack("导入失败，详见下方")


# ============================================================
# B 模块库
# ============================================================
class ModulesTab(MDBoxLayout):
    def __init__(self, ctrl: Controller, on_changed: Callable, **kwargs):
        super().__init__(orientation="vertical", padding=dp(12),
                         spacing=dp(4), **kwargs)
        self.ctrl = ctrl
        self.on_changed = on_changed

        head = MDBoxLayout(orientation="horizontal",
                           size_hint_y=None, height=dp(48),
                           spacing=dp(6))
        self.count_lab = MDLabel(text="", size_hint_x=1)
        defaults_btn = MDFlatButton(text="按管线默认勾选", size_hint=(None, 1),
                                    width=dp(150),
                                    on_release=lambda _w: self._select_defaults())
        clear_btn = MDFlatButton(text="清空", size_hint=(None, 1),
                                 width=dp(70),
                                 on_release=lambda _w: self._clear())
        head.add_widget(self.count_lab)
        head.add_widget(defaults_btn)
        head.add_widget(clear_btn)
        self.add_widget(head)

        self.list_widget = MDList()
        self.add_widget(_scroll_with(self.list_widget))

    def _select_defaults(self):
        n = self.ctrl.select_defaults()
        self.refresh()
        _snack(f"按管线默认勾选 +{n} 个模块" if n else "当前管线未配置默认模块")

    def _clear(self):
        self.ctrl.clear_selection()
        self.refresh()
        _snack("已清空勾选")

    def refresh(self):
        self.list_widget.clear_widgets()
        for m in self.ctrl.list_modules():
            self.list_widget.add_widget(
                _module_row(self.ctrl, m, on_toggled=self._changed))
        self.count_lab.text = (f"已选 {self.ctrl.selected_count()} / "
                               f"{len(self.ctrl.list_modules())}")

    def _changed(self):
        self.count_lab.text = (f"已选 {self.ctrl.selected_count()} / "
                               f"{len(self.ctrl.list_modules())}")
        self.on_changed()


# ============================================================
# C 管线
# ============================================================
class PipelineTab(MDBoxLayout):
    def __init__(self, ctrl: Controller, on_changed: Callable, **kwargs):
        super().__init__(orientation="vertical", padding=dp(12),
                         spacing=dp(4), **kwargs)
        self.ctrl = ctrl
        self.on_changed = on_changed

        lab = MDLabel(text="选择生成管线（决定模块分层与装配顺序）",
                      size_hint_y=None, height=dp(36),
                      theme_text_color="Primary", bold=True)
        self.add_widget(lab)
        self.list_widget = MDList()
        self.add_widget(_scroll_with(self.list_widget))

    def refresh(self):
        self.list_widget.clear_widgets()
        cur = self.ctrl.current_pipeline_id
        for p in self.ctrl.list_pipelines():
            self.list_widget.add_widget(_radio_row(
                f"{p.id} · {p.name}", group="pipe_group",
                active=(p.id == cur),
                on_select=lambda _b, pid=p.id: self._pick(pid)))

    def _pick(self, pid: str):
        self.ctrl.set_pipeline(pid)
        self.refresh()
        _snack(f"当前管线：{self.ctrl.current_pipeline().name}")
        self.on_changed()


# ============================================================
# D 资产
# ============================================================
class AssetTab(MDBoxLayout):
    def __init__(self, ctrl: Controller, on_changed: Callable, **kwargs):
        super().__init__(orientation="vertical", padding=dp(12),
                         spacing=dp(4), **kwargs)
        self.ctrl = ctrl
        self.on_changed = on_changed

        lab = MDLabel(text="选择资产包（生成时按需注入命名/设定素材）",
                      size_hint_y=None, height=dp(36),
                      theme_text_color="Primary", bold=True)
        self.add_widget(lab)
        self.list_widget = MDList()
        self.add_widget(_scroll_with(self.list_widget))

    def refresh(self):
        self.list_widget.clear_widgets()
        cur = self.ctrl.store.get_config("asset_pack", "")
        # “无”选项
        self.list_widget.add_widget(_radio_row(
            "（无资产包）", group="asset_group", active=(cur == ""),
            on_select=lambda _b: self._pick("")))
        for a in self.ctrl.list_asset_packs():
            self.list_widget.add_widget(_radio_row(
                f"{a.name}（{len(a.entries)} 资产键）", group="asset_group",
                active=(a.name == cur),
                on_select=lambda _b, n=a.name: self._pick(n)))

    def _pick(self, name: str):
        self.ctrl.set_asset_pack(name)
        self.refresh()
        _snack("资产包：无" if not name else f"资产包：{name}")
        self.on_changed()


# ============================================================
# E 生成
# ============================================================
class GenerateTab(MDBoxLayout):
    def __init__(self, ctrl: Controller, **kwargs):
        super().__init__(orientation="vertical", padding=dp(12),
                         spacing=dp(8), **kwargs)
        self.ctrl = ctrl
        self.last_saved: str = ""

        self.title_input = MDTextField(hint_text="文档标题（留空自动生成）",
                                       size_hint_y=None, height=dp(56))
        self.add_widget(self.title_input)

        btns = MDBoxLayout(orientation="horizontal",
                           size_hint_y=None, height=dp(52), spacing=dp(8))
        gen_btn = MDRaisedButton(text="生成文档", size_hint=(0.5, 1),
                                 on_release=lambda _w: self._generate())
        save_btn = MDRaisedButton(text="保存", size_hint=(0.5, 1),
                                  on_release=lambda _w: self._save())
        btns.add_widget(gen_btn)
        btns.add_widget(save_btn)
        self.add_widget(btns)

        self.status_lab = MDLabel(text="未生成",
                                  size_hint_y=None, height=dp(24),
                                  theme_text_color="Secondary")
        self.add_widget(self.status_lab)

        self.preview = MDTextField(readonly=True, multiline=True,
                                   hint_text="生成的 Markdown 预览…",
                                   size_hint_y=1)
        self.add_widget(self.preview)

        share_btn = MDFlatButton(text="分享文本…", size_hint_y=None,
                                 height=dp(40),
                                 on_release=lambda _w: self._share())
        self.add_widget(share_btn)
        self.save_lab = MDLabel(text="", size_hint_y=None, height=dp(36),
                                theme_text_color="Secondary")
        self.add_widget(self.save_lab)

    def refresh_status(self):
        pipe = self.ctrl.current_pipeline()
        ap = self.ctrl.current_asset_pack()
        parts = [f"管线：{pipe.name if pipe else '无'}",
                 f"已勾选 {self.ctrl.selected_count()} 模块",
                 f"资产：{ap.name if ap else '无'}"]
        self.status_lab.text = "  ·  ".join(parts)

    def _generate(self):
        try:
            md, warns = self.ctrl.generate(title=(self.title_input.text or "").strip())
        except Exception as exc:  # noqa: BLE001
            self.status_lab.text = "✗ 生成失败"
            self.preview.text = f"生成失败：{exc}"
            _snack(str(exc), duration=5)
            return
        self.preview.text = md
        self.status_lab.text = f"✓ 生成 {len(md)} 字符 · 警告 {len(warns)} 条"
        if warns:
            _snack("；".join(warns[:3]), duration=5)
        # 预览后自动展示默认文件名
        self.save_lab.text = f"默认文件名：{self.ctrl.default_output_name()}"

    def _save(self):
        if not self.ctrl.last_md:
            _snack("请先生成文档")
            return
        try:
            out_dir = self.ctrl.home / "output"
            out_dir.mkdir(parents=True, exist_ok=True)
            name = self.ctrl.default_output_name()
            path = out_dir / name
            if not self.ctrl.save_to(path):
                _snack("无可保存内容")
                return
            self.last_saved = str(path)
            self.save_lab.text = f"已保存：{self.last_saved}"
            _snack("已保存到应用数据目录", duration=5)
        except Exception as exc:  # noqa: BLE001
            _snack(f"保存失败：{exc}", duration=5)

    def _share(self):
        if not self.ctrl.last_md:
            _snack("请先生成文档")
            return
        try:
            from plyer import share
            share.share(text=self.ctrl.last_md,
                        title=self.ctrl.default_output_name())
        except Exception as exc:  # noqa: BLE001
            _snack(f"分享不可用：{exc}", duration=5)
