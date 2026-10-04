"""为 `drill_fidelity` 生成分支级判据（期望值从真源生成；可反复重跑）。

真语料上该面是**全绿**的（`issues=0`、保真度 1.0）⇒ 只靠契约对账核不到任何错误分支。
本夹具逐分支踩：

- 执行演练：`fabricated_id` / `browse_repeat` / `no_citation` / `semantic_misalignment`
  四条硬断言各自的命中与不命中；`expect_captured` 未满足 ⇒ 保真度不足；
- 回合级：R-R1 缺引用 / R-R2 无推进 / R-R3 允许集外编号（含「带前缀 tok 与无前缀 allowed 同尾」豁免）/
  跳号 warn_gaps / 无回合标记；样本声明与实测不一致 ⇒ 未复现声明；
- 外层：找不到执行用例 / 找不到回合样本 / 坏 JSON。

用法：python engine/rust/tools/gen_drill_fidelity_branches.py
"""
import json
import pathlib
import shutil
import sys

ROOT = pathlib.Path('.').resolve()
sys.path.insert(0, str(ROOT / 'desktop' / 'src'))
from core import drill_fidelity as df  # noqa: E402

BASE = ROOT / 'engine' / 'rust' / 'target' / 'test-fixtures' / 'drill-fidelity-branches'
if BASE.exists():
    shutil.rmtree(BASE)

SRC_TEXT = "官方核心装配 P01：由 通用:M10 驱动节拍，事件候选经质量门后生成成品。"

EXEC_CASES = [
    # 四条硬断言各踩一次命中
    {"id": "c-fab", "output": "由 M99 完成本条推进。", "expect_captured": ["fabricated_id"]},
    {"id": "c-browse", "output": SRC_TEXT + " 就到这里。", "expect_captured": ["browse_repeat"]},
    {"id": "c-cite", "output": "结论：应当输出。", "expect_captured": ["no_citation"]},
    # M00 的职责词是「装配」，本句用的是通用:M10 的「节拍」⇒ 语义错位
    {"id": "c-sem", "output": "M00 负责节拍。", "expect_captured": ["semantic_misalignment"]},
    # guard：同原文复制但带推进信号 ⇒ 不得误报
    {"id": "g-progress", "output": SRC_TEXT + "回合推进：已进入第 5 回合。", "expect_captured": []},
    # 期望未满足 ⇒ passed != cases（保真度不足分支）
    {"id": "c-unsat", "output": "干干净净一句话，没有任何失范。", "expect_captured": ["no_citation"]},
]
EXEC = {
    "schema": "nf-execution-drill/1",
    "pipeline": "P01",
    "real_ids": ["M00", "通用:M10"],
    "semantics": {"M00": ["装配"], "通用:M10": ["节拍"]},
    "source_text": SRC_TEXT,
    "cases": EXEC_CASES,
}

ROUND_GOOD = {
    "schema": "nf-round-transcript/1",
    "verdict": "good",
    "transcript": "回合 1：引用 06 §3 推进，M00 写回 状态快照。\n"
                  "回合 2：引用 06 §3，通用:M10 输出并进入下一回合。\n",
    "allowed": ["M00", "通用:M10"],
}
# 声明 good 但实测 non-conformant ⇒ 未复现声明分支
ROUND_BAD = {
    "schema": "nf-round-transcript/1",
    "verdict": "good",
    "transcript": "回合 1：无引用也无推进。\n回合 3：引用 06 §3 推进，M99 越集。\n",
    "allowed": ["M00"],
}
# 无回合标记 ⇒ round_drill 的「未检测到回合标记」分支
ROUND_NOTURN = {
    "schema": "nf-round-transcript/1",
    "verdict": "bad",
    "transcript": "这里一个回合标记也没有。\n",
    "allowed": [],
}
# 允许集里写「通用:M10」，正文写裸「M10」⇒ 同尾豁免，不得报 R-R3
ROUND_TAIL = {
    "schema": "nf-round-transcript/1",
    "verdict": "good",
    "transcript": "回合 1：引用 06 §3 推进，M10 写回状态。\n",
    "allowed": ["通用:M10"],
}


def build(scenario, exec_doc, rounds, bad_json_exec=False, bad_json_round=False, extra=None):
    fix = BASE / scenario
    (fix / 'desktop' / 'tests' / 'fixtures' / 'execution' / 'rounds').mkdir(parents=True)
    if exec_doc is not None:
        p = fix / 'desktop' / 'tests' / 'fixtures' / 'execution' / 'p01_drill_cases.json'
        p.write_text('{ "broken": ' if bad_json_exec else json.dumps(exec_doc, ensure_ascii=False),
                     encoding='utf-8', newline='')
    for name, doc in rounds.items():
        p = fix / 'desktop' / 'tests' / 'fixtures' / 'execution' / 'rounds' / name
        p.write_text('{ "broken": ' if bad_json_round else json.dumps(doc, ensure_ascii=False),
                     encoding='utf-8', newline='')
    for rel, body in (extra or {}).items():
        q = fix / rel
        q.parent.mkdir(parents=True, exist_ok=True)
        q.write_text(body, encoding='utf-8', newline='')
    return fix


SCEN = {}
SCEN['kitchen'] = build('kitchen', EXEC,
                        {'good.json': ROUND_GOOD, 'bad.json': ROUND_BAD,
                         'noturn.json': ROUND_NOTURN, 'tail.json': ROUND_TAIL})
SCEN['empty'] = build('empty', None, {})
SCEN['badround'] = build('badround', None, {'bad.json': ROUND_BAD}, bad_json_round=True)
SCEN['badexec'] = build('badexec', EXEC, {'good.json': ROUND_GOOD}, bad_json_exec=True)

RESULTS = {}
for name, fix in SCEN.items():
    issues, warns, stats = df.scan(str(fix))
    RESULTS[name] = (issues, warns, stats)
    print('# 场景 %s：issues=%d warns=%d' % (name, len(issues), len(warns)))
    for x in issues:
        print('#   ! %s' % x)
    print('# stats = %s' % json.dumps(stats, ensure_ascii=False, sort_keys=True))

# 真源对「坏 JSON 的执行集」给出的原文（**含 CPython 解析器文本，本线不复刻**）
badexec_issue = RESULTS['badexec'][0][0]
print('# 坏 JSON 执行集真源原文 = %r' % badexec_issue)


def rj(s):
    assert '"#' not in s
    return 'r#"%s"#' % s


def arr(v):
    return "&[%s]" % ", ".join(json.dumps(x, ensure_ascii=False) for x in v)


TEMPLATE = r'''
    /// ===== 分支级差分判据（期望值由 `tools/gen_drill_fidelity_branches.py` 从真源生成）=====
    ///
    /// 真语料上本面**全绿**（`issues=0`、保真度 1.0）⇒ 对账核不到任何错误分支。本夹具逐分支踩：
    /// 执行演练四条硬断言（`fabricated_id` / `browse_repeat` / `no_citation` /
    /// `semantic_misalignment`）各自的命中与不命中、`expect_captured` 未满足 ⇒ 保真度不足；
    /// 回合级 R-R1 缺引用 / R-R2 无推进 / R-R3 越集（含「带前缀 tok ↔ 无前缀 allowed」同尾豁免）/
    /// 跳号 / 无回合标记；样本声明与实测不一致 ⇒ 未复现声明；找不到用例 / 找不到样本 / 坏 JSON。
    ///
    /// ⚠️ **坏 JSON 的执行集**那条 issue 里含 CPython `JSONDecodeError` 原文，**无法逐字复刻**：
    /// 本判据只断言其前缀（见 `badexec_needs_a_self_authored_prefix`），其余场景逐条全比。
    const DF_EXEC: &str = @@EXEC@@;
    const DF_ROUND_GOOD: &str = @@RGOOD@@;
    const DF_ROUND_BAD: &str = @@RBAD@@;
    const DF_ROUND_NOTURN: &str = @@RNOTURN@@;
    const DF_ROUND_TAIL: &str = @@RTAIL@@;

    fn build_df_fixture(scenario: &str, exec_doc: Option<&str>,
                        rounds: &[(&str, &str)]) -> std::path::PathBuf {
        let root = crate::testutil::fixture(&format!("drill-fidelity-branches-{}", scenario));
        let base = root.join("desktop/tests/fixtures/execution");
        std::fs::create_dir_all(base.join("rounds")).unwrap();
        if let Some(d) = exec_doc {
            std::fs::write(base.join("p01_drill_cases.json"), d).unwrap();
        }
        for (name, body) in rounds {
            std::fs::write(base.join("rounds").join(name), body).unwrap();
        }
        root
    }

    #[test]
    fn scan_matches_truth_source_branch_by_branch() {
        for (scenario, exec_doc, rounds, want_issues, want_cases, want_passed, want_fid, want_sets, want_rs) in [
            (
                "kitchen",
                Some(DF_EXEC),
                &[
                    ("good.json", DF_ROUND_GOOD),
                    ("bad.json", DF_ROUND_BAD),
                    ("noturn.json", DF_ROUND_NOTURN),
                    ("tail.json", DF_ROUND_TAIL),
                ][..],
                @@I1@@ as &[&str],
                @@C1@@,
                @@P1@@,
                @@F1@@,
                @@E1@@,
                @@R1@@,
            ),
            ("empty", None, &[][..], @@I2@@ as &[&str], @@C2@@, @@P2@@, @@F2@@, @@E2@@, @@R2@@),
        ] {
            let root = build_df_fixture(scenario, exec_doc, rounds);
            let (issues, warns, stats) = scan(&root);
            assert_eq!(issues, want_issues, "场景 {} 的 issues", scenario);
            assert!(warns.is_empty(), "本面 warns 恒空");
            let want_stats = crate::jsonread::convert(&serde_json::json!({
                "cases": want_cases, "passed": want_passed,
                "fidelity": want_fid, "exec_sets": want_sets, "round_samples": want_rs
            }))
            .unwrap();
            assert!(
                crate::jsonread::json_eq(&stats, &want_stats),
                "场景 {} 的 stats：实得 {:?}，期望 {:?}",
                scenario,
                stats,
                want_stats
            );
        }
    }

    #[test]
    fn bad_json_round_sample_matches_the_truth_source() {
        // 坏 JSON 的回合样本：真源那条**没有 `first_issue` 键** ⇒ `str(None)` = `"None"`
        let root = build_df_fixture("badround", None, &[("bad.json", "{ \"broken\": ")]);
        let (issues, _w, stats) = scan(&root);
        assert_eq!(issues, @@I3@@ as &[&str], "坏 JSON 回合样本的 issue 逐字一致");
        assert!(crate::jsonread::json_eq(
            &stats,
            &crate::jsonread::convert(&serde_json::json!({
                "cases": 1, "passed": 0, "fidelity": 0.0, "exec_sets": 0, "round_samples": 1
            }))
            .unwrap()
        ));
    }

    #[test]
    fn badexec_needs_a_self_authored_prefix() {
        // ⚠️ 已知偏差：真源 issue 尾部是 CPython `JSONDecodeError` 原文，本线措辞自拟。
        // 这里只断言「件名 + 自拟前缀」，不伪造真源文本。
        let root = build_df_fixture("badexec", Some("{ \"broken\": "), &[("good.json", DF_ROUND_GOOD)]);
        let (issues, _w, _s) = scan(&root);
        // 真源这里同样是 **2 条**：执行集坏掉 ⇒ `cases == 0` ⇒ 连带触发「找不到执行演练用例」
        assert_eq!(issues.len(), 2, "{:?}", issues);
        assert!(issues[0].starts_with("找不到执行演练用例"), "{}", issues[0]);
        assert!(
            issues[1].starts_with("p01_drill_cases.json JSON 不可解析："),
            "{}",
            issues[1]
        );
    }
'''

sc = RESULTS
text = (TEMPLATE
        .replace('@@EXEC@@', rj(json.dumps(EXEC, ensure_ascii=False)))
        .replace('@@RGOOD@@', rj(json.dumps(ROUND_GOOD, ensure_ascii=False)))
        .replace('@@RBAD@@', rj(json.dumps(ROUND_BAD, ensure_ascii=False)))
        .replace('@@RNOTURN@@', rj(json.dumps(ROUND_NOTURN, ensure_ascii=False)))
        .replace('@@RTAIL@@', rj(json.dumps(ROUND_TAIL, ensure_ascii=False)))
        .replace('@@I1@@', arr(sc['kitchen'][0]))
        .replace('@@I2@@', arr(sc['empty'][0]))
        .replace('@@I3@@', arr(sc['badround'][0]))
        .replace('@@C1@@', str(sc['kitchen'][2]['cases']))
        .replace('@@P1@@', str(sc['kitchen'][2]['passed']))
        .replace('@@C2@@', str(sc['empty'][2]['cases']))
        .replace('@@P2@@', str(sc['empty'][2]['passed']))
        .replace('@@F1@@', repr(sc['kitchen'][2]['fidelity']))
        .replace('@@E1@@', str(sc['kitchen'][2]['exec_sets']))
        .replace('@@R1@@', str(sc['kitchen'][2]['round_samples']))
        .replace('@@F2@@', repr(sc['empty'][2]['fidelity']))
        .replace('@@E2@@', str(sc['empty'][2]['exec_sets']))
        .replace('@@R2@@', str(sc['empty'][2]['round_samples'])))

BEGIN = '    // >>> GENERATED by tools/gen_drill_fidelity_branches.py（勿手改；重跑生成器覆盖本段）\n'
END = '    // <<< GENERATED\n'
block = BEGIN + text + END
path = ROOT / 'engine' / 'rust' / 'src' / 'drill_fidelity.rs'
t = path.read_text(encoding='utf-8')
if BEGIN in t:
    a = t.index(BEGIN)
    b = t.index(END, a) + len(END)
    path.write_text(t[:a] + block + t[b:], encoding='utf-8', newline='')
    print('# 已刷新标记区间')
else:
    path.write_text(t.rstrip() + '\n\n#[cfg(test)]\nmod tests {\n    use super::*;\n'
                    + block + '}\n', encoding='utf-8', newline='')
    print('# 已追加标记区间')
