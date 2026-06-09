# Spatial Feature Forecasting Report

**California Grid Demand Forecasting**

**Generated:** 2026-06-09 09:08:45

---

## Executive Summary

This analysis validates whether spatial information improves forecasting performance before implementing a Graph Neural Network (GNN).

### Key Findings

- **Baseline LightGBM MAPE:** 62.92%
- **LightGBM + Spatial Features MAPE:** 66.39%
- **Overall Improvement:** -3.47% (-5.5%)
- **Authorities Improved:** 3/5
- **Average Spatial Feature Importance:** 13.7%

### Recommendation

❌ **GNN IMPLEMENTATION: NOT JUSTIFIED**

Spatial features do not improve performance. GNN implementation is not justified.

---

## 1. Performance Comparison

### Overall Results

| Authority | Baseline MAPE | Spatial MAPE | Improvement | Spatial Importance |
|-----------|---------------|--------------|-------------|--------------------|
| BANC | 4.33% | 5.42% | -1.09% (-25.1%) | 41.9% |
| CISO | 1.87% | 1.73% | +0.14% (+7.5%) | 6.3% |
| IID | 3.33% | 3.16% | +0.17% (+5.0%) | 1.5% |
| LDWP | 303.13% | 319.79% | -16.67% (-5.5%) | 10.7% |
| TIDC | 1.96% | 1.86% | +0.10% (+4.9%) | 8.2% |
| **AVERAGE** | **62.92%** | **66.39%** | **-3.47% (-5.5%)** | **13.7%** |

### Interpretation

❌ **No improvement detected.** Spatial features do not add predictive value.

---

## 2. Authority-Specific Analysis

### Top 3 Improvements

**CISO:** +0.14% (+7.5%)
- Baseline: 1.87% → Spatial: 1.73%
- Spatial feature importance: 6.3%

**IID:** +0.17% (+5.0%)
- Baseline: 3.33% → Spatial: 3.16%
- Spatial feature importance: 1.5%

**TIDC:** +0.10% (+4.9%)
- Baseline: 1.96% → Spatial: 1.86%
- Spatial feature importance: 8.2%

### LDWP Analysis

- **Baseline MAPE:** 303.13%
- **Spatial MAPE:** 319.79%
- **Improvement:** -16.67% (-5.5%)
- **Adjusted MAPE (≥250 MW):** 2.68%
- **Spatial feature importance:** 10.7%

❌ LDWP did not benefit from spatial features.

---

## 3. Feature Importance Analysis

### Feature Type Importance

- **Baseline Features (temporal):** 86.3%
- **Spatial Features (graph-inspired):** 13.7%

❌ Spatial features have low importance (<15% of total importance).

### Most Important Spatial Features

Aggregated across all authorities:

1. `spatial_lag1h_TIDC`: 1728646841
2. `spatial_granger_causal_avg`: 1327667521
3. `spatial_corr_weighted_demand`: 804143115
4. `spatial_lag24h_TIDC`: 775737081
5. `spatial_avg_connected`: 736496206
6. `spatial_lag1h_IID`: 691426494
7. `spatial_lag1h_LDWP`: 547372650
8. `spatial_lag24h_BANC`: 460851810
9. `spatial_rolling_24h_avg`: 359210508
10. `spatial_lag1h_BANC`: 326811209

---

## 4. Comprehensive Metrics

### All Evaluation Metrics

| Authority | MAPE | SMAPE | MAE (MW) | RMSE (MW) | Median % Error |
|-----------|------|-------|----------|-----------|----------------|
| BANC | 5.42% | 5.45% | 113.4 | 410.9 | 4.24% |
| CISO | 1.73% | 1.72% | 416.2 | 554.7 | 1.29% |
| IID | 3.16% | 3.13% | 12.9 | 18.2 | 2.55% |
| LDWP | 319.79% | 36.41% | 447.2 | 881.3 | 2.99% |
| TIDC | 1.86% | 1.86% | 5.1 | 6.7 | 1.45% |

---

## 5. GNN Implementation Decision

### ❌ DO NOT IMPLEMENT GNN

**Evidence:**
- Spatial features did not improve performance (-5.5%)
- Spatial features account for only 13.7% of model importance
- Authorities operate independently for forecasting purposes

**Recommendation:**
- **Do not implement GNN** - spatial modeling is not justified
- Continue with baseline LightGBM (already excellent performance)
- Focus on per-authority improvements:
  - Hyperparameter tuning
  - Additional temporal features
  - External data integration (weather, events)
  - Ensemble methods

---

## 6. Research Progression Summary

This analysis completes the evidence-based research progression:

1. ✅ **Forecasting Benchmark** - Established baseline (Naive: 11.05% MAPE)
2. ✅ **Failure Analysis** - Identified LDWP as outlier (32.76% MAPE)
3. ✅ **Metric Robustness Analysis** - Validated SMAPE and adjusted MAPE
4. ✅ **Spatial Dependency Analysis** - Found correlations and Granger causality
5. ✅ **Spatial Feature Validation** - Tested graph-inspired features
6. ❌ **Evidence-Based GNN Decision** - NOT JUSTIFIED

---

## 7. Next Steps

### Recommended Actions

1. **Deploy baseline LightGBM** as production model
2. **Focus on per-authority improvements**
3. **Investigate external features** (weather, events)
4. **Do not pursue GNN** - not justified by evidence

---

## Appendix: Detailed Results

### Complete Comparison Table

```
authority  test_mape  test_smape   test_mae  test_rmse  median_pct_error  ldwp_adjusted_mape  test_samples  n_features  n_baseline_features  n_spatial_features  baseline_importance_pct  spatial_importance_pct  baseline_mape  improvement_mape  improvement_pct
     BANC   5.418203    5.449270 113.432359 410.947060          4.244212                 NaN           479          23                    7                  16                58.111511               41.888489       4.330785         -1.087418       -25.109023
     CISO   1.728712    1.722704 416.195350 554.707846          1.293141                 NaN           479          23                    7                  16                93.670912                6.329088       1.869450          0.140738         7.528308
      IID   3.164720    3.133124  12.902590  18.186956          2.547602                 NaN           479          23                    7                  16                98.547253                1.452747       3.332903          0.168183         5.046130
     LDWP 319.792775   36.414964 447.173268 881.348707          2.990217            2.682693           479          23                    7                  16                89.334949               10.665051     303.127408        -16.665367        -5.497809
     TIDC   1.862041    1.855181   5.125551   6.722175          1.453942                 NaN           479          23                    7                  16                91.791365                8.208635       1.957975          0.095935         4.899695
```

