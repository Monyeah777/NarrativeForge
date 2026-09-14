# 实践包（patterns）
> ⛔ 操作指令：阅读即执行——本文含可直接执行的命令与判定，勿当资料阅读。
> 最后更新：2026-09-14

## 是什么

`patterns/` 是与 `community/`（内容域包）并列的**实践包货架**：每条 pattern 是可发布、可消费、
可移植的最佳实践。真源 = `patterns/<name>/PATTERN.md` 的 frontmatter，`patterns/INDEX.md` 是投影。

## 入库铁律（可证性）

`applies_to` 指向的路径/通配**必须匹配到仓库内真实文件**；`evidence` 必须指向真实件或 `checkN`
——指向空气的 pattern 会被 `nf patterns verify` 判 FAIL。**不为齐全而造 pattern。**

## 怎么用

```bash
python scripts/nf.py patterns ls
python scripts/nf.py patterns show single-source-truth
python scripts/nf.py patterns for library/INDEX.md     # 反向查：这个文件适用哪些 pattern
python scripts/nf.py patterns verify
python scripts/nf.py patterns reindex                  # 重建 INDEX 投影
```

MCP 侧：`pattern_read`（工具）/ `nf://repo/pattern/{id}`（资源）。
