# -*- coding: utf-8 -*-
"""静默跳过必须**成文理由**（`try/except: pass|continue` 逐站点）。

为什么：仓库既有纪律是「静默跳过要登记理由」（AUD-0016：30 条静默跳过与源码里 30 条
`# nosec … AUD-0016` 标记一一对应，CHANGELOG 写着「无未登记吞错」）。2026-09-30 用
AST 重扫发现：**实际站点数是 79，不是一个 30**——其中 27 处连一行注释都没有，另有 3 处
是**真 fail-open**（读不到 `library/` 条目却当作「未漂移」；registry 读不到却把全部域规格
显示成「未建」；会话落盘失败却不吭声）。三处已按 fail-closed 修掉，其余 24 处补了成文理由。

判据（零依赖、AST 级，与 ruff S110/S112 同形但覆盖面更宽）：`try` 的某个 handler 体**只有**
`pass` 或 `continue` ⇒ 该 handler 的 `except` 行（或 try 行、或其上三行）必须出现注释。
变异自证：合成两段源码，无注释的必判红、有注释的不许误报；并要求真仓站点数 ≥ 50（防止
判据面意外缩小成「扫不到东西 ⇒ 永远绿」）。

**规则实现在 `core/silent_skip.py`（2026-10-01 收敛）**：同一条规则此前**两份实现**——本件
（AST 版）与缺口引擎 `core/gap_review._silent_skip_candidates`（行扫版，窗口更窄），口径一宽
一窄的结果是 `nf review` 在真仓报出 **8 条假缺口**（逐条核过，全是有理由的站点）。现在两边
都调 `core.silent_skip`，本件的全部断言与变异自证原样保留，只是不再自带实现。
"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCAN_DIRS = ("desktop/src/core", "scripts")
if str(ROOT / "desktop" / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "desktop" / "src"))

from core.silent_skip import silent_returns, silent_skips, unjustified  # noqa: E402


class SilentSkipReasonTest(unittest.TestCase):
    def test_every_silent_skip_carries_a_reason(self):
        bad, total = [], 0
        for d in SCAN_DIRS:
            for f in sorted((ROOT / d).glob("*.py")):
                text = f.read_text(encoding="utf-8")
                hits = unjustified(text)
                total += len(silent_skips(text))
                for try_line, h_line, kind, _ in hits:
                    bad.append("%s:%d(%s, try@%d)" % (f.relative_to(ROOT).as_posix(),
                                                      h_line, kind, try_line))
        self.assertGreaterEqual(total, 50, "站点数异常偏少（%d）——判据面可能被缩小" % total)
        self.assertEqual([], bad, "静默跳过缺成文理由（修复指引：在该 `except` 行补一行"
                                  "「为何可以吞」的注释，或改成 fail-closed 如实报问题）：%s" % bad)

    def test_no_bare_empty_return_swallows_an_exception(self):
        """第二种吞错形态：`except → return 空值` 且不留任何痕（见 `silent_returns`）。"""
        bad, total = [], 0
        for d in SCAN_DIRS:
            for f in sorted((ROOT / d).glob("*.py")):
                text = f.read_text(encoding="utf-8")
                hits = silent_returns(text)
                total += len(hits)
                for try_line, h_line in hits:
                    bad.append("%s:%d(try@%d)" % (f.relative_to(ROOT).as_posix(),
                                                  h_line, try_line))
        self.assertGreaterEqual(total, 0)
        self.assertEqual([], bad, "`except` 后直接返回空值且不留痕（修复指引：带上错误消息、"
                                  "补一行理由注释，或在 docstring 写明失败语义）：%s" % bad)

    def test_empty_return_predicate_catches_the_mutation(self):
        bare = "try:\n    x()\nexcept OSError:\n    return {}\n"
        noted = "try:\n    x()\nexcept OSError:  # 读不到就当没有（调用方按缺失处理）\n    return {}\n"
        messaged = 'try:\n    x()\nexcept OSError as e:\n    return {}, str(e)\n'
        documented = ('def f():\n    """失败 ⇒ 空 dict（调用方按缺失如实呈现）。"""\n'
                      "    try:\n        x()\n    except OSError:\n        return {}\n")
        self.assertEqual(1, len(silent_returns(bare)))
        self.assertEqual([], silent_returns(noted))
        self.assertEqual([], silent_returns(messaged))
        self.assertEqual([], silent_returns(documented))

    def test_predicate_catches_the_mutation(self):
        """变异自证：无注释必判红；有注释、以及非静默形态都不许误报。"""
        bare = "for x in y:\n    try:\n        read(x)\n    except OSError:\n        continue\n"
        noted = ("for x in y:\n    try:\n        read(x)\n"
                 "    except OSError:  # 跳过不可读件（对应门禁另报）\n        continue\n")
        logged = ("for x in y:\n    try:\n        read(x)\n"
                  "    except OSError:\n        log.warning('x')\n")
        self.assertEqual(1, len(unjustified(bare)))
        self.assertEqual([], unjustified(noted))
        self.assertEqual([], unjustified(logged))


if __name__ == "__main__":
    unittest.main()
