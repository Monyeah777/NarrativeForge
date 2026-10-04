"""勘查：machine_contract 围栏 YAML 的真实形态（决定 Rust 侧要支持多大的 YAML 子集）。"""
import sys
import re
from pathlib import Path

sys.path.insert(0, str(Path(".").resolve() / "desktop" / "src"))
from core import conformance_scan as csc  # noqa: E402

print("FENCE 正则 :", csc.FENCE.pattern)

docs = csc._module_docs(".")
print("模块文档数 :", len(docs))

blocks = []
for d in docs:
    t = Path(d).read_text(encoding="utf-8")
    m = csc.FENCE.search(t)
    if m:
        blocks.append((d, m.group(1)))

print("含围栏块   :", len(blocks))
if blocks:
    print("===== 首件全文块 (%s) =====" % blocks[0][0])
    print(blocks[0][1][:1500])

# 统计所有围栏块的形态特征（用于界定子集）
feat = {
    "带引号标量": 0, "裸标量": 0, "行内列表": 0, "块列表(- )": 0,
    "嵌套映射": 0, "多行折叠(|/>)": 0, "锚点(*&)": 0, "文档分隔(---)": 0,
    "制表符": 0, "非 ASCII 值": 0,
}
for _, b in blocks:
    for ln in b.splitlines():
        s = ln.strip()
        if not s or s.startswith("#"):
            continue
        if s.startswith("- "):
            feat["块列表(- )"] += 1
        if re.search(r":\s*\[", s):
            feat["行内列表"] += 1
        if re.search(r":\s*['\"]", s):
            feat["带引号标量"] += 1
        elif re.search(r":\s*\S", s):
            feat["裸标量"] += 1
        if re.search(r":\s*[|>]", s):
            feat["多行折叠(|/>)"] += 1
        if re.search(r"[&*]\w", s):
            feat["锚点(*&)"] += 1
        if s == "---":
            feat["文档分隔(---)"] += 1
        if "\t" in ln:
            feat["制表符"] += 1
        if any(ord(c) > 127 for c in s):
            feat["非 ASCII 值"] += 1
print("===== 形态统计 =====")
for k, v in feat.items():
    print("  %-14s %d" % (k, v))
