#!/usr/bin/env python3
"""
Скрипт для разработки с автоперезагрузкой
"""
import subprocess
import sys
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time
import os

class CodeChangeHandler(FileSystemEventHandler):
    def __init__(self):
        self.process = None
        self.start_bot()
    
    def on_modified(self, event):
        if event.is_directory:
            return
        
        # Перезапускаем только при изменении .py файлов
        if event.src_path.endswith('.py'):
            print(f"🔄 Изменен файл: {event.src_path}")
            self.restart_bot()
    
    def start_bot(self):
        print("🚀 Запускаем бота...")
        self.process = subprocess.Popen([
            sys.executable, "-m", "app.main"
        ])
    
    def restart_bot(self):
        if self.process:
            print("⏹️  Останавливаем бота...")
            self.process.terminate()
            self.process.wait()
        
        self.start_bot()
    
    def stop(self):
        if self.process:
            self.process.terminate()

def main():
    print("👀 Запускаем режим разработки с автоперезагрузкой...")
    
    handler = CodeChangeHandler()
    observer = Observer()
    observer.schedule(handler, path='./app', recursive=True)
    observer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Останавливаем...")
        handler.stop()
        observer.stop()
    
    observer.join()

if __name__ == "__main__":
    main()