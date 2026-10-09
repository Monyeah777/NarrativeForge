# -*- coding: utf-8 -*-
"""对外文档 ↔ 机读真源对账（防「声明 > 实测」——内部差距实证 2026-10-07 三轴审计）。

两类漂移都是**同一形状**：人读文档写着旧状态，机读真源早已前进，而没有任何门禁对账。
MCP 有 test_mcp_packaging 逐项对账 docs/mcp.md；决策层与「默认无需快照」红线此前没有，
于是 docs/decision-layer.md 的 pulled / real_run / 容差三处、protocol/driver.json 的 serve 入口
与 skills 参考里的入口都漂了。本件把这几条钉成判据（真源读取，不抄数字）。
"""
import json
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from core import decision_layer as dl  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]


def _read(rel):
    return (ROOT / rel).read_text(encoding="utf-8")


class TestDecisionLayerDocReconciles(unittest.TestCase):
    """docs/decision-layer.md 的候选状态与判据必须与机读真源一致。"""

    @classmethod
    def setUpClass(cls):
        cls.doc = _read("docs/decision-layer.md")
        cls.spec = json.loads(_read("protocol/decision_layer.json"))

    def test_tolerance_documented_matches_runtime(self):
        reps = {"%.0e" % dl.PROB_TOL, str(dl.PROB_TOL), "1e-3"}
        self.assertTrue(any(r in self.doc for r in reps),
                        "文档未写出运行时的 PROB_TOL（%r）" % dl.PROB_TOL)
        self.assertNotIn("容差 1e-6", self.doc, "文档仍写着已被实测推翻的 1e-6 容差")

    def test_no_stale_blanket_pulled_claim(self):
        self.assertNotIn("三者 `pulled=false`", self.doc,
                         "文档仍断言三者均未拉取，与 protocol/decision_layer.json 不符")

    def test_real_run_reflected_in_doc(self):
        runs = [c for c in (self.spec.get("candidates") or [])
                if (c.get("local") or {}).get("real_run")]
        if not runs:
            self.skipTest("机读真源无 real_run 记录（本判据无从对账）")
        self.assertIn("docs_audit-61", self.doc,
                      "机读真源有真跑记录，文档须指出证据件")
        self.assertNotIn("本机未跑通任何真实模型", self.doc,
                         "文档仍称未跑通任何真实模型，与真源 real_run 不符")

    def test_every_candidate_named_and_pulled_state_consistent(self):
        ids = [c.get("id") for c in (self.spec.get("candidates") or [])]
        self.assertTrue(ids)
        for cid in ids:
            self.assertIn(cid, self.doc, "文档缺候选 %s" % cid)
        not_pulled = [c.get("id") for c in self.spec.get("candidates") or []
                      if not c.get("pulled")]
        pulled = [c.get("id") for c in self.spec.get("candidates") or [] if c.get("pulled")]
        self.assertTrue(not_pulled or pulled)
        # 文档必须对「未拉取」与「已拉取」分述——不允许用一句统一断言盖过状态差异。
        if pulled and not_pulled:
            self.assertIn("pulled=false", self.doc)


class TestServeEntryNeedsNoSnapshot(unittest.TestCase):
    """「nf serve 默认实时仓库面，无需快照」这条上架红线必须在机器面与人读面都成立。"""

    def test_driver_binding_has_no_snapshot_requirement(self):
        bind = json.loads(_read("protocol/driver.json"))["bindings"]
        self.assertNotIn("快照", bind["mcp.server"],
                         "protocol/driver.json 的 MCP 入口仍要求快照（默认面应无需快照）")
        self.assertIn("无需快照", bind["setup"])

    def test_docs_state_snapshot_is_optional(self):
        mcp_doc = _read("docs/mcp.md")
        self.assertIn("**默认接入不需要这一步**", mcp_doc)
        skill = _read("skills/ninfenz/SKILL.md")
        self.assertIn("无需快照", skill)
        refs = _read("skills/ninfenz/references/commands.md")
        self.assertIn("无需快照", refs)

    def test_documented_serve_form_exists_in_cli(self):
        src = _read("scripts/nf.py")
        self.assertIn('add_parser("serve"', src,
                      "文档里的 nf serve 必须是对得上的 CLI 子命令")


STATUS_REL = "results/interop-thirdparty-status.md"
_BT = chr(96)


def _status_faces():
    """他证回填表里在册的 face id 集合（从状态表行首列反解）。"""
    faces = set()
    for line in _read(STATUS_REL).splitlines():
        if line.startswith("| " + _BT):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if cells:
                faces.add(cells[0].strip(_BT))
    return faces


def stale_row_refs(text, faces):
    """文档里指向回填表**具体某一行**的引用中，指向不在册 face 的 → 列表。

    为什么需要：文档很容易写下「装载结果回填到 results/interop-thirdparty-status.md 的
    lsp 行」这样的承诺——而那一行**根本不存在**（本仓实际发生过：编辑器面上一波就写了这句，
    而 interop 他证卡的 lsp 面因需同步 .NET 线 golden 一直没补）。指向不存在的行 = 无法履行
    的承诺，读者照着做会发现无行可填。
    """
    nl = "[^" + chr(10) + "]*?"
    path = _BT + re.escape(STATUS_REL) + _BT
    tok = _BT + "([a-zA-Z0-9_-]+)" + _BT + r"\s*(?:行|row)"
    # 两种语序都要看住：路径在前（中文习惯）与行号在前（英文习惯）。
    after = re.compile(path + nl + tok)
    before = re.compile(_BT + "([a-zA-Z0-9_-]+)" + _BT + r"\s*(?:行|row)" + nl + path)
    out = []
    for rx in (after, before):
        for m in rx.finditer(text):
            if m.group(1) not in faces:
                out.append(m.group(1))
    return out


class TestInteropRowReferences(unittest.TestCase):
    """文档不得指向他证回填表里不存在的行。"""

    def test_core_logic_catches_missing_row(self):
        faces = {"mcp", "ccv3"}
        path = _BT + STATUS_REL + _BT
        self.assertEqual(["lsp"], stale_row_refs(
            "结果回填到 " + path + " 的 " + _BT + "lsp" + _BT + " 行。", faces))
        self.assertEqual(["nope"], stale_row_refs(
            "Backfill the result into the " + _BT + "nope" + _BT + " row of " + path + ".", faces))
        self.assertEqual([], stale_row_refs(
            "结果回填到 " + path + " 的 " + _BT + "mcp" + _BT + " 行。", faces))

    def test_repo_docs_point_only_at_existing_rows(self):
        faces = _status_faces()
        self.assertGreaterEqual(len(faces), 10, "回填表在册 face 过少（判据可能已失效）")
        bad = []
        for rel in sorted((ROOT / "docs").rglob("*.md")):
            text = rel.read_text(encoding="utf-8")
            for fid in stale_row_refs(text, faces):
                bad.append("%s → %s" % (rel.relative_to(ROOT).as_posix(), fid))
        self.assertEqual([], bad, "文档指向了他证回填表里不存在的行")


#: 仓库相对路径候选（与 test_site_face 的扫描口径同一套：含扩展名，URL 片段不取）
_REPO_PATH = re.compile(r"(?<![\w./-])([\w][\w.-]*(?:/[\w][\w.-]*)*"
                        r"\.(?:md|py|sh|json|cff|toml|yaml|yml|txt))")


#: 仓库根下的顶层目录（动态取自盘上——不写死清单，避免清单自身漂移）
def _top_dirs():
    return {p.name for p in ROOT.iterdir() if p.is_dir() and not p.name.startswith(".")}


def llms_path_gaps(text, exist=None):
    """llms.txt 里以仓库根相对路径形态点名的件，哪些不在盘上。

    为什么需要（审计 G3 的另一半）：根 llms.txt 是**仓库侧权威机器入口**，agent 会照着它直取
    原文；此前只有「生成区数字 + 固定锚点」受判（check34/check38），**路径承诺无人核**——改名
    或挪件之后机器入口会指向不存在的路径而门禁全绿（本仓刚经历过全局改名）。
    只认「含 / 且首段是仓库顶层目录」的 token：page.md（llms.txt v2 约定名）与 mcp.json
    （生成产物名）这类概念/占位名不是路径承诺，不参与。
    """
    tops = _top_dirs()
    checker = exist or (lambda rel: (ROOT / rel).is_file() or (ROOT / rel).is_dir())
    gaps = []
    for m in _REPO_PATH.finditer(text):
        tok = m.group(1)
        if "/" not in tok or tok.split("/")[0] not in tops:
            continue
        if not checker(tok):
            gaps.append(tok)
    return gaps


class TestLlmsEntryPointPromises(unittest.TestCase):
    """仓库机器入口（llms.txt）点名的仓库路径必须真在场。"""

    def test_core_logic_catches_missing_path(self):
        self.assertEqual(["docs/gone.md"], llms_path_gaps(
            "见 docs/gone.md 与 page.md 与 mcp.json", exist=lambda rel: False))
        self.assertEqual([], llms_path_gaps(
            "见 docs/locales.md", exist=lambda rel: True))

    def test_repo_entry_point_paths_exist(self):
        text = _read("llms.txt")
        scanned = [m.group(1) for m in _REPO_PATH.finditer(text)
                   if "/" in m.group(1) and m.group(1).split("/")[0] in _top_dirs()]
        self.assertGreaterEqual(len(scanned), 30, "没扫到仓库路径（判据可能已失效）")
        self.assertEqual([], llms_path_gaps(text),
                         "llms.txt 点名的仓库路径不在场（修复指引：改路径或补件）")


_BT_TOKEN = re.compile(chr(96) + "([a-z][a-z0-9_]+)" + chr(96))


def driver_header_claims(text):
    """指令档头部 DRIVER OVERRIDE 块里声明的（工具集, 块全文）；无块返回 None。

    只取**连续的行首引用块**：正文里后来再提工具名不算声明（实测 assemble 档正文第 12 行也会提
    内容工具，扫全文就会把声明面撑大、判据变松）。
    """
    lines = text.splitlines()
    start = next((i for i, ln in enumerate(lines) if "DRIVER OVERRIDE" in ln), None)
    if start is None:
        return None
    block = []
    for ln in lines[start:]:
        if not ln.lstrip().startswith(">"):
            break
        block.append(ln)
    tools = set()
    for ln in block:
        if "工具" in ln:                      # 提示与工具可能同一行：只取「工具」之后的段
            _head, _sep, tail = ln.partition("工具")
            tools |= {m.group(1) for m in _BT_TOKEN.finditer(tail)}
    return tools, "\n".join(block)


class TestDriverHeaderReconciles(unittest.TestCase):
    """指令档头部的 override 声明必须与 protocol/driver.json 的工作流映射逐名一致。

    为什么需要：driver.scan 判「机器面引用的工具在运行时存在」「头部有声明块」「有 fail-closed
    关键词」，但**不判头部声明的工具集是否等于该工作流映射的工具集**——driver.json 加了工具而
    头部没跟（或反之），执行者会照头部少走一条路，门禁无感。头部是 agent 真正读的那一行。
    """

    def test_extractor_takes_only_the_block(self):
        bt = chr(96)
        text = ("> **DRIVER OVERRIDE**：工作流 x\n> - 工具 " + bt + "a_tool" + bt + " / "
                + bt + "b_tool" + bt + "\n> - 提示 " + bt + "p_one" + bt
                + "\n\n正文又说工具 " + bt + "c_tool" + bt + "。")
        claims = driver_header_claims(text)
        self.assertEqual({"a_tool", "b_tool"}, claims[0])
        self.assertIn("p_one", claims[1])
        self.assertNotIn("c_tool", claims[1])
        self.assertIsNone(driver_header_claims("没有声明块"))

    def test_headers_match_machine_truth(self):
        doc = json.loads(_read("protocol/driver.json"))
        checked = 0
        for item in doc["documents"]:
            rel, wf_name = item["path"], item["workflow"]
            wf = (doc.get("workflows") or {}).get(wf_name) or {}
            claims = driver_header_claims(_read(rel))
            self.assertIsNotNone(claims, "%s 缺 DRIVER OVERRIDE 块" % rel)
            tools, block = claims
            self.assertEqual(set(wf.get("mcp_tools") or []), tools,
                             "%s 头部声明的工具集与 driver.json 的 %s 不一致" % (rel, wf_name))
            prompt = str(wf.get("mcp_prompt") or "")
            if prompt:
                self.assertIn(prompt, block, "%s 头部缺提示声明 %s" % (rel, prompt))
            checked += 1
        self.assertGreaterEqual(checked, 3, "指令档过少（判据可能空转）")


class TestSkillCommandFace(unittest.TestCase):
    """Agent Skill（skills/**）里当命令写的 nf 子命令必须真在 CLI 注册表里。

    为什么需要：prose_lint.command_face 的扫描面是 FACE_DOCS + docs/*.md——**不含 skills/**；
    而 skills/ninfenz 正是给外部 agent 的装载面（它列了 13 个子命令）。命令改名后技能文档会指向
    死命令，而门禁全绿。
    为什么不在 command_face 里扩扫描面：那会改它的 stats（文档数/命令数），而 .NET 线金标
    real_command_face.digest32 正好钉着那行摘要——本机无 .NET SDK 与金标快照，改不动。故本判据
    落在常驻套件里，抽取复用 command_face 的同一批函数（不另写正则）。
    """

    def test_extraction_reuses_command_face_rule(self):
        from core import prose_lint as pl
        bt = chr(96)
        snippet = "跑 " + bt + "nf market --list" + bt + " 即可"
        found = [m.group(1) for sn in pl._command_snippets(snippet)
                 for m in pl._NF_CALL.finditer(sn)]
        self.assertEqual(["market"], found)

    def test_skill_commands_are_registered(self):
        from core import prose_lint as pl
        cmds = pl.cli_commands(str(ROOT))
        self.assertTrue(cmds, "CLI 注册表读不到（判据无从生效）")
        bad, checked = [], 0
        for path in sorted((ROOT / "skills").rglob("*.md")):
            text = path.read_text(encoding="utf-8")
            for snip in pl._command_snippets(text):
                for m in pl._NF_CALL.finditer(snip):
                    checked += 1
                    if m.group(1) not in cmds:
                        bad.append("%s → nf %s" % (path.relative_to(ROOT).as_posix(),
                                                   m.group(1)))
        self.assertGreaterEqual(checked, 10, "没扫到技能面命令（判据可能已失效）")
        self.assertEqual([], bad, "技能文档写了不存在的 nf 子命令（修复指引：核对 CLI 注册表）")


if __name__ == "__main__":
    unittest.main()
