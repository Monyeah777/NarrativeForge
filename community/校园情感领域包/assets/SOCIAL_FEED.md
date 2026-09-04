### 12.2 朋友圈动态流（M57 + SOCIAL_FEED）

**生成规则**：
- 触发时机：P50 层 M22.advance_quests 之后（M57.scan_feeds）
- 生成条件：NPC 按自身状态（mood/stress/location/habit_slot）+ 事件状态（近期事件/隐藏事件线索）+ 与玩家好感度（affinity_gate）综合判定
- 内容来源：content_templates（日常/心情/事件感想/求助/线索埋放五类）
- 线索埋放：HIDDEN_EVENTS 的 clue_trail 可经动态流自然埋放（v0.7.7 联动）

**互动规则**：
- 玩家点赞/评论 → M40 好感度双向（点赞 +1~3，评论视内容 ±）
- NPC 可回复（reactions.reply），回复文本走 M42 表面反应生成
- 动态可作为新事件触发点（trigger_event → M30 事件队列）

**示例**：
- SF001：佐藤发动态"文化祭排练到九点，腿已经不是自己的了"（npc_state.mood=疲惫，affinity_gate≥20）
- SF002：小林转发幽灵话题帖（事件状态=幽灵传闻发酵期，线索埋放 HE001）

