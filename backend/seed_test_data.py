"""
Скрипт наполнения БД тестовыми данными.

Запуск:
    python seed_test_data.py

Требования:
    - БД должна быть запущена
    - Миграции применены (alembic upgrade head)
"""

import os
import sys
import bcrypt
from datetime import date, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Добавляем путь к приложению
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import Base, get_settings
from app.models import (
    Role, User, Workshop, Service, Order, OrderService, Worker,
    City, WorkerSchedule, WorkerTimeOff, OrderWorker, OrderServiceWorker,
    Payment
)

settings = get_settings()

# Создаём движок и сессию
engine = create_engine(settings.DATABASE_URL)
Session = sessionmaker(bind=engine)
db = Session()

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12)).decode()

def clear_data():
    """Очистка существующих данных (кроме ролей)."""
    print("🗑️  Очистка существующих данных...")

    # Очищаем новые таблицы в правильном порядке (по зависимостям FK)
    db.query(WorkerTimeOff).delete()
    db.query(WorkerSchedule).delete()
    db.query(OrderServiceWorker).delete()
    db.query(OrderWorker).delete()
    db.query(OrderService).delete()
    db.query(Payment).delete()
    db.flush()  # Сначала удаляем payments (FK -> orders)
    db.query(Order).delete()
    db.query(Worker).delete()
    
    # Очистка связи M2M
    db.execute(text("DELETE FROM user_workshop_link"))
    db.query(User).filter(User.email != "admin@autoservice.ru").delete()
    db.query(Workshop).delete()
    db.query(Service).delete()
    db.query(City).delete()  # Очищаем города
    
    db.commit()
    print("✅ Очистка завершена")

def create_cities():
    """Создание справочника городов."""
    print("\n🏙️  Создание справочника городов...")
    
    cities_data = [
        {"name": "Москва", "region": "Московская область"},
        {"name": "Санкт-Петербург", "region": "Ленинградская область"},
        {"name": "Новосибирск", "region": "Новосибирская область"},
        {"name": "Казань", "region": "Республика Татарстан"},
        {"name": "Екатеринбург", "region": "Свердловская область"},
    ]
    
    cities = []
    for city_data in cities_data:
        city = City(**city_data)
        db.add(city)
        cities.append(city)
    
    db.commit()
    print(f"✅ Создано {len(cities)} городов")
    return {c.name: c.id for c in cities}


def create_workshops(city_ids):
    """Создание мастерских в разных городах."""
    print("\n🏭 Создание мастерских...")

    workshops_data = [
        # Москва - 2 мастерские
        {"name": "Москва — Центральная", "city": "Москва", "address": "ул. Тверская 1", "phone": "+7 495 100-00-01"},
        {"name": "Москва — Юг", "city": "Москва", "address": "ул. Ленина 50", "phone": "+7 495 100-00-02"},

        # Санкт-Петербург - 2 мастерские
        {"name": "Санкт-Петербург — Невский", "city": "Санкт-Петербург", "address": "Невский пр. 100", "phone": "+7 812 200-00-01"},
        {"name": "Санкт-Петербург — Васильевский", "city": "Санкт-Петербург", "address": "В.О. 15-я линия 20", "phone": "+7 812 200-00-02"},

        # Новосибирск - 1 мастерская
        {"name": "Новосибирск — Центр", "city": "Новосибирск", "address": "Красный пр. 10", "phone": "+7 383 300-00-01"},

        # Казань - 1 мастерская
        {"name": "Казань — Волга", "city": "Казань", "address": "ул. Пушкина 10", "phone": "+7 843 123-45-67"},

        # Екатеринбург - 1 мастерская
        {"name": "Екатеринбург — Урал", "city": "Екатеринбург", "address": "пр. Ленина 30", "phone": "+7 343 400-00-01"},
    ]

    workshops = []
    for ws_data in workshops_data:
        ws = Workshop(
            name=ws_data["name"],
            city_id=city_ids[ws_data["city"]],  # Используем city_id вместо city
            address=ws_data["address"],
            phone=ws_data["phone"]
        )
        db.add(ws)
        workshops.append(ws)

    db.commit()
    print(f"✅ Создано {len(workshops)} мастерских")
    return {ws.name: ws.id for ws in workshops}

def create_services():
    """Создание услуг."""
    print("\n🔧 Создание услуг...")

    services_data = [
        ("Замена масла", 1500),
        ("Диагностика двигателя", 2500),
        ("Замена тормозных колодок", 3000),
        ("Замена фильтров", 1000),
        ("Замена свечей зажигания", 2000),
        ("Ремонт подвески", 5000),
        ("Замена аккумулятора", 1500),
        ("Балансировка колес", 2000),
        ("Замена шины", 1800),
        ("Диагностика КПП", 3000),
        ("Замена ремня ГРМ", 8000),
        ("Промывка форсунок", 4000),
        ("Заправка кондиционера", 3500),
        ("Полировка кузова", 6000),
        ("Химчистка салона", 5500),
    ]

    services = []
    for name, price in services_data:
        service = Service(name=name, price=price, is_active=True)
        db.add(service)
        services.append(service)

    db.commit()
    print(f"✅ Создано {len(services)} услуг")
    return {s.name: s.id for s in services}

def create_workers(workshop_ids):
    """Создание работников (техников) для каждой мастерской."""
    print("\n👷 Создание работников...")
    
    workers_data = [
        # Москва — Центральная
        {"first_name": "Алексей", "last_name": "Петров", "position": "Техник"},
        {"first_name": "Дмитрий", "last_name": "Сидоров", "position": "Техник"},
        {"first_name": "Сергей", "last_name": "Волков", "position": "Техник"},
        
        # Москва — Юг
        {"first_name": "Иван", "last_name": "Козлов", "position": "Техник"},
        {"first_name": "Павел", "last_name": "Орлов", "position": "Техник"},
        
        # Санкт-Петербург — Невский
        {"first_name": "Андрей", "last_name": "Морозов", "position": "Техник"},
        {"first_name": "Николай", "last_name": "Васильев", "position": "Техник"},
        
        # Санкт-Петербург — Васильевский
        {"first_name": "Михаил", "last_name": "Павлов", "position": "Техник"},
        
        # Новосибирск
        {"first_name": "Евгений", "last_name": "Кузнецов", "position": "Техник"},
        
        # Казань
        {"first_name": "Рустам", "last_name": "Иванов", "position": "Техник"},
        
        # Екатеринбург
        {"first_name": "Александр", "last_name": "Попов", "position": "Техник"},
    ]
    
    # Распределяем работников по мастерским
    workshop_workers = {
        "Москва — Центральная": 3,
        "Москва — Юг": 2,
        "Санкт-Петербург — Невский": 2,
        "Санкт-Петербург — Васильевский": 1,
        "Новосибирск — Центр": 1,
        "Казань — Волга": 1,
        "Екатеринбург — Урал": 1,
    }
    
    workers = []
    idx = 0
    for workshop_name, count in workshop_workers.items():
        for i in range(count):
            if idx < len(workers_data):
                worker = Worker(
                    first_name=workers_data[idx]["first_name"],
                    last_name=workers_data[idx]["last_name"],
                    position=workers_data[idx]["position"],
                    workshop_id=workshop_ids[workshop_name]
                )
                db.add(worker)
                workers.append(worker)
                idx += 1
    
    db.commit()
    print(f"✅ Создано {len(workers)} работников")
    return workers

def create_users_and_assign_workshops():
    """Создание мастеров и клиентов с привязкой к мастерским."""
    print("\n👥 Создание пользователей...")

    # Получаем роли
    roles = {r.name: r.id for r in db.query(Role).all()}
    
    # Получаем актуальные ID мастерских
    workshops_map = {w.name: w.id for w in db.query(Workshop).all()}
    print(f"📊 Мастерские: {workshops_map}")
    
    # Мастера для каждой мастерской
    masters_data = [
        # Москва
        {"first_name": "Иван", "last_name": "Москвин", "email": "master.moscow1@autoservice.ru", "workshop": "Москва — Центральная"},
        {"first_name": "Пётр", "last_name": "Южный", "email": "master.moscow2@autoservice.ru", "workshop": "Москва — Юг"},
        # Санкт-Петербург
        {"first_name": "Алексей", "last_name": "Питерский", "email": "master.spb1@autoservice.ru", "workshop": "Санкт-Петербург — Невский"},
        {"first_name": "Владимир", "last_name": "Невский", "email": "master.spb2@autoservice.ru", "workshop": "Санкт-Петербург — Васильевский"},
        # Новосибирск
        {"first_name": "Дмитрий", "last_name": "Сибирский", "email": "master.nsk@autoservice.ru", "workshop": "Новосибирск — Центр"},
        # Казань
        {"first_name": "Тимур", "last_name": "Волжский", "email": "master.kzn@autoservice.ru", "workshop": "Казань — Волга"},
        # Екатеринбург
        {"first_name": "Константин", "last_name": "Уральский", "email": "master.ekb@autoservice.ru", "workshop": "Екатеринбург — Урал"},
    ]
    
    # Создаём мастеров
    for m in masters_data:
        user = User(
            first_name=m["first_name"],
            last_name=m["last_name"],
            email=m["email"],
            password_hash=hash_password("master123"),
            role_id=roles["master"],
            is_active=True
        )
        db.add(user)
        db.flush()
        # Привязываем к мастерской по name -> id
        workshop_id = workshops_map.get(m["workshop"])
        if workshop_id:
            db.execute(
                text(f"INSERT INTO user_workshop_link (user_id, workshop_id, role_in_workshop) VALUES ({user.id}, {workshop_id}, 'master')")
            )
    
    # Клиенты для каждой мастерской (по 3 на каждую)
    clients_data = [
        # Москва — Центральная
        {"first_name": "Ольга", "last_name": "Клиентова", "email": "client1.moscow@autoservice.ru", "phone": "+7 901 111-11-11", "workshop": "Москва — Центральная"},
        {"first_name": "Наталья", "last_name": "Автова", "email": "client2.moscow@autoservice.ru", "phone": "+7 901 222-22-22", "workshop": "Москва — Центральная"},
        {"first_name": "Елена", "last_name": "Водитель", "email": "client3.moscow@autoservice.ru", "phone": "+7 901 333-33-33", "workshop": "Москва — Центральная"},
        
        # Москва — Юг
        {"first_name": "Мария", "last_name": "Югова", "email": "client1.south@autoservice.ru", "phone": "+7 902 444-44-44", "workshop": "Москва — Юг"},
        {"first_name": "Анна", "last_name": "Шина", "email": "client2.south@autoservice.ru", "phone": "+7 902 555-55-55", "workshop": "Москва — Юг"},
        
        # Санкт-Петербург — Невский
        {"first_name": "Екатерина", "last_name": "Невская", "email": "client1.spb@autoservice.ru", "phone": "+7 903 666-66-66", "workshop": "Санкт-Петербург — Невский"},
        {"first_name": "Татьяна", "last_name": "Балтийская", "email": "client2.spb@autoservice.ru", "phone": "+7 903 777-77-77", "workshop": "Санкт-Петербург — Невский"},
        
        # Санкт-Петербург — Васильевский
        {"first_name": "Оксана", "last_name": "Васильева", "email": "client1.vas@autoservice.ru", "phone": "+7 904 888-88-88", "workshop": "Санкт-Петербург — Васильевский"},
        
        # Новосибирск
        {"first_name": "Светлана", "last_name": "Обская", "email": "client1.nsk@autoservice.ru", "phone": "+7 905 999-99-99", "workshop": "Новосибирск — Центр"},
        {"first_name": "Юлия", "last_name": "Сибиряк", "email": "client2.nsk@autoservice.ru", "phone": "+7 905 888-77-66", "workshop": "Новосибирск — Центр"},
        
        # Казань
        {"first_name": "Гульнара", "last_name": "Волжская", "email": "client1.kzn@autoservice.ru", "phone": "+7 906 777-66-55", "workshop": "Казань — Волга"},
        
        # Екатеринбург
        {"first_name": "Ольга", "last_name": "Уральская", "email": "client1.ekb@autoservice.ru", "phone": "+7 907 666-55-44", "workshop": "Екатеринбург — Урал"},
    ]
    
    for c in clients_data:
        user = User(
            first_name=c["first_name"],
            last_name=c["last_name"],
            email=c["email"],
            phone=c.get("phone"),
            password_hash=hash_password("client123"),
            role_id=roles["client"],
            is_active=True
        )
        db.add(user)
        db.flush()
        # Привязываем к мастерской
        workshop_id = workshops_map.get(c["workshop"])
        if workshop_id:
            db.execute(
                text(f"INSERT INTO user_workshop_link (user_id, workshop_id, role_in_workshop) VALUES ({user.id}, {workshop_id}, 'client')")
            )

    db.commit()
    print(f"✅ Создано мастеров: {len(masters_data)}, клиентов: {len(clients_data)}")

    # Возвращаем клиентов для создания заявок
    clients = db.query(User).filter(User.role_id == roles["client"]).all()
    masters = db.query(User).filter(User.role_id == roles["master"]).all()
    return clients, masters, masters_data, clients_data

def create_orders(clients, masters, workshop_ids, service_ids, workers):
    """Создание заявок всех статусов для каждого клиента."""
    print("\n📋 Создание заявок...")

    # Статусы заявок (обновлённые: 3 статуса)
    statuses = ["new", "in_progress", "done"]

    # Данные для автомобилей
    cars = [
        {"brand": "Toyota", "model": "Camry", "year": 2020},
        {"brand": "BMW", "model": "X5", "year": 2019},
        {"brand": "Mercedes", "model": "E-Class", "year": 2021},
        {"brand": "Audi", "model": "A6", "year": 2018},
        {"brand": "Volkswagen", "model": "Tiguan", "year": 2022},
        {"brand": "Hyundai", "model": "Santa Fe", "year": 2020},
        {"brand": "Kia", "model": "Sportage", "year": 2019},
        {"brand": "Nissan", "model": "X-Trail", "year": 2021},
        {"brand": "Mazda", "model": "CX-5", "year": 2020},
        {"brand": "Ford", "model": "Kuga", "year": 2018},
    ]

    # Описания проблем
    descriptions = [
        "Требуется плановое ТО, замена масла и фильтров",
        "Стук в передней подвеске, нужна диагностика",
        "Загорелся Check Engine, необходима компьютерная диагностика",
        "Замена тормозных колодок, износ 80%",
        "Вибрация на руле при торможении",
        "Посторонний звук при работе двигателя",
        "Замена свечей зажигания и ремня ГРМ",
        "Не работает кондиционер, нужна заправка",
        "Замена аккумулятора, не держит заряд",
        "Химчистка салона, полировка кузова",
    ]

    # Получаем всех мастеров по мастерским
    masters_by_workshop = {}
    for master in masters:
        result = db.execute(text(f"SELECT workshop_id FROM user_workshop_link WHERE user_id = {master.id}")).fetchone()
        if result:
            wid = result[0]
            if wid not in masters_by_workshop:
                masters_by_workshop[wid] = master

    # Получаем техников по мастерским
    workers_by_workshop = {}
    for worker in workers:
        if worker.workshop_id not in workers_by_workshop:
            workers_by_workshop[worker.workshop_id] = []
        workers_by_workshop[worker.workshop_id].append(worker)

    # Получаем цены услуг
    services = db.query(Service).all()
    service_prices = {s.id: float(s.price) for s in services}

    orders_created = 0

    # Для каждого клиента создаём по 3 заявки каждого статуса
    for client in clients:
        # Получаем мастерскую клиента
        client_workshop = db.execute(text(f"SELECT workshop_id FROM user_workshop_link WHERE user_id = {client.id}")).fetchone()

        if not client_workshop:
            continue

        workshop_id = client_workshop[0]
        master = masters_by_workshop.get(workshop_id)
        workshop_workers = workers_by_workshop.get(workshop_id, [])

        if not master:
            continue

        for status in statuses:
            # Создаём 3 заявки каждого статуса
            num_orders = 3
            for i in range(num_orders):
                car = cars[orders_created % len(cars)]
                desc = descriptions[orders_created % len(descriptions)]

                order = Order(
                    client_id=client.id,
                    master_id=master.id if status != "new" else None,
                    workshop_id=workshop_id,
                    car_brand=car["brand"],
                    car_model=car["model"],
                    car_year=car["year"],
                    description=desc,
                    status=status,
                    total_amount=0,  # Будет рассчитано ниже
                    paid_amount=0
                )
                db.add(order)
                db.flush()

                # Добавляем 2-4 услуги в заявку с ценой на момент заказа
                num_services = 2 if status == "new" else 3 if status == "in_progress" else 4
                service_id_list = list(service_ids.values())
                start_idx = orders_created % (len(service_id_list) - num_services)
                selected_services = service_id_list[start_idx:start_idx + num_services]

                total = 0
                for service_id in selected_services:
                    price = service_prices.get(service_id, 0)
                    total += price
                    db.add(OrderService(
                        order_id=order.id,
                        service_id=service_id,
                        unit_price=price,
                        quantity=1
                    ))

                # Обновляем total_amount
                order.total_amount = total
                if status == "done":
                    order.paid_amount = total  # Полностью оплачено

                # Назначаем техников на заказ (M2N)
                if status != "new" and workshop_workers:
                    # Главный техник
                    main_worker = workshop_workers[0]
                    db.add(OrderWorker(
                        order_id=order.id,
                        worker_id=main_worker.id,
                        role="main",
                        hours_spent=4
                    ))
                    
                    # Если есть ещё техники, добавляем как помощников
                    if len(workshop_workers) > 1 and status == "done":
                        for assistant in workshop_workers[1:3]:
                            db.add(OrderWorker(
                                order_id=order.id,
                                worker_id=assistant.id,
                                role="assistant",
                                hours_spent=2
                            ))
                    
                    # Назначаем техников на услуги (order_service_workers)
                    service_workers = db.query(OrderService).filter(
                        OrderService.order_id == order.id
                    ).all()
                    
                    for idx, os in enumerate(service_workers):
                        worker_idx = idx % len(workshop_workers)
                        db.add(OrderServiceWorker(
                            order_id=order.id,
                            service_id=os.service_id,
                            worker_id=workshop_workers[worker_idx].id,
                            hours_spent=2
                        ))

                orders_created += 1

    db.commit()
    print(f"✅ Создано {orders_created} заявок")

def create_worker_schedules_and_time_off(workers):
    """Создание расписания и отпусков для техников."""
    print("\n📅 Создание расписания техников...")
    
    today = date.today()
    
    for worker in workers:
        # Создаём расписание на 2 недели вперёд
        for i in range(14):
            schedule_date = today + timedelta(days=i)
            # 5 рабочих дней, 2 выходных
            is_working = schedule_date.weekday() < 5
            
            schedule = WorkerSchedule(
                worker_id=worker.id,
                date=schedule_date,
                shift_type="full" if is_working else None,
                hours=8 if is_working else 0,
                is_working=is_working,
                comment=None
            )
            db.add(schedule)
        
        # Добавляем один отпуск одному технику из каждой мастерской
        if worker.id % 3 == 0:  # Каждый третий техник
            time_off = WorkerTimeOff(
                worker_id=worker.id,
                start_date=today + timedelta(days=20),
                end_date=today + timedelta(days=34),
                reason="vacation",
                comment="Ежегодный отпуск"
            )
            db.add(time_off)
    
    db.commit()
    print("✅ Расписание создано")


def main():
    print("=" * 60)
    print("🚀 Наполнение БД тестовыми данными")
    print("=" * 60)

    # Очищаем данные
    clear_data()

    # Создаём города
    city_ids = create_cities()

    # Создаём мастерские
    workshop_ids = create_workshops(city_ids)

    # Создаём услуги
    service_ids = create_services()

    # Создаём работников
    workers = create_workers(workshop_ids)

    # Создаём пользователей и привязываем к мастерским
    clients, masters, masters_data, clients_data = create_users_and_assign_workshops()

    # Создаём заявки
    create_orders(clients, masters, workshop_ids, service_ids, workers)
    
    # Создаём расписание техников
    create_worker_schedules_and_time_off(workers)

    print("\n" + "="*60)
    print("✅ НАЧАЛЬНЫЕ ДАННЫЕ СОЗДАНЫ!")
    print("="*60)
    print("\n📊 Статистика:")
    print(f"   Городов: {len(city_ids)}")
    print(f"   Мастерских: {len(workshop_ids)}")
    print(f"   Услуг: {len(service_ids)}")
    print(f"   Работников: {len(workers)}")
    print(f"   Мастеров: {len(masters_data)}")
    print(f"   Клиентов: {len(clients_data)}")
    print(f"   Заявок: {db.query(Order).count()}")
    print(f"   Назначений техников: {db.query(OrderWorker).count()}")
    print(f"   Расписаний: {db.query(WorkerSchedule).count()}")
    print(f"\n🔐 Учётные данные:")
    print("   Admin: admin@autoservice.ru / admin123")
    print("   Masters: master.*@autoservice.ru / master123")
    print("   Clients: client.*@autoservice.ru / client123")
    print("="*60)

    db.close()

if __name__ == "__main__":
    main()
