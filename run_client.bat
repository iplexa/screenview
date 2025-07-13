@echo off
chcp 65001 >nul
title Screen Share Client
color 0a

echo ========================================
echo    Screen Share Client
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

echo [INFO] Starting client...
echo [INFO] Enter server IP and port in the dialog window
echo.

:: Start client
python client.py

echo.
echo [INFO] Client finished
pause 