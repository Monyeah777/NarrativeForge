# protocol/generated · 协议层 IDL 校验摘要（43 A4 golden 产物）

> 本文件由 `desktop/src/core/protocol_golden.py` 确定性渲染；
> 校验摘要与 schema/协议件双源一致由 verify check31 断言（过期即红，重跑刷新）。

## 覆盖
| schema | 模块文档 | 机读契约 | 管线 | 协议包 | 台账条目 |
| - | - | - | - | - | - |
| 5 | 70 | 70 | 21 | 18 | 2 |

## schema 定义
- asset.schema.json
- contract.schema.json
- module.schema.json
- pipeline.schema.json
- protocol.schema.json

## 装配在册证据（id 集）
- AI系统:M25, AI系统:M26, M00, M01, M02, M03, M04, M06, M07, M08, M09, M11, M12, M13, M14, M15, M16, M17, M18, M19, M20, M23, M24, M40, M41, M43, M50, M55, M57, M58, M59, M65, M80, M90, M91, M92, M93, M94, M95, M96, M97, M98, 事件:M22, 分类与情感分析:M01, 分类与情感分析:M02, 图像生成与编辑:M01, 图像生成与编辑:M02, 多模态大模型:M01, 多模态大模型:M02, 大语言模型:M01, 大语言模型:M02, 情感:M22, 摘要与信息压缩:M01, 摘要与信息压缩:M02, 文本生成与创作:M01, 文本生成与创作:M02, 机器翻译与本地化:M01, 机器翻译与本地化:M02, 生存:M10, 视觉模型:M01, 视觉模型:M02, 视频生成与理解:M01, 视频生成与理解:M02, 语音识别与合成:M01, 语音识别与合成:M02, 通用:M10, 量化金融:M31, 量化金融:M32, 音频与音乐生成:M01, 音频与音乐生成:M02

## 机读契约模块
| id | conformance | layer | source |
| - | - | - | - |
| AI系统:M25 | L2 | P40 | community/AI系统域包/modules/M25_前置闭包求值.md |
| AI系统:M26 | L2 | P60 | community/AI系统域包/modules/M26_装载序就绪门.md |
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
| 事件:M22 | L2 | P30 | 04_模块库/事件类/M22_事件叙事.md |
| 分类与情感分析:M01 | L2 | P40 | community/分类与情感分析域包/modules/B04a_分类口径登记.md |
| 分类与情感分析:M02 | L2 | P60 | community/分类与情感分析域包/modules/B04b_分类面收口与形态派生.md |
| 图像生成与编辑:M01 | L2 | P40 | community/图像生成与编辑域包/modules/A07a_图像生成口径登记.md |
| 图像生成与编辑:M02 | L2 | P60 | community/图像生成与编辑域包/modules/A07b_生成面收口与形态派生.md |
| 多模态大模型:M01 | L2 | P40 | community/多模态大模型域包/modules/A02a_多模态口径登记.md |
| 多模态大模型:M02 | L2 | P60 | community/多模态大模型域包/modules/A02b_多模态面收口与形态派生.md |
| 大语言模型:M01 | L2 | P40 | community/大语言模型域包/modules/A01a_模型与能力口径登记.md |
| 大语言模型:M02 | L2 | P60 | community/大语言模型域包/modules/A01b_能力面收口与形态派生.md |
| 摘要与信息压缩:M01 | L2 | P40 | community/摘要与信息压缩域包/modules/B02a_摘要口径登记.md |
| 摘要与信息压缩:M02 | L2 | P60 | community/摘要与信息压缩域包/modules/B02b_摘要面收口与形态派生.md |
| 文本生成与创作:M01 | L2 | P40 | community/文本生成与创作域包/modules/B01a_创作口径登记.md |
| 文本生成与创作:M02 | L2 | P60 | community/文本生成与创作域包/modules/B01b_创作面收口与形态派生.md |
| 机器翻译与本地化:M01 | L2 | P40 | community/机器翻译与本地化域包/modules/B03a_翻译口径登记.md |
| 机器翻译与本地化:M02 | L2 | P60 | community/机器翻译与本地化域包/modules/B03b_本地化面收口与形态派生.md |
| 视觉模型:M01 | L2 | P40 | community/视觉模型域包/modules/A03a_视觉任务口径登记.md |
| 视觉模型:M02 | L2 | P60 | community/视觉模型域包/modules/A03b_视觉面收口与形态派生.md |
| 视频生成与理解:M01 | L2 | P40 | community/视频生成与理解域包/modules/A06a_视频口径登记.md |
| 视频生成与理解:M02 | L2 | P60 | community/视频生成与理解域包/modules/A06b_视频面收口与形态派生.md |
| 语音识别与合成:M01 | L2 | P40 | community/语音识别与合成域包/modules/A04a_语音口径登记.md |
| 语音识别与合成:M02 | L2 | P60 | community/语音识别与合成域包/modules/A04b_语音面收口与形态派生.md |
| 通用:M10 | L2 | P10 | 04_模块库/通用类/M10_时间推进.md |
| 量化金融:M31 | L2 | P40 | community/量化金融域包/modules/M31_因子与信号口径.md |
| 量化金融:M32 | L2 | P60 | community/量化金融域包/modules/M32_回测与绩效口径.md |
| 音频与音乐生成:M01 | L2 | P40 | community/音频与音乐生成域包/modules/A05a_音频音乐口径登记.md |
| 音频与音乐生成:M02 | L2 | P60 | community/音频与音乐生成域包/modules/A05b_音频面收口与形态派生.md |

## 管线
- P00_通用文档生成管线.md, P01_标准管线.md, P02_校园情感流管线.md, P03_西幻生存流管线.md, P04_轻混装配流管线.md, P05_核心基础流管线.md, P06_技术文档题材装配流管线.md, P07_AI系统域装配流管线.md, P08_量化金融域装配流管线.md, P09_大语言模型装配流管线.md, P11_多模态大模型装配流管线.md, P12_视觉模型装配流管线.md, P13_语音识别与合成装配流管线.md, P14_音频与音乐生成装配流管线.md, P15_视频生成与理解装配流管线.md, P16_图像生成与编辑装配流管线.md, P17_文本生成与创作装配流管线.md, P18_摘要与信息压缩装配流管线.md, P19_机器翻译与本地化装配流管线.md, P21_分类与情感分析装配流管线.md, P90_技术文档生成管线.md

## 协议包
- community/AI系统域包/protocol.yaml, community/分类与情感分析域包/protocol.yaml, community/图像生成与编辑域包/protocol.yaml, community/多模态大模型域包/protocol.yaml, community/大语言模型域包/protocol.yaml, community/技术文档域包/protocol.yaml, community/摘要与信息压缩域包/protocol.yaml, community/文本生成与创作域包/protocol.yaml, community/机器翻译与本地化域包/protocol.yaml, community/校园情感领域包/protocol.yaml, community/校园西幻轻混组合包/protocol.yaml, community/西幻生存领域包/protocol.yaml, community/视觉模型域包/protocol.yaml, community/视频生成与理解域包/protocol.yaml, community/语音识别与合成域包/protocol.yaml, community/通用核心基础包/protocol.yaml, community/量化金融域包/protocol.yaml, community/音频与音乐生成域包/protocol.yaml

## 资产台账键
- TECH_RULES, TECH_TEMPLATES

