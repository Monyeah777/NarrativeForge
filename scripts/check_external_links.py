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
    """逐链接探测（同链接只探一次）→ 结构化报告。limit>0 时只取样前 N 条唯一链接。"""
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
            if url not in seen:
                seen[url] = fetcher(url)
            ok, detail = seen[url]
            rows.append({"file": rel, "url": url,
                         "status": "ok" if ok else "fail", "detail": detail})
    failed = [r for r in rows if r["status"] == "fail"]
    return {"schema": "nf-external-links/1", "checked": len(seen), "total": total,
            "failed": len(failed), "rows": rows}


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="外部链接巡检（非门禁；默认只解析，--fetch 才联网）")
    ap.add_argument("--root", default=".", help="仓库根（缺省当前目录）")
    ap.add_argument("--fetch", action="store_true", help="联网探测可达性（默认关闭）")
    ap.add_argument("--timeout", type=float, default=10.0, help="单条超时秒数（缺省 10）")
    ap.add_argument("--limit", type=int, default=0, help="取样上限（0 = 全量）")
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

    report = check(links, default_fetcher(args.timeout), limit=max(0, args.limit))
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print("== 外部链接巡检（模式：联网探测）==")
        for row in report["rows"]:
            if row["status"] == "fail":
                print("  [FAIL] %s ← %s（%s）"
                      % (row["url"], row["file"], row["detail"]))
        print("  探测 %d 条 / 失败 %d 条" % (report["checked"], report["failed"]))
    if args.write:
        p = Path(args.root) / args.write
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                     encoding="utf-8", newline="\n")
        print("  报告已写入：%s" % args.write)
    return 1 if report["failed"] else 0


if __name__ == "__main__":
    sys.exit(main())
