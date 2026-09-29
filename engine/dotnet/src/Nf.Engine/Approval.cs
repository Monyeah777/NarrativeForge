using System.Text;
using System.Text.Json;

namespace Nf.Engine;

// 复刻 core/approval.py（**内容绑定批准记录** · 机制借鉴 MCOP approved-changeset gate）。
//
// 记录 = {schema, subject, subject_digest, approved_by, approved_at, note}；
// **被批准对象一改，subject_digest 立刻不符 → 失效**（approved 不是永久通行证）；
// 缺批准人 / 摘要不符 / 指向不存在的对象 → FAIL。
//
// 只移植**只读面**（records / verify / list_records）：写面 `approve()`（落 protocol/approvals/*.json）
// 明确拒绝——本引擎是只读门。
public static class Approval
{
    public const string Schema = "nf-approval/1";
    public const string DirRel = "protocol/approvals";

    public sealed record Result(List<string> Issues, Dictionary<string, object?> Stats)
    {
        public bool Ok => Issues.Count == 0;
    }

    /// <summary>被批准对象的整文件摘要（不含批准记录本身——记录是独立文件，无自指问题）。</summary>
    public static string SubjectDigest(string root, string subject)
    {
        var path = Path.Combine(root, subject.Replace('/', Path.DirectorySeparatorChar));
        return Convert.ToHexString(
            System.Security.Cryptography.SHA256.HashData(File.ReadAllBytes(path))).ToLowerInvariant();
    }

    /// <summary>读全部批准记录（按文件名排序；不可解析的记录按 Python 同式降级为 `{"schema":"?","subject":文件名,"broken":true}`）。</summary>
    public static List<Dictionary<string, object?>> Records(string root)
    {
        var outList = new List<Dictionary<string, object?>>();
        var dir = Path.Combine(root, DirRel.Replace('/', Path.DirectorySeparatorChar));
        if (!Directory.Exists(dir)) return outList;
        foreach (var file in Directory.GetFiles(dir, "*.json")
                     .OrderBy(f => Path.GetFileName(f), StringComparer.Ordinal))
        {
            try
            {
                using var json = JsonIo.ReadFile(file);
                outList.Add(PythonJson.ToGraph(json.RootElement) as Dictionary<string, object?>
                             ?? new Dictionary<string, object?>(StringComparer.Ordinal));
            }
            catch (Exception)
            {
                outList.Add(new Dictionary<string, object?>(StringComparer.Ordinal)
                {
                    ["schema"] = "?",
                    ["subject"] = Path.GetFileName(file),
                    ["broken"] = true,
                });
            }
        }
        return outList;
    }

    /// <summary>校验全部批准记录 → (issues, stats)。</summary>
    public static Result Verify(string root)
    {
        var issues = new List<string>();
        var rows = Records(root);
        var stale = new List<string>();
        foreach (var rec in rows)
        {
            var subject = PyOr(rec.GetValueOrDefault("subject"));
            if (PyOr(rec.GetValueOrDefault("schema")) != Schema)
            {
                issues.Add($"批准记录 schema 不匹配：{subject}");
                continue;
            }
            if (PyOr(rec.GetValueOrDefault("approved_by")).Trim().Length == 0)
                issues.Add($"批准记录缺批准人：{subject}");
            var path = Path.Combine(root, subject.Replace('/', Path.DirectorySeparatorChar));
            if (!File.Exists(path))
            {
                issues.Add($"批准对象不存在：{subject}");
                continue;
            }
            if (SubjectDigest(root, subject) != PyOr(rec.GetValueOrDefault("subject_digest")))
            {
                stale.Add(subject);
                issues.Add($"批准已失效（对象内容已改）：{subject}（修复指引：重新批准）");
            }
        }
        var subjects = rows.Select(r => PyOr(r.GetValueOrDefault("subject")))
            .Distinct(StringComparer.Ordinal).OrderBy(x => x, StringComparer.Ordinal).ToList();
        var stats = new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["records"] = (long)rows.Count,
            ["stale"] = stale,
            ["subjects"] = subjects.Cast<object?>().ToList(),
        };
        return new Result(issues, stats);
    }

    /// <summary>Python <c>str(x or "")</c>：**假值**（缺失 / None / 空串 / 0 / 空表 / 空映射 / False）一律回落空串。</summary>
    private static string PyOr(object? value) => PyTruthy(value) ? PyStr(value) : "";

    /// <summary>
    /// Python <c>str(x)</c>：字符串**原样**（不是 `repr`——`repr('a')` 会带上引号，用它比 schema 永远不等）。
    /// 容器走 <see cref="PyScalar.PyRepr"/>（Python 的 `str(dict)` 就是 repr 形态）。
    /// </summary>
    private static string PyStr(object? value) => value switch
    {
        null => "None",
        string s => s,
        _ => PyScalar.PyRepr(value),
    };

    private static bool PyTruthy(object? value) => value switch
    {
        null => false,
        bool b => b,
        int i => i != 0,
        long l => l != 0,
        double d => d != 0,
        string s => s.Length > 0,
        List<object?> list => list.Count > 0,
        Dictionary<string, object?> map => map.Count > 0,
        _ => true,
    };
}
