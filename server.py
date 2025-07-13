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
        self.root.geometry("1400x900")
        self.root.configure(bg='#2c3e50')
        
        # Стили
        title_font = ('Arial', 16, 'bold')
        button_font = ('Arial', 12)
        
        # Заголовок
        title_label = tk.Label(self.root, text="Remote Screen Viewer", 
                              font=title_font, bg='#2c3e50', fg='white')
        title_label.pack(pady=5)
        
        # Информация о подключении
        self.status_label = tk.Label(self.root, text="Status: Waiting for connection...", 
                                    font=('Arial', 10), bg='#2c3e50', fg='#ecf0f1')
        self.status_label.pack(pady=2)
        
        self.ip_label = tk.Label(self.root, text=f"IP: {socket.gethostbyname(socket.gethostname())}", 
                                font=('Arial', 10), bg='#2c3e50', fg='#ecf0f1')
        self.ip_label.pack()
        
        self.port_label = tk.Label(self.root, text=f"Port: {self.port}", 
                                  font=('Arial', 10), bg='#2c3e50', fg='#ecf0f1')
        self.port_label.pack()
        
        # Кнопки управления
        button_frame = tk.Frame(self.root, bg='#2c3e50')
        button_frame.pack(pady=5)
        
        self.start_button = tk.Button(button_frame, text="Start Server", 
                                     command=self.start_server, font=button_font,
                                     bg='#27ae60', fg='white', relief='flat', padx=20)
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = tk.Button(button_frame, text="Stop Server", 
                                    command=self.stop_server, font=button_font,
                                    bg='#e74c3c', fg='white', relief='flat', padx=20)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        self.stop_button.config(state='disabled')
        
        # Кнопка управления
        self.control_button = tk.Button(button_frame, text="Enable Remote Control", 
                                       command=self.toggle_control, font=button_font,
                                       bg='#3498db', fg='white', relief='flat', padx=20)
        self.control_button.pack(side=tk.LEFT, padx=5)
        self.control_button.config(state='disabled')
        
        # Кнопка полноэкранного режима
        self.fullscreen_button = tk.Button(button_frame, text="Fullscreen", 
                                          command=self.toggle_fullscreen, font=button_font,
                                          bg='#9b59b6', fg='white', relief='flat', padx=20)
        self.fullscreen_button.pack(side=tk.LEFT, padx=5)
        self.fullscreen_button.config(state='disabled')
        
        # Фрейм для отображения экрана
        screen_frame = tk.Frame(self.root, bg='#34495e', relief='sunken', bd=2)
        screen_frame.pack(pady=5, padx=10, fill='both', expand=True)
        
        # Создаем Canvas для отображения экрана с прокруткой
        self.canvas = tk.Canvas(screen_frame, bg='#34495e', highlightthickness=0)
        scrollbar_v = tk.Scrollbar(screen_frame, orient="vertical", command=self.canvas.yview)
        scrollbar_h = tk.Scrollbar(screen_frame, orient="horizontal", command=self.canvas.xview)
        
        self.canvas.configure(yscrollcommand=scrollbar_v.set, xscrollcommand=scrollbar_h.set)
        
        # Размещаем элементы
        scrollbar_v.pack(side="right", fill="y")
        scrollbar_h.pack(side="bottom", fill="x")
        self.canvas.pack(side="left", fill="both", expand=True)
        
        # Метка для отображения экрана клиента
        self.screen_label = tk.Label(self.canvas, text="Waiting for client screen...", 
                                    bg='#34495e', fg='white', font=('Arial', 14))
        self.canvas.create_window(400, 300, window=self.screen_label, anchor="center")
        
        # Лог событий
        log_frame = tk.Frame(self.root, bg='#2c3e50')
        log_frame.pack(pady=5, padx=10, fill='x')
        
        log_label = tk.Label(log_frame, text="Event Log:", font=('Arial', 10, 'bold'), 
                            bg='#2c3e50', fg='white')
        log_label.pack(anchor='w')
        
        self.log_text = tk.Text(log_frame, height=4, width=100, bg='#34495e', fg='white')
        self.log_text.pack(fill='x')
        
        # Обработчик закрытия окна
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Переменные для полноэкранного режима
        self.is_fullscreen = False
        
        # Переменные для отслеживания кликов
        self.last_click_time = 0
        self.click_count = 0
        
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
                self.fullscreen_button.config(state='normal')
                
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
                            
                            # Сохраняем оригинальный размер кадра
                            self.original_frame_size = (pil_image.width, pil_image.height)
                            
                            # Изменяем размер для отображения (максимум 1200x800)
                            display_width = min(1200, pil_image.width)
                            display_height = min(800, pil_image.height)
                            
                            # Сохраняем пропорции
                            aspect_ratio = pil_image.width / pil_image.height
                            if display_width / display_height > aspect_ratio:
                                display_width = int(display_height * aspect_ratio)
                            else:
                                display_height = int(display_width / aspect_ratio)
                            
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
            
    def toggle_fullscreen(self):
        """Включает/выключает полноэкранный режим"""
        self.is_fullscreen = not self.is_fullscreen
        if self.is_fullscreen:
            self.root.attributes('-fullscreen', True)
            self.fullscreen_button.config(text="Exit Fullscreen", bg='#e67e22')
            self.log_message("Fullscreen mode enabled")
        else:
            self.root.attributes('-fullscreen', False)
            self.fullscreen_button.config(text="Fullscreen", bg='#9b59b6')
            self.log_message("Fullscreen mode disabled")
            
    def update_screen(self, photo, frame_count):
        """Обновляет отображение экрана клиента"""
        # Удаляем предыдущее изображение
        self.canvas.delete("all")
        
        # Сохраняем размеры для масштабирования координат мыши
        self.display_frame_size = (photo.width(), photo.height())
        
        # Получаем размеры canvas
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        if canvas_width <= 1 or canvas_height <= 1:
            # Canvas еще не отрисован, используем размеры окна
            canvas_width = 1200
            canvas_height = 600
        
        # Размещаем изображение по центру canvas
        x = canvas_width // 2
        y = canvas_height // 2
        
        # Создаем новое изображение в canvas
        self.canvas.create_image(x, y, image=photo, anchor="center")
        self.screen_label.config(image=photo)
        self.screen_label.image = photo  # Сохраняем ссылку
        
        # Обновляем информацию
        original_size = getattr(self, 'original_frame_size', (0, 0))
        info_text = f"Client Screen - Frame: {frame_count} | Display: {photo.width()}x{photo.height()} | Original: {original_size[0]}x{original_size[1]}"
        self.canvas.create_text(10, 10, text=info_text, anchor="nw", 
                               fill="white", font=("Arial", 10, "bold"))
        
        # Обновляем область прокрутки
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        
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
        # Привязываем события мыши к canvas
        self.canvas.bind("<Motion>", self.on_mouse_move)
        self.canvas.bind("<Button-1>", self.on_mouse_click)
        self.canvas.bind("<Button-3>", self.on_mouse_right_click)
        self.canvas.bind("<Double-Button-1>", self.on_mouse_double_click)
        self.canvas.bind("<MouseWheel>", self.on_mouse_scroll)
        
        def on_key_press(key):
            if self.control_enabled and self.client_socket:
                try:
                    # Обрабатываем специальные клавиши
                    if hasattr(key, 'char') and key.char:
                        command = {
                            'type': 'key_press',
                            'key': key.char
                        }
                    else:
                        # Специальные клавиши
                        key_name = str(key).replace("'", "")
                        command = {
                            'type': 'key_press',
                            'key': key_name
                        }
                    
                    self.client_socket.send(pickle.dumps(command))
                    self.log_message(f"Sent key command: {command['key']}")
                except Exception as e:
                    self.log_message(f"Error sending key command: {e}")
                    
        # Запускаем слушатель клавиатуры
        self.keyboard_listener = keyboard.Listener(
            on_press=on_key_press)
        self.keyboard_listener.start()
        
    def scale_coordinates(self, event_x, event_y):
        """Масштабирует координаты мыши от отображаемого размера к оригинальному"""
        if not hasattr(self, 'display_frame_size') or not hasattr(self, 'original_frame_size'):
            return 0, 0
            
        display_width, display_height = self.display_frame_size
        original_width, original_height = self.original_frame_size
        
        # Получаем размеры canvas
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        if canvas_width <= 1 or canvas_height <= 1:
            return 0, 0
        
        # Вычисляем позицию изображения в canvas
        image_x = canvas_width // 2
        image_y = canvas_height // 2
        
        # Вычисляем относительные координаты в изображении
        rel_x = (event_x - image_x + display_width // 2) / display_width
        rel_y = (event_y - image_y + display_height // 2) / display_height
        
        # Ограничиваем координаты
        rel_x = max(0, min(1, rel_x))
        rel_y = max(0, min(1, rel_y))
        
        # Масштабируем к оригинальному размеру
        scaled_x = int(rel_x * original_width)
        scaled_y = int(rel_y * original_height)
        
        return scaled_x, scaled_y
        
    def on_mouse_move(self, event):
        """Обработчик движения мыши"""
        if self.control_enabled and self.client_socket:
            try:
                scaled_x, scaled_y = self.scale_coordinates(event.x, event.y)
                
                command = {
                    'type': 'mouse_move',
                    'x': scaled_x,
                    'y': scaled_y
                }
                self.client_socket.send(pickle.dumps(command))
            except Exception as e:
                self.log_message(f"Error sending mouse move: {e}")
                
    def on_mouse_click(self, event):
        """Обработчик клика левой кнопкой мыши"""
        if self.control_enabled and self.client_socket:
            try:
                scaled_x, scaled_y = self.scale_coordinates(event.x, event.y)
                
                # Проверяем на двойной клик
                current_time = time.time()
                if current_time - self.last_click_time < 0.3:
                    self.click_count += 1
                    if self.click_count >= 2:
                        # Двойной клик
                        command = {
                            'type': 'mouse_double_click',
                            'x': scaled_x,
                            'y': scaled_y,
                            'button': 'left'
                        }
                        self.click_count = 0
                    else:
                        # Одинарный клик
                        command = {
                            'type': 'mouse_click',
                            'x': scaled_x,
                            'y': scaled_y,
                            'button': 'left'
                        }
                else:
                    # Одинарный клик
                    command = {
                        'type': 'mouse_click',
                        'x': scaled_x,
                        'y': scaled_y,
                        'button': 'left'
                    }
                    self.click_count = 1
                
                self.last_click_time = current_time
                self.client_socket.send(pickle.dumps(command))
                self.log_message(f"Sent mouse click: {scaled_x}, {scaled_y}")
            except Exception as e:
                self.log_message(f"Error sending mouse click: {e}")
                
    def on_mouse_double_click(self, event):
        """Обработчик двойного клика левой кнопкой мыши"""
        if self.control_enabled and self.client_socket:
            try:
                scaled_x, scaled_y = self.scale_coordinates(event.x, event.y)
                
                command = {
                    'type': 'mouse_double_click',
                    'x': scaled_x,
                    'y': scaled_y,
                    'button': 'left'
                }
                self.client_socket.send(pickle.dumps(command))
                self.log_message(f"Sent mouse double click: {scaled_x}, {scaled_y}")
            except Exception as e:
                self.log_message(f"Error sending mouse double click: {e}")
                
    def on_mouse_right_click(self, event):
        """Обработчик клика правой кнопкой мыши"""
        if self.control_enabled and self.client_socket:
            try:
                scaled_x, scaled_y = self.scale_coordinates(event.x, event.y)
                
                command = {
                    'type': 'mouse_click',
                    'x': scaled_x,
                    'y': scaled_y,
                    'button': 'right'
                }
                self.client_socket.send(pickle.dumps(command))
                self.log_message(f"Sent mouse right click: {scaled_x}, {scaled_y}")
            except Exception as e:
                self.log_message(f"Error sending mouse right click: {e}")
                
    def on_mouse_scroll(self, event):
        """Обработчик прокрутки мыши"""
        if self.control_enabled and self.client_socket:
            try:
                scaled_x, scaled_y = self.scale_coordinates(event.x, event.y)
                
                # Определяем направление прокрутки
                if event.delta > 0:
                    clicks = 3  # Вверх
                else:
                    clicks = -3  # Вниз
                
                command = {
                    'type': 'mouse_scroll',
                    'x': scaled_x,
                    'y': scaled_y,
                    'clicks': clicks
                }
                self.client_socket.send(pickle.dumps(command))
                self.log_message(f"Sent mouse scroll: {clicks} at {scaled_x}, {scaled_y}")
            except Exception as e:
                self.log_message(f"Error sending mouse scroll: {e}")
            
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
        self.fullscreen_button.config(state='disabled')
        
        # Очищаем canvas и показываем сообщение
        self.canvas.delete("all")
        self.screen_label.config(text="Waiting for client screen...", image='')
        self.canvas.create_window(400, 300, window=self.screen_label, anchor="center")
        
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