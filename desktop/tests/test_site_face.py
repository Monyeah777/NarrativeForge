# -*- coding: utf-8 -*-
"""站点面（对外文档门户）常驻判据。

内部差距实证（2026-10-07 文档平台轴审计）：site/ 是唯一的线上文档门户，但它的自检工装
只在 .github/workflows/ci-verify.yml 里跑——**本机 verify 全绿 ≠ 站点面绿**，而
desktop/tests/test_suite_wiring.py 立下的纪律正是「不许有写好了却没人跑的套件」（先例：
packaging/npm 的工装曾只在发布流跑，后由 test_npm_package 纳入常驻）。本件把站点两件
工装接进常驻套件，并把 facts.json 里此前无人核对的四类事实绑定到机读真源。
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

ROOT = Path(__file__).resolve().parents[2]


def _json(rel):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


class TestSiteFactsBindToRepoTruth(unittest.TestCase):
    """site/facts.json 的每条事实必须有锚与源，能与机读真源对上的必须对上。"""

    @classmethod
    def setUpClass(cls):
        cls.facts = _json("site/facts.json")
        cls.stats = _json("protocol/repo_stats.json")

    def _fact(self, fid):
        for f in self.facts.get("facts") or []:
            if f.get("id") == fid:
                return f
        self.fail("site/facts.json 缺事实 %s" % fid)

    def test_generated_from_sources_exist(self):
        srcs = self.facts.get("generated_from") or []
        self.assertTrue(srcs)
        for src in srcs:
            rel = str(src).split("#")[0]
            self.assertTrue((ROOT / rel).is_file(), "facts.json 声明的真源不在场：%s" % rel)

    def test_every_fact_anchored_and_sourced(self):
        for f in self.facts.get("facts") or []:
            for key in ("id", "claim_zh", "anchor", "source"):
                self.assertTrue(f.get(key), "事实 %s 缺 %s" % (f.get("id"), key))
            self.assertTrue(str(f["anchor"]).startswith("https://"), f.get("id"))

    def test_quality_fact_matches_repo_stats(self):
        want = "verify v%s · check1-%s · PASS=%s" % (
            self.stats["verify_version"], self.stats["verify_checks"], self.stats["baseline_pass"])
        self.assertIn(want, self._fact("quality")["claim_zh"],
                      "质量事实与 protocol/repo_stats.json 不一致（真源：%s）" % want)

    def test_core_fact_matches_repo_stats(self):
        claim = self._fact("core")["claim_zh"]
        self.assertIn("%d 模块" % self.stats["core_modules"], claim)
        pipes = list(self.stats["core_pipelines"])
        self.assertIn("%d 管线" % len(pipes), claim)
        for pid in pipes:
            self.assertIn(str(pid), claim)

    def test_mcp_fact_versions_match_runtime(self):
        from core import mcp_runtime as mcp
        claim = self._fact("mcp")["claim_zh"]
        for ver in mcp.SUPPORTED_VERSIONS:
            self.assertIn(ver, claim, "MCP 事实缺运行时支持版本 %s" % ver)

    def test_terminal_fact_names_real_entry(self):
        claim = self._fact("terminal")["claim_zh"]
        self.assertIn("tui/nf.py", claim)
        self.assertTrue((ROOT / "tui" / "nf.py").is_file())

    def test_npm_fact_names_package(self):
        # 版本/文件数与 npm 注册表一致属联网事实（本地不假称已核）；此处只钉包名与非空声明。
        claim = self._fact("npm")["claim_zh"]
        self.assertIn("ninfenz", claim)

    def test_verifiable_fact_binds_to_receipts_and_attestation(self):
        """可验证事实：回执单根的形状必须与 library/RECEIPTS.json 一致，签名档须真在代码里。"""
        from core import attest
        receipts = json.loads((ROOT / "library" / "RECEIPTS.json").read_text(encoding="utf-8"))
        claim = self._fact("verifiable")["claim_zh"]
        self.assertIn("RFC 6962", claim)
        self.assertIn("RFC6962", receipts["algorithm"], "回执算法须仍是 RFC 6962 域分隔")
        self.assertRegex(receipts["root"], r"^[0-9a-f]{64}$")
        for entry in receipts["entries"]:
            self.assertIsInstance(entry["proof"], list, entry.get("id"))
            self.assertRegex(entry["digest"], r"^[0-9a-f]{64}$")
        # 声明是人类可读的族名（hmac / ssh-sig / sigstore-keyless），代码给精确档名
        # （hmac-sha256 / ssh-sig / sigstore-keyless）——按族名对账，精确档名由常量本身保证。
        for scheme in (attest.SCHEME_HMAC, attest.SCHEME_SSH, attest.SCHEME_SIGSTORE):
            self.assertIn(scheme.split("-")[0], claim,
                          "事实声明的签名族 %s 须真在 attest 中（常量 %s）" % (scheme, scheme))
        self.assertIn("fail-closed", claim)

    def test_limits_fact_is_truthful(self):
        """边界事实：必须仍是「无托管服务 / 无付费层 / 核心纯标准库」。"""
        limits = self.facts.get("limits") or {}
        self.assertIs(False, limits.get("hosted_service"))
        self.assertIs(False, limits.get("paid_tier"))
        self.assertIn("纯标准库", str(limits.get("third_party_deps")))
        self.assertTrue(str(limits.get("gates_scope") or "").strip())


#: 站点机器面与一键引导；其中的仓库路径与命令是这个站的**对外承诺**
MACHINE_ENTRIES = ("site/llms.txt", "site/nf.txt", "site/agent.txt", "site/run.sh")
#: 站点自身产出的文件名（在站内出现是自指，不是仓库路径）
_SITE_OWNED = {"llms.txt", "llms-full.txt", "facts.json", "nf.txt", "agent.txt", "run.sh"}
#: 仓库相对路径候选（含扩展名；前缀带 / 的 URL 片段不取——避免把仓库地址里的路径当承诺）
_REPO_PATH = re.compile(r"(?<![\w./-])([\w][\w.-]*(?:/[\w][\w.-]*)*"
                        r"\.(?:md|py|sh|json|cff|toml|yaml|yml|txt))")
_NF_CALL = re.compile(r"(?:\bpython\s+scripts/nf\.py|\bnf)\s+([a-z][a-z0-9-]*)")
#: 脚本里的调用形如 `"$PY" scripts/nf.py doctor`（解释器是变量，不能只认字面 python）
_SCRIPT_NF_CALL = re.compile(r"scripts/nf\.py\"?\s+([a-z][a-z0-9-]*)")
_NPX_CALL = re.compile(r"\bnpx\s+-y\s+ninfenz\s+([a-z][a-z0-9-]*)")


def _machine_texts():
    for rel in MACHINE_ENTRIES:
        yield rel, (ROOT / rel).read_text(encoding="utf-8")


def _cli_commands():
    src = (ROOT / "scripts" / "nf.py").read_text(encoding="utf-8")
    cmds = set(re.findall(r'sub\.add_parser\(\s*"([a-z0-9-]+)"', src))
    for group in re.findall(r"aliases\s*=\s*\[([^\]]*)\]", src):
        cmds.update(re.findall(r'"([a-z0-9-]+)"', group))
    return cmds


class TestSiteMachineEntriesPointAtRealArtifacts(unittest.TestCase):
    """站点的机器面**只承诺仓库里真实在场的东西**（原差距：站点正文语义无真源绑定）。

    站点是唯一线上文档门户，它的 llms/nf/agent 三件是给 AI 与 agent 直接执行的入口清单——
    里面写着的仓库路径与命令就是这个站的对外承诺。此前只有「数字」受判（质量凭证串/规模 8 数），
    路径与命令没有任何判据：一次改名或删除就能让站点指向不存在的件，而门禁全绿。
    """

    def test_repo_paths_mentioned_exist(self):
        seen, missing = 0, []
        for rel, text in _machine_texts():
            for m in _REPO_PATH.finditer(text):
                tok = m.group(1)
                if os.path.basename(tok) in _SITE_OWNED:
                    continue
                seen += 1
                if not (ROOT / tok).exists():
                    missing.append("%s → %s" % (rel, tok))
        self.assertGreaterEqual(seen, 8, "没扫到仓库路径（判据可能已失效）")
        self.assertEqual([], missing,
                         "站点机器面指向了不存在的仓库件（修复指引：修正路径或补件）")

    def test_nf_commands_mentioned_are_registered(self):
        cmds = _cli_commands()
        self.assertTrue(cmds)
        bad = []
        for rel, text in _machine_texts():
            for m in (list(_NF_CALL.finditer(text)) + list(_NPX_CALL.finditer(text))
                      + list(_SCRIPT_NF_CALL.finditer(text))):
                name = m.group(1)
                if name not in cmds and name != "tui":   # tui 由 npm 启动器/终端入口承接
                    bad.append("%s → nf %s" % (rel, name))
        self.assertEqual([], bad,
                         "站点机器面写了不存在的 nf 子命令（修复指引：核对 scripts/nf.py 注册表）")


@unittest.skipUnless(shutil.which("node"), "node 不在 PATH（站点工装需要 node；CI 已装）")
class TestSiteToolsRunResident(unittest.TestCase):
    """站点两件工装必须在常驻套件里真跑（此前只在 CI 跑，本机无人核）。"""

    def _node(self, *args):
        return subprocess.run(["node", *args], cwd=str(ROOT), capture_output=True,
                              encoding="utf-8", errors="replace", timeout=180)

    def test_sync_numbers_reports_no_drift(self):
        p = self._node("site/tools/sync-numbers.mjs")
        self.assertEqual(0, p.returncode, (p.stdout or "") + (p.stderr or ""))

    def test_site_check_offline_passes(self):
        p = self._node("site/tools/site-check.mjs", "--offline")
        self.assertEqual(0, p.returncode, (p.stdout or "") + (p.stderr or ""))

    def test_worker_behavior_probe_passes(self):
        """把 worker 真跑起来（桩 ASSETS）：协商 / q=0 / 通配 / 回落 / www 301 / 透传。"""
        p = self._node("site/tools/worker-check.mjs")
        self.assertEqual(0, p.returncode, (p.stdout or "") + (p.stderr or ""))
        self.assertIn("worker 行为判据全过", p.stdout)

    def test_worker_probe_catches_a_broken_worker(self):
        """变异负例：把协商闸门换回旧的 includes 写法 → 判据必须红（否则本件是空转的）。"""
        src = (ROOT / "site" / "worker.js").read_text(encoding="utf-8")
        broken = src.replace("if (wantsMarkdown(accept)) {",
                             "if (accept.includes('text/markdown')) {")
        self.assertNotEqual(src, broken, "变异点已不在（判据需同步更新）")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "worker.js"
            path.write_text(broken, encoding="utf-8", newline="\n")
            p = self._node("site/tools/worker-check.mjs", "--worker", str(path))
        self.assertEqual(1, p.returncode, "改坏协商闸门后判据仍全过 ⇒ 判据空转")
        self.assertIn("未过", p.stdout)


#: 中英页面对（站点实际存在的三处语言面里，site/en/* 是此前无判据的那一处）
PAGE_PAIRS = (("site/index.html", "site/en/index.html"),
              ("site/use/index.html", "site/en/use/index.html"))


def _page_ids(text):
    return set(re.findall(r'id="([a-zA-Z0-9_-]+)"', text))


def _page_heading_levels(text):
    return [int(m) for m in re.findall(r"<h([1-6])[^>]*>", text)]


def _page_ld_types(text):
    return set(re.findall(r'"@type"\s*:\s*"([A-Za-z]+)"', text))


def _page_machine_links(text):
    return set(re.findall(
        r'href="[^"]*?(llms-full[.]txt|llms[.]txt|nf[.]txt|agent[.]txt|facts[.]json|run[.]sh)"',
        text))


def page_pair_diffs(zh_text, en_text):
    """中英页对的四维平价差异（空表 = 平价）：锚点集 / 标题层级序列 / JSON-LD 类型集 / 机器入口链接集。"""
    diffs = []
    if _page_ids(zh_text) != _page_ids(en_text):
        diffs.append("锚点集不一致：%s" % sorted(_page_ids(zh_text) ^ _page_ids(en_text)))
    if _page_heading_levels(zh_text) != _page_heading_levels(en_text):
        diffs.append("标题层级序列不一致")
    if _page_ld_types(zh_text) != _page_ld_types(en_text):
        diffs.append("JSON-LD 类型集不一致：%s" % sorted(_page_ld_types(zh_text) ^ _page_ld_types(en_text)))
    if _page_machine_links(zh_text) != _page_machine_links(en_text):
        diffs.append("机器入口链接集不一致：%s"
                     % sorted(_page_machine_links(zh_text) ^ _page_machine_links(en_text)))
    return diffs


def fact_anchor_gaps(facts_doc, zh_text, en_text):
    """facts.json 每条事实声明的落地锚必须真的在页上（中英两页都查）。"""
    gaps = []
    for fact in facts_doc.get("facts") or []:
        frag = str(fact.get("anchor") or "").rsplit("#", 1)[-1]
        if not frag:
            gaps.append("%s 缺 anchor" % fact.get("id"))
            continue
        if ('id="%s"' % frag) not in zh_text:
            gaps.append("%s 的锚 #%s 不在中文主页" % (fact.get("id"), frag))
        if ('id="%s"' % frag) not in en_text:
            gaps.append("%s 的锚 #%s 不在英文主页" % (fact.get("id"), frag))
    return gaps


class TestSiteLanguagePageParity(unittest.TestCase):
    """中英页面平价 + 事实锚落点（审计 G5：site/en 是实际存在的第三处语言面，此前无判据）。

    覆盖的是**会静默漂移**的四维：锚点集（深链与答卡锚点）、标题层级序列（少一节/多一节）、
    JSON-LD 类型集（结构化数据对答卡的影响）、机器入口链接集（AI 读者拿到的入口）。
    另绑 facts.json 的落地锚——机器可读事实声称的锚此前没人核过它是否真的在页上。
    """

    def test_comparators_catch_drift(self):
        zh = '<h1 id="a">x</h1><h2 id="b">y</h2><a href="https://ninfenz.dev/llms.txt">l</a>' \
             '<script>"@type": "WebSite"</script>'
        self.assertEqual([], page_pair_diffs(zh, zh))
        bad = zh.replace('id="b"', 'id="c"')
        self.assertTrue(any("锚点集" in d for d in page_pair_diffs(zh, bad)))
        bad2 = zh.replace("<h2", "<h3")
        self.assertTrue(any("标题层级" in d for d in page_pair_diffs(zh, bad2)))
        bad3 = zh.replace('"@type": "WebSite"', '"@type": "Article"')
        self.assertTrue(any("JSON-LD" in d for d in page_pair_diffs(zh, bad3)))
        bad4 = zh.replace("llms.txt", "gone.txt")
        self.assertTrue(any("机器入口" in d for d in page_pair_diffs(zh, bad4)))

    def test_anchor_binding_catches_drift(self):
        facts = {"facts": [{"id": "quality", "anchor": "https://ninfenz.dev/#fact-quality"}]}
        ok = '<h2 id="fact-quality">q</h2>'
        self.assertEqual([], fact_anchor_gaps(facts, ok, ok))
        self.assertTrue(fact_anchor_gaps(facts, ok, "<h2>缺失</h2>"))
        self.assertTrue(fact_anchor_gaps({"facts": [{"id": "x", "anchor": ""}]}, ok, ok))

    def test_real_pages_are_in_parity(self):
        for zh_rel, en_rel in PAGE_PAIRS:
            zh = (ROOT / zh_rel).read_text(encoding="utf-8")
            en = (ROOT / en_rel).read_text(encoding="utf-8")
            self.assertGreaterEqual(len(_page_ids(zh)), 5, zh_rel + " 锚点过少（判据可能空转）")
            self.assertGreaterEqual(len(_page_machine_links(zh)), 4, zh_rel + " 机器入口过少")
            self.assertEqual([], page_pair_diffs(zh, en), "%s ↔ %s 未平价" % (zh_rel, en_rel))

    def test_real_fact_anchors_land_on_both_pages(self):
        facts = json.loads((ROOT / "site" / "facts.json").read_text(encoding="utf-8"))
        zh = (ROOT / "site" / "index.html").read_text(encoding="utf-8")
        en = (ROOT / "site" / "en" / "index.html").read_text(encoding="utf-8")
        self.assertGreaterEqual(len(facts.get("facts") or []), 5, "facts 过少（判据可能空转）")
        self.assertEqual([], fact_anchor_gaps(facts, zh, en))


#: 机器面里以「工具（a / b / c）」/「prompt（x）」形式点名 MCP 能力的句式
_MCP_MENTION = re.compile(r"(?:工具|prompt|提示)\s*（([^）]*)）")


def mcp_capability_mentions(text):
    """机器面点名的 MCP 能力名（工具 / prompt）。"""
    out = []
    for m in _MCP_MENTION.finditer(text):
        for tok in re.split(r"\s*/\s*", m.group(1)):
            tok = tok.strip()
            if tok:
                out.append(tok)
    return out


class TestSiteMcpCapabilityNames(unittest.TestCase):
    """站点机器面点名的 MCP 能力必须真在运行时里。

    为什么需要：site/agent.txt 是 agent 直接读的装载指令，里面点名了可调用的 MCP 工具与
    prompt（检索类四个 / 内容通道三个 / 装载引导一个）。docs/ 面有 prose_lint.command_face
    的「MCP 工具名 ↔ 运行时」判据，但它的扫描面不含 site/*.txt——站点改名或删掉一个工具，
    这里会静默漂移，agent 照站点调用就会拿到 -32602。
    """

    def test_extraction_logic(self):
        text = "检索类工具（library_search / registry_query）、引导 prompt（assemble_guide）"
        self.assertEqual(["library_search", "registry_query", "assemble_guide"],
                         mcp_capability_mentions(text))
        self.assertEqual([], mcp_capability_mentions("没有任何能力名"))

    def test_mentioned_capabilities_exist_in_runtime(self):
        from core import mcp_runtime as mcp
        known = {str(t["name"]) for t in mcp.TOOL_DEFS}
        known |= {str(p.get("name")) for p in mcp.PROMPT_DEFS}
        seen, bad = 0, []
        for rel, text in _machine_texts():
            for name in mcp_capability_mentions(text):
                seen += 1
                if name not in known:
                    bad.append("%s → %s" % (rel, name))
        self.assertGreaterEqual(seen, 6, "没扫到 MCP 能力名（判据可能已失效）")
        self.assertEqual([], bad,
                         "站点机器面点名了运行时里没有的 MCP 能力（修复指引：核对 "
                         "core/mcp_runtime.TOOL_DEFS / PROMPT_DEFS）")


if __name__ == "__main__":
    unittest.main()
