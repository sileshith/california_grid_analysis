# California Grid Forecasting Strategy & Benchmark Plan

**Document Version:** 1.0  
**Date:** 2026-06-09  
**Status:** Planning Phase  
**Purpose:** Define forecasting approach, baseline models, and GNN readiness criteria

---

## Executive Summary

This document outlines a systematic forecasting benchmark plan for the California Grid Intelligence Platform. The strategy follows a **crawl-walk-run** approach:

1. **Crawl:** Establish baseline models (naive, moving average, Prophet)
2. **Walk:** Implement ML models (LightGBM, XGBoost) with engineered features
3. **Run:** Evaluate GNN necessity based on spatial dependency evidence

**Key Decision Point:** GNNs are justified ONLY if spatial dependencies between authorities demonstrably improve forecast accuracy beyond traditional ML approaches.

**Expected Timeline:** 10-14 days from baseline to GNN readiness assessment

---

## 1. Forecast Target Selection

### Primary Targets (Implement All Three)

#### Target 1: Demand Forecasting (MW)
**Objective:** Predict hourly demand 24 hours ahead for each balancing authority

**Why This Matters:**
- Core operational metric for grid operators
- Enables proactive resource allocation
- Direct business value (cost avoidance)
- Standard benchmark in energy forecasting literature

**Forecast Horizon:** 24 hours ahead (single-step)

**Granularity:** Hourly, per authority (5 separate models initially)

**Success Criteria:**
- MAPE < 10% (excellent)
- MAPE 10-20% (good)
- MAPE > 20% (needs improvement)

**Resume Value:** ⭐⭐⭐⭐⭐ (Core ML skill, quantifiable results)

---

#### Target 2: Grid Stress Index Forecasting (0-100 scale)
**Objective:** Predict stress index 24 hours ahead to enable proactive alert generation

**Why This Matters:**
- Directly supports operational decision-making
- Enables "what-if" scenario planning
- Combines demand + capacity constraints
- More interpretable than raw demand for stakeholders

**Forecast Horizon:** 24 hours ahead

**Granularity:** Hourly, per authority

**Success Criteria:**
- MAE < 5 points (excellent)
- MAE 5-10 points (good)
- MAE > 10 points (needs improvement)

**Resume Value:** ⭐⭐⭐⭐ (Domain-specific, shows business acumen)

---

#### Target 3: High-Stress Event Classification (Binary)
**Objective:** Predict whether stress index will exceed 90 (High Priority threshold) in next 24 hours

**Why This Matters:**
- Directly actionable for operators
- Addresses class imbalance (only 0.6% of hours are high-stress)
- Enables precision/recall tradeoff analysis
- Supports cost-benefit analysis (false positive vs false negative costs)

**Forecast Horizon:** 24 hours ahead

**Granularity:** Hourly, per authority

**Success Criteria:**
- Recall > 80% (catch most high-stress events)
- Precision > 50% (avoid alert fatigue)
- F1 > 0.60 (balanced performance)

**Resume Value:** ⭐⭐⭐⭐⭐ (Classification + imbalanced data handling)

---

### Target Priority Ranking

| Priority | Target | Reason | Implement First? |
|---|---|---|---|
| 1 | Demand (MW) | Standard benchmark, easiest to validate | ✅ YES |
| 2 | High-Stress Events | Most actionable, addresses imbalance | ✅ YES |
| 3 | Stress Index | Derived from demand, less critical | ⚠️ OPTIONAL |

**Recommendation:** Start with Demand + High-Stress Event classification. Add Stress Index forecasting only if time permits.

---

## 2. Baseline Models (Crawl Phase)

### Purpose of Baselines
- Establish performance floor
- Validate data quality and feature engineering
- Provide comparison for ML models
- Quick implementation (1-2 days total)

---

### Baseline 1: Naive Forecast
**Method:** Use previous day's value at same hour (24-hour lag)

**Implementation:**
```python
forecast_t = actual_{t-24}
```

**Pros:**
- Zero training time
- Captures daily seasonality
- Hard to beat for stable time series

**Cons:**
- No trend adaptation
- No weekly/monthly patterns
- No external features

**Expected Performance:**
- Demand MAPE: 15-25%
- Event Recall: 40-60%

**Time to Implement:** 1 hour

**Resume Value:** ⭐ (Baseline only, but shows rigor)

---

### Baseline 2: Moving Average (7-day window)
**Method:** Average of same hour over past 7 days

**Implementation:**
```python
forecast_t = mean(actual_{t-24}, actual_{t-48}, ..., actual_{t-168})
```

**Pros:**
- Smooths noise
- Captures weekly patterns
- Simple to explain

**Cons:**
- Lags trend changes
- Equal weight to all days
- No feature engineering

**Expected Performance:**
- Demand MAPE: 12-20%
- Event Recall: 50-70%

**Time to Implement:** 2 hours

**Resume Value:** ⭐ (Baseline only)

---

### Baseline 3: Prophet (Facebook's Time Series Tool)
**Method:** Additive model with trend + seasonality + holidays

**Why Prophet:**
- Handles multiple seasonality (daily, weekly, yearly)
- Robust to missing data
- Interpretable components
- Industry standard for time series
- Fast training (<5 minutes per authority)

**Implementation:**
```python
from prophet import Prophet

model = Prophet(
    daily_seasonality=True,
    weekly_seasonality=True,
    yearly_seasonality=True,
    changepoint_prior_scale=0.05
)
model.fit(train_df)
forecast = model.predict(future_df)
```

**Hyperparameters to Tune:**
- `changepoint_prior_scale`: Trend flexibility (0.001 - 0.5)
- `seasonality_prior_scale`: Seasonality strength (0.01 - 10)
- `seasonality_mode`: 'additive' vs 'multiplicative'

**Expected Performance:**
- Demand MAPE: 8-15%
- Event Recall: 60-75%

**Time to Implement:** 1 day (including tuning)

**Resume Value:** ⭐⭐⭐ (Industry standard, shows time series expertise)

---

### Baseline 4: SARIMAX (Seasonal ARIMA with Exogenous Variables)
**Method:** Statistical time series model with seasonal components

**Why SARIMAX:**
- Classical statistical approach
- Captures autocorrelation + seasonality
- Can include exogenous features (temperature, day-of-week)
- Provides confidence intervals
- Benchmark for academic comparisons

**Implementation:**
```python
from statsmodels.tsa.statespace.sarimax import SARIMAX

model = SARIMAX(
    train_data,
    order=(1, 1, 1),           # (p, d, q) - ARIMA order
    seasonal_order=(1, 1, 1, 24),  # (P, D, Q, s) - seasonal order
    exog=exog_features
)
results = model.fit()
forecast = results.forecast(steps=24, exog=future_exog)
```

**Hyperparameters to Tune:**
- `order (p, d, q)`: AR, differencing, MA terms
- `seasonal_order (P, D, Q, s)`: Seasonal components
- Exogenous variables selection

**Expected Performance:**
- Demand MAPE: 10-18%
- Event Recall: 55-70%

**Time to Implement:** 1-2 days (slow training, complex tuning)

**Resume Value:** ⭐⭐⭐ (Shows statistical rigor)

**⚠️ Warning:** SARIMAX is computationally expensive. Consider skipping if Prophet performs well.

---

### Baseline Summary Table

| Model | MAPE (Expected) | Training Time | Tuning Complexity | Implement? |
|---|---|---|---|---|
| Naive (24h lag) | 15-25% | Instant | None | ✅ YES |
| Moving Average | 12-20% | Instant | Low | ✅ YES |
| Prophet | 8-15% | 5 min | Medium | ✅ YES |
| SARIMAX | 10-18% | 30+ min | High | ⚠️ OPTIONAL |

**Recommendation:** Implement Naive + Moving Average + Prophet. Skip SARIMAX unless Prophet underperforms.

---

## 3. ML Models (Walk Phase)

### Purpose of ML Models
- Leverage engineered features (hour, day-of-week, lag features)
- Capture non-linear relationships
- Handle multiple authorities jointly
- Provide feature importance insights

---

### ML Model 1: LightGBM (Gradient Boosting)
**Method:** Gradient boosted decision trees optimized for speed

**Why LightGBM:**
- Fast training (10-100x faster than XGBoost)
- Handles categorical features natively
- Built-in feature importance
- Excellent for tabular data
- Industry standard for Kaggle competitions

**Implementation:**
```python
import lightgbm as lgb

params = {
    'objective': 'regression',
    'metric': 'mae',
    'boosting_type': 'gbdt',
    'num_leaves': 31,
    'learning_rate': 0.05,
    'feature_fraction': 0.8,
    'bagging_fraction': 0.8,
    'bagging_freq': 5,
    'verbose': -1
}

train_data = lgb.Dataset(X_train, label=y_train)
model = lgb.train(params, train_data, num_boost_round=1000)
forecast = model.predict(X_test)
```

**Key Features to Engineer:**
- Lag features: demand_{t-1}, demand_{t-24}, demand_{t-168}
- Rolling statistics: 7-day mean, 7-day std
- Time features: hour, day_of_week, month, is_weekend
- Calendar features: is_holiday, day_of_year
- Authority features: authority_id (categorical)

**Hyperparameters to Tune:**
- `num_leaves`: Tree complexity (20-100)
- `learning_rate`: Step size (0.01-0.1)
- `feature_fraction`: Feature sampling (0.6-1.0)
- `num_boost_round`: Number of trees (100-2000)

**Expected Performance:**
- Demand MAPE: 6-12%
- Event F1: 0.55-0.70

**Time to Implement:** 2-3 days (including feature engineering)

**Resume Value:** ⭐⭐⭐⭐⭐ (Industry standard, shows ML engineering)

---

### ML Model 2: XGBoost (Extreme Gradient Boosting)
**Method:** Optimized gradient boosting with regularization

**Why XGBoost:**
- Slightly better accuracy than LightGBM (marginal)
- More mature library
- Better handling of missing values
- Provides SHAP values for explainability
- Academic benchmark standard

**Implementation:**
```python
import xgboost as xgb

params = {
    'objective': 'reg:squarederror',
    'eval_metric': 'mae',
    'max_depth': 6,
    'learning_rate': 0.05,
    'subsample': 0.8,
    'colsample_bytree': 0.8,
    'min_child_weight': 1,
    'gamma': 0
}

dtrain = xgb.DMatrix(X_train, label=y_train)
model = xgb.train(params, dtrain, num_boost_round=1000)
forecast = model.predict(xgb.DMatrix(X_test))
```

**Hyperparameters to Tune:**
- `max_depth`: Tree depth (3-10)
- `learning_rate`: Step size (0.01-0.1)
- `subsample`: Row sampling (0.6-1.0)
- `colsample_bytree`: Column sampling (0.6-1.0)

**Expected Performance:**
- Demand MAPE: 6-12% (similar to LightGBM)
- Event F1: 0.55-0.70

**Time to Implement:** 2-3 days

**Resume Value:** ⭐⭐⭐⭐⭐ (Industry standard)

**⚠️ Note:** XGBoost and LightGBM typically perform within 1-2% of each other. Choose one based on speed vs accuracy tradeoff.

---

### ML Model Summary Table

| Model | MAPE (Expected) | Training Time | Feature Engineering | Implement? |
|---|---|---|---|---|
| LightGBM | 6-12% | Fast (1-5 min) | Required | ✅ YES |
| XGBoost | 6-12% | Medium (5-15 min) | Required | ⚠️ OPTIONAL |

**Recommendation:** Implement LightGBM first. Add XGBoost only if you want ensemble or comparison.

---

## 4. Evaluation Metrics

### Regression Metrics (Demand & Stress Index Forecasting)

#### MAE (Mean Absolute Error)
**Formula:** `MAE = mean(|actual - forecast|)`

**Interpretation:**
- Average error in original units (MW or stress points)
- Easy to explain to stakeholders
- Not sensitive to outliers

**Target:**
- Demand: MAE < 1,500 MW (excellent), < 2,500 MW (good)
- Stress Index: MAE < 5 points (excellent), < 10 points (good)

**Resume Value:** ⭐⭐⭐⭐ (Standard metric)

---

#### RMSE (Root Mean Squared Error)
**Formula:** `RMSE = sqrt(mean((actual - forecast)^2))`

**Interpretation:**
- Penalizes large errors more than MAE
- Same units as target variable
- Sensitive to outliers

**Target:**
- Demand: RMSE < 2,000 MW (excellent), < 3,000 MW (good)
- Stress Index: RMSE < 8 points (excellent), < 12 points (good)

**Resume Value:** ⭐⭐⭐⭐ (Standard metric)

---

#### MAPE (Mean Absolute Percentage Error)
**Formula:** `MAPE = mean(|actual - forecast| / actual) * 100`

**Interpretation:**
- Scale-independent (compare across authorities)
- Easy to communicate (percentage)
- Undefined when actual = 0

**Target:**
- MAPE < 10% (excellent)
- MAPE 10-15% (good)
- MAPE 15-20% (acceptable)
- MAPE > 20% (needs improvement)

**Resume Value:** ⭐⭐⭐⭐⭐ (Most cited metric in industry)

**⚠️ Warning:** MAPE can be misleading for low-demand periods. Use weighted MAPE or exclude low-demand hours.

---

### Classification Metrics (High-Stress Event Prediction)

#### Precision
**Formula:** `Precision = TP / (TP + FP)`

**Interpretation:**
- Of all predicted high-stress events, what % were correct?
- High precision = low false alarm rate
- Important for avoiding alert fatigue

**Target:**
- Precision > 60% (excellent)
- Precision 40-60% (good)
- Precision < 40% (too many false alarms)

**Resume Value:** ⭐⭐⭐⭐⭐ (Shows understanding of business tradeoffs)

---

#### Recall (Sensitivity)
**Formula:** `Recall = TP / (TP + FN)`

**Interpretation:**
- Of all actual high-stress events, what % did we catch?
- High recall = few missed events
- Critical for grid reliability

**Target:**
- Recall > 85% (excellent - catch most events)
- Recall 70-85% (good)
- Recall < 70% (missing too many events)

**Resume Value:** ⭐⭐⭐⭐⭐ (Shows understanding of business tradeoffs)

---

#### F1 Score
**Formula:** `F1 = 2 * (Precision * Recall) / (Precision + Recall)`

**Interpretation:**
- Harmonic mean of precision and recall
- Balances false positives and false negatives
- Good for imbalanced datasets

**Target:**
- F1 > 0.70 (excellent)
- F1 0.55-0.70 (good)
- F1 < 0.55 (needs improvement)

**Resume Value:** ⭐⭐⭐⭐⭐ (Standard for imbalanced classification)

---

### Metric Priority by Target

| Target | Primary Metric | Secondary Metrics | Why |
|---|---|---|---|
| Demand (MW) | MAPE | MAE, RMSE | Scale-independent, easy to communicate |
| Stress Index | MAE | RMSE, MAPE | Interpretable in stress points |
| High-Stress Events | F1 | Precision, Recall | Balances false positives/negatives |

---

### Evaluation Strategy

**Time-Based Split (No Random Shuffling):**
```
Training:   Jan 1 - Mar 31 (80% of data)
Validation: Apr 1 - Apr 15 (10% of data)
Test:       Apr 16 - Apr 30 (10% of data)
```

**Walk-Forward Validation:**
- Train on months 1-3, test on month 4
- Retrain on months 1-4, test on month 5
- Simulates production deployment

**Cross-Authority Validation:**
- Train on 4 authorities, test on 5th
- Evaluates model generalization

**Evaluation Frequency:**
- Overall metrics (full test set)
- By authority (identify weak performers)
- By hour-of-day (identify temporal patterns)
- By stress level (high vs low stress performance)

---

## 5. Data Requirements

### Minimum Data Requirements

| Requirement | Current Status | Needed? |
|---|---|---|
| **Historical Depth** | 4 months (Jan-Apr 2026) | ⚠️ Marginal |
| **Hourly Granularity** | ✅ Yes | ✅ Sufficient |
| **Multiple Authorities** | ✅ 5 authorities | ✅ Sufficient |
| **Complete Records** | ✅ 13,020 hours | ✅ Sufficient |
| **Missing Data Handling** | ⚠️ Unknown | 🔍 Needs Check |

**Recommendation:** 4 months is minimal for time series. Ideally 1-2 years for robust seasonality modeling.

---

### Required Features (Already Available)

| Feature | Source | Purpose |
|---|---|---|
| `demand_mw` | EIA API | Primary forecast target |
| `demand_forecast_mw` | EIA API | Baseline comparison |
| `net_generation_mw` | EIA API | Supply-side feature |
| `total_interchange_mw` | EIA API | Import/export feature |
| `period_utc` | EIA API | Timestamp for time features |
| `balancing_authority` | EIA API | Authority identifier |

---

### Features to Engineer

#### Temporal Features (High Priority)
```python
df['hour'] = df['period_utc'].dt.hour
df['day_of_week'] = df['period_utc'].dt.dayofweek
df['month'] = df['period_utc'].dt.month
df['day_of_year'] = df['period_utc'].dt.dayofyear
df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
df['is_business_hour'] = df['hour'].between(8, 18).astype(int)
```

**Resume Value:** ⭐⭐⭐⭐ (Shows feature engineering skills)

---

#### Lag Features (High Priority)
```python
# Previous hour, previous day, previous week
df['demand_lag_1h'] = df.groupby('authority')['demand_mw'].shift(1)
df['demand_lag_24h'] = df.groupby('authority')['demand_mw'].shift(24)
df['demand_lag_168h'] = df.groupby('authority')['demand_mw'].shift(168)
```

**⚠️ Warning:** Ensure no data leakage. Lag features must use only past data.

**Resume Value:** ⭐⭐⭐⭐⭐ (Critical for time series ML)

---

#### Rolling Statistics (Medium Priority)
```python
# 7-day rolling mean and std
df['demand_rolling_mean_7d'] = df.groupby('authority')['demand_mw'].transform(
    lambda x: x.rolling(window=168, min_periods=1).mean()
)
df['demand_rolling_std_7d'] = df.groupby('authority')['demand_mw'].transform(
    lambda x: x.rolling(window=168, min_periods=1).std()
)
```

**Resume Value:** ⭐⭐⭐⭐ (Shows advanced feature engineering)

---

#### Interaction Features (Low Priority)
```python
# Generation-demand gap
df['gen_demand_gap'] = df['net_generation_mw'] - df['demand_mw']

# Interchange as % of demand
df['interchange_pct'] = df['total_interchange_mw'] / df['demand_mw']
```

**Resume Value:** ⭐⭐⭐ (Shows domain knowledge)

---

### External Data (Future Enhancement)

| Data Source | Feature | Value | Effort |
|---|---|---|---|
| Weather API | Temperature | High (demand correlation) | Medium |
| Calendar API | Holidays | Medium (demand spikes) | Low |
| CAISO Market | Electricity prices | Medium (supply signal) | High |
| Renewable Gen | Solar/wind output | High (supply variability) | Medium |

**Recommendation:** Start without external data. Add weather if baseline models underperform.

---

## 6. Feature Engineering Opportunities

### High-Impact Features (Implement First)

1. **Lag Features (24h, 168h)**
   - Captures daily and weekly patterns
   - Essential for time series ML
   - **Expected Impact:** 20-30% MAPE improvement over no lags

2. **Hour-of-Day Encoding**
   - Captures intraday demand curve
   - Use cyclical encoding: `sin(2π * hour/24)`, `cos(2π * hour/24)`
   - **Expected Impact:** 10-15% MAPE improvement

3. **Day-of-Week Encoding**
   - Captures weekday vs weekend patterns
   - Use cyclical encoding or one-hot
   - **Expected Impact:** 5-10% MAPE improvement

4. **Rolling Statistics (7-day window)**
   - Smooths noise, captures trends
   - Mean, std, min, max
   - **Expected Impact:** 5-10% MAPE improvement

---

### Medium-Impact Features (Implement Second)

5. **Forecast Error Features**
   - `forecast_error_lag_24h = demand_forecast_mw - demand_mw` (lagged)
   - Captures systematic forecast bias
   - **Expected Impact:** 3-5% MAPE improvement

6. **Generation-Demand Gap**
   - `gen_demand_gap = net_generation_mw - demand_mw`
   - Indicates import/export pressure
   - **Expected Impact:** 2-5% MAPE improvement

7. **Authority Embeddings**
   - One-hot encoding or learned embeddings
   - Captures authority-specific patterns
   - **Expected Impact:** 5-10% MAPE improvement

---

### Low-Impact Features (Implement If Time)

8. **Interaction Terms**
   - `hour * day_of_week`
   - `demand_lag_24h * is_weekend`
   - **Expected Impact:** 1-3% MAPE improvement

9. **Trend Features**
   - Linear trend: `days_since_start`
   - Polynomial trend: `days_since_start^2`
   - **Expected Impact:** 1-2% MAPE improvement

---

### Feature Engineering Checklist

**Before Training:**
- [ ] Check for missing values (impute or drop)
- [ ] Verify no data leakage (lag features use only past data)
- [ ] Normalize/scale features (for neural networks, not tree models)
- [ ] Encode categorical variables (authority, hour, day_of_week)
- [ ] Create train/val/test splits (temporal, no shuffling)

**After Training:**
- [ ] Analyze feature importance (LightGBM/XGBoost built-in)
- [ ] Remove low-importance features (reduce overfitting)
- [ ] Check for multicollinearity (VIF > 10)
- [ ] Validate feature distributions (train vs test)

---

## 7. Risks and Limitations

### Data Risks

**Risk 1: Limited Historical Data (4 months)**
- **Impact:** May not capture full seasonal patterns (summer peaks, winter troughs)
- **Mitigation:** Focus on short-term patterns (daily, weekly), document limitation
- **Likelihood:** High
- **Severity:** Medium

**Risk 2: Missing Data / API Failures**
- **Impact:** Gaps in training data, model degradation
- **Mitigation:** Implement robust imputation, fallback to CSV
- **Likelihood:** Medium
- **Severity:** Medium

**Risk 3: Data Quality Issues**
- **Impact:** Noisy forecasts, unreliable metrics
- **Mitigation:** Extensive validation checks (already implemented)
- **Likelihood:** Low
- **Severity:** High

---

### Modeling Risks

**Risk 4: Overfitting (Especially with Limited Data)**
- **Impact:** Great training performance, poor test performance
- **Mitigation:** Cross-validation, regularization, feature selection
- **Likelihood:** High
- **Severity:** High

**Risk 5: Class Imbalance (High-Stress Events = 0.6%)**
- **Impact:** Model predicts "no stress" for all hours, high accuracy but useless
- **Mitigation:** Use F1/Recall metrics, class weights, SMOTE, threshold tuning
- **Likelihood:** High
- **Severity:** High

**Risk 6: Concept Drift**
- **Impact:** Model performance degrades over time (grid changes, new generation)
- **Mitigation:** Automated retraining, drift detection, monitoring
- **Likelihood:** Medium
- **Severity:** Medium

---

### Technical Risks

**Risk 7: Computational Resources**
- **Impact:** Slow training, can't iterate quickly
- **Mitigation:** Use LightGBM (fast), cloud compute if needed
- **Likelihood:** Low
- **Severity:** Low

**Risk 8: Model Complexity vs Explainability**
- **Impact:** Stakeholders don't trust "black box" models
- **Mitigation:** Start with interpretable models (Prophet), add SHAP values
- **Likelihood:** Medium
- **Severity:** Medium

---

### Career/Resume Risks

**Risk 9: Over-Engineering (GNN Too Early)**
- **Impact:** Spend weeks on GNN, no baseline comparison, can't justify approach
- **Mitigation:** Follow crawl-walk-run plan, establish baselines first
- **Likelihood:** High
- **Severity:** High

**Risk 10: Under-Delivery (Start Too Many Models, Finish None)**
- **Impact:** No working models, nothing to show in interviews
- **Mitigation:** Time-box each model (2-3 days max), prioritize completion
- **Likelihood:** Medium
- **Severity:** High

**Risk 11: Poor Storytelling (Great Models, Weak Narrative)**
- **Impact:** Can't articulate value in interviews, resume bullets fall flat
- **Mitigation:** Document everything, practice explaining, quantify results
- **Likelihood:** Medium
- **Severity:** High

---

### Risk Mitigation Priority

| Risk | Mitigation Strategy | Priority |
|---|---|---|
| Overfitting | Cross-validation, regularization | 🔴 Critical |
| Class Imbalance | F1 metric, class weights, threshold tuning | 🔴 Critical |
| Limited Data | Document limitation, focus on short-term patterns | 🟡 High |
| Over-Engineering | Follow crawl-walk-run plan | 🟡 High |
| Concept Drift | Monitoring, retraining (future work) | 🟢 Medium |

---

## 8. Recommended Model Progression

### Phase 1: Baseline Establishment (Days 1-3)

**Goal:** Establish performance floor, validate data pipeline

**Models to Implement:**
1. Naive forecast (24h lag) - 1 hour
2. Moving average (7-day) - 2 hours
3. Prophet (with tuning) - 1 day

**Deliverables:**
- Baseline MAPE for each authority
- Forecast vs actual visualizations
- Model comparison table
- Documentation of approach

**Success Criteria:**
- Prophet MAPE < 15%
- All models trained and evaluated
- Results documented

**Resume Bullet (Draft):**
"Established time series forecasting baselines using Prophet, achieving 12% MAPE on 24h demand prediction across 5 California balancing authorities"

---

### Phase 2: ML Model Development (Days 4-7)

**Goal:** Improve accuracy with feature engineering and gradient boosting

**Models to Implement:**
1. Feature engineering pipeline - 1 day
2. LightGBM (regression + classification) - 2 days
3. Hyperparameter tuning - 1 day

**Deliverables:**
- Engineered feature set (20+ features)
- LightGBM models for demand + event classification
- Feature importance analysis
- Model comparison vs baselines

**Success Criteria:**
- LightGBM MAPE < 10% (20% improvement over Prophet)
- Event classification F1 > 0.60
- Feature importance documented

**Resume Bullet (Draft):**
"Developed LightGBM forecasting model with 30+ engineered features, achieving 8% MAPE and 15% improvement over Prophet baseline"

---

### Phase 3: Spatial Dependency Analysis (Days 8-10)

**Goal:** Determine if spatial dependencies justify GNN complexity

**Analysis to Perform:**
1. **Correlation Analysis**
   - Calculate cross-authority demand correlations
   - Identify lead-lag relationships
   - Visualize correlation matrix

2. **Granger Causality Tests**
   - Test if authority A's demand predicts authority B's demand
   - Quantify predictive power of spatial features

3. **Spatial Feature Engineering**
   - Add neighbor authority lag features
   - Add interchange flow features
   - Test if spatial features improve LightGBM

**Deliverables:**
- Correlation heatmap (5x5 authorities)
- Granger causality test results
- LightGBM with spatial features
- Decision matrix: GNN vs no-GNN

**Success Criteria:**
- Spatial features improve MAPE by >5% → GNN justified
- Spatial features improve MAPE by <5% → GNN not justified

**Resume Bullet (Draft):**
"Conducted spatial dependency analysis across interconnected grid authorities, identifying 15% correlation in demand patterns and justifying graph neural network approach"

---

### Phase 4: GNN Implementation (Days 11-14) - CONDITIONAL

**Proceed ONLY if Phase 3 shows spatial dependencies improve accuracy by >5%**

**Models to Implement:**
1. Graph construction (NetworkX) - 1 day
2. Simple GCN (PyTorch Geometric) - 2 days
3. GNN vs LightGBM comparison - 1 day

**Deliverables:**
- Authority network graph (5 nodes, weighted edges)
- GCN model for demand forecasting
- Ablation study: GNN vs non-spatial baseline
- Final model comparison table

**Success Criteria:**
- GNN MAPE < LightGBM MAPE (any improvement)
- Spatial message passing demonstrably helps
- Clear narrative for why GNN was needed

**Resume Bullet (Draft):**
"Applied Graph Convolutional Networks to model spatial-temporal dependencies across California's interconnected grid, achieving 7% MAPE and 12% improvement over non-spatial baseline"

---

### Decision Tree: Should You Implement GNN?

```
START
  ↓
Have you implemented baselines (Prophet)? 
  NO → Go to Phase 1
  YES ↓
Have you implemented LightGBM with features?
  NO → Go to Phase 2
  YES ↓
Have you tested spatial features in LightGBM?
  NO → Go to Phase 3
  YES ↓
Do spatial features improve MAPE by >5%?
  NO → STOP. GNN not justified. Document why.
  YES ↓
Do you have 3+ days for GNN implementation?
  NO → STOP. Prioritize other features.
  YES ↓
PROCEED to Phase 4: Implement GNN
```

---

### Time Budget Allocation

| Phase | Days | Cumulative | Priority |
|---|---|---|---|
| Phase 1: Baselines | 3 | 3 | 🔴 Critical |
| Phase 2: LightGBM | 4 | 7 | 🔴 Critical |
| Phase 3: Spatial Analysis | 3 | 10 | 🟡 High |
| Phase 4: GNN (conditional) | 4 | 14 | 🟢 Medium |

**Total Time:** 10-14 days depending on GNN decision

---

## 9. GNN Readiness Criteria

### Prerequisites (Must Complete Before GNN)

- ✅ **Baseline models trained** (Naive, Prophet)
- ✅ **LightGBM model trained** with engineered features
- ✅ **Spatial dependency analysis** completed
- ✅ **Spatial features tested** in LightGBM
- ✅ **Performance gap identified** (>5% improvement potential)

### Technical Readiness

- ✅ **Graph structure defined** (5 authorities, interchange edges)
- ✅ **PyTorch Geometric installed** and tested
- ✅ **Node features prepared** (demand, generation, time features)
- ✅ **Edge weights calculated** (interchange flows, normalized)
- ✅ **Train/test split** preserves temporal order

### Justification Criteria (Answer YES to Proceed)

**Question 1:** Do spatial features improve LightGBM MAPE by >5%?
- YES → Spatial dependencies exist, GNN may help
- NO → GNN not justified, stick with LightGBM

**Question 2:** Can you articulate WHY spatial dependencies matter?
- Example: "CISO demand spikes propagate to LDWP via interchange flows with 2-hour lag"
- YES → Clear narrative for interviews
- NO → Need more analysis before GNN

**Question 3:** Do you have 3-4 days for GNN implementation?
- YES → Proceed
- NO → Prioritize other features (monitoring, documentation)

**Question 4:** Will GNN differentiate you from other candidates?
- YES → Unique selling point, worth the effort
- NO → Focus on other differentiators

---

### GNN Implementation Checklist

**Before Starting:**
- [ ] Baseline MAPE documented (Prophet, LightGBM)
- [ ] Spatial dependency analysis completed
- [ ] Graph structure designed (nodes, edges, features)
- [ ] PyTorch Geometric environment tested
- [ ] 3-4 days allocated in schedule

**During Implementation:**
- [ ] Graph construction (NetworkX → PyG)
- [ ] Simple GCN architecture (2 layers, 64 hidden units)
- [ ] Training loop with validation
- [ ] Hyperparameter tuning (learning rate, dropout)
- [ ] Ablation study (with vs without spatial edges)

**After Implementation:**
- [ ] GNN MAPE vs LightGBM MAPE comparison
- [ ] Visualization of learned attention/message passing
- [ ] Documentation of spatial modeling approach
- [ ] Resume bullet with quantified improvement

---

### Red Flags: When NOT to Implement GNN

🚩 **Red Flag 1:** Spatial features don't improve LightGBM
- **Action:** Stop. Document why GNN wasn't needed. Focus on other features.

🚩 **Red Flag 2:** Only 5 nodes in graph (too small)
- **Action:** Acknowledge limitation. Frame as "proof of concept for larger grids."

🚩 **Red Flag 3:** GNN training takes >1 day
- **Action:** Simplify architecture. Use smaller hidden dimensions.

🚩 **Red Flag 4:** GNN performs worse than LightGBM
- **Action:** Debug (data leakage? wrong architecture?). If still worse, document and move on.

🚩 **Red Flag 5:** Can't explain why GNN helps
- **Action:** Do more analysis. Visualize message passing. Understand spatial patterns.

---

### Green Lights: When GNN is Justified

✅ **Green Light 1:** Spatial features improve LightGBM by >5%
- **Interpretation:** Spatial dependencies exist and are predictive

✅ **Green Light 2:** Granger causality tests show cross-authority predictive power
- **Interpretation:** Authority A's demand helps predict authority B's demand

✅ **Green Light 3:** Interchange flows correlate with demand changes
- **Interpretation:** Grid network structure matters for forecasting

✅ **Green Light 4:** GNN improves MAPE by any amount over LightGBM
- **Interpretation:** Spatial modeling adds value

✅ **Green Light 5:** You can clearly explain the spatial mechanism
- **Example:** "CISO stress propagates to LDWP via interchange, GNN captures this"

---

## 10. Expected Resume and Interview Value

### Resume Bullets by Model

#### Baseline Models (Prophet)
**Resume Bullet:**
"Established time series forecasting baselines using Prophet, achieving 12% MAPE on 24-hour demand prediction across 5 California balancing authorities"

**Interview Value:** ⭐⭐⭐
- Shows time series expertise
- Industry-standard tool
- Quantified results

**Talking Points:**
- Why Prophet? (handles seasonality, interpretable)
- How validated? (walk-forward, per-authority)
- What learned? (daily/weekly patterns, forecast bias)

---

#### ML Models (LightGBM)
**Resume Bullet:**
"Developed gradient boosting forecasting model with 30+ engineered features (lag, rolling, temporal), achieving 8% MAPE and 33% improvement over Prophet baseline"

**Interview Value:** ⭐⭐⭐⭐⭐
- Shows ML engineering skills
- Feature engineering expertise
- Quantified improvement over baseline

**Talking Points:**
- Feature engineering process (lag, rolling, temporal)
- Hyperparameter tuning approach
- Feature importance insights
- Why LightGBM over XGBoost? (speed, performance)

---

#### Classification (High-Stress Events)
**Resume Bullet:**
"Built imbalanced classification model for high-stress event prediction (0.6% positive class), achieving 85% recall and 55% precision using class weights and threshold tuning"

**Interview Value:** ⭐⭐⭐⭐⭐
- Shows understanding of imbalanced data
- Business-focused (precision/recall tradeoff)
- Demonstrates cost-benefit thinking

**Talking Points:**
- How handled imbalance? (class weights, SMOTE, threshold tuning)
- Precision vs recall tradeoff (false alarms vs missed events)
- Business impact (cost of false positive vs false negative)

---

#### GNN (If Implemented)
**Resume Bullet:**
"Applied Graph Convolutional Networks to model spatial-temporal dependencies across California's interconnected grid authorities, achieving 7% MAPE and 12% improvement over non-spatial LightGBM baseline"

**Interview Value:** ⭐⭐⭐⭐⭐⭐ (Highest)
- Unique differentiator (95% of candidates don't have GNN experience)
- Shows research → production translation
- Demonstrates spatial modeling expertise

**Talking Points:**
- Why GNN? (spatial dependencies between authorities)
- Graph structure (nodes = authorities, edges = interchange)
- Ablation study (with vs without spatial edges)
- Challenges (small graph, limited data)
- Future work (temporal GNN, larger grids)

---

### Interview Question Bank

**Q1: Why did you choose Prophet over ARIMA?**
**A:** "Prophet handles multiple seasonality (daily, weekly, yearly) out-of-the-box and is robust to missing data. ARIMA requires manual seasonal order tuning and is slower to train. For a 4-month dataset with hourly data, Prophet gave better performance with less tuning effort."

**Q2: How did you handle the class imbalance (0.6% high-stress events)?**
**A:** "Three approaches: (1) Used F1 score instead of accuracy as primary metric, (2) Applied class weights in LightGBM to penalize false negatives more, (3) Tuned classification threshold to achieve desired recall (85%) while maintaining acceptable precision (55%). Also considered SMOTE but found class weights sufficient."

**Q3: What features were most important for forecasting?**
**A:** "Top 3: (1) 24-hour lag demand (captures daily seasonality), (2) Hour-of-day (captures intraday demand curve), (3) 7-day rolling mean (captures weekly trends). Feature importance from LightGBM showed these accounted for 60% of predictive power."

**Q4: How did you validate your models?**
**A:** "Time-based split (no random shuffling) - trained on Jan-Mar, validated on Apr 1-15, tested on Apr 16-30. Also used walk-forward validation to simulate production deployment. Evaluated overall metrics plus per-authority and per-hour-of-day breakdowns to identify weak spots."

**Q5: Why did you implement GNN? (If applicable)**
**A:** "Spatial dependency analysis showed that CISO demand changes predicted LDWP demand changes with 2-hour lag (Granger causality p<0.01). Adding spatial features to LightGBM improved MAPE by 7%, justifying the GNN approach. GNN captures these spatial dependencies through message passing across the grid network."

**Q6: What would you do differently with more time/data?**
**A:** "Three priorities: (1) Add weather data (temperature strongly correlates with demand), (2) Extend to 1-2 years of data for robust seasonality modeling, (3) Implement temporal GNN (STGCN) for joint spatial-temporal modeling. Also would add automated retraining and drift detection for production deployment."

---

### Portfolio Value Summary

| Component | Resume Value | Interview Value | Differentiation | Implement? |
|---|---|---|---|---|
| Prophet Baseline | ⭐⭐⭐ | ⭐⭐⭐ | Low | ✅ YES |
| LightGBM + Features | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Medium | ✅ YES |
| Event Classification | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Medium | ✅ YES |
| Spatial Analysis | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | Medium | ✅ YES |
| GNN (if justified) | ⭐⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐⭐ | Very High | ⚠️ CONDITIONAL |

---

## Implementation Roadmap Summary

### Week 1: Baselines + ML Models (Days 1-7)

**Day 1-2: Baseline Models**
- Implement Naive, Moving Average, Prophet
- Calculate MAPE for each authority
- Create forecast vs actual visualizations
- **Deliverable:** Baseline performance table

**Day 3-5: Feature Engineering + LightGBM**
- Engineer 20+ features (lag, rolling, temporal)
- Train LightGBM for demand forecasting
- Train LightGBM for event classification
- **Deliverable:** ML models with feature importance

**Day 6-7: Evaluation + Documentation**
- Calculate all metrics (MAPE, MAE, RMSE, F1)
- Create model comparison table
- Document methodology
- **Deliverable:** Model documentation

---

### Week 2: Spatial Analysis + GNN (Days 8-14)

**Day 8-10: Spatial Dependency Analysis**
- Calculate cross-authority correlations
- Run Granger causality tests
- Test spatial features in LightGBM
- **Deliverable:** Spatial analysis report + GNN decision

**Day 11-14: GNN Implementation (If Justified)**
- Build graph structure (NetworkX → PyG)
- Implement GCN architecture
- Train and evaluate GNN
- Compare to LightGBM baseline
- **Deliverable:** GNN model + ablation study

---

### Success Criteria

**Minimum Viable Product (MVP):**
- ✅ Prophet baseline (MAPE < 15%)
- ✅ LightGBM model (MAPE < 10%)
- ✅ Event classification (F1 > 0.60)
- ✅ Model comparison table
- ✅ Documentation for interviews

**Stretch Goals:**
- ✅ Spatial dependency analysis
- ✅ GNN implementation (if justified)
- ✅ Automated retraining pipeline
- ✅ Model monitoring dashboard

---

## Conclusion

This forecasting strategy provides a systematic, evidence-based approach to model development. The key insight: **GNNs are justified ONLY if spatial dependencies demonstrably improve forecast accuracy.**

**Follow the crawl-walk-run progression:**
1. **Crawl:** Establish baselines (Prophet) - 3 days
2. **Walk:** Implement ML models (LightGBM) - 4 days
3. **Run:** Evaluate GNN necessity - 3-7 days

**Decision Point:** After Phase 3 (spatial analysis), you'll have clear evidence whether GNN is worth the effort. If spatial features improve LightGBM by >5%, proceed to GNN. If not, document why GNN wasn't needed and focus on other differentiators (monitoring, documentation, business impact).

**Resume Impact:**
- Without GNN: Strong ML engineering project (⭐⭐⭐⭐)
- With GNN (justified): Unique research-to-production project (⭐⭐⭐⭐⭐⭐)

**Remember:** A well-executed baseline + LightGBM project with clear documentation is better than a half-finished GNN project with no results.

---

**Next Steps:**
1. Review this strategy document
2. Set up development environment (Prophet, LightGBM, PyTorch Geometric)
3. Start Phase 1: Baseline models (Day 1)
4. Document everything for interviews
5. Make data-driven decision on GNN at Phase 3 checkpoint

**Questions to Answer Before Starting:**
- [ ] Do I have 10-14 days for this work?
- [ ] Is my goal to maximize resume impact or learn GNNs?
- [ ] Am I comfortable stopping at LightGBM if GNN isn't justified?
- [ ] Do I have compute resources for model training?
- [ ] Have I allocated time for documentation and storytelling?

Good luck! 🚀
