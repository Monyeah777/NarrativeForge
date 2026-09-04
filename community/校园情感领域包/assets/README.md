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

> **官方模块对照（v0.5.0 T2.2 补注）**：上表 A 区「主要消费模块」列为**源文切片残留编号**（源文 8620 行内旧模块体系编号，切片未改写，I3），非本仓库模块文件全集。可解析规则：
> - **官方核心模块（04_模块库 实存）**：M00 / 通用:M10 / M06 / M08 / M12 / M13 / M20 / M23 / M24 / M50 / M80 / 事件:M22 —— 表内 M23（COGNITIVE_LOAD）、M08（WEATHER_SEASON）、M80（WRITING_STYLE/COGNITIVE_LOAD）即官方核心件。
> - **本包模块（modules/ 实存，9 件）**：情感:M22 / M40 / M41 / M43 / M55 / M57 / M58 / M59 / M65 —— 表内 M22（情感:M22，FEAR_LIBRARY/EMOTION_WHEEL/ATTR_TEMPLATES）、M40、M43、M55、M57、M59、M65 均直接对应本包模块文件。
> - **源编号残留（无模块文件，仅溯源上下文）**：M07 / M10（未限定前缀）/ M21 / M26 / M34 / M42 / M60 / M62 等 —— 表内 GOSSIP_TOPICS 的 M34、BIG5_INFER/EVOLUTION_RULES 的 M21 即此类；实际消费对象以各模块头 events/core.assets 声明与 02 注册表 §8.1 在册为准。

### B. 扩展资产（v0.7.7-v0.7.9 新增 12 键，第 11-13 章，源行 2475-2885）

| 资产键 | 文件 | 条目规模 | 源行区间 | 引入版本/章节 | 主要消费模块 |
|--------|------|----------|----------|----------------|--------------|
| FAMILY_BACKGROUND | FAMILY_BACKGROUND.md | 12（FB001-FB899） | 2494-2530 | v0.7.7 / 11.2 | — |
| DAILY_HABITS | DAILY_HABITS_SCHEDULE.md | 12（DH001-DH899） | 2531-2574 | v0.7.7 / 11.3 | — |
| SCHEDULE | DAILY_HABITS_SCHEDULE.md | 10（SC001-SC899） | 2531-2574（同文件 SCHEDULE 段） | v0.7.7 / 11.3 | — |
| GIFT_PREFS | GIFT_PREFS.md | 10（GP001-GP899） | 2575-2606 | v0.7.7 / 11.4 | — |
| HIDDEN_EVENTS | HIDDEN_EVENTS.md | 8（HE001-HE899） | 2607-2658 | v0.7.7 / 11.5 | — |
| SOCIAL_FEED | SOCIAL_FEED.md | 8（SF001-SF899） | 2673-2689 | v0.7.8 / 12.2 | M57（core.assets 声明） |
| PHONE_CALL | PHONE_CALL.md | 8（PC001-PC899） | 2690-2704 | v0.7.8 / 12.3 | M58（core.assets 声明） |
| GROUP_CHAT | GROUP_CHAT.md | 8（GC001-GC899） | 2705-2720 | v0.7.8 / 12.4 | M59（core.assets 声明） |
| RIVAL_INFO | RIVAL_INFO.md | 6（RI001-RI899） | 2796-2814 | v0.7.9 / 13.2 | — |
| PRESSURE_RULES | PRESSURE_RULES.md | 8（PR001-PR899） | 2815-2836 | v0.7.9 / 13.3 | — |
| PART_TIME_JOB | PART_TIME_JOB.md | 20（PJ001-PJ899） | 2837-2855 | v0.7.9 / 13.4 | — |
| WEATHER_MOOD | WEATHER_MOOD.md | 8（WM001-WM899） | 2856-2872 | v0.7.9 / 13.5 | — |

> **B 表消费列补注（v0.5.0 T5 补）**：「—」= 本包 9 件模块字面零引用（含正文 prose 与 core.assets 两级 grep 均无命中）——属"资产在册、消费方待扩展或经 P 层/官方核心侧调度"状态，非孤儿资产；若后续版本新增消费模块，以模块头 core.assets 声明为准回填本列。

### C. 附机制文件（非资产实体，供模块联动参考）

| 文件 | 内容 | 源行区间 | 联动参考模块 |
|------|------|----------|--------------|
| 附_社交系统触发联动.md | 触发扫描伪代码 + 深度联动矩阵 + 防丢包清单（12.5-12.7） | 2721-2780 | M57 / M58 / M59（§12.5 社交结算段同段依序 scan_feeds / scan_calls / scan_group_chats） |
| 附_生活情敌联动结算.md | 生活与情敌结算防丢包清单（13.6） | 2873-2885 | —（本包模块零字面引用；供 P 层生活/情敌结算联动参考） |

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

## 6. 反向索引（模块 → 消费资产键，v0.5.0 T5 补注）

本包 9 件在册模块（02 联动注册表 §8.1：情感:M22/M40/M41/M43/M55/M57/M58/M59/M65）对资产键的消费关系。依据三级标注：**①core.assets 声明级**（模块头 yaml 协议段显式声明，权威）；**②正文 prose 引用级**（模块正文直接引用键名/资产语义，无显式声明）；**③资产侧标注级**（A/B 表「主要消费模块」列由资产侧推断，模块正文无键名字面命中）。

| 模块 | 消费资产键 | 依据 |
|------|-----------|------|
| M57 朋友圈动态 | SOCIAL_FEED / FORUM_POSTS（core.assets 声明）；GOSSIP_TOPICS / WRITING_STYLE（正文联动）；附_社交系统触发联动（§12.5 scan_feeds） | ①+② |
| M58 电话通讯 | PHONE_CALL（core.assets 声明）；附_社交系统触发联动（§12.5 scan_calls） | ① |
| M59 群聊系统 | GROUP_CHAT / GOSSIP_TOPICS（core.assets 声明）；附_社交系统触发联动（§12.5 scan_group_chats） | ① |
| M40 关系深度 | INTERACTION_DEPTH（核心模型，正文 §1/§2）；BIG5_INFER / BEHAVIOR_SIGNALS / PERSONALITY_LINK（剖面推断/行为信号/破坏结算） | ②/③ |
| M43 情敌系统 | ATTR_TEMPLATES（情敌生成取样） | ② |
| M55 匿名情书 | LOCATIONS（投递通道取样：鞋柜/书桌/信箱） | ② |
| M65 幽灵遗憾 | REGRET_LIBRARY（遗憾系统基线） | ② |
| M22 三冲动驱动 | FEAR_LIBRARY / EMOTION_WHEEL / ATTR_TEMPLATES（冲动区数据，受 v0.7.12 隔离约束）；INTERACTION_DEPTH（§7 违例与边界提及） | ③ |
| M41 恋爱进阶 | —（无直接资产键引用，数据流经 M40 关系深度模型桥接） | — |

> 反向索引差异说明（v0.5.0 T5）：
> - **B 表 9 键零消费**：FAMILY_BACKGROUND / DAILY_HABITS / SCHEDULE / GIFT_PREFS / HIDDEN_EVENTS / RIVAL_INFO / PRESSURE_RULES / PART_TIME_JOB / WEATHER_MOOD 及附_生活情敌联动结算，本包 9 模块两级 grep 均无字面命中——资产在册、消费方待扩展或经 P 层/官方核心侧调度（P50 社交结算段仅消费 M57/M58/M59 对应键）；非孤儿。
> - **M22 标注差异**：A 表 FEAR_LIBRARY / EMOTION_WHEEL / ATTR_TEMPLATES 行"M22（恐惧驱动/三冲动）"为资产侧推断（③级），模块正文无 asset_* 显式调用；冲动层读表须遵守 v0.7.12 冲动-社会关系隔离（数据仅供表层行为驱动，告白/交往/约会等关系推进权归 M40/M41）。
> - **M41 桥接**：不直接消费资产键，其恋爱进阶逻辑依赖 M40 关系深度（INTERACTION_DEPTH 族）间接读取，故不计入资产侧消费列。

---

*28 键 = 第 5 章 16 键 + v0.7.7-v0.7.9 扩展 12 键；DAILY_HABITS 与 SCHEDULE 两键共享一个源小节切片文件（源 11.3 节天然合写），寻址时两键均指向该文件。*