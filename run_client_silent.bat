@echo off
chcp 65001 >nul
title Screen Share Client
color 0a

echo ========================================
echo    Screen Share Client - Silent Mode
echo ========================================
echo.

:: Проверяем наличие Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python не найден в системе!
    echo Установите Python с https://python.org
    pause
    exit /b 1
)

:: Проверяем наличие необходимых библиотек
echo [INFO] Проверяем зависимости...
python -c "import cv2, numpy, pyautogui, pynput, tkinter" >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Не все необходимые библиотеки установлены!
    echo Установите зависимости: pip install -r requirements.txt
    pause
    exit /b 1
)

echo [INFO] Запускаем клиент в тихом режиме...
echo [INFO] Клиент будет работать в фоновом режиме
echo [INFO] Для остановки используйте Диспетчер задач
echo.

:: Запускаем клиент в тихом режиме
start /min pythonw client.py --silent

echo [INFO] Клиент запущен в фоновом режиме
echo [INFO] Проверьте Диспетчер задач для остановки процесса
echo.
echo Нажмите любую клавишу для выхода...
pause >nul 