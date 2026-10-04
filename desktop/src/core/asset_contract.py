"""数字资产契约层：三面验证（数据 / 代码 / 脚本组合 · 声明即契约）。

为什么需要（内部差距实证 2026-10-03）：NF 的门禁此前只守「NF 自己产出的内容资产」——
`export_schema`（5 种产物 shape）、`json_schema`（协议件）、`code_metrics`（AST 度量）、
`purity_scan`（sink 面/纯度）、`sast_check`（bandit + ruff-S 计数棘轮）。而「任何 AI 产出的
数字资产（数据文件 / 生成代码 / 多语言脚本链）」没有统一契约面：数据格式与字段完整性只能
逐件人查，脚本组合的「A 的输出必须匹配 B 的输入」完全没有判据。本模块把这一面做成
**声明即契约 + 只判可证**的机读门禁（真源 `protocol/asset_contracts.json`）。

三面口径：
- **数据面**：JSON（严格 RFC 8259：拒 NaN/Infinity）/ CSV（表头 + 逐行列数）/ Markdown
  （frontmatter + 表格列数）；必填字段；可选 sha256 防篡改；可选 link（某字段是文件路径，
  其行数必须等于另一字段的计数——输入输出一致性）。
- **代码面**：AST 规范符合性（可解析 + 禁用调用面）+ **可证**空指针（同一语句序列内
  `x = None` 之后解引用 x，且期间无重新赋值/无分支并入）+ 测试用例在场（声明的测试件必须
  存在、可解析、且点名被测模块）。**安全漏洞面不另造一套**——SQL 拼接 / 命令注入 / 弱随机等
  由 `scripts/sast_check.py`（bandit + ruff-S 计数棘轮）与 `purity_scan` R6 守着，
  本模块重复造第二套只会造出两套口径。
- **脚本面**：脚本自带的 `nf-io:` 头（Python `#` / Bash `#` / VBA ``` 用同一声明格式）
  是契约双源之一，声明件是另一源；两源必须逐字一致；链（A→B）上「A 的产物」必须落在
  「B 的输入」里且路径对齐。**只判字面路径**——变量拼出来的路径不判（不编造）。
- **测试执行**：`run_tests()` 是**显式开启**面（`nf asset contract --run-tests`），
  默认门禁不执行任何被声明脚本的代码——门禁必须静态可复现。

纪律：纯标准库；只读扫描（唯 `freeze()` 写声明件）；解析不到的面写「未收窄」，不替它
编结论；问题消息带修复指引。
"""
from __future__ import annotations

import ast
import csv
import hashlib
import importlib.util
import io
import json
import re
import unittest
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from core import atomic_write

DECL_REL = "protocol/asset_contracts.json"
SCHEMA = "nf-asset-contracts/1"
FACES = ("data", "code", "script")
LANGS = ("python", "bash", "vba")
FORMATS = ("json", "csv", "markdown", "text")
#: 脚本自带 I/O 契约头：Python/Bash 用 #，VBA 用单引号——同一条 nf-io: 声明格式；
#: 不锚行首：允许挂在既有注释行尾（不新增行 ⇒ 不触发 code_metrics 行数棘轮）。
_IO_RE = re.compile(r"(?:#|')[ \t]*nf-io:[ \t]*(.+?)[ \t]*$", re.M)
_MISSING = object()


# ---------------------------------------------------------------- 基础
def _strict_json(text: str) -> Any:
    """严格如 RFC 8259：NaN/Infinity 不是 JSON 常量，出现即报错（不静默收下）。"""
    def _bad(token: str) -> Any:
        raise ValueError("非 RFC 8259 常量 %s（修复指引：改用 null 或有限数字）" % token)
    return json.loads(text, parse_constant=_bad)


def digest_of(path: Path) -> str:
    """文件内容摘要（防篡改判据的单一口径：sha256 十六进制）。"""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read(root: str, rel: str) -> Tuple[Optional[str], Optional[str]]:
    """读文本件 → (text, issue)。缺件/不可读不抛裸异常，如实报问题（扫描要能出报告）。"""
    p = Path(root) / rel
    try:
        return p.read_text(encoding="utf-8"), None
    except OSError as exc:
        return None, "读不到 %s：%s（修复指引：核对声明里的路径在场）" % (rel, exc)
    except UnicodeDecodeError as exc:
        return None, "%s 不是 UTF-8：%s（修复指引：转成 UTF-8 再入库）" % (rel, exc)


def resolve(root: str, spec: Dict[str, Any]) -> List[str]:
    """声明 → 命中的仓库相对路径列表（`path` 单件 / `glob` 多件，后者稳定排序）。"""
    r = Path(root)
    if spec.get("path"):
        rel = str(spec["path"]).replace("\\", "/")
        return [rel] if (r / rel).is_file() else []
    pat = str(spec.get("glob") or "")
    if not pat:
        return []
    return sorted(p.relative_to(r).as_posix() for p in r.glob(pat) if p.is_file())


def _dig(obj: Any, path: str) -> Any:
    """按点号路径取值（dict 键 / list 下标）；取不到返回哨兵（不抛异常）。"""
    cur = obj
    for part in str(path).split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        elif isinstance(cur, list) and part.isdigit() and int(part) < len(cur):
            cur = cur[int(part)]
        else:
            return _MISSING
    return cur


# ---------------------------------------------------------------- 数据面
def _data_json(root: str, rel: str, text: str, spec: Dict[str, Any]
               ) -> Tuple[List[str], Dict[str, Any]]:
    issues: List[str] = []
    try:
        obj = _strict_json(text)
    except ValueError as exc:
        return ["数据件 %s 不是合法 JSON：%s（修复指引：修好语法或换 format）" % (rel, exc)], {}
    sch_rel = str(spec.get("schema") or "")
    if sch_rel:
        sch_text, err = _read(root, sch_rel)
        if err:
            issues.append("数据件 %s 的 schema 读不到：%s" % (rel, err))
        else:
            from core import json_schema as js
            try:
                errs = js.json_schema_check(obj, _strict_json(sch_text))
            except ValueError as exc:
                errs = ["schema 本身不是合法 JSON：%s" % exc]
            issues += ["数据件 %s 不符 schema %s：%s" % (rel, sch_rel, e) for e in errs[:5]]
    for field in spec.get("required_fields") or []:
        if _dig(obj, field) is _MISSING:
            issues.append("数据件 %s 缺必填字段 %s（修复指引：补字段或从声明里删掉——声明即契约）"
                          % (rel, field))
    return issues, {"fields": len(spec.get("required_fields") or [])}


def _csv_rows(text: str) -> List[List[str]]:
    return [row for row in csv.reader(io.StringIO(text))]


def _data_csv(rel: str, text: str, spec: Dict[str, Any]) -> Tuple[List[str], Dict[str, Any]]:
    issues: List[str] = []
    rows = _csv_rows(text)
    if not rows:
        return ["数据件 %s 是空 CSV（修复指引：至少要有表头行）" % rel], {"rows": 0}
    header = [c.strip() for c in rows[0]]
    if any(not c for c in header):
        issues.append("数据件 %s 表头有空列名（修复指引：每列都要有名字）" % rel)
    width = len(header)
    data = [r for r in rows[1:] if r != [""]]
    bad = [i for i, r in enumerate(data, 2) if len(r) != width]
    if bad:
        issues.append("数据件 %s 第 %s 行列数 != 表头 %d（修复指引：补齐/删除多余的分隔符）"
                      % (rel, ",".join(str(b) for b in bad[:3]), width))
    missing = [c for c in spec.get("required_columns") or [] if c not in header]
    if missing:
        issues.append("数据件 %s 缺必需列 %s（修复指引：加列或改声明）" % (rel, ",".join(missing)))
    low = int(spec.get("min_rows") or 0)
    if len(data) < low:
        issues.append("数据件 %s 数据行 %d < min_rows %d（修复指引：补样例或下调声明）"
                      % (rel, len(data), low))
    return issues, {"rows": len(data), "columns": width}


def _md_tables(text: str) -> List[List[List[str]]]:
    """按连续竖线行切表 → 每张表是行列表（表头 + 分隔行 + 数据行）。"""
    tables: List[List[List[str]]] = []
    cur: List[List[str]] = []
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("|") and s.count("|") >= 2:
            cur.append([c.strip() for c in s.strip("|").split("|")])
        elif cur:
            tables.append(cur)
            cur = []
    if cur:
        tables.append(cur)
    return tables


def _data_markdown(rel: str, text: str, spec: Dict[str, Any]) -> Tuple[List[str], Dict[str, Any]]:
    issues: List[str] = []
    if spec.get("frontmatter") and not text.startswith("---"):
        issues.append("数据件 %s 缺 frontmatter（修复指引：件首补 --- 块）" % rel)
    n = 0
    for table in _md_tables(text):
        if len(table) < 2:
            continue
        header = table[0]
        body = [r for r in table[1:] if not all(set(c) <= set("-:") for c in r)]
        ragged = [r for r in body if len(r) != len(header)]
        if ragged:
            issues.append("数据件 %s 有一张表列数不齐：表头 %d 列 vs 数据 %d 列（修复指引：对齐竖线）"
                          % (rel, len(header), len(ragged[0])))
        n += 1
    return issues, {"tables": n}


def _data_link(root: str, rel: str, spec: Dict[str, Any], obj: Any) -> List[str]:
    """输入输出一致性：路径字段指向的文件必须在场，其行数必须等于计数字段。"""
    link = spec.get("link") or {}
    issues: List[str] = []
    target = _dig(obj, str(link.get("path_field") or ""))
    if not isinstance(target, str) or not target:
        return ["数据件 %s 的 link.path_field=%s 取不到字符串路径（修复指引：核对字段名）"
                % (rel, link.get("path_field"))]
    rel_dir = Path(rel).parent
    bases = [str(link.get("base"))] if link.get("base") else [str(rel_dir), str(rel_dir.parent)]
    found = None
    for base in bases:
        cand = Path(root) / base / target
        if cand.is_file():
            found = cand
            break
    if found is None:
        return ["数据件 %s 指向的 %s 不在场（修复指引：补件或修正 link.base）" % (rel, target)]
    rows_field = str(link.get("rows_field") or "")
    if rows_field:
        want = _dig(obj, rows_field)
        got = len(_csv_rows(found.read_text(encoding="utf-8"))[1:])
        if want != got:
            issues.append("数据件 %s 的 %s=%s 与 %s 数据行 %d 不一致（修复指引：重算或改声明）"
                          % (rel, rows_field, want, target, got))
    return issues


def _check_data(root: str, spec: Dict[str, Any]) -> Tuple[List[str], Dict[str, Any]]:
    sid = str(spec.get("id") or spec.get("path") or spec.get("glob") or "?")
    rels = resolve(root, spec)
    if not rels:
        return (["数据契约 %s 未命中任何文件（修复指引：修正 path/glob —— 空气不是契约）" % sid],
                {"files": 0})
    fmt = str(spec.get("format") or "").lower()
    if fmt not in FORMATS:
        return (["数据契约 %s 的 format=%r 不在词表 %s（修复指引：改用词表内格式）"
                 % (sid, fmt, "/".join(FORMATS))], {"files": len(rels)})
    if spec.get("sha256") and len(rels) != 1:
        return (["数据契约 %s 声明了 sha256 却命中 %d 件（修复指引：sha256 只用于 path 单件）"
                 % (sid, len(rels))], {"files": len(rels)})
    issues: List[str] = []
    stats: Dict[str, Any] = {"files": len(rels), "format": fmt}
    for rel in rels:
        text, err = _read(root, rel)
        if err:
            issues.append(err)
            continue
        obj: Any = None
        if fmt == "json":
            sub, s = _data_json(root, rel, text, spec)
            try:
                obj = _strict_json(text)
            except ValueError:
                obj = None
        elif fmt == "csv":
            sub, s = _data_csv(rel, text, spec)
        elif fmt == "markdown":
            sub, s = _data_markdown(rel, text, spec)
        else:
            sub, s = [], {"lines": len(text.splitlines())}
        issues += sub
        stats.update(s)
        if spec.get("sha256"):
            got = digest_of(Path(root) / rel)
            if got != str(spec["sha256"]):
                issues.append("数据件 %s 摘要不符（记录 %s / 实测 %s）（修复指引：核对改动，"
                              "确认后用 nf asset contract --freeze 重冻）"
                              % (rel, str(spec["sha256"])[:12], got[:12]))
        if spec.get("link") and obj is not None:
            issues += _data_link(root, rel, spec, obj)
    return issues, stats


# ---------------------------------------------------------------- 代码面
def _walk_scope(node: ast.AST) -> Iterable[ast.AST]:
    """遍历作用域内节点，**不进入**嵌套函数/lambda（各自另算，避免跨作用域误判）。"""
    stack = [node]
    while stack:
        cur = stack.pop()
        if isinstance(cur, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef)):
            continue
        yield cur
        stack.extend(ast.iter_child_nodes(cur))


def _assigned_names(node: ast.AST) -> set:
    out = set()
    for n in _walk_scope(node):
        if isinstance(n, ast.Assign):
            out |= {t.id for t in n.targets if isinstance(t, ast.Name)}
        elif isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name):
            out.add(n.target.id)
        elif isinstance(n, ast.AugAssign) and isinstance(n.target, ast.Name):
            out.add(n.target.id)
        elif isinstance(n, (ast.For, ast.AsyncFor)) and isinstance(n.target, ast.Name):
            out.add(n.target.id)
        elif isinstance(n, ast.withitem) and isinstance(n.optional_vars, ast.Name):
            out.add(n.optional_vars.id)
    return out


def _is_none(node: Optional[ast.AST]) -> bool:
    return isinstance(node, ast.Constant) and node.value is None


def _assigns_none(stmt: ast.AST, name: str) -> bool:
    """该赋值语句是否把 name 明确置为 None（可证）。"""
    if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1:
        tgt = stmt.targets[0]
        return isinstance(tgt, ast.Name) and tgt.id == name and _is_none(stmt.value)
    if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
        return stmt.target.id == name and _is_none(stmt.value)
    return False


def _guard(stmt: ast.AST) -> Optional[Tuple[str, str]]:
    """识别 `x is None` / `x is not None` → (名字, is-none | is-not-none)。"""
    test = getattr(stmt, "test", None)
    if not isinstance(test, ast.Compare) or len(test.ops) != 1 or len(test.comparators) != 1:
        return None
    if not isinstance(test.left, ast.Name) or not _is_none(test.comparators[0]):
        return None
    if isinstance(test.ops[0], ast.Is):
        return (test.left.id, "is-none")
    if isinstance(test.ops[0], ast.IsNot):
        return (test.left.id, "is-not-none")
    return None


def _always_exits(stmts: List[ast.stmt]) -> bool:
    if not stmts:
        return False
    last = stmts[-1]
    if isinstance(last, (ast.Return, ast.Raise, ast.Continue, ast.Break)):
        return True
    return (isinstance(last, ast.If) and bool(last.orelse)
            and _always_exits(last.body) and _always_exits(last.orelse))


def _head_exprs(stmt: ast.AST) -> List[ast.AST]:
    """语句**自身**要立刻求值的表达式（复合语句只取条件/迭代表达式，不含子块）。

    子块由 _scan_block 带各自状态扫描；这里只取头部表达式，避免把「分支里先重新赋值再解引用」
    错判成外层 None 的解引用（宁少勿滥）。
    """
    if isinstance(stmt, (ast.If, ast.While)):
        return [stmt.test]
    if isinstance(stmt, (ast.For, ast.AsyncFor)):
        return [stmt.iter]
    if isinstance(stmt, (ast.With, ast.AsyncWith)):
        return [i.context_expr for i in stmt.items]
    if isinstance(stmt, (ast.Try, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        return []
    return [stmt]


def _derefs(stmt: ast.AST, names: set) -> List[int]:
    """该语句头部对「当前可证为 None」的名字做的解引用行号（属性/下标/调用）。"""
    out = []
    for head in _head_exprs(stmt):
        for n in _walk_scope(head):
            if (isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name)
                    and n.value.id in names):
                out.append(n.lineno)
            elif (isinstance(n, ast.Subscript) and isinstance(n.value, ast.Name)
                  and n.value.id in names):
                out.append(n.lineno)
            elif isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in names:
                out.append(n.lineno)
    return out


def _scan_block(stmts: List[ast.stmt], cur: set, rel: str,
                out: List[Tuple[str, int, str]]) -> set:
    """顺序扫描一个语句块；**不跨分支并入**（只判同一序列内可证的 None 解引用）。

    复合语句（if/for/while/with/try）只在各自子块里检测，不把子块的 None 状态并回外层；
    分支里可能发生的重新赋值则从外层状态里扣除（保守方向：宁少勿滥）。
    """
    cur = set(cur)
    for st in stmts:
        for lineno in _derefs(st, cur):
            out.append((rel, lineno, ",".join(sorted(cur))))
        if isinstance(st, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
            for name in _assigned_names(st):
                (cur.add if _assigns_none(st, name) else cur.discard)(name)
        elif isinstance(st, ast.Assert):
            g = _guard(st)
            if g and g[1] == "is-not-none":
                cur.discard(g[0])
        elif isinstance(st, ast.If):
            g = _guard(st)
            if g and g[1] == "is-not-none":
                _scan_block(st.body, cur - {g[0]}, rel, out)
                _scan_block(st.orelse, cur, rel, out)
            elif g and g[1] == "is-none":
                _scan_block(st.body, cur, rel, out)
                _scan_block(st.orelse, cur - {g[0]}, rel, out)
            else:
                _scan_block(st.body, cur, rel, out)
                _scan_block(st.orelse, cur, rel, out)
            if g and g[1] == "is-none" and _always_exits(st.body):
                cur.discard(g[0])
            cur -= _assigned_names(st)
        elif isinstance(st, (ast.For, ast.AsyncFor, ast.While, ast.With, ast.AsyncWith)):
            _scan_block(st.body, cur, rel, out)
            cur -= _assigned_names(st)
        elif isinstance(st, ast.Try):
            _scan_block(st.body, cur, rel, out)
            for handler in st.handlers:
                _scan_block(handler.body, cur, rel, out)
            _scan_block(st.orelse, cur, rel, out)
            _scan_block(st.finalbody, cur, rel, out)
            cur -= _assigned_names(st)
    return cur


def _none_deref(tree: ast.AST, rel: str) -> List[str]:
    """可证空指针：x = None（或默认参数 None）之后在同一语句序列里解引用 x。"""
    out: List[Tuple[str, int, str]] = []
    seeds = [(list(getattr(tree, "body", [])), set())]
    for fn in ast.walk(tree):
        if isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            default_none = set()
            pos = list(fn.args.posonlyargs) + list(fn.args.args)
            pos_defaults = list(fn.args.defaults)
            # 位置默认值对应**尾部**参数（python 语义）——首版错配到头部，把普通形参也当成
            # None 默认（实测 json_schema._check 假红 37 条）；kw_defaults 与 kwonlyargs 一一对应。
            pairs = list(zip(pos[len(pos) - len(pos_defaults):], pos_defaults))
            pairs += list(zip(fn.args.kwonlyargs, fn.args.kw_defaults))
            for arg, default in pairs:
                if _is_none(default):
                    default_none.add(arg.arg)
            seeds.append((fn.body, default_none))
    for body, seed in seeds:
        _scan_block(body, seed, rel, out)
    msgs = []
    seen = set()
    for rel_name, lineno, names in sorted(out, key=lambda x: x[1]):
        if (lineno, names) in seen:
            continue
        seen.add((lineno, names))
        msgs.append("代码件 %s 第 %d 行解引用可证为 None 的 %s（修复指引：解引用前判空，或把初始值"
                    "改成真实对象——同一语句序列内没有任何重新赋值）" % (rel_name, lineno, names))
    return msgs


def _dotted(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = _dotted(node.value)
        return "%s.%s" % (base, node.attr) if base else node.attr
    return ""


def _denied_calls(tree: ast.AST, rel: str, deny: set) -> List[str]:
    out = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Call):
            name = _dotted(n.func)
            if name and name in deny:
                out.append("代码件 %s 第 %d 行调用了禁用面 %s（修复指引：换用不执行任意代码的等价实现；"
                           "确需保留须改声明并写明理由）" % (rel, n.lineno, name))
    return out


def _check_tests(root: str, rel: str, spec: Dict[str, Any]) -> List[str]:
    issues = []
    stem = Path(rel).stem
    if not spec.get("tests"):
        issues.append("代码件 %s 未声明测试件（修复指引：补 tests 列表——没有用例的代码资产不算"
                      "通过测试）" % rel)
    for t in spec.get("tests") or []:
        trel = str(t).replace("\\", "/")
        p = Path(root) / trel
        if not p.is_file():
            issues.append("代码件 %s 声明的测试件不在场：%s（修复指引：先写测试再登记）" % (rel, trel))
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        try:
            ast.parse(text)
        except SyntaxError as exc:
            issues.append("测试件 %s 语法坏：%s（修复指引：先修语法）" % (trel, exc))
            continue
        if stem not in text:
            issues.append("测试件 %s 未点名被测模块 %s（修复指引：在测试里 import 或引用该模块）"
                          % (trel, stem))
    return issues


def _check_code(root: str, spec: Dict[str, Any]) -> Tuple[List[str], Dict[str, Any]]:
    rel = str(spec.get("path") or "")
    if str(spec.get("lang") or "python") != "python":
        return (["代码契约 %s 的 lang=%s 不在支持面（仅 python 走 AST；Bash/VBA 走脚本面声明式契约）"
                 % (spec.get("id"), spec.get("lang"))], {})
    rels = resolve(root, spec)
    if not rels:
        return (["代码契约 %s 未命中任何文件（修复指引：修正 path/glob）" % spec.get("id")], {"files": 0})
    issues: List[str] = []
    stats: Dict[str, Any] = {"files": len(rels)}
    deny = {str(x) for x in spec.get("deny_calls") or []}
    for one in rels:
        text, err = _read(root, one)
        if err:
            issues.append(err)
            continue
        try:
            tree = ast.parse(text)
        except SyntaxError as exc:
            issues.append("代码件 %s 语法坏：%s（修复指引：先修语法，AST 判据需要可解析的树）"
                          % (one, exc))
            continue
        issues += _denied_calls(tree, one, deny)
        issues += _none_deref(tree, one)
    if rel:
        issues += _check_tests(root, rel, spec)
    return issues, stats


# ---------------------------------------------------------------- 脚本面
def parse_io_header(text: str) -> Optional[Dict[str, List[str]]]:
    """解析脚本自带 nf-io 头 → {"inputs": [...], "outputs": [...]}；没有头返回 None。

    格式（三种语言同一写法，注释符不同）：# nf-io: inputs=a,b outputs=c；- 表示空。
    """
    m = _IO_RE.search(text)
    if not m:
        return None
    out: Dict[str, List[str]] = {"inputs": [], "outputs": []}
    for token in m.group(1).split():
        if "=" not in token:
            continue
        key, val = token.split("=", 1)
        key = key.strip().lower()
        if key not in out:
            continue
        out[key] = [] if val.strip() in ("-", "") else \
            [x.strip() for x in val.split(",") if x.strip()]
    return out


def observed_paths(text: str, lang: str) -> List[str]:
    """脚本里**字面量**形式的文件路径（可证的那部分；变量拼出来的不判）。"""
    out: List[str] = []
    if lang == "python":
        try:
            tree = ast.parse(text)
        except SyntaxError:
            return out
        for n in ast.walk(tree):
            if not isinstance(n, ast.Call):
                continue
            if _dotted(n.func) not in ("open", "Path", "pathlib.Path"):
                continue
            for a in n.args:
                if isinstance(a, ast.Constant) and isinstance(a.value, str):
                    out.append(a.value)
    elif lang == "bash":
        for m in re.finditer(r">>?[ \t]*([^\s;|&()]+)|<[ \t]*([^\s;|&()]+)", text):
            out.append(m.group(1) or m.group(2) or "")
    elif lang == "vba":
        for m in re.finditer(r'(?i)\bOpen\s+"([^"]+)"', text):
            out.append(m.group(1))
    skip = {"/dev/null", "/dev/stdin", "/dev/stdout", "-"}
    return [p for p in out if p and p not in skip and not p.startswith("$")]


def _check_script(root: str, spec: Dict[str, Any]) -> Tuple[List[str], Dict[str, Any]]:
    sid = str(spec.get("id") or spec.get("path") or "?")
    lang = str(spec.get("lang") or "")
    if lang not in LANGS:
        return (["脚本契约 %s 的 lang=%r 不在词表 %s（修复指引：改用词表内语言）"
                 % (sid, lang, "/".join(LANGS))], {})
    rel = str(spec.get("path") or "")
    if not (Path(root) / rel).is_file():
        return (["脚本契约 %s 的件不在场：%s（修复指引：修正 path）" % (sid, rel)], {"files": 0})
    text, err = _read(root, rel)
    if err:
        return [err], {"files": 1}
    issues: List[str] = []
    header = parse_io_header(text)
    if header is None:
        issues.append("脚本 %s 未自带 nf-io 头（修复指引：顶部加一行注释 # nf-io: inputs=a,b "
                      "outputs=c；VBA 用单引号起头——脚本契约必须双源）" % rel)
        header = {"inputs": [], "outputs": []}
    for key in ("inputs", "outputs"):
        declared = list(spec.get(key) or [])
        embedded = list(header.get(key) or [])
        if declared != embedded:
            issues.append("脚本 %s 的 %s 双源不一致：声明=%s / 头=%s（修复指引：让两边逐字一致）"
                          % (rel, key, declared, embedded))
    declared_all = set(spec.get("inputs") or []) | set(spec.get("outputs") or [])
    extra = sorted({x for x in observed_paths(text, lang) if x not in declared_all})
    if extra:
        issues.append("脚本 %s 出现未声明的字面路径 %s（修复指引：补进 inputs/outputs 或去掉硬编码）"
                      % (rel, ",".join(extra[:3])))
    return issues, {"files": 1, "inputs": len(spec.get("inputs") or []),
                    "outputs": len(spec.get("outputs") or [])}


def _check_chain(specs: Dict[str, Dict[str, Any]], chain: Dict[str, Any]
                 ) -> Tuple[List[str], Dict[str, Any]]:
    a_id, b_id = str(chain.get("from") or ""), str(chain.get("to") or "")
    if a_id not in specs or b_id not in specs:
        return (["链 %s→%s 的端点未在脚本面登记（修复指引：先登记两端脚本契约）" % (a_id, b_id)], {})
    a, b = specs[a_id], specs[b_id]
    ao = [str(x).replace("\\", "/") for x in a.get("outputs") or []]
    bi = [str(x).replace("\\", "/") for x in b.get("inputs") or []]
    issues: List[str] = []
    feeds = chain.get("feeds") or []
    if feeds:
        for f in feeds:
            out_p = str(f.get("output") or "").replace("\\", "/")
            in_p = str(f.get("input") or "").replace("\\", "/")
            if out_p not in ao:
                issues.append("链 %s→%s：上游未声明产物 %s（修复指引：补进上游 outputs）"
                              % (a_id, b_id, out_p))
            if in_p not in bi:
                issues.append("链 %s→%s：下游未声明该输入 %s（修复指引：补进下游 inputs）"
                              % (a_id, b_id, in_p))
            if out_p != in_p:
                issues.append("链 %s→%s：产物路径不对齐（上游 %s vs 下游 %s）（修复指引：统一路径写法）"
                              % (a_id, b_id, out_p, in_p))
    elif not set(ao) & set(bi):
        issues.append("链 %s→%s：上游产物与下游输入无交集（上游 %s / 下游 %s）（修复指引："
                      "契约未对齐——A 的输出必须匹配 B 的输入）"
                      % (a_id, b_id, ao[:3], bi[:3]))
    return issues, {"matched": len(set(ao) & set(bi))}


# ---------------------------------------------------------------- 聚合 / 入口
def load(root: str = ".") -> Tuple[Dict[str, Any], List[str]]:
    """读契约声明件 → (doc, issues)。缺件/坏件如实报，不抛裸异常。"""
    p = Path(root) / DECL_REL
    if not p.is_file():
        return {}, ["缺数字资产契约声明 %s（修复指引：新建并写入 schema=%s 与 data/code/script 三面）"
                    % (DECL_REL, SCHEMA)]
    try:
        doc = _strict_json(p.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return {}, ["%s 不可读或不是合法 JSON：%s（修复指引：修好语法）" % (DECL_REL, exc)]
    if not isinstance(doc, dict) or doc.get("schema") != SCHEMA:
        return {}, ["%s schema 不匹配（期望 %s）（修复指引：改为声明件当前形态）" % (DECL_REL, SCHEMA)]
    return doc, []


def scan(root: str = ".", faces: Iterable[str] = ()
         ) -> Tuple[List[str], List[str], Dict[str, Any]]:
    """三面契约扫描 → (issues, warns, stats)；唯一门禁入口（verify check40 与机器报告同源）。"""
    doc, issues = load(root)
    warns: List[str] = []
    stats: Dict[str, Any] = {f: 0 for f in FACES}
    stats.update({"files": 0, "chains": 0})
    if issues:
        return issues, warns, stats
    want = {str(x) for x in faces} or set(FACES)
    for face in FACES:
        if face not in want:
            continue
        for spec in doc.get(face) or []:
            if not isinstance(spec, dict):
                issues.append("契约 %s 面有非对象条目（修复指引：每条须是对象）" % face)
                continue
            if face == "data":
                sub, s = _check_data(root, spec)
            elif face == "code":
                sub, s = _check_code(root, spec)
            else:
                sub, s = _check_script(root, spec)
            issues += sub
            stats[face] += 1
            stats["files"] += s.get("files", 0)
    specs = {str(s.get("id")): s for s in doc.get("script") or [] if isinstance(s, dict)}
    if "script" in want:
        for chain in doc.get("chains") or []:
            sub, _ = _check_chain(specs, chain if isinstance(chain, dict) else {})
            issues += sub
            stats["chains"] += 1
    return issues, warns, stats


def freeze(root: str = ".") -> Tuple[List[str], Dict[str, Any]]:
    """按当前内容重冻声明的 sha256（防篡改棘轮：改动须显式重冻，不由扫描器偷偷写）。"""
    doc, issues = load(root)
    if issues:
        return issues, {"frozen": 0}
    n = 0
    for spec in doc.get("data") or []:
        if not isinstance(spec, dict) or not spec.get("sha256"):
            continue
        rel = str(spec.get("path") or "")
        p = Path(root) / rel
        if not p.is_file():
            issues.append("数据契约 %s 的 %s 不在场（修复指引：补件后再冻）" % (spec.get("id"), rel))
            continue
        spec["sha256"] = digest_of(p)
        n += 1
    if not issues:
        atomic_write.write_text(Path(root) / DECL_REL,
                                json.dumps(doc, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    return issues, {"frozen": n}


def _run_test_file(path: Path) -> Tuple[List[str], int]:
    """按路径加载一个测试件并跑它（显式开启面；门禁默认不执行被声明脚本的代码）。"""
    name = "nf_asset_contract_test_%s" % hashlib.sha256(str(path).encode("utf-8")).hexdigest()[:12]
    spec = importlib.util.spec_from_file_location(name, str(path))
    if spec is None or spec.loader is None:
        return ["测试件不可加载：%s（修复指引：核对路径与扩展名）" % path], 0
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except Exception as exc:                                    # noqa: BLE001 —— 测试件任意错误都记档
        return ["测试件执行失败：%s（%s: %s）（修复指引：先修测试件）"
                % (path.name, type(exc).__name__, exc)], 0
    suite = unittest.defaultTestLoader.loadTestsFromModule(mod)
    res = unittest.TextTestRunner(stream=io.StringIO(), verbosity=0).run(suite)
    issues = []
    for case, tb in list(res.failures) + list(res.errors):
        issues.append("测试未过：%s（修复指引：修到全绿；%s）"
                      % (case, tb.strip().splitlines()[-1][:160]))
    return issues, res.testsRun


def run_tests(root: str = ".", ids: Iterable[str] = ()) -> Tuple[List[str], Dict[str, Any]]:
    """跑声明的测试件（nf asset contract --run-tests）→ (issues, stats)。"""
    doc, issues = load(root)
    out: Dict[str, Any] = {"files": 0, "tests": 0}
    if issues:
        return issues, out
    want = {str(x) for x in ids}
    for spec in doc.get("code") or []:
        if not isinstance(spec, dict) or (want and str(spec.get("id")) not in want):
            continue
        for t in spec.get("tests") or []:
            p = Path(root) / str(t)
            if not p.is_file():
                issues.append("测试件不在场：%s（修复指引：先写测试再改契约）" % t)
                continue
            out["files"] += 1
            sub, ran = _run_test_file(p)
            issues += sub
            out["tests"] += ran
    return issues, out
