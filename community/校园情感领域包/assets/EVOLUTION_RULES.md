## 5.12 EVOLUTION_RULES 人格演变规则表

> 用途：M60 长期演变（NPC人格随事件累积漂移）、M22 三冲动（出厂值随人格演变重算基线）、M61 关系演变（亲密度影响演变速率）。
> 结构：演变触发器（trigger）/ 演变方向（direction）/ 演变幅度（delta）/ 生效条件（condition）/ 冷却（cooldown）。三冲动出厂值随大五漂移自动重算（见 M22 compute_impulses）。

```python
"EVOLUTION_RULES": {
  "baseline": "大五人格五维 + 三冲动出厂值 为演变锚点；演变只改大五，三冲动由 compute_impulses 按新大五重算，不直接改冲动值。",
  "rules": [
    {"rule_id": "E01", "name": "创伤固化", "trigger": "角色经历 fear_match 命中的恐惧事件（单次 intensity≥70）",
     "direction": "neuroticism +10，extraversion -5", "delta": {"neuroticism": +10, "extraversion": -5},
     "condition": "同源恐惧首次触发；重复触发叠加减半（+5/+2）", "cooldown": "3个事件回合"},
    {"rule_id": "E02", "name": "应激钝化", "trigger": "同一恐惧类型累计触发≥3次且均未逃脱",
     "direction": "该恐惧 intensity_default -15，neuroticism -3", "delta": {"fear_desensitize": -15, "neuroticism": -3},
     "condition": "需累计≥3次同源恐惧", "cooldown": "无"},
    {"rule_id": "E03", "name": "被温柔以待", "trigger": "角色接受他人善意帮助（友好行为事件）",
     "direction": "agreeableness +6，trust 相关情绪权重提升", "delta": {"agreeableness": +6},
     "condition": "善意来源为亲近角色（亲密度≥40）时翻倍（+12）", "cooldown": "2个事件回合"},
    {"rule_id": "E04", "name": "背叛创伤", "trigger": "被信任对象背叛（好感度≥60的角色做出背叛行为）",
     "direction": "agreeableness -12，neuroticism +8，trust 相关情绪权重下降", "delta": {"agreeableness": -12, "neuroticism": +8},
     "condition": "一次性事件；触发后该角色对同类行为敏感度+", "cooldown": "无"},
    {"rule_id": "E05", "name": "社牛化", "trigger": "累计参与≥5次多人社交事件（社团/聚餐/活动）",
     "direction": "extraversion +5，openness +3", "delta": {"extraversion": +5, "openness": +3},
     "condition": "事件中主动发言次数≥3才计1次有效参与", "cooldown": "1个事件回合"},
    {"rule_id": "E06", "name": "独处沉淀", "trigger": "累计≥4次独自行动事件（图书馆/天台独处/放学独自回家）",
     "direction": "introversion 倾向 +4（extraversion -4），conscientiousness +3", "delta": {"extraversion": -4, "conscientiousness": +3},
     "condition": "独处事件需 time_cost≥10 的地点（L004/L008/L024 等）", "cooldown": "1个事件回合"},
    {"rule_id": "E07", "name": "恋爱心动", "trigger": "与心仪对象产生亲密互动（sexual 冲动主导事件且对方好感≥50）",
     "direction": "openness +5，neuroticism -3（安全感上升）", "delta": {"openness": +5, "neuroticism": -3},
     "condition": "若事件结果为拒绝/破裂，则反向（openness -3，neuroticism +5）", "cooldown": "2个事件回合"},
    {"rule_id": "E08", "name": "恶作剧成瘾", "trigger": "mischief 主导行为累计≥5次且均未被惩罚",
     "direction": "conscientiousness -5，openness +4", "delta": {"conscientiousness": -5, "openness": +4},
     "condition": "若被惩罚≥2次，改向：conscientiousness +3（收敛）", "cooldown": "2个事件回合"},
    {"rule_id": "E09", "name": "责任觉醒", "trigger": "担任职务（班长/部长/值日组长）并完成≥3次职责事件",
     "direction": "conscientiousness +8，extraversion +3", "delta": {"conscientiousness": +8, "extraversion": +3},
     "condition": "职责事件失败不计数；失败≥2次触发反向（conscientiousness -5）", "cooldown": "1个事件回合"},
    {"rule_id": "E10", "name": "群体同化", "trigger": "长期与某群体互动（与同群体成员互动占比≥60%，持续5回合）",
     "direction": "向群体平均大五收敛（差值的20%）", "delta": "clamp(群体均值 - 自身值) × 0.2",
     "condition": "群体需≥3人且有共同标签（如运动系/宅系）", "cooldown": "3个事件回合"},
    {"rule_id": "E11", "name": "黑化阈值", "trigger": "累计负面事件（背叛/霸凌/冤枉）≥3次且求助无果",
     "direction": "触发『黑化』状态：neuroticism +15，agreeableness -15，mischief 重算后+",
     "delta": {"neuroticism": +15, "agreeableness": -15},
     "condition": "黑化状态下行为裁决中恶意选项权重×1.3；可通过 E03 善意事件2次解除", "cooldown": "无"},
    {"rule_id": "E12", "name": "梦想校准", "trigger": "经历与梦想相关的重大事件（升学/获奖/被否定梦想）",
     "direction": "openness ±8（成功+，受挫-），conscientiousness +4（行动力沉淀）", "delta": {"openness": 8, "conscientiousness": +4},
     "condition": "方向正负由事件结果决定（成功+8 / 受挫-8）", "cooldown": "3个事件回合"}
  ],
  "process": "M60 每回合扫描全局事件日志 → 命中触发器的规则进入待生效队列 → 检查 condition 与 cooldown → 生效后修改大五 → 通知 M22 重算三冲动出厂值 → 写 m60_evolution_log（{char, rules_hit, big5_before, big5_after, impulses_recalc: true}）",
  "clamp": "演变后大五各维 clamp(0,100)；超出时取边界值并记录『极性偏移』（如 neuroticism=100 时标记为『情绪极不稳定』，供 M80 使用）。"
}
```

---
