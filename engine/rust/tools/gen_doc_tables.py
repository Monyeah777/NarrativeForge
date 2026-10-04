"""从真源 `desktop/src/core/doc_hygiene.py` 转录常量表 → Rust 源码。

**为什么用生成器**：DOC_KINDS（50 条）/ REQUIRED_DOCS / INSTRUCTION_DOCS 是纯数据表，
手抄必然出错且无法审。生成后由 Rust 侧 `include`，并在文件头注明出处与重生成方式。

用法：python engine/rust/target/parity/gen_doc_tables.py <仓库根> <输出 .rs>
"""
import sys
from pathlib import Path

root = Path(sys.argv[1]).resolve()
out = Path(sys.argv[2])

sys.path.insert(0, str(root / "desktop" / "src"))
from core import doc_hygiene as dh  # noqa: E402


def rs_str(s: str) -> str:
    return 'r#"%s"#' % s


lines = []
lines.append("//! **由真源转录的常量表 —— 勿手改。**")
lines.append("//!")
lines.append("//! 出处：`desktop/src/core/doc_hygiene.py`（DOC_KINDS / REQUIRED_DOCS /")
lines.append("//! INSTRUCTION_DOCS / KINDS / KIND_RULES）。真源改表后须重生成，否则对账会红。")
lines.append("//!")
lines.append("//! 重生成：`python engine/rust/target/parity/gen_doc_tables.py <仓库根> <本文件>`")
lines.append("")
lines.append("/// 文档四型。")
lines.append("pub const KINDS: [&str; %d] = [%s];" % (len(dh.KINDS), ", ".join(rs_str(k) for k in dh.KINDS)))
lines.append("")
lines.append("/// 四型**写法**判据：(kind, must_any 正则, label)。")
lines.append("pub const KIND_RULES: [(&str, &[&str], &str); %d] = [" % len(dh.KIND_RULES))
for k, rule in dh.KIND_RULES.items():
    pats = ", ".join(rs_str(p) for p in rule["must_any"])
    lines.append("    (%s, &[%s], %s)," % (rs_str(k), pats, rs_str(rule["label"])))
lines.append("];")
lines.append("")
lines.append("/// 文档 → 四型归属。")
lines.append("pub const DOC_KINDS: [(&str, &str); %d] = [" % len(dh.DOC_KINDS))
for rel, kind in dh.DOC_KINDS.items():
    lines.append("    (%s, %s)," % (rs_str(rel), rs_str(kind)))
lines.append("];")
lines.append("")
lines.append("/// 须带「最后更新」位的关键文档。")
lines.append("pub const REQUIRED_DOCS: [&str; %d] = [" % len(dh.REQUIRED_DOCS))
for rel in dh.REQUIRED_DOCS:
    lines.append("    %s," % rs_str(rel))
lines.append("];")
lines.append("")
lines.append("/// 须带「⛔ 操作指令」标识头的指令类文档。")
lines.append("pub const INSTRUCTION_DOCS: [&str; %d] = [" % len(dh.INSTRUCTION_DOCS))
for rel in dh.INSTRUCTION_DOCS:
    lines.append("    %s," % rs_str(rel))
lines.append("];")
lines.append("")

out.write_text("\n".join(lines), encoding="utf-8")
print(
    "转写完成：KINDS=%d KIND_RULES=%d DOC_KINDS=%d REQUIRED_DOCS=%d INSTRUCTION_DOCS=%d"
    % (len(dh.KINDS), len(dh.KIND_RULES), len(dh.DOC_KINDS), len(dh.REQUIRED_DOCS), len(dh.INSTRUCTION_DOCS))
)
