"""互操作导出面（外部标准净吸收：OpenAPI 3.1 / AsyncAPI 3.0 / in-toto Statement v1 /
SPDX 2.3 / CloudEvents 属性 / RFC 9457 Problem Details）。

内部差距（本波实证）：NF 的**声明面**已经很厚——8 条服务端点契约、43 条事件载荷、
48 条协议层回执（Merkle 单根）、依赖登记面（hard/soft import）——但**没有一条能直接
喂给外部标准工具**的导出面：外部读者只能读 NF 自己的 JSON 形状，无法用 OpenAPI 校验器、
AsyncAPI 代码生成器、in-toto 校验器或 SPDX 扫描器对接。

定位纪律：**纯派生，不新增真源**。所有字段都从既有声明件实时算出，此处绝不引入新的
手工维护值；因此「导出面漂移」在结构上不可能发生——门禁断言的是**覆盖完整 + 形状合法
+ 确定性**（同输入两次导出逐字节一致）。

落点：check33「新面汇总」（不新增 check 序号，ADR-0002）。
"""
from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, List, Tuple

CONTRACT_REL = "protocol/endpoint_contract.json"
EVENTS_REL = "protocol/event_registry.json"
EXTERNAL_EVENTS_REL = "protocol/external_events.json"
RECEIPTS_REL = "protocol/RECEIPTS.json"

#: NF 项目自身的许可结论（与 LICENSE 同源）
LICENSE_NAME = "MIT"

#: SBOM `created` 的派生源（N=非墙钟）：从仓内**已声明日期**取最大值——
#: 目的有二：① SPDX 2.3 的 `creationInfo.created` 是必填（外部 meta-schema 实测会 FAIL）；
#: ② 摘要/导出面必须确定性可复现，用 `now()` 会破坏「两次渲染逐字节一致」的判据。
_DATE_SOURCES = ("protocol/score_baseline.json", "05_资产库/provenance.json")
_DATE_RE = re.compile(r"20\d\d-\d\d-\d\d")


def _declared_max_date(root: str) -> str:
    """仓内声明日期的最大值（YYYY-MM-DD）；取不到返回空串（门禁侧会记 FAIL）。"""
    dates: List[str] = []
    for rel in _DATE_SOURCES:
        path = os.path.join(root, rel)
        if os.path.isfile(path):
            with open(path, encoding="utf-8") as fh:
                dates += _DATE_RE.findall(fh.read())
    d = os.path.join(root, "protocol", "approvals")
    if os.path.isdir(d):
        for name in sorted(os.listdir(d)):
            if name.endswith(".json"):
                with open(os.path.join(d, name), encoding="utf-8") as fh:
                    dates += _DATE_RE.findall(fh.read())
    return max(dates) if dates else ""


def _read_json(root: str, rel: str) -> Dict[str, Any]:
    path = os.path.join(root, rel)
    if not os.path.isfile(path):
        return {}
    with open(path, encoding="utf-8") as fh:
        try:
            return json.load(fh)
        except json.JSONDecodeError:
            return {}


_TYPE_MAP = {"string", "integer", "number", "boolean", "object", "array"}
_HEAD = re.compile(r"^\s*([a-z]+)")


def _schema_for(desc: str) -> Dict[str, Any]:
    """字段说明串 → JSON Schema 片段（只做可判定映射，未识别一律 object 保守兜底）。"""
    m = _HEAD.match(str(desc or ""))
    token = m.group(1) if m else ""
    jtype = token if token in _TYPE_MAP else "object"
    nullable = "null" in str(desc or "")
    out: Dict[str, Any] = {"type": [jtype, "null"] if nullable else jtype}
    if jtype == "array":
        out["items"] = {}
    if jtype == "object":
        out["additionalProperties"] = True
    if str(desc or "").strip():
        out["description"] = str(desc)
    return out


def openapi_doc(root: str = ".") -> Dict[str, Any]:
    """服务端点契约 → OpenAPI 3.1 文档（纯派生）。"""
    contract = _read_json(root, CONTRACT_REL)
    conv = contract.get("conventions") or {}
    # 幂等声明面（RFC 9110 §9.2.2）：默认幂等，例外在契约层登记 → 派生面逐端点标注
    non_idem = {str(e.get("id")): str(e.get("key") or "")
                for e in (contract.get("idempotency_exceptions") or [])}
    paths: Dict[str, Any] = {}
    for ep in contract.get("endpoints") or []:
        path = str(ep.get("path") or "")
        method = str(ep.get("method") or "").lower()
        if not path or not method:
            continue
        req = ep.get("request") or {}
        resp = ep.get("response") or {}
        op: Dict[str, Any] = {
            "operationId": str(ep.get("id") or ""),
            "summary": "maps_to %s" % str(ep.get("maps_to") or ""),
            "x-nf-idempotency": ("non-idempotent（幂等键 %s）" % non_idem[str(ep.get("id"))]
                                 if str(ep.get("id")) in non_idem else "idempotent"),
            "responses": {
                "200": {"description": "成功",
                        "content": {"application/json": {"schema": {
                            "type": "object",
                            "properties": {k: _schema_for(v) for k, v in resp.items()},
                        }}}},
                "default": {"description": "错误（RFC 9457 Problem Details 映射见 "
                                           "x-nf-error-mapping）",
                            "content": {"application/json": {"schema": {
                                "$ref": "#/components/schemas/NfError"}}}},
            },
        }
        if req or method == "post":
            op["requestBody"] = {
                "required": True,
                "content": {"application/json": {"schema": {
                    "type": "object",
                    "properties": {k: _schema_for(v) for k, v in req.items()},
                }}},
            }
        if ep.get("streaming"):
            op["responses"]["200"]["content"]["text/event-stream"] = {
                "schema": {"type": "string"},
                "x-nf-streaming": conv.get("streaming", ""),
            }
        if ep.get("deprecated"):
            op["deprecated"] = True
            op["x-nf-sunset"] = ep.get("sunset")
            op["x-nf-replacement"] = ep.get("replacement")
        paths.setdefault(path, {})[method] = op
    return {
        "openapi": "3.1.0",
        "info": {"title": "NarrativeForge 服务端点契约（派生）",
                 "version": "1.0.0",
                 "description": "由 protocol/endpoint_contract.json 实时派生（status=%s）；"
                                "本文件非真源。" % contract.get("status", "")},
        "servers": [],
        "paths": paths,
        "components": {"schemas": {
            "NfError": {
                "type": "object",
                "required": ["error"],
                "properties": {"error": {
                    "type": "object",
                    "required": ["code", "message"],
                    "properties": {"code": {"type": "integer",
                                            "description": "机器可判定错误码"},
                                   "message": {"type": "string",
                                               "description": "人读说明，必须带修复指引"},
                                   "data": {"type": ["object", "null"]}},
                }},
            },
        }},
        "x-nf-error-mapping": {
            "type": "about:blank",
            "title": "error.message",
            "detail": "error.message + 修复指引（patterns/error-message-guidance）",
            "instance": "请求路径",
            "status": "HTTP 状态码（与 message 同源）",
            "source": conv.get("errors", ""),
        },
        "x-nf-endpoints": len(contract.get("endpoints") or []),
    }


def asyncapi_doc(root: str = ".") -> Dict[str, Any]:
    """事件登记 → AsyncAPI 3.0 文档 + CloudEvents 属性（纯派生）。"""
    reg = _read_json(root, EVENTS_REL)
    ext = _read_json(root, EXTERNAL_EVENTS_REL)
    events: Dict[str, Any] = {}
    for src in (reg.get("events") or {}, ext.get("events") or {}):
        if isinstance(src, dict):
            for name, meta in src.items():
                events.setdefault(str(name), meta if isinstance(meta, dict) else {})
    channels: Dict[str, Any] = {}
    messages: Dict[str, Any] = {}
    for name, meta in sorted(events.items()):
        fields = meta.get("fields") or {}
        channels["nf/%s" % name] = {
            "address": "nf/%s" % name,
            "title": name,
            "messages": {"nf.%s" % name: {"$ref": "#/components/messages/%s" % name}},
            "x-nf-cloudevents": {"type": "nf.%s" % name, "source": "urn:nf:repo",
                                 "specversion": "1.0",
                                 "datacontenttype": "application/json"},
        }
        messages[name] = {
            "name": name,
            "contentType": "application/json",
            "payload": {"type": "object",
                        "properties": {k: _schema_for((v or {}).get("type", ""))
                                       for k, v in fields.items()}},
            "x-nf-note": str(meta.get("note") or "")[:200],
        }
    return {
        "asyncapi": "3.0.0",
        "info": {"title": "NarrativeForge 事件登记（派生）", "version": "1.0.0",
                 "description": "由 protocol/event_registry.json + external_events.json "
                                "实时派生；本文件非真源。"},
        "channels": channels,
        "operations": {
            "publish/%s" % n: {"action": "send",
                               "channel": {"$ref": "#/channels/nf/%s" % n}}
            for n in sorted(events)},
        "components": {"messages": messages},
        "x-nf-events": len(events),
    }


def intoto_statement(root: str = ".") -> Dict[str, Any]:
    """协议层回执 → in-toto Statement v1（消费者：in-toto / cosign 系校验器）。"""
    rec = _read_json(root, RECEIPTS_REL)
    subject = [{"name": str(e.get("path") or ""),
                "digest": {"sha256": str(e.get("digest") or "")}}
               for e in (rec.get("entries") or [])]
    return {
        "_type": "https://in-toto.io/Statement/v1",
        "subject": subject,
        "predicateType": "https://narrativeforge.dev/attestation/protocol-receipts/v1",
        "predicate": {
            "algorithm": rec.get("algorithm", ""),
            "root": rec.get("root", ""),
            "count": rec.get("count", len(subject)),
            "scope": rec.get("scope", ""),
            "note": "派生自 protocol/RECEIPTS.json；inclusion proof 留在原回执单根内。",
        },
    }


def sbom_doc(root: str = ".") -> Dict[str, Any]:
    """依赖登记面 → SPDX 2.3 风格 SBOM（消费者：外部依赖扫描器）。"""
    import sys

    nf_version = "0.0.0"
    verify_path = os.path.join(root, "verify.sh")
    if os.path.isfile(verify_path):
        with open(verify_path, encoding="utf-8") as fh:
            m = re.search(r"# 版本\s*:\s*(v[0-9.]+)", fh.read())
        if m:
            nf_version = m.group(1)
    sys.path.insert(0, os.path.join(root, "desktop", "src"))
    try:
        from core import purity_scan as ps
        hard = dict(ps.HARD_ALLOW)
        soft = dict(ps.SOFT_IMPORTS)
    except Exception:  # pragma: no cover - 登记面不可读即空表（门禁侧会报）
        hard, soft = {}, {}
    packages: List[Dict[str, Any]] = [{
        "SPDXID": "SPDXRef-Package-narrativeforge",
        "name": "NarrativeForge",
        "versionInfo": nf_version,
        "downloadLocation": "NOASSERTION",
        "licenseConcluded": LICENSE_NAME,
        "licenseDeclared": LICENSE_NAME,
        "copyrightText": "NOASSERTION",
    }]
    deps: List[Tuple[str, str]] = []
    for name, why in sorted(hard.items()):
        pkg = "SPDXRef-Dependency-%s" % name
        packages.append({"SPDXID": pkg, "name": name, "downloadLocation": "NOASSERTION",
                         "licenseConcluded": "NOASSERTION",
                         "comment": "硬依赖（登记）：%s" % why})
        deps.append((pkg, "DEPENDENCY_OF"))
    for name, why in sorted(soft.items()):
        pkg = "SPDXRef-Optional-%s" % name
        packages.append({"SPDXID": pkg, "name": name, "downloadLocation": "NOASSERTION",
                         "licenseConcluded": "NOASSERTION",
                         "comment": "软依赖（可选，须 try/except 守卫）：%s" % why})
        deps.append((pkg, "OPTIONAL_DEPENDENCY_OF"))
    return {
        "spdxVersion": "SPDX-2.3",
        "dataLicense": "CC0-1.0",
        "SPDXID": "SPDXRef-DOCUMENT",
        "name": "narrativeforge-sbom",
        "documentNamespace": "https://narrativeforge.dev/spdx/%s" % nf_version,
        "creationInfo": {
            "creators": ["Tool: nf interop --kind sbom"],
            "created": ("%sT00:00:00Z" % _declared_max_date(root)) if _declared_max_date(root)
                       else "",
            "comment": "由纯度扫描登记面（HARD_ALLOW / SOFT_IMPORTS）实时派生；"
                       "created = 仓内声明日期最大值（非墙钟，保确定性）",
        },
        # SPDX 2.3 根级允许 `comment`（`documentComment` 不在词表内，实测被 meta-schema 拦下）
        "comment": "派生面非真源；created = max(仓内声明日期: "
                   "score_baseline / provenance / approvals)（保确定性，非墙钟）。",
        "packages": packages,
        "relationships": ([{"spdxElementId": "SPDXRef-DOCUMENT",
                            "relatedSpdxElement": "SPDXRef-Package-narrativeforge",
                            "relationshipType": "DESCRIBES"}]
                          + [{"spdxElementId": pkg,
                              "relatedSpdxElement": "SPDXRef-Package-narrativeforge",
                              "relationshipType": rel} for pkg, rel in deps]),
    }


def slsa_provenance(root: str = ".") -> Dict[str, Any]:
    """SLSA Provenance v1（in-toto predicate）——从**本地门禁事实**派生，不宣称外部构建。

    诚实边界：NF 的「构建」= 本地 verify 门禁（无远程 builder、无托管构建平台），
    因此 `builder.id` 指向本仓门禁脚本、`buildType` 是 NF 自定义型别，并在 `metadata` 里
    写明这不是 SLSA 认证等级声明。派生源 = verify.sh 版本头 + `protocol/score_baseline.json`
    + `protocol/RECEIPTS.json`（三者都是既有真源）。
    """
    rec = _read_json(root, RECEIPTS_REL)
    # 基线句的真源 = core.quality_baseline（verify.sh 为单一真值，本模块只读期望值）；
    # 不读 score_baseline.json——它只有分数与信号，没有 check 数/PASS 数（早期写成 0 的真事故）。
    import sys as _sys
    _sys.path.insert(0, os.path.join(root, "desktop", "src"))
    try:
        from core import quality_baseline as qb
        want_checks, want_pass = qb.EXPECTED_CHECKS, qb.EXPECTED_PASS
    except Exception:  # pragma: no cover - 真源不可读即 0（门禁侧会判 FAIL）
        want_checks = want_pass = 0
    version = ""
    verify_path = os.path.join(root, "verify.sh")
    if os.path.isfile(verify_path):
        with open(verify_path, encoding="utf-8") as fh:
            m = re.search(r"# 版本\s*:\s*(v[0-9.]+)", fh.read())
        version = m.group(1) if m else ""
    subjects = [{"name": str(e.get("path") or ""),
                 "digest": {"sha256": str(e.get("digest") or "")}}
                for e in (rec.get("entries") or [])]
    return {
        "_type": "https://in-toto.io/Statement/v1",
        "subject": subjects,
        "predicateType": "https://slsa.dev/provenance/v1",
        "predicate": {
            "buildDefinition": {
                "buildType": "https://narrativeforge.dev/buildtypes/local-gate/v1",
                "externalParameters": {
                    "gate": "verify.sh",
                    "gateVersion": version,
                    "declaredBaseline": "check1-%d PASS=%d" % (
                        want_checks, want_pass),
                    "note": "参数取自仓内声明件（不引入新真源）",
                },
                "internalParameters": {"repoRoot": "relative"},
                "resolvedDependencies": [{"uri": "nf://repo/%s" % s["name"]}
                                         for s in subjects],
            },
            "runDetails": {
                "builder": {"id": "https://narrativeforge.dev/builder/verify-sh"},
                "metadata": {
                    "invocationId": str(rec.get("root") or "")[:16],
                    "note": "本地门禁执行事实；**不构成 SLSA 等级声明**（无远程 builder）",
                },
            },
        },
    }


def prov_document(root: str = ".") -> Dict[str, Any]:
    """PROV-O（W3C Provenance Ontology）派生面：资产 / 馆藏 / 回执 → 实体·活动·代理三元组。

    真源：`05_资产库/provenance.json`（资产）+ `library/INDEX.md`（馆藏行）+ 
    `protocol/transform_log.json`（消化活动）+ `protocol/RECEIPTS.json`（回执绑定）。
    诚实边界：只写仓内**已有**的事实（谁何时入库、资产属谁、改了什么），不推断来源；
    空面如实为空（transform_log 当前 0 条 → activities 里就没有消化活动）。
    """
    prov = _read_json(root, "05_资产库/provenance.json")
    transform = _read_json(root, "protocol/transform_log.json")
    rec = _read_json(root, RECEIPTS_REL)
    nodes: Dict[str, Dict[str, Any]] = {}

    def add(node: Dict[str, Any]) -> None:
        """去重入图（同 id 只留一次——同一投稿人/同一文件会自然重复出现）。"""
        nodes.setdefault(str(node.get("@id")), node)

    # ① 实体：资产（键 / 归属模块 / 状态）
    for a in prov.get("assets") or []:
        add({"@id": "nf:asset/%s" % a.get("key"), "@type": "prov:Entity",
             "prov:label": str(a.get("key") or ""),
             "nf:file": str(a.get("file") or ""),
             "nf:module": str(a.get("module") or ""),
             "nf:status": str(a.get("status") or ""),
             "nf:version": str(a.get("version") or "")})
    # ② 实体 + 入库活动：馆藏条目（活动与代理来自 INDEX 行的真值）
    idx = os.path.join(root, "library", "INDEX.md")
    if os.path.isfile(idx):
        with open(idx, encoding="utf-8") as fh:
            for line in fh:
                if not re.match(r"^\|\s*NF-[A-Za-z0-9\-]+\s*\|", line):
                    continue
                cells = [c.strip() for c in line.strip().strip("|").split("|")]
                if len(cells) < 6:
                    continue
                eid, author, date, lic = cells[0], cells[3], cells[4], cells[5]
                add({"@id": "nf:library/%s" % eid, "@type": "prov:Entity",
                     "prov:label": cells[1], "nf:license": lic})
                add({"@id": "nf:activity/library-ingest/%s" % eid,
                     "@type": "prov:Activity", "prov:endedAtTime": date,
                     "prov:wasAssociatedWith": "nf:agent/%s" % author,
                     "prov:generated": "nf:library/%s" % eid})
                add({"@id": "nf:agent/%s" % author, "@type": "prov:Person",
                     "prov:label": author})
    # ③ 实体：回执绑定的协议层文件（内容寻址）
    for e in rec.get("entries") or []:
        add({"@id": "nf:file/%s" % e.get("path"), "@type": "prov:Entity",
             "nf:sha256": str(e.get("digest") or "")})
    # ④ 活动：消化记录（把「参考级源 → 本地产物」的转换写成活动，逐条绑 digest）
    for i, t in enumerate(transform.get("entries") or [], 1):
        add({"@id": "nf:transform/%d" % i, "@type": "prov:Activity",
             "prov:used": "nf:file/%s" % (t.get("source") or t.get("from") or ""),
             "prov:generated": "nf:file/%s" % (t.get("product") or t.get("to") or ""),
             "nf:digest": str(t.get("digest") or "")})
    # ⑤ 代理：仓本体（软件代理）
    add({"@id": "nf:agent/verify-sh", "@type": "prov:SoftwareAgent",
         "prov:label": "NarrativeForge verify.sh 门禁",
         "nf:present": os.path.isfile(os.path.join(root, "verify.sh"))})
    graph = [nodes[k] for k in sorted(nodes)]
    return {
        "@context": {"prov": "http://www.w3.org/ns/prov#",
                     "nf": "https://narrativeforge.dev/ns#"},
        "schema": "nf-prov/1",
        "note": "由仓内声明件派生（资产 / 馆藏 / 消化记录 / 回执）；本文件非真源，"
                "空面即如实为空。",
        "@graph": graph,
        "x-nf-counts": {"entities": sum(1 for n in graph if n["@type"] == "prov:Entity"),
                        "activities": sum(1 for n in graph if n["@type"] == "prov:Activity"),
                        "agents": sum(1 for n in graph
                                      if n["@type"] in ("prov:Person", "prov:SoftwareAgent"))},
    }


def cyclonedx_doc(root: str = ".") -> Dict[str, Any]:
    """CycloneDX 1.5 SBOM（派生自依赖登记面 + LICENSE）——SPDX 之外的第二个 SBOM 形状。

    与 `sbom_doc`（SPDX 2.3）**同源不同形**：都读 `purity_scan.HARD_ALLOW / SOFT_IMPORTS`，
    因此不存在「两份 SBOM 互相漂移」的问题；`serialNumber` 用内容寻址的 urn:uuid
    形式（由本仓声明摘要派生，保确定性，非随机 UUID）。
    """
    sbom = sbom_doc(root)
    import hashlib
    import sys as _sys
    _sys.path.insert(0, os.path.join(root, "desktop", "src"))
    try:
        from core import purity_scan as ps
        hard, soft = dict(ps.HARD_ALLOW), dict(ps.SOFT_IMPORTS)
    except Exception:  # pragma: no cover
        hard, soft = {}, {}
    seed = hashlib.sha256((sbom.get("documentNamespace") or "").encode("utf-8")).hexdigest()
    serial = "urn:uuid:%s-%s-%s-%s-%s" % (seed[:8], seed[8:12], seed[12:16],
                                          seed[16:20], seed[20:32])
    components = []
    for name, why in sorted(hard.items()):
        components.append({"type": "library", "bom-ref": "dep:%s" % name, "name": name,
                           "scope": "required", "description": "硬依赖（登记）：%s" % why})
    for name, why in sorted(soft.items()):
        components.append({"type": "library", "bom-ref": "opt:%s" % name, "name": name,
                           "scope": "optional",
                           "description": "软依赖（可选，须守卫）：%s" % why})
    return {
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "serialNumber": serial,
        "version": 1,
        "metadata": {
            "timestamp": sbom.get("creationInfo", {}).get("created", ""),
            "component": {"type": "application", "bom-ref": "pkg:nf/narrativeforge@%s"
                          % sbom.get("packages", [{}])[0].get("versionInfo", "0.0.0"),
                          "name": "NarrativeForge",
                          "licenses": [{"license": {"id": LICENSE_NAME}}]},
            "tools": [{"vendor": "NarrativeForge", "name": "nf interop --kind cyclonedx",
                       "version": "1.0.0"}],
            # CycloneDX 根级 additionalProperties=false（官方 meta-schema 实测拦下自定义键）
            # → 自述信息只许落在 metadata.properties 里
            "properties": [
                {"name": "nf:source", "value": "purity_scan 依赖登记面（纯派生）"},
                {"name": "nf:note",
                 "value": "与 SPDX 面同源；timestamp 取仓内声明日期最大值（非墙钟）。"},
            ],
        },
        "components": components,
    }


def vc_document(root: str = ".") -> Dict[str, Any]:
    """W3C Verifiable Credential（VC Data Model 2.0 形状）——内容绑定的「一致性凭证」。

    诚实边界：**未签名**。VC 的可验证性来自 proof（JWS/Data Integrity），而 NF 的签名走
    ssh 外挂锚（`nf attest` + `library/anchors/*.sig`），两者套件不同；故本件产出
    **未签名凭证形状**并把状态写进 `x-nf-proof-status`（门禁判该注记必须在场）——
    形状可被 VC 工具链读，但**不宣称可验证**。
    """
    rec = _read_json(root, RECEIPTS_REL)
    rep = _read_json(root, "protocol/conformance_report.json")
    approvals = []
    adir = os.path.join(root, "protocol", "approvals")
    if os.path.isdir(adir):
        for name in sorted(os.listdir(adir)):
            if name.endswith(".json"):
                a = _read_json(root, os.path.join("protocol", "approvals", name))
                if a:
                    approvals.append(a)
    issuer = str((approvals[0].get("approved_by") if approvals else "") or "NarrativeForge")
    valid_from = str((approvals[0].get("approved_at") if approvals else "") or "")
    return {
        "@context": ["https://www.w3.org/ns/credentials/v2",
                     "https://narrativeforge.dev/ns/credentials/v1"],
        "type": ["VerifiableCredential", "NfConformanceCredential"],
        "issuer": issuer,
        "validFrom": valid_from,
        "credentialSubject": {
            "id": "nf:conformance_report",
            "verdict": str(rep.get("verdict") or ""),
            "contracts": len(rep.get("contracts") or []),
            "receiptRoot": str(rec.get("root") or ""),
            "receiptCount": int(rec.get("count") or 0),
        },
        "x-nf-proof-status": "unsigned（本仓签名走 ssh 外挂锚 nf attest；未接 JWS/Data Integrity "
                             "签名套件——形状可读，不可验证，勿当凭证使用）",
        "x-nf-note": "派生自 protocol/conformance_report.json + protocol/RECEIPTS.json + "
                     "protocol/approvals/*（纯派生，不新增真源）",
    }


def c2pa_manifest(root: str = ".") -> Dict[str, Any]:
    """C2PA 内容凭证的 **JSON 清单形态**（未做 JUMBF/CBOR 封装、未签名）。

    取 C2PA 2.x 的 JSON 表示字段面（`claim_generator` / `assertions[label,data]`），
    硬绑定用 `c2pa.hash.data`（sha256）指向被证内容——与回执/attest 同一份摘要口径。
    诚实边界：生产级 C2PA 需要 CBOR/JUMBF 封装与 X.509 签名，本仓**不做**（无证书链），
    故只出 JSON 清单并把状态写进 `x-nf-package-status`（门禁判该注记在场）。
    """
    rec = _read_json(root, RECEIPTS_REL)
    sample = next((e for e in (rec.get("entries") or []) if e.get("path")), None)
    assertions = [{"label": "c2pa.actions",
                   "data": {"actions": [{"action": "c2pa.created",
                                         "digitalSourceType": "http://cv.iptc.org/newscodes/"
                                                              "digitalsourcetype/digitalCapture"}]}}]
    if sample:
        assertions.append({"label": "c2pa.hash.data",
                           "data": {"alg": "sha256", "hash": str(sample.get("digest") or ""),
                                    "name": str(sample.get("path"))}})
    return {
        "claim_generator": "NarrativeForge/1.0 (nf interop --kind c2pa)",
        "claim_generator_info": [{"name": "NarrativeForge", "version": "1.0.0"}],
        "title": "NarrativeForge 协议层内容清单",
        "format": "application/json",
        "assertions": assertions,
        "x-nf-package-status": "未封装（无 JUMBF/CBOR 容器）、未签名（无 X.509 证书链）——"
                               "只出 JSON 清单形状，不得当作可验证内容凭证",
        "x-nf-source": "protocol/RECEIPTS.json（回执摘要）",
    }


def cid_index(root: str = ".") -> Dict[str, Any]:
    """内容寻址索引：回执 → CIDv1（multibase base32 / codec raw / sha2-256）。

    为什么有用：CID 给外部系统一个**自描述、可校验、跨系统唯一**的内容地址
    （multiformats 生态），不必依赖 NF 路径约定。实现只用标准库（`base64.b32encode`
    小写化去填充），故零依赖；已知向量见单测：raw codec（0x71）+ sha2-256 下
    `sha256("")` → `bafyreihdwdcefgh4dqkjv67uzcmw7ojee6xedzdetojuzjevtenxquvyku`
    （注：IPFS 空文件常见的 `bafkrei…` 是 dag-pb codec 0x70，非本面所用的 raw codec）。
    """
    import base64
    import hashlib
    rec = _read_json(root, RECEIPTS_REL)

    def cidv1_raw_sha256(digest_hex: str) -> str:
        raw = bytes.fromhex(digest_hex)
        mh = b"\x12\x20" + raw               # 0x12 = sha2-256, 0x20 = 32 字节
        return "b" + base64.b32encode(b"\x01\x71" + mh).decode("ascii").lower().rstrip("=")

    entries = []
    for e in rec.get("entries") or []:
        d = str(e.get("digest") or "")
        entries.append({"path": str(e.get("path") or ""), "sha256": d,
                        "cid": cidv1_raw_sha256(d) if re.fullmatch(r"[0-9a-f]{64}", d) else ""})
    return {
        "schema": "nf-cid-index/1",
        "multibase": "base32 (lowercase, no padding, prefix 'b')",
        "codec": "raw (0x71)",
        "multihash": "sha2-256 (0x12)",
        "entries": entries,
        "x-nf-note": "派生自 protocol/RECEIPTS.json；CID 可被 multiformats 生态直接校验。",
    }


def decision_surface(root: str = ".") -> Dict[str, Any]:
    """决策面（派生）：外部工具链能读到「本仓有哪些决策能力、按什么规则、模型拉取状态如何」。

    派生真源 = `protocol/decision_layer.json`（原语/适配器/候选/边界/workloop 契约）+
    `results/audit/*.md` 的 frontmatter（公开的决策与裁决**索引**：id/标题/日期/结论）。
    **不导出逐次工单**：工单与收口件留在内部档案（`STRATEGY §四` 计划内部消化），
    本面显式声明这一点（门禁判该声明必须在位），避免"看起来什么都导出了"的错觉。
    """
    import glob as _glob
    decl = _read_json(root, "protocol/decision_layer.json")
    audits = []
    for p in sorted(_glob.glob(os.path.join(root, "results", "audit", "*.md"))):
        try:
            with open(p, encoding="utf-8") as fh:
                head = fh.read(1200)
        except OSError:
            continue
        if not head.startswith("---"):
            continue
        block = head.split("---", 2)[1]
        rec: Dict[str, str] = {}
        for line in block.splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                rec[k.strip()] = v.strip()
        if rec.get("id"):
            audits.append({"id": rec.get("id"), "title": rec.get("title", ""),
                           "date": rec.get("date", ""), "verdict": rec.get("verdict", "")})
    return {
        "schema": "nf-decision-surface/1",
        "primitives": decl.get("primitives") or {},
        "responseContract": decl.get("response_contract") or {},
        "adapters": [{"id": a.get("id"), "kind": a.get("kind"),
                      "inGatePath": a.get("in_gate_path"),
                      "calibrated": a.get("calibrated")}
                     for a in (decl.get("adapters") or [])],
        "candidates": [{"id": c.get("id"), "source": c.get("source"),
                        "license": c.get("license"), "pulled": c.get("pulled"),
                        "evidence": str(c.get("evidence") or "")[:200],
                        "local": ({"runtime": (c.get("local") or {}).get("runtime"),
                                   "servedBy": (c.get("local") or {}).get("served_by")}
                                  if c.get("local") else None)}
                       for c in (decl.get("candidates") or [])],
        "boundaries": decl.get("boundaries") or [],
        "workloop": decl.get("workloop") or {},
        "publicDecisionIndex": audits,
        "x-nf-internal": "逐次工单（挑活/风险/收口）留在内部档案 .rivet/private_archive/work_orders/，"
                         "不随本面发布（STRATEGY §四 计划内部消化）；本面只投影**能力与公开裁决索引**。",
    }


def a2a_agent_card(root: str = ".") -> Dict[str, Any]:
    """A2A Agent Card（能力面投影）——skills 来自服务端点契约 + MCP 包声明，不新增真源。"""
    contract = _read_json(root, CONTRACT_REL)
    pkg = _read_json(root, "protocol/mcp_package.json")
    skills = []
    for ep in contract.get("endpoints") or []:
        skills.append({
            "id": str(ep.get("id") or ""),
            "name": str(ep.get("id") or ""),
            "description": "maps_to %s（%s %s）" % (ep.get("maps_to"), ep.get("method"),
                                                    ep.get("path")),
            "tags": ["narrativeforge", "content-contract"],
        })
    return {
        "protocolVersion": "0.2.5",
        "name": "NarrativeForge",
        "description": "内容契约层：装配 / 质检 / 图书馆 / 一致性报告（只读面）",
        "url": "urn:nf:repo",
        "preferredTransport": "stdio",
        "version": str(pkg.get("version") or "1.0.0"),
        "capabilities": {"streaming": any(e.get("streaming")
                                         for e in (contract.get("endpoints") or [])),
                         "pushNotifications": False},
        "defaultInputModes": ["text/plain", "application/json"],
        "defaultOutputModes": ["text/plain", "application/json"],
        "skills": skills,
        "x-nf-note": "能力面 = protocol/endpoint_contract.json 的投影；服务本体 status=%s"
                     "（未实装，本卡不据此宣称在线）" % contract.get("status", ""),
    }


KINDS = {
    "openapi": (openapi_doc, "OpenAPI 3.1 服务端点文档"),
    "asyncapi": (asyncapi_doc, "AsyncAPI 3.0 事件通道文档（含 CloudEvents 属性）"),
    "intoto": (intoto_statement, "in-toto Statement v1（协议层回执）"),
    "sbom": (sbom_doc, "SPDX 2.3 SBOM（依赖登记面）"),
    "slsa": (slsa_provenance, "SLSA Provenance v1（本地门禁构建声明）"),
    "a2a": (a2a_agent_card, "A2A Agent Card（能力面投影）"),
    "prov": (prov_document, "PROV-O 溯源图（资产 / 馆藏 / 消化 / 回执）"),
    "cyclonedx": (cyclonedx_doc, "CycloneDX 1.5 SBOM（与 SPDX 面同源）"),
    "vc": (vc_document, "W3C VC 2.0 形状（未签名，含状态注记）"),
    "c2pa": (c2pa_manifest, "C2PA JSON 清单形状（未封装/未签名）"),
    "cid": (cid_index, "CIDv1 内容寻址索引（multiformats）"),
    "decisions": (decision_surface, "决策面（决策能力 + 公开裁决索引；工单不入公开面）"),
}


def render(kind: str, root: str = ".") -> bytes:
    """确定性渲染（排序键 + UTF-8 + LF 尾）——两次调用逐字节一致。"""
    fn, _label = KINDS[kind]
    return (json.dumps(fn(root), ensure_ascii=False, indent=2, sort_keys=True)
            + "\n").encode("utf-8")


def verify(root: str = ".") -> Tuple[List[str], Dict[str, Any]]:
    """门禁：覆盖完整 + 形状合法 + 确定性（派生面不许漂移）。"""
    issues: List[str] = []
    contract = _read_json(root, CONTRACT_REL)
    reg = _read_json(root, EVENTS_REL)
    ext = _read_json(root, EXTERNAL_EVENTS_REL)
    rec = _read_json(root, RECEIPTS_REL)
    # fail-closed：真源缺失 = 派生面无从校验（不是"空导出面"，是"没有可导出的东西"）
    for rel in (CONTRACT_REL, EVENTS_REL, RECEIPTS_REL):
        if not os.path.isfile(os.path.join(root, rel)):
            issues.append("缺派生真源 %s（修复指引：先落声明件——导出面只做纯派生，"
                          "不自造真源）" % rel)

    oa = openapi_doc(root)
    want_paths = {str(e.get("path")) for e in (contract.get("endpoints") or [])}
    got_paths = set(oa.get("paths") or {})
    if got_paths != want_paths:
        issues.append("OpenAPI 派生面与服务端点契约不一致：缺 %s / 多 %s"
                      % (sorted(want_paths - got_paths), sorted(got_paths - want_paths)))
    for path, ops in (oa.get("paths") or {}).items():
        for method, op in ops.items():
            if not op.get("operationId"):
                issues.append("OpenAPI %s %s 缺 operationId（修复指引：端点 id 必填）"
                              % (method.upper(), path))
            if "200" not in (op.get("responses") or {}):
                issues.append("OpenAPI %s %s 缺 200 响应（修复指引：每端点须声明成功形状）"
                              % (method.upper(), path))
    if "NfError" not in (oa.get("components") or {}).get("schemas", {}):
        issues.append("OpenAPI 缺 NfError 错误形状（修复指引：错误面须可机读）")
    if not (oa.get("x-nf-error-mapping") or {}).get("title"):
        issues.append("OpenAPI 缺 RFC 9457 字段映射（修复指引：声明 error.message ↔ title/detail）")

    aa = asyncapi_doc(root)
    want_events = set((reg.get("events") or {}).keys()) | set((ext.get("events") or {}).keys())
    got_events = {k.split("/", 1)[1] for k in (aa.get("channels") or {})}
    if got_events != want_events:
        issues.append("AsyncAPI 派生面与事件登记不一致：缺 %s / 多 %s"
                      % (sorted(want_events - got_events), sorted(got_events - want_events)))
    ce_types = [(c.get("x-nf-cloudevents") or {}).get("type")
                for c in (aa.get("channels") or {}).values()]
    if len(set(ce_types)) != len(ce_types):
        issues.append("CloudEvents type 派生重复（修复指引：事件名须全库唯一，"
                      "见 01 §1.1 事件名唯一 + 词法纪律）")

    st = intoto_statement(root)
    want_subjects = {str(e.get("path")) for e in (rec.get("entries") or [])}
    got_subjects = {s.get("name") for s in st.get("subject") or []}
    if got_subjects != want_subjects:
        issues.append("in-toto subject 与协议层回执不一致：缺 %d / 多 %d"
                      % (len(want_subjects - got_subjects),
                         len(got_subjects - want_subjects)))
    for s in st.get("subject") or []:
        d = (s.get("digest") or {}).get("sha256", "")
        if not re.fullmatch(r"[0-9a-f]{64}", str(d)):
            issues.append("in-toto subject 缺合规 sha256：%s"
                          "（修复指引：回执 digest 须 64 位小写十六进制）" % s.get("name"))
    if st.get("_type") != "https://in-toto.io/Statement/v1":
        issues.append("in-toto Statement 类型头不合法（修复指引：_type 须为 Statement/v1）")

    sb = sbom_doc(root)
    ids = [p.get("SPDXID") for p in sb.get("packages") or []]
    if len(set(ids)) != len(ids):
        issues.append("SBOM 包 SPDXID 重复（修复指引：每依赖一个唯一 SPDXID）")
    if not any(p.get("name") == "NarrativeForge" for p in sb.get("packages") or []):
        issues.append("SBOM 缺本项目包（修复指引：SBOM 须自述本仓）")
    rels = sb.get("relationships") or []
    if not [r for r in rels if r.get("relationshipType") == "DESCRIBES"]:
        issues.append("SBOM 缺 DESCRIBES 关系（修复指引：文档须描述本仓包）")
    created = ((sb.get("creationInfo") or {}).get("created") or "")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", str(created)):
        issues.append("SBOM 的 creationInfo.created 缺失或非 ISO 8601 UTC：%r"
                      "（修复指引：SPDX 2.3 要求必填；本仓取「仓内声明日期最大值」保确定性）"
                      % created)

    for kind in KINDS:
        if render(kind, root) != render(kind, root):
            issues.append("导出面不确定性：%s 两次渲染不一致"
                          "（修复指引：禁止引入时间戳/随机源）" % kind)
    # SLSA provenance：subject 须与回执同源；等级**不得**虚标（本地门禁 ≠ SLSA 认证）
    sl = slsa_provenance(root)
    if sl.get("predicateType") != "https://slsa.dev/provenance/v1":
        issues.append("SLSA 派生面 predicateType 不合法（修复指引：须为 slsa.dev/provenance/v1）")
    if len(sl.get("subject") or []) != len(rec.get("entries") or []):
        issues.append("SLSA 派生面 subject 数与回执不一致：%d vs %d"
                      % (len(sl.get("subject") or []), len(rec.get("entries") or [])))
    note = ((sl.get("predicate") or {}).get("runDetails") or {}).get("metadata", {}).get("note", "")
    if "不构成 SLSA 等级声明" not in note:
        issues.append("SLSA 派生面缺「不作等级声明」注记（修复指引：本地门禁不得虚标 SLSA 等级）")
    declared = ((sl.get("predicate") or {}).get("buildDefinition") or {}).get(
        "externalParameters", {}).get("declaredBaseline", "")
    m_base = re.match(r"^check1-(\d+) PASS=(\d+)$", str(declared))
    if not m_base or int(m_base.group(1)) == 0 or int(m_base.group(2)) == 0:
        issues.append("SLSA 派生面基线句非法或为 0：%r（修复指引：基线取自 "
                      "core.quality_baseline 期望值——写 0 等于虚报门禁口径）" % declared)
    else:
        try:
            import sys as _s
            _s.path.insert(0, os.path.join(root, "desktop", "src"))
            from core import quality_baseline as _qb
            if (int(m_base.group(1)), int(m_base.group(2))) != (_qb.EXPECTED_CHECKS,
                                                               _qb.EXPECTED_PASS):
                issues.append("SLSA 派生面基线句与 quality_baseline 期望值不一致：%s"
                              "（修复指引：两处须同源）" % declared)
        except Exception:  # pragma: no cover
            pass
    # A2A Agent Card：skills 须覆盖端点契约；未实装须显式声明
    card = a2a_agent_card(root)
    if len(card.get("skills") or []) != len(contract.get("endpoints") or []):
        issues.append("A2A 卡片 skills 数与端点契约不一致（修复指引：卡片能力面须与契约同源）")
    if contract.get("status") != "implemented" and "未实装" not in str(card.get("x-nf-note")):
        issues.append("A2A 卡片未声明「服务未实装」（修复指引：不得据此宣称在线能力）")
    for sk in card.get("skills") or []:
        if not sk.get("id") or not sk.get("description"):
            issues.append("A2A 卡片 skill 缺 id/description（修复指引：能力面须自述）")
    # PROV-O 溯源图：节点 id 唯一 + 关系指向在册节点 + 资产实体全覆盖
    pv = prov_document(root)
    pv_ids = [n.get("@id") for n in pv.get("@graph") or []]
    if len(set(pv_ids)) != len(pv_ids):
        issues.append("PROV 图存在重复节点 id（修复指引：实体/活动/代理同一 id 只出现一次）")
    known = set(pv_ids)
    for n in pv.get("@graph") or []:
        for rel in ("prov:used", "prov:generated", "prov:wasAssociatedWith"):
            target = n.get(rel)
            if target and str(target) not in known:
                issues.append("PROV 图关系 %s 指向不在册节点：%s"
                              "（修复指引：被引用节点须在图内）" % (rel, target))
    prov_src = _read_json(root, "05_资产库/provenance.json")
    want_assets = {"nf:asset/%s" % a.get("key") for a in prov_src.get("assets") or []}
    if not want_assets.issubset(known):
        issues.append("PROV 图缺资产实体：%s（修复指引：资产台账每条须有实体节点）"
                      % sorted(want_assets - known))
    if "prov:Entity" not in {n.get("@type") for n in pv.get("@graph") or []}:
        issues.append("PROV 图无实体节点（修复指引：溯源图至少一个被证对象）")

    # CycloneDX：格式头 + 组件 bom-ref 唯一 + 与 SPDX 面同源（依赖集合一致）
    cdx = cyclonedx_doc(root)
    if cdx.get("bomFormat") != "CycloneDX" or str(cdx.get("specVersion")) != "1.5":
        issues.append("CycloneDX 头非法：%r/%r（修复指引：bomFormat=CycloneDX、specVersion=1.5）"
                      % (cdx.get("bomFormat"), cdx.get("specVersion")))
    refs = [c.get("bom-ref") for c in cdx.get("components") or []]
    if len(set(refs)) != len(refs):
        issues.append("CycloneDX 组件 bom-ref 重复（修复指引：每依赖一个唯一 bom-ref）")
    if not re.match(r"^urn:uuid:[0-9a-f-]{36}$", str(cdx.get("serialNumber") or "")):
        issues.append("CycloneDX serialNumber 非 urn:uuid 形态：%r"
                      "（修复指引：由声明摘要派生，勿用随机 UUID）" % cdx.get("serialNumber"))
    hard = {c.get("name") for c in cdx.get("components") or [] if c.get("scope") == "required"}
    try:
        import sys as _s2
        _s2.path.insert(0, os.path.join(root, "desktop", "src"))
        from core import purity_scan as _ps
        want_hard = set(_ps.HARD_ALLOW)
    except Exception:  # pragma: no cover - 登记面不可读即跳过该断言
        want_hard = set()
    if want_hard and hard != want_hard:
        issues.append("CycloneDX 硬依赖集与登记面不一致：%s（期望 %s）"
                      "（修复指引：两形同源——都读 purity_scan 登记面）"
                      % (sorted(hard), sorted(want_hard)))

    # VC：VC 2.0 上下文 + 必备字段 + 未签名状态注记
    vc = vc_document(root)
    if "https://www.w3.org/ns/credentials/v2" not in (vc.get("@context") or []):
        issues.append("VC 缺 v2 上下文（修复指引：@context 须含 "
                      "https://www.w3.org/ns/credentials/v2）")
    if "VerifiableCredential" not in (vc.get("type") or []):
        issues.append("VC type 缺 VerifiableCredential")
    if not vc.get("issuer") or not re.fullmatch(r"\d{4}-\d{2}-\d{2}",
                                                str(vc.get("validFrom") or "")):
        issues.append("VC 缺 issuer 或 validFrom（修复指引：自 protocol/approvals/* 取批准人与批准日）")
    subj = vc.get("credentialSubject") or {}
    if not re.fullmatch(r"[0-9a-f]{64}", str(subj.get("receiptRoot") or "")):
        issues.append("VC credentialSubject.receiptRoot 非 sha256：%r"
                      "（修复指引：凭证须绑定内容摘要）" % subj.get("receiptRoot"))
    if "proof" not in vc and "unsigned" not in str(vc.get("x-nf-proof-status") or ""):
        issues.append("VC 无 proof 却未声明未签名状态（修复指引：x-nf-proof-status 须写明"
                      "——形状可读 ≠ 可验证）")

    # C2PA：claim_generator + hash.data 硬绑定 + 未封装状态注记
    c2 = c2pa_manifest(root)
    if not str(c2.get("claim_generator") or "").startswith("NarrativeForge"):
        issues.append("C2PA 缺 claim_generator（修复指引：须自述生成器）")
    labels = {a.get("label") for a in c2.get("assertions") or []}
    if "c2pa.hash.data" not in labels or "c2pa.actions" not in labels:
        issues.append("C2PA 断言面不全（修复指引：须含 c2pa.hash.data 与 c2pa.actions）：%s"
                      % sorted(labels))
    hd = next((a.get("data") or {} for a in c2.get("assertions") or []
               if a.get("label") == "c2pa.hash.data"), {})
    if not re.fullmatch(r"[0-9a-f]{64}", str(hd.get("hash") or "")):
        issues.append("C2PA hash.data 非 sha256（修复指引：硬绑定摘要须 64 位小写十六进制）")
    if "未封装" not in str(c2.get("x-nf-package-status") or ""):
        issues.append("C2PA 未声明封装/签名状态（修复指引：JSON 清单 ≠ 生产级 C2PA 包）")

    # CID：条目数与回执一致 + 形态合法（b + base32）
    ci = cid_index(root)
    if len(ci.get("entries") or []) != len(rec.get("entries") or []):
        issues.append("CID 索引条目数与回执不一致：%d vs %d"
                      % (len(ci.get("entries") or []), len(rec.get("entries") or [])))
    for e in ci.get("entries") or []:
        if not re.fullmatch(r"b[a-z2-7]{50,}", str(e.get("cid") or "")):
            issues.append("CID 形态非法：%s（修复指引：CIDv1 multibase base32 小写，"
                          "前缀 b + raw codec 0x71 + sha2-256 multihash）" % e.get("path"))
            break

    # 决策面：适配器/候选全覆盖 + 「工单不入公开面」声明在位（防"看起来什么都导出了"）
    ds = decision_surface(root)
    decl_dl = _read_json(root, "protocol/decision_layer.json")
    if len(ds.get("adapters") or []) != len(decl_dl.get("adapters") or []):
        issues.append("决策面适配器数与声明不一致：%d vs %d"
                      % (len(ds.get("adapters") or []), len(decl_dl.get("adapters") or [])))
    if len(ds.get("candidates") or []) != len(decl_dl.get("candidates") or []):
        issues.append("决策面候选数与声明不一致：%d vs %d"
                      % (len(ds.get("candidates") or []), len(decl_dl.get("candidates") or [])))
    if "不随本面发布" not in str(ds.get("x-nf-internal") or ""):
        issues.append("决策面缺「工单不入公开面」声明（修复指引：写明内部档案边界，"
                      "不得让外部以为逐次决策已公开）")
    if not (ds.get("publicDecisionIndex") or []):
        issues.append("决策面缺公开裁决索引（修复指引：results/audit/*.md 的 frontmatter 可派生）")

    stats = {"openapi_paths": len(oa.get("paths") or {}),
             "asyncapi_channels": len(aa.get("channels") or {}),
             "intoto_subjects": len(st.get("subject") or []),
             "sbom_packages": len(sb.get("packages") or []),
             "slsa_subjects": len(sl.get("subject") or []),
             "a2a_skills": len(card.get("skills") or []),
             "prov_nodes": len(pv.get("@graph") or []),
             "prov_counts": pv.get("x-nf-counts") or {},
             "cyclonedx_components": len(cdx.get("components") or []),
             "vc_type": (vc.get("type") or [""])[0],
             "c2pa_assertions": len(c2.get("assertions") or []),
             "cid_entries": len(ci.get("entries") or []),
             "decision_adapters": len(ds.get("adapters") or []),
             "decision_candidates": len(ds.get("candidates") or []),
             "decision_audits": len(ds.get("publicDecisionIndex") or []),
             "issues": len(issues)}
    return issues, stats


def summary(stats: Dict[str, Any]) -> str:
    return ("OpenAPI 路径 %(openapi_paths)d / AsyncAPI 通道 %(asyncapi_channels)d / "
            "in-toto subject %(intoto_subjects)d / SBOM 包 %(sbom_packages)d / "
            "SLSA subject %(slsa_subjects)d / A2A skills %(a2a_skills)d / "
            "PROV 节点 %(prov_nodes)d / 决策面 适配器 %(decision_adapters)d"
            "（裁决索引 %(decision_audits)d）" % stats)
