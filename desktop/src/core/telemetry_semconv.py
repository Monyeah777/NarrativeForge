"""遥测对齐 OTel GenAI 语义约定（内部差距实证：docs/45_执行遥测规范.md 定义的
`nf assemble --trace` 记录是**自定 JSON**，仓库全域 opentelemetry/otel/span 命中 0
——遥测落盘面存在，但对外界不可消费）。

本模块把既有 trace 记录**映射**为 OTel GenAI semconv 的属性面（不改 trace 格式本身，
不引入 OTel SDK——core 零第三方依赖红线保持）：

- 每个 trace 记录 = 一次工具调用的 span：`gen_ai.operation.name=execute_tool` +
  `gen_ai.tool.name=nf.<命令>`；
- 入参/出参走 semconv 的结构化字段（`gen_ai.tool.call.arguments` / `.result`）；
- NF 侧身份走 `gen_ai.agent.name`；需求原文走 `gen_ai.tool.call.arguments` 内字段；
- 输出 `OTLP 形状` JSON（resourceSpans → scopeSpans → spans），供 collector 侧适配。

纪律：**不宣称 OTLP 传输兼容**（无 protobuf/无导出端点，只有形状与属性命名对齐）；
属性名以 semconv 现行文档为准（docs/gen-ai/gen-ai-spans.md 实测提取）；
schema_url 未填 = semconv 官方站点尚标 TODO，不杜撰。
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List

#: 本模块输出的 scope 名（采集侧识别用）
SCOPE_NAME = "nf.telemetry"
SCOPE_VERSION = "1.0.0"

#: semconv 属性名（照抄规范，不做同义改写）
A_OPERATION = "gen_ai.operation.name"
A_TOOL_NAME = "gen_ai.tool.name"
A_TOOL_CALL_ID = "gen_ai.tool.call.id"
A_TOOL_ARGS = "gen_ai.tool.call.arguments"
A_TOOL_RESULT = "gen_ai.tool.call.result"
A_AGENT_NAME = "gen_ai.agent.name"
A_CONVERSATION = "gen_ai.conversation.id"

OP_EXECUTE_TOOL = "execute_tool"

#: trace 字段 → 调用参数面（入参）/ 结果面（出参）
_ARG_FIELDS = ("requirement", "phase", "status")
_RESULT_FIELDS = ("matched", "package", "pipeline", "allowed_modules",
                  "ok", "issues", "stats")


def _json_value(value: Any) -> Any:
    """semconv 的结构化字段：保持 JSON 可表示（字符串原样）。"""
    if isinstance(value, (dict, list, str, int, float, bool)) or value is None:
        return value
    return str(value)


def tool_name_of(record: Dict[str, Any]) -> str:
    """`nf assemble` / `nf run` → `nf.assemble` / `nf.run`（点分工具名）。"""
    raw = str(record.get("tool") or "nf").strip()
    parts = raw.split()
    return "%s.%s" % (parts[0], parts[1]) if len(parts) > 1 else parts[0]


def call_id_of(record: Dict[str, Any]) -> str:
    """确定性调用标识（trace 无时间戳纪律：id 由内容摘要派生，可复现）。"""
    key = json.dumps({k: record.get(k) for k in
                      ("tool", "phase", "requirement", "package", "pipeline")},
                     sort_keys=True, ensure_ascii=False)
    return "nf-" + hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]


def attributes_for(record: Dict[str, Any],
                   agent_name: str = "narrativeforge") -> Dict[str, Any]:
    """单条 trace 记录 → semconv 属性 dict（未提供的字段不杜撰）。"""
    attrs: Dict[str, Any] = {
        A_OPERATION: OP_EXECUTE_TOOL,
        A_TOOL_NAME: tool_name_of(record),
        A_TOOL_CALL_ID: call_id_of(record),
        A_AGENT_NAME: agent_name,
    }
    args = {k: _json_value(record[k]) for k in _ARG_FIELDS if k in record}
    if args:
        attrs[A_TOOL_ARGS] = args
    result = {k: _json_value(record[k]) for k in _RESULT_FIELDS if k in record}
    if result:
        attrs[A_TOOL_RESULT] = result
    phase = record.get("phase")
    if isinstance(phase, str) and phase:
        attrs[A_CONVERSATION] = "nf-%s" % phase
    return attrs


def to_span(record: Dict[str, Any], span_id: str = "",
            agent_name: str = "narrativeforge") -> Dict[str, Any]:
    """trace 记录 → OTLP 形状 span（无 trace 时间戳：timeUnixNano 留空由采集方外套）。"""
    name = "%s %s" % (OP_EXECUTE_TOOL, tool_name_of(record))
    return {
        "name": name,
        "kind": 1,  # SPAN_KIND_INTERNAL
        "traceId": "",
        "spanId": span_id or call_id_of(record)[3:19],
        "attributes": [{"key": k, "value": _otlp_value(v)}
                       for k, v in sorted(attributes_for(record, agent_name).items())],
        "status": {"code": 1 if record.get("ok", True) else 2},
    }


def _otlp_value(value: Any) -> Dict[str, Any]:
    """Python 值 → OTLP AnyValue 形状。"""
    if isinstance(value, bool):
        return {"boolValue": value}
    if isinstance(value, int):
        return {"intValue": str(value)}
    if isinstance(value, float):
        return {"doubleValue": value}
    if isinstance(value, (dict, list)):
        return {"stringValue": json.dumps(value, ensure_ascii=False,
                                          sort_keys=True)}
    if value is None:
        return {"stringValue": ""}
    return {"stringValue": str(value)}


def to_export(records: List[Dict[str, Any]],
              agent_name: str = "narrativeforge") -> Dict[str, Any]:
    """trace 记录集 → OTLP 形状 JSON（resourceSpans → scopeSpans → spans）。"""
    spans = [to_span(r, agent_name=agent_name) for r in records]
    return {"resourceSpans": [{
        "resource": {"attributes": [
            {"key": "service.name", "value": {"stringValue": "narrativeforge"}},
        ]},
        "scopeSpans": [{
            "scope": {"name": SCOPE_NAME, "version": SCOPE_VERSION},
            "spans": spans,
        }],
    }]}


def load_trace(path: str) -> List[Dict[str, Any]]:
    """读 trace JSON：单条记录或记录数组均可（兼容 nf assemble --trace 产物）。"""
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    if isinstance(data, dict):
        if isinstance(data.get("records"), list):
            return [r for r in data["records"] if isinstance(r, dict)]
        return [data]
    if isinstance(data, list):
        return [r for r in data if isinstance(r, dict)]
    return []
