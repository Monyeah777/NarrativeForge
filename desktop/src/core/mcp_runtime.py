"""MCP Server 运行时（v2.5.0 Wave5 C1：快照烧成服务——静态 mcp.json → stdio JSON-RPC）。

33_v2.2.0_A5-MCP规范差距核查报告 三差距勾销（对照 2025-11-25 schema.ts 实证）：
- G1 形态级：mcp.json 静态定义文件 → 运行时 JSON-RPC 会话协议（stdio transport，
  换行分隔 UTF-8 消息——transport 页实证）；mcp.json 快照降为数据源。
- G2 字段级：resources/list 返回去 text 的 Resource 纯元数据（schema.ts L802 Resource
  无 text）；正文经 resources/read 按 uri 返回 contents[].text（L895 TextResourceContents）。
- G4 归属层：name/version 从快照顶层迁入 initialize 握手 serverInfo（L550 Implementation）——
  快照文件仅作数据源，运行时自述经握手。

C2 最小安全层（Wave5 随 C1）：
- 只读：本运行时只实现只读面（resources list/read + 41 波C C7 只读 tools/prompts），
  写路径工具一律不实现（-32601 METHOD_NOT_FOUND / 未知工具 -32602 天然被拒）。
- uri 白名单：resources/read 只接受快照内已登记 uri，未知 uri → -32602 INVALID_PARAMS
  （schema.ts 无 resource-not-found 专用码，参数级拒绝为最小面裁决，不泄露目录结构）。

C7 只读工具面（41_v2.8.0_波C质量编译深化规划，2026-09-08）：
- tools（检索类结构化工具，inputSchema 真实存在）：library_search（仓库侧知识库检索）/
  registry_query（registry 模块+协议查询）/ pipeline_ls（管线清单）/ spec_ls（协议包清单）。
- prompts：assemble_guide 装载引导模板（1 条）。
- 数据源 = 本仓库只读扫描（03_管线库/04_模块库/community/*/docs/registry.json），
  不改 C2 只读安全层（全部只读，无 tools 写路径）。

协议事实（schema.ts 2025-11-25 权威）：
- LATEST_PROTOCOL_VERSION = "2025-11-25"；JSONRPC_VERSION = "2.0"
- initialize 响应：{protocolVersion, capabilities, serverInfo: Implementation}
- notifications/initialized 是通知（无 id）→ 不应答
- ping → EmptyResult（{}）
- 标准错误码：PARSE_ERROR=-32700 / INVALID_REQUEST=-32600 / METHOD_NOT_FOUND=-32601 /
  INVALID_PARAMS=-32602 / INTERNAL_ERROR=-32603

用法：
    snap = load_snapshot("mcp.json")     # 快照 → 运行时数据源
    srv = McpRuntime(snap)
    srv.serve_stdio(sys.stdin, sys.stdout)   # 换行分隔 JSON-RPC 循环
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, TextIO

#: 协议版本常量（schema.ts L12 实证）
PROTOCOL_VERSION = "2025-11-25"
JSONRPC_VERSION = "2.0"

#: JSON-RPC 标准错误码（schema.ts L173-177 实证）
PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
INTERNAL_ERROR = -32603


def _err(code: int, message: str) -> dict:
    return {"jsonrpc": JSONRPC_VERSION, "id": None, "error": {"code": code,
                                                              "message": message}}


def _repo_root() -> "Path":
    """仓库根 = desktop/src/core 向上三级（mcp_runtime 常驻仓库内）。"""
    return Path(__file__).resolve().parents[3]


def _read_json_rel(rel: str) -> dict:
    return json.loads((_repo_root() / rel).read_text(encoding="utf-8"))


def _md_title(text: str) -> str:
    for ln in text.splitlines():
        if ln.startswith("#"):
            return ln.lstrip("# ").strip()
    return ""


TOOL_DEFS = [
    {
        "name": "pipeline_ls",
        "description": "列出 NF 管线清单（03_管线库 + community 包 pipelines）。",
        "inputSchema": {
            "type": "object",
            "properties": {"query": {"type": "string", "description": "可选过滤串（匹配 id/标题）"}},
        },
    },
    {
        "name": "spec_ls",
        "description": "列出 registry protocols 协议包清单（id/version/模块数/类别）。",
        "inputSchema": {
            "type": "object",
            "properties": {"tier": {"type": "string", "description": "可选按分级过滤"}},
        },
    },
    {
        "name": "registry_query",
        "description": "查询 registry 模块/协议（按 id/name/包 id 子串匹配，只读）。",
        "inputSchema": {
            "type": "object",
            "properties": {"query": {"type": "string", "description": "检索串（如 M90 或 域包 id）"}},
            "required": ["query"],
        },
    },
    {
        "name": "library_search",
        "description": "仓库侧知识库检索（docs + community README + 编号方案文档），按标题/路径匹配。",
        "inputSchema": {
            "type": "object",
            "properties": {"query": {"type": "string", "description": "检索串"}},
            "required": ["query"],
        },
    },
    {
        "name": "module_read",
        "description": "取模块正文实质内容（04_模块库 + community modules，按 id 或限定 id 解析）。",
        "inputSchema": {
            "type": "object",
            "properties": {"module_id": {"type": "string", "description": "如 M90 或 通用:M10"}},
            "required": ["module_id"],
        },
    },
    {
        "name": "pipeline_read",
        "description": "取管线正文实质内容（03_管线库 + community pipelines，按 id 或相对路径）。",
        "inputSchema": {
            "type": "object",
            "properties": {"pipeline": {"type": "string", "description": "如 P90 或 community/…/P04….md"}},
            "required": ["pipeline"],
        },
    },
    {
        "name": "asset_get",
        "description": "取资产正文实质内容（community/*/assets + 05 用户自定义，按键/包定位）。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "key": {"type": "string", "description": "资产键（如 EMOTION_WHEEL / JOB / TECH_RULES）"},
                "package": {"type": "string", "description": "可选包过滤（如 校园情感领域包）"},
            },
            "required": ["key"],
        },
    },
]

PROMPT_DEFS = [
    {
        "name": "assemble_guide",
        "description": "NF 世界装配引导（作者/agent 五分钟上手 + 取件顺序）。",
    },
]


def _tool_pipeline_ls(query: str = "") -> list:
    root = _repo_root()
    out = []
    for pat in ("03_管线库/*.md", "community/*/pipelines/*.md"):
        for p in sorted(root.glob(pat)):
            text = p.read_text(encoding="utf-8")
            title = _md_title(text)
            rel = p.relative_to(root).as_posix()
            if query and query not in rel and query not in title:
                continue
            out.append({"path": rel, "title": title})
    return out


def _tool_spec_ls() -> list:
    reg = _read_json_rel("desktop/src/core/registry.json")
    return [{
        "id": p.get("id"), "version": p.get("version"),
        "modules": len(p.get("module_ids") or []),
        "categories": p.get("categories") or [],
    } for p in reg.get("protocols", [])]


def _tool_registry_query(query: str) -> dict:
    reg = _read_json_rel("desktop/src/core/registry.json")
    q = query.strip()
    modules = [m for m in reg.get("modules", [])
               if q in str(m.get("id")) or q in str(m.get("name"))]
    protos = [p for p in reg.get("protocols", [])
              if q in str(p.get("id")) or q in str(p.get("name"))]
    return {
        "modules": [{"id": m.get("id"), "name": m.get("name")} for m in modules],
        "protocols": [{"id": p.get("id"), "version": p.get("version"),
                       "modules": len(p.get("module_ids") or [])} for p in protos],
    }


def _tool_library_search(query: str, limit: int = 10) -> list:
    root = _repo_root()
    q = query.strip()
    hits = []
    for p in sorted(root.glob("*.md")):
        if p.name.startswith(("0", "4")) is False and not p.name[:2].isdigit():
            continue
        text = p.read_text(encoding="utf-8")
        title = _md_title(text)
        if q in p.name or q in title:
            hits.append({"path": p.name, "title": title})
    for p in sorted((root / "docs").glob("*.md")):
        text = p.read_text(encoding="utf-8")
        title = _md_title(text)
        if q in p.name or q in title:
            hits.append({"path": p.relative_to(root).as_posix(), "title": title})
    for p in sorted((root / "community").glob("*/README.md")):
        text = p.read_text(encoding="utf-8")
        title = _md_title(text)
        if q in p.name or q in title:
            hits.append({"path": p.relative_to(root).as_posix(), "title": title})
    return hits[:limit]


def _repo_module_index() -> list:
    from core import conformance_scan as csc
    import re

    root = _repo_root()
    out = []
    for doc in csc._module_docs(str(root)):
        text = Path(doc).read_text(encoding="utf-8")
        parsed = csc._fence_yaml(text, "machine_contract")
        mc = parsed.get("machine_contract") if isinstance(parsed, dict) else None
        mid = mc.get("id") if isinstance(mc, dict) else None
        m = re.search(r"#\s*模块\s+([^\s·]+)", text)
        title_id = m.group(1).strip() if m else None
        rel = Path(doc).relative_to(root).as_posix()
        out.append({"mc_id": mid, "title_id": title_id, "rel": rel,
                    "text": text, "has_contract": bool(mid)})
    out.sort(key=lambda x: x["rel"])
    return out


def _resolve_module(index: list, module_id: str) -> dict:
    import re

    req = module_id.strip()
    exact, suffix = [], []
    for it in index:
        ids = [x for x in (it["mc_id"], it["title_id"]) if x]
        if req in ids:
            exact.append(it)
        elif req.isdigit() and any(
                isinstance(x, str) and x.split(":", 1)[-1] == req for x in ids):
            suffix.append(it)
    if exact:
        return dict(exact[0])
    if len(suffix) == 1:
        return dict(suffix[0])
    if len(suffix) > 1:
        raise ValueError(
            "module_id 存在多个同号限定（如 通用:M10 / 生存:M10）——请用限定 id"
            "（修复指引：先 registry_query 查全限定 id 再重试）")
    raise ValueError("模块未找到：%s（module ls / registry_query 可枚举）"
                     "（修复指引：用仓库内真实模块 id，如 M90、M40 或 通用:M10）"
                     % module_id)


def _tool_module_read(module_id: str) -> dict:
    root = _repo_root()
    hit = _resolve_module(_repo_module_index(), module_id)
    text = Path(root, hit["rel"]).read_text(encoding="utf-8")
    return {"found": True,
            "id": hit["mc_id"] or hit["title_id"] or module_id,
            "path": hit["rel"],
            "has_machine_contract": hit["has_contract"],
            "bytes": len(text.encode("utf-8")),
            "text": text}


def _tool_pipeline_read(pipeline: str) -> dict:
    root = _repo_root()
    req = pipeline.strip()
    path = root / req
    if req.endswith(".md") and path.is_file():
        allowed = req.startswith("03_管线库/") or "/pipelines/" in req
        if not allowed:
            raise ValueError("管线路径越界：只读 03_管线库 与 community/*/pipelines"
                             "（修复指引：路径须指向仓库内管线件，如 03_管线库/P90….md）")
        text = path.read_text(encoding="utf-8")
        return {"found": True, "path": req, "bytes": len(text.encode("utf-8")),
                "text": text}
    hits = []
    for pat in ("03_管线库/*.md", "community/*/pipelines/*.md"):
        for p in sorted(root.glob(pat)):
            stem = p.name.split("_", 1)[0]
            if stem == req:
                hits.append(p)
    if not hits:
        raise ValueError("管线未找到：%s（pipeline_ls 可枚举）"
                         "（修复指引：用 Pxx 编号或仓库内相对路径）" % pipeline)
    hit = hits[0]
    text = hit.read_text(encoding="utf-8")
    return {"found": True, "path": hit.relative_to(root).as_posix(),
            "bytes": len(text.encode("utf-8")), "text": text}


def _asset_key_candidates(name: str) -> list:
    import re
    return re.findall(r"[A-Z][A-Z0-9_]*", name)


def _asset_keys_of_file(path: Path) -> list:
    """资产文件内登记的键集：文件名令牌 ∪ 正文键声明（`KEY` / "KEY": / ## KEY）。"""
    import re

    keys = set(_asset_key_candidates(path.stem))
    try:
        head = path.read_text(encoding="utf-8")[:6000]
    except OSError:
        return sorted(keys)
    keys.update(re.findall(r"`([A-Z][A-Z0-9_]{2,})`", head))
    keys.update(re.findall(r"\"([A-Z][A-Z0-9_]{2,})\"\s*:", head))
    keys.update(re.findall(r"##\s*([A-Z][A-Z0-9_]{2,})", head))
    return sorted(keys)


def _tool_asset_get(key: str, package: str = "") -> dict:
    root = _repo_root()
    req = key.strip()
    hits = []
    patterns = []
    if package:
        patterns.append("community/%s/assets/*.md" % package)
    else:
        patterns += ["community/*/assets/*.md", "05_资产库/用户自定义/*.md"]
    for pat in patterns:
        for p in sorted(root.glob(pat)):
            if p.name == "README.md":
                continue
            if req not in _asset_keys_of_file(p):
                continue
            rel = p.relative_to(root).as_posix()
            hits.append({"package": rel.split("/")[1] if rel.startswith("community") else "官方",
                         "file": rel, "key": req})
    if not hits:
        raise ValueError("资产键未找到：%s（asset ls / 包 assets/README.md 可枚举）"
                         "（修复指引：用包内资产键表登记的键名重试）" % key)
    out = []
    for h in hits:
        text = (root / h["file"]).read_text(encoding="utf-8")
        out.append({"package": h["package"], "file": h["file"],
                    "bytes": len(text.encode("utf-8")), "text": text})
    return {"found": True, "key": req, "matches": out}


TOOL_HANDLERS = {
    "pipeline_ls": lambda a: _tool_pipeline_ls((a or {}).get("query", "")),
    "spec_ls": lambda a: _tool_spec_ls(),
    "registry_query": lambda a: _tool_registry_query((a or {}).get("query", "")),
    "library_search": lambda a: _tool_library_search((a or {}).get("query", "")),
    "module_read": lambda a: _tool_module_read((a or {}).get("module_id", "")),
    "pipeline_read": lambda a: _tool_pipeline_read((a or {}).get("pipeline", "")),
    "asset_get": lambda a: _tool_asset_get((a or {}).get("key", ""),
                                           (a or {}).get("package", "")),
}


def _prompt_assemble_guide() -> str:
    return (
        "你是 NarrativeForge 装配师。取件顺序：07_官方核心出厂与社区预设导航.md（包索引）→ "
        "02_联动注册表.md（登记/依赖真相源）→ 01_核心协议.md（契约）→ 06_Agent执行协议.md。"
        "选装配包：community/<领域包>/README.md（含装载清单/资产/验收）。装配主规范："
        "agent_组装指令包_v0.2.md。输出完整版 md 自检过 "
        "「##7. 自检清单」；引用式档位须如实标注缺口，禁止编造未读内容。仓库验证：bash verify.sh。"
        "取实质内容用内容工具：module_read <模块 id>（模块正文）/ pipeline_read <Pxx 或路径>"
        "（管线正文）/ asset_get <资产键>（资产正文）——禁止凭记忆写未读取的模块/资产内容。"
        "标准资源面亦可取正文：resources/read nf://repo/module/<id> / nf://repo/pipeline/<Pxx> "
        "/ nf://repo/asset/<包>/<键>。"
    )


def _repo_resource_metas() -> list:
    """仓库内容资源元数据（nf://repo/…）：模块/管线/资产，纯元数据不含正文。"""
    import urllib.parse as up

    root = _repo_root()
    metas = []
    for it in _repo_module_index():
        mid = it["mc_id"] or it["title_id"]
        if not mid:
            continue
        uri = "nf://repo/module/" + up.quote(str(mid), safe="")
        metas.append({"uri": uri, "name": "模块 %s" % mid,
                      "mimeType": "text/markdown"})
    for pat in ("03_管线库/*.md", "community/*/pipelines/*.md"):
        for p in sorted(root.glob(pat)):
            stem = p.name.split("_", 1)[0]
            uri = "nf://repo/pipeline/" + up.quote(stem, safe="")
            metas.append({"uri": uri, "name": "管线 %s" % stem,
                          "mimeType": "text/markdown"})
    for pat in ("community/*/assets/*.md", "05_资产库/用户自定义/*.md"):
        for p in sorted(root.glob(pat)):
            if p.name == "README.md":
                continue
            keys = _asset_keys_of_file(p)
            if not keys:
                continue
            rel = p.relative_to(root).as_posix()
            package = rel.split("/")[1] if rel.startswith("community") else "官方"
            for k in keys:
                uri = "nf://repo/asset/" + up.quote(package, safe="") + "/" + up.quote(k, safe="")
                metas.append({"uri": uri, "name": "资产 %s/%s" % (package, k),
                              "mimeType": "text/markdown"})
    metas.sort(key=lambda m: m["uri"])
    return metas


def _repo_read_uri(uri: str) -> str:
    """nf://repo/<kind>/… → 仓库正文（只读）。未知结构抛 KeyError → 调用方转白名单拒绝。"""
    import urllib.parse as up

    root = _repo_root()
    parts = uri.split("/")
    if len(parts) < 4 or parts[0] != "nf:" or parts[2] != "repo":
        raise KeyError(uri)
    kind = parts[3]
    if kind == "module":
        mid = up.unquote(parts[4])
        hit = _resolve_module(_repo_module_index(), mid)
        return Path(root, hit["rel"]).read_text(encoding="utf-8")
    if kind == "pipeline":
        pid = up.unquote(parts[4])
        for pat in ("03_管线库/*.md", "community/*/pipelines/*.md"):
            for p in sorted(root.glob(pat)):
                if p.name.split("_", 1)[0] == pid:
                    return p.read_text(encoding="utf-8")
        raise KeyError(uri)
    if kind == "asset":
        package = up.unquote(parts[4])
        key = up.unquote(parts[5])
        for pat in ("community/%s/assets/*.md" % package,
                    "05_资产库/用户自定义/*.md"):
            for p in sorted(root.glob(pat)):
                if p.name == "README.md":
                    continue
                if key in _asset_keys_of_file(p):
                    return p.read_text(encoding="utf-8")
        raise KeyError(uri)
    raise KeyError(uri)


def _repo_resource_templates() -> list:
    """resources/templates/list：仓库内容寻址模板（URI 模板语义）。"""
    return [
        {"uriTemplate": "nf://repo/module/{id}",
         "name": "模块正文", "mimeType": "text/markdown",
         "description": "按模块 id / 限定 id 取正文"},
        {"uriTemplate": "nf://repo/pipeline/{id}",
         "name": "管线正文", "mimeType": "text/markdown",
         "description": "按 Pxx 或路径取管线正文"},
        {"uriTemplate": "nf://repo/asset/{package}/{key}",
         "name": "资产正文", "mimeType": "text/markdown",
         "description": "按包/键取资产正文"},
    ]


class UnknownUriError(KeyError):
    """resources/read 白名单外 uri 的专用信号（C2 只读拒绝）。

    从 KeyError 分化而非复用裸 KeyError：未来任何方法内部抛出的普通
    KeyError（真实 bug）不会被 handle() 误吞成「未知资源 uri」(-32602)——
    白名单拒绝只认本专用异常，其余内部错误归 INTERNAL_ERROR 面。
    """


class McpRuntime:
    """快照 → MCP 资源型 server 运行时。

    数据源 = mcp_adapter 产出的 mcp.json 快照（mcp{name, version, resources[]}）。
    内部把 text 从 Resource 元数据剥离，list 与 read 两段式对外。
    """

    def __init__(self, snapshot: Dict[str, Any]):
        mcp = snapshot.get("mcp", snapshot)
        self.server_name = str(mcp.get("name") or "nf-mcp")
        self.server_version = str(mcp.get("version") or "0.1.0")
        #: uri → Resource 元数据（无 text——G2 剥离点）
        self._meta: Dict[str, Dict[str, Any]] = {}
        #: uri → 正文（read 专用，G2 两段式）
        self._text: Dict[str, str] = {}
        #: 仓库实时内容资源（nf://repo/…，44 深化：标准资源面可取实质内容）
        self._repo_meta: Dict[str, Dict[str, str]] = {}
        try:
            for meta in _repo_resource_metas():
                self._repo_meta[meta["uri"]] = meta
        except Exception:
            self._repo_meta = {}
        for r in mcp.get("resources") or []:
            uri = r.get("uri")
            if not uri:
                continue
            self._meta[uri] = {
                "uri": uri,
                "name": r.get("name") or uri,
                "mimeType": r.get("mimeType") or "text/markdown",
            }
            self._text[uri] = r.get("text") or ""

    # ---- 消息面 ----
    def handle(self, msg: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """处理一条入站 JSON-RPC 消息。

        通知（无 id）→ None（不应答）；请求 → 响应 dict。
        """
        if not isinstance(msg, dict):
            return _err(INVALID_REQUEST, "消息必须是 JSON 对象")
        if msg.get("jsonrpc") != JSONRPC_VERSION:
            return _err(INVALID_REQUEST, f"jsonrpc 版本必须为 {JSONRPC_VERSION}")
        method = msg.get("method")
        if not isinstance(method, str):
            return _err(INVALID_REQUEST, "缺 method")
        # 通知：无 id 字段 → 处理但不应答
        is_request = "id" in msg
        rid = msg.get("id")
        params = msg.get("params") or {}

        try:
            result = self._dispatch(method, params)
        except UnknownUriError:
            # uri 白名单外（read）——仅 _read 抛的专用信号才归 -32602
            if is_request:
                return {"jsonrpc": JSONRPC_VERSION, "id": rid,
                        "error": {"code": INVALID_PARAMS, "message": "未知资源 uri"}}
            return None
        except ValueError as exc:
            if is_request:
                return {"jsonrpc": JSONRPC_VERSION, "id": rid,
                        "error": {"code": INVALID_PARAMS, "message": str(exc)}}
            return None

        if result is _NOT_IMPLEMENTED:
            if is_request:
                return {"jsonrpc": JSONRPC_VERSION, "id": rid,
                        "error": {"code": METHOD_NOT_FOUND,
                                  "message": f"Method not found: {method}"}}
            return None
        if not is_request:
            return None
        return {"jsonrpc": JSONRPC_VERSION, "id": rid, "result": result}

    def _dispatch(self, method: str, params: dict) -> Any:
        if method == "initialize":
            return self._initialize(params)
        if method == "resources/list":
            return self._list_resources(params)
        if method == "resources/templates/list":
            return {"resourceTemplates": _repo_resource_templates()}
        if method == "resources/read":
            return self._read(params)
        if method == "tools/list":
            return {"tools": TOOL_DEFS}
        if method == "tools/call":
            return self._call_tool(params)
        if method == "prompts/list":
            return {"prompts": [{"name": d["name"], "description": d["description"]}
                                for d in PROMPT_DEFS]}
        if method == "prompts/get":
            return self._prompt_get(params)
        if method == "ping":
            return {}
        return _NOT_IMPLEMENTED

    # ---- 方法实现 ----
    def _initialize(self, params: dict) -> dict:
        return {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {"resources": {}, "tools": {}, "prompts": {}},
            "serverInfo": {"name": self.server_name, "version": self.server_version},
        }

    # ---- C7 只读 tools/prompts（41 波C；无写路径）----
    def _call_tool(self, params: Any) -> dict:
        if not isinstance(params, dict) or not isinstance(params.get("name"), str):
            raise ValueError("tools/call 需 params{name, arguments}")
        name = params["name"]
        args = params.get("arguments") or {}
        if not isinstance(args, dict):
            raise ValueError("arguments 须为对象")
        handler = TOOL_HANDLERS.get(name)
        if handler is None:
            raise ValueError("未知工具：%s（只读工具面 = %s）"
                             % (name, "、".join(sorted(TOOL_HANDLERS))))
        result = handler(args)
        return {"content": [{"type": "text",
                             "text": json.dumps(result, ensure_ascii=False,
                                                indent=2, sort_keys=True)}]}

    def _prompt_get(self, params: Any) -> dict:
        name = params.get("name") if isinstance(params, dict) else None
        if name != "assemble_guide":
            raise ValueError("未知 prompt：%s（prompts/list 可枚举）" % name)
        return {
            "description": "NF 世界装配引导（只读模板）",
            "messages": [{"role": "user",
                          "content": {"type": "text",
                                      "text": _prompt_assemble_guide()}}],
        }

    def _read(self, params: dict) -> dict:
        uri = params.get("uri") if isinstance(params, dict) else None
        if isinstance(uri, str) and uri in self._repo_meta:
            try:
                text = _repo_read_uri(uri)
            except (KeyError, OSError):
                raise UnknownUriError(uri)
            return {"contents": [{"uri": uri, "mimeType": "text/markdown",
                                  "text": text}]}
        if not isinstance(uri, str) or uri not in self._text:
            # C2 白名单：未知 uri 拒绝（schema 无 not-found 码，参数级拒绝）
            raise UnknownUriError(uri)
        return {"contents": [{
            "uri": uri,
            "mimeType": self._meta[uri]["mimeType"],
            "text": self._text[uri],
        }]}

    def _list_resources(self, params: dict) -> dict:
        """resources/list 分页 + 过滤（type=module|pipeline|asset / package）。"""
        items = list(self._meta.values()) + list(self._repo_meta.values())
        ftype = None
        fpackage = None
        if isinstance(params, dict):
            ftype = params.get("type")
            fpackage = params.get("package")
        if ftype or fpackage:
            import urllib.parse as up

            kept = []
            for it in items:
                uri = it["uri"]
                parts = uri.split("/")
                if len(parts) >= 5 and parts[0] == "nf:" and parts[2] == "repo":
                    kind = parts[3]
                    if ftype and kind != ftype:
                        continue
                    if fpackage:
                        if kind == "asset":
                            pkg = up.unquote(parts[4])
                        elif kind in ("module", "pipeline"):
                            pkg = it.get("name", "").split(" ", 1)[-1]
                            pkg = ""
                        if pkg != fpackage:
                            continue
                elif ftype:
                    continue
                kept.append(it)
            items = kept
        page = 20
        start = 0
        if isinstance(params, dict) and isinstance(params.get("cursor"), str):
            try:
                start = max(0, int(params["cursor"]))
            except ValueError:
                start = 0
        end = start + page
        out = {"resources": items[start:end]}
        if end < len(items):
            out["nextCursor"] = str(end)
        return out

    # ---- transport ----
    def serve_stdio(self, stdin: Optional[TextIO] = None,
                    stdout: Optional[TextIO] = None) -> int:
        """stdio transport 主循环：逐行读 stdin → handle → 写 stdout。

        transport 纪律（modelcontextprotocol.io 2025-11-25 transports 页实证）：
        消息以换行分隔、UTF-8、消息内不得含嵌入换行；stdout 只写 MCP 消息；
        stderr 可作日志通道（本实现静默，日志由调用方决定）。
        """
        stdin = stdin or sys.stdin
        stdout = stdout or sys.stdout
        # transport 纪律：消息 MUST 为 UTF-8 编码（schema.ts JSONRPCMessage）——
        # Windows 下管道默认按 locale（GBK）解码，须强制 UTF-8，否则含非 ASCII
        # uri 的消息会乱码、命中白名单拒绝。
        for stream in (stdin, stdout):
            reconfigure = getattr(stream, "reconfigure", None)
            if reconfigure is not None:
                try:
                    reconfigure(encoding="utf-8")
                except (ValueError, OSError):
                    pass
        try:
            for line in stdin:
                line = line.strip()
                if not line:
                    continue
                try:
                    msg = json.loads(line)
                except json.JSONDecodeError:
                    out = _err(PARSE_ERROR, "Parse error")
                    stdout.write(json.dumps(out, ensure_ascii=False) + "\n")
                    stdout.flush()
                    continue
                try:
                    resp = self.handle(msg)
                except Exception as exc:  # 防御：单条消息异常不杀循环
                    resp = _err(INTERNAL_ERROR, f"Internal error: {exc}")
                if resp is not None:
                    stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
                    stdout.flush()
        except KeyboardInterrupt:
            # Ctrl+C：会话正常终止——静默退出，不打印 traceback
            return 130
        except BrokenPipeError:
            # client 已断开（管道破裂）：stdio 会话正常终止——静默退出
            return 0
        return 0


#: 哨兵：方法存在但本运行时未实现（只读纪律——写路径/未知方法一律拒出）
_NOT_IMPLEMENTED = object()


def load_snapshot(path: str) -> Dict[str, Any]:
    """读 mcp.json 静态快照 → 运行时数据源 dict（mcp{name, version, resources[]}）。"""
    p = Path(path)
    data = json.loads(p.read_text(encoding="utf-8"))
    if "mcp" not in data:
        raise ValueError(f"快照缺 mcp 顶层键（非 mcp.json 产物）：{p}")
    return data


def main(argv: Optional[List[str]] = None) -> int:
    """CLI 入口：python -m core.mcp_runtime <mcp.json>（stdio 服务）。"""
    from core import plog
    log = plog.get_logger("mcp_runtime")
    args = list(argv) if argv is not None else sys.argv[1:]
    if not args:
        log.error("用法: python -m core.mcp_runtime <mcp.json>  （stdio MCP 服务）")
        return 2
    snap = load_snapshot(args[0])
    srv = McpRuntime(snap)
    log.info("MCP server 启动：%s v%s（stdio · 只读 resources/tools/prompts）",
             srv.server_name, srv.server_version)
    rc = srv.serve_stdio()
    log.info("MCP server 退出：rc=%s", rc)
    return rc


if __name__ == "__main__":
    sys.exit(main())
