"""普查：全部模块文档围栏块里**所有**标量的解析后类型（不只 boundary 字段）。

界定 mini-YAML 需要复刻多少 YAML 1.1 标量解析。
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(".").resolve() / "desktop" / "src"))
from core import conformance_scan as csc  # noqa: E402

types = {}
samples = {}


def walk(v, where):
    t = type(v).__name__
    types[t] = types.get(t, 0) + 1
    if isinstance(v, dict):
        for k, vv in v.items():
            walk(vv, where + "." + str(k))
    elif isinstance(v, list):
        for vv in v:
            walk(vv, where + "[]")
    else:
        samples.setdefault(t, [])
        if len(samples[t]) < 8 and not isinstance(v, str):
            samples[t].append((where, repr(v)))


n_ok = n_none = 0
for d in csc._module_docs("."):
    t = Path(d).read_text(encoding="utf-8")
    p = csc._fence_yaml(t, "machine_contract")
    if not isinstance(p, dict) or not isinstance(p.get("machine_contract"), dict):
        n_none += 1
        continue
    n_ok += 1
    walk(p["machine_contract"], Path(d).name)

print("可解析模块:", n_ok, " 取不到 mc:", n_none)
print("全块类型分布:", types)
for t, ss in samples.items():
    print("  %-10s %s" % (t, ss[:6]))
