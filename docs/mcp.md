# NinFenz MCP 接入（`nf serve` · 40 总纲 v2.7 波A S1-E3 / X2）
> 最后更新：2026-09-30

> **状态**：公开化文档已随基础层 v2.7 落地；**E3 协议级装载实测已于 2026-09-08 通过**（stdio JSON-RPC 帧序列直测五方法全绿，见文末记录；修复 P06 管线两缺口——缺闭合 ``` / 缺 techdoc 声明）。41 波C C7（2026-09-08）开放只读 tools/prompts（本机 stdio 冒烟通过，见 docs/41_波C_C7_实测记录.md）。**宿主类客户端（Claude Desktop 等 GUI 装载）仍建议用户侧补录**——README 对 MCP 的宣告维持现状（S13 门按 docs_external-validation-v2.7.md 规则开），回填后补「转正」。

## 这是什么

NF 提供 MCP（Model Context Protocol）stdio 服务 `nf serve`：

- 把「MCP 快照」（`nf run --fmt mcp` 导出的 `.json`）烧成 JSON-RPC stdio 会话（换行分隔 UTF-8 消息）；
- **只读面**：`resources/list` + `resources/read`；41 波C C7（2026-09-08 裁决）开放**只读 tools/prompts**——`tools/list`+`tools/call`（library_search / registry_query / pipeline_ls / spec_ls）与 `prompts/list`+`prompts/get`（assemble_guide 装载引导）；写路径工具不实现，未知工具/方法拒出；
- **uri 白名单**：`resources/read` 只接受快照内已登记 uri，未知 uri 返回 `-32602 INVALID_PARAMS`（不泄露目录结构）；
- **协议版本 = dual-era**：modern `2026-07-28`（每请求 `_meta` 携带版本，无协商握手）+ legacy `2025-11-25`（`initialize` 握手）并存；不支持版本回 `-32022` 并列出支持集。声明版本用的键是**规范键名** `_meta["io.modelcontextprotocol/protocolVersion"]`；用别的键名（如裸 `protocolVersion`）**不算版本声明**，服务端按 legacy 处理、不会回 `-32022`（实测 2026-10-01）。历史对照见 33 号 A5 核查报告（G1/G2/G4 已勾销），现代口径实证见规范 §Versioning / §Discovery。

安全定位（C2 最小安全层）：只读 + 白名单——适合把仓库/内容库能力**只读暴露**给 agent 检索，天然无写面。

**入站资源闸门**：一条消息上限 **8 MiB**（超过即回 `-32600` 并**丢弃到行尾**，会话不中断）——
客户端不发换行也不能把整条流灌进服务端内存；行对齐不破，后续消息照常服务。

## 三步接入

### 1. 产快照（**可选面**）

**默认接入不需要这一步**——`nf serve` 缺省即实时仓库面，直接跳到第 2 步。只有想把「某次装配的
成果面」固化下来时，才用全链 CLI 导出一份 `--fmt mcp` 快照（质量门须 PASS 才产出，语义同 verify 铁律）：

```bash
python scripts/nf.py run \
  --pipeline community/技术文档域包/pipelines/P06_技术文档题材装配流管线.md \
  --modules 技术文档类:M90,技术文档类:M97,技术文档类:M98,通用类:M00,通用类:M80 \
  --store <store 目录> --fmt mcp --dest <输出目录>
```

**题材铁律**：MCP 出口仅接受协议/规则类（techdoc）装配——管线须在 `Pipeline.structure.type` 声明 `techdoc`（P06 即范例），叙事类管线（如 P04 轻混）一律拒出（诚实映射裁决，0 文件 + warnings）。

**模块装载说明**：`--seed` 只装载官方核心（04_模块库 13 件，含 M90）+ 校园西幻轻混组合包——**不覆盖社区域包自带模块**（M97/M98 在 `community/技术文档域包/modules/`）。用 P06 全装配需先按下方脚本装载 store；`--seed` 仅适合官方核心组合的演示/自测（对应地把 `--store` 换成 `--seed` 即可）。

```bash
python3 - <<'PY'
import sys, glob
sys.path.insert(0, 'desktop/src')
from core.storage import Store
from core.parser import parse_module
store = Store(home='<store 目录>')          # 真实装配目录
for f in sorted(glob.glob('04_模块库/*/*.md')):
    store.save_module(parse_module(open(f, encoding='utf-8').read()))
for f in sorted(glob.glob('community/技术文档域包/modules/*.md')):
    store.save_module(parse_module(open(f, encoding='utf-8').read()))
print(f'装载 {len(store.list_modules())} 模块 → {store.home}')
PY
```

### 2. 起服务

```bash
python scripts/nf.py serve                 # 默认路径：实时仓库面（无需快照，推荐 agent 密集调用）
python scripts/nf.py serve <快照 .json 路径>  # 或烧快照面（须先 `nf run --fmt mcp` 产快照）
```

stdio 服务随调用进程生命周期运行（`Ctrl+C` 结束）。也可用 `nf run --fmt mcp` 产物再经 export_schema 校验（check19/22 覆盖产物 shape）。

### 3. 客户端接入（标准 MCP 客户端）

任意支持 MCP stdio 的客户端，把 `nf.py serve` 声明为一个 server（示例为通用 `mcpServers` 配置，Claude Desktop 类客户端同构）：

```json
{
  "mcpServers": {
    "ninfenz": {
      "command": "python",
      "args": ["<仓库绝对路径>/scripts/nf.py", "serve"]
    }
  }
}
```

（快照面：`args` 末尾补 `<快照 .json 绝对路径>`。）

连接后 agent 可调用：`resources/list` 枚举资源 → `resources/read` 按 uri 取正文——实时仓库面给的是 `nf://repo/...`（模块 / 资产 / 管线 / 馆藏 / 模式），快照面给的是该次装配登记的资源。具体 uri 集以实际 `resources/list` 返回为准。
41 波C C7 起 agent 还可调用只读检索工具：`pipeline_ls`（管线清单）/ `spec_ls`（协议包清单）/ `registry_query`（模块+协议查询）/ `library_search`（仓库侧知识库检索），及装载引导 prompt `assemble_guide`。44 起再开放**内容通道工具**：`module_read`（模块正文）/ `pipeline_read`（管线正文）/ `asset_get`（资产正文）——从「元数据检索」升级为「实质内容取用」（机制借鉴 MCP resource/content 两段式实证适配，仍全只读）。数据源 = 仓库只读扫描（03/04/community/docs/registry.json），全部只读、无写面。

## 能力表（与 mcp_runtime 实现一一对应）

| 方法 | 实现 | 说明 |
|---|---|---|
| `server/discover` | ✅ | modern 必备：一次返回 `supportedVersions` / `capabilities` / `_meta.serverInfo` + `instructions`/`ttlMs` |
| `initialize` | ✅ | legacy 握手：请求版本受支持则回显，否则回落 `2025-11-25`；`serverInfo` 自述（非快照文件顶层） |
| `notifications/initialized` | ✅ 静默 | 通知无 id，不应答 |
| `ping` | ✅ | 返回 `{}` |
| `resources/list` | ✅ | 快照登记资源纯元数据（无 text 字段） |
| `resources/templates/list` | ✅ | RFC 6570 一级子集资源模板（library / pattern / module / pipeline / asset 五条），真实资源 uri 全覆盖由 check33 断言 |
| `resources/read` | ✅ | 白名单 uri → `contents[].text`；未知 uri → `-32602` |
| `tools/list` / `tools/call`（只读 · 检索面） | ✅ | 41 波C C7：library_search / registry_query / pipeline_ls / spec_ls（inputSchema 真实存在，全只读） |
| `tools/list` / `tools/call`（只读 · 内容通道） | ✅ | 44：module_read / pipeline_read / asset_get——返回模块/管线/资产正文实质内容（不只元数据） |
| `tools/list` 的工具注解 | ✅ | 10 个工具全部声明 `annotations.readOnlyHint: true`（2026-10-08 起）——「只读」不止写在散文里，MCP 客户端据此可**自动放行**只读调用，不必逐个弹窗 |
| `prompts/list` / `prompts/get` | ✅ | 41 波C C7：assemble_guide 装载引导模板（只读） |
| 写路径工具（未实现） | ❌ | 未知工具 → `-32602`；未知方法 → `-32601`（只读安全层天然拒写） |

标准错误码：`-32700` 解析错误 / `-32600` 非法请求 / `-32601` 方法不存在 / `-32602` 参数非法 / `-32603` 内部错误；版本协商错误 `-32022`（`data.supported` / `data.requested`）。

## E3 实测记录（2026-09-08 · 协议级装载实测通过）

| 日期 | 客户端 | 结果（成功/失败/差距） | 差距与修复 |
|---|---|---|---|
| 2026-09-08 | 协议级 stdio 客户端（按 MCP `2025-11-25` JSON-RPC 帧直测 `nf serve`，非 GUI 宿主） | ✅ **五方法全绿**：`initialize`（协议 2025-11-25 + serverInfo P06-mcp v0.1.0）→ `notifications/initialized` 静默 → `ping` `{}` → `resources/list`（5 资源：M00/M97/M98/M80/M90）→ `resources/read`（`nf://P06/P40/术语管理-M97` 正文完整返回）→ `tools/list` `-32601 METHOD_NOT_FOUND` → 未知 uri `-32602` | 修复 2 处 P06 管线缺口：① 文件尾部缺闭合 ```` ``` ````（56 行截断，管线解析静默 None）；② `Pipeline.structure.type` 缺 `techdoc` 声明（默认 linear → IR.type=narrative → MCP 出口拒出）。修复后 PASS 0/WARN 1/FAIL 0 产出 5 资源快照，实测通过。**待补**：Claude Desktop 类 GUI 宿主装载（用户侧可选补录） |

> 回填原则：真实装载/调用结果，不造假。上表为**协议级真实会话记录**（模拟标准客户端帧序列直连进程），GUI 宿主补录后据此把 README 宣告逐项转正（S13），并沉淀 fixture 入测试库（X1）。

## 相关

- 实现：`desktop/src/core/mcp_runtime.py`（运行时）/ `mcp_adapter.py`（导出）/ `export_schema.py`（shape 校验）
- 核查基线：`results/audit/docs_audit-58-pending-items.md`（外部核验记录：MCP 可缓存结果缺键的发现与修复）
- 上架材料（对外命名 / 一句话 / 类目 / 安装与提交文案）：本文「上架材料」节（真源 = `protocol/mcp_package.json`）
- CLI 入口：`scripts/nf.py`（`run --fmt mcp` / `serve`）

## 帧纪律与结构约束（2026-09-21 增补，外部标准吸收）

stdio transport 的**可执行判据**（此前只写在注释里，现在进 check33）：

1. **一条消息一行** —— `encode_message()` 用紧凑分隔符序列化，且消息内不得出现裸换行；
2. **行边界陷阱转义** —— `U+2028` 行分隔 / `U+2029` 段分隔 / `U+0085` NEL 按 Unicode 换行
   边界读行的客户端会把它们当换行（JSON 规范允许裸写）→ 出口一律转义为 `\uXXXX`；
3. **通知不写响应行** —— 无 `id` 的消息处理完即静默（`encode_message(None) is None`）；
4. **JSON-RPC 2.0 §4 / §5** —— `params` 若在场 MUST 为结构化（原始类型 → `-32600`；
   数组 → `-32602`，本运行时只接受按名参数）、`id` MUST 为字符串/数字/null，
   **id 可判定时错误响应 MUST 回显**（不可判定才 `null`）。

自测：`desktop/tests/test_mcp_runtime.py`（含帧纪律三例 + 结构约束四例）；
门禁：`verify.sh` check33 第 11/13 面。

**资源模板面**（RFC 6570 一级子集）：`resources/templates/list` 的 5 条模板（library /
pattern / module / pipeline / asset）须满足——只许 `{var}` 简单展开（不许 `{+id}` 操作符、
`{x*}` 爆炸、前缀修饰）、变量名唯一、花括号配平、无查询串；并且**每条真实资源 uri 都必须
被某条模板覆盖**（模板⇄读取面一致，防止「列得出但取不回」）。实测：5 模板全合法、
**全部真实资源 uri 零未覆盖**（数随仓库增长，**不写死**：判据见
`desktop/tests/test_mcp_runtime.py::test_template_matches_real_uris`）；负例（操作符/重名/问号/
空变量/不配平）逐类可拦。

**参数准入（方法级）**：每个带参方法只认自己声明的键，未声明键（`_` 前缀的协议保留名除外）
一律 `-32602` + 修复指引——`resources/read` → `uri`、`prompts/get` → `name`（外加协议自带的可选 `arguments`：**允许出现但须为空对象**，很多客户端总会带上它；非空即明说「该模板不收参数」）、`initialize` →
`protocolVersion` / `capabilities` / `clientInfo`（后两者还须是对象）、`server/discover` → 无
（仅保留名）。`resources/list` 另有两项值域判据：`cursor` 须为非负整数字符串（原样传上一页的
`nextCursor`）、`type` 须在词表内（`module` / `pipeline` / `asset` / `library` / `pattern`）；`package` 过滤用**列表项里 `package` 字段的原值**（如 `三维与世界模型域包`，即中文名本身），**不是** uri 里那段百分号编码——传编码形式会得到空表（实测 2026-10-01）。
此前非法 `cursor` 会被静默当 0、非法 `type` 会静默给空表、陌生键会被静默忽略（客户端以为
过滤生效了）——都是「看起来正常」的错答。

## 上架材料（B 线包装 · 对外提交用）

> 真源 = `protocol/mcp_package.json`（机读）。本节是它的**人读投影**：改动先改真源，
> 再由 `desktop/tests/test_mcp_packaging.py` 断言两处逐项一致（漂移即 FAIL）。

### 一、对外标识

| 字段 | 取值 |
|---|---|
| 名称（Name） | `NinFenz Content Gate` |
| 一句话（One-liner） | 给任何 AI agent 一个可校验的内容规范与资产底座——先查契约，再落笔。 |
| 类目（Category） | `content-creation` |
| 传输（Transport） | `stdio`（dual-era：modern `2026-07-28` + legacy `2025-11-25`） |
| 入口（Entry） | `python scripts/nf.py serve`（**缺省 = 实时仓库面，无需快照**）｜快照面（可选）：`python scripts/nf.py run --fmt mcp` → `python scripts/nf.py serve <快照 .json>` |

### 二、安装（三步，复制即用）

```bash
# ① 起服务（默认路径：实时仓库面，**不需要先产快照**）
python scripts/nf.py serve

# ② 可选：烧一份快照面（techdoc 装配才出 MCP；叙事类一律拒出 = 诚实映射）
python scripts/nf.py run \
  --pipeline community/技术文档域包/pipelines/P06_技术文档题材装配流管线.md \
  --modules 技术文档类:M90,技术文档类:M97,技术文档类:M98,通用类:M00,通用类:M80 \
  --store <store 目录> --fmt mcp --dest <输出目录>
python scripts/nf.py serve <输出目录>/mcp.json

# ③ 客户端声明（标准 MCP stdio 客户端同构）
```

```json
{
  "mcpServers": {
    "ninfenz": {
      "command": "python",
      "args": ["<仓库绝对路径>/scripts/nf.py", "serve"]
    }
  }
}
```

> 快照面：把 `args` 末尾补上 `<输出目录>/mcp.json` 即可；缺省（不补）走**实时仓库面**，
> 服务随调用进程生命周期运行（`Ctrl+C` 结束）。

### 三、English install notes

1. Start the server: `python scripts/nf.py serve` — the default **live-repo surface**
   needs no snapshot (that is the path agent-dense callers should use).
2. Optional snapshot: `python scripts/nf.py run --pipeline ... --fmt mcp --dest <dir>`
   (only techdoc assemblies are exported; narrative pipelines are refused by design)
   then `python scripts/nf.py serve <dir>/mcp.json`.
3. Declare it in any MCP stdio client via the `mcpServers` block above.

### 四、能力面（只读）

- **tools（10）**：`pipeline_ls` · `spec_ls` · `registry_query` · `library_search` ·
  `library_read` · `pattern_read` · `knowledge_order` · `module_read` ·
  `pipeline_read` · `asset_get`
- **prompts（1）**：`assemble_guide`
- **resources**：快照登记资源（`resources/list` → `resources/read`，uri 白名单）+ 仓库实时
  资源（`nf://repo/...`，真实 uri 全被 5 条模板覆盖；条数随仓库增长，不写死）

### 五、红线（提交前自查）

1. **只读**：不新增任何写工具（当前 10 工具 + 1 prompt）。
2. **零新依赖**：仅标准库。
3. **uri 白名单**：资源模板受白名单约束；未知 uri → `-32602`。
4. **双协议版本**：modern `2026-07-28` + legacy `initialize` 并存。
5. **门禁不减**：仓库自检 PASS 数不得下降。
6. **信任边界**：返回的外来内容（`library/`、`community/*`、外部材料摘要）一律按**数据**
   消费。四件都在实现里：**参数准入**（控制字符 / 超长 / 穿越 / 盘符 / 备用数据流 → `-32602`）、
   **声明面校验**（按 `tools/list` 的 `inputSchema` 逐条校验：必填缺失 / 类型不符 / 枚举越界 /
   多余或拼错的键——`additionalProperties: false`——都在进处理器前拒掉，避免「参数拼错却拿到
   未过滤结果」这类**静默错答**）、
   **来源标注**（外来来源的回包带 `_meta["nf.trust"]`：`untrusted` + `policy` + `sources` +
   `injection_hits`；仓库自持内容不打标记；标注不改正文一个字节）、**入库侧扫描**（投稿机器人
  在公开边界按同一条 `trust_boundary.detect` 记档）。判据见 `desktop/tests/test_trust_boundary.py`
   、`desktop/tests/test_mcp_trust_meta.py`。

### 六、提交文案（可直接粘贴到目录站表单）

> **NinFenz Content Gate** — 一个只读 MCP 服务器：把长内容的验收标准
> （协议 / 模块 / 管线 / 资产 / 馆藏）变成 agent 可调用的检索与取件工具面。
> 10 个只读工具 + 1 个装载引导 prompt，支持 modern `2026-07-28` 与 legacy `2025-11-25`
> 双协议版本，零第三方依赖，无写路径。
