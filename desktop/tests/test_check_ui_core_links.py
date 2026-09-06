# -*- coding: utf-8 -*-
"""check_ui_core_links 单测（38 W0：UI↔core 漂移扫描逻辑）。

运行：cd desktop && python -m unittest tests.test_check_ui_core_links -v
覆盖：extract_imports 识别 ui（..core level2）、android controller/bootstrap
（.core level1）与 android ui/screens（app.core level0 绝对导入）形态及
import core.* 模块级引用；scan 对缺失符号报硬断、存在符号报可用；引用面
收集含 android 全引用层；空扫描面 fail-closed（main 返回 2）；main 退出码。
"""
from __future__ import annotations

import contextlib
import io
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent
                       / "scripts"))

from check_ui_core_links import (  # noqa: E402
    MODULE_REF,
    _module_has_attr,
    collect_scan_paths,
    extract_imports,
    main,
    scan,
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

    def test_screens_level0_absolute(self):
        """android/ui/screens.py 形态：from app.core.*（level=0）不被丢弃。"""
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            f = _mk_file(d, "screens.py",
                         "from app.core.models import Module\n"
                         "from app.core.parser import parse_module\n")
            refs = extract_imports([f])
            self.assertEqual(refs["core.models"], ["Module"])
            self.assertEqual(refs["core.parser"], ["parse_module"])

    def test_import_core_module(self):
        """import core.X / import app.core.X → 模块级引用（MODULE_REF）。"""
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            f = _mk_file(d, "x.py",
                         "import core.generator\n"
                         "import app.core.parser as p\n")
            refs = extract_imports([f])
            self.assertEqual(refs["core.generator"], [MODULE_REF])
            self.assertEqual(refs["core.parser"], [MODULE_REF])

    def test_non_core_ignored(self):
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            f = _mk_file(d, "x.py",
                         "import os\nfrom PySide6 import QtWidgets\n"
                         "from . import common\n")
            self.assertEqual(extract_imports([f]), {})

    def test_from_core_import_module_alias(self):
        """from ..core import X as imp：X 归一为 core 模块引用。"""
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            f = _mk_file(d, "zone.py",
                         "from ..core import import_adapter as imp\n")
            refs = extract_imports([f])
            self.assertEqual(refs["core"], ["import_adapter"])


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


class TestCollectScanPaths(unittest.TestCase):
    def test_android_full_reference_surface(self):
        """引用面含 android 全引用层：controller/bootstrap/screens 皆在列。"""
        ui = ROOT / "desktop" / "src" / "ui"
        android = ROOT / "android" / "app"
        paths = collect_scan_paths(ui, android)
        names = {p.name for p in paths}
        self.assertIn("bootstrap.py", names)
        self.assertIn("controller.py", names)
        self.assertIn("screens.py", names)
        # ui 顶层引用文件也在面内
        self.assertIn("zone_g_community.py", names)

    def test_empty_dirs_yield_empty(self):
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            self.assertEqual(collect_scan_paths(d / "no_ui",
                                                d / "no_android"), [])


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

    def test_module_ref_resolved_and_missing(self):
        """import core.X：模块存在报 ok，模块缺失报硬断。"""
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            ui = d / "ui"
            core = d / "core"
            ui.mkdir()
            core.mkdir()
            _mk_file(ui, "a.py", "import core.models\nimport core.ghost\n")
            _mk_file(core, "models.py", "class Module: pass\n")
            res = scan([ui / "a.py"], core)
            self.assertTrue(any("core.models" in x for x in res["ok"]))
            self.assertTrue(any("core.ghost" in x for x in res["missing"]))

    def test_screens_level0_no_hard_break(self):
        """level=0 绝对导入在 scan 全链路可解析（screens.py 形态回归）。"""
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            ui = d / "ui"
            core = d / "core"
            ui.mkdir()
            core.mkdir()
            _mk_file(ui, "screens.py",
                     "from app.core.models import Module\n")
            _mk_file(core, "models.py", "class Module: pass\n")
            res = scan([ui / "screens.py"], core)
            self.assertEqual(res["missing"], [])
            self.assertTrue(any("core.models:Module" in x for x in res["ok"]))

    def test_real_core_no_hard_breaks(self):
        """真实引用面（desktop ui + android 全引用层）对 v2.5 core 无硬断。

        38 W0 主断言：引用面经 collect_scan_paths 构建，覆盖 ui 顶层 + android
        controller/bootstrap/ui/screens——空面/半面不能令本断言变绿。
        """
        ui = ROOT / "desktop" / "src" / "ui"
        android = ROOT / "android" / "app"
        core = ROOT / "desktop" / "src" / "core"
        paths = collect_scan_paths(ui, android)
        self.assertGreaterEqual(len(paths), 13,
                                f"引用面过小（{len(paths)} 文件），"
                                "疑似覆盖回退")
        res = scan(paths, core)
        self.assertEqual(res["missing"], [])


class TestMain(unittest.TestCase):
    def test_empty_scan_fails_closed(self):
        """空扫描面 ≠ 干净面：main 必须返回非零而非静默通过。"""
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            core = d / "core"
            core.mkdir()
            with contextlib.redirect_stdout(io.StringIO()):
                code = main(["--ui-dir", str(d / "no_ui"),
                             "--android-dir", str(d / "no_android"),
                             "--core-dir", str(core)])
            self.assertEqual(code, 2)

    def test_real_surface_returns_zero(self):
        """真实缺省引用面 main 退出码 0（无硬断）。"""
        with contextlib.redirect_stdout(io.StringIO()):
            code = main([])
        self.assertEqual(code, 0)


if __name__ == "__main__":
    unittest.main()
