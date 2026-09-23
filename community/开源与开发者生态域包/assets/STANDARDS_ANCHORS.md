<!-- nf-asset: key="STANDARDS_ANCHORS" version="1.0" status="active" -->
# 权威锚表 · 开源与开发者生态

> 用途：本域 12 条细分各自的**外部权威锚**（规范 / 论文 / 参考实现）与**可达性实证**。外部锚只作口径与机制参照，**不作品质背书**（STRATEGY §3.2/§3.3）。
> 资产键：`STANDARDS_ANCHORS`｜实测日期：2026-09-22（本机 GET，HTTP 状态见下表；不可达如实记 `✗`，不假装可达）。

## 1. 锚表

| 条目键 | 锚类型 | URL | 可达性 | 可扩展标准（绑定） |
|---|---|---|---|---|
| `F09-01` | spec | https://opensource.org/osd | ✓ 200 | `creativecommons` 许可与权利表达（Creative Commons；关键词「许可|版权|知识产权|授权」命中） |
| `F09-02` | spec | https://opensource.org/osd | ✓ 200 | `osi-osd` 开源定义（OSI；域码 F09 专属绑定（轮换 0）） |
| `F09-03` | spec | https://opensource.org/osd | ✓ 200 | `oasis-openapi` OpenAPI 3.1（OpenAPI Initiative；关键词「接口|API|端点|服务|部署」命中） |
| `F09-04` | spec | https://opensource.org/osd | ✓ 200 | `w3c-epub33` EPUB 3.3（W3C；关键词「文档|出版|排版|校对」命中） |
| `F09-05` | spec | https://opensource.org/osd | ✓ 200 | `osi-osd` 开源定义（OSI；域码 F09 专属绑定（轮换 0）） |
| `F09-06` | spec | https://opensource.org/osd | ✓ 200 | `nist-800-188` SP 800-188 去标识化（NIST；关键词「权限|访问控制|治理」命中） |
| `F09-07` | spec | https://opensource.org/osd | ✓ 200 | `osi-osd` 开源定义（OSI；域码 F09 专属绑定（轮换 0）） |
| `F09-08` | spec | https://opensource.org/osd | ✓ 200 | `mlcommons-bench` MLPerf 基准（可扩展场景）（MLCommons；关键词「评测|基准|排行榜|跑分」命中） |
| `F09-09` | spec | https://opensource.org/osd | ✓ 200 | `osi-osd` 开源定义（OSI；域码 F09 专属绑定（轮换 0）） |
| `F09-10` | spec | https://opensource.org/osd | ✓ 200 | `osi-osd` 开源定义（OSI；域码 F09 专属绑定（轮换 0）） |
| `F09-11` | spec | https://opensource.org/osd | ✓ 200 | `owasp-llm` LLM 应用十大风险（OWASP；关键词「安全|越狱|红队|攻击|对抗」命中） |
| `F09-12` | spec | https://opensource.org/osd | ✓ 200 | `osi-osd` 开源定义（OSI；域码 F09 专属绑定（轮换 0）） |

## 2. 使用边界

- 锚用于**口径复核**（该细分的通行定义/评测口径从何而来），不表示 NF 复制了外部文本；本包正文自撰。
- 锚不可达时按不可达记档，不影响本包口径面的机检（判据落在本包 schema 与度量族）。
- 锚版本漂移（规范改版）由维护者按需复核；本表不做自动追踪。
