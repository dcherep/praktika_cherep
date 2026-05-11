# backend/app/models/order.py
"""
ORM-модели: Order и OrderService (связь заявка-услуга).
Order связан с User (client, master) и Service (через OrderService).
"""

from sqlalchemy import Column, Integer, String, Text, SmallInteger, ForeignKey, DateTime, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..database import Base


class Order(Base):
    """
    Заявка клиента на ремонт.

    Связи:
    - client_id -> User (кто создал заявку)
    - master_id -> User (назначенный мастер, может быть NULL)
    - workshop_id -> Workshop (мастерская, где выполняется заявка)
    - workers -> OrderWorker[] (техники на заказе, many-to-many)
    - order_services -> OrderService[] (услуги в заявке, many-to-many)
    - service_workers -> OrderServiceWorker[] (техники на услугах)
    - payments -> Payment (платёж по заявке; 1:1)

    Статусы: new | in_progress | done

    # ==========================================================================
    # МАСШТАБИРУЕМОСТЬ
    # ==========================================================================
    # - total_amount/paid_amount — гибкая модель оплат (частичные оплаты в будущем)
    # - worker_id удалён → order_workers (M2N, несколько техников)
    # - updated_at — отслеживание изменений
    # - Индексы: client_id, master_id, workshop_id, status, created_at DESC
    # - ON DELETE SET NULL для master_id — заявка остаётся при удалении мастера
    # - В будущем можно добавить: priority, estimated_completion, customer_rating
    # ==========================================================================
    """
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    master_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), index=True)
    workshop_id = Column(Integer, ForeignKey("workshops.id", ondelete="RESTRICT"), nullable=False, index=True)
    car_brand = Column(String(100), nullable=False)
    car_model = Column(String(100), nullable=False)
    car_year = Column(SmallInteger, nullable=False)
    description = Column(Text)
    status = Column(String(30), nullable=False, default="new")
    total_amount = Column(Numeric(10, 2), default=0)  # Рассчитанная сумма заказа
    paid_amount = Column(Numeric(10, 2), default=0)   # Сколько оплачено
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Связи
    client = relationship("User", back_populates="orders_as_client", foreign_keys=[client_id])
    master = relationship("User", back_populates="orders_as_master", foreign_keys=[master_id])
    workshop = relationship("Workshop", back_populates="orders")

    # Техники на заказе (M2N)
    workers = relationship(
        "OrderWorker",
        back_populates="order",
        cascade="all, delete-orphan",
    )

    # Услуги в заказе (M2M)
    order_services = relationship(
        "OrderService",
        back_populates="order",
        cascade="all, delete-orphan",
    )

    # Техники на услугах (M2N)
    service_workers = relationship(
        "OrderServiceWorker",
        back_populates="order",
        cascade="all, delete-orphan",
    )

    # Платёж (1:1)
    payment = relationship("Payment", back_populates="order", uselist=False, cascade="all, delete-orphan")


class OrderService(Base):
    """
    Промежуточная таблица Order-Service (many-to-many).
    Одна заявка — много услуг, одна услуга — много заявок.

    # ==========================================================================
    # МАСШТАБИРУЕМОСТЬ
    # ==========================================================================
    # - unit_price — цена на момент заказа (не зависит от изменений в services)
    # - quantity — количество (если услуга многократная)
    # - PRIMARY KEY (order_id, service_id) — уникальность пары
    # - ON DELETE CASCADE на order_id — при удалении заявки удаляются связи
    # - ON DELETE RESTRICT на service_id — нельзя удалить услугу из справочника, если она в заказах
    # - В будущем можно добавить: discount, warranty_months
    # ==========================================================================
    """
    __tablename__ = "order_services"

    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), primary_key=True)
    service_id = Column(Integer, ForeignKey("services.id", ondelete="RESTRICT"), primary_key=True)
    unit_price = Column(Numeric(10, 2), nullable=False)  # Цена на момент заказа
    quantity = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    order = relationship("Order", back_populates="order_services")
    service = relationship("Service", back_populates="orders")
