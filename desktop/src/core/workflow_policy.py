"""工作流供应链策略（外部标准落地 · 机检本仓 `.github/workflows/*.yml`）。

标准出处（2026-09-29 取源，`ossf/scorecard` 的 `docs/checks.md`）：
- **Pinned-Dependencies**：构建/发布过程的依赖必须钉到**具体哈希**，不允许可变版本或范围
  （"a dependency that is explicitly set to a specific hash instead of allowing a mutable
  version or range of versions"）；对 GitHub 工作流即 `uses: owner/repo@<40 位提交 SHA>`。
- **Token-Permissions**：GITHUB_TOKEN 的权限须**显式且最小**（默认只读），不得隐式全权。

落到本仓的两条机检（外部标准只作机制借鉴；判据本体在仓库内可核）：
1. 每条 `uses:` 的引用必须是 40 位十六进制**提交** SHA——`@v4` 这类可变引用判 FAIL；
   本地动作（`./…`）豁免；`# vX.Y.Z` 注释记 WARN（可读性，不判死）。
2. 每个工作流须有**显式** `permissions:` 段，且不得 `write-all`。
3. 每个工作流的 job 须声明 `timeout-minutes`（**挂死有界**：GitHub 默认 6h，挂死的 job
   会把 runner 占满并挤掉后续定时任务——2026-10-01 补，实测 8 件工作流缺此项）。
4. `.github/requirements-*.txt` 的每条依赖须钉 `==` 具体版本（同一标准的「包度量」面；
   出处之二：FAIR4RS v1.0（DOI 10.5281/zenodo.6374314）的 **R（Reusable）**——可复现要求
   依赖可重建，故版本不得浮动）。

纪律：纯标准库、只读、错误消息带修复指引。
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

WORKFLOWS_REL = ".github/workflows"
USES_RE = re.compile(r"^\s*(?:-\s*)?uses:\s*(\S+)(.*)$")
SHA_RE = re.compile(r"^[0-9a-f]{40}$")


def workflows(root: str = ".") -> List[str]:
    """仓库内的工作流件（仓库相对、排序）。"""
    d = Path(root) / WORKFLOWS_REL
    if not d.is_dir():
        return []
    return sorted("%s/%s" % (WORKFLOWS_REL, p.name)
                  for p in d.iterdir() if p.suffix in (".yml", ".yaml"))


def _timeout_issues(rel: str, text: str) -> List[str]:
    """每个工作流必须有 job 级 `timeout-minutes`（2026-10-01 补，Fail-Closed 面）。

    为什么：GitHub 的默认上限是 **6 小时**——一个挂死的 job（网络等待、工具卡住）会把
    runner 占满到默认上限，期间**后续定时任务被挤掉**（`gitee-poll` 是每 10 分钟一轮的
    轮询入库线）。显式声明上限 = 「挂死有界」这条不变量的可核载体。
    """
    if re.search(r"^\s*timeout-minutes:\s*\d+\s*(?:#.*)?$", text, re.M):
        return []
    return ["%s 未声明 job 级 `timeout-minutes`（修复指引：在该 job 的 `runs-on` 下一行加 "
            "`timeout-minutes: <分钟>`；挂死不许占满默认 6h）" % rel]


def _pin_issues(rel: str, text: str) -> List[str]:
    out: List[str] = []
    for i, line in enumerate(text.splitlines(), 1):
        m = USES_RE.match(line)
        if not m:
            continue
        ref = m.group(1).rstrip(",").strip('"\'')
        if ref.startswith("./"):
            continue                                   # 本地动作：无供应链风险
        if "@" not in ref:
            out.append("%s:%d uses 缺版本引用：%s（修复指引：钉 owner/repo@<40 位提交 SHA>）"
                       % (rel, i, ref))
            continue
        _, _, rev = ref.rpartition("@")
        if not SHA_RE.match(rev):
            out.append("%s:%d 未钉提交 SHA：%s@%s（修复指引：钉 40 位 SHA——`@v4` 这类可变引用"
                       "可被上游改写；改法见 ossf/scorecard docs/checks.md §Pinned-Dependencies）"
                       % (rel, i, ref.split("@")[0], rev[:24]))
    return out


def _perm_issues(rel: str, text: str) -> List[str]:
    out: List[str] = []
    perms = [ln for ln in text.splitlines()
             if re.match(r"^permissions:\s*", ln) or re.match(r"^\s+permissions:\s*", ln)]
    if not perms:
        out.append("%s 缺显式 permissions 段（修复指引：按 ossf/scorecard §Token-Permissions "
                   "给 GITHUB_TOKEN 最小权限，如 `permissions:\n  contents: read`）" % rel)
    elif any(re.search(r"\bwrite-all\b", ln) for ln in perms):
        out.append("%s 使用 write-all（修复指引：改为按需最小集，见 §Token-Permissions）" % rel)
    return out


def scan(root: str = ".") -> Tuple[List[str], List[str], Dict[str, Any]]:
    """→ (issues, warns, stats)：未钉 SHA / 缺显式 permissions = FAIL；缺版本注释 = WARN。"""
    issues: List[str] = []
    warns: List[str] = []
    files = workflows(root)
    pinned = 0
    for rel in files:
        text = (Path(root) / rel).read_text(encoding="utf-8", errors="replace")
        issues += _pin_issues(rel, text)
        issues += _perm_issues(rel, text)
        issues += _timeout_issues(rel, text)
        for line in text.splitlines():
            m = USES_RE.match(line)
            if m and SHA_RE.match(m.group(1).rpartition("@")[2].rstrip(",")):
                pinned += 1
                if "#" not in m.group(2):
                    warns.append("%s 钉了 SHA 但没写版本注释（修复指引：行尾补 `# v4` 一类注释，"
                                 "便于依赖更新）" % rel)
    stats = {"workflows": len(files), "pinned_uses": pinned,
             "with_explicit_permissions": sum(
                 1 for rel in files
                 if re.search(r"^permissions:\s*|^\s+permissions:\s*",
                              (Path(root) / rel).read_text(encoding="utf-8", errors="replace"),
                              re.M))}
    reqs = sorted((Path(root) / ".github").glob("requirements-*.txt")) \
        if (Path(root) / ".github").is_dir() else []
    for p in reqs:
        for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
            t = line.strip()
            if not t or t.startswith(("#", "-")):
                continue
            if "==" not in t:
                issues.append("%s:%d 依赖未钉版本：%s（修复指引：改 `包==版本`——FAIR4RS R 面"
                              "要求依赖可重建，见 DOI 10.5281/zenodo.6374314 / Scorecard "
                              "§Pinned-Dependencies）" % (p.name, i, t[:60]))
    stats["requirements_files"] = len(reqs)
    return issues, warns, stats
