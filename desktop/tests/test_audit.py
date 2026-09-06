# -*- coding: utf-8 -*-
"""M_AUDIT 协议设计审计模块单测（v2.6：nf design audit——决策过程质量）。

运行：cd desktop && python -m unittest tests.test_audit -v
覆盖（§十 test_audit.py 条目）：schema 完整性 / verdict 三态校验 / 3-7
清单边界（<3 与 >7 均拒绝）/ 模板存在性 / check 对缺文件返回提示不抛错 /
steelman mode 复用 core.steelman / 单源回归（对抗验证）：2/3/4 节占位别名
core.steelman 常量 + 列表判据共用（无正则副本/死导入）+ 小数正文行不计条目。
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from typing import List

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from core.audit import (  # noqa: E402
    AUDIT_MODES,
    VERDICTS,
    init_audit,
    check_audit,
    scan_audit,
    validate_list_count,
)
import core.audit as audit_mod  # noqa: E402
from core import steelman as sm  # noqa: E402


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


class TestAuditSteelmanCheckReuse(unittest.TestCase):
    """回归（RED→GREEN）：steelman/full mode 的钢人节内容判据复用
    core.steelman check 语义——占位骨架不得假绿（返回空列表），论据节按
    ≥3 真实条目校验，核心变量节非空校验。"""

    def test_steelman_skeleton_check_not_false_green(self):
        """空骨架 steelman → check 应报论据不足/核心变量未填（不得 []）。"""
        txt = init_audit("问题", target="t", mode="steelman")
        warns = check_audit_text(txt)
        self.assertTrue(
            any("论据不足" in w or "核心变量未填" in w for w in warns),
            "steelman 占位骨架 check 假绿（应报缺项）：%s" % warns)

    def test_steelman_filled_passes(self):
        """steelman 论据/核心变量填实（编号与项目符号形态混合）→ 无缺项。"""
        txt = init_audit("问题", target="t", mode="steelman")
        txt = txt.replace("- （论据一：独立成立、不可轻易驳倒）",
                          "1. 支持论据一：完整强论证")
        txt = txt.replace("- （论据二）", "2. 支持论据二")
        txt = txt.replace("- （论据三）", "3. 支持论据三")
        txt = txt.replace("- （论据一：独立成立、不可软化）",
                          "一、反对论据一：完整强论证")
        txt = txt.replace("- （论据二）\n- （论据三）\n> 反对侧论据不得软化为'只是有点担心'。",
                          "二、反对论据二\n三、反对论据三\n> 反对侧论据不得软化为'只是有点担心'。")
        txt = txt.replace("<改变结论的那个变量>", "G1 是否已修复")
        warns = check_audit_text(txt)
        self.assertEqual(warns, [], "steelman 填实被误报：%s" % warns)

    def test_real_parenthesized_argument_not_stripped(self):
        """整行括号包裹的真实论据 ≠ init 占位——不得被占位剔除误伤。"""
        txt = init_audit("问题", target="t", mode="steelman")
        txt = txt.replace("- （论据一：独立成立、不可轻易驳倒）",
                          "- （真实论据：括号内完整陈述的论证，非占位模板）")
        txt = txt.replace("- （论据二）", "- 支持论据二")
        txt = txt.replace("- （论据三）", "- 支持论据三")
        txt = txt.replace("- （论据一：独立成立、不可软化）",
                          "- 反对论据一")
        txt = txt.replace("- （论据二）", "- 反对论据二")
        txt = txt.replace("- （论据三）", "- 反对论据三")
        txt = txt.replace("<改变结论的那个变量>", "变量 X")
        warns = check_audit_text(txt)
        self.assertEqual(warns, [], "真实（…）论据被误剔：%s" % warns)


class TestAuditListMorphology(unittest.TestCase):
    """回归（RED→GREEN）：列表条目形态判据与 core.steelman 对齐——
    编号（1. / 一、 /（1））真实清单不得误报 0 条越界；空 bullet 行不计。"""

    def test_numbered_blindspot_items_not_miscounted(self):
        txt = init_audit("问题", target="t", mode="blindspot")
        txt = txt.replace("- （低置信度一：附影响面）", "1. 不确定 schema（影响面：返工）")
        txt = txt.replace("- （低置信度二）", "2. 不确定边界（影响面：误报）")
        txt = txt.replace("- （低置信度三）", "3. 不确定 CLI（影响面：接线）")
        txt = txt.replace("- （遗漏一：没问出口的假设/没考虑到的场景）",
                          "（1）没考虑 Windows（后果：乱码）")
        txt = txt.replace("- （遗漏二）", "（2）没考虑空目录（后果：ls 空）")
        txt = txt.replace("- （遗漏三）", "（3）没考虑并发（后果：覆盖）")
        warns = check_audit_text(txt)
        self.assertEqual(warns, [], "编号形态清单被误报越界：%s" % warns)

    def test_empty_bullet_lines_not_counted(self):
        """3 条真实 + 5 行空 bullet = 3 条有效（空行不得计入致越界误报）。"""
        txt = init_audit("问题", target="t", mode="blindspot")
        txt = txt.replace("- （低置信度一：附影响面）", "- 真实一")
        txt = txt.replace("- （低置信度二）", "- 真实二")
        txt = txt.replace("- （低置信度三）", "- 真实三")
        # 遗漏节：3 条真实 + 混入 5 行空 bullet（"- " 后缀仅空白）
        txt = txt.replace(
            "- （遗漏一：没问出口的假设/没考虑到的场景）",
            "- 遗漏一\n- 遗漏二\n- 遗漏三\n- \n- \n- \n- \n- ")
        txt = txt.replace("- （遗漏二）", "")
        txt = txt.replace("- （遗漏三）", "")
        warns = check_audit_text(txt)
        self.assertEqual(warns, [], "空 bullet 行被计入条目：%s" % warns)


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


def _replace_section_body(text: str, sec_title: str, new_lines) -> str:
    """把文档中「## sec_title」到下一节标题间的正文替换为 new_lines。"""
    marker = f"## {sec_title}"
    lines = text.splitlines()
    i = next(k for k, ln in enumerate(lines) if ln.strip() == marker)
    j = next((k for k in range(i + 1, len(lines))
              if lines[k].strip().startswith("## ")), len(lines))
    return "\n".join(lines[:i + 1] + list(new_lines) + lines[j:])


def _audit_section_bullets(txt: str, sec_title: str) -> List[str]:
    """从 audit 骨架抽取某节的项目符号占位行（剔除 > 引导脚注等非条目行）。"""
    body = audit_mod._sec_text(txt, sec_title)
    return [ln for ln in body.splitlines() if ln.strip().startswith("- ")]


class TestAuditSingleSourceSteelman(unittest.TestCase):
    """回归（对抗验证 RED→GREEN）：audit 钢人判据真正单一来源——2/3 节占位
    文本别名 core.steelman.ARG_PLACEHOLDERS（删除自持逐字副本），4 节占位
    别名 core.steelman.SECTION_PLACEHOLDERS；_LIST_ITEM_RE 与条目计数直接
    复用 core.steelman（不自持正则副本、清除死导入 STEELMAN_SECTIONS）。
    跨模块假绿反例锁死：audit init 的 2/3 节占位原文在 core.steelman.check
    中必须仍被识别为占位，不得被计为真实论据。"""

    def test_section23_placeholder_alias_steelman_single_source(self):
        """audit 2/3/4 节占位文本与 core.steelman 逐字同源（非复制副本）。"""
        self.assertEqual(audit_mod._SECTION_PLACEHOLDERS[2],
                         list(sm.ARG_PLACEHOLDERS[2]))
        self.assertEqual(audit_mod._SECTION_PLACEHOLDERS[3],
                         list(sm.ARG_PLACEHOLDERS[3]))
        self.assertEqual(audit_mod._SECTION_PLACEHOLDERS[4],
                         [sm.SECTION_PLACEHOLDERS[4]])

    def test_list_item_regex_and_counting_reused_from_steelman(self):
        """audit 不自持 _LIST_ITEM_RE 正则副本（源码无本地 re.compile 定义），
        条目计数直接复用 core.steelman.count_list_entries——判据双源漂移
        不可能发生。"""
        self.assertIs(audit_mod.count_list_entries, sm.count_list_entries)
        src = Path(audit_mod.__file__).read_text(encoding="utf-8")
        self.assertNotIn("_LIST_ITEM_RE = re.compile", src)

    def test_audit_init_placeholders_not_false_green_in_steelman(self):
        """跨模块假绿锁死（对抗验证方向）：audit init 2/3 节占位原文置入钢人
        工作单 → core.steelman.check 必须仍识别为占位（报论据不足），不得
        计为真实论据。修复前 audit 占位文本与 ARG_PLACEHOLDERS 逐字不同 →
        steelman 计为真实论据（假绿）；修复后同源 → 正确报缺。"""
        atxt = init_audit("跨模块问题", target="t", mode="steelman")
        ws = sm.init_worksheet("跨模块问题", context="t")
        for num, sec in ((2, "2. 支持侧最强论据"), (3, "3. 反对侧最强论据")):
            bullets = _audit_section_bullets(atxt, sec)
            self.assertTrue(bullets, f"audit 骨架 {sec} 抽不出占位行")
            ws = _replace_section_body(ws, sec, bullets)
        warns = sm.check_worksheet(ws)
        self.assertTrue(
            any("论据" in w and "不足" in w or "<3" in w for w in warns),
            "audit init 占位置入钢人工作单被计为真实论据（假绿）：%s" % warns)

    def test_decimal_paragraph_not_counted_as_argument(self):
        """对抗验证第三项（RED→GREEN）：正文段如 '1.5 倍成本风险…' 行首
        数字+点不得被 _LIST_ITEM_RE 误计为列表条目——修复前行首代理把小数
        判成编号条目，2 条真实 + 1 条小数行 = 3 假绿通过；修复后小数行不计，
        论据不足应被报出。"""
        txt = init_audit("问题", target="t", mode="steelman")
        txt = txt.replace("- （论据一：独立成立、不可轻易驳倒）",
                          "1.5 倍成本风险会放大预算")
        txt = txt.replace("- （论据二）", "2. 支持论据二")
        txt = txt.replace("- （论据三）", "3. 支持论据三")
        txt = txt.replace("- （论据一：独立成立、不可软化）", "- 反对论据一")
        txt = txt.replace("- （论据二）", "- 反对论据二")
        txt = txt.replace("- （论据三）", "- 反对论据三")
        txt = txt.replace("<改变结论的那个变量>", "变量 X")
        warns = check_audit_text(txt)
        self.assertTrue(
            any("支持侧论据不足" in w for w in warns),
            "小数正文行被计为支持侧论据（假绿）：%s" % warns)


#: 库层 check 需从文本构造临时文件——测试辅助
def check_audit_text(text: str) -> list:
    d = Path(tempfile.mkdtemp(prefix="nf_audit_txt_"))
    p = d / "audit.md"
    p.write_text(text, encoding="utf-8")
    return check_audit(p)


if __name__ == "__main__":
    unittest.main()
