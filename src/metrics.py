"""
Evaluation metrics for depth refinement.
"""
import numpy as np
import cv2
from scipy import ndimage
from skimage import metrics as skmetrics


def compute_rmse(pred_depth, gt_depth, valid_mask=None):
    """Root Mean Squared Error."""
    pred = np.asarray(pred_depth, dtype=np.float32)
    gt = np.asarray(gt_depth, dtype=np.float32)
    
    if valid_mask is None:
        valid_mask = np.isfinite(gt)
    
    diff = pred[valid_mask] - gt[valid_mask]
    rmse = np.sqrt(np.mean(diff**2))
    return float(rmse) if not np.isnan(rmse) else np.nan


def compute_mae(pred_depth, gt_depth, valid_mask=None):
    """Mean Absolute Error."""
    pred = np.asarray(pred_depth, dtype=np.float32)
    gt = np.asarray(gt_depth, dtype=np.float32)
    
    if valid_mask is None:
        valid_mask = np.isfinite(gt)
    
    diff = np.abs(pred[valid_mask] - gt[valid_mask])
    mae = np.mean(diff)
    return float(mae) if not np.isnan(mae) else np.nan


def compute_absrel(pred_depth, gt_depth, valid_mask=None):
    """Absolute Relative Error."""
    pred = np.asarray(pred_depth, dtype=np.float32)
    gt = np.asarray(gt_depth, dtype=np.float32)
    
    if valid_mask is None:
        valid_mask = np.isfinite(gt)
    
    # Remove zero or very small GT values
    mask = (valid_mask) & (np.abs(gt) > 1e-6)
    
    if not np.any(mask):
        return np.nan
    
    absrel = np.mean(np.abs(pred[mask] - gt[mask]) / (np.abs(gt[mask]) + 1e-6))
    return float(absrel) if not np.isnan(absrel) else np.nan


def compute_psnr(pred_depth, gt_depth, valid_mask=None, max_depth=None):
    """Peak Signal-to-Noise Ratio."""
    pred = np.asarray(pred_depth, dtype=np.float32)
    gt = np.asarray(gt_depth, dtype=np.float32)
    
    if valid_mask is None:
        valid_mask = np.isfinite(gt)
    
    if max_depth is None:
        max_depth = np.max(gt[valid_mask])
    
    mse = np.mean((pred[valid_mask] - gt[valid_mask])**2)
    if mse == 0:
        return 100.0  # Perfect prediction
    
    psnr = 10 * np.log10(max_depth**2 / (mse + 1e-10))
    return float(psnr) if not np.isnan(psnr) else np.nan


def compute_ssim(pred_depth, gt_depth, valid_mask=None):
    """Structural Similarity Index."""
    pred = np.asarray(pred_depth, dtype=np.float32)
    gt = np.asarray(gt_depth, dtype=np.float32)
    
    if valid_mask is None:
        valid_mask = np.isfinite(gt)
    
    # Normalize to [0, 1]
    pred_valid = pred[valid_mask]
    gt_valid = gt[valid_mask]
    
    pred_min, pred_max = np.min(pred_valid), np.max(pred_valid)
    gt_min, gt_max = np.min(gt_valid), np.max(gt_valid)
    
    if pred_max > pred_min:
        pred_norm = (pred - pred_min) / (pred_max - pred_min)
    else:
        pred_norm = pred
    
    if gt_max > gt_min:
        gt_norm = (gt - gt_min) / (gt_max - gt_min)
    else:
        gt_norm = gt
    
    # Compute SSIM on valid region only
    try:
        ssim = skmetrics.structural_similarity(pred_norm, gt_norm, data_range=1.0)
        return float(ssim)
    except:
        return np.nan


def compute_edge_rmse(pred_depth, gt_depth, valid_mask=None, edge_dilation=3):
    """RMSE computed only on depth edges."""
    pred = np.asarray(pred_depth, dtype=np.float32)
    gt = np.asarray(gt_depth, dtype=np.float32)
    
    if valid_mask is None:
        valid_mask = np.isfinite(gt)
    
    # Compute depth edges
    gx = cv2.Sobel(gt, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(gt, cv2.CV_32F, 0, 1, ksize=3)
    edges = np.sqrt(gx**2 + gy**2)
    
    # Threshold
    edge_threshold = np.percentile(edges[valid_mask], 75) if np.any(valid_mask) else 0.1
    edge_mask = edges > edge_threshold
    
    # Dilate edge mask
    edge_mask = cv2.dilate(edge_mask.astype(np.uint8), 
                           cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)), 
                           iterations=edge_dilation).astype(bool)
    
    # Combine masks
    eval_mask = edge_mask & valid_mask
    
    if not np.any(eval_mask):
        return np.nan
    
    diff = pred[eval_mask] - gt[eval_mask]
    edge_rmse = np.sqrt(np.mean(diff**2))
    return float(edge_rmse) if not np.isnan(edge_rmse) else np.nan


def compute_all_metrics(pred_depth, gt_depth, valid_mask=None, max_depth=None):
    """
    Compute all depth metrics.
    
    Args:
        pred_depth: H x W float32 predicted depth.
        gt_depth: H x W float32 ground truth depth.
        valid_mask: H x W bool valid pixels.
        max_depth: float for PSNR computation.
    
    Returns:
        dict with all metrics.
    """
    if valid_mask is None:
        valid_mask = np.isfinite(gt_depth)
    
    if not np.any(valid_mask):
        return {
            'RMSE': np.nan,
            'MAE': np.nan,
            'AbsRel': np.nan,
            'PSNR': np.nan,
            'SSIM': np.nan,
            'Edge_RMSE': np.nan,
        }
    
    return {
        'RMSE': compute_rmse(pred_depth, gt_depth, valid_mask),
        'MAE': compute_mae(pred_depth, gt_depth, valid_mask),
        'AbsRel': compute_absrel(pred_depth, gt_depth, valid_mask),
        'PSNR': compute_psnr(pred_depth, gt_depth, valid_mask, max_depth),
        'SSIM': compute_ssim(pred_depth, gt_depth, valid_mask),
        'Edge_RMSE': compute_edge_rmse(pred_depth, gt_depth, valid_mask),
    }
