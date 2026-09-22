---
id: AUD-0015
title: 决策模型逐行审查缺口 —— 93 行候选全判 + 三类修复（收割器根因 / 数据契约登记 / 静默吞错计数）
date: 2026-09-22
scope: 作者指令「让决策模型逐行检验缺口，找出所有漏洞，然后你来一并修理」——机械预筛行级候选 → 真模型逐行判（缺口/严重度）→ 确定性证据复核 → 按类一并修理；本件如实区分「已修」「挂账（内容面）」与「不可由代码修」三类
verdict: pass
auditor: 本轮执行者
subjects:
  - desktop/src/core/gap_review.py:dd4a4e792c24996ebfe591c71b97a5664dd65cde9395ae8bed48e4b00014158a
  - desktop/src/core/payload_harvest.py:f62843f3301a7331aa0bc73b9f240070d963de694357b1f3e90ec54ee281d3ca
  - protocol/data_contracts.json:ce951a3322dd7a4827c39d68826aee9e3945986e5c64bd0b4b1fa1741ff72b32
  - protocol/assertions.json:4eb0b6ad0ca755daeef0a1d6c4d98eb8515173338ad51abd9bc07dac9f5e18f6
  - desktop/src/core/interop_export.py:9dc832aba768fbd97f927283b85ffc749c5714304b5f75032b59893d5e079a21
  - desktop/src/core/text_hygiene.py:52f0f945aa948cccc276de1d8f6a228d301dfe2314e195c555fea6c38743aeb8
  - desktop/src/core/workloop.py:11eac59e76eb1b8e0b49a88f8f1620cf2d5a7e8257dedbc9c91084ba9c75e3ab
  - scripts/serve_decision_model.py:02074902fcdaeda997bc36a16020f64521140dcfc70ca9a9e5cff3e5c7da93a0
  - scripts/nf.py:423440d0eff4526dfdf2284c0f460ea941e9ea53317803ec2d3def3e2bb6a93c
---

> 签收位：本件**未填 `accepted_by`/`accepted_at`**——验收签收属作者动作，执行者不自签。
> subjects = 九件（审查模块 / 收割器 / 契约登记 / 断言表 / 四个被修文件 / CLI）；**不含派生物**（口径同前）。

## 一、逐行审查是怎么做的（双轨，缺一不进修复清单）

新增 `core/gap_review.py` + `nf review`：

```
候选行（机械预筛，行级可定位） → 真模型逐行判（noul 是否构成缺口 + score 严重度）
    → 确定性证据复核（该行能否由规则证实） → fixable / suspected / not-a-gap
```

**为什么必须双轨**：Laya 系是未校准分类器（模型卡自述 ECE 0.213 偏自信）——它只能**排序与提示**，
不能单独判决"这是漏洞"。故进修复清单的每一行都必须另有确定性证据；模型说"是"但无证据的，
一律记 `suspected` 挂账，不修。

## 二、真模型逐行判定结果（93 行，实测）

| 类 | 行数 | 模型判定（noul p 区间） | 严重度（score 期望） | 证据复核 |
|---|---|---|---|---|
| `missing-quality-rule`（规范件未登记数据契约） | 15 | 0.84–0.96 | 2.27–2.35 | 15/15 可证 |
| `silent-skip`（except → pass/continue 无说明） | 50 | 0.94–0.97 | 2.24–2.33 | 50/50 可证 |
| `unharvestable-payload`（正文有类型信息但收不到） | 28 | 0.91–0.96 | 2.25–2.3 | 28/28 可证 |
| 合计 | **93** | — | — | 93/93 |

报告存档：`.rivet/private_archive/gap_review/2026-09-22.json`（逐行含 p、severity、证据文本）。

## 三、一并修理（按类，不逐条打补丁）

| 类 | 修法 | 结果 |
|---|---|---|
| ① `unharvestable-payload`（28 行） | **修根因**：`payload_harvest.harvest_doc` 增加 `produce:` 事件标记写法（旧规则只认 `event:`/`name:`/`publish:`）——28 行一处代码修复 | 收割立即多收窄 **13 个字段**；事件载荷类型覆盖 **45.6% → 52.7%**；`type_backlog` **99 → 86**；再按"是否真有类型证据"细分后：真缺口 **28 → 7**，另 19 行归为 `payload-no-evidence`（只有字段名、无任何类型证据） |
| ② `missing-quality-rule`（15 行） | 补数据契约登记：12 件指向真实 checkN（driver/endpoint/rfc → `check36`；asset_line_baseline → `check23`；5 份 schema → `check28`；external_events → `check16`；transform_log/knowledge_usage → `check37`）；3 件（vocabularies/normative/data_contracts）**无对应 checkN** → 改为新增 3 条断言（`assertion:vocabularies-face` / `normative-face` / `data-contracts-face`，json_value schema 自证）并以 `assertion:<id>` 登记 | 数据契约登记 **11 → 26**；`nf model contracts` 全绿（quality_rule 全部解析到真实 check/assertion）；该类候选 **15 → 0** |
| ③ `silent-skip`（50 行） | 先给**本波新写文件**的 5 处补真实理由（内联注释：尽力而为跳过 / Ctrl+C 正常终止 / 软依赖缺面）；判据同步接受"内联在 except 行的说明" | 该类 **50 → 45**；**其余 45 处跨 20 个既有模块**属存量面，按"存量先可数、再逐波收"处理：**不批量编造理由**，留挂账（模型 p/严重度已在档），收敛路径 = 逐文件读语义后补说明 |

## 四、门禁与验收

| 判据 | 结果 |
|---|---|
| `bash verify.sh` | **PASS=61 · WARN=0 · FAIL=0** |
| `python -m unittest discover -s desktop/tests -q` | 全绿 |
| `nf conformance` | **27/27 conformant**（含 `modeling` 契约：数据契约 26 · 断言 11 条全过） |

## 五、遗留与不宣称

1. **不宣称"零漏洞"**：本件是**候选面 + 复核面**的结论，不是形式化证明；`nf review` 是**非门禁工具**
   （不进 verify），其候选规则本身也可被审计改进。
2. **三类挂账（内容面，不可由代码修）**：`payload-no-evidence` 19 行（字段只有名字、无类型证据 →
   须模块作者补类型；**我拒绝替作者编类型**）、`unharvestable-payload` 7 行（正文缺事件标记，
   修复需按模块 `machine_contract.events.publish` 归因，属内容编辑）、`silent-skip` 45 行
   （存量 20 个模块，须逐文件读语义补说明）。
3. **模型判定的正确用法**：93 行中模型全部判"是缺口"（p≥0.84），但**是否可修**由证据决定——
   这正是"模型找出、证据裁决、worker 落笔"的固定分工。
