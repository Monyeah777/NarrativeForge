namespace Nf.Engine;

/// <summary>
/// 产出形态面（45 波 · check32 output_forms 子扫描）所依赖的**三张外部表**——全部**机械导出**，
/// 不手抄：量化口径函数名集（`hasattr(quant_metrics, fn)` 等价）、度量族在册表（`domain_metrics.FAMILIES` 键）、
/// 组合证书 JSON Schema（`pack_combo.CERT_SCHEMA`）。导出件 `_output_tables.cs.txt` 一并留档可复核。
///
/// 表滞后于仓库的风险由**面级对账**兜住：`nf output list/check` 一旦与 Python 不同就立刻显形。
/// </summary>
public static class OutputTables
{
    /// <summary>core/quant_metrics 的公开属性名集合（供 `hasattr(qm, fn)` 等价判定）。机械导出。</summary>
    public static readonly HashSet<string> QuantMetricNames = new(StringComparer.Ordinal)
    {
        "ANNUAL_FACTORS",
        "Any",
        "DIGITS",
        "Dict",
        "GIPS_ALIGNMENT",
        "List",
        "Path",
        "Sequence",
        "Tuple",
        "_block",
        "_geo_link",
        "_mean",
        "_pearson",
        "_r",
        "_rank",
        "_stdev",
        "annotations",
        "annualized_return",
        "annualized_volatility",
        "calmar",
        "csv",
        "cumulative_return",
        "drawdown_series",
        "information_coefficient",
        "information_ratio",
        "load_equity_curve",
        "log_returns",
        "math",
        "max_drawdown",
        "mermaid_declaration_flow",
        "performance_report",
        "returns",
        "sharpe",
        "simple_returns",
        "tracking_error",
        "turnover",
        "vega_drawdown",
        "vega_equity_curve",
    };

    /// <summary>core/domain_metrics.FAMILIES 的键（度量族在册表）。机械导出。</summary>
    public static readonly HashSet<string> DomainMetricFamilies = new(StringComparer.Ordinal)
    {
        "agreement",
        "calibration",
        "classification",
        "contract_compliance",
        "drift",
        "exact_judgement",
        "extraction",
        "generation",
        "latency_cost",
        "preference",
        "regression",
        "retrieval",
    };

    /// <summary>core/pack_combo.CERT_SCHEMA（组合证书 JSON Schema）。机械导出，含 2020-12 子集关键字。</summary>
    public const string ComboCertSchemaJson = @"{
  ""$schema"": ""https://json-schema.org/draft/2020-12/schema"",
  ""additionalProperties"": false,
  ""properties"": {
    ""assets_borrowed"": {
      ""type"": ""array""
    },
    ""assets_unresolved"": {
      ""maxItems"": 0,
      ""type"": ""array""
    },
    ""dependency_closure"": {
      ""additionalProperties"": false,
      ""properties"": {
        ""core"": {
          ""type"": ""array""
        },
        ""dangling"": {
          ""maxItems"": 0,
          ""type"": ""array""
        },
        ""explicit"": {
          ""type"": ""array""
        }
      },
      ""required"": [
        ""core"",
        ""explicit"",
        ""dangling""
      ],
      ""type"": ""object""
    },
    ""digest"": {
      ""pattern"": ""^[0-9a-f]{32}$"",
      ""type"": ""string""
    },
    ""event_closure"": {
      ""additionalProperties"": false,
      ""properties"": {
        ""published"": {
          ""type"": ""array""
        },
        ""unbridged"": {
          ""maxItems"": 0,
          ""type"": ""array""
        }
      },
      ""required"": [
        ""published"",
        ""unbridged""
      ],
      ""type"": ""object""
    },
    ""events_unpublished"": {
      ""maxItems"": 0,
      ""type"": ""array""
    },
    ""extra_modules"": {
      ""items"": {
        ""type"": ""string""
      },
      ""type"": ""array""
    },
    ""label"": {
      ""minLength"": 2,
      ""type"": ""string""
    },
    ""layer_stacks"": {
      ""items"": {
        ""additionalProperties"": false,
        ""properties"": {
          ""layer"": {
            ""minLength"": 3,
            ""type"": ""string""
          },
          ""modules"": {
            ""items"": {
              ""minLength"": 2,
              ""type"": ""string""
            },
            ""minItems"": 1,
            ""type"": ""array""
          }
        },
        ""required"": [
          ""layer"",
          ""modules""
        ],
        ""type"": ""object""
      },
      ""minItems"": 1,
      ""type"": ""array""
    },
    ""legal"": {
      ""const"": true
    },
    ""module_count"": {
      ""minimum"": 1,
      ""type"": ""integer""
    },
    ""module_missing_contract"": {
      ""maxItems"": 0,
      ""type"": ""array""
    },
    ""modules"": {
      ""items"": {
        ""type"": ""string""
      },
      ""minItems"": 1,
      ""type"": ""array""
    },
    ""modules_borrowed"": {
      ""type"": ""array""
    },
    ""note"": {
      ""minLength"": 4,
      ""type"": ""string""
    },
    ""packs"": {
      ""items"": {
        ""minLength"": 2,
        ""type"": ""string""
      },
      ""type"": ""array""
    },
    ""references_unresolved"": {
      ""maxItems"": 0,
      ""type"": ""array""
    },
    ""schema"": {
      ""const"": ""nf-combo/1""
    },
    ""unknown_packs"": {
      ""items"": {
        ""type"": ""string""
      },
      ""type"": ""array""
    }
  },
  ""required"": [
    ""schema"",
    ""packs"",
    ""modules"",
    ""module_count"",
    ""layer_stacks"",
    ""dependency_closure"",
    ""event_closure"",
    ""legal"",
    ""digest""
  ],
  ""title"": ""nf-combo/1 组合证书"",
  ""type"": ""object""
}";
}
