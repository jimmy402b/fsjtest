"""
Traditional filtering methods for depth refinement.
"""
import numpy as np
import cv2
try:
    from . import utils
except ImportError:
    import utils


def fill_input(degraded_depth, rgb=None, degraded_mask=None):
    """
    Fill holes in degraded depth using nearest neighbor.
    Baseline method.
    
    Args:
        degraded_depth: H x W float32 with nan.
        rgb: not used.
        degraded_mask: not used.
    
    Returns:
        refined_depth: H x W float32, no nan.
    """
    return utils.fill_depth_holes(degraded_depth, method='nearest')


def median_filter(degraded_depth, rgb=None, degraded_mask=None, kernel_size=5):
    """
    Apply median filter after filling holes.
    
    Args:
        degraded_depth: H x W float32 with nan.
        rgb: not used.
        degraded_mask: not used.
        kernel_size: filter kernel size.
    
    Returns:
        refined_depth: H x W float32.
    """
    # Fill holes first
    filled = utils.fill_depth_holes(degraded_depth, method='nearest')
    
    # Apply median filter
    refined = cv2.medianBlur(filled, kernel_size)
    
    return refined.astype(np.float32)


def bilateral_filter(degraded_depth, rgb=None, degraded_mask=None, 
                     d=5, sigma_color=0.1, sigma_space=5.0):
    """
    Apply bilateral filter after filling holes.
    
    Args:
        degraded_depth: H x W float32 with nan.
        rgb: not used.
        degraded_mask: not used.
        d: diameter of each pixel neighborhood.
        sigma_color: filter sigma in the color space.
        sigma_space: filter sigma in the coordinate space.
    
    Returns:
        refined_depth: H x W float32.
    """
    # Fill holes first
    filled = utils.fill_depth_holes(degraded_depth, method='nearest')
    
    # Normalize for bilateral filter (expecting [0, 255] range for better sigma tuning)
    filled_min = np.nanmin(filled)
    filled_max = np.nanmax(filled)
    if filled_max > filled_min:
        filled_normalized = (filled - filled_min) / (filled_max - filled_min) * 255.0
    else:
        filled_normalized = filled
    
    # Apply bilateral filter
    refined_normalized = cv2.bilateralFilter(
        filled_normalized.astype(np.float32), d, sigma_color, sigma_space
    )
    
    # Denormalize
    if filled_max > filled_min:
        refined = refined_normalized / 255.0 * (filled_max - filled_min) + filled_min
    else:
        refined = refined_normalized
    
    return refined.astype(np.float32)


def guided_filter(degraded_depth, rgb, degraded_mask=None, radius=8, eps=1e-3):
    """
    Guided filter using RGB as guidance.
    
    Args:
        degraded_depth: H x W float32 with nan.
        rgb: H x W x 3 uint8 or float32 [0,1].
        degraded_mask: not used.
        radius: filter radius.
        eps: regularization epsilon.
    
    Returns:
        refined_depth: H x W float32.
    """
    # Fill holes first
    p = utils.fill_depth_holes(degraded_depth, method='nearest')
    
    # Convert RGB to grayscale as guidance image
    if rgb.dtype == np.uint8:
        rgb_float = rgb.astype(np.float32) / 255.0
    else:
        rgb_float = np.asarray(rgb, dtype=np.float32)
    
    I = 0.299 * rgb_float[:, :, 0] + 0.587 * rgb_float[:, :, 1] + 0.114 * rgb_float[:, :, 2]
    
    # Guided filter implementation
    mean_I = utils.box_filter(I, radius)
    mean_p = utils.box_filter(p, radius)
    corr_I = utils.box_filter(I * I, radius)
    corr_Ip = utils.box_filter(I * p, radius)
    
    var_I = corr_I - mean_I * mean_I
    cov_Ip = corr_Ip - mean_I * mean_p
    
    a = cov_Ip / (var_I + eps)
    b = mean_p - a * mean_I
    
    mean_a = utils.box_filter(a, radius)
    mean_b = utils.box_filter(b, radius)
    
    refined = mean_a * I + mean_b
    
    return refined.astype(np.float32)


def apply_filter(method_name, degraded_depth, rgb, degraded_mask, **kwargs):
    """
    Apply filtering method by name.
    
    Args:
        method_name: 'input_filled', 'median_filter', 'bilateral_filter', or 'guided_filter'.
        degraded_depth: H x W float32 with nan.
        rgb: H x W x 3 uint8.
        degraded_mask: H x W bool.
        **kwargs: additional parameters for specific methods.
    
    Returns:
        refined_depth: H x W float32.
    """
    if method_name == 'input_filled':
        return fill_input(degraded_depth, rgb, degraded_mask)
    elif method_name == 'median_filter':
        kernel_size = kwargs.get('kernel_size', 5)
        return median_filter(degraded_depth, rgb, degraded_mask, kernel_size=kernel_size)
    elif method_name == 'bilateral_filter':
        d = kwargs.get('d', 5)
        sigma_color = kwargs.get('sigma_color', 0.1)
        sigma_space = kwargs.get('sigma_space', 5.0)
        return bilateral_filter(degraded_depth, rgb, degraded_mask, d=d, 
                              sigma_color=sigma_color, sigma_space=sigma_space)
    elif method_name == 'guided_filter':
        radius = kwargs.get('radius', 8)
        eps = kwargs.get('eps', 1e-3)
        return guided_filter(degraded_depth, rgb, degraded_mask, radius=radius, eps=eps)
    else:
        raise ValueError(f"Unknown filter method: {method_name}")
