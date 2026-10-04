//! RFC 6962 风格 Merkle 折叠 —— **与 Python 真源 `desktop/src/core/receipts.py` 同规则**。
//!
//! 叶 = `SHA-256(0x00 ‖ 规范载荷)`；内部节点 = `SHA-256(0x01 ‖ 左 ‖ 右)`；
//! 分裂点 = **小于 n 的最大 2 的幂**（不是"平均二分"——这条差异会让根完全对不上）。
//!
//! 本模块是纯函数：不读盘、不写盘、不依赖任何外部状态。

use sha2::{Digest, Sha256};

/// 32 字节摘要。
pub type Hash = [u8; 32];

const HEX: &[u8; 16] = b"0123456789abcdef";

/// `sha256(data)`。
pub fn sha256(data: &[u8]) -> Hash {
    Sha256::digest(data).into()
}

/// 小写十六进制（Python `bytes.hex()` 同形）。
pub fn hex(h: &Hash) -> String {
    let mut s = String::with_capacity(64);
    for b in h.iter() {
        s.push(HEX[(b >> 4) as usize] as char);
        s.push(HEX[(b & 0x0f) as usize] as char);
    }
    s
}

/// 叶哈希：域分隔前缀 `0x00`。
pub fn leaf_hash(payload: &[u8]) -> Hash {
    let mut h = Sha256::new();
    h.update([0x00u8]);
    h.update(payload);
    h.finalize().into()
}

/// 内部节点哈希：域分隔前缀 `0x01`。
pub fn node_hash(left: &Hash, right: &Hash) -> Hash {
    let mut h = Sha256::new();
    h.update([0x01u8]);
    h.update(left);
    h.update(right);
    h.finalize().into()
}

/// 分裂点 = 小于 `n` 的最大 2 的幂（`n >= 2` 时）。与 Python 的 `while mid * 2 < n` 逐位同解。
fn split(n: usize) -> usize {
    let mut mid = 1usize;
    while mid * 2 < n {
        mid *= 2;
    }
    mid
}

/// 空集 → `None`；单叶 → 该叶本身（与 Python `merkle_root` 同口径）。
pub fn merkle_root(leaves: &[Hash]) -> Option<Hash> {
    match leaves.len() {
        0 => None,
        1 => Some(leaves[0]),
        n => {
            let mid = split(n);
            let l = merkle_root(&leaves[..mid])?;
            let r = merkle_root(&leaves[mid..])?;
            Some(node_hash(&l, &r))
        }
    }
}

/// 审计路径的一步：`sibling_is_left` 表示兄弟在折叠时的位置（左 / 右）。
#[derive(Clone, Copy, Debug)]
pub struct ProofStep {
    pub sibling_is_left: bool,
    pub hash: Hash,
}

/// 包含证明，**自底向上**（叶的兄弟在前）。调用方按序折叠即得根。
pub fn inclusion_proof(leaves: &[Hash], index: usize) -> Vec<ProofStep> {
    let mut out = Vec::new();
    if leaves.is_empty() || index >= leaves.len() {
        return out;
    }
    walk(leaves, index, &mut out);
    out.reverse();
    out
}

fn walk(sub: &[Hash], i: usize, out: &mut Vec<ProofStep>) {
    if sub.len() <= 1 {
        return;
    }
    let mid = split(sub.len());
    if i < mid {
        let sib = merkle_root(&sub[mid..]).expect("右半非空");
        out.push(ProofStep { sibling_is_left: false, hash: sib });
        walk(&sub[..mid], i, out);
    } else {
        let sib = merkle_root(&sub[..mid]).expect("左半非空");
        out.push(ProofStep { sibling_is_left: true, hash: sib });
        walk(&sub[mid..], i - mid, out);
    }
}

/// 读者侧折叠：不依赖仓库其余内容即可复算根。用于自校验（证明内部一致）。
pub fn fold_proof(leaf: &Hash, proof: &[ProofStep]) -> Hash {
    let mut cur = *leaf;
    for step in proof {
        cur = if step.sibling_is_left {
            node_hash(&step.hash, &cur)
        } else {
            node_hash(&cur, &step.hash)
        };
    }
    cur
}

#[cfg(test)]
mod tests {
    use super::*;

    fn leaves(n: usize) -> Vec<Hash> {
        (0..n).map(|i| leaf_hash(format!("leaf-{}", i).as_bytes())).collect()
    }

    #[test]
    fn split_matches_python_rule() {
        // 与 Python `while mid * 2 < n` 同解：n=2→1, n=3→2, n=4→2, n=5→4, n=8→4, n=9→8
        assert_eq!(split(2), 1);
        assert_eq!(split(3), 2);
        assert_eq!(split(4), 2);
        assert_eq!(split(5), 4);
        assert_eq!(split(8), 4);
        assert_eq!(split(9), 8);
    }

    #[test]
    fn root_of_empty_and_single() {
        assert!(merkle_root(&[]).is_none());
        let l = leaves(1);
        assert_eq!(merkle_root(&l).unwrap(), l[0]);
    }

    #[test]
    fn every_leaf_folds_to_root() {
        for n in 1..=33usize {
            let ls = leaves(n);
            let root = merkle_root(&ls).expect("非空");
            for i in 0..n {
                let proof = inclusion_proof(&ls, i);
                assert_eq!(fold_proof(&ls[i], &proof), root, "n={} i={}", n, i);
            }
        }
    }

    #[test]
    fn domain_separation_is_real() {
        let a = leaf_hash(b"x");
        let b = node_hash(&a, &a);
        assert_ne!(a, b);
    }
}
