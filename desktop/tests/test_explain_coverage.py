# -*- coding: utf-8 -*-
"""`nf explain <check>` 的**全覆盖**判据（门禁红了要能拿到指引）。

动机（2026-09-30 完整性检查）：`CHECK_GUIDE` 只写到 32，而 verify.sh 已扩到 39 条
——check33–39 红的时候，`nf explain 33` 一律回「未知 check：33」，**修复指引缺位**。
本件把「explain 覆盖面 == verify.sh 的 check 面」立成可核事实（新增 check 必须同步补条目）。
"""
import contextlib
import importlib.util
import io
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("nfcli_explain", ROOT / "scripts" / "nf.py")
nf = importlib.util.module_from_spec(spec)
spec.loader.exec_module(nf)


def _checks_in_verify() -> list:
    return sorted(int(m) for m in re.findall(r"^check(\d+)\(\)\{",
                                             (ROOT / "verify.sh").read_text(encoding="utf-8"),
                                             re.M))


def _explain(n: int):
    out = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
        code = nf.main(["explain", str(n)])
    return code, out.getvalue()


class ExplainCoverageTest(unittest.TestCase):
    def test_every_check_has_guidance(self):
        checks = _checks_in_verify()
        self.assertGreater(len(checks), 30, "check 面解析失败")
        missing = []
        for n in checks:
            code, text = _explain(n)
            if code != 0 or "缺什么" not in text or "补什么" not in text:
                missing.append((n, code, text.strip()[:60]))
        self.assertEqual([], missing, "这些 check 没有修复指引（nf explain）")

    def test_guide_table_has_no_extra_numbers(self):
        """反向：指引表不许留已不存在的 check 号（防「删 check 后指引留尸」）。"""
        checks = set(_checks_in_verify())
        extra = sorted(int(k) for k in nf.CHECK_GUIDE if k.isdigit() and int(k) not in checks)
        self.assertEqual([], extra)

    def test_fail_path_points_to_explain(self):
        """接线：门禁报红时必须把用户指到 `nf explain`（否则指引面做了没人到得了）。"""
        text = (ROOT / "verify.sh").read_text(encoding="utf-8")
        i = text.find('if [ "$FAIL" -gt 0 ]')
        self.assertGreater(i, 0, "verify.sh 收尾块缺失？")
        self.assertIn("nf.py explain", text[i:i + 400],
                      "FAIL 分支未指向修复指引面")


if __name__ == "__main__":
    unittest.main()
