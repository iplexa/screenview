#!/usr/bin/env python3
"""
Простой тестовый клиент для диагностики проблем с отображением экрана
"""

import socket
import struct
import cv2
import numpy as np
import threading
import time
import sys

class TestClient:
    def __init__(self, server_ip="127.0.0.1", server_port=9999):
        self.server_ip = server_ip
        self.server_port = server_port
        self.socket = None
        self.running = False
        
    def connect(self):
        """Подключается к серверу"""
        try:
            print(f"Connecting to {self.server_ip}:{self.server_port}...")
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.server_ip, self.server_port))
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
            cv2.namedWindow('Test Remote Screen', cv2.WINDOW_NORMAL)
            cv2.resizeWindow('Test Remote Screen', 800, 600)
            
            print("Starting to receive screen data...")
            frame_count = 0
            
            while self.running and self.socket:
                try:
                    # Получаем размер данных
                    data_size = struct.unpack('!I', self.socket.recv(4))[0]
                    print(f"Receiving frame {frame_count + 1}, size: {data_size} bytes")
                    
                    # Получаем данные изображения
                    data = b''
                    while len(data) < data_size:
                        packet = self.socket.recv(data_size - len(data))
                        if not packet:
                            print("Connection lost")
                            break
                        data += packet
                        
                    if len(data) == data_size:
                        # Декодируем изображение
                        frame_data = np.frombuffer(data, dtype=np.uint8)
                        frame = cv2.imdecode(frame_data, cv2.IMREAD_COLOR)
                        
                        if frame is not None:
                            # Отображаем изображение
                            cv2.imshow('Test Remote Screen', frame)
                            frame_count += 1
                            
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
            print(f"Total frames received: {frame_count}")
            
    def run(self):
        """Запускает клиент"""
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
    # Получаем параметры из аргументов командной строки
    server_ip = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
    server_port = int(sys.argv[2]) if len(sys.argv) > 2 else 9999
    
    print(f"Test Client - Server: {server_ip}:{server_port}")
    print("Press ESC to exit")
    
    client = TestClient(server_ip, server_port)
    client.run() 