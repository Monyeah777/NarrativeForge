#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""外部链接巡检（**非门禁** · 可选联网 · 只读）。

定位（2026-09-20 作者裁决执行）：NF 的门禁必须**静态可复现**（同输入同输出），因此外链
可达性**不进 verify 基线**；本脚本把「对外链接是否还活着」做成**独立任务**——默认只解析并
打印候选，`--fetch` 才真正联网探测，`--write` 才落盘报告（默认位置留给 `results/`，属说明件面）。

用法（仓库根目录）：
  python scripts/check_external_links.py                       # 只解析：目标文件 + 链接数
  python scripts/check_external_links.py --fetch               # 联网探测（受网络与第三方站点影响）
  python scripts/check_external_links.py --fetch --write results/external-links-report.json
退出码：0 正常（含「无链接」）/ 1 仅当 --fetch 且存在失败链接（便于定时任务告警）/ 2 用法错误。

纪律：零第三方依赖；不改仓库任何文件（除 `--write` 指定路径）；**禁止**写入协议层 `protocol/`。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path
from typing import Callable, Dict, List, Sequence, Tuple

#: 默认巡检目标（人读入口与公开文档；不含脚本、测试夹具与协议层）
DEFAULT_TARGETS = ("README.md", "README.en.md", "llms.txt", "AGENT_START.md", "ROUTES.md")
DEFAULT_GLOBS = ("docs/*.md",)
#: 不探测的链接前缀（站内锚点 / 邮件 / 电话）
SKIP_PREFIXES = ("#", "mailto:", "tel:")
_URL_RE = re.compile(r"https?://[^\s\)\]\>\"'，。；、）】`（]+")
_TRAILING = ".,;:!?）)】」』`\"'"
#: 模板占位符：含 `{…}` 的「URL」是文档里的骨架示例，不是可探测链接（跳过而非报失败）
_PLACEHOLDER = re.compile(r"[{}]")

#: 瞬态失败口径（机制借鉴 RFC 9110 §15.5 的 5xx 语义 + 429 限速语义）：
#: 这些结果只说明「这一刻没问到」，不代表链接死了——须退避重试后再定性。
TRANSIENT_HTTP = ("HTTP 408", "HTTP 425", "HTTP 429", "HTTP 500", "HTTP 502",
                  "HTTP 503", "HTTP 504")
TRANSIENT_ERRORS = ("timeout", "TimeoutError", "URLError", "ConnectionResetError",
                    "IncompleteRead", "RemoteDisconnected", "Temporary failure", "超时")


def is_transient(detail: str) -> bool:
    """瞬态判定（供退避重试使用；确定性纯函数，可单测）。"""
    d = str(detail or "")
    if any(d.startswith(p) for p in TRANSIENT_HTTP):
        return True
    return any(tok.lower() in d.lower() for tok in TRANSIENT_ERRORS)


def retry_after_seconds(detail: str, cap: float = 10.0) -> float:
    """从 `HTTP 429/503（Retry-After: N）` 形态里取建议等待秒数（无则 0，带上限）。"""
    m = re.search(r"Retry-After:\s*(\d+)", str(detail or ""))
    return min(float(m.group(1)), cap) if m else 0.0


def probe_with_retry(url: str, single: Callable[[str], Tuple[bool, str]],
                     retries: int = 2, backoff: float = 1.5,
                     sleep: Callable[[float], None] = None) -> Tuple[bool, str]:
    """带退避的探测：**只对瞬态失败重试**（4xx 除 408/425/429 一律定性，不再重试）。

    纪律：重试必须幂等（本工具只用 HEAD，天然幂等）；等待时长上界 = backoff * 2^n
    并尊重服务端 Retry-After；总尝试次数 = 1 + retries。
    """
    import time
    wait = sleep or time.sleep
    ok, detail = single(url)
    attempt = 0
    while not ok and attempt < max(0, retries) and is_transient(detail):
        attempt += 1
        delay = max(backoff * (2 ** (attempt - 1)), retry_after_seconds(detail))
        wait(delay)
        ok, detail = single(url)
        if ok:
            return True, "%s（第 %d 次重试成功）" % (detail, attempt)
    return ok, detail


def host_of(url: str) -> str:
    """URL → 主机名（用于域级熔断；解析失败返回空串）。"""
    m = re.match(r"^https?://([^/:?#]+)", str(url))
    return m.group(1).lower() if m else ""


class DomainBreaker:
    """域级熔断（本机网络实测驱动：不可达域会把每条链接拖成 ≈34s）。

    纪律：只对**连续性失败**计数（成功即清零）；达到阈值后该域的后续链接**不再探测**，
    直接标 `skipped(domain-breaker)`——报告里看得见跳过原因与计数，不静默丢弃。
    """

    def __init__(self, threshold: int = 3) -> None:
        self.threshold = max(1, threshold)
        self.failures: Dict[str, int] = {}
        self.tripped: Dict[str, int] = {}

    def is_open(self, url: str) -> bool:
        host = host_of(url)
        return bool(host) and self.failures.get(host, 0) >= self.threshold

    def record(self, url: str, ok: bool) -> None:
        host = host_of(url)
        if not host:
            return
        if ok:
            self.failures[host] = 0
            return
        self.failures[host] = self.failures.get(host, 0) + 1
        if self.failures[host] == self.threshold:
            self.tripped[host] = self.threshold


def remaining_budget(started: float, max_seconds: float, clock=time.monotonic) -> float:
    """剩余时间预算（<=0 表示已超预算；max_seconds<=0 = 不限）。"""
    if max_seconds <= 0:
        return float("inf")
    return max_seconds - (clock() - started)


def strip_trailing(url: str) -> str:
    """去掉中英标点尾巴（markdown 里常见的 `…）` 收尾）。"""
    while url and url[-1] in _TRAILING:
        url = url[:-1]
    return url


def extract_links(text: str, skip: Sequence[str] = ()) -> List[str]:
    """抽取正文 http(s) 链接（去尾标点/反引号/引号、跳过模板占位符、去重、保序、过 skip 前缀）。"""
    out: List[str] = []
    for raw in _URL_RE.findall(text):
        url = strip_trailing(raw.strip())
        if not url or url.startswith(SKIP_PREFIXES):
            continue
        if _PLACEHOLDER.search(url):                # 形如 …/{路径} 的骨架示例：跳过
            continue
        if any(url.startswith(s) for s in skip if s):
            continue
        if url not in out:
            out.append(url)
    return out


def collect(root: str, targets: Sequence[str] = DEFAULT_TARGETS,
            globs: Sequence[str] = DEFAULT_GLOBS,
            skip: Sequence[str] = ()) -> Dict[str, List[str]]:
    """{相对路径: [链接]}（文件不存在则跳过）。"""
    r = Path(root)
    files: List[Path] = []
    for rel in targets:
        p = r / rel
        if p.is_file():
            files.append(p)
    for pat in globs:
        files += sorted(r.glob(pat))
    out: Dict[str, List[str]] = {}
    for p in files:
        try:
            text = p.read_text(encoding="utf-8")
        except OSError:
            continue
        links = extract_links(text, skip)
        if links:
            out[p.relative_to(r).as_posix()] = links
    return out


def default_fetcher(timeout: float = 10.0) -> Callable[[str], Tuple[bool, str]]:
    """基于 urllib 的探测（HEAD；异常如实归类，不静默）。返回 (ok, detail)。"""
    import urllib.error
    import urllib.request

    def fetch(url: str) -> Tuple[bool, str]:
        # 非 ASCII 路径须先百分号编码（浏览器同义行为）——否则 urllib 抛 UnicodeEncodeError
        import urllib.parse
        target = urllib.parse.quote(url, safe=":/?#[]@!$&'()*+,;=%~")
        req = urllib.request.Request(
            target, method="HEAD",
            headers={"User-Agent": "nf-external-link-check/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                code = int(getattr(resp, "status", 200))
                return (200 <= code < 400, "HTTP %s" % code)
        except urllib.error.HTTPError as exc:
            return (False, "HTTP %s" % exc.code)
        except Exception as exc:                     # 网络类异常：如实报告
            return (False, type(exc).__name__)

    return fetch


def check(links_by_file: Dict[str, List[str]],
          fetcher: Callable[[str], Tuple[bool, str]],
          limit: int = 0) -> Dict[str, object]:
    """逐链接探测（同链接只探一次）→ 结构化报告。

    limit>0 时只取样前 N 条唯一链接；域级熔断开启时，连续失败的域后续链接标
    `skipped`（原因可见），避免不可达域把整轮拖成分钟级。
    """
    return check_with_breaker(links_by_file, fetcher, limit=limit)


def check_with_breaker(links_by_file: Dict[str, List[str]],
                       fetcher: Callable[[str], Tuple[bool, str]],
                       limit: int = 0, breaker: "DomainBreaker" = None,
                       deadline=None) -> Dict[str, object]:
    """带域级熔断与时间预算的探测（breaker=None 即不熔断，行为与旧版一致）。"""
    seen: Dict[str, Tuple[bool, str]] = {}
    rows: List[Dict[str, object]] = []
    total = 0
    for rel, links in sorted(links_by_file.items()):
        for url in links:
            total += 1
            if limit and url not in seen and len(seen) >= limit:
                rows.append({"file": rel, "url": url, "status": "skipped",
                             "detail": "超过取样上限"})
                continue
            if breaker is not None and url not in seen and breaker.is_open(url):
                rows.append({"file": rel, "url": url, "status": "skipped",
                             "detail": "域级熔断（%s 连续失败 ≥%d 次，本轮不再探测）"
                                       % (host_of(url), breaker.threshold)})
                continue
            if deadline is not None and url not in seen and deadline() <= 0:
                rows.append({"file": rel, "url": url, "status": "skipped",
                             "detail": "超出本轮时间预算（--max-seconds）"})
                continue
            if url not in seen:
                seen[url] = fetcher(url)
                if breaker is not None:
                    breaker.record(url, bool(seen[url][0]))
            ok, detail = seen[url]
            rows.append({"file": rel, "url": url,
                         "status": "ok" if ok else "fail", "detail": detail})
    failed = [r for r in rows if r["status"] == "fail"]
    skipped = [r for r in rows if r["status"] == "skipped"]
    out = {"schema": "nf-external-links/1", "checked": len(seen), "total": total,
           "failed": len(failed), "skipped": len(skipped), "rows": rows}
    if breaker is not None and breaker.tripped:
        out["tripped_hosts"] = dict(breaker.tripped)
    return out


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="外部链接巡检（非门禁；默认只解析，--fetch 才联网）")
    ap.add_argument("--root", default=".", help="仓库根（缺省当前目录）")
    ap.add_argument("--fetch", action="store_true", help="联网探测可达性（默认关闭）")
    ap.add_argument("--timeout", type=float, default=10.0, help="单条超时秒数（缺省 10）")
    ap.add_argument("--limit", type=int, default=0, help="取样上限（0 = 全量）")
    ap.add_argument("--retries", type=int, default=2,
                    help="瞬态失败重试次数（缺省 2；只对超时/5xx/429/408/425 重试）")
    ap.add_argument("--backoff", type=float, default=1.5,
                    help="退避基数秒（缺省 1.5，逐次翻倍；尊重 Retry-After）")
    ap.add_argument("--breaker", type=int, default=3,
                    help="域级熔断阈值（缺省 3 次连续失败即跳过该域；0 = 关闭）")
    ap.add_argument("--max-seconds", type=float, default=0.0,
                    help="本轮时间预算秒（0 = 不限；超预算的链接标 skipped）")
    ap.add_argument("--skip", default="", help="额外跳过的 URL 前缀（逗号分隔）")
    ap.add_argument("--json", action="store_true", help="输出结构化 JSON")
    ap.add_argument("--write", default="", help="报告写入路径（不得写入 protocol/）")
    args = ap.parse_args(argv)

    if args.write and args.write.replace("\\", "/").startswith("protocol/"):
        print("  ✗ 报告不得写入协议层 protocol/"
              "（修复指引：写入 results/ 或 docs/——协议层须静态可复现）", file=sys.stderr)
        return 2
    skip = [s.strip() for s in (args.skip or "").split(",") if s.strip()]
    links = collect(args.root, skip=skip)
    total_links = sum(len(v) for v in links.values())
    if not args.fetch:
        if args.json:
            print(json.dumps({"schema": "nf-external-links/1", "mode": "scan",
                              "files": len(links), "total": total_links,
                              "links_by_file": links},
                             ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print("== 外部链接巡检（模式：只解析，未联网）==")
            for rel, urls in sorted(links.items()):
                print("  %-28s %d 条" % (rel, len(urls)))
            print("  合计 %d 文件 / %d 条链接（加 --fetch 才联网探测）"
                  % (len(links), total_links))
        return 0

    import time as _time
    started = _time.monotonic()
    base = default_fetcher(args.timeout)
    fetcher = (lambda url: probe_with_retry(url, base, retries=max(0, args.retries),
                                            backoff=max(0.0, args.backoff)))
    breaker = DomainBreaker(threshold=args.breaker) if args.breaker else None
    report = check_with_breaker(
        links, fetcher, limit=max(0, args.limit), breaker=breaker,
        deadline=(lambda: remaining_budget(started, args.max_seconds))
        if args.max_seconds > 0 else None)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print("== 外部链接巡检（模式：联网探测）==")
        for row in report["rows"]:
            if row["status"] == "fail":
                print("  [FAIL] %s ← %s（%s）"
                      % (row["url"], row["file"], row["detail"]))
        print("  探测 %d 条 / 失败 %d 条" % (report["checked"], report["failed"]))
        if report.get("skipped"):
            print("  跳过 %d 条（域级熔断/超预算；明细见 --json）" % report["skipped"])
        for host, n in sorted((report.get("tripped_hosts") or {}).items()):
            print("  ⚠ 域级熔断：%s（连续失败 ≥%d 次，本轮不再探测）" % (host, n))
    if args.write:
        p = Path(args.root) / args.write
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                     encoding="utf-8", newline="\n")
        print("  报告已写入：%s" % args.write)
    return 1 if report["failed"] else 0


if __name__ == "__main__":
    sys.exit(main())
