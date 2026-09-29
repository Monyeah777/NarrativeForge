# README（反向证明夹具：故意保留陈旧数字，**不是**真 README）

> 用途：证 `probes/handoff_integrity_probe.py` 的「文档数字自洽」判据**不是恒绿**。
> 跑法：`python probes/handoff_integrity_probe.py --skip-relocate --readme probes/_fixtures/_readme_drift_variant.md`
> 期望：**exit 1**，并逐条报出下面三处漂移（面数 / 交付形态 fNN / 最新分片号）。

**现成规模**：CLI **177 面逐字节全同 + 1 边界面** · conformance 26/27 · MCP 28 工具 · 自检 **218 例** · 全量探针 **34 个**。

| 形态 | 体积 | 说明 |
|---|---|---|
| `<当片 dist 目录>/nf-dotnet-win-x64-f98-2026-09-27` | 72.3 MB | 陈旧当片形态（故意留旧；此处刻意不写绝对路径） |

## 第一百零五片（故意留旧的分片号）
