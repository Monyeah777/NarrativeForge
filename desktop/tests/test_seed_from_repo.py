# -*- coding: utf-8 -*-
"""路径可达门禁：`desktop/scripts/seed_from_repo.py` 必须**自定位到本仓根**。

依据（2026-10-01 取证）：该入口此前只试 `/tmp/NinFenz` 等三个**固定历史路径**，
在本仓真实工作目录（Windows / 任意克隆点）一律找不到 → SystemExit，命令等于不可达。
现改为「本脚本位置自定位优先」，本件把它钉住：不传参也必须解析到含 `03_管线库` 的仓根，
且该仓根就是本测试所在仓库（不是某个历史盘路径）。
"""
import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "desktop" / "scripts" / "seed_from_repo.py"


def _load():
    spec = importlib.util.spec_from_file_location("nf_seed_from_repo_probe", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


class SeedFromRepoReachabilityTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = _load()

    def test_self_locates_to_this_repo_root(self):
        got = self.mod.find_repo_root()
        self.assertTrue((got / "03_管线库").is_dir(), "自定位的仓根缺 03_管线库：%s" % got)
        self.assertEqual(ROOT, got.resolve(), "未自定位到本仓根（回了历史路径？）")

    def test_script_lives_under_desktop_scripts(self):
        """入口路径口径：文档与自述都写 `desktop/scripts/seed_from_repo.py`（不是 `scripts/`）。"""
        self.assertTrue(SCRIPT.is_file(), "种子导入器不在 desktop/scripts/ 下：%s" % SCRIPT)


if __name__ == "__main__":
    unittest.main()
