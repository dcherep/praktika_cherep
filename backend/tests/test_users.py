"""Тесты API пользователей (users) — только admin."""

import pytest


def test_list_users_admin(client, admin_token):
    """Список пользователей — только admin."""
    r = client.get("/users/", headers={"Authorization": f"Bearer {admin_token}"})
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert len(data) >= 2  # admin + master из conftest


def test_list_users_forbidden_for_master(client, master_token):
    """Мастер не может смотреть список пользователей."""
    r = client.get("/users/", headers={"Authorization": f"Bearer {master_token}"})
    assert r.status_code == 403


def test_register_user_admin(client, admin_token, db):
    """Регистрация нового пользователя (клиента) — только admin."""
    from app.models import Workshop

    workshop = db.query(Workshop).first()
    assert workshop is not None
    r = client.post(
        "/auth/register",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "first_name": "Новый",
            "last_name": "Клиент",
            "email": "newclient@test.ru",
            "password": "pass123",
            "role_id": 1,
            "workshop_ids": [workshop.id],
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert data["email"] == "newclient@test.ru"
    assert data["role_id"] == 1
    assert len(data["workshops"]) >= 1
    assert data["workshops"][0]["id"] == workshop.id
    assert "id" in data


def test_create_user_via_users_api_admin(client, admin_token, db):
    """Создание пользователя через POST /users/ — admin."""
    from app.models import Workshop

    workshop = db.query(Workshop).first()
    r = client.post(
        "/users/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "first_name": "Второй",
            "last_name": "Мастер",
            "email": "secondmaster@test.ru",
            "password": "master456",
            "role_id": 2,
            "workshop_ids": [workshop.id],
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert data["email"] == "secondmaster@test.ru"
    assert data["role_id"] == 2


def test_patch_user_admin(client, admin_token):
    """Редактирование пользователя — admin."""
    # Редактируем мастера (id=2 в нашем conftest)
    r = client.get("/users/", headers={"Authorization": f"Bearer {admin_token}"})
    users = r.json()
    master = next((u for u in users if u["email"] == "master@test.ru"), None)
    assert master is not None
    uid = master["id"]
    patch = client.patch(
        f"/users/{uid}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"first_name": "Мастерович"},
    )
    assert patch.status_code == 200
    assert patch.json()["first_name"] == "Мастерович"


def test_delete_user_admin(client, admin_token, db):
    """Удаление пользователя — admin (удаляем созданного через API)."""
    from app.models import Workshop

    workshop = db.query(Workshop).first()
    create = client.post(
        "/users/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "first_name": "На",
            "last_name": "Удаление",
            "email": "todelete@test.ru",
            "password": "pass",
            "role_id": 1,
            "workshop_ids": [workshop.id],
        },
    )
    assert create.status_code == 200
    uid = create.json()["id"]
    r = client.delete(f"/users/{uid}", headers={"Authorization": f"Bearer {admin_token}"})
    assert r.status_code == 200
