## M13 正文（NPC交互系统）

### M13.1 NPC状态机（NPCInstance运行时状态）
> 数据源：NPC系统核心模块代码（行21877-22059），NPCInstance类
**运行时状态结构**（status字典，每NPC实例一份）：
| 状态字段 | 默认值 | 说明 |
|---------|--------|------|
| health | 100 | 健康度（0-100） |
| mood | 50 | 心情（0-100，50为中性） |
| energy | 100 | 精力（0-100，每日自动恢复） |
| location | 模板location | 当前位置（地点ID） |
| destination | None | 移动目标地点 |
| schedule_index | 0 | 日程表循环指针 |
| last_updated | 0 | 最后更新天数 |
**NPC实例字段**：id / template / name / race / occupation / level / hp / max_hp / attributes（属性副本）/ status / schedule（日程表）/ relations（关系表）/ memory（记忆）/ secrets（秘密表，known+data）/ goals（目标）/ inventory（物品）/ is_dead / death_cause / death_day。
**状态迁移**：update_location(new_location, day) → 更新location与last_updated；每日由NPCManager.update_all驱动状态演化（见M13.4）。

### M13.2 好感度与关系系统
**关系结构**：`relations[other_id] = {favor好感, trust信任, fear恐惧, notes备注}`，取值0-100。
**默认值**：新关系 favor=50、trust=50、fear=0（中立起点）。
**修改规则**（modify_relation）：
- 按关系维度增减：`modify_relation(other_id, delta, relation_type="favor")`，relation_type 可为 favor/trust/fear。
- 钳制规则：favor/trust/fear 三值均限制在 0-100 区间（`max(0, min(100, ...))`）。
- 双向性：change_favor 修改玩家视角关系的同时，调用 `npc.modify_relation("player", delta)` 保持NPC侧同步（见M13.7）。
**联动**：
- @M06初始NPC关系矩阵：开局关系按矩阵赋值（老汤姆↔扎克挚友75-80、苏珊↔玛丽姐妹90-95、维克多↔老汤姆警惕55-60、维克多↔扎克冲突30-35）。
- @M12.3好感区间门槛：favor < -20仅greeting / 0-20加general / 20-50加trade / 50-80加rumor / ≥80加quest高级。

### M13.3 NPC记忆系统
**记忆结构**：`memory = [{day, event, importance}]`（天数/事件描述/重要度）。
**容量规则**：最多保留50条，超出时滚动丢弃最旧（`memory[-50:]`）。
**写入接口**：`add_memory(event_description, day, importance=1)`。
**用途**：
- 行为依据：NPC基于重要事件（importance高）调整后续行为与对话。
- 对话背景：与@M12对话模板结合，记忆事件可作为rumor/quest话题素材。
- 关系演化：玩家对NPC的关键行为（帮助/伤害/赠礼）写入记忆，影响后续好感度变动解释。

### M13.4 NPC日程与行为（每日更新流程）
**日程表**（schedule）：循环列表，每项含 location（地点ID）等字段；schedule_index 循环推进（`(idx + 1) % len(schedule)`），NPC按日程在不同地点间移动。
**每日更新**（NPCManager.update_all，跳过死亡NPC）：
1. `_update_npc_schedule`：当前天数 > last_updated 时按日程推进位置（防重复更新）。
2. `_update_npc_status`：energy +5（上限100）；mood 向50回归（>50逐日-1，<50逐日+1）。
3. `_check_npc_goals`：检查目标进度，完成则移除并触发回调。
**地点查询**：`get_npcs_at_location(location_id)` 返回该地点所有存活NPC（用于场景交互时列出在场NPC，联动@M07地点系统）。

### M13.5 NPC目标系统
**目标结构**：`goals = [{progress, ...}]`，progress 0-100。
**完成判定**：每日检查，progress ≥ 100 → 从goals移除 → 触发 `_on_goal_complete(npc, goal, world)` 钩子（默认空实现，可扩展）。
**联动**：
- @M06任务系统：NPC目标可由任务叙事生成/推进（任务完成 → progress增加）。
- @M12 quest对话：玩家接取NPC委托时创建/推进目标。
- **扩展点 [EXT-规则]**：新增NPC交互状态 / 好感权重——可在_on_goal_complete中自定义完成奖励（好感变动、物品、剧情解锁）。
### M13.6 NPC死亡与继承
> 数据源：NPC系统核心模块代码（行21877-22059），NPCManager死亡判定部分 + npc_death_triggers配置（行21844-21876）
**死亡触发器配置**（npc_death_triggers，每日概率基准）：
| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| base_accidental | 0.0002 | 每日意外死亡基础概率 |
| occupation_mult | 职业系数 | 战士1.5/游侠1.3/盗贼1.4/冒险者1.8（高危）/铁匠0.8/商人0.7/学者0.6（低危） |
| age_factor | 年龄系数 | 儿童0.3/少年0.5/青年0.8/中年1.0/老年1.5/耄耋2.0 |
| danger_level_factor | 0.2 | 地点危险度加成（×1+0.2×danger_level） |
| war_factor | 2.0 | 战争期间整体死亡概率翻倍 |
| disease_factor | 1.3 | 疾病爆发期间系数 |
| accident_pool | 意外/疾病/野兽/仇杀/战争/衰老/诅咒/魔法反噬 | 死亡原因随机池 |
**概率计算**（_calculate_death_probability）：base_accidental × 职业系数 × 年龄系数（>60岁×age/30）× 地点危险加成 × 战争系数，上限0.1（钳制）。
**每日判定**（npc_death_check）：遍历所有存活NPC → 按概率掷骰 → 命中则从 accident_pool 随机选死亡原因 → 调用 kill_npc。
**死亡流程**（kill_npc）：置 is_dead=True、记录 death_cause/death_day → _apply_death_consequences → _handle_inheritance。
**继承规则**（_handle_inheritance）：
- 查找继承人（_find_heir，按关系网络，简化版返回None=无继承）。
- 有继承人：死者 inventory 全部转移给继承人；死者对第三方的所有关系好感度按30%折价转移给继承人（`heir.modify_relation(other_id, rel["favor"] * 0.3)`）。
- 无继承人：遗产自然流失（物品消失）。
**联动**：
- @M06关系矩阵：继承人判定优先从挚友/亲族关系（信任/好感≥80）中选取。
- @M11死亡系统：NPC死亡事件可联动玩家死亡处理的叙事链（如NPC葬礼、复仇任务）。
- @M14阵营声望：重要NPC死亡可触发阵营声望变动（扩展点）。
- **扩展点 [EXT-规则]**：自定义继承范围 / 遗嘱 / 遗物剧情——覆写_find_heir与_handle_inheritance。
### M13.7 对话与好感度函数
> 数据源：NPC系统核心模块代码（行22017-22041），generate_dialogue + change_favor
**generate_dialogue(npc, topic, player_state, world)**：
- 取好感：`player_state.relations["NPCs"][npc.id].favor`（缺省50）。
- 取心情：npc.status.mood。
- 选模板：topic 命中 npc.dialogue_templates[topic]；未命中回退到模板的"通用"列表；再兜底 `["..."]`。
- 心情修饰前缀：mood<30 → `（不耐烦地）`；mood>70 → `（热情地）`；否则无前缀。
- 从候选列表中随机返回一条（preface + response）。
**change_favor(npc, player_state, delta, world)**：
- 玩家侧：初始化关系记录（含 last_seen=当前天数）→ favor += delta → 钳制0-100。
- NPC侧同步：`npc.modify_relation("player", delta)` 保持双向一致（不破坏NPC实例独立性）。
**联动**：
- @M12.3好感区间门槛：本函数是对话模板路由的好感度来源（favor决定可选话题层级）。
- @M13.2关系系统：change_favor 是 modify_relation 在玩家视角的封装，双向同步。
- @M13.5目标系统：对话中可触发目标创建（委托）；目标完成回调内调用 change_favor 加好感。
- **扩展点 [EXT-规则]**：好感变动触发事件（如到达阈值解锁剧情/商店折扣）——可在change_favor中追加钩子。
### M13.8 接口注册与核心联动
> 数据源：NPC系统核心模块代码（行22042-22059），register_npc_system
**注册流程**（register_npc_system）：创建 NPCManager → load_all 实例化全部NPC模板 → 将以下7个接口挂载到 EXTERNAL_DATA：
| 接口键 | 绑定对象 | 核心调用点 |
|--------|----------|-----------|
| npc_manager | NPCManager实例 | 全局管理器访问 |
| get_npc | manager.get_npc | @M04世界初始化按需取NPC |
| update_npcs | manager.update_all | 每日推进（advance_time） |
| npc_death_check | manager.npc_death_check | 每日死亡判定（advance_time末尾） |
| get_npcs_at_location | manager.get_npcs_at_location | @M07地点/场景交互列出在场NPC |
| generate_dialogue | generate_dialogue函数 | @M12对话系统文本生成 |
| change_favor | change_favor函数 | @M12好感度变更（任务奖励/对话选项） |
**装载方式**（load_external_data）：核心伪代码加载 `npc_death_triggers.json` 后调用 register_npc_system(external_data) 完成注入，与@M04外部数据装载流程一致。
**每日推进时序**（联动@M11时间系统 advance_time）：
1. update_npcs(world, day)：日程移动+状态恢复+目标检查。
2. npc_death_check(world, day)：死亡概率判定与继承。
3. get_npcs_at_location 供场景渲染；generate_dialogue/change_favor 供@M12交互使用。
**扩展点 [EXT-规则]**：新增NPC交互状态 / 好感权重——保持7接口签名不变，可在NPCManager子类或包装函数中追加逻辑（如季节心情修正、阵营联动、剧情NPC免死标记）。

---

