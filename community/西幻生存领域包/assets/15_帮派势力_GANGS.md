## M15.帮派与势力
> **数据源**：gangs 帮派系统——Gang类定义（`/tmp/extract_test.txt` 行7028-7056，核心版）、GangActionType枚举（行6968-6973）、沙盒Gang类（行11036-11055，含secrets帮派秘密）、帮派核心方法（行7181-7212 `_update_gangs`/`_trigger_gang_event`；行7324-7358 `join_gang`/`gang_conflict`；沙盒行11533-11565 `check_gang_conflicts`/`trigger_gang_war`）、gangs JSON数据（行32532-32860，13帮派）。
> **依赖**：@M09经济与贸易（帮派走私/敲诈/贸易活动与资源体系）、@M14阵营与声望（关系/情报/声望接口全面复用）。
> **状态**：✅ 已填充 v1.0
### M15.1 帮派总表与数据模型

游戏世界共 **13个帮派**，按地域与行业分为六类：北境帮派、港口帮派、草原帮派、矿脉帮派、王冠城帮派、行业/海上帮派。完整总表如下：
| ID | 名称 | 实力 | 声望 | 领土（@M07地点） | 领袖 | 主要活动 |
|----|------|------|------|------------------|------|----------|
| north_wolf_gang | 北境狼帮 | 25 | 30 | north_village, winterhold | gray_wolf_leader | 走私、敲诈、偷猎 |
| bear_clan_gang | 熊氏帮派 | 35 | 40 | icewind_city, winterhold | brown_bear_leader | 走私、敲诈、偷猎、私酒酿造 |
| azureport_dockers | 码头兄弟会 | 55 | 55 | azureport, silverbay | docker_boss_01 | 码头装卸、货物转运、走私保护、雇佣护卫 |
| thieves_guild_azure | 海蓝暗影 | 45 | 30 | azureport, silverbay | shadowmaster_azure | 偷窃、勒索、情报贩卖、暗杀 |
| horsetown_nomads | 草原游骑 | 50 | 65 | horsetown, east_steppe | nomad_chief_01 | 牧马、商队护卫、草原巡逻、马匹交易 |
| bandit_gang_east | 草原豺狼 | 40 | 15 | east_steppe | bandit_leader_east | 抢劫商队、偷马、绑架勒索 |
| ironforge_miners | 矿工兄弟会 | 60 | 75 | ironforge, copperhill | miner_elder_01 | 采矿、矿石贸易、矿工权益维护 |
| goblin_gang | 地精掠夺者 | 30 | 10 | west_mines | goblin_boss_01 | 偷窃矿石、袭击矿工、设陷阱抢劫 |
| crowncity_nobles | 贵族俱乐部 | 70 | 60 | crowncity | duke_everett | 政治联姻、权力斗争、商业投资、宴会社交 |
| crowncity_underdogs | 下水道之鼠 | 35 | 15 | crowncity_underbelly | rat_king | 乞讨、小偷小摸、捡垃圾、情报收集 |
| vinetown_vintners | 酿酒师协会 | 45 | 70 | vinetown | master_vintner_01 | 酿酒、葡萄种植、酒类贸易 |
| pirate_gang | 血帆海盗 | 65 | 20 | pirate_isles, sea_of_oblivion | captain_redbeard | 劫掠商船、走私、贩卖奴隶、海盗聚会 |
| merfolk_traders | 人鱼商团 | 40 | 50 | coral_city, pearl_reef | merchant_prince_merfolk | 珍珠贸易、珊瑚采集、海底商品交易 |

**帮派分类说明**：
- **北境帮派**：北境狼帮（小型，走私偷猎，与熊氏合作）、熊氏帮派（冰风城地头蛇，控制部分走私路线），二者皆与冰风城守卫icewind_defenders敌对。
- **港口帮派**：码头兄弟会（控制货物进出与走私，与商人行会关系密切，与血帆海盗/海蓝暗影冲突）、海蓝暗影（盗贼公会海蓝分支，与码头兄弟会有地盘冲突）。
- **草原帮派**：草原游骑（游牧部落，商队护卫，与草原豺狼死敌）、草原豺狼（强盗团伙，抢劫商队偷马）。
- **矿脉帮派**：矿工兄弟会（控制主要矿脉，与矮人dwarf_faction关系密切）、地精掠夺者（偷窃矿石袭击矿工，与矿工兄弟会死敌）。
- **王冠城帮派**：贵族俱乐部（掌握城市财富与政治权力，与盗贼公会矛盾）、下水道之鼠（底层帮派，依附盗贼公会，与贵族俱乐部/城卫敌对）。
- **行业/海上帮派**：酿酒师协会（控制葡萄酒产业，与商人行会密切合作）、血帆海盗（劫掠商船，与码头兄弟会/商人行会敌对，与人鱼商团有合作）、人鱼商团（海底商团，珍珠珊瑚贸易）。

**Gang数据模型字段**（gangs JSON，核心版）：
| 字段 | 类型 | 说明 |
|------|------|------|
| id / name | string | 帮派唯一ID与显示名 |
| territory | string[] | 地盘（地点ID列表，对应@M07） |
| power | int 0-100 | 综合实力 |
| leadership | string[] | 领导层（NPC ID列表，通常1人首领） |
| members | string[] | 成员（NPC ID列表，玩家加入后含"player"） |
| allies | {gang_id: int} | 盟友 {帮派ID: 关系强度0-100} |
| enemies | {gang_id: int} | 敌人 {帮派ID: 敌意值0-100} |
| resources | {gold, weapons, influence, ...} | 资源（金币/武器/影响力+帮派特有资源如horses/ships/pearls/wine/iron_ore/land） |
| activities | string[] | 当前活动（走私/敲诈/护卫/采矿等） |
| reputation | int 0-100 | 帮派声望 |
| headquarters | string | 总部地点ID |
| description | string | 简介（含势力定位与恩怨关系） |
**沙盒版扩展字段**：`leader_id`（首领NPC ID，单独字段）、`strength`（实力，默认30，等价power）、`secrets`（帮派秘密列表，可被玩家发现，联动@M14.4情报）。
### M15.2 帮派内部结构
**帮派由五层结构构成**：
| 层级 | 字段 | 说明 |
|------|------|------|
| 领导层 | leadership / leader_id | 首领与核心决策者（NPC ID），决定帮派战略方向与敌对/结盟 |
| 成员 | members | 帮派战斗与行动主力（NPC ID列表），含玩家（"player"） |
| 地盘 | territory | 控制的地点ID列表，地盘数量与实力/收入直接挂钩 |
| 资源 | resources | gold金币/weapons武器/influence影响力 + 行业特有资源（horses马匹、ships船只、pearls珍珠、wine酒、iron_ore铁矿石、land土地等） |
| 活动 | activities | 当前进行中的活动类型（决定帮派收入来源与玩家可参与任务） |

**帮派资源与行业对应**：
| 帮派 | 资源构成 | 行业特色 |
|------|----------|----------|
| 北境狼帮 / 熊氏帮派 | gold+weapons+influence | 走私与私酒（@M09贸易链路） |
| 码头兄弟会 | gold 2000, weapons 50, influence 60 | 码头装卸与货物转运 |
| 海蓝暗影 | gold 1500, weapons 20, influence 40 | 情报贩卖与暗杀（@M14.4情报源） |
| 草原游骑 | horses 30, weapons 40, influence 50 | 马匹贸易与商队护卫 |
| 矿工兄弟会 | iron_ore 500, weapons 80, influence 70 | 矿脉开采与矿石贸易 |
| 贵族俱乐部 | gold 10000, influence 90, land 5 | 政治与商业投资（最高金币） |
| 酿酒师协会 | gold 2500, wine 200, influence 55 | 葡萄酒产业 |
| 血帆海盗 | gold 5000, ships 3, weapons 100, influence 40 | 劫掠与走私 |
| 人鱼商团 | gold 4000, pearls 100, coral 50, influence 35 | 珍珠与珊瑚贸易 |

**帮派规模分级**（按成员数）：小规模1-4人（北境狼帮）、中等5-7人（熊氏/海蓝暗影/草原豺狼/下水道之鼠/人鱼商团等）、大规模8+人（码头兄弟会/矿工兄弟会/血帆海盗）。规模越大，火并胜负时波及面越广。
### M15.3 帮派行动类型
**帮派行动使用 GangActionType 枚举**（5类）：
| 行动类型 | 键 | 说明 | 典型触发场景 |
|----------|----|------|------------|
| 争夺地盘 | TERRITORY | 对敌对帮派发动地盘争夺，胜者夺取败者一个领地 | 帮派冲突gang_conflict/火并trigger_gang_war |
| 敲诈勒索 | RACKET | 对商贩/居民/商队收取保护费，获取gold | 帮派日常活动（北境狼帮/草原豺狼/海蓝暗影） |
| 走私 | SMUGGLE | 绕开官方监管运输违禁品，获取gold与influence | 北境/港口帮派的核心收入（@M09贸易） |
| 火并 | FIGHT | 帮派间正面冲突，决定地盘与声望归属 | 敌对帮派之间（check_gang_conflicts 30%触发） |
| 结盟 | ALLIANCE | 与他方缔结盟友关系（allies映射），共同对抗强敌 | 狼帮-熊氏、码头兄弟会-商人行会、海盗-人鱼商团 |

**行动效果规则**：
- TERRITORY/FIGHT：胜者获得地盘（territory append/remove）、实力增减（火并胜者strength+3，败者-5）、关系置为WAR 80、广播确凿情报。
- RACKET/SMUGGLE：获得gold与influence资源增长，同时提高帮派reputation或被官方通缉（reputation下降）。
- ALLIANCE：allies关系强度30-70不等（数据中狼帮-熊氏30、码头兄弟会-商人行会60、贵族俱乐部-商人行会60/光明教团50、矿工兄弟会-矮人70）。
### M15.4 帮派冲突与地盘争夺
**每日更新入口**：`_update_gangs(current_day)` 每日对所有帮派遍历，每个帮派5%概率触发帮派事件（核心版行7181-7212，沙盒版对应行11533-11565）。
**帮派事件逻辑（5步）**：
1. 遍历13帮派，每帮派5%概率触发事件；
2. 检查帮派 enemies 是否非空（无敌人则pass）；
3. 随机选取一个敌对帮派作为冲突对象；
4. 双方实力（power/strength）对比，强者获胜，夺取败者一个地盘（territory转移）；
5. 通过 `_broadcast_intelligence` 广播 CONFIRMED 情报“X从Y手中夺取了Z”，相关势力30%概率得知，弱者方pass无反应。
**帮派冲突判定表**（gang_conflict，核心版行7324-7358）：
| 实力差（power差） | 判定结果 | 后果 |
|------------------|----------|------|
| 差 > 20 | 强者胜 | 强者夺取败者一个地盘，关系置WAR 80 |
| 差 < -20 | 反方胜 | 反方夺取强者一个地盘，关系置WAR 80 |
| \|差\| ≤ 20 | 平局 | 双方互不退让，关系仍置WAR 80 |
**沙盒火并机制**（check_gang_conflicts/trigger_gang_war，沙盒行11533-11565）：
- 每日随机抽取一对敌对帮派，30%概率触发火并；
- trigger_gang_war：胜者夺取败者一个地盘并 strength+3，败者 strength-5；
- 火并结果产生确凿情报，广播至情报网络（@M14.4情报模板）。
**地盘争夺对玩家影响**：玩家所在地盘帮派更替会影响——安全度（敌对帮派地盘内NPC敌意上升）、贸易税率（帮派RACKET强度变化影响@M09交易成本）、任务来源（帮派任务随控制者变化刷新@M12）。
### M15.5 玩家与帮派互动
**加入帮派（join_gang，核心版行7324-7335）**：
| 步骤 | 条件/操作 | 结果 |
|------|----------|------|
| 1 | 玩家对目标帮派 favor ≥ 30 | 可发起加入申请 |
| 2 | 帮派成员列表追加 "player" | 玩家成为帮派成员 |
| 3 | favor + 10 | 玩家与该帮派关系加深 |
| 4 | 重复加入 | 返回“已是成员” |
**帮派任务参与奖励**：玩家参与帮派活动（走私SMUGGLE、护卫商队、地盘防守）可获得 gold、帮派 favor、帮派声望（reputation）提升；高风险活动（火并FIGHT）额外获得武器/装备奖励（@M12任务结算）。
**退出与背叛规则**：
- 主动退出：失去帮派保护与成员特权，favor清零；
- 背叛帮派（如向敌对帮派泄露秘密）：帮派关系置为WAR 80，该帮派及盟友（allies）对玩家敌视，可能触发追杀事件（@M13战斗）。
**声望联动**：帮派reputation影响玩家在该帮派控制区域的社会评价——高声望帮派成员获得NPC尊敬与交易折扣；低声望帮派（如草原豺狼reputation 15、地精掠夺者reputation 10）成员被官方与正派势力敌视（@M14阵营判定）。
### M15.6 帮派秘密与情报
**沙盒secrets字段**（沙盒Gang类，行11036-11055）：帮派秘密列表（如走私路线、隐藏金库、内奸身份），玩家可通过侦查、情报购买、任务奖励等方式发现。
**情报联动场景表（4项）**：
| 场景 | 触发 | 情报结果 | 影响 |
|------|------|----------|------|
| 帮派火并/冲突 | 每日火并或gang_conflict | 确凿情报“X从Y手中夺取了Z”广播 | 相关势力30%概率调整行动（@M14） |
| 走私活动 | 帮派SMUGGLE行动 | 走私路线情报 | 玩家可举报（获官方奖励）或利用（低价货源@M09） |
| 帮派秘密 | secrets被玩家发现 | 秘密情报（CONFIRMED） | 可交易（换取gold/favor）或威胁（勒索帮派） |
| 帮派-势力关系变化 | set_faction_relation | 关系变更情报 | 情报网络更新，NPC阵营态度随之变化 |
**情报影响**：CONFIRMED级别情报直接影响NPC决策与玩家任务选择；秘密情报持有者可在帮派间斡旋获利（@M14.4情报模板、@M18事件触发）。
### M15.7 接口注册与核心联动
**接口键映射表（9项）**：
| 接口键 | 对应实现 | 用途 |
|--------|----------|------|
| gangs_data | 13帮派JSON（行32532-32860） | 帮派基础数据查询 |
| gang_action | _trigger_gang_event | 帮派日常事件触发 |
| gang_conflict | gang_conflict() | 帮派冲突判定与地盘转移 |
| gang_war | trigger_gang_war/check_gang_conflicts | 火并机制 |
| join_gang | join_gang() | 玩家加入帮派 |
| gang_secrets | Gang.secrets | 帮派秘密存取 |
| gang_intel | _broadcast_intelligence | 帮派情报广播 |
| faction_relation | set_faction_relation | 帮派-势力关系写入 |
| daily_update | _update_gangs | 每日帮派推进入口 |
**外部数据需求（4项）**：①13帮派完整数据（ID/名称/领土/实力/领导层/成员/盟友/敌人/资源/活动/声望）；②帮派关系映射（allies/enemies）；③帮派资源数据（gold/weapons/influence/行业资源）；④帮派活动与秘密数据。
**每日推进时序（3步）**：
1. `_update_gangs(current_day)` 每日入口触发（5%概率帮派事件）；
2. 事件/火并判定（gang_conflict或check_gang_conflicts）；
3. 结果广播与关系更新（_broadcast_intelligence + set_faction_relation）。
**核心联动（6大模块）**：@M07（帮派成员NPC日程与行为）、@M09（走私/敲诈影响贸易与经济）、@M12（帮派任务生成与结算）、@M13（火并战斗结算）、@M14（帮派-势力阵营与声望联动）、@M18（帮派事件写入事件系统）。
**扩展点**：[EXT-资产] 新增帮派/势力事件——新增帮派数据按M15.4机制注册（_trigger_gang_event扩展、check_gang_conflicts判定规则）；新增帮派秘密追加至secrets列表并关联@M14.4情报模板。
