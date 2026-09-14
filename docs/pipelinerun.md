# 管线抽象执行（dry-run → GraphSpec）
> ⛔ 操作指令：阅读即执行——本文含可直接执行的命令与判定，勿当资料阅读。
> 最后更新：2026-09-14

## 是什么

**不调模型、不动状态、不写盘**，只用声明跑一遍管线：按层取 `default_modules`，读各模块
`machine_contract` 的 inputs/outputs/events/io_types，产出执行图（steps/edges/tokens/issues/notes）。
此前 NF 只能答"声明自洽吗"，现在能答"跑得通吗"。

## 判决分层（关键）

- **hard**：模块在仓库找不到；依赖的提供方在**严格更后的层**。
- **advisory**：同层依赖序（NF 的 I5 明确"层内顺序由注册表合并裁决"）；依赖/事件由
  **references 跨包闭包或外部域包**提供。

## 怎么用

```bash
python scripts/nf.py pipeline dryrun --pipeline community/西幻生存领域包/pipelines/P03_西幻生存流管线.md
python scripts/nf.py pipeline dryrun --all          # 全仓扫（hard 数即门禁口径）
```

## 边界

- 执行集 = **官方核心基座（registry.json modules[]，恒执行）∪ 管线各层模块**。
- advisory 不判死，但会列出所在模块与事件名，供人工裁决是否为真缺口。
