# NF 决策记录（ADR）

> ⛔ 操作指令：阅读即执行——新决策一律 `nf decisions new`/手写本目录 ADR 文件后跑 `nf decisions verify`。

**分工**（与相邻品类划清边界，避免混装）：

| 品类 | 回答什么 | 落点 |
|---|---|---|
| **ADR（本目录）** | **为什么这样定**（一条决策一编号；采纳后不改不删，只可被取代） | `decisions/ADR-NNNN-*.md` |
| RFC 头 | 协议件**是哪一版**（编号/类别/状态/supersede 链） | `protocol/rfc_index.json` + 01/02/06/07 头部 |
| 审计报告 | **查到了什么**（审查结论与证据，时点事实） | `results/audit/*.md` |
| 迁移记录 | **怎么迁移**（bump 四步） | `01_核心协议.md` §7 / `02` §9.3 |

**格式**：frontmatter 必填 `id / title / status / date / evidence`（`supersedes` / `superseded_by` 缺省写 `—`），
正文必含三段 `## 背景` / `## 决策` / `## 后果`。

**不可改怎么成立**：`status: accepted` 的 ADR **必须已被协议回执锚定**（见 `protocol/RECEIPTS.json`）——
正文一改回执即失效，于是「改了」这件事必然被 `check35` 抓住，决策只能通过新增一条并互指 supersede 来演进。

```bash
python scripts/nf.py decisions            # 列全部决策（编号/状态/日期/标题）
python scripts/nf.py decisions show ADR-0001
python scripts/nf.py decisions verify     # 机检：编号/状态/取代链/证据可解析/三段齐/回执锚定
python scripts/nf.py decisions reindex    # 重建 INDEX 投影
```
