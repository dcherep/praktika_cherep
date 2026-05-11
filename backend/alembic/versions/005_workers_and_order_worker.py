"""Workers table and worker link on orders

Revision ID: 005
Revises: 004
Create Date: 2026-02-28
"""

from alembic import op
import sqlalchemy as sa


revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Таблица работников мастерских
    op.create_table(
        "workers",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("first_name", sa.String(100), nullable=False),
        sa.Column("last_name", sa.String(100), nullable=False),
        sa.Column("position", sa.String(100), nullable=True),
        sa.Column("workshop_id", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.sql.expression.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["workshop_id"], ["workshops.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_workers_workshop", "workers", ["workshop_id"])

    # Привязка работника к заявке
    op.add_column(
        "orders",
        sa.Column("worker_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_orders_worker",
        "orders",
        "workers",
        ["worker_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_orders_worker", "orders", type_="foreignkey")
    op.drop_column("orders", "worker_id")

    op.drop_index("idx_workers_workshop", "workers")
    op.drop_table("workers")

