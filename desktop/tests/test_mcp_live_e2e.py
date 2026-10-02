# -*- coding: utf-8 -*-
"""MCP 上架面·**真进程**端到端（默认实时仓库面 `nf serve` ↔ 越权/注入拒出面）。

为什么单列一件：`test_mcp_runtime` / `test_trust_boundary` 都在**进程内**驱动 `McpRuntime`，
`test_mcp_read_budget` 数的是打开文件数——**上架入口本身**（`python scripts/nf.py serve`，
缺省 = 实时仓库面、无快照）从未被端到端验证过：外部 MCP 客户端拿到的就是这条通道，它的
握手、只读工具面、拒出语义与帧纪律，只能在真进程上证明。

判据（一条通道，三面）：
  ① **默认路径开**：无参 `nf serve` 的握手/发现/资源/工具/提示面全部应答，且返回的是**真仓库**
     内容（不是空壳、不是需要先产快照）；
  ② **只读工具面冻结**：`tools/list` 恰好是那 10 个只读工具——想加工具就得改本表（新增即评审）；
  ③ **越权/注入硬面**：路径穿越（工具参数 + 资源 uri）/ 超长载荷 / 控制字符 / 写形工具名 /
     Windows 盘符相对（`C:foo`）/ NTFS 备用数据流（`x.md:hidden`）六类试探一律 `-32602`，
     **不泄露**被试探的目标内容，且**会话不崩**（随后一条正常调用照样应答）。
"""
import json
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
NF = str(ROOT / "scripts" / "nf.py")
INVALID_PARAMS = -32602

#: 只读工具面（冻结）：与 `docs/mcp.md` 能力表、`mcp_runtime` 实现一一对应。
READ_TOOLS = {
    "pipeline_ls", "spec_ls", "registry_query", "library_search", "library_read",
    "pattern_read", "knowledge_order", "module_read", "pipeline_read", "asset_get",
}
#: 写形/越权形工具名的形态（出现即说明只读白名单被破了口子）。
#: 只挑**不会误伤**的词根——`set_` 会命中 `asset_get`、`run` 会命中 `runtime`，一律不收。
WRITE_SHAPED = re.compile(r"write|delete|remove|exec|shell|upload|patch|create|mkdir", re.I)


def _serve(frames) -> tuple:
    """把帧喂给真 CLI 的 stdio 服务 → (返回帧表, 原始 stdout, stderr 文本)。"""
    payload = "\n".join(json.dumps(f, ensure_ascii=False) for f in frames) + "\n"
    p = subprocess.run([sys.executable, NF, "serve"], cwd=str(ROOT),
                       input=payload.encode("utf-8"), capture_output=True, timeout=300)
    out_raw = p.stdout.decode("utf-8", "replace")
    err = p.stderr.decode("utf-8", "replace")
    msgs = [json.loads(ln) for ln in out_raw.splitlines() if ln.strip()]
    return msgs, out_raw, err


def _req(mid, method, params=None):
    msg = {"jsonrpc": "2.0", "id": mid, "method": method}
    if params is not None:
        msg["params"] = params
    return msg


def _init(mid=1):
    return _req(mid, "initialize", {"protocolVersion": "2025-11-25", "capabilities": {},
                                    "clientInfo": {"name": "e2e", "version": "0"}})


def _by_id(msgs):
    return {m["id"]: m for m in msgs if "id" in m}


class McpLiveFaceTest(unittest.TestCase):
    def test_default_path_serves_real_repo_without_snapshot(self):
        """① 无参 `nf serve` 直起实时仓库面：握手 + 发现 + 资源 + 提示面齐备。"""
        msgs, out_raw, err = _serve([
            _init(), _req(2, "resources/list"), _req(3, "resources/templates/list"),
            _req(4, "prompts/list"), _req(5, "server/discover"),
        ])
        got = _by_id(msgs)
        self.assertEqual("2025-11-25", got[1]["result"]["protocolVersion"])
        self.assertEqual("nf-repo-live", got[1]["result"]["serverInfo"]["name"])
        versions = got[5]["result"]["supportedVersions"]
        self.assertIn("2025-11-25", versions)
        self.assertIn("2026-07-28", versions)          # dual-era（与 docs/mcp.md 同口径）
        res = got[2]["result"]["resources"]
        self.assertTrue(res)
        self.assertTrue(all(r["uri"].startswith("nf://") for r in res), res[:2])
        self.assertTrue(got[3]["result"]["resourceTemplates"])
        self.assertTrue(got[4]["result"]["prompts"])
        # 帧纪律：stdout 只有 JSON-RPC 行；横幅走 stderr
        self.assertEqual(len(msgs), 5)
        self.assertNotIn("nf serve", out_raw)
        self.assertIn("nf serve", err)

    def test_tools_list_is_the_frozen_read_only_surface(self):
        """② 只读工具面冻结：多一个工具就红（新增写路径必须评审）。"""
        msgs, _, _ = _serve([_init(), _req(2, "tools/list")])
        names = {t["name"] for t in _by_id(msgs)[2]["result"]["tools"]}
        self.assertEqual(READ_TOOLS, names, "只读工具面漂移（新增工具须评审并更新本表）")
        self.assertFalse([n for n in names if WRITE_SHAPED.search(n)], sorted(names))

    def test_declared_inputschema_is_enforced_on_the_published_face(self):
        """声明面校验必须**真的接线**（依赖倒置的注入点在 CLI）：拼错键 / 类型不符 → `-32602`。

        为什么单列：校验器由 CLI 注入（`McpRuntime(schema_check=…)`），若哪天忘了注入，工具面
        会**静默**回到「未知键被忽略、返回未过滤结果」——本判据在**真进程**上把这条接线钉住。
        """
        msgs, _, _ = _serve([
            _init(),
            _req(2, "tools/call", {"name": "registry_query", "arguments": {"quer": "M90"}}),
            _req(3, "tools/call", {"name": "registry_query", "arguments": {"query": 123}}),
            _req(4, "tools/call", {"name": "registry_query", "arguments": {"query": "M90"}}),
        ])
        got = _by_id(msgs)
        for mid in (2, 3):
            self.assertEqual(INVALID_PARAMS, got[mid]["error"]["code"], got[mid])
            self.assertIn("inputSchema", got[mid]["error"]["message"])
        self.assertIn("M90", got[4]["result"]["content"][0]["text"])

    def test_authorised_read_call_returns_repo_content(self):
        """① 续：白名单内的调用必须真读到仓库内容（拒出面之外还有正常面）。"""
        msgs, _, _ = _serve([
            _init(),
            _req(2, "tools/call", {"name": "registry_query", "arguments": {"query": "M90"}}),
            _req(3, "resources/read", {"uri": "nf://repo/module/M90"}),
        ])
        got = _by_id(msgs)
        text = got[2]["result"]["content"][0]["text"]
        self.assertIn("M90", text)
        self.assertTrue(got[3]["result"]["contents"][0]["text"])

    def test_adversarial_frames_refused_without_leak_and_session_survives(self):
        """③ 越权/注入硬面：六类试探 → 一律 -32602；不泄露；随后正常调用照样应答。"""
        msgs, out_raw, _ = _serve([
            _init(),
            _req(2, "tools/call", {"name": "asset_get",
                                   "arguments": {"key": "../../../etc/passwd"}}),
            _req(3, "resources/read", {"uri": "nf://repo/../../../etc/passwd"}),
            _req(4, "tools/call", {"name": "registry_query",
                                   "arguments": {"query": "x" * 10000}}),
            _req(5, "tools/call", {"name": "registry_query",
                                   "arguments": {"query": "M90\x07"}}),
            _req(6, "tools/call", {"name": "write_file", "arguments": {"path": "x"}}),
            _req(7, "tools/call", {"name": "module_read",
                                   "arguments": {"module_id": "C:secrets.txt"}}),
            _req(8, "tools/call", {"name": "module_read",
                                   "arguments": {"module_id": "M90.md:hidden"}}),
            _req(9, "tools/call", {"name": "registry_query", "arguments": {"query": "M90"}}),
        ])
        got = _by_id(msgs)
        for mid in (2, 3, 4, 5, 6, 7, 8):
            self.assertEqual(INVALID_PARAMS, got[mid]["error"]["code"], got[mid])
        self.assertIn("修复指引", got[2]["error"]["message"])
        # 不泄露：试图外带的那个目标，内容一个字都不许出现在回包里
        self.assertNotIn("root:", out_raw)
        self.assertNotIn("/etc/passwd\"", out_raw)
        # 会话不崩：拒了 7 帧之后，最后那一帧正常应答
        self.assertIn("M90", got[9]["result"]["content"][0]["text"])


if __name__ == "__main__":
    unittest.main()
