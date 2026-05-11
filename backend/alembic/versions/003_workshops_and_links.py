"""Workshops and links to users/orders

Revision ID: 003
Revises: 002
Create Date: 2026-02-28
"""

from alembic import op
import sqlalchemy as sa


revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Новая таблица мастерских
    op.create_table(
        "workshops",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("city", sa.String(100), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_workshops_city", "workshops", ["city"])

    # Привязка пользователей к мастерской (может быть NULL для глобального админа)
    op.add_column(
        "users",
        sa.Column("workshop_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_users_workshop",
        "users",
        "workshops",
        ["workshop_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # Привязка заявок к мастерской
    op.add_column(
        "orders",
        sa.Column("workshop_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_orders_workshop",
        "orders",
        "workshops",
        ["workshop_id"],
        ["id"],
        ondelete="RESTRICT",
    )


def downgrade() -> None:
    op.drop_constraint("fk_orders_workshop", "orders", type_="foreignkey")
    op.drop_column("orders", "workshop_id")

    op.drop_constraint("fk_users_workshop", "users", type_="foreignkey")
    op.drop_column("users", "workshop_id")

    op.drop_index("idx_workshops_city", "workshops")
    op.drop_table("workshops")

