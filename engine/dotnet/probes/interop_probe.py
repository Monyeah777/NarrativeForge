#!/usr/bin/env python3
"""互操作导出面探针：两个独立判据 + 一条"不许给半个面"的纪律断言。

判据一（**在盘 pin 复现**）：已移植形状 `--out` 落下的字节须与仓内 `results/interop/<kind>.json`
**逐字节相同**——这正是 check33 对入仓导出面的断言，本探针把它在引擎侧独立复现。
判据二（**不许给半个面**）：未移植形状必须**明确拒绝**（非零退出 + 可读理由），
`--check` / `--all` 在全量移植前同样明确拒绝——不得静默返回空面或半面。

用法：
    python probes/interop_probe.py --root <快照> --cli <nf-dotnet> [--tmp <目录>]

退出码：0 全过；1 有未达项。
"""
from __future__ import annotations

import argparse
import hashlib
import os
import subprocess
import sys

ALL_KINDS = ["openapi", "asyncapi", "intoto", "sbom", "slsa", "a2a", "prov",
             "cyclonedx", "vc", "c2pa", "cid", "decisions"]


def sha256(path: str) -> str:
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--cli", required=True)
    ap.add_argument("--tmp", default=os.environ.get("TEMP", "/tmp"))
    args = ap.parse_args()

    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass

    checks: list[tuple[str, bool, str]] = []

    # 判据一：全部形状 == 在盘 pin（check33 的引擎侧独立复现）
    for kind in ALL_KINDS:
        pin = os.path.join(args.root, "results", "interop", f"{kind}.json")
        tmp = os.path.join(args.tmp, f"nf-interop-{kind}.json")
        proc = subprocess.run([args.cli, "--root", args.root, "interop", "--kind", kind, "--out", tmp],
                              capture_output=True)
        ok = proc.returncode == 0 and os.path.isfile(tmp) and os.path.isfile(pin) and sha256(tmp) == sha256(pin)
        checks.append((f"形状 {kind} · --out 字节 == 在盘 results/interop/{kind}.json",
                       ok, f"exit={proc.returncode} · 字节 {os.path.getsize(tmp) if os.path.isfile(tmp) else 0}"
                           f" / pin {os.path.getsize(pin) if os.path.isfile(pin) else 0}"))

    # 判据二：门禁 --check 必须过（引擎侧独立跑同一套跨真源断言）
    proc = subprocess.run([args.cli, "--root", args.root, "interop", "--check"], capture_output=True)
    out = (proc.stdout or b"").decode("utf-8", "replace").strip()
    checks.append(("interop --check（覆盖完整 + 形状合法 + 确定性）", proc.returncode == 0,
                   f"exit={proc.returncode} · {out[:100] if out else '（无输出）'}"))

    # 判据三：--all 缺省落仓内必须拒绝（仓库写面），显式 --out 才写
    proc_no = subprocess.run([args.cli, "--root", args.root, "interop", "--all"], capture_output=True)
    checks.append(("interop --all 缺省（仓内路径）· 明确拒绝", proc_no.returncode != 0,
                   f"exit={proc_no.returncode}"))
    out_dir = os.path.join(args.tmp, "nf-interop-all")
    proc_all = subprocess.run([args.cli, "--root", args.root, "interop", "--all", "--out", out_dir],
                              capture_output=True)
    written = len([f for f in os.listdir(out_dir) if f.endswith(".json")]) if os.path.isdir(out_dir) else 0
    checks.append(("interop --all --out <目录> · 12 件全写", proc_all.returncode == 0 and written == len(ALL_KINDS),
                   f"exit={proc_all.returncode} · 写出 {written} 件"))

    print("| # | 判定项 | 结果 | 证据 |")
    print("|---|---|---|---|")
    for name, ok, ev in checks:
        print("| | %s | %s | %s |" % (name, "通过" if ok else "**未达**", ev))
    failed = [c for c in checks if not c[1]]
    print("\n结论：%s" % (f"全部通过——{len(ALL_KINDS)}/{len(ALL_KINDS)} 形状逐字节复现 pin，"
                        f"门禁 --check 独立可跑，--all 只在显式 --out 下落盘" if not failed
                        else f"未达 {len(failed)} 项"))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
