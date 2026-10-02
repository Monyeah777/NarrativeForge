# -*- coding: utf-8 -*-
"""载荷收割的**形态覆盖**门禁：正文写了证据就必须收得到（缺口引擎的 `unharvestable-payload` 恒空）。

依据（2026-10-01 缺口普查）：`nf review` 的缺口引擎报 15 条「可修」，其中 7 条是
`unharvestable-payload`——官方/社区模块正文写着 `payload: {…}`，里面**带类型证据**
（`flags[]` = 数组、`modifiers{combat, travel}` = 对象），可收割器一条都没收到：事件名写成了
**块映射**形态

    publish:
      interaction_update:
        payload: {npc_id, type, affinity_delta, context, flags[]}

而 `harvest_doc` 只认 `publish: <名字>`（同行）/ `event:` / `name:` 三种写法。更要命的是那段
「事件名没人认领时回头找」的兜底**是个空转墓碑**——`for back in fence.splitlines(): … continue`
只 `continue`，既不赋值也不 break，等于没写。所以这不是「没有证据」，是**证据收不到**：
`event_registry.json` 里那些字段一直停在 `untyped`（或干脆不在册）。

修法：块映射形态补进收割器（缩进一层的事件键即事件名、同级下一个键换事件、结构键不当事件；
`location(M07)` 这类**括注**从键里剥掉），空转循环删除。本件把「形态覆盖」钉住：
**围栏里每一条 payload 行的类型证据都必须收得到**——新增一种没被认出的写法即红。
"""
import re
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "desktop" / "src"))

from core import gap_review as gr          # noqa: E402
from core import payload_harvest as ph     # noqa: E402

_FENCE = re.compile(r"```(?:yaml|yml)\n(.*?)```", re.S)
_PAYLOAD_LINE = re.compile(r"(?m)^\s*payload\s*:\s*\{")


def _fence(body: str) -> str:
    return "## 事件契约\n\n```yaml\n%s```\n" % body


class BlockMappingFormTest(unittest.TestCase):
    """块映射形态（事件名在**下一层缩进**的键上）必须被认出——这是那 7 条缺口的根因。"""

    def test_block_mapping_resolves_event_and_types(self):
        got = ph.harvest_doc(_fence(
            "publish:\n"
            "  interaction_update:\n"
            "    payload: {npc_id, flags[]}\n"
            "    subscribers: [M40, M14]\n"))
        self.assertIn("interaction_update", got, "块映射写法的事件名没被认出来")
        self.assertEqual("array", got["interaction_update"]["flags"], "类型证据应收窄为 array")
        self.assertEqual("untyped", got["interaction_update"]["npc_id"], "无类型证据须如实 untyped")

    def test_sibling_keys_switch_the_event(self):
        """同一 `publish:` 块里并列多个事件：各归各的（「认第一个就锁死」的实现会在这里判红）。"""
        got = ph.harvest_doc(_fence(
            "publish:\n"
            "  event_a:\n"
            "    payload: {a_id, a_tags[]}\n"
            "  event_b:\n"
            "    payload: {b_id, b_tags[]}\n"))
        self.assertEqual({"a_id", "a_tags"}, set(got.get("event_a") or {}))
        self.assertEqual({"b_id", "b_tags"}, set(got.get("event_b") or {}))

    def test_structural_keys_are_never_events(self):
        """`subscribers:` / `payload:` 是结构键，不是事件名——认错了就是把字段挂到不存在的事件上。"""
        got = ph.harvest_doc(_fence(
            "publish:\n"
            "  subscribers: [M01]\n"
            "  payload: {orphan_id, orphan_tags[]}\n"))
        self.assertEqual({}, got, "结构键被当成了事件名")

    def test_event_below_the_block_is_not_captured(self):
        """块已经结束（缩进回到 publish 同级）之后的行，不该再被算进该块。"""
        got = ph.harvest_doc(_fence(
            "publish:\n"
            "  ev_in:\n"
            "    payload: {in_id, in_tags[]}\n"
            "subscribers: [M01]\n"
            "payload: {out_id, out_tags[]}\n"))
        self.assertEqual({"in_id", "in_tags"}, set(got.get("ev_in") or {}))
        self.assertEqual(["ev_in"], list(got), "块外的 payload 不该另起事件")

    def test_marker_forms_still_work(self):
        """回归：既有三种写法（`event:` / 行内 `publish:` / `produce:`）不许被这次改动碰坏。"""
        self.assertEqual("array", ph.harvest_doc(_fence(
            "event: e_one\npayload: {a, b[]}\n"))["e_one"]["b"])
        self.assertEqual("array", ph.harvest_doc(_fence(
            "publish: e_two\npayload: {c, d[]}\n"))["e_two"]["d"])
        self.assertEqual("array", ph.harvest_doc(_fence(
            "produce: e_three\npayload: {e, f[]}\n"))["e_three"]["f"])

    def test_payload_without_any_event_is_not_guessed(self):
        """没有任何事件标记的 payload 行**不许猜**事件名（宁可收不到，也不许挂错）。"""
        self.assertEqual({}, ph.harvest_doc(_fence("payload: {lonely_id, lonely_tags[]}\n")))

    def test_inline_annotation_is_not_part_of_the_field_name(self):
        """`location(M07)` 的括注是「该字段由 M07 提供」的说明，不是键的一部分。"""
        got = ph.harvest_doc(_fence(
            "publish:\n"
            "  quest_state:\n"
            "    payload: {quest_id, location(M07), reward}\n"))
        self.assertEqual({"quest_id", "location", "reward"}, set(got["quest_state"]))


class RepoHarvestCoverageTest(unittest.TestCase):
    """真仓面：**不许有收不到的类型证据**（缺口引擎的 `unharvestable-payload` 恒为空）。"""

    def _payload_lines(self) -> int:
        n = 0
        for p in sorted((ROOT / "04_模块库").rglob("*.md")) + sorted(
                (ROOT / "community").glob("*/modules/*.md")):
            text = p.read_text(encoding="utf-8", errors="replace")
            for body in _FENCE.findall(text):
                n += len(_PAYLOAD_LINE.findall(body))
        return n

    def test_no_typed_payload_evidence_is_unreachable(self):
        lines = self._payload_lines()
        self.assertGreaterEqual(lines, 300, "扫到的 payload 行太少（判据可能已失效）")
        rows = gr.candidates(str(ROOT), classes=("unharvestable-payload",))
        self.assertEqual([], rows,
                         "模块正文里的载荷类型证据收不到（修复指引：把该写法补进 "
                         "`payload_harvest.harvest_doc`，或把正文改成已支持的写法）：%s"
                         % [("%s:%s" % (r["file"], r["line"])) for r in rows])

    def test_the_detector_still_has_teeth(self):
        """变异自证：合成一篇「有类型证据却无事件标记」的模块文档，缺口引擎必须报出来。"""
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp, "04_模块库", "通用类")
            d.mkdir(parents=True)
            (d / "M99_合成.md").write_text(
                "# M99 合成\n\n## 事件契约\n\n```yaml\npayload: {foo_id, foo_tags[]}\n```\n",
                encoding="utf-8", newline="\n")
            rows = gr.candidates(tmp, classes=("unharvestable-payload",))
        self.assertTrue(rows, "缺口引擎对「有类型证据收不到」已失去判别力（判据将永远是绿的）")


if __name__ == "__main__":
    unittest.main()
