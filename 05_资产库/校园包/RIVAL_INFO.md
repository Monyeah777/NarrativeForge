### 13.2 情敌系统（M43 + RIVAL_INFO）

**激活条件**：
- 玩家与某 NPC 好感度 ≥ 60 且该 NPC 存在暗恋者（rival_info_list 非空，v0.6.2 卷B既有字段）
- 暗恋者档案：admirer_profile（身份/性格/与目标关系/暗恋时长）

**三动作库**（每回 M43.settle_rival 依 competition_intensity 抽取）：
- 接近目标：暗恋者主动接近目标 NPC → 目标好感度流向竞争者（竞争强度↑）
- 论坛发帖：暗恋者在论坛散布与目标亲密的暗示（M52 联动 → 风评波动）
- 制造误会：暗恋者制造"玩家与目标疏远"的误会（M34 闲聊联动 → 目标好感度回落）

**告白成功率修正**：
- 竞争强度 ≥ 阈值时，玩家对目标告白成功率 = 基础值 × rival_factor（rival_factor 默认 0.8，竞争强度越高越低）
- 玩家可反制：澄清误会（M42 文本）/ 送礼挽回（M53 GIFT_PREFS）/ 正面竞争（好感度反超）

**示例**：
- RI001：小林暗恋佐藤（admirer_profile=同班同学/内向/暗恋2年；competition_intensity=中）
- RI002：高桥暗恋佐藤（admirer_profile=学长/外显/暗恋半年；action_library=论坛发帖优先）

