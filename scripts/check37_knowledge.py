#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check37 · 知识层门禁（双源知识：权威分层 / 查询有序 / 时效 / 消化可追溯 / 认知裁剪）。

只读；零第三方依赖。退出码：0 全绿 / 1 有 FAIL。
"""
import os
import sys

sys.path.insert(0, os.path.join("desktop", "src"))


def main() -> int:
    problems = []
    try:
        from core import knowledge as kn
    except Exception as exc:                      # 导入失败 = 不通过
        print("import 失败：%s" % exc)
        return 1

    # 1 声明：词表 / 权威分层 / locator 真实性 / 时效 / 晋升 / 审核 / 认知裁剪
    issues, _warns, stats = kn.scan(".")
    for i in issues:
        problems.append("知识源声明：%s" % i)

    # 2 查询有序：合同级必须全部排在参考级之前
    order = [r["authority"] for r in kn.resolve_order(".")]
    if order and order != sorted(order, key=lambda a: 0 if a == "contract" else 1):
        problems.append("查询有序被破坏（参考级排到了合同级之前）：%s" % order)

    # 3 消化可追溯：记录与产物 digest 绑定 + 转正须三档证据双签
    for i in kn.verify_transform(".")[0]:
        problems.append("消化记录：%s" % i)

    # 3b 频次可复算：频率台账合法且与消化记录的 reuse_count 一致（不许手写频次）
    for i in kn.verify_usage(".")[0]:
        problems.append("频率台账：%s" % i)

    # 3c 认知裁剪执行面：越权源不得进入任何 clearance 的查询顺序
    for clearance in ("public", "internal", "restricted"):
        allowed = kn.visible_ids(".", clearance)
        leaked = [r["id"] for r in kn.resolve_order(".", clearance=clearance)
                  if r["id"] not in allowed]
        if leaked:
            problems.append("认知裁剪失效（%s 看到越权源）：%s" % (clearance, leaked))

    # 4 巡检：悬空引用 / 孤儿条目（时效缺失按 WARN 挂账，不判死）
    lint_issues, _lint_warns, lstats = kn.lint(".")
    for i in lint_issues:
        problems.append("知识层巡检：%s" % i)

    for p in problems:
        print("[FAIL] %s" % p)
    print("知识层统计：源 %d（合同 %d / 参考 %d）· 消化记录 %d · 悬空 %d · 孤儿 %d · 时效缺失 %d"
          % (stats.get("sources", 0), stats.get("contract", 0), stats.get("reference", 0),
             stats.get("transforms", 0), lstats.get("dangling", 0), lstats.get("orphan", 0),
             lstats.get("no_stale_after", 0)))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
