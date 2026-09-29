"""馆藏条目读取（**叶子件**：不 import 任何 core 模块）。

为什么单独成件（2026-09-29）：`receipts.build` 需要 `entries`/`entry_digest`，而
`library.set_attestation` 又要刷 `receipts` —— 与 `receipts → library` 构成双向对，零环
硬判据不达标。条目读取（frontmatter 解析 + 摘要）本就是纯数据面，迁到叶子后：
`library` 兼容转发（既有调用点零改动）、`receipts` 只依赖叶子，各自单向。
"""
from __future__ import annotations

import hashlib
import os
import re
from pathlib import Path
from typing import Any, Dict, List


ENTRY_GLOB = "library/NF-*.md"

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
    """读单条条目 → {path, id, fm, body, decode_issue}（id 以文件名为准）。

    编码纪律（极端渗透 D4 实证）：馆藏是**外来内容**，一个非 UTF-8 文件此前会让
    `entries()` 抛裸 `UnicodeDecodeError`，连带 INDEX/ALIAS 投影、`nf library verify`、
    MCP `resources/read` 整面瘫痪。现改为**降级读取 + 如实登记**：不静默丢条目，
    也不让单个坏文件拖垮整面；问题经 `decode_issue` 上报（`verify` 判 FAIL 并给修复指引）。
    """
    raw = Path(path).read_bytes()
    decode_issue = ""
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        text = raw.decode("utf-8", "replace")
        decode_issue = ("%s 非合法 UTF-8（%s）；已按替换字符降级读取"
                        "（修复指引：把该文件另存为 UTF-8 后重跑 nf library verify）"
                        % (Path(path).name, exc))
    fm, body = parse_frontmatter(text)
    return {"path": Path(path).as_posix(), "id": Path(path).stem,
            "fm": fm, "body": body, "text": text, "decode_issue": decode_issue}


def entries(root: str = ".") -> List[Dict[str, Any]]:
    """全量条目（按编号排序；path 一律归一为仓库相对路径）。"""
    r = Path(root)
    out = [read_entry(str(p)) for p in sorted(r.glob(ENTRY_GLOB))]
    for e in out:
        e["path"] = os.path.relpath(e["path"], str(r)).replace("\\", "/")
    out.sort(key=lambda e: e["id"])
    return out


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
