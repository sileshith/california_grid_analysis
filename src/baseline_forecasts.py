"""
Baseline forecasting models for California grid demand.

Implements:
- Naive forecast (24-hour lag)
- Moving average forecast (7-day window)
- MAPE calculation
"""

import pandas as pd
import numpy as np
from pathlib import Path


def calculate_mape(y_true, y_pred):
    """
    Calculate Mean Absolute Percentage Error.
    
    Args:
        y_true: Actual values
        y_pred: Predicted values
    
    Returns:
        MAPE as percentage
    """
    # Remove any NaN values
    mask = ~(np.isnan(y_true) | np.isnan(y_pred))
    y_true = y_true[mask]
    y_pred = y_pred[mask]
    
    # Avoid division by zero
    mask = y_true != 0
    y_true = y_true[mask]
    y_pred = y_pred[mask]
    
    if len(y_true) == 0:
        return np.nan
    
    return np.mean(np.abs((y_true - y_pred) / y_true)) * 100


def naive_forecast(df, target_col='demand_mw', lag_hours=24):
    """
    Naive forecast: use value from lag_hours ago.
    
    Args:
        df: DataFrame with datetime index and target column
        target_col: Column name to forecast
        lag_hours: Number of hours to lag (default 24 for day-ahead)
    
    Returns:
        Series with forecasted values
    """
    return df[target_col].shift(lag_hours)


def moving_average_forecast(df, target_col='demand_mw', window_days=7, lag_hours=24):
    """
    Moving average forecast: average of past window_days, lagged by lag_hours.
    
    Args:
        df: DataFrame with datetime index and target column
        target_col: Column name to forecast
        window_days: Number of days to average
        lag_hours: Number of hours to lag the window
    
    Returns:
        Series with forecasted values
    """
    window_hours = window_days * 24
    # Calculate rolling mean, then shift by lag_hours to avoid data leakage
    return df[target_col].shift(lag_hours).rolling(window=window_hours, min_periods=1).mean()


def evaluate_forecasts(df, target_col='demand_mw'):
    """
    Evaluate naive and moving average forecasts.
    
    Args:
        df: DataFrame with datetime index and target column
        target_col: Column name containing actual values
    
    Returns:
        Dictionary with MAPE scores
    """
    # Generate forecasts
    df = df.copy()
    df['naive_forecast'] = naive_forecast(df, target_col)
    df['ma_forecast'] = moving_average_forecast(df, target_col)
    
    # Calculate MAPE (skip first week to allow moving average to stabilize)
    skip_hours = 7 * 24
    df_eval = df.iloc[skip_hours:]
    
    naive_mape = calculate_mape(
        df_eval[target_col].values,
        df_eval['naive_forecast'].values
    )
    
    ma_mape = calculate_mape(
        df_eval[target_col].values,
        df_eval['ma_forecast'].values
    )
    
    return {
        'naive_mape': naive_mape,
        'ma_mape': ma_mape,
        'n_samples': len(df_eval)
    }


def run_baseline_forecasts(input_path=None):
    """
    Run baseline forecasts on California grid data.
    
    Args:
        input_path: Path to dashboard-ready CSV file
    
    Returns:
        DataFrame with results by authority
    """
    # Load data
    if input_path is None:
        input_path = Path('outputs/tableau_exports/dashboard_ready.csv')
    
    print(f"Loading data from {input_path}...")
    df = pd.read_csv(input_path)
    
    # Convert timestamp to datetime
    df['timestamp_utc'] = pd.to_datetime(df['timestamp_utc'])
    
    # Get unique authorities
    authorities = df['balancing_authority'].unique()
    print(f"Found {len(authorities)} balancing authorities: {', '.join(authorities)}")
    
    # Evaluate each authority
    results = []
    for authority in sorted(authorities):
        print(f"\nEvaluating {authority}...")
        
        # Filter to this authority and sort by time
        df_auth = df[df['balancing_authority'] == authority].copy()
        df_auth = df_auth.sort_values('timestamp_utc').set_index('timestamp_utc')
        
        # Evaluate forecasts
        metrics = evaluate_forecasts(df_auth, target_col='demand_mw')
        
        results.append({
            'balancing_authority': authority,
            'naive_mape': metrics['naive_mape'],
            'moving_avg_mape': metrics['ma_mape'],
            'n_samples': metrics['n_samples']
        })
        
        print(f"  Naive MAPE: {metrics['naive_mape']:.1f}%")
        print(f"  Moving Avg MAPE: {metrics['ma_mape']:.1f}%")
        print(f"  Samples evaluated: {metrics['n_samples']:,}")
    
    # Create results DataFrame
    results_df = pd.DataFrame(results)
    
    # Calculate average
    avg_row = pd.DataFrame([{
        'balancing_authority': 'AVERAGE',
        'naive_mape': results_df['naive_mape'].mean(),
        'moving_avg_mape': results_df['moving_avg_mape'].mean(),
        'n_samples': results_df['n_samples'].sum()
    }])
    results_df = pd.concat([results_df, avg_row], ignore_index=True)
    
    # Save results
    output_path = Path('outputs/baseline_forecast_results.csv')
    output_path.parent.mkdir(parents=True, exist_ok=True)
    results_df.to_csv(output_path, index=False)
    print(f"\n✅ Results saved to {output_path}")
    
    # Print summary table
    print("\n" + "="*60)
    print("BASELINE FORECAST RESULTS")
    print("="*60)
    print(f"{'Authority':<10} {'Naive MAPE':>12} {'Moving Avg MAPE':>18}")
    print("-"*60)
    for _, row in results_df.iterrows():
        auth = row['balancing_authority']
        naive = row['naive_mape']
        ma = row['moving_avg_mape']
        if auth == 'AVERAGE':
            print("-"*60)
        print(f"{auth:<10} {naive:>11.1f}% {ma:>17.1f}%")
    print("="*60)
    
    return results_df


if __name__ == '__main__':
    results = run_baseline_forecasts()
