"""v2.8.0 波C D4：可观测性 —— logging 级别体系（41 规划 D 组杂务）。

规则：
- 库/服务诊断走 logging（默认 INFO，级别可调），handler 绑定 **stderr**——
  绝不污染 stdout（MCP stdio 协议面只写 JSON-RPC；CLI 用户面输出保持）。
- 库层不自造 print 诊断；既有 CLI 用户面 print（结果/产物路径）为输出协议，保留。

用法：from core import plog; log = plog.get_logger(__name__)
"""
from __future__ import annotations

import logging
import sys

_CONFIGURED = False


def get_logger(name: str, level: int = logging.INFO) -> "logging.Logger":
    """取模块 logger；首次调用自动初始化 stderr handler（幂等）。"""
    global _CONFIGURED
    if not _CONFIGURED:
        logging.basicConfig(
            level=level,
            format="%(levelname)s %(name)s: %(message)s",
            stream=sys.stderr,
        )
        _CONFIGURED = True
    return logging.getLogger(name)
