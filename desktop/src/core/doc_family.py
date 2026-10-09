"""声明件驱动的文档族门禁的**公共实现**（同一件事一处实现）。

为什么单独成件（2026-10-09 取证）：静态扫「重复函数体」实测出三类同源拷贝——

- audit / handover / postmortem 各写一份 decl()（读 protocol/*.json 声明件）
  与 entries()（glob 到 frontmatter 条目）；
- handover / postmortem / decisions 各写一份「verify.sh 在册 check 编号抽取」，
  handover 与 postmortem 又各写一份「引用解析」；
- decisions / patterns 的 write_projection / check_projection 是两份逐行近似的拷贝
  （只差索引路径、生成区标记与提示语）。

按本仓纪律，同一件事两份实现的风险是「改一份忘一份」（同 md_blocks 收口 handover /
postmortem 两份 _bullet_blocks 的由来，见 test_dead_code::test_no_duplicate_bodies）。
本模块把这一族的**机械面**收敛到一处：各门禁只保留自己的真源声明、专属判据与投影渲染。

纪律（SDP）：本件是**稳定侧**——只依赖叶子件（library_entries 的 frontmatter 解析、
atomic_write 的原子写），由更不稳的门禁模块依赖它；故 parse_frontmatter 从
core.library_entries 取（core.library 是 I 更高的转发面，反向依赖会构成 SDP 违例）。
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List

from core import atomic_write
from core.library_entries import parse_frontmatter

VERIFY_REL = "verify.sh"
_DATED = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_CHECK = re.compile(r"^check(\d+)$")
_ADR = re.compile(r"^ADR-\d{4}$")
_CHECK_DEF = re.compile(r"^check(\d+)\(\)\{", re.M)


def load_decl(root: str, rel: str) -> Dict[str, Any]:
    """读协议声明件（protocol/*.json）；缺件返回 {}（是否判死由调用方决定）。"""
    p = Path(root) / rel
    return json.loads(p.read_text(encoding="utf-8")) if p.is_file() else {}


def entries(root: str, glob_pattern: str) -> List[Dict[str, Any]]:
    """glob 到条目清单（{path, file, fm, body}；path 为仓库相对路径，按路径排序）。"""
    r = Path(root)
    out: List[Dict[str, Any]] = []
    for p in sorted(r.glob(glob_pattern)):
        fm, body = parse_frontmatter(p.read_text(encoding="utf-8"))
        out.append({"path": p.relative_to(r).as_posix(), "file": p.name,
                    "fm": fm or {}, "body": body or ""})
    return out


def check_numbers(root: str) -> set:
    """verify.sh 在册的 check 编号集合（引用判据用；缺件返回空集）。"""
    p = Path(root) / VERIFY_REL
    if not p.is_file():
        return set()
    return set(_CHECK_DEF.findall(p.read_text(encoding="utf-8")))


def frontmatter_issues(fm: Dict[str, Any], decl: Dict[str, Any], *,
                       required: Iterable[str], vocab_key: str, field: str,
                       default_vocab: Iterable[str]) -> List[str]:
    """frontmatter 的公共三段判据：必填齐 / 词表内 / 日期形态。

    词表键与字段名由调用方声明（audit 用 verdict_vocabulary/verdict，
    handover / postmortem 用 status_vocabulary/status），故本条可一源多用。
    """
    out: List[str] = []
    for k in (decl.get("required_fields") or list(required)):
        if not fm.get(k):
            out.append("缺必填字段：%s" % k)
    if str(fm.get(field)) not in (decl.get(vocab_key) or list(default_vocab)):
        out.append("%s 越词表：%s" % (field, fm.get(field)))
    if not _DATED.match(str(fm.get("date") or "")):
        out.append("date 非 YYYY-MM-DD：%s" % fm.get("date"))
    return out


def refs_issues(root: str, refs: Any, checks: set, *, label: str = "引用",
                allow_adr: bool = False, strip_brackets: bool = False) -> List[str]:
    """引用解析：checkN（须在册）/ 仓库真实件路径 /（可选）ADR-N 放行。

    label 决定消息前缀（handover 用 refs、postmortem 用 引用，语义同源、措辞各自在册）。
    """
    out: List[str] = []
    if isinstance(refs, str):
        refs = [refs]
    r = Path(root)
    for ref in (refs or []):
        s = str(ref).strip()
        if strip_brackets and s.startswith("[") and s.endswith("]"):
            s = s.strip("[]").strip()
        c = _CHECK.match(s)
        if c:
            if c.group(1) not in checks:
                out.append("%s 指向不存在的 check：%s" % (label, s))
            continue
        if allow_adr and _ADR.match(s):
            continue
        if not (r / s.replace("\\", "/")).exists():
            out.append("%s 无法解析：%s" % (label, s))
    return out


def write_index(root: str, *, index_rel: str, header: str, begin: str, end: str,
                block: str) -> Dict[str, Any]:
    """写生成投影：缺件则建头，生成区就地替换，无标记则追加（唯一写盘入口）。"""
    p = Path(root) / index_rel
    if not p.is_file():
        p.parent.mkdir(parents=True, exist_ok=True)
        atomic_write.write_text(p, header + begin + "\n" + end + "\n")
    text = p.read_text(encoding="utf-8")
    if begin in text and end in text:
        new = text[:text.index(begin)] + block + text[text.index(end) + len(end):]
    else:
        new = text.rstrip("\n") + "\n\n" + block + "\n"
    changed = new != text
    if changed:
        atomic_write.write_text(p, new)
    return {"changed": changed, "path": index_rel}


def check_index(root: str, *, index_rel: str, begin: str, end: str, block: str,
                missing_hint: str, mismatch: str) -> List[str]:
    """校验生成投影与实时重算一致（缺件 / 缺生成区 / 漂移各给修复指引）。"""
    p = Path(root) / index_rel
    if not p.is_file():
        return ["缺 %s（修复指引：%s）" % (index_rel, missing_hint)]
    text = p.read_text(encoding="utf-8")
    if begin not in text or end not in text:
        return ["%s 缺生成区标记" % index_rel]
    cur = text[text.index(begin):text.index(end) + len(end)]
    return [] if cur == block else [mismatch]
