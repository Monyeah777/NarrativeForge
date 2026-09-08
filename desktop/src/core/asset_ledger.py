#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""NarrativeForge 资产供应链台账（40 总纲 v2.7 波 A S2：资产六环中的 入库/溯源/浏览/版本/淘汰）。

设计定位：
- 台账 = 资产根目录下 provenance.json（溯源键表，机读唯一真相）；
- 每个托管资产文件头部写入一行机器可读头（nf-asset header），与台账双源一致；
- 生命周期：active -> deprecated -> retired（deprecate/restore 经 CLI 流转）；
- verify.sh check23 = 供应链闭合门禁：每资产可溯源（source）、可发现（文件在册）、
  键无孤儿（文件头键 ∈ 台账 且 台账条目文件实存且头一致）。

纯 Python 标准库、零第三方依赖（L2 core 红线）。路径均为显式传入，便于单测隔离。
"""
import datetime
import json
import os
import re

LEDGER_SCHEMA_VERSION = "1"
LEDGER_FILE = "provenance.json"

STATUS_ACTIVE = "active"
STATUS_DEPRECATED = "deprecated"
STATUS_RETIRED = "retired"
VALID_STATUS = (STATUS_ACTIVE, STATUS_DEPRECATED, STATUS_RETIRED)

VALID_TIER = ("official", "community", "experimental")

HEADER_MARK = "nf-asset"
_HEADER_RE = re.compile(
    r'<!--\s*nf-asset:\s*key="([^"]+)"\s+version="([^"]+)"\s+status="([^"]+)"\s*-->')


class AssetLedgerError(ValueError):
    """台账操作拒绝原因（CLI 层据此友好提示，退出码 2）。"""


def _today() -> str:
    return datetime.date.today().isoformat()


def blank_ledger(package: str = "", tier: str = "official", **meta) -> dict:
    """空白台账骨架。tier 缺省 official（官方资产集为默认货架）。"""
    if tier not in VALID_TIER:
        raise AssetLedgerError("tier 非法：%s（应为 %s）" % (tier, "/".join(VALID_TIER)))
    ledger = {"schema_version": LEDGER_SCHEMA_VERSION, "tier": tier, "assets": []}
    if package:
        ledger["package"] = package
    for k, v in meta.items():
        if v not in (None, ""):
            ledger[k] = v
    return ledger


def default_ledger_path(assets_root: str) -> str:
    return os.path.join(assets_root, LEDGER_FILE)


def load_ledger(ledger_path: str) -> dict:
    """读取台账；缺失或结构非法抛 AssetLedgerError（防静默覆盖/误写）。"""
    if not os.path.isfile(ledger_path):
        raise AssetLedgerError("台账不存在：%s（先 nf asset add 建档）" % ledger_path)
    with open(ledger_path, encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict) or not isinstance(data.get("assets"), list):
        raise AssetLedgerError("台账结构非法：%s（缺 assets[]）" % ledger_path)
    if data.get("schema_version") != LEDGER_SCHEMA_VERSION:
        raise AssetLedgerError(
            "台账 schema_version=%r 不识别（当前 %s）：%s"
            % (data.get("schema_version"), LEDGER_SCHEMA_VERSION, ledger_path))
    return data


def save_ledger(ledger: dict, ledger_path: str) -> None:
    """写盘（UTF-8、缩进 2、ensure_ascii=False）。"""
    os.makedirs(os.path.dirname(os.path.abspath(ledger_path)), exist_ok=True)
    with open(ledger_path, "w", encoding="utf-8") as f:
        json.dump(ledger, f, ensure_ascii=False, indent=2)
        f.write("\n")


def make_entry(file_rel: str, key: str, source: str, module: str = "",
               version: str = "1.0", status: str = STATUS_ACTIVE,
               added: str = None) -> dict:
    """构造条目并做字段级校验（源头拦截，CLI/测试共用）。"""
    if not key or not str(key).strip():
        raise AssetLedgerError("溯源键 key 不能为空——请先填溯源键再入库")
    if not file_rel or not str(file_rel).strip():
        raise AssetLedgerError("file 不能为空——请先填相对文件路径再入库")
    if not source or not str(source).strip():
        raise AssetLedgerError("source（溯源说明）不能为空——每资产必须可溯源")
    if not version or not str(version).strip():
        raise AssetLedgerError("version 不能为空——资产版本位必填")
    if status not in VALID_STATUS:
        raise AssetLedgerError("status 非法：%s（应为 %s）" % (status, "/".join(VALID_STATUS)))
    entry = {"file": str(file_rel), "key": str(key), "source": str(source),
             "version": str(version), "status": status}
    if module:
        entry["module"] = str(module)
    entry["added"] = added or _today()
    return entry


def _safe_join(assets_root: str, file_rel: str) -> str:
    """防路径逃逸：拒绝绝对路径与 .. 段；返回根内绝对路径。"""
    root = os.path.realpath(assets_root)
    if os.path.isabs(file_rel) or ".." in file_rel.replace("\\", "/").split("/"):
        raise AssetLedgerError("file 必须是相对路径且不得含 ..：%s" % file_rel)
    full = os.path.realpath(os.path.join(root, file_rel))
    if full != root and not full.startswith(root + os.sep):
        raise AssetLedgerError("file 逃逸资产根目录：%s" % file_rel)
    return full


def render_header(entry: dict) -> str:
    return '<!-- %s: key="%s" version="%s" status="%s" -->\n' % (
        HEADER_MARK, entry["key"], entry["version"], entry["status"])


def parse_header(text: str):
    """解析 nf-asset 头；无头返回 None，有头但不可解析抛错（防半截头混过）。"""
    if HEADER_MARK not in text:
        return None
    m = _HEADER_RE.search(text)
    if not m:
        raise AssetLedgerError("发现 %s 头但格式不可解析（应 key/version/status 齐备）" % HEADER_MARK)
    return {"key": m.group(1), "version": m.group(2), "status": m.group(3)}


def add_asset(assets_root: str, file_rel: str, key: str, source: str,
              module: str = "", version: str = "1.0", status: str = STATUS_ACTIVE,
              tier: str = None, package: str = "", added: str = None,
              ledger_path: str = None) -> dict:
    """入库：资产文件头部写 nf-asset 头 + 台账 append 条目。

    幂等判定 = 同键/同文件已托管 → 拒绝（键唯一 + 文件唯一）。tier 在首次建档时落台账级。
    """
    full = _safe_join(assets_root, file_rel)
    if not os.path.isfile(full):
        raise AssetLedgerError("资产文件不存在：%s" % full)
    lp = ledger_path or default_ledger_path(assets_root)
    if os.path.isfile(lp):
        ledger = load_ledger(lp)
        if tier is not None:
            if ledger.get("tier") and ledger.get("tier") != tier:
                raise AssetLedgerError(
                    "台账已属 tier=%s，与本次 tier=%s 冲突（一册一货架）" % (ledger.get("tier"), tier))
            ledger["tier"] = tier
    else:
        ledger = blank_ledger(package=package, tier=tier or "official")
    for e in ledger["assets"]:
        if e.get("key") == key:
            raise AssetLedgerError("台账已托管该键：%s（先 nf asset rm / restore）" % key)
        if e.get("file") == file_rel.replace("\\", "/"):
            raise AssetLedgerError("台账已托管该文件：%s" % file_rel)
    with open(full, encoding="utf-8") as f:
        text = f.read()
    existing = parse_header(text)
    if existing is not None:
        raise AssetLedgerError(
            "资产文件已带 %s 头（key=%s）——文件级唯一，禁止双托管"
            % (HEADER_MARK, existing.get("key")))
    entry = make_entry(file_rel.replace("\\", "/"), key, source,
                       module=module, version=version, status=status, added=added)
    with open(full, "w", encoding="utf-8") as f:
        f.write(render_header(entry) + text)
    ledger["assets"].append(entry)
    save_ledger(ledger, lp)
    return entry


def _load_for_update(assets_root: str, ledger_path: str, key: str):
    lp = ledger_path or default_ledger_path(assets_root)
    ledger = load_ledger(lp)
    for e in ledger["assets"]:
        if e.get("key") == key:
            return ledger, e, lp
    raise AssetLedgerError("台账无该键：%s（nf asset inventory 查看在册键）" % key)


def set_status(assets_root: str, key: str, status: str, ledger_path: str = None) -> dict:
    """状态流转（active/deprecated/retired）；同步改写资产文件头 status 位（双源一致）。"""
    if status not in VALID_STATUS:
        raise AssetLedgerError("status 非法：%s" % status)
    ledger, target, lp = _load_for_update(assets_root, ledger_path, key)
    if target["status"] == status:
        return target
    target["status"] = status
    full = _safe_join(assets_root, target["file"])
    if os.path.isfile(full):
        with open(full, encoding="utf-8") as f:
            text = f.read()
        if parse_header(text) is not None:
            text = _HEADER_RE.sub(
                '<!-- %s: key="%s" version="%s" status="%s" -->'
                % (HEADER_MARK, target["key"], target["version"], target["status"]),
                text, count=1)
            with open(full, "w", encoding="utf-8") as f:
                f.write(text)
    save_ledger(ledger, lp)
    return target


def remove_entry(assets_root: str, key: str, ledger_path: str = None) -> dict:
    """从台账摘除条目（只删台账不删文件；文件仍带旧头时 verify 报孤儿头，提示手动清理）。"""
    ledger, target, lp = _load_for_update(assets_root, ledger_path, key)
    ledger["assets"] = [e for e in ledger["assets"] if e.get("key") != key]
    save_ledger(ledger, lp)
    return target


def _iter_md_candidates(ledger_dir: str) -> list:
    """台账目录下候选资产 md（排除 README*——包/库索引手册非内容资产，对齐 check7 口径）。"""
    out = []
    for base, dirs, files in os.walk(ledger_dir):
        dirs[:] = [d for d in dirs if d not in (".git", ".gitee", "__pycache__")]
        for fn in sorted(files):
            if fn.lower().startswith("readme"):
                continue
            if fn.endswith(".md"):
                out.append(os.path.join(base, fn))
    return out


def verify_ledger_dir(ledger_dir: str, ledger_path: str = None) -> tuple:
    """单台账闭合校验。返回 (issues, stats)。

    stats：assets（在册条目数）/ untracked（目录下无头 md）/ orphans（孤儿文件头）。
    目录无台账 → 不校验（存量未入库由 inventory 提示，不视为事故）。
    """
    lp = ledger_path or default_ledger_path(ledger_dir)
    issues = []
    stats = {"assets": 0, "untracked": 0, "orphans": 0}
    if not os.path.isfile(lp):
        return issues, stats
    try:
        ledger = load_ledger(lp)
    except AssetLedgerError as exc:
        return [str(exc)], stats
    entries = ledger["assets"]
    stats["assets"] = len(entries)
    seen_keys = set()
    seen_files = set()
    for e in entries:
        key = str(e.get("key", "") or "")
        frel = str(e.get("file", "") or "").replace("\\", "/")
        if not key:
            issues.append("[%s] 条目缺 key" % lp)
        if key in seen_keys:
            issues.append("[%s] 键重复（键无孤儿前提：键唯一）: %s" % (lp, key))
        seen_keys.add(key)
        if not frel or frel in seen_files:
            issues.append("[%s] 文件重复/为空: %r" % (lp, frel))
            continue
        seen_files.add(frel)
        full = os.path.join(ledger_dir, frel)
        if not os.path.isfile(full):
            issues.append("[%s] 在册文件缺失（可发现性断裂）: %s" % (lp, frel))
            continue
        with open(full, encoding="utf-8") as f:
            text = f.read()
        try:
            header = parse_header(text)
        except AssetLedgerError as exc:
            issues.append("[%s] %s" % (lp, exc))
            continue
        if header is None:
            issues.append("[%s] 台账条目缺文件头（双源不一致）: %s" % (lp, frel))
        elif header["key"] != key or header["status"] != e.get("status"):
            issues.append("[%s] 文件头与台账不一致（台账 key=%s status=%s / 头=%s）: %s"
                          % (lp, key, e.get("status"), header, frel))
        if not str(e.get("source") or "").strip():
            issues.append("[%s] 条目缺 source（不可溯源）: %s" % (lp, key))
        if not str(e.get("version") or "").strip():
            issues.append("[%s] 条目缺 version（版本位必填）: %s" % (lp, key))
        if e.get("status") not in VALID_STATUS:
            issues.append("[%s] status 非法: %s" % (lp, e.get("status")))
    # 反向闭合：目录内带头 md 的键必须 ∈ 台账（键无孤儿）
    for cand in _iter_md_candidates(ledger_dir):
        rel = os.path.relpath(cand, ledger_dir).replace("\\", "/")
        if rel in seen_files:
            continue
        with open(cand, encoding="utf-8") as f:
            text = f.read()
        if HEADER_MARK not in text:
            stats["untracked"] += 1
            continue
        try:
            header = parse_header(text)
        except AssetLedgerError as exc:
            issues.append("[%s] %s" % (lp, exc))
            continue
        stats["orphans"] += 1
        issues.append("[%s] 孤儿文件头（键不在台账）: %s（key=%s）——nf asset rm 后需手动清理旧头"
                      % (lp, rel, header["key"]))
    return issues, stats


def verify_root(root: str) -> tuple:
    """仓库级扫描：找出全部 provenance.json 台账目录并逐册校验；聚合统计。"""
    issues = []
    stats = {"ledgers": 0, "assets": 0, "untracked": 0, "orphans": 0}
    for base, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in (".git", ".gitee", "__pycache__")]
        if LEDGER_FILE in files:
            dir_issues, dir_stats = verify_ledger_dir(base, os.path.join(base, LEDGER_FILE))
            issues.extend(dir_issues)
            stats["ledgers"] += 1
            for k in ("assets", "untracked", "orphans"):
                stats[k] += dir_stats.get(k, 0)
    return issues, stats


def iter_assets(root: str):
    """浏览：逐台账展开为行（台账级 package/tier 与条目字段合并），按目录+文件排序。"""
    rows = []
    for base, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in (".git", ".gitee", "__pycache__")]
        if LEDGER_FILE not in files:
            continue
        try:
            ledger = load_ledger(os.path.join(base, LEDGER_FILE))
        except AssetLedgerError:
            continue
        rel_dir = os.path.relpath(base, root).replace("\\", "/")
        for e in ledger["assets"]:
            row = dict(e)
            row["dir"] = rel_dir if rel_dir != "." else "(root)"
            row["package"] = ledger.get("package", "")
            row["tier"] = ledger.get("tier", "")
            rows.append(row)
    rows.sort(key=lambda r: (r["dir"], r["file"], r["key"]))
    return rows


def filter_rows(rows: list, pkg: str = "", tier: str = "",
                status: str = "") -> list:
    """ls 过滤器（pkg = 台账 package 字段；tier/status = 台账级/条目级匹配）。"""
    if tier and tier not in VALID_TIER:
        raise AssetLedgerError("tier 过滤器非法：%s" % tier)
    if status and status not in VALID_STATUS:
        raise AssetLedgerError("status 过滤器非法：%s" % status)
    out = []
    for r in rows:
        if pkg and r.get("package", "") != pkg:
            continue
        if tier and r.get("tier", "") != tier:
            continue
        if status and r.get("status") != status:
            continue
        out.append(r)
    return out


def inventory_root(root: str) -> list:
    """库存盘点：返回台账摘要行（目录/package/tier/在册数/未托管数/问题数），按目录排序。"""
    rows = []
    for base, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in (".git", ".gitee", "__pycache__")]
        if LEDGER_FILE not in files:
            continue
        lp = os.path.join(base, LEDGER_FILE)
        try:
            ledger = load_ledger(lp)
            _, dir_stats = verify_ledger_dir(base, lp)
            rel = os.path.relpath(base, root).replace("\\", "/")
            rows.append({
                "dir": rel if rel != "." else "(root)",
                "package": ledger.get("package", ""),
                "tier": ledger.get("tier", ""),
                "assets": len(ledger["assets"]),
                "untracked": dir_stats.get("untracked", 0),
                "orphans": dir_stats.get("orphans", 0),
            })
        except AssetLedgerError as exc:
            rel = os.path.relpath(base, root).replace("\\", "/")
            rows.append({"dir": rel, "package": "", "tier": "", "assets": -1,
                         "untracked": 0, "orphans": 0, "error": str(exc)})
    rows.sort(key=lambda r: r["dir"])
    return rows
