#!/usr/bin/env python3
"""conformance 负例探针：每条已移植契约都构造**变异树**，让 Python 真源与 .NET 引擎同参数求值 → 逐字段比对。

为什么需要它：正向对账只能证明「在干净语料上两边一致」，证明不了「该红的能红」。
本探针为每条契约准备「干净 / 破坏」两组语料，逐条比对 (ok, detail, digest)：
差异即失败；另外校验「破坏」用例确实触发了预期的 FAIL（防止探针本身写歪了）。

用法：
    python probes/conformance_negative_probe.py --py-src <repo>/desktop/src \
        --cli <engine>/tools/nfparity/bin/Release/net8.0/nfparity.exe [--keep]

纪律：全程用**文件 + 子进程**通道；不经过 PowerShell 对象往返（会造假不一致）。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path
import _paths  # 默认路径唯一出处（探针可移植）


def contract_digest(cid: str, ok: bool, detail: str) -> str:
    payload = json.dumps({"id": cid, "ok": bool(ok), "detail": detail},
                         sort_keys=True, ensure_ascii=False,
                         separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def write_tree(base: Path, files: dict) -> None:
    for rel, content in files.items():
        path = base / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8", newline="\n")


# --------------------------------------------------------------------- 语料构造

def pattern_md(pid: str, name: str = "示例实践包", status: str = "active",
               scope=("代码层",), applies_to=("src",), rules=("规则一",),
               evidence=("check34",), omit=()) -> str:
    lines = ["---"]
    if "id" not in omit:
        lines.append("id: %s" % pid)
    if "name" not in omit:
        lines.append("name: %s" % name)
    if "status" not in omit:
        lines.append("status: %s" % status)
    if "scope" not in omit:
        lines += ["scope:"] + ["  - %s" % s for s in scope]
    if "applies_to" not in omit:
        lines += ["applies_to:"] + ["  - %s" % s for s in applies_to]
    if "rules" not in omit:
        lines += ["rules:"] + ["  - %s" % r for r in rules]
    if "evidence" not in omit and evidence is not None:
        lines += ["evidence:"] + ["  - %s" % e for e in evidence]
    return "\n".join(lines) + "\n---\n\n## 正文\n"


def rfc_doc(rfc: str, cat: str = "Standards Track", date: str = "2026-01-02",
            status: str = "Active", supersedes: str = "—", superseded_by: str = "—",
            last_updated: str = "2026-01-02", omit_head: bool = False) -> str:
    lines = ["# 示例协议件"]
    if not omit_head:
        lines.append("> 最后更新：%s" % last_updated)
        lines.append("> **RFC**: %s · **Category**: %s · **Date**: %s · **Status**: %s · "
                     "**Supersedes**: %s · **Superseded by**: %s"
                     % (rfc, cat, date, status, supersedes, superseded_by))
    return "\n".join(lines) + "\n\n正文。\n"


def rfc_index(docs, status_vocabulary=("Active", "Superseded", "Deprecated", "Experimental")) -> str:
    return json.dumps({"schema": "nf-rfc/1",
                       "status_vocabulary": list(status_vocabulary),
                       "docs": [{"rfc": r, "path": p, "category": c} for r, p, c in docs]},
                      ensure_ascii=False, indent=2) + "\n"


VALID_PATTERN_DIR = "src"


def patterns_valid_tree() -> dict:
    return {
        "src/示例.py": "# 占位\n",
        "patterns/alpha/PATTERN.md": pattern_md("alpha", applies_to=("src",)),
    }


CASES = [
    # ---------------------------------------------------------------- patterns
    dict(id="patterns", name="patterns-valid", files=patterns_valid_tree(),
         post="patterns_index", expect_ok=True,
         why="干净实践包：必填齐 + applies_to 可证 + 投影一致"),
    dict(id="patterns", name="patterns-two-valid", files={
        "src/示例.py": "# 占位\n",
        "lib/其他.md": "# 占位\n",
        "patterns/alpha/PATTERN.md": pattern_md("alpha", applies_to=("src",), scope=("代码层", "协议层")),
        "patterns/beta/PATTERN.md": pattern_md("beta", name="乙", applies_to=("lib", "src"),
                                               rules=("a", "b", "c"), evidence=("check1", "docs/指南.md")),
        "docs/指南.md": "# 指南\n",
    }, post="patterns_index", expect_ok=True,
        why="两条实践包 + 多值 scope/rules/evidence（含多元素渲染）"),
    dict(id="patterns", name="patterns-id-mismatch", files={
        "patterns/alpha/PATTERN.md": pattern_md("beta"),
    }, expect_ok=False, why="id 与目录名不一致 → FAIL"),
    dict(id="patterns", name="patterns-missing-rules", files={
        "patterns/alpha/PATTERN.md": pattern_md("alpha", omit=("rules",)),
    }, expect_ok=False, why="缺必填字段 rules → FAIL"),
    dict(id="patterns", name="patterns-empty-rules", files={
        "patterns/alpha/PATTERN.md": pattern_md("alpha", rules=()),
    }, expect_ok=False, why="rules 为空 → FAIL"),
    dict(id="patterns", name="patterns-applies-missing", files={
        "patterns/alpha/PATTERN.md": pattern_md("alpha", applies_to=("nope/缺失.py",)),
    }, expect_ok=False, why="applies_to 指向不存在的件 → FAIL"),
    dict(id="patterns", name="patterns-wildcard-hit", files={
        "src/deep/模块.py": "# 占位\n",
        "patterns/alpha/PATTERN.md": pattern_md("alpha", applies_to=("src/**/*.py",)),
    }, post="patterns_index", expect_ok=True, why="applies_to 通配命中真实件 → PASS（走 glob 分支）"),
    dict(id="patterns", name="patterns-wildcard-miss", files={
        "patterns/alpha/PATTERN.md": pattern_md("alpha", applies_to=("nope/**/*.txt",)),
    }, expect_ok=False, why="applies_to 通配无匹配 → FAIL（走 glob 分支）"),
    dict(id="patterns", name="patterns-status-out", files={
        "patterns/alpha/PATTERN.md": pattern_md("alpha", status="archived"),
    }, expect_ok=False, why="status 越词表 → FAIL"),
    dict(id="patterns", name="patterns-dup-id", files={
        "patterns/alpha/PATTERN.md": pattern_md("alpha"),
        "patterns/beta/PATTERN.md": pattern_md("beta") + "",
        "patterns/gamma/PATTERN.md": pattern_md("beta"),
    }, expect_ok=False, why="两个包同 id → FAIL"),
    dict(id="patterns", name="patterns-projection-drift", files={
        "patterns/alpha/PATTERN.md": pattern_md("alpha"),
        "patterns/INDEX.md": "<!-- BEGIN GENERATED: patterns-index -->\n改过的表\n<!-- END GENERATED: patterns-index -->\n",
    }, expect_ok=False, why="INDEX 投影被手改 → FAIL（真源纪律）"),
    dict(id="patterns", name="patterns-none", files={"patterns/README.md": "# 空\n"},
         expect_ok=False, why="无实践包 → FAIL（不为齐全而造）"),
    dict(id="patterns", name="patterns-evidence-warn-only", files={
        "src/占位.py": "# 占位（让 applies_to 可证）\n",
        "patterns/alpha/PATTERN.md": pattern_md("alpha", evidence=("docs/不存在.md",)),
        "patterns/INDEX.md": "",
    }, post="patterns_index", expect_ok=True, why="evidence 指向缺失件只记 WARN，不判 FAIL"),
    dict(id="patterns", name="patterns-no-frontmatter", files={
        "patterns/alpha/PATTERN.md": "## 没有 frontmatter\n",
    }, expect_ok=False, why="缺 frontmatter → FAIL"),

    # ---------------------------------------------------------------- rfc-heads
    dict(id="rfc-heads", name="rfc-valid-chain", files={
        "protocol/rfc_index.json": rfc_index([("NF-0001", "a.md", "Standards Track"),
                                              ("NF-0002", "b.md", "Informational")]),
        "a.md": rfc_doc("NF-0001", status="Superseded", superseded_by="NF-0002"),
        "b.md": rfc_doc("NF-0002", cat="Informational", supersedes="NF-0001"),
    }, expect_ok=True, why="两条协议件 + 一条 supersede 链 → PASS"),
    dict(id="rfc-heads", name="rfc-head-missing", files={
        "protocol/rfc_index.json": rfc_index([("NF-0001", "a.md", "Standards Track")]),
        "a.md": rfc_doc("NF-0001", omit_head=True),
    }, expect_ok=False, why="缺 RFC 头 → FAIL"),
    dict(id="rfc-heads", name="rfc-date-mismatch", files={
        "protocol/rfc_index.json": rfc_index([("NF-0001", "a.md", "Standards Track")]),
        "a.md": rfc_doc("NF-0001", date="2026-01-02", last_updated="2026-03-04"),
    }, expect_ok=False, why="Date 与「最后更新」不一致 → FAIL"),
    dict(id="rfc-heads", name="rfc-status-out", files={
        "protocol/rfc_index.json": rfc_index([("NF-0001", "a.md", "Standards Track")]),
        "a.md": rfc_doc("NF-0001", status="Frozen"),
    }, expect_ok=False, why="Status 越词表 → FAIL"),
    dict(id="rfc-heads", name="rfc-category-out", files={
        "protocol/rfc_index.json": rfc_index([("NF-0001", "a.md", "Marketing")]),
        "a.md": rfc_doc("NF-0001", cat="Marketing"),
    }, expect_ok=False, why="Category 越词表 → FAIL"),
    dict(id="rfc-heads", name="rfc-category-index-mismatch", files={
        "protocol/rfc_index.json": rfc_index([("NF-0001", "a.md", "Informational")]),
        "a.md": rfc_doc("NF-0001", cat="Standards Track"),
    }, expect_ok=False, why="索引 Category 与头部不一致 → FAIL"),
    dict(id="rfc-heads", name="rfc-dangling-supersede", files={
        "protocol/rfc_index.json": rfc_index([("NF-0001", "a.md", "Standards Track")]),
        "a.md": rfc_doc("NF-0001", status="Superseded", superseded_by="NF-9999"),
    }, expect_ok=False, why="Superseded by 指向不在册编号 → FAIL"),
    dict(id="rfc-heads", name="rfc-superseded-without-target", files={
        "protocol/rfc_index.json": rfc_index([("NF-0001", "a.md", "Standards Track")]),
        "a.md": rfc_doc("NF-0001", status="Superseded"),
    }, expect_ok=False, why="Status=Superseded 但缺 Superseded by → FAIL"),
    dict(id="rfc-heads", name="rfc-cycle", files={
        "protocol/rfc_index.json": rfc_index([("NF-0001", "a.md", "Standards Track"),
                                              ("NF-0002", "b.md", "Standards Track")]),
        "a.md": rfc_doc("NF-0001", status="Superseded", superseded_by="NF-0002"),
        "b.md": rfc_doc("NF-0002", status="Superseded", superseded_by="NF-0001"),
    }, expect_ok=False, why="supersede 链成环 → FAIL"),
    dict(id="rfc-heads", name="rfc-index-missing-doc", files={
        "protocol/rfc_index.json": rfc_index([("NF-0001", "ghost.md", "Standards Track")]),
    }, expect_ok=False, why="索引指向不存在的文档 → FAIL"),
    dict(id="rfc-heads", name="rfc-dup-number", files={
        "protocol/rfc_index.json": rfc_index([("NF-0001", "a.md", "Standards Track"),
                                              ("NF-0001", "b.md", "Standards Track")]),
        "a.md": rfc_doc("NF-0001"),
        "b.md": rfc_doc("NF-0001"),
    }, expect_ok=False, why="RFC 编号在册重复 → FAIL"),
    dict(id="rfc-heads", name="rfc-head-number-mismatch", files={
        "protocol/rfc_index.json": rfc_index([("NF-0001", "a.md", "Standards Track")]),
        "a.md": rfc_doc("NF-0002"),
    }, expect_ok=False, why="头部编号与索引不一致 → FAIL"),
    dict(id="rfc-heads", name="rfc-index-absent", files={"a.md": rfc_doc("NF-0001")},
         expect_ok=False, why="缺 RFC 索引 → FAIL"),

    # ------------------------------------------------------------ public-surface
    dict(id="public-surface", name="ps-clean", files={
        "desktop/tests/fixtures/external/chara.json": '{"name": "示例"}\n',
        "docs/external-validation-assets/README.md": "# 对外素材\n",
    }, expect_ok=True, why="对外产物零泄漏 → PASS"),
    dict(id="public-surface", name="ps-absent-dirs", files={"README.md": "# 无关\n"},
         expect_ok=True, why="对外面不存在 → 无泄漏可报 → PASS"),
    dict(id="public-surface", name="ps-win-abs", files={
        "desktop/tests/fixtures/external/leak.md": "见 C:\\Users\\某人\\Documents\\私有件.md\n",
    }, expect_ok=False, why="Windows 绝对路径泄漏 → FAIL"),
    dict(id="public-surface", name="ps-posix-home", files={
        "desktop/tests/fixtures/external/deep/leak.json": '{"p": "/home/bob/x"}\n',
    }, expect_ok=False, why="类 Unix home 绝对路径（递归层）→ FAIL"),
    dict(id="public-surface", name="ps-unc", files={
        "docs/external-validation-assets/leak.txt": "路径 \\\\Users\\\\mon\\\\x\n",
    }, expect_ok=False, why="UNC/Users 形态（单层 glob）→ FAIL"),
    dict(id="public-surface", name="ps-extension-filtered", files={
        "desktop/tests/fixtures/external/script.py": "P = 'C:\\\\Users\\\\x'\n",
        "desktop/tests/fixtures/external/readme.md": "干净\n",
    }, expect_ok=True, why="非白名单扩展名不参与判据 → PASS（不越判）"),
    dict(id="public-surface", name="ps-two-leaks-order", files={
        "desktop/tests/fixtures/external/a-first.md": "C:\\Users\\一\n",
        "desktop/tests/fixtures/external/z-last.md": "C:\\Users\\二\n",
    }, expect_ok=False, why="两处泄漏 → detail 取前两条且顺序稳定"),
]


DEFAULT_PY_SRC = _paths.snap_src()
DEFAULT_CLI = _paths.engine("tools", "nfparity", "bin", "Release", "net8.0", "nfparity.exe")
def python_side(py_src: str, cid: str, root: str):
    if py_src not in sys.path:
        sys.path.insert(0, py_src)
    from core import conformance_report as cr
    fn = dict((i, f) for i, f, _ in cr.CONTRACTS).get(cid)
    if fn is None:
        raise SystemExit("Python 侧无此契约：%s" % cid)
    try:
        ok, detail = fn(root)
    except Exception as exc:                      # 同 run() 的兜底口径
        ok, detail = False, "契约执行异常：%s" % exc
    return bool(ok), detail


def net_side(cli: str, cid: str, root: str):
    proc = subprocess.run([cli, "--conformance-one", cid, root],
                          capture_output=True)
    if proc.returncode != 0:
        raise SystemExit("nfparity 退出码 %d：%s" % (proc.returncode, proc.stderr.decode("utf-8", "replace")))
    row = json.loads(proc.stdout.decode("utf-8"))
    return row


def canonical_vectors() -> list:
    return [
        {"b": 2, "a": 1},
        {"a": 1, "b": 2},
        {"名": "值", "a": 1},
        {"z": [1, 2, {"y": True}], "a": {"b": [], "c": {}}},
        {"s": "行\n\t制表\"引号\\反斜杠"},
        {"emoji": "😀", "accent": "é", "cjk": "中文字"},
        {"i": 1234567890123, "j": -7, "k": 0},
        {"l": ["a", "b", "c"], "empty": []},
        {"n": None, "t": True, "f": False},
        {"nested": {"b": {"c": [{"d": "e"}]}}},
        # 浮点写法（Python json.dumps 形态：必须带小数点或指数；≥1e16 切科学计数法）
        {"f": 1.0, "g": 1e16, "h": 1e-5, "i": 1e-4, "j": 123456789012345.0,
         "k": 1.5e16, "l": 1e100, "m": -1e16},
    ]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--py-src", default=DEFAULT_PY_SRC)
    ap.add_argument("--cli", default=DEFAULT_CLI)
    ap.add_argument("--keep", action="store_true", help="保留临时语料树（默认保留，便于复看）")
    args = ap.parse_args()

    sys.path.insert(0, args.py_src)
    from core import attest
    from core import patterns as pt

    base = Path(tempfile.mkdtemp(prefix="nf_conf_probe_"))
    print("语料根：%s" % base)
    print("Python 真源：%s" % args.py_src)
    print("引擎 CLI：%s\n" % args.cli)

    failures = []
    rows = []
    for case in CASES:
        tree = base / case["name"]
        write_tree(tree, case["files"])
        if case.get("post") == "patterns_index":
            (tree / "patterns" / "INDEX.md").write_text(pt.render_index(str(tree)),
                                                        encoding="utf-8", newline="\n")
        py_ok, py_detail = python_side(args.py_src, case["id"], str(tree))
        net = net_side(args.cli, case["id"], str(tree))
        expect_ok = case.get("expect_ok")
        expect_hit = expect_ok is None or py_ok == expect_ok
        same = (py_ok == net["ok"] and py_detail == net["detail"]
                and contract_digest(case["id"], py_ok, py_detail) == net["digest"])
        rows.append((case, py_ok, py_detail, net, same, expect_hit))
        if not same:
            failures.append((case, "两侧不一致", py_ok, py_detail, net))
        if not expect_hit:
            failures.append((case, "用例未触发预期判定（Python 侧 ok=%s，期望 %s）" % (py_ok, expect_ok),
                             py_ok, py_detail, net))

    for case, py_ok, py_detail, net, same, _hit in rows:
        print("%-6s %-32s %-28s py=%-5s net=%-5s %s"
              % ("OK" if same else "DIFF", case["name"], case["id"], py_ok, net["ok"],
                 py_detail[:52]))

    # 规范化摘要（attest.canonical 口径）跨实现逐字节校验
    canon_bad = 0
    for i, doc in enumerate(canonical_vectors()):
        path = base / ("canonical_%02d.json" % i)
        path.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
        expect = attest.canonical(json.loads(path.read_text(encoding="utf-8"))).decode("utf-8")
        proc = subprocess.run([args.cli, "--canonical-compact", str(path)], capture_output=True)
        got = proc.stdout.decode("utf-8").rstrip("\r\n")
        if expect != got:
            canon_bad += 1
            print("DIFF   canonical-%02d 期望 %r 实得 %r" % (i, expect, got))
    print("\n规范化摘要向量：%d 条，%s" % (len(canonical_vectors()),
                                          "全部逐字节一致" if canon_bad == 0 else "%d 条不一致" % canon_bad))

    total = len(rows)
    print("\n负例探针：%d 例，%d 例两侧一致，%d 处问题" % (total, total - len(failures), len(failures)))
    for case, kind, py_ok, py_detail, net in failures:
        print("  [%s] %s：py=(%s, %r) net=(%s, %r)"
              % (kind, case["name"], py_ok, py_detail, net["ok"], net["detail"]))
    return 0 if (not failures and canon_bad == 0) else 1


if __name__ == "__main__":
    raise SystemExit(main())
