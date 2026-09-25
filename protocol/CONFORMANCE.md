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
| 基线 | `v2.28 · check1-38 · PASS=66` | `verify.sh` + `quality_baseline.EXPECTED_*` |

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
- `skills`

## 排除

> 「允许不存在」标注的条目为运行期/本地件（可不在库内，缺省不算缺口）；其余条目路径须真实存在。

| 路径 | 理由 |
|---|---|
| `.rivet` | 本地 AI 协作工作区（运行时状态与内部档案，不入库；**允许不存在**——运行期/本地件，fresh clone 无此目录属预期） |
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

## 规范化摘要口径

> 本段是**算法声明**，不是新机制：把回执 / 锚 / 一致性报告 / 模组契约摘要共用的规范化摘要口径写明——
> 此前该口径只存在于实现里（`receipts.py` / `attest.py` / `mvu_adapter.py` / `knowledge_sig.py`），
> **仓外读者侧验证器**（`scripts/nf_verify.py` 形态：纯标准库、零 NF 依赖）无从逐字复现。

**摘要口径**：`SHA-256`（十六进制小写）；输入 = UTF-8 编码的规范 JSON——键按字典序排序（`sort_keys`）、
非 ASCII 不转义（`ensure_ascii=False`）、无多余空白（分隔符 `,` 与 `:`）。

**Merkle（RFC 6962 风格）**：叶 = `SHA-256(0x00 ‖ 载荷)`；节点 = `SHA-256(0x01 ‖ 左 ‖ 右)`；空集 → 无根；单叶 → 该叶。域分隔字节 `0x00` / `0x01` 是防「叶与节点」跨型碰撞的结构手段。

**与 RFC 8785（JSON Canonicalization Scheme）的关系**：本口径**不是** JCS 实现，差异可判定——① 数值序列化：JCS 采用 ECMAScript 数值字面量规则，本仓沿用实现语言的 JSON 序列化；② 键排序：JCS 按 UTF-16 码元排序，本仓按码位排序（非 BMP 字符处可能不同）；③ 转义集规则另有规定。**故本仓摘要只声明「仓内可复现 + 读者侧可按本段复现」，不声明 JCS 兼容**；将来若需对外互操作（L3 导出面），须先做 JCS 对齐评估再改本声明，不得默认两者相等。
