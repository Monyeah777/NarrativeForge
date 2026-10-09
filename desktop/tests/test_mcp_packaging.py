# -*- coding: utf-8 -*-
"""MCP 上架材料门禁：声明（机读真源）与投影（docs/mcp.md 人读节）逐项一致。

上架材料最容易漂移的三样是**工具面 / 类目 / 红线**——把这三样钉死：
① `protocol/mcp_package.json` 必须已收口（status=ready、pending 空、命名与一句话定稿）；
② 声明的 tools/prompts 必须与 `mcp_runtime` 运行时面**逐名一致**（多一个少一个即 FAIL）；
③ `docs/mcp.md` 的「上架材料」节必须逐项复述真源（否则人读面会与机读面分叉）。
"""
import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from core import mcp_runtime as mrt  # noqa: E402

DECL = ROOT / "protocol" / "mcp_package.json"
LISTING = ROOT / "docs" / "mcp.md"


class McpPackageDeclarationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = json.loads(DECL.read_text(encoding="utf-8"))
        cls.pkg = cls.doc.get("package") or {}

    def test_declaration_is_finalized(self):
        self.assertEqual("nf-mcp-package/1", self.doc.get("schema"))
        self.assertEqual("ready", self.doc.get("status"),
                         "上架声明仍未收口（status=%s）" % self.doc.get("status"))
        self.assertEqual([], list(self.doc.get("pending") or []),
                         "上架声明仍带待办（pending 非空）")

    def test_naming_and_category_are_final(self):
        self.assertTrue(str(self.pkg.get("name") or "").strip(), "缺定稿名称")
        self.assertTrue(str(self.pkg.get("one_liner") or "").strip(), "缺定稿一句话")
        self.assertIn(self.pkg.get("category"),
                      self.doc.get("category_vocabulary") or [],
                      "类目越词表")
        self.assertTrue(self.doc.get("red_lines"), "红线不得为空")

    def test_declared_surface_matches_runtime(self):
        live_tools = sorted(t["name"] for t in mrt.TOOL_DEFS)
        live_prompts = sorted(p["name"] for p in mrt.PROMPT_DEFS)
        self.assertEqual(live_tools, sorted(self.pkg.get("tools") or []),
                         "声明的工具面与运行时不一致（上架材料会漂移）")
        self.assertEqual(live_prompts, sorted(self.pkg.get("prompts") or []),
                         "声明的提示面与运行时不一致")

    def test_runtime_surface_is_read_only(self):
        """越权面红线：工具名不得出现写路径词汇（只读面 = 天然无写）。"""
        forbidden = ("write", "delete", "remove", "exec", "shell", "put", "post")
        for tool in self.pkg.get("tools") or []:
            self.assertFalse(any(word in tool.lower() for word in forbidden),
                             "工具面出现写路径词汇：%s" % tool)

    def test_prose_tool_counts_match_runtime(self):
        """散文里的「当前 N 工具 + M prompt」若写了数字，就必须与运行时面一致。

        依据（2026-09-30）：上架材料正文与 `docs/mcp.md` 都写着「当前 10 工具 + 1 prompt」——
        工具面一扩，这处数字没有任何判据盯着（工具**名**有判据，**数**没有）。这里把它也接上
        运行时：写了就对得上；哪天不写了，本判据自然失效（无声称即无漂移）。
        """
        live = (len(mrt.TOOL_DEFS), len(mrt.PROMPT_DEFS))
        seen = False
        for label, text in (("protocol/mcp_package.json", DECL.read_text(encoding="utf-8")),
                            ("docs/mcp.md", LISTING.read_text(encoding="utf-8"))):
            m = re.search(r"当前\s*(\d+)\s*工具\s*\+\s*(\d+)\s*prompt", text)
            if not m:
                continue
            seen = True
            self.assertEqual(live, (int(m.group(1)), int(m.group(2))),
                             "%s 的散文计数与运行时面不符（工具 %d / prompt %d）"
                             % (label, live[0], live[1]))
        self.assertTrue(seen, "上架材料与投影件都缺「当前 N 工具 + M prompt」句式"
                              "（修复指引：补回句式，或删掉数字并改成「只读工具面见下」）")

    def test_declared_entry_leads_with_the_zero_snapshot_default(self):
        """默认路径开（作者指令）：上架入口必须写清「无需快照」，且声明字段机读可判。

        依据（2026-09-30 取证）：`nf serve` 早就可以缺省直起实时仓库面，但**上架材料**仍只写
        「`nf run --fmt mcp` → `nf serve <快照>`」——外部客户端照抄就得先备 store、先产快照，
        默认路径等于没开。本判据把「快照不是前置条件」钉在机读真源上（行为面由
        `test_mcp_live_e2e` 的真进程端到端证明）。
        """
        self.assertIs(False, self.pkg.get("snapshot_required"),
                      "上架声明仍把快照写成前置条件")
        self.assertIn("live-repo", str(self.pkg.get("default_surface") or ""),
                      "上架声明缺「缺省 = 实时仓库面」的机读字段")
        self.assertIn("serve", str(self.pkg.get("entry") or ""))


class McpListingProjectionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = json.loads(DECL.read_text(encoding="utf-8"))
        cls.pkg = cls.doc.get("package") or {}
        cls.text = LISTING.read_text(encoding="utf-8")

    def test_listing_section_exists(self):
        self.assertIn("上架材料", self.text, "docs/mcp.md 缺上架材料节")

    def test_listing_mirrors_declaration(self):
        for field in ("name", "one_liner"):
            val = str(self.pkg.get(field) or "")
            self.assertIn(val, self.text, "人读面缺真源字段 %s = %s" % (field, val))
        self.assertIn(str(self.pkg.get("category")), self.text, "人读面缺类目")
        for tool in self.pkg.get("tools") or []:
            self.assertIn(tool, self.text, "人读面缺工具 %s" % tool)
        for prompt in self.pkg.get("prompts") or []:
            self.assertIn(prompt, self.text, "人读面缺 prompt %s" % prompt)

    def test_listing_carries_install_commands(self):
        self.assertIn("nf.py run", self.text)
        self.assertIn("nf.py serve", self.text)
        self.assertIn("mcpServers", self.text)
        self.assertIn("English", self.text, "缺英文安装说明")

    def test_listing_shows_the_bare_serve_form(self):
        """人读投影必须给出**不带快照参数**的 `serve` 写法（默认路径开在同一条口径上）。"""
        self.assertTrue(re.search(r"nf\.py serve\s*(?:#.*)?$", self.text, re.M),
                        "docs/mcp.md 没有「裸 serve」写法——默认路径开在人读面缺失")
        self.assertIn("serve\"]", self.text.replace(" ", ""),
                      "mcpServers 示例仍把快照写成必填参数")

    def test_declaration_points_at_listing_doc(self):
        self.assertEqual("docs/mcp.md", self.pkg.get("listing"),
                         "声明未指向人读投影件")


class McpToolAnnotationsTest(unittest.TestCase):
    """工具注解：只读红线必须**机读可证**（MCP 2025-03-26+ 的 annotations.readOnlyHint）。

    为什么需要（2026-10-08）：`protocol/mcp_package.json` 的红线写着「只读：不新增任何写工具」，
    但那是**散文**；MCP 客户端真正读的是 `tools/list` 里的 `annotations`——没有它，客户端只能对
    每次调用弹窗确认（无法自动放行只读工具），红线在协议层等于不存在。本件把「每个工具都声明只读、
    且该声明真的发布在 tools/list 上」钉住，并用变异负例逆验判据本身能红。
    """

    @staticmethod
    def _offenders(tools):
        return [t["name"] for t in tools
                if (t.get("annotations") or {}).get("readOnlyHint") is not True]

    def test_every_tool_declares_read_only(self):
        self.assertGreaterEqual(len(mrt.TOOL_DEFS), 10, "工具面塌缩（判据可能空转）")
        self.assertEqual([], self._offenders(mrt.TOOL_DEFS),
                         "这些工具没声明 readOnlyHint（修复指引：加 annotations，别只写在散文里）")

    def test_annotation_is_published_on_the_wire(self):
        rt = mrt.McpRuntime({"mcp": {"name": "annot", "version": "0", "resources": []}})
        out = rt.handle({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
        tools = out["result"]["tools"]
        self.assertEqual(len(mrt.TOOL_DEFS), len(tools))
        self.assertEqual([], self._offenders(tools), "注解没出现在 tools/list 上")

    def test_no_tool_claims_to_be_destructive(self):
        bad = [t["name"] for t in mrt.TOOL_DEFS
               if (t.get("annotations") or {}).get("destructiveHint") is True]
        self.assertEqual([], bad, "只读面出现 destructiveHint=true（与红线冲突）")

    def test_check_detects_a_mislabeled_tool(self):
        """变异负例：把某个工具标成非只读 → 助手必须抓到（否则本件空转）。"""
        mutant = [dict(mrt.TOOL_DEFS[0]), dict(mrt.TOOL_DEFS[1])]
        mutant[1]["annotations"] = {"readOnlyHint": False}
        self.assertEqual([mutant[1]["name"]], self._offenders(mutant))
        self.assertEqual([], self._offenders(mrt.TOOL_DEFS))


if __name__ == "__main__":
    unittest.main()
