"""编号命名空间 + 管线 id 避让判据（01 §1.6.11）——直接执行 verify.sh check14 的内嵌程序。

为什么取真件执行而不是同构复刻：这两条判据的唯一实现住在 verify.sh check14 的 heredoc 里；
同构复刻只能证明"我写的副本对"，不能证明门禁对。故本测试按 verification-before-completion
纪律取 verify.sh 真件运行，自己搭一棵最小登记树后逐例注入变异：
类别未在册 / 类内号重号 / 新包裸号越段 / 管线占层位 id / 管线与官方重号 / 管线跨包重号，
并以"合规树零违规"（含 M91-M99 机制段通道）钉住无假阳性。
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VERIFY = ROOT / "verify.sh"
_ANCHOR = re.compile(r"<<'PYEOF'\s+>\"\$NFL_TMP\"/nf_check14\.log")
LAYERS = ["P00", "P10", "P20", "P30", "P40", "P50", "P60", "P70", "P80"]
OFFICIAL_PIPELINES = {"P00", "P01", "P90"}


def check14_program() -> str:
    """从 verify.sh 取出 check14 的内嵌 python 程序（判据唯一实现）。"""
    src = VERIFY.read_text(encoding="utf-8")
    m = _ANCHOR.search(src)
    if not m:
        raise AssertionError("verify.sh 里未找到 check14 内嵌程序锚点（判据实现已改形？）")
    begin = src.index("\n", m.end()) + 1
    end = src.index("\nPYEOF", begin)
    return src[begin:end]


def _proto(pid: str, name: str, pipeline: str, ids: list, cats: list) -> str:
    ids_l = "\n".join('    - "%s"' % i for i in ids)
    cats_l = "\n".join("    - %s" % c for c in cats)
    mods_l = "\n".join('    - id: "%s"\n      desc: 示例' % i for i in ids)
    return (
        "protocol:\n"
        '  schema_version: "2"\n'
        "package:\n"
        "  id: %s\n"
        "  name: %s\n"
        '  version: "1.0.0"\n'
        "  pipeline: %s\n"
        "  module_id_range:\n%s\n"
        "  categories:\n%s\n"
        "  dependencies:\n"
        "    core_only: true\n"
        "    core_modules: [M00]\n"
        "    cross_package: []\n"
        "  references: []\n"
        "  modules:\n%s\n"
        "  assets:\n"
        "    count: 0\n"
        "    readme: README.md\n"
        "  mount_layers:\n"
        "    P40 行为决策: {default: [], available: []}\n"
        % (pid, name, pipeline, ids_l, cats_l, mods_l)
    )


def _write_tree(tmp: Path, pkgs: list) -> None:
    """pkgs = [(目录, id, 显示名, 管线, 编号清单, 类别清单)] → 写最小但在册的登记树。"""
    (tmp / "desktop" / "src" / "core").mkdir(parents=True, exist_ok=True)
    (tmp / "03_管线库").mkdir(parents=True, exist_ok=True)
    for offi in sorted(OFFICIAL_PIPELINES):
        (tmp / "03_管线库" / ("%s_官方件.md" % offi)).write_text(
            "# 管线 %s\n\n```yaml\nid: %s\n```\n" % (offi, offi), encoding="utf-8")
    prots, segs = [], []
    for i, (d, pid, name, pipe, ids, cats) in enumerate(pkgs, start=1):
        pdir = tmp / d
        pdir.mkdir(parents=True, exist_ok=True)
        (pdir / "protocol.yaml").write_text(_proto(pid, name, pipe, ids, cats), encoding="utf-8")
        (pdir / "README.md").write_text(
            "# %s\n\n> 管线：%s｜资产数：0\n" % (name, pipe), encoding="utf-8")
        prots.append({
            "id": pid, "pipeline": pipe, "categories": cats, "schema_version": "2",
            "version": "1.0.0", "module_ids": ids, "assets": {"count": 0},
            "mount_layers": {"P40": {"default": [], "available": []}},
        })
        segs.append("### 8.%d %s（%s/）\n- 模块（%d）：%s\n- 资产（0）：合成夹具\n"
                    % (i, d.split("/")[-1], d, len(ids), "、".join(ids)))
    (tmp / "02_联动注册表.md").write_text(
        "# 合成登记表\n\n## 8. 社区领域包登记表\n" + "".join(segs) + "## 9. 机读投影\n",
        encoding="utf-8")
    (tmp / "desktop" / "src" / "core" / "registry.json").write_text(
        json.dumps({
            "registry_schema_version": 2,
            "mount_points": {lid: {"default": [], "available": []} for lid in LAYERS},
            "protocols": prots,
        }, ensure_ascii=False), encoding="utf-8")


def _run(tmp: Path) -> tuple:
    prog = tmp / "check14_prog.py"
    prog.write_text(check14_program(), encoding="utf-8")
    # 子进程按 UTF-8 读写：真实门禁读文件用显式 encoding='utf-8'，stdout 只进日志（字节）——
    # 这里只是让本测试能把中文错误串按 UTF-8 取回比对，不改变判据本身。
    env = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
    cp = subprocess.run([sys.executable, str(prog)], cwd=str(tmp),
                        capture_output=True, text=True, encoding="utf-8",
                        errors="replace", env=env)
    return cp.returncode, (cp.stdout or "") + (cp.stderr or "")


BASE = [
    ("community/校园情感领域包", "校园情感领域包", "校园情感领域包", "P02",
     ["情感:M22"], ["情感"]),
    ("community/西幻生存领域包", "西幻生存领域包", "西幻生存领域包", "P03",
     ["生存:M10"], ["生存", "世界", "事件"]),
    ("community/测试域包", "测试域包", "测试域包", "P07",
     ["测试类:M01"], ["测试类"]),
]


class Check14NamespaceGate(unittest.TestCase):
    def _case(self, new_ids=None, new_cats=None, new_pipe=None) -> tuple:
        pkgs = [list(p) for p in BASE]
        if new_ids is not None:
            pkgs[2][4] = new_ids
        if new_cats is not None:
            pkgs[2][5] = new_cats
        if new_pipe is not None:
            pkgs[2][3] = new_pipe
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            _write_tree(tmp, [tuple(p) for p in pkgs])
            return _run(tmp)

    def test_compliant_tree_zero_violation(self):
        """正例：类内段（测试类:M01）与机制段（M99）两条通道 + 避让过的管线 → 零违规。"""
        rc, out = self._case()
        self.assertEqual(rc, 0, out)
        rc2, out2 = self._case(new_ids=["M99"])
        self.assertEqual(rc2, 0, out2)

    def test_category_not_registered_is_caught(self):
        rc, out = self._case(new_cats=["别的类"])
        self.assertEqual(rc, 1, out)
        self.assertIn("⑤类内编号类别未在册", out)

    def test_intra_class_duplicate_is_caught(self):
        rc, out = self._case(new_ids=["情感:M22"], new_cats=["情感"])
        self.assertEqual(rc, 1, out)
        self.assertIn("⑤类内号重号", out)

    def test_bare_number_out_of_segment_is_caught(self):
        rc, out = self._case(new_ids=["M01"])
        self.assertEqual(rc, 1, out)
        self.assertIn("⑤裸号越段", out)

    def test_pipeline_on_layer_id_is_caught(self):
        rc, out = self._case(new_pipe="P40")
        self.assertEqual(rc, 1, out)
        self.assertIn("⑧测试域包 管线 id 占用层位 id: P40", out)

    def test_pipeline_conflict_official_is_caught(self):
        rc, out = self._case(new_pipe="P90")
        self.assertEqual(rc, 1, out)
        self.assertIn("⑧测试域包 管线 id 与官方管线重号: P90", out)

    def test_pipeline_conflict_across_packages_is_caught(self):
        rc, out = self._case(new_pipe="P02")
        self.assertEqual(rc, 1, out)
        self.assertIn("⑧管线 id 跨包重号: P02", out)


if __name__ == "__main__":
    unittest.main()
