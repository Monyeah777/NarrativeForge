using System.Globalization;
using System.Text;
using System.Text.Json;
using System.Text.RegularExpressions;

namespace Nf.Engine;

/// <summary>
/// 复刻 <c>desktop/src/core/text_hygiene.py</c>（**编码与标识面卫生门禁** · check33 第 9 面，
/// 外部标准净吸收：RFC 3629 / RFC 8259 §4 / RFC 7493 / UAX #15 / UTS #39 / SemVer 2.0.0）：
///
/// ① <b>EOL 落点</b>：<c>.gitattributes</c> 须在场且声明 <c>* text=auto eol=lf</c>；
/// ② <b>承载编码</b>：逐件查 UTF-8 BOM / CRLF / 非法 UTF-8；
/// ③ <b>标识面词法</b>：<c>.json</c> 的**每个键**（+ 三份登记件的指定**值**）须过 NFC + 字符集 + 无隐形/同形字符；
/// ④ <b>JSON 唯一名</b>：RFC 8259 §4——重复键即 FAIL（多数解析器后值覆盖前值、静默丢数据）；
/// ⑤ <b>版本词法</b>：<c>community/*/protocol.yaml</c> 的 <c>version</c> 须过 SemVer 2.0.0。
///
/// 真源里本面只被 <c>verify.sh check33</c> 消费（无 <c>nf</c> 子命令面），故**不新增 CLI 面**；
/// 证据通道 = 真材料 + 合成负例（自检钉）+ 探针 <c>probes/text_hygiene_probe.py</c>
/// （真源模块**原文**在同树双跑，逐字节同摘要）。
///
/// <b>复用而非重写</b>：JSON 重复键语义已由 <c>OutputForms.ScanDuplicateKeys</c> 实现（Python
/// <c>object_pairs_hook</c> 口径）；本件按同一语义在 <see cref="TextHygiene"/> 内做**键序**遍历
/// （第一出现位置 + 最后出现值，同 Python <c>dict(pairs)</c>），两者对输出各司其职。
///
/// <b>受控化差异（登记，不冒充等价）</b>：
/// ① 非法 JSON 的具体文案来自各自 JSON 解析器（Python <c>Expecting value: line 1 column 1 (char 0)</c>
///    vs STJ <c>'x' is an invalid start of a value</c>）——判定一致、文案不可约；
/// ② Python 的 <c>json.loads</c> 默认接受 <c>NaN</c> / <c>Infinity</c> 与孤立代理转义，STJ 拒绝——
///    本件取**越界即 FAIL**（宁可假红不假绿），真仓无此类件；
/// ③ <c>protocol.yaml</c> 读取失败（编码/权限）真源会抛到 check33 的兜底（"扫描不可用"），
///    本件收敛为可读问题条目；
/// ④ 排序用 <c>StringComparer.Ordinal</c>（UTF-16 码元序）——与 Python 码点序在 BMP 内一致，
///    含增补面字符时理论可分叉（与引擎其余面同口径）。
/// </summary>
public static class TextHygiene
{
    private static readonly HashSet<string> ExcludeDirs = new(StringComparer.Ordinal)
    {
        ".git", ".rivet", "__pycache__", ".ruff_cache", ".mypy_cache", ".pylint.d", ".pytest_cache",
    };

    private static readonly HashSet<string> ExcludeFiles = new(StringComparer.Ordinal) { "_cov_tmp.json" };

    private static readonly HashSet<string> BinaryExt = new(StringComparer.Ordinal)
    {
        ".png", ".jpg", ".jpeg", ".ico", ".gif", ".gz", ".zip", ".pdf",
        ".woff", ".woff2", ".ttf", ".so", ".dll", ".exe",
    };

    /// <summary>标识面允许的字符（额外允许 CJK 统一表意汉字；<c>$ @ {}</c> 是外部标准的既有合法形状）。</summary>
    private const string AsciiOk = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-.:/ ${}@";

    private static readonly (int Lo, int Hi)[] Cjk = { (0x4E00, 0x9FFF), (0x3400, 0x4DBF) };

    /// <summary>典型同形/隐形字符（命中即 FAIL；顺序照抄真源字典）。</summary>
    private static readonly (int Code, string Name)[] Invisible =
    {
        (0x200B, "零宽空格"), (0x200C, "零宽非连接"), (0x200D, "零宽连接"),
        (0xFEFF, "BOM/零宽无间断"), (0x00A0, "不换行空格(NBSP)"), (0x3000, "全角空格"),
        (0x2028, "行分隔符"), (0x2029, "段分隔符"), (0x2060, "词连接符"),
    };

    /// <summary>SemVer 2.0.0 §9/§10 词法（数字标识无前导零、三段必填、空标识非法）。</summary>
    private static readonly Regex SemverRe = new(
        "^(0|[1-9]\\d*)\\.(0|[1-9]\\d*)\\.(0|[1-9]\\d*)"
        + "(?:-((?:0|[1-9]\\d*|\\d*[A-Za-z-][0-9A-Za-z-]*)(?:\\.(?:0|[1-9]\\d*|\\d*[A-Za-z-][0-9A-Za-z-]*))*))?"
        + "(?:\\+([0-9A-Za-z-]+(?:\\.[0-9A-Za-z-]+)*))?$",
        RegexOptions.Compiled);

    private static readonly Regex ThreeNumberRe = new("^\\d+\\.\\d+\\.\\d+$", RegexOptions.Compiled);
    private static readonly Regex TwoNumberRe = new("^\\d+\\.\\d+$", RegexOptions.Compiled);
    private static readonly Regex GitAttributesRe = new("^\\*\\s+text(?:=\\w+)?\\s+eol=lf", RegexOptions.Multiline | RegexOptions.Compiled);
    private static readonly Regex VersionLineRe = new("^\\s*version:\\s*\"?([^\"\\s#]+)\"?", RegexOptions.Multiline | RegexOptions.Compiled);

    private static readonly UTF8Encoding StrictUtf8 = new(false, throwOnInvalidBytes: true);

    /// <summary>标识**值**面：登记册里作为值出现的 id/类别/键同样要过词法（键有判据而值没有 = 同形后门）。</summary>
    private static readonly (string Rel, string[] Paths)[] ValueSources =
    {
        ("desktop/src/core/registry.json", new[] { "modules[*].id", "modules[*].category", "protocols[*].id" }),
        ("05_资产库/provenance.json", new[] { "assets[*].key", "assets[*].module" }),
        ("protocol/vocabularies.json", new[] { "schemes[*].id", "schemes[*].values[*]" }),
    };

    public sealed record Result(List<string> Issues, Dictionary<string, object?> Stats)
    {
        public bool Ok => Issues.Count == 0;

        /// <summary>真源 <c>summary(stats)</c> 原文。</summary>
        public string SummaryLine =>
            $"文本 {Num("text")} 件 / JSON {Num("json")} 件 / 键 {Num("keys_checked")} 个 / "
            + $"版本 {Num("versions_checked")} 个 / BOM {Num("bom")} / CRLF {Num("crlf")}";

        /// <summary>真源 <c>__main__</c> 的输出：摘要行 + 逐条 <c>[FAIL]</c>。</summary>
        public List<string> Log
        {
            get
            {
                var lines = new List<string> { SummaryLine };
                lines.AddRange(Issues.Select(i => "[FAIL] " + i));
                return lines;
            }
        }

        /// <summary>逐字节同口径摘要（<c>sha256("\n".join(日志行))[:32]</c>，与真源 <c>__main__</c> 输出同式）。</summary>
        public string LogDigest => Convert.ToHexString(
            System.Security.Cryptography.SHA256.HashData(
                Encoding.UTF8.GetBytes(string.Join("\n", Log)))).ToLowerInvariant()[..32];

        private long Num(string key) => Convert.ToInt64(Stats[key] ?? 0L);
    }

    public static Result Scan(string root)
    {
        var issues = new List<string>();

        // ① EOL 纪律的可执行落点
        var gitAttributes = Path.Combine(root, ".gitattributes");
        if (!File.Exists(gitAttributes))
        {
            issues.Add("缺 .gitattributes（修复指引：声明 `* text=auto eol=lf`——"
                       + "EOL 纪律须有落点，否则 Windows 检出反复回流 CRLF）");
        }
        else
        {
            var ga = NormalizeNewlines(File.ReadAllText(gitAttributes, new UTF8Encoding(false)));
            if (!GitAttributesRe.IsMatch(ga))
                issues.Add(".gitattributes 未声明 `* text=auto eol=lf`"
                           + "（修复指引：全仓行尾纪律须显式声明，见仓库根 .gitattributes）");
        }

        var files = Walk(root);
        long nText = 0, nJson = 0, nCrlf = 0, nBom = 0, keysChecked = 0, valuesChecked = 0;

        foreach (var path in files)
        {
            var rel = Rel(root, path);
            byte[] raw;
            try
            {
                raw = File.ReadAllBytes(path);
            }
            catch (Exception)
            {
                continue;   // 尽力而为：读不到的文件跳过（缺件由回执门/门禁件清单报出）
            }
            if (ContainsNul(raw, 4096)) continue;   // 二进制哨兵
            nText++;

            if (raw.Length >= 3 && raw[0] == 0xEF && raw[1] == 0xBB && raw[2] == 0xBF)
            {
                nBom++;
                issues.Add($"{rel} 以 UTF-8 BOM 开头（修复指引：去掉 BOM——BOM 会让 json/yaml "
                           + "首键解析失败，也让摘要随编辑器变化）");
                raw = raw[3..];
            }
            if (ContainsCrlf(raw))
            {
                nCrlf++;
                issues.Add($"{rel} 含 CRLF 行尾（修复指引：仓库 EOL 纪律 = LF"
                           + "（.gitattributes `* text=auto eol=lf`）；本地去 CR 后存回，勿改内容）");
            }

            string text;
            try
            {
                text = StrictUtf8.GetString(raw);
            }
            catch (DecoderFallbackException exc)
            {
                issues.Add($"{rel} 不是合法 UTF-8：{exc.Message}（修复指引：RFC 3629 只许 UTF-8——"
                           + "重存为 UTF-8 无 BOM）");
                continue;
            }

            if (!path.EndsWith(".json", StringComparison.Ordinal)) continue;
            nJson++;
            var doc = DupCheck(text, rel, issues);
            if (doc is null) continue;
            using (doc)
            {
                var keys = new List<string>();
                CollectKeys(doc.RootElement, keys);
                foreach (var key in keys)
                {
                    keysChecked++;
                    var msg = IdentifierIssue(key);
                    if (msg.Length > 0)
                    {
                        issues.Add($"{rel} JSON 键 {PyScalar.PyRepr(key)} 违规：{msg}（修复指引：键须 NFC + 字符集内；"
                                   + "同形/隐形字符会让机器侧当成另一个键）");
                    }
                }
                foreach (var (srcRel, paths) in ValueSources)
                {
                    if (rel != srcRel) continue;
                    foreach (var jsonPath in paths)
                    {
                        foreach (var value in ResolvePath(doc.RootElement, jsonPath))
                        {
                            if (value.ValueKind != JsonValueKind.String) continue;
                            var text2 = value.GetString() ?? "";
                            valuesChecked++;
                            var msg = IdentifierIssue(text2);
                            if (msg.Length > 0)
                            {
                                issues.Add($"{rel} 的 {jsonPath} = {PyScalar.PyRepr(text2)} 违规：{msg}（修复指引：标识值须 NFC + "
                                           + "字符集内——键有判据而值没有，等于给同形留后门）");
                            }
                        }
                    }
                }
            }
        }

        // ⑤ 版本面：声明件里的 version 值须过 SemVer 2.0.0 词法
        long nVersions = 0;
        foreach (var path in GlobProtocolYaml(root))
        {
            var rel = Rel(root, path);
            string text;
            try
            {
                text = NormalizeNewlines(File.ReadAllText(path, new UTF8Encoding(false)));
            }
            catch (Exception exc)
            {
                issues.Add($"{rel} 不可读（{exc.GetType().Name}：{exc.Message}）——真源此处会抛到 check33 兜底");
                continue;
            }
            foreach (Match m in VersionLineRe.Matches(text))
            {
                var value = m.Groups[1].Value;
                nVersions++;
                var bad = SemverIssue(value);
                if (bad.Length > 0)
                {
                    issues.Add($"{rel} 的版本值 {PyScalar.PyRepr(value)} 违规：{bad}（修复指引：按 SemVer 2.0.0 改写，"
                               + "破坏性变更须 bump 主版本并留迁移记录）");
                }
            }
        }

        var stats = new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["files"] = (long)files.Count,
            ["text"] = nText,
            ["json"] = nJson,
            ["bom"] = nBom,
            ["crlf"] = nCrlf,
            ["keys_checked"] = keysChecked,
            ["values_checked"] = valuesChecked,
            ["versions_checked"] = nVersions,
            ["issues"] = (long)issues.Count,
        };
        return new Result(issues, stats);
    }

    /// <summary>标识面词法体检 → 违规说明（空串 = 合规）。逐**码点**走，与 Python <c>ord()/unicodedata</c> 同口径。</summary>
    public static string IdentifierIssue(string text)
    {
        if (text.Length == 0) return "标识为空";
        if (text.Normalize(NormalizationForm.FormC) != text)
            return "非 NFC 规范化形态（UAX #15：同形异码会让机器侧不等）";
        foreach (var (code, name) in Invisible)
        {
            if (ContainsCodePoint(text, code))
                return $"含隐形/同形字符 {name}（U+{code:X4}）";
        }
        var bad = new List<int>();
        foreach (var rune in text.EnumerateRunes())
        {
            if (rune.Value < 128 && AsciiOk.Contains((char)rune.Value)) continue;
            if (IsCjk(rune.Value)) continue;
            bad.Add(rune.Value);
        }
        if (bad.Count > 0)
        {
            var names = string.Join("、", bad.Take(4).Select(c => "U+" + c.ToString("X4", CultureInfo.InvariantCulture)));
            return $"含越界字符 {names}（标识面只许 ASCII 字母数字 + _-.:/ 与 CJK 汉字）";
        }
        foreach (var rune in text.EnumerateRunes())
        {
            var category = Rune.GetUnicodeCategory(rune);
            if (category is UnicodeCategory.Control or UnicodeCategory.Format or UnicodeCategory.Surrogate
                or UnicodeCategory.PrivateUse or UnicodeCategory.OtherNotAssigned)
                return "含控制/格式/未分配码位";
        }
        return "";
    }

    /// <summary>SemVer 2.0.0 词法体检 → 违规说明（空串 = 合规）。</summary>
    public static string SemverIssue(string value)
    {
        var v = (value ?? "").Trim();
        if (v.Length == 0) return "版本为空";
        if (SemverRe.IsMatch(v)) return "";
        if (ThreeNumberRe.IsMatch(v)) return "数字标识含前导零（SemVer §9：`01` 不是合法数字标识）";
        if (TwoNumberRe.IsMatch(v)) return "缺补丁号（SemVer 要求 MAJOR.MINOR.PATCH 三段）";
        if (v.EndsWith('-') || v.EndsWith('+') || v.Contains("-.", StringComparison.Ordinal)
            || v.Contains("+.", StringComparison.Ordinal))
            return "预发布/构建标识为空段（SemVer §9/§10）";
        return "不符合 SemVer 2.0.0 形态（修复指引：MAJOR.MINOR.PATCH[-prerelease][+build]）";
    }

    /// <summary>JSON 唯一名（RFC 8259 §4）：每个对象各自查重 → 去重排序后逐条报。</summary>
    private static JsonDocument? DupCheck(string text, string rel, List<string> issues)
    {
        JsonDocument doc;
        try
        {
            doc = JsonDocument.Parse(text, JsonIo.Options);
        }
        catch (JsonException exc)
        {
            issues.Add($"{rel} 不是合法 JSON：{exc.Message}（修复指引：跑 python -m json.tool 定位）");
            return null;
        }
        var dups = new List<string>();
        ScanDuplicates(doc.RootElement, dups);
        dups.Sort(StringComparer.Ordinal);
        foreach (var key in dups.Distinct(StringComparer.Ordinal))
        {
            issues.Add($"{rel} JSON 重复键 {PyScalar.PyRepr(key)}（修复指引：RFC 8259 §4 要求名唯一——"
                       + "多数解析器后值覆盖前值、静默丢数据；删掉其中一条）");
        }
        return doc;
    }

    private static void ScanDuplicates(JsonElement element, List<string> dups)
    {
        switch (element.ValueKind)
        {
            case JsonValueKind.Object:
                var seen = new HashSet<string>(StringComparer.Ordinal);
                foreach (var property in element.EnumerateObject())
                {
                    if (!seen.Add(property.Name)) dups.Add(property.Name);
                    ScanDuplicates(property.Value, dups);
                }
                break;
            case JsonValueKind.Array:
                foreach (var item in element.EnumerateArray()) ScanDuplicates(item, dups);
                break;
        }
    }

    /// <summary>
    /// 递归取键：Python <c>dict(pairs)</c> 口径——**第一出现位置 + 最后出现值**，再前序遍历
    /// （父键先于其子键；数组按元素序）。
    /// </summary>
    private static void CollectKeys(JsonElement element, List<string> keys)
    {
        switch (element.ValueKind)
        {
            case JsonValueKind.Object:
                var order = new List<string>();
                var lastValue = new Dictionary<string, JsonElement>(StringComparer.Ordinal);
                foreach (var property in element.EnumerateObject())
                {
                    if (!lastValue.ContainsKey(property.Name)) order.Add(property.Name);
                    lastValue[property.Name] = property.Value;
                }
                foreach (var name in order)
                {
                    keys.Add(name);
                    CollectKeys(lastValue[name], keys);
                }
                break;
            case JsonValueKind.Array:
                foreach (var item in element.EnumerateArray()) CollectKeys(item, keys);
                break;
        }
    }

    /// <summary>真源 <c>_resolve</c>：只支持 <c>a[*].b</c> 形态（<c>[*]</c> 展开 + 点分字段）。</summary>
    private static List<JsonElement> ResolvePath(JsonElement doc, string path)
    {
        var current = new List<JsonElement> { doc };
        foreach (var part in path.Split('.'))
        {
            var star = part.EndsWith("[*]", StringComparison.Ordinal);
            var key = star ? part[..^3] : part;
            var next = new List<JsonElement>();
            foreach (var item in current)
            {
                if (item.ValueKind != JsonValueKind.Object) continue;
                if (!item.TryGetProperty(key, out var value)) continue;
                if (star)
                {
                    if (value.ValueKind == JsonValueKind.Array)
                        foreach (var element in value.EnumerateArray()) next.Add(element);
                }
                else
                {
                    next.Add(value);
                }
            }
            current = next;
        }
        return current;
    }

    private static List<string> Walk(string root)
    {
        var files = new List<string>();
        void Recurse(string dir)
        {
            string[] dirs;
            string[] entries;
            try
            {
                dirs = Directory.GetDirectories(dir);
                entries = Directory.GetFiles(dir);
            }
            catch (Exception)
            {
                return;   // os.walk(onerror=None) 静默跳过不可读目录
            }
            foreach (var sub in dirs)
            {
                if (ExcludeDirs.Contains(Path.GetFileName(sub))) continue;
                Recurse(sub);
            }
            foreach (var file in entries)
            {
                var name = Path.GetFileName(file);
                if (ExcludeFiles.Contains(name)) continue;
                if (BinaryExt.Contains(PyExtLower(name))) continue;
                files.Add(file);
            }
        }
        Recurse(root);
        files.Sort(StringComparer.Ordinal);
        return files;
    }

    /// <summary>Python <c>os.path.splitext</c> 的扩展名规则（前导点不算扩展名分隔符）。</summary>
    private static string PyExtLower(string name)
    {
        var dot = name.LastIndexOf('.');
        if (dot < 0) return "";
        var start = 0;
        while (start < dot && name[start] == '.') start++;
        if (start == dot) return "";
        return name[dot..].ToLowerInvariant();
    }

    private static List<string> GlobProtocolYaml(string root)
    {
        var result = new List<string>();
        var community = Path.Combine(root, "community");
        if (!Directory.Exists(community)) return result;
        foreach (var pack in Directory.GetDirectories(community))
        {
            var candidate = Path.Combine(pack, "protocol.yaml");
            if (File.Exists(candidate)) result.Add(candidate);
        }
        result.Sort((a, b) => string.CompareOrdinal(Rel(root, a), Rel(root, b)));
        return result;
    }

    private static bool IsCjk(int codePoint)
    {
        foreach (var (lo, hi) in Cjk)
        {
            if (codePoint >= lo && codePoint <= hi) return true;
        }
        return false;
    }

    private static bool ContainsCodePoint(string text, int codePoint)
    {
        foreach (var rune in text.EnumerateRunes())
        {
            if (rune.Value == codePoint) return true;
        }
        return false;
    }

    private static bool ContainsNul(byte[] raw, int limit)
    {
        var end = Math.Min(limit, raw.Length);
        for (var i = 0; i < end; i++)
        {
            if (raw[i] == 0) return true;
        }
        return false;
    }

    private static bool ContainsCrlf(byte[] raw)
    {
        for (var i = 1; i < raw.Length; i++)
        {
            if (raw[i - 1] == (byte)'\r' && raw[i] == (byte)'\n') return true;
        }
        return false;
    }

    private static string NormalizeNewlines(string text) => text.Replace("\r\n", "\n").Replace('\r', '\n');

    private static string Rel(string root, string path) =>
        Path.GetRelativePath(root, path).Replace('\\', '/');
}
