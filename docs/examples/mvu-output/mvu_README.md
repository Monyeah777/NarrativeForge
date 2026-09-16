# MVU 变量模板（由 NarrativeForge 导出）

- 生成器：mvu_adapter/0.1 ｜ 目标格式锚点核对日期：2026-09-16
- 契约来源：https://raw.githubusercontent.com/Lunacaty/MVU-Maker/HEAD/README.md

## 产物

| 文件 | 内容 | 状态 |
|---|---|---|
| mvu_variables.json | 变量表 + 初值 + checks + 相位 + 不变式 + 溯源 digest | 可核 |
| mvu_worldbook.json | 世界书条目草案（`[InitVar]` / `[mvu_update]` ×2） | **draft** |

## 如实声明

- **未在真实 SillyTavern 实测**，不声称兼容；条目位置参数与数组硬要求**未核对**，故 worldbook 保持 draft。
- 正则五件套**未产出**（组成未核对）。
- 未核对清单：stat_data 树路径规则、条目位置参数 atDepth/depth/order、entries / tavern_helper.scripts 数组硬要求、正则五件套组成、变量列表条目形态（蓝灯 @D0）、base64/chara 分发细节
