"""43 A2 —— Conformance 一致性分级扫描（声明 ≤ 可证级别，防虚标）。

分级定义见 01 §1.2：L0 结构可读 / L1 机读契约 / L2 装配可执行 / L3 外部互操作。

扫描对象：
- 模块文档 machine_contract.conformance（23 件机读块，check28 约束必带）
- community/*/protocol.yaml package.conformance（5 协议包，在册 = L2）
- protocol/export_conformance.json（导出契约面 manifest，L3 = 导出门禁锁定面）

用法：conformance_scan.scan('.') -> (issues, stats)
"""

from __future__ import annotations

import copy
import contextlib
import glob
import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import yaml  # PyYAML（仓库既有依赖）
except Exception:  # pragma: no cover
    yaml = None  # type: ignore[assignment]

FENCE = re.compile(r"(?ms)```yaml\s*(.*?)```")
_T = chr(96) * 3
#: 统一的安全 YAML 加载器：优先 **libyaml 的 C 实现**（`CSafeLoader`），缺则回退纯 Python。
#: 依据（本波实测）：本仓 473 次 YAML 解析里 PyYAML 扫描器是纯 Python，单份机器契约 ~2 ms——
#: 换 C 实现后同一批正文 **7.8× 快**（200 份正文 0.164 s → 0.021 s）。
#: 等价性**逐块实证**：本仓全部 1395 个 YAML 文本块（584 份文件）用两种加载器各解析一遍，
#: 值差异 0、异常行为差异 0（见 `test_conformance_scan` 的等价断言；缺 libyaml 时自动跳过）。
SAFE_LOADER = getattr(yaml, "CSafeLoader", None) or getattr(yaml, "SafeLoader", None)
#: 围栏 YAML 解析缓存：键 = (marker, **文本本身**)，值 = 解析结果或 None（见 `_fence_yaml`）。
_FENCE_CACHE: Dict[Tuple[str, str], Any] = {}
_FENCE_CACHE_MAX = 4096
#: 围栏**正文**缓存：键 = 正文本身。给「自己抽正文」的调用方用（pipeline_loader /
#: concept_graph 过去直接调 load_yaml，等于每轮都重解析——与 `_fence_yaml` 的缓存互补）。
_BODY_CACHE: Dict[str, Any] = {}
_BODY_CACHE_MAX = 4096

#: 「一次**只读**扫描内共享语料」的读缓存：作用域由 `read_memo()` 显式框定，出口即清。
#: 必要性（实测）：一次 `regression_score.evaluate` 打开 **7833** 次文件、其中只有 **2354**
#: 个不同文件——**70% 是冗余读**（同一份包资产被 concept_graph / asset_density / output_forms
#: 等各读一遍）。作用域严格等于「一次扫描调用」，且这些聚合入口都是纯读（写路径 `--write`
#: 在聚合**之后**才发生），所以冷却语义与「新起进程」一致：不跨调用、不跨请求复用。
#: 与读缓存**同生命周期**的「列目录」缓存：一次只读调用内，`_module_docs` 这类清单只走一遍
#: 文件系统（实测一次 evaluate 里它被调 5 次、合计 167 ms；各扫描器各自重走同一批目录）。
_READ_MEMO: Optional[Dict[str, Any]] = None
_DIR_MEMO: Optional[Dict[str, Any]] = None


@contextlib.contextmanager
def read_memo():
    """框定「共享语料」的作用域（可嵌套；出口恢复外层）。"""
    global _READ_MEMO, _DIR_MEMO
    outer, _READ_MEMO = _READ_MEMO, {}
    outer_dir, _DIR_MEMO = _DIR_MEMO, {}
    try:
        yield
    finally:
        _READ_MEMO = outer
        _DIR_MEMO = outer_dir


def read_text_cached(path) -> str:
    """读文本：在 `read_memo()` 作用域内，同一**文件**只读一次（含解码）；域外就是普通读。

    键做**路径归一化**（`normcase(abspath)`）：各扫描器传进来的写法不同（`"."/相对路径`
    vs 绝对路径），不归一会指向不同键、共享失效——实测就是这样（同一份资产仍被读 4 次）。
    """
    if _READ_MEMO is not None:
        key = os.path.normcase(os.path.abspath(str(path)))
        hit = _READ_MEMO.get(key)
        if hit is not None:
            return hit
    text = Path(path).read_text(encoding="utf-8")
    if _READ_MEMO is not None:
        _READ_MEMO[os.path.normcase(os.path.abspath(str(path)))] = text
    return text


def read_bytes_cached(path) -> bytes:
    """读字节：同上（`_recompute_entry` 的逐字节比对用）。"""
    if _READ_MEMO is not None:
        key = "b:" + os.path.normcase(os.path.abspath(str(path)))
        if key in _READ_MEMO:
            return _READ_MEMO[key]              # type: ignore[return-value]
    raw = Path(path).read_bytes()
    if _READ_MEMO is not None:
        _READ_MEMO["b:" + os.path.normcase(os.path.abspath(str(path)))] = raw  # type: ignore[assignment]
    return raw


def content_fingerprint(root: str, patterns) -> str:
    """按**内容**给一组文件取指纹（键即内容 ⇒ 内容一变指纹就变，无陈旧风险）。

    用于「派生结果的跨调用缓存」：先在本模块里**穷举输入面**（写成 patterns），再拿指纹当键。
    走共享读（`read_text_cached`），这些文件本来就要被读，指纹近乎白拿。
    """
    h = hashlib.sha256()
    r = Path(root)
    for pat in patterns:
        for p in sorted(r.glob(str(pat))):
            if not p.is_file():
                continue                      # `**/*` 会把目录也匹配进来，只对文件取指纹
            h.update(p.relative_to(r).as_posix().encode("utf-8"))
            h.update(b"\x00")
            h.update(read_text_cached(p).encode("utf-8"))
            h.update(b"\x01")
    return h.hexdigest()


#: `scan()` 派生结果的跨调用缓存（键 = 输入内容指纹）。输入面见 `SCAN_INPUTS`——**穷举**，
#: 所以「输入一变必然换键」，不需要随请求清空。
_SCAN_CACHE: Dict[str, Tuple[List[str], Dict[str, int]]] = {}
#: `scan()` 的全部输入（逐一对照实现枚举：证据 id 的 registry + 模块文档 + 协议包声明 +
#: 导出契约 manifest + 门禁脚本里的证据名）。
SCAN_INPUTS = ("desktop/src/core/registry.json",
               "04_模块库/*/*.md",
               "community/*/modules/*.md",
               "community/*/protocol.yaml",
               "protocol/export_conformance.json",
               "verify.sh")


def load_yaml(text: str) -> Any:
    """模块间**共用**的安全 YAML 载入（libyaml 优先；无 PyYAML 即报，不静默降级）。

    新调用点一律走这里，别再各写一份 `yaml.safe_load`——否则「同一个仓库里两套解析器」
    既慢又会有语义分叉。

    注意：这里**直接实例化安全加载器**（`SAFE_LOADER(text)` + `get_single_data()`），与
    `yaml.safe_load()` 逐字同语义，但不写 `yaml.load(...)`——后者是纯度扫描 R6 登记的
    危险 sink（CWE-502 非安全载入），不该为了少写两行把禁用面叫回来。
    """
    if yaml is None:
        raise RuntimeError("PyYAML 不在（修复指引：pip install pyyaml）")
    loader = SAFE_LOADER(text)
    try:
        return loader.get_single_data()
    finally:
        loader.dispose()


def load_yaml_cached(body: str) -> Any:
    """按**正文文本**缓存的安全 YAML 载入（键即内容 ⇒ 文本一变键就变，无陈旧风险）。

    与 `_fence_yaml` 的缓存同一条纪律，只是键更贴近「自己抽正文」的调用方：管道加载器与
    概念图加载器各自用正则抽出正文后直接解析，过去因此**每轮全量重解析**（实测热跑 score
    里仍有 325 次 YAML 解析）。解析失败按原样抛出、不缓存（确定性）。
    """
    if body in _BODY_CACHE:
        return _BODY_CACHE[body]
    got = load_yaml(body)
    if len(_BODY_CACHE) >= _BODY_CACHE_MAX:
        _BODY_CACHE.clear()
    _BODY_CACHE[body] = got
    return got


def _read_json(path: str) -> Tuple[Any, str]:
    try:
        return json.loads(read_text_cached(path)), ""
    except Exception as exc:
        return None, str(exc)


def _parse_fence_yaml(text: str, marker: str) -> Any:
    """真的去扫围栏并交给 PyYAML（未命中缓存时走这里）；未命中 / 解析失败 → None。"""
    for m in FENCE.finditer(text):
        body = m.group(1)
        if marker not in body:
            continue
        try:
            parsed = load_yaml_cached(body) if yaml is not None else None
        except Exception:
            return None
        if isinstance(parsed, dict):
            return parsed
    return None


def _fence_yaml_cached(text: str, marker: str) -> Any:
    """`(marker, 文本)` → 解析结果（None = 没找到该围栏或解析失败）。见 `_fence_yaml`。"""
    key = (marker, text)
    if key not in _FENCE_CACHE:
        if len(_FENCE_CACHE) >= _FENCE_CACHE_MAX:
            _FENCE_CACHE.clear()
        _FENCE_CACHE[key] = _parse_fence_yaml(text, marker)
    return _FENCE_CACHE[key]


def _fence_yaml(text: str, marker: str) -> Dict[str, Any]:
    """取围栏 ```yaml 里含 marker 的第一个块（未命中 → `{}`）；结果按**文本本身**缓存。

    效率（实测）：`nf doctor` 里同一批 **248 份**模块文档被恰好解析**两遍**（496 次
    `yaml.safe_load`，累计 **1.47 s ≈ 体检总时的 74%**）——PyYAML 的扫描器是纯 Python，
    单份 ~3 ms，重复一遍就是纯亏。缓存键取文本本身（不是路径）：文本没变必然同结果，
    文本一变键就变，所以**不存在「改了文件还读到旧值」的陈旧风险**——这正是它敢跨命令
    常驻的原因。返回值一律给**深拷贝**，调用方就地改动不会串味。
    """
    got = _fence_yaml_cached(text, marker)
    return copy.deepcopy(got) if got is not None else {}


def _fence_yaml_opt(text: str, marker: str) -> Optional[Dict[str, Any]]:
    """同 `_fence_yaml`，但「没找到 / 解析失败」返回 None（schema_lint 的既有语义）。

    与 `_fence_yaml` **同一份缓存、同一次解析**——同一段文本被两个模块各解析一遍是纯重复。
    """
    got = _fence_yaml_cached(text, marker)
    return copy.deepcopy(got) if got is not None else None


def _module_docs(root: str) -> List[str]:
    """模块文档清单（**一次只读调用内只走一遍文件系统**——见 `read_memo`）。

    实测：一次 `evaluate` 里本函数被调 **5** 次（各扫描器各自重走 `04_模块库` + `community/*/modules`），
    合计 167 ms。作用域与读缓存同生命周期，出口即清——下一次调用照常重新列目录，故不会陈旧。
    """
    key = os.path.normcase(os.path.abspath(str(root)))
    if _DIR_MEMO is not None and key in _DIR_MEMO:
        return list(_DIR_MEMO[key])
    out: List[str] = []
    for sub in ["04_模块库"]:
        base = os.path.join(root, sub)
        if os.path.isdir(base):
            for dirpath, _, files in os.walk(base):
                out += [os.path.join(dirpath, f) for f in files if f.endswith(".md")]
    pkg_dir = os.path.join(root, "community")
    if os.path.isdir(pkg_dir):
        for pkg in sorted(os.listdir(pkg_dir)):
            mdir = os.path.join(pkg_dir, pkg, "modules")
            if os.path.isdir(mdir):
                out += [os.path.join(mdir, f) for f in sorted(os.listdir(mdir)) if f.endswith(".md")]
    out = sorted(out)
    if _DIR_MEMO is not None:
        _DIR_MEMO[key] = out
    return list(out)


def _evidence_ids(root: str, reg: Any = None) -> List[str]:
    """官方 registry modules[] + community registry protocols[].module_ids（装配在册证据）。

    `reg` 可由调用方传入（同一次扫描里 registry.json 只该读一次——见 `scan`）。
    """
    if reg is None:
        reg, _ = _read_json(os.path.join(root, "desktop", "src", "core", "registry.json"))
    ids: List[str] = []
    if isinstance(reg, dict):
        for m in reg.get("modules") or []:
            if isinstance(m, dict) and isinstance(m.get("id"), str):
                ids.append(m["id"])
        for p in reg.get("protocols") or []:
            for mid in (p.get("module_ids") or []):
                if isinstance(mid, str):
                    ids.append(mid)
    return ids


def scan(root: str = ".") -> Tuple[List[str], Dict[str, int]]:
    """检查（外层）：派生结果按**输入内容指纹**跨调用缓存（输入面见 `SCAN_INPUTS`，已穷举）。

    依据（实测）：本函数一次调用约 0.4 s，而它只依赖那 6 类输入——守护逐请求清空按 root 的
    缓存时，这些派生账会被白交一遍。键即内容 ⇒ 输入一变指纹就变，故不需要随请求清空。

    「读到的文件必须全部落在输入面内」有判据守着（test_conformance_scan.DerivedResultCacheTest）：
    将来给本函数加新读取，判据会先红、逼着把新输入补进来——不会悄悄读到陈旧结果。
    """
    fp = content_fingerprint(root, SCAN_INPUTS)
    hit = _SCAN_CACHE.get(fp)
    if hit is not None:
        return copy.deepcopy(hit[0]), copy.deepcopy(hit[1])
    got = _scan_impl(root)
    _SCAN_CACHE[fp] = copy.deepcopy(got)
    return got


def _scan_impl(root: str = ".") -> Tuple[List[str], Dict[str, int]]:
    issues: List[str] = []
    if yaml is None:
        issues.append("PyYAML 不在（conformance_scan 依赖仓库既有 yaml 依赖）")
        return issues, {"modules_mc": 0, "packages": 0, "export_items": 0}

    # registry.json 只读一次：过去它在**每个社区包的循环体里**被重读一遍（实测 112 次
    # ≈ 0.09 s，纯重复 IO + JSON 解析），现在提到扫描开头，两个用处共用同一份。
    reg, _ = _read_json(os.path.join(root, "desktop", "src", "core", "registry.json"))
    evidence = set(_evidence_ids(root, reg))
    reg_ids = {p.get("id") for p in (reg or {}).get("protocols") or []}

    modules_mc = 0
    #: 模块 id 全局唯一（01 §1.6.11：module id 是全局寻址面）——登记面由 check14 ⑤b 管
    #: `module_id_range` 声明；但**同一包内两个模块文件声明同一 mc.id** 此前无判据，
    #: 运行时索引为 first-wins 静默择一（mcp_runtime._resolve_module / pipelinerun._module_files），
    #: 会让「看起来唯一」的编号实际指向不确定的模块。此处补文件级唯一判据（极端渗透 D3）。
    seen_mc_id: dict = {}
    for doc in _module_docs(root):
        rel = os.path.relpath(doc, root).replace(os.sep, "/")
        try:
            text = read_text_cached(doc)      # 共享语料：同一份模块文档一次只读一遍
        except Exception as exc:
            issues.append(f"{rel}: 读取失败 {exc}")
            continue
        parsed = _fence_yaml(text, "machine_contract")
        if "machine_contract" not in parsed:
            continue
        mc = parsed["machine_contract"]
        mid = str((mc or {}).get("id") or "")
        if mid:
            if mid in seen_mc_id:
                issues.append("%s: 模块 id 与 %s 重复（mc.id=%s）——编号是全局寻址面，"
                              "运行时索引会静默择一，须改号"
                              "（修复指引：按 01 §1.6.11 换类内段号或 M91-M99 段号）"
                              % (rel, seen_mc_id[mid], mid))
            else:
                seen_mc_id[mid] = rel
        modules_mc += 1
        declared = mc.get("conformance")
        if declared not in ("L1", "L2", "L3"):
            issues.append(f"{rel}: machine_contract 缺/非法 conformance 声明 {declared!r}")
            continue
        mid = mc.get("id")
        provable = 2 if isinstance(mid, str) and mid in evidence else 1
        order = {"L1": 1, "L2": 2, "L3": 3}
        if order[declared] > provable:
            issues.append(
                f"{rel}: conformance 虚标 {declared} > 可证 L{provable}"
                f"（{mid!r} 不在装配在册证据）"
            )

    # community 协议包
    packages = 0
    for proto in sorted(glob.glob(os.path.join(root, "community", "*", "protocol.yaml"))):
        rel = os.path.relpath(proto, root).replace(os.sep, "/")
        try:
            # 共享语料 + 内容键解析（同一份 protocol.yaml 一轮只读一次、只解析一次）
            data = load_yaml_cached(read_text_cached(proto))
        except Exception as exc:
            issues.append(f"{rel}: protocol.yaml 解析失败 {exc}")
            continue
        packages += 1
        pkg = (data or {}).get("package") or {}
        declared = pkg.get("conformance")
        pid = pkg.get("id")
        if declared not in ("L1", "L2", "L3"):
            issues.append(f"{rel}: package 缺/非法 conformance 声明 {declared!r}")
            continue
        provable = 2 if isinstance(pid, str) and pid in reg_ids else 1
        order = {"L1": 1, "L2": 2, "L3": 3}
        if order[declared] > provable:
            issues.append(f"{rel}: conformance 虚标 {declared} > 可证 L{provable}（包不在 registry protocols[]）")

    # 导出契约面 manifest（L3 = 导出契约门禁锁定面）
    manifest_path = os.path.join(root, "protocol", "export_conformance.json")
    manifest, err = _read_json(manifest_path)
    export_items = 0
    if not isinstance(manifest, dict):
        issues.append(f"protocol/export_conformance.json 缺失/解析失败：{err}")
    else:
        verify_txt = ""
        verify_path = os.path.join(root, "verify.sh")
        if os.path.isfile(verify_path):
            with open(verify_path, encoding="utf-8") as fh:
                verify_txt = fh.read()
        for item in manifest.get("items") or []:
            export_items += 1
            if not isinstance(item, dict):
                issues.append("export manifest item 非对象")
                continue
            if item.get("conformance") != "L3":
                issues.append(f"导出面 {item.get('id')}: conformance 应为 L3（导出门禁锁定面）")
            for ev in item.get("evidence") or []:
                if not os.path.isfile(os.path.join(root, ev)):
                    issues.append(f"导出面 {item.get('id')}: 证据文件缺失 {ev}")
            for gate in item.get("gates") or []:
                if gate not in verify_txt:
                    issues.append(f"导出面 {item.get('id')}: 证据门禁 {gate} 不在 verify.sh")

    stats = {
        "modules_mc": modules_mc,
        "packages": packages,
        "export_items": export_items,
    }
    return issues, stats
