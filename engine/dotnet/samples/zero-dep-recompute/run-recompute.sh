#!/usr/bin/env bash
# NF 零依赖复算样例 · 外部侧复算器（Linux / POSIX）
#
# ⚠ 状态 = UNKNOWN：本机没有 Linux 运行环境（WSL 无发行版、无 docker/podman），**本脚本从未执行过**。
#    它与 run-recompute.ps1 同参数、同判定（PASS=0 / 语料漂移=3 / FAIL=1），但**未跑就不标 PASS**。
#    首次在 Linux 上执行者：请把实测结论回填到本样例的 README §5 边界表。
set -u
KIT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLI="${NF_SAMPLE_CLI:-$KIT/dist/nf-dotnet-linux-x64-f111-2026-09-28/nf-dotnet}"
ROOT="${NF_SAMPLE_ROOT:-$(dirname "$KIT")/nf-snap-h8}"
SCENARIO="${1:-small}"
OUT="$KIT/out"

[ -x "$CLI" ] || { echo "找不到可执行引擎产物：$CLI" >&2; exit 1; }
[ -d "$ROOT" ] || { echo "找不到语料根：$ROOT" >&2; exit 1; }
mkdir -p "$OUT"

fp="$("$CLI" --root "$ROOT" corpus --json | tr -d '\r')"
fingerprint="$(printf '%s' "$fp" | sed -n 's/.*"fingerprint"[[:space:]]*:[[:space:]]*"\([0-9a-f]*\)".*/\1/p')"
pinned="$(sed -n 's/.*"corpus_fingerprint"[[:space:]]*:[[:space:]]*"\([0-9a-f]*\)".*/\1/p' "$KIT/scenario.json" | head -1)"
echo "语料实测 = $fingerprint（钉定 $pinned）"

"$CLI" --root "$ROOT" combine verify --json > "$OUT/verify_all.json" || true
idx="${NF_SAMPLE_CERT_INDEX:-1}"
if [ "$SCENARIO" = "limit" ]; then idx=16; fi
packs="$(python3 - "$ROOT/protocol/combo_certificates.json" "$idx" <<'PY'
import json,sys
d=json.load(open(sys.argv[1],encoding='utf-8'))
print(','.join(d['certificates'][int(sys.argv[2])]['packs']))
PY
)"
expected="$(python3 - "$ROOT/protocol/combo_certificates.json" "$idx" <<'PY'
import json,sys
d=json.load(open(sys.argv[1],encoding='utf-8'))
print(d['certificates'][int(sys.argv[2])]['digest'])
PY
)"
"$CLI" --root "$ROOT" combine plan --packs "$packs" --json > "$OUT/certificate_${idx}.json"
actual="$(sed -n 's/.*"digest"[[:space:]]*:[[:space:]]*"\([0-9a-f]*\)".*/\1/p' "$OUT/certificate_${idx}.json" | head -1)"
echo "cert#$idx · 期望 $expected · 实得 $actual"

if [ "$expected" = "$actual" ]; then
  if [ "$fingerprint" = "$pinned" ]; then echo "== 判定：PASS =="; exit 0; fi
  echo "== 判定：CORPUS_DRIFT（语料非钉定版本，期望摘要不可比）=="; exit 3
fi
echo "== 判定：FAIL（复算与期望不符）=="; exit 1
