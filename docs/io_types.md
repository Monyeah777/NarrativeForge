# I/O 类型面（io_types）
> ⛔ 操作指令：阅读即执行——本文含可直接执行的命令与判定，勿当资料阅读。
> 最后更新：2026-09-14

## 是什么

`machine_contract` 的可选键（01 §7 **V1 字段级新增**，非 bump）：`outputs` = token→kind、
`inputs` = 依赖模块→期望 kind。词表 `string|integer|number|boolean|array|object|event|state|untyped`。

## 判定原则（只判可证）

- kind 越词表 → **FAIL**；消费方声明期望 kind 且提供方已声明类型、无一匹配 → **FAIL**；
- 未收窄（`untyped`）或未标 → **WARN**（如实缺口，**不判死**）；
- `untyped` 是合法值（与 `protocol/event_registry.json` 措辞一致）——**禁止为省事编造类型**。

## 取值来源（确定性、有据可依）

1. `outputs[token]` = `event_registry.json` 里同名事件字段的类型（证据）；未命中 → `untyped`。
2. `inputs[M00]` = `state`；其余依赖 → `untyped`。

## 怎么用

```bash
python scripts/nf.py module types            # 覆盖率 + 可证不匹配
python scripts/nf.py module types --write    # 按上述规则补标（幂等）
```

## 边界

覆盖率取决于模块**显式声明 outputs**；未声明就只能是 `untyped`——这是内容侧的活。
