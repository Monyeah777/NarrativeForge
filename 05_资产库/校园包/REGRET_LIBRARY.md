## 5.13 REGRET_LIBRARY 遗憾模板库（6条，v0.7.2）
> 反向系统核心资产：将"玩家未行动/未选择的路径"沉淀为可显形的遗憾模板。
> 每条模板 = 一类"未选择之路"的叙事原型；由 M65 幽灵结算系统按触发条件实例化为 ghost 条目。

### 5.13.1 模板结构（7字段）
| 字段 | 类型 | 说明 |
|---|---|---|
| id | string | 唯一标识（regret_xxx） |
| name | string | 遗憾名（NPC/UI 展示用） |
| trigger_type | array[string] | 可触发的触发器类别（五类） |
| manifest_modes | array[string] | 显形形式（NPC对话/独白/梦境/论坛/行为修正/冲动偏移） |
| text_slots | array[string] | 文本槽位（按 context 填充的模板句，{X}/{Y} 占位） |
| impulse_mod | dict{sexual,mischief,escape} | 显形时对 M22 三冲动的修正系数 |
| weight_default | number(0-1) | 默认显形权重（受 decay_count 衰减） |

### 5.13.2 六类遗憾模板实体
1. **regret_missed_event 错过校园活动**
   - trigger_type: [纪念日, 剧情节点]
   - manifest_modes: [NPC对话暗语, 论坛帖间接提及, 行为修正因子]
   - text_slots: ["那天{X}你没来，{Y}一个人玩到了散场", "公告栏上还贴着{X}的海报，边角已经卷了"]
   - impulse_mod: {sexual:0.9, mischief:0.9, escape:1.0} / weight_default: 0.6
2. **regret_unconfessed 未说出口的心意**
   - trigger_type: [高情绪点, 角色生日]
   - manifest_modes: [内心独白额外段落, 梦境浮现, 冲动偏移]
   - text_slots: ["如果那天你叫住了我……算了，现在说这个也没用", "梦里她站在旧校舍的走廊尽头，还是那天的光线"]
   - impulse_mod: {sexual:1.2, mischief:1.0, escape:0.8} / weight_default: 0.8
3. **regret_no_show 未赴之约**
   - trigger_type: [相似场景复现]
   - manifest_modes: [NPC对话暗语, 内心独白, 行为修正因子]
   - text_slots: ["{X}又在老地方等了一个下午", "长椅上的漆掉了，和你放鸽子那天一样"]
   - impulse_mod: {sexual:0.8, mischief:1.1, escape:1.0} / weight_default: 0.7
4. **regret_silence 沉默未言**
   - trigger_type: [高情绪点, 剧情节点]
   - manifest_modes: [内心独白, NPC对话暗语, 冲动偏移]
   - text_slots: ["那句话你始终没问出口", "{X}替你把后半句说了，语气轻得像叹气"]
   - impulse_mod: {sexual:1.0, mischief:0.8, escape:1.2} / weight_default: 0.5
5. **regret_abandoned_option 放弃的选择支**
   - trigger_type: [相似场景复现, 剧情节点]
   - manifest_modes: [行为修正因子, 内心独白, 论坛帖间接提及]
   - text_slots: ["分支剧情线的存档还在，只是你永远走不到那里了", "如果当初选了另一条路……{X}会是现在这样吗"]
   - impulse_mod: {sexual:1.0, mischief:1.0, escape:1.0} / weight_default: 0.4
6. **regret_unearned_achievement 未解锁的成就**
   - trigger_type: [纪念日, 角色生日, 毕业]
   - manifest_modes: [GAL模式成就空位, 论坛帖间接提及, 冲动偏移]
   - text_slots: ["成就图鉴第{N}格是空的，只有一行灰色小字", "奖杯陈列柜最底层的格子，落灰比别的都厚"]
   - impulse_mod: {sexual:0.9, mischief:1.1, escape:0.9} / weight_default: 0.3
---
