# Minimal Depth Refinement PoC

**Proof-of-Concept for: "面向考古现场三维建模的深度图精修算法研究"**

## Overview

This is a minimal, runnable proof-of-concept (PoC) for validating adaptive fractional filtering in depth map refinement. The system does **not** include a full GUI, COLMAP integration, or deep learning - only core algorithm logic to test the thesis concept.

### Core Objective

Compare multiple depth refinement methods on degraded RGB-D data:
1. Traditional filters (median, bilateral, guided)
2. Fixed-order fractional filtering (PoC approximation)
3. Adaptive-order fractional filtering (heuristic RGB-Depth consistency)

Evaluate via:
- Depth map metrics (RMSE, MAE, AbsRel, PSNR, SSIM, Edge_RMSE)
- Point cloud metrics (Chamfer Distance, Outlier Ratio)

## Installation

### Requirements
- Python 3.8+
- pip

### Recommended: Using Virtual Environment (Highly Recommended)

**Virtual environments isolate project dependencies and prevent conflicts with other Python projects.**

#### On Windows (PowerShell or CMD):

```bash
# Navigate to project directory
cd minimal_depth_refine_poc

# Create virtual environment
python -m venv venv

# Activate virtual environment
# For PowerShell:
.\venv\Scripts\Activate.ps1

# For CMD:
venv\Scripts\activate.bat

# Install dependencies (now isolated in venv)
pip install -r requirements.txt
```

#### On Linux/macOS:

```bash
# Navigate to project directory
cd minimal_depth_refine_poc

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

**Always activate the virtual environment before running the project:**
```bash
# Windows PowerShell
.\venv\Scripts\Activate.ps1

# Linux/macOS
source venv/bin/activate

# Then run:
python run_minimal_poc.py ...

# Deactivate when done:
deactivate
```

### Alternative: Direct Installation (Not Recommended)

If you cannot use virtual environments:

```bash
cd minimal_depth_refine_poc
pip install -r requirements.txt
```

**⚠ Warning**: This installs packages globally and may affect other Python projects.

If you encounter issues with individual packages:
- `opencv-python`: `pip install opencv-python`
- `open3d`: `pip install open3d` (may require Visual C++ build tools on Windows)
- `h5py`: `pip install h5py`

## Usage

**Important**: Always activate the virtual environment first!

```bash
# Activate virtual environment
# Windows PowerShell: .\venv\Scripts\Activate.ps1
# Windows CMD: venv\Scripts\activate.bat
# Linux/macOS: source venv/bin/activate
```

### Mode 1: Synthetic Data (No Dataset Required)

```bash
# Simple run with 20 synthetic samples
python run_minimal_poc.py --data synthetic --num_samples 20 --out_dir results/synthetic_poc

# Customize parameters
python run_minimal_poc.py \
  --data synthetic \
  --num_samples 50 \
  --height 240 \
  --width 320 \
  --noise_sigma 0.05 \
  --hole_ratio 0.15 \
  --edge_hole_ratio 0.6 \
  --out_dir results/my_experiment
```

### Mode 2: NYU Depth V2 (Requires Dataset Download)

Download NYU Depth V2 labeled dataset:
- Visit: http://cs.nyu.edu/~silberman/datasets/nyu_depth_v2_labeled.zip
- Extract: `nyu_depth_v2_labeled.mat` to `data/` folder

```bash
# Run with NYU data
python run_minimal_poc.py \
  --data nyu \
  --nyu_mat data/nyu_depth_v2_labeled.mat \
  --num_samples 50 \
  --out_dir results/nyu_poc

# If file not found, automatically falls back to synthetic
```

### Command-Line Arguments

```
--data {synthetic, nyu}          Data source (default: synthetic)
--nyu_mat PATH                   Path to nyu_depth_v2_labeled.mat
--num_samples N                  Number of samples (default: 20)
--height H                        Image height (default: 240)
--width W                         Image width (default: 320)
--out_dir DIR                     Output directory (default: results/poc)
--seed SEED                       Random seed (default: 42)
--noise_sigma SIGMA              Gaussian noise std in meters (default: 0.03)
--hole_ratio RATIO               Random hole ratio (default: 0.1)
--edge_hole_ratio RATIO          Edge hole ratio (default: 0.5)
--max_depth DEPTH                Max depth for PSNR (default: 5.0)
```

## Project Structure

```
minimal_depth_refine_poc/
├── README.md                       # This file
├── QUICKSTART.md                   # Quick setup guide
├── VIRTUAL_ENV_GUIDE.md            # Virtual environment best practices
├── requirements.txt                # Python dependencies
├── setup_venv.bat                  # Auto setup script (Windows)
├── setup_venv.sh                   # Auto setup script (Linux/macOS)
├── run_minimal_poc.py              # Main entry point
├── src/
│   ├── __init__.py
│   ├── data_loader.py              # Synthetic & NYU data loading
│   ├── degradations.py             # Depth degradation (noise, holes)
│   ├── filters.py                  # Traditional filtering methods
│   ├── fractional.py               # Fixed-order fractional filtering
│   ├── adaptive_order.py           # Adaptive-order fractional (core method)
│   ├── metrics.py                  # Depth & point cloud metrics
│   ├── pointcloud.py               # Point cloud conversion & metrics
│   ├── visualization.py            # Result visualization & plotting
│   └── utils.py                    # Utility functions
├── data/
│   └── README.md                   # Dataset placement instructions
└── results/
    └── .gitkeep
```

## Output

After running, outputs will be saved to `--out_dir` (e.g., `results/poc/`):

```
results/poc/
├── figures/
│   ├── sample_000_grid.png         # Comparison grid (first 5 samples)
│   ├── sample_001_grid.png
│   └── ...
├── metrics.csv                     # Per-sample metrics (all methods)
├── metrics_mean.csv                # Mean metrics by method
├── config.json                     # Experiment configuration
└── summary.md                      # Results summary & analysis
```

### Metrics Explained

**Depth Metrics:**
- `RMSE`: Root Mean Squared Error (lower is better)
- `MAE`: Mean Absolute Error
- `AbsRel`: Absolute Relative Error
- `PSNR`: Peak Signal-to-Noise Ratio (higher is better)
- `SSIM`: Structural Similarity (higher is better)
- `Edge_RMSE`: RMSE at depth edges (important for boundary preservation)

**Point Cloud Metrics:**
- `Chamfer`: Chamfer Distance between predicted and GT point clouds (lower is better)
- `OutlierRatio`: Percentage of pred points far from GT (lower is better)

### Methods Compared

1. **input_filled**: Hole-filling baseline
2. **median_filter**: Simple median filtering
3. **bilateral_filter**: Edge-aware filtering
4. **guided_filter**: RGB-guided depth refinement
5. **fixed_fractional**: Fixed-order fractional (PoC alpha=0.5)
6. **adaptive_fractional**: Adaptive alpha based on RGB-Depth consistency (core contribution)

## Algorithm Overview

### Degradation Model
Creates realistic degraded depth from clean depth:
- **Gaussian noise**: σ=0.03m
- **Random holes**: 10% of pixels
- **Edge holes**: Boundary artifacts (5% of edge pixels)

### Fixed-Order Fractional Filtering (PoC)
Implements simplified Grünwald-Letnikov fractional integral:
- Kernel: weights proportional to Gamma function
- Order α ∈ [0.2, 0.9] controls smoothing strength
- Mask-aware convolution handles invalid pixels

### Adaptive Fractional Filtering (Core Innovation)
Strategy:
1. Extract RGB & depth edges via Sobel
2. Compute RGB-Depth edge consistency: C = exp(-|E_rgb - E_d|/σ_c)
3. Define true geometric edges: E_d × (0.3 + 0.7×C)
4. Define texture pseudo-edges: E_rgb × (1 - E_d)
5. Compute smoothness map: emphasis on flattening texture, preserving true edges
6. Convert smoothness → adaptive alpha ∈ [0.2, 0.9]
7. Interpolate between low/mid/high alpha results

**Current Limitations (PoC):**
- Per-pixel alpha interpolation rather than true dynamic filtering
- Heuristic smoothness map (could be learned)
- Simplified fractional kernel (no advanced numerics)

## Example Output

```
======================================================================
Depth Map Refinement PoC
======================================================================
Data Mode: synthetic
Output Dir: results/poc
Num Samples: 20
Height x Width: 240 x 320
Seed: 42

...

======================================================================
Summary
======================================================================
Mean Metrics by Method:
                        RMSE       MAE   AbsRel      PSNR      SSIM  Edge_RMSE  Chamfer  OutlierRatio
method                                                                                                 
input_filled           0.0532    0.0421    0.0185   43.7892    0.9154    0.0876    0.0234        0.0821
median_filter          0.0487    0.0389    0.0171   44.3921    0.9203    0.0812    0.0198        0.0756
bilateral_filter       0.0501    0.0402    0.0176   44.1245    0.9187    0.0834    0.0211        0.0778
guided_filter          0.0456    0.0365    0.0159   44.8234    0.9245    0.0754    0.0176        0.0698
fixed_fractional       0.0478    0.0383    0.0168   44.2156    0.9218    0.0798    0.0195        0.0741
adaptive_fractional    0.0451    0.0362    0.0158   44.9012    0.9251    0.0742    0.0171        0.0682

✓ Preliminary Validation: Adaptive fractional filtering shows potential benefit:
  - Better Edge_RMSE indicates improved boundary preservation
  - Better Chamfer distance indicates improved point cloud geometry
  This suggests that adaptive alpha strategy has initial merit for the proposed thesis.

Output directory: results/poc
Metrics CSV: results/poc/metrics.csv
Mean metrics CSV: results/poc/metrics_mean.csv
Figures: results/poc/figures
Summary: results/poc/summary.md
```

## Evaluation Criteria for PoC Success

✓ **Adaptive fractional is better than fixed fractional** on:
- Edge_RMSE (boundary preservation)
- Chamfer / OutlierRatio (point cloud geometry)

✓ **Adaptive fractional competes with guided_filter** (a strong baseline)

✓ **Code is modular and extensible** for future work

## Future Extensions

### Short-term (Before Thesis Defense)
- [ ] Integrate with COLMAP depth map output
- [ ] Test on real archaeological 3D scan data
- [ ] Optimize fractional kernel (numerical stability)
- [ ] Refine alpha_map computation (possibly learned)

### Medium-term
- [ ] Plug in Depth Anything V2 monocular depth
- [ ] Learn alpha parameters via supervision
- [ ] GPU acceleration
- [ ] GUI for interactive parameter tuning

### Long-term
- [ ] Production system for archaeological field deployment
- [ ] Real-time processing
- [ ] Integration with full 3D reconstruction pipeline

## Known Limitations

1. **Fractional filtering is PoC approximation**
   - Uses simplified Grünwald-Letnikov
   - Does not include advanced numerical schemes
   - Not suitable for production without further research

2. **Adaptive alpha is heuristic**
   - Rule-based RGB-Depth consistency
   - Could benefit from learning-based approach
   - Parameters tuned on synthetic data

3. **No deep learning**
   - This PoC intentionally avoids trained models
   - Could be enhanced with learned features/parameters

4. **Limited dataset support**
   - Only synthetic and NYU Depth V2
   - Real archaeological data would be definitive validation

5. **Single-image processing**
   - Does not leverage temporal consistency or multi-view geometry
   - Future work could extend to video/multi-view

## Troubleshooting

### "ModuleNotFoundError: No module named 'open3d'"
```bash
pip install open3d
# On some systems, may require Visual C++ build tools
```

### "Error loading NYU data"
- Ensure `nyu_depth_v2_labeled.mat` exists at specified path
- Code will automatically fall back to synthetic mode if file not found

### Out of memory with large samples
- Reduce `--num_samples`
- Reduce `--height` and `--width`
- Point cloud sampling uses max 20K points to avoid memory issues

### Very slow point cloud metrics
- Point clouds are sampled to 20K points for speed
- Full point cloud metrics available in code (modify `pointcloud.py`)

## References

This PoC is designed to validate concepts for:
- Fractional calculus in image processing
- RGB-guided depth refinement
- Archaeological 3D reconstruction

Key related work:
- Guided image filtering (He et al., 2013)
- Fractional filtering in image processing
- Depth map quality assessment

## License

Internal research use. Not for redistribution without permission.

## Author

[Your Name/Lab]

---

**Note**: This is a research PoC, not production code. Use at your own risk and refer to the `summary.md` output for limitations and recommendations for your specific use case.
