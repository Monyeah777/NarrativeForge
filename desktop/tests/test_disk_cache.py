#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""内容寻址持久缓存（`core.disk_cache`）单测：键的构成 + 不可信即重算 + 有界 + 可关闭。"""
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = str(Path(__file__).resolve().parents[2])
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from core import disk_cache as dc  # noqa: E402


class DiskCacheTest(unittest.TestCase):
    def setUp(self):
        self.home = tempfile.mkdtemp(prefix="nf_diskcache_")
        self._old_home = os.environ.get("NARRATIVE_FORGE_HOME")
        self._old_off = os.environ.pop(dc.ENV_OFF, None)
        os.environ["NARRATIVE_FORGE_HOME"] = self.home

    def tearDown(self):
        if self._old_home is None:
            os.environ.pop("NARRATIVE_FORGE_HOME", None)
        else:
            os.environ["NARRATIVE_FORGE_HOME"] = self._old_home
        if self._old_off is not None:
            os.environ[dc.ENV_OFF] = self._old_off
        shutil.rmtree(self.home, ignore_errors=True)

    def test_round_trip_and_untrusted_entries_are_rejected(self):
        ckey = dc.key("t", "part")
        dc.store("t", ckey, {"A01": 3, "B02": 0})
        self.assertEqual({"A01": 3, "B02": 0}, dc.load("t", ckey))
        self.assertIsNone(dc.load("t", dc.key("t", "other")), "别的键不得命中")
        self.assertIsNone(dc.load("t", ckey, validate=lambda v: False), "校验器否决即当未命中")
        with open(dc.dir_for("t") / ("%s.json" % ckey), "w", encoding="utf-8") as fh:
            fh.write('{"A01": ')                       # 半截 JSON
        self.assertIsNone(dc.load("t", ckey), "坏文件必须拒绝")

    def test_env_switch_disables_read_and_write(self):
        os.environ[dc.ENV_OFF] = "1"
        try:
            ckey = dc.key("t", "part")
            dc.store("t", ckey, {"X": 1})
            self.assertEqual([], list(dc.dir_for("t").glob("*.json"))
                             if dc.dir_for("t").is_dir() else [], "关闭时不得落盘")
            self.assertIsNone(dc.load("t", ckey))
            self.assertFalse(dc.enabled())
        finally:
            os.environ.pop(dc.ENV_OFF, None)

    def test_deferred_store_writes_only_on_flush(self):
        """**延迟写盘**：`store()` 在延迟模式下只入队（盘上什么都不写），`defer_flush()` 才落盘。

        依据（实测 2026-09-29）：一次新内容状态的落盘合计 14–17 ms（守护口径差值实测 20–80 ms），
        而它是**纯写**、只供别的进程（冷进程 / 守护重启）用 ⇒ 守护把它挪到「回包之后」再付，
        客户端不必等。缓存不是事实：中途丢了只是下次重算。
        """
        ckey = dc.key("t_def", "part")
        d = dc.dir_for("t_def")
        self.assertFalse(dc.deferring(), "默认不是延迟模式（单测/冷进程行为一字不动）")
        dc.defer_begin()
        try:
            dc.store("t_def", ckey, {"A": 1})
            left = list(d.glob("*.json")) if d.is_dir() else []
            self.assertEqual([], left, "延迟模式下不得写盘")
            self.assertIsNone(dc.load("t_def", ckey), "延迟模式下读不到（还没落盘）")
        finally:
            self.assertEqual(1, dc.defer_flush(), "flush 应写出 1 条")
        self.assertEqual({"A": 1}, dc.load("t_def", ckey), "flush 之后必须能读到")
        self.assertFalse(dc.deferring(), "flush 后退出延迟模式")

    def test_deferred_drop_writes_nothing(self):
        """异常路径：`defer_drop()` 丢弃队列 ⇒ 盘上不留半截（缓存非事实，丢了只重算）。"""
        ckey = dc.key("t_drop", "part")
        d = dc.dir_for("t_drop")
        dc.defer_begin()
        dc.store("t_drop", ckey, {"B": 2})
        dc.defer_drop()
        self.assertEqual([], list(d.glob("*.json")) if d.is_dir() else [], "丢弃后不得写盘")
        self.assertIsNone(dc.load("t_drop", ckey))

    def test_prune_keeps_only_recent(self):
        """有界：裁剪按批 ⇒ 上限 = `KEEP + PRUNE_EVERY_SMALL`（多留一批，换 8× 少的 prune）。"""
        for i in range(dc.KEEP * 3):
            dc.store("t", dc.key("t", "p%d" % i), {"X": i})
        left = list(dc.dir_for("t").glob("*.json"))
        self.assertLessEqual(len(left), dc.KEEP + dc.PRUNE_EVERY_SMALL, "缓存不得无界增长")

    def test_small_tag_prune_is_batched(self):
        """判据：**小集合标签也按批裁**——`prune` 次数必须远少于写次数。

        依据（实测 2026-09-29）：一次新内容状态里 11 次 `store` 花 33–42 ms，其中 20–23 ms 是
        11 次 `prune`（每次 `glob("*.json")` + 逐件 `stat`）——「小目录裁起来可忽略」的假设不成立。
        """
        calls = []
        orig = dc.prune
        dc.prune = lambda tag, keep=dc.KEEP: calls.append(tag)   # type: ignore[assignment]
        try:
            for i in range(dc.PRUNE_EVERY_SMALL * 3):
                dc.store("t_batch", dc.key("t_batch", "q%d" % i), {"X": i})
        finally:
            dc.prune = orig                                      # type: ignore[assignment]
        self.assertEqual(3, len(calls), "每 %d 次写才裁一次" % dc.PRUNE_EVERY_SMALL)
        self.assertEqual(0, dc._PRUNE_COUNT.get("t_batch", 0), "裁完计数应归零")

    def test_key_covers_tag_parts_code_and_runtime(self):
        base = dc.key("t", "a")
        self.assertNotEqual(base, dc.key("t", "b"), "任一段键不同就必须换键")
        self.assertNotEqual(base, dc.key("other", "a"), "标签不同必须换键")
        real = dc.code_fingerprint
        try:
            dc.code_fingerprint = lambda root=".": "code-A"
            one = dc.key("t", "a")
            dc.code_fingerprint = lambda root=".": "code-B"
            two = dc.key("t", "a")
        finally:
            dc.code_fingerprint = real
        self.assertNotEqual(one, two, "**代码面变了必须换键**（否则改了算法还吃旧账）")

    def test_code_fingerprint_memoizes_per_root_and_resets(self):
        """按根记忆（不重复哈希 41 ms）；`reset_code_fingerprint()` 之后必须看到新代码。

        记忆是必需的：`key()` 每次查缓存都会要这段指纹，不记忆就是每查一次哈希 157 份源码。
        代价是「进程内代码改了不会被自动看见」——所以**守护判定代码换版时必须显式 reset**
        （`daemon._sync_code` 已接上这条钩子）。
        """
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp) / "desktop" / "src" / "core"
            d.mkdir(parents=True)
            f = d / "m.py"
            f.write_text("A = 1\n", encoding="utf-8")
            first = dc.code_fingerprint(tmp)
            self.assertEqual(first, dc.code_fingerprint(tmp), "同内容必须同指纹")
            f.write_text("A = 2\n", encoding="utf-8")
            self.assertEqual(first, dc.code_fingerprint(tmp), "进程内按根记忆（避免每次重哈希）")
            dc.reset_code_fingerprint(tmp)
            self.assertNotEqual(first, dc.code_fingerprint(tmp), "reset 之后必须换指纹")
        with tempfile.TemporaryDirectory() as other:
            d = Path(other) / "desktop" / "src" / "core"
            d.mkdir(parents=True)
            (d / "m.py").write_text("A = 3\n", encoding="utf-8")
            self.assertNotEqual(first, dc.code_fingerprint(other), "换根不得串味")

    def test_runtime_tag_names_interpreter_and_soft_dep(self):
        tag = dc.runtime_tag()
        self.assertIn("%d.%d" % (sys.version_info[0], sys.version_info[1]), tag)
        self.assertIn("yaml=", tag, "软依赖在场与否必须进键")
        self.assertEqual(tag, dc.runtime_tag(), "同一进程内稳定")

    def test_stored_payload_is_plain_json(self):
        """落盘必须是**可读的纯 JSON**（不是 pickle 之类）——取回即用，无代码执行面。"""
        ckey = dc.key("t", "p")
        dc.store("t", ckey, (["a"], {"n": 1}))          # 元组会被 json 规约成数组
        with open(dc.dir_for("t") / ("%s.json" % ckey), encoding="utf-8") as fh:
            raw = json.load(fh)
        self.assertEqual([["a"], {"n": 1}], raw)


class ImportGraphCacheTest(unittest.TestCase):
    """导入图**落盘**的两条契约：① 落盘往返与现算**逐位一致**；② `(mtime_ns, size)` 一变就换键。

    依据（实测 2026-09-29）：一次冷跑里 16 个站点各解析一遍同一批 `core/*.py` 的导入闭包，
    6 站点样本 BFS 就要 133 ms（`quality_depth` 一个 101 ms）——同一份正文的依赖解析是纯函数，
    所以像 `ast-facts` 一样落盘。键含 `(mtime_ns, size)`＋版本位，故「改了源码必须换图」。
    """

    def test_persisted_graph_matches_fresh_parse(self):
        from core import import_graph as ig
        with tempfile.TemporaryDirectory() as tmp:
            core = Path(tmp, "desktop", "src", "core")
            core.mkdir(parents=True)
            (core / "a.py").write_text("from core import b\nimport os\n", encoding="utf-8")
            (core / "b.py").write_text("x = 1\n", encoding="utf-8")
            listing = ig.listing(tmp)
            self.assertIn("a.py", listing, "列目录失败？判据自身要有效")
            fresh = ig.parse((core / "a.py").read_text(encoding="utf-8"))
            first = ig.load_or_parse(tmp, "a", listing["a.py"])
            self.assertEqual(fresh, (first[1], first[2]), "首算必须与现算一致")
            self.assertEqual(("b",), tuple(sorted(first[1])), "只该收 core.* 的静态依赖")
            # ① 落盘往返：第二次必须走持久层且值相同（键相同）
            self.assertEqual(first, ig.load_or_parse(tmp, "a", listing["a.py"]))
            self.assertEqual(ig.dc_digest(tmp, "a", listing["a.py"]),
                             ig.dc_digest(tmp, "a", listing["a.py"]))
            # ② 改正文（**长度也变**）⇒ 键必变，且图跟着换（不许拿旧图当新图）
            # 注意（2026-09-30 实测 flaky）：原夹具把 `b` 改成 `c` ——**同长度**，键只能靠
            # mtime 区分；而 Windows 对短时间内的重复写入会**延迟刷新 last-write 时间**，
            # 整包跑（文件系统压力大）时两个键会撞成同一个，判据偶发假红。夹具改成变长写入
            # （多一行 import），键的区分就不依赖时间戳粒度了。
            (core / "a.py").write_text("from core import c\nimport os\nimport sys\n",
                                       encoding="utf-8")
            (core / "c.py").write_text("y = 1\n", encoding="utf-8")
            listing2 = ig.listing(tmp)
            self.assertNotEqual(ig.dc_digest(tmp, "a", listing["a.py"]),
                                ig.dc_digest(tmp, "a", listing2["a.py"]), "正文变必须换键")
            second = ig.load_or_parse(tmp, "a", listing2["a.py"])
            self.assertEqual(("c",), tuple(sorted(second[1])), "改了依赖就必须重新解析")


if __name__ == "__main__":
    unittest.main()
