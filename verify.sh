#!/usr/bin/env bash
# ============================================================
# NarrativeForge verify.sh —— 十项验收门禁（07 §7 可执行化）
# 版本 : v1.0  配套 : 07_官方核心出厂与社区预设导航.md §7（L116-129 判定标准）
# 用法 : 仓库根目录执行  bash verify.sh  （脚本自动定位根目录）
# 语义 : 任何 Agent/人对 01/02/03/04/05/06/07 层增删改后必须运行；
#        任一 FAIL = 协议事故 → 回滚该次修改再重新验收。
# 基准 : 判定逐字对齐 07 §7；计数/行数/锚点采用 v1.0 发布实测基线
#        （校园包 29 文件 1573 行 / 西幻包 23 文件 4285 行）。
# ============================================================
set -u
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT" || { echo '无法进入仓库根目录'; exit 2; }
PASS=0; FAIL=0; WARN=0
ok(){ PASS=$((PASS+1)); printf '  [PASS] %s\n' "$1"; }
no(){ FAIL=$((FAIL+1)); printf '  [FAIL] %s\n' "$1"; }
wn(){ WARN=$((WARN+1)); printf '  [WARN] %s\n' "$1"; }

check1(){
  echo '== [1/10] 目录结构完整 =='
  local err=0
  for f in 01_核心协议.md 02_联动注册表.md 06_Agent执行协议.md 07_官方核心出厂与社区预设导航.md README.md LICENSE; do
    [ -f "$f" ] || { no "根级缺失: $f"; err=1; }
  done
  local n03=$(find 03_管线库 -maxdepth 1 -name '*.md' 2>/dev/null | wc -l)
  [ "$n03" -ge 4 ] || { no "03_管线库应至少 4 个 md（P00 骨架 + 叙事实例），实为 $n03"; err=1; }
  for p in P00_通用文档生成管线.md P01_标准管线.md P02_校园情感流管线.md P03_西幻生存流管线.md; do
    [ -f "03_管线库/$p" ] || { no "03 缺管线文件: $p"; err=1; }
  done
  local n04=$(find 04_模块库 -name '*.md' 2>/dev/null | wc -l)
  [ "$n04" -ge 32 ] || { no "04_模块库应至少 32 个 md（叙事基准，可增不减），实为 $n04"; err=1; }
  local nw=$(find 04_模块库/世界类 -name '*.md' 2>/dev/null | wc -l)
  local ne=$(find 04_模块库/事件类 -name '*.md' 2>/dev/null | wc -l)
  local nq=$(find 04_模块库/情感类 -name '*.md' 2>/dev/null | wc -l)
  local ns=$(find 04_模块库/生存类 -name '*.md' 2>/dev/null | wc -l)
  local ng=$(find 04_模块库/通用类 -name '*.md' 2>/dev/null | wc -l)
  [ "$nw" -ge 6 ] || { no "04 世界类应至少 6，实为 $nw"; err=1; }
  [ "$ne" -ge 6 ] || { no "04 事件类应至少 6，实为 $ne"; err=1; }
  [ "$nq" -ge 6 ] || { no "04 情感类应至少 6，实为 $nq"; err=1; }
  [ "$ns" -ge 8 ] || { no "04 生存类应至少 8，实为 $ns"; err=1; }
  [ "$ng" -ge 6 ] || { no "04 通用类应至少 6，实为 $ng"; err=1; }
  [ -f 05_资产库/README.md ] || { no '05_资产库缺总 README'; err=1; }
  local nx=$(find 05_资产库/校园包 -name '*.md' ! -name 'README.md' 2>/dev/null | wc -l)
  local xh=$(find 05_资产库/西幻包 -name '*.md' ! -name 'README.md' 2>/dev/null | wc -l)
  [ "$nx" -eq 29 ] || { no "校园包资产应 29 文件，实为 $nx"; err=1; }
  [ "$xh" -eq 23 ] || { no "西幻包资产应 23 文件，实为 $xh"; err=1; }
  [ -d 05_资产库/用户自定义 ] || { no '05 缺 用户自定义 目录'; err=1; }
  if [ "$err" -eq 0 ]; then
    ok '根级 5 md + LICENSE；03 管线 ≥4（P00 骨架 + P01/P02/P03 实例）；04 模块 ≥32（世界≥6/事件≥6/情感≥6/生存≥8/通用≥6，可增不减）；05 总README+校园29+西幻23+用户自定义'
  fi
}

check2(){
  echo '== [2/10] 05_资产库行数溯源 =='
  local c=$(find 05_资产库/校园包 -name '*.md' ! -name 'README.md' -exec wc -l {} + 2>/dev/null | awk '/total/{s+=$1} END{print s+0}')
  local w=$(find 05_资产库/西幻包 -name '*.md' ! -name 'README.md' -exec wc -l {} + 2>/dev/null | awk '/total/{s+=$1} END{print s+0}')
  if [ "$c" -eq 1573 ] && [ "$w" -eq 4285 ]; then
    ok "行数溯源一致：校园 29 文件 ${c} 行 / 西幻 23 文件 ${w} 行"
  else
    no "行数偏差：校园 ${c}（应 1573）/ 西幻 ${w}（应 4285）——与子包 README 溯源表核对"
  fi
}

check3(){
  echo '== [3/10] 模块-资产引用可寻址 =='
  local err=0 cov=0
  local pairs='ATTR_TEMPLATES:05_资产库/校园包/ATTR_TEMPLATES.md
LOCATIONS:05_资产库/校园包/LOCATIONS.md
EMOTION_WHEEL:05_资产库/校园包/EMOTION_WHEEL.md
JOB:05_资产库/西幻包/01_职业成长与基础属性_JOB.md
WORLD_KNOWLEDGE:05_资产库/西幻包/20_世界知识_WORLD_KNOWLEDGE.md'
  while IFS=: read -r key file; do
    [ -n "$key" ] || continue
    if [ -f "$file" ]; then
      cov=$((cov+1))  # 键在 05 可寻址即通过（对齐 07 §7 第3项：04 引用 → 05 存在）
    else
      no "04 引用键 $key 对应 05 资产文件缺失（应可经 asset_get 五接口寻址）"; err=1
    fi
  done << EOF2
$pairs
EOF2
  if [ "$err" -eq 0 ]; then
    ok '代表键 ATTR_TEMPLATES/LOCATIONS/EMOTION_WHEEL/JOB/WORLD_KNOWLEDGE 在 05 全部可寻址（对齐 07 §7 第3项）'
  fi
}

check4(){
  echo '== [4/10] 重号 ID 全限定（M10 通用/生存、M22 情感/事件）=='
  local err=0
  # 04 层：四重号文件须各自存在且由类别目录隔离
  [ -f 04_模块库/通用类/M10_时间推进.md ] || { no '缺 通用类/M10_时间推进.md'; err=1; }
  [ -f 04_模块库/生存类/M10_死亡重生.md ] || { no '缺 生存类/M10_死亡重生.md'; err=1; }
  [ -f 04_模块库/情感类/M22_三冲动驱动.md ] || { no '缺 情感类/M22_三冲动驱动.md'; err=1; }
  [ -f 04_模块库/事件类/M22_事件叙事.md ] || { no '缺 事件类/M22_事件叙事.md'; err=1; }
  local n10=$(find 04_模块库 -name 'M10_*.md' | wc -l); local n22=$(find 04_模块库 -name 'M22_*.md' | wc -l)
  [ "$n10" -eq 2 ] || { no "M10 重号文件应 2 个，实为 $n10"; err=1; }
  [ "$n22" -eq 2 ] || { no "M22 重号文件应 2 个，实为 $n22"; err=1; }
  # 02 注册表：四个限定 ID 均须注册
  for q in '通用:M10' '生存:M10' '情感:M22' '事件:M22'; do
    grep -q "$q" 02_联动注册表.md || { no "注册表缺限定 ID: $q"; err=1; }
  done
  # 02/06/07：逐行扫描——含 M10/M22 的行须带类别词；仅当 M10 与 M22 同现（重号元说明）时豁免
  for f in 02_联动注册表.md 06_Agent执行协议.md 07_官方核心出厂与社区预设导航.md; do
    local bad=$(awk '
      { hasCat = ($0 ~ /通用|生存|情感|事件/)
        m10 = ($0 ~ /(^|[^0-9])M10([^0-9]|$)/)
        m22 = ($0 ~ /(^|[^0-9])M22([^0-9]|$)/)
        if ((m10 || m22) && !hasCat && !(m10 && m22) && $0 !~ /☐/) bad++ }
      END { print bad+0 }' "$f")
    [ "$bad" -eq 0 ] || { no "$f 含 ${bad} 处未类别限定的 M10/M22 引用"; err=1; }
  done
  # 05 西幻 README 溯源表：含 M10/M22 行须带功能限定词（西幻语境两重号并存）
  local wbad=$(awk '
    { m10 = ($0 ~ /(^|[^0-9])M10([^0-9]|$)/)
      m22 = ($0 ~ /(^|[^0-9])M22([^0-9]|$)/)
      if ((m10 || m22) && $0 !~ /死亡|时间|重生|事件|叙事/) bad++ }
    END { print bad+0 }' 05_资产库/西幻包/README.md)
  [ "$wbad" -eq 0 ] || { no "西幻包 README 含 ${wbad} 处未限定 M10/M22 引用"; err=1; }
  if [ "$err" -eq 0 ]; then ok 'M10/M22 四重号目录隔离；02/06/07 全类别前缀限定；05 西幻溯源表带功能限定'
  fi
}

check5(){
  echo '== [5/10] 五条不变式落点（01 §5）=='
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
check6(){
  echo '== [6/10] 认知边界（06 §4 管线 ↔ M23 认知域）=='
  local err=0
  # 06 §4 认知五步层名（L91-99：事实管线/快照/认知裁剪/裁剪渲染/锚点回验）
  for k in '事实管线' '事实快照' '认知裁剪' '裁剪渲染' '锚点回验'; do
    grep -q "$k" 06_Agent执行协议.md || { no "06 §4 缺认知层名: $k"; err=1; }
  done
  # M23 认知域措辞（视角裁剪/可见域/推断域/隐藏域 + fail/白描 违例处理）
  for k in '视角裁剪' '可见域' '推断域' '隐藏域' 'fail' '白描'; do
    grep -q "$k" 04_模块库/通用类/M23_认知边界.md || { no "M23 缺认知域措辞: $k"; err=1; }
  done
  if [ "$err" -eq 0 ]; then ok '06 §4 认知五步与 M23 认知域措辞语义一致（快照/裁剪/隐藏域/fail/白描）'
  fi
}
check7(){
  echo '== [7/10] 质检门（M80 gate 三档 ↔ 06 §5）=='
  local err=0
  # M80 gate yaml：pass:/warn:/fail: + 白描降级 + 隐藏域前置校验
  for k in 'pass:' 'warn:' 'fail:' '白描' '隐藏域直述'; do
    grep -q "$k" 04_模块库/通用类/M80_输出生成器.md || { no "M80 gate 缺: $k"; err=1; }
  done
  # 06 §5 gate 呼应（表 L110-112 + L133 违例处理）
  for k in 'pass' 'warn' 'fail' '隐藏域直述' '白描'; do
    grep -q "$k" 06_Agent执行协议.md || { no "06 §5 gate 缺呼应: $k"; err=1; }
  done
  if [ "$err" -eq 0 ]; then ok 'M80 gate 三档（pass/warn/fail + 白描降级）与 06 §5 呼应一致'
  fi
}
check8(){
  echo '== [8/10] 外部实体闭合（西幻 EXT 溯源）=='
  local err=0
  local f1="05_资产库/西幻包/01_职业成长与基础属性_JOB.md"
  local f2="05_资产库/西幻包/20_世界知识_WORLD_KNOWLEDGE.md"
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
  if [ "$err" -eq 0 ]; then ok '西幻01(36820-37280 职业)与西幻20(28894-29064 world_knowledge) EXT 闭合+溯源注释'
  fi
}
check9(){
  echo '== [9/10] v0.7.12 冲动隔离（M22 §7 ↔ 校园 README ↔ 06 §9 红线7）=='
  local err=0
  local m22="04_模块库/情感类/M22_三冲动驱动.md"
  local crd="05_资产库/校园包/README.md"
  # M22 §7：冲动驱动边界 + 关系推进权归属
  for k in '冲动驱动边界' '物理位移' '动作连带' '视线停留' 'relationship_change'; do
    grep -q "$k" "$m22" || { no "M22 §7 缺冲动隔离措辞: $k"; err=1; }
  done
  grep -q 'v0.7.12' "$m22" || { no 'M22 §7 缺 v0.7.12 版本锚点'; err=1; }
  # 校园包 README §4：v0.7.12/v0.7.13 补丁 + 隔离表述
  grep -q 'v0.7.12' "$crd" || { no '校园 README 缺 v0.7.12 版本锚点'; err=1; }
  grep -q '冲动-社会关系隔离' "$crd" || { no '校园 README 缺 冲动-社会关系隔离 表述'; err=1; }
  # 06 §9 红线 7：三冲动仅驱动表层行为，关系推进权归 M40/M41
  grep -q 'v0.7.12' 06_Agent执行协议.md || { no '06 §9 缺 v0.7.12 红线锚点'; err=1; }
  grep -q '关系推进权归 M40/M41' 06_Agent执行协议.md || { no '06 §9 缺 关系推进权归 M40/M41 表述'; err=1; }
  if [ "$err" -eq 0 ]; then ok '冲动-社会关系隔离三落点一致（M22 §7 / 校园 README §4 / 06 §9 红线7）'
  fi
}
check10(){
  echo '== [10/10] 入口导航（README → 07 → 协议链/资产/管线）=='
  local err=0
  # 总 README 指向 07 预设
  grep -q "07_官方核心出厂与社区预设导航" README.md || { no 'README 缺指向 07_官方核心出厂与社区预设导航'; err=1; }
  # 07 头部依据链：01/02/03/05/06 全部可寻址
  for k in '01_核心协议' '02_联动注册表' '03_管线库' '05_资产库' '06_Agent执行协议'; do
    grep -q "$k" 07_官方核心出厂与社区预设导航.md || { no "07 缺引用: $k"; err=1; }
  done
  # 被引用目标文件确实存在（可访问性闭环）
  for f in 01_核心协议.md 02_联动注册表.md 06_Agent执行协议.md; do
    [ -f "$f" ] || { no "导航目标缺失: $f"; err=1; }
  done
  [ -d 03_管线库 ] || { no '导航目标缺失: 03_管线库 目录'; err=1; }
  [ -d 05_资产库 ] || { no '导航目标缺失: 05_资产库 目录'; err=1; }
  if [ "$err" -eq 0 ]; then ok 'README→07→01/02/03/05/06 入口导航闭环可访问'
  fi
}
# ================= 主执行体 =================
echo '=================================================='
echo ' NarrativeForge 十项验收门禁  v1.0（对齐 07 §7）'
echo '=================================================='
for i in 1 2 3 4 5 6 7 8 9 10; do
  check$i
done
echo '=================================================='
echo "结果统计: PASS=$PASS  WARN=$WARN  FAIL=$FAIL"
if [ "$FAIL" -gt 0 ]; then
  echo '>>> 存在 FAIL = 协议事故：请回滚本次修改，修正后重新运行验收 <<<'
  exit 1
else
  echo '>>> 十项全部通过，变更可提交 <<<'
  exit 0
fi
