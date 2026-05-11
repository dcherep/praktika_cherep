"""Фикстуры pytest для тестов API."""

import bcrypt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db
from app.models import Role, User
from app.models.city import City
from app.models.workshop import Workshop, user_workshop_link

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

# Pre-computed bcrypt хэши (cost factor 12)
ADMIN_HASH = bcrypt.hashpw(b"admin123", bcrypt.gensalt(rounds=12)).decode()
MASTER_HASH = bcrypt.hashpw(b"master123", bcrypt.gensalt(rounds=12)).decode()


@pytest.fixture(scope="function")
def db():
    """Изолированная БД для каждого теста. StaticPool гарантирует, что все
    соединения в рамках одного теста работают с одной и той же in-memory БД."""
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()

    # --- Seed данных ---

    # Роли
    for name in ("client", "master", "admin"):
        session.add(Role(name=name))
    session.commit()

    # Город
    city = City(name="Москва")
    session.add(city)
    session.commit()
    session.refresh(city)

    # Мастерская
    workshop = Workshop(name="Тестовая мастерская", city_id=city.id)
    session.add(workshop)
    session.commit()
    session.refresh(workshop)

    # Админ (role_id=3)
    admin = User(
        first_name="Admin",
        last_name="Test",
        email="admin@test.ru",
        password_hash=ADMIN_HASH,
        role_id=3,
    )
    session.add(admin)
    session.commit()

    # Мастер (role_id=2) + привязка к мастерской через M2M
    master = User(
        first_name="Master",
        last_name="Test",
        email="master@test.ru",
        password_hash=MASTER_HASH,
        role_id=2,
    )
    session.add(master)
    session.commit()
    session.execute(
        user_workshop_link.insert().values(
            user_id=master.id,
            workshop_id=workshop.id,
            role_in_workshop="master",
        )
    )
    session.commit()

    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def admin_token(client):
    r = client.post("/auth/login", json={"email": "admin@test.ru", "password": "admin123"})
    assert r.status_code == 200
    return r.json()["token"]


@pytest.fixture
def master_token(client):
    r = client.post("/auth/login", json={"email": "master@test.ru", "password": "master123"})
    assert r.status_code == 200
    return r.json()["token"]
