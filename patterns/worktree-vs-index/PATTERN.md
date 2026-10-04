---
id: worktree-vs-index
name: 门禁看工作区、git 看索引——两处口径先对齐
status: active
scope:
  - 代码层
applies_to:
  - .gitattributes
  - desktop/src/core/repo_face.py
  - desktop/src/core/text_hygiene.py
  - verify.sh
rules:
  - 「仓库件」的门禁按**工作区字节**判定（行尾/编码/BOM/引用可达），而 git 只在 `git add` 时把内容规范化进**索引**（`.gitattributes` 的 `text=auto eol=lf`）——两者会在 EOL/BOM 上分歧，先明确以哪一个为准（本仓：门禁以工作区为准）
  - 遇到「门禁报红但 `git status` 干净」，先分三种：① 文件**未跟踪**（`??`，`git diff` 天然为空）；② 差异只在**工作区 vs 索引的规范化**（`git show :<路径>` 与盘上文件逐字节不同）；③ 门禁扫错了面。**先量 `git show` 与盘上字节再下结论**
  - 修法只有一条：**重写工作区文件**（`git add` 只改索引；`git checkout` 对未跟踪件无从恢复）——对**未跟踪的进行中文件**动手前先另存一份到忽略面
evidence:
  - .gitattributes
  - desktop/src/core/text_hygiene.py
  - desktop/tests/test_text_hygiene.py
  - verify.sh
  - handovers/HO-0002-顶尖化两线与收口.md
---

## 为什么

门禁与 git 看的**不是同一份字节**：门禁扫**工作区**，git 的 `text=auto eol=lf` 只在 `git add` 那一刻把
内容规范化进**索引**。于是同一件文件可以同时「工作区是 CRLF（门禁红）」而「`git status` 全绿」
——因为 git 比较的是规范化后的内容。坑在于**没有任何一条命令会主动告诉你这件事**：不动手量
`git show :<路径>` 与盘上字节，最自然的结论是「git 说没问题，是门禁错了」。

实测（2026-10-03）：`engine/rust/src/doc_tables.rs` 在工作区含 CRLF，门禁 check12/编码卫生与
文档入口实跑两条**同时红**；而 `git status --porcelain` 显示 `??`（**未跟踪**）、`git diff` 为空、
`git show :engine/rust/src/doc_tables.rs` 长度为 **0**（索引里根本没有它）。也就是说：这件文件
既不在索引里，也无从 `checkout` 恢复，唯一修法是重写工作区字节——而**只有动手量过**才知道这一点。
该文件最终由所有者的全量重写变成 LF，两条判据同时转绿（CRLF 1 → 0）。

**可复现自证（2026-10-03 · 临时 git 仓，与本仓同款 `.gitattributes`）**：

```text
① 已跟踪件（提交后再写回 CRLF）
   git status --porcelain : ''            ← git 认为「无改动」
   git show :a.rs         : b'fn main() {}\n'      ← 索引里是 LF
   盘上 a.rs              : b'fn main() {}\r\n'    ← 工作区是 CRLF
② 未跟踪件
   git status --porcelain : '?? b.rs'
   git ls-files -o -i     : ''            ← 注意：该命令只列**被忽略**的件，
                                            不能拿它当「未跟踪」的判据
```

也就是说：**「git 干净」与「工作区 CRLF」可以同时成立**——这正是本包要防的那个错判。

## 怎么用

```bash
git status --porcelain <路径>        # ?? = 未跟踪：git diff 为空是正常的，别据此判「门禁错」
git show :<路径> | wc -c             # 0 = 索引里没有它（未跟踪）；非 0 则可与盘上字节逐字节比
python -c "raw=open('<路径>','rb').read(); print('worktree CRLF:', b'\r\n' in raw, len(raw))"
python .rivet/scratch/crlf_scan.py   # 本仓的工作区级 EOL/BOM 全量扫描（面 = 仓库件）
```

判断顺序：**先量再判**。三种可能里只有第 ③ 种才算门禁缺陷，而它恰恰是最不该先假设的那种。

## 反例

看到 `git status` 干净就断定「门禁误报」，然后去改门禁的扫描面——真正的差异仍在工作区，改完门禁
只是把红挪走。另一个反例：对**未跟踪**的进行中文件直接规范化（想「顺手修一下」）——它没有索引副本，
改坏了无从回滚；正确做法是先另存一份到忽略面，或留给所有者。

## 相关

- 与 `single-source-truth` 的关系：那条讲**数据**只有一份真源；这条讲**同一份内容的两个载体**
  （工作区 / 索引）口径不同，得先声明以谁为准，再谈判据。
- 与 `verifier-must-run` 的关系：两者都在处理「判据与事实对不上」；那条管**没人跑**，这条管**跑的对象**
  与交付对象不是同一份字节。
