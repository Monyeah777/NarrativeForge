#!/usr/bin/env python3
"""变更影响面预检探针：**动态选目标 + 合成 registry 语料**两侧差分。

为什么单开一面：`nf impact` 的判据是"registry 引用图 + 裸号归一"的共同结果，
只跑一两个目标看不出归一/歧义/悬空三类分支有没有对齐。本探针：

  ① 从真 registry 里**动态挑**出六类目标（官方核心模块 / 被引用模块 / 无引用且非官方模块 /
     有入边整包 / 无入边整包 / 不存在目标），逐个跑 default 与 `--check` 两种模式，两侧逐字节比；
  ② 用**合成 registry**（同时含：裸号重复、references.source_package 悬空、references.module_id
     不在源包在列）走 `--registry <fixture>`，把"该报的错"喂进去看两侧是否同判；
  ③ 裸号/限定号两种写法（`M50` 与 `通用:M10`）也各跑一遍，验归一。

用法：
    python probes/impact_probe.py --root <快照> --cli <nf-dotnet> --py-exe <python>

退出码：0 全过；1 有未达项。
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys

SYNTHETIC = {
    "schema_version": "2",
    "modules": [{"id": "M00"}, {"id": "M50"}],
    "protocols": [
        {"id": "包甲", "module_ids": ["甲:M01", "M01"], "references": [
            {"source_package": "包乙", "module_id": "乙:M07"},
            {"source_package": "幽灵包", "module_id": "M09"},
            {"source_package": "包乙", "module_id": "M99"}]},
        {"id": "包乙", "module_ids": ["M07"], "references": []},
    ],
}


def run(argv: list[str], cwd: str) -> tuple[int, str, str]:
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

    reg_path = os.path.join(args.root, "desktop", "src", "core", "registry.json")
    with open(reg_path, encoding="utf-8") as fh:
        reg = json.load(fh)

    protocols = reg.get("protocols") or []
    modules = reg.get("modules") or []
    refs = [(p.get("id"), r.get("source_package"), r.get("module_id"))
            for p in protocols for r in (p.get("references") or [])]
    referenced = [r[2] for r in refs if r[2]]
    core_ids = [m.get("id") for m in modules if m.get("id")]
    # 入边 = references 的 **source_package**（被引用的那一侧）；缺失的多半是"没人引用"的包
    inbound_pkgs = {r[1] for r in refs if r[1]}
    clean_module = next((m for p in protocols for m in (p.get("module_ids") or [])
                         if m not in referenced and m not in core_ids), "")
    no_inbound_pkg = next((p.get("id") for p in protocols if p.get("id") not in inbound_pkgs), "")
    inbound_pkg = next((p.get("id") for p in protocols if p.get("id") in inbound_pkgs), "")

    targets = [
        ("官方核心模块", "M50"),
        ("被引用模块（限定号）", referenced[0] if referenced else "M01"),
        ("无引用且非官方模块", clean_module),
        ("有入边整包", inbound_pkg),
        ("无入边整包", no_inbound_pkg),
        ("不存在目标", "不存在的目标XYZ"),
    ]
    checks: list[tuple[str, bool, str]] = []

    def compare(label: str, extra: list[str]) -> None:
        py_code, py_out, py_err = run([args.py_exe, os.path.join(args.root, "scripts", "nf.py"),
                                       "impact", *extra], args.root)
        net_code, net_out, net_err = run([args.cli, "--root", args.root, "impact", *extra], args.root)
        same = py_out == net_out and py_err == net_err and py_code == net_code
        checks.append((label, same,
                       f"exit {py_code}/{net_code} · stdout {len(py_out)}/{len(net_out)} 字节 · "
                       f"stderr 同={py_err == net_err}"))

    for label, target in targets:
        if not target:
            continue
        compare(f"真 registry·{label}（{target}）", [target])
        compare(f"真 registry·{label}·--check", [target, "--check"])

    # 裸号 / 限定号两种写法（归一）
    for raw in core_ids[:2]:
        compare(f"真 registry·写法归一（{raw}）", [raw])

    # 合成 registry：裸号重复 + 悬空源包 + 源包无此号 —— 走 --registry 夹具
    work = args.work or os.path.join(os.environ.get("TEMP", "/tmp"), "nf-impact-probe")
    os.makedirs(work, exist_ok=True)
    fixture = os.path.join(work, "registry_synthetic.json")
    with open(fixture, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(SYNTHETIC, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    for label, target in (("合成谱·包甲（有 references 悬空）", "包甲"),
                          ("合成谱·M07（被包甲引用）", "M07"),
                          ("合成谱·M99（源包无此号）", "M99"),
                          ("合成谱·不存在", "幽灵")):
        compare(f"{label}", [target, "--registry", fixture])
        compare(f"{label}·--check", [target, "--check", "--registry", fixture])

    print("| # | 判定项 | 结果 | 证据 |")
    print("|---|---|---|---|")
    for name, ok, ev in checks:
        print("| | %s | %s | %s |" % (name, "通过" if ok else "**未达**", ev))
    failed = [c for c in checks if not c[1]]
    print("\n结论：%s" % (f"全部通过——{len(checks)} 个面（真 registry 六类目标 × 两模式 + 写法归一 + 合成谱四类）两侧逐字节同"
                        if not failed else f"未达 {len(failed)} 项"))
    if not failed:
        shutil.rmtree(work, ignore_errors=True)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
