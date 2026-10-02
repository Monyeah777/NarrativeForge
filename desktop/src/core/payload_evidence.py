"""45 A1 · 事件载荷正文证据扫描器（保守：只收同发布行内联载荷）。

自动抽取易混入无关载荷（上轮实证）；故本模块只产出「候选证据」，
不自动写注册表。规则：
- 文档内出现 `publish: <event>` 行，且该行（或紧邻 3 行内）带 `payload:{...}`，
  括号内逗号分隔的 snake_case 标识符视为候选字段；
- 返回 {event: [{source, fields}]}，供作者/维护者人工核验后按
  protocol/event_registry.json 登记为 declared。
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List

_ROOT = Path(__file__).resolve().parents[3]
_FIELD = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
_BRACE = re.compile(r"payload\s*[:：]\s*\{([^}]{2,200})\}")


def _module_docs(root: str = ".") -> List[Path]:
    """模块文档清单——**按传入的根**枚举。

    此前写死模块级 `_ROOT` 且 `scan(root)` 不传它：传别的根时，枚举到的是**真仓**的文件，
    紧接着 `p.relative_to(新根)` 直接抛 `ValueError: … is not in the subpath of …`
    （2026-10-01 空根普查抓到：`root` 参数等于**谎报**，且是空根下唯一抛 ValueError 的入口）。
    """
    r = Path(root)
    out = []
    for sub in ("04_模块库",):
        out += sorted((r / sub).rglob("*.md"))
    for pkg in sorted((r / "community").iterdir()) if (r / "community").is_dir() else []:
        mdir = pkg / "modules"
        if mdir.is_dir():
            out += sorted(mdir.glob("*.md"))
    return out


def scan(root: str = ".") -> Dict[str, Any]:
    r = Path(root)
    candidates: Dict[str, List[Dict[str, Any]]] = {}
    for p in _module_docs(root):
        try:
            lines = p.read_text(encoding="utf-8").splitlines()
        except OSError:  # 尽力而为：跳过不可读/不可解析项；该类缺口由对应门禁另行报出（见 AUD-0016）
            continue
        rel = p.relative_to(r).as_posix()
        for i, ln in enumerate(lines):
            if not re.search(r"publish\s*[:：]", ln):
                continue
            window = "\n".join(lines[i:i + 4])
            m = _BRACE.search(window)
            if not m:
                continue
            for ev in _FIELD.findall(ln.split("publish", 1)[1])[:3]:
                fields = [f for f in _FIELD.findall(m.group(1))
                          if f not in ("payload",)]
                if fields and ev not in ("publish",):
                    candidates.setdefault(ev, []).append(
                        {"source": rel, "fields": fields[:12]})
    for ev in candidates:
        candidates[ev] = candidates[ev][:4]
    return candidates


def main() -> int:
    import json

    print(json.dumps(scan(str(_ROOT)), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
