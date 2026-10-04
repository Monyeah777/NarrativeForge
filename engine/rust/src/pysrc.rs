//! Python 源码的**词法级**事实提取 —— 只做真源 L6 用到的那一件事：
//! 判断 `desktop/src/core/*.py` 里有没有真的 `import nf` / `from scripts …`。
//!
//! **为什么不能裸行扫描**（实测 2026-10-03）：真源 L6 先用文本预筛
//! `\b(?:import|from)\s+(?:nf|scripts)\b`，命中后才走 `ast.parse` + `ast.walk`。
//! 当前语料里该预筛**命中 2 件**（`layer_model.py` / `terminal.py`），而命中的内容是
//! **文档字符串里的散文提及**（"core 不许出现 import nf / from scripts"）——
//! 裸行扫描会把散文当 import，凭空造出 L6 假红。故必须先按 Python 词法剥掉注释与字符串。
//!
//! **已知近似（不宣称等价于 `ast`）**：
//! - 不做完整解析：剥注释/字符串后按语句行取 import；
//! - 多行 import（`from x import (\n a,\n b)`）按首行取模块名——与 AST 的 `lineno` 同；
//! - 嵌套 import（函数内）按行首缩进同样能取到；但 `ast.walk` 是**广度优先**，
//!   本实现按**源码顺序**——同深度语句下两者一致，跨深度时可能不同序；
//! - f-string 内嵌引号等极端写法按普通字符串处理。

/// 引擎阶不得反向 import 的入口面模块名（与真源 `ENTRY_MODULE_NAMES` 同）。
pub const ENTRY_MODULES: [&str; 2] = ["nf", "scripts"];

fn entry_re() -> &'static regex::Regex {
    static RE: std::sync::OnceLock<regex::Regex> = std::sync::OnceLock::new();
    // 真源 `_ENTRY_IMPORT_RE`
    RE.get_or_init(|| {
        regex::Regex::new(r"\b(?:import|from)\s+(?:nf|scripts)\b").expect("预筛正则固定合法")
    })
}

/// 剥掉 Python 的注释与字符串字面量（**保留换行**，故行号不变）。
///
/// 字符串前缀（`r`/`b`/`u`/`f` 及其组合）会影响反斜杠转义语义，故需识别 raw 前缀。
pub fn strip_comments_and_strings(src: &str) -> String {
    let chars: Vec<char> = src.chars().collect();
    let n = chars.len();
    let mut out = String::with_capacity(src.len());
    let mut i = 0usize;
    // (引号字符, 是否三引号, 是否 raw)
    let mut state: Option<(char, bool, bool)> = None;

    while i < n {
        let c = chars[i];
        match state {
            Some((q, triple, raw)) => {
                if !raw && c == '\\' {
                    out.push(' ');
                    if i + 1 < n {
                        out.push(if chars[i + 1] == '\n' { '\n' } else { ' ' });
                    }
                    i += 2;
                    continue;
                }
                if triple && c == q && i + 2 < n && chars[i + 1] == q && chars[i + 2] == q {
                    out.push_str("   ");
                    i += 3;
                    state = None;
                    continue;
                }
                if !triple && c == q {
                    out.push(' ');
                    i += 1;
                    state = None;
                    continue;
                }
                out.push(if c == '\n' { '\n' } else { ' ' });
                i += 1;
            }
            None => {
                if c == '#' {
                    while i < n && chars[i] != '\n' {
                        out.push(' ');
                        i += 1;
                    }
                    continue;
                }
                if c == '\'' || c == '"' {
                    let triple = i + 2 < n && chars[i + 1] == c && chars[i + 2] == c;
                    let raw = is_raw_prefix(&chars, i);
                    out.push_str(if triple { "   " } else { " " });
                    i += if triple { 3 } else { 1 };
                    state = Some((c, triple, raw));
                    continue;
                }
                out.push(c);
                i += 1;
            }
        }
    }
    out
}

/// 引号前是否是 raw 字符串前缀（`r"…"` / `rb"…"` / `fr"…"`）。
fn is_raw_prefix(chars: &[char], quote_at: usize) -> bool {
    let mut j = quote_at;
    let mut saw_raw = false;
    while j > 0 {
        match chars[j - 1] {
            'r' | 'R' => {
                saw_raw = true;
                j -= 1;
            }
            'b' | 'B' | 'u' | 'U' | 'f' | 'F' => j -= 1,
            _ => break,
        }
    }
    if !saw_raw {
        return false;
    }
    if j == 0 {
        return true;
    }
    // 前缀前面若是标识符字符，说明那个 r 是某个名字的尾字母，不是前缀
    let before = chars[j - 1];
    !(before.is_alphanumeric() || before == '_')
}

/// 真源 `_entry_imports` 的等价物：`(行号, 顶层模块名)`，只保留入口面模块。
pub fn entry_imports(src: &str) -> Vec<(usize, String)> {
    if !entry_re().is_match(src) {
        return Vec::new(); // 文本预筛：绝大多数件不含入口 import，连剥字符串都不必付
    }
    let stripped = strip_comments_and_strings(src);
    let mut out = Vec::new();
    for (idx, line) in stripped.lines().enumerate() {
        let t = line.trim_start();
        if let Some(rest) = t.strip_prefix("import ") {
            for alias in rest.split(',') {
                let name = alias.trim().split('.').next().unwrap_or("").trim();
                let name = name.split_whitespace().next().unwrap_or("");
                if ENTRY_MODULES.contains(&name) {
                    out.push((idx + 1, name.to_string()));
                }
            }
        } else if let Some(rest) = t.strip_prefix("from ") {
            let rest = rest.trim_start();
            let name = rest.split_whitespace().next().unwrap_or("");
            let name = name.split('.').next().unwrap_or("");
            if ENTRY_MODULES.contains(&name) {
                out.push((idx + 1, name.to_string()));
            }
        }
    }
    out
}
