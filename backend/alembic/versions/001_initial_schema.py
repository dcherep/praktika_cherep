"""Initial schema — roles, users, services, orders, order_services, payments

Revision ID: 001
Revises: 
Create Date: 2026-02-28

# =============================================================================
# ЗОНА РАБОТЫ СЕМЁНА
# =============================================================================
# СЕМЁН, ТУТ: Эта миграция создаёт начальную схему БД по ТЗ.
# 
# Чек-лист для тебя:
# 1. Запусти: alembic upgrade head (применит 001 + 002 с seed)
# 2. Seed уже в 002_seed_roles_admin.py (admin@autoservice.ru / admin123)
# 3. Проверь индексы: idx_orders_client, idx_orders_status, idx_orders_created, idx_users_email
# 4. Добавь составной индекс (status, created_at DESC) для частых запросов списка заявок
# 5. При изменении схемы: alembic revision --autogenerate -m "описание"
# =============================================================================
"""
from alembic import op
import sqlalchemy as sa


revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('roles',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(50), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_table('users',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('first_name', sa.String(100), nullable=False),
        sa.Column('last_name', sa.String(100), nullable=False),
        sa.Column('middle_name', sa.String(100)),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('phone', sa.String(20)),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('role_id', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    op.create_index('idx_users_email', 'users', ['email'])
    op.create_table('services',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('price', sa.Numeric(10, 2)),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table('orders',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('client_id', sa.Integer(), nullable=False),
        sa.Column('master_id', sa.Integer()),
        sa.Column('car_brand', sa.String(100), nullable=False),
        sa.Column('car_model', sa.String(100), nullable=False),
        sa.Column('car_year', sa.SmallInteger(), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('status', sa.String(30), nullable=False, server_default='new'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['client_id'], ['users.id']),
        sa.ForeignKeyConstraint(['master_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_orders_client', 'orders', ['client_id'])
    op.create_index('idx_orders_status', 'orders', ['status'])
    op.create_index('idx_orders_created', 'orders', ['created_at'])
    op.create_table('order_services',
        sa.Column('order_id', sa.Integer(), nullable=False),
        sa.Column('service_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['service_id'], ['services.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('order_id', 'service_id')
    )
    op.create_table('payments',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('order_id', sa.Integer()),
        sa.Column('card_last4', sa.String(4)),
        sa.Column('amount', sa.Numeric(10, 2)),
        sa.Column('status', sa.String(20), server_default='pending'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('order_id')
    )


def downgrade() -> None:
    op.drop_table('payments')
    op.drop_table('order_services')
    op.drop_index('idx_orders_created', 'orders')
    op.drop_index('idx_orders_status', 'orders')
    op.drop_index('idx_orders_client', 'orders')
    op.drop_table('orders')
    op.drop_table('services')
    op.drop_index('idx_users_email', 'users')
    op.drop_table('users')
    op.drop_table('roles')
