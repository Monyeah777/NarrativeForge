"""叙事工坊 · Android 应用控制器（纯逻辑层，不依赖 Kivy）。

把 desktop core（模块/管线/资产/校验/生成）封装为移动端 MVP 流程：
    A 导入 → B 模块库勾选 → C 管线 → D 资产包 → E 生成（预览/保存）

行为对齐 desktop/src/ui 各 zone 的调用约定：
- 管线列表来自 store cache("pipelines")（bootstrap 首装时写入）；
- 当前管线持久化在 config["pipeline"]；
- 勾选集合 selected 为 full_id 集合（与桌面 self.app.selected 一致）；
- 生成前 check_assembly → generate_document(pipeline, modules, asset_pack, title)。

本模块不 import Kivy，可在桌面 python3 下直接做逻辑自测。
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from . import config
from .bootstrap import seed_from_dir, seeded_version
from .core.generator import default_filename, generate_document
from .core.models import LAYER_IDS, AssetPack, Module, Pipeline, fid_key
from .core.parser import parse_module
from .core.storage import Store
from .core.validator import check_assembly, validate_module


class Controller:
    """应用状态机 + 数据访问门面。UI 壳持有单例并调用其方法。"""

    def __init__(self, home: Optional[Path | str] = None):
        self.home = Path(home) if home else config.mobile_home()
        self.store = Store(self.home)
        self.selected: set = set()          # full_id 集合（B 屏勾选，跨屏共享）
        self.pipelines: List[Pipeline] = []
        self.current_pipeline_id: Optional[str] = None
        self.last_md: str = ""
        self.last_warnings: List[str] = []
        self._modules_cache: Optional[List[Module]] = None
        self.reload_pipelines()

    # ---------------- 生命周期 / 自举 ----------------
    def ensure_seeded(self, force: bool = False) -> dict:
        """首装自举：数据目录为空或版本不符时从内置 seed 导入。返回统计。"""
        need = force or (not seeded_version(self.store)
                         and not self.store.list_modules())
        if not need:
            return {"skipped": True, "modules": 0,
                    "asset_packs": 0, "pipelines": 0, "errors": []}
        stats = seed_from_dir(self.store, config.seed_dir(), force=force)
        self.reload_pipelines()
        self._modules_cache = None
        # 若无缓存管线（老版本首次升级），尝试从 seed 重新发现
        if not self.pipelines:
            stats.setdefault("errors", []).append("管线列表为空，请检查内置 seed")
        return stats

    def reseed(self) -> dict:
        """强制重导内置种子（覆盖同名模块/资产，不删除用户自建）。"""
        return self.ensure_seeded(force=True)

    def home_path(self) -> str:
        return str(self.home)

    # ---------------- 管线 ----------------
    def reload_pipelines(self) -> None:
        raw = self.store.load_cache("pipelines")
        self.pipelines = ([Pipeline.from_json(d) for d in raw]
                          if raw else [])
        cfg = self.store.get_config("pipeline")
        ids = [p.id for p in self.pipelines]
        self.current_pipeline_id = cfg if cfg in ids else (
            ids[0] if ids else None)

    def list_pipelines(self) -> List[Pipeline]:
        return list(self.pipelines)

    def get_pipeline(self, pid: Optional[str] = None) -> Optional[Pipeline]:
        pid = pid or self.current_pipeline_id
        for p in self.pipelines:
            if p.id == pid:
                return p
        return self.pipelines[0] if self.pipelines else None

    def current_pipeline(self) -> Optional[Pipeline]:
        return self.get_pipeline()

    def set_pipeline(self, pid: str) -> None:
        ids = [p.id for p in self.pipelines]
        if pid in ids:
            self.current_pipeline_id = pid
            self.store.set_config("pipeline", pid)

    # ---------------- 模块库 ----------------
    def invalidate_modules(self) -> None:
        self._modules_cache = None

    def list_modules(self) -> List[Module]:
        if self._modules_cache is None:
            self._modules_cache = self.store.list_modules()
        return self._modules_cache

    def modules_by_category(self) -> Dict[str, List[Module]]:
        out: Dict[str, List[Module]] = {}
        for m in self.list_modules():
            out.setdefault(m.category, []).append(m)
        return out

    def get_module(self, full_id: str) -> Optional[Module]:
        for m in self.list_modules():
            if m.full_id == full_id or fid_key(m.full_id) == fid_key(full_id):
                return m
        return None

    # ---------------- B：勾选 ----------------
    def is_selected(self, full_id: str) -> bool:
        return any(fid_key(x) == fid_key(full_id) for x in self.selected)

    def toggle(self, full_id: str) -> bool:
        """切换勾选；返回切换后是否选中。"""
        key = fid_key(full_id)
        hit = None
        for x in self.selected:
            if fid_key(x) == key:
                hit = x
                break
        if hit is not None:
            self.selected.discard(hit)
            return False
        m = self.get_module(full_id)
        if m:
            self.selected.add(m.full_id)
            return True
        return False

    def select_defaults(self) -> int:
        """按当前管线各层 default_modules 自动勾选（只加不减）。"""
        pipe = self.current_pipeline()
        if not pipe:
            return 0
        n = 0
        for m in self.list_modules():
            if fid_key(m.full_id) in self.selected:
                continue
            for layer in pipe.layers:
                for ref in (layer.default_modules or []):
                    if fid_key(f"{m.category}:{m.id}") == fid_key(ref) \
                            or fid_key(m.id) == fid_key(ref):
                        self.selected.add(m.full_id)
                        n += 1
                        break
                else:
                    continue
                break
        return n

    def clear_selection(self) -> None:
        self.selected.clear()

    def selected_count(self) -> int:
        return len(self.selected)

    def selected_modules(self) -> Tuple[List[Module], List[str]]:
        """解析勾选集合 → (有效模块列表, 已失效的 full_id 列表)。"""
        modules: List[Module] = []
        missing: List[str] = []
        installed = {m.full_id: m for m in self.list_modules()}
        for fid in self.selected:
            m = installed.get(fid)
            if m is None:      # 宽匹配兜底
                m = self.get_module(fid)
            if m is not None:
                modules.append(m)
            else:
                missing.append(fid)
        # 按九层层位排序，生成时 order_modules 再按管线重排
        modules.sort(key=lambda x: (LAYER_IDS.index(x.layer)
                                    if x.layer in LAYER_IDS else 99, x.id))
        return modules, missing

    def check_module(self, m: Module) -> List[str]:
        """单模块校验（依赖 + 层位 + 管线允许集）。"""
        installed = [x.full_id for x in self.list_modules()]
        return validate_module(m, installed_ids=installed,
                               pipeline=self.current_pipeline())

    def assembly_issues(self) -> List[str]:
        """装配前整体检查（check_assembly 文本化）。"""
        modules, missing = self.selected_modules()
        issues = []
        if missing:
            issues.append(f"⚠ 以下勾选模块已不存在，已跳过：{', '.join(missing)}")
        issues.extend(check_assembly(modules, self.current_pipeline())
                      if self.current_pipeline() else [])
        return issues

    # ---------------- A：导入模块 ----------------
    def parse_module_text(self, text: str,
                          category_hint: str = "") -> Module:
        """解析模块文本；失败抛 ValueError（原因在消息内）。"""
        return parse_module(text, category_hint=category_hint)

    def import_module(self, text: str,
                      category_hint: str = "") -> Module:
        """解析并安装模块（覆盖同名）。返回已安装 Module。"""
        m = parse_module(text, category_hint=category_hint)
        m.source_md = text.strip()
        self.store.save_module(m)
        self.invalidate_modules()
        return m

    def remove_module(self, full_id: str) -> bool:
        ok = self.store.remove_module(full_id)
        if ok:
            self.selected.discard(full_id)
            self.invalidate_modules()
        return ok

    # ---------------- D：资产包 ----------------
    def list_asset_packs(self) -> List[AssetPack]:
        return self.store.list_asset_packs()

    def asset_pack_names(self) -> List[str]:
        return [a.name for a in self.list_asset_packs()]

    def get_asset_pack(self, name: str) -> Optional[AssetPack]:
        return self.store.get_asset_pack(name)

    def current_asset_pack(self) -> Optional[AssetPack]:
        name = self.store.get_config("asset_pack", "")
        return self.store.get_asset_pack(name) if name else None

    def set_asset_pack(self, name: str) -> None:
        self.store.set_config("asset_pack", name)

    # ---------------- E：生成 ----------------
    def generate(self, title: str = "") -> Tuple[str, List[str]]:
        """装配校验 + 生成文档。返回 (md文本, 汇总警告)。"""
        pipe = self.current_pipeline()
        if not pipe:
            raise RuntimeError("未找到可用管线，请先导入种子或选择管线")
        modules, missing = self.selected_modules()
        if not modules:
            raise RuntimeError("未选择任何有效模块，请先在模块库勾选")
        issues = self.assembly_issues()
        if missing:
            issues.append(f"已跳过失效勾选：{', '.join(missing)}")
        asset_pack = self.current_asset_pack()
        try:
            md, gen_warns = generate_document(
                pipe, modules, asset_pack=asset_pack, title=title)
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(f"生成失败：{exc}") from exc
        self.last_md = md
        self.last_warnings = issues + (["—— 生成器提示 ——"]
                                       + (gen_warns or ["（无）"]))
        return md, self.last_warnings

    def default_output_name(self) -> str:
        pipe = self.current_pipeline()
        return default_filename(pipe) if pipe else "output.md"

    def save_to(self, path: Path | str) -> bool:
        """把最近一次生成结果写入文件（UI 保存/分享用）。"""
        if not self.last_md:
            return False
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(self.last_md, encoding="utf-8")
        return True

    # ---------------- 统计 / 展示辅助 ----------------
    def stats(self) -> dict:
        return self.store.stats()

    def module_summary(self, m: Module, max_assets: int = 12) -> str:
        """模块字段摘要（A 屏导入预览 / B 屏详情）。"""
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
        return "\n".join(lines)