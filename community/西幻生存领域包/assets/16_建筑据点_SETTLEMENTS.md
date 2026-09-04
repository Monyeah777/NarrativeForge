### M16.1 建筑模板总表与数据模型
**数据源**：building_templates（`/tmp/extract_test.txt` 行33247-33788，32个建筑模板）、BuildingType枚举（行7425）、Building类（行7466-7527）、ResourceStock类（行7528-7537）。
**依赖**：@M07（居民NPC日程与工作分配）、@M09（资源与贸易联动）、@M15（帮派地盘与建筑归属）。
**状态**：✅ 已填充 v1.0
**建筑类型（BuildingType枚举8类）**：
| 类型 | 键 | 说明 | 模板数 |
|------|----|------|--------|
| 资源生产 | RESOURCE | 农场、矿场等基础资源产出 | 8 |
| 加工 | PROCESSING | 工坊、磨坊等原料加工 | 5 |
| 仓库 | STORAGE | 仓库、粮仓等物资存储 | 2 |
| 住宅 | RESIDENTIAL | 民居、公寓等居民住所 | 2 |
| 防御 | DEFENSE | 哨塔、城墙等防御工事 | 3 |
| 商业 | COMMERCIAL | 市场、商店等商业设施 | 4 |
| 文化 | CULTURAL | 教堂、学院等文化设施 | 3 |
| 特殊 | SPECIAL | 魔法塔、炼金室等特殊建筑 | 4 |
（另有基础设施infrastructure1个：well水井）**32个建筑模板总表**：
| 建筑ID | 名称 | 类型 | 建造成本 | 最大工人 | 基础产出 | HP |
|--------|------|------|----------|----------|----------|-----|
| farm | 农场 | resource | wood50/stone20/gold100 | 3 | food20 | 100 |
| farm_lv2 | 高级农场 | resource | wood80/stone40/iron10/gold200 | 5 | food40 | 150 |
| wheat_field | 麦田 | resource | wood30/gold50 | 2 | food15 | 80 |
| fishing_hut | 渔屋 | resource | wood40/gold60 | 2 | food18 | 80 |
| mine | 矿场 | resource | wood60/stone30 | 3 | - | - |
| stone_quarry | 采石场 | resource | - | - | - | - |
| lumber_mill | 伐木场 | resource | - | - | - | - |
| herb_garden | 草药园 | resource | - | - | - | - |
| workshop | 工坊 | processing | - | - | - | - |
| blacksmith | 铁匠铺 | processing | - | - | - | - |
| mill | 磨坊 | processing | - | - | - | - |
| sawmill | 锯木厂 | processing | - | - | - | - |
| bakery | 面包房 | processing | - | - | - | - |
| warehouse | 仓库 | storage | - | - | - | - |
| granary | 粮仓 | storage | - | - | - | - |
| house | 民居 | residential | - | - | - | - |
| apartment | 公寓 | residential | - | - | - | - |
| guard_tower | 哨塔 | defense | wood80/stone100/iron30/gold250 | - | - | - |
| wall | 城墙 | defense | - | - | - | - |
| barracks | 兵营 | defense | - | - | - | - |
| market | 市场 | commercial | wood100/stone50/gold300 | - | - | - |
| shop | 商店 | commercial | - | - | - | - |
| tavern | 酒馆 | commercial | - | - | - | - |
| inn | 旅店 | commercial | - | - | - | - |
| temple | 教堂 | cultural | - | - | - | - |
| library | 图书馆 | cultural | - | - | - | - |
| academy | 学院 | cultural | - | - | - | - |
| magic_tower | 魔法塔 | special | - | - | - | - |
| alchemy_lab | 炼金室 | special | - | - | - | - |
| workshop_special | 特殊工坊 | special | - | - | - | - |
| stable | 马厩 | special | - | - | - | - |
| well | 水井 | infrastructure | - | - | - | - |
**Building数据模型（13字段）**：id（实例ID）、template（模板引用）、name、type（BuildingType）、level（等级）、hp/max_hp、construction_progress（建造进度，建成100/建设中0）、input_resources（输入库存）、output_resources（输出库存）、workers（工作居民ID列表）、production_queue（生产队列）、upgrade_progress（升级进度）。
**ResourceStock数据模型（4字段）**：amount（存量）、capacity（容量，默认1000可由仓库提升）、daily_production（日产量）、daily_consumption（日消耗）。
### M16.2 建筑类型详解
**资源生产类（RESOURCE）**：农场farm→farm_lv2升级链（wood80/stone40/iron10/gold200，产出food40，max_workers5）；麦田wheat_field含季节修正（夏季1.2/冬季0.6）；渔屋fishing_hut需临水（requires_water:true）。
**加工类（PROCESSING）**：工坊workshop、铁匠铺blacksmith、磨坊mill、锯木厂sawmill、面包房bakery——将原料加工为成品，需匹配ProductionRecipe配方（见M16.5）。
**存储类（STORAGE）**：仓库warehouse、粮仓granary——提升ResourceStock容量上限（默认容量1000）。
**住宅类（RESIDENTIAL）**：民居house、公寓apartment——提供住房容量（_calculate_housing_capacity计算），容纳居民home_building。
**防御类（DEFENSE）**：哨塔guard_tower（wood80/stone100/iron30/gold250）、城墙wall、兵营barracks——提升据点安全度security（默认50）。
**商业类（COMMERCIAL）**：市场market（wood100/stone50/gold300）、商店shop、酒馆tavern、旅店inn——贸易与税收加成（@M09贸易联动，酒馆tavern为居民喜好最高建筑权重12）。
**文化类（CULTURAL）**：教堂temple、图书馆library、学院academy——居民士气与技能加成（学者scholar偏好）。
**特殊类（SPECIAL）**：魔法塔magic_tower、炼金室alchemy_lab、特殊工坊workshop_special、马厩stable——特殊功能与专属配方。
**建筑升级链**：farm→farm_lv2为唯一已配置升级链（upgrade_to字段），upgrade()消耗资源并进入upgrade_progress。
### M16.3 居民模板与生成机制
**数据源**：resident_templates（行33789-34190，27个居民模板）、ResidentJob枚举（行7440）、Resident类（行7540-7550）、random_resident_generation（行35525-35859）。
**居民模板总表（27个，按种族）**：人类11（农夫艾德/农妇玛莎/矿工/商人/守卫等）、精灵4（伐木工艾瑞尔等）、矮人4（矿工格朗/赫尔嘉等）、龙裔2、猫人2、兽人2、魅魔1、美人鱼1。
**Resident模板字段（11项）**：name、race（种族）、preferred_job（偏好职业）、skills（技能字典）、morale_base（基础士气）、traits（性格特质1-3个）、likes（喜爱建筑）、dislikes（厌恶建筑）、specialization（专精方向）。
**ResidentJob枚举（8类）**：FARMER农民/MINER矿工/LUMBERJACK伐木工/CRAFTSMAN工匠/GUARD守卫/MERCHANT商人/SCHOLAR学者/UNEMPLOYED失业（resident_templates中另有fisher渔夫/alchemist炼金师/cook厨师偏好）。
**Resident数据模型（9字段）**：id、name、job（ResidentJob）、skill_level（技能等级）、morale（士气0-100，默认50）、health（生命100）、assigned_building（工作建筑）、home_building（住所建筑）、needs（需求food/rest/entertainment）、last_updated。
**随机居民生成机制（random_resident_generation）**：
- 种族权重：人类50/精灵15/矮人15/兽人10/猫人5/美人鱼3/龙裔1/魅魔1；
- 职业权重：farmer15/miner10/lumberjack10/craftsman12/guard12/merchant8/fisher8/cook6/scholar5/alchemist4/unemployed10；
- 种族职业倾向：各种族对各职业的倍率系数（如矮人miner1.8、精灵scholar1.5/lumberjack1.4、兽人guard1.7、魅魔merchant1.6）；
- 技能生成：按职业生成技能（基础+浮动+上限+概率），如farmer耕种{基础2/浮动2/上限5}、miner采矿{基础2/浮动3/上限6}；
- 特质池：26种特质加权抽取1-3个（勤劳10/勇敢8/友善7/耐心7/诚实6/忠诚6/叛徒1等）；
- 名字池：8种族×性别独立名字列表；
- 士气生成：均值50/标准差10/最小20/最大80；
- 喜好生成：喜爱建筑加权（酒馆tavern12/农场farm10/市场market9/矿场mine8等）。
### M16.4 城镇生成与据点管理
**数据源**：SandboxManager.create_settlement（`/tmp/extract_test.txt` 行7540-7610）、resource_definitions（行35423-35525，15种资源）、initial_settlement_buildings/initial_settlement_residents（行10421-10480）、build/upgrade/demolish/recruit_resident/assign_job（行7590-7700）。
**依赖**：@M07（居民日程与工作分配）、@M15（帮派地盘与建筑归属）。
**状态**：✅ 已填充 v1.0
**据点创建流程（create_settlement）**：
| 步骤 | 操作 | 说明 |
|------|------|------|
| 1 | 创建Settlement | 设置name、tax_rate默认0.05、security默认50 |
| 2 | 初始化资源 | 按resource_definitions创建15种ResourceStock，容量取base_capacity |
| 3 | 添加初始建筑 | 从initial_settlement_buildings批量_add_building |
| 4 | 添加初始居民 | 从initial_settlement_residents批量_add_resident |
| 5 | 绑定玩家状态 | player_state.settlement = settlement，记录established_day |
**资源定义表（resource_definitions，15种）**：food食物1000/wood木材1000/stone石材800/iron铁矿600/gold金币5000/tool工具300/weapon武器200/armor防具200/herb草药500/magic_essence魔法精华200/coal煤炭800/crystal晶体300/potion药水200/steel钢材500/water水源2000（容量=base_capacity）。
**初始据点配置**：初始建筑7个（house×2、farm、lumber_mill、well、workshop、warehouse）；初始居民6个（farmer_human_01、farmer_human_02、lumberjack_human_01、miner_dwarf_01、craftsman_human_01、unemployed_human_01）。
**建筑操作机制**：
- build建造：检查construction_cost→扣除资源→_add_building（construction_progress=0、hp=1建设中）→daily_tick每日+10进度，满100后hp恢复max_hp；
- upgrade升级：按building_upgrade_costs（类型×等级）检查扣除→upgrade_progress=0/level+1→每日+10进度满100完成；
- demolish拆除：按demolish_recovery_rate=0.5回收construction_cost资源→移除建筑；
- recruit_resident招募：检查_calculate_housing_capacity住房容量→消耗recruit_cost（gold100/food50）→随机生成或指定模板→morale取morale_base；
- assign_job分配工作：检查max_workers→解除原工作→building.workers追加→_building_type_to_job映射职业。
**升级成本表（building_upgrade_costs示例）**：farm级1-3：{wood30/stone10/gold80}→{wood60/stone20/gold150}→{wood100/stone40/gold300}；mine级1-3：{wood40/stone20/iron10/gold120}→{wood80/stone40/iron20/gold250}→{wood150/stone80/iron40/gold500}；workshop级1-3：{wood50/iron10/gold150}→{wood100/iron20/gold300}→{wood200/iron40/gold600}。
**扩展点[EXT-资产]**：新增建筑模板入building_templates、新增资源入resource_definitions、调整初始据点配置。
### M16.5 生产配方与资源流转
**数据源**：ProductionRecipe类（行7500）、production_recipes（行34191-34580，详细版25配方）、_update_production/_update_resources（行7758-7800）、start_production。
**依赖**：@M09（资源与贸易联动）、@M17（生产与制造）、@M07（居民工作分配）。
**状态**：✅ 已填充 v1.0
**ProductionRecipe数据模型（7字段）**：id、name、type（food/material/weapon/armor/consumable/tool）、building（生产建筑）、skill_required（技能门槛）、time（耗时）、inputs（投入）、outputs（产出）、description。
**生产配方总表（详细版25个）**：
| 配方 | 产物 | 类型 | 建筑 | 技能 | 耗时 | 投入→产出 |
|------|------|------|------|------|------|-----------|
| bread | 面包 | food | bakery | 1 | 1 | flour2+water1→bread5 |
| flour | 面粉 | material | mill | 1 | 1 | wheat2→flour3 |
| iron_ingot | 铁锭 | material | blacksmith | 1 | 2 | iron_ore3+coal1→iron_ingot2 |
| steel_ingot | 钢锭 | material | blacksmith | 3 | 3 | iron_ingot2+coal2→steel_ingot1 |
| mithril_ingot | 秘银锭 | material | blacksmith | 5 | 5 | mithril_ore2+magic_essence1→mithril_ingot1 |
| iron_sword | 铁剑 | weapon | blacksmith | 2 | 3 | iron_ingot2+wood1→iron_sword1 |
| steel_longsword | 钢制长剑 | weapon | blacksmith | 3 | 4 | steel_ingot2+leather1→steel_longsword1 |
| iron_dagger | 铁匕首 | weapon | blacksmith | 1 | 2 | iron_ingot1→iron_dagger1 |
| battle_axe | 战斧 | weapon | blacksmith | 4 | 4 | steel_ingot2+wood2→battle_axe1 |
| longbow | 长弓 | weapon | workshop | 3 | 3 | wood3+leather1→longbow1 |
| leather_armor | 皮甲 | armor | workshop | 2 | 2 | leather2→leather_armor1 |
| chainmail | 锁子甲 | armor | blacksmith | 4 | 4 | steel_ingot3→chainmail1 |
| plate_armor | 板甲 | armor | blacksmith | 5 | 5 | steel_ingot4→plate_armor1 |
| shield | 盾牌 | armor | workshop | 2 | 2 | iron_ingot1+wood2→shield1 |
| tower_shield | 塔盾 | armor | blacksmith | 4 | 4 | steel_ingot2+wood3→tower_shield1 |
| health_potion_small | 小型生命药水 | consumable | alchemy_lab | 1 | 1 | herb2+water1→potion1 |
| health_potion_medium | 中型生命药水 | consumable | alchemy_lab | 2 | 2 | herb4+potion1→potion2 |
| health_potion_large | 大型生命药水 | consumable | alchemy_lab | 3 | 3 | herb6+potion2→potion3 |
| mana_potion_small | 小型魔力药水 | consumable | alchemy_lab | 2 | 2 | magic_essence1+water2→potion1 |
| antidote | 解毒剂 | consumable | alchemy_lab | 2 | 1 | herb3+water1→antidote1 |
| torch | 火把 | tool | workshop | 1 | 1 | wood1+coal1→torch1 |
| rope | 绳索 | tool | workshop | 1 | 1 | fiber2→rope1 |
| tent | 帐篷 | tool | workshop | 2 | 2 | cloth2+wood2→tent1 |
| fishing_rod | 鱼竿 | tool | workshop | 1 | 1 | wood2+fiber1→fishing_rod1 |
| pickaxe | 镐 | tool | blacksmith | 2 | 2 | iron_ingot2+wood1→pickaxe1 |
**生产流程（_update_production）**：生产队列项每日progress+1→满total_time后按quantity将outputs加入资源→移除队列。
**资源流转（_update_resources）**：基础消耗=居民数×2食物/天（不足则各居民morale-5）；资源建筑按base_production×worker_count产出；加工/制造经配方投入产出转换。
**扩展点[EXT-资产]**：新增配方入production_recipes、新增原料资源入resource_definitions。
### M16.6 事件与税收系统

**数据源**：_trigger_events/_check_event_conditions/_apply_event/_collect_taxes（行7830-7910）、settlement_events事件库（行10200-10310）、Settlement类events字段（行7520）

**依赖**：@M16.4 城镇生成与据点管理、@M16.5 生产配方与资源流转、@M13 资源系统、@M02 战斗系统（combat事件联动）

**状态**：✅ 已填充 v1.0

#### 16.6.1 事件库总表（7个事件）

| 事件ID | 名称 | 类型 | 触发条件 | 效果 |
|--------|------|------|----------|------|
| harvest_festival | 丰收节 | positive | food>500 | 全居民morale+10 |
| bandit_raid | 强盗袭击 | negative | security<50 | 资源损失、可能触发战斗 |
| plague | 瘟疫 | negative | 随机 | 居民健康下降、士气降低 |
| merchant_caravan | 商队到访 | positive | 随机 | 获得随机资源、贸易机会 |
| mine_collapse | 矿洞塌方 | negative | 存在mine建筑 | 矿产量损失、可能伤亡 |
| drought | 干旱 | negative | 存在farm建筑 | 食物产量下降 |
| festival | 节日庆典 | positive | 随机 | 全居民morale+5、消耗金币 |

#### 16.6.2 事件触发机制（_trigger_events）

- 每日10%概率触发事件
- 从event_library中筛选满足_check_event_conditions条件的事件
- 随机选择一个事件触发并应用效果

#### 16.6.3 事件条件检查（_check_event_conditions）

- security_below：安全度低于指定阈值时触发
- food_above：食物储备高于指定阈值时触发
- 建筑存在性检查：mine_collapse要求存在mine、drought要求存在farm
- 未满足条件的事件不进入候选池

#### 16.6.4 事件应用（_apply_event）

- 记录事件到settlement.events列表（含时间戳与结果）
- 应用resources/stats即时效果（增减资源、士气、安全度）
- combat类型事件调用战斗系统结算

#### 16.6.5 税收系统（_collect_taxes）

- tax_rate默认0.05，可在据点设置中调整
- 按居民工作产出收税：tax_income=基础收入10×tax_rate
- 居民数量与工作效率直接影响税收总量
- 税收金币入账settlement.gold

#### 16.6.6 据点概览（get_settlement_summary）

返回据点完整状态：name/population/buildings/resources/security/tax_rate/events

**扩展点[EXT-规则]**：新增事件入settlement_events事件库、调整触发概率与税率参数、自定义事件条件与效果。
### M16.7 接口注册与核心联动

**数据源**：register_with_core（行7900-7910）、create_settlement初始化流程（行7540-7610）、_building_type_to_job映射（行7650）

**依赖**：@M01 核心框架、@M02 战斗系统（combat事件）、@M04 帮派系统（地盘归属）、@M09 NPC系统（居民日程）、@M13 资源系统

**状态**：✅ 已填充 v1.0

#### 16.7.1 接口注册表（register_with_core，10键）

| 接口键 | 功能 | 参数 |
|--------|------|------|
| sandbox_manager | 沙盒管理器实例 | - |
| create_settlement | 创建据点 | name/player_state |
| build | 建造建筑 | building_type/x/y |
| upgrade | 升级建筑 | building_id |
| demolish | 拆除建筑 | building_id |
| recruit | 招募居民 | template_id |
| assign_job | 分配工作 | resident_id/job |
| start_production | 启动生产 | recipe_id/building_id |
| daily_settlement_update | 每日更新 | settlement_id |
| get_settlement_summary | 据点概览 | settlement_id |

#### 16.7.2 职业映射表（_building_type_to_job）

| 建筑类型 | 映射职业 |
|----------|----------|
| RESOURCE | FARMER |
| PROCESSING | CRAFTSMAN |
| DEFENSE | GUARD |
| COMMERCIAL | MERCHANT |
| CULTURAL | SCHOLAR |

#### 16.7.3 核心联动机制

- create_settlement绑定player_state并记录established_day（建城日）
- daily_tick六步更新：生产→资源→居民→建造→事件→税收
- combat类型事件联动战斗系统结算
- 帮派地盘归属影响据点安全度与税收
- NPC居民与据点建筑通过assign_job双向绑定

**扩展点[EXT-接口]**：新增自定义接口键、扩展daily_tick更新步骤、联动其他模块事件。
