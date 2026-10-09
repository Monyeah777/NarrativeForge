# NFA-L · NF 装配语言（声明式 + 命令式混合）

> 最后更新：2026-10-09
> ⛔ 操作指令：阅读即执行——本文含可直接执行的命令与判定，勿当资料阅读。

## 是什么

NFA-L 把 NF 的两半语言合到一处：

- **声明层（沿用，不新造）**：YAML 围栏 + protocol/schema 的 JSON-Schema IDL，回答「有什么」；
- **命令层（本件补）**：封闭 guard 表达式，回答「什么时候走」。

它补的那处内部缺口：Pipeline 的 structure.flow[].condition 此前只是自由字符串（IDL 仅
type: string / minLength: 1），仓内多处管线把它写成中文散文——人能读，机器既不能静态检查、
也不能执行。NFA-L 让它可检查、可执行、可复算。

设计纪律：不自造开放表达力（封闭函数集，无用户函数/循环/赋值/IO）；边缘全借仓库既有真源
（world_slots / event_registry / io_types / 模块 machine_contract）；散文 condition 不判死
（advisory），只有以 = 开头的 condition 才进命令层。

## 怎么用

    nf nfal help
    nf nfal parse 'WorldState.time.day >= 30'
    nf nfal check 'WorldState.time.day >= 30' --tokens
    nf nfal build 03_管线库/P01_标准管线.md --no-tokens
    nf nfal eval 03_管线库/P01_标准管线.md --state state.json
    nf nfal schema-check 03_管线库/P01_标准管线.md

把 condition 写成命令式片段：以 = 开头，其后是 nf-expr。未加 = 的 condition 保持原样（散文），
门禁只记 advisory A0201（V1 只增不删）。

## 命令层语法（封闭）

    expr    := ternary
    ternary := or ( "?" expr ":" expr )?
    or      := and ( "||" and )*
    and     := cmp ( "&&" cmp )*
    cmp     := add ( ("=="|"!="|"<"|"<="|">"|">="|"in") add )?
    add     := mul ( ("+"|"-") mul )*
    mul     := unary ( ("*"|"/"|"%") unary )*
    unary   := ("!"|"-") unary | postfix
    postfix := primary ( "(" expr ("," expr)* ")" )?     # 只有具名函数可调用
    primary := literal | path | "(" expr ")" | list | map

命名空间（不另造层级，直接借登记真源）：

| 写法 | 真源 | 语义 |
|---|---|---|
| WorldState.time.day 一类 | protocol/world_slots.json 的 slots 全名 | 世界状态量（也接受 state. 前缀） |
| event.<name> | protocol/event_registry.json 的 events | 事件是否发生（bool） |
| token.<name> | 模块 machine_contract 的 outputs | 产出令牌（类型取 io_types） |
| input.<name> | 调用方注入 | guard 输入 |

封闭函数集：size / contains / has / startsWith / int / string。

## 类型与判决（fail-closed）

类型词表复用既有 io_types：string / integer / number / boolean / array / object / event / state / untyped。

- 未登记符号 = fail（E0301）；guard 非 bool = fail（E0302）；函数越封闭集 = fail（E0304）；
- untyped = warn（E0310，合法但未收窄），执行后端记 abstain；
- 求值为三值 Kleene：unknown && false = false、unknown || true = true，其余 unknown；
- 判决三态 pass / fail / abstain，abstain 永不折算为 pass（与决策层同源口径）。

## 边界（不宣称）

- 不做通用编程语言：无循环、赋值、函数定义、模块导入、I/O；
- 不替代声明层：拓扑、层、模块边界仍是 YAML + schema；
- 不生成正文：只做判决与 NF-IR 中间表示（规范 JSON，可 diff/golden）。
