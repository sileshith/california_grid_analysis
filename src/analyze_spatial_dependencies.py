"""
Spatial Dependency Analysis for California Balancing Authorities

Investigates spatial relationships and dependencies between balancing authorities:
- Pairwise demand correlations
- Lagged cross-correlations
- Temporal lead-lag relationships
- Granger causality tests

Goal: Determine whether graph-based modeling (GNN) is justified before implementation.

Outputs:
- outputs/spatial_correlation_matrix.csv
- outputs/spatial_dependency_report.md
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from scipy import stats
from itertools import combinations
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


def pivot_to_wide_format(df, col_map):
    """
    Pivot data to wide format with authorities as columns.
    
    Args:
        df: DataFrame with long format data
        col_map: Column name mapping
    
    Returns:
        DataFrame with timestamp index and authority columns
    """
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


def calculate_correlation_matrix(df_wide):
    """
    Calculate pairwise Pearson correlations between authorities.
    
    Args:
        df_wide: DataFrame with authorities as columns
    
    Returns:
        Correlation matrix DataFrame
    """
    corr_matrix = df_wide.corr(method='pearson')
    return corr_matrix


def calculate_lagged_correlations(df_wide, max_lag=24):
    """
    Calculate lagged cross-correlations between all authority pairs.
    
    Args:
        df_wide: DataFrame with authorities as columns
        max_lag: Maximum lag in hours to test
    
    Returns:
        DataFrame with lagged correlation results
    """
    authorities = df_wide.columns.tolist()
    results = []
    
    for auth1, auth2 in combinations(authorities, 2):
        series1 = df_wide[auth1].values
        series2 = df_wide[auth2].values
        
        # Calculate correlations at different lags
        lag_corrs = []
        for lag in range(-max_lag, max_lag + 1):
            if lag < 0:
                # auth2 leads auth1
                corr = np.corrcoef(series1[:lag], series2[-lag:])[0, 1]
            elif lag > 0:
                # auth1 leads auth2
                corr = np.corrcoef(series1[lag:], series2[:-lag])[0, 1]
            else:
                # No lag
                corr = np.corrcoef(series1, series2)[0, 1]
            
            lag_corrs.append(corr)
        
        # Find maximum correlation and its lag
        max_corr_idx = np.argmax(np.abs(lag_corrs))
        max_corr = lag_corrs[max_corr_idx]
        max_lag_value = max_corr_idx - max_lag
        
        results.append({
            'authority_1': auth1,
            'authority_2': auth2,
            'zero_lag_corr': lag_corrs[max_lag],  # Correlation at lag 0
            'max_corr': max_corr,
            'max_corr_lag': max_lag_value,
            'lead_authority': auth1 if max_lag_value > 0 else auth2 if max_lag_value < 0 else 'simultaneous'
        })
    
    return pd.DataFrame(results)


def granger_causality_test(series1, series2, max_lag=12):
    """
    Simple Granger causality test: does series1 help predict series2?
    
    Uses F-test comparing:
    - Restricted model: series2 ~ lag(series2)
    - Unrestricted model: series2 ~ lag(series2) + lag(series1)
    
    Args:
        series1: First time series (potential cause)
        series2: Second time series (effect)
        max_lag: Maximum lag to test
    
    Returns:
        Dictionary with test results
    """
    from sklearn.linear_model import LinearRegression
    
    # Prepare lagged features
    n = len(series1)
    X_restricted = []
    X_unrestricted = []
    y = []
    
    for i in range(max_lag, n):
        # Lags of series2 (always included)
        lags_series2 = [series2[i - lag] for lag in range(1, max_lag + 1)]
        
        # Lags of series1 (only in unrestricted model)
        lags_series1 = [series1[i - lag] for lag in range(1, max_lag + 1)]
        
        X_restricted.append(lags_series2)
        X_unrestricted.append(lags_series2 + lags_series1)
        y.append(series2[i])
    
    X_restricted = np.array(X_restricted)
    X_unrestricted = np.array(X_unrestricted)
    y = np.array(y)
    
    # Fit models
    model_restricted = LinearRegression().fit(X_restricted, y)
    model_unrestricted = LinearRegression().fit(X_unrestricted, y)
    
    # Calculate RSS (residual sum of squares)
    rss_restricted = np.sum((y - model_restricted.predict(X_restricted)) ** 2)
    rss_unrestricted = np.sum((y - model_unrestricted.predict(X_unrestricted)) ** 2)
    
    # F-test
    n_samples = len(y)
    n_restricted = X_restricted.shape[1]
    n_unrestricted = X_unrestricted.shape[1]
    
    f_stat = ((rss_restricted - rss_unrestricted) / (n_unrestricted - n_restricted)) / \
             (rss_unrestricted / (n_samples - n_unrestricted))
    
    # P-value from F-distribution
    from scipy.stats import f as f_dist
    p_value = 1 - f_dist.cdf(f_stat, n_unrestricted - n_restricted, n_samples - n_unrestricted)
    
    return {
        'f_stat': f_stat,
        'p_value': p_value,
        'significant': p_value < 0.05,
        'rss_improvement': (rss_restricted - rss_unrestricted) / rss_restricted * 100
    }


def analyze_granger_causality(df_wide, max_lag=12):
    """
    Test Granger causality between all authority pairs.
    
    Args:
        df_wide: DataFrame with authorities as columns
        max_lag: Maximum lag for Granger test
    
    Returns:
        DataFrame with Granger causality results
    """
    authorities = df_wide.columns.tolist()
    results = []
    
    print("\nTesting Granger causality (does X help predict Y?)...")
    
    for auth1 in authorities:
        for auth2 in authorities:
            if auth1 == auth2:
                continue
            
            series1 = df_wide[auth1].values
            series2 = df_wide[auth2].values
            
            test_result = granger_causality_test(series1, series2, max_lag=max_lag)
            
            results.append({
                'cause': auth1,
                'effect': auth2,
                'f_stat': test_result['f_stat'],
                'p_value': test_result['p_value'],
                'significant': test_result['significant'],
                'rss_improvement_pct': test_result['rss_improvement']
            })
    
    return pd.DataFrame(results)


def visualize_correlation_matrix(corr_matrix, output_dir):
    """Create heatmap of correlation matrix."""
    fig, ax = plt.subplots(figsize=(10, 8))
    
    sns.heatmap(
        corr_matrix,
        annot=True,
        fmt='.3f',
        cmap='RdBu_r',
        center=0,
        vmin=-1,
        vmax=1,
        square=True,
        linewidths=0.5,
        cbar_kws={'label': 'Pearson Correlation'},
        ax=ax
    )
    
    ax.set_title('Demand Correlation Matrix\nCalifornia Balancing Authorities', 
                fontsize=14, fontweight='bold', pad=20)
    
    plt.tight_layout()
    plt.savefig(output_dir / 'spatial_correlation_heatmap.png', dpi=150, bbox_inches='tight')
    plt.close()


def visualize_lagged_correlations(lagged_corr_df, output_dir):
    """Create visualization of lagged correlations."""
    # Sort by maximum correlation strength
    lagged_corr_df = lagged_corr_df.sort_values('max_corr', ascending=False)
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Create pair labels
    lagged_corr_df['pair'] = lagged_corr_df['authority_1'] + ' - ' + lagged_corr_df['authority_2']
    
    x = np.arange(len(lagged_corr_df))
    width = 0.35
    
    bars1 = ax.bar(x - width/2, lagged_corr_df['zero_lag_corr'], width,
                   label='Zero Lag', color='#3498db', alpha=0.8)
    bars2 = ax.bar(x + width/2, lagged_corr_df['max_corr'], width,
                   label='Max Correlation', color='#e74c3c', alpha=0.8)
    
    ax.set_ylabel('Correlation', fontsize=11)
    ax.set_xlabel('Authority Pair', fontsize=11)
    ax.set_title('Lagged Cross-Correlations Between Authorities', 
                fontsize=13, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(lagged_corr_df['pair'], rotation=45, ha='right')
    ax.legend(loc='upper right', fontsize=10)
    ax.grid(True, alpha=0.3, axis='y')
    ax.axhline(y=0, color='black', linewidth=0.5)
    
    plt.tight_layout()
    plt.savefig(output_dir / 'lagged_correlations.png', dpi=150, bbox_inches='tight')
    plt.close()


def visualize_granger_network(granger_df, output_dir):
    """Create network visualization of significant Granger causality relationships."""
    # Filter to significant relationships
    sig_granger = granger_df[granger_df['significant']].copy()
    
    if len(sig_granger) == 0:
        print("  No significant Granger causality relationships found.")
        return
    
    # Create adjacency matrix
    authorities = sorted(set(sig_granger['cause'].tolist() + sig_granger['effect'].tolist()))
    n = len(authorities)
    
    fig, ax = plt.subplots(figsize=(10, 10))
    
    # Create matrix for visualization
    matrix = np.zeros((n, n))
    for _, row in sig_granger.iterrows():
        i = authorities.index(row['cause'])
        j = authorities.index(row['effect'])
        matrix[i, j] = row['rss_improvement_pct']
    
    sns.heatmap(
        matrix,
        annot=True,
        fmt='.1f',
        cmap='YlOrRd',
        xticklabels=authorities,
        yticklabels=authorities,
        square=True,
        linewidths=0.5,
        cbar_kws={'label': 'RSS Improvement (%)'},
        ax=ax
    )
    
    ax.set_title('Granger Causality Network\n(Row → Column: Cause → Effect)', 
                fontsize=14, fontweight='bold', pad=20)
    ax.set_xlabel('Effect (Predicted)', fontsize=11)
    ax.set_ylabel('Cause (Predictor)', fontsize=11)
    
    plt.tight_layout()
    plt.savefig(output_dir / 'granger_causality_network.png', dpi=150, bbox_inches='tight')
    plt.close()


def generate_markdown_report(corr_matrix, lagged_corr_df, granger_df, output_dir):
    """Generate comprehensive markdown report."""
    report_path = output_dir / 'spatial_dependency_report.md'
    
    # Calculate summary statistics
    avg_corr = corr_matrix.values[np.triu_indices_from(corr_matrix.values, k=1)].mean()
    max_corr = corr_matrix.values[np.triu_indices_from(corr_matrix.values, k=1)].max()
    min_corr = corr_matrix.values[np.triu_indices_from(corr_matrix.values, k=1)].min()
    
    sig_granger = granger_df[granger_df['significant']]
    n_sig_relationships = len(sig_granger)
    total_tests = len(granger_df)
    
    with open(report_path, 'w') as f:
        f.write("# Spatial Dependency Analysis Report\n\n")
        f.write("**California Grid Balancing Authorities**\n\n")
        f.write(f"**Generated:** {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("---\n\n")
        
        f.write("## Executive Summary\n\n")
        f.write("This analysis investigates spatial dependencies and temporal relationships between ")
        f.write("California's five balancing authorities to determine whether graph-based modeling ")
        f.write("(e.g., Graph Neural Networks) is justified.\n\n")
        
        f.write("### Key Findings\n\n")
        f.write(f"- **Average Correlation:** {avg_corr:.3f}\n")
        f.write(f"- **Correlation Range:** {min_corr:.3f} to {max_corr:.3f}\n")
        f.write(f"- **Significant Granger Relationships:** {n_sig_relationships}/{total_tests} ")
        f.write(f"({100*n_sig_relationships/total_tests:.1f}%)\n\n")
        
        # Recommendation
        f.write("### Recommendation\n\n")
        if avg_corr > 0.7 and n_sig_relationships > 5:
            f.write("✅ **STRONG SPATIAL DEPENDENCIES DETECTED**\n\n")
            f.write("Graph-based modeling (GNN) is **JUSTIFIED** based on:\n")
            f.write(f"- High average correlation ({avg_corr:.3f})\n")
            f.write(f"- Multiple significant Granger causality relationships ({n_sig_relationships})\n")
            f.write("- Evidence of temporal lead-lag dynamics\n\n")
            f.write("**Next Step:** Implement Graph Neural Network for multi-authority forecasting.\n\n")
        elif avg_corr > 0.5 or n_sig_relationships > 3:
            f.write("⚠️ **MODERATE SPATIAL DEPENDENCIES DETECTED**\n\n")
            f.write("Graph-based modeling may provide marginal improvements:\n")
            f.write(f"- Moderate correlation ({avg_corr:.3f})\n")
            f.write(f"- Some Granger causality relationships ({n_sig_relationships})\n\n")
            f.write("**Recommendation:** Consider GNN if per-authority models underperform.\n\n")
        else:
            f.write("❌ **WEAK SPATIAL DEPENDENCIES**\n\n")
            f.write("Graph-based modeling is **NOT JUSTIFIED** based on:\n")
            f.write(f"- Low average correlation ({avg_corr:.3f})\n")
            f.write(f"- Few significant relationships ({n_sig_relationships})\n\n")
            f.write("**Recommendation:** Continue with per-authority models (LightGBM, Prophet).\n\n")
        
        f.write("---\n\n")
        
        f.write("## 1. Correlation Analysis\n\n")
        f.write("### Pairwise Pearson Correlations\n\n")
        f.write("Simultaneous (zero-lag) correlations between authority demand patterns:\n\n")
        f.write("```\n")
        f.write(corr_matrix.to_string())
        f.write("\n```\n\n")
        
        f.write("### Interpretation\n\n")
        f.write("- **High correlation (>0.8):** Strong synchronous demand patterns\n")
        f.write("- **Moderate correlation (0.5-0.8):** Some shared patterns\n")
        f.write("- **Low correlation (<0.5):** Independent demand dynamics\n\n")
        
        f.write("---\n\n")
        
        f.write("## 2. Lagged Cross-Correlation Analysis\n\n")
        f.write("Tests whether one authority's demand leads or lags another:\n\n")
        
        # Top 5 lagged correlations
        top_lagged = lagged_corr_df.nlargest(5, 'max_corr')
        f.write("### Top 5 Strongest Lagged Relationships\n\n")
        f.write("| Authority 1 | Authority 2 | Zero Lag | Max Corr | Lag (hours) | Lead Authority |\n")
        f.write("|-------------|-------------|----------|----------|-------------|----------------|\n")
        for _, row in top_lagged.iterrows():
            f.write(f"| {row['authority_1']} | {row['authority_2']} | ")
            f.write(f"{row['zero_lag_corr']:.3f} | {row['max_corr']:.3f} | ")
            f.write(f"{row['max_corr_lag']:+d} | {row['lead_authority']} |\n")
        f.write("\n")
        
        f.write("### Interpretation\n\n")
        f.write("- **Positive lag:** Authority 1 leads Authority 2\n")
        f.write("- **Negative lag:** Authority 2 leads Authority 1\n")
        f.write("- **Zero lag:** Simultaneous relationship\n\n")
        
        f.write("---\n\n")
        
        f.write("## 3. Granger Causality Analysis\n\n")
        f.write("Tests whether past values of one authority help predict another:\n\n")
        
        if n_sig_relationships > 0:
            f.write(f"### Significant Relationships (p < 0.05): {n_sig_relationships}\n\n")
            f.write("| Cause | Effect | F-Statistic | P-Value | RSS Improvement (%) |\n")
            f.write("|-------|--------|-------------|---------|---------------------|\n")
            
            sig_sorted = sig_granger.sort_values('rss_improvement_pct', ascending=False)
            for _, row in sig_sorted.iterrows():
                f.write(f"| {row['cause']} | {row['effect']} | ")
                f.write(f"{row['f_stat']:.2f} | {row['p_value']:.4f} | ")
                f.write(f"{row['rss_improvement_pct']:.2f}% |\n")
            f.write("\n")
            
            f.write("### Interpretation\n\n")
            f.write("- **RSS Improvement:** How much better the model predicts when including the cause\n")
            f.write("- **Significant relationships indicate predictive value across authorities**\n\n")
        else:
            f.write("**No significant Granger causality relationships found (p < 0.05)**\n\n")
            f.write("This suggests authorities operate independently for forecasting purposes.\n\n")
        
        f.write("---\n\n")
        
        f.write("## 4. Implications for Forecasting\n\n")
        
        f.write("### Current Approach (Per-Authority Models)\n\n")
        f.write("- ✅ LightGBM: 3.29% MAPE average\n")
        f.write("- ✅ Each authority modeled independently\n")
        f.write("- ✅ Simple, interpretable, production-ready\n\n")
        
        f.write("### Graph Neural Network Potential\n\n")
        if avg_corr > 0.7 and n_sig_relationships > 5:
            f.write("**HIGH POTENTIAL** - GNN could capture:\n")
            f.write("- Spatial dependencies between authorities\n")
            f.write("- Temporal lead-lag relationships\n")
            f.write("- Shared demand patterns\n\n")
            f.write("**Expected Improvement:** 10-30% MAPE reduction\n\n")
        elif avg_corr > 0.5 or n_sig_relationships > 3:
            f.write("**MODERATE POTENTIAL** - GNN might provide:\n")
            f.write("- Marginal improvements from weak dependencies\n")
            f.write("- Better handling of edge cases\n\n")
            f.write("**Expected Improvement:** 5-15% MAPE reduction\n\n")
        else:
            f.write("**LOW POTENTIAL** - GNN unlikely to improve:\n")
            f.write("- Weak spatial dependencies\n")
            f.write("- Authorities operate independently\n")
            f.write("- Added complexity not justified\n\n")
            f.write("**Expected Improvement:** <5% MAPE reduction\n\n")
        
        f.write("---\n\n")
        
        f.write("## 5. Recommendations\n\n")
        
        if avg_corr > 0.7 and n_sig_relationships > 5:
            f.write("### ✅ PROCEED WITH GNN IMPLEMENTATION\n\n")
            f.write("1. **Architecture:** Temporal Graph Convolutional Network (T-GCN)\n")
            f.write("2. **Graph Structure:** Use correlation matrix as adjacency weights\n")
            f.write("3. **Features:** Include lagged values from connected authorities\n")
            f.write("4. **Validation:** Compare against LightGBM baseline (3.29% MAPE)\n")
            f.write("5. **Target:** <3.0% MAPE with spatial modeling\n\n")
        elif avg_corr > 0.5 or n_sig_relationships > 3:
            f.write("### ⚠️ OPTIONAL: TEST GNN AS EXPERIMENT\n\n")
            f.write("1. **Quick prototype:** Simple GNN with 1-2 graph layers\n")
            f.write("2. **Compare:** GNN vs LightGBM on validation set\n")
            f.write("3. **Decision:** Only deploy if >10% improvement\n")
            f.write("4. **Fallback:** Continue with LightGBM if no improvement\n\n")
        else:
            f.write("### ❌ DO NOT IMPLEMENT GNN\n\n")
            f.write("1. **Weak dependencies:** Spatial modeling not justified\n")
            f.write("2. **Current performance:** LightGBM already excellent (3.29% MAPE)\n")
            f.write("3. **Recommendation:** Focus on per-authority improvements\n")
            f.write("4. **Alternative:** Investigate external features (weather, events)\n\n")
        
        f.write("---\n\n")
        
        f.write("## Appendix: Full Results\n\n")
        f.write("### Complete Lagged Correlation Table\n\n")
        f.write("```\n")
        f.write(lagged_corr_df.to_string(index=False))
        f.write("\n```\n\n")
        
        f.write("### Complete Granger Causality Results\n\n")
        f.write("```\n")
        f.write(granger_df.to_string(index=False))
        f.write("\n```\n\n")
    
    print(f"\n✓ Report saved to {report_path}")


def run_spatial_analysis(output_dir=None):
    """Run complete spatial dependency analysis."""
    if output_dir is None:
        output_dir = Path("outputs")
    else:
        output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("\n" + "="*70)
    print("SPATIAL DEPENDENCY ANALYSIS")
    print("="*70)
    print("\nLoading data...")
    
    df, col_map = load_dashboard_data()
    
    timestamp_col = col_map['timestamp']
    authority_col = col_map['authority']
    
    authorities = sorted(df[authority_col].unique())
    print(f"Authorities: {', '.join(authorities)}")
    print(f"Date range: {df[timestamp_col].min()} to {df[timestamp_col].max()}")
    
    # Pivot to wide format
    print("\nPivoting to wide format...")
    df_wide = pivot_to_wide_format(df, col_map)
    print(f"Samples: {len(df_wide):,}")
    
    # 1. Correlation analysis
    print("\n" + "="*60)
    print("1. CORRELATION ANALYSIS")
    print("="*60)
    corr_matrix = calculate_correlation_matrix(df_wide)
    print("\nPairwise Correlations:")
    print(corr_matrix)
    
    # Save correlation matrix
    corr_path = output_dir / 'spatial_correlation_matrix.csv'
    corr_matrix.to_csv(corr_path)
    print(f"\n✓ Correlation matrix saved to {corr_path}")
    
    # 2. Lagged correlation analysis
    print("\n" + "="*60)
    print("2. LAGGED CROSS-CORRELATION ANALYSIS")
    print("="*60)
    print("Testing lags from -24 to +24 hours...")
    lagged_corr_df = calculate_lagged_correlations(df_wide, max_lag=24)
    print("\nTop 5 strongest lagged relationships:")
    print(lagged_corr_df.nlargest(5, 'max_corr')[
        ['authority_1', 'authority_2', 'zero_lag_corr', 'max_corr', 'max_corr_lag', 'lead_authority']
    ].to_string(index=False))
    
    # Save lagged correlations
    lagged_path = output_dir / 'spatial_lagged_correlations.csv'
    lagged_corr_df.to_csv(lagged_path, index=False)
    print(f"\n✓ Lagged correlations saved to {lagged_path}")
    
    # 3. Granger causality analysis
    print("\n" + "="*60)
    print("3. GRANGER CAUSALITY ANALYSIS")
    print("="*60)
    granger_df = analyze_granger_causality(df_wide, max_lag=12)
    
    sig_granger = granger_df[granger_df['significant']]
    print(f"\nSignificant relationships (p < 0.05): {len(sig_granger)}/{len(granger_df)}")
    
    if len(sig_granger) > 0:
        print("\nTop 5 strongest Granger causality relationships:")
        print(sig_granger.nlargest(5, 'rss_improvement_pct')[
            ['cause', 'effect', 'f_stat', 'p_value', 'rss_improvement_pct']
        ].to_string(index=False))
    else:
        print("No significant Granger causality relationships found.")
    
    # Save Granger results
    granger_path = output_dir / 'spatial_granger_causality.csv'
    granger_df.to_csv(granger_path, index=False)
    print(f"\n✓ Granger causality results saved to {granger_path}")
    
    # 4. Generate visualizations
    print("\n" + "="*60)
    print("4. GENERATING VISUALIZATIONS")
    print("="*60)
    
    visualize_correlation_matrix(corr_matrix, output_dir)
    print("✓ Correlation heatmap saved")
    
    visualize_lagged_correlations(lagged_corr_df, output_dir)
    print("✓ Lagged correlations plot saved")
    
    visualize_granger_network(granger_df, output_dir)
    print("✓ Granger causality network saved")
    
    # 5. Generate markdown report
    print("\n" + "="*60)
    print("5. GENERATING REPORT")
    print("="*60)
    generate_markdown_report(corr_matrix, lagged_corr_df, granger_df, output_dir)
    
    # Summary
    print("\n" + "="*70)
    print("ANALYSIS COMPLETE")
    print("="*70)
    
    avg_corr = corr_matrix.values[np.triu_indices_from(corr_matrix.values, k=1)].mean()
    n_sig = len(sig_granger)
    
    print(f"\nAverage correlation: {avg_corr:.3f}")
    print(f"Significant Granger relationships: {n_sig}")
    
    print("\nRecommendation:")
    if avg_corr > 0.7 and n_sig > 5:
        print("✅ STRONG spatial dependencies - GNN implementation JUSTIFIED")
    elif avg_corr > 0.5 or n_sig > 3:
        print("⚠️  MODERATE spatial dependencies - GNN may provide marginal improvements")
    else:
        print("❌ WEAK spatial dependencies - Continue with per-authority models")
    
    print("\nOutputs:")
    print(f"  - {output_dir}/spatial_correlation_matrix.csv")
    print(f"  - {output_dir}/spatial_lagged_correlations.csv")
    print(f"  - {output_dir}/spatial_granger_causality.csv")
    print(f"  - {output_dir}/spatial_dependency_report.md")
    print(f"  - {output_dir}/spatial_correlation_heatmap.png")
    print(f"  - {output_dir}/lagged_correlations.png")
    print(f"  - {output_dir}/granger_causality_network.png")
    print("="*70 + "\n")


if __name__ == "__main__":
    run_spatial_analysis()
