<!-- nf-asset: key="STANDARDS_ANCHORS" version="1.0" status="active" -->
# 权威锚表 · 代码审查与缺陷检测

> 用途：本域 12 条细分各自的**外部权威锚**（规范 / 论文 / 参考实现）与**可达性实证**。外部锚只作口径与机制参照，**不作品质背书**（STRATEGY §3.2/§3.3）。
> 资产键：`STANDARDS_ANCHORS`｜实测日期：2026-09-22（本机 GET，HTTP 状态见下表；不可达如实记 `✗`，不假装可达）。

## 1. 锚表

| 条目键 | 锚类型 | URL | 可达性 | 可扩展标准（绑定） |
|---|---|---|---|---|
| `B09-01` | doc | https://semgrep.dev/docs/ | ✓ 200 | `oasis-sarif` SARIF 2.1.0（OASIS；域码 B09 专属绑定（轮换 0）） |
| `B09-02` | spec | https://owasp.org/www-project-top-ten/ | ✓ 200 | `cwe` CWE 缺陷枚举（MITRE；关键词「漏洞|缺陷|弱点」命中） |
| `B09-03` | repo | https://pypi.org/project/radon/ | ✓ 200 | `oasis-sarif` SARIF 2.1.0（OASIS；域码 B09 专属绑定（轮换 0）） |
| `B09-04` | doc | https://owasp.org/www-project-dependency-check/ | ✓ 200 | `spdx-3` SPDX 3.0（含 AI profile）（SPDX；关键词「供应链|依赖」命中） |
| `B09-05` | repo | https://pypi.org/project/detect-secrets/ | ✓ 200 | `oasis-sarif` SARIF 2.1.0（OASIS；域码 B09 专属绑定（轮换 0）） |
| `B09-06` | doc | https://coverage.readthedocs.io/ | ✓ 200 | `oasis-sarif` SARIF 2.1.0（OASIS；域码 B09 专属绑定（轮换 0）） |
| `B09-07` | doc | https://google.github.io/eng-practices/review/ | ✓ 200 | `oasis-sarif` SARIF 2.1.0（OASIS；域码 B09 专属绑定（轮换 0）） |
| `B09-08` | doc | https://git-scm.com/docs/git-diff | ✓ 200 | `oasis-sarif` SARIF 2.1.0（OASIS；域码 B09 专属绑定（轮换 0）） |
| `B09-09` | dataset | https://defects4j.org/ | ✓ 200 | `oasis-sarif` SARIF 2.1.0（OASIS；域码 B09 专属绑定（轮换 0）） |
| `B09-10` | dataset | https://swebench.com/ | ✓ 200 | `oasis-sarif` SARIF 2.1.0（OASIS；域码 B09 专属绑定（轮换 0）） |
| `B09-11` | doc | https://codeql.github.com/docs/ | ✓ 200 | `oasis-sarif` SARIF 2.1.0（OASIS；域码 B09 专属绑定（轮换 0）） |
| `B09-12` | spec | https://docs.oasis-open.org/sarif/sarif/v2.1.0/sarif-v2.1.0.html | ✓ 200 | `oasis-sarif` SARIF 2.1.0（OASIS；域码 B09 专属绑定（轮换 0）） |

## 2. 使用边界

- 锚用于**口径复核**（该细分的通行定义/评测口径从何而来），不表示 NF 复制了外部文本；本包正文自撰。
- 锚不可达时按不可达记档，不影响本包口径面的机检（判据落在本包 schema 与度量族）。
- 锚版本漂移（规范改版）由维护者按需复核；本表不做自动追踪。
