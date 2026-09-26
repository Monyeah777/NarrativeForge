# NF 抽象阶梯（layers）

> 最后更新：2026-09-26

> ⛔ 操作指令：本文含可直接执行的命令与判定，读到即执行；勿当资料阅读。

## 这份文件解决什么

NF 原本已有四套「层」的说法：**L0–L3**（依赖治理编号，见 `L3_FROZEN.md`）、**P00–P80**（管线层位）、
**mount_layers**（模块挂载层）、**标准目录 layer**（data/eng/form/gov/iface）。四套各有其义，但
「谁在动」（终端、AI、外部工具）与「被加工的物」（协议、资产）此前混在同一根梯子上——于是出现
「终端在最底、AI 在顶」这类把**角色**当**层**的错位。端壳退役已经证明这种混装的代价：一个角色
被当成一层，整层退役时能力无处安放，只能事后补判据兜住。

本阶梯把两者分开，并把规则变成**每次提交都跑**的判据（不是文档口号）：

- **抽象轴四阶**：契约 → 资产 → 引擎 → 出口。越往下越稳定、越贵改；依赖只许向下。
- **入口面**：只登记角色（人机 / AI 装配线 / MCP / 图书馆取件），**永不作为真源**。
- **验证纵切**：门禁与证据切过四阶，所以它不是一个「层」。

命名纪律：本阶梯只用「**阶 / 面 / 纵切**」，不复用上面四套词汇中的任何一个。

## 怎么用

```bash
python scripts/nf.py layers            # 人读阶梯（含接口面与实现面标注）
python scripts/nf.py layers --json     # 机读（逐阶真源面 / 接口面 / 判据）
python scripts/nf.py layers --verify   # 跑阶梯体检（与 verify check27 同源，退出码即门禁语义）
python scripts/nf.py layers --write    # 刷新本文件的生成区（改真源后必跑）
```

改一件东西时先问三个问题，答案就写在下表里：

1. **它属于哪一阶？**（真源面决定）
2. **别人依赖它的哪一面？**（接口面才允许跨阶依赖；实现面随便改）
3. **这一改算什么档？**（editorial / additive / bump，词表与 `protocol/EXTENSION.md` 同一套）

## 阶梯（生成区 · 真源 = `protocol/LAYERS.json`）

<!-- nf:layers:begin -->
### 抽象轴：四阶

| 阶 | 真源面 | 接口面（跨阶唯一可依赖） | 既有判据 | 状态 / 变更档 |
|---|---|---|---|---|
| **契约** | `01_核心协议.md`、`02_联动注册表.md`、`06_Agent执行协议.md`、`07_官方核心出厂与社区预设导航.md`、`STRATEGY.md`、`protocol/*.md`、`protocol/*.json`、`protocol/schema/*.json`、`desktop/src/core/registry.json` | `protocol/schema/*.json`、`protocol/CONFORMANCE.md`、`desktop/src/core/registry.json` | check13、check28、check29、check30、check31 | active（bump） |
| **资产** | `03_管线库/*.md`、`04_模块库/*/*.md`、`05_资产库/**/*`、`community/**/*`、`library/*.md` | `community/*/protocol.yaml`、`05_资产库/provenance.json` | check7、check8、check9、check10、check11、check14、check15、check16、check23、check24、check34 | active（additive） |
| **引擎** | `desktop/src/core/*.py`、`desktop/tests/**/*.py`、`desktop/scripts/*.py`、`scripts/*.py`、`scripts/*.sh`、`scripts/nf`、`scripts/nf.cmd` | `scripts/nf.py` | check12、check17、check18、check19、check20、check21、check22、check27、check32、check33 | active（additive） |
| **出口** | `results/interop/*.json`、`docs/standards/*.md`、`docs/fde-sample/**/*` | `results/interop/*.json`、`docs/standards/index.md` | check18、check19、check22、check33、check38 | active（editorial） |

### 资产阶五子级（同一格内异质，分开看代价）

| 子级 | 真源面 | 既有判据 | 口径 |
|---|---|---|---|
| **声明** | `community/*/protocol.yaml` | check14 | 契约的实例：改它要走登记三要件（01 §6.1 + 02 §8.3 + registry 投影）。 |
| **内容** | `03_管线库/*.md`、`04_模块库/*/*.md`、`community/*/modules/*.md`、`community/*/pipelines/*.md` | check7、check9、check24 | 模块与管线正文：受编号命名空间与挂载层约束。 |
| **数据** | `05_资产库/**/*`、`community/*/assets/*.md` | check8、check11、check23 | 资产键与溯源台账：判据是可寻址 / 可溯源 / 键无孤儿。 |
| **知识** | `protocol/knowledge_sources.json`、`protocol/transform_log.json` | check37 | 双源知识层：判据是权威分层 / 查询有序 / 时效 / 消化可追溯（与词条类资产不同口径）。 |
| **本体** | `protocol/standards_catalog.json`、`protocol/standards_binding.json`、`protocol/domain_packs.json` | check32 | 概念图与标准目录/绑定：判据是概念密度 / 标准可达性 / 数据真实性。 |

### 入口面（只登记角色，永不作为真源）

| 面 | 入口件 | 服务阶 | 口径 |
|---|---|---|---|
| **人机入口** | `scripts/nf`、`scripts/nf.cmd`、`scripts/nf.py` | engine | 无参数进终端（nf shell → desktop/src/core/terminal.py）；其余参数透传 CLI。 |
| **AI 装配线** | `AGENT_START.md`、`agent_组装指令包_v0.2.md`、`AI_ROUTING.md` | asset | 任意 agent 仅凭仓库地址自助取件组装「完整版」；与 A 线（人机）同等级，不预设模型。 |
| **MCP 服务面** | `docs/mcp.md`、`protocol/mcp_package.json` | engine | 长驻运行时入口 = nf serve（引擎阶 CLI 面）；本面只登记契约与用法文档。 |
| **图书馆取件面** | `ROUTES.md`、`library/INDEX.md`、`library/ALIAS.md` | asset | 按编号寻址 + 镜像路由；馆藏本体属资产阶，本面只负责「怎么找到它」。 |

### 验证纵切（贯穿四阶，不是层）

| 件 | 落点 | 既有判据 |
|---|---|---|
| **verify** | `verify.sh` | check27 |
| **conformance** | `protocol/conformance_report.json` | check35 |
| **audit** | `results/audit` | check36 |
| **receipts** | `protocol/RECEIPTS.json` | check35 |
| **attest** | `docs/attest.md` | check33 |
| **provenance** | `05_资产库/provenance.json` | check23 |

> 本区由 `nf layers --write` 渲染，禁止手改；真源 = `protocol/LAYERS.json`。
<!-- nf:layers:end -->

## 五条纪律（判据见 `desktop/src/core/layer_model.py` 的 L1–L10）

- **依赖只许向下**：契约不依赖任何阶；资产只依赖契约；引擎依赖契约与资产（只读）；出口依赖引擎。
- **跨阶只依接口面**：`02 §8` 登记条目、`protocol.yaml`、资产溯源台账、CLI 命令面——这些才是承诺；
  其余（模块正文、core 内部函数）属实现面，可自由重写。
- **入口不是真源**：入口可以被替换（端壳→终端就是一次替换），任何阶都不得把入口件当真源或反向依赖它。
- **退役是一等公民**：一阶退役必须走「能力重分派 → 入口补齐 → 判据改判 + 记录 + 作者裁决」三步。
- **纵切不参与归属**：`results/audit/**`、`protocol/RECEIPTS.json` 等证据与派生物按 `derived` 名单豁免，
  不靠隐含约定。
