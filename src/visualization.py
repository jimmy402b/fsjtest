"""
Visualization utilities for depth refinement results.
"""
import numpy as np
import cv2
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for batch processing
import matplotlib.pyplot as plt
from matplotlib import cm
import os


def depth_to_colormap(depth, mask=None, cmap_name='turbo'):
    """
    Convert depth map to RGB using colormap.
    
    Args:
        depth: H x W float32.
        mask: H x W bool valid pixels.
        cmap_name: matplotlib colormap name.
    
    Returns:
        rgb: H x W x 3 uint8.
    """
    depth = np.asarray(depth, dtype=np.float32)
    
    if mask is None:
        mask = np.isfinite(depth)
    
    # Normalize depth to [0, 1]
    valid_depth = depth[mask]
    if len(valid_depth) == 0:
        return np.zeros((*depth.shape, 3), dtype=np.uint8)
    
    depth_min = np.min(valid_depth)
    depth_max = np.max(valid_depth)
    
    if depth_max > depth_min:
        depth_norm = (depth - depth_min) / (depth_max - depth_min)
    else:
        depth_norm = np.zeros_like(depth)
    
    # Apply colormap
    cmap = cm.get_cmap(cmap_name)
    depth_colored = cmap(depth_norm)  # Returns RGBA in [0, 1]
    rgb = (depth_colored[:, :, :3] * 255).astype(np.uint8)
    
    # Set invalid pixels to black
    rgb[~mask] = 0
    
    return rgb


def error_to_colormap(error, mask=None, percentile=95):
    """
    Convert error map to RGB using hot colormap.
    
    Args:
        error: H x W float32 error values.
        mask: H x W bool valid pixels.
        percentile: percentile for color scaling.
    
    Returns:
        rgb: H x W x 3 uint8.
    """
    error = np.asarray(error, dtype=np.float32)
    
    if mask is None:
        mask = np.isfinite(error)
    
    # Scale to valid region
    valid_error = error[mask]
    if len(valid_error) == 0:
        return np.zeros((*error.shape, 3), dtype=np.uint8)
    
    error_max = np.percentile(valid_error, percentile)
    error_norm = np.clip(error / (error_max + 1e-6), 0, 1)
    
    # Apply hot colormap
    cmap = cm.get_cmap('hot')
    error_colored = cmap(error_norm)
    rgb = (error_colored[:, :, :3] * 255).astype(np.uint8)
    
    # Set invalid pixels to black
    rgb[~mask] = 0
    
    return rgb


def mask_to_colormap(mask, fg_color=(0, 255, 0)):
    """
    Convert binary mask to RGB.
    
    Args:
        mask: H x W bool.
        fg_color: RGB color for foreground.
    
    Returns:
        rgb: H x W x 3 uint8.
    """
    H, W = mask.shape
    rgb = np.zeros((H, W, 3), dtype=np.uint8)
    rgb[mask] = np.array(fg_color, dtype=np.uint8)
    return rgb


def create_comparison_grid(sample_idx, rgb, gt_depth, degraded_depth, 
                           refined_dict, valid_mask, debug_dict=None, 
                           output_dir=None):
    """
    Create comparison grid visualization for a single sample.
    
    Args:
        sample_idx: sample index.
        rgb: H x W x 3 uint8.
        gt_depth: H x W float32.
        degraded_depth: H x W float32.
        refined_dict: dict of method_name -> refined_depth.
        valid_mask: H x W bool.
        debug_dict: optional dict with debug info (e.g., alpha_map).
        output_dir: directory to save visualization.
    
    Returns:
        None (saves to file).
    """
    H, W = rgb.shape[:2]
    
    # Prepare images
    images = {}
    titles = {}
    
    # RGB
    images['rgb'] = rgb
    titles['rgb'] = 'RGB'
    
    # GT Depth
    images['gt_depth'] = depth_to_colormap(gt_depth, valid_mask, cmap_name='viridis')
    titles['gt_depth'] = 'GT Depth'
    
    # Degraded Depth
    images['degraded_depth'] = depth_to_colormap(degraded_depth, 
                                                 np.isfinite(degraded_depth), 
                                                 cmap_name='viridis')
    titles['degraded_depth'] = 'Degraded'
    
    # Refined methods
    for method_name, refined_depth in refined_dict.items():
        images[f'refined_{method_name}'] = depth_to_colormap(refined_depth, 
                                                              valid_mask, 
                                                              cmap_name='viridis')
        titles[f'refined_{method_name}'] = method_name.replace('_', '\n')
    
    # Error maps (for adaptive method)
    if 'adaptive_fractional' in refined_dict:
        error = np.abs(refined_dict['adaptive_fractional'] - gt_depth)
        images['error_map'] = error_to_colormap(error, valid_mask)
        titles['error_map'] = 'Error Map'
    
    # Debug info
    if debug_dict is not None:
        if 'alpha_map' in debug_dict:
            alpha_map = debug_dict['alpha_map']
            alpha_norm = (alpha_map - 0.2) / (0.9 - 0.2)
            images['alpha_map'] = depth_to_colormap(alpha_norm, 
                                                    valid_mask, 
                                                    cmap_name='cool')
            titles['alpha_map'] = 'Alpha Map'
        
        if 'E_mask' in debug_dict:
            images['E_mask'] = mask_to_colormap(debug_dict['E_mask'] > 0.5)
            titles['E_mask'] = 'Mask Boundary'
    
    # Create grid
    num_images = len(images)
    cols = min(5, num_images)
    rows = (num_images + cols - 1) // cols
    
    fig, axes = plt.subplots(rows, cols, figsize=(cols * 4, rows * 3))
    if rows == 1 and cols == 1:
        axes = np.array([[axes]])
    elif rows == 1 or cols == 1:
        axes = axes.reshape(rows, cols)
    
    axes = axes.flatten()
    
    for idx, (key, img) in enumerate(images.items()):
        ax = axes[idx]
        ax.imshow(img)
        ax.set_title(titles[key], fontsize=10)
        ax.axis('off')
    
    # Hide unused subplots
    for idx in range(len(images), len(axes)):
        axes[idx].axis('off')
    
    plt.tight_layout()
    
    # Save
    if output_dir is not None:
        os.makedirs(output_dir, exist_ok=True)
        save_path = os.path.join(output_dir, f'sample_{sample_idx:03d}_grid.png')
        plt.savefig(save_path, dpi=100, bbox_inches='tight')
        print(f"    Saved: {save_path}")
    
    plt.close()


def save_depth_maps(sample_idx, refined_dict, valid_mask, output_dir):
    """
    Save individual depth maps as PNG (colormap visualization).
    
    Args:
        sample_idx: sample index.
        refined_dict: dict of method_name -> refined_depth.
        valid_mask: H x W bool.
        output_dir: directory to save.
    
    Returns:
        None.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    for method_name, refined_depth in refined_dict.items():
        img = depth_to_colormap(refined_depth, valid_mask, cmap_name='viridis')
        save_path = os.path.join(output_dir, f'sample_{sample_idx:03d}_{method_name}.png')
        cv2.imwrite(save_path, cv2.cvtColor(img, cv2.COLOR_RGB2BGR))


def plot_metrics_comparison(metrics_df, output_dir, methods=None):
    """
    Plot comparison of metrics across methods.
    
    Args:
        metrics_df: pandas DataFrame with metrics.
        output_dir: directory to save plots.
        methods: list of method names (optional).
    
    Returns:
        None.
    """
    if methods is None:
        methods = metrics_df['method'].unique()
    
    metrics_to_plot = ['RMSE', 'MAE', 'AbsRel', 'PSNR', 'SSIM', 'Edge_RMSE', 'Chamfer', 'OutlierRatio']
    available_metrics = [m for m in metrics_to_plot if m in metrics_df.columns]
    
    num_metrics = len(available_metrics)
    cols = min(4, num_metrics)
    rows = (num_metrics + cols - 1) // cols
    
    fig, axes = plt.subplots(rows, cols, figsize=(cols * 4, rows * 3))
    axes = axes.flatten()
    
    for idx, metric in enumerate(available_metrics):
        ax = axes[idx]
        
        method_means = []
        for method in methods:
            method_data = metrics_df[metrics_df['method'] == method][metric]
            method_means.append(method_data.mean())
        
        ax.bar(range(len(methods)), method_means)
        ax.set_xticks(range(len(methods)))
        ax.set_xticklabels([m.replace('_', '\n') for m in methods], rotation=45, ha='right')
        ax.set_ylabel(metric)
        ax.set_title(f'Mean {metric}')
        ax.grid(axis='y', alpha=0.3)
    
    # Hide unused
    for idx in range(len(available_metrics), len(axes)):
        axes[idx].axis('off')
    
    plt.tight_layout()
    
    os.makedirs(output_dir, exist_ok=True)
    save_path = os.path.join(output_dir, 'metrics_comparison.png')
    plt.savefig(save_path, dpi=100, bbox_inches='tight')
    print(f"Saved: {save_path}")
    
    plt.close()
