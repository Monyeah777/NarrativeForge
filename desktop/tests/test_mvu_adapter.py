# -*- coding: utf-8 -*-
"""MVU 变量模板导出适配器单测（fixture 自包含，不依赖仓库外部状态）。"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from core import exporter  # noqa: E402
from core.mvu_adapter import build_mvu_payload, export_mvu  # noqa: E402

CONTRACT = """```yaml
machine_contract:
  id: M50
  world_model:
    variables:
      pipeline:
        kind: string
        slot: pipeline_id
      tick:
        kind: integer
      phase:
        kind: string
      phase_trace:
        kind: array
    abstract_state:
      initial:
        P01: begin
        tick: 0
    checks:
      phase:
        values: [begin, run, end, archive, roll]
    transition:
      phases:
        - id: begin
          guard: "tick == 0"
          writes: [phase, phase_trace]
    invariants:
      - "tick 单调不减"
```
"""


class _M:
    def __init__(self, mid, content):
        self.full_id = mid
        self.id = mid
        self.content = content


class _L:
    def __init__(self, mods):
        self.modules = mods


class _IR:
    def __init__(self, mods):
        self.layers = [_L(mods)]
        self.extra_modules = []


class TestMvuAdapter(unittest.TestCase):
    def test_payload_variables_match_contract(self):
        p = build_mvu_payload(_IR([_M("通用:M50", CONTRACT)]))
        names = {v["name"] for v in p["variables"]}
        self.assertEqual(names, {"pipeline", "tick", "phase", "phase_trace"})
        self.assertEqual(p["initial"], {"P01": "begin", "tick": 0})
        self.assertEqual(p["checks"]["phase"]["values"],
                         ["begin", "run", "end", "archive", "roll"])
        self.assertTrue(p["nf_draft"])

    def test_type_map_applied(self):
        p = build_mvu_payload(_IR([_M("通用:M50", CONTRACT)]))
        got = {v["name"]: v["mvu_type"] for v in p["variables"]}
        self.assertEqual(got["tick"], "number")
        self.assertEqual(got["pipeline"], "string")

    def test_digest_deterministic_and_sensitive(self):
        a = build_mvu_payload(_IR([_M("通用:M50", CONTRACT)]))["provenance"]["digests"]
        b = build_mvu_payload(_IR([_M("通用:M50", CONTRACT)]))["provenance"]["digests"]
        self.assertEqual(a, b)
        c = build_mvu_payload(
            _IR([_M("通用:M50", CONTRACT.replace("kind: integer", "kind: number"))])
        )["provenance"]["digests"]
        self.assertNotEqual(a, c)

    def test_export_writes_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            res = exporter.ExportResult("mvu")
            export_mvu(_IR([_M("通用:M50", CONTRACT)]), Path(tmp), res)
            self.assertEqual(len(res.files), 4)
            for f in res.files:
                json.loads(Path(f).read_text(encoding="utf-8")) if f.endswith(".json") else None
            payload = json.loads((Path(tmp) / "mvu_variables.json").read_text(encoding="utf-8"))
            self.assertEqual(len(payload["variables"]), 4)
            wb = json.loads((Path(tmp) / "mvu_worldbook.json").read_text(encoding="utf-8"))
            # 结构与位置参数已核对 → 不再是整体 draft，改为精确标注待填范围
            self.assertFalse(wb["nf_draft"])
            self.assertIn("待作者填", wb["nf_draft_scope"])
            rx = json.loads((Path(tmp) / "mvu_regex.json").read_text(encoding="utf-8"))
            self.assertEqual([s["name"] for s in rx["scripts"]],
                             ["隐藏", "更新中", "美化", "隐藏状态栏", "状态栏界面"])

    def test_no_world_model_is_warning_not_crash(self):
        with tempfile.TemporaryDirectory() as tmp:
            res = exporter.ExportResult("mvu")
            export_mvu(_IR([_M("通用:M00", "no contract here")]), Path(tmp), res)
            self.assertEqual(res.files, [])
            self.assertTrue(res.warnings)

    def test_registry_has_mvu_and_unknown_fmt_mentions_it(self):
        self.assertIn("mvu", exporter._REGISTRY)
        with self.assertRaises(KeyError) as ctx:
            exporter.export(_IR([]), "nope")
        self.assertIn("mvu", str(ctx.exception))

    def test_variable_name_conflict_is_reported(self):
        p = build_mvu_payload(_IR([_M("A:M1", CONTRACT), _M("B:M2", CONTRACT)]))
        self.assertTrue(any("变量名冲突" in w for w in p["warnings"]))
        self.assertEqual(len([v for v in p["variables"] if v["name"] == "tick"]), 1)


if __name__ == "__main__":
    unittest.main()
