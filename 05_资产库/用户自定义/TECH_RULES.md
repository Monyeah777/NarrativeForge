# 资产键 TECH_RULES · 技术文档规范校验规则
> 05_资产库/用户自定义 扩展资产（P90 技术文档演示，asset_register 登记于 2026-09-03）

## schema
```yaml
key: TECH_RULES
required_fields: [id, rule_type, check, action]
field_types:
  id: string
  rule_type: structure|terminology|reference|revision
  check: string
  action: warn|fail
id_prefix: R9xx   # 用户自定义 900+ 命名空间
```

## 条目
| id | rule_type | check | action |
| --- | --- | --- | --- |
| R901 | structure | 每个章节至少 1 个 body_ref，无孤儿节标题 | fail |
| R902 | terminology | 术语首现须登记 terms 表，全文同词同义 | warn |
| R903 | reference | link_refs / code_refs 全部闭合（无死链/悬空引用） | fail |
| R904 | revision | 每次变更须追加修订记录（ver/date/change） | warn |

> 访问：asset_get("TECH_RULES","R901") / asset_match("TECH_RULES", DocState)（I4 五接口）