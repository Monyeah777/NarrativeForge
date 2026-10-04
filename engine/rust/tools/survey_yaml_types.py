"""勘查：boundary 字段的**解析后类型面**（决定 Rust 侧标量解析要多严）。

若出现 int/float/bool/null/date，就必须复刻 PyYAML 的标量类型解析；若全是 str/list/dict，
子集解析器只需处理字符串即可。
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(".").resolve() / "desktop" / "src"))
from core import conformance_scan as csc  # noqa: E402
from core import module_signature as ms  # noqa: E402

sigs = ms.signatures(".")
print("模块数:", len(sigs))

types = {}


def walk(v, path=""):
    t = type(v).__name__
    types[t] = types.get(t, 0) + 1
    if isinstance(v, dict):
        for k, vv in v.items():
            walk(vv, path + "/" + str(k))
    elif isinstance(v, list):
        for i, vv in enumerate(v):
            walk(vv, path + "[%d]" % i)


for mid, rec in sigs.items():
    walk(rec["boundary"], mid)

print("类型分布:", types)

# 裸标量里有没有「看着像数字/布尔/null」的？
import re
suspicious = []
for mid, rec in sigs.items():
    for k, v in rec["boundary"].items():
        vals = v if isinstance(v, list) else [v]
        for x in vals:
            if isinstance(x, str) and re.fullmatch(
                    r"(?:[-+]?\d+|\d+\.\d+|true|false|yes|no|on|off|null|~|None)", x, re.I):
                suspicious.append((mid, k, x))
print("可疑（会被 PyYAML 转成非字符串）:", suspicious[:10], "共", len(suspicious))

# 键里有冒号的（`通用:M10`）——解析器的分键规则必须用「冒号+空格」
colon_keys = set()
for mid, rec in sigs.items():
    for k, v in rec["boundary"].items():
        if isinstance(v, dict):
            for kk in v:
                if ":" in str(kk):
                    colon_keys.add(kk)
print("键内含冒号的样例:", sorted(colon_keys)[:6], "共", len(colon_keys))
