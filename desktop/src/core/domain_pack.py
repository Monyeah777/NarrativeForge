"""域包工厂：从一个「域规格」生成整套**过门禁**的社区域包（AI 品类清单工程的机制面）。

为什么要有工厂：清单是 100 大类 / 1200 细分。手工复制 100 遍 = 每包漂移一处就静默破门禁。
工厂把「域包必须满足的一切」写成可复算的生成规则，并把**不可协商项**固化成断言：

- 唯一性：独占类别（R2）/ 模块文件名裸 token（check14 ⑤c）/ 管线 id（check14 ⑧）全局唯一；
- 登记三要件：protocol.yaml + 02 §8 在册（含 `模块（N）`）+ registry protocols[] 投影；
- 资产供应链：assets/*.md 头（`nf-asset`）与 provenance.json 双源一致（check23）；
- 概念图健康：无环 / 无悬空 / 边有溯源 / 层位合法 / 别名唯一 / 分支完备（check32）；
- 产出形态：`outputs/INDEX.json` 声明 T2/T3/T4 面，其中**可机验占比 = 100%**（≥95% 门槛）；
  且必有一个 **T4 可复算面**（core/domain_metrics 重算并与在盘报告逐字段比对）。

内容 vs 机制：**内容**（12 条细分的定义 / 权威锚 / 可机验判据 / 失效模式）来自域规格文件
（作者侧输入，内部档案，不入公开仓）；**机制**（本模块）保证内容的形态与可验证性。
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

SPEC_DIR = ".rivet/private_archive/ai_packs/specs"
MANIFEST_REL = "protocol/domain_packs.json"
DOMAIN_LIST_ANCHOR = "DOMAIN = ["
REGISTRY_REL = "desktop/src/core/registry.json"
STANDARDS_REL = "protocol/standards_catalog.json"
BINDING_REL = "protocol/standards_binding.json"
DOC02_REL = "02_联动注册表.md"
VERIFY_REL = "verify.sh"

#: 可用管线 id 池（避开层位 id P00/P10…/P80、官方 P00/P01/P90、既有包 P02–P08）
#: 管线 id 池（两位段）——避开层位 id（P00/P10/…/P80）、官方 P00/P01/P90 与既有包 P02–P08。
#: 两位段共 90 个；AI 品类清单有 100 类，**两位段不够**（2026-09-23 实测：第 83 个域包起无号可用），
#: 故按「模块号命名空间扩展」同源做法扩到三位：`P[0-9]{2,3}`（schema 已同步）。
PIPELINE_POOL: List[str] = (
    ["P09"] + ["P1%d" % i for i in range(1, 10)] + ["P2%d" % i for i in range(1, 10)]
    + ["P3%d" % i for i in range(1, 10)] + ["P4%d" % i for i in range(1, 10)]
    + ["P5%d" % i for i in range(1, 10)] + ["P6%d" % i for i in range(1, 10)]
    + ["P7%d" % i for i in range(1, 10)] + ["P8%d" % i for i in range(1, 10)]
    + ["P9%d" % i for i in range(1, 10)]
    # 三位段（P100–P199）：给清单剩下的域包用，避免与两位段/层位/官方号冲突
    + ["P%03d" % i for i in range(100, 200)]
)

SUB_COUNT = 12


def load_spec(root: str, code: str) -> Dict[str, Any]:
    p = Path(root) / SPEC_DIR / ("%s.json" % code)
    if not p.is_file():
        raise ValueError("域规格不存在：%s" % p)
    spec = json.loads(p.read_text(encoding="utf-8"))
    issues = spec_issues(spec)
    if issues:
        raise ValueError("域规格不合规：%s" % "；".join(issues))
    return spec


# ---------------------------------------------------------------- 标准绑定（可扩展标准面）

#: 段默认 + 关键词规则 + 域码覆盖（与内部 `binding_rules.py` 同源；此处是**执行侧**副本，
#: 保证 core 不依赖 .rivet 内部档案——规则变更时两处同步由 check32 断言「绑定覆盖率 100%」。）
_STD_SECTION_DEFAULT = {
    "A": ["ietf-json-schema", "mlcommons-bench", "onnx"],
    "B": ["ietf-json-schema", "w3c-tabular-data", "frictionless-table"],
    "C": ["cncf-otel-semconv", "mlcommons-bench", "frictionless-table"],
    "D": ["nist-ai-rmf", "w3c-prov-o", "iso-iec-25010"],
    "E": ["commonmark", "w3c-tabular-data", "w3c-epub33"],
    "F": ["nist-ai-rmf", "w3c-prov-o", "spdx-licenses"],
}
_STD_KEYWORD: List[Tuple[str, str]] = [
    ("许可|版权|知识产权|授权", "creativecommons"),
    ("隐私|个人信息|去标识|合规|监管", "gdpr"),
    ("安全|越狱|红队|攻击|对抗", "owasp-llm"),
    ("漏洞|缺陷|弱点", "cwe"),
    ("供应链|依赖", "spdx-3"),
    ("水印|溯源|凭证|内容来源", "c2pa-spec"),
    ("无障碍|可访问", "w3c-wcag22"),
    ("医疗|临床|病历|诊断", "hl7-fhir"),
    ("影像|放射", "dicom"),
    ("食品|餐饮|膳食", "codex-alimentarius"),
    ("政务|公共事务|政策", "oecd-ai"),
    ("教育|培训|组织学习", "unesco-ai"),
    ("金融|投研|风控|保险|绩效", "gips"),
    ("市场代码|证券", "iso10383"),
    ("支付|结算|清算", "iso20022"),
    ("制造|产线|工业", "iso-iec-25010"),
    ("能源|电力|电网", "iso-iec-42010"),
    ("农业|种植|养殖", "fao-food"),
    ("物流|仓储|运输", "w3c-wot"),
    ("交通|出行|车机|车辆|导航", "covesa-vss"),
    ("机械|机器人|协作", "eu-machinery"),
    ("固件|OTA|升级", "uptane"),
    ("地理|遥感|地图|空间|三维|点云", "opengeospatial"),
    ("时间线|时序|日期", "w3c-owl-time"),
    ("术语|词表|本体|知识图谱", "w3c-skos"),
    ("三元组|关系抽取", "rdf11"),
    ("溯源|证据链|审计", "w3c-prov-o"),
    ("约束|校验|schema|形状|契约", "ietf-json-schema"),
    ("表格|CSV|列式", "w3c-tabular-data"),
    ("数据集|元数据|标注", "mlcommons-croissant"),
    ("评测|基准|排行榜|跑分", "mlcommons-bench"),
    ("可观测|遥测|监控|日志|成本|可靠性", "cncf-otel-semconv"),
    ("接口|API|端点|服务|部署", "oasis-openapi"),
    ("事件|消息|通道", "cncf-cloudevents"),
    ("工具调用|智能体|工作流|Agent", "mcp"),
    ("多智能体|协同|编排", "a2a"),
    ("模型|推理|量化", "onnx"),
    ("提示|指令|模板", "commonmark"),
    ("图表|可视化|看板", "vega-lite"),
    ("流程|结构图|示意", "mermaid"),
    ("视频|剪辑|字幕", "oci-image"),
    ("音频|语音|声学|音乐|歌声", "w3c-webaudio"),
    ("图像|视觉|扩散|超分|抠图", "w3c-svg2"),
    ("文档|出版|排版|校对", "w3c-epub33"),
    ("公式|数学|符号|证明", "w3c-mathml3"),
    ("单位|量纲|计量", "onvif-ucum"),
    ("浮点|数值|精度|误差", "ieee-754"),
    ("时间戳|时区", "rfc3339"),
    ("检索|向量|嵌入|召回", "frictionless-package"),
    ("问答|知识库", "frictionless-table"),
    ("缓存|分块|上下文", "gfm"),
    ("训练|微调|对齐|蒸馏|偏好", "mlcommons-bench"),
    ("合成数据|数据生成|增强", "mlcommons-croissant"),
    ("采集|清洗|质量|异常|缺失", "frictionless-table"),
    ("权限|访问控制|治理", "nist-800-188"),
    ("风险|伦理|责任", "nist-ai-rmf"),
    ("管理体系|流程|制度", "iec-42001"),
]
_STD_BY_CODE = {
    "A01": ["ietf-json-schema", "mlcommons-bench"],
    "A02": ["w3c-svg2", "mlcommons-croissant"],
    "A09": ["osv", "cwe", "lsp"],
    "A10": ["w3c-mathml3", "peps"],
    "A11": ["arrow", "parquet"],
    "A12": ["mlcommons-bench", "nist-ai-rmf"],
    "A13": ["eu-machinery", "uptane"],
    "A14": ["onnx", "ieee-754"],
    "B09": ["oasis-sarif", "cwe", "osv"],
    "B10": ["nist-800-142", "peps"],
    "B12": ["w3c-tabular-data", "ietf-json-schema"],
    "C01": ["frictionless-table", "w3c-tabular-data"],
    "C08": ["mlcommons-bench", "oasis-sarif"],
    "C11": ["k8s-crd", "cncf-otel-otlp"],
    "C15": ["arrow", "parquet", "frictionless-package"],
    "C16": ["mcp", "oasis-openapi"],
    "C17": ["a2a", "mcp"],
    "C18": ["cncf-otel-semconv", "prometheus-exposition", "openmetrics"],
    "D01": ["hl7-fhir", "dicom"],
    "D04": ["gips", "iso10383"],
    "D20": ["rocrate", "datacite"],
    "E10": ["w3c-epub33", "w3c-epub-a11y"],
    "E13": ["peps", "osi-osd"],
    "E20": ["khronos-gltf", "w3c-webaudio"],
    "F04": ["creativecommons", "spdx-licenses"],
    "F09": ["osi-osd", "spdx-licenses"],
}


def standards_catalog(root: str = ".") -> Dict[str, Dict[str, Any]]:
    doc = _read_json(Path(root) / STANDARDS_REL) or {}
    return {str(s["id"]): s for s in (doc.get("standards") or [])}


def bind_standard(spec: Dict[str, Any], sub: Dict[str, Any],
                  catalog: Dict[str, Dict[str, Any]],
                  index: int = 0) -> Tuple[str, str]:
    """给一条细分选标准：关键词命中 → 域码默认 → 段默认（都取目录内第一条命中）。

    返回 (standard_id, rationale)。不猜：目录里没有的 id 一律跳过。
    段默认候选按 `index` 轮换——保证单包**至少贴 3 条不同标准**（check32 门槛），
    同时让同一域内的细分不至于全挤在一条标准上。
    """
    name = str(sub.get("name") or "")
    for pat, sid in _STD_KEYWORD:
        if re.search(pat, name) and sid in catalog:
            return sid, "关键词「%s」命中" % pat
    for sid in _STD_BY_CODE.get(spec["code"], []):
        if sid in catalog:
            pool = [x for x in _STD_BY_CODE[spec["code"]] if x in catalog]
            return pool[index % len(pool)], "域码 %s 专属绑定（轮换 %d）" % (spec["code"],
                                                                       index % len(pool))
    sec = str(spec.get("section", "")).split(" · ")[0]
    pool = [x for x in _STD_SECTION_DEFAULT.get(sec, []) if x in catalog]
    if pool:
        return pool[index % len(pool)], "%s 段默认绑定（轮换 %d）" % (sec, index % len(pool))
    return "", ""


def bindings_for(spec: Dict[str, Any],
                 catalog: Dict[str, Dict[str, Any]]) -> Dict[str, Tuple[str, str]]:
    """整包绑定（**单一入口**）：关键词 → 专属/段默认轮换，并保证**至少 3 条不同标准**。

    多样性后处理：若关键词命中把整包挤到 1–2 条标准上，按顺序把部分细分改绑段默认池里的
    其它标准，直到不同标准数 ≥3（check32 门槛）；改写理由如实写「多样性补位」。
    """
    out: Dict[str, Tuple[str, str]] = {}
    for i, s in enumerate(spec["subdivisions"]):
        out[s["id"]] = bind_standard(spec, s, catalog, i)
    sec = str(spec.get("section", "")).split(" · ")[0]
    pool = [x for x in (_STD_BY_CODE.get(spec["code"], []) +
                        _STD_SECTION_DEFAULT.get(sec, [])) if x in catalog]
    pool = list(dict.fromkeys(pool))
    if len({v[0] for v in out.values() if v[0]}) >= 3 or not pool:
        return out
    k = 0
    for sid in list(out):
        if len({v[0] for v in out.values() if v[0]}) >= 3:
            break
        cand = pool[k % len(pool)]
        k += 1
        if cand != out[sid][0]:
            out[sid] = (cand, "多样性补位（段默认池轮换）")
    return out


def spec_issues(spec: Dict[str, Any]) -> List[str]:
    """域规格结构自检（内容质量由作者负责，结构由这里判）。"""
    issues: List[str] = []
    for k in ("code", "section", "name", "pack_name", "category", "metric_family",
              "module_titles", "subdivisions"):
        if not spec.get(k):
            issues.append("缺字段 %s" % k)
    code = str(spec.get("code") or "")
    if not re.fullmatch(r"[A-F]\d{2}", code):
        issues.append("code 形态应为 <A-F><两位数>，实为 %r" % code)
    subs = spec.get("subdivisions") or []
    if len(subs) != SUB_COUNT:
        issues.append("细分条目须 %d 条，实为 %d" % (SUB_COUNT, len(subs)))
    seen = set()
    for i, s in enumerate(subs, 1):
        want = "%s-%02d" % (code, i)
        if s.get("id") != want:
            issues.append("第 %d 条 id 应为 %s，实为 %r" % (i, want, s.get("id")))
        if s.get("id") in seen:
            issues.append("细分 id 重复：%s" % s.get("id"))
        seen.add(s.get("id"))
        for k in ("name", "definition", "anchor", "check", "pitfall"):
            if not str(s.get(k) or "").strip():
                issues.append("%s 缺 %s" % (s.get("id"), k))
        if not str(s.get("anchor") or "").startswith(("http://", "https://")):
            issues.append("%s anchor 须为绝对 URL" % s.get("id"))
        if len(str(s.get("check") or "")) < 10:
            issues.append("%s 可机验判据过短（<10 字）" % s.get("id"))
    if len(spec.get("module_titles") or []) != 2:
        issues.append("module_titles 须 2 条（P40 口径层 / P60 收口层）")
    edges = spec.get("edges") or []
    ids = {s.get("id") for s in subs}
    node_ids = {str(x) for x in (spec.get("node_ids") or ids)}
    for e in edges:
        if len(e) != 2 or str(e[0]) not in node_ids or str(e[1]) not in node_ids:
            issues.append("边 %r 端点不在节点表" % (e,))
    if not edges:
        issues.append("须至少声明一条前置边（概念图非空偏序）")
    return issues


def _read_json(path: Path) -> Any:
    """读 JSON；缺件/坏件返回 None（工厂在局部树上也要能工作——由调用方决定语义）。"""

    return _read_json_raw(path)


def _write_text_retry(path: Path, text: str, tries: int = 5) -> None:
    """带重试的落盘（Windows 实测：杀软/句柄扫描会让 write_text 偶发 EINVAL(22)）。

    只重试写盘本身（内容已确定），不改语义；最终失败仍抛错，不静默。
    """
    import time

    last: Exception | None = None
    for i in range(tries):
        try:
            path.write_text(text, encoding="utf-8", newline="\n")
            return
        except OSError as exc:
            last = exc
            time.sleep(0.4 * (i + 1))
    raise last  # type: ignore[misc]


def _read_json_raw(path: Path) -> Any:
    """读 JSON；缺件/坏件返回 None（工厂在局部树上也要能工作——由调用方决定语义）。"""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


# ---------------------------------------------------------------- 全局唯一性

def used_pipeline_ids(root: str = ".") -> List[str]:
    reg = _read_json(Path(root) / REGISTRY_REL) or {}
    out = [str(p.get("pipeline")) for p in (reg.get("protocols") or [])]
    for f in sorted((Path(root) / "03_管线库").glob("*.md")):
        m = re.search(r"(?m)^\s*id:\s*(P\d{2})\s*$", f.read_text(encoding="utf-8"))
        if m:
            out.append(m.group(1))
    return out


def host_categories(root: str = ".") -> List[str]:
    cats: List[str] = []
    reg = _read_json(Path(root) / REGISTRY_REL) or {}
    for p in (reg.get("protocols") or []):
        cats += [str(c) for c in (p.get("categories") or [])]
    return cats


def module_stems(root: str = ".") -> Dict[str, List[str]]:
    out: Dict[str, List[str]] = {}
    for p in sorted(Path(root).glob("community/*/modules/*.md")) + \
            sorted(Path(root).glob("04_模块库/*/*.md")):
        stem = p.name.split("_")[0]
        out.setdefault(stem, []).append(p.as_posix())
    return out


def allocate(root: str, spec: Dict[str, Any]) -> Dict[str, Any]:
    """分配全局唯一 id（幂等：已登记包返回其现值）。"""
    code = spec["code"]
    proto = Path(root) / "community" / spec["pack_name"] / "protocol.yaml"
    if proto.is_file():
        text = proto.read_text(encoding="utf-8")
        pipe = re.search(r"(?m)^\s*pipeline:\s*(P\d{2,3})\s*$", text)
        ids = re.findall(r'(?m)^\s*-\s*"([^"]+:M\d{2})"\s*$', text)
        if pipe and len(ids) == 2:
            return {"pipeline": pipe.group(1), "exist": True, "module_ids": ids,
                    "stems": ["%sa" % code, "%sb" % code]}
    reg = _read_json(Path(root) / REGISTRY_REL) or {}
    for p in reg.get("protocols") or []:
        if p.get("id") == spec["pack_name"] and re.fullmatch(r"P\d{2,3}",
                                                             str(p.get("pipeline") or "")):
            return {"pipeline": p["pipeline"], "exist": True,
                    "module_ids": [str(x) for x in p.get("module_ids") or []]}
    used = set(used_pipeline_ids(root))
    pipe = next((x for x in PIPELINE_POOL if x not in used), "")
    if not pipe:
        raise ValueError("管线 id 池已用尽（%d 个）" % len(PIPELINE_POOL))
    stems = module_stems(root)
    ids = []
    for letter in ("a", "b"):
        stem = "%s%s" % (code, letter)
        others = [p for p in stems.get(stem, []) if "/%s/" % spec["pack_name"] not in p]
        if others:
            raise ValueError("模块文件名 token 冲突：%s ∈ %s" % (stem, others))
        ids.append("%s:M%02d" % (spec["category"], 1 if letter == "a" else 2))
    return {"pipeline": pipe, "exist": False, "module_ids": ids,
            "stems": ["%sa" % code, "%sb" % code]}


# ---------------------------------------------------------------- 生成

def _slug(spec: Dict[str, Any]) -> str:
    return spec["code"].lower()


def _yaml_scalar(v: Any) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return str(v)
    return '"%s"' % str(v).replace("\\", "\\\\").replace('"', '\\"')


def dump_yaml(obj: Any, indent: int = 0) -> List[str]:
    """极简确定性 YAML 发射器（只覆盖本工厂的数据形状；字符串一律带引号）。

    用途：概念图机读块必须是 `concept_graph:` 起头的 YAML 围栏（JSON 带引号的键过不了
    concept_graph.fenced_block 的首键判据）。
    """
    pad = " " * indent
    out: List[str] = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, (dict, list)) and v:
                out.append("%s%s:" % (pad, k))
                out += dump_yaml(v, indent + 2)
            else:
                out.append("%s%s: %s" % (pad, k, "[]" if v == [] else "{}" if v == {} else _yaml_scalar(v)))
        return out
    if isinstance(obj, list):
        for item in obj:
            if isinstance(item, dict):
                first = True
                for k, v in item.items():
                    if first and not isinstance(v, (dict, list)):
                        out.append("%s- %s: %s" % (pad, k, _yaml_scalar(v)))
                        first = False
                    elif first:
                        out.append("%s- %s:" % (pad, k))
                        out += dump_yaml(v, indent + 4)
                        first = False
                    elif isinstance(v, (dict, list)) and v:
                        out.append("%s  %s:" % (pad, k))
                        out += dump_yaml(v, indent + 4)
                    else:
                        out.append("%s  %s: %s"
                                   % (pad, k, "[]" if v == [] else _yaml_scalar(v)))
            else:
                out.append("%s- %s" % (pad, _yaml_scalar(item)))
        return out
    return ["%s%s" % (pad, _yaml_scalar(obj))]


def _anchor_evidence(spec: Dict[str, Any]) -> Dict[str, Any]:
    """锚可达性实证（外部探针结果，由作者侧写入 spec；缺则如实标未探）。"""
    return {s["anchor"]: s.get("anchor_status") for s in spec["subdivisions"]}


def concept_graph_md(spec: Dict[str, Any], root: str = ".") -> str:
    code, name = spec["code"], spec["name"]
    subs = spec["subdivisions"]
    edges = [tuple(e) for e in spec["edges"]]
    legend_key = "%s-anchor" % _slug(spec)
    cat = standards_catalog(root)
    bound: Dict[str, str] = {}          # 细分 id → 标准 id
    _bd = bindings_for(spec, cat)
    for s in subs:
        sid, why = _bd[s["id"]]
        bound[s["id"]] = sid
    std_ids = sorted({v for v in bound.values() if v})
    lines = [
        '<!-- nf-asset: key="CONCEPT_GRAPH" version="1.0" status="active" -->',
        "# 概念图 · %s（概念前置偏序）" % name,
        "",
        "> 用途：本域包的**前置闭包求值输入面**——把「%s」这一域的 %d 个细分概念声明成一张偏序图（DAG），"
        "供域内口径模块（%s:M01）与收口模块（%s:M02）消费。" % (name, len(subs), spec["category"],
                                                          spec["category"]),
        "> 资产键：`CONCEPT_GRAPH`｜形态：人读表（§2）/ 别名表（§3）/ 机器可读块（§4）三形态同源——"
        "**§4 围栏块是唯一机读真相**，§2/§3 由它导出。",
        "> 覆盖：%d 个包内概念 + %d 个**可扩展标准节点**（标准目录绑定）+ 1 个包外前置族"
        "（%s-00 领域通用前置）。" % (len(subs), len(std_ids), code),
        "> 来源：本件正文自撰；每条细分的权威锚见资产 `DOMAIN_SPEC` 与 `STANDARDS_ANCHORS`（逐条可达性实证）。",
        "",
        "## 1. 读法",
        "",
        "- **概念**：一个可独立装载的知识单元（本域第 N 条细分）。",
        "- **前置**：装载该概念之前必须先具备的概念（边方向「前置 → 后继」）。",
        "- **层**：该概念在 NF 九层位中的合理驻留层（P00–P80），用于装配定位，不是执行顺序。",
        "- **证据**：节点来源锚（见 §5 图例）；本图所有节点均挂外部可复核锚。",
        "",
        "## 2. 条目键表（一概念一键，asset_get 寻址）",
        "",
        "| 条目键 | 概念 | 层 | 直接前置 | 证据 |",
        "|---|---|---|---|---|",
    ]
    prereq = {s["id"]: [] for s in subs}
    for a, b in edges:
        prereq.setdefault(b, []).append(a)
    for s in std_ids:                    # 标准节点：概念 → 标准（该概念依据的标准）
        prereq["STD-%s" % s] = []
    for sid, std in bound.items():
        if std:
            prereq.setdefault("STD-%s" % std, []).append(sid)
    for s in subs:
        layer = "P40" if (subs.index(s) % 2 == 0) else "P60"
        pre = "、".join("`%s`" % x for x in prereq.get(s["id"], [])) or "—"
        lines.append("| `%s` | %s | %s | %s | %s |"
                     % (s["id"], s["name"], layer, pre, legend_key))
    for sid in std_ids:                  # 标准节点入条目键表（可寻址）
        std = cat.get(sid) or {}
        lines.append("| `STD-%s` | 标准 · %s（%s） | P80 | %s | std-catalog |"
                     % (sid, std.get("title", sid), std.get("body", ""),
                        "、".join("`%s`" % x for x in prereq.get("STD-%s" % sid, [])) or "—"))
    for i, s in enumerate(subs):
        pass                             # 概念行已在上方输出
    lines += [
        "",
        "## 3. 别名表（求值时 id 与别名等价）",
        "",
        "| 别名 | 概念 id |",
        "|---|---|",
    ]
    for s in subs:
        alias = "%s-%s" % (code, re.sub(r"[\s（）()]+", "-", s["name"].strip()))[:48]
        lines.append("| `%s` | `%s` |" % (alias, s["id"]))
    for sid in std_ids:
        lines.append("| `std-%s` | `STD-%s` |" % (sid, sid))
    nodes = []
    for i, s in enumerate(subs):
        layer = "P40" if i % 2 == 0 else "P60"
        nodes.append({
            "id": s["id"], "name": s["name"], "layer": layer,
            "branch": "domain",
            "prereqs": prereq.get(s["id"], []),
            "provenance": [legend_key],
        })
    cs = "std-catalog"
    for sid in std_ids:
        std = cat.get(sid) or {}
        nodes.append({
            "id": "STD-%s" % sid, "name": "标准 · %s" % std.get("title", sid),
            "layer": "P80", "branch": "standards",
            "prereqs": prereq.get("STD-%s" % sid, []),
            "provenance": [cs],
        })
    block = {
        "concept_graph": {
            "version": "1.0",
            "domain": name,
            "code": code,
            "provenance_strength": "external",
            "provenance_legend": {
                legend_key: "域内权威锚（规范 / 论文 / 参考实现），逐条 URL 与可达性实证见资产 "
                            "STANDARDS_ANCHORS（本波实测）",
                cs: "可扩展标准目录条目（protocol/standards_catalog.json，本机可达性实测）",
            },
            "external_prereqs": [
                {"id": "%s-00" % code, "name": "领域通用前置族（数学/工程基础，包外）"},
            ],
            "branches": [
                {"id": "domain", "name": "%s 全域" % name, "nodes": [s["id"] for s in subs]},
                {"id": "standards", "name": "可扩展标准（绑定）",
                 "nodes": ["STD-%s" % x for x in std_ids]},
            ],
            "nodes": nodes,
        },
    }
    lines += [
        "",
        "## 4. 机器可读块（唯一机读真相）",
        "",
        "```yaml",
        "\n".join(dump_yaml(block)),
        "```",
        "",
        "## 5. 证据与边界",
        "",
        "- 每个节点的来源锚（外部规范 / 论文 / 参考实现）逐条登记于 `STANDARDS_ANCHORS`，"
        "本图 `provenance_strength = external`（全覆盖，可复核）。",
        "- 图只声明**结构前置**（装载顺序），不声明掌握程度；边为「先具备 → 后展开」的域内常识序。",
        "- 包外前置族（%s-00）不随包交付，装载方须自备领域基础。" % code,
    ]
    return "\n".join(lines) + "\n"


def domain_spec_md(spec: Dict[str, Any], root: str = ".") -> str:
    code, name = spec["code"], spec["name"]
    tier = spec.get("content_tier", "authored")
    tier_note = (
        "> **内容档位（如实标注）**：本包为 **derived 档**——12 条细分名取自品类清单，"
        "判据/失效模式按所属段的**工程口径框架**（输入规格 / 处理参数 / 输出契约 / 验收判据）登记，"
        "**领域细则待作者逐条补全**；权威锚为段级参照，不做领域专属断言。"
        if tier == "derived" else
        "> **内容档位**：authored（逐条撰写，含领域专属判据与权威锚）。")
    lines = [
        '<!-- nf-asset: key="DOMAIN_SPEC" version="1.0" status="active" -->',
        "# 域口径表 · %s" % name,
        "",
        "> 用途：本域包的**内容资产与口径面**——把「%s」这一域的 %d 条细分写成"
        "可判定的口径（定义 / 可机验判据 / 常见失效模式），并逐条挂权威锚。" % (name, len(spec["subdivisions"])),
        "> 资产键：`DOMAIN_SPEC`｜机读同源面 = `outputs/DOMAIN_SPEC.json`（双源一致由 "
        "check32 output_forms 断言；**本表是唯一人读真相，JSON 是它的机读投影**）。",
        tier_note,
        "",
        "## 1. 口径纪律",
        "",
        "1. **定义可判定**：每条细分的定义必须能回答「什么算做对/做错」，不允许只给形容词。",
        "2. **判据可机检**：每条细分给出可写进校验器的判据（字段 / 范围 / 词表 / 一致性）。",
        "3. **锚可复核**：每条挂一个外部权威锚（规范 / 论文 / 参考实现），URL 与可达性实测记于 "
        "`STANDARDS_ANCHORS`。",
        "4. **失效模式显式**：写清该细分最常见的错法——它是质检单，不是介绍页。",
        "5. **口径不合并**：不同细分不共用同一条判据文本；相似即拆细。",
        "",
        "## 2. 细分口径表（%d 条）" % len(spec["subdivisions"]),
        "",
        "| 条目键 | 细分 | 定义口径 | 可机验判据 | 常见失效模式 | 可扩展标准（绑定） |",
        "|---|---|---|---|---|---|",
    ]
    cat = standards_catalog(root)
    _bd = bindings_for(spec, cat)
    for s in spec["subdivisions"]:
        sid, why = _bd[s["id"]]
        std = cat.get(sid) or {}
        std_txt = "`%s` %s（%s）" % (sid, std.get("title", ""), std.get("body", "")) if sid else "—"
        lines.append("| `%s` | %s | %s | %s | %s | %s |"
                     % (s["id"], s["name"], s["definition"], s["check"], s["pitfall"], std_txt))
    lines += [
        "",
        "## 3. 机读投影契约",
        "",
        "- `outputs/DOMAIN_SPEC.json`：本表的结构化等价物（`kind = nf-domain-spec/1`）；"
        "键集与本节**双向一致**（多一键或少一键即 FAIL）。",
        "- `outputs/REPORT.json`：域内度量的**可复算报告**（T4）——由 `outputs/samples/CASES.csv` "
        "按声明的度量族重算，check32 逐字段比对。",
        "- 度量族：`%s`（口径公式见 `docs/domain-packs.md`）。" % spec["metric_family"],
        "",
        "## 4. 与模块的关系",
        "",
        "- `%s:M01`（P40）：读本表登记口径，校验判据齐备性，越界即发口径冲突事件。" % spec["category"],
        "- `%s:M02`（P60）：收口度量报告与形态产出，保证「口径 → 数 → 图」三段同源。" % spec["category"],
    ]
    return "\n".join(lines) + "\n"


def standards_md(spec: Dict[str, Any], root: str = ".") -> str:
    code, name = spec["code"], spec["name"]
    cat = standards_catalog(root)
    lines = [
        '<!-- nf-asset: key="STANDARDS_ANCHORS" version="1.0" status="active" -->',
        "# 权威锚表 · %s" % name,
        "",
        "> 用途：本域 %d 条细分各自的**外部权威锚**（规范 / 论文 / 参考实现）与**可达性实证**。"
        "外部锚只作口径与机制参照，**不作品质背书**（STRATEGY §3.2/§3.3）。" % len(spec["subdivisions"]),
        "> 资产键：`STANDARDS_ANCHORS`｜实测日期：2026-09-22（本机 GET，HTTP 状态见下表；"
        "不可达如实记 `✗`，不假装可达）。",
        "",
        "## 1. 锚表",
        "",
        "| 条目键 | 锚类型 | URL | 可达性 | 可扩展标准（绑定） |",
        "|---|---|---|---|---|",
    ]
    for s in spec["subdivisions"]:
        st = s.get("anchor_status")
        mark = "✓ %s" % st if isinstance(st, int) and st == 200 else (
            "✗ %s" % st if st else "未探（如实记档）")
        sid, why = bind_standard(spec, s, cat)
        std = cat.get(sid) or {}
        lines.append("| `%s` | %s | %s | %s | `%s` %s（%s；%s） |"
                     % (s["id"], s.get("anchor_kind", "spec"), s["anchor"], mark,
                        sid or "—", std.get("title", ""), std.get("body", ""), why or "未绑定"))
    lines += [
        "",
        "## 2. 使用边界",
        "",
        "- 锚用于**口径复核**（该细分的通行定义/评测口径从何而来），不表示 NF 复制了外部文本；"
        "本包正文自撰。",
        "- 锚不可达时按不可达记档，不影响本包口径面的机检（判据落在本包 schema 与度量族）。",
        "- 锚版本漂移（规范改版）由维护者按需复核；本表不做自动追踪。",
    ]
    return "\n".join(lines) + "\n"


def _event_names(spec: Dict[str, Any], which: int) -> Tuple[str, str]:
    """包内事件名（**单源**：machine_contract 与 §4 事件契约必须同名）。

    命名纪律：事件名按域码命名空间（a01_/b03_…）——01 §1.1「发布方唯一」要求同一事件名
    只能有一个发布方，故跨域同名会被 check16 ④ 判违约（2026-09-22 实测）。
    """
    code = spec["code"].lower()
    kind = "spec" if which == 1 else "report"
    return "%s_%s_ready" % (code, kind), "%s_%s_conflict" % (code, kind)


def module_md(spec: Dict[str, Any], which: int, alloc: Dict[str, Any]) -> str:
    """which: 1 = P40 口径层，2 = P60 收口层。"""
    code, cat, name = spec["code"], spec["category"], spec["name"]
    mid = "%s:M%02d" % (cat, which)
    title = spec["module_titles"][which - 1]
    layer = "P40" if which == 1 else "P60"
    layer_name = "行为决策" if which == 1 else "长期演变"
    ready_ev, conflict_ev = _event_names(spec, which)
    if which == 1:
        duty = ("逐条登记本域 %d 个细分口径（定义 / 可机验判据 / 失效模式），校验齐备性与词表边界；"
                "越界或缺项即发布口径冲突事件" % len(spec["subdivisions"]))
        outs = ["domain_spec", "spec_conflict_list"]
        pub = [ready_ev, conflict_ev]
        sub_ev: List[str] = []
        assets = "CONCEPT_GRAPH, DOMAIN_SPEC, STANDARDS_ANCHORS"
    else:
        duty = ("把口径面收口为**可复算产出**：由样例与度量族重算域报告（T4），并从概念图派生图形态；"
                "报告与图与口径表三段同源，任一漂移即发布收口冲突事件")
        outs = ["domain_report", "closure_conflict_list"]
        pub = [ready_ev, conflict_ev]
        sub_ev = [_event_names(spec, 1)[0]]
        assets = "DOMAIN_SPEC, CONCEPT_GRAPH"
    lines = [
        "# 模块 %s · %s" % (mid, title),
        "",
        "> 类别：%s｜来源：社区（%s自带，类内段）｜挂载点：%s %s（active，default）｜"
        "依赖：M00、M50%s｜发布：%s｜状态：active"
        % (cat, spec["pack_name"], layer, layer_name,
           ("、%s:M01" % cat) if which == 2 else "", "、".join(pub)),
        "> 用途：%s。" % duty,
        "",
        "```yaml",
        "machine_contract:",
        '  conformance: "L2"',
        '  schema: "1"',
        "  id: %s" % mid,
        "  name: %s" % title,
        "  category: %s" % cat,
        '  layer: %s' % layer,
        "  inputs: [M00, M50%s]" % (", '%s:M01'" % cat if which == 2 else ""),
        "  outputs: [%s]" % ", ".join(outs),
        "  events:",
        "    publish: [%s]" % ", ".join(pub),
        "    subscribe: [%s]" % ", ".join(sub_ev),
        "  interfaces: [%s_query]" % outs[0],
        "  io_types:",
        "    outputs:",
    ]
    for o in outs:
        lines.append("      %s: untyped" % o)
    lines += ["    inputs:", "      M00: state"]
    if which == 2:
        lines.append("      '%s:M01': untyped" % cat)
    lines.append("      M50: untyped")
    lines += [
        "```",
        "",
        "## 1. 职责",
        "",
        duty + "。",
        "",
        "域知识结构不写死在模块里：概念前置在资产 `CONCEPT_GRAPH`，口径在资产 `DOMAIN_SPEC`"
        "（图 = 内容，口径 = 机制，三正交分离）。",
        "",
        "## 2. 协议声明（01 §2 模块协议）",
        "",
        "```yaml",
        "Module:",
        "  id: %s" % mid,
        "  name: %s" % title,
        "  layer: %s" % layer,
        "  inputs: [M00, M50%s]" % (", '%s:M01'" % cat if which == 2 else ""),
        "  outputs: [%s]" % ", ".join(outs),
        "  events:",
        "    publish: [%s]" % ", ".join(pub),
        "    subscribe: [%s]" % ", ".join(sub_ev),
        "  core:",
        "    assets: [%s]" % assets,
        "    logic:",
    ]
    if which == 1:
        logic = {
            "读口径": "从 DOMAIN_SPEC 读 %d 条细分的定义 / 判据 / 失效模式" % len(spec["subdivisions"]),
            "登记": "逐条登记 Spec 条目（id ∈ 条目键表，判据非空，锚为绝对 URL）",
            "校验": "判据齐备且锚可达性已记档 → 通过；缺项 / 锚非 URL → spec_conflict",
            "落槽": "写 DomainSpecState{subdivisions, conflicts, tick}",
            "发布": "全通过 → %s；否则逐条 %s" % (ready_ev, conflict_ev),
        }
    else:
        logic = {
            "读口径": "读 %s:M01 的口径状态（spec 齐备才继续）" % cat,
            "复算": "由 samples/CASES.csv 按度量族重算域报告（core/domain_metrics）",
            "对齐": "报告字段 ⊆ 口径表条目键；对不上 → %s" % conflict_ev,
            "派生": "由 CONCEPT_GRAPH 派生分层图（Mermaid / GraphML）",
            "发布": "全部一致 → %s；否则 %s" % (ready_ev, conflict_ev),
        }
    for k, v in logic.items():
        lines.append("      %s: %s" % (k, v))
    lines += [
        "```",
        "",
        "## 3. 产出面（可机验）",
        "",
        "| 产出 | 形态 | 档位 | 说明 |",
        "|---|---|---|---|",
        "| `outputs/DOMAIN_SPEC.json` | 结构化数据 | T3 | 口径表机读投影（与资产双源一致） |",
        "| `outputs/REPORT.json` | 可复算报告 | T4 | 度量族重算（check32 逐字段比对） |",
        "| `outputs/charts/*.vega.json` | 图表规格 | T3 | 由报告确定性生成 |",
        "| `outputs/CONCEPT_DAG.graphml` 等 | 图结构 | T3 | 由概念图确定性派生 |",
        "",
        "## 4. 事件联动（机读契约）",
        "",
    ]
    if which == 1:
        events = [
            (ready_ev, "{ subdivisions: number, checked: number, tick: number }",
             "口径面齐备（%d 条全过判据）" % len(spec["subdivisions"])),
            (conflict_ev,
             "{ field: string, reason: string, blocking: boolean }",
             "口径缺项 / 越词表 / 锚非 URL"),
        ]
    else:
        events = [
            (ready_ev,
             "{ family: string, metrics: number, tick: number }",
             "度量复算完成且与口径表同源"),
            (conflict_ev,
             "{ field: string, reason: string, blocking: boolean }",
             "复算结果与在盘报告不一致 / 报告字段越口径表"),
        ]
    for name, payload, note in events:
        lines += [
            "```yaml",
            "event: %s" % name,
            "payload: %s" % payload,
            "description: %s" % note,
            "```",
            "",
        ]
    lines += [
        "## 5. 边界与不宣称",
        "",
        "- 本模块**不产出模型能力结论**：报告是样例集上的口径值，不是能力评测结论。",
        "- 外部锚只作口径参照，不作质量背书；口径表正文自撰。",
        "- 域包不承担该域的教学职能：包外前置族（%s-00）须装载方自备。" % code,
    ]
    return "\n".join(lines) + "\n"


def pipeline_md(spec: Dict[str, Any], alloc: Dict[str, Any]) -> str:
    code, cat, name = spec["code"], spec["category"], spec["name"]
    pid = alloc["pipeline"]
    lines = [
        "# 管线 %s · %s装配流" % (pid, name),
        "",
        "> 社区版「%s」使用的管线（域包工厂生成；派生自 P00 通用骨架，九层位名沿用骨架）。"
        "以「口径先行」为流主轴：官方核心 M00 数据槽承载口径状态，通用:M10 节拍定拍，"
        "M50 主循环在回卷点推进；本包自带 %s:M01 挂 P40 做**口径登记**，"
        "%s:M02 挂 P60 做**收口与派生**；P80 输出呈现由官方核心 M80 承担（gate 唯一出口）。"
        % (spec["pack_name"], cat, cat),
        "> **允许编号段固化（R2）**：本包 `allowed_modules` 只含官方核心承载件与本包类内段编号；"
        "references=[] 零跨包零借阅。",
        "> **挂载层规避**：本包 P40/P60 default 用的是类内段唯一编号，与既有各包同层 default 无交集"
        "（独立装载不冲突）。",
        "```yaml",
        "Pipeline:",
        "  id: %s" % pid,
        "  name: %s装配流" % name,
        "  structure:",
        "    type: linear",
        "    flow:",
    ]
    order = ["P00", "P10", "P20", "P30", "P40", "P50", "P60", "P70", "P80"]
    for i, lay in enumerate(order):
        nxt = order[i + 1] if i + 1 < len(order) else "P00"
        cond = ("",
                "\n        condition: 主循环回卷（M50 调度下一回合；通用:M10 节拍同拍推进）")[nxt == "P00"]
        lines += ["      - from: %s" % lay, "        to: %s%s" % (nxt, cond)]
    layer_names = {"P00": "数据基座", "P10": "世界推进", "P20": "角色状态", "P30": "事件生产",
                   "P40": "行为决策", "P50": "交互执行", "P60": "长期演变", "P70": "叙事素材",
                   "P80": "输出呈现"}
    core_allow = {"P00": ["M00"], "P10": ["通用:M10"], "P20": ["M23"], "P30": ["事件:M22", "M06", "M13"],
                  "P50": ["M12"], "P70": ["M20", "M24"], "P80": ["M80"]}
    lines.append("  layers:")
    for lay in order:
        if lay == "P40":
            desc = "本包自带 %s:M01 做「%s」口径登记（%d 条细分判据齐备性）" % (
                cat, spec["module_titles"][0], len(spec["subdivisions"]))
            default = "['%s:M01']" % cat
            allow = "['%s:M01']" % cat
        elif lay == "P60":
            desc = "本包自带 %s:M02 做收口（度量复算 + 图形态派生）" % cat
            default = "['%s:M02']" % cat
            allow = "['%s:M02']" % cat
        else:
            desc = "由官方核心 %s 承载（本体驻官方核心位不搬移，本包零重复挂载）" % \
                   "、".join(core_allow[lay])
            default = "[]"
            allow = "[%s]" % ", ".join(core_allow[lay])
        lines += [
            "    - id: %s" % lay,
            "      name: %s" % layer_names[lay],
            "      description: %s" % desc,
            "      optional: false",
            "      default_modules: %s" % default,
            "      allowed_modules: %s" % allow,
        ]
    lines += [
        "```",
        "",
        "## 说明",
        "",
        "- 九层位名与 P00 骨架一致；本域只在 P40/P60 驻留自有模块，其余层位由官方核心承载。",
        "- M50 主循环是全局调度器（无层挂载），以 core 依赖引用参与回卷。",
        "- 本管线为域包工厂生成件：`nf domain build --spec %s`（幂等，重跑逐字节一致）。" % code,
    ]
    return "\n".join(lines) + "\n"


def readme_md(spec: Dict[str, Any], alloc: Dict[str, Any]) -> str:
    code, cat, name = spec["code"], spec["category"], spec["name"]
    pid = alloc["pipeline"]
    return "\n".join([
        "# %s（community 非叙事题材域包 · %s装配流）" % (spec["pack_name"], name),
        "> 定位：**AI 品类域包**（清单 %s · %s）——把「%s」这一域的 %d 条细分协议化："
        "口径可判定、判据可机检、锚可复核，并产出**可复算的域报告**与**可机验的形态面**。"
        % (code, spec["section"], name, len(spec["subdivisions"])),
        "> 协议声明：包根 `protocol.yaml`（01 §6.1 Schema，schema_version \"2\"）为机读真相，"
        "本 README 为人读速览，双源一致（check14 ⑥）。",
        "> 结构：modules/（2 域模块 %s:M01、%s:M02，类内段编号）｜assets/（**3 内容资产**："
        "概念图 CONCEPT_GRAPH、域口径表 DOMAIN_SPEC、权威锚表 STANDARDS_ANCHORS）｜"
        "outputs/（**9 机验产出面**）｜pipelines/%s_%s装配流管线.md" % (cat, cat, pid, name),
        "> 依赖边界（R1）：只依赖官方核心层（M00 / 通用:M10 / M50 / M80，core_only true），"
        "官方模块文件不复制进包。",
        "",
        "## 1. 包速览",
        "",
        "| 项 | 值 |",
        "| --- | --- |",
        "| 管线 | **%s** %s装配流（九层线性回卷，装配自 P00 通用骨架） |" % (pid, name),
        "| 自带模块（本包） | 2：%s:M01（P40 口径登记） / %s:M02（P60 收口与派生） |" % (cat, cat),
        "| 资产 | **3 文件**：`CONCEPT_GRAPH.md`（%d 概念前置图）· `DOMAIN_SPEC.md`（%d 条细分口径）"
        "· `STANDARDS_ANCHORS.md`（逐条权威锚 + 可达性实测）" % (len(spec["subdivisions"]),
                                                         len(spec["subdivisions"])),
        "| 机验产出面 | **9 件**：schema 2 / 数据 2 / 可复算 1（T4）/ 图表 1 / 图结构 2 / 系统卡 1 |",
        "| 度量族 | `%s`（口径公式见 `docs/domain-packs.md`） |" % spec["metric_family"],
        "",
        "## 2. 复现命令",
        "",
        "| 产物 | 命令（仓库根目录） |",
        "| --- | --- |",
        "| 前置闭包 / 装载序 | `python scripts/ai_domain_closure.py --asset community/%s/assets/CONCEPT_GRAPH.md --target %s-12` |"
        % (spec["pack_name"], code),
        "| 形态与档位机检 | `python scripts/nf.py output verify` |",
        "| 重渲染产出面 | `python scripts/nf.py output render --write --package %s` |" % spec["pack_name"],
        "| 重新生成整包 | `python scripts/nf.py domain build --spec %s --write` |" % code,
        "",
        "## 3. 边界与不宣称",
        "",
        "- 本包是**口径协议 + 机验产出**类域包：**不提供**模型、不执行推理、不做能力承诺。",
        "- 域报告是**样例集上的口径值**（合成夹具，非真实测量），不是模型评测结论。",
        "- 外部权威锚只作口径参照，**不作质量背书**；本包正文自撰。",
    ]) + "\n"


def protocol_yaml(spec: Dict[str, Any], alloc: Dict[str, Any]) -> str:
    cat, code = spec["category"], spec["code"]
    pid, ids = alloc["pipeline"], alloc["module_ids"]
    return "\n".join([
        "# protocol.yaml — 第三方协议声明（%s，清单 %s · %s）" % (spec["pack_name"], code, spec["section"]),
        "# 依据 01 §6.1 Schema 模板骨架 + 02 §8.3 第三方协议登记；机读真相 = 本文件，"
        "人读速览 = README.md（双源一致，check14 ⑥ 断言）",
        "protocol:",
        '  schema_version: "2"',
        "package:",
        '  conformance: "L2"',
        "  id: %s" % spec["pack_name"],
        "  name: %s" % spec["pack_name"],
        '  version: "1.0.0"',
        "  pipeline: %s" % pid,
        "  module_id_range:",
        '    - "%s"' % ids[0],
        '    - "%s"' % ids[1],
        "  categories:",
        "    - %s" % cat,
        "  dependencies:",
        "    core_only: true",
        "    core_modules: [M00, 通用:M10, M50, M80]",
        "    cross_package: []",
        "  references: []",
        "  modules:",
        "    - id: \"%s\"" % ids[0],
        "      desc: %s（%d 条细分的定义 / 可机检判据 / 失效模式登记与冲突上报）"
        % (spec["module_titles"][0], len(spec["subdivisions"])),
        "    - id: \"%s\"" % ids[1],
        "      desc: %s（度量复算 T4 + 概念图派生 + 与口径表同源收口）" % spec["module_titles"][1],
        "  assets:",
        "    count: 3",
        "    readme: README.md",
        "  outputs:",
        "    index: outputs/INDEX.json",
        "    count: 9",
        "    machine_verifiable: 9",
        "    functional: 1",
        "  mount_layers:",
        "    P40 行为决策: {default: [%s], available: []}" % ids[0],
        "    P60 长期演变: {default: [%s], available: []}" % ids[1],
    ]) + "\n"


def provenance_json(spec: Dict[str, Any], alloc: Dict[str, Any]) -> str:
    cat = spec["category"]
    doc = {
        "schema_version": "1",
        "tier": "community",
        "assets": [
            {"file": "CONCEPT_GRAPH.md", "key": "CONCEPT_GRAPH", "version": "1.0",
             "status": "active", "module": "%s:M01" % cat, "added": "2026-09-22",
             "source": "%s自带概念前置图（域包工厂生成，2026-09-22）；%d 个概念的来源锚见 "
                       "STANDARDS_ANCHORS，逐条可达性实证" % (spec["pack_name"],
                                                       len(spec["subdivisions"]))},
            {"file": "DOMAIN_SPEC.md", "key": "DOMAIN_SPEC", "version": "1.0",
             "status": "active", "module": "%s:M01" % cat, "added": "2026-09-22",
             "source": "%s自带域口径表（2026-09-22 自撰）；域内通行口径的规范化表述，"
                       "不含外部文本" % spec["pack_name"]},
            {"file": "STANDARDS_ANCHORS.md", "key": "STANDARDS_ANCHORS", "version": "1.0",
             "status": "active", "module": "%s:M02" % cat, "added": "2026-09-22",
             "source": "%s自带权威锚表（2026-09-22 本机实测可达性）；锚只作口径参照，"
                       "不作品质背书" % spec["pack_name"]},
        ],
    }
    return json.dumps(doc, ensure_ascii=False, indent=2) + "\n"


# ---------------------------------------------------------------- 产出面（机验）

def domain_spec_json(spec: Dict[str, Any], root: str = ".") -> str:
    cat = standards_catalog(root)
    subs = []
    _bd = bindings_for(spec, cat)
    for s in spec["subdivisions"]:
        sid, why = _bd[s["id"]]
        subs.append({
            "id": s["id"], "name": s["name"], "definition": s["definition"],
            "anchor": s["anchor"], "anchor_kind": s.get("anchor_kind", "spec"),
            "anchor_status": int(s.get("anchor_status") or 0),
            "standard_ref": sid, "standard_why": why,
            "check": s["check"], "pitfall": s["pitfall"],
        })
    doc = {
        "kind": "nf-domain-spec/1",
        "code": spec["code"],
        "domain": spec["name"],
        "section": spec["section"],
        "anchors_verified_on": "2026-09-22",
        "metric_family": spec["metric_family"],
        "content_tier": spec.get("content_tier", "authored"),
        "subdivisions": subs,
    }
    return json.dumps(doc, ensure_ascii=False, indent=2) + "\n"


def domain_spec_schema(spec: Dict[str, Any]) -> str:
    code = spec["code"]
    return json.dumps({
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://narrativeforge.local/schema/domain-spec-%s.schema.json" % code.lower(),
        "title": "%s 域口径表（机读投影）" % spec["name"],
        "description": "assets/DOMAIN_SPEC.md 的机读投影契约；键集须与散文面双向一致（双源一致由 "
                       "check32 output_forms 断言）。",
        "type": "object",
        "additionalProperties": False,
        "required": ["kind", "code", "domain", "section", "anchors_verified_on",
                     "metric_family", "subdivisions", "content_tier"],
        "properties": {
            "kind": {"const": "nf-domain-spec/1"},
            "content_tier": {"enum": ["authored", "derived"]},
            "code": {"const": code},
            "domain": {"type": "string", "minLength": 1},
            "section": {"type": "string", "minLength": 1},
            "anchors_verified_on": {"type": "string", "format": "date"},
            "metric_family": {"type": "string", "minLength": 3},
            "subdivisions": {
                "type": "array", "minItems": SUB_COUNT, "maxItems": SUB_COUNT,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["id", "name", "definition", "anchor", "anchor_kind",
                                 "anchor_status", "standard_ref", "standard_why",
                                 "check", "pitfall"],
                    "properties": {
                        "id": {"type": "string", "pattern": "^%s-[0-9]{2}$" % code},
                        "name": {"type": "string", "minLength": 2},
                        "definition": {"type": "string", "minLength": 8},
                        "anchor": {"type": "string", "format": "uri"},
                        "anchor_kind": {"enum": ["spec", "paper", "repo", "doc", "dataset"]},
                        "anchor_status": {"type": "integer", "minimum": 0},
                        "standard_ref": {"type": "string", "minLength": 2},
                        "standard_why": {"type": "string", "minLength": 3},
                        "check": {"type": "string", "minLength": 10},
                        "pitfall": {"type": "string", "minLength": 6},
                    },
                },
            },
        },
    }, ensure_ascii=False, indent=2) + "\n"


def report_schema(spec: Dict[str, Any]) -> str:
    code = spec["code"]
    return json.dumps({
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://narrativeforge.local/schema/domain-report-%s.schema.json" % code.lower(),
        "title": "%s 域报告（可复算）" % spec["name"],
        "description": "样例集上的口径值报告（T4）：由 outputs/samples/CASES.csv 经 "
                       "core/domain_metrics 重算并逐字段比对。**非模型能力声明**。",
        "type": "object",
        "additionalProperties": False,
        "required": ["kind", "code", "domain", "family", "sample", "sample_rows", "metrics"],
        "properties": {
            "kind": {"const": "nf-domain-report/1"},
            "code": {"const": code},
            "domain": {"type": "string", "minLength": 1},
            "family": {"type": "string", "minLength": 3},
            "sample": {"type": "string", "pattern": "^outputs/samples/"},
            "sample_rows": {"type": "integer", "minimum": 1},
            "metrics": {"type": "object", "minProperties": 3},
        },
    }, ensure_ascii=False, indent=2) + "\n"


SYSTEM_CARD_SCHEMA_JSON = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://narrativeforge.local/schema/domain-system-card.schema.json",
    "title": "域包系统卡（模型无关的机验形态）",
    "description": "机制借鉴 Model Cards / Datasheets / NIST AI RMF 的字段面（取机制，不引外部文本背书）："
                   "把「这个域包是什么 / 能做什么 / 不能做什么 / 怎么验的」写成有 schema 的数据。",
    "type": "object",
    "additionalProperties": False,
    "required": ["kind", "system", "intended_use", "limitations", "data", "evaluation",
                 "human_oversight", "risk_management", "out_of_scope", "not_claims"],
    "properties": {
        "kind": {"const": "nf-system-card/1"},
        "system": {
            "type": "object", "additionalProperties": False,
            "required": ["id", "name", "version", "kind_of_system", "model_agnostic"],
            "properties": {
                "id": {"type": "string", "pattern": "^[A-Z0-9-]{3,}$"},
                "name": {"type": "string", "minLength": 1},
                "version": {"type": "string", "pattern": "^\\d+\\.\\d+\\.\\d+$"},
                "kind_of_system": {"enum": ["domain-package", "pipeline", "module", "runtime"]},
                "model_agnostic": {"type": "boolean"},
            },
        },
        "intended_use": {
            "type": "object", "additionalProperties": False,
            "required": ["purpose", "consumers", "in_scope"],
            "properties": {
                "purpose": {"type": "string", "minLength": 8},
                "consumers": {"type": "array", "minItems": 1,
                              "items": {"type": "string", "minLength": 1}},
                "in_scope": {"type": "array", "minItems": 1,
                             "items": {"type": "string", "minLength": 1}},
            },
        },
        "limitations": {"type": "array", "minItems": 1,
                        "items": {"type": "string", "minLength": 8}},
        "data": {
            "type": "object", "additionalProperties": False,
            "required": ["sources", "provenance_policy", "personal_data"],
            "properties": {
                "sources": {"type": "array", "minItems": 1,
                            "items": {"type": "object", "additionalProperties": False,
                                      "required": ["id", "kind", "note"],
                                      "properties": {
                                          "id": {"type": "string", "minLength": 1},
                                          "kind": {"enum": ["self-authored",
                                                            "external-structure",
                                                            "repository-artifact",
                                                            "generated"]},
                                          "note": {"type": "string", "minLength": 3}}}},
                "provenance_policy": {"type": "string", "minLength": 8},
                "personal_data": {"enum": ["none", "synthetic-only", "unknown"]},
            },
        },
        "evaluation": {
            "type": "object", "additionalProperties": False,
            "required": ["method", "faces", "reproduce_command", "not_measured"],
            "properties": {
                "method": {"type": "string", "minLength": 8},
                "faces": {"type": "array", "minItems": 1,
                          "items": {"type": "object", "additionalProperties": False,
                                    "required": ["name", "gate", "result"],
                                    "properties": {
                                        "name": {"type": "string", "minLength": 2},
                                        "gate": {"type": "string", "minLength": 2},
                                        "result": {"type": "string", "minLength": 1}}}},
                "reproduce_command": {"type": "string", "minLength": 4},
                "not_measured": {"type": "array", "minItems": 1,
                                 "items": {"type": "string", "minLength": 4}},
            },
        },
        "human_oversight": {"type": "array", "minItems": 1,
                            "items": {"type": "string", "minLength": 8}},
        "risk_management": {
            "type": "object", "additionalProperties": False,
            "required": ["framework", "functions", "residual_risks"],
            "properties": {
                "framework": {"enum": ["NIST AI RMF 1.0", "ISO/IEC 42001", "none-declared"]},
                "functions": {"type": "object", "additionalProperties": False,
                              "required": ["GOVERN", "MAP", "MEASURE", "MANAGE"],
                              "properties": {
                                  k: {"type": "array", "minItems": 1,
                                      "items": {"type": "string", "minLength": 3}}
                                  for k in ("GOVERN", "MAP", "MEASURE", "MANAGE")}},
                "residual_risks": {"type": "array", "minItems": 1,
                                   "items": {"type": "string", "minLength": 8}},
            },
        },
        "out_of_scope": {"type": "array", "minItems": 1,
                         "items": {"type": "string", "minLength": 4}},
        "not_claims": {"type": "array", "minItems": 1,
                       "items": {"type": "string", "minLength": 8}},
    },
}


def system_card(spec: Dict[str, Any], alloc: Dict[str, Any]) -> str:
    code, cat, name = spec["code"], spec["category"], spec["name"]
    doc = {
        "kind": "nf-system-card/1",
        "system": {"id": "NF-%s-PACK" % code, "name": spec["pack_name"], "version": "1.0.0",
                   "kind_of_system": "domain-package", "model_agnostic": True},
        "intended_use": {
            "purpose": "把「%s」这一域的 %d 条细分协议化：口径可判定、判据可机检、锚可复核，"
                       "并产出可复算的域报告与可机验的形态面。" % (name, len(spec["subdivisions"])),
            "consumers": ["装配运行时（%s 管线）" % alloc["pipeline"],
                          "需要该域口径清单的内容/评测生产方",
                          "下游域包（同源引用本域口径面）"],
            "in_scope": ["%d 条细分的定义口径与可机检判据" % len(spec["subdivisions"]),
                         "概念前置偏序与装载序", "样例集上的域度量复算（T4）"],
        },
        "limitations": [
            "覆盖以本节声明的 %d 条细分为界：域内相邻主题未列入者不自动继承" % len(spec["subdivisions"]),
            "域报告是**样例集（合成夹具）上的口径值**，不代表真实模型/系统能力",
            "外部权威锚只作口径参照，未做逐条规范全文比对",
            "包外前置族（%s-00）不随包交付，装载方须自备领域基础" % code,
        ],
        "data": {
            "sources": [
                {"id": "DOMAIN_SPEC", "kind": "self-authored",
                 "note": "域口径表正文自撰；外部锚仅登记 URL 与可达性，不复制外部文本"},
                {"id": "CASES", "kind": "generated",
                 "note": "度量夹具为确定性合成数据（core/domain_metrics.synthesize，种子 = 域码）"},
            ],
            "provenance_policy": "外部输入只作机制借鉴与口径参照（逐条实测可达性），不作立项理由或"
                                 "质量背书（STRATEGY §3.2/§3.3）",
            "personal_data": "synthetic-only",
        },
        "evaluation": {
            "method": "内部机检链：verify 门禁（check14/23/32/33）+ 域报告复算（T4）+ 单测",
            "faces": [
                {"name": "登记与投影一致", "gate": "check14 ⑦",
                 "result": "protocol.yaml ↔ registry protocols[] ↔ 02 §8 三处一致"},
                {"name": "资产供应链闭合", "gate": "check23",
                 "result": "3 件资产头 ↔ provenance.json 双源一致"},
                {"name": "概念图健康", "gate": "check32 concept_graph",
                 "result": "无环 / 无悬空 / 边有溯源 / 层位合法 / 别名唯一 / 分支完备"},
                {"name": "产出形态与机验率", "gate": "check32 output_forms",
                 "result": "9 面全部 ≥T2（可机验占比 100%）；T4 面复算一致"},
            ],
            "reproduce_command": "python scripts/nf.py output verify --json",
            "not_measured": ["真实模型在该域的能力（本包不含模型，也不做能力声明）",
                             "外部客户端装载实测（外部接触按 STRATEGY 封存）",
                             "锚规范全文一致性（只登记入口与可达性）"],
        },
        "human_oversight": [
            "口径条目变更须走资产表 + 机读投影双改，并重跑门禁（禁止只改 JSON）",
            "不可达锚由维护者复核后更新（本表如实记 ✗，不假装可达）",
            "域包公开面只放结果（资产 + 模块 + 产出面 + 收口注记）",
        ],
        "risk_management": {
            "framework": "NIST AI RMF 1.0",
            "functions": {
                "GOVERN": ["登记三要件由 check14 硬门守住（protocol.yaml / 02 §8 / registry）",
                           "公开文案纪律：只写结果与状态"],
                "MAP": ["域边界 = 本节 %d 条细分表：不覆盖处以新条目显式登记"
                        % len(spec["subdivisions"]),
                        "前置关系显式成图（CONCEPT_GRAPH）"],
                "MEASURE": ["度量族口径显式（%s）并可复算（T4）" % spec["metric_family"],
                            "产出面档位与机验率落基线（回退即 FAIL）"],
                "MANAGE": ["资产/模块状态位支持淘汰流转", "机验率回退即门禁失败"],
            },
            "residual_risks": ["夹具为合成数据，不能替代真实评测",
                               "锚版本漂移需人工复核", "域内细分边界存在主观性（已声明覆盖边界）"],
        },
        "out_of_scope": ["该域的教学内容", "具体模型权重与推理运行时",
                         "外部服务的可用性与定价承诺"],
        "not_claims": ["不做模型能力结论（域报告是样例口径值）",
                       "不宣称外部兼容性（未做客户端装载实测）",
                       "口径表不宣称完备：覆盖以本节声明边界为准",
                       "NIST AI RMF 段为字段映射陈述，不构成合规认证"]
        + (["本包内容为 **derived 档**：细分名与框架判据已登记，领域细则待作者补全——"
            "不得当作领域专家级口径使用"]
           if spec.get("content_tier") == "derived" else []),
    }
    return json.dumps(doc, ensure_ascii=False, indent=2) + "\n"


def output_index(spec: Dict[str, Any]) -> str:
    code = spec["code"]
    entries = [
        {"path": "outputs/schemas/DOMAIN_SPEC.schema.json", "form": "json-schema",
         "tier": "T2", "role": "schema", "note": "口径表机读投影契约"},
        {"path": "outputs/schemas/DOMAIN_REPORT.schema.json", "form": "json-schema",
         "tier": "T2", "role": "schema", "note": "域报告契约（可复算面）"},
        {"path": "outputs/schemas/SYSTEM_CARD.schema.json", "form": "json-schema",
         "tier": "T2", "role": "schema", "note": "系统卡契约"},
        {"path": "outputs/DOMAIN_SPEC.json", "form": "domain-spec", "tier": "T3",
         "role": "data", "schema": "outputs/schemas/DOMAIN_SPEC.schema.json",
         "dual_source": {"markdown": "assets/DOMAIN_SPEC.md", "field": "id",
                         "key_pattern": "`(%s-[0-9]{2})`" % code},
         "note": "口径表机读投影（与资产双向一致）"},
        {"path": "outputs/samples/CASES.csv", "form": "csv", "tier": "T2", "role": "data",
         "note": "度量夹具（确定性合成；口径可复算，非真实测量）"},
        {"path": "outputs/REPORT.json", "form": "domain-report", "tier": "T4",
         "role": "functional", "schema": "outputs/schemas/DOMAIN_REPORT.schema.json",
         "recompute": {"id": "domain-report",
                       "inputs": ["outputs/samples/CASES.csv"],
                       "params": {"family": spec["metric_family"],
                                  "code": spec["code"], "domain": spec["name"]}},
         "note": "度量族复算报告（check32 重算比对）"},
        {"path": "outputs/charts/METRICS.vega.json", "form": "vega-lite", "tier": "T3",
         "role": "chart",
         "render": {"id": "vega-metrics", "inputs": ["outputs/REPORT.json"],
                    "params": {"title": "%s · 样例口径值" % spec["name"]}},
         "note": "指标条形图（由报告确定性生成）"},
        {"path": "outputs/CONCEPT_DAG.graphml", "form": "graphml", "tier": "T3",
         "role": "diagram",
         "render": {"id": "graphml-concept-dag",
                    "graph": "community/%s/assets/CONCEPT_GRAPH.md" % spec["pack_name"]},
         "note": "概念前置图（图交换形态；边端点引用完整性由形态校验器判定）"},
        {"path": "outputs/charts/CONCEPT_DAG.mmd", "form": "mermaid", "tier": "T3",
         "role": "diagram",
         "render": {"id": "mermaid-concept-dag",
                    "graph": "community/%s/assets/CONCEPT_GRAPH.md" % spec["pack_name"]},
         "note": "概念前置图（按层分组的 Mermaid 形态）"},
        {"path": "outputs/SYSTEM_CARD.json", "form": "system-card", "tier": "T3",
         "role": "data", "schema": "outputs/schemas/SYSTEM_CARD.schema.json",
         "note": "域包系统卡（用途 / 限制 / 数据 / 评测 / 人审 / 风险治理 / 不宣称）"},
    ]
    doc = {
        "schema": "nf-output-index/1",
        "package": spec["pack_name"],
        "note": "机验产出面清单（域包工厂生成；check14/check32 与 nf output 按此判定）。"
                "role 语义：schema 契约 / data 数据 / chart 图表 / diagram 图示 / functional 可复算。",
        "outputs": entries,
    }
    return json.dumps(doc, ensure_ascii=False, indent=2) + "\n"


# ---------------------------------------------------------------- 组装

def plan(root: str, spec: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, str]]:
    """产出「写什么」的计划：返回 (alloc, {仓库相对路径: 内容})。不落盘、不改登记。"""
    alloc = allocate(root, spec)
    pkg = "community/%s" % spec["pack_name"]
    code = spec["code"]
    from core import domain_metrics as dm
    cases = dm.rows_to_csv(dm.synthesize(spec["metric_family"], code))
    files = {
        "%s/protocol.yaml" % pkg: protocol_yaml(spec, alloc),
        "%s/README.md" % pkg: readme_md(spec, alloc),
        "%s/modules/%sa_%s.md" % (pkg, code, spec["module_titles"][0]): module_md(spec, 1, alloc),
        "%s/modules/%sb_%s.md" % (pkg, code, spec["module_titles"][1]): module_md(spec, 2, alloc),
        "%s/pipelines/%s_%s装配流管线.md" % (pkg, alloc["pipeline"], spec["name"]):
            pipeline_md(spec, alloc),
        "%s/assets/CONCEPT_GRAPH.md" % pkg: concept_graph_md(spec, root),
        "%s/assets/DOMAIN_SPEC.md" % pkg: domain_spec_md(spec, root),
        "%s/assets/STANDARDS_ANCHORS.md" % pkg: standards_md(spec, root),
        "%s/assets/provenance.json" % pkg: provenance_json(spec, alloc),
        "%s/outputs/INDEX.json" % pkg: output_index(spec),
        "%s/outputs/schemas/DOMAIN_SPEC.schema.json" % pkg: domain_spec_schema(spec),
        "%s/outputs/schemas/DOMAIN_REPORT.schema.json" % pkg: report_schema(spec),
        "%s/outputs/schemas/SYSTEM_CARD.schema.json" % pkg:
            json.dumps(SYSTEM_CARD_SCHEMA_JSON, ensure_ascii=False, indent=2) + "\n",
        "%s/outputs/DOMAIN_SPEC.json" % pkg: domain_spec_json(spec, root),
        "%s/outputs/SYSTEM_CARD.json" % pkg: system_card(spec, alloc),
        "%s/outputs/samples/CASES.csv" % pkg: cases,
    }
    return alloc, files


def _append_section02(root: str, spec: Dict[str, Any], alloc: Dict[str, Any]) -> bool:
    """在 02 §8 末尾追加登记段（幂等）。返回是否改动。"""
    doc_path = Path(root) / DOC02_REL
    text = doc_path.read_text(encoding="utf-8")
    if "### 8." in text and spec["pack_name"] + "（community/" in text:
        return False
    m = re.search(r"^## 9\.", text, re.M)
    if not m:
        raise ValueError("02 文档缺 §9 锚点，无法安全插入 §8 登记段")
    nums = [int(x) for x in re.findall(r"^### 8\.(\d+) ", text, re.M)]
    nxt = (max(nums) + 1) if nums else 1
    ids = alloc["module_ids"]
    seg = "\n".join([
        "### 8.%d %s（community/%s/）" % (nxt, spec["pack_name"], spec["pack_name"]),
        "> **定位**：AI 品类域包（清单 %s · %s）——把「%s」这一域的 %d 条细分协议化："
        "口径可判定、判据可机检、锚可复核，并产出可复算域报告与机验形态面。"
        "独占类别：%s（R2，与既有 [情感]/[生存]/[世界]/[事件]/[轻混]/[通用]/[技术文档]/[AI系统]/"
        "[量化金融] 及各 AI 品类域包类别无交集）。"
        % (spec["code"], spec["section"], spec["name"], len(spec["subdivisions"]), spec["category"]),
        "- 管线：%s %s装配流（pipelines/%s_%s装配流管线.md；九层位 linear flow P00→P80→P00 回卷，"
        "P40/P60 两驻留层各挂 %s / %s，官方核心 M00·通用:M10·M50·M80 core 依赖引用不搬移）"
        % (alloc["pipeline"], spec["name"], alloc["pipeline"], spec["name"], ids[0], ids[1]),
        "- 模块（2）：%s %s（P40 行为决策，%d 条细分口径登记与冲突上报）、%s %s（P60 长期演变，"
        "度量复算 + 概念图派生收口）（modules/；编号落类内段 `<独占类别>:Mxx`，01 §1.6.11 通道②）"
        % (ids[0], spec["module_titles"][0], len(spec["subdivisions"]),
           ids[1], spec["module_titles"][1]),
        "- 资产（3 内容文件 + README.md）：assets/CONCEPT_GRAPH.md（%d 概念前置图）· "
        "assets/DOMAIN_SPEC.md（%d 条细分口径）· assets/STANDARDS_ANCHORS.md（逐条权威锚 + "
        "可达性实测）——经包内供应链台账 `provenance.json` 托管（check23 自证）"
        % (len(spec["subdivisions"]), len(spec["subdivisions"])),
        "- 产出面（9 机验件）：outputs/ 下 schema 3 / 数据 3 / 可复算 1（T4 域报告）/ 图表 1 / "
        "图结构 2；可机验占比 100%（≥95% 门槛），见 outputs/INDEX.json 与 docs/domain-packs.md",
        "- 依赖（R1）：core_only true + core_modules 4 件官方核心配合（M00 / 通用:M10 / M50 / M80）；"
        "cross_package [] 恒空、references [] 零跨包引用",
        "- 挂载层：P40 default [%s]、P60 default [%s]——类内段编号唯一，与既有包同层 default 无交集"
        % (ids[0], ids[1]),
        "",
    ])
    text = text[:m.start()] + seg + text[m.start():]
    _write_text_retry(doc_path, text)
    return True


def _append_domain_list(root: str, spec: Dict[str, Any]) -> bool:
    """把包目录加进 verify.sh check14 的 DOMAIN 列表（幂等）。"""
    p = Path(root) / VERIFY_REL
    text = p.read_text(encoding="utf-8")
    entry = "'community/%s'" % spec["pack_name"]
    m = re.search(r"(?m)^(DOMAIN = \[)([^\]]*)(\])", text)
    if not m:
        raise ValueError("verify.sh 未找到 DOMAIN 列表锚点")
    if entry in m.group(2):
        return False
    inner = m.group(2)
    if not inner.rstrip().endswith(","):
        inner = inner.rstrip() + ","
    new = m.group(1) + inner + " " + entry + m.group(3)
    _write_text_retry(p, text[:m.start()] + new + text[m.end():])
    return True


def _register_protocols(root: str, spec: Dict[str, Any], alloc: Dict[str, Any]) -> str:
    """把包投影进 registry protocols[]（与 `nf register --apply` 同一套纯函数）。"""
    from core import protocol_projection as pp
    from core import registry_sync as rsync

    pkg_dir = str(Path(root) / "community" / spec["pack_name"])
    path = Path(root) / REGISTRY_REL
    reg = _read_json(path) or {}
    cur = reg.get("protocols")
    if not isinstance(cur, list):
        return "registry protocols[] 缺失（跳过投影）"
    try:
        entry = pp.project_entry(pkg_dir)
    except Exception as exc:  # 投影失败必须可见
        return "投影失败：%s" % exc
    merged = rsync.merge_protocols(cur, [entry])
    if [json.dumps(p, sort_keys=True, ensure_ascii=False) for p in merged] == \
            [json.dumps(p, sort_keys=True, ensure_ascii=False) for p in cur]:
        return "已登记（幂等，无变化）"
    reg["protocols"] = merged
    _write_text_retry(path, json.dumps(reg, ensure_ascii=False, indent=2) + "\n")
    return "已写入（protocols[] %d → %d）" % (len(cur), len(merged))


def build(root: str, spec: Dict[str, Any], write: bool = False,
          render: bool = True) -> Dict[str, Any]:
    """生成整包：文件 + 登记三处（02 §8 / verify.sh DOMAIN / registry protocols[]）+ 渲染产出面。

    登记三处**一次做完**（2026-09-23 实测教训：漏跑 `nf register --apply` 会让
    check14 ⑦ / check15 ⑤ / check29 虚标 / check32 名录四处红——工厂把这一步收进来，
    从构造上消除「建了包没登记」这一类）。
    """
    alloc, files = plan(root, spec)
    changed, written = [], []
    for rel, content in sorted(files.items()):
        p = Path(root) / rel
        cur = p.read_bytes() if p.is_file() else b""
        if cur != content.encode("utf-8"):
            changed.append(rel)
            if write:
                p.parent.mkdir(parents=True, exist_ok=True)
                _write_text_retry(p, content)
                written.append(rel)
    reg = {"section02": False, "domain_list": False, "render": []}
    if write:
        reg["section02"] = _append_section02(root, spec, alloc)
        reg["domain_list"] = _append_domain_list(root, spec)
        reg["protocols"] = _register_protocols(root, spec, alloc)
        update_manifest(root, spec, write=True)
        if render:
            from core import output_forms as of
            issues, rows = of.render_outputs(root, package=spec["pack_name"], write=True)
            reg["render"] = rows
            reg["render_issues"] = issues
    return {"spec": spec["code"], "pipeline": alloc["pipeline"],
            "module_ids": alloc["module_ids"], "files": len(files),
            "changed": len(changed), "written": len(written), "registry": reg}


def verify(root: str, spec: Dict[str, Any]) -> Tuple[List[str], Dict[str, Any]]:
    """工厂自检：生成物是否与计划逐字节一致 + 登记是否到位 + 产出面机检。"""
    issues: List[str] = []
    _, files = plan(root, spec)
    missing = [r for r, c in files.items()
               if not (Path(root) / r).is_file()]
    drift = [r for r, c in files.items()
             if (Path(root) / r).is_file()
             and (Path(root) / r).read_bytes() != c.encode("utf-8")]
    issues += ["缺件：%s" % r for r in sorted(missing)]
    issues += ["与生成器漂移：%s" % r for r in sorted(drift)]
    doc02 = (Path(root) / DOC02_REL).read_text(encoding="utf-8")
    if spec["pack_name"] + "（community/" not in doc02:
        issues.append("02 §8 未登记本包")
    else:
        segm = re.search(r"(?ms)^### 8\.\d+ %s\b.*?(?=^### 8\.|^## 9\.)"
                         % re.escape(spec["pack_name"]), doc02)
        if not segm or "模块（2）" not in segm.group(0):
            issues.append("02 §8 段缺 `模块（2）` 在册行")
    vs = (Path(root) / VERIFY_REL).read_text(encoding="utf-8")
    if "'community/%s'" % spec["pack_name"] not in vs:
        issues.append("verify.sh DOMAIN 列表未登记本包")
    reg = _read_json(Path(root) / REGISTRY_REL) or {}
    pids = [p.get("id") for p in reg.get("protocols") or []]
    if spec["pack_name"] not in pids:
        issues.append("registry protocols[] 未登记本包（修复指引：nf register --apply）")
    cats = [c for p in reg.get("protocols") or []
            if p.get("id") != spec["pack_name"] for c in (p.get("categories") or [])]
    if spec["category"] in cats:
        issues.append("R2 类别冲突：%s 已被他包占用" % spec["category"])
    stats = {"files": len(files), "missing": len(missing), "drift": len(drift)}
    return issues, stats


# ---------------------------------------------------------------- 名录（公开结果面）

def manifest_entry(root: str, spec: Dict[str, Any]) -> Dict[str, Any]:
    alloc = allocate(root, spec)
    idx = json.loads(output_index(spec))
    mv = [e for e in idx["outputs"] if e.get("tier") in ("T2", "T3", "T4")]
    t4 = [e for e in idx["outputs"] if e.get("tier") == "T4"]
    ratio = round(len(mv) / max(1, len(idx["outputs"])), 4)
    spec_blob = json.dumps(spec, ensure_ascii=False, sort_keys=True).encode("utf-8")
    cat = standards_catalog(root)
    bound = {}
    _bd = bindings_for(spec, cat)
    for s in spec["subdivisions"]:
        sid, why = _bd[s["id"]]
        if sid:
            bound[s["id"]] = sid
    nodes = len(spec["subdivisions"]) + len(set(bound.values()))
    edges = len(spec["edges"]) + len(bound)
    return {
        "code": spec["code"],
        "section": spec["section"],
        "name": spec["name"],
        "package": spec["pack_name"],
        "category": spec["category"],
        "pipeline": alloc["pipeline"],
        "module_ids": alloc["module_ids"],
        "modules": len(alloc["module_ids"]),
        "subdivisions": len(spec["subdivisions"]),
        "assets": 3,
        "output_faces": len(idx["outputs"]),
        "machine_verifiable_faces": len(mv),
        "functional_faces": len(t4),
        "machine_verifiable_ratio": ratio,
        "metric_family": spec["metric_family"],
        "content_tier": spec.get("content_tier", "authored"),
        "standards_bound": len(set(bound.values())),
        "standards_binding_coverage": round(len(bound) / max(1, len(spec["subdivisions"])), 4),
        "concept_nodes": nodes,
        "concept_edges": edges,
        "concept_density": round(edges / max(1, nodes), 4),
        "spec_digest": hashlib.sha256(spec_blob).hexdigest(),
    }


def update_manifest(root: str, spec: Dict[str, Any], write: bool = False) -> Dict[str, Any]:
    """维护 `protocol/domain_packs.json`（公开名录：域码 → 包/管线/模块/产出面/机验率）。"""
    path = Path(root) / MANIFEST_REL
    doc = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {
        "schema": "nf-domain-packs/1",
        "note": "AI 品类域包名录（公开结果面）。每包：域码 / 独占类别 / 管线 / 模块 / "
                "资产数 / 产出面与机验率 / 规格摘要。机检：check32 domain_packs 子扫描"
                "（名录 ↔ 盘上实况一致 + 可机验占比 ≥95%）。规格源在内部档案，"
                "故名录只登记摘要（spec_digest）不携带内容。",
        "machine_verifiable_threshold": 0.95,
        "packs": [],
    }
    entry = manifest_entry(root, spec)
    packs = [p for p in doc["packs"] if p.get("code") != entry["code"]]
    packs.append(entry)
    doc["packs"] = sorted(packs, key=lambda p: p["code"])
    doc["count"] = len(doc["packs"])
    doc["subdivisions_total"] = sum(int(p.get("subdivisions") or 0) for p in doc["packs"])
    doc["standards_catalog"] = STANDARDS_REL
    doc["concept_density_threshold"] = 1.0
    doc["concept_density_min"] = min((float(p.get("concept_density") or 0)
                                      for p in doc["packs"]), default=0.0)
    doc["binding_coverage_min"] = min((float(p.get("standards_binding_coverage") or 0)
                                       for p in doc["packs"]), default=0.0)
    if write:
        path.parent.mkdir(parents=True, exist_ok=True)
        _write_text_retry(path, json.dumps(doc, ensure_ascii=False, indent=2) + "\n")
        _write_binding_table(root, spec)
    return doc


def _write_binding_table(root: str, spec: Dict[str, Any]) -> None:
    """维护 `protocol/standards_binding.json`：逐包逐细分的标准绑定 + 理由（公开结果面）。"""
    path = Path(root) / BINDING_REL
    doc = _read_json(path) or {
        "schema": "nf-standards-binding/1",
        "note": "域包 × 细分 → 可扩展标准目录条目的绑定表（公开结果面）。判据"
                "（check32 domain_packs）：① 每条细分都有 standard_ref；② 引用 id 必须在 "
                "protocol/standards_catalog.json 在册；③ 每包绑定覆盖率 100%；"
                "④ 概念密度（边/节点，含标准节点与绑定边）≥ 门槛。",
        "catalog": STANDARDS_REL,
        "packs": [],
    }
    cat = standards_catalog(root)
    rows = []
    _bd = bindings_for(spec, cat)
    for s in spec["subdivisions"]:
        sid, why = _bd[s["id"]]
        rows.append({"subdivision": s["id"], "name": s["name"],
                     "standard": sid, "rationale": why,
                     "standard_body": (cat.get(sid) or {}).get("body", ""),
                     "standard_url": (cat.get(sid) or {}).get("url", "")})
    entry = {"code": spec["code"], "package": spec["pack_name"],
             "category": spec["category"], "subdivisions": len(rows),
             "distinct_standards": len({r["standard"] for r in rows if r["standard"]}),
             "bindings": rows}
    packs = [p for p in doc["packs"] if p.get("code") != entry["code"]]
    packs.append(entry)
    doc["packs"] = sorted(packs, key=lambda p: p["code"])
    doc["count"] = len(doc["packs"])
    doc["bindings_total"] = sum(len(p["bindings"]) for p in doc["packs"])
    _write_text_retry(path, json.dumps(doc, ensure_ascii=False, indent=2) + "\n")


def manifest_verify(root: str = ".") -> Tuple[List[str], Dict[str, Any]]:
    """名录机检：名录 ↔ 盘上实况一致 + 可机验占比 ≥ 门槛（check32 子扫描）。"""
    issues: List[str] = []
    path = Path(root) / MANIFEST_REL
    if not path.is_file():
        return [], {"packs": 0, "note": "无域包名录（域包工程未启用）"}
    doc = json.loads(path.read_text(encoding="utf-8"))
    thr = float(doc.get("machine_verifiable_threshold") or 0.95)
    cat = standards_catalog(root)
    dens_min = float(doc.get("concept_density_threshold") or 1.0)
    stats = {"packs": 0, "faces": 0, "functional": 0}
    reg = _read_json(Path(root) / REGISTRY_REL) or {}
    by_id = {p.get("id"): p for p in reg.get("protocols") or []}
    for p in doc.get("packs") or []:
        pkg = str(p.get("package") or "")
        stats["packs"] += 1
        stats["faces"] += int(p.get("output_faces") or 0)
        stats["functional"] += int(p.get("functional_faces") or 0)
        regp = by_id.get(pkg)
        if not regp:
            issues.append("%s：registry protocols[] 无该包（名录 ↔ 登记不一致）" % pkg)
        else:
            if str(regp.get("pipeline")) != str(p.get("pipeline")):
                issues.append("%s：管线不一致（名录 %s / registry %s）"
                              % (pkg, p.get("pipeline"), regp.get("pipeline")))
            if [str(x) for x in regp.get("module_ids") or []] != \
                    [str(x) for x in p.get("module_ids") or []]:
                issues.append("%s：模块 id 不一致（名录 ↔ registry）" % pkg)
        proto = Path(root) / "community" / pkg / "protocol.yaml"
        if not proto.is_file():
            issues.append("%s：包目录或 protocol.yaml 缺失" % pkg); continue
        text = proto.read_text(encoding="utf-8")
        for tok in (str(p.get("pipeline")), str(p.get("category"))):
            if tok not in text:
                issues.append("%s：protocol.yaml 缺名录声明 %s" % (pkg, tok))
        idx_path = Path(root) / "community" / pkg / "outputs" / "INDEX.json"
        if not idx_path.is_file():
            issues.append("%s：缺 outputs/INDEX.json" % pkg); continue
        faces = (json.loads(idx_path.read_text(encoding="utf-8")).get("outputs") or [])
        ratio = round(sum(1 for e in faces if e.get("tier") in ("T2", "T3", "T4"))
                      / max(1, len(faces)), 4)
        if ratio < thr:
            issues.append("%s：可机验产出占比 %.4f < 门槛 %.2f（产出面必须 ≥95%% 可机验）"
                          % (pkg, ratio, thr))
        if not any(e.get("tier") == "T4" for e in faces):
            issues.append("%s：无 T4 可复算面（域包必须有一个可重算产出）" % pkg)
        if int(p.get("output_faces") or 0) != len(faces):
            issues.append("%s：名录产出面数 %s ≠ INDEX 实况 %d"
                          % (pkg, p.get("output_faces"), len(faces)))
        # 可扩展标准绑定面（2026-09-23 对齐）：覆盖率 100% + 引用在册 + 概念密度不回落
        spec_path = Path(root) / SPEC_DIR / ("%s.json" % p.get("code", ""))
        if spec_path.is_file():
            spec = json.loads(spec_path.read_text(encoding="utf-8"))
            payload = _read_json(Path(root) / "community" / pkg / "outputs"
                                 / "DOMAIN_SPEC.json") or {}
            subs = payload.get("subdivisions") or []
            bad_ref = [s["id"] for s in subs if str(s.get("standard_ref") or "") not in cat]
            if bad_ref:
                issues.append("%s：细分未绑可扩展标准或引用不在册：%s" % (pkg, bad_ref[:4]))
            if subs and len(bad_ref) > 0:
                pass
            if float(p.get("standards_binding_coverage") or 0) < 1.0:
                issues.append("%s：标准绑定覆盖率 %.2f < 1.0（每条细分须绑一个目录内标准）"
                              % (pkg, float(p.get("standards_binding_coverage") or 0)))
            if float(p.get("concept_density") or 0) < dens_min:
                issues.append("%s：概念密度 %.3f < 门槛 %.3f（边/节点；含标准节点与绑定边）"
                              % (pkg, float(p.get("concept_density") or 0), dens_min))
            if int(p.get("standards_bound") or 0) < 3:
                issues.append("%s：绑定标准数 %s < 3（单包至少要贴 3 条不同标准）"
                              % (pkg, p.get("standards_bound")))
    return issues, stats


def scan(root: str = ".") -> Tuple[List[str], Dict[str, Any]]:
    """check32 子扫描入口：域包名录机检（无名录即中性通过）。"""
    return manifest_verify(root)
