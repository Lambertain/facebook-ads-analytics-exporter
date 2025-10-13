"""
Тест нормалізації телефонних номерів
"""
import sys
sys.path.insert(0, 'D:\\Automation\\Development\\projects\\ecademy')

from app.services.alfacrm_tracking import normalize_contact

# Тестові дані
test_cases = [
    ("+380501234567", "380501234567"),
    ("380501234567", "380501234567"),
    ("0501234567", "380501234567"),
    ("501234567", "380501234567"),
    ("+38 (050) 123-45-67", "380501234567"),
    ("38 050 123 45 67", "380501234567"),
]

print("=" * 80)
print("ТЕСТУВАННЯ НОРМАЛІЗАЦІЇ УКРАЇНСЬКИХ НОМЕРІВ")
print("=" * 80)
print()

all_passed = True

for input_num, expected in test_cases:
    result = normalize_contact(input_num)
    passed = result == expected
    all_passed = all_passed and passed

    status = "✓ PASS" if passed else "✗ FAIL"
    print(f"{status:8} | Вхід: {input_num:25} -> Результат: {result:15} (очікується: {expected})")

print()
print("=" * 80)
if all_passed:
    print("✓ ВСІ ТЕСТИ ПРОЙДЕНО!")
else:
    print("✗ ДЕЯКІ ТЕСТИ НЕ ПРОЙДЕНО!")
print("=" * 80)
