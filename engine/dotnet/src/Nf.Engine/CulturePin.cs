using System.Globalization;
using System.Runtime.CompilerServices;

namespace Nf.Engine;

/// <summary>
/// **确定性兜底**：把引擎所在进程的文化显式钉成 invariant。
///
/// 为什么需要它（第八十一片）：编码卫生面要判 **UAX #15 NFC**，而 <c>String.Normalize</c> 依赖 ICU——
/// 项目原先开 <c>InvariantGlobalization=true</c>，该模式下归一化退化为**空操作**，NFC 判据形同虚设
/// （实测：键 <c>"e\u0301"</c> 本该报"非 NFC 规范化形态"，引擎却报"含越界字符 U+0301"）。
/// 改为 <c>InvariantGlobalization=false</c> 以恢复 ICU 归一化，同时用本类把文化钉死，
/// 使「区域设置影响排序/大小写/数字格式」这条风险仍被挡住。
///
/// 证据：改后 148 面逐字节双跑对账**全同**、自检 161/161、一键门 PASS —— 即确定性没有退化。
/// </summary>
internal static class CulturePin
{
#pragma warning disable CA2255 // 引擎库也要用它：文化钉必须在任何 API 使用**之前**生效，
    // 而宿主（未来可能不止 nf-dotnet / nfparity）不该各自记得调一次。已核：148 面复跑全同。
    [ModuleInitializer]
    internal static void Init()
    {
        CultureInfo.DefaultThreadCurrentCulture = CultureInfo.InvariantCulture;
        CultureInfo.DefaultThreadCurrentUICulture = CultureInfo.InvariantCulture;
        CultureInfo.CurrentCulture = CultureInfo.InvariantCulture;
        CultureInfo.CurrentUICulture = CultureInfo.InvariantCulture;
    }
#pragma warning restore CA2255
}
