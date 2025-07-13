@echo off
setlocal

echo ========================================
echo Screen Share Client Launcher
echo ========================================

REM Проверяем наличие Python
python --version >nul 2>&1
if %errorlevel% == 0 (
    set PYTHON_CMD=python
    echo Found Python: 
    python --version
) else (
    python3 --version >nul 2>&1
    if %errorlevel% == 0 (
        set PYTHON_CMD=python3
        echo Found Python3: 
        python3 --version
    ) else (
        echo ERROR: Python not found!
        echo Please install Python 3.7 or higher
        pause
        exit /b 1
    )
)

REM Проверяем наличие venv
if not exist venv (
    echo Creating virtual environment...
    %PYTHON_CMD% -m venv venv
    if %errorlevel% neq 0 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
)

REM Активируем venv
echo Activating virtual environment...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)

REM Устанавливаем зависимости
echo Installing/updating dependencies...
%PYTHON_CMD% -m pip install --upgrade pip
%PYTHON_CMD% -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo WARNING: Some dependencies may not have installed correctly
    echo Continuing anyway...
)

REM Запускаем клиент
echo.
echo Starting Screen Share Client...
echo ========================================
%PYTHON_CMD% client.py

pause
endlocal 