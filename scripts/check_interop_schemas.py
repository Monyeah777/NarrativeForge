#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""互操作导出面的**外部权威校验**（非门禁 · 可选联网 · 只读）。

定位（与 `check_external_links.py` 同纪律）：NF 的门禁必须静态可复现，因此「派生面是否
真的符合外部标准」**不进 verify 基线**；本脚本把这件事做成独立任务——`--fetch` 才联网，
拉官方 meta-schema 用 `jsonschema` 校验 `nf interop` 的派生面，`--write` 才落报告。

为什么要这层：`core/interop_export.py` 的门禁只判「覆盖完整 + 形状合法（自述）」——
**自述不是标准**。这一步把「我们按 OpenAPI 3.1 / AsyncAPI 3.0 / in-toto / SPDX 写」
变成「**官方 meta-schema 说合法**」，失败同样记档（失败比自证更值钱）。

用法（仓库根目录）：
  python scripts/check_interop_schemas.py                 # 只列要校验的面与目标 schema
  python scripts/check_interop_schemas.py --fetch         # 联网取 schema 并校验
  python scripts/check_interop_schemas.py --fetch --write results/interop-schema-validation.md
退出码：0 = 全部通过（或未校验）；1 = 存在校验失败；2 = 用法错误（禁写 protocol/）。
纪律：零第三方硬依赖（`jsonschema` 缺失即跳过并如实说明）；不写仓库受管区（除 --write 指定）。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Dict, Sequence, Tuple

#: 派生面 → (主 URL, GitHub 兜底 (owner/repo, path, ref))；raw 取不到时走 contents API
SCHEMAS: Dict[str, tuple] = {
    "openapi": ("https://spec.openapis.org/oas/3.1/schema/2022-10-07", None),
    "asyncapi": ("https://raw.githubusercontent.com/asyncapi/spec-json-schemas/"
                 "master/schemas/3.0.0.json",
                 ("asyncapi/spec-json-schemas", "schemas/3.0.0.json", "master")),
    "slsa": ("https://raw.githubusercontent.com/slsa-framework/slsa/"
             "main/docs/specs/provenance/v1.0/schema.json",
             ("slsa-framework/slsa", "docs/specs/provenance/v1.0/schema.json", "main")),
    "intoto": ("https://raw.githubusercontent.com/in-toto/attestation/"
               "main/spec/v1/statement.schema.json",
               ("in-toto/attestation", "spec/v1/statement.schema.json", "main")),
    "sbom": ("https://raw.githubusercontent.com/spdx/spdx-spec/"
             "develop/schemas/spdx-schema-2-3.json",
             ("spdx/spdx-spec", "schemas/spdx-schema-2-3.json", "develop")),
    "prov": ("https://www.w3.org/ns/prov.jsonld", None),
    "cyclonedx": ("https://raw.githubusercontent.com/CycloneDX/specification/"
                  "master/schema/bom-1.5.schema.json",
                  ("CycloneDX/specification", "schema/bom-1.5.schema.json", "master")),
}

#: 无 JSON Schema 可校验的面（官方以其它形态发布规范）——如实记档，不假装校验过
NOSCHEMA: Dict[str, str] = {
    "slsa": ("SLSA v1 官方以 CUE / Protobuf 定义机器可读协议"
             "（slsa-framework/slsa: spec/schema/provenance.cue + provenance.proto），"
             "无官方 JSON Schema —— 本机无 CUE 工具链，故不做 schema 校验"),
    "intoto": ("in-toto Statement v1 官方以 Markdown 规范发布"
               "（in-toto/attestation: spec/v1/statement.md），该目录无 JSON Schema"),
    "a2a": ("A2A 官方仓以 .proto + 文档为主"
            "（a2aproject/A2A: specification/a2a.proto；specification/json 下仅 README），"
            "无官方 JSON Schema 可供本机校验"),
    "vc": ("W3C VC Data Model 2.0 以规范文本 + JSON-LD 上下文发布"
           "（w3c/vc-data-model: 规范正文；无官方 JSON Schema 收口凭证形状）"),
    "c2pa": ("C2PA 规范以 CBOR/JUMBF 容器 + JSON 清单表示定义"
             "（contentauth/c2pa-rs 等实现仓；官方无独立 JSON Schema 文件），"
             "且本仓**不做容器封装**，故只做自校验"),
    "cid": ("CID 由 multiformats 规范定义（multiformats/cid + multicodec 表），"
            "无 JSON Schema；本仓以**已知向量**校验（sha256(\"\") 的 CIDv1 raw）"),
    "decisions": ("决策面是 **NF 自有形状**（决策能力 + 公开裁决索引），非外部标准；"
                  "无官方 JSON Schema 可对，判据落在本仓 check33"
                  "（覆盖一致 / 内部边界声明 / 确定性）"),
}


def fetch(url: str, timeout: int = 25) -> Tuple[int, bytes]:
    req = urllib.request.Request(url, headers={"User-Agent": "nf-interop-schema/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return int(getattr(resp, "status", 200)), resp.read()
    except urllib.error.HTTPError as exc:
        return exc.code, b""
    except Exception:  # noqa: BLE001 - 网络类异常如实计为取不到
        return 0, b""


def fetch_via_api(repo: str, path: str, ref: str, timeout: int = 25) -> Tuple[int, bytes]:
    """raw.githubusercontent 不可达时的兜底：contents API 取原始字节（raw media type）。"""
    req = urllib.request.Request(
        "https://api.github.com/repos/%s/contents/%s?ref=%s" % (repo, path, ref),
        headers={"User-Agent": "nf-interop-schema/1.0",
                 "Accept": "application/vnd.github.raw"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return int(getattr(resp, "status", 200)), resp.read()
    except urllib.error.HTTPError as exc:
        return exc.code, b""
    except Exception:  # noqa: BLE001
        return 0, b""


def _validator_for(schema: dict, js):
    """按 schema 自述的 $schema 选 validator 类（draft-07 / 2020-12 / 默认 2020-12）。"""
    dialect = str(schema.get("$schema") or "")
    if "draft-07" in dialect:
        return js.Draft7Validator
    if "2019-09" in dialect:
        return js.Draft201909Validator
    return js.Draft202012Validator


def validate_one(kind: str, spec: tuple, doc: dict, validator=None) -> Dict[str, object]:
    """单面校验 → 结果行（status ∈ ok / fail / unavailable / skipped）。"""
    schema_url, fallback = spec
    row: Dict[str, object] = {"kind": kind, "schema": schema_url}
    if kind in NOSCHEMA:
        row["status"] = "no-schema"
        row["schema_http"] = "-"
        row["detail"] = NOSCHEMA[kind]
        return row
    st, blob = fetch(schema_url)
    if (st != 200 or not blob) and fallback:
        st, blob = fetch_via_api(*fallback)
        if st == 200 and blob:
            row["schema"] = "github-contents:%s/%s@%s" % fallback
            row["schema_fallback"] = True
    row["schema_http"] = st
    if st != 200 or not blob:
        row["status"] = "unavailable"
        row["detail"] = "schema 取不到（网络/地址问题，非派生面问题）"
        return row
    try:
        schema = json.loads(blob)
    except json.JSONDecodeError:
        row["status"] = "unavailable"
        row["detail"] = "schema 非 JSON（可能取到 HTML 页）"
        return row
    if kind == "prov":
        row["status"] = "ok"
        row["detail"] = "PROV-O 上下文可取（JSON-LD context 形态；不做 schema 校验）"
        return row
    if validator is None:
        row["status"] = "skipped"
        row["detail"] = "jsonschema 不可用（软依赖缺失）——如实跳过"
        return row
    cls = _validator_for(schema, validator)
    try:
        cls.check_schema(schema)
    except Exception as exc:  # noqa: BLE001
        row["status"] = "skipped"
        row["detail"] = "schema 本身无法被本机 validator 装载：%s" % str(exc)[:90]
        return row
    try:
        errs = sorted(cls(schema).iter_errors(doc), key=lambda e: list(e.path))[:5]
    except Exception as exc:  # noqa: BLE001 - 远程 $ref 无法解析等
        row["status"] = "skipped"
        row["detail"] = ("schema 含需联网解析的远程 $ref 或本机无法装载：%s"
                         % str(exc)[:110])
        return row
    if errs:
        row["status"] = "fail"
        row["error_count"] = len(errs)
        row["detail"] = "；".join(
            "/%s: %s" % ("/".join(str(p) for p in e.path) or "(root)", e.message[:90])
            for e in errs)
        return row
    row["status"] = "ok"
    row["detail"] = "官方 meta-schema 校验通过"
    return row


#: 出口面外部核验（非 JSON Schema 类）：目标平台自身的源码字面量 / 结构要求
export_checks_doc = """\
出口面外部核验（E1）：把本仓 CCV3 样本与 SillyTavern 写卡源码的字面量对齐——\
它写什么 spec/spec_version，我们的样本就必须是什么，且 v3 内容字段须在 `data` 内。"""


def check_st_ccv3(root: str) -> Dict[str, object]:
    """E1 出口面核验：CCV3 样本 ⇄ SillyTavern 写卡源码（spec / spec_version / data 结构）。"""
    row: Dict[str, object] = {"kind": "ccv3(E1)", "schema": "SillyTavern 源码字面量"}
    path = Path(root) / "docs" / "external-validation-assets" / \
        "E1_ccv3_sample_lightmix_P04_chara.json"
    if not path.is_file():
        row.update({"status": "unavailable", "detail": "缺样本件：%s" % path.name})
        return row
    st, blob = fetch("https://raw.githubusercontent.com/SillyTavern/SillyTavern/"
                     "release/src/character-card-parser.js")
    if st != 200 or not blob:
        st, blob = fetch_via_api("SillyTavern/SillyTavern",
                                 "src/character-card-parser.js", "release")
    row["schema_http"] = st
    if st != 200 or not blob:
        row.update({"status": "unavailable",
                    "detail": "写卡源码取不到（网络/地址问题，非出口面问题）"})
        return row
    src = blob.decode("utf-8", "replace")
    want_spec = re.search(r"spec\s*=\s*['\"]([^'\"]+)['\"]", src)
    want_ver = re.search(r"spec_version\s*=\s*['\"]([^'\"]+)['\"]", src)
    if not want_spec or not want_ver:
        row.update({"status": "unavailable",
                    "detail": "源码里未找到 spec/spec_version 赋值（上游已改写法，须人工复核）"})
        return row
    doc = json.loads(path.read_text(encoding="utf-8"))
    problems = []
    if doc.get("spec") != want_spec.group(1):
        problems.append("spec %r ≠ 上游 %r" % (doc.get("spec"), want_spec.group(1)))
    if str(doc.get("spec_version")) != want_ver.group(1):
        problems.append("spec_version %r ≠ 上游 %r"
                        % (doc.get("spec_version"), want_ver.group(1)))
    if not isinstance(doc.get("data"), dict):
        problems.append("缺 data 块（v3 内容字段须在 data 内）")
    elif not isinstance((doc["data"] or {}).get("character_book"), dict):
        problems.append("data.character_book 缺失")
    row["status"] = "fail" if problems else "ok"
    row["detail"] = ("；".join(problems) if problems
                     else "与上游字面量一致（spec=%s / spec_version=%s / data 结构在位）"
                          % (want_spec.group(1), want_ver.group(1)))
    return row


#: MCP 官方 schema（modelcontextprotocol/modelcontextprotocol: schema/<版本>/schema.json）
MCP_SCHEMA_URL = ("https://raw.githubusercontent.com/modelcontextprotocol/"
                  "modelcontextprotocol/main/schema/2026-07-28/schema.json")
MCP_SCHEMA_FALLBACK = ("modelcontextprotocol/modelcontextprotocol",
                       "schema/2026-07-28/schema.json", "main")
#: 本仓运行时实际会应答的方法 → 官方 $defs 里的响应定义名
MCP_FACES = (("server/discover", "DiscoverResultResponse"),
             ("resources/list", "ListResourcesResultResponse"),
             ("tools/list", "ListToolsResultResponse"),
             ("prompts/list", "ListPromptsResultResponse"))


def check_mcp_session(root: str, js=None) -> Dict[str, object]:
    """E3 核验：本仓 `nf serve` 的实际应答 ⇄ MCP 官方 schema 的 $defs 定义。"""
    row: Dict[str, object] = {"kind": "mcp(E3)", "schema": MCP_SCHEMA_URL}
    st, blob = fetch(MCP_SCHEMA_URL)
    if st != 200 or not blob:
        st, blob = fetch_via_api(*MCP_SCHEMA_FALLBACK)
        if st == 200:
            row["schema"] = "github-contents:%s/%s@%s" % MCP_SCHEMA_FALLBACK
    row["schema_http"] = st
    if st != 200 or not blob or js is None:
        row.update({"status": "unavailable" if js is None or st != 200 else "skipped",
                    "detail": ("本机缺 jsonschema（软依赖）" if js is None
                               else "官方 schema 取不到（网络/地址问题）")})
        return row
    try:
        schema = json.loads(blob)
        defs = schema.get("$defs") or {}
    except json.JSONDecodeError:
        row.update({"status": "unavailable", "detail": "schema 非 JSON"})
        return row
    sys.path.insert(0, str(Path(root) / "desktop" / "src"))
    try:
        from core import mcp_runtime as mcp
    except Exception as exc:  # noqa: BLE001
        row.update({"status": "skipped", "detail": "本仓运行时不可导入：%s" % exc})
        return row
    srv = mcp.McpRuntime({"mcp": {"name": "nf-schema-check", "version": "1.0.0",
                                  "resources": []}})
    problems, checked = [], 0
    for method, def_name in MCP_FACES:
        if def_name not in defs:
            problems.append("%s：官方 schema 无 %s（上游改版须人工复核）" % (method, def_name))
            continue
        resp = srv.handle({"jsonrpc": "2.0", "id": 1, "method": method,
                           "params": {"_meta": {"io.modelcontextprotocol/"
                                                 "protocolVersion": "2026-07-28"}}})
        if not isinstance(resp, dict) or "result" not in resp:
            problems.append("%s：本仓未返回 result（%s）" % (method, str(resp)[:80]))
            continue
        checked += 1
        try:
            validator = js.Draft202012Validator(
                {"$ref": "#/$defs/%s" % def_name, "$defs": defs})
            errs = sorted(validator.iter_errors(resp), key=lambda e: list(e.path))[:3]
        except Exception as exc:  # noqa: BLE001
            problems.append("%s：schema 装载失败 %s" % (method, str(exc)[:70]))
            continue
        for e in errs:
            problems.append("%s /%s: %s" % (method, "/".join(str(p) for p in e.path) or "(root)",
                                            e.message[:110]))
    row["checked"] = checked
    row["status"] = "fail" if problems else "ok"
    row["detail"] = ("；".join(problems) if problems
                     else "%d 个方法应答通过官方 schema（%s）"
                          % (checked, " / ".join(m for m, _ in MCP_FACES)))
    return row


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="互操作导出面外部权威校验（非门禁）")
    ap.add_argument("--root", default=".", help="仓库根（缺省当前目录）")
    ap.add_argument("--fetch", action="store_true", help="联网取官方 schema（默认关闭）")
    ap.add_argument("--write", default="", help="报告写入路径（不得写入 protocol/）")
    ap.add_argument("--json", action="store_true", help="输出结构化 JSON")
    args = ap.parse_args(argv)
    if args.write and args.write.replace("\\", "/").startswith("protocol/"):
        print("  ✗ 报告不得写入协议层 protocol/（修复指引：写 results/ 或 docs/）",
              file=sys.stderr)
        return 2

    sys.path.insert(0, str(Path(args.root) / "desktop" / "src"))
    try:
        from core import interop_export as ie
    except Exception as exc:  # noqa: BLE001
        print("  ✗ 无法导入 interop_export：%s（修复指引：在仓库根运行）" % exc, file=sys.stderr)
        return 2
    try:
        import jsonschema as validator
    except Exception:  # noqa: BLE001
        validator = None

    if not args.fetch:
        print("== 互操作导出面 · 外部权威校验（模式：只列目标，未联网）==")
        listing = dict(SCHEMAS)
        for kind in NOSCHEMA:
            listing.setdefault(kind, (NOSCHEMA[kind], None))
        for kind, spec in listing.items():
            print("  %-9s ← %s" % (kind, spec[0]))
        print("  加 --fetch 才联网校验；jsonschema 可用：%s" % ("是" if validator else "否（跳过校验）"))
        return 0

    docs = {k: json.loads(ie.render(k, args.root)) for k in ie.KINDS}
    # 逐面校验：SCHEMAS 表 + 官方无 schema 的面（no-schema 也要出现在报告里）
    all_specs = dict(SCHEMAS)
    for kind in NOSCHEMA:
        all_specs.setdefault(kind, (NOSCHEMA[kind], None))
    rows = [validate_one(kind, spec, docs.get(kind, {}), validator)
            for kind, spec in all_specs.items()]
    rows.append(check_st_ccv3(args.root))     # 出口面核验（E1）
    rows.append(check_mcp_session(args.root, validator))   # 会话面核验（E3）
    failed = [r for r in rows if r["status"] == "fail"]
    if args.json:
        print(json.dumps({"schema": "nf-interop-schema-check/1", "rows": rows},
                         ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print("== 互操作导出面 · 外部权威校验 ==")
        for r in rows:
            print("  [%s] %-9s %s" % (str(r["status"]).upper(), r["kind"], r["detail"]))
        print("  合计 %d 面 / 失败 %d 面" % (len(rows), len(failed)))
    if args.write:
        out = Path(args.root) / args.write
        out.parent.mkdir(parents=True, exist_ok=True)
        lines = ["# 互操作导出面 · 外部权威校验报告", "",
                 "> 由 `scripts/check_interop_schemas.py --fetch` 生成（非门禁；联网取证）。", "",
                 "| 面 | 官方 schema | HTTP | 结果 | 说明 |", "|---|---|---|---|---|"]
        for r in rows:
            lines.append("| %s | %s | %s | %s | %s |"
                         % (r["kind"], r["schema"], r.get("schema_http"), r["status"],
                            str(r["detail"]).replace("|", "/")))
        lines += ["", "> 口径：`unavailable` = schema 取不到（网络/地址问题，不判派生面不合格）；",
                  "> `skipped` = 本机缺 validator；`fail` = 官方 schema 判定派生面不合规（须修派生面）。", ""]
        out.write_text("\n".join(lines), encoding="utf-8", newline="\n")
        print("  报告已写入：%s" % args.write)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
