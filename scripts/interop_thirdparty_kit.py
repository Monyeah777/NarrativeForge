#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""互操作性「从他证」通道套件（check38 子扫描 2）。

分层纪律（不混淆两种证据）：
- 第一层（已有）：`scripts/check_interop_schemas.py --fetch` 用**上游官方 meta-schema** 校验导出面
  → 属「上游判据校验」，落 `results/interop-schema-validation.md`。
- 第二层（本套件）：**对端消费 / 官方验证器**由第三方在自己环境跑，把结果回填
  → 属「他证」。本仓**只建通道，不伪造第三方证据**：未回填一律记「通道就绪」。

用法：
  python scripts/interop_thirdparty_kit.py --emit      # 生成 docs/interop-thirdparty.md + 回填状态表
  python scripts/interop_thirdparty_kit.py --check     # 校验状态表完整性（每个面有行；已回填则六字段齐备）
  python scripts/interop_thirdparty_kit.py --dry-run   # 本机探测对端工具是否可得（不联网、不写盘）
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
from typing import Any, Dict, List, Tuple

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOC_REL = "docs/interop-thirdparty.md"
STATUS_REL = "results/interop-thirdparty-status.md"
UNFILLED = "未回填（通道就绪）"

# 每个面：id / 标题 / 产物 / 种类 / 对端 / 安装 / 命令 / 期望 / 说明 / 本机探测（模块名或可执行名）
FACES: List[Dict[str, Any]] = [
    {
        "id": "mcp", "title": "MCP 运行时（server/discover · tools/list）",
        "artifact": "", "kind": "peer-consumption",
        "peer": "任意 MCP 客户端（Claude Desktop / mcp-inspector 等）",
        "install": "对端自选；服务端：`python scripts/nf.py run --fmt mcp --dest out` 产出 mcp.json 快照",
        "command": "python scripts/nf.py serve out/mcp.json  然后由对端客户端调用 server/discover / tools/list / resources/list / prompts/list",
        "expect": "对端能完成初始化并取到 4 类列表；应答通过官方 MCP 2026-07-28 schema",
        "why": "", "probe": "core.mcp_runtime",
    },
    {
        "id": "ccv3", "title": "CCV3 角色卡（SillyTavern 侧消费）",
        "artifact": "docs/external-validation-assets/", "kind": "peer-consumption",
        "peer": "SillyTavern（或任何 CCV3 实现）",
        "install": "对端自装；样本卡见 docs/external-validation-assets/",
        "command": "在对端导入样本卡 → 启动 → 记录是否可读、是否报错、首回合输出",
        "expect": "导入不报错且角色卡字段被正确识别（spec=chara_card_v3 / spec_version=3.0）",
        "why": "", "probe": "",
    },
    {
        "id": "openapi", "title": "OpenAPI 3.1 导出面",
        "artifact": "results/interop/openapi.json", "kind": "official-cli",
        "peer": "openapi-spec-validator（官方生态校验器）",
        "install": "pip install openapi-spec-validator",
        "command": "python -m openapi_spec_validator results/interop/openapi.json",
        "expect": "退出码 0（无 ValidationError）", "why": "", "probe": "openapi_spec_validator",
    },
    {
        "id": "asyncapi", "title": "AsyncAPI 3.0 导出面",
        "artifact": "results/interop/asyncapi.json", "kind": "official-cli",
        "peer": "@asyncapi/cli（官方 CLI）",
        "install": "npm i -g @asyncapi/cli",
        "command": "asyncapi validate results/interop/asyncapi.json",
        "expect": "退出码 0，输出 “is valid”", "why": "", "probe": "asyncapi",
    },
    {
        "id": "sbom", "title": "SPDX 3.x SBOM 导出面",
        "artifact": "results/interop/sbom.json", "kind": "official-cli",
        "peer": "spdx-tools（SPDX 官方工具）",
        "install": "pip install spdx-tools",
        "command": "pyspdxtools -i results/interop/sbom.json",
        "expect": "退出码 0（解析通过）", "why": "", "probe": "spdx_tools",
    },
    {
        "id": "cyclonedx", "title": "CycloneDX 1.5 SBOM 导出面",
        "artifact": "results/interop/cyclonedx.json", "kind": "official-cli",
        "peer": "cyclonedx-cli（官方 CLI）",
        "install": "下载 cyclonedx-cli 发行版（GitHub Releases）",
        "command": "cyclonedx validate --input-file results/interop/cyclonedx.json",
        "expect": "BOM validated", "why": "", "probe": "cyclonedx",
    },
    {
        "id": "slsa", "title": "SLSA v1.0 来源面（形状）",
        "artifact": "results/interop/slsa.json", "kind": "shape-only",
        "peer": "slsa-verifier / CUE 工具链（官方）",
        "install": "go install github.com/slsa-framework/slsa-verifier/v2/cli/slsa-verifier@latest",
        "command": "slsa-verifier version  # 并对照官方 CUE/Protobuf 定义核对形状",
        "expect": "工具可得；形状与官方定义一致（本面**只证形状，不证构建来源**）",
        "why": "SLSA v1.0 官方以 CUE / Protobuf 定义机器可读协议，不发布 JSON Schema；NF 导出面是契约形状而非真实构建证明，故本面判据止于形状一致。",
        "probe": "slsa-verifier",
    },
    {
        "id": "intoto", "title": "in-toto Statement 面（形状）",
        "artifact": "results/interop/intoto.json", "kind": "shape-only",
        "peer": "in-toto（官方实现）",
        "install": "pip install in-toto",
        "command": "python -c \"import in_toto, json; s=json.load(open('results/interop/intoto.json',encoding='utf-8')); assert {'_type','subject','predicateType'} <= set(s)\"",
        "expect": "断言通过（Statement 必备键在位）",
        "why": "in-toto 官方以 Markdown 规范发布 Statement，不提供 JSON Schema 文件；本面判据为必备键形状 + 官方文本核对。",
        "probe": "in_toto",
    },
    {
        "id": "vc", "title": "W3C VC 2.0 凭证面（形状）",
        "artifact": "results/interop/vc.json", "kind": "shape-only",
        "peer": "W3C VC 数据模型校验库 / JSON-LD 处理器",
        "install": "pip install pyld",
        "command": "python -c \"import json; d=json.load(open('results/interop/vc.json',encoding='utf-8')); assert {'@context','type','credentialSubject'} <= set(d)\"",
        "expect": "断言通过（凭证必备键在位）",
        "why": "VC 2.0 以规范文本 + JSON-LD 上下文发布，无官方 JSON Schema；本面判据为必备键形状 + 上下文可取。",
        "probe": "pyld",
    },
    {
        "id": "prov", "title": "W3C PROV-O 溯源面（形状）",
        "artifact": "results/interop/prov.json", "kind": "shape-only",
        "peer": "PROV 工具链 / JSON-LD 处理器",
        "install": "pip install pyld",
        "command": "python -c \"import json; d=json.load(open('results/interop/prov.json',encoding='utf-8')); assert d\"",
        "expect": "断言通过；JSON-LD 上下文可解析",
        "why": "PROV-O 以本体 + 规范文本发布（官方 prov.jsonld 本轮实测 300/不可取），本面判据为形状 + 上下文解析。",
        "probe": "pyld",
    },
    {
        "id": "a2a", "title": "A2A Agent Card 面",
        "artifact": "results/interop/a2a.json", "kind": "not-applicable",
        "peer": "A2A 客户端（如官方 SDK）",
        "install": "对端自装",
        "command": "（本仓不提供 A2A 端点，无法对端消费）",
        "expect": "—",
        "why": "本仓只导出 Agent Card 形状、不运行 A2A 端点，故无法做对端消费；改由官方 .proto/文本核对形状（不判本面通过）。",
        "probe": "",
    },
    {
        "id": "c2pa", "title": "C2PA 内容凭证面",
        "artifact": "results/interop/c2pa.json", "kind": "not-applicable",
        "peer": "c2pa-rs（官方实现）",
        "install": "对端自装",
        "command": "（本仓不做 CBOR/JUMBF 容器封装）",
        "expect": "—",
        "why": "C2PA 以容器封装为真值载体；本仓只做清单形状，不做容器，故他证不适用（保留为形状面）。",
        "probe": "",
    },
    {
        "id": "cid", "title": "CID 已知向量面",
        "artifact": "results/interop/cid.json", "kind": "official-cli",
        "peer": "multiformats 参照实现 / 已知向量复算",
        "install": "无需安装（sha256 + base32 复算）",
        "command": "python scripts/interop_thirdparty_kit.py --dry-run   # 内含 CID 已知向量复算（sha256(\"\")）",
        "expect": "复算出的 CIDv1 与 results/interop/cid.json 记录一致",
        "why": "", "probe": "",
    },
    {
        "id": "decisions", "title": "决策面（NF 自有形状）",
        "artifact": "results/interop/decisions.json", "kind": "not-applicable",
        "peer": "—",
        "install": "—",
        "command": "—",
        "expect": "—",
        "why": "决策面是 NF 自有形状，无外部对端与外部 schema；判据落在 check33（覆盖一致 / 内部边界声明 / 确定性），不属他证范围。",
        "probe": "",
    },
]


def _root(root: str = "") -> str:
    return os.path.abspath(root or ROOT)


def _kcid_recompute(base: str) -> Tuple[bool, str]:
    """CID 已知向量复算（对端视角，两条不变量）：
    ① 回执摘要 == 文件实算 sha256（协议层回执 protocol/RECEIPTS.json 是否新鲜）；
    ② 记录 CID == CIDv1(codec 0x71 · sha2-256)（multiformats 编码是否正确）。
    """
    import base64
    import hashlib

    path = os.path.join(base, "results/interop/cid.json")
    try:
        with open(path, encoding="utf-8") as fh:
            doc = json.load(fh)
    except Exception as e:  # noqa: BLE001
        return False, "cid.json 不可读：%s" % e
    try:
        with open(os.path.join(base, "protocol/RECEIPTS.json"), encoding="utf-8") as fh:
            rec = json.load(fh)
    except Exception as e:  # noqa: BLE001
        return False, "protocol/RECEIPTS.json 不可读：%s（跑 `nf receipts --write` 重签）" % e
    digests = {str(e.get("path")): str(e.get("digest")) for e in (rec.get("entries") or [])}
    entries = doc.get("entries") or []
    if not entries:
        return False, "cid.json 无 entries（已知向量缺失）"
    stale, misencode, missing = [], [], []
    for e in entries:
        rel = str(e.get("path") or "")
        p = os.path.join(base, rel)
        if not os.path.isfile(p):
            missing.append(rel)
            continue
        with open(p, "rb") as fh:
            actual = hashlib.sha256(fh.read()).hexdigest()
        if digests.get(rel) != actual:
            stale.append(rel)
        mh = bytes([0x12, 0x20]) + bytes.fromhex(digests.get(rel) or actual)
        cid = "b" + base64.b32encode(bytes([0x01, 0x71]) + mh).decode("ascii").lower().rstrip("=")
        if cid != e.get("cid"):
            misencode.append(rel)
    ok = not stale and not misencode and not missing
    detail = "向量 %d 条：摘要过期 %d · 编码不符 %d · 缺文件 %d" % (
        len(entries), len(stale), len(misencode), len(missing))
    if stale:
        detail += "（过期样例：%s；修复指引：nf receipts --write 重签并刷新派生面）" % stale[:3]
    return ok, detail


def dry_run(base: str = "") -> Tuple[List[str], List[Dict[str, Any]]]:
    base = _root(base)
    rows, issues = [], []
    for f in FACES:
        probe = f.get("probe") or ""
        if f["kind"] == "not-applicable":
            rows.append({"id": f["id"], "state": "不适用", "detail": f["why"][:60]})
            continue
        if f["id"] == "cid":
            ok, detail = _kcid_recompute(base)
            rows.append({"id": f["id"], "state": "ok" if ok else "fail", "detail": detail})
            if not ok:
                issues.append("cid 已知向量复算不一致：%s" % detail)
            continue
        if not probe:
            rows.append({"id": f["id"], "state": "需对端", "detail": "需第三方客户端/对端环境（本机不可自证）"})
            continue
        if probe.startswith("core."):
            avail = importlib.util.find_spec("core") is not None and \
                os.path.isfile(os.path.join(base, "desktop/src/core/%s.py" % probe.split(".")[1]))
            detail = "本仓运行时在场（%s）" % probe
        else:
            avail = bool(shutil.which(probe)) or importlib.util.find_spec(probe) is not None
            detail = "对端工具在位" if avail else "对端工具不在位（pip/npm 安装后重跑）"
        rows.append({"id": f["id"], "state": "ok" if avail else "skipped", "detail": detail})
        if f["artifact"] and f["artifact"].endswith(".json"):
            p = os.path.join(base, f["artifact"])
            if not os.path.isfile(p):
                issues.append("%s 的产物缺失：%s" % (f["id"], f["artifact"]))
            else:
                try:
                    with open(p, encoding="utf-8") as fh:
                        json.load(fh)
                except Exception as e:  # noqa: BLE001
                    issues.append("%s 的产物不可解析：%s" % (f["id"], e))
    return issues, rows


def _card(f: Dict[str, Any]) -> str:
    lines = ["### `%s` · %s" % (f["id"], f["title"]), "",
             "- 种类：`%s`" % f["kind"],
             "- 对端：%s" % f["peer"],
             "- 安装：%s" % f["install"],
             "- 命令（原样）：`%s`" % f["command"],
             "- 期望：%s" % f["expect"]]
    if f["artifact"]:
        lines.append("- 相关产物：`%s`" % f["artifact"])
    if f["why"]:
        lines.append("- 为何如此判定：%s" % f["why"])
    lines.append("- 回填：请在 `%s` 对应行填入 tool_version / run_by / run_at / output_sha256 / verdict。" % STATUS_REL)
    lines.append("")
    return "\n".join(lines)


def emit(base: str = "") -> List[str]:
    base = _root(base)
    doc = ["# 互操作性 · 他证通道（第三方可自跑）", "",
           "> 本页由 `python scripts/interop_thirdparty_kit.py --emit` 生成，禁止手改。",
           "> 定位：这些卡片是给**第三方**跑的，不冒充「本仓已他证」。回填表：`%s`。" % STATUS_REL,
           "",
           "## 两种证据，别混（分层）", "",
           "- **上游判据校验（已有）**：`scripts/check_interop_schemas.py --fetch` 用上游官方 meta-schema 校导出面 → `results/interop-schema-validation.md`。",
           "- **他证（本页）**：对端消费或官方验证器由第三方在其环境跑，结果回填状态表。未回填 = 未他证。",
           "",
           "## 回填纪律", "",
           "1. 六字段齐备才算一条他证：`tool_version` · `run_by` · `run_at` · `output_sha256` · `verdict` · `note`。",
           "2. `output_sha256` 必须是被跑对象或输出的 sha256（不可用「看起来通过」代替）。",
           "3. 标 `not-applicable` 的面**不计入他证通过数**，只说明为何不适用。",
           "",
           "## 他证卡", ""]
    doc += [_card(f) for f in FACES]
    os.makedirs(os.path.join(base, os.path.dirname(DOC_REL)), exist_ok=True)
    with open(os.path.join(base, DOC_REL), "w", encoding="utf-8", newline="") as fh:
        fh.write("\n".join(doc) + "\n")

    rows = ["# 互操作性 · 他证回填状态表", "",
            "> 由 `python scripts/interop_thirdparty_kit.py --emit` 生成骨架；由第三方回填右侧字段。",
            "> 初始 `verdict` = `%s`（表示通道就绪、**未被任何第三方跑过**）。" % UNFILLED,
            "",
            "| face | kind | 对端工具 | 安装 | 命令原文 | tool_version | run_by | run_at | output_sha256 | verdict | note |",
            "|---|---|---|---|---|---|---|---|---|---|---|"]
    for f in FACES:
        note = f["why"] if f["kind"] == "not-applicable" else ""
        rows.append("| `%s` | %s | %s | %s | `%s` |  |  |  |  | %s | %s |"
                    % (f["id"], f["kind"], f["peer"], f["install"], f["command"], UNFILLED, note))
    with open(os.path.join(base, STATUS_REL), "w", encoding="utf-8", newline="") as fh:
        fh.write("\n".join(rows) + "\n")
    return []


def check(base: str = "") -> Tuple[List[str], Dict[str, Any]]:
    base = _root(base)
    issues: List[str] = []
    spath = os.path.join(base, STATUS_REL)
    dpath = os.path.join(base, DOC_REL)
    if not os.path.isfile(spath):
        return ["缺回填状态表 %s（跑 --emit）" % STATUS_REL], {}
    if not os.path.isfile(dpath):
        issues.append("缺说明页 %s（跑 --emit）" % DOC_REL)
    with open(spath, encoding="utf-8") as fh:
        status_lines = fh.read().splitlines()
    rows = [l for l in status_lines if l.startswith("| `")]
    seen, filled = {}, 0
    for line in rows:
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 11:
            issues.append("状态表行列数不足（%d）：%s" % (len(cells), line[:60]))
            continue
        fid = cells[0].strip("`")
        seen[fid] = cells
        verdict = cells[9]
        if verdict and verdict != UNFILLED:
            filled += 1
            need = {"tool_version": cells[5], "run_by": cells[6], "run_at": cells[7],
                    "output_sha256": cells[8]}
            miss = [k for k, v in need.items() if not v]
            if miss:
                issues.append("%s 已标 verdict=%s 但缺字段：%s" % (fid, verdict, miss))
            if cells[8] and not re.fullmatch(r"[0-9a-f]{64}", cells[8]):
                issues.append("%s 的 output_sha256 不是 64 位十六进制（不可用「看起来通过」代替）" % fid)
    for f in FACES:
        if f["id"] not in seen:
            issues.append("状态表缺面：%s（每个互操作面都必须有一行，含 not-applicable）" % f["id"])
        elif not seen[f["id"]][10] and f["kind"] == "not-applicable":
            issues.append("%s 标为 not-applicable 但 note 未写理由" % f["id"])
    stats = {"faces": len(FACES), "rows": len(seen), "filled": filled,
             "unfilled": len(FACES) - filled}
    return issues, stats


def record(base: str, evidence_path: str) -> Tuple[List[str], int]:
    """把证据行写回状态表（机器写入，禁止手改）。

    证据行字段：face / tool / tool_version / run_by / run_at / command / output_sha256 / verdict / note
    （`command` 缺省沿用表内命令原文；`verdict` 必填且不得为 UNFILLED）
    """
    base = _root(base)
    spath = os.path.join(base, STATUS_REL)
    if not os.path.isfile(spath):
        return ["缺回填状态表（先 --emit）"], 0
    with open(evidence_path, encoding="utf-8") as fh:
        rows = [json.loads(l) for l in fh if l.strip()]
    with open(spath, encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    issues: List[str] = []
    done = 0
    by_face = {str(r.get("face")): r for r in rows}
    for i, line in enumerate(lines):
        if not line.startswith("| `"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        fid = cells[0].strip("`")
        ev = by_face.get(fid)
        if not ev:
            continue
        verdict = str(ev.get("verdict") or "")
        if not verdict or verdict == UNFILLED:
            issues.append("%s 证据行缺 verdict" % fid)
            continue
        cells[5] = str(ev.get("tool_version") or "")
        cells[6] = str(ev.get("run_by") or "")
        cells[7] = str(ev.get("run_at") or "")
        cells[8] = str(ev.get("output_sha256") or "")
        cells[9] = verdict
        cells[10] = str(ev.get("note") or cells[10])
        if ev.get("command"):
            cells[4] = "`%s`" % str(ev["command"]).replace("|", "\\|")
        lines[i] = "| " + " | ".join(cells) + " |"
        done += 1
    with open(spath, "w", encoding="utf-8", newline="") as fh:
        fh.write("\n".join(lines) + "\n")
    return issues, done


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="interop_thirdparty_kit",
                                 description="互操作性他证通道（只建通道，不伪造第三方证据）")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--emit", action="store_true")
    g.add_argument("--check", action="store_true")
    g.add_argument("--dry-run", action="store_true")
    g.add_argument("--record", metavar="EVIDENCE_JSONL",
                   help="把第三方跑出的证据行写回状态表（六字段齐备才算他证）")
    ap.add_argument("--root", default="")
    args = ap.parse_args(argv)
    if args.emit:
        issues = emit(args.root)
        print("== 他证通道已生成 ==")
        print("  说明页：%s" % DOC_REL)
        print("  回填表：%s（%d 面，初始全部「%s」）" % (STATUS_REL, len(FACES), UNFILLED))
    elif args.check:
        issues, stats = check(args.root)
        print("== 他证通道自检 ==")
        print("  面 %(faces)d · 表行 %(rows)d · 已回填 %(filled)d · 未回填 %(unfilled)d" % stats
              if stats else "  状态表缺失")
    elif args.record:
        issues, n = record(args.root, args.record)
        print("== 他证回填 ==")
        print("  已写回 %d 行 → %s" % (n, STATUS_REL))
    else:
        issues, rows = dry_run(args.root)
        print("== 他证通道 dry-run（本机探测；不联网、不写盘）==")
        for r in rows:
            print("  %-12s %-10s %s" % (r["id"], r["state"], r["detail"]))
    for i in issues:
        print("  [FAIL] %s" % i, file=sys.stderr)
    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
