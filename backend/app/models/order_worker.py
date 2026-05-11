# backend/app/models/order_worker.py
"""
ORM-модели: OrderWorker и OrderServiceWorker (связь техников с заказами и услугами).
"""

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, PrimaryKeyConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..database import Base


class OrderWorker(Base):
    """
    Промежуточная таблица Order-Worker (many-to-many).
    Один заказ — много техников, один техник — много заказов.

    Связи:
    - order_id -> Order
    - worker_id -> Worker

    # ==========================================================================
    # МАСШТАБИРУЕМОСТЬ
    # ==========================================================================
    # - role — роль техника в заказе (main/assistant/observer)
    # - hours_spent — затраченное время (для оплаты/учёта)
    # - PRIMARY KEY (order_id, worker_id) — уникальность пары
    # - ON DELETE CASCADE — при удалении заказа удаляются связи
    # - В будущем можно добавить: status, started_at, completed_at
    # ==========================================================================
    """
    __tablename__ = "order_workers"

    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    worker_id = Column(Integer, ForeignKey("workers.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(50), default="main")  # main/assistant/observer
    hours_spent = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Первичный ключ — комбинация order_id + worker_id
    __table_args__ = (
        PrimaryKeyConstraint('order_id', 'worker_id'),
    )

    # Связи
    order = relationship("Order", back_populates="workers")
    worker = relationship("Worker", back_populates="orders")

    def __repr__(self):
        return f"<OrderWorker(order_id={self.order_id}, worker_id={self.worker_id}, role='{self.role}')>"


class OrderServiceWorker(Base):
    """
    Промежуточная таблица Order-Service-Worker (many-to-many-to-many).
    Связывает конкретную услугу в заказе с техником, который её выполнял.

    Связи:
    - order_id -> Order
    - service_id -> Service
    - worker_id -> Worker

    # ==========================================================================
    # МАСШТАБИРУЕМОСТЬ
    # ==========================================================================
    # - Позволяет назначать разных техников на разные услуги в одном заказе
    # - hours_spent — время на конкретную услугу
    # - PRIMARY KEY (order_id, service_id, worker_id) — уникальность тройки
    # - В будущем можно добавить: quality_rating, completed_at
    # ==========================================================================
    """
    __tablename__ = "order_service_workers"

    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    service_id = Column(Integer, ForeignKey("services.id", ondelete="CASCADE"), nullable=False)
    worker_id = Column(Integer, ForeignKey("workers.id", ondelete="CASCADE"), nullable=False)
    hours_spent = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Первичный ключ — комбинация order_id + service_id + worker_id
    __table_args__ = (
        PrimaryKeyConstraint('order_id', 'service_id', 'worker_id'),
    )

    # Связи
    order = relationship("Order", back_populates="service_workers")
    service = relationship("Service", back_populates="service_workers")
    worker = relationship("Worker", back_populates="service_assignments")

    def __repr__(self):
        return f"<OrderServiceWorker(order_id={self.order_id}, service_id={self.service_id}, worker_id={self.worker_id})>"
