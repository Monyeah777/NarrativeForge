using System.Text.Json;

namespace Nf.Engine;

/// <summary>
/// 引擎的**唯一 JSON 读取入口**——为什么需要它：<c>JsonDocument.Parse</c> 的默认
/// <c>MaxDepth</c> 是 **64**，而 CPython 的 <c>json.loads</c> 到 **995 层**才抛
/// <c>RecursionError</c>（实测 990 OK / 1000 失败）。自设 64 会让引擎在 65 层就单方面
/// 判死合法输入——**比 Python 更严不是等价，是另一种错**。
///
/// 口径：深度上限取 **1000**（与 CPython 的 1000 递归上限同量级，±1 层边界差异如实登记），
/// 超出仍是 fail-closed（<c>JsonReaderException</c> → 受控失败 / 契约执行异常），不静默截断。
/// 真实语料实测最深 12 层（1035 件可解析 JSON），故本上限只影响敌意输入。
/// </summary>
public static class JsonIo
{
    public const int MaxDepth = 1000;

    public static readonly JsonDocumentOptions Options = new()
    {
        MaxDepth = MaxDepth,
        AllowTrailingCommas = false,
        CommentHandling = JsonCommentHandling.Disallow,
    };

    public static JsonDocument Parse(byte[] utf8) => JsonDocument.Parse(utf8, Options);

    public static JsonDocument Parse(string text) => JsonDocument.Parse(text, Options);

    public static JsonDocument ReadFile(string path) => JsonDocument.Parse(File.ReadAllBytes(path), Options);
}
