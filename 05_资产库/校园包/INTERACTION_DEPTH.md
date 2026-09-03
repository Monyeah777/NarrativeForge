## 5.15 INTERACTION_DEPTH NPC互动深度规则库（v0.7.5）
> 用途：将「互动」拆成三个正交维度，由两个既有模块分管——
> **频率 → 认知（M23 主角认知管理：认知的“量”与“速度”）**
> **质量 → 下限线（M40 好感度计算：关系的“下限”，疏远不归零）**
> **破坏 → 击穿（M40 好感度计算：突破下限线，可清零/负数）**
> 核心原则：频率决定认知多快、多深；质量决定关系最低能掉到哪；破坏决定下限线是否失效。

### 5.15.1 频率 → 认知（M23 侧：量与速度）
```
认知量（只增不减，疏远不倒退）：
  meet_count += 1      # 每次相遇（同地点/事件共处）
  talk_turns += 1      # 每完成一个对话回合
认知层级 cognition_level（按 meet_count 累计升级）：
  0 陌生（0次） / 1 眼熟（1-2次） / 2 认识（3-5次）
  3 熟识（6-10次） / 4 深交（11-20次） / 5 知己（21次+）
认知速度（高频加速，低频不倒退）：
  3 回合内相遇 ≥2 次 → memory_depth 累积 ×1.5（“速度快”）
  长期不见（≥10 回合）→ 层级冻结不降级，memory_depth 停止增长（“量不变，速度停”）
记忆深度 memory_depth（0-1）= min(1.0, meet_count×0.3 + talk_turns×0.7 归一化)
认知效果：
  层级越高 → M40 互动质量结算的基础加成越高（level ×0.02 depth 保底）
  memory_depth 高 → 关键时刻触发概率 +（NPC 更“记得”你）
```

### 5.15.2 质量 → 下限线（M40 侧：关系下限 floor）
```
深度分 depth_score 累积（每回合结算，封顶 1.0）：
  普通对话 +0.02
  触及兴趣/共同话题 +0.05
  触及核心面（梦想/恐惧/创伤）+0.15 → core_touched = true
  见过脆弱面（流泪/崩溃/秘密）+0.20 → vuln_seen = true
  关键时刻出现（NPC 困境/重要节点）+0.25 → key_moments += 1
关系下限线 floor（质量决定，疏远不跌破）：
  floor = round(depth_score × 100 × 0.6)，封顶 60
  关键时刻加成：floor += 10 × key_moments，封顶 +50
疏远衰减：
  连续 5 回合未互动 → affinity -3/回合（仅好感度衰减）
  铁律：affinity ≥ floor 永不跌破 —— 即使后来疏远，关系不会完全回到原点
```

### 5.15.3 破坏 → 击穿下限线（M40 侧：破坏结算，v0.7.6：人格敏感度 × 重复惩罚）
```
破坏行为（回合内触发立即结算）：
  背叛 betrayal：affinity -40/次；floor_breached = true；floor ×0.3（击穿）
  伤害 harm：affinity -25/次
  漠视 neglect（关键时刻缺席/无视）：affinity -15/次
人格敏感度系数（M21×M40 深度联动，v0.7.6，系数表见 5.16 PERSONALITY_LINK）：
   sens_betrayal = 0.5 + (neuroticism/100)×0.6 + (agreeableness/100)×0.4   # 0.5~1.5（焦虑敏感者被背叛更痛）
   sens_harm     = 0.5 + (neuroticism/100)×1.0                              # 0.5~1.5（高神经质受伤更重）
   sens_neglect  = 0.5 + (agreeableness/100)×0.5 + (neuroticism/100)×0.5    # 0.5~1.5（友善者被漠视更痛）
   取值：该 NPC 的 BIG5_INFER 当前剖面（M21 维护）；50 基线分 → 系数 ×1.0（与 v0.7.5 原数值完全一致）
重复破坏累计惩罚（与人格联动一体，v0.7.6）：
   同类型第 n 次破坏（n = damage.betrayals / harms / neglects 计数）：
   实际伤害 = 基准伤害 × 人格敏感度 × repeat_multiplier
   repeat_multiplier = min(1 + 0.5×(n-1), 2.0)   # 第1次×1.0，第2次×1.5，第3次×2.0 封顶
   示例：焦虑敏感+友善利他（sens=1.5）背叛第3次 = -40×1.5×2.0 = -120（击穿后仍重创）
affinity 下限 -100（可负，不留情面）
floor 击穿后重建：连续 5 回合高质量互动（depth_score 累积 ≥0.5）→ floor 恢复为原 floor×0.5
damage_log 记录：{type, turn, delta, sens, repeat}（破坏类型/回合/幅度/人格敏感度/累计次数）
显示模式联动：现实模式对玩家隐藏 floor/depth 数值（仅文学化暗示）；GAL 模式显示 floor 标签（如「底线·牢固」）
```

### 5.15.4 relationships 结构化升级（存档侧，v0.7.5）
```python
"relationships": {
  "c001": {
    "relationship_type": "normal",               # normal主线/常规 | temp临时角色 | romance恋爱角色（v0.7.6）
    "affinity": 72,                              # 当前好感度（-100~100，可负）
    "cognition": {"meet_count": 12, "talk_turns": 34, "level": 3, "memory_depth": 0.62},
    "depth": {"depth_score": 0.45, "core_touched": false, "vuln_seen": true, "key_moments": 1, "floor": 30},
    "damage": {"betrayals": 0, "harms": 1, "neglects": 2, "floor_breached": false, "log": []}
  }
}
```
> 旧档兼容：relationships 为 int（如 {"c001": 50}）→ 读取时自动升级为对象
> （affinity=原值，relationship_type=normal，cognition/depth/damage 默认初始化，floor=0）

### 5.15.5 适用范围与关系类型分级（v0.7.6）
> 本规则库适用于所有 NPC 关系，但按关系类型分级生效。关系类型由 relationships.relationship_type 标记
> （M33 缘分系统登记 temp，M41 恋爱进阶系统登记 romance，其余默认 normal）。

| 关系类型 | 登记方 | floor 规则 | 破坏结算 | 重建成本 |
|---|---|---|---|---|
| normal 主线/常规 | M40 默认 | 全规则（5.15.2 公式） | 全规则（5.15.3 人格敏感度×重复惩罚） | 连续5回合高质量互动（depth_score≥0.5） |
| temp 临时角色 | M33 缘分系统（一次性相遇/路人） | floor 上限 10（极浅底线） | 基准值×0.5 简化（不乘人格敏感度）——关系太浅不值得深算 | 连续2回合高质量互动即可恢复 |
| romance 恋爱角色 | M41 恋爱进阶（已确认/曾经确认） | ★恋爱必须有下限：确认时 floor≥40；破裂后 floor≥20 | 全规则 + 恋爱保底（见下） | 破裂后连续3回合高质量互动 → floor 恢复破裂时原值（可复合） |

★ 恋爱保底下限（v0.7.6 重点，M41 × M40）：
- 关系确认时：floor 立即提升至 max(现有 floor, 40)（恋爱保底线）
- 恋爱破裂（分手）后：floor 保留为 max(破裂时 floor×0.5, 20)（破裂仍有底线）
- 铁律：romance 角色的 affinity 永不跌破 20 —— 前任即使决裂，也回不到陌生人的位置
- 依据：现实中关系破裂不代表关系消失；恋爱关系一旦建立，即使破裂也不能完全归零（"关系韧性"的最高规格保障）

适用范围说明：临时角色极少发生破坏行为（现实中很少对陌生人做破坏行为）——就算发生也按极浅规则合理结算；
恋爱关系必须有保底下限，是 5.15 规则库对"关系韧性"的最高规格保障。

