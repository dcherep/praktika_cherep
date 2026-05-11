"""Seed workshops (cities) and base users

Revision ID: 004
Revises: 003
Create Date: 2026-02-28
"""

import bcrypt
from alembic import op
from sqlalchemy import text


revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()

    # Создаём мастерские в разных городах
    conn.execute(
        text(
            "INSERT INTO workshops (name, city) VALUES "
            "(:n1, :c1), (:n2, :c2), (:n3, :c3)"
        ),
        {
            "n1": "Москва — Центральная",
            "c1": "Москва",
            "n2": "Санкт-Петербург — Север",
            "c2": "Санкт-Петербург",
            "n3": "Новосибирск — Восток",
            "c3": "Новосибирск",
        },
    )

    # Получаем id мастерских
    workshops = {
        row.city: row.id
        for row in conn.execute(text("SELECT id, city FROM workshops"))
    }

    # Роли
    role_ids = {
        row.name: row.id
        for row in conn.execute(text("SELECT id, name FROM roles"))
    }
    master_role_id = role_ids.get("master")
    client_role_id = role_ids.get("client")

    if not master_role_id or not client_role_id:
        return

    def _hash(pwd: str) -> str:
        return bcrypt.hashpw(pwd.encode(), bcrypt.gensalt(rounds=12)).decode()

    users_payload = [
        # Москва
        {
            "fn": "Иван",
            "ln": "Москвин",
            "email": "master.moscow@autoservice.ru",
            "pwd": _hash("master123"),
            "rid": master_role_id,
            "wid": workshops["Москва"],
        },
        {
            "fn": "Пётр",
            "ln": "Клиентов",
            "email": "client.moscow@autoservice.ru",
            "pwd": _hash("client123"),
            "rid": client_role_id,
            "wid": workshops["Москва"],
        },
        # Санкт-Петербург
        {
            "fn": "Алексей",
            "ln": "Питерский",
            "email": "master.spb@autoservice.ru",
            "pwd": _hash("master123"),
            "rid": master_role_id,
            "wid": workshops["Санкт-Петербург"],
        },
        {
            "fn": "Мария",
            "ln": "Невская",
            "email": "client.spb@autoservice.ru",
            "pwd": _hash("client123"),
            "rid": client_role_id,
            "wid": workshops["Санкт-Петербург"],
        },
        # Новосибирск
        {
            "fn": "Дмитрий",
            "ln": "Сибирский",
            "email": "master.nsk@autoservice.ru",
            "pwd": _hash("master123"),
            "rid": master_role_id,
            "wid": workshops["Новосибирск"],
        },
        {
            "fn": "Ольга",
            "ln": "Обская",
            "email": "client.nsk@autoservice.ru",
            "pwd": _hash("client123"),
            "rid": client_role_id,
            "wid": workshops["Новосибирск"],
        },
    ]

    for u in users_payload:
        conn.execute(
            text(
                "INSERT INTO users (first_name, last_name, email, password_hash, role_id, workshop_id, is_active) "
                "VALUES (:fn, :ln, :email, :pwd, :rid, :wid, true)"
            ),
            u,
        )


def downgrade() -> None:
    conn = op.get_bind()
    # Удаляем созданных пользователей по email
    emails = [
        "master.moscow@autoservice.ru",
        "client.moscow@autoservice.ru",
        "master.spb@autoservice.ru",
        "client.spb@autoservice.ru",
        "master.nsk@autoservice.ru",
        "client.nsk@autoservice.ru",
    ]
    conn.execute(
        text("DELETE FROM users WHERE email = ANY(:emails)"),
        {"emails": emails},
    )
    # Удаляем мастерские
    conn.execute(
        text(
            "DELETE FROM workshops WHERE city IN (:c1, :c2, :c3)"
        ),
        {"c1": "Москва", "c2": "Санкт-Петербург", "c3": "Новосибирск"},
    )

