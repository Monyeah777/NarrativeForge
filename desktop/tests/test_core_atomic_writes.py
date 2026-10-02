# -*- coding: utf-8 -*-
"""在仓产物的写入口必须走 `atomic_write`（半截件不留）——**模块级机械普查**。

为什么（2026-10-01 取证）：`atomic_write` 的模块 docstring 早写明「已发布产物的写入口仍是
裸 `open(path, "w")`……agent 密集重复调用下，读者可能读到半截内容」，仓库也转过两批；但没有
判据盯着，于是又长出 8 处：`payload_harvest`（写 `protocol/event_registry.json` /
`type_backlog.json`）、`perf_budget`（写 `perf_budget.json`）、`pipelinerun`（写
`pipeline_advisory.json`）、`protocol_golden`（写 `protocol/generated/*`）、
`transparency_log`（写 `receipt_chain.json`）、`verify_report`（写
`verification_report.json`）、`regression_score`（写 `score_baseline.json`）、
`skill_adapter` / `steelman`（交付件）。本件把「core 里有写 sink 就得引用 atomic_write」
做成常驻判据；**只写用户态/临时**的模块逐条列进 `REVIEWED_NO_ATOMIC` 并写明理由。
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CORE = ROOT / "desktop" / "src" / "core"

SINKS = re.compile(r"\.write_text\(|\.write_bytes\(|open\([^)]*['\"]w|json\.dump\(")
#: 自身/缓存实现不参与（前者就是 atomic_write 本体；后者早用 tmp+os.replace，见其 docstring）
SKIP_STEMS = {"atomic_write", "disk_cache"}
#: 已复核：有写 sink 但**只写用户态/临时路径**，不算在仓产物
REVIEWED_NO_ATOMIC = {
    "attest": "只写临时工作目录里的 ssh 签名载荷（非仓产物）",
    "daemon": "只写 `<NF_HOME>/daemon.json`——它自己做了 tmp + `os.replace`（见 write_state）",
    "storage": "只写 NF_HOME 用户库（Store 自有语义；本波未纳入）",
    "watch": "只写 NF_HOME 监听状态",
}


def modules_with_sinks() -> dict:
    """→ `{模块名: 命中行号}`：core 里有写 sink 的模块。"""
    out = {}
    for p in sorted(CORE.glob("*.py")):
        if p.stem in SKIP_STEMS:
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        hits = [i for i, ln in enumerate(text.splitlines(), 1) if SINKS.search(ln)]
        if hits:
            out[p.stem] = hits
    return out


class CoreAtomicWriteTest(unittest.TestCase):
    def test_scanner_is_not_vacuous(self):
        self.assertGreater(len(modules_with_sinks()), 10, "普查没扫到模块（判据可能已失效）")

    def test_all_artifact_writers_use_atomic_write(self):
        missing = []
        for stem in modules_with_sinks():
            if stem in REVIEWED_NO_ATOMIC:
                continue
            text = (CORE / ("%s.py" % stem)).read_text(encoding="utf-8", errors="replace")
            if "atomic_write" not in text:
                missing.append(stem)
        self.assertEqual([], sorted(missing),
                         "有写 sink 却没用 atomic_write 的 core 模块（在仓产物须原子落盘；"
                         "只写用户态/临时路径的请登记进 REVIEWED_NO_ATOMIC 并写明理由）：%s"
                         % sorted(missing))

    def test_reviewed_allowlist_is_not_stale(self):
        """已复核清单**只减不增**：某模块补上了 atomic_write 就该从清单里划掉。"""
        live = modules_with_sinks()
        stale = []
        for stem in REVIEWED_NO_ATOMIC:
            if stem not in live:
                stale.append("%s（已无写 sink 或已删）" % stem)
                continue
            text = (CORE / ("%s.py" % stem)).read_text(encoding="utf-8", errors="replace")
            if "atomic_write" in text:
                stale.append("%s（已接入 atomic_write）" % stem)
        self.assertEqual([], sorted(stale), "REVIEWED_NO_ATOMIC 有失效条目：%s" % sorted(stale))

    def test_script_and_bot_faces_use_atomic_write_too(self):
        """**脚本面**（`scripts/*.py` + `.github/scripts/*.py`）的落盘同样要原子。

        依据（2026-10-01 三批普查）：核心模块那件只管 `desktop/src/core/*.py`；随后两批才补到
        `scripts/nf.py`（11 处裸写：`render --dest` / `pipeline new` / 模块头就地改 /
        `attest|bench|state-front|st-validate --out` / `review --write` / `assemble --save|--build`
        / 会话状态）、其余 `scripts/*.py`（8 处：验证卡册 / 取证报告 / GEO 导出 / 他证状态表 /
        FDE 样例 / 冒烟产物 / 自包含样本）与两个**入库机器人**（`.github/scripts/*`，写的是
        **公开边界**的馆藏件）。本件把整片脚本面钉住：不得再有裸写 sink。
        """
        faces = [ROOT / "scripts" / "nf.py"] + sorted((ROOT / "scripts").glob("*.py")) \
            + sorted((ROOT / ".github" / "scripts").glob("*.py"))
        raw = {}
        for p in dict.fromkeys(faces):          # 去重（nf.py 在上面的 glob 里会出现两次）
            text = p.read_text(encoding="utf-8", errors="replace")
            bad = [i for i, ln in enumerate(text.splitlines(), 1)
                   if SINKS.search(ln) and "atomic_write" not in ln]
            if bad:
                raw[p.relative_to(ROOT).as_posix()] = bad
        self.assertEqual({}, raw,
                         "脚本面有裸写 sink（在仓产物/交付件须走 atomic_write）：%s" % raw)


if __name__ == "__main__":
    unittest.main()
