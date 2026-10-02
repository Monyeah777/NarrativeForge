# -*- coding: utf-8 -*-
"""语法级静态检查**本地化**：CI 跑的那条 ruff 规则（E9/F63/F7/F82），本机也要跑。

为什么（2026-10-01 取证）：`ruff.toml` 的 select 是 `E9 / F63 / F7 / **F82**`——F82 就是
**未定义名**，属「跑起来必崩」的硬错，但 `verify.sh` 按纪律**不碰 ruff**（纯 unittest/stdlib，
零第三方红线），于是本地门禁与 CI 的 `lint.yml` 之间留了缝：本轮全量扫到
`scripts/serve_decision_model.py` 用了 `sys` 却没 `import sys`（**脚本一跑就 NameError**，
`--help` 也过不去）——本机全绿、云端会红。本件把 CI 那条规则搬进单测：ruff 在场就跑，
不在场**明示跳过**（软依赖纪律，与 `nf release check` 同口径），不引硬依赖。
"""
import importlib.util
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _ruff_available() -> bool:
    return bool(shutil.which("ruff")) or importlib.util.find_spec("ruff") is not None


class RuffSyntaxTest(unittest.TestCase):
    def test_repo_passes_ruff_syntax_rules(self):
        if not _ruff_available():
            self.skipTest("本机无 ruff（CI 的 lint.yml 会跑；修复指引：pip install ruff）")
        p = subprocess.run([sys.executable, "-m", "ruff", "check",
                            "desktop/src", "scripts"],
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace", cwd=str(ROOT), timeout=300)
        out = (p.stdout or "") + (p.stderr or "")
        if p.returncode == 1 and "No module named" in out:
            self.fail("`python -m ruff` 不可用但 PATH 上另有 ruff（修复指引：统一用同一个）")
        self.assertEqual(0, p.returncode,
                         "ruff 语法级检查未过（E9/F63/F7/F82，逐条修：\n%s" % out)

    def test_config_keeps_the_syntax_rule_set(self):
        """配置不得被悄悄放宽（把 F82 去掉 = 本判据变空转）。"""
        cfg = (ROOT / "ruff.toml").read_text(encoding="utf-8")
        self.assertIn("select", cfg)
        for rule in ("E9", "F63", "F7", "F82"):
            self.assertIn(rule, cfg, "ruff 规则集缺 %s" % rule)

    def test_rule_set_really_catches_undefined_names(self):
        """**变异自证**：未定义名必须被判红（否则这条判据只是装饰）。"""
        if not _ruff_available():
            self.skipTest("本机无 ruff（修复指引：pip install ruff）")
        import tempfile
        fd, probe = tempfile.mkstemp(suffix=".py", prefix="nf_ruff_probe_")
        with __import__("os").fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write("def f():\n    return totally_undefined_name\n")
        try:
            p = subprocess.run([sys.executable, "-m", "ruff", "check",
                                "--config", str(ROOT / "ruff.toml"), probe],
                               capture_output=True, text=True, encoding="utf-8",
                               errors="replace", cwd=str(ROOT), timeout=120)
            self.assertNotEqual(0, p.returncode,
                                "未定义名没被判红（规则集失效）：%s%s" % (p.stdout, p.stderr))
        finally:
            __import__("os").unlink(probe)


class RuffDeadCodeTest(unittest.TestCase):
    """**死代码面**（F401 未用导入 / F841 未用局部）在仓库面上必须为零。

    依据（2026-10-02，作者指令「清除逻辑垃圾（注意辨别）」）：`ruff.toml` 的 select **有意保守**
    （只收 E9/F63/F7/F82 语法级，风格规则另议）——所以死代码从来没有任何判据守过。本轮按
    `--select F401,F841` 全量扫，**18 处**（4 × `scripts/nf.py` 里早已不用的
    `from core.storage import Store`、`scripts/nf_client.py` 的 `as exc`、以及 13 处测试件里的
    死导入/死局部）。逐条辨别后全部删除（都是重构/改写后的遗留，无一处承担副作用）。

    口径：**不改 CI 的 ruff 配置**（保守口径是作者的，不归本判据动），本件作为**仓库卫生判据**
    只收 F401/F841 这两条**死代码**规则；要保留的"看似未用"导入走**官方逃生口** `# noqa: F401`
    （ruff 自己认，不必另建豁免表），并且**变异自证**（合成一件带死导入的件必须被判红）。
    """

    FACES = ("desktop/src", "scripts", "desktop/tests", ".github/scripts")

    @staticmethod
    def _run(targets, select="F401,F841"):
        return subprocess.run([sys.executable, "-m", "ruff", "check",
                               "--no-cache", "--select", select] + list(targets),
                              capture_output=True, text=True, encoding="utf-8",
                              errors="replace", cwd=str(ROOT), timeout=300)

    def test_no_dead_imports_or_locals(self):
        if not _ruff_available():
            self.skipTest("本机无 ruff（修复指引：pip install ruff）")
        p = self._run(self.FACES)
        out = (p.stdout or "") + (p.stderr or "")
        if p.returncode == 1 and "No module named" in out:
            self.fail("`python -m ruff` 不可用但 PATH 上另有 ruff（修复指引：统一用同一个）")
        self.assertEqual(0, p.returncode,
                         "存在死代码（F401 未用导入 / F841 未用局部）——修复指引：删掉它，"
                         "确实需要保留的加 `# noqa: F401` 并写明理由：\n%s" % out)

    def test_predicate_has_catch_power(self):
        """变异自证：合成的死导入必须被判红（否则这条判据只是装饰）。"""
        if not _ruff_available():
            self.skipTest("本机无 ruff（修复指引：pip install ruff）")
        import tempfile
        fd, probe = tempfile.mkstemp(suffix=".py", prefix="nf_dead_probe_")
        with __import__("os").fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write("import json\n\n\ndef f():\n    unused = 1\n    return 2\n")
        try:
            p = self._run([probe])
            self.assertNotEqual(0, p.returncode,
                                "合成死代码没被判红（判据将永远是绿的）：%s%s"
                                % (p.stdout, p.stderr))
        finally:
            __import__("os").unlink(probe)


if __name__ == "__main__":
    unittest.main()
