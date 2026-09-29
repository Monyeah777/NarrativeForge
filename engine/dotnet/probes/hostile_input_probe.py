#!/usr/bin/env python3
"""敌意输入探针：坏输入只许**受控失败**（可读错误 + exit 2）或给裁决（0/1），**不许崩、不许挂**。

为什么单开一面：正向/负例/差分三套探针都在「输入还能被解析」的范围内工作。工业级引擎还要回答
另一个问题——**当输入本身是敌意的（超深嵌套 / 目录环 / 巨行 / 海量文件 / 巨型宽度）时，它会不会
把门禁变成"卡住"或"崩栈"**。卡住比判错更糟：门禁挂住，整条流水线都要人来看。

判定口径（每格）：
  VERDICT      exit 0/1（正常裁决，含"判红"）
  CONTROLLED   exit 2（受控失败：有可读错误文案）
  CRASH        exit ∉ {0,1,2}（崩栈/未处理异常逃逸）
  HANG        超时（本探针唯一允许的"未决"分类：必须修）
  SILENT       exit∉{0,1,2} 且无任何输出（最坏：无声死亡）

用法：
    python probes/hostile_input_probe.py --cli <nf-dotnet.exe> [--work <目录>] [--timeout 90]

退出码：0 无 CRASH/HANG/SILENT；1 有。全部语料只写工作目录，不碰仓库。
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path


def write(root: Path, rel: str, text: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def skeleton(root: Path) -> None:
    """最小合法骨架：CLI 会先检查 root/protocol 存在。"""
    (root / "protocol").mkdir(parents=True, exist_ok=True)


# ------------------------------------------------------------------ 语料构造

def build_deep_json(root: Path, depth: int) -> str:
    skeleton(root)
    nested = "[" * depth + "]" * depth
    write(root, "protocol/glossary.json",
          json.dumps({"schema": "nf-glossary/1", "terms": json.loads(nested)}, ensure_ascii=False))
    return "protocol/glossary.json 里嵌了 %d 层数组" % depth


def build_deep_yaml(root: Path) -> str:
    skeleton(root)
    depth = 400
    lines = ["```yaml", "machine_contract:", "  schema: \"1\"", "  id: DEEP:M01", "  layer: P40",
             "  nested:"]
    for i in range(depth):
        lines.append("  " * (i + 2) + "k%d:" % i)
    lines.append("  " * (depth + 2) + "leaf: 1")
    lines.append("```")
    write(root, "community/DeepPack/protocol.yaml",
          "protocol:\n  schema_version: \"2\"\npackage:\n  id: DeepPack\n  pipeline: P99\n"
          "  module_id_range:\n    - \"DEEP:M01\"\n  mount_layers:\n    P40: {default: [DEEP:M01]}\n")
    write(root, "community/DeepPack/modules/M01.md", "\n".join(lines) + "\n")
    return "module contract 里嵌了 %d 层缩进映射（每层 2 空格，共约 %d KB）" % (depth, depth * depth // 1000)


def build_dir_depth(root: Path) -> str:
    skeleton(root)
    depth = 0
    current = root / "docs"
    current.mkdir(parents=True, exist_ok=True)
    try:
        for i in range(4000):
            current = current / "d"
            current.mkdir(exist_ok=True)
            depth += 1
    except OSError:
        pass
    write(root, "protocol/assertions.json", json.dumps({
        "schema": "nf-assertions/1",
        "severity_vocabulary": ["fail", "warn"],
        "kind_vocabulary": ["regex_absent", "regex_present", "count_at_least", "json_value"],
        "assertions": [{"id": "deep-glob", "severity": "fail", "kind": "regex_absent",
                        "params": {"globs": ["docs/**/*"], "pattern": "绝不出现的串"},
                        "message": "深目录", "fix": "—"}],
    }, ensure_ascii=False, indent=2))
    return "docs/ 嵌套 %d 层（受本机路径长度上限约束）+ 断言表指向 docs/**/*" % depth


def build_junction_loop(root: Path) -> str:
    skeleton(root)
    write(root, "protocol/assertions.json", json.dumps({
        "schema": "nf-assertions/1",
        "severity_vocabulary": ["fail", "warn"],
        "kind_vocabulary": ["regex_absent", "regex_present", "count_at_least", "json_value"],
        "assertions": [{"id": "loop-glob", "severity": "fail", "kind": "regex_absent",
                        "params": {"globs": ["docs/**/*"], "pattern": "绝不出现的串"},
                        "message": "目录环", "fix": "—"}],
    }, ensure_ascii=False, indent=2))
    write(root, "docs/real.md", "# 真件\n")
    loop = root / "docs" / "loop"
    made = False
    try:
        # Windows：junction 不需要管理员权限；POSIX：符号链接
        if os.name == "nt":
            subprocess.run(["cmd", "/c", "mklink", "/J", str(loop), str(root / "docs")],
                           capture_output=True, check=True)
        else:
            loop.symlink_to(root / "docs", target_is_directory=True)
        made = True
    except Exception as exc:                                    # 造不出来就如实记下
        return "目录环：**未能构造**（%s）——本条不计入判据" % exc
    return "docs/loop/ 是指回 docs/ 的目录环（made=%s）" % made


def build_patterns_wildcard_loop(root: Path) -> str:
    """打 Patterns.GlobHasHit：`applies_to` 带 `**` 通配 + 目录环（走 EnumerateFileSystemEntries 全递归）。"""
    note = build_junction_loop(root)
    write(root, "patterns/loop/PATTERN.md", "\n".join([
        "---", "id: loop", "name: 目录环用例", "status: active", "scope:", "  - 代码层",
        "applies_to:", "  - docs/**/*", "rules:", "  - 规则一", "evidence:", "  - check34",
        "---", "", "## 正文", "",
    ]))
    return note + "；另加一条 applies_to 带 ** 通配的实践包（走 GlobHasHit）"


def build_many_files(root: Path, count: int = 20000) -> str:
    skeleton(root)
    target = root / "docs" / "many"
    target.mkdir(parents=True, exist_ok=True)
    for i in range(count):
        (target / ("f%05d.md" % i)).write_text("# %d\n" % i, encoding="utf-8")
    write(root, "protocol/assertions.json", json.dumps({
        "schema": "nf-assertions/1",
        "severity_vocabulary": ["fail", "warn"],
        "kind_vocabulary": ["regex_absent", "regex_present", "count_at_least", "json_value"],
        "assertions": [{"id": "many-glob", "severity": "fail", "kind": "regex_absent",
                        "params": {"globs": ["docs/many/**/*"], "pattern": "绝不出现的串"},
                        "message": "海量文件", "fix": "—"}],
    }, ensure_ascii=False, indent=2))
    return "docs/many/ 下 %d 个文件 + 断言表对整面做正则扫描" % count


def build_huge_line(root: Path, megabytes: int = 12) -> str:
    skeleton(root)
    target = root / "docs" / "huge.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write("# 巨行\n")
        fh.write("甲" * (megabytes * 1024 * 1024 // 3))
    write(root, "protocol/assertions.json", json.dumps({
        "schema": "nf-assertions/1",
        "severity_vocabulary": ["fail", "warn"],
        "kind_vocabulary": ["regex_absent", "regex_present", "count_at_least", "json_value"],
        "assertions": [{"id": "huge-glob", "severity": "fail", "kind": "regex_absent",
                        "params": {"globs": ["docs/**/*"], "pattern": "绝不出现的串"},
                        "message": "巨行", "fix": "—"}],
    }, ensure_ascii=False, indent=2))
    return "docs/huge.md 单行 ~%d MB + 断言表对该面做正则扫描" % megabytes


def build_weird_names(root: Path) -> str:
    skeleton(root)
    write(root, "docs/空格 与 全角（括号）.md", "# 怪名\n")
    write(root, "docs/emoji-😀.md", "# emoji\n")
    write(root, "docs/" + "长" * 120 + ".md", "# 长名\n")
    write(root, "docs/换行前导.md", "# 前导\n")
    (root / "docs" / "zero.md").write_bytes(b"")
    (root / "docs" / "bom.md").write_bytes(b"\xef\xbb\xbf# BOM\n")
    (root / "docs" / "bad-utf8.md").write_bytes(b"# \xff\xfe bad\n")
    return "怪名/空件/BOM/非法 UTF-8 各一件"


CASES = [
    ("deep-json-200", build_deep_json, (200,),
     ["conformance", "cognition", "verify", "model"], ["cognition", "modeling"]),
    ("deep-json-63", build_deep_json, (63,),
     ["conformance", "cognition", "verify"], ["cognition"]),
    ("deep-yaml-400", build_deep_yaml, (),
     ["combine plan --packs DeepPack", "combine verify", "conformance"], []),
    ("dir-depth", build_dir_depth, (),
     ["assertions", "verify", "conformance"], ["assertions"]),
    ("junction-loop", build_junction_loop, (),
     ["assertions", "verify", "conformance"], ["assertions"]),
    ("patterns-wildcard-loop", build_patterns_wildcard_loop, (),
     ["conformance", "verify"], ["patterns", "assertions"]),
    ("many-files-20k", build_many_files, (12000,),
     ["assertions", "verify"], ["assertions"]),
    ("huge-line-12mb", build_huge_line, (12,),
     ["assertions", "verify", "sig"], ["assertions"]),
    ("weird-names", build_weird_names, (),
     ["assertions", "verify", "conformance"], ["assertions", "public-surface", "library-verify"]),
]


def classify(exit_code: int, stdout: bytes, stderr: bytes, timed_out: bool) -> str:
    if timed_out:
        return "HANG"
    if exit_code in (0, 1):
        return "VERDICT"
    if exit_code == 2:
        return "CONTROLLED"
    return "SILENT" if not (stdout or stderr) else "CRASH"


PY_HELPER = """import json, sys
sys.path.insert(0, sys.argv[1])
from core import conformance_report as cr
fn = dict((i, f) for i, f, _ in cr.CONTRACTS)[sys.argv[2]]
try:
    ok, detail = fn(sys.argv[3])
except Exception as exc:
    ok, detail = False, "契约执行异常：%s" % exc
print(json.dumps({"ok": bool(ok), "detail": detail}, ensure_ascii=False, sort_keys=True))
"""


def run_with_timeout(argv, timeout, env=None):
    """固定子进程环境（见 main 里的 CHILD_ENV）：量具不许随调用者的本地化设置漂移。"""
    start = time.time()
    try:
        proc = subprocess.run(argv, capture_output=True, timeout=timeout, env=env)
        return proc.returncode, proc.stdout, proc.stderr, False, time.time() - start
    except subprocess.TimeoutExpired as exc:
        return -1, exc.stdout or b"", exc.stderr or b"", True, time.time() - start


def probe_mcp(cli: str, case: Path, timeout: int) -> tuple:
    """MCP 会话鲁棒性：坏消息只许**变成 JSON-RPC 错误**，不许杀循环。

    对应 core/mcp_runtime.py 的两条兜底：解析失败 → -32700 "Parse error" 且 continue；
    单条消息异常 → -32603 "Internal error: …" 且 continue（注释原文：「单条消息异常不杀循环」）。
    """
    deep = "[" * 2000 + "]" * 2000
    payloads = [
        '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}',
        '{这不是 JSON',                                                   # 解析失败
        '{"jsonrpc":"2.0","id":3,"method":"tools/list","params":{"x":%s}}' % deep,  # 超深 → 解析失败
        '{"jsonrpc":"2.0","id":4,"method":"tools/call","params":{"name":"spec_ls","arguments":{}}}',  # 结构缺失 → 内部错误
        '{"jsonrpc":"2.0","id":5,"method":"ping"}',                        # 存活探针
    ]
    proc = subprocess.Popen([cli, "--root", str(case), "serve"],
                            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    broke = None
    try:
        for payload in payloads:
            proc.stdin.write((payload + "\n").encode("utf-8"))
            proc.stdin.flush()
    except (BrokenPipeError, OSError) as exc:
        broke = exc
    finally:
        try:
            proc.stdin.close()
        except OSError:
            pass
    timed_out = False
    try:
        out, err = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()
        out, err = proc.communicate()
        timed_out = True

    lines = [ln for ln in out.decode("utf-8", "replace").splitlines() if ln.strip()]
    parsed = []
    unparsable = 0
    for ln in lines:
        try:
            parsed.append(json.loads(ln))
        except ValueError:
            unparsable += 1
    codes = [m.get("error", {}).get("code") for m in parsed if isinstance(m, dict) and "error" in m]
    survived = any(m.get("id") == 5 and "result" in m for m in parsed if isinstance(m, dict))
    detail = ("响应 %d 条 · 解析失败 %d · 错误码 %s · 末条 ping 有答=%s · 管道早断=%s"
              % (len(lines), unparsable, codes, survived, bool(broke)))
    if timed_out:
        kind = "HANG"
    elif proc.returncode not in (0, 1, 2):
        kind = "CRASH"
    elif not survived:
        kind = "DIED"            # 循环被杀：进程可能仍优雅退出，但会话已不可用
    elif unparsable:
        kind = "BADLINE"         # stdout 混入非 JSON
    else:
        kind = "SURVIVED"
    return kind, proc.returncode, detail, err[-300:]


def probe_mcp_stress(cli: str, case: Path, timeout: int) -> tuple:
    """MCP 会话压力面：**巨行**（单条 4 MB 消息）· **海量请求**（2,000 次 ping）· **并发会话**（2 个 server 同时跑）。"""
    findings = []

    # ① 巨行：单条 4 MB 的非法 JSON —— 只许变成 Parse error，且会话必须活着
    huge = '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{"x":"' + "A" * (4 * 1024 * 1024) + '"}}'
    payloads = [huge, '{"jsonrpc":"2.0","id":2,"method":"ping"}']
    proc = subprocess.Popen([cli, "--root", str(case), "serve"],
                            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    broke = False
    timed_out = False
    try:
        # 必须用 communicate（并发读写）：先灌满 stdin 再读 stdout 会**管道死锁**
        # （子进程写响应写满管道缓冲 → 不再读 stdin → 灌入侧阻塞）。本探针曾把自己卡死。
        out, _err = proc.communicate(input=("\n".join(payloads) + "\n").encode("utf-8"), timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()
        out, _err = proc.communicate()
        timed_out = True
    except OSError:
        broke = True
        out, _err = b"", b""
    lines = [l for l in out.decode("utf-8", "replace").splitlines() if l.strip()]
    survived = any('"id": 2' in l or '"id":2' in l for l in lines)
    kind = "HANG" if timed_out else ("CRASH" if proc.returncode not in (0, 1, 2) else "OK")
    findings.append(("mcp-huge-line-4mb", kind,
                     f"4 MB 单行后再 ping：响应 {len(lines)} 条 · ping 有答={survived} · 管道早断={broke}"))
    if kind != "OK" or not survived:
        findings.append(("mcp-huge-line-4mb", "FAIL", "巨行把会话搞坏了"))

    # ② 海量请求：2,000 次 ping 必须逐条应答，且不崩
    many = "\n".join('{"jsonrpc":"2.0","id":%d,"method":"ping"}' % i for i in range(1, 2001)) + "\n"
    start = time.time()
    proc = subprocess.Popen([cli, "--root", str(case), "serve"],
                            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    timed_out = False
    try:
        out, _err = proc.communicate(input=many.encode("utf-8"), timeout=timeout)   # 同上：并发读写
    except subprocess.TimeoutExpired:
        proc.kill()
        out, _err = proc.communicate()
        timed_out = True
    elapsed = time.time() - start
    answered = len([l for l in out.decode("utf-8", "replace").splitlines() if l.strip()])
    kind = "HANG" if timed_out else ("CRASH" if proc.returncode not in (0, 1, 2) else ("OK" if answered == 2000 else "FAIL"))
    findings.append(("mcp-2000-pings", kind, f"应答 {answered}/2000 · {elapsed:.2f}s · exit={proc.returncode}"))

    # ③ 并发会话：两个 server 同时跑（只读，无共享写），都必须答上
    procs, outs = [], []
    for _ in range(2):
        p = subprocess.Popen([cli, "--root", str(case), "serve"],
                             stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        procs.append(p)
    ok_both = True
    for p in procs:
        timed_out = False
        try:
            out, _err = p.communicate(input=b'{"jsonrpc":"2.0","id":1,"method":"ping"}\n', timeout=timeout)
        except subprocess.TimeoutExpired:
            p.kill()
            out, _err = p.communicate()
            timed_out = True
        answered = b'"result"' in out
        ok = (not timed_out) and p.returncode in (0, 1, 2) and answered
        outs.append(f"exit={p.returncode} 有答={answered} 超时={timed_out}")
        ok_both = ok_both and ok
    findings.append(("mcp-concurrent-sessions", "OK" if ok_both else "FAIL", "；".join(outs)))
    return findings


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cli", required=True)
    ap.add_argument("--parity", default="", help="nfparity 可执行体（给了才做两侧差分）")
    ap.add_argument("--py-src", default="", help="快照的 desktop/src（给了才做两侧差分）")
    ap.add_argument("--py-exe", default=sys.executable)
    ap.add_argument("--work", default="")
    ap.add_argument("--timeout", type=int, default=90)
    ap.add_argument("--keep", action="store_true")
    ap.add_argument("--strict", action="store_true",
                    help="文案分歧一律算失败（默认把「两侧都报异常、措辞随运行时」的差异单列为平台文案）")
    args = ap.parse_args()

    # 子进程环境必须**显式钉死**：Python 侧若按宿主 locale（本机 = GBK）输出，
    # 探针的 utf-8 严格解码会把自己崩掉——那是量具缺陷，不是被测对象的问题。
    child_env = dict(os.environ)
    child_env["PYTHONIOENCODING"] = "utf-8"
    if args.py_src:
        child_env["PYTHONPATH"] = args.py_src

    work = Path(args.work) if args.work else Path(
        os.environ.get("TEMP", "/tmp")) / ("nf-hostile-" + str(os.getpid()))
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)
    print("语料根：%s\n引擎：%s\n超时：%ds\n" % (work, args.cli, args.timeout))

    bad: list[tuple] = []
    rows: list[tuple] = []
    diff_rows: list[tuple] = []
    diff_issues: list[tuple] = []
    platform_text: list[tuple] = []
    readable: list[tuple] = []
    helper = work / "_py_contract.py"
    helper.write_text(PY_HELPER, encoding="utf-8", newline="\n")
    do_diff = bool(args.parity and args.py_src)
    if not do_diff:
        print("[注意] 未给 --parity/--py-src：本轮只做「崩/挂」扫描，不做两侧差分\n")

    for name, builder, extra, commands, contracts in CASES:
        case = work / name
        note = builder(case, *extra)
        for command in commands:
            argv = [args.cli, "--root", str(case)] + command.split()
            code, out, err, timed_out, elapsed = run_with_timeout(argv, args.timeout, env=child_env)
            kind = classify(code, out, err, timed_out)
            rows.append((name, command, kind, code, elapsed))
            print("%-8s %-16s %-12s exit=%-4d %5.2fs  %s"
                  % (kind, name, command, code, elapsed,
                     (err.decode("utf-8", "replace").strip().splitlines() or [""])[-1][:70]))
            if kind in ("CRASH", "HANG", "SILENT"):
                bad.append((name, command, kind, code, err[-400:]))
        for cid in contracts:
            if not do_diff:
                break
            py_code, py_out, py_err, py_hang, py_sec = run_with_timeout(
                [args.py_exe, str(helper), args.py_src, cid, str(case)], args.timeout, env=child_env)
            net_code, net_out, net_err, net_hang, net_sec = run_with_timeout(
                [args.parity, "--conformance-one", cid, str(case)], args.timeout, env=child_env)
            tag = "SAME"
            if py_hang or net_hang:
                tag = ("PY-HANG" if py_hang else "") + ("NET-HANG" if net_hang else "")
                diff_issues.append((name, cid, tag, "两侧之一未在 %ds 内返回" % args.timeout, ""))
            else:
                py = json.loads(py_out.decode("utf-8"))
                net = json.loads(net_out.decode("utf-8"))
                if py["ok"] != net["ok"]:
                    tag = "DIFF"
                    diff_issues.append((name, cid, "裁决分歧",
                                        "py=(%s, %s)" % (py["ok"], py["detail"]),
                                        "net=(%s, %s)" % (net["ok"], net["detail"])))
                elif py["detail"] != net["detail"]:
                    # 两侧都在报「异常」→ 措辞来自各自运行时（Python 异常 vs .NET 异常），不可约；
                    # 引擎给可读判定、Python 抛异常 → 有意为之（工业级可读性），单列不判死；
                    # **引擎抛异常、Python 给判定** → 必须修（在下面按真差异记）
                    both_exception = "异常" in py["detail"] and "异常" in net["detail"]
                    engine_readable = "异常" in py["detail"] and "异常" not in net["detail"]
                    tag = "PLAT" if both_exception else ("READ" if engine_readable else "TEXT")
                    if args.strict or tag == "TEXT":
                        diff_issues.append((name, cid, "文案分歧", py["detail"], net["detail"]))
                    elif tag == "READ":
                        readable.append((name, cid, py["detail"], net["detail"]))
                    else:
                        platform_text.append((name, cid, py["detail"], net["detail"]))
            diff_rows.append((name, cid, tag, py_sec, net_sec))
            print("%-8s %-16s %-12s py=%.2fs net=%.2fs" % (tag, name, cid, py_sec, net_sec))
        print("         └ %s\n" % note)

    total = len(rows)
    print("敌意输入：%d 格 · 裁决 %d · 受控失败 %d · 异常 %d"
          % (total, sum(1 for r in rows if r[2] == "VERDICT"),
             sum(1 for r in rows if r[2] == "CONTROLLED"), len(bad)))
    for name, command, kind, code, err in bad:
        print("  [%s] %s / %s（exit=%d）\n      %s"
              % (kind, name, command, code, err.decode("utf-8", "replace")[:300]))

    if diff_rows:
        print("\n两侧差分（敌意语料上同为已移植契约）：%d 格 · 一致 %d · 平台文案 %d · 引擎更可读 %d · 有问题 %d"
              % (len(diff_rows), sum(1 for r in diff_rows if r[2] == "SAME"),
                 len(platform_text), len(readable), len(diff_issues)))
        for name, cid, kind, py_detail, net_detail in diff_issues:
            print("  [%s] %s / %s\n      py : %s\n      net: %s" % (kind, name, cid, py_detail, net_detail))
        for name, cid, py_detail, net_detail in platform_text:
            print("  [平台文案] %s / %s（裁决一致，异常措辞随运行时）" % (name, cid))
        for name, cid, py_detail, net_detail in readable:
            print("  [引擎更可读] %s / %s（裁决一致：Python 抛异常，引擎给可读判定）\n      py : %s\n      net: %s"
                  % (name, cid, py_detail, net_detail))

    # MCP 会话：坏消息不许杀循环（对应 core/mcp_runtime.py 的两条兜底）
    mcp_case = work / "deep-json-63"
    mcp_kind, mcp_code, mcp_detail, mcp_err = probe_mcp(args.cli, mcp_case, args.timeout)
    print("\nMCP 会话鲁棒性：%s · exit=%d\n  %s" % (mcp_kind, mcp_code, mcp_detail))
    if mcp_err.strip():
        print("  stderr: %s" % mcp_err.decode("utf-8", "replace").strip()[:200])
    if mcp_kind != "SURVIVED":
        bad.append(("mcp-serve", "serve", mcp_kind, mcp_code, mcp_detail.encode("utf-8")))

    # MCP 压力面（巨行 / 海量请求 / 并发会话）
    print("\nMCP 压力面：")
    for name, kind, detail in probe_mcp_stress(args.cli, mcp_case, args.timeout):
        print(f"  {kind:6} {name:28} {detail}")
        if kind != "OK":
            bad.append((name, "serve", kind, -1, detail.encode("utf-8")))

    if not args.keep:
        shutil.rmtree(work, ignore_errors=True)
    return 1 if (bad or diff_issues) else 0


if __name__ == "__main__":
    raise SystemExit(main())
