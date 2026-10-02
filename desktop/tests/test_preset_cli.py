# -*- coding: utf-8 -*-
"""`nf preset` 面回归：退役端壳的预设语义接成 CLI 后，**真跑一遍全链**。

依据（2026-10-01）：`core/preset_manager.py` 此前只有自己的单测引用（`test_dead_code` 的
`TEST_ONLY_ALLOWED` 如实登记为缺口，并写明补齐方向「端壳能力一律落 CLI」）。本命令落地后，
本件把 `save → ls → show → apply → export → import（改名）→ rm` 走通——
落点 = **隔离 NF_HOME**（`NARRATIVE_FORGE_HOME` 指临时目录），不碰真实用户预设库、不写仓库。
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
NF = str(ROOT / "scripts" / "nf.py")


class PresetCliTest(unittest.TestCase):
    def setUp(self):
        self.home = tempfile.mkdtemp(prefix="nf_preset_test_")
        self.env = dict(os.environ, NARRATIVE_FORGE_HOME=self.home)

    def _run(self, *argv, want_rc=0):
        p = subprocess.run([sys.executable, NF, *argv], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", cwd=str(ROOT),
                           env=self.env, timeout=300)
        self.assertEqual(want_rc, p.returncode, p.stdout + p.stderr)
        return p.stdout + p.stderr

    def test_full_roundtrip(self):
        self._run("preset", "save", "西幻演示", "--pipeline", "P04",
                  "--modules", "通用类:M00,轻混类:M91", "--assets", "校园情感领域包")
        # 同名再存须被拒（防误覆盖），加 --force 才放过
        out = self._run("preset", "save", "西幻演示", want_rc=1)
        self.assertIn("同名预设已存在", out)
        self._run("preset", "save", "西幻演示", "--pipeline", "P04",
                  "--modules", "通用类:M00,轻混类:M91", "--assets", "校园情感领域包",
                  "--force")
        doc = json.loads(self._run("preset", "ls", "--json"))
        self.assertEqual("preset-ls", doc["kind"])
        self.assertEqual(["西幻演示"], [r["name"] for r in doc["rows"]])
        one = json.loads(self._run("preset", "show", "西幻演示", "--json"))
        self.assertEqual("preset-show", one["kind"])
        self.assertEqual("P04", one["preset"]["pipeline"])
        app = json.loads(self._run("preset", "apply", "西幻演示", "--json"))
        self.assertEqual("preset-apply", app["kind"])
        self.assertEqual("校园情感领域包", app["asset_pack"])
        # 空 store（本机未装模块）⇒ 如实进 warnings，不假装装配成功
        self.assertEqual(2, len(app["warnings"]))

    def test_export_import_and_rm(self):
        self._run("preset", "save", "迁移用", "--pipeline", "P01", "--modules", "通用类:M00")
        out_file = os.path.join(self.home, "exported.json")
        self._run("preset", "export", "迁移用", "--out", out_file)
        self.assertTrue(os.path.isfile(out_file))
        self._run("preset", "rm", "迁移用")
        self.assertEqual([], json.loads(self._run("preset", "ls", "--json"))["rows"])
        self._run("preset", "import", out_file)
        self.assertEqual(["迁移用"],
                         [r["name"] for r in json.loads(self._run("preset", "ls", "--json"))["rows"]])
        self._run("preset", "import", out_file, "--name", "改名后的")
        names = {r["name"] for r in json.loads(self._run("preset", "ls", "--json"))["rows"]}
        self.assertEqual({"迁移用", "改名后的"}, names)

    def test_missing_preset_and_bad_import_give_guidance(self):
        out = self._run("preset", "show", "不存在", want_rc=1)
        self.assertIn("预设未找到", out)
        self.assertIn("nf preset ls", out)
        bad = os.path.join(self.home, "bad.json")
        Path(bad).write_text('{"nope": 1}', encoding="utf-8")
        out = self._run("preset", "import", bad, want_rc=1)
        self.assertIn("预设不可用", out)
        # 机读面：失败也必须是可解析 JSON（与全仓 `_machine_fail` 口径一致）
        p = subprocess.run([sys.executable, NF, "preset", "show", "不存在", "--json"],
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace", cwd=str(ROOT), env=self.env, timeout=300)
        self.assertEqual(1, p.returncode)
        self.assertFalse(json.loads(p.stdout)["ok"])


if __name__ == "__main__":
    unittest.main()
