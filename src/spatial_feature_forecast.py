"""
Spatial Feature Forecasting Benchmark

Validates whether spatial information improves forecasting performance
before implementing a Graph Neural Network (GNN).

Approach:
1. Load baseline LightGBM results
2. Load spatial dependency analysis (correlations, Granger causality)
3. Engineer graph-inspired spatial features
4. Train LightGBM with spatial features
5. Compare performance: Naive → LightGBM → LightGBM+Spatial
6. Recommend whether GNN is justified

Spatial Features:
- Lag-1h and lag-24h demand from other authorities
- Correlation-weighted neighbor demand
- Average demand of connected authorities
- Strongest correlated authority demand
- Granger-causal authority demand
- Rolling neighbor demand averages

Outputs:
- outputs/spatial_feature_results.csv
- outputs/spatial_feature_importance.csv
- outputs/spatial_feature_comparison.csv
- outputs/spatial_feature_report.md
"""

import pandas as pd
import numpy as np
from pathlib import Path
import lightgbm as lgb
import warnings
warnings.filterwarnings('ignore')


def detect_column_names(df):
    """Detect the correct column names for timestamp, authority, and demand."""
    columns = df.columns.tolist()
    
    # Detect timestamp column
    timestamp_col = None
    for col in ['timestamp_utc', 'period_utc', 'local_time_pacific']:
        if col in columns:
            timestamp_col = col
            break
    
    if timestamp_col is None:
        raise ValueError(f"No timestamp column found. Expected one of: timestamp_utc, period_utc, local_time_pacific. Found: {columns}")
    
    # Detect authority column
    authority_col = 'balancing_authority'
    if authority_col not in columns:
        raise ValueError(f"Column '{authority_col}' not found in data. Found: {columns}")
    
    # Detect demand column
    demand_col = 'demand_mw'
    if demand_col not in columns:
        raise ValueError(f"Column '{demand_col}' not found in data. Found: {columns}")
    
    return {
        'timestamp': timestamp_col,
        'authority': authority_col,
        'demand': demand_col
    }


def load_dashboard_data():
    """Load the dashboard-ready dataset."""
    data_path = Path("outputs/tableau_exports/california_grid_dashboard_ready.csv")
    if not data_path.exists():
        raise FileNotFoundError(f"Dashboard data not found at {data_path}")
    
    df = pd.read_csv(data_path)
    
    # Detect column names
    col_map = detect_column_names(df)
    timestamp_col = col_map['timestamp']
    
    # Convert timestamp to datetime (utc=True handles mixed DST offsets)
    df[timestamp_col] = pd.to_datetime(df[timestamp_col], utc=True)
    
    return df, col_map


def load_spatial_metadata():
    """Load spatial dependency analysis results."""
    # Load correlation matrix
    corr_path = Path("outputs/spatial_correlation_matrix.csv")
    if not corr_path.exists():
        raise FileNotFoundError(f"Correlation matrix not found at {corr_path}")
    corr_matrix = pd.read_csv(corr_path, index_col=0)
    
    # Load Granger causality results
    granger_path = Path("outputs/spatial_granger_causality.csv")
    if not granger_path.exists():
        raise FileNotFoundError(f"Granger causality results not found at {granger_path}")
    granger_df = pd.read_csv(granger_path)
    
    # Load baseline LightGBM results for comparison
    baseline_path = Path("outputs/lightgbm_forecast_results.csv")
    if not baseline_path.exists():
        raise FileNotFoundError(f"LightGBM baseline results not found at {baseline_path}")
    baseline_results = pd.read_csv(baseline_path)
    
    return corr_matrix, granger_df, baseline_results


def pivot_to_wide_format(df, col_map):
    """Pivot data to wide format with authorities as columns."""
    timestamp_col = col_map['timestamp']
    authority_col = col_map['authority']
    demand_col = col_map['demand']
    
    # Pivot to wide format
    df_wide = df.pivot(
        index=timestamp_col,
        columns=authority_col,
        values=demand_col
    )
    
    # Sort by timestamp
    df_wide = df_wide.sort_index()
    
    # Remove any rows with missing values
    df_wide = df_wide.dropna()
    
    return df_wide


def create_spatial_features(df_wide, target_authority, corr_matrix, granger_df):
    """
    Create graph-inspired spatial features for a target authority.
    
    Args:
        df_wide: DataFrame with authorities as columns
        target_authority: Authority to forecast
        corr_matrix: Correlation matrix between authorities
        granger_df: Granger causality results
    
    Returns:
        DataFrame with spatial features added
    """
    df_spatial = pd.DataFrame(index=df_wide.index)
    
    # Get other authorities (exclude target)
    other_authorities = [col for col in df_wide.columns if col != target_authority]
    
    # 1. Lag-1h demand from other authorities
    for auth in other_authorities:
        df_spatial[f'spatial_lag1h_{auth}'] = df_wide[auth].shift(1)
    
    # 2. Lag-24h demand from other authorities
    for auth in other_authorities:
        df_spatial[f'spatial_lag24h_{auth}'] = df_wide[auth].shift(24)
    
    # 3. Correlation-weighted neighbor demand (lag-1h)
    # Weight each authority's demand by its correlation with target
    weighted_demand = pd.Series(0, index=df_wide.index)
    total_weight = 0
    
    for auth in other_authorities:
        if auth in corr_matrix.columns and target_authority in corr_matrix.index:
            corr = corr_matrix.loc[target_authority, auth]
            if not pd.isna(corr) and corr > 0:
                weighted_demand += df_wide[auth].shift(1) * corr
                total_weight += corr
    
    if total_weight > 0:
        df_spatial['spatial_corr_weighted_demand'] = weighted_demand / total_weight
    else:
        df_spatial['spatial_corr_weighted_demand'] = 0
    
    # 4. Average demand of connected authorities (correlation > 0.5)
    connected_authorities = []
    for auth in other_authorities:
        if auth in corr_matrix.columns and target_authority in corr_matrix.index:
            corr = corr_matrix.loc[target_authority, auth]
            if not pd.isna(corr) and corr > 0.5:
                connected_authorities.append(auth)
    
    if connected_authorities:
        df_spatial['spatial_avg_connected'] = df_wide[connected_authorities].shift(1).mean(axis=1)
    else:
        df_spatial['spatial_avg_connected'] = 0
    
    # 5. Strongest correlated authority demand
    if target_authority in corr_matrix.index:
        correlations = corr_matrix.loc[target_authority, other_authorities]
        correlations = correlations.dropna()
        if len(correlations) > 0:
            strongest_auth = correlations.abs().idxmax()
            df_spatial['spatial_strongest_corr'] = df_wide[strongest_auth].shift(1)
            df_spatial['spatial_strongest_corr_value'] = correlations[strongest_auth]
        else:
            df_spatial['spatial_strongest_corr'] = 0
            df_spatial['spatial_strongest_corr_value'] = 0
    else:
        df_spatial['spatial_strongest_corr'] = 0
        df_spatial['spatial_strongest_corr_value'] = 0
    
    # 6. Granger-causal authority demand (authorities that help predict target)
    # Find authorities where cause=auth, effect=target, significant=True
    causal_authorities = granger_df[
        (granger_df['effect'] == target_authority) & 
        (granger_df['significant'] == True)
    ]['cause'].tolist()
    
    if causal_authorities:
        # Average demand from causal authorities
        df_spatial['spatial_granger_causal_avg'] = df_wide[causal_authorities].shift(1).mean(axis=1)
        
        # Strongest causal authority (highest RSS improvement)
        strongest_causal = granger_df[
            (granger_df['effect'] == target_authority) & 
            (granger_df['significant'] == True)
        ].nlargest(1, 'rss_improvement_pct')
        
        if len(strongest_causal) > 0:
            strongest_causal_auth = strongest_causal.iloc[0]['cause']
            df_spatial['spatial_strongest_causal'] = df_wide[strongest_causal_auth].shift(1)
        else:
            df_spatial['spatial_strongest_causal'] = 0
    else:
        df_spatial['spatial_granger_causal_avg'] = 0
        df_spatial['spatial_strongest_causal'] = 0
    
    # 7. Rolling neighbor demand averages (24h and 168h windows)
    if other_authorities:
        df_spatial['spatial_rolling_24h_avg'] = df_wide[other_authorities].shift(1).rolling(window=24, min_periods=1).mean().mean(axis=1)
        df_spatial['spatial_rolling_168h_avg'] = df_wide[other_authorities].shift(1).rolling(window=168, min_periods=1).mean().mean(axis=1)
    else:
        df_spatial['spatial_rolling_24h_avg'] = 0
        df_spatial['spatial_rolling_168h_avg'] = 0
    
    return df_spatial


def create_baseline_features(df_wide, target_authority):
    """Create baseline temporal features (same as LightGBM baseline)."""
    df_baseline = pd.DataFrame(index=df_wide.index)
    
    target_series = df_wide[target_authority]
    
    # Lag features
    df_baseline['lag_1h'] = target_series.shift(1)
    df_baseline['lag_24h'] = target_series.shift(24)
    df_baseline['lag_168h'] = target_series.shift(168)
    
    # Rolling mean features
    df_baseline['rolling_mean_24h'] = target_series.shift(1).rolling(window=24, min_periods=1).mean()
    df_baseline['rolling_mean_7d'] = target_series.shift(1).rolling(window=168, min_periods=1).mean()
    
    # Time-based features
    df_baseline['hour'] = df_wide.index.hour
    df_baseline['day_of_week'] = df_wide.index.dayofweek
    
    return df_baseline


def calculate_metrics(y_true, y_pred):
    """Calculate comprehensive evaluation metrics."""
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    
    # MAPE
    mask = y_true != 0
    mape = np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100 if mask.sum() > 0 else np.nan
    
    # SMAPE
    numerator = np.abs(y_true - y_pred)
    denominator = (np.abs(y_true) + np.abs(y_pred)) / 2
    mask = denominator != 0
    smape = np.mean(numerator[mask] / denominator[mask]) * 100 if mask.sum() > 0 else np.nan
    
    # MAE
    mae = np.mean(np.abs(y_true - y_pred))
    
    # RMSE
    rmse = np.sqrt(np.mean((y_true - y_pred) ** 2))
    
    # Median Percentage Error
    pct_errors = np.abs((y_true - y_pred) / y_true) * 100
    median_pct_error = np.median(pct_errors[~np.isnan(pct_errors)])
    
    return {
        'mape': mape,
        'smape': smape,
        'mae': mae,
        'rmse': rmse,
        'median_pct_error': median_pct_error
    }


def train_test_split_temporal(df, test_size=0.2):
    """Split data temporally (no shuffling for time series)."""
    split_idx = int(len(df) * (1 - test_size))
    train = df.iloc[:split_idx].copy()
    test = df.iloc[split_idx:].copy()
    return train, test


def forecast_with_spatial_features(df_wide, target_authority, corr_matrix, granger_df):
    """
    Train LightGBM with spatial features for one authority.
    
    Returns:
        Dictionary with results and feature importance
    """
    print(f"\n{'='*60}")
    print(f"SPATIAL FORECASTING: {target_authority}")
    print(f"{'='*60}")
    
    # Create baseline features
    df_baseline = create_baseline_features(df_wide, target_authority)
    
    # Create spatial features
    df_spatial = create_spatial_features(df_wide, target_authority, corr_matrix, granger_df)
    
    # Combine features
    df_features = pd.concat([df_baseline, df_spatial], axis=1)
    df_features['target'] = df_wide[target_authority]
    
    # Drop rows with NaN
    df_features = df_features.dropna()
    
    print(f"  Total samples: {len(df_features):,}")
    print(f"  Baseline features: {len(df_baseline.columns)}")
    print(f"  Spatial features: {len(df_spatial.columns)}")
    print(f"  Total features: {len(df_features.columns) - 1}")
    
    # Split train/test
    train_df, test_df = train_test_split_temporal(df_features, test_size=0.2)
    
    feature_cols = [col for col in df_features.columns if col != 'target']
    X_train = train_df[feature_cols]
    y_train = train_df['target']
    X_test = test_df[feature_cols]
    y_test = test_df['target']
    
    print(f"  Train samples: {len(train_df):,}")
    print(f"  Test samples: {len(test_df):,}")
    
    # Train LightGBM with spatial features
    print(f"  Training LightGBM with spatial features...")
    
    params = {
        'objective': 'regression',
        'metric': 'mape',
        'boosting_type': 'gbdt',
        'num_leaves': 31,
        'learning_rate': 0.05,
        'feature_fraction': 0.9,
        'bagging_fraction': 0.8,
        'bagging_freq': 5,
        'verbose': -1
    }
    
    train_data = lgb.Dataset(X_train, label=y_train)
    valid_data = lgb.Dataset(X_test, label=y_test, reference=train_data)
    
    model = lgb.train(
        params,
        train_data,
        num_boost_round=1000,
        valid_sets=[valid_data],
        callbacks=[lgb.early_stopping(stopping_rounds=50), lgb.log_evaluation(period=0)]
    )
    
    # Generate predictions
    y_pred_test = model.predict(X_test, num_iteration=model.best_iteration)
    y_pred_test = np.clip(y_pred_test, 0, None)
    
    # Calculate metrics
    metrics = calculate_metrics(y_test, y_pred_test)
    
    print(f"  Test MAPE: {metrics['mape']:.2f}%")
    print(f"  Test SMAPE: {metrics['smape']:.2f}%")
    print(f"  Test MAE: {metrics['mae']:.1f} MW")
    print(f"  Test RMSE: {metrics['rmse']:.1f} MW")
    print(f"  Median % Error: {metrics['median_pct_error']:.2f}%")
    
    # LDWP adjusted metrics
    ldwp_adjusted_mape = None
    if target_authority == 'LDWP':
        high_demand_mask = y_test >= 250
        if high_demand_mask.sum() > 0:
            ldwp_adjusted_mape = calculate_metrics(
                y_test[high_demand_mask],
                y_pred_test[high_demand_mask]
            )['mape']
            print(f"  LDWP Adjusted MAPE (≥250 MW): {ldwp_adjusted_mape:.2f}%")
    
    # Feature importance
    importance = model.feature_importance(importance_type='gain')
    feature_importance = dict(zip(feature_cols, importance))
    
    # Separate baseline vs spatial importance
    baseline_importance = {k: v for k, v in feature_importance.items() if not k.startswith('spatial_')}
    spatial_importance = {k: v for k, v in feature_importance.items() if k.startswith('spatial_')}
    
    total_importance = sum(feature_importance.values())
    baseline_pct = sum(baseline_importance.values()) / total_importance * 100 if total_importance > 0 else 0
    spatial_pct = sum(spatial_importance.values()) / total_importance * 100 if total_importance > 0 else 0
    
    print(f"  Feature importance: Baseline {baseline_pct:.1f}%, Spatial {spatial_pct:.1f}%")
    
    # Top 5 features
    top_features = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)[:5]
    print(f"  Top 5 features:")
    for feat, imp in top_features:
        print(f"    - {feat}: {imp:.0f}")
    
    return {
        'authority': target_authority,
        'test_mape': metrics['mape'],
        'test_smape': metrics['smape'],
        'test_mae': metrics['mae'],
        'test_rmse': metrics['rmse'],
        'median_pct_error': metrics['median_pct_error'],
        'ldwp_adjusted_mape': ldwp_adjusted_mape,
        'test_samples': len(test_df),
        'train_samples': len(train_df),
        'n_features': len(feature_cols),
        'n_baseline_features': len(baseline_importance),
        'n_spatial_features': len(spatial_importance),
        'baseline_importance_pct': baseline_pct,
        'spatial_importance_pct': spatial_pct,
        'feature_importance': feature_importance,
        'best_iteration': model.best_iteration
    }


def generate_comparison_report(results_df, baseline_results, output_dir):
    """Generate comprehensive comparison report."""
    report_path = output_dir / 'spatial_feature_report.md'
    
    # Load feature importance from CSV
    importance_path = output_dir / 'spatial_feature_importance.csv'
    if importance_path.exists():
        importance_df = pd.read_csv(importance_path)
    else:
        importance_df = None
    
    # Merge with baseline results
    baseline_results = baseline_results.rename(columns={
        'authority': 'authority',
        'test_mape': 'baseline_mape'
    })
    
    comparison = results_df.merge(
        baseline_results[['authority', 'baseline_mape']],
        on='authority',
        how='left'
    )
    
    # Calculate improvements
    comparison['improvement_mape'] = comparison['baseline_mape'] - comparison['test_mape']
    comparison['improvement_pct'] = (comparison['improvement_mape'] / comparison['baseline_mape']) * 100
    
    # Overall statistics
    avg_baseline = comparison['baseline_mape'].mean()
    avg_spatial = comparison['test_mape'].mean()
    overall_improvement = avg_baseline - avg_spatial
    overall_improvement_pct = (overall_improvement / avg_baseline) * 100
    
    # Count improvements
    n_improved = (comparison['improvement_mape'] > 0).sum()
    n_total = len(comparison)
    
    # Determine recommendation
    if overall_improvement_pct > 5:
        recommendation = "JUSTIFIED"
        recommendation_icon = "✅"
        recommendation_text = "Spatial features provide significant improvement (>5%). GNN implementation is justified as a research extension."
    elif overall_improvement_pct > 0:
        recommendation = "OPTIONAL"
        recommendation_icon = "⚠️"
        recommendation_text = f"Spatial features provide marginal improvement ({overall_improvement_pct:.1f}%). GNN is optional but not high priority."
    else:
        recommendation = "NOT JUSTIFIED"
        recommendation_icon = "❌"
        recommendation_text = "Spatial features do not improve performance. GNN implementation is not justified."
    
    with open(report_path, 'w') as f:
        f.write("# Spatial Feature Forecasting Report\n\n")
        f.write("**California Grid Demand Forecasting**\n\n")
        f.write(f"**Generated:** {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("---\n\n")
        
        f.write("## Executive Summary\n\n")
        f.write("This analysis validates whether spatial information improves forecasting performance ")
        f.write("before implementing a Graph Neural Network (GNN).\n\n")
        
        f.write("### Key Findings\n\n")
        f.write(f"- **Baseline LightGBM MAPE:** {avg_baseline:.2f}%\n")
        f.write(f"- **LightGBM + Spatial Features MAPE:** {avg_spatial:.2f}%\n")
        f.write(f"- **Overall Improvement:** {overall_improvement:+.2f}% ({overall_improvement_pct:+.1f}%)\n")
        f.write(f"- **Authorities Improved:** {n_improved}/{n_total}\n")
        f.write(f"- **Average Spatial Feature Importance:** {comparison['spatial_importance_pct'].mean():.1f}%\n\n")
        
        f.write("### Recommendation\n\n")
        f.write(f"{recommendation_icon} **GNN IMPLEMENTATION: {recommendation}**\n\n")
        f.write(f"{recommendation_text}\n\n")
        
        f.write("---\n\n")
        
        f.write("## 1. Performance Comparison\n\n")
        f.write("### Overall Results\n\n")
        f.write("| Authority | Baseline MAPE | Spatial MAPE | Improvement | Spatial Importance |\n")
        f.write("|-----------|---------------|--------------|-------------|--------------------|\n")
        
        for _, row in comparison.iterrows():
            auth = row['authority']
            baseline = row['baseline_mape']
            spatial = row['test_mape']
            improvement = row['improvement_mape']
            improvement_pct = row['improvement_pct']
            spatial_imp = row['spatial_importance_pct']
            
            improvement_str = f"{improvement:+.2f}% ({improvement_pct:+.1f}%)"
            
            f.write(f"| {auth} | {baseline:.2f}% | {spatial:.2f}% | {improvement_str} | {spatial_imp:.1f}% |\n")
        
        f.write(f"| **AVERAGE** | **{avg_baseline:.2f}%** | **{avg_spatial:.2f}%** | ")
        f.write(f"**{overall_improvement:+.2f}% ({overall_improvement_pct:+.1f}%)** | ")
        f.write(f"**{comparison['spatial_importance_pct'].mean():.1f}%** |\n\n")
        
        f.write("### Interpretation\n\n")
        if overall_improvement_pct > 5:
            f.write("✅ **Significant improvement detected.** Spatial features provide substantial value.\n\n")
        elif overall_improvement_pct > 0:
            f.write("⚠️ **Marginal improvement detected.** Spatial features provide some value but not transformative.\n\n")
        else:
            f.write("❌ **No improvement detected.** Spatial features do not add predictive value.\n\n")
        
        f.write("---\n\n")
        
        f.write("## 2. Authority-Specific Analysis\n\n")
        
        # Best improvements
        best_improvements = comparison.nlargest(3, 'improvement_pct')
        f.write("### Top 3 Improvements\n\n")
        for _, row in best_improvements.iterrows():
            f.write(f"**{row['authority']}:** {row['improvement_mape']:+.2f}% ({row['improvement_pct']:+.1f}%)\n")
            f.write(f"- Baseline: {row['baseline_mape']:.2f}% → Spatial: {row['test_mape']:.2f}%\n")
            f.write(f"- Spatial feature importance: {row['spatial_importance_pct']:.1f}%\n\n")
        
        # LDWP specific
        ldwp_row = comparison[comparison['authority'] == 'LDWP']
        if len(ldwp_row) > 0:
            ldwp_row = ldwp_row.iloc[0]
            f.write("### LDWP Analysis\n\n")
            f.write(f"- **Baseline MAPE:** {ldwp_row['baseline_mape']:.2f}%\n")
            f.write(f"- **Spatial MAPE:** {ldwp_row['test_mape']:.2f}%\n")
            f.write(f"- **Improvement:** {ldwp_row['improvement_mape']:+.2f}% ({ldwp_row['improvement_pct']:+.1f}%)\n")
            if pd.notna(ldwp_row['ldwp_adjusted_mape']):
                f.write(f"- **Adjusted MAPE (≥250 MW):** {ldwp_row['ldwp_adjusted_mape']:.2f}%\n")
            f.write(f"- **Spatial feature importance:** {ldwp_row['spatial_importance_pct']:.1f}%\n\n")
            
            if ldwp_row['improvement_pct'] > 5:
                f.write("✅ LDWP significantly benefited from spatial features.\n\n")
            elif ldwp_row['improvement_pct'] > 0:
                f.write("⚠️ LDWP showed marginal improvement from spatial features.\n\n")
            else:
                f.write("❌ LDWP did not benefit from spatial features.\n\n")
        
        f.write("---\n\n")
        
        f.write("## 3. Feature Importance Analysis\n\n")
        
        # Average feature importance by type
        avg_baseline_imp = comparison['baseline_importance_pct'].mean()
        avg_spatial_imp = comparison['spatial_importance_pct'].mean()
        
        f.write("### Feature Type Importance\n\n")
        f.write(f"- **Baseline Features (temporal):** {avg_baseline_imp:.1f}%\n")
        f.write(f"- **Spatial Features (graph-inspired):** {avg_spatial_imp:.1f}%\n\n")
        
        if avg_spatial_imp > 30:
            f.write("✅ Spatial features are highly important (>30% of total importance).\n\n")
        elif avg_spatial_imp > 15:
            f.write("⚠️ Spatial features are moderately important (15-30% of total importance).\n\n")
        else:
            f.write("❌ Spatial features have low importance (<15% of total importance).\n\n")
        
        f.write("### Most Important Spatial Features\n\n")
        f.write("Aggregated across all authorities:\n\n")
        
        # Aggregate feature importance from CSV
        if importance_df is not None:
            spatial_importance = importance_df[importance_df['is_spatial'] == True].copy()
            if len(spatial_importance) > 0:
                # Aggregate by feature name
                agg_importance = spatial_importance.groupby('feature')['importance'].sum().reset_index()
                agg_importance = agg_importance.sort_values('importance', ascending=False)
                
                top_spatial = agg_importance.head(10)
                for i, (_, row) in enumerate(top_spatial.iterrows(), 1):
                    f.write(f"{i}. `{row['feature']}`: {row['importance']:.0f}\n")
            else:
                f.write("No spatial features found in importance data.\n")
        else:
            f.write("Feature importance data not available.\n")
        
        f.write("\n---\n\n")
        
        f.write("## 4. Comprehensive Metrics\n\n")
        f.write("### All Evaluation Metrics\n\n")
        f.write("| Authority | MAPE | SMAPE | MAE (MW) | RMSE (MW) | Median % Error |\n")
        f.write("|-----------|------|-------|----------|-----------|----------------|\n")
        
        for _, row in results_df.iterrows():
            f.write(f"| {row['authority']} | {row['test_mape']:.2f}% | {row['test_smape']:.2f}% | ")
            f.write(f"{row['test_mae']:.1f} | {row['test_rmse']:.1f} | {row['median_pct_error']:.2f}% |\n")
        
        f.write("\n---\n\n")
        
        f.write("## 5. GNN Implementation Decision\n\n")
        
        if recommendation == "JUSTIFIED":
            f.write("### ✅ PROCEED WITH GNN IMPLEMENTATION\n\n")
            f.write("**Evidence:**\n")
            f.write(f"- Spatial features improved performance by {overall_improvement_pct:.1f}%\n")
            f.write(f"- {n_improved}/{n_total} authorities benefited\n")
            f.write(f"- Spatial features account for {avg_spatial_imp:.1f}% of model importance\n\n")
            f.write("**Recommended Architecture:**\n")
            f.write("1. **Temporal Graph Convolutional Network (T-GCN)**\n")
            f.write("2. **Graph structure:** Use correlation matrix as edge weights\n")
            f.write("3. **Node features:** Include temporal lags and rolling statistics\n")
            f.write("4. **Message passing:** Aggregate neighbor information via graph convolution\n")
            f.write("5. **Target:** Further improve upon LightGBM+Spatial baseline\n\n")
            f.write("**Expected Benefits:**\n")
            f.write("- Better capture of spatial dependencies\n")
            f.write("- Joint optimization across all authorities\n")
            f.write("- Potential for 10-20% additional improvement\n\n")
            
        elif recommendation == "OPTIONAL":
            f.write("### ⚠️ GNN IMPLEMENTATION IS OPTIONAL\n\n")
            f.write("**Evidence:**\n")
            f.write(f"- Spatial features improved performance by only {overall_improvement_pct:.1f}%\n")
            f.write(f"- Improvement is marginal (<5%)\n")
            f.write(f"- Spatial features account for {avg_spatial_imp:.1f}% of model importance\n\n")
            f.write("**Recommendation:**\n")
            f.write("- GNN may provide incremental improvements but is not high priority\n")
            f.write("- Consider GNN only if:\n")
            f.write("  - Research time is available\n")
            f.write("  - Interested in exploring graph-based methods\n")
            f.write("  - Need to demonstrate cutting-edge techniques\n\n")
            f.write("**Alternative:**\n")
            f.write("- Continue with LightGBM + Spatial Features (current best model)\n")
            f.write("- Focus on feature engineering and hyperparameter tuning\n")
            f.write("- Investigate external data sources (weather, events)\n\n")
            
        else:
            f.write("### ❌ DO NOT IMPLEMENT GNN\n\n")
            f.write("**Evidence:**\n")
            f.write(f"- Spatial features did not improve performance ({overall_improvement_pct:+.1f}%)\n")
            f.write(f"- Spatial features account for only {avg_spatial_imp:.1f}% of model importance\n")
            f.write("- Authorities operate independently for forecasting purposes\n\n")
            f.write("**Recommendation:**\n")
            f.write("- **Do not implement GNN** - spatial modeling is not justified\n")
            f.write("- Continue with baseline LightGBM (already excellent performance)\n")
            f.write("- Focus on per-authority improvements:\n")
            f.write("  - Hyperparameter tuning\n")
            f.write("  - Additional temporal features\n")
            f.write("  - External data integration (weather, events)\n")
            f.write("  - Ensemble methods\n\n")
        
        f.write("---\n\n")
        
        f.write("## 6. Research Progression Summary\n\n")
        f.write("This analysis completes the evidence-based research progression:\n\n")
        f.write("1. ✅ **Forecasting Benchmark** - Established baseline (Naive: 11.05% MAPE)\n")
        f.write("2. ✅ **Failure Analysis** - Identified LDWP as outlier (32.76% MAPE)\n")
        f.write("3. ✅ **Metric Robustness Analysis** - Validated SMAPE and adjusted MAPE\n")
        f.write("4. ✅ **Spatial Dependency Analysis** - Found correlations and Granger causality\n")
        f.write("5. ✅ **Spatial Feature Validation** - Tested graph-inspired features\n")
        f.write(f"6. {recommendation_icon} **Evidence-Based GNN Decision** - {recommendation}\n\n")
        
        f.write("---\n\n")
        
        f.write("## 7. Next Steps\n\n")
        
        if recommendation == "JUSTIFIED":
            f.write("### Immediate Actions\n\n")
            f.write("1. **Design GNN architecture** (T-GCN or GraphSAGE)\n")
            f.write("2. **Implement graph construction** from correlation matrix\n")
            f.write("3. **Train GNN model** with temporal and spatial features\n")
            f.write("4. **Compare GNN vs LightGBM+Spatial** on validation set\n")
            f.write("5. **Document results** and update portfolio\n\n")
            
        elif recommendation == "OPTIONAL":
            f.write("### Recommended Actions\n\n")
            f.write("1. **Deploy LightGBM + Spatial Features** as production model\n")
            f.write("2. **Monitor performance** in production\n")
            f.write("3. **Consider GNN as research extension** if time permits\n")
            f.write("4. **Focus on operational deployment** and monitoring\n\n")
            
        else:
            f.write("### Recommended Actions\n\n")
            f.write("1. **Deploy baseline LightGBM** as production model\n")
            f.write("2. **Focus on per-authority improvements**\n")
            f.write("3. **Investigate external features** (weather, events)\n")
            f.write("4. **Do not pursue GNN** - not justified by evidence\n\n")
        
        f.write("---\n\n")
        
        f.write("## Appendix: Detailed Results\n\n")
        f.write("### Complete Comparison Table\n\n")
        f.write("```\n")
        f.write(comparison.to_string(index=False))
        f.write("\n```\n\n")
    
    print(f"\n✓ Report saved to {report_path}")


def run_spatial_feature_benchmark(output_dir=None):
    """Run complete spatial feature forecasting benchmark."""
    if output_dir is None:
        output_dir = Path("outputs")
    else:
        output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("\n" + "="*70)
    print("SPATIAL FEATURE FORECASTING BENCHMARK")
    print("="*70)
    print("\nValidating whether spatial information improves forecasting...")
    print("Goal: Determine if GNN implementation is justified\n")
    
    # Load data
    print("Loading data...")
    df, col_map = load_dashboard_data()
    
    timestamp_col = col_map['timestamp']
    authority_col = col_map['authority']
    
    authorities = sorted(df[authority_col].unique())
    print(f"Authorities: {', '.join(authorities)}")
    
    # Load spatial metadata
    print("Loading spatial dependency analysis...")
    corr_matrix, granger_df, baseline_results = load_spatial_metadata()
    
    # Pivot to wide format
    print("Pivoting to wide format...")
    df_wide = pivot_to_wide_format(df, col_map)
    print(f"Samples: {len(df_wide):,}")
    
    # Run spatial feature forecasting for each authority
    results = []
    
    for authority in authorities:
        result = forecast_with_spatial_features(df_wide, authority, corr_matrix, granger_df)
        results.append(result)
    
    # Create results DataFrame
    results_df = pd.DataFrame([
        {
            'authority': r['authority'],
            'test_mape': r['test_mape'],
            'test_smape': r['test_smape'],
            'test_mae': r['test_mae'],
            'test_rmse': r['test_rmse'],
            'median_pct_error': r['median_pct_error'],
            'ldwp_adjusted_mape': r['ldwp_adjusted_mape'],
            'test_samples': r['test_samples'],
            'n_features': r['n_features'],
            'n_baseline_features': r['n_baseline_features'],
            'n_spatial_features': r['n_spatial_features'],
            'baseline_importance_pct': r['baseline_importance_pct'],
            'spatial_importance_pct': r['spatial_importance_pct']
        }
        for r in results
    ])
    
    # Save results
    results_path = output_dir / 'spatial_feature_results.csv'
    results_df.to_csv(results_path, index=False)
    print(f"\n✓ Results saved to {results_path}")
    
    # Save feature importance
    importance_records = []
    for r in results:
        for feat, imp in r['feature_importance'].items():
            importance_records.append({
                'authority': r['authority'],
                'feature': feat,
                'importance': imp,
                'is_spatial': feat.startswith('spatial_')
            })
    
    importance_df = pd.DataFrame(importance_records)
    importance_path = output_dir / 'spatial_feature_importance.csv'
    importance_df.to_csv(importance_path, index=False)
    print(f"✓ Feature importance saved to {importance_path}")
    
    # Create comparison table
    comparison_df = results_df.merge(
        baseline_results[['authority', 'test_mape']].rename(columns={'test_mape': 'baseline_mape'}),
        on='authority',
        how='left'
    )
    comparison_df['improvement_mape'] = comparison_df['baseline_mape'] - comparison_df['test_mape']
    comparison_df['improvement_pct'] = (comparison_df['improvement_mape'] / comparison_df['baseline_mape']) * 100
    
    comparison_path = output_dir / 'spatial_feature_comparison.csv'
    comparison_df.to_csv(comparison_path, index=False)
    print(f"✓ Comparison table saved to {comparison_path}")
    
    # Print summary
    print("\n" + "="*70)
    print("SPATIAL FEATURE RESULTS SUMMARY")
    print("="*70)
    
    avg_baseline = comparison_df['baseline_mape'].mean()
    avg_spatial = comparison_df['test_mape'].mean()
    overall_improvement = avg_baseline - avg_spatial
    overall_improvement_pct = (overall_improvement / avg_baseline) * 100
    
    print(f"\nBaseline LightGBM MAPE: {avg_baseline:.2f}%")
    print(f"LightGBM + Spatial Features MAPE: {avg_spatial:.2f}%")
    print(f"Overall Improvement: {overall_improvement:+.2f}% ({overall_improvement_pct:+.1f}%)")
    
    n_improved = (comparison_df['improvement_mape'] > 0).sum()
    print(f"Authorities Improved: {n_improved}/{len(comparison_df)}")
    
    avg_spatial_importance = comparison_df['spatial_importance_pct'].mean()
    print(f"Average Spatial Feature Importance: {avg_spatial_importance:.1f}%")
    
    # Recommendation
    print("\n" + "="*70)
    print("GNN IMPLEMENTATION RECOMMENDATION")
    print("="*70)
    
    if overall_improvement_pct > 5:
        print("\n✅ GNN IMPLEMENTATION: JUSTIFIED")
        print(f"\nSpatial features improved performance by {overall_improvement_pct:.1f}% (>5% threshold).")
        print("Graph-based modeling is justified as a research extension.")
        print("\nNext step: Implement Temporal Graph Convolutional Network (T-GCN)")
    elif overall_improvement_pct > 0:
        print("\n⚠️  GNN IMPLEMENTATION: OPTIONAL")
        print(f"\nSpatial features improved performance by {overall_improvement_pct:.1f}% (<5% threshold).")
        print("GNN may provide marginal improvements but is not high priority.")
        print("\nRecommendation: Continue with LightGBM + Spatial Features")
    else:
        print("\n❌ GNN IMPLEMENTATION: NOT JUSTIFIED")
        print(f"\nSpatial features did not improve performance ({overall_improvement_pct:+.1f}%).")
        print("Graph-based modeling is not justified by the evidence.")
        print("\nRecommendation: Continue with baseline LightGBM")
    
    print("="*70)
    
    # Generate report
    print("\nGenerating comprehensive report...")
    generate_comparison_report(results_df, baseline_results, output_dir)
    
    print("\n" + "="*70)
    print("SPATIAL FEATURE BENCHMARK COMPLETE")
    print("="*70)
    print("\nOutputs:")
    print(f"  - {output_dir}/spatial_feature_results.csv")
    print(f"  - {output_dir}/spatial_feature_importance.csv")
    print(f"  - {output_dir}/spatial_feature_comparison.csv")
    print(f"  - {output_dir}/spatial_feature_report.md")
    print("="*70 + "\n")
    
    return results_df, comparison_df


if __name__ == "__main__":
    run_spatial_feature_benchmark()
