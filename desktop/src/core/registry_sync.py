"""协议登记同步（v2.1.0-B3-B：nf register 本地登记助手纯函数层）。

B3 自举闭环最后一段：把 protocol_projection 产物（protocol.yaml → registry
protocols[] 条目）**校验后**合并入 registry.json protocols[]，替代人工手抄投影。

- 三要件校验（对齐 02 §8.3 / §9.2）：
  ① 包根 protocol.yaml 在场可解析 + schema_version ∈ {1,2}；
  ② 包在 02 §8 在册（登记段 ### 8. → ## 9. 正文含包 id；领域包标题在册、
     通用/组合包段内登记实况——对齐 verify check15 ⑤ 的可寻址语义）；
  ③ registry protocols[] 现状（由调用方传 list，本层不碰 IO）。
- merge 语义：id 命中更新 / 缺失追加（保既有序）/ 多余不删（只增不删，V1 底线）/
  幂等（重复合并结果一致）。
- I5：本层是纯函数，绝不写 02 文档、不碰 modules/mount_points/subscriptions——
  写 registry.json 的 IO 由 nf.py 承担（最窄化：仅 protocols[] 数组替换）。
"""
from __future__ import annotations

import os
from typing import Any, Dict, List

import yaml


def _read_pkg(pkg_dir: str) -> Dict[str, Any]:
    """读包根 protocol.yaml → (data, pkg)。文件缺失/解析失败抛 ValueError。"""
    path = os.path.join(pkg_dir, "protocol.yaml")
    if not os.path.isfile(path):
        raise ValueError("① protocol.yaml 缺失：%s" % path)
    with open(path, encoding="utf-8") as f:
        try:
            data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError("① protocol.yaml 解析失败: %s" % e)
    if not isinstance(data, dict) or not isinstance(data.get("package"), dict):
        raise ValueError("① protocol.yaml 缺 package 段（01 §6.1 Schema）")
    return data


def check_registerable(pkg_dir: str, doc: str) -> List[str]:
    """校验三要件，返回 issues 列表（空 = 通过）。

    ② 02 在册判定：段标题 `### 8.x <包名>（…）` 含包 id（目录名即包 id）。
    注意：仅标题命中不足以保证「在册内容完整」——完整的 ⑤ 段反解在 verify.sh
    check14 ⑤ 承担；本层只做登记前置门槛（02 未在册 → 拒绝 nf register 写 json）。
    """
    issues: List[str] = []
    try:
        data = _read_pkg(pkg_dir)
    except ValueError as e:
        issues.append(str(e))
        return issues
    pkg = data["package"]
    sv = str(data.get("protocol", {}).get("schema_version", ""))
    if sv not in ("1", "2"):
        issues.append("① protocol.schema_version=%r（预期 v1 或 v2）" % sv)
    pid = str(pkg.get("id", ""))
    if not pid:
        issues.append("① package.id 缺失")
        return issues
    # ② 02 §8 在册：登记段（### 8. → ## 9. 区间）正文出现包 id 即视为在册。
    #    领域包以 `### 8.x <包名>` 标题在册（8.1/8.2）；通用/组合包在 8.3/8.4 段内
    #    登记实况正文（段标题为通用「第三方协议登记」/「组合管线登记」）——故不匹配
    #    标题而匹配登记段正文（verify check14 ⑤ 的标题反解仅对两领域包，nf 面向任意包）。
    seg_zone = doc[doc.find("### 8."):doc.find("## 9.")] if "### 8." in doc else ""
    if not seg_zone:
        issues.append("② 02 §8 登记段未找到（文档结构异常）")
    elif pid not in seg_zone:
        issues.append("② 包不在 02 §8 在册（登记三要件②缺失）：%s——须先在 02 §8.x 登记" % pid)
    return issues


def _normalize(entry: Dict[str, Any]) -> Dict[str, Any]:
    """条目规范化（module_ids 全 str、空列表字段兜底），保证合并可比较。"""
    return {
        "id": str(entry["id"]),
        "name": str(entry.get("name", entry["id"])),
        "pipeline": str(entry.get("pipeline", "")),
        "categories": [str(x) for x in entry.get("categories", [])],
        "module_ids": [str(x) for x in entry.get("module_ids", [])],
        "assets": dict(entry.get("assets") or {}),
        "mount_layers": dict(entry.get("mount_layers") or {}),
        "references": list(entry.get("references") or []),
        "schema_version": str(entry.get("schema_version", "")),
    }


def merge_protocols(reg_protocols: List[Dict[str, Any]],
                    entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """合并：id 命中更新（保原键序，仅覆盖差异键）/ 缺失追加 / 多余不删。

    幂等：重复调用结果一致（同 id 覆盖同值）；键序稳定（命中条目保留原序，
    避免 json.dump 重写污染既有条目的键序——registry.json 现存条目非统一键序）。
    """
    out = [dict(p) for p in reg_protocols]
    by_id = {p["id"]: i for i, p in enumerate(out)}
    for raw in entries:
        e = _normalize(raw)
        if e["id"] in by_id:
            idx = by_id[e["id"]]
            target = out[idx]
            for k, v in e.items():
                target[k] = v                 # 覆盖差异键，保留原键序
        else:
            out.append(e)                     # 缺失 → 末尾追加（只增不删）
    return out
