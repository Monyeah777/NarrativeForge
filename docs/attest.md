# 内容 attestation（`nf attest`）
> ⛔ 操作指令：阅读即执行——本文含可直接执行的命令与判定，勿当资料阅读。
> 最后更新：2026-09-14

## 为什么有这一层

`nf sig` 产出的是**可复现内容摘要**：它证明「两遍算出来一样」，**不证明这份内容没被换过**
——任何人都能重算同一摘要。`nf attest` 在其上补一层**可对外验证**的信封，判的是
**证据强度**，不是内容质量。

## 三级信任（逐级 fail-closed）

| 级 | 命令 | 证明了什么 | 没证明什么 |
|---|---|---|---|
| `digest_only` | `nf attest <file>` | 内容与信封一致（未被改动） | 签发方身份（谁都能重算） |
| `hmac-sha256` | `nf attest <file> --key-file <k>` | 信封由持钥方签发且未改 | 密钥外分发的可信度 |
| `sigstore-keyless` | 外部 `cosign` 锚（`signature.bundle`） | 第三方可验证的签发锚 | —— 缺验证器即**拒绝**，不降级 |

## 用法

```bash
# 生成（缺省 = 01/02/06/07 四件集合；不写盘）
python scripts/nf.py attest
python scripts/nf.py attest 01_核心协议.md --out .attest/01.json --issuer "作者"

# 本地密钥签发（stdlib hmac，无第三方依赖）
python scripts/nf.py attest 01_核心协议.md --key-file <密钥文件> --out .attest/01.json

# 校验（信任级与问题逐条输出；exit 0 = 证据成立）
python scripts/nf.py attest --verify .attest/01.json
python scripts/nf.py attest --verify .attest/01.json --key-file <密钥文件>
```

## 与门禁的关系

attestation **不是** verify 门禁的一部分：门禁判协议/内容是否合格，attestation 判
「这份内容是不是它声称的那份」。二者互不替代；缺锚时 attestation 拒绝，而门禁可仍为绿。
