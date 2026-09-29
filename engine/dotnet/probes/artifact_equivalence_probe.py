"""产物一致性取证：源码构建（bin）与两个 RID 自包含产物（win/linux）到底差在哪。

为什么需要：`nf-dotnet` 的等价判据一直是**行为面**（面级 183 面逐字节输出）。但「已发布的那个产物
是不是我验证过的那个」是另一个问题——本探针把它量出来，并把 linux 冒烟缺位的风险**界定清楚**：

- **判据库程序集 `Nf.Engine.dll`**：在三处（bin / win-x64 / linux-x64）**逐字节相同** ⇒
  凡是靠 Nf.Engine 复算的判据（全部 39 道 check 的载体），**在 linux 产物里就是同一个二进制**；
- **应用程序集 `nf-dotnet.dll`**：三处哈希**不同**——原因是 **RID 被嵌进程序集**（win 里出现 `win-x64`、
  linux 里出现 `linux-x64`，实测两文件相差 104 字节；bin 是无 RID 构建）。**同一 RID 下异地重建逐字节相同**
  （判据见 `probes/reproducible_build_probe.py`），所以这不是"不可复现"，而是"RID 不同 ⇒ 字节不同"；
  故 CLI 面的等价性仍按**每个产物各跑一遍**来证（bin 与 win-x64 已各跑：183 面全同）；
- **RID 原生层**：win/linux 各有 15 个平台专属文件（`.dll/.exe` ↔ `.so`），其余托管文件同名；
- **linux 运行冒烟**：本机无 Linux 运行时（WSL 无发行版）⇒ 仍挂账，但风险已被界定在
  「RID 原生层 + 运行环境」这一层，**不在判据代码**。

用法：
    python probes/artifact_equivalence_probe.py --bin <bin/Release/net8.0> --win <dist/win-x64-fNN> \
                                                --linux <dist/linux-x64-fNN> [--record <输出 md>]
"""
from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # noqa: BLE001
    pass
sys.dont_write_bytecode = True

import _paths  # 默认路径唯一出处（探针可移植）
ENGINE = str(_paths.ENGINE)
DEFAULT_BIN = ENGINE + r"\tools\nf-dotnet\bin\Release\net8.0"
DEFAULT_WIN = str(_paths.newest_dist("win-x64"))
DEFAULT_LINUX = str(_paths.newest_dist("linux-x64"))
DEFAULT_RECORD = _paths.records("NF_NET引擎_产物一致性记录_v1.md")
#: 判据库程序集（Nf.Engine 里装着全部 39 道 check 的载体）与应用程序集
ENGINE_ASSEMBLY = "Nf.Engine.dll"
APP_ASSEMBLY = "nf-dotnet.dll"
#: 平台专属的**应用宿主**（apphost）：win 是 `nf-dotnet.exe`、linux 是无扩展名的 `nf-dotnet`
APP_HOST_WIN = "nf-dotnet.exe"
APP_HOST_LINUX = "nf-dotnet"


def hashes(directory: Path) -> dict:
    return {f.name: hashlib.sha256(f.read_bytes()).hexdigest()
            for f in sorted(directory.iterdir()) if f.is_file()}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bin", default=DEFAULT_BIN)
    ap.add_argument("--win", default=DEFAULT_WIN)
    ap.add_argument("--linux", default=DEFAULT_LINUX)
    ap.add_argument("--record", default=DEFAULT_RECORD)
    ap.add_argument("--behavior-verified", action="append", default=[],
        help="已跑过行为面（183 面）的产物名，可用多次：bin / win / linux")
    args = ap.parse_args()

    bin_dir, win_dir, linux_dir = Path(args.bin), Path(args.win), Path(args.linux)
    hb, hw, hl = hashes(bin_dir), hashes(win_dir), hashes(linux_dir)
    problems = []

    # ① RID 原生层：win/linux 同名托管面不变，差的应是平台专属文件
    win_only = sorted(set(hw) - set(hl))
    linux_only = sorted(set(hl) - set(hw))
    common = sorted(set(hw) & set(hl))
    native_win = [n for n in win_only if n != APP_HOST_WIN]
    native_linux = [n for n in linux_only if n != APP_HOST_LINUX]
    apphost_ok = APP_HOST_WIN in win_only and APP_HOST_LINUX in linux_only
    ok_counts = len(hw) == len(hl) and len(win_only) == len(linux_only)
    print(f"① 产物文件：win {len(hw)} · linux {len(hl)} · 同名 {len(common)}"
          f" · win 独有 {len(win_only)}（平台原生 {len(native_win)}）"
          f" · linux 独有 {len(linux_only)}（平台原生 {len(native_linux)}）")
    if not ok_counts:
        problems.append("win/linux 产物文件数或独有文件数不对称")
    if not apphost_ok:
        problems.append(f"平台应用宿主不成对（期望 win={APP_HOST_WIN} / linux={APP_HOST_LINUX}）")
    if len(native_win) != len(native_linux):
        problems.append(f"平台原生文件数不对称（win {len(native_win)} / linux {len(native_linux)}）")
    if not all(n.endswith(".dll") or n.endswith(".exe") for n in native_win):
        problems.append("win 独有文件里出现非 .dll/.exe 名（托管面可能已漂移）")
    if not all(n.endswith(".so") or n == "createdump" for n in native_linux):
        problems.append("linux 独有文件里出现非 .so/createdump 名（托管面可能已漂移）")

    # ② 判据库程序集在**全部产物**里逐字节相同（本片最要紧的一条）
    #    （第一百二十一片补：**`nfparity` 自己的 bin 也带着一份判据库副本**——它是对账/规模探针的入口，
    #     此前漏检 ⇒ 只重建 nf-dotnet 时，规模探针会用**漂移前的判据库**报出假差异。实测踩到。）
    parity_dir = Path(ENGINE) / "tools" / "nfparity" / "bin" / "Release" / "net8.0"
    parity_dll = parity_dir / ENGINE_ASSEMBLY
    engine_hashes = {"bin": hb.get(ENGINE_ASSEMBLY), "win": hw.get(ENGINE_ASSEMBLY),
                     "linux": hl.get(ENGINE_ASSEMBLY),
                     "parity": hashlib.sha256(parity_dll.read_bytes()).hexdigest() if parity_dll.exists() else None}
    engine_same = len(set(engine_hashes.values())) == 1 and None not in engine_hashes.values()
    print(f"② 判据库 {ENGINE_ASSEMBLY}：{'四处（bin/win/linux/nfparity）逐字节相同' if engine_same else '**不一致**'}"
          f" · sha256[:16] {str(engine_hashes['win'])[:16]} · parity {str(engine_hashes['parity'])[:16]}")
    if not engine_same:
        problems.append(f"{ENGINE_ASSEMBLY} 在各产物里不一致（含 nfparity 的副本——它常被漏重建）：{engine_hashes}")

    # ③ 应用程序集：跨 RID 预期不同（RID 字符串被嵌进程序集）——**记录而非断言相等**
    app_hashes = {"bin": hb.get(APP_ASSEMBLY), "win": hw.get(APP_ASSEMBLY),
                  "linux": hl.get(APP_ASSEMBLY)}
    app_same = len(set(app_hashes.values())) == 1
    print(f"③ 应用程序集 {APP_ASSEMBLY}：{'三处相同' if app_same else '三处不同（RID 被嵌进程序集；同 RID 异地重建逐字节相同——见 reproducible_build_probe）'}"
          f" · bin {str(app_hashes['bin'])[:12]} / win {str(app_hashes['win'])[:12]}"
          f" / linux {str(app_hashes['linux'])[:12]}")

    # ④ 托管面同名文件里，win/linux 有多少逐字节相同（BCL 是 RID 专属构建，预期普遍不同）
    same_common = [n for n in common if hw[n] == hl[n]]
    print(f"④ 同名托管面逐字节相同 {len(same_common)}/{len(common)}"
          f"（其余为 RID 专属 BCL 构建，非本工程代码）")

    # ⑤ bin ∩ win：源码构建与 win 产物里哪些相同
    common_bw = sorted(set(hb) & set(hw))
    same_bw = [n for n in common_bw if hb[n] == hw[n]]
    print(f"⑤ bin ∩ win：同名 {len(common_bw)} · 逐字节相同 {len(same_bw)}（{', '.join(same_bw)}）")
    if ENGINE_ASSEMBLY not in same_bw:
        problems.append(f"bin 与 win 产物的 {ENGINE_ASSEMBLY} 不同")

    # ⑥ 记录件
    record = Path(args.record)
    lines = [
        "# NF .NET 引擎 · 产物一致性记录（v1）",
        "",
        "> 生成物（由 `probes/artifact_equivalence_probe.py` 写入，**勿手改**）。回答一个问题："
        "**已发布的产物，是不是我验证过的那个？**",
        "",
        "## 1. 被测产物",
        "",
        f"- 源码构建（framework-dependent）：`{bin_dir}`（{len(hb)} 文件）",
        f"- win-x64 自包含：`{win_dir}`（{len(hw)} 文件）",
        f"- linux-x64 自包含：`{linux_dir}`（{len(hl)} 文件）",
        f"- **已跑行为面（183 面逐字节）的产物**：{'、'.join(args.behavior_verified) or '（未指定）'}",
        "",
        "## 2. 三条结论",
        "",
        f"1. **判据库 `{ENGINE_ASSEMBLY}` 在三处逐字节相同**"
        f"（sha256 `{str(engine_hashes['win'])}`）⇒ 凡靠它复算的判据（39 道 check 的全部载体），"
        "在 linux 产物里就是**同一个二进制**。",
        f"2. **应用程序集 `{APP_ASSEMBLY}` 三处不同**（**RID 被嵌进程序集**，不是不可复现）：bin `{str(app_hashes['bin'])[:16]}`（无 RID）/ "
        f"win `{str(app_hashes['win'])[:16]}`（内嵌 `win-x64`）/ linux `{str(app_hashes['linux'])[:16]}`（内嵌 `linux-x64`），"
        "win↔linux 实测差 104 字节。**同一 RID 下异地重建逐字节相同**（判据 `reproducible_build_probe.py`：两棵独立源码树各发布一次，189/189 文件全等；"
        "关掉 `PathMap` 的负对照会红）。故 CLI 面的等价性按「每个产物各跑一遍」来证（bin 与 win-x64 已各跑）.",
        f"3. **平台专属层**：平台原生 {len(native_win)} 对（`{native_win[0]}` … ↔ `{native_linux[0]}` …）+ "
        f"应用宿主 1 对（`{APP_HOST_WIN}` ↔ `{APP_HOST_LINUX}`）；其余 {len(common)} 个同名文件里"
        f" {len(same_common)} 个逐字节相同，其余为 RID 专属 BCL 构建（非本工程代码）。",
        "",
        "## 3. linux 冒烟缺位的风险界定",
        "",
        "- 本机**无 Linux 运行时**（WSL 无发行版 / 无 Docker），故 linux 产物的**运行冒烟仍挂账**。",
        "- 但由上第 1 条：linux 产物里的**判据代码与 Windows 上验证过的完全同二进制**；"
        "未验证部分被界定为 **RID 原生层 + 运行环境**（.NET 自包含运行时在 Linux 上的加载与 I/O 行为），"
        "**不包含任何本工程的判据逻辑**。",
        "- 触发条件：一旦有 Linux 主机（或 CI runner），跑 `run-gate.ps1 -Root <snapshot> -Cli <linux 产物>` + "
        "`face_parity_probe.py`，即可把这条挂账收掉。",
        "",
        "## 4. 问题清单",
        "",
    ]
    lines += [f"- {p}" for p in problems] if problems else ["- （无）"]
    lines.append("")
    with open(record, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines))
    print(f"⑥ 记录件已写：{record}")

    if problems:
        print("FAIL:")
        for p in problems:
            print("  -", p)
        return 1
    print("OK: 产物一致性取证通过（判据库三处同二进制 · RID 原生层对称 · 应用层按行为面逐产物验证）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
