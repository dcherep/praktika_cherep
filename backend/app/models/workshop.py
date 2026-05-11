from sqlalchemy import Column, Integer, String, ForeignKey, Table, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..database import Base


# Связь Many-to-Many между пользователями и мастерскими
# Один пользователь может работать в нескольких мастерских
user_workshop_link = Table(
    "user_workshop_link",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("workshop_id", Integer, ForeignKey("workshops.id", ondelete="CASCADE"), primary_key=True),
    Column("role_in_workshop", String(50), nullable=True),  # Должность в конкретной мастерской
)


class Workshop(Base):
    """
    Мастерская (филиал сети) с адресом.

    Примеры: Москва — Центральная, Санкт-Петербург — Север.
    У мастерской есть адрес, телефон, и свои сотрудники.

    # ==========================================================================
    # МАСШТАБИРУЕМОСТЬ
    # ==========================================================================
    # - city_id FK → cities — справочник городов (вместо VARCHAR)
    # - updated_at — отслеживание изменений
    # - ON DELETE RESTRICT — нельзя удалить город, если есть мастерские
    # - В будущем можно добавить: coordinates, timezone, manager_id
    # ==========================================================================
    """

    __tablename__ = "workshops"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    city_id = Column(Integer, ForeignKey("cities.id", ondelete="RESTRICT"), nullable=False, index=True)
    address = Column(String(255), nullable=True)  # Улица, дом
    phone = Column(String(20), nullable=True)     # Телефон мастерской
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Связи
    city = relationship("City", back_populates="workshops")

    # Связь Many-to-Many с пользователями
    users = relationship("User", secondary=user_workshop_link, back_populates="workshops")

    # Заявки в этой мастерской
    orders = relationship("Order", back_populates="workshop")

    # Техники в этой мастерской
    workers = relationship("Worker", back_populates="workshop")

