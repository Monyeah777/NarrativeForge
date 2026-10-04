#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""`.NET` 加速线的 probe 清单接线判据：`probe_manifest.json` ⟷ `probes/*.py` 必须严格对齐。

为什么（2026-10-04 实测）：该 manifest 自称**跑批口径的唯一出处**（`name/script/tier/args/note`），
批处理 `engine/dotnet/run-probes.ps1` 按它跑；但全仓**没有任何常驻判据引用它**
（`desktop/` · `scripts/` · `verify.sh` 里 `probe_manifest` 零命中），而 CI 只直跑 3 条 probe ——
也就是说：**新增一个 probe 文件却忘了登记，它永远不会跑，且没有任何东西会红**。本件把这条接上
（纯文本 + json，无需 dotnet/pwsh，也不写盘）。

口径：登记项必须①有对应文件；②`script` 不得重复；③`probes/` 下的 `.py` 要么被登记、
要么在 `NON_PROBE_FILES` 里逐条写明理由（共享辅助模块，非判据本身）。
"""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROBES = ROOT / "engine" / "dotnet" / "probes"
MANIFEST = PROBES / "probe_manifest.json"
#: 不是判据的共享件（逐条给理由；判据会断言它们**真的在场**，免得清单变成借口）
NON_PROBE_FILES = {"_paths.py": "probe 之间共用的路径辅助模块（被多条 probe import）"}


def entries_of(manifest) -> list:
    """→ 登记项列表（兼容 `[...]` 与 `{"probes": [...]}` 两种形态）。"""
    if isinstance(manifest, list):
        return manifest
    return list(manifest.get("probes") or [])


def wiring(manifest, files, non_probe=()) -> dict:
    """纯函数：manifest + 文件名清单 → `{missing, unregistered, duplicates, registered}`（便于变异自证）。"""
    items = entries_of(manifest)
    scripts = [str(e.get("script", "")) for e in items]
    missing = sorted(s for s in scripts if s and s not in files)
    unregistered = sorted(f for f in files if f not in scripts and f not in non_probe)
    duplicates = sorted({s for s in scripts if s and scripts.count(s) > 1})
    return {"missing": missing, "unregistered": unregistered, "duplicates": duplicates,
            "registered": len([s for s in scripts if s])}


class ProbeManifestWiringTest(unittest.TestCase):
    def test_every_probe_file_is_registered_and_every_entry_has_a_file(self):
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        files = sorted(p.name for p in PROBES.glob("*.py"))
        # 防「解析塌缩」：清单或目录一旦取错，下面会变成空转的假绿。
        self.assertGreaterEqual(len(files), 30, "解析面塌缩（probe 文件数异常）：%d" % len(files))
        got = wiring(manifest, files, tuple(NON_PROBE_FILES))
        self.assertGreaterEqual(got["registered"], 30, "解析面塌缩（登记项异常）：%s" % got)
        self.assertEqual([], got["missing"],
                         "登记了但盘上没有的 probe（跑批会直接失败）：%s" % got["missing"])
        self.assertEqual([], got["unregistered"],
                         "未登记的 probe 文件 ⇒ 永远不会被跑批执行（修复指引：登记进 probe_manifest.json，"
                         "或加进 NON_PROBE_FILES 并写明理由）：%s" % got["unregistered"])
        self.assertEqual([], got["duplicates"], "重复登记（同一 script 多次）：%s" % got["duplicates"])

    def test_non_probe_allowlist_is_not_stale(self):
        """豁免清单只许收缩：列出的件必须真的还在（消失或已登记即失效）。"""
        files = {p.name for p in PROBES.glob("*.py")}
        self.assertTrue(NON_PROBE_FILES, "豁免清单被清空——若非有意，说明判据口径变了")
        for name in NON_PROBE_FILES:
            self.assertIn(name, files, "NON_PROBE_FILES 里的 %s 已不在盘上（清单失效）" % name)

    def test_wiring_predicate_catches_the_mutations(self):
        """变异自证：漏登记 / 幽灵登记 / 重复登记必判红；正常态与豁免件不许误伤。"""
        ok = {"probes": [{"script": "a_probe.py"}, {"script": "b_probe.py"}]}
        self.assertEqual({"missing": [], "unregistered": [], "duplicates": [], "registered": 2},
                         wiring(ok, ["a_probe.py", "b_probe.py"]))
        self.assertEqual(["c_probe.py"], wiring(ok, ["a_probe.py", "b_probe.py", "c_probe.py"])["unregistered"])
        self.assertEqual([], wiring(ok, ["a_probe.py", "b_probe.py", "_paths.py"], ("_paths.py",))["unregistered"],
                         "豁免件不得算作漏登记")
        ghost = {"probes": [{"script": "ghost_probe.py"}]}
        self.assertEqual(["ghost_probe.py"], wiring(ghost, ["a_probe.py"])["missing"])
        dup = {"probes": [{"script": "a_probe.py"}, {"script": "a_probe.py"}]}
        self.assertEqual(["a_probe.py"], wiring(dup, ["a_probe.py"])["duplicates"])


if __name__ == "__main__":
    unittest.main()
