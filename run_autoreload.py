import time
import os
import subprocess
import sys
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Команда для запуска сервера
COMMAND = [sys.executable, 'run_waitress.py']
# Директории для отслеживания
WATCH_PATHS = ['.', './app']

class ChangeHandler(FileSystemEventHandler):
    """Обработчик событий файловой системы."""
    def __init__(self):
        self.process = None
        self.start_server()

    def start_server(self):
        """Запускает или перезапускает сервер."""
        if self.process:
            print("Перезапуск сервера...")
            self.process.kill()
            self.process.wait()
        else:
            print("Запуск сервера...")
        
        # Запускаем сервер в новом процессе
        self.process = subprocess.Popen(COMMAND)

    def on_any_event(self, event):
        """Вызывается при любом событии."""
        # Реагируем только на изменения в .py файлах
        if event.src_path.endswith('.py'):
            print(f"Обнаружено изменение в файле: {event.src_path}")
            self.start_server()

if __name__ == "__main__":
    event_handler = ChangeHandler()
    observer = Observer()
    
    for path in WATCH_PATHS:
        observer.schedule(event_handler, path, recursive=True)
        print(f"Отслеживание изменений в: {os.path.abspath(path)}")
        
    observer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        if event_handler.process:
            event_handler.process.kill()
            event_handler.process.wait()
            
    observer.join()
    print("Сервер остановлен.")
