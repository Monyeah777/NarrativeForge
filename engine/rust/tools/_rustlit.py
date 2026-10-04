r"""Rust 字符串字面量的**唯一出处**（生成器专用）。

## 为什么需要它（实测踩到）

`json.dumps` 默认 ``ensure_ascii=True``，会把非 ASCII 写成 ``\uXXXX``；而 **Rust 只认** ``\u{XXXX}``
——直接当字面量用，生成的源码会**编译不过**（`incorrect unicode escape sequence`）。

当前各生成器的键恰好都是 ASCII（文件路径、标识符），所以这只是**潜在**陷阱而非现行 bug；
但一旦给夹具加中文键/名就会炸。故收口到一处。

## 两类用法必须分开

- **用作 Rust 字面量**（`'%s' % json.dumps(k)` 这类）→ 换成本模块的 `rs()`；
- **用作 JSON 内容**（`rj(json.dumps(obj))` 包在原始字符串里）→ **保持不动**：
  JSON 本身接受 ``\uXXXX``，且原始字符串里不能转义引号。
"""
import json
import re

_U4 = re.compile(r"\\u([0-9a-fA-F]{4})")


def rs(s: object) -> str:
    r"""任意值 → 可直接拼进 Rust 源码的**字符串字面量**（含两侧引号）。

    - 非 ASCII **原样保留**（Rust 源是 UTF-8，接受）；
    - 引号与反斜杠按 Rust 规则转义；
    - 残余的 ``\uXXXX``（控制字符等）改写成 Rust 形式 ``\u{XXXX}``。
    """
    return _U4.sub(r"\\u{\1}", json.dumps(s if isinstance(s, str) else str(s),
                                          ensure_ascii=False))


def raw(s: str) -> str:
    r"""任意文本 → Rust **原始字符串**字面量，分隔符按内容自动升级。

    原始字符串 `r#"..."#` 不能被内容里的 `"#` 穿过，否则**提前终止**、后续内容变成语法噪声。
    故按需升级到 `r##"..."##`、`r###"..."###`……（实测踩到：夹具里含 `"## 块"` 这种文本）。
    """
    n = 1
    while ('"' + '#' * n) in s:
        n += 1
    bar = '#' * n
    return 'r%s"%s"%s' % (bar, s, bar)
