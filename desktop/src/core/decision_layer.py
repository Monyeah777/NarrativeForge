"""决策层端口（机制借鉴一句式：非自回归 typed-decision 模型用 choice / noul / score 三原语
报「候选集上的概率 + argmax」，不做生成、不执行动作）。

为什么 NF 需要这一层：装配/质检/流转的**选择**目前散在规则与人的判断里（选哪些模块、走哪条
管线、这一步该不该继续）。把它们写成**类型化问题**交给决策模型，好处是三件可核验的事：
① 问题与答案有 schema（模型不得自造候选、不得只回一句自然语言）；
② 每个决策都带概率与来源（可审计、可回放）；
③ 模型不可用时**abstained**，绝不用猜测补齐（fail-closed）。

架构纪律（STRATEGY「定内容，不定模型」）：
- 本模块是**端口**：模型在端口之外，换模型不改协议、不改内容资产；
- 门禁只用 `stub`（离线确定性、`calibrated=false`）；真实模型（本地 HTTP 或远程 API）
  一律非门禁任务，且经 `protocol/decision_layer.json` 声明后才可用；
- 纯标准库（`urllib` + `json`），无第三方硬依赖。

用法：
    from core import decision_layer as dl
    req = {"state": "…", "questions": {"pick": {"type": "choice", "options": ["A", "B"]}}}
    out = dl.decide(req, adapter="stub")          # 门禁/CI
    out = dl.decide(req, adapter="systemone-http", endpoint="http://127.0.0.1:8791/v1/systemone")
"""
from __future__ import annotations

import hashlib
import json
import os
import time
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional, Tuple

DECL_REL = "protocol/decision_layer.json"
SCHEMA = "nf-decision-layer/1"
RESPONSE_SCHEMA = "nf-decision-response/1"
PRIMITIVES = ("choice", "noul", "score")
#: 概率求和容差（schema 级判据）。实证来源（2026-09-22，真模型）：Laya 系服务把概率
#: **四舍五入到 4 位小数**回传（三次问题实测和 = 0.9999），而残差 1e-4 属**舍入**而非错误——
#: 若坚持 1e-6，等于把每一个真实校准模型都拒在门外。故取 1e-3（4 位小数的量化误差上界），
#: 且适配器侧**先归一化再入档**、把原始和记进 meta（判据放松，证据不放松）。
PROB_TOL = 1e-3


# ---------------------------------------------------------------- 声明面

def load_decl(root: str = ".") -> Dict[str, Any]:
    p = os.path.join(root, DECL_REL)
    if not os.path.isfile(p):
        return {}
    with open(p, encoding="utf-8") as fh:
        return json.load(fh)


def adapter_ids(root: str = ".") -> List[str]:
    return [str(a.get("id")) for a in (load_decl(root).get("adapters") or [])]


def adapter_spec(root: str, adapter: str) -> Dict[str, Any]:
    for a in load_decl(root).get("adapters") or []:
        if str(a.get("id")) == adapter:
            return a
    return {}


# ---------------------------------------------------------------- 形状校验

def request_issue(req: Any) -> str:
    """请求体检 → 违规说明（空串 = 合规）。"""
    if not isinstance(req, dict):
        return "请求须为对象"
    if not isinstance(req.get("state"), str) or not req["state"].strip():
        return "缺 state（决策层只对给定的状态做判断）"
    qs = req.get("questions")
    if not isinstance(qs, dict) or not qs:
        return "缺 questions（须至少一个问题）"
    for name, q in qs.items():
        if not isinstance(q, dict):
            return "问题 %s 须为对象" % name
        ptype = q.get("type")
        if ptype not in PRIMITIVES:
            return "问题 %s 的 type 越词表：%r（允许 %s）" % (name, ptype, "/".join(PRIMITIVES))
        if ptype == "choice":
            opts = q.get("options")
            if not isinstance(opts, list) or len(opts) < 2:
                return "choice 问题 %s 须给 ≥2 个候选（候选集由调用方提供）" % name
            if not all(isinstance(o, str) and o for o in opts):
                return "choice 问题 %s 的候选须为非空字符串" % name
            if len(set(opts)) != len(opts):
                return "choice 问题 %s 的候选取值重复" % name
        if ptype == "score":
            levels = q.get("levels")
            if not isinstance(levels, list) or len(levels) < 2:
                return "score 问题 %s 须给 ≥2 个有序等级" % name
    return ""


def response_issue(out: Any, req: Dict[str, Any]) -> str:
    """应答体检 → 违规说明（空串 = 合规）。"""
    if not isinstance(out, dict):
        return "应答须为对象"
    for k in ("schema", "status", "answers", "meta"):
        if k not in out:
            return "缺字段 %s" % k
    if out.get("schema") != RESPONSE_SCHEMA:
        return "schema 不匹配（期望 %s）" % RESPONSE_SCHEMA
    status = out.get("status")
    if status == "abstained":
        return "" if str(out.get("reason") or "").strip() else "abstained 须给 reason"
    if status != "ok":
        return "status 越词表：%r（允许 ok/abstained）" % status
    answers = out.get("answers")
    questions = (req or {}).get("questions") or {}
    if not isinstance(answers, dict):
        return "answers 须为对象"
    missing = [n for n in questions if n not in answers]
    if missing:
        return "answers 缺问题：%s（不得静默漏答）" % "、".join(missing)
    for name, ans in answers.items():
        if not isinstance(ans, dict):
            return "答案 %s 须为对象" % name
        ptype = (questions.get(name) or {}).get("type")
        if ans.get("type") != ptype:
            return "答案 %s 的 type 与提问不一致：%r ≠ %r" % (name, ans.get("type"), ptype)
        if ptype in ("choice", "score"):
            opts = (questions[name].get("options") or questions[name].get("levels") or [])
            probs = ans.get("probs")
            if not isinstance(probs, list) or len(probs) != len(opts):
                return "答案 %s 的 probs 长度须等于候选/等级数（%d）" % (name, len(opts))
            if any(not isinstance(p, (int, float)) or p < 0 for p in probs):
                return "答案 %s 的概率须为非负数" % name
            if abs(sum(probs) - 1.0) > PROB_TOL:
                return "答案 %s 的概率和须 ≈1（实得 %.6f）" % (name, sum(probs))
            if ptype == "choice":
                if ans.get("argmax") not in opts:
                    return "答案 %s 的 argmax 须落在候选集内：%r" % (name, ans.get("argmax"))
            else:
                if not isinstance(ans.get("value"), (int, float)):
                    return "答案 %s 须给期望值 value（score 原语）" % name
        else:  # noul
            p = ans.get("p")
            if not isinstance(p, (int, float)) or not (0.0 <= float(p) <= 1.0):
                return "答案 %s 的 p 须为 [0,1] 内的数" % name
    meta = out.get("meta") or {}
    if meta.get("non_gate") is not True:
        return "meta.non_gate 须为 true（决策层不出现在门禁路径）"
    if "calibrated" not in meta:
        return "meta 缺 calibrated（是否校准概率必须自述）"
    return ""


# ---------------------------------------------------------------- 适配器

def _normalize(scores: List[float]) -> List[float]:
    total = float(sum(scores))
    if total <= 0:
        return [1.0 / len(scores)] * len(scores)
    return [float(s) / total for s in scores]


def normalize_probs(probs: List[float]) -> List[float]:
    """把外部模型的（可能被舍入的）概率归一化到和为 1（消费者需要真分布）。"""
    return _normalize([float(p) for p in probs])


def _hits(state: str, needles: List[str]) -> int:
    low = state.lower()
    return sum(1 for n in needles if n and str(n).lower() in low)


def stub_decide(req: Dict[str, Any]) -> Dict[str, Any]:
    """离线确定性决策（门禁/CI/演练用）。

    规则（全部可复现，无随机源）：choice/score 按「候选串/等级串在 state 中出现的次数」打分，
    同分按**声明顺序**打破平局；noul 命中 `true_hints` 关键词即 1.0，否则 0.0。
    **calibrated=false**：这是排序信号，不是校准概率（不要当概率消费）。
    """
    state = str(req.get("state") or "")
    answers: Dict[str, Any] = {}
    for name, q in (req.get("questions") or {}).items():
        ptype = q.get("type")
        if ptype == "choice":
            opts = [str(o) for o in q.get("options") or []]
            scores = [float(_hits(state, [o])) for o in opts]
            probs = _normalize(scores)
            answers[name] = {"type": "choice", "options": opts, "probs": probs,
                             "argmax": opts[probs.index(max(probs))]}
        elif ptype == "score":
            levels = [str(l) for l in q.get("levels") or []]
            scores = [float(_hits(state, [l])) for l in levels]
            probs = _normalize(scores)
            value = sum((i + 1) * p for i, p in enumerate(probs))
            answers[name] = {"type": "score", "levels": levels, "probs": probs,
                             "value": value}
        else:  # noul
            hits = _hits(state, [str(h) for h in (q.get("true_hints") or [])])
            answers[name] = {"type": "noul", "p": 1.0 if hits else 0.0}
    return {"schema": RESPONSE_SCHEMA, "status": "ok", "answers": answers,
            "meta": {"adapter": "stub", "calibrated": False, "non_gate": True,
                     "note": "规则式确定性输出：排序信号，非校准概率"}}


def _post_json(url: str, payload: Dict[str, Any], timeout: float) -> Dict[str, Any]:
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST",
                                headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def systemone_decide(req: Dict[str, Any], endpoint: str,
                     timeout: float = 30.0) -> Dict[str, Any]:
    """本地 typed-decision 服务适配器（Jev / Laya 系：POST {state, questions}）。

    服务返回「声明键 + 概率」；本函数把它翻成 NF 应答形状（补 argmax/期望值），
    任何异常都向上抛给 `decide()` 做 fail-closed（本层不吞错、不猜测）。
    """
    raw = _post_json(endpoint, {"state": req.get("state"),
                                "questions": req.get("questions") or {}}, timeout)
    answers: Dict[str, Any] = {}
    raw_sums: Dict[str, float] = {}
    for name, q in (req.get("questions") or {}).items():
        node = raw.get(name) if isinstance(raw, dict) else None
        if isinstance(node, dict) and "probs" in node:
            probs = [float(p) for p in node["probs"]]
        elif isinstance(node, dict) and isinstance(node.get("probabilities"), dict):
            probs = list(node["probabilities"].values())
        else:
            raise ValueError("服务未返回问题 %s 的概率分布" % name)
        ptype = q.get("type")
        if ptype in ("choice", "score"):
            raw_sums[name] = sum(probs)
            probs = normalize_probs(probs)      # 舍入容差内的归一（原始和见 meta）
        if ptype == "choice":
            opts = [str(o) for o in q.get("options") or []]
            if len(probs) != len(opts):
                raise ValueError("问题 %s 概率长度与候选数不符（%d ≠ %d）"
                                 % (name, len(probs), len(opts)))
            answers[name] = {"type": "choice", "options": opts, "probs": probs,
                             "argmax": opts[probs.index(max(probs))]}
        elif ptype == "score":
            levels = [str(l) for l in q.get("levels") or []]
            if len(probs) != len(levels):
                raise ValueError("问题 %s 概率长度与等级数不符" % name)
            answers[name] = {"type": "score", "levels": levels, "probs": probs,
                             "value": sum((i + 1) * p for i, p in enumerate(probs))}
        else:
            answers[name] = {"type": "noul", "p": float(probs[-1])}
    return {"schema": RESPONSE_SCHEMA, "status": "ok", "answers": answers,
            "meta": {"adapter": "systemone-http", "calibrated": True, "non_gate": True,
                     "endpoint": endpoint,
                     "model": str((raw or {}).get("_meta", {}).get("model")
                                  or (raw or {}).get("model") or "unknown"),
                     "raw_prob_sums": raw_sums,
                     "confidence": {k: v.get("confidence")
                                    for k, v in (raw or {}).items()
                                    if isinstance(v, dict) and "confidence" in v},
                     "usage": (raw or {}).get("_meta", {}).get("usage")}}


def openai_json_decide(req: Dict[str, Any], endpoint: str, model: str,
                       api_key: str = "", timeout: float = 60.0) -> Dict[str, Any]:
    """任一聊天模型 + 受限 JSON 作答（calibrated=false：自报概率不可当校准概率）。"""
    prompt = ("你是决策层：只回答给定问题，不得自造候选。state:\n%s\n\nquestions:\n%s\n\n"
              "只输出 JSON：{问题名: {\"probs\": [...]}}（概率和为 1）"
              % (req.get("state"), json.dumps(req.get("questions") or {}, ensure_ascii=False)))
    payload = {"model": model, "messages": [{"role": "user", "content": prompt}],
               "temperature": 0}
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = "Bearer %s" % api_key
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    r = urllib.request.Request(endpoint, data=data, method="POST", headers=headers)
    with urllib.request.urlopen(r, timeout=timeout) as resp:
        body = json.loads(resp.read().decode("utf-8"))
    text = body["choices"][0]["message"]["content"]
    raw = json.loads(text)
    answers: Dict[str, Any] = {}
    for name, q in (req.get("questions") or {}).items():
        probs = [float(p) for p in raw[name]["probs"]]
        ptype = q.get("type")
        if ptype == "choice":
            opts = [str(o) for o in q.get("options") or []]
            answers[name] = {"type": "choice", "options": opts, "probs": probs,
                             "argmax": opts[probs.index(max(probs))]}
        elif ptype == "score":
            levels = [str(l) for l in q.get("levels") or []]
            answers[name] = {"type": "score", "levels": levels, "probs": probs,
                             "value": sum((i + 1) * p for i, p in enumerate(probs))}
        else:
            answers[name] = {"type": "noul", "p": probs[-1]}
    return {"schema": RESPONSE_SCHEMA, "status": "ok", "answers": answers,
            "meta": {"adapter": "openai-json", "calibrated": False, "non_gate": True,
                     "model": model}}


def decide(req: Dict[str, Any], adapter: str = "stub", endpoint: str = "",
           model: str = "", api_key: str = "", timeout: float = 30.0,
           root: str = ".") -> Dict[str, Any]:
    """统一入口：形状校验 → 适配器 → 应答校验；任一环节失败 → abstained（fail-closed）。"""
    bad = request_issue(req)
    if bad:
        return {"schema": RESPONSE_SCHEMA, "status": "abstained",
                "answers": {}, "reason": "请求不合规：%s" % bad,
                "meta": {"adapter": adapter, "calibrated": False, "non_gate": True}}
    spec = adapter_spec(root, adapter)
    if not spec:
        return {"schema": RESPONSE_SCHEMA, "status": "abstained", "answers": {},
                "reason": "未登记的适配器：%s（登记面 %s）" % (adapter, DECL_REL),
                "meta": {"adapter": adapter, "calibrated": False, "non_gate": True}}
    started = time.monotonic()
    try:
        if adapter == "stub":
            out = stub_decide(req)
        elif adapter == "systemone-http":
            if not endpoint:
                raise ValueError("systemone-http 需 --endpoint（本地 typed-decision 服务地址）")
            out = systemone_decide(req, endpoint, timeout)
        elif adapter == "openai-json":
            if not endpoint or not model:
                raise ValueError("openai-json 需 --endpoint 与 --model")
            out = openai_json_decide(req, endpoint, model, api_key, timeout)
        else:
            raise ValueError("适配器 %s 未实现（登记面已声明：%s）" % (adapter, DECL_REL))
    except Exception as exc:  # 网络/解析/服务异常一律 fail-closed
        return {"schema": RESPONSE_SCHEMA, "status": "abstained", "answers": {},
                "reason": "adapter %s 不可用：%s: %s" % (adapter, type(exc).__name__,
                                                         str(exc)[:140]),
                "meta": {"adapter": adapter, "calibrated": bool(spec.get("calibrated")),
                         "non_gate": True}}
    out.setdefault("meta", {})
    out["meta"]["latency_ms"] = int((time.monotonic() - started) * 1000)
    issue = response_issue(out, req)
    if issue:
        return {"schema": RESPONSE_SCHEMA, "status": "abstained", "answers": {},
                "reason": "adapter %s 输出不合 schema：%s" % (adapter, issue),
                "meta": {"adapter": adapter, "calibrated": bool(spec.get("calibrated")),
                         "non_gate": True}}
    return out


def fingerprint(req: Dict[str, Any]) -> str:
    """请求指纹（可回放：同 state+questions 得同指纹）。"""
    payload = json.dumps(req, ensure_ascii=False, sort_keys=True,
                         separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


# ---------------------------------------------------------------- 面体检

def scan(root: str = ".") -> Tuple[List[str], Dict[str, Any]]:
    """决策层面体检（离线）：声明完整 + 适配器诚实标注 + stub 确定性 + fail-closed。"""
    issues: List[str] = []
    decl = load_decl(root)
    if not decl:
        return ["缺决策层声明 %s（修复指引：补声明件再跑门禁）" % DECL_REL], {}
    if decl.get("schema") != SCHEMA:
        issues.append("%s schema 不匹配（期望 %s）" % (DECL_REL, SCHEMA))
    prims = decl.get("primitives") or {}
    for p in PRIMITIVES:
        if p not in prims:
            issues.append("声明缺原语 %s（三原语齐全才谈得上类型化决策）" % p)
    adapters = decl.get("adapters") or []
    if not any(a.get("id") == "stub" for a in adapters):
        issues.append("缺 stub 适配器（门禁必须有一条离线确定性路径）")
    for a in adapters:
        aid = str(a.get("id") or "")
        for k in ("id", "kind", "in_gate_path", "calibrated"):
            if k not in a:
                issues.append("适配器 %s 缺字段 %s" % (aid or "?", k))
        if not str(a.get("note") or "").strip():
            issues.append("适配器 %s 缺 note（能力与边界须自述）" % aid)
        if a.get("in_gate_path") and aid != "stub":
            issues.append("适配器 %s 声明 in_gate_path 却非 stub"
                          "（门禁只许离线确定性路径）" % aid)
    cands = decl.get("candidates") or []
    if not cands:
        issues.append("候选模型清单为空（决策层没有可拉取的模型就只是空壳）")
    for c in cands:
        cid = str(c.get("id") or "")
        for k in ("id", "source", "license", "evidence", "pulled"):
            if k not in c:
                issues.append("候选 %s 缺字段 %s（来源/许可/实证/是否已拉取都要写）" % (cid or "?", k))
        if not isinstance(c.get("pulled"), bool):
            issues.append("候选 %s 的 pulled 须为布尔（状态不许含糊）" % cid)
        elif c.get("pulled") is True:
            # 拉取是**显式动作**：一旦声明已拉取，必须自带可追溯的本地证据
            local = c.get("local") or {}
            for k in ("how", "runtime", "served_by"):
                if not str(local.get(k) or "").strip():
                    issues.append("候选 %s 声明 pulled=true 却缺 local.%s"
                                  "（修复指引：写明怎么拉的、什么运行时、由谁服务）" % (cid, k))
    if not (decl.get("boundaries") or []):
        issues.append("声明缺 boundaries（不执行动作/不生成正文/不入门禁 等边界须成文）")

    req = {"state": "雨天走廊 与 校园情感 场景；候选：P02 校园情感流 / P03 西幻生存流",
           "questions": {
               "pipeline": {"type": "choice",
                            "options": ["P02 校园情感流", "P03 西幻生存流"]},
               "multilingual": {"type": "noul", "true_hints": ["中文", "多语"]},
               "risk": {"type": "score", "levels": ["低", "中", "高"]}}}
    if request_issue(req):
        issues.append("内部样例请求不合规：%s" % request_issue(req))
    a1 = decide(req, adapter="stub", root=root)
    a2 = decide(req, adapter="stub", root=root)
    if a1 != a2:
        issues.append("stub 非确定性（同输入两次结果不一致）")
    if a1.get("status") != "ok":
        issues.append("stub 样例未产出 ok：%s" % a1.get("reason"))
    issue = response_issue(a1, req)
    if issue:
        issues.append("stub 应答不合 schema：%s" % issue)
    if (a1.get("meta") or {}).get("calibrated") is not False:
        issues.append("stub 应答须自称 calibrated=false（排序信号不是概率）")
    # fail-closed：未登记适配器 / 缺 endpoint / 请求不合规 → abstained
    for label, kwargs in (("未登记适配器", {"adapter": "ghost"}),
                          ("缺 endpoint", {"adapter": "systemone-http"})):
        out = decide(req, root=root, **kwargs)
        if out.get("status") != "abstained" or not out.get("reason"):
            issues.append("%s 未 fail-closed（应 abstained + reason）" % label)
    bad = decide({"questions": {}}, adapter="stub", root=root)
    if bad.get("status") != "abstained":
        issues.append("不合规请求未 fail-closed")
    if response_issue({"schema": RESPONSE_SCHEMA, "status": "ok",
                       "answers": {"risk": {"type": "score", "probs": [0.2, 0.2],
                                            "value": 1.5}},
                       "meta": {"calibrated": True, "non_gate": True}}, req) == "":
        issues.append("概率和不等于 1 的应答竟通过校验（判据失效）")
    stats = {"primitives": len(prims), "adapters": len(adapters),
             "candidates": len(cands), "issueless_stub": a1.get("status") == "ok",
             "issues": len(issues)}
    return issues, stats


def summary(stats: Dict[str, Any]) -> str:
    return ("原语 %(primitives)d · 适配器 %(adapters)d · 候选模型 %(candidates)d · "
            "stub %(issueless_stub)s" % stats)
