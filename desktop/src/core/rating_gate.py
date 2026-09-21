"""内容分级门（挂账收口：原触发条件 = 「馆藏出现分级消费方」）。

内部差距实证：`library/INDEX.md` 登记表有「形态 / 许可 / 状态」列，**没有分级列**；
条目的 frontmatter 也没有 `rating` 字段——投稿须知里连「分级」二字都没出现。
后果：消费方（家长控制、平台分级、检索过滤）**无从判断**一件馆藏适龄与否，
只能读了才知道；而 NF 的门禁对此完全沉默（`license_gate` 只管许可）。

设计纪律（与 `license_gate` 同源，不另造标准）：
- **真源 = 条目 frontmatter**（`rating:`），投影 = INDEX「分级」列（由 `nf library reindex` 生成）；
- 取值 = 声明件 `library/intake.json: rating.vocabulary` 词表（general / teen / mature / unrated），
  词表以**声明**为准——改词表 = 改声明件，门禁自动跟随（不写死在代码里）；
- `unrated` 是**显式声明未分级**，不是缺省：缺字段 = FAIL（分级是消费方选择的前提，不许沉默）；
- 本门只判「声明在场且合规」，**不替投稿人做适龄判断**（那是内容责任，不是机器责任）。
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Tuple

INTAKE_REL = "library/intake.json"
DEFAULT_VOCAB = ("general", "teen", "mature", "unrated")


def vocabulary(root: str = ".") -> List[str]:
    """分级词表真源 = library/intake.json 的 rating.vocabulary（缺失即用默认值）。"""
    path = Path(root) / INTAKE_REL
    if not path.is_file():
        return list(DEFAULT_VOCAB)
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except ValueError:
        return list(DEFAULT_VOCAB)
    vocab = ((doc.get("rating") or {}).get("vocabulary") or [])
    return [str(v) for v in vocab] or list(DEFAULT_VOCAB)


def scan(root: str = ".") -> Tuple[List[str], Dict[str, Any]]:
    """馆藏分级声明体检 → (issues, stats)。"""
    from core import library  # 延迟导入：避免与 library↔rating 形成导入环

    issues: List[str] = []
    vocab = vocabulary(root)
    rows = library.entries(root)
    counts: Dict[str, int] = {}
    for e in rows:
        fm = e["fm"]
        rating = str(fm.get("rating") or "").strip()
        if not rating:
            issues.append("%s 缺 frontmatter `rating`（修复指引：取值为 %s；未定级写 unrated "
                          "而非留空——分级是消费方选择的前提）" % (e["id"], "/".join(vocab)))
            continue
        if rating not in vocab:
            issues.append("%s 的 rating 越词表：%s（允许：%s；词表真源 = %s）"
                          % (e["id"], rating, "/".join(vocab), INTAKE_REL))
            continue
        counts[rating] = counts.get(rating, 0) + 1
    # 声明面须在场（词表可声明，才谈得上「按声明判」）
    path = os.path.join(root, INTAKE_REL)
    if os.path.isfile(path):
        with open(path, encoding="utf-8") as fh:
            doc = json.loads(fh.read())
        if not ((doc.get("rating") or {}).get("vocabulary")):
            issues.append("%s 缺 rating.vocabulary 声明（修复指引：分级词表须成文，"
                          "门禁按声明判而不写死）" % INTAKE_REL)
    else:
        issues.append("缺 %s（修复指引：投稿闸门声明件须在场）" % INTAKE_REL)
    stats = {"entries": len(rows), "vocabulary": vocab, "counts": counts,
             "issues": len(issues)}
    return issues, stats


def summary(stats: Dict[str, Any]) -> str:
    parts = "、".join("%s=%d" % (k, v) for k, v in sorted((stats.get("counts") or {}).items()))
    return "馆藏 %d 件 · 分级 %s · 词表 %s" % (
        stats.get("entries", 0), parts or "—", "/".join(stats.get("vocabulary") or []))
