# -*- coding: utf-8 -*-
"""思维链/对话转写暴露门禁：仓库文本面不得残留**内部推理**或**对话稿**（作者指令「思维链暴露删掉」）。

为什么：`AGENTS.md`「公开文案纪律」写明「不写决策过程」，多份产出纪律文档也要求交付是
**结果形态**。但这条纪律此前**没有机器判据**——一次会话里把模型的思考块、或
`用户：/助手：` 形式的对话稿粘进文档/代码，没人会拦。

口径（高精度，宁少勿滥）：
- **只认能不可能是正常内容**的形态：`<thinking>` 一类标签、行首 `Human:/Assistant:/System:`
  或 `用户：/助手：/系统：` 转写、`作为一个 AI`、`我的思考过程/内部推理/思考过程如下`、
  `chain of thought` 的英文写法。
- **刻意不认** `思维链` 一词本身：它是本仓的**主题词**（标准目录条目名、提示工程域包的
  细分名）——把主题词当泄漏会做成假红，由 `test_topic_word_is_not_flagged` 自证豁免。
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SKIP_PARTS = {".git", ".rivet", "__pycache__", ".ruff_cache", ".mypy_cache",
              "node_modules", ".pytest_cache"}
#: 扫描面按**「agent 可能读到」**取，而不是按「像代码」取（2026-10-01 扩面）：
#: 生成图（`.mmd` / `.graphml`：节点标签是人话）、PowerShell 门禁脚本（`.ps1`）、
#: 逐行记录（`.jsonl`）、构建配置（`.csproj` / `.props` / `.toml`）此前都不在面内——
#: 实测这些扩展名共 **222 件**、当时零命中，但**判据不在场就是假绿**（有人把转写粘进
#: `.ps1` 或图标签里没人会拦）。
EXTS = (".md", ".py", ".json", ".txt", ".yaml", ".yml", ".cs", ".csv", ".sh", ".cmd",
        ".mmd", ".graphml", ".ps1", ".jsonl", ".toml", ".csproj", ".props")
#: **无扩展名的文本件**：按名字点名（都能被 agent 读到）。判据会断言它们真的在场，
#: 免得改名后这条覆盖静默失效。
EXTRA_TEXT_FILES = ("scripts/nf", "LICENSE", ".gitattributes", ".gitignore")
#: 本判据自身的仓库相对路径（含负例样本 ⇒ 豁免，见 public_texts）
SELF = "desktop/tests/test_cot_exposure.py"

# 形态 -> 正则（大小写敏感：避免把 `system:` 这类正常键当转写）
PATTERNS = {
    "think_tag": re.compile(r"<\s*/?\s*(thinking|reasoning|analysis)\s*>"),
    "transcript_en": re.compile(r"(?m)^\s*(Human|Assistant|System)\s*:"),
    "transcript_zh": re.compile(r"(?m)^\s*(用户|助手|系统)\s*："),
    "ai_persona": re.compile(r"作为(一个)?\s*AI|As an AI\b"),
    "reasoning_talk": re.compile(r"我的思考过程|内部推理|思考过程如下|推理链如下"),
    "cot_en": re.compile(r"chain[- ]of[- ]thought|Chain-of-Thought"),
}


def scan_texts(texts: dict) -> list:
    """-> `[(相对路径, 形态名, 行号)]`（纯函数，便于变异自证）。"""
    hits = []
    for rel, text in sorted(texts.items()):
        for label, rx in PATTERNS.items():
            for m in rx.finditer(text):
                hits.append((rel, label, text.count("\n", 0, m.start()) + 1))
    return hits


def public_texts() -> dict:
    out = {}
    for p in ROOT.rglob("*"):
        if not p.is_file() or any(part in SKIP_PARTS for part in p.parts):
            continue
        rel0 = p.relative_to(ROOT).as_posix()
        if p.suffix.lower() not in EXTS and rel0 not in EXTRA_TEXT_FILES:
            continue
        rel = rel0
        if rel == SELF:
            # 本判据自身必然含**负例样本**（要用于变异自证的泄漏串）与形态名 ⇒ 豁免自身，
            # 与 test_leak_surface 豁免 probes/ 同一口径（豁免的是样本，不是真实产物）。
            continue
        try:
            out[rel] = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
    return out


class CotExposureTest(unittest.TestCase):
    def test_repo_has_no_chain_of_thought_or_transcript(self):
        hits = scan_texts(public_texts())
        self.assertEqual([], hits, "仓库文本面出现思维链/对话转写残留（修复指引：删掉推理过程，"
                         "只留**结果形态**的结论与判据；确属主题词请改口径并在此登记）：%s"
                         % hits[:10])


class CotRuleTest(unittest.TestCase):
    def test_scan_surface_covers_generated_graphs_and_shell_entries(self):
        """**扩面不得静默失效**：点名过的无扩展文本件必须真在场；且扫描面里要有生成图与 `.ps1`。"""
        for rel in EXTRA_TEXT_FILES:
            self.assertTrue((ROOT / rel).is_file(), "点名的无扩展文本件不见了：%s" % rel)
        texts = public_texts()
        self.assertTrue(any(r.endswith(".mmd") for r in texts), "生成图（.mmd）不在扫描面内")
        self.assertTrue(any(r.endswith(".graphml") for r in texts), "生成图（.graphml）不在扫描面内")
        self.assertTrue(any(r.endswith(".ps1") for r in texts), "PowerShell 门禁脚本不在扫描面内")
        self.assertIn("scripts/nf", texts, "启动器 scripts/nf 不在扫描面内（它是被 agent 读的文本件）")

    def test_topic_word_is_not_flagged(self):
        """变异自证：主题词 `思维链设计` 不许误报；真泄漏形态必判红。"""
        clean = {"community/x/assets/DOMAIN_SPEC.md":
                 "| `E01-04` | 思维链设计 | 口径 = 产出形态 / 目标受众 …|\n"}
        self.assertEqual([], scan_texts(clean), "主题词被误当泄漏")

    def test_real_leaks_are_flagged(self):
        self.assertTrue(scan_texts({"docs/x.md": "我的思考过程：先看 A，再看 B。\n"}),
                        "推理口播未被判红")
        self.assertTrue(scan_texts({"docs/y.md": "用户：帮我写\n助手：好的，我先…\n"}),
                        "中文对话稿未被判红")
        self.assertTrue(scan_texts({"docs/z.md": "Human: hi\nAssistant: ok\n"}),
                        "英文对话稿未被判红")
        self.assertTrue(scan_texts({"desktop/src/core/a.py": "<thinking>先这样</thinking>\n"}),
                        "思考块标签未被判红")


if __name__ == "__main__":
    unittest.main()
