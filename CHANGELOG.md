# Changelog

## [2.11.0] - 未发布

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
