"""
Fixed-order fractional filtering for depth refinement.
PoC approximation - not the final algorithm.
"""
import numpy as np
import cv2
from scipy import special
try:
    from . import utils
except ImportError:
    import utils


def fractional_integral_kernel(alpha, radius):
    """
    Generate 1D fractional integral kernel using Grünwald-Letnikov formula.
    
    PoC APPROXIMATION: This is a simplified implementation for proof-of-concept.
    The production version will include more sophisticated numerical schemes.
    
    Args:
        alpha: order of fractional integral (0 < alpha < 1, higher = more smoothing).
        radius: kernel radius.
    
    Returns:
        kernel: 1D array of size (2*radius+1,).
    """
    # Compute weights: c_k = Gamma(k+alpha) / (Gamma(alpha) * Gamma(k+1))
    weights = []
    for k in range(radius + 1):
        try:
            # Use scipy.special.beta for stability
            c_k = special.gamma(k + alpha) / (special.gamma(alpha) * special.gamma(k + 1))
        except:
            c_k = 0.0
        weights.append(c_k)
    
    weights = np.array(weights, dtype=np.float32)
    
    # Make symmetric
    kernel = np.concatenate([weights[::-1], weights[1:]])
    
    # Normalize
    kernel = kernel / np.sum(kernel)
    
    return kernel.astype(np.float32)


def fractional_separable_conv(depth_map, alpha, radius, mask=None):
    """
    Apply fractional integral smoothing via separable convolution.
    Mask-aware: only valid pixels participate in averaging.
    
    Args:
        depth_map: H x W float32 (can contain nan).
        alpha: fractional order.
        radius: kernel radius.
        mask: H x W bool, valid pixels.
    
    Returns:
        filtered: H x W float32.
    """
    depth = np.asarray(depth_map, dtype=np.float32)
    
    if mask is None:
        mask = np.isfinite(depth)
    
    # Fill holes for fallback only; main path uses valid-only normalization
    depth_filled = utils.fill_depth_holes(depth)
    
    # Get kernel
    kernel = fractional_integral_kernel(alpha, radius)
    
    # Separable convolution with mask-aware normalization
    # Use only valid pixels in numerator to avoid amplifying filled values.
    depth_work = np.where(mask, depth, 0.0).astype(np.float32)
    mask_float = mask.astype(np.float32)
    
    # Apply separable convolution
    kernel_2d = kernel[:, np.newaxis] * kernel[np.newaxis, :]
    kernel_2d = kernel_2d / np.sum(kernel_2d)  # Renormalize
    
    # Convolve valid-weighted depth and valid-count mask
    filtered = cv2.filter2D(depth_work, -1, kernel_2d, borderType=cv2.BORDER_REFLECT)
    
    # Mask-aware normalization: weighted by valid pixel count
    mask_convolved = cv2.filter2D(mask_float, -1, kernel_2d, borderType=cv2.BORDER_REFLECT)
    
    # Avoid division by zero
    mask_convolved = np.maximum(mask_convolved, 1e-6)
    
    # Renormalize to account for missing pixels
    filtered = filtered / mask_convolved

    # Where local support is too weak, fall back to hole-filled estimate.
    weak_support = mask_convolved < 1e-3
    if np.any(weak_support):
        filtered[weak_support] = depth_filled[weak_support]

    # Keep values in plausible range to avoid numerical explosion over iterations.
    valid_vals = depth[mask]
    if valid_vals.size > 0:
        lo = np.nanpercentile(valid_vals, 0.5)
        hi = np.nanpercentile(valid_vals, 99.5)
        if np.isfinite(lo) and np.isfinite(hi) and hi > lo:
            filtered = np.clip(filtered, lo, hi)
    
    return filtered.astype(np.float32)


def fixed_fractional_filter(degraded_depth, rgb=None, degraded_mask=None, 
                           alpha=0.5, radius=5, iterations=2):
    """
    Fixed-order fractional depth refinement.
    
    PoC APPROXIMATION: This implements a simplified version for concept validation.
    Production version will include optimized numerical schemes and parameter tuning.
    
    Args:
        degraded_depth: H x W float32 with nan.
        rgb: not used.
        degraded_mask: H x W bool.
        alpha: fractional order (0.2-0.9 recommended).
        radius: convolution radius.
        iterations: number of iterations.
    
    Returns:
        refined_depth: H x W float32.
    """
    refined = degraded_depth.copy()
    
    if degraded_mask is None:
        degraded_mask = np.isfinite(degraded_depth)
    
    for _ in range(iterations):
        refined = fractional_separable_conv(refined, alpha, radius, mask=degraded_mask)
    
    return refined.astype(np.float32)


def apply_fixed_fractional(degraded_depth, rgb=None, degraded_mask=None, **kwargs):
    """
    Wrapper for fixed fractional filter.
    
    Args:
        degraded_depth: H x W float32 with nan.
        rgb: H x W x 3 uint8.
        degraded_mask: H x W bool.
        **kwargs: alpha, radius, iterations.
    
    Returns:
        refined_depth: H x W float32.
    """
    alpha = kwargs.get('alpha', 0.5)
    radius = kwargs.get('radius', 5)
    iterations = kwargs.get('iterations', 2)
    
    return fixed_fractional_filter(degraded_depth, rgb, degraded_mask, 
                                  alpha=alpha, radius=radius, iterations=iterations)
