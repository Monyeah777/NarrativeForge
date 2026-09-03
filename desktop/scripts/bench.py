#!/usr/bin/env python3
"""性能基准：验收 10（启动 <3s）与验收 11（生成 100 模块 <10s）。

用法：
    python3 scripts/bench.py
数据目录优先取 $NARRATIVE_FORGE_HOME；未设置时回退 /tmp/nf-test-home
（存在则用，否则用临时空库）。
"""
from __future__ import annotations

import os
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
_home = os.environ.get("NARRATIVE_FORGE_HOME")
if not _home or not os.path.isdir(_home):
    cand = "/tmp/nf-test-home"
    _home = cand if os.path.isdir(cand) else tempfile.mkdtemp(prefix="nf-bench-")
os.environ["NARRATIVE_FORGE_HOME"] = _home

from PySide6 import QtWidgets  # noqa: E402
from src.core.models import LAYER_IDS, Module, Pipeline, PipelineLayer  # noqa: E402
from src.core.generator import generate_document  # noqa: E402
from src.ui.main_window import MainWindow  # noqa: E402


def main() -> int:
    # ---------- 验收 10：启动 <3s（实例化 MainWindow + show + 首帧事件循环） ----------
    t0 = time.perf_counter()
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
    win = MainWindow()
    win.show()
    app.processEvents()
    t_launch = time.perf_counter() - t0

    # ---------- 验收 11：生成 100 模块 <10s（内存构造，不落盘） ----------
    mods = []
    for i in range(100):
        lid = LAYER_IDS[i % len(LAYER_IDS)]
        mods.append(Module(
            id=f"M{i:03d}", name=f"性能模块{i:03d}", category="通用类",
            layer=lid,
            source_md=f"# 模块 通用类:M{i:03d}\n\n"
                      f"## 基本信息\n- 名称：性能模块{i:03d}\n- 挂载层：{lid}\n"
                      f"- 可替换：是\n- 输入依赖：\n- 输出键：k{i}\n\n"
                      f"## 核心逻辑\n- 输出规则 {i}\n"))
    pipe = Pipeline(
        id="PB", name="性能基准", structure_type="linear",
        layers=[PipelineLayer(id=l, name=f"层{l}") for l in LAYER_IDS])

    t1 = time.perf_counter()
    md, warns = generate_document(pipe, mods, None, "性能基准文档")
    t_gen = time.perf_counter() - t1

    ok_launch = t_launch < 3.0
    ok_gen = t_gen < 10.0
    print(f"数据目录        : {_home}")
    print(f"启动(实例化+首帧): {t_launch * 1000:8.0f} ms"
          f"  [{'PASS' if ok_launch else 'FAIL'}]  要求 < 3000 ms")
    print(f"生成100模块      : {t_gen * 1000:8.0f} ms"
          f"  [{'PASS' if ok_gen else 'FAIL'}]  要求 < 10000 ms"
          f"（输出 {len(md)} 字符，警告 {len(warns)} 条）")
    return 0 if (ok_launch and ok_gen) else 1


if __name__ == "__main__":
    sys.exit(main())