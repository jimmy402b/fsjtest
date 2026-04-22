"""
Depth map degradation functions.
"""
import numpy as np
import cv2
from scipy import ndimage
try:
    from . import utils
except ImportError:
    import utils


def apply_gaussian_noise(depth, sigma=0.03, valid_mask=None):
    """
    Apply Gaussian noise to depth map.
    
    Args:
        depth: H x W float32, in meters.
        sigma: standard deviation of noise.
        valid_mask: H x W bool, where to apply noise.
    
    Returns:
        degraded_depth: H x W float32.
        degradation_info: dict.
    """
    depth = np.asarray(depth, dtype=np.float32)
    if valid_mask is None:
        valid_mask = np.isfinite(depth)
    
    noise = np.random.normal(0, sigma, depth.shape).astype(np.float32)
    degraded_depth = depth.copy()
    degraded_depth[valid_mask] += noise[valid_mask]
    
    info = {
        'type': 'gaussian_noise',
        'sigma': sigma,
        'affected_pixels': np.sum(valid_mask)
    }
    return degraded_depth, info


def apply_depth_dependent_noise(depth, base_sigma=0.01, valid_mask=None):
    """
    Apply depth-dependent noise: sigma(z) = base_sigma * (1 + z / z_max).
    
    Args:
        depth: H x W float32.
        base_sigma: base noise level.
        valid_mask: H x W bool.
    
    Returns:
        degraded_depth: H x W float32.
        degradation_info: dict.
    """
    depth = np.asarray(depth, dtype=np.float32)
    if valid_mask is None:
        valid_mask = np.isfinite(depth)
    
    valid_depths = depth[valid_mask]
    z_max = np.max(valid_depths) if valid_depths.size > 0 else 1.0
    z_min = np.min(valid_depths) if valid_depths.size > 0 else 0.0
    
    # Normalize depth to [0, 1]
    depth_norm = (depth - z_min) / (z_max - z_min + 1e-6)
    
    # Compute depth-dependent sigma
    sigma_map = base_sigma * (1 + depth_norm)
    
    # Apply noise
    noise = np.random.normal(0, 1, depth.shape).astype(np.float32)
    degraded_depth = depth.copy()
    degraded_depth[valid_mask] += noise[valid_mask] * sigma_map[valid_mask]
    
    info = {
        'type': 'depth_dependent_noise',
        'base_sigma': base_sigma,
        'z_min': float(z_min),
        'z_max': float(z_max)
    }
    return degraded_depth, info


def apply_random_holes(depth, hole_ratio=0.1, valid_mask=None):
    """
    Randomly remove depth values (create holes).
    
    Args:
        depth: H x W float32.
        hole_ratio: fraction of valid pixels to remove.
        valid_mask: H x W bool.
    
    Returns:
        degraded_depth: H x W float32, holes as nan.
        degradation_info: dict.
    """
    depth = np.asarray(depth, dtype=np.float32)
    if valid_mask is None:
        valid_mask = np.isfinite(depth)
    
    degraded_depth = depth.copy()
    valid_indices = np.where(valid_mask)
    num_valid = len(valid_indices[0])
    num_holes = int(num_valid * hole_ratio)
    
    if num_holes > 0:
        hole_idx = np.random.choice(num_valid, size=num_holes, replace=False)
        degraded_depth[valid_indices[0][hole_idx], valid_indices[1][hole_idx]] = np.nan
    
    degraded_mask = np.isfinite(degraded_depth)
    
    info = {
        'type': 'random_holes',
        'hole_ratio': hole_ratio,
        'num_holes': num_holes,
        'total_valid': num_valid
    }
    return degraded_depth, info


def apply_edge_holes(depth, valid_mask=None, edge_hole_ratio=0.5):
    """
    Remove depth at edges to simulate boundary artifacts.
    
    Args:
        depth: H x W float32.
        valid_mask: H x W bool.
        edge_hole_ratio: fraction of edge pixels to remove.
    
    Returns:
        degraded_depth: H x W float32.
        degradation_info: dict.
    """
    depth = np.asarray(depth, dtype=np.float32)
    if valid_mask is None:
        valid_mask = np.isfinite(depth)
    
    # Fill holes temporarily to detect edges
    depth_filled = utils.fill_depth_holes(depth)
    
    # Compute depth edges using Sobel
    depth_edges = utils.get_depth_edges(depth_filled, method='sobel')
    
    # Threshold edges
    edge_threshold = 0.1
    edge_mask = depth_edges > edge_threshold
    
    # Dilate edge mask to get boundary region
    edge_mask = cv2.dilate(edge_mask.astype(np.uint8), 
                           cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)), 
                           iterations=2).astype(bool)
    
    # Randomly remove some edge pixels
    edge_valid = edge_mask & valid_mask
    edge_indices = np.where(edge_valid)
    num_edge = len(edge_indices[0])
    num_remove = int(num_edge * edge_hole_ratio)
    
    degraded_depth = depth.copy()
    if num_remove > 0:
        remove_idx = np.random.choice(num_edge, size=num_remove, replace=False)
        degraded_depth[edge_indices[0][remove_idx], edge_indices[1][remove_idx]] = np.nan
    
    info = {
        'type': 'edge_holes',
        'edge_hole_ratio': edge_hole_ratio,
        'num_edge_holes': num_remove,
        'num_edge_pixels': num_edge
    }
    return degraded_depth, info


def apply_mixed_degradation(depth, rgb, valid_mask, 
                           noise_sigma=0.03, hole_ratio=0.1, edge_hole_ratio=0.5):
    """
    Apply mixed degradation: Gaussian noise + random holes + edge holes.
    
    Args:
        depth: H x W float32 clean depth.
        rgb: H x W x 3 uint8.
        valid_mask: H x W bool.
        noise_sigma: Gaussian noise std.
        hole_ratio: random hole ratio.
        edge_hole_ratio: edge hole ratio.
    
    Returns:
        degraded_depth: H x W float32 with nan as holes.
        degraded_mask: H x W bool indicating valid pixels.
        degradation_info: dict with all info.
    """
    # Start with clean depth
    degraded_depth = depth.copy()
    degraded_mask = valid_mask.copy()
    
    all_info = {'type': 'mixed'}
    
    # 1. Gaussian noise
    degraded_depth, info1 = apply_gaussian_noise(degraded_depth, sigma=noise_sigma, 
                                                 valid_mask=degraded_mask)
    all_info['gaussian_noise'] = info1
    
    # 2. Random holes
    degraded_depth, info2 = apply_random_holes(degraded_depth, hole_ratio=hole_ratio)
    all_info['random_holes'] = info2
    degraded_mask = np.isfinite(degraded_depth)
    
    # 3. Edge holes
    degraded_depth, info3 = apply_edge_holes(degraded_depth, valid_mask=degraded_mask, 
                                            edge_hole_ratio=edge_hole_ratio)
    all_info['edge_holes'] = info3
    degraded_mask = np.isfinite(degraded_depth)
    
    return degraded_depth, degraded_mask, all_info


def create_degradations(depth, rgb, valid_mask, noise_sigma=0.03, 
                       hole_ratio=0.1, edge_hole_ratio=0.5):
    """
    Create degraded depth with mixed degradation types.
    Wrapper for consistency with main pipeline.
    
    Args:
        depth: H x W float32.
        rgb: H x W x 3 uint8.
        valid_mask: H x W bool.
        noise_sigma: noise std.
        hole_ratio: hole ratio.
        edge_hole_ratio: edge hole ratio.
    
    Returns:
        degraded_depth, degraded_mask, degradation_info.
    """
    return apply_mixed_degradation(depth, rgb, valid_mask, 
                                  noise_sigma=noise_sigma, 
                                  hole_ratio=hole_ratio, 
                                  edge_hole_ratio=edge_hole_ratio)
