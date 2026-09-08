"""42 M2：回合状态头 v1（协议可执行性改造 —— AI 每回合见「此刻协议约束」）。

状态头 = C9 回合装载指针的运行态实例：每回合注入当前管线路径 / 已执行段 /
本回合必守铁律编号（判级器）。与 06 判级器段 + execution_drill 演练断言对齐。

- make_header()：确定性生成状态头（幂等：同参数同串）。
- replay_identity()：中断重入断言——从任意步重入恢复出的后续序列与连续执行一致
  （纯函数确定性底座：中断丢弃只是重新喂同一计划切片，输出逐字节一致）。
"""
from __future__ import annotations

from typing import List

HEADER_VERSION = "v1"

#: 判级器（06 §11 · RFC2119/8174 NF 化）——ID/强度/规则语义
LAWS = [
    {"id": "L1", "level": "必须", "name": "引用后执行",
     "text": "关键决策点先引用 §/行号/编号 再输出（编造零容忍）"},
    {"id": "L2", "level": "禁止", "name": "编造编号",
     "text": "模块/管线编号必须真实且属当前装配集"},
    {"id": "L3", "level": "禁止", "name": "浏览-复述",
     "text": "不得只复述文档不推进回合（须带推进信号）"},
    {"id": "L4", "level": "必须", "name": "职责自洽",
     "text": "提及模块职责须与 machine_contract 自洽（编号真实语义不得错位）"},
    {"id": "L5", "level": "应", "name": "可说明性豁免",
     "text": "默认行为可偏离，但须说明理由并记 WARN 档"},
]

LAW_INDEX = {law["id"]: law for law in LAWS}


def law_ids(level: str = "") -> List[str]:
    """按强度取铁律编号（空 = 全部）。"""
    return [law["id"] for law in LAWS if not level or law["level"] == level]


def make_header(pipeline_path: str, step: str,
                done: List[str], laws: List[str]) -> str:
    """确定性生成回合状态头（幂等：同参数产出同串）。"""
    laws = laws or law_ids()
    done_part = "、".join(done) if done else "装载"
    laws_part = "、".join(laws)
    return ("【回合状态头 %s】管线：%s｜已执行段：%s｜本回合：%s｜"
            "本回合铁律：%s（判级器见 06 §11）"
            % (HEADER_VERSION, pipeline_path, done_part, step, laws_part))


def _plan(pipeline_path: str, steps: List[str], laws: List[str],
          done0: List[str] = None) -> List[str]:
    out = []
    done = list(done0) if done0 else []
    for i, step in enumerate(steps):
        header = make_header(pipeline_path, step, list(done), laws)
        out.append(header + "\n执行：%s" % step)
        done.append(step)
    return out


def replay_identity(pipeline_path: str, steps: List[str],
                    interrupt_at: int, laws: List[str]) -> dict:
    """中断重入断言：连续执行 vs 中断后重入的输出切面一致性。

    - 连续执行：从头跑全部 step；
    - 中断重入：先跑到 interrupt_at 丢弃，再凭状态头（done = 前段）从断点续跑。
    纯确定性 → 两组后续输出应逐字节一致。
    """
    continuous = _plan(pipeline_path, steps, laws)
    replay = _plan(pipeline_path, list(steps), laws)  # 同参数重跑 = 幂等同串
    rejoin = _plan(pipeline_path, steps[interrupt_at:],
                   laws, done0=list(steps[:interrupt_at]))
    return {
        "idempotent": continuous == replay,
        "rejoin_matches": continuous[interrupt_at:] == rejoin,
    }
