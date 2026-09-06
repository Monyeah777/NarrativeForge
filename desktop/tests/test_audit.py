# -*- coding: utf-8 -*-
"""M_AUDIT 协议设计审计模块单测（v2.6：nf design audit——决策过程质量）。

运行：cd desktop && python -m unittest tests.test_audit -v
覆盖（§十 test_audit.py 条目）：schema 完整性 / verdict 三态校验 / 3-7
清单边界（<3 与 >7 均拒绝）/ 模板存在性 / check 对缺文件返回提示不抛错 /
steelman mode 复用 core.steelman。
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from core.audit import (  # noqa: E402
    AUDIT_MODES,
    VERDICTS,
    init_audit,
    check_audit,
    scan_audit,
    validate_list_count,
)


def _mk_audit_dir():
    return Path(tempfile.mkdtemp(prefix="nf_audit_"))


class TestAuditSchema(unittest.TestCase):
    def test_modes_and_verdicts(self):
        self.assertEqual(set(AUDIT_MODES), {"steelman", "blindspot", "full"})
        self.assertEqual(set(VERDICTS),
                         {"通过", "需补充以下信息", "需重做"})

    def test_init_full_has_all_sections(self):
        txt = init_audit("是否启动 38 方案？", target="38 方案",
                         mode="full", context="v2.6")
        for marker in ("mode: full", "target: 38 方案", "verdict:",
                       "## 1. 问题重述", "## 2. 支持侧最强论据",
                       "## 3. 反对侧最强论据", "## 4. 核心变量",
                       "## 5. 低置信度清单", "## 6. 遗漏清单",
                       "## 7. 评估结论", "## 8. 行动建议与缺陷条目"):
            self.assertIn(marker, txt)

    def test_init_steelman_mode_has_steelman_semantics(self):
        """steelman mode（升格合并裁决）：含钢人核心变量节 + 结论节，
        不含 blindspot 段；frontmatter mode 标记正确。"""
        txt = init_audit("测试问题", target="t", mode="steelman")
        self.assertIn("## 4. 核心变量", txt)
        self.assertIn("## 7. 评估结论", txt)
        self.assertNotIn("低置信度", txt)
        self.assertNotIn("遗漏", txt)
        self.assertIn("mode: steelman", txt)

    def test_init_writes_file_when_path_given(self):
        d = _mk_audit_dir()
        out = d / "audit.md"
        init_audit("问题", target="t", mode="blindspot", path=out)
        self.assertTrue(out.exists())
        content = out.read_text(encoding="utf-8")
        self.assertIn("mode: blindspot", content)


class TestAuditCheck(unittest.TestCase):
    def test_check_missing_file_returns_hint_no_raise(self):
        """check 对缺文件返回提示（非红、不抛错）。"""
        d = _mk_audit_dir()
        result = check_audit(d / "不存在.md")
        self.assertIsInstance(result, list)
        self.assertTrue(any("未审计" in r or "不存在" in r for r in result))

    def test_check_empty_blindspot_lists_warn(self):
        """空骨架 blindspot 清单 0 条 → 越界 warn（契约：<3 = 敷衍）。"""
        txt = init_audit("问题", target="t", mode="blindspot")
        warns = check_audit_text(txt)
        self.assertTrue(any("越界" in w for w in warns))

    def test_check_filled_blindspot_passes(self):
        """blindspot 清单填满 3-7 条 → 无越界 warn。"""
        txt = init_audit("问题", target="t", mode="blindspot")
        txt = txt.replace("- （低置信度一：附影响面）", "- 不确定 schema 是否够用（影响：返工）")
        txt = txt.replace("- （低置信度二）", "- 不确定 3-7 边界是否合理（影响：误报）")
        txt = txt.replace("- （低置信度三）", "- 不确定 CLI 形状（影响：接线）")
        txt = txt.replace("- （遗漏一：没问出口的假设/没考虑到的场景）", "- 没考虑 Windows 路径（影响：乱码）")
        txt = txt.replace("- （遗漏二）", "- 没考虑空目录（影响：ls 空）")
        txt = txt.replace("- （遗漏三）", "- 没考虑并发会话（影响：覆盖）")
        warns = check_audit_text(txt)
        self.assertEqual(warns, [])

    def test_check_invalid_verdict_warns(self):
        txt = init_audit("问题", target="t", mode="blindspot")
        txt = txt.replace("verdict: <三态之一：通过 / 需补充以下信息 / 需重做>",
                          "verdict: 随便写")
        warns = check_audit_text(txt)
        self.assertTrue(any("verdict" in w for w in warns))


class TestListBoundary(unittest.TestCase):
    def test_count_2_rejected(self):
        self.assertFalse(validate_list_count(2))

    def test_count_7_accepted(self):
        self.assertTrue(validate_list_count(7))

    def test_count_8_rejected(self):
        self.assertFalse(validate_list_count(8))

    def test_count_3_accepted(self):
        self.assertTrue(validate_list_count(3))


class TestAuditScan(unittest.TestCase):
    def test_scan_finds_audit_md(self):
        d = _mk_audit_dir()
        (d / "a.md").write_text(init_audit("审计问题", target="决策甲",
                                           mode="full"), encoding="utf-8")
        (d / "b.txt").write_text("不是审计", encoding="utf-8")
        hits = scan_audit(d)
        self.assertEqual(len(hits), 1)
        self.assertIn("决策甲", hits[0])

    def test_scan_empty_dir(self):
        d = _mk_audit_dir()
        self.assertEqual(scan_audit(d), [])


#: 库层 check 需从文本构造临时文件——测试辅助
def check_audit_text(text: str) -> list:
    d = Path(tempfile.mkdtemp(prefix="nf_audit_txt_"))
    p = d / "audit.md"
    p.write_text(text, encoding="utf-8")
    return check_audit(p)


if __name__ == "__main__":
    unittest.main()
