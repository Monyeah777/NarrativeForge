"""语言面（locales）：**注册表 + 文件即真源 + 逐面同事实 + 覆盖面诚实声明**。

为什么需要（内部差距实证 2026-10-05）：入口此前是硬编码的两份——check34 的断言写死
`README.md` / `README.en.md`，「加第三种语言」既没有登记面也没有判据面。第一轮升级为
「文件即真源」的注册面；第二轮（对标同类顶尖项目整站 i18n）再补两件：

1. **注册表** `protocol/locales.json`：逐语言的入口、责任方（codeowner）、**覆盖面声明**
   （`entry` 只译入口 / `entry+guides` 另译指南）与**指南翻译表**——语言面的边界从「没写」
   变成「写了且可核」，禁止悄悄多一本单语文档。
2. **双向判据**：声明了却缺件 → FAIL；在 `docs/<lang>/` 下放了没声明的译件 → 也 FAIL
   （防「未声明的多语面」）。coverage=`entry` 的语言**不得**有指南译件（防虚标覆盖面）。

其余判据不变：机读事实锚点齐、**语言切换行逐条列出全部在场语言**、H2 结构对齐、
canonical 引用的 ASCII .md 件在每面都出现。

纪律：纯标准库；只读；无网络；同输入同输出；缺件/空根如实报 issue 不裸崩。
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REGISTRY_REL = "protocol/locales.json"
CANONICAL = "README.md"
SWITCH_MARK = "<!-- nf:locales -->"
#: 覆盖面词表：entry = 只译入口；entry+guides = 入口 + registry 声明的指南。
COVERAGES = ("entry", "entry+guides")
_LOCALE_RE = re.compile(r"^README\.([A-Za-z][A-Za-z0-9-]*)\.md$")
_LANG_LABEL = {"zh": "中文", "en": "English", "ja": "日本語", "ko": "한국어", "fr": "Français"}
_H2_RE = re.compile(r"(?m)^## ")
_MD_REF_RE = re.compile(r"[A-Za-z0-9_\-\./]+\.md")
_DOCS_LANG_RE = re.compile(r"^[A-Za-z][A-Za-z0-9-]*$")


def registry(root: str = ".") -> Tuple[Optional[Dict[str, Any]], List[str]]:
    """读语言面注册表（缺件/坏件如实报，不裸崩）。"""
    p = Path(root) / REGISTRY_REL
    if not p.is_file():
        return None, ["缺语言面注册表 %s（修复指引：声明 locales / guides；"
                      "canonical = zh）" % REGISTRY_REL]
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return None, ["%s 不可解析：%s" % (REGISTRY_REL, exc)]
    issues: List[str] = []
    if data.get("schema") != "nf-locales/1":
        issues.append("%s schema 应为 nf-locales/1" % REGISTRY_REL)
    locs = data.get("locales")
    if not isinstance(locs, list) or len(locs) < 2:
        issues.append("%s 的 locales 须为 ≥2 项数组" % REGISTRY_REL)
    return data, issues


def entries(root: str = ".") -> List[Tuple[str, str]]:
    """在场语言面（注册表优先；缺注册表退回文件扫描，保证空根/临时根仍可判）。"""
    data, _ = registry(root)
    out: List[Tuple[str, str]] = []
    if data and isinstance(data.get("locales"), list):
        for item in data["locales"]:
            if isinstance(item, dict) and item.get("id") and item.get("entry"):
                out.append((str(item["id"]).lower(), str(item["entry"])))
    if out:
        return out
    r = Path(root)
    out = [("zh", CANONICAL)]
    if r.is_dir():
        for p in sorted(r.glob("README.*.md")):
            m = _LOCALE_RE.match(p.name)
            if m:
                out.append((m.group(1).lower(), p.name))
    return out


def label(lang: str) -> str:
    """语言人读名（不在表内就原样，不编造）。"""
    return _LANG_LABEL.get(lang, lang)


def switcher(locales: List[Tuple[str, str]], current: str) -> str:
    """语言切换行：当前语言加粗不链接，其余给链接——逐条列出**全部在场语言**。"""
    parts: List[str] = []
    for lang, fn in locales:
        text = label(lang)
        parts.append("**%s**" % text if lang == current else "[%s](%s)" % (text, fn))
    # 不用 emoji：issue 消息会把期望行原样回吐，而 GBK 控制台编不出 U+1F310。
    return "%s 语言 / Languages：%s" % (SWITCH_MARK, " · ".join(parts))


def anchors() -> Tuple[str, ...]:
    """每面都必须出现的机读事实锚点（期望值取自 quality_baseline，不写字面量）。"""
    from core import quality_baseline as qb
    return ("check1-%d" % qb.EXPECTED_CHECKS, "PASS=%d" % qb.EXPECTED_PASS,
            "01_核心协议.md", "06_Agent执行协议.md", "llms.txt", "community/")


def _docs(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """文档面登记（新键 docs；旧键 guides 兼容）。"""
    raw = data.get("docs")
    if raw is None:
        raw = data.get("guides")
    return [g for g in (raw or []) if isinstance(g, dict)]


def _tpath(value: Any) -> Tuple[str, str]:
    """译件条目 → (路径, 登记源件摘要)；字符串形式登记摘要为空（判据会要求补签）。"""
    if isinstance(value, dict):
        return str(value.get("path", "")), str(value.get("source_sha256", ""))
    return str(value), ""


def _sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _declared_translations(data: Dict[str, Any]) -> Dict[str, set]:
    """→ {locale_id: {已声明译件相对路径}}。"""
    out: Dict[str, set] = {}
    for g in _docs(data):
        for lang, value in (g.get("translations") or {}).items():
            tp, _ = _tpath(value)
            if tp:
                out.setdefault(str(lang).lower(), set()).add(tp)
    return out


def stamp(root: str = ".", write: bool = False) -> Dict[str, Any]:
    """给每个译件登记**当前源件摘要**（译件过期判据的真源）。

    write=False 只算（返回将要写入的映射）；write=True 覆写注册表的 docs[].translations[lang].source_sha256。
    """
    r = Path(root)
    p = r / REGISTRY_REL
    if not p.is_file():
        return {"ok": False, "issues": ["缺 %s" % REGISTRY_REL]}
    data = json.loads(p.read_text(encoding="utf-8"))
    stamped: List[str] = []
    for g in _docs(data):
        src = str(g.get("path", ""))
        sp = r / src
        if not src or not sp.is_file():
            continue
        digest = _sha256_file(sp)
        for lang, value in (g.get("translations") or {}).items():
            if isinstance(value, dict):
                value["source_sha256"] = digest
            else:
                g["translations"][lang] = {"path": str(value), "source_sha256": digest}
            stamped.append("%s ← %s" % (lang, src))
    if write:
        from core import atomic_write      # 真源件：原子写（与其余写面同待遇）
        atomic_write.write_text(str(p), json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    return {"ok": True, "stamped": stamped, "written": bool(write)}


def check(root: str = ".") -> Tuple[List[str], Dict[str, Any]]:
    """语言面机检（check34 口径）。缺根如实报 issue，不裸崩。"""
    r = Path(root)
    if not (r / "verify.sh").is_file():
        return (["读不到仓库根（缺 verify.sh）——语言面须在 NF 仓库根运行"], {})
    issues: List[str] = []
    data, reg_issues = registry(root)
    issues += reg_issues
    data = data or {}
    locs = entries(root)
    if len(locs) < 2:
        issues.append("语言面只有 %d 面（修复指引：注册表须声明 canonical + 至少一面译文）" % len(locs))
    canon = data.get("canonical") or "zh"
    if (canon, CANONICAL) not in locs:
        issues.append("注册表的 canonical=%s 未指向 %s" % (canon, CANONICAL))
    seen: Dict[str, str] = {}
    for item in (data.get("locales") or []):
        if not isinstance(item, dict):
            continue
        lid = str(item.get("id", "")).lower()
        if not lid:
            issues.append("%s 有 locale 缺 id" % REGISTRY_REL)
            continue
        if lid in seen:
            issues.append("语言 id 重复：%s" % lid)
        seen[lid] = str(item.get("entry", ""))
        if not str(item.get("label", "")).strip():
            issues.append("%s/%s 缺 label（人读语言名）" % (REGISTRY_REL, lid))
        if not str(item.get("codeowner", "")).strip():
            issues.append("%s/%s 缺 codeowner（语言面责任方）" % (REGISTRY_REL, lid))
        cov = str(item.get("coverage", ""))
        if cov not in COVERAGES:
            issues.append("%s/%s coverage 越出词表：%s（词表：%s）"
                          % (REGISTRY_REL, lid, cov, "/".join(COVERAGES)))
    # 入口面逐面（锚点 / 版本 / 切换行 / 结构 / 引件）
    zh = (r / CANONICAL).read_text(encoding="utf-8") if (r / CANONICAL).is_file() else ""
    zh_h2 = len(_H2_RE.findall(zh))
    zh_refs = sorted(set(_MD_REF_RE.findall(zh)))
    want = anchors()
    for lang, fn in locs:
        p = r / fn
        if not p.is_file():
            issues.append("语言面缺件 %s（修复指引：补齐该语言入口，或从注册表移除）" % fn)
            continue
        txt = p.read_text(encoding="utf-8")
        for a in want:
            if a not in txt:
                issues.append("%s 缺机读锚点 %s（修复指引：与 %s 同步机读事实）" % (fn, a, CANONICAL))
        if not re.search(r"v\d+\.\d+", txt):
            issues.append("%s 缺版本号（vX.Y）" % fn)
        line = switcher(locs, lang)
        found = re.search(r"(?m)^" + re.escape(SWITCH_MARK) + r".*$", txt)
        if not found or found.group(0).strip() != line:
            issues.append("%s 缺/错语言切换行（期望逐字：%s）" % (fn, line))
        if fn != CANONICAL:
            h2 = len(_H2_RE.findall(txt))
            if h2 != zh_h2:
                issues.append("语言面结构不对齐：%s H2=%d ≠ %s H2=%d" % (fn, h2, CANONICAL, zh_h2))
            miss = [x for x in zh_refs if x not in txt]
            if miss:
                issues.append("%s 缺 canonical 引用的件：%s" % (fn, "、".join(miss[:5])))
    # 文档面：声明 ⇄ 在场，双向；路径须镜像（docs/<lang>/<rest> ← docs/<rest>）；源件摘要须与当前字节一致（防过期）
    declared = _declared_translations(data)
    guides = _docs(data)
    for g in guides:
        src = str(g.get("path", ""))
        if not src:
            issues.append("%s 有 docs 条目缺 path" % REGISTRY_REL)
            continue
        sp = r / src
        if not sp.is_file():
            issues.append("文档原文不在场：%s" % src)
            continue
        src_digest = _sha256_file(sp)
        for lang, value in (g.get("translations") or {}).items():
            tp, tsha = _tpath(value)
            tfile = r / tp
            if not tp or not tfile.is_file():
                issues.append("文档译件不在场：%s（%s ← %s）" % (tp or "（缺 path）", lang, src))
                continue
            # 路径镜像：译件必须落 docs/<lang>/ 下，且剩余路径与源件一致
            if not src.startswith("docs/") or not tp.startswith("docs/" + str(lang) + "/"):
                issues.append("译件路径未镜像：%s（%s 的译文应落 docs/%s/<原文相对路径>）" % (tp, src, lang))
            elif tp[len("docs/" + str(lang) + "/"):] != src[len("docs/"):]:
                issues.append("译件路径未镜像：%s ≠ docs/%s/%s" % (tp, lang, src[len("docs/"):]))
            if not tsha:
                issues.append("译件未签源件摘要：%s（修复指引：跑 nf locales --write 重签 source_sha256）" % tp)
            elif tsha != src_digest:
                issues.append("译件过期：%s 的 source_sha256 与 %s 当前字节不一致（修复指引：更新译文后跑 nf locales --write 重签）"
                              % (tp, src))
    for item in (data.get("locales") or []):
        if not isinstance(item, dict):
            continue
        lid = str(item.get("id", "")).lower()
        if lid == str(canon).lower():
            continue        # canonical 语言的「译件」就是 guide 原文，不参与译件齐备判据
        cov = str(item.get("coverage", ""))
        got = declared.get(lid, set())
        if cov == "entry+guides" and guides and len(got) < len(guides):
            issues.append("%s 声明 entry+guides 但指南译件不全（缺 %d 件）"
                          % (lid, len(guides) - len(got)))
        if cov == "entry" and got:
            issues.append("%s 声明 coverage=entry 却有指南译件 %s（修复指引：升为 entry+guides 或删译件）"
                          % (lid, "、".join(sorted(got))))
    # 未声明的多语面：docs/<lang>/ 下的 md 必须被注册表声明
    docs = r / "docs"
    lang_ids = {str(i.get("id", "")).lower() for i in (data.get("locales") or [])
                if isinstance(i, dict)}
    if docs.is_dir():
        # 只看**注册在册语言**的子目录——docs/examples 这类同形目录不是语言面。
        for d in sorted(p for p in docs.iterdir()
                        if p.is_dir() and p.name.lower() in lang_ids):
            declared_files = set()
            for s in declared.values():
                declared_files |= s
            for f in sorted(d.glob("*.md")):
                rel = "docs/%s/%s" % (d.name, f.name)
                if rel not in declared_files:
                    issues.append("未声明的多语文档 %s（修复指引：在 %s 的 guides 里登记或删除）"
                                  % (rel, REGISTRY_REL))
    stats: Dict[str, Any] = {"locales": [l for l, _ in locs], "files": [f for _, f in locs],
                             "canonical": canon, "guides": len(guides),
                             "translations": sum(len(v) for v in declared.values()),
                             "switcher": switcher(locs, locs[0][0])}
    return issues, stats


#: 扫描器统一入口名（与 repo_stats / release_gate / integrations 一致）。
scan = check
