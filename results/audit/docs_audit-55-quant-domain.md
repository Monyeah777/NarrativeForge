---
id: AUD-0007
title: 量化金融域包落盘 —— 第 3 个非叙事域、第二个「依赖闭包型」域包；机制复用与证据强度分级
date: 2026-09-20
scope: 作者指示新建域包（community 第 7 包）：口径协议（因子 / 回测与绩效）+ 概念前置图 + P08 管线 + 三要件登记；并回答两个内部问题——① 新收口的概念图判据与跨域求值器是否真通用 ② 第二个依赖闭包型域包的证据强度与 AI系统域包有何差异
verdict: pass
auditor: 本轮执行者
subjects:
  - community/量化金融域包/protocol.yaml:7ba7176c55538b2e57c70c3f0b58439601107ac9091b60495b86cc3996f7d83a
  - community/量化金融域包/assets/QUANT_GRAPH.md:331d63943effe51462440c41832202df3b8e6bb2553734472947ac77927e094c
  - community/量化金融域包/assets/QUANT_METRICS.md:fd85b5a871729e04b9c4026cc177e66875e35ca44cd098808cadbeb46f19ef06
  - community/量化金融域包/modules/M31_因子与信号口径.md:6404dd6093d63828e39b5ff69b9e289a54c50fed32e61e5c8e15832ef371fd00
  - community/量化金融域包/modules/M32_回测与绩效口径.md:30a5a15d78272ea2cc95418423fc356f053c58da313f2ab2cf33cb777b851d8e
  - community/量化金融域包/pipelines/P08_量化金融域装配流管线.md:2d1b47c702c1bce5418786643f3f0d9d89b9943c5ed39a0987433453d41d0e37
---

> 签收位：本件**未填 `accepted_by`/`accepted_at`**——验收签收属作者动作，执行者不自签。
> subjects = 本包**承重件**六件（协议声明 / 两件资产 / 两模块 / 管线）；任一件再改，本件结论即失效须重审。

## 一、立项依据（内部口径，不含外部论据）

- **指令来源**：作者在既有通道明确指示（外部输入 `wilsonfreitas.github.io/awesome-quant/` → 对应仓 `wilsonfreitas/awesome-quant`）——按 STRATEGY §四，新工程由作者指示开工；外部清单**不构成立项理由**（§3.3 禁令一）。
- **内部靶子（两条，均可证伪）**：
  1. **机制通用性**：刚收口的「概念图内部一致性门禁」（check32 的 `concept_graph` 子扫描）与「跨域只读求值器」（`scripts/ai_domain_closure.py --asset …`）声明为**通用**——第二个域包若不能直接用，声明即为虚标；
  2. **证据强度分级**：AI系统域包的边有课程讲序与论文锚点（可做「序违反边 = 0」交叉验证）；量化域的输入是**资源清单**（不提供前置关系），且该仓**未声明许可**——第二个依赖闭包型域包能否在**零外部结构传导**下成立。

## 二、输入勘验与内容纪律

| 面 | 实况 | 处置 |
|---|---|---|
| 输入仓形态 | 54 文件 / 1.63 MB：README 138 KB（19 类目）+ `site/` 站点 + `parse.py`（README → `projects.csv`）+ `tests/` + `AGENTS.md`/`CLAUDE.md` + `CONTRIBUTING.md` | 只读勘验 |
| 许可 | **顶层无 LICENSE / COPYING**；README 内无许可段（命中的 license 字样均为**条目自身**的许可） | **不传导其结构**（04 §3：借鉴须能注明出处与许可）——本包概念图与全部正文**自撰**，溯源只用 `domain-logic` / `inferred` |
| 机制对照（不吸收） | ① 清单 → 机读投影（`parse.py` → CSV）↔ NF `library/INDEX·ALIAS` 投影 + check34 投影一致断言（更机检）；② 自带 `AGENTS.md`/`CLAUDE.md` ↔ NF `AGENTS.md` + 06 执行协议；③ GitHub Pages 站点 ↔ 属壳 / 浏览面（按 L3 冻结与 P3 壳波挂账） | 逐条判「已具备 / 不适面 / 计划内」 |

## 三、交付（包体七件 + 登记三要件）

| # | 件 | 要点 |
|---|---|---|
| 1 | `protocol.yaml` | schema_version "2"；`pipeline: P08`；类内段 `量化金融:M31`/`M32`；独占类别 `量化金融`；core_only + 4 件核心配合；references=[]；assets.count=2 |
| 2 | `modules/M31_因子与信号口径.md` | P40；FactorSpec 五项（定义 / 标准化 / 极值 / 中性化基准 / 频率对齐）+ 跨因子对齐；publish `factor_spec_ready` / `factor_spec_conflict` |
| 3 | `modules/M32_回测与绩效口径.md` | P60；BacktestSpec（成本与成交假设 / 样本外切分 / 指标口径）+ **前视与存活偏差口径检查**；publish `backtest_spec_ready` / `backtest_spec_conflict`；subscribe M31 两事件 |
| 4 | `assets/QUANT_GRAPH.md` | 概念前置图：3 支 **27 概念** + 1 包外前置族 + 别名表 + 机读块（无 orderings——本图无来源序） |
| 5 | `assets/QUANT_METRICS.md` | 绩效与风控口径表：口径纪律四则 + 10 项指标定义（含常见口径事故）+ 成本与容量 4 项 + 两条偏差口径 |
| 6 | `pipelines/P08_量化金融域装配流管线.md` | 九层位沿用 + allowed_modules 固化 + 同层 default 无交集 |
| 7 | `README.md` | 人读速览（包名 / 管线 / 模块 / 资产 / 装载命令），与 protocol.yaml 双源一致 |
| 登记 | `02 §8.6` + registry `protocols[]` 第 7 条 | `nf register --apply` 写入；check14 ⑦ 元素级自证 |

## 四、两条内部靶子的实测结论

### 靶子 1：机制通用性 —— **成立（且不复制机制）**

| 检验 | 实测 |
|---|---|
| 概念图门禁跨域 | `core.concept_graph.scan('.')` 现覆盖**两个域包的两张图**（AI系统 47 + 量化金融 27 = **74 节点 / 133 边**），零 issue；注入环的负例在本资产上被抓（`test_quant_domain_package.QuantGraphTest`） |
| 跨域求值器 | `--asset community/量化金融域包/assets/QUANT_GRAPH.md` 直接可用：`closure(Q17)` = 15 概念 / `missing(Q17, L)` = 11 / `frontier(L)` 分支配（`--branch research` → Q09、Q10）/ 别名同解（`回测`→Q15、`TCA`→Q18） |
| 是否复制模块 | **未复制**：本包**不带闭包求值模块**，求值与体检均由通用面承担（工具横幅同步去域化，改为「概念前置闭包求值」） |
| 遗留缺口 | **模块级**闭包事件 / 数据槽（`concept_closure_ready` / `prereq_missing` / `PrereqState`）仍属 AI系统域包私有且绑定其 `CONCEPT_GRAPH` 键——第二域包若要「模块级」闭包，须先裁决**参数化图资产键**或**上提为通用机制**（挂账，见 §五） |

### 靶子 2：证据强度分级 —— **成立（并暴露一处判据面候选）**

- 本图在**零外部结构传导**下成立：27 概念 / 3 支 / 别名表 / 无环无悬空，边全部标 `domain-logic`（域内「产物 → 输入」可复算依赖，自撰可复核）。
- 与 AI系统域包相比少了**来源序**这一档证据（无课程 / 论文锚点 → 无 orderings、无「序违反边 = 0」交叉验证）——本包 README 与资产 §6 均**显式声明证据强度差异**，不假称同等。
- **判据面候选（新挂账）**：现行门禁只判「图是否健康」（结构 / 图论 / 别名 / 分支），**不判「边是否有足够证据」**——两张图在门禁面前等权。是否引入「证据强度分级声明」（如 `provenance_strength: external | domain-logic | inferred` 并要求资产如实标注、门禁只做**声明在场 + 分级与来源图例一致**）交作者裁决。

## 五、门禁与验收

| 判据 | 结果 |
|---|---|
| `bash verify.sh` | PASS=61 · WARN=0 · FAIL=0（check1-37 常驻；**不新增 check、不改 Schema**） |
| `python -m unittest discover -s desktop/tests -q` | 全绿（本波新增 14 例：包体四面一致 / 管线九层 / 事件登记与发布方唯一 / 图健康 / 跨域求值确定性 / 别名 / 两负例；另修正概念图门禁测试的仓库计数 1 图 → 2 图） |
| `python -m ruff check .` · `python -m compileall -q desktop/src scripts` | 零违规 |
| `nf pipeline dryrun --all` | **10 条管线**零 hard（P08 自身 10 advisory，均为官方核心跨包事件订阅，与既有管线同源） |
| `nf market --list` | 新包在列：**量化金融域包 v1.0.0（2 模块）**，徽章 community |
| `nf events` | 事件 **43**（39 + 本波 4）· 跨包 9 · 无发布方挂账 0 |
| 资产面 | `nf asset verify` 闭合（台账 3 · 托管资产 5 · 孤儿头 0）；密度 58 档 / 261 键（键/档 4.5 ≥ 基线 3.0） |
| 登记三要件 | protocol.yaml + `02 §8.6` 在册 + registry `protocols[]` 第 7 条（check14 ⑦ 元素级自证） |

## 六、遗留（挂账，交作者裁决）

1. **闭包能力的跨域形态**：模块级闭包（事件 + 数据槽）仍绑 AI系统域包及其 `CONCEPT_GRAPH` 键；第二域包目前靠通用只读面。选项：a) 保持现状（各域自带才算模块级能力）b) 将图资产键参数化后由 AI系统域包模块跨包消费（需 `references`）c) 上提为通用机制模块。
2. **证据强度的判据面**（本波新发现）：见 §四靶子 2。
3. **量化域内容纵深**：本包只交付「口径协议 + 概念前置」；域内可续补的资产（如因子词典、回测检查单、数据契约）留待按需。
4. 未做的：本波**不引入**输入仓的任何结构 / 文本（无许可）；也不把其类目映射成序（不造序）。

## 七、五维自评

1. **静态可核验**：verify 全绿；包体四面一致（协议 / 模块 / 资产 / registry）由 check14 ⑦ + 本包单测双覆盖。
2. **动态可执行**：`--asset` 跨域求值给出闭包 / 缺失 / 就绪清单；P08 装配零 hard；事件背书闭合。
3. **架构纯度**：**零机制复制**（不复制闭包算法）、零跨包引用、官方模块不搬移；输入仓结构零传导。
4. **资产密度**：2 件内容资产（概念图 27 概念 + 口径表 14 项），键/档 4.5（高于基线 3.0）。
5. **文档可执行性**：README（四步：装载 → 读图 → 取产物 → 事件）/ 模块（数据槽与事件契约）/ 资产（人读表 + 别名表 + 机读块）三处互指，命令可粘贴执行。

**差在哪**：① 边的证据强度弱于 AI系统域包（已显式声明，非隐瞒）；② 域内可续补资产未做（§六.3）；③ 模块级闭包的跨域形态未决（§六.1）。
