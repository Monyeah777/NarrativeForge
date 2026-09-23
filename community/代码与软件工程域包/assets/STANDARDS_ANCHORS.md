<!-- nf-asset: key="STANDARDS_ANCHORS" version="1.0" status="active" -->
# 权威锚表 · 代码与软件工程

> 用途：本域 12 条细分各自的**外部权威锚**（规范 / 论文 / 参考实现）与**可达性实证**。外部锚只作口径与机制参照，**不作品质背书**（STRATEGY §3.2/§3.3）。
> 资产键：`STANDARDS_ANCHORS`｜实测日期：2026-09-22（本机 GET，HTTP 状态见下表；不可达如实记 `✗`，不假装可达）。

## 1. 锚表

| 条目键 | 锚类型 | URL | 可达性 | 可扩展标准（绑定） |
|---|---|---|---|---|
| `E13-01` | spec | https://peps.python.org/pep-0008/ | ✓ 200 | `peps` PEP 体系（含 8/257/621）（Python；域码 E13 专属绑定（轮换 0）） |
| `E13-02` | spec | https://peps.python.org/pep-0008/ | ✓ 200 | `peps` PEP 体系（含 8/257/621）（Python；域码 E13 专属绑定（轮换 0）） |
| `E13-03` | spec | https://peps.python.org/pep-0008/ | ✓ 200 | `peps` PEP 体系（含 8/257/621）（Python；域码 E13 专属绑定（轮换 0）） |
| `E13-04` | spec | https://peps.python.org/pep-0008/ | ✓ 200 | `peps` PEP 体系（含 8/257/621）（Python；域码 E13 专属绑定（轮换 0）） |
| `E13-05` | spec | https://peps.python.org/pep-0008/ | ✓ 200 | `cwe` CWE 缺陷枚举（MITRE；关键词「漏洞|缺陷|弱点」命中） |
| `E13-06` | spec | https://peps.python.org/pep-0008/ | ✓ 200 | `spdx-3` SPDX 3.0（含 AI profile）（SPDX；关键词「供应链|依赖」命中） |
| `E13-07` | spec | https://peps.python.org/pep-0008/ | ✓ 200 | `w3c-epub33` EPUB 3.3（W3C；关键词「文档|出版|排版|校对」命中） |
| `E13-08` | spec | https://peps.python.org/pep-0008/ | ✓ 200 | `peps` PEP 体系（含 8/257/621）（Python；域码 E13 专属绑定（轮换 0）） |
| `E13-09` | spec | https://peps.python.org/pep-0008/ | ✓ 200 | `commonmark` CommonMark 0.31.2（CommonMark；关键词「提示|指令|模板」命中） |
| `E13-10` | spec | https://peps.python.org/pep-0008/ | ✓ 200 | `owasp-llm` LLM 应用十大风险（OWASP；关键词「安全|越狱|红队|攻击|对抗」命中） |
| `E13-11` | spec | https://peps.python.org/pep-0008/ | ✓ 200 | `eu-machinery` 机械条例 2023/1230（EU；关键词「机械|机器人|协作」命中） |
| `E13-12` | spec | https://peps.python.org/pep-0008/ | ✓ 200 | `peps` PEP 体系（含 8/257/621）（Python；域码 E13 专属绑定（轮换 0）） |

## 2. 使用边界

- 锚用于**口径复核**（该细分的通行定义/评测口径从何而来），不表示 NF 复制了外部文本；本包正文自撰。
- 锚不可达时按不可达记档，不影响本包口径面的机检（判据落在本包 schema 与度量族）。
- 锚版本漂移（规范改版）由维护者按需复核；本表不做自动追踪。
