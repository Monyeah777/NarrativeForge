using System.Text.RegularExpressions;

namespace Nf.Engine;

/// <summary>
/// 复刻 <c>core/quality_baseline.py</c>：**基线自描述一致性机检**——以 <c>verify.sh</c> 为单一真值，
/// 断言其余三处声明（README 基线句 / CHANGELOG 最新节 / VERSION-MATRIX）与它自洽。
/// 任何一处落后即 FAIL（防「口头 PASS=N、文档 PASS=M」类失配）。
///
/// **照抄真源两处口径**：① CHANGELOG 只认「最新节」= 文件开头到 <c>\n## [2.8.0]</c> 之前那段（真源硬编码该分节标记）；
/// ② 期望值 <see cref="ExpectedChecks"/> / <see cref="ExpectedPass"/> 是真源里的常量，仓库扩 check 时**两边都要改**
/// （本镜像滞后即报不一致，不静默通过）。
/// </summary>
public static class QualityBaseline
{
    public const string VerifyRel = "verify.sh";
    public const int ExpectedChecks = 39;
    public const int ExpectedPass = 68;

    private static readonly Regex VersionRe = new(@"# 版本 : (v\d+\.\d+)", RegexOptions.CultureInvariant);
    private static readonly Regex CheckFnRe = new(@"^check(\d+)\(\)\{", RegexOptions.Multiline);
    private static readonly System.Text.UTF8Encoding StrictUtf8 = new(false, throwOnInvalidBytes: true);

    public static (List<string> Issues, Dictionary<string, object?> Stats) Scan(string root)
    {
        var issues = new List<string>();
        string Read(string rel) =>
            StrictUtf8.GetString(File.ReadAllBytes(Path.Combine(root, rel)));

        var verifyText = Read(VerifyRel);
        var match = VersionRe.Match(verifyText);
        var ver = match.Success ? match.Groups[1].Value : "";
        var nums = CheckFnRe.Matches(verifyText)
            .Select(m => int.Parse(m.Groups[1].Value, System.Globalization.CultureInfo.InvariantCulture))
            .Distinct().OrderBy(n => n).ToList();
        if (ver.Length == 0) issues.Add("verify.sh 缺版本头（vX.Y）");
        if (nums.Count != ExpectedChecks
            || !nums.SequenceEqual(Enumerable.Range(1, ExpectedChecks)))
            issues.Add($"verify.sh check 函数数/编号异常：{PyScalar.PyRepr(nums.Cast<object?>().ToList())}");

        var passToken = $"PASS={ExpectedPass}";
        var readme = Read("README.md");
        var readmeOk = ver.Length > 0 && readme.Contains(ver, StringComparison.Ordinal)
                       && readme.Contains($"check1-{ExpectedChecks}", StringComparison.Ordinal)
                       && readme.Contains(passToken, StringComparison.Ordinal);
        var changelog = Read("CHANGELOG.md");
        var head = changelog.Split("\n## [2.8.0]")[0];
        var versions = Read("VERSION-MATRIX.md");
        var checks = new (string Name, string What, int Count)[]
        {
            ("README", "基线句", readmeOk ? 1 : 0),
            ("CHANGELOG 最新节", passToken, CountOccurrences(head, passToken)),
            ("VERSION-MATRIX", passToken, CountOccurrences(versions, passToken)),
        };
        foreach (var (name, what, count) in checks)
        {
            if (count < 1)
                issues.Add($"{name} 缺 {what} 声明（预期含 v2.x/check1-{ExpectedChecks}/{passToken}）");
        }
        return (issues, new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["verify_version"] = ver, ["checks"] = (long)nums.Count,
        });
    }

    /// <summary>Python <c>str.count(sub)</c>：非重叠出现次数。</summary>
    private static int CountOccurrences(string text, string needle)
    {
        var count = 0;
        var index = 0;
        while ((index = text.IndexOf(needle, index, StringComparison.Ordinal)) >= 0)
        {
            count++;
            index += needle.Length;
        }
        return count;
    }
}
