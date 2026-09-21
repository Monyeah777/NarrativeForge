# -*- coding: utf-8 -*-
"""双语入口（README.md / README.en.md）机读事实一致性测试。

背景（外部实证）：某清单开了中英双语面却无一致性判据，中文面腐烂到英文面的 ~54%。
本仓的防线 = verify check34 的「双语入口机读锚点」断言；本测试把同一判据在单测面钉住，
期望值取自 `quality_baseline`（不写字面量，随基线自适应）。
"""
import contextlib
import importlib.util
import io
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "desktop" / "src"))

from core import quality_baseline as qb  # noqa: E402

ANCHORS = ("check1-%d" % qb.EXPECTED_CHECKS, "PASS=%d" % qb.EXPECTED_PASS,
           "01_核心协议.md", "06_Agent执行协议.md", "llms.txt", "community/")
ENTRIES = ("README.md", "README.en.md")
_MD_REF = re.compile(r"[A-Za-z0-9_\-\./]+\.md")


class BilingualEntryTest(unittest.TestCase):
    def _read(self, rel: str) -> str:
        return (ROOT / rel).read_text(encoding="utf-8")

    def test_both_entries_exist(self):
        for rel in ENTRIES:
            self.assertTrue((ROOT / rel).is_file(), rel)

    def test_shared_machine_anchors(self):
        for rel in ENTRIES:
            text = self._read(rel)
            for anchor in ANCHORS:
                self.assertIn(anchor, text, "%s 缺机读锚点 %s" % (rel, anchor))

    def test_both_entries_carry_version(self):
        for rel in ENTRIES:
            self.assertRegex(self._read(rel), r"v\d+\.\d+", rel)

    def test_machine_index_points_to_english_entry(self):
        self.assertIn("README.en.md", self._read("llms.txt"))

    def test_section_structure_is_aligned(self):
        """结构对齐：两份入口的 H2 章节数一致（英文面逐节镜像中文面）。"""
        counts = [len(re.findall(r"(?m)^## ", self._read(rel))) for rel in ENTRIES]
        self.assertEqual(counts[0], counts[1],
                         "双语入口章节数不一致：%s" % dict(zip(ENTRIES, counts)))
        self.assertEqual(counts[0], 5)

    def test_english_entry_covers_chinese_doc_references(self):
        """文档入口覆盖：中文入口引用的 ASCII 名 .md 件须在英文入口同样出现。"""
        zh_refs = sorted(set(_MD_REF.findall(self._read("README.md"))))
        en = self._read("README.en.md")
        missing = [r for r in zh_refs if r not in en]
        self.assertEqual(missing, [], "英文入口缺件：%s" % missing)


class ExternalLinkToolTest(unittest.TestCase):
    """外链巡检工具（**非门禁**）：解析判据 + 注入 fetcher 的正负例（离线可跑）。"""

    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location(
            "nf_ext_links", ROOT / "scripts" / "check_external_links.py")
        cls.tool = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.tool)

    def test_extract_dedup_and_strip_punctuation(self):
        text = "见 https://a.example/x，还有 https://a.example/x 与 https://b.example/y）。"
        self.assertEqual(self.tool.extract_links(text),
                         ["https://a.example/x", "https://b.example/y"])

    def test_skips_anchors_and_mail(self):
        text = "[锚](#section) [邮件](mailto:a@b.c) 正文 https://c.example/z"
        self.assertEqual(self.tool.extract_links(text), ["https://c.example/z"])

    def test_skips_template_placeholder_urls(self):
        """骨架示例 URL（含 `{…}` 占位符）必须跳过——否则巡检把模板当死链。"""
        text = "取件：https://x.example/tree/main/{路径}` 与真实 https://x.example/real"
        self.assertEqual(self.tool.extract_links(text), ["https://x.example/real"])

    def test_strips_trailing_backtick_and_quote(self):
        """markdown 行内代码/引号里的 URL 会带尾随反引号或引号，须剥掉。"""
        text = "见 `https://a.example/x` 与 \"https://b.example/y\""
        self.assertEqual(self.tool.extract_links(text),
                         ["https://a.example/x", "https://b.example/y"])

    def test_check_reports_ok_and_fail_with_injected_fetcher(self):
        links = {"README.md": ["https://ok.example/1", "https://dead.example/2"],
                 "docs/x.md": ["https://ok.example/1"]}
        fake = lambda url: (not url.startswith("https://dead"), "fake")   # noqa: E731
        report = self.tool.check(links, fake)
        self.assertEqual(report["total"], 3)
        self.assertEqual(report["checked"], 2)      # 同链接只探一次
        self.assertEqual(report["failed"], 1)

    def test_transient_classification_and_retry_after(self):
        """瞬态口径：超时/5xx/429/408/425 可重试；4xx（非上述）一律定性。"""
        for d in ("HTTP 500", "HTTP 429", "HTTP 408", "超时", "TimeoutError",
                  "URLError", "ConnectionResetError"):
            self.assertTrue(self.tool.is_transient(d), d)
        for d in ("HTTP 404", "HTTP 403", "HTTP 200", "HTTP 410"):
            self.assertFalse(self.tool.is_transient(d), d)
        self.assertEqual(self.tool.retry_after_seconds("HTTP 429（Retry-After: 3）"), 3.0)
        self.assertEqual(self.tool.retry_after_seconds("HTTP 429（Retry-After: 999）"), 10.0)
        self.assertEqual(self.tool.retry_after_seconds("HTTP 404"), 0.0)

    def test_probe_with_retry_recovers_and_respects_attempt_budget(self):
        """退避重试：瞬态失败重试后成功即 ok；非瞬态不重试；次数用尽如实报失败。"""
        calls = {"n": 0}
        waits = []

        def seq(url):
            calls["n"] += 1
            return (calls["n"] >= 3, "HTTP 503" if calls["n"] < 3 else "HTTP 200")

        ok, detail = self.tool.probe_with_retry("https://x.example", seq, retries=2,
                                                backoff=1.0, sleep=waits.append)
        self.assertTrue(ok, detail)
        self.assertEqual(calls["n"], 3)
        self.assertEqual(waits, [1.0, 2.0], "退避应逐次翻倍")

        calls2 = {"n": 0}

        def dead(url):
            calls2["n"] += 1
            return False, "HTTP 404"

        ok2, detail2 = self.tool.probe_with_retry("https://y.example", dead, retries=3,
                                                  backoff=1.0, sleep=lambda _s: None)
        self.assertFalse(ok2)
        self.assertEqual(calls2["n"], 1, "非瞬态失败不得重试")
        self.assertEqual(detail2, "HTTP 404")

    def test_retry_wrapped_fetch_keeps_report_shape(self):
        """接线面：probe_with_retry 包装后的 fetcher 仍产出同形报告（失败项逐条可寻址）。"""
        self._retry_wrapped_case()

    def test_domain_breaker_skips_after_repeated_failure(self):
        """域级熔断（本机网络实测驱动）：连续失败达阈值后同域链接不再探测，且跳过可见。"""
        breaker = self.tool.DomainBreaker(threshold=2)
        calls = {"n": 0}

        def dead(url):
            calls["n"] += 1
            return (self.tool.host_of(url) == "ok.example", "TimeoutError")

        links = {"README.md": ["https://bad.example/1", "https://bad.example/2",
                               "https://bad.example/3", "https://ok.example/9"]}
        report = self.tool.check_with_breaker(links, dead, breaker=breaker)
        self.assertEqual(calls["n"], 3, "第三次同域链接应被熔断跳过（bad×2 + ok×1）")
        self.assertEqual(report["failed"], 2)
        self.assertEqual(report["skipped"], 1)
        self.assertEqual(report["tripped_hosts"], {"bad.example": 2})
        skipped = [r for r in report["rows"] if r["status"] == "skipped"]
        self.assertIn("域级熔断", skipped[0]["detail"])
        self.assertEqual(self.tool.host_of("https://a.b.example:8443/x?y=1"), "a.b.example")

    def test_breaker_resets_after_success(self):
        breaker = self.tool.DomainBreaker(threshold=2)
        breaker.record("https://x.example/1", False)
        breaker.record("https://x.example/2", True)
        breaker.record("https://x.example/3", False)
        self.assertFalse(breaker.is_open("https://x.example/4"), "成功须清零连续失败计数")

    def test_time_budget_marks_skipped(self):
        links = {"README.md": ["https://a.example/1", "https://b.example/2"]}
        report = self.tool.check_with_breaker(
            links, lambda url: (True, "ok"), deadline=lambda: -1.0)
        self.assertEqual(report["checked"], 0)
        self.assertEqual(report["skipped"], 2)
        self.assertIn("时间预算", report["rows"][0]["detail"])

    def _retry_wrapped_case(self):
        calls = {"n": 0}

        def flaky(url):
            calls["n"] += 1
            if calls["n"] == 1:
                return False, "HTTP 503"
            return (True, "HTTP 200")

        wrapped = lambda url: self.tool.probe_with_retry(  # noqa: E731
            url, flaky, retries=1, backoff=0.0, sleep=lambda _s: None)
        links = {"README.md": ["https://ok.example/1", "https://dead.example/2"]}
        report = self.tool.check(links, wrapped)
        self.assertEqual(report["checked"], 2)
        self.assertEqual([r["status"] for r in report["rows"]], ["ok", "ok"])

    def test_limit_skips_beyond_sample(self):
        links = {"README.md": ["https://a.example/1", "https://a.example/2"]}
        report = self.tool.check(links, lambda url: (True, "fake"), limit=1)
        self.assertEqual(report["checked"], 1)
        self.assertIn("skipped", [r["status"] for r in report["rows"]])

    def test_scan_mode_does_not_fetch(self):
        """默认（不 --fetch）必须只解析、不联网：main 返回 0。"""
        with contextlib.redirect_stdout(io.StringIO()):
            code = self.tool.main(["--root", str(ROOT)])
        self.assertEqual(code, 0)

    def test_write_into_protocol_layer_is_rejected(self):
        """报告不得写入协议层（保静态可复现）。"""
        with contextlib.redirect_stderr(io.StringIO()):
            code = self.tool.main(["--root", str(ROOT),
                                   "--write", "protocol/x.json"])
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
