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


def _reference_entry_imports(text):
    """**未缓存的参考实现**：原先 `_rule_issues` 里那段「预筛 + `ast.parse` + `ast.walk`」原样搬来。"""
    import ast
    out = []
    if not lm._ENTRY_IMPORT_RE.search(text):
        return out
    try:
        tree = ast.parse(text)
    except (OSError, SyntaxError):
        return out
    for node in ast.walk(tree):
        names = []
        if isinstance(node, ast.Import):
            names = [a.name.split(".")[0] for a in node.names]
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            names = [node.module.split(".")[0]]
        for name in names:
            if name in lm.ENTRY_MODULE_NAMES:
                out.append((node.lineno, name))
    return out


class EntryImportFactTest(unittest.TestCase):
    """L6 的**逐件事实缓存**（`_entry_imports`）：与未缓存参考实现等价，且顺序/重复项不丢。

    依据（实测 2026-09-29）：L6 每次扫描都要读 255 份 core/*.py 并做预筛 + AST walk，而「这一件
    是否 import nf/scripts」只是该件正文的纯函数——改与引擎无关的件时这一整笔应当为零。
    """

    def test_real_repo_core_files_match_reference(self):
        files = sorted((ROOT / "desktop" / "src" / "core").glob("*.py"))
        self.assertGreater(len(files), 100, "core 件太少，判据没测到东西")
        for p in files:
            text = p.read_text(encoding="utf-8")
            self.assertEqual(_reference_entry_imports(text), lm._entry_imports(text),
                             "%s 的事实与参考实现不一致" % p.name)

    def test_order_and_duplicates_survive(self):
        text = ("import os\n"
                "import nf\n"
                "import nf.cli\n"
                "from scripts import x\n"
                "from . import nf\n")          # 相对 import（level≠0）不算
        got = lm._entry_imports(text)
        self.assertEqual([(2, "nf"), (3, "nf"), (4, "scripts")], got)
        self.assertEqual(got, lm._entry_imports(text), "同内容第二次必须逐位相同")

    def test_cache_is_content_keyed(self):
        """键是**正文**不是路径：同正文复用得同一结果，改一个字节就得重算。"""
        lm._ENTRY_IMPORT_CACHE.clear()
        self.assertEqual([(1, "nf")], lm._entry_imports("import nf\n"))
        self.assertEqual([(1, "nf")], lm._entry_imports("import nf\n"))
        self.assertEqual([], lm._entry_imports("import nfz\n"))
        self.assertEqual([], lm._entry_imports("import os\n"))


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

    def test_expand_fast_path_matches_reference(self):
        """快路径（子树一次走 + 正则匹配）必须与参考实现 `_expand` 逐 pattern 等价。

        v13 的收益来自「不再为每个 pattern 各走一遍文件系统」，代价是 glob→正则的语义
        必须守住——本断言即等价性的可执行证据（含字符类回退、固定件直判、缺失子树）。
        """
        doc = lm.load(str(ROOT))
        pats = set()

        def collect(node):
            if isinstance(node, dict):
                for key, val in node.items():
                    if key in ("globs", "derived", "exempt_paths") and isinstance(val, list):
                        pats.update(str(x) for x in val)
                    else:
                        collect(val)
            elif isinstance(node, list):
                for item in node:
                    collect(item)

        collect(doc)
        # 真源里没有、但快路径必须同样处理的形态：字符类 / 单字符 / 跨目录 ** / 固定件 / 空子树
        pats |= {"desktop/src/core/[a-z]*.py", "protocol/?.json", "desktop/**/*.py",
                 "STRATEGY.md", "scripts/nf", "no/such/dir/*.md"}
        for pattern in sorted(pats):
            self.assertEqual(lm._expand(str(ROOT), [pattern]),
                             lm._expand_many(str(ROOT), [pattern], {}), pattern)

    def test_tier_faces_match_reference(self):
        """每阶真源面（含派生物扣除）也必须与参考实现逐阶一致。"""
        doc = lm.load(str(ROOT))
        derived = lm._expand(str(ROOT), doc.get("derived") or [])
        faces = lm.tier_faces(str(ROOT), doc)
        for tier in doc.get("tiers") or []:
            tid = str(tier.get("id"))
            ref = lm._expand(str(ROOT), (tier.get("source") or {}).get("globs")) - derived
            self.assertEqual(faces[tid], ref, tid)

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
