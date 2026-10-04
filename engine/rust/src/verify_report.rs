//! 门禁的**机器可读出口**（`verify_report`）—— 与真源 `desktop/src/core/verify_report.py` 对账。
//!
//! 真源把 **28 条判据**（各自调一个 core 扫描器）聚合成 `protocol/verification_report.json`：
//! 逐条归一到 `(issues, warns, stats)` → 定 status → 汇总 counts + 声明面 → 主体规范化 sha256 作
//! `root_digest`（报告被手改即对不上）→ 按 `indent=2, sort_keys=True` 渲染。
//!
//! **本线已自主算出 4/28 条**（`schema` / `doc_markers` / `baseline` / `self_stats`），
//! 其余 24 条由 `--results` 喂入各自的 `(issues, warns, stats)`——与 `score` 的 `--signals` 同一
//! 增量法：每移植一个扫描器，喂入面就小一格，内核不动。
//!
//! **口径提醒**：`root_digest` 的源串用 CPython **默认分隔符**（`", "` / `": "`，带空格），
//! 不是紧凑模式——差一个空格摘要就全变（见 `pyjson::dumps_default`）。

use crate::baseline;
use crate::jsonread;
use crate::merkle;
use crate::pyjson::Json;
use crate::pyval::{get, plain_str_opt, py_str};
use std::collections::HashMap;
use std::path::Path;

pub const REPORT_REL: &str = "protocol/verification_report.json";
pub const SCHEMA: &str = "nf-verify-report/1";

pub struct Spec {
    pub id: &'static str,
    pub name: &'static str,
    pub module: &'static str,
    pub entry: &'static str,
}

impl Spec {
    pub fn source(&self) -> String {
        format!("{}.{}", self.module, self.entry)
    }
}

/// 真源 `SPECS` 逐字（次序即报告 items 的次序）。
pub const SPECS: [Spec; 28] = [
    Spec { id: "purity", name: "架构纯度体检（R1-R7 + 分层阶梯 L1-L4）", module: "purity_scan", entry: "scan" },
    Spec { id: "schema", name: "协议层 IDL schema 门禁", module: "schema_lint", entry: "scan" },
    Spec { id: "conformance", name: "社区领域包 conformance 分级", module: "conformance_scan", entry: "scan" },
    Spec { id: "contract", name: "机读契约面（官方核心 13 件 id/标题一致）", module: "machine_contract", entry: "scan" },
    Spec { id: "knowledge", name: "双源知识层（权威分层/顺序/时效/巡检）", module: "knowledge", entry: "scan" },
    Spec { id: "rating", name: "馆藏内容分级声明", module: "rating_gate", entry: "scan" },
    Spec { id: "license", name: "许可证门", module: "license_gate", entry: "scan" },
    Spec { id: "intake", name: "投稿闸门三方一致", module: "intake", entry: "scan" },
    Spec { id: "payload", name: "事件载荷注册表", module: "payload_registry", entry: "scan" },
    Spec { id: "doc_markers", name: "文档 marker 卫生", module: "doc_hygiene", entry: "check_markers" },
    Spec { id: "assets_ledger", name: "资产 ledger 投影一致", module: "asset_ledger_projection", entry: "verify" },
    Spec { id: "instruction", name: "指令档步骤审计", module: "instruction_step_audit", entry: "scan" },
    Spec { id: "baseline", name: "基线自描述一致（verify 版本 / check 数）", module: "quality_baseline", entry: "scan" },
    Spec { id: "library", name: "图书馆 frontmatter + 投影一致", module: "library", entry: "verify" },
    Spec { id: "library_projection", name: "图书馆 INDEX/ALIAS 实时一致", module: "library", entry: "check_projection" },
    Spec { id: "receipts", name: "馆藏回执折叠到根", module: "receipts", entry: "verify_wrapped" },
    Spec { id: "conformance_report", name: "一致性报告（已提交 == 实时重算）", module: "conformance_report", entry: "verify_committed" },
    Spec { id: "audit", name: "审计件被审对象 digest", module: "audit", entry: "scan" },
    Spec { id: "self_stats", name: "自述数字 == 实算（README/llms 生成区）", module: "repo_stats", entry: "check_strict" },
    Spec { id: "code_metrics", name: "代码规模/复杂度上限（棘轮冻结）", module: "code_metrics", entry: "scan" },
    Spec { id: "key_naming", name: "资产键命名规范（形态 + 声明词表）", module: "key_naming", entry: "scan" },
    Spec { id: "instruction_evidence", name: "规范入口指令实测记录（新鲜 + 退出码 0）", module: "instruction_evidence", entry: "scan" },
    Spec { id: "coupling", name: "模块级耦合（Martin 包度量 / SDP / 环 · 只许收敛）", module: "coupling_metrics", entry: "scan" },
    Spec { id: "perf_budget", name: "性能预算（中位耗时 ≤ 预算 + 记录新鲜）", module: "perf_budget", entry: "scan" },
    Spec { id: "drill_fidelity", name: "演练保真度（执行演练 + 回合级回放 = 100%）", module: "drill_fidelity", entry: "scan" },
    Spec { id: "judgement_coverage", name: "判据接线覆盖（暴露 scan() 的判据必须有消费者或例外登记）", module: "judgement_coverage", entry: "scan" },
    Spec { id: "workflow_policy", name: "工作流供应链策略（actions 钉 40 位 SHA + 显式最小 permissions）", module: "workflow_policy", entry: "scan" },
    Spec { id: "asset_contract", name: "数字资产契约（数据/代码/脚本三面：格式+字段完整性+防篡改+AST 规范+脚本 I/O 对齐）", module: "asset_contract", entry: "scan" },
];

/// 未移植判据的喂入结果（`--results` 的一条）。
#[derive(Clone)]
pub struct Supplied {
    pub issues: Vec<String>,
    pub warns: Vec<String>,
    pub stats: Json,
    /// 覆盖派生出的 status（仅真源的 `error` 路径需要——它也是非空 issues）。
    pub status: Option<String>,
}

impl Default for Supplied {
    fn default() -> Self {
        Self { issues: Vec::new(), warns: Vec::new(), stats: empty_obj(), status: None }
    }
}

/// 一条判据的归一结果。
struct Called {
    status: String,
    issues: Vec<String>,
    warns: Vec<String>,
    stats: Json,
}

fn empty_obj() -> Json {
    Json::Object(Vec::new())
}

fn status_of(issues: &[String], warns: &[String]) -> String {
    if !issues.is_empty() {
        "fail".to_string()
    } else if !warns.is_empty() {
        "warn".to_string()
    } else {
        "pass".to_string()
    }
}

/// 本线**已自主算出**的判据；未移植的返回 `None`（由 `--results` 喂入）。
fn native(spec: &Spec, root: &Path) -> Option<Called> {
    match spec.id {
        "schema" => {
            let (issues, stats) = crate::schema_lint::scan(root);
            Some(Called {
                status: status_of(&issues, &[]),
                issues,
                warns: Vec::new(),
                stats: stats.to_json(),
            })
        }
        // 形态 `list`：真源直接返回 issues 列表
        "doc_markers" => {
            let issues = crate::doc_hygiene::check_markers(root);
            Some(Called {
                status: status_of(&issues, &[]),
                issues,
                warns: Vec::new(),
                stats: empty_obj(),
            })
        }
        "baseline" => {
            let (issues, stats) = baseline::scan(root);
            let stats = match stats {
                Some(s) => Json::Object(vec![
                    ("verify_version".to_string(), Json::Str(s.verify_version)),
                    ("checks".to_string(), Json::Int(s.checks)),
                ]),
                None => empty_obj(),
            };
            Some(Called {
                status: status_of(&issues, &[]),
                issues,
                warns: Vec::new(),
                stats,
            })
        }
        "asset_contract" => {
            let (issues, warns, stats) = crate::asset_contract::scan(root);
            Some(Called {
                status: status_of(&issues, &warns),
                issues,
                warns,
                stats,
            })
        }
        "code_metrics" => {
            let (issues, warns, stats) = crate::code_metrics::scan(root);
            Some(Called {
                status: status_of(&issues, &warns),
                issues,
                warns,
                stats,
            })
        }
        "conformance_report" => {
            let (issues, stats) = crate::conformance::verify_committed(root);
            Some(Called {
                status: status_of(&issues, &[]),
                issues,
                warns: Vec::new(),
                stats,
            })
        }
        "purity" => {
            let (issues, stats) = crate::purity::scan(root);
            Some(Called {
                status: status_of(&issues, &[]),
                issues,
                warns: Vec::new(),
                stats,
            })
        }
        "receipts" => {
            // 真源 `_call` 对这条有**前置在场检查**：文件不在 → 直接记 fail 并给修复指引
            if !root.join(crate::receipts_verify::LIBRARY_RECEIPTS_REL).is_file() {
                Some(Called {
                    status: "fail".to_string(),
                    issues: vec![format!(
                        "缺 {}（修复指引：nf library receipts --write）",
                        crate::receipts_verify::LIBRARY_RECEIPTS_REL
                    )],
                    warns: Vec::new(),
                    stats: crate::pyjson::Json::Object(Vec::new()),
                })
            } else {
                let (issues, stats) = crate::receipts_verify::verify(root);
                Some(Called {
                    status: status_of(&issues, &[]),
                    issues,
                    warns: Vec::new(),
                    stats,
                })
            }
        }
        "drill_fidelity" => {
            let (issues, warns, stats) = crate::drill_fidelity::scan(root);
            Some(Called {
                status: status_of(&issues, &warns),
                issues,
                warns,
                stats,
            })
        }
        "conformance" => {
            let c = crate::conformance_scan::scan(root);
            Some(Called {
                status: status_of(&c.issues, &[]),
                issues: c.issues,
                warns: Vec::new(),
                stats: c.stats,
            })
        }
        "knowledge" => {
            let k = crate::knowledge::scan(root);
            Some(Called {
                status: k.status.map(|s| s.to_string()).unwrap_or_else(|| status_of(&k.issues, &k.warns)),
                issues: k.issues,
                warns: k.warns,
                stats: k.stats,
            })
        }
        "contract" => {
            let m = crate::machine_contract::scan(root);
            Some(Called {
                status: status_of(&m.issues, &m.warns),
                issues: m.issues,
                warns: m.warns,
                stats: m.stats,
            })
        }
        "license" => {
            let l = crate::license_gate::scan(root);
            Some(Called { status: status_of(&l.issues, &[]), issues: l.issues, warns: Vec::new(), stats: l.stats })
        }
        "coupling" => {
            let c = crate::coupling_metrics::scan(root);
            Some(Called {
                status: status_of(&c.issues, &c.warns),
                issues: c.issues,
                warns: c.warns,
                stats: c.stats,
            })
        }
        "judgement_coverage" => {
            let j = crate::judgement_coverage::scan(root);
            Some(Called {
                status: status_of(&j.issues, &j.warns),
                issues: j.issues,
                warns: j.warns,
                stats: j.stats,
            })
        }
        "audit" => {
            let a = crate::audit::scan(root);
            Some(Called {
                status: status_of(&a.issues, &a.warns),
                issues: a.issues,
                warns: a.warns,
                stats: a.stats,
            })
        }
        "workflow_policy" => {
            let w = crate::workflow_policy::scan(root);
            Some(Called {
                status: status_of(&w.issues, &w.warns),
                issues: w.issues,
                warns: w.warns,
                stats: w.stats,
            })
        }
        "rating" => {
            let r = crate::rating_gate::scan(root);
            Some(Called {
                status: status_of(&r.issues, &[]),
                issues: r.issues,
                warns: Vec::new(),
                stats: r.stats,
            })
        }
        "library" => {
            let l = crate::library::verify(root);
            Some(Called {
                status: status_of(&l.issues, &l.warns),
                issues: l.issues,
                warns: l.warns,
                stats: l.stats,
            })
        }
        // 形态 `list`：真源直接返回 issues 列表
        "library_projection" => {
            let issues = crate::library::check_projection(root);
            Some(Called {
                status: status_of(&issues, &[]),
                issues,
                warns: Vec::new(),
                stats: empty_obj(),
            })
        }
        "key_naming" => {
            let k = crate::key_naming::scan(root);
            // 三态：issues 非空 = fail；否则 warns 非空 = warn；都空 = pass
            let status = k.status.map(|s| s.to_string()).unwrap_or_else(|| status_of(&k.issues, &k.warns));
            Some(Called { status, issues: k.issues, warns: k.warns, stats: k.stats })
        }
        "intake" => {
            let k = crate::intake::scan(root);
            Some(Called {
                status: status_of(&k.issues, &[]),
                issues: k.issues,
                warns: Vec::new(),
                stats: k.stats,
            })
        }
        "payload" => {
            let (issues, stats) = crate::payload_registry::scan(root);
            Some(Called {
                status: status_of(&issues, &[]),
                issues,
                warns: Vec::new(),
                stats: stats.map(|s| s.to_json()).unwrap_or_else(empty_obj),
            })
        }
        "assets_ledger" => {
            let (issues, stats) = crate::asset_ledger_projection::verify(root);
            Some(Called {
                status: status_of(&issues, &[]),
                issues,
                warns: Vec::new(),
                stats: stats.unwrap_or_else(empty_obj),
            })
        }
        "instruction" => {
            let (issues, stats) = crate::instruction_step_audit::scan(root);
            Some(Called {
                status: status_of(&issues, &[]),
                issues,
                warns: Vec::new(),
                stats: stats.map(|s| s.to_json()).unwrap_or_else(empty_obj),
            })
        }
        // 真源 `check_strict` 是 `repo_stats.check` 的别名（模块里并无该属性）
        "self_stats" => {
            let (issues, stats) = crate::stats::check(root);
            Some(Called {
                status: status_of(&issues, &[]),
                issues,
                warns: Vec::new(),
                stats: stats.to_json(),
            })
        }
        _ => None,
    }
}

/// 真源 `_call`：先本线自算，未移植则取喂入值。
fn call(spec: &Spec, root: &Path, supplied: &HashMap<String, Supplied>) -> Called {
    if let Some(c) = native(spec, root) {
        return c;
    }
    match supplied.get(spec.id) {
        Some(s) => Called {
            status: s.status.clone().unwrap_or_else(|| status_of(&s.issues, &s.warns)),
            issues: s.issues.clone(),
            warns: s.warns.clone(),
            stats: s.stats.clone(),
        },
        None => Called {
            status: "error".to_string(),
            issues: vec![format!(
                "{}.{} 未移植且未喂入结果（修复指引：本线尚未移植该扫描器；用 --results 提供它的 issues/warns/stats）",
                spec.module, spec.entry
            )],
            warns: Vec::new(),
            stats: empty_obj(),
        },
    }
}

/// 真源 `_declared`：声明面（真源 = `quality_baseline`）。
fn declared(root: &Path) -> Json {
    let (ec, ep) = baseline::constants(root);
    let (_, stats) = baseline::scan(root);
    let vv = stats.map(|s| s.verify_version);
    Json::Object(vec![
        (
            "expected_checks".to_string(),
            ec.map(Json::Int).unwrap_or(Json::Null),
        ),
        (
            "expected_pass".to_string(),
            ep.map(Json::Int).unwrap_or(Json::Null),
        ),
        (
            "verify_version".to_string(),
            vv.map(Json::Str).unwrap_or(Json::Null),
        ),
    ])
}

/// 真源 `build`：跑全部判据 → 报告 dict（含声明/实测并排 + 稳定 digest）。
pub fn build(root: &Path, supplied: &HashMap<String, Supplied>) -> Json {
    let mut items: Vec<Json> = Vec::new();
    let mut counts: HashMap<&str, i64> = HashMap::new();
    for spec in SPECS.iter() {
        let c = call(spec, root, supplied);
        *counts.entry(match c.status.as_str() {
            "pass" => "pass",
            "fail" => "fail",
            "warn" => "warn",
            _ => "error",
        }).or_insert(0) += 1;
        let sample: Vec<Json> = c
            .issues
            .iter()
            .take(3)
            .map(|x| Json::Str(x.chars().take(200).collect()))
            .collect();
        items.push(Json::Object(vec![
            ("id".to_string(), Json::Str(spec.id.to_string())),
            ("name".to_string(), Json::Str(spec.name.to_string())),
            ("source".to_string(), Json::Str(spec.source())),
            ("status".to_string(), Json::Str(c.status)),
            ("issues".to_string(), Json::Int(c.issues.len() as i64)),
            ("warns".to_string(), Json::Int(c.warns.len() as i64)),
            ("stats".to_string(), c.stats),
            ("sample".to_string(), Json::Array(sample)),
        ]));
    }
    let summary = Json::Object(
        ["pass", "fail", "warn", "error"]
            .iter()
            .map(|k| ((*k).to_string(), Json::Int(*counts.get(k).unwrap_or(&0))))
            .collect(),
    );
    let mut body = Json::Object(vec![
        ("schema".to_string(), Json::Str(SCHEMA.to_string())),
        ("items".to_string(), Json::Array(items)),
        ("summary".to_string(), summary),
        ("declared".to_string(), declared(root)),
    ]);
    let digest_src = body.dumps_default();
    let digest = merkle::hex(&merkle::sha256(digest_src.as_bytes()));
    if let Json::Object(pairs) = &mut body {
        pairs.push(("root_digest".to_string(), Json::Str(digest)));
    }
    body
}

/// 真源 `render`：`json.dumps(..., indent=2, sort_keys=True) + "\n"`（LF）。
pub fn render(report: &Json) -> Vec<u8> {
    report.dumps_file().into_bytes()
}

/// 真源 `check`：提交件 == 实时重算 → `(issues, live)`。
pub fn check(root: &Path, supplied: &HashMap<String, Supplied>) -> (Vec<String>, Json) {
    let live = build(root, supplied);
    let p = root.join(REPORT_REL);
    if !p.is_file() {
        return (
            vec![format!(
                "缺 {}（修复指引：python scripts/verify_report.py --write）",
                REPORT_REL
            )],
            live,
        );
    }
    let recorded = jsonread::read_file(root, REPORT_REL)
        .unwrap_or_else(|| Json::Object(Vec::new()));
    let mut issues: Vec<String> = Vec::new();
    if py_str(get(&recorded, "root_digest")) != py_str(get(&live, "root_digest")) {
        let a = py_str(get(&recorded, "root_digest"));
        let b = py_str(get(&live, "root_digest"));
        issues.push(format!(
            "{} 与实时重算不一致（记录={} 实测={}）（修复指引：重跑 python scripts/verify_report.py --write）",
            REPORT_REL,
            trunc(&a, 12),
            trunc(&b, 12)
        ));
    }
    if plain_str_opt(get(&recorded, "schema")) != SCHEMA {
        issues.push(format!(
            "{} schema 不匹配（期望 {}）（修复指引：重跑 --write）",
            REPORT_REL, SCHEMA
        ));
    }
    (issues, live)
}

fn trunc(s: &str, n: usize) -> String {
    s.chars().take(n).collect()
}

/// 真源 `summary_line`。
pub fn summary_line(report: &Json) -> String {
    let s = get(report, "summary");
    let d = get(report, "declared");
    let g = |o: Option<&Json>, k: &str| -> String {
        match o.and_then(|x| get(x, k)) {
            Some(Json::Null) | None => "None".to_string(),
            Some(v) => crate::pyval::plain_str(v),
        }
    };
    format!(
        "判据 {} 条：PASS {} · FAIL {} · WARN {} · ERROR {}；声明 check1-{} / PASS={} · verify {}",
        crate::pyval::arr_items(get(report, "items")).len(),
        g(s, "pass"),
        g(s, "fail"),
        g(s, "warn"),
        g(s, "error"),
        g(d, "expected_checks"),
        g(d, "expected_pass"),
        g(d, "verify_version")
    )
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn spec_table_matches_the_truth_source_shape() {
        assert_eq!(SPECS.len(), 28);
        assert_eq!(SPECS[0].id, "purity");
        assert_eq!(SPECS[1].source(), "schema_lint.scan");
        assert_eq!(SPECS[27].id, "asset_contract");
    }

    #[test]
    fn unported_spec_without_supplied_result_is_reported_as_error() {
        let spec = Spec { id: "nope", name: "x", module: "m", entry: "scan" };
        let got = call(&spec, Path::new("."), &HashMap::new());
        assert_eq!(got.status, "error");
        assert!(got.issues[0].contains("未移植且未喂入结果"), "{:?}", got.issues);
    }

    #[test]
    fn supplied_warns_alone_yield_warn_status() {
        let mut m = HashMap::new();
        m.insert(
            "nope".to_string(),
            Supplied {
                issues: Vec::new(),
                warns: vec!["w".to_string()],
                stats: empty_obj(),
                status: None,
            },
        );
        let spec = Spec { id: "nope", name: "x", module: "m", entry: "scan" };
        assert_eq!(call(&spec, Path::new("."), &m).status, "warn");
    }

    #[test]
    fn sample_truncates_at_200_characters() {
        let long = "字".repeat(250);
        let sample: Vec<Json> = vec![Json::Str(long.chars().take(200).collect())];
        let Json::Str(s) = &sample[0] else { panic!() };
        assert_eq!(s.chars().count(), 200);
    }
}
