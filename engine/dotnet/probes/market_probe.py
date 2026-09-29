#!/usr/bin/env python3
"""市场面探针：`market --list`（分级目录）与 `related`（See-Also 关联）两侧差分。

为什么单开一面：这两面的判据是"分级规则 + 引用图 + 模块级依赖图"三者叠加，
只跑一两个目标看不出分支。本探针：
  ① 真 registry：`--list`（全量 / 三种 tier）各跑文本与 `--json`；
  ② 真 registry：`related` 对**动态挑出**的包（有 references / 无 references）与模块
     （官方核心 / 社区 / 被依赖）各跑文本与 `--json`；
  ③ **合成 registry**（`--registry <fixture>`）：专造 M91-M99 实验段、带前缀官方号、
     链式 references —— 验分级与关联边（两侧图都取自同一 --root，只有 registry 不同）。

用法：
    python probes/market_probe.py --root <快照> --cli <nf-dotnet> --py-exe <python>

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
    "modules": [{"id": "M00", "name": "数据结构"}, {"id": "通用:M10", "name": "时间推进"},
                {"id": "事件:M22", "name": "事件总线"}],
    "protocols": [
        {"id": "合成甲包", "name": "合成甲", "version": "2.0.0",
         "module_ids": ["甲:M91", "甲:M92"], "references": []},
        {"id": "合成乙包", "name": "合成乙",
         "module_ids": ["乙:M01", "通用:M10"], "references": [
             {"source_package": "合成甲包", "module_id": "甲:M91"}]},
        {"id": "合成丙包", "name": "合成丙",
         "module_ids": ["丙:M01"], "references": [
             {"source_package": "合成乙包", "module_id": "乙:M01"}]},
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

    with open(os.path.join(args.root, "desktop", "src", "core", "registry.json"),
              encoding="utf-8") as fh:
        reg = json.load(fh)
    protocols = reg.get("protocols") or []
    refs = {r.get("source_package") for p in protocols for r in (p.get("references") or [])}
    with_refs = next((p.get("id") for p in protocols if p.get("id") in refs), "")
    without_refs = next((p.get("id") for p in protocols if p.get("id") not in refs), "")
    core_mod = next((m.get("id") for m in (reg.get("modules") or []) if m.get("id")), "M00")
    community_mod = next((m for p in protocols for m in (p.get("module_ids") or [])), "M01")
    referenced_mod = next((r.get("module_id") for p in protocols
                           for r in (p.get("references") or []) if r.get("module_id")), "M01")

    checks: list[tuple[str, bool, str]] = []

    def compare(label: str, extra: list[str]) -> None:
        py_code, py_out, py_err = run([args.py_exe, os.path.join(args.root, "scripts", "nf.py"), *extra],
                                      args.root)
        net_code, net_out, net_err = run([args.cli, "--root", args.root, *extra], args.root)
        same = py_out == net_out and py_err == net_err and py_code == net_code
        checks.append((label, same,
                       f"exit {py_code}/{net_code} · stdout {len(py_out)}/{len(net_out)} 字节 · "
                       f"stderr 同={py_err == net_err}"))

    # ① 目录视图：全量 + 三种 tier ×（文本 / JSON）
    compare("真 registry·market --list（文本）", ["market", "--list"])
    compare("真 registry·market --list --json", ["market", "--list", "--json"])
    for tier in ("official", "community", "experimental"):
        compare(f"真 registry·market --list --tier {tier}", ["market", "--list", "--tier", tier])
        compare(f"真 registry·market --list --tier {tier} --json", ["market", "--list", "--tier", tier, "--json"])

    # ② related：包 / 模块 / 不存在 ×（文本 / JSON）
    for label, target in (("有 references 的包", with_refs), ("无 references 的包", without_refs),
                          ("官方核心模块", core_mod), ("社区模块", community_mod),
                          ("被引用模块", referenced_mod), ("不存在目标", "不存在的目标XYZ")):
        if not target:
            continue
        compare(f"真 registry·related·{label}（{target}）", ["related", target])
        compare(f"真 registry·related·{label}·--json", ["related", target, "--json"])

    # ③ 合成 registry（--registry）：实验段 / 前缀官方号 / 链式 references
    work = args.work or os.path.join(os.environ.get("TEMP", "/tmp"), "nf-market-probe")
    os.makedirs(work, exist_ok=True)
    fixture = os.path.join(work, "registry_synthetic.json")
    with open(fixture, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(SYNTHETIC, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    compare("合成谱·market --list（实验段/前缀官方号）", ["market", "--list", "--registry", fixture])
    compare("合成谱·market --list --tier experimental", ["market", "--list", "--tier", "experimental",
                                                          "--registry", fixture])
    for target in ("合成甲包", "合成乙包", "甲:M91", "通用:M10", "M00"):
        compare(f"合成谱·related {target}", ["related", target, "--registry", fixture])
        compare(f"合成谱·related {target} --json", ["related", target, "--json", "--registry", fixture])

    # ④ 包视图（依赖闭包 + 挂载冲突）：真语料若干包 ×（文本 / JSON）
    for pkg in ("community/校园西幻轻混组合包", "community/校园情感领域包", "community/AI农业域包",
                "community/不存在的包XYZ"):
        compare(f"真语料·market {pkg}", ["market", pkg])
        compare(f"真语料·market {pkg} --json", ["market", pkg, "--json"])

    # ⑤ 合成语料（副本树）：闭包叶越界 / 源包嵌套 references / 挂载层冲突 / 未在 02 §8 在册
    copy = os.path.join(work, "tree")
    if os.path.isdir(copy):
        shutil.rmtree(copy)
    os.makedirs(copy)
    for rel in ("scripts", os.path.join("desktop", "src"), "protocol"):
        shutil.copytree(os.path.join(args.root, rel), os.path.join(copy, rel))
    os.makedirs(os.path.join(copy, "community"), exist_ok=True)

    def write_pack(name, deps_core, refs, mount_default, nested_refs=None):
        d = os.path.join(copy, "community", name)
        os.makedirs(d, exist_ok=True)
        lines = ["protocol:", "  schema_version: \"2\"", "package:", f"  id: {name}",
                 f"  version: \"1.0.0\"", "  module_id_range:",
                 f"    - \"{name[:4]}:M01\"", "  dependencies:", "    core_only: true",
                 "    core_modules: [" + ", ".join(deps_core) + "]",
                 "    cross_package: []", "  references:"]
        for r in refs or []:
            lines += [f"    - source_package: {r[0]}", f"      module_id: {r[1]}"]
        if not refs:
            lines[-1] = "  references: []"
        lines += ["  modules:", f"    - id: \"{name[:4]}:M01\"", "      desc: 合成包",
                  "  mount_layers:", f"    P40 行为决策: {{default: [{mount_default}], available: []}}"]
        with open(os.path.join(d, "protocol.yaml"), "w", encoding="utf-8", newline="\n") as fh:
            fh.write("\n".join(lines) + "\n")
        return d

    write_pack("合成组合包", ["M00"], [("合成源包", "M07")], "合成:M01")
    # 源包自身带 package 层 references → 触发「不支持多层组合」；其 core_modules 含 M99 → 触发叶越界
    write_pack("合成源包", ["M00", "M99"], [("合成未登记包", "M07")], "合成:M01")
    write_pack("合成未登记包", ["M00"], [], "合成未登记:M01")

    synth_reg = {"schema_version": "2", "modules": [],
                 "protocols": [{"id": "合成组合包", "module_ids": ["合成:M01"],
                                "references": [{"source_package": "合成源包", "module_id": "合成源:M07"}]},
                               {"id": "合成源包", "module_ids": ["合成源:M07"], "references": []},
                               {"id": "合成未登记包", "module_ids": ["合成未登记:M01"]}]}
    with open(os.path.join(copy, "desktop", "src", "core", "registry.json"), "w",
              encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(synth_reg, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    # 02 文档：只登记「合成组合包」与「合成源包」，故意不登记「合成未登记包」
    with open(os.path.join(copy, "02_联动注册表.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("### 8.1 合成组合包（组合包）\n\n合成组合包\n\n### 8.2 合成源包（域包）\n\n合成源包\n\n## 9. 附录\n")

    for pkg in ("community/合成组合包", "community/合成未登记包", "community/不存在的包"):
        for extra in ([], ["--json"]):
            py_code, py_out, py_err = run([args.py_exe, os.path.join(copy, "scripts", "nf.py"),
                                           "market", pkg, *extra], copy)
            net_code, net_out, net_err = run([args.cli, "--root", copy, "market", pkg, *extra], copy)
            same = py_out == net_out and py_err == net_err and py_code == net_code
            checks.append((f"合成副本·market {pkg}{' --json' if extra else ''}", same,
                           f"exit {py_code}/{net_code} · stdout {len(py_out)}/{len(net_out)} 字节 · "
                           f"stderr 同={py_err == net_err}"))

    print("| # | 判定项 | 结果 | 证据 |")
    print("|---|---|---|---|")
    for name, ok, ev in checks:
        print("| | %s | %s | %s |" % (name, "通过" if ok else "**未达**", ev))
    failed = [c for c in checks if not c[1]]
    print("\n结论：%s" % (f"全部通过——{len(checks)} 面（目录视图 + related + 合成谱 + 包视图四类）两侧逐字节同"
                        if not failed else f"未达 {len(failed)} 项"))
    if not failed:
        shutil.rmtree(work, ignore_errors=True)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
