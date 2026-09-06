# -*- coding: utf-8 -*-
"""UI↔core 接线漂移扫描（38 方案 W0：check_ui_core_links）。

脉冲式接线波基础设施（合并稿交付物 #1）：冻结快照恢复后，UI 层
（desktop/src/ui）与 Android 引用层（android/app：controller/bootstrap/
ui/screens）引用的 core 符号须在 v2.5 core 中仍存在——冻结快照接的是
v2.0-era core，core 已演进至 v2.5（30 模块），引用面可能漂移。本脚本 AST
解析引用面 → 对 v2.5 core 逐一做符号存在性检查 → 输出三类清单：

  1. 符号缺失（硬断）：import 的 module/attr 在 core 中不存在 → 接线必须先修
  2. 软漂移：符号存在但签名可能变（本脚本只报存在性，签名比对靠冒烟断言）
  3. 可用：符号存在 → 无需处理

用法：python scripts/check_ui_core_links.py [--ui-dir ...] [--android-dir ...]
      [--controller ...] [--core-dir ...]

范围纪律：本脚本属 L3 接线工具，不参与 verify（L3 豁免纪律），作 smoke_gui
前置步骤；AST 解析零第三方依赖（L2 惯例）。
"""
from __future__ import annotations

import argparse
import ast
import sys
from pathlib import Path
from typing import Dict, List, Optional

ROOT = Path(__file__).resolve().parent.parent

# 模块级引用哨兵：ast.Import（import core.X / import app.core.X）不绑定具名
# 符号，只要求模块文件存在。scan 对哨兵做模块存在性检查。
MODULE_REF = "<module>"


def _normalize_core_mod(mod: str) -> Optional[str]:
    """把任意引用形态归一为 core 模块路径；非 core 引用返回 None。

    支持的真实形态：
      from ..core.models import X      → level=2, module="core.models"（desktop ui）
      from .core.generator import X    → level=1, module="core.generator"
                                        （android controller/bootstrap 相对导入）
      from app.core.models import X    → level=0, module="app.core.models"
                                        （android ui/screens 绝对导入）
      import core.models / import app.core.models → 模块级引用（同上归一）

    归一判据不看 level 与包前缀：只要模块路径里有一个段恰为 "core"，即取
    core 起的后缀——避免 level=0 绝对导入被相对导入判据误丢。
    """
    parts = mod.split(".")
    try:
        i = parts.index("core")
    except ValueError:
        return None
    return ".".join(parts[i:])


def extract_imports(paths: List[Path]) -> Dict[str, List[str]]:
    """AST 解析一组文件，返回 {core 模块: [符号...]}。

    识别形态（统一先归一化到 core 模块路径）：
      from ..core.X import Y / from .core.X import Y / from app.core.X import Y
          → core.X: [Y]
      from ..core import X          → core: [X]（X 是模块或 __init__ 导出符号）
      from ..core.X import (A, B)   → 多符号（ast 已拆成多个 ImportFrom）
      import core.X / import app.core.X → core.X: [MODULE_REF]（模块级引用）
    非 core 引用（标准库/第三方/包内跨模块）一律忽略。
    """
    refs: Dict[str, List[str]] = {}
    for path in paths:
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except (OSError, SyntaxError):
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                # import core.X / import app.core.X：绑定的是模块整体
                for alias in node.names:
                    core_mod = _normalize_core_mod(alias.name)
                    if core_mod is None:
                        continue
                    refs.setdefault(core_mod, []).append(MODULE_REF)
            elif isinstance(node, ast.ImportFrom):
                core_mod = _normalize_core_mod(node.module or "")
                if core_mod is None:
                    continue
                for alias in node.names:
                    refs.setdefault(core_mod, []).append(alias.name)
    return refs


def _locate_module(core_root: Path, core_mod: str) -> Optional[Path]:
    """core.X.Y → 模块文件（.py 或 __init__.py）；不存在返回 None。

    core → core_root/__init__.py；core.X → 从最深前缀向下试，首个存在的
    X.py / X/__init__.py；core.X.Y → X/Y.py → X/Y/__init__.py → X.py 递减。
    """
    if core_mod == "core":
        init = core_root / "__init__.py"
        return init if init.exists() else None
    rel = core_mod[len("core."):] if core_mod.startswith("core.") else core_mod
    parts = rel.split(".")
    for end in range(len(parts), 0, -1):
        cand = core_root.joinpath(*parts[:end])
        if cand.with_suffix(".py").exists():
            return cand.with_suffix(".py")
        if (cand / "__init__.py").exists():
            return cand / "__init__.py"
    return None


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


def collect_scan_paths(ui_root, android_root,
                       controller=None) -> List[Path]:
    """构建引用面文件清单（desktop ui + android 引用层）。

    递归收集两棵引用树下的 .py：排除 __init__.py，并跳过路径中含 core 段
    的目录（core 是被检查的镜像/目标，不是引用面）。controller 为兼容参数，
    单独传入的文件仍会被加入（android 根下已含时幂等去重）。结果排序。
    """
    files: List[Path] = []
    for root in (Path(ui_root), Path(android_root)):
        if not root.is_dir():
            continue
        for p in root.rglob("*.py"):
            if p.name == "__init__.py":
                continue
            if any(part == "core"
                   for part in p.relative_to(root).parts):
                continue  # core 镜像目录不是引用面
            files.append(p)
    if controller:
        c = Path(controller)
        if c.is_file():
            files.append(c)
    return sorted(set(files))


def scan(ui_paths: List[Path], core_root: Path) -> Dict[str, List[str]]:
    """扫描引用面 import 面 → 三类清单。

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
            if sym == MODULE_REF:
                # import core.X：只要求模块文件存在，无需具体符号
                if _locate_module(core_root, core_mod) is not None:
                    result["ok"].append(f"{core_mod}（模块）")
                else:
                    result["missing"].append(f"{core_mod}（模块缺失）")
                continue
            if core_mod == "core":
                # from ..core import X：X 是模块则 OK；否则查 __init__ 导出
                if _locate_module(core_root, f"core.{sym}") is not None:
                    result["ok"].append(f"core:{sym}（模块）")
                elif _module_has_attr(core_root / "__init__.py", sym):
                    result["ok"].append(f"core:{sym}")
                else:
                    result["missing"].append(f"core:{sym}")
                continue
            # 定位符号所在模块文件
            found_path = _locate_module(core_root, core_mod)
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
    ap.add_argument("--android-dir",
                    default=str(ROOT / "android" / "app"),
                    help="Android 引用层根目录（缺省 android/app，递归收集）")
    ap.add_argument("--controller", default=None,
                    help="额外单文件（已含于 --android-dir 时无需传）")
    ap.add_argument("--core-dir", default=str(ROOT / "desktop" / "src" / "core"),
                    help="core 目录（缺省 desktop/src/core）")
    args = ap.parse_args(argv)

    ui_paths = collect_scan_paths(args.ui_dir, args.android_dir,
                                  args.controller)
    core_root = Path(args.core_dir)

    if not ui_paths:
        print(">>> 扫描面为空：ui/android 引用目录下找不到可扫描的 .py 文件",
              file=sys.stderr)
        print("    （ui_dir/android_dir 是否存在？空面 ≠ 干净面——拒绝放行）",
              file=sys.stderr)
        return 2
    if not core_root.is_dir():
        print(f">>> core 目录不存在：{core_root}", file=sys.stderr)
        return 2

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
