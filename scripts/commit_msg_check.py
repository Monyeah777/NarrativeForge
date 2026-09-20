#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""提交信息机检（Conventional Commits · 纯标准库）。

**内部差距**：`CONTRIBUTING §1` 有成文的提交信息格式，但此前**零判据**——
格式全靠人记（审查中实测：80 条里 3 条 Merge 之外全部合规，属"实践好但没门禁"）。
本脚本把该节翻成可执行判据，由 `scripts/install_hooks.sh` 安装为 `commit-msg` 钩子：
不合规即**拒绝提交**并给出修复指引（不想被检可用 `git commit --no-verify`）。

判据（逐条对齐 CONTRIBUTING §1 + 仓库提交史实证）：
1. 主题行 `<type>(<scope>): <subject>`——type ∈ 六种规范 type + `release`（实证存在，
   已同步补进 §1 表）；scope 可省，字符集宽松（实测有 `state-front` / `v2.10.0` 这类）；
   `!` 表破坏性变更；
2. `subject` 非空，**禁以句号/「。」结尾**（§1 明写；实测 80 条零例外）；
3. 有正文时，主题行后须空一行（Conventional Commits 体例）；
4. **不设行长上限**——实测仓库主题行中位 86、最长 239，硬套 72/100 会压死既有实践；
5. 放行：`Merge …` / `Revert …` / `fixup!…` / `squash!…` / 空消息（git 会自行中止）。

用法：
    python scripts/commit_msg_check.py <提交信息文件>     # commit-msg 钩子调用（git 传 $1）
    python scripts/commit_msg_check.py --self-test        # 自检（正/反例各若干）

**校准数据（本仓 385 条历史提交回放）**：合规 381 条，例外 4 条（1.0%）——3 条为早期
无 type 的提交（`E3 MCP 协议级实测通过：…` / `T3-1 …chore(ci) A3/B3` / `Narrative Forge v1.0：…`），
1 条为**已退役 Android 线**的 `build(android): …`（该线已按裁决 #16 移除，`build` 不再入词表，
构建类改动走 `chore`）。门禁**不回检历史**，只约束新提交。
"""
from __future__ import annotations

import re
import sys

#: type 词表 = CONTRIBUTING §1 六种 + **仓库提交史实证**的四种：`release`（发版）、
#: `merge`（并行流合流）、`ci`（CI 改动，3 例）、`lib`（**入库机器人**，见
#: .github/scripts/{gitee,library}_ingest.py 的 `lib(Y12):` 提交——漏掉它会让门禁打断自动化）。
TYPES = ("feat", "fix", "docs", "refactor", "test", "chore", "release", "merge", "ci", "lib")
#: scope 字符集**从宽**：实测仓内用过 `state-front` / `v2.10.0` / `docs+test` / `41,B1`
#: / `remote 42立项/41封存注记`——凡非括号内容皆收（严到 CONTRIBUTING 字面会误伤实践）
SCOPE = r"[^()]+"
#: 允许多 type 并联（`docs+feat(quality):` / `feat(cli)+docs:` / `merge(remote main) + fix:`）
_ONE = r"(?:%s)(?:\(%s\))?!?" % ("|".join(TYPES), SCOPE)
SUBJECT_RE = re.compile(r"^%s(?:\s*\+\s*%s)*: (?P<subject>.*)$" % (_ONE, _ONE))
BYPASS_PREFIX = ("Merge ", "Revert ", "fixup!", "squash!")


def normalize(text: str) -> str:
    """规范化提交信息：去 git 注释行（`#`）、行尾空白，并**掐掉首尾空行**。

    首行空行不能当主题行——git 的 `%B` 记录与默认模板都可能以空行或注释开头
    （本仓回放实测：不掐首空行会把 79 条合规提交全判成违规）。
    """
    keep = [ln.rstrip() for ln in text.splitlines() if not ln.startswith("#")]
    while keep and not keep[0]:
        keep.pop(0)
    while keep and not keep[-1]:
        keep.pop()
    return "\n".join(keep)


def check(text: str) -> list:
    """→ 违规清单（空 = 合规）。纯函数，便于单测。"""
    body = normalize(text)
    if not body.strip():
        return []                       # 空消息：git 自己会中止，不重复判
    lines = body.split("\n")
    subject = lines[0].strip()
    if any(subject.startswith(p) for p in BYPASS_PREFIX):
        return []                       # 合并/回退/压缩提交不按 CC 判
    out = []
    m = SUBJECT_RE.match(subject)
    if not m:
        out.append(
            "主题行不合 Conventional Commits：%r\n"
            "      应为 `<type>(<scope>): <subject>`（scope 可省）——"
            "type 限 %s（见 CONTRIBUTING §1）" % (subject[:80], "/".join(TYPES)))
    else:
        subj = m.group("subject").strip()
        if not subj:
            out.append("主题行缺 <subject>：`%s` 之后须写一句话摘要" % m.group(0).split(":")[0])
        elif subj.endswith(("。", ".")):
            out.append("subject 禁以句号结尾（CONTRIBUTING §1）：%r" % subj[-20:])
    if len(lines) > 1 and lines[1].strip():
        out.append("主题行与正文之间须空一行（Conventional Commits 体例）；"
                   "第 2 行现在是：%r" % lines[1][:60])
    return out


def _self_test() -> int:
    cases = [
        ("feat(protocol): 新增 X 判据", True),
        ("docs: 补 02 §8 登记", True),
        ("release(v2.10.0): 收口发布", True),
        ("chore!: 彻底移除旧线（裁决 #16）", True),
        ("refactor(core): 收口\n\n正文说明", True),
        ("docs+feat(quality): 多 type 并联（仓内实证形态）", True),
        ("feat(cli)+docs: 并联带 scope", True),
        ("merge(remote main) + fix: 合流型", True),
        ("feat(41,B1): scope 带逗号", True),
        ("feat(docs+test): scope 带加号", True),
        ("ci(workflow): CI 改动", True),
        ("lib(Y12): 云端代收 NF-9 自动入库（Issue #1，投稿人 X）", True),
        ("Merge branch 'main'", True),
        ("Revert \"feat: x\"", True),
        ("", True),
        ("feat 少了冒号", False),
        ("\n\nfeat(core): 首部空行也算合规（git 记录形态）", True),
        ("unknown(scope): 类型越词表", False),
        ("feat(core): 句号结尾。", False),
        ("feat(core): ", False),
        ("feat(core): 摘要\n正文紧贴未空行", False),
    ]
    bad = 0
    for msg, want_ok in cases:
        got = check(msg)
        ok = not got
        if ok != want_ok:
            bad += 1
            print("[x] 期望 %s 实得 %s：%r → %s" % (want_ok, ok, msg[:40], got))
    print("自检：%d/%d 通过" % (len(cases) - bad, len(cases)))
    return 1 if bad else 0


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] == "--self-test":
        return _self_test()
    if not argv:
        print("用法：python scripts/commit_msg_check.py <提交信息文件>", file=sys.stderr)
        return 2
    try:
        with open(argv[0], encoding="utf-8") as fh:
            text = fh.read()
    except OSError as exc:
        print("读不到提交信息文件：%s（修复指引：确认路径存在后重试）" % exc, file=sys.stderr)
        return 2
    issues = check(text)
    if not issues:
        return 0
    print("== 提交信息不合规（CONTRIBUTING §1 · 判据见 scripts/commit_msg_check.py）==", file=sys.stderr)
    # 标记用 ASCII：Windows 的 git 会把控制台码页装不下的字形（如 ✗）转义成 \u2717，
    # 而中文能正常显示——故此处避开花哨字形，保证修复指引在 hook 路径上可读。
    for i in issues:
        print("  [x] %s" % i, file=sys.stderr)
    print("  修复指引：改成 `<type>(<scope>): <subject>`，type ∈ %s；"
          "确实需要绕过用 `git commit --no-verify`（并说明原因）" % "/".join(TYPES), file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
