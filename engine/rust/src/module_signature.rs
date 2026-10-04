//! 模块**边界签名**（`module_signature`）—— 与真源 `desktop/src/core/module_signature.py` 对账。
//!
//! 判据：模块文档围栏块 `machine_contract` 的边界字段（`_BOUNDARY_KEYS`）改了就必须显式重签，
//! 否则 `protocol/module_signatures.json` 的摘要对不上 → **边界漂移 = FAIL**。
//!
//! **只读**：`write`（重签并落基线）不实现——真源仍在 Python 侧。
//! 依赖 [`crate::miniyaml`]（围栏 YAML 子集解析）。

use crate::miniyaml;
use crate::pyjson::Json;
use crate::pyval::{get, obj_is_empty, plain_str_opt, py_str};
use std::path::Path;

pub const BASELINE_REL: &str = "protocol/module_signatures.json";
/// 真源 `_BOUNDARY_KEYS` —— 摘要覆盖面的**单一真相源**（issue 文案也从它生成）。
const BOUNDARY_KEYS: [&str; 7] =
    ["inputs", "outputs", "events", "interfaces", "layer", "category", "io_types"];

/// 真源 `_module_docs`：`04_模块库/**/*.md` + `community/*/modules/*.md`，排序。
pub(crate) fn module_docs(root: &Path) -> Vec<String> {
    let mut out = crate::glob::expand(root, "04_模块库/**/*.md");
    out.extend(crate::glob::expand(root, "community/*/modules/*.md"));
    out.sort();
    out
}

/// 真源 `signatures(root)`：`id → (digest, path)`。
///
/// 真源用 dict 承载（**同 id 后者覆盖前者**）；此处同样覆盖，故顺序与真源一致地由排序决定。
pub fn signatures(root: &Path) -> Vec<(String, String, String)> {
    let mut out: Vec<(String, String, String)> = Vec::new();
    for rel in module_docs(root) {
        let Ok(text) = std::fs::read_to_string(root.join(&rel)) else {
            continue;
        };
        let Some(parsed) = miniyaml::fence_yaml(&text, "machine_contract") else {
            continue;
        };
        let Some(mc) = get(&parsed, "machine_contract") else {
            continue;
        };
        if !matches!(mc, Json::Object(_)) {
            continue;
        }
        let mid = py_str(get(mc, "id"));
        if mid.is_empty() {
            continue;
        }
        let boundary: Vec<(String, Json)> = BOUNDARY_KEYS
            .iter()
            .map(|k| ((*k).to_string(), get(mc, k).cloned().unwrap_or(Json::Null)))
            .collect();
        let blob = Json::Object(boundary).dumps_compact();
        let digest = crate::merkle::hex(&crate::merkle::sha256(blob.as_bytes()));
        match out.iter_mut().find(|(id, _, _)| *id == mid) {
            Some(slot) => {
                slot.1 = digest;
                slot.2 = rel;
            }
            None => out.push((mid, digest, rel)),
        }
    }
    out
}

/// 真源 `verify(root)[0]`：只取 issues（本契约只用它）。
pub fn verify_issues(root: &Path) -> Vec<String> {
    let missing = || {
        vec![format!(
            "缺模块边界基线 {}（修复指引：nf module signature --write）",
            BASELINE_REL
        )]
    };
    if !root.join(BASELINE_REL).is_file() {
        return missing();
    }
    let Some(base) = crate::jsonread::read_file(root, BASELINE_REL) else {
        // 真源此处会因 json 解析异常冒到契约的 except 分支；本线按"缺基线"报（措辞不承诺逐字节）
        return missing();
    };
    if obj_is_empty(&base) {
        return missing();
    }

    let base_mods = get(&base, "modules").cloned().unwrap_or(Json::Object(Vec::new()));
    let mut sigs = signatures(root);
    sigs.sort_by(|a, b| a.0.cmp(&b.0));

    let mut issues = Vec::new();
    for (mid, digest, _) in &sigs {
        match get(&base_mods, mid) {
            None => {} // 真源此处进 warns（本契约不看 warns）
            Some(rec) => {
                if plain_str_opt(get(rec, "digest")) != *digest {
                    issues.push(format!(
                        "边界漂移：{}（签名覆盖面：{}）（修复指引：评审后 nf module signature --write 重新冻结）",
                        mid,
                        BOUNDARY_KEYS.join("/")
                    ));
                }
            }
        }
    }
    issues
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn missing_baseline_reports_with_fix_hint() {
        let tmp = crate::testutil::fixture("ms-missing");
        let issues = verify_issues(&tmp);
        assert_eq!(issues.len(), 1);
        assert!(issues[0].contains("缺模块边界基线"));
        let _ = std::fs::remove_dir_all(&tmp);
    }

    #[test]
    fn digest_covers_only_boundary_keys() {
        let tmp = crate::testutil::fixture("ms-boundary");
        std::fs::create_dir_all(tmp.join("04_模块库/通用类")).unwrap();
        let mk = |name: &str, inputs: &str| {
            format!(
                "```yaml\nmachine_contract:\n  id: M99\n  layer: P10\n  inputs: {}\n  name: {}\n```\n",
                inputs, name
            )
        };
        let path = tmp.join("04_模块库/通用类/M99_x.md");
        std::fs::write(&path, mk("甲", "[a]")).unwrap();
        let a = signatures(&tmp);
        // 非边界字段（name）变化不得改摘要
        std::fs::write(&path, mk("乙乙乙", "[a]")).unwrap();
        let b = signatures(&tmp);
        assert_eq!(a.len(), 1);
        assert_eq!(a[0].1, b[0].1, "非边界字段不得进摘要");
        // 边界字段变化必须改摘要
        std::fs::write(&path, mk("甲", "[b]")).unwrap();
        let c = signatures(&tmp);
        assert_ne!(a[0].1, c[0].1, "边界字段变更必须改变摘要");
        let _ = std::fs::remove_dir_all(&tmp);
    }
}
