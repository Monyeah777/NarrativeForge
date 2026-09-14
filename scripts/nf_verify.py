#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""NF 馆藏**读者侧独立验证器**（纯标准库，不 import NF 的任何模块）。

用途：读者只拿到「回执（RECEIPTS.json 里的一条）+ 条目内容」，就能自己判断
「这条属于本馆、且没被换过」——不依赖 NF 的代码、不取全馆、不需要联网。

用法：
  python nf_verify.py --entry NF-1 \\
      [--receipts library/RECEIPTS.json] [--entry-file library/NF-1.md] \\
      [--key-file <hmac 密钥>] \\
      [--ssh-allowed-signers <文件> --ssh-identity <principal>] \\
      [--json]

复现的算法（与仓库实现逐字一致，RFC 6962 域分隔）：
  规范摘要  = SHA-256( 条目文本剔除 attestation/attested_at/anchor_* 行后的字节 )
  叶        = SHA-256( 0x00 ‖ UTF-8( {"id":…,"digest":…} 的紧凑规范 JSON ) )
  内部节点  = SHA-256( 0x01 ‖ 左 ‖ 右 )
  折叠      = 按 proof 的 side 逐层合并，结果应等于回执里的 root

退出码：0 = 全部可验证项通过；1 = 有校验失败或不可验证（fail-closed）；2 = 用法错误。
"""
from __future__ import annotations

import argparse
import hashlib
import hmac as _hmac
import json
import os
import re
import subprocess
import sys

SCHEMA = "nf-receipts/1"
SSH_NS = "nf-attest"
SSH_PAYLOAD_PREFIX = "nf-attest-v1\nsubject_sha256:"
_EXCLUDE = re.compile(r"^(attestation|attested_at|anchor_[a-z_]+)\s*:")


def canonical_bytes(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":")).encode("utf-8")


def leaf_of(entry_id: str, digest: str) -> bytes:
    return hashlib.sha256(b"\x00" + canonical_bytes({"id": entry_id,
                                                     "digest": digest})).digest()


def node(left: bytes, right: bytes) -> bytes:
    return hashlib.sha256(b"\x01" + left + right).digest()


def fold(leaf: bytes, proof) -> bytes:
    cur = leaf
    for step in proof:
        sib = bytes.fromhex(step["hash"])
        cur = node(sib, cur) if step["side"] == "left" else node(cur, sib)
    return cur


def entry_digest(path: str) -> str:
    """与 `nf library entry_digest` 同规则：剔除签名/锚字段行后取 SHA-256。"""
    with open(path, "rb") as fh:
        text = fh.read().decode("utf-8").replace("\r\n", "\n")
    kept = [ln for ln in text.split("\n") if not _EXCLUDE.match(ln)]
    return hashlib.sha256("\n".join(kept).encode("utf-8")).hexdigest()


def verify_hmac(digest: str, anchor, key: bytes):
    expect = _hmac.new(key, digest.strip().lower().encode("utf-8"),
                       hashlib.sha256).hexdigest()
    return (_hmac.compare_digest(expect, str(anchor.get("mac") or "")),
            "hmac 锚匹配" if _hmac.compare_digest(expect, str(anchor.get("mac") or ""))
            else "hmac 锚不匹配（密钥不符或摘要被改）")


def verify_ssh(digest: str, anchor, allowed_signers: str, identity: str):
    if not allowed_signers or not os.path.isfile(allowed_signers):
        return False, "缺 allowed_signers（--ssh-allowed-signers）"
    sig = str(anchor.get("sig_file") or "")
    if not sig or not os.path.isfile(sig):
        return False, "缺签名文件：%s" % (sig or "(未记录)")
    ident = identity or str(anchor.get("identity") or "")
    payload = (SSH_PAYLOAD_PREFIX + digest.strip().lower() + "\n").encode("utf-8")
    proc = subprocess.run(["ssh-keygen", "-Y", "verify", "-f", allowed_signers,
                           "-I", ident, "-n", str(anchor.get("ns") or SSH_NS),
                           "-s", sig],
                          input=payload, capture_output=True)
    msg = (proc.stderr or proc.stdout or b"").decode("utf-8", "replace").strip()
    return (proc.returncode == 0, "ssh-sig 匹配" if proc.returncode == 0
            else "ssh-sig 校验失败：%s" % msg[:160])


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        prog="nf_verify", description="NF 馆藏读者侧独立验证器（纯标准库）")
    ap.add_argument("--entry", required=True, help="馆藏编号（如 NF-1）")
    ap.add_argument("--receipts", default="library/RECEIPTS.json",
                    help="回执文件（缺省 library/RECEIPTS.json）")
    ap.add_argument("--entry-file", default="",
                    help="条目内容文件（缺省 library/<编号>.md；无则只验包含关系）")
    ap.add_argument("--key-file", default="", help="hmac 锚校验用密钥文件")
    ap.add_argument("--ssh-allowed-signers", default="",
                    help="ssh-sig 锚校验用 allowed_signers 文件")
    ap.add_argument("--ssh-identity", default="", help="ssh-sig 锚的 principal")
    ap.add_argument("--json", action="store_true", help="输出结构化 JSON")
    args = ap.parse_args(argv)

    try:
        with open(args.receipts, encoding="utf-8") as fh:
            doc = json.load(fh)
    except (OSError, ValueError) as exc:
        print("✗ 回执不可读：%s" % exc, file=sys.stderr)
        return 2
    if doc.get("schema") != SCHEMA:
        print("✗ 回执 schema 不匹配（期望 %s）" % SCHEMA, file=sys.stderr)
        return 2
    want = args.entry.strip().lower()
    hit = next((e for e in doc.get("entries") or []
                if str(e.get("id", "")).lower() == want), None)
    if hit is None:
        print("✗ 回执中没有该条目：%s" % args.entry, file=sys.stderr)
        return 2

    checks = []
    digest = str(hit.get("digest") or "")
    root = str(doc.get("root") or "")

    # 1) 包含关系：叶 → 折叠 → 根
    folded = fold(leaf_of(hit["id"], digest), hit.get("proof") or []).hex()
    checks.append(("inclusion", folded == root,
                   "包含证明折叠到根" if folded == root
                   else "折叠结果 %s ≠ 根 %s" % (folded[:16], root[:16])))

    # 2)（可选）内容绑定：重算规范摘要 == 回执摘要
    path = args.entry_file or os.path.join("library", "%s.md" % hit["id"])
    if os.path.isfile(path):
        live = entry_digest(path)
        checks.append(("content", live == digest,
                       "内容摘要与回执一致" if live == digest
                       else "内容摘要 %s ≠ 回执 %s（内容被改）"
                            % (live[:16], digest[:16])))
    else:
        checks.append(("content", False,
                       "未提供条目内容（--entry-file），无法校验内容绑定"))

    # 3)（可选）签名锚
    anchor = hit.get("anchor")
    if anchor:
        scheme = anchor.get("scheme")
        if scheme == "hmac-sha256":
            if args.key_file and os.path.isfile(args.key_file):
                with open(args.key_file, "rb") as fh:
                    ok, msg = verify_hmac(digest, anchor, fh.read().strip())
            else:
                ok, msg = False, "缺 --key-file，hmac 锚不可校验（fail-closed）"
            checks.append(("anchor", ok, msg))
        elif scheme == "ssh-sig":
            ok, msg = verify_ssh(digest, anchor, args.ssh_allowed_signers,
                                 args.ssh_identity)
            checks.append(("anchor", ok, msg))
        elif scheme == "sigstore-keyless":
            checks.append(("anchor", False,
                           "sigstore 锚需 cosign，未安装 → fail-closed"))
        else:
            checks.append(("anchor", False, "未知锚方案：%s" % scheme))
    else:
        checks.append(("anchor", True, "该条未挂签名锚（仅包含关系可验）"))

    ok_all = all(ok for _n, ok, _m in checks)
    if args.json:
        print(json.dumps({"entry": hit["id"], "root": root, "digest": digest,
                          "ok": ok_all,
                          "checks": [{"name": n, "ok": o, "detail": m}
                                     for n, o, m in checks]},
                         ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print("== nf_verify（读者侧独立验证）%s ==" % hit["id"])
        print("  全馆根：%s" % root[:32])
        for n, o, m in checks:
            print("  %s %-10s %s" % ("✓" if o else "✗", n, m))
        print("  => %s" % ("可验证通过" if ok_all else "未通过（详上）"))
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main())
