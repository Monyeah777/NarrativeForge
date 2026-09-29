#!/usr/bin/env python3
"""ISA v1 C1′（同一 module id 不得由两块同时提供，撞号即 DENY）探针。

为什么单开一面：C1′ 的判据在引擎库里已有（`Combinator.Build(..., strictCoherence)`）并在自检里钉过，
但它此前**没有对外开关**——外部调用方没法把它当成门来用。本探针钉四件事：
  ① 撞号语料 · 默认模式：与 Python 同口径（`legal=true`，静默塌陷到后到者），且证书**形状不变**
  ② 撞号语料 · `--strict-coherence`：判 DENY（exit 1 · `legal=false` · 列出冲突与真实归属）
  ③ 干净语料：严格模式输出与默认模式**逐字节相同**（"只在撞号时才扩展证书形状"这句声明为真）
  ④ MCP 面：`nf_combine_plan` 的 `strict_coherence` 入参同样生效

用法：
    python probes/strict_coherence_probe.py --snapshot <隔离快照> --cli <nf-dotnet>

退出码：0 全过；1 有未达项。
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

PACK_A, PACK_B = "相干A包", "相干B包"
DUP_ID = "DUP:M01"


def write_pack(root: Path, pack: str, layer_key: str, layer_code: str) -> None:
    d = root / "community" / pack
    (d / "modules").mkdir(parents=True, exist_ok=True)
    (d / "protocol.yaml").write_text(
        "# 合成撞号包（严格相干探针）\n"
        "protocol:\n"
        "  schema_version: \"2\"\n"
        "package:\n"
        "  conformance: \"L2\"\n"
        "  id: %s\n"
        "  name: %s\n"
        "  version: \"1.0.0\"\n"
        "  module_id_range:\n"
        "    - \"%s\"\n"
        "  categories:\n"
        "    - 相干探针\n"
        "  dependencies:\n"
        "    core_only: true\n"
        "    core_modules: [M00]\n"
        "    cross_package: []\n"
        "  references: []\n"
        "  modules:\n"
        "    - id: \"%s\"\n"
        "      desc: 撞号探针合成模块（%s）\n"
        "  assets:\n"
        "    count: 0\n"
        "  mount_layers:\n"
        "    %s: {default: [%s], available: []}\n"
        % (pack, pack, DUP_ID, DUP_ID, pack, layer_key, DUP_ID),
        encoding="utf-8", newline="\n")
    (d / "modules" / (DUP_ID.replace(":", "_") + ".md")).write_text(
        "# 模块 %s · 撞号探针（%s）\n\n"
        "> 类别：相干探针｜来源：社区（合成）｜挂载点：%s（active，default）｜依赖：无｜状态：active\n\n"
        "```yaml\n"
        "machine_contract:\n"
        "  conformance: \"L2\"\n"
        "  schema: \"1\"\n"
        "  id: %s\n"
        "  name: 撞号探针\n"
        "  category: 相干探针\n"
        "  layer: %s\n"
        "  inputs: []\n"
        "  outputs: [probe_out]\n"
        "  events:\n"
        "    publish: []\n"
        "    subscribe: []\n"
        "  interfaces: []\n"
        "```\n"
        % (DUP_ID, pack, layer_key, DUP_ID, layer_code),
        encoding="utf-8", newline="\n")


def run(cmd: list[str], cwd: Path) -> tuple[int, str]:
    p = subprocess.run(cmd, cwd=str(cwd), capture_output=True)
    return p.returncode, p.stdout.decode("utf-8", "replace")


def mcp_call(cli: str, root: Path, arguments: dict) -> dict:
    """一次会话内 initialize + tools/call（communicate 并发读写，避免管道死锁）。"""
    msgs = [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/call",
         "params": {"name": "nf_combine_plan", "arguments": arguments}},
    ]
    payload = "\n".join(json.dumps(m, ensure_ascii=False) for m in msgs) + "\n"
    proc = subprocess.Popen([cli, "--root", str(root), "serve"],
                            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, _ = proc.communicate(input=payload.encode("utf-8"), timeout=300)
    for line in out.decode("utf-8", "replace").splitlines():
        if not line.strip():
            continue
        msg = json.loads(line)
        if msg.get("id") == 2:
            return msg
    raise SystemExit("MCP 无 id=2 响应")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--snapshot", required=True)
    ap.add_argument("--cli", required=True)
    ap.add_argument("--keep", action="store_true")
    args = ap.parse_args()

    snap = Path(args.snapshot).resolve()
    work = snap.parent / (snap.name + "-coherence")
    if work.exists():
        shutil.rmtree(work)
    shutil.copytree(snap, work)
    print("样板快照：%s\n探针副本：%s\n" % (snap, work))
    write_pack(work, PACK_A, "P40 行为决策", "P40")
    write_pack(work, PACK_B, "P60 长期演变", "P60")
    packs = "%s,%s" % (PACK_A, PACK_B)

    checks: list[tuple[str, bool, str]] = []

    # ① 默认模式：与 Python 同口径（合法 + 静默塌陷），且证书形状不含相干键
    rc_d, out_d = run([args.cli, "--root", str(work), "combine", "plan", "--packs", packs, "--json"], work)
    cert_d = json.loads(out_d)
    layers = cert_d.get("layer_stacks", [])
    where = [row.get("layer") for row in layers if DUP_ID in (row.get("modules") or [])]
    collapsed_to_b = where == ["P60"]
    checks.append(("① 撞号 · 默认模式与 Python 同口径判合法", rc_d == 0 and cert_d.get("legal") is True,
                   "exit=%d legal=%s" % (rc_d, cert_d.get("legal"))))
    checks.append(("① 撞号 · 默认模式证书形状不变（无 coherence_* 键）",
                   "coherence_conflicts" not in cert_d and "coherence_mode" not in cert_d,
                   "keys=%s" % ("含相干键" if "coherence_conflicts" in cert_d else "无相干键")))
    checks.append(("① 撞号 · 塌陷到后到包（层位 P60 = 相干B包）", collapsed_to_b,
                   "落在 %s" % (where or ["（无）"])))

    # ② 严格模式：判 DENY + 列出冲突与真实归属
    rc_s, out_s = run([args.cli, "--root", str(work), "combine", "plan", "--packs", packs,
                       "--strict-coherence", "--json"], work)
    cert_s = json.loads(out_s)
    conflicts = cert_s.get("coherence_conflicts") or []
    first = conflicts[0] if conflicts else {}
    strict_ok = (rc_s == 1 and cert_s.get("legal") is False and cert_s.get("coherence_mode") == "strict"
                 and conflicts and first.get("resolved_pack") != first.get("pack"))
    checks.append(("② 撞号 · 严格相干模式判 DENY（exit 1 · legal=false · 冲突非空）", bool(strict_ok),
                   "exit=%d legal=%s conflicts=%d mode=%s" % (rc_s, cert_s.get("legal"), len(conflicts),
                                                              cert_s.get("coherence_mode"))))
    if conflicts:
        print("     冲突详情：包 %s 声明的 %s 实际解析到包 %s"
              % (first.get("pack"), first.get("module"), first.get("resolved_pack")))

    # ③ 干净语料：严格模式与默认模式输出逐字节相同
    rc_c1, out_c1 = run([args.cli, "--root", str(snap), "combine", "plan", "--packs", "AI农业域包", "--json"], snap)
    rc_c2, out_c2 = run([args.cli, "--root", str(snap), "combine", "plan", "--packs", "AI农业域包",
                         "--strict-coherence", "--json"], snap)
    checks.append(("③ 干净语料 · 严格模式输出与默认逐字节相同",
                   rc_c1 == rc_c2 and out_c1 == out_c2 and len(out_c1) > 0,
                   "exit %d/%d · 字节 %d/%d" % (rc_c1, rc_c2, len(out_c1.encode()), len(out_c2.encode()))))

    # ④ MCP 面：参数同样生效
    try:
        msg_d = mcp_call(args.cli, work, {"packs": [PACK_A, PACK_B]})
        msg_s = mcp_call(args.cli, work, {"packs": [PACK_A, PACK_B], "strict_coherence": True})
        txt_d = json.dumps(msg_d, ensure_ascii=False)
        txt_s = json.dumps(msg_s, ensure_ascii=False)
        mcp_ok = ("coherence_conflicts" not in txt_d) and ("coherence_conflicts" in txt_s)
        checks.append(("④ MCP `nf_combine_plan` · strict_coherence 入参生效", mcp_ok,
                       "默认响应 %d 字节 · 严格响应 %d 字节" % (len(txt_d), len(txt_s))))
    except Exception as exc:  # noqa: BLE001 —— 探针要如实报错，不吞
        checks.append(("④ MCP `nf_combine_plan` · strict_coherence 入参生效", False, "异常：%s" % exc))

    print("\n| # | 判定项 | 结果 | 证据 |")
    print("|---|---|---|---|")
    for name, ok, ev in checks:
        print("| | %s | %s | %s |" % (name, "通过" if ok else "**未达**", ev))
    failed = [c for c in checks if not c[1]]
    print("\n结论：%s" % ("全部通过——C1′ 已是可用开关，且不改变干净语料输出" if not failed
                        else "未达 %d 项" % len(failed)))
    if not args.keep:
        shutil.rmtree(work, ignore_errors=True)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
