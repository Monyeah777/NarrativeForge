# -*- coding: utf-8 -*-
"""UI↔core 接线漂移扫描（38 方案 W0：check_ui_core_links）。

脉冲式接线波基础设施（合并稿交付物 #1）：冻结快照恢复后，UI 层（desktop/
src/ui）与 Android controller 引用的 core 符号须在 v2.5 core 中仍存在——
冻结快照接的是 v2.0-era core，core 已演进至 v2.5（30 模块），引用面可能
漂移。本脚本 AST 解析引用面 → 对 v2.5 core 逐一做符号存在性检查 → 输出
三类清单：

  1. 符号缺失（硬断）：import 的 module/attr 在 core 中不存在 → 接线必须先修
  2. 软漂移：符号存在但签名可能变（本脚本只报存在性，签名比对靠冒烟断言）
  3. 可用：符号存在 → 无需处理

用法：python scripts/check_ui_core_links.py [--ui-dir ...] [--core-dir ...]

范围纪律：本脚本属 L3 接线工具，不参与 verify（L3 豁免纪律），作 smoke_gui
前置步骤；AST 解析零第三方依赖（L2 惯例）。
"""
from __future__ import annotations

import argparse
import ast
import sys
from pathlib import Path
from typing import Dict, List, Tuple

ROOT = Path(__file__).resolve().parent.parent


def extract_imports(paths: List[Path]) -> Dict[str, List[str]]:
    """AST 解析一组文件，返回 {core 模块: [符号...]}。

    识别形态：
      from ..core.X import Y        → core.X: [Y]
      from ..core import X          → core: [X]（X 是模块或符号，交给检查层）
      from ..core.X import (A, B)   → 多符号（ast 已拆成多个 ImportFrom）
      import core.X                 → 少见，忽略（ui 惯例是 from ..core）
    """
    refs: Dict[str, List[str]] = {}
    for path in paths:
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except (OSError, SyntaxError):
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.ImportFrom):
                continue
            mod = node.module or ""
            # 相对导入引用包外 core：
            #   from ..core.models import X → level=2, module="core.models"（ui）
            #   from .core.generator import Y → level=1, module="core.generator"（android controller，core 为 sync 镜像同构）
            # 统一判据：level>=1 且 module 以 core 开头
            if node.level >= 1 and mod.startswith("core"):
                core_mod = mod  # "core.models" 等
            else:
                continue
            for alias in node.names:
                sym = alias.name
                refs.setdefault(core_mod, []).append(sym)
    return refs


def _core_module_exists(core_root: Path, core_mod: str) -> bool:
    """core.X.Y → core_root/X/Y.py 存在性（X 可为包目录）。"""
    if core_mod == "core":
        return (core_root / "__init__.py").exists()
    rel = core_mod[len("core."):] if core_mod.startswith("core.") else core_mod
    # 尝试 文件.py / 目录/__init__.py
    parts = rel.split(".")
    for end in range(len(parts), 0, -1):
        p = core_root.joinpath(*parts[:end])
        if p.with_suffix(".py").exists():
            return True
        if (p / "__init__.py").exists():
            return True
        # 前缀模块存在即可（from ..core.X.Y import Z 中 X.Y 是深路径）
    return False


def _module_has_attr(module_path: Path, attr: str) -> bool:
    """AST 检查模块顶层是否定义 attr（函数/类/赋值/import 重导出）。"""
    try:
        tree = ast.parse(module_path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError):
        return False
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef,
                             ast.ClassDef)):
            if node.name == attr:
                return True
        elif isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id == attr:
                    return True
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                if alias.name == attr or (
                        alias.asname and alias.asname == attr):
                    return True
    return False


def scan(ui_paths: List[Path], core_root: Path) -> Dict[str, List[str]]:
    """扫描 UI/controller import 面 → 三类清单。

    返回 {"missing": [...], "soft": [...], "ok": [...], "refs": {...}}
    每项格式 "模块: 符号"（missing/soft）或 "模块: 符号"(ok)。
    """
    refs = extract_imports(ui_paths)
    result = {"missing": [], "soft": [], "ok": [], "refs": refs}
    for core_mod, syms in sorted(refs.items()):
        for sym in sorted(set(syms)):
            if sym == "*":
                result["soft"].append(f"{core_mod}:*（通配导入，人工核对）")
                continue
            if core_mod == "core":
                # from ..core import X：X 是模块则 OK；否则查 __init__ 导出
                mod_file = core_root / f"{sym}.py"
                if mod_file.exists() or (core_root / sym / "__init__.py").exists():
                    result["ok"].append(f"core:{sym}（模块）")
                elif _module_has_attr(core_root / "__init__.py", sym):
                    result["ok"].append(f"core:{sym}")
                else:
                    result["missing"].append(f"core:{sym}")
                continue
            # 定位符号所在模块文件
            rel = core_mod[len("core."):] if core_mod.startswith("core.") \
                else core_mod
            parts = rel.split(".")
            found_path = None
            for end in range(len(parts), 0, -1):
                cand = core_root.joinpath(*parts[:end])
                if cand.with_suffix(".py").exists():
                    found_path = cand.with_suffix(".py")
                    break
                if (cand / "__init__.py").exists():
                    found_path = cand / "__init__.py"
                    break
            if found_path is None:
                result["missing"].append(f"{core_mod}:{sym}（模块缺失）")
                continue
            if _module_has_attr(found_path, sym):
                result["ok"].append(f"{core_mod}:{sym}")
            else:
                result["missing"].append(f"{core_mod}:{sym}")
    return result


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        prog="check_ui_core_links",
        description="UI↔core 接线漂移扫描（38 W0）")
    ap.add_argument("--ui-dir", default=str(ROOT / "desktop" / "src" / "ui"),
                    help="UI 层目录（缺省 desktop/src/ui）")
    ap.add_argument("--controller", default=str(ROOT / "android" / "app"
                                                / "controller.py"),
                    help="Android controller 路径（缺省 android/app/controller.py）")
    ap.add_argument("--core-dir", default=str(ROOT / "desktop" / "src" / "core"),
                    help="core 目录（缺省 desktop/src/core）")
    args = ap.parse_args(argv)

    ui_root = Path(args.ui_dir)
    ui_paths = [p for p in ui_root.glob("*.py") if p.name != "__init__.py"]
    controller = Path(args.controller)
    if controller.exists():
        ui_paths.append(controller)
    core_root = Path(args.core_dir)

    result = scan(ui_paths, core_root)
    print("== check_ui_core_links（38 W0 漂移扫描）==")
    print(f"  扫描 {len(ui_paths)} 文件 import 面 → core "
          f"{len(result['refs'])} 模块引用")
    for label, key in (("硬断缺失", "missing"), ("软漂移待比对", "soft"),
                       ("可用", "ok")):
        items = result[key]
        print(f"  [{label}] {len(items)} 项")
        for it in items[:20]:
            print(f"    {it}")
        if len(items) > 20:
            print(f"    … 共 {len(items)} 项")
    hard = len(result["missing"])
    if hard:
        print(f">>> 硬断缺失 {hard} 项——接线前必须先修（漂移清单入接线账）")
        return 1
    print(">>> 无硬断缺失——UI import 面与 v2.5 core 符号兼容")
    return 0


if __name__ == "__main__":
    sys.exit(main())
