#!/usr/bin/env python3
"""面级双跑对账：同一快照上并行跑 Python 真源与 .NET 引擎，**逐字节**比对 stdout。

为什么要脚本化：此前每片面都是手敲命令，改动共享模块（如 PythonJson）后要不要重验、
验哪几面，全靠记忆。本探针把「已等价面」固化成一张表，一条命令复验全部。

用法：
    python probes/face_parity_probe.py --root <仓库或隔离快照> [--py-exe <python>] [--cli <nf-dotnet>]

退出码：0 全部逐字节一致（且退出码一致）/ 1 有差异。

换行口径：Windows 上 Python 的 print 走文本模式 → stdout 是 CRLF，而 .NET 写 LF。
两侧在 Linux（CI 目标）上都是 LF，故判据取**换行归一后逐字节**；仅 CRLF/LF 之差会被
单独标成「LF」而不是静默算通过，原始字节是否完全一致另记一列。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import _paths  # 默认路径唯一出处（探针可移植）

# (名称, 参数) —— 两侧共用同一套参数（Python 侧 = nf.py，.NET 侧 = nf-dotnet --root）
FACES = [
    # 第一百零八片新增：需求 → 装配计划（assemble）——预设命中 / 自定义流 / 澄清漏斗 / --answer / --check
    ("assemble-preset", ["assemble", "西幻生存"]),
    ("assemble-preset2", ["assemble", "校园情感"]),
    ("assemble-custom", ["assemble", "自定义权谋宫廷"]),
    ("assemble-clarify", ["assemble", "帮我做个游戏"]),
    ("assemble-answer", ["assemble", "权谋", "--answer", "题材：宫廷"]),
    ("assemble-check", ["assemble", "西幻生存", "--check", "library/NF-1.md"]),
    # 第一百零三片新增：缺口逐行审查（review）——`--scope` 在真源里是空转（算而不用），故也对齐其无效果
    ("review", ["review"]),
    ("review-limit5", ["review", "--limit", "5"]),
    ("review-limit5-json", ["review", "--limit", "5", "--json"]),
    ("review-scope-noop", ["review", "--scope", "silent-skip", "--limit", "9"]),
    # 第一百零一片新增：环境自检（doctor）与 Spec Registry（spec）
    ("doctor", ["doctor"]),
    ("doctor-json", ["doctor", "--json"]),
    ("spec", ["spec"]),
    ("spec-ls", ["spec", "ls"]),
    # 第一百片新增：决策层（decide）——真源同命令同参数；问题件由探针写进临时目录，两侧读同一份
    ("decide", ["decide", "--state-text", "雨天走廊 与 校园情感 场景", "--questions", "{tmp}/decide-questions.json"]),
    ("decide-json", ["decide", "--state-text", "雨天走廊 与 校园情感 场景", "--questions", "{tmp}/decide-questions.json", "--json"]),
    ("decide-dry-run", ["decide", "--dry-run", "--questions", "{tmp}/decide-questions.json"]),
    ("decide-dry-run-json", ["decide", "--dry-run", "--questions", "{tmp}/decide-questions.json", "--json"]),
    ("decide-abstained", ["decide", "--state-text", "x", "--questions", "{tmp}/decide-questions.json", "--adapter", "ghost"]),
    ("decide-abstained-json", ["decide", "--state-text", "x", "--questions", "{tmp}/decide-questions.json", "--adapter", "ghost", "--json"]),
    # 第九十九片新增：构建回路（workloop）与许可证门（license）——真源同命令同参数，两侧逐字节比对
    ("license", ["license"]),
    ("license-json", ["license", "--json"]),
    ("workloop-list", ["workloop", "--list", "--top", "5"]),
    ("workloop-list-json", ["workloop", "--list", "--json"]),
    ("workloop", ["workloop"]),
    ("workloop-json", ["workloop", "--json"]),
    ("receipts", ["receipts", "--json"]),
    ("transparency", ["transparency", "--json"]),
    ("assertions", ["assertions", "--json"]),
    ("decisions", ["decisions", "verify", "--json"]),
    ("cognition", ["cognition", "--json"]),
    ("library", ["library", "verify", "--json"]),
    ("model", ["model", "--json"]),
    ("model-contracts", ["model", "contracts", "--json"]),
    ("sig", ["sig", "--json"]),
    ("lint-kinds", ["lint", "--kinds"]),
    ("module-types-backlog", ["module", "types", "--backlog"]),
    ("module-types", ["module", "types"]),
    ("module-types-json", ["module", "types", "--json"]),
    ("module-signature", ["module", "signature"]),
    ("module-signature-json", ["module", "signature", "--json"]),
    ("pipeline-dryrun-all", ["pipeline", "dryrun", "--all"]),
    ("pipeline-dryrun-all-json", ["pipeline", "dryrun", "--all", "--json"]),
    ("pipeline-dryrun-one", ["pipeline", "dryrun", "--pipeline", "03_管线库/P01_标准管线.md"]),
    ("pipeline-dryrun-one-json", ["pipeline", "dryrun", "--pipeline", "03_管线库/P01_标准管线.md", "--json"]),
    ("handover-ls", ["handover"]),
    ("handover-ls-json", ["handover", "ls", "--json"]),
    ("handover-verify", ["handover", "verify"]),
    ("handover-verify-json", ["handover", "verify", "--json"]),
    ("postmortem-ls", ["postmortem"]),
    ("postmortem-ls-json", ["postmortem", "ls", "--json"]),
    ("postmortem-verify-json", ["postmortem", "verify", "--json"]),
    ("audit-ls", ["audit"]),
    ("audit-ls-json", ["audit", "ls", "--json"]),
    ("audit-verify", ["audit", "verify"]),
    ("audit-verify-json", ["audit", "verify", "--json"]),
    ("handover-json-no-sub", ["handover", "--json"]),      # 两侧都应是用例错误 exit 2
    ("audit-json-no-sub", ["audit", "--json"]),
    # 实践包面（第五十三片）：ls / show / for / verify 各自的文本与机读面
    ("patterns-ls", ["patterns", "ls"]),
    ("patterns-ls-json", ["patterns", "ls", "--json"]),
    ("patterns-show", ["patterns", "show", "single-source-truth"]),
    ("patterns-show-json", ["patterns", "show", "single-source-truth", "--json"]),
    ("patterns-for", ["patterns", "for", "protocol/RECEIPTS.json"]),
    ("patterns-for-json", ["patterns", "for", "protocol/RECEIPTS.json", "--json"]),
    ("patterns-verify", ["patterns", "verify"]),
    ("patterns-verify-json", ["patterns", "verify", "--json"]),
    # 协议头 / 端点契约面（第五十四片）
    ("rfc", ["rfc"]),
    ("rfc-json", ["rfc", "--json"]),
    ("endpoint", ["endpoint"]),
    ("endpoint-json", ["endpoint", "--json"]),
    # 事件背书 / 模块工具面（第五十五片）
    ("events", ["events"]),
    ("events-json", ["events", "--json"]),
    ("toolface", ["toolface"]),
    ("toolface-json", ["toolface", "--json"]),
    # ST 制卡校验器（第五十六片）：三类形状 + 错误路径退出码
    ("st-validate-card", ["st-validate", "docs/examples/st-validate/fixture_card_v2_clean.json"]),
    ("st-validate-card-json", ["st-validate", "docs/examples/st-validate/fixture_card_v2_clean.json", "--json"]),
    ("st-validate-worldbook", ["st-validate", "docs/examples/st-validate/fixture_worldbook_messy.json"]),
    ("st-validate-worldbook-json", ["st-validate", "docs/examples/st-validate/fixture_worldbook_messy.json", "--json"]),
    ("st-validate-mvu", ["st-validate", "docs/examples/mvu-output/mvu_variables.json"]),
    ("st-validate-missing", ["st-validate", "docs/examples/st-validate/no-such-file.json"]),
    # 自述数字实算（第五十七片）：注意 **不加** `--json` 面——Python 侧该路径缺 import json 崩栈（已登记缺陷）
    ("stats", ["stats"]),
    ("stats-check", ["stats", "--check"]),
    # 知识源频次复算（第五十八片）：trace 夹具在引擎侧（仓库内无 trace 件），两侧读同一绝对路径
    ("knowledge-frequency", ["knowledge", "frequency", "--trace",
                             str(_paths.FIXTURES / "knowledge_trace.jsonl")]),
    ("knowledge-frequency-json", ["knowledge", "frequency", "--trace",
                                  str(_paths.FIXTURES / "knowledge_trace.jsonl"), "--json"]),
    ("knowledge-frequency-missing", ["knowledge", "frequency", "--trace",
                                     str(_paths.FIXTURES / "no-such-trace.json")]),
    # 互操作导出面（第五十九片）：--list + 7 个已移植形状的 stdout 面（未移植形状不进本表：双方本应不同判）
    ("interop-list", ["interop", "--list"]),
    ("interop-intoto", ["interop", "--kind", "intoto"]),
    ("interop-sbom", ["interop", "--kind", "sbom"]),
    ("interop-slsa", ["interop", "--kind", "slsa"]),
    ("interop-cyclonedx", ["interop", "--kind", "cyclonedx"]),
    ("interop-vc", ["interop", "--kind", "vc"]),
    ("interop-c2pa", ["interop", "--kind", "c2pa"]),
    ("interop-cid", ["interop", "--kind", "cid"]),
    ("interop-check", ["interop", "--check"]),
    ("interop-check-json", ["interop", "--check", "--json"]),
    # 世界模型（第六十二片）：浏览面（重放面未移植，双方本应不同判，故不进本表）
    ("worldmodel", ["worldmodel"]),
    ("worldmodel-json", ["worldmodel", "--json"]),
    ("worldmodel-walk", ["worldmodel", "--walk"]),
    ("worldmodel-run", ["worldmodel", "--run"]),
    ("worldmodel-run-json", ["worldmodel", "--run", "--json"]),
    # 变更影响面预检（第六十四片）：几种目标形态（其余组合走 impact 专探针）
    ("impact-core-module", ["impact", "M50"]),
    ("impact-core-module-check", ["impact", "M50", "--check"]),
    ("impact-missing", ["impact", "不存在的目标XYZ"]),
    # 市场面（第六十五片）：目录视图与 See-Also 关联（其余组合走 market 专探针）
    ("market-list", ["market", "--list"]),
    ("market-list-tier-official", ["market", "--list", "--tier", "official"]),
    ("related-core-module", ["related", "M90"]),
    # 判据面小口三件（第六十九片）：修复指引 / 引用反查 / 版本差异（相对路径按探针 cwd=root 解析，两侧同）
    ("explain-all", ["explain", "all"]),
    ("explain-check", ["explain", "25"]),
    ("who-refers-bare", ["who-refers", "M55"]),
    ("who-refers-category", ["who-refers", "情感:M55"]),
    ("diff-real", ["diff", "01_核心协议.md", "02_联动注册表.md"]),
    ("diff-real-json", ["diff", "01_核心协议.md", "02_联动注册表.md", "--json"]),
    # 产出形态面（第七十片）：清单 + 判件（相对路径按探针 cwd=root 解析，两侧同）
    # 遥测 semconv 面（第八十四片）：trace 夹具在引擎侧（仓库内无 trace 件），两侧读同一绝对路径
    # 指令档路由面（第八十五片）：列全部 / 单工作流 / 未知工作流 / JSON 两态
    ("driver", ["driver"]),
    ("driver-json", ["driver", "--json"]),
    ("driver-assemble", ["driver", "assemble"]),
    ("driver-assemble-json", ["driver", "assemble", "--json"]),
    ("driver-unknown", ["driver", "不存在的流"]),
    ("telemetry", ["telemetry",
                   str(_paths.FIXTURES / "_telemetry_trace.json")]),
    ("telemetry-otlp", ["telemetry",
                        str(_paths.FIXTURES / "_telemetry_trace.json"),
                        "--otlp"]),
    ("telemetry-single", ["telemetry",
                          str(_paths.FIXTURES / "_telemetry_trace_single.json")]),
    ("telemetry-empty", ["telemetry",
                         str(_paths.FIXTURES / "_telemetry_trace_empty.json")]),
    ("output-list", ["output", "list"]),
    ("output-list-json", ["output", "list", "--json"]),
    ("output-list-tier", ["output", "list", "--tier", "T2"]),
    ("output-check-real", ["output", "check",
                           "community/组合包-受监管行业/outputs/COMBO_CERT.json",
                           "community/量化金融域包/outputs/QUANT_METRICS.json",
                           "community/AI系统域包/outputs/CONCEPT_CLOSURE.json"]),
    ("output-check-missing", ["output", "check", "不存在的文件.json"]),
    # 产出形态门禁合成（第七十三片）：机验率 / 渲染 / check32 三合一（无 --write，全是读面）
    ("output-meter", ["output", "meter"]),
    ("output-meter-json", ["output", "meter", "--json"]),
    ("output-render", ["output", "render"]),
    ("output-render-json", ["output", "render", "--json"]),
    ("output-verify", ["output", "verify"]),
    ("output-verify-json", ["output", "verify", "--json"]),
    # 模块生命周期（第七十六片）：ls / status 只读面与 verify（check24 同语义）
    ("module-verify", ["module", "verify"]),
    ("module-ls", ["module", "ls"]),
    ("module-ls-json", ["module", "ls", "--json"]),
    ("module-ls-deprecated", ["module", "ls", "--status", "deprecated"]),
    ("module-status", ["module", "status", "04_模块库/事件类/M22_事件叙事.md"]),
    # 概念前置闭包求值器（第七十一片）——**真源是 scripts/ 下的独立脚本，不是 nf 子命令**：
    # 第三条 = Python 侧入口脚本；第四条 = 引擎参数要在 Python 参数前**去掉几个词**（这里是子命令名 1 个）。
    ("closure-default", ["domain-closure", "--target", "C22"], "scripts/ai_domain_closure.py", 1),
    ("closure-list", ["domain-closure", "--list"], "scripts/ai_domain_closure.py", 1),
    ("closure-json", ["domain-closure", "--json"], "scripts/ai_domain_closure.py", 1),
    ("closure-ready", ["domain-closure", "--ready-list", "--loaded", "C00,C01"],
     "scripts/ai_domain_closure.py", 1),
    ("closure-order", ["domain-closure", "--order", "design-guide-chapter-order"],
     "scripts/ai_domain_closure.py", 1),
    ("closure-check", ["domain-closure", "--check"], "scripts/ai_domain_closure.py", 1),
    ("closure-quant-check", ["domain-closure", "--check", "--asset",
                             "community/量化金融域包/assets/QUANT_GRAPH.md"],
     "scripts/ai_domain_closure.py", 1),
    # 包视图（第六十六片）：依赖闭包 + 挂载冲突 + 登记三要件
    ("market-package", ["market", "community/校园西幻轻混组合包"]),
    ("market-package-json", ["market", "community/校园西幻轻混组合包", "--json"]),
    ("market-package-unregistered", ["market", "community/不存在的包XYZ"]),
    # 资产台账（第六十七片）：verify / inventory / ls（扫描根缺省 = 仓根，两侧同）
    ("asset-verify", ["asset", "verify"]),
    ("asset-inventory", ["asset", "inventory"]),
    ("asset-ls", ["asset", "ls"]),
    ("asset-ls-json", ["asset", "ls", "--json"]),
    # 资产质量五面（第六十八片）：行数基线 / 键语义密度 / 引用度 / 语义厚度 / 键表机读投影
    ("asset-baseline", ["asset", "baseline"]),
    ("asset-density", ["asset", "density"]),
    ("asset-density-json", ["asset", "density", "--json"]),
    ("asset-usage", ["asset", "usage"]),
    ("asset-usage-json", ["asset", "usage", "--json"]),
    ("asset-usage-strict", ["asset", "usage", "--strict"]),
    ("asset-thickness", ["asset", "thickness"]),
    ("asset-thickness-json", ["asset", "thickness", "--json"]),
    ("asset-ledger", ["asset", "ledger"]),
    ("asset-ledger-json", ["asset", "ledger", "--json"]),
    ("handover-check", ["handover", "check", "handovers/HO-0001-W1到W2.md"]),
    ("handover-check-json", ["handover", "check", "handovers/HO-0001-W1到W2.md", "--json"]),
    ("postmortem-check", ["postmortem", "check", "postmortems/PO-0001-冻结顺序事故.md"]),
    ("audit-check", ["audit", "check", "results/audit/docs_audit-49-audit-protocol.md"]),
    ("audit-check-json", ["audit", "check", "results/audit/docs_audit-49-audit-protocol.md", "--json"]),
    ("state-front-check", ["state-front", "docs/examples/state-front/nf1_front.md", "--check"]),
    ("state-front-ab", ["state-front", "docs/examples/state-front/nf1_front.md", "--ab"]),
    ("state-front-ab-json", ["state-front", "docs/examples/state-front/nf1_front.md", "--ab", "--json"]),
    ("state-front-reorder", ["state-front", "docs/examples/state-front/nf1_front.md"]),
    ("state-front-reorder-json", ["state-front", "docs/examples/state-front/nf1_front.md", "--mode", "back", "--json"]),
    ("knowledge-status", ["knowledge"]),
    ("knowledge-json-no-sub", ["knowledge", "--json"]),        # 两侧都应是用例错误 exit 2
    ("knowledge-status-sub", ["knowledge", "status"]),          # Python 无 status 子命令 → exit 2
    ("knowledge-order", ["knowledge", "order"]),
    ("knowledge-order-json", ["knowledge", "order", "--json"]),
    ("knowledge-order-clearance", ["knowledge", "order", "--as", "internal"]),
    ("knowledge-visible", ["knowledge", "visible", "--as", "public"]),
    ("knowledge-visible-json", ["knowledge", "visible", "--as", "internal", "--json"]),
    ("knowledge-transform", ["knowledge", "transform"]),
    ("knowledge-transform-json", ["knowledge", "transform", "--json"]),
    ("knowledge-lint", ["knowledge", "lint"]),
    ("knowledge-lint-json", ["knowledge", "lint", "--json"]),
]

DEFAULT_ROOT = _paths.SNAP
DEFAULT_PY = _paths.PY
DEFAULT_CLI = _paths.engine("tools", "nf-dotnet", "bin", "Release", "net8.0", "nf-dotnet.exe")
def run(argv, root, env=None):
    proc = subprocess.run(argv, cwd=root, capture_output=True, env=env)
    return proc.returncode, proc.stdout, proc.stderr


# 声明边界面：**不逐字节一致**，但差异必须**恰好**是被登记的那一处，多余即失败。
# 每项：（名称, 参数, 引擎侧应多出的行片段, 真源侧应被替换掉的行片段）
# 面用夹具：探针写进临时目录，{tmp} 占位符在参数里被替换（两侧读同一份，谁也不写它）
FACE_FIXTURES = {
    "decide-questions.json": json.dumps({
        "pipeline": {"type": "choice",
                     "options": ["P02 校园情感流", "P03 西幻生存流"]},
        "multilingual": {"type": "noul", "true_hints": ["中文", "多语"]},
        "risk": {"type": "score", "levels": ["低", "中", "高"]},
    }, ensure_ascii=False, indent=2) + "\n",
}


BOUNDARY_FACES = [
    ("score", ["score"],
     "v=UNKNOWN（声明边界：源码 AST linter 面，本引擎不复算，不伪造）",
     "purity_clean"),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=DEFAULT_ROOT)
    ap.add_argument("--py-exe", default=DEFAULT_PY)
    ap.add_argument("--cli", default=DEFAULT_CLI)
    args = ap.parse_args()

    # 量具自身不许随宿主就地编码崩：宿主控制台是 GBK 时，打印引擎 stderr（含 ✗ 等字符）会抛
    # UnicodeEncodeError，把探针自己的判定结果吃掉。统一改成 UTF-8 + errors=replace。
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass

    env = dict(os.environ)
    env["PYTHONPATH"] = os.path.join(args.root, "desktop", "src")
    env["PYTHONIOENCODING"] = "utf-8"
    nf_py = os.path.join(args.root, "scripts", "nf.py")

    print("快照：%s" % args.root)
    print("Python：%s\n引擎：%s\n" % (args.py_exe, args.cli))

    bad = []
    raw_identical = 0
    lf_only = 0
    face_tmp = tempfile.mkdtemp(prefix="nf-face-")
    for fname, ftext in FACE_FIXTURES.items():
        with open(os.path.join(face_tmp, fname), "w", encoding="utf-8", newline="") as fh:
            fh.write(ftext)
    for face in FACES:
        name, tail = face[0], [a.replace("{tmp}", face_tmp) for a in face[1]]
        # 真源入口缺省 = nf.py；个别面（如 concept_graph 的只读求值器）真源是 scripts/ 下的独立脚本，
        # 由第三项显式指定、第四项给出"引擎参数比 Python 多几个词"——**不含糊地把两种真源混成一种**。
        py_script = face[2] if len(face) > 2 else "scripts/nf.py"
        py_drop = face[3] if len(face) > 3 else 0
        py_entry = os.path.join(args.root, py_script.replace("/", os.sep))
        py_code, py_out, py_err = run([args.py_exe, py_entry, *tail[py_drop:]], args.root, env)
        net_code, net_out, net_err = run([args.cli, "--root", args.root, *tail], args.root, env)
        same_raw = py_out == net_out
        same_lf = py_out.replace(b"\r\n", b"\n") == net_out.replace(b"\r\n", b"\n")
        same_code = py_code == net_code
        digest = hashlib.sha256(py_out).hexdigest()[:16]
        label = "OK" if (same_raw and same_code) else ("LF" if (same_lf and same_code) else "DIFF")
        raw_identical += 1 if same_raw else 0
        lf_only += 1 if (same_lf and not same_raw) else 0
        print("%-6s %-16s py=%-3d net=%-3d 字节 py=%-6d net=%-6d sha=%s"
              % (label, name, py_code, net_code, len(py_out), len(net_out), digest))
        if not same_lf:
            bad.append((name, "stdout 内容不一致"))
            for i, (a, b) in enumerate(zip(py_out, net_out)):
                if a != b:
                    print("       首个差异字节 @%d：py=%r net=%r" % (i, py_out[max(0, i - 40):i + 40],
                                                                   net_out[max(0, i - 40):i + 40]))
                    break
        if not same_code:
            bad.append((name, "退出码不一致 py=%d net=%d" % (py_code, net_code)))
        if net_err.strip():
            print("       net stderr：%s" % net_err.decode("utf-8", "replace").strip()[:200])
        if not same_code:
            # 第一百零六片补：**两侧证据都打出来**。此前只打 net stderr——真源侧失败时（例如一次
            # 未复现的 `decide-dry-run-json py=1 net=0` 瞬态）看不到真源任何输出，**无法归因**。
            for label, code, raw, err in (("py ", py_code, py_out, py_err),
                                           ("net", net_code, net_out, net_err)):
                text = raw.decode("utf-8", "replace").replace("\r\n", "\n").strip()
                print(f"       {label} exit={code} stdout尾：{text[-200:] if text else '（空）'}")
                stderr = err.decode("utf-8", "replace").replace("\r\n", "\n").strip()
                if stderr:
                    print(f"       {label} stderr尾：{stderr[-300:]}")

    # 声明边界面：**不逐字节一致**，但差异必须**恰好**是登记的那一处（多一处即失败）
    boundary_bad = []
    for name, tail, net_marker, py_marker in BOUNDARY_FACES:
        py_code, py_out, _ = run([args.py_exe, nf_py, *tail], args.root, env)
        net_code, net_out, _ = run([args.cli, "--root", args.root, *tail], args.root, env)
        py_lines = py_out.decode("utf-8", "replace").splitlines()
        net_lines = net_out.decode("utf-8", "replace").splitlines()
        py_kept = [l for l in py_lines if py_marker not in l]
        net_kept = [l for l in net_lines if net_marker not in l]
        extra_net = len(net_lines) - len(net_kept)
        extra_py = len(py_lines) - len(py_kept)
        ok = py_code == net_code and py_kept == net_kept and extra_net == 1 and extra_py == 1
        print("边界   %-16s py=%-3d net=%-3d 剔除登记行后一致=%s（引擎多 1 行 UNKNOWN · 真源多 1 行 %s）"
              % (name, py_code, net_code, py_code == net_code and py_kept == net_kept, py_marker))
        if not ok:
            boundary_bad.append(name)

    print("\n面级对账：%d 面 · 原始字节全同 %d · 仅换行风格差异 %d · 差异 %d · 边界面 %d/%d"
          % (len(FACES), raw_identical, lf_only, len(bad),
             len(BOUNDARY_FACES) - len(boundary_bad), len(BOUNDARY_FACES)))
    for name, why in bad:
        print("  [差异] %s：%s" % (name, why))
    for name in boundary_bad:
        print("  [边界差异] %s：差异不止登记的那一处" % name)
    return 0 if not bad and not boundary_bad else 1


if __name__ == "__main__":
    raise SystemExit(main())
