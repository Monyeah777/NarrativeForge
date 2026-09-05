#!/usr/bin/env bash
# ============================================================
# NarrativeForge verify.sh —— 两段式验收门禁（07 §7 可执行化）
# 版本 : v2.9  配套 : 07_官方核心出厂与社区预设导航.md §7（两级结构终验）+ 08_社区扩展规划与验收方案.md T5 A5（资产三方对账）+ 09_v0.6.0_协议中转站方案（check12 代码层门禁 + check13 协议版本一致性/迁移完整性）+ 10_v0.7.0_自定义协议方案（check14 社区协议登记门禁）+ 11_v0.8.0_自定义模块组合方案（check15 组合引用门禁）+ 12_v1.0.0_自定义模块组合方案（check16 契约仲裁门禁）+ 16_v1.4.0_质量治理闭环方案（check17 质量治理门）+ 17_v2.0.0_导出层CCV3方案（check18 导出契约门）
# 用法 : 仓库根目录执行  bash verify.sh  （脚本自动定位根目录）
# 语义 : 任何 Agent/人对 01/02/03/04/05/06/07 层增删改后必须运行；
#        任一 FAIL = 协议事故 → 回滚该次修改再重新验收。
# 结构 : [段 A] 官方核心出厂（check1-6，无 community 亦须通过）
#        [段 B] 社区领域包（check7-11，两包在场时执行；缺包 WARN 跳过）
#        [段 C] 代码层门禁（check12-check18，无条件执行：分层治理 23 方案——本段默认锁 L0-L2；
#        段 A/B = L0/L1（协议一致性 + 内容对账），check12-18 = L2 core（unittest/py_compile/协议投影/
#        组合/契约/质量/导出门）；android 相关 check 已随 L3 端壳冻结移出（见 L3_FROZEN.md）。check12 = desktop unittest 全量 + 全量 py_compile；check13 = 协议版本一致性（两处）+ 迁移完整性；check14 = 社区协议登记门禁：01 §6.1 Schema 必填 12 字段 + 02 §8.3 登记三要件 + registry protocols[] 投影一致；check15 = 组合引用门禁：02 §8.4 references 五断言（在册可寻址/依赖闭包闭合/挂载层冲突/schema 兼容/双源一致）；check16 = 契约仲裁门禁：01 §1.1 machine_contract 机读结构 + 02 §8.4 规则④ references 装配 publish⊆subscribe + 运行时寻址授权一致；check17 = 质量治理门；check18 = 导出契约门）
# 基准 : 判定逐字对齐 07 §7；04=核心 13 件 / 03=P00+P01+P90 / 05=README+用户自定义；
#        校园资产 29 文件 1575 行 / 西幻资产 23 文件 4285 行（v1.0 发布实测基线）。
# ============================================================
set -u
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT" || { echo '无法进入仓库根目录'; exit 2; }
# ---- Python 解释器探测（Windows 兼容）----
# Windows 的 python3 可能是应用商店 stub：command -v 能找到但执行静默失败零输出。
# 以「能真正执行 import sys」为可用判据：stub 被跳过，回退真实 python。
PY3=''
if command -v python3 >/dev/null 2>&1 && python3 -c 'import sys' >/dev/null 2>&1; then
  PY3='python3'
elif command -v python >/dev/null 2>&1 && python -c 'import sys' >/dev/null 2>&1; then
  PY3='python'
fi
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
  echo '== [7/4·B] 社区两包结构完整（07 §7 项2，T6 在册数一致性）=='
  local err=0 regxy='' regxh=''
  # T6：在册数一致性——02 §8.1/§8.2 登记行反解在册模块数，与 modules/ 实存件数比对（防注册表与文件失同步）
  if [ -f 02_联动注册表.md ]; then
    regxy=$(sed -n '/^### 8\.1/,/^### 8\.2/p' 02_联动注册表.md | grep -oE '模块（[0-9]+）' | grep -oE '[0-9]+')
    regxh=$(sed -n '/^### 8\.2/,/^### 8\.3/p' 02_联动注册表.md | grep -oE '模块（[0-9]+）' | grep -oE '[0-9]+')
  fi
  if [ -d community/校园情感领域包 ]; then
    local cmod=$(find community/校园情感领域包/modules -name '*.md' 2>/dev/null | wc -l)
    local cass=$(find community/校园情感领域包/assets -name '*.md' ! -name 'README.md' 2>/dev/null | wc -l)
    [ -n "$regxy" ] || { no '02 §8.1 未取到校园包在册模块数（登记行缺失）'; err=1; }
    [ "$cmod" -eq "$regxy" ] || { no "校园包 modules 实存 $cmod 件，02 §8.1 在册 $regxy 件——不一致"; err=1; }
    [ "$cass" -eq 29 ] || { no "校园包 assets 应 29 件，实为 $cass"; err=1; }
    [ -f community/校园情感领域包/README.md ] || { no '校园包缺顶层 README'; err=1; }
    [ -f community/校园情感领域包/pipelines/P02_校园情感流管线.md ] || { no '校园包缺 pipelines/P02_校园情感流管线.md'; err=1; }
  else
    wn '校园情感领域包不在场（跳过其结构校验）'
  fi
  if [ -d community/西幻生存领域包 ]; then
    local xmod=$(find community/西幻生存领域包/modules -name '*.md' 2>/dev/null | wc -l)
    local xass=$(find community/西幻生存领域包/assets -name '*.md' ! -name 'README.md' 2>/dev/null | wc -l)
    [ -n "$regxh" ] || { no '02 §8.2 未取到西幻包在册模块数（登记行缺失）'; err=1; }
    [ "$xmod" -eq "$regxh" ] || { no "西幻包 modules 实存 $xmod 件，02 §8.2 在册 $regxh 件——不一致"; err=1; }
    [ "$xass" -eq 23 ] || { no "西幻包 assets 应 23 件，实为 $xass"; err=1; }
    [ -f community/西幻生存领域包/README.md ] || { no '西幻包缺顶层 README'; err=1; }
    [ -f community/西幻生存领域包/pipelines/P03_西幻生存流管线.md ] || { no '西幻包缺 pipelines/P03_西幻生存流管线.md'; err=1; }
  else
    wn '西幻生存领域包不在场（跳过其结构校验）'
  fi
  if [ "$err" -eq 0 ]; then ok "校园 ${cmod:-9} 模块+29 资产+P02+README（与 02 §8.1 在册 ${regxy:-9} 一致）；西幻 ${xmod:-14} 模块+23 资产+P03+README（与 02 §8.2 在册 ${regxh:-14} 一致）结构完整"
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
check11(){
  echo '== [11/5·B] 资产-模块三方对账（08 方案 T5 A5；02 §8.1 ↔ modules/ ↔ assets/README）=='
  local err=0
  if [ -f scripts/reconcile_assets.sh ]; then
    if bash scripts/reconcile_assets.sh --quiet; then :; else
      no 'reconcile_assets.sh 报告资产对账告警（幽灵编号/孤儿模块/未登记模块任一非零）——核对 02 §8.1 在册、modules/ 实存、assets/README 引用与豁免清单'; err=1
    fi
  else
    wn 'scripts/reconcile_assets.sh 不在场（跳过资产对账；08 方案 T5 A5 要求缺脚本 WARN）'
  fi
  if [ "$err" -eq 0 ]; then ok '资产三方对账全清：幽灵编号=0（源编号残留已豁免）/ 孤儿模块=0 / 未登记模块=0'
  fi
}
check12(){
  echo '== [12/代码层] 桌面核心单元测试 + 全量 py_compile 语法抽查（v0.6.0 治理补漏）=='
  local err=0
  # ① desktop core 单元测试（desktop/tests 全量 discover，纯 unittest 无 pytest 依赖；L2 核心层）
  if [ -d desktop/tests ]; then
    if ( cd desktop && "$PY3" -m unittest discover -s tests -q >/tmp/nf_check12_unittest.log 2>&1 ); then
      ok 'desktop core 单元测试全绿（desktop/tests 全量 discover，纯 unittest 内置）'
    else
      no 'desktop core 单元测试失败——见 /tmp/nf_check12_unittest.log'; err=1
    fi
  else
    wn 'desktop/tests 不在场（跳过代码层 unittest）'
  fi
  # ② 全量 py_compile 语法抽查（desktop/src scripts——L2 core 域；android/app
  #    已随 L3 端壳冻结移出，不再编译，见 23 方案 / L3_FROZEN.md）
  if [ -n "$PY3" ]; then
    if "$PY3" -m compileall -q desktop/src scripts >/tmp/nf_check12_pyc.log 2>&1; then
      ok '全量 py_compile 语法抽查通过（desktop/src scripts）'
    else
      no 'py_compile 语法抽查失败——见 /tmp/nf_check12_pyc.log'; err=1
    fi
  else
    wn 'python3 不在 PATH（跳过 py_compile）'
  fi
  if [ "$err" -eq 0 ]; then ok '代码层门禁全绿：unittest 全量 + py_compile（L2 核心层）'
  fi
}
check13(){
  echo '== [13/段C] 协议版本一致性 + 迁移完整性（09 方案 T2.3）=='
  local err=0
  # ① 版本一致性：02 头部 registry_schema_version == desktop registry.json 版本
  #    （两处同源。android/app/core 为 L3 端壳 sync 生成物，已随分层治理冻结
  #    移出主仓库演进主线——不再参与比对，见 23 方案 / L3_FROZEN.md）
  local v02 vdesk
  v02=$(grep -o 'registry_schema_version: *"[^"]*"' 02_联动注册表.md | head -1 | sed 's/.*"\([^"]*\)"/\1/')
  vdesk=$("$PY3" -c "import json;print(json.load(open('desktop/src/core/registry.json', encoding='utf-8'))['registry_schema_version'])" 2>/dev/null)
  if [ -n "$v02" ] && [ -n "$vdesk" ]; then
    if [ "$v02" = "$vdesk" ]; then
      ok "协议版本两处一致：02 头部 = desktop registry.json = \"$v02\""
    else
      no "协议版本不一致：02=\"$v02\" desktop=\"$vdesk\"（须两处同步 bump）"; err=1
    fi
  else
    no "版本字段缺失：02=\"${v02:-空}\" desktop=\"${vdesk:-空}\""; err=1
  fi
  # ② 迁移完整性：bump 实体必有迁移记录（02 §9.3 四步在场）
  local seg miss='' k
  seg=$(awk '/^### 9\.3 迁移记录/{f=1} f' 02_联动注册表.md)
  if [ -n "$seg" ]; then
    for k in '现状快照' 'bump 声明' '迁移说明' '校验回读'; do
      echo "$seg" | grep -q "$k" || miss="$miss $k"
    done
    if [ -z "$miss" ]; then
      ok '迁移记录在场：02 §9.3 四步齐备（现状快照/bump 声明/迁移说明/校验回读）'
    else
      no "02 §9.3 迁移记录缺步：$miss（bump 实体必有迁移记录，按 01 §7 迁移实操四步补全）"; err=1
    fi
  else
    no '02 缺 §9.3 迁移记录节（版本 bump 实体必有迁移记录）'; err=1
  fi
  # ③ 模块逐条一致：02 §2 模块表 13 件 == registry.json modules（条目数与 ID 集合全等）
  if [ -n "$PY3" ]; then
    if "$PY3" - <<'PYEOF' >/tmp/nf_check13_cmp.log 2>&1
import json, re, sys
doc = open('02_联动注册表.md', encoding='utf-8').read()
m = re.search(r'## 2\. 官方核心模块表.*?(?=\n## 3\.)', doc, re.S)
rows = []
if m:
    for line in m.group(0).splitlines():
        cells = [c.strip() for c in line.strip().strip('|').split('|')]
        if len(cells) == 5 and cells[0] not in ('模块ID', '---') and cells[0]:
            rows.append(cells)
doc_ids = [r[0] for r in rows]
reg_ids = [x['id'] for x in json.load(open('desktop/src/core/registry.json', encoding='utf-8'))['modules']]
errs = []
if len(doc_ids) != 13: errs.append('02 §2 模块表行数=%d（预期 13）' % len(doc_ids))
if len(reg_ids) != 13: errs.append('registry.json modules 数=%d（预期 13）' % len(reg_ids))
only_doc = sorted(set(doc_ids) - set(reg_ids)); only_reg = sorted(set(reg_ids) - set(doc_ids))
if only_doc: errs.append('02 有而 registry.json 缺：' + ','.join(only_doc))
if only_reg: errs.append('registry.json 有而 02 缺：' + ','.join(only_reg))
sys.exit(1 if errs else 0)
PYEOF
    then
      ok '模块逐条一致：02 §2 模块表 13 件 == registry.json modules（ID 集合全等）'
    else
      no "模块表与机读投影不一致——$(head -3 /tmp/nf_check13_cmp.log | tr '\n' ' ')"; err=1
    fi
  else
    wn 'python3 不在 PATH（跳过 check13 模块逐条比对）'
  fi
  if [ "$err" -eq 0 ]; then ok '协议版本一致性 + 迁移完整性全绿（check13：两处版本一致 + §9.3 四步在场 + 13 件模块全等）'
  fi
}
check14(){
  echo '== [14/段C] 社区协议登记门禁（v0.7.0 check14：01 §6.1 Schema + 02 §8.3 登记三要件 + registry protocols[] 投影）=='
  local err=0
  # 依赖探测：python3 + PyYAML（yaml 解析用；缺失时该子项 WARN 降级文本粗校验，不 FAIL——动作 3）
  local PYOK=0 YAMLOK=0
  [ -n "$PY3" ] && PYOK=1
  { [ "$PYOK" -eq 1 ] && "$PY3" -c 'import yaml' >/dev/null 2>&1; } && YAMLOK=1
  [ "$YAMLOK" -eq 1 ] || wn 'Python/PyYAML 不可用（check14 ② yaml 解析降级文本粗校验；建议 pip install pyyaml 后重跑精确校验）'
  # ① protocol.yaml 在场（登记三要件①；community/* 自动扫描——新增包目录须自带协议声明，含组合/通用包）
  local d miss=0
  for d in community/*/; do
    d=${d%/}
    [ -f "$d/protocol.yaml" ] || { no "①缺协议声明: $d/protocol.yaml（登记三要件①不满足；community/* 下每个目录须为带 protocol.yaml 的登记包）"; miss=1; }
  done
  if [ "$miss" -eq 1 ]; then
    no 'protocol.yaml 缺失——check14 ②-⑦ 跳过（登记三要件不全，包不被平台门禁识别）'
    return
  fi
  # ②-⑦ 精确比对（python3 + PyYAML：解析两包 protocol.yaml + desktop registry.json + 02 文档反解）
  if [ "$YAMLOK" -eq 1 ]; then
    if "$PY3" - <<'PYEOF' >/tmp/nf_check14.log 2>&1
import glob, json, os, re, sys
import yaml

# C2 包目录 glob 化（29 方案 B3-C）：遍历层（②④⑥⑦ + ① 目录在场）自动发现 community/* 全部
# 含 protocol.yaml 的目录——新增组合/通用包登记零改 verify.sh（目录 + protocol.yaml + registry 条目即可）。
# DOMAIN = 领域包显式登记（③ 独占类别互斥 + ⑤ 编号在册/M91-99 不占用专属）——领域包语义依赖
# 02 §8.1/8.2 段落结构（segmap）与「不占 M91-99 社区段」规则（通用 M93-96/轻混 M91-92 合法占段，
# 不能内容推导纳入领域检查）；新增领域包须在此登记 + 02 §8 开新段 + registry 条目（登记三要件②）。
DOMAIN = ['community/校园情感领域包', 'community/西幻生存领域包']
ALL_PKGS = sorted(d.replace('\\', '/') for d in glob.glob('community/*')
                  if os.path.isdir(d) and os.path.isfile(os.path.join(d, 'protocol.yaml')))
REQUIRED = [
    'protocol.schema_version', 'package.id', 'package.name', 'package.pipeline',
    'package.module_id_range', 'package.categories', 'package.dependencies.core_only',
    'package.dependencies.core_modules', 'package.dependencies.cross_package',
    'package.modules', 'package.assets', 'package.mount_layers',
]
OFFICIAL13 = ['M00', '通用:M10', 'M08', 'M23', 'M24', 'M50', 'M80',
              '事件:M22', 'M06', 'M12', 'M13', 'M20', 'M90']
errs = []
data = {}
# --- 解析领域包+组合包 protocol.yaml + ②必填 12 字段 ---
for d in ALL_PKGS:
    try:
        data[d] = yaml.safe_load(open(d + '/protocol.yaml', encoding='utf-8'))
    except Exception as e:
        errs.append('%s yaml 解析失败: %s' % (d, e))
        continue
    pkg = data[d].get('package', {})
    for k in REQUIRED:
        node, parts = data[d], k.split('.')
        for p in parts:
            if isinstance(node, dict) and p in node:
                node = node[p]
            else:
                errs.append('%s 缺必填字段: %s' % (d, k)); break
    mr, ms = pkg.get('module_id_range'), pkg.get('modules')
    if isinstance(mr, list) and isinstance(ms, list) and len(mr) != len(ms):
        errs.append('%s module_id_range(%d) != modules(%d)' % (d, len(mr), len(ms)))
if not errs:
    # ③ R2 类别包间不冲突（全部登记包独占类别两两互斥——32 方案 C-b 扩域：
    #    从 DOMAIN 两领域包扩为 ALL_PKGS 全两两；新题材域包（techdoc 技术文档）
    #    自带模块落 M91-99 社区段不进 DOMAIN，类别仍须与其他社区包无交集）
    cats = {d: set(data[d]['package'].get('categories') or []) for d in ALL_PKGS}
    pkgs = list(ALL_PKGS)
    for i in range(len(pkgs)):
        for j in range(i + 1, len(pkgs)):
            inter = cats[pkgs[i]] & cats[pkgs[j]]
            if inter:
                errs.append('③R2 类别冲突（登记包不得共占独占类别）: %s∩%s=%s' % (pkgs[i], pkgs[j], ','.join(sorted(inter))))
    # ④ R1 core_modules ⊆ 官方核心 13 件 + cross_package 空（含组合包）
    for d in ALL_PKGS:
        dep = data[d]['package']['dependencies']
        bad = [x for x in dep.get('core_modules', []) if x not in OFFICIAL13]
        if bad: errs.append('%s ④R1 core_modules 越界官方核心 13 件: %s' % (d, ','.join(bad)))
        if dep.get('core_only') is not True: errs.append('%s ④R1 core_only 应为 true' % d)
        if dep.get('cross_package'): errs.append('%s ④R1 cross_package 应为空数组' % d)
    # ⑤ 编号在册一致（module_id_range ↔ 02 §8 反解）+ M91-M99 不占用（领域包专属：通用/组合包合法占 M91-99 社区段）
    doc = open('02_联动注册表.md', encoding='utf-8').read()
    # segmap：领域包目录 → 02 §8.x 段（按段标题含包名定位；新增领域包自动匹配，勿硬编码 §8.1/§8.2 下标）
    segmap = {}
    for d in DOMAIN:
        segname = d.split('/')[-1]
        segpat = re.compile(r'^### 8\.\d+ %s\b.*?(?=^### 8\.|^## 9\.)' % re.escape(segname), re.S | re.M)
        segm = segpat.search(doc)
        segmap[d] = segm.group(0) if segm else ''
    for d in DOMAIN:
        ids = [str(x) for x in data[d]['package']['module_id_range']]
        m99 = [i for i in ids if re.match(r'^M9[1-9]$', i)]
        if m99: errs.append('%s ⑤M91-M99 段被占用: %s（新包新增编号才落 M91-M99，既有包沿用原编号）' % (d, ','.join(m99)))
        mm = re.search(r'模块（(\d+)）', segmap[d])
        regn = int(mm.group(1)) if mm else -1
        if regn < 0:
            errs.append('%s ⑤02 §8 在册模块数未取到' % d)
        elif len(ids) != regn:
            errs.append('%s ⑤module_id_range(%d) != 02 §8 在册(%d)' % (d, len(ids), regn))
    # ⑥ protocol.yaml ↔ README 关键字段一致（双源一致，check14 ⑥，含组合包）
    for d in ALL_PKGS:
        rd = open(d + '/README.md', encoding='utf-8').read()
        pkg = data[d]['package']
        if pkg['name'] not in rd: errs.append('%s ⑥README 缺包名: %s' % (d, pkg['name']))
        if pkg['pipeline'] not in rd: errs.append('%s ⑥README 缺管线: %s' % (d, pkg['pipeline']))
        ac = pkg['assets']['count']
        if str(ac) not in rd: errs.append('%s ⑥README 缺资产数 %d 字样' % (d, ac))
    # ⑦ registry protocols[] ↔ protocol.yaml / 02 §8 一致（check14 ⑦）
    reg = json.load(open('desktop/src/core/registry.json', encoding='utf-8'))
    prots = {p['id']: p for p in reg.get('protocols', [])}
    if len(prots) != len(ALL_PKGS):
        errs.append('⑦registry protocols[] 条目数=%d（预期 %d：两领域包+组合包+通用包）' % (len(prots), len(ALL_PKGS)))
    for d in ALL_PKGS:
        pkg = data[d]['package']
        pid = pkg['id']
        p = prots.get(pid)
        if not p:
            errs.append('⑦registry protocols[] 缺条目: %s' % pid); continue
        if p['pipeline'] != pkg['pipeline']: errs.append('⑦%s pipeline 不一致' % pid)
        if sorted(p['categories']) != sorted(pkg['categories']): errs.append('⑦%s categories 不一致' % pid)
        if p['schema_version'] != data[d]['protocol']['schema_version']: errs.append('⑦%s schema_version 不一致' % pid)
        # ⑦ 升级（29 方案 B3-C）：module_ids / mount_layers 从长度比对 → 元素级全序
        reg_ids = [str(x) for x in p.get('module_ids', [])]
        proto_ids = [str(x) for x in pkg.get('module_id_range', [])]
        if reg_ids != proto_ids:
            errs.append('⑦%s module_ids 与 module_id_range 不一致（元素级）: reg=%s proto=%s' % (pid, reg_ids, proto_ids))
        if p['assets']['count'] != pkg['assets']['count']: errs.append('⑦%s assets.count 不一致' % pid)
        # mount_layers 键归一：protocol 长键（P40 行为决策）→ Pxx 短键（registry 形态）
        def _layer_key(k):
            return str(k).split()[0] if str(k).split() else str(k)
        reg_ml = {_layer_key(k): v for k, v in (p.get('mount_layers') or {}).items()}
        proto_ml = {_layer_key(k): v for k, v in (pkg.get('mount_layers') or {}).items()}
        if set(reg_ml) != set(proto_ml):
            errs.append('⑦%s mount_layers 层集不一致: reg=%s proto=%s' % (pid, sorted(reg_ml), sorted(proto_ml)))
        else:
            for lid in sorted(reg_ml):
                for field in ('default', 'available'):
                    rv = reg_ml[lid].get(field) if isinstance(reg_ml[lid], dict) else []
                    pv = proto_ml[lid].get(field) if isinstance(proto_ml[lid], dict) else []
                    if (rv or []) != (pv or []):
                        errs.append('⑦%s 层 %s %s 不一致: reg=%s proto=%s' % (pid, lid, field, rv, pv))
        if d in segmap:
            mm = re.search(r'模块（(\d+)）', segmap[d])
            regn = int(mm.group(1)) if mm else -1
            if regn >= 0 and len(p['module_ids']) != regn:
                errs.append('⑦%s module_ids(%d) != 02 §8 在册(%d)' % (pid, len(p['module_ids']), regn))
sys.exit(1 if errs else 0)
PYEOF
    then
      :
    else
      no "check14 ②-⑦ 校验失败——$(head -5 /tmp/nf_check14.log | tr '\n' ' ')"; err=1
    fi
  else
    # 降级：PyYAML 缺失 → 文本粗校验必填键在场（②），③-⑦ WARN 跳过不 FAIL（动作 3）
    local dd k miss2=0
    for dd in community/*/; do
      dd=${dd%/}
      for k in 'schema_version' 'package:' 'id:' 'name:' 'pipeline:' 'module_id_range' 'categories:' 'core_only' 'core_modules' 'cross_package' 'modules:' 'assets:' 'mount_layers'; do
        grep -q "$k" "$dd/protocol.yaml" || { no "②(降级) $dd/protocol.yaml 缺键: $k"; miss2=1; }
      done
    done
    [ "$miss2" -eq 0 ] || err=1
    [ "$miss2" -eq 0 ] && wn 'check14 ②-⑦ 精确比对跳过（PyYAML 缺失，仅必填键文本粗校验；建议安装 pyyaml 后重跑）'
  fi
  if [ "$err" -eq 0 ]; then ok '社区协议登记门禁全绿（check14 七项：①protocol.yaml 在场 ②Schema 必填 12 字段 ③R2 类别不冲突 ④R1 依赖边界 ⑤编号在册一致+M91-M99 不占用 ⑥双源一致 ⑦protocols[] 投影一致）'
  fi
}
check15(){
  echo '== [15/段C] 组合引用门禁（v0.8.0 check15：02 §8.4 references 五断言）=='
  local err=0 PYOK=0 YAMLOK=0
  [ -n "$PY3" ] && PYOK=1
  { [ "$PYOK" -eq 1 ] && "$PY3" -c 'import yaml' >/dev/null 2>&1; } && YAMLOK=1
  [ "$YAMLOK" -eq 1 ] || wn 'Python/PyYAML 不可用（check15 组合引用精确比对降级为 references 键文本粗校验；建议 pip install pyyaml 后重跑）'
  if [ "$YAMLOK" -eq 1 ]; then
    if "$PY3" - <<'PYEOF' >/tmp/nf_check15.log 2>&1
import glob, json, os, sys
import yaml
# C2 包目录 glob 化（29 方案 B3-C）：check15 遍历层扫全部含 protocol.yaml 的 community 目录
# （references 空包自动跳过，组合门禁语义不变）；新增包登记零改 verify.sh
PKGS = sorted(d.replace('\\', '/') for d in glob.glob('community/*')
              if os.path.isdir(d) and os.path.isfile(os.path.join(d, 'protocol.yaml')))
OFFICIAL13 = ['M00', '通用:M10', 'M08', 'M23', 'M24', 'M50', 'M80',
              '事件:M22', 'M06', 'M12', 'M13', 'M20', 'M90']
errs = []
data = {}
# --- 解析两包 protocol.yaml ---
for d in PKGS:
    try:
        data[d] = yaml.safe_load(open(d + '/protocol.yaml', encoding='utf-8'))
    except Exception as e:
        errs.append('%s yaml 解析失败: %s' % (d, e))
        continue
    pkg = data[d].get('package', {})
    # ④ schema_version 兼容：v1/v2 均可读；references 缺省等价 []
    sv = data[d].get('protocol', {}).get('schema_version', '')
    if sv not in ('1', '2'):
        errs.append('④%s protocol.schema_version=%r（预期 v1 或 v2）' % (d, sv))
    refs = pkg.get('references')
    if refs is None:
        refs = []   # v1 文件无 references 字段 → 缺省等价 []
    if not isinstance(refs, list):
        errs.append('%s references 应为列表' % d)
        refs = []
    for r in refs:
        if not isinstance(r, dict):
            errs.append('%s references 条目非对象: %r' % (d, r)); continue
        for k in ('source_package', 'module_id', 'source_schema_version', 'asset_readonly'):
            if k not in r:
                errs.append('%s references 条目缺字段 %s: %r' % (d, k, r))
    data[d]['_refs'] = refs

reg = json.load(open('desktop/src/core/registry.json', encoding='utf-8'))
prots = {p['id']: p for p in reg.get('protocols', [])}
dir_by_id = {}
for d in PKGS:
    if d in data and 'package' in data[d]:
        dir_by_id[data[d]['package'].get('id')] = d

# ⑤ 双源一致：protocol.yaml references ↔ registry protocols[] references 逐条比对
def norm(rl):
    return sorted([{k: r.get(k) for k in ('source_package', 'module_id', 'source_schema_version', 'asset_readonly') if k in r}
                   for r in (rl or [])], key=lambda x: json.dumps(x, ensure_ascii=False))
for d in PKGS:
    if d not in data:
        continue
    pkg = data[d].get('package', {})
    pid = pkg.get('id')
    p = prots.get(pid)
    if not p:
        errs.append('⑤registry protocols[] 缺条目: %s' % pid); continue
    if norm(data[d]['_refs']) != norm(p.get('references')):
        errs.append('⑤%s protocol.yaml references ↔ registry protocols[] references 不一致（%r vs %r）' % (pid, data[d]['_refs'], p.get('references')))

# ①-③ 组合登记断言（references 非空时逐条执行；两包 references 空 → 天然 PASS）
for d in PKGS:
    if d not in data:
        continue
    refs = data[d]['_refs']
    pid = data[d]['package'].get('id')
    if not refs:
        continue
    # ① 在册可寻址：source_package 可解析（registry protocols[]）+ module_id 在源包 module_ids 在列
    for r in refs:
        sp, mid = r.get('source_package'), r.get('module_id')
        if sp not in prots:
            errs.append('①%s references.source_package 不在册（registry protocols[] 不可解析）: %s' % (pid, sp)); continue
        src_ids = [str(x) for x in prots[sp].get('module_ids', [])]
        mid_bare = mid.split(':', 1)[-1] if isinstance(mid, str) and ':' in mid else mid
        if mid not in src_ids and mid_bare not in src_ids:
            errs.append('①%s references.module_id 不在源包 %s modules[] 在列: %s' % (pid, sp, mid))
    # ② 依赖闭包：以 references 起点沿源包 dependencies.core_modules 递归展开，无环/无悬空，叶 ⊆ OFFICIAL13
    stack = []
    for r in refs:
        sp = r.get('source_package')
        if sp in dir_by_id:
            stack.append((sp, data[dir_by_id[sp]]['package'].get('dependencies', {}).get('core_modules', [])))
        else:
            errs.append('②%s 依赖闭包源包不可读（缺 community 目录 protocol.yaml）: %s' % (pid, sp))
    seen = set()
    while stack:
        sp, cms = stack.pop()
        if sp in seen:
            errs.append('②%s 依赖闭包成环: %s' % (pid, sp)); continue
        seen.add(sp)
        pkg2 = data[dir_by_id[sp]]['package']
        deps = pkg2.get('dependencies', {})
        for x in cms:
            if x not in OFFICIAL13:
                errs.append('②%s 依赖闭包叶节点越界官方核心 13 件: %s（源包 %s core_modules）' % (pid, x, sp))
        # 源包嵌套 references（package 层——references 与 dependencies 平级，见
        # protocol.yaml 结构；原取 deps.get('references') 恒空 = 死检查，31 方案瑶光发现修复）
        if pkg2.get('references'):
            errs.append('②%s 依赖闭包检测到源包 %s 嵌套 references（当前不支持多层组合，须闭合官方核心）' % (pid, sp))
    # ③ 挂载层冲突：组合包各层 default 与源包同层 default 取交集非空即冲突
    ml = data[d]['package'].get('mount_layers', {})
    if isinstance(ml, dict):
        for layer_key, spec in ml.items():
            if not isinstance(spec, dict):
                continue
            key = layer_key.split()[0] if isinstance(layer_key, str) else layer_key
            for r in refs:
                sp = r.get('source_package')
                sp_dir = dir_by_id.get(sp)
                if not sp_dir:
                    continue
                sp_ml = data[sp_dir]['package'].get('mount_layers', {})
                sp_spec = None
                if isinstance(sp_ml, dict):
                    for lk, ls in sp_ml.items():
                        lk0 = lk.split()[0] if isinstance(lk, str) else lk
                        if lk0 == key or lk == key:
                            sp_spec = ls; break
                if isinstance(sp_spec, dict):
                    inter = set(spec.get('default', []) or []) & set(sp_spec.get('default', []) or [])
                    if inter:
                        errs.append('③%s 挂载层 %s default 与源包 %s 冲突（交集: %s）' % (pid, key, sp, ','.join(sorted(inter))))
sys.exit(1 if errs else 0)
PYEOF
    then
      :
    else
      no "check15 ①-⑤ 校验失败——$(head -5 /tmp/nf_check15.log | tr '\n' ' ')"; err=1
    fi
  else
    # 降级：PyYAML 缺失 → references 键文本粗校验（①-⑤ 精确比对跳过不 FAIL）
    local d miss3=0
    for d in community/*/; do
      d=${d%/}
      grep -q 'references:' "$d/protocol.yaml" || { no "check15 降级 $d/protocol.yaml 缺 references: 键（v2 必含，可为 []）"; miss3=1; }
    done
    [ "$miss3" -eq 0 ] || err=1
    [ "$miss3" -eq 0 ] && wn 'check15 ①-⑤ 精确比对跳过（PyYAML 缺失，仅 references 键文本粗校验；建议安装 pyyaml 后重跑）'
  fi
  if [ "$err" -eq 0 ]; then ok '组合引用门禁全绿（check15 五断言：①references 在册可寻址 ②依赖闭包闭合官方核心 ③挂载层 default 无冲突 ④schema_version v1/v2 兼容 ⑤双源一致）'
  fi
}
check16(){
  echo '== [16/段C] 契约仲裁门禁（v1.0.0 check16：01 §1.1 machine_contract 机读结构 + 02 §8.4 规则④ references 装配自动仲裁 + 运行时寻址授权一致）=='
  local errA=0 errB=0 PYOK=0 YAMLOK=0
  [ -n "$PY3" ] && PYOK=1
  { [ "$PYOK" -eq 1 ] && "$PY3" -c 'import yaml' >/dev/null 2>&1; } && YAMLOK=1
  [ "$YAMLOK" -eq 1 ] || wn 'python3/PyYAML 不在（check16-A 契约仲裁降级 machine_contract 键文本粗校验；建议 pip install pyyaml 后重跑）'
  # ---- 子断言 A：契约仲裁（官方核心 13 件机读结构 + references 装配 publish⊆subscribe）----
  if [ "$YAMLOK" -eq 1 ]; then
    if "$PY3" - <<'PYEOF' >/tmp/nf_check16a.log 2>&1
import json, sys, os, glob
import yaml
CORE13 = [
 '04_模块库/通用类/M00_数据结构.md','04_模块库/通用类/M10_时间推进.md',
 '04_模块库/通用类/M23_认知边界.md','04_模块库/通用类/M24_组合规则.md',
 '04_模块库/通用类/M50_主循环.md','04_模块库/通用类/M80_输出生成器.md',
 '04_模块库/事件类/M06_任务剧情.md','04_模块库/事件类/M12_NPC对话.md',
 '04_模块库/事件类/M13_NPC交互.md','04_模块库/事件类/M20_世界知识库.md',
 '04_模块库/事件类/M22_事件叙事.md','04_模块库/世界类/M08_季节天气.md',
 '04_模块库/技术文档类/M90_技术文档结构.md']
def extract_mc(path):
    txt = open(path, encoding='utf-8').read()
    for part in txt.split('```'):
        if 'machine_contract:' not in part:
            continue
        body = part.split('\n', 1)[1] if '\n' in part else part
        body = body.lstrip()
        if 'machine_contract:' not in body:
            continue
        parsed = yaml.safe_load(body)
        if isinstance(parsed, dict) and 'machine_contract' in parsed:
            return parsed['machine_contract']
        return parsed
    return None
errs = []
incomplete = []
scanned = 0
# ① 官方核心 13 件 machine_contract 结构性机读解析（FAIL 级强校验；01 §1.1 schema/id/events/interfaces 形状）
for f in CORE13:
    try:
        mc = extract_mc(f)
    except Exception as e:
        errs.append('①官方核心机读块解析异常: %s (%s)' % (f, e))
        continue
    if not isinstance(mc, dict):
        errs.append('①官方核心机读块缺失/非对象: %s' % f)
        continue
    ev = mc.get('events')
    if mc.get('schema') != '1':
        errs.append('①%s machine_contract.schema=%r（预期 "1"，01 §1.1）' % (f, mc.get('schema')))
    if not isinstance(mc.get('id'), str) or not mc.get('id'):
        errs.append('①%s machine_contract.id 缺失/非字符串: %r' % (f, mc.get('id')))
    if not isinstance(ev, dict) or not isinstance(ev.get('publish'), list) or not isinstance(ev.get('subscribe'), list):
        errs.append('①%s machine_contract.events 形状违约（publish/subscribe 须均为列表）: keys=%s' % (f, sorted(mc.keys())))
    if 'interfaces' in mc and not isinstance(mc.get('interfaces'), list):
        errs.append('①%s machine_contract.interfaces 非列表: %r' % (f, mc.get('interfaces')))
# ② 社区模块分级（13 方案 §6 开放问题 1 过渡策略）：机读完备 → 同结构强校验；未完备存量 → WARN+统计不阻断（community/*/ 自动发现，含组合包）
for pkg in sorted(glob.glob('community/*/')):
    pkg = pkg.rstrip('/')
    mod_dir = os.path.join(pkg, 'modules')
    if not os.path.isdir(mod_dir):
        continue
    for f in sorted(glob.glob(os.path.join(mod_dir, '*.md'))):
        scanned += 1
        try:
            mc = extract_mc(f)
        except Exception as e:
            errs.append('②社区模块机读块解析异常: %s (%s)' % (f, e))
            continue
        if mc is None:
            incomplete.append(os.path.basename(f)[:-3])
            continue
        ev = mc.get('events')
        if mc.get('schema') != '1' or not isinstance(ev, dict) or not isinstance(ev.get('publish'), list) or not isinstance(ev.get('subscribe'), list):
            errs.append('②社区模块机读块结构违约: %s (schema=%r events keys=%s)' % (f, mc.get('schema'), sorted(ev.keys()) if isinstance(ev, dict) else ev))
# ③ references 装配契约仲裁（02 §8.4 规则④：相邻装配「源包发布面 ⊆ 邻居订阅面」，publish ⊄ subscribe 即 FAIL）
reg = json.load(open('desktop/src/core/registry.json', encoding='utf-8'))
prots = {p['id']: p for p in reg.get('protocols', [])}
pkg_dir = {}
for pkg in sorted(glob.glob('community/*/')):
    pkg = pkg.rstrip('/')
    try:
        data = yaml.safe_load(open(pkg + '/protocol.yaml', encoding='utf-8'))
        pid = (data.get('package') or {}).get('id')
        if pid:
            pkg_dir[pid] = pkg
    except Exception as e:
        errs.append('③%s protocol.yaml 解析失败: %s' % (pkg, e))
def find_module_file(pkg, mid):
    bare = mid.split(':', 1)[-1] if isinstance(mid, str) and ':' in mid else mid
    mod_dir = os.path.join(pkg, 'modules')
    if not os.path.isdir(mod_dir):
        return None
    for f in sorted(glob.glob(os.path.join(mod_dir, '*.md'))):
        b = os.path.basename(f)
        if b.startswith(bare + '_') or b == bare + '.md':
            return f
    return None
assembly = 0
for pid, p in prots.items():
    refs = p.get('references') or []
    if not refs:
        continue
    cur_dir = pkg_dir.get(pid)
    if not cur_dir:
        continue
    nsub = set()
    for f in sorted(glob.glob(os.path.join(cur_dir, 'modules', '*.md'))):
        mc = extract_mc(f)
        if isinstance(mc, dict):
            nsub |= set((mc.get('events') or {}).get('subscribe') or [])
    for r in refs:
        assembly += 1
        sp, mid = r.get('source_package'), r.get('module_id')
        sp_dir = pkg_dir.get(sp)
        if sp not in prots or not sp_dir:
            errs.append('③%s references.source_package 不在册/不可读: %s' % (pid, sp))
            continue
        sf = find_module_file(sp_dir, mid)
        if not sf:
            errs.append('③%s 源模块文件缺失，契约仲裁无法执行: %s' % (pid, mid))
            continue
        smc = extract_mc(sf)
        if not isinstance(smc, dict):
            errs.append('③%s 源模块机读块缺失，契约仲裁无法执行: %s（%s）' % (pid, mid, sf))
            continue
        pub = set((smc.get('events') or {}).get('publish') or [])
        miss = pub - nsub
        if miss:
            errs.append('③契约断裂 FAIL：%s 引用 %s 发布面 ⊄ 邻居订阅面——越界/缺失事件=%s（判据 02 §8.4 规则④ + 01 §1 events publish⊆subscribe）' % (pid, mid, sorted(miss)))
print('契约仲裁汇总：①官方核心 13 件机读结构解析 %d 件；②社区模块扫描 %d 件（机读完备 %d / 未完备 %d）；③references 装配仲裁样本 %d 条' % (len(CORE13), scanned, scanned - len(incomplete), len(incomplete), assembly))
if incomplete:
    print(' [WARN] 社区模块机读契约未完备 %d 件（过渡期 WARN+统计不阻断，随 C6 组合战例 retro-fit）：%s' % (len(incomplete), '、'.join(incomplete)))
for e in errs:
    print(' [FAIL] ' + e)
sys.exit(1 if errs else 0)
PYEOF
    then
      :
    else
      no "check16-A 契约仲裁校验失败——$(head -5 /tmp/nf_check16a.log | tr '\n' ' ')"; errA=1
    fi
  else
    local f miss4=0
    for f in 04_模块库/通用类/M00_数据结构.md 04_模块库/通用类/M10_时间推进.md 04_模块库/通用类/M23_认知边界.md 04_模块库/通用类/M24_组合规则.md 04_模块库/通用类/M50_主循环.md 04_模块库/通用类/M80_输出生成器.md 04_模块库/事件类/M06_任务剧情.md 04_模块库/事件类/M12_NPC对话.md 04_模块库/事件类/M13_NPC交互.md 04_模块库/事件类/M20_世界知识库.md 04_模块库/事件类/M22_事件叙事.md 04_模块库/世界类/M08_季节天气.md 04_模块库/技术文档类/M90_技术文档结构.md; do
      grep -q 'machine_contract:' "$f" || { no "check16-A 降级 $f 缺 machine_contract: 键（01 §1.1 机读块必含）"; miss4=1; }
    done
    [ "$miss4" -eq 0 ] || errA=1
    [ "$miss4" -eq 0 ] && wn 'check16-A 契约仲裁精确比对跳过（PyYAML 缺失，仅 machine_contract 键文本粗校验；建议安装 pyyaml 后重跑）'
  fi
  if [ "$errA" -eq 0 ]; then ok '契约仲裁全绿（check16-A：官方核心 13 件 machine_contract 机读结构解析 + references 装配 publish⊆subscribe 无违约）'
  fi
  # ---- 子断言 B：运行时寻址授权一致（registry references.asset_readonly ↔ _readonly_sources ↔ asset_get；loader 纯 json 消费，无 PyYAML 依赖）----
  if [ "$PYOK" -eq 1 ]; then
    if "$PY3" - <<'PYEOF' >/tmp/nf_check16b.log 2>&1
import json, sys, os, glob
sys.path.insert(0, 'desktop/src')
from core.registry_loader import load_registry
errs = []
reg = json.load(open('desktop/src/core/registry.json', encoding='utf-8'))
prots = {p['id']: p for p in reg.get('protocols', [])}
# ① 声明侧：registry protocols[].references[] 中 asset_readonly:true 的 source_package 集合
declared = set()
for p in prots.values():
    for r in (p.get('references') or []):
        if r.get('asset_readonly') is True and r.get('source_package'):
            declared.add(r['source_package'])
# ② 投影侧：loader._readonly_sources（C3 运行时投影，__post_init__ 白名单）
r = load_registry()
projected = set(r._readonly_sources)
if declared != projected:
    errs.append('②声明/投影不一致：registry references.asset_readonly 集合=%s vs loader._readonly_sources=%s' % (sorted(declared), sorted(projected)))
# ③ 行为侧：白名单内源包 asset_get 真实资产 key 可寻址；白名单外全 None
for sp in sorted(prots):
    if sp in declared:
        files = sorted(glob.glob(os.path.join('community', sp, 'assets', '*.md')))
        if not files:
            errs.append('③%s 白名单内但源包 assets 无 .md，无法验证可寻址行为' % sp)
            continue
        key = os.path.basename(files[0])[:-3]
        got = r.asset_get(sp, key)
        if got is None:
            errs.append('③%s 白名单内 asset_get(%r) 返回 None（应可寻址返回资产文本）' % (sp, key))
    else:
        got = r.asset_get(sp, 'README')
        if got is not None:
            errs.append('③%s 白名单外 asset_get 返回非 None（越权寻址未拦截）' % sp)
for e in errs:
    print(' [FAIL] ' + e)
print('运行时寻址授权汇总：声明侧=%s 投影侧=%s 行为侧=%s' % (sorted(declared), sorted(projected), '白名单内可寻址/外全拒' if not errs else '存在违约'))
sys.exit(1 if errs else 0)
PYEOF
    then
      :
    else
      no "check16-B 运行时寻址授权断言失败——$(head -5 /tmp/nf_check16b.log | tr '\n' ' ')"; errB=1
    fi
  else
    no 'check16-B 运行时寻址授权断言无法执行（Python 解释器不可用）'; errB=1
  fi
  if [ "$errB" -eq 0 ]; then ok '运行时寻址授权一致（check16-B：registry references.asset_readonly ↔ _readonly_sources ↔ asset_get 三方一致，空白名单全拒）'
  fi
}
check17(){
  echo '== [17/段C] 质量治理门禁（v1.4.0 check17：16_v1.4.0_质量治理闭环方案.md）=='
  local err=0
  if [ -d desktop/tests ]; then
    if ( cd desktop && "$PY3" -m unittest tests.test_quality_gate -q >/tmp/nf_check17_unittest.log 2>&1 ); then
      ok '质量治理门 unittest 全绿（test_quality_gate：空装配/缺锚点 fail、资产悬空/层外 warn、合法装配 ok；ok()=fail==0 可信任度不变量）'
    else
      no "质量治理门 unittest 失败——见 /tmp/nf_check17_unittest.log"; err=1
    fi
  else
    wn 'desktop/tests 不在场（跳过 check17）'
  fi
}
check18(){
  echo '== [18/段C] 导出契约门禁（v2.0.0 check18：17_v2.0.0_导出层CCV3方案.md）=='
  local err=0
  if [ -d desktop/tests ]; then
    if ( cd desktop && "$PY3" -m unittest tests.test_ccv3_adapter tests.test_exporter -q >/tmp/nf_check18_unittest.log 2>&1 ); then
      ok '导出契约 unittest 全绿（ccv3_adapter：映射层引擎锚点排除/资产条目/无静默丢弃；exporter：chara spec 锚点/world 条目/PNG tEXt 回读）'
    else
      no "导出契约 unittest 失败——见 /tmp/nf_check18_unittest.log"; err=1
    fi
  else
    wn 'desktop/tests 不在场（跳过 check18）'
  fi
}
check19(){
  echo '== [19/段C] 导出产物 schema 合规（v2.2.0 A1：export_schema 5 格式 shape 自检）=='
  local err=0
  if [ -d desktop/tests ]; then
    if ( cd desktop && "$PY3" -m unittest tests.test_export_schema -q >/tmp/nf_check19_unittest.log 2>&1 ); then
      ok '导出产物 schema 校验全绿（ccv3/skill/agents/claude/mcp 5 格式 shape 自检：合法产物通过 + 篡改检出）'
    else
      no "导出产物 schema 校验失败——见 /tmp/nf_check19_unittest.log"; err=1
    fi
  else
    wn 'desktop/tests 不在场（跳过 check19）'
  fi
  if [ "$err" -eq 0 ]; then ok '导出产物 schema 合规门禁全绿（check19：A1 外部吸收——产物 shape 不漂移）'
  fi
}
check20(){
  echo '== [20/段C] 文档完整性门禁（v2.2.0 A3：模块文档必填项——对齐 check16 过渡策略分层）=='
  local err=0 PYOK=0
  [ -n "$PY3" ] && PYOK=1
  if [ "$PYOK" -eq 1 ]; then
    if "$PY3" - <<'PYEOF' >/tmp/nf_check20.log 2>&1
import glob, os, re, sys

# A3 文档完整性（v2.2.0 外部吸收）：模块文档硬性必填项，缺即 fail。
# 分层判据（对齐 check16 过渡策略——13 方案 §6 开放问题 1）：
#   - 官方核心 13 件（04_模块库）：机读完备（machine_contract 必含）+ 元数据行必填；
#   - 社区模块（community/*/modules）：机读完备者同结构强校验；未完备存量
#     WARN+统计不阻断（存量 retro-fit 随社区演进，不破既有 PASS）。
REQ_META = ('类别', '来源', '挂载点', '依赖')
errs = []
incomplete = []   # 社区未完备模块（WARN 统计）
scanned = 0

def check_file(path, strict):
    """strict=True 机读完备须含 machine_contract + 元数据；否则仅元数据行提示。"""
    global scanned
    scanned += 1
    txt = open(path, encoding='utf-8').read()
    issues = []
    has_mc = 'machine_contract' in txt
    if strict and not has_mc:
        issues.append('%s 缺 machine_contract（01 §1.1 机读契约，官方模块必含）' % os.path.basename(path))
    head = txt.split('\n', 1)[0] if txt else ''
    if not re.match(r'^# (模块|M\d+|情感:|生存:|事件:|通用:)[^#]*', head):
        issues.append('%s 标题格式异常（应 # 模块 Mxx · 名称）' % os.path.basename(path))
    # 元数据行：标题下多行 > 引用（类别/来源/挂载点/依赖可分布多行）；取前 6 行合查
    meta_block = '\n'.join(txt.split('\n')[:6])
    for k in REQ_META:
        if k not in meta_block:
            issues.append('%s 元数据缺 %s（标题下应含 > 类别/来源/挂载点/依赖 行）' % (os.path.basename(path), k))
    if ('## 职责' not in txt and '## 核心逻辑' not in txt
            and '## 1. 职责' not in txt and '## 1 职责' not in txt
            and '## 2 输入输出' not in txt):
        issues.append('%s 缺 职责/核心逻辑 章节' % os.path.basename(path))
    return issues, has_mc

# 官方核心 13 件（04_模块库）
core_files = sorted(glob.glob('04_模块库/*/*.md'))
for f in core_files:
    issues, _ = check_file(f, strict=True)
    for i in issues:
        errs.append('[官方] ' + i)
# 社区模块（community/*/modules）
comm_files = sorted(glob.glob('community/*/modules/*.md'))
for f in comm_files:
    issues, has_mc = check_file(f, strict=False)
    if has_mc:
        for i in issues:
            errs.append('[社区] ' + i)   # 机读完备社区模块强校验
    elif issues:
        incomplete.append((os.path.basename(f), issues))
print('文档完整性扫描：官方 %d 件 + 社区 %d 件（社区机读完备强校验；未完备存量 WARN 统计 %d 件）'
      % (len(core_files), len(comm_files), len(incomplete)))
for base, iss in incomplete:
    print(' [WARN] 社区未完备存量（过渡期不阻断，随 retro-fit）：%s %s' % (base, '；'.join(iss[:2])))
for e in errs:
    print(' [FAIL] ' + e)
if incomplete:
    print(' [STAT] 社区未完备 %d 件（WARN 统计，随 13 方案过渡策略演进）' % len(incomplete))
sys.exit(1 if errs else 0)
PYEOF
    then
      :
    else
      no "check20 文档完整性校验失败——$(head -5 /tmp/nf_check20.log | tr '\n' ' ')"; err=1
    fi
  else
    wn 'python3 不在 PATH（跳过 check20）'
  fi
  if [ "$err" -eq 0 ]; then ok '文档完整性门禁全绿（check20：A3 模块必填项——官方强校验 + 社区机读完备强校验，未完备 WARN 统计）'
  fi
}
# ================= 主执行体（三段式） =================
echo '=================================================='
echo ' NarrativeForge 三段式验收门禁  v2.9（对齐 07 §7 + 08 T5 A5 资产对账 + 09 v0.6.0 check12 代码层 + check13 迁移完整性 + 10 v0.7.0 check14 社区协议登记门禁 + 11 v0.8.0 check15 组合引用门禁 + 12 v1.0.0 check16 契约仲裁门禁 + 16 v1.4.0 check17 质量治理门 + 17 v2.0.0 check18 导出契约门；分层治理 23 方案：L3 端壳冻结移出，门禁默认锁 L0-L2）'
echo '=================================================='
echo '—— 段 A：官方核心出厂（无 community 亦须通过）——'
check1; check2; check3; check4; check5; check6
echo '—— 段 B：社区领域包（两包在场执行，缺包 WARN 跳过）——'
if [ -d community/校园情感领域包 ] && [ -d community/西幻生存领域包 ]; then
  check7; check8; check9; check10; check11
elif [ -d community ]; then
  wn 'community 仅部分领域包在场：社区段（check7-11）跳过——单包/半包部署仅验收官方段'
else
  wn 'community 不在场：社区段（check7-11）跳过——无包部署仅验收官方段'
fi
echo '—— 段 C：代码层门禁（L2 core：check12-check18 无条件执行；android 相关已随 L3 冻结移出）——'
check12
check13
check14
check15
check16
check17
check18
check19
check20
echo '=================================================='
echo "结果统计: PASS=$PASS  WARN=$WARN  FAIL=$FAIL"
if [ "$FAIL" -gt 0 ]; then
  echo '>>> 存在 FAIL = 协议事故：请回滚本次修改，修正后重新运行验收 <<<'
  exit 1
else
  echo '>>> 全部通过（WARN 仅提示非致命），变更可提交 <<<'
  exit 0
fi
