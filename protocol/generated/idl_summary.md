# protocol/generated · 协议层 IDL 校验摘要（43 A4 golden 产物）

> 本文件由 `desktop/src/core/protocol_golden.py` 确定性渲染；
> 校验摘要与 schema/协议件双源一致由 verify check31 断言（过期即红，重跑刷新）。

## 覆盖
| schema | 模块文档 | 机读契约 | 管线 | 协议包 | 台账条目 |
| - | - | - | - | - | - |
| 5 | 248 | 248 | 114 | 111 | 2 |

## schema 定义
- asset.schema.json
- contract.schema.json
- module.schema.json
- pipeline.schema.json
- protocol.schema.json

## 装配在册证据（id 集）
- AI人力资源与招聘:M01, AI人力资源与招聘:M02, AI保险:M01, AI保险:M02, AI农业:M01, AI农业:M02, AI制药与生物:M01, AI制药与生物:M02, AI制造业:M01, AI制造业:M02, AI医疗健康:M01, AI医疗健康:M02, AI政务与公共事务:M01, AI政务与公共事务:M02, AI教育:M01, AI教育:M02, AI法律与合规:M01, AI法律与合规:M02, AI系统:M25, AI系统:M26, AI能源与电力:M01, AI能源与电力:M02, AI金融投研与风控:M01, AI金融投研与风控:M02, AI食品与餐饮:M01, AI食品与餐饮:M02, M00, M01, M02, M03, M04, M06, M07, M08, M09, M11, M12, M13, M14, M15, M16, M17, M18, M19, M20, M23, M24, M40, M41, M43, M50, M55, M57, M58, M59, M65, M80, M90, M91, M92, M93, M94, M95, M96, M97, M98, 三维与世界模型:M01, 三维与世界模型:M02, 上下文工程与长上下文:M01, 上下文工程与长上下文:M02, 世界书与设定库:M01, 世界书与设定库:M02, 个人助理与日常生活:M01, 个人助理与日常生活:M02, 事件:M22, 交通与出行:M01, 交通与出行:M02, 产业与商业落地:M01, 产业与商业落地:M02, 代码与软件工程:M01, 代码与软件工程:M02, 代码大模型:M01, 代码大模型:M02, 代码审查与缺陷检测:M01, 代码审查与缺陷检测:M02, 代码生成与补全:M01, 代码生成与补全:M02, 企业培训与组织学习:M01, 企业培训与组织学习:M02, 传媒与新闻:M01, 传媒与新闻:M02, 信息抽取与结构化:M01, 信息抽取与结构化:M02, 具身智能与机器人:M01, 具身智能与机器人:M02, 内容分发与社区运营:M01, 内容分发与社区运营:M02, 内容改写与风格迁移:M01, 内容改写与风格迁移:M02, 分类与情感分析:M01, 分类与情感分析:M02, 参数高效微调:M01, 参数高效微调:M02, 可观测性成本与可靠性:M01, 可观测性成本与可靠性:M02, 可解释性与审计:M01, 可解释性与审计:M02, 合成数据生成:M01, 合成数据生成:M02, 合规与监管:M01, 合规与监管:M02, 向量库与检索管线:M01, 向量库与检索管线:M02, 图像生成与编辑:M01, 图像生成与编辑:M02, 图像生成与视觉创作:M01, 图像生成与视觉创作:M02, 图像生成与视觉设计:M01, 图像生成与视觉设计:M02, 多智能体协同:M01, 多智能体协同:M02, 多模态大模型:M01, 多模态大模型:M02, 多语翻译与本地化:M01, 多语翻译与本地化:M02, 多轮对话与角色扮演:M01, 多轮对话与角色扮演:M02, 大语言模型:M01, 大语言模型:M02, 安全与对齐:M01, 安全与对齐:M02, 对话与客服:M01, 对话与客服:M02, 对齐与偏好优化:M01, 对齐与偏好优化:M02, 嵌入与检索表示:M01, 嵌入与检索表示:M02, 平台与基础设施:M01, 平台与基础设施:M02, 建筑与房地产:M01, 建筑与房地产:M02, 开源与开发者生态:M01, 开源与开发者生态:M02, 强化学习与决策:M01, 强化学习与决策:M02, 情感:M22, 推理优化与加速:M01, 推理优化与加速:M02, 推理服务与部署:M01, 推理服务与部署:M02, 推荐排序与广告:M01, 推荐排序与广告:M02, 提示工程与指令设计:M01, 提示工程与指令设计:M02, 提示工程与提示模板:M01, 提示工程与提示模板:M02, 搜索与信息聚合:M01, 搜索与信息聚合:M02, 摘要与信息压缩:M01, 摘要与信息压缩:M02, 数字人与虚拟形象:M01, 数字人与虚拟形象:M02, 数学与形式化推理:M01, 数学与形式化推理:M02, 数据分析与决策支持:M01, 数据分析与决策支持:M02, 数据分析与表格理解:M01, 数据分析与表格理解:M02, 数据标注与标注质量:M01, 数据标注与标注质量:M02, 数据采集与清洗:M01, 数据采集与清洗:M02, 文旅与酒店:M01, 文旅与酒店:M02, 文本生成与创作:M01, 文本生成与创作:M02, 文档解析与版面理解:M01, 文档解析与版面理解:M02, 智能体与工作流编排:M01, 智能体与工作流编排:M02, 智能体框架与工具调用:M01, 智能体框架与工具调用:M02, 机器翻译与本地化:M01, 机器翻译与本地化:M02, 模型运营与成本:M01, 模型运营与成本:M02, 测试与用例生成:M01, 测试与用例生成:M02, 游戏与互动娱乐:M01, 游戏与互动娱乐:M02, 版权与知识产权:M01, 版权与知识产权:M02, 物流与供应链:M01, 物流与供应链:M02, 生存:M10, 监督微调:M01, 监督微调:M02, 知识管理与检索增强:M01, 知识管理与检索增强:M02, 知识问答与检索增强:M01, 知识问答与检索增强:M02, 科研与实验:M01, 科研与实验:M02, 端侧与边缘小模型:M01, 端侧与边缘小模型:M02, 红队越狱与安全测试:M01, 红队越狱与安全测试:M02, 编辑校对与出版:M01, 编辑校对与出版:M02, 视觉模型:M01, 视觉模型:M02, 视频生成与剪辑:M01, 视频生成与剪辑:M02, 视频生成与理解:M01, 视频生成与理解:M02, 视频生成与自动剪辑:M01, 视频生成与自动剪辑:M02, 角色扮演与角色卡:M01, 角色扮演与角色卡:M02, 记忆体与个性化:M01, 记忆体与个性化:M02, 评测与基准:M01, 评测与基准:M02, 评测基准与排行榜:M01, 评测基准与排行榜:M02, 语音合成与配音:M01, 语音合成与配音:M02, 语音识别与合成:M01, 语音识别与合成:M02, 语音转写与会议记录:M01, 语音转写与会议记录:M02, 通用:M10, 量化金融:M31, 量化金融:M32, 长文本与小说创作:M01, 长文本与小说创作:M02, 隐私与数据治理:M01, 隐私与数据治理:M02, 零售与电商:M01, 零售与电商:M02, 音频与音乐生成:M01, 音频与音乐生成:M02, 音频音乐与语音:M01, 音频音乐与语音:M02, 预测异常与风险:M01, 预测异常与风险:M02, 预训练与继续预训练:M01, 预训练与继续预训练:M02

## 机读契约模块
| id | conformance | layer | source |
| - | - | - | - |
| AI人力资源与招聘:M01 | L2 | P40 | community/AI人力资源与招聘域包/modules/D14a_AI人力资源与招聘口径登记.md |
| AI人力资源与招聘:M02 | L2 | P60 | community/AI人力资源与招聘域包/modules/D14b_AI人力资源与招聘收口与形态派生.md |
| AI保险:M01 | L2 | P40 | community/AI保险域包/modules/D05a_AI保险口径登记.md |
| AI保险:M02 | L2 | P60 | community/AI保险域包/modules/D05b_AI保险收口与形态派生.md |
| AI农业:M01 | L2 | P40 | community/AI农业域包/modules/D10a_AI农业口径登记.md |
| AI农业:M02 | L2 | P60 | community/AI农业域包/modules/D10b_AI农业收口与形态派生.md |
| AI制药与生物:M01 | L2 | P40 | community/AI制药与生物域包/modules/D02a_AI制药与生物口径登记.md |
| AI制药与生物:M02 | L2 | P60 | community/AI制药与生物域包/modules/D02b_AI制药与生物收口与形态派生.md |
| AI制造业:M01 | L2 | P40 | community/AI制造业域包/modules/D08a_AI制造业口径登记.md |
| AI制造业:M02 | L2 | P60 | community/AI制造业域包/modules/D08b_AI制造业收口与形态派生.md |
| AI医疗健康:M01 | L2 | P40 | community/AI医疗健康域包/modules/D01a_AI医疗健康口径登记.md |
| AI医疗健康:M02 | L2 | P60 | community/AI医疗健康域包/modules/D01b_AI医疗健康收口与形态派生.md |
| AI政务与公共事务:M01 | L2 | P40 | community/AI政务与公共事务域包/modules/D07a_AI政务与公共事务口径登记.md |
| AI政务与公共事务:M02 | L2 | P60 | community/AI政务与公共事务域包/modules/D07b_AI政务与公共事务收口与形态派生.md |
| AI教育:M01 | L2 | P40 | community/AI教育域包/modules/D06a_AI教育口径登记.md |
| AI教育:M02 | L2 | P60 | community/AI教育域包/modules/D06b_AI教育收口与形态派生.md |
| AI法律与合规:M01 | L2 | P40 | community/AI法律与合规域包/modules/D03a_AI法律与合规口径登记.md |
| AI法律与合规:M02 | L2 | P60 | community/AI法律与合规域包/modules/D03b_AI法律与合规收口与形态派生.md |
| AI系统:M25 | L2 | P40 | community/AI系统域包/modules/M25_前置闭包求值.md |
| AI系统:M26 | L2 | P60 | community/AI系统域包/modules/M26_装载序就绪门.md |
| AI能源与电力:M01 | L2 | P40 | community/AI能源与电力域包/modules/D09a_AI能源与电力口径登记.md |
| AI能源与电力:M02 | L2 | P60 | community/AI能源与电力域包/modules/D09b_AI能源与电力收口与形态派生.md |
| AI金融投研与风控:M01 | L2 | P40 | community/AI金融投研与风控域包/modules/D04a_AI金融投研与风控口径登记.md |
| AI金融投研与风控:M02 | L2 | P60 | community/AI金融投研与风控域包/modules/D04b_AI金融投研与风控收口与形态派生.md |
| AI食品与餐饮:M01 | L2 | P40 | community/AI食品与餐饮域包/modules/D16a_AI食品与餐饮口径登记.md |
| AI食品与餐饮:M02 | L2 | P60 | community/AI食品与餐饮域包/modules/D16b_AI食品与餐饮收口与形态派生.md |
| M00 | L2 | P00 | 04_模块库/通用类/M00_数据结构.md |
| M01 | L2 | P20 | community/西幻生存领域包/modules/M01_职业成长.md |
| M02 | L2 | P20 | community/西幻生存领域包/modules/M02_种族天赋.md |
| M03 | L2 | P40 | community/西幻生存领域包/modules/M03_技能融合.md |
| M04 | L2 | P50 | community/西幻生存领域包/modules/M04_战斗系统.md |
| M06 | L2 | P30 | 04_模块库/事件类/M06_任务剧情.md |
| M07 | L2 | P60 | community/西幻生存领域包/modules/M07_地图区域.md |
| M08 | L2 | P10 | 04_模块库/世界类/M08_季节天气.md |
| M09 | L2 | P60 | community/西幻生存领域包/modules/M09_经济贸易.md |
| M10 | L1 | P40 | community/西幻生存领域包/modules/M10_死亡重生.md |
| M11 | L2 | P50 | community/西幻生存领域包/modules/M11_文字魔法.md |
| M12 | L2 | P50 | 04_模块库/事件类/M12_NPC对话.md |
| M13 | L2 | P30 | 04_模块库/事件类/M13_NPC交互.md |
| M14 | L2 | P60 | community/西幻生存领域包/modules/M14_阵营声望.md |
| M15 | L2 | P60 | community/西幻生存领域包/modules/M15_帮派势力.md |
| M16 | L2 | P60 | community/西幻生存领域包/modules/M16_建筑据点.md |
| M17 | L2 | P50 | community/西幻生存领域包/modules/M17_生产制造.md |
| M18 | L2 | P30 | community/西幻生存领域包/modules/M18_混沌事件.md |
| M19 | L2 | P20 | community/西幻生存领域包/modules/M19_遗传后代.md |
| M20 | L2 | P70 | 04_模块库/事件类/M20_世界知识库.md |
| M22 | L1 | P40 | community/校园情感领域包/modules/M22_三冲动驱动.md |
| M23 | L2 | P20 | 04_模块库/通用类/M23_认知边界.md |
| M24 | L2 | P70 | 04_模块库/通用类/M24_组合规则.md |
| M40 | L2 | P40 | community/校园情感领域包/modules/M40_关系深度.md |
| M41 | L2 | P40 | community/校园情感领域包/modules/M41_恋爱进阶.md |
| M43 | L2 | P40 | community/校园情感领域包/modules/M43_情敌系统.md |
| M50 | L2 | 调度器 | 04_模块库/通用类/M50_主循环.md |
| M55 | L2 | P40 | community/校园情感领域包/modules/M55_匿名情书.md |
| M57 | L2 | P50 | community/校园情感领域包/modules/M57_朋友圈动态.md |
| M58 | L2 | P50 | community/校园情感领域包/modules/M58_电话通讯.md |
| M59 | L2 | P50 | community/校园情感领域包/modules/M59_群聊系统.md |
| M65 | L2 | P60 | community/校园情感领域包/modules/M65_幽灵遗憾.md |
| M80 | L2 | P80 | 04_模块库/通用类/M80_输出生成器.md |
| M90 | L2 | P90 | 04_模块库/技术文档类/M90_技术文档结构.md |
| M91 | L2 | P40 | community/校园西幻轻混组合包/modules/M91_异界身份桥.md |
| M92 | L2 | P50 | community/校园西幻轻混组合包/modules/M92_轻混装配执行.md |
| M93 | L2 | P00 | community/通用核心基础包/modules/M93_通用状态快照.md |
| M94 | L2 | P10 | community/通用核心基础包/modules/M94_通用节拍桥.md |
| M95 | L2 | P40 | community/通用核心基础包/modules/M95_通用决策汇总.md |
| M96 | L2 | P80 | community/通用核心基础包/modules/M96_通用输出润色.md |
| M97 | L2 | P40 | community/技术文档域包/modules/M97_术语管理.md |
| M98 | L2 | P60 | community/技术文档域包/modules/M98_修订记录.md |
| 三维与世界模型:M01 | L2 | P40 | community/三维与世界模型域包/modules/A08a_三维口径登记.md |
| 三维与世界模型:M02 | L2 | P60 | community/三维与世界模型域包/modules/A08b_三维面收口与形态派生.md |
| 上下文工程与长上下文:M01 | L2 | P40 | community/上下文工程与长上下文域包/modules/C12a_上下文工程与长上下文口径登记.md |
| 上下文工程与长上下文:M02 | L2 | P60 | community/上下文工程与长上下文域包/modules/C12b_上下文工程与长上下文收口与形态派生.md |
| 世界书与设定库:M01 | L2 | P40 | community/世界书与设定库域包/modules/E03a_世界书与设定库口径登记.md |
| 世界书与设定库:M02 | L2 | P60 | community/世界书与设定库域包/modules/E03b_世界书与设定库收口与形态派生.md |
| 个人助理与日常生活:M01 | L2 | P40 | community/个人助理与日常生活域包/modules/E16a_个人助理与日常生活口径登记.md |
| 个人助理与日常生活:M02 | L2 | P60 | community/个人助理与日常生活域包/modules/E16b_个人助理与日常生活收口与形态派生.md |
| 事件:M22 | L2 | P30 | 04_模块库/事件类/M22_事件叙事.md |
| 交通与出行:M01 | L2 | P40 | community/交通与出行域包/modules/D13a_交通与出行口径登记.md |
| 交通与出行:M02 | L2 | P60 | community/交通与出行域包/modules/D13b_交通与出行收口与形态派生.md |
| 产业与商业落地:M01 | L2 | P40 | community/产业与商业落地域包/modules/F10a_产业与商业落地口径登记.md |
| 产业与商业落地:M02 | L2 | P60 | community/产业与商业落地域包/modules/F10b_产业与商业落地收口与形态派生.md |
| 代码与软件工程:M01 | L2 | P40 | community/代码与软件工程域包/modules/E13a_代码与软件工程口径登记.md |
| 代码与软件工程:M02 | L2 | P60 | community/代码与软件工程域包/modules/E13b_代码与软件工程收口与形态派生.md |
| 代码大模型:M01 | L2 | P40 | community/代码大模型域包/modules/A09a_代码口径登记.md |
| 代码大模型:M02 | L2 | P60 | community/代码大模型域包/modules/A09b_代码面收口与形态派生.md |
| 代码审查与缺陷检测:M01 | L2 | P40 | community/代码审查与缺陷检测域包/modules/B09a_审查口径登记.md |
| 代码审查与缺陷检测:M02 | L2 | P60 | community/代码审查与缺陷检测域包/modules/B09b_审查面收口与形态派生.md |
| 代码生成与补全:M01 | L2 | P40 | community/代码生成与补全域包/modules/B08a_代码生成口径登记.md |
| 代码生成与补全:M02 | L2 | P60 | community/代码生成与补全域包/modules/B08b_生成面收口与形态派生.md |
| 企业培训与组织学习:M01 | L2 | P40 | community/企业培训与组织学习域包/modules/E15a_企业培训与组织学习口径登记.md |
| 企业培训与组织学习:M02 | L2 | P60 | community/企业培训与组织学习域包/modules/E15b_企业培训与组织学习收口与形态派生.md |
| 传媒与新闻:M01 | L2 | P40 | community/传媒与新闻域包/modules/D17a_传媒与新闻口径登记.md |
| 传媒与新闻:M02 | L2 | P60 | community/传媒与新闻域包/modules/D17b_传媒与新闻收口与形态派生.md |
| 信息抽取与结构化:M01 | L2 | P40 | community/信息抽取与结构化域包/modules/B05a_抽取口径登记.md |
| 信息抽取与结构化:M02 | L2 | P60 | community/信息抽取与结构化域包/modules/B05b_抽取面收口与形态派生.md |
| 具身智能与机器人:M01 | L2 | P40 | community/具身智能与机器人域包/modules/A13a_具身口径登记.md |
| 具身智能与机器人:M02 | L2 | P60 | community/具身智能与机器人域包/modules/A13b_具身面收口与形态派生.md |
| 内容分发与社区运营:M01 | L2 | P40 | community/内容分发与社区运营域包/modules/E19a_内容分发与社区运营口径登记.md |
| 内容分发与社区运营:M02 | L2 | P60 | community/内容分发与社区运营域包/modules/E19b_内容分发与社区运营收口与形态派生.md |
| 内容改写与风格迁移:M01 | L2 | P40 | community/内容改写与风格迁移域包/modules/E05a_内容改写与风格迁移口径登记.md |
| 内容改写与风格迁移:M02 | L2 | P60 | community/内容改写与风格迁移域包/modules/E05b_内容改写与风格迁移收口与形态派生.md |
| 分类与情感分析:M01 | L2 | P40 | community/分类与情感分析域包/modules/B04a_分类口径登记.md |
| 分类与情感分析:M02 | L2 | P60 | community/分类与情感分析域包/modules/B04b_分类面收口与形态派生.md |
| 参数高效微调:M01 | L2 | P40 | community/参数高效微调域包/modules/C06a_参数高效微调口径登记.md |
| 参数高效微调:M02 | L2 | P60 | community/参数高效微调域包/modules/C06b_参数高效微调收口与形态派生.md |
| 可观测性成本与可靠性:M01 | L2 | P40 | community/可观测性成本与可靠性域包/modules/C18a_可观测性成本与可靠性口径登记.md |
| 可观测性成本与可靠性:M02 | L2 | P60 | community/可观测性成本与可靠性域包/modules/C18b_可观测性成本与可靠性收口与形态派生.md |
| 可解释性与审计:M01 | L2 | P40 | community/可解释性与审计域包/modules/F06a_可解释性与审计口径登记.md |
| 可解释性与审计:M02 | L2 | P60 | community/可解释性与审计域包/modules/F06b_可解释性与审计收口与形态派生.md |
| 合成数据生成:M01 | L2 | P40 | community/合成数据生成域包/modules/C03a_合成数据生成口径登记.md |
| 合成数据生成:M02 | L2 | P60 | community/合成数据生成域包/modules/C03b_合成数据生成收口与形态派生.md |
| 合规与监管:M01 | L2 | P40 | community/合规与监管域包/modules/F02a_合规与监管口径登记.md |
| 合规与监管:M02 | L2 | P60 | community/合规与监管域包/modules/F02b_合规与监管收口与形态派生.md |
| 向量库与检索管线:M01 | L2 | P40 | community/向量库与检索管线域包/modules/C15a_向量库与检索管线口径登记.md |
| 向量库与检索管线:M02 | L2 | P60 | community/向量库与检索管线域包/modules/C15b_向量库与检索管线收口与形态派生.md |
| 图像生成与编辑:M01 | L2 | P40 | community/图像生成与编辑域包/modules/A07a_图像生成口径登记.md |
| 图像生成与编辑:M02 | L2 | P60 | community/图像生成与编辑域包/modules/A07b_生成面收口与形态派生.md |
| 图像生成与视觉创作:M01 | L2 | P40 | community/图像生成与视觉创作域包/modules/E07a_图像生成与视觉创作口径登记.md |
| 图像生成与视觉创作:M02 | L2 | P60 | community/图像生成与视觉创作域包/modules/E07b_图像生成与视觉创作收口与形态派生.md |
| 图像生成与视觉设计:M01 | L2 | P40 | community/图像生成与视觉设计域包/modules/B15a_图像生成与视觉设计口径登记.md |
| 图像生成与视觉设计:M02 | L2 | P60 | community/图像生成与视觉设计域包/modules/B15b_图像生成与视觉设计收口与形态派生.md |
| 多智能体协同:M01 | L2 | P40 | community/多智能体协同域包/modules/C17a_多智能体协同口径登记.md |
| 多智能体协同:M02 | L2 | P60 | community/多智能体协同域包/modules/C17b_多智能体协同收口与形态派生.md |
| 多模态大模型:M01 | L2 | P40 | community/多模态大模型域包/modules/A02a_多模态口径登记.md |
| 多模态大模型:M02 | L2 | P60 | community/多模态大模型域包/modules/A02b_多模态面收口与形态派生.md |
| 多语翻译与本地化:M01 | L2 | P40 | community/多语翻译与本地化域包/modules/E06a_多语翻译与本地化口径登记.md |
| 多语翻译与本地化:M02 | L2 | P60 | community/多语翻译与本地化域包/modules/E06b_多语翻译与本地化收口与形态派生.md |
| 多轮对话与角色扮演:M01 | L2 | P40 | community/多轮对话与角色扮演域包/modules/B07a_角色扮演口径登记.md |
| 多轮对话与角色扮演:M02 | L2 | P60 | community/多轮对话与角色扮演域包/modules/B07b_对话面收口与形态派生.md |
| 大语言模型:M01 | L2 | P40 | community/大语言模型域包/modules/A01a_模型与能力口径登记.md |
| 大语言模型:M02 | L2 | P60 | community/大语言模型域包/modules/A01b_能力面收口与形态派生.md |
| 安全与对齐:M01 | L2 | P40 | community/安全与对齐域包/modules/F01a_安全与对齐口径登记.md |
| 安全与对齐:M02 | L2 | P60 | community/安全与对齐域包/modules/F01b_安全与对齐收口与形态派生.md |
| 对话与客服:M01 | L2 | P40 | community/对话与客服域包/modules/E18a_对话与客服口径登记.md |
| 对话与客服:M02 | L2 | P60 | community/对话与客服域包/modules/E18b_对话与客服收口与形态派生.md |
| 对齐与偏好优化:M01 | L2 | P40 | community/对齐与偏好优化域包/modules/C07a_对齐与偏好优化口径登记.md |
| 对齐与偏好优化:M02 | L2 | P60 | community/对齐与偏好优化域包/modules/C07b_对齐与偏好优化收口与形态派生.md |
| 嵌入与检索表示:M01 | L2 | P40 | community/嵌入与检索表示域包/modules/A11a_嵌入口径登记.md |
| 嵌入与检索表示:M02 | L2 | P60 | community/嵌入与检索表示域包/modules/A11b_嵌入面收口与形态派生.md |
| 平台与基础设施:M01 | L2 | P40 | community/平台与基础设施域包/modules/F08a_平台与基础设施口径登记.md |
| 平台与基础设施:M02 | L2 | P60 | community/平台与基础设施域包/modules/F08b_平台与基础设施收口与形态派生.md |
| 建筑与房地产:M01 | L2 | P40 | community/建筑与房地产域包/modules/D15a_建筑与房地产口径登记.md |
| 建筑与房地产:M02 | L2 | P60 | community/建筑与房地产域包/modules/D15b_建筑与房地产收口与形态派生.md |
| 开源与开发者生态:M01 | L2 | P40 | community/开源与开发者生态域包/modules/F09a_开源与开发者生态口径登记.md |
| 开源与开发者生态:M02 | L2 | P60 | community/开源与开发者生态域包/modules/F09b_开源与开发者生态收口与形态派生.md |
| 强化学习与决策:M01 | L2 | P40 | community/强化学习与决策域包/modules/A12a_决策口径登记.md |
| 强化学习与决策:M02 | L2 | P60 | community/强化学习与决策域包/modules/A12b_决策面收口与形态派生.md |
| 推理优化与加速:M01 | L2 | P40 | community/推理优化与加速域包/modules/C10a_推理优化与加速口径登记.md |
| 推理优化与加速:M02 | L2 | P60 | community/推理优化与加速域包/modules/C10b_推理优化与加速收口与形态派生.md |
| 推理服务与部署:M01 | L2 | P40 | community/推理服务与部署域包/modules/C11a_推理服务与部署口径登记.md |
| 推理服务与部署:M02 | L2 | P60 | community/推理服务与部署域包/modules/C11b_推理服务与部署收口与形态派生.md |
| 推荐排序与广告:M01 | L2 | P40 | community/推荐排序与广告域包/modules/B17a_推荐排序与广告口径登记.md |
| 推荐排序与广告:M02 | L2 | P60 | community/推荐排序与广告域包/modules/B17b_推荐排序与广告收口与形态派生.md |
| 提示工程与指令设计:M01 | L2 | P40 | community/提示工程与指令设计域包/modules/E01a_提示工程与指令设计口径登记.md |
| 提示工程与指令设计:M02 | L2 | P60 | community/提示工程与指令设计域包/modules/E01b_提示工程与指令设计收口与形态派生.md |
| 提示工程与提示模板:M01 | L2 | P40 | community/提示工程与提示模板域包/modules/C13a_提示工程与提示模板口径登记.md |
| 提示工程与提示模板:M02 | L2 | P60 | community/提示工程与提示模板域包/modules/C13b_提示工程与提示模板收口与形态派生.md |
| 搜索与信息聚合:M01 | L2 | P40 | community/搜索与信息聚合域包/modules/E17a_搜索与信息聚合口径登记.md |
| 搜索与信息聚合:M02 | L2 | P60 | community/搜索与信息聚合域包/modules/E17b_搜索与信息聚合收口与形态派生.md |
| 摘要与信息压缩:M01 | L2 | P40 | community/摘要与信息压缩域包/modules/B02a_摘要口径登记.md |
| 摘要与信息压缩:M02 | L2 | P60 | community/摘要与信息压缩域包/modules/B02b_摘要面收口与形态派生.md |
| 数字人与虚拟形象:M01 | L2 | P40 | community/数字人与虚拟形象域包/modules/E20a_数字人与虚拟形象口径登记.md |
| 数字人与虚拟形象:M02 | L2 | P60 | community/数字人与虚拟形象域包/modules/E20b_数字人与虚拟形象收口与形态派生.md |
| 数学与形式化推理:M01 | L2 | P40 | community/数学与形式化推理域包/modules/A10a_推理口径登记.md |
| 数学与形式化推理:M02 | L2 | P60 | community/数学与形式化推理域包/modules/A10b_推理面收口与形态派生.md |
| 数据分析与决策支持:M01 | L2 | P40 | community/数据分析与决策支持域包/modules/E14a_数据分析与决策支持口径登记.md |
| 数据分析与决策支持:M02 | L2 | P60 | community/数据分析与决策支持域包/modules/E14b_数据分析与决策支持收口与形态派生.md |
| 数据分析与表格理解:M01 | L2 | P40 | community/数据分析与表格理解域包/modules/B11a_分析口径登记.md |
| 数据分析与表格理解:M02 | L2 | P60 | community/数据分析与表格理解域包/modules/B11b_分析面收口与形态派生.md |
| 数据标注与标注质量:M01 | L2 | P40 | community/数据标注与标注质量域包/modules/C02a_数据标注与标注质量口径登记.md |
| 数据标注与标注质量:M02 | L2 | P60 | community/数据标注与标注质量域包/modules/C02b_数据标注与标注质量收口与形态派生.md |
| 数据采集与清洗:M01 | L2 | P40 | community/数据采集与清洗域包/modules/C01a_采集与清洗口径登记.md |
| 数据采集与清洗:M02 | L2 | P60 | community/数据采集与清洗域包/modules/C01b_数据面收口与形态派生.md |
| 文旅与酒店:M01 | L2 | P40 | community/文旅与酒店域包/modules/D19a_文旅与酒店口径登记.md |
| 文旅与酒店:M02 | L2 | P60 | community/文旅与酒店域包/modules/D19b_文旅与酒店收口与形态派生.md |
| 文本生成与创作:M01 | L2 | P40 | community/文本生成与创作域包/modules/B01a_创作口径登记.md |
| 文本生成与创作:M02 | L2 | P60 | community/文本生成与创作域包/modules/B01b_创作面收口与形态派生.md |
| 文档解析与版面理解:M01 | L2 | P40 | community/文档解析与版面理解域包/modules/B12a_解析口径登记.md |
| 文档解析与版面理解:M02 | L2 | P60 | community/文档解析与版面理解域包/modules/B12b_解析面收口与形态派生.md |
| 智能体与工作流编排:M01 | L2 | P40 | community/智能体与工作流编排域包/modules/E12a_智能体与工作流编排口径登记.md |
| 智能体与工作流编排:M02 | L2 | P60 | community/智能体与工作流编排域包/modules/E12b_智能体与工作流编排收口与形态派生.md |
| 智能体框架与工具调用:M01 | L2 | P40 | community/智能体框架与工具调用域包/modules/C16a_智能体框架与工具调用口径登记.md |
| 智能体框架与工具调用:M02 | L2 | P60 | community/智能体框架与工具调用域包/modules/C16b_智能体框架与工具调用收口与形态派生.md |
| 机器翻译与本地化:M01 | L2 | P40 | community/机器翻译与本地化域包/modules/B03a_翻译口径登记.md |
| 机器翻译与本地化:M02 | L2 | P60 | community/机器翻译与本地化域包/modules/B03b_本地化面收口与形态派生.md |
| 模型运营与成本:M01 | L2 | P40 | community/模型运营与成本域包/modules/F07a_模型运营与成本口径登记.md |
| 模型运营与成本:M02 | L2 | P60 | community/模型运营与成本域包/modules/F07b_模型运营与成本收口与形态派生.md |
| 测试与用例生成:M01 | L2 | P40 | community/测试与用例生成域包/modules/B10a_测试口径登记.md |
| 测试与用例生成:M02 | L2 | P60 | community/测试与用例生成域包/modules/B10b_测试面收口与形态派生.md |
| 游戏与互动娱乐:M01 | L2 | P40 | community/游戏与互动娱乐域包/modules/D18a_游戏与互动娱乐口径登记.md |
| 游戏与互动娱乐:M02 | L2 | P60 | community/游戏与互动娱乐域包/modules/D18b_游戏与互动娱乐收口与形态派生.md |
| 版权与知识产权:M01 | L2 | P40 | community/版权与知识产权域包/modules/F04a_版权与知识产权口径登记.md |
| 版权与知识产权:M02 | L2 | P60 | community/版权与知识产权域包/modules/F04b_版权与知识产权收口与形态派生.md |
| 物流与供应链:M01 | L2 | P40 | community/物流与供应链域包/modules/D12a_物流与供应链口径登记.md |
| 物流与供应链:M02 | L2 | P60 | community/物流与供应链域包/modules/D12b_物流与供应链收口与形态派生.md |
| 监督微调:M01 | L2 | P40 | community/监督微调域包/modules/C05a_监督微调口径登记.md |
| 监督微调:M02 | L2 | P60 | community/监督微调域包/modules/C05b_监督微调收口与形态派生.md |
| 知识管理与检索增强:M01 | L2 | P40 | community/知识管理与检索增强域包/modules/E11a_知识管理与检索增强口径登记.md |
| 知识管理与检索增强:M02 | L2 | P60 | community/知识管理与检索增强域包/modules/E11b_知识管理与检索增强收口与形态派生.md |
| 知识问答与检索增强:M01 | L2 | P40 | community/知识问答与检索增强域包/modules/B06a_RAG 口径登记.md |
| 知识问答与检索增强:M02 | L2 | P60 | community/知识问答与检索增强域包/modules/B06b_RAG 面收口与形态派生.md |
| 科研与实验:M01 | L2 | P40 | community/科研与实验域包/modules/D20a_科研与实验口径登记.md |
| 科研与实验:M02 | L2 | P60 | community/科研与实验域包/modules/D20b_科研与实验收口与形态派生.md |
| 端侧与边缘小模型:M01 | L2 | P40 | community/端侧与边缘小模型域包/modules/A14a_端侧口径登记.md |
| 端侧与边缘小模型:M02 | L2 | P60 | community/端侧与边缘小模型域包/modules/A14b_端侧面收口与形态派生.md |
| 红队越狱与安全测试:M01 | L2 | P40 | community/红队越狱与安全测试域包/modules/C09a_红队越狱与安全测试口径登记.md |
| 红队越狱与安全测试:M02 | L2 | P60 | community/红队越狱与安全测试域包/modules/C09b_红队越狱与安全测试收口与形态派生.md |
| 编辑校对与出版:M01 | L2 | P40 | community/编辑校对与出版域包/modules/E10a_编辑校对与出版口径登记.md |
| 编辑校对与出版:M02 | L2 | P60 | community/编辑校对与出版域包/modules/E10b_编辑校对与出版收口与形态派生.md |
| 视觉模型:M01 | L2 | P40 | community/视觉模型域包/modules/A03a_视觉任务口径登记.md |
| 视觉模型:M02 | L2 | P60 | community/视觉模型域包/modules/A03b_视觉面收口与形态派生.md |
| 视频生成与剪辑:M01 | L2 | P40 | community/视频生成与剪辑域包/modules/E08a_视频生成与剪辑口径登记.md |
| 视频生成与剪辑:M02 | L2 | P60 | community/视频生成与剪辑域包/modules/E08b_视频生成与剪辑收口与形态派生.md |
| 视频生成与理解:M01 | L2 | P40 | community/视频生成与理解域包/modules/A06a_视频口径登记.md |
| 视频生成与理解:M02 | L2 | P60 | community/视频生成与理解域包/modules/A06b_视频面收口与形态派生.md |
| 视频生成与自动剪辑:M01 | L2 | P40 | community/视频生成与自动剪辑域包/modules/B16a_视频生成与自动剪辑口径登记.md |
| 视频生成与自动剪辑:M02 | L2 | P60 | community/视频生成与自动剪辑域包/modules/B16b_视频生成与自动剪辑收口与形态派生.md |
| 角色扮演与角色卡:M01 | L2 | P40 | community/角色扮演与角色卡域包/modules/E02a_角色扮演与角色卡口径登记.md |
| 角色扮演与角色卡:M02 | L2 | P60 | community/角色扮演与角色卡域包/modules/E02b_角色扮演与角色卡收口与形态派生.md |
| 记忆体与个性化:M01 | L2 | P40 | community/记忆体与个性化域包/modules/C14a_记忆体与个性化口径登记.md |
| 记忆体与个性化:M02 | L2 | P60 | community/记忆体与个性化域包/modules/C14b_记忆体与个性化收口与形态派生.md |
| 评测与基准:M01 | L2 | P40 | community/评测与基准域包/modules/F05a_评测与基准口径登记.md |
| 评测与基准:M02 | L2 | P60 | community/评测与基准域包/modules/F05b_评测与基准收口与形态派生.md |
| 评测基准与排行榜:M01 | L2 | P40 | community/评测基准与排行榜域包/modules/C08a_评测基准与排行榜口径登记.md |
| 评测基准与排行榜:M02 | L2 | P60 | community/评测基准与排行榜域包/modules/C08b_评测基准与排行榜收口与形态派生.md |
| 语音合成与配音:M01 | L2 | P40 | community/语音合成与配音域包/modules/B14a_语音合成与配音口径登记.md |
| 语音合成与配音:M02 | L2 | P60 | community/语音合成与配音域包/modules/B14b_语音合成与配音收口与形态派生.md |
| 语音识别与合成:M01 | L2 | P40 | community/语音识别与合成域包/modules/A04a_语音口径登记.md |
| 语音识别与合成:M02 | L2 | P60 | community/语音识别与合成域包/modules/A04b_语音面收口与形态派生.md |
| 语音转写与会议记录:M01 | L2 | P40 | community/语音转写与会议记录域包/modules/B13a_语音转写与会议记录口径登记.md |
| 语音转写与会议记录:M02 | L2 | P60 | community/语音转写与会议记录域包/modules/B13b_语音转写与会议记录收口与形态派生.md |
| 通用:M10 | L2 | P10 | 04_模块库/通用类/M10_时间推进.md |
| 量化金融:M31 | L2 | P40 | community/量化金融域包/modules/M31_因子与信号口径.md |
| 量化金融:M32 | L2 | P60 | community/量化金融域包/modules/M32_回测与绩效口径.md |
| 长文本与小说创作:M01 | L2 | P40 | community/长文本与小说创作域包/modules/E04a_长文本与小说创作口径登记.md |
| 长文本与小说创作:M02 | L2 | P60 | community/长文本与小说创作域包/modules/E04b_长文本与小说创作收口与形态派生.md |
| 隐私与数据治理:M01 | L2 | P40 | community/隐私与数据治理域包/modules/F03a_隐私与数据治理口径登记.md |
| 隐私与数据治理:M02 | L2 | P60 | community/隐私与数据治理域包/modules/F03b_隐私与数据治理收口与形态派生.md |
| 零售与电商:M01 | L2 | P40 | community/零售与电商域包/modules/D11a_零售与电商口径登记.md |
| 零售与电商:M02 | L2 | P60 | community/零售与电商域包/modules/D11b_零售与电商收口与形态派生.md |
| 音频与音乐生成:M01 | L2 | P40 | community/音频与音乐生成域包/modules/A05a_音频音乐口径登记.md |
| 音频与音乐生成:M02 | L2 | P60 | community/音频与音乐生成域包/modules/A05b_音频面收口与形态派生.md |
| 音频音乐与语音:M01 | L2 | P40 | community/音频音乐与语音域包/modules/E09a_音频音乐与语音口径登记.md |
| 音频音乐与语音:M02 | L2 | P60 | community/音频音乐与语音域包/modules/E09b_音频音乐与语音收口与形态派生.md |
| 预测异常与风险:M01 | L2 | P40 | community/预测异常与风险域包/modules/B18a_预测异常与风险口径登记.md |
| 预测异常与风险:M02 | L2 | P60 | community/预测异常与风险域包/modules/B18b_预测异常与风险收口与形态派生.md |
| 预训练与继续预训练:M01 | L2 | P40 | community/预训练与继续预训练域包/modules/C04a_预训练与继续预训练口径登记.md |
| 预训练与继续预训练:M02 | L2 | P60 | community/预训练与继续预训练域包/modules/C04b_预训练与继续预训练收口与形态派生.md |

## 管线
- P00_通用文档生成管线.md, P01_标准管线.md, P02_校园情感流管线.md, P03_西幻生存流管线.md, P04_轻混装配流管线.md, P05_核心基础流管线.md, P06_技术文档题材装配流管线.md, P07_AI系统域装配流管线.md, P08_量化金融域装配流管线.md, P09_大语言模型装配流管线.md, P100_版权与知识产权装配流管线.md, P101_评测与基准装配流管线.md, P102_可解释性与审计装配流管线.md, P103_模型运营与成本装配流管线.md, P104_平台与基础设施装配流管线.md, P105_开源与开发者生态装配流管线.md, P106_产业与商业落地装配流管线.md, P107_监督微调装配流管线.md, P108_组合包-数据管线装配流管线.md, P109_组合包-检索栈装配流管线.md, P110_组合包-受监管行业装配流管线.md, P111_组合包-轻混与保险装配流管线.md, P112_游戏与互动娱乐装配流管线.md, P113_角色扮演与角色卡装配流管线.md, P114_知识管理与检索增强装配流管线.md, P115_企业培训与组织学习装配流管线.md, P116_对话与客服装配流管线.md, P117_零售与电商装配流管线.md, P118_推荐、排序与广告装配流管线.md, P119_预测、异常与风险装配流管线.md, P11_多模态大模型装配流管线.md, P120_评测、基准与排行榜装配流管线.md, P121_红队、越狱与安全测试装配流管线.md, P122_可观测性、成本与可靠性装配流管线.md, P123_AI+医疗健康装配流管线.md, P124_AI+制药与生物装配流管线.md, P125_AI+法律与合规装配流管线.md, P126_AI+金融投研与风控装配流管线.md, P127_AI+保险装配流管线.md, P128_AI+教育装配流管线.md, P129_AI+政务与公共事务装配流管线.md, P12_视觉模型装配流管线.md, P130_AI+制造业装配流管线.md, P131_AI+能源与电力装配流管线.md, P132_AI+农业装配流管线.md, P133_AI+人力资源与招聘装配流管线.md, P13_语音识别与合成装配流管线.md, P14_音频与音乐生成装配流管线.md, P15_视频生成与理解装配流管线.md, P16_图像生成与编辑装配流管线.md, P17_文本生成与创作装配流管线.md, P18_摘要与信息压缩装配流管线.md, P19_机器翻译与本地化装配流管线.md, P21_分类与情感分析装配流管线.md, P22_代码大模型装配流管线.md, P23_嵌入与检索表示装配流管线.md, P24_具身智能与机器人装配流管线.md, P25_三维与世界模型装配流管线.md, P26_数学与形式化推理装配流管线.md, P27_强化学习与决策装配流管线.md, P28_端侧与边缘小模型装配流管线.md, P29_信息抽取与结构化装配流管线.md, P31_知识问答与检索增强装配流管线.md, P32_多轮对话与角色扮演装配流管线.md, P33_代码生成与补全装配流管线.md, P34_代码审查与缺陷检测装配流管线.md, P35_测试与用例生成装配流管线.md, P36_数据分析与表格理解装配流管线.md, P37_文档解析与版面理解装配流管线.md, P38_语音转写与会议记录装配流管线.md, P39_语音合成与配音装配流管线.md, P41_图像生成与视觉设计装配流管线.md, P42_视频生成与自动剪辑装配流管线.md, P43_AI+食品与餐饮装配流管线.md, P45_数据采集与清洗装配流管线.md, P46_数据标注与标注质量装配流管线.md, P47_合成数据生成装配流管线.md, P48_预训练与继续预训练装配流管线.md, P49_参数高效微调装配流管线.md, P51_对齐与偏好优化装配流管线.md, P53_推理优化与加速装配流管线.md, P54_推理服务与部署装配流管线.md, P55_上下文工程与长上下文装配流管线.md, P56_提示工程与提示模板装配流管线.md, P57_记忆体与个性化装配流管线.md, P58_向量库与检索管线装配流管线.md, P59_智能体框架与工具调用装配流管线.md, P61_多智能体协同装配流管线.md, P71_物流与供应链装配流管线.md, P72_交通与出行装配流管线.md, P74_建筑与房地产装配流管线.md, P76_传媒与新闻装配流管线.md, P77_文旅与酒店装配流管线.md, P78_科研与实验装配流管线.md, P79_提示工程与指令设计装配流管线.md, P81_世界书与设定库装配流管线.md, P82_长文本与小说创作装配流管线.md, P83_内容改写与风格迁移装配流管线.md, P84_多语翻译与本地化装配流管线.md, P85_图像生成与视觉创作装配流管线.md, P86_视频生成与剪辑装配流管线.md, P87_音频音乐与语音装配流管线.md, P88_编辑校对与出版装配流管线.md, P89_智能体与工作流编排装配流管线.md, P90_技术文档生成管线.md, P91_代码与软件工程装配流管线.md, P92_数据分析与决策支持装配流管线.md, P93_个人助理与日常生活装配流管线.md, P94_搜索与信息聚合装配流管线.md, P95_内容分发与社区运营装配流管线.md, P96_数字人与虚拟形象装配流管线.md, P97_安全与对齐装配流管线.md, P98_合规与监管装配流管线.md, P99_隐私与数据治理装配流管线.md

## 协议包
- community/AI人力资源与招聘域包/protocol.yaml, community/AI保险域包/protocol.yaml, community/AI农业域包/protocol.yaml, community/AI制药与生物域包/protocol.yaml, community/AI制造业域包/protocol.yaml, community/AI医疗健康域包/protocol.yaml, community/AI政务与公共事务域包/protocol.yaml, community/AI教育域包/protocol.yaml, community/AI法律与合规域包/protocol.yaml, community/AI系统域包/protocol.yaml, community/AI能源与电力域包/protocol.yaml, community/AI金融投研与风控域包/protocol.yaml, community/AI食品与餐饮域包/protocol.yaml, community/三维与世界模型域包/protocol.yaml, community/上下文工程与长上下文域包/protocol.yaml, community/世界书与设定库域包/protocol.yaml, community/个人助理与日常生活域包/protocol.yaml, community/交通与出行域包/protocol.yaml, community/产业与商业落地域包/protocol.yaml, community/代码与软件工程域包/protocol.yaml, community/代码大模型域包/protocol.yaml, community/代码审查与缺陷检测域包/protocol.yaml, community/代码生成与补全域包/protocol.yaml, community/企业培训与组织学习域包/protocol.yaml, community/传媒与新闻域包/protocol.yaml, community/信息抽取与结构化域包/protocol.yaml, community/具身智能与机器人域包/protocol.yaml, community/内容分发与社区运营域包/protocol.yaml, community/内容改写与风格迁移域包/protocol.yaml, community/分类与情感分析域包/protocol.yaml, community/参数高效微调域包/protocol.yaml, community/可观测性成本与可靠性域包/protocol.yaml, community/可解释性与审计域包/protocol.yaml, community/合成数据生成域包/protocol.yaml, community/合规与监管域包/protocol.yaml, community/向量库与检索管线域包/protocol.yaml, community/图像生成与编辑域包/protocol.yaml, community/图像生成与视觉创作域包/protocol.yaml, community/图像生成与视觉设计域包/protocol.yaml, community/多智能体协同域包/protocol.yaml, community/多模态大模型域包/protocol.yaml, community/多语翻译与本地化域包/protocol.yaml, community/多轮对话与角色扮演域包/protocol.yaml, community/大语言模型域包/protocol.yaml, community/安全与对齐域包/protocol.yaml, community/对话与客服域包/protocol.yaml, community/对齐与偏好优化域包/protocol.yaml, community/嵌入与检索表示域包/protocol.yaml, community/平台与基础设施域包/protocol.yaml, community/建筑与房地产域包/protocol.yaml, community/开源与开发者生态域包/protocol.yaml, community/强化学习与决策域包/protocol.yaml, community/技术文档域包/protocol.yaml, community/推理优化与加速域包/protocol.yaml, community/推理服务与部署域包/protocol.yaml, community/推荐排序与广告域包/protocol.yaml, community/提示工程与指令设计域包/protocol.yaml, community/提示工程与提示模板域包/protocol.yaml, community/搜索与信息聚合域包/protocol.yaml, community/摘要与信息压缩域包/protocol.yaml, community/数字人与虚拟形象域包/protocol.yaml, community/数学与形式化推理域包/protocol.yaml, community/数据分析与决策支持域包/protocol.yaml, community/数据分析与表格理解域包/protocol.yaml, community/数据标注与标注质量域包/protocol.yaml, community/数据采集与清洗域包/protocol.yaml, community/文旅与酒店域包/protocol.yaml, community/文本生成与创作域包/protocol.yaml, community/文档解析与版面理解域包/protocol.yaml, community/智能体与工作流编排域包/protocol.yaml, community/智能体框架与工具调用域包/protocol.yaml, community/机器翻译与本地化域包/protocol.yaml, community/校园情感领域包/protocol.yaml, community/校园西幻轻混组合包/protocol.yaml, community/模型运营与成本域包/protocol.yaml, community/测试与用例生成域包/protocol.yaml, community/游戏与互动娱乐域包/protocol.yaml, community/版权与知识产权域包/protocol.yaml, community/物流与供应链域包/protocol.yaml, community/监督微调域包/protocol.yaml, community/知识管理与检索增强域包/protocol.yaml, community/知识问答与检索增强域包/protocol.yaml, community/科研与实验域包/protocol.yaml, community/端侧与边缘小模型域包/protocol.yaml, community/红队越狱与安全测试域包/protocol.yaml, community/组合包-受监管行业/protocol.yaml, community/组合包-数据管线/protocol.yaml, community/组合包-检索栈/protocol.yaml, community/组合包-轻混与保险/protocol.yaml, community/编辑校对与出版域包/protocol.yaml, community/西幻生存领域包/protocol.yaml, community/视觉模型域包/protocol.yaml, community/视频生成与剪辑域包/protocol.yaml, community/视频生成与理解域包/protocol.yaml, community/视频生成与自动剪辑域包/protocol.yaml, community/角色扮演与角色卡域包/protocol.yaml, community/记忆体与个性化域包/protocol.yaml, community/评测与基准域包/protocol.yaml, community/评测基准与排行榜域包/protocol.yaml, community/语音合成与配音域包/protocol.yaml, community/语音识别与合成域包/protocol.yaml, community/语音转写与会议记录域包/protocol.yaml, community/通用核心基础包/protocol.yaml, community/量化金融域包/protocol.yaml, community/长文本与小说创作域包/protocol.yaml, community/隐私与数据治理域包/protocol.yaml, community/零售与电商域包/protocol.yaml, community/音频与音乐生成域包/protocol.yaml, community/音频音乐与语音域包/protocol.yaml, community/预测异常与风险域包/protocol.yaml, community/预训练与继续预训练域包/protocol.yaml

## 资产台账键
- TECH_RULES, TECH_TEMPLATES

