@echo off
setlocal

REM Проверяем наличие venv
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

REM Активируем venv
call venv\Scripts\activate.bat

REM Устанавливаем зависимости
pip install --upgrade pip
pip install -r requirements.txt

REM Запускаем клиент
python client.py

pause
endlocal 