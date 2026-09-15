# NF 接力协议（handover / SBAR）

> ⛔ 操作指令：接手前先读 `handovers/HO-*.md` 的**建议**与**未决项**两段，再读其余。

**是什么**：交接不是总结。总结说「做过什么」，交接说「**现在什么状态 + 下一棒优先做什么 + 什么算做完**」。
结构借 SBAR（医疗/航空结构化交接）：**情境 → 背景 → 评估 → 建议**，另加**未决项**。

**硬约束**：**空未决项 = 不合格交接**（没有未决就是没交接）；每条未决必须带判据（怎样算完成）。

```bash
python scripts/nf.py handover ls                 # 列全部交接件
python scripts/nf.py handover check handovers/HO-0001-W1到W2.md   # 机检五段 + 未决判据 + refs 可解析
python scripts/nf.py handover verify             # 机检声明 + 全部交接件
```

**与相邻品类的分工**：ADR（`decisions/`）= 为什么这样定；交接件（本目录）= 现在到哪 + 下一步；
审计（`results/audit/`）= 查到了什么；RFC 头 = 协议件是哪一版。
