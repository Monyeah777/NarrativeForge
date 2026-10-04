# 外部验证资产（E1 · CCV3 出口样本）
> 最后更新：2026-09-21

## 这是什么

本目录两件 JSON 是 **NF 导出层的真实产物**（P04 轻混装配流 → `--fmt ccv3`），
用于外部验证线 E1（CCV3 → SillyTavern 装载）：`*_chara.json` = 角色卡（含 `character_book`
世界书），`*_world.json` = 独立世界书条目集。

## 怎么重生成（可复现）

```bash
python scripts/nf.py run \
  --pipeline community/校园西幻轻混组合包/pipelines/P04_轻混装配流管线.md \
  --modules 通用类:M00,通用类:M10,M91,M92,通用类:M80 \
  --fmt ccv3 --dest <tmp>
```

> **⚠️ 可复现性缺口（2026-10-02 外部实测发现，未修 · P0）**
> 上面这条命令**重现不出本目录已 committed 的样本**。实测三种模块选择：
> `…M00,M10,M91,M92,M80`（按本文）得 22,111 B / 18,596 B；改带类别前缀
> `…M00,M10,轻混类:M91,轻混类:M92,M80 --seed` 得 31,761 B / 28,134 B；
> 而盘上样本是 11,652 B / 8,691 B。前两种都会报 `勾选模块 M91 / M92 本地不存在，已跳过`。
> 须先补齐「命令 ↔ 制品」的可复现映射（含 store 预置状态与 `--seed` 语义），再重出样本。
> **在此之前，本目录样本视为 stale**——它们的 sha256 见
> `results/docs_external-validation-v2.7.md` §1，且 `desktop/src/core/ccv3_adapter.py`
> 已于同日修复 `scenario` 硬切缺陷，样本尚未按修复后适配器重出。

## 2026-09-21 · 结构性修正（外部实证驱动）

旧样本是**假 v3**：只有顶层 v2 字段 + `spec: chara_card_v3` / `spec_version: "3.0"` 两个头，
**没有 `data` 块**。证据链：

1. SillyTavern 自身写卡逻辑（`src/character-card-parser.js` 的 `write()`）在 CCv3 分支里
   设置的正是 `spec = 'chara_card_v3'` / `spec_version = '3.0'`，而 v3 **内容字段位于 `data`**
   （顶层保留 v2 字段只为向后兼容）；
2. 本仓 `export_schema.check_ccv3_chara` 原判据只校顶层键 → 从未发现该缺陷
   （内部自述 schema ≠ 外部标准）；
3. 判据升级后旧样本立即报 `ccv3 chara 缺必填键: data`。

修正：`ccv3_adapter.map_ir_to_ccv3` 改为输出 **`data` 承载 v3 全字段（权威位）+
顶层 v2 兼容镜像（同源、逐字段相等）**；`export_schema` 同步升级判据（`data` 必填 +
`character_book` 在 `data` 内 + 镜像一致性）；样本按上面的命令重生成。

## 边界（不宣称）

- 本目录只证明**导出格式面**；**GUI 级装载**（SillyTavern 实际导入并跑起来）仍需用户侧执行，
  属外部实测线封存口径，不在本仓门禁内。
- 联网权威校验见 `scripts/check_interop_schemas.py --fetch`（会取 SillyTavern 写卡源码
  比对 `spec` / `spec_version` 字面量与 `data` 结构要求）。
