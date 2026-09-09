---
mode: full
target: 45 A5 指令档步进级可机检审计
verdict: 通过
date: 2026-09-09
auditor: 天枢（基于项目现状取证）
related: [desktop/src/core/instruction_step_audit.py, agent_组装指令包_v0.2.md, docs/45_执行遥测规范.md, docs/45_M2_回合级drill.md, docs/45_M3_techdoc载荷提案.md, docs/44_M2_AI通道内容规范.md]
---

# M_AUDIT 45 A5 · 指令档步进级审计

## 审计口径

核心指令/规范档（v0.2 指令包、45 遥测、45 M2 drill、45 M3 提案、44 M2 内容规范）中**机器可执行的步骤引用**逐一验证：
- 内联命令 `nf <sub>`：子命令存在于 scripts/nf.py parser 面；
- `python scripts/…`：脚本文件真实存在；
- 引用仓库相对路径（.md/.json/.yaml）：文件真实存在。

实现：`instruction_step_audit.py`（常驻 unittest）。

## 结果

- 审计 5 档、检出 5 条机器可执行步骤引用，全部可寻址；零缺失、零未知子命令。
- 步骤引用（抽样）：`nf assemble --check`/`--rounds`/`--trace`、`nf asset thickness/usage/density`、`nf release --fast`、`scripts/bump_verify.sh`、`payload_registry` 校验等均与当前实现一致（此前 W 系列已先行补齐，故审计零命中）。

## 五维注记

文档可执行性：⛔/last-updated 清单级之上，新增“步骤引用可寻址”机检常驻——指令不再只“读起来像命令”。

## 结论

通过。A2-A5 全部收口；A 剩余仅 5 条 techdoc 载荷待作者确认（提案在 `docs/45_M3_techdoc载荷提案.md`）。
