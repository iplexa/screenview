@echo off
echo ========================================
echo Quick Start - Screen Share Server
echo ========================================

REM Проверяем наличие Python
python --version >nul 2>&1
if %errorlevel% == 0 (
    echo Found Python:
    python --version
    echo.
    echo Starting server...
    python server.py
    goto :end
)

python3 --version >nul 2>&1
if %errorlevel% == 0 (
    echo Found Python3:
    python3 --version
    echo.
    echo Starting server...
    python3 server.py
    goto :end
)

echo ERROR: Python not found!
echo Please install Python 3.7 or higher
echo Or use run_server.bat for full setup with virtual environment

:end
pause 