@echo off
REM ╔══════════════════════════════════════════════════════════════════════════════╗
REM ║                    CLASSIFIED - INSTALLATION SCRIPT                          ║
REM ║                        Border Surveillance System                             ║
REM ║                                                                              ║
REM ║  Purpose: Automated installation for Windows                                  ║
REM ║  Security Level: CONFIDENTIAL                                                 ║
REM ║  Version: 1.0.0                                                              ║
REM ╚══════════════════════════════════════════════════════════════════════════════╝
REM
REM SECURITY NOTICE:
REM - This script should only be run on air-gapped systems
REM - All dependencies must be pre-downloaded for offline installation
REM - Review all operations before executing
REM
REM USAGE:
REM   install.bat
REM
REM REQUIREMENTS:
REM   - Python 3.9 or higher
REM   - pip package manager
REM   - 50GB available disk space
REM   - 8GB RAM minimum (16GB recommended)

setlocal EnableDelayedExpansion

REM =============================================================================
REM CONFIGURATION
REM =============================================================================

set "SCRIPT_DIR=%~dp0"
set "VENV_DIR=%SCRIPT_DIR%venv"
set "PYTHON_MIN_VERSION=3.9"
set "LOG_FILE=%SCRIPT_DIR%install.log"

REM =============================================================================
REM MAIN
REM =============================================================================

cls
echo.
echo ╔══════════════════════════════════════════════════════════════════════════════╗
echo ║                    CLASSIFIED - BORDER SURVEILLANCE SYSTEM                    ║
echo ║                           Installation Script                                ║
echo ╚══════════════════════════════════════════════════════════════════════════════╝
echo.

echo [%date% %time%] Installation started > "%LOG_FILE%"

REM Check Python
echo [INFO] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python %PYTHON_MIN_VERSION% or higher.
    echo [ERROR] Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version') do set PYTHON_VERSION=%%i
echo [OK] Python %PYTHON_VERSION% found
echo [%date% %time%] Python %PYTHON_VERSION% found >> "%LOG_FILE%"

REM Create virtual environment
echo.
echo [INFO] Creating virtual environment...
if exist "%VENV_DIR%" (
    echo [WARNING] Virtual environment already exists. Skipping creation.
) else (
    python -m venv "%VENV_DIR%"
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created
)

REM Activate virtual environment
echo.
echo [INFO] Activating virtual environment...
call "%VENV_DIR%\Scripts\activate.bat"
if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment
    pause
    exit /b 1
)
echo [OK] Virtual environment activated

REM Upgrade pip
echo.
echo [INFO] Upgrading pip...
python -m pip install --upgrade pip --quiet
echo [OK] pip upgraded

REM Install dependencies
echo.
echo [INFO] Installing dependencies (this may take several minutes)...
if not exist "%SCRIPT_DIR%requirements.txt" (
    echo [ERROR] requirements.txt not found
    pause
    exit /b 1
)
pip install -r "%SCRIPT_DIR%requirements.txt" --quiet
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies
    pause
    exit /b 1
)
echo [OK] Dependencies installed

REM Create directories
echo.
echo [INFO] Creating required directories...
if not exist "%SCRIPT_DIR%data" mkdir "%SCRIPT_DIR%data"
if not exist "%SCRIPT_DIR%data\map_tiles" mkdir "%SCRIPT_DIR%data\map_tiles"
if not exist "%SCRIPT_DIR%data\video_cache" mkdir "%SCRIPT_DIR%data\video_cache"
if not exist "%SCRIPT_DIR%logs" mkdir "%SCRIPT_DIR%logs"
if not exist "%SCRIPT_DIR%logs\audit" mkdir "%SCRIPT_DIR%logs\audit"
if not exist "%SCRIPT_DIR%logs\system" mkdir "%SCRIPT_DIR%logs\system"
if not exist "%SCRIPT_DIR%logs\detections" mkdir "%SCRIPT_DIR%logs\detections"
if not exist "%SCRIPT_DIR%models" mkdir "%SCRIPT_DIR%models"
if not exist "%SCRIPT_DIR%exports" mkdir "%SCRIPT_DIR%exports"
echo [OK] Directories created

REM Check for YOLOv8 model
echo.
echo [INFO] Checking for YOLOv8 model...
if exist "%SCRIPT_DIR%models\yolov8n.pt" (
    echo [OK] YOLOv8 model found
) else (
    echo [WARNING] YOLOv8 model not found at %SCRIPT_DIR%models\yolov8n.pt
    echo.
    echo For OFFLINE installation, you need to:
    echo 1. Download yolov8n.pt from https://github.com/ultralytics/assets/releases
    echo 2. Copy it to: %SCRIPT_DIR%models\yolov8n.pt
    echo.
    set /p DOWNLOAD_MODEL="Would you like to download the model now? (requires internet) [y/N]: "
    if /i "!DOWNLOAD_MODEL!"=="y" (
        echo [INFO] Downloading YOLOv8n model...
        python -c "import urllib.request; urllib.request.urlretrieve('https://github.com/ultralytics/assets/releases/download/v8.2.0/yolov8n.pt', '%SCRIPT_DIR%models\yolov8n.pt'.replace('\\', '/'))"
        if errorlevel 1 (
            echo [WARNING] Failed to download model. Please download manually.
        ) else (
            echo [OK] YOLOv8 model downloaded
        )
    )
)

REM Initialize database
echo.
echo [INFO] Initializing database...
python -c "import sys; sys.path.insert(0, r'%SCRIPT_DIR%'); from database.db_manager import DatabaseManager; db = DatabaseManager(); db.initialize_database(); print('[OK] Database initialized')"

REM Verify installation
echo.
echo [INFO] Verifying installation...
python -c "import streamlit; import cv2; import torch; from ultralytics import YOLO; import folium; from cryptography.fernet import Fernet; print('[OK] All dependencies verified')"
if errorlevel 1 (
    echo [ERROR] Installation verification failed
    pause
    exit /b 1
)

REM Complete
echo.
echo ╔══════════════════════════════════════════════════════════════════════════════╗
echo ║                        INSTALLATION COMPLETE                                ║
echo ╚══════════════════════════════════════════════════════════════════════════════╝
echo.
echo To start the Border Surveillance System:
echo.
echo   1. Activate the virtual environment:
echo      %VENV_DIR%\Scripts\activate.bat
echo.
echo   2. Run the application:
echo      streamlit run ui\app.py
echo.
echo   Or use the run script:
echo      run.bat
echo.
echo SECURITY REMINDER:
echo   - Change the default admin password immediately
echo   - Ensure system is air-gapped for production use
echo   - Review audit logs regularly
echo.

echo [%date% %time%] Installation completed >> "%LOG_FILE%"

pause
