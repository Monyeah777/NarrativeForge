"""为 `world_model.scan` 生成差分判据：真语料 + 合成分支夹具。

真语料上只有 **1 个模块**（M50）声明 world_model 且全绿 ⇒ `validate_contract` 的 30 多个
错误分支一个都踩不到。故除了真语料差分，另造一批合成模块文档逐支踩。

用法：python engine/rust/tools/gen_world_model_cases.py
"""
import json
import pathlib
import shutil
import sys

ROOT = pathlib.Path('.').resolve()
sys.path.insert(0, str(ROOT / 'desktop' / 'src'))
sys.path.insert(0, str(ROOT / 'engine' / 'rust' / 'tools'))
from _rustlit import raw as rr  # noqa: E402
from core import world_model as wm  # noqa: E402

real_issues, real_stats = wm.scan(str(ROOT))
print('# 真语料: issues=%d stats=%s' % (len(real_issues),
                                      json.dumps(real_stats, ensure_ascii=False, sort_keys=True)[:150]))

FIX = ROOT / 'engine' / 'rust' / 'target' / 'test-fixtures' / 'world-model-cases'
if FIX.exists():
    shutil.rmtree(FIX)

SLOTS = {
    "schema_version": "1",
    "slots": {
        "s.ok": {"kind": "integer", "owner": "M99"},
        "s.driftkind": {"kind": "string", "owner": "M99"},
        "s.driftitem": {"kind": "array", "item_kind": "integer", "owner": "M99"},
        "s.drifdowner": {"kind": "integer", "owner": "M98"},
    },
}


def doc(module_id, body_lines):
    return (
        "---\nmodule: %s\n---\n\n# 测试模块\n\n```yaml\nmachine_contract:\n  id: \"%s\"\n%s\n```\n"
        % (module_id, module_id, body_lines)
    )


def wm_block(lines, indent="      "):
    out = ["  world_model:"] if False else []
    return "\n".join(indent + l if l else "" for l in lines)


# ① 契约骨架全缺
D1 = doc("M90", '''  world_model:
    abstract_state: "not-an-object"
    transition: "not-an-object"
''')

# ② 变量面各种违规
D2 = doc("M91", '''  world_model:
    abstract_state:
      variables:
        - name: ""
          kind: "widget"
          source: ""
        - name: "v1"
          kind: "string"
          source: "M91"
          item_kind: "string"
        - name: "v1"
          kind: "array"
          source: "M91"
          item_kind: "widget"
        - name: "v2"
          kind: "array"
          source: "M91"
          item_kind: "string"
          slot: "s.ok"
        - name: "v3"
          kind: "integer"
          source: "M91"
          slot: "s.ok"
        - name: "v4"
          kind: "integer"
          source: "M91"
          slot: "s.nope"
        - name: "v5"
          kind: "string"
          source: "M91"
          slot: "s.driftkind"
        - name: "v6"
          kind: "integer"
          source: "M91"
          slot: "s.drifdowner"
        - "not-an-object"
      initial:
        undeclared: 1
        v1: 5
        v2: ["a"]
        v3: "x"
    transition:
      initial_phase: ""
      phases: []
    invariants: []
''')

# ③ 相位面各种违规
D3 = doc("M92", '''  world_model:
    abstract_state:
      variables:
        - name: "p"
          kind: "string"
          source: "M92"
      initial:
        p: "begin"
    transition:
      initial_phase: "begin"
      phases:
        - phase: ""
          next: "b"
          guard: "g"
          writes: []
        - phase: "begin"
          next: "ghost"
          guard: ""
          writes: ["ok", 1]
        - phase: "begin"
          next: "begin"
          guard: "g"
          writes: []
        - phase: "b"
          next: "b"
          guard: "g"
          writes: []
        - phase: "c"
          next: "b"
          guard: "g"
          writes: []
        - "not-an-object"
    invariants: ["", "ok"]
''')

# ④ checks 面各种违规
D4 = doc("M93", '''  world_model:
    abstract_state:
      variables:
        - name: "n"
          kind: "string"
          source: "M93"
        - name: "arr"
          kind: "array"
          item_kind: "integer"
          source: "M93"
      initial:
        n: "begin"
        arr: [1]
    transition:
      initial_phase: "begin"
      phases:
        - phase: "begin"
          next: "begin"
          guard: "g"
          writes: []
    invariants: ["ok"]
    checks:
      - kind: "widget"
        field: "nope"
        values: []
      - kind: "finite_phase"
        field: "n"
        values: ["begin"]
      - kind: "monotonic"
        field: "n"
      - kind: "finite_sequence"
        field: "n"
        values: ["a"]
      - kind: "finite_sequence"
        field: "arr"
        values: ["a"]
      - "not-an-object"
''')

FILES = {
    '04_模块库/通用类/M90_测试.md': D1,
    '04_模块库/通用类/M91_测试.md': D2,
    '04_模块库/通用类/M92_测试.md': D3,
    '04_模块库/通用类/M93_测试.md': D4,
    'protocol/world_slots.json': json.dumps(SLOTS, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
}
for rel, body in FILES.items():
    fp = FIX / rel
    fp.parent.mkdir(parents=True, exist_ok=True)
    fp.write_text(body, encoding='utf-8', newline='')

syn_issues, syn_stats = wm.scan(str(FIX))
print('# 合成: issues=%d stats=%s' % (len(syn_issues),
                                   json.dumps(syn_stats, ensure_ascii=False, sort_keys=True)[:150]))
for x in syn_issues[:8]:
    print('#   ! %s' % x[:118])


def arr(v):
    return "&[%s]" % ", ".join(rr(x) for x in v)


TEMPLATE = r'''
    // >>> GENERATED by tools/gen_world_model_cases.py（勿手改；重跑生成器覆盖本段）
    /// ===== 真语料差分 =====
    #[test]
    fn world_model_matches_truth_source_on_real_corpus() {
        let root = crate::testutil::repo_root();
        let (issues, stats) = scan(&root);
        assert_eq!(issues, @@REALI@@ as &[&str], "真语料 issues 须逐字且同序");
        let want: Json = crate::jsonread::convert(
            &serde_json::from_str::<serde_json::Value>(@@REALS@@).unwrap(),
        )
        .unwrap();
        assert!(crate::jsonread::json_eq(&stats, &want),
                "真语料 stats 不一致\n  实得 {}\n  期望 {}", stats.dumps(), want.dumps());
    }

    /// ===== 合成分支夹具（逐支踩 `validate_contract`）=====
    ///
    /// 真语料只有 1 个模块且全绿 ⇒ 30 多个错误分支一个都踩不到。本夹具用 4 份合成模块文档覆盖：
    /// 契约骨架缺失 / 变量面（空名·非法 kind·重名·item_kind 越界·source 空·槽位重复·未注册·
    /// 类型漂移·元素类型漂移·owner 漂移·非对象）/ initial 面（未声明变量·类型不符）/
    /// 相位面（空 initial_phase·空 phases·空 phase 名·next 悬空·guard 空·writes 非字符串数组·
    /// 相位重名·ghost next·不可达相位）/ invariants 面 / checks 面（非法 kind·未声明 field·
    /// values 非法·monotonic 用错类型·finite_sequence 用错类型与元素类型）。
    const WM_FILES: [(&str, &str); @@NF@@] = [
@@FILES@@
    ];

    fn build_wm_fixture() -> std::path::PathBuf {
        let root = crate::testutil::fixture("world-model-cases");
        for (rel, body) in WM_FILES {
            let p = root.join(rel);
            std::fs::create_dir_all(p.parent().unwrap()).unwrap();
            std::fs::write(p, body).unwrap();
        }
        root
    }

    #[test]
    fn world_model_matches_truth_source_branch_by_branch() {
        let root = build_wm_fixture();
        let (issues, stats) = scan(&root);
        assert_eq!(issues, @@SYNI@@ as &[&str], "合成 issues 须逐字且同序");
        let want: Json = crate::jsonread::convert(
            &serde_json::from_str::<serde_json::Value>(@@SYNS@@).unwrap(),
        )
        .unwrap();
        assert!(crate::jsonread::json_eq(&stats, &want),
                "合成 stats 不一致\n  实得 {}\n  期望 {}", stats.dumps(), want.dumps());
    }
    // <<< GENERATED
'''
text = (TEMPLATE
        .replace('@@REALI@@', arr(real_issues))
        .replace('@@REALS@@', rr(json.dumps(real_stats, ensure_ascii=False, sort_keys=True)))
        .replace('@@NF@@', str(len(FILES)))
        .replace('@@FILES@@', "\n".join('        (%s, %s),' % (rr(k), rr(v))
                                       for k, v in sorted(FILES.items())))
        .replace('@@SYNI@@', arr(syn_issues))
        .replace('@@SYNS@@', rr(json.dumps(syn_stats, ensure_ascii=False, sort_keys=True))))
BEGIN = '    // >>> GENERATED by tools/gen_world_model_cases.py（勿手改；重跑生成器覆盖本段）\n'
END = '    // <<< GENERATED\n'
block = BEGIN + text.split(BEGIN, 1)[1]

path = ROOT / 'engine' / 'rust' / 'src' / 'world_model.rs'
t = path.read_text(encoding='utf-8')
if BEGIN in t:
    a = t.index(BEGIN)
    b = t.index(END, a) + len(END)
    t = t[:a] + block + t[b:]
else:
    t = t.rstrip() + '\n\n#[cfg(test)]\nmod tests {\n    use super::*;\n}\n'
    t = t.rstrip()[:-1].rstrip() + '\n' + block + '}\n'
path.write_text(t, encoding='utf-8', newline='')
print('# 已写入 world_model 判据（真语料 %d 条 / 合成 %d 条）' % (len(real_issues), len(syn_issues)))
