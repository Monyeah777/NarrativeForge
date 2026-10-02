# -*- coding: utf-8 -*-
"""原子写（`core/atomic_write.py`）回归测试：读者不见半截、失败不留残、LF 落盘。

动机（重复调用安全）：仓库把原子写惯用法写在 `disk_cache`/`daemon` 里，而**已发布产物**
的写入口此前是裸 `open(path, "w")`——并发写同一件时读者可能读到半截内容。
"""
import os
import json
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from core import atomic_write as aw  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]


def _load_nf():
    import importlib.util
    spec = importlib.util.spec_from_file_location("nfcli_atomic", ROOT / "scripts" / "nf.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class RepoTruthWritersUseAtomicWriteTest(unittest.TestCase):
    """在仓**真源**写入口不得回退成裸写（静态不变量：registry.json 只有原子写一条路）。

    为什么用静态断言：`registry.json` 是全仓消费真源（verify 各 check、`nf run`/`nf serve`
    都读），而它的两个 `--apply` 写入口在 `nf.py` 里——走一遍 `--apply` 需要真包与真文档
    在场，行为测试代价高、且会动真仓；这里钉的是**不变量**（禁裸写 + 必走原子写），
    行为侧由 `_write_trace_file` 与 `atomic_write` 自身的用例覆盖。
    """

    def test_registry_writers_are_not_bare(self):
        text = (ROOT / "scripts" / "nf.py").read_text(encoding="utf-8")
        self.assertNotIn('open(reg_path, "w"', text,
                         "registry.json 不得再出现裸写（半截真源会被并发 readers 判成不可读）")
        self.assertIn("atomic_write.write_text(reg_path", text,
                      "registry.json 的 --apply 写入口必须走 atomic_write")

    def test_trace_writer_keeps_old_content_on_failed_replace(self):
        from unittest import mock
        nf = _load_nf()
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp, "trace.json")
            self.assertTrue(nf._write_trace_file(str(p), {"a": 1}))
            before = p.read_bytes()
            with mock.patch.object(aw, "_replace", side_effect=PermissionError("busy")):
                self.assertFalse(nf._write_trace_file(str(p), {"a": 2}),
                                 "写失败须如实回 False（自身失败面）")
            self.assertEqual(before, p.read_bytes(),
                             "trace 写失败时必须保留旧全量（读回侧才不会被判成「漂移」）")


class DerivedWritersAreAtomicTest(unittest.TestCase):
    """**派生件写入口**必须走原子写（2026-09-30 收口）。

    依据：`atomic_write` 此前只被 `repo_stats` 用上，其余写 `protocol/*.json` 基线 / INDEX
    投影的入口仍是裸 `open(w)`——agent 密集重复调用（多进程同时 `--write`，或写入期间有人
    跑 verify）时，读者会看到半截 JSON/半截索引。本判据在两个代表性入口上**行为取证**：
    把 `os.replace` 打桩成失败 ⇒ 目标必须保持旧全量，且不留临时件。
    """

    def _fixture(self, tmp):
        root = Path(tmp)
        (root / "a.py").write_text("x = 1\n", encoding="utf-8")
        return root

    def test_code_metrics_baseline_write_is_atomic(self):
        from unittest import mock
        from core import code_metrics as cm
        with tempfile.TemporaryDirectory() as tmp:
            root = self._fixture(tmp)
            cm.write(str(root))                        # 先落一版
            target = root / cm.BASELINE_REL
            before = target.read_text(encoding="utf-8")
            (root / "a.py").write_text("x = 2\ny = 3\n", encoding="utf-8")
            with mock.patch.object(aw, "_replace", side_effect=PermissionError("busy")):
                with self.assertRaises(PermissionError):
                    cm.write(str(root))
            self.assertEqual(before, target.read_text(encoding="utf-8"),
                             "失败时必须保留旧全量（不得留半截）")
            litter = [p.name for p in target.parent.iterdir() if p.name.endswith(".tmp")]
            self.assertEqual([], litter, "失败路径不得留下临时件：%s" % litter)
            cm.write(str(root))                        # 反向：解除打桩后照常可写（仍是合法 JSON）
            json.loads(target.read_text(encoding="utf-8"))

    def test_index_projection_write_is_atomic(self):
        from unittest import mock
        from core import decisions as dc
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "decisions").mkdir()
            (root / "decisions" / "INDEX.md").write_text(
                "# NF 决策记录索引（INDEX）\n\n<!-- nf:index:begin -->\n旧\n<!-- nf:index:end -->\n",
                encoding="utf-8")
            before = (root / dc.INDEX_REL).read_text(encoding="utf-8")
            with mock.patch.object(aw, "_replace", side_effect=PermissionError("busy")):
                with self.assertRaises(PermissionError):
                    dc.write_projection(str(root))
            self.assertEqual(before, (root / dc.INDEX_REL).read_text(encoding="utf-8"),
                             "投影写失败时必须保留旧全量")

    def test_inplace_editors_keep_old_content_on_failed_replace(self):
        """**就地编辑器**（autofix / 素材台账）同样原子：`replace` 失败 ⇒ 旧内容逐字节原样。

        依据（2026-09-30）：这两处此前是裸 `open(w)`——崩在中途会把一份源件/台账截断成半截，
        那是**数据损坏**（比派生件半截更重）。
        """
        from unittest import mock
        from core import asset_ledger as al
        from core import autofix
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp, "doc.md")
            f.write_text("标题\n\n正文带尾随空格   \n", encoding="utf-8")
            before = f.read_bytes()
            with mock.patch.object(aw, "_replace", side_effect=PermissionError("busy")):
                with self.assertRaises(PermissionError):
                    autofix.fix_file(str(f), root=tmp)      # 机械修复：会改写该件
            self.assertEqual(before, f.read_bytes(), "修复失败时必须保留旧内容")

            lp = Path(tmp, "ledger.json")
            al.save_ledger({"assets": []}, str(lp))
            lbefore = lp.read_bytes()
            with mock.patch.object(aw, "_replace", side_effect=PermissionError("busy")):
                with self.assertRaises(PermissionError):
                    al.save_ledger({"assets": [{"a": 1}]}, str(lp))
            self.assertEqual(lbefore, lp.read_bytes(), "台账写失败时必须保留旧全量")

    def test_second_wave_repo_writers_keep_old_content_on_failed_replace(self):
        """第二批**在仓产物**写入口（批准记录 / 知识台账 / 模块签名 / 阶梯文档）同样原子。

        依据（2026-09-30 收口）：静态盘点「argparse/派生值直接进文件 sink」时发现这四处仍是
        裸写（`write_text` / `open(w)`）——它们都落在**仓库内**，而 `verify` 各 check 正好是
        并发读者（批准记录 check35、知识层 check37、模块边界签名 check35、`docs/layers.md`
        被 `layer_model` 自己当常驻语料读）⇒ 半截内容会被判成「内容被改/签名无效」。
        """
        from unittest import mock
        from core import approval
        from core import knowledge as kn
        from core import module_signature as ms
        from core import layer_model as lm
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            # ① 批准记录（protocol/approvals/*.json）
            subject = root / "doc.md"
            subject.write_text("正文\n", encoding="utf-8")
            approval.approve(str(root), "doc.md", "tester", "自测")
            rec = Path(root, approval.DIR_REL, "doc.md.json")
            before = rec.read_bytes()
            with mock.patch.object(aw, "_replace", side_effect=PermissionError("busy")):
                with self.assertRaises(PermissionError):
                    approval.approve(str(root), "doc.md", "tester", "第二次")
            self.assertEqual(before, rec.read_bytes(), "批准记录失败时必须保留旧全量")
            # ② 知识使用频次台账
            kn.write_usage(str(root), {"A": 1})
            up = root / kn.USAGE_REL
            ubefore = up.read_bytes()
            with mock.patch.object(aw, "_replace", side_effect=PermissionError("busy")):
                with self.assertRaises(PermissionError):
                    kn.write_usage(str(root), {"A": 2})
            self.assertEqual(ubefore, up.read_bytes(), "知识台账失败时必须保留旧全量")
            # ③ 模块边界签名基线
            (root / "modules").mkdir()
            (root / "modules" / "M01.md").write_text("# 模块 通用类:M01 · 甲\n",
                                                     encoding="utf-8")
            ms.write(str(root))
            sp = root / ms.BASELINE_REL
            sbefore = sp.read_bytes()
            with mock.patch.object(aw, "_replace", side_effect=PermissionError("busy")):
                with self.assertRaises(PermissionError):
                    ms.write(str(root))
            self.assertEqual(sbefore, sp.read_bytes(), "签名基线失败时必须保留旧全量")
            # ④ 阶梯活文档（docs/layers.md 生成区）
            decl = root / lm.DECL_REL
            decl.parent.mkdir(parents=True, exist_ok=True)
            decl.write_bytes(Path(ROOT, lm.DECL_REL).read_bytes())   # 真源照搬（只需 schema 合法）
            doc = root / lm.DOC_REL
            doc.parent.mkdir(parents=True, exist_ok=True)
            doc.write_text("# 阶梯\n\n%s\n旧\n%s\n" % (lm.MARK_BEGIN, lm.MARK_END),
                           encoding="utf-8")
            lm.write_region(str(root))
            dbefore = doc.read_bytes()
            with mock.patch.object(aw, "_replace", side_effect=PermissionError("busy")):
                with self.assertRaises(PermissionError):
                    lm.write_region(str(root))
            self.assertEqual(dbefore, doc.read_bytes(), "阶梯文档失败时必须保留旧全量")


class AtomicWriteTest(unittest.TestCase):
    def test_lock_file_serializes_and_times_out(self):
        """排他锁语义：同名目标互斥（先入先出），等待超时**如实报错**并带修复指引。"""
        import threading
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp, "shared.json")
            p.write_text("{}", encoding="utf-8")
            order = []

            def worker(tag, hold):
                with aw.lock_file(p, what="probe"):
                    order.append(tag + "-in")
                    time.sleep(hold)
                    order.append(tag + "-out")

            a = threading.Thread(target=worker, args=("A", 0.15))
            b = threading.Thread(target=worker, args=("B", 0.02))
            a.start()
            time.sleep(0.03)
            b.start()
            a.join()
            b.join()
            self.assertEqual(["A-in", "A-out", "B-in", "B-out"], order,
                             "锁未生效（B 在 A 释放前进入）")

            def hold():
                with aw.lock_file(p, what="probe"):
                    time.sleep(0.4)

            h = threading.Thread(target=hold)
            h.start()
            time.sleep(0.05)
            try:
                with aw.lock_file(p, timeout=0.1, what="probe"):
                    self.fail("持锁期间不该拿到锁")
            except TimeoutError as exc:
                self.assertIn("修复指引", str(exc))
            h.join()

    def test_locked_rmw_keeps_both_updates(self):
        """**读-改-写**加锁后不丢更新（跨进程真跑）；锁件落在临时目录，不在仓库里留件。"""
        child = (
            "import json, sys, time, pathlib\n"
            "sys.path.insert(0, sys.argv[3])\n"
            "from core import atomic_write\n"
            "p = pathlib.Path(sys.argv[1])\n"
            "with atomic_write.lock_file(p, what='probe'):\n"
            "    doc = json.loads(p.read_text(encoding='utf-8'))\n"
            "    time.sleep(0.05)\n"
            "    doc['entries'].append(sys.argv[2])\n"
            "    atomic_write.write_text(p, json.dumps(doc) + '\\n')\n")
        for _ in range(3):
            with tempfile.TemporaryDirectory() as tmp:
                target = Path(tmp, "reg.json")
                target.write_text(json.dumps({"entries": []}) + "\n", encoding="utf-8")
                procs = [subprocess.Popen(
                    [sys.executable, "-c", child, str(target), tag,
                     str(Path(__file__).resolve().parent.parent / "src")],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE) for tag in ("A", "B")]
                for pr in procs:
                    pr.wait(timeout=60)
                entries = json.loads(target.read_text(encoding="utf-8"))["entries"]
                self.assertEqual(["A", "B"], sorted(entries),
                                 "加锁后仍丢更新：%s" % entries)

    def test_registry_writers_use_the_lock(self):
        """在仓真源写入口必须套锁（静态钉住，防回退；配合上一条的行为判据）。"""
        src = (ROOT / "scripts" / "nf.py").read_text(encoding="utf-8")
        self.assertIn('atomic_write.lock_file(reg_path', src,
                      "registry.json 的 --apply 写入口未套排他锁（并发会丢更新）")

    def test_read_matches_plain_read(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp, "x.json")
            aw.write_text(p, "{\n  \"a\": 1\n}\n")
            self.assertEqual("{\n  \"a\": 1\n}\n", aw.read_text(p))
            self.assertEqual(p.read_bytes(), aw.read_bytes(p))

    def test_transient_permission_error_is_retried(self):
        """并发原子写下读者会瞬时撞 `PermissionError`（实测 ≈0.09%）——读侧必须短重试。"""
        from unittest import mock
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp, "x.json")
            aw.write_text(p, "{}")
            real_open = open
            state = {"n": 0}

            def flaky(*a, **kw):
                state["n"] += 1
                if state["n"] <= 2:          # 前两次模拟「名字被写侧占用」
                    raise PermissionError(13, "Permission denied", str(p))
                return real_open(*a, **kw)

            with mock.patch("builtins.open", side_effect=flaky):
                self.assertEqual("{}", aw.read_text(p))
            self.assertGreaterEqual(state["n"], 3, "必须真的重试过")

    def test_persistent_permission_error_reraises(self):
        """重试耗尽仍失败 ⇒ 如实抛出（不退化成「读空」——那会把瞬时故障变成错数据）。"""
        from unittest import mock
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp, "x.json")
            aw.write_text(p, "{}")
            with mock.patch("builtins.open", side_effect=PermissionError(13, "denied")):
                with self.assertRaises(PermissionError):
                    aw.read_text(p)

    def test_transient_einval_on_write_is_retried(self):
        """写侧瞬时 `EINVAL(22)`（Windows 杀软/句柄扫描实测）必须重试；持续错如实抛。"""
        from unittest import mock
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp, "x.json")
            real_fsync = os.fsync
            state = {"n": 0}

            def flaky_fsync(fd):
                state["n"] += 1
                if state["n"] <= 2:
                    raise OSError(22, "Invalid argument")
                return real_fsync(fd)

            with mock.patch("os.fsync", side_effect=flaky_fsync):
                aw.write_text(p, "{}\n")
            self.assertEqual("{}\n", p.read_text(encoding="utf-8"))
            self.assertGreaterEqual(state["n"], 3, "必须真的重试过")
            # 持续 EINVAL ⇒ 如实抛（不掩盖）
            with mock.patch("os.fsync", side_effect=OSError(22, "Invalid argument")):
                with self.assertRaises(OSError):
                    aw.write_text(p, "{\"a\": 1}\n")
            self.assertEqual("{}\n", p.read_text(encoding="utf-8"), "失败须保留旧全量")

    def test_write_bytes_round_trip_and_failure_path(self):
        """二进制入口同规（签名锚 `.sig` 走它）：写成功逐字节一致；`replace` 失败保留旧全量。"""
        from unittest import mock
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp, "anchor.sig")
            aw.write_bytes(p, b"\x00\x01\x02")
            self.assertEqual(b"\x00\x01\x02", p.read_bytes())
            with mock.patch.object(aw, "_replace", side_effect=PermissionError("busy")):
                with self.assertRaises(PermissionError):
                    aw.write_bytes(p, b"\xff" * 32)
            self.assertEqual(b"\x00\x01\x02", p.read_bytes(),
                             "失败时必须保留旧全量（不得留半截签名件）")
            litter = [x.name for x in Path(tmp).iterdir() if x.name.endswith(".tmp")]
            self.assertEqual([], litter, "失败路径不得留临时件：%s" % litter)

    def test_round_trip_is_lf(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp, "out.md")
            aw.write_text(p, "a\r\nb\rc\n")
            self.assertEqual(b"a\nb\nc\n", p.read_bytes())

    def test_leaves_no_temp_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp, "out.json")
            aw.write_text(p, "{}")
            self.assertEqual(["out.json"], sorted(os.listdir(tmp)))

    def test_creates_parent_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp, "nested", "deep", "out.txt")
            aw.write_text(p, "x")
            self.assertTrue(p.is_file())

    def test_concurrent_writers_never_expose_partial_content(self):
        """判据核心：读者看到的**永远是完整的一版**（A 或 B），不会是半截拼接。"""
        big_a = "A" * 300000
        big_b = "B" * 300000
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp, "shared.txt")
            aw.write_text(p, big_a)
            stop = threading.Event()
            torn = []

            def writer(payload):
                while not stop.is_set():
                    try:
                        aw.write_text(p, payload)
                    except PermissionError:      # 极端并发下重试耗尽（平台语义，非本判据对象）
                        continue

            def reader():
                while not stop.is_set():
                    try:
                        got = p.read_text(encoding="utf-8")
                    except PermissionError:      # Windows：与 replace 短时互占（平台语义）
                        continue
                    if got not in (big_a, big_b):
                        torn.append(len(got))
                        return

            ts = [threading.Thread(target=writer, args=(big_a,)),
                  threading.Thread(target=writer, args=(big_b,)),
                  threading.Thread(target=reader)]
            for t in ts:
                t.start()
            stop.wait(1.5)
            stop.set()
            for t in ts:
                t.join(timeout=30)
            self.assertEqual([], torn, "读者读到了半截内容（原子性被破坏）")

    def test_failure_path_keeps_target_and_cleans_temp(self):
        """目标不可替换时（用目录占位模拟），既有目标与目录都不应被破坏。"""
        with tempfile.TemporaryDirectory() as tmp:
            blocked = Path(tmp, "target")
            blocked.mkdir()
            with self.assertRaises(OSError):
                aw.write_text(blocked, "x")
            self.assertTrue(blocked.is_dir(), "失败路径不得破坏既有目标")
            self.assertEqual(["target"], sorted(os.listdir(tmp)), "失败路径应清掉临时件")


if __name__ == "__main__":
    unittest.main()
