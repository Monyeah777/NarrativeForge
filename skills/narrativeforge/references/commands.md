# NarrativeForge CLI 命令族

统一入口：`python scripts/nf.py`。可用 `python scripts/nf.py help <cmd>` 查看任意子命令。

## 装配与运行

```bash
python scripts/nf.py demo

python scripts/nf.py run \
  --pipeline community/校园西幻轻混组合包/pipelines/P04_轻混装配流管线.md \
  --modules "通用类:M00,轻混类:M91" \
  --seed --fmt ccv3 --dest out/

python scripts/nf.py assemble "帮我组装一个西幻生存世界的完整版"
python scripts/nf.py assemble "需求" --check 成品.md --save 档案.md --trace trace.json --rounds
```

## 市场与协议

```bash
python scripts/nf.py market --list
python scripts/nf.py market community/西幻生存领域包
python scripts/nf.py market --tier community --json
python scripts/nf.py spec --help
python scripts/nf.py register --help
```

## 资产 / 模块 / 管线

```bash
python scripts/nf.py asset ls
python scripts/nf.py asset inventory
python scripts/nf.py asset verify
python scripts/nf.py asset density
python scripts/nf.py asset usage
python scripts/nf.py asset thickness
python scripts/nf.py asset ledger --refresh

python scripts/nf.py module ls
python scripts/nf.py module status <file>
python scripts/nf.py module verify

python scripts/nf.py pipeline new --help
```

## 导出 / MCP / 治理

```bash
python scripts/nf.py render community/技术文档域包 --fmt agents --dest out/
python scripts/nf.py render community/技术文档域包 --fmt claude --dest out/
python scripts/nf.py render community/技术文档域包 --fmt skill --dest out/

python scripts/nf.py serve <mcp.json>
python scripts/nf.py who-refers <module_id>
python scripts/nf.py impact <module_id>
python scripts/nf.py rename --help
python scripts/nf.py import --help
python scripts/nf.py explain --help
python scripts/nf.py sig --help
python scripts/nf.py diff --help
```

## 质检与发布

```bash
python scripts/nf.py doctor
python scripts/nf.py release
python scripts/nf.py toolface --json
python scripts/nf.py worldmodel --walk
python scripts/nf.py worldmodel --run --state state.json

bash verify.sh
```

## 补全

## 图书馆（library）

```bash
python scripts/nf.py library ls
python scripts/nf.py library show NF-1
python scripts/nf.py library search "雨天"
python scripts/nf.py library reindex          # INDEX 生成区 + ALIAS 投影重生成
python scripts/nf.py library verify           # frontmatter 真源 + 投影一致
python scripts/nf.py library attest NF-1      # 挂 attestation（规范摘要）
python scripts/nf.py library attest NF-1 --ssh-key ~/.ssh/id_ed25519 --ssh-identity me@host  # ssh-sig 非对称锚
python scripts/nf.py library verify --ssh-allowed-signers allowed_signers --ssh-identity me@host
python scripts/nf_verify.py --entry NF-1 --ssh-allowed-signers allowed_signers   # 读者侧独立验证（纯标准库）
python scripts/nf.py library receipts --write # 全馆 Merkle 根 + 逐条 inclusion proof
python scripts/nf.py library receipts --entry NF-1   # 读者侧：只验一条
python scripts/nf.py library deprecate NF-1 / restore NF-1 / supersede NF-1 NF-2
```

## 抽象执行与治理

```bash
python scripts/nf.py pipeline dryrun --pipeline 03_管线库/P01_标准管线.md
python scripts/nf.py pipeline dryrun --all
python scripts/nf.py module types            # I/O 类型面覆盖率 + 可证不匹配（--write 补标）
python scripts/nf.py module signature        # 模块边界冻结（漂移即 FAIL；--write 重签）
python scripts/nf.py module contract         # L0 → L1/L2 机读块 retro-fit（--write 落盘）
python scripts/nf.py module contract --write # retro-fit 落盘（含 outputs 投影：人读契约 + 正文事件契约推导，幂等）
python scripts/nf.py module types --harvest  # 从模块正文收割载荷字段（证据可溯）
python scripts/nf.py module types --backlog  # 类型积压台账（--write 重建）
python scripts/nf.py events                  # 全仓事件背书（订阅必有发布方）
python scripts/nf.py receipts --write        # 协议层回执单根（01–07/schema/baseline）
python scripts/nf.py pipeline dryrun --all --write-advisory   # advisory 分类台账
python scripts/nf.py conformance             # 16 契约 → Merkle 根 + verdict（--write 归档）
python scripts/nf.py approve <路径> --by <人> --note "…"  # 内容绑定批准
python scripts/nf.py approve --verify
```

## 治理声明与机器面（声明 / RFC / driver / 实践包 / 跑分台 / 端点）

```bash
python scripts/nf.py driver                  # 列工作流 → MCP 提示/工具/文本 fallback
python scripts/nf.py driver assemble         # 解析某工作流该走哪条路（MCP vs fallback）
python scripts/nf.py rfc                     # 协议件 RFC 版本史（编号/Category/Date/Status/supersede 链）
python scripts/nf.py patterns ls             # 实践包清单
python scripts/nf.py patterns show fail-closed-verification
python scripts/nf.py patterns for docs/ai-menu.md   # 反向查：该文件适用哪些 pattern
python scripts/nf.py patterns verify         # 格式 + 可证性机检
python scripts/nf.py patterns reindex        # 重建 patterns/INDEX 投影
python scripts/nf.py bench run --case desktop/tests/fixtures/benchmark/suite/p03-western-cross --model claude
python scripts/nf.py bench compare runs.json # 多跑逐维均值/极差/相对最佳回落
python scripts/nf.py bench report runs.json  # 人读跑分报告
python scripts/nf.py endpoint                # 服务端点契约（status: proposed；maps_to 须指向现存能力）
```

一致性**声明**在 `protocol/CONFORMANCE.md`（版本表 + scope 白名单 + 显式排除清单）；
`nf conformance` 会把它作为 `declaration` 契约逐条与真源比对（声明了真源没有的规范项即 FAIL）。
指令档（组装指令包 / `AI_ROUTING.md` / `docs/ai-menu.md`）头部带 `DRIVER OVERRIDE` 块：
**有 MCP 实现就走 MCP；派发失败即停，禁止回退成文本步骤**（真源 `protocol/driver.json`）。

## 质量与遥测

```bash
python scripts/nf.py attest 01_核心协议.md --out .attest/01.json   # 三级信任签名
python scripts/nf.py score --baseline protocol/score_baseline.json # 基线相对回归评分
python scripts/nf.py lint --fix --dry-run                          # 机械修复（不写盘）
python scripts/nf.py lint --prose                                  # 正文 lint（去 AI 味）
python scripts/nf.py license                                       # 图书馆许可证门
python scripts/nf.py telemetry trace.json --otlp                   # 遥测 semconv 映射
python scripts/nf.py lsp                                           # 最小 LSP 服务器（stdio）
```

## 补全

```bash
python scripts/nf.py completion bash >> ~/.bashrc
python scripts/nf.py completion zsh >> ~/.zshrc
python scripts/nf.py completion fish > ~/.config/fish/completions/nf.fish
```

退出码约定：`0` 成功，`1` 运行/校验失败，`2` 用法错误。
