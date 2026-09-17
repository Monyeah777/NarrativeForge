# ST 校验演示 fixture（**自造 · 非真实卡**）

> 用途：让 `nf st-validate` 的样例报告能覆盖三类资产生命线（R1 卡 / R3 世界书 / R4 变量）。
> **诚实声明**：这两个 fixture 是**手工自造的最小样本**，用于演示判据怎么触发，**不是真实社区卡**，也不代表任何真实作品。A-S4 要的「真实战例」仍需一张公开示例卡或作者自造卡。

| 文件 | 期望结果 |
|---|---|
| `fixture_card_v2_clean.json` | 结构合规的 V2 卡 → 期望 **fail 0**（演示"干净长什么样"） |
| `fixture_worldbook_messy.json` | 故意留坑的世界书 → 期望 **W1 fail + W2 warn + W5 warn**（演示"报告怎么指问题"） |

复现：

```bash
python scripts/nf.py st-validate docs/examples/st-validate/fixture_card_v2_clean.json --out docs/examples/st-validate/report_card.md
python scripts/nf.py st-validate docs/examples/st-validate/fixture_worldbook_messy.json --out docs/examples/st-validate/report_worldbook.md
```
