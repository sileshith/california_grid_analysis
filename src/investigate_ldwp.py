"""
LDWP Data Quality Investigation

Analyzes LDWP demand patterns to understand why baseline forecast error
is 6.9x worse than CISO (32.76% vs 4.75% MAPE).

Checks:
- Missing values and data gaps
- Outliers and anomalies
- Demand volatility vs other authorities
- Temporal patterns and seasonality
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path


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
    
    # Convert timestamp to datetime
    df[timestamp_col] = pd.to_datetime(df[timestamp_col])
    
    return df, col_map


def analyze_missing_data(df, col_map):
    """Check for missing values and data gaps."""
    print("\n" + "="*60)
    print("MISSING DATA ANALYSIS")
    print("="*60)
    
    timestamp_col = col_map['timestamp']
    authority_col = col_map['authority']
    demand_col = col_map['demand']
    
    for authority in sorted(df[authority_col].unique()):
        auth_df = df[df[authority_col] == authority].copy()
        auth_df = auth_df.sort_values(timestamp_col)
        
        # Check for missing demand values
        missing_count = auth_df[demand_col].isna().sum()
        missing_pct = 100 * missing_count / len(auth_df)
        
        # Check for time gaps (should be hourly)
        auth_df['time_diff'] = auth_df[timestamp_col].diff()
        expected_diff = pd.Timedelta(hours=1)
        gaps = auth_df[auth_df['time_diff'] > expected_diff]
        
        print(f"\n{authority}:")
        print(f"  Missing values: {missing_count} ({missing_pct:.2f}%)")
        print(f"  Time gaps > 1 hour: {len(gaps)}")
        print(f"  Total samples: {len(auth_df)}")
        
        if len(gaps) > 0:
            print(f"  Largest gap: {gaps['time_diff'].max()}")


def analyze_outliers(df, col_map):
    """Detect outliers using IQR method."""
    print("\n" + "="*60)
    print("OUTLIER ANALYSIS")
    print("="*60)
    
    authority_col = col_map['authority']
    demand_col = col_map['demand']
    
    results = []
    
    for authority in sorted(df[authority_col].unique()):
        auth_df = df[df[authority_col] == authority].copy()
        demand = auth_df[demand_col].dropna()
        
        # IQR method
        Q1 = demand.quantile(0.25)
        Q3 = demand.quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 3 * IQR
        upper_bound = Q3 + 3 * IQR
        
        outliers = demand[(demand < lower_bound) | (demand > upper_bound)]
        outlier_pct = 100 * len(outliers) / len(demand)
        
        results.append({
            'authority': authority,
            'outlier_count': len(outliers),
            'outlier_pct': outlier_pct,
            'min': demand.min(),
            'max': demand.max(),
            'mean': demand.mean(),
            'std': demand.std()
        })
        
        print(f"\n{authority}:")
        print(f"  Outliers (3*IQR): {len(outliers)} ({outlier_pct:.2f}%)")
        print(f"  Range: {demand.min():.0f} - {demand.max():.0f} MW")
        print(f"  Mean ± Std: {demand.mean():.0f} ± {demand.std():.0f} MW")
    
    return pd.DataFrame(results)


def analyze_volatility(df, col_map):
    """Compare demand volatility across authorities."""
    print("\n" + "="*60)
    print("VOLATILITY ANALYSIS")
    print("="*60)
    
    timestamp_col = col_map['timestamp']
    authority_col = col_map['authority']
    demand_col = col_map['demand']
    
    results = []
    
    for authority in sorted(df[authority_col].unique()):
        auth_df = df[df[authority_col] == authority].copy()
        auth_df = auth_df.sort_values(timestamp_col)
        
        demand = auth_df[demand_col].dropna()
        
        # Calculate hour-to-hour changes
        hourly_change = demand.diff().dropna()
        hourly_change_pct = (demand.pct_change() * 100).dropna()
        
        # Calculate day-to-day changes (24h lag)
        daily_change = demand.diff(24).dropna()
        daily_change_pct = (demand.pct_change(24) * 100).dropna()
        
        # Coefficient of variation
        cv = demand.std() / demand.mean()
        
        results.append({
            'authority': authority,
            'cv': cv,
            'hourly_change_mean': hourly_change.abs().mean(),
            'hourly_change_std': hourly_change.std(),
            'hourly_change_pct_mean': hourly_change_pct.abs().mean(),
            'daily_change_mean': daily_change.abs().mean(),
            'daily_change_std': daily_change.std(),
            'daily_change_pct_mean': daily_change_pct.abs().mean()
        })
        
        print(f"\n{authority}:")
        print(f"  Coefficient of Variation: {cv:.4f}")
        print(f"  Mean hourly change: {hourly_change.abs().mean():.1f} MW ({hourly_change_pct.abs().mean():.2f}%)")
        print(f"  Mean daily change: {daily_change.abs().mean():.1f} MW ({daily_change_pct.abs().mean():.2f}%)")
    
    return pd.DataFrame(results)


def visualize_ldwp_patterns(df, output_dir=None):
    """Create visualizations comparing LDWP to other authorities."""
    if output_dir is None:
        output_dir = Path("outputs/monitoring")
    else:
        output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Time series comparison
    fig, axes = plt.subplots(5, 1, figsize=(14, 12), sharex=True)
    
    for idx, authority in enumerate(sorted(df['balancing_authority'].unique())):
        auth_df = df[df['balancing_authority'] == authority].copy()
        auth_df = auth_df.sort_values('timestamp_utc')
        
        axes[idx].plot(auth_df['timestamp_utc'], auth_df['demand_mw'], 
                      linewidth=0.5, alpha=0.7)
        axes[idx].set_ylabel('Demand (MW)', fontsize=10)
        axes[idx].set_title(f'{authority}', fontsize=11, fontweight='bold')
        axes[idx].grid(True, alpha=0.3)
        
        # Highlight LDWP
        if authority == 'LDWP':
            axes[idx].set_facecolor('#fff3cd')
    
    axes[-1].set_xlabel('Date', fontsize=10)
    plt.suptitle('Demand Patterns by Balancing Authority', fontsize=14, fontweight='bold', y=0.995)
    plt.tight_layout()
    plt.savefig(output_dir / 'ldwp_time_series_comparison.png', dpi=150, bbox_inches='tight')
    plt.close()
    
    # 2. Distribution comparison
    fig, ax = plt.subplots(figsize=(12, 6))
    
    for authority in sorted(df[authority_col].unique()):
        auth_df = df[df[authority_col] == authority]
        demand = auth_df[demand_col].dropna()
        
        # Normalize to 0-1 scale for comparison
        demand_norm = (demand - demand.min()) / (demand.max() - demand.min())
        
        color = '#ff6b6b' if authority == 'LDWP' else '#4ecdc4'
        linewidth = 2.5 if authority == 'LDWP' else 1.5
        alpha = 1.0 if authority == 'LDWP' else 0.6
        
        ax.hist(demand_norm, bins=50, alpha=alpha, label=authority, 
               color=color, linewidth=linewidth, histtype='step')
    
    ax.set_xlabel('Normalized Demand (0-1 scale)', fontsize=11)
    ax.set_ylabel('Frequency', fontsize=11)
    ax.set_title('Demand Distribution Comparison (Normalized)', fontsize=13, fontweight='bold')
    ax.legend(loc='upper right', fontsize=10)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_dir / 'ldwp_distribution_comparison.png', dpi=150, bbox_inches='tight')
    plt.close()
    
    # 3. Hourly patterns (average by hour of day)
    fig, ax = plt.subplots(figsize=(12, 6))
    
    for authority in sorted(df[authority_col].unique()):
        auth_df = df[df[authority_col] == authority].copy()
        auth_df['hour'] = pd.to_datetime(auth_df[timestamp_col]).dt.hour
        
        hourly_avg = auth_df.groupby('hour')[demand_col].mean()
        
        # Normalize
        hourly_avg_norm = (hourly_avg - hourly_avg.min()) / (hourly_avg.max() - hourly_avg.min())
        
        color = '#ff6b6b' if authority == 'LDWP' else '#4ecdc4'
        linewidth = 2.5 if authority == 'LDWP' else 1.5
        alpha = 1.0 if authority == 'LDWP' else 0.6
        
        ax.plot(hourly_avg_norm.index, hourly_avg_norm.values, 
               marker='o', label=authority, color=color, 
               linewidth=linewidth, alpha=alpha, markersize=4)
    
    ax.set_xlabel('Hour of Day', fontsize=11)
    ax.set_ylabel('Normalized Average Demand', fontsize=11)
    ax.set_title('Daily Demand Pattern by Authority (Normalized)', fontsize=13, fontweight='bold')
    ax.set_xticks(range(0, 24, 2))
    ax.legend(loc='upper right', fontsize=10)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_dir / 'ldwp_hourly_pattern_comparison.png', dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"\n✓ Visualizations saved to {output_dir}/")


def generate_summary_report(df, outlier_df, volatility_df, output_dir=None):
    """Generate a summary report of findings."""
    if output_dir is None:
        output_dir = Path("outputs/monitoring")
    else:
        output_dir = Path(output_dir)
    
    report_path = output_dir / 'ldwp_investigation_report.txt'
    
    with open(report_path, 'w') as f:
        f.write("="*70 + "\n")
        f.write("LDWP DATA QUALITY INVESTIGATION REPORT\n")
        f.write("="*70 + "\n\n")
        f.write(f"Generated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("EXECUTIVE SUMMARY\n")
        f.write("-"*70 + "\n")
        f.write("LDWP baseline forecast error is 32.76% MAPE, 6.9x worse than CISO (4.75%).\n")
        f.write("This investigation analyzes data quality and demand patterns to identify root causes.\n\n")
        
        f.write("KEY FINDINGS\n")
        f.write("-"*70 + "\n\n")
        
        # Outlier comparison
        ldwp_outliers = outlier_df[outlier_df['authority'] == 'LDWP'].iloc[0]
        ciso_outliers = outlier_df[outlier_df['authority'] == 'CISO'].iloc[0]
        
        f.write(f"1. OUTLIER RATE:\n")
        f.write(f"   LDWP: {ldwp_outliers['outlier_pct']:.2f}% outliers\n")
        f.write(f"   CISO: {ciso_outliers['outlier_pct']:.2f}% outliers\n")
        f.write(f"   Ratio: {ldwp_outliers['outlier_pct'] / ciso_outliers['outlier_pct']:.1f}x higher\n\n")
        
        # Volatility comparison
        ldwp_vol = volatility_df[volatility_df['authority'] == 'LDWP'].iloc[0]
        ciso_vol = volatility_df[volatility_df['authority'] == 'CISO'].iloc[0]
        
        f.write(f"2. DEMAND VOLATILITY:\n")
        f.write(f"   LDWP Coefficient of Variation: {ldwp_vol['cv']:.4f}\n")
        f.write(f"   CISO Coefficient of Variation: {ciso_vol['cv']:.4f}\n")
        f.write(f"   Ratio: {ldwp_vol['cv'] / ciso_vol['cv']:.2f}x more volatile\n\n")
        
        f.write(f"3. HOURLY CHANGES:\n")
        f.write(f"   LDWP: {ldwp_vol['hourly_change_pct_mean']:.2f}% average hourly change\n")
        f.write(f"   CISO: {ciso_vol['hourly_change_pct_mean']:.2f}% average hourly change\n")
        f.write(f"   Ratio: {ldwp_vol['hourly_change_pct_mean'] / ciso_vol['hourly_change_pct_mean']:.2f}x more volatile\n\n")
        
        f.write("RECOMMENDATIONS FOR PROPHET MODELING\n")
        f.write("-"*70 + "\n")
        f.write("1. Enable robust outlier detection (outlier handling in Prophet)\n")
        f.write("2. Increase changepoint flexibility (changepoint_prior_scale)\n")
        f.write("3. Add custom seasonality if daily pattern is weak\n")
        f.write("4. Consider separate model for LDWP with tuned hyperparameters\n")
        f.write("5. Investigate external factors (weather, events) for LDWP\n\n")
        
        f.write("DETAILED METRICS\n")
        f.write("-"*70 + "\n\n")
        f.write("Outlier Analysis:\n")
        f.write(outlier_df.to_string(index=False))
        f.write("\n\n")
        f.write("Volatility Analysis:\n")
        f.write(volatility_df.to_string(index=False))
        f.write("\n\n")
    
    print(f"\n✓ Summary report saved to {report_path}")


def run_investigation(output_dir=None):
    """Run complete LDWP investigation."""
    print("\n" + "="*70)
    print("LDWP DATA QUALITY INVESTIGATION")
    print("="*70)
    print("\nLoading data...")
    
    df, col_map = load_dashboard_data()
    
    timestamp_col = col_map['timestamp']
    authority_col = col_map['authority']
    
    print(f"\nDataset: {len(df):,} total samples")
    print(f"Authorities: {', '.join(sorted(df[authority_col].unique()))}")
    print(f"Date range: {df[timestamp_col].min()} to {df[timestamp_col].max()}")
    
    # Run analyses
    analyze_missing_data(df, col_map)
    outlier_df = analyze_outliers(df, col_map)
    volatility_df = analyze_volatility(df, col_map)
    
    # Generate visualizations
    print("\n" + "="*60)
    print("GENERATING VISUALIZATIONS")
    print("="*60)
    visualize_ldwp_patterns(df, col_map, output_dir)
    
    # Generate summary report
    generate_summary_report(df, outlier_df, volatility_df, output_dir)
    
    print("\n" + "="*70)
    print("INVESTIGATION COMPLETE")
    print("="*70)
    print("\nNext steps:")
    print("1. Review visualizations in outputs/monitoring/")
    print("2. Read summary report: outputs/monitoring/ldwp_investigation_report.txt")
    print("3. Implement Prophet with LDWP-specific tuning")
    print("="*70 + "\n")


if __name__ == "__main__":
    run_investigation()
