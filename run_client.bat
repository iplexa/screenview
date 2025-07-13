@echo off
chcp 65001 >nul
title Screen Share Client
color 0a

echo ========================================
echo    Screen Share Client
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

:: Проверяем наличие виртуального окружения
if exist "venv\Scripts\activate.bat" (
    echo [INFO] Активируем виртуальное окружение...
    call venv\Scripts\activate.bat
) else (
    echo [INFO] Виртуальное окружение не найдено, используем системный Python
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

echo [INFO] Запускаем клиент...
echo [INFO] Введите IP адрес сервера и порт в диалоговом окне
echo.

:: Запускаем клиент
python client.py

echo.
echo [INFO] Клиент завершен
pause 