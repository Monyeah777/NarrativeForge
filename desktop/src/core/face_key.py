#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**两段式面键**：内容面指纹 ‖ 成员面路径流（2026-09-29 实测得出）。

动机（实测）：`layer_model` 的申报输入面是四阶**真源面**（2640 件），但规则只对它做「存在且非空」
一类**枚举级**判断——内容一件都不读（真读面 130 件：`desktop/src/core/*.py` + 声明件 + 判据脚本 +
渲染投影）。旧口径把这些件逐件读进来取摘要，`layer scan` 的取键实测 **425 ms**；拆成「内容指纹
（130 件）+ 成员集指纹（2640 条路径）」后 ~25 ms，而语义不变：

- **加/删**一件 ⇒ 成员集变 ⇒ 换键（「存在且非空」这类判据不会陈旧）；
- **改**一件规则**不读**的件的内容 ⇒ 不必重算（那件的内容本来就不进结论）；
- 改一件规则**真读**的件 ⇒ 内容指纹变 ⇒ 必重算。

纪律：`content_patterns` 必须**覆盖真读面**（判据：`test_conformance_scan.LogicalReadFaceAuditTest`
逐站点量「读盘面 ⊆ 申报输入面」）；`member_patterns` 必须覆盖**做枚举级判断的那些面**。两段缺一段
就是假绿——所以这里把「两段都要」写进函数签名，而不是留给调用方记性。
"""
from __future__ import annotations

import hashlib

from core import conformance_scan as csc


def fingerprint(root: str, content_patterns, member_patterns) -> str:
    """`sha256(内容面指纹 ‖ 成员面路径流)`：内容与成员**分别进键**（理由见模块 docstring）。"""
    h = hashlib.sha256(csc.face_fingerprint(root, content_patterns).encode("utf-8"))
    for pat in member_patterns:
        for rel in csc.iter_files(root, pat):
            h.update(b"\x01")
            h.update(rel.encode("utf-8"))
    return h.hexdigest()
