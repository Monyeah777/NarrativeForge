"""集成面（integrations）：把 NF 的**接入面**做成可机检的目录（真源 + 人读投影）。

为什么需要（内部差距实证 2026-10-05）：NF 的接入面已有一批（MCP / LSP / CLI / TUI / 图书馆 raw /
Agent Skill / AGENTS 规则出口 / CCV3 出口 / npm 启动器 / Rust 快线 / .NET 引擎 / A2A 卡片），
但它们散在 README 表、docs/*、各子目录 README 与导出物里——**没有一处能回答「NF 现在有哪些
接入面、各自入口是什么、件还在不在」**。本模块把接入面做成三件可证的事：

1. 真源 integrations/<id>/integration.json（描述件：kind / status / 入口 / 文档 / 证据）；
2. 人读投影 integrations/README.md 的生成区（nf:integrations 标记，逐字对账）；
3. 判据（check38 子扫描）：描述件可解析 / id 唯一且与目录同名 / 词表封闭 / 入口与文档与证据件
   **真实在场** / 投影 == 实时渲染 / 无孤儿目录。

纪律：纯标准库；只读；无网络；同输入同输出；缺件/空根如实报 issue 不裸崩。
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

DIR = "integrations"
INDEX_REL = "integrations/README.md"
BEGIN = "<!-- nf:integrations:begin -->"
END = "<!-- nf:integrations:end -->"
SCHEMA = "nf-integration/1"
KINDS = ("server", "client", "cli", "library", "editor", "package", "export", "collection")
STATUSES = ("active", "proposed", "deprecated")
REQUIRED = ("schema", "id", "title", "kind", "status", "version", "codeowner", "tier",
            "entry", "docs", "evidence")
SCHEMA_ID = "nf:integration"
STRINGS_SCHEMA_ID = "nf:integration-strings"
STRINGS_NAME = "strings.json"
_PATH_TOKEN = re.compile(r"[A-Za-z0-9_./\\-]+\\.(?:py|sh|ps1|cmd|mjs|js|json|md|csproj|toml)")


def entries(root: str = ".") -> List[Dict[str, Any]]:
    """在场接入面描述件（按目录名排序；坏件也返回，由 check 如实报）。"""
    d = Path(root) / DIR
    out: List[Dict[str, Any]] = []
    if not d.is_dir():
        return out
    for sub in sorted(p for p in d.iterdir() if p.is_dir()):
        f = sub / "integration.json"
        if not f.is_file():
            out.append({"id": sub.name, "rel": DIR + "/" + sub.name, "_missing": True})
            continue
        rec: Dict[str, Any] = {"rel": DIR + "/" + sub.name}
        try:
            rec.update(json.loads(f.read_text(encoding="utf-8")))
        except (OSError, ValueError) as exc:
            rec["_bad"] = str(exc)
        out.append(rec)
    return out


def render_index(root: str = ".") -> str:
    """人读投影（生成区内容）：接入面一张表，逐条给入口与文档。"""
    rows = ["| id | 面 | 类型 | 状态 | 版本 | 责任方 | 入口 | 文档 |",
            "|---|---|---|---|---|---|---|---|"]
    for e in entries(root):
        if e.get("_missing") or e.get("_bad"):
            rows.append("| " + str(e.get("id", "?")) + " | — | — | — | （坏件/缺件） | — |")
            continue
        entry = e.get("entry") or {}
        cmd = entry.get("command") or entry.get("path") or ""
        docs = e.get("docs") or []
        rows.append("| " + str(e.get("id", "?")) + " | " + str(e.get("title", ""))
                    + " | " + str(e.get("kind", "")) + " | " + str(e.get("status", ""))
                    + " | " + str(e.get("version", "")) + " | " + str(e.get("codeowner", ""))
                    + " | " + cmd + " | " + " · ".join(str(d) for d in docs) + " |")
    return "\n".join(rows)


def check(root: str = ".") -> Tuple[List[str], Dict[str, Any]]:
    """接入面机检（check38 子扫描口径）。缺根如实报 issue，不裸崩。"""
    r = Path(root)
    if not (r / "verify.sh").is_file():
        return (["读不到仓库根（缺 verify.sh）——接入面须在 NF 仓库根运行"], {})
    issues: List[str] = []
    recs = entries(root)
    if not recs:
        issues.append("缺接入面目录 " + DIR + "/（修复指引：每个接入面一个子目录 + integration.json；"
                      "字段见 core/integrations.py::REQUIRED）")
    seen: Dict[str, str] = {}
    kinds: List[str] = []
    # 配置即契约：描述件必须过 protocol/schema/integration.schema.json（缺 schema 即红）。
    _schema = None
    try:
        from core import schema_lint as _sl
        _schema = _sl.load_schema(str(r), SCHEMA_ID)
        if _schema is None:
            issues.append("缺接入面 schema（%s；修复指引：protocol/schema/integration.schema.json）"
                          % SCHEMA_ID)
    except Exception as exc:
        issues.append("接入面 schema 校验不可用：%s" % exc)
    for e in recs:
        rel = e["rel"]
        if e.get("_missing"):
            issues.append(rel + " 缺 integration.json（修复指引：补齐描述件，或删掉该目录）")
            continue
        if e.get("_bad"):
            issues.append(rel + " integration.json 不可解析：" + e["_bad"])
            continue
        miss = [k for k in REQUIRED if k not in e]
        if miss:
            issues.append(rel + " 缺字段：" + "、".join(miss))
            continue
        if e["schema"] != SCHEMA:
            issues.append(rel + " schema 应为 " + SCHEMA + "（实为 " + str(e["schema"]) + "）")
        if str(e["id"]) != Path(rel).name:
            issues.append(rel + " id=" + str(e["id"]) + " 与目录名不一致（修复指引：id 即目录名）")
        if e["id"] in seen:
            issues.append("接入面 id 重复：" + str(e["id"]) + "（" + seen[e["id"]] + " 与 " + rel + "）")
        seen[e["id"]] = rel
        if e["kind"] not in KINDS:
            issues.append(rel + " kind 越出词表：" + str(e["kind"]) + "（词表：" + "/".join(KINDS) + "）")
        if e["status"] not in STATUSES:
            issues.append(rel + " status 越出词表：" + str(e["status"])
                          + "（词表：" + "/".join(STATUSES) + "）")
        kinds.append(str(e["kind"]))
        if _schema is not None:
            from core import schema_lint as _sl2
            _desc = {k: v for k, v in e.items() if k != "rel" and not k.startswith("_")}
            for _v in _sl2.subset_validate(_desc, _schema, rel):
                issues.append("%s 越出 integration schema：%s" % (rel, _v))
        entry = e["entry"] if isinstance(e["entry"], dict) else {}
        if not (entry.get("command") or entry.get("path")):
            issues.append(rel + " entry 缺 command/path（修复指引：给可跑的入口或路径锚）")
        if entry.get("path") and not (r / str(entry["path"])).exists():
            issues.append(rel + " entry.path 不在场：" + str(entry["path"]))
        for tok in _PATH_TOKEN.findall(str(entry.get("command") or "")):
            if not (r / tok).exists():
                issues.append(rel + " entry.command 引用的件不在场：" + tok)
        for key in ("docs", "evidence"):
            vals = e[key] if isinstance(e[key], list) else [e[key]]
            for v in vals:
                if not str(v).strip():
                    issues.append(rel + " " + key + " 含空项")
                elif not (r / str(v)).exists():
                    issues.append(rel + " " + key + " 不在场：" + str(v))
    # 每接入面的本地化字符串（HA strings.json 同型）：在场 + 过 schema + 语言集 == 注册语言
    try:
        from core import locales as _lc
        _reg, _ = _lc.registry(str(r))
        _want = {str(x.get("id", "")).lower() for x in ((_reg or {}).get("locales") or [])}
    except Exception:
        _want = set()
    _str_schema = None
    try:
        from core import schema_lint as _sl3
        _str_schema = _sl3.load_schema(str(r), STRINGS_SCHEMA_ID)
        if _str_schema is None:
            issues.append("缺接入面字符串 schema（%s；修复指引：protocol/schema/integration_strings.schema.json）"
                          % STRINGS_SCHEMA_ID)
    except Exception as exc:
        issues.append("接入面字符串 schema 校验不可用：%s" % exc)
    for e in recs:
        if e.get("_missing") or e.get("_bad") or "id" not in e:
            continue
        sid = str(e["id"])
        sf = r / DIR / sid / STRINGS_NAME
        if not sf.is_file():
            issues.append(DIR + "/" + sid + " 缺 " + STRINGS_NAME
                          + "（修复指引：逐语言 title/summary；语言集见 protocol/locales.json）")
            continue
        try:
            sdata = json.loads(sf.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            issues.append(DIR + "/" + sid + " " + STRINGS_NAME + " 不可解析：" + str(exc))
            continue
        if _str_schema is not None:
            for _v in _sl3.subset_validate(sdata, _str_schema, DIR + "/" + sid + "/" + STRINGS_NAME):
                issues.append(DIR + "/" + sid + " strings 越界：" + _v)
        got = {str(k).lower() for k in (sdata.get("locales") or {})}
        if _want and got != _want:
            _miss = sorted(_want - got)
            _extra = sorted(got - _want)
            if _miss:
                issues.append(DIR + "/" + sid + " strings 缺语言：" + "、".join(_miss))
            if _extra:
                issues.append(DIR + "/" + sid + " strings 多出未注册语言：" + "、".join(_extra)
                              + "（修复指引：与 protocol/locales.json 对齐）")
    idx = r / INDEX_REL
    if not idx.is_file():
        issues.append("缺接入面人读投影 " + INDEX_REL + "（修复指引：加 " + BEGIN + " / " + END + " 生成区）")
    else:
        txt = idx.read_text(encoding="utf-8")
        m = re.search(re.escape(BEGIN) + r"\n(.*?)\n" + re.escape(END), txt, re.S)
        if not m:
            issues.append(INDEX_REL + " 缺生成区标记（" + BEGIN + " / " + END + "）")
        elif m.group(1).strip() != render_index(root).strip():
            issues.append(INDEX_REL + " 生成区与实时渲染不一致（修复指引：按 render_index 重出该区）")
    return issues, {"count": len([x for x in recs if not x.get("_missing") and not x.get("_bad")]),
                    "ids": sorted(seen), "kinds": sorted(set(kinds))}


def localized(root: str = ".", integration_id: str = "", locale: str = "zh") -> Dict[str, str]:
    """取某接入面某语言的字符串（缺件缺语言返回空 dict——调用方自行兜底，不臆造）。"""
    p = Path(root) / DIR / integration_id / STRINGS_NAME
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    loc = (data.get("locales") or {}).get(locale) or {}
    return {k: str(v) for k, v in loc.items()}


#: 扫描器统一入口名（与 repo_stats / release_gate / locales 一致）。
scan = check
