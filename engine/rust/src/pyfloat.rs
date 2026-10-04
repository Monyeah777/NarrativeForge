//! CPython `float.__repr__` 的复刻 —— 逐字节对账的**浮点口径**。
//!
//! **为什么需要它**：真源多处输出含浮点（`nf score` 的分值/权重、`verify_report` 的覆盖率、
//! `io-types` 的 `26.9%`）。在这些面写出浮点之前，`pyjson` 一直是 **fail-closed 拒绝写出**
//! （宁可炸也不吐"看起来像"的假对账）——本模块把那个缺口补上。
//!
//! **规则**（2026-10-03 用真源实测确认，非凭记忆）：
//!
//! | 情形 | 输出 |
//! |---|---|
//! | 最短往返十进制，`decpt` = 小数点位置 | `decpt <= -4 \|\| decpt > 16` → 指数形，否则定点形 |
//! | 定点形且无小数位 | 补 `.0`（`100.0` / `9999999999999998.0`） |
//! | 指数形 | 尾数不带 `.0`；指数带符号且**至少两位**补零（`1e+16` / `1e-05` / `5e-324`） |
//! | 零 | `0.0` / `-0.0`（负零保号） |
//! | 非有限 | `inf` / `-inf` / `nan`（**不是** `Infinity`/`NaN`） |
//!
//! 实测分界探针：`1e-4 → 0.0001`（定点）、`1e-5 → 1e-05`（指数）、
//! `1e15 → 1000000000000000.0`（定点）、`1e16 → 1e+16`（指数）。
//!
//! 最短十进制的**数字串**取自 Rust 自带的 `{:e}`（Rust 的浮点 Display 即"最短往返"表示），
//! 再由本模块按上表重排——不自己实现 Dragon4。

/// 复刻 `repr(float)`。
pub fn repr(x: f64) -> String {
    if x.is_nan() {
        return "nan".to_string();
    }
    if x.is_infinite() {
        return if x > 0.0 { "inf".to_string() } else { "-inf".to_string() };
    }
    if x == 0.0 {
        return if x.is_sign_negative() { "-0.0".to_string() } else { "0.0".to_string() };
    }

    let neg = x.is_sign_negative();
    let (digits, e) = shortest_digits(x.abs());
    let decpt: i32 = e + 1;

    let body = if decpt <= -4 || decpt > 16 {
        // 指数形
        let mut m = String::new();
        m.push_str(&digits[..1]);
        if digits.len() > 1 {
            m.push('.');
            m.push_str(&digits[1..]);
        }
        let (sign, mag) = if e < 0 { ('-', -e) } else { ('+', e) };
        format!("{}e{}{:02}", m, sign, mag)
    } else if decpt <= 0 {
        // 0.000ddd
        let mut out = String::from("0.");
        for _ in 0..(-decpt) {
            out.push('0');
        }
        out.push_str(&digits);
        out
    } else if decpt as usize >= digits.len() {
        // ddd000.0
        let mut out = digits.clone();
        for _ in 0..(decpt as usize - digits.len()) {
            out.push('0');
        }
        out.push_str(".0");
        out
    } else {
        // dd.ddd
        let (i, f) = digits.split_at(decpt as usize);
        format!("{}.{}", i, f)
    };

    if neg {
        format!("-{}", body)
    } else {
        body
    }
}

/// 最短往返十进制 → `(数字串, 指数E)`，值 = `d.ddd × 10^E`。
///
/// **为什么不用 Rust 内建的 `{:e}`**（实测 2026-10-03，两万例中 7 例不一致）：
/// Rust 的最短表示在**恰好落在截断点正中间**的值上用 half-up，而 CPython 用
/// **正确舍入（half-to-even）**。例：精确值 `153838026194641.125` —— CPython `repr` 得
/// `153838026194641.12`，Rust `{:e}` 得 `…13`；两者都能往返，但取的不是同一个十进制。
///
/// 本函数改为 CPython `dtoa` 的语义：**取最小的 k，使「正确舍入到 k 位有效数字」的值能往返**。
/// 正确舍入由 Rust 的**定精度**格式化保证（`{:.{k-1}e}`，half-to-even）；由于 k 从 1 递增，
/// 首个命中即"最短"；由于该值就是 k 位里最接近 x 的那个，它就是"最近"。
fn shortest_digits(a: f64) -> (String, i32) {
    for k in 1..=17usize {
        let s = format!("{:.*e}", k - 1, a);
        if s.parse::<f64>().map(|v| v == a).unwrap_or(false) {
            return split_mantissa(&s);
        }
    }
    // 兜底：17 位有效数字对 double 恒可往返，理论不可达。
    split_mantissa(&format!("{:e}", a))
}

fn split_mantissa(s: &str) -> (String, i32) {
    let (mant, exp) = s.split_once('e').unwrap_or((s, "0"));
    let mut digits: String = mant.chars().filter(|c| *c != '.').collect();
    // 定精度格式化会补尾零（如 `1.50e0`）；最短语义下不该有，兜底剪掉。
    while digits.len() > 1 && digits.ends_with('0') {
        digits.pop();
    }
    (digits, exp.parse().unwrap_or(0))
}

/// Python `round(x, n)` —— 十进制**正确舍入（half-to-even）**。
///
/// **不用** `(x * 10^n).round() / 10^n`：那是 half-away-from-zero，且乘除各引入一次二次误差。
/// Rust 的定精度格式化本身就是正确舍入（tie 走 even），故走「格式化 → 解析回」这条路。
pub fn round_to(x: f64, digits: usize) -> f64 {
    if !x.is_finite() {
        return x;
    }
    format!("{:.*}", digits, x).parse::<f64>().unwrap_or(x)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn integral_values_get_dot_zero() {
        assert_eq!(repr(0.0), "0.0");
        assert_eq!(repr(-0.0), "-0.0");
        assert_eq!(repr(1.0), "1.0");
        assert_eq!(repr(100.0), "100.0");
        assert_eq!(repr(-1.0), "-1.0");
    }

    #[test]
    fn fixed_vs_exponential_boundaries_match_cpython() {
        // decpt = 17 → 指数；decpt = 16 → 定点
        assert_eq!(repr(1e15), "1000000000000000.0");
        assert_eq!(repr(1e16), "1e+16");
        // decpt = -3 → 定点；decpt = -4 → 指数
        assert_eq!(repr(1e-4), "0.0001");
        assert_eq!(repr(1e-5), "1e-05");
    }

    #[test]
    fn exponent_is_signed_and_at_least_two_digits() {
        assert_eq!(repr(1e-5), "1e-05");
        assert_eq!(repr(1e100), "1e+100");
        assert_eq!(repr(5e-324), "5e-324");
        assert_eq!(repr(2.5e-10), "2.5e-10");
        assert_eq!(repr(1.23e20), "1.23e+20");
    }

    #[test]
    fn exponential_form_has_no_trailing_dot_zero() {
        // 真源 `repr(1e16) == '1e+16'`（**不是** '1.0e+16'）
        assert_eq!(repr(1e16), "1e+16");
        assert!(!repr(1e16).contains(".0"));
    }

    #[test]
    fn hard_shortest_repr_cases() {
        assert_eq!(repr(0.1), "0.1");
        assert_eq!(repr(0.2), "0.2");
        assert_eq!(repr(1.0 / 3.0), "0.3333333333333333");
        assert_eq!(repr(2.0 / 3.0), "0.6666666666666666");
        assert_eq!(repr(0.0001234), "0.0001234");
        assert_eq!(repr(9999999999999998.0), "9999999999999998.0");
        assert_eq!(repr(1.7976931348623157e308), "1.7976931348623157e+308");
    }

    #[test]
    fn non_finite_uses_python_spelling() {
        assert_eq!(repr(f64::INFINITY), "inf");
        assert_eq!(repr(f64::NEG_INFINITY), "-inf");
        assert_eq!(repr(f64::NAN), "nan");
    }

    #[test]
    fn round_to_matches_python_half_to_even() {
        // Python: round(2.675, 2) == 2.67（2.675 实际略小于中点）；round(0.125, 2) == 0.12（tie→even）
        assert_eq!(round_to(2.675, 2), 2.67);
        assert_eq!(round_to(0.125, 2), 0.12);
        assert_eq!(round_to(0.135, 2), 0.14);
        assert_eq!(round_to(2.5, 0), 2.0);
        assert_eq!(round_to(12.5722222, 2), 12.57);
    }

    #[test]
    fn exact_half_tie_rounds_to_even_like_cpython() {
        // 实测回归（2026-10-03，两万例普查里唯一的分歧族）：
        // 该 double 的**精确值**是 153838026194641.125 —— 恰好落在 17 位正中。
        // CPython 取 half-to-even 得 .12；Rust 内建 `{:e}` 的 half-up 得 .13。
        // 两条十进制都能往返，但真源只认 .12。
        let x = f64::from_bits(0x42e17d469cefda24);
        assert_eq!(repr(x), "153838026194641.12");
        assert_eq!(repr(-x), "-153838026194641.12");
    }

    #[test]
    fn every_value_round_trips_back_to_itself() {
        // 最强自证：解析回去必须得到同一个 f64（最短往返语义）
        let vals = [
            0.1, 0.2, 1.0 / 3.0, 9999999999999998.0, 1e15, 1e16, 1e-4, 1e-5, 5e-324,
            1.7976931348623157e308, 123456789012345.0, 2.5e-10,
        ];
        for v in vals {
            let s = repr(v);
            assert_eq!(s.parse::<f64>().unwrap(), v, "repr={} 未能往返", s);
        }
    }
}
