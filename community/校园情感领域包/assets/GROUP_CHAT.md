### 12.4 群聊系统（M59 + GROUP_CHAT）

**消息生成**：
- 触发时机：P50 层 M58 之后（M59.scan_group_chats）
- 生成条件：群按 active_condition（时间段/事件flag/成员状态）激活；消息从 message_pool 抽取
- 素材来源：GOSSIP_TOPICS（M34）作消息素材池；SCHEDULE 定活跃时段

**参与规则**：
- 玩家参与（发言/接话）→ M40 好感度增减 + 素材收集
- 群聊可作为事件触发点（trigger_event）
- 冷场/无视 → 沉淀 ghost 素材（M65）

**示例**：
- GC001：班级群"文化祭筹备群"（active_condition=文化祭期间，消息含筹备/八卦/求助）
- GC002：幽灵话题匿名群（素材=GOSSIP_TOPICS 幽灵传闻，可触发隐藏事件线索）

