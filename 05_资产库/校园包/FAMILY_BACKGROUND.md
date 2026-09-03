### 11.2 家庭背景（FAMILY_BACKGROUND）

**功能**：角色初始化时按画像 asset_match 抽取 1 条家庭背景（或 asset_get 指定），实例化写入 characters.family。

**字段**：
- family_type：家庭类型（核心家庭/单亲/隔代/寄养/重组…）
- members：成员列表 [{role, name, status, relation}]（role=父亲/母亲/兄弟姐妹/祖辈…；status=在世/离世/分居/远行…）
- economic_status：经济状况 low|middle|upper（影响零花钱、打工、社团经费等小事件）
- home_environment：家庭环境描述（住所/氛围/规矩）
- secrets：家庭秘密（M70 梦境素材 / M34 闲聊线索，现实模式文学化隐写）
- influence_big5：大五基线偏移 dict（初始化时叠加到出厂大五）
- evolution_weights：人格演变权重 dict（EVOLUTION_RULES 各维度速率系数）
- fear_match：恐惧候补来源（与 FEAR_LIBRARY 合并去重）

**联动链**：
1. 初始化：大五基线 += influence_big5（如"严格家教" → conscientiousness+8 / neuroticism+4）；
2. 人格演变：M21 按 evolution_weights 调整各维度演变速率（家庭底色越深，对应维度越难改变）；
3. 恐惧匹配：M22 fear_matching 合并 family.fear_match（童年经历 → 恐惧模板）；
4. 梦境素材：M70 引用 secrets 生成意象（不点破）；
5. 小事件锚点：经济状况/家庭环境 → M30 小事件（打工/家访/家长会）。

**示例**（FB001）：
```python
"FB001": {
  "id": "FB001", "name": "严格家教·书店世家",
  "family_type": "核心家庭", "economic_status": "middle",
  "members": [{"role": "父亲", "name": "佐藤 明", "status": "在世", "relation": "书店店主"},
              {"role": "母亲", "name": "佐藤 美咲", "status": "在世", "relation": "全职主妇"},
              {"role": "妹妹", "name": "佐藤 芽衣", "status": "在世", "relation": "国中生"}],
  "home_environment": "旧式町屋，一楼是自家书店，二楼住人；晚饭必须全家一起，宵禁九点",
  "secrets": ["父亲年轻时组过乐队，书架暗格锁着旧吉他谱", "母亲娘家是没落和果子老铺"],
  "influence_big5": {"extraversion": -5, "agreeableness": 3, "conscientiousness": 8, "neuroticism": 4, "openness": 2},
  "evolution_weights": {"conscientiousness": 0.6, "neuroticism": 0.8, "openness": 1.3},
  "fear_match": ["让家人失望", "深夜不归"], "tags": ["书店", "严格", "书香", "家庭温情"]
}
```

