"""NFA-L 前端 · 表达式词法/语法（封闭、全函数、无副作用）。

NF 的声明层（YAML 围栏 + protocol/schema 的 JSON-Schema IDL）承载「有什么」；
本模块补命令层：Pipeline.structure.flow[].condition 此前只是自由字符串（IDL 仅
type: string / minLength: 1），既不能静态检查也不能执行。命令层只覆盖 guard 表达式
这一处——无用户函数、无循环、无赋值、无 I/O，函数集封闭（见 core.nfal.FUNCS）。

边缘全借：Pratt 优先级爬升是通行算法；AST 用 JSON 形状（与 NF 机读件同族）；
诊断沿用 NF 的 fail/warn 口径（见 core.nfal.diag）。纯标准库；只读无副作用。
"""
from __future__ import annotations

import re
from typing import Any, Dict, List

_IDENT = re.compile(r"[A-Za-z_\u4e00-\u9fff][A-Za-z0-9_\u4e00-\u9fff]*")
_NUM = re.compile(r"\d+(?:\.\d+)?")
_PUNCT = ("&&", "||", "==", "!=", "<=", ">=", "<", ">", "!", "+", "-", "*", "/", "%",
          "(", ")", "[", "]", "{", "}", ",", ".", ":", "?", "=")
_ESCAPES = {"n": "\n", "t": "\t", "r": "\r", '"': '"', "\\": "\\"}
_BIN_LEVELS = (("||",), ("&&",), ("==", "!=", "<", "<=", ">", ">=", "in"),
               ("+", "-"), ("*", "/", "%"))
#: R4 纪律（错误信息即微型文档）：每条解析错误都带修复指引
_GUIDE = "（修复指引：见 docs/nfal.md 的表达式语法）"


class LexError(Exception):
    """词法错误（带 pos，供诊断定位；不裸崩）。"""

    def __init__(self, message: str, pos: int) -> None:
        super().__init__(message)
        self.message = message
        self.pos = pos


class ParseError(Exception):
    """语法错误（带 pos）。"""

    def __init__(self, message: str, pos: int) -> None:
        super().__init__(message)
        self.message = message
        self.pos = pos


def tokenize(src: str) -> List[Dict[str, Any]]:
    """源码 → token 列表（末项恒为 eof）；非法字符/未闭合字符串抛 LexError。"""
    out: List[Dict[str, Any]] = []
    i, n = 0, len(src)
    while i < n:
        ch = src[i]
        if ch in " \t\r\n":
            i += 1
            continue
        if ch == "#":                              # 行注释（借 YAML/JSON5 习惯）
            while i < n and src[i] != "\n":
                i += 1
            continue
        if ch == '"':
            tok, i = _scan_string(src, i)
            out.append(tok)
            continue
        m = _NUM.match(src, i)
        if m:
            raw = m.group(0)
            kind = "float" if "." in raw else "int"
            out.append({"k": kind, "v": float(raw) if kind == "float" else int(raw), "pos": i})
            i = m.end()
            continue
        m = _IDENT.match(src, i)
        if m:
            out.append({"k": "ident", "v": m.group(0), "pos": i})
            i = m.end()
            continue
        for p in _PUNCT:
            if src.startswith(p, i):
                out.append({"k": "punct", "v": p, "pos": i})
                i += len(p)
                break
        else:
            raise LexError("非法字符 %r" % ch + _GUIDE, i)
    out.append({"k": "eof", "v": None, "pos": n})
    return out


def _scan_string(src: str, i: int):
    """从 i（指向开引号）扫一个双引号字符串 → (token, 新下标)；未闭合抛 LexError。"""
    j, buf = i + 1, []
    while j < len(src) and src[j] != '"':
        if src[j] == "\\":
            if j + 1 >= len(src):
                raise LexError("字符串转义未闭合" + _GUIDE, j)
            esc = src[j + 1]
            if esc not in _ESCAPES:
                raise LexError("未知转义 \\%s" % esc + _GUIDE, j)
            buf.append(_ESCAPES[esc])
            j += 2
            continue
        buf.append(src[j])
        j += 1
    if j >= len(src):
        raise LexError("字符串未闭合" + _GUIDE, i)
    return {"k": "str", "v": "".join(buf), "pos": i}, j + 1


class Parser:
    """递归下降 + 优先级爬升；节点形状见 parse() 的文档串。"""

    def __init__(self, tokens: List[Dict[str, Any]]) -> None:
        self.toks = tokens
        self.i = 0

    def peek(self) -> Dict[str, Any]:
        return self.toks[self.i]

    def next(self) -> Dict[str, Any]:
        t = self.toks[self.i]
        self.i += 1
        return t

    def expect(self, v: str) -> Dict[str, Any]:
        t = self.next()
        if t["k"] != "punct" or t["v"] != v:
            raise ParseError("应为 %r，实为 %r" % (v, t["v"]) + _GUIDE, t["pos"])
        return t

    def parse(self) -> Dict[str, Any]:
        node = self._ternary()
        t = self.peek()
        if t["k"] != "eof":
            raise ParseError("表达式后有多余记号 %r" % (t["v"],) + _GUIDE, t["pos"])
        return node

    def _ternary(self) -> Dict[str, Any]:
        cond = self._binary(0)
        t = self.peek()
        if t["k"] == "punct" and t["v"] == "?":
            self.next()
            yes = self._ternary()
            self.expect(":")
            no = self._ternary()
            return {"k": "cond", "c": cond, "t": yes, "f": no, "pos": cond["pos"]}
        return cond

    def _binary(self, level: int) -> Dict[str, Any]:
        if level >= len(_BIN_LEVELS):
            return self._unary()
        ops = _BIN_LEVELS[level]
        left = self._binary(level + 1)
        while True:
            t = self.peek()
            if t["k"] == "ident" and t["v"] == "in" and "in" in ops:
                op = "in"
            elif t["k"] == "punct" and t["v"] in ops:
                op = t["v"]
            else:
                return left
            self.next()
            right = self._binary(level + 1)
            left = {"k": "bin", "op": op, "l": left, "r": right, "pos": left["pos"]}

    def _unary(self) -> Dict[str, Any]:
        t = self.peek()
        if t["k"] == "punct" and t["v"] in ("!", "-"):
            self.next()
            return {"k": "un", "op": t["v"], "x": self._unary(), "pos": t["pos"]}
        return self._postfix()

    def _postfix(self) -> Dict[str, Any]:
        node = self._primary()
        while True:
            t = self.peek()
            if not (t["k"] == "punct" and t["v"] == "("):
                return node
            if node["k"] != "ref" or len(node["path"]) != 1:
                raise ParseError("只有具名函数可调用" + _GUIDE, t["pos"])
            self.next()
            args: List[Dict[str, Any]] = []
            if not (self.peek()["k"] == "punct" and self.peek()["v"] == ")"):
                args.append(self._ternary())
                while self.peek()["k"] == "punct" and self.peek()["v"] == ",":
                    self.next()
                    args.append(self._ternary())
            self.expect(")")
            node = {"k": "call", "fn": node["path"][0], "args": args, "pos": node["pos"]}

    def _primary(self) -> Dict[str, Any]:
        t = self.next()
        if t["k"] in ("int", "float", "str"):
            return {"k": "lit", "t": t["k"], "v": t["v"], "pos": t["pos"]}
        if t["k"] == "ident":
            return self._ident(t)
        if t["k"] == "punct" and t["v"] == "(":
            node = self._ternary()
            self.expect(")")
            return node
        if t["k"] == "punct" and t["v"] == "[":
            return self._list(t)
        if t["k"] == "punct" and t["v"] == "{":
            return self._map(t)
        raise ParseError("意外的记号 %r" % (t["v"],) + _GUIDE, t["pos"])

    def _ident(self, t: Dict[str, Any]) -> Dict[str, Any]:
        word = t["v"]
        if word == "true":
            return {"k": "lit", "t": "bool", "v": True, "pos": t["pos"]}
        if word == "false":
            return {"k": "lit", "t": "bool", "v": False, "pos": t["pos"]}
        if word == "null":
            return {"k": "lit", "t": "null", "v": None, "pos": t["pos"]}
        if word == "in":
            raise ParseError("'in' 只能作中缀运算符" + _GUIDE, t["pos"])
        path = [word]
        while self.peek()["k"] == "punct" and self.peek()["v"] == ".":
            self.next()
            seg = self.next()
            if seg["k"] != "ident":
                raise ParseError("'.' 后应为标识符" + _GUIDE, seg["pos"])
            path.append(seg["v"])
        return {"k": "ref", "path": path, "pos": t["pos"]}

    def _list(self, t: Dict[str, Any]) -> Dict[str, Any]:
        items: List[Dict[str, Any]] = []
        if not (self.peek()["k"] == "punct" and self.peek()["v"] == "]"):
            items.append(self._ternary())
            while self.peek()["k"] == "punct" and self.peek()["v"] == ",":
                self.next()
                if self.peek()["k"] == "punct" and self.peek()["v"] == "]":
                    break
                items.append(self._ternary())
        self.expect("]")
        return {"k": "list", "items": items, "pos": t["pos"]}

    def _map(self, t: Dict[str, Any]) -> Dict[str, Any]:
        entries: List[List[Dict[str, Any]]] = []
        if not (self.peek()["k"] == "punct" and self.peek()["v"] == "}"):
            entries.append(self._map_entry())
            while self.peek()["k"] == "punct" and self.peek()["v"] == ",":
                self.next()
                if self.peek()["k"] == "punct" and self.peek()["v"] == "}":
                    break
                entries.append(self._map_entry())
        self.expect("}")
        return {"k": "map", "entries": entries, "pos": t["pos"]}

    def _map_entry(self) -> List[Dict[str, Any]]:
        t = self.peek()
        if t["k"] not in ("ident", "str"):
            raise ParseError("映射键应为标识符或字符串" + _GUIDE, t["pos"])
        self.next()
        key = {"k": "lit", "t": "str", "v": t["v"], "pos": t["pos"]}
        self.expect(":")
        return [key, self._ternary()]


def parse(src: str) -> Dict[str, Any]:
    """表达式 → AST。

    节点形状（JSON 可序列化；pos 只在诊断期用，入 IR 前 strip_pos）：
      {"k":"lit","t":bool|int|float|str|null,"v":...,"pos":n}
      {"k":"ref","path":[段...],"pos":n}
      {"k":"call","fn":名,"args":[...],"pos":n}
      {"k":"un","op":"!"|"-","x":节点,"pos":n}
      {"k":"bin","op":...,"l":节点,"r":节点,"pos":n}
      {"k":"cond","c":节点,"t":节点,"f":节点,"pos":n}
      {"k":"list","items":[...],"pos":n}
      {"k":"map","entries":[[键,值],...],"pos":n}
    """
    return Parser(tokenize(src)).parse()


def strip_pos(node: Any) -> Any:
    """剥离 pos（IR 规范化：同输入 → 逐字节同 IR）。"""
    if isinstance(node, dict):
        return {k: strip_pos(v) for k, v in node.items() if k != "pos"}
    if isinstance(node, list):
        return [strip_pos(x) for x in node]
    return node
