namespace Nf.Engine;

/// <summary>
/// CPython <c>random.Random(int)</c> 的逐位复刻：MT19937 + <c>genrand_res53</c> + <c>_randbelow</c> + <c>sample</c>。
///
/// 为什么要逐位复刻：广度证明用定种子抽样（`seed=20260923`）生成三元/四元/五元/六元组合集；
/// 若 C# 用另一套抽样，统计会"看起来对"但样本集与 Python 不同——那是隐性不等价。
/// 本类保证**同样的种子与同样的调用序列产出同样的集合**，判据 = 与 Python 导出的样本集逐项相等。
///
/// 依据：CPython <c>Modules/_randommodule.c</c>（init_by_array / genrand_res53 / _randbelow_with_getrandbits）
/// 与 <c>Lib/random.py</c>（sample 的 set 分支）。
/// </summary>
public sealed class PyRandom
{
    private const int N = 624;
    private const int M = 397;
    private const uint MatrixA = 0x9908b0dfU;
    private const uint UpperMask = 0x80000000U;
    private const uint LowerMask = 0x7fffffffU;

    private readonly uint[] _mt = new uint[N];
    private int _mti = N + 1;

    public PyRandom(long seed)
    {
        SeedFromInt(seed);
    }

    private void InitGenrand(uint s)
    {
        _mt[0] = s;
        for (var i = 1; i < N; i++)
        {
            _mt[i] = unchecked(1812433253U * (_mt[i - 1] ^ (_mt[i - 1] >> 30)) + (uint)i);
        }
        _mti = N;
    }

    /// <summary>等价 CPython <c>random_seed</c> 的整数分支：小端字节 → 32 位字数组 → <c>init_by_array</c>。</summary>
    private void SeedFromInt(long seed)
    {
        var n = Math.Abs(seed);
        var bytes = new List<byte>();
        if (n == 0)
        {
            bytes.Add(0);
        }
        else
        {
            var value = n;
            while (value > 0)
            {
                bytes.Add((byte)(value & 0xff));
                value >>= 8;
            }
        }
        var key = new uint[(bytes.Count + 3) / 4];
        for (var i = 0; i < bytes.Count; i++) key[i / 4] |= (uint)bytes[i] << (8 * (i % 4));
        InitByArray(key, key.Length);
    }

    private void InitByArray(uint[] key, int keyLength)
    {
        InitGenrand(19650218U);
        int i = 1, j = 0;
        var k = Math.Max(N, keyLength);
        for (; k > 0; k--)
        {
            _mt[i] = unchecked((_mt[i] ^ ((_mt[i - 1] ^ (_mt[i - 1] >> 30)) * 1664525U)) + key[j] + (uint)j);
            i++;
            j++;
            if (i >= N) { _mt[0] = _mt[N - 1]; i = 1; }
            if (j >= keyLength) j = 0;
        }
        for (k = N - 1; k > 0; k--)
        {
            _mt[i] = unchecked((_mt[i] ^ ((_mt[i - 1] ^ (_mt[i - 1] >> 30)) * 1566083941U)) - (uint)i);
            i++;
            if (i >= N) { _mt[0] = _mt[N - 1]; i = 1; }
        }
        _mt[0] = 0x80000000U;
    }

    public uint NextUInt32()
    {
        uint y;
        if (_mti >= N)
        {
            int kk;
            for (kk = 0; kk < N - M; kk++)
            {
                y = (_mt[kk] & UpperMask) | (_mt[kk + 1] & LowerMask);
                _mt[kk] = _mt[kk + M] ^ (y >> 1) ^ ((y & 1) != 0 ? MatrixA : 0U);
            }
            for (; kk < N - 1; kk++)
            {
                y = (_mt[kk] & UpperMask) | (_mt[kk + 1] & LowerMask);
                _mt[kk] = _mt[kk + (M - N)] ^ (y >> 1) ^ ((y & 1) != 0 ? MatrixA : 0U);
            }
            y = (_mt[N - 1] & UpperMask) | (_mt[0] & LowerMask);
            _mt[N - 1] = _mt[M - 1] ^ (y >> 1) ^ ((y & 1) != 0 ? MatrixA : 0U);
            _mti = 0;
        }

        y = _mt[_mti++];
        y ^= y >> 11;
        y ^= (y << 7) & 0x9d2c5680U;
        y ^= (y << 15) & 0xefc60000U;
        y ^= y >> 18;
        return y;
    }

    /// <summary>等价 CPython <c>random()</c>（genrand_res53）。</summary>
    public double NextDouble()
    {
        var a = NextUInt32() >> 5;
        var b = NextUInt32() >> 6;
        return (a * 67108864.0 + b) * (1.0 / 9007199254740992.0);
    }

    /// <summary>等价 CPython <c>_randbelow_with_getrandbits(n)</c>（n &gt; 0）。</summary>
    public int RandBelow(int n)
    {
        var k = BitLength(n);
        while (true)
        {
            var r = GetRandBits(k);
            if (r < n) return (int)r;
        }
    }

    private uint GetRandBits(int k)
        => k <= 32 ? NextUInt32() >> (32 - k) : (uint)(RandBelow(int.MaxValue));   // 本工程只用 k ≤ 7

    private static int BitLength(int value)
    {
        var bits = 0;
        while (value > 0) { bits++; value >>= 1; }
        return bits;
    }

    /// <summary>
    /// 等价 CPython <c>random.sample(population, k)</c> 中 <c>n &gt; setsize</c> 的 **set 分支**
    /// （本工程的 n=111、k=3..6 恒走该分支）。
    /// </summary>
    public List<T> SampleSet<T>(IReadOnlyList<T> population, int k)
    {
        var n = population.Count;
        var selected = new HashSet<int>();
        var result = new List<T>(k);
        for (var i = 0; i < k; i++)
        {
            var j = RandBelow(n);
            while (selected.Contains(j)) j = RandBelow(n);
            selected.Add(j);
            result.Add(population[j]);
        }
        return result;
    }
}
