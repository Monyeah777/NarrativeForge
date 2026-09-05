"""协议投影生成器（v2.1.0 B3-A：protocol.yaml → registry.json protocols[] 条目）。

- 消除手工投影漂移：读 community/* 包根 protocol.yaml，产 registry.json protocols[]
  应并入的条目（字段逐一对齐 check14 ⑦ 元素级断言 + check15 ⑤ references 双源）。
- 语义（对齐 02 §9.1 字段映射 + verify.sh check14 ⑦ 断言同构）：
    module_ids    = protocol.yaml package.module_id_range（列表全序）
    mount_layers  = 键归一后 {Pxx: {name, default, available}}——protocol 键为长键
                    （"P40 行为决策"），registry 形态为短键 P40；层内 name 取自长键
                    第二段（有则填，无则空）；default/available 逐层透传。
    references    = protocol.yaml package.references（含 source_package /
                    module_id / source_schema_version / asset_readonly，v0.8.0）
- I5 纪律：产物是「应并入条目」——人工合并入 registry.json（02 §9.2 登记自动化
  留后续，B 最后一公里）；本生成器让投影从手写变半自动可核。
- 非目标：不写 registry.json（只读 registry_loader 纪律）；不校验 02 §8 在册段
  （编号段归属 check14 ⑤，非投影职责）。
"""
from __future__ import annotations

import glob
import os
from typing import Any, Dict, List

import yaml

#: registry.json 内资产形态（真实实例：通用/轻混包 count=0、readme=README.md）
_ASSETS_DEFAULT = {"count": 0, "readme": "README.md"}


def _layer_key(key: Any) -> str:
    """mount_layers 键归一：protocol 长键（'P40 行为决策'）→ Pxx 短键（registry 形态）。"""
    s = str(key)
    return s.split()[0] if s.split() else s


def _layer_name(key: Any) -> str:
    """长键第二段为层显示名（registry mount_layers 值内 name 字段来源）。"""
    s = str(key).split(None, 1)
    return s[1] if len(s) > 1 else ""


def project_entry(pkg_dir: str) -> Dict[str, Any]:
    """读 <pkg_dir>/protocol.yaml → registry.json protocols[] 应并入条目 dict。

    字段对齐 02 §9.1 映射 + check14 ⑦ 元素级断言（module_ids 全序、mount_layers
    层集/每层 default/available、assets.count）+ check15 ⑤ references 双源。
    """
    with open(os.path.join(pkg_dir, "protocol.yaml"), encoding="utf-8") as f:
        data = yaml.safe_load(f)
    pkg = data["package"]
    proto = data.get("protocol", {})
    ml_raw = pkg.get("mount_layers") or {}

    mount_layers: Dict[str, Dict[str, Any]] = {}
    for raw_key, spec in ml_raw.items():
        key = _layer_key(raw_key)
        spec = spec if isinstance(spec, dict) else {}
        mount_layers[key] = {
            "name": (spec.get("name") if spec.get("name") else _layer_name(raw_key)),
            "default": list(spec.get("default") or []),
            "available": list(spec.get("available") or []),
        }

    assets = dict(pkg.get("assets") or {})
    assets.setdefault("count", _ASSETS_DEFAULT["count"])
    assets.setdefault("readme", _ASSETS_DEFAULT["readme"])

    return {
        "id": pkg["id"],
        "name": pkg["name"],
        "pipeline": pkg["pipeline"],
        "categories": list(pkg.get("categories") or []),
        "module_ids": [str(x) for x in (pkg.get("module_id_range") or [])],
        "assets": assets,
        "mount_layers": mount_layers,
        "references": list(pkg.get("references") or []),
        "schema_version": proto.get("schema_version", ""),
    }


def project_all(community_root: str = "community") -> List[Dict[str, Any]]:
    """扫描 community/* 含 protocol.yaml 的包 → 全部条目（按包名排序）。

    判据与 check14 ①/⑦ 同构：目录含 protocol.yaml 即视为登记包（含组合/通用包）。
    """
    entries = []
    for d in sorted(glob.glob(os.path.join(community_root, "*"))):
        if os.path.isdir(d) and os.path.isfile(os.path.join(d, "protocol.yaml")):
            entries.append(project_entry(d))
    return entries
