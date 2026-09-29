"""**交接件体检**：交付件「异地可跑」+ 文档「现状数字 = 实测」。

两件事各自都会咬人：

1. **异地可跑**——把 `run-gate.ps1` 与当片 `dist/` 复制到临时目录，用**显式 -Root / -Cli** 跑门；
   若工具链里藏着指向本机 `Downloads` 的绝对路径依赖，这一步就会暴露（交付件必须能换机器跑）。
2. **文档现状数字自洽**——README 的「现成规模」行、对账表页脚、覆盖率矩阵「当前计数」三处都声称
   「当前」数字；它们最容易在连轴推进时落后于实测（第一百零九片实测：README 仍写 177 面 / 218 例 / 34 探针，
   而实测已是 183 / 227 / 37）。本探针把「文档声称」与「实测」逐条比，不一致即 FAIL 并给出改法提示。

用法：
    python probes/handoff_integrity_probe.py --snap <快照> --cli <当片 dist/nf-dotnet.exe>
        [--probes <probes 目录>] [--readme <README>] [--docs-dir <Downloads>] [--faces N] [--skip-relocate]
"""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # noqa: BLE001
    pass
sys.dont_write_bytecode = True

import _paths  # 默认路径唯一出处（探针可移植）
ENGINE = _paths.ENGINE
DEFAULT_SNAP = _paths.SNAP
DEFAULT_CLI = str(ENGINE / "dist/nf-dotnet-win-x64-f105-2026-09-28/nf-dotnet.exe")
DEFAULT_DOCS = _paths.RECORDS_DIR
_CN_DIGITS = {"零": 0, "一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9}


def cn_number(text: str) -> int:
    """中文数字 → int（覆盖到「一百二十一」这一级；够本项目用）。"""
    if not text:
        return -1
    total, section, number = 0, 0, 0
    for ch in text:
        if ch in _CN_DIGITS:
            number = _CN_DIGITS[ch]
        elif ch == "十":
            section += (number or 1) * 10
            number = 0
        elif ch == "百":
            section += (number or 1) * 100
            number = 0
        else:
            return -1
    return total + section + number


def newest_dist() -> int:
    best = -1
    for d in (ENGINE / "dist").glob("nf-dotnet-win-x64-f*-*"):
        m = re.search(r"-f(\d+)-", d.name)
        if m:
            best = max(best, int(m.group(1)))
    return best


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--snap", default=DEFAULT_SNAP)
    ap.add_argument("--cli", default=DEFAULT_CLI)
    ap.add_argument("--probes", default=str(ENGINE / "probes"))
    ap.add_argument("--readme", default=str(ENGINE / "README.md"))
    ap.add_argument("--docs-dir", default=DEFAULT_DOCS)
    ap.add_argument("--faces", type=int, default=0, help="面级实测面数（不给则只比其余三项）")
    ap.add_argument("--skip-relocate", action="store_true")
    args = ap.parse_args()

    snap = Path(args.snap)
    cli = Path(args.cli)
    probes_dir = Path(args.probes)
    problems = []

    # ── ① 异地可跑：工具链复制到临时目录，显式参数跑门
    if not args.skip_relocate:
        with tempfile.TemporaryDirectory(prefix="nf-relocate-") as tmp:
            kit = Path(tmp) / "kit"
            kit.mkdir(parents=True)
            shutil.copyfile(ENGINE / "run-gate.ps1", kit / "run-gate.ps1")
            shutil.copytree(probes_dir, kit / "probes")
            shutil.copytree(cli.parent, kit / cli.parent.name)
            moved_cli = kit / cli.parent.name / cli.name
            gate = subprocess.run(["pwsh", "-NoProfile", "-File", str(kit / "run-gate.ps1"),
                                   "-Root", str(snap), "-Cli", str(moved_cli),
                                   "-Baseline", str(kit / "bench-baseline.json")],
                                  capture_output=True, timeout=3600)
            gate_out = gate.stdout.decode("utf-8", "replace")
            verdict = "PASS" if "== NF .NET 门：PASS ==" in gate_out else "FAIL"
            print(f"① 异地可跑（工具链在 {kit.parent.name}/ · 显式 -Root/-Cli）：exit={gate.returncode} · {verdict}")
            if gate.returncode != 0:
                tail = "\n".join(gate_out.strip().splitlines()[-6:])
                problems.append(f"异地跑门未通过：exit={gate.returncode}\n{tail}")
            faces = subprocess.run([sys.executable, "-X", "utf8", str(kit / "probes" / "face_parity_probe.py"),
                                    "--root", str(snap), "--py-exe", sys.executable, "--cli", str(moved_cli)],
                                   capture_output=True, timeout=3600)
            line = next((l.strip() for l in faces.stdout.decode("utf-8", "replace").splitlines()
                         if "面级对账" in l), "（未取到）")
            print(f"   异地面级对账：exit={faces.returncode} · {line}")
            if faces.returncode != 0:
                problems.append("异地跑面级对账未全绿")
            m = re.search(r"面级对账：(\d+) 面", line)
            if m:
                args.faces = args.faces or int(m.group(1))

    # ── ② 实测数字
    proc = subprocess.run([str(cli), "--root", str(snap), "selftest", "--json"],
                          capture_output=True, timeout=1800)
    import json
    measured_cases = len(json.loads(proc.stdout.decode("utf-8", "replace"))["rows"])
    # 探针 = 不以 `_` 开头的 *.py（`_paths.py` 是辅助模块，不是判据）
    measured_probes = len([p for p in probes_dir.glob("*.py") if not p.name.startswith("_")])
    measured_dist = newest_dist()
    print(f"② 实测：自检 {measured_cases} 例 · 探针 {measured_probes} 个 · 最新交付形态 f{measured_dist}"
          + (f" · 面级 {args.faces} 面" if args.faces else ""))

    # ── ③ 文档声称
    readme = Path(args.readme).read_text(encoding="utf-8-sig")
    scale = re.search(r"现成规模\*\*：CLI \*\*(\d+) 面逐字节全同 \+ (\d+) 边界面\*\*.*?"
                      r"自检 \*\*(\d+) 例\*\*.*?全量探针 \*\*(\d+) 个\*\*", readme, re.S)
    if not scale:
        problems.append("README 里找不到「现成规模」行（或格式变了）——请保持该行可解析")
    else:
        doc_faces, doc_boundary, doc_cases, doc_probes = (int(scale.group(1)), int(scale.group(2)),
                                                          int(scale.group(3)), int(scale.group(4)))
        print(f"③ README 现成规模：面 {doc_faces}+{doc_boundary} 边界 · 自检 {doc_cases} 例 · 探针 {doc_probes} 个")
        for label, doc, real in (("面级", doc_faces, args.faces), ("自检", doc_cases, measured_cases),
                                 ("探针", doc_probes, measured_probes)):
            if real and doc != real:
                problems.append(f"README 现成规模的「{label}」与实测不符：文档 {doc} / 实测 {real}")

    # 交付形态行：README 里按片累加了很多行，**取最大 fNN**（= 最新当片形态），不是第一处匹配
    dist_claims = [int(m) for m in re.findall(r"x64-f(\d+)-", readme)]
    if dist_claims and max(dist_claims) != measured_dist:
        problems.append(f"README 交付形态 f{max(dist_claims)} 与最新 dist f{measured_dist} 不符")

    sections = re.findall(r"## 第([一二三四五六七八九十百零]+)片", readme)
    readme_slice = cn_number(sections[-1]) if sections else -1
    foot = (Path(args.docs_dir) / "NF_NET引擎_双跑对账表_v1.md").read_text(encoding="utf-8-sig")
    matrix = (Path(args.docs_dir) / "NF_NET引擎_门禁覆盖率矩阵_v1.md").read_text(encoding="utf-8-sig")
    # **只看页脚那一行**：正文里每个分片都有「N 探针全绿」（历史值，本就该不同），拿全文搜会误判
    foot_lines = [l for l in foot.splitlines() if l.startswith("*v1 ｜ 编制日")]
    foot_footer = foot_lines[-1] if foot_lines else foot
    foot_slice_m = re.search(r"（\*\*第([一二三四五六七八九十百零]+)片\*\*", foot_footer)
    foot_slice = cn_number(foot_slice_m.group(1)) if foot_slice_m else -1
    foot_probes_m = re.search(r"\*\*([一二三四五六七八九十百零]+)探针全绿\*\*", foot_footer)
    foot_probes = cn_number(foot_probes_m.group(1)) if foot_probes_m else -1
    matrix_slice_m = re.search(r"当前计数（第([一二三四五六七八九十百零]+)片后）", matrix)
    matrix_slice = cn_number(matrix_slice_m.group(1)) if matrix_slice_m else -1
    print(f"④ 文档片号：README 最新分片 {readme_slice} · 对账表页脚 {foot_slice} · 矩阵当前计数 {matrix_slice}"
          + (f" · 页脚探针 {foot_probes}" if foot_probes >= 0 else ""))
    if not (readme_slice == foot_slice == matrix_slice):
        problems.append(f"三处「当前」片号不一致：README {readme_slice} / 对账表 {foot_slice} / 矩阵 {matrix_slice}")
    if foot_probes >= 0 and foot_probes != measured_probes:
        problems.append(f"对账表页脚探针数 {foot_probes} 与实测 {measured_probes} 不符")

    if problems:
        print("FAIL:")
        for p in problems:
            print("  -", p)
        print("\n改法提示：把文档里的陈旧数字改成实测值（README「现成规模」行 / 交付形态行 / "
              "对账表页脚片号与探针数 / 矩阵「当前计数」片号）。")
        return 1
    print("OK: 交接件体检通过（异地可跑 + 文档现状数字 = 实测）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
