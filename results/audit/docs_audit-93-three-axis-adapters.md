---
id: AUD-0045
title: 三轴接入生产级适配第一波（IDE/编辑器面 + 文档门户常驻判据 + 对外文档对账）
date: 2026-10-07
scope: 作者指令「将 NF 与 IDE、文档平台与 LLM 框架集成达到生产级适配」。开工依据为内部差距实证（三轴只读审计：编辑器面 / site 文档门户面 / MCP-决策层-导出面，逐条带 file:line 证据面）；外部项目与外部 AI 仅作机制借鉴，未作立项理由或质量背书。
verdict: pass
auditor: 本轮执行者
subjects:
  - desktop/src/core/lsp.py:304e8edabe0c2878bc6fe997d957281cdc8b7cdfa7474b271bc25871690bc107
  - desktop/src/core/nf_language.py:a59d48d441a2cf4a52500680bbe93d3912323671cbec48168ee72847b946d0d7
  - desktop/tests/test_lsp.py:d07f7ed61fa65c2be085f562b07d79c7b76dcd82ef2493a5b13abac74e4494a7
  - desktop/tests/test_nf_language.py:c3db5b402404a9054079dbdc4fbd5e9de9acb30f341df52ed3392dbf7c0ddd9c
  - desktop/tests/test_doc_truth.py:384ce4b09c7a59149dd5f8d021bc094207b7f3a8d7a6d40eb3238da0a9ccfc3f
  - desktop/tests/test_site_face.py:d8e538a3af62d37994667d141dc940334d0821701644ceb8e34fbaf2ca07eb31
  - verify.sh:06932ee691ac96922d199ed3662099dbf6094d62b16c7d3a263e4dfff64a6230
  - scripts/nf.py:2f0ae88f3f05e3d391a70a8f860724b8ed0c3ebe5b2182e2bd2d7606bde43d7e
  - docs/lsp.md:db91bbfed27d7e14eb63c72e58ad8e009ce44a2b6563c15982b644ec358eca39
  - docs/mcp.md:24afe867db3ac4a7395591ba4938a87d771afbe6c1d631e0e639eb9adeea7716
  - docs/decision-layer.md:50755549b0970dbd64d7d98b4757011d55c586cd14172df5957d998a23c431a2
  - protocol/driver.json:66d6caf189756b8131eb5123673c90592dfa998b62f3de8192b997e983b5212c
  - integrations/site/integration.json:4a0b13e80d195f74e2c9965b899f87576e38d9c0b42190defb10bb13184e1374
  - integrations/site/strings.json:4d19bc7e32eb8bb9f7d368261c8bf464c02837ff828cbce364da4da229c4e59c
  - integrations/lsp/integration.json:2a0a752a3138db7bfd0d7c1c912c375f98e1eaf3fe783744ecb61a4d28e2a41e
  - integrations/lsp/strings.json:880d4cfd99a9c5ffe7c342af52f312f108d8c2e3455119dc538b77743fcb194b
  - skills/ninfenz/SKILL.md:5ef5858a08e6fd76a7cdee201938e0140e05257a7759a3ab27c05f9339109197
  - skills/ninfenz/references/commands.md:b62d73dfef22553dfc05c371e6725670b29201ae973e30fc7edca2bc3261b0bd

---

> 签收位：本件**未填 `accepted_by`/`accepted_at`**——验收签收属作者动作，执行者不自签。
> subjects = 本波承重件十八件（编辑器实现与符号索引 / 四个新判据件 / 门禁接线 / CLI / 四份人读文档 /
> 机器面绑定 / 两个新接入面登记 / 技能参考）。subjects 不含派生物（回执/生成物由 check31/33/35 自证）。

## 一、内部差距（开工依据，三轴审计）

| 轴 | 最强缺口（原文证据） |
|---|---|
| IDE | `docs/lsp.md:36-37` 承诺「装载结果请回填本文件」而无载体；门禁自述「编辑器面」而 `verify.sh:1738-1740` 只断言一个布尔；诊断位置恒 `(0,0)`（`lsp.py:113-114`）；无 didClose/rootUri/补全/悬停/跳定义 |
| 文档平台 | `verify.sh` 对 `site/` 零引用，站点门禁只在 `ci-verify.yml:40-43`；`integrations/README.md:3` 自称接入面机检真源却无 site 面；`site/facts.json` 七类事实仅 quality/scale 受判 |
| LLM 框架 | `docs/decision-layer.md:63/73/82` 与 `protocol/decision_layer.json:65-77`、`decision_layer.py:PROB_TOL` 三处直接矛盾且无对账门；`protocol/driver.json:5` 仍以 `serve <快照>` 为入口（与上架红线「默认无需快照」冲突）；`docs/mcp.md:84-95` 漏列已实现的 `resources/templates/list` |

## 二、交付

### 2.1 IDE 轴：编辑器面从「一个布尔」到协议行为

| 面 | 落点 |
|---|---|
| 符号索引 | 新增叶子模块 `core/nf_language.py`：模块 id 取模块文件自身 `machine_contract.id/name`（域包 `大语言模型:M01` 落在 `A01a_*.md`，按文件名反解必漏）、层位/订阅取 registry.json、事件取 event_registry.json ∪ subscriptions、资产键取文件名令牌、管线取 `id:` 声明行；**歧义不猜**（`M10`/`P00` 同名候选列全，跳定义失败关闭）；mtime 签名失效，长驻会话不必重启 |
| 协议能力 | `initialize` 声明 positionEncoding（固定 utf-16，位置按 UTF-16 码元折算）+ openClose/save 同步 + 补全/悬停/跳定义/大纲/工作区符号 + codeActionKinds；新增 `textDocument/didClose`（清状态并清诊断）；`rootUri/workspaceFolders` 采纳（显式 `--root` 优先）；未 shutdown 直接 exit 退出码 1（LSP 规范） |
| 定位精度 | 诊断逐条给真实行/列（trailing_ws 指向首个行尾空白列、final_newline 指向文末、头部规则指向插入位、正文 lint 按片段定位）；quickfix 由整文档替换改为**最小行级编辑**并用 `apply_edits` 回放自校验（不过即退回整文档，绝不交出改坏正文的编辑） |
| 装配成本 | `nf lsp --print-config neovim\|emacs\|helix` 生成现成配置（唯一真相 `lsp.render_client_config`）；VS Code 类**不生成**未经实测的配置，按 docs/lsp.md 诚实标注 |
| 门禁 | `lsp.check`（check33 第 5 面替换布尔断言）：能力齐备 / 诊断定位 / didClose / 退出码 / 领域解析真件 / 补全·悬停·跳定义·大纲真跑 / 三种配置可生成 |

### 2.2 文档平台轴：站点面进常驻判据 + 登记接入面

- 新增 `desktop/tests/test_site_face.py`（随 check12 常驻）：真跑 `site/tools/sync-numbers.mjs` 与
  `site/tools/site-check.mjs --offline`；并把 facts.json 此前无人核对的事实绑定到机读真源
  （quality↔repo_stats 凭证串、core↔core_modules/core_pipelines、mcp↔运行时支持版本、terminal↔真实入口）。
- `integrations/site/`（integration.json + strings.json）：站点登记为接入面（`status=proposed`——
  件与本地判据在场，**线上部署与联网自检待作者侧发布后回填**，不假称已上线）。

### 2.3 LLM 框架轴：对外文档与机读真源对账

- 修正三处文档漂移（决策层 pulled/real_run/容差、MCP 能力表、serve 入口与技能参考），
  并新增 `desktop/tests/test_doc_truth.py` 把「决策层文档 ↔ decision_layer.json ↔ PROB_TOL」
  与「`nf serve` 默认无需快照」钉成判据（此前 MCP 有对账门、这两处没有）。

## 三、验收证据（本机实测）

- `python -m unittest tests.test_lsp tests.test_nf_language tests.test_doc_truth tests.test_site_face` → **49 + 9 例全绿**。
- `lsp.check('.') → issues=[]`，符号面 **248 模块 / 360 资产 / 443 事件 / 9 层位 / 114 管线 · 客户端配置 3 种**。
- `integrations.check('.') → issues=[]`（13 个接入面，投影逐字）。
- `node site/tools/sync-numbers.mjs` / `node site/tools/site-check.mjs --offline` → rc=0。
- `python scripts/verify_run.py` → **PASS=72 · WARN=0 · FAIL=0**（check 序号不变，棘轮重冻见 CHANGELOG）。

## 四、遗留与设计偏差

1. **未在真实编辑器装载**：本机无 VS Code/Neovim/Emacs/Helix，编辑器侧装载仍属使用者回填
   （`docs/lsp.md` 已把回填去处钉到 `results/interop-thirdparty-status.md` 的 lsp 行；interop 卡待下一波补）。
2. **VS Code 类未适配**：需扩展宿主且本机无从实测，按纪律不产出未经验证的扩展/配置。
3. **站点联网面未自动化**：`site-check` 联网 14 项属线上事实，本地无外网依赖；本波只把离线面与
   facts 真源绑定纳入常驻，联网面维持「部署后人工跑」。
4. **facts.json 仍有 3 类未绑真源**（verifiable / npm 版本与文件数 / limits）：分别依赖 library 回执
   与 npm 注册表（联网事实），留待有真源可读时再绑。
5. **接入面他证通道未覆盖编辑器面**：`docs/interop-thirdparty.md` 14 卡仍无 LSP 卡；本波只做了
   内部协议行为判据，peer-consumption 卡留待下一波（避免把「没跑过」写成「已他证」）。
6. **code_metrics 棘轮重冻**：`lsp.py` 268→772 行（新增整套编辑器面，仍低于新文件 800 行上限）、
   `scripts/nf.py` +9 行；已按工具指引评审后重冻，非静默上调。

## 四之二、同波追加（第二段，2026-10-07 续）

审计差距消除三处（均只增判据，不改机制）：

1. **决策端口成功路径获常驻证据**（原差距：真实适配器 systemone-http 的成功面只有手工 AUD-0013 一次）
   → 新增 `desktop/tests/test_serve_decision_success.py`：真 HTTP（回环 + 临时端口）跑真 handler，
   钉 choice 顺序 / score legend 数字序 / noul 单值 / `_meta.model·usage·calibrated` / 404·413·500 具名错误；
   桩注入只替换模型，翻译层与 HTTP 契约走真代码。
2. **facts.json 剩余两类绑真源**（原差距：七类事实只绑 quality/scale）
   → verifiable 绑 `library/RECEIPTS.json`（RFC 6962 算法串 + 64 位十六进制根 + 每条 proof/digest）
   与 `core.attest` 的三个签名档常量；limits 绑 hosted_service/paid_tier/纯标准库三声明。
   npm 版本与文件数仍属联网事实，未绑（不假称已核）。
3. **编辑器配置从手抄变投影**（原差距：`docs/lsp.md` 的配置块登记为「不必真跑」，无人核对）
   → `test_lsp.TestDocConfigStaysInSync`：占位符还原后逐块比对 `render_client_config` 输出，
   并禁止文档写死本机绝对路径。

本段不改承重实现（只新增测试件与审计记录），故 `conformance` 仍 **conformant 27/27**；
审计 subjects 摘要按既有脚本机械重绑。

## 四之三、同波追加（第三段，2026-10-07 续）

1. **遥测判据扩面**（原差距 G5：门禁只判两个属性名，而 `to_span`/`to_export` 的 OTLP 形状、
   属性列表形态、同输入确定性、traceId 留空纪律都无门禁项）→ check33 第 7 面扩为：
   属性四键（operation/tool/agent/call.id）+ 结构化入参/出参面 + OTLP 形状（spans 数、
   scope.name、span 必备键、attributes 为 `{key,value}` 列表）+ 同输入两次导出一致 + traceId 留空。
2. **编辑器文档多语化**（原差距 G6：`docs/en`/`docs/ja` 有 mcp/terminal/layers/release/locales 而无 lsp）
   → 新增 `docs/en/lsp.md`、`docs/ja/lsp.md`（镜像路径、四节结构对齐原文）并在
   `protocol/locales.json` 登记，`nf locales --write` 重签（译件 10 → 12 件）。

## 四之四、同波追加（第四段，2026-10-07 续）

**站点机器面承诺绑真源**（原差距：站点正文语义无真源绑定，只有数字受判）
→ `test_site_face.TestSiteMachineEntriesPointAtRealArtifacts`：扫 `site/llms.txt`、
`site/nf.txt`、`site/agent.txt`（给 AI/agent 直读的入口清单）里的仓库相对路径与
`nf <子命令>` / `npx -y ninfenz <子命令>` 承诺，逐条要求**件在场 / 命令在 CLI 注册表**，
并设样本下限防判据空转。此前的缺口很具体：一次改名或删除就能让站点指向不存在的件，
而门禁全绿（本仓刚经历过 NarrativeForge→NinFenz 全局改名）。

## 四之五、同波追加（第五段，2026-10-07 续）

**check29 的门禁判据：从「名子串」升级为「真定义 + 真调用 + 有失败路径」**（原差距 G3）

- 旧口径：`gate in verify.sh 文本`——**注释里写一句 check18/22 就算过**；未定义、从未被调用、
  或任何分支都不会红的 check 都能被声明为「锁定该导出面」，于是 01 §1.2 的
  「L3 = 经导出门禁锁定」无从证伪。
- 新判据（真源 `conformance_scan.py`：`_gate_defs` / `_gate_calls` / `export_manifest_issues`）：
  解析 `^checkN(){..}` 到行首 `}` 的函数体；只在「主执行体」标记之后统计真调用；
  并要求函数体含 `err=1` / `problems.append` / `no "` / `no '` 之一（可能红）。
- 负例判据：新增 `desktop/tests/test_export_manifest_gates.py` 六例（注释提及 / 未调用 /
  不可失败 / `check18extra` 不得当 `check18` / 正例 / 真仓零 issue）。
- 跨语言：Rust 快线 `engine/rust/src/conformance_scan.rs` 同步镜像（同常量、同措辞），
  `cargo build --release`（1m35s）后 `test_rust_fastlane` **20 例全绿**（平价成立）。
- 行为等价证据：真仓重算后 **conformance root 不变**（47e358e6538a1827）、仍 **27/27** ——
  强化只增加抓错能力，不改当前判定；`code_metrics` 按工具指引评审后重冻
  （`conformance_scan.py` 1050→1106 行）。

## 四之六、同波追加（第六段，2026-10-07 续）

**修掉一处本波自己引入的「无法履行的承诺」+ 立同型判据**

- 缺陷：`docs/lsp.md`（及 en/ja 译件）写着「装载结果回填到 `results/interop-thirdparty-status.md`
  的 `lsp` 行」——而那张表**没有 lsp 行**（补卡要同步 .NET 线 golden，本机无 SDK，见本件
  §四之前置）。处置：三份文档改为如实标注「他证卡未补、本文不指向任何回填行」，并指明前置条件。
- 判据：新增 `test_doc_truth.TestInteropRowReferences`——文档里指向回填表**具体某一行**的引用
  （中/英两种语序）必须指向在册 face；逻辑核心以合成输入自证（注释提及式的空判据不算），
  并对全仓 `docs/**/*.md` 逐件扫描。

## 四之七、同波追加（第七段，2026-10-07/08 续）

1. **站点中英页平价 + 事实锚落点**（原差距 G5：`site/en/*` 是实际存在的第三处语言面，
   既不在 `protocol/locales.json` 的注册面里，也没有任何与中文页的平价判据；`facts.json`
   给每条事实声明的落地锚 `#fact-*` 此前也没人核过它是否真的在页上）
   → 新增 `test_site_face.TestSiteLanguagePageParity`：四维平价（锚点集 / 标题层级序列 /
   JSON-LD 类型集 / 机器入口链接集）+ facts 锚在中英两页落地；比较器以合成页对自证
   （四类漂移各自可被抓到），并对真页断言样本下限。
2. **uri ↔ 路径往返判据**（原差距 G5 的测试缺口：`uri_to_path` 的 Windows 盘符与
   空格/CJK 路径无断言——编辑器里天天出现，错位就是「跳定义打开不存在的文件」）
   → `test_lsp.TestUriRoundTrip` 三例（盘符 / 百分号编码 / 带空格与中文的往返）。

## 四之八、同波追加（第八段，2026-10-07/08 续）

**决策端口 HTTP 服务：不读完请求体就回响应 ⇒ 客户端连接被重置（本波由自家判据抓出）**

- 症状：`test_serve_decision_success.test_error_paths_are_explicit` 在**全量套件**里红
  （`ConnectionAbortedError [WinError 10053]`），单跑却绿——典型的负载相关竞态。
- 根因（服务端缺陷，不是测试问题）：`do_POST` 对未知路径直接回 404、对超限体直接回 413，
  **都没读请求体**；HTTP/1.1 下服务器不读完就回响应并关连接，客户端在写/读之间会拿到重置。
- 修法：新增 `Handler._drain(keep=MAX_BODY_BYTES)`——回 404/413 前把已声明的请求体读到丢弃
  （有界：最多 1 MiB，上限闸门仍然生效，不会因一个自称 2 GB 的请求把内存吃光）。
- 判据：该错误路径测试改为**带 64 KiB 真请求体**打未知路径（此前发空体，测不出 drain）。
- 影响面：这是「机器面报错必须可达」的一类；只跑单测测不出负载相关的连接重置，
  故该判据的价值在**常驻全套**里体现。

> **同段补记（自家判据抓出自家修复）**：`_drain` 首版把 `except ValueError: return` 写成无痕吞错，
> `test_silent_skip_reasons`（AST 级、窗口 = try 行 + 上三行 + handler 体）当场判红——
> 已在 `except` 行补「为何可以吞」的注释。记下来是因为它印证了这条纪律的价值：
> 修复动作本身也要过同一套判据。

## 四之九、同波追加（第九段，2026-10-08 续）

**LSP 端到端帧级金标（fixtures）**（原差距：编辑器面的回归全是「直接调 handle()」的行为断言
加传输层加固断言，**没有一件端到端帧级金标**——真实客户端帧序列到服务端应答这条链没有可
diff 的产物，任一能力的应答形状漂移只有人眼能发现）

- 生成器 `scripts/build_lsp_transcript.py`（`--write` 重签 / `--check` 只读对账）：把
  initialize → initialized → didOpen → completion → hover → definition → documentSymbol →
  workspace/symbol → codeAction → didChange → didClose → shutdown → exit 这一串**真实入站帧**
  跑一遍 `serve`，逐条固化出站应答；`today` 固定传入（产物不随日历漂）。
- 夹具 `desktop/tests/fixtures/lsp/session.json`：11 条应答 + 摘要。**可移植**——根路径折成
  占位符 `nf-repo-root`（含 URL 编码形态与 `edit.changes` 的 **uri 键**）；夹具是公开件，
  不带机器路径。
- **同段三处自纠（都由自家判据抓出，如实记）**：① 归一化首版只折字符串值、漏了**字典键**
  （`edit.changes` 以 uri 为键）→ 被 `test_leak_surface` 口径抓到后改为键也折；② 占位符
  首版用 `<ROOT>`，含 `<`/`>`，**JSON 键字符集判据**（`test_text_hygiene`）当场判红 → 换成
  字符集内且可读的 `nf-repo-root`；③ 生成器首版用 `Path.write_text` 落盘，**原子写单源判据**
  （`test_core_atomic_writes`）判红 → 改走 `core.atomic_write`；④ 占位符常量首版命名
  `ROOT_TOKEN`，**SAST 棘轮**（bandit B105 / ruff S105 的「硬编码口令形状」）新增命中 →
  改名 `ROOT_PLACEHOLDER`（常量名不该长成凭据形状）。四条都是「修复动作本身也要过同一套
  判据」的实例——本波共被自家判据拦下四次，逐条记档。
- 判据 `desktop/tests/test_lsp_transcript.py` 四层：可移植 / 逐字节对账（帧回放 == 夹具）/
  摘要 + 覆盖下限（诊断 ≥3 次、id 1-8 齐）/ 在盘夹具 == 实时重算（`--check` 语义常驻）。
- 接入面登记同步：`integrations/lsp` 版本 2.0.0 → **2.1.0**（字段级新增：证据加夹具与生成器，
  按 SemVer 档位映射 additive → MINOR），人读投影逐字重出。

## 四之十、同波追加（第十段，2026-10-08 续）

**机器入口的「能力承诺」与「路径承诺」两半补齐**

1. **站点机器面点名的 MCP 能力必须在运行时里**（`site/agent.txt` 列出检索类工具四个、内容通道
   三个、装载引导 prompt 一个）。此前 `prose_lint.command_face` 只扫 `docs/**`（FACE_DOCS），
   **不含 `site/*.txt`**——站点改名或删掉一个工具，agent 照站点调用就会拿到 `-32602`，而门禁全绿。
   判据：`test_site_face.TestSiteMcpCapabilityNames`（抽取句式「工具（a / b / c）」/「prompt（x）」，
   逐名对 `mcp_runtime` 的 `TOOL_DEFS` / `PROMPT_DEFS` 核；含抽取逻辑自证与「≥6 名」下限）。
2. **仓库机器入口（根 `llms.txt`）点名的仓库路径必须真在场**（审计 G3 的另一半：此前只有
   「生成区数字 + 固定锚点」受判，**路径承诺无人核**）。判据：`test_doc_truth.TestLlmsEntryPointPromises`
   （只认「含 / 且首段是仓库顶层目录」的 token，动态取顶层目录集，含逻辑自证与「≥30 条」下限）。
   实测**抓出一处真漂移**：`core/locales.py` 是模块简称，不是仓库根相对路径——机器入口（agent 会
   照着直取原文）写着它就会取不到；已改为 `desktop/src/core/locales.py`。

## 四之十一、同波追加（第十一段，2026-10-08 续）

1. **他证说明页成为逐字投影**（原差距：`docs/interop-thirdparty.md` 由 `--emit` 生成，但
   `check()` 只判状态表——而 `emit()` 会重置**第三方回填**的状态表，故真仓不能重跑它；
   于是说明页成了「是生成物却不被对账」的一件：卡片改了而说明页没重出，门禁看不出来）。
   修法与判据：把说明页渲染抽成纯函数 `render_doc()`（`emit()` 照旧写盘，行为逐字节不变），
   判据 `test_interop_thirdparty_kit.DocProjectionTest` 核「在盘说明页 == render_doc()」并带
   「≥14 卡」下限与「渲染确由 FACES 派生（合成 FACES 后卡片数随之变）」的自证。
2. **指令档头部的 override 声明与机读真源逐名对账**（原差距：`driver.scan` 判「机器面引用的
   工具在运行时存在」「头部有声明块」「有 fail-closed 关键词」，但**不判头部声明的工具集是否
   等于该工作流映射的工具集**——driver.json 加工具而头部没跟，执行者会照头部少走一条路）。
   判据：`test_doc_truth.TestDriverHeaderReconciles`——只取**连续的行首引用块**（正文后来再提
   工具名不算声明），逐档核工具集相等 + 提示名在块内；含抽取逻辑自证与「≥3 档」下限。
   实测三档（assemble / routing / menu）头部与 `protocol/driver.json` 完全一致。

## 四之十二、同波追加（第十二段，2026-10-08 续）

**编辑器面：把「每个请求都重扫仓库」这条真实的卡顿根因修掉（本机实测数字）**

- 实测（改动前）：`nf_language.signature()` 对全部扫描面 **731 件逐件 stat，119.5 ms/次**；
  补全请求 **158.33 ms/请求**——因为 `LspServer.symbols()` 每个请求都取一次索引，而取索引
  第一步就是重扫签名。编辑器里那就是「每敲一个字卡一下」（真客户端会明显掉帧/排队）。
- 两处修法：① 索引签名**复查加 TTL**（`INDEX_TTL_S = 1.0`）：窗口内复用索引，过期才重扫；
  `didSave`（磁盘件可能变了，且**放在 docs 守卫之前**——没跟踪的文档也可能是仓库件）会
  `invalidate()` 强制下次重扫。② `nf_language.build(root, sig)` 接受**已算好的签名**，
  服务端不再让 build 内部重扫第二遍（首建实测省一次 119.5 ms）。
- 实测（改动后）：**暖补全 158.33 ms → 0.51 ms/请求**；冷启动首次建表 221.1 ms（每 TTL 最多一次）。
- 判据（`test_lsp.TestIndexTtl`，四例，**用调用计数不看墙钟**）：窗口内 6 次取索引只扫 1 次签名 /
  `invalidate()` 后重扫一次 / TTL 过期且签名变化才重建（未变则复用同一对象）/ `didSave` 必
  强制下次重扫。性能判据不看时间，换来的是**不会因机器快慢而假红**。

> **同段补记（判据本身踩到仓库已记档的坑）**：`TestIndexTtl` 首版用 `from core import nf_language`
> 取模块再打桩——单跑全绿，**全量套件里三条判据同时红**。根因不是被测代码：daemon/watch 类测试
> 会把 `core.*` 从 `sys.modules` 摘掉重载（`test_watch` 有专门的「模块身份还原」段），于是
> `from core import nf_language` 拿到的是**另一份实例**，而 `lsp` 用的是先前那份——桩打在了
> 影子对象上。修法：一律改 `lsp.nf_language`（被测方真正引用的那个对象）。记档理由：这类
> 「同进程两份模块对象」的坑本仓已写过一次，仍会在新判据里复发。

## 四之十三、同波追加（第十三段，2026-10-08 续）

1. **服务端自述版本单一来源**（原差距：`initialize` 的 `serverInfo.version` 是写死的字面量，而
   接入面卡 `integrations/lsp/integration.json` 另有自己的 `version`——两处各写一遍，改名/升版
   必漂）。修法：代码侧立 `SERVER_NAME`/`SERVER_VERSION` 常量，`initialize` 从常量取值；
   `lsp.check` 增加「serverInfo 与常量一致」判据；`test_lsp` 增加「接入面卡 version ==
   SERVER_VERSION」对账。**顺带被自己的金标抓到**：改版本后 **帧级转写夹具当场不一致**——
   这正是它该做的事（金标拦住未重签的协议面变更），已按 `--write` 重签。
2. **`lsp.py` 拆出客户端装配面**（原差距：模块涨到 **805 行**，越过 800 行的新文件上限——本仓
   纪律是「能拆就拆」，不是 `--write` 一把梭）。拆出 `core/lsp_client.py`（`CLIENT_EDITORS` +
   `render_client_config`）：这是**另一个变化原因**（跟编辑器生态走，不跟 LSP 规范走）。
   拆分后 `lsp.py` 回到上限内（冻结值 796 之下，**无需重冻**），调用方 `nf.py` 与测试改为直接
   引 `core.lsp_client`（不留转口 shim）。接入面卡证据补上该模块，版本 2.1.0 → **2.2.0**
   （字段级新增，SemVer additive → MINOR），人读投影逐字重出。

## 四之十四、同波追加（第十四段，2026-10-08 续）

**一键引导脚本进「机器入口承诺」判据面**（原差距：判据只扫 `site/llms.txt` / `nf.txt` /
`agent.txt`，而 `site/run.sh` 同样是对外承诺——它写着 `scripts/nf.py doctor`、`tui/nf.py`、
`bash verify.sh`，且安装器是**外部最先执行**的那一件）。修法与判据：把 `site/run.sh` 并入
`MACHINE_ENTRIES`（路径在场 + `nf` 子命令在册），并补 `"$PY" scripts/nf.py <cmd>` 形态的
抽取（解释器是变量，旧正则只认字面 `python` 会漏）。实测：run.sh 的 4 条路径全在场、
唯一命令 `doctor` 在册。

> **同段一条「已具备不重做」**：本轮先写了「MCP 红线里的散文计数（当前 N 工具 + M prompt）
> 与运行时对账」，跑起来才发现 `test_mcp_packaging` **早有一条** `test_prose_tool_counts_match_runtime`
> （还多覆盖了 `docs/mcp.md` 投影面）。按纪律「已具备不重做」——新增件已撤回，本波只留
> run.sh 一项；这条记录留档，免得下一波再写一遍。

## 四之十五、同波追加（第十五段，2026-10-08 续）

**Agent Skill 的命令面进判据**（原差距：`prose_lint.command_face` 的扫描面是 FACE_DOCS +
`docs/*.md`，**不含 `skills/**`**——而 `skills/ninfenz` 是给外部 agent 的装载面，里面列了 13 个
`nf` 子命令；命令改名后技能文档指向死命令，门禁全绿）

- 判据：`test_doc_truth.TestSkillCommandFace`（抽取复用 `prose_lint._command_snippets` /
  `_NF_CALL`，不另写正则；含抽取自证与「≥10 条」下限）。实测 13 个子命令全部在册。
- **为何不直接扩 `command_face` 的扫描面**（那样更「机制唯一」）：它会改该方法返回的 stats
  （文档数/命令数），而 .NET 线金标 `real_command_face.digest32` 与 `log[0]` **正好钉着那行摘要**
  ——本机无 .NET SDK、也无金标快照 `nf-snap-h16`，改不动（同 LSP 他证卡同类前置）。故本判据落
  在常驻套件里，并**把 CLI 注册表抽取收敛成 `prose_lint.cli_commands()`**（`command_face` 改调它，
  行为逐字不变、42 例判据复验），避免两处各写一遍正则。

## 四之十六、同波追加（第十六段，2026-10-08 续）

**编辑器面：参数准入（把「不合形参数 → 内部错误」修成「-32602 + 修复指引」）**

- 实测差距（**四类**，全部会把 Python 异常文本回给客户端）：`position.line` 非整数 →
  ValueError；`context.diagnostics` 是字典或字符串 → AttributeError；`didOpen.text` 非字符串 →
  AttributeError；`contentChanges` 元素非对象 → AttributeError。旧路径一律被 serve 兜成
  **-32603 内部错误**。协议上这是**参数非法**，与 MCP 面 2026-09-30 修的同一类问题（那边已有
  参数准入与门禁）。
- 修法：新增 `core/lsp_params.py`（请求形状准入 + 通知载荷准入）——
  请求不合形回 **-32602** 带修复指引；**通知没有应答位，则丢弃且不进状态**（存进去会让后续
  每次诊断都以 AttributeError 收场）。`lsp.check` 补一条准入探针（非法 position 必须回 -32602），
  常驻判据 `test_lsp.TestParamAdmission` 五例（含「坏帧不进状态、会话仍可服务」）。
- 规模棘轮如实走：准入层加在 `lsp.py` 后到 **843 行**（越 800 上限）且最长函数 37 行（越冻结 35）
  ——两处同时亮。按纪律「能拆就拆」：准入层独立成 `core/lsp_params.py`（另一个变化原因：跟协议
  规范与客户端实现走），客户端配置体检抽成 `_client_config_issues()`，函数回到限内；模块行数
  重冻（764 → 786，纯接线 + 门禁探针）。接入面卡证据补 `lsp_params.py`，版本 2.2.0 → **2.3.0**
  （行为面确有变化：新增拒绝语义），转写金标与 README 投影同步重出。

> **同段一条「已具备不重做」（本波第二次）**：本波先拟「把 docs/lsp.md 等入口文档加入
> `test_doc_reachability.ENTRY_DOCS`」——读到该文件后半才发现已有 `LivingDocConsistencyTest`
> 扫描**全部在场文档**（`.md/.txt`，排除 CHANGELOG/results），那几件早已在面内。未改动，留档。

## 四之十七、同波追加（第十七段，2026-10-08 续）

**LLM 框架面：MCP `tools/call` 的 `arguments` 静默降级修掉（按面普查的下一行）**

- 实测差距：`_call_tool` 旧写法 `params.get("arguments") or {}` 把 **假值**（`[]` · `""` · `0` · `false`）
  静默当成「没传参数」并继续执行——客户端以为走了位置参数，服务端却按默认值跑完**还给了结果**
  （静默降级，正是本仓最忌讳的失败形状）；口径也与 `prompts/get` 不一致（那边早已拒绝非对象）。
  同轮普查还确认：MCP 面其余形状（未知名 / 缺 name / 多余键 / 类型错 / 缺必填 / 逃逸 uri / 未知方法 /
  坏 id / params 非结构化）**都已**是 `-32602` 或 `-32600` 带修复指引——只有这一处漏。
- 修法：显式 `null` 视为未传；**其余非对象一律 `-32602` + 修复指引**。判据落在**真进程**上
  （`test_mcp_live_e2e.test_arguments_must_be_an_object_not_a_list`：[] / 0 / "oops" 全拒，
  `{}` 仍正常执行）。接入面卡 `integrations/mcp` 1.0.0 → **1.1.0**；`protocol/mcp_package.json`
  的红线本就声明「不合即 -32602」——本修法让那条声明更真，不需要改包版本。
- **金标安全核对**：.NET 线探针只用 `{}` 或含多余键的对象，没有「假值非对象」用例，
  故本次行为收紧不会改动任何已录金标（已逐条核 `engine/dotnet/probes/*.py`）。

## 四之十八、同波追加（第十八段，2026-10-08 续）

1. **决策端口（LLM 轴 · systemone-http 契约）把「客户端错」与「服务端错」分开**。
   实测差距：请求体不是 JSON / 缺 state / questions 是数组 → 旧实现一律 **500** 且响应体带
   Python 异常类名（JSONDecodeError / AttributeError）。后果是调用方按状态码判定「服务端故障」
   并**重试**——而这类请求重试一万次也不会成功；排查方向也被引向服务端。本仓另两个服务面
   （LSP 的 -32602、MCP 的 -32602/-32600）早已分开，这里补齐：
   **入参形状错 → 400 + `hint`（指向 docs/decision-layer.md 契约）**；**推理/传输失败仍 500**。
   顺带补：未支持方法（PUT/DELETE/PATCH/OPTIONS）回 **405 JSON + Allow**（旧路径是
   BaseHTTPRequestHandler 的 **HTML 501**，机器客户端拿到一坨 HTML）；`HEAD` 只回表头（探活用）。
   判据：`test_serve_decision_success` 扩到 4 例（400 五类 / 真 500 仍 500 / 405+HEAD / 原成功面），
   真 HTTP 回环跑真 handler。
   （过程如实记：全量验证第一次跑红——死代码判据 test_dead_code 把新增的 do_PUT / do_PATCH /
   do_OPTIONS / do_DELETE / do_HEAD 判成零引用。这是教科书级假阳性（http.server 按方法名派发），
   也正是该判据存在的意义：它逼我逐条登记进 IMPLICIT_HOOKS 并写明理由，而不是把规则放宽。）
2. **无效转义序列卫生（本波自查产物）**。起因：本波跑判据时看到
   `DeprecationWarning: invalid escape sequence`——追下去发现是**自己前几波**留下的笔误
   （`lsp_client.py` / `lsp_params.py` 的文档串里「反斜杠 + 反引号」），另有一处**既有**的
   Windows 路径写法落在非 raw 文档串里（`test_cli_error_framing.py`）。三处都已修（改 raw 或
   去多余反斜杠，语义不变），并立常驻判据 `test_text_hygiene.SourceEscapeHygieneTest`：
   对 379 件源文件 `compile()` 捕警告面（正例零命中 + 变异负例必被抓）。

## 四之十九、同波追加（第十九段，2026-10-08 续）

**文档平台面：站点 Worker 从「字符串包含判据」升级为「行为判据」**

- 实测差距：`site-check.mjs` 对 `worker.js` 只有两条**字符串包含**判据
  （`wk.includes('text/markdown')` / `includes('301')`）——把协商写成永不触发、把 `q=0` 当同意、
  把回落逻辑写反，它**都照样全绿**：这是空转判据（本仓对「判据要能红」有明确纪律）。
- 同时修掉一处**真行为缺陷**：旧闸门是 `accept.includes('text/markdown')`——按 RFC 9110 §12.5.1，
  `Accept: text/markdown;q=0` 是客户端**明确不要**，旧实现照回 markdown（观测到的后果：明确
  排除了机器面的客户端反而拿到机器面）。
- 落地：新增 `site/tools/worker-check.mjs`（真跑模块 + 桩 ASSETS，**16 条行为表**：三条协商路由 /
  `q=0` 两种写法 / 通配 `*/*` 不触发 / 未点名不触发 / 列表与 `text/*` 触发 / 非协商路由与非 GET
  不触发 / 机器面缺失与抛错**回落原请求** / www 301 保留路径与查询 / 其余透传）。`worker.js` 改为
  `wantsMarkdown()`（显式点名 + q>0；通配不触发，理由写进注释——`curl` 默认发 `*/*`）。
  `site-check.mjs` 的两条空转判据删除，只留「有导出 fetch」的结构性一条。
- 判据接入常驻套件：`test_site_face` 真跑该工具，并带**变异负例**（把闸门换回 `includes` 的临时副本
  → 必须退出码 1：「改坏后仍全过 ⇒ 判据空转」）。接入面卡 `integrations/site` 1.0.0 → **1.1.0**
  （证据补 `worker.js` 与 `worker-check.mjs`）。

## 四之二十、同波追加（第二十段，2026-10-08 续）

**① 编辑器面：LSP 会话状态机**（实测三处协议违规 → 全部照常服务）

- 修前实测：未 `initialize` 就发请求 → 正常应答；重复 `initialize` → 正常应答；`shutdown` 之后
  继续发请求 → **仍然服务**。按 LSP 规范这三类都该拒：未初始化要回 `-32002`，重复 initialize 与
  shutdown 之后的请求回 `-32600`。危害不只是「不合规」：未初始化就服务意味着**拿 CLI 默认根**
  （还没采纳客户端 rootUri）去解析，结果可能是错的。
- 落地：`core/lsp_params.lifecycle_problem()`（形状准入与会话状态准入同处一模块）；`handle` 重构
  为「状态机 → 握手 → 通知 → 请求」四段式，错误应答收敛到 `_error()`、握手收敛到 `_handshake()`；
  未握手前的**通知**一律不做（`exit` 除外，由 serve 循环收口退出码）。门禁 `lsp.check` 增三条探针；
  常驻判据 `test_lsp.TestLifecycleStateMachine` 五例。

**② 传输分帧独立成 `core/lsp_framing.py`**（线格式 vs 协议语义是两个变化原因）：`read_message` /
`write_message` / `MAX_MESSAGE_BYTES` / 坏帧哨兵迁出，`lsp.py` 只做转口；顺带修掉一处被夹断的
注释块（`INDEX_TTL_S` 的说明此前粘在坏帧说明后面）。

**③ 事故与恢复（如实记，必须留档）**：做 ② 时我用脚本按「起点标记 → 终点标记」切片搬运代码，
**边界取样错了**——把 `_binary` 到 `_error` 之间**整块**（约 270 行）切走，其中包含**文档级能力**
（`diagnose` / `outline` / `word_span` / `prefix_before` / `text_edits` / `apply_edits` / UTF-16 换算）。
而且这次会话**没有提交过**，git 里没有可回滚的版本；`.rivet/scratch` 的缓存副本是发布期快照（早于本会话）。
恢复方式：按**调用点契约 + 单测期望 + 端到端帧级金标**重建该块——**金标是关键**：重建后
`scripts/build_lsp_transcript.py --check` **11 条应答逐字节一致**，即重建实现与被删实现在该夹具覆盖的
行为面上等价。这一条同时说明本波之前建的夹具不是装饰：**它在实现被我自己弄丢时当了 oracle**。
事后纪律（写进本段以免复发）：脚本化切片必须在写盘前**打印并核对边界行号与切除字节数**。

## 四之二十一、同波追加（第二十一段，2026-10-08 续）

**① `$/` 请求被静默吞掉（规范违规，会让合规客户端一直等）**

设计加宽金标时发现：`handle` 对 `$/` 前缀一律 `return []`——**通知**忽略是对的，但**请求**
（带 id）必须回 `MethodNotFound`（LSP 3.17「$/ Requests and Notifications」）。静默不回 = 客户端
永远等不到应答。修法：`rid is None` 才忽略，否则回 `-32601`。金标里新增 `$/noSuchRequest` 帧
把它钉在帧级。

**② 端到端帧级金标从 11 条扩到 20 条应答**（上一波事故的正面产物：金标是我唯一的 oracle，
那就要把编辑器的真实入站面都罩住）

新增覆盖：`textDocument/willSave`（通知，静默）· `willSaveWaitUntil`（未声明能力 → `-32601`）·
`workspace/didChangeWatchedFiles` · `workspace/didChangeConfiguration` · `$/setTrace` ·
`$/cancelRequest` · `textDocument/didSave`（触发索引失效）· 命中不到符号的悬停（`null`）·
工作区符号无命中（`[]`）· 未知方法（`-32601`）· 未知 `$/` **请求**（`-32601`）· 连续两次
`didChange` 全文同步（末次为准）· 已关闭文档的补全（空面）· shutdown 之后的请求（`-32600`）。

判据同步加强：`test_lsp_transcript` 下限抬到「≥18 条应答 / id 1–15 齐 / ≥6 条静默入站帧」，
并新增 `test_lifecycle_and_dollar_edges_are_pinned`——不只对字节，还把**语义**钉住
（未声明能力回 -32601、无符号悬停为 null、shutdown 后 -32600、`$/` 请求必须回错误）。

**③ 过程两条**：㈠ bandit B105（「硬编码口令形状」）在 `"token": 1` 这个 `$/progress` 帧上报了一次
**假阳性**——我没有 `# nosec` 也没有重冻基线，而是换成编辑器真正会发的 `$/cancelRequest`（键名不再是
凭据形状），基线因此回到 32；㈡ `handle` 变长后按可读性抽了 `_dispatch_request()`（函数回到限内）。

## 四之二十二、同波追加（第二十二段，2026-10-08 续）

**① 先说一个「已具备」的负面结论**：按上一波的线索去量 MCP 面的协议族口径，逐条实测（`ping` 请求
→ `{}`；`ping`/各 `notifications/*` 通知 → 静默；`notifications/initialized` 带 id → `-32601`；
可选能力 `completion/complete` / `logging/setLevel` / `resources/subscribe` → `-32601`；
`resources/templates/list` → 已实现）——**MCP 面本来就合规**，LSP 那处 `$/` 缺陷在它这里不存在。
这条负面结论照实记：它说明「同型问题」在另一轴**没有**，也构成两侧口径对账的基线。

**② 立「两轴同族判据」**（`desktop/tests/test_two_faces_jsonrpc.py`）：把共享的 JSON-RPC 族口径列成表
逐条**在两侧实跑**——未知请求 → `-32601`；通知 → 一律不应答（含「把请求方法当通知发」）；
已知方法参数不合 → `-32602`；MCP 特有 `ping` 必须有应答、LSP 无 `ping`（`-32601`）。
带**变异负例**（对通知也回错的桩必须被助手抓到）。立此件的理由：两侧各自的测试都自洽，
**没有任何一条判据要求两侧对同一语义给同一档**——口径漂移恰好生长在这个缝隙里。

**③ 新判据当场抓到一个真缺陷**：LSP 面对「**请求方法当通知发**」（无 id）会回一条 `id=null` 的应答。
JSON-RPC 2.0 §4.1：**通知没有应答位，禁止应答**。后果是客户端收到不请自来的响应（真客户端会记日志
甚至报错）。修法：`_dispatch_request` 在 `rid is None` 时直接不应答（`shutdown` 的通知形态仍记
状态、只是不回）；同族口径在 MCP 面本来是对的。**金标里也补了这个入站帧**：出站应答条数仍是 20
（没有对应应答），哪天回一条就与夹具不再逐字节相等。

> **同段事故与恢复（第二次自伤，必须留档）**：全量验证第一遍红在**我自己第 16 波立的转义卫生判据**上
> ——新写的 `test_two_faces_jsonrpc.py` 里又有「反斜杠 + 反引号」的生成笔误。修那一处时我图省事，写了
> **全仓批量替换**（把「反斜杠+反引号」一律换成反引号），结果**误伤了合法正文**：`terminal.py`（行尾 \ 续行
> 的说明）、`trust_boundary.py` 与 `watch.py`（Windows 路径写法说明）、`test_cli_error_framing.py`（反斜杠
> 分隔符说明）、`nf.py`（`nf diff` 的路径显示帮助）——五处文档串被悄悄削掉反斜杠，而**语法与判据都不会报**。
> 恢复方式：**没有用任何破坏性 git 命令**（`checkout --` / `restore` / `stash` 一律未用），而是用
> `git show HEAD:<file>` 取回原文，按**严格谓词**逐行核对「当前行 == HEAD 行做过那一替换后的样子」
> 才还原，并打印所修行号复验；`nf.py` 因为同时有本会话的合法改动、行数不同，改用「反向映射唯一命中」
> 的方式还原三行。复验：四处文件与 HEAD 的 diff 归零、`nf.py` 只剩此前有意改的 explain 文案、
> 256 例相关判据全绿。
> **两条纪律（本波代价换来的）**：㈠**不许全仓批量文本替换**——即使替换目标是已知的生成笔误，也必须先
> 「列出待改文件 + 行号 + 前后对照」，人核后再改；㈡生成含反引号的文档串时，**不要在 JS 模板里写反斜杠
> 转义**（这已是第三次踩），要么用 `chr(96)` 拼，要么写完后立刻跑一次转义卫生判据。

## 四之二十三、同波追加（第二十三段，2026-10-08 续）：**按参照做，而不是自己发明**

两次自伤都出在「我自己写脚本改自己的文件」这件事上。作者点出方向：**多找参照**。照做，先普查本仓已有惯例：

| 问题 | 本仓既有参照 | 我此前的做法 |
|---|---|---|
| 需要在字符串里写反引号 | `chr(96)`：`conformance_scan.py`（`_T = chr(96) * 3`）· `test_doc_truth.py`（`_BT`）· `test_lsp.py`（`FENCE`） | 在生成模板里写转义，反复产出笔误 |
| 落盘 | `core.atomic_write.write_text`（单写面） | 偶尔直接用 `open(...).write` |
| 机械改写 | 生成器/搬运件一律 `--write`/`--check` 双态（`rebind_audits.py --check`、`nf locales --write`、`build_lsp_transcript.py`） | 临时脚本**直接落盘**，无干跑、无对照 |

**落地（把最后一行补上）**：新增 `scripts/rewrite_text.py`——**默认干跑**，逐行打印「文件:行号 + 改前 → 改后」；
`--write` 才走 `atomic_write`；**爆炸半径闸门**（命中行数 > `--max-hits` 即拒绝，默认 50）——这条正是
「一处笔误改成全仓事故」的反制；`--check` 复验残留；`--root` 可指向临时树（同 `interop_thirdparty_kit` 惯例，
让判据能在隔离树上跑真流程）；非 UTF-8 件跳过不改。判据 `desktop/tests/test_rewrite_tool.py` 五例：
干跑不动盘 / 落盘只改命中件（include 外与未命中件不动）/ `--check` 残留即 rc=1 / 超限拒绝且不动盘 /
二进制件跳过不损坏。`CONTRIBUTING` §4.2 补一行指向它（含「不做无对照的全仓替换」这条纪律）。

**顺带做了一次全仓复核**：用本工具 `--check` 扫「反斜杠+反引号」，命中 26 处 / 14 件——逐件核对**全部是
合法正文**（行尾续行说明、Windows 路径写法说明、`nf diff` 帮助及其 npm 载荷镜像），**无残留笔误**；
并核对了 npm 载荷镜像与源件逐行一致（我那次批量替换只扫了 desktop/scripts/site，没碰 packaging/，幸而如此）。

## 四之二十四、同波追加（第二十四段，2026-10-08 续）：**编辑器面补「结构化引用」**

**新增能力 `textDocument/references`**（协议/实现/门禁/文档/证据五件齐）

- **口径（这是本波的关键判断）**：NF 里的「引用」是**有登记的**关系——`registry.json` 的
  `subscriptions`（事件 ↔ 发布/订阅模块）、`modules[].mounts`（模块 ↔ 挂载层）、`protocols`
  （管线 ← 域包采用，位置取该包 README 且**文件不存在即不给**）。因此引用面**只给结构化关系**，
  每条位置都带 **why**（发布方 / 订阅方 / 挂载于 Pxx / 被域包 X 采用）；未登记 token 一律空表。
  **不做全文搜索**——那会喷一堆假引用，正是本仓「不猜」纪律的反面。同名 token（`P00` 层位/管线）
  把两类关系的命中一并列出，而不是猜一种。
- **实现**：`nf_language._relations()`（按来源拆三个小函数）+ `SymbolIndex._resolve_kind()`
  （按**声明的目标种类**解析，专治 `P00` 同名）+ `SymbolIndex.references()`；`lsp.py` 增
  `referencesProvider` 能力、`_references()` 处理器（`includeDeclaration=false` 剔除声明自身）、
  准入表一行、门禁探针 `_references_issues()`。
- **判据**：索引侧 4 例（事件带 why 且路径真在盘上 / 模块↔层双向 / 管线→域包文件 / 未知 token 空表）；
  协议侧 4 例（给 file: 位置 / 未知 token 不猜 / `includeDeclaration` 桩索引剔除声明 / 缺 position 回 -32602）；
  **帧级金标**加 `references` 帧（应答 20 → **21** 条），并把 `referencesProvider` 接进
  「声明能力 → 转写证据」映射表。
- **文档**：`docs/lsp.md` 能力表加行 + 边界加「引用不是文本搜索」，`docs/en|ja/lsp.md` 同步翻译，
  `nf locales --write` 重签（12 件）。接入面卡 2.5.0 → **2.6.0**。

**同波结构变更（按第 20 波事故换来的纪律做的）**：`lsp.py` 加引用面后到 **826 行**（越 800 上限），
按纪律拆出 `core/lsp_doc.py`（文档级能力：位置换算/词法/大纲/诊断/文本编辑，纯函数、无会话状态）。
这次**先打印边界**（第 102–315 行、214 行）再切，切完跑**验证三件套**：ruff 未定义名 → 全部单测 →
**帧级金标逐字节**（这一步正是第 18 波事故里救我一次的那个 oracle）。结果：`lsp.py` 826 → 616，
判据全绿、金标一致；调用方（测试）改为直接引 `core.lsp_doc`，不留转口。

> **同波补记（拆完要清场）**：第一次全量验证红在死代码判据——切走文档级能力后，`lsp.py` 里
> 留下了四个**零引用常量**（`SEVERITY_WARNING` / `SYMBOL_KIND` / `HEADING` / `WORD`），正是「拆完
> 没清场」的痕迹：移动代码时只搬了使用者，没搬定义处。修法：**先打印待删行再删**（本波新立的纪律
> 用上了），删后 ruff / 单测 / 帧级金标三件套复验通过。这条也说明：**搬运不是复制粘贴，是「搬走 +
> 在原处清场 + 三件套复验」**。

## 四之二十五、同波追加（第二十五段，2026-10-08 续）：**把「只读」红线写成协议层可机读的形式**

**① 先给一个负面结论**：按「声明 ↔ 实现」这条线去量 MCP 面，先查了**能力声明**——initialize 与
`server/discover` 都只声明 `{resources: {}, tools: {}, prompts: {}}`，**没有**声明 `subscribe` /
`listChanged` / `logging` 这些未实现的能力（即没有虚报）。这条照实记：MCP 的能力面本来就是诚实的。

**② 真缺口在「红线住在散文里」**：`protocol/mcp_package.json` 的红线写着「只读：不新增任何写工具」，
`docs/mcp.md` 通篇说只读——但 MCP 客户端**读不到散文**，它读 `tools/list` 的
`annotations.readOnlyHint`（MCP 2025-03-26+）。缺这个注解的后果是具体的：客户端**无法自动放行**
只读工具，只能对每次调用弹窗确认——「只读」在协议层等于不存在。
- **实现**：10 个工具**逐条**声明 `annotations: {readOnlyHint: true}`（**不做统一贴标**——将来真加写工具时，
  贴标会让注解变成假话；逐条声明 + 既有「工具名只读」判据合起来才自洽）。
- **判据**（`test_mcp_packaging.McpToolAnnotationsTest` 四例）：每个工具都声明只读 / 注解**真出现在
  `tools/list` 上**（不只在常量里）/ 无工具声明 `destructiveHint=true` / **变异负例**（把某工具标成非只读必须被抓）。
- **文档**：`docs/mcp.md` 能力表加行（说明客户端可自动放行），`docs/en|ja` 同步，`nf locales --write` 重签。
  接入面卡 1.1.0 → **1.2.0**。
- **过程一条（照参照做）**：插入注解前我先跑了**干跑脚本**，它按行号列出 11 个待插入点并断言「应为 10」——
  当场停下（第 11 个是同区的 `PROMPT_DEFS` 条目），改成按 `TOOL_DEFS..PROMPT_DEFS` 边界后再插。
  这正是第 20 波事故后立的纪律（先打印待改点、边界不对就停）第一次**在写盘前**拦住我。

## 四之二十六、同波追加（第二十六段，2026-10-08 续）：**模板可用性**——「发布了的模板必须真能用」

**① 先量（两个负面/正面结论）**

- `prompts/get`：`assemble_guide` **不声明参数**，而实现也**明确拒绝**非空 `arguments`（回 -32602 并给
  「本模板无参数」的修复指引）——声明与实现一致，**不是缺口**；这条口径（允许出现 `arguments`，但非空即拒）
  已在 2026-10-01 的实测注释里写明。
- 资源模板：`resources/templates/list` 发布 5 条模板，其中 4 条按模板替身能读；**第 5 条读不出来** ↓

**② 真缺口：模板是「不可用承诺」**。`nf://repo/asset/{package}/{key}` 的替身写法（agent 按模板自然代入
**中文包名**，即未编码形态）`resources/read` 一律回「未知资源 uri」——因为 `resources/list` 给的是
**percent-encoded** 形态，而读入侧只做**字面**匹配。这就是「发布在机器面上的模板，照它写反而读不到」。

**③ 修法（加法，不动白名单）**：读入时先做一次**转义等价归一** `_uri_escaped_alias()`——把入参
`unquote` 后与**已登记** uri 的 `unquote` 形式比对，命中则改写成登记形态继续走原逻辑。
白名单语义不变（仍只认已登记 uri；错包名/缺段依旧拒绝）。与「馆藏 uri 大小写不敏感」是同一条纪律。

**④ 判据（补的是**反方向**）**：既有 `test_listed_resources_are_all_readable` 只读 **list 给的形态**；
新增 `test_template_substitution_is_readable`——每种 kind 取一件，**解码后**再读，必须成功；并断言
「至少一件解码前后不同」（防空转）。既有判据 + 新判据合起来才覆盖「列出、代入两种写法都能读」。

**⑤ 过程一条（判据当天就抓到我）**：归一助手首版写了「入参无转义就早退」的优化——恰恰把
「入参未编码、登记项已编码」这一种组合漏掉（就是本缺口本身）。新判据与复测当场把它抓出来，
去掉早退后通过。**优化不能改变语义**，这条记在函数注释里。

接入面卡 1.2.0 → **1.3.0**。

## 四之二十七、同波追加（第二十七段，2026-10-08 续）：**声明即承诺**——声明了就必须有效果

**① 普查方法**：先试静态（AST 抓处理器读到的 `args` 键），发现处理器挂的是 lambda、抓不到；**改用行为普查**
——对每个工具、每个 `inputSchema` 声明的属性，把该属性置成一个「绝无此值」的探针串，比较响应是否变化。
（这一条也说明：**能跑就别读代码猜**。）

**② 结论分两半**

- **好的那一半**：无必填字段的工具（`pipeline_ls` / `spec_ls` / `knowledge_order`）传 `{}` 都能正常返回
  ——**没有隐藏必填**；有必填字段的工具一律按声明回 `-32602`；`knowledge_order` 的 `clearance` 声明了
  `enum`，传枚举外的值被正确拒绝（我最初判它「拒」是探针值错，不是缺陷）。
- **真缺口**：`spec_ls` 声明 `tier`「可选按分级过滤」，而 `registry.json` 的 protocols 里**根本没有分级
  字段**——传任意 tier（含乱填）返回**完全相同**的全量清单，结果里也没有 tier 字段。客户端以为筛过了，
  实际拿到全部：**静默降级**，比缺个参数更坏（本仓明令反对的失败形状）。

**③ 修法（删声明，不造数据）**：把 `spec_ls` 的 `tier` 删掉，并在原处写明理由与「将来 registry 补了
分级数据再连同实现一起加回」。**不为了让声明成真而去编造分级数据**。

**④ 新判据（把「声明即承诺」立成通则）**：`test_mcp_runtime.ToolSchemaEffectTest`——
① 每个声明属性置「绝无此值」后响应必须**变化**（否则须进 `NOOP_ALLOWED` 并写明理由，本表**只许缩小**，
同 `test_doc_reachability.EXEMPT_DOCS` 的既有惯例）；② 带**变异负例**（忽略参数的桩必须被助手抓到，
真用参数的桩不得误报）；③ 覆盖面下限（≥8 个属性）防空转。修完实测：**10 个工具的全部声明属性都有效果**。

接入面卡 1.3.0 → **1.4.0**。

## 四之二十八、同波追加（第二十八段，2026-10-08 续）：**配置生成件的「能用」判据** + 一条反向覆盖负面结论

**① 先给负面结论（模板反向覆盖）**：既有判据只保证「每条真实 uri 被某模板覆盖」；本波补量**反方向**
——每条模板是否都命中至少一件真实 uri（幽灵模板检查）。实测：5 条模板全部有命中
（library 3 / pattern 7 / module 248 / pipeline 114 / asset 926），**没有幽灵模板**；每个 `{var}` 也都在
真实 uri 里有非空取值。这条照实记，作为模板面的基线。

**② 真缺口（判据强度）**：编辑器配置面此前**只有子串判据**（含 `scripts/nf.py` 与 `"lsp"`）。
生成器若把 Windows 路径或含空格路径写成**非法 TOML**（把反斜杠留在基本字符串里就是这种错误），
子串判据全绿，用户粘进 `languages.toml` 才炸——**判据强度不足以支撑「生成件能用」这条承诺**。
（顺带实测：当前生成器是对的——四种根都能解析、括号平衡——但**没有人钉住它**。）

**③ 落地两件**：
- 常驻判据 `test_lsp.TestGeneratedConfigIsUsable`（三例）：① 四种根（POSIX / Windows / 含空格 /
  盘符+空格）下 Helix 生成件都能被 `tomllib` 解析，且结构正确（language-servers 指向 nf-lsp、
  command/args 对、路径里不得留反斜杠）；② Lua/elisp 块括号平衡（生成代码的冒烟检查）；
  ③ **文档里那段**（用户真正复制的东西）在三语里都必须是合法 TOML——判据直接读 `docs/lsp.md` 与
  en/ja 译件，而不是只读生成器。
- 门禁（check33 编辑器面）同步加强：`_client_config_issues()` 不再只查子串，**Helix 那份必须通过
  `tomllib` 解析**且 language-server 段结构对——这条在 verify 里跑，用的是**本机真实路径**
  （Windows 反斜杠因此每次都被真考一遍）。

**④ 语义边界（本波）**：没有任何协议/行为面变更，故**不动接入面卡版本**（版本跟行为走，判据加强不刷版本）。
这一条也写进审计，免得下次有人看见「改了 lsp.py 却没升版本」犯嘀咕。

## 四之二十九、同波追加（第二十九段，2026-10-08 续）：编辑器面补**折叠**（长档可用性的地基）

**先量再定（为什么这条值得做）**：本仓长档常见——`02_联动注册表.md` **1151 行**、`CHANGELOG.md` 1538 行、
`docs/terminal.md` 49 KB；而 LSP 面此前**没有折叠能力**（全仓 grep 无 `foldingRange`），编辑器里只能一路滚。
折叠的**真源我们本来就有**（标题结构 = 大纲判据的同一份口径），所以它是「派生自既有真源的能力」，
不是新造事实——这正是本仓对「新增能力」的一贯口径。

**实现（协议/实现/门禁/文档/证据五件齐）**：
- **协议**：`capabilities()` 增 `foldingRangeProvider`，并进 `_REQUIRED_CAPS`；准入表增
  `textDocument/foldingRange: (uri,)`。
- **实现**：`lsp_doc.folding_ranges()`（纯函数，与大纲共用 `HEADING` / `_FENCE`）——**标题小节** =
  标题行 → 下一个**同级或更高级**标题的前一行（到文末）；**代码围栏**整段；**单行区间不给**，
  **尾部空行不折**（折了看不见内容，只是噪声）。三处口径都写进 docstring。
- **门禁**：`lsp.check` 增 `_folding_issues()`——多标题文档必须给 ≥2 条区间，且不得出现空跨
  （endLine ≤ startLine 会被客户端忽略）。
- **文档**：`docs/lsp.md` 能力表加行 + 边界行改成「…+ 结构化引用 + **折叠**」，en/ja 同步，
  `nf locales --write` 重签。
- **证据**：帧级金标加 `foldingRange` 帧（应答 21 → **22** 条），并把 `foldingRangeProvider` 接进
  「声明能力 → 转写证据」映射表；常驻判据 `test_lsp.TestFoldingRanges` 五例（嵌套边界 / 围栏可折 /
  单行与空文档不给 / **围栏内的 # 不得成为折叠起点** / 协议层请求与缺参准入）。
- 接入面卡 2.6.0 → **2.7.0**。

## 四之三十、同波追加（第三十段，2026-10-08 续）：接入面卡的**命令承诺**也要在册

**最后一块「声明了没人核」的面**：`integrations/*/integration.json` 的 `entry.command` 此前只核「引用的件
在不在场」（`_PATH_TOKEN` 逐个查存在性）——把 `nf srve` 这种**拼错**写进卡里，件都在场、判据全绿，
用户照卡敲才发现命令不存在。

**修法（复用既有单一真相，不新造机制）**：`check()` 增一条——抽出 `entry.command` 里的 `nf <子命令>`
（`python scripts/nf.py <子>` 与裸 `nf <子>` 两种形态），与 **`prose_lint.cli_commands()`**（第 13 波
从文档命令面抽出来的同一份 CLI 注册表）对账；**读不到注册表就不判**（宁少不假）。

**判据（变异负例 + 不误报）**：`test_integrations` 三例——拼错的 `srve` 必被抓 / 在册的 `serve` 不得报 /
注册表不在场时不得误红。实测真仓：13 个接入面 issues 为空（`run` 与 `lsp`/`serve` 都在册；
`tui/nf.py --selftest` 与 `npx ninfenz` 形态正确地**不被当成 nf 子命令**）。

**语义边界**：本波只加强门禁（check38 子扫描），**无协议/行为变更**，故不动接入面卡版本（同第二十八段口径）。

## 五、五维自评

| 维度 | 本波水位 | 说明 |
|---|---|---|
| 静态可核验 | ↑ | 新增 4 个测试件、check33 编辑器面从布尔变协议行为；verify 全绿 |
| 动态可执行 | ↑↑ | 编辑器智能与站点工装**真跑**（真仓库件解析、node 工装常驻），不再是「件在场」 |
| 架构纯度 | ↑ | 符号索引为叶子模块、单一真相派生；歧义失败关闭；最小编辑自校验 |
| 资产密度 | → | 不新增内容资产（复用 registry / machine_contract / event_registry） |
| 文档可执行性 | ↑ | docs/lsp.md 能力表 + 配置生成 + 边界诚实标注；决策层与 MCP 文档回真源并有对账门 |

## 六、边界与不宣称

- 本件只证**内部链**（verify/单测/真跑工装）；外部装载、联网自检、npm 注册表事实均标为未核。
- 「生产级适配」按 STRATEGY §二 的五维定义，不引用任何外部项目或外部评价作论据。
