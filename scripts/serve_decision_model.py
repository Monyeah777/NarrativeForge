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
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, List, Optional, Sequence

AGENT = None          # 进程内单例（模型常驻，避免每请求重载）
AGENT_LOCK = threading.Lock()


def _load_agent(model_dir: str, device: str):
    """软依赖装载：缺依赖/缺权重都给可执行修复指引（fail-closed，不静默降级）。"""
    try:
        import laya  # noqa: PLC0415 - 软依赖：仅在启动本服务时才需要
    except ImportError as exc:  # pragma: no cover - 环境相关
        raise SystemExit(
            "缺 laya 运行时：%s\n修复指引：python -m pip install laya（会带 torch/transformers）"
            % exc)
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


class Handler(BaseHTTPRequestHandler):
    server_version = "nf-decision/1.0"

    def log_message(self, fmt: str, *args: Any) -> None:   # 静默：日志由调用方决定
        return

    def _send(self, code: int, payload: Dict[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        if self.path.rstrip("/") in ("/health", "/v1/health"):
            self._send(200, {"status": "ok", "model_loaded": AGENT is not None})
            return
        self._send(404, {"error": "unknown path"})

    def do_POST(self) -> None:  # noqa: N802
        if self.path.rstrip("/") != "/v1/systemone":
            self._send(404, {"error": "unknown path"})
            return
        try:
            length = int(self.headers.get("Content-Length") or 0)
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            state = payload.get("state")
            questions = payload.get("questions") or {}
            if not isinstance(state, str) or not questions:
                raise ValueError("请求须含 state 字符串与非空 questions")
            with AGENT_LOCK:                      # 模型非线程安全：串行化
                raw = AGENT.predict(state, _to_laya_questions(questions))
            self._send(200, _normalize(raw, questions))
        except Exception as exc:                  # 任何失败都如实回 500，不猜
            self._send(500, {"error": {"type": type(exc).__name__, "message": str(exc)[:200]}})


def main(argv: Optional[Sequence[str]] = None) -> int:
    global AGENT
    ap = argparse.ArgumentParser(description="NF 决策层本地服务（Laya 系模型）")
    ap.add_argument("--model-dir", default=".rivet/scratch/models/laya-multilingual",
                    help="本地模型目录（由 huggingface_hub 拉取）")
    ap.add_argument("--device", default="cpu", help="cpu / cuda:0")
    ap.add_argument("--host", default="127.0.0.1", help="监听地址（默认仅本地回环）")
    ap.add_argument("--port", type=int, default=8791, help="端口（NF 侧 --endpoint 用同一端口）")
    args = ap.parse_args(argv)
    AGENT = _load_agent(args.model_dir, args.device)
    srv = ThreadingHTTPServer((args.host, args.port), Handler)
    print("决策层服务就绪：http://%s:%d/v1/systemone（模型 %s · device=%s）"
          % (args.host, args.port, args.model_dir, args.device), flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        srv.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
