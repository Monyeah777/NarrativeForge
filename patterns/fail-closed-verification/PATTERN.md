---
id: fail-closed-verification
name: 缺验证器即拒绝，不静默降级
status: active
scope:
  - 代码层
  - 协议层
applies_to:
  - desktop/src/core/attest.py
  - desktop/src/core/driver.py
  - desktop/src/core/approval.py
  - scripts/nf_verify.py
rules:
  - 校验路径遇到"验证器/密钥/锚缺失"时必须判不可信，不得降级成"通过"
  - 降级只允许由使用者显式选择（如改用另一级签名方案），且必须在输出里写明当前信任级
  - 内容被改后旧锚即失效（判 FAIL），不保留"曾经有效"的通行权
evidence:
  - check33
  - docs/attest.md
  - docs/receipts.md
---

## 为什么

安全面上最贵的错误不是"拒绝了好东西"，而是"放过了坏东西"。缺 cosign、缺 hmac 密钥、
缺 allowed_signers 都是**证据缺失**，证据缺失不等于证据成立。

## 怎么用

```bash
# 缺允许签名者 → 如实报"无法校验"（exit 1），而不是"看起来没问题"
python scripts/nf_verify.py --entry NF-1
# 显式提供验证器后才通过
python scripts/nf_verify.py --entry NF-1 --ssh-allowed-signers protocol/demo_signers/allowed_signers
```

## 反例

把"验证器未安装"当成"跳过校验"，或在输出里把 `digest_only` 级说成"已验证"。
