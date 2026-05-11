"""Seed: роли (client, master, admin) и первый admin

Revision ID: 002
Revises: 001
Create Date: 2026-02-28

Данные для входа admin: admin@autoservice.ru / admin123
"""
import bcrypt
from alembic import op
from sqlalchemy import text

revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None

ADMIN_HASH = bcrypt.hashpw(b"admin123", bcrypt.gensalt(rounds=12)).decode()


def upgrade() -> None:
    conn = op.get_bind()
    # Роли: 1=client, 2=master, 3=admin
    conn.execute(text("INSERT INTO roles (name) VALUES ('client'), ('master'), ('admin')"))
    # Первый admin: admin@autoservice.ru / admin123
    conn.execute(
        text(
            "INSERT INTO users (first_name, last_name, email, password_hash, role_id, is_active) "
            "VALUES (:fn, :ln, :email, :pwd, :rid, true)"
        ),
        {"fn": "Администратор", "ln": "Системы", "email": "admin@autoservice.ru", "pwd": ADMIN_HASH, "rid": 3},
    )
    # Пара тестовых услуг для демо
    conn.execute(text("INSERT INTO services (name, price) VALUES ('Замена масла', 1500), ('Диагностика', 2500)"))


def downgrade() -> None:
    op.execute("DELETE FROM users WHERE email = 'admin@autoservice.ru'")
    op.execute("DELETE FROM services")
    op.execute("DELETE FROM roles")
