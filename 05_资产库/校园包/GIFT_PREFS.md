### 11.4 礼物偏好（GIFT_PREFS）

**字段**：
- gift_items：[{item, interest_level, reaction_mod}]，interest_level 三级：
  - core：强烈喜欢 → 好感 +3~+5，M42 表面反应明显（惊喜/害羞）
  - interest：一般喜欢 → 好感 +1
  - minefield：雷区 → 好感 -3~-5（踩雷也是自然剧情，不惩罚任务）
- occasions：送礼最佳场合（生日/文化祭/圣诞/情人节/安慰时机…）
- source_hint：自然线索（对话/闲聊/日常习惯观察），**不直接展示列表**——玩家自己发现"她喜欢什么"

**联动链**：
1. 好感度：M40 结算礼物反应（含 5.15.3 人格敏感度 / 5.15.5 关系类型分级）；
2. 网购：M53 网购系统可购入礼物 → player.gift_inventory 暂存 → 选时机赠送；
3. 恋爱：M41 进阶中 core 礼物是关系升级的自然推动（但不产生任务承诺，强制感归零）；
4. 日常锚点：source_hint 与 DAILY_HABITS 互证（"她总在便利店买那款草莓牛奶" → 习惯+偏好双线索）。

**示例**（GP002）：
```python
"GP002": {
  "id": "GP002", "name": "藤原同学的礼物偏好",
  "gift_items": [
    {"item": "手作点心", "interest_level": "core", "reaction_mod": 4},
    {"item": "乐队CD（老式）", "interest_level": "core", "reaction_mod": 5},
    {"item": "最新款游戏", "interest_level": "interest", "reaction_mod": 1},
    {"item": "香水", "interest_level": "minefield", "reaction_mod": -4}
  ],
  "occasions": ["生日", "文化祭", "情人节", "她低落时"],
  "source_hint": "常在午休听随身听里的旧乐队；书包挂着自己烤的曲奇包装袋",
  "tags": ["手作", "音乐", "怀旧"]
}
```

