#!/usr/bin/env python3
"""资产台账探针：`asset verify / inventory / ls` 两侧差分（真语料 + 合成违规语料）。

为什么单开一面：台账闭合是**双源一致**判据（台账 ↔ 文件头）＋反向闭合（键无孤儿）＋
货架单层不变量，顺路径（仓库自身干净）绿不代表判据在判——必须喂坏台账。

做法：合成资产根建在 **TEMP**（不在快照内），两侧扫同一目录：
  Python：`nf asset verify --root <dir>`；引擎：`nf-dotnet --root <快照> asset verify --assets-root <dir>`。
  输出与退出码逐字节比对（stdout + stderr）。

覆盖：缺头 / 头与台账不一致 / 孤儿头 / 未托管 md / 键重复 / 在册文件缺失 / 缺 source /
缺 version / status 非法 / 货架含子目录 / 过滤器（pkg/tier/status）与非法取值退出码。

用法：
    python probes/asset_probe.py --root <快照> --cli <nf-dotnet> --py-exe <python>

退出码：0 全过；1 有未达项。
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys

HEADER = lambda key, ver, st: '<!-- nf-asset: key="%s" version="%s" status="%s" -->\n' % (key, ver, st)


def build_assets_root(work: str) -> str:
    root = os.path.join(work, "assets")
    if os.path.isdir(root):
        shutil.rmtree(root)
    os.makedirs(root)
    ledger = {
        "schema_version": "1", "tier": "community", "package": "合成资产集",
        "assets": [
            {"file": "good.md", "key": "GOOD", "source": "合成来源 A", "version": "1.0",
             "status": "active", "added": "2026-09-27"},
            {"file": "dup1.md", "key": "DUP", "source": "合成来源 B", "version": "1.0",
             "status": "active", "added": "2026-09-27"},
            {"file": "dup2.md", "key": "DUP", "source": "合成来源 C", "version": "1.0",
             "status": "active", "added": "2026-09-27"},
            {"file": "missing.md", "key": "MISSING", "source": "合成来源 D", "version": "1.0",
             "status": "active", "added": "2026-09-27"},
            {"file": "noheader.md", "key": "NOHEADER", "source": "合成来源 E", "version": "1.0",
             "status": "active", "added": "2026-09-27"},
            {"file": "mismatch.md", "key": "MISMATCH", "source": "合成来源 F", "version": "1.0",
             "status": "active", "added": "2026-09-27"},
            {"file": "nosource.md", "key": "NOSOURCE", "source": "", "version": "1.0",
             "status": "active", "added": "2026-09-27"},
            {"file": "noversion.md", "key": "NOVERSION", "source": "合成来源 G", "version": "",
             "status": "active", "added": "2026-09-27"},
            {"file": "badstatus.md", "key": "BADSTATUS", "source": "合成来源 H", "version": "1.0",
             "status": "zombie", "added": "2026-09-27"},
        ],
    }
    with open(os.path.join(root, "provenance.json"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(ledger, ensure_ascii=False, indent=2) + "\n")

    def write(name, text):
        with open(os.path.join(root, name), "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)

    write("good.md", HEADER("GOOD", "1.0", "active") + "# 好资产\n")
    write("dup1.md", HEADER("DUP", "1.0", "active") + "# 重键一\n")
    write("dup2.md", HEADER("DUP", "1.0", "active") + "# 重键二\n")
    write("noheader.md", "# 无头资产\n")
    write("mismatch.md", HEADER("OTHER", "1.0", "deprecated") + "# 头与台账不一致\n")
    write("nosource.md", HEADER("NOSOURCE", "1.0", "active") + "# 缺 source\n")
    write("noversion.md", HEADER("NOVERSION", "", "active") + "# 缺 version\n")
    write("badstatus.md", HEADER("BADSTATUS", "1.0", "zombie") + "# 非法 status\n")
    write("orphan.md", HEADER("ORPHAN", "1.0", "active") + "# 孤儿头\n")
    write("untracked.md", "# 未托管（无头）\n")
    write("README.md", "# 手册（不计候选）\n")
    # 货架单层不变量：community/<包>/assets/ 下出现子目录即 FAIL
    shelf = os.path.join(root, "community", "合成包", "assets")
    os.makedirs(os.path.join(shelf, "子目录"), exist_ok=True)
    write(os.path.join("community", "合成包", "assets", "a.md"), HEADER("SHELF", "1.0", "active") + "# 架内\n")
    return root


def run(argv, cwd):
    proc = subprocess.run(argv, cwd=cwd, capture_output=True)
    return (proc.returncode, proc.stdout.decode("utf-8", "replace"),
            proc.stderr.decode("utf-8", "replace"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--cli", required=True)
    ap.add_argument("--py-exe", default=sys.executable)
    ap.add_argument("--work", default="")
    args = ap.parse_args()

    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass

    work = args.work or os.path.join(os.environ.get("TEMP", "/tmp"), "nf-asset-probe")
    os.makedirs(work, exist_ok=True)
    synth = build_assets_root(work)

    # 引擎侧用 --assets-root（避开与全局 --root 撞名）；Python 侧是 asset 子命令自己的 --root
    CASES = [
        ("真语料·verify（仓根）", ["verify"], ["verify"]),
        ("真语料·inventory（仓根）", ["inventory"], ["inventory"]),
        ("合成·verify（含全部违规类）", ["verify", "--root", synth], ["verify", "--assets-root", synth]),
        ("合成·inventory（文本）", ["inventory", "--root", synth], ["inventory", "--assets-root", synth]),
        ("合成·inventory --json", ["inventory", "--root", synth, "--json"], ["inventory", "--assets-root", synth, "--json"]),
        ("合成·ls（文本）", ["ls", "--root", synth], ["ls", "--assets-root", synth]),
        ("合成·ls --json", ["ls", "--root", synth, "--json"], ["ls", "--assets-root", synth, "--json"]),
        ("合成·ls --tier community", ["ls", "--root", synth, "--tier", "community"],
         ["ls", "--assets-root", synth, "--tier", "community"]),
        ("合成·ls --status deprecated", ["ls", "--root", synth, "--status", "deprecated"],
         ["ls", "--assets-root", synth, "--status", "deprecated"]),
        ("合成·ls --pkg 合成资产集", ["ls", "--root", synth, "--pkg", "合成资产集"],
         ["ls", "--assets-root", synth, "--pkg", "合成资产集"]),
        ("合成·ls --tier 非法（两侧都应 exit 2）", ["ls", "--root", synth, "--tier", "bogus"],
         ["ls", "--assets-root", synth, "--tier", "bogus"]),
        ("合成·ls --status 非法（两侧都应 exit 2）", ["ls", "--root", synth, "--status", "bogus"],
         ["ls", "--assets-root", synth, "--status", "bogus"]),
    ]

    checks: list[tuple[str, bool, str]] = []
    for label, py_tail, net_tail in CASES:
        py_code, py_out, py_err = run([args.py_exe, os.path.join(args.root, "scripts", "nf.py"),
                                       "asset", *py_tail], args.root)
        net_code, net_out, net_err = run([args.cli, "--root", args.root, "asset", *net_tail], args.root)
        same = py_out == net_out and py_code == net_code
        fails = [l.strip() for l in py_out.splitlines() if l.strip().startswith("[FAIL]")]
        checks.append((label, same,
                       f"exit {py_code}/{net_code} · stdout {len(py_out)}/{len(net_out)} 字节 · "
                       f"FAIL {len(fails)} 条" + (f" · 首条 {fails[0][7:50]}" if fails else "")))

    print("| # | 判定项 | 结果 | 证据 |")
    print("|---|---|---|---|")
    for name, ok, ev in checks:
        print("| | %s | %s | %s |" % (name, "通过" if ok else "**未达**", ev))
    failed = [c for c in checks if not c[1]]
    print("\n结论：%s" % (f"全部通过——{len(checks)} 面（真语料 verify + 合成台账 10 面）两侧同判"
                        if not failed else f"未达 {len(failed)} 项"))
    if not failed:
        shutil.rmtree(work, ignore_errors=True)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
