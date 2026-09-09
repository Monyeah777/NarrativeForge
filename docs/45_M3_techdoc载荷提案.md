# 45 A1 · techdoc 链载荷补充（proposed → 已确认 · 2026-09-09）

> ⛔ 操作指令：以下提案已于 2026-09-09 经作者确认并写入 registry（declared 30/30）；改字段须走 schema/registry 纪律。
> 最后更新：2026-09-09

## 现状（已收口）

5 条 techdoc 事件原无显式 `payload:{…}` 结构；按本提案字段经作者确认后全部转 `payload_status: declared`（每字段 `untyped`，类型待正文补全后收窄）。

## 提案（每条均带依据与开放项）

| 事件 | 来源 | 建议 payload 字段 | 开放项 |
|---|---|---|---|
| doc_structure_ready（M90 发布） | M90 产出 DocState 骨架 | `doc_id, title, version, sections[]` | sections 结构粒度待 M90 补全 |
| doc_delta_committed（M90 发布） | M98 订阅后 `changes=diff(prev,cur)` | `doc_id, prev_ver, new_ver, changes[]` | changes 条目类型待定 |
| intent_received（P90 装载输入闭环） | C3 补发布方时建立 | `intent_id, mode, text` | 字段名待作者定 |
| term_synced（M97 发布） | outputs term_delta/term_status | `delta[], status[], count` | 结构待 M97 补全 |
| term_conflict_detected（M97 发布） | dup definition → status=conflict | `term, definitions[], status` | 冲突形态待定 |

## 落库纪律

- 确认已落库（note 记 `45_M3 techdoc 载荷提案经作者确认`）。
- 后续：建议在 M90/M97/M98 事件契约补显式 payload 以收窄 untyped 类型。
