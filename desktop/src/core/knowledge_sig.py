"""v2.8.0 波C C1/C2：协议知识签名 + 版本差异检测（41 规划「确定性知识编译」）。

C1 `nf sig`：对 NF 文档（编号方案 01-36 / 协议 / 管线 / 模块）生成结构化签名
    ——知识指纹（标题/编号/版本/章节/引用集/正文哈希），纯标准库、可复现。
C2 `nf diff`：任意两份签名 → 字段级差异 + 兼容判定；verify.sh check25 收编
   「全量 01-36 签名覆盖 + 可复现」门禁（编译期冲突发现，录入时而非提问时）。

纪律：只做新增可计算摘要，不改 01-07/registry/verify 既有契约字段；
      yaml 一律按文本片段解析（无第三方依赖，verify 零依赖红线保持）。
"""
from __future__ import annotations

import hashlib
import json
import os
import re

#: 根目录编号方案文档范围：01..36（含 33/34/35 各子报告）
DOC_RANGE = re.compile(r"^((?:0[1-9]|[12][0-9]|3[0-6]))_")
_VERSION = re.compile(r"v\d+(?:\.\d+){1,2}")
_REF_P = re.compile(r"(?<![A-Za-z0-9])P\d{2,4}")
_REF_M = re.compile(r"(?<![A-Za-z0-9])M\d{2,4}")
_HEADING = re.compile(r"^#{1,6}\s+(.*?)\s*$")
_YAML_FENCE = re.compile(r"^```[ \t]*[Yy][Aa][Mm][Ll]?[ \t]*$", re.M)
_BLOCK_KEY = re.compile(r"^([A-Za-z_][\w]*):\s*$", re.M)


def _norm(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def parse_doc_id(path: str) -> str:
    """从相对路径取根目录编号方案文档的两位编号（01-36），否则空串。"""
    base = os.path.basename(path)
    m = DOC_RANGE.match(base)
    return m.group(1) if m else ""


def kind_of(path: str) -> str:
    p = path.replace("\\", "/")
    if "/03_管线库/" in p or "/pipelines/" in p:
        return "pipeline"
    if "/04_模块库/" in p or "/modules/" in p:
        return "module"
    return "doc"


def _extract_fences(text: str) -> list:
    """提取 ```yaml 代码块内文本（纯文本切段，不做 yaml 解析）。"""
    out = []
    in_fence = False
    buf = []
    for ln in text.splitlines():
        if not in_fence:
            if _YAML_FENCE.match(ln):
                in_fence = True
                buf = []
        else:
            if ln.strip().startswith("```"):
                in_fence = False
                out.append("\n".join(buf))
            else:
                buf.append(ln)
    return out


def _field_from_fence(text: str, field: str) -> str:
    for fence in _extract_fences(text):
        m = re.search(r"(?m)^\s*%s:\s*(.+?)\s*$" % re.escape(field), fence)
        if m:
            return m.group(1).strip().strip("'\"")
    return ""


def build_signature(path: str, root: str = ".") -> dict:
    """对单个 NF 文档生成结构化签名（相对 root 的可复现摘要）。"""
    abs_path = os.path.join(root, path)
    with open(abs_path, encoding="utf-8") as fh:
        raw = fh.read()
    text = _norm(raw)
    lines = text.splitlines()
    headings = []
    for ln in lines:
        m = _HEADING.match(ln)
        if m and not m.group(1).startswith("#"):
            headings.append(m.group(1).strip())
    doc_id = parse_doc_id(path)
    title = headings[0] if headings else os.path.basename(path)
    ver_m = _VERSION.search(title + "\n" + "\n".join(lines[:8]))
    schema_names = []
    for fence in _extract_fences(text):
        for m in _BLOCK_KEY.finditer(fence):
            name = m.group(1)
            if name not in ("yaml", "yml", "text"):
                schema_names.append(name)
    refs = sorted(set(_REF_M.findall(text) + _REF_P.findall(text)))
    kind = kind_of(path)
    self_id = _field_from_fence(text, "id")
    layer = _field_from_fence(text, "layer")
    category = _field_from_fence(text, "category")
    meta_lines = [ln for ln in lines if ln.strip().startswith(">")]
    sig = {
        "kind": kind,
        "path": path.replace("\\", "/"),
        "doc_id": doc_id,
        "title": title,
        "version": ver_m.group(0) if ver_m else "",
        "self_id": self_id,
        "layer": layer,
        "category": category,
        "heading_count": len(headings),
        "headings": headings,
        "schema_names": sorted(set(schema_names)),
        "refs": refs,
        "meta_line_count": len(meta_lines),
        "line_count": len(lines),
        "body_hash": _sha(text),
    }
    return sig


def _canonical(sig: dict) -> bytes:
    return json.dumps(sig, sort_keys=True, ensure_ascii=False).encode("utf-8")


def signature_digest(sig: dict) -> str:
    return _sha(_canonical(sig).decode("utf-8"))


def discover_docs(root: str = ".") -> list:
    """全量 01-36 根目录方案文档（验收基线：试点 3 + 全量 01-36）。"""
    out = []
    for name in sorted(os.listdir(root)):
        if name.endswith(".md") and DOC_RANGE.match(name):
            out.append(name)
    return out


def scan(root: str = ".") -> dict:
    """生成全量签名集：{count, records:[{digest, sig}]}。"""
    records = []
    for rel in discover_docs(root):
        sig = build_signature(rel, root)
        records.append({"digest": signature_digest(sig), "sig": sig})
    return {"count": len(records), "records": records}


def verify_reproducible(root: str = ".") -> tuple:
    """check25 语义：01-36 全量签名两遍生成逐字节一致（可复现 = 知识指纹稳定）。"""
    issues = []
    first = scan(root)
    second = scan(root)
    if first["count"] == 0:
        issues.append("未发现任何 01-36 编号方案文档")
    if first["count"] != second["count"]:
        issues.append("两遍扫描文件数不一致")
    d1 = {r["sig"]["path"]: r["digest"] for r in first["records"]}
    d2 = {r["sig"]["path"]: r["digest"] for r in second["records"]}
    if d1 != d2:
        for p in sorted(set(d1) | set(d2)):
            if d1.get(p) != d2.get(p):
                issues.append("签名不可复现：%s" % p)
    for r in first["records"]:
        if not r["sig"]["title"]:
            issues.append("缺少标题：%s" % r["sig"]["path"])
    stats = {
        "docs": first["count"],
        "reproducible": int(not issues),
        "digests": sorted(d1.values()),
    }
    return issues, stats


def diff_signatures(a: dict, b: dict) -> dict:
    """C2：任意两签名 → 字段级差异 + 兼容判定（判定规则自含文档化）。"""
    changes = []
    scalar_fields = ("kind", "doc_id", "title", "version", "self_id",
                     "layer", "category", "heading_count",
                     "meta_line_count", "line_count", "body_hash")
    for f in scalar_fields:
        va, vb = a.get(f), b.get(f)
        if va != vb:
            changes.append({"field": f, "from": va, "to": vb, "kind": "字段变更"})
    list_fields = ("headings", "schema_names", "refs")
    for f in list_fields:
        sa, sb = set(a.get(f, [])), set(b.get(f, []))
        for x in sorted(sa - sb):
            changes.append({"field": f, "from": x, "to": None, "kind": "移除"})
        for x in sorted(sb - sa):
            changes.append({"field": f, "from": None, "to": x, "kind": "新增"})
    removed = [c for c in changes if c["kind"] == "移除" and c["field"] in ("refs", "headings")]
    if a.get("doc_id") and b.get("doc_id") and a["doc_id"] != b["doc_id"]:
        verdict = "破坏（文档编号变更）"
    elif removed:
        verdict = "需评审（存在移除项：引用/章节收缩）"
    elif a.get("version") != b.get("version"):
        verdict = "兼容（版本演进）"
    else:
        verdict = "兼容"
    return {"from": a.get("path"), "to": b.get("path"),
            "verdict": verdict, "changes": changes}
