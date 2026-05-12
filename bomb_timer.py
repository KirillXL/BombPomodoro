import tkinter as tk
from tkinter import messagebox
import time
import os

# Пытаемся импортировать pygame для звука
try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False

class BombTimerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Бомба-Помодоро")
        self.root.geometry("400x550")
        self.root.minsize(300, 450)
        
        # Инициализация звука
        if PYGAME_AVAILABLE:
            pygame.mixer.init()
        
        # Статистика
        self.defused_count = 0
        self.total_work_seconds = 0
        
        # Переменные состояния
        self.running = False
        self.is_rest = False
        self.time_left = 0
        self.max_time = 0
        
        self.setup_ui()
        self.update_always_on_top()

    def setup_ui(self):
        # --- Фрейм настроек ---
        settings_frame = tk.Frame(self.root, padx=10, pady=10)
        settings_frame.pack(fill=tk.X)

        tk.Label(settings_frame, text="Текущая задача:").grid(row=0, column=0, sticky=tk.W)
        self.task_entry = tk.Entry(settings_frame, width=30)
        self.task_entry.grid(row=0, column=1, columnspan=2, pady=2)
        self.task_entry.insert(0, "Спасти мир")

        tk.Label(settings_frame, text="Время работы (мин):").grid(row=1, column=0, sticky=tk.W)
        self.work_time_var = tk.IntVar(value=30)
        tk.Spinbox(settings_frame, from_=1, to=120, textvariable=self.work_time_var, width=5).grid(row=1, column=1, sticky=tk.W, pady=2)

        tk.Label(settings_frame, text="Время отдыха (мин, 0=выкл):").grid(row=2, column=0, sticky=tk.W)
        self.rest_time_var = tk.IntVar(value=5)
        tk.Spinbox(settings_frame, from_=0, to=60, textvariable=self.rest_time_var, width=5).grid(row=2, column=1, sticky=tk.W, pady=2)

        self.topmost_var = tk.BooleanVar(value=False)
        tk.Checkbutton(settings_frame, text="Поверх всех окон", variable=self.topmost_var, command=self.update_always_on_top).grid(row=3, column=0, columnspan=2, sticky=tk.W)

        # --- Визуализация бомбы ---
        self.canvas = tk.Canvas(self.root, width=200, height=200, bg=self.root.cget('bg'), highlightthickness=0)
        self.canvas.pack(pady=10)
        
        # Рисуем саму бомбу (статичные элементы)
        self.canvas.create_oval(50, 80, 150, 180, fill="#2c3e50") # Тело бомбы
        self.canvas.create_rectangle(85, 60, 115, 85, fill="#7f8c8d") # Крышка/цоколь
        
        # Фитиль (будем обновлять его длину)
        self.fuse_id = self.canvas.create_arc(100, 20, 180, 100, start=180, extent=90, style=tk.ARC, outline="#e67e22", width=5)
        self.spark_id = self.canvas.create_oval(0, 0, 0, 0, fill="yellow", outline="red") # Искорка (спрятана по умолчанию)

        # --- Таймер и статус ---
        self.status_label = tk.Label(self.root, text="Ожидание...", font=("Helvetica", 14))
        self.status_label.pack()

        self.timer_label = tk.Label(self.root, text="00:00", font=("Helvetica", 36, "bold"))
        self.timer_label.pack(pady=5)

        # --- Кнопки управления ---
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=10)

        self.start_btn = tk.Button(btn_frame, text="Поджечь фитиль (Старт)", bg="#e74c3c", fg="white", font=("Helvetica", 12, "bold"), command=self.start_work)
        self.start_btn.grid(row=0, column=0, padx=5)

        self.defuse_btn = tk.Button(btn_frame, text="Разминировать (Готово!)", bg="#2ecc71", fg="white", font=("Helvetica", 12, "bold"), state=tk.DISABLED, command=self.defuse)
        self.defuse_btn.grid(row=0, column=1, padx=5)

    def update_always_on_top(self):
        self.root.attributes('-topmost', self.topmost_var.get())

    def start_work(self):
        if not self.task_entry.get().strip():
            messagebox.showwarning("Ошибка", "Введите задачу перед запуском!")
            return

        self.is_rest = False
        work_mins = self.work_time_var.get()
        self.max_time = work_mins * 60
        self.time_left = self.max_time
        self.running = True
        
        self.start_btn.config(state=tk.DISABLED)
        self.defuse_btn.config(state=tk.NORMAL)
        self.status_label.config(text=f"Работаем: {self.task_entry.get()}", fg="red")
        self.update_timer_display()
        self.update_bomb_visual()
        self.tick()

    def start_rest(self):
        rest_mins = self.rest_time_var.get()
        if rest_mins <= 0:
            # Если время отдыха отключено, ждем ручного запуска
            self.running = False
            self.status_label.config(text="Ожидание...", fg="black")
            self.start_btn.config(state=tk.NORMAL)
            return

        self.is_rest = True
        self.max_time = rest_mins * 60
        self.time_left = self.max_time
        self.running = True
        
        self.status_label.config(text="Отдых...", fg="green")
        self.start_btn.config(state=tk.DISABLED)
        self.defuse_btn.config(state=tk.DISABLED) # Нельзя разминировать во время отдыха
        self.update_timer_display()
        # Во время отдыха фитиль не горит
        self.canvas.itemconfig(self.fuse_id, extent=0)
        self.canvas.coords(self.spark_id, 0, 0, 0, 0)
        self.tick()

    def tick(self):
        if not self.running:
            return

        self.time_left -= 1
        self.update_timer_display()
        
        if not self.is_rest:
            self.update_bomb_visual()

        if self.time_left <= 0:
            self.running = False
            if self.is_rest:
                # Отдых закончился -> автоматический старт работы
                self.start_work()
            else:
                # Время работы вышло -> ВЗРЫВ
                self.explode()
        else:
            self.root.after(1000, self.tick)

    def defuse(self):
        if not self.running or self.is_rest:
            return

        # Останавливаем таймер
        self.running = False
        
        # Обновляем статистику
        elapsed_seconds = self.max_time - self.time_left
        self.total_work_seconds += elapsed_seconds
        self.defused_count += 1
        
        self.defuse_btn.config(state=tk.DISABLED)
        self.canvas.itemconfig(self.fuse_id, extent=90) # Возвращаем фитиль
        self.canvas.coords(self.spark_id, 0, 0, 0, 0) # Прячем искру
        
        self.start_rest()

    def update_timer_display(self):
        mins, secs = divmod(self.time_left, 60)
        self.timer_label.config(text=f"{mins:02d}:{secs:02d}")

    def update_bomb_visual(self):
        if self.max_time <= 0: return
        progress = self.time_left / self.max_time
        # Угол отрисовки дуги фитиля (от 90 градусов до 0)
        current_extent = 90 * progress
        self.canvas.itemconfig(self.fuse_id, extent=current_extent)
        
        # Примерный расчет координат конца дуги для искры
        # Для дуги (100, 20, 180, 100), центр эллипса: cx=140, cy=60, rx=40, ry=40
        import math
        angle_rad = math.radians(180 + current_extent)
        spark_x = 140 + 40 * math.cos(angle_rad)
        spark_y = 60 - 40 * math.sin(angle_rad)
        
        # Мигание искры
        spark_color = "yellow" if self.time_left % 2 == 0 else "orange"
        self.canvas.itemconfig(self.spark_id, fill=spark_color)
        self.canvas.coords(self.spark_id, spark_x-5, spark_y-5, spark_x+5, spark_y+5)

    def explode(self):
        self.running = False
        self.start_btn.config(state=tk.NORMAL)
        self.defuse_btn.config(state=tk.DISABLED)
        self.canvas.coords(self.spark_id, 0, 0, 0, 0)

        # Воспроизведение звука
        if PYGAME_AVAILABLE:
            if os.path.exists("boom.wav"):
                sound = pygame.mixer.Sound("boom.wav")
                sound.play()
            else:
                print("Звуковой файл boom.wav не найден в папке со скриптом!")

        # Окно взрыва
        boom_window = tk.Toplevel(self.root)
        boom_window.attributes('-fullscreen', True)
        boom_window.configure(bg='black')
        boom_window.attributes('-topmost', True)

        tk.Label(boom_window, text="БАБАХ!", font=("Impact", 150), bg="black", fg="red").pack(expand=True)
        
        total_mins = self.total_work_seconds // 60
        stats_text = f"Количество разминированных бомб: {self.defused_count}\nОбщее время выполнения задач (горение фитиля): {total_mins} мин."
        tk.Label(boom_window, text=stats_text, font=("Helvetica", 24), bg="black", fg="white").pack(pady=20)

        close_btn = tk.Button(boom_window, text="Очистить пепел (Закрыть)", font=("Helvetica", 16), bg="#e74c3c", fg="white", command=boom_window.destroy)
        close_btn.pack(pady=50)

if __name__ == "__main__":
    root = tk.Tk()
    app = BombTimerApp(root)
    root.mainloop()