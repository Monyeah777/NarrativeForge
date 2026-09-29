"""**入库包体检**：验「要交给作者的那包东西」本身，而不是引擎。

第一百零九片的 `handoff_integrity_probe` 体检的是**引擎工作区**（文档数字 ↔ 实测）；
本探针体检的是**入库包**（`NF_NET入库包_v1/`）——它是唯一要离开这台机器的产物，此前**一次都没验过**：

  ① **包内卫生**：无 CRLF · 无 BOM · 无 `bin`/`obj`/`dist`/`_stout`/`__pycache__` ·
     **无作者机器绝对路径**（包是要进别人仓库的）；
  ② **workflow 可解析且平台面干净**：YAML 能被解析 · 有 `jobs/steps` · 关键步骤在场（构建 / 只读门 / 对账）·
     **run 块里不得出现盘符路径或 `.exe`**（那是 ubuntu job，写 Windows 路径等于一次都不跑）；
  ③ **ADR 结构**：frontmatter 必填字段（id/title/status/date/evidence）· 三段齐（背景/决策/后果）·
     `decisions/INDEX.md` 投影里有对应行；
  ④ **清单 ↔ 包内探针**一一对应（排除 `_` 开头的辅助模块）；
⑤ **包内文档数字 = 实测**：包 README 的文件数声明、引擎 README 的「命令行面 / 负例自检 / 一致性契约 /
     判据探针」四个数字，逐条与实测比（与第一百零九片同一纪律：文档不许自称"当前"）。
  ⑥ **维护手册的命令引用可执行**：`engine/dotnet/RUNBOOK.md` 在场，且里面出现的每个
     `nf-dotnet <cmd>` 命令词都能在 CLI 帮助的命令表里查到（仿仓内「文档命令面」判据，防手册写不存在的命令）。

用法：
    python probes/bundle_integrity_probe.py --bundle <NF_NET入库包_v1> [--engine <引擎>]
        [--snap <语料>] [--cli <nf-dotnet>]
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # noqa: BLE001
    pass
sys.dont_write_bytecode = True

import _paths  # 默认路径唯一出处（探针可移植）

DEFAULT_BUNDLE = str(_paths.ENGINE.parent / "NF_NET入库包_v1")
# **通用规则**：落地件（`repo/**`）里不许出现**盘符绝对路径**或 POSIX 家目录路径——
# 不写死某台机器的用户名（那样探针自己就带上了机器路径，本片首跑就是这么被自己抓住的）。
# 注意要**排除转义序列**：`"protocol:\n"` 这种字符串里 `l:\` 会被朴素的 `[A-Za-z]:[\\/]` 误命中，
# 故要求「盘符 + 一段目录名 + 再一个分隔符」才判（实测：朴素版误报 49 个文件）。
#: **本机路径标记**：运行期算出来的家目录（正/反斜杠两种写法）——不写死任何字面量，
#: 故零误报；同时天然覆盖「换台机器就换标记」的情形。
_HOME = Path.home()
HOME_MARKERS = tuple({str(_HOME), str(_HOME).replace("\\", "/"), str(_SIBLING_PARENT) if (_SIBLING_PARENT := _HOME / "Downloads") else ""} - {""})
#: 其它盘符路径/家目录路径：**只报告不判红**（合成夹具与 Windows 专属姿态会命中）
GENERIC_PATH = re.compile(r"[A-Za-z]:[\\/][^\s\"'\\/]+[\\/]|/(?:Users|home)/[A-Za-z0-9._-]+/")
#: **带理由的豁免**（与仓库 `EXCLUDE_DIRS` 同一纪律：排除要写清为什么）。
#: 只允许「合成夹具」与「Windows 专属姿态」两类——它们含路径是**判据本身的要求**。
PATH_ALLOW = {
    "repo/engine/dotnet/probes/conformance_negative_probe.py":
        "合成泄漏夹具：故意含 `C:\\Users\\某人` / `/home/bob`，用来验「公开面泄漏」判据（非本机路径）",
    "repo/engine/dotnet/probes/no_python_smoke_probe.py":
        "Windows 专属姿态：故意把 PATH 限成 `C:\\Windows\\System32` 以证明 python 不可见",
}
DRIVE_PATH = re.compile(r"[A-Za-z]:[\\/]")
EXE_SUFFIX = re.compile(r"\.exe\b")
BAD_DIRS = {"bin", "obj", "__pycache__", "_stout", "dist"}


def read_json(cmd: list[str], timeout: int = 900) -> dict:
    p = subprocess.run(cmd, capture_output=True, timeout=timeout)
    return json.loads(p.stdout.decode("utf-8", "replace"))


def load_faces(engine_dotnet: Path) -> tuple[int, int]:
    import importlib.util
    probes = engine_dotnet / "probes"
    sys.path.insert(0, str(probes))
    try:
        spec = importlib.util.spec_from_file_location("_fp_count", probes / "face_parity_probe.py")
        mod = importlib.util.module_from_spec(spec)
        assert spec and spec.loader
        spec.loader.exec_module(mod)  # type: ignore[union-attr]
        return len(mod.FACES), len(mod.BOUNDARY_FACES)
    finally:
        sys.path.pop(0)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bundle", default=DEFAULT_BUNDLE)
    ap.add_argument("--engine", default=str(_paths.ENGINE))
    ap.add_argument("--snap", default=_paths.SNAP)
    ap.add_argument("--cli", default=str(_paths.newest_dist("win-x64") / "nf-dotnet.exe"))
    ap.add_argument("--timeout", type=int, default=900)
    args = ap.parse_args()

    bundle = Path(args.bundle)
    engine_dotnet = bundle / "repo" / "engine" / "dotnet"
    problems: list[str] = []
    if not bundle.is_dir():
        print(f"FAIL: 入库包不在场：{bundle}")
        return 1

    # ① 包内卫生
    files = [p for p in bundle.rglob("*") if p.is_file()]
    crlf, bom, author, bad_dir, allowed, generic = [], [], [], [], [], []
    for p in files:
        rel = p.relative_to(bundle).as_posix()
        if BAD_DIRS & set(p.relative_to(bundle).parts):
            bad_dir.append(rel)
        data = p.read_bytes()
        if b"\r\n" in data:
            crlf.append(rel)
        if data[:3] == b"\xef\xbb\xbf":
            bom.append(rel)
        # 作者机器路径只许出现在**包级说明**（本地备忘）；`repo/**` 是要落地的东西，一律不许带
        lands = rel.startswith("repo/")
        if lands and p.suffix.lower() in (".md", ".py", ".cs", ".json", ".yml", ".yaml", ".ps1", ".txt", ".props", ".csproj"):
            try:
                text = data.decode("utf-8")
                if any(mk and mk in text for mk in HOME_MARKERS):
                    (allowed if rel in PATH_ALLOW else author).append(rel)
                elif GENERIC_PATH.search(text):
                    generic.append(rel)
            except UnicodeDecodeError:
                pass
    print(f"① 包内卫生：{len(files)} 文件 · CRLF {len(crlf)} · BOM {len(bom)} · 构建/缓存目录 {len(bad_dir)} · "
          f"本机路径 {len(author)}（{len(allowed)} 件带理由豁免）· 其它含路径样文本 {len(generic)} 件（只报告）")
    for rel in allowed:
        print(f"   · 豁免：{rel} —— {PATH_ALLOW[rel]}")
    for label, lst in (("CRLF", crlf), ("BOM", bom), ("构建/缓存目录", bad_dir), ("作者机器路径", author)):
        if lst:
            problems.append(f"包内含{label}：{lst[:5]}")

    # ② workflow
    wf = bundle / "repo" / ".github" / "workflows" / "net-engine.yml"
    if not wf.exists():
        problems.append(f"workflow 不在场：{wf}")
    else:
        import yaml
        try:
            doc = yaml.safe_load(wf.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            doc = None
            problems.append(f"workflow YAML 解析失败：{exc}")
        if isinstance(doc, dict):
            jobs = doc.get("jobs") or {}
            if not jobs:
                problems.append("workflow 没有 jobs")
            names, runs = [], []
            for job in jobs.values():
                if not job.get("runs-on"):
                    problems.append("workflow job 缺 runs-on")
                for st in job.get("steps", []):
                    names.append(str(st.get("name", "")))
                    if st.get("run"):
                        runs.append(str(st["run"]))
            for need in ("构建", "只读门", "对账"):
                if not any(need in n for n in names):
                    problems.append(f"workflow 缺关键步骤（名字含「{need}」）")
            platform_bad = [(i, l) for i, blk in enumerate(runs) for l in blk.splitlines()
                            if DRIVE_PATH.search(l) or EXE_SUFFIX.search(l)]
            print(f"② workflow：jobs {len(jobs)} · 步骤 {len(names)} · 平台面可疑行 {len(platform_bad)}")
            if platform_bad:
                problems.append(f"workflow run 块含 Windows 路径/`.exe`（ubuntu job 会一跑就废）：{platform_bad[:3]}")
        elif doc is not None:
            problems.append("workflow 顶层不是映射（YAML 形状异常）")

    # ③ ADR
    adr_dir = bundle / "repo" / "decisions"
    adrs = sorted(adr_dir.glob("ADR-0005-*.md"))
    if not adrs:
        problems.append(f"ADR-0005 不在场：{adr_dir}")
    else:
        text = adrs[0].read_text(encoding="utf-8")
        m = re.match(r"^---\n(.*?)\n---\n", text, flags=re.S)
        fm = m.group(1) if m else ""
        need = ("id:", "title:", "status:", "date:", "evidence:")
        missing = [k for k in need if k not in fm]
        sections = [s for s in ("## 背景", "## 决策", "## 后果") if s in text]
        idx = (adr_dir / "INDEX.md").read_text(encoding="utf-8") if (adr_dir / "INDEX.md").exists() else ""
        adr_id = re.search(r"id:\s*(\S+)", fm)
        title = re.search(r"title:\s*(.+)", fm)
        status = re.search(r"status:\s*(\S+)", fm)
        in_index = bool(adr_id and title and status and re.search(
            r"\|\s*" + re.escape(adr_id.group(1)) + r"\s*\|\s*" + re.escape(title.group(1).strip()) + r"\s*\|\s*"
            + re.escape(status.group(1)), idx))
        print(f"③ ADR：frontmatter 缺字段 {len(missing)} · 三段齐 {len(sections)}/3 · INDEX 投影 {'有' if in_index else '无/不匹配'}")
        if missing:
            problems.append(f"ADR frontmatter 缺字段：{missing}")
        if len(sections) < 3:
            problems.append(f"ADR 三段不齐（只有 {sections}）")
        if not in_index:
            problems.append("ADR 未在 decisions/INDEX.md 里按 (编号, 标题, 状态) 投影")

    # ④ 清单 ↔ 包内探针
    manifest = json.loads((engine_dotnet / "probes" / "probe_manifest.json").read_text(encoding="utf-8"))
    declared = [p["script"] for p in manifest["probes"]]
    disk = sorted(p.name for p in (engine_dotnet / "probes").glob("*.py") if not p.name.startswith("_"))
    print(f"④ 清单 {len(declared)} 条 ↔ 包内探针 {len(disk)} 个")
    if sorted(declared) != disk:
        problems.append(f"清单与包内探针不一致：清单独有 {sorted(set(declared) - set(disk))[:3]} · 磁盘独有 {sorted(set(disk) - set(declared))[:3]}")

    # ⑤ 包内文档数字 = 实测
    faces, boundary = load_faces(engine_dotnet)
    live = {}
    if Path(args.cli).exists():
        st = read_json([args.cli, "--root", args.snap, "selftest", "--json"], args.timeout)
        conf = read_json([args.cli, "--root", args.snap, "conformance", "--json"], args.timeout)
        live["selftest"] = len(st.get("rows", []))
        live["conformance"] = (int(conf.get("passed", 0)), int(conf.get("passed", 0)) + len(conf.get("unported", []) or []))
    else:
        problems.append(f"CLI 不在场，无法取实测自检/契约数：{args.cli}")
    eng_readme = (engine_dotnet / "README.md").read_text(encoding="utf-8")
    claims = {
        "命令行面": (re.search(r"\|\s*命令行面\s*\|\s*\*\*(\d+) 面", eng_readme), faces, "包内对账面数"),
        "判据探针": (re.search(r"\|\s*判据探针\s*\|\s*\*\*(\d+) 条", eng_readme), len(declared), "清单条数"),
    }
    if "selftest" in live:
        claims["负例自检"] = (re.search(r"\|\s*负例自检\s*\|\s*\*\*(\d+) 例", eng_readme), live["selftest"], "实测自检例数")
        claims["一致性契约"] = (re.search(r"\|\s*一致性契约\s*\|\s*\*\*(\d+) / (\d+)\*\*", eng_readme),
                          live["conformance"], "实测契约（已移植/总数）")
    if boundary:
        pass  # 边界面数在 README 里作为「+ 1 边界面」出现，不单独解析
    bundle_claim = re.search(r"包内容（(\d+) 文件）", (bundle / "README.md").read_text(encoding="utf-8"))
    print("⑤ 文档数字：", end="")
    for label, (mt, real, hint) in claims.items():
        if not mt:
            problems.append(f"包内引擎 README 的「{label}」行解析不到（格式变了）")
            continue
        got = tuple(int(g) for g in mt.groups())
        ok = got == (real if isinstance(real, tuple) else (real,))
        print(f"{label} 文档{got} 实测{real}{'✓' if ok else '✗'} ", end="")
        if not ok:
            problems.append(f"包内引擎 README 的「{label}」与实测不符：文档 {got} / {hint} {real}")
    if bundle_claim:
        doc_n = int(bundle_claim.group(1))
        ok = doc_n == len(files)
        print(f"· 包文件数 文档{doc_n} 实测{len(files)}{'✓' if ok else '✗'}")
        if not ok:
            problems.append(f"包 README 的文件数声明与实测不符：文档 {doc_n} / 实测 {len(files)}")
    else:
        problems.append("包 README 解析不到「包内容（N 文件）」声明")
    print()

    # ⑥ 维护手册：存在 + 命令引用可执行
    runbook = engine_dotnet / "RUNBOOK.md"
    if not runbook.exists():
        problems.append(f"维护手册不在场：{runbook}")
    else:
        text = runbook.read_text(encoding="utf-8")
        mentioned = sorted(set(re.findall(r"nf-dotnet\s+(?:--root\s+\S+\s+)?([a-z][a-z0-9-]*)", text)))
        help_txt = ""
        if Path(args.cli).exists():
            # 帮助文本走 stderr（实测），故把 stderr 并入 stdout 一起抓
            p = subprocess.run([args.cli, "--help"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=120)
            help_txt = p.stdout.decode("utf-8", "replace")
        known = set()
        in_cmd = False
        for line in help_txt.splitlines():
            if line.startswith("命令"):
                in_cmd = True
                continue
            if in_cmd:
                if not line.strip():
                    break
                if re.match(r"^\s{2}(\S+)", line):
                    known.add(re.match(r"^\s{2}(\S+)", line).group(1))  # type: ignore[union-attr]
        unknown = [c for c in mentioned if c not in known]
        print(f"⑥ 维护手册：{runbook.name} · 引用命令 {len(mentioned)} 个 · CLI 命令表 {len(known)} 个 · 查不到 {len(unknown)}")
        if not known:
            problems.append("取不到 CLI 命令表（--help 形状变了？），维护手册的命令面无法校验")
        elif unknown:
            problems.append(f"维护手册引用了 CLI 里不存在的命令：{unknown}")

    if problems:
        print("FAIL:")
        for p in problems:
            print("  -", p)
        return 1
    print("OK: 入库包体检通过（卫生 · workflow 可解析且平台面干净 · ADR 结构与投影 · 清单一致 · 文档数字=实测）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
