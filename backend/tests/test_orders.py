"""Тесты заявок."""

import bcrypt
import pytest
from app.models import User, Order, OrderService, Service


def test_create_order(client, admin_token, db):
    # Создаём клиента
    client_hash = bcrypt.hashpw(b"client123", bcrypt.gensalt(rounds=12)).decode()
    client_user = User(
        first_name="Иван",
        last_name="Иванов",
        email="client@test.ru",
        password_hash=client_hash,
        role_id=1,
    )
    db.add(client_user)
    db.commit()
    # Создаём услугу
    svc = Service(name="Тест", price=1000)
    db.add(svc)
    db.commit()
    # Логинимся как клиент и создаём заявку
    login = client.post("/auth/login", json={"email": "client@test.ru", "password": "client123"})
    assert login.status_code == 200
    token = login.json()["token"]
    r = client.post(
        "/orders/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "car_brand": "Toyota",
            "car_model": "Camry",
            "car_year": 2020,
            "description": "Тест",
            "service_ids": [svc.id],
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert data["car_brand"] == "Toyota"
    assert data["status"] == "new"


def test_list_orders_admin(client, admin_token):
    r = client.get("/orders/", headers={"Authorization": f"Bearer {admin_token}"})
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_get_order_by_id_client_sees_own(client, admin_token, db):
    """Клиент видит только свою заявку."""
    client_hash = bcrypt.hashpw(b"client123", bcrypt.gensalt(rounds=12)).decode()
    client_user = User(
        first_name="Иван", last_name="Иванов", email="client2@test.ru",
        password_hash=client_hash, role_id=1,
    )
    db.add(client_user)
    db.commit()
    svc = Service(name="Услуга", price=500)
    db.add(svc)
    db.commit()
    from app.models import Order as OrderModel
    from app.models import Workshop
    workshop = db.query(Workshop).first()
    order = OrderModel(
        client_id=client_user.id, workshop_id=workshop.id,
        car_brand="A", car_model="B", car_year=2020,
        description="", status="new",
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    login = client.post("/auth/login", json={"email": "client2@test.ru", "password": "client123"})
    token = login.json()["token"]
    r = client.get(f"/orders/{order.id}", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["id"] == order.id
    # Другой пользователь (admin) тоже может видеть заявку
    r2 = client.get(f"/orders/{order.id}", headers={"Authorization": f"Bearer {admin_token}"})
    assert r2.status_code == 200


def test_patch_order_assign_worker(client, admin_token, master_token, db):
    """Мастер меняет статус заявки и назначает работника через отдельный эндпоинт."""
    from app.models import Workshop, Worker
    workshop = db.query(Workshop).first()
    client_hash = bcrypt.hashpw(b"client123", bcrypt.gensalt(rounds=12)).decode()
    client_user = User(
        first_name="К", last_name="К", email="client3@test.ru",
        password_hash=client_hash, role_id=1,
    )
    db.add(client_user)
    db.commit()
    svc = Service(name="Услуга", price=500)
    db.add(svc)
    db.commit()
    from app.models import Order as OrderModel
    order = OrderModel(
        client_id=client_user.id, workshop_id=workshop.id,
        car_brand="A", car_model="B", car_year=2020, description="", status="new",
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    worker = Worker(first_name="В", last_name="В", workshop_id=workshop.id)
    db.add(worker)
    db.commit()
    db.refresh(worker)

    # 1. Мастер меняет статус
    r = client.patch(
        f"/orders/{order.id}",
        headers={"Authorization": f"Bearer {master_token}"},
        json={"status": "in_progress"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "in_progress"

    # 2. Мастер назначает техника через отдельный эндпоинт
    r2 = client.post(
        f"/orders/{order.id}/workers",
        headers={"Authorization": f"Bearer {master_token}"},
        params={"worker_id": worker.id, "role": "main"},
    )
    assert r2.status_code == 200
    assert r2.json()["worker_id"] == worker.id


def test_delete_order_master(client, master_token, db):
    """Мастер может удалить заявку в статусе new."""
    from app.models import Workshop
    workshop = db.query(Workshop).first()
    client_hash = bcrypt.hashpw(b"client123", bcrypt.gensalt(rounds=12)).decode()
    client_user = User(
        first_name="К2", last_name="К2", email="client4@test.ru",
        password_hash=client_hash, role_id=1,
    )
    db.add(client_user)
    db.commit()
    from app.models import Order as OrderModel
    order = OrderModel(
        client_id=client_user.id, workshop_id=workshop.id,
        car_brand="A", car_model="B", car_year=2020, description="", status="new",
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    r = client.delete(f"/orders/{order.id}", headers={"Authorization": f"Bearer {master_token}"})
    assert r.status_code == 200
    get_after = client.get("/orders/", headers={"Authorization": f"Bearer {master_token}"})
    ids = [o["id"] for o in get_after.json()]
    assert order.id not in ids
