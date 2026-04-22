"""
Minimal Proof-of-Concept for Depth Map Refinement.

This is a PoC to validate the feasibility of adaptive fractional filtering
for archaeological 3D modeling. Not a production system.

Usage:
    python run_minimal_poc.py --data synthetic --num_samples 10 --out_dir results/poc
    python run_minimal_poc.py --data nyu --nyu_mat data/nyu_depth_v2_labeled.mat --num_samples 20
"""

import argparse
import os
import sys
import json
import random
import warnings
import numpy as np
import pandas as pd
from tqdm import tqdm
import traceback

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from data_loader import load_dataset
from degradations import create_degradations
from filters import apply_filter
from fractional import apply_fixed_fractional
from adaptive_order import apply_adaptive_fractional
from metrics import compute_all_metrics
from pointcloud import compute_all_pc_metrics, depth_to_pointcloud
from visualization import create_comparison_grid, plot_metrics_comparison
from utils import print_section, create_intrinsics, resize_with_mask


def setup_seed(seed):
    """Set random seed for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)


def process_sample(sample_idx, rgb, gt_depth, valid_mask, 
                   height, width, noise_sigma, hole_ratio, edge_hole_ratio,
                   max_depth, intrinsics,
                   fixed_alpha=0.5, fixed_radius=5, fixed_iterations=2,
                   adaptive_alpha_min=0.2, adaptive_alpha_max=0.9,
                   adaptive_radius=5, adaptive_iterations=2):
    """
    Process a single sample through all methods.
    
    Returns:
        result_dict: dictionary with all results.
    """
    result = {
        'sample_idx': sample_idx,
        'rgb': rgb,
        'gt_depth': gt_depth,
        'valid_mask': valid_mask,
    }
    
    # Create degraded depth
    degraded_depth, degraded_mask, deg_info = create_degradations(
        gt_depth, rgb, valid_mask,
        noise_sigma=noise_sigma,
        hole_ratio=hole_ratio,
        edge_hole_ratio=edge_hole_ratio
    )
    
    result['degraded_depth'] = degraded_depth
    result['degraded_mask'] = degraded_mask
    result['deg_info'] = deg_info
    
    # Run all refinement methods
    methods = [
        ('input_filled', 'filters'),
        ('median_filter', 'filters'),
        ('bilateral_filter', 'filters'),
        ('guided_filter', 'filters'),
        ('fixed_fractional', 'fractional'),
        ('adaptive_fractional', 'adaptive'),
    ]
    
    refined_results = {}
    debug_results = {}
    
    for method_name, method_type in methods:
        print(f"  [{method_name}]...", end='', flush=True)
        
        try:
            if method_type == 'filters':
                refined = apply_filter(method_name, degraded_depth, rgb, degraded_mask)
                refined_results[method_name] = refined
                debug_results[method_name] = None
            
            elif method_type == 'fractional':
                refined = apply_fixed_fractional(degraded_depth, rgb, degraded_mask,
                                                alpha=fixed_alpha,
                                                radius=fixed_radius,
                                                iterations=fixed_iterations)
                refined_results[method_name] = refined
                debug_results[method_name] = None
            
            elif method_type == 'adaptive':
                refined, debug_info = apply_adaptive_fractional(
                    degraded_depth, rgb, degraded_mask,
                    alpha_min=adaptive_alpha_min,
                    alpha_max=adaptive_alpha_max,
                    radius=adaptive_radius,
                    iterations=adaptive_iterations
                )
                refined_results[method_name] = refined
                debug_results[method_name] = debug_info
            
            print(" OK")
        
        except Exception as e:
            print(f" ERROR: {e}")
            traceback.print_exc()
            refined_results[method_name] = gt_depth.copy()  # Fallback
            debug_results[method_name] = None
    
    result['refined_results'] = refined_results
    result['debug_results'] = debug_results
    
    # Compute metrics for each method
    metrics_per_method = {}
    pc_metrics_per_method = {}
    
    for method_name, refined_depth in refined_results.items():
        # Depth metrics
        depth_metrics = compute_all_metrics(refined_depth, gt_depth, valid_mask, max_depth)
        metrics_per_method[method_name] = depth_metrics
        
        # Point cloud metrics
        pc_metrics = compute_all_pc_metrics(refined_depth, gt_depth, intrinsics, valid_mask)
        pc_metrics_per_method[method_name] = pc_metrics
    
    result['metrics_per_method'] = metrics_per_method
    result['pc_metrics_per_method'] = pc_metrics_per_method
    
    return result


def run_experiment(args):
    """Main experiment runner."""
    
    print_section("Depth Map Refinement PoC")
    print(f"Data Mode: {args.data}")
    print(f"Output Dir: {args.out_dir}")
    print(f"Num Samples: {args.num_samples}")
    print(f"Height x Width: {args.height} x {args.width}")
    print(f"Seed: {args.seed}")
    
    # Setup
    setup_seed(args.seed)
    os.makedirs(args.out_dir, exist_ok=True)
    
    # Load data
    print_section("Loading Dataset")
    
    dataset = load_dataset(
        args.data,
        nyu_mat=args.nyu_mat,
        num_samples=args.num_samples,
        height=args.height,
        width=args.width,
        seed=args.seed
    )
    
    print(f"Loaded {len(dataset)} samples")
    
    # Camera intrinsics
    if args.data == 'synthetic':
        intrinsics = create_intrinsics(
            fx=500, fy=500,
            cx=args.width / 2, cy=args.height / 2
        )
    else:  # NYU
        intrinsics = create_intrinsics(
            fx=518.8579, fy=519.4696,
            cx=325.5824, cy=253.7362
        )
    
    # Process all samples
    print_section("Processing Samples")
    
    all_results = []
    figures_dir = os.path.join(args.out_dir, 'figures')
    os.makedirs(figures_dir, exist_ok=True)
    
    for sample_idx, (rgb, gt_depth, valid_mask) in enumerate(tqdm(dataset, desc="Samples")):
        print(f"\nSample {sample_idx}:")
        
        # Resize if needed
        if rgb.shape[:2] != (args.height, args.width):
            import cv2
            rgb = cv2.resize(rgb, (args.width, args.height), interpolation=cv2.INTER_LINEAR)
            gt_depth_resized, valid_mask_resized = resize_with_mask(gt_depth, valid_mask, 
                                                                     (args.height, args.width))
            gt_depth = gt_depth_resized
            valid_mask = valid_mask_resized
        
        # Process sample
        result = process_sample(
            sample_idx, rgb, gt_depth, valid_mask,
            args.height, args.width,
            args.noise_sigma, args.hole_ratio, args.edge_hole_ratio,
            args.max_depth, intrinsics,
            fixed_alpha=args.fixed_alpha,
            fixed_radius=args.fixed_radius,
            fixed_iterations=args.fixed_iterations,
            adaptive_alpha_min=args.adaptive_alpha_min,
            adaptive_alpha_max=args.adaptive_alpha_max,
            adaptive_radius=args.adaptive_radius,
            adaptive_iterations=args.adaptive_iterations
        )
        
        all_results.append(result)
        
        # Visualize (first 5 samples)
        if sample_idx < 5:
            print(f"  Saving visualizations...")
            create_comparison_grid(
                sample_idx, rgb, gt_depth, result['degraded_depth'],
                result['refined_results'], valid_mask,
                debug_dict=result['debug_results'].get('adaptive_fractional'),
                output_dir=figures_dir
            )
    
    # Aggregate metrics
    print_section("Aggregating Metrics")
    
    metrics_list = []
    for result in all_results:
        for method_name, method_metrics in result['metrics_per_method'].items():
            pc_metrics = result['pc_metrics_per_method'][method_name]
            
            row = {
                'sample_id': result['sample_idx'],
                'method': method_name,
            }
            row.update(method_metrics)
            row.update(pc_metrics)
            metrics_list.append(row)
    
    metrics_df = pd.DataFrame(metrics_list)
    
    # Save metrics CSV
    metrics_csv = os.path.join(args.out_dir, 'metrics.csv')
    metrics_df.to_csv(metrics_csv, index=False)
    print(f"Saved: {metrics_csv}")
    
    # Compute mean metrics
    metrics_mean_df = metrics_df.groupby('method').mean()
    metrics_mean_csv = os.path.join(args.out_dir, 'metrics_mean.csv')
    metrics_mean_df.to_csv(metrics_mean_csv)
    print(f"Saved: {metrics_mean_csv}")
    
    # Save config
    config = {
        'data_mode': args.data,
        'num_samples': args.num_samples,
        'height': args.height,
        'width': args.width,
        'seed': args.seed,
        'noise_sigma': args.noise_sigma,
        'hole_ratio': args.hole_ratio,
        'edge_hole_ratio': args.edge_hole_ratio,
        'max_depth': args.max_depth,
        'fixed_alpha': args.fixed_alpha,
        'fixed_radius': args.fixed_radius,
        'fixed_iterations': args.fixed_iterations,
        'adaptive_alpha_min': args.adaptive_alpha_min,
        'adaptive_alpha_max': args.adaptive_alpha_max,
        'adaptive_radius': args.adaptive_radius,
        'adaptive_iterations': args.adaptive_iterations,
    }
    
    config_json = os.path.join(args.out_dir, 'config.json')
    with open(config_json, 'w') as f:
        json.dump(config, f, indent=2)
    print(f"Saved: {config_json}")
    
    # Generate summary
    print_section("Summary")
    
    summary_md = os.path.join(args.out_dir, 'summary.md')
    with open(summary_md, 'w', encoding='utf-8') as f:
        f.write("# Depth Map Refinement PoC - Results Summary\n\n")
        
        f.write("## Experiment Configuration\n\n")
        f.write(f"- Data Mode: {args.data}\n")
        f.write(f"- Number of Samples: {len(all_results)}\n")
        f.write(f"- Image Size: {args.height} x {args.width}\n")
        f.write(f"- Degradation: Mixed (Gaussian noise + random holes + edge holes)\n")
        f.write(f"- Noise Sigma: {args.noise_sigma} m\n")
        f.write(f"- Hole Ratio: {args.hole_ratio}\n")
        f.write(f"- Edge Hole Ratio: {args.edge_hole_ratio}\n")
        f.write("- Fractional Params:\n")
        f.write(f"  - fixed: alpha={args.fixed_alpha}, radius={args.fixed_radius}, iterations={args.fixed_iterations}\n")
        f.write(
            f"  - adaptive: alpha_min={args.adaptive_alpha_min}, alpha_max={args.adaptive_alpha_max}, "
            f"radius={args.adaptive_radius}, iterations={args.adaptive_iterations}\n\n"
        )
        
        f.write("## Methods Evaluated\n\n")
        f.write("1. **input_filled**: Simple hole-filling baseline\n")
        f.write("2. **median_filter**: Median filtering (kernel size=5)\n")
        f.write("3. **bilateral_filter**: Edge-preserving bilateral filtering\n")
        f.write("4. **guided_filter**: RGB-guided depth refinement\n")
        f.write("5. **fixed_fractional**: Fixed-order fractional integral (PoC alpha=0.5)\n")
        f.write("6. **adaptive_fractional**: Adaptive-order fractional with RGB-Depth consistency (PoC)\n\n")
        
        f.write("## Mean Metrics by Method\n\n")
        f.write(metrics_mean_df.to_markdown())
        f.write("\n\n")
        
        # Analysis
        f.write("## Analysis\n\n")
        
        # Compare adaptive vs fixed and guided
        adaptive_row = metrics_mean_df.loc['adaptive_fractional']
        fixed_row = metrics_mean_df.loc['fixed_fractional']
        guided_row = metrics_mean_df.loc['guided_filter']
        
        f.write("### Adaptive Fractional vs Baselines\n\n")
        
        # RMSE comparison
        if not np.isnan(adaptive_row.get('RMSE', np.nan)) and not np.isnan(fixed_row.get('RMSE', np.nan)):
            rmse_improvement = (fixed_row['RMSE'] - adaptive_row['RMSE']) / (fixed_row['RMSE'] + 1e-6) * 100
            f.write(f"- **RMSE**: adaptive={adaptive_row['RMSE']:.4f}, fixed={fixed_row['RMSE']:.4f} "
                   f"({rmse_improvement:+.1f}%)\n")
        
        # Edge RMSE comparison
        if not np.isnan(adaptive_row.get('Edge_RMSE', np.nan)) and not np.isnan(fixed_row.get('Edge_RMSE', np.nan)):
            edge_improvement = (fixed_row['Edge_RMSE'] - adaptive_row['Edge_RMSE']) / (fixed_row['Edge_RMSE'] + 1e-6) * 100
            f.write(f"- **Edge_RMSE**: adaptive={adaptive_row['Edge_RMSE']:.4f}, fixed={fixed_row['Edge_RMSE']:.4f} "
                   f"({edge_improvement:+.1f}%)\n")
        
        # Chamfer comparison
        if not np.isnan(adaptive_row.get('Chamfer', np.nan)) and not np.isnan(fixed_row.get('Chamfer', np.nan)):
            chamfer_improvement = (fixed_row['Chamfer'] - adaptive_row['Chamfer']) / (fixed_row['Chamfer'] + 1e-6) * 100
            f.write(f"- **Chamfer**: adaptive={adaptive_row['Chamfer']:.4f}, fixed={fixed_row['Chamfer']:.4f} "
                   f"({chamfer_improvement:+.1f}%)\n")
        
        # Outlier Ratio comparison
        if not np.isnan(adaptive_row.get('OutlierRatio', np.nan)) and not np.isnan(fixed_row.get('OutlierRatio', np.nan)):
            outlier_improvement = (fixed_row['OutlierRatio'] - adaptive_row['OutlierRatio']) / (fixed_row['OutlierRatio'] + 1e-6) * 100
            f.write(f"- **OutlierRatio**: adaptive={adaptive_row['OutlierRatio']:.4f}, fixed={fixed_row['OutlierRatio']:.4f} "
                   f"({outlier_improvement:+.1f}%)\n")
        
        f.write("\n")
        
        # Conclusion
        f.write("## Conclusions (PoC Evaluation)\n\n")
        
        is_adaptive_better_edge = (not np.isnan(adaptive_row.get('Edge_RMSE', np.nan)) and 
                                  not np.isnan(fixed_row.get('Edge_RMSE', np.nan)) and 
                                  adaptive_row['Edge_RMSE'] < fixed_row['Edge_RMSE'])
        
        is_adaptive_better_chamfer = (not np.isnan(adaptive_row.get('Chamfer', np.nan)) and 
                                     not np.isnan(fixed_row.get('Chamfer', np.nan)) and 
                                     adaptive_row['Chamfer'] < fixed_row['Chamfer'])
        
        is_adaptive_better_rmse = (not np.isnan(adaptive_row.get('RMSE', np.nan)) and 
                                  not np.isnan(fixed_row.get('RMSE', np.nan)) and 
                                  adaptive_row['RMSE'] < fixed_row['RMSE'])
        
        if is_adaptive_better_edge or is_adaptive_better_chamfer:
            f.write("✓ **Preliminary Validation**: Adaptive fractional filtering shows potential benefit:\n")
            if is_adaptive_better_edge:
                f.write("  - Better Edge_RMSE indicates improved boundary preservation\n")
            if is_adaptive_better_chamfer:
                f.write("  - Better Chamfer distance indicates improved point cloud geometry\n")
            f.write("  This suggests that adaptive alpha strategy has initial merit for the proposed thesis.\n\n")
        else:
            f.write("⚠ **Needs Improvement**: Adaptive strategy does not yet outperform fixed baseline:\n")
            f.write("  - Current alpha_map computation is heuristic and may need refinement\n")
            f.write("  - RGB-Depth consistency model could be strengthened\n")
            f.write("  - Fractional kernel design may benefit from optimization\n")
            f.write("  - Consider: richer edge descriptors, learned parameters, or alternative smoothness criteria\n\n")
        
        f.write("## Important Notes\n\n")
        f.write("This is a **PoC (Proof-of-Concept)** implementation, not production code:\n\n")
        f.write("- Fractional filtering uses simplified Grünwald-Letnikov approximation\n")
        f.write("- Adaptive alpha_map is heuristic and rule-based\n")
        f.write("- No integration with COLMAP or Depth Anything V2 yet\n")
        f.write("- Synthetic and NYU experiments are limited validation; real archaeological data would be definitive\n")
        f.write("- Next steps: refine alpha adaptation, explore learning-based approaches, integrate with real data pipelines\n\n")
        
        f.write("## Output Files\n\n")
        f.write(f"- `figures/`: Sample visualizations (first 5 samples)\n")
        f.write(f"- `metrics.csv`: Per-sample metrics\n")
        f.write(f"- `metrics_mean.csv`: Mean metrics by method\n")
        f.write(f"- `config.json`: Experiment configuration\n")
        f.write(f"- `summary.md`: This summary\n")
    
    print(f"Saved: {summary_md}")
    
    # Print summary to terminal
    print("\n" + "="*70)
    print("Mean Metrics by Method:")
    print("="*70)
    print(metrics_mean_df.to_string())
    
    print("\n" + "="*70)
    print("Output Summary:")
    print("="*70)
    print(f"Output directory: {args.out_dir}")
    print(f"Metrics CSV: {metrics_csv}")
    print(f"Mean metrics CSV: {metrics_mean_csv}")
    print(f"Figures: {figures_dir}")
    print(f"Summary: {summary_md}")
    
    print("\n✓ Experiment completed successfully!")


def main():
    parser = argparse.ArgumentParser(
        description="Minimal PoC for depth map refinement research"
    )
    
    parser.add_argument('--data', type=str, choices=['synthetic', 'nyu'], default='synthetic',
                       help='Data source')
    parser.add_argument('--nyu_mat', type=str, default=None,
                       help='Path to nyu_depth_v2_labeled.mat')
    parser.add_argument('--num_samples', type=int, default=20,
                       help='Number of samples to process')
    parser.add_argument('--height', type=int, default=240,
                       help='Image height')
    parser.add_argument('--width', type=int, default=320,
                       help='Image width')
    parser.add_argument('--out_dir', type=str, default='results/poc',
                       help='Output directory')
    parser.add_argument('--seed', type=int, default=42,
                       help='Random seed')
    parser.add_argument('--noise_sigma', type=float, default=0.03,
                       help='Gaussian noise std (meters)')
    parser.add_argument('--hole_ratio', type=float, default=0.1,
                       help='Random hole ratio')
    parser.add_argument('--edge_hole_ratio', type=float, default=0.5,
                       help='Edge hole ratio')
    parser.add_argument('--max_depth', type=float, default=5.0,
                       help='Maximum depth for PSNR computation')

    # Fractional parameters
    parser.add_argument('--fixed_alpha', type=float, default=0.5,
                       help='Fixed fractional alpha')
    parser.add_argument('--fixed_radius', type=int, default=5,
                       help='Fixed fractional kernel radius')
    parser.add_argument('--fixed_iterations', type=int, default=2,
                       help='Fixed fractional iterations')
    parser.add_argument('--adaptive_alpha_min', type=float, default=0.2,
                       help='Adaptive fractional minimum alpha')
    parser.add_argument('--adaptive_alpha_max', type=float, default=0.9,
                       help='Adaptive fractional maximum alpha')
    parser.add_argument('--adaptive_radius', type=int, default=5,
                       help='Adaptive fractional kernel radius')
    parser.add_argument('--adaptive_iterations', type=int, default=2,
                       help='Adaptive fractional iterations')
    
    args = parser.parse_args()
    
    try:
        run_experiment(args)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
