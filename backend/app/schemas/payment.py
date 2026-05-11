# backend/app/schemas/payment.py
"""Pydantic-схемы для Payment (заглушка)."""

from decimal import Decimal
from pydantic import BaseModel


class PaymentStubIn(BaseModel):
    """Входные данные заглушки. Данные карты НЕ передаются (только для UI)."""
    order_id: int
    amount: Decimal
    card_number: str | None = None  # опционально, последние 4 — только для записи


class PaymentStubOut(BaseModel):
    success: bool = True
    message: str = "Заявка зарегистрирована"
