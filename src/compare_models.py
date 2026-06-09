"""
Model Comparison Report

Compares baseline (naive, moving average), Prophet, and LightGBM forecasts.
Generates comprehensive comparison table with multiple metrics:
- MAPE (Mean Absolute Percentage Error)
- SMAPE (Symmetric Mean Absolute Percentage Error)
- MAE (Mean Absolute Error)
- RMSE (Root Mean Squared Error)
- Median Percentage Error

Includes adjusted LDWP evaluation for demand >= 250 MW.
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


def load_ldwp_error_analysis():
    """Load LDWP error analysis for adjusted metrics."""
    ldwp_path = Path("outputs/ldwp_error_analysis.csv")
    if not ldwp_path.exists():
        return None
    return pd.read_csv(ldwp_path)


def generate_comparison_table():
    """Generate comprehensive model comparison table."""
    print("\n" + "="*80)
    print("MODEL COMPARISON REPORT - COMPREHENSIVE METRICS")
    print("="*80)
    
    # Load results
    baseline_df = load_baseline_results()
    prophet_df = load_prophet_results()
    lightgbm_df = load_lightgbm_results()
    ldwp_error_df = load_ldwp_error_analysis()
    
    # Standardize column names
    if 'balancing_authority' in baseline_df.columns:
        baseline_df = baseline_df.rename(columns={'balancing_authority': 'authority'})
    
    # Merge on authority - start with baseline
    comparison = baseline_df.copy()
    
    # Add Prophet metrics
    if 'authority' in prophet_df.columns:
        prophet_cols = ['authority', 'test_mape']
        comparison = comparison.merge(
            prophet_df[prophet_cols], 
            on='authority',
            how='left',
            suffixes=('', '_prophet')
        )
        comparison = comparison.rename(columns={'test_mape': 'prophet_mape'})
    
    # Add LightGBM metrics if available
    has_lightgbm = lightgbm_df is not None
    if has_lightgbm:
        lgbm_cols = ['authority', 'test_mape', 'test_smape', 'test_mae', 'test_rmse']
        available_cols = ['authority'] + [col for col in lgbm_cols[1:] if col in lightgbm_df.columns]
        comparison = comparison.merge(
            lightgbm_df[available_cols],
            on='authority',
            how='left',
            suffixes=('', '_lgbm')
        )
        comparison = comparison.rename(columns={
            'test_mape': 'lightgbm_mape',
            'test_smape': 'lightgbm_smape',
            'test_mae': 'lightgbm_mae',
            'test_rmse': 'lightgbm_rmse'
        })
    
    # Rename baseline columns for clarity
    comparison = comparison.rename(columns={
        'naive_mape': 'naive_24h_mape',
        'moving_avg_mape': 'moving_avg_7d_mape'
    })
    
    # Calculate adjusted LDWP metrics (demand >= 250 MW)
    if has_lightgbm and ldwp_error_df is not None:
        ldwp_high_demand = ldwp_error_df[ldwp_error_df['actual'] >= 250].copy()
        if len(ldwp_high_demand) > 0:
            # Calculate MAPE for high demand
            ldwp_high_mape = np.mean(np.abs(ldwp_high_demand['pct_error']))
            
            # Calculate median percentage error
            ldwp_median_pct_error = ldwp_high_demand['pct_error'].median()
            
            # Add to comparison table
            ldwp_idx = comparison[comparison['authority'] == 'LDWP'].index
            if len(ldwp_idx) > 0:
                comparison.loc[ldwp_idx, 'lightgbm_mape_high_demand'] = ldwp_high_mape
                comparison.loc[ldwp_idx, 'lightgbm_median_pct_error'] = ldwp_median_pct_error
                comparison.loc[ldwp_idx, 'high_demand_samples'] = len(ldwp_high_demand)
    
    # Calculate improvements
    comparison['prophet_vs_naive'] = comparison['naive_24h_mape'] - comparison['prophet_mape']
    comparison['prophet_vs_naive_pct'] = (comparison['prophet_vs_naive'] / comparison['naive_24h_mape']) * 100
    
    comparison['prophet_vs_ma'] = comparison['moving_avg_7d_mape'] - comparison['prophet_mape']
    comparison['prophet_vs_ma_pct'] = (comparison['prophet_vs_ma'] / comparison['moving_avg_7d_mape']) * 100
    
    # Sort by Prophet performance
    comparison = comparison.sort_values('prophet_mape')
    
    # Display MAPE results
    print("\n1. MAPE COMPARISON (Mean Absolute Percentage Error)")
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
        prophet = row.get('prophet_mape', np.nan)
        
        if has_lightgbm:
            lgbm = row.get('lightgbm_mape', np.nan)
            if pd.notna(lgbm) and pd.notna(prophet):
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
                best_mape = min(naive, ma, prophet) if pd.notna(prophet) else min(naive, ma)
                if pd.notna(prophet) and best_mape == prophet:
                    best = "Prophet"
                elif best_mape == naive:
                    best = "Naive 24h"
                else:
                    best = "MA 7d"
                lgbm_str = f"{lgbm:>6.2f}%" if pd.notna(lgbm) else "N/A"
                print(f"{auth:<10} {naive:>6.2f}%      {ma:>6.2f}%      {prophet:>6.2f}%      {lgbm_str:<10}      {best:<12}")
        else:
            best_mape = min(naive, ma, prophet) if pd.notna(prophet) else min(naive, ma)
            if pd.notna(prophet) and best_mape == prophet:
                best = "Prophet"
            elif best_mape == naive:
                best = "Naive 24h"
            else:
                best = "MA 7d"
            prophet_str = f"{prophet:>6.2f}%" if pd.notna(prophet) else "N/A"
            print(f"{auth:<10} {naive:>6.2f}%      {ma:>6.2f}%      {prophet_str:<10}      {best:<12}")
    
    # Calculate averages (exclude AVERAGE row if present)
    comparison_no_avg = comparison[comparison['authority'] != 'AVERAGE'].copy()
    avg_naive = comparison_no_avg['naive_24h_mape'].mean()
    avg_ma = comparison_no_avg['moving_avg_7d_mape'].mean()
    avg_prophet = comparison_no_avg['prophet_mape'].mean() if 'prophet_mape' in comparison_no_avg.columns else np.nan
    
    if has_lightgbm:
        avg_lgbm = comparison_no_avg['lightgbm_mape'].mean()
        print("-"*80)
        if pd.notna(avg_prophet):
            print(f"{'AVERAGE':<10} {avg_naive:>6.2f}%      {avg_ma:>6.2f}%      {avg_prophet:>6.2f}%      {avg_lgbm:>6.2f}%")
        else:
            print(f"{'AVERAGE':<10} {avg_naive:>6.2f}%      {avg_ma:>6.2f}%      {'N/A':<10}      {avg_lgbm:>6.2f}%")
    else:
        print("-"*80)
        if pd.notna(avg_prophet):
            print(f"{'AVERAGE':<10} {avg_naive:>6.2f}%      {avg_ma:>6.2f}%      {avg_prophet:>6.2f}%")
        else:
            print(f"{'AVERAGE':<10} {avg_naive:>6.2f}%      {avg_ma:>6.2f}%      {'N/A':<10}")
    print("="*80)
    
    # Display additional LightGBM metrics if available
    if has_lightgbm and 'lightgbm_smape' in comparison.columns:
        print("\n2. ADDITIONAL LIGHTGBM METRICS")
        print("-"*80)
        print(f"{'Authority':<10} {'SMAPE':<12} {'MAE (MW)':<12} {'RMSE (MW)':<12}")
        print("-"*80)
        
        for _, row in comparison_no_avg.iterrows():
            auth = row['authority']
            smape = row.get('lightgbm_smape', np.nan)
            mae = row.get('lightgbm_mae', np.nan)
            rmse = row.get('lightgbm_rmse', np.nan)
            
            smape_str = f"{smape:>6.2f}%" if pd.notna(smape) else "N/A"
            mae_str = f"{mae:>8.1f}" if pd.notna(mae) else "N/A"
            rmse_str = f"{rmse:>8.1f}" if pd.notna(rmse) else "N/A"
            
            print(f"{auth:<10} {smape_str:<12} {mae_str:<12} {rmse_str:<12}")
        
        # Averages
        avg_smape = comparison_no_avg['lightgbm_smape'].mean() if 'lightgbm_smape' in comparison_no_avg.columns else np.nan
        avg_mae = comparison_no_avg['lightgbm_mae'].mean() if 'lightgbm_mae' in comparison_no_avg.columns else np.nan
        avg_rmse = comparison_no_avg['lightgbm_rmse'].mean() if 'lightgbm_rmse' in comparison_no_avg.columns else np.nan
        
        print("-"*80)
        smape_str = f"{avg_smape:>6.2f}%" if pd.notna(avg_smape) else "N/A"
        mae_str = f"{avg_mae:>8.1f}" if pd.notna(avg_mae) else "N/A"
        rmse_str = f"{avg_rmse:>8.1f}" if pd.notna(avg_rmse) else "N/A"
        print(f"{'AVERAGE':<10} {smape_str:<12} {mae_str:<12} {rmse_str:<12}")
        print("="*80)
    
    # Display adjusted LDWP metrics
    if has_lightgbm and 'lightgbm_mape_high_demand' in comparison.columns:
        ldwp_row = comparison[comparison['authority'] == 'LDWP']
        if len(ldwp_row) > 0:
            ldwp_row = ldwp_row.iloc[0]
            print("\n3. ADJUSTED LDWP EVALUATION (Demand >= 250 MW)")
            print("-"*80)
            print(f"Standard MAPE (all samples):     {ldwp_row['lightgbm_mape']:.2f}%")
            print(f"Adjusted MAPE (>= 250 MW):       {ldwp_row['lightgbm_mape_high_demand']:.2f}%")
            print(f"Median Percentage Error:         {ldwp_row['lightgbm_median_pct_error']:.2f}%")
            print(f"High demand samples:             {int(ldwp_row['high_demand_samples'])}")
            print(f"SMAPE (robust metric):           {ldwp_row.get('lightgbm_smape', np.nan):.2f}%")
            print("-"*80)
            print("Note: Standard MAPE is inflated by low demand values (<250 MW).")
            print("      Adjusted MAPE and SMAPE provide more realistic performance assessment.")
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
    
    # Best overall model by MAPE
    if has_lightgbm and pd.notna(avg_prophet):
        best_avg = min(avg_naive, avg_ma, avg_prophet, avg_lgbm)
        if best_avg == avg_lgbm:
            print(f"✓ LightGBM is the best overall model by MAPE ({avg_lgbm:.2f}%)")
            improvement_vs_naive = ((avg_naive - avg_lgbm) / avg_naive) * 100
            print(f"  - {improvement_vs_naive:.1f}% better than Naive 24h baseline")
            
            # Check if LightGBM wins on most authorities
            lgbm_wins = 0
            for _, row in comparison_no_avg.iterrows():
                models = [row['naive_24h_mape'], row['moving_avg_7d_mape']]
                if pd.notna(row.get('prophet_mape')):
                    models.append(row['prophet_mape'])
                if pd.notna(row.get('lightgbm_mape')):
                    models.append(row['lightgbm_mape'])
                    if row['lightgbm_mape'] == min(models):
                        lgbm_wins += 1
            
            print(f"  - Best model for {lgbm_wins}/{len(comparison_no_avg)} authorities")
            
            if 'lightgbm_smape' in comparison_no_avg.columns:
                print(f"  - Average SMAPE: {avg_smape:.2f}% (robust to low demand values)")
            
        elif best_avg == avg_prophet:
            print(f"✓ Prophet is the best overall model ({avg_prophet:.2f}% MAPE)")
        elif best_avg == avg_naive:
            print(f"✓ Naive 24h is the best overall model ({avg_naive:.2f}% MAPE)")
        else:
            print(f"✓ Moving Average 7d is the best overall model ({avg_ma:.2f}% MAPE)")
    elif pd.notna(avg_prophet):
        if avg_prophet < avg_naive and avg_prophet < avg_ma:
            print(f"✓ Prophet is the best overall model ({avg_prophet:.2f}% MAPE)")
        elif avg_naive < avg_prophet and avg_naive < avg_ma:
            print(f"✓ Naive 24h is the best overall model ({avg_naive:.2f}% MAPE)")
        else:
            print(f"✓ Moving Average 7d is the best overall model ({avg_ma:.2f}% MAPE)")
    else:
        if avg_naive < avg_ma:
            print(f"✓ Naive 24h is the best overall model ({avg_naive:.2f}% MAPE)")
        else:
            print(f"✓ Moving Average 7d is the best overall model ({avg_ma:.2f}% MAPE)")
    
    # LightGBM vs Naive
    if has_lightgbm:
        lgbm_vs_naive = avg_naive - avg_lgbm
        lgbm_vs_naive_pct = (lgbm_vs_naive / avg_naive) * 100
        print(f"✓ LightGBM outperforms Naive 24h by {lgbm_vs_naive:.2f}% ({lgbm_vs_naive_pct:.0f}% improvement)")
    
    # Prophet vs Naive (if available)
    if pd.notna(avg_prophet):
        avg_vs_naive = avg_naive - avg_prophet
        avg_vs_naive_pct = (avg_vs_naive / avg_naive) * 100
        if avg_prophet < avg_naive:
            print(f"✓ Prophet outperforms Naive 24h by {avg_vs_naive:.2f}% ({avg_vs_naive_pct:.0f}% improvement)")
        else:
            print(f"✗ Prophet underperforms Naive 24h by {-avg_vs_naive:.2f}%")
    
    # LDWP specific analysis
    ldwp_rows = comparison_no_avg[comparison_no_avg['authority'] == 'LDWP']
    if len(ldwp_rows) > 0:
        ldwp_row = ldwp_rows.iloc[0]
        
        print(f"\nLDWP Analysis:")
        if has_lightgbm:
            ldwp_lgbm = ldwp_row.get('lightgbm_mape', np.nan)
            ldwp_naive = ldwp_row['naive_24h_mape']
            if pd.notna(ldwp_lgbm):
                ldwp_improvement = ldwp_naive - ldwp_lgbm
                ldwp_improvement_pct = (ldwp_improvement / ldwp_naive) * 100
                print(f"  - LightGBM MAPE: {ldwp_lgbm:.2f}% (baseline: {ldwp_naive:.2f}%)")
                print(f"  - Improvement: {ldwp_improvement:.2f}% ({ldwp_improvement_pct:.0f}%)")
                
                if 'lightgbm_mape_high_demand' in ldwp_row and pd.notna(ldwp_row['lightgbm_mape_high_demand']):
                    print(f"  - Adjusted MAPE (>= 250 MW): {ldwp_row['lightgbm_mape_high_demand']:.2f}%")
                    print(f"  - Note: Standard MAPE inflated by low demand values")
    
    # Target achievement
    print("\nTARGET ACHIEVEMENT")
    print("-"*80)
    
    target_overall = 10.0
    target_ldwp = 15.0
    
    if has_lightgbm:
        print(f"Overall MAPE (LightGBM): {avg_lgbm:.2f}% (Target: <{target_overall}%)")
        if avg_lgbm < target_overall:
            print("  ✓ OVERALL TARGET MET")
        else:
            print(f"  ✗ Need {avg_lgbm - target_overall:.2f}% improvement")
        
        if len(ldwp_rows) > 0:
            ldwp_mape = ldwp_row.get('lightgbm_mape', np.nan)
            if pd.notna(ldwp_mape):
                print(f"\nLDWP MAPE (LightGBM): {ldwp_mape:.2f}% (Target: <{target_ldwp}%)")
                if ldwp_mape < target_ldwp:
                    print("  ✓ LDWP TARGET MET")
                else:
                    print(f"  ✗ Need {ldwp_mape - target_ldwp:.2f}% improvement")
                    if 'lightgbm_mape_high_demand' in ldwp_row and pd.notna(ldwp_row['lightgbm_mape_high_demand']):
                        adj_mape = ldwp_row['lightgbm_mape_high_demand']
                        print(f"  Note: Adjusted MAPE (>= 250 MW) is {adj_mape:.2f}%")
    elif pd.notna(avg_prophet):
        print(f"Overall MAPE (Prophet): {avg_prophet:.2f}% (Target: <{target_overall}%)")
        if avg_prophet < target_overall:
            print("  ✓ OVERALL TARGET MET")
        else:
            print(f"  ✗ Need {avg_prophet - target_overall:.2f}% improvement")
    
    print("="*80 + "\n")
    
    # Save detailed comparison table
    output_path = Path("outputs/model_comparison.csv")
    comparison.to_csv(output_path, index=False)
    print(f"✓ Detailed comparison saved to {output_path}")
    
    # Save summary table with all metrics
    summary_data = {
        'model': ['Naive 24h', 'Moving Avg 7d'],
        'avg_mape': [avg_naive, avg_ma],
        'avg_smape': [np.nan, np.nan],
        'avg_mae': [np.nan, np.nan],
        'avg_rmse': [np.nan, np.nan]
    }
    
    if pd.notna(avg_prophet):
        summary_data['model'].append('Prophet')
        summary_data['avg_mape'].append(avg_prophet)
        summary_data['avg_smape'].append(np.nan)
        summary_data['avg_mae'].append(np.nan)
        summary_data['avg_rmse'].append(np.nan)
    
    if has_lightgbm:
        summary_data['model'].append('LightGBM')
        summary_data['avg_mape'].append(avg_lgbm)
        summary_data['avg_smape'].append(avg_smape if pd.notna(avg_smape) else np.nan)
        summary_data['avg_mae'].append(avg_mae if pd.notna(avg_mae) else np.nan)
        summary_data['avg_rmse'].append(avg_rmse if pd.notna(avg_rmse) else np.nan)
    
    summary_df = pd.DataFrame(summary_data)
    summary_df = summary_df.sort_values('avg_mape')
    
    # Add rank column
    summary_df['rank'] = range(1, len(summary_df) + 1)
    
    # Reorder columns
    summary_df = summary_df[['rank', 'model', 'avg_mape', 'avg_smape', 'avg_mae', 'avg_rmse']]
    
    summary_path = Path("outputs/model_comparison_summary.csv")
    summary_df.to_csv(summary_path, index=False)
    print(f"✓ Summary table saved to {summary_path}")
    
    # Print summary table
    print("\n" + "="*80)
    print("MODEL RANKING SUMMARY")
    print("="*80)
    print(summary_df.to_string(index=False))
    print("="*80 + "\n")
    
    return comparison


if __name__ == "__main__":
    generate_comparison_table()
