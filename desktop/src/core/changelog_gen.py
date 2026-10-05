"""变更日志生成（changelog generation）：从**变更条目 + 提交约定**生成版本节。

为什么需要（内部差距实证 2026-10-05）：对标同类顶尖项目（release-please / semantic-release /
changesets）的最后一环是「版本节由机器生成」——NF 此前有提交信息判据（scripts/commit_msg_check.py）
与变更条目收集（changes/unreleased/），但 CHANGELOG 段落仍靠收口时手写，**条目与日志之间没有机器通路**。
本模块补上这一环，且保持 NF 纪律：

1. **确定性**：渲染不含墙钟——版本与日期由调用方给（--version / --date），分组按固定类型序、
   条目按文件名序；同输入两次渲染逐字节一致。
2. **可溯源**：每条渲染出来的条目必须来自「变更条目文件」或「提交主题」——不生成、不合并、
   不改写原文（只做分组与格式），因此不可能编造。
3. **无外部耦合**：不连 GitHub、不开 PR；发布 PR 的 NF 原生等价物 = 预览面（打印）与写面
   （--write）两步走，人工审阅后落盘。

子命令：nf changelog [--version X.Y.Z] [--date YYYY-MM-DD] [--json] [--write] [--no-commits]。
写面（--write）：把生成的版本节插入 CHANGELOG 顶部，并把 changes/unreleased/*.md 归档到
changes/<version>/（幂等：同版本重复写替换该节，不重复插入）。

纪律：纯标准库；无网络；缺件/空根如实报 issue 不裸崩；git 不在场时提交面退化为空（不报错）。
"""
from __future__ import annotations

import re
import shutil
import subprocess  # nosec B404 —— 仅调本地 git（argv 列表、无 shell）
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

#: 类型分组顺序（渲染顺序真源；与 CONTRIBUTING §1 的 type 词表同源 + release）。
TYPE_ORDER: Tuple[str, ...] = ("feat", "fix", "perf", "refactor", "docs", "test", "chore", "release")
_TYPE_TITLE = {"feat": "Features", "fix": "Bug Fixes", "perf": "Performance",
               "refactor": "Refactors", "docs": "Documentation", "test": "Tests",
               "chore": "Chores", "release": "Releases", "other": "Other"}
_ENTRY_TYPE = re.compile(r"(?m)^type:\s*([a-z]+)\s*$")
_ENTRY_NOTE = re.compile(r"(?m)^note:\s*(.+?)\s*$")
_ENTRY_SURFACE = re.compile(r"(?m)^surface:\s*(.+?)\s*$")
_CONV = re.compile(r"^(?P<type>[a-z]+)(?:\((?P<scope>[^)]*)\))?!?:\s*(?P<text>.+)$")
_HEADER = "# Changelog"


def entries(root: str = ".", changes_dir: str = "changes/unreleased") -> List[Dict[str, str]]:
    """读变更条目（按文件名序；字段缺失的条目也返回，由调用方如实报）。"""
    d = Path(root) / changes_dir
    out: List[Dict[str, str]] = []
    if not d.is_dir():
        return out
    for f in sorted(d.glob("*.md")):
        txt = f.read_text(encoding="utf-8", errors="replace")

        def _m(rx):
            m = rx.search(txt)
            return m.group(1) if m else ""

        out.append({"file": f.name, "type": _m(_ENTRY_TYPE), "note": _m(_ENTRY_NOTE),
                    "surface": _m(_ENTRY_SURFACE)})
    return out


def _git(root: Path, *args: str) -> Optional[str]:
    """调 git（argv 列表、无 shell）；git 不在场/非 git 树 → None（不报错）。"""
    git = shutil.which("git")
    if not git:
        return None
    try:
        p = subprocess.run([git, *args], cwd=str(root), capture_output=True, text=True,  # noqa: S603
                           encoding="utf-8", errors="replace")  # nosec B603/B607 —— argv 列表、无 shell
    except OSError:
        return None
    return p.stdout if p.returncode == 0 else None


def _last_tag(root: str = ".") -> str:
    """最近一个 tag（发布边界）——提交扫描只取「上次发布之后」，不把全史塞进版本节。"""
    out = _git(Path(root), "describe", "--tags", "--abbrev=0")
    return (out or "").strip()


def commit_subjects(root: str = ".", since: str = "") -> List[str]:
    """提交主题（新→旧；git 不在场返回空）。"""
    args = ["log", "--pretty=%s"]
    if since:
        args.append(since + "..HEAD")
    out = _git(Path(root), *args)
    return [ln.strip() for ln in (out or "").splitlines() if ln.strip()]


def parse_commit(subject: str) -> Optional[Dict[str, str]]:
    """解析约定式提交主题；不匹配返回 None（不猜）。"""
    m = _CONV.match(subject)
    if not m:
        return None
    return {"type": m.group("type"), "scope": m.group("scope") or "", "text": m.group("text")}


def _bullets(root: str, changes_dir: str, use_commits: bool) -> Dict[str, List[str]]:
    groups: Dict[str, List[str]] = {}
    for e in entries(root, changes_dir):
        note = e["note"] or e["file"]
        text = note + (("（%s）" % e["surface"]) if e["surface"] else "")
        groups.setdefault(e["type"] or "other", []).append(text)
    if use_commits:
        seen = set()
        since = _last_tag(root)          # 边界 = 最近 tag（无 tag 时退化为全史，行为与旧版一致）
        for subject in commit_subjects(root, since=since):
            parsed = parse_commit(subject)
            if not parsed:
                continue
            line = parsed["text"] if not parsed["scope"] else "%s: %s" % (parsed["scope"], parsed["text"])
            if line in seen:
                continue
            seen.add(line)
            groups.setdefault(parsed["type"], []).append(line)
    return groups


def render(root: str = ".", version: str = "", date: str = "", changes_dir: str = "changes/unreleased",
           use_commits: bool = True) -> str:
    """确定性版本节（无墙钟；类型序固定，组内保持来源序）。"""
    groups = _bullets(root, changes_dir, use_commits)
    lines = ["## [%s] - %s" % (version or "X.Y.Z", date or "YYYY-MM-DD"), ""]
    order = list(TYPE_ORDER) + sorted(k for k in groups if k not in TYPE_ORDER)
    for t in order:
        if not groups.get(t):
            continue
        lines.append("### " + _TYPE_TITLE.get(t, t))
        lines.append("")
        for b in groups[t]:
            lines.append("- " + b)
        lines.append("")
    if len(lines) == 2:
        lines.append("（本波无变更条目与可解析提交）")
        lines.append("")
    return "\n".join(lines).rstrip("\n") + "\n"


def _section_bullets(section_text: str) -> List[str]:
    """版本节里的条目行（「- 」起首）——同版本替换前的**丢内容守卫**用。"""
    return [ln for ln in section_text.splitlines() if ln.startswith("- ")]


def _lost_bullets(old: str, section: str) -> List[str]:
    """同版本替换会丢掉的条目（旧节有、生成节没有）；空 = 可安全替换。"""
    generated = set(_section_bullets(section))
    return [b for b in _section_bullets(old) if b not in generated]


def insert_into_changelog(text: str, section: str, version: str) -> str:
    """把版本节插到表头之后、第一已有版本节之前；同版本已存在则替换（幂等）。

    丢内容守卫（2026-10-05）：同版本节含未被生成覆盖的条目 → 抛 `ValueError`（写面 fail-closed）。
    """
    if not text.startswith(_HEADER):
        return section + "\n" + text
    head, sep, rest = text.partition("\n")
    marker = "## [%s]" % version
    if version and marker in rest:
        pre, _s, post = rest.partition(marker)
        old, _s2, tail = post.partition("\n## [")
        tail = ("\n## [" + tail) if tail else ""
        lost = _lost_bullets(old, section)
        if lost:
            raise ValueError(
                "同版本节替换会丢失 %d 条未被生成的条目（首条：%s）——修复指引：先归档/合并既有节，"
                "或改用新版本号（写面默认 fail-closed，不静默丢内容）" % (len(lost), lost[0][:80]))
        return head + sep + pre + section + tail
    parts = rest.split("\n", 1)
    tail = parts[1] if len(parts) > 1 else ""
    while tail.startswith("\n"):
        tail = tail[1:]
    return head + sep + "\n" + section + "\n" + tail


def write(root: str = ".", version: str = "", date: str = "", changes_dir: str = "changes/unreleased",
          use_commits: bool = True) -> Dict[str, Any]:
    """写面：插版本节 + 归档变更条目（changes/<version>/）；返回动作摘要。"""
    r = Path(root)
    if not version:
        return {"ok": False, "issues": ["--write 需要 --version（版本号是真源，不臆造）"]}
    section = render(root, version=version, date=date, changes_dir=changes_dir, use_commits=use_commits)
    cl = r / "CHANGELOG.md"
    txt = cl.read_text(encoding="utf-8") if cl.is_file() else (_HEADER + "\n")
    from core import atomic_write          # 活文档：原子写（半截文件会被门禁当漂移）
    try:
        new_text = insert_into_changelog(txt, section, version)
    except ValueError as exc:              # 丢内容守卫：如实报出，不落半截/不静默删历史
        return {"ok": False, "issues": [str(exc)]}
    atomic_write.write_text(str(cl), new_text)
    archived: List[str] = []
    d = r / changes_dir
    if d.is_dir():
        dest = r / "changes" / version
        dest.mkdir(parents=True, exist_ok=True)
        for f in sorted(d.glob("*.md")):
            shutil.move(str(f), str(dest / f.name))
            archived.append(f.name)
        (d / ".gitkeep").touch()
    return {"ok": True, "version": version, "date": date, "section_lines": section.count("\n"),
            "archived": archived}


def check(root: str = ".", changes_dir: str = "changes/unreleased") -> Tuple[List[str], Dict[str, Any]]:
    """可机检面：渲染确定 + 条目可溯源（每条都出现在渲染里）。"""
    r = Path(root)
    if not (r / "verify.sh").is_file():
        return (["读不到仓库根（缺 verify.sh）——变更日志生成须在 NF 仓库根运行"], {})
    issues: List[str] = []
    a = render(root, version="0.0.0", date="1970-01-01", changes_dir=changes_dir, use_commits=False)
    b = render(root, version="0.0.0", date="1970-01-01", changes_dir=changes_dir, use_commits=False)
    if a != b:
        issues.append("变更日志渲染不确定（同输入两次不一致）")
    ents = entries(root, changes_dir)
    for e in ents:
        if not e["note"]:
            continue        # 字段缺失由 release_gate 的条目判据报，这里只管可溯源性
        if ("- " + e["note"]) not in a:
            issues.append("条目 %s 未出现在渲染里（修复指引：检查 type/note 字段）" % e["file"])
    return issues, {"entries": len(ents), "types": sorted({e["type"] for e in ents if e["type"]}),
                    "preview_lines": a.count("\n")}
