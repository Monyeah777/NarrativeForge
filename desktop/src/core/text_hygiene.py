"""编码与标识面卫生门禁（外部标准净吸收：RFC 3629 / RFC 8259 / RFC 7493 / UAX #15 / UTS #39）。

内部差距（本波实证）：NF 的门禁只判「内容语义」，不判**承载编码**——
① JSON 重复键（RFC 8259 §4 要求名唯一；多数解析器后者覆盖前者，静默丢数据）；
② 工作区行尾漂移（同一文件在 Windows 检出为 CRLF、Linux 为 LF）；
③ 标识面同形/隐形字符（UTS #39）——全角字母、零宽字符、NBSP 会让「看起来同名的两个键」
   在机器侧不相等（事件名已有 ASCII 蛇形词法纪律，模块 id / 资产键 / JSON 键尚无词法门）；
④ Unicode 规范化形态（UAX #15）——NFD/NFC 两种写法在不同文件系统上所指不同。

落点纪律（ADR-0002 门禁不注水）：不新增 check 序号，语义并入 check33「新面汇总」。
本模块纯只读、纯 stdlib、确定性（同输入同输出）。
"""
from __future__ import annotations

import json
import os
import re
import unicodedata
from typing import Any, Dict, List, Tuple

#: 扫描排除目录（本地 AI 工作区 / 版本库元数据 / 缓存）
EXCLUDE_DIRS = {".git", ".rivet", "__pycache__", ".ruff_cache"}
#: 排除的二进制扩展（内容哨兵为主，这里只做快速跳过）
BINARY_EXT = {".png", ".jpg", ".jpeg", ".ico", ".gif", ".gz", ".zip", ".pdf",
              ".woff", ".woff2", ".ttf", ".so", ".dll", ".exe"}

#: 标识面允许的字符（额外允许 CJK 统一表意汉字：类内段 id 的既有形态）
#: `$` / `@` = JSON Schema、JSON-LD 保留键前缀（`$schema` / `@context` / `@id`）；
#: `{}` = URI/路径模板占位（OpenAPI 的 `/library/{id}`、MCP 的 `uriTemplate`）——
#: 都是外部标准的既有合法形状（本判据只挡隐形字符与越界码位，不做语法审美）
_ASCII_OK = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-.:/ ${}@")
_CJK = ((0x4E00, 0x9FFF), (0x3400, 0x4DBF))
#: 典型同形/隐形字符（命中即 FAIL）
INVISIBLE = {
    "\u200b": "零宽空格", "\u200c": "零宽非连接", "\u200d": "零宽连接",
    "\ufeff": "BOM/零宽无间断", "\u00a0": "不换行空格(NBSP)", "\u3000": "全角空格",
    "\u2028": "行分隔符", "\u2029": "段分隔符", "\u2060": "词连接符",
}


def _is_cjk(ch: str) -> bool:
    cp = ord(ch)
    return any(lo <= cp <= hi for lo, hi in _CJK)


def identifier_issue(text: str) -> str:
    """标识面词法体检 → 违规说明（空串 = 合规）。"""
    if not text:
        return "标识为空"
    if unicodedata.normalize("NFC", text) != text:
        return "非 NFC 规范化形态（UAX #15：同形异码会让机器侧不等）"
    for ch, name in INVISIBLE.items():
        if ch in text:
            return "含隐形/同形字符 %s（U+%04X）" % (name, ord(ch))
    bad = [c for c in text if c not in _ASCII_OK and not _is_cjk(c)]
    if bad:
        names = "、".join("U+%04X" % ord(c) for c in bad[:4])
        return "含越界字符 %s（标识面只许 ASCII 字母数字 + _-.:/ 与 CJK 汉字）" % names
    if {unicodedata.category(c) for c in text} & {"Cc", "Cf", "Cs", "Co", "Cn"}:
        return "含控制/格式/未分配码位"
    return ""


#: 版本面词法（SemVer 2.0.0 §9/§10）：数字标识不得有前导零、三段数字必填、
#: 预发布/构建标识只许 [0-9A-Za-z-]，空标识（如 `1.0.0-` 或 `1.0.0+`）非法。
_SEMVER = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-((?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*)(?:\.(?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*))*))?"
    r"(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$")


def semver_issue(value: str) -> str:
    """SemVer 2.0.0 词法体检 → 违规说明（空串 = 合规）。"""
    v = str(value or "").strip()
    if not v:
        return "版本为空"
    if _SEMVER.match(v):
        return ""
    if re.match(r"^\d+\.\d+\.\d+$", v):
        return "数字标识含前导零（SemVer §9：`01` 不是合法数字标识）"
    if re.match(r"^\d+\.\d+$", v):
        return "缺补丁号（SemVer 要求 MAJOR.MINOR.PATCH 三段）"
    if v.endswith(("-", "+")) or "-." in v or "+." in v:
        return "预发布/构建标识为空段（SemVer §9/§10）"
    return "不符合 SemVer 2.0.0 形态（修复指引：MAJOR.MINOR.PATCH[-prerelease][+build]）"


#: 版本字段声明面（真源 → 字段）：**域包内容版本**必须过 SemVer 词法。
#: 边界写明：资产槽位 `05_资产库/provenance.json: assets[].version` 是**自由槽版本**
#: （asset.schema.json 只约束 minLength），既有值 2 段（`1.0`）——属另一语义面，不入本判据；
#: 域包 `version` 是包内容版本（既有值全为 3 段 SemVer），故在此判定。
VERSION_SOURCES = (
    ("community/*/protocol.yaml", r'(?m)^\s*version:\s*"?([^"\s#]+)"?'),
)


def _walk(root: str) -> List[str]:
    out: List[str] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
        for fn in filenames:
            if os.path.splitext(fn)[1].lower() in BINARY_EXT:
                continue
            out.append(os.path.join(dirpath, fn))
    return sorted(out)


def _dup_check(text: str, rel: str, issues: List[str]) -> Tuple[Any, bool]:
    dups: List[str] = []

    def hook(pairs):
        seen = set()
        for k, _v in pairs:
            if isinstance(k, str):
                if k in seen:
                    dups.append(k)
                seen.add(k)
        return dict(pairs)

    try:
        doc = json.loads(text, object_pairs_hook=hook)
    except json.JSONDecodeError as exc:
        issues.append("%s 不是合法 JSON：%s（修复指引：跑 python -m json.tool 定位）"
                      % (rel, exc))
        return {}, False
    for k in sorted(set(dups)):
        issues.append("%s JSON 重复键 %r（修复指引：RFC 8259 §4 要求名唯一——"
                      "多数解析器后值覆盖前值、静默丢数据；删掉其中一条）" % (rel, k))
    return doc, True


def _keys(doc: Any, out: List[str]) -> None:
    if isinstance(doc, dict):
        for k, v in doc.items():
            out.append(k)
            _keys(v, out)
    elif isinstance(doc, list):
        for v in doc:
            _keys(v, out)


#: 标识**值**面（键之外）：登记册里作为值出现的 id/类别/键/模块号同样要过词法——
#: 键有判据而值没有，等于给同形字符留了后门（如 registry.json 里某人写 `М00` 西里尔 М）。
VALUE_SOURCES = (
    ("desktop/src/core/registry.json", ("modules[*].id", "modules[*].category", "protocols[*].id")),
    ("05_资产库/provenance.json", ("assets[*].key", "assets[*].module")),
    ("protocol/vocabularies.json", ("schemes[*].id", "schemes[*].values[*]")),
)


def _resolve(doc: Any, path: str) -> List[Any]:
    """极简路径解析：`a[*].b` 形态（只支持 `[*]` 展开与点分字段）。"""
    cur = [doc]
    for part in path.split("."):
        nxt: List[Any] = []
        star = part.endswith("[*]")
        key = part[:-3] if star else part
        for item in cur:
            if not isinstance(item, dict) or key not in item:
                continue
            val = item[key]
            if star:
                if isinstance(val, list):
                    nxt.extend(val)
            else:
                nxt.append(val)
        cur = nxt
    return cur


def scan(root: str = ".") -> Tuple[List[str], Dict[str, Any]]:
    """→ (issues, stats)。issues 为 FAIL 级；本门不产 WARN（要么合规要么违规）。"""
    issues: List[str] = []
    # EOL 纪律的**可执行落点**：.gitattributes 须声明全仓 LF（属性优先于 core.autocrlf，
    # 因此这是跨平台字节一致的前提；缺失则 CRLF 会在 Windows 检出时反复回流）。
    ga_path = os.path.join(root, ".gitattributes")
    if not os.path.isfile(ga_path):
        issues.append("缺 .gitattributes（修复指引：声明 `* text=auto eol=lf`——"
                      "EOL 纪律须有落点，否则 Windows 检出反复回流 CRLF）")
    else:
        with open(ga_path, encoding="utf-8") as fh:
            ga = fh.read()
        if not re.search(r"(?m)^\*\s+text(?:=\w+)?\s+eol=lf", ga):
            issues.append(".gitattributes 未声明 `* text=auto eol=lf`"
                          "（修复指引：全仓行尾纪律须显式声明，见仓库根 .gitattributes）")
    files = _walk(root)
    n_text = n_json = n_crlf = n_bom = 0
    keys_checked = values_checked = 0
    for path in files:
        rel = os.path.relpath(path, root).replace(os.sep, "/")
        try:
            with open(path, "rb") as fh:
                raw = fh.read()
        except OSError:            # 尽力而为：读不到的文件跳过（缺件由 check35 回执门/门禁件清单报出）
            continue
        if b"\x00" in raw[:4096]:  # 二进制哨兵
            continue
        n_text += 1
        if raw.startswith(b"\xef\xbb\xbf"):
            n_bom += 1
            issues.append("%s 以 UTF-8 BOM 开头（修复指引：去掉 BOM——BOM 会让 json/yaml "
                          "首键解析失败，也让摘要随编辑器变化）" % rel)
            raw = raw[3:]
        if b"\r\n" in raw:
            n_crlf += 1
            issues.append("%s 含 CRLF 行尾（修复指引：仓库 EOL 纪律 = LF"
                          "（.gitattributes `* text=auto eol=lf`）；本地去 CR 后存回，勿改内容）"
                          % rel)
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            issues.append("%s 不是合法 UTF-8：%s（修复指引：RFC 3629 只许 UTF-8——"
                          "重存为 UTF-8 无 BOM）" % (rel, exc))
            continue
        if path.endswith(".json"):
            n_json += 1
            doc, ok = _dup_check(text, rel, issues)
            if ok:
                ks: List[str] = []
                _keys(doc, ks)
                for k in ks:
                    keys_checked += 1
                    msg = identifier_issue(k)
                    if msg:
                        issues.append("%s JSON 键 %r 违规：%s（修复指引：键须 NFC + 字符集内；"
                                      "同形/隐形字符会让机器侧当成另一个键）" % (rel, k, msg))
                # 标识**值**面：登记册里作为值出现的 id/类别/键同样要过词法
                for src_rel, paths in VALUE_SOURCES:
                    if rel != src_rel:
                        continue
                    for jp in paths:
                        for val in _resolve(doc, jp):
                            if not isinstance(val, str):
                                continue
                            values_checked += 1
                            msg = identifier_issue(val)
                            if msg:
                                issues.append("%s 的 %s = %r 违规：%s（修复指引：标识值须 NFC + "
                                              "字符集内——键有判据而值没有，等于给同形留后门）"
                                              % (rel, jp, val, msg))
    stats = {"files": len(files), "text": n_text, "json": n_json, "bom": n_bom,
             "crlf": n_crlf, "keys_checked": keys_checked,
             "values_checked": values_checked, "issues": len(issues)}
    # 版本面：声明件里的 version 值须过 SemVer 2.0.0 词法（schema 只挡到三段数字，
    # 挡不住前导零/空预发布段这类「看起来像版本、实际不是」的值）
    import glob as _glob
    n_versions = 0
    for pattern, regex in VERSION_SOURCES:
        for path in sorted(_glob.glob(os.path.join(root, pattern))):
            rel = os.path.relpath(path, root).replace(os.sep, "/")
            with open(path, encoding="utf-8") as fh:
                text = fh.read()
            for m in re.finditer(regex, text):
                value = m.group(1)
                n_versions += 1
                bad = semver_issue(value)
                if bad:
                    issues.append("%s 的版本值 %r 违规：%s（修复指引：按 SemVer 2.0.0 改写，"
                                  "破坏性变更须 bump 主版本并留迁移记录）" % (rel, value, bad))
    stats["versions_checked"] = n_versions
    stats["issues"] = len(issues)
    return issues, stats


def summary(stats: Dict[str, Any]) -> str:
    return ("文本 %(text)d 件 / JSON %(json)d 件 / 键 %(keys_checked)d 个 / "
            "版本 %(versions_checked)d 个 / BOM %(bom)d / CRLF %(crlf)d" % stats)


if __name__ == "__main__":  # pragma: no cover - 手动体检入口
    import sys

    _root = sys.argv[1] if len(sys.argv) > 1 else "."
    _issues, _stats = scan(_root)
    print(summary(_stats))
    for _i in _issues:
        print("[FAIL] %s" % _i)
    sys.exit(1 if _issues else 0)
