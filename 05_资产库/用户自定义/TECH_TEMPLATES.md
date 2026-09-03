# 资产键 TECH_TEMPLATES · 技术文档章节骨架模板
> 05_资产库/用户自定义 扩展资产（P90 技术文档演示，asset_register 登记于 2026-09-03）

## schema
```yaml
key: TECH_TEMPLATES
required_fields: [id, doc_type, sections, required_fields]
field_types:
  id: string
  doc_type: guide|reference|tutorial|note
  sections: [string]
  required_fields: [string]
id_prefix: T9xx   # 用户自定义 900+ 命名空间
```

## 条目
| id | doc_type | sections | required_fields |
| --- | --- | --- | --- |
| T901 | guide | [概述, 快速开始, 概念, 操作步骤, 故障排查, 修订记录] | [概述, 修订记录] |
| T902 | reference | [术语表, 参数表, 返回码表, 示例, 修订记录] | [术语表, 修订记录] |
| T903 | tutorial | [目标, 前置条件, 分步练习, 验证, 修订记录] | [目标, 验证] |

> 访问：asset_get("TECH_TEMPLATES","T901") / asset_query("TECH_TEMPLATES", doc_type=guide)（I4 五接口）