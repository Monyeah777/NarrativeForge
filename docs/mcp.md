# NarrativeForge MCP 接入（`nf serve` · 40 总纲 v2.7 波A S1-E3 / X2）
> 最后更新：2026-09-08

> **状态**：公开化文档已随基础层 v2.7 落地；**E3 协议级装载实测已于 2026-09-08 通过**（stdio JSON-RPC 帧序列直测五方法全绿，见文末记录；修复 P06 管线两缺口——缺闭合 ``` / 缺 techdoc 声明）。41 波C C7（2026-09-08）开放只读 tools/prompts（本机 stdio 冒烟通过，见 docs/41_波C_C7_实测记录.md）。**宿主类客户端（Claude Desktop 等 GUI 装载）仍建议用户侧补录**——README 对 MCP 的宣告维持现状（S13 门按 docs_external-validation-v2.7.md 规则开），回填后补「转正」。

## 这是什么

NF 提供 MCP（Model Context Protocol）stdio 服务 `nf serve`：

- 把「MCP 快照」（`nf run --fmt mcp` 导出的 `.json`）烧成 JSON-RPC stdio 会话（换行分隔 UTF-8 消息）；
- **只读面**：`resources/list` + `resources/read`；41 波C C7（2026-09-08 裁决）开放**只读 tools/prompts**——`tools/list`+`tools/call`（library_search / registry_query / pipeline_ls / spec_ls）与 `prompts/list`+`prompts/get`（assemble_guide 装载引导）；写路径工具不实现，未知工具/方法拒出；
- **uri 白名单**：`resources/read` 只接受快照内已登记 uri，未知 uri 返回 `-32602 INVALID_PARAMS`（不泄露目录结构）；
- 协议版本对齐 `2025-11-25`（逐条实证对照见 33 号 A5 核查报告，G1/G2/G4 已勾销）。

安全定位（C2 最小安全层）：只读 + 白名单——适合把仓库/内容库能力**只读暴露**给 agent 检索，天然无写面。

## 三步接入

### 1. 产快照

先用全链 CLI 导出一份 `--fmt mcp` 快照（质量门须 PASS 才产出，语义同 verify 铁律）：

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
python scripts/nf.py serve <快照 .json 路径>
```

stdio 服务随调用进程生命周期运行（`Ctrl+C` 结束）。也可用 `nf run --fmt mcp` 产物再经 export_schema 校验（check19/22 覆盖产物 shape）。

### 3. 客户端接入（标准 MCP 客户端）

任意支持 MCP stdio 的客户端，把 `nf.py serve` 声明为一个 server（示例为通用 `mcpServers` 配置，Claude Desktop 类客户端同构）：

```json
{
  "mcpServers": {
    "narrativeforge": {
      "command": "python",
      "args": ["<仓库绝对路径>/scripts/nf.py", "serve", "<快照 .json 绝对路径>"]
    }
  }
}
```

连接后 agent 可调用：`resources/list` 枚举快照内已登记资源 → `resources/read` 按 uri 取正文。具体资源 uri 集以实际快照的 `resources/list` 返回为准。
41 波C C7 起 agent 还可调用只读检索工具：`pipeline_ls`（管线清单）/ `spec_ls`（协议包清单）/ `registry_query`（模块+协议查询）/ `library_search`（仓库侧知识库检索），及装载引导 prompt `assemble_guide`。数据源 = 仓库只读扫描（03/04/community/docs/registry.json），全部只读、无写面。

## 能力表（与 mcp_runtime 实现一一对应）

| 方法 | 实现 | 说明 |
|---|---|---|
| `initialize` | ✅ | 协议版本 `2025-11-25`；`serverInfo` 自述（name/version 经握手，非快照文件顶层） |
| `notifications/initialized` | ✅ 静默 | 通知无 id，不应答 |
| `ping` | ✅ | 返回 `{}` |
| `resources/list` | ✅ | 快照登记资源纯元数据（无 text 字段） |
| `resources/read` | ✅ | 白名单 uri → `contents[].text`；未知 uri → `-32602` |
| `tools/list` / `tools/call`（只读） | ✅ | 41 波C C7：library_search / registry_query / pipeline_ls / spec_ls（inputSchema 真实存在，全只读） |
| `prompts/list` / `prompts/get` | ✅ | 41 波C C7：assemble_guide 装载引导模板（只读） |
| 写路径工具（未实现） | ❌ | 未知工具 → `-32602`；未知方法 → `-32601`（只读安全层天然拒写） |

标准错误码：`-32700` 解析错误 / `-32600` 非法请求 / `-32601` 方法不存在 / `-32602` 参数非法 / `-32603` 内部错误。

## E3 实测记录（2026-09-08 · 协议级装载实测通过）

| 日期 | 客户端 | 结果（成功/失败/差距） | 差距与修复 |
|---|---|---|---|
| 2026-09-08 | 协议级 stdio 客户端（按 MCP `2025-11-25` JSON-RPC 帧直测 `nf serve`，非 GUI 宿主） | ✅ **五方法全绿**：`initialize`（协议 2025-11-25 + serverInfo P06-mcp v0.1.0）→ `notifications/initialized` 静默 → `ping` `{}` → `resources/list`（5 资源：M00/M97/M98/M80/M90）→ `resources/read`（`nf://P06/P40/术语管理-M97` 正文完整返回）→ `tools/list` `-32601 METHOD_NOT_FOUND` → 未知 uri `-32602` | 修复 2 处 P06 管线缺口：① 文件尾部缺闭合 ```` ``` ````（56 行截断，管线解析静默 None）；② `Pipeline.structure.type` 缺 `techdoc` 声明（默认 linear → IR.type=narrative → MCP 出口拒出）。修复后 PASS 0/WARN 1/FAIL 0 产出 5 资源快照，实测通过。**待补**：Claude Desktop 类 GUI 宿主装载（用户侧可选补录） |

> 回填原则：真实装载/调用结果，不造假。上表为**协议级真实会话记录**（模拟标准客户端帧序列直连进程），GUI 宿主补录后据此把 README 宣告逐项转正（S13），并沉淀 fixture 入测试库（X1）。

## 相关

- 实现：`desktop/src/core/mcp_runtime.py`（运行时）/ `mcp_adapter.py`（导出）/ `export_schema.py`（shape 校验）
- 核查基线：`33_v2.2.0_A5-MCP规范差距核查报告.md`
- CLI 入口：`scripts/nf.py`（`run --fmt mcp` / `serve`）
