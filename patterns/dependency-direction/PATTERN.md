---
id: dependency-direction
name: 依赖方向：需要低层能力时由调用方注入
status: active
scope:
  - 代码层
applies_to:
  - desktop/src/core/*.py
  - scripts/*.py
rules:
  - 为取用共享低层能力而新增 import，会抬高该模块的 Ca、压低其 I（稳定度）——可能把既有依赖关系变成稳定依赖原则（SDP）违例；这类取用应改为「调用方注入」参数
  - 注入方优先选**已经是该低层模块依赖方**的模块——既有依赖边不新增，包内耦合度量因此不动
  - 耦合违例只许收敛：coupling_metrics 报出的新增违例即 FAIL；确属存量债须评审后重算基线并写进 protocol/coupling_baseline.json
evidence:
  - desktop/src/core/coupling_metrics.py
  - desktop/src/core/orchestration.py
  - desktop/src/core/driver.py
  - protocol/coupling_baseline.json
---

## 为什么

稳定依赖原则（Martin）说：依赖必须指向**更稳定**的方向。NF 把它做成机检——每个
`desktop/src/core` 模块算 Ca（谁依赖我）/ Ce（我依赖谁）/ I = Ce/(Ca+Ce)，A 依赖 B 而
`I(B) > I(A)` 即违例；基线里已登记的存量债可存在，**新增违例即 FAIL**。

坑在于：**新增一个消费者，会改变被依赖方的稳定度**。被依赖方的 Ca +1 ⇒ I 下降 ⇒ 它原本与
「同等稳定」的模块平起平坐的依赖边，会突然变成「依赖了更不稳的一方」。

实测（2026-10-03）：编排层最初在自己的模块里 `from core import mcp_runtime` 取工具面，
于是 `mcp_runtime` 的 Ca 5→6、I 0.5→0.4545，**当场造出两条 SDP 违例**：
`mcp_runtime → knowledge`（I=0.5）与 `mcp_runtime → trust_boundary`（I=0.5）——两者按
「严格更不稳」判定成立。去掉这条 import、改为调用方注入后，`mcp_runtime` 回到 `ca=5 / i=0.5`，
两条违例归零（注意：不是 `I` 相等就安全——是「新增消费者把 I 压下去」才不安全）。

## 怎么用

```bash
python scripts/coupling_metrics.py            # 只读：看当前 I / 违例
python scripts/coupling_metrics.py --write    # 评审后重算基线（只许收敛）
nf patterns for desktop/src/core/driver.py    # 反查某文件适用哪些 pattern
```

代码形态：底层模块（如工具面）不 import 消费者；需要它的一方把**数据/句柄**当参数传下去。

## 反例

在编排层里直接 `from core import mcp_runtime`（看起来最省事）——包内耦合度量当场多出两条
违例；把命令行入口也塞进 `desktop/src/core` 同理（入口放 `scripts/` 就不进这套度量）。

## 相关

- 与 `single-source-truth` 的区别：那条管**数据**只有一份真源；这条管**依赖**只沿更稳定的方向。
