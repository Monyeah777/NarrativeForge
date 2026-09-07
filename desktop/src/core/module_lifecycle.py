"""v2.8.0 波B S5：模块生命周期（status 位 + deprecate/restore + 引用门禁）。

状态存放：模块文件元信息行（`> 类别：…｜…｜状态：deprecated（原因：…）`）；
缺省视作 active。发现范围：04_模块库/*/*.md + community/*/modules/*.md。
门禁（verify check24 / nf module verify）：deprecated/retired 模块不得被
其它 active 模块（依赖/被依赖）或 community protocol.yaml 引用——被引用即
FAIL，防「边废弃边被消费」。纯标准库，无 yaml 依赖（protocol 扫描用子集解析）。
"""
from __future__ import annotations

import glob
import os
import re

STATUSES = ("active", "deprecated", "retired")
DEFAULT = "active"
_TAG = "状态"

_TITLE_RE = re.compile(r"#\s*模块\s*([\u4e00-\u9fffA-Za-z]+:)?(M?\d+)\s*[·.、\-]?\s*(.*)")
_META_SEP = re.compile(r"[｜|]")
_REF_KEYS = ("依赖", "被依赖", "订阅")
_ID_NUM = re.compile(r"M(\d{2,3})$")


def iter_module_files(root: str = ".") -> list:
    """返回相对 root 的模块 md 路径（04_模块库 + community 登记包 modules/）。"""
    pats = (
        os.path.join(root, "04_模块库", "*", "*.md"),
        os.path.join(root, "community", "*", "modules", "*.md"),
    )
    out = []
    for p in pats:
        for f in sorted(glob.glob(p)):
            rel = os.path.relpath(f, root).replace("\\", "/")
            if os.path.basename(f).startswith(("README", "readme", "_")):
                continue
            out.append(rel)
    return out


def read_text(root: str, rel: str) -> str:
    with open(os.path.join(root, rel), encoding="utf-8") as fh:
        return fh.read()


def _meta_pairs(line_body: str) -> dict:
    """解析一条 `> …` 元信息内容为 key->value（以 | 或 ｜ 分隔）。"""
    out = {}
    for seg in _META_SEP.split(line_body):
        kv = re.split(r"[:：]", seg, maxsplit=1)
        if len(kv) == 2 and kv[0].strip():
            out[kv[0].strip()] = kv[1].strip()
    return out


def parse_meta(text: str) -> dict:
    """聚合全文 `>` 元信息行（重复键后者覆盖）。"""
    agg = {}
    for ln in text.splitlines():
        s = ln.strip()
        if s.startswith(">"):
            for k, v in _meta_pairs(s[1:].strip()).items():
                agg[k] = v
    return agg


def module_id_from_text(text: str) -> str:
    for ln in text.splitlines():
        s = ln.strip()
        if s.startswith("# 模块"):
            m = _TITLE_RE.match(s)
            if m:
                num = m.group(2).lstrip("M").rjust(2, "0")
                return ("%s:M%s" % (m.group(1).rstrip(":"), num) if m.group(1)
                        else "M%s" % num)
    return ""


def get_status(text: str) -> tuple:
    meta = parse_meta(text)
    raw = meta.get(_TAG, DEFAULT)
    raw = raw.strip()
    if "（" in raw:
        body = raw.split("（", 1)[0].strip()
    else:
        body = raw
    body = body.lower()
    if body not in STATUSES:
        return DEFAULT, ""
    reason = ""
    m = re.search(r"[（(](.*?)[)）]", raw)
    if m:
        reason = m.group(1).strip()
    return body, reason


def _num_of(module_id: str):
    m = _ID_NUM.search(module_id)
    return m.group(1) if m else ""


def parse_refs(meta: dict, module_id: str) -> set:
    """模块头依赖/被依赖/订阅的 id 集合（精确 id 或裸号唯一时匹配数值）。"""
    refs = set()
    for k in _REF_KEYS:
        for tok in re.split(r"[、,，;\s]+", meta.get(k, "")):
            tok = tok.strip()
            if not tok or re.match(r"^[（(].*[)）]$", tok):
                continue
            refs.add(tok)
    return refs


def set_status(text: str, status: str, reason: str = "", module_file: str = "") -> str:
    """把模块文件状态位写入最后一条 `>` 元信息行（无则报错，防无头文件误写）。"""
    if status not in STATUSES:
        raise ValueError("status 须为 %s" % "/".join(STATUSES))
    lines = text.split("\n")
    last = -1
    for i, ln in enumerate(lines):
        if ln.strip().startswith(">"):
            last = i
    if last < 0:
        raise ValueError("%s 无 `> …` 元信息行，拒绝写状态位（头格式不符）" % module_file)
    body = lines[last].strip()[1:].strip()
    pairs = _meta_pairs(body)
    seg = "%s:%s" % (_TAG, status)
    if reason:
        seg += "（%s）" % reason
    new_body = []
    for k, v in pairs.items():
        if k == _TAG:
            continue
        new_body.append("%s：%s" % (k, v))
    new_body.append("状态：%s" % status if not reason else
                    "状态：%s（%s）" % (status, reason))
    indent = lines[last][: len(lines[last]) - len(lines[last].lstrip())]
    lines[last] = indent + "> " + "｜".join(new_body)
    return "\n".join(lines)


def _protocol_ids(root: str) -> dict:
    """community protocol.yaml 里出现的模块 id 词频（core_modules/modules/… 行）。"""
    hits = {}
    for p in glob.glob(os.path.join(root, "community", "*", "protocol.yaml")):
        try:
            text = open(p, encoding="utf-8").read()
        except OSError:
            continue
        for num in _ID_NUM.findall(text):
            hits.setdefault("M" + num, []).append(os.path.relpath(p, root).replace("\\", "/"))
    return hits

def _collect_infos(root: str) -> tuple:
    """扫描模块文件 → {id: {status, file, refs}} + 统计。"""
    infos = {}
    counts = {"modules": 0, "active": 0, "deprecated": 0, "retired": 0}
    num_ids = {}
    for rel in iter_module_files(root):
        text = read_text(root, rel)
        mid = module_id_from_text(text)
        status, _reason = get_status(text)
        meta = parse_meta(text)
        refs = parse_refs(meta, mid)
        counts["modules"] += 1
        counts[status] = counts.get(status, 0) + 1
        key = mid or rel
        infos[key] = {"status": status, "file": rel, "refs": refs, "id": mid}
        n = _num_of(key)
        if n:
            num_ids.setdefault(n, []).append(key)
    return infos, counts, num_ids


def _is_referenced(target_id: str, infos: dict, num_ids: dict,
                   protocol_hits: dict) -> list:
    """返回引用方清单（模块文件 + protocol 文本命中）。"""
    out = []
    tnum = _num_of(target_id)
    numeric_unique = len(num_ids.get(tnum, [])) == 1 if tnum else True
    for key, info in infos.items():
        if key == target_id:
            continue
        for r in info["refs"]:
            if r == target_id:
                out.append("%s(依赖引用)" % info["file"])
            elif ":" not in r and ":" not in target_id and r == target_id:
                out.append("%s(依赖引用)" % info["file"])
            elif ":" not in r and not numeric_unique and r == ("M" + tnum if tnum else r):
                # 裸号 + 目标编号与其它模块撞号：不能断定指向本模块，跳过
                pass
    if tnum:
        for p in protocol_hits.get(tnum, []):
            out.append("%s(protocol 出现)" % p)
    return sorted(set(out))


def verify_modules(root: str = ".") -> tuple:
    """check24 语义：扫描全部模块状态；deprecated/retired 被引用 → FAIL。"""
    issues = []
    infos, counts, num_ids = _collect_infos(root)
    proto = _protocol_ids(root)
    for key, info in infos.items():
        if info["status"] in ("deprecated", "retired"):
            refs = _is_referenced(info["id"] or key, infos, num_ids, proto)
            if refs:
                issues.append("%s 状态=%s 但仍被引用：%s"
                              % (info["file"], info["status"], "；".join(refs)))
    stats = {"modules": counts["modules"],
             "active": counts.get("active", 0),
             "deprecated": counts.get("deprecated", 0),
             "retired": counts.get("retired", 0)}
    return issues, stats