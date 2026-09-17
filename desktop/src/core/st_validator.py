"""ST 制卡校验器原型 v0（任务书 A-S3）：卡 / 世界书 / MVU 变量 → 可复用报告。

零新依赖（仅标准库）。只做**可自动化项**：
- **R1 结构完备** → C1 可解析且版本可判 / C2 版本字段正确 / C3 基础六字段齐备非空；
- **R3 世界书健康** → W1 entries 结构合法 / W2 key 卫生（逗号分隔符、同书重复）/ W5 扫描范围提示；
- **R4 变量系统** → V2 初始值完备（initial ⊆ 变量集合）/ V5 命名与结构建议（宏、数组优先 record）。

边界（对齐规范与 B 线红线）：**不解析 PNG 实卡**（chunk/base64 解析属后续）、**不新增读写工具**、
级别映射沿用 `protocol/st_quality.json`：M→fail · S→warn · R→info。
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

SEV = {"M": "fail", "S": "warn", "R": "info"}
REQUIRED_SIX = ("name", "description", "personality", "scenario",
                "first_mes", "mes_example")
SPEC_EXPECT = {"chara_card_v2": "2.0", "chara_card_v3": "3.0"}


def _issue(rid: str, level: str, detail: str) -> Dict[str, str]:
    return {"rule": rid, "level": level, "severity": SEV.get(level, "info"),
            "detail": detail}


def check_card(doc: Dict[str, Any]) -> List[Dict[str, str]]:
    """R1：卡结构（V1/V2/V3）。"""
    out: List[Dict[str, str]] = []
    spec = str(doc.get("spec") or "")
    data = doc.get("data") if isinstance(doc.get("data"), dict) else None
    if spec:
        if spec not in SPEC_EXPECT:
            out.append(_issue("C1", "M", "spec 非法：%s（应为 chara_card_v2/v3）" % spec))
        want = SPEC_EXPECT.get(spec)
        got = str(doc.get("spec_version") or (data or {}).get("spec_version") or "")
        if want and got != want:
            out.append(_issue("C2", "M", "spec_version 应为 %s，实为 %s" % (want, got or "(缺)")))
        body = data or {}
    elif data is not None:
        out.append(_issue("C1", "M", "有 data 但缺 spec——无法判定 V2/V3"))
        body = data
    else:
        body = doc                      # V1 平铺
    for k in REQUIRED_SIX:
        v = body.get(k)
        if v is None or (isinstance(v, str) and not v.strip()):
            out.append(_issue("C3", "M", "基础字段缺失或为空：%s" % k))
    return out


def check_worldbook(doc: Dict[str, Any]) -> List[Dict[str, str]]:
    """R3：世界书健康。"""
    out: List[Dict[str, str]] = []
    raw = doc.get("entries")
    if raw is None and isinstance(doc.get("character_book"), dict):
        raw = doc["character_book"].get("entries")
    rows: List[Dict[str, Any]] = []
    if isinstance(raw, dict):
        rows = [v for v in raw.values() if isinstance(v, dict)]
    elif isinstance(raw, list):
        rows = [v for v in raw if isinstance(v, dict)]
    else:
        return [_issue("W1", "M", "entries 缺失或不是 dict/list（ST convertCharacterBook 要求数组）")]
    seen: Dict[str, int] = {}
    for i, e in enumerate(rows):
        keys = e.get("keys") if e.get("keys") is not None else e.get("key")
        if isinstance(keys, str):
            keys = [keys]
        keys = [str(k) for k in (keys or []) if str(k).strip()]
        if not keys:
            out.append(_issue("W1", "M", "第 %d 条 key 为空" % i))
        if not str(e.get("content") or "").strip():
            out.append(_issue("W1", "M", "第 %d 条 content 为空" % i))
        for k in keys:
            if "," in k:
                out.append(_issue("W2", "S", "key 含逗号（会被当分隔符）：%s" % k))
            seen[k] = seen.get(k, 0) + 1
        if e.get("scanDepth") is None:
            out.append(_issue("W5", "S", "第 %d 条未声明 scanDepth（触发可能在扫描范围外）" % i))
    for k, n in seen.items():
        if n > 1:
            out.append(_issue("W2", "S", "同书内 key 重复 %d 次：%s" % (n, k)))
    return out


def check_mvu_variables(doc: Dict[str, Any]) -> List[Dict[str, str]]:
    """R4：MVU 变量系统。"""
    out: List[Dict[str, str]] = []
    names = [str(v.get("name")) for v in (doc.get("variables") or []) if v.get("name")]
    if not names:
        return [_issue("V2", "M", "变量表为空——无 schema 可校验")]
    init = doc.get("initial") or {}
    extra = sorted(set(init) - set(names))
    if extra:
        out.append(_issue("V2", "M", "initial 含未声明变量：%s" % "、".join(extra)))
    missing = sorted(set(names) - set(init))
    if missing:
        out.append(_issue("V2", "M", "变量缺初始值：%s" % "、".join(missing)))
    for n in names:
        if "{{" in n or "}}" in n:
            out.append(_issue("V5", "S", "变量名含宏：%s" % n))
        if n.startswith(("_", "$")):
            out.append(_issue("V4", "S", "变量名带可见性前缀（%s）——确认语义正确" % n[0]))
    for v in (doc.get("variables") or []):
        if str(v.get("kind")) == "array":
            out.append(_issue("V5", "S", "变量 %s 为 array，规范建议优先 record" % v.get("name")))
    return out


def validate(path: str) -> Dict[str, Any]:
    """按形状分派（卡 / 世界书 / MVU 变量）→ 报告。"""
    p = Path(path)
    doc = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(doc, dict):
        return {"path": path, "kind": "unknown", "issues": [
            _issue("C1", "M", "顶层不是对象，无法判定资产类型")]}
    if doc.get("variables") is not None and doc.get("initial") is not None:
        kind, issues = "mvu-variables", check_mvu_variables(doc)
    elif doc.get("entries") is not None or doc.get("character_book") is not None:
        kind, issues = "worldbook", check_worldbook(doc)
    elif doc.get("spec") is not None or doc.get("name") is not None:
        kind, issues = "card", check_card(doc)
    else:
        kind, issues = "unknown", [_issue("C1", "M", "无法识别资产类型（无 spec/name/entries/variables 特征）")]
    return {"path": path, "kind": kind, "issues": issues,
            "counts": {s: sum(1 for i in issues if i["severity"] == s)
                       for s in ("fail", "warn", "info")}}


def report_markdown(rep: Dict[str, Any]) -> str:
    c = rep.get("counts", {})
    out = ["# ST 制卡校验报告", "",
           "- 对象：`%s`" % rep.get("path"), "- 判定形态：**%s**" % rep.get("kind"),
           "- 结果：fail %d · warn %d · info %d" % (c.get("fail", 0), c.get("warn", 0),
                                                    c.get("info", 0)), ""]
    if not rep.get("issues"):
        out += ["**零问题**——该对象在可自动化项（R1/R3/R4）上全部通过。", ""]
    else:
        out += ["| 规则 | 级别 | 严重度 | 说明 |", "|---|---|---|---|"]
        for i in rep["issues"]:
            out.append("| %s | %s | %s | %s |" % (i["rule"], i["level"], i["severity"],
                                                  i["detail"]))
        out.append("")
    out += ["> 本报告只覆盖**可自动化项**（R1 结构 / R3 世界书 / R4 变量）；",
            "> R2 引用一致、R5 可复现、R6 长会话友好等仍需人工清单（见 `docs/st-quality-checklist.md`）。",
            "> 校验器原型 v0 不解析 PNG 实卡；输入为已解出的 JSON。", ""]
    return "\n".join(out)
