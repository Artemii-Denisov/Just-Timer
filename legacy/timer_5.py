import tkinter as tk

def update_timer():
    global time_left, running, initial_time
    if running and time_left > 0:
        hours, remainder = divmod(time_left, 3600)
        minutes, seconds = divmod(remainder, 60)
        time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        label.config(text=time_str, fg="#000000")
        time_left -= 1
        root.after(1000, update_timer)
    elif time_left == 0:
        running = False
        label.config(text="00:00:00", fg="#ff0000")

def start_timer(event=None):
    global running
    if not running and time_left > 0:
        running = True
        update_timer()
    elif time_left == 0:
        # Если таймер на нуле - не запускаем
        pass

def reset_timer(event=None):
    global time_left, running, initial_time
    running = False
    time_left = initial_time  # Сбрасываем на ИСХОДНОЕ значение (не жёстко 300)
    hours, remainder = divmod(time_left, 3600)
    minutes, seconds = divmod(remainder, 60)
    time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    label.config(text=time_str, fg="#000000")

def exit_app(event=None):
    root.destroy()

# Функции для перетаскивания окна без рамки
def start_move(event):
    root.x = event.x
    root.y = event.y

def do_move(event):
    x = root.winfo_x() + event.x - root.x
    y = root.winfo_y() + event.y - root.y
    root.geometry(f"+{x}+{y}")

# ===== НАСТРОЙКИ =====
# Установите нужное время в СЕКУНДАХ здесь
initial_time = 300  # 5 минут (300 секунд)
# initial_time = 60   # 1 минута
# initial_time = 3600 # 1 час
# =====================

time_left = initial_time
running = False

root = tk.Tk()
root.overrideredirect(True)
root.geometry("350x100")
root.configure(bg="#ffffff")
root.attributes('-topmost', True)

# Показываем начальное время
hours, remainder = divmod(initial_time, 3600)
minutes, seconds = divmod(remainder, 60)
initial_display = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

label = tk.Label(
    root,
    text=initial_display,
    font=("Helvetica", 60, "bold"),
    fg="#000000",
    bg="#ffffff",
    cursor="fleur"
)
label.pack(expand=True, fill="both")

# Привязываем события мыши для перемещения
label.bind("<ButtonPress-1>", start_move)
label.bind("<B1-Motion>", do_move)

# ЛКМ по окну - старт (если таймер не запущен)
label.bind("<Button-1>", start_timer, add="+")

# ПКМ по окну - сброс на исходное значение
root.bind("<Button-3>", reset_timer)

# КАК ЗАКРЫТЬ ПРОГРАММУ:
# Вариант 1: Нажмите ESC
root.bind("<Escape>", exit_app)

# Вариант 2: Закрыть через системный трей не получится (окно без рамки)
# Поэтому добавим кнопку выхода по двойному клику ПКМ или Ctrl+Q
root.bind("<Control-q>", exit_app)
# Двойной клик ПКМ
root.bind("<Button-3>", reset_timer, add="+")  # оставляем сброс
root.bind("<Double-Button-3>", exit_app)  # двойной ПКМ - выход

root.mainloop()