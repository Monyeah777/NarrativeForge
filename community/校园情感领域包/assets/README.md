# 校园包 — 资产索引（28 键）

> 数据源：`校园框架_v0.7_完整合并版.md`（8620 行）
> 版本基准：v0.7.13（含 v0.7.12 冲动-社会关系隔离补丁 / v0.7.13 认知边界强制补丁的机制约束，见 04_模块库 与 01_核心协议）
> 本包文件均为**源文按行区间切片**，未改写；注册中心与 Schema 原文见源文件第 3 章（行 147-341）。

---

## 1. 文件清单与溯源行号

### A. 基础资产（官方区 official_zone，第 5 章 5.1-5.16，源行 502-1711）

| 资产键 | 文件 | 条目规模 | 源行区间 | 主要消费模块 |
|--------|------|----------|----------|--------------|
| ATTR_TEMPLATES | ATTR_TEMPLATES.md | 60 条 | 502-809 | M43 / M22 / M40 |
| FEAR_LIBRARY | FEAR_LIBRARY.md | 9 条 | 810-849 | M22（恐惧驱动） |
| BIG5_INFER | BIG5_INFER.md | 18 行为 + 15 标签 | 850-907 | M21 / M40（剖面推断） |
| EMOTION_WHEEL | EMOTION_WHEEL.md | 8 基础情绪 | 908-952 | M22（三冲动） |
| BEHAVIOR_SIGNALS | BEHAVIOR_SIGNALS.md | 4 倾向 × 3 档 | 953-1000 | M40（行为信号） |
| COGNITIVE_LOAD | COGNITIVE_LOAD.md | 4 级 | 1001-1027 | M23 / M80 |
| LOCATIONS | LOCATIONS.md | 30 条（L001-L099） | 1028-1160 | M55 / M10 / M07 |
| WEATHER_SEASON | WEATHER_SEASON.md | 8 天气 + 4 季节 | 1161-1199 | M08 / M26 / M10 |
| GOSSIP_TOPICS | GOSSIP_TOPICS.md | 100 条 | 1200-1274 | M34 / M59 / M57 |
| FORUM_POSTS | FORUM_POSTS.md | 30 条 | 1275-1385 | M57（论坛） |
| WRITING_STYLE | WRITING_STYLE.md | 8 DNA + 质检三档 | 1386-1440 | M80（输出） |
| EVOLUTION_RULES | EVOLUTION_RULES.md | 12 条 | 1441-1493 | M21（人格演变） |
| REGRET_LIBRARY | REGRET_LIBRARY.md | 6 条 | 1494-1540 | M65（遗憾/幽灵） |
| NAME_LIBRARY | NAME_LIBRARY.md | 20 条（jp/cn） | 1541-1581 | 角色生成池 |
| INTERACTION_DEPTH | INTERACTION_DEPTH.md | 8 类（freq/quality/damage） | 1582-1677 | M40（关系深度） |
| PERSONALITY_LINK | PERSONALITY_LINK.md | 3 组系数 + 3 组参数 | 1678-1711 | M40（破坏结算） |

### B. 扩展资产（v0.7.7-v0.7.9 新增 12 键，第 11-13 章，源行 2475-2885）

| 资产键 | 文件 | 条目规模 | 源行区间 | 引入版本/章节 |
|--------|------|----------|----------|----------------|
| FAMILY_BACKGROUND | FAMILY_BACKGROUND.md | 12（FB001-FB899） | 2494-2530 | v0.7.7 / 11.2 |
| DAILY_HABITS | DAILY_HABITS_SCHEDULE.md | 12（DH001-DH899） | 2531-2574 | v0.7.7 / 11.3 |
| SCHEDULE | DAILY_HABITS_SCHEDULE.md | 10（SC001-SC899） | 2531-2574（同文件 SCHEDULE 段） | v0.7.7 / 11.3 |
| GIFT_PREFS | GIFT_PREFS.md | 10（GP001-GP899） | 2575-2606 | v0.7.7 / 11.4 |
| HIDDEN_EVENTS | HIDDEN_EVENTS.md | 8（HE001-HE899） | 2607-2658 | v0.7.7 / 11.5 |
| SOCIAL_FEED | SOCIAL_FEED.md | 8（SF001-SF899） | 2673-2689 | v0.7.8 / 12.2 |
| PHONE_CALL | PHONE_CALL.md | 8（PC001-PC899） | 2690-2704 | v0.7.8 / 12.3 |
| GROUP_CHAT | GROUP_CHAT.md | 8（GC001-GC899） | 2705-2720 | v0.7.8 / 12.4 |
| RIVAL_INFO | RIVAL_INFO.md | 6（RI001-RI899） | 2796-2814 | v0.7.9 / 13.2 |
| PRESSURE_RULES | PRESSURE_RULES.md | 8（PR001-PR899） | 2815-2836 | v0.7.9 / 13.3 |
| PART_TIME_JOB | PART_TIME_JOB.md | 20（PJ001-PJ899） | 2837-2855 | v0.7.9 / 13.4 |
| WEATHER_MOOD | WEATHER_MOOD.md | 8（WM001-WM899） | 2856-2872 | v0.7.9 / 13.5 |

### C. 附机制文件（非资产实体，供模块联动参考）

| 文件 | 内容 | 源行区间 |
|------|------|----------|
| 附_社交系统触发联动.md | 触发扫描伪代码 + 深度联动矩阵 + 防丢包清单（12.5-12.7） | 2721-2780 |
| 附_生活情敌联动结算.md | 生活与情敌结算防丢包清单（13.6） | 2873-2885 |

---

## 2. ID 前缀与命名空间

- 官方条目：`<前缀>001`-`<前缀>899`；用户自定义：`<前缀>900+`。
- 前缀表：ATTR_TEMPLATES→T / LOCATIONS→L / FAMILY_BACKGROUND→FB / DAILY_HABITS→DH / SCHEDULE→SC / GIFT_PREFS→GP / HIDDEN_EVENTS→HE / SOCIAL_FEED→SF / PHONE_CALL→PC / GROUP_CHAT→GC / RIVAL_INFO→RI / PRESSURE_RULES→PR / PART_TIME_JOB→PJ / WEATHER_MOOD→WM（基础资产其余键的 ID 规则见各文件内实体与源第 3 章）。

## 3. Schema 与字段校验

- 每个资产键的 `required_fields` / `field_types` 定义于源文件第 3 章 3.1.1（行 149-284），`asset_register` 校验失败将拒绝注册。
- 扩展资产键（FAMILY_BACKGROUND 等 12 键）Schema 原文同在第 3 章（v0.7.1 起统一维护）。

## 4. 运行约束（v0.7.12 / v0.7.13 机制补丁）

- **冲动-社会关系隔离**（v0.7.12）：M22 三冲动仅驱动物理位移 / 动作连带 / 视线停留等表层行为；**告白 / 交往 / 约会 / 关系推进等驱动权从冲动层切除**，归还 M40/M41 社会关系系统。本包 EMOTION_WHEEL / ATTR_TEMPLATES 等数据在被冲动层读取时须遵守该边界。
- **认知边界强制**（v0.7.13）：叙事输出必须经 M00→M40 事实管线产出事实快照 → 认知裁剪器按角色裁剪 → AI 仅渲染裁剪包 → 锚点回验。本包数据仅可进入**事实层**，禁止作为全知信息直通渲染层。

## 5. 调用示例

```
asset_get("ATTR_TEMPLATES", "T001")        # 单条人格模板
asset_query("LOCATIONS", {"type": "室内"})  # 室内地点集
asset_match("BIG5_INFER", {"behaviors": [...]})  # 大五剖面推断
asset_roll("GOSSIP_TOPICS", {"mood": "日常"})    # 按 mood 加权抽话题
asset_register("FAMILY_BACKGROUND", {...FB901...})  # 自定义条目
```

---

*28 键 = 第 5 章 16 键 + v0.7.7-v0.7.9 扩展 12 键；DAILY_HABITS 与 SCHEDULE 两键共享一个源小节切片文件（源 11.3 节天然合写），寻址时两键均指向该文件。*