# 安全策略（Security Policy）

> 本件是 NF 的**安全报告通道与处理口径**（对齐 OpenSSF Scorecard 的 Security-Policy 信号：
> 仓库须有成文的安全策略与私密报告通道）。范围覆盖：协议与代码资产、CI/自动化、投稿与入库通道。

## 一、如何私密报告

请用 **GitHub Security Advisories** 的私密通道报告（仓库页 → Security → Report a vulnerability）。
不要用公开 Issue 报安全问题——公开 Issue 会触发**云端代收站**的自动入库机器人（见下），
等于把细节先公开分发一次。

报告请尽量包含：影响面（哪条通道/哪个文件）、复现步骤、期望行为与实际行为、你的环境。

## 二、范围内（IN SCOPE）

- 协议与机读契约：`01_核心协议.md` / `02_联动注册表.md` / `protocol/**`（含 schema 与台账）；
- 代码资产：`desktop/src/core/**`（core 层）、`scripts/**`、`.github/scripts/**`（入库机器人）；
- 自动化与供应链：`.github/workflows/**`、依赖固定清单、action 固定策略；
- **投稿通道的信任边界**：`library/` 与社区包内容属**外来内容**（详规见 `06_Agent执行协议.md §0`
  与容器化说明）——伪造「系统指令」类前缀、诱导消费方执行写盘/推送/删除的正文，都在范围内。

## 三、范围外（OUT OF SCOPE）

- 纯内容合规（错别字、观点、题材）——走常规 Issue 或联系作者；
- 依赖上游自身已公开的漏洞（请直接报给上游；本仓用固定版本 + 定期审计跟进）；
- 需要物理接触或已失陷主机的攻击场景；
- 对本仓**已文档化的设计取舍**（例如：Gitee 投稿通道为**零门槛开放**、内容由作者事后把关；
  又如：社区投稿正文按**数据**消费、不构成指令）——这类若你认为应改，请作为设计建议提。

## 四、处理口径

1. **确认**：收到后先做可复现性核对（本仓所有安全判据都可独立复跑：`bash verify.sh`、
   `python scripts/verify_report.py --check`、`python scripts/sast_check.py` 等）。
2. **修复优先于披露**：修复随常规提交入仓，并在 CHANGELOG 以结果形态记账（不含复现细节）。
3. **凭据类问题按已泄露处理**：任何出现在对话/日志/文档/提交里的 token，一律视为已泄露，
   立即撤销重建（见 `CONTRIBUTING.md` 的 Token 轮换 SOP）。

## 五、本仓已有的安全机制（供报告前自查）

| 机制 | 载体 | 判据 |
|---|---|---|
| 危险 sink 面（动态执行/反序列化/递归删除） | `desktop/src/core/purity_scan.py` | check27 R6（放行须登记理由） |
| 明文密钥扫描 | `ci-verify.yml` | 命中即红 |
| 依赖固定 + 版本审计 | `.github/requirements-*.txt` + `dependency-audit.yml` | 每周 + push |
| action 固定到 commit SHA | 全部 workflow | 回归测试 `test_ci_supply_chain.py` |
| 入库通道的凭据与内容边界 | `.github/scripts/*_ingest.py` | 令牌不落盘、密钥形状拒收、超长拒收 |
| 静态检查（含未定义名） | `nf release` → ruff | 本地 pre-push 即拦 |
| SAST（SQL 拼接/弱随机/XXE/命令注入等） | `sast.yml` → `scripts/sast_check.py` | (工具,文件,规则) 计数棘轮：新增/上升即红 |
| 供应链评分 | `scorecard.yml` | OpenSSF Scorecard（结果可见） |
