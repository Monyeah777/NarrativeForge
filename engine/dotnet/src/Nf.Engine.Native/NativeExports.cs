using System.Runtime.InteropServices;

namespace Nf.Engine.Native;

/// <summary>原生出口：只导出 C ABI 符号，供 core/engine_loader.py 经 ctypes 载入。</summary>
public static class NativeExports
{
    /// <summary>C ABI：引擎 ABI 版本号（与 Rust 线同名同义）。</summary>
    [UnmanagedCallersOnly(EntryPoint = "nf_engine_abi_version")]
    public static uint AbiVersion() => 1;
}
