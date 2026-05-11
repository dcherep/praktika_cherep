# backend/app/models/payment.py
"""
ORM-модель: Payment (заглушка оплаты).
ТЗ: никакого реального платёжного шлюза. Статус stub_ok = "заявка зарегистрирована".
"""

from sqlalchemy import Column, Integer, String, Numeric, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..database import Base


class Payment(Base):
    """
    Заглушка платежа. card_last4 — только для UI (последние 4 цифры).
    status: pending | paid | refunded.

    Связь: order_id -> Order (уникальность: одна заявка — один платёж).

    # ==========================================================================
    # МАСШТАБИРУЕМОСТЬ
    # ==========================================================================
    # - payment_method — способ оплаты (cash/card/online)
    # - updated_at — отслеживание изменений статуса
    # - UNIQUE (order_id) — 1 заказ = 1 платёж (можно убрать для частичных оплат)
    # - В будущем можно добавить: transaction_id, payment_gateway, refund_id
    # ==========================================================================
    """
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="RESTRICT"), unique=True, index=True)
    amount = Column(Numeric(10, 2), nullable=False)
    status = Column(String(30), nullable=False, default="pending")  # pending/paid/refunded
    payment_method = Column(String(30), default="cash")  # cash/card/online
    card_last4 = Column(String(4))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    order = relationship("Order", back_populates="payment")
