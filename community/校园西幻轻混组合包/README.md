# 校园西幻轻混组合包（community 组合包 · 轻混类）
> 定位：**社区组合包**（v0.8.1 完整战例落盘，C6），独占「轻混」类（01 §6 R2 / 02 §8.4 组合登记）。在官方核心 12 件之上**叠加装配**两源包题材流——校园（情感表达通道）与西幻（生产制造事件）——经本包自带 **P04 管线**装载（R3 装配契约）。本包为**组合装配样板**：不搬移源包模块本体，只做 references 协议级事件订阅与 asset_readonly 只读借阅。
> 协议声明（v0.8.1）：包根 `protocol.yaml`（01 §6.1 Schema，schema_version "2"，references 两条目跨包引用校园 M55 / 西幻 M17）为**机读真相**，本 README 为**人读速览**，双源一致（check14 ⑥）；组合登记三要件见 02 §8.4，登记判定四规则见 02 §8.4 注释。
> 结构：modules/（2 题材模块 M91/M92，M91-M99 社区预留段在册 2 件）｜assets/（**0 资产文件**，asset_readonly 只读借阅源包资产，不复制）｜pipelines/P04_轻混装配流管线.md
> 依赖边界（R1）：只依赖官方核心层（M00 / 通用:M10 / M08 / M23 / 事件:M22 / M06 / M12 / M13 / M20 / M24 / M50 / M80）+ 两源包 references 引用模块（校园 M55 / 西幻 M17）；**不搬移**任何源包模块入本包 default/available 槽。

## 1. 包速览
| 项 | 值 |
| --- | --- |
| 管线 | **P04** 轻混装配流（九层线性回卷，装配自官方 P00 通用骨架） |
| 题材模块（本包自带） | 2：M91 异界身份桥（P40 行为决策位） / M92 轻混装配执行（P50 交互执行位） |
| 官方核心配合件 | 12：M00 / 通用:M10 / M08 / M23 / 事件:M22 / M06 / M12 / M13 / M20 / M24 / M50 / M80 |
| 总装配 | **14 模块**（核心 12 + 本包自带 2；references 源模块不计数） |
| references 引用 | 2：校园情感领域包:M55（匿名情书链，asset_readonly）/ 西幻生存领域包:M17（生产制造，asset_readonly） |
| 资产 | **0 文件**（不自建资产；asset_readonly 借阅源包资产键，不复制不占位） |
| 主轴 | 轻混装配：源包事件（confession_event / production_output）→ M91 身份秘密权衡 → M92 跨语境匿名馈赠 |
| 时间制 | 沿用源包（校园作息 / 西幻历法；本包不叠加独立时间制） |
| 输出风格 | 叠加「匿名馈赠」呈现面：校园匿名化、不见生产链（去来源化） |
| 死亡规则 | 沿用源包（校园无死亡线 / 西幻生存判定）；本包不引入独立死亡线 |
| 存档键 | 复用源包（校园 relationships / 西幻 attributes+vitals 等）；本包不自建数据槽 |

## 2. 模块装载清单（按层，14 = 核心 12 + 自带 2）
> 与 pipelines/P04_轻混装配流管线.md 的 layers（default 列）严格一致。

| 层 | 挂载（default） | 模块职责 | 归属 |
| --- | --- | --- | --- |
| P00 数据基座 | M00 | 数据槽结构/存档装载（复用源包存档键） | 核心 |
| P10 世界推进 | 通用:M10、M08 | 节拍推进沿用源包（校园作息 / 西幻历法+天气季节） | 核心 |
| P20 角色状态 | M23、情感:M22 | 认知裁剪 + 三冲动基线（源包承载；轻混身份秘密为叠加观察面） | 核心 |
| P30 事件生产 | 事件:M22、M06、M13、M12 | 源包事件流入料口：confession_event（M55）/ production_output（M17） | 核心 |
| P40 行为决策 | **M91** | 异界身份桥：订阅 relationship_change / confession_event / npc_action，做「情感表达 × 身份秘密」权衡，发布 campus_gift_intent | 本包 |
| P50 交互执行 | **M92** | 轻混装配执行：订阅 production_output（西幻 M17）+ campus_gift_intent（M91），跨语境再包装为 campus_anonymous_gift | 本包 |
| P60 长期演变 | M40、M65 | 轻混关系演变沿用源包（校园遗憾沉淀 / 西幻世界演变），不重复结算 | 核心 + 源包 |
| P70 叙事素材 | M20、M24 | 世界知识库 + 写作 DNA/组合校验（源包资产经 asset_readonly 借阅） | 核心 |
| P80 输出呈现 | M80 | 官方核心输出生成器承载；叠加「匿名馈赠」呈现面 | 核心 |
| 全局 | M50 | 主循环调度（读注册表） | 核心 |

## 3. 资产包挂载（0 文件）
- 本包 **不自建资产**（assets.count = 0）；题材所需资产经 **asset_readonly 借阅**（02 §8.4 登记判定四规则）自源包按需读取：
  - 校园侧：WRITING_STYLE（写作 DNA）/ GIFT_PREFS（馈赠偏好）/ LOCATIONS（场景）等键，源键名直读。
  - 西幻侧：PRODUCTION_RULES（生产规则，M17 依赖）等键，源键名直读。
- 借阅不复制：本包 modules/ 与 assets/ 均无源资产副本；卸载本包不影响源包资产完整性。
> 调用示例：asset_get('GIFT_PREFS', 键) 取校园馈赠偏好；asset_get('PRODUCTION_RULES', 键) 取西幻生产规则——均经 references 协议级通道（asset_readonly true）。
## 4. 默认状态与回合节拍
- 默认开局：源包预设正常装载（校园高一生/西幻求生者按各自 README §4），组合包在其上叠加「异界身份秘密」观察面（M91 消费，不覆盖源包角色状态）。
- 回合节拍沿用源包管线（P02 校园四拍 / P03 西幻历法）；本包 P04 与源包管线同节拍并行推进（P80→P00 主循环回卷条件注明）。
- 每回合 P40/P50 两驻留位检查：源包事件入料 → M91 权衡 → campus_gift_intent → M92 装配 → campus_anonymous_gift 落输出。
## 5. 运行约束（红线）
- **只叠加、不搬移**：M55/M17 本体驻源包 default；组合包经 references 订阅其事件、asset_readonly 借阅其资产——**禁止**将源包模块复制入本包 modules/ 或写入本包 default/available 槽。
- **契约闭合**：M92 subscribe（production_output）覆盖 M17 publish，check16-A ③ pub⊆nsub 无越界；M91 publish（campus_gift_intent）为组合包内部事件，不要求源包反向订阅。
- **同层 default 无交集**（check15 ③）：本包 P40=[M91] ∩ 校园 P40=∅、P50=[M92] ∩ 西幻 P50=∅——两源包可独立运行，本包可叠加装配；卸载本包不影响源包。
- **编号段红线**（R2）：本包模块限 M91/M92（M91-M99 社区预留段）；不得引入官方核心未列模块或源包编号入 default/available。
- **数据隔离**：本包不自建存档键；源包键各自归属源包流程读写，组合包只读源包事件流，不跨写源包存档。
## 6. SillyTavern 装载指引（三步）
1. **系统提示/角色卡**：把 01_核心协议 → 02_联动注册表（§6 顺序 + §8.4 组合登记条目）→ 06_Agent执行协议 → 本 README §2 装载清单，按序写入系统提示；角色卡按源包 §4 默认状态装载，组合包不覆盖源包角色卡。
2. **世界信息（Lorebook）**：本包无自有资产键，不新增 Lorebook 导入项；源包资产键按各源包 README §6 导入（命中即注入裁剪后素材）。
3. **正则与扩展**：挂「匿名馈赠」脱敏正则（campus_anonymous_gift 输出前剥离生产链细节，去来源化）；骰子/事件判定沿用源包扩展接 asset_roll(seed)。
> 最小系统提示骨架见官方 07_官方核心出厂与社区预设导航.md §4（协议引导，多包通用）。
## 7. 包级验收清单
| # | 验收项 | 判定标准 |
| --- | --- | --- |
| 1 | 目录结构完整 | modules/ 2 模块（M91/M92）+ assets/（0 文件）+ pipelines/P04 + 本 README + protocol.yaml |
| 2 | 双源一致（check14 ⑥） | protocol.yaml 与 README 的包名（校园西幻轻混组合包）/管线（P04）/资产数（0）一致 |
| 3 | 机读结构合规（check16 ①） | 自带模块 machine_contract：schema="1" + id 字符串 + events.publish/subscribe 均列表 |
| 4 | 装配契约闭合（check16 ③） | M92 subscribe ⊆ M17 publish（production_output），references 仲裁无 miss |
| 5 | 挂载层无冲突（check15 ③） | 本包 P40/P50 与校园 P40 / 西幻 P50 同层 default 交集 = ∅ |
| 6 | 编号段合规（R2） | 本包模块限 M91/M92（M91-M99 预留段），未占官方核心或源包编号 |
| 7 | 入口可导航 | 根 README → community/README.md 索引 → 本包 README 可访问 |
> 执行方式：与文件实况对照终验（verify.sh check1-16 全绿为机器判定；行数/锚点以终端 grep 复核为准）。
