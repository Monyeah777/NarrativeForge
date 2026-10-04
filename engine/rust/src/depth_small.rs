//! 三个**小**深度子扫描器（各 < 80 行，合置一件以免文件碎片化）：
//! `payload_consumer` / `tool_face` / `world_slots`。
//!
//! 三者都读模块文档的 `machine_contract` 机读块或协议件，口径与真源逐字对齐。

use crate::miniyaml;
use crate::pyjson::Json;
use crate::pyval;
use std::path::Path;

/// 真源 `conformance_scan._module_docs` 的路径面。
///
/// 返回**仓库相对**路径（`/` 分隔）。真源给绝对路径、再 `relpath` 归一；本线直接以
/// `glob::expand` 取相对路径，二者命中**同一批件**，排序亦同（同一 root 前缀下的字典序等价）。
pub fn module_docs(root: &Path) -> Vec<String> {
    let mut out: Vec<String> = Vec::new();
    for pat in ["04_模块库/**/*.md", "community/*/modules/*.md"] {
        out.extend(crate::glob::expand(root, pat));
    }
    out.sort();
    out.dedup();
    out
}

fn read(root: &Path, rel: &str) -> String {
    std::fs::read(root.join(rel))
        .map(|b| String::from_utf8_lossy(&b).into_owned())
        .unwrap_or_default()
}

fn obj_get<'a>(v: &'a Json, k: &str) -> Option<&'a Json> {
    match v {
        Json::Object(o) => o.iter().find(|(kk, _)| kk == k).map(|(_, vv)| vv),
        _ => None,
    }
}

/// 取某份模块文档的 `machine_contract` 块（不存在 → `None`）。
fn machine_contract(root: &Path, rel: &str) -> Option<Json> {
    let text = read(root, rel);
    let parsed = miniyaml::fence_yaml(&text, "machine_contract")?;
    obj_get(&parsed, "machine_contract").cloned()
}

// ---------------------------------------------------------------- payload_consumer

/// 真源 `payload_consumer.scan`：**只报告不设闸**（issues 恒空，消费统计进 stats）。
pub fn payload_consumer_scan(root: &Path) -> (Vec<String>, Json) {
    let reg_rel = "protocol/event_registry.json";
    if !root.join(reg_rel).is_file() {
        return (
            vec![format!(
                "缺 {}（修复指引：在 NF 仓库根运行本扫描，或先补齐该协议件——消费核对要以它当真源）",
                reg_rel
            )],
            Json::Object(vec![]),
        );
    }
    let reg = crate::jsonread::read_file(root, reg_rel).unwrap_or(Json::Object(vec![]));
    // event → [订阅该事件的模块 id]（**插入序无关**：最后每项都 sorted+set）
    let mut subs: Vec<(String, Vec<String>)> = Vec::new();
    for doc in module_docs(root) {
        let Some(mc) = machine_contract(root, &doc) else { continue };
        let mid = match obj_get(&mc, "id") {
            Some(Json::Str(s)) => s.clone(),
            _ => String::new(),
        };
        let Some(events) = obj_get(&mc, "events") else { continue };
        let Some(Json::Array(list)) = obj_get(events, "subscribe") else { continue };
        for e in list {
            let key = pyval::plain_str(e);
            match subs.iter_mut().find(|(k, _)| *k == key) {
                Some((_, v)) => v.push(mid.clone()),
                None => subs.push((key, vec![mid.clone()])),
            }
        }
    }
    let mut consumers: Vec<(String, Json)> = Vec::new();
    let mut declared = 0i64;
    if let Some(Json::Object(events)) = obj_get(&reg, "events") {
        for (ev, spec) in events {
            if pyval::py_truthy(&obj_get(spec, "fields").cloned().unwrap_or(Json::Null)) {
                declared += 1;
                let mut list: Vec<String> =
                    subs.iter().find(|(k, _)| k == ev).map(|(_, v)| v.clone()).unwrap_or_default();
                list.sort();
                list.dedup();
                consumers.push((
                    ev.clone(),
                    Json::Array(list.into_iter().map(Json::Str).collect()),
                ));
            }
        }
    }
    let consumed = consumers
        .iter()
        .filter(|(_, v)| matches!(v, Json::Array(a) if !a.is_empty()))
        .count() as i64;
    (
        Vec::new(),
        Json::Object(vec![
            ("events_declared".to_string(), Json::Int(declared)),
            ("events_consumed".to_string(), Json::Int(consumed)),
            ("consumer_map".to_string(), Json::Object(consumers)),
        ]),
    )
}

// ---------------------------------------------------------------- tool_face

/// 真源 `tool_face.validate_entry`。
pub fn validate_entry(entry: &Json) -> Vec<String> {
    let mut issues: Vec<String> = Vec::new();
    let purpose_ok = matches!(obj_get(entry, "purpose"), Some(Json::Str(s)) if !s.trim().is_empty());
    if !purpose_ok {
        issues.push("tool_face 条目缺 purpose".to_string());
    }
    let guidance = obj_get(entry, "guidance");
    let guidance_ok = matches!(guidance, Some(Json::Object(o)) if !o.is_empty());
    if !guidance_ok {
        issues.push("tool_face 条目缺 guidance（指导段是验收硬核）".to_string());
    }
    if let Some(Json::Array(cands)) = obj_get(entry, "candidates") {
        for c in cands {
            if !matches!(c, Json::Object(_)) {
                issues.push("candidate 非对象".to_string());
                continue;
            }
            let repo = match obj_get(c, "repo") {
                Some(Json::Str(s)) => s.clone(),
                Some(Json::Null) | None => String::new(),
                Some(v) => pyval::plain_str(v),
            };
            if !repo.starts_with("http://") && !repo.starts_with("https://") {
                issues.push("candidate 缺合法 https 链接".to_string());
            }
            let lic = match obj_get(c, "license") {
                Some(Json::Str(s)) => s.clone(),
                Some(Json::Null) | None => String::new(),
                Some(v) => pyval::plain_str(v),
            };
            if lic.trim().is_empty() {
                issues.push("candidate 缺 license（有链接必须有出处）".to_string());
            }
        }
    }
    issues
}

/// 真源 `tool_face.scan`。
pub fn tool_face_scan(root: &Path) -> (Vec<String>, Json) {
    let mut issues: Vec<String> = Vec::new();
    let mut modules = 0i64;
    let mut entries = 0i64;
    let mut candidates = 0i64;
    let mut faces: Vec<Json> = Vec::new();
    for rel in module_docs(root) {
        let Some(mc) = machine_contract(root, &rel) else { continue };
        let Some(face) = obj_get(&mc, "tool_face") else { continue };
        let Json::Array(items) = face else {
            issues.push(format!("{}: tool_face 非空列表", rel));
            continue;
        };
        if items.is_empty() {
            issues.push(format!("{}: tool_face 非空列表", rel));
            continue;
        }
        modules += 1;
        let mid = match obj_get(&mc, "id") {
            Some(Json::Str(s)) if !s.is_empty() => s.clone(),
            _ => rel.clone(),
        };
        faces.push(Json::Object(vec![
            ("module".to_string(), Json::Str(mid)),
            ("source".to_string(), Json::Str(rel.clone())),
            ("entries".to_string(), Json::Int(items.len() as i64)),
        ]));
        for e in items {
            entries += 1;
            issues.extend(validate_entry(e));
            if let Some(Json::Array(cs)) = obj_get(e, "candidates") {
                candidates += cs.len() as i64;
            }
        }
    }
    (
        issues,
        Json::Object(vec![
            ("modules".to_string(), Json::Int(modules)),
            ("entries".to_string(), Json::Int(entries)),
            ("candidates".to_string(), Json::Int(candidates)),
            ("faces".to_string(), Json::Array(faces)),
        ]),
    )
}

// ---------------------------------------------------------------- world_slots

const SLOT_KINDS: [&str; 6] =
    ["string", "integer", "number", "boolean", "array", "object"];
const ITEM_KINDS: [&str; 4] = ["string", "integer", "number", "boolean"];

/// 真源 `world_slots.validate_registry`。
pub fn validate_registry(data: &Json, label: &str) -> Vec<String> {
    let mut issues: Vec<String> = Vec::new();
    let Json::Object(_) = data else {
        return vec![format!("{}: 顶层非对象", label)];
    };
    if !matches!(obj_get(data, "schema_version"), Some(Json::Str(s)) if s == "1") {
        issues.push(format!("{}.schema_version: 应为 \"1\"", label));
    }
    let slots = obj_get(data, "slots");
    let ok_slots = matches!(slots, Some(Json::Object(o)) if !o.is_empty());
    if !ok_slots {
        issues.push(format!("{}.slots: 非空对象", label));
        return issues;
    }
    let Some(Json::Object(slots)) = slots else { return issues };
    for (path, spec) in slots {
        let at = format!("{}.slots.{}", label, pyval::py_repr(&Json::Str(path.clone())));
        if path.trim().is_empty() {
            issues.push(format!("{}: 槽位路径非空字符串", at));
        }
        let Json::Object(_) = spec else {
            issues.push(format!("{}: 槽位定义非对象", at));
            continue;
        };
        let kind = obj_get(spec, "kind").cloned().unwrap_or(Json::Null);
        let owner = obj_get(spec, "owner").cloned().unwrap_or(Json::Null);
        let item_kind = obj_get(spec, "item_kind").cloned().unwrap_or(Json::Null);
        let kind_str = match &kind {
            Json::Str(s) => s.clone(),
            _ => String::new(),
        };
        if !SLOT_KINDS.contains(&kind_str.as_str()) {
            issues.push(format!("{}.kind: 非法类型 {}", at, pyval::py_repr(&kind)));
        }
        let owner_ok = matches!(&owner, Json::Str(s) if !s.trim().is_empty());
        if !owner_ok {
            issues.push(format!("{}.owner: 非空字符串", at));
        }
        if kind_str == "array" {
            if !matches!(item_kind, Json::Null) {
                let ik = match &item_kind {
                    Json::Str(s) => s.clone(),
                    _ => String::new(),
                };
                if !ITEM_KINDS.contains(&ik.as_str()) {
                    issues.push(format!(
                        "{}.item_kind: 非法元素类型 {}",
                        at,
                        pyval::py_repr(&item_kind)
                    ));
                }
            }
        } else if !matches!(item_kind, Json::Null) {
            issues.push(format!("{}.item_kind: 仅 kind=array 可用", at));
        }
    }
    issues
}

/// 真源 `world_slots.scan`。
pub fn world_slots_scan(root: &Path) -> (Vec<String>, Json) {
    let rel = "protocol/world_slots.json";
    if !root.join(rel).is_file() {
        return (vec!["protocol/world_slots.json 缺失".to_string()], json_slots(0, 0));
    }
    let text = read(root, rel);
    let data = match crate::asset_contract::strict_json(&text) {
        Ok(v) => v,
        Err(e) => {
            return (
                vec![format!("protocol/world_slots.json 解析失败：{}", e)],
                json_slots(0, 0),
            )
        }
    };
    let mut issues = validate_registry(&data, "world_slots");
    let m00 = "04_模块库/通用类/M00_数据结构.md";
    if root.join(m00).is_file() {
        let m00_text = read(root, m00);
        if let Some(Json::Object(slots)) = obj_get(&data, "slots") {
            for (slot, _) in slots.iter() {
                for part in slot.split('.') {
                    if !part.is_empty() && !m00_text.contains(part) {
                        issues.push(format!(
                            "world_slots slot 路径段未在 M00 文档锚定：{}（{}）",
                            pyval::py_repr(&Json::Str(part.to_string())),
                            slot
                        ));
                    }
                }
            }
        }
    } else {
        issues.push("04_模块库/通用类/M00_数据结构.md 缺失".to_string());
    }
    let (n, arrays) = match obj_get(&data, "slots") {
        Some(Json::Object(o)) => (
            o.len() as i64,
            o.iter()
                .filter(|(_, v)| matches!(obj_get(v, "kind"), Some(Json::Str(s)) if s == "array"))
                .count() as i64,
        ),
        _ => (0, 0),
    };
    (issues, json_slots(n, arrays))
}

fn json_slots(n: i64, arrays: i64) -> Json {
    Json::Object(vec![
        ("slots".to_string(), Json::Int(n)),
        ("arrays".to_string(), Json::Int(arrays)),
    ])
}

#[cfg(test)]
mod tests {
    use super::*;
    // >>> GENERATED by tools/gen_depth_small_cases.py（勿手改；重跑生成器覆盖本段）
    /// ===== 三个小深度子扫描器（真实语料，期望值由生成器从真源取）=====
    #[test]
    fn depth_small_matches_truth_source() {
        let root = crate::testutil::repo_root();
        let cases: &[(&str, &[&str], &str)] = &[
        (
            r#"payload_consumer_scan"#,
            &[],
            r#"{"consumer_map": {"a01_report_conflict": ["大语言模型:M01"], "a01_report_ready": ["大语言模型:M01"], "a01_spec_conflict": ["大语言模型:M02"], "a01_spec_ready": ["大语言模型:M02"], "a02_report_conflict": ["多模态大模型:M01"], "a02_report_ready": ["多模态大模型:M01"], "a02_spec_conflict": ["多模态大模型:M02"], "a02_spec_ready": ["多模态大模型:M02"], "a03_report_conflict": ["视觉模型:M01"], "a03_report_ready": ["视觉模型:M01"], "a03_spec_conflict": ["视觉模型:M02"], "a03_spec_ready": ["视觉模型:M02"], "a04_report_conflict": ["语音识别与合成:M01"], "a04_report_ready": ["语音识别与合成:M01"], "a04_spec_conflict": ["语音识别与合成:M02"], "a04_spec_ready": ["语音识别与合成:M02"], "a05_report_conflict": ["音频与音乐生成:M01"], "a05_report_ready": ["音频与音乐生成:M01"], "a05_spec_conflict": ["音频与音乐生成:M02"], "a05_spec_ready": ["音频与音乐生成:M02"], "a06_report_conflict": ["视频生成与理解:M01"], "a06_report_ready": ["视频生成与理解:M01"], "a06_spec_conflict": ["视频生成与理解:M02"], "a06_spec_ready": ["视频生成与理解:M02"], "a07_report_conflict": ["图像生成与编辑:M01"], "a07_report_ready": ["图像生成与编辑:M01"], "a07_spec_conflict": ["图像生成与编辑:M02"], "a07_spec_ready": ["图像生成与编辑:M02"], "a08_report_conflict": ["三维与世界模型:M01"], "a08_report_ready": ["三维与世界模型:M01"], "a08_spec_conflict": ["三维与世界模型:M02"], "a08_spec_ready": ["三维与世界模型:M02"], "a09_report_conflict": ["代码大模型:M01"], "a09_report_ready": ["代码大模型:M01"], "a09_spec_conflict": ["代码大模型:M02"], "a09_spec_ready": ["代码大模型:M02"], "a10_report_conflict": ["数学与形式化推理:M01"], "a10_report_ready": ["数学与形式化推理:M01"], "a10_spec_conflict": ["数学与形式化推理:M02"], "a10_spec_ready": ["数学与形式化推理:M02"], "a11_report_conflict": ["嵌入与检索表示:M01"], "a11_report_ready": ["嵌入与检索表示:M01"], "a11_spec_conflict": ["嵌入与检索表示:M02"], "a11_spec_ready": ["嵌入与检索表示:M02"], "a12_report_conflict": ["强化学习与决策:M01"], "a12_report_ready": ["强化学习与决策:M01"], "a12_spec_conflict": ["强化学习与决策:M02"], "a12_spec_ready": ["强化学习与决策:M02"], "a13_report_conflict": ["具身智能与机器人:M01"], "a13_report_ready": ["具身智能与机器人:M01"], "a13_spec_conflict": ["具身智能与机器人:M02"], "a13_spec_ready": ["具身智能与机器人:M02"], "a14_report_conflict": ["端侧与边缘小模型:M01"], "a14_report_ready": ["端侧与边缘小模型:M01"], "a14_spec_conflict": ["端侧与边缘小模型:M02"], "a14_spec_ready": ["端侧与边缘小模型:M02"], "b01_report_conflict": ["文本生成与创作:M01"], "b01_report_ready": ["文本生成与创作:M01"], "b01_spec_conflict": ["文本生成与创作:M02"], "b01_spec_ready": ["文本生成与创作:M02"], "b02_report_conflict": ["摘要与信息压缩:M01"], "b02_report_ready": ["摘要与信息压缩:M01"], "b02_spec_conflict": ["摘要与信息压缩:M02"], "b02_spec_ready": ["摘要与信息压缩:M02"], "b03_report_conflict": ["机器翻译与本地化:M01"], "b03_report_ready": ["机器翻译与本地化:M01"], "b03_spec_conflict": ["机器翻译与本地化:M02"], "b03_spec_ready": ["机器翻译与本地化:M02"], "b04_report_conflict": ["分类与情感分析:M01"], "b04_report_ready": ["分类与情感分析:M01"], "b04_spec_conflict": ["分类与情感分析:M02"], "b04_spec_ready": ["分类与情感分析:M02"], "b05_report_conflict": ["信息抽取与结构化:M01"], "b05_report_ready": ["信息抽取与结构化:M01"], "b05_spec_conflict": ["信息抽取与结构化:M02"], "b05_spec_ready": ["信息抽取与结构化:M02"], "b06_report_conflict": ["知识问答与检索增强:M01"], "b06_report_ready": ["知识问答与检索增强:M01"], "b06_spec_conflict": ["知识问答与检索增强:M02"], "b06_spec_ready": ["知识问答与检索增强:M02"], "b07_report_conflict": ["多轮对话与角色扮演:M01"], "b07_report_ready": ["多轮对话与角色扮演:M01"], "b07_spec_conflict": ["多轮对话与角色扮演:M02"], "b07_spec_ready": ["多轮对话与角色扮演:M02"], "b08_report_conflict": ["代码生成与补全:M01"], "b08_report_ready": ["代码生成与补全:M01"], "b08_spec_conflict": ["代码生成与补全:M02"], "b08_spec_ready": ["代码生成与补全:M02"], "b09_report_conflict": ["代码审查与缺陷检测:M01"], "b09_report_ready": ["代码审查与缺陷检测:M01"], "b09_spec_conflict": ["代码审查与缺陷检测:M02"], "b09_spec_ready": ["代码审查与缺陷检测:M02"], "b10_report_conflict": ["测试与用例生成:M01"], "b10_report_ready": ["测试与用例生成:M01"], "b10_spec_conflict": ["测试与用例生成:M02"], "b10_spec_ready": ["测试与用例生成:M02"], "b11_report_conflict": ["数据分析与表格理解:M01"], "b11_report_ready": ["数据分析与表格理解:M01"], "b11_spec_conflict": ["数据分析与表格理解:M02"], "b11_spec_ready": ["数据分析与表格理解:M02"], "b12_report_conflict": ["文档解析与版面理解:M01"], "b12_report_ready": ["文档解析与版面理解:M01"], "b12_spec_conflict": ["文档解析与版面理解:M02"], "b12_spec_ready": ["文档解析与版面理解:M02"], "b13_report_conflict": ["语音转写与会议记录:M01"], "b13_report_ready": ["语音转写与会议记录:M01"], "b13_spec_conflict": ["语音转写与会议记录:M02"], "b13_spec_ready": ["语音转写与会议记录:M02"], "b14_report_conflict": ["语音合成与配音:M01"], "b14_report_ready": ["语音合成与配音:M01"], "b14_spec_conflict": ["语音合成与配音:M02"], "b14_spec_ready": ["语音合成与配音:M02"], "b15_report_conflict": ["图像生成与视觉设计:M01"], "b15_report_ready": ["图像生成与视觉设计:M01"], "b15_spec_conflict": ["图像生成与视觉设计:M02"], "b15_spec_ready": ["图像生成与视觉设计:M02"], "b16_report_conflict": ["视频生成与自动剪辑:M01"], "b16_report_ready": ["视频生成与自动剪辑:M01"], "b16_spec_conflict": ["视频生成与自动剪辑:M02"], "b16_spec_ready": ["视频生成与自动剪辑:M02"], "b17_report_conflict": ["推荐排序与广告:M01"], "b17_report_ready": ["推荐排序与广告:M01"], "b17_spec_conflict": ["推荐排序与广告:M02"], "b17_spec_ready": ["推荐排序与广告:M02"], "b18_report_conflict": ["预测异常与风险:M01"], "b18_report_ready": ["预测异常与风险:M01"], "b18_spec_conflict": ["预测异常与风险:M02"], "b18_spec_ready": ["预测异常与风险:M02"], "backtest_spec_conflict": [], "backtest_spec_ready": [], "beat_tick": ["M95"], "c01_report_conflict": ["数据采集与清洗:M01"], "c01_report_ready": ["数据采集与清洗:M01"], "c01_spec_conflict": ["数据采集与清洗:M02"], "c01_spec_ready": ["数据采集与清洗:M02"], "c02_report_conflict": ["数据标注与标注质量:M01"], "c02_report_ready": ["数据标注与标注质量:M01"], "c02_spec_conflict": ["数据标注与标注质量:M02"], "c02_spec_ready": ["数据标注与标注质量:M02"], "c03_report_conflict": ["合成数据生成:M01"], "c03_report_ready": ["合成数据生成:M01"], "c03_spec_conflict": ["合成数据生成:M02"], "c03_spec_ready": ["合成数据生成:M02"], "c04_report_conflict": ["预训练与继续预训练:M01"], "c04_report_ready": ["预训练与继续预训练:M01"], "c04_spec_conflict": ["预训练与继续预训练:M02"], "c04_spec_ready": ["预训练与继续预训练:M02"], "c05_report_conflict": ["监督微调:M01"], "c05_report_ready": ["监督微调:M01"], "c05_spec_conflict": ["监督微调:M02"], "c05_spec_ready": ["监督微调:M02"], "c06_report_conflict": ["参数高效微调:M01"], "c06_report_ready": ["参数高效微调:M01"], "c06_spec_conflict": ["参数高效微调:M02"], "c06_spec_ready": ["参数高效微调:M02"], "c07_report_conflict": ["对齐与偏好优化:M01"], "c07_report_ready": ["对齐与偏好优化:M01"], "c07_spec_conflict": ["对齐与偏好优化:M02"], "c07_spec_ready": ["对齐与偏好优化:M02"], "c08_report_conflict": ["评测基准与排行榜:M01"], "c08_report_ready": ["评测基准与排行榜:M01"], "c08_spec_conflict": ["评测基准与排行榜:M02"], "c08_spec_ready": ["评测基准与排行榜:M02"], "c09_report_conflict": ["红队越狱与安全测试:M01"], "c09_report_ready": ["红队越狱与安全测试:M01"], "c09_spec_conflict": ["红队越狱与安全测试:M02"], "c09_spec_ready": ["红队越狱与安全测试:M02"], "c10_report_conflict": ["推理优化与加速:M01"], "c10_report_ready": ["推理优化与加速:M01"], "c10_spec_conflict": ["推理优化与加速:M02"], "c10_spec_ready": ["推理优化与加速:M02"], "c11_report_conflict": ["推理服务与部署:M01"], "c11_report_ready": ["推理服务与部署:M01"], "c11_spec_conflict": ["推理服务与部署:M02"], "c11_spec_ready": ["推理服务与部署:M02"], "c12_report_conflict": ["上下文工程与长上下文:M01"], "c12_report_ready": ["上下文工程与长上下文:M01"], "c12_spec_conflict": ["上下文工程与长上下文:M02"], "c12_spec_ready": ["上下文工程与长上下文:M02"], "c13_report_conflict": ["提示工程与提示模板:M01"], "c13_report_ready": ["提示工程与提示模板:M01"], "c13_spec_conflict": ["提示工程与提示模板:M02"], "c13_spec_ready": ["提示工程与提示模板:M02"], "c14_report_conflict": ["记忆体与个性化:M01"], "c14_report_ready": ["记忆体与个性化:M01"], "c14_spec_conflict": ["记忆体与个性化:M02"], "c14_spec_ready": ["记忆体与个性化:M02"], "c15_report_conflict": ["向量库与检索管线:M01"], "c15_report_ready": ["向量库与检索管线:M01"], "c15_spec_conflict": ["向量库与检索管线:M02"], "c15_spec_ready": ["向量库与检索管线:M02"], "c16_report_conflict": ["智能体框架与工具调用:M01"], "c16_report_ready": ["智能体框架与工具调用:M01"], "c16_spec_conflict": ["智能体框架与工具调用:M02"], "c16_spec_ready": ["智能体框架与工具调用:M02"], "c17_report_conflict": ["多智能体协同:M01"], "c17_report_ready": ["多智能体协同:M01"], "c17_spec_conflict": ["多智能体协同:M02"], "c17_spec_ready": ["多智能体协同:M02"], "c18_report_conflict": ["可观测性成本与可靠性:M01"], "c18_report_ready": ["可观测性成本与可靠性:M01"], "c18_spec_conflict": ["可观测性成本与可靠性:M02"], "c18_spec_ready": ["可观测性成本与可靠性:M02"], "campus_anonymous_gift": [], "campus_gift_intent": [], "chaos_event": ["M06", "M10", "事件:M22"], "combat_result": ["M01", "M03", "M06", "M10"], "concept_closure_ready": ["AI系统:M26"], "confession_event": ["M55", "M91"], "d01_report_conflict": ["AI医疗健康:M01"], "d01_report_ready": ["AI医疗健康:M01"], "d01_spec_conflict": ["AI医疗健康:M02"], "d01_spec_ready": ["AI医疗健康:M02"], "d02_report_conflict": ["AI制药与生物:M01"], "d02_report_ready": ["AI制药与生物:M01"], "d02_spec_conflict": ["AI制药与生物:M02"], "d02_spec_ready": ["AI制药与生物:M02"], "d03_report_conflict": ["AI法律与合规:M01"], "d03_report_ready": ["AI法律与合规:M01"], "d03_spec_conflict": ["AI法律与合规:M02"], "d03_spec_ready": ["AI法律与合规:M02"], "d04_report_conflict": ["AI金融投研与风控:M01"], "d04_report_ready": ["AI金融投研与风控:M01"], "d04_spec_conflict": ["AI金融投研与风控:M02"], "d04_spec_ready": ["AI金融投研与风控:M02"], "d05_report_conflict": ["AI保险:M01"], "d05_report_ready": ["AI保险:M01"], "d05_spec_conflict": ["AI保险:M02"], "d05_spec_ready": ["AI保险:M02"], "d06_report_conflict": ["AI教育:M01"], "d06_report_ready": ["AI教育:M01"], "d06_spec_conflict": ["AI教育:M02"], "d06_spec_ready": ["AI教育:M02"], "d07_report_conflict": ["AI政务与公共事务:M01"], "d07_report_ready": ["AI政务与公共事务:M01"], "d07_spec_conflict": ["AI政务与公共事务:M02"], "d07_spec_ready": ["AI政务与公共事务:M02"], "d08_report_conflict": ["AI制造业:M01"], "d08_report_ready": ["AI制造业:M01"], "d08_spec_conflict": ["AI制造业:M02"], "d08_spec_ready": ["AI制造业:M02"], "d09_report_conflict": ["AI能源与电力:M01"], "d09_report_ready": ["AI能源与电力:M01"], "d09_spec_conflict": ["AI能源与电力:M02"], "d09_spec_ready": ["AI能源与电力:M02"], "d10_report_conflict": ["AI农业:M01"], "d10_report_ready": ["AI农业:M01"], "d10_spec_conflict": ["AI农业:M02"], "d10_spec_ready": ["AI农业:M02"], "d11_report_conflict": ["零售与电商:M01"], "d11_report_ready": ["零售与电商:M01"], "d11_spec_conflict": ["零售与电商:M02"], "d11_spec_ready": ["零售与电商:M02"], "d12_report_conflict": ["物流与供应链:M01"], "d12_report_ready": ["物流与供应链:M01"], "d12_spec_conflict": ["物流与供应链:M02"], "d12_spec_ready": ["物流与供应链:M02"], "d13_report_conflict": ["交通与出行:M01"], "d13_report_ready": ["交通与出行:M01"], "d13_spec_conflict": ["交通与出行:M02"], "d13_spec_ready": ["交通与出行:M02"], "d14_report_conflict": ["AI人力资源与招聘:M01"], "d14_report_ready": ["AI人力资源与招聘:M01"], "d14_spec_conflict": ["AI人力资源与招聘:M02"], "d14_spec_ready": ["AI人力资源与招聘:M02"], "d15_report_conflict": ["建筑与房地产:M01"], "d15_report_ready": ["建筑与房地产:M01"], "d15_spec_conflict": ["建筑与房地产:M02"], "d15_spec_ready": ["建筑与房地产:M02"], "d16_report_conflict": ["AI食品与餐饮:M01"], "d16_report_ready": ["AI食品与餐饮:M01"], "d16_spec_conflict": ["AI食品与餐饮:M02"], "d16_spec_ready": ["AI食品与餐饮:M02"], "d17_report_conflict": ["传媒与新闻:M01"], "d17_report_ready": ["传媒与新闻:M01"], "d17_spec_conflict": ["传媒与新闻:M02"], "d17_spec_ready": ["传媒与新闻:M02"], "d18_report_conflict": ["游戏与互动娱乐:M01"], "d18_report_ready": ["游戏与互动娱乐:M01"], "d18_spec_conflict": ["游戏与互动娱乐:M02"], "d18_spec_ready": ["游戏与互动娱乐:M02"], "d19_report_conflict": ["文旅与酒店:M01"], "d19_report_ready": ["文旅与酒店:M01"], "d19_spec_conflict": ["文旅与酒店:M02"], "d19_spec_ready": ["文旅与酒店:M02"], "d20_report_conflict": ["科研与实验:M01"], "d20_report_ready": ["科研与实验:M01"], "d20_spec_conflict": ["科研与实验:M02"], "d20_spec_ready": ["科研与实验:M02"], "death_trigger": ["事件:M22"], "decision_brief": ["M96"], "doc_delta_committed": ["M98"], "doc_structure_ready": ["M97", "M98"], "e01_report_conflict": ["提示工程与指令设计:M01"], "e01_report_ready": ["提示工程与指令设计:M01"], "e01_spec_conflict": ["提示工程与指令设计:M02"], "e01_spec_ready": ["提示工程与指令设计:M02"], "e02_report_conflict": ["角色扮演与角色卡:M01"], "e02_report_ready": ["角色扮演与角色卡:M01"], "e02_spec_conflict": ["角色扮演与角色卡:M02"], "e02_spec_ready": ["角色扮演与角色卡:M02"], "e03_report_conflict": ["世界书与设定库:M01"], "e03_report_ready": ["世界书与设定库:M01"], "e03_spec_conflict": ["世界书与设定库:M02"], "e03_spec_ready": ["世界书与设定库:M02"], "e04_report_conflict": ["长文本与小说创作:M01"], "e04_report_ready": ["长文本与小说创作:M01"], "e04_spec_conflict": ["长文本与小说创作:M02"], "e04_spec_ready": ["长文本与小说创作:M02"], "e05_report_conflict": ["内容改写与风格迁移:M01"], "e05_report_ready": ["内容改写与风格迁移:M01"], "e05_spec_conflict": ["内容改写与风格迁移:M02"], "e05_spec_ready": ["内容改写与风格迁移:M02"], "e06_report_conflict": ["多语翻译与本地化:M01"], "e06_report_ready": ["多语翻译与本地化:M01"], "e06_spec_conflict": ["多语翻译与本地化:M02"], "e06_spec_ready": ["多语翻译与本地化:M02"], "e07_report_conflict": ["图像生成与视觉创作:M01"], "e07_report_ready": ["图像生成与视觉创作:M01"], "e07_spec_conflict": ["图像生成与视觉创作:M02"], "e07_spec_ready": ["图像生成与视觉创作:M02"], "e08_report_conflict": ["视频生成与剪辑:M01"], "e08_report_ready": ["视频生成与剪辑:M01"], "e08_spec_conflict": ["视频生成与剪辑:M02"], "e08_spec_ready": ["视频生成与剪辑:M02"], "e09_report_conflict": ["音频音乐与语音:M01"], "e09_report_ready": ["音频音乐与语音:M01"], "e09_spec_conflict": ["音频音乐与语音:M02"], "e09_spec_ready": ["音频音乐与语音:M02"], "e10_report_conflict": ["编辑校对与出版:M01"], "e10_report_ready": ["编辑校对与出版:M01"], "e10_spec_conflict": ["编辑校对与出版:M02"], "e10_spec_ready": ["编辑校对与出版:M02"], "e11_report_conflict": ["知识管理与检索增强:M01"], "e11_report_ready": ["知识管理与检索增强:M01"], "e11_spec_conflict": ["知识管理与检索增强:M02"], "e11_spec_ready": ["知识管理与检索增强:M02"], "e12_report_conflict": ["智能体与工作流编排:M01"], "e12_report_ready": ["智能体与工作流编排:M01"], "e12_spec_conflict": ["智能体与工作流编排:M02"], "e12_spec_ready": ["智能体与工作流编排:M02"], "e13_report_conflict": ["代码与软件工程:M01"], "e13_report_ready": ["代码与软件工程:M01"], "e13_spec_conflict": ["代码与软件工程:M02"], "e13_spec_ready": ["代码与软件工程:M02"], "e14_report_conflict": ["数据分析与决策支持:M01"], "e14_report_ready": ["数据分析与决策支持:M01"], "e14_spec_conflict": ["数据分析与决策支持:M02"], "e14_spec_ready": ["数据分析与决策支持:M02"], "e15_report_conflict": ["企业培训与组织学习:M01"], "e15_report_ready": ["企业培训与组织学习:M01"], "e15_spec_conflict": ["企业培训与组织学习:M02"], "e15_spec_ready": ["企业培训与组织学习:M02"], "e16_report_conflict": ["个人助理与日常生活:M01"], "e16_report_ready": ["个人助理与日常生活:M01"], "e16_spec_conflict": ["个人助理与日常生活:M02"], "e16_spec_ready": ["个人助理与日常生活:M02"], "e17_report_conflict": ["搜索与信息聚合:M01"], "e17_report_ready": ["搜索与信息聚合:M01"], "e17_spec_conflict": ["搜索与信息聚合:M02"], "e17_spec_ready": ["搜索与信息聚合:M02"], "e18_report_conflict": ["对话与客服:M01"], "e18_report_ready": ["对话与客服:M01"], "e18_spec_conflict": ["对话与客服:M02"], "e18_spec_ready": ["对话与客服:M02"], "e19_report_conflict": ["内容分发与社区运营:M01"], "e19_report_ready": ["内容分发与社区运营:M01"], "e19_spec_conflict": ["内容分发与社区运营:M02"], "e19_spec_ready": ["内容分发与社区运营:M02"], "e20_report_conflict": ["数字人与虚拟形象:M01"], "e20_report_ready": ["数字人与虚拟形象:M01"], "e20_spec_conflict": ["数字人与虚拟形象:M02"], "e20_spec_ready": ["数字人与虚拟形象:M02"], "f01_report_conflict": ["安全与对齐:M01"], "f01_report_ready": ["安全与对齐:M01"], "f01_spec_conflict": ["安全与对齐:M02"], "f01_spec_ready": ["安全与对齐:M02"], "f02_report_conflict": ["合规与监管:M01"], "f02_report_ready": ["合规与监管:M01"], "f02_spec_conflict": ["合规与监管:M02"], "f02_spec_ready": ["合规与监管:M02"], "f03_report_conflict": ["隐私与数据治理:M01"], "f03_report_ready": ["隐私与数据治理:M01"], "f03_spec_conflict": ["隐私与数据治理:M02"], "f03_spec_ready": ["隐私与数据治理:M02"], "f04_report_conflict": ["版权与知识产权:M01"], "f04_report_ready": ["版权与知识产权:M01"], "f04_spec_conflict": ["版权与知识产权:M02"], "f04_spec_ready": ["版权与知识产权:M02"], "f05_report_conflict": ["评测与基准:M01"], "f05_report_ready": ["评测与基准:M01"], "f05_spec_conflict": ["评测与基准:M02"], "f05_spec_ready": ["评测与基准:M02"], "f06_report_conflict": ["可解释性与审计:M01"], "f06_report_ready": ["可解释性与审计:M01"], "f06_spec_conflict": ["可解释性与审计:M02"], "f06_spec_ready": ["可解释性与审计:M02"], "f07_report_conflict": ["模型运营与成本:M01"], "f07_report_ready": ["模型运营与成本:M01"], "f07_spec_conflict": ["模型运营与成本:M02"], "f07_spec_ready": ["模型运营与成本:M02"], "f08_report_conflict": ["平台与基础设施:M01"], "f08_report_ready": ["平台与基础设施:M01"], "f08_spec_conflict": ["平台与基础设施:M02"], "f08_spec_ready": ["平台与基础设施:M02"], "f09_report_conflict": ["开源与开发者生态:M01"], "f09_report_ready": ["开源与开发者生态:M01"], "f09_spec_conflict": ["开源与开发者生态:M02"], "f09_spec_ready": ["开源与开发者生态:M02"], "f10_report_conflict": ["产业与商业落地:M01"], "f10_report_ready": ["产业与商业落地:M01"], "f10_spec_conflict": ["产业与商业落地:M02"], "f10_spec_ready": ["产业与商业落地:M02"], "faction_event": [], "factor_spec_conflict": ["量化金融:M32"], "factor_spec_ready": ["量化金融:M32"], "ghost_event": ["事件:M22"], "group_chat_event": [], "intent_received": ["M90"], "interaction_update": ["M95", "事件:M22"], "level_up": ["M03", "M13"], "load_order_ready": [], "market_event": ["M17", "事件:M22"], "minute_tick": ["M01", "M93", "M94"], "narrative_event": ["M96"], "npc_action": ["M43", "M55", "M57", "M58", "M59", "M91"], "phone_call_event": [], "polished_output": [], "prereq_missing": ["AI系统:M26"], "production_output": ["M92", "事件:M22"], "quest_state": ["M10", "M13", "M57", "M58", "M59", "M95"], "relationship_change": ["M43", "M55", "M57", "M58", "M59", "M91", "事件:M22"], "reputation_change": ["M06"], "revision_recorded": [], "romance_state_change": ["M43"], "social_feed_event": [], "spell_cast": ["M03"], "state_snapshot": ["M95"], "term_conflict_detected": ["M97"], "term_synced": [], "tick_day": ["M01", "M08", "M19", "M93", "M94"], "travel_event": ["M06"], "weather_state": []}, "events_consumed": 430, "events_declared": 443}"#
        ),
        (
            r#"tool_face_scan"#,
            &[],
            r#"{"candidates": 1, "entries": 1, "faces": [{"entries": 1, "module": "通用:M10", "source": "04_模块库/通用类/M10_时间推进.md"}], "modules": 1}"#
        ),
        (
            r#"world_slots_scan"#,
            &[],
            r#"{"arrays": 3, "slots": 10}"#
        ),
        ];
        for (name, want_issues, want_stats) in cases {
            let (issues, stats) = match *name {
                "payload_consumer_scan" => payload_consumer_scan(&root),
                "tool_face_scan" => tool_face_scan(&root),
                "world_slots_scan" => world_slots_scan(&root),
                other => panic!("未知用例 {}", other),
            };
            assert_eq!(issues, want_issues.to_vec(), "{} 的 issues 不一致", name);
            let want: Json = crate::jsonread::convert(
                &serde_json::from_str::<serde_json::Value>(want_stats).unwrap(),
            )
            .unwrap();
            assert!(
                crate::jsonread::json_eq(&stats, &want),
                "{} 的 stats 不一致\n  实得 {}\n  期望 {}",
                name,
                stats.dumps(),
                want.dumps()
            );
        }
    }
    // <<< GENERATED
}
