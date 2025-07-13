import socket
import threading
import cv2
import numpy as np
import pyautogui
from pynput import mouse, keyboard
import tkinter as tk
from tkinter import messagebox
import struct
import pickle
import time

class ScreenShareServer:
    def __init__(self, host='0.0.0.0', port=9999):
        self.host = host
        self.port = port
        self.server_socket = None
        self.client_socket = None
        self.client_address = None
        self.running = False
        self.control_enabled = False
        
        # Создаем GUI для сервера
        self.create_gui()
        
    def create_gui(self):
        self.root = tk.Tk()
        self.root.title("Screen Share Server")
        self.root.geometry("400x300")
        self.root.configure(bg='#2c3e50')
        
        # Стили
        title_font = ('Arial', 16, 'bold')
        button_font = ('Arial', 12)
        
        # Заголовок
        title_label = tk.Label(self.root, text="Screen Share Server", 
                              font=title_font, bg='#2c3e50', fg='white')
        title_label.pack(pady=20)
        
        # Информация о подключении
        self.status_label = tk.Label(self.root, text="Status: Waiting for connection...", 
                                    font=('Arial', 10), bg='#2c3e50', fg='#ecf0f1')
        self.status_label.pack(pady=10)
        
        self.ip_label = tk.Label(self.root, text=f"IP: {socket.gethostbyname(socket.gethostname())}", 
                                font=('Arial', 10), bg='#2c3e50', fg='#ecf0f1')
        self.ip_label.pack()
        
        self.port_label = tk.Label(self.root, text=f"Port: {self.port}", 
                                  font=('Arial', 10), bg='#2c3e50', fg='#ecf0f1')
        self.port_label.pack()
        
        # Кнопки управления
        button_frame = tk.Frame(self.root, bg='#2c3e50')
        button_frame.pack(pady=20)
        
        self.start_button = tk.Button(button_frame, text="Start Server", 
                                     command=self.start_server, font=button_font,
                                     bg='#27ae60', fg='white', relief='flat', padx=20)
        self.start_button.pack(side=tk.LEFT, padx=10)
        
        self.stop_button = tk.Button(button_frame, text="Stop Server", 
                                    command=self.stop_server, font=button_font,
                                    bg='#e74c3c', fg='white', relief='flat', padx=20)
        self.stop_button.pack(side=tk.LEFT, padx=10)
        self.stop_button.config(state='disabled')
        
        # Кнопка управления
        self.control_button = tk.Button(self.root, text="Enable Remote Control", 
                                       command=self.toggle_control, font=button_font,
                                       bg='#3498db', fg='white', relief='flat', padx=20)
        self.control_button.pack(pady=10)
        self.control_button.config(state='disabled')
        
        # Лог событий
        self.log_text = tk.Text(self.root, height=8, width=45, bg='#34495e', fg='white')
        self.log_text.pack(pady=10, padx=20)
        
        # Обработчик закрытия окна
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def log_message(self, message):
        """Добавляет сообщение в лог"""
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        
    def start_server(self):
        """Запускает сервер"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(1)
            
            self.running = True
            self.status_label.config(text="Status: Server started, waiting for client...")
            self.start_button.config(state='disabled')
            self.stop_button.config(state='normal')
            
            self.log_message("Server started successfully")
            
            # Запускаем поток для принятия подключений
            accept_thread = threading.Thread(target=self.accept_connections)
            accept_thread.daemon = True
            accept_thread.start()
            
        except Exception as e:
            self.log_message(f"Error starting server: {e}")
            messagebox.showerror("Error", f"Failed to start server: {e}")
            
    def accept_connections(self):
        """Принимает подключения от клиентов"""
        while self.running:
            try:
                self.log_message("Waiting for client connection...")
                self.client_socket, self.client_address = self.server_socket.accept()
                
                self.log_message(f"Client connected from {self.client_address}")
                self.status_label.config(text=f"Status: Connected to {self.client_address[0]}")
                self.control_button.config(state='normal')
                
                # Запускаем потоки для обработки данных
                self.start_data_threads()
                
            except Exception as e:
                if self.running:
                    self.log_message(f"Error accepting connection: {e}")
                break
                
    def start_data_threads(self):
        """Запускает потоки для обработки данных"""
        # Поток для отправки скриншотов
        screen_thread = threading.Thread(target=self.send_screen)
        screen_thread.daemon = True
        screen_thread.start()
        
        # Поток для приема команд управления
        control_thread = threading.Thread(target=self.receive_control)
        control_thread.daemon = True
        control_thread.start()
        
    def send_screen(self):
        """Отправляет скриншоты клиенту"""
        try:
            while self.running and self.client_socket:
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
                
                time.sleep(0.1)  # 10 FPS
                
        except Exception as e:
            self.log_message(f"Error sending screen: {e}")
            self.disconnect_client()
            
    def receive_control(self):
        """Принимает команды управления от клиента"""
        try:
            while self.running and self.client_socket:
                # Получаем команду
                command_data = self.client_socket.recv(1024)
                if not command_data:
                    break
                    
                command = pickle.loads(command_data)
                self.log_message(f"Received command: {command}")
                
                if self.control_enabled:
                    self.execute_command(command)
                    
        except Exception as e:
            self.log_message(f"Error receiving control: {e}")
            self.disconnect_client()
            
    def execute_command(self, command):
        """Выполняет команду управления"""
        try:
            cmd_type = command.get('type')
            
            if cmd_type == 'mouse_move':
                x, y = command['x'], command['y']
                pyautogui.moveTo(x, y)
                
            elif cmd_type == 'mouse_click':
                x, y = command['x'], command['y']
                button = command.get('button', 'left')
                pyautogui.click(x, y, button=button)
                
            elif cmd_type == 'key_press':
                key = command['key']
                pyautogui.press(key)
                
            elif cmd_type == 'key_type':
                text = command['text']
                pyautogui.typewrite(text)
                
        except Exception as e:
            self.log_message(f"Error executing command: {e}")
            
    def toggle_control(self):
        """Включает/выключает удаленное управление"""
        self.control_enabled = not self.control_enabled
        if self.control_enabled:
            self.control_button.config(text="Disable Remote Control", bg='#e67e22')
            self.log_message("Remote control enabled")
        else:
            self.control_button.config(text="Enable Remote Control", bg='#3498db')
            self.log_message("Remote control disabled")
            
    def disconnect_client(self):
        """Отключает клиента"""
        if self.client_socket:
            self.client_socket.close()
            self.client_socket = None
            self.client_address = None
            
        self.status_label.config(text="Status: Waiting for connection...")
        self.control_button.config(state='disabled')
        self.log_message("Client disconnected")
        
    def stop_server(self):
        """Останавливает сервер"""
        self.running = False
        self.disconnect_client()
        
        if self.server_socket:
            self.server_socket.close()
            self.server_socket = None
            
        self.status_label.config(text="Status: Server stopped")
        self.start_button.config(state='normal')
        self.stop_button.config(state='disabled')
        self.control_button.config(state='disabled')
        self.log_message("Server stopped")
        
    def on_closing(self):
        """Обработчик закрытия окна"""
        self.stop_server()
        self.root.destroy()
        
    def run(self):
        """Запускает GUI"""
        self.root.mainloop()

if __name__ == "__main__":
    server = ScreenShareServer()
    server.run() 