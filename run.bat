@echo off
REM ╔══════════════════════════════════════════════════════════════════════════════╗
REM ║                    CLASSIFIED - RUN SCRIPT                                   ║
REM ║                        Border Surveillance System                             ║
REM ║                                                                              ║
REM ║  Purpose: Launch the surveillance dashboard on Windows                        ║
REM ║  Security Level: CONFIDENTIAL                                                 ║
REM ║  Version: 1.0.0                                                              ║
REM ╚══════════════════════════════════════════════════════════════════════════════╝
REM
REM USAGE:
REM   run.bat [PORT]
REM
REM OPTIONS:
REM   PORT    Specify port number (default: 8501)

setlocal EnableDelayedExpansion

REM =============================================================================
REM CONFIGURATION
REM =============================================================================

set "SCRIPT_DIR=%~dp0"
set "VENV_DIR=%SCRIPT_DIR%venv"
set "APP_FILE=%SCRIPT_DIR%ui\app.py"
set "DEFAULT_PORT=8501"

REM Parse arguments
set "PORT=%DEFAULT_PORT%"
if not "%~1"=="" set "PORT=%~1"

REM =============================================================================
REM MAIN
REM =============================================================================

cls
echo.
echo ╔══════════════════════════════════════════════════════════════════════════════╗
echo ║                    CLASSIFIED - BORDER SURVEILLANCE SYSTEM                    ║
echo ║                              Launching...                                    ║
echo ╚══════════════════════════════════════════════════════════════════════════════╝
echo.

REM Check virtual environment
if not exist "%VENV_DIR%" (
    echo [ERROR] Virtual environment not found.
    echo Please run install.bat first.
    pause
    exit /b 1
)

REM Activate virtual environment
echo [INFO] Activating virtual environment...
call "%VENV_DIR%\Scripts\activate.bat"
if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment
    pause
    exit /b 1
)
echo [OK] Virtual environment activated

REM Check Streamlit
echo [INFO] Checking dependencies...
python -c "import streamlit" 2>nul
if errorlevel 1 (
    echo [ERROR] Streamlit not installed. Run install.bat first.
    pause
    exit /b 1
)
echo [OK] Dependencies OK

REM Log startup
if not exist "%SCRIPT_DIR%logs\system" mkdir "%SCRIPT_DIR%logs\system"
echo [%date% %time%] System startup on port %PORT% >> "%SCRIPT_DIR%logs\system\startup.log"

REM Start application
echo.
echo [INFO] Starting Border Surveillance System...
echo [INFO] Port: %PORT%
echo [INFO] URL: http://localhost:%PORT%
echo.
echo Press Ctrl+C to stop
echo.

streamlit run "%APP_FILE%" ^
    --server.port=%PORT% ^
    --server.address=localhost ^
    --server.enableCORS=false ^
    --server.enableXsrfProtection=true ^
    --theme.base=dark ^
    --theme.primaryColor=#4ade80 ^
    --theme.backgroundColor=#0a0a0a ^
    --theme.secondaryBackgroundColor=#1a1a1a ^
    --theme.textColor=#e6e6e6

echo.
echo [INFO] Application stopped

REM Log shutdown
echo [%date% %time%] System shutdown >> "%SCRIPT_DIR%logs\system\startup.log"

pause
