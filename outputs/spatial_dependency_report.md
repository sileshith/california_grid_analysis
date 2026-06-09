# Spatial Dependency Analysis Report

**California Grid Balancing Authorities**

**Generated:** 2026-06-09 08:55:22

---

## Executive Summary

This analysis investigates spatial dependencies and temporal relationships between California's five balancing authorities to determine whether graph-based modeling (e.g., Graph Neural Networks) is justified.

### Key Findings

- **Average Correlation:** 0.484
- **Correlation Range:** 0.282 to 0.781
- **Significant Granger Relationships:** 20/20 (100.0%)

### Recommendation

⚠️ **MODERATE SPATIAL DEPENDENCIES DETECTED**

Graph-based modeling may provide marginal improvements:
- Moderate correlation (0.484)
- Some Granger causality relationships (20)

**Recommendation:** Consider GNN if per-authority models underperform.

---

## 1. Correlation Analysis

### Pairwise Pearson Correlations

Simultaneous (zero-lag) correlations between authority demand patterns:

```
balancing_authority      BANC      CISO       IID      LDWP      TIDC
balancing_authority                                                  
BANC                 1.000000  0.451621  0.282681  0.282092  0.493541
CISO                 0.451621  1.000000  0.603739  0.514633  0.781117
IID                  0.282681  0.603739  1.000000  0.414400  0.586468
LDWP                 0.282092  0.514633  0.414400  1.000000  0.430559
TIDC                 0.493541  0.781117  0.586468  0.430559  1.000000
```

### Interpretation

- **High correlation (>0.8):** Strong synchronous demand patterns
- **Moderate correlation (0.5-0.8):** Some shared patterns
- **Low correlation (<0.5):** Independent demand dynamics

---

## 2. Lagged Cross-Correlation Analysis

Tests whether one authority's demand leads or lags another:

### Top 5 Strongest Lagged Relationships

| Authority 1 | Authority 2 | Zero Lag | Max Corr | Lag (hours) | Lead Authority |
|-------------|-------------|----------|----------|-------------|----------------|
| CISO | TIDC | 0.781 | 0.781 | +0 | simultaneous |
| IID | TIDC | 0.586 | 0.612 | -1 | TIDC |
| CISO | IID | 0.604 | 0.604 | +0 | simultaneous |
| CISO | LDWP | 0.515 | 0.517 | -1 | LDWP |
| BANC | TIDC | 0.494 | 0.494 | +0 | simultaneous |

### Interpretation

- **Positive lag:** Authority 1 leads Authority 2
- **Negative lag:** Authority 2 leads Authority 1
- **Zero lag:** Simultaneous relationship

---

## 3. Granger Causality Analysis

Tests whether past values of one authority help predict another:

### Significant Relationships (p < 0.05): 20

| Cause | Effect | F-Statistic | P-Value | RSS Improvement (%) |
|-------|--------|-------------|---------|---------------------|
| TIDC | IID | 116.93 | 0.0000 | 35.72% |
| TIDC | CISO | 70.77 | 0.0000 | 25.17% |
| IID | TIDC | 60.66 | 0.0000 | 22.38% |
| IID | CISO | 50.02 | 0.0000 | 19.21% |
| IID | LDWP | 39.93 | 0.0000 | 15.95% |
| TIDC | BANC | 36.90 | 0.0000 | 14.92% |
| CISO | TIDC | 33.62 | 0.0000 | 13.78% |
| CISO | BANC | 26.72 | 0.0000 | 11.27% |
| CISO | IID | 26.45 | 0.0000 | 11.17% |
| IID | BANC | 23.63 | 0.0000 | 10.10% |
| TIDC | LDWP | 23.05 | 0.0000 | 9.87% |
| LDWP | CISO | 21.84 | 0.0000 | 9.40% |
| LDWP | BANC | 15.99 | 0.0000 | 7.06% |
| LDWP | TIDC | 15.99 | 0.0000 | 7.06% |
| CISO | LDWP | 14.31 | 0.0000 | 6.37% |
| BANC | IID | 7.17 | 0.0000 | 3.29% |
| BANC | CISO | 6.95 | 0.0000 | 3.20% |
| LDWP | IID | 5.03 | 0.0000 | 2.33% |
| BANC | LDWP | 3.94 | 0.0000 | 1.84% |
| BANC | TIDC | 2.61 | 0.0018 | 1.23% |

### Interpretation

- **RSS Improvement:** How much better the model predicts when including the cause
- **Significant relationships indicate predictive value across authorities**

---

## 4. Implications for Forecasting

### Current Approach (Per-Authority Models)

- ✅ LightGBM: 3.29% MAPE average
- ✅ Each authority modeled independently
- ✅ Simple, interpretable, production-ready

### Graph Neural Network Potential

**MODERATE POTENTIAL** - GNN might provide:
- Marginal improvements from weak dependencies
- Better handling of edge cases

**Expected Improvement:** 5-15% MAPE reduction

---

## 5. Recommendations

### ⚠️ OPTIONAL: TEST GNN AS EXPERIMENT

1. **Quick prototype:** Simple GNN with 1-2 graph layers
2. **Compare:** GNN vs LightGBM on validation set
3. **Decision:** Only deploy if >10% improvement
4. **Fallback:** Continue with LightGBM if no improvement

---

## Appendix: Full Results

### Complete Lagged Correlation Table

```
authority_1 authority_2  zero_lag_corr  max_corr  max_corr_lag lead_authority
       BANC        CISO       0.451621  0.451621             0   simultaneous
       BANC         IID       0.282681  0.293508             1           BANC
       BANC        LDWP       0.282092  0.282092             0   simultaneous
       BANC        TIDC       0.493541  0.493541             0   simultaneous
       CISO         IID       0.603739  0.603739             0   simultaneous
       CISO        LDWP       0.514633  0.516522            -1           LDWP
       CISO        TIDC       0.781117  0.781117             0   simultaneous
        IID        LDWP       0.414400  0.445447            23            IID
        IID        TIDC       0.586468  0.612353            -1           TIDC
       LDWP        TIDC       0.430559  0.430559             0   simultaneous
```

### Complete Granger Causality Results

```
cause effect     f_stat      p_value  significant  rss_improvement_pct
 BANC   CISO   6.950725 1.552203e-12         True             3.197685
 BANC    IID   7.167692 5.091483e-13         True             3.294213
 BANC   LDWP   3.943537 4.704400e-06         True             1.839678
 BANC   TIDC   2.614252 1.810983e-03         True             1.227170
 CISO   BANC  26.720206 1.110223e-16         True            11.267841
 CISO    IID  26.446782 1.110223e-16         True            11.165413
 CISO   LDWP  14.314544 1.110223e-16         True             6.369629
 CISO   TIDC  33.617132 1.110223e-16         True            13.775605
  IID   BANC  23.634118 1.110223e-16         True            10.097859
  IID   CISO  50.016404 1.110223e-16         True            19.205089
  IID   LDWP  39.933181 1.110223e-16         True            15.950951
  IID   TIDC  60.655267 1.110223e-16         True            22.376078
 LDWP   BANC  15.994206 1.110223e-16         True             7.064240
 LDWP   CISO  21.843471 1.110223e-16         True             9.404744
 LDWP    IID   5.030571 2.481479e-08         True             2.334943
 LDWP   TIDC  15.986398 1.110223e-16         True             7.061034
 TIDC   BANC  36.901195 1.110223e-16         True            14.920554
 TIDC   CISO  70.766734 1.110223e-16         True            25.167465
 TIDC    IID 116.932043 1.110223e-16         True            35.720942
 TIDC   LDWP  23.051195 1.110223e-16         True             9.873391
```

