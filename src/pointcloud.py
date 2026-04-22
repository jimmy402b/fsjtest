"""
Point cloud utilities and metrics.
"""
import numpy as np
import warnings


def depth_to_pointcloud(depth, intrinsics, mask=None):
    """
    Convert depth map to point cloud.
    
    Args:
        depth: H x W float32 depth map.
        intrinsics: 3x3 camera intrinsic matrix.
        mask: H x W bool valid pixels (optional).
    
    Returns:
        points: N x 3 float32 point cloud (X, Y, Z).
    """
    depth = np.asarray(depth, dtype=np.float32)
    
    if mask is None:
        mask = np.isfinite(depth)
    
    H, W = depth.shape
    fx = intrinsics[0, 0]
    fy = intrinsics[1, 1]
    cx = intrinsics[0, 2]
    cy = intrinsics[1, 2]
    
    # Create grid
    v, u = np.meshgrid(np.arange(W), np.arange(H))
    
    # Unproject
    Z = depth
    X = (u - cx) * Z / fx
    Y = (v - cy) * Z / fy
    
    # Stack and filter by mask
    points_homogeneous = np.stack([X, Y, Z], axis=-1).reshape(-1, 3)
    mask_flat = mask.reshape(-1)
    points = points_homogeneous[mask_flat]
    
    return points.astype(np.float32)


def sample_pointcloud(points, max_points=20000, seed=None):
    """
    Randomly sample point cloud to max_points.
    
    Args:
        points: N x 3 float32.
        max_points: maximum number of points.
        seed: random seed.
    
    Returns:
        sampled_points: min(N, max_points) x 3 float32.
    """
    if seed is not None:
        np.random.seed(seed)
    
    points = np.asarray(points, dtype=np.float32)
    
    if len(points) <= max_points:
        return points
    
    indices = np.random.choice(len(points), size=max_points, replace=False)
    return points[indices]


def chamfer_distance(points_pred, points_gt, max_points=20000):
    """
    Compute symmetric Chamfer distance between two point clouds.
    
    Args:
        points_pred: N1 x 3 float32 predicted points.
        points_gt: N2 x 3 float32 ground truth points.
        max_points: maximum points for sampling.
    
    Returns:
        chamfer_dist: float, symmetric Chamfer distance.
    """
    points_pred = np.asarray(points_pred, dtype=np.float32)
    points_gt = np.asarray(points_gt, dtype=np.float32)
    
    # Check for empty clouds
    if len(points_pred) == 0 or len(points_gt) == 0:
        warnings.warn("Empty point cloud for Chamfer distance")
        return np.nan
    
    # Sample
    points_pred = sample_pointcloud(points_pred, max_points)
    points_gt = sample_pointcloud(points_gt, max_points)
    
    # Compute distances using scipy KDTree
    try:
        from scipy.spatial import cKDTree
    except ImportError:
        warnings.warn("scipy.spatial.cKDTree not available, returning nan")
        return np.nan
    
    tree_gt = cKDTree(points_gt)
    tree_pred = cKDTree(points_pred)
    
    # Distance from pred to gt
    dist_pred_to_gt, _ = tree_gt.query(points_pred)
    
    # Distance from gt to pred
    dist_gt_to_pred, _ = tree_pred.query(points_gt)
    
    # Symmetric Chamfer
    chamfer_dist = np.mean(dist_pred_to_gt) + np.mean(dist_gt_to_pred)
    
    return float(chamfer_dist)


def outlier_ratio(points_pred, points_gt, threshold=0.02):
    """
    Compute outlier ratio: percentage of pred points far from gt.
    
    Args:
        points_pred: N1 x 3 float32 predicted points.
        points_gt: N2 x 3 float32 ground truth points.
        threshold: distance threshold in meters.
    
    Returns:
        outlier_ratio: float in [0, 1].
    """
    points_pred = np.asarray(points_pred, dtype=np.float32)
    points_gt = np.asarray(points_gt, dtype=np.float32)
    
    # Check for empty clouds
    if len(points_pred) == 0:
        warnings.warn("Empty predicted point cloud for outlier ratio")
        return np.nan
    
    if len(points_gt) == 0:
        warnings.warn("Empty ground truth point cloud for outlier ratio")
        return np.nan
    
    try:
        from scipy.spatial import cKDTree
    except ImportError:
        warnings.warn("scipy.spatial.cKDTree not available, returning nan")
        return np.nan
    
    tree_gt = cKDTree(points_gt)
    
    # Query distance to nearest neighbor
    distances, _ = tree_gt.query(points_pred)
    
    # Count outliers
    outliers = distances > threshold
    outlier_ratio = np.sum(outliers) / len(points_pred)
    
    return float(outlier_ratio)


def compute_all_pc_metrics(pred_depth, gt_depth, intrinsics, valid_mask=None):
    """
    Compute all point cloud metrics.
    
    Args:
        pred_depth: H x W float32 predicted depth.
        gt_depth: H x W float32 ground truth depth.
        intrinsics: 3x3 camera intrinsic matrix.
        valid_mask: H x W bool valid pixels in GT.
    
    Returns:
        dict with Chamfer and OutlierRatio.
    """
    if valid_mask is None:
        valid_mask = np.isfinite(gt_depth)
    
    # Convert to point clouds
    points_pred = depth_to_pointcloud(pred_depth, intrinsics)
    points_gt = depth_to_pointcloud(gt_depth, intrinsics, mask=valid_mask)
    
    if len(points_pred) == 0 or len(points_gt) == 0:
        return {
            'Chamfer': np.nan,
            'OutlierRatio': np.nan,
        }
    
    return {
        'Chamfer': chamfer_distance(points_pred, points_gt),
        'OutlierRatio': outlier_ratio(points_pred, points_gt),
    }
