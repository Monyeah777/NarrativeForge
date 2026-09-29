#!/usr/bin/env python3
"""概念前置闭包求值器差分探针（第 71 片）：`scripts/ai_domain_closure.py` ↔ `nf-dotnet domain-closure`。

真仓的两张图（CONCEPT_GRAPH / QUANT_GRAPH）**都是健康的**，所以正向对账证不了判据在判。
本探针造合成图，把 `concept_graph.problems()` 的**每条判据**都单独触发一次：
环 / 悬空前置 / 自环 / 节点 id 重复 / 缺 name / 缺 provenance / 图例漂移 / 层位越界 /
别名重复 / 未归分支 / 分支声明不存在 / 一概念多分支 / provenance_strength 缺声明与越词表与不自洽。
另钉三条退出码口径：未知目标（1）/ 未知分支（2）/ 未知序（2），以及未登记资产的通用判据自检。

两侧读**同一张合成图**（`--asset` 传绝对路径，两侧都不在仓库内 → 标签同为原串）。
退出码：0 = 全部一致 · 1 = 存在不一致。
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def run(argv, cwd):
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    proc = subprocess.run(argv, capture_output=True, env=env, cwd=cwd)
    return proc.returncode, proc.stdout, proc.stderr


def py(snap: Path, cwd: Path, *argv):
    return run([sys.executable, str(snap / "scripts" / "ai_domain_closure.py"), *argv], cwd)


def engine(cli: Path, root: Path, cwd: Path, *argv):
    return run([str(cli), "--root", str(root), "domain-closure", *argv], cwd)


class Report:
    def __init__(self) -> None:
        self.passed = 0
        self.failed = 0

    def check(self, name: str, ok: bool, detail: str) -> None:
        if ok:
            self.passed += 1
            print(f"  ✓ {name}")
        else:
            self.failed += 1
            print(f"  ✗ {name} —— {detail}")


def parity(rep: Report, name: str, snap: Path, cli: Path, cwd: Path, argv,
           expect_rc: int | None = None, must_contain: str | None = None) -> bytes:
    pe, po, pex = py(snap, cwd, *argv)
    de, do, dex = engine(cli, snap, cwd, *argv)
    same = (pe == de and po == do and pex == dex)
    detail = f"py_rc={pe} net_rc={de}"
    ok = same
    if expect_rc is not None and pe != expect_rc:
        ok = False
        detail += f" · 期望真源 rc={expect_rc}"
    if must_contain is not None and must_contain not in (po + pex).decode("utf-8", "replace"):
        ok = False
        detail += f" · 真源输出缺「{must_contain}」"
    if not same:
        detail += ("\n--- PY stdout ---\n" + po.decode("utf-8", "replace")
                   + "\n--- NET stdout ---\n" + do.decode("utf-8", "replace")
                   + "\n--- PY stderr ---\n" + pex.decode("utf-8", "replace")
                   + "\n--- NET stderr ---\n" + dex.decode("utf-8", "replace"))
    rep.check(name, ok, detail)
    return po + pex


HEALTHY = """# 合成概念图

```yaml
concept_graph:
  version: "1.0"
  domain: 合成域
  provenance_strength: domain-logic
  provenance_legend:
    domain-logic: 域内推理
  nodes:
    - id: C00
      name: 根概念
      layer: P00
      provenance: [domain-logic]
    - id: C01
      name: 子概念甲
      layer: P10
      provenance: [domain-logic]
      aliases: [甲, Alpha]
      prereqs: [C00]
    - id: C02
      name: 子概念乙
      layer: P20
      provenance: [domain-logic]
      prereqs: [C01]
  branches:
    - id: main
      nodes: [C00, C01, C02]
  orderings:
    - id: seq
      seq: [C00, C01, C02]
```
"""


def variant(work: Path, name: str, text: str) -> str:
    path = work / f"{name}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")
    return str(path)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--snap", required=True)
    ap.add_argument("--cli", required=True)
    ap.add_argument("--keep", action="store_true")
    args = ap.parse_args()
    snap = Path(args.snap).resolve()
    cli = Path(args.cli).resolve()
    rep = Report()
    work = Path(tempfile.mkdtemp(prefix="nf-domain-closure-"))
    cwd = snap   # 两侧同一 cwd（脚本 `--asset` 相对路径按 cwd 解析）
    print("== 概念闭包求值器差分（合成图 · 两侧同图同 cwd）==")
    try:
        good = variant(work, "good", HEALTHY)
        # ————— 正向面（同一张健康图上的六种调用）
        parity(rep, "正向 · 默认目标（C02）", snap, cli, cwd, ["--asset", good, "--target", "C02"], expect_rc=0)
        parity(rep, "正向 · --list", snap, cli, cwd, ["--asset", good, "--list"], expect_rc=0, must_contain="条目键全表")
        parity(rep, "正向 · 别名解析（Alpha）", snap, cli, cwd, ["--asset", good, "--target", "Alpha"], expect_rc=0)
        parity(rep, "正向 · --ready-list --loaded", snap, cli, cwd,
               ["--asset", good, "--ready-list", "--loaded", "C00", "--json"], expect_rc=0)
        parity(rep, "正向 · --gaps --limit", snap, cli, cwd, ["--asset", good, "--gaps", "--limit", "2"], expect_rc=0)
        parity(rep, "正向 · --order 零违反", snap, cli, cwd, ["--asset", good, "--order", "seq"], expect_rc=0,
               must_contain="违反边：0")
        parity(rep, "正向 · --json 机读面", snap, cli, cwd, ["--asset", good, "--target", "C02", "--json"], expect_rc=0)

        # ————— problems() 逐条判据（每条一次注入）
        cases = {
            "环": (HEALTHY.replace("      prereqs: [C00]\n", "      prereqs: [C00, C02]\n"), "环"),
            "悬空": (HEALTHY.replace("      prereqs: [C01]\n", "      prereqs: [C01, C99]\n"), "悬空前置"),
            "自环": (HEALTHY.replace("      prereqs: [C00]\n", "      prereqs: [C01]\n"), "自环"),
            "id重复": (HEALTHY.replace("    - id: C02\n", "    - id: C01\n"), "节点 id 重复"),
            "缺name": (HEALTHY.replace("      name: 子概念甲\n", ""), "缺 name"),
            "缺provenance": (HEALTHY.replace("      provenance: [domain-logic]\n      aliases: [甲, Alpha]\n",
                                             "      aliases: [甲, Alpha]\n"), "缺 provenance"),
            "图例漂移": (HEALTHY.replace("      provenance: [domain-logic]\n      aliases: [甲, Alpha]\n",
                                         "      provenance: [external-x]\n      aliases: [甲, Alpha]\n"), "不在 provenance_legend 中"),
            "层位越界": (HEALTHY.replace("      layer: P10\n", "      layer: P99\n"), "层位越界"),
            "别名重复": (HEALTHY.replace("      aliases: [甲, Alpha]\n", "      aliases: [甲, Alpha, 乙]\n")
                          .replace("      name: 子概念乙\n", "      name: 子概念乙\n      aliases: [乙]\n"), "别名重复"),
            "未归分支": (HEALTHY.replace("      nodes: [C00, C01, C02]", "      nodes: [C00, C01]"), "未归入任何分支"),
            "分支声明不存在": (HEALTHY.replace("      nodes: [C00, C01, C02]", "      nodes: [C00, C01, C02, C99]"),
                               "分支声明了不存在的概念"),
            "一概念多分支": (HEALTHY.replace("  branches:\n    - id: main\n      nodes: [C00, C01, C02]",
                                             "  branches:\n    - id: main\n      nodes: [C00, C01, C02]\n"
                                             "    - id: extra\n      nodes: [C02]"),
                               "多个分支重复声明"),
            "缺强度声明": (HEALTHY.replace("  provenance_strength: domain-logic\n", ""), "缺 provenance_strength 声明"),
            "强度越词表": (HEALTHY.replace("provenance_strength: domain-logic", "provenance_strength: 强证据"), "越词表"),
            "强度不自洽": (HEALTHY.replace("provenance_strength: domain-logic", "provenance_strength: external"),
                           "但外部覆盖仅"),
        }
        for label, (text, expect) in cases.items():
            path = variant(work, "case-" + label, text)
            parity(rep, f"problems · {label}", snap, cli, cwd, ["--asset", path], expect_rc=1, must_contain=expect)

        # ————— 退出码口径
        parity(rep, "错误面 · 未知目标 → exit 1", snap, cli, cwd, ["--asset", good, "--target", "不存在XYZ"],
               expect_rc=1, must_contain="检索词不在图中")
        parity(rep, "错误面 · 未知分支 → exit 2", snap, cli, cwd, ["--asset", good, "--branch", "不存在分支"],
               expect_rc=2, must_contain="未知分支")
        parity(rep, "错误面 · 未知序 → exit 2", snap, cli, cwd, ["--asset", good, "--order", "不存在序"],
               expect_rc=2, must_contain="资产内无该序")
        parity(rep, "错误面 · 资产缺件 → exit 1", snap, cli, cwd, ["--asset", str(work / "不存在.md")],
               expect_rc=1, must_contain="概念图资产不存在")
        parity(rep, "错误面 · 无 concept_graph 块 → exit 1", snap, cli, cwd,
               ["--asset", variant(work, "noblock", "# 只有散文\n")], expect_rc=1,
               must_contain="机器可读块")

        # ————— 未登记资产的自检走「通用判据」退化路径
        out = parity(rep, "自检 · 未登记资产退化为通用判据", snap, cli, cwd, ["--asset", good, "--check"],
                     expect_rc=0, must_contain="未登记键级样例")
        rep.check("自检 · 通用判据确实跑了确定性 + 逆序负例",
                  "确定性：同输入两次求值逐字节一致" in out.decode("utf-8", "replace")
                  and "逆序序列的违反边非零" in out.decode("utf-8", "replace"),
                  "缺通用判据条目")

        # ————— 真仓两面（登记资产的键级样例路径）
        for extra in ([], ["--list"], ["--ready-list", "--loaded", "C00,C01"], ["--json"]):
            parity(rep, "真仓 · 默认资产 " + (" ".join(extra) or "（默认目标）"), snap, cli, cwd, extra,
                   expect_rc=0)
        parity(rep, "真仓 · QUANT_GRAPH --check", snap, cli, cwd,
               ["--check", "--asset", "community/量化金融域包/assets/QUANT_GRAPH.md"], expect_rc=0)
    finally:
        if args.keep:
            print(f"（合成树保留：{work}）")
        else:
            shutil.rmtree(work, ignore_errors=True)
    print(f"== 汇总：通过 {rep.passed} · 失败 {rep.failed} ==")
    return 0 if rep.failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
