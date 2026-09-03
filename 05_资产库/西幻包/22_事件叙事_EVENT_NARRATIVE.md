## M22 事件与叙事生成

> **数据源**：`/tmp/extract_test.txt` 行6880-6960（register_narrative_system 叙事系统架构）、行8775-8840（register_freedom_system 自由度系统）、行1543-1600（season_system 季节事件池）、行25382+（encounter_tables 遭遇表）、行32109+（quest_narratives 任务叙事）、行30411（location_descriptions）、行31346（story_fragments）
> **依赖**：@M18 混沌与随机事件、@M20 世界知识库、@M21 数据接口与外部调用、@M07 世界地图与地点、@M13 NPC交互系统、@M04 战斗系统、@M06 任务与剧情、@M10 死亡与重生
> **状态**：✅ 已填充 v1.0

### 22.1 事件生成机制

事件生成机制负责从五大事件来源（随机事件池/季节事件池/混沌事件/任务事件/遭遇事件）中判定、抽取并执行事件，是世界动态推进与玩家体验变化的核心驱动层。

#### 22.1.1 事件类型体系

事件按来源划分为五种类型，对应五套独立的数据源与触发逻辑：

| 事件类型 | 数据源 | 触发方式 | 典型示例 |
|---|---|---|---|
| 随机事件 | 随机事件池（A11，按野外/城镇/地牢分类） | 区域探索时按概率抽取 | 野外遇到商队、城镇突发盗窃、地牢触发陷阱 |
| 季节事件 | 季节事件池（四季各含事件条目） | 每日更新时按当季事件概率触发 | 春季桃花汛、夏季干旱、秋季丰收祭、冬季暴雪 |
| 混沌事件 | chaos_quests（自由度系统混沌委托库） | generate_chaos_quest 随机选取 | 荒诞委托任务（如"帮史莱姆找对象"） |
| 任务事件 | quest_narratives（任务叙事库） | 任务接受/进行/完成三阶段触发 | 铁匠的请求、失踪的儿子、强盗威胁 |
| 遭遇事件 | encounter_tables（按区域类型分类） | roll_encounter 判定后抽取 | 野外遭遇野狼群、河流遇到商人车队 |

**随机事件池结构**（附录A11）：按区域类型分类（野外/城镇/地牢），每条目含事件名称、触发条件、描述文本、效果列表，供探索系统按区域抽取。

**季节事件池结构**（行1543-1600）：四季各含事件条目，每事件含五要素——名称、触发概率、触发条件、描述文本、执行效果。春季：桃花汛（概率0.1，条件：区域类型=河流且连续雨天≥3）、春耕节（概率0.2，条件：日期=15）；夏季：干旱（概率0.15，条件：连续无雨≥7天）、雷暴（概率0.1，条件：天气=暴雨）；秋季：丰收祭（概率1.0，条件：日期=30）、野兽囤粮等；冬季：暴雪封路、兽群迁徙等。

**遭遇事件池结构**（encounter_tables，行25382起）：按区域类型分类（野外/河流/森林等），每条目含名称、描述、enemies列表、weight权重、min_level/max_level等级范围、type类型——战斗型（含enemies敌人列表）、event型（含event_id，如 merchant_caravan/nomad_camp/wild_horses/goblin_trader）、loot型（含loot_table，如 abandoned_cart）。


#### 22.1.2 生成接口总览

事件生成统一通过 EXTERNAL_DATA 键调用（@M21 联动），核心生成接口如下：

| 接口键 | 所属系统 | 职责 | 数据源 |
|---|---|---|---|
| generate_chaos_quest | 自由度系统 | 从 chaos_quests 随机选取混沌委托任务，可按玩家位置调整 | chaos_quests（A区混沌委托库） |
| trigger_season_event | 季节系统 | 遍历当季事件、按概率触发一个季节事件（每日限一个） | 季节事件池（四季条目） |
| roll_encounter | 遭遇系统 | 判定是否遭遇：基础概率0.001×危险度×旅行时间 | 区域危险度/旅行时间 |
| generate_encounter | 遭遇系统 | 从 spawn_table 按权重选择怪物配置并生成怪物组 | spawn_table / spawn_group |
| generate_event_desc | 叙事系统 | 生成事件描述文本（支持 NORMAL/LITERARY 两种风格） | event_narratives / style_rules |
| random_encounter | 占位接口 | 核心伪代码预留的随机遭遇 lambda 占位，可替换为 roll_encounter + generate_encounter 正式实现 | —（待实现） |

**generate_chaos_quest 调用链**：`register_freedom_system`（行8783）注册 → `EXTERNAL_DATA["generate_chaos_quest"](player_state, context)` → 从 `self.external_data.get("chaos_quests", [])` 中 `random.choice` 选取混沌委托任务 → 可选按玩家位置（城市/野外）调整任务目标 → 返回任务对象（含荒诞目标、奖励、时限）。

**trigger_season_event 调用链**：每日更新时调用 → 根据当前季节取出当季事件列表 → 逐条 `check_event_conditions` 检查触发条件（区域类型/连续天数/日期/天气等）→ 按事件触发概率 `random.random() < probability` 判定 → 命中后 `execute_event` 执行事件效果（修改世界状态/玩家状态/生成描述文本）→ 每日只触发一个季节事件。

**roll_encounter 调用链**：旅行/探索移动时调用 → 计算遭遇概率 = 0.001 × 区域危险度 × 旅行时间 → 概率判定命中后按区域类型（野外/河流/森林等）选择对应 encounter_tables 子表 → `random.choice` 随机抽取一条遭遇条目 → 返回遭遇对象。

**generate_encounter 调用链**：遭遇条目为战斗型时调用 → 从 spawn_table 按 weight 权重随机选择怪物配置 → 调用 spawn_group 按配置生成怪物组（含数量/等级/种类）→ 返回怪物组并切入战斗（@M04 联动）。


#### 22.1.3 事件触发条件与流程

**事件触发条件分类**：五类事件各自维护独立的触发条件体系，条件检查统一收敛于 `check_event_conditions`：

| 条件类型 | 判定依据 | 适用事件 |
|---|---|---|
| 区域条件 | 玩家所在区域类型（野外/城镇/地牢/河流/森林等） | 季节事件（桃花汛需河流区域）、遭遇事件（按区域选表） |
| 时间条件 | 日期/季节/时段 | 季节事件（春耕节日期=15、丰收祭日期=30） |
| 天气条件 | 天气状态（暴雨/连续雨天/连续无雨天数） | 季节事件（干旱需连续无雨≥7天、雷暴需暴雨） |
| 概率条件 | random.random() < 触发概率 | 全部五类事件（遭遇基础0.001×危险度×旅行时间） |
| 状态条件 | 玩家/世界状态（通缉等级/生活方式/任务进度等） | 混沌事件（通缉等级影响犯罪委托）、任务事件（按阶段触发） |

**事件触发标准流程**（五类事件统一）：

1. **触发时机**：探索移动（遭遇/随机事件）、每日更新（季节事件）、行动解析（混沌事件）、任务阶段变更（任务事件）各自触发；
2. **条件检查**：调用 `check_event_conditions` 校验区域/时间/天气/状态条件，不满足则跳过；
3. **概率判定**：通过 `random.random() < probability` 进行概率门控，未命中则本次不触发；
4. **事件抽取**：从对应数据池（season_events/chaos_quests/encounter_tables/随机事件池/quest_narratives）中按权重或随机选取具体事件条目；
5. **效果执行**：`execute_event` 执行事件效果——修改世界状态（天气/季节/区域）、玩家状态（属性/物品/任务）、生成描述文本；
6. **结果返回**：返回事件结果对象（含事件名/描述文本/效果明细），供上层系统（叙事系统/UI/日志）消费。

**季节事件触发示例**（春季）：每日更新 → 当前季节=春季 → 事件池=[桃花汛(概率0.1, 条件:河流+连续雨天≥3), 春耕节(概率0.2, 条件:日期=15)] → 遍历并检查条件：若玩家在河流区域且连续雨天≥3，桃花汛条件满足 → 概率0.1判定 → 命中则执行效果（河流涨水/淹没低洼区域/生成描述文本）→ 当日不再触发其他季节事件。

**遭遇事件触发示例**：旅行移动 → 区域危险度=2.0、旅行时间=3小时 → 遭遇概率=0.001×2.0×3=0.006 → 判定命中 → 区域类型=森林 → 从森林遭遇表随机抽取 → 抽中战斗型"野狼群"（含enemies列表/等级范围）→ generate_encounter 按权重生成怪物组 → 切入战斗（@M04）。


### 22.2 叙事生成机制

叙事生成机制基于 NarrativeManager 统一管理全部叙事文本生成，支持普通（NORMAL）与文学（LITERARY）两种风格，从9类外部JSON数据读取模板动态生成地点描述、NPC对话、事件描述、战斗/死亡描述、任务叙事等文本。

#### 22.2.1 叙事类型体系

**NarrativeStyle 风格枚举**（两种）：`NORMAL`（普通风格，直白叙事）/ `LITERARY`（文学风格，调用 literary_phrases 与 style_rules 润色，输出诗化表达）。

**NarrativeType 类型枚举**（9种）：

| 类型 | 说明 | 生成方法 | 外部数据依赖 |
|---|---|---|---|
| LOCATION | 地点描述 | _generate_location_description | location_descriptions |
| NPC_DIALOGUE | NPC对话 | _generate_npc_dialogue | npc_dialogue_templates |
| EVENT | 事件描述 | _generate_event_narrative | event_narratives |
| FRAGMENT | 碎片化叙事 | _generate_fragment | story_fragments |
| COMBAT | 战斗描述 | _generate_combat_narrative | combat_narratives |
| SKILL | 技能描述 | _generate_skill_narrative | style_rules |
| QUEST | 任务叙事 | _generate_quest_narrative | quest_narratives |
| DEATH | 死亡描述 | _generate_death_narrative | death_narratives |
| BIRTH | 新生描述 | （与 DEATH 对应，用于后代出生叙事） | 遗传系统数据 |

**NarrativeContext 上下文类**：承载叙事生成所需全部上下文，含六要素——`player`（玩家状态）、`world`（世界状态）、`type`（叙事类型，取自 NarrativeType 枚举）、`parameters`（附加参数字典，如目标对象/数值）、`style`（风格，NORMAL/LITERARY）、`cached_fragments`（已缓存的碎片引用，用于碎片化叙事串联）。

**BIRTH 类型说明**：与 DEATH（死亡叙事）对应，用于后代出生场景（@M19 遗传与后代联动），为新生儿生成新生描述文本，通常与遗传特质（继承技能/能力突变）文本组合输出。


#### 22.2.2 叙事管理流程

**NarrativeManager 管理器类**（register_narrative_system 行6888 注册）：

1. **数据加载**：构造函数加载9类外部数据（location_descriptions/npc_dialogue_templates/event_narratives/story_fragments/literary_phrases/combat_narratives/death_narratives/quest_narratives/style_rules）；
2. **碎片去重**：维护 `triggered_fragments` 集合，已触发过的碎片不重复触发，保证碎片化叙事的唯一性与推进性；
3. **风格切换**：`set_narrative_style(style)` 切换 NORMAL/LITERARY 风格，影响全部后续生成文本的措辞与润色。

**generate_narrative 主接口分发流程**：

```
EXTERNAL_DATA["generate_narrative"](context)  # context = NarrativeContext
  → 按 context.type 分发：
      LOCATION      → _generate_location_description
      NPC_DIALOGUE  → _generate_npc_dialogue
      EVENT         → _generate_event_narrative
      FRAGMENT      → _generate_fragment
      COMBAT        → _generate_combat_narrative
      SKILL         → _generate_skill_narrative
      QUEST         → _generate_quest_narrative
      DEATH         → _generate_death_narrative
  → 子方法从对应外部数据读取模板 → 填充 parameters 参数 → 按 style 润色 → 返回文本
```

**8个注册键总览**（全部经 register_narrative_system 注册至 EXTERNAL_DATA）：

| 注册键 | 功能 | 典型调用方 |
|---|---|---|
| narrative_manager | NarrativeManager 管理器实例 | 各系统通过管理器访问 |
| generate_narrative | 主叙事生成接口（按类型分发） | 事件系统/战斗系统/NPC系统 |
| set_narrative_style | 切换叙事风格（NORMAL/LITERARY） | 全局配置/剧情演出 |
| generate_combat_desc | 战斗描述快捷生成（COMBAT） | 战斗系统（@M04）每回合调用 |
| generate_death_desc | 死亡描述快捷生成（DEATH） | 死亡系统（@M10） |
| generate_event_desc | 事件描述快捷生成（EVENT） | 事件系统（22.1） |
| generate_fragment | 碎片叙事快捷生成（FRAGMENT） | 剧情演出/探索触发 |
| generate_location_desc | 地点描述快捷生成（LOCATION） | 地图探索（@M07） |
| generate_npc_dialogue | NPC对话快捷生成（NPC_DIALOGUE） | NPC交互（@M13） |


#### 22.2.3 叙事数据依赖

NarrativeManager 依赖9类外部JSON数据（经 register_narrative_system 加载，@M21 数据接口联动）：

| 数据键 | 内容 | 数据位置（源文件） | 状态 |
|---|---|---|---|
| location_descriptions | 地点描述模板库 | 行30411起 | ✅ 已确认JSON |
| npc_dialogue_templates | NPC对话模板库 | 注册说明提及 | 🔶 待补充定位 |
| event_narratives | 事件叙事模板库 | 注册说明提及 | 🔶 待补充定位 |
| story_fragments | 碎片化叙事库 | 行31346起 | ✅ 已确认JSON |
| literary_phrases | 文学风格短语库 | 注册说明提及 | 🔶 待补充定位 |
| combat_narratives | 战斗叙事模板库 | 注册说明提及 | 🔶 待补充定位 |
| death_narratives | 死亡叙事模板库 | 注册说明提及 | 🔶 待补充定位 |
| quest_narratives | 任务叙事库 | 行32109起 | ✅ 已确认JSON |
| style_rules | 风格规则库（文学润色规则） | 注册说明提及 | 🔶 待补充定位 |

**已确认的JSON数据结构**：

- **location_descriptions**（行30411起）：地点→描述文本映射，供 LOCATION 类型按地点ID查询生成描述；
- **story_fragments**（行31346起）：碎片化叙事条目（含碎片ID/条件/文本），供 FRAGMENT 类型按条件触发，triggered_fragments 集合去重；
- **quest_narratives**（行32109起）：任务叙事库，每任务含六要素——giver（发布者NPC）、accept（接受文本，2个变体）、progress（进行中文本，3个变体）、complete（完成文本，2个变体）、target（目标描述）、reward（奖励描述）；已确认任务：铁匠的请求（giver=old_tom，target=收集10块铁矿石，reward=50金币+铁匕首）、失踪的儿子（giver=susan，target=森林中寻找少年，reward=100金币+疗伤草×3）、强盗威胁（giver=zack，target=消灭强盗营地，reward=200金币+经验100）、山贼清剿（giver=冒险者公会，target=杀死山贼首领，reward=500金币+公会积分）。

**待补充数据说明**：npc_dialogue_templates / event_narratives / literary_phrases / combat_narratives / death_narratives / style_rules 六类数据仅在 register_narrative_system 注册说明（行6913-6921）中提及键名，源文件内未定位到独立JSON区块，需由外部超级库（附录A区扩展）提供，或在后续版本中补充数据区块。


### 22.3 事件与叙事联动

事件生成（22.1）与叙事生成（22.2）构成"事件驱动叙事、叙事反哺事件"的闭环：事件系统判定并执行事件，叙事系统将事件结果转化为玩家可感知的文本；叙事系统在特定场景（碎片触发/死亡）反向产生新事件。

**事件→叙事调用链**：

1. 事件系统触发事件（季节/遭遇/混沌/任务）→ 事件执行 `execute_event` 产生效果；
2. 事件效果需要文本呈现时，调用叙事接口：`generate_event_desc`（EVENT类型）/ `generate_combat_desc`（COMBAT类型）/ `generate_location_desc`（LOCATION类型）；
3. 叙事系统从对应模板库读取模板 → 填充事件参数（事件名/地点/角色/数值）→ 按当前风格（NORMAL/LITERARY）生成描述文本；
4. 文本返回事件系统，随事件结果对象一并交付上层（UI/日志/演出）。

**叙事→事件反向联动**：

1. **碎片触发**：探索/剧情演出时检查 story_fragments 条件 → 触发碎片叙事（FRAGMENT）→ 碎片内容可能携带事件效果（解锁区域/给予物品/改变世界状态），转化为新事件执行；
2. **死亡叙事**：死亡发生时（@M10）调用 `generate_death_desc` 生成死亡描述 → 同时按死亡触发器判定是否衍生后续事件（继承/惩罚/转生）；
3. **任务叙事**：任务三阶段（accept/progress/complete）触发对应文本（QUEST类型）→ 阶段文本输出的同时执行任务效果（给予奖励/推进目标），任务完成文本后联动生成后续事件。

**风格联动**：`set_narrative_style` 全局切换叙事风格——NORMAL 风格用于日常探索/系统提示，LITERARY 风格用于关键剧情（季节事件演出、碎片叙事、死亡/新生场景），文学风格自动调用 literary_phrases 与 style_rules 润色输出。

**模块联动总览**（@标注）：

| 联动模块 | 联动内容 |
|---|---|
| @M04 战斗系统 | 战斗每回合 generate_combat_desc；遭遇战斗切入（22.1.2） |
| @M06 任务与剧情 | quest_narratives 三阶段叙事；任务事件触发 |
| @M07 世界地图与地点 | generate_location_desc 地点描述；区域类型决定遭遇/季节事件条件 |
| @M10 死亡与重生 | generate_death_desc 死亡叙事；死亡触发器衍生事件 |
| @M13 NPC交互系统 | generate_npc_dialogue 对话包装；任务发布者NPC（giver） |
| @M18 混沌与随机事件 | 混沌事件（generate_chaos_quest）；随机事件池（A11） |
| @M19 遗传与后代 | BIRTH 新生叙事；遗传特质文本 |
| @M20 世界知识库 | world_knowledge 数据驱动叙事模板与描述 |
| @M21 数据接口与外部调用 | 全部注册键经 EXTERNAL_DATA 统一调用 |

#### 22.4 扩展点
- **[EXT-规则] 新增事件类型**：在事件类型体系（22.1.1）基础上新增自定义事件类型——在事件池 JSON 中追加新分类（如特殊事件池/副本事件池），并在事件触发流程（22.1.3）的条件检查注册表中挂载新条件类型；事件抽取逻辑（random.choice/权重选择）为数据驱动，无需改动即可支持新类型。
- **[EXT-规则] 新增触发条件**：触发条件分类表（22.1.3 五类：区域/时间/天气/概率/状态）之外，可在条件检查函数中注册自定义条件（如好感度条件、世界状态条件、声望条件），以"条件名 + 判定函数"形式挂载到条件注册表，季节/遭遇/混沌事件的 conditions 字段可直接引用新条件。
- **[EXT-资产] 新增事件池条目**：随机事件池（野外/城镇/地牢）、季节事件池（四季各含五要素：名称/触发概率/条件/描述/效果）、遭遇事件表（encounter_tables 战斗/event/loot 三种类型）均为纯数据驱动——向对应 JSON 追加条目即可扩展事件内容，无需修改代码。
- **[EXT-资产] 新增叙事模板数据**：九类外部数据（location_descriptions/npc_dialogue_templates/event_narratives/story_fragments/literary_phrases/combat_narratives/death_narratives/quest_narratives/style_rules）全部为 JSON 模板——追加新条目即可扩展叙事文本；其中六类待补充数据（npc_dialogue_templates/event_narratives/literary_phrases/combat_narratives/death_narratives/style_rules）由外部超级库提供或在后续版本补充（见22.2.3）。
- **[EXT-资产] 新增叙事类型**：在 NarrativeType 枚举（22.2.1 九种类型）基础上新增类型——需三步：①枚举增加新值；②在 generate_narrative 分发流程（22.2.2）注册对应生成方法；③提供对应模板数据。已注册的 8 个分发键（generate_combat_desc 等）可作为新类型的参考实现。
- **[EXT-资产] 新增任务叙事**：quest_narratives 支持新增任务条目（giver/accept/progress/complete/target/reward 六要素），新任务自动接入任务事件触发（22.1.1）与三阶段叙事联动（22.3），并同步接入 @M06 任务与剧情系统。
- **[EXT-接口] 占位接口落地**：22.1.2 预留的 random_encounter 占位接口可替换为正式实现（roll_encounter + generate_encounter 组合），并可通过 EXTERNAL_DATA（@M21）注册为外部调用键供其他模块复用。
- **[EXT-接口] 叙事生成钩子**：generate_narrative 主接口分发流程（22.2.2）支持在生成前/后插入自定义钩子（如前置条件检查、后处理润色），钩子可读取 NarrativeContext 六要素（player/world/type/parameters/style/cached_fragments）并修改输出文本，实现风格定制与内容过滤。
