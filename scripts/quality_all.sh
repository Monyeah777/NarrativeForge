#!/usr/bin/env bash
# 42 M5.4 本地质量一键聚合：verify（协议/门禁）+ e2e（core 直驱端到端）。
# bench（端壳）不在本地跑——L3 冻结移出清单（见 L3_FROZEN.md），壳波接回时随接线账恢复。
set -e
cd "$(dirname "$0")/.."
echo "== 1/2 分层门禁 =="
bash verify.sh
echo "== 2/2 端到端（headless core 直驱）=="
PYTHONPATH=desktop/src python scripts/e2e_desktop_headless.py
echo "== 质量聚合入口完成：verify + e2e 全绿 =="
