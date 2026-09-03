"""核心数据模型：Module / Pipeline / AssetPack / Preset。

对齐 NarrativeForge 协议与桌面工具指令集 3.3-3.5 的数据结构。
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Optional

# 模块分类（对应 04_模块库 顶层目录 + 桌面工具功能B的筛选）
CATEGORIES = ["情感类", "生存类", "世界类", "事件类", "通用类", "技术文档类"]


def fid_key(fid: str) -> str:
    """把 full_id 归一为协议比较键：类别段去『类』字后比较。

    存储层 category 为长名（情感类），而管线/标题/预设引用为短名（情感:M22），
    二者语义上指同一模块。统一比较键后 get_module / validator 允许集
    均能双向命中（情感:M22 ↔ 情感类:M22）。
    """
    if ":" in fid:
        c, i = fid.split(":", 1)
        return c.rstrip("类") + ":" + i
    return fid

# 九层骨架（P00 通用骨架声明；P01-P03 为叙事实例，层名可替换）
LAYER_IDS = ["P00", "P10", "P20", "P30", "P40", "P50", "P60", "P70", "P80"]

# 桌面工具指令集功能C：预设管线展示名 → 真实管线 id
PIPELINE_ALIASES = {
    "极简": "P00",
    "标准": "P01",
    "校园情感流": "P02",
    "西幻生存流": "P03",
    "技术文档": "P90",
    "世界优先": "P01",  # 兜底映射（P01 已含世界驱动），UI 层面另做结构图展示
    "情感优先": "P02",
    "全管线": "P03",
}


@dataclass
class Module:
    """模块定义（指令集 3.3 module.json）。

    id: 模块数字号，如 M22（情感:M22 带类前缀的写法在 category 字段分离）
    """
    id: str = ""
    name: str = ""
    category: str = "通用类"
    layer: str = "P40"               # 挂载层位 P00-P80
    replaceable: bool = True
    inputs: list = field(default_factory=list)      # 依赖的模块 id 列表
    outputs: list = field(default_factory=list)     # 输出数据键，如 "sexual:int"
    events_publish: list = field(default_factory=list)
    events_subscribe: list = field(default_factory=list)
    assets: list = field(default_factory=list)      # 引用的资产键
    logic: str = ""                   # 核心逻辑（伪代码/规则）
    source_md: str = ""               # 原始 markdown 全文（装配时拼接）
    enabled: bool = True
    installed_at: str = ""

    @property
    def full_id(self) -> str:
        """带类前缀的全名，如 情感:M22（仓库内同名不同类的消歧方式）"""
        if ":" in self.id:
            return self.id
        return f"{self.category}:{self.id}" if self.category else self.id

    def to_json(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_json(d: dict) -> "Module":
        m = Module()
        for k, v in d.items():
            if hasattr(m, k):
                setattr(m, k, v)
        return m

    def __repr__(self) -> str:
        return f"<Module {self.full_id} · {self.name} @{self.layer}>"


@dataclass
class PipelineLayer:
    """管线单层定义"""
    id: str = "P00"                   # 层位 id
    name: str = ""
    description: str = ""
    optional: bool = False
    default_modules: list = field(default_factory=list)
    allowed_modules: list = field(default_factory=list)


@dataclass
class Pipeline:
    """管线定义（对齐 03_管线库 YAML frontmatter）"""
    id: str = "P01"
    name: str = "标准管线"
    description: str = ""
    structure_type: str = "linear"    # linear / 回卷
    layers: list = field(default_factory=list)      # list[PipelineLayer]，按序
    dependencies: list = field(default_factory=list)  # list[dict{from,to,reason}]
    tags: list = field(default_factory=list)

    @property
    def layer_ids(self) -> list:
        return [l.id for l in self.layers]

    def layer(self, lid: str) -> Optional[PipelineLayer]:
        for l in self.layers:
            if l.id == lid:
                return l
        return None

    def to_json(self) -> dict:
        return {
            "id": self.id, "name": self.name, "description": self.description,
            "structure_type": self.structure_type,
            "layers": [asdict(l) for l in self.layers],
            "dependencies": self.dependencies, "tags": self.tags,
        }

    @staticmethod
    def from_json(d: dict) -> "Pipeline":
        p = Pipeline(id=d.get("id", "P01"), name=d.get("name", ""),
                     description=d.get("description", ""),
                     structure_type=d.get("structure_type", "linear"),
                     dependencies=d.get("dependencies", []),
                     tags=d.get("tags", []))
        p.layers = [PipelineLayer(**{k: v for k, v in l.items() if k in
                                     PipelineLayer.__dataclass_fields__})
                    for l in d.get("layers", [])]
        return p

    def __repr__(self) -> str:
        return f"<Pipeline {self.id} · {self.name} [{len(self.layers)}层]>"


@dataclass
class AssetPack:
    """资产包定义（指令集 3.4 asset.json）"""
    name: str = ""                    # 如 校园包 / 西幻包
    version: str = "1.0.0"
    entries: dict = field(default_factory=dict)  # {资产键: 内容/说明}
    source_dir: str = ""              # 资产文件目录（本地）
    installed_at: str = ""

    def to_json(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_json(d: dict) -> "AssetPack":
        a = AssetPack()
        for k, v in d.items():
            if hasattr(a, k):
                setattr(a, k, v)
        return a

    def __repr__(self) -> str:
        return f"<AssetPack {self.name} v{self.version} [{len(self.entries)}键]>"


@dataclass
class Preset:
    """预设配置（指令集 3.5 preset.json）"""
    name: str = "未命名预设"
    pipeline: str = "P01"
    modules: list = field(default_factory=list)   # 勾选的模块 full_id 列表
    asset_pack: str = ""
    created_at: str = ""

    def to_json(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_json(d: dict) -> "Preset":
        p = Preset()
        for k, v in d.items():
            if hasattr(p, k):
                setattr(p, k, v)
        return p

    def __repr__(self) -> str:
        return f"<Preset {self.name} · {self.pipeline} · {len(self.modules)}模块>"


def now_str() -> str:
    return datetime.now().isoformat(timespec="seconds")
