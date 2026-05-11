#!/usr/bin/env python3
"""
Скрипт для тестирования API автосервиса v3.1
"""

import requests
from datetime import datetime

BASE_URL = "http://localhost:8000"

def print_result(name, success, data=None):
    status = "✅" if success else "❌"
    print(f"{status} {name}")
    if data and not success:
        print(f"   Ошибка: {data}")
    return success

def test_api():
    print("=" * 60)
    print("🧪 ТЕСТИРОВАНИЕ API v3.1")
    print("=" * 60)
    
    results = []
    
    # 1. Health check
    try:
        r = requests.get(f"{BASE_URL}/health", timeout=5)
        results.append(print_result("Health check", r.status_code == 200))
    except Exception as e:
        results.append(print_result("Health check", False, str(e)))
    
    # 2. Login
    token = None
    try:
        r = requests.post(
            f"{BASE_URL}/auth/login",
            json={"email": "admin@autoservice.ru", "password": "admin123"},
            timeout=5
        )
        if r.status_code == 200:
            token = r.json()["token"]
            results.append(print_result("Login (admin)", True))
        else:
            results.append(print_result("Login (admin)", False, r.text[:100]))
    except Exception as e:
        results.append(print_result("Login (admin)", False, str(e)))
    
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    
    # 3. Cities
    try:
        r = requests.get(f"{BASE_URL}/cities/", headers=headers, timeout=5)
        if r.status_code == 200:
            cities = r.json()
            results.append(print_result(f"GET /cities/ ({len(cities)} городов)", True))
        else:
            results.append(print_result("GET /cities/", False, r.text[:100]))
    except Exception as e:
        results.append(print_result("GET /cities/", False, str(e)))
    
    # 4. Services
    try:
        r = requests.get(f"{BASE_URL}/services/", headers=headers, timeout=5)
        if r.status_code == 200:
            services = r.json()
            results.append(print_result(f"GET /services/ ({len(services)} услуг)", True))
        else:
            results.append(print_result("GET /services/", False, r.text[:100]))
    except Exception as e:
        results.append(print_result("GET /services/", False, str(e)))
    
    # 5. Workshops
    try:
        r = requests.get(f"{BASE_URL}/workshops/", headers=headers, timeout=5)
        if r.status_code == 200:
            workshops = r.json()
            results.append(print_result(f"GET /workshops/ ({len(workshops)} мастерских)", True))
        else:
            results.append(print_result("GET /workshops/", False, r.text[:200]))
    except Exception as e:
        results.append(print_result("GET /workshops/", False, str(e)))
    
    # 6. Workers
    try:
        r = requests.get(f"{BASE_URL}/workers/", headers=headers, timeout=5)
        if r.status_code == 200:
            workers = r.json()
            results.append(print_result(f"GET /workers/ ({len(workers)} техников)", True))
            # Сохраняем первый ID для теста schedules
            first_worker_id = workers[0]["id"] if workers else None
        else:
            results.append(print_result("GET /workers/", False, r.text[:200]))
            first_worker_id = None
    except Exception as e:
        results.append(print_result("GET /workers/", False, str(e)))
        first_worker_id = None
    
    # 7. Users
    try:
        r = requests.get(f"{BASE_URL}/users/", headers=headers, timeout=5)
        if r.status_code == 200:
            users = r.json()
            results.append(print_result(f"GET /users/ ({len(users)} пользователей)", True))
        else:
            results.append(print_result("GET /users/", False, r.text[:200]))
    except Exception as e:
        results.append(print_result("GET /users/", False, str(e)))
    
    # 8. Orders
    try:
        r = requests.get(f"{BASE_URL}/orders/?limit=5", headers=headers, timeout=5)
        if r.status_code == 200:
            orders = r.json()
            results.append(print_result(f"GET /orders/ ({len(orders)} заявок)", True))
        else:
            results.append(print_result("GET /orders/", False, r.text[:200]))
    except Exception as e:
        results.append(print_result("GET /orders/", False, str(e)))
    
    # 9. Worker Schedules (с динамическим ID)
    try:
        if first_worker_id:
            r = requests.get(f"{BASE_URL}/worker-schedules/worker/{first_worker_id}/", headers=headers, timeout=5)
            if r.status_code == 200:
                schedules = r.json()
                results.append(print_result(f"GET /worker-schedules/worker/{first_worker_id}/ ({len(schedules)} записей)", True))
            else:
                results.append(print_result(f"GET /worker-schedules/worker/{first_worker_id}/", False, r.text[:100]))
        else:
            results.append(print_result("GET /worker-schedules/worker/{id}/", False, "Нет техников"))
    except Exception as e:
        results.append(print_result("GET /worker-schedules/worker/{id}/", False, str(e)))
    
    # 10. Payments
    try:
        r = requests.get(f"{BASE_URL}/payments/", headers=headers, timeout=5)
        # Может вернуть 404 если нет платежей, это нормально
        results.append(print_result("GET /payments/", r.status_code in [200, 404]))
    except Exception as e:
        results.append(print_result("GET /payments/", False, str(e)))
    
    # Итоги
    print("\n" + "=" * 60)
    print("📊 ИТОГИ:")
    print(f"   Успешно: {sum(results)}/{len(results)}")
    print(f"   Ошибок: {len(results) - sum(results)}/{len(results)}")
    print("=" * 60)
    
    if all(results):
        print("✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ!")
    else:
        print("❌ ЕСТЬ ОШИБКИ")
    
    return all(results)

if __name__ == "__main__":
    test_api()
