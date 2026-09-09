#!/usr/bin/env bash
# 45 · 本地 git hook 安装（多会话防呆）：pre-push 跑 nf release --fast，
# 基线自描述不一致即拒推（完整 verify 由 CI release-gate 在 tag 上强制）。
set -e
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
mkdir -p "$ROOT/.git/hooks"
cat > "$ROOT/.git/hooks/pre-push" <<'EOF'
#!/usr/bin/env bash
# 自动安装：scripts/install_hooks.sh
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT" || exit 1
echo "== pre-push：nf release --fast（基线自描述一致） =="
python scripts/nf.py release --fast || {
  echo "!! 基线自描述不一致——先修文档/verify 再推（完整门禁见 release-gate CI）" >&2
  exit 1
}
EOF
chmod +x "$ROOT/.git/hooks/pre-push"
echo "installed: $ROOT/.git/hooks/pre-push"
