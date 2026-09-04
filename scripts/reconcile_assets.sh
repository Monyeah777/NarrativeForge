#!/usr/bin/env bash
# ============================================================
# NarrativeForge reconcile_assets.sh —— 资产-模块三方对账（08 方案 T5 A5）
# 版本 : v1.0  配套 : 08_社区扩展规划与验收方案.md T5 动作2（C7 chore: A5）
# 用法 : 仓库根目录执行  bash scripts/reconcile_assets.sh [--quiet]
#   --quiet : 仅输出告警明细与汇总（供 verify.sh check11 静默调用，以退出码判结果）
# 对账 : 02 §8.1 在册清单 ↔ community/*/modules/ 实存 ↔ assets/README 消费列引用
# 告警 : 三类
#   [幽灵编号]   assets/README 引用的 M 编号既无对应文件、亦不在源编号残留豁免清单
#   [孤儿模块]   modules/ 实存但 02 §8.1 未登记（应 0：所有模块必须登记在册）
#   [未登记模块] 02 §8.1 在册但 modules/ 无对应文件（应 0：登记须有模块实体）
# 豁免 : ① 官方核心文件编号（04_模块库 实存，运行时动态收集）
#        ② 本包 modules/ 实存编号（运行时动态收集）
#        ③ 源编号残留静态清单（与两份 assets/README「源编号残留」注释同步维护，
#           注释修改处必须同步本清单，否则误报幽灵）
# 退出码 : 0=对账全清（可提交） / 1=存在告警（协议事故，回滚后重验）
# ============================================================
set -u
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT" || { echo '无法进入仓库根目录'; exit 2; }

QUIET=0
[ "${1:-}" = '--quiet' ] && QUIET=1
say(){ [ "$QUIET" -eq 0 ] && echo "$1"; }
G=0; O=0; U=0   # 幽灵 / 孤儿 / 未登记 计数

# ---------- ① 官方核心编号（04_模块库 实存，动态收集；find 到 13 件：M00/M06/M08/M10/M12/M13/M20/M22/M23/M24/M50/M80/M90，无 M21） ----------
CORE=$(find 04_模块库 -type f -name 'M[0-9]*.md' -exec basename {} \; \
  | sed -E 's/^M([0-9]+)_.*/\1/' | sort -u | tr '\n' ' ')
say "== ① 官方核心文件（04_模块库 实存）：$(echo $CORE | wc -w) 件 =="

# ---------- ③ 源编号残留静态豁免（须与 assets/README「源编号残留」注释同步维护） ----------
#   校园 A 表注释：M07 / M10（未限定前缀）/ M21 / M26 / M34 / M42 / M60 / M62 等（源文 8620 行旧模块体系编号残留）
REMNANT_XY='07 10 21 26 34 42 60 62'
#   西幻 §1 表 21 号文件"M21（通用）"：官方核心无 M21 文件（骨架通用数据接口职能由 M00 数据结构 + asset_* 五接口承载）
REMNANT_XH='21'
#   显示用（补回 M 前缀，与 scripts/ 内比对用的纯数字存储解耦）：07→M07
rem_xy_s=$(printf 'M%s ' $REMNANT_XY); rem_xh_s=$(printf 'M%s ' $REMNANT_XH)
say "== ③ 源编号残留豁免：校园 [${rem_xy_s% }] / 西幻 [${rem_xh_s% }] =="

# ---------- 02 §8.1 在册登记行（校园 §8.1 模块（9）/ 西幻 §8.2 模块（14）） ----------
REG_XY=$(grep -E '^- 模块（9）：' 02_联动注册表.md | head -1)
REG_XH=$(grep -E '^- 模块（14）：' 02_联动注册表.md | head -1)

# 从登记行提取编号集（纯数字输出；限定前缀 情感:M22 / 生存:M10 一并剥离取编号）
#   grep -oE 'M[0-9]+' 提取 M+数字串 → awk 仅保留数字部分恰好 2 位者（模块编号规范 M00-M99；
#   M001/M899 等 3 位伪编号与孤立 M 字母自动排除），输出与 modules/ 实存编号（sed 剥离 M）同构
ids_of(){ echo "$1" | grep -oE 'M[0-9]+' | awk '{n=substr($0,2); if (length(n)==2) print n}' | sort -u | tr '\n' ' '; }

reconcile_pkg(){
  # $1=登记行  $2=包目录  $3=包显示名  $4=该包源编号残留豁免串
  local reg_line="$1" pkg="$2" name="$3" rem="$4"
  local reg_ids mod_ids refs m
  reg_ids=$(ids_of "$reg_line")
  # modules/ 实存编号（文件名 M<编号>_*.md）
  mod_ids=$(find "$pkg/modules" -type f -name 'M[0-9]*.md' -exec basename {} \; \
    | sed -E 's/^M([0-9]+)_.*/\1/' | sort -u | tr '\n' ' ')
  # --- 孤儿模块：modules/ 实存但 02 §8.1 未登记 ---
  for m in $mod_ids; do
    if ! echo " $reg_ids " | grep -q " $m "; then
      O=$((O+1)); echo "  [孤儿模块] $name modules/M$m 实存但 02 §8.1 未登记"
    fi
  done
  # --- 未登记模块：02 §8.1 在册但 modules/ 无对应文件 ---
  for m in $reg_ids; do
    if ! echo " $mod_ids " | grep -q " $m "; then
      U=$((U+1)); echo "  [未登记模块] 02 §8.1 在册 $name M$m 但 modules/ 无对应文件"
    fi
  done
  # --- 幽灵编号：assets/README 引用无文件且未豁免（官方核心 ∪ 本包 modules ∪ 源编号残留） ---
  #   与 ids_of 同构提取（纯数字 2 位）：全文扫描但自动剔除 3 位伪编号（M001/M899 区段号等）与孤立 M
  refs=$(grep -oE 'M[0-9]+' "$pkg/assets/README.md" | awk '{n=substr($0,2); if (length(n)==2) print n}' | sort -u | tr '\n' ' ')
  for r in $refs; do
    local ex=''
    echo " $CORE " | grep -q " $r " && ex=1
    echo " $mod_ids " | grep -q " $r " && ex=1
    echo " $rem " | grep -q " $r " && ex=1
    [ -n "$ex" ] && continue
    G=$((G+1)); echo "  [幽灵编号] $name assets/README.md 引用 M$r：无对应文件（非官方核心 / 非本包 modules / 非源编号残留豁免）"
  done
  say "== $name：在册 $(echo $reg_ids | wc -w) / 实存 $(echo $mod_ids | wc -w) / README 引用 $(echo $refs | wc -w) 编号扫描 =="
}

say '=================================================='
say ' NarrativeForge 资产-模块三方对账  v1.0（T5 A5）'
say '=================================================='
reconcile_pkg "$REG_XY" 'community/校园情感领域包' '校园' "$REMNANT_XY"
reconcile_pkg "$REG_XH" 'community/西幻生存领域包' '西幻' "$REMNANT_XH"
say '--------------------------------------------------'
echo "对账汇总: 幽灵编号=$G  孤儿模块=$O  未登记模块=$U"
if [ "$((G+O+U))" -gt 0 ]; then
  echo '>>> 存在告警 = 资产-模块对账不一致：请核对 02 §8.1 / modules/ 实存 / assets/README 引用与豁免清单 <<<'
  exit 1
else
  echo '>>> 对账全清：零幽灵（源编号残留已豁免）/ 零孤儿 / 零未登记，变更可提交 <<<'
  exit 0
fi
