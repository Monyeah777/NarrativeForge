#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""npm 一键包交付线的**常驻**门禁：把 `packaging/npm` 的**两条发布前自检**接进 unittest discover。

为什么（2026-10-03 取证）：`test/smoke.test.mjs` 与 `tools/verify-package.mjs` 此前**只在发布工作流**
（dispatch / tag）里跑过，常驻门禁从没跑过它们。两条**互补**，缺一条就有面没人看：

- `test/smoke.test.mjs`：payload 与清单逐文件 sha256 一致 + 启动器 `--version` 快路 + `--help` +
  在已有检出上真跑一条只读命令；
- `tools/verify-package.mjs`（工作流的 `npm run verify`）：package.json 结构（bin 双别名 / files 清单）、
  关键件在场、清单 ⟷ 包版本一致、payload **不含点文件**（npm 打包含剔除 ⇒ tarball 与清单不一致）、
  **不含 __pycache__ 字节码**、解包体积预算、LICENSE 在场。

跳过条件（各自写明理由，不是静默）：无 node；或 payload 未暂存（`payload/` 是
`packaging/npm/.gitignore` 的忽略面，需先跑 `node tools/stage-payload.mjs`）。

第三条（本文件自建）：**包的公开承诺不能只是一句话**——README 写着「零网络请求、零遥测」，
故常驻扫一遍该包 JS 里的网络/埋点原语（不依赖 node，纯静态）。
"""
import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "packaging" / "npm"
MANIFEST = PKG / "payload" / "payload-manifest.json"
#: 冒烟用例数下限（防「面塌缩」：删用例比删断言更容易被忽略）
MIN_CASES = 4


#: 网络 / 埋点原语（**静态**可真伪：包若哪天需要联网，这条会先红，逼人改承诺或改做法）
NET_PAT = re.compile(
    r"\bfetch\b|XMLHttpRequest|sendBeacon"
    r"|require\(['\"](?:http|https|net|dns|tls)['\"]\)|from ['\"](?:http|https|net|dns|tls)['\"]"
    r"|posthog|segment\.io|analytics|telemetry|https?://", re.I)


def net_hits(pkg=PKG):
    """→ 包内 JS 里命中网络/埋点原语的行（纯函数，便于变异自证）。"""
    out = []
    for p in sorted(list(pkg.rglob("*.mjs")) + list(pkg.rglob("*.js"))):
        rel = p.relative_to(pkg).as_posix()
        if rel.startswith(("payload/", "node_modules/", "test/")):
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        for n, line in enumerate(text.splitlines(), 1):
            if NET_PAT.search(line):
                out.append("%s:%d %s" % (rel, n, line.strip()[:90]))
    return out


def _node_or_skip(case):
    """两条自检共用的前置：无 node / 未暂存 payload 都显式跳过并写明理由。"""
    node = shutil.which("node")
    if not node:
        case.skipTest("无 node——交付线前置缺失（非本仓缺陷）")
    if not MANIFEST.is_file():
        case.skipTest("payload 未暂存（忽略面；先 node tools/stage-payload.mjs）")
    return node


class NpmPackageGateTest(unittest.TestCase):
    """工作流跑哪两条自检，常驻面就跑哪两条（判据必须接线）。"""

    def test_smoke_suite_passes(self):
        """冒烟套件：sha256 对账 + 启动器快路 + 在已有检出上真跑一条只读命令。"""
        node = _node_or_skip(self)
        proc = subprocess.run([node, "--test", "test/smoke.test.mjs"], cwd=str(PKG),
                              capture_output=True, timeout=900)
        out = (proc.stdout + proc.stderr).decode("utf-8", "replace")
        self.assertEqual(0, proc.returncode, "npm 包冒烟测试未过：\n%s" % out[-1500:])
        passed = re.search(r"pass (\d+)", out)
        self.assertIsNotNone(passed, "冒烟输出里读不到 pass 计数（判据可能已失效）：\n%s" % out[-800:])
        self.assertGreaterEqual(int(passed.group(1)), MIN_CASES,
                                "冒烟用例塌缩（只减不增的判据面不许缩）：\n%s" % out[-800:])
        self.assertIn("fail 0", out, "有失败用例：\n%s" % out[-800:])

    def test_package_has_no_network_or_telemetry_primitives(self):
        """包的公开承诺（README：「零网络请求、零遥测」）必须**可静态核验**，而不是口号。"""
        files = [p for p in list(PKG.rglob("*.mjs")) + list(PKG.rglob("*.js"))
                 if not p.relative_to(PKG).as_posix().startswith(("payload/", "node_modules/", "test/"))]
        self.assertGreaterEqual(len(files), 4, "扫描面塌缩（判据可能已失效）：%s" % files)
        hits = net_hits()
        self.assertEqual([], hits, "包内出现网络/埋点原语（与 README 的「零网络/零遥测」承诺冲突）：%s" % hits[:5])

    def test_install_materializes_a_run_tree(self):
        """物化路径（README 第二种用法 `npx -y narrativeforge install --dest <目录>`）：
        必须真落成**运行时树**——含关键件，且**不含** `.git/`、`.github/`、`results/`。

        为什么补：冒烟套件只用正则断言 `--help` 里**提到**了这条用法，**从未执行过它**；
        而它是 README 列出的第二条用户路径，也是「把 payload 变成可用工作树」的唯一入口。
        """
        node = _node_or_skip(self)
        with tempfile.TemporaryDirectory(dir=str(ROOT / ".rivet")) as tmp:
            dest = Path(tmp) / "nf"
            proc = subprocess.run([node, str(PKG / "bin" / "nf.mjs"), "install", "--dest", str(dest)],
                                  cwd=tempfile.gettempdir(), capture_output=True, timeout=900)
            out = (proc.stdout + proc.stderr).decode("utf-8", "replace")
            self.assertEqual(0, proc.returncode, "物化失败：\n%s" % out[-1200:])
            self.assertIn("已落盘", out, "缺落盘回执：%s" % out[-400:])
            for rel in ("verify.sh", "scripts/nf.py"):
                self.assertTrue((dest / rel).is_file(), "物化树缺关键件 %s：%s"
                                % (rel, sorted(x.name for x in dest.iterdir())[:8]))
            for bad in (".git", ".github", "results"):
                self.assertFalse((dest / bad).exists(),
                                 "物化树混入 %s（README 承诺 payload 是运行时/协议树）" % bad)
            self.assertGreaterEqual(len(list(dest.iterdir())), 5, "物化树件数过少（可能只落了一半）")
            # 非空目录必须 **fail-closed**（rc≠0 + 修复指引），显式 --force 才覆盖
            # 实测（2026-10-03）：非空 → rc=3「✗ 目标非空：…（修复指引：加 --force 覆盖，或换空目录）」
            again = subprocess.run([node, str(PKG / "bin" / "nf.mjs"), "install", "--dest", str(dest)],
                                   cwd=tempfile.gettempdir(), capture_output=True, timeout=900)
            out2 = (again.stdout + again.stderr).decode("utf-8", "replace")
            self.assertNotEqual(0, again.returncode, "非空目标竟被静默覆盖：%s" % out2[-400:])
            self.assertIn("目标非空", out2, out2[-400:])
            self.assertIn("--force", out2, "修复指引里应给出 --force：%s" % out2[-400:])
            forced = subprocess.run([node, str(PKG / "bin" / "nf.mjs"), "install", "--dest", str(dest), "--force"],
                                    cwd=tempfile.gettempdir(), capture_output=True, timeout=900)
            self.assertEqual(0, forced.returncode, "显式 --force 仍失败：%s"
                             % (forced.stdout + forced.stderr).decode("utf-8", "replace")[-400:])

    def test_payload_is_extracted_to_cache_and_runs(self):
        """包的核心机制：**无 --repo 且 cwd 不在仓库树内**时，把随包 payload 解到缓存目录并从那里跑起来。

        为什么补这条：其余用例都靠 `--repo`（或 `--version` 快路）**绕开了这条路径**——而它正是用户
        `npx -y narrativeforge install/doctor` 走的那条；不测它，等于这条交付线的主机制没人跑。
        两个环境细节（都写在判据里，免得后人重踩）：① cwd 必须在**仓库外**，否则 `findRepoRoot` 命中，
        launcher 会直接用该仓库、**不会解包**；② 缓存目录用 `NARRATIVEFORGE_CACHE` 指到**仓库内**
        （本机沙箱**只对 `nf-rs.exe` 写 `%TEMP%` 拒访问**（os error 5）——Python/Node 写 `%TEMP%` 正常，
        实测 e2e 与 npm 物化都写成功；缓存目录因此指到仓库内，不依赖沙箱策略）。
        """
        node = _node_or_skip(self)
        with tempfile.TemporaryDirectory(dir=str(ROOT / ".rivet")) as cache:
            env = dict(os.environ, NARRATIVEFORGE_CACHE=cache)
            proc = subprocess.run([node, str(PKG / "bin" / "nf.mjs"), "doctor"],
                                  cwd=tempfile.gettempdir(), capture_output=True, env=env, timeout=900)
            out = (proc.stdout + proc.stderr).decode("utf-8", "replace")
            self.assertEqual(0, proc.returncode, "解包后从缓存跑 doctor 失败：\n%s" % out[-1200:])
            homes = [p for p in Path(cache).iterdir() if p.is_dir()]
            self.assertTrue(homes, "缓存目录里没有解包家——核心机制没跑（判据可能已失效）：%s" % out[-400:])
            home = homes[0]
            for rel in ("scripts/nf.py", "verify.sh"):
                self.assertTrue((home / rel).exists(), "解包树缺关键件 %s：%s" % (rel, sorted(x.name for x in home.iterdir())[:8]))
            self.assertGreaterEqual(len(list(home.iterdir())), 5, "解包树件数过少（可能只解了一半）")

    def test_package_has_no_install_time_scripts(self):
        """README 承诺「**零安装脚本**」：package.json 不得声明 preinstall / install / postinstall。

        为什么单独判：安装期脚本是供应链攻击最常用的一环（npm i 即执行），而这条承诺**不依赖 node**
        就能核——纯读 package.json。附一条防呆：scripts 里必须仍有自检项（证明读到的是真包声明，
        而不是空对象导致的假绿）。
        """
        import json
        pkg = json.loads((PKG / "package.json").read_text(encoding="utf-8"))
        scripts = pkg.get("scripts") or {}
        bad = sorted(k for k in scripts if k in ("preinstall", "install", "postinstall"))
        self.assertEqual([], bad, "包声明了安装期脚本（与 README 的「零安装脚本」承诺冲突）：%s" % bad)
        self.assertIn("verify", scripts, "scripts.verify 不在（判据可能在读错的件）：%s" % scripts)

    def test_net_predicate_catches_the_mutation(self):
        """变异自证：抓得到 fetch / require('https')，且不误伤正常代码。"""
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp) / "lib"
            d.mkdir(parents=True)
            (d / "a.mjs").write_text("const r = await fetch('x');\nimport https from 'https';\n",
                                     encoding="utf-8")
            (d / "b.mjs").write_text("export function add(a, b) { return a + b; }\n", encoding="utf-8")
            hits = net_hits(Path(tmp))
        self.assertGreaterEqual(len(hits), 2, "变异未被抓到：%s" % hits)
        self.assertTrue(all("a.mjs" in h for h in hits), "误伤：%s" % hits)

    def test_package_verifier_passes(self):
        """发布前自检 `tools/verify-package.mjs`：须 0 issue（查冒烟套件不查的打包面）。"""
        node = _node_or_skip(self)
        proc = subprocess.run([node, "tools/verify-package.mjs"], cwd=str(PKG),
                              capture_output=True, timeout=900)
        out = (proc.stdout + proc.stderr).decode("utf-8", "replace")
        self.assertEqual(0, proc.returncode, "npm 发布前自检未过：\n%s" % out[-1500:])
        self.assertIn("0 issue", out, "自检输出里读不到 issue 计数（判据可能已失效）：\n%s" % out[-800:])


if __name__ == "__main__":
    unittest.main()
