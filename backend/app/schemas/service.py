# backend/app/schemas/service.py
"""Pydantic-схемы для Service."""

from decimal import Decimal
from pydantic import BaseModel


class ServiceCreate(BaseModel):
    name: str
    price: Decimal | None = None


class ServiceUpdate(BaseModel):
    name: str | None = None
    price: Decimal | None = None


class ServiceRead(BaseModel):
    id: int
    name: str
    price: Decimal | None
    model_config = {"from_attributes": True}
