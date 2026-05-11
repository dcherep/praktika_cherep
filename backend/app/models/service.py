# backend/app/models/service.py
"""
ORM-модель: Service (услуги автосервиса).
Связь с Order — через промежуточную таблицу OrderService (many-to-many).
"""

from sqlalchemy import Column, Integer, String, Numeric, Boolean, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..database import Base


class Service(Base):
    """
    Классификатор услуг: название и цена.
    ТЗ: services — справочник услуг.

    # ==========================================================================
    # МАСШТАБИРУЕМОСТЬ
    # ==========================================================================
    # - is_active — soft delete (архивные услуги не удаляются)
    # - updated_at — отслеживание изменений цены/названия
    # - В будущем можно добавить: category_id, duration_minutes, description
    # ==========================================================================
    """
    __tablename__ = "services"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Обратная связь через order_services (заявки, в которых эта услуга)
    orders = relationship(
        "OrderService",
        back_populates="service",
    )

    # Техники, выполнявшие эту услугу (через order_service_workers)
    service_workers = relationship(
        "OrderServiceWorker",
        back_populates="service",
    )
