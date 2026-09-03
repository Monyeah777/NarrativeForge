### 11.5 隐藏事件（HIDDEN_EVENTS）—— 自然触发状态机

**硬约束（不强制·不任务感五条落实）**：
1. 不进 active_quests 任务容器——无任务列表、无进度条、无完成度 UI；
2. 无强制推进——错过即错过（允许 missed 态），不产生"未完成任务"的负罪感；
3. 无提示轰炸——线索只以自然方式埋放（对话/日记/习惯/论坛帖），玩家可看可不看；
4. 触发靠"恰好撞见"——trigger_condition 多为 时间+地点+状态 交集，不注册强制事件队列；
5. 现实模式零元语言——禁止出现"隐藏事件/未解锁/支线"等词汇，一律文学化呈现。

**状态机**：`latent → revealed → in_progress → completed | missed`
- latent：未触发，仅存在于 HIDDEN_EVENTS 资产库；
- revealed：触发条件满足且线索被玩家观察到 → 写入 events.hidden_events；
- in_progress：玩家正在经历（clue_trail 逐阶段推进，下一阶段仍靠"恰好撞见"触发）；
- completed：结局达成（写入 characters.hidden_event_state / player.hidden_event_log）；
- missed：触发窗口关闭（毕业/转学/关系破裂/错过时机）→ 若 ghost_link 非空 → 沉淀 ghost.he_pool。

**联动链（反向系统闭环）**：
1. missed 的隐藏事件按 ghost_link 映射入 ghost.he_pool（如 HE002"毕业前没问出口的事" → 遗憾：未说出口的心意），由 M65 统一结算——隐藏事件的"错过"成为反向系统的"遗憾"，双向闭合；
2. revealed 后由 M30 按 clue_trail 阶段自然挂载后续线索事件（不注册强制队列，靠玩家行为触发下一阶段）；
3. 存档：characters.hidden_event_state / events.hidden_events / player.hidden_event_log 随存档持久化（旧档缺失 → 全部默认 latent/空，零影响）；
4. 与 active_quests 的区分：任务系统=跨回合张力容器（有发起者/目标/阶段）；隐藏事件=世界自然生长（无线索追踪、无完成承诺、无失败惩罚）。

**触发扫描（每回合，M30 事件结算后）**：
```
for he in HIDDEN_EVENTS:
  if he.id in events.hidden_events: continue        # 已 reveal 或进行中
  if match(he.trigger_condition, state):            # 时间+地点+状态交集
    if he.requires 全部满足:
      events.hidden_events[he.id] = {"state": "revealed", "revealed_at": turn, "clue_progress": 1}
      # 以自然方式呈现第一条线索（不提示"新事件"）
```

**示例**（HE001 天台旧琴盒）：
```python
"HE001": {
  "id": "HE001", "name": "天台旧琴盒",
  "trigger_condition": {"type": "time+location+flag",
    "params": {"time_slot": "after_school", "location": "L012_天台", "flag": "dh003_active"}},
  "clue_trail": [
    {"stage": 1, "clue": "天台角落的琴盒积着灰，锁扣却是新的", "reveal": "琴盒有主人"},
    {"stage": 2, "clue": "他课间反复看手机里一张旧乐队合照", "reveal": "乐队解散的真相"},
    {"stage": 3, "clue": "文化祭节目单上没有乐队，只有独奏", "reveal": "他其实想合奏"}
  ],
  "requires": ["relationship.c001.affinity >= 40"],
  "effects": {"affinity": 8, "impulse": {"escape": -3}, "memory": "天台旧琴盒"},
  "ghost_link": "HE001_missed",
  "natural_only": true, "tags": ["隐藏", "音乐", "c001"]
}
```

---

