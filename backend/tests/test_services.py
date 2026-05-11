"""Тесты API услуг (services)."""

import pytest


def test_list_services_authenticated(client, admin_token):
    """Список услуг доступен любому авторизованному пользователю."""
    r = client.get("/services/", headers={"Authorization": f"Bearer {admin_token}"})
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_list_services_without_auth(client):
    """Без токена список услуг — 401."""
    r = client.get("/services/")
    assert r.status_code == 401


def test_create_service_admin(client, admin_token):
    """Создание услуги — только admin."""
    r = client.post(
        "/services/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"name": "Замена масла", "price": 3500.50},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == "Замена масла"
    assert float(data["price"]) == 3500.50
    assert "id" in data


def test_create_service_forbidden_for_client(client, db):
    """Клиент не может создавать услуги."""
    import bcrypt
    from app.models import User

    h = bcrypt.hashpw(b"client123", bcrypt.gensalt(rounds=12)).decode()
    u = User(first_name="C", last_name="C", email="c@test.ru", password_hash=h, role_id=1)
    db.add(u)
    db.commit()
    login = client.post("/auth/login", json={"email": "c@test.ru", "password": "client123"})
    assert login.status_code == 200
    token = login.json()["token"]
    r = client.post(
        "/services/",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Услуга", "price": 100},
    )
    assert r.status_code == 403


def test_patch_service_admin(client, admin_token):
    """Редактирование услуги — admin."""
    create = client.post(
        "/services/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"name": "Шиномонтаж", "price": 2000},
    )
    assert create.status_code == 200
    sid = create.json()["id"]
    r = client.patch(
        f"/services/{sid}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"name": "Шиномонтаж (зима)", "price": 2500},
    )
    assert r.status_code == 200
    assert r.json()["name"] == "Шиномонтаж (зима)"
    assert float(r.json()["price"]) == 2500
