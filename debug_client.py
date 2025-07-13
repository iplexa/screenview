#!/usr/bin/env python3
"""
Клиент с подробной диагностикой для выявления проблем с отображением экрана
"""

import socket
import struct
import cv2
import numpy as np
import threading
import time
import sys
import tkinter as tk
from tkinter import messagebox

class DebugClient:
    def __init__(self, server_ip="127.0.0.1", server_port=9999):
        self.server_ip = server_ip
        self.server_port = server_port
        self.socket = None
        self.running = False
        self.frame_count = 0
        self.last_frame_time = time.time()
        
    def show_connection_dialog(self):
        """Показывает диалог для ввода IP и порта"""
        root = tk.Tk()
        root.withdraw()
        
        from tkinter import simpledialog
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
            return True
        except Exception as e:
            print(f"Connection failed: {e}")
            return False
            
    def receive_screen(self):
        """Принимает и отображает скриншоты"""
        try:
            # Создаем окно
            cv2.namedWindow('Debug Remote Screen', cv2.WINDOW_NORMAL)
            cv2.resizeWindow('Debug Remote Screen', 1024, 768)
            
            print("Starting to receive screen data...")
            
            while self.running and self.socket:
                try:
                    # Получаем размер данных
                    data_size = struct.unpack('!I', self.socket.recv(4))[0]
                    
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
                            # Вычисляем FPS
                            current_time = time.time()
                            fps = 1.0 / (current_time - self.last_frame_time) if self.last_frame_time > 0 else 0
                            self.last_frame_time = current_time
                            
                            # Отображаем информацию на кадре
                            info_text = f"Frame: {self.frame_count}, FPS: {fps:.1f}, Size: {data_size/1024:.1f}KB"
                            cv2.putText(frame, info_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                            
                            # Отображаем изображение
                            cv2.imshow('Debug Remote Screen', frame)
                            self.frame_count += 1
                            
                            # Логируем каждые 30 кадров
                            if self.frame_count % 30 == 0:
                                print(f"Frame {self.frame_count}: {data_size/1024:.1f}KB, "
                                      f"Transfer: {transfer_time*1000:.1f}ms, "
                                      f"Decode: {decode_time*1000:.1f}ms, "
                                      f"FPS: {fps:.1f}")
                            
                            # Обрабатываем события окна
                            key = cv2.waitKey(1) & 0xFF
                            if key == 27:  # ESC
                                print("ESC pressed, exiting...")
                                break
                        else:
                            print("Failed to decode frame")
                    else:
                        print(f"Data size mismatch: expected {data_size}, got {len(data)}")
                        
                except Exception as e:
                    print(f"Error receiving frame: {e}")
                    break
                    
        except Exception as e:
            print(f"Error in receive_screen: {e}")
        finally:
            cv2.destroyAllWindows()
            print(f"Total frames received: {self.frame_count}")
            
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
        
        # Основной цикл
        try:
            while self.running:
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("Interrupted by user")
        finally:
            self.cleanup()
            
    def cleanup(self):
        """Очищает ресурсы"""
        self.running = False
        if self.socket:
            self.socket.close()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    print("Debug Client - Screen Share")
    print("This client will show detailed information about screen transmission")
    
    client = DebugClient()
    client.run() 