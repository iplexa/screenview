@echo off
chcp 65001 >nul
title Screen Share Client
color 0a

echo ========================================
echo    Screen Share Client - Silent Mode
echo ========================================
echo.

:: Check for Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found!
    echo Please install Python from https://python.org
    pause
    exit /b 1
)

:: Check required libraries
echo [INFO] Checking dependencies...
python -c "import cv2, numpy, pyautogui, pynput, tkinter" >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Not all required libraries are installed!
    echo Please run: pip install -r requirements.txt
    pause
    exit /b 1
)

echo [INFO] Starting client in silent mode...
echo [INFO] Client will run in background
echo [INFO] To stop, use Task Manager
echo.

:: Start client in silent mode with IP and port
start /min pythonw client.py --silent plxa.ru 9999

echo [INFO] Client started in background
echo [INFO] Use Task Manager to stop the process
echo.
echo Press any key to exit...
pause >nul 