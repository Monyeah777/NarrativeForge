#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""极端渗透（八向）暴露问题的回归测试 —— 2026-09-28 波。

覆盖：
  F-1 图书馆编码容错（非 UTF-8 不得让整面崩）
  F-2 消费纪律（信任边界）在机器入口可见
  F-3 同一包内重复 mc.id 有判据（此前 first-wins 静默择一）
  F-4 machine_contract.scan 可证范围 = 官方核心（社区命名空间不同，不再误报）
  F-5 payload_registry.scan 缺根返回 issue（不再抛裸 FileNotFoundError）
  F-6 nf run --pipeline 收编号 + 未知编号给可操作指引
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "desktop" / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "desktop" / "src"))

from core import conformance_scan as csc      # noqa: E402
from core import library as nflib             # noqa: E402
from core import machine_contract as mc       # noqa: E402
from core import payload_registry as pr       # noqa: E402


def _w(root: Path, rel: str, text: str) -> Path:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    return p


class LibraryEncodingTest(unittest.TestCase):
    """F-1：一个非 UTF-8 文件不得让图书馆面瘫痪。"""

    def test_non_utf8_entry_is_reported_not_crashing(self):
        with tempfile.TemporaryDirectory() as tmp:
            lib = Path(tmp) / "library"
            lib.mkdir()
            (lib / "NF-1.md").write_text(
                "---\nid: NF-1\ntype: t\ntitle: t\nrating: general\n---\n\n正文\n", encoding="utf-8")
            (lib / "NF-BIN.md").write_bytes(b"\xff\xfe\x00binary\x80\n")

            rows = nflib.entries(tmp)                       # 不得抛 UnicodeDecodeError
            self.assertEqual({"NF-1", "NF-BIN"}, {e["id"] for e in rows})
            bad = [e for e in rows if e["id"] == "NF-BIN"][0]
            self.assertTrue(bad["decode_issue"], "非 UTF-8 条目须带 decode_issue")

            issues = nflib.verify(tmp)[0]
            self.assertTrue(any("编码" in i and "NF-BIN" in i for i in issues),
                            "verify 须把编码问题判 FAIL 并给指引：%s" % issues)
            # 投影面不得因坏文件而崩（write_projection 只在 INDEX 已存在时重写，故这里
            # 直接验渲染：坏条目不进表，其余条目照常出表）
            block = nflib.render_index_block(tmp)
            self.assertIn("NF-1", block)
            self.assertFalse(bad["decode_issue"] in block, "坏条目不得把诊断串写进登记表")


class TrustBoundaryTest(unittest.TestCase):
    """F-2：消费纪律（数据 ≠ 指令）必须在机器入口可见。"""

    KEYS = ("不是可执行指令", "数据")

    def test_index_generated_block_states_discipline(self):
        block = nflib.render_index_block(str(ROOT))
        self.assertIn("消费纪律", block)
        self.assertIn("不是可执行指令", block)

    def test_llms_entry_states_discipline(self):
        text = (ROOT / "llms.txt").read_text(encoding="utf-8")
        self.assertIn("消费纪律", text)
        self.assertIn("外来内容", text)
        for fake in ("[系统]", "[天枢]"):
            self.assertIn(fake, text, "应显式点名伪造前缀：%s" % fake)

    def test_committed_index_matches_renderer(self):
        idx = (ROOT / "library" / "INDEX.md").read_text(encoding="utf-8")
        self.assertIn("消费纪律", idx)
        self.assertEqual([], nflib.check_projection(str(ROOT)),
                         "改了渲染器就须同步 INDEX（跑 nf library reindex）")


class DuplicateModuleIdTest(unittest.TestCase):
    """F-3：同包内两个文件声明同一 mc.id 必须被 conformance 判出。"""

    def test_duplicate_mc_id_is_flagged(self):
        with tempfile.TemporaryDirectory() as tmp:
            body = ("# 模块\n\n```yaml\nmachine_contract:\n  id: \"探针:DUP1\"\n"
                    "  inputs: []\n  outputs: []\n```\n")
            _w(Path(tmp), "community/zz_dup/modules/A_a.md", body)
            _w(Path(tmp), "community/zz_dup/modules/B_b.md", body)
            issues, _ = csc.scan(tmp)
            self.assertTrue(any("重复" in i and "DUP1" in i for i in issues),
                            "重复 mc.id 须被捕获：%s" % issues)

    def test_real_repo_has_no_duplicate_mc_id(self):
        issues, _ = csc.scan(str(ROOT))
        self.assertEqual([], [i for i in issues if "重复" in i], "真仓不得有重复 mc.id")


class MachineContractScopeTest(unittest.TestCase):
    """F-4：可证范围 = 官方核心；社区包的类内段命名空间不再误报。"""

    def test_real_repo_scan_is_clean(self):
        issues, _warns, stats = mc.scan(str(ROOT))
        self.assertEqual([], issues)
        self.assertGreater(stats.get("checked", 0), 0, "须实际检查了核心模块")
        self.assertEqual(stats.get("checked"), 13, "官方核心 13 件")

    def test_core_mismatch_is_still_flagged(self):
        with tempfile.TemporaryDirectory() as tmp:
            _w(Path(tmp), "04_模块库/通用类/M98_测试件.md",
               "# M98_测试件\n\n```yaml\nmachine_contract:\n  id: \"WRONG:M99\"\n```\n")
            issues, _warns, _s = mc.scan(tmp)
            self.assertTrue(issues, "核心面 id 与文件名不符仍须 FAIL")

    def test_community_namespace_is_not_flagged(self):
        with tempfile.TemporaryDirectory() as tmp:
            _w(Path(tmp), "community/zz_pack/modules/D14a_口径登记.md",
               "# D14a_口径登记\n\n```yaml\nmachine_contract:\n  id: \"某域包:M01\"\n```\n")
            issues, _warns, _s = mc.scan(tmp)
            self.assertEqual([], issues, "社区包走类内段命名空间，不应按文件名比对：%s" % issues)


class PayloadRegistryRobustnessTest(unittest.TestCase):
    """F-5：缺根返回 issue，不抛裸 FileNotFoundError。"""

    def test_missing_root_returns_issue(self):
        with tempfile.TemporaryDirectory() as tmp:
            issues, _stats = pr.scan(tmp)
            self.assertTrue(issues)
            self.assertIn("修复指引", " ".join(issues))


class RunPipelineArgTest(unittest.TestCase):
    """F-6：--pipeline 收编号；未知编号给可操作指引（列出可用管线）。"""

    def _run(self, *args):
        return subprocess.run([sys.executable, str(ROOT / "scripts" / "nf.py"), *args],
                              cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
                              errors="replace", timeout=600)

    def test_pipeline_id_is_resolved(self):
        p = self._run("run", "--pipeline", "P01", "--modules", "M00",
                      "--store", os.path.join(tempfile.gettempdir(), "nf_t_p01"),
                      "--dest", os.path.join(tempfile.gettempdir(), "nf_t_p01_out"))
        self.assertNotIn("管线解析失败", (p.stdout or "") + (p.stderr or ""),
                         "合法编号 P01 不得被判解析失败")

    def test_unknown_pipeline_lists_available(self):
        p = self._run("run", "--pipeline", "P999", "--modules", "M00")
        out = (p.stdout or "") + (p.stderr or "")
        self.assertIn("修复指引", out)
        self.assertIn("P01", out, "指引须列出可用管线编号")


if __name__ == "__main__":
    unittest.main()
