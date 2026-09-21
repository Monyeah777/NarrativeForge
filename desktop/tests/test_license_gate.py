# -*- coding: utf-8 -*-
"""图书馆入库许可证门单测（登记行合表 + 内联声明双源）。"""
import sys
import tempfile
import os
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


class LicenseExpressionTest(unittest.TestCase):
    """SPDX 表达式词法（本波净吸收）：单一 id 是特例，组合式也要能判。"""

    def test_accepted_expressions(self):
        for expr in ("MIT", "Apache-2.0", "MIT OR Apache-2.0",
                     "(MIT OR Apache-2.0) AND CC0-1.0", "LicenseRef-Custom-1",
                     "专有", "未声明"):
            self.assertEqual(lg.expression_issue(expr), "", expr)

    def test_rejected_expressions(self):
        cases = {
            "Apache 2.0": "不在词表",           # 空格被剥掉 → 词法过，id 过不了
            "MIT AND": "首/尾",
            "AND MIT": "首/尾",
            "MIT OR OR Apache-2.0": "缺少操作数",
            "MIT AND (CC0-1.0": "括号不配平",
            "GPL-3.0": "不在词表",
            "": "许可为空",
        }
        for expr, why in cases.items():
            self.assertIn(why, lg.expression_issue(expr), expr)

    def test_scan_uses_expression_judgement(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.makedirs(os.path.join(tmp, "library"))
            with open(os.path.join(tmp, "library", "INDEX.md"), "w", encoding="utf-8") as fh:
                fh.write("| 编号 | 标题 | 形态/领域 | 投稿人 | 入库日期 | 许可 | 状态 | 一句话 |\n"
                         "|---|---|---|---|---|---|---|---|\n"
                         "| NF-1 | 样例 | 世界 | 作者 | 2026-01-01 | MIT OR Apache-2.0 "
                         "| active | 正例：组合式许可应被接受 |\n")
            issues, stats = lg.scan(tmp)
            self.assertEqual(issues, [], issues)
            self.assertEqual(stats["declared"], 1)


if __name__ == "__main__":
    unittest.main()
