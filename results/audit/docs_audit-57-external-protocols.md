---
id: AUD-0009
title: 外部协议清单吸收波（162 条 → 逐条实证 → 净吸收 15 条归并 10 项机制）——编码卫生 / 互操作导出 / 文档命令面 / JSON-RPC 结构约束
date: 2026-09-21
scope: 作者指示的七项任务（NF 深析 / 外部协议清单 ≥100 条 / 逐条与 NF 对比 / 转成可吸收项 / 直接执行吸收 / 每条抽象可相似点 / 连续运行）；本件只对本波落地的四项门禁新面与清单判定分布作实证建档
verdict: pass
auditor: 本轮执行者
subjects:
  - verify.sh:8badf11a8c1e52d6338d5dae26df0e4390ea05c6fed3d1d83f84afec6276f234
  - .gitattributes:f6fb4175293c85a259d4c60564352c811dded74210c1ad54ec4bfc0376a4188a
  - desktop/src/core/text_hygiene.py:44f22d14c2ab470a2d30a5484b484a81c57baaf3111a5a1fcec0005a9d0cdeae
  - desktop/src/core/interop_export.py:98be4b86f7b8a83359ee3f894e0b11531cd992a51dc25cb9aa887c6321dcbe93
  - desktop/src/core/mcp_runtime.py:104e72d90c207132a1479297ba5853a50e525e65f17ff12c08524c9520708751
  - desktop/src/core/prose_lint.py:680715a34a1c43687a87113edc323c1491ab7577f99352bda4b30633b064b15c
  - desktop/src/core/license_gate.py:602d29e257651283e5d51cd173568878ab7cb4daa385a79fd79e53cd37ff3889
  - desktop/src/core/doc_hygiene.py:2b0acc2498874f2d37ca7d7e51b8f89d17c1bd5171e9532e75667c58d9d5f5fb
  - desktop/src/core/endpoint.py:6d09b2efc63aa5d863093871d5ffdbdb19627e5a83c439fbc00fafde9fd4cf87
  - desktop/src/core/purity_scan.py:223ccbb2fc52c4a15362e1eff06b97341fa00de2094c97f93409d5bbadcb676a
  - scripts/nf.py:c3751c8d95eeb66abdb6eff45af3eb90f5fbbf578f35066d7440e0930bcdfcd7
  - scripts/check_external_links.py:4167e9e27e453a9f495870c9a69820d9c8886023cfd2d10d4457ae3686f15515
  - scripts/check_interop_schemas.py:6cae41b5247e8ea594b3825ff61bc3b9186caf21c170bc122d31861d30974c74
  - results/interop-schema-validation.md:e2546c6407416b61912ac351d14d20c171167e36be4d4d3461f6c2fceb56c0c9
  - docs/interop.md:f884a0533ed89aae8c83a2a44da491afb334c083dc05051158ac3a91e88e4f5c
  - docs/text-hygiene.md:36edf35f60bc669192443a8c16a4bcdc7c22408270fff5ea15308a16a756f986
  - docs/endpoint.md:4da6d07f9d0ed0a7166c028b1a4070a370f2edc9e70e700cce03c3d38b4e930f
  - docs/mcp.md:fb8c5a30492705190e879e7f0124ecd01d95c4d7a099980ccbf8c1976acb9ca5
  - llms.txt:226450a3a0c88846032aed01ac216c20cb400f654bff68c79f47c92a14b16ffe
---

> 签收位：本件**未填 `accepted_by`/`accepted_at`**——验收签收属作者动作，执行者不自签。
> subjects = 本波承重件十九件（门禁 / EOL 声明 / 编码卫生 / 互操作导出 / MCP 硬化与帧纪律 / 文档命令面 / 许可表达式门 / 文档分类表 / 端点幂等判据 / sink 登记自洽 / CLI 入口 / 外链巡检重试面 / **外部 schema 校验工具与其取证报告** / 四份对外文档 / 机器入口）；任一件再改，本件结论即失效须重审。

## 一、开工依据（内部差距实证，不含外部论据）

按 STRATEGY §3.3（立项理由不得引用外部、质量论证不得引用外部背书），本波四条开项理由**全部来自仓内实证**（探针脚本 `.rivet/scratch/probe57*.py`，只读）：

1. **承载编码无判据**：全仓文本件/JSON 件此前无 BOM、行尾、键唯一、标识面同形四项检查——实测工作区 6 件被 Windows 侧写成 CRLF（`.gitignore` / `05_资产库/provenance.json` / 两件用户自定义资产 / 两件 E1 外部验证样本），而 `git hash-object` 与 `git rev-parse HEAD:` 逐件比对显示 **git 侧 blob 全为 LF**（漂移只在工作区）；另实测 `protocol/**` 存在重复键的可能性无法被任何门禁看见（无判据即为盲区）。
2. **声明面厚、导出面缺**：8 条服务端点契约 + 43 条事件载荷 + 48 条协议层回执 + 依赖登记面（hard/soft import）都是 NF 形状的 JSON，**无一条能直接喂给 OpenAPI/AsyncAPI/in-toto/SPDX 工具链**（外部读者只能读 NF 自述形状）。
3. **文档命令面无判据**：`driver.json` 只锚住三个指令档；README / ROUTES / 07 导航 / `docs/**` 里写的 `nf <子命令>` 写错时，门禁一条都不会红。
4. **协议边角条款无判据**：JSON-RPC 2.0 §4.2（params 必须结构化）与 §5（id 可判定须回显）在 MCP 运行时**静默放行**——实测 `params="raw"`、`params=[1]`、`id={...}` 三种请求全部按成功返回（错误请求被当成合法请求）。

## 二、清单与判定（162 条）

采集面 = GitHub 标准/规范仓与 awesome 索引 + 搜索引擎检索 + 标准组织公开目录（IETF / W3C / OASIS / ISO-IEC / Unicode / OpenSSF / SPDX / in-toto / CloudEvents 等）。**纪律声明**：外部标准不构成立项理由（禁令一），判定只认仓内实证；逐条台账（含每条的可相似点抽象）留内部档案 `57`，公开侧只落结果。

| 判定 | 条数 | 处置 |
|---|---|---|
| 已具备（不重做） | 74 | 写出 NF 侧实证件（协议件 / core 模块 / check 号），零改动 |
| 部分覆盖 | 18 | 主干已覆盖、边角未落；其中 23 条转成本波吸收 |
| 净吸收已落地 | 26 | 归并 20 项机制（第一轮 10 + 第二轮 4 + 第三轮 2 + 第四轮 4，见 §三） |
| 挂账候选 | 6 | 逐条写明触发条件（透明日志 / CycloneDX / VC 凭证 / C2PA / CID 寻址 / 内容分级——**幂等键、CWE、A2A 已分别由第二/三轮收掉**） |
| 不适面剔除 | 38 | 需运行时、网络服务或模型通道，或与「不产没人消费的东西」冲突（含以外部框架作判据的条目） |

## 三、本波交付（四项机制 + 一个入口 + 两份文档）

| 类 | 件 | 要点 |
|---|---|---|
| 机制 | `core/text_hygiene.py` + check33 第 9 面 | RFC 3629 / RFC 8259 §4 / RFC 7493 / UAX #15 / UTS #39 五条判据一次落地：UTF-8 严格可解码、无 BOM、行尾 LF、JSON 键唯一、标识面 NFC + 字符集（ASCII + CJK 汉字 + `$` 保留键前缀）；每条违规带修复指引 |
| 机制 | 仓库根 `.gitattributes` | `* text=auto eol=lf` + 二进制面显式声明（属性优先于 `core.autocrlf`，任何平台检出即 LF）；同门判据「声明在位」——EOL 纪律须有落点 |
| 机制 | `core/interop_export.py` + check33 第 10 面 | 纯派生四件：OpenAPI 3.1（8 端点 + NfError + RFC 9457 映射）、AsyncAPI 3.0（43 通道 + CloudEvents 属性）、in-toto Statement v1（48 subject + sha256）、SPDX 2.3 SBOM（4 包）；门禁判覆盖完整 + 形状合法 + 两次渲染逐字节一致 + 真源缺失 fail-closed |
| 机制 | `prose_lint.command_face` + check33 第 12 面 | 文档命令面 ↔ CLI 注册表 / MCP `TOOL_DEFS` 一致性；只判「当作命令呈现」的片段（行内代码 + 围栏块），不误伤散文 |
| 机制 | `core/mcp_runtime.py` 硬化 + check33 第 11 面 | JSON-RPC 2.0 §4.2：params 原始类型 → `-32600`、数组 → `-32602`；§4：id 须字符串/数字/null；§5：id 可判定则回显（`_err_at`） |
| 入口 | `scripts/nf.py interop`（`--list/--check/--kind/--out`） | 四种导出形状统一入口；`--check` 走门禁 |
| 文档 | `docs/interop.md`（how-to）· `docs/text-hygiene.md`（reference） | 入 `doc_hygiene` 三表（DOC_KINDS / REQUIRED_DOCS / INSTRUCTION_DOCS），头部标记与「最后更新」位齐 |
| 机制（第二轮） | `mcp_runtime.encode_message` + check33 第 13 面 | stdio 帧纪律（NDJSON 口径）：一条消息一行 + `U+2028`/`U+2029`/`U+0085` 行边界陷阱转义 + 通知不写行 |
| 机制（第二轮） | `protocol/endpoint_contract.json` 幂等面 + `endpoint.scan` 判据 | RFC 9110 §9.2.2：默认幂等 + `idempotency_exceptions`（`bench.evaluate` → 幂等键 required）；未声明幂等语义即 FAIL；派生面 `x-nf-idempotency` |
| 机制（第二轮） | `purity_scan` R6 自洽面 | 每条 sink 带 CWE 对齐（CWE-78/95/470/502）+ `SINK_ALLOW` 放行键须指向已登记 sink |
| 机制（第二轮） | `scripts/check_external_links.py` 退避重试 | `is_transient` / `retry_after_seconds` / `probe_with_retry`（只对瞬态重试、退避翻倍、尊重 Retry-After、4xx 一次定性）+ `--retries/--backoff` |
| 机制（第三轮） | `interop_export.slsa_provenance`（`nf interop --kind slsa`） | SLSA Provenance v1：本地门禁口径（`buildType` 自定义型别 + 版本头/基线句作外部参数 + 48 subject）；**「不构成 SLSA 等级声明」注记为门禁判据** |

> **自审发现并当场修掉的真缺陷（记档）**：SLSA 派生面首版把基线句读自 `protocol/score_baseline.json`——
> 该文件只有 `score/signals/metrics`，**没有 check 数 / PASS 数**，于是产出 `check1-0 PASS=0` 的
> 假基线（"看起来有条目、其实是 0"）。根因 = 参数源选错（拿了分数台账当基线真源）。
> 修法：改用 `core.quality_baseline.EXPECTED_CHECKS/EXPECTED_PASS`（基线句真源），
> 并新增门禁判据——基线句非法、为 0、或与 `quality_baseline` 期望值不一致即 FAIL。
> 实测修正后为 `check1-37 PASS=61`；`test_interop_export` 增断言钉住两处同源。
| 机制（第三轮） | `interop_export.a2a_agent_card`（`nf interop --kind a2a`） | A2A Agent Card：skills = 端点契约投影（8 条），`streaming` 由契约推出，未实装须显式注记 |
| 机制（第三轮） | `mcp_runtime.uri_template_issue` / `template_matches` + check33 第 13 面扩 | RFC 6570 一级子集 + **模板⇄真实 uri 覆盖**（5 模板合法、390 条真实 uri 零未覆盖） |
| 机制（第四轮） | `license_gate.expression_issue` | SPDX 许可表达式词法判定（AND/OR/WITH/括号/`+`/LicenseRef + 运算符位置与缺操作数） |
| 机制（第四轮） | `text_hygiene.semver_issue` + 域包 version 面 | SemVer 2.0.0 词法（前导零 / 缺段 / 空预发布段），7 个域包版本位在扫；资产自由槽版本边界写明 |
| 机制（第四轮） | `text_hygiene.VALUE_SOURCES` + `_resolve` | 标识**值**面词法（registry / vocabularies / provenance，95 个值）——堵「键查值不查」的同形后门 |
| 机制（第四轮） | `interop_export.prov_document`（`nf interop --kind prov`） | PROV-O 图：59 节点（53 实体 / 3 活动 / 3 代理），空面如实为空；门禁判节点唯一 + 关系在册 + 资产全覆盖 |
| 机制（第四轮收口） | `scripts/check_interop_schemas.py` + `results/interop-schema-validation.md` | **外部权威校验**（非门禁·联网）：openapi / asyncapi / sbom 三面过官方 meta-schema；slsa / intoto / a2a 官方无 JSON Schema → `no-schema` 如实记；prov 本机取不到 → `unavailable`。**外部校验抓出两处真缺陷并修复**：SBOM `created` 缺失（SPDX 2.3 必填）→ 取仓内声明日期最大值（非墙钟）；`documentComment` 不在词表 → 根级 `comment` |
| 测试 | 单测新增 59 例（总 940 例全绿） | 编码卫生 14 / 互操作 18 / 许可表达式 3 / 外部校验工具 5 / JSON-RPC 结构与帧纪律 7 / 文档命令面 3 / 端点幂等 1 / CWE 自洽 3 / 退避重试 3 / 资源模板 2 |

## 四、门禁与验收（实测）

| 判据 | 结果 |
|---|---|
| `bash verify.sh` | **PASS=61 · WARN=0 · FAIL=0**（check1-37 不变——语义全部并入 check33，符合 ADR-0002「门禁不注水」） |
| `python -m unittest discover -s desktop/tests -q` | **940 例全绿**（本波新增 59 例，分布见 §三末行） |
| 本波新模块覆盖率（`coverage` 实测） | `interop_export` 90% · `text_hygiene` 95% · `license_gate` 95%（合计 92%） |
| `python -m ruff check .` · `python -m compileall -q desktop/src scripts` | 零违规（All checks passed） |
| `nf doctor` | 16/16 通过（含「基线自描述一致 v2.27 · check1-37 PASS=61」） |
| `nf conformance` | conformant 27/27（报告已重写并重签） |
| `nf receipts` | 48 件逐条折叠到根，根与实时重算一致（`protocol/RECEIPTS.json` 重签） |
| `nf approve --verify` | 内容绑定批准有效（`protocol/approvals/protocol__conformance_report.json.json` 重批准） |
| `nf interop --check` | 绿（7 面：8 端点 / 43 通道 / 48 subject / 4 包 / 48 SLSA subject / 8 skills / 59 PROV 节点） |
| 编码卫生 | 580 文本件 / 65 JSON / 6634 键 · BOM 0 · CRLF 0 · 违规 0 |
| 文档命令面 | 64 文档 / 167 处命令提及 · 漂移 0（文档面含本波新增的两份对外文档） |

## 五、遗留与不宣称

1. **挂账 6 条**（透明日志 / CycloneDX / W3C VC / C2PA / CID 寻址 / 内容分级）——每条写明触发条件，不排期、不预设；幂等键、CWE 编码、A2A 卡片三条已分别由第二 / 第三轮收掉。
2. **导出面不入仓**：`nf interop` 输出走 stdout 或 `--out`，**不在 `protocol/generated/` 落盘**——落盘会扩张 `protocol/` 登记面（normative / 回执覆盖面）而无消费方；需要归档时由使用者显式 `--out`。
3. **行尾整改只做声明与判据**：未改任何文件内容（逐件 blob 哈希核验）；工作区漂移由 `.gitattributes` 属性在检出层消除。
4. **JSON-RPC 批量请求面**：仍按 `-32600` 拒绝（MCP 不要求批量；本运行时只做单消息），属**已知边界**而非缺口——若将来需要，按 §4 补数组应答语义。
5. **外部实测线仍封存**（STRATEGY §四封闭式发育期）：本波不含任何外部实测；E1/E2/E3 与 B1 通道维持发布后回填口径。
6. **清单数字以内部台账为准**：162 条逐条台账（含每条可相似点）留 `.rivet/private_archive/57_*`，公开仓只承载本件的判定分布与机制结论。
7. **采集面如实记档**：GitHub API 元数据（24 仓）+ RFC Editor 官方索引（8995 条解析，逐编号核对 28 条 RFC 标题）+ 规范原文取样落 `.rivet/private_archive/57_采集回执_GitHub与检索.md`；本轮**检索通道**（DuckDuckGo HTML/Lite、Wikipedia API）在本机网络口径下超时，标准在场性改由 GitHub 元数据与 RFC 原文回执承担——**不把「搜不到」当「不存在」**（见采集回执 §三口径说明）。
8. **退避重试仍是「非门禁工具面」**：外链巡检不进 verify 基线（STRATEGY 的静态可复现红线），重试只提升巡检的定性准确度，不改变门禁口径。
9. **本机网络口径实测（如实记）**：外链巡检 `--fetch` 在**本机**探测 20 条取样 → 失败 11 条，失败集中在 `github.com` / `raw.githubusercontent.com`（`URLError` / `TimeoutError`），而 `api.github.com` 与 `spec.openapis.org` / `rfc-editor.org` 可达——即**本机出口对部分 GitHub 域名不通**，不是链接死了（同一批 URL 在 CI 侧由 weekly workflow 复核）。附带一条自曝：**默认重试（2 次）会让不可达域的探测最坏耗时 ≈ 单条 34s**（10s 超时 ×3 + 退避 1.5/3s），30 条取样本机跑了 9 分钟仍未收口——受限网络下建议 `--retries 0 --timeout 4`（已实测 20 条 77s 收口）。这条写在这里而不是写进工具默认值：**重试是给瞬态故障的**，把默认值调小会削弱它对抖动的价值；取舍交给调用方。
