"""透明日志（RFC 6962 风格哈希链）——「某条回执在某时点已在册」的可证明链条。

内部差距（挂账收口，原触发条件 = 出现第二署名方/外部验证需求）：NF 已有回执单根
（`protocol/RECEIPTS.json`，inclusion proof）+ 内容绑定批准，但**缺一条链**：
单根只证明「此刻的集合」，不证明「顺序与历史」——外部验证方无法判断某条回执是
一开始就在，还是后来补进去的。哈希链把顺序钉死：`chain[i] = H(chain[i-1] || leaf[i])`。

数学精确性（不夸大）：链条可证明 **append-only 顺序与不做删改**（任何中间插入/删除/改序
都会让后续所有链节对不上）；它**不**提供不可抵赖性——那需要第三方见证（witness）或远程
日志（Rekor/SCITT），本仓单人治理下**没有第二署名方**，故本件在 `boundary` 字段里显式
写明该边界，门禁判该声明必须在场。

落点：生成物 `protocol/generated/receipt_chain.json`（确定性，随 check31 golden 校验）。
"""
from __future__ import annotations

import hashlib
import json
import os
from typing import Any, Dict, List, Tuple

RECEIPTS_REL = "protocol/RECEIPTS.json"
GENERATED_REL = "protocol/generated/receipt_chain.json"
SCHEMA = "nf-transparency/1"
#: 域分隔前缀（RFC 6962 §2.1 的叶子/节点域分隔思路）：链节与叶子用不同前缀，
#: 防止「叶子被当成链节」这类跨类型碰撞
LEAF_PREFIX = b"\x00nf-leaf:"
NODE_PREFIX = b"\x01nf-node:"
BOUNDARY = ("append-only 顺序 + 防删改：链条可证；不可抵赖：**不提供**"
            "（需第三方见证/远程日志；NF 当前单人治理、无第二署名方）")


def _h(prefix: bytes, *parts: bytes) -> str:
    h = hashlib.sha256()
    h.update(prefix)
    for p in parts:
        h.update(b"|")
        h.update(p)
    return h.hexdigest()


def build(root: str = ".") -> Dict[str, Any]:
    """读回执 → 哈希链（确定性：只依赖回执内容与顺序）。"""
    path = os.path.join(root, RECEIPTS_REL)
    rec: Dict[str, Any] = {}
    if os.path.isfile(path):
        with open(path, encoding="utf-8") as fh:
            rec = json.load(fh)
    prev = "0" * 64
    links: List[Dict[str, Any]] = []
    for i, e in enumerate(rec.get("entries") or [], 1):
        leaf = _h(LEAF_PREFIX, str(e.get("path") or "").encode("utf-8"),
                  str(e.get("digest") or "").encode("utf-8"))
        node = _h(NODE_PREFIX, prev.encode("ascii"), leaf.encode("ascii"))
        links.append({"index": i, "path": str(e.get("path") or ""),
                      "digest": str(e.get("digest") or ""), "leaf": leaf,
                      "prev": prev, "chain": node})
        prev = node
    return {
        "schema": SCHEMA,
        "note": "由 protocol/RECEIPTS.json 确定性派生（纯派生，不新增真源）；"
                "链节 = H(prev || leaf)，叶子 = H(path || digest)（域分隔前缀见实现）。",
        "boundary": BOUNDARY,
        "count": len(links),
        "head": prev,
        "receipts_root": str(rec.get("root") or ""),
        "links": links,
    }


def render(doc: Dict[str, Any]) -> bytes:
    return (json.dumps(doc, ensure_ascii=False, indent=2, sort_keys=True)
            + "\n").encode("utf-8")


def verify(root: str = ".") -> Tuple[List[str], Dict[str, Any]]:
    """门禁：链自洽 + 与回执一致 + 边界声明在场 + 在盘生成物 == 实时重算。"""
    issues: List[str] = []
    if not os.path.isfile(os.path.join(root, RECEIPTS_REL)):
        return ["缺 %s（修复指引：先跑 nf receipts --scope protocol --write）"
                % RECEIPTS_REL], {}
    doc = build(root)
    rec: Dict[str, Any] = {}
    with open(os.path.join(root, RECEIPTS_REL), encoding="utf-8") as fh:
        rec = json.load(fh)
    entries = rec.get("entries") or []
    if doc["count"] != len(entries):
        issues.append("链节数 %d ≠ 回执条目数 %d（修复指引：链须逐条对应回执）"
                      % (doc["count"], len(entries)))
    prev = "0" * 64
    for i, link in enumerate(doc["links"], 1):
        if link["index"] != i:
            issues.append("链节序号断裂：期望 %d 实得 %s" % (i, link["index"]))
        if link["prev"] != prev:
            issues.append("链节 %d 的 prev 与上一节 chain 不一致（修复指引：链被改过——"
                          "append-only 顺序不成立）" % i)
        want = _h(NODE_PREFIX, prev.encode("ascii"), link["leaf"].encode("ascii"))
        if link["chain"] != want:
            issues.append("链节 %d 哈希不匹配（修复指引：链节内容与推导式不符）" % i)
        if link["path"] != str(entries[i - 1].get("path")):
            issues.append("链节 %d 与回执第 %d 条路径不一致" % (i, i))
        if link["digest"] != str(entries[i - 1].get("digest")):
            issues.append("链节 %d 与回执第 %d 条摘要不一致（修复指引：回执改了就重写链）"
                          % (i, i))
        prev = link["chain"]
    if doc["head"] != prev:
        issues.append("链头与末节不一致（修复指引：head 须等于末节 chain）")
    if "不可抵赖" not in str(doc.get("boundary") or "") or "不提供" not in str(doc.get("boundary")):
        issues.append("缺「不可抵赖不提供」的边界声明（修复指引：链条可证顺序与防删改，"
                      "不可抵赖需第三方见证——不得夸大）")
    disk = os.path.join(root, GENERATED_REL)
    if os.path.isfile(disk):
        with open(disk, "rb") as fh:
            if fh.read() != render(doc):
                issues.append("%s 过期：与实时重算不一致"
                              "（修复指引：nf transparency --write）" % GENERATED_REL)
    stats = {"links": doc["count"], "head": doc["head"][:16],
             "on_disk": os.path.isfile(disk), "issues": len(issues)}
    return issues, stats


def write(root: str = ".") -> str:
    """把实时重算的链写入生成物位（确定性；同一回执两次写字节一致）。"""
    dest = os.path.join(root, GENERATED_REL)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest, "wb") as fh:
        fh.write(render(build(root)))
    return GENERATED_REL
