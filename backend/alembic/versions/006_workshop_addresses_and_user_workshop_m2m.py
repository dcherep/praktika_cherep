"""Workshop addresses and user-workshop M2M

Revision ID: 006
Revises: 005
Create Date: 2026-03-15

Масштабируемость:
- Добавляем адреса мастерским (address, phone)
- Связь Many-to-Many между пользователями и мастерскими
- Один пользователь может работать в нескольких мастерских
"""

from alembic import op
import sqlalchemy as sa


revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Добавляем поля адреса и телефона в workshops
    op.add_column('workshops', sa.Column('address', sa.String(255), nullable=True))
    op.add_column('workshops', sa.Column('phone', sa.String(20), nullable=True))
    
    # 2. Создаём таблицу связи Many-to-Many между пользователями и мастерскими
    op.create_table(
        'user_workshop_link',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('workshop_id', sa.Integer(), nullable=False),
        sa.Column('role_in_workshop', sa.String(50), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['workshop_id'], ['workshops.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_id', 'workshop_id')
    )
    op.create_index('idx_user_workshop_user', 'user_workshop_link', ['user_id'])
    op.create_index('idx_user_workshop_workshop', 'user_workshop_link', ['workshop_id'])
    
    # 3. Мигрируем существующие данные из users.workshop_id в user_workshop_link
    #    (для обратной совместимости)
    op.execute("""
        INSERT INTO user_workshop_link (user_id, workshop_id, role_in_workshop)
        SELECT id, workshop_id, 
               CASE 
                   WHEN role_id = 3 THEN 'admin'
                   WHEN role_id = 2 THEN 'master'
                   ELSE 'client'
               END
        FROM users
        WHERE workshop_id IS NOT NULL
    """)
    
    # 4. Удаляем старое поле workshop_id из users (теперь связь через M2M)
    op.drop_constraint('fk_users_workshop', 'users', type_='foreignkey')
    op.drop_column('users', 'workshop_id')


def downgrade() -> None:
    # 1. Возвращаем поле workshop_id в users
    op.add_column('users', sa.Column('workshop_id', sa.Integer(), nullable=True))
    
    # 2. Мигрируем данные обратно (берём первую мастерскую из связи M2M)
    op.execute("""
        UPDATE users
        SET workshop_id = (
            SELECT workshop_id FROM user_workshop_link 
            WHERE user_workshop_link.user_id = users.id 
            LIMIT 1
        )
    """)
    
    # 3. Восстанавливаем foreign key
    op.create_foreign_key('fk_users_workshop', 'users', 'workshops', ['workshop_id'], ['id'], ondelete='SET NULL')
    
    # 4. Удаляем таблицу связи
    op.drop_index('idx_user_workshop_workshop', 'user_workshop_link')
    op.drop_index('idx_user_workshop_user', 'user_workshop_link')
    op.drop_table('user_workshop_link')
    
    # 5. Удаляем новые поля из workshops
    op.drop_column('workshops', 'phone')
    op.drop_column('workshops', 'address')
