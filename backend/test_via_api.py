"""
Автотест 35 сценариев через HTTP к запущенному серверу.
Запуск: python test_via_api.py
Требование: сервер должен работать (http://localhost:8000)
"""

import requests
import sys
import time

BASE = "http://localhost:8000"
passed = 0
failed = 0
results = []
U = str(int(time.time()))  # уникальный суффикс для email

# Определяем актуальный workshop_id первой мастерской и city_id первого города
_r = requests.get(f"{BASE}/workshops/public")
FIRST_WS_ID = _r.json()[0]["id"] if _r.status_code == 200 and _r.json() else 1
_r2 = requests.get(f"{BASE}/cities/", headers={"Authorization": f"Bearer {requests.post(f'{BASE}/auth/login', json={'email': 'admin@autoservice.ru', 'password': 'admin123'}).json()['token']}"})
FIRST_CITY_ID = _r2.json()[0]["id"] if _r2.status_code == 200 and _r2.json() else 1

def check(test_num, name, method, url, expected, json=None, headers=None):
    global passed, failed
    try:
        r = method(url, json=json, headers=headers)
        ok = r.status_code == expected
        status = "✅ PASS" if ok else "❌ FAIL"
        if ok:
            passed += 1
        else:
            failed += 1
        results.append(f"  Тест {test_num:2d}. {name:45s} → {r.status_code} (ожид. {expected})  {status}")
        if not ok:
            results[-1] += f"\n         Body: {r.text[:200]}"
        return r
    except Exception as e:
        failed += 1
        results.append(f"  Тест {test_num:2d}. {name:45s} → ОШИБКА: {e}  ❌ FAIL")
        return None

# ============================================================
print("=" * 70)
print("  АВТОТЕСТ 35 СЦЕНАРИЕВ  (сервер: " + BASE + ")")
print("=" * 70)

# --- Тест 1: Успешный вход (admin) ---
r = check(1, "Успешный вход (admin)",
    requests.post, f"{BASE}/auth/login", 200,
    json={"email": "admin@autoservice.ru", "password": "admin123"})
admin_token = r.json()["token"] if r and r.status_code == 200 else None

# --- Тест 2: Неверный пароль ---
check(2, "Неверный пароль",
    requests.post, f"{BASE}/auth/login", 401,
    json={"email": "admin@autoservice.ru", "password": "wrong"})

# --- Тест 3: Несуществующий email ---
check(3, "Несуществующий email",
    requests.post, f"{BASE}/auth/login", 401,
    json={"email": "nonexistent@test.ru", "password": "admin123"})

# --- Тест 4: Запрос без токена ---
check(4, "Запрос без токена (GET /orders/)",
    requests.get, f"{BASE}/orders/", 401)

# --- Тест 5: Запрос с токеном ---
check(5, "Запрос с токеном (GET /orders/)",
    requests.get, f"{BASE}/orders/", 200,
    headers={"Authorization": f"Bearer {admin_token}"})

# --- Тест 6: Регистрация клиента ---
r = check(6, "Регистрация клиента",
    requests.post, f"{BASE}/auth/register/client", 200,
    json={
        "first_name": "Тест", "last_name": "Клиент",
        "email": f"autotest{U}@test.ru",
        "password": "client123", "workshop_id": FIRST_WS_ID
    })
client_token = r.json()["token"] if r and r.status_code == 200 else None

# --- Тест 7: Дублирующийся email ---
check(7, "Дублирующийся email",
    requests.post, f"{BASE}/auth/register/client", 400,
    json={
        "first_name": "Другой", "last_name": "Клиент",
        "email": f"autotest{U}@test.ru",
        "password": "client123", "workshop_id": FIRST_WS_ID
    })

# --- Тест 8: Создание заявки ---
r = check(8, "Создание заявки клиентом",
    requests.post, f"{BASE}/orders/", 200,
    json={"car_brand": "Toyota", "car_model": "Camry", "car_year": 2020, "description": "Тест", "service_ids": []},
    headers={"Authorization": f"Bearer {client_token}"})
order_id = r.json()["id"] if r and r.status_code == 200 else None

# --- Тест 9: Список заявок (admin) ---
check(9, "Список заявок (admin)",
    requests.get, f"{BASE}/orders/", 200,
    headers={"Authorization": f"Bearer {admin_token}"})

# --- Тест 10: Клиент видит свою заявку ---
check(10, "Клиент видит свою заявку",
    requests.get, f"{BASE}/orders/{order_id}", 200,
    headers={"Authorization": f"Bearer {client_token}"})

# --- Логин мастера ---
r = requests.post(f"{BASE}/auth/login",
    json={"email": "master.moscow1@autoservice.ru", "password": "master123"})
master_token = r.json()["token"] if r.status_code == 200 else None

# --- Тест 11: Смена статуса мастером ---
check(11, "Смена статуса мастером",
    requests.patch, f"{BASE}/orders/{order_id}", 200,
    json={"status": "in_progress"},
    headers={"Authorization": f"Bearer {master_token}"})

# --- Тест 12: Удаление заявки мастером ---
r = requests.post(f"{BASE}/orders/",
    json={"car_brand": "VAZ", "car_model": "2107", "car_year": 2005, "description": "Удалить", "service_ids": []},
    headers={"Authorization": f"Bearer {client_token}"})
del_id = r.json()["id"] if r.status_code == 200 else None
# Сбросим статус в new (мастер может удалять только new/in_progress)
requests.patch(f"{BASE}/orders/{del_id}",
    json={"status": "new"},
    headers={"Authorization": f"Bearer {master_token}"})
check(12, "Удаление заявки мастером",
    requests.delete, f"{BASE}/orders/{del_id}", 200,
    headers={"Authorization": f"Bearer {master_token}"})

# --- Тест 13: Создание платежа (клиент) ---
check(13, "Создание платежа (клиент)",
    requests.post, f"{BASE}/payments/stub", 200,
    json={"order_id": order_id, "amount": 5000, "card_number": "4111111111111111"},
    headers={"Authorization": f"Bearer {client_token}"})

# --- Тест 14: Платёж от администратора ---
check(14, "Платёж от администратора",
    requests.post, f"{BASE}/payments/stub", 403,
    json={"order_id": order_id, "amount": 100},
    headers={"Authorization": f"Bearer {admin_token}"})

# --- Тест 15: Список услуг ---
check(15, "Список услуг",
    requests.get, f"{BASE}/services/", 200,
    headers={"Authorization": f"Bearer {admin_token}"})

# --- Тест 16: Список без токена ---
check(16, "Список услуг без токена",
    requests.get, f"{BASE}/services/", 401)

# --- Тест 17: Создание услуги (admin) ---
r = check(17, "Создание услуги (admin)",
    requests.post, f"{BASE}/services/", 200,
    json={"name": "Автотест услуга", "price": 999},
    headers={"Authorization": f"Bearer {admin_token}"})
service_id = r.json()["id"] if r and r.status_code == 200 else None

# --- Тест 18: Создание услуги (client) ---
check(18, "Создание услуги (client) → 403",
    requests.post, f"{BASE}/services/", 403,
    json={"name": "Тест", "price": 100},
    headers={"Authorization": f"Bearer {client_token}"})

# --- Тест 19: Редактирование услуги ---
check(19, "Редактирование услуги",
    requests.patch, f"{BASE}/services/{service_id}", 200,
    json={"name": "Автотест (обновл.)", "price": 1500},
    headers={"Authorization": f"Bearer {admin_token}"})

# --- Тест 20: Список пользователей (admin) ---
check(20, "Список пользователей (admin)",
    requests.get, f"{BASE}/users/", 200,
    headers={"Authorization": f"Bearer {admin_token}"})

# --- Тест 21: Список пользователей (master) → 403 ---
check(21, "Список пользователей (master) → 403",
    requests.get, f"{BASE}/users/", 403,
    headers={"Authorization": f"Bearer {master_token}"})

# --- Тест 22: Регистрация пользователя (admin) ---
check(22, "Регистрация пользователя (admin)",
    requests.post, f"{BASE}/auth/register", 200,
    json={
        "first_name": "Новый", "last_name": "Мастер",
        "email": f"autotest_m{U}@test.ru",
        "password": "pass123", "role_id": 2, "workshop_ids": [FIRST_WS_ID]
    },
    headers={"Authorization": f"Bearer {admin_token}"})

# --- Тест 23: Создание через POST /users/ ---
check(23, "Создание через POST /users/",
    requests.post, f"{BASE}/users/", 200,
    json={
        "first_name": "Второй", "last_name": "Клиент",
        "email": f"autotest_u{U}@test.ru",
        "password": "pass456", "role_id": 1, "workshop_ids": [FIRST_WS_ID]
    },
    headers={"Authorization": f"Bearer {admin_token}"})

# --- Тест 24: Редактирование пользователя ---
# Находим мастера
r = requests.get(f"{BASE}/users/", headers={"Authorization": f"Bearer {admin_token}"})
users = r.json()
master_user = next((u for u in users if u["email"] == "master.moscow1@autoservice.ru"), None)
if master_user:
    check(24, "Редактирование пользователя",
        requests.patch, f"{BASE}/users/{master_user['id']}", 200,
        json={"first_name": "Мастерович"},
        headers={"Authorization": f"Bearer {admin_token}"})
else:
    failed += 1
    results.append(f"  Тест 24. Редактирование пользователя                        → SKIP (мастер не найден)  ❌ FAIL")

# --- Тест 25: Деактивация пользователя ---
r = requests.get(f"{BASE}/users/", headers={"Authorization": f"Bearer {admin_token}"})
users = r.json()
test_user = next((u for u in users if f"autotest_u{U}" in u.get("email", "")), None)
if test_user:
    check(25, "Деактивация пользователя",
        requests.delete, f"{BASE}/users/{test_user['id']}", 200,
        headers={"Authorization": f"Bearer {admin_token}"})
else:
    failed += 1
    results.append(f"  Тест 25. Деактивация пользователя                           → SKIP (пользователь не найден)  ❌ FAIL")

# --- Тест 26: Список работников (admin) ---
check(26, "Список работников (admin)",
    requests.get, f"{BASE}/workers/", 200,
    headers={"Authorization": f"Bearer {admin_token}"})

# --- Тест 27: Список работников (master) ---
check(27, "Список работников (master)",
    requests.get, f"{BASE}/workers/", 200,
    headers={"Authorization": f"Bearer {master_token}"})

# --- Тест 28: Создание работника (master) ---
r = check(28, "Создание работника (master)",
    requests.post, f"{BASE}/workers/", 200,
    json={"first_name": "Иван", "last_name": "Механиков", "position": "Слесарь"},
    headers={"Authorization": f"Bearer {master_token}"})
worker_id = r.json()["id"] if r and r.status_code == 200 else None

# --- Тест 29: Редактирование работника ---
check(29, "Редактирование работника",
    requests.patch, f"{BASE}/workers/{worker_id}", 200,
    json={"position": "Старший мастер"},
    headers={"Authorization": f"Bearer {master_token}"})

# --- Тест 30: Список работников (client) → 403 ---
check(30, "Список работников (client) → 403",
    requests.get, f"{BASE}/workers/", 403,
    headers={"Authorization": f"Bearer {client_token}"})

# --- Тест 31: Публичный список мастерских ---
check(31, "Публичный список мастерских",
    requests.get, f"{BASE}/workshops/public", 200)

# --- Тест 32: Список мастерских (admin) ---
check(32, "Список мастерских (admin)",
    requests.get, f"{BASE}/workshops/", 200,
    headers={"Authorization": f"Bearer {admin_token}"})

# --- Тест 33: Список без токена → 401 ---
check(33, "Список мастерских без токена → 401",
    requests.get, f"{BASE}/workshops/", 401)

# --- Тест 34: Создание мастерской ---
r = check(34, "Создание мастерской (admin)",
    requests.post, f"{BASE}/workshops/", 200,
    json={"name": "Тест — Авто", "city_id": FIRST_CITY_ID, "address": "ул. Тестовая 1"},
    headers={"Authorization": f"Bearer {admin_token}"})
workshop_id = r.json()["id"] if r and r.status_code == 200 else None

# --- Тест 35: Удаление мастерской ---
if workshop_id:
    check(35, "Удаление мастерской (admin)",
        requests.delete, f"{BASE}/workshops/{workshop_id}", 200,
        headers={"Authorization": f"Bearer {admin_token}"})
else:
    failed += 1
    results.append(f"  Тест 35. Удаление мастерской                                → SKIP (мастерская не создана)  ❌ FAIL")

# ============================================================
print()
for line in results:
    print(line)

print()
print("=" * 70)
print(f"  РЕЗУЛЬТАТ: {passed} passed, {failed} failed  (всего {passed + failed})")
print("=" * 70)

if failed == 0:
    print("  🎉 ВСЕ 35 ТЕСТОВ ПРОШЛИ УСПЕШНО!")
else:
    print(f"  ⚠️  {failed} тест(ов) не прошли")

sys.exit(0 if failed == 0 else 1)
