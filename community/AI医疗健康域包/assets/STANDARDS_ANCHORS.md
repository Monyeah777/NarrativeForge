<!-- nf-asset: key="STANDARDS_ANCHORS" version="1.0" status="active" -->
# 权威锚表 · AI+医疗健康

> 用途：本域 12 条细分各自的**外部权威锚**（规范 / 论文 / 参考实现）与**可达性实证**。外部锚只作口径与机制参照，**不作品质背书**（STRATEGY §3.2/§3.3）。
> 资产键：`STANDARDS_ANCHORS`｜实测日期：2026-09-22（本机 GET，HTTP 状态见下表；不可达如实记 `✗`，不假装可达）。

## 1. 锚表

| 条目键 | 锚类型 | URL | 可达性 | 可扩展标准（绑定） |
|---|---|---|---|---|
| `D01-01` | spec | https://www.who.int/health-topics/artificial-intelligence | ✓ 200 | `hl7-fhir` FHIR（资源扩展机制）（HL7；关键词「医疗|临床|病历|诊断」命中） |
| `D01-02` | spec | https://www.who.int/health-topics/artificial-intelligence | ✓ 200 | `hl7-fhir` FHIR（资源扩展机制）（HL7；关键词「医疗|临床|病历|诊断」命中） |
| `D01-03` | spec | https://www.who.int/health-topics/artificial-intelligence | ✓ 200 | `hl7-fhir` FHIR（资源扩展机制）（HL7；关键词「医疗|临床|病历|诊断」命中） |
| `D01-04` | spec | https://www.who.int/health-topics/artificial-intelligence | ✓ 200 | `w3c-skos` SKOS 词表（W3C；关键词「术语|词表|本体|知识图谱」命中） |
| `D01-05` | spec | https://www.who.int/health-topics/artificial-intelligence | ✓ 200 | `hl7-fhir` FHIR（资源扩展机制）（HL7；域码 D01 专属绑定（轮换 0）） |
| `D01-06` | spec | https://www.who.int/health-topics/artificial-intelligence | ✓ 200 | `hl7-fhir` FHIR（资源扩展机制）（HL7；域码 D01 专属绑定（轮换 0）） |
| `D01-07` | spec | https://www.who.int/health-topics/artificial-intelligence | ✓ 200 | `unesco-ai` AI 伦理建议书（UNESCO；关键词「教育|培训|组织学习」命中） |
| `D01-08` | spec | https://www.who.int/health-topics/artificial-intelligence | ✓ 200 | `hl7-fhir` FHIR（资源扩展机制）（HL7；关键词「医疗|临床|病历|诊断」命中） |
| `D01-09` | spec | https://www.who.int/health-topics/artificial-intelligence | ✓ 200 | `hl7-fhir` FHIR（资源扩展机制）（HL7；域码 D01 专属绑定（轮换 0）） |
| `D01-10` | spec | https://www.who.int/health-topics/artificial-intelligence | ✓ 200 | `hl7-fhir` FHIR（资源扩展机制）（HL7；关键词「医疗|临床|病历|诊断」命中） |
| `D01-11` | spec | https://www.who.int/health-topics/artificial-intelligence | ✓ 200 | `gdpr` GDPR（EU；关键词「隐私|个人信息|去标识|合规|监管」命中） |
| `D01-12` | spec | https://www.who.int/health-topics/artificial-intelligence | ✓ 200 | `gdpr` GDPR（EU；关键词「隐私|个人信息|去标识|合规|监管」命中） |

## 2. 使用边界

- 锚用于**口径复核**（该细分的通行定义/评测口径从何而来），不表示 NF 复制了外部文本；本包正文自撰。
- 锚不可达时按不可达记档，不影响本包口径面的机检（判据落在本包 schema 与度量族）。
- 锚版本漂移（规范改版）由维护者按需复核；本表不做自动追踪。
