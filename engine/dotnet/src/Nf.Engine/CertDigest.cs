using System.Security.Cryptography;
using System.Text;
using System.Text.Json;

namespace Nf.Engine;

/// <summary>
/// 组合证书摘要：复刻 Python 侧
/// <c>sha256(json.dumps({k: v for k, v in obj.items() if k != "digest"}, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()[:32]</c>
/// （来源：<c>desktop/src/core/pack_combo.py</c> 的 <c>_digest</c>）。
/// </summary>
public static class CertDigest
{
    public const string DigestKey = "digest";

    /// <summary>
    /// 计算证书摘要。<paramref name="skipTopLevelKeys"/> 为参与哈希前须剔除的顶层键。
    ///
    /// 两种口径（勿混用）：
    /// 引擎层 = 只剔除 digest（等价 Python <c>_digest</c>）；
    /// 台账层 = 剔除 digest / label / note（在盘 <c>protocol/combo_certificates.json</c> 的实际口径，
    /// 因 Python 侧 <c>combine()</c> 先算 digest、<c>certify()</c> 之后才追加 label/note；实测 17/17 命中）。
    /// </summary>
    public static string Compute(JsonElement certificate, params string[] skipTopLevelKeys)
    {
        if (certificate.ValueKind != JsonValueKind.Object)
        {
            throw new InvalidOperationException("证书必须是 JSON 对象，实际为 " + certificate.ValueKind);
        }

        var keys = skipTopLevelKeys.Length > 0 ? skipTopLevelKeys : new[] { DigestKey };
        var canonical = PythonJson.Canonicalize(certificate, keys);
        var bytes = Encoding.UTF8.GetBytes(canonical);
        var hash = SHA256.HashData(bytes);
        var hex = Convert.ToHexString(hash).ToLowerInvariant();
        return hex[..32];
    }

    /// <summary>引擎层摘要（Python <c>_digest</c> 语义：只剔除 digest）。</summary>
    public static string EngineDigest(JsonElement certificate) => Compute(certificate, DigestKey);

    /// <summary>台账层摘要（在盘证书实际口径：剔除 digest / label / note）。</summary>
    public static string LedgerDigest(JsonElement certificate) => Compute(certificate, DigestKey, "label", "note");
}
