#!/usr/bin/env bash
# 45 · 本地 git hook 安装（多会话防呆）：
#   pre-push  → 跑完整 nf release（verify + 基线 + 资产 ledger + 指令审计 + 载荷 + 覆盖率），任一红即拒推；
#   commit-msg→ 跑 commit_msg_check.py（CONTRIBUTING §1 提交信息格式），不合规即拒提交。
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

cat > "$ROOT/.git/hooks/commit-msg" <<'EOF'
#!/usr/bin/env bash
# 自动安装：scripts/install_hooks.sh
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT" || exit 1
# $1 = git 传进来的提交信息文件路径
python scripts/commit_msg_check.py "$1" || {
  echo "!! 提交信息不合规——按上面的修复指引改后再提交（确需绕过：git commit --no-verify）" >&2
  exit 1
}
EOF
chmod +x "$ROOT/.git/hooks/commit-msg"
echo "installed: $ROOT/.git/hooks/commit-msg"
