# -*- coding: utf-8 -*-
"""产出面清单的**落点逃逸**门禁（外来投稿 ⇄ 仓库外写入）。

依据（2026-09-30 实测）：社区域包是**外来投稿**，`outputs/INDEX.json` 的 `path` / `inputs` /
`graph` 出自投稿者之手。此前这些字段直拼 `community/<包>/<path>`——实验把 `path` 改成
`../../../PWNED.mmd` 再跑 `nf output render --write`，文件**真的落到了仓库外**（临时目录根，
实测命中）。写面越界 = 任意文件写；读面同理可越界读（`detect` / schema / 复算都会去读它）。

本件把两件事钉住：① 清单里的越界写法（`..` / 绝对 / 盘符 / 备用数据流）在**写之前**就被拒，
落盘只可能落在仓库内；② 拒得动的同时**不许误伤**——合法路径照常渲染落盘（变异自证）。
"""
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "desktop" / "src"))

from core import output_forms as of  # noqa: E402

PKG = "AI农业域包"
_REFUSAL_MARKS = ("越界", "`..`", "盘符", "备用数据流")


def _refused(issues) -> bool:
    """问题面里出现「越界/形状」拒收（且带修复指引）即算拒收。"""
    return any("修复指引" in i and any(m in i for m in _REFUSAL_MARKS) for i in issues)


def _fixture(root: Path, declared_path: str) -> Path:
    """把真包整棵拷进临时根（`<tmp>/repo`），只改一条声明的产出行（其余保持真实）。

    临时根**自成一层**：越界的落点断言只看 `<tmp>/outside`，不会被 `%TEMP%` 里的无关文件干扰。
    """
    shutil.copytree(ROOT / "community" / PKG, root / "community" / PKG)
    idx_path = root / "community" / PKG / "outputs" / "INDEX.json"
    doc = json.loads(idx_path.read_text(encoding="utf-8"))
    hit = next(e for e in doc["outputs"]
               if (e.get("render") or {}).get("id") == "mermaid-concept-dag")
    hit["path"] = declared_path
    idx_path.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    return idx_path


class DeclaredPathEscapeTest(unittest.TestCase):
    def _run(self, declared_path: str):
        tmp = Path(tempfile.mkdtemp(prefix="nf_out_escape_"))
        self.addCleanup(shutil.rmtree, tmp, True)
        root = tmp / "repo"
        _fixture(root, declared_path)
        issues, rows = of.render_outputs(str(root), write=True)
        return tmp, root, issues, rows

    def test_traversing_declared_path_is_refused_before_writing(self):
        tmp, root, issues, rows = self._run("../../outside/PWNED.mmd")
        self.assertTrue(_refused(issues), issues)
        self.assertFalse([r for r in rows if "PWNED" in str(r.get("path"))], rows)
        self.assertFalse((tmp / "outside").exists(), "文件被写到仓库外了")
        self.assertFalse((root / "outside").exists())

    def test_absolute_and_drive_and_ads_forms_are_refused(self):
        for declared in ("/tmp/PWNED.mmd", "C:PWNED.mmd", "outputs/x.md:hidden",
                         "outputs/NUL", "outputs/CON.txt", "a\x00b.mmd"):
            tmp, root, issues, rows = self._run(declared)
            self.assertTrue(_refused(issues), "%s 未被拒：%s" % (declared, issues))
            self.assertFalse([r for r in rows if "PWNED" in str(r.get("path"))], rows)
            self.assertFalse((tmp / "outside").exists())

    def test_cross_package_declared_path_is_refused(self):
        """跨包越权写：包 A 声明 `community/包 B/outputs/...` → 必须拒（包含性收在本包内）。"""
        other = "AI农业域包的其他包"
        tmp, root, issues, rows = self._run("community/%s/outputs/PWNED.mmd" % other)
        self.assertTrue(_refused(issues), issues)
        self.assertFalse([r for r in rows if "PWNED" in str(r.get("path"))], rows)
        self.assertFalse((root / "community" / other).exists())

    def test_legit_declared_path_still_renders(self):
        """变异自证：同一夹具、合法落点时**必须**照常落盘——判据不是「一律拒」。"""
        tmp, root, issues, rows = self._run("outputs/charts/PWNED.mmd")
        self.assertFalse(_refused(issues), issues)
        self.assertTrue((root / "community" / PKG / "outputs" / "charts" / "PWNED.mmd").is_file())
        self.assertTrue([r for r in rows if str(r.get("path")).endswith("PWNED.mmd")], rows)

    def test_index_verify_reports_escape_as_issue_instead_of_reading_outside(self):
        tmp = Path(tempfile.mkdtemp(prefix="nf_out_verify_"))
        self.addCleanup(shutil.rmtree, tmp, True)
        root = tmp / "repo"
        _fixture(root, "../../outside/PWNED.mmd")
        issues, _stats = of.index_verify(str(root))
        self.assertTrue(_refused(issues), issues)

    def test_pkg_rel_rejects_escape_forms_and_keeps_legit_ones(self):
        for bad in ("../../x.md", "/etc/passwd", "C:x.md", "x.md:hidden", "NUL",
                    "outputs/NUL", "a\x00b.md", ""):
            with self.assertRaises(ValueError, msg=bad):
                of._pkg_rel({"_pkg": PKG}, bad)
        for good in ("outputs/REPORT.json", "assets/DOMAIN_SPEC.md",
                     "community/%s/assets/CONCEPT_GRAPH.md" % PKG):
            self.assertTrue(of._pkg_rel({"_pkg": PKG}, good))


if __name__ == "__main__":
    unittest.main()
