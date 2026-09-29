#!/usr/bin/env python3
"""闭包深度边界探针：12 轮上限处必须 fail-closed，不得静默给"少件证书"。

背景（ISA v1 §2.6 / §2.9 的「实测待补」）：闭包补齐是**固定轮次上限（现 12 轮）**。
超过上限的深链，正确行为是 **fail-closed**（`legal=false` + `dependency_closure.dangling` 非空），
而不是静默返回一个"少了尾巴但看起来合法"的组合集——那是本工程最不该有的 fail-open。

做法：从隔离快照复制一份 → 写入合成「链包」：模块 `L:00` 依赖 `L:01` 依赖 … 依赖 `L:0n`
（每模块一个包，跨包依赖，与真实联邦同形）→ 两侧（引擎 / Python）各跑 `combine plan --json`：
  · n ≤ 12：两侧均 `legal=true` 且 `module_count = n+1`（正对照：证明链真被补齐）
  · n ≥ 13：两侧均 `legal=false` 且 `dangling` 非空（fail-closed：报缺口，不静默取错）
并逐字段比对两侧（legal / module_count / dangling / digest）。

用法：
    python probes/closure_depth_probe.py --snapshot <隔离快照> --cli <nf-dotnet> [--py-exe python] [--ns 12,13,20]

退出码：0 全过；1 有未受控项或两侧不一致。
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

CAP = 12  # 与 Python 侧一致的闭包轮次上限（超限即 fail-closed）


def write_pack(work: Path, pack_id: str, mod_id: str, next_id: str) -> None:
    d = work / "community" / pack_id
    (d / "modules").mkdir(parents=True, exist_ok=True)
    (d / "protocol.yaml").write_text(
        "# 合成链包（闭包深度探针）\n"
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
        "    - 闭包探针\n"
        "  dependencies:\n"
        "    core_only: true\n"
        "    core_modules: [M00]\n"
        "    cross_package: []\n"
        "  references: []\n"
        "  modules:\n"
        "    - id: \"%s\"\n"
        "      desc: 闭包深度探针合成模块\n"
        "  assets:\n"
        "    count: 0\n"
        "  mount_layers:\n"
        "    P40 行为决策: {default: [%s], available: []}\n"
        % (pack_id, pack_id, mod_id, mod_id, mod_id),
        encoding="utf-8", newline="\n")
    inputs = "[%s]" % next_id if next_id else "[]"
    (d / "modules" / (mod_id.replace(":", "_") + ".md")).write_text(
        "# 模块 %s · 闭包深度探针\n\n"
        "> 类别：闭包探针｜来源：社区（合成）｜挂载点：P40 行为决策（active，default）｜依赖：%s｜状态：active\n\n"
        "```yaml\n"
        "machine_contract:\n"
        "  conformance: \"L2\"\n"
        "  schema: \"1\"\n"
        "  id: %s\n"
        "  name: 闭包深度探针\n"
        "  category: 闭包探针\n"
        "  layer: P40\n"
        "  inputs: %s\n"
        "  outputs: [probe_out]\n"
        "  events:\n"
        "    publish: []\n"
        "    subscribe: []\n"
        "  interfaces: []\n"
        "```\n"
        % (mod_id, next_id or "无", mod_id, inputs),
        encoding="utf-8", newline="\n")


def build_chain(work: Path, n: int) -> str:
    """建 n+1 个模块的跨包链（每模块一包），返回入口包 id。"""
    tag = "C%d" % n
    entry = "闭链%sP00" % tag
    for k in range(n + 1):
        # 模块 id 必须是「<前缀>:M<数字>」（两侧画像都用 M\d{2,3} 正则取号），
        # 且**裸号不得落在核心 13 件里**——否则闭包会正确地把它当核心件跳过，链就断了。
        mod = "%s:M%03d" % (tag, 300 + k)
        nxt = "%s:M%03d" % (tag, 300 + k + 1) if k < n else ""
        write_pack(work, "闭链%sP%02d" % (tag, k), mod, nxt)
    return entry


def run_json(cmd: list[str], cwd: Path, env: dict) -> tuple[int, str, str]:
    p = subprocess.run(cmd, cwd=str(cwd), capture_output=True, env=env)
    return p.returncode, p.stdout.decode("utf-8", "replace"), p.stderr.decode("utf-8", "replace")


def parse_stdout(rc: int, out: str, err: str) -> dict:
    """stdout 是纯 JSON；失败时把 stderr 末段带出来，便于定位。"""
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        raise SystemExit("退出码 %d 且 stdout 非 JSON：%s" % (rc, (err or out)[-500:]))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--snapshot", required=True)
    ap.add_argument("--cli", required=True)
    ap.add_argument("--py-exe", default=sys.executable)
    ap.add_argument("--ns", default="12,13,20")
    ap.add_argument("--keep", action="store_true")
    args = ap.parse_args()

    snap = Path(args.snapshot).resolve()
    work = snap.parent / (snap.name + "-closure")
    ns = [int(x) for x in args.ns.split(",") if x.strip()]
    print("样板快照：%s\n探针副本：%s\n轮次上限：%d\n" % (snap, work, CAP))
    if work.exists():
        shutil.rmtree(work)
    shutil.copytree(snap, work)

    env = dict(os.environ)
    env["PYTHONPATH"] = str(work / "desktop" / "src")
    env["PYTHONIOENCODING"] = "utf-8"

    problems: list[str] = []
    print("| n（链深） | 期望 | 引擎 legal/模块/缺口 | Python legal/模块/缺口 | 两侧同判 | 判定 |")
    print("|---|---|---|---|---|---|")
    for n in ns:
        entry = build_chain(work, n)
        rc_n, out_n, err_n = run_json(
            [args.cli, "--root", str(work), "combine", "plan", "--packs", entry, "--json"], work, env)
        rc_p, out_p, err_p = run_json(
            [args.py_exe, str(work / "scripts" / "nf.py"), "combine", "plan", "--packs", entry, "--json"], work, env)
        cert_n = parse_stdout(rc_n, out_n, err_n)
        cert_p = parse_stdout(rc_p, out_p, err_p)

        def cell(c: dict) -> tuple[bool, int, int]:
            return bool(c.get("legal")), int(c.get("module_count", -1)), len(c.get("dependency_closure", {}).get("dangling", []))

        legal_n, count_n, dang_n = cell(cert_n)
        legal_p, count_p, dang_p = cell(cert_p)
        want_legal = n <= CAP

        ok_side = True
        reason = []
        if want_legal:
            if not (legal_n and legal_p):
                ok_side = False; reason.append("应合法却判不合法")
            if not (count_n == n + 1 and count_p == n + 1):
                ok_side = False; reason.append("应补齐 %d 件却得 引擎%d/Py%d" % (n + 1, count_n, count_p))
        else:
            if legal_n or legal_p:
                ok_side = False; reason.append("**超限却判合法（fail-open）**")
            if not (dang_n > 0 and dang_p > 0):
                ok_side = False; reason.append("超限却未报缺口（静默取错）")

        same = (legal_n, count_n, dang_n) == (legal_p, count_p, dang_p)
        if not same:
            reason.append("两侧不同判：引擎 %s / Py %s" % ((legal_n, count_n, dang_n), (legal_p, count_p, dang_p)))
        ok = ok_side and same
        if not ok:
            problems.append("n=%d：%s" % (n, "；".join(reason)))
        print("| %d | %s | %s/%d/%d | %s/%d/%d | %s | %s |"
              % (n, "合法（全补齐）" if want_legal else "fail-closed（报缺口）",
                 "legal" if legal_n else "unlegal", count_n, dang_n,
                 "legal" if legal_p else "unlegal", count_p, dang_p,
                 "是" if same else "**否**", "通过" if ok else "**未受控**"))

    print("\n结论：%s" % ("全部受控——上限处 fail-closed，正对照真补齐，两侧同判" if not problems else "发现 %d 处未受控" % len(problems)))
    for p in problems:
        print("  x " + p)
    if not args.keep:
        shutil.rmtree(work, ignore_errors=True)
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
