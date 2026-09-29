"""内容面指纹的**叶子件**（不 import 任何 core 模块）。

为什么单独成件（2026-09-29）：`disk_cache`（持久层）原先自己去算「代码面指纹」——于是
`disk_cache → conformance_scan`（借 `face_fingerprint` / `_payload_digest`）与
`disk_cache → import_graph`（借 `listing`）两条**反向依赖**，与
`conformance_scan → disk_cache`、`import_graph → disk_cache` 一起构成两个模块级环
（零环是硬判据）。指纹本是**纯内容函数**：把「帧 + payload 口径 + 枚举」收进叶子后，
持久层与校验层各自单向依赖它。

口径与 `conformance_scan` **逐位一致**（由 `desktop/tests/test_content_face.py` 钉住）：
- 帧：逐件 `相对路径 \\x00 摘要 \\x01` 顺序拼接后 sha256；
- payload：原始字节（含 CR 时按 UTF-8 通用换行翻译后重编码；解码失败退回字节）。
"""
from __future__ import annotations

import hashlib
import io
import os
from pathlib import Path
from typing import Dict, Iterable, List, Set


def hash_face(rels: Iterable[str], digests: Dict[str, bytes]) -> str:
    """面指纹：逐件「相对路径 + \\x00 + 摘要 + \\x01」流式哈希（与 `content_fingerprint` 同帧）。"""
    h = hashlib.sha256()
    for rel in rels:
        h.update(str(rel).encode("utf-8") + b"\x00" + digests[rel] + b"\x01")
    return h.hexdigest()


def payload_digest(root: str, rel: str) -> bytes:
    """单件 payload 摘要（raw digest）——与 `conformance_scan._payload_digest` 值口径同式。"""
    path = os.path.join(str(root), *str(rel).split("/"))
    with open(path, "rb") as fh:
        raw = fh.read()
    if b"\r" in raw:
        try:
            with io.TextIOWrapper(io.BytesIO(raw), encoding="utf-8", newline=None) as wrapper:
                raw = wrapper.read().encode("utf-8")
        except UnicodeDecodeError:
            pass                    # 非 UTF-8（图片等）按字节取指纹
    return hashlib.sha256(raw).digest()


def rels_for(root: str, patterns) -> List[str]:
    """按模式枚举文件（`**` 跨目录；含点文件）→ 相对 posix 路径列表。

    与 `conformance_scan.face_digests` **同构**：逐模式追加（各自排序、**不跨模式去重**）——
    重叠模式集因此也逐位一致（有判据 `test_content_face` 钉住）。
    """
    base = Path(str(root))
    out: List[str] = []
    for pat in patterns:
        out.extend(sorted(p.relative_to(base).as_posix()
                          for p in base.glob(str(pat)) if p.is_file()))
    return out


def code_face_digest(root: str, patterns) -> str:
    """面指纹 = 枚举 + 逐件 payload 摘要 + 帧。"""
    rels = rels_for(root, patterns)
    return hash_face(rels, {rel: payload_digest(root, rel) for rel in rels})


def list_core_files(root: str) -> Set[str]:
    """`desktop/src/core/*.py` 的**在场文件名**集合（闭包指纹「缺件不计入」用）。"""
    d = Path(str(root)) / "desktop" / "src" / "core"
    return {p.name for p in d.glob("*.py")} if d.is_dir() else set()
