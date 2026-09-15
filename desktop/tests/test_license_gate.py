# -*- coding: utf-8 -*-
"""图书馆入库许可证门单测（登记行合表 + 内联声明双源）。"""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from core import license_gate as lg  # noqa: E402

ROOT = str(Path(__file__).resolve().parents[2])

HEADER = ("| 编号 | 标题 | 形态/领域 | 投稿人 | 入库日期 | 许可 | 一句话 |\n"
          "|---|---|---|---|---|---|---|\n")


def _tree(tmp, rows, files=None):
    lib = Path(tmp, "library")
    lib.mkdir(parents=True, exist_ok=True)
    Path(lib, "INDEX.md").write_text(
        "# INDEX\n\n## 登记表\n\n" + HEADER +
        "".join("| %s | t | d | a | 2026-09-14 | %s | one |\n" % (i, lic)
                for i, lic in rows), encoding="utf-8")
    for name, text in (files or {}).items():
        Path(lib, name).write_text(text, encoding="utf-8")


class TestLicenseGate(unittest.TestCase):
    def test_real_repo_declared_rows_pass(self):
        """真实仓库：登记行许可齐备且在词表内（未声明只挂 WARN 不算 FAIL）。"""
        issues, stats = lg.scan(ROOT)
        self.assertEqual(issues, [])
        # 条目数从馆藏目录推导（原为硬编码 2，新增一件即误报）——
        # 该断言实为一个更强的不变量：登记表投影覆盖全部条目文件。
        n_entry_files = len(list((Path(ROOT) / "library").glob("NF-*.md")))
        self.assertEqual(stats["entries"], n_entry_files)
        self.assertIn("NF-WORLDCAMPUS-Monyeah777-1", stats["undeclared"])
        self.assertEqual(stats["unknown"], [])

    def test_missing_license_column_value_is_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            _tree(tmp, [("NF-1", "")])
            issues, _stats = lg.scan(tmp)
            self.assertTrue(any("缺「许可」列值" in i for i in issues), issues)

    def test_unknown_license_is_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            _tree(tmp, [("NF-1", "WTFPL")])
            issues, stats = lg.scan(tmp)
            self.assertTrue(any("不在词表" in i for i in issues), issues)
            self.assertEqual(stats["unknown"], ["NF-1"])

    def test_inline_mismatch_warns(self):
        with tempfile.TemporaryDirectory() as tmp:
            _tree(tmp, [("NF-1", "MIT")], {"NF-1.md": "> 许可：Apache-2.0\n正文\n"})
            issues, stats = lg.scan(tmp)
            self.assertEqual(issues, [])
            self.assertEqual(stats["mismatched"], ["NF-1"])
            self.assertTrue(any("双源不一致" in w for w in stats["warnings"]))

    def test_inline_match_no_inline_warning(self):
        with tempfile.TemporaryDirectory() as tmp:
            _tree(tmp, [("NF-1", "MIT")], {"NF-1.md": "# 件\n> 许可：MIT\n正文\n"})
            _issues, stats = lg.scan(tmp)
            self.assertEqual(stats["no_inline"], [])
            self.assertEqual(stats["mismatched"], [])


if __name__ == "__main__":
    unittest.main()
