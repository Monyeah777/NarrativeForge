# ST 制卡校验报告

- 对象：`docs/examples/mvu-output/mvu_variables.json`
- 判定形态：**mvu-variables**
- 结果：fail 0 · warn 1 · info 0

| 规则 | 级别 | 严重度 | 说明 |
|---|---|---|---|
| V5 | S | warn | 变量 phase_trace 为 array，规范建议优先 record |

> 本报告只覆盖**可自动化项**（R1 结构 / R3 世界书 / R4 变量）；
> R2 引用一致、R5 可复现、R6 长会话友好等仍需人工清单（见 `docs/st-quality-checklist.md`）。
> 校验器原型 v0 不解析 PNG 实卡；输入为已解出的 JSON。
