"""
Скрипт для примусового перезапуску FastAPI серверу
"""
import os
import sys
import time
import subprocess
import psutil

print("=" * 80)
print("ПРИМУСОВИЙ ПЕРЕЗАПУСК СЕРВЕРА З ОНОВЛЕНИМ КОДОМ")
print("=" * 80)

# Крок 1: Знайти та зупинити всі uvicorn процеси
print("\n[1/4] Пошук процесів uvicorn на порту 8000...")
killed_count = 0

for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
    try:
        cmdline = proc.info.get('cmdline')
        if cmdline and any('uvicorn' in str(arg) and '8000' in str(arg) for arg in cmdline):
            pid = proc.info['pid']
            print(f"   Знайдено: PID {pid} - {' '.join(cmdline)}")
            proc.kill()
            killed_count += 1
            print(f"   Зупинено: PID {pid}")
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        pass

if killed_count == 0:
    print("   Процеси uvicorn не знайдено")
else:
    print(f"   Зупинено процесів: {killed_count}")
    time.sleep(2)

# Крок 2: Перевірити порт 8000
print("\n[2/4] Перевірка порту 8000...")
port_free = True
for conn in psutil.net_connections():
    if conn.laddr.port == 8000:
        print(f"   УВАГА: Порт 8000 все ще зайнятий процесом PID {conn.pid}")
        port_free = False

if port_free:
    print("   Порт 8000 вільний")

# Крок 3: Очистити Python кеш
print("\n[3/4] Очищення Python кешу (.pyc файлів)...")
project_dir = r"D:\Automation\Development\projects\ecademy"
os.chdir(project_dir)

cache_removed = 0
for root, dirs, files in os.walk(project_dir):
    # Видалити __pycache__ папки
    if '__pycache__' in dirs:
        cache_dir = os.path.join(root, '__pycache__')
        try:
            import shutil
            shutil.rmtree(cache_dir)
            cache_removed += 1
        except Exception as e:
            pass

print(f"   Видалено __pycache__ папок: {cache_removed}")

# Крок 4: Запустити новий сервер
print("\n[4/4] Запуск нового серверу з оновленим кодом...")
print(f"   Робоча директорія: {project_dir}")
print(f"   Команда: python -m uvicorn app.main:app --host 127.0.0.1 --port 8000")
print("\n" + "=" * 80)
print("СЕРВЕР ЗАПУЩЕНО! Логи нижче:")
print("=" * 80 + "\n")

# Запустити сервер у цьому ж процесі, щоб бачити вивід
os.system("python -m uvicorn app.main:app --host 127.0.0.1 --port 8000")
