#!/usr/bin/env python3
"""差分模糊探针：对**真实语料**做定向变异，再让 Python 真源与 .NET 引擎同参数求值 → 逐字段比对。

为什么要有它：正向对账只覆盖「仓库当前恰好长这样」这一种输入；负例探针覆盖的是我手写的用例。
两者都答不了「随机破坏时两侧还一致吗」。本探针把已移植的一致性契约当被测面，对每个契约的
**输入面**做定向变异（改 frontmatter / 改表 / 造环 / 造悬空 / 注入泄漏 …），每次变异后：

    Python 侧：core.conformance_report 的同名契约函数 → (ok, detail)
    .NET 侧：nfparity --conformance-one <契约> <变异树> → (ok, detail, digest)

判定分两层：**裁决一致**（ok 相同）是硬判据；**文案一致**（detail/digest 逐字节）另计一列，
因为「失败分支文案未对齐」是本工程已知的挂账——本探针把它从口头承认变成可追踪的数字。

用法：
    python probes/differential_fuzz_probe.py --root <快照> --py-src <快照>/desktop/src \
        --cli <nfparity.exe> [--work <工作副本目录>] [--only <契约 id 前缀>] [--strict]

退出码：0 无裁决分歧（默认）/ 1 有裁决分歧，或 --strict 下有文案分歧 / 2 用法错误。
纪律：一切变异只发生在**工作副本**上；被检快照全程只读。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path


def contract_digest(cid: str, ok: bool, detail: str) -> str:
    payload = json.dumps({"id": cid, "ok": bool(ok), "detail": detail},
                         sort_keys=True, ensure_ascii=False,
                         separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


class Edit:
    """一次变异的文件操作集合（可整体回滚）。只碰工作副本。"""

    def __init__(self, work: Path):
        self.work = work
        self.saved: list[tuple[Path, bytes | None]] = []

    def _remember(self, path: Path) -> None:
        self.saved.append((path, path.read_bytes() if path.is_file() else None))

    def write(self, rel: str, text: str) -> None:
        path = self.work / rel
        self._remember(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="\n")

    def patch(self, rel: str, old: str, new: str, count: int = 1) -> None:
        path = self.work / rel
        self._remember(path)
        text = path.read_text(encoding="utf-8")
        if old not in text:
            raise AssertionError("变异锚点不存在：%s ← %r" % (rel, old[:60]))
        path.write_text(text.replace(old, new, count), encoding="utf-8", newline="\n")

    def patch_all(self, rel: str, old: str, new: str) -> None:
        path = self.work / rel
        self._remember(path)
        text = path.read_text(encoding="utf-8")
        if old not in text:
            raise AssertionError("变异锚点不存在：%s ← %r" % (rel, old[:60]))
        path.write_text(text.replace(old, new), encoding="utf-8", newline="\n")

    def delete(self, rel: str) -> None:
        path = self.work / rel
        self._remember(path)
        path.unlink()

    def json_edit(self, rel: str, fn) -> None:
        path = self.work / rel
        self._remember(path)
        doc = json.loads(path.read_text(encoding="utf-8"))
        fn(doc)
        path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8", newline="\n")

    def rollback(self) -> None:
        for path, original in reversed(self.saved):
            if original is None:
                if path.is_file():
                    path.unlink()
            else:
                path.write_bytes(original)
        self.saved.clear()


# ------------------------------------------------------------------ 变异清单
#
# 每个变异声明它打的是哪几条契约（只跑受影响的面，省时间），并给出「为什么值得打」。

ADR1 = "decisions/ADR-0001-双源知识层落位.md"
ADR2 = "decisions/ADR-0002-门禁不注水.md"
LIB1 = "library/NF-1.md"
LIB_MODE_INSTANCE = "docs/迁移指南-基于nf-sig-diff.md"


def _m(name, contracts, why, apply, tolerated_text=False):
    """一个变异。tolerated_text=True 表示「文案差异来自各自运行时的异常文本」，不可约。"""
    return dict(name=name, contracts=contracts, why=why, apply=apply,
                tolerated_text=tolerated_text)


def _kind_edit(kind: str, field: str, value):
    """把某种 kind 的第一条断言的某个 params 字段改掉（找不到即报错，防止变异静默落空）。"""
    def apply(doc):
        for assertion in doc["assertions"]:
            if assertion.get("kind") == kind:
                assertion["params"][field] = value
                return
        raise AssertionError("找不到 kind=%s 的断言" % kind)
    return apply


def _json_value_edit(doc):
    """把 json_value(equals) 的期望值改掉（该条应转不通过）。"""
    for assertion in doc["assertions"]:
        if assertion.get("kind") == "json_value" and assertion["params"].get("op") == "equals":
            assertion["params"]["value"] = "__mutated__"
            return
    raise AssertionError("找不到 json_value(equals) 断言")


def _stq_dup(doc):
    """复制首条 ST 规则（id 必重复）。"""
    if not doc.get("rules"):
        raise AssertionError("st_quality 无 rules")
    doc["rules"].insert(1, dict(doc["rules"][0]))


def _ep_set(endpoint_id, field, value):
    """把某个端点的某字段改掉（找不到即报错，防变异静默落空）。"""
    def apply(doc):
        for ep in doc["endpoints"]:
            if ep.get("id") == endpoint_id:
                ep[field] = value
                return
        raise AssertionError("找不到端点 %s" % endpoint_id)
    return apply


def _ep_dup_path(doc):
    """让第二个端点的 path 与第一个相同（method+path 重复）。"""
    doc["endpoints"][1]["method"] = doc["endpoints"][0]["method"]
    doc["endpoints"][1]["path"] = doc["endpoints"][0]["path"]


def _new_module_doc(mid: str) -> str:
    """合成一篇新模块文档（含合法 machine_contract 围栏）——用于「新模块未签边界」用例。"""
    return "\n".join([
        "---", f"id: {mid}", "title: 新模块用例", "---", "",
        "```yaml", "machine_contract:", "  schema: \"1\"", f"  id: {mid}", "  layer: P40",
        "  inputs: []", "  outputs: []", "  events:", "    publish: []", "    subscribe: []",
        "  interfaces: []", "```", "",
    ])


def _ms_tamper(doc):
    """把基线里第一条摘要改掉（等价边界漂移）。"""
    modules = doc.get("modules") or {}
    if not modules:
        raise AssertionError("基线无 modules")
    first = sorted(modules)[0]
    modules[first]["digest"] = "0" * 64


def _tb_first_untyped(doc):
    """找第一个 untyped 字段的 (事件, 字段, 记录)，找不到即报错。"""
    for ev in sorted(doc["events"]):
        for field in sorted((doc["events"][ev].get("fields") or {})):
            spec = doc["events"][ev]["fields"][field]
            if (spec or {}).get("type") == "untyped":
                return ev, field, spec
    raise AssertionError("event_registry 里没有 untyped 字段")


def _tb_clear_note(doc):
    _ev, _field, spec = _tb_first_untyped(doc)
    spec["note"] = ""


def _tb_narrow(doc):
    _ev, _field, spec = _tb_first_untyped(doc)
    spec["type"] = "string"
    spec["note"] = "已收窄为 string（用例）"


MUTATIONS = [
    # ---------------------------------------------------------- 馆藏（library-verify / library-projection）
    _m("lib-id-mismatch", ["library-verify"], "frontmatter id 与文件名不一致",
       lambda e: e.patch(LIB1, "id: NF-1\n", "id: NF-9\n")),
    _m("lib-id-missing", ["library-verify"], "缺必填键 id",
       lambda e: e.patch(LIB1, "id: NF-1\n", "")),
    _m("lib-title-missing", ["library-verify"], "缺必填键 title",
       lambda e: e.patch(LIB1, "title: ", "titles: ")),
    _m("lib-license-out", ["library-verify"], "license 越词表",
       lambda e: e.patch(LIB1, "license: MIT", "license: WTFPL")),
    _m("lib-status-out", ["library-verify"], "status 越词表",
       lambda e: e.patch(LIB1, "status: active", "status: retired")),
    _m("lib-superseded-no-target", ["library-verify"], "status=superseded 但缺 superseded_by",
       lambda e: e.patch(LIB1, "status: active", "status: superseded")),
    _m("lib-bad-date", ["library-verify"], "generated 非 YYYY-MM-DD",
       lambda e: e.patch(LIB1, "generated: 2026-09-06", "generated: 2026/09/06")),
    _m("lib-attestation-drift", ["library-verify"], "签名锚不再覆盖当前内容",
       lambda e: e.patch(LIB1, "attestation: a3872e040ba2dc307bc665896908cc0b2a53802517bf867d39ba34d1dea83866",
                         "attestation: b3872e040ba2dc307bc665896908cc0b2a53802517bf867d39ba34d1dea83866")),
    _m("lib-sources-empty", ["library-verify"], "sources 清空（只该 WARN，不该 FAIL）",
       lambda e: e.patch(LIB1, "sources:\n  - community/校园情感领域包\n  - 04_模块库\n", "sources: []\n")),
    _m("lib-entry-deleted", ["library-verify", "library-projection"], "条目整件消失（真源少一件）",
       lambda e: e.delete(LIB1)),
    _m("lib-index-tamper", ["library-projection"], "INDEX 登记表被手改",
       lambda e: e.patch("library/INDEX.md", "| 校园情感流（高二 · 毕业遗憾线） |",
                         "| 校园情感流（手改过的标题） |")),
    _m("lib-alias-tamper", ["library-projection"], "ALIAS 转译表被手改",
       lambda e: e.patch("library/ALIAS.md", "| nf-1 | NF-1 |", "| nf-one | NF-1 |")),
    _m("lib-type-missing", ["library-verify"], "缺必填键 type",
       lambda e: e.patch(LIB1, "type: 世界（校园情感装配样本）\n", "")),
    _m("lib-frontmatter-absent", ["library-verify"], "整块 frontmatter 消失",
       lambda e: e.patch(LIB1, "---\nid: NF-1", "id: NF-1")),
    _m("lib-superseded-by-ghost", ["library-verify"], "superseded_by 指向不存在的条目",
       lambda e: e.patch(LIB1, "status: active", "status: superseded\nsuperseded_by: NF-999")),
    _m("lib-superseded-by-self", ["library-verify"], "superseded_by 指向自身（链成环）",
       lambda e: e.patch(LIB1, "status: active", "status: superseded\nsuperseded_by: NF-1")),
    _m("lib-attestation-nonhex", ["library-verify"], "attestation 非 64 位十六进制",
       lambda e: e.patch(LIB1, "attestation: a3872e04", "attestation: zz872e04")),
    _m("lib-anchor-scheme-unknown", ["library-verify"], "未知锚方案（应给「未实现」而非判通过）",
       lambda e: e.patch(LIB1, "anchor_scheme: ssh-sig", "anchor_scheme: rsa-sig")),
    _m("lib-recommended-missing", ["library-verify"], "缺推荐键（只该 WARN）",
       lambda e: e.patch(LIB1, "description: 官方装配样本：P02 校园情感管线 + 幽灵遗憾模块（引用式档位，示范诚实纪律）\n", "")),
    _m("lib-bad-stale-date", ["library-verify"], "stale_after 非 YYYY-MM-DD",
       lambda e: e.patch(LIB1, "stale_after: 2027-03-14", "stale_after: 2027-3-14")),

    # ---------------------------------------------------------- 断言表
    _m("asrt-kind-out", ["assertions"], "assertion kind 越封闭集",
       lambda e: e.json_edit("protocol/assertions.json",
                             lambda d: d["assertions"][0].__setitem__("kind", "regex_typo"))),
    _m("asrt-severity-out", ["assertions"], "severity 越词表",
       lambda e: e.json_edit("protocol/assertions.json",
                             lambda d: d["assertions"][0].__setitem__("severity", "blocker"))),
    _m("asrt-dup-id", ["assertions"], "断言 id 重复",
       lambda e: e.json_edit("protocol/assertions.json",
                             lambda d: d["assertions"].insert(1, dict(d["assertions"][0])))),
    _m("asrt-fix-empty", ["assertions"], "fix 为空（判据要求可照做）",
       lambda e: e.json_edit("protocol/assertions.json",
                             lambda d: d["assertions"][0].__setitem__("fix", ""))),
    _m("asrt-row-fail", ["assertions"], "表本身合法但某条断言不通过（detail 里的通过数要一致）",
       lambda e: e.json_edit("protocol/assertions.json",
                             lambda d: d["assertions"][0]["params"].__setitem__("pattern", "叙事"))),
    _m("asrt-missing-field", ["assertions"], "断言缺必填字段",
       lambda e: e.json_edit("protocol/assertions.json",
                             lambda d: d["assertions"][0].pop("message", None))),
    _m("asrt-bad-regex", ["assertions"], "正则非法（断言自身异常 = 该条不通过；异常文案随各运行时，不可约）",
       lambda e: e.json_edit("protocol/assertions.json",
                             lambda d: d["assertions"][0]["params"].__setitem__("pattern", "([unclosed")),
       tolerated_text=True),
    _m("asrt-glob-ghost", ["assertions"], "glob 指向不存在的面（零命中 → 该条通过）",
       lambda e: e.json_edit("protocol/assertions.json",
                             lambda d: d["assertions"][0]["params"].__setitem__("globs", ["ghost/**/*"]))),
    _m("asrt-regex-present-ghost", ["assertions"], "regex_present 目标件不存在",
       lambda e: e.json_edit("protocol/assertions.json", _kind_edit("regex_present", "path", "docs/ghost.md"))),
    _m("asrt-count-at-least-fail", ["assertions"], "count_at_least 下限过高（不通过）",
       lambda e: e.json_edit("protocol/assertions.json", _kind_edit("count_at_least", "min", 999999))),
    _m("asrt-json-value-fail", ["assertions"], "json_value 取值不符",
       lambda e: e.json_edit("protocol/assertions.json", _json_value_edit)),

    # ---------------------------------------------------------- 内容建模
    _m("model-vocab-status-out", ["modeling"], "词表 status 越词表",
       lambda e: e.json_edit("protocol/vocabularies.json",
                             lambda d: d["schemes"][0].__setitem__("status", "retired"))),
    _m("model-vocab-values-drift", ["modeling"], "python_attr 探针值与真源漂移",
       lambda e: e.json_edit("protocol/vocabularies.json",
                             lambda d: d["schemes"][0]["values"].append("diary"))),
    _m("model-normative-ghost", ["modeling"], "规范件指向不存在的文档",
       lambda e: e.json_edit("protocol/normative.json",
                             lambda d: d["normative"][0].__setitem__("path", "不存在的协议件.md"))),
    _m("model-contract-dup", ["modeling"], "数据契约 id 重复",
       lambda e: e.json_edit("protocol/data_contracts.json",
                             lambda d: d["contracts"].insert(1, dict(d["contracts"][0])))),
    _m("model-contract-rule-out", ["modeling"], "quality_rule 指向不在册规则",
       lambda e: e.json_edit("protocol/data_contracts.json",
                             lambda d: d["contracts"][0].__setitem__("quality_rule", "check404"))),
    _m("model-contract-artifact-ghost", ["modeling"], "数据契约指向不存在的产物",
       lambda e: e.json_edit("protocol/data_contracts.json",
                             lambda d: d["contracts"][0].__setitem__("artifact", "protocol/ghost.json"))),
    _m("model-vocab-dup-id", ["modeling"], "词表 id 重复",
       lambda e: e.json_edit("protocol/vocabularies.json",
                             lambda d: d["schemes"].insert(1, dict(d["schemes"][0])))),
    _m("model-normative-dup", ["modeling"], "规范件重复登记",
       lambda e: e.json_edit("protocol/normative.json",
                             lambda d: d["normative"].append(dict(d["normative"][0])))),
    _m("model-contract-status-out", ["modeling"], "数据契约 status 越词表",
       lambda e: e.json_edit("protocol/data_contracts.json",
                             lambda d: d["contracts"][0].__setitem__("status", "retired"))),

    # ---------------------------------------------------------- 决策记录
    _m("dec-id-mismatch", ["decisions"], "ADR 编号与文件名不一致",
       lambda e: e.patch(ADR1, "id: ADR-0001", "id: ADR-0009")),
    _m("dec-status-out", ["decisions"], "ADR 状态越词表",
       lambda e: e.patch(ADR1, "status: accepted", "status: maybe")),
    _m("dec-section-missing", ["decisions"], "正文缺必需段",
       lambda e: e.patch(ADR1, "## 决策\n", "### 决策\n")),
    _m("dec-evidence-ghost-check", ["decisions"], "evidence 指向不在册 check",
       lambda e: e.patch(ADR1, "evidence: [protocol/knowledge_sources.json, 04_模块库/事件类/M20_世界知识库.md, check37]",
                         "evidence: [protocol/knowledge_sources.json, check404]")),
    _m("dec-evidence-ghost-file", ["decisions"], "evidence 指向不存在的件",
       lambda e: e.patch(ADR1, "protocol/knowledge_sources.json", "protocol/ghost.json")),
    _m("dec-supersede-cycle", ["decisions"], "两条 ADR 互相取代（成环）",
       lambda e: (e.patch(ADR1, "superseded_by: —", "superseded_by: ADR-0002"),
                  e.patch(ADR2, "supersedes: —", "supersedes: ADR-0001"))),
    _m("dec-index-tamper", ["decisions"], "decisions/INDEX.md 投影被手改",
       lambda e: e.patch("decisions/INDEX.md", "| ADR-0001 |", "| ADR-0001（手改） |")),
    _m("dec-date-bad", ["decisions"], "date 非 YYYY-MM-DD",
       lambda e: e.patch(ADR1, "date: 2026-09-15", "date: 2026/09/15")),
    _m("dec-evidence-adr-ghost", ["decisions"], "evidence 指向不存在的 ADR",
       lambda e: e.patch(ADR1, "protocol/knowledge_sources.json", "ADR-0099")),

    # ---------------------------------------------------------- 认知族
    _m("cog-term-ghost", ["cognition"], "术语表声明了真源里没有的术语",
       lambda e: e.json_edit("protocol/glossary.json",
                             lambda d: d["terms"][0].__setitem__("term", "不存在的术语"))),
    _m("cog-term-used-in-ghost", ["cognition"], "术语使用面指向不存在的件",
       lambda e: e.json_edit("protocol/glossary.json",
                             lambda d: d["terms"][0]["used_in"].append("docs/ghost.md"))),
    _m("cog-mode-instances-empty", ["cognition"], "执行档没有任何合格实例",
       lambda e: e.json_edit("protocol/execution_modes.json",
                             lambda d: d["modes"][0].__setitem__("instances", []))),
    _m("cog-mode-block-missing", ["cognition"], "实例文档缺必备结构块",
       lambda e: e.patch_all(LIB_MODE_INSTANCE, "判定", "判断")),
    _m("cog-term-dup", ["cognition"], "术语重复登记",
       lambda e: e.json_edit("protocol/glossary.json",
                             lambda d: d["terms"].insert(1, dict(d["terms"][0])))),
    _m("cog-mode-instance-ghost", ["cognition"], "执行档实例指向不存在的件",
       lambda e: e.json_edit("protocol/execution_modes.json",
                             lambda d: d["modes"][0].__setitem__("instances", ["docs/ghost.md"]))),
    _m("cog-mode-blocks-empty", ["cognition"], "执行档缺必备结构声明",
       lambda e: e.json_edit("protocol/execution_modes.json",
                             lambda d: d["modes"][0].__setitem__("required_blocks", []))),

    # ---------------------------------------------------------- 实践包 / RFC / 公开面（补三类面）
    _m("pat-status-out", ["patterns"], "pattern status 越词表",
       lambda e: e.patch("patterns/single-source-truth/PATTERN.md", "status: active", "status: archived")),
    _m("pat-rules-empty", ["patterns"], "pattern 没有可执行规则",
       lambda e: e.patch("patterns/single-source-truth/PATTERN.md",
                         "rules:\n  - 每份数据只有一个真源（frontmatter / registry.json / 契约声明），其余形态一律由脚本重生成\n",
                         "rules: []\n")),
    _m("pat-evidence-ghost", ["patterns"], "evidence 指向不存在的件（只该 WARN）",
       lambda e: e.patch("patterns/single-source-truth/PATTERN.md", "  - check34", "  - docs/ghost.md")),
    _m("pat-id-mismatch", ["patterns"], "pattern id 与目录名不一致",
       lambda e: e.patch("patterns/single-source-truth/PATTERN.md",
                         "id: single-source-truth", "id: single-source")),
    _m("pat-applies-ghost", ["patterns"], "applies_to 指向不存在的件",
       lambda e: e.patch("patterns/single-source-truth/PATTERN.md",
                         "  - library/ALIAS.md", "  - library/ghost.md")),
    _m("pat-projection-tamper", ["patterns"], "patterns 登记表被手改",
       lambda e: e.patch("patterns/INDEX.md", "| single-source-truth |", "| single-source-truth（手改） |")),
    _m("rfc-date-mismatch", ["rfc-heads"], "RFC 头 Date 与「最后更新」不一致",
       lambda e: e.patch("01_核心协议.md", "**Date**: 2026-09-08", "**Date**: 2026-09-09")),
    _m("rfc-category-out", ["rfc-heads"], "RFC Category 越词表",
       lambda e: e.patch("01_核心协议.md", "**Category**: Standards Track", "**Category**: Marketing")),
    _m("rfc-index-ghost", ["rfc-heads"], "RFC 索引指向不存在的文档",
       lambda e: e.json_edit("protocol/rfc_index.json",
                             lambda d: d["docs"][0].__setitem__("path", "ghost.md"))),
    _m("ps-leak-inject", ["public-surface"], "对外产物里注入本机绝对路径",
       lambda e: e.write("desktop/tests/fixtures/external/leak.md", "见 C:\\Users\\某人\\私有件.md\n")),
    _m("ps-leak-clean", ["public-surface"], "对外产物干净（不该误报）",
       lambda e: e.write("desktop/tests/fixtures/external/ok.json", '{"p": "docs/相对路径.md"}\n')),

    # ---------------------------------------------------------- 文档四型（doc-kinds）
    _m("dockinds-doc-deleted", ["doc-kinds"], "清单内文档整件消失（写法判据须跳过缺件，不误报）",
       lambda e: e.delete("docs/library.md")),
    _m("dockinds-last-updated-removed", ["doc-kinds"], "去掉「最后更新」位（本契约只看四型，不该受影响）",
       lambda e: e.patch("docs/library.md", "> 最后更新：", "> 更新于：")),
    _m("dockinds-instruction-mark-removed", ["doc-kinds"], "去掉「⛔ 操作指令」标识（打法写判据的 must_any）",
       lambda e: e.patch("docs/library.md", "> ⛔ 操作指令", "> 阅读材料")),
    _m("dockinds-rule-break", ["doc-kinds"], "把 how-to 实例的可执行命令块与围栏拆掉（该型写法未定型 → WARN+1）",
       lambda e: (e.patch_all("docs/layers.md", "```", "'''"),
                  e.patch_all("docs/layers.md", "scripts/nf.py", "scripts/nf-note.py"))),
    _m("dockinds-warn-count-up", ["doc-kinds"], "再拆一件原本定型的 how-to（WARN 计数应 +1，detail 数要一致）",
       lambda e: (e.patch_all("docs/receipts.md", "```", "'''"),
                  e.patch_all("docs/receipts.md", "scripts/nf.py", "scripts/nf-note.py"))),
    _m("dockinds-warn-count-down", ["doc-kinds"], "把一条 missing「步骤序列」的 tutorial 补上步骤（WARN 计数应 −1）",
       lambda e: e.write("docs/45_M2_回合级drill.md", "# 回合级 drill\n\n1. 步骤一：先看状态头\n2. 步骤二：再跑一遍\n")),

    # ---------------------------------------------------------- IDL / schema（schema-clean）
    _m("schema-dialect-drift", ["schema-clean"], "schema 声明的方言与校验器实现不一致",
       lambda e: e.patch("protocol/schema/contract.schema.json",
                         '"$schema": "https://json-schema.org/draft/2020-12/schema"',
                         '"$schema": "https://json-schema.org/draft-07/schema"')),
    _m("schema-unknown-keyword", ["schema-clean"], "schema 用了校验器未实现的关键字（子集越界）",
       lambda e: e.patch("protocol/schema/contract.schema.json", "\"properties\": {",
                         "\"oneOf\": [],\n  \"properties\": {")),
    _m("schema-missing-id", ["schema-clean"], "schema 缺 $id（元结构与装配都该报）",
       lambda e: e.patch("protocol/schema/module.schema.json", '"$id": "module.schema.json",', "")),
    _m("schema-contract-unknown-field", ["schema-clean"], "模块契约出现词表外字段（additionalProperties=False）",
       lambda e: e.patch("04_模块库/世界类/M08_季节天气.md", "  schema: \"1\"\n", "  schema: \"1\"\n  未知扩展键: 1\n")),
    _m("schema-contract-propertynames", ["schema-clean"], "模块契约键名越 propertyNames 模式",
       lambda e: e.patch("04_模块库/世界类/M08_季节天气.md", "  schema: \"1\"\n", "  schema: \"1\"\n  BadKey: 1\n")),
    _m("schema-contract-required-missing", ["schema-clean"], "模块契约缺必填字段（layer）",
       lambda e: e.patch("04_模块库/世界类/M08_季节天气.md", "  layer: P10\n", "")),
    _m("schema-contract-enum", ["schema-clean"], "conformance 取值越枚举",
       lambda e: e.patch("04_模块库/世界类/M08_季节天气.md", "  conformance: \"L2\"\n", "  conformance: \"L9\"\n")),
    _m("schema-contract-pattern", ["schema-clean"], "模块 id 不匹配 pattern",
       lambda e: e.patch("04_模块库/世界类/M08_季节天气.md", "  id: M08\n", "  id: Z08\n")),
    _m("schema-protocol-type", ["schema-clean"], "协议件 assets.count 变字符串（type: integer 应报）",
       lambda e: e.patch("community/AI农业域包/protocol.yaml", "    count: 3\n", "    count: \"3\"\n")),
    _m("schema-registry-missing", ["schema-clean"], "registry.json 整件消失（读取/解析失败）",
       lambda e: e.delete("desktop/src/core/registry.json")),
    _m("schema-provenance-missing", ["schema-clean"], "资产台账整件消失",
       lambda e: e.delete("05_资产库/provenance.json")),
    _m("schema-pipeline-fence-broken", ["schema-clean"], "管线围栏标记坏掉（Pipeline yaml 缺失/解析失败）",
       lambda e: e.patch("03_管线库/P00_通用文档生成管线.md", "```yaml", "```yml")),

    # ------------------------------------------------- 一致性声明（declaration）
    _m("decl-version-drift", ["declaration"], "声明里的版本号与真源不一致",
       lambda e: e.patch("protocol/CONFORMANCE.md", "| protocol.yaml schema | `2` |",
                         "| protocol.yaml schema | `3` |")),
    _m("decl-scope-ghost", ["declaration"], "scope 白名单里的路径不存在",
       lambda e: e.patch("protocol/CONFORMANCE.md", "- `skills`\n", "- `skills`\n- `不存在的目录`\n")),
    _m("decl-exclude-overlap", ["declaration"], "排除项与 scope 重叠（同一条不能既在范围又排除）",
       lambda e: e.patch("protocol/CONFORMANCE.md", "| `results` |", "| `library` |")),
    _m("decl-unverifiable-row", ["declaration"], "声明了真源里没有的规范项（不许用声明充数）",
       lambda e: e.patch("protocol/CONFORMANCE.md", "| 规范 | 版本 | 真源 |",
                         "| 规范 | 版本 | 真源 |\n| 不存在的规范 | `1` | 无 |")),
    _m("decl-excluded-section-missing", ["declaration"], "整段「排除」缺失（显式排除是声明的核心价值）",
       lambda e: e.patch("protocol/CONFORMANCE.md", "## 排除\n", "## 排除项\n")),

    # ------------------------------------------------- ST 制卡质量规范（st-quality）
    _m("stq-rule-dup", ["st-quality"], "规则 id 重复",
       lambda e: e.json_edit("protocol/st_quality.json", _stq_dup)),
    _m("stq-scope-prefix", ["st-quality"], "规则 id 前缀与 scope 不一致",
       lambda e: e.json_edit("protocol/st_quality.json",
                             lambda d: d["rules"][0].__setitem__("scope", "W"))),
    _m("stq-missing-basis", ["st-quality"], "规则缺必填字段 basis",
       lambda e: e.json_edit("protocol/st_quality.json",
                             lambda d: d["rules"][0].__setitem__("basis", ""))),
    _m("stq-checklist-miss", ["st-quality"], "自查清单未覆盖规则（清单不是装饰）",
       lambda e: e.patch("docs/st-quality-checklist.md", "| C1 |", "| C1x |")),
    _m("stq-v2-initial-extra", ["st-quality"], "V2：initial 含未声明变量",
       lambda e: e.json_edit("docs/examples/mvu-output/mvu_variables.json",
                             lambda d: d["initial"].__setitem__("不存在的变量", 0))),

    # ------------------------------------------------- B 线包装声明（mcp-package）
    _m("mcp-tool-drift", ["mcp-package"], "声明的工具面与运行时不一致（上架材料会漂移）",
       lambda e: e.json_edit("protocol/mcp_package.json",
                             lambda d: d["package"]["tools"].pop())),
    _m("mcp-category-out", ["mcp-package"], "包类目越词表",
       lambda e: e.json_edit("protocol/mcp_package.json",
                             lambda d: d["package"].__setitem__("category", "marketing"))),
    _m("mcp-redlines-empty", ["mcp-package"], "红线为空（纪律必须成文）",
       lambda e: e.json_edit("protocol/mcp_package.json",
                             lambda d: d.__setitem__("red_lines", []))),
    _m("mcp-schema-drift", ["mcp-package"], "包装声明 schema 不匹配",
       lambda e: e.json_edit("protocol/mcp_package.json",
                             lambda d: d.__setitem__("schema", "nf-mcp-package/2"))),

    # ------------------------------------------------- 条件先行（state-front）
    _m("sf-family-member-violation", ["state-front"], "族内件未通过 condition-first（状态块未前置）",
       lambda e: e.patch("docs/examples/state-front/nf1_front.md", "## 状态块（条件先行摘要）", "## 摘要")),
    _m("sf-family-short", ["state-front"], "族成员不足（min_members 未满足）",
       lambda e: e.delete("docs/examples/state-front/p03_front.md")),
    _m("sf-schema-drift", ["state-front"], "条件先行声明 schema 不匹配",
       lambda e: e.json_edit("protocol/state_front.json",
                             lambda d: d.__setitem__("schema", "nf-state-front/2"))),

    # ------------------------------------------------- 接力协议（handover）
    _m("ho-status-out", ["handover"], "交接件 status 越词表",
       lambda e: e.patch("handovers/HO-0001-W1到W2.md", "status: open", "status: pending")),
    _m("ho-date-bad", ["handover"], "交接件 date 非 YYYY-MM-DD",
       lambda e: e.patch("handovers/HO-0001-W1到W2.md", "date: 2026-09-15", "date: 2026/09/15")),
    _m("ho-section-missing", ["handover"], "正文缺必备段（层级被改）",
       lambda e: e.patch("handovers/HO-0001-W1到W2.md", "## 情境\n", "### 情境\n")),
    _m("ho-pending-no-criteria", ["handover"], "未决项缺判据（怎样算完成）",
       lambda e: e.patch("handovers/HO-0001-W1到W2.md", "判据", "说明")),
    _m("ho-ref-ghost", ["handover"], "refs 指向不存在的件",
       lambda e: e.patch("handovers/HO-0001-W1到W2.md", "  - verify.sh\n", "  - verify-不存在.sh\n")),
    _m("ho-decl-schema-drift", ["handover"], "交接协议声明 schema 不匹配",
       lambda e: e.json_edit("protocol/handover.json",
                             lambda d: d.__setitem__("schema", "nf-handover/2"))),

    # ------------------------------------------------- 复盘（postmortem）
    _m("po-blame-token", ["postmortem"], "复盘正文出现指责性归因词（对事不对人）",
       lambda e: e.patch("postmortems/PO-0001-冻结顺序事故.md", "## 影响\n", "## 影响\n\n个人失误导致。\n")),
    _m("po-root-not-mechanism", ["postmortem"], "根因段未指向机制",
       lambda e: e.json_edit("protocol/postmortem.json",
                             lambda d: d.__setitem__("root_cause_tokens", ["绝不出现的机制词"]))),
    _m("po-action-missing-owner", ["postmortem"], "行动项缺负责人（不可指派）",
       lambda e: e.patch("postmortems/PO-0001-冻结顺序事故.md", "**负责人**", "**承接方**")),
    _m("po-closed-unanchored", ["postmortem"], "status=closed 但未被协议回执锚定",
       lambda e: e.patch("postmortems/PO-0001-冻结顺序事故.md", "status: open", "status: closed")),
    _m("po-trigger-ghost", ["postmortem"], "trigger 指向不存在的 check",
       lambda e: e.patch("postmortems/PO-0001-冻结顺序事故.md", "trigger: check35", "trigger: check404")),

    # ------------------------------------------------- 审计（audit）
    _m("audit-subject-drift", ["audit"], "被审对象已变，旧审计失效（digest 绑定）",
       lambda e: e.patch("desktop/src/core/audit.py", '"""审计 / 验收门禁', '"""审计 / 验收门禁（已改）')),
    _m("audit-verdict-out", ["audit"], "审计 verdict 越词表",
       lambda e: e.json_edit("protocol/audit.json",
                             lambda d: d.__setitem__("verdict_vocabulary", ["pass", "fail"]))),
    _m("audit-rules-empty", ["audit"], "审计纪律为空",
       lambda e: e.json_edit("protocol/audit.json", lambda d: d.__setitem__("rules", []))),
    _m("audit-subject-format", ["audit"], "subjects 条目缺 :sha256 形态",
       lambda e: e.patch("results/audit/docs_audit-49-audit-protocol.md",
                         "  - protocol/audit.json:914c5dfe", "  - protocol/audit.json")),

    # ------------------------------------------------- 端点契约（endpoint-contract）
    _m("ep-maps-ghost-cli", ["endpoint-contract"], "maps_to 指向不存在的 CLI 子命令（契约不许指向空气）",
       lambda e: e.json_edit("protocol/endpoint_contract.json", _ep_set("assemble.plan", "maps_to", "nf 不存在的命令"))),
    _m("ep-maps-ghost-mcp", ["endpoint-contract"], "maps_to 指向不存在的 MCP 工具",
       lambda e: e.json_edit("protocol/endpoint_contract.json", _ep_set("library.read", "maps_to", "ghost_tool（MCP 工具）"))),
    _m("ep-method-out", ["endpoint-contract"], "method 越词表",
       lambda e: e.json_edit("protocol/endpoint_contract.json", _ep_set("assemble.plan", "method", "OPTIONS"))),
    _m("ep-dup-path", ["endpoint-contract"], "两个端点 method+path 重复",
       lambda e: e.json_edit("protocol/endpoint_contract.json", _ep_dup_path)),
    _m("ep-streaming-no-convention", ["endpoint-contract"], "声明 streaming 但 conventions 无 SSE 约定",
       lambda e: e.json_edit("protocol/endpoint_contract.json",
                             lambda d: d["conventions"].__setitem__("streaming", ""))),
    _m("ep-idempotency-silent", ["endpoint-contract"], "幂等语义沉默（不许沉默）",
       lambda e: e.json_edit("protocol/endpoint_contract.json",
                             lambda d: d["conventions"].__setitem__("idempotency", ""))),
    _m("ep-exception-ghost", ["endpoint-contract"], "幂等例外指向不存在的端点",
       lambda e: e.json_edit("protocol/endpoint_contract.json",
                             lambda d: d["idempotency_exceptions"][0].__setitem__("id", "不存在.端点"))),
    _m("ep-exception-no-why", ["endpoint-contract"], "幂等例外缺 why",
       lambda e: e.json_edit("protocol/endpoint_contract.json",
                             lambda d: d["idempotency_exceptions"][0].__setitem__("why", ""))),
    _m("ep-deprecated-unimplemented", ["endpoint-contract"], "未实装却声明 deprecated（没有可弃用的东西）",
       lambda e: e.json_edit("protocol/endpoint_contract.json",
                             lambda d: d["endpoints"][0].__setitem__("deprecated", True))),
    _m("ep-sunset-orphan", ["endpoint-contract"], "未声明 deprecated 却带 sunset（悬空弃用字段）",
       lambda e: e.json_edit("protocol/endpoint_contract.json",
                             lambda d: d["endpoints"][0].__setitem__("sunset", "2027-01-01"))),
    _m("ep-schema-drift", ["endpoint-contract"], "端点契约 schema 不匹配",
       lambda e: e.json_edit("protocol/endpoint_contract.json",
                             lambda d: d.__setitem__("schema", "nf-endpoint/2"))),

    # ------------------------------------------------- 模块边界签名（module-signature）
    _m("ms-boundary-drift", ["module-signature"], "边界字段变了但未重签（漂移即 FAIL）",
       lambda e: e.patch("04_模块库/世界类/M08_季节天气.md", "  inputs: [通用:M10]\n", "  inputs: [通用:M99]\n")),
    _m("ms-non-boundary-change", ["module-signature"], "只改非边界文本（description/note）→ 不该报漂移",
       lambda e: e.patch("04_模块库/世界类/M08_季节天气.md", "  name: 季节天气\n", "  name: 季节天气（改了名字，非边界字段）\n")),
    _m("ms-new-module", ["module-signature"], "新模块未签边界（WARN 挂账）",
       lambda e: e.write("04_模块库/世界类/M99_新模块.md", _new_module_doc("M99"))),
    _m("ms-module-removed", ["module-signature"], "基线里的模块已不在仓库（提示撤签）",
       lambda e: e.delete("04_模块库/世界类/M08_季节天气.md")),
    _m("ms-baseline-missing", ["module-signature"], "边界基线整件消失",
       lambda e: e.delete("protocol/module_signatures.json")),
    _m("ms-baseline-digest-tamper", ["module-signature"], "基线摘要被改（等价于边界漂移）",
       lambda e: e.json_edit("protocol/module_signatures.json", _ms_tamper)),

    # ------------------------------------------------- 事件背书（event-backing）
    _m("eb-orphan-subscribe", ["event-backing"], "订阅的事件全仓无发布方且未挂账（hard FAIL）",
       lambda e: e.patch("04_模块库/世界类/M08_季节天气.md", "    subscribe: [tick_day]\n",
                         "    subscribe: [tick_day, 幽灵事件]\n")),
    _m("eb-allowlisted", ["event-backing"], "同一事件登记进外部通道后转为挂账（只 WARN）",
       lambda e: (e.patch("04_模块库/世界类/M08_季节天气.md", "    subscribe: [tick_day]\n",
                          "    subscribe: [tick_day, 幽灵事件]\n"),
                  e.json_edit("protocol/external_events.json",
                              lambda d: d["events"].__setitem__("幽灵事件", {"why": "外部通道"})))),
    _m("eb-cross-pkg", ["event-backing"], "官方核心订阅只由社区包发布的事件（跨包 WARN）",
       lambda e: e.patch("04_模块库/世界类/M08_季节天气.md", "    subscribe: [tick_day]\n",
                         "    subscribe: [tick_day, d14_report_ready]\n")),
    _m("eb-allowlist-broken-json", ["event-backing"], "外部通道挂账件 JSON 损坏（视为空表，不崩）",
       lambda e: e.write("protocol/external_events.json", "{这不是 JSON\n")),

    # ------------------------------------------------- 类型积压台账（type-backlog）
    _m("tb-note-missing", ["type-backlog"], "untyped 字段缺 note（无声增长）",
       lambda e: e.json_edit("protocol/event_registry.json", _tb_clear_note)),
    _m("tb-backlog-missing", ["type-backlog"], "在盘台账整件消失",
       lambda e: e.delete("protocol/type_backlog.json")),
    _m("tb-backlog-stale", ["type-backlog"], "台账过期（记录 ≠ 实测）",
       lambda e: e.json_edit("protocol/type_backlog.json",
                             lambda d: d.__setitem__("count", 0))),
    _m("tb-backlog-broken-json", ["type-backlog"], "台账 JSON 不可解析",
       lambda e: e.write("protocol/type_backlog.json", "{这不是 JSON\n")),
    _m("tb-narrowed-untracked", ["type-backlog"], "把一项 untyped 收窄为具体类型（台账未同步 → 应判过期）",
       lambda e: e.json_edit("protocol/event_registry.json", _tb_narrow)),

    # ------------------------------------------------- I/O 类型面（io-types）
    _m("io-kind-out", ["io-types"], "io_types 取值越词表",
       lambda e: e.patch("04_模块库/世界类/M08_季节天气.md", "      season: string\n", "      season: 字符串\n")),
    _m("io-outputs-keyset", ["io-types"], "io_types.outputs 与 outputs 键集不一致（只 WARN）",
       lambda e: e.patch("04_模块库/世界类/M08_季节天气.md", "      region: untyped\n", "")),
    _m("io-outputs-extra", ["io-types"], "io_types.outputs 多了 outputs 里没有的键（只 WARN）",
       lambda e: e.patch("04_模块库/世界类/M08_季节天气.md", "      region: untyped\n",
                         "      region: untyped\n      幽灵产物: untyped\n")),
    _m("io-provably-mismatch", ["io-types"], "可证类型不匹配（消费方期望的产物类型提供方没声明）",
       lambda e: e.patch("04_模块库/世界类/M08_季节天气.md", "      通用:M10: untyped\n",
                         "      通用:M10: untyped\n      M50: boolean\n")),
    _m("io-missing-block", ["io-types"], "整块 io_types 被删（未收窄只 WARN）",
       lambda e: e.patch("04_模块库/世界类/M08_季节天气.md", "  io_types:\n", "  io_types_removed:\n")),

    # ------------------------------------------------- 管线抽象执行（pipeline-dryrun）
    _m("pd-module-missing", ["pipeline-dryrun"], "管线层引用了仓库里不存在的模块（hard FAIL）",
       lambda e: e.patch("03_管线库/P01_标准管线.md", "      default_modules: [M23]\n",
                         "      default_modules: [M23, 幽灵模块]\n")),
    _m("pd-dependency-order", ["pipeline-dryrun"], "依赖落在严格更后的层（依赖序违约）",
       lambda e: e.patch("03_管线库/P01_标准管线.md", "      default_modules: [M00]\n",
                         "      default_modules: [M00, M80]\n")),
    _m("pd-parse-fail", ["pipeline-dryrun"], "管线围栏坏掉（解析失败 → 契约执行异常，同 Python）",
       lambda e: e.patch("03_管线库/P01_标准管线.md", "```yaml\nPipeline:", "```yamz\nPipeline:")),
    _m("pd-type-conflict", ["pipeline-dryrun"], "同一 token 被两个模块声明为不同类型（类型冲突）",
       lambda e: e.patch("04_模块库/通用类/M50_主循环.md", "      text: untyped\n", "      text: number\n")),
    _m("pd-type-mismatch", ["pipeline-dryrun"], "执行集内期望的产物类型提供方没声明（可证不匹配）",
       lambda e: e.patch("04_模块库/通用类/M23_认知边界.md", "    inputs:\n      M00: state\n",
                         "    inputs:\n      M00: state\n      M10: boolean\n")),

    # ------------------------------------------------- 双源知识层（knowledge-sources）
    _m("ks-decl-missing", ["knowledge-sources"], "知识源声明整件消失",
       lambda e: e.delete("protocol/knowledge_sources.json")),
    _m("ks-schema-drift", ["knowledge-sources"], "声明 schema 不匹配",
       lambda e: e.json_edit("protocol/knowledge_sources.json",
                             lambda d: d.__setitem__("schema", "nf-knowledge-sources/2"))),
    _m("ks-vocab-drift", ["knowledge-sources"], "authority 词表与判据不一致",
       lambda e: e.json_edit("protocol/knowledge_sources.json",
                             lambda d: d.__setitem__("authority_vocabulary", ["contract"]))),
    _m("ks-locator-ghost", ["knowledge-sources"], "locator 指向不存在的件（防纸面源）",
       lambda e: e.json_edit("protocol/knowledge_sources.json",
                             lambda d: d["sources"][0].__setitem__("locator", "不存在的目录"))),
    _m("ks-reference-no-label", ["knowledge-sources"], "参考级未要求标注来源（外部数据不得写死）",
       lambda e: e.json_edit("protocol/knowledge_sources.json",
                             lambda d: d["sources"][3].__setitem__("requires_source_label", False))),
    _m("ks-reference-bad-policy", ["knowledge-sources"], "参考级时效策略非法",
       lambda e: e.json_edit("protocol/knowledge_sources.json",
                             lambda d: d["sources"][3]["freshness"].__setitem__("policy", "stale_after"))),
    _m("ks-order-broken", ["knowledge-sources"], "query_order 未把合同级排在参考级之前",
       lambda e: e.json_edit("protocol/knowledge_sources.json",
                             lambda d: d.__setitem__("query_order",
                                                     [d["query_order"][3]] + d["query_order"][:3] + d["query_order"][4:]))),
    _m("ks-order-mismatch", ["knowledge-sources"], "query_order 与 sources 不是同一集合",
       lambda e: e.json_edit("protocol/knowledge_sources.json",
                             lambda d: d.__setitem__("query_order", d["query_order"][:-1]))),
    _m("ks-transform-missing", ["knowledge-sources"], "消化记录整件消失",
       lambda e: e.delete("protocol/transform_log.json")),
    _m("ks-usage-missing", ["knowledge-sources"], "频率台账整件消失",
       lambda e: e.delete("protocol/knowledge_usage.json")),
    _m("ks-usage-ghost-source", ["knowledge-sources"], "频率台账含未声明的源（防幽灵频次）",
       lambda e: e.json_edit("protocol/knowledge_usage.json",
                             lambda d: d["counts"].__setitem__("幽灵源", 1))),
    _m("ks-type-field-missing", ["knowledge-sources"], "源缺必填字段（kind）",
       lambda e: e.json_edit("protocol/knowledge_sources.json",
                             lambda d: d["sources"][0].pop("kind", None))),
    _m("ks-cognition-ghost", ["knowledge-sources"], "认知裁剪模块不在册",
       lambda e: e.json_edit("protocol/knowledge_sources.json",
                             lambda d: d["cognition"].__setitem__("filter_module", "M99"))),
]


def python_contract(py_src: str, cid: str, root: str):
    from core import conformance_report as cr
    fn = dict((i, f) for i, f, _ in cr.CONTRACTS).get(cid)
    if fn is None:
        raise SystemExit("Python 侧无此契约：%s" % cid)
    try:
        ok, detail = fn(root)
    except Exception as exc:
        ok, detail = False, "契约执行异常：%s" % exc
    return bool(ok), detail


def net_contract(cli: str, cid: str, root: str):
    proc = subprocess.run([cli, "--conformance-one", cid, root], capture_output=True)
    if proc.returncode != 0:
        raise SystemExit("nfparity 退出码 %d：%s" % (proc.returncode,
                                                   proc.stderr.decode("utf-8", "replace")))
    return json.loads(proc.stdout.decode("utf-8"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True, help="只读快照（真源）")
    ap.add_argument("--py-src", required=True, help="快照的 desktop/src")
    ap.add_argument("--cli", required=True, help="nfparity 可执行体")
    ap.add_argument("--work", default="", help="工作副本目录（默认 <root>-fuzz）")
    ap.add_argument("--only", default="", help="只跑契约 id 含该子串的变异")
    ap.add_argument("--strict", action="store_true", help="文案分歧也算失败")
    ap.add_argument("--keep", action="store_true", help="保留工作副本（默认删除）")
    args = ap.parse_args()

    sys.path.insert(0, args.py_src)
    root = Path(args.root).resolve()
    work = Path(args.work).resolve() if args.work else root.parent / (root.name + "-fuzz")

    print("快照（只读）：%s" % root)
    print("工作副本    ：%s" % work)
    print("引擎        ：%s\n" % args.cli)

    if work.exists():
        shutil.rmtree(work)
    shutil.copytree(root, work, symlinks=True,
                    ignore=shutil.ignore_patterns("_py_conformance.json", "_net_*.json",
                                                  "_net_root.txt", "_cli_check.txt",
                                                  "_final_conformance_check.txt"))

    stats: dict[str, dict[str, int]] = {}
    divergences: list[tuple] = []
    text_only: list[tuple] = []
    tolerated: list[tuple] = []

    for mut in MUTATIONS:
        if args.only and not any(args.only in c for c in mut["contracts"]):
            continue
        edit = Edit(work)
        try:
            mut["apply"](edit)
        except Exception as exc:
            edit.rollback()
            print("SKIP   %-28s 变异未生效：%s" % (mut["name"], exc))
            continue
        try:
            for cid in mut["contracts"]:
                py_ok, py_detail = python_contract(args.py_src, cid, str(work))
                net = net_contract(args.cli, cid, str(work))
                bucket = stats.setdefault(cid, dict(cases=0, verdict_ok=0, text_ok=0))
                bucket["cases"] += 1
                verdict_same = py_ok == net["ok"]
                text_same = (py_detail == net["detail"]
                             and contract_digest(cid, py_ok, py_detail) == net["digest"])
                bucket["verdict_ok"] += 1 if verdict_same else 0
                bucket["text_ok"] += 1 if (verdict_same and text_same) else 0
                tag = "OK  " if (verdict_same and text_same) else ("TEXT" if verdict_same else "DIFF")
                print("%-5s %-28s %-20s py=%-5s net=%-5s %s"
                      % (tag, mut["name"], cid, py_ok, net["ok"],
                         (py_detail if not text_same else "一致")[:70]))
                if not verdict_same:
                    divergences.append((mut["name"], cid, py_ok, py_detail, net))
                elif not text_same:
                    (tolerated if mut.get("tolerated_text") else text_only).append(
                        (mut["name"], cid, py_detail, net["detail"]))
        finally:
            edit.rollback()

    print("\n按契约汇总（cases / 裁决一致 / 裁决+文案一致）：")
    for cid, b in sorted(stats.items()):
        flag = "" if b["verdict_ok"] == b["cases"] else "   ← 有裁决分歧"
        print("  %-28s %d / %d / %d%s" % (cid, b["cases"], b["verdict_ok"], b["text_ok"], flag))

    total = sum(b["cases"] for b in stats.values())
    v_ok = sum(b["verdict_ok"] for b in stats.values())
    t_ok = sum(b["text_ok"] for b in stats.values())
    print("\n差分模糊：%d 次比较 · 裁决一致 %d · 文案一致 %d（另 %d 例差异来自各自运行时的异常文本，不可约）"
          % (total, v_ok, t_ok, len(tolerated)))

    for name, cid, py_ok, py_detail, net in divergences:
        print("  [裁决分歧] %s / %s\n      py=(%s, %r)\n      net=(%s, %r)"
              % (name, cid, py_ok, py_detail, net["ok"], net["detail"]))
    for name, cid, py_detail, net_detail in text_only:
        print("  [文案分歧] %s / %s\n      py=%r\n      net=%r" % (name, cid, py_detail, net_detail))
    for name, cid, py_detail, net_detail in tolerated:
        print("  [平台文案] %s / %s（裁决一致，异常文本随运行时）\n      py=%r\n      net=%r"
              % (name, cid, py_detail, net_detail))

    if not args.keep:
        shutil.rmtree(work, ignore_errors=True)
    if divergences:
        return 1
    return 1 if (args.strict and text_only) else 0


if __name__ == "__main__":
    raise SystemExit(main())
