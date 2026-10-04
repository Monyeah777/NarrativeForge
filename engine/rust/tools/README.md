# `engine/rust/tools/` —— 判据期望值的**可再生来源**

这些脚本不属于构建产物，也不属于运行时；它们的作用是**从 Python 真源生成判据的期望值**，
使「本线行为 == 真源行为」这件事**可复现**，而不是靠人手抄一遍。

## 为什么必须放在这里（而不是 `target/`）

它们原先写在 `engine/rust/target/parity/`——而 `engine/rust/.gitignore` 忽略 `/target`。
**判据的期望值来源若随构建目录一起被清掉，判据就变成了"只可读不可再生"**：
真源改了措辞，没人知道怎么更新期望值。故移至此处。

## 两类脚本

### 一、分支级差分判据的生成器（`gen_*_branches.py` / `gen_*_expected.py`）

对**真语料全绿**的面（对账只能核到"都对"这一侧），构造一个逐形态/逐分支踩的合成语料，
跑真源、打印期望值、并把 Rust 判据直接写进对应的 `src/*.rs`。

| 脚本 | 面 | 踩的分支 |
|---|---|---|
| `gen_knowledge_expected.py` + `emit_knowledge_tests.py` | `knowledge.verify_transform` / `verify_usage` | 14 + 6 条（含 1 条全绿样本） |
| `gen_coupling_expected.py` + `emit_coupling_tests.py` | `coupling_metrics` | 10 种 import 写法 |
| `gen_workflow_expected.py` + `emit_workflow_tests.py` | `workflow_policy` | 11 个分支 |
| `gen_audit_branches.py` | `audit` | 9 个分支 |
| `gen_license_branches.py` | `license_gate` | 8 个分支 |
| `gen_payload_branches.py` | `payload_registry` | 5 个分支 |
| `gen_modeling_branches.py` | `modeling` | 27 个分支（三件子判据） |
| `gen_intake_branches.py` | `intake` | 9 个分支 |
| `gen_rating_branches.py` | `rating_gate` | 3 场景 × 3 分支 |
| `gen_drill_fidelity_branches.py` | `drill_fidelity` | 四场景：执行演练四条硬断言、保真度不足、回合级 R-R1/R-R2/R-R3（含同尾豁免）、跳号、无回合标记、未复现声明、找不到用例/样本、坏 JSON |
| `gen_handover_branches.py` | `handover` | 三场景 × 缺必填 / status 越词表 / 日期 / 缺段落 / 未决项为空 / 缺判据 / `refs` 各种形态 |
| `gen_postmortem_branches.py` | `postmortem` | 四场景 × 引用两种失败 / 缺必填 / status / 日期 / 缺段落 / 指责性归因词 / 根因未指向机制 / 行动项为空·缺负责人·缺判据 / closed 未锚定 |
| `gen_state_front_branches.py` | `state_front` | 三场景 × schema / 族规则缺 glob / 族成员不足 / 族内件未过 condition-first / 条目缺 path / 登记件不存在·未通过 |
| `gen_patterns_branches.py` | `patterns` | 三场景 × 缺 frontmatter / 缺必填 / id 与目录名不一致 / id 重复 / status 越词表 / rules 空 / applies_to 通配无匹配·路径不存在 / evidence 缺失·空项·指向不存在 |
| `gen_endpoint_branches.py` | `endpoint` | 三场景 × 20+ 分支（schema / status / id 重复 / method / method+path / streaming / maps_to 两种失败 / 弃用面 7 支 / 幂等面 6 支） |
| `gen_endpoint_tools.py` | `endpoint` 的 `TOOL_NAMES` 常量表 | 转录真源 `mcp_runtime.TOOL_DEFS` 的名字集（**改真源后必须重跑**，见脚本头） |
| `gen_declaration_branches.py` | `declaration` | 五路版本真源 / 声明不一致 / 无法核验项 / 范围路径不存在 / 排除 glob 无匹配 / 「允许不存在」豁免 / scope∩排除重叠 |
| `gen_pipeline_dryrun_branches.py` | `pipeline-dryrun` | 三场景（kitchen / 解析失败 / 零管线）× 模块未找到 / 同层依赖序 / 跨包外部依赖 / 跨包外部事件 / 类型冲突 / 类型不匹配 / 基座进池 / `fid_key` 归一 / `README.md` 跳过 / 解析失败⇒契约记异常 |
| `gen_decisions_branches.py` | `decisions` | 16 个分支（缺 id / 不合法 / 与文件名不一致 / 编号重复 / 缺必填 / status / 日期 / 缺段落 / 证据三态 / accepted 未锚定 / superseded 三态 / 成环） |

**重跑方式**（在仓库根）：

```powershell
python engine/rust/tools/gen_modeling_branches.py   # 重新生成期望值并写回 src/modeling.rs
cargo test --release --manifest-path engine/rust/Cargo.toml
```

**纪律**：`gen_*` 写出的期望值**一律标"从真源生成，勿手改"**。真源改了措辞 → 判据红 →
重跑生成器 → 期望值跟上。手改期望值等于把判据降级成"记录我上次写的字"。

### 二、普查 / 审计脚本（`survey_*.py` / `audit_engine_reads.py`）

| 脚本 | 作用 |
|---|---|
| `survey_all_scalars.py` | 普查全部模块文档围栏块里的标量类型（界定 mini-YAML 要复刻多少 YAML 1.1） |
| `survey_yaml.py` / `survey_yaml_types.py` | 普查真源 YAML 用到的形态与类型 |
| `audit_engine_reads.py` | `sys.addaudithook` 审计：证明 `conformance` 对 `engine/` **零读取**（零侵入的构建性证明） |
| `gen_doc_tables.py` | 从真源生成 `src/doc_tables.rs` 的常量表 |

### 三、一致性守护（`check_native_sync.py`）

把「**对账门 / 同行判据里手写的自算集，必须与快线实际自算面一致**」变成机器可检的不变量。

`verify_report.call` 是 **native 优先于 `--results`**：自算集**多列**一条无害，**少列**一条则危险——
该条分派断掉时会静默回落到喂入值、门禁照样全绿。实测（2026-10-04）两处清单都漂过。

做法：给 `nf-rs verify-report` 喂**空** `--results`，凡未自算的判据都会自报「未移植且未喂入」，
据此反推真实自算面，再与两处手写清单比对，不一致即退出码 1。

```powershell
python engine/rust/tools/check_native_sync.py
```

### 四、`_rustlit.py`：Rust 字符串字面量的唯一出处（一处**潜在**陷阱）

`json.dumps` 默认 `ensure_ascii=True`，会把非 ASCII 写成 ``\uXXXX``；而 **Rust 只认** ``\u{XXXX}``。
把前者直接当字面量拼进 `src/*.rs`，生成的源码会**编译不过**（`incorrect unicode escape sequence`）。

**这是实测踩到的**（`pipeline-dryrun` 移植时，`json.dumps` 的中文键让整个文件编译失败），
但当时只是**潜在**陷阱——各生成器的键恰好都是 ASCII（文件路径、标识符），所以一直没炸。
一旦给夹具加中文键/名就会炸。现收口到 [`_rustlit.py`](_rustlit.py) 的 `rs()`：

- 非 ASCII **原样保留**（Rust 源是 UTF-8，接受）；
- 引号与反斜杠按 Rust 规则转义；
- 残余的 ``\uXXXX``（控制字符等）改写成 ``\u{XXXX}``。

**两类用法必须分开**（我第一版批量替换做过头，把 73 处写 JSON 夹具文件的调用也换掉了，
22 个生成器里坏了 18 个，靠"括号内含 `ensure_ascii` 即回退"精确修回）：

| 用法 | 形态 | 怎么办 |
|---|---|---|
| **Rust 字面量** | `'%s' % json.dumps(k)`（**不带** `ensure_ascii`） | 用 `rs()` |
| **JSON 夹具内容** | `write_text(json.dumps(obj, ensure_ascii=False))`、`rj(json.dumps(obj))` | **保持 `json.dumps`**——文件内容要可读中文；原始字符串里也不能转义引号 |

教训：**批量替换前先想清楚"这两处看着一样、其实不是一类"**；改完必须**把全部生成器重跑一遍**
（本轮就是这么发现 18 个坏掉的）。

### 五、`audit_pub_readers.py`：揪出「没人核的代码面」

本线的纪律是**移植面按消费者界定**（`machine_contract` 只移植 `id` 那条路径、
`handover`/`state_front`/`postmortem`/`endpoint` 不落没人读的 `warns`……）。
纪律靠人记必漏，故做成普查：某个 `pub` 项若**除定义处外无人引用**（含测试），
它要么是死代码、要么是"写了但没人验"——两种都该被看见。

```powershell
python engine/rust/tools/audit_pub_readers.py     # 有 [dead] 即退出码 1
```

当前结论：**304 个有读者 / 1 个合理 test-only（`testutil::fixture`）/ 0 死代码**。

**判据本身也踩过坑**：初版把 `#[cfg(test)] mod testutil;`（**文件模块**）当成测试区起点，
于是 `main.rs` 里它之后的整片都被算作测试代码，**所有真读者都被误报成 `[test-only]`**。
现只认 `#[cfg(test)]` 后紧邻 `mod X {`（**块**）才算测试区。这次误报顺带掩盖了一个真问题：
同一轮里 `knowledge.rs::source_ids` **确实**是全仓零引用，已删。

### 六、`audit_unported_consumers.py`：给「没做的那部分是可选体量」这句话取证

我在 README 里断言：`quality_depth_scan` 的 8 个未移植子扫描器属于「**可做但没做**」（体量），
**不是**「不可做」、也**不是**缺口。这个断言若错了（某个子扫描器其实**支撑着某条已移植的判据**），
性质就完全不同——那是"**声称做完的面其实有缺口**"。

故做成反向依赖普查：扫全仓 `.py`，看谁引用这 8 个。

```powershell
python engine/rust/tools/audit_unported_consumers.py    # 发现缺口即退出码 1
```

当前结论：**8 个都只被未移植面 / CLI / 测试引用，没有一个落在已移植面的判据链上** ⇒
「可选体量」成立。引用者分别是 `quality_depth_scan`（聚合器本身）、`nf`（CLI）、
`pack_combo`/`output_forms`（互为未移植）、`daemon`、`ai_domain_closure`、`fde_sample_run`。

## 二·五、`_rustlit.py` 与它的 lint（同一个陷阱咬了三次）

`json.dumps` 默认 `ensure_ascii=True` ⇒ 中文写成 `\uXXXX`；**Rust 只认 `\u{XXXX}`** ⇒
生成的源码直接编译不过（`incorrect unicode escape sequence`）。

实测踩过**三次**：`pipeline-dryrun` 移植时、我批量替换那轮、以及 `doc-kinds` 生成器
（键用了 `json.dumps(k)` 而非 `rs(k)`）。三次都发生在**新建生成器**时——
说明"记住就行"不成立，故立两道闸：

| 出处 | 用途 |
|---|---|
| [`_rustlit.py`](_rustlit.py) 的 `rs()` | **Rust 普通字符串字面量**（键、短文本）：非 ASCII 原样保留、引号反斜杠按 Rust 转义、残余 `\uXXXX` → `\u{XXXX}` |
| 同文件的 `raw()` | **Rust 原始字符串**，分隔符按内容**自动升级**（`r#"…"#` → `r##"…"##`）——内容里含 `"#` 时会提前终止，实测踩到（夹具里有 `"## 块"`） |
| [`audit_rust_literals.py`](audit_rust_literals.py) | lint：**整调用**分析，凡 `json.dumps(...)` 调用里**没有** `ensure_ascii` 就报错 |

lint 的判据刻意能区分两类用法（早期逐行版有多行调用的假阳性，已改整调用）：
- **不带** `ensure_ascii` ⇒ 输出会当 Rust 字面量 ⇒ 应改走 `rs()` ⇒ **报错**；
- **带** `ensure_ascii=False` ⇒ 是写 JSON 夹具内容（文件要可读中文）⇒ 正常。

该 lint 已并入对账门**面 13d**。

## 三至七节四项已并入对账门

`check_native_sync.py` / `audit_pub_readers.py` / `audit_unported_consumers.py` 三项现由
`check_parity.ps1` 的**面 13** 自动跑（各接受一个可选 `<仓库根>` 参数）。它们**不是**"逐字节对账"，
而是**判据自身可信度**的不变量：

| 脚本 | 守的是什么 | 会怎么红 |
|---|---|---|
| `check_native_sync.py` | 两处手写自算集 == 快线实际自算面 | 少列一条即 FAIL（该条分派断掉不会红，是真实盲区） |
| `audit_pub_readers.py` | 无「全仓零引用的 pub 项」 | 植入死代码即 FAIL（**已做反向对照**） |
| `audit_unported_consumers.py` | 未移植模块不落在已移植面的判据链上 | 有依赖即 FAIL |
| `audit_rust_literals.py` | 生成器不写出会编译不过的 Rust 字面量 | 缺 `ensure_ascii` 的 `json.dumps` 即 FAIL |

## 与 `check_parity.ps1` 的分工

对账的 12 个**面**（receipts / stats / conformance / layers / 浮点 / density / score / schema_lint /
差分 / verify_report）由 `engine/rust/check_parity.ps1` 现场生成参照并比对，其参照生成器
**内嵌在脚本里**（每次运行重写，不依赖磁盘上的副本）。

本目录的脚本管的是**另一件事**：分支级判据的期望值——那些**只在改了对应 `src/*.rs` 时才需要重跑**，
所以做成独立、可版本化的脚本，而不是每次对账都跑一遍。
