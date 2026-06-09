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
    
    # Split train/test
    train_df, test_df = train_test_split_temporal(prophet_df, test_size=0.2)
    print(f"  Train samples: {len(train_df):,}")
    print(f"  Test samples: {len(test_df):,}")
    
    # Create and train model
    print(f"  Training Prophet model...")
    model = create_prophet_model(authority)
    model.fit(train_df)
    
    # Generate forecasts for test period
    future = model.make_future_dataframe(periods=len(test_df), freq='H')
    forecast = model.predict(future)
    
    # Extract test predictions
    test_forecast = forecast.iloc[-len(test_df):].copy()
    test_forecast['y_true'] = test_df['y'].values
    test_forecast['authority'] = authority
    
    # Calculate MAPE
    mape = calculate_mape(test_forecast['y_true'], test_forecast['yhat'])
    print(f"  Test MAPE: {mape:.2f}%")
    
    # Also calculate in-sample MAPE for comparison
    train_forecast = forecast.iloc[:len(train_df)].copy()
    train_forecast['y_true'] = train_df['y'].values
    train_mape = calculate_mape(train_forecast['y_true'], train_forecast['yhat'])
    print(f"  Train MAPE: {train_mape:.2f}%")
    
    return {
        'authority': authority,
        'test_mape': mape,
        'train_mape': train_mape,
        'test_samples': len(test_df),
        'train_samples': len(train_df),
        'forecast': test_forecast,
        'model': model
    }


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
    
    return results_df, all_forecasts_df


if __name__ == "__main__":
    run_prophet_forecasts()
