# 协议件 RFC 头与 supersede 链（rfc）
> ⛔ 操作指令：阅读即执行——本文含可直接执行的命令与判定，勿当资料阅读。
> 最后更新：2026-09-14

## 是什么

01/02/06/07 头部现在带机器可读的版本史行（机制借鉴 HMP 的 RFC 系列）：

```
> **RFC**: NF-0001 · **Category**: Standards Track · **Date**: 2026-09-08 ·
  **Status**: Active · **Supersedes**: — · **Superseded by**: —
```

`protocol/rfc_index.json` 是机读索引；文档头部是真源。

## 怎么用

```bash
python scripts/nf.py rfc          # 列 RFC 件与状态
python scripts/nf.py rfc --json
```

## 判据（可证）

六字段齐备；编号在册唯一；`Category`/`Status` 在词表内；**`Date` 必须等于该文档的「最后更新」**
（禁止两份日期各说各话）；`Status: Superseded` 必须有 `Superseded by`，且指向在册编号；链不得成环。
