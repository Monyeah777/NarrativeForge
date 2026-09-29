namespace Nf.Engine;

/// <summary>
/// 概念闭包求值器（<c>scripts/ai_domain_closure.py</c>）依赖的**键级自检样例表**——机械导出件
/// （同 <c>_doc_tables.cs.txt</c> / <c>CheckGuide</c> / <c>OutputTables</c> 的口径），导出件
/// <c>_closure_samples.cs.txt</c> 一并留档可复核。
///
/// 表滞后于仓库的风险由**面级对账**兜住：<c>--check</c> 一旦与真源不同就立刻显形。
/// </summary>
public static class ClosureSamples
{
    /// <summary>`scripts/ai_domain_closure.py::_SAMPLES`（键级自检样例集）——机械导出，不自抄。</summary>
    public const string SamplesJson = @"{
  ""CONCEPT_GRAPH"": {
    ""alias_pair"": [
      ""RAG"",
      ""C28""
    ],
    ""branch_drop"": ""C45"",
    ""branch_empty"": ""app"",
    ""closure_root"": ""C00"",
    ""closure_size"": 13,
    ""closure_target"": ""C22"",
    ""frontier_has"": ""C02"",
    ""frontier_loaded"": [
      ""C00"",
      ""C01""
    ],
    ""frontier_not"": ""C25"",
    ""inject_cycle"": [
      ""C09"",
      ""C12""
    ],
    ""inject_dangling"": [
      ""C22"",
      ""C99""
    ],
    ""inject_dup_alias"": [
      ""C29"",
      ""RAG""
    ],
    ""min_closure"": [
      ""C00"",
      ""C01""
    ],
    ""min_target"": ""C01"",
    ""missing_has"": [
      ""C22"",
      ""C09""
    ],
    ""missing_loaded"": [
      ""C01"",
      ""C07"",
      ""C08"",
      ""C10"",
      ""C18""
    ],
    ""missing_size"": 8,
    ""resolve_cases"": [
      [
        ""RAG"",
        ""C28""
      ],
      [
        ""PagedAttention"",
        ""C22""
      ],
      [
        ""  autodiff  "",
        ""C08""
      ]
    ]
  },
  ""QUANT_GRAPH"": {
    ""alias_pair"": [
      ""因子"",
      ""Q09""
    ],
    ""branch_drop"": ""Q30"",
    ""branch_empty"": ""research"",
    ""closure_root"": ""Q00"",
    ""closure_size"": 15,
    ""closure_target"": ""Q17"",
    ""frontier_has"": ""Q02"",
    ""frontier_loaded"": [
      ""Q00"",
      ""Q01""
    ],
    ""frontier_not"": ""Q09"",
    ""inject_cycle"": [
      ""Q09"",
      ""Q17""
    ],
    ""inject_dangling"": [
      ""Q17"",
      ""Q99""
    ],
    ""inject_dup_alias"": [
      ""Q30"",
      ""因子""
    ],
    ""min_closure"": [
      ""Q00"",
      ""Q01""
    ],
    ""min_target"": ""Q01"",
    ""missing_has"": [
      ""Q17"",
      ""Q09""
    ],
    ""missing_loaded"": [
      ""Q00"",
      ""Q01"",
      ""Q02"",
      ""Q07"",
      ""Q10""
    ],
    ""missing_size"": 10,
    ""resolve_cases"": [
      [
        ""因子"",
        ""Q09""
      ],
      [
        ""组合优化"",
        ""Q12""
      ],
      [
        ""  Quant Overview  "",
        ""Q01""
      ]
    ]
  }
}";
}
