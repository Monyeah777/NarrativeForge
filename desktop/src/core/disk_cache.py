"""内容寻址的**持久**缓存：把「内容的纯函数」结果移出进程生命周期。

用途：执行层里最贵的几笔账（引用度普查、产出面逐件校验、一致性分级扫描…）都是**输入内容的
纯函数**，但每开一个新进程就要重付一遍。把它们按内容寻址落到盘上，新进程直接取回。

键 = `sha256(标签 | 代码面内容 | 运行时标签 | 调用方给的各段键)`

- **代码面内容**（`desktop/src/**/*.py` + `scripts/**/*`，实测 157 件 / 41 ms）：把「算这段的
  函数本身」也放进键里，于是 **改了算法必然换键**——不需要靠"记得手工 bump 版本标签"这种脆弱
  纪律（漏 bump 就等于悄悄拿旧算法的结果当新结果）。
- **运行时标签**：Python 版本 / 平台 / PyYAML 是否在场——软依赖的有无会改变结果。
- **调用方给的各段键**：各自的输入面内容指纹（例如产出面的 `INDEX_INPUTS`）。

落点：`<NF_HOME>/cache/<tag>/<key>.json`（**不在仓库内**，故仓库纯净与门禁不受影响）。

纪律（fail-closed）：
1. 读回必须**校验**（调用方给 `validate`）：结构不对 / 键集不符 / 半截 JSON → 一律当没命中；
2. 一切 IO **尽力而为**：写不进、读不到都静默回落重算，绝不影响命令结果；
3. `NF_NO_DISK_CACHE=1` 整体关闭（读写皆废）；
4. 每个标签只留最近 `KEEP` 份（按 mtime 裁剪），缓存不得无界增长。
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Callable, Optional

ENV_OFF = "NF_NO_DISK_CACHE"
KEEP = 16
#: 参与「代码面」的路径（改了算法即换键；不含 tests——测试不影响结果）。
CODE_FACE = ("desktop/src/**/*.py", "scripts/**/*")

_CODE_FP: dict = {}                      # root → 代码面指纹（**按根记忆**：换根不得串味）
_RUNTIME: Optional[str] = None


def enabled() -> bool:
    return not os.environ.get(ENV_OFF)


def root_dir() -> Path:
    from core import storage
    return storage.default_home() / "cache"


def dir_for(tag: str) -> Path:
    return root_dir() / str(tag)


def runtime_tag() -> str:
    """运行时标签：软依赖与解释器在场与否**会改变结果**，故必须进键。"""
    global _RUNTIME
    if _RUNTIME is None:
        import sys
        try:
            import yaml
            yaml_bit = "yaml=%s" % getattr(yaml, "__version__", "?")
        except Exception:                              # noqa: BLE001 - 缺 PyYAML 是合法状态
            yaml_bit = "yaml=none"
        _RUNTIME = "%d.%d.%d|%s|%s" % (sys.version_info[0], sys.version_info[1],
                                       sys.version_info[2], os.name, yaml_bit)
    return _RUNTIME


def code_fingerprint(root: str = ".") -> str:
    """代码面内容指纹（**按根**进程内记忆；实测 41 ms）。

    按根记忆是必须的：早先写成单变量时，换一棵树会拿回上一棵树的指纹——判据当场抓住
    （`test_code_fingerprint_tracks_code_content`）。守护在**判定代码已换版**时要调
    `reset_code_fingerprint()`，否则会拿旧算法的键去命中盘上旧算法的账。
    """
    rkey = os.path.normcase(os.path.abspath(str(root)))
    hit = _CODE_FP.get(rkey)
    if hit is None:
        from core import conformance_scan as csc
        hit = csc.content_fingerprint(str(root), CODE_FACE)
        _CODE_FP[rkey] = hit
    return hit


def reset_code_fingerprint(root: Optional[str] = None) -> None:
    """清掉代码面指纹记忆（守护判定「代码已换版」后调用；不给 root 则全清）。"""
    if root is None:
        _CODE_FP.clear()
        return
    _CODE_FP.pop(os.path.normcase(os.path.abspath(str(root))), None)


def key(tag: str, *parts: str, root: str = ".") -> str:
    """算缓存键：标签 + 代码面 + 运行时 + 调用方给的各段。"""
    h = hashlib.sha256()
    for piece in ("v1", str(tag), code_fingerprint(root), runtime_tag()) + tuple(
            str(p) for p in parts):
        h.update(piece.encode("utf-8"))
        h.update(b"\x00")
    return h.hexdigest()


def _path(tag: str, ckey: str) -> Path:
    return dir_for(tag) / ("%s.json" % ckey)


def load(tag: str, ckey: str,
         validate: Optional[Callable[[Any], bool]] = None) -> Any:
    """读回缓存值；**任何不可信**一律返回 None（宁可重算，不可错答）。"""
    if not enabled():
        return None
    try:
        got = json.loads(_path(tag, ckey).read_text(encoding="utf-8"))
    except Exception:                                  # noqa: BLE001 - 缺件/半截/不可读
        return None
    if validate is not None:
        try:
            if not validate(got):
                return None
        except Exception:                              # noqa: BLE001 - 校验器自己炸也算不可信
            return None
    return got


def store(tag: str, ckey: str, value: Any) -> None:
    """写盘（尽力而为）：原子替换 + 裁剪；失败静默。"""
    if not enabled():
        return
    try:
        d = dir_for(tag)
        d.mkdir(parents=True, exist_ok=True)
        p = _path(tag, ckey)
        tmp = p.with_name(p.name + ".tmp")
        with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(value, ensure_ascii=False, sort_keys=True))
        os.replace(tmp, p)                             # 原子替换：读者看不到半截 JSON
        prune(tag)
    except Exception:                                  # noqa: BLE001 - 写不进就算了
        return


def prune(tag: str, keep: int = KEEP) -> None:
    """只留最近 `keep` 份（按 mtime）。"""
    try:
        d = dir_for(tag)
        entries = sorted(d.glob("*.json"), key=lambda q: q.stat().st_mtime, reverse=True)
        for old in entries[keep:]:
            old.unlink()
    except Exception:                                  # noqa: BLE001 - 裁剪失败不影响结果
        return
