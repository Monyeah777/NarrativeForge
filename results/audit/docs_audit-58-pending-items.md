---
id: AUD-0010
title: 六条挂账全部收口 + 出口/会话面外部核验（CCV3 假 v3 与 MCP 可缓存结果两处真缺陷）
date: 2026-09-21
scope: 作者指令「遗留全部补上」——处置 AUD-0009 §五 列出的全部遗留：六条挂账候选（透明日志 / CycloneDX / W3C VC / C2PA / CID 寻址 / 内容分级）、导出面入仓、外链巡检网络口径、外部实测线中**本环境可执行**的格式与协议面核验
verdict: pass
auditor: 本轮执行者
subjects:
  - verify.sh:0e94959965c35d7d9bcc3008da5747eae26ce460ae5b30dfb8a8f4a14682f08b
  - desktop/src/core/transparency_log.py:ffb298d1a55611f03ee8dca1a57aa6148fd06bfaeb4cbd6a07dade279ebddd00
  - desktop/src/core/rating_gate.py:13f3a681d8fdbda1886bb7996d3cc2da609eac15dbf4455ac7b074d0920b6d10
  - desktop/src/core/interop_export.py:98be4b86f7b8a83359ee3f894e0b11531cd992a51dc25cb9aa887c6321dcbe93
  - desktop/src/core/ccv3_adapter.py:cb33b76eb4e3af332f73fceefd5ef8e7ed171d76cc4ee02327555f21bb5c9ca1
  - desktop/src/core/export_schema.py:3b80c1b772bb8309d918e461b4adcc80d1ce887aa69882f0cbb48c7bd7780e5b
  - desktop/src/core/mcp_runtime.py:104e72d90c207132a1479297ba5853a50e525e65f17ff12c08524c9520708751
  - desktop/src/core/import_adapter.py:5620194e56ce42b175e02f69d4bc6d03b99f35b43e5d38ab6c0d4aab9eaab333
  - desktop/src/core/library.py:ea04c30e07ccb3588057d9257ec27f5d051bf94ff6ebc0f2e45e37473d4b30f1
  - scripts/check_interop_schemas.py:6cae41b5247e8ea594b3825ff61bc3b9186caf21c170bc122d31861d30974c74
  - scripts/check_external_links.py:4167e9e27e453a9f495870c9a69820d9c8886023cfd2d10d4457ae3686f15515
  - library/intake.json:28288978a5c4dcbdcff5017bdac52a027f83ec2478f81034f39415c181190533
  - docs/external-validation-assets/E1_ccv3_sample_lightmix_P04_chara.json:528935dcf5be9caf69e25a88ec1637b64b8b725c51a539e1ede1d3a864dbcb45
  - results/interop-schema-validation.md:e2546c6407416b61912ac351d14d20c171167e36be4d4d3461f6c2fceb56c0c9
---

> 签收位：本件**未填 `accepted_by`/`accepted_at`**——验收签收属作者动作，执行者不自签。
> subjects = 本波承重件十五件（门禁 / 透明日志 / 分级门 / 互操作导出 / CCV3 出口与判据 / MCP 运行时 / 还原适配器 / 图书馆真源 / 两个外部核验工具 / 链生成物 / 声明件 / E1 样本 / 取证报告）。
> **口径修正（2026-09-22）**：subjects **不含派生物**——透明日志生成物每次重生成都会变，
> 绑进审计只会制造假失效；派生物由自己的门禁自证（check31 golden / check35 回执 / check33 入仓面逐字节）。

## 一、逐条处置（原挂账 6 条 → 全部落地）

| # | 原挂账（触发条件） | 本波处置 | 落点 | 实测 |
|---|---|---|---|---|
| 1 | 透明日志（SCITT/Rekor 类） | **实现为确定性哈希链**：`leaf=H(path‖digest)`、`chain[i]=H(chain[i-1]‖leaf[i])`，域分隔前缀防跨类型碰撞 | `core/transparency_log.py` + `nf transparency` + 生成物 `protocol/generated/receipt_chain.json`（check31 golden 校验） | 48 节 · 链头 `cc45f8d6…`；改回执不刷新即 FAIL、改生成物即 FAIL；**不可抵赖性显式不宣称**（写入 `boundary`，门禁判其在位） |
| 2 | CycloneDX SBOM | **与 SPDX 同源不同形**（都读依赖登记面），`serialNumber` 由声明摘要派生 | `interop_export.cyclonedx_doc` + `nf interop --kind cyclonedx` | **官方 meta-schema 通过**（首轮 FAIL：根级自定义键越界 → 移入 `metadata.properties`） |
| 3 | W3C VC（内容凭证） | **VC 2.0 形状 + 未签名状态机读化**（本仓签名走 ssh 外挂锚，套件不同） | `interop_export.vc_document` + `--kind vc` | `@context`/`type`/`issuer`/`validFrom`/`credentialSubject.receiptRoot` 齐；无 `proof` 时 `x-nf-proof-status` 必须在场（门禁判） |
| 4 | C2PA 内容凭证 | **JSON 清单形状**（`claim_generator` + `c2pa.hash.data` 硬绑定 + `c2pa.actions`），封装/签名状态机读化 | `interop_export.c2pa_manifest` + `--kind c2pa` | 断言标签齐 + sha256 硬绑定；`x-nf-package-status` 明写「未封装（无 JUMBF/CBOR）、未签名（无 X.509）」 |
| 5 | CID 内容寻址 | **CIDv1（multibase base32 / raw codec 0x71 / sha2-256）**，纯标准库实现 | `interop_export.cid_index` + `--kind cid` | **multiformats 已知向量自校**：`sha256("")` → `bafyreihdwdcefgh4dqkjv67uzcmw7ojee6xedzdetojuzjevtenxquvyku`；48 条回执各得 CID |
| 6 | 内容分级 | **声明驱动**：词表真源 = `library/intake.json: rating.vocabulary`；每件馆藏 frontmatter 声明 `rating`，投影到登记表新列 | `core/rating_gate.py` + `library.py:render_index_block`（分级列）+ 三件馆藏补 `rating` + check34 第 5b 面 | 馆藏 3 件（general×2 / teen×1）· 词表 general/teen/mature/unrated · 缺字段即 FAIL；入库闸门 gate 列表同批加 `rating_warn` |

## 二、其余三项遗留

| 遗留 | 处置 |
|---|---|
| 导出面不入仓（只 stdout/--out） | **补上入仓面**：`nf interop --all --out results/interop` 落 **11 面**派生投影；check33 第 14 面断言「入仓面 == 实时派生」**逐字节**（投影不是真源，改声明件后重跑） |
| 本机网络实测（11/20 失败、重试最坏 ≈34s/条） | **补上工具侧对策**：域级熔断（`--breaker`，默认连续 3 次失败即跳过该域）+ 时间预算（`--max-seconds`），跳过项在报告里可见（`skipped` + `tripped_hosts`）；实测 20 条取样由「9 分钟未收口」变为 **27s 收口**（失败 6 / 跳过 28） |
| 外部实测线仍封存 | **补齐本环境可执行的部分**（GUI 级装载仍属用户侧，如实不宣称）：① **E1 出口面**：取 SillyTavern 写卡源码字面量核对 → 发现并修复「**假 v3**」真缺陷（见 §三）；② **E3 会话面**：取 MCP 官方 `schema/2026-07-28/schema.json` 校验本仓运行时应答 → 发现并修复 list 三面缺 `resultType`/`ttlMs`/`cacheScope` |

## 三、外部核验驱动的两处真缺陷（同 AUD-0009 的取证纪律）

**缺陷 1 · CCV3「假 v3」**（出口层结构错）：旧样本/旧导出只有顶层 v2 字段 + `spec`/`spec_version` 两个头，**没有 `data` 块**；而 SillyTavern 自身写卡逻辑（`src/character-card-parser.js` 的 `write()`）把 v3 内容放在 `data` 内（顶层仅向后兼容）。内部判据只校自述 schema，所以从未红过。
修法：`ccv3_adapter` 输出 **`data`（权威位）+ 顶层 v2 镜像（逐字段同源）**；`export_schema` 判据升级（`data` 必填 + `character_book` 在 `data` 内 + 镜像一致）；`import_adapter` 还原时优先读 `data`（兼容旧形状）；E1 样本按真实导出命令重生成，并加 `docs/external-validation-assets/README.md` 记录取证链。

**缺陷 2 · MCP 可缓存结果缺三键**（协议面结构错）：官方 schema 的 `CacheableResult.required = [cacheScope, resultType, ttlMs]`，本仓只在 `server/discover` 给了这三个键，`resources/list` / `tools/list` / `prompts/list`（与 `resources/templates/list`）都缺 → 官方 schema 判 FAIL。
修法：`mcp_runtime._cacheable()` 统一补齐；单测钉住五面必带三键；复验 4 方法全绿。

## 四、门禁与验收

| 判据 | 结果 |
|---|---|
| `bash verify.sh` | **PASS=61 · WARN=0 · FAIL=0**（check1-37 不变；语义并入 check31 golden / check33 / check34） |
| `python -m unittest discover -s desktop/tests -q` | **961 例全绿**（本波 +21 例：透明日志 7 / 分级 5 / 互操作与入仓 4 / 外链熔断与预算 3 / MCP 可缓存 1 / CCV3 v3 形状 1） |
| `python -m ruff check .` · `python -m compileall -q desktop/src scripts` | 零违规 |
| 编码卫生（含新入仓的 11 面派生物） | 606 文本件 / 77 JSON / 9752 键 · 零违规（判据补 `{}` 与 `@`：URI 模板与 JSON-LD 保留键属外部标准既有形状） |
| `nf transparency` | 链自洽（48 节）· 在盘生成物一致 · 边界声明在位 |
| `nf interop --check` | 11 面一致（含入仓面逐字节） |
| `scripts/check_interop_schemas.py --fetch` | **13 面：官方 schema 通过 5（openapi / asyncapi / sbom / cyclonedx / mcp）+ 上游源码字面量通过 1（ccv3）+ no-schema 6 + unavailable 1** |
| `nf conformance` / `nf receipts` / `nf approve --verify` | conformant 27/27 · 回执折叠到根一致 · 批准有效 |
| `nf library verify --ssh-allowed-signers …` | 3 件在役 · WARN 0（NF-1 演示锚随内容变更用本地演示私钥重签，公钥与 allowed_signers 不变） |
| 外链巡检（域级熔断 + 时间预算） | 20 条取样 **27s 收口**：失败 6 / 跳过 28（跳过原因与 `tripped_hosts` 在报告里可见） |

## 五、遗留与不宣称（本波后）

1. **挂账 0 条**——AUD-0009 §五 的六条全部收口；**新的边界声明**取代新的挂账（写进产物而非留待办）：
   透明日志**不提供不可抵赖**（无第二署名方）、VC/C2PA **未签名/未封装**、资产槽版本面为自由槽版本。
2. **GUI 级外部实测仍未做**：SillyTavern 实际导入、宿主客户端装载属用户侧动作，本环境无法执行——
   本波只把「格式面/协议面」证到官方标准与上游源码口径，**不宣称装载成功**。
3. **prov 面 schema 取不到**：`www.w3.org/ns/prov.jsonld` 在本机返回 HTTP 300，记 `unavailable`，
   不据此判派生面不合规（口径已写进报告与工具）。
4. **分级是声明而非审核**：本门只判「声明在场且合规」，适龄判断责任仍在投稿人/消费方。
