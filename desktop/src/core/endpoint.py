"""服务端点契约（机制借鉴 microsoft/ai-chat-protocol）。

NF 不产服务（公开面 = 协议 + core + CLI），所以本模块**不实现 HTTP**——它做两件诚实的事：

1. 把"若将来要把 NF 能力暴露成服务，面长什么样"固定成机器可读契约
   （`protocol/endpoint_contract.json`，`status: proposed`）；
2. **门禁**：每个端点的 `maps_to` 必须指向**当下真实存在**的 CLI 子命令或 MCP 工具
   ——契约不许指向空气（防"纸面能力"）。

判据：schema；status ∈ {proposed, implemented}；每个 endpoint 的 id/method/path 唯一；
`maps_to` 可解析（`nf <cmd>` 在 CLI 注册表内，或 MCP 工具名在 `TOOL_DEFS` 内）；
`streaming: true` 的端点必须声明 SSE 约定（conventions.streaming 在场）。
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

CONTRACT_REL = "protocol/endpoint_contract.json"
STATUSES = ("proposed", "implemented")
METHODS = ("GET", "POST", "PUT", "PATCH", "DELETE")
IDEMPOTENCY_MODES = ("idempotent", "non-idempotent")
IDEMPOTENCY_KEY = ("required", "none")
_MCP = re.compile(r"^([a-z_]+)（MCP 工具）$")
_CLI = re.compile(r"^nf\s+([a-z-]+)")


def load(root: str = ".") -> Dict[str, Any]:
    p = Path(root) / CONTRACT_REL
    return json.loads(p.read_text(encoding="utf-8")) if p.is_file() else {}


def _cli_commands(root: str = ".") -> set:
    nf = Path(root) / "scripts" / "nf.py"
    if not nf.is_file():
        return set()
    text = nf.read_text(encoding="utf-8")
    return set(re.findall(r'sub\.add_parser\(\s*"([a-z-]+)"', text))


def _check_ep_basics(ep: Dict[str, Any], eid: str, ids: set, paths: set,
                     issues: List[str]) -> None:
    """端点基础面：id 重复 / method 词表 / method+path 重复。"""
    if eid in ids:
        issues.append("端点 id 重复：%s" % eid)
    ids.add(eid)
    method, path = str(ep.get("method") or ""), str(ep.get("path") or "")
    if method not in METHODS:
        issues.append("%s 的 method 越词表：%s" % (eid, method))
    key = "%s %s" % (method, path)
    if key in paths:
        issues.append("端点 method+path 重复：%s" % key)
    paths.add(key)


def _check_ep_maps_to(ep: Dict[str, Any], eid: str, tools: set, cmds: set,
                      issues: List[str]) -> None:
    """端点映射面：maps_to 须解析为现存 MCP 工具或 CLI 子命令。"""
    maps = str(ep.get("maps_to") or "")
    m = _MCP.match(maps)
    if m:
        if m.group(1) not in tools:
            issues.append("%s 的 maps_to 指向不存在的 MCP 工具：%s" % (eid, m.group(1)))
        return
    c = _CLI.match(maps)
    if not c or c.group(1) not in cmds:
        issues.append("%s 的 maps_to 无法解析为现存 CLI 子命令或 MCP 工具：%s"
                      "（修复指引：改正，或先实现该能力）" % (eid, maps))


def _check_deprecated_marked(ep: Dict[str, Any], eid: str, status: str,
                             conv: Dict[str, Any], all_ids: List[str],
                             issues: List[str]) -> None:
    """已声明 deprecated 的端点：status 须 implemented、须有弃用约定 / sunset / replacement。"""
    if status != "implemented":
        issues.append("%s 声明 deprecated 但契约 status=%s——未实装的能力没有可弃用的东西"
                      "（修复指引：先落 implemented 再谈弃用）" % (eid, status))
    if not conv.get("deprecation"):
        issues.append("%s 声明 deprecated 但 conventions 未定义弃用约定" % eid)
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(ep.get("sunset") or "")):
        issues.append("%s 声明 deprecated 但缺合规 sunset（YYYY-MM-DD）：%r"
                      "（修复指引：按 RFC 8594 给出日落日期）" % (eid, ep.get("sunset")))
    if "replacement" not in ep:
        issues.append("%s 声明 deprecated 但缺 replacement（无替代写 null，不许省略）" % eid)
    else:
        rep = ep.get("replacement")
        if rep is not None and str(rep) not in all_ids:
            issues.append("%s 的 replacement 指向契约内不存在的端点：%r"
                          "（修复指引：改为契约内端点 id，或写 null 表示无替代）" % (eid, rep))


def _check_ep_deprecated(ep: Dict[str, Any], eid: str, status: str,
                         conv: Dict[str, Any], all_ids: List[str],
                         issues: List[str]) -> None:
    """弃用/日落语义（机制借鉴 OpenAPI deprecated + RFC 8594 Sunset）：有标志就必须有出口。"""
    dep = ep.get("deprecated")
    if dep is not None and not isinstance(dep, bool):
        issues.append("%s 的 deprecated 应为布尔：%r" % (eid, dep))
    if dep:
        _check_deprecated_marked(ep, eid, status, conv, all_ids, issues)
    elif any(k in ep for k in ("sunset", "replacement")):
        issues.append("%s 未声明 deprecated 却带 sunset/replacement（悬空弃用字段）" % eid)


def _check_idem_mode(xid: str, exc: Dict[str, Any], conv: Dict[str, Any],
                     issues: List[str]) -> None:
    """幂等例外 mode 词表；非幂等端点须给幂等键策略。"""
    mode = str(exc.get("mode") or "")
    if mode not in IDEMPOTENCY_MODES:
        issues.append("幂等例外 mode 越词表：%s = %r（允许 %s）"
                      % (xid, mode, "/".join(IDEMPOTENCY_MODES)))
    elif mode == "non-idempotent":
        key = str(exc.get("key") or "")
        if key not in IDEMPOTENCY_KEY:
            issues.append("非幂等端点 %s 缺幂等键策略（修复指引：key ∈ %s——required = "
                          "须幂等键去重；none = 明示不可重放并写 why）"
                          % (xid, "/".join(IDEMPOTENCY_KEY)))
        elif key == "required" and not conv.get("idempotency"):
            issues.append("幂等例外要求幂等键但 conventions 未定义幂等语义：%s" % xid)


def _check_idempotency_exceptions(exceptions: List[Any], ids: set,
                                  conv: Dict[str, Any], issues: List[str]) -> None:
    """幂等例外：须指向契约内端点、mode 在词表内、非幂等须给幂等键策略与 why。"""
    seen_exc = set()
    for exc in exceptions:
        xid = str(exc.get("id") or "")
        if xid not in ids:
            issues.append("幂等例外指向契约内不存在的端点：%r（修复指引：改为契约内端点 id，"
                          "或删除该例外）" % xid)
            continue
        if xid in seen_exc:
            issues.append("幂等例外重复登记端点：%s" % xid)
        seen_exc.add(xid)
        _check_idem_mode(xid, exc, conv, issues)
        if not str(exc.get("why") or "").strip():
            issues.append("幂等例外缺 why（修复指引：写明为何非幂等、重放会发生什么）")


def _scan_endpoints(doc: Dict[str, Any], status: str, conv: Dict[str, Any], tools: set,
                    cmds: set, issues: List[str]) -> set:
    """逐端点：基础面 + streaming 约定 + maps_to + 弃用语义 → 返回在册端点 id 集。"""
    all_ids = [str(e.get("id") or "") for e in (doc.get("endpoints") or [])]
    ids, paths = set(), set()
    for ep in doc.get("endpoints") or []:
        eid = str(ep.get("id") or "")
        _check_ep_basics(ep, eid, ids, paths, issues)
        if ep.get("streaming") and not conv.get("streaming"):
            issues.append("%s 声明 streaming 但 conventions 未定义 SSE 约定" % eid)
        _check_ep_maps_to(ep, eid, tools, cmds, issues)
        _check_ep_deprecated(ep, eid, status, conv, all_ids, issues)
    return ids


def _check_contract_header(doc: Dict[str, Any], issues: List[str],
                           warns: List[str]) -> str:
    """契约头：schema / status 词表 / proposed 提示 → 返回 status。"""
    if str(doc.get("schema") or "") != "nf-endpoint/1":
        issues.append("端点契约 schema 不匹配（期望 nf-endpoint/1）")
    status = str(doc.get("status") or "")
    if status not in STATUSES:
        issues.append("status 越词表：%s（%s）" % (status, "/".join(STATUSES)))
    if status == "proposed":
        warns.append("端点契约状态 = proposed（服务本体未实现，本契约只固定形状）")
    return status


def _load_ep_tools() -> set:
    """MCP 工具名集（导入失败即空集——门禁侧按「不认得」判）。"""
    try:
        from core.mcp_runtime import TOOL_DEFS
        return {t["name"] for t in TOOL_DEFS}
    except Exception:
        return set()


def _ep_stats(doc: Dict[str, Any], status: str, cmds: set, tools: set,
              exceptions: List[Any]) -> Dict[str, Any]:
    eps = doc.get("endpoints") or []
    return {"status": status, "endpoints": len(eps),
            "streaming": sum(1 for e in eps if e.get("streaming")),
            "cli_commands": len(cmds), "mcp_tools": len(tools),
            "idempotency_exceptions": len(exceptions)}


def scan(root: str = ".") -> Tuple[List[str], List[str], Dict[str, Any]]:
    """→ (issues, warns, stats)。"""
    issues: List[str] = []
    warns: List[str] = []
    doc = load(root)
    if not doc:
        return ["缺端点契约 %s（修复指引：见 protocol/endpoint_contract.json）"
                % CONTRACT_REL], warns, {}
    status = _check_contract_header(doc, issues, warns)
    conv = doc.get("conventions") or {}
    tools = _load_ep_tools()
    cmds = _cli_commands(root)
    ids = _scan_endpoints(doc, status, conv, tools, cmds, issues)
    # 幂等声明面（RFC 9110 §9.2.2）：默认幂等，例外须登记且非幂等端点须给幂等键策略
    if not conv.get("idempotency"):
        issues.append("conventions 未声明幂等语义（修复指引：按 RFC 9110 §9.2.2 写明默认幂等 + "
                      "例外登记规则——幂等性是重试安全的前提，不许沉默）")
    exceptions = doc.get("idempotency_exceptions") or []
    _check_idempotency_exceptions(exceptions, ids, conv, issues)
    return issues, warns, _ep_stats(doc, status, cmds, tools, exceptions)
