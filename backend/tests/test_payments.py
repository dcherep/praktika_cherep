"""Тесты API платежей (заглушка)."""

import pytest
import bcrypt
from app.models import User, Order, OrderService, Service, Workshop


def test_payment_stub_client(client, db):
    """Клиент может создать платёж-заглушку по своей заявке."""
    # Клиент с мастерской
    workshop = db.query(Workshop).first()
    h = bcrypt.hashpw(b"client123", bcrypt.gensalt(rounds=12)).decode()
    client_user = User(
        first_name="Плательщик",
        last_name="Клиентов",
        email="payer@test.ru",
        password_hash=h,
        role_id=1,
    )
    db.add(client_user)
    db.commit()
    db.refresh(client_user)
    # Услуга и заявка
    svc = Service(name="Услуга", price=5000)
    db.add(svc)
    db.commit()
    db.refresh(svc)
    order = Order(
        client_id=client_user.id,
        workshop_id=workshop.id,
        car_brand="Toyota",
        car_model="Camry",
        car_year=2020,
        description="Оплата",
        status="new",
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    os = OrderService(order_id=order.id, service_id=svc.id, unit_price=svc.price)
    db.add(os)
    db.commit()
    # Логин и платёж
    login = client.post("/auth/login", json={"email": "payer@test.ru", "password": "client123"})
    assert login.status_code == 200
    token = login.json()["token"]
    r = client.post(
        "/payments/stub",
        headers={"Authorization": f"Bearer {token}"},
        json={"order_id": order.id, "amount": 5000, "card_number": "4111111111111111"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data.get("success") is True
    assert "message" in data


def test_payment_stub_forbidden_for_admin(client, admin_token, db):
    """Платёж-заглушка только для клиента; admin получает 403."""
    # Нужна хотя бы одна заявка в БД с известным id
    from app.models import User as U, Workshop as W

    workshop = db.query(W).first()
    h = bcrypt.hashpw(b"c", bcrypt.gensalt(rounds=12)).decode()
    u = U(first_name="X", last_name="Y", email="x@test.ru", password_hash=h, role_id=1)
    db.add(u)
    db.commit()
    from app.models import Order as O

    o = O(client_id=u.id, workshop_id=workshop.id, car_brand="A", car_model="B", car_year=2020, description="", status="new")
    db.add(o)
    db.commit()
    db.refresh(o)
    r = client.post(
        "/payments/stub",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"order_id": o.id, "amount": 100},
    )
    assert r.status_code == 403
