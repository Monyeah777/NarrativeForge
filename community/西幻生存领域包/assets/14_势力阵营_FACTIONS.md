## M14.阵营与声望

> **数据源**：factions 势力系统——关系系统核心代码（`/tmp/extract_test.txt` 行6940-7420，RelationshipManager类）、factions JSON数据（行27795-28450，15个势力）、plots势力阴谋模板（行28230-28310）。
> **依赖**：@M01基础属性（玩家声望挂载）、@M12对话与NPC交互（交互产生声望变化）。
> **状态**：✅ 已填充 v1.0

### M14.1 势力总表与数据模型

游戏世界共 **15个势力**，按类型分为五类：旧神教会（7个，对应七宗罪）、光明教团、魔王军、中立/地下/商业/学术组织、北境部落。完整总表如下：

| ID | 名称 | 类型 | 核心定位 | 领袖 | 总部 |
|----|------|------|----------|------|------|
| arrogance_church | 圣辉庭 | 旧神教会 | 傲慢·上流社会财富政治收集碎片 | archbishop_marcus | crowncity_cathedral |
| greed_church | 金匮会 | 旧神教会 | 贪婪·商人银行家秘密收集珍宝 | master_banker_ignatius | azureport_exchange |
| lust_church | 绯红教团 | 旧神教会 | 色欲·诱惑与情报网络 | mistress_carmilla | — |
| envy_church | 暗镜会 | 旧神教会 | 嫉妒·渗透与颠覆 | — | — |
| gluttony_church | 饕餮圣殿 | 旧神教会 | 暴食·资源与享乐 | — | — |
| wrath_church | 血怒教 | 旧神教会 | 愤怒·战争与破坏 | — | — |
| sloth_church | 静默修道会 | 旧神教会 | 懒惰·隐匿与蛰伏 | — | — |
| light_order | 光明教团 | 光明教团 | 秩序与正义，对抗七旧神教会 | — | — |
| demon_lord_army | 魔王军 | 魔王军 | 魔族势力，与光明教团战争状态 | — | — |
| adventurers_guild | 冒险者公会 | 中立组织 | 冒险者枢纽，玩家主要互动方 | — | — |
| thieves_guild | 盗贼公会 | 地下组织 | 地下犯罪网络，与商人行会敌对 | — | — |
| merchant_guild | 商人行会 | 商业组织 | 贸易垄断，与盗贼公会敌对 | — | — |
| magic_academy | 苍穹学院 | 学术组织 | 魔法研究与人才培养 | — | — |
| wolf_clan | 狼氏部落 | 北境部落 | 北境游猎，与熊氏部落敌对 | — | — |
| bear_clan | 熊氏部落 | 北境部落 | 北境狩猎，与狼氏部落敌对 | — | — |

**Faction数据模型字段**（factions JSON）：

| 字段 | 类型 | 说明 |
|------|------|------|
| id / name | string | 势力唯一ID与显示名 |
| type | string | 势力类型（旧神教会/光明教团/魔王军/中立组织/地下组织/商业组织/学术组织/北境部落） |
| leader_id / members | string[] | 领袖NPC ID与成员NPC ID列表 |
| headquarters | string | 总部地点ID（对应@M07地点） |
| territory | string[] | 势力控制的领土地点ID列表 |
| resources | {gold, manpower, influence} | 资源：金币/人力/影响力 |
| strength | int 0-100 | 综合实力 |
| reputation | int 0-100 | 势力声望 |
| secrecy | int 0-100 | 保密程度（越高情报越难获取） |
| relations | {faction_id: {type, strength}} | 与其他势力的关系 |
| plots | Plot[] | 正在执行的阴谋计划 |
| known_intelligence | string[] | 已掌握的情报ID |
| active | bool | 是否活跃 |
| description | string | 简介（含碎片收集方式） |

**势力关系初始化示例**（初始relations）：圣辉庭与金匮会中立50、与血怒教敌对80、与光明教团紧张40；血怒教与光明教团敌对90；魔王军与光明教团战争100；盗贼公会与商人行会敌对70；狼氏/熊氏部落互相敌对80。

### M14.2 声望等级体系

**玩家对NPC/势力的关系使用 RelationEntry 四维模型**（均0-100）：

| 维度 | 键 | 说明 |
|------|----|----|
| 好感度 | favor | 喜恶程度，默认50 |
| 信任度 | trust | 相信程度，默认50 |
| 恐惧度 | fear | 害怕程度，默认0 |
| 尊敬度 | respect | 敬重程度，默认50 |

**综合关系值**：`overall = (favor + trust + respect - fear) / 3`，用于判定NPC对玩家的整体态度与事件解锁阈值。

**声望等级映射**（势力reputation字段 0-100 → 玩家可见等级）：

| 区间 | 等级 | 解锁效果 |
|------|------|----------|
| 0-19 | 声名狼藉 | 多数势力拒绝交易、任务；悬赏可能上升 |
| 20-39 | 默默无闻 | 普通任务可接，交易加价5% |
| 40-59 | 小有名气 | 标准交易与任务；可加入帮派（favor≥30） |
| 60-79 | 声名鹊起 | 高级任务开放；部分势力主动示好 |
| 80-100 | 传奇之名 | 势力领袖接见、专属剧情与绝密情报开放 |

**玩家对势力关系**（player_faction_relations）：每个势力一份RelationEntry，通过modify_player_faction(faction_id, rel_type, delta)修改，交互/任务/间谍成功/帮派加入等事件触发变化。


### M14.3 阵营关系类型与动态变化

**势力间关系**使用 FactionRelationEntry（type + strength 0-100）描述：

| 关系类型 | 键 | 说明 |
|----------|----|----|
| 同盟 | alliance | 军事/政治同盟，共同行动 |
| 贸易伙伴 | trade | 贸易往来，资源互通 |
| 中立 | neutral | 无特殊往来（默认） |
| 紧张 | tense | 摩擦上升，接近敌对 |
| 敌对 | hostile | 公开对抗，任务/交易受限 |
| 战争 | war | 全面战争，互相攻击 |

**关系强度**（strength 0-100）：数值越大关系越稳固/越深；由 get_faction_relation(a,b) 惰性获取（不存在时默认中立50）、set_faction_relation 显式设置、modify_faction_strength(a,b,delta) 增减（钳制0-100）。

**每日动态更新**（daily_update，@M11时间系统每日末尾调用）：

| 机制 | 规则 |
|------|------|
| NPC/玩家关系衰减 | 超过3天未互动后，favor每日衰减0.5，trust衰减0.25（relation_decay_rate×超出天数） |
| 势力关系随机波动 | 每个势力关系对10%概率随机波动±3 |
| 帮派活动检查 | 每个帮派5%概率触发事件（实力对比：强者夺取弱者随机地盘并广播情报；弱者可能失败） |
| 玩家对势力衰减 | 玩家与势力超过3天无交互，同样按关系衰减规则处理 |

**玩家与势力关系**：modify_player_faction(faction_id, rel_type, delta) 修改玩家对势力的RelationEntry四维；触发场景包括任务完成（+favor/+respect）、对抗行为（-favor/+fear）、间谍失败暴露（-10）、帮派加入（+10 favor）等。

### M14.4 情报系统

**情报等级**（IntelligenceLevel）：

| 等级 | 键 | 说明 |
|------|----|------|
| 传闻 | rumor | 不确定，可能为假 |
| 线索 | clue | 部分证实 |
| 确凿 | confirmed | 完全证实 |
| 绝密 | top_secret | 极少数人知道，需特殊途径获取 |

**情报生命周期**：

| 操作 | 接口 | 规则 |
|------|------|------|
| 创建 | create_intelligence(content, level, source_faction, expire_days=30) | 生成唯一ID info_xxx；默认30天后过期 |
| 分享 | share_intelligence(info_id, faction_id?, player?) | 分享给指定势力或玩家 |
| 确认 | confirm_intelligence(info_id, faction_id?, player?) | 提升等级：rumor→clue→confirmed（不能提升到绝密） |
| 获取 | get_player_intel(level_filter?) | 返回玩家已知情报列表 |
| 广播 | _broadcast_intelligence(content, level, source, expire_day) | 相关势力30%概率得知 |

**势力known_intelligence**：各势力JSON中的已掌握情报ID列表；情报可通过间谍行动、NPC对话（@M12）、阴谋结果获得。

### M14.5 间谍行动

**行动类型**（SpyActionType）七类：

| 类型 | 键 | 说明 |
|------|----|------|
| 渗透 | infiltrate | 安插卧底，获取内部情报 |
| 窃取 | steal | 盗取资源/情报/物品 |
| 破坏 | sabotage | 破坏设施/补给线 |
| 暗杀 | assassinate | 刺杀目标人物 |
| 陷害 | frame | 栽赃嫁祸第三方 |
| 勒索 | blackmail | 利用把柄要挟 |
| 策反 | recruit | 策反敌方成员 |

**成功率规则**（perform_spy_action(action_type, target_faction, agent_npc, player_state)）：

| 因素 | 调整 |
|------|------|
| 基础成功率 | 0.5 |
| 执行者势力与目标关系：敌对 | ×0.7 |
| 执行者势力与目标关系：同盟 | ×1.3 |
| 间谍技能/实力 | 按agent_npc属性调整（读取@M01技能） |
| 目标secrecy | 保密度越高成功率越低 |

**失败惩罚**：行动暴露时，执行者势力与目标势力关系-10，且可能产生负面情报广播。成功时返回 (True, 描述, 获得情报/效果)。

### M14.6 势力阴谋（plots）

**阴谋模板结构**：多阶段计划，逐阶段判定成功。

| 字段 | 类型 | 说明 |
|------|------|------|
| id / name | string | 阴谋ID与名称 |
| description | string | 目标与策略描述 |
| initiator_type | string | 发起者条件（any / any_hostile） |
| target_type | string | 目标类型（faction_leader / faction） |
| duration | int(天) | 总持续时间 |
| stages | Stage[] | 阶段列表：name/description/success_chance/required_intel/required_assets/cost/effects |

**效果类型**（effects）：

| 效果 | 参数 | 说明 |
|------|------|------|
| assassinate | target, chance | 暗杀目标（成功概率） |
| modify_faction_relation | faction_a, faction_b, delta | 修改两势力关系强度 |
| reduce_faction_resource | faction, resource, amount | 削减势力资源 |
| modify_faction_reputation | faction, delta | 修改势力声望 |
| create_intel | content | 生成情报（含{target_faction}/{third_party}占位符） |
| add_spy | faction | 向目标势力安插卧底 |

**内置阴谋模板示例**：

| 模板 | 时长 | 阶段（成功率） | 关键效果 |
|------|------|----------------|----------|
| 暗杀敌对首领 | 14天 | 情报收集0.8 → 派遣刺客0.4 → 善后处理0.7 | assassinate(leader, 0.6)；关系-30/-20；生成嫁祸情报 |
| 散布谣言 | 7天 | 编造谣言0.9 → 收买传播者0.7(金500) → 谣言爆发0.8 | 目标声望-15；生成丑闻情报 |
| 破坏补给线 | 10天 | 侦查补给路线0.8(需intel) → … | 削减目标资源/补给 |

**执行逻辑**：势力按initiator_type条件选择目标后，将plot加入factions JSON的plots数组；每日推进阶段，各阶段按success_chance判定，成功后应用effects，失败则中止并可能暴露。

### M14.7 接口注册与核心联动

**注册接口**（register_relationship_system(external_data) → manager.register_with_core）：

| 接口键 | 绑定 | 说明 |
|--------|------|------|
| relation_manager | RelationshipManager实例 | 管理器总入口 |
| get_npc_relation | get_npc_relation | 获取NPC间关系 |
| modify_npc_relation | modify_npc_relation | 修改NPC间关系 |
| get_npc_to_player | get_npc_to_player_relation | 获取NPC对玩家关系 |
| get_faction_relation | get_faction_relation | 获取势力间关系 |
| modify_faction_strength | modify_faction_strength | 修改势力关系强度 |
| daily_relation_update | daily_update | 每日关系更新（衰减/波动/帮派） |
| create_intelligence | create_intelligence | 创建情报 |
| share_intelligence | share_intelligence | 分享情报 |
| get_player_intel | get_player_intelligence | 获取玩家情报列表 |
| perform_spy | perform_spy_action | 执行间谍行动 |
| join_gang | join_gang | 玩家加入帮派（favor≥30） |
| trigger_gang_conflict | gang_conflict | 帮派冲突（实力差>20判胜负，夺地盘，关系置WAR 80） |

**外部数据需求**（load_external_data注入）：initial_npc_relations（初始NPC关系）、initial_faction_relations（初始势力关系）、gangs（帮派定义，13帮派→@M15）、intel_pool（各势力情报池）、relation_decay_rate（关系衰减速率）、interaction_boost（互动增加量）。

**装载方式**：核心伪代码 load_external_data() 中调用 register_relationship_system(external_data) 完成注入。

**每日推进时序**（联动@M11时间系统 advance_time）：
1. EXTERNAL_DATA["daily_relation_update"](current_day)：关系衰减+波动+帮派活动。
2. 势力plots阶段推进（@M18混沌事件可引用）。
3. 玩家交互/任务/间谍结果调用 modify_player_faction / modify_faction_strength / create_intelligence 等接口落地。

**与相关模块联动**：
- @M01：玩家声望/属性挂载与技能影响间谍成功率。
- @M07：势力headquarters/territory关联地点，进入领地触发关系检查。
- @M12：NPC对话选项按favor/respect解锁，交互产生关系变化。
- @M13：NPC死亡（M13.6）可触发阵营声望变动；NPC成员归属势力参与阴谋。
- @M15：帮派系统复用关系/情报接口，帮派冲突由gang_conflict驱动。

**扩展点 [EXT-资产]**：新增阵营 / 声望条目——按Faction数据模型字段追加至factions JSON（含relations/plots），新增声望等级需同步M14.2映射表与解锁效果；新增阴谋模板按M14.6结构追加至plots库。
