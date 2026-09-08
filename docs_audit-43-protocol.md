---
mode: full
target: 43 协议层顶尖化工程（A1-A5）收口
verdict: 通过
date: 2026-09-08
auditor: 天枢（基于项目现状取证）
related: [43_协议层顶尖化工程规划.md, protocol/README.md, ROADMAP §9 协议层顶尖行, VERSION-MATRIX.md]
---

# M_AUDIT 协议设计审计（43 · 五维自评段随行）

> **被审计对象（target）**：43「协议层顶尖化 A1-A5」全量收口。
> **审计问题**：协议层是否按 43 五要素验收（IDL 单一真相 / 一致性可分级 / 演进可预测 / 产物可复现 / 顶尖闭环）完成，且执行约束（零第三方 JSON-schema 依赖 / 不 bump registry_schema_version / 门禁绿不构成全称宣称）如实落地。

## 1. 问题重述

A1 协议 IDL / A2 Conformance 分级 / A3 扩展策略 + 影响分层 / A4 生成物同仓 golden / A5 收口 audit 是否逐一兑现，且与既有设施（check13/25/26/27、42 判级器层、nf sig/diff）边界清楚、零重复建设。

## 2. 支持侧最强论据

- A1 `protocol/schema/*.json` 五定义 + `schema_lint.py`（自实现 JSON-schema 子集，无 jsonschema）→ check28；首轮扫描即暴露 P90/P06 `type: techdoc` 值域漂移并收口（01 §2 值域文档化扩展，非 bump）。
- A2 01 §1.2 分级表 + 23 件机读块/5 协议包 `conformance: L2` + `protocol/export_conformance.json`（4 导出面 L3，证据 = 导出门禁 + 文件在场）→ check29 声明 ≤ 可证，零虚标。
- A3 `protocol/EXTENSION.md` 判据表 + `nf diff` verdict 增 `impact` 三档（CLI 打印）+ check30 拦截「版本字段结构性变更无迁移四步」。
- A4 `protocol/generated/`（idl_report.json + idl_summary.md）确定性渲染 + check31 双源一致（schema↔生成物，过期即红）。
- 全程 verify v2.16→v2.20（check1-31）PASS 41→49 每里程碑绿提交；四新 check 各带变异/否定单测（test_schema_lint / test_conformance_scan / test_extension_impact / test_protocol_golden）。

## 3. 反对侧最强论据

- A1 验收措辞「44 模块全量过 schema」的落地口径 = 44 件全量纳入扫描、**在场机读块全量过 schema**（23/44）；21 件存量旧格式模块无 machine_contract，按 check16 过渡策略保留 L0（不阻断），未做一次性情面 retro-fit——若把「全量过 schema」当「44 件均已机读契约化」是高估。
- A2 L3 的定义为「导出门禁锁定的外部契约面」，模块/包以 L2 封顶；标准 MCP/CCV3 客户端实测仍随 E3 冻结口径待回填，未做 L3 运行态宣称。
- A3 check30 的 bump 守卫基于 `git diff HEAD`（工作树 vs HEAD），fresh-clone CI 中为恒过状态；防回退主要靠 unit + check13 基线。
- 「连续两波零命中」仅完成第一波（本波自检零命中）；第二波留待下个内容波复核。

## 4. 核心变量

协议层「顶尖」的可机检载体 = schema 定义（IDL）+ 一致性声明（Conformance）+ 扩展判据（EXTENSION）+ 生成物（golden）。门禁绿 ≠ 协议全称正确——但漂移一旦发生即被编译期拦截（check28-31），这是从「机检闭环」到「顶尖」的增量所在。

## 5. 低置信度清单

- 21 件 L0 存量模块何时 retro-fit machine_contract（进 L1/L2）无排期——列为下波候选。
- 四新 check 在 GitHub Actions CI（verify job）首次全量跑仍未发生（本机绿）——推送后即验证。
- A3 三档回放实证为抽样 3+1 例，未覆盖近两年全量变更（如需可另建回放审计）。

## 6. 遗漏清单

- 未给 community 包 assets 台账（assets/README.md 键表）落 machine schema——asset.schema 现覆盖 05 provenance 官方台账；社区包资产以包内 README 为人读真相（check23 已对账键）。
- 导出面 manifest 未与 export_schema.py 内部格式定义做代码级联检（现以证据文件 + verify 门禁文字断言）。
- nf diff impact 未回写 knowledge_sig 文档串说明（代码注释已含，README 未列）——若需人读可补。

## 7. 评估结论

**评估结论（三态）**：通过

**一句话理由**：A1-A5 按 43 验收落地、四个新门禁全程绿提交、执行约束（零 jsonschema / 不 bump / 纯内部可做）如实遵守；「44 全量过 schema 的口径」「L3 门禁面 vs 实测」等边界均在 audit 与 protocol README 显式标注，未以绿代全称宣称。

## 8. 行动建议与缺陷条目

**下一步行动**：① 本 audit + CHANGELOG [Unreleased] 收口落档；② push 后确认 GitHub Actions verify job 跑 check28-31 全绿；③ 下个内容波收口复核「第二波零命中」与 21 件 L0 retro-fit 排期；④ tag/发布决策随作者拍板（43 随内容波收口，不产独立 tag）。

**回退路径**：任一 schema/协议件漂移 → 对应 check28/29/31 FAIL 即阻断提交；生成物过期 → check31 红，重跑 `protocol_golden.write_golden` 并随变更提交。

**本轮缺陷条目（= 下轮迭代输入）**：
- （缺陷：21 件存量模块缺 machine_contract——L0 过渡态，下波 retro-fit 候选）
- （缺陷：四新 check 的 GitHub Actions 首跑待 push 后验证）
- （缺陷：plan 估计 PASS 41→约 45 与实落 49 的差额 = check 计数 2/枚的账户规则，非漏项——已按实落口径归档）

## 五维自评段（43 §四.5）

① 静态可核验：check1-31 PASS=49（verify v2.20）+ schema/协议件全量扫描 + 双源 golden；② 动态可执行：IDL 漂移编译期拦截、conformance 声明 ≤ 可证、bump 无迁移记录即红；③ 架构纯度：零第三方 JSON-schema 实现（schema_lint 自实现子集）；④ 资产密度：协议 schema/EXTENSION/golden 全部入仓可追溯；⑤ 文档可执行性：protocol README + EXTENSION + generated README 均机器可查。水位：四新门禁 + 变异单测常驻；差在「21 件 L0 retro-fit 与外部实测回填」仍需后续波。
