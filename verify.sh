#!/usr/bin/env bash
# ============================================================
# NarrativeForge verify.sh —— 两段式验收门禁（07 §7 可执行化）
# 版本 : v2.0  配套 : 07_官方核心出厂与社区预设导航.md §7（两级结构终验 9 项）
# 用法 : 仓库根目录执行  bash verify.sh  （脚本自动定位根目录）
# 语义 : 任何 Agent/人对 01/02/03/04/05/06/07 层增删改后必须运行；
#        任一 FAIL = 协议事故 → 回滚该次修改再重新验收。
# 结构 : [段 A] 官方核心出厂（check1-6，无 community 亦须通过）
#        [段 B] 社区领域包（check7-10，两包在场时执行；缺包 WARN 跳过）
# 基准 : 判定逐字对齐 07 §7；04=核心 13 件 / 03=P00+P01+P90 / 05=README+用户自定义；
#        校园资产 29 文件 1575 行 / 西幻资产 23 文件 4285 行（v1.0 发布实测基线）。
# ============================================================
set -u
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT" || { echo '无法进入仓库根目录'; exit 2; }
PASS=0; FAIL=0; WARN=0
ok(){ PASS=$((PASS+1)); printf '  [PASS] %s\n' "$1"; }
no(){ FAIL=$((FAIL+1)); printf '  [FAIL] %s\n' "$1"; }
wn(){ WARN=$((WARN+1)); printf '  [WARN] %s\n' "$1"; }
check1(){
  echo '== [1/6·A] 官方核心目录结构（07 §7 项1）=='
  local err=0
  for f in 01_核心协议.md 02_联动注册表.md 06_Agent执行协议.md 07_官方核心出厂与社区预设导航.md README.md LICENSE; do
    [ -f "$f" ] || { no "根级缺失: $f"; err=1; }
  done
  # 03 管线库：官方 P00 骨架 + P01 标准 + P90 技术文档（P02/P03 已随社区包分发至 community/*/pipelines/）
  for p in P00_通用文档生成管线.md P01_标准管线.md P90_技术文档生成管线.md; do
    [ -f "03_管线库/$p" ] || { no "03 缺官方管线文件: $p"; err=1; }
  done
  # 04 模块库：官方核心 13 件逐文件存在（通用 6 / 事件 5 / 世界 1 / 技术 1，清单见 07 §1）
  local core13='04_模块库/世界类/M08_季节天气.md
04_模块库/事件类/M06_任务剧情.md
04_模块库/事件类/M12_NPC对话.md
04_模块库/事件类/M13_NPC交互.md
04_模块库/事件类/M20_世界知识库.md
04_模块库/事件类/M22_事件叙事.md
04_模块库/技术文档类/M90_技术文档结构.md
04_模块库/通用类/M00_数据结构.md
04_模块库/通用类/M10_时间推进.md
04_模块库/通用类/M23_认知边界.md
04_模块库/通用类/M24_组合规则.md
04_模块库/通用类/M50_主循环.md
04_模块库/通用类/M80_输出生成器.md'
  while IFS= read -r f; do
    [ -f "$f" ] || { no "04 缺核心模块: $f"; err=1; }
  done <<< "$core13"
  # 05 资产库：仅总 README + 用户自定义扩增槽（题材领域资产已整体迁出至 community）
  [ -f 05_资产库/README.md ] || { no '05_资产库缺总 README'; err=1; }
  [ -d 05_资产库/用户自定义 ] || { no '05 缺 用户自定义 扩增槽目录'; err=1; }
  if [ "$err" -eq 0 ]; then
    ok '根级 6 件；03 官方三管线（P00/P01/P90）；04 核心 13 件逐件在场；05=README+用户自定义'
  fi
}
check2(){
  echo '== [2/6·A] 重号 ID 全限定·官方层（07 §7 项5）=='
  local err=0
  # 04 层：核心两重号文件须存在；04 内 M10/M22 各仅 1 件（生存:M10/情感:M22 属社区包）
  [ -f 04_模块库/通用类/M10_时间推进.md ] || { no '缺 通用类/M10_时间推进.md'; err=1; }
  [ -f 04_模块库/事件类/M22_事件叙事.md ] || { no '缺 事件类/M22_事件叙事.md'; err=1; }
  local n10=$(find 04_模块库 -name 'M10_*.md' | wc -l); local n22=$(find 04_模块库 -name 'M22_*.md' | wc -l)
  [ "$n10" -eq 1 ] || { no "04 内 M10 文件应 1 件（仅通用:M10），实为 $n10"; err=1; }
  [ "$n22" -eq 1 ] || { no "04 内 M22 文件应 1 件（仅事件:M22），实为 $n22"; err=1; }
  # 02 注册表：核心两限定 ID 均须注册（§2 核心模块表）
  grep -q '通用:M10' 02_联动注册表.md || { no '注册表缺限定 ID: 通用:M10'; err=1; }
  grep -q '事件:M22' 02_联动注册表.md || { no '注册表缺限定 ID: 事件:M22'; err=1; }
  # 02/06/07：逐行扫描——含裸 M10/M22 的行须带类别词（通用/生存/情感/事件）；
  # 仅当 M10 与 M22 同现（重号元说明）或行含 ☐ 待办时豁免
  for f in 02_联动注册表.md 06_Agent执行协议.md 07_官方核心出厂与社区预设导航.md; do
    local bad=$(awk '
      { hasCat = ($0 ~ /通用|生存|情感|事件/)
        m10 = ($0 ~ /(^|[^0-9])M10([^0-9]|$)/)
        m22 = ($0 ~ /(^|[^0-9])M22([^0-9]|$)/)
        if ((m10 || m22) && !hasCat && !(m10 && m22) && $0 !~ /☐/) bad++ }
      END { print bad+0 }' "$f")
    [ "$bad" -eq 0 ] || { no "$f 含 ${bad} 处未类别限定的 M10/M22 引用"; err=1; }
  done
  if [ "$err" -eq 0 ]; then ok '04 核心两重号在场（M10/M22 各 1 件）；02 注册两限定 ID；02/06/07 全类别前缀限定'
  fi
}
check3(){
  echo '== [3/6·A] 五条不变式落点（01 §5 ↔ 07 §7 项6）=='
  local err=0
  for s in '三正交分离' '核心固定' '通信契约' '数据隔离' '真相唯一'; do
    grep -q "$s" 01_核心协议.md || { no "01 §5 缺不变式: $s"; err=1; }
  done
  for q in 'asset_get' 'asset_query' 'asset_match' 'asset_roll' 'asset_register'; do
    grep -q "$q" 01_核心协议.md || { no "I4 五接口缺: $q"; err=1; }
  done
  grep -q 'M50' 01_核心协议.md && grep -q 'M80' 01_核心协议.md || { no 'I2 核心固定缺 M50/M80 字样'; err=1; }
  if [ "$err" -eq 0 ]; then ok 'I1-I5 五条不变式 + I4 五接口 + I2 核心锚点全部落于 01 §5'
  fi
}
check4(){
  echo '== [4/6·A] 认知边界（06 §4 管线 ↔ M23 认知域）=='
  local err=0
  for k in '事实管线' '事实快照' '认知裁剪' '裁剪渲染' '锚点回验'; do
    grep -q "$k" 06_Agent执行协议.md || { no "06 §4 缺认知层名: $k"; err=1; }
  done
  for k in '视角裁剪' '可见域' '推断域' '隐藏域' 'fail' '白描'; do
    grep -q "$k" 04_模块库/通用类/M23_认知边界.md || { no "M23 缺认知域措辞: $k"; err=1; }
  done
  if [ "$err" -eq 0 ]; then ok '06 §4 认知五步与 M23 认知域措辞语义一致（快照/裁剪/隐藏域/fail/白描）'
  fi
}
check5(){
  echo '== [5/6·A] 质检门（M80 gate_action 流水线 ↔ 06 §5）=='
  local err=0
  for k in 'pass:' 'warn:' 'fail:' '白描' '隐藏域直述' 'gate_action' 'gate_decision_record'; do
    grep -q "$k" 04_模块库/通用类/M80_输出生成器.md || { no "M80 gate 缺: $k"; err=1; }
  done
  for k in 'pass' 'warn' 'fail' '隐藏域直述' '白描'; do
    grep -q "$k" 06_Agent执行协议.md || { no "06 §5 gate 缺呼应: $k"; err=1; }
  done
  if [ "$err" -eq 0 ]; then ok 'M80 gate_action 声明式流水线（pass/warn/fail + 白描降级 + 决策记录）与 06 §5 呼应一致'
  fi
}
check6(){
  echo '== [6/6·A] 入口导航（README → 07 → 协议链/官方目录）=='
  local err=0
  grep -q '07_官方核心出厂与社区预设导航' README.md || { no 'README 缺指向 07_官方核心出厂与社区预设导航'; err=1; }
  for k in '01_核心协议' '02_联动注册表' '03_管线库' '05_资产库' '06_Agent执行协议' 'community'; do
    grep -q "$k" 07_官方核心出厂与社区预设导航.md || { no "07 缺引用: $k"; err=1; }
  done
  for f in 07_官方核心出厂与社区预设导航.md 01_核心协议.md 02_联动注册表.md 06_Agent执行协议.md 05_资产库/README.md; do
    [ -f "$f" ] || { no "导航目标缺失: $f"; err=1; }
  done
  [ -d 03_管线库 ] || { no '导航目标缺失: 03_管线库 目录'; err=1; }
  if [ "$err" -eq 0 ]; then ok 'README→07→01/02/06/03/05 官方入口导航闭环可访问'
  fi
}
check7(){
  echo '== [7/4·B] 社区两包结构完整（07 §7 项2）=='
  local err=0
  if [ -d community/校园情感领域包 ]; then
    local cmod=$(find community/校园情感领域包/modules -name '*.md' 2>/dev/null | wc -l)
    local cass=$(find community/校园情感领域包/assets -name '*.md' ! -name 'README.md' 2>/dev/null | wc -l)
    [ "$cmod" -eq 9 ] || { no "校园包 modules 应 9 件，实为 $cmod"; err=1; }
    [ "$cass" -eq 29 ] || { no "校园包 assets 应 29 件，实为 $cass"; err=1; }
    [ -f community/校园情感领域包/README.md ] || { no '校园包缺顶层 README'; err=1; }
    [ -f community/校园情感领域包/pipelines/P02_校园情感流管线.md ] || { no '校园包缺 pipelines/P02_校园情感流管线.md'; err=1; }
  else
    wn '校园情感领域包不在场（跳过其结构校验）'
  fi
  if [ -d community/西幻生存领域包 ]; then
    local xmod=$(find community/西幻生存领域包/modules -name '*.md' 2>/dev/null | wc -l)
    local xass=$(find community/西幻生存领域包/assets -name '*.md' ! -name 'README.md' 2>/dev/null | wc -l)
    [ "$xmod" -eq 14 ] || { no "西幻包 modules 应 14 件，实为 $xmod"; err=1; }
    [ "$xass" -eq 23 ] || { no "西幻包 assets 应 23 件，实为 $xass"; err=1; }
    [ -f community/西幻生存领域包/README.md ] || { no '西幻包缺顶层 README'; err=1; }
    [ -f community/西幻生存领域包/pipelines/P03_西幻生存流管线.md ] || { no '西幻包缺 pipelines/P03_西幻生存流管线.md'; err=1; }
  else
    wn '西幻生存领域包不在场（跳过其结构校验）'
  fi
  if [ "$err" -eq 0 ]; then ok '校园 9 模块+29 资产+P02+README；西幻 14 模块+23 资产+P03+README 结构完整'
  fi
}
check8(){
  echo '== [8/4·B] 社区资产行数溯源（07 §7 项3）=='
  local err=0 c='' w=''
  if [ -d community/校园情感领域包 ]; then
    c=$(find community/校园情感领域包/assets -name '*.md' ! -name 'README.md' -exec wc -l {} + 2>/dev/null | awk '/total/{s+=$1} END{print s+0}')
    [ "$c" -eq 1575 ] || { no "校园资产累计行数 ${c}（应 1575）——与发布基线核对"; err=1; }
  else
    wn '校园情感领域包不在场（跳过行数溯源）'
  fi
  if [ -d community/西幻生存领域包 ]; then
    w=$(find community/西幻生存领域包/assets -name '*.md' ! -name 'README.md' -exec wc -l {} + 2>/dev/null | awk '/total/{s+=$1} END{print s+0}')
    [ "$w" -eq 4285 ] || { no "西幻资产累计行数 ${w}（应 4285）——与发布基线核对"; err=1; }
  else
    wn '西幻生存领域包不在场（跳过行数溯源）'
  fi
  if [ "$err" -eq 0 ]; then ok "行数溯源一致：校园 29 文件 ${c:-N/A} 行 / 西幻 23 文件 ${w:-N/A} 行（N/A=不在场跳过）"
  fi
}
check9(){
  echo '== [9/4·B] 模块-资产引用可寻址 + 社区 README 重号限定（07 §7 项4/5）=='
  local err=0
  # 可寻址代表键（键→community 两包 assets 文件，经 asset_get 五接口寻址）
  local pairs='ATTR_TEMPLATES:community/校园情感领域包/assets/ATTR_TEMPLATES.md
LOCATIONS:community/校园情感领域包/assets/LOCATIONS.md
EMOTION_WHEEL:community/校园情感领域包/assets/EMOTION_WHEEL.md
JOB:community/西幻生存领域包/assets/01_职业成长与基础属性_JOB.md
WORLD_KNOWLEDGE:community/西幻生存领域包/assets/20_世界知识_WORLD_KNOWLEDGE.md'
  while IFS=: read -r key file; do
    [ -n "$key" ] || continue
    if [ -f "$file" ]; then :; else
      no "引用键 $key 对应资产缺失（应经五接口可寻址）: $file"; err=1
    fi
  done <<< "$pairs"
  # 两包顶层 README：裸 M10/M22 行须类别前缀限定（与 check2 同规则）
  for rd in community/校园情感领域包/README.md community/西幻生存领域包/README.md; do
    [ -f "$rd" ] || continue
    local bad=$(awk '
      { hasCat = ($0 ~ /通用|生存|情感|事件/)
        m10 = ($0 ~ /(^|[^0-9])M10([^0-9]|$)/)
        m22 = ($0 ~ /(^|[^0-9])M22([^0-9]|$)/)
        if ((m10 || m22) && !hasCat && !(m10 && m22) && $0 !~ /☐/) bad++ }
      END { print bad+0 }' "$rd")
    [ "$bad" -eq 0 ] || { no "$rd 含 ${bad} 处未类别限定的 M10/M22 引用"; err=1; }
  done
  if [ "$err" -eq 0 ]; then ok '代表键 ATTR_TEMPLATES/LOCATIONS/EMOTION_WHEEL/JOB/WORLD_KNOWLEDGE 在两包 assets 可寻址；两包 README 的 M10/M22 全类别前缀限定'
  fi
}
check10(){
  echo '== [10/4·B] EXT 闭合 + 社区红线落地（07 §7 项2/8）=='
  local err=0
  # 西幻 EXT 溯源闭合（asset 21/22 前身：01_JOB 与 20_WORLD_KNOWLEDGE）
  local f1='community/西幻生存领域包/assets/01_职业成长与基础属性_JOB.md'
  local f2='community/西幻生存领域包/assets/20_世界知识_WORLD_KNOWLEDGE.md'
  [ -f "$f1" ] || { no "缺西幻 01: $f1"; err=1; }
  [ -f "$f2" ] || { no "缺西幻 20: $f2"; err=1; }
  if [ -f "$f1" ]; then
    grep -q '36820' "$f1" || { no '西幻01 缺 EXT 起始行 36820'; err=1; }
    grep -q '37280' "$f1" || { no '西幻01 缺 EXT 终止行 37280'; err=1; }
    grep -q '外部完整实体源' "$f1" || { no '西幻01 缺 EXT 溯源注释'; err=1; }
  fi
  if [ -f "$f2" ]; then
    grep -q '28894' "$f2" || { no '西幻20 缺 EXT 起始行 28894'; err=1; }
    grep -q '29064' "$f2" || { no '西幻20 缺 EXT 终止行 29064'; err=1; }
    grep -q '外部完整实体源' "$f2" || { no '西幻20 缺 EXT 溯源注释'; err=1; }
    grep -q '已填充' "$f2" || { no '西幻20 缺 状态已填充 标记'; err=1; }
  fi
  # v0.7.12 冲动-社会关系隔离（校园 M22 §7 ↔ 校园 README ↔ 06 §9 红线 7）
  local m22='community/校园情感领域包/modules/M22_三冲动驱动.md'
  local crd='community/校园情感领域包/README.md'
  [ -f "$m22" ] || { no "缺校园 M22: $m22"; err=1; }
  [ -f "$crd" ] || { no "缺校园包 README: $crd"; err=1; }
  for k in '冲动驱动边界' '物理位移' '动作连带' '视线停留' 'relationship_change'; do
    grep -q "$k" "$m22" || { no "M22 §7 缺冲动隔离措辞: $k"; err=1; }
  done
  grep -q 'v0.7.12' "$m22" || { no 'M22 §7 缺 v0.7.12 版本锚点'; err=1; }
  grep -q 'v0.7.12' "$crd" || { no '校园 README 缺 v0.7.12 版本锚点'; err=1; }
  grep -q '冲动-社会关系隔离' "$crd" || { no '校园 README 缺 冲动-社会关系隔离 表述'; err=1; }
  grep -q 'v0.7.12' 06_Agent执行协议.md || { no '06 §9 缺 v0.7.12 红线锚点'; err=1; }
  grep -q '关系推进权归 M40/M41' 06_Agent执行协议.md || { no '06 §9 缺 关系推进权归 M40/M41 表述'; err=1; }
  if [ "$err" -eq 0 ]; then ok '西幻01/20 EXT 闭合+溯源注释+已填充；冲动-社会关系隔离三落点一致（M22 §7/校园 README/06 §9 红线7）'
  fi
}
# ================= 主执行体（两段式） =================
echo '=================================================='
echo ' NarrativeForge 两段式验收门禁  v2.0（对齐 07 §7）'
echo '=================================================='
echo '—— 段 A：官方核心出厂（无 community 亦须通过）——'
check1; check2; check3; check4; check5; check6
echo '—— 段 B：社区领域包（两包在场执行，缺包 WARN 跳过）——'
if [ -d community/校园情感领域包 ] && [ -d community/西幻生存领域包 ]; then
  check7; check8; check9; check10
elif [ -d community ]; then
  wn 'community 仅部分领域包在场：社区段（check7-10）跳过——单包/半包部署仅验收官方段'
else
  wn 'community 不在场：社区段（check7-10）跳过——无包部署仅验收官方段'
fi
echo '=================================================='
echo "结果统计: PASS=$PASS  WARN=$WARN  FAIL=$FAIL"
if [ "$FAIL" -gt 0 ]; then
  echo '>>> 存在 FAIL = 协议事故：请回滚本次修改，修正后重新运行验收 <<<'
  exit 1
else
  echo '>>> 全部通过（WARN 仅提示非致命），变更可提交 <<<'
  exit 0
fi
