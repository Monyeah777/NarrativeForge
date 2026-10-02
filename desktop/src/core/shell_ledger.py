"""派生空壳台账（域口径表）：把「还剩多少待补条目」变成可数事实 + 只减不增棘轮。

背景（实测）：社区域包的 `assets/DOMAIN_SPEC.md` 里有一类**派生空壳**——12 条细分名取自品类
清单，判据/失效模式只到**段级工程口径框架**，以占位短语「领域细则待作者补全 / 领域专属判据待补 /
领域专属失效模式待补」如实标注（每包 36 处 = 12 条 × 3 处）。

本模块**不代写领域判据**（宁缺毋滥：领域口径须由作者/领域专家落笔），只负责两件事：

1. `survey()`：逐包清点空壳与已填包 → 缺口可数、可交付边界清晰；
2. `ratchet()`：与冻结基线比对——**空壳只许减少**，新增一律 FAIL（防「越生越多还没人发现」）。

统计面与判据：人读真源 = `community/*/assets/DOMAIN_SPEC.md`；机读投影 = 同包
`outputs/DOMAIN_SPEC.json`——两处的占位出现次数必须一致（双源口径，`survey` 顺带判）。
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

#: 占位短语（命中任一即计一条空壳）
SHELL_PHRASES = ("领域细则待作者补全", "领域专属判据待补", "领域专属失效模式待补")
#: 人读真源（每个已建域包一件）
PACKAGE_GLOB = "community/*/assets/DOMAIN_SPEC.md"
#: 机读投影（与真源逐条同源）
JSON_SUFFIX = "outputs/DOMAIN_SPEC.json"

#: 冻结基线（2026-09-30 实测）。**只减不增**：空壳数 > 基线即 FAIL（补全后请下调本表）。
BASELINE: Dict[str, int] = {"packs_total": 100, "packs_with_shell": 73,
                            "hits": 2628, "per_shell_pack": 36}


def _hits(text: str) -> int:
    return sum(text.count(phrase) for phrase in SHELL_PHRASES)


def survey(root: str = ".") -> Dict[str, Any]:
    """逐包清点 → `{packs_total, packs_with_shell, packs_filled, hits, per_package, mismatches}`。"""
    base = Path(root)
    per_package: Dict[str, int] = {}
    mismatches: List[str] = []
    total = 0
    for p in sorted(base.glob(PACKAGE_GLOB)):
        pkg = p.parent.parent.name
        total += 1
        n = _hits(p.read_text(encoding="utf-8", errors="replace"))
        if n:
            per_package[pkg] = n
        proj = p.parent.parent / JSON_SUFFIX
        if proj.is_file():
            m = _hits(proj.read_text(encoding="utf-8", errors="replace"))
            if m != n:
                mismatches.append("%s：md %d / json %d" % (pkg, n, m))
    with_shell = len(per_package)
    return {"packs_total": total, "packs_with_shell": with_shell,
            "packs_filled": total - with_shell, "hits": sum(per_package.values()),
            "per_package": per_package, "mismatches": mismatches,
            "tier_mismatches": tier_mismatches(base, per_package)}


#: 人读档位声明里表示「还是占位档」的记号（生成器 `domain_pack.domain_spec_md` 的原文）。
DERIVED_MARK = "derived 档"


def tier_mismatches(base: Path, per_package: Dict[str, int]) -> List[str]:
    """**档位如实**：三处必须同真——人读声明（`.md` 档位行）/ 机读投影（`.json` `content_tier`）/
    正文占位计数。→ 不一致清单（空 = 全一致）。

    为什么（2026-10-01 取证）：档位行只是**声明**，条目正文来自内部规格（`.rivet/private_archive/
    ai_packs/specs/<code>.json`）的 `definition/check/pitfall` 原文。于是有两条静默错误路径：
    ① **虚报完成度**：把 `content_tier` 改成 `authored`（或新包忘了标）而正文仍带占位 ⇒ 读者
       以为「这一域已逐条撰写」，实际是段级框架；
    ② **少报完成度**：真填了内容却忘翻档位 ⇒ 包继续自称「领域细则待作者补全」，缺口台账虚高。
    补全这件事此前**只按占位计数**记账，两条路径都不拦——现把三处钉在一起（缺失即报，见
    `ratchet` 与 `test_shell_ledger`）。
    """
    out: List[str] = []
    for p in sorted(base.glob(PACKAGE_GLOB)):
        pkg = p.parent.parent.name
        hits = per_package.get(pkg, 0)
        head = "\n".join(p.read_text(encoding="utf-8", errors="replace").splitlines()[:8])
        says_derived = DERIVED_MARK in head
        proj = p.parent.parent / JSON_SUFFIX
        proj_tier = None
        if proj.is_file():
            try:
                proj_tier = json.loads(proj.read_text(encoding="utf-8", errors="replace"))\
                    .get("content_tier")
            except ValueError:
                out.append("%s：机读投影不可解析（修复指引：重渲染 outputs/DOMAIN_SPEC.json）" % pkg)
                continue
        if says_derived != (hits > 0):
            out.append("%s：人读档位声明与正文占位%s（占位 %d 处）（修复指引：补全正文后把档位行改成 "
                       "authored，或按 derived 如实标注）"
                       % (pkg, "矛盾——声明 derived 却无占位" if says_derived else
                          "矛盾——声明 authored 却仍有占位", hits))
        if proj_tier is not None and (proj_tier == "derived") != says_derived:
            out.append("%s：档位与人读声明分叉（json=%s / 人读=%s）（修复指引：重渲染该包产物）"
                       % (pkg, proj_tier, "derived" if says_derived else "authored"))
    return out


def ratchet(root: str = ".") -> Tuple[List[str], Dict[str, Any]]:
    """→ (issues, stats)。空壳 / 双源不一致 / 包数缩水 任一超基线即报。"""
    s = survey(root)
    issues: List[str] = []
    if s["packs_total"] < BASELINE["packs_total"]:
        issues.append("域包总数 %d < 基线 %d（包被删了？修复指引：确认删除是有意为之并下调基线）"
                      % (s["packs_total"], BASELINE["packs_total"]))
    if s["hits"] > BASELINE["hits"]:
        issues.append("派生空壳 %d 处 > 基线 %d 处（修复指引：新条目不许再留占位——补领域判据，"
                      "或补全后下调 %s.BASELINE）" % (s["hits"], BASELINE["hits"], __name__))
    if s["packs_with_shell"] > BASELINE["packs_with_shell"]:
        issues.append("带空壳的域包 %d > 基线 %d（修复指引：新域包不得以占位条目出厂）"
                      % (s["packs_with_shell"], BASELINE["packs_with_shell"]))
    for m in s["mismatches"]:
        issues.append("域口径表双源不一致：%s（修复指引：重渲染 outputs/DOMAIN_SPEC.json 使其同源）" % m)
    for m in s["tier_mismatches"]:
        issues.append("档位声明与实况不符：%s" % m)
    return issues, s
