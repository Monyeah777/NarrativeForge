#!/usr/bin/env bash
# 42 M5.4 本地质量一键聚合：verify（协议/门禁）+ e2e（core 直驱端到端）。
# 端壳冒烟/基准（bench/smoke_gui 等）已随 L3 端壳线 2026-09-09 退役移除（见 L3_FROZEN.md）；本地聚合 = verify + e2e（headless core 直驱）。
set -e
cd "$(dirname "$0")/.."
echo "== 1/2 分层门禁 =="
bash verify.sh
echo "== 2/2 端到端（headless core 直驱）=="
PYTHONPATH=desktop/src python scripts/e2e_desktop_headless.py
echo "== 质量聚合入口完成：verify + e2e 全绿 =="
