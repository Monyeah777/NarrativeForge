//! 真源 **Python 模块级常量**的转录登记册（勿手改数值；出处见每条注释）。
//!
//! **为什么需要它**：真源的 `modeling._probe` 支持 `python_attr` 探针——用
//! `importlib.import_module` 取某个 Python 模块的常量来与登记册逐项比对
//! （如「词表 `doc-kinds` 必须与 `core.doc_hygiene.KINDS` 一致」）。本线没有 Python 运行时，
//! 故把这些常量**转录**过来，并**未登记即 fail-closed**（报"真源取不到"，不冒充一致）。
//!
//! 这与「解析 Python 源码」不是一回事：转录的是真源**对外声明的常量**，
//! 且每一条都能在原模块里一眼核对。真源改了这些常量而本册未同步 → 对账会红。

/// `(模块名, 属性名, 值)`
pub type ConstEntry = (&'static str, &'static str, &'static [&'static str]);

pub const ENTRIES: &[ConstEntry] = &[
    // desktop/src/core/doc_hygiene.py :: KINDS（文档四型）
    (
        "core.doc_hygiene",
        "KINDS",
        &["tutorial", "how-to", "reference", "explanation"],
    ),
    // desktop/src/core/assertions.py :: KINDS（断言 kind 封闭集，dict 键序即此序）
    (
        "core.assertions",
        "KINDS",
        &["regex_absent", "regex_present", "count_at_least", "json_value"],
    ),
    // desktop/src/core/rfc.py :: CATEGORIES
    (
        "core.rfc",
        "CATEGORIES",
        &["Standards Track", "Informational", "Experimental", "Process"],
    ),
    // desktop/src/core/patterns.py :: STATUSES
    ("core.patterns", "STATUSES", &["active", "deprecated"]),
];

/// 取真源常量；未登记 → `None`（调用方按"真源取不到"报，**不伪造一致**）。
pub fn lookup(module: &str, attr: &str) -> Option<&'static [&'static str]> {
    ENTRIES
        .iter()
        .find(|(m, a, _)| *m == module && *a == attr)
        .map(|(_, _, v)| *v)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn lookup_matches_the_probes_declared_in_vocabularies() {
        // 与 protocol/vocabularies.json 的 python_attr 探针逐条对应
        assert!(lookup("core.doc_hygiene", "KINDS").is_some());
        assert!(lookup("core.assertions", "KINDS").is_some());
        assert!(lookup("core.rfc", "CATEGORIES").is_some());
        assert!(lookup("core.patterns", "STATUSES").is_some());
    }

    #[test]
    fn unknown_constant_is_explicitly_absent() {
        assert!(lookup("core.nope", "KINDS").is_none());
    }
}
