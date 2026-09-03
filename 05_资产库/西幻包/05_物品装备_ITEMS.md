### 模块正文 M05.装备与物品

#### 1. 物品刷新池体系
- 全游戏物品通过 **刷新池（refresh pool）** 组织，共21个池，分5大类：
  - **商店池**（8个）：shop_basic_goods（基础商品）、shop_weapons（武器店）、shop_armor（防具店）、shop_consumables（消耗品店）、shop_magic（魔法商店）、shop_alchemy（炼金商店）、shop_blacksmith（铁匠铺）、shop_general（杂货综合）
  - **宝箱池**（3个）：loot_common_chest（普通）/ loot_rare_chest（稀有）/ loot_epic_chest（史诗）
  - **怪物掉落池**（6个）：enemy_beast_loot（野兽）/ enemy_humanoid_loot（人形）/ enemy_undead_loot（亡灵）/ enemy_demon_loot（恶魔）/ enemy_elemental_loot（元素）/ enemy_dragonkin_loot（龙裔）
  - **资源池**（4个）：resource_mining（采矿）/ resource_herb（草药）/ resource_wood（伐木）/ fishing（钓鱼）
- 池条目通用结构：`{name, weight, quantity, min_level?, max_level?, quality?}`
  - weight：抽取权重（越大越常见）
  - quantity：数量骰（如"2d6"）或固定值
  - min_level / max_level：等级区间限制（玩家等级不满足则不出现）

#### 2. 商店刷新规则（按地区）
| 地区 | 基础池 | 基础数量 | 附加池（数量 × 概率） | 固定商品 |
|---|---|---|---|---|
| 北村 | shop_general | 10 | 武器2×0.8 / 防具2×0.5 / 消耗品3×0.7 | 面包×5 |
| 冰风城 | shop_general | 15 | 武器3×1.0 / 防具3×1.0 / 消耗品5×1.0 / 魔法2×0.4 | 冰钢×2、鲸油×3 |
| 蔚蓝港 | shop_general | 20 | 武器4×1.0 / 防具4×1.0 / 消耗品6×1.0 / 魔法3×0.6 / 炼金4×0.8 | — |
| 铁炉堡 | shop_blacksmith | 12 | 武器5×1.0 / 防具5×1.0 | 秘银矿石×1（0.3概率） |
| 月影 | shop_magic | 8 | 炼金3×0.9 | 精灵工艺品×2 |
- 刷新逻辑：基础池必刷满 base_count 件；附加池按 probability 判定是否参与，参与则抽取 count 件；固定商品每次必在。

#### 3. 资源采集与刷新
- 资源点按区域配置采集组（groups），每组含：名称 / 概率 / 池 / 数量 / 条件：
  - **北森林**：木材0.8→resource_wood×3；狩猎0.5→enemy_beast_loot×1；草药0.4→resource_herb×2
  - **西矿脉**：铁矿1.0→resource_mining×4；稀有矿石0.2→resource_mining×1（需Lv3+）
  - **东草原**：狩猎0.9→enemy_beast_loot×2；采集0.6→resource_herb×2
- 资源池内容示例：resource_mining（铁矿石80/铜矿石70/锡矿石60/银矿石30/金矿石15/秘银矿石3/宝石10/煤矿50）；resource_herb（普通草药100/疗伤草60/魔力草50/龙葵20/龙血草2/月长石5）；fishing（鱼80/旧靴子10/魔法鱼1）

#### 4. 怪物掉落表（enemy_loot_tables）
| 怪物 | 必掉组 | 附加掉落 |
|---|---|---|
| 野狼 wolf | enemy_beast_loot×1 | 狼牙1d2（0.3） |
| 熊 bear | enemy_beast_loot×2 | 熊胆×1（0.5） |
| 强盗 bandit | enemy_humanoid_loot×1 | 铜币2d10（0.2） |
| 强盗头目 bandit_leader | enemy_humanoid_loot×2 | 金币2d10 + 长剑×1（1.0） |
| 骷髅 skeleton | enemy_undead_loot×1 | — |
| 火元素 fire_elemental | enemy_elemental_loot×1 | — |
| 幼龙 drake | enemy_dragonkin_loot×2 | — |
- 各池核心掉落：野兽（皮革/肉/毛皮/狼牙/兽骨）；人形（铜银币/短剑/长剑/皮甲）；亡灵（骨头/黑暗护符/灵魂宝石）；恶魔（硫磺/恶魔角/火焰心脏/深渊核心）；元素（元素核心/黑曜石）；龙裔（龙鳞/龙牙/龙血/龙晶）

#### 5. 宝箱掉落表（chest_tables）
| 宝箱 | 固定掉落 | 随机池 | 保底 |
|---|---|---|---|
| 普通宝箱 common_chest | — | loot_common_chest×2 | — |
| 稀有宝箱 rare_chest | 金币3d10 | loot_rare_chest×3 | — |
| 史诗宝箱 epic_chest | 金币5d20 + 中型生命药水1d2 | loot_epic_chest×2 | — |
| 古代宝箱 ancient_chest | — | loot_epic×1 + loot_rare×2 | 古代遗物×1 |
- 宝箱池梯度：普通（铜银币/面包/铁器）；稀有（金币/秘银剑5%/板甲/火焰冰霜法杖）；史诗（龙骨剑5%/龙鳞/闪电暗影法杖/灵魂宝石/符文石）

#### 6. 刷新间隔（refresh_intervals）
- 默认：1天
- 商店：北村2天 / 冰风城3天 / 蔚蓝港2天 / 铁炉堡3天 / 月影5天
- 资源：北森林1天 / 西矿脉2天 / 东草原1天
- 宝箱：普通7天 / 稀有14天 / 史诗30天；古代宝箱 -1（永不刷新，一次性）

#### 7. 职业资源映射（job_resource_map，18职业）
| 职业 | 主资源 | 副资源 |
|---|---|---|
| 战士 / 铁匠 / 农夫 / 冒险者 | stamina | health |
| 游侠 / 盗贼 | energy | focus |
| 法师 | mana | insanity |
| 牧师 | willpower | health |
| 吟游诗人 | willpower | mana |
| 萨满 / 德鲁伊 | equilibrium | mana |
| 魅惑师 | willpower | insanity |
| 商人 | willpower | energy |
| 学者 | mana | focus |
| 死灵法师 | souls | mana |
| 狂战士 | hate | stamina |
| 时空法师 | paradox | mana |
| 邪术师 | vim | insanity |
- 资源映射决定：职业行为消耗/恢复的资源种类、装备与职业的适配度、以及击杀战利品向资源转化的方向（如战士获得stamina倾向资源）。

#### 8. 商品经济学（commodities，37种）
- 商品结构：`{name, base_price, type, description, produced_in, demand{村庄/城镇/城市}, region_mult{11区域}, season_mult{四季}}`
- 37种商品清单：谷物/肉类/鱼/盐/羊毛/皮革/铁矿石/铁锭/铜矿石/锡矿石/银矿石/金矿石/秘银矿石/木材/魔法木材/普通草药/稀有草药/毛皮/鲸油/冰钢/葡萄酒/橄榄油/香料/骏马/奶酪/宝石/精良武器/矮人烈酒/符文石/精灵工艺品/珍珠/珊瑚/龙鳞/龙血草/海盗宝藏
- 定价机制：`实际价格 = base_price × demand[聚落类型] × region_mult[区域] × season_mult[季节]`
- 示例：谷物 base 10 → 北境村庄冬季：10 × 1.2(村庄) × 1.5(北境) × 1.3(冬季) = 23.4
- 经济逻辑：产地（produced_in）外销价更高（如鲸油仅北境产，南境溢价）；季节影响（冬季农产品×1.3涨价，秋季×0.8丰收降价）；聚落规模影响（村庄消耗品需求1.2、城市奢侈品需求1.2）

#### 9. 装备属性要点
- 武器伤害以骰面定义（代码层 `damage: "1d4"~"1d6"` 起步，随材质升级），材质梯度：铁（Lv1匕首1d4/剑1d6）→ 钢（Lv3长剑1d8）→ 秘银（Lv5）→ 矮人/龙骨（Lv10）→ 传说（Lv15）
- 防具按部位：头（皮头盔/铁盔/巨盔）、身（皮甲/锁子甲/板甲/矮人板甲）、手（皮手套/铁护手）、腿（皮靴/铁护腿）、盾（盾牌/塔盾）
- 等级解锁联动（@M03:level_unlock）：Lv1铁剑皮甲 → Lv3钢剑锁子甲 → Lv5秘银剑板甲 → Lv8冶炼附魔 → Lv10龙骨剑矮人板甲 → Lv12龙鳞甲 → Lv15传说之刃
- 魔法装备线：火焰/冰霜/闪电/暗影法杖、火球术/传送卷轴、魔法水晶/元素水晶/灵魂宝石/符文石，与M04元素反应系统联动
- 消耗品线：生命药水（小/中/大）、魔力药水（小/中）、解毒剂、力量灵药；炼金材料（普通草药/疗伤草/魔力草/龙葵/龙血草）

#### 10. 生成示例
```
场景：冒险者（战士Lv2）抵达北村，进入铁匠铺
铁匠铺池：shop_blacksmith（基础12件）
刷新：铁矿石2d6 / 铁锭1d8 / 钢锭1d4 / 铁剑×1 / 盾牌×1 / 锁子甲×1 / 铁盔×1 …
等级过滤：玩家Lv2 → 钢制长剑(min Lv3)不出现
战斗：击杀野狼 → enemy_beast_loot：皮革1d2、肉1d4、狼牙1d3
职业映射：战士 → [stamina, health] → 战利品肉/皮革转化为体力与生命恢复资源
商店定价：北村面包 = 10 × 1.0(村庄面包需求) × 1.2(北境) × 1.0(春) = 12
```
---
> 数据源：[EXT-资产]item_refresh_pools（行26505-26828）、shop_refresh_rules（行26882-26990）、resource_rules（行26990-27030）、enemy_loot_tables（行27030-27080）、chest_tables（行27080-27110）、refresh_intervals（行27110-27147）、commodities（行22421-23494）、job_resource_map（行24581-24600）
---
