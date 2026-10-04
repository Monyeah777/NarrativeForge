//! 真源 `core.mcp_runtime` 的**名字表**（`TOOL_DEFS` / `PROMPT_DEFS`）—— 供 `endpoint` 与
//! `mcp_package` 共用。
//!
//! 真源这两张表是**代码常量**（与 `root` 无关），两条判据都只用到每个条目的 `name`。
//! 故本线用**转录的常量表**复刻，**而不是去解析 Python 源码**（后者换覆盖率的代价是脆性）。
//!
//! ⚠️ **覆盖缺口集中在这里**：真源增删工具/提示面时，**只有 `mcp-package` 契约会因此变红**
//! （它判「声明的 tools/prompts 必须与运行时逐名一致」）——这正是它作为「红线：只读面不变」
//! 的价值。若 `mcp-package` 尚未移植，则**没有判据**会红，此时必须重跑
//! `tools/gen_mcp_tables.py`。
//!
//! 本文件由 `tools/gen_mcp_tables.py` 生成，**勿手改**。

// >>> GENERATED TOOL_NAMES by tools/gen_mcp_tables.py（勿手改；重跑生成器覆盖本段）
pub const TOOL_NAMES: [&str; 10] = [
    "asset_get",
    "knowledge_order",
    "library_read",
    "library_search",
    "module_read",
    "pattern_read",
    "pipeline_ls",
    "pipeline_read",
    "registry_query",
    "spec_ls",
];
// <<< GENERATED TOOL_NAMES

// >>> GENERATED PROMPT_NAMES by tools/gen_mcp_tables.py（勿手改；重跑生成器覆盖本段）
pub const PROMPT_NAMES: [&str; 1] = [
    "assemble_guide",
];
// <<< GENERATED PROMPT_NAMES
