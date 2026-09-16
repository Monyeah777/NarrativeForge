# NF 复盘（postmortem）

> ⛔ 操作指令：踩坑后先建档（`PO-NNNN-*.md`），再动手修；**未复盘不得关闭**。

**四段**：现象 → 影响 → 根因 → 行动项（机制借鉴 SRE postmortem 的无指责原则）。

**硬约束**：根因必须写**机制**（不是"谁没注意"）；每条行动项必须带**负责人 + 判据**；
`status: closed` 的复盘件必须已被 `protocol/RECEIPTS.json` 锚定——防事后美化。

```bash
python scripts/nf.py postmortem ls                       # 列全部复盘
python scripts/nf.py postmortem check postmortems/PO-0001-*.md
python scripts/nf.py postmortem verify
```

**分工**：复盘（本目录）= 学到什么、怎么防下次；ADR（`decisions/`）= 定下来的决策；
交接件（`handovers/`）= 现在到哪、下一步；审计（`results/audit/`）= 查到了什么。
