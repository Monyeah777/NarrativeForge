#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""缺口逐行审查（gap_review）单测：候选筛法可复现 + 确定性证据复核 + stub 双轨纪律。

补齐既有覆盖缺口（逐模块覆盖率门禁实测 `gap_review.py` 0.0%——AUD-0015 落地时无随行单测；
本波把它顶上 ≥30%）。判据只用**离线 stub**（真模型不进单测，避免不确定性进 CI）。
"""
import sys
import subprocess
import tempfile
import unittest
from pathlib import Path

if str(Path(__file__).resolve().parent.parent / "src") not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from core import gap_review as gr  # noqa: E402

ROOT = str(Path(__file__).resolve().parents[2])


class CandidateTest(unittest.TestCase):
    def test_candidates_are_deterministic_and_capped(self):
        a = gr.candidates(ROOT)
        b = gr.candidates(ROOT)
        self.assertEqual(a, b, "候选筛法必须确定性可复现（同输入同输出）")
        self.assertTrue(a, "真仓库应有候选（缺证据/静默吞错/缺质量规则三类）")
        for row in a[:5]:
            self.assertIn("class", row)
            self.assertIn("file", row)
            self.assertIn("line", row)

    def test_class_filter_narrows_scope(self):
        allrows = gr.candidates(ROOT)
        classes = sorted({r["class"] for r in allrows})
        self.assertGreaterEqual(len(classes), 1)
        only = gr.candidates(ROOT, classes=(classes[0],))
        self.assertTrue(all(r["class"] == classes[0] for r in only))
        self.assertLessEqual(len(only), len(allrows))


class EvidenceTest(unittest.TestCase):
    def test_evidence_available_for_some_rows_and_always_a_string(self):
        """真仓候选行：证据面是**字符串**，且「无证据」只许出现在设计内的挂账类。

        2026-10-01 改写：原断言要求「真仓至少有一条行带确定性证据」——那是**拿真仓当非空转
        样本**，而这批缺口修完后真仓已无可修行（2026-10-01 `nf review`：可修 0），断言反而成了
        「必须有缺口」的错误门槛。改为按**设计口径**断言（有证据 ⇔ 不属于 `payload-no-evidence`
        这一内容挂账类），判别力另由合成样本自证（下一个用例）。
        """
        rows = gr.candidates(ROOT)
        self.assertTrue(rows)
        for r in rows:
            text = gr.evidence(ROOT, r)
            self.assertIsInstance(text, str)
            if r["class"] == "payload-no-evidence":
                self.assertEqual("", text.strip(), "内容挂账类不许被当成可修缺口")
            else:
                self.assertTrue(text.strip(),
                                "非挂账类候选应能给出确定性证据（否则复核面失真）：%r" % r)

    def test_evidence_predicate_has_catch_power(self):
        """变异自证（替代原「真仓必须还有缺口」的非空转断言）：合成一条**真缺口**，证据必出。"""
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp, "04_模块库", "通用类")
            d.mkdir(parents=True)
            (d / "M99_合成.md").write_text(
                "# M99 合成\n\n## 事件契约\n\n```yaml\npayload: {foo_id, foo_tags[]}\n```\n",
                encoding="utf-8", newline="\n")
            rows = [r for r in gr.candidates(tmp)
                    if r["class"] == "unharvestable-payload"]
            self.assertTrue(rows, "合成缺口没被判出（候选筛法失真）")
            self.assertTrue(all(gr.evidence(tmp, r).strip() for r in rows),
                            "合成缺口应给出确定性证据")

    def test_rows_without_evidence_are_the_suspected_class(self):
        """无证据行不得进修复清单——按类归到 suspected（双轨纪律的机检面）。"""
        doc = gr.review(ROOT, adapter="stub", limit=0)
        for row in doc.get("fixable", []):
            self.assertTrue(str(row.get("evidence", "")).strip(),
                            "fixable 行必须带确定性证据：%r" % row)


class ReviewTest(unittest.TestCase):
    def test_stub_review_shape_and_double_track(self):
        doc = gr.review(ROOT, adapter="stub", limit=6, batch=3)
        self.assertEqual(doc.get("schema"), "nf-gap-review/1")
        self.assertIn("fixable", doc)
        self.assertIn("suspected", doc)
        self.assertIn("by_class", doc)
        self.assertLessEqual(doc["scanned"], 6)
        self.assertFalse(doc["model_meta"]["calibrated"],
                         "stub 未校准（calibrated=false）——不得当质量背书")


class ScopeTest(unittest.TestCase):
    """`--scope` 必须**真的在筛**、拼错必须 fail-closed、`--help` 的枚举面必须与实现对账。

    依据（2026-10-01）：`nf review --scope X` 此前只算了一个**没人用**的局部变量——报告永远
    是全类（按类筛也拿到全量，属「文档写了却做不到」）；而 `--help` 又列了一个**永不产出**的
    类别、漏了真仓占绝大多数的 `payload-no-evidence`。两个方向都错，故三件事一起钉。
    """

    def _run(self, *argv):
        return subprocess.run([sys.executable, str(Path(ROOT) / "scripts" / "nf.py"), "review"]
                              + list(argv), cwd=str(ROOT), capture_output=True, text=True,
                              encoding="utf-8", errors="replace", timeout=300)

    def test_scope_filters_the_review(self):
        everything = gr.review(ROOT)
        only = gr.review(ROOT, classes=("payload-no-evidence",))
        self.assertLessEqual(only["scanned"], everything["scanned"])
        self.assertEqual({"payload-no-evidence"}, set(only["by_class"]))
        self.assertEqual(len(gr.candidates(ROOT, classes=("payload-no-evidence",))),
                         only["scanned"], "限定类别后的行数须等于该类候选数（筛没生效即红）")

    def test_unknown_scope_is_refused_with_guidance(self):
        p = self._run("--scope", "bogus")
        self.assertEqual(2, p.returncode, "拼错的 --scope 必须 fail-closed，不许静默成空表")
        for c in gr.CLASSES:
            self.assertIn(c, p.stderr, "拒绝时必须列出可枚举类别：%s" % c)

    def test_help_enumerates_every_class(self):
        """对账：`--help` 列的类别必须**恰好**是 `gap_review.CLASSES`（漏一个即红）。"""
        p = self._run("--help")
        text = p.stdout + p.stderr
        for c in gr.CLASSES:
            self.assertIn(c, text, "--help 漏了实际会产出的类别：%s" % c)

    def test_unknown_classes_predicate_has_catch_power(self):
        self.assertEqual([], gr.unknown_classes(gr.CLASSES), "真类别不许被误判成未知")
        self.assertEqual(["bogus"],
                         gr.unknown_classes(["payload-no-evidence", "bogus"]))


class ReviewLimitTest(unittest.TestCase):
    def test_limit_zero_means_all_rows(self):
        all_rows = gr.review(ROOT, adapter="stub", limit=0)
        few = gr.review(ROOT, adapter="stub", limit=2)
        self.assertGreaterEqual(all_rows["scanned"], few["scanned"])
        self.assertEqual(few["scanned"], 2)
        self.assertTrue(gr.summary(all_rows))

    def test_limit_two_caps_rows(self):
        all_rows = gr.review(ROOT, adapter="stub", limit=0)
        few = gr.review(ROOT, adapter="stub", limit=2)
        self.assertGreaterEqual(all_rows["scanned"], few["scanned"])
        self.assertEqual(few["scanned"], 2)


if __name__ == "__main__":
    unittest.main()
