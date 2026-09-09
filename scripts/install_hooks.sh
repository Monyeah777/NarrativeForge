#!/usr/bin/env bash
# 45 · 本地 git hook 安装（多会话防呆）：pre-push 跑完整 nf release
#（verify + 基线 + 资产 ledger + 指令审计 + 载荷 + 逐模块覆盖率），任一红即拒推。
set -e
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
mkdir -p "$ROOT/.git/hooks"
cat > "$ROOT/.git/hooks/pre-push" <<'EOF'
#!/usr/bin/env bash
# 自动安装：scripts/install_hooks.sh
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT" || exit 1
echo "== pre-push：nf release（完整发布前体检） =="
python scripts/nf.py release || {
  echo "!! 发布前体检未过——先修再推" >&2
  exit 1
}
EOF
chmod +x "$ROOT/.git/hooks/pre-push"
echo "installed: $ROOT/.git/hooks/pre-push"
