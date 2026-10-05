# NF Rust 引擎线（`engine/rust/`）

> **定位：只读快线的第三个实现面。**与 Python 侧（`verify.sh` + `desktop/src`）**并列**——不替代、不写盘、不改 `verify.sh` 基线。
> 治理范式同 `engine/dotnet/`（见 `decisions/ADR-0005-新增NET引擎线.md`）：**只读判据面 + 与 Python 真源逐字节对账 + 写面不实现**。

## 评审者速览（2026-10-04 现值）

**一句话**：本线是只读的**第二实现**，与 Python 真源**逐字节对账**；写面、执行层一概不碰。

### 目标门禁 `verify.sh`：**全绿**（2026-10-04 11:08 实测）

```
结果统计: PASS=70  WARN=0  FAIL=0
>>> 全部通过（WARN 仅提示非致命），变更可提交 <<<
exit code: 0
```

它是目标自己那条门禁（141 KB bash，两段式验收，`check1`–`check40`）。本机原本 `PATH` 里没有 bash，
实测走 Git 自带的 `C:\comfyui\Git\bin\bash.exe`（GNU bash 5.3.15）可跑。

> **留档一段曲折**：这条门禁自 round 22 起一直是红的——`protocol/conformance_report.json` 记录的
> `root=fe99e166…` 与当时语料实测 `06be4220…` 不符。查明是**并发会话改动语料**导致的漂移
> （报告件工作区干净；审计钩子实测本线对 `engine/` **零读取**，conformance 的输入面也不含
> `desktop/tests/`，故本线的改动不可能引起它）。修法是 `nf conformance --write`——那属**写在仓产物**，
> 与目标另两条「写面不碰」「不改变现有基线」冲突，故当初报为阻塞待裁。
> 后续并发会话自己重生了该报告，本轮复跑即 **PASS=70 / FAIL=0**。
> **这条红的始末一并记下**：它说明"门禁红了"先要分清是**自己的改动**还是**共享工作区里别人的改动**。

### `code_metrics`（代码规模/复杂度上限，棘轮冻结）

真源 142 行，**写面不移植**（`write()` 是显式冻结基线动作）。

两处陷阱：

1. **`worst_fn` 取严格大于** ⇒ 并列时"谁先被 `ast.walk` 到"决定结果。`ast.walk` 是 **BFS**，
   故度量收集器同样用 (深度, 前序) 还原 BFS 序。
2. **`lines` 走 Python 的 `splitlines()`**（`\v` / `\f` / `\x85` / `\u2028` 等也断行），
   不是 Rust 的 `lines()`。实测常见边界两者一致，但这行数要拿去和**冻结基线**比，
   差一行就是假红/假绿，故实现了 Python 语义版本 `pyval::splitlines_count`。

**已知偏差**：语法坏时真源记 CPython 的 `SyntaxError` 文本，本线只能给本线解析器的文本
⇒ **文本不可比**。分支判据里两侧都归一到 `<rel> <SYNTAX>` 后比较，**不假装文本相同**。

对账结果：`{issues, warns, stats}` **逐字节一致**（173 文件、`max_fn_cc=150`）。见对账门**面 15**。

### `purity_scan`（R1–R7 架构纯度体检）

**一次移植解锁三处**：`verify_report` 的 `purity` 判据、`purity-clean` 契约（**契约至此 27/27 全部移植**）、
`score` 的 `purity_clean` 信号（**信号至此 5/6 自算**）。

真源 530 行，**移植面按消费者界定**：`write`/`apply` 类写面、以及 `memo_pair`/`disk_cache`/逐件
findings 三层缓存**不移植**——缓存是纯函数优化，不改结论。

两处顺序陷阱（都影响逐字节对账）：

1. **R1–R3 的重复标题**取自 `dict` 的**插入序**（首次出现顺序），不是排序序——本线用 `Vec` 保序。
2. **R6 的命中标志推导**用 `call` 做两件事：整串在 `DANGEROUS_CALLS`、**末段**在 `METHOD_SINKS`。

`sys.stdlib_module_names`（R5 判"是否标准库"）由 `tools/gen_py_stdlib.py` 转录成
`src/py_stdlib.rs`（305 条）。**该集合随 Python 版本变**——换解释器后若表过期，
`purity-scan` 对账会红（这正是要的：宁可红，也不要静默用旧集合判"标准库"）。

对账结果：`nf-rs purity-scan` 与真源 `purity_scan.scan` 的 `{issues, stats}` **逐字节一致**
（含 R7 分层阶梯的 stats）。见对账门**面 14**。

### 内置 Python 解析器（AST 类判据的地基）

`purity_scan` / `code_metrics` / `asset_contract` 三条判据建立在 **Python 语法树**之上
（手写子集解析器复刻不了 CPython 的 AST 语义），故内置 `rustpython-parser 0.4` +
`rustpython-ast`（`visitor` + `unparse`）。实测依赖树**无** `windows-sys` / `windows-link` /
`iana-time` / `chrono` / `winapi` ⇒ 不触发 dlltool 陷阱。

**两处必须小心的坑（都实测踩到并已解决/证明）：**

1. **遍历顺序**：CPython 的 `ast.walk` 是 **BFS**，而 `rustpython-ast` 的 `Visitor` 是 **DFS**；
   真源把 `raises`/`modules`/`sinks` 的**列表顺序写进消息**。解法：DFS 时记录 `(深度, 前序序号)`，
   再按此排序——**对树而言与 BFS 序等价**。深度靠"调用 `generic_visit_*` 前后自己压/弹栈"得到。

2. **上游 visitor 有空实现**：`generic_visit_{comprehension,arguments,arg,keyword,alias,withitem,match_case}`
   在 `rustpython-ast` 里是 `{}`（**不下钻**），而 CPython 会遍历全部 `_fields`。
   逐构造探针实测漏收三类：`with ... as x:` 的 `context_expr`、关键字参数值、推导式的 `if`。
   已在自己的 Collector 里按 **CPython 的 `_fields` 顺序**补下钻。

**结论（可复现）**：全仓 **175 个源码文件**差分对账 —— `raises` 与 `modules` **逐字节一致**；
`sinks` 仅 1 处 unparser 括号差异（CPython 给生成器表达式当参数补括号，rustpython 不补），
且已用 `tools/check_ast_facts_inert.py` 对 **23,489 条 sink 候选**证明**命中标志序列完全一致**
——即该差异对本线判据无影响。**这一条是"有据"，不是"我认为"。**

### 质量纵深线（`quality_depth_scan`）

`nf-rs depth-scan` 移植真源 `quality_depth_scan.scan`：把 **13 个子扫描器**（载荷注册表 / 资产台账投影 /
指令步骤审计 / 概念图 / 产出形态 / 域包 / 组合包 / 资产密度 / 语义厚度 / 零引用普查 / 工具面 /
世界模型 / 数据槽）+ 4 个后置项聚合成**一条硬门**，任一子扫描 FAIL ⇒ 本扫描 FAIL。

对账结果：与真源 `quality_depth_scan.scan` 的 `{issues, stats}` **逐字节一致**（14 项统计、
规范 JSON 43,094 字符完全相同；零 issue 两侧一致）。常驻 oracle 就在
`engine/rust/src/quality_depth_scan.rs` 的 `tests::depth_scan_matches_truth_source`，
并在 `desktop/tests/test_rust_fastlane.py` 的 `COVERED_FACES["depth-scan"]` 登记
——快线那条「**不许有无人核的面**」的规矩，要求新加的命令面必须同时给出 oracle。

**它也是那批子扫描器的生产消费者**：没有聚合器时，`domain_pack` / `output_forms` /
`world_model` 等模块只有测试引用，同行的 `test_rust_module_wiring` 会当场判 FAIL（实测过）。

### 一条命令验证全部

```powershell
# ① 一条命令跑完全部门禁：面 1–15（逐字节对账 + 面 13「判据自身的不变量」），应 0 FAIL
pwsh -NoProfile -File engine/rust/check_parity.ps1 -Root <仓库根>

# ② 两侧各自的单元判据
cargo test --release --manifest-path engine/rust/Cargo.toml          # 232 条
python desktop/tests/test_rust_fastlane.py                           # 同行独立判据 20 条
```

> 门禁的 **PASS 条数会随语料变**（例如面 13 的不变量按实际面数逐条报），故这里只钉**面编号**
> 而不钉条数——写死一个会漂的数字等于给自己埋一条迟早要改的断言。

面 13 是三项**判据自身可信度**的不变量（原先要分别手工跑，现已并入——靠人记得跑的东西迟早会漏）：
自算面一致性（`check_native_sync.py`）、「没人核的代码面」普查（`audit_pub_readers.py`）、
未移植面的反向依赖（`audit_unported_consumers.py`）。三项都做过**反向对照**：
例如植入一个全仓零引用的 `pub fn`，13b 会报 `[FAIL] 存在全仓零引用的 pub 项（死代码）` 且门禁退出 1
——**守护确实会红**，不是摆设。

### 落地到什么程度

| 面 | 状态 |
|---|---|
| `receipts` / `stats` / `layers --verify` | **逐字节一致**（含退出码），冷测 **6.4× / 3.7× / 4.2×**（同序） |
| `conformance` 封缄内核 + 差分核对 | **逐字节一致**；27 条契约 digest 独立复核 27/27 |
| `conformance` 契约 | **27/27 全部**逐字节一致（含 `purity-clean`——随内置解析器一并移植） |
| `score` 内核 | **逐字节一致**（含 compare 与退出码）；**5/6** 信号源自算 |
| `verify_report` 内核 | **逐字节一致**（含 `root_digest`）；**22/28** 判据自算 |

### 没做的那部分，每条都有实证

- **需 Python AST**（不可做）：`purity-clean` · `purity` · `code_metrics` · `asset_contract`
  （最后一条是整套控制流分析，不是"顺带用一下"）。
- **需本地日历日期**（不可做）：`perf_budget` · `instruction_evidence`。真源注释明写本地日期是
  **有意语义**；而本机 `windows-gnu` 取本地时区要经 raw-dylib crate，其 `dlltool` 垫片是坏的（实测）。
- **需全量 27 契约实时重算**：`conformance_report`（本线 27/27）。
- **可做但体量大（不是边界）**：`depth_clean` —— `quality_depth_scan` 聚合 13 个子扫描器，
  本线已移植 5 个，余 8 个共 **5,513 行**，且**全都无 AST/日期/子进程依赖**。
  这一类必须与"不可做"分开记，否则后人会把"没做"误读成"不可做"。

### 三条最该先读的方法论

1. **"契约行一致"不等于"判据正确"**。真源在很多面上是真语料**全绿**的——两侧都输出空集，
   对账天然核不到错误分支。故对高风险面另做**分支级差分判据**（22 个面，生成器在
   [`tools/`](tools/README.md)，期望值从真源生成）。这套判据已真的抓到过东西：
   `preserve_order` 缺口、`intake` 漏一个 `%r` 引号——**都不是真语料对账能发现的**。
2. **判据的覆盖面本身也要被核**。`verify_report.call` 是 native 优先于 `--results`：
   自算集**少列一条**，该条分派断掉时不会红。这处盲区真实发生过，现由
   `check_native_sync.py` 变成机器可检的不变量。
3. **数字会随语料漂**。性能与计数都写明口径与复现脚本；换语料就重跑，别沿用旧数。
   本 README 曾被审计出 7 处过时陈述（含一处说 `score`/`verify_report`"未动"的严重低估），已全部修正。

## 这是什么

同一份语料上，本线用 Rust **独立复算**只读判据面，并与 Python 侧**逐字节对账**。

选 Rust 的依据是**内部实测**（本机 2026-10-03，同一语料 8,074 文件 / 807 MB），不是"语言偏好"：

| 维度 | Python 侧 | Rust 侧 | 判定 |
|---|---|---|---|
| 进程冷启动 | 33.3 ms 裸解释器 / `nf --version` 93.1 ms | **11 ms** | 见下「一处已修正的旧数」 |
| 目录遍历 | 275 ms（`os.scandir`） | 303 ms | **打平**——内核 I/O 受限，换语言不省 |
| 遍历 + SHA-256 全仓 | 4,828 ms | **1,130 ms** | **4.3×**——CPU 受限，真优势 |

**结论：本线只在 CPU 受限的哈希/解析面取收益；遍历面不取。**把这一点写明，是为了让后续加面时不被"Rust 一定更快"的直觉带偏。

**一处已修正的旧数**：进程冷启动原先记为「Python 36 ms / Rust 28 ms」——**Rust 那一侧高估了**。
2026-10-04 重测为裸解释器 33.3 ms、`nf --version` 93.1 ms、`nf-rs --version` **11 ms**。
旧值把 Rust 的地板说高了 2.5 倍，**反而低估了它的优势**；这类"看起来对我不利所以没人质疑"的数字
同样要重测——它会让后续判断（"换语言省不下启动成本"）建立在错的前提上。

后两行（目录遍历 / 遍历+SHA-256）是 **2026-10-03 用一次性基准脚本**测的，本轮未复现，
故在这里标明出处日期，不当成本轮的证据。

### 已落地面的实测收益（**2026-10-04 冷测复现**）

**口径**（可复现，脚本在 [`tools/measure_faces.ps1`](tools/measure_faces.ps1)）：
两侧都是**端到端 CLI**（含进程启动），真源侧设 `NF_NO_DISK_CACHE=1` 关掉持久缓存
——否则第二次起量到的是"热"数；各取 **min of 7**。

| 面 | Python 真源 | Rust 快线 | 倍数 |
|---|---|---|---|
| `stats --json` | 194.3 ms | **52.3 ms** | **3.7×** |
| `layers --verify --json` | 1053.6 ms | **252.3 ms** | **4.2×** |
| `receipts`（协议层回执） | 150.0 ms | **23.3 ms** | **6.4×** |

> 上一版记的是 3.9× / 7.1× / 3.4×（2026-10-03）。**数字会随语料漂**——语料被并发会话改动后，
> 旧数字就不再成立。本表连同口径一起留档，**复现方式写在表头**；换语料就重跑脚本，别沿用旧数。
> 其中 `layers` 从 3.4× 变成 4.2× 是语料变化所致，不是实现变化。

**`layers` 这一行是被自己的实测抓出来的**（务必留档）：第一版实现**比 Python 慢 1.5×**（1280 ms vs 857 ms）。根因是 `glob::expand` **每次调用都重走整棵子树**，而 `layers` 会对同一批 glob 反复展开（L1/L2/L3 各阶 + L6 + L9），`community/**/*` 那类大树被整棵重走多次。补上真源 `_expand_many` 同构的**两层缓存**（每子树只枚举一次 + 每 pattern 结果复用）后降到 247 ms，且逐字节一致性不变。**没有这次量测，这行会是一个被"Rust 一定更快"掩盖的回归。**

## 覆盖现状

| 面 | 现状（实测） |
|---|---|
| `nf receipts`（协议层回执单根 · RFC 6962 折叠） | **逐字节一致**：55,727 B / 同一 sha256；含 `subjects` 顺序与 `selfcheck` 折叠回根 |
| `nf stats`（自述数字实算 · `repo_stats.compute` + `check`） | **逐字节一致**：662 B / 同一 sha256；**退出码同真源**（有 issue ⇔ 1） |
| `nf layers --verify --json`（抽象阶梯体检 L1–L10） | **逐字节一致**：189 B / 同一 sha256；退出码同真源。含 `render_markdown` 渲染比对（L10）与 L6 反向 import 检测 |
| `nf conformance` **封缄内核**（裁决 → 防篡改报告） | **逐字节一致**：7,404 B / 同一 sha256（27 条契约 digest + RFC 6962 根 + verdict） |
| `nf conformance` **差分核对** | 喂真源自带摘要的报告对象，本线逐条重算 —— **27/27 一致**（真源摘要算法获独立复核） |
| `nf conformance` **已移植契约** | **27/27 逐字节一致**（含 digest）：`canonical-digest-determinism` · `decisions` · `declaration` · `audit` · `doc-kinds` · `event-backing` · `handover` · `knowledge-sources` · `library-projection` · `library-verify` · `modeling` · `module-signature` · `patterns` · `postmortem` · `public-surface` · `schema-clean` · `state-front` · `st-quality` · `rfc-heads` · `cognition` · `assertions` · `endpoint-contract` · `io-types` · `type-backlog` · `mcp-package` · `pipeline-dryrun`；未移植 id **显式缺席**（退出码 2，不伪造结论） |
| 单元判据 | 202 条（Merkle、CPython JSON 排版、**CPython 浮点 repr（含正中平局）**、Python falsy 口径、glob 子集、**YAML 子集**、**自研 frontmatter（首个冒号切分）**、**bullet 块切分**、断言四算子、RFC 头与环检测、Python 词法剥离、渲染器、marker 区、头部 8 行窗口、`**` 追加语义） |
| 常驻回归 | `desktop/tests/test_rust_fastlane.py`（同行会话所建，独立实现；含判别力自证） |

### 分支级差分判据（**"契约行一致"不等于"判据正确"**）

真源在很多面上**是真语料全绿的**——`schema-lint`（check28 0 issues）、`knowledge`（三条子判据各 0）、
`coupling`（固定几组环/SDP）、`workflow_policy`（0 issues / 0 warns）。这些面做字节对账时，
**两侧都输出空集**：对账天然核不到错误分支。

故对高风险面另做**分支级差分判据**：构造一个逐形态/逐分支踩的合成语料，用真源跑出逐条消息，
再钉成 Rust 判据。生成器都在 [`tools/`](tools/README.md)（`gen_*_branches.py` / `gen_*_expected.py`），期望值**从真源生成、勿手改**。

| 面 | 夹具踩的形态 | 结果 |
|---|---|---|
| `schema_lint` | 280 条合成 `instance × schema` | 逐条一致 |
| `knowledge` | 14 条 transform + 6 条 usage 分支（含 1 条**全绿样本**证明不空转） | 逐条一致，并**抓到 `preserve_order` 缺口** |
| `coupling` | 10 种 import 写法（普通/多别名/点号模块/相对无模块/相对 core/相对带模块/括号多行/别名/字符串与注释里的假 import/`__init__` 忽略） | deps·Ca·Ce·I·环·SDP 全一致 |
| `workflow_policy` | 未钉 SHA / 缺版本 / 本地豁免 / 钉了带注释 / 无注释 / 缺 permissions / write-all / 缺 timeout / 全绿 / 非 .yml 忽略 / 依赖已钉与未钉 | 6 issues + 1 warn + stats 全一致 |
| `audit` | 无审计头(legacy) / verdict 越词表 / date 非法 / subjects 无冒号 / 被审对象不存在 / 摘要不符 / 摘要相符 / accepted_by 缺合法 accepted_at / 签收双要素齐(全绿) | 6 issues + 1 warn + stats 全一致 |
| `license_gate` | 空许可列 / 表达式越词表 / `未声明` / 无内联 / 双源不一致 / 单 id 全绿 / SPDX 表达式合法 / 单元格过少不计入 | 2 issues + 4 类 WARN + stats 全一致 |
| `payload_registry` | schema 自校验不过 / 死注册 / 漏登 / `fields` 缺失计 pending / `subscriptions` 计入 used | 3 issues + stats 全一致 |
| `modeling` | 词表（schema / status 词表 / id 重复 / 值不足 / 值重复 / alias 撞车 / probe.kind 不在册 / json_path 断链 / 真源漂移 / python_attr 已登记）· 规范件（缺 path / 不存在 / 无锚定 / covered_by 指向不存在 check / 合法 / 与说明件重叠）· 数据契约（schema / rule_prefixes / id 重复 / artifact 缺 / status 越词表 / 缺 owner / 缺 freshness / 指向不存在 check / 指向不存在断言 / 无法解析 / 合法） | **27 issues 逐字且同序一致** |
| `intake` | schema / updated 非日期 / 缺 after_action / mode 非法 / author_only 白名单空 / 缺 index_label / label 不在 INDEX / 合法 mode ×2 / 缺机器人 / 未引用声明件 | 8 issues + stats 全一致（**并抓到一处 `%r` 引号缺失**） |
| `rating_gate` | 三种声明状态（齐 / 缺词表 / 缺件）× 缺 rating / 越词表 / 合法 | 逐场景 issues + vocabulary + counts 全一致 |
| `declaration` | 五路版本真源全在场 / 声明与真源不一致 / 声明无法核验项 / 范围路径不存在 / 排除 glob 无匹配 / 排除「允许不存在」豁免 / scope ∩ 排除重叠 | 9 issues + 三项计数全一致 |
| `decisions` | 缺 id / id 不合法 / id 与文件名不一致 / 编号重复 / 缺必填 / status 越词表 / 日期非法 / 缺正文段落 / 证据空项 / 证据指向不存在 check / 证据无法解析 / accepted 未被回执锚定 / superseded 缺 superseded_by / superseded_by 指向不在册 / 取代链成环 / supersedes 指向不在册 | **38 issues 逐字且同序一致** |
| `handover` | 三场景（声明坏 / 缺声明 / 无件）× 缺必填 / status 越词表 / 日期非法 / 正文缺段落 / 未决项为空 / 未决项缺判据 / `refs` 字符串形态 / 指向不存在 check / 在册 check / ADR 豁免 / 无法解析 | 12 issues + 件数/未决项数全一致 |
| `state_front` | 三场景（kitchen / 缺声明 / 空声明）× schema / 族规则缺 glob / 族成员不足 / 族内件未过 condition-first / 条目缺 path / 登记件不存在 / 登记件未过 condition-first | 12 issues 全一致 |
| `patterns` | 三场景（kitchen / 撞号 / 无包）× 缺 frontmatter / 缺必填 / id 与目录名不一致 / id 重复 / status 越词表 / rules 为空 / applies_to 通配无匹配 / 路径不存在 / evidence 缺失·空项·指向不存在 | 逐场景全一致 |
| `drill_fidelity` | 四场景（kitchen / 空 / 坏回合样本 / 坏执行集）× 执行演练四条硬断言各自的命中与不命中、`expect_captured` 未满足 ⇒ 保真度不足；回合级 R-R1 缺引用 / R-R2 无推进 / R-R3 越集（含同尾豁免）/ 跳号 / 无回合标记；声明与实测不一致 ⇒ 未复现声明；坏 JSON | 逐场景 issues + cases/passed/fidelity/exec_sets/round_samples 全一致 |
| `endpoint` | 三场景（kitchen / 全绿 / 缺契约）× schema / status 越词表 / id 重复 / method 越词表 / method+path 重复 / streaming 无 SSE 约定 / maps_to 的 MCP 工具不存在 / 无法解析为现存 CLI / deprecated 非布尔 / 未实装却声明弃用 / 无弃用约定 / sunset 不合规 / 缺 replacement / replacement 指向不存在端点 / 悬空 sunset / 无幂等语义 / 幂等例外指向不存在 / 重复登记 / mode 越词表 / key 越词表 / required 但无幂等语义 / 缺 why | 21 issues + stats 全一致 |
| `io_types` | L0 件 / 未标 io_types / 类型越词表 / 输出键集不一致 / 输入键集不一致 / 类型不匹配 / `state` 与 `untyped` 跳过 / 含冒号的跨包键 / 显式空段 / 全绿 | **两侧都比**（2 issues + 5 warns）+ stats + coverage 一致 |
| `type_backlog` | 无声增长 / 缺台账 / 台账不可解析 / 台账过期 / 全绿 | 4 场景 issues + stats 全一致 |
| `cognition` | 术语表（schema / rules 空 / 无 term 条目 / 术语重复 / 缺 definition / source 不存在 / 未在 source 中逐字出现 / used_in 不存在 / used_in 未逐字出现 / 全绿计入 uses）+ 执行分档（schema / id 重复 / 缺 required_blocks / 无实例 / 实例不存在 / 缺结构块） | **18 issues 逐字且同序** + detail + 两项 stats |
| `doc_kinds` | 常量表一致性（`kind_coverage` 忽略 root、只用真源固定常量 ⇒ 本线漏转录即报）+ `kind_rules`：写法不符 ⇒ WARN / 合规 ⇒ 不 WARN / 路径不在场 ⇒ 跳过 | issues·warns·detail 全一致 |
| `library_verify` | 缺 frontmatter / 缺必填键 / id 与文件名不一致 / license 不在词表 / status 不在词表 / superseded 缺 superseded_by / 指向不存在 / 指向自身（成环）/ 三个日期键格式非法 / attestation 非 64 位十六进制 / 缺 sources / **缺推荐键 ×7** | 13 issues + 70 warns 逐字且同序一致 |
| `public_surface` | 驱动器号+`\Users\` / `/Users/` / `/home/<user>`；后缀不在白名单 ⇒ 跳过；**前一个字符是字母数字 ⇒ 后顾断言不命中** | ok + detail 字面 + 前两条一致 |
| `postmortem` | 四场景 × 引用指向不存在 check / 引用无法解析 / 缺必填 / status 越词表 / 日期非法 / 正文缺段落 / **命中指责性归因词** / 根因段未指向机制 / 行动项为空 / 缺负责人 / 缺判据 / closed 未被回执锚定 / 声明 schema / sections / 词表为空 | 逐场景全一致 |

`coupling` 那条尤其重要：真源用 `ast` 抽 import，本线是**词法近似**——10 种写法逐一对齐，
这条近似才算有了直接证据（原先只有"真语料上结论相同"这种弱证据）。

**这套判据已经真的抓到过东西**（都不是真语料对账能发现的）：

- `preserve_order` 缺口（Python `dict` 是插入序，`serde_json` 默认排序键）；
- `intake` 的 `通道 … mode 非法：'sometimes'` —— 真源用 `%r` 带引号，本线漏了引号。
  该分支**真语料永远踩不到**（那边 mode 全合法），所以字节对账一直是绿的。

**避开依赖"当天日期"的分支**：`library_verify` 的夹具刻意只踩**日期格式**（`非 YYYY-MM-DD`），
不碰 `doc_hygiene` 那种「超过 N 个月未更新」——**那类夹具会随日历变红**，是把不稳定性埋进判据。

**期望值只能来自真源暴露的面**：`public-surface` 的真源 `_c_public_surface` **只返回 `(ok, detail)`**，
而 `detail` 是 `"; ".join(bad[:2])`——**它把清单截断到前两条**，总条数根本不在外露面上。
故那条分支判据只断言 `ok` / `detail` 字面 / 本线 issues 的**前两条**与之相同；
我一开始顺手断言了"总条数 == 2"（从 detail 数出来的），**那是我自己发明的期望值**，已删。
**判据宁可少断言，也不许把"我以为的"当"真源说的"。**

**移植面按消费者界定**：真源 `handover` / `state_front` / `postmortem` 的 `scan` 都还返回 `warns`
（「门禁空转」一类提示），但**本面无消费者**（契约只看 issues），故本线结构体未纳入——
期望值里的 `want_warns` 只作记录、不参与断言。`endpoint` / `mcp_package` / `drill_fidelity` 同此处置；`io_types` 的 `warns` 例外**保留**——它含实质判据（键集对齐），故由分支级判据覆盖，并在结构体上写明 `allow(dead_code)` 的理由。这比"为了对称而多移植一个没人读的字段"更省，
也避免留下**没有判据覆盖的代码面**。

### 对账门的**自算集**必须与快线同步（一处真实盲区）

`verify_report.call` 是 **native 优先于 `--results`**。后果：喂入集里**多列**一条不会报错
（喂进去的值被自算覆盖），但**少列**一条就有实质危害——**只要该条的分派将来断掉，
就会静默回落到喂入值，门禁照样全绿**。

实测（2026-10-04）：对账门面 12 与同行常驻判据的自算集都**停在旧状态**（分别是 11 条与 19 条），
缺了后来移植的 10 / 2 条。之前的几次「同步」用 `String.Replace` 打在了不存在的目标串上、**静默空转**。
现已两处都同步到 **26 条**，并写明「必须与自算面同步」的理由。**更进一步**：加了 [`tools/check_native_sync.py`](tools/check_native_sync.py) 把它变成机器可检的不变量——喂空 `--results` 反推真实自算面，再与两处手写清单比对，不一致即退出码 1。

### `drill_fidelity` 的分支级判据（本已补上）

真语料上它**全绿**（69 例 / 8 集 / fidelity=1.0 / 5 个回合样本）⇒ 对账核不到错误分支。判定词表随 fixture 的 `lexicon` 键走（`p07_en_drill_cases.json` 为英文集），缺省仍是中文内置词表。
现由 `tools/gen_drill_fidelity_branches.py` 生成分支级判据（标记区间替换），逐分支踩：
执行演练四条硬断言各自的命中与不命中、`expect_captured` 未满足 ⇒ 保真度不足；
回合级 R-R1 缺引用 / R-R2 无推进 / R-R3 越集（含「带前缀 tok ↔ 无前缀 allowed」同尾豁免）/
跳号 / 无回合标记；声明与实测不一致 ⇒ 未复现声明；找不到用例 / 找不到样本 / 坏 JSON。
四个场景的 issues 与 `cases`/`passed`/`fidelity`/`exec_sets`/`round_samples` 全部逐条一致。

### 剩余面的边界理由（**逐条实证**，非断言）

`nf verify-report` 有 28 条判据。下面这 6 条不做，**每条都有实测证据**——
写在这里是为了让「为什么不移植」也可被复核，而不是一句"边界外"了事。

| 判据 | 挡住它的东西 | 实证 |
|---|---|---|
| `purity` | **Python AST** | `purity_scan.py` `import ast`，R1-R7 与 L1-L4 阶梯都建立在语法树与调用图之上 |
| `code_metrics` | **Python AST** | `code_metrics.py` `import ast`，规模/复杂度按 `ast.walk` 统计 |
| `asset_contract` | **Python AST**（且是**控制流分析**） | `asset_contract.py` 有 `_scan_block` / `_none_deref` / `_always_exits` / `_guard` / `_derefs` 等十余处 `ast.*`——不是"顺带用一下 AST"，而是整条判据就是一套数据流检查 |
| `perf_budget` | **本地日历日期** | `_dt.date.today()`，且源码注释明写「本地日历日期是**有意语义**（UTC 会在跨零点给出错误「今天」）」——所以**不能**用 UTC 顶替 |
| `instruction_evidence` | **本地日历日期** | 同上，`_age_days(stamp, _dt.date.today())` |
| `conformance_report` | 需要**全量 27 契约的实时重算** | `verify_committed` 的判据是「在盘报告 == 实时重算」，而实时重算会跑**全套契约**（含 `purity` 等）——本线 27/27，缺的正是 `purity-clean` |

**为什么"本地日历日期"是硬边界**：本机工具链是 `x86_64-pc-windows-gnu`，取本地时区要经
`windows-sys` / `iana-time-zone` 一类 raw-dylib crate，而它们的 `dlltool` 垫片在本机是坏的
（实测：`chrono --no-default-features --features clock` → `error calling dlltool 'dlltool.exe': program not found`）。
`std::time` 只给 UNIX 纪元秒，**给不出本地偏移**——拿不到本地日期，就复刻不了这条语义。

**一处曾经的误判（已改正）**：`drill_fidelity` 我起初记为「需要子进程」，本轮逐行核实后发现是**错的**——
它是纯读 JSON 夹具 + 纯断言/正则（`execution_drill` 139 行 + `round_drill` 43 行 + 本体 109 行，合计 291 行，
无 AST、无子进程、无日期）。现已移植。**这条误判说明"边界理由"本身也必须被核**，不能靠印象传承。

### `nf score` 剩余 2 个信号源的理由（同样逐条实证）

`score` 6 个信号源里本线自算 4 个；余下 2 个：

| 信号源 | 挡住它的东西 | 实证 |
|---|---|---|
| `purity_clean` | **Python AST** | `purity_scan.py` 530 行里 **22 处 `ast.`**，R1-R7 全靠语法树 |
| `depth_clean` | **体量**（**不是**边界） | `quality_depth_scan.py` 聚合 **13 个子扫描器**；本线已移植 5 个（`asset_density` / `asset_ledger_projection` / `conformance_scan` / `instruction_step_audit` / `payload_registry`），余 8 个合计 **5,513 行**：`domain_pack` 1928 · `output_forms` 1293 · `pack_combo` 1154 · `world_model` 622 · `concept_graph` 345 · `world_slots` 74 · `tool_face` 59 · `payload_consumer` 38 |

**这 8 个全都 `ast` / `datetime` / `subprocess` 命中为 0**，且经反向依赖普查确认**没有一个落在已移植面的判据链上**（`tools/audit_unported_consumers.py`）——即它们**不是**边界类、也**不是缺口**，
纯粹是量的问题。这个区分很重要：它意味着 `depth_clean` 属于"**可做但没做**"，
而不是"**不该做**"。两者在遗留清单里必须分开记，否则后人会把"没做"误读成"不可做"。

（同理，`conformance` 剩的 6 条未移植契约也多是量的问题，不是边界问题。）

### `drill_fidelity` 的已知偏差（无法逐字比对，单列说明）

真源那四处的失败态与快线**同判红**，但**状态或文本**对不齐（真语料上均不触发）：

1. **坏 JSON 的执行集**：真源 issue 尾部是 CPython `JSONDecodeError` 原文
   （如 `Expecting value: line 1 column 13 (char 12)`），本线措辞自拟 ⇒ 只断言前缀，不复刻。
2. **JSON 合法但顶层非对象**：真源 `data.get(...)` 抛 `AttributeError` ⇒ 整条**记 ERROR**；
   本线当作「无 cases / 无样本」继续 ⇒ 记 **FAIL**。
3. **`cases` / `allowed` 显式为 `null`**：真源 `for case in None` 抛 `TypeError` ⇒ ERROR；本线按空集处理。
4. **Unicode 数字回合号**：Python `int("٣")` = 3；本线只吃 ASCII 数字，按 0 计。

### 生成器的可重跑性（`tools/`）

生成器**必须能反复重跑**：真源改了措辞 → 判据红 → 重跑生成器刷新期望值。
首版写成「已存在就跳过」，结果改一次夹具后期望值刷不进去（实测踩过）。
现统一为**标记区间替换**：

```
    // >>> GENERATED by tools/gen_decisions_branches.py（勿手改；重跑生成器覆盖本段）
    ...判据块...
    // <<< GENERATED
```

### 已知偏差（无法逐字比对，单列说明）

`modeling` 的词表若声明了一个**未登记的 `python_attr` 探针**（如 `core.nope.X`），
真源 `importlib.import_module` 会直接抛 `ModuleNotFoundError`，整条判据记 **ERROR**；
本线返回一条显式 issue，记 **FAIL**。两边**都是红的**，但状态不同——这条无法逐字比对，
故不塞进逐条对账的夹具（真正需要它时，本线会以显式 issue 报出来，不会静默放行）。

`declaration` 的**基线**一路：真源写的是 `from core import quality_baseline as qb`——读**安装态的模块**，
与 `root` 无关（实测：夹具根写 `EXPECTED_CHECKS=2 / PASS=3`，真源仍报真仓库的 `40 / 70`），
即 `scan(root)` 并非 `root` 的纯函数。本线是**从 `root` 读**的（更纯）。
在真仓库上两者一致（`root` 就是仓库根），故契约行照旧逐字节相同；只有传给别的 `root` 时才分叉。
这是一处**有意保留的分歧**：与其复刻一个纯度 bug，不如把「结论只依赖 root」这条性质守住。
夹具里该路改用真仓库的值，使分支本身仍可比。
### `preserve_order`：一个只有"逐条踩分支"才抓得到的保真度缺口

`knowledge-sources` 在真语料上是**全绿**的（三条子判据各 0 issues）——只靠契约对账，
**错误路径一条也核不到**。为此构造了一个逐条踩分支的夹具，期望值由
`tools/gen_knowledge_expected.py` 从真源生成（14 条 transform + 6 条 usage 消息），
其中**第 5 条是全绿样本**，用来证明这套判据不是空转。

判据立刻抓到一个真缺口：**Python 的 `dict` 迭代是插入序，而 `serde_json` 默认用 `BTreeMap` ⇒ 键被排序**。
`verify_usage` 按 `counts.items()` 逐键报 issue，排序后**消息次序与真源不同**。修法是给
`serde_json` 开 `preserve_order`（键序改为 `IndexMap`）。这是一处**全局性改动**，故全量回归过
（34 项 PASS / 0 FAIL，无副作用）。

教训：**"契约行一致"不等于"判据正确"**。真源全绿的判据，其错误分支必须用合成夹具单独核——
这和 `subset_validate` 那次的差分测试是同一条道理。
### 契约表的**退出码语义**（一处我自己埋的判定错误）

对账门（面 5）与同行常驻判据**都**曾写「已移植契约 rc≠0 即不一致」。这是错的：**真源自己就会判某些契约
`ok=false`**（实测 2026-10-03：`audit` 因并发会话改了 `verify.sh`，旧审计的 `subjects` digest 不再匹配）。
两个后果：① 误报；② 更糟——**判 false 的那一侧，行内容从未被比对过**（`rc≠0` 直接 `continue` 了）。

正确判据是「**rc == 真源 ok 的映射**（true→0 / false→1）**且**行照比」。
两侧都已改正；改完后门禁从「32 PASS + 1 FAIL」变成「33 PASS + 0 FAIL」，且 false 侧现在真的受核。
### `verify_report` 内核（门禁的机器可读出口）

真源把 **28 条判据**（各自调一个 core 扫描器）聚合成 `protocol/verification_report.json`：
逐条归一到 `(issues, warns, stats)` → 定 status → 汇总 counts + 声明面 → 主体规范化 sha256 作
`root_digest` → 按 `indent=2, sort_keys=True` 渲染。本线已实现该内核，**逐字节一致含 `root_digest`**。

**已自主算出 22/28 条**：`schema` / `doc_markers` / `baseline` / `self_stats` / `payload` /
`assets_ledger` / `instruction` / `key_naming` / `intake` / `library` / `library_projection` / `rating` /
`audit` / `workflow_policy` / `judgement_coverage` / `license` / `coupling` / `contract` / `knowledge` /
`conformance` / `receipts` / `drill_fidelity`。
其余 6 条由 `--results` 喂入各自的 `(issues, warns, stats)`——与 `score` 的 `--signals` 同一增量法：
**每移植一个扫描器，喂入面就小一格，内核不动。**

`conformance_scan` 一次解锁**两处**：`verify_report` 的 `conformance` 判据 **与** `score` 的
`conformance_clean` 信号（权重 0.20）。故 `score` 的喂入面同步收窄到 **2 个信号**
（`purity_clean` / `depth_clean`）——**能自算的一律自算，喂入面越小越不容易掩盖分歧**。

**移植面刻意最小化**：`contract`（`machine_contract`）真源的 `parse_header` 还返回 类别/层位/依赖/
发布/订阅，但 `scan` **只用到 `id`**——其余字段只喂给 `apply` / `apply_outputs` / `derive_outputs`
三个**写面**（本线不碰）。故本线只移植 id 推导那一条路径：既够用，又把**没有判据覆盖的代码面压到零**
（写了也没人能核）。

### 测试夹具的隔离（一处实测事故）

本仓常有并发 agent 会话，两边都会跑 `cargo test --release`；而夹具此前写死在
`target/test-fixtures/<名>`——两个进程会互相 `remove_dir_all` + `create_dir_all` **同一目录**，
表现为**随机几条判据同时变红、单独复跑即全绿**（实测一次 5 条）。

这正是 AGENTS.md 点名的「测试非隔离、共享固定临时路径」那一类根因——**不能用重跑糊过去**。
现收敛到 [`crate::testutil::fixture`]：每个夹具带**进程号 + 自增序号**。
验证方式不是"再跑一遍看看"，而是**三份测试二进制并发跑**，全绿（159/0 × 3）。

### 本线**刻意不做**的三类（边界，不是欠账）

1. **需要宿主语言解析器的**：`code_metrics`（Python AST 量圈复杂度/函数长度）、`purity_scan`（474 行 AST）。
   移植它们等于自造一个 Python 解析器，代价与脆性远超收益。快线只做**不依赖宿主解析器**的重只读扫描。
2. **需要本地日历日期的**：`perf_budget` / `instruction_evidence`（真源用 `date.today()` 算「记录是否过期」）。
   **这条是实测证实的，不是推测**：给 `Cargo.toml` 加 `chrono --no-default-features --features clock`
   → 拉进 `iana-time-zone` → `windows-*` → `cargo build` 报
   `error calling dlltool 'dlltool.exe': program not found`，正是本线早先记下的 **raw-dylib/dlltool 陷阱**。
   为一个「今天是几号」引入时区依赖树不划算，故不做（已回滚依赖）。
3. **需要跑子进程/写盘的**：`drill_fidelity`（要跑两套演练）、`conformance_report.verify_committed`
   （要跑全部 27 条契约）——属于执行/写面，不在只读快线范围。

### 一处"近似"如何自证

`coupling` 真源用 `ast` 抽 import；本线用**词法抽取**（剥注释与字符串后解析 `import` / `from … import …`，
含相对导入与括号多行）。这是近似——但它**不是悄悄近似**：任何分歧都会改变环/SDP 集合，
而这两个集合是与基线**逐条**比对的，故分歧必然以「新增环/新增 SDP 违例」的形式在对账面上暴露。
真语料上两侧得出同一组环与违例（面 12 逐字节过），这条近似因此有了实证。

`judgement_coverage` 这条值得单说：它抓的是 **"全 check PASS" 的盲区**——core 里有模块暴露了
`scan()` 却没有任何消费者，门禁全绿并不代表每条判据都在跑。真源的**精度纪律**我照抄了：
只认「真消费」信号（`NAME.scan(...)` 属性调用 / `from core import NAME` / 注册表里的带引号模块名），
**不认「文件里提到过该名字」**——真源上一版按裸名字匹配，把例外表自己的说明文字当成了消费方，
产生 5 条假「例外失效」。本线另做了一处**不改语义**的优化：真源对每个候选名把所有 core 文件重读
一遍（O(n²) 次读盘），本线把文本读一次缓存复用。

`library` 是本轮的关键路径：它自己占 2 条（`library` / `library_projection`），
后面还压着 `rating`（本轮一并拿下）与 `audit`。移植时连带做了它的**叶子件** `library_entries`
（条目读取 + 规范摘要——真源当年专门拆出来断 `receipts ↔ library` 的双向依赖）。
`entry_digest` 的自指避免性质已单列判据：**签名行的增删与取值都不得改变摘要**，
否则每次落签都会自我失效。另有一条 fail-closed：条目若带 `anchor_scheme`，
本线未移植 `attest.verify_digest_anchor`，故**如实报 issue 而不冒充通过**
（真源当前 3 条馆藏里 0 条带锚）。

已移植的这几条都是**零 core 依赖**的小件；对账走面 12 的整篇报告逐字节比对（不另开 CLI 面，
故不新增无人核的面）。其中两处口径值得留档：

- `key_naming` 真源用 **`rx.match(key)`**——只锚起始、不锚结尾。Rust 的 `is_match` 是任意位置匹配，
  直接用会把 `XABC` 判成匹配 `ABC`。本线显式包成 `^(?:pattern)`。
- `asset_ledger_projection._file_keys` 与 `asset_density._keys_of` **不是同一套口径**（各自真源如此）：
  前者字符集 `[A-Z0-9_]`（**不含连字符**）、头窗 8000、`##` 走 `re.M`；后者含连字符、头窗 6000。
  抄成另一套会静默改变键集，故单列判据钉住。

有一处口径极易踩空：`root_digest` 的源串是 CPython `json.dumps` 的**默认分隔符**
（`", "` / `": "`，**带空格**），不是紧凑模式，也不是 `indent=2`。差一个空格摘要就全变。
为此给 `pyjson` 补了第三种排版 `dumps_default`，并单列判据钉住。
### 行尾约定（**重要偏差披露**）

本线所有输出统一为 **LF、无 BOM、文末有换行**。

需要如实说明的是：**真源 CLI 在 Windows 上通过 `print()` 输出时会把 `\n` 翻成 `\r\n`**
（`scripts/nf.py` 只 `reconfigure(encoding="utf-8")`，未管 `newline`；实测 `nf score --json`
的 stdout 含 59 个 CR）。本线的对账基准取自真源**内容字节**（与真源自己写文件时用的
`newline="\n"` 一致），**不是** Windows 控制台文本翻译后的 stdout。

- 影响面：`nf-rs <面> | 管道` 的字节与 `python scripts/nf.py <面> | 管道` 在 Windows 上**行尾不同**；
- 在 Linux/macOS 上真源的 `print()` 也产出 LF，两侧一致；
- NF 自己写盘的所有产物都用 `newline="\n"`，故 LF 是本仓既有的产物约定。

**这是刻意选择，不是疏漏**——若需要与 Windows stdout 完全一致的字节，应显式要求。

### `score` 内核与 `asset_density` 扫描

`nf-rs score` 复刻真源 `regression_score.py`：6 路加权信号（权重和 1.0）、`_penalty` 封顶、
`compare` 的**单信号回落判定**（no silent worsening：总分不降掩盖不了单信号恶化）、
审计例外折算的**整体门预算释放**、以及 `round(x, n)` 的 **half-to-even** 十进制舍入
（`pyfloat::round_to`：用定精度格式化再解析回，而非 `(x*10^n).round()/10^n`——后者是
half-away-from-zero 且引入二次误差）。

6 个信号源里本线已自主算出 4 个（`doc_hygiene` / `asset_density` / `schema_lint` / `conformance_scan`）；其余 2 个
（`conformance_scan` / `purity_scan` / `quality_depth_scan`）由 `--signals`
以**计数**喂入，**缺键 = 扫描器不可用**——与真源 `_count` 的哨兵语义一致
（**不可用 ≠ 零问题**：真源按 0 分计并记 issue，本线同）。随着扫描器逐个移植，
`--signals` 的输入面会缩小，直至 `nf score` 完全自主。

`nf-rs density` 移植 `asset_density.scan`：文件名令牌 ∪ 正文头 6000 字的三路键声明
（反引号 / JSON 键 / 标题键）。真源注释记着一次实测教训——早先的字符集 `[A-Z0-9_]`
看不见**带连字符**的条目键（如域包的 `C01-01`），密度被系统性低估；本线四路取齐。
（Aho–Corasick 的 `usage_scan` / `thickness_scan` 是另两个面，**不在本次范围**。）

### `schema_lint`（check28 协议件子集校验）

真源是**自实现的 JSON-Schema 子集校验器**：`SUBSET_ALLOWED_KEYS` 之外的关键字一律 FAIL
（防止「校验器声称子集却静默忽略语义」的假绿），再用它校五张面——模块契约围栏 / registry 投影 /
管线声明 / community 协议声明 / 资产台账。本线已全量移植，是 `score` 的 `schema_clean` 信号源（权重 0.20）。

**真仓库 check28 是全绿的（0 issues）⇒ 光靠对账抓不到校验器自身的 bug。**
为此加了 `nf-rs schema-validate`（同 `pyval reprf` 的路数）：在 280 条合成 `instance × schema`
上逐条比对两侧的消息文案，**0 不一致**，并固化成对账门的面 11。

**未移植的近似（如实标注）**：真源把底层异常文本（JSON 解析失败等）拼进 issue，本线的错误措辞是自拟的。
正常仓库上走不到这两条分支。

### 遍历性能：三处实测修正（务必留档）

**① 错误对比口径（同一个坑踩了三次，务必留档）**：真源在这条路径上有**三层**缓存——
`memo_pair`（进程内 + 持久）、`schema_lint._DOC_LINT_CACHE`、以及 `conformance_scan._FENCE_CACHE`
（围栏解析，被 `schema_lint._fence_yaml` 借用）。只清 `_DOC_LINT_CACHE` 时仍会命中围栏缓存，
于是三次都得到「Rust 更慢」的假结论。**正确做法：测量前把这几层一起清空**，
两侧都走真正的冷算。（清干净后 `schema_lint` 是 1.48× 更快。）

**② 按段定深遍历（已被 ④ 取代，留作过程记录）**：`glob` 早先一律「把前缀子树整个递归枚举，再用正则过滤」。
对 `community/*/assets/*.md` 这种窄面，前缀只到 `community` —— 为了找 360 份资产件，
把整棵 community（2191+ 件）走了一遍。改为：无 `**` 时候选路径**段数恒定**（`*` 只吃一段），
只走到该深度即可。**`density` 155 → 109 ms、`schema_lint` 396 → 191 ms。**

**③ 正则编译缓存**：`subset_validate` 的 `pattern` 分支起初每次校验都 `Regex::new`，
而 Python 的 `re` 自带编译缓存（512 条）⇒ 编译成本被乘了几千倍。加缓存后 606 → 393 ms。

**④ 逐段字面剪枝 + 全递归清单优先**：无 `**` 的模式改为**逐段走**——字面段（`assets`）直接下钻，
只有通配段才列目录，列出的清单按目录缓存供其它模式共享。**但必须先查同前缀的全递归清单**：
`layers` 里 `community/**/*` 本来就要整棵走一遍，那几条 `community/*/…` 窄模式白捡的
「过滤已缓存清单」被换成「各走一遍目录」后，`layers` 从 257 退到 453 ms。恢复该优先路径后
**243 ms / 3.60×**。收在 [`glob::Cache`] 的三层（整模式 / 单层目录 / 全递归子树）。

### 性能现状（min of 7，同机同语料；**冷算口径**）

| 面 | 真源（冷算） | 本线 | |
|---|---|---|---|
| `conformance` 封缄（27 条） | 1502 ms | **11 ms** | 130× |
| `receipts` | 118 ms | **20 ms** | 5.9× |
| `stats --json` | 193 ms | **50 ms** | 3.9× |
| `layers --verify --json` | 877 ms | **244 ms** | 3.60× |
| `schema_lint`（check28） | 278 ms | **188 ms** | 1.48× |
| `asset_density` | 88 ms | **89 ms** | 0.99× |

口径说明：真源侧**每次测量前清空其全部模块级缓存**（`_DOC_LINT_CACHE` / `_FENCE_CACHE` /
`_BODY_CACHE` / `_KEYS_OF_CACHE` / `_FILE_COUNT_CACHE`），两侧都走冷算——这才是可比的算法口径。
`asset_density` 大致持平：它的活主要是读 360 份件 + 四路正则，本就 IO 主导。

**另有一处本线不占优，如实记录**：真源 `memo_pair` 有**持久层**缓存（内容键），
跨进程复用；本线没有等价层。该层不是免费的（实测一次 `memo_pair` 的指纹计算约 212 ms），
但输入未变时它确实省下一次重算。要不要补这一层，属设计取舍，尚未做。

### 浮点口径（`src/pyfloat.rs`）——解锁 `score` / `verify_report` 的前置

真源多处输出含浮点（`nf score` 的分值/权重、`verify_report` 的覆盖率）。此前 `pyjson` 对浮点
**fail-closed 拒绝写出**（没复刻 repr 就写不出逐字节对账，吐出来的只是"看起来像"）。
现按真源实测把 CPython `float.__repr__` 复刻完毕，并以 **20,000 例位模式穷举对账**（含 27 个
手工边界值 + 随机位模式）验证逐值一致。

**实测分界与坑**：定点区间 `decpt ≤ -4 || decpt > 16`（`1e-4` 定点 / `1e-5` 指数；`1e15` 定点 /
`1e16` 指数）；指数形尾数不带 `.0`、指数至少两位补零；`inf`/`-inf`/`nan`（非 `Infinity`）。

**一个只有穷举才能发现的坑**：两万例里有 **7 例**不一致——都落在**精确值恰好是 17 位正中**的
double 上（如精确值 `153838026194641.125`）。CPython 取**正确舍入（half-to-even）**得 `…12`，
而 Rust 内建 `{:e}` 用 half-up 得 `…13`；**两条十进制都能往返**，靠"能否往返"永远判不出对错。
故本线不用 Rust 的最短表示，改为「取最小的 k，使正确舍入到 k 位的值能往返」——这正是 CPython
`dtoa` 的语义。

### conformance 面的架构（分批移植）

真源的一致性报告 = **27 条契约** 各自裁决 → **封缄**成防篡改报告。本线把这两段拆开：

- **封缄内核**（已交付）：`(id, ok, detail)` → 契约摘要 → Merkle 根 → 报告字节。纯哈希，全量覆盖；
- **契约实现**（分批移植）：每条契约**单独**跑出与真源同形的 `(ok, detail)`；清单由 `nf-rs conformance list` **自描述**，对账门据此逐条比对（不硬编码）。

未移植的 id 一律**显式缺席**（退出码 2 + 指名修复指引），**不伪造空结论**——这正是 ADR-0005「不伪造」那条纪律。

**剩余 23 条的移植性普查**（2026-10-03，按真源内核的依赖面分类）：

| 类别 | 契约 | 说明 |
|---|---|---|
| **已移植 26 条** | `canonical-digest-determinism` · `decisions` · `declaration` · `audit` · `doc-kinds` · `event-backing` · `handover` · `knowledge-sources` · `library-projection` · `library-verify` · `modeling` · `module-signature` · `patterns` · `postmortem` · `public-surface` · `schema-clean` · `state-front` · `st-quality` · `rfc-heads` · `cognition` · `assertions` · `endpoint-contract` · `io-types` · `type-backlog` · `mcp-package` · `pipeline-dryrun` | `doc-kinds` 走 `doc_hygiene.rs`（纯表驱动）；`module-signature`/`event-backing` 走 `miniyaml.rs`；`modeling` 走 `pyconsts.rs`；`handover`/`postmortem` 走 `mdblocks.rs` |
| 依赖 Python 源码里的运行期数据 | `mcp-package` | 需解析 `mcp_runtime.py` 的 `PROMPT_DEFS` 等——**刻意不做**：解析 Python 源码换覆盖率，代价是脆性 |
| 已用**常量表**绕开（本轮） | ~~`endpoint-contract`~~ | 真源 `TOOL_DEFS` 是**代码常量**（与 `root` 无关），故本线用转录的常量表复刻其名字集——**不算"解析 Python 源码"**。两张表已收进 [`src/mcp_tables.rs`](src/mcp_tables.rs)（`tools/gen_mcp_tables.py` 生成）。**守护已就位**：`mcp-package` 契约判「声明的 tools/prompts 与运行时逐名一致」——真源增删工具面时它会红 |
| 已具备地基、可直接续做 | （无） | 27 条里 26 条已落地，余 1 条卡在 AST |
| 未做（仅剩 1 条） | `purity-clean`(AST) | 530 行里 22 处 `ast.`，须宿主语言解析器 |

### 前导块与列表块（`src/mdblocks.rs`）

真源里 `handover` / `postmortem` / `decisions` / `patterns` / `audit` 共用两件叶子逻辑，
真源自己也因「同一件事两份拷贝」收口过一次（`md_blocks.py` 开头的注释记着这段）——本线同样只留一份。

**`parse_frontmatter` 不是 YAML**（真源 `library_entries.py` 里是自研极简解析器）：
分隔点取**第一个冒号**（不要求后跟空格）、缩进行归给上一个键、标量两侧引号用 `strip("'\"")` 去掉。
抄成 YAML 口径会在 `key:value` 或 `key: 通用:M10` 这类值上分叉，故单列一条判据钉住。

### 真源 Python 常量登记册（`src/pyconsts.rs`）

真源 `modeling._probe` 有一种 `python_attr` 探针：用 `importlib` 取某个 Python 模块的常量，
与登记册逐项比对（如「词表 `doc-kinds` 必须等于 `core.doc_hygiene.KINDS`」）。本线没有 Python
运行时，故把这 4 个常量**转录**成册（`doc_hygiene.KINDS` / `assertions.KINDS` / `rfc.CATEGORIES` /
`patterns.STATUSES`），**未登记即报"真源取不到"，绝不冒充一致**。

这与「解析 Python 源码」不是一回事：转录的是真源**对外声明的常量元组**，每条都能一眼核对；
真源改了而本册未同步 → 对账会红。

### YAML 子集（`src/miniyaml.rs`）——解锁整批契约的地基

真源用 PyYAML（`lazy_yaml` 惰性入口）解析 `machine_contract` 围栏块与各类 frontmatter；
本线按依赖纪律自研子集（与 `engine/dotnet` 的 `MiniYaml.cs` 同路数），**只支持真源用到的那一层**。

子集由**实测**界定（248 份模块文档全量普查）：嵌套映射 · 裸/引号标量 · 行内列表 `[a, b]` ·
块列表 `- item` · **列表项本身是映射** · 空流式集合 `{}`/`[]`。类型面：`str`/`list`/`dict`/`int`（仅 1 处）。

**四个只有对着真源跑才会暴露的坑**（每个都曾让对账变红，全部已钉成回归判据）：

1. **`outputs: {}`** 曾被当成字符串 `"{}"` → 该件边摘要漂移；
2. **行尾注释**（`host_consumed:   # 说明`）曾被当成值 → 该件边界漂移；
3. **列表项是映射**（`- purpose: …` 后跟更深缩进的键）曾被 fail-closed → **整个模块被丢弃**，
   连带它发布的 `minute_tick` 变成"无发布方"，让 `event-backing` 凭空报缺口；
4. **同键覆盖**：PyYAML 是后者胜，我起初保留第一条。

还有一条**刻意的设计修正**：起初对「看着像非字符串」的裸标量一律 fail-closed——而 `M50` 里一个
`tick: 0` 就让**整件**解析失败被丢弃。教训是 **fail-closed 必须精确到标量，不能连坐整件**；
现在按 YAML 1.1 解析 null/bool/int/float，只对**真没复刻**的形态（日期、六十进制）拒绝。

### 生成式常量表（`src/doc_tables.rs`）

`DOC_KINDS`(48) / `REQUIRED_DOCS`(45) / `INSTRUCTION_DOCS`(34) / `KINDS` / `KIND_RULES` 是真源里的
**纯数据表**。手抄必然出错且无法审，故由 `tools/gen_doc_tables.py` 从真源转录
（文件头注明出处与重生成命令）。**真源改表后须重生成**，否则该契约的对账会红——这是刻意的：
让表漂移在门禁上显形，而不是悄悄分叉。

`src/doc_hygiene.rs` 覆盖 `kind_coverage` / `kind_rules` / `check_markers` 三件（皆纯表驱动、
不涉 YAML/AST）。它们同时是三条链的输入——conformance 的 `doc-kinds` 契约、`score` 的
`doc_hygiene` 信号、`verify_report` 的同名项——故一次投入三处可用（后两处尚未落地，已标注）。

### 移植时踩到的两类「语义陷阱」（务必留档）

1. **`str(x)` 与 `str(x or "")` 在真源里混用**：前者 `None → "None"`、`0 → "0"`；后者一律落空串。同一模块内两种写法并存，抄错一处就在边界案例上静默分叉。本线为此分了 `plain_str` / `py_str` 两个函数并各有对照判据。
2. **真源的数据驱动模式超出 Rust `regex` 的能力**：`protocol/assertions.json` 的 `regex_absent` 含**负向后顾** `(?<![A-Za-z0-9])`，`regex` crate 不支持（编译即失败）。故引入 `fancy-regex`（回溯引擎，支持后顾；**实测本机可构建、依赖树无 windows**）——但**只用它跑真源给的模式**，本线自己的固定正则仍走 `regex`（更快）。

## 明确边界（不得对外宣称的）

- **不能替代 `verify.sh`**：真源仍在 Python 侧，本线是**并行的只读面**，不新增 check 序号；
- **写面不实现**：`receipts --write`、`stats --write`（重写 README/README.en/llms.txt 生成区与在仓机读件）一律不实现——真源仍是 Python 侧；
- **执行层/交互层不提供**：`daemon` / `shell` / `terminal` / `lsp` / `serve` 一概不做；
- **覆盖到什么程度**（2026-10-04 现值）：`receipts` / `stats` / `layers --verify` 三面完整；
  `conformance` = 封缄内核 + **27/27 契约**（唯缺 `purity-clean`，需 Python AST）；
  `score` 内核完整、**5/6 信号源自算**（余 `purity_clean`·AST 与 `depth_clean`·13 子扫描器）；
  `verify_report` 内核完整、**22/28 判据自算**（余 6 条：AST 3 条 · 本地日历日期 2 条 · 全量契约重算 1 条）；
  `receipts` 的 library scope **已做**（`verify_report` 的 `receipts` 判据）。
- **写面一律不实现**：`receipts --write`、`stats --write`、`layers --write`（刷新生成区）、以及 `conformance --write`。

## 构建与运行

```bash
cargo build --release
cargo test  --release

# 生成（原始字节写文件，可直接与真源落盘件逐字节 diff）
./target/release/nf-rs receipts build     --root <仓库根> [--scope protocol] --out <文件>
./target/release/nf-rs receipts subjects  --root <仓库根> --out <文件>
./target/release/nf-rs receipts selfcheck --root <仓库根> [--scope protocol]
./target/release/nf-rs stats              --root <仓库根> [--json] [--out <文件>]

# conformance：封缄内核 / 已移植契约 / 自描述清单
./target/release/nf-rs conformance seal     --in <裁决行.json> [--out <文件>]
./target/release/nf-rs conformance contract <契约 id> --root <仓库根> [--out <文件>]
./target/release/nf-rs conformance list
./target/release/nf-rs layers     --root <仓库根> --verify [--json] [--out <文件>]
```

对账门（一条命令跑完"两侧现场重算 → 背靠背比 sha256"）：

```powershell
pwsh -NoProfile -File engine/rust/check_parity.ps1 -Root <仓库根>
```

## 环境前置（本机实测，2026-10-03）

工具链 = **`x86_64-pc-windows-gnu` host + minimal profile**（含 `rust-mingw` 自带链接器）⇒ **不需要装 Visual Studio Build Tools**。

**依赖姿态：std + `sha2` + `serde_json`（仅读入）+ `regex`（本线固定正则）+ `fancy-regex`（真源数据驱动模式）。刻意不引 `windows-sys` / `windows-link`。**

理由（实测，非推断）：`windows-sys` 走 `raw-dylib`，链接期强依赖 `dlltool`，而 `rust-mingw` 自带的 `dlltool.exe` 是残废 shim（`CreateProcess` 失败）⇒ 一旦引入该类 crate，本机 `windows-gnu` host **构建即失败**。本线实测干净通过，且 **PATH 无需任何注入**。

`serde_json` 只出现在**读入**侧（真源机读件含浮点，读入必须宽容）；**写出**一律走本线的 `pyjson`——因为判据是"与 CPython `json.dumps` 逐字节一致"，而 `serde_json` 的排版口径与之不同形。

`regex` 用于真源大量以 Python `re` 表述的判据（如 `rfc-heads` 的文档头）。**实测该 crate 在本机 windows-gnu host 可构建，依赖树里没有 `windows-sys`**——不触发下面那条陷阱。

### 浮点纪律（fail-closed）

真源机读件里确实有浮点（`standards_binding.json` 302 处、`domain_packs.json` 608 处），读入侧宽容。

**写出：已复刻，不再 fail-closed**。CPython `float.__repr__`（最短往返表示、整数值补 `.0`、正中平局按「最小的 k 使正确舍入的 k 位往返」定夺）由 [`src/pyfloat.rs`](src/pyfloat.rs) 的 `repr` 复刻，`pyjson` 的浮点写出即走它，并由对账门**面 7（20000 例位模式逐值比对）**守着。

> 这段历史值得留档：**曾有很长一段时间 `pyjson` 对浮点 fail-closed 拒绝写出**——理由是"没有 repr 就写不出逐字节对账，吐出来的只是看起来像"。后来复刻了 repr，才把这条限制撤掉。**先拒绝，再有能力时放开**，比一开始就"看起来像"更安全。

## 判据纪律

- 对账必须**两侧实时重算、背靠背比对**：本仓常有并发会话改动语料（实测同一轮内回执根变过 4 次），拿在盘旧产物当基准会假红。
- **不写盘**：本线只把字节交回调用方；`target/` 已 gitignore，对账暂存一律落 `target/parity/`。
- 新增面时先取证该面是否真读 `engine/`（`sys.addaudithook` 记 `open`/`scandir`），再谈 `protocol/LAYERS.json` 归属——实测 `conformance` 对本目录**零读取**。
