"""**不倒退判据**：把项目纪律「基线只增不减」从文档口号变成机检。

仓库与月计划里反复写着「门禁基线 PASS 只增不减」，但此前**没有任何判据挡着倒退**——
一次误删一面、一例自检、或悄悄把某条契约挪进「范围外」，全绿照样是绿的。本探针对
**五类可数基线**做单向比较（只许涨，不许跌）：

  ① 一致性**已移植契约集合**：必须 ⊇ 基线（少一条即红）；**范围外条目**只许减不许增；
  ② **负例自检例数**：≥ 基线；
  ③ **判据探针条数**：≥ 基线（且清单 ↔ 磁盘一致，排除 `_` 开头的辅助模块）；
  ④ **面级对账面数**（`face_parity` 的 `FACES` / `BOUNDARY_FACES` 条数，静态读表）：≥ 基线；
  ⑤ **一致性契约总数**：≥ 基线（新增契约是进步，减少是倒退）。

另带**自证**：把基线里任意一个数字人为抬高 1 后重跑同一套比较，**必须判红**——否则
这条判据本身不可信（沿用本工程「先证它能红」的纪律）。

基线文件 = `api/no_regression_baseline.json`（有意变更才 `--update`）。

用法：
    python probes/no_regression_probe.py --engine <引擎> --snap <语料> --cli <nf-dotnet>
        [--baseline <路径>] [--update]
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # noqa: BLE001
    pass
sys.dont_write_bytecode = True

import _paths  # 默认路径唯一出处（探针可移植）
import subprocess

DEFAULT_BASELINE = str(_paths.ENGINE / "api" / "no_regression_baseline.json")


def run_json(cmd: list[str], timeout: int = 900):
    p = subprocess.run(cmd, capture_output=True, timeout=timeout)
    if p.returncode not in (0, 1):  # conformance 等命令允许 exit 1（有问题但报告仍可解析）
        raise RuntimeError(f"命令失败 exit={p.returncode}：{' '.join(cmd)}")
    return json.loads(p.stdout.decode("utf-8", "replace"))


def load_face_counts(engine: Path) -> tuple[int, int]:
    """静态读 `face_parity_probe.py` 的两张面表（导入模块只取常量，不执行 main）。"""
    target = engine / "probes" / "face_parity_probe.py"
    spec = importlib.util.spec_from_file_location("_face_parity_for_count", target)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return len(mod.FACES), len(mod.BOUNDARY_FACES)


def measure(engine: Path, snap: str, cli: str) -> dict:
    conf = run_json([cli, "--root", snap, "conformance", "--json"])
    ported = sorted(c["id"] for c in conf.get("ported", []))
    # 引擎侧把「已裁定范围外」表现为 `unported`（真源的 out_of_scope ↔ 本引擎的未移植集合）
    unported = sorted(conf.get("unported", []) or [])
    st = run_json([cli, "--root", snap, "selftest", "--json"])
    manifest = json.loads((engine / "probes" / "probe_manifest.json").read_text(encoding="utf-8"))
    probes = [p["name"] for p in manifest["probes"]]
    disk = sorted(p.name for p in (engine / "probes").glob("*.py") if not p.name.startswith("_"))
    faces, boundary = load_face_counts(engine)
    return {
        "conformance_total": int(conf.get("passed", 0)) + len(unported),
        "conformance_ported": ported,
        "conformance_unported": unported,
        "selftest_cases": len(st.get("rows", [])),
        "probes": len(probes),
        "probe_scripts_on_disk": len(disk),
        "face_parity_faces": faces,
        "boundary_faces": boundary,
    }


def compare(live: dict, base: dict) -> list[str]:
    problems: list[str] = []
    live_ported, base_ported = set(live["conformance_ported"]), set(base["conformance_ported"])
    lost = sorted(base_ported - live_ported)
    if lost:
        problems.append(f"一致性已移植契约少了 {len(lost)} 条：{lost[:5]}")
    if len(live["conformance_unported"]) > len(base["conformance_unported"]):
        problems.append(
            f"未移植/范围外条目变多了：{base['conformance_unported']} → {live['conformance_unported']}"
            "（把契约挪进「未移植/范围外」也是倒退）")
    for key, label in (("conformance_total", "契约总数"), ("selftest_cases", "负例自检例数"),
                       ("probes", "判据探针条数"), ("face_parity_faces", "面级对账面数"),
                       ("boundary_faces", "边界面条数")):
        if live[key] < base[key]:
            problems.append(f"{label}倒退：{base[key]} → {live[key]}")
    if live["probe_scripts_on_disk"] != live["probes"]:
        problems.append(f"清单 {live['probes']} 条 ≠ 磁盘探针 {live['probe_scripts_on_disk']} 个（清单与磁盘必须一一对应）")
    return problems


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--engine", default=str(_paths.ENGINE))
    ap.add_argument("--snap", default=_paths.SNAP)
    ap.add_argument("--cli", default=str(_paths.newest_dist("win-x64") / "nf-dotnet.exe"))
    ap.add_argument("--baseline", default=DEFAULT_BASELINE)
    ap.add_argument("--update", action="store_true")
    ap.add_argument("--timeout", type=int, default=900)
    args = ap.parse_args()

    engine = Path(args.engine)
    baseline_path = Path(args.baseline)
    if not Path(args.cli).exists():
        print(f"FAIL: 找不到 CLI：{args.cli}（用 --cli 指定）")
        return 1

    live = measure(engine, args.snap, args.cli)
    live["date"] = None
    print(f"① 实测：契约总数 {live['conformance_total']} · 已移植 {len(live['conformance_ported'])} · "
          f"未移植 {len(live['conformance_unported'])} · 自检 {live['selftest_cases']} 例 · "
          f"探针 {live['probes']} 条 · 对账面 {live['face_parity_faces']} + 边界 {live['boundary_faces']}")

    if args.update:
        baseline_path.parent.mkdir(parents=True, exist_ok=True)
        payload = dict(live)
        payload["schema"] = "nf-net-no-regression/1"
        baseline_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                                 encoding="utf-8", newline="\n")
        print(f"② 基线已重刷（有意变更）：{baseline_path}")
        return 0

    if not baseline_path.exists():
        print(f"FAIL: 基线不在场：{baseline_path}（先跑一次 --update 生成）")
        return 1
    base = json.loads(baseline_path.read_text(encoding="utf-8-sig"))
    problems = compare(live, base)
    print(f"② 对基线（{baseline_path.name}）：{'一致或只增' if not problems else '发现倒退'}")

    # ③ 自证：把基线里每个数字抬高 1，同一套比较必须判红
    inflated = json.loads(json.dumps(base))
    for key in ("conformance_total", "selftest_cases", "probes", "face_parity_faces", "boundary_faces"):
        inflated[key] = int(inflated[key]) + 1
    if not compare(live, inflated):
        problems.append("自证失败：把基线数字抬高 1 后仍未判红 ⇒ 这条判据照不出倒退")
    else:
        print("③ 自证：基线数字人为抬高 1 ⇒ 判红（判据会红，不是恒绿）")

    # ③b 自证（集合面）：模拟「实测丢了一条已移植契约」与「实测多了一条未移植」，都必须判红
    shrunk = json.loads(json.dumps(live))
    shrunk["conformance_ported"] = list(shrunk["conformance_ported"])[:-1]
    grown = json.loads(json.dumps(live))
    grown["conformance_unported"] = list(grown["conformance_unported"]) + ["（伪造的）新范围外条目"]
    if not compare(shrunk, base):
        problems.append("自证失败：实测的已移植契约砍掉一条后仍未判红（集合面照不出倒退）")
    elif not compare(grown, base):
        problems.append("自证失败：实测的未移植条目增多后仍未判红（集合面照不出倒退）")
    else:
        print("③b 自证（集合面）：实测丢一条已移植 / 多一条未移植 ⇒ 均判红")

    if problems:
        print("FAIL:")
        for p in problems:
            print("  -", p)
        return 1
    print("OK: 不倒退（已移植契约集合 / 自检例数 / 探针条数 / 对账面数 / 契约总数均未低于基线）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
