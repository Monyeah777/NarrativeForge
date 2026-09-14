# NF Patterns · 实践包品类
> ⛔ 操作指令：本文含可直接执行的命令与格式判定，阅读即执行。
> 最后更新：2026-09-14

## 这是什么

`patterns/` 是 NF 的**实践包**货架（与 `community/` 的内容域包并列）：每条 pattern 是一份
**可发布、可消费、可移植**的最佳实践——它不说"这个世界的魔法怎么运作"，而说
"这类文件应当怎么写"。

**入库铁律**：每条 pattern 必须有**仓库内实证**——`applies_to` 指向的路径/通配必须真的匹配到文件，
`evidence` 必须指向真实件或 `checkN`。指向空气的 pattern 会被 `nf patterns verify` 判 FAIL。

## 目录结构

```
patterns/
  README.md              # 本文（品类说明）
  INDEX.md               # 登记表（投影，由 frontmatter 重生成）
  <name>/PATTERN.md      # 一个 pattern 包（真源 = 头部 frontmatter）
```

## PATTERN.md 格式

```markdown
---
id: <目录同名>
name: <人读名>
status: active|deprecated
scope: [<这条 pattern 管哪一层，如 协议层 / 代码层>]
applies_to:            # 适用面（必须是仓库内真实存在的路径或通配）
  - desktop/src/core/*.py
rules:                 # 可执行规则（每条一句话、可检查）
  - ...
evidence:              # 可证性：真实件路径 或 checkN
  - check27
  - desktop/src/core/purity_scan.py
---

正文：为什么、怎么用、反例。
```

## 怎么用

```bash
python scripts/nf.py patterns ls                 # 列全部 pattern
python scripts/nf.py patterns show <id>          # 看单条（frontmatter + 正文）
python scripts/nf.py patterns for <文件路径>      # 反向查：这个文件适用哪些 pattern
python scripts/nf.py patterns verify             # 机检（格式 + 可证性）
python scripts/nf.py patterns reindex            # 重建 INDEX 投影
```
