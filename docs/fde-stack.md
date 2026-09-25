# NF 在 FDE AI infra 中的中游位置（栈位契约）

> 用途：给做客户交付的前向工程师（FDE）与客户侧技术决策人一份**可判定的位置说明**——NF 不是模型、不是端壳、不是垂直应用，而是**中间那层契约与证据**。
> 纪律：本文只写结果与状态；每条达标线都给可跑命令或可复算判据。

## 一、栈位

```
上：客户交付物               报告 / 手册 / 系统卡 / 上线材料 / 内容产物
                        ▲  交付契约：装载路径 + 验收判据 + 证据包
中：NF 契约层 ← 本仓库       装载契约 · 装配（模块/管线/资产）· 门禁（verify.sh）
                        │   证据（回执单根 + 结论 JSONL + 证书）· 互操作导出 · 标准绑定
                        ▼  基础设施契约：域包/资产的可机检声明
下：模型与协议             模型推理 · 传输（MCP/A2A）· 身份与凭证 · 格式（OpenAPI/SBOM…）
```

一句话：**下层换任何一个（换模型、换协议、换引擎），中层的契约与判据不变**——这就是「模型无关、域中立」在栈上的含义。

## 二、边界契约

**对下（基础设施侧）——NF 要求下层提供什么**

| 契约 | 形态 | 载体 |
|---|---|---|
| 传输/工具面 | MCP（`server/discover` + 四类列表）、A2A Agent Card | `results/interop/mcp.json` / `a2a.json`；他证通道 `docs/interop-thirdparty.md` |
| 内容与格式面 | OpenAPI / AsyncAPI / SBOM / CycloneDX / in-toto / SLSA / PROV / VC | `results/interop/*.json`（12 面）+ 上游判据校验 `results/interop-schema-validation.md` |
| 标准锚面 | 370 条可扩展标准（含扩展点）与 1200 条绑定 | `protocol/standards_catalog.json` · `standards_binding.json` · GEO 出口 `docs/standards/index.md` |

**对上（交付侧）——NF 向 FDE 承诺什么**

| 契约 | 形态 | 复算 |
|---|---|---|
| 装载 | 三条装载路径（A 有 API / B1 能读文件 / B2 纯粘贴） | `AI_ROUTING.md`；机读入口 `llms.txt` |
| 装配 | 模块 + 管线 + 资产的声明式装配（域包自带装配流） | `community/*/protocol.yaml` + `pipelines/*` |
| 门禁 | 单入口验收：`bash verify.sh` | `check1-38` 常驻；期望基线在 `desktop/src/core/quality_baseline.py` |
| 证据 | 回执单根 + 逐门结论 + 产物指纹 | `protocol/RECEIPTS.json` · `fde_sample_run.py --check` |
| 交付样例 | 一次完整 FDE 交付的可跑样例 | `docs/fde-sample/`（五门证据） |

## 三、中游标准的五条达标线（可判定）

1. **可装载**：AI/Agent 按 `llms.txt` 与 `AGENT_START.md` 能取到货并装配；判据 = 入口件在场且其指向路径存在（`nf stats --check` 覆盖入口一致性）。
2. **可质检**：任一交付物都能过单入口门禁；判据 = `bash verify.sh` 退出码 0。
3. **可复现**：同一输入两次产出除时间戳外一致；判据 = 样例 `--run` 两次比对 + `--check` 逐字节比对证据。
4. **零编造**：文档里的数字与状态全部来自产物实算；判据 = `nf stats --check` + `geo_export.py --check` 双绿。
5. **白盒**：判据、证据、口径均可读可复算（不依赖读代码即可验证）；判据 = 每条数字/结论都能回指 `protocol/repo_stats.json`、`RECEIPTS.json` 或 `docs/standards/*`。

## 四、与其它出口的关系

- **自述数字自动化**（`nf stats`）：栈位契约里的每个规模数字都可实算，公开面不会漂。
- **标准目录 GEO 出口**（`docs/standards/`）：下层标准锚面可被生成式引擎直接引用，客户问「这类内容该依据什么标准」时有可引用清单。
- **互操作性从他证**（`docs/interop-thirdparty.md` + `results/interop-thirdparty-status.md`）：下层协议面的「兼容」不靠自证；第三方跑完回填六字段才算他证。
- **FDE 打样**（`docs/fde-sample/`）：把「brief → 装配 → 门禁 → 证据包」跑成可复算样例。

## 五、非目标（明确不做）

- 不做模型训练/推理服务，不做端壳（桌面/移动壳已退役），不做垂直应用本体。
- 不替客户决定业务内容；NF 只保证「产得出、可质检、可复现、零编造、白盒」。
- 不把外部项目规模/评价当作质量背书（`STRATEGY §3`）。
