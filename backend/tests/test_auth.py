"""Тесты авторизации."""

def test_login_success(client):
    r = client.post("/auth/login", json={"email": "admin@test.ru", "password": "admin123"})
    assert r.status_code == 200
    data = r.json()
    assert "token" in data
    assert data["user"]["role"] == "admin"
    assert data["user"]["id"] == 1


def test_login_wrong_password(client):
    r = client.post("/auth/login", json={"email": "admin@test.ru", "password": "wrong"})
    assert r.status_code == 401


def test_login_wrong_email(client):
    r = client.post("/auth/login", json={"email": "nonexistent@test.ru", "password": "admin123"})
    assert r.status_code == 401


def test_protected_route_without_token(client):
    r = client.get("/orders/")
    assert r.status_code == 401  # No credentials (HTTPBearer returns 401)


def test_protected_route_with_token(client, admin_token):
    r = client.get("/orders/", headers={"Authorization": f"Bearer {admin_token}"})
    assert r.status_code == 200


def test_client_self_register_and_login(client, db):
    """Обычный клиент может самостоятельно зарегистрироваться через /auth/register/client."""
    # workshop_id=1 создаётся в conftest (Тестовая мастерская, Москва)
    email = "selfclient@test.ru"
    r = client.post(
        "/auth/register/client",
        json={
            "first_name": "Самостоятельный",
            "last_name": "Клиент",
            "email": email,
            "password": "client123",
            "workshop_id": 1,
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert "token" in data
    assert data["user"]["role"] == "client"
    # Повторная регистрация с тем же email должна вернуть 400
    r2 = client.post(
        "/auth/register/client",
        json={
            "first_name": "Другой",
            "last_name": "Клиент",
            "email": email,
            "password": "client123",
            "workshop_id": 1,
        },
    )
    assert r2.status_code == 400


def test_client_register_invalid_workshop(client, db):
    """Регистрация с несуществующей мастерской возвращает 400."""
    r = client.post(
        "/auth/register/client",
        json={
            "first_name": "Тест",
            "last_name": "Клиент",
            "email": "badworkshop@test.ru",
            "password": "client123",
            "workshop_id": 999,
        },
    )
    assert r.status_code == 400
