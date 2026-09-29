#!/usr/bin/env python3
"""MCP 工具面完整性探针：逐个调用**全部工具**，断言每个都能给出结果。

为什么单开一面：MCP 工具级对账只覆盖了**与 Python 同名**的那 10 个；本引擎另有的
12 个判据工具（`nf_*`）从未被系统性调用过——「写出来了」不等于「调得通」。
本探针把 22 个工具全打一遍，记录响应字节数与失败原因。

用法：
    python probes/mcp_surface_probe.py --cli <nf-dotnet> --root <仓库或快照>

退出码：0 全部工具可调用；1 有工具失败。
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys

#: 工具 → 最小合法参数（缺省 {}）
ARGS = {
    "nf_combine_plan": {"packs": ["AI农业域包"]},
    "nf_patterns_for": {"target": "protocol/RECEIPTS.json"},
    "nf_interop": {"kind": "intoto"},
    "nf_st_validate": {"path": "docs/examples/st-validate/fixture_card_v2_clean.json"},
    "registry_query": {"query": "M08"},
    "library_read": {"entry_id": "NF-1"},
    "pattern_read": {"pattern_id": "single-source-truth"},
    "module_read": {"module_id": "M08"},
    "pipeline_read": {"pipeline": "P01"},
    "library_search": {"query": "叙事"},
    "knowledge_order": {},
    "asset_get": {"key": "QUANT_METRICS"},
}


def call(proc, messages):
    """一次会话内顺序发多条请求（communicate 并发读写，避免管道死锁）。"""
    payload = "\n".join(json.dumps(m, ensure_ascii=False) for m in messages) + "\n"
    out, err = proc.communicate(input=payload.encode("utf-8"), timeout=300)
    return out.decode("utf-8", "replace"), err.decode("utf-8", "replace")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cli", required=True)
    ap.add_argument("--root", required=True)
    args = ap.parse_args()

    init = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
    ls = {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}
    proc = subprocess.Popen([args.cli, "--root", args.root, "serve"],
                            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, _err = call(proc, [init, ls])
    lines = [l for l in out.splitlines() if l.strip()]
    if len(lines) < 2:
        print("  ✗ 初始化或 tools/list 无响应：%r" % out[:200])
        return 1
    tools = json.loads(lines[1])["result"]["tools"]
    names = [t["name"] for t in tools]
    print("工具面：%d 个（%s…）" % (len(names), "、".join(names[:3])))

    # 逐个调用（同一会话内顺次发，避免进程启动开销）
    messages = [{"jsonrpc": "2.0", "id": 100 + i, "method": "tools/call",
                 "params": {"name": name, "arguments": ARGS.get(name, {})}}
                for i, name in enumerate(names)]
    proc = subprocess.Popen([args.cli, "--root", args.root, "serve"],
                            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = call(proc, [init] + messages)
    responses = {}
    for line in [l for l in out.splitlines() if l.strip()]:
        try:
            msg = json.loads(line)
        except ValueError:
            continue
        if isinstance(msg, dict) and isinstance(msg.get("id"), int) and msg["id"] >= 100:
            responses[msg["id"] - 100] = msg

    failed = []
    for i, name in enumerate(names):
        msg = responses.get(i)
        if msg is None:
            failed.append((name, "无响应"))
            print("  FAIL %-20s 无响应" % name)
            continue
        if "error" in msg:
            failed.append((name, "错误 %s" % msg["error"].get("code")))
            print("  FAIL %-20s error=%s %s" % (name, msg["error"].get("code"),
                                                str(msg["error"].get("message"))[:60]))
            continue
        text = ""
        try:
            text = msg["result"]["content"][0]["text"]
        except (KeyError, IndexError, TypeError):
            pass
        if not text:
            failed.append((name, "结果无正文"))
            print("  FAIL %-20s 结果无 content[0].text" % name)
            continue
        print("  OK   %-20s %6d 字节" % (name, len(text.encode("utf-8"))))

    print("\nMCP 工具面：%d 个 · 可调用 %d · 失败 %d（exit=%d）"
          % (len(names), len(names) - len(failed), len(failed), proc.returncode))
    if err.strip():
        print("  stderr: %s" % err.strip().splitlines()[-1][:160])

    # 错误参数面：空参数 / 错类型参数 —— 只许受控错误（-32602/-32603）或正常结果，不许崩
    bad = [{"jsonrpc": "2.0", "id": 300 + i, "method": "tools/call",
            "params": {"name": name, "arguments": {}}} for i, name in enumerate(names)]
    typo = [{"jsonrpc": "2.0", "id": 400 + i, "method": "tools/call",
             "params": {"name": name, "arguments": {"__bogus__": {"x": [1, 2]}}}} for i, name in enumerate(names)]
    proc = subprocess.Popen([args.cli, "--root", args.root, "serve"],
                            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = call(proc, [init] + bad + typo)
    seen = {}
    for line in [l for l in out.splitlines() if l.strip()]:
        try:
            msg = json.loads(line)
        except ValueError:
            continue
        if isinstance(msg, dict) and isinstance(msg.get("id"), int) and msg["id"] >= 300:
            seen[msg["id"]] = msg

    controlled = 0
    uncovelled = []
    for i, name in enumerate(names):
        for base, kind in ((300, "空参数"), (400, "未知参数")):
            msg = seen.get(base + i)
            if msg is None:
                uncovelled.append((name, kind, "无响应"))
                continue
            if "error" in msg:
                code = msg["error"].get("code")
                if code in (-32602, -32603, -32600):
                    controlled += 1
                else:
                    uncovelled.append((name, kind, "非受控错误码 %s" % code))
            else:
                controlled += 1          # 宽容接受未知参数也算受控
    print("错误参数面：%d 次调用 · 受控 %d · 异常 %d"
          % (len(names) * 2, controlled, len(uncovelled)))
    for name, kind, why in uncovelled[:8]:
        print("  [异常] %-20s %s：%s" % (name, kind, why))

    # 工具内部抛异常：JSON-RPC 2.0 §5 要求**错误响应回带请求 id**（否则调用方按 id 匹配时"看不到"这次失败）。
    # 这里用一个必然抛异常的工具调用（不存在的路径）验证：既不许沉默，也不许丢 id。
    boom = [{"jsonrpc": "2.0", "id": 500, "method": "tools/call",
             "params": {"name": "nf_st_validate", "arguments": {"path": "no/such/card.json"}}},
            {"jsonrpc": "2.0", "id": 501, "method": "ping"}]
    proc = subprocess.Popen([args.cli, "--root", args.root, "serve"],
                            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, _err = call(proc, [init] + boom)
    err_id_ok = False
    code_ok = False
    for line in [l for l in out.splitlines() if l.strip()]:
        try:
            msg = json.loads(line)
        except ValueError:
            continue
        if isinstance(msg, dict) and msg.get("id") == 500:
            err_id_ok = "error" in msg
            code_ok = (msg.get("error") or {}).get("code") == -32603
    alive = any('"id":501' in l or '"id": 501' in l for l in out.splitlines())
    print("工具异常面：错误响应回带 id=%s · 受控码 -32603=%s · 循环未杀（ping 有应答）=%s"
          % (err_id_ok, code_ok, alive))
    if not (err_id_ok and code_ok and alive):
        uncovelled.append(("nf_st_validate", "工具异常面", "id 未回带或未受控"))

    return 1 if (failed or uncovelled) else 0


if __name__ == "__main__":
    raise SystemExit(main())
