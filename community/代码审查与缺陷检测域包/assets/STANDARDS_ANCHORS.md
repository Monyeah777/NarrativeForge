<!-- nf-asset: key="STANDARDS_ANCHORS" version="1.0" status="active" -->
# 权威锚表 · 代码审查与缺陷检测

> 用途：本域 12 条细分各自的**外部权威锚**（规范 / 论文 / 参考实现）与**可达性实证**。外部锚只作口径与机制参照，**不作品质背书**（STRATEGY §3.2/§3.3）。
> 资产键：`STANDARDS_ANCHORS`｜细分锚实测日期：2026-09-22（本机 GET，HTTP 状态见下表；不可达如实记 `✗`，不假装可达）｜标准锚实测日期见下表「标准锚」列（取自 `protocol/standards_catalog.json` 的本机探针记录）。

## 1. 锚表

| 条目键 | 锚类型 | URL | 可达性 | 主锚（域口径标准） | 辅锚（产出承载标准） |
|---|---|---|---|---|---|
| `B09-01` | doc | https://semgrep.dev/docs/ | ✓ 200 | `oasis-sarif` SARIF 2.1.0（OASIS｜iface｜✓ 2026-09-24；域码 B09 专属绑定（轮换 0）） | `ietf-json-schema` JSON Schema 2020-12（IETF/JSON Schema｜data｜✓ 2026-09-24；B 段载体锚（轮换 0；与主锚异层）） |
| `B09-02` | spec | https://owasp.org/www-project-top-ten/ | ✓ 200 | `cwe` CWE 缺陷枚举（MITRE｜gov｜✓ 2026-09-24；关键词「漏洞|缺陷|弱点」命中） | `w3c-tabular-data` Tabular Data Model (CSVW)（W3C｜data｜✓ 2026-09-24；B 段载体锚（轮换 1；与主锚异层）） |
| `B09-03` | repo | https://pypi.org/project/radon/ | ✓ 200 | `osv` OSV 漏洞格式（Google/OSV｜gov｜✓ 2026-09-24；域码 B09 专属绑定（轮换 2）） | `vega-lite` Vega-Lite v5（Vega｜form｜✓ 2026-09-24；B 段载体锚（轮换 2；与主锚异层）） |
| `B09-04` | doc | https://owasp.org/www-project-dependency-check/ | ✓ 200 | `spdx-3` SPDX 3.0（含 AI profile）（SPDX｜gov｜✓ 2026-09-24；关键词「供应链|依赖」命中） | `commonmark` CommonMark 0.31.2（CommonMark｜form｜✓ 2026-09-24；B 段载体锚（轮换 3；与主锚异层）） |
| `B09-05` | repo | https://pypi.org/project/detect-secrets/ | ✓ 200 | `cwe` CWE 缺陷枚举（MITRE｜gov｜✓ 2026-09-24；域码 B09 专属绑定（轮换 1）） | `ietf-json-schema` JSON Schema 2020-12（IETF/JSON Schema｜data｜✓ 2026-09-24；B 段载体锚（轮换 0；与主锚异层）） |
| `B09-06` | doc | https://coverage.readthedocs.io/ | ✓ 200 | `osv` OSV 漏洞格式（Google/OSV｜gov｜✓ 2026-09-24；域码 B09 专属绑定（轮换 2）） | `ietf-json-schema` JSON Schema 2020-12（IETF/JSON Schema｜data｜✓ 2026-09-24；B 段载体锚（轮换 0；与主锚异层）） |
| `B09-07` | doc | https://google.github.io/eng-practices/review/ | ✓ 200 | `oasis-sarif` SARIF 2.1.0（OASIS｜iface｜✓ 2026-09-24；域码 B09 专属绑定（轮换 0）） | `w3c-tabular-data` Tabular Data Model (CSVW)（W3C｜data｜✓ 2026-09-24；B 段载体锚（轮换 1；与主锚异层）） |
| `B09-08` | doc | https://git-scm.com/docs/git-diff | ✓ 200 | `cwe` CWE 缺陷枚举（MITRE｜gov｜✓ 2026-09-24；域码 B09 专属绑定（轮换 1）） | `vega-lite` Vega-Lite v5（Vega｜form｜✓ 2026-09-24；B 段载体锚（轮换 2；与主锚异层）） |
| `B09-09` | dataset | https://defects4j.org/ | ✓ 200 | `osv` OSV 漏洞格式（Google/OSV｜gov｜✓ 2026-09-24；域码 B09 专属绑定（轮换 2）） | `commonmark` CommonMark 0.31.2（CommonMark｜form｜✓ 2026-09-24；B 段载体锚（轮换 3；与主锚异层）） |
| `B09-10` | dataset | https://swebench.com/ | ✓ 200 | `oasis-sarif` SARIF 2.1.0（OASIS｜iface｜✓ 2026-09-24；域码 B09 专属绑定（轮换 0）） | `w3c-prov-o` PROV-O 溯源本体（W3C｜gov｜✓ 2026-09-24；B 段载体锚（轮换 4；与主锚异层）） |
| `B09-11` | doc | https://codeql.github.com/docs/ | ✓ 200 | `cwe` CWE 缺陷枚举（MITRE｜gov｜✓ 2026-09-24；域码 B09 专属绑定（轮换 1）） | `ietf-json-schema` JSON Schema 2020-12（IETF/JSON Schema｜data｜✓ 2026-09-24；B 段载体锚（轮换 0；与主锚异层）） |
| `B09-12` | spec | https://docs.oasis-open.org/sarif/sarif/v2.1.0/sarif-v2.1.0.html | ✓ 200 | `osv` OSV 漏洞格式（Google/OSV｜gov｜✓ 2026-09-24；域码 B09 专属绑定（轮换 2）） | `w3c-tabular-data` Tabular Data Model (CSVW)（W3C｜data｜✓ 2026-09-24；B 段载体锚（轮换 1；与主锚异层）） |

## 2. 使用边界

- 锚用于**口径复核**（该细分的通行定义/评测口径从何而来），不表示 NF 复制了外部文本；本包正文自撰。
- **双锚分工**：主锚 = 该细分依据的域口径标准（可能与细分锚不同源，形成第二证据链）；辅锚 = 该细分产出（数据 / 契约 / 图表 / 图示 / 溯源）所承载的开放标准。
- 标准锚取自 `protocol/standards_catalog.json` 的**本机实测记录**（含取样标题与 sha256），可达性 false 如实标注，不假装可达。
- 锚不可达时按不可达记档，不影响本包口径面的机检（判据落在本包 schema 与度量族）。
- 锚版本漂移（规范改版）由维护者按需复核；本表不做自动追踪。
