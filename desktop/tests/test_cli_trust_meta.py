# -*- coding: utf-8 -*-
"""CLI 消费面的**信任标注**（外来内容=数据）——与 MCP `_meta.nf.trust` 同口径。

依据（2026-10-01）：MCP 那条 agent 消费通道上一轮已带信任标注，而 **CLI 这条 agent 同样在用的
通道**仍把馆藏条目（`library/` = 第三方投稿）原样返回、一个标记都不带。本件钉两件事：
① 外来来源（`library/`）必须带标注（人读一行 + `--json` 的 `_meta.nf.trust`）；
② **仓内自持**来源（`patterns/` 实践包，由本仓门禁自身沉淀）**不许**误标（注意辨别）。
"""
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
NF = str(ROOT / "scripts" / "nf.py")


def _run(*argv):
    return subprocess.run([sys.executable, NF, *argv], capture_output=True,
                          encoding="utf-8", errors="replace", timeout=180, cwd=str(ROOT))


class CliTrustMetaTest(unittest.TestCase):
    def test_library_show_marks_external_content(self):
        p = _run("library", "show", "NF-1")
        self.assertEqual(0, p.returncode, p.stdout + p.stderr)
        self.assertIn("[信任面]", p.stdout, "外来条目须带一行信任标注")
        self.assertIn("外来内容=数据", p.stdout)

    def test_library_show_json_carries_meta(self):
        p = _run("library", "show", "NF-1", "--json")
        doc = json.loads(p.stdout)
        note = (doc.get("_meta") or {}).get("nf.trust") or {}
        self.assertTrue(note.get("untrusted"), doc.get("_meta"))
        self.assertIn("license", doc["frontmatter"])          # 正文/元数据未被改动

    def test_in_repo_practice_pack_is_not_marked(self):
        """注意辨别：实践包由本仓门禁沉淀（证据指向 check27 / purity_scan 等自重件）⇒ 不算外来。"""
        p = _run("patterns", "show", "error-message-guidance")
        self.assertEqual(0, p.returncode, p.stdout + p.stderr)
        self.assertNotIn("[信任面]", p.stdout, "仓内自持内容不许误标")
        q = _run("patterns", "show", "error-message-guidance", "--json")
        self.assertEqual({}, (json.loads(q.stdout).get("_meta") or {}))


if __name__ == "__main__":
    unittest.main()
