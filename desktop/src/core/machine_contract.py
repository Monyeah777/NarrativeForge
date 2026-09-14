"""L0 → L1 机读契约 retro-fit（01 §1.1：机读块是人读引用块/正文的**结构化投影**）。

社区域包里有 21 件模块仍是 L0（无机读块）：check16 契约仲裁、check26 语义矛盾、
`io_types` 类型面都读不到它们。本模块把这批模块升到 L1/L2——**只做投影，不编造**：

| machine_contract 字段 | 来源（人读头逐字解析） |
|---|---|
| `id` / `name` | 标题行 `# 模块 Mxx · 名称`（与文件名交叉校验） |
| `category` | `类别：X`（去「类」后取短名，与官方件同形） |
| `layer` | `挂载点：Pxx …` |
| `inputs` | `依赖：…` 段内出现的 `Mxx` / `类别:Mxx` 令牌（去括号注记） |
| `events.publish` / `subscribe` | `发布：…` / `订阅：…` 段内的标识符（无反引号亦可） |
| `outputs` / `interfaces` | 人读头未声明 → 按 01 §1.1 写 `[]`（**不猜**） |
| `conformance` | **按可证事实判定**：在册（registry protocols module_ids）且被管线引用 → `L2`；否则 `L1` |

纪律：只读取既有文本做映射；任何解析不到的字段写空/不写，并在报告里列出缺口。
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

_ID_TOKEN = re.compile(r"(?:[^\s、,，:：]{1,8}:)?M\d{2}")
_EVENT_TOKEN = re.compile(r"`([A-Za-z_][A-Za-z0-9_]*)`|(?<![\w`])([a-z][a-z0-9_]{3,})(?![\w`])")
_SEG_SPLIT = re.compile(r"[｜|]")


def _header_lines(text: str) -> List[str]:
    out = []
    for ln in text.splitlines():
        s = ln.strip()
        if s.startswith(">"):
            out.append(s.lstrip("> ").strip())
        elif s.startswith("# ") or s == "":
            if out:
                break
        elif out:
            break
    return out


_FENCE = re.compile(r"```(?:yaml|yml)\n(.*?)```", re.S)


def _body_events(text: str) -> Dict[str, List[str]]:
    """正文事件契约（01 §1.1：机读块须覆盖正文全集，不能只看引用块）。

    只取 ```yaml 围栏内的 `publish:` / `subscribe:` 键（行内列表或块列表），
    并剥掉 `#` 注释——避免把伪代码里的同名键误当事件。
    """
    pub: set = set()
    sub: set = set()
    for body in _FENCE.findall(text):
        lines = [ln.split("#", 1)[0].rstrip() for ln in body.splitlines()]
        cur = None
        for ln in lines:
            m = re.match(r"\s*(publish|subscribe)\s*:\s*(.*)$", ln)
            if m:
                cur = "publish" if m.group(1) == "publish" else "subscribe"
                rest = m.group(2).strip()
                if rest.startswith("[") and rest.endswith("]"):
                    for item in rest[1:-1].split(","):
                        item = item.strip().strip("'\"")
                        if item:
                            (pub if cur == "publish" else sub).add(item)
                    cur = None
                continue
            if cur is None:
                continue
            mm = re.match(r"\s*-\s*([A-Za-z_][A-Za-z0-9_]*)\s*$", ln)
            if mm:
                (pub if cur == "publish" else sub).add(mm.group(1))
            elif ln.strip():
                cur = None
    return {"publish": sorted(pub), "subscribe": sorted(sub)}


def _segments(text: str) -> Dict[str, str]:
    """把引用块按 ｜ 切段 → {键: 值}（键 = 段首「xx：」）。"""
    got: Dict[str, str] = {}
    for line in _header_lines(text):
        for seg in _SEG_SPLIT.split(line):
            seg = seg.strip()
            if not seg or "：" not in seg and ":" not in seg:
                continue
            key, val = re.split(r"[:：]", seg, maxsplit=1)
            key = key.strip()
            if key in ("类别", "来源", "挂载点", "依赖", "发布", "订阅", "被依赖"):
                got.setdefault(key, val.strip())
            elif key.startswith("依赖"):
                got.setdefault("依赖", seg.split("：", 1)[-1].strip())
    return got


def parse_header(text: str, rel: str) -> Dict[str, Any]:
    """人读头 → 契约字段（解析不到的留空，由调用方决定写什么）。"""
    segs = _segments(text)
    title = next((ln.strip() for ln in text.splitlines() if ln.startswith("# 模块")), "")
    m = re.match(r"#\s*模块\s*(M\d{2})\s*[·:：]?\s*(.*)$", title)
    mid = m.group(1) if m else (os.path.basename(rel).split("_", 1)[0])
    name = (m.group(2).strip() if m else "") or Path(rel).stem.split("_", 1)[-1]
    cat = re.split(r"[:：]", segs.get("类别", ""), maxsplit=1)[-1].strip()
    cat = cat.replace("类", "") if cat.endswith("类") else cat
    layer_m = re.search(r"P\d{2}", segs.get("挂载点", ""))
    deps = _ID_TOKEN.findall(segs.get("依赖", "").replace("（", "、").replace("(", "、"))
    deps = [d for d in deps if not d.endswith(mid)] or deps
    def _events(key: str) -> List[str]:
        val = segs.get(key, "")
        val = val.split("——")[0]
        hits = [a or b for a, b in _EVENT_TOKEN.findall(val)]
        bad = {"无", "none"}
        return sorted({h for h in hits if h and h not in bad and not h.startswith("M")})
    return {"id": mid, "name": name, "category": cat or "通用",
            "layer": layer_m.group(0) if layer_m else "",
            "inputs": sorted(set(deps)),
            "publish": sorted(set(_events("发布")) | set(_body_events(text)["publish"])),
            "subscribe": sorted(set(_events("订阅")) | set(_body_events(text)["subscribe"])),
            "had_deps": "依赖" in segs, "had_publish": "发布" in segs}


def _provable_level(root: str, mid: str, package_dir: str) -> str:
    """L2 = 在册 + 被管线引用（01 §1.2）；否则 L1。"""
    reg = Path(root) / "desktop" / "src" / "core" / "registry.json"
    registered = False
    try:
        data = json.loads(reg.read_text(encoding="utf-8"))
        for p in data.get("protocols") or []:
            if mid in (p.get("module_ids") or []):
                registered = True
                break
    except (OSError, ValueError):
        pass
    referenced = False
    for pat in ("03_管线库/*.md", "community/*/pipelines/*.md"):
        for p in sorted(Path(root).glob(pat)):
            if package_dir and package_dir not in p.as_posix():
                continue
            if re.search(r"\b%s\b" % re.escape(mid), p.read_text(encoding="utf-8")):
                referenced = True
                break
        if referenced:
            break
    return "L2" if (registered and referenced) else "L1"


def render_block(spec: Dict[str, Any], level: str) -> str:
    def arr(xs: List[str]) -> str:
        return "[%s]" % ", ".join(xs)
    lines = ["```yaml", "machine_contract:",
             '  conformance: "%s"' % level, '  schema: "1"',
             "  id: %s" % spec["id"], "  name: %s" % spec["name"],
             "  category: %s" % spec["category"], "  layer: %s" % (spec["layer"] or "P00"),
             "  inputs: %s" % arr(spec["inputs"]),
             "  outputs: []",
             "  events:",
             "    publish: %s" % arr(spec["publish"]),
             "    subscribe: %s" % arr(spec["subscribe"]),
             "  interfaces: []", "```"]
    return "\n".join(lines)


def _insert_point(text: str) -> Optional[int]:
    """插点 = 引用块之后、首个 `## ` 标题之前（01 §1.1 规定位置）。"""
    lines = text.splitlines()
    last_gt = -1
    for i, ln in enumerate(lines):
        if ln.strip().startswith(">"):
            last_gt = i
    for i, ln in enumerate(lines):
        if ln.startswith("## ") and i > last_gt:
            return i
    if last_gt >= 0:
        return last_gt + 1        # 兜底：引用块之后（无 `## ` 章节头的模块）
    return 0


def inject_contract(text: str, spec: Dict[str, Any], level: str) -> str:
    at = _insert_point(text)
    if at is None:
        raise ValueError("找不到插入点（缺 `## ` 章节头）")
    lines = text.splitlines()
    block = render_block(spec, level).splitlines()
    lines[at:at] = block + [""]
    return "\n".join(lines) + ("\n" if text.endswith("\n") else "")


def apply(root: str = ".", write: bool = False) -> List[Dict[str, Any]]:
    """给全部 L0 模块补机读块（幂等：已有机读块则跳过）→ 变更清单。"""
    from core import conformance_scan as csc

    out = []
    for doc in csc._module_docs(root):
        rel = Path(doc).relative_to(root).as_posix()
        text = Path(doc).read_text(encoding="utf-8")
        parsed = csc._fence_yaml(text, "machine_contract")
        mc = parsed.get("machine_contract") if isinstance(parsed, dict) else None
        if isinstance(mc, dict) and mc.get("id"):
            continue
        spec = parse_header(text, rel)
        pkg = rel.split("/")[1] if rel.startswith("community/") else ""
        level = _provable_level(root, spec["id"], pkg)
        new = inject_contract(text, spec, level)
        if write:
            Path(doc).write_text(new, encoding="utf-8", newline="\n")
        out.append({"path": rel, "id": spec["id"], "level": level,
                    "missing": [k for k in ("layer", "inputs") if not spec.get(k)],
                    "events": {"publish": spec["publish"], "subscribe": spec["subscribe"]}})
    return out


def derive_outputs(mc: Dict[str, Any], event_fields: Dict[str, Dict[str, str]]
                   ) -> List[str]:
    """outputs 的证据来源 = 本模块**已发布事件**在 `event_registry.json` 里登记的载荷字段
    （01 §1.1 明列「事件载荷」为 outputs 合法来源）。无证据返回 []（不猜）。
    """
    toks: List[str] = []
    for ev in ((mc.get("events") or {}).get("publish") or []):
        for field in (event_fields.get(str(ev)) or {}):
            if field not in toks:
                toks.append(field)
    return toks


def _replace_outputs_line(text: str, tokens: List[str]) -> str:
    """替换 machine_contract 围栏内的 `outputs: [...]` 行（只动第一处、幂等）。"""
    lines = text.splitlines()
    start = next((i for i, ln in enumerate(lines) if ln.strip() == "machine_contract:"), None)
    if start is None:
        return text
    for i in range(start + 1, len(lines)):
        ln = lines[i]
        if ln.strip().startswith("```"):
            break
        m = re.match(r"^(\s*)outputs\s*:\s*\[.*\]\s*$", ln)
        if m:
            lines[i] = "%soutputs: [%s]" % (m.group(1), ", ".join(tokens))
            return "\n".join(lines) + ("\n" if text.endswith("\n") else "")
    return text


def apply_outputs(root: str = ".", write: bool = False) -> List[Dict[str, Any]]:
    """给 **outputs 为空且有事件证据**的模块补 outputs 声明（幂等）。"""
    from core import conformance_scan as csc

    ev_fields: Dict[str, Dict[str, str]] = {}
    reg = Path(root) / "protocol" / "event_registry.json"
    if reg.is_file():
        try:
            data = json.loads(reg.read_text(encoding="utf-8"))
            for ev, body in (data.get("events") or {}).items():
                ev_fields[ev] = {k: (v.get("type") if isinstance(v, dict) else "untyped")
                                 for k, v in (body.get("fields") or {}).items()}
        except ValueError:
            pass
    out = []
    for doc in csc._module_docs(root):
        rel = Path(doc).relative_to(root).as_posix()
        text = Path(doc).read_text(encoding="utf-8")
        parsed = csc._fence_yaml(text, "machine_contract")
        mc = parsed.get("machine_contract") if isinstance(parsed, dict) else None
        if not isinstance(mc, dict) or not mc.get("id"):
            continue
        if [str(x) for x in (mc.get("outputs") or [])]:
            continue                       # 已显式声明 → 不动
        toks = derive_outputs(mc, ev_fields)
        if not toks:
            out.append({"path": rel, "id": str(mc["id"]), "tokens": [],
                        "changed": False, "reason": "无事件载荷证据（如实留空）"})
            continue
        new = _replace_outputs_line(text, toks)
        changed = new != text
        if changed and write:
            Path(doc).write_text(new, encoding="utf-8", newline="\n")
        out.append({"path": rel, "id": str(mc["id"]), "tokens": toks,
                    "changed": changed, "reason": "事件载荷证据"})
    return out


def scan(root: str = ".") -> Tuple[List[str], List[str], Dict[str, Any]]:
    """→ (issues, warns, stats)：L0 残留 = WARN；机读块与标题/文件名不符 = FAIL。"""
    from core import conformance_scan as csc

    issues: List[str] = []
    warns: List[str] = []
    l0 = []
    for doc in csc._module_docs(root):
        rel = Path(doc).relative_to(root).as_posix()
        text = Path(doc).read_text(encoding="utf-8")
        parsed = csc._fence_yaml(text, "machine_contract")
        mc = parsed.get("machine_contract") if isinstance(parsed, dict) else None
        if not isinstance(mc, dict) or not mc.get("id"):
            l0.append(rel)
            continue
        spec = parse_header(text, rel)
        # 官方限定写法（事件:M22 / 通用:M10）与裸号同义——按裸号比对，避免误报
        if str(mc.get("id")).split(":")[-1] != spec["id"].split(":")[-1]:
            issues.append("机读块 id 与标题/文件名不符：%s（%s vs %s）"
                          % (rel, mc.get("id"), spec["id"]))
    if l0:
        warns.append("仍为 L0（无机读块）：%d 件（修复指引：nf module contract --write）" % len(l0))
    stats = {"l0": len(l0), "checked": len(l0) and 0 or 0}
    stats["l0_list"] = l0
    return issues, warns, stats
