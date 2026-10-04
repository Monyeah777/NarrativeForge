"""为 `conformance_decl.scan`（declaration 契约）生成分支级判据。

用法：python engine/rust/tools/gen_declaration_branches.py
"""
import json
from _rustlit import rs  # noqa: E402
import pathlib
import shutil
import sys

ROOT = pathlib.Path('.').resolve()
sys.path.insert(0, str(ROOT / 'desktop' / 'src'))
from core import conformance_decl as cd  # noqa: E402

FIX = ROOT / 'engine' / 'rust' / 'target' / 'test-fixtures' / 'declaration-branches'
if FIX.exists():
    shutil.rmtree(FIX)
for d in ('protocol/schema', 'community/p1', 'desktop/src/core', 'docs'):
    (FIX / d).mkdir(parents=True)

W = lambda rel, obj: (FIX / rel).write_text(  # noqa: E731
    obj if isinstance(obj, str) else json.dumps(obj, ensure_ascii=False),
    encoding='utf-8', newline='')

# ---- 五路版本真源 ---------------------------------------------------------------
W('desktop/src/core/registry.json', {"registry_schema_version": 2})
W('protocol/schema/contract.schema.json', {"properties": {"schema": {"enum": ["1"]}}})
W('protocol/schema/other.schema.json', {"$id": "other"})
W('community/p1/protocol.yaml', 'protocol:\n  schema_version: "2"\n')
W('verify.sh', "#!/bin/bash\n# 版本 : (v9.9)\ncheck1(){\n  true\n}\ncheck2(){\n  true\n}\n")
# ⚠️ **这一路必须用真仓库的值**：真源是 `from core import quality_baseline as qb`——
# 它读的是**安装态的模块**，与 `root` 无关（实测：夹具根写 2/3，真源仍报 40/70）。
# 本线是从 `root` 读的（更纯：`scan(root)` 只依赖 root），故这是一处**有意保留的语义分歧**，
# 已在 README「已知偏差」单列。夹具这里对齐真仓库的值，让该支两侧可比。
# 夹具里这份只是占位：Rust 判据会在**测试时**从真仓库拷一份覆盖它。
# 若把真源当时的常量嵌进来，真源一改这两个数、判据就假红（并发会话正在改它，实测踩到）。
W('desktop/src/core/quality_baseline.py', "# 由判据在测试时以真仓库那份覆盖\n")

# ---- 声明件：逐分支踩 -----------------------------------------------------------
DECL = """# 一致性声明

## 声明

| 规范 | 版本 | 真源 |
|---|---|---|
| `registry schema` | `2` | `registry.json` |
| `machine_contract schema` | `9` | `contract.schema.json` |
| `无法核验的规范` | `1` | `x` |

## 范围

- `docs/`
- `no/such/dir/`

## 排除

| 路径 | 理由 |
|---|---|
| `docs/a.md` | 存量 |
| `docs/b.md` | 允许不存在 |
| `zzz/**` | 存量 |
"""
W('protocol/CONFORMANCE.md', DECL)
W('docs/a.md', "# a\n")

issues, stats = cd.scan(str(FIX))
live = cd.live_versions(str(FIX))

print('# live = %s' % json.dumps(live, ensure_ascii=False, sort_keys=True))
print('# 真源：issues=%d' % len(issues))
for x in issues:
    print('#   ! %s' % x)
print('# stats = %s' % json.dumps(stats, ensure_ascii=False, sort_keys=True))


def rj(s):
    assert '"#' not in s
    return 'r#"%s"#' % s


TEMPLATE = r'''
    /// ===== 分支级差分判据（期望值由 `tools/gen_declaration_branches.py` 从真源生成）=====
    ///
    /// 本夹具同时踩：五路版本真源**全部在场**（registry / contract.schema / protocol.yaml /
    /// schema 计数 / 基线常量）、声明与真源不一致、声明了无法核验的规范项、范围里路径不存在、
    /// 排除项 glob 无匹配、排除项「允许不存在」豁免、scope ∩ 排除重叠。
    const WANT_DECL_ISSUES: [&str; @@NI@@] = [
@@ISSUES@@
    ];

    /// 真仓库那份 `quality_baseline.py`（真源 `from core import quality_baseline` 读的就是它）。
    fn real_baseline_source() -> String {
        std::fs::read_to_string(concat!(
            env!("CARGO_MANIFEST_DIR"),
            "/../../desktop/src/core/quality_baseline.py"
        ))
        .expect("真仓库的 quality_baseline.py 须在场")
    }

    /// 从真仓库源码里取一个 `NAME = <整数>` 常量。
    fn baseline_const(name: &str) -> i64 {
        let src = real_baseline_source();
        for line in src.lines() {
            let line = line.trim();
            if let Some(rest) = line.strip_prefix(name) {
                let rest = rest.trim_start();
                if let Some(rest) = rest.strip_prefix('=') {
                    let digits: String =
                        rest.trim().chars().take_while(|c| c.is_ascii_digit()).collect();
                    if let Ok(n) = digits.parse() {
                        return n;
                    }
                }
            }
        }
        panic!("真仓库源码里找不到常量 {}", name);
    }

    /// 「基线」那一条把真源当时的两个常量拼进消息——期望串也得按**同一份**常量构造，
    /// 否则真源一改就假红（并发会话正在改它）。
    fn want_for(s: &str) -> String {
        if s.starts_with("声明与真源不一致：基线 ") {
            return format!(
                "声明与真源不一致：基线 声明=(缺) 真源=? · check1-{} · PASS={}（修复指引：改声明对齐真源）",
                baseline_const("EXPECTED_CHECKS"),
                baseline_const("EXPECTED_PASS")
            );
        }
        s.to_string()
    }

    fn build_declaration_fixture() -> std::path::PathBuf {
        let root = crate::testutil::fixture("declaration-branches");
        for rel in ["protocol/schema", "community/p1", "desktop/src/core", "docs"] {
            std::fs::create_dir_all(root.join(rel)).unwrap();
        }
        for (rel, body) in @@FILES@@ {
            std::fs::write(root.join(rel), body).unwrap();
        }
        // ⚠️ `quality_baseline.py` 一路**必须用真仓库那份**：真源是
        // `from core import quality_baseline as qb`——读**安装态模块**、与 `root` 无关。
        // 本线是从 `root` 读的（更纯），故这里现拷一份，让两侧在该路上可比；
        // 期望串也按真仓库当时的常量构造（见 `want_for`），否则真源一改就假红。
        std::fs::write(
            root.join("desktop/src/core/quality_baseline.py"),
            real_baseline_source(),
        )
        .unwrap();
        root
    }

    #[test]
    fn scan_matches_truth_source_branch_by_branch() {
        let root = build_declaration_fixture();
        let got = scan(&root);
        let want: Vec<String> = WANT_DECL_ISSUES.iter().map(|s| want_for(s)).collect();
        assert_eq!(got.issues, want, "逐条消息与次序都须与真源一致");
        assert_eq!(got.versions, @@NV@@, "声明版本条数");
        assert_eq!(got.scope, @@NS@@, "scope 条数");
        assert_eq!(got.excluded, @@NE@@, "排除条数");
    }
'''

FILES = {}
for rel in ('desktop/src/core/registry.json', 'protocol/schema/contract.schema.json',
            'protocol/schema/other.schema.json', 'community/p1/protocol.yaml', 'verify.sh',
            'desktop/src/core/quality_baseline.py', 'protocol/CONFORMANCE.md', 'docs/a.md'):
    FILES[rel] = (FIX / rel).read_text(encoding='utf-8')

files_rust = "[\n" + "\n".join(
    '            (%s, %s),' % (rs(k), rj(v)) for k, v in sorted(FILES.items())
) + "\n        ]"

text = (TEMPLATE
        .replace('@@NI@@', str(len(issues)))
        .replace('@@ISSUES@@', "\n".join('        %s,' % json.dumps(x, ensure_ascii=False) for x in issues))
        .replace('@@FILES@@', files_rust)
        .replace('@@NV@@', str(stats.get('versions', 0)))
        .replace('@@NS@@', str(stats.get('scope', 0)))
        .replace('@@NE@@', str(stats.get('excluded', 0))))

# ---- 标记区间替换：生成器可**反复重跑**（只跳过首版，改一次就得能刷新一次）
BEGIN = '    // >>> GENERATED by tools/gen_declaration_branches.py（勿手改；重跑生成器覆盖本段）\n'
END = '    // <<< GENERATED\n'
path = ROOT / 'engine' / 'rust' / 'src' / 'declaration.rs'
t = path.read_text(encoding='utf-8')
block = BEGIN + text + END
if BEGIN in t:
    a = t.index(BEGIN)
    b = t.index(END, a) + len(END)
    path.write_text(t[:a] + block + t[b:], encoding='utf-8', newline='')
    print('# 已刷新标记区间')
elif '#[cfg(test)]' in t:
    idx = t.rstrip().rfind('\n}')
    path.write_text(t[:idx] + block + t[idx:], encoding='utf-8', newline='')
    print('# 已插入标记区间（原有 tests 模块）')
else:
    path.write_text(t.rstrip() + '\n\n#[cfg(test)]\nmod tests {\n    use super::*;\n'
                    + block + '}\n', encoding='utf-8', newline='')
    print('# 已追加标记区间')
