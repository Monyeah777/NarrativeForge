#!/usr/bin/env bash
# ============================================================
# NarrativeForge verify.sh —— 两段式验收门禁（07 §7 可执行化）
# 版本 : v2.29  配套 : 07_官方核心出厂与社区预设导航.md §7（两级结构终验）+ 08_社区扩展规划与验收方案.md T5 A5（资产三方对账）+ 09_v0.6.0_协议中转站方案（check12 代码层门禁 + check13 协议版本一致性/迁移完整性）+ 10_v0.7.0_自定义协议方案（check14 社区协议登记门禁）+ 11_v0.8.0_自定义模块组合方案（check15 组合引用门禁）+ 12_v1.0.0_自定义模块组合方案（check16 契约仲裁门禁）+ 16_v1.4.0_质量治理闭环方案（check17 质量治理门）+ 17_v2.0.0_导出层CCV3方案（check18 导出契约门）+ 33_v2.2.0_外部吸收首波方案（check19 导出产物 schema 合规 + check20 文档完整性门禁 + check21 registry 引用图闭合门禁）+ 35_v2.4.0_外部吸收大包方案（check22 导出物规范体检门禁 + 40 总纲 v2.7 S2 check23 资产供应链闭合门禁 + 40 总纲 v2.8 波B S4-S7 check24 模块生命周期门禁 + 41_v2.8.0_波C 质量编译深化规划（check25 协议知识签名可复现门禁 + 41_v2.8.0_波C 质量编译深化规划（check26 语义矛盾扫描门禁 + 42_顶尖质量纵深工程规划（check27 架构纯度体检门禁 + 43_协议层顶尖化工程规划（check28 协议层 IDL schema + check29 Conformance 分级 + check30 扩展策略/bump 迁移 + check31 生成物 golden）+ 终端线 check39（端壳退役零回潮 + nf shell 终端入口在场 + 菜单无死命令 + 输出确定）
#        46 吸收七面 check33：MCP dual-era 版本对齐（2026-07-28/2025-11-25 + server/discover）/
#        内容外挂签名 attestation / 基线相对回归评分 / 机械修复 + LSP / 正文 lint / 图书馆许可证门 / 遥测 semconv
#        图书馆面 check34：条目 frontmatter 真源（OKF 借鉴）/ INDEX·ALIAS 投影一致（I5）/ 生命周期 /
#        Diátaxis 四型覆盖 / llms.txt 机器入口清单 / 正文级馆藏检索
#        深化面 check35（Pipelex/MCOP/Specadia 机制借鉴）：管线抽象执行 GraphSpec / 馆藏 MMR 回执单根 /
#        模块边界签名冻结 / 内容绑定批准记录 / 一致性报告工件（Merkle 根 + verdict）/ 无效语料 + golden 修复对
#        治理面 check36（ACP / HMP / ai-chat-protocol 机制借鉴）：一致性声明（scope + 显式排除）/
#        协议件 RFC 头 + supersede 链 / 指令档机器面路由（driver override：fail-closed 不回退）/
#        实践包品类 / 执行结果跑分台 / 服务端点契约（maps_to 指向真实性）
#        知识层 check37：双源知识声明（权威分层 / 查询有序 / 时效 / 可见性）/ 消化可追溯记录
#        （源 ↔ 产物 digest 绑定 + 转正三档证据 + 双签）/ 知识层巡检（悬空 / 孤儿 / 时效缺口）
# 用法 : 仓库根目录执行  bash verify.sh  （脚本自动定位根目录）
# 语义 : 任何 Agent/人对 01/02/03/04/05/06/07 层增删改后必须运行；
#        任一 FAIL = 协议事故 → 回滚该次修改再重新验收。
# 结构 : [段 A] 官方核心出厂（check1-6，无 community 亦须通过）
#        [段 B] 社区领域包（check7-11，两包在场时执行；缺包 WARN 跳过）
#        [段 C] 代码层门禁（check12-check32，无条件执行：分层治理 23 方案——本段默认锁 L0-L2；
#        段 A/B = L0/L1（协议一致性 + 内容对账），check12-22 = L2 core（unittest/py_compile/协议投影/
#        组合/契约/质量/导出/产物schema/文档完整性/registry闭合门/导出物规范体检）；android 相关 check 已随 L3 端壳线退役移出（桌面 GUI 端壳 2026-09-09 同轨退役，见 L3_FROZEN.md）。check12 = desktop unittest 全量 + 全量 py_compile；check13 = 协议版本一致性（两处）+ 迁移完整性；check14 = 社区协议登记门禁：01 §6.1 Schema 必填 12 字段 + 02 §8.3 登记三要件 + registry protocols[] 投影一致；check15 = 组合引用门禁：02 §8.4 references 五断言（在册可寻址/依赖闭包闭合/挂载层冲突/schema 兼容/双源一致）；check16 = 契约仲裁门禁：01 §1.1 machine_contract 机读结构 + 02 §8.4 规则④ references 装配 publish⊆subscribe + 运行时寻址授权一致；check17 = 质量治理门；check18 = 导出契约门；check19 = 导出产物 schema 合规（A1）；check20 = 文档完整性门禁（A3）；check21 = registry 引用图闭合门禁（A4）；check22 = 导出物规范体检门禁（A4，35 方案）；check23 = 资产供应链闭合门禁（40 总纲 S2：溯源键表 provenance.json + 文件头双源一致；check24 = 模块生命周期门禁（40 总纲 v2.8 波B S5：模块头 status 位 + deprecate/restore + 引用门禁——deprecated/retired 不得被引用）；check25 = 协议知识签名门禁（41 波C C2：01-36 全量签名两遍生成逐字节一致 + 结构字段齐备）；check26 = 语义矛盾扫描门禁（41 波C C3：techdoc 链 machine_contract 订阅事件无发布方断链 + 挂载点/类别漂移）；check27 = 架构纯度体检门禁（42 M3：协议层端壳残留/私货可变物/重复标题 grep + core raise 消息修复指引审计））
# 基准 : 判定逐字对齐 07 §7；04=核心 13 件 / 03=P00+P01+P90 / 05=README+用户自定义；
#        抽象阶梯（两轴 + 纵切）判据并入 check27 R7——真源 protocol/LAYERS.json，
#        语义判据在 desktop/src/core/layer_model.py（见 docs/layers.md）。
#        校园资产 29 文件 1575 行 / 西幻资产 23 文件 4284 行（西幻 4285→4284：2026-09-20 删
#        11_魔法系统_MAGIC.md 的孤立收尾围栏 1 行；行数基线属**发布基线**，内容改动后须核对更新）。
# ============================================================
set -u
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT" || { echo '无法进入仓库根目录'; exit 2; }
# ---- 临时文件隔离（并发安全：每次运行独立目录，避免共享固定路径互相覆盖日志）----
# 背景：本仓库常有并发 agent 会话同时跑门禁；固定 /tmp 路径会让 B 会话的失败日志
#       覆盖 A 会话的诊断输出，导致「看到的失败不是自己的」。原生 Windows（无 Git Bash）下
#       硬编码 /tmp 亦不成立。故改为每次运行 mktemp -d 并在退出时清理。
NFL_TMP="$(mktemp -d 2>/dev/null || echo "${TMPDIR:-/tmp}/nf_verify_$$")"
if [ -z "$NFL_TMP" ] || [ ! -d "$NFL_TMP" ]; then
  NFL_TMP="${TMPDIR:-/tmp}/nf_verify_$$"; mkdir -p "$NFL_TMP" 2>/dev/null || true
fi
cleanup_nfl(){
  # 全绿才清理；有 FAIL 时保留目录——诊断日志是修复依据，删掉等于把修复线索一起删了。
  if [ "${FAIL:-0}" -gt 0 ]; then
    printf '  [i] 本次有 FAIL —— 诊断日志保留在：%s\n' "$NFL_TMP" >&2
  else
    [ -n "$NFL_TMP" ] && [ "$NFL_TMP" != "/" ] && rm -rf "$NFL_TMP" 2>/dev/null
  fi
  return 0
}
trap cleanup_nfl EXIT INT TERM
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
# 机制借鉴 reviewdog 的「发现 → 结构化注解」：在 GitHub Actions 里把 FAIL/WARN 同时打成
# Actions 注解（`::error::` / `::warning::`），失败直接显示在 CI 摘要与 PR 界面；
# 本地跑（无 GITHUB_ACTIONS）行为不变。多行消息按 Actions 规则转义为 %0A。
_gha_note(){ [ "${GITHUB_ACTIONS:-}" = "true" ] || return 0
  printf '::%s title=verify.sh::%s\n' "$1" "${2//$'\n'/%0A}"; }
no(){ FAIL=$((FAIL+1)); printf '  [FAIL] %s\n' "$1"; _gha_note error "$1"; }
wn(){ WARN=$((WARN+1)); printf '  [WARN] %s\n' "$1"; _gha_note warning "$1"; }
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
    # 段号须带分隔符匹配：`^### 8\.1` 会连 `### 8.10` 一起命中（域包 >9 个即误取，
    # 2026-09-22 AI 品类域包扩面实测踩到）——故锚定 `### 8.N `（后随空格）
    regxy=$(sed -n '/^### 8\.1 /,/^### 8\.2 /p' 02_联动注册表.md | grep -oE '模块（[0-9]+）' | grep -oE '[0-9]+')
    regxh=$(sed -n '/^### 8\.2 /,/^### 8\.3 /p' 02_联动注册表.md | grep -oE '模块（[0-9]+）' | grep -oE '[0-9]+')
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
  # 基线 = 可重签工件 protocol/asset_line_baseline.json（不再把数字写在 verify.sh 里）：
  # 内容/外形改动 → FAIL + 重签指引（nf asset baseline --write）；缺包按段 B 只记 WARN。
  local err=0
  if [ -n "$PY3" ]; then
    if "$PY3" - <<'PYEOF' >"$NFL_TMP"/nf_check8.log 2>&1
import os, sys
sys.path.insert(0, os.path.join('desktop', 'src'))
try:
    from core import asset_line_baseline as alb
except Exception as exc:
    print('import 失败：%s' % exc)
    sys.exit(1)
issues, warns, stats = alb.verify('.')
for i in issues:
    print('[FAIL] %s' % i)
for w in warns:
    print('WARN: %s' % w)
lines = stats.get('lines') or {}
files = stats.get('files') or {}
summary = ' / '.join('%s %d 文件 %d 行' % (p, files.get(p, 0), lines.get(p, 0))
                     for p in sorted(lines)) or '无在场社区包（基线 %d 包在册）' % stats.get('baseline', 0)
print('SUMMARY %s' % summary)
sys.exit(1 if issues else 0)
PYEOF
    then
      _bl_sum=$(LC_ALL=C.UTF-8 grep -a '^SUMMARY ' "$NFL_TMP"/nf_check8.log | sed 's/^SUMMARY //')
      while IFS= read -r _blline; do
        case "$_blline" in WARN:*) wn "${_blline#WARN: }" ;; esac
      done < "$NFL_TMP"/nf_check8.log
      ok "行数溯源一致（基线可重签）：${_bl_sum:-N/A}"
    else
      while IFS= read -r _blline; do
        case "$_blline" in WARN:*) wn "${_blline#WARN: }" ;; esac
      done < "$NFL_TMP"/nf_check8.log
      no "社区资产行数溯源不符——$(head -3 "$NFL_TMP"/nf_check8.log | tr '\n' ' ')"; err=1
    fi
  else
    wn 'python3 不在 PATH（跳过 check8 资产行数溯源）'
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
    if ( cd desktop && "$PY3" -m unittest discover -s tests -q >"$NFL_TMP"/nf_check12_unittest.log 2>&1 ); then
      ok 'desktop core 单元测试全绿（desktop/tests 全量 discover，纯 unittest 内置）'
    else
      no "desktop core 单元测试失败——见 $NFL_TMP/nf_check12_unittest.log"; err=1
      echo "  ── unittest log 尾部（诊断回显）──"
      tail -40 "$NFL_TMP"/nf_check12_unittest.log 2>/dev/null | sed 's/^/    /'
    fi
  else
    wn 'desktop/tests 不在场（跳过代码层 unittest）'
  fi
  # ② 全量 py_compile 语法抽查（desktop/src scripts——L2 core 域；android/app
  #    已彻底移除（裁决 #16），不再编译，见 L3_FROZEN.md）
  if [ -n "$PY3" ]; then
    if "$PY3" -m compileall -q desktop/src scripts >"$NFL_TMP"/nf_check12_pyc.log 2>&1; then
      ok '全量 py_compile 语法抽查通过（desktop/src scripts）'
    else
      no "py_compile 语法抽查失败——见 $NFL_TMP/nf_check12_pyc.log"; err=1
      echo "  ── py_compile log 尾部（诊断回显）──"
      tail -30 "$NFL_TMP"/nf_check12_pyc.log 2>/dev/null | sed 's/^/    /'
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
  #    （两处同源。android/app/core 已彻底移除（裁决 #16）——不再参与比对，见 L3_FROZEN.md）
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
    if "$PY3" - <<'PYEOF' >"$NFL_TMP"/nf_check13_cmp.log 2>&1
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
for _e in errs:
    print(_e)
sys.exit(1 if errs else 0)
PYEOF
    then
      ok '模块逐条一致：02 §2 模块表 13 件 == registry.json modules（ID 集合全等）'
    else
      no "模块表与机读投影不一致——$(head -3 "$NFL_TMP"/nf_check13_cmp.log | tr '\n' ' ')"; err=1
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
    no 'protocol.yaml 缺失——check14 ②-⑧ 跳过（登记三要件不全，包不被平台门禁识别）'
    return
  fi
  # ②-⑧ 精确比对（python3 + PyYAML：解析两包 protocol.yaml + desktop registry.json + 02 文档反解 + 03 管线库反解）
  if [ "$YAMLOK" -eq 1 ]; then
    if "$PY3" - <<'PYEOF' >"$NFL_TMP"/nf_check14.log 2>&1
import glob, json, os, re, sys
import yaml

# C2 包目录 glob 化（29 方案 B3-C）：遍历层（②④⑥⑦ + ① 目录在场）自动发现 community/* 全部
# 含 protocol.yaml 的目录——新增组合/通用包登记零改 verify.sh（目录 + protocol.yaml + registry 条目即可）。
# DOMAIN = 领域包显式登记（③ 独占类别互斥 + ⑤ 编号在册/M91-99 不占用专属）——领域包语义依赖
# 02 §8.1/8.2 段落结构（segmap）与「不占 M91-99 社区段」规则（通用 M93-96/轻混 M91-92 合法占段，
# 不能内容推导纳入领域检查）；新增领域包须在此登记 + 02 §8 开新段 + registry 条目（登记三要件②）。
DOMAIN = ['community/校园情感领域包', 'community/西幻生存领域包', 'community/大语言模型域包', 'community/多模态大模型域包', 'community/视觉模型域包', 'community/语音识别与合成域包', 'community/音频与音乐生成域包', 'community/视频生成与理解域包', 'community/图像生成与编辑域包', 'community/文本生成与创作域包', 'community/摘要与信息压缩域包', 'community/机器翻译与本地化域包', 'community/分类与情感分析域包', 'community/代码大模型域包', 'community/嵌入与检索表示域包', 'community/具身智能与机器人域包', 'community/三维与世界模型域包', 'community/数学与形式化推理域包', 'community/强化学习与决策域包', 'community/端侧与边缘小模型域包', 'community/信息抽取与结构化域包', 'community/知识问答与检索增强域包', 'community/多轮对话与角色扮演域包', 'community/代码生成与补全域包', 'community/代码审查与缺陷检测域包', 'community/测试与用例生成域包', 'community/数据分析与表格理解域包', 'community/文档解析与版面理解域包', 'community/语音转写与会议记录域包', 'community/语音合成与配音域包', 'community/图像生成与视觉设计域包', 'community/视频生成与自动剪辑域包', 'community/数据采集与清洗域包', 'community/数据标注与标注质量域包', 'community/合成数据生成域包', 'community/预训练与继续预训练域包', 'community/参数高效微调域包', 'community/对齐与偏好优化域包', 'community/推理优化与加速域包', 'community/推理服务与部署域包', 'community/上下文工程与长上下文域包', 'community/提示工程与提示模板域包', 'community/记忆体与个性化域包', 'community/向量库与检索管线域包', 'community/智能体框架与工具调用域包', 'community/多智能体协同域包', 'community/物流与供应链域包', 'community/交通与出行域包', 'community/建筑与房地产域包', 'community/传媒与新闻域包', 'community/文旅与酒店域包', 'community/科研与实验域包', 'community/提示工程与指令设计域包', 'community/世界书与设定库域包', 'community/长文本与小说创作域包', 'community/内容改写与风格迁移域包', 'community/多语翻译与本地化域包', 'community/图像生成与视觉创作域包', 'community/视频生成与剪辑域包', 'community/音频音乐与语音域包', 'community/编辑校对与出版域包', 'community/智能体与工作流编排域包', 'community/代码与软件工程域包', 'community/数据分析与决策支持域包', 'community/个人助理与日常生活域包', 'community/搜索与信息聚合域包', 'community/内容分发与社区运营域包', 'community/数字人与虚拟形象域包', 'community/安全与对齐域包', 'community/合规与监管域包', 'community/隐私与数据治理域包', 'community/版权与知识产权域包', 'community/可解释性与审计域包', 'community/模型运营与成本域包', 'community/平台与基础设施域包', 'community/产业与商业落地域包', 'community/监督微调域包', 'community/零售与电商域包', 'community/游戏与互动娱乐域包', 'community/角色扮演与角色卡域包', 'community/知识管理与检索增强域包', 'community/企业培训与组织学习域包', 'community/对话与客服域包', 'community/评测与基准域包', 'community/开源与开发者生态域包', 'community/推荐排序与广告域包', 'community/预测异常与风险域包', 'community/评测基准与排行榜域包', 'community/红队越狱与安全测试域包', 'community/可观测性成本与可靠性域包', 'community/AI医疗健康域包', 'community/AI制药与生物域包', 'community/AI法律与合规域包', 'community/AI金融投研与风控域包', 'community/AI保险域包', 'community/AI教育域包', 'community/AI政务与公共事务域包', 'community/AI制造业域包', 'community/AI能源与电力域包', 'community/AI农业域包', 'community/AI人力资源与招聘域包', 'community/AI食品与餐饮域包', 'community/组合包-检索栈', 'community/组合包-数据管线', 'community/组合包-受监管行业', 'community/组合包-轻混与保险']
# LEGACY_BARE = 存量既有领域包（v1.1 迁出模块沿用原编号不改号，包内裸号属既有）；其余包**新增**
# 编号须落 M91-M99 机制段或 <独占类别>:Mxx 类内段（01 §1.6.11 编号命名空间扩展；每类 00-99 独立）。
LEGACY_BARE = set(DOMAIN)
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
    #    + 编号命名空间判据（01 §1.6.11：类别在册 / 类内号唯一 / 全库不重号 / 新包裸号限 M91-M99）
    doc = open('02_联动注册表.md', encoding='utf-8').read()
    # segmap：领域包目录 → 02 §8.x 段（按段标题含包名定位；新增领域包自动匹配，勿硬编码 §8.1/§8.2 下标）
    segmap = {}
    for d in DOMAIN:
        segname = d.split('/')[-1]
        segpat = re.compile(r'^### 8\.\d+ %s\b.*?(?=^### 8\.|^## 9\.)' % re.escape(segname), re.S | re.M)
        segm = segpat.search(doc)
        segmap[d] = segm.group(0) if segm else ''
    for d in DOMAIN:
        if d not in data:
            continue        # 合成/局部树里可缺该包目录（真实树上由 ① 段判 missing）
        ids = [str(x) for x in data[d]['package']['module_id_range']]
        m99 = [i for i in ids if re.match(r'^M9[1-9]$', i)]
        if m99: errs.append('%s ⑤M91-M99 段被占用: %s（新包新增编号才落 M91-M99，既有包沿用原编号）' % (d, ','.join(m99)))
        mm = re.search(r'模块（(\d+)）', segmap[d])
        regn = int(mm.group(1)) if mm else -1
        if regn < 0:
            errs.append('%s ⑤02 §8 在册模块数未取到' % d)
        elif len(ids) != regn:
            errs.append('%s ⑤module_id_range(%d) != 02 §8 在册(%d)' % (d, len(ids), regn))
    # ⑤b 编号命名空间（全部登记包逐条）：形态 = 裸号 Mxx（机制段 M91-M99，全局唯一）或
    #     <类别>:Mxx 类内段（类别须在本包 categories 在册 = R2 独占；类内号在类别内唯一）；
    #     两种形态都不许跨包重号（module id 是全局寻址面）。
    seen_mid, seen_catnum = {}, {}
    for d in ALL_PKGS:
        pkg = data[d]['package']
        cats = set(str(c) for c in (pkg.get('categories') or []))
        for mid in [str(x) for x in (pkg.get('module_id_range') or [])]:
            if mid in seen_mid:
                errs.append('⑤模块 id 跨包重号: %s ∈ %s 与 %s（编号须全局唯一寻址）' % (mid, d, seen_mid[mid]))
            seen_mid[mid] = d
            mpre = re.match(r'^([^:]+):(M\d{2,3})$', mid)
            if mpre:
                cat, num = mpre.group(1), mpre.group(2)
                if cat not in cats:
                    errs.append('%s ⑤类内编号类别未在册: %s（类别 %s 须列入本包 categories，R2 独占；01 §1.6.11）'
                                % (d, mid, cat))
                ckey = (cat, num)
                if ckey in seen_catnum and seen_catnum[ckey] != d:
                    errs.append('⑤类内号重号: %s ∈ %s 与 %s（同类别内编号须唯一）' % (mid, d, seen_catnum[ckey]))
                seen_catnum[ckey] = d
            elif re.match(r'^M\d{2,3}$', mid) and d not in LEGACY_BARE and not re.match(r'^M9[1-9]$', mid):
                errs.append('%s ⑤裸号越段: %s（新包新增编号落 M91-M99 机制段或 <独占类别>:Mxx 类内段；'
                            '既有包沿用原编号不改号——01 §1.6.11）' % (d, mid))
    # ⑤c 裸号索引歧义（2026-09-20 作者裁决收口）：运行时模块索引 pipelinerun._module_files 以
    #     **文件名 stem 裸号**为键、setdefault 先到先得——类内段新编号与既有包 / 官方核心裸号相同
    #     时，会静默改写既有管线的裸号引用解析（实测战例：AI系统:M01/M02 曾把西幻 P03 的
    #     M01/M02 解析改指本包；本处把该隐患写成三条判据）：
    #     ① 同一裸号不得属两个及以上 community 包（真歧义）；
    #     ② 同包内文件名裸号不得重复（同包歧义）；
    #     ③ 包自有裸号若被官方核心 / 他包占用，则本包管线不得以**裸号**引用它（须全限定）。
    _stem_owner = {}
    for _m in sorted(glob.glob('community/*/modules/*.md')):
        _pkg = _m.replace('\\', '/').split('/')[1]
        _stem_owner.setdefault(os.path.basename(_m).split('_')[0], []).append(_pkg)
    _core_stems = {os.path.basename(_f).split('_')[0] for _f in glob.glob('04_模块库/*/*.md')}
    for _stem, _pkgs in sorted(_stem_owner.items()):
        _uniq = sorted(set(_pkgs))
        if len(_pkgs) > 1 and len(_uniq) == 1:
            errs.append('%s ⑤裸号同包重复：文件名裸号 %s 出现 %d 次'
                        '（修复指引：同包模块编号须唯一）' % (_uniq[0], _stem, len(_pkgs)))
        elif len(_uniq) > 1:
            errs.append('⑤裸号跨包重号：%s 同时属 %s（运行时模块索引按裸号先到先得解析，'
                        '后到包的裸号引用会被静默改写；修复指引：类内段换号，或全部改用全限定 id 引用）'
                        % (_stem, '、'.join(_uniq)))
    for _pkg in sorted({p for v in _stem_owner.values() for p in v}):
        _own = {s for s, v in _stem_owner.items() if _pkg in v}
        for _pf in sorted(glob.glob('community/%s/pipelines/*.md' % _pkg)):
            try:
                _text = open(_pf, encoding='utf-8').read()
            except OSError:
                continue
            for _lst in re.findall(r'(?m)^\s*(?:default_modules|allowed_modules)\s*:\s*\[([^\]]*)\]',
                                   _text):
                for _tok in (x.strip() for x in _lst.split(',')):
                    if not _tok or ':' in _tok:
                        continue
                    if _tok in _own and (_tok in _core_stems
                                         or len(set(_stem_owner.get(_tok, []))) > 1):
                        errs.append('%s ⑤裸号引用歧义：%s 以裸号引用 %s，而该裸号被官方核心 / 他包占用'
                                    '（修复指引：改写为全限定 id，如 <类别>:%s）'
                                    % (_pf.replace('\\', '/'), _pkg, _tok, _tok))
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
        # v2.5.0 Wave2 版本槽位：package.version 双源一致（缺省等价 1.0.0，V1 只增不删）
        _reg_ver = str(p.get('version') or '1.0.0')
        _proto_ver = str(pkg.get('version') or '1.0.0')
        if _reg_ver != _proto_ver: errs.append('⑦%s version 不一致: reg=%s proto=%s' % (pid, _reg_ver, _proto_ver))
        # 包内容版本格式（02 §8 SemVer 映射：MAJOR.MINOR.PATCH；档位一致性由评审判，机检只判格式）
        for _src, _v in (('registry', _reg_ver), ('protocol.yaml', _proto_ver)):
            if not re.match(r'^\d+\.\d+\.\d+$', _v):
                errs.append('⑦%s package.version 非语义化版本格式: %s=%s（预期 MAJOR.MINOR.PATCH，02 §8 包内容版本）'
                            % (pid, _src, _v))
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
    # ⑧ 管线 id 避让与唯一（R3，01 §1.6.11）：管线 id 与层位 id 同形（P\d{2}），机读侧层位靠 id 解析，
    #    故自带管线须 ① 全库唯一 ② 不占官方管线 id（03_管线库 在册）③ 不占注册层位 id
    #    （registry mount_points = 02 §5 九层）。官方 P00 骨架与 P00 层位同号为派生同名先例，存量豁免。
    layers = set((reg.get('mount_points') or {}).keys())
    offi = set()
    for _f in glob.glob('03_管线库/*.md'):
        try:
            with open(_f, encoding='utf-8') as _fh:
                _m = re.search(r'^\s*id:\s*(P\d{2})\s*$', _fh.read(), re.M)
        except OSError:
            continue
        if _m:
            offi.add(_m.group(1))
    seen_pipe = {}
    for p in reg.get('protocols', []):
        _pid, _pl = str(p.get('id')), str(p.get('pipeline'))
        if _pl in layers:
            errs.append('⑧%s 管线 id 占用层位 id: %s（层位 id = registry mount_points；自带管线须避让——01 §1.6.11）'
                        % (_pid, _pl))
        if _pl in offi:
            errs.append('⑧%s 管线 id 与官方管线重号: %s（03_管线库 在册）' % (_pid, _pl))
        if _pl in seen_pipe:
            errs.append('⑧管线 id 跨包重号: %s ∈ %s 与 %s' % (_pl, _pid, seen_pipe[_pl]))
        seen_pipe[_pl] = _pid
for _e in errs:
    print(_e)
sys.exit(1 if errs else 0)
PYEOF
    then
      :
    else
      no "check14 ②-⑧ 校验失败——$(head -5 "$NFL_TMP"/nf_check14.log | tr '\n' ' ')"; err=1
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
    [ "$miss2" -eq 0 ] && wn 'check14 ②-⑧ 精确比对跳过（PyYAML 缺失，仅必填键文本粗校验；建议安装 pyyaml 后重跑）'
  fi
  if [ "$err" -eq 0 ]; then ok '社区协议登记门禁全绿（check14 八项：①protocol.yaml 在场 ②Schema 必填 12 字段 ③R2 类别不冲突 ④R1 依赖边界 ⑤编号在册一致+M91-M99 不占用+编号命名空间（类别在册/类内号唯一/全库不重号/新包裸号限段） ⑥双源一致 ⑦protocols[] 投影一致 ⑧管线 id 避让层位/官方 id 且全库唯一）'
  fi
}
check15(){
  echo '== [15/段C] 组合引用门禁（v0.8.0 check15：02 §8.4 references 五断言）=='
  local err=0 PYOK=0 YAMLOK=0
  [ -n "$PY3" ] && PYOK=1
  { [ "$PYOK" -eq 1 ] && "$PY3" -c 'import yaml' >/dev/null 2>&1; } && YAMLOK=1
  [ "$YAMLOK" -eq 1 ] || wn 'Python/PyYAML 不可用（check15 组合引用精确比对降级为 references 键文本粗校验；建议 pip install pyyaml 后重跑）'
  if [ "$YAMLOK" -eq 1 ]; then
    if "$PY3" - <<'PYEOF' >"$NFL_TMP"/nf_check15.log 2>&1
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
    _pushed_sp = set()   # 同一源包的多条 references = 一条包级依赖（去重；2026-09-23 实测：
                         # 轻混包补 3 条校园引用后，同源多引被本段误判「依赖闭包成环」）
    for r in refs:
        sp = r.get('source_package')
        if sp in _pushed_sp:
            continue
        if sp in dir_by_id:
            _pushed_sp.add(sp)
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
        # 2026-09-23 精化：嵌套引用**允许**，但必须**显式闭合**——引用方须把源包的全部
        # references（source_package, module_id）逐条登记在自己白名单里；否则依赖链存在隐藏层。
        # 这既支撑「组合包再组合」（组合引擎产物化），又保住本规则的原始意图（无隐式多层依赖）。
        _nested = [x for x in (pkg2.get('references') or []) if isinstance(x, dict)]
        if _nested:
            _have = {(x.get('source_package'), str(x.get('module_id')))
                     for x in refs if isinstance(x, dict)}
            _miss = [(x.get('source_package'), str(x.get('module_id')))
                     for x in _nested
                     if (x.get('source_package'), str(x.get('module_id'))) not in _have]
            if _miss:
                errs.append('②%s 源包 %s 的嵌套 references 未显式闭合（缺 %s；修复指引：'
                            '把源包的 references 逐条登记进本包白名单）' % (pid, sp, _miss[:3]))
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
# ⑥ 钉扎复核提示（01 §6.1：源包结构性变更对已钉扎引用方属条件安全变更；钉扎滞后 = WARN 提示，不判死）
for _d in PKGS:
    if _d not in data or 'package' not in data[_d]:
        continue
    _pid = data[_d]['package'].get('id')
    for _r in data[_d]['_refs']:
        _sp = _r.get('source_package')
        _pin = str(_r.get('source_schema_version'))
        _sd = dir_by_id.get(_sp)
        if not _sd or _sd not in data:
            continue
        _cur = str((data[_sd].get('protocol') or {}).get('schema_version'))
        if _cur and _pin != _cur:
            print('WARN: %s 引用 %s 钉扎=%s，源包当前=%s —— 钉扎滞后，复核契约后更新（01 §6.1 钉扎复核）'
                  % (_pid, _sp, _pin, _cur))
for _e in errs:
    print(_e)
sys.exit(1 if errs else 0)
PYEOF
    then
      # 钉扎复核提示透传（WARN 不判死：刻意钉旧版本合法，但必须可见）
      if [ -f "$NFL_TMP"/nf_check15.log ]; then
        while IFS= read -r _pinline; do
          case "$_pinline" in WARN:*) wn "${_pinline#WARN: }" ;; esac
        done < "$NFL_TMP"/nf_check15.log
      fi
    else
      no "check15 ①-⑤ 校验失败——$(head -5 "$NFL_TMP"/nf_check15.log | tr '\n' ' ')"; err=1
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
    if "$PY3" - <<'PYEOF' >"$NFL_TMP"/nf_check16a.log 2>&1
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
# ④ 发布方唯一 + 事件名词法（01 §1.1）：ASCII 小写蛇形——防全角/大小写/同形字造成「看起来同名其实不同名」
def _ok_event_name(e):
    return (isinstance(e, str) and e.isascii() and e == e.lower() and 1 <= len(e) <= 40
            and e[0].isalpha() and all(c.isalnum() or c == '_' for c in e))
owners = {}
seen_names = {}
for f in CORE13 + sorted(glob.glob('community/*/modules/*.md')):
    owner_mc = extract_mc(f)
    if not isinstance(owner_mc, dict):
        continue
    owner_id = str(owner_mc.get('id') or f)
    _ev = owner_mc.get('events') or {}
    for _side in ('publish', 'subscribe'):
        for e in (_ev.get(_side) or []):
            seen_names.setdefault(str(e), set()).add(_side)
            if _side == 'publish':
                owners.setdefault(str(e), set()).add(owner_id)
for e in sorted(seen_names):
    if not _ok_event_name(e):
        errs.append('④事件名词法违约：%s（须 ASCII 小写蛇形 ^[a-z][a-z0-9_]{0,39}$——防全角/大小写/同形字撞名）' % e)
multi_pub = {e: sorted(v) for e, v in owners.items() if len(v) > 1}
for e in sorted(multi_pub):
    errs.append('④发布方唯一违约：事件 %s 有多个发布方 %s（01 §1.1 发布方唯一；跨题材事件须经官方核心中介即事件桥）'
                % (e, multi_pub[e]))

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
    # ① 先按**机读契约声明 id**匹配（2026-09-23 实测修正）：AI 品类域包的模块文件名 stem 是
    #    包内 token（如 A01a_…），权威 id 在 machine_contract.id（如 大语言模型:M01）——
    #    只按文件名裸号定位会漏判「源模块文件缺失」。契约 id 优先，文件名裸号兜底（官方 04 模块库）。
    for f in sorted(glob.glob(os.path.join(mod_dir, '*.md'))):
        mc = extract_mc(f)
        if isinstance(mc, dict) and str(mc.get('id') or '') in (mid, bare):
            return f
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
    # 邻居订阅面 = 本包自有模块 ∪ **本包引用的源模块**（2026-09-23 修正）：组合包的装配单元
    # 就是「自有 + 借阅」的模块集；组合包自有模块为 0 时（产物化组合包），若只数自有模块，
    # 借阅模块的发布面必然被判「无邻居订阅」而误报契约断裂。
    # 再 ∪ **官方核心订阅面**（核心永远随任意组合装载；production_output / market_event 等
    # 由核心模块消费，漏算即误报——2026-09-23 实测）。
    for _r in refs:
        _sf = find_module_file(pkg_dir.get(_r.get('source_package') or '', ''), _r.get('module_id'))
        if _sf:
            _smc = extract_mc(_sf)
            if isinstance(_smc, dict):
                nsub |= set((_smc.get('events') or {}).get('subscribe') or [])
    for _cf in sorted(glob.glob(os.path.join('04_模块库', '*', '*.md'))):
        _cmc = extract_mc(_cf)
        if isinstance(_cmc, dict):
            nsub |= set((_cmc.get('events') or {}).get('subscribe') or [])
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
        # 宿主消费的终端事件：**显式声明**后豁免（未声明即仍判缺失）
        _host = set((smc.get('events') or {}).get('host_consumed') or [])
        miss = pub - nsub - _host
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
      no "check16-A 契约仲裁校验失败——$(head -5 "$NFL_TMP"/nf_check16a.log | tr '\n' ' ')"; errA=1
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
    if "$PY3" - <<'PYEOF' >"$NFL_TMP"/nf_check16b.log 2>&1
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
            # 借阅型源包（组合包等）声明 assets.count: 0：白名单内无内容资产可寻址，
            # 此时须与声明一致——查到 count: 0 则判「不虚标可寻址」，缺声明才判违约。
            py = os.path.join('community', sp, 'protocol.yaml')
            txt = open(py, encoding='utf-8').read() if os.path.isfile(py) else ''
            if 'count: 0' not in txt:
                errs.append('③%s 白名单内但源包 assets 无 .md 且未声明 assets.count: 0，无法验证可寻址行为' % sp)
            elif r.asset_get(sp, 'README') is not None:
                errs.append('③%s 声明 0 自有资产却 asset_get 返回非 None（虚标可寻址）' % sp)
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
      no "check16-B 运行时寻址授权断言失败——$(head -5 "$NFL_TMP"/nf_check16b.log | tr '\n' ' ')"; errB=1
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
    if ( cd desktop && "$PY3" -m unittest tests.test_quality_gate -q >"$NFL_TMP"/nf_check17_unittest.log 2>&1 ); then
      ok '质量治理门 unittest 全绿（test_quality_gate：空装配/缺锚点 fail、资产悬空/层外 warn、合法装配 ok；ok()=fail==0 可信任度不变量）'
    else
      no "质量治理门 unittest 失败——见 "$NFL_TMP"/nf_check17_unittest.log"; err=1
    fi
  else
    wn 'desktop/tests 不在场（跳过 check17）'
  fi
}
check18(){
  echo '== [18/段C] 导出契约门禁（v2.0.0 check18：17_v2.0.0_导出层CCV3方案.md）=='
  local err=0
  if [ -d desktop/tests ]; then
    if ( cd desktop && "$PY3" -m unittest tests.test_ccv3_adapter tests.test_exporter -q >"$NFL_TMP"/nf_check18_unittest.log 2>&1 ); then
      ok '导出契约 unittest 全绿（ccv3_adapter：映射层引擎锚点排除/资产条目/无静默丢弃；exporter：chara spec 锚点/world 条目/PNG tEXt 回读）'
    else
      no "导出契约 unittest 失败——见 "$NFL_TMP"/nf_check18_unittest.log"; err=1
      echo "  ── unittest log 尾部（诊断回显）──"
      tail -40 "$NFL_TMP"/nf_check18_unittest.log 2>/dev/null | sed 's/^/    /'
    fi
  else
    wn 'desktop/tests 不在场（跳过 check18）'
  fi
}
check19(){
  echo '== [19/段C] 导出产物 schema 合规（v2.2.0 A1：export_schema 5 格式 shape 自检）=='
  local err=0
  if [ -d desktop/tests ]; then
    if ( cd desktop && "$PY3" -m unittest tests.test_export_schema -q >"$NFL_TMP"/nf_check19_unittest.log 2>&1 ); then
      ok '导出产物 schema 校验全绿（ccv3/skill/agents/claude/mcp 5 格式 shape 自检：合法产物通过 + 篡改检出）'
    else
      no "导出产物 schema 校验失败——见 "$NFL_TMP"/nf_check19_unittest.log"; err=1
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
    if "$PY3" - <<'PYEOF' >"$NFL_TMP"/nf_check20.log 2>&1
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
      no "check20 文档完整性校验失败——$(head -5 "$NFL_TMP"/nf_check20.log | tr '\n' ' ')"; err=1
    fi
  else
    wn 'python3 不在 PATH（跳过 check20）'
  fi
  if [ "$err" -eq 0 ]; then ok '文档完整性门禁全绿（check20：A3 模块必填项——官方强校验 + 社区机读完备强校验，未完备 WARN 统计）'
  fi
}
check21(){
  echo '== [21/段C] registry 引用图闭合门禁（v2.2.0 A4：impact_check 变更影响面——registry 自洽无悬空引用/无裸号重复）=='
  local err=0
  if [ -d desktop/tests ]; then
    if ( cd desktop && "$PY3" -m unittest tests.test_impact_check -q >"$NFL_TMP"/nf_check21_unittest.log 2>&1 ); then
      ok 'registry 引用图闭合校验全绿（A4 impact_check：隔离构造悬空引用/重复检出 + registry.json 真源自洽 smoke）'
    else
      no "registry 引用图闭合校验失败——见 "$NFL_TMP"/nf_check21_unittest.log"; err=1
    fi
  else
    wn 'desktop/tests 不在场（跳过 check21）'
  fi
  if [ "$err" -eq 0 ]; then ok 'registry 引用图闭合门禁全绿（check21：A4 外部吸收——registry 自洽无悬空 source_package/module_id、无同包裸号重复）'
  fi
}
check22(){
  echo '== [22/段C] 导出物规范体检门禁（v2.4.0 A4：export_schema 硬约束——spec_version 数值/name 规范/description 上限）=='
  local err=0
  if [ -d desktop/tests ]; then
    if ( cd desktop && "$PY3" -m unittest tests.test_export_schema tests.test_ccv3_adapter tests.test_skill_adapter -q >"$NFL_TMP"/nf_check22_unittest.log 2>&1 ); then
      ok '导出物规范体检全绿（A4 export_schema：ccv3 spec_version 3.0-4.0 数值 + skill name a-z0-9-/≤64/匹配父目录 + description ≤1024）'
    else
      no "导出物规范体检失败——见 "$NFL_TMP"/nf_check22_unittest.log"; err=1
    fi
  else
    wn 'desktop/tests 不在场（跳过 check22）'
  fi
  if [ "$err" -eq 0 ]; then ok '导出物规范体检门禁全绿（check22：A4 外部吸收——A1/A2 核查硬约束机读化，spec_version bug 拦截）'
  fi
}
check23(){
  echo '== [23/段C] 资产供应链闭合门禁（40 总纲 v2.7 波A S2：每资产可溯源/可发现/键无孤儿；台账=provenance.json + 文件头双源一致）=='
  local err=0
  if [ -n "$PY3" ]; then
    if "$PY3" - <<'PYEOF' >"$NFL_TMP"/nf_check23.log 2>&1
import os, sys
sys.path.insert(0, os.path.join('desktop', 'src'))
try:
    from core import asset_ledger as al
except Exception as exc:
    print('import 失败：%s' % exc)
    sys.exit(1)
issues, stats = al.verify_root('.')
for i in issues:
    print('[FAIL] %s' % i)
print('供应链统计：台账 %d / 托管资产 %d / 存量未托管 %d / 孤儿头 %d'
      % (stats['ledgers'], stats['assets'], stats['untracked'], stats['orphans']))
sys.exit(1 if issues else 0)
PYEOF
    then
      ok '资产供应链台账闭合（S2：托管资产 可溯源/可发现/键无孤儿）'
    else
      no "资产供应链台账异常——$(tail -2 "$NFL_TMP"/nf_check23.log | tr '\n' ' ')"; err=1
    fi
  else
    wn 'python3 不在 PATH（跳过 check23）'
  fi
  if [ "$err" -eq 0 ]; then ok '资产供应链闭合门禁全绿（check23：40 总纲 v2.7 S2——入库/溯源/版本/淘汰四环机读闭环，键无孤儿）'
  fi
}
check24(){
  echo '== [24/段C] 模块生命周期门禁（40 总纲 v2.8 波B S5：模块 status 位 + deprecate/restore + 引用门禁——deprecated/retired 不得被引用）=='
  local err=0
  if [ -n "$PY3" ]; then
    if "$PY3" - <<'PYEOF' >"$NFL_TMP"/nf_check24.log 2>&1
import os, sys
sys.path.insert(0, os.path.join('desktop', 'src'))
try:
    from core import module_lifecycle as ml
except Exception as exc:
    print('import 失败：%s' % exc)
    sys.exit(1)
issues, stats = ml.verify_modules('.')
for i in issues:
    print('[FAIL] %s' % i)
print('模块生命周期统计：模块 %d / active %d / deprecated %d / retired %d'
      % (stats['modules'], stats['active'], stats['deprecated'], stats['retired']))
sys.exit(1 if issues else 0)
PYEOF
    then
      ok '模块状态扫描与引用门禁通过（S5：全部模块状态位可读，无 deprecated/retired 被引用）'
    else
      no "模块生命周期门禁异常——$(tail -2 "$NFL_TMP"/nf_check24.log | tr '\n' ' ')"; err=1
    fi
  else
    wn 'python3 不在 PATH（跳过 check24）'
  fi
  if [ "$err" -eq 0 ]; then ok '模块生命周期门禁全绿（check24：40 总纲 v2.8 波B S5——status 位 + 引用门禁闭环，流转战例在册）'
  fi
}
check25(){
  echo '== [25/段C] 协议知识签名门禁（41 波C C2：01-36 全量文档签名两遍可复现——知识指纹稳定 = 编译期冲突可发现）=='
  local err=0
  if [ -n "$PY3" ]; then
    if "$PY3" - <<'PYEOF' >"$NFL_TMP"/nf_check25.log 2>&1
import os, sys
sys.path.insert(0, os.path.join('desktop', 'src'))
try:
    from core import knowledge_sig as ks
except Exception as exc:
    print('import 失败：%s' % exc)
    sys.exit(1)
issues, stats = ks.verify_reproducible('.')
for i in issues:
    print('[FAIL] %s' % i)
print('知识签名统计：文档 %d / 可复现 %d'
      % (stats['docs'], stats['reproducible']))
sys.exit(1 if issues else 0)
PYEOF
    then
      ok '协议知识签名全量可复现（C1/C2：01-36 覆盖，两遍逐字节一致）'
    else
      no "协议知识签名门禁异常——$(tail -2 "$NFL_TMP"/nf_check25.log | tr '\n' ' ')"; err=1
    fi
  else
    wn 'python3 不在 PATH（跳过 check25）'
  fi
  if [ "$err" -eq 0 ]; then ok '协议知识签名门禁全绿（check25：41 波C C2——01-36 签名可复现，签名 = 新增可计算摘要）'
  fi
}
check26(){
  echo '== [26/段C] 语义矛盾扫描门禁（41 波C C3：techdoc 链事件契约断链 + 挂载点/类别漂移——补 check15/21 结构自洽之上的语义空白）=='
  local err=0
  if [ -n "$PY3" ]; then
    if "$PY3" - <<'PYEOF' >"$NFL_TMP"/nf_check26.log 2>&1
import os, sys
sys.path.insert(0, os.path.join('desktop', 'src'))
try:
    from core import semantic_conflict as sc
except Exception as exc:
    print('import 失败：%s' % exc)
    sys.exit(1)
issues, stats = sc.scan('.')
for i in issues:
    print('[FAIL] %s' % i)
print('语义扫描统计：模块 %d / 发布事件方 %d / techdoc 链 %d'
      % (stats['modules'], stats['publishers'], stats['techdoc_chain']))
sys.exit(1 if issues else 0)
PYEOF
    then
      ok '语义矛盾扫描通过（C3：techdoc 链事件契约闭合，无挂载点/类别漂移）'
    else
      no "语义矛盾扫描异常——$(tail -2 "$NFL_TMP"/nf_check26.log | tr '\n' ' ')"; err=1
    fi
  else
    wn 'python3 不在 PATH（跳过 check26）'
  fi
  if [ "$err" -eq 0 ]; then ok '语义矛盾扫描门禁全绿（check26：41 波C C3——事件契约断链/漂移为零，编译期矛盾拦截）'
  fi
}
check27(){
  echo '== [27/段C] 架构纯度体检门禁（42 M3：端壳残留/私货可变物/重复标题 grep 断言族 + core raise 消息修复指引审计 + 抽象阶梯归属与越界 R7）=='
  local err=0
  if [ -n "$PY3" ]; then
    if "$PY3" - <<'PYEOF' >"$NFL_TMP"/nf_check27.log 2>&1
import os, sys
sys.path.insert(0, os.path.join('desktop', 'src'))
try:
    from core import purity_scan as ps
except Exception as exc:
    print('import 失败：%s' % exc)
    sys.exit(1)
issues, stats = ps.scan('.')
for i in issues:
    print('[FAIL] %s' % i)
for w in stats.get('import_residue') or []:
    print('WARN: %s' % w)
_ly = stats.get('layers') or {}
print('纯度体检统计：文档 %d / raise 审计 %d / 第三方 import %d / import 残留 %d / 阶梯阶 %d'
      % (stats['docs'], stats['raises'], stats.get('imports', 0),
         len(stats.get('import_residue') or []), _ly.get('tiers', 0)))
sys.exit(1 if issues else 0)
PYEOF
    then
      # import 残留透传（存量挂账不判死，但必须可见并计数）
      while IFS= read -r _purline; do
        case "$_purline" in WARN:*) wn "${_purline#WARN: }" ;; esac
      done < "$NFL_TMP"/nf_check27.log
      ok '架构纯度体检通过（M3：协议层无端壳残留/私货/重复标题 + 阶梯归属互斥/接口子集/依赖向下 + raise 消息修复指引零缺失）'
    else
      while IFS= read -r _purline; do
        case "$_purline" in WARN:*) wn "${_purline#WARN: }" ;; esac
      done < "$NFL_TMP"/nf_check27.log
      no "纯度体检异常——$(tail -2 "$NFL_TMP"/nf_check27.log | tr '\n' ' ')"; err=1
    fi
  else
    wn 'python3 不在 PATH（跳过 check27）'
  fi
  if [ "$err" -eq 0 ]; then ok '架构纯度体检门禁全绿（check27：42 M3——纯度体检制度化，PASS 39→41）'
  fi
}
check28(){
  echo '== [28/段C] 协议层 IDL schema 门禁（43 A1：protocol/schema 五定义在场 + 全量件过 schema——machine_contract/registry 投影/管线声明/协议包/资产台账，任一字段漂移即 FAIL）=='
  local err=0
  if [ -n "$PY3" ]; then
    if "$PY3" - <<'PYEOF' >"$NFL_TMP"/nf_check28.log 2>&1
import os, sys
sys.path.insert(0, os.path.join('desktop', 'src'))
try:
    from core import schema_lint as sl
except Exception as exc:
    print('import 失败：%s' % exc)
    sys.exit(1)
issues, stats = sl.scan('.')
for i in issues:
    print('[FAIL] %s' % i)
print('IDL 扫描统计：schema %(schema_files)d / 模块文档 %(module_docs)d（机读契约 %(contract_covered)d）/ 管线 %(pipelines)d / 协议包 %(protocols)d / 台账条目 %(asset_entries)d'
      % stats)
sys.exit(1 if issues else 0)
PYEOF
    then
      ok '协议层 IDL 全量件过 schema（A1：contract/module/pipeline/protocol/asset 五定义在场 + 零漂移）'
    else
      no "IDL schema 扫描异常——$(tail -2 "$NFL_TMP"/nf_check28.log | tr '\n' ' ')"; err=1
    fi
  else
    wn 'python3 不在 PATH（跳过 check28）'
  fi
  if [ "$err" -eq 0 ]; then ok '协议层 IDL schema 门禁全绿（check28：43 A1——IDL 单一真相落盘机检，PASS 41→43）'
  fi
}

check29(){
  echo '== [29/段C] Conformance 一致性分级门禁（43 A2：01 §1.2 分级——模块机读块/协议包/导出 manifest 声明 ≤ 可证级别，防虚标）=='
  local err=0
  if [ -n "$PY3" ]; then
    if "$PY3" - <<'PYEOF' >"$NFL_TMP"/nf_check29.log 2>&1
import os, sys
sys.path.insert(0, os.path.join('desktop', 'src'))
try:
    from core import conformance_scan as csc
except Exception as exc:
    print('import 失败：%s' % exc)
    sys.exit(1)
issues, stats = csc.scan('.')
for i in issues:
    print('[FAIL] %s' % i)
print('Conformance 统计：机读块 %(modules_mc)d / 协议包 %(packages)d / 导出面 %(export_items)d'
      % stats)
sys.exit(1 if issues else 0)
PYEOF
    then
      ok 'Conformance 声明 ≤ 可证级别（A2：模块机读块/协议包/导出面零虚标）'
    else
      no "Conformance 分级扫描异常——$(tail -2 "$NFL_TMP"/nf_check29.log | tr '\n' ' ')"; err=1
    fi
  else
    wn 'python3 不在 PATH（跳过 check29）'
  fi
  if [ "$err" -eq 0 ]; then ok 'Conformance 一致性分级门禁全绿（check29：43 A2——分级标注齐 + 零虚标，PASS 43→45）'
  fi
}

check30(){
  echo '== [30/段C] 扩展策略 + bump 迁移门禁（43 A3：EXTENSION 判据在场 + 版本字段结构性变更须带 01 §7/02 §9.3 迁移记录）=='
  local err=0
  if [ -n "$PY3" ]; then
    if "$PY3" - <<'PYEOF' >"$NFL_TMP"/nf_check30.log 2>&1
import os, re, subprocess, sys
issues = []
ext = ''
if os.path.isfile('protocol/EXTENSION.md'):
    ext = open('protocol/EXTENSION.md', encoding='utf-8').read()
need = ['字段级新增', '迁移记录', 'bump', 'additive', 'editorial', '结构 bump', '派生三问']
miss = [m for m in need if m not in ext]
if miss:
    issues.append('EXTENSION.md 缺判据词：' + ','.join(miss))
files = ['01_核心协议.md', '02_联动注册表.md', 'desktop/src/core/registry.json']
sdir = 'protocol/schema'
if os.path.isdir(sdir):
    files += [os.path.join(sdir, f) for f in sorted(os.listdir(sdir)) if f.endswith('.json')]
import glob
files += sorted(glob.glob('community/*/protocol.yaml'))
# 版本字段行判据（001 修正，2026-09-20 实测）：此前 tok 定义后从未使用，实际对所有 ± 行跑
# parse_version——任何含 ": <数字>" 的变更行（注释里的 "= 1.0.0"、assets 计数等）都会被判成版本
# bump；且四步迁移记录只认被扫文件自身 diff，JSON（registry.json / schema）无法内嵌注释 =
# 结构上不可满足。修正：① 判据真正收敛到版本字段行；② 记录面 = 该文件 diff ∪ 迁移记录档
# （02 §9 / protocol/EXTENSION.md）的同次提交 diff——记录仍须四步齐备且随本次变更可见。
tok = re.compile(r'\b(?:registry_schema_version|schema_version|version)"?\s*[:=]\s*"?[0-9][0-9.]*"?')
def parse_version(line):
    m = re.search(r'[:=]\s*"?([0-9][0-9.]*)"?', line)
    return m.group(1) if m else None

def _diff(rel):
    r = subprocess.run(['git', 'diff', 'HEAD', '--', rel],
                       capture_output=True, text=True,
                       encoding='utf-8', errors='replace')
    return r.stdout if r.returncode == 0 else ''

record_face = '\n'.join(_diff(p) for p in ('02_联动注册表.md', 'protocol/EXTENSION.md'))
bumps = []
for f in files:
    diff = _diff(f)
    old = {}; new = {}
    for ln in diff.splitlines():
        if ln.startswith('---') or ln.startswith('+++'):
            continue
        if ln[:1] not in ('-', '+'):
            continue
        body = ln[1:]
        if not tok.search(body):
            continue                        # 只认版本字段行（tok 不再是死代码）
        v = parse_version(body)
        if v is None:
            continue
        (old if ln[0] == '-' else new).setdefault(v, 0)
    if old and new and set(old) != set(new):
        bumps.append(f)
        markers = ['现状快照', 'bump 声明', '迁移说明', '校验回读']
        present = [m for m in markers if m in diff + '\n' + record_face]
        if len(present) < 4:
            issues.append('%s: 版本字段结构性变更（bump）但无四步迁移记录（缺：%s）'
                          '——记录可内嵌该文件 diff，或写入 02 §9 / protocol/EXTENSION.md 的同次提交 diff'
                          % (f, ','.join(sorted(set(markers) - set(present)))))
print('扩展策略统计：判据词缺 %d / bump 文件 %d（%s）'
      % (len(miss), len(bumps), '、'.join(bumps) or '无'))
for i in issues:
    print('[FAIL] %s' % i)
sys.exit(1 if issues else 0)
PYEOF
    then
      ok '扩展策略 + bump 迁移门禁通过（A3：EXTENSION 判据在场，版本 bump 均带迁移四步）'
    else
      no "扩展策略/bump 迁移扫描异常——$(tail -2 "$NFL_TMP"/nf_check30.log | tr '\n' ' ')"; err=1
    fi
  else
    wn 'python3 不在 PATH（跳过 check30）'
  fi
  if [ "$err" -eq 0 ]; then ok '扩展策略 + bump 迁移门禁全绿（check30：43 A3——EXTENSION 判据常驻，PASS 45→47）'
  fi
}

check31(){
  echo '== [31/段C] 生成物同仓 golden 门禁（43 A4：schema 定义 → 生成物可复现，仓库内产物 == 实时重算——双源不一致即过期 FAIL）=='
  local err=0
  if [ -n "$PY3" ]; then
    if "$PY3" - <<'PYEOF' >"$NFL_TMP"/nf_check31.log 2>&1
import os, sys
sys.path.insert(0, os.path.join('desktop', 'src'))
try:
    from core import protocol_golden as pg
except Exception as exc:
    print('import 失败：%s' % exc)
    sys.exit(1)
issues, stats = pg.verify_golden('.')
for i in issues:
    print('[FAIL] %s' % i)
print('golden 统计：报告字节 %(report_bytes)d / schema 定义 %(schema_ids)d'
      % stats)
sys.exit(1 if issues else 0)
PYEOF
    then
      ok '生成物同仓 golden 一致（A4：schema↔生成物双源可复现，无过期）'
    else
      no "golden 双源校验异常——$(tail -2 "$NFL_TMP"/nf_check31.log | tr '\n' ' ')"; err=1
    fi
  else
    wn 'python3 不在 PATH（跳过 check31）'
  fi
  if [ "$err" -eq 0 ]; then ok '生成物同仓 golden 门禁全绿（check31：43 A4——生成物双源一致，PASS 47→49）'
  fi
}

check32(){
  echo '== [32/段C] 质量纵深汇总门禁（45 W28：载荷注册表/资产 ledger/指令审计/概念图健康/资产密度·厚度·零引用 + world_model/world_slots）=='
  local err=0
  if [ -n "$PY3" ]; then
    if "$PY3" - <<'PYEOF' >"$NFL_TMP"/nf_check32.log 2>&1
import os, sys
sys.path.insert(0, os.path.join('desktop', 'src'))
try:
    from core import quality_depth_scan as qds
except Exception as exc:
    print('import 失败：%s' % exc)
    sys.exit(1)
issues, stats = qds.scan('.')
for i in issues:
    print('[FAIL] %s' % i)
print('质量纵深统计：%s'
      % ', '.join('%s=%s' % (k, len(v)) for k, v in sorted(stats.items())))
sys.exit(1 if issues else 0)
PYEOF
    then
      ok '质量纵深汇总扫描通过（载荷/ledger/指令/概念图/资产/world_model/world_slots 零缺口）'
    else
      no "质量纵深汇总异常——$(tail -2 "$NFL_TMP"/nf_check32.log | tr '\n' ' ')"; err=1
    fi
  else
    wn 'python3 不在 PATH（跳过 check32）'
  fi
  if [ "$err" -eq 0 ]; then ok '质量纵深汇总门禁全绿（check32：45 W28 + 概念图健康 + world_model/world_slots——纵深统一硬门，PASS 49→51）'
  fi
}

check33(){
  echo '== [33/段C] 新面汇总门禁（MCP dual-era / stdio 帧纪律 / attestation / 基线回归评分 / 机械修复 / 正文 lint / 许可证门 / 遥测 semconv / 编码卫生 / 互操作导出（含入仓一致性）/ 文档命令面 / 决策层面 / 构建回路）=='
  local err=0
  if [ -n "$PY3" ]; then
    if "$PY3" - <<'PYEOF' >"$NFL_TMP"/nf_check33.log 2>&1
import os, sys
sys.path.insert(0, os.path.join('desktop', 'src'))
problems = []
try:
    from core import (attest, regression_score as rs, autofix, lsp,
                      prose_lint, license_gate, telemetry_semconv as ts,
                      mcp_runtime as mcp)
except Exception as exc:
    print('import 失败：%s' % exc)
    sys.exit(1)

# 1 MCP dual-era：modern/legacy 并存 + server/discover + 版本协商错误码
srv = mcp.McpRuntime({'mcp': {'name': 'nf-check33', 'version': '1.0.0',
                              'resources': []}})
disc = srv.handle({'jsonrpc': '2.0', 'id': 1, 'method': 'server/discover',
                   'params': {'_meta': {
                       'io.modelcontextprotocol/protocolVersion': '2026-07-28'}}})
if disc.get('result', {}).get('supportedVersions') != list(mcp.SUPPORTED_VERSIONS):
    problems.append('server/discover 支持版本集异常')
bad = srv.handle({'jsonrpc': '2.0', 'id': 2, 'method': 'ping',
                  'params': {'_meta': {
                      'io.modelcontextprotocol/protocolVersion': '1900-01-01'}}})
if bad.get('error', {}).get('code') != mcp.UNSUPPORTED_PROTOCOL_VERSION:
    problems.append('版本协商错误码不是 -32022')
leg = srv.handle({'jsonrpc': '2.0', 'id': 3, 'method': 'initialize',
                  'params': {'protocolVersion': '2025-11-25'}})
if leg.get('result', {}).get('protocolVersion') != '2025-11-25':
    problems.append('legacy 握手回显异常')

# 2 attestation：digest_only 一致 + 外挂锚 fail-closed
att = attest.build('01_核心协议.md', '.')
a_ok, a_issues, a_level = attest.verify(att, '.')
if not a_ok or a_level != 'digest_only':
    problems.append('attestation digest_only 校验未过：%s' % a_issues)
a_bad = dict(att, signature={'scheme': 'sigstore-keyless', 'bundle': '/nope'})
if attest.verify(a_bad, '.')[0]:
    problems.append('attestation 外挂锚缺验证器却放行（应 fail-closed）')

# 3 基线回归评分：当前 vs 基线（no silent worsening）
cur = rs.evaluate('.')
base_path = 'protocol/score_baseline.json'
if not os.path.exists(base_path):
    problems.append('缺回归评分基线 %s' % base_path)
else:
    cmp_out = rs.compare(cur, rs.load_baseline(base_path))
    if not cmp_out['ok']:
        problems.append('回归评分未过：%s' % cmp_out['verdict'])

# 4 机械修复面：关键/指令档零待修
try:
    from core import doc_hygiene as dh
    targets = [r for r in sorted(set(dh.REQUIRED_DOCS) | set(dh.INSTRUCTION_DOCS))
               if os.path.exists(r)]
except Exception:
    targets = []
pending = []
for p in targets:
    with open(p, encoding='utf-8') as fh:
        if autofix.lint_rules(p, fh.read(), '.'):
            pending.append(p)
if pending:
    problems.append('机械修复面待办 %d 件：%s' % (len(pending), '、'.join(pending[:3])))

# 5 正文 lint 可检出 + LSP 能力在位
if not prose_lint.lint_text('总而言之，我们应该谨慎。\n'):
    problems.append('正文 lint 未检出已知样例')
if not lsp.LspServer().handle({'jsonrpc': '2.0', 'id': 1,
                               'method': 'initialize'})[0]['result']['capabilities']['codeActionProvider']:
    problems.append('LSP codeAction 能力缺失')

# 6 许可证门：零 FAIL
l_issues, l_stats = license_gate.scan('.')
if l_issues:
    problems.append('许可证门 FAIL：%s' % '; '.join(l_issues))

# 7 遥测 semconv：属性名对齐
attrs = ts.attributes_for({'tool': 'nf assemble', 'phase': 'plan'})
if (attrs.get('gen_ai.operation.name') != 'execute_tool'
        or attrs.get('gen_ai.tool.name') != 'nf.assemble'):
    problems.append('遥测 semconv 映射异常')

for p in problems:
    print('[FAIL] %s' % p)
# 8 正文正规性（围栏配平 + mojibake 特征）：WARN 挂账，不判死（存量先可数，再逐波收）
warns = []
try:
    from core import doc_hygiene as dh2
    warns = dh2.text_sanity('.')
except Exception as exc:
    warns = ['WARN: 正文正规性扫描不可用（%s）' % exc]
for w in warns:
    print(w)

# 9 编码卫生（RFC 3629 / RFC 8259 §4 唯一名 / RFC 7493 I-JSON / UAX #15 NFC / UTS #39 同形）：
#   BOM / CRLF / 非 UTF-8 / JSON 重复键 / 标识面隐形·同形字符 + .gitattributes LF 落点
try:
    from core import text_hygiene as th
    _th_issues, _th_stats = th.scan('.')
    for i in _th_issues:
        problems.append('编码卫生：%s' % i)
    _th_line = th.summary(_th_stats)
except Exception as exc:
    problems.append('编码卫生扫描不可用：%s' % exc)
    _th_line = '不可用'

# 10 互操作导出面（OpenAPI 3.1 / AsyncAPI 3.0 / in-toto Statement v1 / SPDX 2.3 / CloudEvents）：
#   纯派生（不新增真源）→ 门禁断言覆盖完整 + 形状合法 + 确定性
try:
    from core import interop_export as ie
    _ie_issues, _ie_stats = ie.verify('.')
    for i in _ie_issues:
        problems.append('互操作导出：%s' % i)
    _ie_line = ie.summary(_ie_stats)
except Exception as exc:
    problems.append('互操作导出面不可用：%s' % exc)
    _ie_line = '不可用'

# 11 JSON-RPC 2.0 §4 结构约束（MCP 面）：params 须结构化 + id 须字符串/数字/null
try:
    for _msg, _want in (
            ({'jsonrpc': '2.0', 'id': 91, 'method': 'ping', 'params': 'raw'},
             mcp.INVALID_REQUEST),
            ({'jsonrpc': '2.0', 'id': 92, 'method': 'ping', 'params': [1]},
             mcp.INVALID_PARAMS),
            ({'jsonrpc': '2.0', 'id': {'x': 1}, 'method': 'ping'},
             mcp.INVALID_REQUEST)):
        _got = srv.handle(_msg).get('error', {}).get('code')
        if _got != _want:
            problems.append('JSON-RPC 2.0 §4：%r 期望错误码 %s，实得 %s'
                            % (_msg.get('params', _msg.get('id')), _want, _got))
except Exception as exc:
    problems.append('JSON-RPC 结构约束检查不可用：%s' % exc)

# 12 文档命令面 ↔ CLI 注册表 / MCP 工具表（只判「当作命令呈现」的片段）
try:
    from core import prose_lint as _pl
    _pl_issues, _pl_stats = _pl.command_face('.')
    for i in _pl_issues:
        problems.append('文档命令面：%s' % i)
    _pl_line = ('文档 %(docs)d 件 / 命令提及 %(commands_checked)d 处 / CLI %(cli_commands)d 条'
                % _pl_stats)
except Exception as exc:
    problems.append('文档命令面检查不可用：%s' % exc)
    _pl_line = '不可用'

# 13 stdio 帧纪律（一条消息一行 + 行边界陷阱转义）+ 资源模板面（RFC 6570 一级子集 + 覆盖）
try:
    _trap = {'jsonrpc': '2.0', 'id': 93,
             'result': {'text': 'a\nb\u2028c\u2029d\u0085e'}}
    _line = mcp.encode_message(_trap)
    if not mcp.is_single_line_message(_line):
        problems.append('stdio 帧纪律：响应不是单行消息')
    if _line.count('\n') != 1:
        problems.append('stdio 帧纪律：消息内出现裸换行（读者会把一条消息劈成两条）')
    for _ch in ('\u2028', '\u2029', '\u0085'):
        if _ch in _line:
            problems.append('stdio 帧纪律：行边界陷阱字符未转义 U+%04X' % ord(_ch))
    if mcp.encode_message(None) is not None:
        problems.append('stdio 帧纪律：通知（无 id）不应写出响应行')
    # 资源模板面（RFC 6570 一级子集）：模板合法 + 真实资源 uri 全被模板覆盖
    _tpls = mcp._repo_resource_templates()
    for _t in _tpls:
        _bad = mcp.uri_template_issue(_t.get('uriTemplate', ''))
        if _bad:
            problems.append('资源模板：%s（%s）' % (_t.get('uriTemplate'), _bad))
    _metas = mcp._repo_resource_metas()
    _uncovered = [x['uri'] for x in _metas
                  if not any(mcp.template_matches(t['uriTemplate'], x['uri']) for t in _tpls)]
    if _uncovered:
        problems.append('资源模板：%d 条真实资源 uri 无模板覆盖（例：%s）'
                        % (len(_uncovered), _uncovered[0]))
except Exception as exc:
    problems.append('stdio 帧纪律检查不可用：%s' % exc)

# 14 互操作导出面入仓一致性（results/interop/*.json == 实时派生，逐字节）
try:
    from core import interop_export as _ie
    _dir = os.path.join('results', 'interop')
    if os.path.isdir(_dir):
        _missing, _drift = [], []
        for _kind in _ie.KINDS:
            _p = os.path.join(_dir, '%s.json' % _kind)
            if not os.path.isfile(_p):
                _missing.append(_kind)
                continue
            with open(_p, 'rb') as _fh:
                if _fh.read() != _ie.render(_kind, '.'):
                    _drift.append(_kind)
        if _missing:
            problems.append('互操作入仓面缺件：%s（修复指引：nf interop --all --out results/interop）'
                            % ','.join(_missing))
        if _drift:
            problems.append('互操作入仓面与实时派生不一致：%s（修复指引：重跑 nf interop --all '
                            '——入仓面是派生投影，不是真源）' % ','.join(_drift))
except Exception as exc:
    problems.append('互操作入仓面检查不可用：%s' % exc)

# 15 决策层面（typed-decision 端口：声明完整 + 适配器诚实标注 + stub 确定性 + fail-closed）
try:
    from core import decision_layer as _dl
    _dl_issues, _dl_stats = _dl.scan('.')
    for i in _dl_issues:
        problems.append('决策层：%s' % i)
    _dl_line = _dl.summary(_dl_stats)
except Exception as exc:
    problems.append('决策层体检不可用：%s' % exc)
    _dl_line = '不可用'

# 16 构建回路（决策模型挑活 → 工单只落内部档案 → worker 落笔 → 门禁验收）
try:
    from core import workloop as _wl
    _wl_issues, _wl_stats = _wl.scan('.')
    for i in _wl_issues:
        problems.append('构建回路：%s' % i)
    _wl_line = _wl.summary(_wl_stats)
except Exception as exc:
    problems.append('构建回路体检不可用：%s' % exc)
    _wl_line = '不可用'

print('新面统计：MCP %s · 评分 %.2f · 机械待办 %d · 许可 WARN %d · 正文正规性 WARN %d'
      % (mcp.PROTOCOL_VERSION, cur['score'], len(pending), len(l_stats['warnings']), len(warns)))
print('新增面：编码卫生 %s · 互操作 %s · 文档命令面 %s' % (_th_line, _ie_line, _pl_line))
print('决策层面：%s' % _dl_line)
print('构建回路：%s' % _wl_line)
sys.exit(1 if problems else 0)
PYEOF
    then
      # 正文正规性 WARN 透传（存量挂账不判死，但必须可见并计数）
      if [ -f "$NFL_TMP"/nf_check33.log ]; then
        while IFS= read -r _txtline; do
          case "$_txtline" in WARN:*) wn "${_txtline#WARN: }" ;; esac
        done < "$NFL_TMP"/nf_check33.log
      fi
      ok '新面扫描通过（MCP dual-era / stdio 帧纪律 / attestation / 评分 / 机械修复 / 正文 lint / 许可证 / 遥测 / 编码卫生 / 互操作导出与入仓面一致 / 文档命令面 / 决策层面 / 构建回路）'
    else
      no "新面扫描异常——$(tail -3 "$NFL_TMP"/nf_check33.log | tr '\n' ' ')"; err=1
    fi
  else
    wn 'python3 不在 PATH（跳过 check33）'
  fi
  if [ "$err" -eq 0 ]; then ok '新面汇总门禁全绿（check33：MCP 版本对齐/stdio 帧纪律/内容外挂签名/回归评分/编辑器面/正文 lint/许可证门/遥测 semconv/编码卫生/互操作导出含入仓/文档命令面/决策层 typed-decision 端口/构建回路）'
  fi
}

check34(){
  echo '== [34/段C] 云端图书馆面门禁（frontmatter 真源 / INDEX·ALIAS 投影一致 / 生命周期 / 四型覆盖 / llms.txt 入口 / 内容分级声明）=='
  local err=0
  if [ -n "$PY3" ]; then
    if "$PY3" - <<'PYEOF' >"$NFL_TMP"/nf_check34.log 2>&1
import os, sys
sys.path.insert(0, os.path.join('desktop', 'src'))
problems = []
try:
    from core import library as nflib
    from core import doc_hygiene as dh
except Exception as exc:
    print('import 失败：%s' % exc)
    sys.exit(1)

# 1 条目 frontmatter（真源）零 FAIL
issues, warns, stats = nflib.verify('.')
for i in issues:
    problems.append('图书馆 frontmatter：%s' % i)

# 2 投影一致（I5：INDEX 生成区 / ALIAS == 实时重算）
for i in nflib.check_projection('.'):
    problems.append('投影一致：%s' % i)

# 3 文档四型覆盖（Diátaxis 借鉴）
for i in dh.kind_coverage('.'):
    problems.append('四型覆盖：%s' % i)

# 4 llms.txt 机器入口清单在场且指向真件
if not os.path.exists('llms.txt'):
    problems.append('缺 llms.txt（agent 机器入口清单）')
else:
    with open('llms.txt', encoding='utf-8') as fh:
        txt = fh.read()
    for anchor in ('# NarrativeForge', 'library/INDEX.md', '01_核心协议.md',
                   '06_Agent执行协议.md', 'agent_组装指令包_v0.2.md'):
        if anchor not in txt:
            problems.append('llms.txt 缺锚点：%s' % anchor)

# 5 检索面可用（正文级命中，非仅文件名）
if not nflib.search('雨天', '.', limit=1):
    problems.append('馆藏检索无命中（倒排索引不可用）')

# 5b 内容分级声明（挂账收口：分级原是真空——登记表无列、条目无字段、须知无词）
try:
    from core import rating_gate as rg
    r_issues, r_stats = rg.scan('.')
    for i in r_issues:
        problems.append('内容分级：%s' % i)
    print('分级统计：%s' % rg.summary(r_stats))
except Exception as exc:
    problems.append('内容分级门不可用：%s' % exc)

# 6 投稿闸门三方一致（2026-09-20 作者裁决收口）：声明件 ⇄ 须知措辞 ⇄ 两个入库机器人引用
try:
    from core import intake as ik
    for i in ik.scan('.')[0]:
        problems.append('投稿闸门：%s' % i)
except Exception as exc:
    problems.append('投稿闸门声明确认不可用：%s' % exc)

# 7 双语入口机读事实一致（2026-09-20 作者裁决收口）：README.md 与 README.en.md 须共享同一组
#   机读锚点（版本 / check 数 / PASS 基线 / 核心协议件 / 机器入口），防「第二语言面腐烂」
#   （外部实证：某清单的双语面无判据 → 中文面只剩英文面 ~54%）。期望值取自 quality_baseline，不写字面量。
try:
    import re as _re
    from core import quality_baseline as _qb
    _want = ('check1-%d' % _qb.EXPECTED_CHECKS, 'PASS=%d' % _qb.EXPECTED_PASS,
             '01_核心协议.md', '06_Agent执行协议.md', 'llms.txt', 'community/')
    for _rel in ('README.md', 'README.en.md'):
        _p = os.path.join('.', _rel)
        if not os.path.isfile(_p):
            problems.append('双语入口：缺 %s（修复指引：中英入口须成对，英文入口覆盖同组机读事实）' % _rel)
            continue
        with open(_p, encoding='utf-8') as _fh:
            _txt = _fh.read()
        for _a in _want:
            if _a not in _txt:
                problems.append('双语入口：%s 缺机读锚点 %s（修复指引：与 README.md 同步机读事实）'
                                % (_rel, _a))
        if not _re.search(r'v\d+\.\d+', _txt):
            problems.append('双语入口：%s 缺版本号（vX.Y）' % _rel)
except Exception as exc:
    problems.append('双语入口锚点检查不可用：%s' % exc)

# 8 双语入口结构对齐（2026-09-20 收口）：H2 章节数一致 + 中文入口引用的 ASCII 名 .md 件在英文入口同样出现
try:
    with open('README.md', encoding='utf-8') as _fh:
        _zh = _fh.read()
    with open('README.en.md', encoding='utf-8') as _fh:
        _en = _fh.read()
    _zh_h2 = len(_re.findall(r'(?m)^## ', _zh))
    _en_h2 = len(_re.findall(r'(?m)^## ', _en))
    if _zh_h2 != _en_h2:
        problems.append('双语入口：章节结构不对齐（README.md H2=%d，README.en.md H2=%d）'
                        '（修复指引：英文面按中文面逐节镜像）' % (_zh_h2, _en_h2))
    _refs = sorted(set(_re.findall(r'[A-Za-z0-9_\-\./]+\.md', _zh)))
    _miss = [r for r in _refs if r not in _en]
    if _miss:
        problems.append('双语入口：README.en.md 缺中文入口引用的件：%s'
                        '（修复指引：英文面须覆盖同组文档入口）' % '、'.join(_miss[:5]))
except Exception as exc:
    problems.append('双语入口结构对齐检查不可用：%s' % exc)

for p in problems:
    print('[FAIL] %s' % p)
dist = dh.kind_distribution('.')
print('图书馆统计：条目 %d · 在役 %d · WARN %d；文档四型：%s'
      % (stats['entries'], stats['active'], len(warns),
         ','.join('%s=%d' % (k, dist[k]) for k in dh.KINDS)))
sys.exit(1 if problems else 0)
PYEOF
    then
      ok '图书馆面扫描通过（frontmatter 真源 / 投影一致 / 四型覆盖 / llms.txt 入口 / 检索可用）'
    else
      no "图书馆面扫描异常——$(tail -3 "$NFL_TMP"/nf_check34.log | tr '\n' ' ')"; err=1
    fi
  else
    wn 'python3 不在 PATH（跳过 check34）'
  fi
  if [ "$err" -eq 0 ]; then ok '云端图书馆面门禁全绿（check34：单一真相源 I5 + 生命周期 + Diátaxis 四型 + llms.txt 机器入口）'
  fi
}

check35(){
  echo '== [35/段C] 深化面门禁（管线抽象执行 / 馆藏回执单根 / 模块边界冻结 / 内容绑定批准 / 一致性报告工件 / 无效语料）=='
  local err=0
  if [ -n "$PY3" ]; then
    if "$PY3" - <<'PYEOF' >"$NFL_TMP"/nf_check35.log 2>&1
import os, sys
sys.path.insert(0, os.path.join('desktop', 'src'))
problems = []
try:
    from core import pipelinerun as pr
    from core import receipts, module_signature as ms, approval
    from core import conformance_report as cr
except Exception as exc:
    print('import 失败：%s' % exc)
    sys.exit(1)

# 1 管线抽象执行：全仓零 hard 缺陷（advisory 不判死）
d_issues, d_tot = pr.sweep('.')
for i in d_issues:
    problems.append('管线 dry-run：%s' % i)

# 2 馆藏回执：逐条折叠到根 + 根与实时重算一致
if not os.path.exists(receipts.RECEIPTS_REL):
    problems.append('缺馆藏回执 %s（修复指引：nf library receipts --write）'
                    % receipts.RECEIPTS_REL)
else:
    for i in receipts.verify(receipts.load('.'), '.')[0]:
        problems.append('馆藏回执：%s' % i)

# 3 模块边界冻结：零漂移
for i in ms.verify('.')[0]:
    problems.append('模块边界：%s' % i)

# 4 内容绑定批准：零失效
for i in approval.verify('.')[0]:
    problems.append('批准记录：%s' % i)

# 5 一致性报告工件：在盘报告 == 实时重算，且 verdict 达标
r_issues, r_stats = cr.verify_committed('.')
for i in r_issues:
    problems.append('一致性报告：%s' % i)
if r_stats and r_stats.get('verdict') != 'conformant':
    problems.append('一致性报告 verdict 非 conformant：%s' % r_stats.get('verdict'))

# 6 无效语料 + golden 修复对在场
for rel in ('desktop/tests/fixtures/fixes/fix_cases.json',
            'desktop/tests/test_invalid_corpus.py'):
    if not os.path.exists(rel):
        problems.append('缺语料件：%s' % rel)

# 7 协议层回执（覆盖面从馆藏扩到 01-07 / schema / baseline）
import json as _json
if not os.path.exists(receipts.PROTOCOL_RECEIPTS_REL):
    problems.append('缺协议层回执 %s（修复指引：nf receipts --write）'
                    % receipts.PROTOCOL_RECEIPTS_REL)
else:
    with open(receipts.PROTOCOL_RECEIPTS_REL, encoding='utf-8') as fh:
        for i in receipts.verify_scope(_json.load(fh), '.')[0]:
            problems.append('协议回执：%s' % i)

# 8 advisory 分类台账与实时重算一致
for i in pr.verify_advisory('.')[0]:
    problems.append('advisory 台账：%s' % i)

for p in problems:
    print('[FAIL] %s' % p)
print('深化面统计：管线 %d 条（advisory %d）· 回执 %d 条 · 报告 %s'
      % (d_tot['pipelines'], d_tot['notes'],
         (r_stats or {}).get('contracts', 0), (r_stats or {}).get('verdict', '-')))
sys.exit(1 if problems else 0)
PYEOF
    then
      ok '深化面扫描通过（dry-run / 回执单根 / 边界冻结 / 批准记录 / 一致性报告 / 语料）'
    else
      no "深化面扫描异常——$(tail -3 "$NFL_TMP"/nf_check35.log | tr '\n' ' ')"; err=1
    fi
  else
    wn 'python3 不在 PATH（跳过 check35）'
  fi
  if [ "$err" -eq 0 ]; then ok '深化面门禁全绿（check35：抽象执行 GraphSpec + MMR 回执 + 边界签名 + 内容绑定批准 + 报告工件）'
  fi
}

check36(){
  echo '== [36/段C] 治理面门禁（一致性声明 / RFC 版本史 / 指令档机器面路由 / 实践包 / 跑分台 / 端点契约）=='
  local err=0
  if [ -n "$PY3" ]; then
    if "$PY3" - <<'PYEOF' >"$NFL_TMP"/nf_check36.log 2>&1
import json, os, sys
sys.path.insert(0, os.path.join('desktop', 'src'))
problems = []
try:
    from core import (conformance_decl as cd, driver, endpoint,
                      patterns as pt, rfc as rf, bench)
except Exception as exc:
    print('import 失败：%s' % exc)
    sys.exit(1)

# 1 一致性声明（scope 白名单 + 显式排除 + 版本与真源一致 + scope∩排除=∅）
for i in cd.scan('.')[0]:
    problems.append('一致性声明：%s' % i)

# 2 协议件 RFC 头（编号唯一 / Category·Status 词表 / Date=最后更新 / 链可解析）
for i in rf.scan('.')[0]:
    problems.append('RFC 头：%s' % i)

# 3 指令档机器面路由（工具名与运行时一致 / fallback 在场 / 文档 override 块齐）
for i in driver.scan('.')[0]:
    problems.append('driver：%s' % i)

# 4 实践包（格式 + 适用面/证据可证 + INDEX 投影一致）
for i in pt.scan('.')[0] + pt.check_projection('.'):
    problems.append('实践包：%s' % i)

# 5 跑分台：用例在场且对真实产物的评分**确定可复现**（同产物同分）
cases = bench.cases('.')
if len(cases) < 2:
    problems.append('跑分用例不足（需 ≥2 个 case.json，现有 %d）' % len(cases))
for c in cases:
    d = bench.load_case(c)
    rel = c.relative_to('.').as_posix()
    r1 = bench.evaluate('.', rel, d['default_artifact'], model='check')
    r2 = bench.evaluate('.', rel, d['default_artifact'], model='check')
    if r1['scores'] != r2['scores'] or r1['total'] != r2['total']:
        problems.append('跑分不确定（同一产物两次评分不同）：%s' % rel)
    if r1['total'] < r1['floor']:
        problems.append('跑分低于用例下限：%s（%.2f < %.0f）'
                        % (rel, r1['total'], r1['floor']))

# 6 端点契约：每个端点映射到现存能力（不指向空气）
for i in endpoint.scan('.')[0]:
    problems.append('端点契约：%s' % i)

for p in problems:
    print('[FAIL] %s' % p)
print('治理面统计：声明 %s · RFC %s 件 · driver 工作流 %s · 实践包 %s 条 · 跑分用例 %s · 端点 %s'
      % (cd.scan('.')[1].get('versions'),
         rf.scan('.')[2].get('docs'),
         driver.scan('.')[2].get('workflows'),
         len(pt.entries('.')), len(cases),
         endpoint.scan('.')[2].get('endpoints')))
sys.exit(1 if problems else 0)
PYEOF
    then
      ok '治理面扫描通过（声明 / RFC / driver / 实践包 / 跑分 / 端点）'
    else
      no "治理面扫描异常——$(tail -3 "$NFL_TMP"/nf_check36.log | tr '\n' ' ')"; err=1
    fi
  else
    wn 'python3 不在 PATH（跳过 check36）'
  fi
  if [ "$err" -eq 0 ]; then ok '治理面门禁全绿（check36：一致性声明 + RFC 版本史 + 指令档路由 + 实践包 + 跑分台 + 端点契约）'
  fi
}

check37(){
  echo '== [37/段C] 知识层门禁（双源知识：权威分层 / 查询有序 / 时效 / 消化可追溯 / 认知裁剪）=='
  local err=0
  if [ -n "$PY3" ]; then
    if "$PY3" scripts/check37_knowledge.py >"$NFL_TMP"/nf_check37.log 2>&1
    then
      ok '知识层扫描通过（权威分层 / 查询有序 / 时效 / 溯源 / 巡检）'
    else
      no "知识层扫描异常——$(tail -3 "$NFL_TMP"/nf_check37.log | tr '\n' ' ')"; err=1
    fi
  else
    wn 'python3 不在 PATH（跳过 check37）'
  fi
  if [ "$err" -eq 0 ]; then ok '知识层门禁全绿（check37：双源知识——声明 + 顺序 + 溯源 + 巡检，PASS 59→61）'
  fi
}

check38(){
  echo '== [38/段C] 出口自动化门禁（自述数字 / 他证通道 / GEO 出口 / FDE 样例）=='
  local err=0 sub mod label
  if [ -n "$PY3" ]; then
    for sub in 'repo_stats:自述数字' 'interop_thirdparty:他证通道' 'geo_export:GEO 出口' 'fde_sample:FDE 样例'; do
      mod=${sub%%:*}; label=${sub##*:}
      if "$PY3" - "$mod" "$label" >"$NFL_TMP"/nf_check38_$mod.log 2>&1 <<'PYEOF'
import importlib.util, os, sys
sys.path.insert(0, os.path.join('desktop', 'src'))
mod, label = sys.argv[1], sys.argv[2]
if mod == 'repo_stats':
    from core import repo_stats as m
    issues, stats = m.check('.')
else:
    rel = {'interop_thirdparty': 'scripts/interop_thirdparty_kit.py',
           'geo_export': 'scripts/geo_export.py',
           'fde_sample': 'scripts/fde_sample_run.py'}[mod]
    spec = importlib.util.spec_from_file_location(mod, rel)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    issues, stats = m.check('.')
for i in issues:
    print('[FAIL] %s' % i)
print('%s 子扫描：%s' % (label, '零缺口' if not issues else 'FAIL %d' % len(issues)))
sys.exit(1 if issues else 0)
PYEOF
      then
        ok "出口面全绿：$label（check38 子扫描）"
      else
        no "$label 出口面不一致——见 nf_check38_$mod.log：$(tail -2 "$NFL_TMP"/nf_check38_$mod.log 2>/dev/null | tr '\n' ' ')"
        err=1
      fi
    done
  else
    wn 'python3 不在 PATH（跳过 check38 出口自动化门禁）'
  fi
  if [ "$err" -eq 0 ]; then ok '出口自动化门禁全绿（check38：自述数字 + 他证通道 + GEO 出口 + FDE 样例 四子扫描）'
  fi
}

check39(){
  echo '== [39/段C] 终端与端壳残留门禁（端壳退役已成事实 + 终端入口在场 + 菜单无死命令 + 命令面全策展可达）=='
  local err=0
  if [ -n "$PY3" ]; then
    if "$PY3" - <<'PYEOF' >"$NFL_TMP"/nf_check39.log 2>&1
import importlib.util, io, json, os, sys
from contextlib import redirect_stdout
sys.path.insert(0, os.path.join('desktop', 'src'))
from core import terminal as term

problems, notes = [], []

# ---- ① 端壳残留：GUI 端壳源码/入口/打包线不得再出现在树（字节码缓存不算源件）----
shell_leftovers = [
    os.path.join('desktop', 'main.py'),
    os.path.join('desktop', 'src', '__main__.py'),
    os.path.join('desktop', 'packaging'),
    os.path.join('.github', 'workflows', 'build-desktop.yml'),
    os.path.join('.github', 'workflows', 'build-android.yml'),
    os.path.join('scripts', 'smoke_zone_g_market.py'),
    os.path.join('scripts', 'check_ui_core_links.py'),
]
for rel in shell_leftovers:
    if os.path.exists(rel):
        problems.append('端壳残留在场：%s（修复指引：按 L3 退役裁决删除；GUI 源码已于 '
                        '2026-09-09 移出，本项即防回潮）' % rel)
for dirpath, dirnames, filenames in os.walk('.'):
    dirnames[:] = [d for d in dirnames
                   if d not in ('.git', '.rivet', '__pycache__', '.ruff_cache',
                                '.mypy_cache', 'node_modules')]
    for name in filenames:
        if not name.endswith('.py'):
            continue
        if name.startswith('zone_') or name.startswith('test_zone_') or \
                name == 'main_window.py' or name == 'smoke_gui.py':
            problems.append('端壳残留源件：%s（修复指引：端壳能力一律落 CLI，'
                            '不得在树内保留 GUI 模块）' % os.path.join(dirpath, name))
    rel_dir = os.path.relpath(dirpath, '.').replace('\\', '/')
    if rel_dir.endswith('desktop/src/ui'):
        # 只认「有真件」的残余目录：`__pycache__` 是字节码缓存（可再生、非源件），
        # 已在上层剪掉——空壳目录不判死，但任何源码/资源残留即 FAIL。
        if any(n not in ('__pycache__',) for n in dirnames) or filenames:
            problems.append('端壳残留目录：desktop/src/ui 含源件或资源'
                            '（修复指引：端壳能力一律落 CLI，该目录不得有真件）')

# ---- ② 终端面在场 + 确定性 + 机器面 ----
if not os.path.isfile(os.path.join('desktop', 'src', 'core', 'terminal.py')):
    problems.append('终端核心缺失：desktop/src/core/terminal.py（修复指引：'
                    '端壳退役后的人机入口须在场，见 docs/terminal.md）')
if not os.path.isfile('scripts/nf'):
    problems.append('终端启动器缺失：scripts/nf（修复指引：提供 POSIX 启动器，无参数进终端）')
if not os.path.isfile(os.path.join('scripts', 'nf.cmd')):
    problems.append('终端启动器缺失：scripts/nf.cmd（修复指引：提供 Windows 启动器）')

# ---- ③ 终端自检（**单源判据**：与 `nf shell --verify` 调用同一个 terminal.self_check）----
# 覆盖：索引须派生自 argparse 面且含二级 / 能力地图须恰好分区全部顶层命令（不缺不重不虚）/
#       菜单示例须指向真实命令 / 菜单键连续。
spec = importlib.util.spec_from_file_location('nfcli', os.path.join('scripts', 'nf.py'))
nf = importlib.util.module_from_spec(spec)
spec.loader.exec_module(nf)
tree = nf._collect_cli_tree()
cmds, flags = set(tree['commands']), set(tree['root_flags'])
for sub in ('shell', 'terminal'):
    if sub not in cmds:
        problems.append('终端子命令缺失：nf %s（修复指引：在 scripts/nf.py 注册 shell）' % sub)
index = nf._shell_command_index()
self_issues, self_stats = term.self_check(index, cmds, flags)
problems += self_issues

# ---- ③b 运行时面：检索 / 列出 / 地图 / 拼错建议 / 自检命令本身都可用 ----
index_paths = {str(e.get('path')) for e in index}
index_tops = {p.split(' ')[0] for p in index_paths}
miss_search = [c for c in sorted(cmds)
               if not term.search(index, c, limit=1)
               or str(term.search(index, c, limit=1)[0][1].get('path')) != c]
if miss_search:
    problems.append('命令检索不到自身：%s（修复指引：核对 terminal.search 打分档）'
                    % '、'.join(miss_search[:5]))
if 'stats' not in term.did_you_mean('statss', sorted(index_tops)):
    problems.append('拼错建议失效：statss 未指向 stats（修复指引：核对 terminal.did_you_mean）')
buf = io.StringIO()
with redirect_stdout(buf):
    s_code = nf.main(['shell', '--search', 'doctor', '--no-banner'])
if s_code != 0 or 'doctor' not in buf.getvalue():
    problems.append('命令检索面失效：nf shell --search doctor（修复指引：核对 render_search）')
for _argv, _need in ((['shell', '--map', '--no-banner'], '能力地图'),
                     (['shell', '--verify', '--no-banner'], '通过')):
    buf = io.StringIO()
    with redirect_stdout(buf):
        _code = nf.main(_argv)
    if _code != 0 or _need not in buf.getvalue():
        problems.append('终端自检/地图面失效：nf %s（修复指引：核对 --map / --verify 接线）'
                        % ' '.join(_argv[:2]))
buf = io.StringIO()
with redirect_stdout(buf):
    c_code = nf.main(['shell', '--commands', '--no-banner'])
if c_code != 0 or 'nf doctor' not in buf.getvalue():
    problems.append('命令面列出失效：nf shell --commands（修复指引：核对 render_commands）')

# ---- ④ 确定性 + JSON 机器面（同输入两遍逐字节一致）----
captured = []
for _ in range(2):
    buf = io.StringIO()
    with redirect_stdout(buf):
        code = nf.main(['shell', '--exec', '/menu', '--no-banner'])
    captured.append(buf.getvalue())
    if code != 0:
        problems.append('终端非交互模式退出码异常：%s（修复指引：nf shell --exec 只读命令须退出 0）'
                        % code)
if captured[0] != captured[1]:
    problems.append('终端输出不确定（两遍不一致；修复指引：去掉横幅/时间戳等可变面）')
for item in term.zone_table():
    if item['title'] not in captured[0]:
        problems.append('菜单漏出能力区：%s（修复指引：menu() 须逐区列出）' % item['title'])
buf = io.StringIO()
with redirect_stdout(buf):
    nf.main(['shell', '--exec', '/zone 0', '--no-banner', '--json'])
try:
    payload = json.loads(buf.getvalue())
    if payload.get('kind') != 'nf-shell' or payload['records'][0]['kind'] != 'zone':
        problems.append('终端 JSON 机器面形状异常（修复指引：--json 输出 nf-shell 逐条记录）')
except Exception as exc:
    problems.append('终端 JSON 机器面不可解析：%s（修复指引：--json 须输出合法 JSON）' % exc)

for p in problems:
    print('[FAIL] %s' % p)
print('端壳残留项：%d · 菜单区：%d · 菜单示例：%d'
      % (len(shell_leftovers), len(term.zone_table()),
         sum(len(z['examples']) for z in term.zone_table())))
sys.exit(1 if problems else 0)
PYEOF
    then
      ok '端壳残留零在场 + 终端入口在场 + 命令面全策展可达（check39 子扫描：源件/入口/打包线 + terminal.self_check 单源判据 + 检索/地图/自检运行时面）'
    else
      no "终端与端壳残留门禁异常——$(tail -3 "$NFL_TMP"/nf_check39.log 2>/dev/null | tr '\n' ' ')"; err=1
    fi
  else
    wn 'python3 不在 PATH（跳过 check39 终端与端壳残留门禁）'
  fi
  if [ "$err" -eq 0 ]; then ok '终端与端壳残留门禁全绿（check39：端壳零回潮 + 终端三件在场 + 菜单无死命令 + 命令面全策展可达 + 输出确定）'
  fi
}

# ================= 主执行体（三段式） =================
echo '=================================================='
echo ' NarrativeForge 三段式验收门禁  v2.29（对齐 07 §7 + 08 T5 A5 资产对账 + 09 v0.6.0 check12 代码层 + check13 迁移完整性 + 10 v0.7.0 check14 社区协议登记门禁 + 11 v0.8.0 check15 组合引用门禁 + 12 v1.0.0 check16 契约仲裁门禁 + 16 v1.4.0 check17 质量治理门 + 17 v2.0.0 check18 导出契约门 + 33 v2.2.0 check19-21 外部吸收首波 + 35 v2.4.0 check22 规范体检 + 终端线 check39 端壳零回潮/终端入口；分层治理 23 方案：L3 端壳退役移出，门禁默认锁 L0-L2）'
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
echo '—— 段 C：代码层门禁（L2 core：check12-check36 无条件执行；android 相关已随 L3 冻结移出）——'
check12
check13
check14
check15
check16
check17
check18
check19
check20
check21
check22
check23
check24
check25
check26
check27
check28
check29
check30
check31
check32
check33
check34
check35
check36
check37
check38
check39
echo '=================================================='
echo "结果统计: PASS=$PASS  WARN=$WARN  FAIL=$FAIL"
if [ "$FAIL" -gt 0 ]; then
  echo '>>> 存在 FAIL = 协议事故：请回滚本次修改，修正后重新运行验收 <<<'
  exit 1
else
  echo '>>> 全部通过（WARN 仅提示非致命），变更可提交 <<<'
  exit 0
fi
