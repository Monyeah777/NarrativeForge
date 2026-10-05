# 变更条目（changes）

> 本目录是**待发布变更的收集面**（机制借鉴 changesets）：作者/agent 在改动落地时写一条条目，
> 发布收口时按 `core/release_gate.plan()` 的 `changes-1` 步把它们归档进 `CHANGELOG.md` 并清空。

## 规则（机检，见 check38 的 release_gate 子扫描）

- 每条 = `unreleased/<日期或主题>.md`，必须含两行：
  - `type: <feat|fix|docs|refactor|perf|test|chore|release>`（词表同提交信息纪律 `CONTRIBUTING §1`）
  - `note: <一句话说明改了什么>`（非空）
- 可选 `surface: <命令面/文档名>`，便于归档时分组。
- **发布前目录须为空**（条目已归档）；空目录用 `.gitkeep` 占位。

## 为什么（内部差距实证 2026-10-05）

对标同类顶尖项目实测：同类项目用「变更条目 → 版本/变更日志」的收集面（changesets 的 `.changeset/`、
release-please 的 conventional commits）避免「发布时凭记忆写 CHANGELOG」。NF 此前只有
`scripts/commit_msg_check.py` 管**提交信息格式**，没有**面向发布的条目积累**——CHANGELOG 段落
全靠收口时手写。本目录补上这一环。
