using System.Security.Cryptography;
using System.Text;

namespace Nf.Engine;

/// <summary>
/// **语料身份**：把「被测语料」本身先量成一个指纹，好让**摘要类钉的红**能被正确归因。
///
/// 为什么需要（第一百零六片实测踩到的操作性陷阱）：本引擎有一批钉锚定**具体语料的死摘要**
/// （金标 = HEAD `983741b` 的导出快照）。作者前移 HEAD 后若**重新导出快照**再跑门，摘要类钉会红——
/// 那是「**语料变了**」，不是「引擎坏了」；但输出里只有一串摘要不等，**看不出是哪一种**。
/// 本件给出指纹 + 金标基线 + 模式（导出快照 / 工作区），于是归因一眼可判。
///
/// 指纹口径（确定性 · 覆盖全语料）：对根下全部文件（**跳过 <c>.git</c> 与 Python 字节码缓存**）
/// 按相对路径排序，逐件取 <c>相对路径 \0 字节数 \0 sha256</c> 拼行，再整体 sha256 → 取前 16 位十六进制。
/// 只读、无副作用；同语料两遍同值（自检里钉住）。
///
/// **为什么排除 <c>__pycache__</c> / <c>*.pyc</c>（第一百零七片实测踩坑）**：真源门 `verify.sh`
/// 在树内 import 自家模块，会**就地写出 170 个 `.pyc`**（实测：跑完真源门后树里多 170 个字节码缓存）。
/// 若把字节码缓存计入指纹，则「先跑真源门、再跑本门」会报**假的「语料变了」**——而 `.pyc` 是派生物，
/// 不参与任何判据。故指纹只认**语料本体**（源码 + 声明件 + 生成物），不认 Python 的字节码缓存。
/// </summary>
public static class CorpusStamp
{
    /// <summary>
    /// 金标语料（**`nf-snap-h16` · HEAD `aa259d7` 导出快照**）的指纹。
    /// **第一百二十二片复基线**：真源前移（348577d → b1f9a28）后语料指纹由 `b1bb5b3bae754750`
    /// 变为 `17fb5a632888dd75`，文档命令面计数随之移到 302 处；`nf-snap-h5` / `nf-snap-h7`
    /// 降为对照快照，仅用于漂移归因。
    /// **勿手改本段**：它由 `run-rebaseline.ps1 -SnapName <s> -Head <sha>` 断言式重写；
    /// 手改会与 `_paths.py` 的默认快照名脱节（出处守卫会判红）。
    /// </summary>
    public const string Baseline = "fe8e8f3eb215a57d";

    public sealed record Result(string Fingerprint, string Baseline, bool Matches, bool IsSnapshot);

    public static Result Check(string root) =>
        new(Fingerprint(root), Baseline, Fingerprint(root) == Baseline,
            !Directory.Exists(Path.Combine(root, ".git")));

    /// <summary>语料指纹（前 16 位十六进制）。</summary>
    public static string Fingerprint(string root)
    {
        var files = Directory.EnumerateFiles(root, "*", SearchOption.AllDirectories)
            .Where(f => !IsUnderGit(f) && !IsBytecodeCache(f))
            .Select(f => (Rel: Path.GetRelativePath(root, f).Replace('\\', '/'), Full: f))
            .OrderBy(x => x.Rel, StringComparer.Ordinal)
            .ToList();
        var builder = new StringBuilder();
        foreach (var (rel, full) in files)
        {
            var info = new FileInfo(full);
            string digest;
            using (var stream = File.OpenRead(full))
            {
                digest = Convert.ToHexString(SHA256.HashData(stream)).ToLowerInvariant();
            }
            builder.Append(rel).Append('\0').Append(info.Length).Append('\0').Append(digest).Append('\n');
        }
        var total = Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(builder.ToString())))
            .ToLowerInvariant();
        return total[..16];
    }

    private static bool IsUnderGit(string full)
    {
        var sep = Path.DirectorySeparatorChar;
        return full.Contains(sep + ".git" + sep, StringComparison.Ordinal)
               || full.EndsWith(sep + ".git", StringComparison.Ordinal);
    }

    /// <summary>Python 字节码缓存（`__pycache__/` 与 `*.pyc` / `*.pyo`）——派生物，不计入语料指纹。</summary>
    private static bool IsBytecodeCache(string full)
    {
        var sep = Path.DirectorySeparatorChar;
        if (full.Contains(sep + "__pycache__" + sep, StringComparison.Ordinal)) return true;
        return full.EndsWith(".pyc", StringComparison.OrdinalIgnoreCase)
               || full.EndsWith(".pyo", StringComparison.OrdinalIgnoreCase);
    }
}
