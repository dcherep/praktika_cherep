"""Тесты API мастерских (workshops)."""

import pytest


def test_list_workshops_public_without_auth(client, db):
    """Публичный список мастерских — без авторизации (для формы регистрации)."""
    r = client.get("/workshops/public")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert "id" in data[0]
    assert "name" in data[0]
    assert "city" in data[0]


def test_list_workshops_admin(client, admin_token):
    """Список мастерских — с авторизацией (admin)."""
    r = client.get("/workshops/", headers={"Authorization": f"Bearer {admin_token}"})
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert "id" in data[0]
    assert "name" in data[0]
    assert "city" in data[0]


def test_list_workshops_forbidden_without_auth(client):
    """Без токена — 401."""
    r = client.get("/workshops/")
    assert r.status_code == 401


def test_create_workshop_admin(client, admin_token, db):
    """Создание мастерской — только admin."""
    from app.models.city import City
    # Используем существующий город из conftest
    city = db.query(City).first()
    r = client.post(
        "/workshops/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"name": "Казань — Центр", "city_id": city.id},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == "Казань — Центр"
    assert data["city_id"] == city.id
    assert "id" in data


def test_patch_and_delete_workshop_admin(client, admin_token, db):
    """Редактирование и удаление мастерской — admin."""
    from app.models.city import City
    city = db.query(City).first()
    create = client.post(
        "/workshops/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"name": "Удаляемая", "city_id": city.id},
    )
    assert create.status_code == 200
    wid = create.json()["id"]
    patch = client.patch(
        f"/workshops/{wid}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"name": "Обновлённая"},
    )
    assert patch.status_code == 200
    assert patch.json()["name"] == "Обновлённая"
    delete = client.delete(f"/workshops/{wid}", headers={"Authorization": f"Bearer {admin_token}"})
    assert delete.status_code == 200
    get_after = client.get("/workshops/", headers={"Authorization": f"Bearer {admin_token}"})
    ids = [w["id"] for w in get_after.json()]
    assert wid not in ids
