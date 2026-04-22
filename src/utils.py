"""
Utility functions for depth map refinement PoC.
"""
import numpy as np
import cv2
from scipy import ndimage


def fill_depth_holes(depth, method='nearest'):
    """
    Fill holes (nan values) in depth map.
    
    Args:
        depth: H x W float32 depth map with nan as holes.
        method: 'nearest' or 'mean'.
    
    Returns:
        filled_depth: H x W float32, nan-free.
    """
    depth = np.asarray(depth, dtype=np.float32)
    mask = np.isfinite(depth)
    
    if np.all(mask):
        return depth.copy()
    
    if method == 'nearest':
        # Use distance transform for nearest neighbor fill
        filled = depth.copy()
        invalid = ~mask
        if np.any(invalid):
            indices = ndimage.distance_transform_edt(invalid, return_distances=False, return_indices=True)
            # indices shape: (2, H, W), where indices[0] = row, indices[1] = col
            filled[invalid] = depth[indices[0][invalid], indices[1][invalid]]
        return filled
    
    elif method == 'mean':
        filled = depth.copy()
        kernel_size = 5
        for _ in range(3):
            invalid = ~np.isfinite(filled)
            if not np.any(invalid):
                break
            filled_padded = cv2.copyMakeBorder(filled, 2, 2, 2, 2, cv2.BORDER_REFLECT)
            valid_mask = cv2.copyMakeBorder(np.isfinite(filled).astype(np.float32), 2, 2, 2, 2, cv2.BORDER_CONSTANT, value=0)
            
            mean_val = cv2.blur(filled_padded, (kernel_size, kernel_size))
            count_val = cv2.blur(valid_mask, (kernel_size, kernel_size))
            
            mean_val = mean_val[2:-2, 2:-2]
            count_val = count_val[2:-2, 2:-2]
            
            mean_val = np.where(count_val > 0, mean_val / count_val, 0)
            filled[invalid] = mean_val[invalid]
        
        return filled
    
    else:
        raise ValueError(f"Unknown fill method: {method}")


def normalize_depth(depth, mask=None, depth_min=None, depth_max=None):
    """
    Normalize depth to [0, 1] range.
    
    Args:
        depth: H x W float32.
        mask: H x W bool, valid pixels.
        depth_min: float, minimum for normalization.
        depth_max: float, maximum for normalization.
    
    Returns:
        normalized: H x W float32 in [0, 1].
    """
    depth = np.asarray(depth, dtype=np.float32)
    if mask is None:
        mask = np.isfinite(depth)
    
    valid_depth = depth[mask]
    if valid_depth.size == 0:
        return np.zeros_like(depth)
    
    if depth_min is None:
        depth_min = np.min(valid_depth)
    if depth_max is None:
        depth_max = np.max(valid_depth)
    
    if depth_max <= depth_min:
        return np.zeros_like(depth)
    
    normalized = (depth - depth_min) / (depth_max - depth_min)
    normalized = np.clip(normalized, 0, 1)
    return normalized.astype(np.float32)


def get_depth_edges(depth, method='sobel', mask=None):
    """
    Extract depth edges using gradient.
    
    Args:
        depth: H x W float32.
        method: 'sobel' or 'laplacian'.
        mask: H x W bool, valid pixels.
    
    Returns:
        edges: H x W float32 in [0, 1], normalized edge magnitude.
    """
    depth = np.asarray(depth, dtype=np.float32)
    
    if mask is not None:
        depth_filled = depth.copy()
        filled_mask = np.isfinite(depth)
        if not np.all(filled_mask):
            depth_filled = fill_depth_holes(depth)
        depth = depth_filled
    
    if method == 'sobel':
        gx = cv2.Sobel(depth, cv2.CV_32F, 1, 0, ksize=3)
        gy = cv2.Sobel(depth, cv2.CV_32F, 0, 1, ksize=3)
        edges = np.sqrt(gx**2 + gy**2)
    elif method == 'laplacian':
        edges = np.abs(cv2.Laplacian(depth, cv2.CV_32F))
    else:
        raise ValueError(f"Unknown method: {method}")
    
    edges_max = np.max(edges)
    if edges_max > 0:
        edges = edges / edges_max
    
    return edges.astype(np.float32)


def get_rgb_edges(rgb, method='sobel'):
    """
    Extract RGB edges (grayscale).
    
    Args:
        rgb: H x W x 3 uint8 or float32.
        method: 'sobel'.
    
    Returns:
        edges: H x W float32 in [0, 1].
    """
    if rgb.dtype == np.uint8:
        rgb = rgb.astype(np.float32) / 255.0
    
    # Convert to grayscale
    gray = 0.299 * rgb[:, :, 0] + 0.587 * rgb[:, :, 1] + 0.114 * rgb[:, :, 2]
    
    if method == 'sobel':
        gx = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
        gy = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
        edges = np.sqrt(gx**2 + gy**2)
    else:
        raise ValueError(f"Unknown method: {method}")
    
    edges_max = np.max(edges)
    if edges_max > 0:
        edges = edges / edges_max
    
    return edges.astype(np.float32)


def box_filter(img, radius):
    """
    Simple box filter (mean filter).
    
    Args:
        img: H x W image.
        radius: filter radius.
    
    Returns:
        filtered: H x W.
    """
    kernel_size = 2 * radius + 1
    return cv2.blur(img, (kernel_size, kernel_size))


def create_intrinsics(fx, fy, cx, cy):
    """
    Create camera intrinsic matrix.
    
    Args:
        fx, fy: focal lengths.
        cx, cy: principal point.
    
    Returns:
        K: 3 x 3 intrinsic matrix.
    """
    K = np.array([
        [fx, 0, cx],
        [0, fy, cy],
        [0, 0, 1]
    ], dtype=np.float32)
    return K


def ensure_uint8(img):
    """Convert image to uint8 for visualization."""
    if img.dtype == np.uint8:
        return img
    if img.dtype == np.float32 or img.dtype == np.float64:
        img = np.clip(img * 255, 0, 255)
    return img.astype(np.uint8)


def resize_with_mask(depth, mask, size):
    """
    Resize depth and mask to target size.
    
    Args:
        depth: H x W depth map.
        mask: H x W mask.
        size: (H_new, W_new).
    
    Returns:
        resized_depth, resized_mask.
    """
    h_new, w_new = size
    depth_resized = cv2.resize(depth, (w_new, h_new), interpolation=cv2.INTER_LINEAR)
    mask_resized = cv2.resize(mask.astype(np.float32), (w_new, h_new), interpolation=cv2.INTER_NEAREST)
    mask_resized = mask_resized.astype(bool)
    return depth_resized, mask_resized


def dilate_mask(mask, kernel_size=5, iterations=1):
    """
    Dilate a binary mask.
    
    Args:
        mask: H x W bool.
        kernel_size: kernel size.
        iterations: number of iterations.
    
    Returns:
        dilated: H x W bool.
    """
    mask = mask.astype(np.uint8)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
    dilated = cv2.dilate(mask, kernel, iterations=iterations)
    return dilated.astype(bool)


def print_section(title):
    """Print a formatted section header."""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")
