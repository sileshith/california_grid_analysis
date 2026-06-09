"""
Forecast Visualization

Creates plots comparing Prophet forecasts to actual values.
Focuses on LDWP error analysis and model performance visualization.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

sns.set_style("whitegrid")


def load_forecast_data():
    """Load Prophet forecast results."""
    forecast_path = Path("outputs/prophet_forecasts_detailed.csv")
    if not forecast_path.exists():
        raise FileNotFoundError(f"Forecast data not found at {forecast_path}")
    
    df = pd.read_csv(forecast_path)
    df['ds'] = pd.to_datetime(df['ds'])
    return df


def plot_forecast_vs_actual(df, authority, output_dir=None):
    """Plot forecast vs actual for one authority."""
    if output_dir is None:
        output_dir = Path("outputs/monitoring")
    else:
        output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    auth_df = df[df['authority'] == authority].copy()
    auth_df = auth_df.sort_values('ds')
    
    # Calculate error
    auth_df['error'] = auth_df['y_true'] - auth_df['yhat']
    auth_df['error_pct'] = (auth_df['error'] / auth_df['y_true']) * 100
    
    # Create figure with subplots
    fig, axes = plt.subplots(3, 1, figsize=(14, 10))
    
    # 1. Forecast vs Actual
    axes[0].plot(auth_df['ds'], auth_df['y_true'], 
                label='Actual', color='#2c3e50', linewidth=1.5, alpha=0.8)
    axes[0].plot(auth_df['ds'], auth_df['yhat'], 
                label='Prophet Forecast', color='#e74c3c', linewidth=1.5, alpha=0.8)
    axes[0].fill_between(auth_df['ds'], 
                         auth_df['yhat_lower'], 
                         auth_df['yhat_upper'],
                         alpha=0.2, color='#e74c3c', label='95% Confidence')
    axes[0].set_ylabel('Demand (MW)', fontsize=11)
    axes[0].set_title(f'{authority} - Prophet Forecast vs Actual', 
                     fontsize=13, fontweight='bold')
    axes[0].legend(loc='upper right', fontsize=10)
    axes[0].grid(True, alpha=0.3)
    
    # 2. Absolute Error
    axes[1].plot(auth_df['ds'], auth_df['error'].abs(), 
                color='#e67e22', linewidth=1.0, alpha=0.7)
    axes[1].axhline(y=auth_df['error'].abs().mean(), 
                   color='#c0392b', linestyle='--', linewidth=2, 
                   label=f'Mean: {auth_df["error"].abs().mean():.1f} MW')
    axes[1].set_ylabel('Absolute Error (MW)', fontsize=11)
    axes[1].set_title('Forecast Error Over Time', fontsize=12, fontweight='bold')
    axes[1].legend(loc='upper right', fontsize=10)
    axes[1].grid(True, alpha=0.3)
    
    # 3. Percentage Error
    axes[2].plot(auth_df['ds'], auth_df['error_pct'], 
                color='#9b59b6', linewidth=1.0, alpha=0.7)
    axes[2].axhline(y=0, color='black', linestyle='-', linewidth=0.5)
    axes[2].axhline(y=auth_df['error_pct'].mean(), 
                   color='#8e44ad', linestyle='--', linewidth=2,
                   label=f'Mean: {auth_df["error_pct"].mean():.2f}%')
    axes[2].set_ylabel('Error (%)', fontsize=11)
    axes[2].set_xlabel('Date', fontsize=11)
    axes[2].set_title('Percentage Error Over Time', fontsize=12, fontweight='bold')
    axes[2].legend(loc='upper right', fontsize=10)
    axes[2].grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    filename = f'prophet_forecast_{authority.lower()}.png'
    plt.savefig(output_dir / filename, dpi=150, bbox_inches='tight')
    plt.close()
    
    return output_dir / filename


def plot_error_distribution(df, output_dir=None):
    """Plot error distribution comparison across authorities."""
    if output_dir is None:
        output_dir = Path("outputs/monitoring")
    else:
        output_dir = Path(output_dir)
    
    fig, axes = plt.subplots(2, 1, figsize=(12, 8))
    
    # 1. Error distribution by authority
    authorities = sorted(df['authority'].unique())
    
    for authority in authorities:
        auth_df = df[df['authority'] == authority].copy()
        auth_df['error_pct'] = ((auth_df['y_true'] - auth_df['yhat']) / auth_df['y_true']) * 100
        
        color = '#e74c3c' if authority == 'LDWP' else '#3498db'
        linewidth = 2.5 if authority == 'LDWP' else 1.5
        alpha = 1.0 if authority == 'LDWP' else 0.6
        
        axes[0].hist(auth_df['error_pct'], bins=50, alpha=alpha, 
                    label=authority, color=color, linewidth=linewidth, 
                    histtype='step')
    
    axes[0].axvline(x=0, color='black', linestyle='--', linewidth=1)
    axes[0].set_xlabel('Percentage Error (%)', fontsize=11)
    axes[0].set_ylabel('Frequency', fontsize=11)
    axes[0].set_title('Forecast Error Distribution by Authority', 
                     fontsize=13, fontweight='bold')
    axes[0].legend(loc='upper right', fontsize=10)
    axes[0].grid(True, alpha=0.3)
    
    # 2. Box plot comparison
    error_data = []
    labels = []
    
    for authority in authorities:
        auth_df = df[df['authority'] == authority].copy()
        auth_df['error_pct'] = ((auth_df['y_true'] - auth_df['yhat']) / auth_df['y_true']) * 100
        error_data.append(auth_df['error_pct'].values)
        labels.append(authority)
    
    bp = axes[1].boxplot(error_data, labels=labels, patch_artist=True,
                         showmeans=True, meanline=True)
    
    # Color LDWP differently
    for i, patch in enumerate(bp['boxes']):
        if labels[i] == 'LDWP':
            patch.set_facecolor('#e74c3c')
            patch.set_alpha(0.6)
        else:
            patch.set_facecolor('#3498db')
            patch.set_alpha(0.4)
    
    axes[1].axhline(y=0, color='black', linestyle='--', linewidth=1)
    axes[1].set_ylabel('Percentage Error (%)', fontsize=11)
    axes[1].set_xlabel('Balancing Authority', fontsize=11)
    axes[1].set_title('Error Distribution Comparison (Box Plot)', 
                     fontsize=13, fontweight='bold')
    axes[1].grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    plt.savefig(output_dir / 'prophet_error_distribution.png', dpi=150, bbox_inches='tight')
    plt.close()


def plot_mape_comparison(output_dir=None):
    """Plot MAPE comparison between baseline and Prophet."""
    if output_dir is None:
        output_dir = Path("outputs/monitoring")
    else:
        output_dir = Path(output_dir)
    
    # Load Prophet results
    prophet_path = Path("outputs/prophet_forecast_results.csv")
    if not prophet_path.exists():
        print(f"Warning: Prophet results not found at {prophet_path}")
        return
    
    prophet_df = pd.read_csv(prophet_path)
    
    # Load baseline results from CSV instead of hardcoding
    baseline_path = Path("outputs/baseline_forecast_results.csv")
    if baseline_path.exists():
        baseline_df = pd.read_csv(baseline_path)
        # Filter out AVERAGE row if present
        baseline_df = baseline_df[baseline_df['balancing_authority'] != 'AVERAGE'].copy()
        baseline_df = baseline_df.rename(columns={
            'balancing_authority': 'authority',
            'naive_mape': 'baseline_mape'
        })
        baseline_df = baseline_df[['authority', 'baseline_mape']]
    else:
        # Fallback to hardcoded values if baseline results not found
        baseline_data = {
            'authority': ['CISO', 'BANC', 'TIDC', 'IID', 'LDWP'],
            'baseline_mape': [4.75, 5.78, 5.92, 6.04, 32.76]
        }
        baseline_df = pd.DataFrame(baseline_data)
    
    # Merge
    comparison_df = baseline_df.merge(prophet_df[['authority', 'test_mape']], on='authority')
    comparison_df['improvement'] = comparison_df['baseline_mape'] - comparison_df['test_mape']
    comparison_df['improvement_pct'] = (comparison_df['improvement'] / comparison_df['baseline_mape']) * 100
    
    # Create plot
    fig, ax = plt.subplots(figsize=(12, 6))
    
    x = np.arange(len(comparison_df))
    width = 0.35
    
    bars1 = ax.bar(x - width/2, comparison_df['baseline_mape'], width, 
                   label='Baseline (Naive 24h)', color='#95a5a6', alpha=0.8)
    bars2 = ax.bar(x + width/2, comparison_df['test_mape'], width, 
                   label='Prophet', color='#3498db', alpha=0.8)
    
    # Highlight LDWP
    ldwp_idx = comparison_df[comparison_df['authority'] == 'LDWP'].index[0]
    bars1[ldwp_idx].set_color('#e74c3c')
    bars1[ldwp_idx].set_alpha(0.6)
    bars2[ldwp_idx].set_color('#c0392b')
    bars2[ldwp_idx].set_alpha(0.8)
    
    ax.set_ylabel('MAPE (%)', fontsize=11)
    ax.set_xlabel('Balancing Authority', fontsize=11)
    ax.set_title('Forecast Accuracy: Baseline vs Prophet', fontsize=13, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(comparison_df['authority'])
    ax.legend(loc='upper right', fontsize=10)
    ax.grid(True, alpha=0.3, axis='y')
    
    # Add improvement annotations
    for i, row in comparison_df.iterrows():
        if row['improvement'] > 0:
            ax.text(i, max(row['baseline_mape'], row['test_mape']) + 1, 
                   f"-{row['improvement']:.1f}%\n({row['improvement_pct']:.0f}%)",
                   ha='center', va='bottom', fontsize=9, color='green', fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(output_dir / 'prophet_vs_baseline_comparison.png', dpi=150, bbox_inches='tight')
    plt.close()


def generate_visualizations(output_dir=None):
    """Generate all forecast visualizations."""
    if output_dir is None:
        output_dir = Path("outputs/monitoring")
    else:
        output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("\n" + "="*70)
    print("GENERATING FORECAST VISUALIZATIONS")
    print("="*70)
    
    # Load data
    print("\nLoading forecast data...")
    df = load_forecast_data()
    
    authorities = sorted(df['authority'].unique())
    print(f"Authorities: {', '.join(authorities)}")
    
    # Generate plots for each authority
    print("\nGenerating individual authority plots...")
    for authority in authorities:
        filepath = plot_forecast_vs_actual(df, authority, output_dir)
        print(f"  ✓ {authority}: {filepath.name}")
    
    # Generate comparison plots
    print("\nGenerating comparison plots...")
    plot_error_distribution(df, output_dir)
    print(f"  ✓ Error distribution: prophet_error_distribution.png")
    
    plot_mape_comparison(output_dir)
    print(f"  ✓ MAPE comparison: prophet_vs_baseline_comparison.png")
    
    print(f"\n✓ All visualizations saved to {output_dir}/")
    print("="*70 + "\n")


if __name__ == "__main__":
    generate_visualizations()
