#!/usr/bin/env python3
"""种子数据导入器：从 NinFenz 仓库导入 模块/资产包/管线 到本地 NF_HOME。

用法：
    python3 desktop/scripts/seed_from_repo.py [仓库根目录] [NF_HOME]

- 管线：解析 03_管线库/*.md → 保存为 cache/pipelines.json（工具启动时读取）
- 模块：扫描 04_模块库/<分类>/*.md → parse_module（仓库格式）→ store.save_module
- 资产：扫描 05_资产库/<包>/*.md → 键值分段 → store.save_asset_pack
- 范围：仅官方核心结构（03/04/05）；community/ 社区领域包（P02/P03）不由此导入

幂等：重复执行会覆盖同名模块/资产（module.json 每次重写）。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

# 保证可独立运行：把项目根加入 sys.path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from core.models import Module, AssetPack, now_str          # noqa: E402
from core.storage import Store, default_home                # noqa: E402
from core.parser import parse_module, parse_asset_entries_from_text  # noqa: E402
from core.pipeline_loader import discover_pipelines          # noqa: E402


def find_repo_root() -> Path:
    """自动定位仓库根：**本脚本自定位优先** → 当前工作目录 → 历史候选路径 → 报错。

    为什么要自定位（2026-10-01 取证）：此前只试 `/tmp/NinFenz` 等三个**固定历史
    路径**——在本仓真实工作目录（Windows / 任意克隆点）一律找不到，命令直接 SystemExit，
    等于「路径不可达」。仓库根可从本文件位置算（`desktop/scripts/` 的上两级），先试它；
    当前工作目录其次；历史盘 / 手机路径保留给旧环境。都没有才报错，并在指引里要求显式传参。
    """
    candidates = [Path(__file__).resolve().parents[2],   # desktop/scripts/ → 仓库根
                  Path.cwd(),
                  Path("/tmp/NinFenz"),
                  Path("/sdcard/Download/NinFenz"),
                  Path.home() / "NinFenz"]
    for cand in candidates:
        if (cand / "03_管线库").is_dir():
            return cand
    raise SystemExit("找不到 NinFenz 仓库（需含 03_管线库 目录）：已试 %s；"
                     "请显式传入仓库根，如 `python3 desktop/scripts/seed_from_repo.py <仓库根>`"
                     % "、".join(str(c) for c in candidates))


def seed_modules(repo: Path, store: Store) -> dict:
    stats = {"ok": 0, "fail": 0, "by_cat": {}}
    cat_root = repo / "04_模块库"
    if not cat_root.exists():
        return stats
    for cat in sorted(cat_root.iterdir()):
        if not cat.is_dir():
            continue
        for md in sorted(cat.glob("*.md")):
            try:
                text = md.read_text(encoding="utf-8")
                m = parse_module(text)
                # 类别以所在目录为准（仓库文件名可能不含分类）
                if m.category in ("通用类",) and cat.name != "通用类":
                    m.category = cat.name
                # 文件名有时含完整前缀（情感:M22_三冲动驱动.md）
                stem = md.stem
                if ":" in stem:
                    prefix, rest = stem.split(":", 1)
                    if prefix in ("情感", "生存", "世界", "事件", "通用", "技术文档"):
                        if m.category == "通用类":
                            m.category = prefix + "类"
                m.source_md = text
                store.save_module(m)
                stats["ok"] += 1
                stats["by_cat"][cat.name] = stats["by_cat"].get(cat.name, 0) + 1
            except Exception as e:
                stats["fail"] += 1
                print(f"  ! 解析失败 {md.name}: {e}")
    return stats


def seed_assets(repo: Path, store: Store) -> dict:
    stats = {"ok": 0, "fail": 0, "names": []}
    asset_root = repo / "05_资产库"
    if not asset_root.exists():
        return stats
    for pkg in sorted(asset_root.iterdir()):
        if not pkg.is_dir() or pkg.name == "用户自定义":
            continue
        entries = {}
        for f in sorted(pkg.glob("*.md")):
            try:
                text = f.read_text(encoding="utf-8")
                parts = parse_asset_entries_from_text(text)
                if parts:
                    # 单文件多键 → 展开
                    entries.update(parts)
                else:
                    entries[f.stem] = text
            except Exception as e:
                print(f"  ! 资产解析失败 {pkg.name}/{f.name}: {e}")
        if entries:
            a = AssetPack(name=pkg.name, version="1.0.0",
                          entries=entries, installed_at=now_str())
            store.save_asset_pack(a)
            stats["ok"] += 1
            stats["names"].append(pkg.name)
    return stats


def seed_pipelines(repo: Path, store: Store) -> dict:
    pipe_dir = repo / "03_管线库"
    if not pipe_dir.exists():
        return {"ok": 0, "names": []}
    plist = discover_pipelines(pipe_dir)
    store.save_cache("pipelines", [p.to_json() for p in plist])
    return {"ok": len(plist), "names": [p.id for p in plist]}


def main() -> int:
    repo_arg = sys.argv[1] if len(sys.argv) > 1 else ""
    home_arg = sys.argv[2] if len(sys.argv) > 2 else ""
    repo = Path(repo_arg) if repo_arg else find_repo_root()
    home = Path(home_arg) if home_arg else default_home()

    # NF_HOME 缺省 = ~/.NinFenz（可用环境变量 NARRATIVE_FORGE_HOME 覆盖，测试友好）
    store = Store(home)
    print(f"仓库: {repo}")
    print(f"NF_HOME: {store.home}")
    print("---- 导入管线 ----")
    rp = seed_pipelines(repo, store)
    print(f"  管线 {rp['ok']} 个: {rp['names']}")
    print("---- 导入模块 ----")
    rm = seed_modules(repo, store)
    print(f"  模块成功 {rm['ok']} 个 / 失败 {rm['fail']} 个")
    for cat, n in rm["by_cat"].items():
        print(f"    {cat}: {n}")
    print("---- 导入资产包 ----")
    ra = seed_assets(repo, store)
    print(f"  资产包 {ra['ok']} 个: {ra['names']}")
    print("---- 汇总 ----")
    st = store.stats()
    print(f"  本地统计: 模块 {st['modules']} / 资产 {st['assets']} / 预设 {st['presets']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
