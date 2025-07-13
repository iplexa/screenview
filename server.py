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
        self.root.title("Screen Share Server - Remote Viewer")
        self.root.geometry("1200x800")
        self.root.configure(bg='#2c3e50')
        
        # Стили
        title_font = ('Arial', 16, 'bold')
        button_font = ('Arial', 12)
        
        # Заголовок
        title_label = tk.Label(self.root, text="Remote Screen Viewer", 
                              font=title_font, bg='#2c3e50', fg='white')
        title_label.pack(pady=10)
        
        # Информация о подключении
        self.status_label = tk.Label(self.root, text="Status: Waiting for connection...", 
                                    font=('Arial', 10), bg='#2c3e50', fg='#ecf0f1')
        self.status_label.pack(pady=5)
        
        self.ip_label = tk.Label(self.root, text=f"IP: {socket.gethostbyname(socket.gethostname())}", 
                                font=('Arial', 10), bg='#2c3e50', fg='#ecf0f1')
        self.ip_label.pack()
        
        self.port_label = tk.Label(self.root, text=f"Port: {self.port}", 
                                  font=('Arial', 10), bg='#2c3e50', fg='#ecf0f1')
        self.port_label.pack()
        
        # Кнопки управления
        button_frame = tk.Frame(self.root, bg='#2c3e50')
        button_frame.pack(pady=10)
        
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
        self.control_button.pack(pady=5)
        self.control_button.config(state='disabled')
        
        # Фрейм для отображения экрана
        screen_frame = tk.Frame(self.root, bg='#34495e', relief='sunken', bd=2)
        screen_frame.pack(pady=10, padx=20, fill='both', expand=True)
        
        # Метка для отображения экрана клиента
        self.screen_label = tk.Label(screen_frame, text="Waiting for client screen...", 
                                    bg='#34495e', fg='white', font=('Arial', 14))
        self.screen_label.pack(expand=True, fill='both')
        
        # Лог событий
        self.log_text = tk.Text(self.root, height=6, width=80, bg='#34495e', fg='white')
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
        # Поток для приема скриншотов от клиента
        screen_thread = threading.Thread(target=self.receive_screen)
        screen_thread.daemon = True
        screen_thread.start()
        
        # Поток для отправки команд управления клиенту
        control_thread = threading.Thread(target=self.send_control)
        control_thread.daemon = True
        control_thread.start()
        
    def receive_screen(self):
        """Принимает скриншоты от клиента и отображает их"""
        try:
            self.log_message("Starting to receive screen from client...")
            frame_count = 0
            
            while self.running and self.client_socket:
                try:
                    # Получаем размер данных
                    size_data = self.client_socket.recv(4)
                    if len(size_data) != 4:
                        self.log_message("Client disconnected")
                        break
                        
                    data_size = struct.unpack('!I', size_data)[0]
                    
                    # Получаем данные изображения
                    data = b''
                    while len(data) < data_size:
                        packet = self.client_socket.recv(data_size - len(data))
                        if not packet:
                            break
                        data += packet
                        
                    if len(data) == data_size:
                        # Декодируем изображение
                        frame_data = np.frombuffer(data, dtype=np.uint8)
                        frame = cv2.imdecode(frame_data, cv2.IMREAD_COLOR)
                        
                        if frame is not None:
                            # Конвертируем BGR в RGB для PIL
                            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                            
                            # Конвертируем в PIL Image
                            from PIL import Image, ImageTk
                            pil_image = Image.fromarray(frame_rgb)
                            
                            # Изменяем размер для отображения
                            display_width = 800
                            display_height = 600
                            pil_image = pil_image.resize((display_width, display_height), Image.Resampling.LANCZOS)
                            
                            # Конвертируем в PhotoImage
                            photo = ImageTk.PhotoImage(pil_image)
                            
                            # Обновляем GUI в главном потоке
                            self.root.after(0, self.update_screen, photo, frame_count)
                            
                            frame_count += 1
                            if frame_count % 100 == 0:
                                self.log_message(f"Received {frame_count} frames from client")
                        else:
                            self.log_message("Failed to decode frame from client")
                    else:
                        self.log_message(f"Data size mismatch: expected {data_size}, got {len(data)}")
                        
                except Exception as e:
                    self.log_message(f"Error receiving screen: {e}")
                    break
                    
        except Exception as e:
            self.log_message(f"Error in receive_screen: {e}")
        finally:
            self.disconnect_client()
            
    def update_screen(self, photo, frame_count):
        """Обновляет отображение экрана клиента"""
        self.screen_label.config(image=photo)
        self.screen_label.image = photo  # Сохраняем ссылку
        
        # Обновляем информацию
        info_text = f"Client Screen - Frame: {frame_count}"
        self.screen_label.config(text=info_text)
        
    def send_control(self):
        """Отправляет команды управления клиенту"""
        try:
            # Настраиваем обработчики событий мыши и клавиатуры
            self.setup_control_handlers()
            
            # Ждем завершения
            while self.running and self.client_socket:
                time.sleep(0.1)
                
        except Exception as e:
            self.log_message(f"Error in send_control: {e}")
            
    def setup_control_handlers(self):
        """Настраивает обработчики событий управления"""
        def on_mouse_move(x, y):
            if self.control_enabled and self.client_socket:
                try:
                    command = {
                        'type': 'mouse_move',
                        'x': x,
                        'y': y
                    }
                    self.client_socket.send(pickle.dumps(command))
                except:
                    pass
                    
        def on_mouse_click(x, y, button, pressed):
            if pressed and self.control_enabled and self.client_socket:
                try:
                    command = {
                        'type': 'mouse_click',
                        'x': x,
                        'y': y,
                        'button': 'left' if button == mouse.Button.left else 'right'
                    }
                    self.client_socket.send(pickle.dumps(command))
                except:
                    pass
                    
        def on_key_press(key):
            if self.control_enabled and self.client_socket:
                try:
                    command = {
                        'type': 'key_press',
                        'key': key.char if hasattr(key, 'char') else str(key)
                    }
                    self.client_socket.send(pickle.dumps(command))
                except:
                    pass
                    
        # Запускаем слушатели
        self.mouse_listener = mouse.Listener(
            on_move=on_mouse_move,
            on_click=on_mouse_click)
        self.mouse_listener.start()
        
        self.keyboard_listener = keyboard.Listener(
            on_press=on_key_press)
        self.keyboard_listener.start()
            
    def toggle_control(self):
        """Включает/выключает удаленное управление"""
        self.control_enabled = not self.control_enabled
        if self.control_enabled:
            self.control_button.config(text="Disable Remote Control", bg='#e67e22')
            self.log_message("Remote control enabled - you can now control client's computer")
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
        self.screen_label.config(text="Waiting for client screen...", image='')
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