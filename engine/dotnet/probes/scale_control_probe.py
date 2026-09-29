#!/usr/bin/env python3
"""规模受控性探针：语料放大到数百包后，注入一个缺陷还能被抓到吗。

为什么单开一面：scale_probe.py 回答的是「放大后还一致吗」；没有一面回答
「放大后还灵敏吗」——一致可能靠「两边一起瞎」达成，灵敏度只能靠注入缺陷来证。

本探针把快照克隆成数百包，然后逐个注入并断言判定翻转：
  ① 篡改 protocol/RECEIPTS.json 一条叶子摘要 → 聚合门必须 FAIL（回执分量）
  ② 篡改 library/RECEIPTS.json 一条叶子摘要 → 聚合门必须 FAIL（馆藏分量）
  ③ 契约边界漂移（改一个**已登记**社区模块 machine_contract 的 layer 位）→ 聚合门必须 FAIL
     （载体系 `module-signature`：边界七字段与冻结基线比对）
     ★ 同时如实记录**范围边界**：同一改动落在**未登记**的克隆包上不会翻红——不是因为判定失灵，
       而是"未登记即无冻结基线"，该包不在判定面内（克隆包只进全仓扫描面，不进 registry 面）。
  ④ 撞号注入（两包声明同一 module id）→ 默认模式与 Python 同口径（合法·静默塌陷），
     --strict-coherence 必须 DENY（ISA v1 C1′ 是可用开关）
每注入一处都会原样还原，并在最后断言还原后门重新变绿（防「注完忘了还原」）。

用法：
    python probes/scale_control_probe.py --snapshot <隔离快照> --cli <nf-dotnet> [--packs 300]

退出码：0 全部受控；1 有未受控项。
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

SOURCE_PACK = "AI农业域包"


def clone_packs(work: Path, count: int) -> int:
    src = work / "community" / SOURCE_PACK
    made = 0
    for i in range(1, count + 1):
        name, prefix = "规模P%d域包" % i, "规模P%d" % i
        dst = work / "community" / name
        if dst.exists():
            continue
        shutil.copytree(src, dst)
        for path in dst.rglob("*"):
            if not path.is_file():
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            path.write_text(text.replace(SOURCE_PACK, name).replace("AI农业", prefix),
                            encoding="utf-8", newline="\n")
        made += 1
    return made


def gate(cli: str, root: Path, extra: list[str] | None = None) -> tuple[int, str, float]:
    cmd = [cli, "--root", str(root)] + (extra or []) + ["verify"]
    start = time.time()
    p = subprocess.run(cmd, capture_output=True)
    return p.returncode, (p.stdout or b"").decode("utf-8", "replace"), time.time() - start


def failing_lines(out: str) -> list[str]:
    # 控制台在 Windows 上多为 GBK，✗ 无法编码——统一改写成 ASCII 前缀，避免探针自己崩
    rows = []
    for line in out.splitlines():
        s = line.strip()
        if s.startswith("✗"):
            rows.append("FAIL: " + s.lstrip("✗ ").strip())
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--snapshot", required=True)
    ap.add_argument("--cli", required=True)
    ap.add_argument("--packs", type=int, default=300)
    ap.add_argument("--keep", action="store_true")
    args = ap.parse_args()

    snap = Path(args.snapshot).resolve()
    work = snap.parent / (snap.name + "-control")
    if work.exists():
        shutil.rmtree(work)
    shutil.copytree(snap, work)
    made = clone_packs(work, args.packs)
    packs_now = len([p for p in (work / "community").iterdir() if p.is_dir()])
    print("样板快照：%s\n探针副本：%s\n社区包 %d → %d（克隆 %d）\n"
          % (snap, work, packs_now - made, packs_now, made))

    # 三元结果：True 受控 / False 未受控 / None 范围声明（不计入失败）
    checks: list[tuple[str, bool | None, str]] = []
    rc0, _out0, sec0 = gate(args.cli, work)
    checks.append(("基线 · 放大后门仍全绿", rc0 == 0, "exit=%d · %.1fs" % (rc0, sec0)))

    # ① 协议回执篡改
    rec = work / "protocol" / "RECEIPTS.json"
    orig = rec.read_bytes()
    doc = json.loads(orig.decode("utf-8"))
    entries = doc.get("entries") or []
    if entries:
        entries[0]["digest"] = "0" * 8 + str(entries[0]["digest"])[8:]
        rec.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
        rc1, out1, sec1 = gate(args.cli, work)
        hits = failing_lines(out1)
        checks.append(("① 协议回执叶子摘要篡改 · 必被抓",
                       rc1 != 0 and any("RECEIPTS" in l or "回执" in l for l in hits),
                       "exit=%d · %.1fs · %s" % (rc1, sec1, (hits or ["（无失败行）"])[0][:70])))
        rec.write_bytes(orig)
    else:
        checks.append(("① 协议回执叶子摘要篡改 · 必被抓", False, "回执件无 entries，注入无效"))

    # ② 馆藏回执篡改
    lib = work / "library" / "RECEIPTS.json"
    orig_lib = lib.read_bytes()
    ldoc = json.loads(orig_lib.decode("utf-8"))
    lentries = ldoc.get("entries") or []
    if lentries:
        lentries[0]["digest"] = "0" * 8 + str(lentries[0]["digest"])[8:]
        lib.write_text(json.dumps(ldoc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
        rc2, out2, sec2 = gate(args.cli, work)
        hits2 = failing_lines(out2)
        checks.append(("② 馆藏回执叶子摘要篡改 · 必被抓",
                       rc2 != 0 and any("RECEIPTS" in l or "馆藏" in l or "library" in l for l in hits2),
                       "exit=%d · %.1fs · %s" % (rc2, sec2, (hits2 or ["（无失败行）"])[0][:70])))
        lib.write_bytes(orig_lib)
    else:
        checks.append(("② 馆藏回执叶子摘要篡改 · 必被抓", False, "馆藏回执无 entries，注入无效"))

    # ③ 契约边界漂移（改 layer 位）——必须打在**已登记**包上才有基线可比
    mods = sorted((work / "community" / SOURCE_PACK / "modules").glob("*.md"))
    if mods:
        target = mods[0]
        orig_doc = target.read_bytes()
        text = orig_doc.decode("utf-8").replace("layer: P40", "layer: P99", 1)
        target.write_text(text, encoding="utf-8", newline="\n")
        rc3, out3, sec3 = gate(args.cli, work)
        hits3 = failing_lines(out3)
        checks.append(("③ 契约边界漂移（已登记包 · layer 位）· 必被抓", rc3 != 0,
                       "exit=%d · %.1fs · %s" % (rc3, sec3, (hits3 or ["（无失败行）"])[0][:78])))
        target.write_bytes(orig_doc)
    else:
        checks.append(("③ 契约边界漂移（已登记包 · layer 位）· 必被抓", False, "找不到注入目标模块"))

    # ⑤ 同一改动落在未登记克隆包上 → 不翻红：这是**范围声明**，不是失灵
    clone_mods = sorted((work / "community" / "规模P1域包" / "modules").glob("*.md"))
    if clone_mods:
        ctarget = clone_mods[0]
        corig = ctarget.read_bytes()
        ctext = corig.decode("utf-8").replace("layer: P40", "layer: P99", 1)
        ctarget.write_text(ctext, encoding="utf-8", newline="\n")
        rc5, _out5, _ = gate(args.cli, work)
        ctarget.write_bytes(corig)
        checks.append(("⑤ 范围声明 · 未登记克隆包无冻结基线，故不进判定面", None,
                       "exit=%d（预期 0；克隆包只进全仓扫描面，不进 registry 面）" % rc5))
    else:
        checks.append(("⑤ 范围声明 · 未登记克隆包无冻结基线，故不进判定面", None, "无克隆包可测"))

    # ④ 撞号注入：让 规模P2 域包改称 规模P1 的模块 id
    p2 = work / "community" / "规模P2域包"
    backups: list[tuple[Path, bytes]] = []
    for path in list((p2 / "modules").glob("*.md")) + [p2 / "protocol.yaml"]:
        if path.is_file():
            backups.append((path, path.read_bytes()))
            path.write_text(path.read_bytes().decode("utf-8").replace("规模P2:", "规模P1:"),
                            encoding="utf-8", newline="\n")
    packs_arg = ["combine", "plan", "--packs", "规模P1域包,规模P2域包"]
    rc4d, _o4d, _ = gate(args.cli, work, extra=packs_arg)
    rc4s, out4s, _ = gate(args.cli, work, extra=packs_arg + ["--strict-coherence"])
    checks.append(("④ 撞号 · 默认模式与 Python 同口径（合法·静默塌陷）", rc4d == 0, "exit=%d" % rc4d))
    hits4 = failing_lines(out4s)
    checks.append(("④ 撞号 · --strict-coherence 判 DENY（C1′ 是可用开关）", rc4s != 0,
                   "exit=%d · %s" % (rc4s, (hits4 or ["（无失败行）"])[0][:70])))
    for path, blob in backups:
        path.write_bytes(blob)

    rc9, _out9, sec9 = gate(args.cli, work)
    checks.append(("还原后 · 门重新变绿（防注完忘还原）", rc9 == 0, "exit=%d · %.1fs" % (rc9, sec9)))

    print("| # | 判定项 | 结果 | 证据 |")
    print("|---|---|---|---|")
    for name, ok, ev in checks:
        verdict = "通过" if ok is True else ("**未受控**" if ok is False else "范围声明")
        print("| | %s | %s | %s |" % (name, verdict, ev))
    failed = [c for c in checks if c[1] is False]
    print("\n结论：%s" % ("全部受控——放大后注入仍被抓，且还原后门回绿" if not failed
                        else "未受控 %d 项" % len(failed)))
    if not args.keep:
        shutil.rmtree(work, ignore_errors=True)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
