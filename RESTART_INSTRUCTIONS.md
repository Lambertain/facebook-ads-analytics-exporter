# Инструкция по перезапуску сервера с исправлениями нормализации

## 🎯 Проблема
Сервер запущен, но работает на старом коде без исправлений нормализации телефонных номеров.
Нужен ручной перезапуск, чтобы загрузить новый код.

## ✅ Что уже исправлено в коде

1. **alfacrm_tracking.py (lines 70-121)** - функция `normalize_contact()`:
   - `+380501234567` → `380501234567` (12 цифр)
   - `0501234567` → `380501234567` (добавляем 380, убираем 0)
   - `501234567` → `380501234567` (добавляем 380)

2. **nethunt_tracking.py (lines 46-97)** - та же логика нормализации

3. **Тесты подтверждают** - unit тест `test_normalization.py` прошел успешно ✓

## 🔄 Как перезапустить сервер (вручную)

### Вариант 1: PowerShell скрипт (рекомендуется)

1. Откройте PowerShell в `D:\Automation\Development\projects\ecademy`
2. Запустите:
```powershell
.\restart_server.ps1
```

3. Сервер запустится в минимизированном окне PowerShell
4. Подождите 10 секунд для инициализации

### Вариант 2: Ручной перезапуск

1. **Остановите старый сервер:**
```powershell
Get-Process python | Where-Object {$_.CommandLine -like "*uvicorn*8000*"} | Stop-Process -Force
```

2. **Запустите новый сервер:**
```powershell
cd "D:\Automation\Development\projects\ecademy"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

3. Оставьте окно открытым, чтобы видеть логи

## 📊 Как проверить что исправления работают

### Способ 1: Запустить детальный тест

```bash
cd "D:\Automation\Development\projects\ecademy"
python test_api_detailed.py
```

**Ожидаемый результат:**
- Время выполнения: ~5-6 минут
- Статус 200 OK
- В выводе должна быть статистика с **matched > 0**

### Способ 2: Проверить логи сервера

В окне PowerShell с сервером найдите строку:
```
Filtered student index: X matched contacts from 1484 total
```

**Если X > 0** (например, 50, 100, 200) - **УСПЕХ! Нормализация работает!** ✅
**Если X = 0** - сервер все еще использует старый код ❌

### Способ 3: Проверить API response

```bash
cd "D:\Automation\Development\projects\ecademy"
python test_api_structure.py
```

Посмотрите на секцию:
```
📊 ЗАГАЛЬНА СТАТИСТИКА:
   Всього matched контактів: ???
```

Если число > 0 - исправления работают!

## 🐛 Диагностика проблем

### Проблема: Сервер не запускается
**Решение:** Проверьте, не занят ли порт 8000:
```powershell
netstat -ano | findstr :8000
```
Если порт занят - найдите PID и убейте процесс:
```powershell
taskkill /F /PID <номер_процесса>
```

### Проблема: Все еще 0 matched после перезапуска
**Возможные причины:**
1. Python кеширует .pyc файлы - удалите их:
```bash
cd "D:\Automation\Development\projects\ecademy"
find . -type f -name "*.pyc" -delete  # Linux/Mac
# Или вручную удалите папки __pycache__
```

2. Импортирован не тот модуль - перезапустите Python:
```bash
taskkill /IM python.exe /F
# Затем запустите сервер снова
```

## 📞 Поддержка

Если после перезапуска все еще 0 matched, сообщите:
1. Вывод команды `python test_normalization.py` (должен показывать ✓ PASS)
2. Строку из логов серверу `Filtered student index: ...`
3. Первые 10 строк из `api_response.json`

---

**Создано:** 2025-10-13
**Автор:** Claude (AI Agent)
