# -*- coding: utf-8 -*-
"""引擎 provider 注册表（core/engine_registry.py）回归测试 —— 注册表模式 / 装载解析面。"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "desktop" / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "desktop" / "src"))

from core import engine_registry as er  # noqa: E402

FACE = {
    "schema": "nf-integration/1", "id": "rust-fastlane", "title": "Rust 只读快线",
    "kind": "cli", "status": "active", "version": "1.0.0", "codeowner": "@x",
    "tier": "core", "entry": {"command": "cargo run", "path": "engine/rust/Cargo.toml"},
    "requires": ["cargo>=1.75"], "docs": ["engine/rust/README.md"],
    "evidence": ["engine/rust/Cargo.toml"],
}


def _mk(root, rel, text):
    p = Path(root, rel)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    return p


class RealRepoTest(unittest.TestCase):
    def test_engines_are_rust_and_dotnet(self):
        ids = {p["id"] for p in er.engines(str(ROOT))}
        self.assertIn("rust-fastlane", ids)
        self.assertIn("dotnet-engine", ids)
        self.assertTrue(all(p["engine"] for p in er.engines(str(ROOT))))

    def test_language_matrix_and_resolve(self):
        m = er.matrix(str(ROOT))
        self.assertIn("cargo", m)
        self.assertIn("dotnet", m)
        self.assertIn("rust-fastlane", m["cargo"])
        self.assertEqual("rust-fastlane", er.resolve(str(ROOT), "cargo")["id"])
        self.assertIsNone(er.resolve(str(ROOT), "no-such-lang"))

    def test_status_and_report_shape(self):
        st = er.status(str(ROOT))
        self.assertGreaterEqual(st["engines"], 2)
        self.assertLessEqual(st["ready"], st["engines"])
        self.assertTrue(all("tool_present" in d for d in st["detail"]))
        self.assertTrue(all(p["entry_present"] for p in er.engines(str(ROOT))))
        self.assertTrue(any("引擎 provider" in ln for ln in er.report_lines(str(ROOT))))


class MutationTest(unittest.TestCase):
    def test_temp_root_facts(self):
        with tempfile.TemporaryDirectory() as tmp:
            _mk(tmp, "integrations/x/integration.json",
                json.dumps(dict(FACE, id="x"), ensure_ascii=False))
            _mk(tmp, "engine/rust/Cargo.toml", "[package]")
            ps = er.providers(tmp)
            self.assertEqual(1, len(ps))
            self.assertTrue(ps[0]["engine"])
            self.assertEqual("cargo", ps[0]["language"])
            self.assertTrue(ps[0]["entry_present"])
            self.assertEqual([], er.providers(str(Path(tmp) / "nope")))

    def test_bad_and_missing_descriptors_are_skipped(self):
        with tempfile.TemporaryDirectory() as tmp:
            _mk(tmp, "integrations/bad/integration.json", "{ not json")
            _mk(tmp, "integrations/noid/integration.json", json.dumps({"title": "x"}))
            self.assertEqual([], er.providers(tmp))


if __name__ == "__main__":
    unittest.main()
