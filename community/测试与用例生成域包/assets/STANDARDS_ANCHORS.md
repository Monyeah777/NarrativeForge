<!-- nf-asset: key="STANDARDS_ANCHORS" version="1.0" status="active" -->
# 权威锚表 · 测试与用例生成

> 用途：本域 12 条细分各自的**外部权威锚**（规范 / 论文 / 参考实现）与**可达性实证**。外部锚只作口径与机制参照，**不作品质背书**（STRATEGY §3.2/§3.3）。
> 资产键：`STANDARDS_ANCHORS`｜细分锚实测日期：2026-09-22（本机 GET，HTTP 状态见下表；不可达如实记 `✗`，不假装可达）｜标准锚实测日期见下表「标准锚」列（取自 `protocol/standards_catalog.json` 的本机探针记录）。

## 1. 锚表

| 条目键 | 锚类型 | URL | 可达性 | 主锚（域口径标准） | 辅锚（产出承载标准） |
|---|---|---|---|---|---|
| `B10-01` | doc | https://docs.pytest.org/en/stable/ | ✓ 200 | `nist-800-142` SP 800-142 组合测试实践（NIST｜eng｜✓ 2026-09-24；域码 B10 专属绑定（轮换 0）） | `ietf-json-schema` JSON Schema 2020-12（IETF/JSON Schema｜data｜✓ 2026-09-24；B 段载体锚（轮换 0；与主锚异层）） |
| `B10-02` | spec | https://csrc.nist.gov/pubs/sp/800/142/final | ✓ 200 | `peps` PEP 体系（含 8/257/621）（Python｜eng｜✓ 2026-09-24；域码 B10 专属绑定（轮换 1）） | `w3c-tabular-data` Tabular Data Model (CSVW)（W3C｜data｜✓ 2026-09-24；B 段载体锚（轮换 1；与主锚异层）） |
| `B10-03` | doc | https://llvm.org/docs/LibFuzzer.html | ✓ 200 | `nist-800-142` SP 800-142 组合测试实践（NIST｜eng｜✓ 2026-09-24；域码 B10 专属绑定（轮换 0）） | `vega-lite` Vega-Lite v5（Vega｜form｜✓ 2026-09-24；B 段载体锚（轮换 2；与主锚异层）） |
| `B10-04` | spec | https://spec.openapis.org/oas/v3.1.0 | ✓ 200 | `ietf-json-schema` JSON Schema 2020-12（IETF/JSON Schema｜data｜✓ 2026-09-24；关键词「约束|校验|schema|形状|契约」命中） | `oasis-openapi` OpenAPI 3.1（OpenAPI Initiative｜iface｜✓ 2026-09-24；载体锚：产出形态「接口」的承载标准） |
| `B10-05` | doc | https://playwright.dev/docs/best-practices | ✓ 200 | `nist-800-142` SP 800-142 组合测试实践（NIST｜eng｜✓ 2026-09-24；域码 B10 专属绑定（轮换 0）） | `w3c-prov-o` PROV-O 溯源本体（W3C｜gov｜✓ 2026-09-24；B 段载体锚（轮换 4；与主锚异层）） |
| `B10-06` | paper | https://arxiv.org/abs/1803.09010 | ✓ 200 | `peps` PEP 体系（含 8/257/621）（Python｜eng｜✓ 2026-09-24；域码 B10 专属绑定（轮换 1）） | `ietf-json-schema` JSON Schema 2020-12（IETF/JSON Schema｜data｜✓ 2026-09-24；B 段载体锚（轮换 0；与主锚异层）） |
| `B10-07` | paper | https://arxiv.org/abs/2107.03374 | ✓ 200 | `nist-800-142` SP 800-142 组合测试实践（NIST｜eng｜✓ 2026-09-24；域码 B10 专属绑定（轮换 0）） | `w3c-tabular-data` Tabular Data Model (CSVW)（W3C｜data｜✓ 2026-09-24；B 段载体锚（轮换 1；与主锚异层）） |
| `B10-08` | doc | https://coverage.readthedocs.io/ | ✓ 200 | `peps` PEP 体系（含 8/257/621）（Python｜eng｜✓ 2026-09-24；域码 B10 专属绑定（轮换 1）） | `vega-lite` Vega-Lite v5（Vega｜form｜✓ 2026-09-24；B 段载体锚（轮换 2；与主锚异层）） |
| `B10-09` | doc | https://docs.pytest.org/en/stable/how-to/failures.html | ✓ 200 | `nist-800-142` SP 800-142 组合测试实践（NIST｜eng｜✓ 2026-09-24；域码 B10 专属绑定（轮换 0）） | `commonmark` CommonMark 0.31.2（CommonMark｜form｜✓ 2026-09-24；B 段载体锚（轮换 3；与主锚异层）） |
| `B10-10` | doc | https://playwright.dev/docs/test-fixtures | ✓ 200 | `a2a` A2A 协议（Linux Foundation｜iface｜✓ 2026-09-24；关键词「多智能体|协同|编排」命中） | `w3c-prov-o` PROV-O 溯源本体（W3C｜gov｜✓ 2026-09-24；B 段载体锚（轮换 4；与主锚异层）） |
| `B10-11` | doc | https://docs.pytest.org/en/stable/explanation/goodpractices.html | ✓ 200 | `nist-800-142` SP 800-142 组合测试实践（NIST｜eng｜✓ 2026-09-24；域码 B10 专属绑定（轮换 0）） | `ietf-json-schema` JSON Schema 2020-12（IETF/JSON Schema｜data｜✓ 2026-09-24；B 段载体锚（轮换 0；与主锚异层）） |
| `B10-12` | doc | https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions | ✓ 200 | `peps` PEP 体系（含 8/257/621）（Python｜eng｜✓ 2026-09-24；域码 B10 专属绑定（轮换 1）） | `w3c-tabular-data` Tabular Data Model (CSVW)（W3C｜data｜✓ 2026-09-24；B 段载体锚（轮换 1；与主锚异层）） |

## 2. 使用边界

- 锚用于**口径复核**（该细分的通行定义/评测口径从何而来），不表示 NF 复制了外部文本；本包正文自撰。
- **双锚分工**：主锚 = 该细分依据的域口径标准（可能与细分锚不同源，形成第二证据链）；辅锚 = 该细分产出（数据 / 契约 / 图表 / 图示 / 溯源）所承载的开放标准。
- 标准锚取自 `protocol/standards_catalog.json` 的**本机实测记录**（含取样标题与 sha256），可达性 false 如实标注，不假装可达。
- 锚不可达时按不可达记档，不影响本包口径面的机检（判据落在本包 schema 与度量族）。
- 锚版本漂移（规范改版）由维护者按需复核；本表不做自动追踪。
