# 45 A1 · techdoc 链载荷补充提案（proposed · 待作者确认）

> ⛔ 操作指令：以下为**提案**，未经作者确认不得写入 protocol/event_registry.json 的 declared。
> 最后更新：2026-09-09

## 现状

5 条 techdoc 事件在正文无显式 `payload:{…}` 结构：doc_structure_ready / doc_delta_committed / intent_received / term_synced / term_conflict_detected。为不编造，维持 pending，本文件给**可确认字段提案**。

## 提案（每条均带依据与开放项）

| 事件 | 来源 | 建议 payload 字段 | 开放项 |
|---|---|---|---|
| doc_structure_ready（M90 发布） | M90 产出 DocState 骨架 | `doc_id, title, version, sections[]` | sections 结构粒度待 M90 补全 |
| doc_delta_committed（M90 发布） | M98 订阅后 `changes=diff(prev,cur)` | `doc_id, prev_ver, new_ver, changes[]` | changes 条目类型待定 |
| intent_received（P90 装载输入闭环） | C3 补发布方时建立 | `intent_id, mode, text` | 字段名待作者定 |
| term_synced（M97 发布） | outputs term_delta/term_status | `delta[], status[], count` | 结构待 M97 补全 |
| term_conflict_detected（M97 发布） | dup definition → status=conflict | `term, definitions[], status` | 冲突形态待定 |

## 落库纪律

- 作者确认（或作者在 M90/M97/M98 事件契约补显式 payload）后，才可把对应条目转 `payload_status: declared`（note 记 `45_M3 提案确认`）。
- 未确认前：注册表保持 pending；本文件只作提案，不算协议正文。
