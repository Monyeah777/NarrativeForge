//! glob 子集 —— 复刻真源所用的 `Path.glob` 形态。
//!
//! **范围纪律**：真源实际用到的只有两种形态（2026-10-03 全仓普查）：
//! `*`（不跨 `/`）与 `**`（跨目录）；另有直路径（无通配符）与 `?`。故本模块只保证这些：
//!
//! | 形态 | 语义 | 与 `Path.glob` |
//! |---|---|---|
//! | `*` | 段内任意字符（不跨 `/`） | 同 |
//! | `?` | 段内单字符 | 同 |
//! | `**` | 跨目录（可为零段） | 同（**仅作独立段时**；真源无「非独立段的 `**`」用例） |
//! | `[...]` | **不支持** → 由调用方回退或显式报错 | 不同 |
//!
//! `Path.glob` 的 `**` 必须是独立段才算递归；本模块沿用真源自己的快路径口径
//! （`layer_model._pattern_to_regex`：「`**` → `.*`，紧随的 `/` 一并吞掉」），
//! 因为那正是仓库内已验证过等价性的那份实现。
//!
//! 隐藏文件**照收**：`Path.glob` 不像 shell 那样跳过点开头项。

use std::path::Path;

/// 是否含通配符（与真源 `_is_glob` 同判据）。
pub fn has_wildcard(pattern: &str) -> bool {
    pattern.contains('*') || pattern.contains('?') || pattern.contains('[')
}

/// glob → 锚定正则（仓库相对 POSIX 路径上匹配）。
pub fn to_regex(pattern: &str) -> regex::Regex {
    let mut out = String::from("^");
    let chars: Vec<char> = pattern.chars().collect();
    let mut literal = String::new();
    let mut i = 0;
    while i < chars.len() {
        let c = chars[i];
        match c {
            '*' => {
                if i + 1 < chars.len() && chars[i + 1] == '*' {
                    flush(&mut literal, &mut out);
                    out.push_str(".*");
                    i += 2;
                    if i < chars.len() && chars[i] == '/' {
                        i += 1;
                    }
                    continue;
                }
                flush(&mut literal, &mut out);
                out.push_str("[^/]*");
            }
            '?' => {
                flush(&mut literal, &mut out);
                out.push_str("[^/]");
            }
            _ => literal.push(c),
        }
        i += 1;
    }
    flush(&mut literal, &mut out);
    out.push('$');
    regex::Regex::new(&out).expect("glob 转正则固定合法")
}

fn flush(literal: &mut String, out: &mut String) {
    if !literal.is_empty() {
        out.push_str(&regex::escape(literal));
        literal.clear();
    }
}

/// 模式中**通配符之前的固定目录前缀**（无则空串）。
fn fixed_prefix(pattern: &str) -> String {
    let parts: Vec<&str> = pattern.split('/').collect();
    let mut keep: Vec<&str> = Vec::new();
    for part in &parts[..parts.len().saturating_sub(1)] {
        if has_wildcard(part) {
            break;
        }
        keep.push(part);
    }
    keep.join("/")
}

fn to_posix(p: &Path) -> String {
    p.to_string_lossy().replace('\\', "/")
}

fn walk_files(dir: &Path, root: &Path, out: &mut Vec<String>) {
    let Ok(rd) = std::fs::read_dir(dir) else { return };
    for e in rd.flatten() {
        let Ok(ft) = e.file_type() else { continue };
        let p = e.path();
        if ft.is_dir() {
            walk_files(&p, root, out);
        } else if ft.is_file() {
            if let Ok(rel) = p.strip_prefix(root) {
                out.push(to_posix(rel));
            }
        }
    }
}

/// `Path(root).glob(pattern)` 的等价物 → **已排序的仓库相对 POSIX 路径**（仅文件）。
///
/// 真源 `assertions._glob` 返回的是 `str(Path(root)/p)`（含 root 前缀、平台分隔符）；
/// 本函数只回相对路径，需要那个形态时用 [`py_path_str`] 拼。
pub fn expand(root: &Path, pattern: &str) -> Vec<String> {
    Cache::new().expand(root, pattern)
}

/// 一次只读扫描内的 glob 缓存。**三层**，各治一类重复：
///
/// - `patterns`：同一模式的结果复用（真源 `_expand_many` 的同名层）；
/// - `dirs`：**单层目录清单**——这是「逐段字面剪枝」能跨模式共享的关键。
///   `community/*/protocol.yaml`、`community/*/modules/*.md`、`community/*/assets/*.md`
///   都要先列一遍 `community/` 与各包目录；有这层就只列一次；
/// - `trees`：`**` 模式的**全递归子树**清单（`community/**/*` 这类整棵树只需走一遍）。
///
/// **三层的由来**（实测 2026-10-03，性能修正迭代三轮，代价都记在注释里）：
/// 只有 `trees` 时，窄模式被迫先把整棵前缀子树枚举出来再过滤（为 360 份资产件走 2191 件）；
/// 只做「按段定深」时，同深度模式能共享、不同深度不能；
/// 只做「逐段剪枝」时，各模式各走一遍目录（`layers` 因此从 257 ms 退到 453 ms）。
/// 三层齐备才同时拿到两边的便宜。
#[derive(Default)]
pub struct Cache {
    patterns: std::collections::HashMap<String, Vec<String>>,
    dirs: std::collections::HashMap<String, Vec<(String, bool)>>,
    trees: std::collections::HashMap<String, Vec<String>>,
}

impl Cache {
    pub fn new() -> Self {
        Self::default()
    }

    /// 单层目录清单（`(名, 是否目录)`，已排序）。
    fn entries(&mut self, dir: &Path) -> Vec<(String, bool)> {
        let key = dir.to_string_lossy().to_string();
        if let Some(v) = self.dirs.get(&key) {
            return v.clone();
        }
        let mut v: Vec<(String, bool)> = Vec::new();
        if let Ok(rd) = std::fs::read_dir(dir) {
            for e in rd.flatten() {
                let name = e.file_name().to_string_lossy().to_string();
                let is_dir = e.file_type().map(|t| t.is_dir()).unwrap_or(false);
                v.push((name, is_dir));
            }
        }
        v.sort();
        self.dirs.insert(key, v.clone());
        v
    }

    pub fn expand(&mut self, root: &Path, pattern: &str) -> Vec<String> {
        if !has_wildcard(pattern) {
            return if root.join(pattern).is_file() {
                vec![pattern.to_string()]
            } else {
                Vec::new()
            };
        }
        if pattern.contains('[') {
            // 字符类不在本模块承诺范围内——**显式不出结果**，由调用方决定回退或报错。
            return Vec::new();
        }
        if let Some(v) = self.patterns.get(pattern) {
            return v.clone();
        }

        let out: Vec<String> = if pattern.contains("**") {
            let prefix = fixed_prefix(pattern);
            let all = self.subtree(root, &prefix);
            let re = to_regex(pattern);
            let mut o: Vec<String> = all.into_iter().filter(|rel| re.is_match(rel)).collect();
            o.sort();
            o
        } else {
            let prefix = fixed_prefix(pattern);
            // **先看有没有同前缀的全递归清单**（`community/**/*` 这类宽模式留下的）：
            // 有就只需正则过滤，别再逐段走一遍。
            // 实测教训（2026-10-03）：丢了这一步后 `layers` 从 257 ms 退到 453 ms——
            // `community/**/*` 本来就要整棵走一遍，那 4 条 `community/*/…` 窄模式
            // 白捡的「过滤已缓存清单」被我换成了「各走一遍目录」。
            if let Some(all) = self.trees.get(&prefix).cloned() {
                let re = to_regex(pattern);
                let mut o: Vec<String> = all.into_iter().filter(|rel| re.is_match(rel)).collect();
                o.sort();
                o
            } else {
                // **逐段字面剪枝**：字面段（如 `assets`）直接下钻，不做 readdir；
                // 只有通配段才列目录，且列出的清单进 `dirs` 供其它模式复用。
                let segs: Vec<String> = pattern.split('/').map(|s| s.to_string()).collect();
                let mut o: Vec<String> = Vec::new();
                self.walk_segments(root, root, &segs, &mut o);
                o.sort();
                o.dedup();
                o
            }
        };
        self.patterns.insert(pattern.to_string(), out.clone());
        out
    }

    /// 前缀子树的**全递归**清单（按前缀缓存，跨模式共享）。
    fn subtree(&mut self, root: &Path, prefix: &str) -> Vec<String> {
        if let Some(v) = self.trees.get(prefix) {
            return v.clone();
        }
        let base = if prefix.is_empty() { root.to_path_buf() } else { root.join(prefix) };
        let mut v = Vec::new();
        walk_files(&base, root, &mut v);
        self.trees.insert(prefix.to_string(), v.clone());
        v
    }

    fn walk_segments(&mut self, root: &Path, dir: &Path, segs: &[String], out: &mut Vec<String>) {
        let Some((head, tail)) = segs.split_first() else { return };
        if is_literal_seg(head) {
            let next = dir.join(head);
            if tail.is_empty() {
                if next.is_file() {
                    if let Ok(rel) = next.strip_prefix(root) {
                        out.push(to_posix(rel));
                    }
                }
            } else if next.is_dir() {
                self.walk_segments(root, &next, tail, out);
            }
            return;
        }
        let re = to_regex(head);
        for (name, is_dir) in self.entries(dir) {
            if !re.is_match(&name) {
                continue;
            }
            let p = dir.join(&name);
            if tail.is_empty() {
                if !is_dir {
                    if let Ok(rel) = p.strip_prefix(root) {
                        out.push(to_posix(rel));
                    }
                }
            } else if is_dir {
                self.walk_segments(root, &p, tail, out);
            }
        }
    }
}

fn is_literal_seg(s: &str) -> bool {
    !s.chars().any(|c| c == '*' || c == '?' || c == '[')
}



/// **含目录**的展开 —— 复刻 Python `glob.glob(pattern, recursive=True)` 的存在性语义。
///
/// 真源 `patterns.scan` 用它判 `applies_to` 通配是否命中真实件，而 Python 的 `glob` 模块
/// **目录也算命中**（`pathlib.glob` 之后的 `.is_file()` 过滤在那边没有）。本函数返回文件与目录。
///
/// 另一处细节：Python 的 `docs/**`（recursive）会连 `docs/` **本身**一起返回（带尾斜杠）；
/// 故模式以 `**` 结尾时，本函数把前缀目录自身也算作命中——否则「只有 `**` 结尾的模式」
/// 会在空目录上误报。
pub fn expand_any(root: &Path, pattern: &str) -> Vec<String> {
    if !has_wildcard(pattern) {
        return if root.join(pattern).exists() {
            vec![pattern.to_string()]
        } else {
            Vec::new()
        };
    }
    if pattern.contains('[') {
        return Vec::new();
    }
    let re = to_regex(pattern);
    let prefix = fixed_prefix(pattern);
    let base = if prefix.is_empty() { root.to_path_buf() } else { root.join(&prefix) };
    let mut all = Vec::new();
    walk_entries(&base, root, &mut all);
    let mut out: Vec<String> = all.into_iter().filter(|rel| re.is_match(rel)).collect();
    if pattern.ends_with("**") && !prefix.is_empty() && base.exists() {
        out.push(prefix.clone());
    }
    out.sort();
    out.dedup();
    out
}

fn walk_entries(dir: &Path, root: &Path, out: &mut Vec<String>) {
    let Ok(rd) = std::fs::read_dir(dir) else { return };
    for e in rd.flatten() {
        let p = e.path();
        if let Ok(rel) = p.strip_prefix(root) {
            out.push(to_posix(rel));
        }
        if e.file_type().map(|t| t.is_dir()).unwrap_or(false) {
            walk_entries(&p, root, out);
        }
    }
}

/// 复刻 `str(Path(root) / rel)`：Windows 用反斜杠；`root` 尾部分隔符归一；`root == "."` 时丢弃 `./`。
pub fn py_path_str(root: &Path, rel: &str) -> String {
    let mut root_s = to_posix(root);
    if root_s.len() > 1 {
        root_s = root_s.trim_end_matches('/').to_string();
    }
    let body = if cfg!(windows) { rel.replace('/', "\\") } else { rel.to_string() };
    if root_s.is_empty() || root_s == "." {
        return body;
    }
    if cfg!(windows) {
        format!("{}\\{}", root_s.replace('/', "\\"), body)
    } else {
        format!("{}/{}", root_s, body)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn wildcard_detection_matches_truth_source_rule() {
        assert!(has_wildcard("a/*.md"));
        assert!(has_wildcard("a/**/b"));
        assert!(has_wildcard("a/?"));
        assert!(has_wildcard("a/[xy]"));
        assert!(!has_wildcard("docs/layers.md"));
    }

    #[test]
    fn star_does_not_cross_directory_separator() {
        let re = to_regex("protocol/schema/*.json");
        assert!(re.is_match("protocol/schema/asset.schema.json"));
        assert!(!re.is_match("protocol/schema/sub/asset.json"));
    }

    #[test]
    fn double_star_crosses_and_matches_zero_segments() {
        let re = to_regex("a/**/*.md");
        assert!(re.is_match("a/x.md"), "`**` 应可匹配零段");
        assert!(re.is_match("a/b/c/x.md"));
        let re2 = to_regex("external/**/*");
        assert!(re2.is_match("external/x"));
        assert!(re2.is_match("external/a/b"));
    }

    #[test]
    fn fixed_prefix_stops_at_first_wildcard_segment() {
        assert_eq!(fixed_prefix("docs/examples/state-front/*.md"), "docs/examples/state-front");
        assert_eq!(fixed_prefix("a/**/b/*.md"), "a");
        assert_eq!(fixed_prefix("*.md"), "");
    }

    #[test]
    fn char_class_is_out_of_scope_and_yields_nothing() {
        // 不在承诺范围内的形态必须**空手而归**，不许给出近似结果
        let tmp = crate::testutil::fixture("glob");
        std::fs::write(tmp.join("a.md"), b"x").unwrap();
        assert!(expand(&tmp, "[ab].md").is_empty());
        let _ = std::fs::remove_dir_all(&tmp);
    }

    #[test]
    fn expand_finds_files_and_sorts_them() {
        let tmp = crate::testutil::fixture("glob2");
        std::fs::create_dir_all(tmp.join("d/sub")).unwrap();
        std::fs::write(tmp.join("d/b.md"), b"x").unwrap();
        std::fs::write(tmp.join("d/a.md"), b"x").unwrap();
        std::fs::write(tmp.join("d/sub/c.md"), b"x").unwrap();
        assert_eq!(expand(&tmp, "d/*.md"), vec!["d/a.md".to_string(), "d/b.md".to_string()]);
        assert_eq!(
            expand(&tmp, "d/**/*.md"),
            vec!["d/a.md".to_string(), "d/b.md".to_string(), "d/sub/c.md".to_string()]
        );
        assert_eq!(expand(&tmp, "d/a.md"), vec!["d/a.md".to_string()]);
        assert!(expand(&tmp, "d/none.md").is_empty());
        let _ = std::fs::remove_dir_all(&tmp);
    }

    #[test]
    fn cache_segment_pruning_skips_unrelated_dirs() {
        // `community/*/assets/*.md` 必须只碰各包的 assets 目录，不得枚举包内其它件
        let tmp = crate::testutil::fixture("glob-prune");
        std::fs::create_dir_all(tmp.join("community/p1/assets")).unwrap();
        std::fs::create_dir_all(tmp.join("community/p1/modules")).unwrap();
        std::fs::create_dir_all(tmp.join("community/p2/assets")).unwrap();
        std::fs::write(tmp.join("community/p1/assets/A.md"), "x").unwrap();
        std::fs::write(tmp.join("community/p1/modules/M.md"), "x").unwrap();
        std::fs::write(tmp.join("community/p2/assets/B.md"), "x").unwrap();
        std::fs::write(tmp.join("community/p2/README.md"), "x").unwrap();

        let mut c = Cache::new();
        assert_eq!(
            c.expand(&tmp, "community/*/assets/*.md"),
            vec!["community/p1/assets/A.md", "community/p2/assets/B.md"]
        );
        // 命中整模式缓存
        assert_eq!(c.expand(&tmp, "community/*/assets/*.md").len(), 2);
        // 单层目录清单已缓存 ⇒ 换个模式不必重列 `community/`
        assert!(c.dirs.contains_key(&tmp.join("community").to_string_lossy().to_string()));
        assert_eq!(c.expand(&tmp, "community/*/modules/*.md"), vec!["community/p1/modules/M.md"]);
        let _ = std::fs::remove_dir_all(&tmp);
    }

    #[test]
    fn cache_prefers_a_cached_subtree_over_a_segment_walk() {
        // 有 `**` 留下的全递归清单时，窄模式只需过滤它（layers 曾有 257→453 ms 的教训）
        let tmp = crate::testutil::fixture("glob-subtree");
        std::fs::create_dir_all(tmp.join("community/p1/assets")).unwrap();
        std::fs::write(tmp.join("community/p1/assets/A.md"), "x").unwrap();
        std::fs::write(tmp.join("community/p1/note.md"), "x").unwrap();
        let mut c = Cache::new();
        let wide = c.expand(&tmp, "community/**/*.md");
        assert_eq!(wide.len(), 2);
        assert!(c.trees.contains_key("community"), "宽模式应留下全递归清单");
        assert!(c.dirs.is_empty(), "走了全递归就不该再列单层目录");
        assert_eq!(c.expand(&tmp, "community/*/assets/*.md"), vec!["community/p1/assets/A.md"]);
        let _ = std::fs::remove_dir_all(&tmp);
    }

    #[test]
    fn py_path_str_drops_dot_root_and_uses_platform_separator() {
        assert_eq!(py_path_str(Path::new("."), "a/b.md"), if cfg!(windows) { "a\\b.md" } else { "a/b.md" });
        let got = py_path_str(Path::new("C:/x/y/"), "a/b.md");
        assert!(got.ends_with(if cfg!(windows) { "y\\a\\b.md" } else { "y/a/b.md" }), "got: {}", got);
    }
}