# ST 制卡校验报告

- 对象：`docs/examples/st-validate/fixture_worldbook_messy.json`
- 判定形态：**worldbook**
- 结果：fail 1 · warn 6 · info 0

| 规则 | 级别 | 严重度 | 说明 |
|---|---|---|---|
| W5 | S | warn | 第 0 条未声明 scanDepth（触发可能在扫描范围外） |
| W5 | S | warn | 第 1 条未声明 scanDepth（触发可能在扫描范围外） |
| W2 | S | warn | key 含逗号（会被当分隔符）：驿站,客栈 |
| W5 | S | warn | 第 2 条未声明 scanDepth（触发可能在扫描范围外） |
| W1 | M | fail | 第 3 条 content 为空 |
| W5 | S | warn | 第 3 条未声明 scanDepth（触发可能在扫描范围外） |
| W2 | S | warn | 同书内 key 重复 2 次：北境 |

> 本报告只覆盖**可自动化项**（R1 结构 / R3 世界书 / R4 变量）；
> R2 引用一致、R5 可复现、R6 长会话友好等仍需人工清单（见 `docs/st-quality-checklist.md`）。
> 校验器原型 v0 不解析 PNG 实卡；输入为已解出的 JSON。
