"""社区资产行数基线（**可重签工件**；机制对齐 `module_signature` 的「外形冻结」）。

**内部差距实证**：社区资产的行数基线此前写作 `verify.sh` check8 里的**字面量**
（`[ "$w" -eq 4284 ]`）——任何合法的资产内容改动都会撞它，而唯一出口是**改 verify.sh 的数字**：
既没有"谁改的/何时/为什么"的记录面，也不在回执覆盖面内（改了没人知道）。
本模块把基线搬进 `protocol/asset_line_baseline.json`（机读 · 可重签 · 被回执锚定）：

判据（门禁 `nf asset baseline` / verify check8 同源）：
1. 基线件在场、`schema` 匹配；
2. **在场**的每个 `community/*/assets` 包必须在基线在册（新增包未登记 = FAIL）；
3. 在册包的 `files` / `lines` / `digest`（逐文件行数映射的 SHA-256）须与实时扫描一致——
   不一致 = FAIL 并给**重签指引**（`nf asset baseline --write`）；
4. 目录不在场的包按 **WARN 跳过**（对齐 verify 段 B「缺包只记 WARN」的部署语义）。

纪律：重签是**显式动作**（评审后执行），内容改动与基线改动必须在同一次提交里可见。
"""
from __future__ import annotations

import glob
import hashlib
import json
import os
from datetime import date
from typing import Any, Dict, List, Tuple

SCHEMA = "nf-asset-line-baseline/1"
BASELINE_REL = "protocol/asset_line_baseline.json"
PACKAGE_ASSETS_GLOB = os.path.join("community", "*", "assets")
EXCLUDE_NAMES = ("README.md",)


def _line_count(path: str) -> int:
    with open(path, encoding="utf-8") as fh:
        return len(fh.read().splitlines())


def scan_package(assets_dir: str, rel_dir: str) -> Dict[str, Any]:
    """扫一个资产目录 → {package, dir, files, lines, digest, per_file}。"""
    per_file = []
    for f in sorted(glob.glob(os.path.join(assets_dir, "*.md"))):
        if os.path.basename(f) in EXCLUDE_NAMES:
            continue
        per_file.append([os.path.basename(f), _line_count(f)])
    payload = json.dumps(per_file, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return {
        "package": os.path.basename(os.path.dirname(assets_dir)),
        "dir": rel_dir.replace("\\", "/"),
        "files": len(per_file),
        "lines": sum(n for _f, n in per_file),
        "digest": hashlib.sha256(payload).hexdigest(),
        "per_file": per_file,
    }


def scan(root: str = ".") -> Dict[str, Any]:
    """→ {packages: [...]}（自动发现 community/*/assets，缺目录的包不入面）。"""
    pkgs = []
    for d in sorted(glob.glob(os.path.join(root, PACKAGE_ASSETS_GLOB))):
        rel = os.path.relpath(d, root)
        pkgs.append(scan_package(d, rel))
    return {"packages": pkgs}


def load(root: str = ".") -> Dict[str, Any]:
    p = os.path.join(root, BASELINE_REL)
    if not os.path.isfile(p):
        return {}
    try:
        with open(p, encoding="utf-8") as fh:
            return json.load(fh)
    except ValueError:
        return {}


def verify(root: str = ".") -> Tuple[List[str], List[str], Dict[str, Any]]:
    """→ (issues, warns, stats)。issues = FAIL 级；warns = 缺包跳过（部署语义）。"""
    doc = load(root)
    if not doc:
        return (["缺资产行数基线 %s（修复指引：nf asset baseline --write）" % BASELINE_REL],
                [], {})
    if str(doc.get("schema") or "") != SCHEMA:
        return (["资产行数基线 schema 不匹配（期望 %s）：%r"
                 % (SCHEMA, doc.get("schema"))], [], {})
    base = {str(e.get("dir") or ""): e for e in (doc.get("packages") or [])}
    live = {e["dir"]: e for e in scan(root)["packages"]}
    issues: List[str] = []
    warns: List[str] = []
    # 新增包未登记（在场却不在基线）
    for d, cur in sorted(live.items()):
        if d not in base:
            issues.append("社区包资产未登记基线：%s（%d 文件 / %d 行）——"
                          "新增包须重签基线（nf asset baseline --write）" % (d, cur["files"], cur["lines"]))
    for d, want in sorted(base.items()):
        cur = live.get(d)
        if cur is None:
            warns.append("%s 不在场（跳过资产行数基线核对——对齐段 B 缺包只记 WARN）"
                         % (want.get("package") or d))
            continue
        for key, label in (("files", "文件数"), ("lines", "行数"), ("digest", "外形摘要")):
            if cur.get(key) != want.get(key):
                issues.append("%s 资产%s与基线不一致：实时=%s 基线=%s（修复指引：核对内容后显式重签 "
                              "nf asset baseline --write）"
                              % (want.get("package") or d, label, cur.get(key), want.get(key)))
    stats = {"packages": len(live), "baseline": len(base),
             "lines": {e["package"]: e["lines"] for e in live.values()},
             "files": {e["package"]: e["files"] for e in live.values()}}
    return issues, warns, stats


def build(root: str = ".", recorded_at: str = "") -> Dict[str, Any]:
    """→ 当前状态的基线文档（不含 per_file，控制体量；digest 锁住逐文件行数映射）。"""
    pkgs = []
    for e in scan(root)["packages"]:
        pkgs.append({k: e[k] for k in ("package", "dir", "files", "lines", "digest")})
    return {"schema": SCHEMA,
            "note": "社区资产外形基线（文件数 / 行数 / 逐文件行数映射摘要）。内容改动后须显式重签："
                    "`nf asset baseline --write`——数字不写在 verify.sh 里，基线变更与内容变更同提交可见。",
            "recorded_at": recorded_at or date.today().isoformat(),
            "packages": pkgs}


def write(root: str = ".", recorded_at: str = "") -> str:
    """重签基线 → 写入 BASELINE_REL，返回绝对路径。"""
    doc = build(root, recorded_at=recorded_at)
    p = os.path.join(root, BASELINE_REL)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(doc, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    return p
