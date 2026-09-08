# protocol/EXTENSION.md · 协议扩展策略与变更影响分层（43 A3）

> **定位**：明确协议「什么算字段级新增、什么必须结构 bump」，并把 `nf diff` 的判定从兼容性一维升为「兼容判定 + 影响度三档」。任何对 01/02/03/04/05/06/07/registry/machine_contract/schema 定义的变更，先查本表定影响度，再按对应流程走。
> **版本红线**：registry_schema_version / protocol.schema_version / machine_contract.schema 独立演进（01 §7 V3）；字段级新增不 bump（V1 只增不删）；结构性变更必须 bump + 迁移记录（V2）。

## 判据表

| 影响度 | 判定 | 示例 | 处理 |
|---|---|---|---|
| editorial | 纯措辞/注释/说明/值域注解性文字；无任何机器字段增删改义 | 错误信息文案、注释补全、描述语改写 | 走既有文档纪律；不涉版本字段；`nf diff` 仅 editorial |
| additive | 字段级新增：新可选/必填字段、枚举值域新增、键新增（不删不改既有名） | 43 A1 把 `techdoc` 加进管线 type 值域；43 A2 给 machine_contract/协议包加 `conformance` 位 | schema 定义同步补 `properties`；V1 只增不删；**不 bump** registry/protocol 版本；迁移记录可选（复杂新增建议留档） |
| bump | 结构性：字段删除/改义/重排、实体拆分合并、引用语义/装配语义变化、版本槽位升级 | registry_schema_version v1→v2（02 §9.3 首例）；protocol.schema_version v1→v2（references 引入） | 必须 bump 相应版本字段 + 按 01 §7 迁移实操四步留档（现状快照/bump 声明/迁移说明/校验回读）；check30 拦截无迁移记录的 bump diff |

## `nf diff` 影响度（与 verdict 互补）

- `verdict` = 兼容判定（破坏/需评审/兼容——41 波C C2 保留不改语义）。
- `impact` = 影响度三档（本表）：`bump`（doc 编号变更 / 引用或章节移除 / 版本槽位变化）> `additive`（纯新增引用/章节/schema 名）> `editorial`（仅正文/计数/摘要变化）。CLI 打印在 `判定` 下方。

## 三档回放实证（历史变更抽查 3+1 例）

| 历史变更 | 落点 | 影响度 | 依据 |
|---|---|---|---|
| registry_schema_version v1→v2（机读投影 registry.json 引入） | 02 §9.3 | bump | V2 结构性新增投影实体；四步迁移记录在场 |
| protocol.schema_version v1→v2（references 组合引用通道引入） | 01 §7 迁移记录 | bump | V2 结构性新增跨包引用语义；四步迁移记录在场 |
| 模块头 machine_contract 机读化（九键投影） | 01 §1.1 + 模块文档 | additive | 模块文档字段级新增（01 迁移记录 1.2：V1 只增不删，非 V2 bump） |
| 管线 type 值域补 `techdoc`（P90/P06 实际使用暴露） | 01 §2 + pipeline.schema.json | additive | 值域新增非结构（43 A1 check28 收口） |

> 以上为 EXTENSION 判据的回放校验样本：凡归档为 bump 的均有迁移记录、凡 additive 的均未 bump 版本字段——check30 + check13 常驻守住该边界。
