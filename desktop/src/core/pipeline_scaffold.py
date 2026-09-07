"""v2.8.0 波B S4：管线脚手架（`nf pipeline new` 库实现）。

从 03_管线库/P00_通用文档生成管线.md 骨架派生新管线文档——按 01 §2 / 06 §10
「复制 P00 派生，改 id/name/层名/挂载/flow/tags」的最小脚手架。
只做派生文本；登记 02 / 填层名挂载由作者按 README「新领域接入三步」补齐（I5 引擎不改）。
"""
from __future__ import annotations

import re

DEFAULT_TEMPLATE = "03_管线库/P00_通用文档生成管线.md"


def normalize_pipeline_id(raw: str) -> str:
    pid = (raw or "").strip().upper()
    if not re.fullmatch(r"P\d{2,4}", pid):
        raise ValueError("管线 id 应为 P 开头两位以上数字（如 P07/P90）")
    return pid


def default_filename(pid: str, name: str) -> str:
    safe = re.sub(r"[^\w\u4e00-\u9fff]+", "_", name.strip()).strip("_")
    return "%s_%s.md" % (pid, safe or "派生管线")


def scaffold_pipeline(template_text: str, pipeline_id: str, name: str,
                      domain: str = "", note: str = "") -> str:
    """把模板管线文本派生为新管线文本。

    替换：标题行 / 顶层 yaml id / name / tags（追加领域标签）——层位 id P00-P80
    与层名保持不变，交作者按领域装配。校验失败抛 ValueError（不静默产坏档）。
    """
    pid = normalize_pipeline_id(pipeline_id)
    name = (name or "").strip()
    if not name:
        raise ValueError("name 必填（管线显示名）")

    # 1) 标题行：# 管线 P00 · 通用文档生成管线
    new, n = re.subn(r"(?m)^#\s*管线\s+P\d+\s*[·.、\-]?\s*.*$",
                     "# 管线 %s · %s" % (pid, name), template_text, count=1)
    if n != 1:
        raise ValueError("模板缺少管线标题行（期望 `# 管线 Pxx · 名称`）")

    # 2) yaml 顶层 id/name/tags（层位 id 行带 `- id:` 前缀，不受影响）
    tags_extra = []
    d = (domain or "").strip().rstrip("包").rstrip("领域")
    if d:
        tags_extra.append("%s领域" % d)
    lines = new.split("\n")
    out, in_block = [], False
    replaced_id = replaced_name = replaced_tags = False
    for ln in lines:
        if ln.strip().startswith("```") and not in_block:
            in_block = True
            out.append(ln)
            continue
        if in_block and ln.strip().startswith("```"):
            in_block = False
            out.append(ln)
            continue
        if in_block:
            if re.fullmatch(r"  id: P\d{2,4}\s*", ln) and not replaced_id:
                out.append("  id: %s" % pid)
                replaced_id = True
                continue
            if ln.startswith("  name: ") and not replaced_name:
                out.append("  name: %s" % name)
                replaced_name = True
                continue
            if ln.strip().startswith("tags: ") and not replaced_tags:
                inner = ln.split(":", 1)[1].strip()
                items = [x.strip().strip("[]") for x in inner.split(",") if x.strip()]
                for t in tags_extra:
                    if t not in items:
                        items.append(t)
                out.append("  tags: [%s]" % ", ".join(items))
                replaced_tags = True
                continue
        out.append(ln)
    if not (replaced_id and replaced_name and replaced_tags):
        raise ValueError("模板 yaml 块缺少顶层 id / name / tags 键（模板结构变更？）")
    text = "\n".join(out)

    # 3) 派生来源注记（标题下插一行）
    src = note or "由 `nf pipeline new` 自 P00 通用骨架派生"
    if domain:
        src = "由 `nf pipeline new --from P00 --domain %s` 派生" % domain.strip()
    header = "# 管线 %s · %s" % (pid, name)
    idx = text.index(header) + len(header)
    text = text[:idx] + "\n> %s（v2.8.0 波B S4 脚手架：按 01 §2 填层名/挂载 → 02 登记即调度，I5）" % src + text[idx:]
    return text