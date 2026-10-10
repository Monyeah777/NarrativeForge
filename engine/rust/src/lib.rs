//! NF 引擎 C ABI 出口（cdylib）。
//!
//! 用途：给 core/engine_loader.py 一个可 dlopen 的共享库，暴露 ABI 版本号；本文件**零依赖**，
//! 与 bin（src/main.rs 只读快线）互不影响——加它不改变快线行为，只多产一个共享库。
//!
//! 纪律：符号名必须与 Python 侧 core/engine_loader.py 的 ABI_SYMBOL 一致。

/// C ABI：引擎 ABI 版本号（Python 侧按 ABI_SYMBOL 取此符号）。
#[no_mangle]
pub extern "C" fn nf_engine_abi_version() -> u32 {
    1
}
