# -*- coding: utf-8 -*-
"""MCP 工具面**不得改动仓库**——把「只读」从**名字**证到**行为**（越权写）。

依据（2026-10-02）：`test_mcp_live_e2e` 冻结了「`tools/list` 恰好是那 10 个只读工具名」，
但**名字冻结不等于行为冻结**——把某个 read 处理器改成「顺手补一下索引 / 落一份缓存」，工具表
一个字都不用改，越权写就进来了；`purity_scan` 的 R6 也只管 eval/exec/shell/删除/反序列化这类
**危险调用**，`write_text` / `atomic_write` / `open(..., "w")` 这一族**不在它的类目内**（实测）。

本件两面钉死：
  ① **行为**：把 10 个工具逐个**真调**一遍（含只用真 id 的成功路径），调用前后对整棵工作树
     做 sha256 指纹——必须**逐字节一致**（新建/删除/改写任一文件即红）；
  ② **结构**：处理器的直接调用闭包（lambda → `_tool_*`）里不许出现写 sink；判别力由**变异自证**
     守着（合成一个含 `write_text` 的处理器必须被判出）。
"""
import ast
import builtins
import hashlib
import io
import os
import pathlib
import shutil
import sys
import unittest
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "desktop" / "src"))

from core import mcp_runtime as mrt  # noqa: E402

SKIP_PARTS = {".git", ".rivet", "__pycache__", ".ruff_cache", ".mypy_cache",
              "node_modules", ".pytest_cache"}
#: 写 sink（**精确名**；`open` 另按 mode 实参判，见 `_write_sinks`）
SINK_NAMES = {"write_text", "write_bytes", "atomic_write", "replace", "remove", "unlink",
              "rmtree", "mkdir", "makedirs", "rename", "save_module", "save_asset",
              "save_cache", "set_status"}
_OPEN_MODES = ("w", "a", "x", "+")


def _fingerprint() -> dict:
    """整棵工作树的 sha256 指纹（跳过 .git/.rivet/缓存目录）。"""
    out = {}
    for p in sorted(ROOT.rglob("*")):
        if any(part in SKIP_PARTS for part in p.parts) or not p.is_file():
            continue
        rel = p.relative_to(ROOT).as_posix()
        try:
            out[rel] = hashlib.sha256(p.read_bytes()).hexdigest()
        except OSError:                      # 读不到的件（被占用等）按「在场但内容不可读」记
            out[rel] = "unreadable"
    return out


def _writes_in(node) -> list:
    """AST 节点树里**写 sink** 的调用名（纯函数，变异自证直接喂它）。"""
    out = []
    for call in [c for c in ast.walk(node) if isinstance(c, ast.Call)]:
        fn = call.func
        label = fn.attr if isinstance(fn, ast.Attribute) else (
            fn.id if isinstance(fn, ast.Name) else "")
        if label in SINK_NAMES:
            out.append(label)
        elif label == "open":
            mode = call.args[1] if len(call.args) > 1 else None
            if isinstance(mode, ast.Constant) and isinstance(mode.value, str) \
                    and any(ch in mode.value for ch in _OPEN_MODES):
                out.append("open(%s)" % mode.value)
    return out


def _handler_sinks(src: str) -> list:
    """`TOOL_HANDLERS` 的**直接调用闭包**（各 lambda 及其在本文末调用的 `_tool_*`）里的写 sink。"""
    tree = ast.parse(src)
    handlers = None
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id == "TOOL_HANDLERS" for t in node.targets):
            handlers = node.value
    if handlers is None:
        return ["<找不到 TOOL_HANDLERS>"]
    called, hits = set(), []
    for lam in [n for n in ast.walk(handlers) if isinstance(n, ast.Lambda)]:
        hits += _writes_in(lam.body)
        for c in [x for x in ast.walk(lam.body) if isinstance(x, ast.Call)]:
            if isinstance(c.func, ast.Name):
                called.add(c.func.id)
    for fn in [n for n in ast.walk(tree)
               if isinstance(n, ast.FunctionDef) and n.name in called]:
        hits += _writes_in(fn)
    return sorted(set(hits))


class McpHandlerWriteFreedomTest(unittest.TestCase):
    """结构面：处理器的直接调用闭包里没有写 sink（新加一个会写仓库的工具即红）。"""

    def test_handlers_have_no_write_sinks(self):
        src = (ROOT / "desktop" / "src" / "core" / "mcp_runtime.py").read_text(encoding="utf-8")
        self.assertEqual([], _handler_sinks(src),
                         "MCP 处理器里出现写 sink（工具面必须只读）：%s" % _handler_sinks(src))

    def test_sink_predicate_has_catch_power(self):
        bad = ("TOOL_HANDLERS = {'x_write': lambda a: _tool_bad((a or {}).get('q', ''))}\n\n\n"
               "def _tool_bad(q):\n"
               "    with open(q, 'w', encoding='utf-8') as fh:\n"
               "        fh.write('x')\n")
        self.assertEqual(["open(w)"], _handler_sinks(bad),
                         "合成的写处理器没被判出（判据将永远是绿的）")
        good = ("TOOL_HANDLERS = {'x_read': lambda a: _tool_ok((a or {}).get('q', ''))}\n\n\n"
                "def _tool_ok(q):\n"
                "    with open(q, encoding='utf-8') as fh:\n"
                "        return fh.read()\n")
        self.assertEqual([], _handler_sinks(good), "只读形态不许误报")


class McpToolsDoNotTouchTheRepoTest(unittest.TestCase):
    """行为面：10 个工具真跑一遍——**仓库内一次写操作都不许发生**，工作树逐字节不变。

    两层证据：① **拦截**（确定性、与并发会话无关）：窗口内把写面（`open` 写模式 / `Path` 写方法 /
    `os.replace|remove|rename` / `shutil.move|rmtree` / `atomic_write.write_*`）全部记一笔，
    指向**仓库内**即算越权，一条都不许有；② **指纹**：调用前后对整棵工作树做 sha256 比对
    （先取一次「对照窗」指纹，把并发会话正在改的件排除出去，避免共享工作区里的假红）。
    """

    #: 仓库内写操作记录（窗口内清空；非空即越权写）
    WRITES: list = []

    @classmethod
    def _record(cls, target, how):
        try:
            full = os.path.realpath(str(target))
        except (TypeError, ValueError):        # 非路径实参（如 fd）——不判
            return
        root = os.path.realpath(str(ROOT))
        if full == root or full.startswith(root + os.sep):
            cls.WRITES.append("%s -> %s" % (how, os.path.relpath(full, root)))

    @classmethod
    def _install_write_watch(cls):
        """装写面拦截 → 返回还原函数。

        **踩过的坑（2026-10-02）**：第一版只拦 `builtins.open`，自证时发现 `Path.write_text`
        走的是 `pathlib.Path.open → io.open`，**整个拦截是空转的**（判据会永远绿）。真正要拦的
        是这两条漏斗：`io.open` / `builtins.open`（模块级 `open`），以及 `pathlib.Path.open`
        （`write_text` / `write_bytes` 都从它过）。
        """
        real = {"builtins_open": builtins.open, "io_open": io.open,
                "path_open": pathlib.Path.open,
                "write_text": pathlib.Path.write_text,
                "write_bytes": pathlib.Path.write_bytes,
                "unlink": pathlib.Path.unlink, "mkdir": pathlib.Path.mkdir,
                "os_replace": os.replace, "os_remove": os.remove,
                "os_rename": os.rename, "makedirs": os.makedirs,
                "shutil_move": shutil.move, "shutil_rmtree": shutil.rmtree}
        from core import atomic_write as _aw
        real["aw_text"], real["aw_bytes"] = _aw.write_text, _aw.write_bytes

        def _opened(file, mode="r", *a, **kw):
            if isinstance(mode, str) and any(ch in mode for ch in "wax+"):
                cls._record(file, "open(%s)" % mode)
            return real["io_open"](file, mode, *a, **kw)

        def _path_open(p, mode="r", *a, **kw):
            if isinstance(mode, str) and any(ch in mode for ch in "wax+"):
                cls._record(p, "Path.open(%s)" % mode)
            return real["path_open"](p, mode, *a, **kw)

        def _pathmeth(fn, how):
            def inner(p, *a, **kw):
                cls._record(p, how)
                return fn(p, *a, **kw)
            return inner

        def _func(fn, how):
            def inner(*a, **kw):
                if a:
                    cls._record(a[0], how)
                return fn(*a, **kw)
            return inner

        builtins.open, io.open = _opened, _opened
        pathlib.Path.open = _path_open
        pathlib.Path.write_text = _pathmeth(real["write_text"], "Path.write_text")
        pathlib.Path.write_bytes = _pathmeth(real["write_bytes"], "Path.write_bytes")
        pathlib.Path.unlink = _pathmeth(real["unlink"], "Path.unlink")
        pathlib.Path.mkdir = _pathmeth(real["mkdir"], "Path.mkdir")
        os.replace = _func(real["os_replace"], "os.replace")
        os.remove = _func(real["os_remove"], "os.remove")
        os.rename = _func(real["os_rename"], "os.rename")
        os.makedirs = _func(real["makedirs"], "os.makedirs")
        shutil.move = _func(real["shutil_move"], "shutil.move")
        shutil.rmtree = _func(real["shutil_rmtree"], "shutil.rmtree")
        _aw.write_text = _func(real["aw_text"], "atomic_write.write_text")
        _aw.write_bytes = _func(real["aw_bytes"], "atomic_write.write_bytes")

        def restore():
            builtins.open, io.open = real["builtins_open"], real["io_open"]
            pathlib.Path.open = real["path_open"]
            pathlib.Path.write_text = real["write_text"]
            pathlib.Path.write_bytes = real["write_bytes"]
            pathlib.Path.unlink = real["unlink"]
            pathlib.Path.mkdir = real["mkdir"]
            os.replace, os.remove, os.rename = (real["os_replace"], real["os_remove"],
                                                real["os_rename"])
            os.makedirs = real["makedirs"]
            shutil.move, shutil.rmtree = real["shutil_move"], real["shutil_rmtree"]
            _aw.write_text, _aw.write_bytes = real["aw_text"], real["aw_bytes"]
        return restore

    @staticmethod
    def _sample_args(rt) -> dict:
        """从实时资源面取**真 id**，让工具走成功路径（而不是被参数校验挡在门外）。"""
        found, cursor = {}, None
        while True:
            params = {"cursor": cursor} if cursor else {}
            resp = rt.handle({"jsonrpc": "2.0", "id": 1, "method": "resources/list",
                              "params": params})
            res = (resp.get("result") or {}).get("resources") or []
            for it in res:
                parts = unquote(str(it.get("uri") or ""))[len("nf://repo/"):].split("/")
                if len(parts) >= 2 and parts[0] not in found:
                    found[parts[0]] = parts[1:] if len(parts) > 2 else parts[1]
            cursor = (resp.get("result") or {}).get("nextCursor")
            if not cursor or not res:
                break
        args = {"pipeline_ls": {}, "spec_ls": {}, "knowledge_order": {},
                "registry_query": {"query": "M90"}, "library_search": {"query": "MCP"}}
        if isinstance(found.get("module"), str):
            args["module_read"] = {"module_id": found["module"]}
        if isinstance(found.get("pipeline"), str):
            args["pipeline_read"] = {"pipeline": found["pipeline"]}
        if isinstance(found.get("library"), str):
            args["library_read"] = {"entry_id": found["library"]}
        if isinstance(found.get("pattern"), str):
            args["pattern_read"] = {"pattern_id": found["pattern"]}
        if isinstance(found.get("asset"), list):
            args["asset_get"] = {"key": found["asset"][-1], "package": found["asset"][0]}
        return args

    def test_tools_call_leaves_the_tree_untouched(self):
        rt = mrt.McpRuntime({})
        args = self._sample_args(rt)
        names = [t["name"] for t in mrt.TOOL_DEFS]
        self.assertEqual(set(names), set(mrt.TOOL_HANDLERS), "声明面与派发面不一致")
        self.assertGreaterEqual(len(names), 8, "工具面塌缩（判据可能已失效）")
        before = _fingerprint()
        mid = _fingerprint()                   # 对照窗：不调工具，排除并发会话正在改的件
        self.assertGreaterEqual(len(before), 1000, "指纹面太小（判据可能已失效）")
        stable = {k for k in mid if before.get(k) == mid[k]}
        ok, errors = [], []
        type(self).WRITES = []
        restore = self._install_write_watch()
        try:
            for i, name in enumerate(names):
                resp = rt.handle({"jsonrpc": "2.0", "id": i + 1, "method": "tools/call",
                                  "params": {"name": name, "arguments": args.get(name, {})}})
                (errors if "error" in resp else ok).append(name)
        finally:
            restore()
        after = _fingerprint()
        changed = ([k for k in sorted(stable) if after.get(k) != before[k]]
                   + sorted(set(after) - set(mid)) + sorted(set(mid) - set(after)))
        self.assertEqual([], type(self).WRITES,
                         "工具在**仓库内**做了写操作（越权写）：%s" % type(self).WRITES[:5])
        self.assertEqual([], changed, "调工具改动了工作树（越权写）：%s" % changed[:5])
        self.assertGreaterEqual(len(ok), 6,
                                "成功路径太少（真调没发生，指纹比对等于空转）：成功 %s · 拒绝 %s"
                                % (ok, errors))
        self.assertEqual(len(names), len(ok) + len(errors), "有工具没被调到")

    def test_write_interceptor_has_teeth(self):
        """变异自证：拦截器要是**空转**的（第一版就是这样：只拦 builtins.open），本件就永远绿。

        做法：装同一套拦截，然后在**仓内**（`.rivet/scratch/`，gitignored）真写一个临时件、
        再真删一次——两种写都必须被记下来，随后清理。
        """
        probe = ROOT / ".rivet" / "scratch" / "mcp_write_probe.tmp"
        probe.parent.mkdir(parents=True, exist_ok=True)
        type(self).WRITES = []
        restore = self._install_write_watch()
        try:
            probe.write_text("probe", encoding="utf-8")
            probe.unlink()
        finally:
            restore()
        self.assertTrue(type(self).WRITES,
                        "拦截器没抓到仓内写操作（这层证据是空转的，判据会永远绿）")
        self.assertFalse(probe.exists(), "自检用的临时件没清干净")


if __name__ == "__main__":
    unittest.main()
