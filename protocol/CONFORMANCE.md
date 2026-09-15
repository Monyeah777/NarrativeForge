# NF 一致性声明（CONFORMANCE）
> ⛔ 操作指令：本文件是**机检声明**——三段（声明 / 范围 / 排除）由 `nf conformance --declaration` 逐条断言；改数字改不动门禁（版本一律与真源比对）。
> 最后更新：2026-09-14

> 性质：这是 NF 对「符合什么、管到哪、什么不管」的**显式声明**（机制借鉴 ACP 的 `CONFORMANCE.md`：
> 声明 + scope 白名单 + **显式排除清单**）。它不替代 `nf conformance` 的**报告**，两者互补——
> 报告说"跑过一遍的结论"，本声明说"范围与版本边界"。

## 声明

| 规范 | 版本 | 真源 |
|---|---|---|
| protocol.yaml schema | `2` | 01 §6.1 / 各包 `protocol.yaml` |
| registry schema | `2` | 02 头部 + `desktop/src/core/registry.json` |
| machine_contract schema | `1` | `protocol/schema/contract.schema.json` |
| IDL schema 集 | `5 件` | `protocol/schema/` |
| 基线 | `v2.27 · check1-37 · PASS=61` | `verify.sh` + `quality_baseline.EXPECTED_*` |

## 范围

（scope 白名单：以下路径在声明范围内，必须存在且受门禁约束）

- `01_核心协议.md`
- `02_联动注册表.md`
- `06_Agent执行协议.md`
- `07_官方核心出厂与社区预设导航.md`
- `STRATEGY.md`
- `llms.txt`
- `protocol`
- `03_管线库`
- `04_模块库`
- `05_资产库`
- `community`
- `library`
- `patterns`
- `desktop/src`
- `desktop/tests`
- `scripts`

## 排除

| 路径 | 理由 |
|---|---|
| `.rivet` | 本地 AI 协作工作区（运行时状态与内部档案，不入库） |
| `results` | 审计与外部实测记录（历史时点事实，不随现状更新） |
| `docs/41_*` | 波 C 逐波实测记录（历史） |
| `docs/42_*` | 42 质量纵深工程记录（历史） |
| `docs/44_*` | 44 波记录（历史） |
| `docs/45_*` | 45 波记录（历史） |
| `docs/external-validation-assets` | 外部验证素材副本（外部产物，非 NF 规范件） |
| `CHANGELOG.md` | 版本功能史（历史散文段不入范围） |
| `docs/L3_FROZEN.md` | 端壳退役记录（冻结史，不再演进） |
| `.github` | 平台配置与投稿模板（平台面，非协议件） |
| `docs/paste_card.md` | 归档件（B2 通道免除后冻结，不再维护） |
