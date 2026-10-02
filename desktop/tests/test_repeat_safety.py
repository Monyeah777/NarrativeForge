# -*- coding: utf-8 -*-
"""重复写命令的二次调用安全（agent 密集调用会重发同一写命令）。

本件把三条**已验证**的行为钉住（2026-09-30 复核）：
1. 模块状态流转**幂等**：同一目标态重复设置 → 文本逐字不变；
2. 资产重键**拒收**（fail-closed）：重复 `asset add` 同键 → 报错 + 修复指引，**不产生重复台账行**；
3. 库条目生命周期**幂等**：重复 deprecate 不改变文件内容。

（CLI 层另有一条口径修正：`nf module deprecate` 若已在目标态，输出「已是 X（无变化）」，
不再谎报「X → X」。）
"""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from core import asset_ledger as al  # noqa: E402
from core import library as lib  # noqa: E402
from core import module_lifecycle as ml  # noqa: E402

MOD = """# 模块 M98 · 重复安全测试件
> 类别：通用｜来源：测试｜挂载点：P40 行为决策（active）｜依赖：M00

## 1. 职责
测试用。
"""


class RepeatSafetyTest(unittest.TestCase):
    def test_module_status_transition_is_idempotent(self):
        once = ml.set_status(MOD, "deprecated", reason="测试", module_file="x.md")
        twice = ml.set_status(once, "deprecated", reason="测试", module_file="x.md")
        self.assertEqual(once, twice, "重复流转到同一目标态必须逐字不变")
        self.assertEqual("deprecated", ml.get_status(twice)[0])

    def test_asset_duplicate_key_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "assets").mkdir()
            (root / "assets" / "K1.md").write_text("# K1\n", encoding="utf-8")
            al.add_asset(str(root), "assets/K1.md", "K1", "来源")
            with self.assertRaises(al.AssetLedgerError):
                al.add_asset(str(root), "assets/K1.md", "K1", "来源")
            doc = al.load_ledger(al.default_ledger_path(str(root)))
            rows = doc.get("assets") or doc.get("entries") or []
            self.assertEqual(1, len(rows), "重键不得产生重复台账行")

    def test_library_lifecycle_is_idempotent(self):
        good = ("---\nid: NF-99\ntype: 世界（测试件）\ntitle: T\ndescription: d\n"
                "author: tester\nlicense: MIT\ngenerated: 2026-09-14\nstatus: active\n"
                "sources:\n  - Issue #1\n---\n\n正文\n")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "library").mkdir()
            entry = root / "library" / "NF-99.md"
            entry.write_text(good, encoding="utf-8", newline="\n")
            lib.write_projection(str(root))
            lib.set_status(str(root), "NF-99", "deprecated")
            first = entry.read_text(encoding="utf-8")
            lib.set_status(str(root), "NF-99", "deprecated")
            self.assertEqual(first, entry.read_text(encoding="utf-8"),
                             "重复 deprecate 不得改变文件内容")


if __name__ == "__main__":
    unittest.main()
