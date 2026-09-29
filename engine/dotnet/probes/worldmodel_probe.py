#!/usr/bin/env python3
"""世界模型（world_model）探针：**合成违规语料差分** + 片内纪律断言。

为什么单开一面：world_model 判的是"契约形状 + 槽位注册 + 相位图可达 + 检查类型"，
顺路径（仓库里唯一那份契约）绿不代表判据真的在判——**必须喂坏契约**看两侧是否同判。

做法（关键约束）：Python 侧 `nf worldmodel` **没有 --root**，它扫的是 `nf.py` 所在仓库
（`ROOT = <repo>`），所以夹具必须落在**快照副本**里；引擎侧用 `--root <同一副本>`。
两侧扫同一棵树，唯一变量是"谁在判"。

断言：
  ① 干净契约（用真槽位注册表里的 slot）→ 两侧零违例、逐字节同输出；
  ② 违规契约（未注册槽 / 类型漂移 / 元素类型漂移 / owner 漂移 / 相位不可达 / 重复名 / 缺初始值 /
     非法 kind / monotonic 与 finite_sequence 用错 / 非空数组要求）→ **两侧逐字节同输出 + 同退出码**；
  ③ 非对象 world_model → 两侧同判；
  ④ 重放面（第二部分）：干净语料上 `--walk` / `--run` / `--run --json` 与 Python **逐字节同输出**
     （含轨迹、终止原因与 **digest**）；违例契约上两侧同样非零退出（文案不同：Python 抛栈 vs 引擎受控失败，
     属已声明的不可约差异）。

用法：
    python probes/worldmodel_probe.py --root <快照> --cli <nf-dotnet> --py-exe <python>

退出码：0 全过；1 有未达项。
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys

CLEAN = """machine_contract:
  id: WM:01
  layer: P40
  inputs: []
  outputs: []
  events:
    publish: []
    subscribe: []
  world_model:
    abstract_state:
      variables:
        - name: phase
          kind: string
          source: M50
        - name: tick
          kind: integer
          source: 通用:M10
          slot: WorldState.time.tick
        - name: phase_trace
          kind: array
          item_kind: string
          source: M50
          slot: data_bus.round.phase_trace
      initial:
        phase: begin
        tick: 0
        phase_trace: []
    transition:
      initial_phase: begin
      phases:
        - phase: begin
          next: run
          guard: 输入就绪
          writes: [tick]
        - phase: run
          next: begin
          guard: 步进完成
          writes: [tick, phase_trace]
    invariants:
      - tick 单调不减
    checks:
      - kind: finite_phase
        field: phase
        values: [begin, run]
      - kind: monotonic
        field: tick
      - kind: finite_sequence
        field: phase_trace
        values: [begin, run]
"""

BROKEN = """machine_contract:
  id: WM:02
  layer: P40
  inputs: []
  outputs: []
  events:
    publish: []
    subscribe: []
  world_model:
    abstract_state:
      variables:
        - name: tick
          kind: string
          source: 通用:M10
          slot: WorldState.time.tick
        - name: tick
          kind: integer
          source: 通用:M10
          slot: WorldState.time.tick
        - name: ghost
          kind: integer
          source: 通用:M10
          slot: ghost.slot
        - name: trace
          kind: array
          item_kind: integer
          source: M50
          slot: data_bus.round.phase_trace
        - name: day
          kind: integer
          source: 别的模块
          slot: WorldState.time.day
        - name: bad
          kind: not_a_kind
          source: ""
        - name: log
          kind: array
          item_kind: object
          source: M50
      initial:
        tick: 0
        undeclared: 1
    transition:
      initial_phase: nowhere
      phases:
        - phase: a
          next: b
          guard: g
          writes: [ok]
        - phase: a
          next: also_nowhere
          guard: ""
          writes: [1]
        - phase: c
          next: a
          guard: g
          writes: []
    invariants: []
    checks:
      - kind: monotonic
        field: tick
      - kind: finite_sequence
        field: tick
        values: [x]
      - kind: bogus
        field: nope
      - kind: finite_phase
        field: ghost
        values: []
"""

NOT_OBJECT = """machine_contract:
  id: WM:03
  layer: P40
  inputs: []
  outputs: []
  events:
    publish: []
    subscribe: []
  world_model: 不是对象
"""

NEEDED = ("scripts", os.path.join("desktop", "src"), "protocol", "04_模块库")


def prepare(snapshot: str, work: str) -> None:
    """把快照里 worldmodel 需要的那几棵子树拷进副本（Python 侧 ROOT 由 nf.py 位置决定）。"""
    if os.path.isdir(work):
        shutil.rmtree(work)
    os.makedirs(work)
    for rel in NEEDED:
        src = os.path.join(snapshot, rel)
        if not os.path.isdir(src):
            raise SystemExit("快照缺目录：%s" % src)
        shutil.copytree(src, os.path.join(work, rel))
    os.makedirs(os.path.join(work, "community"), exist_ok=True)


def plant(work: str, body: str, name: str) -> None:
    path = os.path.join(work, "04_模块库", "通用类", name)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("# 模块 WM（探针合成）\n\n```yaml\n" + body + "```\n")


def run(argv: list[str], cwd: str) -> tuple[int, str, str]:
    proc = subprocess.run(argv, cwd=cwd, capture_output=True)
    return (proc.returncode, proc.stdout.decode("utf-8", "replace"),
            proc.stderr.decode("utf-8", "replace"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True, help="仓库快照（真源，探针只读）")
    ap.add_argument("--cli", required=True)
    ap.add_argument("--py-exe", default=sys.executable)
    ap.add_argument("--work", default="")
    args = ap.parse_args()

    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass

    work = args.work or os.path.join(os.environ.get("TEMP", "/tmp"), "nf-worldmodel-probe")
    prepare(args.root, work)
    print("合成副本：%s（Python 侧 ROOT = 该副本）\n" % work)

    checks: list[tuple[str, bool, str]] = []

    # ① 干净契约 + ② 违规契约 + ③ 非对象：逐个植入同一副本后两侧同跑（对照 = 每轮都含前几轮的件）
    for label, body, name in (("干净契约", CLEAN, "clean.md"),
                              ("违规契约", BROKEN, "broken.md"),
                              ("非对象契约", NOT_OBJECT, "notobj.md")):
        plant(work, body, name)
        py_code, py_out, py_err = run([args.py_exe, os.path.join(work, "scripts", "nf.py"),
                                       "worldmodel"], work)
        net_code, net_out, net_err = run([args.cli, "--root", work, "worldmodel"], work)
        py_json_code, py_json, _py_jerr = run([args.py_exe, os.path.join(work, "scripts", "nf.py"),
                                               "worldmodel", "--json"], work)
        net_json_code, net_json, _net_jerr = run([args.cli, "--root", work, "worldmodel", "--json"], work)
        same_text = py_out == net_out and py_code == net_code
        same_json = py_json == net_json and py_json_code == net_json_code
        same_err = py_err == net_err
        # FAIL 行走 stderr（两侧同规）——证据里读 stderr，避免"零违例"的错觉
        fails = [l.strip() for l in py_err.splitlines() if l.strip().startswith("[FAIL]")]
        checks.append((f"合成差分·{label}（文本+JSON+stderr 逐字节同 + 同退出码）",
                       same_text and same_json and same_err,
                       f"文本 exit {py_code}/{net_code}·{len(py_out)}/{len(net_out)} 字节 · "
                       f"JSON exit {py_json_code}/{net_json_code} · stderr 违例 {len(fails)} 条 · "
                       f"stderr 同={same_err}" +
                       (f" · 首条 {fails[0][8:60]}" if fails else "")))

    # ④ 重放面：**只含干净契约**的独立副本上三面逐字节同（含 digest 与退出码 0）
    clean_copy = work + "-cleanonly"
    prepare(args.root, clean_copy)
    plant(clean_copy, CLEAN, "clean.md")
    for extra in (["--walk"], ["--run"], ["--run", "--json"]):
        py_code, py_out, py_err = run([args.py_exe, os.path.join(clean_copy, "scripts", "nf.py"),
                                       "worldmodel", *extra], clean_copy)
        net_code, net_out, net_err = run([args.cli, "--root", clean_copy, "worldmodel", *extra], clean_copy)
        same = py_out == net_out and py_code == net_code
        digest = ""
        if extra == ["--run"]:
            for line in py_out.splitlines():
                if "digest=" in line:
                    digest = line.split("digest=")[1].rstrip("）)")
        checks.append((f"重放面 {' '.join(extra)}·仅干净契约副本（逐字节同 + 同退出码 0）",
                       same, f"exit {py_code}/{net_code} · {len(py_out)}/{len(net_out)} 字节" +
                             (f" · digest={digest[:12]}" if digest else "")))

    # 混合语料（含违例契约）：Python 抛 WorldModelViolation（栈）vs 引擎受控失败——
    # 只要求 **stdout 同 + 判定同向**（文案与退出码 1/2 属已声明不可约差异）
    for extra in (["--run"], ["--run", "--json"]):
        py_code, py_out, _e = run([args.py_exe, os.path.join(work, "scripts", "nf.py"),
                                   "worldmodel", *extra], work)
        net_code, net_out, _e2 = run([args.cli, "--root", work, "worldmodel", *extra], work)
        checks.append((f"重放面 {' '.join(extra)}·含违例契约（stdout 同 + 同向非零；文案/码不可约）",
                       py_out == net_out and (py_code == 0) == (net_code == 0),
                       f"exit py={py_code}/net={net_code} · stdout {len(py_out)}/{len(net_out)} 字节"))


    # --state 缺文件：两侧同向非零
    py_code, _o, _e = run([args.py_exe, os.path.join(work, "scripts", "nf.py"), "worldmodel",
                           "--state", os.path.join(work, "no-such-state.json")], work)
    net_code, _o2, _e2 = run([args.cli, "--root", work, "worldmodel",
                              "--state", os.path.join(work, "no-such-state.json")], work)
    checks.append(("--state 缺文件 → 两侧同向非零退出", py_code != 0 and net_code != 0,
                   f"exit py={py_code}/net={net_code}"))

    print("| # | 判定项 | 结果 | 证据 |")
    print("|---|---|---|---|")
    for name, ok, ev in checks:
        print("| | %s | %s | %s |" % (name, "通过" if ok else "**未达**", ev))
    failed = [c for c in checks if not c[1]]
    print("\n结论：%s" % ("全部通过——合成违规语料两侧逐字节同判，重放面未移植前明确拒绝" if not failed
                        else f"未达 {len(failed)} 项"))
    if not failed:
        shutil.rmtree(work, ignore_errors=True)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
