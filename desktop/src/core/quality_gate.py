"""质量治理门（v1.4.0 quality_gate：自定义质检门引擎，2.0 E0-③）。

- 质检在 **IR 层**跑（消费 v1.2 IRDocument，不解析 MD——质检与 v2.0 导出
  共享同一真源）。
- run_gate(ir, rules) -> GateResult：规则集逐条执行 → PASS/WARN/FAIL 三态。
- default_rules 预设四规则（语义对齐现有 validator/order_modules 缺漏提示）：
    fail：R1 空装配（无任何层模块且无层外）→ 无可产出内容
          R2 核心锚点缺失（P00 数据基座 / P80 输出呈现层无模块，registry 锚点）
    warn：W1 资产引用悬空（IR.asset_missing 非空，列缺失键）
          W2 层外模块（IR.extra_modules 非空，模块层不在管线层序）
- 可信任度不变量：存在任何 fail 级 Issue → GateResult.ok() 必须 False
  （fail 阻断"通过"，导出/发布不可在 fail 下声称合格）。
- v2.0：GUI 规则编辑器 + 导出前强制门（适配器内 run_gate）随导出层收口。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, List, Optional

from .ir import IRDocument


@dataclass
class Issue:
    level: str       # "pass" / "warn" / "fail"
    message: str
    #: B1 可解释化（v2.1.0）：actionable 修复指引——缺省空串向后兼容
    #: （现有构造 Issue(level, message) 两参仍成立）。
    suggestion: str = ""


@dataclass
class GateResult:
    n_pass: int = 0
    n_warn: int = 0
    n_fail: int = 0
    issues: List[Issue] = field(default_factory=list)

    def ok(self) -> bool:
        """可信任度不变量：fail 阻断通过。"""
        return self.n_fail == 0

    def report_text(self) -> str:
        """可解释报告（B1）：三态汇总 + 逐条 [LEVEL] 原因 → 修复建议。

        fail 优先列出（阻断项，须修复）；warn 次之（可行动项）；pass 不列
        （无问题无需展示）。无 issues 且 ok → 通过说明。
        """
        if not self.issues and self.ok():
            return "质量门通过：无质量问题。"
        lines = [
            f"质量门：PASS {self.n_pass} · WARN {self.n_warn}"
            f" · FAIL {self.n_fail}（{'可产出' if self.ok() else '存在 FAIL，须修复'}）",
            "",
        ]
        # fail 优先，再 warn
        for level, tag in (("fail", "FAIL"), ("warn", "WARN")):
            hits = [i for i in self.issues if i.level == level]
            if not hits:
                continue
            for i in hits:
                lines.append(f"[{tag}] {i.message}")
                if i.suggestion:
                    lines.append(f"    建议：{i.suggestion}")
        return "\n".join(lines)


Rule = Callable[[IRDocument], List[Issue]]


# ------------------------------------------------------------------ 规则集
def _r_empty_assembly(ir: IRDocument) -> List[Issue]:
    if not ir.layers and not ir.extra_modules:
        return [Issue("fail", "空装配：无任何层模块或层外模块，无可产出内容",
                      suggestion="在装配中勾选参与模块（至少含核心锚点 M00 数据基座"
                                 "/M80 输出呈现），或经 nf/pipe 传 selected 列表")]
    return []


def _r_core_anchor(ir: IRDocument) -> List[Issue]:
    """核心锚点：P00（数据基座）/P80（输出呈现）层须有模块（01 §5 I2 语义）。"""
    by_layer = {l.id: l for l in ir.layers}
    missing = []
    for anchor in ("P00", "P80"):
        layer = by_layer.get(anchor)
        if layer is None or not layer.modules:
            missing.append(anchor)
    if missing:
        return [Issue("fail", "核心锚点层缺失模块：" + "、".join(missing)
                      + "（数据基座/输出呈现，缺失则产物不完整）",
                      suggestion="勾选数据基座层(P00)与输出呈现层(P80)模块"
                                 "（M00 数据结构 / M80 输出生成器）——核心锚点，"
                                 "缺则产物不完整（01 §5 I2）")]
    return []


def _w_asset_missing(ir: IRDocument) -> List[Issue]:
    if ir.asset_missing:
        keys = "、".join(ir.asset_missing)
        return [Issue("warn", "资产引用悬空（本地资产包缺失）：" + keys,
                      suggestion="安装对应资产包（资产库/社区包），或从模块引用中"
                                 f"移除缺失键：{keys}")]
    return []


def _w_extra_modules(ir: IRDocument) -> List[Issue]:
    if ir.extra_modules:
        names = "、".join(m.full_id for m in ir.extra_modules[:5])
        return [Issue("warn", "层外模块（不在管线层序内）：" + names
                      + ("…" if len(ir.extra_modules) > 5 else ""),
                      suggestion="把层外模块移入管线声明的层位（改模块 layer），"
                                 "或改管线层序容纳它（I5：管线登记为真相源）")]
    return []


def default_rules() -> List[Rule]:
    return [_r_empty_assembly, _r_core_anchor,
            _w_asset_missing, _w_extra_modules]


# ------------------------------------------------------------------ 执行
def run_gate(ir: IRDocument,
             rules: Optional[List[Rule]] = None) -> GateResult:
    """执行质检门。rules 缺省 = default_rules()。"""
    result = GateResult()
    for rule in rules if rules is not None else default_rules():
        for issue in rule(ir):
            result.issues.append(issue)
            if issue.level == "fail":
                result.n_fail += 1
            elif issue.level == "warn":
                result.n_warn += 1
            else:
                result.n_pass += 1
    return result
