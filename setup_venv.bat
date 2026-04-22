@echo off
REM Setup script for Windows - Creates and activates virtual environment

echo.
echo ======================================================================
echo  Depth Refinement PoC - Setup Script (Windows)
echo ======================================================================
echo.

if exist venv (
    echo [*] Virtual environment already exists at: venv
    echo [*] Activating...
    call venv\Scripts\activate.bat
    echo [✓] Activated. You can now run: python run_minimal_poc.py
    exit /b 0
)

echo [*] Creating virtual environment...
python -m venv venv

if not exist venv (
    echo [✗] Failed to create virtual environment
    exit /b 1
)

echo [✓] Virtual environment created

echo [*] Activating virtual environment...
call venv\Scripts\activate.bat

echo [*] Installing dependencies...
pip install -U pip setuptools
pip install -r requirements.txt

if %errorlevel% equ 0 (
    echo.
    echo ======================================================================
    echo [✓] Setup complete!
    echo ======================================================================
    echo.
    echo You are now in the virtual environment.
    echo.
    echo Next steps:
    echo   1. Run experiments:
    echo      python run_minimal_poc.py --data synthetic --num_samples 10 --out_dir results/test
    echo.
    echo   2. To deactivate virtual environment:
    echo      deactivate
    echo.
    echo   3. To reactivate next time:
    echo      .\venv\Scripts\activate.bat
    echo.
) else (
    echo [✗] Failed to install dependencies
    exit /b 1
)
