#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""42 M3 —— 纯度体检 check27 单测（四规则 + 变异注入捕获力 = check 的 check）。"""
import ast
import os
import sys
import tempfile
import time
import unittest
from pathlib import Path

if str(Path(__file__).resolve().parent.parent / "src") not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from core import purity_scan as ps  # noqa: E402
from core import conformance_scan as csc  # noqa: E402
from core import disk_cache as dc  # noqa: E402

ROOT = str(Path(__file__).resolve().parents[2])


def _write(root, rel, text):
    path = os.path.join(root, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)
    return path


def _reference_doc_facts(text):
    """**未缓存的参考实现**：原先 `_scan_impl` 里那三段「三遍 `splitlines()` + 逐行正则」原样搬来。"""
    shell, private, seen = [], [], {}
    for i, ln in enumerate(text.splitlines(), 1):
        if ps._END_SHELL.search(ln):
            shell.append((i, ln.strip()[:80]))
    for i, ln in enumerate(text.splitlines(), 1):
        if ps._PRIVATE.search(ln):
            private.append((i, ln.strip()[:80]))
    for i, ln in enumerate(text.splitlines(), 1):
        m = ps._HEAD.match(ln)
        if not m:
            continue
        seen.setdefault(m.group(1).strip(), []).append(i)
    return (tuple(shell), tuple(private),
            tuple((t, tuple(v)) for t, v in seen.items() if len(v) > 1))


class PurityKeyCompositionTest(unittest.TestCase):
    """purity 的键由**两张面各自的指纹组合**——覆盖面必须等于原来那一张合面（不许缩）。

    依据（实测 2026-09-29）：过去把 `patterns()`（自有面 + 阶梯面，54 条）交给 `memo_pair` 枚举一遍，
    而 `layer_model.scan()` 内部又把**同一张 45 条的阶梯面**枚举第二遍 ⇒ 一次 `nf score` 白花 ~10 ms。
    改成「自有面指纹 + 阶梯面指纹」组合键、并把阶梯面指纹传给 `layer_model.scan(_fp=...)` 之后，
    `purity.scan` **64 → 51 ms**（`content_fingerprint` 33.9 → 17.4 ms × 2、`iter_files` 93 → 54 次）。
    """

    def test_composed_faces_cover_exactly_the_old_face(self):
        from core import layer_model as lm
        self.assertEqual(set(ps.patterns(ROOT)),
                         set(ps.OWN_PATTERNS) | set(lm.patterns(ROOT)),
                         "组合键的两张面合起来必须等于 patterns()——少一条就是缓存面缺口")

    def test_each_face_fingerprint_is_stable(self):
        from core import conformance_scan as csc
        from core import layer_model as lm
        self.assertEqual(csc.content_fingerprint(ROOT, ps.OWN_PATTERNS),
                         csc.content_fingerprint(ROOT, ps.OWN_PATTERNS), "同内容必须同指纹")
        self.assertEqual(lm.face_fingerprint(ROOT), lm.face_fingerprint(ROOT))


class FileFindingsCacheTest(unittest.TestCase):
    """R4–R6 的**逐件 findings 缓存**：三态（正文变 / 登记表变 / 局部模块集变都要重算）。

    依据（实测 2026-09-29）：R4–R6 要遍历 **546** 份源码，而真正的检查项只有 ~81 条
    （raise 55 / import 14 / sink 12）⇒ 那 ~20 ms 里绝大头是「把 546 份文件逐件重新过一遍」的循环
    开销。逐件缓存后，未变的件连循环体都不进。键 =（相对路径, 正文 sha256, **环境指纹**），
    环境指纹含**局部模块名集**（`_is_local` 的判据）与六张登记表——任一变即重算。
    """

    def test_environment_fingerprint_is_sensitive(self):
        base = ps._env_fingerprint(ROOT)
        self.assertEqual(base, ps._env_fingerprint(ROOT), "同环境必须同指纹")
        orig = ps.SOFT_IMPORTS
        ps.SOFT_IMPORTS = dict(orig)
        ps.SOFT_IMPORTS["判据用探针包"] = "环境敏感判据"
        try:
            self.assertNotEqual(base, ps._env_fingerprint(ROOT), "登记表一变必须换键")
        finally:
            ps.SOFT_IMPORTS = orig
        self.assertEqual(base, ps._env_fingerprint(ROOT), "还原后必须回到原指纹")

    def test_findings_are_content_keyed(self):
        env = ps._env_fingerprint(ROOT)
        text = "import thirdparty_unregistered\n"
        ps._FILE_FINDINGS.clear()
        got, delta = ps._file_findings("scripts/判据探针.py", text, env, ROOT)
        self.assertEqual(1, delta["imports"], delta)
        self.assertTrue(any("未登记" in m for m in got), got)
        self.assertEqual(1, len(ps._FILE_FINDINGS))
        again, _ = ps._file_findings("scripts/判据探针.py", text, env, ROOT)
        self.assertEqual(got, again)
        self.assertEqual(1, len(ps._FILE_FINDINGS), "同内容同环境必须命中")
        other, _ = ps._file_findings("scripts/判据探针.py", text + "# 尾巴\n", env, ROOT)
        self.assertEqual(got, other)
        self.assertEqual(2, len(ps._FILE_FINDINGS), "正文一变必须换键")


class DocFactsTest(unittest.TestCase):
    """R1–R3 的逐件事实缓存（`_doc_facts`）：与未缓存参考实现逐字段等价（真仓库文档 + 合成样本）。

    依据（实测 2026-09-29）：这三条规则过去每次扫描都把 4 份协议文档 `splitlines()` **三遍**、
    逐行跑三个正则，占 `purity_scan._scan_impl` 的一半以上；而事实只是**该件正文**的纯函数。
    """

    def test_real_repo_docs_match_reference(self):
        seen = 0
        for name in ps.PROTO_DOCS:
            p = Path(ROOT) / name
            if not p.is_file():
                continue
            text = p.read_text(encoding="utf-8")
            self.assertEqual(_reference_doc_facts(text), ps._doc_facts(text),
                             "%s 的事实与参考实现不一致" % name)
            seen += 1
        self.assertGreaterEqual(seen, 4, "协议文档太少，判据没测到东西")

    def test_synthetic_samples_match_reference(self):
        samples = ["",
                   "# 标题\n## 标题\n",
                   "正文\r\napk 端壳\r\n## A\n## B\n## A\n",
                   "路径 C:\\Users\\x 与 TODO 与 /tmp/x\n# 同题\n# 同题\n",
                   "\n".join("第 %d 行" % i for i in range(60)) + "\nKivy\n"]
        for text in samples:
            self.assertEqual(_reference_doc_facts(text), ps._doc_facts(text), repr(text[:40]))

    def test_cache_is_content_keyed(self):
        text = "# 唯一标题\n## 甲\n## 甲\n"
        first = ps._doc_facts(text)
        ps._DOC_FACTS_CACHE.clear()
        self.assertEqual(first, ps._doc_facts(text), "同内容第二次必须逐字段相同")
        self.assertEqual((("甲", (2, 3)),), first[2], "重复标题的行号清单不许变形")
        self.assertEqual((), ps._doc_facts("# 唯一标题\n## 甲\n## 乙\n")[2], "无重复即空")


class PurityScanTest(unittest.TestCase):
    def test_mutation_r1_end_shell_captured(self):
        with tempfile.TemporaryDirectory() as tmp:
            _write(tmp, "02_联动注册表.md", "# 注册表\n\nandroid 残留行\n")
            issues, _ = ps.scan(tmp)
            self.assertTrue(any("端壳/APK 残留" in i for i in issues), issues)

    def test_mutation_r2_private_captured(self):
        with tempfile.TemporaryDirectory() as tmp:
            _write(tmp, "01_核心协议.md", "# 协议\n\n临时路径 C:\\Users\\x\\tmp 残留\n")
            issues, _ = ps.scan(tmp)
            self.assertTrue(any("私货/可变物" in i for i in issues), issues)

    def test_mutation_r3_dup_heading_captured(self):
        with tempfile.TemporaryDirectory() as tmp:
            _write(tmp, "06_Agent执行协议.md",
                   "# A\n## 回合执行\n## 回合执行\n")
            issues, _ = ps.scan(tmp)
            self.assertTrue(any("重复标题" in i for i in issues), issues)

    def test_mutation_r4_raise_no_guidance_captured(self):
        with tempfile.TemporaryDirectory() as tmp:
            _write(tmp, "desktop/src/core/bad.py",
                   'def f():\n    raise ValueError("oops")\n')
            issues, stats = ps.scan(tmp)
            self.assertTrue(any("raise 消息缺修复指引" in i for i in issues), issues)
            self.assertEqual(stats["raises"], 1)

    def test_clean_tree_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            _write(tmp, "01_核心协议.md", "# 协议\n## 模块协议\n")
            _write(tmp, "02_联动注册表.md", "# 注册表\n## 模块表\n")
            _write(tmp, "06_Agent执行协议.md", "# 执行\n## 回合执行\n")
            _write(tmp, "07_官方核心出厂与社区预设导航.md", "# 导航\n## 包索引\n")
            _write(tmp, "desktop/src/core/ok.py",
                   'def f():\n    raise ValueError("请先补 x 再继续")\n')
            issues, _ = ps.scan(tmp)
            self.assertEqual(issues, [])

    def test_mutation_r5_unregistered_third_party_captured(self):
        """R5：未登记的第三方硬 import 被抓（core/scripts 面）。"""
        with tempfile.TemporaryDirectory() as tmp:
            _write(tmp, "desktop/src/core/bad.py", "import requests\n")
            issues, stats = ps.scan(tmp)
            self.assertTrue(any("第三方 import 未登记" in i for i in issues), issues)
            self.assertGreaterEqual(stats["imports"], 1)

    def test_r5_soft_declared_and_hard_allowed_pass(self):
        """R5：软导入 + 登记（jsonschema）与硬依赖白名单（yaml）都放行。"""
        with tempfile.TemporaryDirectory() as tmp:
            _write(tmp, "desktop/src/core/ok.py",
                   "import yaml\n"
                   "try:\n"
                   "    from jsonschema import Draft202012Validator\n"
                   "except ImportError:\n"
                   "    Draft202012Validator = None\n")
            issues, _ = ps.scan(tmp)
            self.assertEqual(issues, [])

    def test_r5_declared_soft_import_without_guard_is_caught(self):
        """R5：已登记的软依赖若**裸导入**（无守卫）仍判 FAIL——登记不等于免守卫。"""
        with tempfile.TemporaryDirectory() as tmp:
            _write(tmp, "desktop/src/core/bad.py", "from PySide6.QtGui import QImage\n")
            issues, _ = ps.scan(tmp)
            self.assertTrue(any("未软导入" in i for i in issues), issues)

    def test_r5_residue_is_warn_not_fail(self):
        """R5：登记在 IMPORT_RESIDUE 的存量残留走 WARN 挂账（不判死但不得隐身）。

        真表当前为空（2026-09-20 清理后零残留），故用临时登记注入验证机制本身。
        """
        with tempfile.TemporaryDirectory() as tmp:
            saved = dict(ps.IMPORT_RESIDUE)
            ps.IMPORT_RESIDUE.clear()
            ps.IMPORT_RESIDUE["scripts/legacy_selfcheck.py"] = "测试用残留（带裁决指针）"
            try:
                _write(tmp, "scripts/legacy_selfcheck.py", "from ghost.controller import C\n")
                issues, stats = ps.scan(tmp)
                self.assertEqual(issues, [])
                self.assertTrue(any("残留" in w for w in stats["import_residue"]), stats)
                # 同一文件若未登记 → 判 FAIL（登记才是豁免的唯一出口）
                ps.IMPORT_RESIDUE.clear()
                issues2, _ = ps.scan(tmp)
                self.assertTrue(any("未登记" in i for i in issues2), issues2)
            finally:
                ps.IMPORT_RESIDUE.clear()
                ps.IMPORT_RESIDUE.update(saved)

    def test_mutation_r6_dangerous_sinks_captured(self):
        """R6：动态执行 / shell 命令 / 不安全反序列化逐个被抓（core/scripts 面）。"""
        cases = {
            "eval": ("desktop/src/core/s1.py", "eval('1+1')\n"),
            "exec": ("desktop/src/core/s2.py", "exec('x=1')\n"),
            "os.system": ("desktop/src/core/s3.py", "import os\nos.system('ls')\n"),
            "shell=True": ("scripts/s4.py",
                           "import subprocess\nsubprocess.run('ls', shell=True)\n"),
            "pickle.loads": ("desktop/src/core/s5.py", "import pickle\npickle.loads(b'')\n"),
            "yaml.load": ("desktop/src/core/s6.py", "import yaml\nyaml.load('a: 1')\n"),
        }
        for label, (rel, body) in cases.items():
            with tempfile.TemporaryDirectory() as tmp:
                _write(tmp, rel, body)
                issues, stats = ps.scan(tmp)
                self.assertTrue(any("危险 sink" in i for i in issues),
                                "%s 未被捕获：%s" % (label, issues))
                self.assertGreaterEqual(stats.get("sinks", 0), 1)

    def test_r6_registered_sink_allowed(self):
        """R6：登记在 SINK_ALLOW 的受控用法放行（放行须可审计）；未登记即 FAIL。"""
        with tempfile.TemporaryDirectory() as tmp:
            saved = dict(ps.SINK_ALLOW)
            ps.SINK_ALLOW.clear()
            ps.SINK_ALLOW["guarded.py:__import__"] = "测试用登记（模块名来自内部常量表）"
            try:
                _write(tmp, "desktop/src/core/guarded.py",
                       "def f(name):\n    return __import__('core.%s' % name)\n")
                issues, _ = ps.scan(tmp)
                self.assertEqual([i for i in issues if "危险 sink" in i], [])
                ps.SINK_ALLOW.clear()
                issues2, _ = ps.scan(tmp)
                self.assertTrue(any("危险 sink" in i for i in issues2), issues2)
            finally:
                ps.SINK_ALLOW.clear()
                ps.SINK_ALLOW.update(saved)

    def test_r6_real_repo_sink_surface_is_declared(self):
        """真仓库：危险 sink 面只剩已登记项。

        2026-09-24（渗透 F-10）起 sink 类目扩了**递归删除面**（shutil.rmtree / os.remove /
        os.rmdir）——该面此前零判据，正是 F-10 能长期存在的原因。基线由 1（受控 __import__）
        升到 5：__import__ ×1 + shutil.rmtree ×4（storage.py 三处同键 + e2e 自检一处），
        全部在 SINK_ALLOW 在册；本断言即「类目扩了、放行仍可审计」的守门。

        2026-09 再扩**方法名类 sink**（`METHOD_SINKS`：`x.unlink()` 与 `os.remove` 同险，
        但被调者名字随接收者变、按整串匹配会整类漏掉）——当时本仓 core 里有 **6 处 `.unlink()`**
        全部一路绿灯穿过 R6，基线随之 5 → **12**（新增 6 处已登记站点：disk_cache / domain_pack /
        pack_combo / storage / watch ×2）。
        """
        issues, stats = ps.scan(ROOT)
        self.assertEqual([i for i in issues if "危险 sink" in i], [],
                         "真仓库出现未登记 sink 即 FAIL")
        self.assertLessEqual(stats.get("sinks", 0), 12)


class SinkRegistryTest(unittest.TestCase):
    """R6 自洽面（本波净吸收）：sink 类目须带 CWE 对齐 + SINK_ALLOW 须指向已登记 sink。"""

    def test_repo_registry_is_self_consistent(self):
        issues, _ = ps.scan(ROOT)
        self.assertEqual([i for i in issues if "CWE" in i or "SINK_ALLOW" in i], [],
                         "仓库 sink 登记面须自洽")
        for call, desc in ps.DANGEROUS_CALLS.items():
            self.assertRegex(desc, r"^CWE-\d+ ", call)

    def test_mutation_missing_cwe_captured(self):
        original = dict(ps.DANGEROUS_CALLS)
        try:
            ps.DANGEROUS_CALLS["eval"] = "动态执行（无 CWE 对齐）"
            issues, _ = ps.scan(ROOT)
        finally:
            ps.DANGEROUS_CALLS.clear()
            ps.DANGEROUS_CALLS.update(original)
        self.assertTrue(any("缺 CWE 对齐" in i for i in issues), issues)

    def test_mutation_allow_key_for_unknown_sink_captured(self):
        original = dict(ps.SINK_ALLOW)
        try:
            ps.SINK_ALLOW["ghost.py:totally_unknown"] = "凭空放行（负例）"
            issues, _ = ps.scan(ROOT)
        finally:
            ps.SINK_ALLOW.clear()
            ps.SINK_ALLOW.update(original)
        self.assertTrue(any("指向未登记 sink" in i for i in issues), issues)

    def test_mutation_unregistered_rmtree_captured(self):
        """F-10 同类面：未登记的递归删除须被 R6 捕获（该面此前**零判据**）。"""
        with tempfile.TemporaryDirectory() as tmp:
            _write(tmp, "scripts/poc_rmtree.py",
                   "import shutil\n\n\ndef wipe(p):\n    return shutil.rmtree(p)\n")
            issues, _ = ps.scan(tmp)
        hits = [i for i in issues
                if i.replace("\\", "/").startswith("scripts/poc_rmtree.py")
                and "shutil.rmtree" in i]
        self.assertTrue(hits, "未登记的 shutil.rmtree 应被 R6 捕获：%s" % issues)

    def test_mutation_unlink_sink_captured(self):
        """**方法名类** sink：`x.unlink()` 与 `os.remove` 同险，但被调者名字随接收者变
        （`old.unlink` / `Path('x').unlink` …）——按整串匹配会**整类漏掉**。

        2026-09 实测：本仓 core 里当时有 6 处 `.unlink()` 一路绿灯穿过 R6；本条判据把这一类钉住，
        放行键也用方法名（`<文件基名>:unlink`），不随变量名漂移。
        """
        with tempfile.TemporaryDirectory() as tmp:
            _write(tmp, "desktop/src/core/m_del.py",
                   "from pathlib import Path\n\n\ndef drop(name):\n"
                   "    return Path(name).unlink()\n")
            issues, _ = ps.scan(tmp)
        hits = [i for i in issues
                if i.replace("\\", "/").startswith("desktop/src/core/m_del.py")
                and "危险 sink unlink" in i]
        self.assertTrue(hits, "未登记的 .unlink() 应被 R6 捕获：%s" % issues)
        # 放行须以**方法名**为键（不随接收者变量名漂移）：登记 m_del.py:unlink 后即静默
        saved = dict(ps.SINK_ALLOW)
        try:
            ps.SINK_ALLOW["m_del.py:unlink"] = "测试用登记：本条同时证明放行键是**方法名**"
            with tempfile.TemporaryDirectory() as tmp2:
                _write(tmp2, "desktop/src/core/m_del.py",
                       "from pathlib import Path\n\n\ndef drop(name):\n"
                       "    return Path(name).unlink()\n")
                issues2, _ = ps.scan(tmp2)
        finally:
            ps.SINK_ALLOW.clear()
            ps.SINK_ALLOW.update(saved)
        self.assertEqual([i for i in issues2 if "危险 sink" in i], [],
                         "以方法名为键的登记必须能放行")

    def test_registered_rmtree_sites_are_audited(self):
        """两个已登记放行点须仍在册（放行不能凭空消失）。"""
        self.assertIn("shutil.rmtree", ps.DANGEROUS_CALLS)
        self.assertIn("e2e_desktop_headless.py:shutil.rmtree", ps.SINK_ALLOW)
        self.assertIn("storage.py:shutil.rmtree", ps.SINK_ALLOW)

    # ---- R7：抽象阶梯归属与越界（真源 protocol/LAYERS.json；语义判据在 core/layer_model）----
    H_MIN = {"schema": "nf-layers/1", "vocabulary": {"status": ["active"]},
             "rules": [{"id": "L1", "statement": "样例"}],
             "tiers": [{"id": "contract", "name": "契约", "order": 0, "status": "active",
                        "change_tier": "bump", "source": {"globs": ["a/*.md"]},
                        "interface": {"globs": ["a/keep.md"]}, "depends_on": [],
                        "judged_by": ["check1"]}],
             "asset_levels": [], "surfaces": [], "derived": []}

    def _ladder_tree(self, tmp, tiers=None):
        import json as _json
        from core import layer_model as _lm
        doc = dict(self.H_MIN)
        doc["tiers"] = tiers or self.H_MIN["tiers"]
        _write(tmp, "protocol/LAYERS.json", _json.dumps(doc, ensure_ascii=False))
        _write(tmp, "protocol/assertions.json", '{"schema": "nf-assertions/1", "assertions": []}')
        _write(tmp, "verify.sh", "#!/usr/bin/env bash\ncheck1(){\n  :\n}\n")
        _write(tmp, "a/keep.md", "x\n")
        _write(tmp, "docs/layers.md",
               "# t\n\n%s\n%s\n%s\n" % (_lm.MARK_BEGIN, _lm.render_markdown(doc), _lm.MARK_END))

    def test_r7_ladder_violation_is_captured(self):
        """R7 接线：阶梯违规必须汇入纯度报告（此处用「真源面展开为空」触发 L1）。"""
        with tempfile.TemporaryDirectory() as tmp:
            self._ladder_tree(tmp, tiers=[{
                "id": "contract", "name": "契约", "order": 0, "status": "active",
                "change_tier": "bump", "source": {"globs": ["ghost/*.md"]},
                "interface": {"globs": ["a/keep.md"]}, "depends_on": [],
                "judged_by": ["check1"]}])
            issues, stats = ps.scan(tmp)
            self.assertTrue(any(i.startswith("L1") for i in issues), issues)
            self.assertEqual(stats.get("layers", {}).get("tiers"), 1)

    def test_r7_skipped_when_ladder_absent(self):
        """合成树无阶梯件时 R7 不误伤（缺件由断言表与规范性名单另判，不静默）。"""
        with tempfile.TemporaryDirectory() as tmp:
            _write(tmp, "01_核心协议.md", "# 协议\n## 模块协议\n")
            issues, stats = ps.scan(tmp)
            self.assertEqual(issues, [])
            self.assertIn("skipped", stats.get("layers", {}))

    def test_ast_facts_cache_is_content_keyed(self):
        """AST 事实缓存必须**按内容**（不是按路径）：同文命中、改文重算。

        这是「常驻进程不得陈旧」的一半：键即内容 ⇒ 文本没变必然同结果、文本变了键就变。
        """
        src = "import os\n\n\ndef f():\n    raise ValueError('缺修复指引：x')\n"
        first = ps._facts_for(src)
        self.assertIsNotNone(first, "含 raise/import 的文本必须产出事实")
        self.assertIs(ps._facts_for(src), first, "同文必须命中缓存（复用同一份事实）")
        changed = src + "\nprint('新内容')\n"
        self.assertIsNot(ps._facts_for(changed), first, "文本变了必须重新解析（不许陈旧）")

    def test_transient_file_edit_is_seen_by_next_scan(self):
        """临时目录里改文件 → 下一次扫描必须看到新结果（按内容缓存的必然推论）。"""
        with tempfile.TemporaryDirectory() as tmp:
            p = _write(tmp, "desktop/src/core/m_probe.py",
                       "raise ValueError('旧文案')\n")
            first, _ = ps.scan(tmp)
            with open(p, "w", encoding="utf-8") as fh:
                fh.write("raise ValueError('新文案')\n")
            second, _ = ps.scan(tmp)
        self.assertNotEqual(first, second, "改文之后结果必须随内容变")

    def test_second_scan_reuses_content_caches(self):
        """常驻复用判据（**确定性**，不靠计时）：两次扫描之间不得再解析任何 `.py`。

        计时版口径太糙（读盘成本是地板，实测只差 1.9×）；直接数 `ast.parse` 调用才是这件事
        本身：第二次必须**零解析**（AST 事实全部命中内容键缓存）；若缓存被误改成「每次清空」，
        第二次就会重新解析 → 立刻红。

        口径（2026-09 修订）：事实现在有两层缓存（进程内 + **持久**），所以「第一次一定真解析
        上百份」不再是真不变量——**先在两层都关掉的最冷状态下证明计数器有效**（必须 >100），
        再测真不变量（第二次零新增）。
        """
        orig_parse = ps.ast.parse
        calls: list = []

        def counting_parse(src, *a, **k):
            calls.append(1)
            return orig_parse(src, *a, **k)

        def scan_with_counter():
            calls.clear()
            ps.scan(ROOT)
            return len(calls)

        # ① 最冷状态（进程内 + 持久都不可用）→ 计数器必须真的数到大数，否则判据本身没测到东西
        old_off = os.environ.get(dc.ENV_OFF)
        os.environ[dc.ENV_OFF] = "1"
        ps.ast.parse = counting_parse          # type: ignore[assignment]
        try:
            ps._FACTS_CACHE.clear()
            ps._FILE_FINDINGS.clear()      # 逐件 findings 层也算一层：最冷状态必须一起清
            cold = scan_with_counter()
        finally:
            if old_off is None:
                os.environ.pop(dc.ENV_OFF, None)
            else:
                os.environ[dc.ENV_OFF] = old_off
        self.assertGreater(cold, 100, "最冷状态下应真解析上百份 .py（判据自身要有效）")

        # ② 真不变量：同内容第二次**零新增**（无论这次是进程内命中还是持久命中）
        ps._FACTS_CACHE.clear()
        ps.ast.parse = counting_parse          # type: ignore[assignment]
        try:
            first = scan_with_counter()
            second = scan_with_counter()
        finally:
            ps.ast.parse = orig_parse          # type: ignore[assignment]
        # 残余的个位数解析来自 layer_model 的 L6（同 A7 文本预筛后解析命中文件）——它与本
        # 判据的缓存不是一个模块，且只涉极少数文件；真正要求的是「少一个数量级」。
        self.assertLessEqual(second, 3, "第二次只允许 L6 预筛命中的极少数解析：%d" % second)
        self.assertLessEqual(second, max(1, first), "第二次不得比第一次多解析：%d vs %d"
                             % (second, first))


class AstFactsPersistenceTest(unittest.TestCase):
    """R4–R6 事实的**可序列化重构 + 持久化**：等价、可往返、跨进程可复用。

    为什么动这段：一次冷进程 `evaluate` 里 AST 面要解析 134–235 份 core/scripts 源码
    （**0.98 s**）。原实现把 `ast.Call` **节点**带出遍历、到 R6 再 `ast.unparse`——节点不可
    序列化，所以事实只能活在进程内。改成"遍历时就摘成 `(行号, 被调名, 是否 shell=True)` 三元组"
    后，整份事实成了纯数据，可按**文件文本**内容寻址落盘。

    动的是**安全判据**（危险 sink），所以三道判据一起上：**等价性**（与旧的 AST 走查逐条同结果）、
    **往返性**（打包/解包后逐位相等）、**持久性**（新进程真从盘上取回）。
    """

    def _code_texts(self):
        out = []
        for pat in ("desktop/src/**/*.py", "scripts/**/*", ".github/**/*.py"):
            for rel in csc.iter_files(ROOT, pat):
                p = Path(ROOT) / rel
                if p.suffix == ".py":
                    out.append((rel, p.read_text(encoding="utf-8")))
        return out

    @staticmethod
    def _flags_from_sinks(sinks):
        """新形态（三元组）→ 与旧实现同形的「(行号, flags)」序列。"""
        out = []
        for lineno, call, shell_true in sinks:
            flags = []
            if call in ps.DANGEROUS_CALLS:
                flags.append(call)
            if shell_true:
                flags.append("subprocess(shell=True)")
            out.append((lineno, tuple(flags)))
        return out

    @staticmethod
    def _flags_by_old_walk(src):
        """**参考实现**（改动前的做法）：`ast.walk` 拿节点、逐节点 unparse + 查 shell 关键字。"""
        out = []
        for node in ast.walk(ast.parse(src)):
            if not isinstance(node, ast.Call):
                continue
            flags = []
            call = ast.unparse(node.func)
            if call in ps.DANGEROUS_CALLS:
                flags.append(call)
            for kw in node.keywords:
                if kw.arg == "shell" and isinstance(kw.value, ast.Constant) \
                        and kw.value.value is True:
                    flags.append("subprocess(shell=True)")
            out.append((node.lineno, tuple(flags)))
        return out

    #: **合成样本**：真仓库里 `shell=True` 只出现在注释里（不是可执行代码），
    #: 只靠真仓库对照**分辨不出** shell 分支被改坏——所以每条危险类目都要有活体样本，
    #: 外加一条「开了 shell 的关键字」与一条「没开 shell 的对照」。
    SAMPLES = (
        "import subprocess\nsubprocess.run('ls', shell=True)\n",
        "import subprocess\nsubprocess.run(['ls'])\n",          # 对照：没开 shell
        "import os\nos.system('x')\n",
        "import pickle\npickle.loads(b'')\n",
        "import shutil\nshutil.rmtree('x')\n",
        "eval('1')\nexec('1')\n",
        "__import__('os')\n",
        "raise ValueError('缺修复指引：x')\n",
    )

    def test_sinks_are_equivalent_to_the_old_ast_walk(self):
        """**全仓逐文件对照**：新形态产出的 flags 序列必须与旧走查**逐条相同**。"""
        checked = 0
        for rel, src in self._code_texts():
            facts = ps._facts_for(src)
            if facts is None:
                self.assertIsNone(ps._NEEDS_AST.search(src),
                                  "预筛不中却含 AST 关注点：%s" % rel)
                continue
            checked += 1
            self.assertEqual(self._flags_by_old_walk(src),
                             self._flags_from_sinks(facts[3]),
                             "危险 sink 面与旧实现不等价：%s" % rel)
        self.assertGreater(checked, 50, "等价性判据必须真覆盖到足够多的源码件")

    def test_sink_categories_are_exercised_by_synthetic_samples(self):
        """合成样本逐条对照（含 shell=True 与其对照）+ **自证判据有分辨力**。"""
        saw_shell = False
        for src in self.SAMPLES:
            ps._FACTS_CACHE.pop(src, None)
            facts = ps._facts_for(src)
            self.assertIsNotNone(facts, "样本应产出事实：%r" % src[:40])
            want = self._flags_by_old_walk(src)
            self.assertEqual(want, self._flags_from_sinks(facts[3]), "样本不等价：%r" % src[:40])
            # 注意：`f` 是**标志元组**，这里要比的是「元组里有没有那个标志」——
            # 写成 `"shell=True" in f` 是元素相等判定，永远为假（本判据自己也踩过）。
            saw_shell = saw_shell or any(flag == "subprocess(shell=True)"
                                         for _ln, flags in want for flag in flags)
        self.assertTrue(saw_shell, "样本里必须真出现 shell=True——否则这条判据测不到那个分支")

    def test_facts_pack_round_trip_is_exact(self):
        """打包/解包必须**逐位还原**（元组回元组、集合回集合），否则取回的结果会悄悄变形状。"""
        checked = 0
        for rel, src in self._code_texts():
            facts = ps._facts_for(src)
            self.assertEqual(facts, ps._unpack_facts(ps._pack_facts(facts)),
                             "往返不等：%s" % rel)
            checked += 1
        self.assertGreater(checked, 50)
        self.assertIsNone(ps._unpack_facts(ps._pack_facts(None)),
                          "None 是合法结果（预筛不中 / 语法错），往返也要保持")

    def test_facts_survive_a_fresh_process_via_disk(self):
        """端到端：清掉进程内缓存（模拟新进程）→ 必须**真从盘上取回**，且与现算逐位相同。"""
        import shutil
        if not dc.enabled():
            self.skipTest("磁盘缓存被 %s 关闭" % dc.ENV_OFF)
        _rel, src = self._code_texts()[0]
        home = tempfile.mkdtemp(prefix="nf_astfacts_")
        old_home = os.environ.get("NARRATIVE_FORGE_HOME")
        os.environ["NARRATIVE_FORGE_HOME"] = home
        try:
            ps._FACTS_CACHE.clear()          # 先清进程内：第一次必须**真算并落盘**
            fresh = ps._facts_for(src)
            ps._FACTS_CACHE.clear()
            seen = []
            real = dc.load

            def spy(tag, ckey, validate=None):
                got = real(tag, ckey, validate=validate)
                if tag == "ast-facts":
                    seen.append(got is not None)
                return got

            dc.load = spy
            ps.disk_cache.load = spy
            try:
                again = ps._facts_for(src)
            finally:
                dc.load = real
                ps.disk_cache.load = real
            self.assertEqual(fresh, again, "盘上取回的事实必须与现算相等")
            self.assertTrue(seen and all(seen), "第二次必须真走盘（否则新进程仍要重解析）")
        finally:
            ps._FACTS_CACHE.clear()
            if old_home is None:
                os.environ.pop("NARRATIVE_FORGE_HOME", None)
            else:
                os.environ["NARRATIVE_FORGE_HOME"] = old_home
            shutil.rmtree(home, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
