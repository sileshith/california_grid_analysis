"""
Model Comparison Report

Compares baseline (naive, moving average) to Prophet forecasts.
Generates comprehensive comparison table and summary statistics.
"""

import pandas as pd
import numpy as np
from pathlib import Path


def load_baseline_results():
    """Load baseline forecast results."""
    baseline_path = Path("outputs/baseline_forecast_results.csv")
    if not baseline_path.exists():
        raise FileNotFoundError(f"Baseline results not found at {baseline_path}")
    return pd.read_csv(baseline_path)


def load_prophet_results():
    """Load Prophet forecast results."""
    prophet_path = Path("outputs/prophet_forecast_results.csv")
    if not prophet_path.exists():
        raise FileNotFoundError(f"Prophet results not found at {prophet_path}")
    return pd.read_csv(prophet_path)


def load_lightgbm_results():
    """Load LightGBM forecast results."""
    lightgbm_path = Path("outputs/lightgbm_forecast_results.csv")
    if not lightgbm_path.exists():
        return None  # LightGBM is optional
    return pd.read_csv(lightgbm_path)


def generate_comparison_table():
    """Generate comprehensive model comparison table."""
    print("\n" + "="*80)
    print("MODEL COMPARISON REPORT")
    print("="*80)
    
    # Load results
    baseline_df = load_baseline_results()
    prophet_df = load_prophet_results()
    lightgbm_df = load_lightgbm_results()
    
    # Standardize column names
    if 'balancing_authority' in baseline_df.columns:
        baseline_df = baseline_df.rename(columns={'balancing_authority': 'authority'})
    
    # Merge on authority
    comparison = baseline_df.merge(
        prophet_df[['authority', 'test_mape']], 
        on='authority',
        suffixes=('_baseline', '_prophet')
    )
    
    # Add LightGBM if available
    has_lightgbm = lightgbm_df is not None
    if has_lightgbm:
        comparison = comparison.merge(
            lightgbm_df[['authority', 'test_mape']],
            on='authority',
            how='left'
        )
        comparison = comparison.rename(columns={'test_mape': 'lightgbm_mape'})
    
    # Rename columns for clarity
    comparison = comparison.rename(columns={
        'naive_mape': 'naive_24h_mape',
        'moving_avg_mape': 'moving_avg_7d_mape',
        'test_mape': 'prophet_mape'
    })
    
    # Calculate improvements
    comparison['prophet_vs_naive'] = comparison['naive_24h_mape'] - comparison['prophet_mape']
    comparison['prophet_vs_naive_pct'] = (comparison['prophet_vs_naive'] / comparison['naive_24h_mape']) * 100
    
    comparison['prophet_vs_ma'] = comparison['moving_avg_7d_mape'] - comparison['prophet_mape']
    comparison['prophet_vs_ma_pct'] = (comparison['prophet_vs_ma'] / comparison['moving_avg_7d_mape']) * 100
    
    # Sort by Prophet performance
    comparison = comparison.sort_values('prophet_mape')
    
    # Display results
    print("\nFORECAST ACCURACY BY AUTHORITY (MAPE %)")
    print("-"*80)
    
    if has_lightgbm:
        print(f"{'Authority':<10} {'Naive 24h':<12} {'MA 7d':<12} {'Prophet':<12} {'LightGBM':<12} {'Best Model':<12}")
    else:
        print(f"{'Authority':<10} {'Naive 24h':<12} {'MA 7d':<12} {'Prophet':<12} {'Best Model':<12}")
    print("-"*80)
    
    for _, row in comparison.iterrows():
        auth = row['authority']
        naive = row['naive_24h_mape']
        ma = row['moving_avg_7d_mape']
        prophet = row['prophet_mape']
        
        if has_lightgbm:
            lgbm = row.get('lightgbm_mape', np.nan)
            if pd.notna(lgbm):
                best_mape = min(naive, ma, prophet, lgbm)
                if best_mape == lgbm:
                    best = "LightGBM"
                elif best_mape == prophet:
                    best = "Prophet"
                elif best_mape == naive:
                    best = "Naive 24h"
                else:
                    best = "MA 7d"
                print(f"{auth:<10} {naive:>6.2f}%      {ma:>6.2f}%      {prophet:>6.2f}%      {lgbm:>6.2f}%      {best:<12}")
            else:
                best_mape = min(naive, ma, prophet)
                if best_mape == prophet:
                    best = "Prophet"
                elif best_mape == naive:
                    best = "Naive 24h"
                else:
                    best = "MA 7d"
                print(f"{auth:<10} {naive:>6.2f}%      {ma:>6.2f}%      {prophet:>6.2f}%      {'N/A':<10}      {best:<12}")
        else:
            best_mape = min(naive, ma, prophet)
            if best_mape == prophet:
                best = "Prophet"
            elif best_mape == naive:
                best = "Naive 24h"
            else:
                best = "MA 7d"
            print(f"{auth:<10} {naive:>6.2f}%      {ma:>6.2f}%      {prophet:>6.2f}%      {best:<12}")
    
    # Calculate averages (exclude AVERAGE row if present)
    comparison_no_avg = comparison[comparison['authority'] != 'AVERAGE']
    avg_naive = comparison_no_avg['naive_24h_mape'].mean()
    avg_ma = comparison_no_avg['moving_avg_7d_mape'].mean()
    avg_prophet = comparison_no_avg['prophet_mape'].mean()
    
    if has_lightgbm:
        avg_lgbm = comparison_no_avg['lightgbm_mape'].mean()
        print("-"*80)
        print(f"{'AVERAGE':<10} {avg_naive:>6.2f}%      {avg_ma:>6.2f}%      {avg_prophet:>6.2f}%      {avg_lgbm:>6.2f}%")
    else:
        print("-"*80)
        print(f"{'AVERAGE':<10} {avg_naive:>6.2f}%      {avg_ma:>6.2f}%      {avg_prophet:>6.2f}%")
    print("="*80)
    
    # Improvement summary
    print("\nPROPHET IMPROVEMENT vs BASELINE")
    print("-"*80)
    print(f"{'Authority':<10} {'vs Naive 24h':<20} {'vs MA 7d':<20}")
    print("-"*80)
    
    for _, row in comparison_no_avg.iterrows():
        auth = row['authority']
        vs_naive = row['prophet_vs_naive']
        vs_naive_pct = row['prophet_vs_naive_pct']
        vs_ma = row['prophet_vs_ma']
        vs_ma_pct = row['prophet_vs_ma_pct']
        
        naive_str = f"{vs_naive:+.2f}% ({vs_naive_pct:+.0f}%)"
        ma_str = f"{vs_ma:+.2f}% ({vs_ma_pct:+.0f}%)"
        
        print(f"{auth:<10} {naive_str:<20} {ma_str:<20}")
    
    avg_vs_naive = avg_naive - avg_prophet
    avg_vs_naive_pct = (avg_vs_naive / avg_naive) * 100
    avg_vs_ma = avg_ma - avg_prophet
    avg_vs_ma_pct = (avg_vs_ma / avg_ma) * 100
    
    print("-"*80)
    print(f"{'AVERAGE':<10} {avg_vs_naive:+.2f}% ({avg_vs_naive_pct:+.0f}%)      {avg_vs_ma:+.2f}% ({avg_vs_ma_pct:+.0f}%)")
    print("="*80)
    
    # Key findings
    print("\nKEY FINDINGS")
    print("-"*80)
    
    # Best overall model
    if has_lightgbm:
        best_avg = min(avg_naive, avg_ma, avg_prophet, avg_lgbm)
        if best_avg == avg_lgbm:
            print(f"✓ LightGBM is the best overall model ({avg_lgbm:.2f}% MAPE)")
        elif best_avg == avg_prophet:
            print(f"✓ Prophet is the best overall model ({avg_prophet:.2f}% MAPE)")
        elif best_avg == avg_naive:
            print(f"✓ Naive 24h is the best overall model ({avg_naive:.2f}% MAPE)")
        else:
            print(f"✓ Moving Average 7d is the best overall model ({avg_ma:.2f}% MAPE)")
    else:
        if avg_prophet < avg_naive and avg_prophet < avg_ma:
            print(f"✓ Prophet is the best overall model ({avg_prophet:.2f}% MAPE)")
        elif avg_naive < avg_prophet and avg_naive < avg_ma:
            print(f"✓ Naive 24h is the best overall model ({avg_naive:.2f}% MAPE)")
        else:
            print(f"✓ Moving Average 7d is the best overall model ({avg_ma:.2f}% MAPE)")
    
    # Prophet vs Naive
    if avg_prophet < avg_naive:
        print(f"✓ Prophet outperforms Naive 24h by {avg_vs_naive:.2f}% ({avg_vs_naive_pct:.0f}% improvement)")
    else:
        print(f"✗ Prophet underperforms Naive 24h by {-avg_vs_naive:.2f}%")
    
    # LDWP specific
    ldwp_row = comparison_no_avg[comparison_no_avg['authority'] == 'LDWP'].iloc[0]
    ldwp_improvement = ldwp_row['prophet_vs_naive']
    ldwp_improvement_pct = ldwp_row['prophet_vs_naive_pct']
    
    if ldwp_improvement > 0:
        print(f"✓ LDWP: Prophet improved by {ldwp_improvement:.2f}% ({ldwp_improvement_pct:.0f}% improvement)")
    else:
        print(f"✗ LDWP: Prophet worse by {-ldwp_improvement:.2f}%")
    
    # Target achievement
    print("\nTARGET ACHIEVEMENT")
    print("-"*80)
    
    target_overall = 10.0
    target_ldwp = 15.0
    ldwp_mape = ldwp_row['prophet_mape']
    
    print(f"Overall MAPE: {avg_prophet:.2f}% (Target: <{target_overall}%)")
    if avg_prophet < target_overall:
        print("  ✓ OVERALL TARGET MET")
    else:
        print(f"  ✗ Need {avg_prophet - target_overall:.2f}% improvement")
    
    print(f"\nLDWP MAPE: {ldwp_mape:.2f}% (Target: <{target_ldwp}%)")
    if ldwp_mape < target_ldwp:
        print("  ✓ LDWP TARGET MET")
    else:
        print(f"  ✗ Need {ldwp_mape - target_ldwp:.2f}% improvement")
    
    print("="*80 + "\n")
    
    # Save comparison table
    output_path = Path("outputs/model_comparison.csv")
    comparison.to_csv(output_path, index=False)
    print(f"✓ Comparison table saved to {output_path}")
    
    # Save summary table
    summary_data = {
        'model': ['Naive 24h', 'Moving Avg 7d', 'Prophet'],
        'avg_mape': [avg_naive, avg_ma, avg_prophet]
    }
    
    if has_lightgbm:
        summary_data['model'].append('LightGBM')
        summary_data['avg_mape'].append(avg_lgbm)
    
    summary_df = pd.DataFrame(summary_data)
    summary_df = summary_df.sort_values('avg_mape')
    
    summary_path = Path("outputs/model_comparison_summary.csv")
    summary_df.to_csv(summary_path, index=False)
    print(f"✓ Summary table saved to {summary_path}\n")
    
    return comparison


if __name__ == "__main__":
    generate_comparison_table()
