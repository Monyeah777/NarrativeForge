### 5.16 PERSONALITY_LINK 人格-破坏联动系数表（v0.7.6）

> 用途：M40 破坏结算（5.15.3）读取——将 M21 维护的 BIG5_INFER 大五剖面（neuroticism/agreeableness）
> 映射为三类破坏行为的敏感度系数；并提供重复破坏累计惩罚、恋爱保底下限、临时角色极浅底线三组参数。
> 接口：`asset_get("PERSONALITY_LINK")` 取参数；M40.apply_damage 按关系类型与人格剖面实时计算。

```python
"PERSONALITY_LINK": {
  "sensitivity": {   # 人格敏感度系数（输入 BIG5 剖面 0-100，输出 0.5~1.5）
    "betrayal": "0.5 + (neuroticism/100)×0.6 + (agreeableness/100)×0.4",
    "harm": "0.5 + (neuroticism/100)×1.0",
    "neglect": "0.5 + (agreeableness/100)×0.5 + (neuroticism/100)×0.5",
    "clamp": "系数 clamp(0.5,1.5)；50 基线分 → ×1.0（与 v0.7.5 原数值完全一致）"
  },
  "repeat_penalty": {
    "formula": "min(1 + 0.5×(n-1), 2.0)",   # n = 同类型累计次数（damage.betrayals/harms/neglects）
    "cap": 2.0,
    "note": "与人格敏感度乘法叠加：实际伤害 = 基准 × sens × repeat"
  },
  "romance_floor": {   # 恋爱保底下限（M41 × M40）
    "on_confirm": 40,      # 关系确认时 floor 提升至 ≥40
    "post_breakup": 20,    # 破裂后 floor 保留 ≥20
    "never_below": 20,     # romance 角色 affinity 永不跌破 20
    "rebuild_turns": 3     # 破裂后连续3回合高质量互动可恢复
  },
  "temp_floor": {   # 临时角色极浅底线（M33 × M40）
    "cap": 10,
    "damage_simplify": "基准 ×0.5（不乘人格敏感度）",
    "rebuild_turns": 2
  }
}
```
---

