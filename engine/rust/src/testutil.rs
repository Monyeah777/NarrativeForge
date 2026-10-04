//! 测试夹具的**唯一出处** —— 每个夹具目录带**进程号 + 自增序号**。
//!
//! **为什么必须隔离**（实测，2026-10-03）：本仓常有并发 agent 会话，两边都会跑
//! `cargo test --release`，而夹具此前写死在 `target/test-fixtures/<名>`——两个进程会互相
//! `remove_dir_all` + `create_dir_all` **同一个目录**，表现为随机几条判据变红（实测一次
//! 5 条同时红、单独复跑即全绿）。这正是 AGENTS.md 点名的「测试非隔离、共享固定临时路径」
//! 那一类根因：**不能用重跑糊过去，要把路径本身隔离开**。
#![cfg(test)]

use std::path::PathBuf;
use std::sync::atomic::{AtomicU64, Ordering};

static SEQ: AtomicU64 = AtomicU64::new(0);

/// 真仓库根（crate 在 `engine/rust/` 下，故上溯两级）。
///
/// 有些判据（如 `asset_contract` / 深度子扫描器）要的是**真语料**而不是合成夹具。
pub fn repo_root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../..")
}

/// 建一个**唯一**夹具目录并返回其路径（已建好、已清空）。
pub fn fixture(name: &str) -> PathBuf {
    let n = SEQ.fetch_add(1, Ordering::SeqCst);
    let p = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("target/test-fixtures")
        .join(format!("{}-{}-{}", name, std::process::id(), n));
    let _ = std::fs::remove_dir_all(&p);
    std::fs::create_dir_all(&p).expect("夹具根目录可建");
    p
}
