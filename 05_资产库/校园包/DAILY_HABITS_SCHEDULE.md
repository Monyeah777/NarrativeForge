### 11.3 日常习惯 × 日程（DAILY_HABITS / SCHEDULE）

**DAILY_HABITS（日常习惯）**：
- time_slot：morning|class|lunch|after_school|evening
- frequency：always（每回合激活）/ often(0.6) / sometimes(0.3) / rare(0.1)——每回合掷骰决定该习惯是否"发生"
- location：习惯发生的地点（须为 LOCATIONS 已有地点）
- interaction_chance：同地点同时间块时的互动概率（0-1）
- personality_link：{big5, impulse}——习惯与大五/冲动的双向印证（习惯固化人格，人格解释习惯）
- event_hooks：习惯可挂载的 M30 小事件锚点列表

**SCHEDULE（日程）**：
- day_type：weekday|weekend|holiday|exam|event
- time_blocks：时间块列表 [{slot, activity, location, participants}]（slot 对应早/午/课后/晚）
- season_variation：季节差异 {spring, summer, autumn, winter}（覆盖或补充时间块）

**联动链**：
1. 认知量速：M23 检测玩家与角色同地点同时间块 → 互动频率提升 → INTERACTION_DEPTH 认知量/速度加速；
2. 缘分触发：M33 扫描两人日程交集（常同时间块同地点 → 缘分概率提升）；
3. 事件锚点：M30 小事件在习惯/日程地点自然挂载（"他每天课后在天台练吉他" → 路过天台的偶遇）；
4. 遗憾源：玩家"知道他总在那里却一直没去" → 沉淀 ghost 条目（M65 结算，见 11.5）；
5. 位置刷新：M10 推进日期时按 day_type 套用 SCHEDULE → 更新 NPC position。

**示例**（DH003 / SC001）：
```python
"DH003": {
  "id": "DH003", "name": "课后天台练吉他",
  "time_slot": "after_school", "frequency": "often", "location": "L012_天台",
  "interaction_chance": 0.5,
  "personality_link": {"big5": {"openness": 5}, "impulse": {"escape": 2}},
  "event_hooks": ["HE001_天台旧琴盒", "E_偶遇合奏"], "tags": ["音乐", "天台", "独处"]
}
"SC001": {
  "id": "SC001", "name": "平日课程表",
  "day_type": "weekday",
  "time_blocks": [
    {"slot": "morning", "activity": "早自习+第一二节课", "location": "L003_教学楼", "participants": ["全员"]},
    {"slot": "lunch", "activity": "食堂/便当", "location": "L005_食堂", "participants": ["随机3人"]},
    {"slot": "after_school", "activity": "社团/自由活动", "location": "L012_天台等", "participants": ["按习惯"]}
  ],
  "season_variation": {"summer": [{"slot": "after_school", "activity": "泳池开放", "location": "L014_泳池"}], "winter": []},
  "tags": ["平日", "课程", "标准"]
}
```

