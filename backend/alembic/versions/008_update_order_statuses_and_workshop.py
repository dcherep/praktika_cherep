"""Update order statuses and make workshop_id required

Revision ID: 008
Revises: 007
Create Date: 2026-03-15

Изменения:
- Убираем статус 'in_repair', оставляем: new, in_progress, done
- Делаем workshop_id NOT NULL (заявка всегда привязана к мастерской)
- Обновляем существующие заявки со статусом 'in_repair' в 'in_progress'
"""

from alembic import op
import sqlalchemy as sa


revision = '008'
down_revision = '007'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Обновляем существующие заявки со статусом 'in_repair' -> 'in_progress'
    op.execute("UPDATE orders SET status = 'in_progress' WHERE status = 'in_repair'")
    
    # 2. Делаем workshop_id NOT NULL
    #    Сначала заполняем NULL значения первой доступной мастерской
    op.execute("""
        UPDATE orders 
        SET workshop_id = (SELECT id FROM workshops LIMIT 1)
        WHERE workshop_id IS NULL
    """)
    
    #    Теперь меняем колонку на NOT NULL
    op.alter_column('orders', 'workshop_id',
               existing_type=sa.Integer(),
               nullable=False)
    
    # 3. Добавляем CHECK constraint для статусов
    op.create_check_constraint(
        'check_order_status',
        'orders',
        "status IN ('new', 'in_progress', 'done')"
    )


def downgrade() -> None:
    # Удаляем CHECK constraint
    op.drop_constraint('check_order_status', 'orders', type_='check')
    
    # Возвращаем workshop_id как nullable
    op.alter_column('orders', 'workshop_id',
               existing_type=sa.Integer(),
               nullable=True)
    
    # Возвращаем статус 'in_repair' для некоторых заявок (50% от in_progress)
    op.execute("""
        UPDATE orders 
        SET status = 'in_repair' 
        WHERE status = 'in_progress' AND id % 2 = 0
    """)
