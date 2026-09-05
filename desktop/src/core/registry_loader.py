"""注册表机读加载器（v0.6.0 T1.2 · 09 方案 §4 动作 1）。

02_联动注册表.md 是联动注册表的真相源（01 §5 I5 真相唯一），registry.json 是它的
机读投影（02 §9，v0.6.0 T1.1 引入，schema_version=2）。本模块是桌面 / Android 两端
消费该投影的**唯一入口**：核心装配逻辑一律经本模块读取注册表，禁止自行扫描模块目录或
硬编码模块清单 / 挂载关系（01 §5 I5、09 §4 T1.2 动作 2 收敛语义）。

职责边界（09 §4 T1.2）：
- registry_loader 管「模块表 / 挂载点 / 订阅」（02 §2 / §3 / §5 投影）；
- pipeline_loader 管「管线结构」（03_管线库 YAML）；两 loader 职责正交，互不替代。
- 注册表内容变更一律经 02 文档发起（02 §9.2 同步纪律），本模块只读不写。

对齐契约：
- 02 §2 限定 ID 规则：重号模块以类别前缀限定（通用:M10、事件:M22），内部引用一律限定
  ID；M91-M99 预留第三方段。裸号仅当该号段无前缀登记（全局唯一）时合法引用。
- 01 §6 R3 装配契约：题材内容经社区包自带 Pxx 管线装载；官方 P01 空层（optional:true）
  不阻塞主循环；社区包装配时追加 default/allowed 并同步注册表 mount_points 与
  execution_order。validate_assembly 即注册表侧装配合法性校验（R3 的机读落地）。
- 模块标识存在两种合法形态，本模块双向归一（对齐 models.fid_key）：
  A. 注册表形态：modules[].id 原样（裸号 M00 / 短前缀 通用:M10 / 事件:M22）；
  B. 模型形态：类别长名 + ":" + 裸号（通用类:M00 / 事件类:M22）——经 Store 安装的
     模块 models.Module.full_id 即此形态。

API（09 §4 T1.2 动作 1 四件套 + T1-3 只读寻址）：
- list_core_modules()         官方核心模块表（注册表登记 13 件）标识符列表
- get_module(module_id)       按标识符查模块条目（A/B 双形态 + 裸号唯一解引用）
- layer_mounts(layer_id)      某层挂载点（name/default/available/optional）
- validate_assembly(module_ids)  R3 装配校验（返回 issues；空列表 = 通过）
- asset_get(source_package, key)  跨包只读寻址源包资产（T1-3/v1.0.0，白名单授权
  + 路径规范化；仅 references.asset_readonly: true 声明的源包可寻址，只读不复制）
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import List, Optional, Union

from .models import fid_key

#: 技术文档领域派生实例挂载层（02 §7 P90）。modules 表登记 M90（source="核心（P90
#: 实证样例）"）但 02 §9 声明 P90 领域实例不纳入 mount_points 投影——validate_assembly
#: 层校验对 P90 豁免（设计意图而非遗漏）。
P90_DOMAIN_LAYER = "P90"


@dataclass
class Registry:
    """注册表机读投影的内存形态（对齐 registry.json / 02 §9.1 字段映射）。

    modules:       list[dict]  模块表原始条目（id/name/category/source/mounts/…）
    mount_points:  dict        {Pxx: {name, default, available, optional}}
    subscriptions: dict        {事件名: {publisher, subscribers, note}}
    """
    registry_schema_version: str = ""
    schema_name: str = ""
    registry_name: str = ""
    truth_source: str = ""
    modules: list = field(default_factory=list)
    mount_points: dict = field(default_factory=dict)
    subscriptions: dict = field(default_factory=dict)
    #: protocols[] 组合包投影（02 §8.4 组合登记 -> registry protocols[]；T1-3 消费
    #: references 白名单做只读寻址授权，不参与装配驱动——❌②纪律）。
    protocols: list = field(default_factory=list)

    # ---- 内部索引（fid_key(id) -> 条目；裸号 -> [条目]；构建时填充） ----
    _by_norm: dict = field(default_factory=dict, init=False, repr=False)
    _by_num: dict = field(default_factory=dict, init=False, repr=False)
    #: T1-3 跨包只读寻址白名单：protocols[].references[] 中 asset_readonly: true
    #: 声明的 source_package 集合（02 §8.4 / registry protocols[].references[]）。
    _readonly_sources: set = field(default_factory=set, init=False, repr=False)

    def __post_init__(self) -> None:
        for m in self.modules:
            mid = m.get("id", "")
            self._by_norm[fid_key(mid)] = m
            self._by_num.setdefault(mid.split(":")[-1], []).append(m)
        # T1-3：组合包 references 投影 -> 只读寻址授权表（空白名单 = 全拒）
        for p in self.protocols:
            for ref in p.get("references") or []:
                if ref.get("asset_readonly") is True and ref.get("source_package"):
                    self._readonly_sources.add(ref["source_package"])

    # ------------------------------------------------------------- 四件套 API
    def list_core_modules(self) -> List[str]:
        """官方核心模块表标识符列表（注册表登记全量——官方核心 13 件，含 M90）。

        02 §8 社区包模块 / M91-M99 第三方段不在此表（registry 只管官方核心层）。
        """
        return [m.get("id", "") for m in self.modules]

    def get_module(self, module_id: str) -> Optional[dict]:
        """按标识符查模块条目；未登记 / 歧义返回 None。

        解析顺序：
          1) 注册表形态直接命中（裸号 / 短前缀限定 id）；
          2) 模型形态长名（xx类:num）→ 短前缀归一命中；miss 且裸号段为裸登记
             且类别一致时解引用（通用类:M00 → M00）；
          3) 裸号：仅当该号段全部为裸登记（无前缀登记）时唯一解引用——M22/M10
             号段存在前缀登记（事件:M22 / 通用:M10）即重号段，裸号引用歧义须
             用限定 ID，返回 None（防与社区 情感:M22 / 生存:M10 错配）。
        """
        q = (module_id or "").strip()
        if not q:
            return None
        # 1) 注册表形态直接命中
        if q in self._by_norm:
            return self._by_norm[q]
        if ":" in q:
            cat, num = q.split(":", 1)
            if cat.endswith("类"):          # 2) 模型形态长名
                norm = cat[:-1] + ":" + num
                if norm in self._by_norm:
                    return self._by_norm[norm]
                cands = self._by_num.get(num, [])
                if (len(cands) == 1 and ":" not in cands[0]["id"]
                        and cands[0].get("category") == cat[:-1]):
                    return cands[0]
                return None
            # 短前缀形态 miss = 真不在注册表（短前缀 id 均直接登记于 _by_norm）
            return None
        # 3) 裸号：号段须无前缀登记（全局唯一）方可解引用
        cands = self._by_num.get(q, [])
        if len(cands) == 1 and ":" not in cands[0]["id"]:
            return cands[0]
        return None

    def layer_mounts(self, layer_id: str) -> Optional[dict]:
        """某层挂载点；层不在 mount_points（含 P90 领域实例层）返回 None。"""
        mp = self.mount_points.get(layer_id)
        return dict(mp) if mp else None

    def validate_assembly(self, module_ids: List[str]) -> List[str]:
        """R3 装配校验：给定装配模块 full_id 清单，校验注册表合法性。

        校验项：
          1) 空装配 → 提示未选择任何模块（与 validator.check_assembly 语义一致）；
          2) 每个引用须解析到注册表唯一模块（02 §2 限定 ID 规则：重号裸号歧义即
             未登记提示，须改用限定 ID）；
          3) 每个模块的挂载层须在注册表 mount_points 层集内（R3 同步契约的注册表
             侧边界；P90 领域实例层豁免——02 §7 / §9 声明不纳入投影）；
          4) 核心锚点（P00/P80 default：M00 / M80）须齐全（01 §5 I2 核心固定）。

        返回 list[str]；空列表 = 通过。community 模块（校园/西幻）不在此注册表，
        装配官方核心层之外的题材模块属社区包自带 Pxx 管线装载范畴（R3），不入本校验。
        """
        issues: List[str] = []
        if not module_ids:
            issues.append("未选择任何模块")
            return issues

        resolved: List[dict] = []
        for mid in module_ids:
            entry = self.get_module(mid)
            if entry is None:
                issues.append(
                    f"模块 {mid} 未在注册表登记（官方核心 13 件；重号须用限定 ID，"
                    f"如 事件:M22；社区模块经社区包 Pxx 管线装载不入本表）")
                continue
            resolved.append(entry)
            for mp in entry.get("mounts") or []:
                lid = mp.get("layer")
                if (lid and lid not in self.mount_points
                        and lid != P90_DOMAIN_LAYER):
                    issues.append(
                        f"模块 {entry.get('id')} 挂载层 {lid} 不在注册表 "
                        f"mount_points 层集内（P00-P80）")

        have_num = {e["id"].split(":")[-1] for e in resolved}
        for a in self.core_anchor_modules():
            if a not in have_num:
                issues.append(
                    f"提示：缺少核心模块 {a}（数据基座/输出呈现）")
        return issues

    # ------------------------------------------------------------- 收敛点助手
    def core_anchor_modules(self) -> List[str]:
        """装配必需锚点：数据基座层(P00)与输出呈现层(P80)的 default 模块。

        当前为 ["M00", "M80"]——取代 validator.check_assembly 的历史硬编码
        core_need={"M00","M80"}（09 §4 T1.2 动作 2 收敛点 CP1），数据源改为注册表
        mount_points 推导（01 §5 I2 核心固定：M00 数据结构 / M80 输出生成器）。
        """
        anchors: List[str] = []
        for lid in ("P00", "P80"):
            mp = self.mount_points.get(lid) or {}
            anchors.extend(mp.get("default") or [])
        return anchors
    # ---- T1-3 cross-package readonly asset addressing ----
    @staticmethod
    def _community_root() -> Optional[Path]:
        '''Locate community assets root (T1-3). desktop/src/core or
        android/app/core both reach repo root at parents[3]; probe each
        ancestor for community/ dir. None if absent.'''
        for anc in Path(__file__).resolve().parents:
            cand = anc / "community"
            if cand.is_dir():
                return cand
        return None

    def asset_get(self, source_package: str, key: str) -> Optional[str]:
        """Cross-package readonly asset addressing (T1-3): read text of
        community/<source_package>/assets/<key>.md when source_package is
        in the readonly whitelist (_readonly_sources, projected from
        protocols references asset_readonly); None otherwise. Path
        normalized: key must be a bare file base (no / or .. components)
        and the resolved target must stay inside the assets dir.
        Read-only: never copies/moves/writes (I5). Missing -> None."""
        if not source_package or not key:
            return None
        if source_package not in self._readonly_sources:
            return None
        root = self._community_root()
        if root is None:
            return None
        root_r = root.resolve()
        assets_dir = (root_r / source_package / "assets").resolve()
        if not assets_dir.is_dir() or not assets_dir.is_relative_to(root_r):
            return None
        k = key.strip()
        if k.endswith(".md"):
            k = k[:-3]
        if not k or "/" in k or ".." in k or k != Path(k).name:
            return None
        target = (assets_dir / (k + ".md")).resolve()
        if not target.is_relative_to(assets_dir):
            return None
        if not target.is_file():
            return None
        try:
            return target.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            return None

@lru_cache(maxsize=4)
def load_registry(path: Optional[Union[str, Path]] = None) -> Registry:
    """读取 registry.json → Registry（进程内缓存，只读不写）。

    path 缺省 = 本文件同目录 registry.json（desktop 与 android/app/core 经 sync
    整目录拷贝后同构，两端共用同一相对定位）。文件缺失 / JSON 损坏视为协议事故
    （I5 真相源投影缺失），原样抛 FileNotFoundError / JSONDecodeError——装配路径
    显式暴露，不静默回退硬编码。
    """
    p = Path(path) if path is not None else Path(__file__).with_name("registry.json")
    raw = json.loads(p.read_text(encoding="utf-8"))
    return Registry(
        registry_schema_version=raw.get("registry_schema_version", ""),
        schema_name=raw.get("schema_name", ""),
        registry_name=raw.get("registry_name", ""),
        truth_source=raw.get("truth_source", ""),
        modules=raw.get("modules", []),
        mount_points=raw.get("mount_points", {}),
        subscriptions=raw.get("subscriptions", {}),
        protocols=raw.get("protocols", []),
    )
