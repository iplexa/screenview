@echo off
setlocal enabledelayedexpansion

echo ========================================
echo Silent Screen Share Client Launcher
echo ========================================

REM Проверяем наличие Python
python --version >nul 2>&1
if !errorlevel! == 0 (
    set PYTHON_CMD=python
    echo Found Python: 
    python --version
    goto :found_python
)

python3 --version >nul 2>&1
if !errorlevel! == 0 (
    set PYTHON_CMD=python3
    echo Found Python3: 
    python3 --version
    goto :found_python
)

echo ERROR: Python not found!
echo Please install Python 3.7 or higher
pause
exit /b 1

:found_python

REM Проверяем наличие venv
if not exist "venv" (
    echo Creating virtual environment...
    %PYTHON_CMD% -m venv venv
    if !errorlevel! neq 0 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
)

REM Активируем venv
echo Activating virtual environment...
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) else (
    echo ERROR: Virtual environment activation script not found
    pause
    exit /b 1
)

REM Устанавливаем зависимости
echo Installing/updating dependencies...
%PYTHON_CMD% -m pip install --upgrade pip
%PYTHON_CMD% -m pip install -r requirements.txt

REM Проверяем аргументы
if "%1"=="" (
    echo Usage: run_silent_client.bat [SERVER_IP] [PORT]
    echo Example: run_silent_client.bat 192.168.1.100 9999
    echo.
    echo Starting silent client with default settings...
    %PYTHON_CMD% client.py --silent
) else (
    if "%2"=="" (
        echo Starting silent client with IP: %1, Port: 9999
        %PYTHON_CMD% client.py --silent %1 9999
    ) else (
        echo Starting silent client with IP: %1, Port: %2
        %PYTHON_CMD% client.py --silent %1 %2
    )
)

echo Silent client started. Check Task Manager to stop it.
endlocal 