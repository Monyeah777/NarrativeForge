# NF Patterns 索引
> 最后更新：2026-09-14

> 真源 = 各 `patterns/<name>/PATTERN.md` 的 frontmatter；下表为**投影**（`nf patterns reindex` 重建，手改会被覆盖）。

<!-- BEGIN GENERATED: patterns-index -->

## Pattern 登记表（由各包 frontmatter 生成，勿手改）

| id | 名称 | 状态 | 适用面 | 规则数 |
|---|---|---|---|---|
| dependency-direction | 依赖方向：需要低层能力时由调用方注入 | active | 代码层 | 3 |
| error-message-guidance | 报错必须带修复指引 | active | 代码层、协议层 | 3 |
| fail-closed-verification | 缺验证器即拒绝，不静默降级 | active | 代码层、协议层 | 3 |
| predicate-single-source | 扫描面收敛：一条判据只准有一处实现 | active | 代码层 | 3 |
| single-source-truth | 真源 + 投影，禁止双写 | active | 协议层、资产层 | 3 |
| verifier-must-run | 判据必须接线：没跑过的判据不算判据 | active | 代码层 | 3 |
| worktree-vs-index | 门禁看工作区、git 看索引——两处口径先对齐 | active | 代码层 | 3 |

> 真源 = 各包 `PATTERN.md` 的 frontmatter；本表为投影（`nf patterns reindex` 重建）。

<!-- END GENERATED: patterns-index -->
