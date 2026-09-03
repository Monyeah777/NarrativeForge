### M17.1 生产配方总表

**数据源**：ProductionRecipe类（行7500-7510）、production_recipes（行34191-34919，40配方）、start_production（行7706-7750）、craft_magical_item（行2971-3033）

**依赖**：@M16 建筑与城镇（生产建筑与工人）、@M05 装备与物品（产出物品入库存）、@M09 经济与贸易（产出资源流转）、@M11 魔法系统（魔法物品制作）

**状态**：✅ 已填充 v1.0

#### 17.1.1 配方数据结构（ProductionRecipe）

| 字段 | 说明 |
|------|------|
| id | 配方唯一ID |
| name | 产物名称 |
| inputs | 投入资源 {资源名: 数量} |
| outputs | 产出资源 {资源名: 数量} |
| time | 生产所需天数 |
| required_building | 所需建筑类型 |
| required_skill | 所需技能等级 |

#### 17.1.2 食物类配方（5个）

| 配方ID | 产物 | 建筑 | 技能 | 天数 | 投入→产出 |
|--------|------|------|------|------|-----------|
| bread | 面包 | bakery | 1 | 1 | flour2+water1→bread5 |
| cooked_fish | 烤鱼 | tavern | 1 | 1 | raw_fish1+salt1→cooked_fish2 |
| cooked_meat | 烤肉 | tavern | 1 | 1 | raw_meat1+salt1→cooked_meat2 |
| vegetable_soup | 蔬菜汤 | tavern | 1 | 1 | vegetable2+water1+salt1→vegetable_soup3 |
| cheese | 奶酪 | farm | 2 | 2 | milk5+salt1→cheese3 |

#### 17.1.3 材料类配方（8个）

| 配方ID | 产物 | 建筑 | 技能 | 天数 | 投入→产出 |
|--------|------|------|------|------|-----------|
| flour | 面粉 | mill | 1 | 1 | wheat2→flour3 |
| iron_ingot | 铁锭 | blacksmith | 1 | 2 | iron_ore3+coal1→iron_ingot2 |
| steel_ingot | 钢锭 | blacksmith | 3 | 3 | iron_ingot2+coal2→steel_ingot1 |
| mithril_ingot | 秘银锭 | blacksmith | 5 | 5 | mithril_ore2+magic_essence1→mithril_ingot1 |
| magic_essence | 魔法精华 | magic_tower | 4 | 3 | magic_crystal1+mana_herb3→magic_essence2 |
| rune_stone | 符文石 | magic_tower | 5 | 4 | stone2+magic_essence2→rune_stone1 |
| wood_plank | 木板 | sawmill | 1 | 1 | wood2→wood_plank3 |
| paper | 纸张 | mill | 2 | 2 | wood1+cloth1→paper5 |

#### 17.1.4 武器类配方（6个）

| 配方ID | 产物 | 建筑 | 技能 | 天数 | 投入→产出 |
|--------|------|------|------|------|-----------|
| iron_sword | 铁剑 | blacksmith | 2 | 3 | iron_ingot2+wood1→iron_sword1 |
| steel_longsword | 钢制长剑 | blacksmith | 3 | 4 | steel_ingot2+leather1→steel_longsword1 |
| iron_dagger | 铁匕首 | blacksmith | 1 | 2 | iron_ingot1+leather1→iron_dagger2 |
| battle_axe | 战斧 | blacksmith | 3 | 4 | steel_ingot3+wood2→battle_axe1 |
| longbow | 长弓 | workshop | 2 | 3 | magic_wood2+leather2→longbow1 |
| enchanted_weapon | 附魔武器 | magic_tower | 5 | 5 | iron_sword1+magic_essence3+rune_stone1→enchanted_sword1 |

#### 17.1.5 防具类配方（5个）

| 配方ID | 产物 | 建筑 | 技能 | 天数 | 投入→产出 |
|--------|------|------|------|------|-----------|
| leather_armor | 皮甲 | workshop | 1 | 2 | leather3+thread1→leather_armor1 |
| chainmail | 锁子甲 | blacksmith | 3 | 5 | iron_ingot5+leather2→chainmail1 |
| plate_armor | 板甲 | blacksmith | 4 | 6 | steel_ingot6+leather3→plate_armor1 |
| shield | 盾牌 | workshop | 2 | 3 | wood3+iron_ingot1→shield1 |
| tower_shield | 塔盾 | blacksmith | 4 | 5 | steel_ingot4+wood4→tower_shield1 |

#### 17.1.6 消耗品类配方（5个）

| 配方ID | 产物 | 建筑 | 技能 | 天数 | 投入→产出 |
|--------|------|------|------|------|-----------|
| health_potion_small | 小型生命药水 | alchemy_lab | 1 | 1 | healing_herb2+water1→health_potion_small3 |
| health_potion_medium | 中型生命药水 | alchemy_lab | 2 | 2 | healing_herb3+magic_essence1→health_potion_medium2 |
| health_potion_large | 大型生命药水 | alchemy_lab | 3 | 3 | healing_herb5+magic_essence2→health_potion_large1 |
| mana_potion_small | 小型魔力药水 | alchemy_lab | 1 | 1 | mana_herb2+water1→mana_potion_small3 |
| antidote | 解毒剂 | alchemy_lab | 1 | 1 | nightshade1+healing_herb1→antidote2 |

#### 17.1.7 工具类配方（8个）

| 配方ID | 产物 | 建筑 | 技能 | 天数 | 投入→产出 |
|--------|------|------|------|------|-----------|
| torch | 火把 | workshop | 0 | 1 | wood1+cloth1→torch4 |
| rope | 绳索 | workshop | 1 | 1 | hemp3→rope1 |
| tent | 帐篷 | workshop | 2 | 3 | cloth5+wood3+rope1→tent1 |
| fishing_rod | 鱼竿 | workshop | 1 | 2 | wood2+hemp2+iron_ingot1→fishing_rod1 |
| pickaxe | 镐 | blacksmith | 2 | 2 | iron_ingot2+wood1→pickaxe1 |
| axe | 斧 | blacksmith | 2 | 2 | iron_ingot2+wood1→axe1 |
| hoe | 锄 | blacksmith | 1 | 1 | iron_ingot1+wood1→hoe1 |
| scythe | 镰刀 | blacksmith | 2 | 2 | iron_ingot2+wood1→scythe1 |

#### 17.1.8 饮品与物品类配方（3个）

| 配方ID | 产物 | 建筑 | 技能 | 天数 | 投入→产出 |
|--------|------|------|------|------|-----------|
| wine | 葡萄酒 | vineyard | 2 | 10 | grape10+sugar2→wine5 |
| beer | 麦酒 | tavern | 1 | 5 | barley5+water5+hops1→beer10 |
| book | 书籍 | library | 3 | 3 | paper10+leather1+ink1→book1 |

### M17.2 生产流程与队列机制

**数据源**：start_production（行7706-7750）、_update_production（行7755-7775）、Settlement.production_queue（行7525）

**依赖**：@M16.5 生产配方与资源流转、@M16.4 城镇生成与据点管理

**状态**：✅ 已填充 v1.0

#### 17.2.1 开始生产五步检查（start_production）

| 步骤 | 检查项 | 失败返回 |
|------|--------|----------|
| 1 | 配方是否存在（production_recipes.get） | 配方不存在 |
| 2 | 建筑是否存在（settlement.buildings.get） | 建筑不存在 |
| 3 | 建筑类型匹配（recipe.required_building == building.type） | 建筑类型不匹配 |
| 4 | 工人技能足够（取建筑内工人最高skill_level ≥ required_skill） | 工人技能不足，需要{n} |
| 5 | 资源足够（inputs×quantity逐项核对） | {资源}不足 |

#### 17.2.2 资源扣除与入队

- 全部检查通过后，按 inputs×quantity 逐项扣除资源
- 生产项加入 settlement.production_queue 队列：{recipe_id, building_id, quantity, progress=0, total_time=time×quantity}
- 返回 (True, "开始生产{recipe.name}")

#### 17.2.3 每日生产进度（_update_production）

- 遍历生产队列，每项 progress+1
- progress 满 total_time 后，按 outputs×quantity 将产物加入资源
- 完成项从队列移除

### M17.3 技能等级与生产门槛

**数据源**：ProductionRecipe.required_skill（行7500-7510）、配方表技能列（行34191-34919）、Resident.skill_level（行7485）

**依赖**：@M16.3 居民模板与生成机制、@M16.7 职业映射表

**状态**：✅ 已填充 v1.0

#### 17.3.1 技能等级分布表

| 技能等级 | 可生产配方数 | 代表配方 | 门槛说明 |
|----------|-------------|----------|----------|
| 0 | 1 | torch 火把 | 无技能要求 |
| 1 | 15 | bread/flour/iron_ingot/铁匕首/皮甲/小型药水/绳索/锄 | 入门级 |
| 2 | 9 | 奶酪/铁剑/长弓/盾牌/中型药水/帐篷/鱼竿/镐/斧/镰刀/纸张 | 熟练级 |
| 3 | 7 | 钢锭/长剑/战斧/锁子甲/大型药水/书籍 | 专家级 |
| 4 | 4 | 板甲/塔盾/魔法精华 | 大师级 |
| 5 | 4 | 秘银锭/符文石/附魔武器 | 宗师级 |

#### 17.3.2 技能判定规则

- 取建筑内所有工人的最高 skill_level 作为判定值
- 工人技能低于配方要求时无法开始生产
- 技能等级随生产经验提升（与M03技能系统联动）

### M17.4 魔法物品制作（craft_magical_item）

**数据源**：craft_magical_item（行2980-3030）、register_with_core（行3032-3040）
**依赖**：@M05 装备与物品、@M16.5 生产配方与资源流转
**状态**：✅ 已填充 v1.0

#### 17.4.1 魔法制作流程（四步）

| 步骤 | 方法 | 说明 | 失败返回 |
|------|------|------|----------|
| 1 | _has_materials | 遍历库存逐项核对材料数量 | (False, None, "材料不足。") |
| 2 | _consume_materials | 按材料列表逐项扣减库存，数量≤0 时移除该物品 | - |
| 3 | _create_item_from_desc | 根据描述生成物品数据 {name: 描述前10字, type: magic_item, effect: 未知效果, quantity: 1} | (False, None, "制造失败。") |
| 4 | 追加记录 | 物品追加至 state.magic.crafted_items 与 state.inventory | - |

#### 17.4.2 魔法系统接口注册（8键）

| 注册键 | 绑定方法 | 功能 |
|--------|----------|------|
| magic_system | self | 魔法系统实例 |
| magic_cultivate | cultivate | 元素修炼 |
| magic_cast | cast_spell | 施法 |
| magic_parse_word | parse_word_spell | 解析咒语 |
| magic_combine_elements | combine_elements | 元素组合 |
| magic_craft | craft_magical_item | 魔法物品制作 |
| get_element_mastery | get_element_mastery | 查询元素熟练度 |
| modify_element_mastery | modify_element_mastery | 修改元素熟练度 |

### M17.5 制作任务配方（craft tasks）

**数据源**：制作任务配方（行29328-29372）
**依赖**：@M12 任务系统（intent=craft）、@M03 技能系统
**状态**：✅ 已填充 v1.0

#### 17.5.1 制作任务结构

| 字段 | 说明 |
|------|------|
| id | 任务唯一标识 |
| description | 任务描述 |
| intent | 任务意图（craft=制作类） |
| conditions | 触发条件（parameters / skills / inventory） |
| base_difficulty | 基础难度（0-1，越小越易成功） |
| effects | 结果（success / failure / critical_success 三态） |

#### 17.5.2 制作任务配方表（2个）

| 任务ID | 描述 | 条件 | 难度 | 成功 | 失败 | 大成功 |
|--------|------|------|------|------|------|--------|
| craft_iron_sword | 锻造铁剑 | 技能锻造≥2 + 铁锭2 + 木材1 | 0.7 | 产出铁剑（消耗铁锭2木材1） | 材料损坏（消耗铁锭2木材1） | 产出精良铁剑 |
| cook_fish | 烹饪鱼 | 鱼1 + 盐1 | 0.9 | 产出烤鱼（消耗鱼1盐1） | 鱼烤焦（消耗鱼1） | - |

### M17.6 模块联动与扩展点

- **产物流转**：生产/制作产物统一进入 settlement 资源或 state.inventory，供装备（@M05）、贸易（@M13）、战斗消耗使用
- **建筑绑定**：配方与建筑类型绑定，工人技能门槛联动技能系统（@M03）
- **任务联动**：intent=craft 的制作任务复用制作判定（条件/难度/三态结果）
- **魔法联动**：craft_magical_item 产出的 magic_item 同时进入 inventory 与 crafted_items
- **扩展点[EXT-资产]**：新增生产配方（food/material/weapon/armor/consumable/tool/drink/item）
- **扩展点[EXT-规则]**：生产流程新增检查步骤、魔法物品生成规则
- **扩展点[EXT-接口]**：start_production / magic_craft / craft 任务接口复用
