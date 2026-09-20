# -*- coding: utf-8 -*-
"""check30（版本字段 bump 迁移门禁）回归测试 —— 取 verify.sh 内嵌程序真件执行。

为什么取真件：判据的唯一实现住在 `verify.sh` check30 的 heredoc 里；同构复刻只能证明
「我写的副本对」。本测试搭**独立 git 仓储夹具**（temp 目录内 init + commit），再逐例注入
变更，用真实 `git diff HEAD` 走一遍判据。

覆盖：
- 正例：包内容版本 bump + 迁移记录写进 02 §9（JSON 类文件的合规通道）→ 放行
- 正例：四步记录内嵌被扫文件自身 diff（可写注释的文件）→ 放行
- 负例：bump 但无四步记录 → 阻断并点名缺项
- 负例：JSON 侧版本字段变更无记录 → 阻断
- 回归：非版本字段的数值变更（assets 计数）与注释里的数字 → **不再误判**（tok 收敛）
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VERIFY = ROOT / "verify.sh"
_ANCHOR = re.compile(r"<<'PYEOF'\s+>\"\$NFL_TMP\"/nf_check30\.log")

_EXTENSION = """# 扩展策略
字段级新增 additive editorial 结构 bump 派生三问
迁移记录：结构性变更必须 bump 并注明迁移说明。
"""

_MARKERS = ("现状快照", "bump 声明", "迁移说明", "校验回读")


def check30_program() -> str:
    """从 verify.sh 取出 check30 的内嵌 python 程序（判据唯一实现）。"""
    src = VERIFY.read_text(encoding="utf-8")
    m = _ANCHOR.search(src)
    if not m:
        raise AssertionError("verify.sh 里未找到 check30 内嵌程序锚点（判据实现已改形？）")
    begin = src.index("\n", m.end()) + 1
    end = src.index("\nPYEOF", begin)
    return src[begin:end]


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _proto(version: str) -> str:
    return ('protocol:\n  schema_version: "2"\n'
            'package:\n  id: 测试域包\n  name: 测试域包\n  pipeline: P09\n'
            '  version: "%s"\n  assets:\n    count: 1\n' % version)


@unittest.skipUnless(shutil.which("git"), "需要 git 才能驱动 git diff 判据")
class Check30BumpGateTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        _write(self.root / "02_联动注册表.md", "# 注册表\n\n### 9.3 迁移记录\n（初版）\n")
        _write(self.root / "protocol" / "EXTENSION.md", _EXTENSION)
        _write(self.root / "desktop" / "src" / "core" / "registry.json",
               '{\n  "registry_schema_version": 2,\n  "protocols": [\n'
               '    {\n      "id": "测试域包",\n      "version": "1.0.0"\n    }\n  ]\n}\n')
        _write(self.root / "community" / "测试域包" / "protocol.yaml", _proto("1.0.0"))
        self._git("init", "-q")
        self._git("add", "-A")
        self._git("-c", "user.name=t", "-c", "user.email=t@example.com",
                  "commit", "-q", "-m", "init")
        self.prog = self.root / "check30_prog.py"
        self.prog.write_text(check30_program(), encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def _git(self, *args) -> subprocess.CompletedProcess:
        return subprocess.run(["git", *args], cwd=str(self.root), capture_output=True,
                              text=True, encoding="utf-8", errors="replace")

    def _run(self) -> tuple:
        env = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
        cp = subprocess.run([sys.executable, str(self.prog)], cwd=str(self.root),
                            capture_output=True, text=True, encoding="utf-8",
                            errors="replace", env=env)
        return cp.returncode, (cp.stdout or "") + (cp.stderr or "")

    def _record_in_02(self, markers=_MARKERS) -> None:
        body = "".join("**%s**：示例。\n" % m for m in markers)
        _write(self.root / "02_联动注册表.md",
               "# 注册表\n\n### 9.4 迁移记录（包内容版本）\n" + body)

    def test_bump_with_record_in_02_passes(self):
        """正例：JSON 侧不可内嵌记录 → 记录写进 02 §9 同次提交 diff 即合规。"""
        _write(self.root / "community" / "测试域包" / "protocol.yaml", _proto("1.1.0"))
        _write(self.root / "desktop" / "src" / "core" / "registry.json",
               '{\n  "registry_schema_version": 2,\n  "protocols": [\n'
               '    {\n      "id": "测试域包",\n      "version": "1.1.0"\n    }\n  ]\n}\n')
        self._record_in_02()
        rc, out = self._run()
        self.assertEqual(rc, 0, out)
        self.assertIn("bump 文件 2", out)

    def test_bump_with_inline_record_passes(self):
        """正例：可写注释的文件把四步记录内嵌自身 diff。"""
        text = _proto("1.1.0") + "".join("# %s：示例\n" % m for m in _MARKERS)
        _write(self.root / "community" / "测试域包" / "protocol.yaml", text)
        rc, out = self._run()
        self.assertEqual(rc, 0, out)

    def test_bump_without_record_blocks(self):
        """负例：版本 bump 无四步记录 → 阻断并点名缺失标记。"""
        _write(self.root / "community" / "测试域包" / "protocol.yaml", _proto("1.1.0"))
        rc, out = self._run()
        self.assertEqual(rc, 1)
        self.assertIn("版本字段结构性变更（bump）但无四步迁移记录", out)
        for mark in _MARKERS:
            self.assertIn(mark, out)

    def test_json_version_change_without_record_blocks(self):
        """负例：registry.json 版本字段变更、无任何记录 → 阻断。"""
        _write(self.root / "desktop" / "src" / "core" / "registry.json",
               '{\n  "registry_schema_version": 2,\n  "protocols": [\n'
               '    {\n      "id": "测试域包",\n      "version": "1.1.0"\n    }\n  ]\n}\n')
        rc, out = self._run()
        self.assertEqual(rc, 1)
        self.assertIn("registry.json", out)

    def test_partial_record_blocks(self):
        """负例：四步只写了三步 → 仍阻断（点名缺项）。"""
        _write(self.root / "community" / "测试域包" / "protocol.yaml", _proto("1.1.0"))
        self._record_in_02(_MARKERS[:3])
        rc, out = self._run()
        self.assertEqual(rc, 1)
        self.assertIn("校验回读", out)

    def test_non_version_numeric_change_not_flagged(self):
        """回归（001 修正）：assets 计数变更 + 注释里的数字**不再**误判为版本 bump。"""
        _write(self.root / "community" / "测试域包" / "protocol.yaml",
               _proto("1.0.0").replace("count: 1", "count: 2") + "# 示例：阈值 = 3 层\n")
        rc, out = self._run()
        self.assertEqual(rc, 0, out)
        self.assertIn("bump 文件 0", out)


if __name__ == "__main__":
    unittest.main()
