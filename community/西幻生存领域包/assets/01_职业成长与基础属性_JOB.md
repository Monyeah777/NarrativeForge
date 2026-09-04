### M01.基础属性与角色创建

- 职责：定义玩家核心数据结构、七项基础属性、等级经验曲线、角色创建流程与职业选择
- 数据源：提取文本行95-270（体系总览/4.1种族/4.2职业/7.2升级）、行1100-1200（PlayerState）、行36820-37280（职业成长表）
- 依赖：M02种族（种族属性加成）、M03技能（技能点分配）、M10死亡（死亡惩罚与继承）
- 扩展点：自定义难度（difficulty）、自定义职业、自定义背景
- 状态：✅已填充v1.0

#### 1. 角色创建流程

1. **选种族**：人类/精灵/矮人/兽人（含猫人）/美人鱼/龙裔/魅魔，应用种族属性加成（见M02）
2. **选职业**：战士/游侠/法师/牧师/盗贼/吟游诗人/萨满/魅惑师，应用职业属性映射（job_attribute_map）
3. **选背景**：平民、猎户、矿工、水手、贵族、学者、奴隶、孤儿、前教团成员、魔王军逃兵等，影响初始技能与财产
4. **分配属性点**：七项基础属性默认10，按种族/职业调整后，可用attribute_points补充
5. **初始化状态**：健康100、饥饿80、口渴70、疲劳20、金币0/银币0/铜币100

#### 2. 七项基础属性（默认10）

| 属性 | 作用 | 典型检定 |
|---|---|---|
| 力量 | 近战伤害、负重、破防 | 战斗力量检定 |
| 敏捷 | 闪避、先手、潜行、远程命中 | 战斗敏捷检定 |
| 体质 | 生命上限、耐力、抗毒 | 生存体质检定 |
| 智力 | 法术强度、学习速度 | 魔法智力检定 |
| 感知 | 侦察、陷阱发现、自然共鸣 | 环境感知检定 |
| 魅力 | 交易、说服、好感 | 社交魅力检定 |
| 意志 | 抗精神、抗魅惑、疯狂抵抗 | 意志检定 |

#### 3. 等级与经验

- 升级所需经验：`exp_next = 10 × 1.5^(level-1)`（指数增长）
- 升级奖励：**+1 属性点 +1 技能点**，每5级触发特殊奖励（可扩展）
- 经验来源：战斗、任务、学习、探索、制造——**任何行动均可获得经验**（成长无边界）

#### 4. 生存状态管理

| 状态 | 默认 | 消耗规则（每分钟） | 危险阈值 |
|---|---|---|---|
| 健康 health | 100 | 战斗/受伤扣减 | ≤0 死亡 |
| 饥饿 hunger | 80 | -0.1/分钟 | ≤0 死亡 |
| 口渴 thirst | 70 | -0.15/分钟 | ≤0 死亡 |
| 疲劳 fatigue | 20 | +0.05/分钟 | ≥100 死亡 |
| 温度 temperature | 正常 | 季节/环境修正 | 极端值影响状态 |
| 疯狂 insanity | 0 | 恐怖/混沌事件累积 | 高值触发幻觉 |

#### 5. 核心数据结构（PlayerState）

| 区块 | 字段 | 说明 |
|---|---|---|
| basic | name/level/exp/exp_next/birthplace/background/age/gender | 基础身份 |
| attributes | 力量/敏捷/体质/智力/感知/魅力/意志 | 七项属性 |
| attribute_points | 可分配属性点 | 升级获得 |
| skill_points | 可分配技能点 | 升级获得 |
| skills | 技能列表 | 元素格式由外部库定义 |
| abilities | 能力列表 | 含碎片能力 |
| inventory | 物品列表 | 背包 |
| status | health/hunger/thirst/fatigue/temperature/insanity | 生存状态 |
| location | region/subarea/description/danger_level | 当前位置 |
| time | day/hour/minute/season/weather | 游戏时间 |
| relations | NPCs/factions | 关系网 |
| knowledge | 已知信息 | 角色限知 |
| economy | gold/silver/copper | 货币（1金=100银=10000铜） |
| death_blessings | 死亡祝福列表 | 见M10 |
| relics | 遗物列表 | 继承遗产 |
| gacha | pity_blue/pity_purple/pity_orange/orange_probability/total_pulls | 抽卡保底（白60/蓝30/紫8/橙2） |
| difficulty | 难度 | 标准冒险等 |
| rogue | death_count/streak/blessing_slots | 死亡继承（blessing_slots默认1） |

#### 6. 职业成长表（节选，18职业完整数据见提取文本行36820-37280）

| 职业 | 日基础经验 | 10级升级需求 | 日收入(满级) | 日消耗 |
|---|---|---|---|---|
| 农民 | 5 | [0,100,250,450,700,1000,1350,1750,2200,2700] | 160 | 食物1 |
| 音乐家 | 6 | [0,120,290,520,820,1190,1630,2150,2760,3480] | 200 | — |
| 乞丐 | 3 | [0,80,200,360,560,800,1080,1400,1760,2160] | 54 | — |
| 小偷 | 7 | [0,150,350,600,900,1250,1650,2100,2600,3150] | 315 | — |
| 店主 | 4 | [0,110,270,480,750,1080,1470,1920,2430,3000] | 252 | 金币2 |
| 旅行者 | 8 | [0,200,450,750,1100,1500,1950,2450,3000,3600] | 162 | 食物2 |
| 学者 | 5 | [0,120,290,510,780,1100,1470,1890,2360,2880] | 108 | — |
| 艺术家 | 5 | [0,130,310,550,850,1210,1630,2110,2650,3250] | 163 | — |
| 角斗士 | 9 | [0,250,550,900,1300,1750,2250,2800,3400,4050] | 360 | 食物3水2 |
| 猎人 | 7 | [0,180,410,700,1050,1460,1930,2460,3050,3700] | 252 | 食物1工具1 |
| 渔夫 | 6 | [0,150,340,580,870,1210,1600,2040,2530,3070] | 198 | 食物1 |
| 厨师 | 5 | [0,140,320,550,830,1160,1540,1970,2450,2980] | 172 | 食物3 |

> 剩余6职业（含生活职业）完整数据：`[EXT-资产]职业系统职业成长表行36820-37280`

#### 7. 生成示例

```
创建角色：人类→战士→孤儿背景
力量10+2(战士职业映射)、敏捷10、体质10、智力10、感知10、魅力10、意志10
初始物品：破旧铁剑、木盾、3铜币
```

---


---
<!-- 外部完整实体源：/tmp/extract_test.txt 行36820-37280（18职业成长完整表） -->

        "人类": 0.4,
        "精灵": 0.2,
        "矮人": 0.5,
        "猫人": 0.6,
        "美人鱼": 0.1,
        "龙裔": 0.2,
        "魅魔": 0.2
      },
      "猫人": {
        "人类": 0.5,
        "精灵": 0.4,
        "矮人": 0.3,
        "兽人": 0.6,
        "美人鱼": 0.1,
        "龙裔": 0.1,
        "魅魔": 0.3
      },
      "美人鱼": {
        "人类": 0.2,
        "精灵": 0.1,
        "矮人": 0.1,
        "兽人": 0.1,
        "猫人": 0.1,
        "龙裔": 0.05,
        "魅魔": 0.1
      },
      "龙裔": {
        "人类": 0.1,
        "精灵": 0.1,
        "矮人": 0.2,
        "兽人": 0.2,
        "猫人": 0.1,
        "美人鱼": 0.05,
        "魅魔": 0.1
      },
      "魅魔": {
        "人类": 0.3,
        "精灵": 0.2,
        "矮人": 0.1,
        "兽人": 0.2,
        "猫人": 0.3,
        "美人鱼": 0.1,
        "龙裔": 0.1
      }
    }
  }
}
{
  "farmer": {
    "name": "农民",
    "daily_exp_base": 5,
    "exp_requirements": [0, 100, 250, 450, 700, 1000, 1350, 1750, 2200, 2700],
    "daily_income": [0, 5, 12, 22, 35, 50, 70, 95, 125, 160],
    "daily_consume": { "food": 1 }
  },
  "musician": {
    "name": "音乐家",
    "daily_exp_base": 6,
    "exp_requirements": [0, 120, 290, 520, 820, 1190, 1630, 2150, 2760, 3480],
    "daily_income": [0, 8, 18, 32, 50, 72, 98, 128, 162, 200],
    "daily_consume": {}
  },
  "beggar": {
    "name": "乞丐",
    "daily_exp_base": 3,
    "exp_requirements": [0, 80, 200, 360, 560, 800, 1080, 1400, 1760, 2160],
    "daily_income": [0, 2, 5, 9, 14, 20, 27, 35, 44, 54],
    "daily_consume": {}
  },
  "thief": {
    "name": "小偷",
    "daily_exp_base": 7,
    "exp_requirements": [0, 150, 350, 600, 900, 1250, 1650, 2100, 2600, 3150],
    "daily_income": [0, 15, 35, 60, 90, 125, 165, 210, 260, 315],
    "daily_consume": {}
  },
  "shopkeeper": {
    "name": "店主",
    "daily_exp_base": 4,
    "exp_requirements": [0, 110, 270, 480, 750, 1080, 1470, 1920, 2430, 3000],
    "daily_income": [0, 12, 28, 48, 72, 100, 132, 168, 208, 252],
    "daily_consume": { "gold": 2 }
  },
  "traveler": {
    "name": "旅行者",
    "daily_exp_base": 8,
    "exp_requirements": [0, 200, 450, 750, 1100, 1500, 1950, 2450, 3000, 3600],
    "daily_income": [0, 6, 15, 27, 42, 60, 81, 105, 132, 162],
    "daily_consume": { "food": 2 }
  },
  "scholar": {
    "name": "学者",
    "daily_exp_base": 5,
    "exp_requirements": [0, 120, 290, 510, 780, 1100, 1470, 1890, 2360, 2880],
    "daily_income": [0, 4, 10, 18, 28, 40, 54, 70, 88, 108],
    "daily_consume": {}
  },
  "artist": {
    "name": "艺术家",
    "daily_exp_base": 5,
    "exp_requirements": [0, 130, 310, 550, 850, 1210, 1630, 2110, 2650, 3250],
    "daily_income": [0, 7, 16, 28, 43, 61, 82, 106, 133, 163],
    "daily_consume": {}
  },
  "gladiator": {
    "name": "角斗士",
    "daily_exp_base": 9,
    "exp_requirements": [0, 250, 550, 900, 1300, 1750, 2250, 2800, 3400, 4050],
    "daily_income": [0, 20, 45, 75, 110, 150, 195, 245, 300, 360],
    "daily_consume": { "food": 3, "water": 2 }
  },
  "hunter": {
    "name": "猎人",
    "daily_exp_base": 7,
    "exp_requirements": [0, 180, 410, 700, 1050, 1460, 1930, 2460, 3050, 3700],
    "daily_income": [0, 12, 28, 48, 72, 100, 132, 168, 208, 252],
    "daily_consume": { "food": 1, "tool": 1 }
  },
  "fisher": {
    "name": "渔夫",
    "daily_exp_base": 6,
    "exp_requirements": [0, 150, 340, 580, 870, 1210, 1600, 2040, 2530, 3070],
    "daily_income": [0, 10, 23, 39, 58, 80, 105, 133, 164, 198],
    "daily_consume": { "food": 1 }
  },
  "cook": {
    "name": "厨师",
    "daily_exp_base": 5,
    "exp_requirements": [0, 140, 320, 550, 830, 1160, 1540, 1970, 2450, 2980],
    "daily_income": [0, 8, 18, 31, 47, 66, 88, 113, 141, 172],
    "daily_consume": { "food": 3 }
  }
}
{
  "death_by_chaos": [
    {
      "id": "self_summoned_monster",
      "description": "你召唤的怪物觉得你看起来更美味，一口把你吞了下去。"
    },
    {
      "id": "door_crush",
      "description": "你试图安装任意门，但门掉下来砸死了你。"
    },
    {
      "id": "poison_food",
      "description": "你吃的那个奇怪的东西有毒……你七窍流血而死。"
    },
    {
      "id": "whip_self",
      "description": "你挥舞鞭子时没控制好，抽到了自己的脸上，失血过多。"
    },
    {
      "id": "pickpocket_wrong",
      "description": "你想偷那个人的钱包，但他是个退休的盗贼大师，反手把你阉了，你流血而亡。"
    },
    {
      "id": "harvest_angry",
      "description": "你想从牛身上挤奶，但牛一脚把你踢飞，你撞在石头上死了。"
    },
    {
      "id": "bad_music",
      "description": "你的演奏太难听，听众愤怒地把你扔下悬崖。"
    },
    {
      "id": "farm_failure",
      "description": "你种地时被自己挖出的坑绊倒，头朝下插进土里窒息而死。"
    },
    {
      "id": "barter_fight",
      "description": "你试图以物易物，但对方觉得你在侮辱他，一剑捅穿了你。"
    },
    {
      "id": "torture_self",
      "description": "你折磨别人时，工具滑脱扎进了你自己的大腿动脉。"
    },
    {
      "id": "streak_freeze",
      "description": "你裸奔到雪地里，被冻成了冰雕。"
    },
    {
      "id": "dance_off_cliff",
      "description": "你跳舞时太投入，没注意身后是悬崖，一脚踩空。"
    },
    {
      "id": "sex_with_monster",
      "description": "你和那个怪物……的过程中，它不小心把你压扁了。"
    },
    {
      "id": "lockpick_explode",
      "description": "你开锁时触发了魔法陷阱，锁爆炸了，碎片扎了你一身。"
    },
    {
      "id": "drink_unknown",
      "description": "你喝下那瓶不明液体，原来是强酸，你从嘴里开始融化。"
    },
    {
      "id": "kick_chicken",
      "description": "你踢了一只鸡，结果它是魔王变的，一口火把你烧成灰。"
    },
    {
      "id": "curse_item_backfire",
      "description": "你戴上了那个诅咒戒指，戒指突然收紧，勒断了你的手指，你感染而死。"
    },
    {
      "id": "sleep_on_trap",
      "description": "你躺下睡觉，但身下是个陷阱，你被倒吊起来，然后被尖刺刺穿。"
    },
    {
      "id": "throw_rock_at_god",
      "description": "你朝天空扔石头，石头反弹回来，正中你的脑门。"
    },
    {
      "id": "insult_dragon",
      "description": "你骂那条龙是条笨蜥蜴，它用尾巴把你拍成了肉饼。"
    },
    {
      "id": "kiss_frog_prince",
      "description": "你亲了一只青蛙，以为会变成王子，结果青蛙有毒，你嘴唇肿得无法呼吸。"
    },
    {
      "id": "jump_into_well",
      "description": "你跳进井里想游泳，但井太深，你摔死在井底。"
    },
    {
      "id": "fart_in_cave",
      "description": "你在洞穴里放了个屁，引燃了沼气，被炸飞。"
    },
    {
      "id": "wear_upside_down",
      "description": "你把裤子套在头上，挡住了视线，一脚踩空掉进下水道淹死。"
    },
    {
      "id": "talk_to_self",
      "description": "你对着镜子自言自语，镜子里的你伸出手把你拉进了镜中世界，现实中的你变成了植物人，饿死了。"
    },
    {
      "id": "count_sheep",
      "description": "你数羊数到第一千只时，羊群冲出来把你踩死了。"
    },
    {
      "id": "build_sandcastle",
      "description": "你堆的沙堡塌了，埋住了你，你窒息而死。"
    },
    {
      "id": "blow_bubbles",
      "description": "你吹的肥皂泡把你包住飘上了天，然后破了你摔下来。"
    },
    {
      "id": "play_with_fire",
      "description": "你玩火点着了衣服，扑不灭。"
    },
    {
      "id": "lick_frozen_metal",
      "description": "你舔了冻住的铁栏杆，舌头粘住了，然后被冻死。"
    },
    {
      "id": "challenge_duck",
      "description": "你向一只鸭子发起决斗，鸭子叫来一群同伴把你啄成了筛子。"
    }
  ]
}
随机生成器系统设计（基于超级库的动态生成）
一、设计理念
以现有的超级库（如 items、enemies、npcs 等）为模板种子，通过随机组合、数值变异、结构重组等方式生成全新的、不在超级库中的内容。这种机制可大幅提升游戏世界的多样性与不可预测性，同时保持与现有核心框架的兼容性。
二、核心架构
1. 生成器基类（Generator Base）
所有随机生成器继承自同一个抽象基类，提供通用方法：
```python
class BaseGenerator:
    def __init__(self, external_data):
        self.external_data = external_data          # 引用超级库
        self.templates = self.load_templates()      # 加载模板（如物品池、怪物池等）
        self.random = random.Random()                # 可播种的随机数生成器
    def load_templates(self):
        """子类需重写，指定从哪个超级库加载模板"""
        raise NotImplementedError
    def generate(self, **kwargs):
        """生成一个新实例，参数可强制指定某些属性"""
        raise NotImplementedError
    def mutate(self, instance, mutation_power=1.0):
        """对已有实例进行随机变异，返回副本"""
        raise NotImplementedError
    def combine(self, instances):
        """将多个实例融合成一个新实例（类似技能融合）"""
        raise NotImplementedError
```
2. 模板加载策略
每个生成器从对应的超级库中读取数据，但不仅限于使用它们作为唯一来源。模板用于定义基础结构、属性范围、概率权重等，生成时可在这些基础上进行扩展。
示例：
· ItemGenerator 从 items 库读取武器、防具等模板，但生成时可能随机组合前缀后缀、调整数值、添加随机附魔。
· MonsterGenerator 从 enemies 库读取种族类型、攻击方式，但生成时可能随机混搭不同种族的技能、改变体型、增加突变。
3. 生成机制
· 模板选择：根据权重从模板池中选取一个基础模板。
· 属性继承：复制模板的基本属性。
· 数值波动：对数值型属性应用随机乘数（如 基础值 * random.uniform(0.8, 1.2)）。
· 词缀系统：从词缀库中随机选取前缀/后缀，附加到名称和效果上。
· 元素组合：随机组合多个模板的特性（如怪物类型 + 元素类型）。
· 条件变异：根据生成时的上下文（玩家等级、地点、季节）调整属性。
· ID生成：使用哈希或UUID生成唯一标识，不与模板ID冲突。
4. 与超级库的衔接
· 生成的实例格式必须与超级库中的条目完全一致，以便无缝插入现有系统（如 items 库的每个条目都是一个字典，生成器也输出相同结构的字典）。
· 生成器可将其生成的条目临时添加到运行时缓存中，供当前游戏会话使用，也可选择持久化到外部文件（若需复用）。
---
三、示例：通用随机生成器框架（伪代码）
```python
import random
import hashlib
import copy
class RandomGenerator:
    """随机生成器基类"""
    def __init__(self, template_pool, rng_seed=None):
        self.template_pool = template_pool          # 列表或字典
        self.rng = random.Random(rng_seed)
    def pick_template(self, filters=None):
        """从模板池中按权重选取一个模板，可附加过滤条件"""
        candidates = self.template_pool
        if filters:
            candidates = [t for t in candidates if all(t.get(k)==v for k,v in filters.items())]
        if not candidates:
            return None
        weights = [t.get('weight', 1) for t in candidates]
        return self.rng.choices(candidates, weights=weights)[0]
    def generate_id(self, base_name):
        """生成唯一ID（基于名称+随机数+时间）"""
        raw = f"{base_name}_{self.rng.randint(10000,99999)}_{self.rng.random()}"
        return hashlib.md5(raw.encode()).hexdigest()[:12]
    def mutate_value(self, base, range_factor=0.2):
        """对数值进行随机波动"""
        if isinstance(base, (int, float)):
            delta = base * range_factor * (self.rng.random() - 0.5) * 2
            return int(base + delta) if isinstance(base, int) else base + delta
        return base
    def combine_dicts(self, dict1, dict2, mode='merge'):
        """合并两个字典（用于融合）"""
        result = copy.deepcopy(dict1)
        for k, v in dict2.items():
            if k in result:
                if isinstance(v, dict) and isinstance(result[k], dict):
                    result[k] = self.combine_dicts(result[k], v, mode)
                elif isinstance(v, (int, float)) and mode == 'add':
                    result[k] += v
                elif mode == 'override':
                    result[k] = v
            else:
                result[k] = v
        return result
    def generate(self, **kwargs):
        """抽象方法，子类实现"""
        raise NotImplementedError
```
---
四、具体生成器示例（以物品为例）
```python
class ItemRandomGenerator(RandomGenerator):
    def __init__(self, item_templates, affix_pool):
        super().__init__(item_templates)
        self.affix_pool = affix_pool          # 词缀库，包含前缀/后缀及其效果
    def generate(self, forced_rarity=None, forced_type=None):
        # 1. 选取基础模板
        template = self.pick_template(filters={'type': forced_type} if forced_type else None)
        if not template:
            return None
        # 2. 复制基础属性
        item = copy.deepcopy(template)
        # 3. 随机稀有度
        rarity_weights = {'common':60, 'uncommon':25, 'rare':10, 'epic':4, 'legendary':1}
        if forced_rarity:
            rarity = forced_rarity
        else:
            rarity = self.rng.choices(list(rarity_weights.keys()), weights=rarity_weights.values())[0]
        item['rarity'] = rarity
        # 4. 根据稀有度调整数值（伤害、护甲、价格等）
        rarity_mult = {'common':1.0, 'uncommon':1.2, 'rare':1.5, 'epic':2.0, 'legendary':3.0}
        mult = rarity_mult[rarity]
        if 'damage' in item:
            # 假设 damage 是字符串如 "2d6+3"，需要解析并调整
            item['damage'] = self.scale_damage(item['damage'], mult)
        if 'armor_class' in item:
            item['armor_class'] = int(item['armor_class'] * mult)
        item['value'] = int(item.get('value', 10) * mult)
        # 5. 随机添加词缀（前缀/后缀）
        affix_count = {'common':0, 'uncommon':1, 'rare':2, 'epic':3, 'legendary':4}[rarity]
        for _ in range(affix_count):
            if self.rng.random() &lt; 0.5 and self.affix_pool['prefixes']:
                affix = self.rng.choice(self.affix_pool['prefixes'])
                item = self.apply_affix(item, affix, 'prefix')
            else:
                if self.affix_pool['suffixes']:
                    affix = self.rng.choice(self.affix_pool['suffixes'])
                    item = self.apply_affix(item, affix, 'suffix')
        # 6. 生成新ID
        item['id'] = self.generate_id(item['name'])
        return item
    def apply_affix(self, item, affix, affix_type):
        """将词缀效果应用到物品上"""
        # 修改名称
        if affix_type == 'prefix':
            item['name'] = affix['name'] + item['name']
        else:
            item['name'] = item['name'] + affix['name']
        # 合并效果
        for prop, value in affix.get('modifiers', {}).items():
            if prop in item:
                if isinstance(item[prop], (int, float)):
                    item[prop] += value
                elif isinstance(item[prop], dict):
                    # 递归合并
                    pass
            else:
                item[prop] = value
        return item
    def scale_damage(self, damage_str, mult):
        # 解析 "XdY+Z" 格式并调整
        # 简单实现：增加骰子数量
        import re
        m = re.match(r'(\d+)d(\d+)(?:\+(\d+))?', damage_str)
        if m:
            dice, sides, bonus = m.groups()
            dice = int(dice)
            sides = int(sides)
            bonus = int(bonus) if bonus else 0
            new_dice = max(1, int(dice * mult))
            return f"{new_dice}d{sides}+{bonus}"
        return damage_str
```
---
五、随机生成器的注册与调用
在游戏初始化时，将生成器注册到 EXTERNAL_DATA 中，与超级库并列。
```python
def load_external_data():
    data = {}
    # 加载现有超级库（静态数据）
    data['items'] = load_json('items.json')
    data['enemies'] = load_json('enemies.json')
    # ...
    # 初始化随机生成器
    from generators import ItemRandomGenerator, MonsterRandomGenerator
    data['item_generator'] = ItemRandomGenerator(
        data['items'],          # 以静态物品为模板
        load_json('affixes.json')   # 词缀库
    )
    data['monster_generator'] = MonsterRandomGenerator(
        data['enemies'],
        load_json('monster_parts.json')
    )
    return data
```
使用时：
```python
# 生成一个随机稀有物品
new_item = EXTERNAL_DATA['item_generator'].generate(forced_rarity='rare')
# 加入玩家背包
state.inventory.append(new_item)
# 生成一个变异怪物
base_monster = EXTERNAL_DATA['enemies']['wolf']
mutant = EXTERNAL_DATA['monster_generator'].mutate(base_monster, mutation_power=1.5)
```
---
六、生成系统的扩展性
· 添加新类型的生成器：只需继承 RandomGenerator，实现 generate 方法，并定义自己的模板池和变异规则。
· 动态模板池：生成器可以混合使用静态模板和已生成的动态实例作为新模板，实现递归生成。
