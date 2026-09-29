"""**抖动（flakiness）判据**：会抖的门等于不可信。

本项目的史书上有一条**未复现**的记录：第一百零六片面级对账里
`decide-dry-run-json py=1 net=0`——同一命令、同一语料，真源返回 1 而引擎返回 0，
当时只留了「未复现」四个字。会偶尔翻脸的门禁比没有门禁更危险（人会开始忽略它）。

本探针把「不抖」钉成判据：

  ① **引擎侧：同一命令重复 N 次（默认 3），退出码与 stdout 字节必须完全一致**；
     重复轮次**交替工作目录**（引擎根 ↔ 临时目录），顺带证「输出与 CWD 无关」；
  ② **跨实现：decide 家族（含那条历史瞬态 `decide-dry-run-json`）两侧各跑 N 次**，
     每侧自身必须稳，且**两侧输出逐字节相同**；
  ③ **负对照**：`bench` 会打印每次实测耗时 ⇒ 它**必须**在重复之间出现差异。
     若它也不变，说明本探针的比较根本照不出差异（判据恒绿），必须失败。
  ④ 顺带记时：每条命令的 min / 中位 / max，给「运行时间可预期」留证据。

用法：
    python probes/stability_probe.py --snap <隔离快照> --cli <nf-dotnet.exe>
        [--py-exe <python>] [--repeats 3] [--keep]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # noqa: BLE001
    pass
sys.dont_write_bytecode = True

import _paths  # 默认路径唯一出处（探针可移植）
DEFAULT_SNAP = _paths.SNAP
ENGINE = _paths.ENGINE
# （名称, 参数, 期望退出码）—— 全部确定性面；{tmp} 由夹具替换
BATTERY = [
    ("verify-json", ["verify", "--json"], 0),
    ("selftest-json", ["selftest", "--json"], 0),
    ("combine-verify-json", ["combine", "verify", "--json"], 0),
    ("receipts-json", ["receipts", "--json"], 0),
    ("receipts-library-json", ["receipts", "--scope", "library", "--json"], 0),
    ("transparency-json", ["transparency", "--json"], 0),
    ("library-json", ["library", "--json"], 0),
    ("model-json", ["model", "--json"], 0),
    ("sig-json", ["sig", "--json"], 0),
    ("decisions-json", ["decisions", "--json"], 0),
    ("assertions-json", ["assertions", "--json"], 0),
    ("cognition-json", ["cognition", "--json"], 0),
    ("conformance-json", ["conformance", "--json"], 0),
    ("corpus-json", ["corpus", "--json"], 0),
]

# decide 家族：同参数跑两侧（真源 scripts/nf.py ↔ 引擎）
DECIDE_FACES = [
    ("decide", ["decide", "--state-text", "雨天走廊 与 校园情感 场景", "--questions", "{tmp}/decide-questions.json"]),
    ("decide-json", ["decide", "--state-text", "雨天走廊 与 校园情感 场景", "--questions", "{tmp}/decide-questions.json", "--json"]),
    ("decide-dry-run-json", ["decide", "--dry-run", "--questions", "{tmp}/decide-questions.json", "--json"]),
    ("decide-abstained-json", ["decide", "--state-text", "x", "--questions", "{tmp}/decide-questions.json", "--adapter", "ghost", "--json"]),
]

DECIDE_FIXTURE = json.dumps({
    "pipeline": {"type": "choice", "options": ["P02 校园情感流", "P03 西幻生存流"]},
    "multilingual": {"type": "noul", "true_hints": ["中文", "多语"]},
    "risk": {"type": "score", "levels": ["低", "中", "高"]},
}, ensure_ascii=False, indent=2) + "\n"

NEGATIVE_CONTROL = ("bench", ["bench"])


def run(cmd: list[str], cwd: Path, env: dict | None = None, timeout: int = 900) -> tuple[int, bytes, float]:
    t0 = time.perf_counter()
    p = subprocess.run(cmd, cwd=str(cwd), capture_output=True, env=env, timeout=timeout)
    dt = time.perf_counter() - t0
    return p.returncode, p.stdout, dt


def h(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()[:16]


def first_diff(a: bytes, b: bytes) -> str:
    la, lb = a.decode("utf-8", "replace").splitlines(), b.decode("utf-8", "replace").splitlines()
    for i in range(max(len(la), len(lb))):
        x = la[i] if i < len(la) else "(缺行)"
        y = lb[i] if i < len(lb) else "(缺行)"
        if x != y:
            return f"第 {i+1} 行：{x[:70]} ≠ {y[:70]}"
    return "（行同而字节不同：行尾/编码差异）"


def dump_evidence(tag: str, runs: list[tuple[int, bytes, str]], argv: list[str]) -> str:
    """不稳定时把**全量证据**写进 `_stout/`（只打印前几行差异会看不出来到底是哪条 issue）。"""
    out_dir = ENGINE / "probes" / "_stout"
    out_dir.mkdir(parents=True, exist_ok=True)
    dest = out_dir / f"_stability_fail_{tag}.txt"
    lines = [f"# 不稳定面：{tag}", f"# argv：{' '.join(argv)}", ""]
    for i, (code, data, cwd) in enumerate(runs, start=1):
        lines.append(f"===== 第 {i} 次 · exit={code} · cwd={cwd} · sha256[:16]={h(data)} =====")
        lines.append(data.decode("utf-8", "replace"))
        lines.append("")
    dest.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    return str(dest)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--snap", default=DEFAULT_SNAP)
    ap.add_argument("--cli", default="")
    ap.add_argument("--py-exe", default=sys.executable)
    ap.add_argument("--engine", default=str(ENGINE))
    ap.add_argument("--repeats", type=int, default=3)
    ap.add_argument("--keep", action="store_true")
    ap.add_argument("--timeout", type=int, default=900)
    args = ap.parse_args()

    snap = Path(args.snap)
    engine = Path(args.engine)
    if args.repeats < 2:
        # 重复 1 次时「负对照必须变」这条无从成立 ⇒ 直接按用法错误拒掉，别给出「判据恒绿」的假象
        print("FAIL: --repeats 至少为 2（抖动判据靠重复比对；单次无法证稳，也无法证负对照会变）")
        return 1
    cli = args.cli
    if not cli:
        cands = sorted((engine / "dist").glob("nf-dotnet-win-x64-f*/nf-dotnet.exe"))
        cli = str(cands[-1]) if cands else ""
    if not cli or not Path(cli).exists():
        print("FAIL: 找不到 nf-dotnet.exe（--cli 未给且 dist 下无 fNN 产物）")
        return 1

    problems: list[str] = []
    tmp = Path(tempfile.mkdtemp(prefix="nf-stability-"))
    try:
        (tmp / "decide-questions.json").write_text(DECIDE_FIXTURE, encoding="utf-8", newline="\n")
        cwds = [engine, tmp]  # 交替工作目录：顺带证「输出与 CWD 无关」

        # ① 引擎侧重复
        print(f"① 引擎侧 {len(BATTERY)} 条 × {args.repeats} 次（交替 CWD：engine ↔ tmp）")
        stats: dict[str, list[float]] = {}
        for name, argv, expect in BATTERY:
            seen: list[tuple[int, bytes, Path]] = []
            for r in range(args.repeats):
                cwd = cwds[r % len(cwds)]
                code, out, dt = run([cli, "--root", str(snap)] + argv, cwd=cwd, timeout=args.timeout)
                seen.append((code, out, cwd))
                stats.setdefault(name, []).append(dt)
            base_code, base_out, base_cwd = seen[0]
            for i, (code, out, cwd) in enumerate(seen[1:], start=2):
                if code != base_code:
                    problems.append(f"{name} 第 {i} 次退出码不同：{base_code} → {code}（CWD={cwd}）")
                elif out != base_out:
                    problems.append(f"{name} 第 {i} 次输出不同（CWD={cwd}）：{first_diff(base_out, out)}")
            if any(s[0] != base_code or s[1] != base_out for s in seen[1:]):
                where = dump_evidence(name, [(c, o, str(w)) for c, o, w in seen], argv)
                print(f"   ⚠ {name} 不稳定 —— 全量证据已写：{where}")
            if base_code != expect:
                problems.append(f"{name} 退出码与期望不符：{base_code} ≠ {expect}")
            ts = stats[name]
            print(f"   {name:24s} exit={base_code} · {len(base_out):7d}B · "
                  f"{min(ts):.2f}/{statistics.median(ts):.2f}/{max(ts):.2f}s（min/中位/max）")

        # ② decide 家族：两侧各 N 次，各自要稳、彼此要同
        nf_py = snap / "scripts" / "nf.py"
        env = dict(os.environ)
        env["PYTHONPATH"] = str(snap / "desktop" / "src")
        env["PYTHONIOENCODING"] = "utf-8"
        print(f"② decide 家族 {len(DECIDE_FACES)} 条 × {args.repeats} 次 × 两侧（含历史瞬态 decide-dry-run-json）")
        for name, argv in DECIDE_FACES:
            if not nf_py.exists():
                problems.append(f"真源入口不在场：{nf_py}")
                break
            real = [a.replace("{tmp}", str(tmp)) for a in argv]
            net_runs, py_runs = [], []
            for r in range(args.repeats):
                c, o, _ = run([cli, "--root", str(snap)] + real, cwd=cwds[r % len(cwds)], timeout=args.timeout)
                net_runs.append((c, o))
                c, o, _ = run([args.py_exe, str(nf_py)] + real, cwd=snap, env=env, timeout=args.timeout)
                py_runs.append((c, o))
            for i, (c, o) in enumerate(net_runs[1:], start=2):
                if c != net_runs[0][0] or o != net_runs[0][1]:
                    problems.append(f"{name} 引擎侧第 {i} 次不稳：exit {net_runs[0][0]}→{c} · {first_diff(net_runs[0][1], o)}")
                    where = dump_evidence(f"{name}.net", [(cc, oo, str(snap)) for cc, oo in net_runs], real)
                    print(f"   ⚠ {name} 引擎侧不稳 —— 全量证据已写：{where}")
            for i, (c, o) in enumerate(py_runs[1:], start=2):
                if c != py_runs[0][0] or o != py_runs[0][1]:
                    problems.append(f"{name} 真源侧第 {i} 次不稳：exit {py_runs[0][0]}→{c} · {first_diff(py_runs[0][1], o)}")
                    where = dump_evidence(f"{name}.py", [(cc, oo, str(snap)) for cc, oo in py_runs], real)
                    print(f"   ⚠ {name} 真源侧不稳 —— 全量证据已写：{where}")
            nc, no = net_runs[0]
            pc, po = py_runs[0]
            verdict = "同" if (nc == pc and no == po) else "不同"
            print(f"   {name:24s} 引擎 exit={nc} {len(no):6d}B · 真源 exit={pc} {len(po):6d}B · 两侧{verdict}"
                  f" · 各自 {args.repeats} 次一致")
            if nc != pc:
                problems.append(f"{name} 两侧退出码不同：引擎 {nc} / 真源 {pc}")
            elif no != po:
                problems.append(f"{name} 两侧输出不同：{first_diff(po, no)}")

        # ③ 负对照：bench 必须变
        print("③ 负对照：bench（打印每次实测耗时）应在重复之间出现差异")
        b_hashes = []
        for r in range(args.repeats):
            _, out, _ = run([cli, "--root", str(snap)] + NEGATIVE_CONTROL[1], cwd=cwds[r % len(cwds)], timeout=args.timeout)
            b_hashes.append(h(out))
        print(f"   bench 三次 sha256[:16] = {b_hashes}")
        if len(set(b_hashes)) == 1:
            problems.append("负对照 bench 三次完全一致 —— 比较照不出差异，本判据恒绿不可信")

        if problems:
            print("FAIL:")
            for p in problems:
                print("  -", p)
            return 1
        print(f"OK: 不抖（引擎侧 {len(BATTERY)} 条 × {args.repeats} 次逐字节一致 · "
              f"decide 家族两侧各自稳且彼此同 · 负对照会变）")
        return 0
    finally:
        if args.keep:
            print(f"   临时目录保留：{tmp}")
        else:
            import shutil
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
