"""
Data loader for synthetic and NYU Depth V2 datasets.
"""
import numpy as np
import cv2
import os
from tqdm import tqdm


def generate_synthetic_sample(height=240, width=320, seed=None):
    """
    Generate a single synthetic RGB-D sample.
    
    Args:
        height: image height.
        width: image width.
        seed: random seed.
    
    Returns:
        rgb: H x W x 3 uint8.
        depth: H x W float32 (in meters).
        valid_mask: H x W bool.
    """
    if seed is not None:
        np.random.seed(seed)
    
    # Create depth map with multiple objects
    depth = np.ones((height, width), dtype=np.float32) * 2.0
    
    # Add a plane at z=2.0
    depth[:height//2, :] = 2.0
    
    # Add a step
    depth[height//2:, :] = 3.0
    
    # Add a circular object
    cy, cx = height // 3, width // 3
    y, x = np.ogrid[:height, :width]
    circle = (x - cx)**2 + (y - cy)**2 <= (height // 8)**2
    depth[circle] = 1.5
    
    # Add a rectangular object
    x1, y1, x2, y2 = width // 2, height // 2, width - 50, height - 50
    depth[y1:y2, x1:x2] = 1.0
    
    # Create RGB with simple patterns
    rgb = np.zeros((height, width, 3), dtype=np.uint8)
    
    # Background: blue
    rgb[depth > 2.5] = [200, 150, 100]  # BGR
    
    # Mid-plane: green
    rgb[(depth >= 1.9) & (depth < 2.5)] = [100, 200, 100]
    
    # Circle: red
    rgb[circle] = [50, 100, 200]
    
    # Rectangle: yellow
    rgb[y1:y2, x1:x2] = [0, 255, 255]
    
    # Add texture
    texture = (np.random.rand(height, width) * 30).astype(np.uint8)
    for c in range(3):
        rgb[:, :, c] = np.clip(rgb[:, :, c].astype(np.int32) + texture, 0, 255).astype(np.uint8)
    
    # Valid mask
    valid_mask = np.ones((height, width), dtype=bool)
    
    return rgb, depth, valid_mask


def load_nyu_depth_v2(mat_path, num_samples=20, height=240, width=320):
    """
    Load NYU Depth V2 dataset from .mat file.
    
    Args:
        mat_path: path to nyu_depth_v2_labeled.mat.
        num_samples: number of samples to load.
        height: target height.
        width: target width.
    
    Returns:
        list of (rgb, depth, valid_mask) tuples.
        Returns None if file not found or h5py error.
    """
    if not os.path.exists(mat_path):
        print(f"[Warning] NYU mat file not found: {mat_path}")
        return None
    
    try:
        import h5py
    except ImportError:
        print("[Warning] h5py not installed, cannot load NYU data")
        return None
    
    try:
        with h5py.File(mat_path, 'r') as f:
            images = f['images']
            depths = f['depths']

            print(f"[Info] NYU images shape: {images.shape}, depths shape: {depths.shape}")

            # Support common layouts:
            # images: (3, H, W, N) or (N, 3, H, W) / (N, 3, W, H)
            if images.ndim != 4 or depths.ndim != 3:
                raise ValueError(f"Unexpected NYU dimensions: images={images.shape}, depths={depths.shape}")

            if images.shape[0] == 3:
                total_samples = images.shape[3]

                def get_image(i):
                    return np.array(images[:, :, :, i])
            elif images.shape[1] == 3:
                total_samples = images.shape[0]

                def get_image(i):
                    return np.array(images[i, :, :, :])
            else:
                raise ValueError(f"Cannot identify channel axis in images shape: {images.shape}")

            # depths: (H, W, N) or (N, H, W) / (N, W, H)
            if depths.shape[2] == total_samples:
                def get_depth(i):
                    return np.array(depths[:, :, i], dtype=np.float32)
            elif depths.shape[0] == total_samples:
                def get_depth(i):
                    return np.array(depths[i, :, :], dtype=np.float32)
            else:
                raise ValueError(
                    f"Cannot identify sample axis in depths shape: {depths.shape}, total_samples={total_samples}"
                )

            samples = []
            for idx in tqdm(range(min(num_samples, total_samples)), desc="Loading NYU samples"):
                img_chw = get_image(idx)
                if img_chw.shape[0] != 3:
                    raise ValueError(f"Unexpected image sample shape: {img_chw.shape}")

                # Normalize orientation to (3, H, W). Some files store (3, W, H).
                if img_chw.shape[1] == 640 and img_chw.shape[2] == 480:
                    img_chw = np.transpose(img_chw, (0, 2, 1))
                elif not (img_chw.shape[1] == 480 and img_chw.shape[2] == 640):
                    # Fallback for unusual orientation: keep the smaller dim as H.
                    if img_chw.shape[1] > img_chw.shape[2]:
                        img_chw = np.transpose(img_chw, (0, 2, 1))

                rgb = np.transpose(img_chw, (1, 2, 0))
                if rgb.dtype != np.uint8:
                    if np.nanmax(rgb) <= 1.5:
                        rgb = np.clip(rgb * 255.0, 0, 255)
                    rgb = rgb.astype(np.uint8)

                depth = get_depth(idx)
                if depth.shape == (640, 480):
                    depth = depth.T
                elif depth.shape[0] > depth.shape[1]:
                    depth = depth.T

                # NYU depth is often in mm; auto-convert when values look like mm scale.
                if np.nanmax(depth) > 20.0:
                    depth = depth / 1000.0

                valid_mask = (depth > 0)
                depth[~valid_mask] = np.nan

                rgb_resized = cv2.resize(rgb, (width, height), interpolation=cv2.INTER_LINEAR)
                depth_resized = cv2.resize(depth, (width, height), interpolation=cv2.INTER_LINEAR)
                valid_mask_resized = cv2.resize(
                    valid_mask.astype(np.float32), (width, height), interpolation=cv2.INTER_NEAREST
                ) > 0.5

                samples.append((rgb_resized, depth_resized, valid_mask_resized))

            return samples
    
    except Exception as e:
        print(f"[Warning] Error loading NYU data: {e}")
        return None


def load_dataset(data_mode, nyu_mat=None, num_samples=20, height=240, width=320, seed=42):
    """
    Load dataset in specified mode.
    
    Args:
        data_mode: 'synthetic' or 'nyu'.
        nyu_mat: path to NYU mat file (if data_mode='nyu').
        num_samples: number of samples.
        height: image height.
        width: image width.
        seed: random seed for synthetic.
    
    Returns:
        list of (rgb, depth, valid_mask) tuples.
    """
    if data_mode == 'synthetic':
        print(f"Generating {num_samples} synthetic samples...")
        samples = []
        for i in tqdm(range(num_samples), desc="Synthetic"):
            rgb, depth, mask = generate_synthetic_sample(height, width, seed=seed + i)
            samples.append((rgb, depth, mask))
        return samples
    
    elif data_mode == 'nyu':
        print(f"Loading NYU Depth V2 from {nyu_mat}...")
        samples = load_nyu_depth_v2(nyu_mat, num_samples, height, width)
        if samples is None:
            print("[Info] Falling back to synthetic mode...")
            return load_dataset('synthetic', num_samples=num_samples, height=height, width=width, seed=seed)
        return samples
    
    else:
        raise ValueError(f"Unknown data_mode: {data_mode}")
