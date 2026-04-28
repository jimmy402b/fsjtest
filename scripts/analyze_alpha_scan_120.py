#!/usr/bin/env python3
import os
import pandas as pd
import glob

# Collect all metrics_mean.csv files from alpha_scan_120
scan_dirs = sorted(glob.glob('results/alpha_scan_120/*/metrics_mean.csv'))
results = []

for metrics_csv in scan_dirs:
    config_dir = os.path.dirname(metrics_csv)
    config_name = os.path.basename(config_dir)
    
    df = pd.read_csv(metrics_csv, index_col=0)
    if 'adaptive_fractional' in df.index:
        row = df.loc['adaptive_fractional']
        results.append({
            'config': config_name,
            'RMSE': row.get('RMSE', None),
            'Chamfer': row.get('Chamfer', None),
            'SelectionScore': row.get('SelectionScore', None),
            'Edge_RMSE': row.get('Edge_RMSE', None),
        })

if results:
    result_df = pd.DataFrame(results)
    print("\n" + "=" * 80)
    print("ALPHA SCAN 120-SAMPLE RESULTS (Adaptive Fractional)")
    print("=" * 80)
    print(result_df.to_string(index=False))
    print()
    
    # Find best by SelectionScore
    best_idx = result_df['SelectionScore'].idxmin()
    best_cfg = result_df.loc[best_idx]
    print("\n" + "=" * 80)
    print("BEST CANDIDATE BY SelectionScore:")
    print("=" * 80)
    print(f"Config: {best_cfg['config']}")
    print(f"  RMSE: {best_cfg['RMSE']:.6f}")
    print(f"  Chamfer: {best_cfg['Chamfer']:.6f}")
    print(f"  SelectionScore: {best_cfg['SelectionScore']:.6f}")
    print(f"  Edge_RMSE: {best_cfg['Edge_RMSE']:.6f}")
    print()
    
    # Also show by RMSE
    best_rmse_idx = result_df['RMSE'].idxmin()
    best_rmse_cfg = result_df.loc[best_rmse_idx]
    print("=" * 80)
    print("BEST BY RMSE (for reference):")
    print("=" * 80)
    print(f"Config: {best_rmse_cfg['config']}")
    print(f"  RMSE: {best_rmse_cfg['RMSE']:.6f}")
    print(f"  Chamfer: {best_rmse_cfg['Chamfer']:.6f}")
    print(f"  SelectionScore: {best_rmse_cfg['SelectionScore']:.6f}")
else:
    print("No adaptive_fractional results found.")
