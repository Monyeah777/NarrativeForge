"""内容外挂签名 / attestation（内部差距实证：knowledge_sig 只证明「两遍算得出一样」，
即自证一致，**不能证明这份内容没被第三方换过**——仓库全域实测 sigstore/attestation/
cosign/gpg 命中 0）。

本模块把内容摘要升级为**可对外验证的 attestation envelope**，三级信任，逐级 fail-closed：

1. `digest_only` —— 可复现内容摘要（sha256/字节数/行数 + 信封摘要）。
   证明「内容与信封一致」；**不证明诚实性**（任何人都能重算）。
2. `hmac-sha256` —— 本地密钥 HMAC（**纯标准库** hashlib/hmac，不引第三方）。
   持有密钥者可在离线环境验证「信封确由持钥方签发且未被改动」。
3. `sigstore-keyless` —— 外挂锚（Sigstore/cosign）。
   本模块**不实现密码学**：只检测外部验证器（`cosign`）并调用；验证器缺失即
   **拒绝**（不静默降级成 digest_only）——缺锚 = 不可信，而非「默认通过」。

纪律（对齐 core 零第三方依赖红线）：stdlib-only；外部锚是可选外挂，装不装由消费方裁决。
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import shutil
import subprocess  # nosec B404/B603/B607 —— 调用 ssh-keygen/git/hf（argv 列表、无 shell、路径经 which 解析）
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

SCHEMA = "nf-attest/1"

#: 支持的签名方案（外挂锚 = 外部验证器；未知方案一律 fail-closed）
SCHEME_HMAC = "hmac-sha256"
SCHEME_SIGSTORE = "sigstore-keyless"
SCHEME_SSH = "ssh-sig"
#: ssh-sig 的签名命名空间（ssh-keygen -Y sign -n）——与密钥其他用途隔离
SSH_NAMESPACE = "nf-attest"
#: ssh-sig 的签名载荷格式（读者侧按同一格式重建，必须逐字一致）
SSH_PAYLOAD_PREFIX = "nf-attest-v1\nsubject_sha256:"

#: 默认锚定的内容面 = 与 `nf sig` 同源的根级编号文档
DEFAULT_SUBJECTS = ("01_核心协议.md", "02_联动注册表.md",
                    "06_Agent执行协议.md", "07_官方核心出厂与社区预设导航.md")


def canonical(obj: Any) -> bytes:
    """规范化 JSON 编码（键排序 + 紧凑分隔符）——摘要稳定的前提。"""
    return json.dumps(obj, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":")).encode("utf-8")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def subject_of(path: str, root: str = ".") -> Dict[str, Any]:
    """内容主体摘要：相对路径 + sha256 + 字节数 + 行数（全部可复现）。"""
    abs_path = os.path.join(root, path)
    with open(abs_path, "rb") as fh:
        raw = fh.read()
    text = raw.decode("utf-8")
    rel = path.replace("\\", "/")
    return {
        "path": rel,
        "sha256": _sha256(raw),
        "bytes": len(raw),
        "line_count": len(text.replace("\r\n", "\n").splitlines()),
    }


def envelope_digest(att: Dict[str, Any]) -> str:
    """信封摘要 = subject + producer + issued_at 的规范化摘要（排除 signature 块本身）。"""
    base = {k: att.get(k) for k in ("schema", "subject", "producer", "issued_at")}
    return _sha256(canonical(base))


def build(path: str, root: str = ".", issuer: str = "",
          subject: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """构造未签名 attestation（digest_only 级）。"""
    subj = subject if subject is not None else subject_of(path, root)
    att = {
        "schema": SCHEMA,
        "subject": subj,
        "producer": {"tool": "nf", "issuer": issuer or ""},
        "issued_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    att["envelope_digest"] = envelope_digest(att)
    return att


def sign_hmac(att: Dict[str, Any], key: bytes) -> Dict[str, Any]:
    """本地密钥签发（stdlib hmac-sha256）——签名绑定信封摘要。"""
    if not key:
        raise ValueError("HMAC 签发需要非空密钥（修复指引：--key-file 指向密钥文件）")
    out = dict(att)
    mac = hmac.new(key, att["envelope_digest"].encode("utf-8"),
                   hashlib.sha256).hexdigest()
    out["signature"] = {"scheme": SCHEME_HMAC, "mac": mac,
                        "key_id": _sha256(key)[:16]}
    return out


def have_external_verifier(tool: str = "cosign") -> bool:
    """外挂锚验证器是否在场（Sigstore 锚 = 外部 CLI，不随 core 分发）。"""
    return shutil.which(tool) is not None


def _which(tool: str, purpose: str) -> str:
    """把外部 CLI 解析成**绝对路径**（逐行审查修正：裸名走 PATH 有 cwd 劫持面）。

    缺失 → ValueError（fail-closed，带可执行修复指引）。
    """
    exe = shutil.which(tool)
    if not exe:
        raise ValueError("%s 需要外部命令 %s，但 PATH 中找不到（修复指引：先安装 %s 后重试，"
                         "或改用 --key-file 的 hmac 级）" % (purpose, tool, tool))
    return exe


def verify_external(att: Dict[str, Any], tool: str = "cosign") -> Tuple[bool, List[str]]:
    """调用外部验证器校验 sigstore 锚；验证器缺失 → **拒绝**（不降级）。"""
    if not have_external_verifier(tool):
        return False, ["外挂锚验证器缺失（%s 未安装）→ fail-closed 拒绝，"
                       "不降级为 digest_only（修复指引：装 cosign 后重验，"
                       "或改用 --key-file 的 hmac 级）" % tool]
    sig = (att.get("signature") or {})
    bundle = sig.get("bundle")
    if not bundle or not os.path.exists(bundle):
        return False, ["外挂锚缺 bundle 实体（signature.bundle 指向不存在）"
                       "（修复指引：随 attestation 一并分发签名 bundle）"]
    proc = subprocess.run([shutil.which(tool) or tool, "verify-blob", "--bundle", bundle, bundle],  # nosec B404/B603/B607 —— 调用 ssh-keygen/git/hf（argv 列表、无 shell、路径经 which 解析）
                          capture_output=True, text=True)
    if proc.returncode != 0:
        return False, ["外挂锚校验失败：%s" % (proc.stderr or proc.stdout).strip()[:300]]
    return True, []


def verify(att: Dict[str, Any], root: str = ".",
           key: Optional[bytes] = None) -> Tuple[bool, List[str], str]:
    """校验 attestation → (ok, issues, level)。

    ok=False 一律表示「不可信」，绝不因缺证据而放行——本函数判的是**证据强度**，
    不是内容质量：「可复现」不等于「诚实」。
    """
    issues: List[str] = []
    if not isinstance(att, dict) or att.get("schema") != SCHEMA:
        return False, ["attestation schema 不匹配（期望 %s）" % SCHEMA], "invalid"
    subj = att.get("subject") or {}
    path = subj.get("path")
    if not path:
        return False, ["attestation 缺 subject.path"], "invalid"
    try:
        live = subject_of(path, root)
    except OSError as exc:
        return False, ["主体不可读：%s（%s）" % (path, exc)], "invalid"
    for field in ("sha256", "bytes", "line_count"):
        if live.get(field) != subj.get(field):
            issues.append("主体漂移：%s 记录=%s 实测=%s"
                          % (field, subj.get(field), live.get(field)))
    if issues:
        return False, issues, "digest_only"
    if att.get("envelope_digest") != envelope_digest(att):
        return False, ["信封摘要不一致（attestation 自身被改动）"], "digest_only"
    sig = att.get("signature")
    if not sig:
        return True, [], "digest_only"
    scheme = sig.get("scheme")
    if scheme == SCHEME_HMAC:
        if key is None:
            return False, ["缺密钥，无法校验 hmac 签名（修复指引：--key-file）"], "hmac-sha256"
        expect = hmac.new(key, att["envelope_digest"].encode("utf-8"),
                          hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expect, str(sig.get("mac") or "")):
            return False, ["hmac 签名不匹配（密钥不符或信封被改）"], "hmac-sha256"
        return True, [], "hmac-sha256"
    if scheme == SCHEME_SIGSTORE:
        ok, ext_issues = verify_external(att)
        return ok, ext_issues, "sigstore-keyless"
    return False, ["未知签名方案：%s（支持：%s / %s）"
                   % (scheme, SCHEME_HMAC, SCHEME_SIGSTORE)], "unsupported"


def sign_digest_hmac(subject_digest: str, key: bytes, issuer: str = "") -> Dict[str, Any]:
    """对**已算好的内容摘要**签发 HMAC 锚（供馆藏条目等"摘要已在 frontmatter"的场景）。

    与 `sign_hmac`（签信封）区分：这里签的是条目规范摘要，锚可独立于信封存在。
    """
    if not key:
        raise ValueError("HMAC 签锚需要非空密钥（修复指引：--key-file <密钥文件>）")
    if not re.fullmatch(r"[0-9a-fA-F]{64}", (subject_digest or "").strip()):
        raise ValueError("待签摘要非法（修复指引：先算条目规范摘要，64 位十六进制）")
    mac = hmac.new(key, subject_digest.strip().lower().encode("utf-8"),
                   hashlib.sha256).hexdigest()
    return {"scheme": SCHEME_HMAC, "mac": mac, "key_id": _sha256(key)[:16],
            "issuer": issuer or ""}


def ssh_payload(subject_digest: str) -> bytes:
    """ssh-sig 的签名载荷（读者侧必须逐字重建同一字节序列）。"""
    return (SSH_PAYLOAD_PREFIX + (subject_digest or "").strip().lower() + "\n").encode("utf-8")


def sign_digest_ssh(subject_digest: str, key_path: str, identity: str,
                    ns: str = SSH_NAMESPACE, workdir: str = "") -> Dict[str, Any]:
    """用 `ssh-keygen -Y sign` 对摘要载荷签名（真实非对称签名，读者侧只需 ssh-keygen）。"""
    if not have_external_verifier("ssh-keygen"):
        raise ValueError("缺 ssh-keygen → 无法签发 ssh-sig 锚（fail-closed，不做假锚）"
                         "（修复指引：安装 OpenSSH 或改用 --key-file 的 hmac 级）")
    if not os.path.isfile(key_path):
        raise ValueError("签名私钥不存在：%s（修复指引：--ssh-key <私钥路径>）" % key_path)
    if not identity.strip():
        raise ValueError("ssh-sig 需要身份标识（修复指引：--ssh-identity <principal>）")
    import tempfile

    base = workdir or tempfile.mkdtemp(prefix="nf_ssh_")
    os.makedirs(base, exist_ok=True)
    payload_path = os.path.join(base, "payload.txt")
    with open(payload_path, "wb") as fh:
        fh.write(ssh_payload(subject_digest))
    # stdin=DEVNULL：密钥若带口令，ssh-keygen 会等输入（实测会挂住）——
    # 这里让它**快速失败**而不是阻塞调用方。
    proc = subprocess.run([_which("ssh-keygen", "ssh-sig 签名"),  # nosec B404/B603/B607 —— 调用 ssh-keygen/git/hf（argv 列表、无 shell、路径经 which 解析）
                           "-Y", "sign", "-f", key_path, "-n", ns,
                           payload_path], capture_output=True, text=True,
                          stdin=subprocess.DEVNULL)
    if proc.returncode != 0:
        raise ValueError("ssh-keygen 签名失败：%s"
                         % (proc.stderr or proc.stdout).strip()[:200])
    sig = payload_path + ".sig"
    if not os.path.isfile(sig):
        raise ValueError("ssh-keygen 未产出签名文件（修复指引：检查 ssh-keygen 版本 ≥8.9）")
    pub = key_path + ".pub"
    fingerprint = ""
    if os.path.isfile(pub):
        fp = subprocess.run([_which("ssh-keygen", "ssh-sig 指纹"), "-lf", pub],  # nosec B404/B603/B607 —— 调用 ssh-keygen/git/hf（argv 列表、无 shell、路径经 which 解析）
                            capture_output=True, text=True)
        if fp.returncode == 0 and fp.stdout.split():
            fingerprint = fp.stdout.split()[1]
    return {"scheme": SCHEME_SSH, "ns": ns, "identity": identity.strip(),
            "sig_file": sig, "fingerprint": fingerprint,
            "payload_sha256": _sha256(ssh_payload(subject_digest))}


def verify_ssh_anchor(subject_digest: str, anchor: Dict[str, Any],
                      allowed_signers: str, identity: str) -> Tuple[bool, List[str]]:
    """`ssh-keygen -Y verify` 校验 ssh-sig 锚；缺验证器/缺 allowed_signers 一律拒绝。"""
    if not have_external_verifier("ssh-keygen"):
        return False, ["缺 ssh-keygen → ssh-sig 锚不可校验（fail-closed）"]
    if not allowed_signers or not os.path.isfile(allowed_signers):
        return False, ["缺 allowed_signers（修复指引：--ssh-allowed-signers <文件>；"
                       "格式 `<身份> <公钥>`）"]
    sig_file = anchor.get("sig_file") or ""
    if not sig_file or not os.path.isfile(sig_file):
        return False, ["缺签名文件实体：%s（修复指引：随锚一并分发 .sig 文件）" % sig_file]
    ns = str(anchor.get("ns") or SSH_NAMESPACE)
    ident = identity or str(anchor.get("identity") or "")
    if not ident:
        return False, ["缺验签身份（修复指引：--ssh-identity <principal>）"]
    # 注意：必须按**字节**喂 stdin——Windows 文本模式会把 \n 翻成 \r\n，
    # 导致验签载荷与签名时不一致（实测踩过：incorrect signature）。
    try:
        exe = _which("ssh-keygen", "ssh-sig 验签")
    except ValueError as exc:
        return False, [str(exc)]
    proc = subprocess.run([exe, "-Y", "verify", "-f", allowed_signers,  # nosec B404/B603/B607 —— 调用 ssh-keygen/git/hf（argv 列表、无 shell、路径经 which 解析）
                           "-I", ident, "-n", ns, "-s", sig_file],
                          input=ssh_payload(subject_digest),
                          capture_output=True)
    out = (proc.stderr or proc.stdout or b"").decode("utf-8", "replace").strip()[:200]
    if proc.returncode != 0:
        return False, ["ssh-sig 校验失败：%s" % out]
    return True, []


def verify_digest_anchor(subject_digest: str, anchor: Dict[str, Any],
                         key: Optional[bytes] = None,
                         ssh_ctx: Optional[Dict[str, str]] = None
                         ) -> Tuple[bool, List[str], str]:
    """校验摘要锚 → (ok, issues, level)；缺验证器一律 fail-closed（不静默放行）。

    ssh_ctx = {"allowed_signers": <path>, "identity": <principal>}
    """
    scheme = (anchor or {}).get("scheme")
    if not scheme:
        return False, ["锚缺 scheme（修复指引：nf library attest <编号> --key-file <密钥>）"], "none"
    if scheme == SCHEME_HMAC:
        if key is None:
            return False, ["锚为 hmac 级但未提供密钥 → 无法校验"
                           "（修复指引：--key-file <同一密钥>）"], "hmac-sha256"
        expect = hmac.new(key, (subject_digest or "").strip().lower().encode("utf-8"),
                          hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expect, str(anchor.get("mac") or "")):
            return False, ["hmac 锚不匹配（密钥不符，或内容/摘要已改）"], "hmac-sha256"
        return True, [], "hmac-sha256"
    if scheme == SCHEME_SSH:
        ctx = ssh_ctx or {}
        ok, issues = verify_ssh_anchor(subject_digest, anchor,
                                      ctx.get("allowed_signers", ""),
                                      ctx.get("identity", ""))
        return ok, issues, "ssh-sig"
    if scheme == SCHEME_SIGSTORE:
        return False, ["sigstore 锚需外部验证器，当前不可校验"
                       "（修复指引：装 cosign 后重验，或改用 hmac / ssh-sig 锚）"], "sigstore-keyless"
    return False, ["未知锚方案：%s（支持：%s / %s / %s）"
                   % (scheme, SCHEME_HMAC, SCHEME_SSH, SCHEME_SIGSTORE)], "unsupported"


def read_key_file(path: str) -> bytes:
    """读本地签名密钥（调用方负责权限；空文件视为无效）。"""
    with open(path, "rb") as fh:
        key = fh.read().strip()
    if not key:
        raise ValueError("密钥文件为空：%s（修复指引：写入 ≥16 字节随机密钥）" % path)
    return key


def dumps(att: Dict[str, Any]) -> str:
    """稳定序列化（便于入仓/分发对照）。"""
    return json.dumps(att, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
