# NarrativeForge MCP 接入（`nf serve` · 40 总纲 v2.7 波A S1-E3 / X2）

> **状态**：公开化文档已随基础层 v2.7 落地；**连接实证（E3：标准 MCP 客户端装载实测）尚未执行**——文末「E3 实测记录」为预留占位，回填前不宣称「转正」。README 能力宣告以本文件状态为准。

## 这是什么

NF 提供 MCP（Model Context Protocol）stdio 服务 `nf serve`：

- 把「MCP 快照」（`nf run --fmt mcp` 导出的 `.json`）烧成 JSON-RPC stdio 会话（换行分隔 UTF-8 消息）；
- **只读面**：实现 `resources/list` + `resources/read`，无 `tools`/`prompts` 写路径——写请求一律 `-32601 METHOD_NOT_FOUND`；
- **uri 白名单**：`resources/read` 只接受快照内已登记 uri，未知 uri 返回 `-32602 INVALID_PARAMS`（不泄露目录结构）；
- 协议版本对齐 `2025-11-25`（逐条实证对照见 33 号 A5 核查报告，G1/G2/G4 已勾销）。

安全定位（C2 最小安全层）：只读 + 白名单——适合把仓库/内容库能力**只读暴露**给 agent 检索，天然无写面。

## 三步接入

### 1. 产快照

先用全链 CLI 导出一份 `--fmt mcp` 快照（质量门须 PASS 才产出，语义同 verify 铁律）：

```bash
python scripts/nf.py run \
  --pipeline <管线 .md 路径，如 community/校园西幻轻混组合包/pipelines/P04_轻混装配流管线.md> \
  --modules <参与装配模块 full_id，逗号分隔，如 通用类:M00,轻混类:M91,轻混类:M92,通用类:M80> \
  --seed --fmt mcp --dest <输出目录>
```

`--seed` 用于演示/自测（把官方核心 + 轻混组合包装载进临时 store）；真实装配时用 `--store` 指向含所选模块的工作区。产物快照 `.json` 即服务的数据源。

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

## 能力表（与 mcp_runtime 实现一一对应）

| 方法 | 实现 | 说明 |
|---|---|---|
| `initialize` | ✅ | 协议版本 `2025-11-25`；`serverInfo` 自述（name/version 经握手，非快照文件顶层） |
| `notifications/initialized` | ✅ 静默 | 通知无 id，不应答 |
| `ping` | ✅ | 返回 `{}` |
| `resources/list` | ✅ | 快照登记资源纯元数据（无 text 字段） |
| `resources/read` | ✅ | 白名单 uri → `contents[].text`；未知 uri → `-32602` |
| `tools/*` / `prompts/*` 等写路径 | ❌ | `-32601 METHOD_NOT_FOUND`（只读安全层，天然拒写） |

标准错误码：`-32700` 解析错误 / `-32600` 非法请求 / `-32601` 方法不存在 / `-32602` 参数非法 / `-32603` 内部错误。

## E3 实测记录（预留占位 · 待回填）

| 日期 | 客户端 | 结果（成功/失败/差距） | 差距与修复 |
|---|---|---|---|
| 待实测 | 待实测 | 待回填 | 待回填 |

> 回填原则：真实装载/调用结果，不造假。E3 完成后据此把 README 宣告逐项转正（S13），并沉淀 fixture 入测试库（X1）。

## 相关

- 实现：`desktop/src/core/mcp_runtime.py`（运行时）/ `mcp_adapter.py`（导出）/ `export_schema.py`（shape 校验）
- 核查基线：`33_v2.2.0_A5-MCP规范差距核查报告.md`
- CLI 入口：`scripts/nf.py`（`run --fmt mcp` / `serve`）
