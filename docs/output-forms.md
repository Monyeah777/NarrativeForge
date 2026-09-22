# 产出形态（output forms）
> ⛔ 操作指令：阅读即执行——本文含可直接执行的命令与判定，勿当资料阅读。
> 最后更新：2026-09-22

## 是什么

NF 此前对「产出」只有一个隐含假设：**产出是散文**。两个非叙事域包（AI系统域包 / 量化金融域包）
的数据契约、指标口径、策略规格全是 Markdown 表格——人能读，机器只能当文本：判不了形状、
判不了单位、判不了引用完整，更复算不了数。产出形态层把**形态本身**变成一等对象：

1. **形态清单**（`protocol/output_forms.json`）：12 类别 **116 条**形态，每条带规范入口与
   **本机可达性实证**（HTTP 状态 / 取样 sha256，非记忆、非宣称）；
2. **机检档位**（tier）：T0 散文 → T1 良构 → T2 形状 → T3 语义 → T4 **可复算**；
3. **包级产出面**（`community/<包>/outputs/INDEX.json`）：每包声明自己的机验产出
   （路径 / 形态 / 档位 / 角色 / schema / 双源 / 复算源）；
4. **机验率与功能面计量**（`protocol/output_forms_baseline.json` 基线，回退即 FAIL）。

档位不是「格式高低」，是**本仓能做到的判定强度**——一个 Markdown 表格是 T0，
一个 Vega-Lite 规格在本仓是 T3（结构判 + 数据绑定判），一份由净值数据重算出来的绩效报告是 T4。

| 档位 | 判定内容 | 本仓实现 |
|---|---|---|
| T0 | 只能人读 | 散文 / 自由文本 |
| T1 | 能否解析 | `markdown` / `xml` / `svg` 良构判定 |
| T2 | 类型·必填·枚举 | 自带 JSON Schema 2020-12 **子集**校验器 + `csv` / `jsonl` / `toml` / `yaml`（收窄子集） |
| T3 | 引用完整·口径·双源 | `quant-metrics`（宣称 engine 必须真实存在）、`vega-lite`、`mermaid`、`graphml`（边端点不悬空）、双源一致 |
| T4 | **可复算** | `performance-report`（净值数据 → 报告）、`concept-closure`（概念图 → 闭包与装载序） |

## 怎么用

```
python scripts/nf.py output list --status absorbed --json   # 看本波净吸收的形态
python scripts/nf.py output check community/量化金融域包/outputs/QUANT_METRICS.json
python scripts/nf.py output verify --json                   # 全量机检（与 verify check32 同语义）
python scripts/nf.py output render --write                  # 按包清单重渲染产出面（数据/图表/图示）
python scripts/nf.py output meter --write                   # 机验率 / 功能面，并重签基线
```

判定口径与门禁的关系：`verify.sh` 的 **check32 `output_forms` 子扫描**做三件事——
形态清单自洽、包级产出面逐件校验（形态 / 档位 / schema / 双源 / T4 复算）、
机验率不低于基线。**不新增 check 序号**（ADR-0002 门禁不注水）。

## 本仓现在的机验产出面

| 包 | 产出面 | 机验面 | 功能面（T4） | 机验率 |
|---|---|---|---|---|
| AI系统域包 | 6（契约 2 / 数据 1 / 可复算 1 / 图示 2） | 6 | 1 | 0.8571 |
| 量化金融域包 | 8（契约 2 / 数据 2 / 可复算 1 / 图表 2 / 图示 1） | 8 | 1 | 0.6667 |

具体地：

- **量化金融域包**：口径注册表 `outputs/QUANT_METRICS.json`（与资产 §2–§4 双源一致；
  每个 `engine` 必须在 `core/quant_metrics.py` 真实存在——**宣称≠实现即 FAIL**）；
  绩效报告 `outputs/PERFORMANCE_REPORT.json`（由 `outputs/samples/EQUITY_CURVE.csv`
  重算，check32 逐字段比对）；净值 / 回撤图（Vega-Lite，由数据生成）；口径声明依赖图（Mermaid）。
- **AI系统域包**：系统卡 `outputs/SYSTEM_CARD.json`（用途 / 限制 / 数据 / 评测 / 人审 /
  NIST AI RMF 字段映射 / **不宣称**清单）；闭包产物 `outputs/CONCEPT_CLOSURE.json`
  （由概念图重算 C42 闭包与全图装载序）；概念图两形态（Mermaid / GraphML）。

## 哪些没做（边界，如实记档）

- 形态清单里 **61 条 `planned` / 11 条 `deferred` / 6 条 `unfit`** 是**明确未做**的：
  每条在清单里写清触发条件或前置（如 Parquet/Arrow 前置是二进制依赖，与 core 零依赖红线冲突；
  OData/WSDL/容器镜像属不适面）。**未做就是未做**，不写成「已支持」。
- 自带 JSON Schema 校验器是**子集**（`_SUPPORTED`）：`if/then/else`、`unevaluatedProperties`、
  `$dynamicRef`、远程 `$ref` 等**显式上报为 unsupported**——「不支持」绝不等价「通过」。
  交叉校验可用软依赖 `jsonschema`（`scripts/check_interop_schemas.py` 同款机制），缺失即跳过并说明。
- 6 条形态的规范入口本机不可达（ISO 付费墙 403 / 限流 429 / 链接漂移 404），
  清单按 `evidence.reachable=false` 记档，**不假装可达**。
- 机验率是**本仓口径的覆盖率**（机验产出面 /（机验产出面 + 散文资产）），不是「内容质量分」；
  它挡的是**回退**（新增产出又退回散文），不是宣称打磨完成。
