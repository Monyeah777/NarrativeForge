# protocol/generated/ · 协议层生成物（43 A4 golden）

> 由 schema 定义与协议件**确定性生成**、随变更同步提交；与实时重算不一致 = 过期（check31 FAIL）。

## 文件

| 文件 | 内容 | 刷新命令 |
|---|---|---|
| `idl_report.json` | 校验摘要（schema 清单 + 覆盖统计 + registry 模块投影 + 机读契约/管线/协议/台账行） | `PYTHONPATH=desktop/src python desktop/src/core/protocol_golden.py .` |
| `idl_summary.md` | 人读摘要（同一 canonical 数据渲染，逐字节可复现） | 同上 |

## 纪律

- 任何 schema 定义 / 01-07 协议件 / registry / protocol.yaml 变更后：重跑刷新命令并把本目录改动随变更提交（check31 双源一致才绿）。
- 示例与变异自检：真实 23 件机读块 + 8 管线 + 5 协议件即为 golden 示例集；漂移检出由 check28/29 + 单测变异注入常驻（不另建重复样例副本）。
