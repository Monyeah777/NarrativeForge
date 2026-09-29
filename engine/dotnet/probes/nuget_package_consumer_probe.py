"""**包化 + 第三方消费 + API 面冻结**（第一百一十二片）。

这条判据回答的是"引擎到底能不能被别人用"，而不是"我本机跑得通"：

  ① **可打包**：`dotnet pack src/Nf.Engine` 必须产出 `NarrativeForge.Engine.<v>.nupkg`，
     且包内**不得出现任何 `<dependency>`**（引擎是 BCL-only，靠外部包才能用就不算零依赖）。
  ② **第三方可消费**：在一个**全新临时项目**里只写
     `<PackageReference Include="NarrativeForge.Engine" />`（本地源，`<clear/>` 掉 nuget.org），
     不引源码、不引工程引用，restore + build + run 必须成功。
  ③ **结果等价**：该外部消费者用公开 API（`CertificateVerifier.VerifyAll` + `PythonJson.Indented`）
     复算 17 条在盘证书，输出与引擎 CLI 的 `combine verify --json` **逐字节相同**。
  ④ **API 面冻结**：用反射导出全部公开类型与成员，与基线 `api/Nf.Engine.PublicAPI.txt` 比对；
     任何 API 漂移都必须是有意的（`--update` 重刷基线）。
  ⑤ **负对照**：把临时副本里某条证书的 `module_count` 改错，消费者必须判出不一致（exit 1）
     ——证明它真在复算，而不是回放一份写死的输出。

用法：
    python probes/nuget_package_consumer_probe.py --engine <NF-NET-engine> --snap <隔离快照>
        [--cli <nf-dotnet.exe>] [--dotnet <dotnet.exe>] [--api-baseline <路径>] [--update] [--keep]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # noqa: BLE001
    pass
sys.dont_write_bytecode = True

import _paths  # 默认路径唯一出处（探针可移植）
ENGINE = _paths.ENGINE
DEFAULT_SNAP = _paths.SNAP
DEFAULT_DOTNET = _paths.DOTNET
PACKAGE_ID = "NarrativeForge.Engine"

CONSUMER_CSPROJ = """<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <OutputType>Exe</OutputType>
    <TargetFramework>net8.0</TargetFramework>
    <Nullable>enable</Nullable>
    <ImplicitUsings>enable</ImplicitUsings>
    <AssemblyName>consumer</AssemblyName>
  </PropertyGroup>
  <ItemGroup>
    <PackageReference Include="__PACKAGE_ID__" Version="__PACKAGE_VERSION__" />
  </ItemGroup>
</Project>
"""

NUGET_CONFIG = """<?xml version="1.0" encoding="utf-8"?>
<configuration>
  <packageSources>
    <!-- 只留本地源：证明引擎包不依赖任何外部包 -->
    <clear />
    <add key="local" value="__FEED__" />
  </packageSources>
</configuration>
"""

CONSUMER_PROGRAM = r"""
using System.Reflection;
using Nf.Engine;

// 第三方消费者：只用 **公开 API**，不引源码、不引工程引用。
var mode = args.Length > 0 ? args[0] : "verify";

if (mode == "--api")
{
    var asm = typeof(CertificateVerifier).Assembly;
    var lines = new List<string>();
    lines.Add("assembly:" + asm.GetName().Name);
    foreach (var t in asm.GetExportedTypes().OrderBy(t => t.FullName, StringComparer.Ordinal))
    {
        lines.Add("T:" + t.FullName);
        var members = new List<string>();
        foreach (var m in t.GetMembers(BindingFlags.Public | BindingFlags.Static | BindingFlags.Instance | BindingFlags.DeclaredOnly))
        {
            members.Add(m switch
            {
                MethodInfo mi => "M:" + mi.Name + "(" + string.Join(",", mi.GetParameters().Select(p => p.ParameterType.ToString())) + ")",
                PropertyInfo pi => "P:" + pi.Name + ":" + pi.PropertyType.ToString(),
                FieldInfo fi => "F:" + fi.Name + ":" + fi.FieldType.ToString(),
                ConstructorInfo ci => "C:(" + string.Join(",", ci.GetParameters().Select(p => p.ParameterType.ToString())) + ")",
                _ => "X:" + m.Name,
            });
        }
        foreach (var mem in members.Distinct().OrderBy(x => x, StringComparer.Ordinal))
            lines.Add("  " + mem);
    }
    Console.Out.Write(string.Join("\n", lines) + "\n");
    return 0;
}

var root = args.Length > 1 ? args[1] : ".";
var rows = CertificateVerifier.VerifyAll(root);
var failed = rows.Count(r => r.Issues.Count > 0);

if (mode == "verify-json")
{
    Console.WriteLine(PythonJson.Indented(new Dictionary<string, object?>
    {
        ["certificates"] = rows.Count,
        ["failed"] = failed,
        ["rows"] = rows.Select(r => (object?)new Dictionary<string, object?>
        {
            ["issues"] = r.Issues.Cast<object?>().ToList(),
            ["label"] = r.Label,
            ["legal"] = r.Legal,
            ["modules"] = r.Modules,
        }).ToList(),
    }));
    return failed == 0 ? 0 : 1;
}

Console.WriteLine($"证书 {rows.Count} · 失败 {failed}");
foreach (var r in rows.Where(x => x.Issues.Count > 0).Take(3))
    Console.WriteLine("  " + r.Label + " -> " + string.Join(" | ", r.Issues));
return failed == 0 ? 0 : 1;
"""


def run(cmd: list[str], cwd: Path | None = None, timeout: int = 1800) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=str(cwd) if cwd else None, capture_output=True, timeout=timeout)


def norm(s: bytes) -> str:
    return s.decode("utf-8", "replace").replace("\r\n", "\n")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--engine", default=str(ENGINE))
    ap.add_argument("--snap", default=DEFAULT_SNAP)
    ap.add_argument("--cli", default="")
    ap.add_argument("--dotnet", default=DEFAULT_DOTNET)
    ap.add_argument("--win", default="", help="win-x64 交付形态目录（缺省取 dist 下最大 fNN）")
    ap.add_argument("--linux", default="", help="linux-x64 交付形态目录（缺省取 dist 下最大 fNN）")
    ap.add_argument("--api-baseline", default="")
    ap.add_argument("--update", action="store_true", help="按当前程序集重刷 API 基线（有意变更时才用）")
    ap.add_argument("--keep", action="store_true")
    ap.add_argument("--timeout", type=int, default=1800)
    args = ap.parse_args()

    engine = Path(args.engine)
    baseline = Path(args.api_baseline) if args.api_baseline else engine / "api" / "Nf.Engine.PublicAPI.txt"
    problems: list[str] = []
    tmp = Path(tempfile.mkdtemp(prefix="nf-nupkg-"))

    def fail(msg: str) -> None:
        problems.append(msg)

    try:
        # ① 打包
        feed = tmp / "feed"
        feed.mkdir(parents=True)
        pack = run([args.dotnet, "pack", str(engine / "src" / "Nf.Engine" / "Nf.Engine.csproj"),
                    "-c", "Release", "-o", str(feed), "-v", "q", "--nologo"], timeout=args.timeout)
        if pack.returncode != 0:
            tail = (norm(pack.stdout).strip().splitlines() or [""])[-3:]
            fail("dotnet pack 失败：" + " | ".join(tail))
            print("FAIL:")
            for p in problems:
                print("  -", p)
            return 1
        nupkgs = list(feed.glob(f"{PACKAGE_ID}.*.nupkg"))
        if not nupkgs:
            fail(f"pack 后没有产出 {PACKAGE_ID}.*.nupkg")
            print("FAIL:")
            for p in problems:
                print("  -", p)
            return 1
        nupkg = nupkgs[0]
        version = nupkg.name[len(PACKAGE_ID) + 1: -len(".nupkg")]
        print(f"① 打包：{nupkg.name} · {nupkg.stat().st_size/1024:.1f} KB · sha256[:16] {sha256(nupkg)[:16]}")

        # ①b 包内不得有依赖
        with zipfile.ZipFile(nupkg) as z:
            nuspec = next((n for n in z.namelist() if n.endswith(".nuspec")), None)
            if not nuspec:
                fail("nupkg 里没有 .nuspec")
            else:
                spec = z.read(nuspec).decode("utf-8", "replace")
                deps = spec.count("<dependency ")
                if deps:
                    fail(f"引擎包声明了 {deps} 个 NuGet 依赖（引擎应为 BCL-only 零依赖）")
                else:
                    print("   包内依赖项：0（BCL-only 零依赖）")
            # ①c 包内判据库必须与交付产物同一二进制（否则"第三方引的包"与"我验过的产物"是两样东西）
            dll_entry = next((n for n in z.namelist()
                              if n.endswith("/Nf.Engine.dll") or n == "Nf.Engine.dll"), None)
            if not dll_entry:
                fail("nupkg 里没有 lib/*/Nf.Engine.dll")
            else:
                packed = z.read(dll_entry)
                packed_sha = hashlib.sha256(packed).hexdigest()
                same_as = []
                # 交付形态目录**不写死**（写死过 f106，换代即假红——本轮实测踩到）：缺省取 dist 下最大 fNN。
                def newest(rid: str) -> Path | None:
                    best, best_n = None, -1
                    for d in (engine / "dist").glob(f"nf-dotnet-{rid}-f*-*"):
                        import re as _re
                        m = _re.search(r"-f(\d+)-", d.name)
                        if m and int(m.group(1)) > best_n:
                            best_n, best = int(m.group(1)), d
                    return best

                targets = [
                    ("bin", engine / "tools/nf-dotnet/bin/Release/net8.0/Nf.Engine.dll"),
                    ("win", (Path(args.win) if args.win else newest("win-x64") or Path("x")) / "Nf.Engine.dll"),
                    ("linux", (Path(args.linux) if args.linux else newest("linux-x64") or Path("x")) / "Nf.Engine.dll"),
                ]
                for tag, p in targets:
                    if p.exists() and sha256(p) == packed_sha:
                        same_as.append(tag)
                print(f"   包内 {dll_entry} sha256[:16] {packed_sha[:16]} · 与交付产物同二进制：{same_as or '（无匹配）'}")
                if len(same_as) < 3:
                    fail(f"包内判据库与交付产物不同二进制（只匹配到 {same_as}）——引包复算的证据就落不到已验产物上")

        # ② 全新第三方工程：只引包
        consumer = tmp / "consumer"
        consumer.mkdir(parents=True)
        (consumer / "consumer.csproj").write_text(
            CONSUMER_CSPROJ.replace("__PACKAGE_ID__", PACKAGE_ID).replace("__PACKAGE_VERSION__", version),
            encoding="utf-8")
        (consumer / "nuget.config").write_text(NUGET_CONFIG.replace("__FEED__", str(feed)), encoding="utf-8")
        (consumer / "Program.cs").write_text(CONSUMER_PROGRAM, encoding="utf-8")
        print(f"② 第三方工程：只写 1 条 PackageReference（源为本地 feed，已 <clear/> 掉 nuget.org）")

        # 注意：`dotnet run` 会把不认识的选项**透传给应用**（--nologo 曾让 args[0] 变成 --nologo），
        # 故这里只给 run 认识的最小选项，应用参数一律放在 `--` 之后。
        api_out = run([args.dotnet, "run", "--project", str(consumer / "consumer.csproj"), "-c", "Release",
                       "--", "--api"], cwd=consumer, timeout=args.timeout)
        if api_out.returncode != 0:
            fail("消费者 --api 运行失败：" + norm(api_out.stdout)[-400:] + norm(api_out.stderr)[-400:])
            print("FAIL:")
            for p in problems:
                print("  -", p)
            return 1
        api_text = norm(api_out.stdout)
        n_types = sum(1 for l in api_text.splitlines() if l.startswith("T:"))
        n_members = sum(1 for l in api_text.splitlines() if l.startswith("  "))
        print(f"   公开面：{n_types} 类型 · {n_members} 成员")

        # ④ API 面冻结
        if args.update:
            baseline.parent.mkdir(parents=True, exist_ok=True)
            baseline.write_text(api_text, encoding="utf-8", newline="\n")
            print(f"④ API 基线已重刷（有意变更）：{baseline}")
        elif not baseline.exists():
            fail(f"API 基线不在场：{baseline}（先跑一次 --update 生成）")
        else:
            want = baseline.read_text(encoding="utf-8-sig").replace("\r\n", "\n")
            if want != api_text:
                wl = want.splitlines()
                gl = api_text.splitlines()
                only_base = [l for l in wl if l not in set(gl)][:5]
                only_new = [l for l in gl if l not in set(wl)][:5]
                fail("API 面与基线不一致（公开面变更必须有意）："
                     f" 基线独有 {only_base} · 当前独有 {only_new} —— 确认无误后跑 --update")
            else:
                print(f"④ API 面冻结：与基线逐行一致（{baseline.name}）")

        # ③ 结果等价：消费者复算 == CLI 机器面
        cli = args.cli
        if not cli or not Path(cli).exists():
            cands = sorted((engine / "dist").glob("nf-dotnet-win-x64-f*/nf-dotnet.exe"))
            cli = str(cands[-1]) if cands else ""
        if not cli or not Path(cli).exists():
            fail("找不到 nf-dotnet.exe（--cli 未给且 dist 下无 fNN 产物）")
        else:
            cons = run([args.dotnet, "run", "--project", str(consumer / "consumer.csproj"), "-c", "Release",
                        "--", "verify-json", args.snap], cwd=consumer, timeout=args.timeout)
            ref = run([cli, "--root", args.snap, "combine", "verify", "--json"], timeout=args.timeout)
            if cons.returncode != 0:
                fail(f"消费者复算失败（exit={cons.returncode}）")
            if ref.returncode != 0:
                fail(f"CLI combine verify 失败（exit={ref.returncode}）")
            if cons.returncode == 0 and ref.returncode == 0:
                a, b = norm(cons.stdout), norm(ref.stdout)
                if a == b:
                    print(f"③ 消费者复算 == CLI 机器面（逐字节）· {len(a.encode('utf-8'))} 字节")
                else:
                    fail(f"消费者输出与 CLI 机器面不同（消费者 {len(a)} 字符 / CLI {len(b)} 字符）")

        # ⑤ 负对照：改坏一条证书，消费者必须判出
        bad = tmp / "snap-bad"
        shutil.copytree(args.snap, bad)
        cert_path = bad / "protocol" / "combo_certificates.json"
        doc = json.loads(cert_path.read_text(encoding="utf-8"))
        first = doc["certificates"][0]
        before = first.get("module_count")
        first["module_count"] = (before or 0) + 1
        cert_path.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
        neg = run([args.dotnet, "run", "--project", str(consumer / "consumer.csproj"), "-c", "Release",
                   "--", "verify", str(bad)], cwd=consumer, timeout=args.timeout)
        if neg.returncode == 0:
            fail("负对照没有判出篡改（消费者可能在与写死输出比对）")
        else:
            head = [l for l in norm(neg.stdout).splitlines() if l.strip()][:2]
            print(f"⑤ 负对照：改坏 module_count ⇒ 消费者 exit={neg.returncode} · {' / '.join(head)}")

        if problems:
            print("FAIL:")
            for p in problems:
                print("  -", p)
            return 1
        print("OK: 引擎可打包（零依赖）· 第三方只引包可复算且与 CLI 逐字节一致 · API 面已冻结 · 负对照会红")
        return 0
    finally:
        if args.keep:
            print(f"   临时目录保留：{tmp}")
        else:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
