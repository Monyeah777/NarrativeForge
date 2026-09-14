# 演示签名者（demo signers）
> 最后更新：2026-09-14

**这不是作者身份，是用于演示「馆藏条目签名锚」全链的**一次性**密钥对**——私钥不入库
（在本地 `.rivet/scratch/nf_demo_ssh/`），此处只公布**公钥与 allowed_signers**，
让任何读者都能端到端复现验证：

```bash
# 读者侧独立验证（纯标准库，不依赖 NF 代码）
python scripts/nf_verify.py --entry NF-1 --ssh-allowed-signers protocol/demo_signers/allowed_signers
# 仓库侧同语义校验
python scripts/nf.py library verify --ssh-allowed-signers protocol/demo_signers/allowed_signers --ssh-identity nf-demo@local
```

**生产使用**：作者应以**自己的密钥**重签并公布对应公钥：
`python scripts/nf.py library attest <编号> --ssh-key <你的私钥> --ssh-identity <你的身份>`
（或改用 `--key-file` 的 hmac 级）。演示锚只证明「机制可跑通」，不构成任何身份背书。
