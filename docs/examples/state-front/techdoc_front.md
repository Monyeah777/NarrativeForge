## 状态块（条件先行摘要）

> 本块由产物**确定性提取**（非模型生成）——它是该产物的「状态文本代理」，供重读时先对齐状态。

| 项 | 值 |
|---|---|
| 模块/挂载编号 | M00、M01、M02、M03、M04、M06、M07、M08、M09、M10、M11、M12、M13、M14、M15、M16、M17、M18、M19、M20、M22、M23、M24、M40、M41、M43、M50、M55、M65、M80、M90、M93、M97、M98、P00、P01、P02、P03、P06、P10、P20、P30、P40、P50、P60、P70、P80、P90 |
| NF 编号 | NF-1、NF-TECHDOC-Monyeah777-1 |
| 二级标题数 | 89 |
| 要点行数 | 92 |
| 原文 sha256 | `904856c28ee4ac04` |

**关键设置点（原文摘录，非改写）**：

- 04_模块库（官方核心 13 件）
- community/技术文档域包（自带 2 件 + P06 管线）
- 技术文档
- 自包含
- 装配样本
- **需求原话**：「组装一个技术文档生成流程的完整版：要有术语管理与修订记录，能直接交给任意 AI 装载开跑」
- **选件决策**（`nf assemble` 装配计划实测输出）：
- 匹配预设：技术文档域包 → 管线 **P06**（`community/技术文档域包/pipelines/P06_技术文档题材装配流管线.md`）

---

---
id: NF-TECHDOC-Monyeah777-1
type: 技术文档装配（自包含完整版）
title: 技术文档装配流 P06 · 自包含完整版
description: 技术文档域包 P06 装配的自包含完整版——15 件模块正文与管线声明全文内嵌、零资产、无需仓库路径即可装载开跑
author: Monyeah777
license: MIT
generated: 2026-09-15
verified: 2026-09-15
status: active
stale_after: 2027-03-15
sources:
  - 04_模块库（官方核心 13 件）
  - community/技术文档域包（自带 2 件 + P06 管线）
tags:
  - 技术文档
  - 自包含
  - 装配样本
---

> 📚 NF 云端图书馆条目 **NF-TECHDOC-Monyeah777-1** · 入库 2026-09-15 · 投稿人：Monyeah777 · 类型：装配样本（自包含）
> 许可：MIT（登记表同列同值）

> 档位：**全文内嵌式（自包含）**——与 `NF-1`、「西幻生存流 P03 样本」的**引用式**相对。
> 引用式档位的正文以仓库路径与 `assets/` 为准，离线须另粘贴；本件不引用任何仓库路径：
> 15 件模块正文与 P06 管线声明全部内嵌，任何 AI 单文件即可装载开跑。

---

## 0. 装配记录

- **需求原话**：「组装一个技术文档生成流程的完整版：要有术语管理与修订记录，能直接交给任意 AI 装载开跑」
- **选件决策**（`nf assemble` 装配计划实测输出）：
  - 匹配预设：技术文档域包 → 管线 **P06**（`community/技术文档域包/pipelines/P06_技术文档题材装配流管线.md`）
  - 取件模块：**M97 术语管理**（P40 行为决策）、**M98 修订记录**（P60 长期演变）
  - 装配允许集：官方核心 + 包模块 = **44**；本件实际内嵌 **15** 件（核心 13 + 自带 2）
  - 资产：**0 文件**（技术文档域包为机制增强包，无题材资产，同通用核心基础包先例）
  - references：**0**（零跨包引用，`core_only: true`）
- **档位声明**：全文内嵌式。本件与引用式样本的差异不在内容，在**可离线自足性**——
  引用式需要接收方另取仓库文件，本件不需要。
- **缺口声明（如实）**：
  - ① 本件内嵌的是**模块层**正文与管线声明；`01_核心协议`/`02_联动注册表`/`06_Agent执行协议` 三份协议件不内嵌——
    它们是全库共用的上位规范，非本装配的专属件（引用式样本同样如此）。
  - ② 内嵌正文为 2026-09-15 仓库快照的**逐字节复制**，不含改写；上游模块若变更，本件须重新生成。
  - ③ 本件未挂签名锚（`anchor_*` 字段缺省），如需第三方独立验真，另走 `nf library attest`。

## 1. 文档域速览

- **定位**：技术文档装配流（非叙事题材）——把「术语一致性 + 修订可追溯」这两条技术文档的工程纪律，做成可装载的产线。
- **主轴**：M90 结构骨架（P00 位装载 DocState）→ **M97 术语管理**（P40：登记/补定义/冲突检测）→ **M98 修订记录**（P60：版本递增/变更日志/回溯）→ M80 质检渲染（P80）。
- **产物形态**：技术文档装配产物，供下游 agents / mcp / skill 适配器消费。
- **输出门**：M80 是唯一渲染出口（gate 唯一出口，与叙事流同规矩）。
- **域中立证据**：本件与校园情感、西幻生存两类叙事包**共用同一套官方核心**，仅替换题材层的 2 件与 1 条管线——这是「机制不绑域」的可装载证据。

## 2. 管线（P06 · 技术文档题材装配流 · techdoc 九层回卷）

挂载投影（源自 P06 layers，逐层列出）：

| 层 | 挂载（default） | 职责 | 归属 |
|---|---|---|---|
| P00 数据基座 | M00、M90 | 数据槽装载 + 技术文档结构骨架（DocState 产） | 官方核心 |
| P40 行为决策 | **M97** | 术语管理：DocState.terms 登记/补定义/冲突检测 | 本包 |
| P60 长期演变 | **M98** | 修订记录：DocState.revision 版本递增/变更日志/回溯 | 本包 |
| P80 输出呈现 | M80 | 质检渲染（gate 唯一出口） | 官方核心 |
| 全局调度 | M50 | 主循环：回合 begin → 逐层推进 → end 一致性校验 → 回卷 | 官方核心 |

管线声明原文（内嵌）：

```markdown
# 绠＄嚎 P06 路 鎶€鏈枃妗ｉ鏉愯閰嶆祦
> 绀惧尯鐗堛€屾妧鏈枃妗ｅ煙鍖呫€嶄娇鐢ㄧ殑绠＄嚎锛坴2.1.0-C-b 鎴樹緥钀界洏锛夈€備互銆岄潪鍙欎簨棰樻潗锛氭妧鏈枃妗ｈ閰嶃€嶄负娴佷富杞达細瀹樻柟 M90 鎶€鏈枃妗ｇ粨鏋勶紙P90 閾惧畼鏂规ā鍧楋紝core_modules 渚濊禆寮曠敤涓嶆惉绉伙級鍦?P00-P60 浣嶄骇 DocState 楠ㄦ灦/姝ｆ枃/鍐崇瓥/瑁呴厤锛涙湰鍖呰嚜甯?M97 鏈绠＄悊鎸?P40 浣嶅仛鏈鍩熸繁鍖栵紙DocState.terms 缁熶竴鎬э級锛孧98 淇璁板綍鎸?P60 浣嶅仛淇鍩熻拷韪紙DocState.revision 鐗堟湰/鍥炴函锛夛紱P80 杈撳嚭鍛堢幇浠嶇敱瀹樻柟鏍稿績 M80 璐ㄦ娓叉煋锛坓ate 鍞竴鍑哄彛锛屽悓鍙欎簨娴侊級銆?> 瀹炰緥澹版槑锛氭湰绠＄嚎鏄€氱敤楠ㄦ灦 **P00**锛?3_绠＄嚎搴?P00_閫氱敤鏂囨。鐢熸垚绠＄嚎.md锛夊湪**鎶€鏈枃妗Ｂ烽鏉愯閰?*鐨勫疄渚嬧€斺€斾節灞備綅鍚嶆部鐢ㄩ鏋讹紱鏈寘 P40/P60 涓ら┗鐣欒嚜甯︽ā鍧楋紙M97/M98锛夛紝M90 瀹樻柟妯″潡缁忎緷璧栧紩鐢ㄩ殢娴佸崗浣滐紙M90 鏈綋涓嶅鍒惰繘鍖咃紝I5 鍗曚竴鐪熺浉婧愶級銆?> **鍏佽缂栧彿娈靛浐鍖栵紙R2锛寁2.1.0-C-b锛?*锛氭湰鍖?`allowed_modules` 浠呴檺瀹樻柟鏍稿績锛圡00 / M80 / M90 绛?core_modules 13 浠跺惈 M90锛変笌鏈寘绀惧尯娈碉紙M97 / M98锛宮odules/ 鍦ㄥ唽 2 浠讹級銆俽eferences=[] 闆惰法鍖呴浂鍊熼槄銆?> **鎸傝浇灞傝閬匡紙check15 鈶級**锛氬畼鏂?P00 楠ㄦ灦涔濆眰 default 鍧囩┖锛涙棦鏈夌ぞ鍖哄寘鍚屽眰 default锛堟牎鍥?P40=[鎯呮劅:M22,M40...]銆丳60=[M40,M65]锛涜タ骞?P40=[M04,M11]銆丳60=[鐢熷瓨:M10...]锛変笌鏈寘 P40=[M97]銆丳60=[M98] 鏃犱氦闆嗏€斺€擬97/M98 鏂扮紪鍙峰敮涓€锛岀嫭绔嬭杞戒笉鍐茬獊锛?2 鏂规鍙嶈瘉瀹炶瘉锛夈€?```yaml
Pipeline:
  id: P06
  name: 鎶€鏈枃妗ｉ鏉愯閰嶆祦
  structure:
    type: techdoc
    flow:
      - from: P00
        to: P10
      - from: P10
        to: P20
      - from: P20
        to: P30
      - from: P30
        to: P40
      - from: P40
        to: P50
      - from: P50
        to: P60
      - from: P60
        to: P70
      - from: P70
        to: P80
      - from: P80
        to: P00
        condition: 涓诲惊鐜洖鍗凤紙M50 璋冨害涓嬩竴鍥炲悎锛涘畼鏂规牳蹇冭妭鎷嶅悓鎷嶆帹杩涳級
  layers:
    - id: P00
      name: 鏁版嵁鍩哄骇
      description: 瀹樻柟 M00 鏁版嵁妲斤紙core 渚濊禆锛涙妧鏈枃妗?DocState 涓昏浇浣擄紝M90 缁撴瀯楠ㄦ灦鍦ㄦ瑁呰浇鈥斺€擬00/M90 鏈綋椹诲畼鏂逛綅涓嶆惉绉伙級
      optional: false
      default_modules: []
      allowed_modules: [M00, M90]
    - id: P40
      name: 琛屼负鍐崇瓥
      description: 鏈鍐崇瓥灞傦細鑷甫 M97 鏈绠＄悊瀹?DocState.terms锛堢櫥璁?琛ュ畾涔?鍐茬獊妫€娴嬶紝publish term_synced锛?      optional: false
      default_modules: [M97]
      allowed_modules: [M97]
    - id: P60
      name: 闀挎湡婕斿彉
      description: 淇灞傦細鑷甫 M98 淇璁板綍缁存姢 DocState.revision锛堢増鏈€掑/鍙樻洿鏃ュ織/鍥炴函锛宲ublish revision_recorded锛?      optional: false
      default_modules: [M98]
      allowed_modules: [M98]
    - id: P80
      name: 杈撳嚭鍛堢幇
      description: 瀹樻柟鏍稿績 M80 杈撳嚭鐢熸垚鍣紙gate 鍞竴鍑哄彛锛涜 term_synced/revision_recorded 鍚庤川妫€娓叉煋锛?      optional: false
      default_modules: []
      allowed_modules: [M80]
```
```

## 3. 注册表投影

本次装配的执行顺序（可由 P06 layers 与官方 02 执行顺序推出，不硬编码于产物内）：

| 步 | 层 | 模块 | 动作 | 写入 |
|---|---|---|---|---|
| 1 | P00 | M00 | 装载数据槽结构（DocState 主载体） | 初始数据槽 |
| 2 | P00 | M90 | 装载技术文档结构骨架（章节层级/文档类型） | DocState 骨架 |
| 3 | 全局 | M50 | 回合 begin：打快照 | round.begin 快照 |
| 4 | P40 | M97 | 术语登记/补定义/冲突检测 → 发布 `term_synced` | DocState.terms |
| 5 | P60 | M98 | 版本递增/变更日志/回溯 → 发布 `revision_recorded` | DocState.revision |
| 6 | P80 | M80 | 读 `term_synced` / `revision_recorded` 后质检渲染 | 玩家可见文档 |
| 7 | 全局 | M50 | 回合 end：一致性校验 → 回卷下一回合 | 存档 |

> 说明：上表为本次装配的**投影**，供接收方装载时对照；执行顺序的真源仍是接收方所装载的注册表（02 不变式 I5：顺序一律读注册表，禁止硬编码）。

## 4. 模块库（15 件 · 正文全文内嵌）

> 下列 15 段为**逐字节内嵌的模块正文原文**（置于代码围栏内，便于机器验收跳过扫描）。
> 每段前的粗体行标明：模块号 / 名称 / 归属 / 源文件路径（路径仅作溯源标注，装载不需要仓库）。

**4.1 M00_数据结构** · 归属：官方核心 · 溯源：04_模块库/通用类/M00_数据结构.md

```markdown
# 妯″潡 M00 路 鏁版嵁缁撴瀯

> 绫诲埆锛氶€氱敤锝滄潵婧愶細鏍稿績锝滄寕杞界偣锛歅00 鏁版嵁鍩哄骇锛坅ctive锛夛綔渚濊禆锛氭棤锝滆渚濊禆锛氶€氱敤:M10銆丮50銆丮01銆丮02銆丮04銆丮07銆丮80 绛?
```yaml
machine_contract:
  conformance: "L2"
  schema: "1"
  id: M00
  name: 鏁版嵁缁撴瀯
  category: 閫氱敤
  layer: P00
  inputs: []
  outputs: []
  events:
    publish: []
    subscribe: []
  interfaces: []
  io_types:
    outputs: {}
    inputs: {}
```

## 1. 鑱岃矗

瀹氫箟鍏ㄧ郴缁熺殑**鏁版嵁妲芥€荤嚎**涓庡洓绫绘牳蹇冨疄浣撶殑瀛楁濂戠害锛屾槸鎵€鏈夋ā鍧楄鍐欑殑鍞竴鏁版嵁閫氶亾銆傛暟鎹殧绂伙紙I4锛変笌閫氫俊濂戠害锛圛3锛夊湪姝よ惤鍦帮細妯″潡涔嬮棿涓嶅緱鐩存帴浜掕鍐呴儴鐘舵€侊紝鍙兘閫氳繃鏁版嵁妲戒笌浜嬩欢浜ゆ崲銆?
## 2. 鏁版嵁妲芥€荤嚎

```yaml
data_bus:
  schema_version: "1"     # 鏁版嵁妲芥€荤嚎鍗忚鐗堟湰锛坴0.5.0 T2.3 棣栧紩锛涘彧澧炰笉鍒狅紝缁撴瀯鎬у彉鏇?bump 骞舵敞鏄庤縼绉伙級
  娉ㄥ唽: 妯″潡鍚姩鏃跺０鏄?[璇绘Ы, 鍐欐Ы]锛屽啿绐佺敱 M00 鎷掔粷骞舵姤閿?  璇诲啓: 鍙厑璁稿啓鑷繁澹版槑鐨勬Ы锛涜浠栦汉妲介』澹版槑鍙锛屽啓浠栦汉妲借涓鸿繚渚?  鐢熷懡鍛ㄦ湡: 姣忓洖鍚堢粨鏉熺敱 M50 瑙﹀彂蹇収锛屼緵瀛樻。锛堢7绔犲崗璁級涓庡洖鍗?  active_pipeline: P01   # 褰撳墠瑁呴厤绠＄嚎 id锛圡50 璋冨害/瑁呴厤鍒囨崲缁存姢锛?  round:                 # 涓诲惊鐜娊璞＄姸鎬佹Ы锛圡50 鍐欏叆锛泈orld_model slot 鎶曞奖锛?    phase: begin         # 涓诲惊鐜浉浣嶏紙begin/run/end/archive/roll锛?    phase_trace: []      # 涓诲惊鐜浉浣嶈建杩癸紙鏃х浉浣嶆寜杩佺Щ椤哄簭杩藉姞锛?```

## 3. 鍥涚被鏍稿績瀹炰綋

```yaml
PlayerState:            # 鐜╁/涓昏
  schema_version: "1"   # v0.5.0 T2.3 棣栧紩锛涙紨杩涘彧澧炰笉鍒狅紙01 鍗忚 搂7 V1锛?  identity: [name, race, job, gender, age]
  attributes: {str, dex, con, int, wis, cha}   # 涓冮」鍩虹灞炴€ч粯璁?10
  vitals: {health, hunger, thirst, fatigue, temperature, insanity}
  level: {lv, exp, exp_next}
  relations: {}         # 涓嶯PC/闃佃惀鐨勫叧绯绘繁搴︼紙M40 鍐欏叆锛?  memories:             # 鍒嗗眰璁板繂锛坴0.5.0 T3锛氬崰浣?[] 缁嗗寲涓轰笁灞傦紱M13/M23 鍐?working 灞傦級
    schema_version: "1" # v0.5.0 T3 棣栧紩锛涘彧澧炰笉鍒狅紙01 鍗忚 搂7 V1锛?    working: []         # 宸ヤ綔璁板繂锛氬洖鍚堝唴鍗虫椂鎰熺煡锛岄殢鍥炲悎蹇収婊氬姩锛圡50 鍥炲悎鏈竻鐞嗭級
    episodic: []        # 鎯呮櫙璁板繂锛氬叧绯诲彶/浜嬩欢鍙?[{tick, type, target, summary, weight}]锛圡50 鍐欏洖锛?    semantic: {}        # 璇箟璁板繂锛氶暱鏈熻瀹氫笌甯歌瘑 {key: value}锛圡50 鎻愮偧锛汳23 璇诲彇杩囨护锛?  flags: {}             # 瀛樻。鏍囪浣?
NPCState:
  schema_version: "1"   # v0.5.0 T2.3 棣栧紩锛涙紨杩涘彧澧炰笉鍒狅紙01 鍗忚 搂7 V1锛?  identity: [name, race, job, hometown]
  personality: {big5: {}, fears: [], impulses: {escape, sexual, mischief}}
  relation: {depth, stage, history: []}   # M40 濂戠害
  memory:               # 鍒嗗眰璁板繂锛坴0.5.0 T3锛氬崰浣?{} 缁嗗寲涓轰笁灞傦紱M13 鍐?working 灞傦級
    schema_version: "1" # v0.5.0 T3 棣栧紩锛涘彧澧炰笉鍒狅紙01 鍗忚 搂7 V1锛?    working: []         # 宸ヤ綔璁板繂锛氬洖鍚堝唴鍗虫椂鎰熺煡锛岄殢鍥炲悎蹇収婊氬姩锛圡50 鍥炲悎鏈竻鐞嗭級
    episodic: []        # 鎯呮櫙璁板繂锛氫笌鐜╁/鍏朵粬NPC鐨勫叧绯诲彶/浜嬩欢鍙?[{tick, type, target, summary, weight}]锛圡50 鍐欏洖锛?    semantic: {}        # 璇箟璁板繂锛氶暱鏈熻瀹氫笌甯歌瘑 {key: value}锛圡50 鎻愮偧锛汳65/M80 鍙娑堣垂锛?  schedule: {}          # 鏃ョ▼锛圡13锛?  alive: true

WorldState:
  schema_version: "1"   # v0.5.0 T2.3 棣栧紩锛涙紨杩涘彧澧炰笉鍒狅紙01 鍗忚 搂7 V1锛?  time: {tick, day, season, weather}       # 閫氱敤:M10/M08 鍐欏叆
  regions: {}           # M07
  economy: {gold_reserve, market_state}    # M09
  factions: {}          # M14
  gangs: {}             # M15
  settlements: {}       # M16

EventState:             # 鍥炲悎浜嬩欢闃熷垪锛圥30 浜у嚭銆丳80 娑堣垂锛?  schema_version: "1"   # v0.5.0 T2.3 棣栧紩锛涙紨杩涘彧澧炰笉鍒狅紙01 鍗忚 搂7 V1锛?  queue: []             # 宸茬敓鎴愬緟鍙欎簨鐨勪簨浠?  consumed: []          # 宸茶鍙欎簨鍚炲苟鐨勪簨浠?  pending_narratives: [] # 浜嬩欢:M22 鍚堟垚涓殑鍙欎簨绱犳潗
```

## 4. 瀛楁瑙勮寖绾﹀畾

- 鏁板€煎瀷瀛楁缁熶竴 `int/float`锛岀姝㈠瓧绗︿覆鎷兼暟鍊硷紱缂哄け瀛楁蹇呴』鏄惧紡 `null`銆?- 鎵€鏈夋椂闂存埑浣跨敤 `tick`锛堟暣鏁板洖鍚堝彿锛? `day` 鍙岃建锛岀鐢ㄧ郴缁熺湡瀹炴椂闂淬€?- 鏂板瀛楁椤诲湪娉ㄥ唽琛ㄧ2鑺傛ā鍧楁€昏〃澶囨敞鐧昏锛屽惁鍒欒涓烘湭瀹氫箟銆?
## 5. 杩濅緥涓庤竟鐣?
- 妯″潡鏈０鏄庡啓妲借€屽啓鍏?鈫?M00 鎶涘嚭 `DATA_SLOT_VIOLATION`锛岃鍐欏叆涓㈠純骞惰褰曘€?- 瀛樻。璇诲彇鏃舵湭鐭ュ瓧娈靛拷鐣ュ苟鍛婅锛屼笉宕╂簝锛堝悜鍓嶅吋瀹癸級銆?
```

**4.2 M06_任务剧情** · 归属：官方核心 · 溯源：04_模块库/事件类/M06_任务剧情.md

```markdown
# 妯″潡 M06 路 浠诲姟鍓ф儏
> 绫诲埆锛氫簨浠讹綔鏉ユ簮锛氬叡浜綔鎸傝浇鐐癸細P30 浜嬩欢鐢熶骇锛坅ctive锛夛綔渚濊禆锛歁20锝滆渚濊禆锛歁13銆佷簨浠?M22锛堢敓瀛?M10 闅忕ぞ鍖鸿タ骞诲寘锛夛綔鍙戝竷锛歚quest_state`

```yaml
machine_contract:
  conformance: "L2"
  schema: "1"
  id: M06
  name: 浠诲姟鍓ф儏
  category: 浜嬩欢
  layer: P30
  inputs: [M20]
  outputs: [quest_id, state, tick]
  events:
    publish: [quest_state]
    subscribe: [combat_result, travel_event, chaos_event, reputation_change]
  interfaces: []
  io_types:
    outputs:
      quest_id: string
      state: string
      tick: number
    inputs:
      M20: untyped
```

## 1. 鑱岃矗
绠＄悊**浠诲姟鐢熸垚銆佸墽鎯呭彊浜嬩笌浠诲姟閾捐鍒?*锛氬熀浜庝换鍔″彊浜嬫ā鏉跨敓鎴愪换鍔★紝缁存姢浠诲姟鐘舵€佹満涓庨摼寮忔搴︼紝鎸夌帺瀹惰繘搴﹀彂甯冧换鍔＄姸鎬併€傦紙鍏变韩浠诲姟鏈哄埗锛歲uest_narratives 8 浠诲姟 / 浠诲姟鐢熸垚瑙勫垯 / 浠诲姟閾句笌濂栧姳姊害锛夈€備换鍔＄粨鏋勭敓鎴愭柟鈥斺€旀枃鏈帾杈炰笌 NPC 婕斿嚭浜?M12/M13锛涙垬鏂楃粨绠楃被鐜妭鍦ㄨ閰嶇ぞ鍖鸿タ骞荤敓瀛樺寘鏃惰蛋 M04锛堥殢鍖咃紝鍙€夛級銆?
## 2. 浠诲姟瑙勫垯
```yaml
quest:
  id: # 浠诲姟鍙欎簨妯℃澘锛? 涓熀绾夸换鍔★級
  妯℃澘缁撴瀯: 鑳屾櫙/鐩爣/鍦扮偣/鍏抽敭NPC/濂栧姳/鍚庣画閾?  瑙﹀彂鏉′欢: 澹版湜闂ㄦ(M14) + 鍦扮偣璁块棶(M07) + 闃舵鍓嶇疆
  phase: available | active | complete | failed | chain_next
quest_chain:
  姊害: 姣忛摼 3-5 鐜紝濂栧姳闅忔搴﹀崌绾э紙鑱斿姩 M01 鑱屼笟鎴愰暱锛?  鏂摼: 鐜╁澶辫触鍚庢彁渚涙浛浠ｅ叆鍙ｏ紙涓嶇‖鍗″墽鎯咃級
```
- 8 浠诲姟妯℃澘銆佷换鍔￠摼涓庡鍔辨搴︽暟鍊?鈫?瀵瑰簲棰嗗煙璧勪骇鍖咃紙闅忕ぞ鍖哄寘鍒嗗彂锛岀粡 asset_get 瀵诲潃锛夈€?
## 3. 浜嬩欢濂戠害
```yaml
subscribe:
  combat_result: # M04 鈫?璁ㄤ紣绫荤洰鏍囪揪鎴愬垽瀹?  travel_event: # M07 鈫?鎶ら€?鍒拌揪绫荤洰鏍囧垽瀹?  chaos_event: # M18 鈫?娣锋矊鎵板姩鏀瑰啓浠诲姟鐩爣/鐢熸垚鏁戞彺浠诲姟
  reputation_change: # M14 鈫?澹版湜鍗囬檷寮€鍏充换鍔＄嚎
publish:
  quest_state:
    payload: {quest_id, phase, objective, location(M07), reward, next_quest}
    subscribers: [M04, M13, 鐢熷瓨:M10]
```

## 4. 缁撶畻娴佺▼
1. 浠诲姟鐢熸垚鍣ㄦ寜瑙﹀彂鏉′欢瀹炰緥鍖栦换鍔★紙鍙栨潗鑷?M20 鐭ヨ瘑搴撲笌 M07 鍦扮偣锛夈€?2. 浠诲姟鐩爣涓庡湴鐐?澹版湜闂ㄦ缁戝畾銆?3. 鎺ㄨ繘 phase 鍙樻洿骞跺彂甯?quest_state銆?4. M13 璋冩暣鐩稿叧 NPC 瀵硅瘽鐩爣銆丮04 鍑嗗鐩爣鎴樸€佺敓瀛?M10 澶勭悊"浠诲姟涓浜?鐨勫け璐ュ垎鏀€?
## 5. 杩濅緥涓庤竟鐣?- M06 **鍙敓鎴愪换鍔＄粨鏋勪笌鐘舵€?*锛氫笉鍐欏彴璇嶏紙M12锛夈€佷笉瑁佸喅鎴樻枟锛圡04锛夈€佷笉鐩存帴娑ㄥ０鏈涳紙鐢变换鍔″畬鎴愪簨浠剁粡 M14 鏍哥畻锛夈€?- 浠诲姟鏂囨湰椤荤粡 M80 璐ㄦ闂紙缁撴瀯闂?+ 妗ｄ綅椋庢牸闂級鍚庤緭鍑猴紝M06 鍐呴儴涓嶅仛鏂囧娓叉煋銆?- 涓昏姝讳骸瀵艰嚧浠诲姟澶辫触鐨勫洖鍗峰垽瀹氬綊鐢熷瓨:M10 涓?M50锛孧06 涓嶈嚜琛屽垽姝汇€
```

**4.3 M08_季节天气** · 归属：官方核心 · 溯源：04_模块库/世界类/M08_季节天气.md

```markdown
# 妯″潡 M08 路 瀛ｈ妭澶╂皵
> 绫诲埆锛氫笘鐣岋綔鏉ユ簮锛氬叡浜綔鎸傝浇鐐癸細P10 涓栫晫鎺ㄨ繘锛坅vailable锛夛綔渚濊禆锛氶€氱敤:M10锝滆渚濊禆锛歁07銆丮04銆丮09锛堥殢绀惧尯瑗垮够鍖咃級锝滃彂甯冿細`weather_state`

```yaml
machine_contract:
  conformance: "L2"
  schema: "1"
  id: M08
  name: 瀛ｈ妭澶╂皵
  category: 涓栫晫
  layer: P10
  inputs: [閫氱敤:M10]
  outputs: [region, season, weather, day_phase, modifiers]
  events:
    publish: [weather_state]
    subscribe: [tick_day]
  interfaces: []
  io_types:
    outputs:
      region: untyped
      season: string
      weather: untyped
      day_phase: untyped
      modifiers: untyped
    inputs:
      閫氱敤:M10: untyped
```

## 1. 鑱岃矗
绠＄悊**瀛ｈ妭寰幆銆佸ぉ姘旂郴缁熶笌鐜鏁堟灉**锛氭寜涓栫晫鍘嗘帹杩涘鑺傦紝鎸夊鑺傛潈閲嶆瘡鏃ョ敓鎴愬ぉ姘旓紝缁存姢鍚勫尯鍩熷綋鍓嶇幆澧冪姸鎬佸苟骞挎挱缁欎緷璧栨柟銆傦紙season_system / environment / location_seasonal_descriptions 缁撴瀯锛涜祫浜ф暟鎹殢绀惧尯棰樻潗鍖呯粡 asset_get 瀵诲潃锛夈€傛槸鎵€鏈?鐜渚濊禆鍨?妯″潡鐨勫ぉ姘旂湡鐩告潵婧愩€?
## 2. 瀛ｈ妭涓庡ぉ姘旇鍒?```yaml
season_cycle:
  year_length: # 鐢辫祫浜у簱瀹氫箟锛堝 4 瀛?脳 90 鏃ワ級
  date: # 鐢?閫氱敤:M10 鏃ュ巻椹卞姩
daily_weather:
  generation: 鎸夊鑺傛潈閲嶆幏楠帮紙鏅?闆?闆?椋庢毚/寮傝薄锛?  persistence: 澶╂皵鐘舵€佹寔缁嫢骞?tick_day 鍚庤嚜鐒舵洿鏇?environment_effect:
  combat: 褰卞搷 M04锛堟毚椋庨洩閬斀/闆ㄥぉ鐏劙-锛?  travel: 褰卞搷 M07锛堥洩灏侀亾璺?娌虫祦娑ㄦ按锛?  market: 褰卞搷 M09锛堝啲瀛ｅ啘浜у搧娑ㄤ环 脳1.3锛?```
- 鍚勫尯鍩熷鑺傛弿杩帮紙location_seasonal_descriptions锛変笌鏁堟灉鏁板€煎叏琛?鈫?瀵瑰簲棰嗗煙璧勪骇鍖咃紙闅忕ぞ鍖哄寘鍒嗗彂锛岀粡 asset_get 瀵诲潃锛夈€?
## 3. 浜嬩欢濂戠害
```yaml
subscribe:
  tick_day: # 閫氱敤:M10 鈫?姣忔棩澶╂皵婕旇繘涓庡鑺傛帹杩?publish:
  weather_state:
    payload: {region, season, weather, day_phase, modifiers{combat, travel, market}}
    subscribers: [M07, M04, M09]
```

## 4. 缁撶畻娴佺▼
1. 鏀跺埌 tick_day锛屾帹杩涙棩鍘嗐€?2. 鍒ゅ畾瀛ｈ妭鏇存浛锛堣法瀛ｆ椂骞挎挱瀛ｈ妭浜嬩欢锛夈€?3. 鎸夋潈閲嶇敓鎴?寤剁画褰撳墠鍖哄煙澶╂皵銆?4. 鍙戝竷 weather_state锛岃闃呮柟鎸夐渶搴旂敤淇銆?
## 5. 杩濅緥涓庤竟鐣?- M08 **鍙绠楃幆澧冪姸鎬佸苟骞挎挱锛屼笉瑁佸喅鎴樻枟/浠锋牸/鏃呰缁撴灉**鈥斺€斾慨姝ｇ敱 M04/M09/M07 鍚勮嚜搴旂敤銆?- 涓嶅緱璺宠繃 tick_day 鑷鎺ㄨ繘鏃堕棿锛堟椂闂村敮涓€鏉ユ簮鏄?閫氱敤:M10锛夈€?- 鐜寮傝薄鑻ユ瀯鎴愬彊浜嬩簨浠讹紝椤讳氦浜嬩欢:M22 缁勭粐锛孧08 涓嶇洿鎺ュ彂甯冨彊浜嬨€?
```

**4.4 M10_时间推进** · 归属：官方核心 · 溯源：04_模块库/通用类/M10_时间推进.md

```markdown
# 妯″潡 閫氱敤:M10 路 鏃堕棿鎺ㄨ繘

> 绫诲埆锛氶€氱敤锝滄潵婧愶細鏍稿績锝滄寕杞界偣锛歅10 涓栫晫鎺ㄨ繘锛坅ctive锛夛綔渚濊禆锛歁00锝滃彂甯冿細`tick_day`

```yaml
machine_contract:
  conformance: "L2"
  schema: "1"
  id: 閫氱敤:M10
  name: 鏃堕棿鎺ㄨ繘
  category: 閫氱敤
  layer: P10
  inputs: [M00]
  outputs: [tick, day, season]
  events:
    publish: [tick_day, minute_tick]
    subscribe: []
  interfaces: []
  tool_face:
    - purpose: 鍥炲悎/鏃?鍒嗛挓涓夎建鏃堕棿鎹㈢畻涓庤法鏃ュ垽瀹?      candidates:
        - repo: https://github.com/arrow-py/arrow
          ref: 1.3.0
          license: BSD-2-Clause
          note: 鎴愮啛鏃堕棿搴擄紝浠呬綔瀹炵幇鍙傝€冿紱寮曠敤涓嶇瓑浜庤儗涔︼紝AI 鍙嚜閫犵瓑浠疯兘鍔?      guidance:
        瑕佺畻浠€涔? 浠?tick 鎶樼畻 day銆乵inute銆乮s_new_day 涓?season_ctx
        杈撳嚭褰㈢姸: 鏁存暟 tick/day/minute锛涘竷灏?is_new_day锛涘瓧绗︿覆 season_ctx
        瀵规帴瀛楁: outputs=[tick, day, season]锛屼簨浠?payload 瑙佺 4 鑺?        甯歌鍧? 鍒嗛挓鍒跺彧鍦?P03 鍚敤锛涜法鏃ュ彧鍙戝竷涓€娆?tick_day锛涚姝㈡ā鍧楄嚜琛屾帹杩涙椂闂?  io_types:
    outputs:
      tick: number
      day: number
      season: string
    inputs:
      M00: state
```

## 1. 鑱岃矗

椹卞姩绯荤粺鏃堕棿杞达紝缁存姢 `tick / day / season` 涓夎建鏃堕挓锛屽苟骞挎挱鍥炲悎鎺ㄨ繘浜嬩欢銆傛墍鏈?姣忔棩/姣忓洖鍚?缁撶畻鐨勬ā鍧楋紙M01銆丮19銆丮08銆丮09銆丮40锛夊潎浠ユ湰妯″潡鐨勬帹杩涗俊鍙蜂负鑺傛媿銆?
## 2. 鏃堕棿灏哄害

| 灏哄害 | 鍗曚綅 | 鐢ㄩ€?| 閫傜敤绠＄嚎 |
| --- | --- | --- | --- |
| tick | 1 鍥炲悎 | 涓诲惊鐜渶灏忔杩涳紙M50 鍥炲嵎鍗曚綅锛?| P01/P02/P03 |
| day | 1 鏃?= 鑻ュ共 tick | 鏃ョ▼/鍒锋柊/濂芥劅缁撶畻 | P01/P02 |
| 鍒嗛挓鍒?| 1 鏃ョ粏鍒?| 鐢熷瓨娑堣€楅€愬垎閽熺粨绠?| 绀惧尯瑗垮够鐢熷瓨鍖咃紙P03锛?|

- 绀惧尯鏍″洯鎯呮劅鍖咃紙P02锛変互 `day` 涓轰富鑺傛媿锛氫笂瀛︽棩/鍛ㄦ湯鍖哄垎鏃ョ▼銆?- 绀惧尯瑗垮够鐢熷瓨鍖咃紙P03锛夊惎鐢ㄥ垎閽熷埗瀛愮粨绠楋細`fatigue/hunger` 姣?10 鍒嗛挓鍒绘墸鍑忥紝M10 璐熻矗鎶婂垎閽熷埢搴︽姌绠椾负 tick 浜嬩欢銆?
## 3. 鎺ㄨ繘娴佺▼

```yaml
advance:
  1. tick += 1
  2. 鑻ヨ法鏃ワ紙day 鍙樻洿锛夆啋 鍙戝竷 tick_day锛堝惈鏂?day 鍙枫€乻eason 鐘舵€侊級
  3. 鑻?P03 鍒嗛挓鍒?鈫?棰濆鍙戝竷 minute_tick锛堟瘡 10 鍒嗛挓鍒诲害锛?  4. 绛夊緟璁㈤槄鑰呭畬鎴愮粨绠楋紙鍚屾锛夛紝鍐嶈繑鍥?M50 缁х画涓嬩竴灞?```

## 4. 浜嬩欢濂戠害

```yaml
publish: tick_day
  payload: {tick, day, is_new_day: bool, season_ctx}
  subscribers: [鐢熷瓨:M01, 鐢熷瓨:M19, M08, M09, M40]
publish: minute_tick        # 浠?P03 鍚敤
  payload: {tick, minute}
  subscribers: [鐢熷瓨:M01, M04]
```

## 5. 杩濅緥涓庤竟鐣?
- 浠讳綍妯″潡绂佹鑷鎺ㄨ繘绯荤粺鏃堕棿锛涘彧鍏佽璇锋眰 `M10.advance(n)`銆?- 鏃堕棿鍥炲嵎锛堝洖婧?璇绘。锛夌敱 M50 缁熶竴瑙﹀彂锛孧10 鍙帴鍙楀洖鍗锋寚浠ゅ苟閲嶆斁浜嬩欢銆?
```

**4.5 M12_NPC对话** · 归属：官方核心 · 溯源：04_模块库/事件类/M12_NPC对话.md

```markdown
# 妯″潡 M12 路 NPC 瀵硅瘽
> 绫诲埆锛氫簨浠讹綔鏉ユ簮锛氬叡浜綔鎸傝浇鐐癸細P50 浜や簰鎵ц锛坅ctive锛夛綔渚濊禆锛歁20銆丮13锝滆渚濊禆锛歁13锝滃彂甯冿細鏃?
```yaml
machine_contract:
  conformance: "L2"
  schema: "1"
  id: M12
  name: NPC 瀵硅瘽
  category: 浜嬩欢
  layer: P50
  inputs: [M20, M13]
  outputs: []
  events:
    publish: []
    subscribe: []
  interfaces: []
  io_types:
    outputs: {}
    inputs:
      M20: untyped
      M13: untyped
```

## 1. 鑱岃矗
绠＄悊**NPC 瀵硅瘽妯℃澘涓庝氦浜掕涓虹礌鏉?*锛氱淮鎶?13+ NPC 鐨勫璇濇ā鏉夸綋绯伙紙闂茶亰/浠诲姟绾跨储/濂芥劅鍥炲簲/绉樺瘑鎯呮姤锛夛紝鎸夎Е鍙戞潯浠朵緵缁欏彲閫夐」涓庡彴璇嶃€傦紙npc_dialogue_templates 13+NPC / 瀵硅瘽绫诲埆涓庤Е鍙戣鍒欙紝妯℃澘鍐呭闅忕ぞ鍖洪鏉愬寘鎵╁睍锛夈€傛槸"鍙拌瘝搴?锛屼笌 M13 鐘舵€佹満鏋勬垚妯℃澘-鐘舵€佷簰鏌ョ殑鍙屽悜鑰﹀悎銆?
## 2. 瀵硅瘽妯℃澘瑙勫垯
```yaml
dialogue_template:
  npc_id: # 13+NPC 鍏ㄨ〃
  category: 闂茶亰 | 浠诲姟绾跨储 | 濂芥劅鍥炲簲 | 绉樺瘑鎯呮姤 | 浜嬩欢鍥炲簲
  trigger_condition:
    濂芥劅妗ｄ綅: # 鐢?M13 濂芥劅搴﹀嚱鏁版彁渚?    浠诲姟闃舵: # 鐢?M06 quest_state 鎻愪緵
    闃佃惀澹版湜: # 鐢?M14 鎻愪緵
  lines: # 鍙拌瘝鏉＄洰锛堟寜妗ｄ綅 DNA 璐ㄦ锛岃嫢鏈夛級
  options: []  # 鐜╁鍙€夐」
  effect: 濂芥劅褰卞搷 | 鎯呮姤瑙ｉ攣 | 浠诲姟鎺ㄨ繘锛堝洖浼?M13锛?```
- 13+NPC 瀵硅瘽妯℃澘鍏ㄨ〃 鈫?瀵瑰簲棰嗗煙璧勪骇鍖咃紙闅忕ぞ鍖哄寘鍒嗗彂锛岀粡 asset_get 瀵诲潃锛夈€?
## 3. 妯℃澘-鐘舵€佷簰鏌?- M12 鎻愪緵**闈欐€佸彴璇?*锛孧13 鎻愪緵**杩愯鏃?NPC 鐘舵€?*锛堝ソ鎰?鏃ョ▼/鐩爣/璁板繂锛夈€?- 瀵硅瘽瑙﹀彂 = M13 鍒ゅ畾"璇ヤ笉璇ヨ亰"鈫?M12 鎸夋潯浠舵绱?鑱婁粈涔?鈫?鏁堟灉鍥炲啓 M13銆?- 浜岃€呭惊鐜緷璧栧湪娉ㄥ唽琛ㄥ凡鐧昏锛?*鎵ц椤哄簭鐢?M50 绗?9 姝ョ粺涓€缂栨帓**锛堝厛 M13 鐘舵€併€佸悗 M12 鍑鸿瘝锛夈€?
## 4. 浜嬩欢濂戠害
```yaml
subscribe: []  # 涓嶇洿鎺ヨ闃呰繍琛屾椂浜嬩欢锛涚粡 M13 鏌ヨ鎺ュ彛鍙栫姸鎬?publish: []    # 涓嶅彂甯冧簨浠讹紱瀵硅瘽鏁堟灉缁?M13 鐨?interaction_update 缁熶竴骞挎挱
```

## 5. 杩濅緥涓庤竟鐣?- M12 鍙彁渚涘彴璇嶄笌閫夐」绱犳潗锛?*涓嶈鍐冲ソ鎰熸暟鍊?*锛堝ソ鎰熷嚱鏁板湪 M13锛夈€?*涓嶇敓鎴愪换鍔?*锛圡06锛夈€?- 鍙拌瘝鍚殣钘忓煙淇℃伅锛堢瀵?浼忕瑪锛夋椂锛屼緵缁欑帺瀹堕』缁?M23 璁ょ煡杈圭晫瑁佸壀銆?- 鍙拌瘝鏂囨湰閬靛惊 M80 椋庢牸闂紙妗ｄ綅 DNA 鍙拌瘝瑙勫垯锛岃嫢鏈夛級锛涚姝㈤暱绡囩嫭鐧姐€
```

**4.6 M13_NPC交互** · 归属：官方核心 · 溯源：04_模块库/事件类/M13_NPC交互.md

```markdown
# 妯″潡 M13 路 NPC 浜や簰
> 绫诲埆锛氫簨浠讹綔鏉ユ簮锛氬叡浜綔鎸傝浇鐐癸細P30 浜嬩欢鐢熶骇锛坅ctive锛夛綔渚濊禆锛歁12銆丮06銆丮20锝滆渚濊禆锛歁40銆丮14锛堥殢绀惧尯鍖咃級銆佷簨浠?M22锝滃彂甯冿細`interaction_update`

```yaml
machine_contract:
  conformance: "L2"
  schema: "1"
  id: M13
  name: NPC 浜や簰
  category: 浜嬩欢
  layer: P30
  inputs: [M12, M06, M20]
  outputs: [npc_id, action, result, tick]
  events:
    publish: [interaction_update]
    subscribe: [quest_state, level_up]
  interfaces: []
  io_types:
    outputs:
      npc_id: string
      action: string
      result: string
      tick: number
    inputs:
      M12: untyped
      M06: untyped
      M20: untyped
```

## 1. 鑱岃矗
绠＄悊 **NPC 杩愯鏃剁姸鎬佹満銆佽蹇嗐€佹棩绋嬨€佺洰鏍囦笌濂芥劅鍑芥暟**锛氬疄渚嬪寲 NPC 涓綋锛岀淮鎶ゅ叾涓庣帺瀹剁殑濂芥劅鏁板€间笌浜や簰鍘嗗彶锛屾妸姣忔浜や簰缁撶畻涓?interaction_update 骞挎挱缁欏叧绯?澹版湜/鍙欎簨妯″潡銆傦紙NPCInstance 鐘舵€佹満 / NPC璁板繂 / 鏃ョ▼琛屼负 / 鐩爣绯荤粺 / 姝讳骸缁ф壙 / 濂芥劅搴﹀嚱鏁帮級銆?*NPC 涓綋鐪熺浉鏉ユ簮**锛堢兢浣撳０鏈涘綊 M14锛汳14 闅忕ぞ鍖鸿タ骞诲寘锛夈€?
## 2. NPC 鐘舵€佹満
```yaml
npc_instance:
  id: # 瀹炰緥鍖栬嚜璧勪骇搴?NPC 妯℃澘
  state: 韬唤/浣嶇疆(M07)/鑱屼笟(M01)/绉嶆棌(M02)
  affinity: 鐜╁濂芥劅鏁板€硷紙鍖洪棿锛岃仈鍔?M40 鍏崇郴娣卞害妯″瀷鏍″噯锛?  memory: []  # 璁板繂鏉＄洰锛堢粡 M23 璁ょ煡杈圭晫绠＄悊锛氳寰椾粈涔?涓嶈寰椾粈涔堬級
  schedule: 鏃ョ▼锛堟瘡鏃ユ洿鏂帮紝鍙?閫氱敤:M10 tick 椹卞姩锛?  goals: []   # 鐩爣锛堜换鍔?M06 / 鐢熷瓨 / 鍏崇郴 M40锛?  alive: true # 姝讳骸涓庣户鎵胯仈鍔?鐢熷瓨:M10 / M19
affinity_function:
  杈撳叆: 瀵硅瘽(M12) / 璧犵ぜ / 甯姪 / 鍐茬獊
  杈撳嚭: affinity_delta 鈫?interaction_update
```

## 3. 浜嬩欢濂戠害
```yaml
subscribe:
  quest_state: # M06 鈫?浠诲姟鏀瑰彉 NPC 鐩爣涓庡彲鐢ㄥ璇?  level_up: # M01 鈫?鐜╁绛夌骇褰卞搷 NPC 鎬佸害鍩虹嚎
publish:
  interaction_update:
    payload: {npc_id, type, affinity_delta, context, flags[]}
    subscribers: [M40, M14, 浜嬩欢:M22]
```

## 4. 缁撶畻娴佺▼
1. 姣忔棩/浜嬩欢椹卞姩 NPC 鏃ョ▼鏇存柊锛堢潯瑙?宸ヤ綔/绉诲姩/寰呮満锛夈€?2. 鐜╁鍙戣捣浜や簰 鈫?缁?M12 妫€绱㈠彴璇嶃€佺帺瀹堕€夋嫨鐢熸晥銆?3. 濂芥劅鍑芥暟缁撶畻 affinity_delta銆?4. 鍙戝竷 interaction_update锛歁40 鎶樼畻鍏崇郴娣卞害銆丮14 鎶樼畻闃佃惀澹版湜璐＄尞銆佷簨浠?M22 閲囬泦鍙欎簨绱犳潗銆?
## 5. 杩濅緥涓庤竟鐣?- M13 瑁佸喅 **NPC 涓綋**鐨勫ソ鎰?璁板繂/鐩爣锛涙亱鐖辨。浣嶅綊 M40/M41锛岀兢浣撳０鏈涘綊 M14銆?- 璁板繂鍐欏叆椤婚伒瀹?M23锛氱帺瀹朵笉鍙鐨勮蹇嗕笉杩涘叆鍙鍩熴€?- NPC 姝讳骸鍒ゅ畾浜ょ敓瀛?M10锛孧13 鍙墽琛?姝讳骸鍚庣姸鎬佹竻鐞嗕笌缁ф壙"銆?- 浜や簰浜х敓鐨勬枃鏈紨鍑哄綊 M12/M80锛孧13 涓嶅仛鏂囧娓叉煋銆
```

**4.7 M20_世界知识库** · 归属：官方核心 · 溯源：04_模块库/事件类/M20_世界知识库.md

```markdown
# 妯″潡 M20 路 涓栫晫鐭ヨ瘑搴?> 绫诲埆锛氫簨浠讹綔鏉ユ簮锛氬叡浜綔鎸傝浇鐐癸細P70 鍙欎簨绱犳潗锛坅ctive锛? P00 鏁版嵁鍩哄骇锛坅vailable锛夛綔渚濊禆锛歁00锝滆渚濊禆锛歁06銆丮12銆丮13锛汳01鈥揗04 闅忕ぞ鍖鸿タ骞诲寘锝滃彂甯冿細鏃?
```yaml
machine_contract:
  conformance: "L2"
  schema: "1"
  id: M20
  name: 涓栫晫鐭ヨ瘑搴?  category: 浜嬩欢
  layer: P70
  inputs: [M00]
  outputs: []
  events:
    publish: []
    subscribe: []
  interfaces: [query]
  io_types:
    outputs: {}
    inputs:
      M00: state
```

## 1. 鑱岃矗
绠＄悊**涓栫晫瑙傚父璇嗗簱**锛氱墿鐞嗘硶鍒欍€佸湴鐞嗐€侀瓟娉曠悊璁恒€佺ぞ浼氱粨鏋勩€佺鏃忕煡璇嗐€佸巻鍙蹭笌鏃堕棿瀛ｈ妭銆佸師缃鐗囪瀹氾紝鎸夐渶渚涚粰鍚勬ā鍧椾綔涓?甯歌瘑涓婁笅鏂?锛岄槻姝㈣鑹插仛鍑鸿繚鍙嶄笘鐣岃鐨勮涓恒€傦紙world_knowledge 鐭ヨ瘑鍩燂細8 绉嶆棌 + 鍦扮悊 + 鐗╃悊 + 榄旀硶 + 绀句細 + 鐢熺墿 + 鐗╁搧 + 甯歌瘑 + 鏃堕棿瀛ｈ妭 + 鍘熺姜纰庣墖锛涙潯鐩唴瀹归殢棰樻潗璧勪骇鍖咃級銆?*鍙鐭ヨ瘑搴擄紝涓嶅惈鏁板€艰鍒?*锛堟暟鍊煎湪鍚勬ā鍧?璧勪骇搴擄級銆?
## 2. 鐭ヨ瘑鏉＄洰缁撴瀯
```yaml
knowledge_entry:
  domain: 鐗╃悊 | 榄旀硶 | 绀句細 | 鐢熺墿 | 鐗╁搧 | 鍦扮悊 | 甯歌瘑 | 鍘嗗彶 | 鏃堕棿瀛ｈ妭 | 鍘熺姜纰庣墖
  key: 鐭ヨ瘑閿紙濡?races.elf / physics.magic_rule / fragments.sin锛?  content: 鏉＄洰鍐呭锛堥潰鍚戝紩鎿庣殑瀹㈣鎻忚堪锛?  access: # 渚涚粰鏉′欢锛氳鑹叉槸鍚?搴旇鐭ラ亾"锛堢粡 M23 璁ょ煡瑁佸壀锛?  consumers: [M01, M02, M03, M04, M06, M12, M13] # 鍏佽娑堣垂鏂?```
- 鍏ㄩ噺鐭ヨ瘑鏉＄洰 鈫?瀵瑰簲棰嗗煙璧勪骇鍖咃紙闅忕ぞ鍖哄寘鍒嗗彂锛岀粡 asset_get 瀵诲潃锛夛紙world_knowledge 鍖哄潡锛夈€?
## 3. 渚涚粰涓庢煡璇?```yaml
query(domain, key, viewer):
  1. 妫€绱㈡潯鐩紱鏈煡閿?鈫?杩斿洖绌哄苟鍛婅锛堥槻骞昏锛?  2. 鎸?viewer 璁ょ煡杈圭晫锛圡23锛夎鍓細闅愯棌鍩熷唴瀹逛笉渚涚粰
  3. 杩斿洖鏉＄洰渚涙秷璐规柟鍋氫竴鑷存€ф牎楠?瑁呰浇鏃舵満: 鎵ц椤哄簭绗?4 姝ワ紙M50 璋冨害锛氫笘鐣屽父璇嗚杞斤級
```

## 4. 涓庡悇妯″潡鐨勯厤鍚?- M01/M02锛氳亴涓?绉嶆棌鑳藉姏鏄惁绗﹀悎涓栫晫瑙傝瀹氥€?- M03/M04锛氭妧鑳?榄旀硶鏁堟灉涓庣煡璇嗗簱瑙勫垯涓€鑷存€с€?- M06锛氫换鍔¤儗鏅彇鏉愶紙鍘嗗彶/鍦扮悊甯歌瘑锛夈€?- M12/M13锛歂PC 鍙拌瘝涓庤涓轰笉寰楄繚鍙嶅叾绉嶆棌/绀句細甯歌瘑銆?
## 5. 杩濅緥涓庤竟鐣?- M20 鏄?*鍙甯歌瘑搴?*锛氫笉瑁佸喅琛屼负銆佷笉浜у嚭鍓ф儏銆佷笉鎸佹湁鏁板€兼洸绾裤€?- 娑堣垂鏂规绱笉鍒扮殑閿涓?鐭ヨ瘑涓嶅瓨鍦?锛岀姝㈠嚟 LLM 鍏堥獙鑴戣ˉ鍐欏叆鍓ф儏銆?- 鏂扮煡璇嗘潯鐩』璧拌祫浜у簱鏂板锛圼EXT-璧勪骇] 鎵╁睍鐐癸級锛岃繍琛屾椂涓嶅彲鐩存帴鏀瑰啓鐭ヨ瘑搴撱€
```

**4.8 M22_事件叙事** · 归属：官方核心 · 溯源：04_模块库/事件类/M22_事件叙事.md

```markdown
# 妯″潡 浜嬩欢:M22 路 浜嬩欢鍙欎簨
> 绫诲埆锛氫簨浠讹綔鏉ユ簮锛氭牳蹇冿綔鎸傝浇鐐癸細P30 浜嬩欢鐢熶骇锛坅ctive锛夛綔渚濊禆锛氭棤锛堢洃鍚簨浠舵€荤嚎锛涘叿浣撲簨浠舵簮闅忕ぞ鍖洪鏉愬寘瑁呴厤锛夛綔琚緷璧栵細M80锝滃彂甯冿細`narrative_event`

```yaml
machine_contract:
  conformance: "L2"
  schema: "1"
  id: 浜嬩欢:M22
  name: 浜嬩欢鍙欎簨
  category: 浜嬩欢
  layer: P30
  inputs: []
  outputs: [type, payload, tick]
  events:
    publish: [narrative_event]
    subscribe: [death_trigger, relationship_change, chaos_event, ghost_event, market_event, production_output, interaction_update]
  interfaces: []
  io_types:
    outputs:
      type: untyped
      payload: object
      tick: number
    inputs: {}
```

## 1. 鑱岃矗
绠＄悊**鍙欎簨浜嬩欢鐢熸垚銆佹椂闂寸嚎鎺ㄨ繘涓庢晠浜嬮┍鍔?*锛氭眹鑱氬悇婧愭ā鍧楀彂甯冪殑闆舵暎浜嬩欢锛堜换鍔?娣锋矊/鍏崇郴/閬楁喚/姝讳骸/甯傚満锛夛紝鏍￠獙鍥犳灉涓€鑷存€у悗缁勭粐涓烘寜搴忕殑 narrative_event 娴侊紝椹卞姩杩炶疮鍙欎簨鏃堕棿绾裤€傦紙浜嬩欢鐢熸垚鏈哄埗 / 浜嬩欢绫诲瀷浣撶郴 / 浜嬩欢瑙﹀彂鏉′欢涓庢祦绋?/ 浜嬩欢涓庡彊浜嬭仈鍔級銆傛槸**鍙欎簨缂栨帓鑰?*鈥斺€斾笉鍋氭暟鍊肩粨绠楋紝鍙仛鍥犳灉缂栨帓銆?
## 2. 浜嬩欢缂栨帓瑙勫垯
```yaml
narrative_event:
  type: 鎴愰暱 | 鍏崇郴 | 鍐茬獊 | 涓栫晫鍙樿縼 | 绉樺瘑鎻檽 | 閬楁喚娌夋穩
  source: 浜嬩欢鏉ユ簮妯″潡锛坬uest/chaos/romance/ghost/death/market鈥︼級
  beats: []  # 鍙欎簨鑺傛媿锛堜緵 M80 娓叉煋鐨勭礌鏉愬簭鍒楋級
  pov: # 瑙嗚鍩燂紙M23锛夛細鐜╁鍙/鎺ㄦ柇/闅愯棌
  causal_chain: # 鍓嶅洜閾撅細姣忎簨浠跺繀椤绘湁鍓嶅洜锛岀姝㈢┖闄?consistency_check:
  鍐茬獊 鈫?闄嶇骇/閲嶆帓/瑕佹眰婧愭ā鍧椾慨姝?  鍘婚噸 鈫?鍚岀被鍚屽洜浜嬩欢鍚堝苟
  缂栨帓 鈫?鍥犳灉椤哄簭鍐欏叆鏃堕棿绾?```

## 3. 浜嬩欢濂戠害
```yaml
subscribe:
  death_trigger: # 鐢熷瓨:M10 鈫?姝讳骸浜嬩欢鍏ョ嚎
  relationship_change: # M40 鈫?鍏崇郴閲岀▼纰?  chaos_event: # M18 鈫?涓栫晫鎵板姩
  ghost_event: # M65 鈫?閬楁喚鏄惧舰
  market_event: # M09 鈫?缁忔祹澶т簨
  production_output: # M17 鈫?浼犲閫犵墿
  interaction_update: # M13 鈫?鍏抽敭浜や簰
publish:
  narrative_event:
    payload: {seq_no, type, beats[], pov, causal_chain}
    subscribers: [M80, M65]
```

## 4. 缂栨帓娴佺▼
1. 鎺ユ敹鍚勬簮妯″潡浜嬩欢锛堟湰鍥炲悎鍐呮殏瀛橈級銆?2. 涓€鑷存€ф牎楠?+ 鍘婚噸 + 鍥犳灉閾炬帴锛堟煡 M00 浜嬩欢鎬荤嚎鍘嗗彶锛夈€?3. 鍐冲畾鍝簺鍏ョ嚎銆佷互浣曢『搴忋€佺帺瀹惰瑙掑浣曞憟鐜帮紙M23 瑁佸壀锛夈€?4. 鍙戝竷 narrative_event 鈫?M80 娓叉煋涓烘鏂囷紱M65 妫€鏌ユ槸鍚︽矇娣€閬楁喚銆?
## 5. 杩濅緥涓庤竟鐣?- 浜嬩欢:M22 **鍙紪鎺掑洜鏋滀笌椤哄簭**锛屼笉鎵ц鏁板€肩粨绠楋紙缁撶畻鍦ㄥ悇婧愭ā鍧楀唴瀹屾垚锛夈€?- 鐜╁鏈煡鐨勭嚎绱㈡斁鍏ラ殣钘忓煙锛圡23锛夛紝涓嶅緱鎻愬墠杩涘叆鍙鍙欎簨銆?- 鎯呮劅:M22锛堜笁鍐插姩锛変簨浠剁敱鍏剁洿鍙戯紝浜嬩欢:M22 缂栨帓鏃跺 NPC 鍐插姩浜嬩欢**璞佸厤涓€娆￠渶鏄惧紡鏍囪**锛堟敞鍐岃〃娉ㄩ噴锛夈€?- 鍙欎簨绾块』灏婇噸鏃㈡湁瑙掕壊琛屼负涓庤瀹氾紙涓€鑷存€х邯寰嬶級锛岀姝㈡€ф牸婕傜Щ銆
```

**4.9 M23_认知边界** · 归属：官方核心 · 溯源：04_模块库/通用类/M23_认知边界.md

```markdown
# 妯″潡 M23 路 璁ょ煡杈圭晫

> 绫诲埆锛氶€氱敤锝滄潵婧愶細鏍稿績锝滄寕杞界偣锛歅20 瑙掕壊鐘舵€侊紙active锛夛綔渚濊禆锛歁00锝滆渚濊禆锛歁13銆佷簨浠?M22

```yaml
machine_contract:
  conformance: "L2"
  schema: "1"
  id: M23
  name: 璁ょ煡杈圭晫
  category: 閫氱敤
  layer: P20
  inputs: [M00]
  outputs: []
  events:
    publish: []
    subscribe: []
  interfaces: [cognition.filter]
  io_types:
    outputs: {}
    inputs:
      M00: state
```

## 1. 鑱岃矗

鎵ц**瑙嗚瑁佸壀**锛氬彊浜嬪彧鑳藉憟鐜?涓昏褰撳墠鍙煡"鐨勪俊鎭€備换浣曡鑹插唴蹇冦€佸鍚庡璇濄€佹湭鎰熺煡浜嬩欢涓€寰嬩笉寰楄繘鍏ヨ緭鍑虹礌鏉愨€斺€旇繖鏄瑙掔邯寰嬶紙涓昏鍙煡鍘熷垯锛夌殑绯荤粺渚т繚闅溿€?
## 2. 璁ょ煡鍩熸ā鍨?
```yaml
cognition:
  鍙鍩? 涓昏鍦ㄥ満銆佸彲瑙傚療锛堝満鏅唴 + 宸茬煡鎯呮姤锛?  鎺ㄦ柇鍩? 鍙鍩熻瘉鎹彲鎺ㄥ嚭鐨勭粨璁猴紙鍏佽瑙掕壊"鐚滄祴"锛岄』鏍囨敞涓嶇‘瀹氾級
  闅愯棌鍩? 鍏朵粬瑙掕壊鍐呭績/鍔ㄦ満銆佹湭瑙﹀彂浜嬩欢銆佺郴缁熺湡瀹炵姸鎬?瑁佸壀瑙勫垯:
  - 杈撳嚭绱犳潗浠呭厑璁告潵鑷?鍙鍩?鈭?鎺ㄦ柇鍩?  - 闅愯棌鍩熶俊鎭笉寰楃洿鎺ュ彊杩帮紱鍙彲閫氳繃琛屼负銆佺墿浠躲€佽〃鎯呯瓑鍙璇佹嵁闂存帴閫忓嚭
```

## 3. 鍙岄噸鐪熺浉鏀寔

- 绯荤粺灞傚彲淇濈暀瀹屾暣鐪熺浉锛堜緵 M65 閬楁喚娌夋穩銆丮41 鎭嬬埍鍒ゅ畾浣跨敤锛夛紱
- 鍛堢幇灞傦紙M80锛夊彧鑳芥嬁鍒拌鍓悗鐨勭礌鏉愶紱
- 鍚屼竴鐢婚潰鍙壙杞戒袱灞傚惈涔夛細琛ㄥ眰涓鸿鑹叉墍瑙侊紝娣卞眰鐪熺浉鐣欑櫧锛堣瑙掔邯寰嬬殑鑷劧寤朵几锛夈€?
## 4. 鑱斿姩

- 璇诲彇锛歁13锛圢PC 璁板繂锛夈€丮20锛堜笘鐣岀煡璇嗗簱锛夈€丮55锛堟儏涔﹀尶鍚嶆€э級銆丮65锛堥仐鎲剧湡鐩革級銆?- 浜嬩欢锛歁23 涓嶅彂甯冧簨浠讹紱M13/浜嬩欢:M22 姣忔鍙栫礌鏉愬墠椤诲厛杩?`cognition.filter()`銆?
## 5. 杩濅緥涓庤竟鐣?
- 杈撳嚭涓嚭鐜伴殣钘忓煙鐩磋堪 鈫?璐ㄦ fail锛堣瑙掔邯寰嬭繚渚嬶紝M80 缁撴瀯闂?S5锛夈€?- 涓昏澶卞繂/鏄忚糠/绂荤嚎鍦烘櫙锛氬彲瑙佸煙闄嶄负绌猴紝鍙兘杈撳嚭鐜鐧芥弿銆?
```

**4.10 M24_组合规则** · 归属：官方核心 · 溯源：04_模块库/通用类/M24_组合规则.md

```markdown
# 妯″潡 M24 路 缁勫悎瑙勫垯

> 绫诲埆锛氶€氱敤锝滄潵婧愶細鍏变韩锝滄寕杞界偣锛歅70 鍙欎簨绱犳潗锛坅ctive锛夛綔渚濊禆锛歁00锝滆渚濊禆锛氭棤

```yaml
machine_contract:
  conformance: "L2"
  schema: "1"
  id: M24
  name: 缁勫悎瑙勫垯
  category: 閫氱敤
  layer: P70
  inputs: [M00]
  outputs: []
  events:
    publish: []
    subscribe: []
  interfaces: [resolve]
  io_types:
    outputs: {}
    inputs:
      M00: state
```

## 1. 鑱岃矗

绯荤粺**缁勫悎/鎵╁睍瑙勫垯**鐨勫敮涓€缁撶畻鍏ュ彛锛氭妧鑳借瀺鍚堛€佸厓绱犵粍鍚堛€佽瘝鏉″悎鎴愮瓑"涓ょ墿鍚堝嚭鏂扮墿"鐨勯€昏緫缁熶竴鍦ㄦ鐧昏涓庡垽瀹氾紝闃叉鍚勬ā鍧楀悇鑷负鏀夸骇鐢熻鍒欏啿绐併€?
## 2. 缁勫悎閰嶆柟娉ㄥ唽琛?
```yaml
combinations:
  skill_fusion:        # 鎶€鑳借瀺鍚?9 閰嶆柟锛堟簮锛氱ぞ鍖鸿タ骞诲寘 M03.2锛?    input: [鎶€鑳紸, 鎶€鑳紹]
    output: 铻嶅悎鎶€鑳斤紙鏂板悕+鏁堟灉鍙犲姞瑙勫垯锛?  element_pair:        # 浜屽厓绱犵粍鍚?22 鏉★紙婧愶細绀惧尯瑗垮够鍖?M11.6锛?    input: [鍏冪礌A, 鍏冪礌B]
    output: 澶嶅悎娉曟湳鏁堟灉
  spell_word:          # 璇嶆牴鍚堟垚锛堟簮锛氱ぞ鍖鸿タ骞诲寘 M11.4/11.5锛?    input: [璇嶆牴搴忓垪]
    output: 鍜掕锛堟枃瀛楀嵆鍜掕锛?  race_hybrid:         # 浜氱鏉備氦锛堟簮锛氱ぞ鍖鸿タ骞诲寘 M02.5锛?    input: [绉嶆棌A, 绉嶆棌B]
    output: 浜氱澶╄祴琛?```

## 3. 鍒ゅ畾娴佺▼

```yaml
resolve(inputA, inputB):
  1. 鏌ョ粍鍚堣〃 鈫?鍛戒腑閰嶆柟杩斿洖 output
  2. 鏈懡涓?鈫?杩斿洖 null锛堜笉鑷姩鑴戣ˉ缁勫悎锛岀姝㈣嚜鐢卞彂鎸ワ級
  3. 鍛戒腑浣嗘潯浠朵笉瓒筹紙绛夌骇/鏉愭枡/缇佺粖锛夆啋 杩斿洖 blocked + 缂轰粈涔?  4. 缁撶畻缁撴灉鍐欏叆 P70 绱犳潗妲斤紝渚?M80 鍛堢幇
```

## 4. 鎵╁睍绾﹀畾

- 鏂板缁勫悎閰嶆柟椤诲湪姝ょ櫥璁板苟闄勫甫鍑哄锛堟簮妗嗘灦绔犺妭鍙锋垨鐢ㄦ埛鑷畾涔夊寘锛夈€?- 鐢ㄦ埛鑷畾涔夊寘鍙鐩栭粯璁ら厤鏂癸紝浼樺厛绾э細鐢ㄦ埛鑷畾涔?> 绀惧尯棰樻潗鍖?> 鏍稿績榛樿銆?
## 5. 杩濅緥涓庤竟鐣?
- 绂佹鍦ㄧ粍鍚堣〃涓笉瀛樺湪鏃惰嚜琛岀敓鎴?鐪嬩技鍚堢悊"鐨勬柊缁勫悎鈥斺€斾繚鎸佸彲瑙ｉ噴銆佸彲澶嶇幇銆?- 缁勫悎澶辫触鍙繑鍥?blocked 鍘熷洜锛屼笉娑堣€楁潗鏂欙紙鍙噸璇曪級锛岄櫎闈為厤鏂规敞鏄庢秷鑰椼€?
```

**4.11 M50_主循环** · 归属：官方核心 · 溯源：04_模块库/通用类/M50_主循环.md

```markdown
# 妯″潡 M50 路 涓诲惊鐜?
> 绫诲埆锛氶€氱敤锝滄潵婧愶細鏍稿績锝滄寕杞界偣锛氳皟搴﹀櫒锛堝叏灞€锛夛綔渚濊禆锛歁00锝滆渚濊禆锛歁80

```yaml
machine_contract:
  conformance: "L2"
  schema: "1"
  id: M50
  name: 涓诲惊鐜?  category: 閫氱敤
  layer: 璋冨害鍣?  inputs: [M00]
  outputs: [intent_id, mode, text]
  events:
    publish: [intent_received]
    subscribe: []
  interfaces: []
  world_model:
    abstract_state:
      variables:
        - name: pipeline
          kind: string
          source: M50
          slot: data_bus.active_pipeline
          note: 褰撳墠瑁呴厤绠＄嚎 id
        - name: tick
          kind: integer
          source: 閫氱敤:M10
          slot: WorldState.time.tick
          note: 鏃堕棿鎺ㄨ繘鑺傛媿锛汳50 鍙
        - name: phase
          kind: string
          source: M50
          slot: data_bus.round.phase
          note: 涓诲惊鐜娊璞＄浉浣?        - name: phase_trace
          kind: array
          item_kind: string
          source: M50
          slot: data_bus.round.phase_trace
          note: 涓诲惊鐜浉浣嶈建杩癸紱鏃х浉浣嶆寜杩佺Щ椤哄簭杩藉姞
      initial:
        pipeline: P01
        tick: 0
        phase: begin
        phase_trace: []
    transition:
      initial_phase: begin
      phases:
        - phase: begin
          next: run
          guard: 鍥炲悎寮€濮嬪苟蹇収 M00 鏁版嵁妲?          writes: []
        - phase: run
          next: end
          guard: 鎸?02 搂6 鎵ц瀹樻柟鏍稿績涓庣ぞ鍖哄寘鍚堝苟椤哄簭
          writes: [memory.working]
        - phase: end
          next: archive
          guard: I2 鏍稿績鍥哄畾缁撴瀯/瀛楁涓€鑷存€ф牎楠岄€氳繃
          writes: []
        - phase: archive
          next: roll
          guard: end 閫氳繃鍚庢墽琛屽洖鍚堟湯璁板繂鍐欏洖
          writes: [memories.memory.episodic.items, memories.memory.semantic.facts]
        - phase: roll
          next: begin
          guard: 鍥炲嵎鑷?begin 蹇収骞惰繘鍏ヤ笅涓€鍥炲悎
          writes: [memory.working]
    invariants:
      - "鎶借薄鐘舵€佸彉閲忓繀椤绘槸 world_model.abstract_state 鏄惧紡澹版槑鐨勬湁闄愰泦"
      - "tick 鍗曡皟涓嶅噺"
      - "phase 鍙湪 begin/run/end/archive/roll 鏈夐檺闆嗗悎鍐呰縼绉?
      - "姣忎釜 phase 鏄惧紡澹版槑 next锛岃縼绉诲浘浠?initial_phase 鍏ㄥ彲杈?
      - "闈?M50 妯″潡涓嶅緱鐩村啓 M00 鏁版嵁妲?
    checks:
      - kind: finite_phase
        field: phase
        values: [begin, run, end, archive, roll]
      - kind: monotonic
        field: tick
      - kind: finite_sequence
        field: phase_trace
        values: [begin, run, end, archive, roll]
  io_types:
    outputs:
      intent_id: untyped
      mode: untyped
      text: untyped
    inputs:
      M00: state
```

## 1. 鑱岃矗

鍥炲悎璋冨害鍣ㄣ€傛寜娉ㄥ唽琛?搂6 鎵ц椤哄簭锛堝畼鏂规牳蹇冭閰?10 姝ワ紝鐪熺浉婧愯 02 搂6锛変緷搴忛┍鍔ㄥ悇灞傛ā鍧楋紱瑁呴厤绀惧尯棰嗗煙鍖呭悗鎸夊寘绱㈠紩鍔ㄦ€佸悎骞讹紙R3锛夈€傚洖鍚堢粨鏉熷洖鍗峰苟杩涘叆涓嬩竴鍥炲悎銆備富寰幆鍐冲畾"璋佸厛璺戙€佽皝鍚庤窇銆佷綍鏃剁粨绠?銆?
## 2. 鎵ц椤哄簭锛堝畼鏂规牳蹇?10 姝ヤ负鐪熺浉婧愶紝瑙?02 搂6锛涚ぞ鍖哄寘鎸夌储寮曞姩鎬佸悎骞讹級

瀹樻柟鏍稿績瑁呴厤锛圥01锛夌殑鎵ц椤哄簭浠?**02_鑱斿姩娉ㄥ唽琛?md 搂6 涓哄敮涓€鐪熺浉婧愶紙I5锛?*锛屾湰妯″潡涓嶅啀缁存姢闈欐€佺紪鍙锋竻鍗曪紝閬垮厤鍙屾簮婕傜Щ銆傝閰嶇ぞ鍖洪鍩熷寘鍚庯紙P02 鏍″洯鎯呮劅 / P03 瑗垮够鐢熷瓨锛夛紝鎸夊寘绱㈠紩灏嗛鏉愭ā鍧楀悎骞惰繘瀵瑰簲灞備綅锛圧3锛夛紝鐢熸垚鏈€缁堟墽琛岄『搴忋€?
瀹樻柟鏍稿績瑁呴厤锛圥01锛?0 姝ラ€熻锛堜粎渚夸簬闃呰锛岀湡鐩告簮浠?02 搂6 涓哄噯锛夛細

```text
 1. M00 鏁版嵁缁撴瀯锛堝垵濮嬪寲锛? 2. M50 涓诲惊鐜紙璋冨害寮€濮嬶級
 3. 閫氱敤:M10 鏃堕棿鎺ㄨ繘
 4. M20 涓栫晫鐭ヨ瘑搴擄紙甯歌瘑瑁呰浇锛? 5. M23 璁ょ煡杈圭晫锛堣瑙掕鍓級
 6. 浜嬩欢:M22 / M06 / M13锛堜簨浠剁敓浜э級
 7. M12 NPC 瀵硅瘽锛堜氦浜掓墽琛岋級
 8. M20 / M24锛堝彊浜嬬礌鏉愪笌缁勫悎鏍￠獙锛? 9. M80 杈撳嚭鐢熸垚鍣紙娓叉煋杈撳嚭锛?10. M50锛堝洖鍗蜂笅涓€鍥炲悎锛?```

> **绀轰緥闈炵湡鐩告簮**锛氫笂杩?10 姝ヤ负 02 搂6 鐨勫揩鐓у壇鏈紝浠呬緵鏈ā鍧楀揩閫熸煡闃咃紱涓€鍒囧啿绐佷互 02 搂6 涓哄噯锛圛5 鍐茬獊瑁佸喅锛夈€傜ぞ鍖哄寘鍚堝苟绀烘剰锛堟渶缁堥『搴忎互鍚勫寘 README 涓?02 搂8 鐧昏涓哄噯锛夛細P02 鏍″洯鎯呮劅灏嗘儏鎰?M22 / M40 / M41 / M43 / M55 / M65 杩藉姞鑷?P40/P60 灞傦紝P03 瑗垮够鐢熷瓨灏?M01 / M02 / M19 / M08 / M18 / M13 / M04 / M11 / M17 / M07 / M09 / M14 / M15 / M16 / 鐢熷瓨:M10 杩藉姞鑷冲搴斿眰浣嶃€?
## 3. 璋冨害瑙勫垯

```yaml
scheduler:
  灞傞棿鍚屾: 姣忎竴姝ョ瓑寰呬笂涓€姝ュ畬鎴愶紙鍚屾涓茶锛夛紝淇濊瘉鏁版嵁鍥犳灉
  灞傚唴: 璇ュ眰澶氭ā鍧楁寜娉ㄥ唽琛?available鈫抋ctive 杩囨护鍚庢墽琛?  璺宠繃: 妯″潡澹版槑 skip锛堟潯浠朵笉婊¤冻锛夆啋 璺宠繃骞惰 skip_reason
  寮傚父: 鍗曟ā鍧楀紓甯镐笉涓柇鏁磋疆锛涙崟鑾峰悗璁?error_log锛屽洖鍚堢户缁?  绠＄嚎鍒囨崲: 鎹㈢敤 P02/P03 鏃跺悓姝ュ垏鎹㈡寕杞借〃涓庢墽琛岄『搴?```

## 4. 鍥炲悎鐢熷懡鍛ㄦ湡

```yaml
round:
  begin:   蹇収锛圡00 鏁版嵁妲斤級
  run:     鎸夋敞鍐岃〃 搂6 椤哄簭鎵ц锛堝畼鏂规牳蹇?10 姝?+ 绀惧尯鍖呭姩鎬佸悎骞讹級
  end:     鏍￠獙涓€鑷存€э紙I2 鏍稿績鍥哄畾锛氱粨鏋?瀛楁涓嶆紓绉伙級
  archive: 鍥炲悎鏈蹇嗗綊妗ｏ紙memory_writeback 涓夎鍒欙紝瑙佷笅锛夆€斺€?end 閫氳繃鍚庢墽琛?  roll:    鍥炲嵎鑷?begin 蹇収

memory_writeback:  # 鍥炲悎鏈蹇嗗啓鍥炰簨浠讹紙v0.5.0 T3锛涚粡 M00 鏁版嵁妲芥€荤嚎鍙戝竷锛屼粎 M50 浜?archive 姝ヨЕ鍙戯級
  working鈫掓竻鐞?    # working 灞傞殢鍥炲悎蹇収婊氬姩锛歟nd 鍚庢竻绌洪噸缃湰鍥炲悎鎰熺煡锛屼笉璺ㄥ洖鍚堟粸鐣?  episodic鈫掑啓鍥?   # 閲嶈浜嬩欢鍐欏洖 episodic锛氬懡涓?{鎯呮劅闂幆銆佸叧绯诲彉鍖栥€佷笘鐣屼簨浠躲€佹浜?绂诲埆} 鐨勬潯鐩?                   # 甯?tick 杩藉姞鑷?memories/memory.episodic.items锛圡13/M23 浜у嚭锛孧50 褰掓。锛?  semantic鈫掓矇娣€:   # episodic 鎻愮偧娌夋穩 semantic锛氳法鍥炲悎绋冲畾鐨勫叧绯讳笌璁惧畾浜嬪疄鎻愮偧涓?semantic.facts
                   # 锛堥暱鏈熻瀹氫笌甯歌瘑锛汳23 璇诲彇杩囨护锛孧65/M80 鍙娑堣垂锛?  绾︽潫:            # 浠呭啓 M00 澹版槑鐨?memories/memory 妲斤紙I4 鏁版嵁闅旂锛夛紱娑堣垂鏂瑰彧璇伙紝
                   # 鐩村啓浠栨ā鍧?memory 瀛楁 = DATA_SLOT_VIOLATION
```

## 5. 杩濅緥涓庤竟鐣?
- 绂佹浠讳綍妯″潡鍦?step 涔嬪鑷瑙﹀彂鍏朵粬妯″潡閫昏緫锛堝繀椤荤粡鐢辨敞鍐岃〃璁㈤槄/鎸傝浇锛夈€?- 姝诲惊鐜槻鎶わ細鍗曞洖鍚堟墽琛岃秴鏃?姝ユ暟瓒呴檺 鈫?M50 寮哄埗鎵撴柇骞跺洖鍗枫€?
```

**4.12 M80_输出生成器** · 归属：官方核心 · 溯源：04_模块库/通用类/M80_输出生成器.md

```markdown
# 妯″潡 M80 路 杈撳嚭鐢熸垚鍣?
> 绫诲埆锛氶€氱敤锝滄潵婧愶細鏍稿績锝滄寕杞界偣锛歅80 杈撳嚭鍛堢幇锛坅ctive锛夛綔渚濊禆锛歁50銆佷簨浠?M22锝滆渚濊禆锛氭棤

```yaml
machine_contract:
  conformance: "L2"
  schema: "1"
  id: M80
  name: 杈撳嚭鐢熸垚鍣?  category: 閫氱敤
  layer: P80
  inputs: [M50, 浜嬩欢:M22]
  outputs: []
  events:
    publish: []
    subscribe: []
  interfaces: []
  io_types:
    outputs: {}
    inputs:
      M50: untyped
      浜嬩欢:M22: untyped
```

## 1. 鑱岃矗
灏?P70 鍙欎簨绱犳潗娓叉煋涓烘渶缁堝彲璇绘枃鏈€傝繖鏄川妫€闂ㄧ殑**鎵ц鍣?*锛氳緭鍑哄厛杩囩粨鏋勯棬锛堢‖ 路 鍏ㄥ煙閫氱敤锛夛紝鍐嶆寜妗ｄ綅鍔犺浇椋庢牸闂紙杞?路 妗ｄ綅 DNA锛涙。浣嶆湭閰嶇疆 DNA 鏃朵粎杩囩粨鏋勯棬锛夛紝璐ㄩ噺鍒嗘。鍚庢斁琛屻€佽嚜绾犳垨閲嶅啓銆?
## 2. 璐ㄦ鍙岄棬锛?026-09-08 閲嶆瀯锛氶鏍奸棬妗ｄ綅鍖栵紝鍙彉鐗╀笉鍏ュ崗璁眰锛?### 2.1 缁撴瀯闂紙纭?路 鍏ㄥ煙閫氱敤 路 鍙満鍣ㄦ牳楠岋級
- 缂栧彿鍚堟硶锛氭枃涓?Mxx/Pxx 鍏ㄩ儴鍦ㄥ唽锛?2 鑱斿姩娉ㄥ唽琛級锛屼笉鍦ㄥ唽鍗崇紪閫?= fail
- 璧勪骇閿瓨鍦細寮曠敤璧勪骇閿彲缁?asset_get 鍙栧埌锛屾偓绌?= fail
- 灞傜骇瀹屾暣锛氱礌鏉愯鐩栧綋鍓嶅洖鍚堢绾胯姹傛锛圥00鈥揚80锛?- 鏈涓€鑷达細涓庡崗璁湳璇〃涓€鑷达紝涓嶆贩鐢?- 鏃犺法灞傜洿鍐欙細绱犳潗鏃犺秺灞傝緭鍑猴紙M23 瑙嗚绾緥鍓嶇疆锛岄殣钘忓煙鐩磋堪 = fail锛?### 2.2 椋庢牸闂紙杞?路 妗ｄ綅 DNA 路 鍙厤缃級
- 娓叉煋鍓嶅姞杞藉綋鍓嶆。浣?DNA 閰嶇疆锛堣祫浜ч敭 STYLE_DNA 鎴栨。浣?protocol.yaml dna 瀛楁锛夛紱
- 妗ｄ綅 DNA 鐢辩敤鎴?鍩熷寘鑷畾涔夆€斺€?*鍗忚灞備笉鍐呭祵浠讳綍鍥哄畾椋庢牸鏉＄洰**锛堣嚜瀹氫箟瑙勮寖涓庣ず渚嬫。瑙?`05_璧勪骇搴?鐢ㄦ埛鑷畾涔?STYLE_DNA.md`锛涗綔鑰呴粯璁ゆ枃瀛︽。鏈簮锛氭牎鍥儏鎰熷寘璧勪骇 5.11锛夛紱
- 妗ｄ綅鏃?DNA 閰嶇疆鏃讹紝浠呰繃缁撴瀯闂ㄥ嵆鏀捐锛堟枃椋庣敱杩愯鏂硅嚜鎷咃級銆?
## 3. 璐ㄦ闂紙璐ㄩ噺闂ㄧ 路 澹版槑寮?gate_action 娴佹按绾匡級
```yaml
gate:                      # 鍙岄棬鍒ゅ畾锛?.1 缁撴瀯闂?+ 2.2 妗ｄ綅 DNA锛?  pass: 缁撴瀯闂ㄥ叏杩?涓旓紙鏃犳。浣?DNA 鎴?妗ｄ綅 DNA 绗﹀悎 鈮?妗ｄ綅闃堝€硷級鈫?鐩存帴杈撳嚭
  warn: 缁撴瀯闂ㄥ叏杩?涓?妗ｄ綅 DNA 閮ㄥ垎绗﹀悎锛?鈥? 鏉℃垨妗ｄ綅鑷畾闃堝€硷級鈫?鑷籂鍚庤緭鍑猴紙鏍囨敞淇鐐癸級
  fail: 缁撴瀯闂ㄨ繚渚嬶紙纭敊锛夋垨 妗ｄ綅 DNA 杩炵画涓嶇锛?4 鏉℃垨妗ｄ綅鑷畾闃堝€硷級鈫?鏁存閲嶅啓锛?        杩炵画 3 娆?fail 闄嶇骇涓虹櫧鎻忔ā寮忥紙淇濆簳鍙锛屼粎缁撴瀯闂級
鍓嶇疆鏍￠獙: 绱犳潗蹇呴』宸茶繃 M23 璁ょ煡杈圭晫瑁佸壀锛堥殣钘忓煙鐩磋堪 = fail锛岃瑙掔邯寰嬶級
gate_action:               # 澹版槑寮忛棬绂佹祦姘寸嚎锛坴0.5.0 T4锛涘榻?NovelClaw 鍙娴嬭繍琛屾€濇兂锛?  pass: [direct]           # 鐩存帴杈撳嚭锛堥浂骞查鏀捐锛?  warn: [self_correct, log_revision]    # 鑷籂鍚庤緭鍑猴紝淇鐐硅鍏ュ喅绛栬褰?  fail: [rewrite, retry_limit: 3, fallback: white_sketch]   # 鏁存閲嶅啓锛涜繛缁?3 娆￠檷绾х櫧鎻忥紙淇濆簳鍙锛?璁板繂璇诲彇: 缁?M00 鏁版嵁妲藉彧璇绘帴鍙ｆ秷璐逛笁灞傝蹇嗏€斺€攅pisodic 鏍￠獙鍙欎簨涓庡叧绯诲彶涓€鑷存€с€?          璇箟 semantic 鏍￠獙闀挎湡璁惧畾涓嶅啿绐侊紙v0.5.0 T3 鍙澹版槑锛夛紱鍙涓嶆敼鐘舵€侊紙I4锛夛紝
          璁板繂鏀瑰啓涓€寰嬩氦 M50 鍥炲悎鏈?memory_writeback 澶勭悊
gate_decision_record:      # 鍐崇瓥璁板綍锛堢粨鏋勫寲琛岋紝璧扮郴缁熸棩蹇楃嫭绔嬮€氶亾锛屼笉杩涘彊浜嬫枃鏈€斺€旇 搂5锛?  鏍煎紡: gate|<娴佹按鍙?|tick|妗ｄ綅(pass/warn/fail)|鍛戒腑椤?缁撴瀯椤?DNA鏉?|淇鐐箌閲嶅啓娆℃暟|fallback
  鏍蜂緥: gate|014|t_2042|warn|S1,S3,D1,D3,D5|L7 鐩磋堪鏀圭墿浠跺寲|0|none
        gate|015|t_2043|fail|S2|闅愯棌鍩熺洿杩皘3|white_sketch
```
## 4. 杈撳嚭鏍煎紡

- 绀惧尯鏍″洯鎯呮劅鍖呴鏉愭祦锛氱煭娈佃惤 + 鐧芥弿/璇楀寲浜ゆ浛 + 鏋佺畝瀵硅瘽锛圥02 椋庢牸娓叉煋锛夈€?- 绀惧尯瑗垮够鐢熷瓨鍖呴鏉愭祦锛氭垬鏂?鐢熷瓨缁撶畻鍙鍖栵紝姝讳骸鎻忚堪鐢?death_descriptions 姹狅紙P03锛夈€?- 閫氱敤鍥為€€锛氭棤绠＄嚎鏍囨敞鏃舵寜 P01 涓€ф覆鏌撱€?
## 5. 杩濅緥涓庤竟鐣?
- 杈撳嚭瀛楁暟涓婇檺鐢辩绾垮弬鏁版帶鍒讹紱绂佹杈撳嚭 JSON/YAML 鍘熷缁撴瀯锛堝彧杈撳嚭鍙欎簨鏂囨湰锛夈€?- 鐜╁鍙鍐呭涓庣郴缁熺粨绠楀唴瀹瑰垎绂伙細绯荤粺鏃ュ織璧扮嫭绔嬮€氶亾锛屼笉杩涘彊浜嬫枃鏈€?- 闂ㄧ涓?*鍞竴杈撳嚭闂?*锛圛2 鏍稿績鍥哄畾锛夛細鍙欎簨锛圡80锛変笌鎶€鏈枃妗ｏ紙P90 缁?M80锛変骇鍑哄潎涓嶅彲缁曡繃鏈?gate銆?- gate 鍐崇瓥璁板綍锛埪? gate_decision_record 鏍煎紡锛夎蛋绯荤粺鏃ュ織鐙珛閫氶亾锛岀姝㈡贩鍏ュ彊浜?鏂囨。姝ｆ枃銆?
```

**4.13 M90_技术文档结构** · 归属：官方核心 · 溯源：04_模块库/技术文档类/M90_技术文档结构.md

```markdown
# 妯″潡 M90 路 鎶€鏈枃妗ｇ粨鏋?
> 绫诲埆锛氭妧鏈枃妗ｏ綔鏉ユ簮锛氶鍩熸紨绀猴紙P90 瀹炶瘉锛岀ぞ鍖烘墿灞曠ず渚嬶級锝滄寕杞界偣锛歅90锛坅ctive锛宒efault锛夛綔渚濊禆锛歁00锝滆渚濊禆锛歁80
> 鐢ㄩ€旓細README銆屾墿灞曟柊棰嗗煙涓夋涔嬧憼銆嶇殑瀹炶瘉妯″潡鈥斺€旇瘉鏄?04_妯″潡搴撳彲鏃犳崯鎺ュ叆闈炲彊浜嬮鍩熸ā鍧楋紙verify.sh 浠呰姹傚彊浜嬩簲绫诲埆鍩虹嚎涓嬮檺锛屾柊绫诲埆/鏂版ā鍧楄嚜鍔ㄧ撼鍏ヨ鏁帮紝鍙涓嶅噺锛夈€?
```yaml
machine_contract:
  conformance: "L2"
  schema: "1"
  id: M90
  name: 鎶€鏈枃妗ｇ粨鏋?  category: 鎶€鏈枃妗?  layer: P90
  inputs: [M00]
  outputs: [DocState, doc_delta]
  events:
    publish: [doc_structure_ready, doc_delta_committed]
    subscribe: [intent_received]
  interfaces: []
  io_types:
    outputs:
      DocState: untyped
      doc_delta: untyped
    inputs:
      M00: state
```

## 1. 鑱岃矗
鎶娿€岃嚜鐒惰瑷€鎰忓浘锛堝锛氬啓涓€浠?API 杩佺Щ璇存槑锛夈€嶈В鏋愪负鎶€鏈枃妗ｇ殑缁撴瀯鍖栬绱狅細鏍囬灞傜骇銆佺珷鑺傞鏋躲€佹湳璇〃銆佽〃鏍?/ 浠ｇ爜鍧楀紩鐢ㄣ€佷慨璁㈣褰曪紱鎸夎祫浜ч敭 `TECH_TEMPLATES` 閫夋嫨绔犺妭妯℃澘銆乣TECH_RULES` 杩囪鑼冧竴鑷存€ф牎楠屻€傛槸 P90 鎶€鏈枃妗ｇ敓鎴愮绾匡紙P00 楠ㄦ灦鍦ㄩ潪鍙欎簨棰嗗煙鐨勫疄渚嬭閰嶏級鐨勯鍩熻杞芥ā鍧椼€?
## 2. 鍗忚澹版槑锛?1 搂2 妯″潡鍗忚锛?```yaml
Module:
  id: M90
  name: 鎶€鏈枃妗ｇ粨鏋?  layer: P90
  inputs: [M00, intent]          # 鏁版嵁妲藉氨缁?+ 鐢ㄦ埛鎰忓浘杞借嵎
  outputs: [DocState, doc_delta] # 鏂囨。缁撴瀯鐘舵€?+ 绔犺妭澧為噺
  events:
    publish: [doc_structure_ready, doc_delta_committed]
    subscribe: [intent_received]
  core:
    assets: [TECH_TEMPLATES, TECH_RULES]   # I4锛氫粎缁忎簲鎺ュ彛璁块棶锛岀姝㈢洿璇?    logic:
      瑙ｆ瀽: 鎰忓浘 鈫?鏂囨。绫诲瀷鍒ゅ畾锛坓uide/reference/tutorial/note锛夆啋 閫?TECH_TEMPLATES 楠ㄦ灦
      瑁呴厤: 绔犺妭 鈫?鏈/琛ㄦ牸/浠ｇ爜鍧楀紩鐢ㄧ櫥璁?鈫?鏇存柊 DocState
      鏍￠獙: 鎸?TECH_RULES 妫€鏌ョ粨鏋勪竴鑷存€э紙绔犺妭闂悎/鏈缁熶竴/淇璁板綍锛?  replaceable: true
```

## 3. 鏁版嵁妲藉绾︼紙鎵╁睍 M00 data_bus 路 鎶€鏈枃妗ｅ煙锛?```yaml
DocState:
  title: string
  doc_type: guide|reference|tutorial|note
  chapters: [{id, heading, level, body_refs[], status}]
  terms: {term: {def, first_use_chapter}}   # 鏈琛?  refs: {link_refs[], code_refs[]}          # 寮曠敤闂悎鐧昏
  revision: [{ver, date, change}]           # 淇璁板綍
```

## 4. 浜嬩欢鑱斿姩
- publish `doc_structure_ready`锛氱粨鏋勯鏋跺氨缁紝閫氱煡 M80 杩涘叆娓叉煋璐ㄦ銆?- subscribe `intent_received`锛氭帴鏀剁敤鎴锋剰鍥句綔涓?P90 瑁呰浇杈撳叆锛堢櫥璁颁簬 02 搂7.4锛夈€?
## 5. 鏍稿績閫昏緫锛堜吉浠ｇ爜锛?```
1. intent_received 鈫?doc_type = classify(intent)
2. skeleton = asset_get(TECH_TEMPLATES, doc_type)      # 鍙栫珷鑺傞鏋?3. chapters = expand(skeleton, intent)                 # 鎷嗙珷/鑺?灏忚妭
4. for each draft: doc_delta = compose(draft)          # 鐗囨鐢熶骇锛圥30 浣嶏級
5. tech_review: check(TECH_RULES, DocState)            # 瑙勮寖涓€鑷存€?6. publish doc_structure_ready
```

## 6. 涓嶅彉寮忛伒瀹堬紙01 搂5锛?- I1 涓夋浜ゅ垎绂伙細鍙０鏄?缁撴瀯鑳藉姏"锛屼笉鎸佹湁绠＄嚎椤哄簭锛堥『搴忓湪 P90锛変笌鏁版嵁鍐呭锛堝唴瀹瑰湪 05 璧勪骇锛夈€?- I2 鏍稿績鍥哄畾锛氬鐢?M00 鏁版嵁妲?/ M50 涓诲惊鐜?/ M80 杈撳嚭闂紝鏈浛鎹换浣曟牳蹇冩ā鍧椼€?- I3 閫氫俊濂戠害锛氫粎缁?DocState 鏁版嵁妲戒笌 doc_structure_ready 浜嬩欢閫氫俊銆?- I4 鏁版嵁闅旂锛歍ECH_TEMPLATES / TECH_RULES 鍙粡 asset_get / asset_query 璁块棶銆?- I5 鐪熺浉鍞竴锛氭寕杞戒笌鎵ц椤哄簭浠?02_鑱斿姩娉ㄥ唽琛?搂7 鐧昏涓哄噯锛岀姝㈢‖缂栫爜銆?
## 7. 涓?P90 鐨勫叧绯?P90 涔濆眰涓紝M90 鎵挎媴瑁呰浇锛圥00 浣嶉鏋惰В鏋愶級銆佺敓浜э紙P30 浣嶇墖娈碉級銆佸喅绛栵紙P40 浣嶆ā鏉块€夋嫨锛夈€佽閰嶏紙P50 浣嶇珷鑺傜粍瑁咃級銆佷竴鑷存€э紙P60 浣嶈法绔犳牎楠岋級绛変綅鑱岃矗锛涜緭鍑哄眰 P80 浠嶇敱鏍稿績 M80 璐ㄦ娓叉煋锛坓ate 鍞竴鍑哄彛锛夈€
```

**4.14 M97_术语管理** · 归属：技术文档域包（自带） · 溯源：community/技术文档域包/modules/M97_术语管理.md

```markdown
# 妯″潡 M97 路 鏈绠＄悊

> 绫诲埆锛氭妧鏈枃妗ｏ綔鏉ユ簮锛氱ぞ鍖猴紙鎶€鏈枃妗ｅ煙鍖呰嚜甯︼紝M91-99 绀惧尯娈碉級锝滄寕杞界偣锛歅40锛坅ctive锛宒efault锛夛綔渚濊禆锛歁90 鎶€鏈枃妗ｇ粨鏋勩€丮00锝滆渚濊禆锛歁80
> 鐢ㄩ€旓細README銆屾墿灞曟柊棰嗗煙涓夋涔嬧憼銆嶇ぞ鍖?techdoc 鍩熷寘棣栨ā鍧椻€斺€斿湪瀹樻柟 M90锛堟妧鏈枃妗ｇ粨鏋勶級涔嬩笂缁存姢 DocState.terms 鏈琛紙瀹氫箟/棣栨浣跨敤绔犺妭/缁熶竴鎬ф牎楠岋級锛孧90 涓撴敞缁撴瀯楠ㄦ灦銆丮97 涓撴敞鏈涓€鑷达紝I1 姝ｄ氦鍒嗗伐銆?
```yaml
machine_contract:
  conformance: "L2"
  schema: "1"
  id: M97
  name: 鏈绠＄悊
  category: 鎶€鏈枃妗?  layer: P40
  inputs: [M90, M00]
  outputs: [term_delta]
  events:
    publish: [term_synced, term_conflict_detected]
    subscribe: [doc_structure_ready, term_conflict_detected]
  interfaces: []
  io_types:
    outputs:
      term_delta: untyped
    inputs:
      M90: untyped
      M00: state
```

## 1. 鑱岃矗
缁存姢鎶€鏈枃妗ｇ殑鏈琛ㄤ竴鑷存€э細浠?DocState.terms 璇诲彇鏈鏉＄洰锛圡90 缁撴瀯鐢熶骇鏃剁櫥璁帮級锛屽仛棣栨浣跨敤绔犺妭鏍囨敞涓庡畾涔夎ˉ鍏紱妫€娴嬪悓涓€鏈澶氬畾涔?棣栫敤鏈畾涔夌瓑鍐茬獊锛坱erm_conflict_detected锛夛紱鍙戝竷 term_synced 渚?M80 璐ㄦ鍙傝€冦€傛槸鏈寘锛堟妧鏈枃妗ｉ鏉愬寮猴級鐩稿瀹樻柟 M90 鐨勫鍊间綅鈥斺€擬90 璐熻矗楠ㄦ灦锛孧97 璐熻矗鏈鍩熴€?
## 2. 鍗忚澹版槑锛?1 搂2 妯″潡鍗忚锛?```yaml
Module:
  id: M97
  name: 鏈绠＄悊
  layer: P40
  inputs: [M90, M00, intent]
  outputs: [term_delta, term_status]
  events:
    publish: [term_synced, term_conflict_detected]
    subscribe: [doc_structure_ready, term_conflict_detected]
  core:
    assets: []                     # 闆堕鏉愯祫浜э紙鏈哄埗澧炲己锛涘悓閫氱敤鍖?M93-96 鍏堜緥锛?    logic:
      鐧昏: doc_structure_ready 鈫?鎵弿绔犺妭姝ｆ枃 鈫?棣栨浣跨敤鏈鐧昏 first_use_chapter
      琛ュ畾涔? 鏈鏃犲畾涔?鈫?鏌ュ凡鏈夋湳璇〃 / 鐣欏緟浜哄伐锛坱erm_status=pending_definition锛?      鏍￠獙: 澶氬畾涔夊悓涓€鏈 / 棣栫敤鏈畾涔?鈫?term_conflict_detected
      鍚屾: 鏍￠獙閫氳繃 鈫?term_synced锛圖ocState.terms 鏀舵暃锛?  replaceable: true
```

## 3. 鏁版嵁妲藉绾︼紙鎵╁睍 M90 DocState 路 鏈鍩燂級
```yaml
term_delta:
  term: string
  first_use_chapter: string
  definition: string          # 绌?= 寰呰ˉ
  status: ok|pending_definition|conflict
term_status:
  total: int
  defined: int
  conflicts: [string]
```

## 4. 浜嬩欢鑱斿姩
- subscribe `doc_structure_ready`锛圡90 鍙戝竷锛夛細缁撴瀯楠ㄦ灦灏辩华 鈫?M97 鎵弿鐧昏鏈銆?- subscribe `term_conflict_detected`锛氭湰妯″潡鑷鍙戠幇澶氬畾涔?鏈畾涔?鈫?鍐呴儴鐘舵€佹爣璁般€?- publish `term_synced`锛氭湳璇〃鏀舵暃 鈫?M80 璐ㄦ鍙鏈涓€鑷存€с€?
## 5. 鏍稿績閫昏緫锛堜吉浠ｇ爜锛?```
1. doc_structure_ready 鈫?for chapter: scan(chapter.body) 鈫?collect terms
2. term not in DocState.terms 鈫?add with first_use_chapter, definition=""
3. term.definition=="" and known 鈫?backfill锛沞lse status=pending_definition
4. dup definition 鈫?status=conflict 鈫?publish term_conflict_detected
5. no conflict 鈫?publish term_synced
```

## 6. 涓嶅彉寮忛伒瀹堬紙01 搂5锛?- I1 涓夋浜ゅ垎绂伙細鍙０鏄庢湳璇兘鍔涳紝涓嶆寔绠＄嚎椤哄簭锛堥『搴忓湪 P06 绠＄嚎锛変笌鍐呭锛圡90 浜?DocState锛夈€?- I2 鏍稿績鍥哄畾锛氫緷璧?M90/M00 鏁版嵁妲斤紝鏈浛鎹㈡牳蹇冩ā鍧楋紙M90 瀹樻柟浣嶄笉鍔級銆?- I3 閫氫俊濂戠害锛氫粎缁?term_delta / term_status 涓?term_synced 浜嬩欢閫氫俊銆?- I4 鏁版嵁闅旂锛氭棤鑷湁璧勪骇锛堥浂璧勪骇鏈哄埗澧炲己锛夈€?- I5 鐪熺浉鍞竴锛氭寕杞戒笌鐧昏浠?02 搂8.5 + registry protocols[] 涓哄噯锛堟湰鍖呯 5 鏉℃姇褰憋級銆?
## 7. 涓庡畼鏂归摼鐨勫叧绯?鏈ā鍧楁槸 M90锛堝畼鏂癸紝鎸?P90 浣嶏級鐨勯鏉愬寮衡€斺€擬90 浜?DocState锛堝惈 terms 闆忓舰锛夛紝M97 鎸?P40 浣嶅仛鏈鍩熸繁鍖栵紱涓嶅鍒?M90 姝ｆ枃锛坈ore_modules 渚濊禆寮曠敤锛孖5锛夛紝鏄€屾墿灞曟柊棰嗗煙涓夋銆嶇ぞ鍖鸿嚜甯︽ā鍧楃ず鑼冦€?
```

**4.15 M98_修订记录** · 归属：技术文档域包（自带） · 溯源：community/技术文档域包/modules/M98_修订记录.md

```markdown
# 妯″潡 M98 路 淇璁板綍

> 绫诲埆锛氭妧鏈枃妗ｏ綔鏉ユ簮锛氱ぞ鍖猴紙鎶€鏈枃妗ｅ煙鍖呰嚜甯︼紝M91-99 绀惧尯娈碉級锝滄寕杞界偣锛歅60锛坅ctive锛宒efault锛夛綔渚濊禆锛歁90 鎶€鏈枃妗ｇ粨鏋勩€丮00锝滆渚濊禆锛歁80
> 鐢ㄩ€旓細README銆屾墿灞曟柊棰嗗煙涓夋涔嬧憼銆嶇ぞ鍖?techdoc 鍩熷寘娆℃ā鍧椻€斺€旂淮鎶?DocState.revision 淇璁板綍锛堢増鏈彿/鍙樻洿鏃ュ織/鍥炴函锛夛紝M90 涓撴敞缁撴瀯楠ㄦ灦銆丮98 涓撴敞鍙樻洿杩借釜锛孖1 姝ｄ氦鍒嗗伐銆?
```yaml
machine_contract:
  conformance: "L2"
  schema: "1"
  id: M98
  name: 淇璁板綍
  category: 鎶€鏈枃妗?  layer: P60
  inputs: [M90, M00]
  outputs: [revision_entry, revision_log]
  events:
    publish: [revision_recorded]
    subscribe: [doc_structure_ready, doc_delta_committed]
  interfaces: []
  io_types:
    outputs:
      revision_entry: untyped
      revision_log: untyped
    inputs:
      M90: untyped
      M00: state
```

## 1. 鑱岃矗
缁存姢鎶€鏈枃妗ｇ殑淇鍘嗗彶锛歁90 姣忎骇鍑虹粨鏋勫閲忥紙doc_delta锛夋垨姝ｆ枃鍙樻洿锛坉oc_delta_committed锛夋椂锛孧98 杩藉姞淇鏉＄洰锛堢増鏈彿閫掑/鍙樻洿鎽樿/鏃ユ湡/浣滆€咃級锛岀淮鎶ゅ彲鍥炴函鐨勫彉鏇存棩蹇楋紙revision_log锛夛紱渚?M80 娓叉煋銆屼慨璁㈣褰曘€嶇珷鑺備笌璇昏€呰拷婧€傛槸鏈寘鐩稿瀹樻柟 M90 鐨勫鍊间綅銆?
## 2. 鍗忚澹版槑锛?1 搂2 妯″潡鍗忚锛?```yaml
Module:
  id: M98
  name: 淇璁板綍
  layer: P60
  inputs: [M90, M00, intent]
  outputs: [revision_entry, revision_log]
  events:
    publish: [revision_recorded]
    subscribe: [doc_structure_ready, doc_delta_committed]
  core:
    assets: []                     # 闆堕鏉愯祫浜э紙鏈哄埗澧炲己锛?    logic:
      鍙樻洿: doc_delta_committed 鈫?姣旇緝鍓嶇増 DocState 鈫?鎻愬彇鍙樻洿鐐?      鐧昏: 鐗堟湰鍙?v{n+1} + 鍙樻洿鎽樿 + date + author 鈫?revision_log 杩藉姞
      鍥炴函: 鎸夌増鏈彿鍙栧巻鍙插揩鐓?鈫?渚?diff 灞曠ず
      鍙戝竷: revision_recorded 鈫?M80 娓叉煋淇绔犺妭
  replaceable: true
```

## 3. 鏁版嵁妲藉绾︼紙鎵╁睍 M90 DocState 路 淇鍩燂級
```yaml
revision_entry:
  ver: string          # v1.0 鈫?v1.1
  date: string
  author: string
  changes: [string]    # 鍙樻洿鎽樿鍒楄〃
revision_log:
  entries: [revision_entry]
```

## 4. 浜嬩欢鑱斿姩
- subscribe `doc_structure_ready`锛圡90 鍙戝竷锛夛細棣栫増 v1.0 鍩虹嚎鐧昏銆?- subscribe `doc_delta_committed`锛氬悗缁彉鏇村閲?鈫?杩藉姞 revision_entry銆?- publish `revision_recorded`锛氫慨璁㈢櫥璁板畬鎴?鈫?M80 璐ㄦ/娓叉煋鍙銆?
## 5. 鏍稿績閫昏緫锛堜吉浠ｇ爜锛?```
1. doc_structure_ready 鈫?revision_log.entries=[v1.0 鍩虹嚎]
2. doc_delta_committed 鈫?cur=DocState锛沜hanges=diff(prev, cur)
3. changes 闈炵┖ 鈫?ver=bump(prev.ver)锛沘ppend entry锛沺ublish revision_recorded
4. query(ver) 鈫?杩斿洖璇ョ増鏈?DocState 蹇収锛堝洖婧級
```

## 6. 涓嶅彉寮忛伒瀹堬紙01 搂5锛?- I1 涓夋浜ゅ垎绂伙細鍙０鏄庝慨璁㈣兘鍔涳紝涓嶆寔绠＄嚎椤哄簭锛堥『搴忓湪 P06锛変笌鍐呭锛圡90 浜?DocState锛夈€?- I2 鏍稿績鍥哄畾锛氫緷璧?M90/M00锛屾湭鏇挎崲鏍稿績妯″潡銆?- I3 閫氫俊濂戠害锛氫粎缁?revision_entry / revision_log 涓?revision_recorded 浜嬩欢閫氫俊銆?- I4 鏁版嵁闅旂锛氭棤鑷湁璧勪骇銆?- I5 鐪熺浉鍞竴锛氭寕杞戒笌鐧昏浠?02 搂8.5 + registry protocols[] 涓哄噯銆?
## 7. 涓庡畼鏂归摼鐨勫叧绯?鍚?M97鈥斺€擬90 瀹樻柟鎸?P90 浣嶄骇 DocState锛孧98 鎸?P60 浣嶅仛淇鍩熸繁鍖栵紱涓嶅鍒?M90 姝ｆ枃锛坈ore_modules 渚濊禆寮曠敤锛孖5锛夈€?
```

## 5. 资产（0 文件）

- 本装配**零题材资产**：技术文档域包为机制增强包（同通用核心基础包先例，无 `assets/` 目录）。
- 因此本件不存在资产键表，也不存在资产正文引用的缺口——**这是它天然可自包含的结构原因**。
- 对照：校园情感包 29 资产文件 / 西幻生存包 23 资产文件，其引用式档位正源于资产正文体量。

## 6. 装载指引

给接收方 AI 的装载四步（对齐 06 执行协议）：

1. **读本件**：§2 取管线结构，§3 取执行顺序投影，§4 取各模块的契约与逻辑。
2. **对表**：按 §3 的表逐层挂载；模块契约见 §4 对应的内嵌段（含 `machine_contract` 机读块）。
3. **执行**：按 M50 主循环推进——P00 装载骨架 → P40 术语同步 → P60 修订记录 → P80 质检渲染；回合 begin/end 打快照与回卷。
4. **验收**：过 §7 自检清单；任一不满足先修正再交付。

边界提醒：

- 本件内嵌的是**模块层与管线层**；上位协议件（01/02/06）为全库共用规范，本件不含其正文。
- 若接收方需要与官方核心保持严格同步，请以仓库最新版为准重新生成本件（见本次生成方式）。

## 7. 自检清单（交付前逐项核对）

- [ ] §0–§7 八段骨架齐备
- [ ] §4 内嵌段数 = 15（两包自带 2 + 官方核心 13）
- [ ] §3 执行顺序与 §2 管线 layers 一致（default 挂载不冲突）
- [ ] 形态为**全文内嵌**：接收方在不访问仓库时可完成装载
- [ ] 缺口声明与会话一致（协议件不内嵌 / 快照时点 / 未挂签名锚）
- [ ] 机器验收通过：nf assemble --check 本文件（需求原话见 §0）

---

*—— 自包含样本 · 由 build_selfcontained_sample.ps1 生成（可复现）· 2026-09-15 · 内嵌 15 件*

