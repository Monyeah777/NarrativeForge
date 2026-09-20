## 状态块（条件先行摘要）

> 本块由产物**确定性提取**（非模型生成）——它是该产物的「状态文本代理」，供重读时先对齐状态。

| 项 | 值 |
|---|---|
| 模块/挂载编号 | M00、M01、M02、M03、M04、M06、M07、M08、M09、M10、M11、M12、M13、M14、M15、M16、M17、M18、M19、M20、M22、M23、M24、M40、M41、M43、M50、M55、M65、M80、M90、M91、M93、M97、M98、P00、P01、P02、P03、P06、P10、P20、P30、P40、P50、P60、P70、P80、P90 |
| NF 编号 | NF-1、NF-TECHDOC-Monyeah777-1 |
| 二级标题数 | 89 |
| 要点行数 | 158 |
| 原文 sha256 | `25ca28cdcccea1a3` |

**关键设置点（原文摘录，非改写）**：

- 04_模块库（官方核心 13 件）
- community/技术文档域包（自带 2 件 + P06 管线）
- 技术文档
- 自包含
- 装配样本
- **需求原话**：「组装一个技术文档生成流程的完整版：要有术语管理与修订记录，能直接交给任意 AI 装载开跑」
- **选件决策**（`nf assemble` 装配计划实测输出）：
- 匹配预设：技术文档域包 → 管线 **P06**（`community/技术文档域包/pipelines/P06_技术文档题材装配流管线.md`）

---

---
id: NF-TECHDOC-Monyeah777-1
type: 技术文档装配（自包含完整版）
title: 技术文档装配流 P06 · 自包含完整版
description: 技术文档域包 P06 装配的自包含完整版——15 件模块正文与管线声明全文内嵌、零资产、无需仓库路径即可装载开跑
author: Monyeah777
license: MIT
generated: 2026-09-15
verified: 2026-09-15
status: active
stale_after: 2027-03-15
sources:
  - 04_模块库（官方核心 13 件）
  - community/技术文档域包（自带 2 件 + P06 管线）
tags:
  - 技术文档
  - 自包含
  - 装配样本
---

> 📚 NF 云端图书馆条目 **NF-TECHDOC-Monyeah777-1** · 入库 2026-09-15 · 投稿人：Monyeah777 · 类型：装配样本（自包含）
> 许可：MIT（登记表同列同值）

> 档位：**全文内嵌式（自包含）**——与 `NF-1`、「西幻生存流 P03 样本」的**引用式**相对。
> 引用式档位的正文以仓库路径与 `assets/` 为准，离线须另粘贴；本件不引用任何仓库路径：
> 15 件模块正文与 P06 管线声明全部内嵌，任何 AI 单文件即可装载开跑。

---

## 0. 装配记录

- **需求原话**：「组装一个技术文档生成流程的完整版：要有术语管理与修订记录，能直接交给任意 AI 装载开跑」
- **选件决策**（`nf assemble` 装配计划实测输出）：
  - 匹配预设：技术文档域包 → 管线 **P06**（`community/技术文档域包/pipelines/P06_技术文档题材装配流管线.md`）
  - 取件模块：**M97 术语管理**（P40 行为决策）、**M98 修订记录**（P60 长期演变）
  - 装配允许集：官方核心 + 包模块 = **44**；本件实际内嵌 **15** 件（核心 13 + 自带 2）
  - 资产：**0 文件**（技术文档域包为机制增强包，无题材资产，同通用核心基础包先例）
  - references：**0**（零跨包引用，`core_only: true`）
- **档位声明**：全文内嵌式。本件与引用式样本的差异不在内容，在**可离线自足性**——
  引用式需要接收方另取仓库文件，本件不需要。
- **缺口声明（如实）**：
  - ① 本件内嵌的是**模块层**正文与管线声明；`01_核心协议`/`02_联动注册表`/`06_Agent执行协议` 三份协议件不内嵌——
    它们是全库共用的上位规范，非本装配的专属件（引用式样本同样如此）。
  - ② 内嵌正文为 2026-09-15 仓库快照的**逐字节复制**，不含改写；上游模块若变更，本件须重新生成。
  - ③ 本件未挂签名锚（`anchor_*` 字段缺省），如需第三方独立验真，另走 `nf library attest`。

## 1. 文档域速览

- **定位**：技术文档装配流（非叙事题材）——把「术语一致性 + 修订可追溯」这两条技术文档的工程纪律，做成可装载的产线。
- **主轴**：M90 结构骨架（P00 位装载 DocState）→ **M97 术语管理**（P40：登记/补定义/冲突检测）→ **M98 修订记录**（P60：版本递增/变更日志/回溯）→ M80 质检渲染（P80）。
- **产物形态**：技术文档装配产物，供下游 agents / mcp / skill 适配器消费。
- **输出门**：M80 是唯一渲染出口（gate 唯一出口，与叙事流同规矩）。
- **域中立证据**：本件与校园情感、西幻生存两类叙事包**共用同一套官方核心**，仅替换题材层的 2 件与 1 条管线——这是「机制不绑域」的可装载证据。

## 2. 管线（P06 · 技术文档题材装配流 · techdoc 九层回卷）

挂载投影（源自 P06 layers，逐层列出）：

| 层 | 挂载（default） | 职责 | 归属 |
|---|---|---|---|
| P00 数据基座 | M00、M90 | 数据槽装载 + 技术文档结构骨架（DocState 产） | 官方核心 |
| P40 行为决策 | **M97** | 术语管理：DocState.terms 登记/补定义/冲突检测 | 本包 |
| P60 长期演变 | **M98** | 修订记录：DocState.revision 版本递增/变更日志/回溯 | 本包 |
| P80 输出呈现 | M80 | 质检渲染（gate 唯一出口） | 官方核心 |
| 全局调度 | M50 | 主循环：回合 begin → 逐层推进 → end 一致性校验 → 回卷 | 官方核心 |

管线声明原文（内嵌）：

```markdown
# 管线 P06 · 技术文档题材装配流
> 社区版「技术文档域包」使用的管线（v2.1.0-C-b 战例落盘）。以「非叙事题材：技术文档装配」为流主轴：官方 M90 技术文档结构（P90 链官方模块，core_modules 依赖引用不搬移）在 P00-P60 位产 DocState 骨架/正文/决策/装配；本包自带 M97 术语管理挂 P40 位做术语域深化（DocState.terms 统一性），M98 修订记录挂 P60 位做修订域追踪（DocState.revision 版本/回溯）；P80 输出呈现仍由官方核心 M80 质检渲染（gate 唯一出口，同叙事流）。
> 实例声明：本管线是通用骨架 **P00**（03_管线库/P00_通用文档生成管线.md）在**技术文档·题材装配**的实例——九层位名沿用骨架；本包 P40/P60 两驻留自带模块（M97/M98），M90 官方模块经依赖引用随流协作（M90 本体不复制进包，I5 单一真相源）。
> **允许编号段固化（R2，v2.1.0-C-b）**：本包 `allowed_modules` 仅限官方核心（M00 / M80 / M90 等 core_modules 13 件含 M90）与本包社区段（M97 / M98，modules/ 在册 2 件）。references=[] 零跨包零借阅。
> **挂载层规避（check15 ③）**：官方 P00 骨架九层 default 均空；既有社区包同层 default（校园 P40=[情感:M22,M40...]、P60=[M40,M65]；西幻 P40=[M04,M11]、P60=[生存:M10...]）与本包 P40=[M97]、P60=[M98] 无交集——M97/M98 新编号唯一，独立装载不冲突（32 方案反证实证）。
```yaml
Pipeline:
  id: P06
  name: 技术文档题材装配流
  structure:
    type: techdoc
    flow:
      - from: P00
        to: P10
      - from: P10
        to: P20
      - from: P20
        to: P30
      - from: P30
        to: P40
      - from: P40
        to: P50
      - from: P50
        to: P60
      - from: P60
        to: P70
      - from: P70
        to: P80
      - from: P80
        to: P00
        condition: 主循环回卷（M50 调度下一回合；官方核心节拍同拍推进）
  layers:
    - id: P00
      name: 数据基座
      description: 官方 M00 数据槽（core 依赖；技术文档 DocState 主载体，M90 结构骨架在此装载——M00/M90 本体驻官方位不搬移）
      optional: false
      default_modules: []
      allowed_modules: [M00, M90]
    - id: P40
      name: 行为决策
      description: 术语决策层：自带 M97 术语管理审 DocState.terms（登记/补定义/冲突检测，publish term_synced）
      optional: false
      default_modules: [M97]
      allowed_modules: [M97]
    - id: P60
      name: 长期演变
      description: 修订层：自带 M98 修订记录维护 DocState.revision（版本递增/变更日志/回溯，publish revision_recorded）
      optional: false
      default_modules: [M98]
      allowed_modules: [M98]
    - id: P80
      name: 输出呈现
      description: 官方核心 M80 输出生成器（gate 唯一出口；读 term_synced/revision_recorded 后质检渲染）
      optional: false
      default_modules: []
      allowed_modules: [M80]
```
```

## 3. 注册表投影

本次装配的执行顺序（可由 P06 layers 与官方 02 执行顺序推出，不硬编码于产物内）：

| 步 | 层 | 模块 | 动作 | 写入 |
|---|---|---|---|---|
| 1 | P00 | M00 | 装载数据槽结构（DocState 主载体） | 初始数据槽 |
| 2 | P00 | M90 | 装载技术文档结构骨架（章节层级/文档类型） | DocState 骨架 |
| 3 | 全局 | M50 | 回合 begin：打快照 | round.begin 快照 |
| 4 | P40 | M97 | 术语登记/补定义/冲突检测 → 发布 `term_synced` | DocState.terms |
| 5 | P60 | M98 | 版本递增/变更日志/回溯 → 发布 `revision_recorded` | DocState.revision |
| 6 | P80 | M80 | 读 `term_synced` / `revision_recorded` 后质检渲染 | 玩家可见文档 |
| 7 | 全局 | M50 | 回合 end：一致性校验 → 回卷下一回合 | 存档 |

> 说明：上表为本次装配的**投影**，供接收方装载时对照；执行顺序的真源仍是接收方所装载的注册表（02 不变式 I5：顺序一律读注册表，禁止硬编码）。

## 4. 模块库（15 件 · 正文全文内嵌）

> 下列 15 段为**逐字节内嵌的模块正文原文**（置于代码围栏内，便于机器验收跳过扫描）。
> 每段前的粗体行标明：模块号 / 名称 / 归属 / 源文件路径（路径仅作溯源标注，装载不需要仓库）。

**4.1 M00_数据结构** · 归属：官方核心 · 溯源：04_模块库/通用类/M00_数据结构.md

```markdown
# 模块 M00 · 数据结构

> 类别：通用｜来源：核心｜挂载点：P00 数据基座（active）｜依赖：无｜被依赖：通用:M10、M50、M01、M02、M04、M07、M80 等

```yaml
machine_contract:
  conformance: "L2"
  schema: "1"
  id: M00
  name: 数据结构
  category: 通用
  layer: P00
  inputs: []
  outputs: []
  events:
    publish: []
    subscribe: []
  interfaces: []
  io_types:
    outputs: {}
    inputs: {}
```

## 1. 职责

定义全系统的**数据槽总线**与四类核心实体的字段契约，是所有模块读写的唯一数据通道。数据隔离（I4）与通信契约（I3）在此落地：模块之间不得直接互访内部状态，只能通过数据槽与事件交换。

## 2. 数据槽总线

```yaml
data_bus:
  schema_version: "1"     # 数据槽总线协议版本（v0.5.0 T2.3 首引；只增不删，结构性变更 bump 并注明迁移）
  注册: 模块启动时声明 [读槽, 写槽]，冲突由 M00 拒绝并报错
  读写: 只允许写自己声明的槽；读他人槽须声明只读，写他人槽视为违例
  生命周期: 每回合结束由 M50 触发快照，供存档（第7章协议）与回卷
  active_pipeline: P01   # 当前装配管线 id（M50 调度/装配切换维护）
  round:                 # 主循环抽象状态槽（M50 写入；world_model slot 投影）
    phase: begin         # 主循环相位（begin/run/end/archive/roll）
    phase_trace: []      # 主循环相位轨迹（旧相位按迁移顺序追加）
```

## 3. 四类核心实体

```yaml
PlayerState:            # 玩家/主角
  schema_version: "1"   # v0.5.0 T2.3 首引；演进只增不删（01 协议 §7 V1）
  identity: [name, race, job, gender, age]
  attributes: {str, dex, con, int, wis, cha}   # 七项基础属性默认 10
  vitals: {health, hunger, thirst, fatigue, temperature, insanity}
  level: {lv, exp, exp_next}
  relations: {}         # 与NPC/阵营的关系深度（M40 写入）
  memories:             # 分层记忆（v0.5.0 T3：占位 [] 细化为三层；M13/M23 写 working 层）
    schema_version: "1" # v0.5.0 T3 首引；只增不删（01 协议 §7 V1）
    working: []         # 工作记忆：回合内即时感知，随回合快照滚动（M50 回合末清理）
    episodic: []        # 情景记忆：关系史/事件史 [{tick, type, target, summary, weight}]（M50 写回）
    semantic: {}        # 语义记忆：长期设定与常识 {key: value}（M50 提炼；M23 读取过滤）
  flags: {}             # 存档标记位

NPCState:
  schema_version: "1"   # v0.5.0 T2.3 首引；演进只增不删（01 协议 §7 V1）
  identity: [name, race, job, hometown]
  personality: {big5: {}, fears: [], impulses: {escape, sexual, mischief}}
  relation: {depth, stage, history: []}   # M40 契约
  memory:               # 分层记忆（v0.5.0 T3：占位 {} 细化为三层；M13 写 working 层）
    schema_version: "1" # v0.5.0 T3 首引；只增不删（01 协议 §7 V1）
    working: []         # 工作记忆：回合内即时感知，随回合快照滚动（M50 回合末清理）
    episodic: []        # 情景记忆：与玩家/其他NPC的关系史/事件史 [{tick, type, target, summary, weight}]（M50 写回）
    semantic: {}        # 语义记忆：长期设定与常识 {key: value}（M50 提炼；M65/M80 只读消费）
  schedule: {}          # 日程（M13）
  alive: true

WorldState:
  schema_version: "1"   # v0.5.0 T2.3 首引；演进只增不删（01 协议 §7 V1）
  time: {tick, day, season, weather}       # 通用:M10/M08 写入
  regions: {}           # M07
  economy: {gold_reserve, market_state}    # M09
  factions: {}          # M14
  gangs: {}             # M15
  settlements: {}       # M16

EventState:             # 回合事件队列（P30 产出、P80 消费）
  schema_version: "1"   # v0.5.0 T2.3 首引；演进只增不删（01 协议 §7 V1）
  queue: []             # 已生成待叙事的事件
  consumed: []          # 已被叙事吞并的事件
  pending_narratives: [] # 事件:M22 合成中的叙事素材
```

## 4. 字段规范约定

- 数值型字段统一 `int/float`，禁止字符串拼数值；缺失字段必须显式 `null`。
- 所有时间戳使用 `tick`（整数回合号）+ `day` 双轨，禁用系统真实时间。
- 新增字段须在注册表第2节模块总表备注登记，否则视为未定义。

## 5. 违例与边界

- 模块未声明写槽而写入 → M00 抛出 `DATA_SLOT_VIOLATION`，该写入丢弃并记录。
- 存档读取时未知字段忽略并告警，不崩溃（向前兼容）。
```

**4.2 M06_任务剧情** · 归属：官方核心 · 溯源：04_模块库/事件类/M06_任务剧情.md

```markdown
# 模块 M06 · 任务剧情
> 类别：事件｜来源：共享｜挂载点：P30 事件生产（active）｜依赖：M20｜被依赖：M13、事件:M22（生存:M10 随社区西幻包）｜发布：`quest_state`

```yaml
machine_contract:
  conformance: "L2"
  schema: "1"
  id: M06
  name: 任务剧情
  category: 事件
  layer: P30
  inputs: [M20]
  outputs: [quest_id, state, tick]
  events:
    publish: [quest_state]
    subscribe: [combat_result, travel_event, chaos_event, reputation_change]
  interfaces: []
  io_types:
    outputs:
      quest_id: string
      state: string
      tick: number
    inputs:
      M20: untyped
```

## 1. 职责
管理**任务生成、剧情叙事与任务链规则**：基于任务叙事模板生成任务，维护任务状态机与链式梯度，按玩家进度发布任务状态。（共享任务机制：quest_narratives 8 任务 / 任务生成规则 / 任务链与奖励梯度）。任务结构生成方——文本措辞与 NPC 演出交 M12/M13；战斗结算类环节在装配社区西幻生存包时走 M04（随包，可选）。

## 2. 任务规则
```yaml
quest:
  id: # 任务叙事模板（8 个基线任务）
  模板结构: 背景/目标/地点/关键NPC/奖励/后续链
  触发条件: 声望门槛(M14) + 地点访问(M07) + 阶段前置
  phase: available | active | complete | failed | chain_next
quest_chain:
  梯度: 每链 3-5 环，奖励随梯度升级（联动 M01 职业成长）
  断链: 玩家失败后提供替代入口（不硬卡剧情）
```
- 8 任务模板、任务链与奖励梯度数值 → 对应领域资产包（随社区包分发，经 asset_get 寻址）。

## 3. 事件契约
```yaml
subscribe:
  combat_result: # M04 → 讨伐类目标达成判定
  travel_event: # M07 → 护送/到达类目标判定
  chaos_event: # M18 → 混沌扰动改写任务目标/生成救援任务
  reputation_change: # M14 → 声望升降开关任务线
publish:
  quest_state:
    payload: {quest_id, phase, objective, location(M07), reward, next_quest}
    subscribers: [M04, M13, 生存:M10]
```

## 4. 结算流程
1. 任务生成器按触发条件实例化任务（取材自 M20 知识库与 M07 地点）。
2. 任务目标与地点/声望门槛绑定。
3. 推进 phase 变更并发布 quest_state。
4. M13 调整相关 NPC 对话目标、M04 准备目标战、生存:M10 处理"任务中死亡"的失败分支。

## 5. 违例与边界
- M06 **只生成任务结构与状态**：不写台词（M12）、不裁决战斗（M04）、不直接涨声望（由任务完成事件经 M14 核算）。
- 任务文本须经 M80 质检门（结构门 + 档位风格门）后输出，M06 内部不做文学渲染。
- 主角死亡导致任务失败的回卷判定归生存:M10 与 M50，M06 不自行判死。
```

**4.3 M08_季节天气** · 归属：官方核心 · 溯源：04_模块库/世界类/M08_季节天气.md

```markdown
# 模块 M08 · 季节天气
> 类别：世界｜来源：共享｜挂载点：P10 世界推进（available）｜依赖：通用:M10｜被依赖：M07、M04、M09（随社区西幻包）｜发布：`weather_state`

```yaml
machine_contract:
  conformance: "L2"
  schema: "1"
  id: M08
  name: 季节天气
  category: 世界
  layer: P10
  inputs: [通用:M10]
  outputs: [region, season, weather, day_phase, modifiers]
  events:
    publish: [weather_state]
    subscribe: [tick_day]
  interfaces: []
  io_types:
    outputs:
      region: untyped
      season: string
      weather: untyped
      day_phase: untyped
      modifiers: untyped
    inputs:
      通用:M10: untyped
```

## 1. 职责
管理**季节循环、天气系统与环境效果**：按世界历推进季节，按季节权重每日生成天气，维护各区域当前环境状态并广播给依赖方。（season_system / environment / location_seasonal_descriptions 结构；资产数据随社区题材包经 asset_get 寻址）。是所有"环境依赖型"模块的天气真相来源。

## 2. 季节与天气规则
```yaml
season_cycle:
  year_length: # 由资产库定义（如 4 季 × 90 日）
  date: # 由 通用:M10 日历驱动
daily_weather:
  generation: 按季节权重掷骰（晴/雨/雪/风暴/异象）
  persistence: 天气状态持续若干 tick_day 后自然更替
environment_effect:
  combat: 影响 M04（暴风雪遮蔽/雨天火焰-）
  travel: 影响 M07（雪封道路/河流涨水）
  market: 影响 M09（冬季农产品涨价 ×1.3）
```
- 各区域季节描述（location_seasonal_descriptions）与效果数值全表 → 对应领域资产包（随社区包分发，经 asset_get 寻址）。

## 3. 事件契约
```yaml
subscribe:
  tick_day: # 通用:M10 → 每日天气演进与季节推进
publish:
  weather_state:
    payload: {region, season, weather, day_phase, modifiers{combat, travel, market}}
    subscribers: [M07, M04, M09]
```

## 4. 结算流程
1. 收到 tick_day，推进日历。
2. 判定季节更替（跨季时广播季节事件）。
3. 按权重生成/延续当前区域天气。
4. 发布 weather_state，订阅方按需应用修正。

## 5. 违例与边界
- M08 **只计算环境状态并广播，不裁决战斗/价格/旅行结果**——修正由 M04/M09/M07 各自应用。
- 不得跳过 tick_day 自行推进时间（时间唯一来源是 通用:M10）。
- 环境异象若构成叙事事件，须交事件:M22 组织，M08 不直接发布叙事。
```

**4.4 M10_时间推进** · 归属：官方核心 · 溯源：04_模块库/通用类/M10_时间推进.md

```markdown
# 模块 通用:M10 · 时间推进

> 类别：通用｜来源：核心｜挂载点：P10 世界推进（active）｜依赖：M00｜发布：`tick_day`

```yaml
machine_contract:
  conformance: "L2"
  schema: "1"
  id: 通用:M10
  name: 时间推进
  category: 通用
  layer: P10
  inputs: [M00]
  outputs: [tick, day, season]
  events:
    publish: [tick_day, minute_tick]
    subscribe: []
  interfaces: []
  tool_face:
    - purpose: 回合/日/分钟三轨时间换算与跨日判定
      candidates:
        - repo: https://github.com/arrow-py/arrow
          ref: 1.3.0
          license: BSD-2-Clause
          note: 成熟时间库，仅作实现参考；引用不等于背书，AI 可自造等价能力
      guidance:
        要算什么: 从 tick 折算 day、minute、is_new_day 与 season_ctx
        输出形状: 整数 tick/day/minute；布尔 is_new_day；字符串 season_ctx
        对接字段: outputs=[tick, day, season]，事件 payload 见第 4 节
        常见坑: 分钟制只在 P03 启用；跨日只发布一次 tick_day；禁止模块自行推进时间
  io_types:
    outputs:
      tick: number
      day: number
      season: string
    inputs:
      M00: state
```

## 1. 职责

驱动系统时间轴，维护 `tick / day / season` 三轨时钟，并广播回合推进事件。所有"每日/每回合"结算的模块（M01、M19、M08、M09、M40）均以本模块的推进信号为节拍。

## 2. 时间尺度

| 尺度 | 单位 | 用途 | 适用管线 |
| --- | --- | --- | --- |
| tick | 1 回合 | 主循环最小步进（M50 回卷单位） | P01/P02/P03 |
| day | 1 日 = 若干 tick | 日程/刷新/好感结算 | P01/P02 |
| 分钟制 | 1 日细分 | 生存消耗逐分钟结算 | 社区西幻生存包（P03） |

- 社区校园情感包（P02）以 `day` 为主节拍：上学日/周末区分日程。
- 社区西幻生存包（P03）启用分钟制子结算：`fatigue/hunger` 每 10 分钟刻扣减，M10 负责把分钟刻度折算为 tick 事件。

## 3. 推进流程

```yaml
advance:
  1. tick += 1
  2. 若跨日（day 变更）→ 发布 tick_day（含新 day 号、season 状态）
  3. 若 P03 分钟制 → 额外发布 minute_tick（每 10 分钟刻度）
  4. 等待订阅者完成结算（同步），再返回 M50 继续下一层
```

## 4. 事件契约

```yaml
publish: tick_day
  payload: {tick, day, is_new_day: bool, season_ctx}
  subscribers: [生存:M01, 生存:M19, M08, M09, M40]
publish: minute_tick        # 仅 P03 启用
  payload: {tick, minute}
  subscribers: [生存:M01, M04]
```

## 5. 违例与边界

- 任何模块禁止自行推进系统时间；只允许请求 `M10.advance(n)`。
- 时间回卷（回溯/读档）由 M50 统一触发，M10 只接受回卷指令并重放事件。
```

**4.5 M12_NPC对话** · 归属：官方核心 · 溯源：04_模块库/事件类/M12_NPC对话.md

```markdown
# 模块 M12 · NPC 对话
> 类别：事件｜来源：共享｜挂载点：P50 交互执行（active）｜依赖：M20、M13｜被依赖：M13｜发布：无

```yaml
machine_contract:
  conformance: "L2"
  schema: "1"
  id: M12
  name: NPC 对话
  category: 事件
  layer: P50
  inputs: [M20, M13]
  outputs: []
  events:
    publish: []
    subscribe: []
  interfaces: []
  io_types:
    outputs: {}
    inputs:
      M20: untyped
      M13: untyped
```

## 1. 职责
管理**NPC 对话模板与交互行为素材**：维护 13+ NPC 的对话模板体系（闲聊/任务线索/好感回应/秘密情报），按触发条件供给可选项与台词。（npc_dialogue_templates 13+NPC / 对话类别与触发规则，模板内容随社区题材包扩展）。是"台词库"，与 M13 状态机构成模板-状态互查的双向耦合。

## 2. 对话模板规则
```yaml
dialogue_template:
  npc_id: # 13+NPC 全表
  category: 闲聊 | 任务线索 | 好感回应 | 秘密情报 | 事件回应
  trigger_condition:
    好感档位: # 由 M13 好感度函数提供
    任务阶段: # 由 M06 quest_state 提供
    阵营声望: # 由 M14 提供
  lines: # 台词条目（按档位 DNA 质检，若有）
  options: []  # 玩家可选项
  effect: 好感影响 | 情报解锁 | 任务推进（回传 M13）
```
- 13+NPC 对话模板全表 → 对应领域资产包（随社区包分发，经 asset_get 寻址）。

## 3. 模板-状态互查
- M12 提供**静态台词**，M13 提供**运行时 NPC 状态**（好感/日程/目标/记忆）。
- 对话触发 = M13 判定"该不该聊"→ M12 按条件检索"聊什么"→ 效果回写 M13。
- 二者循环依赖在注册表已登记；**执行顺序由 M50 第 9 步统一编排**（先 M13 状态、后 M12 出词）。

## 4. 事件契约
```yaml
subscribe: []  # 不直接订阅运行时事件；经 M13 查询接口取状态
publish: []    # 不发布事件；对话效果经 M13 的 interaction_update 统一广播
```

## 5. 违例与边界
- M12 只提供台词与选项素材，**不裁决好感数值**（好感函数在 M13）、**不生成任务**（M06）。
- 台词含隐藏域信息（秘密/伏笔）时，供给玩家须经 M23 认知边界裁剪。
- 台词文本遵循 M80 风格门（档位 DNA 台词规则，若有）；禁止长篇独白。
```

**4.6 M13_NPC交互** · 归属：官方核心 · 溯源：04_模块库/事件类/M13_NPC交互.md

```markdown
# 模块 M13 · NPC 交互
> 类别：事件｜来源：共享｜挂载点：P30 事件生产（active）｜依赖：M12、M06、M20｜被依赖：M40、M14（随社区包）、事件:M22｜发布：`interaction_update`

```yaml
machine_contract:
  conformance: "L2"
  schema: "1"
  id: M13
  name: NPC 交互
  category: 事件
  layer: P30
  inputs: [M12, M06, M20]
  outputs: [npc_id, action, result, tick]
  events:
    publish: [interaction_update]
    subscribe: [quest_state, level_up]
  interfaces: []
  io_types:
    outputs:
      npc_id: string
      action: string
      result: string
      tick: number
    inputs:
      M12: untyped
      M06: untyped
      M20: untyped
```

## 1. 职责
管理 **NPC 运行时状态机、记忆、日程、目标与好感函数**：实例化 NPC 个体，维护其与玩家的好感数值与交互历史，把每次交互结算为 interaction_update 广播给关系/声望/叙事模块。（NPCInstance 状态机 / NPC记忆 / 日程行为 / 目标系统 / 死亡继承 / 好感度函数）。**NPC 个体真相来源**（群体声望归 M14；M14 随社区西幻包）。

## 2. NPC 状态机
```yaml
npc_instance:
  id: # 实例化自资产库 NPC 模板
  state: 身份/位置(M07)/职业(M01)/种族(M02)
  affinity: 玩家好感数值（区间，联动 M40 关系深度模型校准）
  memory: []  # 记忆条目（经 M23 认知边界管理：记得什么/不记得什么）
  schedule: 日程（每日更新，受 通用:M10 tick 驱动）
  goals: []   # 目标（任务 M06 / 生存 / 关系 M40）
  alive: true # 死亡与继承联动 生存:M10 / M19
affinity_function:
  输入: 对话(M12) / 赠礼 / 帮助 / 冲突
  输出: affinity_delta → interaction_update
```

## 3. 事件契约
```yaml
subscribe:
  quest_state: # M06 → 任务改变 NPC 目标与可用对话
  level_up: # M01 → 玩家等级影响 NPC 态度基线
publish:
  interaction_update:
    payload: {npc_id, type, affinity_delta, context, flags[]}
    subscribers: [M40, M14, 事件:M22]
```

## 4. 结算流程
1. 每日/事件驱动 NPC 日程更新（睡觉/工作/移动/待机）。
2. 玩家发起交互 → 经 M12 检索台词、玩家选择生效。
3. 好感函数结算 affinity_delta。
4. 发布 interaction_update：M40 折算关系深度、M14 折算阵营声望贡献、事件:M22 采集叙事素材。

## 5. 违例与边界
- M13 裁决 **NPC 个体**的好感/记忆/目标；恋爱档位归 M40/M41，群体声望归 M14。
- 记忆写入须遵守 M23：玩家不可见的记忆不进入可见域。
- NPC 死亡判定交生存:M10，M13 只执行"死亡后状态清理与继承"。
- 交互产生的文本演出归 M12/M80，M13 不做文学渲染。
```

**4.7 M20_世界知识库** · 归属：官方核心 · 溯源：04_模块库/事件类/M20_世界知识库.md

```markdown
# 模块 M20 · 世界知识库
> 类别：事件｜来源：共享｜挂载点：P70 叙事素材（active）/ P00 数据基座（available）｜依赖：M00｜被依赖：M06、M12、M13；M01–M04 随社区西幻包｜发布：无

```yaml
machine_contract:
  conformance: "L2"
  schema: "1"
  id: M20
  name: 世界知识库
  category: 事件
  layer: P70
  inputs: [M00]
  outputs: []
  events:
    publish: []
    subscribe: []
  interfaces: [query]
  io_types:
    outputs: {}
    inputs:
      M00: state
```

## 1. 职责
管理**世界观常识库**：物理法则、地理、魔法理论、社会结构、种族知识、历史与时间季节、原罪碎片设定，按需供给各模块作为"常识上下文"，防止角色做出违反世界观的行为。（world_knowledge 知识域：8 种族 + 地理 + 物理 + 魔法 + 社会 + 生物 + 物品 + 常识 + 时间季节 + 原罪碎片；条目内容随题材资产包）。**只读知识库，不含数值规则**（数值在各模块/资产库）。

## 2. 知识条目结构
```yaml
knowledge_entry:
  domain: 物理 | 魔法 | 社会 | 生物 | 物品 | 地理 | 常识 | 历史 | 时间季节 | 原罪碎片
  key: 知识键（如 races.elf / physics.magic_rule / fragments.sin）
  content: 条目内容（面向引擎的客观描述）
  access: # 供给条件：角色是否"应该知道"（经 M23 认知裁剪）
  consumers: [M01, M02, M03, M04, M06, M12, M13] # 允许消费方
```
- 全量知识条目 → 对应领域资产包（随社区包分发，经 asset_get 寻址）（world_knowledge 区块）。

## 3. 供给与查询
```yaml
query(domain, key, viewer):
  1. 检索条目；未知键 → 返回空并告警（防幻觉）
  2. 按 viewer 认知边界（M23）裁剪：隐藏域内容不供给
  3. 返回条目供消费方做一致性校验
装载时机: 执行顺序第 4 步（M50 调度：世界常识装载）
```

## 4. 与各模块的配合
- M01/M02：职业/种族能力是否符合世界观设定。
- M03/M04：技能/魔法效果与知识库规则一致性。
- M06：任务背景取材（历史/地理常识）。
- M12/M13：NPC 台词与行为不得违反其种族/社会常识。

## 5. 违例与边界
- M20 是**只读常识库**：不裁决行为、不产出剧情、不持有数值曲线。
- 消费方检索不到的键视为"知识不存在"，禁止凭 LLM 先验脑补写入剧情。
- 新知识条目须走资产库新增（[EXT-资产] 扩展点），运行时不可直接改写知识库。
```

**4.8 M22_事件叙事** · 归属：官方核心 · 溯源：04_模块库/事件类/M22_事件叙事.md

```markdown
# 模块 事件:M22 · 事件叙事
> 类别：事件｜来源：核心｜挂载点：P30 事件生产（active）｜依赖：无（监听事件总线；具体事件源随社区题材包装配）｜被依赖：M80｜发布：`narrative_event`

```yaml
machine_contract:
  conformance: "L2"
  schema: "1"
  id: 事件:M22
  name: 事件叙事
  category: 事件
  layer: P30
  inputs: []
  outputs: [type, payload, tick]
  events:
    publish: [narrative_event]
    subscribe: [death_trigger, relationship_change, chaos_event, ghost_event, market_event, production_output, interaction_update]
  interfaces: []
  io_types:
    outputs:
      type: untyped
      payload: object
      tick: number
    inputs: {}
```

## 1. 职责
管理**叙事事件生成、时间线推进与故事驱动**：汇聚各源模块发布的零散事件（任务/混沌/关系/遗憾/死亡/市场），校验因果一致性后组织为按序的 narrative_event 流，驱动连贯叙事时间线。（事件生成机制 / 事件类型体系 / 事件触发条件与流程 / 事件与叙事联动）。是**叙事编排者**——不做数值结算，只做因果编排。

## 2. 事件编排规则
```yaml
narrative_event:
  type: 成长 | 关系 | 冲突 | 世界变迁 | 秘密揭晓 | 遗憾沉淀
  source: 事件来源模块（quest/chaos/romance/ghost/death/market…）
  beats: []  # 叙事节拍（供 M80 渲染的素材序列）
  pov: # 视角域（M23）：玩家可见/推断/隐藏
  causal_chain: # 前因链：每事件必须有前因，禁止空降
consistency_check:
  冲突 → 降级/重排/要求源模块修正
  去重 → 同类同因事件合并
  编排 → 因果顺序写入时间线
```

## 3. 事件契约
```yaml
subscribe:
  death_trigger: # 生存:M10 → 死亡事件入线
  relationship_change: # M40 → 关系里程碑
  chaos_event: # M18 → 世界扰动
  ghost_event: # M65 → 遗憾显形
  market_event: # M09 → 经济大事
  production_output: # M17 → 传奇造物
  interaction_update: # M13 → 关键交互
publish:
  narrative_event:
    payload: {seq_no, type, beats[], pov, causal_chain}
    subscribers: [M80, M65]
```

## 4. 编排流程
1. 接收各源模块事件（本回合内暂存）。
2. 一致性校验 + 去重 + 因果链接（查 M00 事件总线历史）。
3. 决定哪些入线、以何顺序、玩家视角如何呈现（M23 裁剪）。
4. 发布 narrative_event → M80 渲染为正文；M65 检查是否沉淀遗憾。

## 5. 违例与边界
- 事件:M22 **只编排因果与顺序**，不执行数值结算（结算在各源模块内完成）。
- 玩家未知的线索放入隐藏域（M23），不得提前进入可见叙事。
- 情感:M22（三冲动）事件由其直发，事件:M22 编排时对 NPC 冲动事件**豁免一次需显式标记**（注册表注释）。
- 叙事线须尊重既有角色行为与设定（一致性纪律），禁止性格漂移。
```

**4.9 M23_认知边界** · 归属：官方核心 · 溯源：04_模块库/通用类/M23_认知边界.md

```markdown
# 模块 M23 · 认知边界

> 类别：通用｜来源：核心｜挂载点：P20 角色状态（active）｜依赖：M00｜被依赖：M13、事件:M22

```yaml
machine_contract:
  conformance: "L2"
  schema: "1"
  id: M23
  name: 认知边界
  category: 通用
  layer: P20
  inputs: [M00]
  outputs: []
  events:
    publish: []
    subscribe: []
  interfaces: [cognition.filter]
  io_types:
    outputs: {}
    inputs:
      M00: state
```

## 1. 职责

执行**视角裁剪**：叙事只能呈现"主角当前可知"的信息。任何角色内心、墙后对话、未感知事件一律不得进入输出素材——这是视角纪律（主角可知原则）的系统侧保障。

## 2. 认知域模型

```yaml
cognition:
  可见域: 主角在场、可观察（场景内 + 已知情报）
  推断域: 可见域证据可推出的结论（允许角色"猜测"，须标注不确定）
  隐藏域: 其他角色内心/动机、未触发事件、系统真实状态
裁剪规则:
  - 输出素材仅允许来自 可见域 ∪ 推断域
  - 隐藏域信息不得直接叙述；只可通过行为、物件、表情等可见证据间接透出
```

## 3. 双重真相支持

- 系统层可保留完整真相（供 M65 遗憾沉淀、M41 恋爱判定使用）；
- 呈现层（M80）只能拿到裁剪后的素材；
- 同一画面可承载两层含义：表层为角色所见，深层真相留白（视角纪律的自然延伸）。

## 4. 联动

- 读取：M13（NPC 记忆）、M20（世界知识库）、M55（情书匿名性）、M65（遗憾真相）。
- 事件：M23 不发布事件；M13/事件:M22 每次取素材前须先过 `cognition.filter()`。

## 5. 违例与边界

- 输出中出现隐藏域直述 → 质检 fail（视角纪律违例，M80 结构门 S5）。
- 主角失忆/昏迷/离线场景：可见域降为空，只能输出环境白描。
```

**4.10 M24_组合规则** · 归属：官方核心 · 溯源：04_模块库/通用类/M24_组合规则.md

```markdown
# 模块 M24 · 组合规则

> 类别：通用｜来源：共享｜挂载点：P70 叙事素材（active）｜依赖：M00｜被依赖：无

```yaml
machine_contract:
  conformance: "L2"
  schema: "1"
  id: M24
  name: 组合规则
  category: 通用
  layer: P70
  inputs: [M00]
  outputs: []
  events:
    publish: []
    subscribe: []
  interfaces: [resolve]
  io_types:
    outputs: {}
    inputs:
      M00: state
```

## 1. 职责

系统**组合/扩展规则**的唯一结算入口：技能融合、元素组合、词条合成等"两物合出新物"的逻辑统一在此登记与判定，防止各模块各自为政产生规则冲突。

## 2. 组合配方注册表

```yaml
combinations:
  skill_fusion:        # 技能融合 9 配方（源：社区西幻包 M03.2）
    input: [技能A, 技能B]
    output: 融合技能（新名+效果叠加规则）
  element_pair:        # 二元素组合 22 条（源：社区西幻包 M11.6）
    input: [元素A, 元素B]
    output: 复合法术效果
  spell_word:          # 词根合成（源：社区西幻包 M11.4/11.5）
    input: [词根序列]
    output: 咒语（文字即咒语）
  race_hybrid:         # 亚种杂交（源：社区西幻包 M02.5）
    input: [种族A, 种族B]
    output: 亚种天赋表
```

## 3. 判定流程

```yaml
resolve(inputA, inputB):
  1. 查组合表 → 命中配方返回 output
  2. 未命中 → 返回 null（不自动脑补组合，禁止自由发挥）
  3. 命中但条件不足（等级/材料/羁绊）→ 返回 blocked + 缺什么
  4. 结算结果写入 P70 素材槽，供 M80 呈现
```

## 4. 扩展约定

- 新增组合配方须在此登记并附带出处（源框架章节号或用户自定义包）。
- 用户自定义包可覆盖默认配方，优先级：用户自定义 > 社区题材包 > 核心默认。

## 5. 违例与边界

- 禁止在组合表中不存在时自行生成"看似合理"的新组合——保持可解释、可复现。
- 组合失败只返回 blocked 原因，不消耗材料（可重试），除非配方注明消耗。
```

**4.11 M50_主循环** · 归属：官方核心 · 溯源：04_模块库/通用类/M50_主循环.md

```markdown
# 模块 M50 · 主循环

> 类别：通用｜来源：核心｜挂载点：调度器（全局）｜依赖：M00｜被依赖：M80

```yaml
machine_contract:
  conformance: "L2"
  schema: "1"
  id: M50
  name: 主循环
  category: 通用
  layer: 调度器
  inputs: [M00]
  outputs: [intent_id, mode, text]
  events:
    publish: [intent_received]
    subscribe: []
  interfaces: []
  world_model:
    abstract_state:
      variables:
        - name: pipeline
          kind: string
          source: M50
          slot: data_bus.active_pipeline
          note: 当前装配管线 id
        - name: tick
          kind: integer
          source: 通用:M10
          slot: WorldState.time.tick
          note: 时间推进节拍；M50 只读
        - name: phase
          kind: string
          source: M50
          slot: data_bus.round.phase
          note: 主循环抽象相位
        - name: phase_trace
          kind: array
          item_kind: string
          source: M50
          slot: data_bus.round.phase_trace
          note: 主循环相位轨迹；旧相位按迁移顺序追加
      initial:
        pipeline: P01
        tick: 0
        phase: begin
        phase_trace: []
    transition:
      initial_phase: begin
      phases:
        - phase: begin
          next: run
          guard: 回合开始并快照 M00 数据槽
          writes: []
        - phase: run
          next: end
          guard: 按 02 §6 执行官方核心与社区包合并顺序
          writes: [memory.working]
        - phase: end
          next: archive
          guard: I2 核心固定结构/字段一致性校验通过
          writes: []
        - phase: archive
          next: roll
          guard: end 通过后执行回合末记忆写回
          writes: [memories.memory.episodic.items, memories.memory.semantic.facts]
        - phase: roll
          next: begin
          guard: 回卷至 begin 快照并进入下一回合
          writes: [memory.working]
    invariants:
      - "抽象状态变量必须是 world_model.abstract_state 显式声明的有限集"
      - "tick 单调不减"
      - "phase 只在 begin/run/end/archive/roll 有限集合内迁移"
      - "每个 phase 显式声明 next，迁移图从 initial_phase 全可达"
      - "非 M50 模块不得直写 M00 数据槽"
    checks:
      - kind: finite_phase
        field: phase
        values: [begin, run, end, archive, roll]
      - kind: monotonic
        field: tick
      - kind: finite_sequence
        field: phase_trace
        values: [begin, run, end, archive, roll]
  io_types:
    outputs:
      intent_id: untyped
      mode: untyped
      text: untyped
    inputs:
      M00: state
```

## 1. 职责

回合调度器。按注册表 §6 执行顺序（官方核心装配 10 步，真相源见 02 §6）依序驱动各层模块；装配社区领域包后按包索引动态合并（R3）。回合结束回卷并进入下一回合。主循环决定"谁先跑、谁后跑、何时结算"。

## 2. 执行顺序（官方核心 10 步为真相源，见 02 §6；社区包按索引动态合并）

官方核心装配（P01）的执行顺序以 **02_联动注册表.md §6 为唯一真相源（I5）**，本模块不再维护静态编号清单，避免双源漂移。装配社区领域包后（P02 校园情感 / P03 西幻生存），按包索引将题材模块合并进对应层位（R3），生成最终执行顺序。

官方核心装配（P01）10 步速览（仅便于阅读，真相源以 02 §6 为准）：

```text
 1. M00 数据结构（初始化）
 2. M50 主循环（调度开始）
 3. 通用:M10 时间推进
 4. M20 世界知识库（常识装载）
 5. M23 认知边界（视角裁剪）
 6. 事件:M22 / M06 / M13（事件生产）
 7. M12 NPC 对话（交互执行）
 8. M20 / M24（叙事素材与组合校验）
 9. M80 输出生成器（渲染输出）
10. M50（回卷下一回合）
```

> **示例非真相源**：上述 10 步为 02 §6 的快照副本，仅供本模块快速查阅；一切冲突以 02 §6 为准（I5 冲突裁决）。社区包合并示意（最终顺序以各包 README 与 02 §8 登记为准）：P02 校园情感将情感:M22 / M40 / M41 / M43 / M55 / M65 追加至 P40/P60 层，P03 西幻生存将 M01 / M02 / M19 / M08 / M18 / M13 / M04 / M11 / M17 / M07 / M09 / M14 / M15 / M16 / 生存:M10 追加至对应层位。

## 3. 调度规则

```yaml
scheduler:
  层间同步: 每一步等待上一步完成（同步串行），保证数据因果
  层内: 该层多模块按注册表 available→active 过滤后执行
  跳过: 模块声明 skip（条件不满足）→ 跳过并记 skip_reason
  异常: 单模块异常不中断整轮；捕获后记 error_log，回合继续
  管线切换: 换用 P02/P03 时同步切换挂载表与执行顺序
```

## 4. 回合生命周期

```yaml
round:
  begin:   快照（M00 数据槽）
  run:     按注册表 §6 顺序执行（官方核心 10 步 + 社区包动态合并）
  end:     校验一致性（I2 核心固定：结构/字段不漂移）
  archive: 回合末记忆归档（memory_writeback 三规则，见下）—— end 通过后执行
  roll:    回卷至 begin 快照

memory_writeback:  # 回合末记忆写回事件（v0.5.0 T3；经 M00 数据槽总线发布，仅 M50 于 archive 步触发）
  working→清理:    # working 层随回合快照滚动：end 后清空重置本回合感知，不跨回合滞留
  episodic→写回:   # 重要事件写回 episodic：命中 {情感闭环、关系变化、世界事件、死亡/离别} 的条目
                   # 带 tick 追加至 memories/memory.episodic.items（M13/M23 产出，M50 归档）
  semantic→沉淀:   # episodic 提炼沉淀 semantic：跨回合稳定的关系与设定事实提炼为 semantic.facts
                   # （长期设定与常识；M23 读取过滤，M65/M80 只读消费）
  约束:            # 仅写 M00 声明的 memories/memory 槽（I4 数据隔离）；消费方只读，
                   # 直写他模块 memory 字段 = DATA_SLOT_VIOLATION
```

## 5. 违例与边界

- 禁止任何模块在 step 之外自行触发其他模块逻辑（必须经由注册表订阅/挂载）。
- 死循环防护：单回合执行超时/步数超限 → M50 强制打断并回卷。
```

**4.12 M80_输出生成器** · 归属：官方核心 · 溯源：04_模块库/通用类/M80_输出生成器.md

```markdown
# 模块 M80 · 输出生成器

> 类别：通用｜来源：核心｜挂载点：P80 输出呈现（active）｜依赖：M50、事件:M22｜被依赖：无

```yaml
machine_contract:
  conformance: "L2"
  schema: "1"
  id: M80
  name: 输出生成器
  category: 通用
  layer: P80
  inputs: [M50, 事件:M22]
  outputs: []
  events:
    publish: []
    subscribe: []
  interfaces: []
  io_types:
    outputs: {}
    inputs:
      M50: untyped
      事件:M22: untyped
```

## 1. 职责
将 P70 叙事素材渲染为最终可读文本。这是质检门的**执行器**：输出先过结构门（硬 · 全域通用），再按档位加载风格门（软 · 档位 DNA；档位未配置 DNA 时仅过结构门），质量分档后放行、自纠或重写。

## 2. 质检双门（2026-09-08 重构：风格门档位化，可变物不入协议层）
### 2.1 结构门（硬 · 全域通用 · 可机器核验）
- 编号合法：文中 Mxx/Pxx 全部在册（02 联动注册表），不在册即编造 = fail
- 资产键存在：引用资产键可经 asset_get 取到，悬空 = fail
- 层级完整：素材覆盖当前回合管线要求段（P00–P80）
- 术语一致：与协议术语表一致，不混用
- 无跨层直写：素材无越层输出（M23 视角纪律前置，隐藏域直述 = fail）
### 2.2 风格门（软 · 档位 DNA · 可配置）
- 渲染前加载当前档位 DNA 配置（资产键 STYLE_DNA 或档位 protocol.yaml dna 字段）；
- 档位 DNA 由用户/域包自定义——**协议层不内嵌任何固定风格条目**（自定义规范与示例档见 `05_资产库/用户自定义/STYLE_DNA.md`；作者默认文学档本源：校园情感包资产 5.11）；
- 档位无 DNA 配置时，仅过结构门即放行（文风由运行方自担）。

## 3. 质检门（质量门禁 · 声明式 gate_action 流水线）
```yaml
gate:                      # 双门判定（2.1 结构门 + 2.2 档位 DNA）
  pass: 结构门全过 且（无档位 DNA 或 档位 DNA 符合 ≥ 档位阈值）→ 直接输出
  warn: 结构门全过 且 档位 DNA 部分符合（4–5 条或档位自定阈值）→ 自纠后输出（标注修订点）
  fail: 结构门违例（硬错）或 档位 DNA 连续不符（<4 条或档位自定阈值）→ 整段重写；
        连续 3 次 fail 降级为白描模式（保底可读，仅结构门）
前置校验: 素材必须已过 M23 认知边界裁剪（隐藏域直述 = fail，视角纪律）
gate_action:               # 声明式门禁流水线（v0.5.0 T4；对齐 NovelClaw 可观测运行思想）
  pass: [direct]           # 直接输出（零干预放行）
  warn: [self_correct, log_revision]    # 自纠后输出，修订点记入决策记录
  fail: [rewrite, retry_limit: 3, fallback: white_sketch]   # 整段重写；连续 3 次降级白描（保底可读）
记忆读取: 经 M00 数据槽只读接口消费三层记忆——episodic 校验叙事与关系史一致性、
          语义 semantic 校验长期设定不冲突（v0.5.0 T3 只读声明）；只读不改状态（I4），
          记忆改写一律交 M50 回合末 memory_writeback 处理
gate_decision_record:      # 决策记录（结构化行，走系统日志独立通道，不进叙事文本——见 §5）
  格式: gate|<流水号>|tick|档位(pass/warn/fail)|命中项(结构项/DNA条)|修订点|重写次数|fallback
  样例: gate|014|t_2042|warn|S1,S3,D1,D3,D5|L7 直述改物件化|0|none
        gate|015|t_2043|fail|S2|隐藏域直述|3|white_sketch
```
## 4. 输出格式

- 社区校园情感包题材流：短段落 + 白描/诗化交替 + 极简对话（P02 风格渲染）。
- 社区西幻生存包题材流：战斗/生存结算可读化，死亡描述用 death_descriptions 池（P03）。
- 通用回退：无管线标注时按 P01 中性渲染。

## 5. 违例与边界

- 输出字数上限由管线参数控制；禁止输出 JSON/YAML 原始结构（只输出叙事文本）。
- 玩家可见内容与系统结算内容分离：系统日志走独立通道，不进叙事文本。
- 门禁为**唯一输出闸**（I2 核心固定）：叙事（M80）与技术文档（P90 经 M80）产出均不可绕过本 gate。
- gate 决策记录（§3 gate_decision_record 格式）走系统日志独立通道，禁止混入叙事/文档正文。
```

**4.13 M90_技术文档结构** · 归属：官方核心 · 溯源：04_模块库/技术文档类/M90_技术文档结构.md

```markdown
# 模块 M90 · 技术文档结构

> 类别：技术文档｜来源：领域演示（P90 实证，社区扩展示例）｜挂载点：P90（active，default）｜依赖：M00｜被依赖：M80
> 用途：README「扩展新领域三步之①」的实证模块——证明 04_模块库可无损接入非叙事领域模块（verify.sh 仅要求叙事五类别基线下限，新类别/新模块自动纳入计数，可增不减）。

```yaml
machine_contract:
  conformance: "L2"
  schema: "1"
  id: M90
  name: 技术文档结构
  category: 技术文档
  layer: P90
  inputs: [M00]
  outputs: [DocState, doc_delta]
  events:
    publish: [doc_structure_ready, doc_delta_committed]
    subscribe: [intent_received]
  interfaces: []
  io_types:
    outputs:
      DocState: untyped
      doc_delta: untyped
    inputs:
      M00: state
```

## 1. 职责
把「自然语言意图（如：写一份 API 迁移说明）」解析为技术文档的结构化要素：标题层级、章节骨架、术语表、表格 / 代码块引用、修订记录；按资产键 `TECH_TEMPLATES` 选择章节模板、`TECH_RULES` 过规范一致性校验。是 P90 技术文档生成管线（P00 骨架在非叙事领域的实例装配）的领域装载模块。

## 2. 协议声明（01 §2 模块协议）
```yaml
Module:
  id: M90
  name: 技术文档结构
  layer: P90
  inputs: [M00, intent]          # 数据槽就绪 + 用户意图载荷
  outputs: [DocState, doc_delta] # 文档结构状态 + 章节增量
  events:
    publish: [doc_structure_ready, doc_delta_committed]
    subscribe: [intent_received]
  core:
    assets: [TECH_TEMPLATES, TECH_RULES]   # I4：仅经五接口访问，禁止直读
    logic:
      解析: 意图 → 文档类型判定（guide/reference/tutorial/note）→ 选 TECH_TEMPLATES 骨架
      装配: 章节 → 术语/表格/代码块引用登记 → 更新 DocState
      校验: 按 TECH_RULES 检查结构一致性（章节闭合/术语统一/修订记录）
  replaceable: true
```

## 3. 数据槽契约（扩展 M00 data_bus · 技术文档域）
```yaml
DocState:
  title: string
  doc_type: guide|reference|tutorial|note
  chapters: [{id, heading, level, body_refs[], status}]
  terms: {term: {def, first_use_chapter}}   # 术语表
  refs: {link_refs[], code_refs[]}          # 引用闭合登记
  revision: [{ver, date, change}]           # 修订记录
```

## 4. 事件联动
- publish `doc_structure_ready`：结构骨架就绪，通知 M80 进入渲染质检。
- subscribe `intent_received`：接收用户意图作为 P90 装载输入（登记于 02 §7.4）。

## 5. 核心逻辑（伪代码）
```
1. intent_received → doc_type = classify(intent)
2. skeleton = asset_get(TECH_TEMPLATES, doc_type)      # 取章节骨架
3. chapters = expand(skeleton, intent)                 # 拆章/节/小节
4. for each draft: doc_delta = compose(draft)          # 片段生产（P30 位）
5. tech_review: check(TECH_RULES, DocState)            # 规范一致性
6. publish doc_structure_ready
```

## 6. 不变式遵守（01 §5）
- I1 三正交分离：只声明"结构能力"，不持有管线顺序（顺序在 P90）与数据内容（内容在 05 资产）。
- I2 核心固定：复用 M00 数据槽 / M50 主循环 / M80 输出门，未替换任何核心模块。
- I3 通信契约：仅经 DocState 数据槽与 doc_structure_ready 事件通信。
- I4 数据隔离：TECH_TEMPLATES / TECH_RULES 只经 asset_get / asset_query 访问。
- I5 真相唯一：挂载与执行顺序以 02_联动注册表 §7 登记为准，禁止硬编码。

## 7. 与 P90 的关系
P90 九层中，M90 承担装载（P00 位骨架解析）、生产（P30 位片段）、决策（P40 位模板选择）、装配（P50 位章节组装）、一致性（P60 位跨章校验）等位职责；输出层 P80 仍由核心 M80 质检渲染（gate 唯一出口）。
```

**4.14 M97_术语管理** · 归属：技术文档域包（自带） · 溯源：community/技术文档域包/modules/M97_术语管理.md

```markdown
# 模块 M97 · 术语管理

> 类别：技术文档｜来源：社区（技术文档域包自带，M91-99 社区段）｜挂载点：P40（active，default）｜依赖：M90 技术文档结构、M00｜被依赖：M80
> 用途：README「扩展新领域三步之①」社区 techdoc 域包首模块——在官方 M90（技术文档结构）之上维护 DocState.terms 术语表（定义/首次使用章节/统一性校验），M90 专注结构骨架、M97 专注术语一致，I1 正交分工。

```yaml
machine_contract:
  conformance: "L2"
  schema: "1"
  id: M97
  name: 术语管理
  category: 技术文档
  layer: P40
  inputs: [M90, M00]
  outputs: [term_delta]
  events:
    publish: [term_synced, term_conflict_detected]
    subscribe: [doc_structure_ready, term_conflict_detected]
  interfaces: []
  io_types:
    outputs:
      term_delta: untyped
    inputs:
      M90: untyped
      M00: state
```

## 1. 职责
维护技术文档的术语表一致性：从 DocState.terms 读取术语条目（M90 结构生产时登记），做首次使用章节标注与定义补全；检测同一术语多定义/首用未定义等冲突（term_conflict_detected）；发布 term_synced 供 M80 质检参考。是本包（技术文档题材增强）相对官方 M90 的增值位——M90 负责骨架，M97 负责术语域。

## 2. 协议声明（01 §2 模块协议）
```yaml
Module:
  id: M97
  name: 术语管理
  layer: P40
  inputs: [M90, M00, intent]
  outputs: [term_delta, term_status]
  events:
    publish: [term_synced, term_conflict_detected]
    subscribe: [doc_structure_ready, term_conflict_detected]
  core:
    assets: []                     # 零题材资产（机制增强；同通用包 M93-96 先例）
    logic:
      登记: doc_structure_ready → 扫描章节正文 → 首次使用术语登记 first_use_chapter
      补定义: 术语无定义 → 查已有术语表 / 留待人工（term_status=pending_definition）
      校验: 多定义同一术语 / 首用未定义 → term_conflict_detected
      同步: 校验通过 → term_synced（DocState.terms 收敛）
  replaceable: true
```

## 3. 数据槽契约（扩展 M90 DocState · 术语域）
```yaml
term_delta:
  term: string
  first_use_chapter: string
  definition: string          # 空 = 待补
  status: ok|pending_definition|conflict
term_status:
  total: int
  defined: int
  conflicts: [string]
```

## 4. 事件联动
- subscribe `doc_structure_ready`（M90 发布）：结构骨架就绪 → M97 扫描登记术语。
- subscribe `term_conflict_detected`：本模块自检发现多定义/未定义 → 内部状态标记。
- publish `term_synced`：术语表收敛 → M80 质检可读术语一致性。

## 5. 核心逻辑（伪代码）
```
1. doc_structure_ready → for chapter: scan(chapter.body) → collect terms
2. term not in DocState.terms → add with first_use_chapter, definition=""
3. term.definition=="" and known → backfill；else status=pending_definition
4. dup definition → status=conflict → publish term_conflict_detected
5. no conflict → publish term_synced
```

## 6. 不变式遵守（01 §5）
- I1 三正交分离：只声明术语能力，不持管线顺序（顺序在 P06 管线）与内容（M90 产 DocState）。
- I2 核心固定：依赖 M90/M00 数据槽，未替换核心模块（M90 官方位不动）。
- I3 通信契约：仅经 term_delta / term_status 与 term_synced 事件通信。
- I4 数据隔离：无自有资产（零资产机制增强）。
- I5 真相唯一：挂载与登记以 02 §8.5 + registry protocols[] 为准（本包第 5 条投影）。

## 7. 与官方链的关系
本模块是 M90（官方，挂 P90 位）的题材增强——M90 产 DocState（含 terms 雏形），M97 挂 P40 位做术语域深化；不复制 M90 正文（core_modules 依赖引用，I5），是「扩展新领域三步」社区自带模块示范。
```

**4.15 M98_修订记录** · 归属：技术文档域包（自带） · 溯源：community/技术文档域包/modules/M98_修订记录.md

```markdown
# 模块 M98 · 修订记录

> 类别：技术文档｜来源：社区（技术文档域包自带，M91-99 社区段）｜挂载点：P60（active，default）｜依赖：M90 技术文档结构、M00｜被依赖：M80
> 用途：README「扩展新领域三步之①」社区 techdoc 域包次模块——维护 DocState.revision 修订记录（版本号/变更日志/回溯），M90 专注结构骨架、M98 专注变更追踪，I1 正交分工。

```yaml
machine_contract:
  conformance: "L2"
  schema: "1"
  id: M98
  name: 修订记录
  category: 技术文档
  layer: P60
  inputs: [M90, M00]
  outputs: [revision_entry, revision_log]
  events:
    publish: [revision_recorded]
    subscribe: [doc_structure_ready, doc_delta_committed]
  interfaces: []
  io_types:
    outputs:
      revision_entry: untyped
      revision_log: untyped
    inputs:
      M90: untyped
      M00: state
```

## 1. 职责
维护技术文档的修订历史：M90 每产出结构增量（doc_delta）或正文变更（doc_delta_committed）时，M98 追加修订条目（版本号递增/变更摘要/日期/作者），维护可回溯的变更日志（revision_log）；供 M80 渲染「修订记录」章节与读者追溯。是本包相对官方 M90 的增值位。

## 2. 协议声明（01 §2 模块协议）
```yaml
Module:
  id: M98
  name: 修订记录
  layer: P60
  inputs: [M90, M00, intent]
  outputs: [revision_entry, revision_log]
  events:
    publish: [revision_recorded]
    subscribe: [doc_structure_ready, doc_delta_committed]
  core:
    assets: []                     # 零题材资产（机制增强）
    logic:
      变更: doc_delta_committed → 比较前版 DocState → 提取变更点
      登记: 版本号 v{n+1} + 变更摘要 + date + author → revision_log 追加
      回溯: 按版本号取历史快照 → 供 diff 展示
      发布: revision_recorded → M80 渲染修订章节
  replaceable: true
```

## 3. 数据槽契约（扩展 M90 DocState · 修订域）
```yaml
revision_entry:
  ver: string          # v1.0 → v1.1
  date: string
  author: string
  changes: [string]    # 变更摘要列表
revision_log:
  entries: [revision_entry]
```

## 4. 事件联动
- subscribe `doc_structure_ready`（M90 发布）：首版 v1.0 基线登记。
- subscribe `doc_delta_committed`：后续变更增量 → 追加 revision_entry。
- publish `revision_recorded`：修订登记完成 → M80 质检/渲染可读。

## 5. 核心逻辑（伪代码）
```
1. doc_structure_ready → revision_log.entries=[v1.0 基线]
2. doc_delta_committed → cur=DocState；changes=diff(prev, cur)
3. changes 非空 → ver=bump(prev.ver)；append entry；publish revision_recorded
4. query(ver) → 返回该版本 DocState 快照（回溯）
```

## 6. 不变式遵守（01 §5）
- I1 三正交分离：只声明修订能力，不持管线顺序（顺序在 P06）与内容（M90 产 DocState）。
- I2 核心固定：依赖 M90/M00，未替换核心模块。
- I3 通信契约：仅经 revision_entry / revision_log 与 revision_recorded 事件通信。
- I4 数据隔离：无自有资产。
- I5 真相唯一：挂载与登记以 02 §8.5 + registry protocols[] 为准。

## 7. 与官方链的关系
同 M97——M90 官方挂 P90 位产 DocState，M98 挂 P60 位做修订域深化；不复制 M90 正文（core_modules 依赖引用，I5）。
```

## 5. 资产（0 文件）

- 本装配**零题材资产**：技术文档域包为机制增强包（同通用核心基础包先例，无 `assets/` 目录）。
- 因此本件不存在资产键表，也不存在资产正文引用的缺口——**这是它天然可自包含的结构原因**。
- 对照：校园情感包 29 资产文件 / 西幻生存包 23 资产文件，其引用式档位正源于资产正文体量。

## 6. 装载指引

给接收方 AI 的装载四步（对齐 06 执行协议）：

1. **读本件**：§2 取管线结构，§3 取执行顺序投影，§4 取各模块的契约与逻辑。
2. **对表**：按 §3 的表逐层挂载；模块契约见 §4 对应的内嵌段（含 `machine_contract` 机读块）。
3. **执行**：按 M50 主循环推进——P00 装载骨架 → P40 术语同步 → P60 修订记录 → P80 质检渲染；回合 begin/end 打快照与回卷。
4. **验收**：过 §7 自检清单；任一不满足先修正再交付。

边界提醒：

- 本件内嵌的是**模块层与管线层**；上位协议件（01/02/06）为全库共用规范，本件不含其正文。
- 若接收方需要与官方核心保持严格同步，请以仓库最新版为准重新生成本件（见本次生成方式）。

## 7. 自检清单（交付前逐项核对）

- [ ] §0–§7 八段骨架齐备
- [ ] §4 内嵌段数 = 15（两包自带 2 + 官方核心 13）
- [ ] §3 执行顺序与 §2 管线 layers 一致（default 挂载不冲突）
- [ ] 形态为**全文内嵌**：接收方在不访问仓库时可完成装载
- [ ] 缺口声明与会话一致（协议件不内嵌 / 快照时点 / 未挂签名锚）
- [ ] 机器验收通过：nf assemble --check 本文件（需求原话见 §0）

---

*—— 自包含样本 · 由 build_selfcontained_sample.ps1 生成（可复现）· 2026-09-15 · 内嵌 15 件*

