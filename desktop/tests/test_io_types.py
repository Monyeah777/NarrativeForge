# -*- coding: utf-8 -*-
"""I/O 类型面（io_types）单测：推导规则、注入幂等、可证不匹配、覆盖统计。"""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from core import io_types as iot  # noqa: E402

ROOT = str(Path(__file__).resolve().parents[2])

MOD = """# 模块 M99 · 测试
> 类别：通用｜挂载点：P00

```yaml
machine_contract:
  schema: "1"
  id: M99
  name: 测试
  category: 通用
  layer: P00
  inputs: [M00, M10]
  outputs: [tick, weird_token]
  events:
    publish: []
    subscribe: []
  interfaces: []
```

## 1. 职责
测试用。
"""


def _tree(tmp, text=MOD, name="M99_测试.md"):
    d = Path(tmp, "04_模块库", "通用类")
    d.mkdir(parents=True, exist_ok=True)
    (d / name).write_text(text, encoding="utf-8")
    return tmp


class TestIoTypes(unittest.TestCase):
    def test_derive_uses_event_registry_evidence(self):
        ev = {"tick": "number"}
        io = iot.derive(["tick", "weird_token"], ["M00", "M10"], ev)
        self.assertEqual(io["outputs"]["tick"], "number")
        self.assertEqual(io["outputs"]["weird_token"], "untyped")
        self.assertEqual(io["inputs"]["M00"], "state")
        self.assertEqual(io["inputs"]["M10"], "untyped")

    def test_inject_then_parse_roundtrip(self):
        io = iot.derive(["tick"], ["M00"], {"tick": "number"})
        text = iot.inject(MOD, io)
        self.assertIn("io_types:", text)
        parsed = iot.parse_io_types(text)
        self.assertEqual(parsed["outputs"]["tick"], "number")
        self.assertEqual(parsed["inputs"]["M00"], "state")
        self.assertEqual(iot.inject(text, io), text, "注入必须幂等")

    def test_empty_sections_render_as_map(self):
        io = iot.derive([], ["M10"], {})
        text = iot.inject(MOD, io)
        self.assertIn("outputs: {}", text)
        self.assertNotIn("outputs:\n", text.replace("outputs: {}", ""))

    def test_scan_reports_full_contract_coverage(self):
        """L0 retro-fit 收口后：全库模块均有机器契约（L0=0），且类型面有已收窄字段。"""
        _issues, _warns, stats = iot.scan(ROOT)
        self.assertGreaterEqual(stats["modules_with_contract"], 44)
        self.assertGreater(stats["typed_fields"], 0)
        self.assertEqual(stats["l0_modules"], 0)

    def test_provable_mismatch_is_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            # 提供方 M10：outputs [tick]（number）
            _tree(tmp, MOD.replace("id: M99", "id: M10").replace(
                "inputs: [M00, M10]", "inputs: [M00]"), "M10_时间推进.md")
            provider = Path(tmp, "04_模块库", "通用类", "M10_时间推进.md")
            provider.write_text(
                iot.inject(provider.read_text(encoding="utf-8"),
                           {"outputs": {"tick": "number"}, "inputs": {"M00": "state"}}),
                encoding="utf-8")
            # 消费方 M99：inputs {M10: string}（与 number 冲突）
            consume = Path(tmp, "04_模块库", "通用类")
            body = MOD.replace("inputs: [M00, M10]", "inputs: [M00, M10]")
            (consume / "M99_消费.md").write_text(
                iot.inject(body, {"outputs": {}, "inputs": {"M00": "state",
                                                            "M10": "string"}}),
                encoding="utf-8")
            issues, _warns, _stats = iot.scan(tmp)
            self.assertTrue(any("类型不匹配" in i for i in issues), issues)

    def test_coverage_shape(self):
        cov = iot.coverage(ROOT)
        self.assertIn("coverage", cov)
        self.assertLessEqual(cov["coverage"], 100.0)


class LiveFaceConsistencyTest(unittest.TestCase):
    """`io_types` 派生面必须与**实时推导**一致，且「写了就要读得到」（读写口径同源）。

    依据（2026-10-02 追查）：`nf module types --write` 一次改写了 **105** 件模块文档，逐件核对后
    发现其中 **100 件是纯形态归一**（旧渲染给含冒号的键加了引号、键序也不同，**YAML 层内容逐字段
    相同**），只有 5 件是真收窄（`untyped→object/boolean/string/array`）。但这次归一暴露了两处真
    缺口：① 本模块的行式读者 `parse_io_types` 的键模式是 `[^:\\s]+`——**含冒号的键（跨包依赖
    `AI保险:M01` 这类）永远读不出来**，即"写出去的键读不回来"（YAML 读者认、行式读者不认，两个
    reader 不同源）；② `scan` 只核对 `outputs` 键集，**`inputs` 侧从不核对**，所以①的盲区一直
    不可见。本件把三件事钉住：派生面不许陈旧、两个 reader 往返一致、`inputs` 键集也须对齐。
    """

    def test_derived_face_is_not_stale(self):
        rows = iot.apply(ROOT, write=False)
        changed = [r["path"] for r in rows if r.get("changed")]
        self.assertGreaterEqual(len(rows), 200, "模块面塌缩（判据可能已失效）")
        self.assertEqual([], changed,
                         "io_types 派生面陈旧（修复指引：nf module types --write 后重签边界）：%s"
                         % changed[:5])

    def test_both_sections_have_no_key_set_mismatch(self):
        _issues, warns, _stats = iot.scan(ROOT)
        bad = [w for w in warns if "键集不一致" in w]
        self.assertEqual([], bad, "io_types 与声明键集不一致：%s" % bad[:3])

    def test_reader_reads_what_the_writer_writes(self):
        """写→读**往返**：含冒号的跨包依赖键也必须读得回来（旧读者把它们整条丢掉）。"""
        io = {"outputs": {"tick": "number"},
              "inputs": {"M00": "state", "AI保险:M01": "untyped"}}
        text = iot.inject(MOD, io)
        self.assertEqual(io, iot.parse_io_types(text),
                         "写出去的键读不回来（读者/写者口径不同源）")

    def test_reader_tolerates_the_legacy_quoted_form(self):
        """变异自证的另一半：旧渲染留下的**加引号**写法也要读得回来（不许把历史形态读成缺键）。"""
        legacy = MOD.replace(
            "  interfaces: []",
            "  interfaces: []\n  io_types:\n    outputs:\n      tick: number\n"
            "    inputs:\n      M00: state\n      'AI保险:M01': untyped")
        got = iot.parse_io_types(legacy)
        self.assertEqual("untyped", (got or {}).get("inputs", {}).get("AI保险:M01"))


if __name__ == "__main__":
    unittest.main()
