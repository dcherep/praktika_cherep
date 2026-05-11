"""Refactor database for scalability

Revision ID: 009
Revises: 008
Create Date: 2026-03-25

Изменения:
1. Справочник городов (cities)
2. workshops.city → city_id FK
3. orders: total_amount, paid_amount, created_at NOT NULL
4. order_services: unit_price, quantity
5. payments: payment_method, updated_at
6. users: phone unique index, updated_at
7. services: is_active, updated_at
8. workers: updated_at
9. order_workers (M2N связь заказ-техники)
10. order_service_workers (связь услуга-техник)
11. worker_schedules (расписание)
12. worker_time_off (отпуска/больничные)
"""

from alembic import op
import sqlalchemy as sa


revision = '009'
down_revision = '008'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ============================================================
    # 1. СОЗДАНИЕ СПРАВОЧНИКА ГОРОДОВ (cities)
    # ============================================================
    op.create_table('cities',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(100), nullable=False, unique=True, index=True),
        sa.Column('region', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # ============================================================
    # 2. ДОБАВЛЕНИЕ updated_at ВО ВСЕ ТАБЛИЦЫ
    # ============================================================
    # services
    op.add_column('services', sa.Column('is_active', sa.Boolean(), nullable=True, default=True))
    op.add_column('services', sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()))
    op.add_column('services', sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()))
    
    # workers
    op.add_column('workers', sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()))
    
    # users
    op.add_column('users', sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()))
    
    # payments
    op.add_column('payments', sa.Column('payment_method', sa.String(30), nullable=True, default='cash'))
    op.add_column('payments', sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()))
    
    # workshops - добавляем city_id и timestamps
    op.add_column('workshops', sa.Column('city_id', sa.Integer(), nullable=True))
    op.add_column('workshops', sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()))
    op.add_column('workshops', sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()))

    # ============================================================
    # 3. ИЗМЕНЕНИЯ В orders
    # ============================================================
    op.add_column('orders', sa.Column('total_amount', sa.Numeric(10, 2), nullable=True, default=0))
    op.add_column('orders', sa.Column('paid_amount', sa.Numeric(10, 2), nullable=True, default=0))
    # created_at уже существует, делаем NOT NULL (оно уже server_default)
    op.alter_column('orders', 'created_at', nullable=False)
    # Индексы для производительности
    op.create_index('ix_orders_client_id', 'orders', ['client_id'])
    op.create_index('ix_orders_master_id', 'orders', ['master_id'])
    op.create_index('ix_orders_workshop_id', 'orders', ['workshop_id'])
    op.create_index('ix_orders_created_at', 'orders', ['created_at'])

    # ============================================================
    # 4. ИЗМЕНЕНИЯ В order_services
    # ============================================================
    op.add_column('order_services', sa.Column('unit_price', sa.Numeric(10, 2), nullable=True))
    op.add_column('order_services', sa.Column('quantity', sa.Integer(), nullable=True, default=1))
    op.add_column('order_services', sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()))
    op.add_column('order_services', sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()))

    # ============================================================
    # 5. НОВЫЕ ТАБЛИЦЫ ДЛЯ ТЕХНИКОВ
    # ============================================================
    # order_workers (M2N связь заказы-техники)
    op.create_table('order_workers',
        sa.Column('order_id', sa.Integer(), sa.ForeignKey('orders.id', ondelete='CASCADE'), nullable=False),
        sa.Column('worker_id', sa.Integer(), sa.ForeignKey('workers.id', ondelete='CASCADE'), nullable=False),
        sa.Column('role', sa.String(50), nullable=True, default='main'),
        sa.Column('hours_spent', sa.Integer(), nullable=True, default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('order_id', 'worker_id'),
    )
    op.create_index('ix_order_workers_worker_id', 'order_workers', ['worker_id'])

    # order_service_workers (связь услуги-техники)
    op.create_table('order_service_workers',
        sa.Column('order_id', sa.Integer(), sa.ForeignKey('orders.id', ondelete='CASCADE'), nullable=False),
        sa.Column('service_id', sa.Integer(), sa.ForeignKey('services.id', ondelete='CASCADE'), nullable=False),
        sa.Column('worker_id', sa.Integer(), sa.ForeignKey('workers.id', ondelete='CASCADE'), nullable=False),
        sa.Column('hours_spent', sa.Integer(), nullable=True, default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('order_id', 'service_id', 'worker_id'),
    )
    op.create_index('ix_order_service_workers_worker_id', 'order_service_workers', ['worker_id'])
    op.create_index('ix_order_service_workers_service_id', 'order_service_workers', ['service_id'])

    # worker_schedules (расписание)
    op.create_table('worker_schedules',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('worker_id', sa.Integer(), sa.ForeignKey('workers.id', ondelete='CASCADE'), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('shift_type', sa.String(20), nullable=True, default='full'),
        sa.Column('hours', sa.Integer(), nullable=True, default=8),
        sa.Column('is_working', sa.Boolean(), nullable=True, default=True),
        sa.Column('comment', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_worker_schedules_date', 'worker_schedules', ['date'])
    op.create_index('ix_worker_schedules_worker_id', 'worker_schedules', ['worker_id'])

    # worker_time_off (отпуска/больничные)
    op.create_table('worker_time_off',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('worker_id', sa.Integer(), sa.ForeignKey('workers.id', ondelete='CASCADE'), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.Column('reason', sa.String(50), nullable=False),
        sa.Column('comment', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_worker_time_off_worker_id', 'worker_time_off', ['worker_id'])

    # ============================================================
    # 6. МИГРАЦИЯ ДАННЫХ
    # ============================================================
    # 6.1 Переносим города из workshops в cities (если поле city ещё существует)
    # Проверяем наличие колонки city
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('workshops')]
    
    if 'city' in columns:
        # Переносим города из workshops в cities
        op.execute("""
            INSERT INTO cities (name, region)
            SELECT DISTINCT city, NULL FROM workshops
            WHERE city IS NOT NULL
            ON CONFLICT (name) DO NOTHING
        """)

        # 6.2 Заполняем city_id в workshops
        op.execute("""
            UPDATE workshops w
            SET city_id = c.id
            FROM cities c
            WHERE w.city = c.name
        """)

        # 6.3 Удаляем старое поле city
        op.drop_column('workshops', 'city')

    # 6.3 Заполняем unit_price в order_services из services.price
    op.execute("""
        UPDATE order_services os
        SET unit_price = s.price
        FROM services s
        WHERE os.service_id = s.id
        AND os.unit_price IS NULL
    """)

    # ============================================================
    # 7. ЗАПОЛНЕНИЕ NULL ЗНАЧЕНИЙ
    # ============================================================
    op.execute("UPDATE services SET is_active = TRUE WHERE is_active IS NULL")
    op.execute("UPDATE orders SET total_amount = 0 WHERE total_amount IS NULL")
    op.execute("UPDATE orders SET paid_amount = 0 WHERE paid_amount IS NULL")
    op.execute("UPDATE order_services SET quantity = 1 WHERE quantity IS NULL")
    op.execute("UPDATE payments SET payment_method = 'cash' WHERE payment_method IS NULL")

    # ============================================================
    # 8. ДЕЛАЕМ ПОЛЯ NOT NULL ПОСЛЕ ЗАПОЛНЕНИЯ
    # ============================================================
    op.alter_column('services', 'is_active', nullable=False)
    op.alter_column('services', 'price', nullable=False)
    op.alter_column('workshops', 'city_id', nullable=False)
    op.alter_column('orders', 'total_amount', nullable=False)
    op.alter_column('orders', 'paid_amount', nullable=False)
    op.alter_column('order_services', 'unit_price', nullable=False)
    op.alter_column('order_services', 'quantity', nullable=False)

    # ============================================================
    # 9. ИНДЕКСЫ
    # ============================================================
    # Все индексы уже созданы через SQLAlchemy модели (index=True)
    # Здесь создаём только частичный уникальный индекс на phone

    # ============================================================
    # 10. УНИКАЛЬНОСТЬ TELEPHONE (частичный индекс)
    # ============================================================
    # Создаём частичный уникальный индекс только для НЕ NULL значений
    # PostgreSQL syntax for partial unique index
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_phone_unique ON users (phone) WHERE phone IS NOT NULL")

    # ============================================================
    # 11. ВНЕШНИЕ КЛЮЧИ
    # ============================================================
    op.create_foreign_key('fk_workshops_city_id', 'workshops', 'cities', ['city_id'], ['id'], ondelete='RESTRICT')
    op.create_foreign_key('fk_order_workers_order_id', 'order_workers', 'orders', ['order_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_order_workers_worker_id', 'order_workers', 'workers', ['worker_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_order_service_workers_order_id', 'order_service_workers', 'orders', ['order_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_order_service_workers_service_id', 'order_service_workers', 'services', ['service_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_order_service_workers_worker_id', 'order_service_workers', 'workers', ['worker_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_worker_schedules_worker_id', 'worker_schedules', 'workers', ['worker_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_worker_time_off_worker_id', 'worker_time_off', 'workers', ['worker_id'], ['id'], ondelete='CASCADE')


def downgrade() -> None:
    # ============================================================
    # ОТКАТ: Удаляем внешние ключи и индексы
    # ============================================================
    op.drop_constraint('fk_workshops_city_id', 'workshops', type_='foreignkey')
    op.drop_constraint('fk_order_workers_order_id', 'order_workers', type_='foreignkey')
    op.drop_constraint('fk_order_workers_worker_id', 'order_workers', type_='foreignkey')
    op.drop_constraint('fk_order_service_workers_order_id', 'order_service_workers', type_='foreignkey')
    op.drop_constraint('fk_order_service_workers_service_id', 'order_service_workers', type_='foreignkey')
    op.drop_constraint('fk_order_service_workers_worker_id', 'order_service_workers', type_='foreignkey')
    op.drop_constraint('fk_worker_schedules_worker_id', 'worker_schedules', type_='foreignkey')
    op.drop_constraint('fk_worker_time_off_worker_id', 'worker_time_off', type_='foreignkey')

    # Частичный уникальный индекс
    op.execute("DROP INDEX IF EXISTS ix_users_phone_unique")

    # ============================================================
    # Удаляем новые таблицы
    # ============================================================
    op.drop_table('worker_time_off')
    op.drop_table('worker_schedules')
    op.drop_table('order_service_workers')
    op.drop_table('order_workers')

    # ============================================================
    # Возвращаем city в workshops
    # ============================================================
    op.add_column('workshops', sa.Column('city', sa.String(100), nullable=True))
    
    # Копируем названия городов обратно
    op.execute("""
        UPDATE workshops w
        SET city = c.name
        FROM cities c
        WHERE w.city_id = c.id
    """)
    
    op.alter_column('workshops', 'city', nullable=False)
    op.drop_column('workshops', 'city_id')
    op.drop_column('workshops', 'created_at')
    op.drop_column('workshops', 'updated_at')

    # ============================================================
    # Удаляем справочник городов
    # ============================================================
    op.drop_table('cities')

    # ============================================================
    # Откат изменений в orders
    # ============================================================
    op.drop_column('orders', 'total_amount')
    op.drop_column('orders', 'paid_amount')
    # created_at оставляем как есть

    # ============================================================
    # Откат изменений в order_services
    # ============================================================
    op.drop_column('order_services', 'unit_price')
    op.drop_column('order_services', 'quantity')
    op.drop_column('order_services', 'created_at')
    op.drop_column('order_services', 'updated_at')

    # ============================================================
    # Откат изменений в payments
    # ============================================================
    op.drop_column('payments', 'payment_method')
    op.drop_column('payments', 'updated_at')

    # ============================================================
    # Откат изменений в services
    # ============================================================
    op.drop_column('services', 'is_active')
    op.drop_column('services', 'created_at')
    op.drop_column('services', 'updated_at')

    # ============================================================
    # Откат изменений в workers
    # ============================================================
    op.drop_column('workers', 'updated_at')

    # ============================================================
    # Откат изменений в users
    # ============================================================
    op.drop_column('users', 'updated_at')
