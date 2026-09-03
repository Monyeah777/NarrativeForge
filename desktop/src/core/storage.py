"""存储层：~/.NarrativeForge 目录管理（config/modules/assets/presets/cache）。

目录结构（指令集 3.2）：
~/.NarrativeForge/
├── config.json          # 工具配置（管线选择、激活资产包）
├── modules/<分类>/<id_名称>/module.json + source.md
├── assets/<包名>/asset.json
├── presets/<预设名>.json
└── cache/community_index.json

NF_HOME 默认 ~/.NarrativeForge，可用环境变量 NARRATIVE_FORGE_HOME 覆盖（测试友好）。
"""
from __future__ import annotations

import json
import os
import re
import shutil
from pathlib import Path
from typing import List, Optional

from .models import Module, AssetPack, Preset, now_str, fid_key

ENV_HOME = "NARRATIVE_FORGE_HOME"


def default_home() -> Path:
    env = os.environ.get(ENV_HOME)
    if env:
        return Path(env).expanduser()
    return Path.home() / ".NarrativeForge"


class Store:
    """对 NF_HOME 下所有本地数据的管理器。"""

    def __init__(self, home: Optional[Path | str] = None):
        self.home = Path(home) if home else default_home()
        self.config_path = self.home / "config.json"
        self.modules_root = self.home / "modules"
        self.assets_root = self.home / "assets"
        self.presets_root = self.home / "presets"
        self.cache_root = self.home / "cache"
        self._ensure_dirs()

    # ---------- 基础 ----------
    def _ensure_dirs(self):
        for d in (self.home, self.modules_root, self.assets_root,
                  self.presets_root, self.cache_root):
            d.mkdir(parents=True, exist_ok=True)

    def _safe_name(self, s: str) -> str:
        """文件名安全化"""
        return re.sub(r"[^\w\u4e00-\u9fff-]", "_", s).strip("_") or "unnamed"

    # ---------- config ----------
    def load_config(self) -> dict:
        if self.config_path.exists():
            try:
                return json.loads(self.config_path.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {"pipeline": "P01", "asset_pack": "", "recent": []}

    def save_config(self, cfg: dict):
        self.config_path.write_text(
            json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")

    def get_config(self, key: str, default=None):
        return self.load_config().get(key, default)

    def set_config(self, key: str, value):
        cfg = self.load_config()
        cfg[key] = value
        self.save_config(cfg)

    # ---------- 模块库 ----------
    def module_dirs(self) -> List[Path]:
        """返回所有已安装模块的目录（每个模块一个文件夹）"""
        out = []
        if not self.modules_root.exists():
            return out
        for cat in sorted(self.modules_root.iterdir()):
            if cat.is_dir():
                for md in sorted(cat.iterdir()):
                    if md.is_dir() and (md / "module.json").exists():
                        out.append(md)
        return out

    def list_modules(self) -> List[Module]:
        mods = []
        for d in self.module_dirs():
            try:
                m = Module.from_json(
                    json.loads((d / "module.json").read_text(encoding="utf-8")))
                # source.md 缺失时回退到内嵌 source_md
                src = d / "source.md"
                if src.exists():
                    m.source_md = src.read_text(encoding="utf-8")
                mods.append(m)
            except Exception:
                continue
        return mods

    def get_module(self, full_id: str) -> Optional[Module]:
        """按 full_id 取模块。类别前缀短名/长名均可（情感:M22 ↔ 情感类:M22）。"""
        key = fid_key(full_id)
        for m in self.list_modules():
            if fid_key(m.full_id) == key:
                return m
        return None

    def save_module(self, m: Module) -> Path:
        """保存/更新一个模块。目录: modules/<分类>/<id>_<名称>/"""
        if not m.id:
            raise ValueError("模块 id 不能为空")
        if ":" in m.id:  # 兼容带前缀传入
            cat, num = m.id.split(":", 1)
            m.category = m.category or cat
            m.id = num
        if not m.installed_at:
            m.installed_at = now_str()
        d = self.modules_root / self._safe_name(m.category) / \
            f"{self._safe_name(m.id)}_{self._safe_name(m.name)}"
        # 清理同 full_id 的旧目录（改名/重存遗留），避免双目录并存
        key = fid_key(m.full_id)
        for old in self.module_dirs():
            if old == d:
                continue
            try:
                om = Module.from_json(json.loads(
                    (old / "module.json").read_text(encoding="utf-8")))
            except Exception:
                continue
            if fid_key(om.full_id) == key:
                shutil.rmtree(old, ignore_errors=True)
        d.mkdir(parents=True, exist_ok=True)
        (d / "module.json").write_text(
            json.dumps(m.to_json(), ensure_ascii=False, indent=2), encoding="utf-8")
        if m.source_md:
            (d / "source.md").write_text(m.source_md, encoding="utf-8")
        return d

    def remove_module(self, full_id: str) -> bool:
        """删除模块（清理所有同 full_id 目录）。"""
        key = fid_key(full_id)
        removed = False
        for d in list(self.module_dirs()):
            try:
                mm = Module.from_json(json.loads(
                    (d / "module.json").read_text(encoding="utf-8")))
            except Exception:
                continue
            if fid_key(mm.full_id) == key:
                shutil.rmtree(d, ignore_errors=True)
                removed = True
        return removed

    def toggle_module(self, full_id: str) -> Optional[Module]:
        m = self.get_module(full_id)
        if m:
            m.enabled = not m.enabled
            self.save_module(m)
        return m

    # ---------- 资产包 ----------
    def list_asset_packs(self) -> List[AssetPack]:
        out = []
        if not self.assets_root.exists():
            return out
        for d in sorted(self.assets_root.iterdir()):
            jf = d / "asset.json"
            if jf.exists():
                try:
                    a = AssetPack.from_json(
                        json.loads(jf.read_text(encoding="utf-8")))
                    a.source_dir = str(d)
                    out.append(a)
                except Exception:
                    continue
        return out

    def get_asset_pack(self, name: str) -> Optional[AssetPack]:
        for a in self.list_asset_packs():
            if a.name == name:
                return a
        return None

    def save_asset_pack(self, a: AssetPack) -> Path:
        if not a.installed_at:
            a.installed_at = now_str()
        d = self.assets_root / self._safe_name(a.name)
        d.mkdir(parents=True, exist_ok=True)
        (d / "asset.json").write_text(
            json.dumps(a.to_json(), ensure_ascii=False, indent=2), encoding="utf-8")
        return d

    def remove_asset_pack(self, name: str) -> bool:
        a = self.get_asset_pack(name)
        if not a:
            return False
        d = self.assets_root / self._safe_name(a.name)
        shutil.rmtree(d, ignore_errors=True)
        return True

    # ---------- 预设 ----------
    def list_presets(self) -> List[Preset]:
        out = []
        if not self.presets_root.exists():
            return out
        for f in sorted(self.presets_root.glob("*.json")):
            try:
                out.append(Preset.from_json(
                    json.loads(f.read_text(encoding="utf-8"))))
            except Exception:
                continue
        return out

    def save_preset(self, p: Preset) -> Path:
        if not p.created_at:
            p.created_at = now_str()
        f = self.presets_root / f"{self._safe_name(p.name)}.json"
        f.write_text(json.dumps(p.to_json(), ensure_ascii=False, indent=2),
                     encoding="utf-8")
        return f

    def remove_preset(self, name: str) -> bool:
        f = self.presets_root / f"{self._safe_name(name)}.json"
        if f.exists():
            f.unlink()
            return True
        return False

    # ---------- 缓存 ----------
    def save_cache(self, key: str, data):
        (self.cache_root / f"{key}.json").write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def load_cache(self, key: str) -> Optional[dict]:
        f = self.cache_root / f"{key}.json"
        if f.exists():
            try:
                return json.loads(f.read_text(encoding="utf-8"))
            except Exception:
                return None
        return None

    # ---------- 统计 ----------
    def stats(self) -> dict:
        return {
            "modules": len(self.list_modules()),
            "assets": len(self.list_asset_packs()),
            "presets": len(self.list_presets()),
        }