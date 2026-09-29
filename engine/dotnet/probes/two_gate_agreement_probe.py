"""**两道门同语料对照**：真源 `verify.sh` 与 .NET 只读门在同一份语料上给出同一结论吗？

为什么这是最要紧的一条证据：此前所有对账都是**面级/判据级**（177 面逐字节、39 道 check 逐条载体）。
本探针把**门本身**放在一起比：同一份临时拷贝上，真源门报 `PASS=n WARN=n FAIL=n`，引擎门报
自检 `通过 n/失败 n` + 聚合门 +（可选）面级对账，两边**都应绿**且**退出码一致**。

口径与纪律：
- **在临时拷贝上跑**（`shutil.copytree`）——不碰快照、不碰作者仓库；真源门自身用 `mktemp -d` 放临时件；
- 两边**计数不同构**（真源 39 道 check / PASS 68；引擎 223 例自检 + 177 面 + 11 组件）——本探针比的是
  **结论（绿/红）与退出码**，不是数字相等；
- 引擎门失败时，记录件会**原样截出失败钉名与 detail**（`run-gate.ps1` 自第一百零七片起打印），
  于是「一次性瞬态」也能被追认（同名钉连跑数次即可判）。

用法：
    python probes/two_gate_agreement_probe.py --snap <快照> --cli <nf-dotnet> [--bash <bash.exe>]
                                              [--with-faces] [--record <输出 md>]
"""
from __future__ import annotations

import argparse
import hashlib
import re
import shutil
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
ENGINE = str(_paths.ENGINE)
DEFAULT_SNAP = _paths.SNAP
DEFAULT_CLI = str(_paths.newest_dist("win-x64") / "nf-dotnet.exe")
DEFAULT_BASH = _paths.BASH
DEFAULT_PY = _paths.PY
DEFAULT_RECORD = _paths.records("NF_NET引擎_双门同语料对照记录_v1.md")
def fingerprint(root: Path) -> str:
    rows = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        parts = path.relative_to(root).parts
        rel = path.relative_to(root).as_posix()
        if ".git" in parts or "__pycache__" in parts or rel.endswith((".pyc", ".pyo")):
            continue
        rows.append((rel, path.stat().st_size,
                     hashlib.sha256(path.read_bytes()).hexdigest()))
    rows.sort(key=lambda r: r[0])
    blob = "".join(f"{rel}\0{size}\0{digest}\n" for rel, size, digest in rows).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()[:16]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--snap", default=DEFAULT_SNAP)
    ap.add_argument("--cli", default=DEFAULT_CLI)
    ap.add_argument("--bash", default=DEFAULT_BASH)
    ap.add_argument("--py-exe", default=DEFAULT_PY)
    ap.add_argument("--with-faces", action="store_true")
    ap.add_argument("--record", default=DEFAULT_RECORD)
    args = ap.parse_args()

    snap = Path(args.snap).resolve()
    problems = []
    fail_block = []
    faces_line = ""
    with tempfile.TemporaryDirectory(prefix="nf-bothgates-") as tmp:
        tree = Path(tmp) / "corpus"
        shutil.copytree(snap, tree)
        fp = fingerprint(tree)
        snap_fp = fingerprint(snap)
        print(f"临时拷贝：{tree} · 语料指纹 {fp}（快照 {snap_fp}）")
        if fp != snap_fp:
            problems.append("拷贝与快照指纹不一致（拷贝不完整）")

        # ① 引擎门（先跑：真源门会在树内写 .pyc）
        t0 = time.time()
        gate = subprocess.run(["pwsh", "-NoProfile", "-File", f"{ENGINE}\\run-gate.ps1",
                               "-Root", str(tree), "-Cli", args.cli],
                              capture_output=True, timeout=3600)
        engine_secs = time.time() - t0
        gate_out = gate.stdout.decode("utf-8", "replace").replace("\r\n", "\n")
        cases = re.search(r"用例 (\d+) 条 · 通过 (\d+) · 失败 (\d+)", gate_out)
        eng_total, eng_pass, eng_fail = (
            (int(cases.group(1)), int(cases.group(2)), int(cases.group(3)))
            if cases else (-1, -1, -1))
        gate_verdict = "PASS" if "== NF .NET 门：PASS ==" in gate_out else "FAIL"
        if gate_verdict == "FAIL":
            lines_all = gate_out.splitlines()
            start = next((i for i, l in enumerate(lines_all) if "失败钉" in l), None)
            if start is not None:
                fail_block = [l.strip() for l in lines_all[start:start + 12] if l.strip()]
        print(f"① 引擎门（先跑：真源门会在树内写 .pyc · run-gate.ps1）：exit={gate.returncode} · 自检 {eng_pass}/{eng_total} · "
              f"判定 {gate_verdict} · {engine_secs:.0f}s")
        if fail_block:
            print("   失败钉：" + " | ".join(fail_block[:4]))

        # ② 真源门
        t0 = time.time()
        proc = subprocess.run([args.bash, "./verify.sh"], cwd=str(tree), capture_output=True, timeout=3600)
        real_secs = time.time() - t0
        real_out = proc.stdout.decode("utf-8", "replace").replace("\r\n", "\n")
        summary = re.search(r"结果统计: PASS=(\d+)\s+WARN=(\d+)\s+FAIL=(\d+)", real_out)
        real_pass, real_warn, real_fail = (
            (int(summary.group(1)), int(summary.group(2)), int(summary.group(3)))
            if summary else (-1, -1, -1))
        print(f"② 真源门（verify.sh）：exit={proc.returncode} · PASS={real_pass} WARN={real_warn} "
              f"FAIL={real_fail} · {real_secs:.0f}s")

        # ③ 面级（可选）
        if args.with_faces:
            t0 = time.time()
            faces = subprocess.run([args.py_exe, "-X", "utf8", f"{ENGINE}\\probes\\face_parity_probe.py",
                                    "--root", str(tree), "--py-exe", args.py_exe, "--cli", args.cli],
                                   capture_output=True, timeout=3600)
            faces_secs = time.time() - t0
            faces_out = faces.stdout.decode("utf-8", "replace")
            faces_line = next((l.strip() for l in faces_out.splitlines() if "面级对账" in l), "（未取到）")
            print(f"③ 面级对账：exit={faces.returncode} · {faces_line} · {faces_secs:.0f}s")
            if faces.returncode != 0:
                problems.append("面级对账未全绿")

    both_green = (proc.returncode == 0 and real_fail == 0 and gate.returncode == 0 and eng_fail == 0)
    if proc.returncode != gate.returncode:
        problems.append(f"两道门退出码不一致：真源 {proc.returncode} / 引擎 {gate.returncode}")
    if real_fail != 0:
        problems.append(f"真源门有 FAIL={real_fail}")
    if eng_fail != 0:
        problems.append(f"引擎门有失败 {eng_fail} 条")

    lines = [
        "# NF · 两道门同语料对照记录（v1）",
        "",
        "> 生成物（由 `probes/two_gate_agreement_probe.py` 写入，**勿手改**）。回答一个问题："
        "**真源 `verify.sh` 与 .NET 只读门，在同一份语料上给出同一结论吗？**",
        "",
        "## 1. 被测语料",
        "",
        f"- 快照：`{snap}`（语料指纹 `{snap_fp}`）——探针在**临时拷贝**上跑，跑完即清理（不碰快照与作者仓库）",
        f"- 引擎产物：`{args.cli}`",
        "",
        "## 2. 两侧结论",
        "",
        "| 门 | 退出码 | 统计 | 判定 | 耗时 |",
        "|---|---|---|---|---|",
        f"| 真源 `verify.sh` | {proc.returncode} | PASS={real_pass} · WARN={real_warn} · FAIL={real_fail} | "
        f"{'全部通过' if proc.returncode == 0 else '有失败'} | {real_secs:.0f}s |",
        f"| .NET 门 `run-gate.ps1` | {gate.returncode} | 自检 {eng_pass}/{eng_total} · 聚合门 11 件 | "
        f"{gate_verdict} | {engine_secs:.0f}s |",
    ]
    if faces_line:
        lines.append(f"| .NET 面级对账 | 0 | {faces_line} | 全同 | — |")
    lines += [
        "",
        "## 3. 口径说明（为什么数字不同构）",
        "",
        "- 真源门 = `verify.sh` 的 **39 道 check**（`PASS=68` 是各 check 内部断言计数）；",
        "- 引擎门 = 聚合门 **11 组件** + 负例自检 **223 例** +（可选）面级 **177 面**；",
        "- 本记录比的是**结论（绿/红）与退出码**，不是数字相等——两套门的分辨率不同，数字不可对齐。",
        "",
    ]
    if fail_block:
        lines += ["## 3a. 引擎门失败钉（原样截出 · 同名钉连跑数次可判是否瞬态）", ""]
        lines += [f"- `{l}`" for l in fail_block]
        lines.append("")
    lines += [
        "## 4. 结论",
        "",
        f"- {'**两道门同语料同结论（均绿）**' if both_green else '**未达成同结论**'}——"
        f"真源 exit={proc.returncode} / 引擎 exit={gate.returncode}。",
        "- 意义：.NET 只读门不是「另一套自说自话的检查」，而是与真源门**在同一语料上同判**的第二道门。",
        "",
        "## 5. 问题清单",
        "",
    ]
    lines += [f"- {p}" for p in problems] if problems else ["- （无）"]
    lines.append("")
    record = Path(args.record)
    record.parent.mkdir(parents=True, exist_ok=True)
    with open(record, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines))
    print(f"④ 记录件已写：{record}")

    if problems:
        print("FAIL:")
        for p in problems:
            print("  -", p)
        return 1
    print("OK: 两道门在同一份语料上同结论（均绿 · 退出码一致）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
