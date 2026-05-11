"""Тесты API работников (workers)."""

import pytest


def test_list_workers_admin(client, admin_token):
    """Список работников — admin видит всех."""
    r = client.get("/workers/", headers={"Authorization": f"Bearer {admin_token}"})
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_list_workers_master(client, master_token):
    """Мастер видит работников своей мастерской."""
    r = client.get("/workers/", headers={"Authorization": f"Bearer {master_token}"})
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_create_worker_master(client, master_token):
    """Мастер создаёт работника в своей мастерской (workshop_id подставляется)."""
    r = client.post(
        "/workers/",
        headers={"Authorization": f"Bearer {master_token}"},
        json={"first_name": "Иван", "last_name": "Механиков", "position": "Слесарь"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["first_name"] == "Иван"
    assert data["last_name"] == "Механиков"
    assert data["position"] == "Слесарь"
    assert data["workshop_id"] is not None
    assert data["is_active"] is True
    assert "is_assigned" in data


def test_patch_worker_master(client, master_token):
    """Мастер может обновить работника своей мастерской."""
    create = client.post(
        "/workers/",
        headers={"Authorization": f"Bearer {master_token}"},
        json={"first_name": "Пётр", "last_name": "Слесарев", "position": "Мастер"},
    )
    assert create.status_code == 200
    wid = create.json()["id"]
    r = client.patch(
        f"/workers/{wid}",
        headers={"Authorization": f"Bearer {master_token}"},
        json={"position": "Старший мастер", "is_active": True},
    )
    assert r.status_code == 200
    assert r.json()["position"] == "Старший мастер"


def test_list_workers_forbidden_for_client(client, db):
    """Клиент не имеет доступа к списку работников."""
    import bcrypt
    from app.models import User

    h = bcrypt.hashpw(b"client123", bcrypt.gensalt(rounds=12)).decode()
    u = User(first_name="C", last_name="C", email="client2@test.ru", password_hash=h, role_id=1)
    db.add(u)
    db.commit()
    login = client.post("/auth/login", json={"email": "client2@test.ru", "password": "client123"})
    token = login.json()["token"]
    r = client.get("/workers/", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 403
