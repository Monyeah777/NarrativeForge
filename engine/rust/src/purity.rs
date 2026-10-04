//! 架构纯度体检 R1–R7（`purity` 判据 / `purity-clean` 契约 / `score` 的 `purity_clean` 信号源）
//! —— 与真源 `desktop/src/core/purity_scan.py` 的 `scan` 对账。
//!
//! **R1–R3**（协议层文档）：端壳/APK 残留（仅前两份文档判）、私货/可变物（绝对路径 / TODO 等）、
//! 重复标题。**R4**（`desktop/src/core/*.py`）：`raise` 消息须带修复指引。**R5**：第三方 import
//! 须登记（或软导入 + 守卫）。**R6**：危险 sink（动态执行 / shell / 不安全反序列化 / 删除面）
//! + 登记表自洽（每个 sink 类目须带 CWE 对齐、放行键须指向已登记 sink）。**R7**：分层阶梯（走
//! `layers::scan`，即真源 `layer_model`）。
//!
//! **移植面按消费者界定**：真源的 `write`/`apply` 类写面、以及 `memo_pair`/`disk_cache`/逐件
//! findings 三层缓存**不移植**——缓存是纯函数优化，不改结论。
//!
//! **R1–R3 的顺序陷阱**：真源 `_doc_facts` 的重复标题取自 `dict` 的**插入序**（首次出现的顺序），
//! 不是排序序。本线用 `Vec` 保持插入序。

use crate::pyast;
use crate::pyjson::Json;
use std::path::Path;

pub const PROTO_DOCS: [&str; 4] = [
    "01_核心协议.md",
    "02_联动注册表.md",
    "06_Agent执行协议.md",
    "07_官方核心出厂与社区预设导航.md",
];

/// 真源 `IMPORT_SCAN`（R5 的取件面）。
pub const IMPORT_SCAN: [&str; 3] =
    ["desktop/src/core/*.py", "scripts/*.py", ".github/scripts/*.py"];

/// 真源 `HARD_ALLOW`：登记的第三方硬依赖（允许直接 import）。
const HARD_ALLOW: [&str; 1] = ["yaml"];

/// 真源 `SOFT_IMPORTS`：第三方可选依赖（须 try/except ImportError 守卫）。值只用于消息。
const SOFT_IMPORTS: [(&str, &str); 3] = [
    ("jsonschema", "IDL 标准实现交叉验证（可选对照；缺依赖则跳过该面）"),
    ("PySide6", "CCV3 卡面占位图写入（缺依赖须给明确修复指引，不得裸 ImportError）"),
    (
        "laya",
        "决策层本地服务（scripts/serve_decision_model.py）的模型运行时；软导入 + 缺依赖给修复指引",
    ),
];

/// 真源 `IMPORT_RESIDUE`（空表 = 零残留）。
const IMPORT_RESIDUE: [(&str, &str); 0] = [];

/// 真源 `DANGEROUS_CALLS`（键 = 规范化调用名；值 = CWE 对齐说明）。
const DANGEROUS_CALLS: [(&str, &str); 12] = [
    ("eval", "CWE-95 动态执行（输入可注入）"),
    ("exec", "CWE-95 动态执行（输入可注入）"),
    ("__import__", "CWE-470 动态导入（须证明模块名非用户输入）"),
    ("os.system", "CWE-78 shell 命令（改用 subprocess 列表参数）"),
    ("os.popen", "CWE-78 shell 管道（改用 subprocess 列表参数）"),
    ("pickle.load", "CWE-502 不安全反序列化（可执行任意代码）"),
    ("pickle.loads", "CWE-502 不安全反序列化（可执行任意代码）"),
    ("marshal.loads", "CWE-502 不安全反序列化"),
    ("yaml.load", "CWE-502 非安全 YAML 载入（改用 yaml.safe_load）"),
    ("shutil.rmtree", "CWE-73 递归删除外部可控路径（须证明落点非主目录/仓库根/盘根）"),
    ("os.remove", "CWE-73 删除外部可控路径（须证明来源不可被外部左右）"),
    ("os.rmdir", "CWE-73 删除外部可控目录"),
];

/// 真源 `METHOD_SINKS`（按**方法名**匹配，避免随接收者变量名漂移）。
const METHOD_SINKS: [(&str, &str); 1] = [(
    "unlink",
    "CWE-73 删除外部可控文件（`Path.unlink` 等价 `os.remove`，同样须证明来源不可被外部左右）",
)];

/// 真源 `SINK_ALLOW`（键 = `<文件基名>:<调用名>`；放行须可审计）。值不参与判据，只作留档。
const SINK_ALLOW: [(&str, &str); 10] = [
    ("regression_score.py:__import__", ""),
    ("e2e_desktop_headless.py:shutil.rmtree", ""),
    ("storage.py:shutil.rmtree", ""),
    ("watch.py:os.rmdir", ""),
    ("disk_cache.py:unlink", ""),
    ("atomic_write.py:unlink", ""),
    ("domain_pack.py:unlink", ""),
    ("pack_combo.py:unlink", ""),
    ("storage.py:unlink", ""),
    ("watch.py:unlink", ""),
];

fn end_shell_re() -> &'static regex::Regex {
    static RE: std::sync::OnceLock<regex::Regex> = std::sync::OnceLock::new();
    RE.get_or_init(|| regex::Regex::new(r"(?i)(android|APK|src/ui|Kivy)").expect("固定合法"))
}

fn private_re() -> &'static regex::Regex {
    static RE: std::sync::OnceLock<regex::Regex> = std::sync::OnceLock::new();
    RE.get_or_init(|| {
        regex::Regex::new(r"[A-Za-z]:\\|/tmp/|/Users/|/home/|TODO|FIXME|XXX|TBD").expect("固定合法")
    })
}

fn head_re() -> &'static regex::Regex {
    static RE: std::sync::OnceLock<regex::Regex> = std::sync::OnceLock::new();
    RE.get_or_init(|| regex::Regex::new(r"^#{1,6}\s+(.*?)\s*$").expect("固定合法"))
}

fn action_re() -> &'static regex::Regex {
    static RE: std::sync::OnceLock<regex::Regex> = std::sync::OnceLock::new();
    RE.get_or_init(|| {
        regex::Regex::new(
            r"(应|须|先|必填|必需|必须|请|建议|参考|查看|运行|执行|使用|改用|替换|修复|补齐|重新|重跑|更正|核对|检查|可选|选项|列表|注册|示例|格式|参见|见|按|需|选择|可用|如|缺少|缺|期望|修正|§|文档|帮助|重试|再)",
        )
        .expect("固定合法")
    })
}

/// 真源 `_NEEDS_AST` 的文本预筛：不命中即三类事实必然为空，连 parse 都不做。
fn needs_ast_re() -> &'static regex::Regex {
    static RE: std::sync::OnceLock<regex::Regex> = std::sync::OnceLock::new();
    RE.get_or_init(|| {
        let tails: Vec<String> = DANGEROUS_CALLS
            .iter()
            .map(|(c, _)| regex::escape(c.rsplit('.').next().unwrap_or(c)))
            .collect();
        regex::Regex::new(&format!(r"raise|import|try|shell|{}", tails.join("|")))
            .expect("固定合法")
    })
}

fn cwe_re() -> &'static regex::Regex {
    static RE: std::sync::OnceLock<regex::Regex> = std::sync::OnceLock::new();
    RE.get_or_init(|| regex::Regex::new(r"^CWE-\d+ ").expect("固定合法"))
}

/// Python 的 `list[:n]`（**按字符**截断）。
fn head_chars(s: &str, n: usize) -> String {
    s.chars().take(n).collect()
}

/// 真源 `_doc_facts` → `(端壳命中, 私货命中, 重复标题)`。
pub struct DocFacts {
    pub shell: Vec<(u32, String)>,
    pub private: Vec<(u32, String)>,
    /// **插入序**（首次出现顺序），值是该标题出现的行号。
    pub dup_titles: Vec<(String, Vec<u32>)>,
}

pub fn doc_facts(text: &str) -> DocFacts {
    let mut shell = Vec::new();
    let mut private = Vec::new();
    let mut seen: Vec<(String, Vec<u32>)> = Vec::new();
    for (i, ln) in text.lines().enumerate() {
        let i = i as u32 + 1;
        if end_shell_re().is_match(ln) {
            shell.push((i, head_chars(ln.trim(), 80)));
        }
        if private_re().is_match(ln) {
            private.push((i, head_chars(ln.trim(), 80)));
        }
        if let Some(c) = head_re().captures(ln) {
            let title = c[1].trim().to_string();
            match seen.iter_mut().find(|(t, _)| *t == title) {
                Some((_, v)) => v.push(i),
                None => seen.push((title, vec![i])),
            }
        }
    }
    let dup_titles = seen.into_iter().filter(|(_, v)| v.len() > 1).collect();
    DocFacts { shell, private, dup_titles }
}

/// 真源 `_is_local`。
fn is_local(mod_: &str, root: &Path) -> bool {
    if mod_ == "core" {
        return true;
    }
    for base in ["desktop/src/core", "scripts", ".github/scripts"] {
        if root.join(base).join(format!("{}.py", mod_)).exists() {
            return true;
        }
    }
    false
}

/// 单份源码的 R4–R6 findings。
pub struct FileFindings {
    pub issues: Vec<String>,
    pub raises: i64,
    pub imports: i64,
    pub sinks: i64,
    pub residue: Vec<String>,
}

/// 真源 `_file_findings`。`None` 表示事实不可得（未命中预筛 / 解析失败）——与真源一致，
/// 此时该件贡献空结论。
pub fn file_findings(rel: &str, text: &str, root: &Path) -> Option<FileFindings> {
    if !needs_ast_re().is_match(text) {
        return None;
    }
    let facts = pyast::purity_facts(text)?;
    let fname = rel.rsplit('/').next().unwrap_or(rel);
    let residue: Option<&str> = IMPORT_RESIDUE.iter().find(|(r, _)| *r == rel).map(|(_, v)| *v);
    let mut out: Vec<String> = Vec::new();
    let mut delta = FileFindings {
        issues: Vec::new(),
        raises: 0,
        imports: 0,
        sinks: 0,
        residue: Vec::new(),
    };

    for r in &facts.raises {
        delta.raises += 1;
        if !r.msg.is_empty() && !action_re().is_match(&r.msg) {
            out.push(format!(
                "{}:{} raise 消息缺修复指引：{}",
                fname,
                r.lineno,
                head_chars(&r.msg, 60)
            ));
        }
    }
    for (mod_, lineno) in &facts.modules {
        if crate::py_stdlib::STDLIB.contains(&mod_.as_str()) || is_local(mod_, root) {
            continue;
        }
        delta.imports += 1;
        if HARD_ALLOW.contains(&mod_.as_str()) {
            continue;
        }
        if let Some((_, why)) = SOFT_IMPORTS.iter().find(|(m, _)| m == mod_) {
            if !facts.guarded.contains(lineno) {
                let msg = format!(
                    "{}:{} 第三方 {} 未软导入（须 try/except ImportError 守卫；登记理由：{}）",
                    rel, lineno, mod_, why
                );
                out.push(match residue {
                    Some(r) => format!("{}（{}）", msg, r),
                    None => msg,
                });
            }
            continue;
        }
        let msg = format!(
            "{}:{} 第三方 import 未登记：{}（修复指引：改为软导入并在 purity_scan.SOFT_IMPORTS 登记理由，或加入 HARD_ALLOW；端壳残留则登记 IMPORT_RESIDUE）",
            rel, lineno, mod_
        );
        out.push(match residue {
            Some(r) => format!("{}（{}）", msg, r),
            None => msg,
        });
    }
    for s in &facts.sinks {
        let mut flags: Vec<(String, String)> = Vec::new();
        if DANGEROUS_CALLS.iter().any(|(c, _)| *c == s.call) {
            flags.push((s.call.clone(), s.call.clone()));
        }
        let method = s.call.rsplit('.').next().unwrap_or(&s.call).to_string();
        if METHOD_SINKS.iter().any(|(m, _)| *m == method) {
            flags.push((method.clone(), method.clone()));
        }
        if s.shell_true {
            flags.push(("subprocess(shell=True)".to_string(), "subprocess".to_string()));
        }
        for (name, key_name) in flags {
            delta.sinks += 1;
            if SINK_ALLOW
                .iter()
                .any(|(k, _)| *k == format!("{}:{}", fname, key_name))
            {
                continue;
            }
            let why = DANGEROUS_CALLS
                .iter()
                .find(|(c, _)| *c == s.call)
                .map(|(_, d)| (*d).to_string())
                .or_else(|| {
                    METHOD_SINKS
                        .iter()
                        .find(|(m, _)| *m == method)
                        .map(|(_, d)| (*d).to_string())
                })
                .unwrap_or_else(|| "shell=True 命令注入面".to_string());
            out.push(format!(
                "{}:{} 危险 sink {}（{}）——确需使用须在 purity_scan.SINK_ALLOW 登记理由（修复指引：改用安全等价物，或登记后写明为何不可注入）",
                rel, s.lineno, name, why
            ));
        }
    }
    delta.issues = out;
    Some(delta)
}

/// 真源 `scan` → `(issues, stats)`。
pub fn scan(root: &Path) -> (Vec<String>, Json) {
    let mut issues: Vec<String> = Vec::new();
    let mut docs = 0i64;
    let mut raises = 0i64;
    let mut imports = 0i64;
    let mut sinks: Option<i64> = None;
    let mut residue: Vec<Json> = Vec::new();

    // R1/R2/R3：协议层文档
    for name in PROTO_DOCS {
        let p = root.join(name);
        if !p.exists() {
            continue;
        }
        let Ok(text) = std::fs::read_to_string(&p) else { continue };
        docs += 1;
        let f = doc_facts(&text);
        // 端壳残留**只在前两份**判
        if name == "01_核心协议.md" || name == "02_联动注册表.md" {
            for (i, ln) in &f.shell {
                issues.push(format!("{}:{} 端壳/APK 残留：{}", name, i, ln));
            }
        }
        for (i, ln) in &f.private {
            issues.push(format!("{}:{} 私货/可变物：{}", name, i, ln));
        }
        for (title, lines) in &f.dup_titles {
            let ls: Vec<String> = lines.iter().map(|x| x.to_string()).collect();
            issues.push(format!("{} 重复标题「{}」：行 {}", name, title, ls.join(",")));
        }
    }

    // R4：core/*.py（按文件名排序）
    let core_rel = "desktop/src/core";
    let mut core_files: Vec<String> = Vec::new();
    if root.join(core_rel).is_dir() {
        if let Ok(rd) = std::fs::read_dir(root.join(core_rel)) {
            for e in rd.flatten() {
                let n = e.file_name().to_string_lossy().to_string();
                if n.ends_with(".py") {
                    core_files.push(n);
                }
            }
        }
    }
    core_files.sort();
    for fname in &core_files {
        let rel = format!("{}/{}", core_rel, fname);
        let Ok(text) = std::fs::read_to_string(root.join(&rel)) else { continue };
        if let Some(d) = file_findings(&rel, &text, root) {
            issues.extend(d.issues);
            raises += d.raises;
            imports += d.imports;
            *sinks.get_or_insert(0) += d.sinks;
            residue.extend(d.residue.into_iter().map(Json::Str));
        }
    }

    // R5：IMPORT_SCAN 面（跳过 core/*，R4 已算过）
    let mut rels: Vec<String> = Vec::new();
    for pat in IMPORT_SCAN {
        rels.extend(crate::glob::expand(root, pat));
    }
    rels.sort();
    rels.dedup();
    for rel in &rels {
        if rel.starts_with("desktop/src/core/") {
            continue;
        }
        let Ok(text) = std::fs::read_to_string(root.join(rel)) else { continue };
        if let Some(d) = file_findings(rel, &text, root) {
            issues.extend(d.issues);
            imports += d.imports; // raises 只在 R4 那一段计
            *sinks.get_or_insert(0) += d.sinks;
            residue.extend(d.residue.into_iter().map(Json::Str));
        }
    }

    // R6 自洽面：登记表自身的判据
    let mut all_sinks: Vec<(&str, &str)> = DANGEROUS_CALLS.to_vec();
    all_sinks.extend(METHOD_SINKS.iter().copied());
    all_sinks.sort_by(|a, b| a.0.cmp(b.0));
    for (call, desc) in all_sinks {
        if !cwe_re().is_match(desc) {
            issues.push(format!(
                "危险 sink 类目缺 CWE 对齐：{}（修复指引：在 purity_scan.DANGEROUS_CALLS 的说明前加 `CWE-<nnn> `，便于外部扫描器按缺陷类型对账）",
                call
            ));
        }
    }
    let mut allow_keys: Vec<&str> = SINK_ALLOW.iter().map(|(k, _)| *k).collect();
    allow_keys.sort();
    for key in allow_keys {
        let sink = key.rsplit(':').next().unwrap_or(key);
        if !DANGEROUS_CALLS.iter().any(|(c, _)| *c == sink)
            && !METHOD_SINKS.iter().any(|(m, _)| *m == sink)
            && sink != "subprocess"
        {
            issues.push(format!(
                "SINK_ALLOW 放行键指向未登记 sink：{}（修复指引：删除放行，或先在 DANGEROUS_CALLS 登记该 sink 类目）",
                key
            ));
        }
    }

    // R7：抽象阶梯（真源 layer_model）
    let layers: Json = if root.join(crate::layers::DECL_REL).is_file() {
        let (li, ls) = crate::layers::scan(root);
        issues.extend(li);
        ls
    } else {
        Json::Object(vec![(
            "skipped".to_string(),
            Json::Str(format!(
                "缺 {}（另由断言表与规范性名单判）",
                crate::layers::DECL_REL
            )),
        )])
    };

    let stats = Json::Object(vec![
        ("docs".to_string(), Json::Int(docs)),
        ("raises".to_string(), Json::Int(raises)),
        ("imports".to_string(), Json::Int(imports)),
        ("import_residue".to_string(), Json::Array(residue)),
        ("sinks".to_string(), Json::Int(sinks.unwrap_or(0))),
        ("layers".to_string(), layers),
    ]);
    (issues, stats)
}

#[cfg(test)]
mod tests {
    use super::*;
    // >>> GENERATED by tools/gen_purity_branches.py（勿手改；重跑生成器覆盖本段）
    /// ===== 分支级差分判据（期望值由 `tools/gen_purity_branches.py` 从真源生成）=====
    ///
    /// 真语料上该判据 **0 issue** ⇒ 错误分支全未踩到。本夹具逐支踩：R1 端壳（**且只在前两份
    /// 文档判**——第三份带 android 字样但不报）/ R2 私货 / R3 重复标题 / R4 raise 缺指引（含
    /// "带指引"与"f-string 常量段"两个反例）/ R5 未登记第三方（含软导入未守卫、软导入已守卫、
    /// 硬白名单 `yaml`、标准库、本仓局部 `core.other_local` 五个反例）/ R6 三类 sink（整串命中 /
    /// 末段命中 / `shell=True`）+ `SINK_ALLOW` 放行命中（`storage.py:unlink`）/ R7 缺阶梯件。
    ///
    /// **踩不到的分支**：R6 自洽面（表缺 CWE 对齐、放行键指向未登记 sink）由**常量表本身**驱动
    /// ——夹具改不了编译期常量，故本线那两支不可达；属"表的不变量"，代码保留但无判据覆盖。
    const PURITY_DOC1: &str = r#"# 总纲
本节提到 android 端的旧方案（应为端壳残留）。
路径 D:\private\x 与 /home/someone/y 属私货；TODO 也该清。
## 同名小节
正文一
## 同名小节
正文二
"#;
    const PURITY_DOC2: &str = r#"# 联动
## 也重复
甲
## 也重复
乙
"#;
    const PURITY_DOC3: &str = r#"# 执行协议
这里出现 android 字样，但本档不在端壳判据面内。
"#;
    const PURITY_CORE: &str = r#"import os
import yaml
from core import other_local


def f():
    if True:
        raise ValueError("坏了")            # R4：无修复指引
    if True:
        raise ValueError("请改用安全写法")   # R4 反例：带指引
    raise RuntimeError(f"应检查 {os.sep}")  # R4：JoinedStr 常量段带指引
"#;
    const PURITY_SCRIPTS: &str = r#"import json
import sys
import jsonschema           # R5：软导入登记了但**无守卫**
try:
    import PySide6          # R5 反例：软导入 + 守卫 → 不报
except ImportError:
    PySide6 = None
import requests             # R5：未登记第三方
import nosuchlocal          # R5：未登记（也不是本仓局部）
import shutil
import subprocess


def g(p):
    os.system("ls")                      # R6：整串命中 DANGEROUS_CALLS
    p.unlink()                           # R6：末段命中 METHOD_SINKS
    subprocess.run("x", shell=True)      # R6：shell=True
    shutil.rmtree(p)                     # R6：整串命中
"#;
    const PURITY_STORAGE: &str = r#"import pathlib


def clean(p):
    p.unlink()
"#;

    fn build_purity_fixture() -> std::path::PathBuf {
        let root = crate::testutil::fixture("purity-branches");
        let write = |rel: &str, body: &str| {
            let p = root.join(rel);
            std::fs::create_dir_all(p.parent().unwrap()).unwrap();
            std::fs::write(p, body).unwrap();
        };
        write("01_核心协议.md", PURITY_DOC1);
        write("02_联动注册表.md", PURITY_DOC2);
        write("06_Agent执行协议.md", PURITY_DOC3);
        write("desktop/src/core/zz_fixture.py", PURITY_CORE);
        write("desktop/src/core/other_local.py", "X = 1\n");
        write("scripts/zz_fixture.py", PURITY_SCRIPTS);
        write("scripts/storage.py", PURITY_STORAGE);
        root
    }

    #[test]
    fn purity_matches_truth_source_branch_by_branch() {
        let root = build_purity_fixture();
        let (issues, stats) = scan(&root);
        assert_eq!(issues, &[r#"01_核心协议.md:2 端壳/APK 残留：本节提到 android 端的旧方案（应为端壳残留）。"#, r#"01_核心协议.md:3 私货/可变物：路径 D:\private\x 与 /home/someone/y 属私货；TODO 也该清。"#, r#"01_核心协议.md 重复标题「同名小节」：行 4,6"#, r#"02_联动注册表.md 重复标题「也重复」：行 2,4"#, r#"zz_fixture.py:8 raise 消息缺修复指引：坏了"#, r#"scripts/zz_fixture.py:3 第三方 jsonschema 未软导入（须 try/except ImportError 守卫；登记理由：IDL 标准实现交叉验证（可选对照；缺依赖则跳过该面））"#, r#"scripts/zz_fixture.py:8 第三方 import 未登记：requests（修复指引：改为软导入并在 purity_scan.SOFT_IMPORTS 登记理由，或加入 HARD_ALLOW；端壳残留则登记 IMPORT_RESIDUE）"#, r#"scripts/zz_fixture.py:9 第三方 import 未登记：nosuchlocal（修复指引：改为软导入并在 purity_scan.SOFT_IMPORTS 登记理由，或加入 HARD_ALLOW；端壳残留则登记 IMPORT_RESIDUE）"#, r#"scripts/zz_fixture.py:15 危险 sink os.system（CWE-78 shell 命令（改用 subprocess 列表参数））——确需使用须在 purity_scan.SINK_ALLOW 登记理由（修复指引：改用安全等价物，或登记后写明为何不可注入）"#, r#"scripts/zz_fixture.py:16 危险 sink unlink（CWE-73 删除外部可控文件（`Path.unlink` 等价 `os.remove`，同样须证明来源不可被外部左右））——确需使用须在 purity_scan.SINK_ALLOW 登记理由（修复指引：改用安全等价物，或登记后写明为何不可注入）"#, r#"scripts/zz_fixture.py:17 危险 sink subprocess(shell=True)（shell=True 命令注入面）——确需使用须在 purity_scan.SINK_ALLOW 登记理由（修复指引：改用安全等价物，或登记后写明为何不可注入）"#, r#"scripts/zz_fixture.py:18 危险 sink shutil.rmtree（CWE-73 递归删除外部可控路径（须证明落点非主目录/仓库根/盘根））——确需使用须在 purity_scan.SINK_ALLOW 登记理由（修复指引：改用安全等价物，或登记后写明为何不可注入）"#] as &[&str], "issues 须逐字且同序");
        let want: Json = crate::jsonread::convert(
            &serde_json::from_str::<serde_json::Value>(r#"{"docs": 3, "import_residue": [], "imports": 5, "layers": {"skipped": "缺 protocol/LAYERS.json（另由断言表与规范性名单判）"}, "raises": 3, "sinks": 5}"#).unwrap(),
        )
        .unwrap();
        assert!(
            crate::jsonread::json_eq(&stats, &want),
            "stats 不一致\n  实得 {}\n  期望 {}",
            stats.dumps(),
            want.dumps()
        );
    }
    // <<< GENERATED
}
