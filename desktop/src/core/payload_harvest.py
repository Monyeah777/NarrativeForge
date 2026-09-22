"""事件载荷收割与类型收窄（证据 = 模块正文里的事件契约 `payload: {…}`）。

`protocol/event_registry.json` 里大量字段是 `untyped`（建表时以"正文证据字段名；类型待核"
起步）。本模块**从模块正文逐字收割**已声明的事件载荷，按可证规则收窄类型——
没有证据的字段**保持 untyped**（不猜）。

类型判定规则（全部来自文本字面形式）：

| 正文写法 | 判定 |
|---|---|
| `field: bool` / `int` / `str` / `number` / `list` / `object` | 对应类型 |
| `field: true|false` | boolean |
| `field: 3` / `field: <数字占位>` | number |
| `field[]` / `field: [..]` | array |
| `field{...}` / `field: {..}` | object |
| `field` / `field: <说明占位>` / `field?` | untyped（如实） |

冲突（正文类型与注册表已有具体类型不一致）**只报告不改**——避免收割规则覆盖人工结论。
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

EVENT_REGISTRY = "protocol/event_registry.json"
_FENCE = re.compile(r"```(?:yaml|yml)\n(.*?)```", re.S)
_TYPE_WORDS = {"bool": "boolean", "boolean": "boolean", "int": "integer",
               "integer": "integer", "str": "string", "string": "string",
               "float": "number", "number": "number", "list": "array",
               "array": "array", "object": "object", "dict": "object"}


def _split_top_level(body: str) -> List[str]:
    """按顶层逗号切分（跳过 {} / [] 内部）。"""
    out, depth, cur = [], 0, ""
    for ch in body:
        if ch in "{[":
            depth += 1
        elif ch in "}]":
            depth -= 1
        if ch == "," and depth == 0:
            out.append(cur)
            cur = ""
        else:
            cur += ch
    if cur.strip():
        out.append(cur)
    return out


def _field_type(token: str) -> Tuple[str, str]:
    """单个字段 token → (字段名, 类型)。"""
    token = token.strip().rstrip("?")
    if not token:
        return "", ""
    if "{" in token:                     # modifiers{combat, travel}
        return token.split("{", 1)[0].strip(), "object"
    if token.endswith("[]") or token.endswith("[ ]"):
        return token[:-2].strip(), "array"
    if ":" in token:
        name, val = token.split(":", 1)
        name, val = name.strip(), val.strip()
        if val.startswith("{") or val.endswith("}"):
            return name, "object"
        if val.startswith("["):
            return name, "array"
        low = val.lower()
        if low in _TYPE_WORDS:
            return name, _TYPE_WORDS[low]
        if low in ("true", "false"):
            return name, "boolean"
        if re.fullmatch(r"\d+(\.\d+)?", val):
            return name, "number"
        if val.startswith("<") or val.startswith("（"):
            if re.search(r"回合|tick|日|分钟|数|量", val):
                return name, "number"
            return name, "untyped"
        if "|" in val:                 # 枚举写法  full|delta  → 字符串
            return name, "string"
        if val and not val.startswith(("[", "{")):
            # 正文写了具体常量/标识符（如 origin: M94、style: 通用）→ 字符串证据
            return name, "string"
        return name, "untyped"
    return token, "untyped"


def harvest_doc(text: str) -> Dict[str, Dict[str, str]]:
    """单篇模块文档 → {事件名: {字段: 类型}}。"""
    out: Dict[str, Dict[str, str]] = {}
    for fence in _FENCE.findall(text):
        event, payload_raw = "", ""
        for line in fence.splitlines():
            m = re.match(r"\s*(?:event|name)\s*:\s*([a-z_][a-z0-9_]*)", line)
            if m:
                event = m.group(1)
            # 事件标记三写法（实测缺口：模块正文用 `produce:` 时旧规则认不出 →
            # 28 处 payload 行的类型证据全被漏收，见 AUD-0015）
            m2 = re.match(r"\s*(?:publish|produce)\s*:\s*\[?\s*([a-z_][a-z0-9_]*)", line)
            if m2 and not event:
                event = m2.group(1)
            m3 = re.match(r"\s*payload\s*:\s*\{(.*)\}\s*$", line)
            if m3:
                payload_raw = m3.group(1)
                if not event:
                    for back in fence.splitlines():
                        m4 = re.match(r"\s*([a-z_][a-z0-9_]{3,})\s*:", back)
                        if m4 and m4.group(1) not in ("payload", "description", "inputs",
                                                      "output", "type", "domain"):
                            continue
                if event:
                    fields = {}
                    for tok in _split_top_level(payload_raw):
                        name, kind = _field_type(tok)
                        if name:
                            fields[name] = kind
                    if fields:
                        out.setdefault(event, {}).update(fields)
    return out


def harvest(root: str = ".") -> Dict[str, Dict[str, str]]:
    """全仓收割（同一事件多来源时，具体类型优先于 untyped）。"""
    from core import conformance_scan as csc

    merged: Dict[str, Dict[str, str]] = {}
    for doc in csc._module_docs(root):
        found = harvest_doc(Path(doc).read_text(encoding="utf-8"))
        for ev, fields in found.items():
            bucket = merged.setdefault(ev, {})
            for f, k in fields.items():
                if bucket.get(f, "untyped") == "untyped":
                    bucket[f] = k
    return merged


def apply(root: str = ".", write: bool = False) -> Dict[str, Any]:
    """把收割结果并入 `event_registry.json` → 变更/冲突报告。"""
    reg_path = Path(root) / EVENT_REGISTRY
    data = json.loads(reg_path.read_text(encoding="utf-8"))
    events = data.setdefault("events", {})
    merged = harvest(root)
    added, narrowed, conflicts = [], [], []
    for ev, fields in sorted(merged.items()):
        body = events.setdefault(ev, {"payload_status": "declared",
                                      "note": "证据:模块正文事件契约 payload 收割",
                                      "fields": {}})
        fmap = body.setdefault("fields", {})
        for f, kind in sorted(fields.items()):
            cur = fmap.get(f)
            if cur is None:
                fmap[f] = {"type": kind, "note": "正文 payload 收割（证据可溯）"}
                added.append("%s.%s=%s" % (ev, f, kind))
            else:
                ctype = (cur or {}).get("type")
                if ctype == "untyped" and kind != "untyped":
                    cur["type"] = kind
                    cur["note"] = "45 类型收窄（正文 payload 收割，证据可溯）"
                    narrowed.append("%s.%s: untyped→%s" % (ev, f, kind))
                elif ctype != kind and kind != "untyped" and ctype != "untyped":
                    conflicts.append("%s.%s: 注册表=%s vs 正文=%s" % (ev, f, ctype, kind))
    if write:
        reg_path.write_text(json.dumps(data, ensure_ascii=False, indent=2,
                                       sort_keys=True) + "\n",
                            encoding="utf-8", newline="\n")
    return {"added": added, "narrowed": narrowed, "conflicts": conflicts}


def stats(root: str = ".") -> Dict[str, Any]:
    """类型面统计（供报告）。"""
    reg_path = Path(root) / EVENT_REGISTRY
    if not reg_path.is_file():
        return {}
    data = json.loads(reg_path.read_text(encoding="utf-8"))
    counts: Dict[str, int] = {}
    for body in (data.get("events") or {}).values():
        for spec in (body.get("fields") or {}).values():
            k = (spec or {}).get("type") or "untyped"
            counts[k] = counts.get(k, 0) + 1
    total = sum(counts.values())
    typed = total - counts.get("untyped", 0)
    return {"events": len(data.get("events") or {}), "fields": total,
            "typed": typed, "untyped": counts.get("untyped", 0),
            "coverage": round(100.0 * typed / total, 1) if total else 0.0}


def backlog(root: str = ".", write: bool = False) -> Dict[str, Any]:
    """类型积压台账：把**不可从证据推断**的 untyped 字段显式化（可数、不隐身）。

    纪律：每个 untyped 字段必须带 note（说明为何没有类型证据）——门禁据此判「无声增长」。
    """
    reg_path = Path(root) / EVENT_REGISTRY
    data = json.loads(reg_path.read_text(encoding="utf-8"))
    rows, missing_note = [], []
    for ev, body in sorted((data.get("events") or {}).items()):
        for f, spec in sorted((body.get("fields") or {}).items()):
            if (spec or {}).get("type") != "untyped":
                continue
            note = str((spec or {}).get("note") or "").strip()
            rows.append({"event": ev, "field": f, "note": note})
            if not note:
                missing_note.append("%s.%s" % (ev, f))
    doc = {"schema": "nf-type-backlog/1",
           "note": ("事件载荷中无法从正文证据推断类型的字段——待模块正文补充类型证据后收窄。"
                    "纪律：不得新增无 note 的 untyped。"),
           "count": len(rows), "missing_note": missing_note, "fields": rows}
    if write:
        p = Path(root) / "protocol" / "type_backlog.json"
        p.write_text(json.dumps(doc, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                     encoding="utf-8", newline="\n")
    return doc


def verify_backlog(root: str = ".") -> Tuple[List[str], Dict[str, Any]]:
    """台账一致性：在盘台账 == 实时重算，且无「无 note 的 untyped」。"""
    live = backlog(root)
    issues: List[str] = []
    if live["missing_note"]:
        issues.append("存在无 note 的 untyped 字段（无声增长）：%s"
                      % "、".join(live["missing_note"][:3]))
    p = Path(root) / "protocol" / "type_backlog.json"
    if not p.is_file():
        issues.append("缺类型积压台账 protocol/type_backlog.json"
                      "（修复指引：nf module types --backlog --write）")
    else:
        try:
            committed = json.loads(p.read_text(encoding="utf-8"))
            if committed.get("count") != live["count"]:
                issues.append("台账过期：记录 %s ≠ 实测 %s（修复指引：重写台账）"
                              % (committed.get("count"), live["count"]))
        except ValueError:
            issues.append("台账 JSON 不可解析")
    return issues, {"untyped": live["count"]}
