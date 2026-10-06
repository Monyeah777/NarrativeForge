# -*- coding: utf-8 -*-
"""文档示例可执行性（「照着抄就能跑」）。

动机（2026-09-30 文档示例真跑）：把活文档里出现的 `nf` 示例逐条真跑，抓到 `nf bench
compare runs/*.json` 这条**文档原样示例**在 Windows 上跑不通——cmd 不做通配展开，实现直接
拿字面 `runs/*.json` 去 `open` ⇒ 裸 `OSError` 冒成「内部错误」。修复后：**通配由程序自行
展开**，落空给可执行指引（机器面 `--json` 亦有错误体）。
"""
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
NF = str(ROOT / "scripts" / "nf.py")
CASE = "desktop/tests/fixtures/benchmark/suite/p02-campus-emotion"


def _run(*argv):
    return subprocess.run([sys.executable, NF, *argv], capture_output=True,
                          encoding="utf-8", errors="replace", timeout=300, cwd=str(ROOT))


class DocumentedCommandRunsTest(unittest.TestCase):
    """文档/技能参考里**原样可跑**的示例必须真跑得通（2026-10-01 全量真跑取证）。

    依据：把在场文档里的 `nf …` 示例抽出来（去注释/接续行/占位符/写盘/阻塞形态）逐条真跑
    118 条，抓到两条：`nf market --tier community --json` **示例本身写错**（缺 `--list`，
    照抄即 rc=2），`nf worldmodel --run --state state.json` 抛裸 `[Errno 2]` 冒成「内部错误」，
    两条都已修；这里把修好的形态钉住，防文档再次漂移。
    """

    def test_market_list_tier_json_runs(self):
        p = _run("market", "--list", "--tier", "community", "--json")
        self.assertEqual(0, p.returncode, p.stdout + p.stderr)
        self.assertIn("items", json.loads(p.stdout))

    def test_worldmodel_missing_state_is_a_clean_error(self):
        p = _run("worldmodel", "--run", "--state", "__NF_PROBE__.json")
        text = (p.stdout or "") + (p.stderr or "")
        self.assertNotEqual(0, p.returncode)
        self.assertNotIn("内部错误", text)
        self.assertIn("修复指引", text)


class BenchDocExampleTest(unittest.TestCase):
    def test_documented_glob_form_runs(self):
        """文档原样写法 `nf bench compare runs/*.json` 必须可跑（通配由程序展开）。"""
        with tempfile.TemporaryDirectory() as tmp:
            out = str(Path(tmp, "r1.json"))
            p = _run("bench", "run", "--case", CASE, "--out", out)
            self.assertEqual(0, p.returncode, p.stdout + p.stderr)
            Path(tmp, "r2.json").write_text(Path(out).read_text(encoding="utf-8"),
                                            encoding="utf-8", newline="\n")
            q = _run("bench", "compare", str(Path(tmp, "*.json")))
            self.assertEqual(0, q.returncode, q.stdout + q.stderr)
            self.assertIn("nf bench compare", q.stdout)

    def test_unmatched_glob_is_a_clean_error_with_json_body(self):
        p = _run("bench", "compare", "runs/*.json", "--json")
        self.assertEqual(1, p.returncode)
        self.assertIn("修复指引", p.stderr)
        self.assertNotIn("内部错误", p.stderr)
        doc = json.loads(p.stdout)          # 机器面必须仍是合法 JSON
        self.assertFalse(doc["ok"])


class PostmortemAndAttestDocExampleTest(unittest.TestCase):
    """同轮从文档示例里抓到的另两处：`postmortems/PO-0001-*.md` 通配、`--ssh-key ~/…`。"""

    def test_postmortem_glob_form_runs(self):
        p = _run("postmortem", "check", "postmortems/PO-0001-*.md")
        self.assertEqual(0, p.returncode, p.stdout + p.stderr)
        self.assertIn("行动项", p.stdout)
        self.assertIn("四段齐", p.stdout)

    def test_postmortem_unmatched_glob_is_clean_and_json(self):
        p = _run("postmortem", "check", "postmortems/NOPE-*.md", "--json")
        self.assertEqual(1, p.returncode)
        self.assertNotIn("内部错误", p.stderr)
        self.assertIn("修复指引", p.stderr)
        self.assertFalse(json.loads(p.stdout)["ok"])

    def test_attest_missing_key_is_clean_error_with_tilde_expansion(self):
        p = _run("library", "attest", "NF-1", "--ssh-key", "~/.ssh/nf-no-such-key")
        self.assertEqual(1, p.returncode)
        self.assertNotIn("内部错误", (p.stdout or "") + (p.stderr or ""))
        self.assertIn("修复指引", p.stderr)


class NonNfDocumentedCommandTest(unittest.TestCase):
    """**非 `nf …` 形态**的文档命令也要有去处：要么被本件真跑，要么逐条说明为什么不用跑。

    依据（2026-10-01 围栏普查）：`test_doc_examples` 只抽 `nf …` 形态的示例（118 条），于是
    文档里以 `python -m core.x` / `bash scripts/*.sh` / 客户端配置 JSON 形式出现的**命令块**
    既没被真跑、也没被登记——「照着抄就能跑」这条承诺对它们**无人核**。普查 58 个含命令的围栏块，
    其中 8 个首行不是 `nf …` 形态；逐条辨别后：1 个是**真可执行**的仓内命令（本件真跑），
    7 个是配置样例 / 带占位符 / 仓库外动作（逐条登记，见 `NON_NF_BLOCK`）。
    """

    #: 围栏块所在文件 → 处置说明（"跑" = 本件真跑；其余写明为什么不必跑）
    NON_NF_BLOCK = {
        "README.md": "顶部 TUI 演示帧——是 `--demo` 的**输出**（逐字渲染结果），不是命令行；"
                     "它与渲染器的一致性由 `desktop/tests/test_nf_tui.py` 断言，无需真跑",
        "docs/text-hygiene.md": "跑：`cd desktop/src && python -m core.text_hygiene ../..`",
        "docs/42_M5_Release-checklist.md": "带版本占位符（`vX.Y.Z`）的发布流程示例，非可直接照抄形态",
        "docs/45_执行遥测规范.md": "JSON 遥测样例（数据，不是命令行）",
        "docs/lsp.md": "客户端配置（JSON / Lua 各一处），路径由编辑器填",
        "docs/mcp.md": "MCP 客户端配置（JSON 两处），路径由用户填",
        "skills/ninfenz/references/quickstart.md": "首行是仓库外动作（`git clone`），其后的 nf 命令由 doc-examples 覆盖",
    }
    FENCE = re.compile(r"(?m)^```([a-zA-Z0-9_-]*)[ \t]*$")
    CMD_HEAD = re.compile(r"^(python\s+)?nf\b|^python scripts/nf")

    def test_text_hygiene_documented_invocation_runs(self):
        """文档里那条非 `nf` 形态的仓内命令：真跑一次（`cd desktop/src && python -m …`）。

        **严格按 UTF-8 解码**（不用 `errors="replace"`）：2026-10-01 本判据首版就是栽在这里——
        用 `errors="replace"` 把 GBK 乱码悄悄吃掉，只在断言 `文本` 时才红，看不出根因是「入口
        没钉 stdio」。改成硬解码后，一旦输出不是 UTF-8 就当场抛 UnicodeDecodeError。
        """
        p = subprocess.run([sys.executable, "-m", "core.text_hygiene", "../.."],
                           cwd=str(ROOT / "desktop" / "src"), capture_output=True, timeout=300)
        self.assertEqual(0, p.returncode, (p.stderr or b"")[:200])
        out = p.stdout.decode("utf-8")          # 非 UTF-8 即抛（这正是本判据要抓的）
        self.assertIn("文本", out, "扫描摘要应含件数（判据不空转）")

    def test_every_non_nf_command_block_is_registered(self):
        """普查：含命令的围栏块若首行不是 `nf …`，其所在文件必须在 `NON_NF_BLOCK` 里。"""
        files = ([ROOT / "README.md", ROOT / "llms.txt"]
                 + sorted((ROOT / "docs").glob("*.md")) + sorted((ROOT / "skills").rglob("*.md")))
        seen, orphans = 0, []
        for p in files:
            if not p.is_file():
                continue
            text = p.read_text(encoding="utf-8", errors="replace")
            pos = list(self.FENCE.finditer(text))
            rel = p.relative_to(ROOT).as_posix()
            for i in range(0, len(pos) - 1, 2):
                body = text[pos[i].end():pos[i + 1].start()]
                if "nf " not in body and "scripts/nf" not in body:
                    continue
                if rel == "docs/terminal.md":       # 该文件的 sh 块由 test_launcher 逐条执行
                    continue
                lines = [ln.strip() for ln in body.splitlines()
                         if ln.strip() and not ln.strip().startswith("#")]
                if not lines or self.CMD_HEAD.match(lines[0]):
                    continue
                seen += 1
                if rel not in self.NON_NF_BLOCK:
                    orphans.append("%s :: %s" % (rel, lines[0][:60]))
        self.assertGreaterEqual(seen, 6, "没扫到非 nf 形态的命令块（判据可能已失效）")
        self.assertEqual([], orphans,
                         "文档里出现了未登记的非 `nf` 命令块（修复指引：真跑它，或写进 "
                         "NON_NF_BLOCK 说明为什么不必跑）：%s" % orphans)


if __name__ == "__main__":
    unittest.main()
