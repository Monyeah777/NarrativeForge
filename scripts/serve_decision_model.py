#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""决策层本地服务（把 Laya 系模型包成 NF 的 `systemone-http` 契约）。

为什么需要这一层：模型侧的真实 API 是 Python（`laya.load(...).predict(state, questions)`），
而 NF 决策层端口说的是 **HTTP + JSON**（`POST {state, questions}` → 声明键 + 概率）。
本文件 = 中间的翻译层：入参按 NF 口径、出参按 NF 口径，**只在本地回环**监听。

契约映射（实证自 laya 0.3.5 `Agent.predict` 文档与真跑返回）：

| NF 问题形状 | Laya `criteria` |
|---|---|
| `choice` + `options: [a, b]` | `{a: a, b: b}`（选项文本同时作标签与说明） |
| `score` + `levels: [低, 中, 高]` | `[低, 中, 高]` |
| `noul` + `true_hints` | 无（Laya 的 noul 只有 instructions） |

出参归一：`answers[qid].probabilities` → `probs` 列表（choice 按 NF 选项顺序、score 按 legend 序号），
并把 `confidence` / `usage` 一并回传（**校准置信度要可见**，不藏）。

纪律：纯标准库 HTTP 服务；`laya` 是**软依赖**（缺依赖给可执行修复指引，不裸 ImportError）；
只读模型目录；不写仓库任何文件。
用法：
  python scripts/serve_decision_model.py --model-dir .rivet/scratch/models/laya-multilingual \
      --host 127.0.0.1 --port 8791
"""
from __future__ import annotations

import argparse
import json
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, Optional, Sequence

AGENT: Any = None     # 进程内单例（模型常驻，避免每请求重载）
AGENT_LOCK = threading.Lock()

#: 请求体上限（1 MiB）。本服务只吃 `{state, questions}`，正常请求远小于此。
#: 不设上限时 `self.rfile.read(length)` 会按调用方**自称**的长度无界读入内存，
#: 且 ThreadingHTTPServer 无并发上限 → 回环场景是本地 DoS，误绑外网即远程 DoS。
MAX_BODY_BYTES = 1 << 20
#: 视为「仅本地」的监听地址（其余地址须显式 --allow-non-loopback）
LOOPBACK_HOSTS = ("127.0.0.1", "localhost", "::1")


def _load_agent(model_dir: str, device: str):
    """软依赖装载：缺依赖/缺权重都给可执行修复指引（fail-closed，不静默降级）。"""
    try:
        import laya  # noqa: PLC0415 - 软依赖：仅在启动本服务时才需要
    except ImportError as exc:  # pragma: no cover - 环境相关
        raise SystemExit(
            "缺 laya 运行时：%s\n修复指引：python -m pip install laya（会带 torch/transformers）"
            % exc) from exc
    import os
    if not os.path.isdir(model_dir):
        raise SystemExit("模型目录不存在：%s\n修复指引：python -c \"from huggingface_hub "
                         "import snapshot_download; snapshot_download("
                         "'convaiinnovations/laya-multilingual', local_dir='%s')\""
                         % (model_dir, model_dir))
    return laya.load(model_dir, device=device)


def _to_laya_questions(questions: Dict[str, Any]) -> Dict[str, Any]:
    """NF 问题形状 → Laya questions（形状差异在此收口）。"""
    out: Dict[str, Any] = {}
    for qid, q in (questions or {}).items():
        qtype = str((q or {}).get("type") or "")
        item: Dict[str, Any] = {"type": qtype,
                                "instructions": str((q or {}).get("instructions") or qid)}
        if qtype == "choice":
            item["criteria"] = {str(o): str(o) for o in (q.get("options") or [])}
        elif qtype == "score":
            item["criteria"] = [str(l) for l in (q.get("levels") or [])]
        out[str(qid)] = item
    return out


def _normalize(raw: Dict[str, Any], questions: Dict[str, Any]) -> Dict[str, Any]:
    """Laya 返回 → NF 期望的 `{qid: {probs|p}}`（附 confidence 与 usage）。"""
    answers = (raw or {}).get("answers") or {}
    out: Dict[str, Any] = {}
    for qid, q in (questions or {}).items():
        node = answers.get(qid) or {}
        probs = node.get("probabilities") or {}
        qtype = str((q or {}).get("type") or "")
        if qtype == "choice":
            options = [str(o) for o in (q.get("options") or [])]
            out[qid] = {"probs": [float(probs.get(o, 0.0)) for o in options],
                        "confidence": node.get("confidence")}
        elif qtype == "score":
            levels = [str(l) for l in (q.get("levels") or [])]
            legend = {str(k): v for k, v in (node.get("legend") or {}).items()}
            order = sorted(legend, key=lambda k: int(k)) if legend else [str(i)
                                                                        for i in range(len(levels))]
            out[qid] = {"probs": [float(probs.get(k, 0.0)) for k in order],
                        "legend": legend, "confidence": node.get("confidence")}
        else:  # noul
            p = node.get("noul")
            if p is None:
                p = list(probs.values())[-1] if probs else None
            out[qid] = {"probs": [float(p) if p is not None else None],
                        "confidence": node.get("confidence")}
    out["_meta"] = {"model": getattr(AGENT, "model_id", "laya"),
                    "usage": (raw or {}).get("usage"),
                    "calibrated": True}
    return out


def _bad_request(reason: str) -> Dict[str, Any]:
    """入参形状错误的统一响应体：**400**（客户端问题）而不是 500（服务端问题）。

    为什么要分开（2026-10-08 修）：旧实现把「请求体不是 JSON / 缺 state / questions 是数组」
    全回 500 —— 调用方（NF 决策层）据此会判定「服务端故障」并**重试**，而这类请求重试一万次
    也不会成功；500 里还带着 Python 异常类名（JSONDecodeError/AttributeError），把人引向
    排查服务端。本仓另两个服务面（LSP 的 -32602、MCP 的 -32602/-32600）早已分开，这里补齐。
    """
    return {"error": {"code": 400, "type": "invalid_request", "message": reason,
                      "hint": "按 docs/decision-layer.md 的 systemone-http 契约发 "
                              "{state: 字符串, questions: {qid: {type: ...}}}"}}


def _input_problem(payload: Any) -> str:
    """入参形状体检 → 问题说明（空串 = 通过）。只判形状，不判业务。"""
    if not isinstance(payload, dict):
        return "请求体须为 JSON 对象（收到 %s）" % type(payload).__name__
    state = payload.get("state")
    if not isinstance(state, str):
        return "缺 state 或类型不符（须为字符串，收到 %s）" % type(state).__name__
    questions = payload.get("questions")
    if not isinstance(questions, dict) or not questions:
        return ("缺 questions 或类型不符（须为非空对象 {qid: {type: ...}}，收到 %s）"
                % type(questions).__name__)
    for qid, q in questions.items():
        if not isinstance(q, dict):
            return "questions[%s] 须为对象（收到 %s）" % (qid, type(q).__name__)
    return ""


class Handler(BaseHTTPRequestHandler):
    server_version = "nf-decision/1.0"

    def log_message(self, _fmt: str, *_args: Any) -> None:   # 静默：日志由调用方决定
        return

    def _send(self, code: int, payload: Dict[str, Any], body: bool = True) -> None:
        raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        if body:                               # HEAD 只回表头（协议如此）
            self.wfile.write(raw)

    def _drain(self, keep: int = MAX_BODY_BYTES) -> None:
        """把已声明的请求体**读到丢弃**（最多 keep 字节）再回响应。

        为什么必须读：HTTP/1.1 服务器不读完请求体就回响应并关连接，客户端在写/读之间会
        拿到连接重置（实测 Windows 上表现为 `ConnectionAbortedError [WinError 10053]`）——
        这是「未知路径也该给一个干净 404」的可见性缺口，不是客户端问题。keep 有界，
        免得一个自称 2 GB 的请求把内存吃光（上限闸门仍然生效）。
        """
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:      # 为何可以吞：Content-Length 非数字 ⇒ 视为「无请求体」，不读即回响应
            return
        remaining = min(length, keep)
        while remaining > 0:
            chunk = self.rfile.read(min(65536, remaining))
            if not chunk:
                break
            remaining -= len(chunk)

    def do_GET(self) -> None:
        if self.path.rstrip("/") in ("/health", "/v1/health"):
            self._send(200, {"status": "ok", "model_loaded": AGENT is not None})
            return
        self._send(404, {"error": "unknown path"})

    def _read_body(self) -> Optional[bytes]:
        """读入受限请求体；不合规时已回 413/500 并返回 None（只负责「拿字节」，不解析）。"""
        try:
            length = int(self.headers.get("Content-Length") or 0)
            if length <= 0 or length > MAX_BODY_BYTES:
                self._drain()                  # 超限请求也要给一个可达的 413
                self._send(413, {"error": "请求体须为 1..%d 字节（修复指引：只发 "
                                          "{state, questions} 两个键）" % MAX_BODY_BYTES})
                return None
            return self.rfile.read(length)
        except Exception as exc:                  # 传输面失败才是真的服务端错误
            self._send(500, {"error": {"type": type(exc).__name__, "message": str(exc)[:200]}})
            return None

    def do_POST(self) -> None:
        if self.path.rstrip("/") != "/v1/systemone":
            self._drain()                      # 不读完就回 404 会让客户端拿到连接重置
            self._send(404, {"error": "unknown path"})
            return
        body = self._read_body()
        if body is None:
            return
        try:
            payload = json.loads(body.decode("utf-8"))
        except ValueError as exc:
            self._send(400, _bad_request("请求体不是合法 JSON：%s" % str(exc)[:120]))
            return
        problem = _input_problem(payload)
        if problem:
            self._send(400, _bad_request(problem))
            return
        try:
            with AGENT_LOCK:                      # 模型非线程安全：串行化
                raw = AGENT.predict(payload["state"], _to_laya_questions(payload["questions"]))
        except Exception as exc:                  # 推理失败才是真的服务端错误
            self._send(500, {"error": {"type": type(exc).__name__,
                                       "message": str(exc)[:200]}})
            return
        self._send(200, _normalize(raw, payload["questions"]))

    def do_PUT(self) -> None:
        self._method_not_allowed()

    def do_DELETE(self) -> None:
        self._method_not_allowed()

    def do_PATCH(self) -> None:
        self._method_not_allowed()

    def do_OPTIONS(self) -> None:
        self._method_not_allowed()

    def do_HEAD(self) -> None:
        """只回状态与表头（HEAD 不该拿到 HTML 501——机器客户端会 curl -I 探活）。"""
        ok = self.path.rstrip("/") in ("/health", "/v1/health")
        self._send(200 if ok else 404, {"status": "ok"} if ok else {"error": "unknown path"},
                   body=False)

    def _method_not_allowed(self) -> None:
        self._drain()
        self.send_response(405)
        self.send_header("Allow", "GET, POST, HEAD")
        self.send_header("Content-Type", "application/json; charset=utf-8")
        body = json.dumps({"error": "method not allowed",
                           "allow": ["GET", "POST", "HEAD"]},
                          ensure_ascii=False).encode("utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main(argv: Optional[Sequence[str]] = None) -> int:
    global AGENT
    ap = argparse.ArgumentParser(description="NF 决策层本地服务（Laya 系模型）")
    ap.add_argument("--model-dir", default=".rivet/scratch/models/laya-multilingual",
                    help="本地模型目录（由 huggingface_hub 拉取）")
    ap.add_argument("--device", default="cpu", help="cpu / cuda:0")
    ap.add_argument("--host", default="127.0.0.1", help="监听地址（默认仅本地回环）")
    ap.add_argument("--allow-non-loopback", action="store_true",
                    help="显式允许绑定非回环地址（本服务无鉴权，默认拒绝）")
    ap.add_argument("--port", type=int, default=8791, help="端口（NF 侧 --endpoint 用同一端口）")
    args = ap.parse_args(argv)
    if args.host not in LOOPBACK_HOSTS and not args.allow_non_loopback:
        raise SystemExit(
            "拒绝绑定非回环地址 %s：本服务无鉴权，暴露即等于把决策接口与模型算力交出去。\n"
            "修复指引：保持默认 127.0.0.1 由本地消费；确需跨机访问请在前面加带鉴权的反代，"
            "或显式加 --allow-non-loopback 并自担风险。" % args.host)
    AGENT = _load_agent(args.model_dir, args.device)
    srv = ThreadingHTTPServer((args.host, args.port), Handler)
    print("决策层服务就绪：http://%s:%d/v1/systemone（模型 %s · device=%s）"
          % (args.host, args.port, args.model_dir, args.device), flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:      # Ctrl+C = 正常终止（服务退出，不打印 traceback）
        pass
    finally:
        srv.server_close()
    return 0


if __name__ == "__main__":
    # stdio 钉 UTF-8（2026-10-01）：同一纪律——中文结论行不该依赖宿主控制台编码。
    for _stream in (sys.stdout, sys.stderr):
        if hasattr(_stream, "reconfigure"):
            _stream.reconfigure(encoding="utf-8")
    raise SystemExit(main())
