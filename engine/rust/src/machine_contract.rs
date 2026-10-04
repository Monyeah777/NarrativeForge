//! 机读契约面（`machine_contract`）—— 与真源 `desktop/src/core/machine_contract.py` 的 `scan` 对账。
//!
//! 判据：官方核心（`04_模块库/`）每件的**机读块 `id` 必须与标题/文件名同号**；无机读块 = L0（WARN 挂账）。
//!
//! **可证范围刻意限定在官方核心**（真源 docstring 里的实测理由）：本判据假设「`mc.id` 与文件名/标题
//! token 同命名空间」——这**只对官方核心成立**；社区与域包工厂走两条编号通道：
//! 文件名留在包内代码位（如 `D14a`），运行时 id 是 `<独占类别>:Mxx`（如 `AI人力资源与招聘:M01`），
//! 两者本就不同。对全仓调用会对真仓报 200 条误报。
//!
//! **移植范围（最小化）**：真源的 `parse_header` 还返回 类别 / 层位 / 依赖 / 发布 / 订阅，
//! 但 `scan` **只用到 `id`**——其余字段只喂给 `apply` / `apply_outputs` / `derive_outputs`
//! 三个**写面**（本线不碰）。故本线只移植 id 推导这一条路径：既够用，又把未受判据覆盖的
//! 代码面压到零（写了也没人能核）。
//!
//! 本模块是 `nf verify-report` 的 `contract` 判据，**不单独开 CLI 面**。

use crate::pyjson::Json;
use crate::pyval::{get, py_str};
use std::path::Path;

fn title_re() -> &'static regex::Regex {
    static RE: std::sync::OnceLock<regex::Regex> = std::sync::OnceLock::new();
    RE.get_or_init(|| {
        regex::Regex::new(r"#\s*模块\s*(M\d{2})\s*[·:：]?\s*(.*)$")
            .expect("模块标题正则固定合法")
    })
}

/// 真源 `parse_header` 里**参与 `scan` 的那部分**：`id`。
///
/// 有 `# 模块 Mxx …` 标题 → 用标题里的号；否则退回文件名的第一段。
pub fn header_id(text: &str, rel: &str) -> String {
    let title = text
        .lines()
        .find(|ln| ln.starts_with("# 模块"))
        .unwrap_or("")
        .trim();
    if let Some(c) = title_re().captures(title) {
        return c[1].to_string();
    }
    let base = rel.rsplit('/').next().unwrap_or(rel);
    base.split('_').next().unwrap_or("").to_string()
}

pub struct McScan {
    pub issues: Vec<String>,
    pub warns: Vec<String>,
    pub stats: Json,
}

/// 真源 `scan` → `(issues, warns, stats)`。
pub fn scan(root: &Path) -> McScan {
    let mut issues: Vec<String> = Vec::new();
    let mut warns: Vec<String> = Vec::new();
    let mut l0: Vec<String> = Vec::new();
    let mut checked = 0usize;

    for rel in crate::module_signature::module_docs(root) {
        if !rel.starts_with("04_模块库/") {
            continue;
        }
        checked += 1;
        let Ok(text) = std::fs::read_to_string(root.join(&rel)) else { continue };
        let parsed = crate::miniyaml::fence_yaml(&text, "machine_contract");
        let mc = parsed
            .as_ref()
            .and_then(|p| get(p, "machine_contract"))
            .filter(|m| matches!(m, Json::Object(_)))
            .cloned();
        let Some(mc) = mc else {
            l0.push(rel);
            continue;
        };
        if !crate::pyval::py_truthy(get(&mc, "id").unwrap_or(&Json::Null)) {
            l0.push(rel);
            continue;
        }
        let spec_id = header_id(&text, &rel);
        // 官方限定写法（事件:M22 / 通用:M10）与裸号同义——按裸号比对，避免误报
        let a = py_str(get(&mc, "id")).rsplit(':').next().unwrap_or("").to_string();
        let b = spec_id.rsplit(':').next().unwrap_or("").to_string();
        if a != b {
            issues.push(format!(
                "机读块 id 与标题/文件名不符：{}（{} vs {}）",
                rel,
                py_str(get(&mc, "id")),
                spec_id
            ));
        }
    }
    if !l0.is_empty() {
        warns.push(format!(
            "仍为 L0（无机读块）：{} 件（修复指引：nf module contract --write）",
            l0.len()
        ));
    }
    let stats = Json::Object(vec![
        ("l0".to_string(), Json::Int(l0.len() as i64)),
        ("checked".to_string(), Json::Int(checked as i64)),
        (
            "l0_list".to_string(),
            Json::Array(l0.into_iter().map(Json::Str).collect()),
        ),
    ]);
    McScan { issues, warns, stats }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn id_comes_from_the_title_when_present() {
        let text = "# 模块 M10 · 时间推进\n\n> 类别：通用类\n";
        assert_eq!(header_id(text, "04_模块库/通用类/M10_时间推进.md"), "M10");
    }

    #[test]
    fn id_falls_back_to_the_file_name_prefix() {
        let text = "# 别的标题\n";
        assert_eq!(header_id(text, "04_模块库/通用类/M10_时间推进.md"), "M10");
    }

    #[test]
    fn id_is_compared_on_the_bare_number_so_qualified_ids_do_not_misfire() {
        // 官方限定写法（事件:M22）与裸号同义
        let text = "# 模块 M22 · x\n";
        assert_eq!(header_id(text, "a/M22_x.md"), "M22");
        assert_eq!("事件:M22".rsplit(':').next().unwrap(), "M22");
    }
}
