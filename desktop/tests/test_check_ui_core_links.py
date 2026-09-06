# -*- coding: utf-8 -*-
"""check_ui_core_links 单测（38 W0：UI↔core 漂移扫描逻辑）。

运行：cd desktop && python -m unittest tests.test_check_ui_core_links -v
覆盖：extract_imports 识别 ui（..core level2）与 controller（.core level1）
形态；scan 对缺失符号报硬断、存在符号报可用；main 退出码。
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent
                       / "scripts"))

from check_ui_core_links import (  # noqa: E402
    extract_imports,
    scan,
    _module_has_attr,
)

ROOT = Path(__file__).resolve().parent.parent.parent


def _mk_file(d: Path, name: str, content: str) -> Path:
    p = d / name
    p.write_text(content, encoding="utf-8")
    return p


class TestExtractImports(unittest.TestCase):
    def test_ui_level2_relative(self):
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            f = _mk_file(d, "zone.py",
                         "from ..core.models import Module, Pipeline\n"
                         "from ..core.quality_gate import run_gate\n")
            refs = extract_imports([f])
            self.assertEqual(set(refs["core.models"]),
                             {"Module", "Pipeline"})
            self.assertEqual(refs["core.quality_gate"], ["run_gate"])

    def test_controller_level1_relative(self):
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            f = _mk_file(d, "controller.py",
                         "from .core.generator import default_filename\n")
            refs = extract_imports([f])
            self.assertEqual(refs["core.generator"], ["default_filename"])

    def test_non_core_ignored(self):
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            f = _mk_file(d, "x.py",
                         "import os\nfrom PySide6 import QtWidgets\n"
                         "from . import common\n")
            self.assertEqual(extract_imports([f]), {})


class TestModuleHasAttr(unittest.TestCase):
    def test_func_and_class(self):
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            m = _mk_file(d, "mod.py",
                         "def run_gate(): pass\nclass Module: pass\n"
                         "from ..parser import parse_module\n"
                         "x = 1\n")
            self.assertTrue(_module_has_attr(m, "run_gate"))
            self.assertTrue(_module_has_attr(m, "Module"))
            self.assertTrue(_module_has_attr(m, "parse_module"))  # 重导出
            self.assertTrue(_module_has_attr(m, "x"))
            self.assertFalse(_module_has_attr(m, "不存在"))


class TestScan(unittest.TestCase):
    def test_missing_symbol_reported(self):
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            ui = d / "ui"
            core = d / "core"
            ui.mkdir()
            core.mkdir()
            _mk_file(ui, "z.py",
                     "from ..core.models import Module, 不存在的符号\n")
            _mk_file(core, "models.py", "class Module: pass\n")
            res = scan([ui / "z.py"], core)
            self.assertTrue(any("不存在的符号" in x for x in res["missing"]))
            self.assertTrue(any("Module" in x for x in res["ok"]))

    def test_real_core_no_hard_breaks(self):
        """真实 ui + controller 对 v2.5 core 无硬断（38 W0 主断言）。"""
        ui_dir = ROOT / "desktop" / "src" / "ui"
        ui_paths = [p for p in ui_dir.glob("*.py")
                    if p.name != "__init__.py"]
        ctrl = ROOT / "android" / "app" / "controller.py"
        if ctrl.exists():
            ui_paths.append(ctrl)
        core = ROOT / "desktop" / "src" / "core"
        res = scan(ui_paths, core)
        self.assertEqual(res["missing"], [])


if __name__ == "__main__":
    unittest.main()
