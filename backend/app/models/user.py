# backend/app/models/user.py
"""
ORM-модели: Role и User.
Связь: User.role_id -> Role.id (Many-to-One).
Связь с мастерскими: Many-to-Many через user_workshop_link.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..database import Base
from .workshop import user_workshop_link


class Role(Base):
    """
    Роль пользователя: client | master | admin.
    ТЗ: roles — справочник ролей.

    # ==========================================================================
    # МАСШТАБИРУЕМОСТЬ
    # ==========================================================================
    # - name UNIQUE — справочник ролей
    # - В будущем можно добавить: permissions, description, level
    # ==========================================================================
    """
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)

    # Обратная связь: все пользователи с этой ролью
    users = relationship("User", back_populates="role")


class User(Base):
    """
    Пользователь системы.

    Связи:
    - role_id -> Role (роль: клиент/мастер/админ)
    - workshops -> Workshop[] (Many-to-Many: пользователь в нескольких мастерских)
    - orders_as_client -> Order (заявки, где пользователь — клиент)
    - orders_as_master -> Order (заявки, где назначен мастером)

    # ==========================================================================
    # МАСШТАБИРУЕМОСТЬ
    # ==========================================================================
    # - email UNIQUE — обязательное уникальное поле
    # - phone UNIQUE (частичный индекс) — один телефон = один пользователь
    # - updated_at — отслеживание изменений
    # - is_active — мягкое отключение (архивные пользователи)
    # - В будущем можно добавить: avatar_url, timezone, language, last_login_at
    # ==========================================================================
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    middle_name = Column(String(100))
    email = Column(String(255), unique=True, nullable=False, index=True)
    phone = Column(String(20))  # UNIQUE (частичный индекс, см. __table_args__)
    password_hash = Column(String(255), nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Связи
    role = relationship("Role", back_populates="users")

    # Many-to-Many связь с мастерскими
    workshops = relationship("Workshop", secondary=user_workshop_link, back_populates="users")

    orders_as_client = relationship(
        "Order", back_populates="client", foreign_keys="Order.client_id"
    )
    orders_as_master = relationship(
        "Order", back_populates="master", foreign_keys="Order.master_id"
    )

    # Частичный уникальный индекс на phone (только для НЕ NULL значений)
    __table_args__ = (
        Index('ix_users_phone_unique', 'phone', unique=True, postgresql_where='phone IS NOT NULL'),
    )
