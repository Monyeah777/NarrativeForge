#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SAST 基线闸门（安全/供应链面 · ISO 25010 安全性）：bandit + ruff-S 的**只增不减**计数棘轮。

为什么这样设计：
- 纯「命中即红」在本仓不可行——首轮实测 bandit 10 条（全 LOW/MED）、ruff `--select S` 58 条，
  其中绝大多数是**已逐条裁定**的误报或已登记放行项（如 `S310` 的 scheme 前置校验、`S603/S607`
  的 argv 列表调用、`S110/S112` 与 AUD-0016 静默跳过清单一一对应的 30 处）。
- 但「全放行」也不行——新增的 SQL 拼接/弱随机/命令注入必须拦。
- 故按 **(工具, 文件, 规则) 计数**做棘轮：**计数上升或出现新 (文件,规则) → FAIL**；
  计数下降 → WARN（提示重冻，债务表不得虚挂）。用计数而非行号，是为了让**行号漂移不误报**、
  而语义新增必报。

用法：
  python scripts/sast_check.py            # 只读校验（新增即 exit 1）
  python scripts/sast_check.py --write    # 评审后把当前计数冻结为基线
  python scripts/sast_check.py --json     # 打印当前计数
"""
import argparse
import collections
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASELINE_REL = "protocol/sast_baseline.json"
SCHEMA = "nf-sast/1"
SCAN_TARGETS = ("desktop/src", "scripts", ".github/scripts")
#: 计数**按平台分段**：同一棵树在 Linux 与 Windows 上的命中面并不相同（实测 2026-09-29：Linux
#: bandit 33 / ruff-S 75，Windows 32 / 74，差别在 `S603/S607` 一类子进程规则）。棘轮语义不变——
#: 每个平台各自只许下降；缺本平台段即 FAIL（修复指引：在该平台跑 `--write` 落段）。
PLATFORM = "nt" if os.name == "nt" else "posix"
NOTE = ("SAST 计数棘轮（(工具,文件,规则) 计数只许下降；新增/上升判 FAIL，下降提示重冻）。"
        "按平台分段：platforms[nt] / platforms[posix] 各自冻结、各自只许下降，缺段即失败。")


def _run(argv) -> tuple:
    p = subprocess.run(argv, cwd=str(ROOT), capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    return p.returncode, p.stdout or "", p.stderr or ""


def _counts(rows: list, field: str) -> dict:
    """命中行 → {(仓库相对文件, 规则): 计数}（bandit / ruff 共同的落键口径）。"""
    cnt: collections.Counter = collections.Counter()
    for r in rows:
        rel = os.path.relpath(str(r.get("filename")), str(ROOT)).replace("\\", "/")
        cnt[(rel, str(r.get(field)))] += 1
    return dict(cnt)


def bandit_counts() -> tuple:
    """→ (counts, meta)：{(文件, 规则): n}；工具缺失 → ({}, {"error": ...})。"""
    code, out, err = _run([sys.executable, "-m", "bandit", "-r", *SCAN_TARGETS,
                           "-f", "json", "-q"])
    if "No module named" in err or code == 127:
        return {}, {"error": "bandit 不在（修复指引：pip install -r .github/requirements-sast.txt）"}
    try:
        rows = json.loads(out[out.index("{"):]).get("results", []) if "{" in out else []
    except ValueError as exc:
        return {}, {"error": "bandit 输出不可解析：%s" % exc}
    return _counts(rows, "test_id"), {
        "total": len(rows),
        "severities": collections.Counter(r.get("issue_severity") for r in rows).most_common()}


def ruff_counts() -> tuple:
    """→ (counts, meta)：ruff `--select S` 的 {(文件, 规则): n}。"""
    code, out, err = _run([sys.executable, "-m", "ruff", "check", "--select", "S",
                           "--output-format", "json", *SCAN_TARGETS])
    if "No module named" in err or code == 127:
        return {}, {"error": "ruff 不在（修复指引：pip install -r .github/requirements-lint.txt）"}
    try:
        rows = json.loads(out) if out.strip().startswith("[") else []
    except ValueError as exc:
        return {}, {"error": "ruff 输出不可解析：%s" % exc}
    return _counts(rows, "code"), {"total": len(rows)}


def current() -> dict:
    b, bm = bandit_counts()
    r, rm = ruff_counts()
    # 键分隔用 `::`（不用 `|`）——NF 的编码卫生判据只许 ASCII 字母数字 + _-.:/ 与 CJK
    return {"bandit": {("%s::%s" % k): v for k, v in b.items()},
            "ruff": {("%s::%s" % k): v for k, v in r.items()},
            "meta": {"bandit": bm, "ruff": rm}}


def load_baseline() -> dict:
    p = ROOT / BASELINE_REL
    if not p.is_file():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except ValueError:
        return {}


def platform_baseline(doc: dict) -> dict:
    """取**本平台**那一段（`platforms[PLATFORM]`）；没有该段 → `{}`（compare 判 FAIL）。"""
    if not doc:
        return {}
    return (doc.get("platforms") or {}).get(PLATFORM) or {}


def _tool_diff(tool: str, cur: dict, base: dict, issues: list, warns: list) -> None:
    """单工具双向比对：新增/上升 → issues；下降 → warns（(文件,规则) 键形态由 current() 统一产出）。"""
    for key, n in sorted(cur.items()):
        # 规则名只用于展示：键里没有分隔符也不要崩
        rule = key.split("::", 1)[1] if "::" in key else key
        show = key.replace("::", " · ")
        if key not in base:
            issues.append("[%s] 新增命中 %s（%s ×%d）（修复指引：修掉，或评审后 "
                          "python scripts/sast_check.py --write 冻结）" % (tool, show, rule, n))
        elif n > int(base[key]):
            issues.append("[%s] 命中数上升 %s（%d → %d）（修复指引：同上）"
                          % (tool, show, int(base[key]), n))
    for key, n in sorted(base.items()):
        if int(n) > int(cur.get(key, 0)):
            warns.append("[%s] 命中数下降 %s（%d → %d）（修复指引：从 %s 重冻）"
                         % (tool, key.replace("::", " · "), int(n), int(cur.get(key, 0)),
                            BASELINE_REL))


def compare(cur: dict, base: dict) -> tuple:
    """纯函数比对（可单测）：→ (issues, warns, stats)。计数上升/新增 = FAIL；下降 = WARN。"""
    issues: list = []
    warns: list = []
    if not base:
        issues.append("缺本平台 SAST 基线 %s[%s]（修复指引：在该平台跑 "
                      "python scripts/sast_check.py --write 落段）" % (BASELINE_REL, PLATFORM))
        return issues, warns, {"bandit": sum(cur["bandit"].values()),
                               "ruff": sum(cur["ruff"].values()),
                               "baseline_bandit": 0, "baseline_ruff": 0}
    for tool in ("bandit", "ruff"):
        _tool_diff(tool, cur[tool], base.get(tool) or {}, issues, warns)
    stats = {"bandit": sum(cur["bandit"].values()), "ruff": sum(cur["ruff"].values()),
             "baseline_bandit": sum((base.get("bandit") or {}).values()),
             "baseline_ruff": sum((base.get("ruff") or {}).values())}
    return issues, warns, stats


def scan() -> tuple:
    """→ (issues, warns, stats)（读真仓当前计数 + **本平台**基线段，交给 compare）。"""
    return compare(current(), platform_baseline(load_baseline()))


def write() -> tuple:
    cur = current()
    doc = load_baseline()                      # 保留其它平台的段（各平台各自冻结）
    doc["schema"] = SCHEMA
    doc["note"] = NOTE
    section = {"bandit": cur["bandit"], "ruff": cur["ruff"], "meta": cur["meta"]}
    (doc.setdefault("platforms", {}))[PLATFORM] = section
    (ROOT / BASELINE_REL).write_text(
        json.dumps(doc, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8", newline="\n")
    return [], section


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="SAST 基线闸门（bandit + ruff-S 计数棘轮）")
    ap.add_argument("--write", action="store_true", help="冻结当前计数为基线")
    ap.add_argument("--json", action="store_true", help="打印当前计数")
    args = ap.parse_args(argv)

    if args.write:
        issues, section = write()
        print("== 冻结 SAST 基线 ==")
        print("  ✓ 已写入 %s[%s]（bandit %d 条 · ruff %d 条）"
              % (BASELINE_REL, PLATFORM, sum(section["bandit"].values()),
                 sum(section["ruff"].values())))
        for i in issues:
            print("  ✗ %s" % i, file=sys.stderr)
        return 1 if issues else 0

    if args.json:
        print(json.dumps(current(), ensure_ascii=False, indent=2, sort_keys=True))
        return 0

    issues, warns, stats = scan()
    print("== SAST 基线闸门 ==")
    print("  平台 %s · bandit %d（基线 %d）· ruff-S %d（基线 %d）"
          % (PLATFORM, stats["bandit"], stats["baseline_bandit"],
             stats["ruff"], stats["baseline_ruff"]))
    for w in warns:
        print("  [WARN] %s" % w)
    for i in issues[:10]:
        print("  ✗ %s" % i, file=sys.stderr)
    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
