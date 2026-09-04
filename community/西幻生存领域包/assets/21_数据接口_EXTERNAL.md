### M21.1 数据接口总览（EXTERNAL_DATA）
**数据源**：`/tmp/extract_test.txt` 行1086（超级库加载说明）、行1371-1410（load_external_data定义）、行2072-7909（17个register系统注册点）、行1443-1450（核心伪代码集成说明）
**依赖**：全部模块（M01-M20）
**状态**：✅ 已填充 v1.0
#### 21.1.1 统一调用接口 EXTERNAL_DATA
- **设计原则**：所有可变数据（祝福/NPC/地点/敌人/物品/技能等）均通过外部超级库加载至全局字典 `EXTERNAL_DATA`，处理函数仅调用库中的接口，不直接持有数据（行1086）。
- **全局赋值**：`EXTERNAL_DATA = load_external_data()`（行1409），在核心伪代码启动时一次性加载。
- **调用方式**：`EXTERNAL_DATA["键名"](参数列表)`，返回处理结果（描述文本/状态修改/成功标志等）。
- **基础数据键**（load_external_data 返回字典，行1374-1377）：
| 键名 | 含义 |
|------|------|
| locations | 地点数据 |
| npcs | NPC模板 |
| enemies | 敌人数据 |
| items | 物品数据 |
| ability_pool | 能力池 |
| blessing_pool | 祝福池 |
- **占位lambda接口**（行1379起，实际功能由各register系统注册覆盖）：random_encounter 随机遭遇 / generate_dialogue 对话生成 / combat_system 战斗系统 / use_item_effect 物品效果 / skill_system 技能系统 / get_visible_objects 可见对象 / inspect_target 检查目标 / universal_resolver 通用解析。
#### 21.1.2 load_external_data 加载机制
- **函数定义**：行1371 `def load_external_data()`，占位实现（实际从文件/数据库读取），返回基础字典。
- **加载链**：基础字典初始化 → 依次调用17个register_xxx函数注入各系统功能键 → 返回完整 EXTERNAL_DATA 供核心伪代码使用。
- **可扩展性**：字典可随时添加更多接口（源码注释"可以添加更多接口"），新系统只需新增register函数并在load_external_data()末尾追加调用。
#### 21.1.3 17个系统注册点
| # | 注册函数 | 位置 | 注册核心键 | 所属系统 |
|---|----------|------|-----------|----------|
| 1 | register_npc_system | 行2072 | npc_manager / update_npcs / get_npcs_at_location | NPC交互 |
| 2 | register_state_and_difficulty | 行2400 | handle_state_command / handle_difficulty_command | 状态与难度 |
| 3 | register_blessing_system | 行2640 | blessing_manager / add_blessing / apply_blessing_effects | 祝福 |
| 4 | register_magic_system | 行3038 | magic_system / magic_cast / magic_parse_word | 魔法 |
| 5 | register_combat_system | 行3369 | combat_manager / combat_round / start_combat | 战斗 |
| 6 | register_skill_fusion_system | 行3655 | skill_fusion_manager / fuse_skills / decompose_skill | 技能融合 |
| 7 | register_trade_system | 行4124 | trade_manager / buy_commodity / update_markets | 跑商贸易 |
| 8 | register_resource_system | 行4469 | resource_mapper / refresh_resource / create_resource_manager | 资源 |
| 9 | register_map_system | 行4772 | map_manager / move_player / get_location | 地图 |
| 10 | register_item_refresh_system | 行5108 | item_refresh_manager / refresh_all / generate_random_item | 物品刷新 |
| 11 | register_element_system | 行5304 | element_manager / combine_elements / check_element_reaction | 元素组合 |
| 12 | register_skill_system | 行5789 | skill_manager / update_skill_cooldowns | 技能 |
| 13 | register_monster_system | 行6161 | monster_manager / spawn_monster / scale_monster | 怪物 |
| 14 | register_infinite_engine | 行6560 | infinite_engine / parse_custom_action | 无限可能引擎 |
| 15 | register_narrative_system | 行6888 | narrative_manager / set_narrative_style / generate_narrative | 叙事 |
| 16 | register_relationship_system | 行7380 | relation_manager / change_favor / get_faction_relation | 关系 |
| 17 | register_sandbox_system | 行7909 | sandbox_manager / create_settlement / build | 沙盒经营 |
#### 21.1.4 核心伪代码集成说明
- **调用链**（行1443-1450）：核心循环在每日推进/命令处理/战斗结算处调用各系统：trade_system 跑商 / npc_death_check NPC随机死亡 / magic_system 魔法系统 / blessing_synthesis 祝福合成 / base_system 基地管理 / element_combo 元素组合 / season_system 季节效果（行1677、1700）。
- **集成方式**：在 load_external_data() 中调用全部register函数；命令处理函数中通过 `EXTERNAL_DATA["xxx"](params)` 调用；无法识别的行动交给 `EXTERNAL_DATA["parse_custom_action"]`（行1645，详见20.2）。
- **返回值约定**：各接口统一返回 (success, message/result) 或状态字典，核心伪代码直接使用。
### M21.2 数据键映射
> **数据源**：行1371-1450（load_external_data与核心调用链）、行2072-7909（17个注册函数）、行8220-8233（战术系统注册）、行8773-8780（自由度系统注册）、行16223/17725/20057/22042（生成器与进阶NPC注册）、附录超级库数据A1-A20（行341-421）
> **依赖**：全部模块（@M01-M20）
> **状态**：✅ 已填充 v1.0

#### 21.2.1 数据键体系总览
- **注册键（166个）**：全部 register_xxx 函数通过 `external_data["键名"] = 实现` 注入 EXTERNAL_DATA 的功能键，覆盖 17+2 个系统注册点及 4 个生成器/进阶注册点。
- **读取键（110个）**：核心伪代码通过 `EXTERNAL_DATA["键名"](参数)` 实际调用的键；二者差集（56个）为系统内部互相调用的管理对象与辅助接口。
- **键类型**：①数据键——基础字典6个（locations/npcs/enemies/items/ability_pool/blessing_pool，行1379-1384），由附录A1-A20超级库数据填充；②函数键——管理对象（npc_manager/combat_manager 等）与功能函数（add_blessing/start_combat 等）166个；③占位接口——核心伪代码预留 lambda 8个（random_encounter/generate_dialogue/combat_system/use_item_effect/skill_system/get_visible_objects/inspect_target/universal_resolver，行1388-1400）及设计意图4个（base_system/death_system/gacha_system/element_combo，行1448-1450注释）。

#### 21.2.2 键名→模块映射表（一：#1-#10系统）

| 系统 | 注册位置 | 核心键名（节选） | 功能说明 |
|------|----------|------------------|----------|
| NPC交互 | register_npc_system 行2072 | npc_manager / get_npc / get_npcs_at_location / update_npcs / npc_death_check / generate_dialogue / change_favor | NPC查询、每日更新、死亡判定、对话生成、好感变更（数据源A3/A8） |
| 状态与难度 | register_state_and_difficulty 行2400 | commands / handle_state_command / handle_difficulty_command | 状态查看与难度调整命令路由 |
| 祝福 | register_blessing_system 行2640 | blessing_manager / add_blessing / apply_blessing_effects / remove_blessing / synthesize_blessings / fuse_blessings / get_blessings_by_cause | 祝福增删、效果应用、合成与融合（数据源A1/A2） |
| 魔法 | register_magic_system 行3038 | magic_system / magic_cast / magic_parse_word / magic_combine_elements / magic_craft / magic_cultivate / get_element_mastery / modify_element_mastery | 咒语解析、施法、元素组合、制作、修炼（数据源A15） |
| 战斗 | register_combat_system 行3369 | combat_manager / combat_round / start_combat / get_combat_rewards / apply_job_bonus | 战斗回合、开战、奖励结算（数据源A4） |
| 技能融合 | register_skill_fusion_system 行3655 | skill_fusion_manager / fuse_skills / fuse_by_recipe / fuse_dynamic / decompose_skill / upgrade_skill | 技能融合配方/动态融合、分解、升级（数据源A19） |
| 跑商贸易 | register_trade_system 行4124 | trade_manager / buy_commodity / sell_commodity / daily_trade_update / get_market_price / invest_caravan / invest_future / invest_shop / take_loan / repay_loan / smuggle / update_markets | 买卖、投资、贷款、走私、市场刷新（数据源A16） |
| 资源 | register_resource_system 行4469 | resource_mapper / create_resource_manager / apply_resource_special / get_resource_damage_bonus / get_resource_failure_chance / update_resources_from_attributes / refresh_resource | 资源映射、特殊规则、伤害/失败概率、属性联动 |
| 地图 | register_map_system 行4772 | map_manager / move_player / get_location / get_location_description / get_connected_locations / find_path / get_travel_time / roll_encounter / update_locations | 移动、地点查询、寻路、旅行时间、遭遇掷骰（数据源A6） |
| 物品刷新 | register_item_refresh_system 行5108 | item_refresh_manager / refresh_all / refresh_shop / get_chest_loot / get_enemy_loot / get_items_unlocked | 物品全刷新、商店刷新、宝箱/敌人掉落、解锁物品（数据源A5） |

#### 21.2.3 键名→模块映射表（二：#11-#19系统与生成器）

| 系统 | 注册位置 | 核心键名（节选） | 功能说明 |
|------|----------|------------------|----------|
| 元素组合 | register_element_system 行5304 | element_manager / combine_elements / check_element_reaction / get_element_effect / get_element_info / binary_element_combinations / ternary_element_combinations / element_counter_system / element_quantity_system / dynamic_combination_generator | 元素二元/三元组合、反应判定、相克与数量系统（数据源A18） |
| 技能 | register_skill_system 行5789 | skill_manager / learn_skill / reset_daily_skills / update_skill_cooldowns / get_available_combos / get_skill_axis_weights / get_skill_build_tags / calculate_player_axis / execute_combo / inherit_skill / upgrade_skill | 学习、冷却、轴权重、连招执行、技能继承（数据源A7） |
| 怪物 | register_monster_system 行6161 | monster_manager / spawn_monster / spawn_group / evolve_monster / scale_monster / update_monster_ai / generate_encounter / get_monster_loot | 生成、进化、缩放、AI更新、遭遇与掉落（数据源A4） |
| 无限可能引擎 | register_infinite_engine 行6560 | infinite_engine / parse_custom_action | 规则库驱动行动解析（数据源：intent_patterns 等9类规则库） |
| 叙事 | register_narrative_system 行6888 | narrative_manager / generate_narrative / set_narrative_style / generate_combat_desc / generate_death_desc / generate_event_desc / generate_fragment / generate_location_desc / generate_npc_dialogue | 战斗/死亡/事件/碎片/地点/NPC对话描述生成 |
| 关系 | register_relationship_system 行7380 | relation_manager / change_favor / get_faction_relation / get_npc_relation / get_npc_to_player / modify_npc_relation / modify_player_to_npc / modify_npc_to_player / daily_relation_update / create_intelligence / get_player_intel / share_intelligence / perform_spy / join_gang / modify_faction_strength / trigger_gang_conflict / assign_job | 好感、势力关系、情报、间谍、帮派（数据源A9/A10） |
| 沙盒经营 | register_sandbox_system 行7909 | sandbox_manager / create_settlement / daily_settlement_update / build / demolish / recruit / get_settlement_summary / start_production / upgrade / check_build_synergy | 据点建设、居民招募、生产升级（数据源A20） |
| 战术 | register_tactical_system 行8236 | tactical_manager / get_terrain_modifier / select_body_part / apply_body_part_effect / can_break_defense / update_combo / get_combo_bonus / apply_stance / check_destructible / damage_destructible / check_element_reaction / apply_element_reaction / calculate_morale / morale_effect_on_combat | 地形修正、部位打击、破防、连招、架势、士气（数据源A19） |
| 自由度 | register_freedom_system 行8783 | freedom_manager / init_chaos_state / resolve_chaos_action / change_lifestyle / lifestyle_daily_update / check_physical_limits / generate_chaos_quest / commit_crime | 混沌状态、生活方式、身体极限、犯罪通缉、混沌任务 |
| 物品生成器 | register_item_generator 行16223 | item_generator / generate_random_item | 随机物品生成（数据源A5） |
| 能力生成器 | register_ability_generator 行17725 | ability_generator / generate_random_ability / mutate_ability | 随机能力生成与突变（数据源A7） |
| 动态祝福 | register_dynamic_blessing_system 行20057 | dynamic_blessing_generator / add_blessing | 动态祝福生成（数据源A1） |
| 进阶NPC | register_npc_system 行22042 | npc_manager / get_npc / get_npcs_at_location / update_npcs / npc_death_check / generate_dialogue / change_favor | 进阶版NPC系统（与#1键名复用覆盖，行22042） |

#### 21.2.4 调用方式与约定
- **统一调用**：`EXTERNAL_DATA["键名"](参数1, 参数2, ...)`；数据字典键直接读取 `EXTERNAL_DATA["locations"]`。
- **参数约定**：函数键首参通常为 player_state（玩家状态）或 context（行动上下文）；管理对象键（xxx_manager）返回对象实例，供链式调用。
- **返回值约定**：判定类返回 `(success: bool, message: str)` 或布尔值；生成类返回结果对象/文本；状态类返回更新后的状态字典。
- **调用示例**：
  - `EXTERNAL_DATA["start_combat"](player_state, enemy_id, context)`
  - `EXTERNAL_DATA["magic_cast"](player_state, spell_name, target)`
  - `EXTERNAL_DATA["npc_manager"].get_npc(npc_id)`
- **扩展方式**：新增数据键在 load_external_data() 中追加 `external_data["新键"] = 实现`，或新增 register_xxx 函数并在加载链中调用（见21.1.2）。

### M21.3 模块联动与扩展点
> **数据源**：行1086-1450（核心伪代码集成）、行2072-22042（全部register注册点）、附录A1-A20（行341-421）
> **依赖**：全部模块（@M01-M20）
> **状态**：✅ 已填充 v1.0

#### 21.3.1 模块联动总表（M01-M10）

| 模块 | 联动键/接口 | 联动说明 |
|------|--------------|----------|
| M01 基础属性与角色创建 | ability_generator / generate_random_ability / PlayerState | 角色创建时能力池数据由A7能力池提供，能力生成器注入初始随机能力 |
| M02 种族与天赋 | apply_job_bonus / give_birth / 种族模板（A12） | 职业/种族加成由外部超级库数据驱动 |
| M03 技能系统 | skill_manager / learn_skill / get_skill_axis_weights / get_skill_build_tags / reset_daily_skills | 技能学习、轴权重计算、每日技能重置 |
| M04 战斗系统 | combat_manager / start_combat / combat_round / get_combat_rewards / tactical_manager | 战斗开战/回合/奖励结算，战术细节由战术系统补充 |
| M05 装备与物品 | item_generator / generate_random_item / get_chest_loot / get_enemy_loot / item_refresh_manager / refresh_shop | 随机物品生成、宝箱/敌人掉落、商店刷新（数据源A5） |
| M06 任务与剧情 | generate_chaos_quest / 任务库（A10） | 混沌任务生成，剧情分支由叙事系统文本化 |
| M07 世界地图与地点 | map_manager / move_player / get_location / get_location_description / update_locations / find_path | 移动、地点查询描述、寻路、地点更新（数据源A6） |
| M08 天气季节与环境 | season_system / apply_season_to_location / get_current_season_effects / trigger_season_event | 季节系统：季节效果应用于地点并触发季节事件 |
| M09 经济与贸易 | trade_manager / buy_commodity / sell_commodity / get_market_price / invest_caravan / invest_shop / update_markets | 买卖、投资、市场刷新（数据源A16跑商数据） |
| M10 死亡与重生 | npc_death_check / death_system / give_birth / 继承系统（A17） | NPC随机死亡判定、死亡后果、后代继承 |

#### 21.3.2 模块联动总表（M11-M20）

| 模块 | 联动键/接口 | 联动说明 |
|------|--------------|----------|
| M11 魔法系统·文字即咒语 | magic_system / magic_cast / magic_parse_word / magic_combine_elements / magic_craft / magic_cultivate | 文字咒语解析、施法、元素组合、制作修炼（数据源A15魔法五层理论） |
| M12 对话与NPC交互 | generate_dialogue / generate_npc_dialogue / npc_manager / get_npc | NPC对话模板生成（数据源A8对话库） |
| M13 NPC交互系统 | npc_manager / get_npc / get_npcs_at_location / update_npcs / change_favor | NPC全生命周期管理（数据源A3） |
| M14 阵营与声望 | relation_manager / get_faction_relation / modify_faction_strength / 势力关系（A9） | 阵营声望查询与修改，势力强弱动态调整 |
| M15 帮派与势力 | join_gang / trigger_gang_conflict / assign_job / 13帮派系统 | 加入帮派、帮派冲突触发、职务分配 |
| M16 建筑与城镇 | sandbox_manager / create_settlement / build / demolish / upgrade / recruit / get_settlement_summary | 据点创建、建设拆除升级、居民招募（数据源A20） |
| M17 生产与制造 | start_production / magic_craft / 生产配方 / check_build_synergy | 生产启动、建筑协同加成 |
| M18 混沌与随机事件 | init_chaos_state / resolve_chaos_action / generate_chaos_quest / 随机事件池（A11） | 混沌状态初始化、行动解析、混沌任务生成 |
| M19 遗传与后代 | give_birth / inherit_skill / mutate_ability / 遗传特质（遗传系统） | 后代出生、技能继承、能力突变 |
| M20 世界知识库 | world_knowledge / narrative_manager / generate_narrative / 世界知识数据 | 知识库数据驱动叙事生成与描述文本 |

#### 21.3.3 扩展点
- **[EXT-资产] 新增数据键**：在 load_external_data() 中追加 `external_data["新键"] = 实现`，或新增 register_xxx 函数并在加载链中调用（见21.1.2/21.2.4）。
- **[EXT-资产] 新增接口方法**：在既有管理对象类中新增方法，并在其 register_with_core() 中注册为新键。
- **[EXT-资产] 新增超级库数据**：在附录A1-A20后追加新数据区块（如A21），供新键读取；数据区块与键名一一对应。
- **[EXT-规则] 无限规则库**：无限可能引擎规则库可无限扩展（intent_patterns/entity_patterns/world_knowledge/action_rules/difficulty_tables/result_templates/forbidden_actions/intent_attribute_map/intent_skill_map 共9类），每添加一条新规则即可支持新类型的行动（@M20 联动）。
- **[EXT-接口] 占位接口落地**：核心伪代码预留的8个lambda占位接口（random_encounter/generate_dialogue/combat_system/use_item_effect/skill_system/get_visible_objects/inspect_target/universal_resolver）及4个设计意图键（base_system/death_system/gacha_system/element_combo）可逐步替换为正式实现。

