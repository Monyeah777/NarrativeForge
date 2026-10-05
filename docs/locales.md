# 语言面与本地化（locales）
> ⛔ 操作指令：本文是语言面与本地化策略的**声明件**；判据在 check34（core/locales.py），读到即执行。
> 最后更新：2026-10-05

## 这是什么

NF 的语言面分两层：**入口面**（README.md / README.en.md / README.ja.md）与**文档面**（docs/<lang>/…）。
真源 = protocol/locales.json：逐语言的入口、责任方（codeowner）、覆盖面声明，以及文档译件 + **源件摘要**。

## 规则（全部机检）

1. **入口面**：每面须含同一组机读锚点 + 语言切换行（逐条列出全部在场语言）+ H2 结构对齐 + canonical 引用的 .md 件齐。
2. **文档面**：译件路径必须**镜像**原文（docs/<lang>/<原文相对路径>）；每件登记 source_sha256，**源件一改即判过期**。
3. **覆盖面诚实**：coverage=entry 的语言不得有文档译件；coverage=entry+guides 必须备齐注册表声明的全部译件。
4. **未声明即红**：docs/<lang>/ 下出现未登记译件 → FAIL（防「没人管的第二语言面」）。

## 怎么加一份译文

（1）写译文：docs/<lang>/<原文相对路径>；
（2）在 protocol/locales.json 的 docs[].translations 登记 path；
（3）跑 python scripts/nf.py locales --write 重签源件摘要；
（4）跑 python scripts/nf.py locales 自检——过期 / 未镜像 / 缺语言 / 未声明 都会红。

## 现状与边界

- 入口面 **3 语**（中文 / English / 日本語）；文档面已覆盖「发布」与「本地化」两份指南。
- 其余文档仍单语——**由注册表显式声明**，不是静默单语；新增译文按上面四步走。
- 本机制不引入外部翻译平台、**不做机器翻译**：内容质量由译者负责，判据只保证「声明的都在场且不过期」。
- 语言面责任方见注册表的 codeowner（与 Home Assistant 的 codeowners 同义）。
