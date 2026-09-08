# 迁移指南 · 基于 `nf sig` / `nf diff`（41 波C D5 · C2 产物衍生文档位）

> 用途：协议/方案文档演进与迁移核查的衍生工具文档位——C2 版本差异检测产物的「怎么用」入口。

## 一、何时用

- 大版本升级前：先 `python scripts/nf.py sig --verify` 确认 01-36 基线签名可复现（check25）。
- 改动某协议/方案文档后、提交前：对照旧提交跑 `nf diff`，判断改动是字段级/引用级/破坏级。
- 收到迁移要求（如协议版本 bump、模块改号）：用 diff 定位受影响引用，再按 `nf explain` 修复对应 check。

## 二、标准流程

1. **基线**：`python scripts/nf.py sig <旧文件> <新文件> --json` 或全量 `sig --verify`。
2. **差异**：`python scripts/nf.py diff 01_核心协议.md 36_v2.5.0_基础层深化续方案.md`
   - 输出逐字段差异（字段变更 / 新增 / 移除）+ 判定（破坏 / 需评审 / 兼容）。
   - 判定规则：文档编号变更 = 破坏；引用/章节移除 = 需评审；仅版本演进 = 兼容。
3. **修复指引**：`python scripts/nf.py explain <check>`（如 check24/25/26）取「缺什么/补什么/示例」。
4. **验收**：`bash verify.sh` 全绿（check1-26 PASS=39 基线）方可提交；迁移记录进 CHANGELOG 归档。

## 三、与既有门禁的关系

`nf diff` 是**编译期冲突发现**（录入时），verify check25 是其自动闸门（可复现）；两者互补但不替代
check13（协议版本一致性/迁移完整性四步）与 CHANGELOG 归档——协议层真迁移仍走 02 §9.3。
