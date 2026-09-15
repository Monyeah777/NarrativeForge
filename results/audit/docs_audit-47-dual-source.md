# docs_audit · 47 双源知识层落地（knowledge）· 2026-09-15

> 性质：结果形态收口注记（计划内部消化，仅结论与状态）。
> 基线：verify v2.26 check1-36 PASS=59 → **v2.27 check1-37 PASS=61**。

## 一、本波补的内部差距（开工依据）

知识面三处（`library/` 内容层、`patterns/` 实践层、`protocol/` 契约层）**各自有真源声明**，
但没有一份件回答跨源问题：外部检索来的内容算不算 NF 事实、谁权威、多久失效。表现为四个具体空白：

1. 无「权威分层」声明：无法机检区分「NF 管辖内的事实」与「外部参考」；
2. 无「消化可追溯」记录：外部 → 本地若有转换，仓库里不强制留痕；
3. 无「查询顺序」判据：先查什么后查什么只存在于散文；
4. 时效与可见性散落（条目 `stale_after` 只在 library 层有）。

## 二、落地的件（结果形态）

| 件 | 形态 | 作用 |
|---|---|---|
| `protocol/knowledge_sources.json` | 声明（真源） | 权威分层 / 查询有序 / 时效 / 可见性 / 晋升规则 / 消化审核 / 认知裁剪 |
| `protocol/transform_log.json` | 记录 | 消化可追溯：源 → 产物用 digest 绑死，产物一改记录即失效 |
| `desktop/src/core/knowledge.py` | 门禁模块 | 上述两件的逐条可证校验 + 顺序解析 + 知识层巡检 |
| `nf knowledge [order\|lint\|transform]` | 机器面 | CLI 取用与自检 |
| `docs/knowledge.md` | 使用文档 | 操作指令式（指令类，入 doc_hygiene） |
| `check37` | 门禁 | 治理面之外的**知识层**聚合门 |

## 三、四条共存规矩 → 机检判据的映射

| 规矩 | 判据 | 是否可证 |
|---|---|---|
| 权威分层 | reference ⇒ `requires_source_label: true`；contract ⇒ `false` + local-compiled | 是 |
| 消化可追溯 | 记录 `from`/`to`/`digest` 三元绑定 + 转正须三档证据 + 双签 | 是 |
| 查询有序 | `query_order` 全集一致 + 合同级全部先于参考级 | 是 |
| Lint 常跑 | `nf knowledge lint`：悬空引用 / 孤儿条目 / 时效缺失（WARN）/ 溯源 / 声明 | 是（前四项 FAIL、时效 WARN） |

## 四、五维自评（本波）

| 维 | 水位 | 说明 |
|---|---|---|
| 静态可核验 | 升 | 新增 check37；声明、记录、顺序、时效全部机检；否定用例覆盖 9 类 |
| 动态可执行 | 平 | 本波不产新执行面；`nf knowledge order` 提供可执行顺序解析 |
| 架构纯度 | 升 | 三处分散声明收敛到一份跨源声明件；零第三方依赖未破 |
| 资产密度 | 平 | 未新增内容资产；新增 6 条知识源声明 |
| 文档可执行性 | 升 | `docs/knowledge.md` 指令式，入 doc_hygiene 四型（how-to） |

## 五、遗留（如实挂账）

1. 参考级源**当前 0 条已转正**（`entries: []`）——转正一旦发生必须留痕，本波只建通道。
2. `NF-WORLDCAMPUS-Monyeah777-1` 条目未声明 `stale_after` → 巡检记 **WARN**（不判死）。
3. 外挂混合检索（BM25 + 向量 + rerank）与图谱排序**未做**：前者越 core 红线，后者待排序契约细化。
4. MCP 工具面未加（仅 CLI + JSON）：留作下一增量。
5. 认知裁剪只声明了执行模块（M23）与适用源，**未**实现逐源裁剪执行——叙事域消费侧待接。

## 六、设计偏差

- v1 构想把 Transform / RAG 列为「候选升格模块层」；本波判定**不升模块层**（它们是契约面 + 数据面，
  不是 Pxx 层算子），依据是 M20 先例与模块层定义。此为对 v1 §5 的**判定性偏离**，非降级。
- v1 §7-3「时效策略」按 **声明式 TTL** 落地，未实现缓存逐出（NF 无运行时缓存层）。

## 七、续波（同日）：五件挂账全清

首波登记的五件挂账已逐条落地。**不新增 check**（不注水）：语义并入 check37，门禁形状不变，
故基线仍 `v2.27 · check1-37 · PASS=61`。

| 挂账 | 落地件 | 判据 |
|---|---|---|
| ① 频次自动采集 | `protocol/knowledge_usage.json` + `nf knowledge frequency --trace <file> [--write]` + `harvest_frequency`（支持 JSON 数组 / `{records:[…]}` / JSONL 三形态） | 台账 schema 合法、key 必须是在册源（防幽灵频次）、`total` 必须等于 counts 求和（手改痕迹）、消化记录 `reuse_count` 必须与台账一致——**手写频次即 FAIL** |
| ② 复核工作流 | `nf knowledge transform add`（登记 + 双签，未转正）/ `transform promote`（齐三档证据才可转正） | 转正缺证据档 / 缺复核人即拒；`from` 必须是已声明参考级源、`to` 必须真实件；**先校验后写盘**（拒绝路径实测零落盘） |
| ③ 认知裁剪执行接线 | `knowledge.visible_ids(clearance)` + `nf knowledge order --as` + `resolve_order(clearance=…)` | 秩 public ⊂ internal ⊂ restricted；clearance 达标的源才出现；check37 对三个 clearance 逐一断言「不返回越权源」 |
| ④ MCP 工具面 | `mcp_runtime` 只读工具 `knowledge_order`（入参 `clearance` 可选） | 工具名前缀与 TOOL_HANDLERS 同源；MCP 测试集更新 |
| ⑤ 公开件卫生 | `nf conformance` 帮助文案不再写死契约数；清掉 `.github/scripts/library_ingest.py` / `docs/ai-menu.md` / `CONTRIBUTING.md` 对内部档案路径的引用 | 帮助文案由「9 契约」改为「全部契约」（消除漂移类别，而非只改一处数字） |

**本续波新增判据（并入 check37）**：频率台账三类 FAIL（幽灵源 / 计数非法 / total 不符）+ 频次复算一致 +
三档 clearance 越权断言。

**五维水位变化（续波）**：静态可核验 ↑（频次与裁剪进入门禁）· 动态可执行 ↑（裁剪执行面接上 MCP 与 CLI）；
架构纯度 ↑（公开件内部路径引用清零）· 资产密度 =（无新内容资产）· 文档可执行性 ↑（`docs/knowledge.md` 补新命令与判据）。

**仍挂账（明确不做或待裁决）**：① 缓存逐出（NF 无运行时缓存层，重生成即刷新）；② 真实转正记录
（当前 `entries: []`——无真实消化发生，不造记录）；③ 外部混合检索与图谱排序（越 core 红线 / 待排序契约细化）；
④ `05_资产库/用户自定义/STYLE_DNA.md` 与 `protocol/demo_signers/README.md` 中的 `.rivet` 引用**有意保留**：
前者是内容资产（改动会扰动资产密度/厚度指标），后者是「私钥不公布、仅留本地」的安全说明。
