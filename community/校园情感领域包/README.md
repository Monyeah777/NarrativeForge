# 校园情感领域包（community 领域包 · 独占情感类）
> 定位：**社区领域包**，独占「情感」类（01 §6 R2 / 02 §8.1）。在官方核心 13 件之上装配题材内容，经本包自带 **P02 管线**装载（R3 装配契约）。
> 协议声明（v0.7.0）：包根 `protocol.yaml`（01 §6.1 Schema）为**机读真相**，本 README 为**人读速览**，双源一致（check14 ⑥）；登记三要件见 02 §8.3。
> 结构：modules/（9 题材模块）｜assets/（29 资产文件，索引见 assets/README.md）｜pipelines/P02_校园情感流管线.md
> 依赖边界（R1）：只依赖官方核心层（M00 / 通用:M10 / M23 / M24 / M50 / M80 / 事件:M22 / M06 / M12 / M13 / M20 / M08），**不跨包依赖**西幻生存领域包。

## 1. 包速览
| 项 | 值 |
| --- | --- |
| 管线 | **P02** 校园情感流（九层线性回卷，装配自官方 P00 通用骨架） |
| 题材模块（本包自带） | 9：情感:M22 三冲动驱动 / M40 关系深度 / M41 恋爱进阶 / M43 情敌系统 / M55 匿名情书 / M57 朋友圈动态 / M58 电话通讯 / M59 群聊系统 / M65 幽灵遗憾 |
| 官方核心配合件 | 12：M00 / 通用:M10 / M08 / M23 / 事件:M22 / M06 / M12 / M13 / M20 / M24 / M50 / M80 |
| 总装配 | **21 模块**（含核心；重号限定：情感:M22 ≠ 事件:M22） |
| 资产 | 29 文件（28 键 + 附机制 2；官方区 16 键 + v0.7.7-v0.7.9 扩展 12 键） |
| 主轴 | 关系驱动：人格画像 → 日常事件 → 三冲动 → 关系进阶 |
| 时间制 | 校园作息（节 / 课间 / 放学 / 夜） |
| 输出风格 | 短段落 + 白描/诗化交替 + 极简对话（写作 DNA，见 assets/WRITING_STYLE.md） |
| 死亡规则 | 无死亡线；遗憾显形（幽灵） |
| 存档键 | relationships / active_quests / ghost_data |

## 2. 模块装载清单（按层，21 = 核心 12 + 题材 9）
> 与 pipelines/P02_校园情感流管线.md 的 layers（default 列）严格一致。

| 层 | 挂载（default） | 模块职责 | 归属 |
| --- | --- | --- | --- |
| P00 数据基座 | M00 | 数据槽结构/存档装载（含 relationships/active_quests/ghost_data） | 核心 |
| P10 世界推进 | 通用:M10、M08 | 校园作息节拍 + 季节天气 | 核心 |
| P20 角色状态 | M23、情感:M22 | 认知裁剪 + 三冲动基线（NPC 用；主角豁免） | 核心 + 本包 |
| P30 事件生产 | 事件:M22、M06、M13、M12 | 日常事件流 + 任务 + 隐藏事件状态机 | 核心 |
| P40 关系决策 | 情感:M22、M40、M41、M43、M55 | 三冲动裁决 → 关系深度 → 恋爱进阶/情敌/情书 | 本包 |
| P50 交互执行 | M12、M13、M57、M58、M59 | 对话执行 + 互动结算（频率→认知、质量→下限线）+ 社交流结算（朋友圈/电话/群聊，v0.5.0 补建） | 核心 + 本包 |
| P60 长期演变 | M40、M65 | 关系网演化 + 遗憾沉淀/幽灵冷却 + 人格演变 | 本包 |
| P70 叙事素材 | M20、M24 | 世界知识库 + 写作 DNA/组合校验 | 核心 |
| P80 输出呈现 | M80 | 现实/GAL 双模式渲染（DNA 质检门） | 核心 |
| 全局 | M50 | 主循环调度（读注册表） | 核心 |

## 3. 资产包挂载（29 文件）
- **官方区 16 键**（第 5 章 5.1-5.16）：ATTR_TEMPLATES（60 条）/ FEAR_LIBRARY（9）/ BIG5_INFER（18 行为 + 15 标签）/ EMOTION_WHEEL（8 情绪）/ BEHAVIOR_SIGNALS（4×3 档）/ COGNITIVE_LOAD（4 级）/ LOCATIONS（30 条）/ WEATHER_SEASON / GOSSIP_TOPICS / FORUM_POSTS / WRITING_STYLE（写作 DNA）/ EVOLUTION_RULES / REGRET_LIBRARY / NAME_LIBRARY / INTERACTION_DEPTH / PERSONALITY_LINK。
- **扩展区 12 键**（v0.7.7-9，第 11-13 章）：FAMILY_BACKGROUND / DAILY_HABITS+SCHEDULE（合文件）/ GIFT_PREFS / HIDDEN_EVENTS / SOCIAL_FEED / PHONE_CALL / GROUP_CHAT / RIVAL_INFO / PRESSURE_RULES / PART_TIME_JOB / WEATHER_MOOD。
- **附机制 2 文件**：附_社交系统触发联动、附_生活情敌联动结算。
> 完整清单、溯源行号、ID 前缀与 Schema 见 assets/README.md。
调用示例：asset_get('ATTR_TEMPLATES','T001') 取人格模板；asset_roll('GOSSIP_TOPICS') 抽课间话题；asset_match('BIG5_INFER', profile) 推 NPC 剖面。
## 4. 默认状态与回合节拍
- 默认开局：高中二年级主角槽 + 空关系网 + 0 遗憾；人格模板先经 asset_get 装载。
- 四拍节拍：**上课节**（少互动，可观察）→ **课间**（闲聊/论坛/偶遇）→ **放学**（深度互动窗口）→ **夜**（电话/聊天/遗憾显形窗口）。
- 每拍一回合；互动后必查 INTERACTION_DEPTH（频率/质量/破坏三效应，M40 §3）。
## 5. 运行约束（红线）
- **v0.7.12 冲动-社会关系隔离**：三冲动仅驱动 NPC 物理位移/动作连带/视线停留，**禁止**告白/交往/约会/关系推进；关系推进权归 M40/M41。
- **v0.7.13 认知边界**：叙事须过四层管线（M00 → M40 事实 → 快照 → M23 裁剪 → 渲染 → 锚点回验），见 M23 与官方 06 §4。
- **数据隔离**：存档键 relationships / active_quests / ghost_data 仅本包流程可读写；与西幻包存档键（attributes+vitals 等）**不可互载**，切换预设须开新档。
- **混装拦截**：西幻资产键混入本包流程触发 L3 资产可达校验失败——拒绝开跑。
## 6. SillyTavern 装载指引（三步）
1. **系统提示/角色卡**：把 01_核心协议 → 02_联动注册表（§6 顺序）→ 06_Agent执行协议 → 本 README §2 装载清单，按序写入系统提示；角色卡按 §4 默认状态装载。
2. **世界信息（Lorebook）**：将 assets/ 键按「键名→关键词」导入（ATTR_TEMPLATES / LOCATIONS / GOSSIP_TOPICS / FORUM_POSTS…），命中即注入裁剪后素材，勿整体注入。
3. **正则与扩展**：挂隐藏域/系统数值剥离正则（防泄漏）；骰子/事件判定可由扩展接 asset_roll(seed)。
> 最小系统提示骨架见官方 07_官方核心出厂与社区预设导航.md §4（协议引导，两包通用）。
## 7. 包级验收清单
| # | 验收项 | 判定标准 |
| --- | --- | --- |
| 1 | 目录结构完整 | modules/ 9 模块 + assets/ 29 文件（含 assets/README.md）+ pipelines/P02 + 本 README |
| 2 | 资产溯源一致 | 29 文件行数与 assets/README.md 溯源表一致 |
| 3 | 模块-资产引用可寻址 | 本包模块引用资产键（ATTR_TEMPLATES / LOCATIONS / GOSSIP_TOPICS 等）经五接口可寻址 |
| 4 | 重号 ID 全限定 | 情感:M22（≠事件:M22）、生存:M10（≠通用:M10）类别前缀限定书写 |
| 5 | v0.7.12/13 红线落地 | 冲动隔离与认知边界约束在本 README §5、情感:M22、M40 三处一致 |
| 6 | 入口可导航 | 根 README → community/README.md 索引 → 本包 README 可访问 |
> 执行方式：与文件实况对照终验（行数/锚点以终端 grep 复核为准）。
