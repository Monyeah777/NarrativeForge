"""种子自举：APK 首装时把内置 seed 数据导入 Store（幂等，带版本标记）。

seed 目录布局（由 scripts/sync_android.sh 从仓库根同步，.gitignore 生成物）：
    android/app/seed/03_管线库/*.md
    android/app/seed/04_模块库/<分类>/*.md
    android/app/seed/05_资产库/<包>/*.md

逻辑与 desktop/scripts/seed_from_repo.py 保持一致（管线缓存 pipelines.json、
模块 parse_module 入库、资产转 AssetPack），仅数据来源改为打包内置的 seed。
导入完成后写 cache/seed_version.json；版本一致时跳过，保护用户自建/修改数据。
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from . import config
from .core.models import AssetPack, now_str
from .core.parser import parse_asset_entries_from_text, parse_module
from .core.pipeline_loader import discover_pipelines
from .core.storage import Store

_SEED_VERSION_KEY = "seed_version"


def seeded_version(store: Store) -> Optional[str]:
    """已导入的种子版本；从未导入返回 None。"""
    d = store.load_cache(_SEED_VERSION_KEY)
    return (d or {}).get("version")


def _mark_seeded(store: Store, version: str) -> None:
    store.save_cache(_SEED_VERSION_KEY, {"version": version})


def seed_from_dir(store: Store, seed_root: Path, force: bool = False) -> dict:
    """把内置 seed_root 导入 store。

    返回统计 dict：
      {"modules": n, "asset_packs": n, "pipelines": n, "errors": [..]}
    force=True 时无视版本标记全量重导（覆盖同名条目，与桌面 seed 脚本一致）。
    """
    if not force and seeded_version(store) == config.APP_VERSION:
        return {"modules": 0, "asset_packs": 0, "pipelines": 0,
                "skipped": True, "errors": []}

    stats = {"modules": 0, "asset_packs": 0, "pipelines": 0,
             "skipped": False, "errors": []}

    # ---- 管线：03_管线库/*.md → cache/pipelines.json ----
    pipe_dir = seed_root / "03_管线库"
    if pipe_dir.exists():
        try:
            plist = discover_pipelines(pipe_dir)
            store.save_cache("pipelines", [p.to_json() for p in plist])
            stats["pipelines"] = len(plist)
        except Exception as exc:  # noqa: BLE001
            stats["errors"].append(f"管线导入失败: {exc}")

    # ---- 模块：04_模块库/<分类>/*.md → store.save_module ----
    mod_root = seed_root / "04_模块库"
    if mod_root.exists():
        for cat_dir in sorted(mod_root.iterdir()):
            if not cat_dir.is_dir():
                continue
            for md in sorted(cat_dir.glob("*.md")):
                try:
                    text = md.read_text(encoding="utf-8")
                    m = parse_module(text)
                    # 分类以所在目录为准（仓库文件可能不含分类前缀）
                    if m.category == "通用类" and cat_dir.name != "通用类":
                        m.category = cat_dir.name
                    stem = md.stem
                    if ":" in stem:
                        prefix, _rest = stem.split(":", 1)
                        if prefix in ("情感", "生存", "世界", "事件", "通用", "技术文档"):
                            if m.category == "通用类":
                                m.category = prefix + "类"
                    m.source_md = text
                    store.save_module(m)
                    stats["modules"] += 1
                except Exception as exc:  # noqa: BLE001
                    stats["errors"].append(f"模块解析失败 {md.name}: {exc}")

    # ---- 资产：05_资产库/<包>/*.md → store.save_asset_pack ----
    asset_root = seed_root / "05_资产库"
    if asset_root.exists():
        for pkg in sorted(asset_root.iterdir()):
            if not pkg.is_dir() or pkg.name == "用户自定义":
                continue
            entries: dict = {}
            for f in sorted(pkg.glob("*.md")):
                try:
                    text = f.read_text(encoding="utf-8")
                    parts = parse_asset_entries_from_text(text)
                    if parts:
                        entries.update(parts)
                    else:
                        entries[f.stem] = text
                except Exception as exc:  # noqa: BLE001
                    stats["errors"].append(
                        f"资产解析失败 {pkg.name}/{f.name}: {exc}")
            if entries:
                a = AssetPack(name=pkg.name, version="1.0.0",
                              entries=entries, installed_at=now_str())
                store.save_asset_pack(a)
                stats["asset_packs"] += 1

    if not stats["errors"]:
        _mark_seeded(store, config.APP_VERSION)
    return stats
