//! 仓库内路径**包含性判据**（`validate_path` 的唯一实现点）—— 与真源 `desktop/src/core/paths.py` 对账。
//!
//! 真源模块文档写明了它的作用边界（**仓库内组件之间**的包含性判据，不是进程级沙箱）；本线照搬
//! 这条边界，不夸大。
//!
//! **移植面**：`path_syntax_issue` / `contained` / `validate_path`（判据面）。
//! `guard_recursive_delete_target` **不移植**——它服务于**递归删除**这个不可逆动作，本线只读，
//! 没有任何已移植面会用到它（"不写没人核的代码"）。
//!
//! **一处实现差异（如实记）**：真源 `os.path.realpath` 默认 `strict=False`——**路径不存在也能归一**
//! （解析已有前缀 + 其余按词法）。Rust `std::fs::canonicalize` 要求路径存在 ⇒ 本线实现
//! 「能规范化就规范化，否则取**最长存在祖先**的规范化结果 + 其余分量词法归一」，
//! 与 Python 在**已有路径**上逐字等价，在**不存在路径**上给同一语义方向（都先归一 `..`）。
//! 另外 Windows 上 `canonicalize` 会给 `\\?\` 前缀：比较时两侧一致故无碍，**返回给调用方前剥掉**
//! （否则错误消息里会出现真源没有的前缀）。

use std::path::{Component, Path, PathBuf};

/// 真源 `PathEscapeError`。
#[derive(Debug)]
pub struct PathEscapeError(pub String);

fn control_re() -> &'static regex::Regex {
    static RE: std::sync::OnceLock<regex::Regex> = std::sync::OnceLock::new();
    RE.get_or_init(|| {
        regex::Regex::new("[\u{0}-\u{8}\u{b}\u{c}\u{e}-\u{1f}\u{7f}]").expect("固定合法")
    })
}

fn traversal_re() -> &'static regex::Regex {
    static RE: std::sync::OnceLock<regex::Regex> = std::sync::OnceLock::new();
    RE.get_or_init(|| regex::Regex::new(r"(^|[\\/])\.\.([\\/]|$)").expect("固定合法"))
}

fn drive_relative_re() -> &'static regex::Regex {
    static RE: std::sync::OnceLock<regex::Regex> = std::sync::OnceLock::new();
    // 真源是 `^[A-Za-z]:(?![\\/])`（负向前瞻）。⚠️ Rust `regex` crate **不支持环视** ⇒ 改等价写法：
    // 「盘符 + 冒号，后面**不是**斜杠（或已到结尾）」。匹配面逐字相同。
    RE.get_or_init(|| regex::Regex::new(r"^[A-Za-z]:([^\\/]|$)").expect("固定合法"))
}

fn ads_re() -> &'static regex::Regex {
    static RE: std::sync::OnceLock<regex::Regex> = std::sync::OnceLock::new();
    RE.get_or_init(|| regex::Regex::new(r"\.[A-Za-z0-9]{1,8}:[^\\/\s]").expect("固定合法"))
}

fn reserved_device_re() -> &'static regex::Regex {
    static RE: std::sync::OnceLock<regex::Regex> = std::sync::OnceLock::new();
    RE.get_or_init(|| {
        regex::Regex::new(r"(?i)(^|[\\/])(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(\.[^\\/]*)?($|[\\/])")
            .expect("固定合法")
    })
}

/// 真源 `path_syntax_issue`：根内相对标识符的**词法判据**（单一出处）。
pub fn path_syntax_issue(text: &str) -> String {
    if control_re().is_match(text) {
        return "含控制字符".to_string();
    }
    if traversal_re().is_match(text) || drive_relative_re().is_match(text) {
        return "含越界路径写法（../ 段 / 绝对路径 / 盘符写法如 C:foo）".to_string();
    }
    if ads_re().is_match(text) {
        return "含备用数据流写法（`文件:流` 形态）".to_string();
    }
    if reserved_device_re().is_match(text) {
        return "含 Windows 保留设备名写法（CON/NUL/COM1 等指向设备而非文件）".to_string();
    }
    String::new()
}

/// Python `os.path.isabs` 在 Windows 上的口径：`C:\x` / `\x` / `/x` 都是绝对。
fn is_abs(text: &str) -> bool {
    let b: Vec<char> = text.chars().collect();
    if b.len() >= 3 && b[0].is_ascii_alphabetic() && b[1] == ':' && (b[2] == '\\' || b[2] == '/') {
        return true;
    }
    matches!(b.first(), Some('\\') | Some('/'))
}

/// 词法归一（不碰文件系统）：消去 `.` / `..`。
fn lex_normalize(p: &Path) -> PathBuf {
    let mut out: Vec<Component> = Vec::new();
    for c in p.components() {
        match c {
            Component::CurDir => {}
            Component::ParentDir => {
                if matches!(out.last(), Some(Component::Normal(_))) {
                    out.pop();
                } else {
                    out.push(c);
                }
            }
            other => out.push(other),
        }
    }
    let mut b = PathBuf::new();
    for c in out {
        b.push(c.as_os_str());
    }
    b
}

/// 真源 `os.path.realpath` 的对应物（**不要求路径存在**）。
pub fn realpath(p: &Path) -> PathBuf {
    if let Ok(c) = std::fs::canonicalize(p) {
        return strip_unc(&c);
    }
    // 取**最长存在祖先**的规范化结果 + 余下分量按词法归一
    let mut anc = p.to_path_buf();
    let mut tail: Vec<std::ffi::OsString> = Vec::new();
    loop {
        match std::fs::canonicalize(&anc) {
            Ok(c) => {
                let mut base = strip_unc(&c);
                for t in tail.iter().rev() {
                    base.push(t);
                }
                return lex_normalize(&base);
            }
            Err(_) => {
                let Some(name) = anc.file_name().map(|s| s.to_os_string()) else {
                    return lex_normalize(p);
                };
                tail.push(name);
                if !anc.pop() {
                    return lex_normalize(p);
                }
            }
        }
    }
}

/// 去掉 Windows `canonicalize` 给的 `\\?\` 前缀（真源路径里没有它）。
fn strip_unc(p: &Path) -> PathBuf {
    let s = p.to_string_lossy().to_string();
    if let Some(rest) = s.strip_prefix(r"\\?\") {
        return PathBuf::from(rest);
    }
    PathBuf::from(s)
}

/// 真源 `contained`。
pub fn contained(root: &Path, target: &Path) -> bool {
    let r = realpath(root);
    let t = if target.is_absolute() { target.to_path_buf() } else { r.join(target) };
    let t = realpath(&t);
    t == r || t.starts_with(format!("{}{}", r.display(), std::path::MAIN_SEPARATOR))
}

/// 真源 `validate_path(root, rel)` → 根内绝对路径；越界即 `Err`。
pub fn validate_path(root: &Path, rel: &str) -> Result<PathBuf, PathEscapeError> {
    let text = rel.to_string();
    if text.trim().is_empty() {
        return Err(PathEscapeError(
            "路径为空（修复指引：给出根内相对路径，如 assets/A1.md）".to_string(),
        ));
    }
    if is_abs(&text) {
        return Err(PathEscapeError(format!(
            "不接受绝对路径：{}（修复指引：改用根内相对路径）",
            text
        )));
    }
    let issue = path_syntax_issue(&text);
    if !issue.is_empty() {
        return Err(PathEscapeError(format!(
            "{}：{}（修复指引：改用根内相对路径——勿用 `..` 段 / 盘符写法如 C:foo / `文件:流` 备用数据流写法，并去掉不可见控制字符）",
            issue, text
        )));
    }
    let full = realpath(&realpath(root).join(&text));
    if !contained(root, &full) {
        return Err(PathEscapeError(format!(
            "路径逃逸根目录：{}（修复指引：目标须落在 {} 内）",
            text,
            root.display()
        )));
    }
    Ok(full)
}
