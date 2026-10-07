#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成 README / 站点用的终端演示 GIF（可复现：帧内容直接来自 TUI 渲染器）。

为什么要有这个脚本（而不是留一张手工 GIF 在仓库里）：
  2026-10-07 实测发现 site/assets/demo.gif 是**改名前的遗留产物**——标题栏写着
  「nf — NarrativeForge 终端 TUI」，而项目早已叫 NinFenz；而且仓库里**没有生成器**，
  谁也不知道那张图是怎么来的、下次改名要怎么重做。于是把生成过程入库：
  帧文本来自 tui/nf.py 的 demo_frame()，改名/改界面只需重跑本脚本。

字体：用 SimSun（simsun.ttc）——Windows 上 CJK 为等宽的少数常见字体，
  CJK 恰好是 ASCII 的 2 倍宽，因此图片里的框线严格对齐，**不依赖读者的等宽字体**。
  （这正是「终端演示在 GitHub 上看着没对齐」的根因：多数等宽字体的 CJK 回退字形
  宽度并不等于 2 个 ASCII 宽，文本帧的右边框就会右漂。）

用法：
  python site/tools/make-demo-gif.py            # 写到 site/assets/demo.gif
  python site/tools/make-demo-gif.py --out x.gif --font "C:/Windows/Fonts/simsun.ttc"
"""

import argparse
import importlib.util
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
SITE = HERE.parent
ROOT = SITE.parent
TUI_PY = ROOT / "tui" / "nf.py"

FONT_CANDIDATES = [
    r"C:\Windows\Fonts\simsun.ttc",   # CJK 等宽（首选）
    r"C:\Windows\Fonts\msyh.ttc",     # 回退（比例字体，仅保证可读）
    "/usr/share/fonts/opentype/noto/NotoSansMonoCJKsc-Regular.otf",
    "/System/Library/Fonts/Menlo.ttc",
]

BG = (13, 17, 23)
BAR = (22, 27, 34)
FG = (201, 209, 217)
DIM = (139, 148, 158)
ACCENT = (88, 166, 255)
OK = (63, 185, 80)
WARN = (210, 153, 34)

FONT_SIZE = 15
LINE_H = 20
PAD = 18
BAR_H = 30


def load_tui():
    spec = importlib.util.spec_from_file_location("nf_tui", str(TUI_PY))
    mod = importlib.util.module_from_spec(spec)
    sys.modules["nf_tui"] = mod
    spec.loader.exec_module(mod)
    return mod


def pick_font(explicit: str = "") -> str:
    if explicit:
        return explicit
    for c in FONT_CANDIDATES:
        if Path(c).is_file():
            return c
    raise SystemExit("找不到可用等宽字体，请用 --font 指定")


class Canvas:
    """按「显示列」定位的等宽画布：ASCII 一列，CJK 两列。"""

    def __init__(self, cols: int, rows: int, font_path: str):
        self.font = ImageFont.truetype(font_path, FONT_SIZE)
        self.adv = self.font.getlength("M")          # ASCII 单列宽
        self.w = int(cols * self.adv + PAD * 2)
        self.h = int(rows * LINE_H + PAD * 2 + BAR_H)
        self.img = Image.new("RGB", (self.w, self.h), BG)
        self.d = ImageDraw.Draw(self.img)
        self._titlebar()

    def _titlebar(self):
        self.d.rectangle([0, 0, self.w, BAR_H], fill=BAR)
        for i, c in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
            cx = 14 + i * 16
            self.d.ellipse([cx, BAR_H // 2 - 5, cx + 10, BAR_H // 2 + 5], fill=c)
        self.d.text((self.w / 2, BAR_H / 2), "nf — NinFenz 终端 TUI", font=self.font,
                    fill=DIM, anchor="mm")

    def line(self, row: int, text: str, fill=FG, col: int = 0):
        x = PAD + col * self.adv
        y = PAD + BAR_H + row * LINE_H
        self.d.text((x, y), text, font=self.font, fill=fill)

    def center(self, row: int, text: str, fill=FG):
        self.d.text((self.w / 2, PAD + BAR_H + row * LINE_H), text,
                    font=self.font, fill=fill, anchor="ma")


def card(lines, cols=96, rows=26, font_path=""):
    """卡片也画在**与场景帧同尺寸**的画布上并垂直居中——
    否则 Pillow 会按首帧尺寸对齐，把 26 行的 TUI 帧裁掉一半（本脚本首版就踩了）。"""
    c = Canvas(cols, rows, font_path)
    top = max(0, (rows - len(lines)) // 2)
    for row, (text, fill) in enumerate(lines):
        c.center(top + row, text, fill)
    return c.img


def frame_image(tui, font_path):
    lines = tui.demo_frame(96, 26)
    c = Canvas(96, 26, font_path)
    for row, ln in enumerate(lines):
        c.line(row, ln, ACCENT if row in (0, 2, 25) else FG)
    return c.img


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(SITE / "assets" / "demo.gif"))
    ap.add_argument("--font", default="")
    args = ap.parse_args()
    font_path = pick_font(args.font)
    tui = load_tui()

    title = card([
        ("NinFenz · 终端 TUI", ACCENT),
        ("", FG),
        ("nf — 内容契约层的全屏人机入口", FG),
        ("", FG),
        ("Tab 切面板 · ↑↓ 面板内移动 · / 过滤 · Enter 运行 · ? 帮助", DIM),
        ("只读安全面：无 shell 执行 · 路径包含性判据 · 写盘需确认", DIM),
    ], font_path=font_path)
    title2 = card([
        ("NinFenz · 终端 TUI", ACCENT),
        ("", FG),
        ("❯ nf doctor", OK),
        ("环境自检：Python 3.11 · 仓库在场 · 模块 13 · 管线 3", DIM),
        ("", FG),
        ("✔ 只读体检通过：无缺件 / 无越界 / 无非确定性输出", OK),
    ], font_path=font_path)
    scene = frame_image(tui, font_path)
    done = card([
        ("NinFenz · 终端 TUI", ACCENT),
        ("", FG),
        ("✔ 只读体检通过", OK),
        ("E2E DESKTOP HEADLESS PASSED", OK),
        ("verify v2.30 · check1-40 · PASS=72", FG),
        ("", FG),
        ("菜单与动作都是 nf CLI 真命令的受控调用方", DIM),
    ], font_path=font_path)

    frames = [title, title2, scene, done]
    durs = [1800, 1800, 3000, 2600]
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    frames[0].save(out, save_all=True, append_images=frames[1:], duration=durs,
                   loop=0, optimize=True, disposal=2)
    print("  字体: %s" % font_path)
    print("  尺寸: %s  帧数: %d  时长: %.1fs" % (frames[0].size, len(frames), sum(durs) / 1000.0))
    print("  写出: %s  %.1f KB" % (out, out.stat().st_size / 1024.0))


if __name__ == "__main__":
    main()
