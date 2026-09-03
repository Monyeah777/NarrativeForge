### M23.组合与扩展规则
- 职责：定义系统组合玩法、跨模块联动与扩展协议
- 数据源：element_reaction_rules（行9699/36226，6种元素反应）、skill_combos（行27369，7个组合技）、skill_builds（行27287，10个流派）、skill_axis_weights（三轴权重）、连击系统（行3093）等跨系统数据
- 依赖：全部模块
- 扩展点：[EXT-规则] 新增组合规则 / 扩展协议
- 状态：✅ 已填充 v1.0
---

#### 23.1 组合玩法体系

组合玩法体系是 P3 层的收束性设计：将 @M04 战斗、@M05 技能中的独立能力通过"元素反应 + 组合技 + 流派协同 + 连击奖励"四层机制耦合为复合玩法。全部组合规则均为纯数据驱动，由外部超级库提供 JSON 数据，运行时由战斗系统（TacticalManager，行8001）与技能系统（行5462 combo_defs 加载、行5700 get_skill_build_tags）统一加载与判定。

##### 23.1.1 元素反应规则

元素反应（element_reaction_rules）定义两两元素相遇时的复合效果，由战术系统在战斗中实时判定。数据源位于行9699（英文键版本）与行36226（中文键版本），两处内容一致；加载逻辑在行8018（external_data.get("element_reaction_rules")）。共 6 种反应规则：

| 组合元素 | 反应类型 | 伤害 | 范围/目标 | 附加效果 | 数据行号 |
|---|---|---|---|---|---|
| 火 + 油 | 爆炸 | 40 | 范围3 | 燃烧（持续3回合） | 行9700 |
| 水 + 电 | 连锁闪电 | 25 | 目标5 | 麻痹（持续1回合） | 行9709 |
| 冰 + 火 | 蒸汽 | 10 | 范围5 | 致盲（持续2回合） | 行9719 |
| 土 + 水 | 泥沼 | — | 地形沼泽 | 减速敌人（持续5回合） | 行9730 |
| 风 + 火 | 火焰风暴 | 30 | 范围4 | 燃烧（持续2回合） | 行9737 |
| 光 + 暗 | 虚空 | 60 | 单体 | 混沌伤害，无附加状态 | 行9745 |

触发流程（战术系统集成，行8200 register_tactical_system 第7步）：
1. 攻击命中后，战斗系统收集本次攻击携带的元素标签（如火焰攻击命中油污区域）；
2. 调用 check_element_reaction（注册键）查询 element_reaction_rules 是否命中组合；
3. 命中则调用 apply_element_reaction 执行效果——结算伤害/范围/目标数与附加状态；
4. 反应结果写入战斗描述，供 @M04 战斗叙事（generate_combat_desc）生成文本。
##### 23.1.2 组合技定义

组合技（skill_combos）由两个及以上基础技能组合触发，定义于行27369（JSON 数据），加载逻辑在行5462（combo_defs）。共 7 个组合技：

| 组合技 | id | 所需技能 | 效果 | 冷却 |
|---|---|---|---|---|
| 火龙卷 | combo_fire_wind | fireball + wind_blade | 伤害5d10+20，范围3，燃烧5回合 | 10 |
| 冰雷震 | combo_ice_lightning | ice_bolt + lightning_bolt | 伤害4d12+15，麻痹2+冻结2回合 | 12 |
| 泥沼术 | combo_earth_water | stone_skin + heal | 减速0.6，每秒治疗10，范围4，持续8回合 | 15 |
| 混沌爆发 | combo_light_dark | holy_light + shadow_step | 伤害6d15真实伤害，范围5 | 20 |
| 致命一击 | combo_warrior_thief | execute + backstab | 处决阈值0.3，即死概率50% | 30 |
| 神圣新星 | combo_mage_cleric | fireball + heal | 伤害4d8+10 + 治疗3d8+10，范围4 | 8 |
| 剑雨箭阵 | combo_bow_sword | multishot + whirlwind | 伤害5d8+15，范围5，目标全体敌人 | 10 |

组合技接口（技能系统，行5735-5750）：
- **get_available_combos**（行5735）：遍历 combo_defs，检查玩家与队友技能是否满足 requires 条件，返回可用组合技列表——注册键行5783（external_data["get_available_combos"]）；
- **execute_combo**（行5750）：按 id 查找组合技定义并执行，返回效果描述文本；
- **战斗触发**（行5812）：战斗中通过 EXTERNAL_DATA["get_available_combos"](state, ally_skills) 检测可用组合，玩家可选择执行。

##### 23.1.3 流派协同

流派（skill_builds）定义于行27287，共 10 个流派，每个流派含核心技能（core_skills）、辅助技能（supporting_skills）、协同效果（synergy_effect）与三轴权重（axis_weights）：

| 流派 | 核心技能 | 辅助技能 | 协同效果 | 三轴权重 S/O/V |
|---|---|---|---|---|
| 燃烧流 | fireball/burning_hands/fire_mastery | ignite/flame_shield/fire_breath | 每层燃烧使火焰伤害+2% | 2/8/3 |
| 冰冻流 | ice_bolt/frost_armor/ice_arrow | freezing_nova/ice_shield/cold_snap | 冻结时暴击率+15% | 4/5/4 |
| 毒爆流 | poison_dagger/venom_strike/toxic_cloud | corrosive_spray/plague/antidote | 毒爆伤害=目标当前生命5% | 3/7/3 |
| 召唤流 | summon_skeleton/summon_wolf/summon_elemental | summon_reinforcement/master_summoner/sacrifice | 每召唤物全属性+1% | 5/6/2 |
| 控制流 | stun_blow/entangling_roots/paralyze | slow/silence/fear | 控制持续时间+20% | 6/3/4 |
| 爆发流 | execute/critical_strike/power_infusion | adrenaline/berserker_soul/final_blow | 爆发技能暴击伤害+50% | 2/9/2 |
| 生存流 | stone_skin/shield_bash/taunt | heal/revive/defensive_stance | 受伤获得护盾吸收10%最大生命 | 9/2/2 |
| 速度流 | haste/shadow_step/quick_strike | dash/wind_walk/blink | 攻速+10%，移速+10% | 2/4/7 |
| 反伤流 | thorns_aura/reflect/iron_skin | spiked_armor/retribution/counter_attack | 反弹伤害30%转为治疗 | 7/3/3 |
| 吸血流 | life_steal/vampiric_touch/blood_drain | bloodlust/siphon_life/blood_shield | 吸血溢出20%转为护盾 | 6/5/2 |

流派协同判定：
- **get_skill_build_tags**（行5700）：获取技能所属流派标签；
- **check_build_synergy**（行5705）：检查玩家技能组合是否满足流派协同要求，返回流派名与协同效果；
- **三轴权重**（skill_axis_weights）：每技能含 S战术/O技巧/V活力 三轴权重（如 fireball S1/O8/V2、heal S9/O0/V1、haste S1/O2/V9），用于匹配流派倾向与战术推荐。

#### 23.2 跨模块联动

组合与扩展规则层与全部模块联动，是系统的收束接口。主要联动关系如下：

| 联动模块 | 联动内容 | 数据/接口 |
|---|---|---|
| @M01 角色 | 流派匹配角色天赋轴（S/O/V 三轴），推荐适配流派 | skill_axis_weights + check_build_synergy |
| @M02 种族 | 种族天赋元素加成影响元素反应伤害结算 | element_reaction_rules + 种族元素抗性 |
| @M03 技能 | 组合技由基础技能组合触发，流派定义核心/辅助技能 | skill_combos + skill_builds |
| @M04 战斗 | 战术系统 9 类外部数据实时判定元素反应/地形/部位/士气 | TacticalManager（行8001，14注册键） |
| @M05 装备 | 装备附加元素标签触发元素反应，武器类型影响组合技可用性 | 装备元素属性 + combo requires |
| @M06 任务 | 任务奖励流派技能书/组合技解锁，任务 NPC 教授组合技 | quest_narratives + skill_combos |
| @M07 地图 | 地形修正（terrain_modifiers）影响战斗，区域元素环境触发反应 | terrain_modifiers + destructible_objects |
| @M10 死亡 | 死亡叙事可触发流派传承，装备流派核心技能传承 | death_narratives + skill_builds |
| @M13 NPC | 队友技能参与 get_available_combos 判定，NPC 流派协同 | get_available_combos(state, ally_skills) |
| @M18 混沌 | 混沌任务奖励随机组合技/流派卷轴 | chaos_quests + skill_combos |
| @M19 遗传 | 遗传技能轴影响后代流派倾向，流派三轴权重参与遗传计算 | skill_axis_weights + 遗传系统 |
| @M20 知识库 | 元素反应 lore 写入世界知识库，供叙事引用 | world_knowledge + element_reaction_rules |
| @M21 数据接口 | 全部组合数据经 EXTERNAL_DATA 统一注册（14+3 注册键） | external_data 注册表（行5783/8200） |
| @M22 事件叙事 | 元素反应/组合技效果生成战斗叙事，事件可触发组合教学 | generate_combat_desc + 事件池 |

跨模块调用链（以"玩家释放火球+风刃触发火龙卷"为例）：
1. @M04 战斗系统检测玩家连续释放 fireball + wind_blade（连击系统 combo_count 递增，行3093）；
2. 调用 EXTERNAL_DATA["get_available_combos"]（@M21）检查 combo_fire_wind 可用（行5812）；
3. execute_combo 执行组合技（行5750），结算伤害 5d10+20 与燃烧状态；
4. 若命中油污区域，@M04 再判定 element_reaction_rules 火+油爆炸（行9699）；
5. 战斗结果经 generate_combat_desc（@M22）生成叙事文本，写入 @M20 世界知识库。

#### 23.3 扩展协议

组合与扩展层支持四类扩展协议，全部为纯数据驱动或注册表挂载：

1. **数据扩展协议**：向 element_reaction_rules / skill_combos / skill_builds / skill_axis_weights JSON 追加条目即可新增组合规则，无需修改代码（@M21 统一加载）；
2. **注册表扩展协议**：战术系统 14 个注册键（tactical_manager / get_terrain_modifier / select_body_part / apply_body_part_effect / can_break_defense / update_combo / get_combo_bonus / apply_stance / check_destructible / damage_destructible / check_element_reaction / apply_element_reaction / calculate_morale / morale_effect_on_combat）可被外部模块覆盖或新增；
3. **组合技注册协议**：新组合技需在 skill_combos 定义 requires 技能组合与效果字段，get_available_combos 自动识别（遍历 combo_defs）；
4. **流派注册协议**：新流派需定义 core_skills / supporting_skills / synergy_effect / axis_weights 四要素，check_build_synergy 自动匹配玩家技能组合。

#### 23.4 扩展点

- **[EXT-规则] 新增元素反应**：element_reaction_rules 支持追加新元素组合（如"水+冰→冻结""暗+火→地狱火"），每条需定义 elements 组合与 effect（type/damage/range/element/status/duration），战术系统 check_element_reaction + apply_element_reaction 自动识别，无需修改代码。
- **[EXT-规则] 新增组合技**：skill_combos 支持追加新组合技，需定义 id/name/requires（技能组合）/description/effect/cooldown 六要素，get_available_combos 遍历 combo_defs 自动识别（@M21 注册键 external_data["get_available_combos"]）。
- **[EXT-规则] 新增流派**：skill_builds 支持追加新流派，需定义 core_skills（3核心）/supporting_skills（3辅助）/synergy_effect/axis_weights 四要素，check_build_synergy 自动匹配玩家技能组合判定协同生效。
- **[EXT-资产] 新增技能权重条目**：skill_axis_weights 为纯数据表（30+技能 S/O/V 三轴权重），追加新技能条目即可参与流派匹配与战术推荐，无需修改判定逻辑。
- **[EXT-资产] 新增战术数据**：战术系统 9 类外部数据（terrain_modifiers/body_part_chances/body_part_effects/combo_rewards/stance_modifiers/break_defense_rules/destructible_objects/element_reaction_rules/morale_effects）全部为 JSON 数据驱动，由外部超级库提供，追加条目即可扩展战术判定维度。
- **[EXT-资产] 新增连击奖励**：连击系统（行3093）的 combo_rewards 支持追加连击数对应奖励（如 3 连击伤害+10%、5 连击暴击+20%），纯数据驱动。
- **[EXT-接口] 注册表键覆盖**：战术系统 14 个注册键与技能系统 3 个注册键（get_available_combos/execute_combo/check_build_synergy）均可被外部模块覆盖实现，实现自定义组合判定逻辑（如跨职业技能组合）。
- **[EXT-接口] 组合技钩子**：execute_combo 支持在组合技执行前/后插入自定义钩子（前置条件检查、效果增强、联动事件触发），钩子可读取组合技定义与战斗上下文，实现扩展玩法（如组合技触发 @M22 事件）。

---

