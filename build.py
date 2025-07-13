#!/usr/bin/env python3
"""
Скрипт для создания исполняемых файлов из Python скриптов
Требует установки PyInstaller: pip install pyinstaller
"""

import os
import sys
import subprocess
import shutil

def install_pyinstaller():
    """Устанавливает PyInstaller если не установлен"""
    try:
        import PyInstaller
        print("PyInstaller уже установлен")
    except ImportError:
        print("Устанавливаем PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

def build_executable(script_name, output_name, hidden=False):
    """Создает исполняемый файл из Python скрипта"""
    print(f"Создаем исполняемый файл для {script_name}...")
    
    cmd = [
        "pyinstaller",
        "--onefile",
        "--noconsole" if hidden else "--console",
        "--name", output_name,
        script_name
    ]
    
    if hidden:
        cmd.extend(["--hidden-import", "win32gui", "--hidden-import", "win32con"])
    
    subprocess.check_call(cmd)
    
    # Перемещаем файл в корневую папку
    exe_path = os.path.join("dist", f"{output_name}.exe")
    if os.path.exists(exe_path):
        shutil.move(exe_path, f"{output_name}.exe")
        print(f"Создан файл: {output_name}.exe")
    else:
        print(f"Ошибка: файл {exe_path} не найден")

def clean_build_files():
    """Очищает временные файлы сборки"""
    dirs_to_remove = ["build", "dist", "__pycache__"]
    files_to_remove = ["*.spec"]
    
    for dir_name in dirs_to_remove:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"Удалена папка: {dir_name}")
    
    for pattern in files_to_remove:
        for file in os.listdir("."):
            if file.endswith(".spec"):
                os.remove(file)
                print(f"Удален файл: {file}")

def main():
    """Основная функция"""
    print("=== Сборка исполняемых файлов ===")
    
    # Устанавливаем PyInstaller
    install_pyinstaller()
    
    # Очищаем предыдущие сборки
    clean_build_files()
    
    # Создаем исполняемые файлы
    try:
        # Сервер (с консолью для отладки)
        build_executable("server.py", "ScreenShareServer", hidden=False)
        
        # Клиент с диалогом
        build_executable("client.py", "ScreenShareClient", hidden=True)
        
        # Полностью скрытый клиент
        build_executable("silent_client.py", "SilentClient", hidden=True)
        
        print("\n=== Сборка завершена успешно! ===")
        print("Созданные файлы:")
        print("- ScreenShareServer.exe (сервер)")
        print("- ScreenShareClient.exe (клиент с диалогом)")
        print("- SilentClient.exe (скрытый клиент)")
        
    except subprocess.CalledProcessError as e:
        print(f"Ошибка при сборке: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 