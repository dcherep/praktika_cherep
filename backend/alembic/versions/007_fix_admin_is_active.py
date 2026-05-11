"""Fix admin is_active flag

Revision ID: 007
Revises: 006
Create Date: 2026-03-15

Исправление: устанавливаем is_active=true для админа
"""

from alembic import op
from sqlalchemy import text


revision = '007'
down_revision = '006'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Исправляем is_active для админа
    op.execute(
        text("UPDATE users SET is_active = true WHERE email = 'admin@autoservice.ru' AND is_active IS NULL")
    )


def downgrade() -> None:
    pass
