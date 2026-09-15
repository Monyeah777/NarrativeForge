# Changelog

## [2.12.0] - 未发布

- 内容建模三件（第七波，不新增 check——语义并入一致性报告与既有门禁）：**词表登记册**（`protocol/vocabularies.json`：12 个概念方案集中声明，每个用 `probe` 指回真源（`python_attr` / `json_path` / `literal`）逐项比对——**真源变了册子没跟即 FAIL**；含 alias 撞车、值重复、值少于两个等判据）· **规范件与说明件之分**（`protocol/normative.json`：28 件规范件 + 177 件说明件；规范件必须**有主**——被回执锚定或显式 `covered_by`，**说明件不得被回执锚定**，两名单交集为空）· **数据契约登记**（`protocol/data_contracts.json`：10 个机读件各写明 `quality_rule`（须解析到真实 `checkN` 或 `assertion:<id>`）/ `owner` / `freshness` / `consumers`——**指不出 quality_rule 的契约不许登记**）。机器面 `nf model [vocab|normative|contracts]`。同波：一致性报告 18 → **19 契约**、协议层回执 32 → **35 件**、新增 `docs/modeling.md`（入 doc_hygiene）。

- 内容类型学吸收（P0 四件，不新增 check——语义并入既有门禁）：**四型写法判据**（`doc_hygiene.KIND_RULES`：类型不只是标签，还是写法约束——how-to 须有可执行命令块、reference 须有词表/字段表、tutorial 须有步骤序列、explanation 须有为什么/权衡；存量按 **WARN** 挂账，`nf lint --kinds` 可数）· **断言数据化**（`protocol/assertions.json` + `core/assertions.py` + `nf assertions`：Schematron 式 patterns→rules→assertions，**kind 为封闭集**（`regex_absent` / `regex_present` / `count_at_least` / `json_value`），新增规则 = 加一行数据；每条必须有 `fix`；只搬形状类断言，不新增语义政策，不自造 DSL。一致性报告新增 `assertions` 契约）· **派生三问**（`protocol/EXTENSION.md`：基类是什么 / 新增面是什么 / 旧消费方可读性，并入 `check30` 判据词表）· **唯一来源复用**（`knowledge.verify_reuse`：条目 `id` 唯一且等于文件名、`ALIAS.md` 小写键唯一且指向在册条目、**任意两件全文摘要不得相同**；并入 check37）。同波：一致性报告 17 → **18 契约**、协议层回执 31 → **32 件**、新增 `docs/assertions.md`（入 doc_hygiene）。

- 知识层续波（不新增 check——语义并入 check37，门禁形状不变）：**频次自动采集**（`nf knowledge frequency --trace <file> [--write]`：从 trace 复算源使用频次落 `protocol/knowledge_usage.json`；消化记录一旦声明 `reuse_count` 必须与台账一致，**手写频次即 FAIL**）· **复核工作流**（`nf knowledge transform add|promote`：登记 → 转正两段式，转正须齐三档证据 + 复核双签；两条路径**先校验后写盘**，非法入参不落脏记录）· **认知裁剪执行接线**（`visible_ids(clearance)`：秩 public ⊂ internal ⊂ restricted，`nf knowledge order --as` 与 MCP 工具 `knowledge_order` 均不返回越权源）· **MCP 工具面**（新增只读工具 `knowledge_order`）· **公开件卫生**（清掉 `.github/scripts/library_ingest.py` / `docs/ai-menu.md` / `CONTRIBUTING.md` 中引用内部档案路径的表述；`nf conformance` 帮助文案不再写死契约数）。基线不变：verify v2.27，check1-37，PASS=61。

- 知识层收口（check37）：**双源知识声明**（`protocol/knowledge_sources.json`：权威分层 `contract`/`reference`、查询有序 `query_order`、时效策略、可见性，**reference 级必须标注来源**、`locator` 必须指向真实件防纸面源）· **消化可追溯**（`protocol/transform_log.json`：源 ↔ 产物 `digest` 绑定，产物一改记录即失效；转正须齐三档证据 + 复核双签）· **晋升规则**（缺证据一律 `stay-reference`，不许用推测填）· **认知裁剪**（`cognition.filter_module` 必须指向在册模块）· **知识层巡检**（悬空引用 / 孤儿条目 FAIL，时效缺失 WARN）· 机器面 `nf knowledge [order|lint|transform]`。同波：一致性报告扩到 **17/17 契约**（增 `knowledge-sources`）、协议层回执覆盖面 **28 → 30 件**。基线 verify v2.27，check1-37，PASS=61。

## [2.11.0] - 未发布

- 治理面收口（check36）：**一致性声明**（`protocol/CONFORMANCE.md`：`## 声明` 版本表逐条与真源比对 + `## 范围` 白名单 + `## 排除` 显式清单，scope∩排除=∅，声明了真源没有的规范项即 FAIL；`nf conformance` 增 `declaration` 契约）· **协议件 RFC 版本史**（01/02/06/07 头部机器可读 RFC 头：编号/Category/Date/Status/Supersedes/Superseded by；`nf rfc` + `protocol/rfc_index.json`，日期须等于「最后更新」、链可解析不成环）· **指令档机器面路由**（`protocol/driver.json` + 组装指令包 / `AI_ROUTING.md` / `docs/ai-menu.md` 头部 `DRIVER OVERRIDE` 块：有 MCP 实现就走 MCP，派发失败即停、**禁止回退成文本步骤**；工具名与 `mcp_runtime.TOOL_DEFS` 逐名一致）· **实践包品类**（`patterns/<id>/PATTERN.md` frontmatter 为真源 + `patterns/INDEX.md` 投影；`applies_to`/`evidence` 须在仓库内可证；`nf patterns ls/show/for/verify/reindex` + MCP `pattern_read` 工具 + `nf://repo/pattern/{id}` 资源）· **执行结果跑分台**（`nf bench run/compare/report`：对任意产物做五维确定性评分，用例下限判级，多跑出逐维均值/极差/相对最佳回落——外部实测的容器）· **服务端点契约**（`protocol/endpoint_contract.json`，`status: proposed`：8 端点映射到现存 CLI 子命令或 MCP 工具，`maps_to` 不许指向空气；`nf endpoint`）。同波：一致性报告扩到 **16/16 契约**、协议层回执覆盖面 24 → **28 件**（治理面机读件入锚）、`check36` 加入 段 C。基线 verify v2.26，check1-36，PASS=59。
- 新增 `machine_contract.world_model`：JEPA-inspired 确定性抽象状态契约，含 M00 slot 注册表绑定、M00 锚定独立体检、具体状态映射、机器 checks、`WorldModelRuntime` 重放、SHA-256 轨迹指纹与 `nf worldmodel --run [--state STATE.json] [--json]`（M50 首战 + check32 硬门）。
- 吸收七面随波收口（check33）：MCP 运行时升级为 dual-era（modern `2026-07-28` 每请求 `_meta` 版本协商 + legacy `initialize` 并存 + `server/discover` + `-32022`）、内容 attestation 三级信任（`nf attest`：digest_only / hmac-sha256 / sigstore 外挂锚，缺锚 fail-closed）、基线相对回归评分（`nf score` + `protocol/score_baseline.json`）、机械修复与编辑器面（`nf lint --fix` / `nf lsp`）、正文 lint（`nf lint --prose`）、图书馆许可证门（`nf license` + INDEX 许可列）、遥测 semconv 映射（`nf telemetry`）。
- 云端图书馆机器面收口（check34）：条目 frontmatter 升为**单一真相源**（OKF v0.2 借鉴：`id/type/title/description/license/sources/generated/verified/status/stale_after/attestation`）、INDEX 生成区与 ALIAS 全量投影重生成（I5）、条目生命周期（`active/deprecated/superseded` + 取代链）、正文级馆藏检索（倒排索引 + 中文子串 + 排序，`nf library search`）、MCP 取用面补齐（`library_read` 工具 + `nf://repo/library/{id}` 资源，大小写不敏感）、`llms.txt` 机器入口清单（对齐 llms.txt v2）、文档四型分类（Diátaxis 借鉴）；两个入库机器人（GitHub/Gitee）改写 frontmatter 并改调投影重建。
- 深化面收口（check35，机制借鉴 Pipelex / MCOP-Framework / Specadia）：**管线抽象执行**（`nf pipeline dryrun`：不调模型跑一遍声明 → GraphSpec，hard 缺陷与 advisory 分列，全仓 8 管线零 hard）、**馆藏回执单根**（`nf library receipts`：RFC 6962 域分隔 Merkle + 逐条 O(log n) inclusion proof；读者侧 `--entry <编号>` 本地折叠自验，`llms.txt` 载折叠规则）、**模块边界冻结**（`nf module signature`：边界摘要基线，漂移即 FAIL 直到显式重签）、**内容绑定批准记录**（`nf approve`：对象内容改动即失效）、**一致性报告工件**（`nf conformance`：10 契约 → Merkle 根 + `conformant` verdict，含公开导出面泄漏审计）、**I/O 类型面**（`machine_contract.io_types` 字段级新增 + `nf module types`：确定性推导、可证不匹配 FAIL、未收窄记覆盖缺口）、**无效语料 + golden 修复对**（`fixtures/fixes/fix_cases.json` + `test_invalid_corpus.py`）。基线 verify v2.25，check1-35，PASS=57。
- 深化面续波（同类机制继续收口）：**社区域包机读块 L0→L1/L2 retro-fit**（21 件模块由人读引用块 + 正文事件契约**投影**出 `machine_contract`，发布/订阅取全集；全库 **44/44** 模块均有机器契约，L0 归零）、**类型面落地**（`io_types` + `nf module types`，`nf module contract` 提供 retro-fit 入口）、**6 个新事件登记**（`spell_cast`/`romance_state_change`/`social_feed_event`/`phone_call_event`/`group_chat_event`/`faction_event`，declared 起步）、**dry-run 判决修正**（同层依赖与跨包依赖改 advisory，仅「提供方在更后层」判 hard）、**签名锚入馆藏**（`nf library attest --key-file` 落 `anchor_scheme/anchor_mac/anchor_key_id`；锚字段排除出自指摘要，落锚不改变全馆根；缺钥只 WARN 不判死）、**订阅侧孤儿面收敛**（retro-fit 让发布方可见，closure_scan 孤儿 5+ → 0）。基线 verify v2.25，check1-35，PASS=57。
- 深化面第三波：**outputs 证据回填**（21 件模块由**已登记事件载荷**补出 `outputs`，112 个 token；无证据的 17 件如实留空——不猜；类型覆盖率 21/66 → **68/178 字段**）、**ssh-sig 非对称签名锚**（OpenSSH `ssh-keygen -Y sign`，读者仅需 `ssh-keygen` + allowed_signers 即可验；签名载荷按字节喂 stdin——Windows 文本模式会翻 `\r\n` 导致验签失败，已修）、**读者侧独立验证器** `scripts/nf_verify.py`（纯标准库、零 NF 依赖，自算规范摘要/叶/折叠 proof + 按需验锚；hmac/ssh/sigstore 三级，缺验证器一律 fail-closed）、**锚语义收紧**（落锚后内容被改 = FAIL，不再只是 WARN；重签自动刷新回执）、**回执带锚明细**（scheme/ns/identity/sig_file/fingerprint）。基线 verify v2.25，check1-35，PASS=57。

- 缺口收口波：**回执单根扩到协议层**（`nf receipts`：01–07/schema/baseline 24 件各带 inclusion proof）· **修掉一个真 bug**（inclusion proof 早期自顶向下、折叠自底向上 → n≥3 全部折叠不到根；馆藏只有 2 件把它掩盖了，现由 1–100 叶规模回归钉住）· **类型面收口**（正文载荷收割 `nf module types --harvest` + 不可推断类型进**积压台账** `--backlog`，104 项显式可数，不许无声增长）· **全仓事件背书门禁**（`nf events`：36 事件零未背书、9 条跨包可见，外部通道须 `protocol/external_events.json` 挂账）· **advisory 分类台账**（82 条分 3 类，可追踪收敛）· **300 件馆藏规模回归**（投影/检索/回执/读者工具/审计路径 <12 步）· **工程面补齐**（9 个新模块 docs 说明档并入 doc_hygiene；覆盖率 79%→85%；ruff 本地安装且 lint 全绿；MCP dual-era 真 stdio 端到端；LSP 编辑器配置样张；`nf approve` 首条记录）。基线 verify v2.25，check1-35，PASS=57。

## [2.10.0] - 2026-09-09

- 45 质量纵深与基础层 A 组收口；事件载荷注册、回合级执行、AI 通道内容与自组装落地。

## [2.9.0] - 2026-09-08

- STRATEGY 战略层建立；43 协议层元工具与 44 CLI/动态 drill/AI 通道随波发布。

## 历史版本

| 版本 | 日期 | 结果摘要 |
|---|---|---|
| v2.8.0 | 2026-09-08 | 41 质量编译 + 42 质量纵深随波收口 |
| v2.7.0 | 2026-09-07 | 无壳基础层整合发布 |
| v2.6.0 | 2026-09-06 | 端壳接线波收口 |
| v2.5.0 | 2026-09-06 | 协议 V2 与 MCP 运行时 |
| v2.4.0 | 2026-09-06 | 外部规范体检 |
| v2.3.0 | 2026-09-05 | 基础层深化首波 |
| v2.2.0 | 2026-09-05 | 外部吸收首波 |
| v2.1.0 | 2026-09-05 | 基础层深化 |
| v1.2.0-v2.0.x | 2026-09-05 | 导出层序列 |
| v1.1.0 | 2026-09-04 | 通用核心基础包 |
| v1.0.0 | 2026-09-04 | 全平台正式版 |
| v0.9.0 | 2026-09-04 | Android 同步门禁修复 |
| v0.8.0 | 2026-09-04 | 自定义模块组合 |
| v0.7.0 | 2026-09-04 | 自定义协议 |
| v0.6.0 | 2026-09-04 | 协议中转站 |
| v0.5.0 | 2026-09-04 | 优化版雏形 |

完整版本映射见 `VERSION-MATRIX.md`；过程性计划已内部归档。
