"""
Baseline forecasting models for California grid demand.

Implements:
- Naive forecast (24-hour lag)
- Moving average forecast (7-day window)
- MAPE calculation
"""

import argparse
import pandas as pd
import numpy as np
import sys
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


def run_baseline_forecasts(input_path=None, output_path=None):
    """
    Run baseline forecasts on California grid data.
    
    Args:
        input_path: Path to dashboard-ready CSV file
        output_path: Path to save results CSV file
    
    Returns:
        DataFrame with results by authority
    """
    # Load data
    if input_path is None:
        input_path = Path('outputs/tableau_exports/california_grid_dashboard_ready.csv')
    else:
        input_path = Path(input_path)
    
    if output_path is None:
        output_path = Path('outputs/baseline_forecast_results.csv')
    else:
        output_path = Path(output_path)
    
    # Check if file exists
    if not input_path.exists():
        print(f"❌ ERROR: Input file not found: {input_path}")
        print()
        print("This file should be created by running the main data pipeline.")
        print()
        
        # List available CSV files in outputs/
        outputs_dir = Path('outputs')
        if outputs_dir.exists():
            csv_files = list(outputs_dir.rglob('*.csv'))
            if csv_files:
                print(f"Found {len(csv_files)} CSV file(s) in outputs/:")
                for csv_file in sorted(csv_files):
                    size_kb = csv_file.stat().st_size / 1024
                    print(f"  - {csv_file} ({size_kb:.1f} KB)")
                print()
                print("To use a different file, run:")
                print(f"  python src/baseline_forecasts.py --input <path_to_csv>")
            else:
                print("No CSV files found in outputs/ directory.")
        else:
            print("outputs/ directory does not exist.")
        
        print()
        print("To generate the required file, run the data pipeline:")
        print("  python -m dags.california_grid_daily_pipeline")
        print()
        sys.exit(1)
    
    print(f"Loading data from {input_path}...")
    df = pd.read_csv(input_path)
    
    # Detect column names
    col_map = detect_column_names(df)
    timestamp_col = col_map['timestamp']
    authority_col = col_map['authority']
    demand_col = col_map['demand']
    
    print(f"Using columns: timestamp='{timestamp_col}', authority='{authority_col}', demand='{demand_col}'")
    
    # Convert timestamp to datetime
    df[timestamp_col] = pd.to_datetime(df[timestamp_col])
    
    # Get unique authorities
    authorities = df[authority_col].unique()
    print(f"Found {len(authorities)} balancing authorities: {', '.join(authorities)}")
    
    # Evaluate each authority
    results = []
    for authority in sorted(authorities):
        print(f"\nEvaluating {authority}...")
        
        # Filter to this authority and sort by time
        df_auth = df[df[authority_col] == authority].copy()
        df_auth = df_auth.sort_values(timestamp_col).set_index(timestamp_col)
        
        # Evaluate forecasts
        metrics = evaluate_forecasts(df_auth, target_col=demand_col)
        
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
    parser = argparse.ArgumentParser(
        description='Run baseline forecasts on California grid demand data'
    )
    parser.add_argument(
        '--input',
        type=str,
        default=None,
        help='Path to input CSV file (default: outputs/tableau_exports/california_grid_dashboard_ready.csv)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='Path to output results CSV file (default: outputs/baseline_forecast_results.csv)'
    )
    
    args = parser.parse_args()
    results = run_baseline_forecasts(input_path=args.input, output_path=args.output)
