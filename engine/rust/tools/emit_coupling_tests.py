import json, pathlib
from _rustlit import rs  # noqa: E402

SRC = {
    '__init__': "from core.aa import x\n",
    'aa': "import core.bb\nfrom core import cc, dd\n",
    'bb': "from core.aa import x\n",
    'cc': "from . import ee\n",
    'dd': "from .core import ff\n",
    'ee': "from ..pkg.sub import gg\n",
    'ff': "from core import (hh,\n    ii)\n",
    'gg': "import core.hh as hh\n",
    'hh': 'S = "from core import zzz"\n# import core.yyy\n',
    'ii': "import os\nimport json\n",
}
WANT_DEPS = [
    ("aa", ["bb", "cc", "dd"]), ("bb", ["aa"]), ("cc", ["ee"]), ("dd", ["ff"]),
    ("ee", []), ("ff", ["hh", "ii"]), ("gg", ["hh"]), ("hh", []), ("ii", []),
]
WANT_METRICS = [
    ("aa", 1, 3, 0.75), ("bb", 1, 1, 0.5), ("cc", 1, 1, 0.5), ("dd", 1, 1, 0.5),
    ("ee", 1, 0, 0.0), ("ff", 1, 2, 0.6667), ("gg", 0, 1, 1.0), ("hh", 2, 0, 0.0),
    ("ii", 1, 0, 0.0),
]
WANT_CYCLES = [["aa", "bb"]]
WANT_SDP = [("bb", "aa"), ("dd", "ff")]


def rj(s):
    assert '"#' not in s
    return 'r#"%s"#' % s


TEMPLATE = r'''
    /// ===== 分支级差分判据（期望值由 `target/parity/gen_coupling_expected.py` 从真源生成）=====
    ///
    /// 真语料上 `coupling` 只有固定的那几组环/SDP，**import 抽取的各种写法一条也没被单独核过**；
    /// 而本线的抽取是**词法近似**（真源用 `ast`）——正是最该被直接核的地方。
    /// 本夹具逐形态踩：普通 / 多别名 / 点号模块 / 相对无模块 / 相对 core / 相对带模块 /
    /// 括号多行 / 别名 / 字符串与注释里的假 import / `__init__` 忽略。
    const SRC: [(&str, &str); @@NSRC@@] = [
@@SRC@@
    ];

    fn build_fixture() -> std::path::PathBuf {
        let root = crate::testutil::fixture("coupling-branches");
        let core = root.join("desktop/src/core");
        std::fs::create_dir_all(&core).unwrap();
        for (name, body) in SRC {
            std::fs::write(core.join(format!("{}.py", name)), body).unwrap();
        }
        root
    }

    #[test]
    fn import_extraction_matches_ast_on_every_form() {
        let root = build_fixture();
        let g = graph(&root);
        let want: Vec<(String, Vec<String>)> = vec![
@@DEPS@@
        ];
        let got: Vec<(String, Vec<String>)> = g
            .deps
            .iter()
            .map(|(k, v)| (k.clone(), v.iter().cloned().collect()))
            .collect();
        assert_eq!(got, want, "同包依赖集合须与真源 AST 版逐条一致");
    }

    #[test]
    fn ca_ce_i_match_the_truth_source() {
        let root = build_fixture();
        let g = graph(&root);
        let want: Vec<(&str, i64, i64, f64)> = vec![
@@METRICS@@
        ];
        for (m, ca, ce, i) in want {
            assert_eq!(g.ca.get(m).copied().unwrap_or(-1), ca, "Ca 不符：{}", m);
            assert_eq!(g.ce.get(m).copied().unwrap_or(-1), ce, "Ce 不符：{}", m);
            assert_eq!(g.i_of.get(m).copied().unwrap_or(-1.0), i, "I 不符：{}", m);
        }
    }

    #[test]
    fn cycles_and_sdp_match_the_truth_source() {
        let root = build_fixture();
        let g = graph(&root);
        let cyc = cycles(&g.deps);
        let want: Vec<Vec<String>> = vec![
@@CYCLES@@
        ];
        assert_eq!(cyc, want, "环集合");
        let sdp = sdp_violations(&g);
        let want_sdp: Vec<(String, String)> = vec![
@@SDP@@
        ];
        assert_eq!(sdp, want_sdp, "SDP 违例（有方向，不排序）");
    }

    #[test]
    fn scan_reports_both_cycle_and_sdp_with_exact_wording() {
        let root = build_fixture();
        let got = scan(&root);
        assert_eq!(got.issues.len(), 3, "1 个环 + 2 处 SDP：{:?}", got.issues);
        assert!(got.issues[0].starts_with("新增模块级环：aa → bb → aa（"), "{:?}", got.issues[0]);
        assert!(got.issues[1].starts_with("新增 SDP 违例：bb(I=0.50) 依赖了更不稳的 aa(I=0.75)（"), "{:?}", got.issues[1]);
        assert!(got.issues[2].starts_with("新增 SDP 违例：dd(I=0.50) 依赖了更不稳的 ff(I=0.67)（"), "{:?}", got.issues[2]);
        assert_eq!(got.warns.len(), 1);
        assert!(got.warns[0].starts_with("无耦合基线 protocol/coupling_baseline.json"), "{:?}", got.warns[0]);
        assert!(crate::jsonread::json_eq(
            &got.stats,
            &crate::jsonread::convert(&serde_json::json!({
                "cycles": 1, "modules": 9, "registered_cycles": 0,
                "registered_sdp": 0, "sdp": 2
            }))
            .unwrap()
        ));
    }
'''

text = (TEMPLATE
        .replace('@@NSRC@@', str(len(SRC)))
        .replace('@@SRC@@', "\n".join('        (%s, %s),' % (rs(k), rj(v))
                                      for k, v in sorted(SRC.items())))
        .replace('@@DEPS@@', "\n".join('            (%s.to_string(), vec![%s]),'
                                       % (rs(k), ", ".join('%s.to_string()' % rs(x) for x in v))
                                       for k, v in WANT_DEPS))
        .replace('@@METRICS@@', "\n".join('            (%s, %d, %d, %s),' % (rs(m), ca, ce, repr(i))
                                          for m, ca, ce, i in WANT_METRICS))
        .replace('@@CYCLES@@', "\n".join('            vec![%s],' % ", ".join('%s.to_string()' % rs(x) for x in c)
                                         for c in WANT_CYCLES))
        .replace('@@SDP@@', "\n".join('            (%s.to_string(), %s.to_string()),' % (rs(a), rs(b))
                                      for a, b in WANT_SDP)))

path = pathlib.Path('engine/rust/src/coupling_metrics.rs')
t = path.read_text(encoding='utf-8')
if 'coupling-branches' in t:
    print('已存在分支级判据，未追加')
else:
    idx = t.rstrip().rfind('\n}')
    t = t[:idx] + text + t[idx:]
    path.write_text(t, encoding='utf-8', newline='')
    print('已追加分支级判据；SRC=%d, DEPS=%d, METRICS=%d, CYCLES=%d, SDP=%d'
          % (len(SRC), len(WANT_DEPS), len(WANT_METRICS), len(WANT_CYCLES), len(WANT_SDP)))
