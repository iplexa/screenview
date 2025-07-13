@echo off
chcp 65001 >nul
title Screen Share Server
color 0b

echo ========================================
echo    Screen Share Server
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

echo [INFO] Starting server...
echo [INFO] Server will be available on port 9999
echo.

:: Start server
python server.py

echo.
echo [INFO] Server finished
pause 