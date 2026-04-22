#!/bin/bash
# Setup script for Linux/macOS - Creates and activates virtual environment

echo ""
echo "======================================================================"
echo "  Depth Refinement PoC - Setup Script (Linux/macOS)"
echo "======================================================================"
echo ""

if [ -d "venv" ]; then
    echo "[*] Virtual environment already exists at: venv"
    echo "[*] Activating..."
    source venv/bin/activate
    echo "[✓] Activated. You can now run: python run_minimal_poc.py"
    exit 0
fi

echo "[*] Creating virtual environment..."
python3 -m venv venv

if [ ! -d "venv" ]; then
    echo "[✗] Failed to create virtual environment"
    exit 1
fi

echo "[✓] Virtual environment created"

echo "[*] Activating virtual environment..."
source venv/bin/activate

echo "[*] Installing dependencies..."
pip install -U pip setuptools
pip install -r requirements.txt

if [ $? -eq 0 ]; then
    echo ""
    echo "======================================================================"
    echo "[✓] Setup complete!"
    echo "======================================================================"
    echo ""
    echo "You are now in the virtual environment."
    echo ""
    echo "Next steps:"
    echo "  1. Run experiments:"
    echo "     python run_minimal_poc.py --data synthetic --num_samples 10 --out_dir results/test"
    echo ""
    echo "  2. To deactivate virtual environment:"
    echo "     deactivate"
    echo ""
    echo "  3. To reactivate next time:"
    echo "     source venv/bin/activate"
    echo ""
else
    echo "[✗] Failed to install dependencies"
    exit 1
fi
