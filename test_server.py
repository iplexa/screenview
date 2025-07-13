#!/usr/bin/env python3
"""
Простой тестовый сервер для проверки работы скриншотов
"""

import socket
import threading
import cv2
import numpy as np
import pyautogui
import struct
import time
import sys

class TestServer:
    def __init__(self, host='0.0.0.0', port=9999):
        self.host = host
        self.port = port
        self.server_socket = None
        self.client_socket = None
        self.running = False
        
    def start(self):
        """Запускает сервер"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(1)
            
            self.running = True
            print(f"Test server started on {self.host}:{self.port}")
            print("Waiting for client connection...")
            
            # Принимаем подключение
            self.client_socket, self.client_address = self.server_socket.accept()
            print(f"Client connected from {self.client_address}")
            
            # Запускаем отправку экрана
            self.send_screen()
            
        except Exception as e:
            print(f"Error starting server: {e}")
            
    def send_screen(self):
        """Отправляет скриншоты клиенту"""
        try:
            print("Starting screen transmission...")
            frame_count = 0
            
            while self.running and self.client_socket:
                try:
                    # Делаем скриншот
                    screenshot = pyautogui.screenshot()
                    frame = np.array(screenshot)
                    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                    
                    # Сжимаем изображение
                    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 70]
                    _, buffer = cv2.imencode('.jpg', frame, encode_param)
                    
                    # Отправляем размер данных и сами данные
                    data_size = len(buffer)
                    self.client_socket.send(struct.pack('!I', data_size))
                    self.client_socket.send(buffer.tobytes())
                    
                    frame_count += 1
                    if frame_count % 30 == 0:  # Логируем каждые 30 кадров
                        print(f"Sent {frame_count} frames")
                    
                    time.sleep(0.1)  # 10 FPS
                    
                except Exception as e:
                    print(f"Error sending frame: {e}")
                    break
                    
        except Exception as e:
            print(f"Error in send_screen: {e}")
        finally:
            self.cleanup()
            
    def cleanup(self):
        """Очищает ресурсы"""
        self.running = False
        if self.client_socket:
            self.client_socket.close()
        if self.server_socket:
            self.server_socket.close()
        print("Server stopped")

if __name__ == "__main__":
    print("Test Server - Screen Share")
    print("This server will send screenshots to connected clients")
    print("Press Ctrl+C to stop")
    
    server = TestServer()
    
    try:
        server.start()
    except KeyboardInterrupt:
        print("\nStopping server...")
        server.cleanup() 