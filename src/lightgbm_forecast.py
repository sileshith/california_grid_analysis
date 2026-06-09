"""
LightGBM Forecasting Implementation

Implements LightGBM gradient boosting for time series forecasting with lag-based features.
Compares against naive baseline and Prophet models.

Features:
- 1-hour, 24-hour, 168-hour lags
- Rolling 24-hour and 7-day means
- Hour of day and day of week
- Per-authority models

Target: Outperform naive baseline (11.05% MAPE) and Prophet
"""

import pandas as pd
import numpy as np
from pathlib import Path
import lightgbm as lgb
import warnings
warnings.filterwarnings('ignore')


def detect_column_names(df):
    """
    Detect the correct column names for timestamp, authority, and demand.
    
    Args:
        df: DataFrame to inspect
    
    Returns:
        Dictionary with keys: 'timestamp', 'authority', 'demand'
    """
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


def create_lag_features(df, target_col='demand_mw', timestamp_col='timestamp_utc'):
    """
    Create lag-based features for time series forecasting.
    
    Args:
        df: DataFrame with timestamp and target column
        target_col: Column name for demand values
        timestamp_col: Column name for timestamp
    
    Returns:
        DataFrame with lag features added
    """
    df = df.copy()
    df = df.sort_values(timestamp_col)
    
    # Lag features
    df['lag_1h'] = df[target_col].shift(1)
    df['lag_24h'] = df[target_col].shift(24)
    df['lag_168h'] = df[target_col].shift(168)  # 1 week
    
    # Rolling mean features
    df['rolling_mean_24h'] = df[target_col].shift(1).rolling(window=24, min_periods=1).mean()
    df['rolling_mean_7d'] = df[target_col].shift(1).rolling(window=168, min_periods=1).mean()
    
    # Time-based features
    df['hour'] = pd.to_datetime(df[timestamp_col]).dt.hour
    df['day_of_week'] = pd.to_datetime(df[timestamp_col]).dt.dayofweek
    
    return df


def calculate_mape(y_true, y_pred):
    """Calculate Mean Absolute Percentage Error."""
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    
    # Remove any zero values to avoid division by zero
    mask = y_true != 0
    y_true = y_true[mask]
    y_pred = y_pred[mask]
    
    if len(y_true) == 0:
        return np.nan
    
    return np.mean(np.abs((y_true - y_pred) / y_true)) * 100


def train_test_split_temporal(df, test_size=0.2):
    """Split data temporally (no shuffling for time series)."""
    split_idx = int(len(df) * (1 - test_size))
    train = df.iloc[:split_idx].copy()
    test = df.iloc[split_idx:].copy()
    return train, test


def forecast_authority(df, authority, col_map):
    """Train LightGBM and generate forecasts for one authority."""
    print(f"\n{'='*60}")
    print(f"FORECASTING: {authority}")
    print(f"{'='*60}")
    
    timestamp_col = col_map['timestamp']
    authority_col = col_map['authority']
    demand_col = col_map['demand']
    
    # Filter to this authority
    auth_df = df[df[authority_col] == authority].copy()
    auth_df = auth_df.sort_values(timestamp_col)
    
    print(f"  Total samples: {len(auth_df):,}")
    
    # Create lag features
    auth_df = create_lag_features(auth_df, target_col=demand_col, timestamp_col=timestamp_col)
    
    # Drop rows with NaN in features (due to lagging)
    feature_cols = ['lag_1h', 'lag_24h', 'lag_168h', 'rolling_mean_24h', 'rolling_mean_7d', 'hour', 'day_of_week']
    auth_df = auth_df.dropna(subset=feature_cols)
    
    print(f"  Samples after feature creation: {len(auth_df):,}")
    
    # Split train/test
    train_df, test_df = train_test_split_temporal(auth_df, test_size=0.2)
    print(f"  Train samples: {len(train_df):,}")
    print(f"  Test samples: {len(test_df):,}")
    
    # Prepare features and target
    X_train = train_df[feature_cols]
    y_train = train_df[demand_col]
    X_test = test_df[feature_cols]
    y_test = test_df[demand_col]
    
    # Train LightGBM model
    print(f"  Training LightGBM model...")
    
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
    y_pred_train = model.predict(X_train, num_iteration=model.best_iteration)
    y_pred_test = model.predict(X_test, num_iteration=model.best_iteration)
    
    # Clip predictions at zero (demand cannot be negative)
    y_pred_train = np.clip(y_pred_train, 0, None)
    y_pred_test = np.clip(y_pred_test, 0, None)
    
    # Calculate MAPE
    train_mape = calculate_mape(y_train, y_pred_train)
    test_mape = calculate_mape(y_test, y_pred_test)
    
    print(f"  Train MAPE: {train_mape:.2f}%")
    print(f"  Test MAPE: {test_mape:.2f}%")
    
    # Calculate additional metrics
    test_errors = y_test - y_pred_test
    mae = np.abs(test_errors).mean()
    rmse = np.sqrt((test_errors ** 2).mean())
    print(f"  Test MAE: {mae:.1f} MW")
    print(f"  Test RMSE: {rmse:.1f} MW")
    
    # Feature importance
    importance = model.feature_importance(importance_type='gain')
    feature_importance = dict(zip(feature_cols, importance))
    top_features = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)[:3]
    print(f"  Top 3 features: {', '.join([f'{k}' for k, v in top_features])}")
    
    return {
        'authority': authority,
        'test_mape': test_mape,
        'train_mape': train_mape,
        'test_samples': len(test_df),
        'train_samples': len(train_df),
        'mae': mae,
        'rmse': rmse,
        'best_iteration': model.best_iteration,
        'feature_importance': feature_importance
    }


def run_lightgbm_forecasts(output_dir=None):
    """Run LightGBM forecasts for all authorities."""
    if output_dir is None:
        output_dir = Path("outputs")
    else:
        output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("\n" + "="*70)
    print("LIGHTGBM FORECASTING - CALIFORNIA GRID DEMAND")
    print("="*70)
    print("\nLoading data...")
    
    df, col_map = load_dashboard_data()
    
    timestamp_col = col_map['timestamp']
    authority_col = col_map['authority']
    
    authorities = sorted(df[authority_col].unique())
    
    print(f"\nDataset: {len(df):,} total samples")
    print(f"Authorities: {', '.join(authorities)}")
    print(f"Date range: {df[timestamp_col].min()} to {df[timestamp_col].max()}")
    
    # Run forecasts for each authority
    results = []
    
    for authority in authorities:
        result = forecast_authority(df, authority, col_map)
        results.append({
            'authority': result['authority'],
            'test_mape': result['test_mape'],
            'train_mape': result['train_mape'],
            'test_samples': result['test_samples'],
            'train_samples': result['train_samples'],
            'mae': result['mae'],
            'rmse': result['rmse'],
            'best_iteration': result['best_iteration']
        })
    
    # Create results summary
    results_df = pd.DataFrame(results)
    results_df = results_df.sort_values('test_mape')
    
    # Calculate overall metrics
    overall_mape = results_df['test_mape'].mean()
    
    print(f"\n{'='*70}")
    print("LIGHTGBM RESULTS SUMMARY")
    print(f"{'='*70}\n")
    print(results_df.to_string(index=False))
    print(f"\n{'='*70}")
    print(f"Overall Test MAPE: {overall_mape:.2f}%")
    print(f"{'='*70}")
    
    # Save results
    results_path = output_dir / 'lightgbm_forecast_results.csv'
    results_df.to_csv(results_path, index=False)
    print(f"\n✓ Results saved to {results_path}")
    
    # Compare to baseline
    print(f"\n{'='*70}")
    print("COMPARISON TO BASELINE (Naive 24h Lag)")
    print(f"{'='*70}")
    
    baseline_results = {
        'CISO': 4.75,
        'BANC': 5.78,
        'TIDC': 5.92,
        'IID': 6.04,
        'LDWP': 32.76
    }
    
    print(f"\n{'Authority':<10} {'Baseline':<12} {'LightGBM':<12} {'Improvement':<12}")
    print("-" * 50)
    
    for _, row in results_df.iterrows():
        auth = row['authority']
        lgbm_mape = row['test_mape']
        baseline_mape = baseline_results.get(auth, 0)
        improvement = baseline_mape - lgbm_mape
        improvement_pct = (improvement / baseline_mape * 100) if baseline_mape > 0 else 0
        
        print(f"{auth:<10} {baseline_mape:>6.2f}%     {lgbm_mape:>6.2f}%     {improvement:>+6.2f}% ({improvement_pct:>+5.1f}%)")
    
    baseline_avg = np.mean(list(baseline_results.values()))
    improvement_overall = baseline_avg - overall_mape
    improvement_overall_pct = (improvement_overall / baseline_avg * 100)
    
    print("-" * 50)
    print(f"{'AVERAGE':<10} {baseline_avg:>6.2f}%     {overall_mape:>6.2f}%     {improvement_overall:>+6.2f}% ({improvement_overall_pct:>+5.1f}%)")
    print(f"{'='*70}\n")
    
    return results_df


if __name__ == "__main__":
    run_lightgbm_forecasts()
