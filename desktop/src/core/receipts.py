"""图书馆回执 + 单根（机制借鉴 MCOP 的 Verifiable Reasoning Receipts / MMR）。

线性哈希链「证明某一条 ∈ 全量」要 O(n) 重放；馆藏长大后这是错形状。本模块给出
**逐条 inclusion proof + 一个全馆根**（RFC 6962 域分隔）：

- 叶子 = `SHA-256(0x00 || 规范载荷)`；内部节点 = `SHA-256(0x01 || 左 || 右)`；
- 每条回执只带 O(log n) 审计路径（几 KB），读者拿到**该条 + 根**即可本地折叠验证，
  不必取全馆其余部分；
- 载荷 = `{id, digest}`（digest 用 library.entry_digest：自指安全）。

纪律：纯标准库 hashlib；只读；不自造密码学（域分隔与折叠规则照 RFC 6962）。
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

SCHEMA = "nf-receipts/1"
RECEIPTS_REL = "library/RECEIPTS.json"


def _h(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


def leaf_hash(payload: bytes) -> bytes:
    return _h(b"\x00" + payload)


def node_hash(left: bytes, right: bytes) -> bytes:
    return _h(b"\x01" + left + right)


def merkle_root(leaves: List[bytes]) -> Optional[bytes]:
    """RFC 6962 风格：空集 → None；单叶 → 该叶。"""
    if not leaves:
        return None
    if len(leaves) == 1:
        return leaves[0]
    mid = 1
    while mid * 2 < len(leaves):
        mid *= 2
    return node_hash(merkle_root(leaves[:mid]), merkle_root(leaves[mid:]))


def inclusion_proof(leaves: List[bytes], index: int) -> List[Dict[str, str]]:
    """返回 [{side, hash}]，**自底向上**（叶的兄弟在前，逐层向上）；
    side ∈ {'left','right'} 表示该兄弟在折叠时的位置。

    与 RFC 6962 audit path 同序；读者侧按列表顺序逐个 node() 即可得到根。
    （早期实现返回自顶向下，导致 n>2 时折叠不到根——已由规模回归测试钉住。）
    """
    if not leaves or index < 0 or index >= len(leaves):
        raise IndexError("叶子下标越界：%s（共 %d 叶）" % (index, len(leaves)))
    proof: List[Dict[str, str]] = []

    def walk(sub: List[bytes], i: int) -> None:
        if len(sub) <= 1:
            return
        mid = 1
        while mid * 2 < len(sub):
            mid *= 2
        if i < mid:
            sib = merkle_root(sub[mid:])
            proof.append({"side": "right", "hash": sib.hex()})
            walk(sub[:mid], i)
        else:
            sib = merkle_root(sub[:mid])
            proof.append({"side": "left", "hash": sib.hex()})
            walk(sub[mid:], i - mid)

    walk(leaves, index)
    return proof[::-1]


def fold_proof(leaf_hex: str, proof: List[Dict[str, str]]) -> str:
    """按证明折叠出根（读者侧验证路径，不依赖仓库其余内容）。"""
    cur = bytes.fromhex(leaf_hex)
    for step in proof:
        sib = bytes.fromhex(step["hash"])
        cur = (node_hash(sib, cur) if step["side"] == "left"
               else node_hash(cur, sib))
    return cur.hex()


def build(root: str = ".") -> Dict[str, Any]:
    """从馆藏实时算：{schema, root, count, entries:[{id, path, digest, leaf, proof}]}。"""
    from core import library as nflib

    rows = nflib.entries(root)
    payloads, leaves = [], []
    for e in rows:
        digest = nflib.entry_digest(root, e["path"])
        payload = json.dumps({"id": e["id"], "digest": digest},
                             sort_keys=True, ensure_ascii=False,
                             separators=(",", ":")).encode("utf-8")
        payloads.append((e, digest, payload))
        leaves.append(leaf_hash(payload))
    root_hash = merkle_root(leaves)
    entries = []
    for i, (e, digest, payload) in enumerate(payloads):
        fm = e["fm"]
        entries.append({"id": e["id"], "path": e["path"], "digest": digest,
                        "anchor": ({"scheme": str(fm.get("anchor_scheme")),
                                    "key_id": str(fm.get("anchor_key_id") or ""),
                                    "mac": str(fm.get("anchor_mac") or ""),
                                    "ns": str(fm.get("anchor_ns") or ""),
                                    "identity": str(fm.get("anchor_identity") or ""),
                                    "sig_file": str(fm.get("anchor_sig_file") or ""),
                                    "fingerprint": str(fm.get("anchor_fingerprint") or "")}
                                   if fm.get("anchor_scheme") else None),
                        "leaf": leaf_hash(payload).hex(),
                        "proof": inclusion_proof(leaves, i)})
    return {"schema": SCHEMA,
            "root": root_hash.hex() if root_hash else "",
            "count": len(rows), "algorithm": "RFC6962-style sha256 domain-separated",
            "entries": entries}


def verify(doc: Dict[str, Any], root: str = ".") -> Tuple[List[str], Dict[str, Any]]:
    """校验：每条回执折叠到根 + 根与实时重算一致（防挑单条伪造、防整体替换）。"""
    issues: List[str] = []
    if not isinstance(doc, dict) or doc.get("schema") != SCHEMA:
        return ["回执文件 schema 不匹配（期望 %s）" % SCHEMA], {}
    live = build(root)
    if doc.get("root") != live["root"]:
        issues.append("根不一致：记录=%s 实测=%s（修复指引：馆藏改动后跑 "
                      "nf library receipts --write）"
                      % (str(doc.get("root"))[:16], str(live["root"])[:16]))
    live_by_id = {e["id"]: e for e in live["entries"]}
    for e in doc.get("entries") or []:
        eid = e.get("id")
        if eid not in live_by_id:
            issues.append("回执指向不存在的条目：%s" % eid)
            continue
        live_e = live_by_id[eid]
        if e.get("digest") != live_e["digest"]:
            issues.append("条目内容已变：%s（修复指引：重签该条并重建回执）" % eid)
        if fold_proof(str(e.get("leaf")), e.get("proof") or []) != str(doc.get("root")):
            issues.append("包含证明不折叠到根：%s" % eid)
    if len(doc.get("entries") or []) != live["count"]:
        issues.append("回执条数 %d ≠ 馆藏条数 %d"
                      % (len(doc.get("entries") or []), live["count"]))
    stats = {"entries": live["count"], "root": live["root"]}
    return issues, stats


def write(root: str = ".", rel: str = RECEIPTS_REL) -> str:
    doc = build(root)
    p = Path(root) / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(doc, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                 encoding="utf-8", newline="\n")
    return rel


def load(root: str = ".", rel: str = RECEIPTS_REL) -> Dict[str, Any]:
    return json.loads((Path(root) / rel).read_text(encoding="utf-8"))


# ---------------------------------------------------------------- 协议层回执
PROTOCOL_RECEIPTS_REL = "protocol/RECEIPTS.json"


def protocol_subjects(root: str = ".") -> List[str]:
    """协议层机读产物清单（回执覆盖面；不存在的项自动跳过）。"""
    fixed = ["STRATEGY.md", "01_核心协议.md", "02_联动注册表.md",
             "06_Agent执行协议.md", "07_官方核心出厂与社区预设导航.md",
             "llms.txt", "library/INDEX.md", "library/ALIAS.md",
             "protocol/event_registry.json", "protocol/world_slots.json",
             "protocol/export_conformance.json", "protocol/community_asset_ledger.json",
             "protocol/external_events.json", "protocol/type_backlog.json",
             "protocol/pipeline_advisory.json", "protocol/score_baseline.json",
             "protocol/module_signatures.json", "protocol/conformance_report.json",
             "protocol/CONFORMANCE.md", "protocol/driver.json",
             "protocol/rfc_index.json", "protocol/endpoint_contract.json",
             "protocol/knowledge_sources.json", "protocol/transform_log.json",
             "protocol/knowledge_usage.json",
             "protocol/assertions.json",
             "protocol/vocabularies.json", "protocol/normative.json",
             "protocol/data_contracts.json",
             "decisions/INDEX.md",
             "desktop/src/core/registry.json"]
    r = Path(root)
    fixed += [p.relative_to(r).as_posix() for p in sorted(r.glob("protocol/schema/*.json"))]
    fixed += [p.relative_to(r).as_posix() for p in sorted(r.glob("decisions/ADR-*.md"))]
    return [s for s in fixed if (r / s).is_file()]


def build_scope(root: str = ".", subjects: Optional[List[str]] = None,
                scope: str = "protocol") -> Dict[str, Any]:
    """任意文件集 → 回执（叶 = sha256(0x00‖{"id":相对路径,"digest":文件摘要})）。"""
    rels = subjects if subjects is not None else protocol_subjects(root)
    payloads, leaves, rows = [], [], []
    for rel in rels:
        p = Path(root) / rel
        if not p.is_file():
            continue
        digest = hashlib.sha256(p.read_bytes()).hexdigest()
        payload = json.dumps({"id": rel, "digest": digest}, sort_keys=True,
                             ensure_ascii=False,
                             separators=(",", ":")).encode("utf-8")
        rows.append((rel, digest, payload))
        leaves.append(leaf_hash(payload))
    root_hash = merkle_root(leaves)
    entries = [{"id": rel, "path": rel, "digest": digest,
                "leaf": leaf_hash(payload).hex(),
                "proof": inclusion_proof(leaves, i)}
               for i, (rel, digest, payload) in enumerate(rows)]
    return {"schema": SCHEMA, "scope": scope,
            "root": root_hash.hex() if root_hash else "",
            "count": len(entries), "algorithm": "RFC6962-style sha256 domain-separated",
            "entries": entries}


def verify_scope(doc: Dict[str, Any], root: str = ".") -> Tuple[List[str], Dict[str, Any]]:
    """协议层回执校验：每条折叠到根 + 文件摘要与记录一致 + 根与实时重算一致。"""
    issues: List[str] = []
    if not isinstance(doc, dict) or doc.get("schema") != SCHEMA:
        return ["协议回执 schema 不匹配"], {}
    live = build_scope(root, [e["id"] for e in doc.get("entries") or []])
    if doc.get("root") != live["root"]:
        issues.append("协议回执根不一致：记录=%s 实测=%s（修复指引：nf receipts --scope protocol --write）"
                      % (str(doc.get("root"))[:16], str(live["root"])[:16]))
    live_by = {e["id"]: e["digest"] for e in live["entries"]}
    for e in doc.get("entries") or []:
        if live_by.get(e["id"]) != e.get("digest"):
            issues.append("文件内容已变：%s" % e["id"])
        if fold_proof(str(e.get("leaf")), e.get("proof") or []) != str(doc.get("root")):
            issues.append("包含证明不折叠到根：%s" % e["id"])
    return issues, {"entries": len(doc.get("entries") or []), "root": live["root"]}


def write_scope(root: str = ".", scope: str = "protocol") -> str:
    doc = build_scope(root, scope=scope)
    p = Path(root) / PROTOCOL_RECEIPTS_REL
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(doc, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                 encoding="utf-8", newline="\n")
    return PROTOCOL_RECEIPTS_REL
