//! XML **子集**解析器 —— 复刻真源 `output_forms` 里 `xml.etree.ElementTree` 的**用到的那一层**。
//!
//! **为什么自己写**：真源用标准库 `xml.etree`，而本线的依赖纪律不容 Python 运行时；引第三方
//! （`quick-xml` 等）又要为「只用到 4 个查询」付一整棵 API。路数同 `miniyaml`：**只支持真源
//! 用到的那一层，越出子集即 fail-closed**（不猜、不近似）。
//!
//! 本线**需要**的那一层（全部来自 `output_forms._check_xml` / `_check_graphml`）：
//!
//! | 需要 | 对应 |
//! |---|---|
//! | 良构性（标签配对 / 属性语法 / 单根） | `ET.fromstring` 的 ParseError |
//! | 根元素**局部名** | `r.tag.split("}")[-1]` |
//! | 后代里所有 `graph` | `r.findall(".//{*}graph")` |
//! | 直接子元素 `node` / `edge` | `g.findall("{*}node")` |
//! | 属性取值 | `n.get("id")` / `e.get("source")` |
//!
//! **不做**：实体展开、DTD（真源在 `_xml_guard` 里**先拒**）、CDATA 的语义、命名空间解析
//! （只取局部名，与 `{*}` 通配同效）。

/// 一个元素节点。
#[derive(Debug, Clone)]
pub struct XNode {
    /// 原始标签名（可能带 `ns:` 前缀）。
    pub tag: String,
    pub attrs: Vec<(String, String)>,
    pub children: Vec<XNode>,
}

impl XNode {
    /// 真源 `tag.split("}")[-1]` 的等价物：取**局部名**（去 `ns:` 前缀 / `{uri}` 形式）。
    pub fn local(&self) -> &str {
        let t = self.tag.as_str();
        let t = match t.rfind('}') {
            Some(i) => &t[i + 1..],
            None => t,
        };
        match t.rfind(':') {
            Some(i) => &t[i + 1..],
            None => t,
        }
    }

    /// 真源 `e.get(k)`。
    pub fn attr(&self, k: &str) -> Option<&str> {
        self.attrs.iter().find(|(n, _)| n == k).map(|(_, v)| v.as_str())
    }

    /// 真源 `r.findall(".//{*}graph")`：**后代**（不含自身）里局部名匹配者，文档序。
    pub fn descendants(&self, name: &str) -> Vec<&XNode> {
        let mut out = Vec::new();
        for c in &self.children {
            if c.local() == name {
                out.push(c);
            }
            out.extend(c.descendants(name));
        }
        out
    }

    /// 真源 `g.findall("{*}node")`：**直接子元素**里局部名匹配者。
    pub fn children_named(&self, name: &str) -> Vec<&XNode> {
        self.children.iter().filter(|c| c.local() == name).collect()
    }
}

/// 真源 `_xml_guard`：拒 DTD/ENTITY 声明（堵实体展开 / 十亿笑声类攻击）。
pub fn dtd_guard(text: &str) -> String {
    // `re.compile(r"<!\s*(?:DOCTYPE|ENTITY)", re.I)`
    let lower = text.to_lowercase();
    let bytes: Vec<char> = lower.chars().collect();
    let mut i = 0;
    while i + 1 < bytes.len() {
        if bytes[i] == '<' && bytes[i + 1] == '!' {
            let mut j = i + 2;
            while j < bytes.len() && bytes[j].is_whitespace() {
                j += 1;
            }
            let rest: String = bytes[j..].iter().take(7).collect();
            if rest.starts_with("doctype") || rest.starts_with("entity") {
                return "含 DTD/ENTITY 声明（本仓 XML 产出面禁 DTD：堵实体展开类攻击）".to_string();
            }
        }
        i += 1;
    }
    String::new()
}

/// 真源 `ET.fromstring` 的对应物：解析成树；不良构 → `Err`（**文本与 CPython 不可比**）。
pub fn parse(text: &str) -> Result<XNode, String> {
    let chars: Vec<char> = text.chars().collect();
    let mut i = 0usize;
    let mut stack: Vec<XNode> = Vec::new();
    let mut root: Option<XNode> = None;
    // ⚠️ 判「根之前/之后有内容」要看**根的开始标签是否出现过**，**不能**用 `root.is_none()`：
    // 根元素是在**结束标签**处才赋值的，用它判会把文档中途的所有叶子文本（`P40`、`directed`…）
    // 全误判成"根之前的内容"。实测（2026-10-04）：105 份真 GraphML 因此**全部**解析失败。
    let mut started = false;
    let mut root_closed = false;

    while i < chars.len() {
        if chars[i] != '<' {
            // 文本/空白
            let start = i;
            while i < chars.len() && chars[i] != '<' {
                i += 1;
            }
            let seg: String = chars[start..i].iter().collect();
            if !seg.trim().is_empty() {
                if !started {
                    return Err("内容出现在根元素之前".to_string());
                }
                if root_closed {
                    return Err("内容出现在根元素之后".to_string());
                }
            }
            continue;
        }
        // 注释 / 声明 / CDATA
        if chars[i..].starts_with(&['<', '!', '-', '-']) {
            let mut j = i + 4;
            while j + 2 < chars.len() && !chars[j..].starts_with(&['-', '-', '>']) {
                j += 1;
            }
            if j + 2 >= chars.len() {
                return Err("注释未闭合".to_string());
            }
            i = j + 3;
            continue;
        }
        if chars[i..].starts_with(&['<', '?']) {
            let mut j = i + 2;
            while j + 1 < chars.len() && !chars[j..].starts_with(&['?', '>']) {
                j += 1;
            }
            if j + 1 >= chars.len() {
                return Err("处理指令未闭合".to_string());
            }
            i = j + 2;
            continue;
        }
        if chars[i..].starts_with(&['<', '!', '[', 'C', 'D']) {
            let mut j = i + 9;
            while j + 2 < chars.len() && !chars[j..].starts_with(&[']', ']', '>']) {
                j += 1;
            }
            if j + 2 >= chars.len() {
                return Err("CDATA 未闭合".to_string());
            }
            i = j + 3;
            continue;
        }
        // 结束标签
        if chars[i..].starts_with(&['<', '/']) {
            let mut j = i + 2;
            while j < chars.len() && chars[j] != '>' {
                j += 1;
            }
            if j >= chars.len() {
                return Err("结束标签未闭合".to_string());
            }
            let name: String = chars[i + 2..j].iter().collect();
            let name = name.trim().to_string();
            match stack.pop() {
                None => return Err(format!("多余的结束标签 </{}>", name)),
                Some(node) => {
                    if node.tag != name {
                        return Err(format!(
                            "标签不匹配：<{}> 对 </{}>",
                            node.tag, name
                        ));
                    }
                    match stack.last_mut() {
                        Some(parent) => parent.children.push(node),
                        None => {
                            root = Some(node);
                            root_closed = true;
                        }
                    }
                }
            }
            i = j + 1;
            continue;
        }
        // 开始标签
        let mut j = i + 1;
        let mut quote: Option<char> = None;
        while j < chars.len() {
            let c = chars[j];
            match quote {
                Some(q) => {
                    if c == q {
                        quote = None;
                    }
                }
                None => {
                    if c == '"' || c == '\'' {
                        quote = Some(c);
                    } else if c == '>' {
                        break;
                    }
                }
            }
            j += 1;
        }
        if j >= chars.len() {
            return Err("开始标签未闭合".to_string());
        }
        let raw: String = chars[i + 1..j].iter().collect();
        let raw = raw.trim().to_string();
        let self_closing = raw.ends_with('/');
        let raw = if self_closing { raw[..raw.len() - 1].trim().to_string() } else { raw };
        let (tag, attr_str) = match raw.find(char::is_whitespace) {
            Some(k) => (raw[..k].to_string(), raw[k..].to_string()),
            None => (raw.clone(), String::new()),
        };
        if tag.is_empty() {
            return Err("空标签名".to_string());
        }
        let attrs = parse_attrs(&attr_str)?;
        started = true;
        let node = XNode { tag, attrs, children: Vec::new() };
        if self_closing {
            match stack.last_mut() {
                Some(parent) => parent.children.push(node),
                None => {
                    if root.is_some() {
                        return Err("多个根元素".to_string());
                    }
                    started = true;
                    root = Some(node);
                    root_closed = true;
                }
            }
        } else {
            stack.push(node);
        }
        i = j + 1;
    }
    if !stack.is_empty() {
        return Err(format!("标签未闭合：<{}>", stack.last().unwrap().tag));
    }
    root.ok_or_else(|| "空文档".to_string())
}

fn parse_attrs(s: &str) -> Result<Vec<(String, String)>, String> {
    let chars: Vec<char> = s.chars().collect();
    let mut out: Vec<(String, String)> = Vec::new();
    let mut i = 0usize;
    while i < chars.len() {
        while i < chars.len() && chars[i].is_whitespace() {
            i += 1;
        }
        if i >= chars.len() {
            break;
        }
        let start = i;
        while i < chars.len() && chars[i] != '=' && !chars[i].is_whitespace() {
            i += 1;
        }
        let name: String = chars[start..i].iter().collect();
        if name.is_empty() {
            return Err("属性名缺失".to_string());
        }
        while i < chars.len() && chars[i].is_whitespace() {
            i += 1;
        }
        if i >= chars.len() || chars[i] != '=' {
            return Err(format!("属性 {} 缺 =", name));
        }
        i += 1;
        while i < chars.len() && chars[i].is_whitespace() {
            i += 1;
        }
        if i >= chars.len() || (chars[i] != '"' && chars[i] != '\'') {
            return Err(format!("属性 {} 的值未加引号", name));
        }
        let q = chars[i];
        i += 1;
        let vstart = i;
        while i < chars.len() && chars[i] != q {
            i += 1;
        }
        if i >= chars.len() {
            return Err(format!("属性 {} 的值未闭合", name));
        }
        let value: String = chars[vstart..i].iter().collect();
        i += 1;
        if out.iter().any(|(n, _)| *n == name) {
            return Err(format!("属性重复：{}", name));
        }
        out.push((name, value));
    }
    Ok(out)
}

#[cfg(test)]
mod tests {
    use super::*;
    // >>> GENERATED by tools/gen_xmlmini_cases.py（勿手改；重跑生成器覆盖本段）
    /// ===== 真语料 GraphML/SVG 上的四查询差分（期望值从真源 `ElementTree` 取）=====
    ///
    /// 钉住 `xmlmini` 的**用到那一层**：根元素局部名 / 后代 `graph` 数 / `node` id 集 / `edge`
    /// 端点悬空数。**解析失败的文本不可比**（CPython 的 ParseError vs 本线），故只比"是否解析成功"。
    #[test]
    fn xmlmini_matches_elementtree_query_layer() {
        let root = crate::testutil::repo_root();
        let cases: &[(&str, &str, usize, &[&str], usize)] = &[
        (r#"community/AI人力资源与招聘域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, 1, &[r#"D14-01"#, r#"D14-02"#, r#"D14-03"#, r#"D14-04"#, r#"D14-05"#, r#"D14-06"#, r#"D14-07"#, r#"D14-08"#, r#"D14-09"#, r#"D14-10"#, r#"D14-11"#, r#"D14-12"#, r#"STD-cncf-cloudevents"#, r#"STD-common-criteria"#, r#"STD-frictionless-package"#, r#"STD-frictionless-table"#, r#"STD-gdpr"#, r#"STD-gips"#, r#"STD-ietf-json"#, r#"STD-ietf-json-schema"#, r#"STD-mermaid"#, r#"STD-nist-ai-rmf"#, r#"STD-rdf11"#, r#"STD-unesco-ai"#, r#"STD-vega-lite"#, r#"STD-w3c-prov-o"#], 0),
        (r#"community/AI保险域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, 1, &[r#"D05-01"#, r#"D05-02"#, r#"D05-03"#, r#"D05-04"#, r#"D05-05"#, r#"D05-06"#, r#"D05-07"#, r#"D05-08"#, r#"D05-09"#, r#"D05-10"#, r#"D05-11"#, r#"D05-12"#, r#"STD-common-criteria"#, r#"STD-gdpr"#, r#"STD-gips"#, r#"STD-ietf-bcp47"#, r#"STD-ietf-json"#, r#"STD-ietf-json-schema"#, r#"STD-mermaid"#, r#"STD-nist-ai-rmf"#, r#"STD-rdf11"#, r#"STD-vega-lite"#, r#"STD-w3c-prov-o"#, r#"STD-w3c-tabular-data"#], 0),
        (r#"community/AI农业域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, 1, &[r#"D10-01"#, r#"D10-02"#, r#"D10-03"#, r#"D10-04"#, r#"D10-05"#, r#"D10-06"#, r#"D10-07"#, r#"D10-08"#, r#"D10-09"#, r#"D10-10"#, r#"D10-11"#, r#"D10-12"#, r#"STD-c2pa-spec"#, r#"STD-cbor"#, r#"STD-common-criteria"#, r#"STD-cose"#, r#"STD-fao-food"#, r#"STD-gdpr"#, r#"STD-ietf-bcp47"#, r#"STD-ietf-json"#, r#"STD-ietf-json-schema"#, r#"STD-mermaid"#, r#"STD-nist-ai-rmf"#, r#"STD-oecd-ai"#, r#"STD-opengeospatial"#, r#"STD-rdf11"#, r#"STD-vega-lite"#, r#"STD-w3c-prov-o"#, r#"STD-w3c-tabular-data"#], 0),
        (r#"community/AI制药与生物域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, 1, &[r#"D02-01"#, r#"D02-02"#, r#"D02-03"#, r#"D02-04"#, r#"D02-05"#, r#"D02-06"#, r#"D02-07"#, r#"D02-08"#, r#"D02-09"#, r#"D02-10"#, r#"D02-11"#, r#"D02-12"#, r#"STD-cncf-cloudevents"#, r#"STD-common-criteria"#, r#"STD-commonmark"#, r#"STD-hl7-fhir"#, r#"STD-ietf-bcp47"#, r#"STD-ietf-json"#, r#"STD-ietf-json-schema"#, r#"STD-mermaid"#, r#"STD-nist-ai-rmf"#, r#"STD-rdf11"#, r#"STD-vega-lite"#, r#"STD-w3c-epub33"#, r#"STD-w3c-prov-o"#, r#"STD-w3c-tabular-data"#, r#"STD-w3c-xml"#], 0),
        (r#"community/AI制造业域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, 1, &[r#"D08-01"#, r#"D08-02"#, r#"D08-03"#, r#"D08-04"#, r#"D08-05"#, r#"D08-06"#, r#"D08-07"#, r#"D08-08"#, r#"D08-09"#, r#"D08-10"#, r#"D08-11"#, r#"D08-12"#, r#"STD-common-criteria"#, r#"STD-frictionless-package"#, r#"STD-frictionless-table"#, r#"STD-ietf-bcp47"#, r#"STD-ietf-json"#, r#"STD-ietf-json-schema"#, r#"STD-mermaid"#, r#"STD-nist-ai-rmf"#, r#"STD-opcua"#, r#"STD-owasp-llm"#, r#"STD-owasp-top10"#, r#"STD-rdf11"#, r#"STD-spdx-3"#, r#"STD-vega-lite"#, r#"STD-w3c-prov-o"#, r#"STD-w3c-svg2"#, r#"STD-w3c-tabular-data"#, r#"STD-w3c-xml"#], 0),
        (r#"community/AI医疗健康域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, 1, &[r#"D01-01"#, r#"D01-02"#, r#"D01-03"#, r#"D01-04"#, r#"D01-05"#, r#"D01-06"#, r#"D01-07"#, r#"D01-08"#, r#"D01-09"#, r#"D01-10"#, r#"D01-11"#, r#"D01-12"#, r#"STD-dicom"#, r#"STD-gdpr"#, r#"STD-hl7-fhir"#, r#"STD-ietf-bcp47"#, r#"STD-ietf-json"#, r#"STD-ietf-json-schema"#, r#"STD-mermaid"#, r#"STD-rdf11"#, r#"STD-unesco-ai"#, r#"STD-vega-lite"#, r#"STD-w3c-prov-o"#, r#"STD-w3c-skos"#, r#"STD-w3c-tabular-data"#], 0),
        (r#"community/AI政务与公共事务域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, 1, &[r#"D07-01"#, r#"D07-02"#, r#"D07-03"#, r#"D07-04"#, r#"D07-05"#, r#"D07-06"#, r#"D07-07"#, r#"D07-08"#, r#"D07-09"#, r#"D07-10"#, r#"D07-11"#, r#"D07-12"#, r#"STD-cncf-cloudevents"#, r#"STD-common-criteria"#, r#"STD-commonmark"#, r#"STD-gdpr"#, r#"STD-ietf-bcp47"#, r#"STD-ietf-json"#, r#"STD-ietf-json-schema"#, r#"STD-mermaid"#, r#"STD-nist-800-188"#, r#"STD-nist-privacy"#, r#"STD-oasis-openapi"#, r#"STD-oecd-ai"#, r#"STD-rdf11"#, r#"STD-vega-lite"#, r#"STD-w3c-prov-o"#, r#"STD-w3c-tabular-data"#, r#"STD-w3c-vc"#, r#"STD-w3c-wcag22"#], 0),
        (r#"community/AI教育域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, 1, &[r#"D06-01"#, r#"D06-02"#, r#"D06-03"#, r#"D06-04"#, r#"D06-05"#, r#"D06-06"#, r#"D06-07"#, r#"D06-08"#, r#"D06-09"#, r#"D06-10"#, r#"D06-11"#, r#"D06-12"#, r#"STD-common-criteria"#, r#"STD-gdpr"#, r#"STD-ietf-bcp47"#, r#"STD-ietf-json"#, r#"STD-ietf-json-schema"#, r#"STD-mermaid"#, r#"STD-nist-ai-rmf"#, r#"STD-rdf11"#, r#"STD-unesco-ai"#, r#"STD-vega-lite"#, r#"STD-w3c-prov-o"#, r#"STD-w3c-tabular-data"#], 0),
        (r#"community/AI法律与合规域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, 1, &[r#"D03-01"#, r#"D03-02"#, r#"D03-03"#, r#"D03-04"#, r#"D03-05"#, r#"D03-06"#, r#"D03-07"#, r#"D03-08"#, r#"D03-09"#, r#"D03-10"#, r#"D03-11"#, r#"D03-12"#, r#"STD-common-criteria"#, r#"STD-commonmark"#, r#"STD-creativecommons"#, r#"STD-frictionless-package"#, r#"STD-frictionless-table"#, r#"STD-gdpr"#, r#"STD-ietf-bcp47"#, r#"STD-ietf-json"#, r#"STD-ietf-json-schema"#, r#"STD-mermaid"#, r#"STD-nist-ai-rmf"#, r#"STD-rdf11"#, r#"STD-vega-lite"#, r#"STD-w3c-prov-o"#, r#"STD-w3c-tabular-data"#], 0),
        (r#"community/AI系统域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, 1, &[r#"C00"#, r#"C01"#, r#"C02"#, r#"C03"#, r#"C04"#, r#"C05"#, r#"C06"#, r#"C07"#, r#"C08"#, r#"C09"#, r#"C10"#, r#"C11"#, r#"C12"#, r#"C13"#, r#"C14"#, r#"C15"#, r#"C16"#, r#"C17"#, r#"C18"#, r#"C19"#, r#"C20"#, r#"C21"#, r#"C22"#, r#"C23"#, r#"C24"#, r#"C25"#, r#"C26"#, r#"C27"#, r#"C28"#, r#"C29"#, r#"C30"#, r#"C31"#, r#"C32"#, r#"C33"#, r#"C34"#, r#"C35"#, r#"C36"#, r#"C37"#, r#"C38"#, r#"C39"#, r#"C40"#, r#"C41"#, r#"C42"#, r#"C43"#, r#"C44"#, r#"C45"#, r#"C46"#, r#"C47"#], 0),
        (r#"community/AI能源与电力域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, 1, &[r#"D09-01"#, r#"D09-02"#, r#"D09-03"#, r#"D09-04"#, r#"D09-05"#, r#"D09-06"#, r#"D09-07"#, r#"D09-08"#, r#"D09-09"#, r#"D09-10"#, r#"D09-11"#, r#"D09-12"#, r#"STD-common-criteria"#, r#"STD-cwe"#, r#"STD-frictionless-package"#, r#"STD-frictionless-table"#, r#"STD-gdpr"#, r#"STD-hl7-fhir"#, r#"STD-ietf-bcp47"#, r#"STD-ietf-json"#, r#"STD-ietf-json-schema"#, r#"STD-mermaid"#, r#"STD-nist-ai-rmf"#, r#"STD-owasp-llm"#, r#"STD-owasp-top10"#, r#"STD-rdf11"#, r#"STD-vega-lite"#, r#"STD-w3c-prov-o"#, r#"STD-w3c-tabular-data"#], 0),
        (r#"community/AI金融投研与风控域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, 1, &[r#"D04-01"#, r#"D04-02"#, r#"D04-03"#, r#"D04-04"#, r#"D04-05"#, r#"D04-06"#, r#"D04-07"#, r#"D04-08"#, r#"D04-09"#, r#"D04-10"#, r#"D04-11"#, r#"D04-12"#, r#"STD-cncf-cloudevents"#, r#"STD-gdpr"#, r#"STD-gips"#, r#"STD-ietf-bcp47"#, r#"STD-ietf-json"#, r#"STD-ietf-json-schema"#, r#"STD-iso10383"#, r#"STD-mermaid"#, r#"STD-rdf11"#, r#"STD-vega-lite"#, r#"STD-w3c-prov-o"#, r#"STD-w3c-tabular-data"#], 0),
        (r#"community/AI食品与餐饮域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, 1, &[r#"D16-01"#, r#"D16-02"#, r#"D16-03"#, r#"D16-04"#, r#"D16-05"#, r#"D16-06"#, r#"D16-07"#, r#"D16-08"#, r#"D16-09"#, r#"D16-10"#, r#"D16-11"#, r#"D16-12"#, r#"STD-common-criteria"#, r#"STD-gdpr"#, r#"STD-ietf-bcp47"#, r#"STD-ietf-json"#, r#"STD-ietf-json-schema"#, r#"STD-mermaid"#, r#"STD-nist-ai-rmf"#, r#"STD-rdf11"#, r#"STD-vega-lite"#, r#"STD-w3c-prov-o"#, r#"STD-w3c-tabular-data"#], 0),
        (r#"community/三维与世界模型域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, 1, &[r#"A08-01"#, r#"A08-02"#, r#"A08-03"#, r#"A08-04"#, r#"A08-05"#, r#"A08-06"#, r#"A08-07"#, r#"A08-08"#, r#"A08-09"#, r#"A08-10"#, r#"A08-11"#, r#"A08-12"#, r#"STD-ietf-bcp47"#, r#"STD-ietf-json"#, r#"STD-ietf-json-schema"#, r#"STD-mermaid"#, r#"STD-mlcommons-bench"#, r#"STD-onnx"#, r#"STD-opengeospatial"#, r#"STD-protobuf"#, r#"STD-rdf11"#, r#"STD-vega-lite"#, r#"STD-w3c-prov-o"#, r#"STD-w3c-tabular-data"#], 0),
        (r#"community/上下文工程与长上下文域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, 1, &[r#"C12-01"#, r#"C12-02"#, r#"C12-03"#, r#"C12-04"#, r#"C12-05"#, r#"C12-06"#, r#"C12-07"#, r#"C12-08"#, r#"C12-09"#, r#"C12-10"#, r#"C12-11"#, r#"C12-12"#, r#"STD-cncf-otel-semconv"#, r#"STD-commonmark"#, r#"STD-frictionless-package"#, r#"STD-gfm"#, r#"STD-ietf-bcp47"#, r#"STD-ietf-json"#, r#"STD-ietf-json-schema"#, r#"STD-mermaid"#, r#"STD-mlcommons-bench"#, r#"STD-vega-lite"#, r#"STD-w3c-epub33"#, r#"STD-w3c-tabular-data"#, r#"STD-w3c-xml"#], 0),
        (r#"community/世界书与设定库域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, 1, &[r#"E03-01"#, r#"E03-02"#, r#"E03-03"#, r#"E03-04"#, r#"E03-05"#, r#"E03-06"#, r#"E03-07"#, r#"E03-08"#, r#"E03-09"#, r#"E03-10"#, r#"E03-11"#, r#"E03-12"#, r#"STD-commonmark"#, r#"STD-frictionless-package"#, r#"STD-ietf-bcp47"#, r#"STD-ietf-json"#, r#"STD-ietf-json-schema"#, r#"STD-mermaid"#, r#"STD-vega-lite"#, r#"STD-w3c-epub33"#, r#"STD-w3c-tabular-data"#, r#"STD-w3c-xml"#], 0),
        (r#"community/个人助理与日常生活域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, 1, &[r#"E16-01"#, r#"E16-02"#, r#"E16-03"#, r#"E16-04"#, r#"E16-05"#, r#"E16-06"#, r#"E16-07"#, r#"E16-08"#, r#"E16-09"#, r#"E16-10"#, r#"E16-11"#, r#"E16-12"#, r#"STD-commonmark"#, r#"STD-ietf-bcp47"#, r#"STD-ietf-json"#, r#"STD-ietf-json-schema"#, r#"STD-mermaid"#, r#"STD-vega-lite"#, r#"STD-w3c-epub33"#, r#"STD-w3c-tabular-data"#, r#"STD-w3c-xml"#], 0),
        (r#"community/交通与出行域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, 1, &[r#"D13-01"#, r#"D13-02"#, r#"D13-03"#, r#"D13-04"#, r#"D13-05"#, r#"D13-06"#, r#"D13-07"#, r#"D13-08"#, r#"D13-09"#, r#"D13-10"#, r#"D13-11"#, r#"D13-12"#, r#"STD-a2a"#, r#"STD-cncf-cloudevents"#, r#"STD-common-criteria"#, r#"STD-covesa-vss"#, r#"STD-frictionless-package"#, r#"STD-frictionless-table"#, r#"STD-ietf-bcp47"#, r#"STD-ietf-json-schema"#, r#"STD-mermaid"#, r#"STD-nist-ai-rmf"#, r#"STD-owasp-llm"#, r#"STD-owasp-top10"#, r#"STD-rdf11"#, r#"STD-vega-lite"#, r#"STD-w3c-prov-o"#, r#"STD-w3c-tabular-data"#], 0),
        (r#"community/产业与商业落地域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, 1, &[r#"F10-01"#, r#"F10-02"#, r#"F10-03"#, r#"F10-04"#, r#"F10-05"#, r#"F10-06"#, r#"F10-07"#, r#"F10-08"#, r#"F10-09"#, r#"F10-10"#, r#"F10-11"#, r#"F10-12"#, r#"STD-ietf-json"#, r#"STD-ietf-json-schema"#, r#"STD-mermaid"#, r#"STD-nist-ai-rmf"#, r#"STD-oasis-openapi"#, r#"STD-rdf11"#, r#"STD-spdx-licenses"#, r#"STD-unesco-ai"#, r#"STD-vega-lite"#, r#"STD-w3c-prov-o"#], 0),
        (r#"community/代码与软件工程域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, 1, &[r#"E13-01"#, r#"E13-02"#, r#"E13-03"#, r#"E13-04"#, r#"E13-05"#, r#"E13-06"#, r#"E13-07"#, r#"E13-08"#, r#"E13-09"#, r#"E13-10"#, r#"E13-11"#, r#"E13-12"#, r#"STD-commonmark"#, r#"STD-cwe"#, r#"STD-eu-machinery"#, r#"STD-ietf-bcp47"#, r#"STD-ietf-json"#, r#"STD-ietf-json-schema"#, r#"STD-mermaid"#, r#"STD-osi-osd"#, r#"STD-owasp-llm"#, r#"STD-owasp-top10"#, r#"STD-peps"#, r#"STD-rst-docutils"#, r#"STD-spdx-3"#, r#"STD-vega-lite"#, r#"STD-w3c-epub33"#, r#"STD-w3c-tabular-data"#, r#"STD-w3c-xml"#], 0),
        (r#"community/代码大模型域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, 1, &[r#"A09-01"#, r#"A09-02"#, r#"A09-03"#, r#"A09-04"#, r#"A09-05"#, r#"A09-06"#, r#"A09-07"#, r#"A09-08"#, r#"A09-09"#, r#"A09-10"#, r#"A09-11"#, r#"A09-12"#, r#"STD-commonmark"#, r#"STD-cwe"#, r#"STD-frictionless-package"#, r#"STD-gfm"#, r#"STD-ietf-bcp47"#, r#"STD-ietf-json"#, r#"STD-ietf-json-schema"#, r#"STD-jsonrpc"#, r#"STD-lsp"#, r#"STD-mermaid"#, r#"STD-mlcommons-bench"#, r#"STD-osv"#, r#"STD-owasp-llm"#, r#"STD-owasp-top10"#, r#"STD-vega-lite"#, r#"STD-w3c-tabular-data"#], 0),
        (r#"community/代码审查与缺陷检测域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, 1, &[r#"B09-01"#, r#"B09-02"#, r#"B09-03"#, r#"B09-04"#, r#"B09-05"#, r#"B09-06"#, r#"B09-07"#, r#"B09-08"#, r#"B09-09"#, r#"B09-10"#, r#"B09-11"#, r#"B09-12"#, r#"STD-commonmark"#, r#"STD-cwe"#, r#"STD-ietf-bcp47"#, r#"STD-ietf-json"#, r#"STD-ietf-json-schema"#, r#"STD-oasis-sarif"#, r#"STD-osv"#, r#"STD-rdf11"#, r#"STD-spdx-3"#, r#"STD-vega-lite"#, r#"STD-w3c-prov-o"#, r#"STD-w3c-tabular-data"#], 0),
        (r#"community/代码生成与补全域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, 1, &[r#"B08-01"#, r#"B08-02"#, r#"B08-03"#, r#"B08-04"#, r#"B08-05"#, r#"B08-06"#, r#"B08-07"#, r#"B08-08"#, r#"B08-09"#, r#"B08-10"#, r#"B08-11"#, r#"B08-12"#, r#"STD-commonmark"#, r#"STD-creativecommons"#, r#"STD-frictionless-package"#, r#"STD-frictionless-table"#, r#"STD-ietf-bcp47"#, r#"STD-ietf-json"#, r#"STD-ietf-json-schema"#, r#"STD-oasis-openapi"#, r#"STD-rdf11"#, r#"STD-vega-lite"#, r#"STD-w3c-prov-o"#, r#"STD-w3c-tabular-data"#], 0),
        (r#"community/企业培训与组织学习域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, 1, &[r#"E15-01"#, r#"E15-02"#, r#"E15-03"#, r#"E15-04"#, r#"E15-05"#, r#"E15-06"#, r#"E15-07"#, r#"E15-08"#, r#"E15-09"#, r#"E15-10"#, r#"E15-11"#, r#"E15-12"#, r#"STD-commonmark"#, r#"STD-gdpr"#, r#"STD-ietf-bcp47"#, r#"STD-ietf-json"#, r#"STD-ietf-json-schema"#, r#"STD-mermaid"#, r#"STD-mlcommons-bench"#, r#"STD-unesco-ai"#, r#"STD-vega-lite"#, r#"STD-w3c-epub33"#, r#"STD-w3c-tabular-data"#, r#"STD-w3c-xml"#], 0),
        (r#"community/传媒与新闻域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, 1, &[r#"D17-01"#, r#"D17-02"#, r#"D17-03"#, r#"D17-04"#, r#"D17-05"#, r#"D17-06"#, r#"D17-07"#, r#"D17-08"#, r#"D17-09"#, r#"D17-10"#, r#"D17-11"#, r#"D17-12"#, r#"STD-common-criteria"#, r#"STD-creativecommons"#, r#"STD-ietf-bcp47"#, r#"STD-ietf-json"#, r#"STD-ietf-json-schema"#, r#"STD-mermaid"#, r#"STD-nist-ai-rmf"#, r#"STD-rdf11"#, r#"STD-spdx-licenses"#, r#"STD-vega-lite"#, r#"STD-w3c-prov-o"#, r#"STD-w3c-tabular-data"#], 0),
        (r#"community/信息抽取与结构化域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, 1, &[r#"B05-01"#, r#"B05-02"#, r#"B05-03"#, r#"B05-04"#, r#"B05-05"#, r#"B05-06"#, r#"B05-07"#, r#"B05-08"#, r#"B05-09"#, r#"B05-10"#, r#"B05-11"#, r#"B05-12"#, r#"STD-cncf-cloudevents"#, r#"STD-commonmark"#, r#"STD-frictionless-package"#, r#"STD-frictionless-table"#, r#"STD-ietf-bcp47"#, r#"STD-ietf-json"#, r#"STD-ietf-json-schema"#, r#"STD-mlcommons-bench"#, r#"STD-rdf11"#, r#"STD-vega-lite"#, r#"STD-w3c-prov-o"#, r#"STD-w3c-skos"#, r#"STD-w3c-tabular-data"#], 0),
        (r#"community/具身智能与机器人域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, 1, &[r#"A13-01"#, r#"A13-02"#, r#"A13-03"#, r#"A13-04"#, r#"A13-05"#, r#"A13-06"#, r#"A13-07"#, r#"A13-08"#, r#"A13-09"#, r#"A13-10"#, r#"A13-11"#, r#"A13-12"#, r#"STD-covesa-vss"#, r#"STD-eu-machinery"#, r#"STD-ietf-bcp47"#, r#"STD-ietf-json"#, r#"STD-ietf-json-schema"#, r#"STD-jose"#, r#"STD-jsonrpc"#, r#"STD-mcp"#, r#"STD-mermaid"#, r#"STD-mlcommons-croissant"#, r#"STD-onnx"#, r#"STD-owasp-llm"#, r#"STD-owasp-top10"#, r#"STD-protobuf"#, r#"STD-schema-org"#, r#"STD-uptane"#, r#"STD-vega-lite"#, r#"STD-w3c-tabular-data"#], 0),
        (r#"community/内容分发与社区运营域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, 1, &[r#"E19-01"#, r#"E19-02"#, r#"E19-03"#, r#"E19-04"#, r#"E19-05"#, r#"E19-06"#, r#"E19-07"#, r#"E19-08"#, r#"E19-09"#, r#"E19-10"#, r#"E19-11"#, r#"E19-12"#, r#"STD-commonmark"#, r#"STD-ietf-bcp47"#, r#"STD-ietf-json"#, r#"STD-ietf-json-schema"#, r#"STD-mermaid"#, r#"STD-nist-ai-rmf"#, r#"STD-vega-lite"#, r#"STD-w3c-epub33"#, r#"STD-w3c-tabular-data"#, r#"STD-w3c-xml"#], 0),
        (r#"community/内容改写与风格迁移域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, 1, &[r#"E05-01"#, r#"E05-02"#, r#"E05-03"#, r#"E05-04"#, r#"E05-05"#, r#"E05-06"#, r#"E05-07"#, r#"E05-08"#, r#"E05-09"#, r#"E05-10"#, r#"E05-11"#, r#"E05-12"#, r#"STD-commonmark"#, r#"STD-ietf-bcp47"#, r#"STD-ietf-json"#, r#"STD-ietf-json-schema"#, r#"STD-mermaid"#, r#"STD-vega-lite"#, r#"STD-w3c-epub33"#, r#"STD-w3c-tabular-data"#, r#"STD-w3c-xml"#], 0),
        (r#"community/分类与情感分析域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, 1, &[r#"B04-01"#, r#"B04-02"#, r#"B04-03"#, r#"B04-04"#, r#"B04-05"#, r#"B04-06"#, r#"B04-07"#, r#"B04-08"#, r#"B04-09"#, r#"B04-10"#, r#"B04-11"#, r#"B04-12"#, r#"STD-cncf-otel-semconv"#, r#"STD-commonmark"#, r#"STD-frictionless-package"#, r#"STD-frictionless-table"#, r#"STD-ietf-bcp47"#, r#"STD-ietf-json"#, r#"STD-ietf-json-schema"#, r#"STD-mlcommons-bench"#, r#"STD-rdf11"#, r#"STD-vega-lite"#, r#"STD-w3c-prov-o"#, r#"STD-w3c-tabular-data"#], 0),
        (r#"community/参数高效微调域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, 1, &[r#"C06-01"#, r#"C06-02"#, r#"C06-03"#, r#"C06-04"#, r#"C06-05"#, r#"C06-06"#, r#"C06-07"#, r#"C06-08"#, r#"C06-09"#, r#"C06-10"#, r#"C06-11"#, r#"C06-12"#, r#"STD-cncf-otel-semconv"#, r#"STD-commonmark"#, r#"STD-frictionless-package"#, r#"STD-frictionless-table"#, r#"STD-ietf-bcp47"#, r#"STD-ietf-json"#, r#"STD-ietf-json-schema"#, r#"STD-mermaid"#, r#"STD-mlcommons-bench"#, r#"STD-onnx"#, r#"STD-owasp-llm"#, r#"STD-owasp-top10"#, r#"STD-protobuf"#, r#"STD-vega-lite"#, r#"STD-w3c-tabular-data"#], 0),
        (r#"community/可观测性成本与可靠性域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, 1, &[r#"C18-01"#, r#"C18-02"#, r#"C18-03"#, r#"C18-04"#, r#"C18-05"#, r#"C18-06"#, r#"C18-07"#, r#"C18-08"#, r#"C18-09"#, r#"C18-10"#, r#"C18-11"#, r#"C18-12"#, r#"STD-cncf-cloudevents"#, r#"STD-cncf-otel-semconv"#, r#"STD-commonmark"#, r#"STD-frictionless-package"#, r#"STD-frictionless-table"#, r#"STD-ietf-bcp47"#, r#"STD-ietf-json"#, r#"STD-ietf-json-schema"#, r#"STD-mermaid"#, r#"STD-onnx"#, r#"STD-onvif-ucum"#, r#"STD-openmetrics"#, r#"STD-prometheus-exposition"#, r#"STD-protobuf"#, r#"STD-vega-lite"#, r#"STD-w3c-tabular-data"#], 0),
        (r#"community/可解释性与审计域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, 1, &[r#"F06-01"#, r#"F06-02"#, r#"F06-03"#, r#"F06-04"#, r#"F06-05"#, r#"F06-06"#, r#"F06-07"#, r#"F06-08"#, r#"F06-09"#, r#"F06-10"#, r#"F06-11"#, r#"F06-12"#, r#"STD-gdpr"#, r#"STD-ietf-json"#, r#"STD-ietf-json-schema"#, r#"STD-mermaid"#, r#"STD-nist-ai-rmf"#, r#"STD-onnx"#, r#"STD-protobuf"#, r#"STD-rdf11"#, r#"STD-spdx-3"#, r#"STD-spdx-licenses"#, r#"STD-vega-lite"#, r#"STD-w3c-prov-o"#], 0),
        (r#"community/合成数据生成域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, 1, &[r#"C03-01"#, r#"C03-02"#, r#"C03-03"#, r#"C03-04"#, r#"C03-05"#, r#"C03-06"#, r#"C03-07"#, r#"C03-08"#, r#"C03-09"#, r#"C03-10"#, r#"C03-11"#, r#"C03-12"#, r#"STD-cncf-otel-semconv"#, r#"STD-commonmark"#, r#"STD-creativecommons"#, r#"STD-frictionless-package"#, r#"STD-frictionless-table"#, r#"STD-ietf-bcp47"#, r#"STD-ietf-json"#, r#"STD-ietf-json-schema"#, r#"STD-mermaid"#, r#"STD-mlcommons-bench"#, r#"STD-mlcommons-croissant"#, r#"STD-onnx"#, r#"STD-protobuf"#, r#"STD-schema-org"#, r#"STD-spdx-licenses"#, r#"STD-vega-lite"#, r#"STD-w3c-tabular-data"#], 0),
        (r#"community/合规与监管域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, 1, &[r#"F02-01"#, r#"F02-02"#, r#"F02-03"#, r#"F02-04"#, r#"F02-05"#, r#"F02-06"#, r#"F02-07"#, r#"F02-08"#, r#"F02-09"#, r#"F02-10"#, r#"F02-11"#, r#"F02-12"#, r#"STD-gdpr"#, r#"STD-ietf-json"#, r#"STD-ietf-json-schema"#, r#"STD-mermaid"#, r#"STD-nist-ai-rmf"#, r#"STD-oasis-openapi"#, r#"STD-rdf11"#, r#"STD-spdx-licenses"#, r#"STD-vega-lite"#, r#"STD-w3c-prov-o"#], 0),
        (r#"community/向量库与检索管线域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, 1, &[r#"C15-01"#, r#"C15-02"#, r#"C15-03"#, r#"C15-04"#, r#"C15-05"#, r#"C15-06"#, r#"C15-07"#, r#"C15-08"#, r#"C15-09"#, r#"C15-10"#, r#"C15-11"#, r#"C15-12"#, r#"STD-arrow"#, r#"STD-cncf-otel-semconv"#, r#"STD-frictionless-package"#, r#"STD-ietf-json-schema"#, r#"STD-mermaid"#, r#"STD-mlcommons-bench"#, r#"STD-mlcommons-croissant"#, r#"STD-nist-800-188"#, r#"STD-nist-privacy"#, r#"STD-parquet"#, r#"STD-rdf11"#, r#"STD-schema-org"#, r#"STD-vega-lite"#, r#"STD-w3c-vc"#], 0),
        (r#"community/图像生成与编辑域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, 1, &[r#"A07-01"#, r#"A07-02"#, r#"A07-03"#, r#"A07-04"#, r#"A07-05"#, r#"A07-06"#, r#"A07-07"#, r#"A07-08"#, r#"A07-09"#, r#"A07-10"#, r#"A07-11"#, r#"A07-12"#, r#"STD-c2pa-spec"#, r#"STD-cbor"#, r#"STD-cncf-cloudevents"#, r#"STD-commonmark"#, r#"STD-cose"#, r#"STD-ietf-bcp47"#, r#"STD-ietf-json"#, r#"STD-ietf-json-schema"#, r#"STD-mermaid"#, r#"STD-mlcommons-bench"#, r#"STD-onnx"#, r#"STD-protobuf"#, r#"STD-rdf11"#, r#"STD-vega-lite"#, r#"STD-w3c-prov-o"#, r#"STD-w3c-svg2"#, r#"STD-w3c-tabular-data"#, r#"STD-w3c-xml"#], 0),
        (r#"community/图像生成与视觉创作域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, 1, &[r#"E07-01"#, r#"E07-02"#, r#"E07-03"#, r#"E07-04"#, r#"E07-05"#, r#"E07-06"#, r#"E07-07"#, r#"E07-08"#, r#"E07-09"#, r#"E07-10"#, r#"E07-11"#, r#"E07-12"#, r#"STD-commonmark"#, r#"STD-creativecommons"#, r#"STD-gdpr"#, r#"STD-ietf-bcp47"#, r#"STD-ietf-json"#, r#"STD-ietf-json-schema"#, r#"STD-spdx-licenses"#, r#"STD-vega-lite"#, r#"STD-w3c-epub33"#, r#"STD-w3c-tabular-data"#, r#"STD-w3c-xml"#], 0),
        (r#"community/图像生成与视觉设计域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, 1, &[r#"B15-01"#, r#"B15-02"#, r#"B15-03"#, r#"B15-04"#, r#"B15-05"#, r#"B15-06"#, r#"B15-07"#, r#"B15-08"#, r#"B15-09"#, r#"B15-10"#, r#"B15-11"#, r#"B15-12"#, r#"STD-creativecommons"#, r#"STD-frictionless-package"#, r#"STD-frictionless-table"#, r#"STD-ietf-bcp47"#, r#"STD-ietf-json"#, r#"STD-ietf-json-schema"#, r#"STD-rdf11"#, r#"STD-spdx-licenses"#, r#"STD-vega-lite"#, r#"STD-w3c-prov-o"#, r#"STD-w3c-svg2"#, r#"STD-w3c-tabular-data"#, r#"STD-w3c-xml"#], 0),
        (r#"community/多智能体协同域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, 1, &[r#"C17-01"#, r#"C17-02"#, r#"C17-03"#, r#"C17-04"#, r#"C17-05"#, r#"C17-06"#, r#"C17-07"#, r#"C17-08"#, r#"C17-09"#, r#"C17-10"#, r#"C17-11"#, r#"C17-12"#, r#"STD-a2a"#, r#"STD-cncf-cloudevents"#, r#"STD-cncf-otel-semconv"#, r#"STD-ietf-bcp47"#, r#"STD-ietf-json"#, r#"STD-ietf-json-schema"#, r#"STD-jsonrpc"#, r#"STD-mcp"#, r#"STD-mermaid"#, r#"STD-mlcommons-bench"#, r#"STD-vega-lite"#, r#"STD-w3c-tabular-data"#], 0),
        (r#"community/多模态大模型域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, 1, &[r#"A02-01"#, r#"A02-02"#, r#"A02-03"#, r#"A02-04"#, r#"A02-05"#, r#"A02-06"#, r#"A02-07"#, r#"A02-08"#, r#"A02-09"#, r#"A02-10"#, r#"A02-11"#, r#"A02-12"#, r#"STD-commonmark"#, r#"STD-frictionless-package"#, r#"STD-frictionless-table"#, r#"STD-ietf-bcp47"#, r#"STD-ietf-json"#, r#"STD-ietf-json-schema"#, r#"STD-jsonrpc"#, r#"STD-mcp"#, r#"STD-mlcommons-bench"#, r#"STD-mlcommons-croissant"#, r#"STD-oci-image"#, r#"STD-rdf11"#, r#"STD-schema-org"#, r#"STD-vega-lite"#, r#"STD-w3c-prov-o"#, r#"STD-w3c-svg2"#, r#"STD-w3c-tabular-data"#, r#"STD-w3c-xml"#], 0),
        (r#"community/多语翻译与本地化域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, 1, &[r#"E06-01"#, r#"E06-02"#, r#"E06-03"#, r#"E06-04"#, r#"E06-05"#, r#"E06-06"#, r#"E06-07"#, r#"E06-08"#, r#"E06-09"#, r#"E06-10"#, r#"E06-11"#, r#"E06-12"#, r#"STD-commonmark"#, r#"STD-frictionless-package"#, r#"STD-frictionless-table"#, r#"STD-ietf-bcp47"#, r#"STD-ietf-json"#, r#"STD-ietf-json-schema"#, r#"STD-iso-8601"#, r#"STD-mermaid"#, r#"STD-oci-image"#, r#"STD-rdf11"#, r#"STD-rfc3339"#, r#"STD-w3c-epub33"#, r#"STD-w3c-skos"#, r#"STD-w3c-tabular-data"#, r#"STD-w3c-xml"#], 0),
        (r#"community/多轮对话与角色扮演域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, 1, &[r#"B07-01"#, r#"B07-02"#, r#"B07-03"#, r#"B07-04"#, r#"B07-05"#, r#"B07-06"#, r#"B07-07"#, r#"B07-08"#, r#"B07-09"#, r#"B07-10"#, r#"B07-11"#, r#"B07-12"#, r#"STD-commonmark"#, r#"STD-frictionless-package"#, r#"STD-frictionless-table"#, r#"STD-gfm"#, r#"STD-ietf-bcp47"#, r#"STD-ietf-ixdtf"#, r#"STD-ietf-json"#, r#"STD-ietf-json-schema"#, r#"STD-mlcommons-bench"#, r#"STD-owasp-llm"#, r#"STD-owasp-top10"#, r#"STD-rdf11"#, r#"STD-rfc3339"#, r#"STD-vega-lite"#, r#"STD-w3c-owl-time"#, r#"STD-w3c-owl2"#, r#"STD-w3c-prov-o"#, r#"STD-w3c-tabular-data"#], 0),
        (r#"community/大语言模型域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, 1, &[r#"A01-01"#, r#"A01-02"#, r#"A01-03"#, r#"A01-04"#, r#"A01-05"#, r#"A01-06"#, r#"A01-07"#, r#"A01-08"#, r#"A01-09"#, r#"A01-10"#, r#"A01-11"#, r#"A01-12"#, r#"STD-commonmark"#, r#"STD-creativecommons"#, r#"STD-gfm"#, r#"STD-ietf-bcp47"#, r#"STD-ietf-json"#, r#"STD-ietf-json-schema"#, r#"STD-mermaid"#, r#"STD-mlcommons-bench"#, r#"STD-onnx"#, r#"STD-protobuf"#, r#"STD-rdf11"#, r#"STD-spdx-licenses"#, r#"STD-w3c-prov-o"#, r#"STD-w3c-skos"#, r#"STD-w3c-tabular-data"#], 0),
        (r#"community/安全与对齐域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, 1, &[r#"F01-01"#, r#"F01-02"#, r#"F01-03"#, r#"F01-04"#, r#"F01-05"#, r#"F01-06"#, r#"F01-07"#, r#"F01-08"#, r#"F01-09"#, r#"F01-10"#, r#"F01-11"#, r#"F01-12"#, r#"STD-c2pa-spec"#, r#"STD-cbor"#, r#"STD-commonmark"#, r#"STD-cose"#, r#"STD-ietf-json"#, r#"STD-ietf-json-schema"#, r#"STD-mermaid"#, r#"STD-mlcommons-bench"#, r#"STD-owasp-llm"#, r#"STD-owasp-top10"#, r#"STD-rdf11"#, r#"STD-spdx-licenses"#, r#"STD-vega-lite"#, r#"STD-w3c-prov-o"#], 0),
        (r#"community/对话与客服域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, 1, &[r#"E18-01"#, r#"E18-02"#, r#"E18-03"#, r#"E18-04"#, r#"E18-05"#, r#"E18-06"#, r#"E18-07"#, r#"E18-08"#, r#"E18-09"#, r#"E18-10"#, r#"E18-11"#, r#"E18-12"#, r#"STD-commonmark"#, r#"STD-frictionless-package"#, r#"STD-frictionless-table"#, r#"STD-ietf-bcp47"#, r#"STD-ietf-json"#, r#"STD-ietf-json-schema"#, r#"STD-mermaid"#, r#"STD-vega-lite"#, r#"STD-w3c-epub33"#, r#"STD-w3c-tabular-data"#, r#"STD-w3c-xml"#], 0),
        (r#"community/对齐与偏好优化域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, 1, &[r#"C07-01"#, r#"C07-02"#, r#"C07-03"#, r#"C07-04"#, r#"C07-05"#, r#"C07-06"#, r#"C07-07"#, r#"C07-08"#, r#"C07-09"#, r#"C07-10"#, r#"C07-11"#, r#"C07-12"#, r#"STD-cncf-cloudevents"#, r#"STD-cncf-otel-semconv"#, r#"STD-ietf-bcp47"#, r#"STD-ietf-json"#, r#"STD-ietf-json-schema"#, r#"STD-mermaid"#, r#"STD-mlcommons-bench"#, r#"STD-onnx"#, r#"STD-owasp-llm"#, r#"STD-owasp-top10"#, r#"STD-protobuf"#, r#"STD-vega-lite"#, r#"STD-w3c-tabular-data"#], 0),
        (r#"community/嵌入与检索表示域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, 1, &[r#"A11-01"#, r#"A11-02"#, r#"A11-03"#, r#"A11-04"#, r#"A11-05"#, r#"A11-06"#, r#"A11-07"#, r#"A11-08"#, r#"A11-09"#, r#"A11-10"#, r#"A11-11"#, r#"A11-12"#, r#"STD-arrow"#, r#"STD-commonmark"#, r#"STD-frictionless-package"#, r#"STD-ietf-json-schema"#, r#"STD-mermaid"#, r#"STD-mlcommons-bench"#, r#"STD-onnx"#, r#"STD-protobuf"#, r#"STD-rdf11"#, r#"STD-vega-lite"#, r#"STD-w3c-prov-o"#], 0),
        (r#"community/平台与基础设施域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, 1, &[r#"F08-01"#, r#"F08-02"#, r#"F08-03"#, r#"F08-04"#, r#"F08-05"#, r#"F08-06"#, r#"F08-07"#, r#"F08-08"#, r#"F08-09"#, r#"F08-10"#, r#"F08-11"#, r#"F08-12"#, r#"STD-cncf-otel-semconv"#, r#"STD-ietf-json"#, r#"STD-ietf-json-schema"#, r#"STD-mermaid"#, r#"STD-mlcommons-bench"#, r#"STD-nist-ai-rmf"#, r#"STD-oasis-openapi"#, r#"STD-onnx"#, r#"STD-protobuf"#, r#"STD-rdf11"#, r#"STD-spdx-licenses"#, r#"STD-vega-lite"#, r#"STD-w3c-prov-o"#], 0),
        (r#"community/建筑与房地产域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, 1, &[r#"D15-01"#, r#"D15-02"#, r#"D15-03"#, r#"D15-04"#, r#"D15-05"#, r#"D15-06"#, r#"D15-07"#, r#"D15-08"#, r#"D15-09"#, r#"D15-10"#, r#"D15-11"#, r#"D15-12"#, r#"STD-common-criteria"#, r#"STD-ietf-bcp47"#, r#"STD-ietf-json"#, r#"STD-ietf-json-schema"#, r#"STD-mermaid"#, r#"STD-nist-ai-rmf"#, r#"STD-rdf11"#, r#"STD-vega-lite"#, r#"STD-w3c-prov-o"#, r#"STD-w3c-tabular-data"#], 0),
        (r#"community/开源与开发者生态域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, 1, &[r#"F09-01"#, r#"F09-02"#, r#"F09-03"#, r#"F09-04"#, r#"F09-05"#, r#"F09-06"#, r#"F09-07"#, r#"F09-08"#, r#"F09-09"#, r#"F09-10"#, r#"F09-11"#, r#"F09-12"#, r#"STD-commonmark"#, r#"STD-creativecommons"#, r#"STD-ietf-json"#, r#"STD-ietf-json-schema"#, r#"STD-mermaid"#, r#"STD-mlcommons-bench"#, r#"STD-nist-800-188"#, r#"STD-nist-privacy"#, r#"STD-oasis-openapi"#, r#"STD-osi-osd"#, r#"STD-owasp-llm"#, r#"STD-owasp-top10"#, r#"STD-spdx-3"#, r#"STD-spdx-licenses"#, r#"STD-vega-lite"#, r#"STD-w3c-epub33"#, r#"STD-w3c-xml"#], 0),
        (r#"community/强化学习与决策域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, 1, &[r#"A12-01"#, r#"A12-02"#, r#"A12-03"#, r#"A12-04"#, r#"A12-05"#, r#"A12-06"#, r#"A12-07"#, r#"A12-08"#, r#"A12-09"#, r#"A12-10"#, r#"A12-11"#, r#"A12-12"#, r#"STD-ietf-bcp47"#, r#"STD-ietf-json"#, r#"STD-ietf-json-schema"#, r#"STD-jsonrpc"#, r#"STD-mcp"#, r#"STD-mermaid"#, r#"STD-mlcommons-bench"#, r#"STD-nist-ai-rmf"#, r#"STD-onnx"#, r#"STD-protobuf"#, r#"STD-rdf11"#, r#"STD-vega-lite"#, r#"STD-w3c-prov-o"#, r#"STD-w3c-tabular-data"#], 0),
        (r#"community/推理优化与加速域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, 1, &[r#"C10-01"#, r#"C10-02"#, r#"C10-03"#, r#"C10-04"#, r#"C10-05"#, r#"C10-06"#, r#"C10-07"#, r#"C10-08"#, r#"C10-09"#, r#"C10-10"#, r#"C10-11"#, r#"C10-12"#, r#"STD-cncf-cloudevents"#, r#"STD-cncf-otel-semconv"#, r#"STD-commonmark"#, r#"STD-frictionless-package"#, r#"STD-frictionless-table"#, r#"STD-gfm"#, r#"STD-ietf-bcp47"#, r#"STD-ietf-json"#, r#"STD-ietf-json-schema"#, r#"STD-mermaid"#, r#"STD-mlcommons-bench"#, r#"STD-onnx"#, r#"STD-protobuf"#, r#"STD-vega-lite"#, r#"STD-w3c-tabular-data"#], 0),
        (r#"community/推理服务与部署域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, 1, &[r#"C11-01"#, r#"C11-02"#, r#"C11-03"#, r#"C11-04"#, r#"C11-05"#, r#"C11-06"#, r#"C11-07"#, r#"C11-08"#, r#"C11-09"#, r#"C11-10"#, r#"C11-11"#, r#"C11-12"#, r#"STD-a2a"#, r#"STD-cncf-cloudevents"#, r#"STD-cncf-otel-otlp"#, r#"STD-cncf-otel-semconv"#, r#"STD-commonmark"#, r#"STD-gfm"#, r#"STD-ietf-bcp47"#, r#"STD-ietf-json"#, r#"STD-ietf-json-schema"#, r#"STD-k8s-crd"#, r#"STD-mermaid"#, r#"STD-oasis-openapi"#, r#"STD-onnx"#, r#"STD-protobuf"#, r#"STD-vega-lite"#, r#"STD-w3c-tabular-data"#], 0),
        (r#"community/推荐排序与广告域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, 1, &[r#"B17-01"#, r#"B17-02"#, r#"B17-03"#, r#"B17-04"#, r#"B17-05"#, r#"B17-06"#, r#"B17-07"#, r#"B17-08"#, r#"B17-09"#, r#"B17-10"#, r#"B17-11"#, r#"B17-12"#, r#"STD-cncf-cloudevents"#, r#"STD-commonmark"#, r#"STD-frictionless-package"#, r#"STD-frictionless-table"#, r#"STD-ietf-bcp47"#, r#"STD-ietf-json"#, r#"STD-ietf-json-schema"#, r#"STD-mlcommons-bench"#, r#"STD-onnx"#, r#"STD-protobuf"#, r#"STD-rdf11"#, r#"STD-vega-lite"#, r#"STD-w3c-prov-o"#, r#"STD-w3c-tabular-data"#], 0),
        (r#"community/提示工程与指令设计域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, 1, &[r#"E01-01"#, r#"E01-02"#, r#"E01-03"#, r#"E01-04"#, r#"E01-05"#, r#"E01-06"#, r#"E01-07"#, r#"E01-08"#, r#"E01-09"#, r#"E01-10"#, r#"E01-11"#, r#"E01-12"#, r#"STD-a2a"#, r#"STD-commonmark"#, r#"STD-gfm"#, r#"STD-ietf-bcp47"#, r#"STD-ietf-json"#, r#"STD-ietf-json-schema"#, r#"STD-mlcommons-bench"#, r#"STD-onnx"#, r#"STD-protobuf"#, r#"STD-w3c-epub33"#, r#"STD-w3c-tabular-data"#, r#"STD-w3c-xml"#], 0),
        (r#"community/提示工程与提示模板域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, 1, &[r#"C13-01"#, r#"C13-02"#, r#"C13-03"#, r#"C13-04"#, r#"C13-05"#, r#"C13-06"#, r#"C13-07"#, r#"C13-08"#, r#"C13-09"#, r#"C13-10"#, r#"C13-11"#, r#"C13-12"#, r#"STD-cncf-otel-semconv"#, r#"STD-commonmark"#, r#"STD-frictionless-package"#, r#"STD-frictionless-table"#, r#"STD-ietf-bcp47"#, r#"STD-ietf-json"#, r#"STD-ietf-json-schema"#, r#"STD-mlcommons-bench"#, r#"STD-vega-lite"#, r#"STD-w3c-tabular-data"#], 0),
        (r#"community/搜索与信息聚合域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, 1, &[r#"E17-01"#, r#"E17-02"#, r#"E17-03"#, r#"E17-04"#, r#"E17-05"#, r#"E17-06"#, r#"E17-07"#, r#"E17-08"#, r#"E17-09"#, r#"E17-10"#, r#"E17-11"#, r#"E17-12"#, r#"STD-cncf-otel-semconv"#, r#"STD-commonmark"#, r#"STD-frictionless-package"#, r#"STD-frictionless-table"#, r#"STD-ietf-bcp47"#, r#"STD-ietf-ixdtf"#, r#"STD-ietf-json"#, r#"STD-ietf-json-schema"#, r#"STD-rfc3339"#, r#"STD-vega-lite"#, r#"STD-w3c-epub33"#, r#"STD-w3c-tabular-data"#, r#"STD-w3c-xml"#], 0),
        (r#"community/摘要与信息压缩域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, 1, &[r#"B02-01"#, r#"B02-02"#, r#"B02-03"#, r#"B02-04"#, r#"B02-05"#, r#"B02-06"#, r#"B02-07"#, r#"B02-08"#, r#"B02-09"#, r#"B02-10"#, r#"B02-11"#, r#"B02-12"#, r#"STD-commonmark"#, r#"STD-frictionless-package"#, r#"STD-frictionless-table"#, r#"STD-ietf-bcp47"#, r#"STD-ietf-json"#, r#"STD-ietf-json-schema"#, r#"STD-mlcommons-bench"#, r#"STD-rdf11"#, r#"STD-vega-lite"#, r#"STD-w3c-epub33"#, r#"STD-w3c-prov-o"#, r#"STD-w3c-tabular-data"#, r#"STD-w3c-xml"#], 0),
        (r#"community/数字人与虚拟形象域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, 1, &[r#"E20-01"#, r#"E20-02"#, r#"E20-03"#, r#"E20-04"#, r#"E20-05"#, r#"E20-06"#, r#"E20-07"#, r#"E20-08"#, r#"E20-09"#, r#"E20-10"#, r#"E20-11"#, r#"E20-12"#, r#"STD-cncf-otel-semconv"#, r#"STD-commonmark"#, r#"STD-gdpr"#, r#"STD-ietf-bcp47"#, r#"STD-ietf-json"#, r#"STD-ietf-json-schema"#, r#"STD-khronos-gltf"#, r#"STD-mermaid"#, r#"STD-vega-lite"#, r#"STD-w3c-tabular-data"#, r#"STD-w3c-webaudio"#], 0),
        (r#"community/数学与形式化推理域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, 1, &[r#"A10-01"#, r#"A10-02"#, r#"A10-03"#, r#"A10-04"#, r#"A10-05"#, r#"A10-06"#, r#"A10-07"#, r#"A10-08"#, r#"A10-09"#, r#"A10-10"#, r#"A10-11"#, r#"A10-12"#, r#"STD-cncf-otel-semconv"#, r#"STD-ieee-754"#, r#"STD-ietf-bcp47"#, r#"STD-ietf-json"#, r#"STD-ietf-json-schema"#, r#"STD-mlcommons-bench"#, r#"STD-onnx"#, r#"STD-peps"#, r#"STD-protobuf"#, r#"STD-rdf11"#, r#"STD-rst-docutils"#, r#"STD-vega-lite"#, r#"STD-w3c-mathml3"#, r#"STD-w3c-prov-o"#, r#"STD-w3c-tabular-data"#, r#"STD-w3c-xml"#], 0),
        (r#"community/数据分析与决策支持域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, 1, &[r#"E14-01"#, r#"E14-02"#, r#"E14-03"#, r#"E14-04"#, r#"E14-05"#, r#"E14-06"#, r#"E14-07"#, r#"E14-08"#, r#"E14-09"#, r#"E14-10"#, r#"E14-11"#, r#"E14-12"#, r#"STD-cncf-otel-semconv"#, r#"STD-commonmark"#, r#"STD-frictionless-package"#, r#"STD-frictionless-table"#, r#"STD-ietf-bcp47"#, r#"STD-ietf-json"#, r#"STD-ietf-json-schema"#, r#"STD-mermaid"#, r#"STD-vega-lite"#, r#"STD-w3c-epub33"#, r#"STD-w3c-tabular-data"#, r#"STD-w3c-xml"#], 0),
        (r#"community/数据分析与表格理解域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, 1, &[r#"B11-01"#, r#"B11-02"#, r#"B11-03"#, r#"B11-04"#, r#"B11-05"#, r#"B11-06"#, r#"B11-07"#, r#"B11-08"#, r#"B11-09"#, r#"B11-10"#, r#"B11-11"#, r#"B11-12"#, r#"STD-cncf-otel-semconv"#, r#"STD-commonmark"#, r#"STD-frictionless-package"#, r#"STD-frictionless-table"#, r#"STD-ietf-bcp47"#, r#"STD-ietf-json"#, r#"STD-ietf-json-schema"#, r#"STD-nist-800-188"#, r#"STD-nist-privacy"#, r#"STD-onnx"#, r#"STD-protobuf"#, r#"STD-rdf11"#, r#"STD-vega-lite"#, r#"STD-w3c-prov-o"#, r#"STD-w3c-tabular-data"#, r#"STD-w3c-vc"#], 0),
        (r#"community/数据标注与标注质量域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, 1, &[r#"C02-01"#, r#"C02-02"#, r#"C02-03"#, r#"C02-04"#, r#"C02-05"#, r#"C02-06"#, r#"C02-07"#, r#"C02-08"#, r#"C02-09"#, r#"C02-10"#, r#"C02-11"#, r#"C02-12"#, r#"STD-cncf-otel-semconv"#, r#"STD-frictionless-package"#, r#"STD-frictionless-table"#, r#"STD-gdpr"#, r#"STD-ietf-json-schema"#, r#"STD-mermaid"#, r#"STD-mlcommons-bench"#, r#"STD-mlcommons-croissant"#, r#"STD-schema-org"#, r#"STD-vega-lite"#], 0),
        (r#"community/数据采集与清洗域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, 1, &[r#"C01-01"#, r#"C01-02"#, r#"C01-03"#, r#"C01-04"#, r#"C01-05"#, r#"C01-06"#, r#"C01-07"#, r#"C01-08"#, r#"C01-09"#, r#"C01-10"#, r#"C01-11"#, r#"C01-12"#, r#"STD-cncf-otel-semconv"#, r#"STD-frictionless-package"#, r#"STD-frictionless-table"#, r#"STD-gdpr"#, r#"STD-ietf-bcp47"#, r#"STD-ietf-json"#, r#"STD-ietf-json-schema"#, r#"STD-mermaid"#, r#"STD-rdf11"#, r#"STD-vega-lite"#, r#"STD-w3c-prov-o"#, r#"STD-w3c-tabular-data"#], 0),
        (r#"community/文旅与酒店域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, 1, &[r#"D19-01"#, r#"D19-02"#, r#"D19-03"#, r#"D19-04"#, r#"D19-05"#, r#"D19-06"#, r#"D19-07"#, r#"D19-08"#, r#"D19-09"#, r#"D19-10"#, r#"D19-11"#, r#"D19-12"#, r#"STD-cncf-cloudevents"#, r#"STD-common-criteria"#, r#"STD-frictionless-package"#, r#"STD-frictionless-table"#, r#"STD-ietf-bcp47"#, r#"STD-ietf-json"#, r#"STD-ietf-json-schema"#, r#"STD-mermaid"#, r#"STD-nist-ai-rmf"#, r#"STD-oasis-openapi"#, r#"STD-owasp-llm"#, r#"STD-owasp-top10"#, r#"STD-rdf11"#, r#"STD-vega-lite"#, r#"STD-w3c-prov-o"#, r#"STD-w3c-tabular-data"#], 0),
        (r#"community/文本生成与创作域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, 1, &[r#"B01-01"#, r#"B01-02"#, r#"B01-03"#, r#"B01-04"#, r#"B01-05"#, r#"B01-06"#, r#"B01-07"#, r#"B01-08"#, r#"B01-09"#, r#"B01-10"#, r#"B01-11"#, r#"B01-12"#, r#"STD-commonmark"#, r#"STD-frictionless-package"#, r#"STD-frictionless-table"#, r#"STD-ietf-bcp47"#, r#"STD-ietf-json"#, r#"STD-ietf-json-schema"#, r#"STD-rdf11"#, r#"STD-vega-lite"#, r#"STD-w3c-prov-o"#, r#"STD-w3c-tabular-data"#], 0),
        (r#"community/文档解析与版面理解域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, 1, &[r#"B12-01"#, r#"B12-02"#, r#"B12-03"#, r#"B12-04"#, r#"B12-05"#, r#"B12-06"#, r#"B12-07"#, r#"B12-08"#, r#"B12-09"#, r#"B12-10"#, r#"B12-11"#, r#"B12-12"#, r#"STD-commonmark"#, r#"STD-ietf-bcp47"#, r#"STD-ietf-json"#, r#"STD-ietf-json-schema"#, r#"STD-rdf11"#, r#"STD-vega-lite"#, r#"STD-w3c-epub33"#, r#"STD-w3c-mathml3"#, r#"STD-w3c-prov-o"#, r#"STD-w3c-tabular-data"#, r#"STD-w3c-xml"#], 0),
        (r#"community/智能体与工作流编排域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, 1, &[r#"E12-01"#, r#"E12-02"#, r#"E12-03"#, r#"E12-04"#, r#"E12-05"#, r#"E12-06"#, r#"E12-07"#, r#"E12-08"#, r#"E12-09"#, r#"E12-10"#, r#"E12-11"#, r#"E12-12"#, r#"STD-a2a"#, r#"STD-cncf-cloudevents"#, r#"STD-cncf-otel-semconv"#, r#"STD-commonmark"#, r#"STD-ietf-bcp47"#, r#"STD-ietf-json"#, r#"STD-ietf-json-schema"#, r#"STD-jsonrpc"#, r#"STD-mcp"#, r#"STD-vega-lite"#, r#"STD-w3c-epub33"#, r#"STD-w3c-tabular-data"#, r#"STD-w3c-xml"#], 0),
        (r#"community/智能体框架与工具调用域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, 1, &[r#"C16-01"#, r#"C16-02"#, r#"C16-03"#, r#"C16-04"#, r#"C16-05"#, r#"C16-06"#, r#"C16-07"#, r#"C16-08"#, r#"C16-09"#, r#"C16-10"#, r#"C16-11"#, r#"C16-12"#, r#"STD-cncf-otel-semconv"#, r#"STD-ietf-json"#, r#"STD-ietf-json-schema"#, r#"STD-jsonrpc"#, r#"STD-mcp"#, r#"STD-mermaid"#, r#"STD-mlcommons-bench"#, r#"STD-nist-800-188"#, r#"STD-nist-privacy"#, r#"STD-oasis-openapi"#, r#"STD-rdf11"#, r#"STD-vega-lite"#, r#"STD-w3c-vc"#], 0),
        (r#"community/机器翻译与本地化域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, 1, &[r#"B03-01"#, r#"B03-02"#, r#"B03-03"#, r#"B03-04"#, r#"B03-05"#, r#"B03-06"#, r#"B03-07"#, r#"B03-08"#, r#"B03-09"#, r#"B03-10"#, r#"B03-11"#, r#"B03-12"#, r#"STD-commonmark"#, r#"STD-frictionless-package"#, r#"STD-frictionless-table"#, r#"STD-gdpr"#, r#"STD-ietf-bcp47"#, r#"STD-ietf-json"#, r#"STD-ietf-json-schema"#, r#"STD-oci-image"#, r#"STD-rdf11"#, r#"STD-vega-lite"#, r#"STD-w3c-prov-o"#, r#"STD-w3c-skos"#, r#"STD-w3c-tabular-data"#], 0),
        (r#"community/模型运营与成本域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, 1, &[r#"F07-01"#, r#"F07-02"#, r#"F07-03"#, r#"F07-04"#, r#"F07-05"#, r#"F07-06"#, r#"F07-07"#, r#"F07-08"#, r#"F07-09"#, r#"F07-10"#, r#"F07-11"#, r#"F07-12"#, r#"STD-cncf-otel-semconv"#, r#"STD-commonmark"#, r#"STD-gfm"#, r#"STD-ietf-json"#, r#"STD-ietf-json-schema"#, r#"STD-mermaid"#, r#"STD-nist-ai-rmf"#, r#"STD-oasis-openapi"#, r#"STD-onnx"#, r#"STD-protobuf"#, r#"STD-rdf11"#, r#"STD-spdx-licenses"#, r#"STD-vega-lite"#, r#"STD-w3c-prov-o"#], 0),
        (r#"community/测试与用例生成域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, 1, &[r#"B10-01"#, r#"B10-02"#, r#"B10-03"#, r#"B10-04"#, r#"B10-05"#, r#"B10-06"#, r#"B10-07"#, r#"B10-08"#, r#"B10-09"#, r#"B10-10"#, r#"B10-11"#, r#"B10-12"#, r#"STD-a2a"#, r#"STD-commonmark"#, r#"STD-ietf-bcp47"#, r#"STD-ietf-json"#, r#"STD-ietf-json-schema"#, r#"STD-nist-800-142"#, r#"STD-oasis-openapi"#, r#"STD-peps"#, r#"STD-rdf11"#, r#"STD-rst-docutils"#, r#"STD-vega-lite"#, r#"STD-w3c-prov-o"#, r#"STD-w3c-tabular-data"#], 0),
        (r#"community/游戏与互动娱乐域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, 1, &[r#"D18-01"#, r#"D18-02"#, r#"D18-03"#, r#"D18-04"#, r#"D18-05"#, r#"D18-06"#, r#"D18-07"#, r#"D18-08"#, r#"D18-09"#, r#"D18-10"#, r#"D18-11"#, r#"D18-12"#, r#"STD-common-criteria"#, r#"STD-ieee-754"#, r#"STD-ietf-bcp47"#, r#"STD-ietf-json"#, r#"STD-ietf-json-schema"#, r#"STD-mermaid"#, r#"STD-nist-ai-rmf"#, r#"STD-rdf11"#, r#"STD-vega-lite"#, r#"STD-w3c-prov-o"#, r#"STD-w3c-tabular-data"#], 0),
        (r#"community/版权与知识产权域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, 1, &[r#"F04-01"#, r#"F04-02"#, r#"F04-03"#, r#"F04-04"#, r#"F04-05"#, r#"F04-06"#, r#"F04-07"#, r#"F04-08"#, r#"F04-09"#, r#"F04-10"#, r#"F04-11"#, r#"F04-12"#, r#"STD-creativecommons"#, r#"STD-gdpr"#, r#"STD-ietf-bcp47"#, r#"STD-ietf-json"#, r#"STD-ietf-json-schema"#, r#"STD-mermaid"#, r#"STD-mlcommons-bench"#, r#"STD-nist-ai-rmf"#, r#"STD-rdf11"#, r#"STD-spdx-licenses"#, r#"STD-vega-lite"#, r#"STD-w3c-prov-o"#, r#"STD-w3c-tabular-data"#], 0),
        (r#"community/物流与供应链域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, 1, &[r#"D12-01"#, r#"D12-02"#, r#"D12-03"#, r#"D12-04"#, r#"D12-05"#, r#"D12-06"#, r#"D12-07"#, r#"D12-08"#, r#"D12-09"#, r#"D12-10"#, r#"D12-11"#, r#"D12-12"#, r#"STD-cncf-otel-semconv"#, r#"STD-frictionless-package"#, r#"STD-frictionless-table"#, r#"STD-gdpr"#, r#"STD-ietf-bcp47"#, r#"STD-ietf-json"#, r#"STD-ietf-json-schema"#, r#"STD-mermaid"#, r#"STD-nist-ai-rmf"#, r#"STD-rdf11"#, r#"STD-spdx-3"#, r#"STD-vega-lite"#, r#"STD-w3c-prov-o"#, r#"STD-w3c-tabular-data"#, r#"STD-w3c-wot"#], 0),
        (r#"community/监督微调域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, 1, &[r#"C05-01"#, r#"C05-02"#, r#"C05-03"#, r#"C05-04"#, r#"C05-05"#, r#"C05-06"#, r#"C05-07"#, r#"C05-08"#, r#"C05-09"#, r#"C05-10"#, r#"C05-11"#, r#"C05-12"#, r#"STD-cncf-otel-semconv"#, r#"STD-commonmark"#, r#"STD-creativecommons"#, r#"STD-frictionless-package"#, r#"STD-frictionless-table"#, r#"STD-ietf-bcp47"#, r#"STD-ietf-json"#, r#"STD-ietf-json-schema"#, r#"STD-mermaid"#, r#"STD-mlcommons-bench"#, r#"STD-mlcommons-croissant"#, r#"STD-schema-org"#, r#"STD-spdx-licenses"#, r#"STD-vega-lite"#, r#"STD-w3c-tabular-data"#], 0),
        (r#"community/知识管理与检索增强域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, 1, &[r#"E11-01"#, r#"E11-02"#, r#"E11-03"#, r#"E11-04"#, r#"E11-05"#, r#"E11-06"#, r#"E11-07"#, r#"E11-08"#, r#"E11-09"#, r#"E11-10"#, r#"E11-11"#, r#"E11-12"#, r#"STD-c2pa-spec"#, r#"STD-cbor"#, r#"STD-commonmark"#, r#"STD-cose"#, r#"STD-frictionless-package"#, r#"STD-frictionless-table"#, r#"STD-ietf-bcp47"#, r#"STD-ietf-json"#, r#"STD-ietf-json-schema"#, r#"STD-mermaid"#, r#"STD-mlcommons-bench"#, r#"STD-nist-800-188"#, r#"STD-nist-privacy"#, r#"STD-onnx"#, r#"STD-protobuf"#, r#"STD-rdf11"#, r#"STD-vega-lite"#, r#"STD-w3c-prov-o"#, r#"STD-w3c-tabular-data"#, r#"STD-w3c-vc"#], 0),
        (r#"community/知识问答与检索增强域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, 1, &[r#"B06-01"#, r#"B06-02"#, r#"B06-03"#, r#"B06-04"#, r#"B06-05"#, r#"B06-06"#, r#"B06-07"#, r#"B06-08"#, r#"B06-09"#, r#"B06-10"#, r#"B06-11"#, r#"B06-12"#, r#"STD-commonmark"#, r#"STD-frictionless-package"#, r#"STD-frictionless-table"#, r#"STD-gfm"#, r#"STD-ietf-bcp47"#, r#"STD-ietf-json"#, r#"STD-ietf-json-schema"#, r#"STD-mlcommons-bench"#, r#"STD-vega-lite"#, r#"STD-w3c-tabular-data"#], 0),
        (r#"community/科研与实验域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, 1, &[r#"D20-01"#, r#"D20-02"#, r#"D20-03"#, r#"D20-04"#, r#"D20-05"#, r#"D20-06"#, r#"D20-07"#, r#"D20-08"#, r#"D20-09"#, r#"D20-10"#, r#"D20-11"#, r#"D20-12"#, r#"STD-bagit"#, r#"STD-commonmark"#, r#"STD-datacite"#, r#"STD-frictionless-package"#, r#"STD-ietf-bcp47"#, r#"STD-ietf-json"#, r#"STD-ietf-json-schema"#, r#"STD-mermaid"#, r#"STD-nist-ai-rmf"#, r#"STD-rdf11"#, r#"STD-rocrate"#, r#"STD-vega-lite"#, r#"STD-w3c-json-ld"#, r#"STD-w3c-prov-o"#, r#"STD-w3c-tabular-data"#, r#"STD-w3c-xml"#], 0),
        (r#"community/端侧与边缘小模型域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, 1, &[r#"A14-01"#, r#"A14-02"#, r#"A14-03"#, r#"A14-04"#, r#"A14-05"#, r#"A14-06"#, r#"A14-07"#, r#"A14-08"#, r#"A14-09"#, r#"A14-10"#, r#"A14-11"#, r#"A14-12"#, r#"STD-a2a"#, r#"STD-covesa-vss"#, r#"STD-gdpr"#, r#"STD-ieee-754"#, r#"STD-ietf-bcp47"#, r#"STD-ietf-json"#, r#"STD-ietf-json-schema"#, r#"STD-jose"#, r#"STD-jsonrpc"#, r#"STD-mcp"#, r#"STD-mermaid"#, r#"STD-mlcommons-bench"#, r#"STD-oasis-openapi"#, r#"STD-onnx"#, r#"STD-owasp-llm"#, r#"STD-owasp-top10"#, r#"STD-protobuf"#, r#"STD-rdf11"#, r#"STD-uptane"#, r#"STD-vega-lite"#, r#"STD-w3c-prov-o"#, r#"STD-w3c-tabular-data"#], 0),
        (r#"community/红队越狱与安全测试域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, 1, &[r#"C09-01"#, r#"C09-02"#, r#"C09-03"#, r#"C09-04"#, r#"C09-05"#, r#"C09-06"#, r#"C09-07"#, r#"C09-08"#, r#"C09-09"#, r#"C09-10"#, r#"C09-11"#, r#"C09-12"#, r#"STD-cncf-otel-semconv"#, r#"STD-commonmark"#, r#"STD-cwe"#, r#"STD-frictionless-package"#, r#"STD-frictionless-table"#, r#"STD-ietf-bcp47"#, r#"STD-ietf-json"#, r#"STD-ietf-json-schema"#, r#"STD-mermaid"#, r#"STD-mlcommons-bench"#, r#"STD-owasp-llm"#, r#"STD-owasp-top10"#, r#"STD-vega-lite"#, r#"STD-w3c-tabular-data"#], 0),
        (r#"community/组合包-受监管行业/outputs/DEPENDENCY.graphml"#, r#"graphml"#, 1, &[r#"AI法律与合规:M01"#, r#"AI法律与合规:M02"#, r#"AI金融投研与风控:M01"#, r#"AI金融投研与风控:M02"#, r#"可解释性与审计:M01"#, r#"可解释性与审计:M02"#, r#"隐私与数据治理:M01"#, r#"隐私与数据治理:M02"#], 0),
        (r#"community/组合包-数据管线/outputs/DEPENDENCY.graphml"#, r#"graphml"#, 1, &[r#"合成数据生成:M01"#, r#"合成数据生成:M02"#, r#"数据采集与清洗:M01"#, r#"数据采集与清洗:M02"#, r#"评测基准与排行榜:M01"#, r#"评测基准与排行榜:M02"#, r#"预训练与继续预训练:M01"#, r#"预训练与继续预训练:M02"#], 0),
        (r#"community/组合包-检索栈/outputs/DEPENDENCY.graphml"#, r#"graphml"#, 1, &[r#"向量库与检索管线:M01"#, r#"向量库与检索管线:M02"#, r#"大语言模型:M01"#, r#"大语言模型:M02"#, r#"嵌入与检索表示:M01"#, r#"嵌入与检索表示:M02"#], 0),
        (r#"community/组合包-轻混与保险/outputs/DEPENDENCY.graphml"#, r#"graphml"#, 1, &[r#"AI保险:M01"#, r#"AI保险:M02"#, r#"M07"#, r#"M09"#, r#"M17"#, r#"M22"#, r#"M40"#, r#"M41"#, r#"M43"#, r#"M55"#, r#"M91"#, r#"M92"#], 0),
        (r#"community/编辑校对与出版域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, 1, &[r#"E10-01"#, r#"E10-02"#, r#"E10-03"#, r#"E10-04"#, r#"E10-05"#, r#"E10-06"#, r#"E10-07"#, r#"E10-08"#, r#"E10-09"#, r#"E10-10"#, r#"E10-11"#, r#"E10-12"#, r#"STD-cncf-cloudevents"#, r#"STD-commonmark"#, r#"STD-creativecommons"#, r#"STD-ietf-bcp47"#, r#"STD-ietf-json"#, r#"STD-ietf-json-schema"#, r#"STD-mermaid"#, r#"STD-mlcommons-croissant"#, r#"STD-schema-org"#, r#"STD-spdx-licenses"#, r#"STD-vega-lite"#, r#"STD-w3c-epub-a11y"#, r#"STD-w3c-epub33"#, r#"STD-w3c-tabular-data"#, r#"STD-w3c-xml"#], 0),
        (r#"community/视觉模型域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, 1, &[r#"A03-01"#, r#"A03-02"#, r#"A03-03"#, r#"A03-04"#, r#"A03-05"#, r#"A03-06"#, r#"A03-07"#, r#"A03-08"#, r#"A03-09"#, r#"A03-10"#, r#"A03-11"#, r#"A03-12"#, r#"STD-cwe"#, r#"STD-dicom"#, r#"STD-ietf-bcp47"#, r#"STD-ietf-json"#, r#"STD-ietf-json-schema"#, r#"STD-mermaid"#, r#"STD-mlcommons-bench"#, r#"STD-oci-image"#, r#"STD-onnx"#, r#"STD-opengeospatial"#, r#"STD-protobuf"#, r#"STD-rdf11"#, r#"STD-vega-lite"#, r#"STD-w3c-prov-o"#, r#"STD-w3c-svg2"#, r#"STD-w3c-tabular-data"#, r#"STD-w3c-xml"#], 0),
        (r#"community/视频生成与剪辑域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, 1, &[r#"E08-01"#, r#"E08-02"#, r#"E08-03"#, r#"E08-04"#, r#"E08-05"#, r#"E08-06"#, r#"E08-07"#, r#"E08-08"#, r#"E08-09"#, r#"E08-10"#, r#"E08-11"#, r#"E08-12"#, r#"STD-commonmark"#, r#"STD-frictionless-package"#, r#"STD-ietf-bcp47"#, r#"STD-ietf-json"#, r#"STD-ietf-json-schema"#, r#"STD-mermaid"#, r#"STD-oci-image"#, r#"STD-vega-lite"#, r#"STD-w3c-epub33"#, r#"STD-w3c-tabular-data"#, r#"STD-w3c-xml"#], 0),
        (r#"community/视频生成与理解域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, 1, &[r#"A06-01"#, r#"A06-02"#, r#"A06-03"#, r#"A06-04"#, r#"A06-05"#, r#"A06-06"#, r#"A06-07"#, r#"A06-08"#, r#"A06-09"#, r#"A06-10"#, r#"A06-11"#, r#"A06-12"#, r#"STD-ietf-bcp47"#, r#"STD-ietf-ixdtf"#, r#"STD-ietf-json"#, r#"STD-ietf-json-schema"#, r#"STD-mermaid"#, r#"STD-mlcommons-bench"#, r#"STD-oci-image"#, r#"STD-rdf11"#, r#"STD-rfc3339"#, r#"STD-vega-lite"#, r#"STD-w3c-owl-time"#, r#"STD-w3c-owl2"#, r#"STD-w3c-prov-o"#, r#"STD-w3c-tabular-data"#], 0),
        (r#"community/视频生成与自动剪辑域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, 1, &[r#"B16-01"#, r#"B16-02"#, r#"B16-03"#, r#"B16-04"#, r#"B16-05"#, r#"B16-06"#, r#"B16-07"#, r#"B16-08"#, r#"B16-09"#, r#"B16-10"#, r#"B16-11"#, r#"B16-12"#, r#"STD-commonmark"#, r#"STD-frictionless-package"#, r#"STD-frictionless-table"#, r#"STD-gdpr"#, r#"STD-ietf-bcp47"#, r#"STD-ietf-json"#, r#"STD-ietf-json-schema"#, r#"STD-oci-image"#, r#"STD-rdf11"#, r#"STD-vega-lite"#, r#"STD-w3c-prov-o"#, r#"STD-w3c-tabular-data"#], 0),
        (r#"community/角色扮演与角色卡域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, 1, &[r#"E02-01"#, r#"E02-02"#, r#"E02-03"#, r#"E02-04"#, r#"E02-05"#, r#"E02-06"#, r#"E02-07"#, r#"E02-08"#, r#"E02-09"#, r#"E02-10"#, r#"E02-11"#, r#"E02-12"#, r#"STD-commonmark"#, r#"STD-ietf-bcp47"#, r#"STD-ietf-json"#, r#"STD-ietf-json-schema"#, r#"STD-mermaid"#, r#"STD-mlcommons-bench"#, r#"STD-owasp-llm"#, r#"STD-owasp-top10"#, r#"STD-vega-lite"#, r#"STD-w3c-epub33"#, r#"STD-w3c-tabular-data"#, r#"STD-w3c-xml"#], 0),
        (r#"community/记忆体与个性化域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, 1, &[r#"C14-01"#, r#"C14-02"#, r#"C14-03"#, r#"C14-04"#, r#"C14-05"#, r#"C14-06"#, r#"C14-07"#, r#"C14-08"#, r#"C14-09"#, r#"C14-10"#, r#"C14-11"#, r#"C14-12"#, r#"STD-cncf-otel-semconv"#, r#"STD-creativecommons"#, r#"STD-frictionless-package"#, r#"STD-frictionless-table"#, r#"STD-ietf-bcp47"#, r#"STD-ietf-json"#, r#"STD-ietf-json-schema"#, r#"STD-mermaid"#, r#"STD-mlcommons-bench"#, r#"STD-spdx-licenses"#, r#"STD-vega-lite"#, r#"STD-w3c-tabular-data"#], 0),
        (r#"community/评测与基准域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, 1, &[r#"F05-01"#, r#"F05-02"#, r#"F05-03"#, r#"F05-04"#, r#"F05-05"#, r#"F05-06"#, r#"F05-07"#, r#"F05-08"#, r#"F05-09"#, r#"F05-10"#, r#"F05-11"#, r#"F05-12"#, r#"STD-commonmark"#, r#"STD-frictionless-package"#, r#"STD-frictionless-table"#, r#"STD-ietf-json"#, r#"STD-ietf-json-schema"#, r#"STD-mermaid"#, r#"STD-mlcommons-bench"#, r#"STD-nist-800-188"#, r#"STD-nist-ai-rmf"#, r#"STD-nist-privacy"#, r#"STD-owasp-llm"#, r#"STD-owasp-top10"#, r#"STD-rdf11"#, r#"STD-spdx-3"#, r#"STD-vega-lite"#, r#"STD-w3c-prov-o"#], 0),
        (r#"community/评测基准与排行榜域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, 1, &[r#"C08-01"#, r#"C08-02"#, r#"C08-03"#, r#"C08-04"#, r#"C08-05"#, r#"C08-06"#, r#"C08-07"#, r#"C08-08"#, r#"C08-09"#, r#"C08-10"#, r#"C08-11"#, r#"C08-12"#, r#"STD-cncf-otel-semconv"#, r#"STD-ietf-bcp47"#, r#"STD-ietf-json"#, r#"STD-ietf-json-schema"#, r#"STD-mermaid"#, r#"STD-mlcommons-bench"#, r#"STD-oasis-sarif"#, r#"STD-vega-lite"#, r#"STD-w3c-tabular-data"#], 0),
        (r#"community/语音合成与配音域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, 1, &[r#"B14-01"#, r#"B14-02"#, r#"B14-03"#, r#"B14-04"#, r#"B14-05"#, r#"B14-06"#, r#"B14-07"#, r#"B14-08"#, r#"B14-09"#, r#"B14-10"#, r#"B14-11"#, r#"B14-12"#, r#"STD-commonmark"#, r#"STD-creativecommons"#, r#"STD-frictionless-package"#, r#"STD-frictionless-table"#, r#"STD-ietf-bcp47"#, r#"STD-ietf-json"#, r#"STD-ietf-json-schema"#, r#"STD-mlcommons-bench"#, r#"STD-rdf11"#, r#"STD-spdx-licenses"#, r#"STD-vega-lite"#, r#"STD-w3c-prov-o"#, r#"STD-w3c-tabular-data"#, r#"STD-w3c-webaudio"#], 0),
        (r#"community/语音识别与合成域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, 1, &[r#"A04-01"#, r#"A04-02"#, r#"A04-03"#, r#"A04-04"#, r#"A04-05"#, r#"A04-06"#, r#"A04-07"#, r#"A04-08"#, r#"A04-09"#, r#"A04-10"#, r#"A04-11"#, r#"A04-12"#, r#"STD-cncf-cloudevents"#, r#"STD-ietf-bcp47"#, r#"STD-ietf-ixdtf"#, r#"STD-ietf-json"#, r#"STD-ietf-json-schema"#, r#"STD-mermaid"#, r#"STD-mlcommons-bench"#, r#"STD-oci-image"#, r#"STD-onnx"#, r#"STD-protobuf"#, r#"STD-rdf11"#, r#"STD-rfc3339"#, r#"STD-vega-lite"#, r#"STD-w3c-prov-o"#, r#"STD-w3c-tabular-data"#, r#"STD-w3c-webaudio"#], 0),
        (r#"community/语音转写与会议记录域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, 1, &[r#"B13-01"#, r#"B13-02"#, r#"B13-03"#, r#"B13-04"#, r#"B13-05"#, r#"B13-06"#, r#"B13-07"#, r#"B13-08"#, r#"B13-09"#, r#"B13-10"#, r#"B13-11"#, r#"B13-12"#, r#"STD-commonmark"#, r#"STD-frictionless-package"#, r#"STD-frictionless-table"#, r#"STD-gdpr"#, r#"STD-ietf-bcp47"#, r#"STD-ietf-ixdtf"#, r#"STD-ietf-json"#, r#"STD-ietf-json-schema"#, r#"STD-iso-8601"#, r#"STD-mlcommons-bench"#, r#"STD-rdf11"#, r#"STD-rfc3339"#, r#"STD-vega-lite"#, r#"STD-w3c-prov-o"#, r#"STD-w3c-skos"#, r#"STD-w3c-tabular-data"#, r#"STD-w3c-webaudio"#], 0),
        (r#"community/长文本与小说创作域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, 1, &[r#"E04-01"#, r#"E04-02"#, r#"E04-03"#, r#"E04-04"#, r#"E04-05"#, r#"E04-06"#, r#"E04-07"#, r#"E04-08"#, r#"E04-09"#, r#"E04-10"#, r#"E04-11"#, r#"E04-12"#, r#"STD-commonmark"#, r#"STD-ietf-bcp47"#, r#"STD-ietf-json"#, r#"STD-ietf-json-schema"#, r#"STD-mermaid"#, r#"STD-vega-lite"#, r#"STD-w3c-epub33"#, r#"STD-w3c-tabular-data"#, r#"STD-w3c-xml"#], 0),
        (r#"community/隐私与数据治理域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, 1, &[r#"F03-01"#, r#"F03-02"#, r#"F03-03"#, r#"F03-04"#, r#"F03-05"#, r#"F03-06"#, r#"F03-07"#, r#"F03-08"#, r#"F03-09"#, r#"F03-10"#, r#"F03-11"#, r#"F03-12"#, r#"STD-frictionless-package"#, r#"STD-frictionless-table"#, r#"STD-gdpr"#, r#"STD-ietf-json"#, r#"STD-ietf-json-schema"#, r#"STD-mermaid"#, r#"STD-nist-800-188"#, r#"STD-nist-ai-rmf"#, r#"STD-nist-privacy"#, r#"STD-rdf11"#, r#"STD-spdx-licenses"#, r#"STD-vega-lite"#, r#"STD-w3c-prov-o"#, r#"STD-w3c-vc"#], 0),
        (r#"community/零售与电商域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, 1, &[r#"D11-01"#, r#"D11-02"#, r#"D11-03"#, r#"D11-04"#, r#"D11-05"#, r#"D11-06"#, r#"D11-07"#, r#"D11-08"#, r#"D11-09"#, r#"D11-10"#, r#"D11-11"#, r#"D11-12"#, r#"STD-common-criteria"#, r#"STD-gdpr"#, r#"STD-ietf-bcp47"#, r#"STD-ietf-json"#, r#"STD-ietf-json-schema"#, r#"STD-mermaid"#, r#"STD-nist-ai-rmf"#, r#"STD-rdf11"#, r#"STD-vega-lite"#, r#"STD-w3c-prov-o"#, r#"STD-w3c-tabular-data"#], 0),
        (r#"community/音频与音乐生成域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, 1, &[r#"A05-01"#, r#"A05-02"#, r#"A05-03"#, r#"A05-04"#, r#"A05-05"#, r#"A05-06"#, r#"A05-07"#, r#"A05-08"#, r#"A05-09"#, r#"A05-10"#, r#"A05-11"#, r#"A05-12"#, r#"STD-cncf-cloudevents"#, r#"STD-creativecommons"#, r#"STD-ietf-bcp47"#, r#"STD-ietf-json"#, r#"STD-ietf-json-schema"#, r#"STD-mlcommons-bench"#, r#"STD-onnx"#, r#"STD-opengeospatial"#, r#"STD-protobuf"#, r#"STD-rdf11"#, r#"STD-spdx-licenses"#, r#"STD-vega-lite"#, r#"STD-w3c-prov-o"#, r#"STD-w3c-tabular-data"#, r#"STD-w3c-webaudio"#], 0),
        (r#"community/音频音乐与语音域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, 1, &[r#"E09-01"#, r#"E09-02"#, r#"E09-03"#, r#"E09-04"#, r#"E09-05"#, r#"E09-06"#, r#"E09-07"#, r#"E09-08"#, r#"E09-09"#, r#"E09-10"#, r#"E09-11"#, r#"E09-12"#, r#"STD-commonmark"#, r#"STD-ietf-bcp47"#, r#"STD-ietf-json"#, r#"STD-ietf-json-schema"#, r#"STD-mermaid"#, r#"STD-vega-lite"#, r#"STD-w3c-epub33"#, r#"STD-w3c-tabular-data"#, r#"STD-w3c-webaudio"#, r#"STD-w3c-xml"#], 0),
        (r#"community/预测异常与风险域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, 1, &[r#"B18-01"#, r#"B18-02"#, r#"B18-03"#, r#"B18-04"#, r#"B18-05"#, r#"B18-06"#, r#"B18-07"#, r#"B18-08"#, r#"B18-09"#, r#"B18-10"#, r#"B18-11"#, r#"B18-12"#, r#"STD-cncf-otel-semconv"#, r#"STD-commonmark"#, r#"STD-frictionless-package"#, r#"STD-frictionless-table"#, r#"STD-gips"#, r#"STD-ietf-bcp47"#, r#"STD-ietf-ixdtf"#, r#"STD-ietf-json"#, r#"STD-ietf-json-schema"#, r#"STD-onnx"#, r#"STD-opcua"#, r#"STD-protobuf"#, r#"STD-rdf11"#, r#"STD-rfc3339"#, r#"STD-vega-lite"#, r#"STD-w3c-owl-time"#, r#"STD-w3c-owl2"#, r#"STD-w3c-prov-o"#, r#"STD-w3c-tabular-data"#], 0),
        (r#"community/预训练与继续预训练域包/outputs/CONCEPT_DAG.graphml"#, r#"graphml"#, 1, &[r#"C04-01"#, r#"C04-02"#, r#"C04-03"#, r#"C04-04"#, r#"C04-05"#, r#"C04-06"#, r#"C04-07"#, r#"C04-08"#, r#"C04-09"#, r#"C04-10"#, r#"C04-11"#, r#"C04-12"#, r#"STD-cncf-otel-semconv"#, r#"STD-frictionless-package"#, r#"STD-frictionless-table"#, r#"STD-ietf-bcp47"#, r#"STD-ietf-json"#, r#"STD-ietf-json-schema"#, r#"STD-mermaid"#, r#"STD-mlcommons-bench"#, r#"STD-rdf11"#, r#"STD-vega-lite"#, r#"STD-w3c-skos"#, r#"STD-w3c-tabular-data"#], 0),
        ];
        let mut parsed_ok = 0;
        for (rel, want_tag, want_graphs, want_nodes, want_dangling) in cases {
            let text = std::fs::read_to_string(root.join(rel)).unwrap();
            match parse(&text) {
                Err(_) => {
                    // 真源那条也只记"解析失败"（文本不可比）
                    assert!(want_graphs == &0 && want_nodes.is_empty() && want_tag.is_empty(),
                            "{} 本线解析失败但真源成功", rel);
                }
                Ok(node) => {
                    parsed_ok += 1;
                    assert_eq!(node.local(), *want_tag, "{} 根元素局部名", rel);
                    let graphs = node.descendants("graph");
                    assert_eq!(graphs.len(), *want_graphs, "{} 后代 graph 数", rel);
                    let mut ids: Vec<String> = Vec::new();
                    for g in &graphs {
                        for n in g.children_named("node") {
                            if let Some(id) = n.attr("id") {
                                ids.push(id.to_string());
                            }
                        }
                    }
                    ids.sort();
                    ids.dedup();
                    assert_eq!(ids, want_nodes.iter().map(|s| s.to_string()).collect::<Vec<_>>(),
                               "{} node id 集", rel);
                    let idset: std::collections::BTreeSet<String> = ids.clone().into_iter().collect();
                    let mut dangling = 0usize;
                    for g in &graphs {
                        for e in g.children_named("edge") {
                            for end in ["source", "target"] {
                                if !e.attr(end).map(|v| idset.contains(v)).unwrap_or(false) {
                                    dangling += 1;
                                }
                            }
                        }
                    }
                    assert_eq!(dangling, *want_dangling, "{} edge 悬空数", rel);
                }
            }
        }
        assert!(parsed_ok > 0, "至少要成功解析若干件，否则判据是空转");
    }
    // <<< GENERATED
}
