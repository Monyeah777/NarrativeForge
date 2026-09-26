#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""抽象阶梯（protocol/LAYERS.json）单测 —— 语义判据 L1–L10 + 变异注入 + 生成投影。

纪律：每条规则至少一个违规样本必须被捕（check 的 check）；真仓库必须零 issue；
渲染必须确定性且 LF 落盘（Windows 上写文件不控行尾会落 CRLF，text_hygiene 判红——实测踩过）。
"""
import contextlib
import importlib.util
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "desktop" / "src"))

from core import layer_model as lm  # noqa: E402

_spec = importlib.util.spec_from_file_location("nfcli", ROOT / "scripts" / "nf.py")
nf = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(nf)


def _write(root, rel, text):
    path = os.path.join(root, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    return path


def _tier(tid, name, order, src, iface, deps, **extra):
    tier = {"id": tid, "name": name, "order": order, "status": "active",
            "change_tier": "additive",
            "source": {"globs": src}, "interface": {"globs": iface},
            "implementation": {"note": "-"},
            "depends_on": deps, "judged_by": ["check1"]}
    tier.update(extra)
    return tier


def _fixture(tmp, tiers=None, surfaces=None, derived=None, checks=None):
    """最小自洽阶梯树（改哪一项就变异哪一项，其余保持通过）。"""
    tiers = tiers or [
        _tier("contract", "契约", 0, ["a/*.md"], ["a/keep.md"], []),
        _tier("asset", "资产", 1, ["b/*"], ["b/protocol.yaml"], ["contract"]),
        _tier("engine", "引擎", 2, ["c/*.py"], ["c/nf.py"], ["contract", "asset"]),
        _tier("export", "出口", 3, ["d/*.json"], ["d/interop.json"], ["engine"]),
    ]
    doc = {
        "schema": "nf-layers/1",
        "vocabulary": {"change_tier": ["editorial", "additive", "bump"],
                       "status": ["active", "retired"]},
        "rules": [{"id": "L1", "statement": "样例"}],
        "tiers": tiers,
        "asset_levels": [{"id": "declaration", "name": "声明", "tier": "asset",
                          "globs": ["b/*.yaml"], "judged_by": ["check1"]}],
        "surfaces": surfaces or [{"id": "human", "name": "人机入口",
                                  "is_source_of_truth": False, "serves": ["engine"],
                                  "entries": ["c/nf.py"]}],
        "crosscut": {"name": "验证纵切", "applies_to": ["contract"],
                     "components": [{"id": "verify", "artifact": "verify.sh",
                                     "judged_by": ["check1"]}]},
        "derived": derived or [],
    }
    _write(tmp, "protocol/LAYERS.json", json.dumps(doc, ensure_ascii=False, indent=2))
    _write(tmp, "protocol/assertions.json",
           json.dumps({"schema": "nf-assertions/1", "assertions": []}, ensure_ascii=False))
    body = "".join("check%d(){\n  :\n}\n" % c for c in (checks or [1]))
    _write(tmp, "verify.sh", "#!/usr/bin/env bash\n" + body)
    for rel in ("a/keep.md", "a/more.md", "b/protocol.yaml", "c/nf.py", "d/interop.json"):
        _write(tmp, rel, "x\n")
    _write(tmp, "docs/layers.md",
           "# t\n\n" + lm.MARK_BEGIN + "\n" + lm.render_markdown(doc) + "\n"
           + lm.MARK_END + "\n")
    return doc


class LayerScanTest(unittest.TestCase):
    def test_fixture_is_clean(self):
        with tempfile.TemporaryDirectory() as tmp:
            _fixture(tmp)
            issues, stats = lm.scan(tmp)
            self.assertEqual(issues, [])
            self.assertEqual(stats["tiers"], 4)

    def test_real_repo_is_clean(self):
        issues, stats = lm.scan(str(ROOT))
        self.assertEqual(issues, [])
        self.assertEqual(stats["tiers"], 4)
        self.assertEqual(stats["asset_levels"], 5)
        self.assertEqual(stats["surfaces"], 4)
        self.assertEqual(stats["rules"], 10)

    def test_scan_is_deterministic(self):
        with tempfile.TemporaryDirectory() as tmp:
            _fixture(tmp)
            self.assertEqual(lm.scan(tmp), lm.scan(tmp))

    def test_mutation_l1_empty_source_face(self):
        with tempfile.TemporaryDirectory() as tmp:
            _fixture(tmp, tiers=[_tier("contract", "契约", 0, ["a/none/*.md"],
                                       ["a/keep.md"], [])])
            issues, _ = lm.scan(tmp)
            self.assertTrue(any(i.startswith("L1") for i in issues), issues)

    def test_mutation_l1_missing_entry_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            _fixture(tmp, surfaces=[{"id": "human", "name": "人机",
                                     "is_source_of_truth": False, "serves": ["engine"],
                                     "entries": ["c/ghost.py"]}])
            issues, _ = lm.scan(tmp)
            self.assertTrue(any("入口件不存在" in i for i in issues), issues)

    def test_mutation_l2_tier_overlap(self):
        with tempfile.TemporaryDirectory() as tmp:
            _fixture(tmp, tiers=[
                _tier("contract", "契约", 0, ["a/*.md"], ["a/keep.md"], []),
                _tier("asset", "资产", 1, ["a/*.md"], ["a/keep.md"], ["contract"]),
            ])
            issues, _ = lm.scan(tmp)
            self.assertTrue(any(i.startswith("L2") for i in issues), issues)

    def test_derived_is_exempt_from_overlap(self):
        with tempfile.TemporaryDirectory() as tmp:
            _fixture(tmp, tiers=[
                _tier("contract", "契约", 0, ["a/*.md"], ["a/keep.md"], []),
                _tier("asset", "资产", 1, ["a/shared.md", "b/*"],
                      ["b/protocol.yaml"], ["contract"]),
            ], derived=["a/shared.md"],
                surfaces=[{"id": "human", "name": "人机", "is_source_of_truth": False,
                           "serves": ["asset"], "entries": ["c/nf.py"]}])
            _write(tmp, "a/shared.md", "x\n")
            issues, _ = lm.scan(tmp)
            self.assertFalse(any(i.startswith("L2") for i in issues), issues)

    def test_mutation_l3_interface_outside_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            _fixture(tmp, tiers=[
                _tier("contract", "契约", 0, ["a/*.md"], ["a/keep.md", "d/interop.json"], []),
            ])
            issues, _ = lm.scan(tmp)
            self.assertTrue(any(i.startswith("L3") for i in issues), issues)

    def test_mutation_l4_dependency_upward(self):
        with tempfile.TemporaryDirectory() as tmp:
            _fixture(tmp, tiers=[
                _tier("contract", "契约", 0, ["a/*.md"], ["a/keep.md"], ["export"]),
                _tier("export", "出口", 3, ["d/*.json"], ["d/interop.json"], []),
            ])
            issues, _ = lm.scan(tmp)
            self.assertTrue(any(i.startswith("L4") for i in issues), issues)

    def test_mutation_l5_entry_claims_truth(self):
        with tempfile.TemporaryDirectory() as tmp:
            _fixture(tmp, surfaces=[{"id": "human", "name": "人机",
                                     "is_source_of_truth": True, "serves": ["engine"],
                                     "entries": ["c/nf.py"]}])
            issues, _ = lm.scan(tmp)
            self.assertTrue(any(i.startswith("L5") for i in issues), issues)

    def test_mutation_l6_core_imports_entry_face(self):
        with tempfile.TemporaryDirectory() as tmp:
            _fixture(tmp)
            _write(tmp, "desktop/src/core/evil.py", "import nf\n")
            issues, _ = lm.scan(tmp)
            self.assertTrue(any(i.startswith("L6") for i in issues), issues)

    def test_mutation_l7_retired_tier_depended_on(self):
        with tempfile.TemporaryDirectory() as tmp:
            _fixture(tmp, tiers=[
                _tier("contract", "契约", 0, ["a/*.md"], ["a/keep.md"], []),
                _tier("shell", "端壳", 1, ["b/*.md"], ["b/protocol.yaml"], [], status="retired"),
                _tier("engine", "引擎", 2, ["c/*.py"], ["c/nf.py"], ["shell"]),
            ])
            issues, _ = lm.scan(tmp)
            self.assertTrue(any(i.startswith("L7") for i in issues), issues)

    def test_mutation_l8_judged_by_unknown_check(self):
        with tempfile.TemporaryDirectory() as tmp:
            _fixture(tmp, tiers=[_tier("contract", "契约", 0, ["a/*.md"],
                                       ["a/keep.md"], [], judged_by=["check99"])])
            issues, _ = lm.scan(tmp)
            self.assertTrue(any(i.startswith("L8") for i in issues), issues)

    def test_mutation_l9_derived_hits_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            _fixture(tmp, derived=["z/*.json"])
            issues, _ = lm.scan(tmp)
            self.assertTrue(any(i.startswith("L9") for i in issues), issues)

    def test_mutation_l10_generated_region_drift(self):
        with tempfile.TemporaryDirectory() as tmp:
            _fixture(tmp)
            _write(tmp, "docs/layers.md", "# t\n\n%s\n手改过的内容\n%s\n"
                   % (lm.MARK_BEGIN, lm.MARK_END))
            issues, _ = lm.scan(tmp)
            self.assertTrue(any(i.startswith("L10") for i in issues), issues)

    def test_missing_declaration_reports_guidance(self):
        with tempfile.TemporaryDirectory() as tmp:
            issues, stats = lm.scan(tmp)
            self.assertTrue(any("缺阶梯真源" in i for i in issues), issues)
            self.assertEqual(stats["tiers"], 0)


class RenderTest(unittest.TestCase):
    def test_render_is_deterministic_and_covers_faces(self):
        doc = lm.load(str(ROOT))
        a, b = lm.render_markdown(doc), lm.render_markdown(doc)
        self.assertEqual(a, b)
        for name in ("契约", "资产", "引擎", "出口"):
            self.assertIn(name, a)
        self.assertIn("验证纵切", a)

    def test_write_region_is_idempotent_and_lf(self):
        with tempfile.TemporaryDirectory() as tmp:
            _fixture(tmp)
            path = os.path.join(tmp, "docs/layers.md")
            first = Path(path).read_bytes()
            lm.write_region(tmp)
            second = Path(path).read_bytes()
            self.assertEqual(first, second, "写回必须幂等")
            self.assertNotIn(b"\r\n", second, "生成区落盘必须是 LF")
            self.assertEqual(lm.scan(tmp)[0], [])


class CliTest(unittest.TestCase):
    @staticmethod
    def _run(argv):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = nf.main(list(argv))
        return code, out.getvalue()

    def test_layers_human_face(self):
        code, out = self._run(["layers"])
        self.assertEqual(code, 0)
        self.assertIn("抽象阶梯", out)
        self.assertIn("接口面", out)

    def test_layers_verify_and_json(self):
        code, out = self._run(["layers", "--verify"])
        self.assertEqual(code, 0, out)
        self.assertIn("通过", out)
        code, out = self._run(["layers", "--json"])
        self.assertEqual(code, 0)
        payload = json.loads(out)
        self.assertEqual(payload["kind"], "layers")
        self.assertEqual(len(payload["tiers"]), 4)
        self.assertEqual(payload["issues"], [])

    def test_command_face_self_consistent(self):
        tree = nf._collect_cli_tree()
        self.assertIn("layers", tree["commands"])
        for flag in ("--json", "--verify", "--write"):
            self.assertIn(flag, tree["tree"]["layers"]["flags"])


if __name__ == "__main__":
    unittest.main()
