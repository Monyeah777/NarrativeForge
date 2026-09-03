"""管线加载器：解析 03_管线库/*.md 的 YAML frontmatter → Pipeline 对象。

仓库管线文件结构：
  # 管线 P01 · 标准管线
  > 摘要
  ```yaml
  Pipeline:
    id: P01
    name: ...
    structure: { type, flow: [{from,to},...] }
    layers:
      - id: P00
        name: ...
        description: ...
        optional: false
        default_modules: [M00, M20]
        allowed_modules: [...]
    dependencies: [{from,to,reason}]
    tags: [...]
  ```
  ## 运行规则 ...

解析策略：优先 import yaml；无 PyYAML 环境时回退内置轻量子集解析器
（仅支持该固定缩进结构，行内 list [a, b] 与 scalar 键值）。
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import List, Optional

from .models import Pipeline, PipelineLayer

YAML_FENCE_RE = re.compile(r"```ya?ml\s*\n(.*?)\n```", re.S)


# ---------------------------------------------------------------- yaml 子集
def _parse_scalar(s: str):
    s = s.strip()
    if not s:
        return ""
    if s.startswith("[") and s.endswith("]"):
        inner = s[1:-1].strip()
        if not inner:
            return []
        items = []
        for it in inner.split(","):
            it = it.strip().strip("'\"").strip()
            items.append(it)
        return items
    low = s.lower()
    if low in ("true", "yes", "on"):
        return True
    if low in ("false", "no", "off"):
        return False
    if low == "null" or low == "~":
        return None
    if (s.startswith('"') and s.endswith('"')) or \
       (s.startswith("'") and s.endswith("'")):
        return s[1:-1]
    # 数字
    try:
        if re.fullmatch(r"-?\d+", s):
            return int(s)
        if re.fullmatch(r"-?\d+\.\d+", s):
            return float(s)
    except ValueError:
        pass
    return s


def _kv(line: str):
    """拆分 'key: value'（值可能含冒号，用 partition）"""
    k, _, v = line.partition(":")
    return k.strip(), v.strip()


class _Node:
    """简单缩进树节点"""

    def __init__(self, indent: int, key: str, value=None,
                 is_list_item: bool = False, list_key: str = ""):
        self.indent = indent
        self.key = key
        self.value = value          # scalar 值（行内 list 已解析）
        self.is_list_item = is_list_item
        self.list_key = list_key    # 若属于某个 "- " 列表，记录列表键
        self.children: List["_Node"] = []


def _build_tree(lines: List[str]) -> List[_Node]:
    """按缩进建树（仅处理我们关心的子集）。"""
    roots: List[_Node] = []
    stack: List[_Node] = []
    for raw in lines:
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        content = raw.strip()
        is_item = content.startswith("- ")
        if is_item:
            content = content[2:].strip()
            # 列表项形如 "- id: P00"（键值）或 "- 纯文本"
            if ":" in content and not content.startswith(("http", "{")):
                key, val = _kv(content)
                node = _Node(indent, key, _parse_scalar(val), True)
            else:
                node = _Node(indent, "", _parse_scalar(content), True)
        else:
            if ":" not in content:
                continue
            key, val = _kv(content)
            node = _Node(indent, key, _parse_scalar(val), False)

        # 找父节点：缩进严格小于当前节点的最近祖先
        while stack and stack[-1].indent >= indent:
            stack.pop()
        if stack:
            stack[-1].children.append(node)
        else:
            roots.append(node)
        stack.append(node)
    return roots


def _tree_to_dict(root: _Node):
    """把单棵节点树转 dict/list。

    - 列表容器（children 为 "- " 项）→ list[dict]
    - 列表项节点（自带 key/value + 子 scalar）→ dict（自身键值并入）
    - 普通容器 → dict
    """
    items = [c for c in root.children if c.is_list_item]
    if items:
        return [_tree_to_dict(c) for c in items]
    d: dict = {}
    if root.is_list_item and root.key:
        d[root.key] = root.value
    for c in root.children:
        if c.is_list_item:
            continue
        if c.children:
            d[c.key] = _tree_to_dict(c)
        else:
            d[c.key] = c.value
    return d


def _parse_yaml_block(text: str) -> dict:
    """解析固定子集 YAML → dict（顶层根形如 {'Pipeline': {...}}）"""
    lines = [ln for ln in text.splitlines() if ln.strip()]
    if not lines:
        return {}
    roots = _build_tree(lines)
    result: dict = {}
    for r in roots:
        result[r.key] = _tree_to_dict(r) if r.children else r.value
    return result


# ---------------------------------------------------------------- 解析管线
def _norm_module_ref(ref: str) -> str:
    """模块引用归一：M00 / 通用:M10 → 保留原样；loader 侧不做类别补全。"""
    return ref.strip()


def parse_pipeline_md(text: str) -> Optional[Pipeline]:
    """从管线 md 全文解析 Pipeline。失败返回 None。"""
    m = YAML_FENCE_RE.search(text)
    if not m:
        return None
    try:
        import yaml  # type: ignore
        data = yaml.safe_load(m.group(1)) or {}
    except ImportError:
        data = _parse_yaml_block(m.group(1))
    pnode = data.get("Pipeline", data)
    if not isinstance(pnode, dict):
        return None

    pid = str(pnode.get("id", "")).strip() or "P00"
    p = Pipeline(
        id=pid,
        name=str(pnode.get("name", pid)).strip(),
        description=str(pnode.get("description", "")).strip(),
        structure_type="linear",
        tags=list(pnode.get("tags", []) or []),
    )
    # structure
    struct = pnode.get("structure") or {}
    if isinstance(struct, dict):
        p.structure_type = str(struct.get("type", "linear"))
    # dependencies
    for dep in pnode.get("dependencies", []) or []:
        if isinstance(dep, dict):
            p.dependencies.append({
                "from": dep.get("from", ""), "to": dep.get("to", ""),
                "reason": dep.get("reason", "")})
    # layers
    for ly in pnode.get("layers", []) or []:
        if not isinstance(ly, dict):
            continue
        p.layers.append(PipelineLayer(
            id=str(ly.get("id", "")).strip(),
            name=str(ly.get("name", "")).strip(),
            description=str(ly.get("description", "")).strip(),
            optional=bool(ly.get("optional", False)),
            default_modules=[_norm_module_ref(x) for x in (ly.get("default_modules") or [])],
            allowed_modules=[_norm_module_ref(x) for x in (ly.get("allowed_modules") or [])],
        ))
    return p


def load_pipeline_file(path: Path | str) -> Optional[Pipeline]:
    p = Path(path)
    if not p.exists():
        return None
    return parse_pipeline_md(p.read_text(encoding="utf-8"))


def discover_pipelines(directory: Path | str) -> List[Pipeline]:
    """扫描目录下所有管线 md，返回可解析的 Pipeline 列表。"""
    out = []
    d = Path(directory)
    if not d.exists():
        return out
    for f in sorted(d.glob("*.md")):
        try:
            pl = load_pipeline_file(f)
            if pl:
                out.append(pl)
        except Exception:
            continue
    return out