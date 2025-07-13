#!/usr/bin/env python3
"""
Специальная версия клиента для macOS с обходом проблем OpenCV
"""

import socket
import struct
import cv2
import numpy as np
import threading
import time
import sys
import tkinter as tk
from tkinter import simpledialog, messagebox
from PIL import Image, ImageTk

class MacClient:
    def __init__(self, server_ip="127.0.0.1", server_port=9999):
        self.server_ip = server_ip
        self.server_port = server_port
        self.socket = None
        self.running = False
        self.frame_count = 0
        self.last_frame_time = time.time()
        
        # Создаем GUI окно
        self.root = tk.Tk()
        self.root.title("Remote Screen Viewer")
        self.root.geometry("1024x768")
        
        # Создаем метку для отображения изображения
        self.image_label = tk.Label(self.root, text="Waiting for connection...")
        self.image_label.pack(expand=True, fill='both')
        
        # Создаем метку для информации
        self.info_label = tk.Label(self.root, text="", bg='black', fg='white')
        self.info_label.pack(side='bottom', fill='x')
        
        # Обработчик закрытия окна
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def show_connection_dialog(self):
        """Показывает диалог для ввода IP и порта"""
        self.root.withdraw()
        
        server_ip = simpledialog.askstring("Connection", 
                                         "Enter server IP address:",
                                         parent=self.root)
        if not server_ip:
            self.root.destroy()
            return False
            
        server_port = simpledialog.askstring("Connection", 
                                           "Enter server port (default: 9999):",
                                           parent=self.root)
        if not server_port:
            server_port = "9999"
            
        try:
            self.server_port = int(server_port)
        except ValueError:
            messagebox.showerror("Error", "Invalid port number")
            self.root.destroy()
            return False
            
        self.server_ip = server_ip
        self.root.deiconify()
        return True
        
    def connect(self):
        """Подключается к серверу"""
        try:
            print(f"Connecting to {self.server_ip}:{self.server_port}...")
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(10)
            self.socket.connect((self.server_ip, self.server_port))
            self.socket.settimeout(None)
            self.running = True
            print("Connected successfully!")
            self.info_label.config(text="Connected! Receiving screen...")
            return True
        except Exception as e:
            print(f"Connection failed: {e}")
            self.info_label.config(text=f"Connection failed: {e}")
            return False
            
    def receive_screen(self):
        """Принимает и отображает скриншоты"""
        try:
            print("Starting to receive screen data...")
            
            while self.running and self.socket:
                try:
                    # Получаем размер данных
                    size_data = self.socket.recv(4)
                    if len(size_data) != 4:
                        print(f"Failed to receive size data, got {len(size_data)} bytes")
                        break
                        
                    data_size = struct.unpack('!I', size_data)[0]
                    
                    if data_size > 1000000:  # Проверяем разумность размера
                        print(f"Warning: Very large frame size: {data_size} bytes")
                    
                    # Получаем данные изображения
                    data = b''
                    start_time = time.time()
                    
                    while len(data) < data_size:
                        packet = self.socket.recv(min(4096, data_size - len(data)))
                        if not packet:
                            print("Connection lost during data transfer")
                            break
                        data += packet
                        
                    transfer_time = time.time() - start_time
                    
                    if len(data) == data_size:
                        # Декодируем изображение
                        decode_start = time.time()
                        frame_data = np.frombuffer(data, dtype=np.uint8)
                        frame = cv2.imdecode(frame_data, cv2.IMREAD_COLOR)
                        decode_time = time.time() - decode_start
                        
                        if frame is not None:
                            # Конвертируем BGR в RGB для PIL
                            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                            
                            # Вычисляем FPS
                            current_time = time.time()
                            fps = 1.0 / (current_time - self.last_frame_time) if self.last_frame_time > 0 else 0
                            self.last_frame_time = current_time
                            
                            # Конвертируем в PIL Image
                            pil_image = Image.fromarray(frame_rgb)
                            
                            # Изменяем размер для отображения
                            display_width = 1024
                            display_height = 768
                            pil_image = pil_image.resize((display_width, display_height), Image.Resampling.LANCZOS)
                            
                            # Конвертируем в PhotoImage
                            photo = ImageTk.PhotoImage(pil_image)
                            
                            # Обновляем GUI в главном потоке
                            self.root.after(0, self.update_image, photo, fps, data_size, transfer_time, decode_time)
                            
                            self.frame_count += 1
                            
                            # Логируем каждые 30 кадров
                            if self.frame_count % 30 == 0:
                                print(f"Frame {self.frame_count}: {data_size/1024:.1f}KB, "
                                      f"Transfer: {transfer_time*1000:.1f}ms, "
                                      f"Decode: {decode_time*1000:.1f}ms, "
                                      f"FPS: {fps:.1f}")
                        else:
                            print("Failed to decode frame")
                    else:
                        print(f"Data size mismatch: expected {data_size}, got {len(data)}")
                        
                except BrokenPipeError:
                    print("Server disconnected (broken pipe)")
                    break
                except ConnectionResetError:
                    print("Server disconnected (connection reset)")
                    break
                except Exception as e:
                    print(f"Error receiving frame: {e}")
                    break
                    
        except Exception as e:
            print(f"Error in receive_screen: {e}")
        finally:
            print(f"Total frames received: {self.frame_count}")
            self.info_label.config(text=f"Disconnected. Total frames: {self.frame_count}")
            
    def update_image(self, photo, fps, data_size, transfer_time, decode_time):
        """Обновляет изображение в GUI"""
        self.image_label.config(image=photo)
        self.image_label.image = photo  # Сохраняем ссылку
        
        # Обновляем информацию
        info_text = f"Frame: {self.frame_count}, FPS: {fps:.1f}, Size: {data_size/1024:.1f}KB, Transfer: {transfer_time*1000:.1f}ms"
        self.info_label.config(text=info_text)
        
    def on_closing(self):
        """Обработчик закрытия окна"""
        self.running = False
        if self.socket:
            self.socket.close()
        self.root.destroy()
        
    def run(self):
        """Запускает клиент"""
        # Показываем диалог подключения
        if not self.show_connection_dialog():
            return
            
        if not self.connect():
            return
            
        # Запускаем поток для получения экрана
        screen_thread = threading.Thread(target=self.receive_screen)
        screen_thread.daemon = True
        screen_thread.start()
        
        # Запускаем GUI
        self.root.mainloop()

if __name__ == "__main__":
    print("Mac Client - Screen Share")
    print("This client is optimized for macOS")
    
    client = MacClient()
    client.run() 