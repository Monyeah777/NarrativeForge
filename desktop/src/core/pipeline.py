"""全链管道化单一入口（v2.1.0 B2：retrieve→compose→gate→export 单命令）。

把 E4/E5 的检索/装载、E3 的组合合并（references 跨包）、E1 的导出，从
"脚本手串"（e2e_desktop_headless [8] 曾内联 build_assembly→render_ir→
run_gate→export 五步）升级为库级可串的 pipe() 单一入口——CLI/库先行
薄壳形态（L3_FROZEN.md：端壳冻结，CLI→库→GUI 一次性包络）的地基。

pipe(store, pipeline, selected, ...) -> PipeResult：
  selected(full_id 列表) → build_assembly(含 E3 references 并入)
  → render_ir(装配→IR) → run_gate(质检三态) → ok 且未禁用阻断 → export。
- 可信任度不变量（v1.4.0）：gate.n_fail>0 → PipeResult.ok=False；
  fail_on_gate=False 可强制导出（下游先看坏产物）但 ok 仍 False。
- 产物×适配矩阵（v2.0.x）：export fmt 走 exporter._REGISTRY（ccv3/skill）；
  skill 拒 narrative（适配器内拒出，warnings 带说明）——pipe 原样透传。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from .models import Pipeline
from .storage import Store
from .generator import render_ir
from .quality_gate import GateResult, run_gate
from .ir import IRDocument


@dataclass
class PipeResult:
    """pipe() 结果：IR 始终可查；gate 三态；export 仅门过（或 force）非 None。"""
    ok: bool
    ir: Optional[IRDocument] = None
    gate: Optional[GateResult] = None
    export: Optional["object"] = None    # ExportResult（exporter 模块）
    warnings: List[str] = field(default_factory=list)


def pipe(store: Store, pipeline: Pipeline,
         selected: List[str],
         *,
         include_references: bool = True,
         fmt: str = "ccv3",
         dest_dir=None,
         fail_on_gate: bool = True,
         ) -> PipeResult:
    """全链单命令：selected(full_id) → 装配+引用合并 → IR → 质检 → 导出。

    - selected：模块 full_id 列表；本地缺失项跳过并记入 warnings（不崩）。
    - include_references：E3 跨包 references 是否并入装配（默认并入）。
    - fmt/dest_dir：透传 exporter.export；fmt 未注册 → KeyError（显式暴露）。
    - fail_on_gate=False：质量门 fail 也导出（下游诊断用）——但 ok() 仍 False。
    """
    warnings: List[str] = []

    # ---- ① selected full_id → Module（跳过本地缺失，同 zone_d._collect_modules）----
    modules = []
    for fid in selected:
        m = store.get_module(fid)
        if m is None:
            warnings.append(f"勾选模块 {fid} 本地不存在，已跳过")
            continue
        modules.append(m)
    if not modules and selected:
        # 全缺：仍有空装配进入 render（门会 fail），但提示缺失
        pass

    # ---- ② compose：own + E3 references 跨包并入 ----
    from .composer import build_assembly
    asm = build_assembly(store, pipeline, modules,
                         include_references=include_references)

    # ---- ③ render_ir：装配 → IR ----
    ir = render_ir(pipeline, asm)
    warnings.extend(ir.warnings or [])

    # ---- ④ gate：IR 质检三态 ----
    gate = run_gate(ir)
    ok = gate.ok()

    # ---- ⑤ export：门过（或 force）才导出 ----
    export_res = None
    if ok or not fail_on_gate:
        from .exporter import export
        export_res = export(ir, fmt=fmt, dest_dir=dest_dir)
        warnings.extend(export_res.warnings or [])

    return PipeResult(ok=ok, ir=ir, gate=gate, export=export_res,
                      warnings=warnings)
