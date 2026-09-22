"""NF 云端图书馆（library/）机器面：frontmatter 真源 → INDEX/ALIAS 投影 + 检索索引。

机制借鉴 OKF v0.2（Google Open Knowledge Format，markdown + YAML frontmatter，纯文本可读、
可 diff、可移植），按 NF 现有纪律收窄落地：

- **单一真相源（I5）**：条目文件头 frontmatter = 真源；`INDEX.md` / `ALIAS.md` 一律由本模块
  重生成（投影），不再人机混写。
- **OKF 三族字段**：provenance(`sources`) / trust(`generated`,`verified`,`attestation`) /
  lifecycle(`status`,`stale_after`)——把「从哪来 / 谁验过 / 还作数吗」变成一等字段。
- **未知键保留**：消费方不得因未识别字段拒收（对齐 OKF 扩展规则）。

纪律：纯标准库（自实现 YAML 子集解析，不用第三方）；写盘只由 `write_projection` 一处发生。
"""
from __future__ import annotations

import hashlib
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ENTRY_GLOB = "library/NF-*.md"
INDEX_REL = "library/INDEX.md"
ALIAS_REL = "library/ALIAS.md"

#: 必填 frontmatter 键（OKF: type 必填；NF 追加 id/title 以便编号寻址）
REQUIRED_KEYS = ("id", "type", "title")
#: 推荐键（缺失记 WARN 不阻断）
RECOMMENDED_KEYS = ("description", "license", "sources", "generated",
                    "status", "tags", "author")
#: 生命周期词表
STATUSES = ("active", "deprecated", "superseded")
#: 镜像前缀（双端；raw = 喂 AI，blob = 给人点开）
MIRRORS = (
    {"id": "github", "label": "GitHub（海外）",
     "raw": "https://raw.githubusercontent.com/Monyeah777/NarrativeForge/main/",
     "blob": "https://github.com/Monyeah777/NarrativeForge/blob/main/"},
    {"id": "gitee", "label": "Gitee（国内直连 · 主入口）",
     "raw": "https://gitee.com/monyeah777/narrative-forge/raw/main/",
     "blob": "https://gitee.com/monyeah777/narrative-forge/blob/main/"},
)

_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_ID = re.compile(r"^NF(-[A-Za-z0-9]{1,16})?(-[A-Za-z0-9]{1,16})?-\d+$|^NF-[0-9A-Z]+$")

BEGIN_INDEX = "<!-- BEGIN GENERATED: library-index -->"
END_INDEX = "<!-- END GENERATED: library-index -->"
BEGIN_MIRROR = "<!-- BEGIN GENERATED: library-mirror -->"
END_MIRROR = "<!-- END GENERATED: library-mirror -->"


# ---------------------------------------------------------------- frontmatter
def parse_frontmatter(text: str) -> Tuple[Dict[str, Any], str]:
    """极简 YAML frontmatter 解析（key: value / key: [a, b] / key: 换行 - item）。"""
    if not text.startswith("---"):
        return {}, text
    lines = text.splitlines()
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        return {}, text
    fm: Dict[str, Any] = {}
    key: Optional[str] = None
    for ln in lines[1:end]:
        if not ln.strip() or ln.strip().startswith("#"):
            continue
        if ln.startswith(("  ", "\t")) and key:
            item = ln.strip()
            if item.startswith("- "):
                item = item[2:].strip()
            if not isinstance(fm.get(key), list):
                fm[key] = [] if not fm.get(key) else [fm[key]]
            fm[key].append(item.strip("'\""))
            continue
        if ":" in ln:
            k, v = ln.split(":", 1)
            key = k.strip()
            v = v.strip()
            if not v:
                fm[key] = []
            elif v.startswith("[") and v.endswith("]"):
                fm[key] = [x.strip().strip("'\"") for x in v[1:-1].split(",")
                           if x.strip()]
            else:
                fm[key] = v.strip("'\"")
    return fm, "\n".join(lines[end + 1:])


def read_entry(path: str) -> Dict[str, Any]:
    """读单条条目 → {path, id, fm, body}（id 以文件名为准）。"""
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    fm, body = parse_frontmatter(text)
    return {"path": Path(path).as_posix(), "id": Path(path).stem,
            "fm": fm, "body": body, "text": text}


def entries(root: str = ".") -> List[Dict[str, Any]]:
    """全量条目（按编号排序；path 一律归一为仓库相对路径）。"""
    r = Path(root)
    out = [read_entry(str(p)) for p in sorted(r.glob(ENTRY_GLOB))]
    for e in out:
        e["path"] = os.path.relpath(e["path"], str(r)).replace("\\", "/")
    out.sort(key=lambda e: e["id"])
    return out


# ------------------------------------------------------------------- 校验
def verify(root: str = ".", key: Optional[bytes] = None,
           ssh_allowed_signers: str = "", ssh_identity: str = ""
           ) -> Tuple[List[str], List[str], Dict[str, Any]]:
    """校验条目 frontmatter → (issues FAIL, warns WARN, stats)。"""
    issues: List[str] = []
    warns: List[str] = []
    rows = entries(root)
    ids = {e["id"] for e in rows}
    for e in rows:
        fm, eid = e["fm"], e["id"]
        if not fm:
            issues.append("%s 缺 YAML frontmatter（真源要求：type/id/title 起）" % eid)
            continue
        for k in REQUIRED_KEYS:
            if not str(fm.get(k) or "").strip():
                issues.append("%s frontmatter 缺必填键：%s" % (eid, k))
        if str(fm.get("id") or "") != eid:
            issues.append("%s frontmatter id 与文件名不一致：%s" % (eid, fm.get("id")))
        lic = str(fm.get("license") or "")
        try:
            from core.license_gate import ALLOWED
            if lic and lic not in ALLOWED:
                issues.append("%s license 不在词表：%s" % (eid, lic))
        except Exception:  # nosec B110/B112 —— 尽力而为：跳过不可读/不可解析项；该类缺口由对应门禁与 AUD-0016 静默跳过清单另行报出
            pass
        st = str(fm.get("status") or "active")
        if st not in STATUSES:
            issues.append("%s status 不在词表：%s（%s）" % (eid, st, "/".join(STATUSES)))
        if st == "superseded" and not str(fm.get("superseded_by") or "").strip():
            issues.append("%s status=superseded 但缺 superseded_by" % eid)
        sb = str(fm.get("superseded_by") or "").strip()
        if sb and sb not in ids:
            issues.append("%s superseded_by 指向不存在的条目：%s" % (eid, sb))
        if sb == eid:
            issues.append("%s superseded_by 指向自身（取代链成环）" % eid)
        src = fm.get("sources")
        if not src:
            warns.append("%s 缺 sources（provenance 未声明）" % eid)
        for date_key in ("generated", "verified", "stale_after"):
            v = str(fm.get(date_key) or "").strip()
            if v and not _DATE.match(v):
                issues.append("%s %s 非 YYYY-MM-DD：%s" % (eid, date_key, v))
        att = str(fm.get("attestation") or "").strip()
        if att:
            drifted = False
            if not re.fullmatch(r"[0-9a-fA-F]{64}", att):
                issues.append("%s attestation 非 64 位十六进制摘要：%s" % (eid, att[:16]))
            else:
                try:
                    live = entry_digest(root, e["path"])
                    drifted = live != att.lower()
                except OSError:
                    pass
            scheme = str(fm.get("anchor_scheme") or "").strip()
            if drifted:
                if scheme:
                    # 有锚却内容已改 = 签名不再覆盖当前内容 → 判 FAIL（读者不应被误导）
                    issues.append("%s 签名锚已不覆盖当前内容（落锚后内容被改）"
                                  "（修复指引：重新 nf library attest <编号> 并分发新回执）" % eid)
                else:
                    warns.append("%s attestation 与当前内容不符（内容已改，需重签）" % eid)
            if scheme:
                from core import attest as _attest
                a_ok, a_issues, a_level = _attest.verify_digest_anchor(
                    att, {"scheme": scheme, "mac": str(fm.get("anchor_mac") or ""),
                          "ns": str(fm.get("anchor_ns") or ""),
                          "identity": str(fm.get("anchor_identity") or ""),
                          "sig_file": (os.path.join(root, str(fm.get("anchor_sig_file") or ""))
                                       if fm.get("anchor_sig_file") else "")},
                    key, {"allowed_signers": ssh_allowed_signers,
                          "identity": ssh_identity})
                if scheme == _attest.SCHEME_HMAC and key is None:
                    warns.append("%s 有 hmac 签名锚但未提供密钥 → 本轮无法校验"
                                 "（修复指引：--key-file <同一密钥>）" % eid)
                elif scheme == _attest.SCHEME_SSH and not ssh_allowed_signers:
                    warns.append("%s 有 ssh-sig 锚但未提供 allowed_signers → 本轮无法校验"
                                 "（修复指引：--ssh-allowed-signers <文件>）" % eid)
                elif not a_ok:
                    issues.append("%s 签名锚校验失败（级 %s）：%s"
                                  % (eid, a_level, "; ".join(a_issues)))
        for k in RECOMMENDED_KEYS:
            if k not in fm:
                warns.append("%s 缺推荐键：%s" % (eid, k))
    stats = {"entries": len(rows), "ids": sorted(ids),
             "active": sum(1 for e in rows
                           if str(e["fm"].get("status") or "active") == "active"),
             "warns": warns}
    return issues, warns, stats


# ------------------------------------------------------------------- 投影
def _cell(v: Any) -> str:
    if isinstance(v, list):
        v = ",".join(str(x) for x in v)
    return str(v or "").replace("|", "\\|").strip()


def render_mirror_block() -> str:
    """镜像 + MD 孪生声明（机器可读，对齐 llms.txt v2 的 raw/markdown 约定）。"""
    out = [BEGIN_MIRROR, "", "## 取件基底（机器可读 · 双镜像）", "",
           "| 镜像 | 形态 | 前缀 |", "|---|---|---|"]
    for m in MIRRORS:
        out.append("| %s | raw（喂 AI · 主用） | `%s` |" % (m["id"], m["raw"]))
        out.append("| %s | blob（给人点开） | `%s` |" % (m["id"], m["blob"]))
    out += ["",
            "> **MD 孪生**：本馆全部条目本身就是 markdown（`library/<编号>.md`）——"
            "等价于 llms.txt v2 建议的 `page.md` 孪生形态，无需另做 HTML 版；"
            "`INDEX.md` 是本馆的描述文件（等价 `rel=\"describedby\"` 指向物）。",
            "> **换镜像 = 只换前缀**，后缀路径一个字不动。",
            "", END_MIRROR]
    return "\n".join(out)


def render_index_block(root: str = ".") -> str:
    """登记表（由条目 frontmatter 重生成；含生命周期与可信度列）。"""
    rows = entries(root)
    out = [BEGIN_INDEX, "", "## 登记表（由条目 frontmatter 自动生成，勿手改）", "",
           "| 编号 | 标题 | 形态/领域 | 投稿人 | 入库日期 | 许可 | 分级 | 状态 | 一句话 |",
           "|---|---|---|---|---|---|---|---|---|"]
    for e in rows:
        fm = e["fm"]
        out.append("| %s | %s | %s | %s | %s | %s | %s | %s | %s |" % (
            e["id"], _cell(fm.get("title")) or e["id"],
            _cell(fm.get("type")), _cell(fm.get("author")),
            _cell(fm.get("generated")) or _cell(fm.get("added")),
            _cell(fm.get("license")), _cell(fm.get("rating")) or "unrated",
            _cell(fm.get("status")) or "active",
            _cell(fm.get("description"))))
    out += ["",
            "> 状态：`active`（在役）/ `deprecated`（不再推荐但仍可读）/ "
            "`superseded`（已被取代，见条目内 `superseded_by`）。",
            "", END_INDEX]
    return "\n".join(out)


def render_alias(root: str = ".") -> str:
    """ALIAS 全量重生成（大小写转译 + 双镜像直链）。"""
    rows = entries(root)
    out = ["# 📖 大小写转译表（ALIAS）· AI 专用",
           "",
           "> **用法**：拿不准编号大小写时 → 先把编号**全小写化** → 在「小写键」列匹配 "
           "→ 用「真实编号」列拼链接取件。",
           "> 取件基底（GitHub）：`%s`（国内镜像 Gitee：`%s`，规则相同）。"
           % (MIRRORS[0]["raw"], MIRRORS[1]["raw"]),
           "> 本表由 `nf library reindex` 全量重建（真源 = 条目 frontmatter）；手工改将被覆盖。",
           "",
           "| 小写键 | 真实编号 | 状态 | GitHub raw 链接 | Gitee raw 链接 |",
           "|---|---|---|---|---|"]
    for e in rows:
        out.append("| %s | %s | %s | %s | %s |" % (
            e["id"].lower(), e["id"],
            str(e["fm"].get("status") or "active"),
            MIRRORS[0]["raw"] + "library/%s.md" % e["id"],
            MIRRORS[1]["raw"] + "library/%s.md" % e["id"]))
    return "\n".join(out) + "\n"


def _replace_region(text: str, begin: str, end: str, block: str) -> str:
    """用 block 替换 begin..end 之间的生成区（保留两侧人工内容）。"""
    if begin in text and end in text:
        pre = text[:text.index(begin)]
        post = text[text.index(end) + len(end):]
        return pre + block + post
    return text.rstrip("\n") + "\n\n" + block + "\n"


def write_projection(root: str = ".") -> Dict[str, Any]:
    """重写 INDEX 的生成区 + 全量重生成 ALIAS（唯一写盘入口）。"""
    r = Path(root)
    idx = r / INDEX_REL
    ali = r / ALIAS_REL
    changed = []
    if idx.exists():
        text = idx.read_text(encoding="utf-8")
        new = _replace_region(text, BEGIN_MIRROR, END_MIRROR, render_mirror_block())
        new = _replace_region(new, BEGIN_INDEX, END_INDEX, render_index_block(root))
        if new != text:
            idx.write_text(new, encoding="utf-8", newline="\n")
            changed.append(INDEX_REL)
    new_alias = render_alias(root)
    if not ali.exists() or ali.read_text(encoding="utf-8") != new_alias:
        ali.write_text(new_alias, encoding="utf-8", newline="\n")
        changed.append(ALIAS_REL)
    return {"changed": changed}


def check_projection(root: str = ".") -> List[str]:
    """投影一致性（I5）：INDEX 生成区 / ALIAS 必须等于实时重算结果。"""
    issues = []
    r = Path(root)
    idx = r / INDEX_REL
    if idx.exists():
        text = idx.read_text(encoding="utf-8")
        for begin, end, block in ((BEGIN_MIRROR, END_MIRROR, render_mirror_block()),
                                  (BEGIN_INDEX, END_INDEX, render_index_block(root))):
            if begin not in text or end not in text:
                issues.append("INDEX 缺生成区标记：%s" % begin)
                continue
            cur = text[text.index(begin):text.index(end) + len(end)]
            if cur != block:
                issues.append("INDEX 生成区「%s」与实时重算不一致（跑 nf library reindex）"
                              % begin.split(":")[-1].strip(" -"))
    else:
        issues.append("缺 %s" % INDEX_REL)
    ali = r / ALIAS_REL
    if ali.exists():
        if ali.read_text(encoding="utf-8") != render_alias(root):
            issues.append("ALIAS 与实时重算不一致（跑 nf library reindex）")
    else:
        issues.append("缺 %s" % ALIAS_REL)
    return issues


# ------------------------------------------------------------------- 检索
def _tokens(s: str) -> List[str]:
    """中英混排切分：英文词 + 数字 + 中文 2-gram（无第三方分词）。"""
    s = s.lower()
    toks = re.findall(r"[a-z0-9_]+", s)
    han = re.findall(r"[\u4e00-\u9fa5]+", s)
    for h in han:
        toks.append(h)
        if len(h) > 2:
            toks += [h[i:i + 2] for i in range(len(h) - 1)]
    return toks


def build_index(root: str = ".") -> Dict[str, Dict[str, int]]:
    """轻量倒排索引：词 → {条目 id: 权重}（标题/描述/标签权重高，正文低）。"""
    idx: Dict[str, Dict[str, int]] = {}
    for e in entries(root):
        fm = e["fm"]
        fields = [
            (str(fm.get("title") or ""), 6),
            (str(fm.get("description") or ""), 4),
            (" ".join(fm.get("tags") or []), 3),
            (" ".join(fm.get("sources") or []), 2),
            (e["id"], 5),
            (re.sub(r"(?m)^#{1,6}\s*", "", e["body"])[:8000], 1),
        ]
        for text, weight in fields:
            for tok in set(_tokens(text)):
                idx.setdefault(tok, {}).setdefault(e["id"], 0)
                idx[tok][e["id"]] += weight
    return idx


def search(query: str, root: str = ".", limit: int = 10) -> List[Dict[str, Any]]:
    """关键词检索（标题/描述/标签/正文），返回按分排序的结果。"""
    idx = build_index(root)
    scores: Dict[str, int] = {}
    q_low = query.strip().lower()
    for tok in set(_tokens(query)):
        for eid, w in (idx.get(tok) or {}).items():
            scores[eid] = scores.get(eid, 0) + w
    for e in entries(root):  # 裸子串兜底（"雨天走廊" 这类跨 token 串）
        if q_low and q_low in (e["text"] or "").lower():
            scores[e["id"]] = scores.get(e["id"], 0) + 2
    out = []
    for eid, score in sorted(scores.items(), key=lambda kv: (-kv[1], kv[0])):
        hit = next(e for e in entries(root) if e["id"] == eid)
        out.append({"id": eid, "score": score,
                    "title": hit["fm"].get("title", eid),
                    "type": hit["fm"].get("type", ""),
                    "status": hit["fm"].get("status", "active"),
                    "path": hit["path"],
                    "description": hit["fm"].get("description", "")})
    return out[:limit]


# ------------------------------------------------------- 生命周期（写面）
def _rewrite_frontmatter(path: str, updates: Dict[str, Optional[str]]) -> None:
    """就地改 frontmatter 指定键（值 None = 删除该键）；正文与其余键原样保留。"""
    with open(path, encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError("%s 缺 frontmatter，无法流转生命周期" % path)
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    if end is None:
        raise ValueError("%s frontmatter 未闭合" % path)
    head, body = lines[1:end], lines[end:]
    done = set()
    out = []
    for ln in head:
        key = ln.split(":", 1)[0].strip() if ":" in ln else ""
        if key in updates:
            val = updates[key]
            done.add(key)
            if val is not None:
                out.append("%s: %s" % (key, val))
            continue
        out.append(ln)
    for key, val in updates.items():
        if key not in done and val is not None:
            out.append("%s: %s" % (key, val))
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(["---"] + out + body) + "\n")


def set_status(root: str, entry_id: str, status: str,
               superseded_by: str = "") -> str:
    """流转条目生命周期（active/deprecated/superseded）并同步重建投影。"""
    if status not in STATUSES:
        raise ValueError("status 非法：%s（取值 %s）" % (status, "/".join(STATUSES)))
    hit = None
    for e in entries(root):
        if e["id"].lower() == (entry_id or "").strip().lower():
            hit = e
            break
    if hit is None:
        raise ValueError("条目未找到：%s（nf library ls 可枚举）" % entry_id)
    if status == "superseded":
        if not superseded_by:
            raise ValueError("superseded 必须指定取代者"
                             "（修复指引：nf library supersede <旧编号> <新编号>）")
        ids = {e["id"] for e in entries(root)}
        if superseded_by not in ids:
            raise ValueError("取代者不存在：%s" % superseded_by)
        if superseded_by == hit["id"]:
            raise ValueError("取代者不能是自己（修复指引：指向另一条已入库条目，"
                             "如 nf library supersede NF-1 NF-2）")
    _rewrite_frontmatter(
        os.path.join(root, hit["path"]),
        {"status": status,
         "superseded_by": superseded_by if status == "superseded" else None})
    write_projection(root)
    return hit["path"]


def digest_of_entry(path: str) -> str:
    """条目内容摘要（供 attestation 字段挂接）。"""
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def entry_digest(root: str, rel: str) -> str:
    """条目**规范摘要**：剔除签名/锚字段行后的整文件 sha256。

    自指避免：签名值与锚字段不能参与自身摘要的计算，否则每次落签都会自我失效。
    剔除项 = `attestation` / `attested_at` / `anchor_scheme` / `anchor_mac` /
    `anchor_key_id` / `anchor_issuer`。
    """
    with open(os.path.join(root, rel), encoding="utf-8") as fh:
        text = fh.read().replace("\r\n", "\n")
    kept = [ln for ln in text.split("\n")
            if not re.match(r"^(attestation|attested_at|anchor_[a-z_]+)\s*:", ln)]
    return hashlib.sha256("\n".join(kept).encode("utf-8")).hexdigest()


def set_attestation(root: str, entry_id: str, issuer: str = "nf library",
                    key: Optional[bytes] = None, ssh_key: str = "",
                    ssh_identity: str = "",
                    ssh_ns: str = "") -> Dict[str, Any]:
    """把规范摘要写进条目 frontmatter；给了密钥就一并落 **hmac 签名锚**。

    锚字段（扁平键，frontmatter 解析器友好）：
    `anchor_scheme` / `anchor_mac` / `anchor_key_id` / `anchor_issuer`。
    不给密钥时清掉旧锚——避免"降级后残留旧锚"造成假可信。
    """
    from core import attest as _attest
    hit = None
    for e in entries(root):
        if e["id"].lower() == (entry_id or "").strip().lower():
            hit = e
            break
    if hit is None:
        raise ValueError("条目未找到：%s（修复指引：nf library ls 列全量编号）" % entry_id)
    rel = hit["path"]
    att = _attest.build(rel, root, issuer=issuer)
    # 存入的摘要必须**自指安全**（剔除 attestation 字段后计算），否则一落签即失效
    digest = entry_digest(root, rel)
    anchor: Dict[str, Any] = {}
    level = "digest_only"
    anchor_fields: Dict[str, Any] = {}
    if ssh_key:
        info = _attest.sign_digest_ssh(digest, ssh_key, ssh_identity,
                                       ns=ssh_ns or _attest.SSH_NAMESPACE)
        sig_rel = "library/anchors/%s.sig" % hit["id"]
        dest = os.path.join(root, sig_rel)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(info["sig_file"], "rb") as src, open(dest, "wb") as dst:
            dst.write(src.read())
        level = _attest.SCHEME_SSH
        anchor_fields = {"anchor_ns": info["ns"],
                         "anchor_identity": info["identity"],
                         "anchor_sig_file": sig_rel,
                         "anchor_fingerprint": info["fingerprint"]}
    elif key:
        anchor = _attest.sign_digest_hmac(digest, key, issuer)
        level = str(anchor.get("scheme") or "hmac-sha256")
        anchor_fields = {"anchor_key_id": anchor.get("key_id"),
                         "anchor_issuer": anchor.get("issuer")}
    _rewrite_frontmatter(os.path.join(root, rel), {
        "attestation": digest, "attested_at": att["issued_at"][:10],
        "anchor_scheme": (anchor.get("scheme") or level) if (key or ssh_key) else None,
        "anchor_mac": anchor.get("mac") if key and not ssh_key else None,
        "anchor_key_id": anchor_fields.get("anchor_key_id"),
        "anchor_issuer": anchor_fields.get("anchor_issuer"),
        "anchor_ns": anchor_fields.get("anchor_ns"),
        "anchor_identity": anchor_fields.get("anchor_identity"),
        "anchor_sig_file": anchor_fields.get("anchor_sig_file"),
        "anchor_fingerprint": anchor_fields.get("anchor_fingerprint"),
    })
    write_projection(root)
    # 锚信息进了回执（receipts.entries[].anchor），重签后必须同步刷新，
    # 否则读者拿到的回执仍指向旧锚（会在读者侧 fail-closed）。
    try:
        from core import receipts as _rc
        _rc.write(root)
        warn = ""
    except Exception as exc:
        # 逐行审查修正（2026-09-20）：回执刷新失败**不得静默**——锚已写进条目而回执没跟上，
        # 读者侧会 fail-closed；把失败带回调用方（CLI 打印 / --json 可见）。
        warn = ("回执未刷新：%s（修复指引：手动跑 nf library receipts --write）" % exc)
    out = {"id": hit["id"], "path": rel, "attestation": digest,
           "envelope_digest": att["envelope_digest"], "level": level,
           "key_id": anchor.get("key_id", ""),
           "identity": anchor_fields.get("anchor_identity", ""),
           "sig_file": anchor_fields.get("anchor_sig_file", "")}
    if warn:
        out["warn"] = warn
    return out


def to_manifest(root: str = ".") -> Dict[str, Any]:
    """机器清单（MCP/llms.txt 复用同一份事实）。"""
    rows = entries(root)
    return {"schema": "nf-library/1", "count": len(rows),
            "mirrors": [m["raw"] for m in MIRRORS],
            "entries": [{"id": e["id"], "title": e["fm"].get("title", e["id"]),
                         "type": e["fm"].get("type", ""),
                         "status": e["fm"].get("status", "active"),
                         "license": e["fm"].get("license", ""),
                         "path": e["path"]} for e in rows]}
