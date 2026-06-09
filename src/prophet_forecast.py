"""
Prophet Forecasting Implementation

Implements Prophet time series forecasting for all California balancing authorities.
Includes LDWP-specific tuning based on investigation findings.

Target: Overall MAPE < 10%, LDWP MAPE < 15%
Baseline: Naive 11.05% MAPE, LDWP 32.76% MAPE
"""

import pandas as pd
import numpy as np
from pathlib import Path
from prophet import Prophet
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


def prepare_prophet_data(df, authority, col_map):
    """Prepare data for Prophet (requires 'ds' and 'y' columns)."""
    timestamp_col = col_map['timestamp']
    authority_col = col_map['authority']
    demand_col = col_map['demand']
    
    auth_df = df[df[authority_col] == authority].copy()
    auth_df = auth_df.sort_values(timestamp_col)
    
    # Prophet requires specific column names and timezone-naive timestamps
    prophet_df = pd.DataFrame({
        'ds': auth_df[timestamp_col],
        'y': auth_df[demand_col]
    })
    
    # Remove any missing values
    prophet_df = prophet_df.dropna()
    
    # Convert to timezone-naive (Prophet requires this)
    if prophet_df['ds'].dt.tz is not None:
        prophet_df['ds'] = prophet_df['ds'].dt.tz_localize(None)
    
    return prophet_df


def create_prophet_model(authority):
    """Create Prophet model with authority-specific tuning."""
    
    # Base configuration for all authorities
    base_config = {
        'daily_seasonality': True,
        'weekly_seasonality': True,
        'yearly_seasonality': True,
        'seasonality_mode': 'multiplicative',
        'interval_width': 0.95
    }
    
    # LDWP-specific tuning based on investigation
    if authority == 'LDWP':
        model = Prophet(
            **base_config,
            changepoint_prior_scale=0.5,  # More flexible for volatile patterns
            seasonality_prior_scale=15.0,  # Stronger seasonality
            n_changepoints=50,  # More changepoints for volatility
            changepoint_range=0.9  # Allow changepoints throughout series
        )
        print(f"  Using LDWP-specific tuning (high volatility handling)")
    else:
        model = Prophet(
            **base_config,
            changepoint_prior_scale=0.05,  # Standard flexibility
            seasonality_prior_scale=10.0  # Standard seasonality
        )
    
    return model


def calculate_mape(y_true, y_pred):
    """Calculate Mean Absolute Percentage Error."""
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    
    # Remove any zero values to avoid division by zero
    mask = y_true != 0
    y_true = y_true[mask]
    y_pred = y_pred[mask]
    
    return np.mean(np.abs((y_true - y_pred) / y_true)) * 100


def train_test_split_temporal(df, test_size=0.2):
    """Split data temporally (no shuffling for time series)."""
    split_idx = int(len(df) * (1 - test_size))
    train = df.iloc[:split_idx].copy()
    test = df.iloc[split_idx:].copy()
    return train, test


def forecast_authority(df, authority, col_map):
    """Train Prophet and generate forecasts for one authority."""
    print(f"\n{'='*60}")
    print(f"FORECASTING: {authority}")
    print(f"{'='*60}")
    
    # Prepare data
    prophet_df = prepare_prophet_data(df, authority, col_map)
    print(f"  Total samples: {len(prophet_df):,}")
    
    # DIAGNOSTIC 1: Check for zero/near-zero values
    zero_count = (prophet_df['y'] == 0).sum()
    near_zero_count = (prophet_df['y'] < 1).sum()
    print(f"  Zero demand values: {zero_count}")
    print(f"  Near-zero demand (<1 MW): {near_zero_count}")
    
    # DIAGNOSTIC 2: Check timestamp continuity
    prophet_df_sorted = prophet_df.sort_values('ds')
    time_diffs = prophet_df_sorted['ds'].diff()
    expected_diff = pd.Timedelta(hours=1)
    gaps = time_diffs[time_diffs > expected_diff]
    print(f"  Time gaps > 1 hour: {len(gaps)}")
    if len(gaps) > 0:
        print(f"    Largest gap: {gaps.max()}")
    
    # Split train/test
    train_df, test_df = train_test_split_temporal(prophet_df, test_size=0.2)
    print(f"  Train samples: {len(train_df):,}")
    print(f"  Test samples: {len(test_df):,}")
    
    # DIAGNOSTIC 3: Check train/test split is time-ordered
    train_end = train_df['ds'].max()
    test_start = test_df['ds'].min()
    print(f"  Train end: {train_end}")
    print(f"  Test start: {test_start}")
    print(f"  Split is valid: {train_end < test_start}")
    
    # DIAGNOSTIC 4: Check demand value ranges
    print(f"  Train demand range: {train_df['y'].min():.1f} - {train_df['y'].max():.1f} MW")
    print(f"  Test demand range: {test_df['y'].min():.1f} - {test_df['y'].max():.1f} MW")
    
    # Create and train model with floor=0 to prevent negative predictions
    print(f"  Training Prophet model...")
    model = create_prophet_model(authority)
    model.fit(train_df)
    
    # Generate forecasts for test period
    future = model.make_future_dataframe(periods=len(test_df), freq='H')
    forecast = model.predict(future)
    
    # DIAGNOSTIC 5: Check for negative predictions
    negative_preds = (forecast['yhat'] < 0).sum()
    print(f"  Negative predictions: {negative_preds}")
    if negative_preds > 0:
        print(f"    Min prediction: {forecast['yhat'].min():.1f} MW")
    
    # Clip predictions at zero (demand cannot be negative)
    forecast['yhat'] = forecast['yhat'].clip(lower=0)
    forecast['yhat_lower'] = forecast['yhat_lower'].clip(lower=0)
    forecast['yhat_upper'] = forecast['yhat_upper'].clip(lower=0)
    
    # Extract test predictions
    test_forecast = forecast.iloc[-len(test_df):].copy()
    test_forecast['y_true'] = test_df['y'].values
    test_forecast['authority'] = authority
    
    # DIAGNOSTIC 6: Check prediction ranges
    print(f"  Test predictions range: {test_forecast['yhat'].min():.1f} - {test_forecast['yhat'].max():.1f} MW")
    
    # DIAGNOSTIC 7: Check for unrealistic predictions
    pred_mean = test_forecast['yhat'].mean()
    true_mean = test_forecast['y_true'].mean()
    pred_std = test_forecast['yhat'].std()
    true_std = test_forecast['y_true'].std()
    print(f"  Prediction mean: {pred_mean:.1f} MW (actual: {true_mean:.1f} MW)")
    print(f"  Prediction std: {pred_std:.1f} MW (actual: {true_std:.1f} MW)")
    
    # Calculate MAPE
    mape = calculate_mape(test_forecast['y_true'], test_forecast['yhat'])
    print(f"  Test MAPE: {mape:.2f}%")
    
    # Also calculate in-sample MAPE for comparison
    train_forecast = forecast.iloc[:len(train_df)].copy()
    train_forecast['y_true'] = train_df['y'].values
    train_mape = calculate_mape(train_forecast['y_true'], train_forecast['yhat'])
    print(f"  Train MAPE: {train_mape:.2f}%")
    
    # DIAGNOSTIC 8: Calculate error metrics
    test_errors = test_forecast['y_true'] - test_forecast['yhat']
    mae = np.abs(test_errors).mean()
    rmse = np.sqrt((test_errors ** 2).mean())
    print(f"  Test MAE: {mae:.1f} MW")
    print(f"  Test RMSE: {rmse:.1f} MW")
    
    # Return diagnostics
    diagnostics = {
        'authority': authority,
        'test_mape': mape,
        'train_mape': train_mape,
        'test_samples': len(test_df),
        'train_samples': len(train_df),
        'zero_values': zero_count,
        'near_zero_values': near_zero_count,
        'time_gaps': len(gaps),
        'negative_predictions': negative_preds,
        'pred_mean': pred_mean,
        'true_mean': true_mean,
        'pred_std': pred_std,
        'true_std': true_std,
        'mae': mae,
        'rmse': rmse,
        'train_end': train_end,
        'test_start': test_start,
        'forecast': test_forecast,
        'model': model
    }
    
    return diagnostics


def run_prophet_forecasts(output_dir=None):
    """Run Prophet forecasts for all authorities."""
    if output_dir is None:
        output_dir = Path("outputs")
    else:
        output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("\n" + "="*70)
    print("PROPHET FORECASTING - CALIFORNIA GRID DEMAND")
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
    all_forecasts = []
    diagnostics_list = []
    
    for authority in authorities:
        result = forecast_authority(df, authority, col_map)
        results.append({
            'authority': result['authority'],
            'test_mape': result['test_mape'],
            'train_mape': result['train_mape'],
            'test_samples': result['test_samples'],
            'train_samples': result['train_samples']
        })
        all_forecasts.append(result['forecast'])
        
        # Collect diagnostics
        diagnostics_list.append({
            'authority': result['authority'],
            'test_mape': result['test_mape'],
            'train_mape': result['train_mape'],
            'zero_values': result['zero_values'],
            'near_zero_values': result['near_zero_values'],
            'time_gaps': result['time_gaps'],
            'negative_predictions': result['negative_predictions'],
            'pred_mean': result['pred_mean'],
            'true_mean': result['true_mean'],
            'pred_std': result['pred_std'],
            'true_std': result['true_std'],
            'mae': result['mae'],
            'rmse': result['rmse'],
            'train_end': result['train_end'],
            'test_start': result['test_start']
        })
    
    # Create results summary
    results_df = pd.DataFrame(results)
    results_df = results_df.sort_values('test_mape')
    
    # Calculate overall metrics
    overall_mape = results_df['test_mape'].mean()
    
    print(f"\n{'='*70}")
    print("PROPHET RESULTS SUMMARY")
    print(f"{'='*70}\n")
    print(results_df.to_string(index=False))
    print(f"\n{'='*70}")
    print(f"Overall Test MAPE: {overall_mape:.2f}%")
    print(f"{'='*70}")
    
    # Save results
    results_path = output_dir / 'prophet_forecast_results.csv'
    results_df.to_csv(results_path, index=False)
    print(f"\n✓ Results saved to {results_path}")
    
    # Save all forecasts
    all_forecasts_df = pd.concat(all_forecasts, ignore_index=True)
    forecasts_path = output_dir / 'prophet_forecasts_detailed.csv'
    all_forecasts_df.to_csv(forecasts_path, index=False)
    print(f"✓ Detailed forecasts saved to {forecasts_path}")
    
    # Save diagnostics
    diagnostics_df = pd.DataFrame(diagnostics_list)
    diagnostics_path = output_dir / 'prophet_debug_summary.csv'
    diagnostics_df.to_csv(diagnostics_path, index=False)
    print(f"✓ Diagnostics saved to {diagnostics_path}")
    
    # Check if targets met
    print(f"\n{'='*70}")
    print("TARGET ACHIEVEMENT")
    print(f"{'='*70}")
    
    target_overall = 10.0
    target_ldwp = 15.0
    ldwp_mape = results_df[results_df['authority'] == 'LDWP']['test_mape'].values[0]
    
    print(f"\nOverall MAPE: {overall_mape:.2f}% (Target: <{target_overall}%)")
    if overall_mape < target_overall:
        print("  ✓ OVERALL TARGET MET")
    else:
        print(f"  ✗ Need {overall_mape - target_overall:.2f}% improvement")
    
    print(f"\nLDWP MAPE: {ldwp_mape:.2f}% (Target: <{target_ldwp}%)")
    if ldwp_mape < target_ldwp:
        print("  ✓ LDWP TARGET MET")
    else:
        print(f"  ✗ Need {ldwp_mape - target_ldwp:.2f}% improvement")
    
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
    
    print(f"\n{'Authority':<10} {'Baseline':<12} {'Prophet':<12} {'Improvement':<12}")
    print("-" * 50)
    
    for _, row in results_df.iterrows():
        auth = row['authority']
        prophet_mape = row['test_mape']
        baseline_mape = baseline_results.get(auth, 0)
        improvement = baseline_mape - prophet_mape
        improvement_pct = (improvement / baseline_mape * 100) if baseline_mape > 0 else 0
        
        print(f"{auth:<10} {baseline_mape:>6.2f}%     {prophet_mape:>6.2f}%     {improvement:>+6.2f}% ({improvement_pct:>+5.1f}%)")
    
    baseline_avg = np.mean(list(baseline_results.values()))
    improvement_overall = baseline_avg - overall_mape
    improvement_overall_pct = (improvement_overall / baseline_avg * 100)
    
    print("-" * 50)
    print(f"{'AVERAGE':<10} {baseline_avg:>6.2f}%     {overall_mape:>6.2f}%     {improvement_overall:>+6.2f}% ({improvement_overall_pct:>+5.1f}%)")
    print(f"{'='*70}\n")
    
    # Print diagnostic summary
    print(f"{'='*70}")
    print("DIAGNOSTIC SUMMARY")
    print(f"{'='*70}\n")
    
    diagnostics_df = pd.DataFrame(diagnostics_list)
    
    # Check for data quality issues
    print("Data Quality Issues:")
    for _, row in diagnostics_df.iterrows():
        issues = []
        if row['zero_values'] > 0:
            issues.append(f"{row['zero_values']} zero values")
        if row['near_zero_values'] > 10:
            issues.append(f"{row['near_zero_values']} near-zero values")
        if row['time_gaps'] > 0:
            issues.append(f"{row['time_gaps']} time gaps")
        if row['negative_predictions'] > 0:
            issues.append(f"{row['negative_predictions']} negative predictions (clipped)")
        
        if issues:
            print(f"  {row['authority']}: {', '.join(issues)}")
    
    # Check for prediction quality issues
    print("\nPrediction Quality:")
    for _, row in diagnostics_df.iterrows():
        mean_diff_pct = abs(row['pred_mean'] - row['true_mean']) / row['true_mean'] * 100
        std_diff_pct = abs(row['pred_std'] - row['true_std']) / row['true_std'] * 100
        
        issues = []
        if mean_diff_pct > 10:
            issues.append(f"mean off by {mean_diff_pct:.1f}%")
        if std_diff_pct > 20:
            issues.append(f"std off by {std_diff_pct:.1f}%")
        
        if issues:
            print(f"  {row['authority']}: {', '.join(issues)}")
    
    print(f"\n{'='*70}\n")
    
    return results_df, all_forecasts_df


if __name__ == "__main__":
    run_prophet_forecasts()
