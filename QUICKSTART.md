# Quick Start Guide

## ⚡ Fast Setup with Virtual Environment (Recommended)

### Windows

```powershell
# 1. Navigate to project
cd minimal_depth_refine_poc

# 2. Run setup script (one-click setup)
.\setup_venv.bat

# This will automatically create venv and activate it

# 3. Run an experiment
python run_minimal_poc.py --data synthetic --num_samples 10 --out_dir results/test

# 4. When done, deactivate virtual environment
deactivate
```

### Linux / macOS

```bash
# 1. Navigate to project
cd minimal_depth_refine_poc

# 2. Make script executable and run
chmod +x setup_venv.sh
./setup_venv.sh

# This will automatically create venv and activate it

# 3. Run an experiment
python run_minimal_poc.py --data synthetic --num_samples 10 --out_dir results/test

# 4. When done, deactivate virtual environment
deactivate
```

## Manual Virtual Environment Setup

If you prefer to set up manually:

### Windows (PowerShell)

```powershell
# Create
python -m venv venv

# Activate
.\venv\Scripts\Activate.ps1

# Install
pip install -r requirements.txt

# Run
python run_minimal_poc.py --data synthetic --num_samples 10 --out_dir results/test

# Deactivate
deactivate
```

### Windows (CMD)

```cmd
python -m venv venv
venv\Scripts\activate.bat
pip install -r requirements.txt
python run_minimal_poc.py --data synthetic --num_samples 10 --out_dir results/test
deactivate
```

### Linux / macOS

```bash
# Create
python3 -m venv venv

# Activate
source venv/bin/activate

# Install
pip install -r requirements.txt

# Run
python run_minimal_poc.py --data synthetic --num_samples 10 --out_dir results/test

# Deactivate
deactivate
```

## Verify Installation

After activation, verify dependencies are installed:

```bash
python -c "import numpy, cv2, scipy, skimage, open3d, pandas; print('✓ All dependencies OK')"
```

## Common Issues

### Issue: "ModuleNotFoundError: No module named 'cv2'"

**Solution**: Ensure virtual environment is activated before installing

```bash
# Check if venv is active (should show venv path)
where python  # Windows
which python  # Linux/macOS

# If not in venv, activate it first:
# Windows: .\venv\Scripts\Activate.ps1
# Linux/macOS: source venv/bin/activate

# Then install
pip install -r requirements.txt
```

### Issue: Virtual environment won't activate on PowerShell

PowerShell execution policy might block scripts. Try:

```powershell
# Allow script execution for current user
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Then activate
.\venv\Scripts\Activate.ps1
```

### Issue: "python: command not found" on Linux/macOS

Use `python3` instead:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python run_minimal_poc.py ...
```

## Example: Running First Experiment

```bash
# 1. Activate venv (one-time per session)
# Windows PowerShell: .\venv\Scripts\Activate.ps1
# Linux/macOS: source venv/bin/activate

# 2. Run minimal synthetic experiment
python run_minimal_poc.py \
  --data synthetic \
  --num_samples 5 \
  --height 128 \
  --width 160 \
  --out_dir results/first_test \
  --seed 42

# 3. Check results
# Results saved to: results/first_test/
# View summary: results/first_test/summary.md
# View figures: results/first_test/figures/
```

## Next Steps

See `README.md` for full documentation and command-line arguments.
