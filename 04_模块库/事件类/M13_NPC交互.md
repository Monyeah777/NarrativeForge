# 模块 M13 · NPC 交互
> 类别：事件｜来源：共享｜挂载点：P30 事件生产（active）｜依赖：M12、M06、M20｜被依赖：M40、M14（随社区包）、事件:M22｜发布：`interaction_update`

```yaml
machine_contract:
  schema: "1"
  id: M13
  name: NPC 交互
  category: 事件
  layer: P30
  inputs: [M12, M06, M20]
  outputs: []
  events:
    publish: [interaction_update]
    subscribe: [quest_state, level_up]
  interfaces: []
```

## 1. 职责
管理 **NPC 运行时状态机、记忆、日程、目标与好感函数**：实例化 NPC 个体，维护其与玩家的好感数值与交互历史，把每次交互结算为 interaction_update 广播给关系/声望/叙事模块。（NPCInstance 状态机 / NPC记忆 / 日程行为 / 目标系统 / 死亡继承 / 好感度函数）。**NPC 个体真相来源**（群体声望归 M14；M14 随社区西幻包）。

## 2. NPC 状态机
```yaml
npc_instance:
  id: # 实例化自资产库 NPC 模板
  state: 身份/位置(M07)/职业(M01)/种族(M02)
  affinity: 玩家好感数值（区间，联动 M40 关系深度模型校准）
  memory: []  # 记忆条目（经 M23 认知边界管理：记得什么/不记得什么）
  schedule: 日程（每日更新，受 通用:M10 tick 驱动）
  goals: []   # 目标（任务 M06 / 生存 / 关系 M40）
  alive: true # 死亡与继承联动 生存:M10 / M19
affinity_function:
  输入: 对话(M12) / 赠礼 / 帮助 / 冲突
  输出: affinity_delta → interaction_update
```

## 3. 事件契约
```yaml
subscribe:
  quest_state: # M06 → 任务改变 NPC 目标与可用对话
  level_up: # M01 → 玩家等级影响 NPC 态度基线
publish:
  interaction_update:
    payload: {npc_id, type, affinity_delta, context, flags[]}
    subscribers: [M40, M14, 事件:M22]
```

## 4. 结算流程
1. 每日/事件驱动 NPC 日程更新（睡觉/工作/移动/待机）。
2. 玩家发起交互 → 经 M12 检索台词、玩家选择生效。
3. 好感函数结算 affinity_delta。
4. 发布 interaction_update：M40 折算关系深度、M14 折算阵营声望贡献、事件:M22 采集叙事素材。

## 5. 违例与边界
- M13 裁决 **NPC 个体**的好感/记忆/目标；恋爱档位归 M40/M41，群体声望归 M14。
- 记忆写入须遵守 M23：玩家不可见的记忆不进入可见域。
- NPC 死亡判定交生存:M10，M13 只执行"死亡后状态清理与继承"。
- 交互产生的文本演出归 M12/M80，M13 不做文学渲染。