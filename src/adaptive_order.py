"""
Adaptive-order fractional filtering for depth refinement.
PoC approximation - heuristic strategy, not final algorithm.
"""
import numpy as np
import cv2
try:
    from . import utils
    from . import fractional
except ImportError:
    import utils
    import fractional


def compute_rgb_depth_consistency(rgb, depth, filled_mask):
    """
    Compute RGB-Depth edge consistency.
    
    Args:
        rgb: H x W x 3 uint8.
        depth: H x W float32, filled.
        filled_mask: H x W bool.
    
    Returns:
        C: H x W float32, consistency in [0, 1].
    """
    # Extract edges
    E_rgb = utils.get_rgb_edges(rgb, method='sobel')
    E_d = utils.get_depth_edges(depth, method='sobel')
    
    # Consistency: high when edges align
    sigma_c = 0.3
    C = np.exp(-np.abs(E_rgb - E_d) / (sigma_c + 1e-6))
    
    return C.astype(np.float32)


def compute_true_edge_confidence(depth, rgb, C):
    """
    Compute true geometric edge confidence.
    
    True edges = depth edges that align with RGB edges.
    
    Args:
        depth: H x W float32, filled.
        rgb: H x W x 3 uint8.
        C: H x W float32, consistency.
    
    Returns:
        true_edge: H x W float32 in [0, 1].
    """
    E_d = utils.get_depth_edges(depth, method='sobel')
    
    # Confidence: strong depth edges + good RGB alignment
    true_edge = E_d * (0.3 + 0.7 * C)
    
    return true_edge.astype(np.float32)


def compute_texture_pseudo_edge(rgb, depth):
    """
    Compute texture pseudo-edge (RGB edges without depth edges).
    
    Args:
        rgb: H x W x 3 uint8.
        depth: H x W float32, filled.
    
    Returns:
        texture_edge: H x W float32 in [0, 1].
    """
    E_rgb = utils.get_rgb_edges(rgb, method='sobel')
    E_d = utils.get_depth_edges(depth, method='sobel')
    
    # Texture edges: strong RGB edges but weak depth edges
    texture_edge = E_rgb * (1 - np.clip(E_d, 0, 1))
    
    return texture_edge.astype(np.float32)


def compute_mask_boundary(degraded_mask, dilation_iterations=3):
    """
    Compute boundary around invalid regions.
    
    Args:
        degraded_mask: H x W bool, valid pixels.
        dilation_iterations: dilation iterations.
    
    Returns:
        E_mask: H x W float32 in [0, 1], boundary indicator.
    """
    # Dilate hole region
    hole_mask = (~degraded_mask).astype(np.uint8)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    dilated_hole = cv2.dilate(hole_mask, kernel, iterations=dilation_iterations).astype(bool)
    
    # Boundary is the transition between dilated holes and original valid
    E_mask = np.logical_xor(dilated_hole, (~degraded_mask)).astype(np.float32)
    
    return E_mask


def compute_smoothness_map(rgb, depth, degraded_mask):
    """
    Compute smoothness strength map for adaptive filtering.
    
    Strategy:
    - High smoothness in texture pseudo-edge regions (prevent RGB artifacts).
    - High smoothness in low-confidence areas.
    - Low smoothness at true geometric edges (preserve boundaries).
    - Moderate smoothness at mask boundaries.
    
    Args:
        rgb: H x W x 3 uint8.
        depth: H x W float32, filled.
        degraded_mask: H x W bool.
    
    Returns:
        smooth_strength: H x W float32 in [0, 1].
        debug_info: dict with intermediate results.
    """
    # Step 1: Compute edges and consistency
    E_rgb = utils.get_rgb_edges(rgb, method='sobel')
    E_d = utils.get_depth_edges(depth, method='sobel')
    C = compute_rgb_depth_consistency(rgb, depth, degraded_mask)
    
    # Step 2: Compute confidences
    true_edge = compute_true_edge_confidence(depth, rgb, C)
    texture_edge = compute_texture_pseudo_edge(rgb, depth)
    E_mask = compute_mask_boundary(degraded_mask, dilation_iterations=3)
    
    # Step 3: Compute smoothness
    # Base: 1 - true_edge (smooth away from true edges)
    smooth_strength = 1.0 - np.clip(true_edge, 0, 1)
    
    # Boost smoothness at texture edges to prevent RGB artifacts
    smooth_strength = np.minimum(smooth_strength, 1.0 - 0.5 * np.clip(texture_edge, 0, 1))
    
    # Reduce smoothness at mask boundaries to avoid crossing holes
    smooth_strength = smooth_strength * (1.0 - 0.3 * np.clip(E_mask, 0, 1))
    
    # Clip to valid range
    smooth_strength = np.clip(smooth_strength, 0, 1).astype(np.float32)
    
    debug_info = {
        'E_rgb': E_rgb,
        'E_d': E_d,
        'C': C,
        'true_edge': true_edge,
        'texture_edge': texture_edge,
        'E_mask': E_mask,
        'smooth_strength': smooth_strength
    }
    
    return smooth_strength, debug_info


def compute_alpha_map(smooth_strength, alpha_min=0.2, alpha_max=0.9):
    """
    Convert smoothness to adaptive alpha order.
    
    Higher smoothness => higher alpha => stronger smoothing.
    
    Args:
        smooth_strength: H x W float32 in [0, 1].
        alpha_min: minimum fractional order.
        alpha_max: maximum fractional order.
    
    Returns:
        alpha_map: H x W float32 in [alpha_min, alpha_max].
    """
    alpha_map = alpha_min + smooth_strength * (alpha_max - alpha_min)
    return alpha_map.astype(np.float32)


def adaptive_fractional_filter(degraded_depth, rgb, degraded_mask=None,
                              alpha_min=0.2, alpha_max=0.9, radius=5, iterations=2):
    """
    Adaptive-order fractional depth refinement.
    
    PoC APPROXIMATION: Heuristic strategy combining RGB-Depth consistency and edge analysis.
    Production version will refine alpha_map computation and fractional kernel.
    
    Args:
        degraded_depth: H x W float32 with nan.
        rgb: H x W x 3 uint8.
        degraded_mask: H x W bool.
        alpha_min: minimum fractional order.
        alpha_max: maximum fractional order.
        radius: convolution radius.
        iterations: number of iterations.
    
    Returns:
        refined_depth: H x W float32.
        debug_info: dict with intermediate results.
    """
    refined = degraded_depth.copy()
    
    if degraded_mask is None:
        degraded_mask = np.isfinite(degraded_depth)
    
    # Fill holes for processing
    depth_filled = utils.fill_depth_holes(degraded_depth)
    
    # Compute smoothness map
    smooth_strength, debug_info = compute_smoothness_map(rgb, depth_filled, degraded_mask)
    
    # Compute alpha map
    alpha_map = compute_alpha_map(smooth_strength, alpha_min, alpha_max)
    debug_info['alpha_map'] = alpha_map
    
    # For simplicity: compute three filtered versions and interpolate
    # This is a PoC approximation; production would use per-pixel alpha
    low_alpha = alpha_min
    mid_alpha = (alpha_min + alpha_max) / 2
    high_alpha = alpha_max
    
    print("  [Fractional] Computing low-alpha filter...")
    low_filtered = fractional.fixed_fractional_filter(
        degraded_depth, rgb, degraded_mask, alpha=low_alpha, radius=radius, iterations=iterations
    )
    
    print("  [Fractional] Computing mid-alpha filter...")
    mid_filtered = fractional.fixed_fractional_filter(
        degraded_depth, rgb, degraded_mask, alpha=mid_alpha, radius=radius, iterations=iterations
    )
    
    print("  [Fractional] Computing high-alpha filter...")
    high_filtered = fractional.fixed_fractional_filter(
        degraded_depth, rgb, degraded_mask, alpha=high_alpha, radius=radius, iterations=iterations
    )
    
    # Interpolate based on alpha_map
    # Normalize alpha_map to [0, 1]
    alpha_norm = (alpha_map - alpha_min) / (alpha_max - alpha_min + 1e-6)
    alpha_norm = np.clip(alpha_norm, 0, 1)
    
    # Linear interpolation: low -> mid -> high
    refined = np.zeros_like(degraded_depth)
    mask_low = alpha_norm < 0.5
    mask_high = alpha_norm >= 0.5
    
    refined[mask_low] = (low_filtered[mask_low] * (1 - 2 * alpha_norm[mask_low]) + 
                         mid_filtered[mask_low] * (2 * alpha_norm[mask_low]))
    refined[mask_high] = (mid_filtered[mask_high] * (2 * (1 - alpha_norm[mask_high])) + 
                          high_filtered[mask_high] * (2 * alpha_norm[mask_high] - 1))
    
    return refined.astype(np.float32), debug_info


def apply_adaptive_fractional(degraded_depth, rgb, degraded_mask=None, **kwargs):
    """
    Wrapper for adaptive fractional filter.
    
    Args:
        degraded_depth: H x W float32 with nan.
        rgb: H x W x 3 uint8.
        degraded_mask: H x W bool.
        **kwargs: alpha_min, alpha_max, radius, iterations.
    
    Returns:
        refined_depth: H x W float32.
        debug_info: dict (or empty if not needed).
    """
    alpha_min = kwargs.get('alpha_min', 0.2)
    alpha_max = kwargs.get('alpha_max', 0.9)
    radius = kwargs.get('radius', 5)
    iterations = kwargs.get('iterations', 2)
    
    refined, debug_info = adaptive_fractional_filter(
        degraded_depth, rgb, degraded_mask,
        alpha_min=alpha_min, alpha_max=alpha_max, radius=radius, iterations=iterations
    )
    
    return refined, debug_info
