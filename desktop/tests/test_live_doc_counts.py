# -*- coding: utf-8 -*-
"""活文档不得钉运行时计数（check 数 / PASS 数）——「内外口径统一」的可核判据。

为什么：仓库纪律写的是「活文档不钉运行时计数（钉死会漂）」，但此前只有人记着。本轮实测
（2026-09-30）在活文档里抓到四处真漂移——`CONTRIBUTING.md` 的社区包自检单还写
`check1–32`、`docs/42_M5_Release-checklist.md` 的模板还写 `check1-32 PASS=51，v2.22`、
`docs/fde-stack.md` 写 `check1-38 常驻`、`docs/decision-layer.md` 的示例把 `--gate "PASS=61"`
当范例——四条都比当前基线旧。

扫描面（2026-10-03 扩面）：除入口文档与 `docs/*.md` 外，**收入 `scripts/*.sh`**——实测
`scripts/gates_all.sh` 的横幅停在 `check1-36 PASS=59`（当时真源已 v2.30 / check1-40 / PASS=70），
而它既不是文档（不在原扫描面）也不是 CI 跑的脚本，于是长期无判据。同一类漂移在**脚本横幅**里
与在文档里一样会误导读者，故并入本判据；`skills/**` 一并收入（**agent 第一跳的文案**——与
`test_nf_cli` 的旗标可达判据把 skills 纳入同一理由：写错了没有人会替他改）；`.py` 暂不收
（`--help` 里的占位示例、探针的运行时输出格式会造假红，宁少勿滥）；`scripts/` 下**无扩展名**的可执行
启停器一并收入（2026-10-04 补：`scripts/nf` 是 208 行的 POSIX 启动器，属人对/agent 读的活文案，
但当按 `.sh` 取面时**整个漏掉**——按扩展名取面的典型漏面）。实测当前**零命中**：
8 个 `scripts/*.sh` + 1 个 `scripts/nf` + 5 个 `skills/**` 都没有钉运行时计数
（`scripts/nf` 里的 `1.7 ms` / `260.9 ms` 属**带日期的计时记录**，不是运行时时点计数，判据不拦）。

口径（防误杀）：
- 豁免面：`CHANGELOG.md` / `VERSION-MATRIX.md`（发布史，记录当时值即其本分）、
  `docs/verification-cards.md`（由 `verify.sh` 生成，数字由生成器保证）、`docs/examples/**`
  与 `docs/reference/**`（样本与外部材料）、以及 README / llms.txt 里
  `<!-- nf:stats:begin --> … <!-- nf:stats:end -->` 的生成区（`nf stats --write` 刷新）。
- 历史留痕：同一行里出现「曾 / 历史 / 此前 / 漂移 / 旧 / 年份」即视为刻意留痕，放行
  （例：`CONTRIBUTING.md` 把「曾落后到 check1-36/PASS=59」写进句中，正是要留这段证据）。
- **协议根文档（`01_核心协议.md` / `02_联动注册表.md` / `06_` / `07_`）刻意不在面内（2026-10-04 实测）**：
  前两件在「校验回读」块里逐波记 `PASS=20/22/57/61`、`check1-35/37` 等**当时值**（01 有 16 行、02 有 1 行），
  而这些**行内不含**上一条的历史留痕词（「保持」「校验回读」都不是）⇒ 纳入面会**当场假红**。
  要给它们补留痕词也不便宜：`01_核心协议.md` 在 **receipts / normative 面内**（
  `protocol/generated/receipt_chain.json`、`protocol/normative.json`、`protocol/LAYERS.json` 都引用它），
  改它即让回执链过期——那是冻结链的活，不是顺手改的活。故本判据只覆盖**入口文档 + `docs/` + `scripts/` + `skills/`**；
  要收 01/02 的正确顺序是：**先给那些行补历史留痕词 → 再纳入面 → 最后走冻结链刷新回执**。
"""
import json
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

ENTRY_DOCS = ("README.md", "README.en.md", "CONTRIBUTING.md", "AGENT_START.md", "AI_ROUTING.md",
              "DEEP_DIVE.md", "ROADMAP.md", "SECURITY.md", "ROUTES.md", "llms.txt")
EXEMPT = {"CHANGELOG.md", "VERSION-MATRIX.md", "docs/verification-cards.md"}
EXEMPT_PREFIX = ("docs/examples/", "docs/reference/", "community/", "results/", "library/")

COUNT = re.compile(r"PASS=\d+|check1-\d+")
HISTORY = ("曾", "历史", "此前", "漂移", "旧", "当波", "当时", "本波", "2026-", "2025-")
_STATS_BLOCK = re.compile(r"<!-- nf:stats:begin -->.*?<!-- nf:stats:end -->", re.S)


def pinned_counts(text: str) -> list:
    """→ 钉了运行时计数且未留历史痕迹的行（纯函数，便于变异自证）。"""
    text = _STATS_BLOCK.sub("", text)
    out = []
    for n, line in enumerate(text.splitlines(), 1):
        if COUNT.search(line) and not any(h in line for h in HISTORY):
            out.append((n, line.strip()))
    return out


def live_docs() -> list:
    # `-z` 是必须的：`git ls-files` 默认把**非 ASCII 路径**转义成 `"\346\241\243..."` 并加引号，
    # 于是按空白切分后 `docs/45_质量纵深收口总档.md` 这类件名根本对不上前缀判据——判据会
    # **静默漏掉整批中文名文档**（本判据首版就栽在这里：实测只扫到 ASCII 名，漏 13 处命中）。
    listed = subprocess.run(["git", "ls-files", "-z"], cwd=str(ROOT), capture_output=True,
                            text=True, encoding="utf-8", errors="replace",
                            timeout=300).stdout.split("\0")
    out = []
    for rel in listed:
        if not rel:
            continue
        if rel in EXEMPT or rel.startswith(EXEMPT_PREFIX):
            continue
        if (rel in ENTRY_DOCS
                or (rel.startswith("docs/") and rel.endswith(".md"))
                or (rel.startswith("scripts/") and rel.endswith(".sh"))
                or (rel.startswith("scripts/") and "." not in Path(rel).name)
                or rel.startswith("skills/")):
            out.append(rel)
    return out


class LiveDocCountTest(unittest.TestCase):
    def test_live_docs_do_not_pin_runtime_counts(self):
        bad = []
        for rel in live_docs():
            text = (ROOT / rel).read_text(encoding="utf-8", errors="replace")
            for n, line in pinned_counts(text):
                bad.append("%s:%d %s" % (rel, n, line[:80]))
        self.assertEqual([], bad, "活文档钉了运行时计数（修复指引：改为指向 `nf stats --check` "
                                  "生成区 / `quality_baseline.EXPECTED_*`，或就地写明历史留痕）")

    def test_predicate_catches_the_mutation(self):
        """变异自证：钉死必判红；生成区、历史留痕、占位写法都不许误报。"""
        self.assertTrue(pinned_counts("`bash verify.sh`（check1-32 PASS=51，v2.22）0 WARN。"))
        self.assertFalse(pinned_counts("`bash verify.sh` 全绿（曾停在 check1-32/PASS=51）。"))
        self.assertFalse(pinned_counts("<!-- nf:stats:begin -->\ncheck1-39 · PASS=68\n"
                                       "<!-- nf:stats:end -->\n"))
        self.assertFalse(pinned_counts('--gate "PASS=<当次 verify 输出的 PASS 数>"'))


#: 总量口径的声明（近旁须有「全部/共/覆盖/总计/一共」——子集计数如「14 个声明了 --root 的
#: 命令」不算，首版探针就是这么误报的）。
TOTAL_COUNT = re.compile(r"(?:全部|共|覆盖|总计|一共)\s*(\d+)\s*(个命令|项契约|件回执|个只读工具)")


def total_claims(text: str) -> list:
    """→ `[(行号, 数字, 单位)]`（纯函数，便于变异自证）。"""
    return [(n, int(m.group(1)), m.group(2))
            for n, line in enumerate(text.splitlines(), 1) for m in TOTAL_COUNT.finditer(line)]


class LiveTotalCountTest(unittest.TestCase):
    """活文档里的**总量**声明必须与实测一致（上一轮抓到过一处这类漂移：`docs/terminal.md`
    写着「覆盖全部 64 个命令」而实际 65）。与 `LiveDocCountTest` 的分工：那边禁「钉运行时
    计数」，这边管「已经钉了的总量必须准」——两者互补，都属「内外口径统一」。
    """

    def _live(self) -> dict:
        def json_of(argv):
            p = subprocess.run([sys.executable, str(ROOT / "scripts" / "nf.py"), *argv],
                               cwd=str(ROOT), capture_output=True, text=True,
                               encoding="utf-8", errors="replace", timeout=300)
            return json.loads(p.stdout or "{}")
        rows = json_of(["shell", "--commands", "--json"])
        paths = [r["path"] for r in (rows.get("commands") or rows.get("rows") or [])]
        mcp = json.loads((ROOT / "protocol" / "mcp_package.json").read_text(encoding="utf-8"))
        return {"个命令": len({p.split()[0] for p in paths}),
                "项契约": int(((json_of(["conformance", "--json"]).get("report") or {})
                              .get("total")) or 0),
                "件回执": int((json_of(["receipts", "--json"]).get("stats") or {})
                             .get("entries") or 0),
                "个只读工具": len((mcp.get("package") or {}).get("tools") or [])}

    def test_total_claims_match_live_values(self):
        live = self._live()
        bad = []
        for rel in live_docs():
            text = (ROOT / rel).read_text(encoding="utf-8", errors="replace")
            for n, num, unit in total_claims(text):
                if unit in live and num != live[unit]:
                    bad.append("%s:%d 写 %d %s（实测 %d）" % (rel, n, num, unit, live[unit]))
        self.assertEqual([], bad, "活文档的总量声明与实测不符（改文档或改行为）：%s" % bad)

    def test_predicate_catches_the_mutation(self):
        self.assertTrue(total_claims("能力地图：8 个能力族，覆盖全部 64 个命令"))
        self.assertFalse(total_claims("本轮把声明了 `--root` 的 14 个命令逐个真跑"))
        self.assertFalse(total_claims("`nf conformance` 报 27 项契约通过"))


#: 顶层 `count`/`total` 刻意**不数同层集合**的文件 → 理由（当前为空；有例外必须逐条写明）。
NAMED_COUNTS: dict = {}


def self_counts(root: Path) -> dict:
    """→ `{文件名: (键, 自述值, [同层集合长度…])}`（纯函数，便于变异自证）。"""
    out = {}
    for p in sorted(Path(root).glob("*.json")):
        try:
            doc = json.loads(p.read_text(encoding="utf-8"))
        except ValueError:
            continue
        if not isinstance(doc, dict):
            continue
        for key in ("count", "total"):
            if isinstance(doc.get(key), int):
                out[p.name] = (key, doc[key],
                               sorted(len(v) for v in doc.values()
                                      if isinstance(v, (list, dict))))
    return out


def self_count_issues(root: Path) -> list:
    """→ 自述计数与同层集合长度对不上的清单（空 = 全部对得上）。"""
    bad = []
    for name, (key, value, lengths) in sorted(self_counts(root).items()):
        if name in NAMED_COUNTS:
            continue
        if value not in lengths:
            bad.append("%s:%s=%d（同层集合长度只有 %s）" % (name, key, value, lengths))
    return bad


class ProtocolSelfCountTest(unittest.TestCase):
    """`protocol/*.json` 的**自述计数**必须等于它数的那份集合（同层列表 / 字典的长度）。

    依据（2026-10-01）：`RECEIPTS.json:count=52`、`module_signatures.json:count=248`、
    `domain_packs.json:count=100`、`conformance_report.json:total=27` 这类**自述数字**是被人读、
    被文档引用、被脚本当接口用的；而此前只有**一次性盘点**（50 件 0 不一致），没有常驻判据 ——
    写盘逻辑改了（多一条回执 / 多一个模块）却忘了同步 `count`，没有任何东西会红。

    口径（**只判顶层**，宁少勿滥）：同层只要有一个集合（list 或 dict）的长度等于该值即算对得上；
    嵌套层不判——实测 `protocol/sast_baseline.json` 的 `meta.bandit.total`（SAST 命中数）与
    `results/interop/intoto.json` 的 `predicate.count`（第三方标准里的 subject 数）都**不是**
    「同层集合长度」，硬判会造假红（本判据首版就撞上这两类）。
    """

    def test_self_counts_match_their_collections(self):
        counts = self_counts(ROOT / "protocol")
        self.assertGreaterEqual(len(counts), 8,
                                "没扫到足够的自述计数（判据可能已失效）：%s" % sorted(counts))
        bad = self_count_issues(ROOT / "protocol")
        self.assertEqual([], bad,
                         "自述计数与它数的集合对不上（修复指引：重跑对应的 `--write` 生成器，"
                         "或把该文件写进 NAMED_COUNTS 并说明它数的是什么）：%s" % bad)

    def test_named_counts_are_not_stale(self):
        counts = self_counts(ROOT / "protocol")
        stale = sorted(k for k in NAMED_COUNTS if k not in counts)
        self.assertEqual([], stale, "NAMED_COUNTS 里有已消失（或已无自述计数）的文件：%s" % stale)

    def test_mutation_lying_count_is_caught(self):
        """变异自证：写 3 条却自述 `count: 2` 必须被抓；对得上的一律放行。"""
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "a.json").write_text(
                json.dumps({"count": 2, "entries": [1, 2, 3]}), encoding="utf-8")
            (Path(tmp) / "b.json").write_text(
                json.dumps({"total": 2, "rows": [1, 2]}), encoding="utf-8")
            bad = self_count_issues(Path(tmp))
        self.assertEqual(1, len(bad), "变异未被抓到：%s" % bad)
        self.assertIn("a.json:count=2", bad[0])


if __name__ == "__main__":
    unittest.main()
